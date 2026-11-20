"""1.1.7 — Stellio Intelligence : recommandation de réglages et causes probables, apprises des impressions notées (statistiques, pas un modèle d'IA)."""
import importlib.util, logging, os, sqlite3
import pytest
flask = pytest.importorskip('flask')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _mod():
    spec = importlib.util.spec_from_file_location('intel_t', os.path.join(ROOT, 'modules', 'intelligence.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


PROFILES = {
    'good': {'id': 'good', 'name': 'Standard 215', 'nozzle_temp': 215, 'bed_temp': 60, 'print_speed': 60},
    'cold': {'id': 'cold', 'name': 'Froid 195', 'nozzle_temp': 195, 'bed_temp': 50, 'print_speed': 60},
    'fast': {'id': 'fast', 'name': 'Rapide', 'nozzle_temp': 215, 'bed_temp': 60, 'print_speed': 150},
}


def R(i, result, pid='good', mat='PLA', printer=1, reason='', path='/m/a.stl'):
    return {'id': i, 'result': result, 'failure_reason': reason, 'filament_material': mat, 'printer_id': printer, 'slicer_profile_id': pid,
            'slicer_profile_name': PROFILES[pid]['name'], 'model_path': path, 'sent_at': f'2026-11-{i % 28 + 1:02d} 10:00:00'}


def test_recommande_le_profil_qui_reussit_et_deconseille_celui_qui_rate():
    m = _mod()
    rows = [R(i, 'success') for i in range(6)] + [R(10 + i, 'failed' if i < 3 else 'success', 'cold', reason='adhesion') for i in range(4)]
    r = m.recommend(rows, PROFILES, material='PLA', printer_id=1)
    assert r['best']['profile'] == 'Standard 215' and r['best']['confidence'] == 'high' and r['best']['total'] == 6
    assert [a['profile'] for a in r['avoid']] == ['Froid 195'] and r['readiness']['ready']
    p = {x['param']: x for x in r['params']}
    assert p['nozzle_temp']['typical'] == 215 and p['nozzle_temp']['min'] == 195 and p['nozzle_temp']['max'] == 215 and p['nozzle_temp']['n_ok'] == 7


def test_refuse_de_conclure_sans_assez_de_donnees():
    m = _mod()
    r = m.recommend([R(1, 'success'), R(2, 'failed')], PROFILES, material='PLA')
    assert r['best'] is None and r['reason'] == 'not_enough_data' and not r['readiness']['ready']
    assert m.recommend([], PROFILES)['reason'] == 'not_enough_data'
    d = m.diagnose([R(1, 'failed', reason='warping')], PROFILES, material='PLA')
    assert d['causes'] == [] and d['reason'] == 'not_enough_data'


def test_le_perimetre_s_elargit_quand_la_matiere_manque_de_donnees():
    m = _mod()
    rows = [R(i, 'success', mat='PETG') for i in range(5)] + [R(20, 'success', mat='PLA')]
    r = m.recommend(rows, PROFILES, material='PLA', printer_id=1)
    assert r['scope']['widened'] and r['scope']['kind'] != 'material_printer' and r['best'] is not None
    r2 = m.recommend(rows, PROFILES, material='PETG', printer_id=1)
    assert not r2['scope']['widened'] and r2['sample'] == 5


def test_diagnostic_motif_declare_et_ecart_de_reglage():
    m = _mod()
    rows = [R(i, 'success') for i in range(5)] + [R(10 + i, 'failed', 'cold', reason='adhesion') for i in range(3)] + [R(20, 'failed', 'cold', reason='warping')]
    d = m.diagnose(rows, PROFILES, material='PLA', printer_id=1)
    top = d['causes'][0]
    assert top['cause'] == 'adhesion' and {e['type'] for e in top['evidence']} >= {'declared', 'param'}
    assert any(e['type'] == 'param' and e['param'] == 'nozzle_temp' and e['direction'] == 'lower' for e in top['evidence'])
    assert d['failed'] == 4 and d['reason'] is None


def test_diagnostic_d_une_impression_donnee_compte_son_motif():
    m = _mod()
    rows = [R(i, 'success') for i in range(4)] + [R(10, 'failed', reason='stringing'), R(11, 'failed', reason='stringing')]
    d = m.diagnose(rows, PROFILES, material='PLA', printer_id=1, target=rows[-1])
    assert d['causes'][0]['cause'] == 'stringing' and d['this_print'] == {'failure_reason': 'stringing'}
    assert any(e['type'] == 'this_print' for e in d['causes'][0]['evidence'])


def test_contexte_profil_qui_echoue_plus_que_la_moyenne_et_pas_de_cause_inventee():
    m = _mod()
    rows = [R(i, 'success') for i in range(6)] + [R(10 + i, 'failed', 'fast') for i in range(3)] + [R(20, 'success', 'fast')]
    d = m.diagnose(rows, PROFILES, material='PLA', printer_id=1)
    assert any(c['dimension'] == 'profile' and c['key'] == 'Rapide' for c in d['contexts'])
    assert d['causes'] == [] or all(c['cause'] in m.REASONS for c in d['causes'])
    # motifs non précisés et aucun réglage connu : aucune cause inventée
    rows2 = [dict(R(i, 'success'), slicer_profile_id='') for i in range(4)] + [dict(R(10 + i, 'failed'), slicer_profile_id='') for i in range(3)]
    d2 = m.diagnose(rows2, {}, material='PLA', printer_id=1)
    assert d2['causes'] == [] and d2['reason'] == 'no_clear_cause'


def test_donnees_hostiles_ne_plantent_pas():
    m = _mod()
    bad = [{'result': 'success', 'filament_material': None, 'slicer_profile_id': 'x'}, {'result': 'weird'}, {}, dict(R(1, 'failed'), failure_reason=None, printer_id='abc')]
    m.recommend(bad, {'x': {'nozzle_temp': 'abc', 'bed_temp': float('nan')}}, material=None, printer_id='zz', model_path=None)
    m.diagnose(bad, {'x': {'nozzle_temp': float('inf')}}, material='', printer_id=None)


def _app(tmp_path, monkeypatch):
    m = _mod(); db = tmp_path / 'i.db'
    c = sqlite3.connect(db)
    c.execute("CREATE TABLE print_history (id INTEGER PRIMARY KEY, user_id INT, file_path TEXT, file_name TEXT, result TEXT, failure_reason TEXT, filament_material TEXT, printer_id INT, slicer_profile_id TEXT, slicer_profile_name TEXT, sent_at TEXT)")
    c.execute("CREATE TABLE printers (id INTEGER PRIMARY KEY, name TEXT)"); c.execute("INSERT INTO printers VALUES (1,'Voron')")
    rows = [(i, 1, '/m/a.stl', 'a.stl', 'success', '', 'PLA', 1, 'good', 'Standard 215', '2026-11-01 10:00:00') for i in range(1, 7)]
    rows += [(10 + i, 1, '/m/a.stl', 'a.stl', 'failed', 'adhesion', 'PLA', 1, 'cold', 'Froid 195', '2026-11-02 10:00:00') for i in range(3)]
    rows += [(50, 2, '/m/z.stl', 'z.stl', 'failed', 'warping', 'ABS', 1, 'cold', 'Froid 195', '2026-11-02 10:00:00')]       # autre utilisateur : jamais mélangé
    c.executemany("INSERT INTO print_history VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows); c.commit(); c.close()
    def get_db():
        k = sqlite3.connect(db); k.row_factory = sqlite3.Row; return k
    app = flask.Flask('i'); app.secret_key = 'x'
    m.init(dict(app=app, get_db=get_db, jsonify=flask.jsonify, login_required=lambda f: f, request=flask.request, session=flask.session, app_logger=logging.getLogger('t')))
    monkeypatch.setattr(m, '_profiles', lambda: PROFILES)
    return app


def test_routes(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch); cl = app.test_client()
    with cl.session_transaction() as s: s['user_id'] = 1
    o = cl.get('/api/intelligence/overview').get_json()
    assert o['readiness']['rated'] == 9 and o['materials'] == ['PLA'] and o['printers'] == [{'id': 1, 'name': 'Voron'}]      # l'autre utilisateur n'apparaît pas
    r = cl.get('/api/intelligence/recommend?material=pla&printer_id=1').get_json()
    assert r['best']['profile'] == 'Standard 215' and r['readiness']['ready']
    d = cl.get('/api/intelligence/diagnose?history_id=10').get_json()
    assert d['causes'][0]['cause'] == 'adhesion' and d['this_print']['failure_reason'] == 'adhesion'
    assert cl.get('/api/intelligence/diagnose?history_id=50').status_code == 404                                              # ligne d'un autre utilisateur
    assert cl.get('/api/intelligence/recommend?printer_id=abc&material=%00').status_code == 200
