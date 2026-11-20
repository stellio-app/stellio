"""1.1.7 — assistant de fabrication : diagnostic, matières, réglages, pièces voisines, garde-fous."""
import importlib.util, json, logging, os, sqlite3, sys
import pytest
flask = pytest.importorskip('flask')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _mod(name):
    spec = importlib.util.spec_from_file_location(name + '_t', __import__('conftest').mod_path(name))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def test_wilson_et_pistes():
    f = _mod('fab_assistant')
    assert f.wilson_lower(0, 0) == 0 and f.wilson_lower(9, 10) > f.wilson_lower(1, 1) and f.wilson_lower(50, 100) < 0.5
    adv = f.advice_for(['Décollement du plateau', 'décollement du plateau', 'stringing', 'cause mystère', ''])
    by = {x['reason']: x for x in adv}
    assert adv[0]['count'] == 2 and 'plateau' in adv[0]['tips'][0].lower()
    assert by['cause mystère']['tips'] == [] and by['stringing']['tips']              # motif inconnu : pas de piste inventée
    assert len(adv) == 3                                                               # raison vide ignorée


def test_facteurs_au_dessus_de_la_moyenne():
    f = _mod('fab_assistant')
    rows = [{'failed': i < 4, 'material': 'ABS', 'printer': 'A', 'nozzle_band': None} for i in range(5)] + \
           [{'failed': False, 'material': 'PLA', 'printer': 'A', 'nozzle_band': None} for i in range(10)] + [{'failed': True, 'material': 'TPU', 'printer': 'B', 'nozzle_band': None}] * 2
    base = 100 * sum(r['failed'] for r in rows) / len(rows)
    gaps = f.factor_gaps(rows, base)
    assert [(g['factor'], g['value']) for g in gaps] == [('material', 'ABS')] and gaps[0]['rate'] == 80.0       # TPU : 2 impressions < minimum, ignoré
    assert f.nozzle_band(215) == '210–219 °C' and f.nozzle_band(None) is None


def test_validation_du_catalogue():
    f = _mod('fab_assistant')
    assert f.validate_call('suggest_material', {'model': 'vase', 'printer_id': '3', 'sql': 'DROP'}, {3}) == ('suggest_material', {'model': 'vase', 'printer_id': 3})
    for q, p, pids in (('inconnue', {}, None), ('suggest_material', {}, None), ('suggest_material', {'model': 'x', 'printer_id': 9}, {1})):
        with pytest.raises(ValueError): f.validate_call(q, p, pids)
    assert f.validate_call('diagnose_failure', {'material': 'petg'}, None)[1] == {'material': 'PETG'}
    assert f.parse_ai_reply('Voici : {"query": "similar_models", "params": {"model": "x"}} ok')['query'] == 'similar_models' and f.parse_ai_reply('rien') is None


def test_routeur_a_regles():
    f = _mod('fab_assistant'); pr = [{'id': 1, 'name': 'Prusa'}]
    assert f.route_rules('Quels modèles ressemble au vase ?', pr, ['vase'])[0] == 'similar_models'
    assert f.route_rules('quelle matière pour le vase sur Prusa', pr, ['vase']) == ('suggest_material', {'model': 'vase', 'printer_id': 1})
    assert f.route_rules('quels réglages pour vase', pr, ['vase'])[0] == 'suggest_settings'
    assert f.route_rules('pourquoi mes impressions en ABS ratent', pr, []) == ('diagnose_failure', {'material': 'ABS'})


def _env(tmp_path):
    f = _mod('fab_assistant'); path = str(tmp_path / 't.db')
    def get_db():
        c = sqlite3.connect(path); c.row_factory = sqlite3.Row; return c
    c = get_db()
    c.executescript("""CREATE TABLE printers (id INTEGER PRIMARY KEY, user_id INT, name TEXT, config TEXT);
        CREATE TABLE print_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, file_path TEXT, file_name TEXT, result TEXT, printer_id INT,
            filament_material TEXT, failure_reason TEXT, slicer_profile_name TEXT, nozzle_temp REAL, bed_temp REAL);
        INSERT INTO printers VALUES (1,1,'Prusa','{}'),(2,2,'Autre','{}');""")
    rows = [('/src/vase.stl', 'success', 'PLA', '', 'Standard', 210, 60)] * 6 + [('/src/vase.stl', 'failed', 'ABS', 'décollement plateau', 'Rapide', 245, 95)] * 4 + \
           [('/src/vase.stl', 'success', 'ABS', '', 'Rapide', 245, 95)] * 1
    for p, res, mat, why, prof, nt, bt in rows:
        c.execute("INSERT INTO print_history (user_id, file_path, file_name, result, printer_id, filament_material, failure_reason, slicer_profile_name, nozzle_temp, bed_temp) VALUES (1,?,?,?,1,?,?,?,?,?)",
                  (p, 'vase.stl', res, mat, why, prof, nt, bt))
    c.execute("INSERT INTO print_history (user_id, file_path, file_name, result, printer_id, filament_material) VALUES (2,'/src/vase.stl','vase.stl','failed',2,'PLA')")
    c.commit(); c.close()
    app = flask.Flask('t'); app.secret_key = 'x'
    f.init(dict(app=app, app_logger=logging.getLogger('t'), get_db=get_db, jsonify=flask.jsonify, login_required=lambda fn: fn, request=flask.request, session=flask.session,
                _is_path_within_sources=lambda p, uid: str(p).startswith('/src/')))
    cl = app.test_client()
    with cl.session_transaction() as s: s['user_id'] = 1
    return f, cl, get_db


def test_diagnostic_chiffre_et_pistes(tmp_path):
    f, cl, _ = _env(tmp_path)
    r = cl.post('/api/fab/ask', json={'query': 'diagnose_failure', 'params': {'model': 'vase'}}).get_json()
    assert r['summary'] == {'rated': 11, 'failed': 4, 'failure_rate': 36.4}                                  # l'échec d'un autre compte n'est pas compté
    assert r['rows'][0]['factor'] == 'material' and r['rows'][0]['value'] == 'ABS' and r['rows'][0]['rate'] == 80.0
    assert r['tips'][0]['count'] == 4 and 'plateau' in r['tips'][0]['tips'][0].lower()
    assert r['proposals'][0]['target'] == 'Fragile en ABS' and r['via'] == 'direct'


def test_peu_de_donnees_aucune_conclusion(tmp_path):
    f, cl, _ = _env(tmp_path)
    r = cl.post('/api/fab/ask', json={'query': 'diagnose_failure', 'params': {'material': 'TPU'}}).get_json()
    assert r['rows'] == [] and 'trop peu' in r['notes'][0]


def test_matieres_reglages_et_question_libre(tmp_path):
    f, cl, _ = _env(tmp_path)
    r = cl.post('/api/fab/ask', json={'query': 'suggest_material', 'params': {'model': 'vase'}}).get_json()
    assert [x['material'] for x in r['rows']] == ['PLA', 'ABS'] and r['rows'][0]['score'] > r['rows'][1]['score']
    r = cl.post('/api/fab/ask', json={'query': 'suggest_settings', 'params': {'model': 'vase'}}).get_json()
    d = {x['setting']: x['value'] for x in r['rows']}
    assert d['Matière la plus utilisée'] == 'PLA' and d['Profil de slicer le plus utilisé'] == 'Standard' and r['summary']['successes'] == 7
    r = cl.post('/api/fab/ask', json={'question': 'pourquoi mes impressions en ABS ratent ?'}).get_json()
    assert r['query'] == 'diagnose_failure' and r['via'] == 'rules'


def test_ia_hors_catalogue_rejetee_au_profit_des_regles(tmp_path):
    f, cl, get_db = _env(tmp_path); c = get_db()
    r = f.ask(c, 1, 'pourquoi ABS rate', ai_choose=lambda p: '{"query": "DROP TABLE users", "params": {}}')
    assert r['via'] == 'rules' and r['ai_note'].startswith('ai_rejected') and r['query'] == 'diagnose_failure'
    r = f.ask(c, 1, 'pourquoi ABS rate', ai_choose=lambda p: '{"query": "diagnose_failure", "params": {"printer_id": 2}}')   # imprimante d'un autre compte
    assert r['via'] == 'rules' and 'unknown_printer' in r['ai_note']
    r = f.ask(c, 1, 'x', ai_choose=lambda p: 1 / 0); assert r['via'] == 'rules' and r['ai_note'] == 'ai_error'


def test_proposition_appliquee_seulement_apres_confirmation(tmp_path):
    f, cl, get_db = _env(tmp_path)
    body = {'action': 'tag', 'path': '/src/vase.stl', 'target': 'Fragile en ABS'}
    assert cl.post('/api/fab/apply', json=body).status_code == 400                                          # pas de confirmation
    assert cl.post('/api/fab/apply', json=dict(body, confirm=True, path='/ailleurs/x.stl')).status_code == 400  # hors sources
    assert cl.post('/api/fab/apply', json=dict(body, confirm=True, action='delete')).status_code == 400
    assert cl.post('/api/fab/apply', json=dict(body, confirm=True)).status_code == 200
    assert get_db().execute("SELECT t.name FROM file_tags f JOIN tags t ON t.id=f.tag_id WHERE f.file_path='/src/vase.stl'").fetchone()[0] == 'Fragile en ABS'
    with cl.session_transaction() as s: s['role'] = 'viewer'
    assert cl.post('/api/fab/ask', json={'query': 'diagnose_failure'}).status_code == 403


def test_pieces_voisines_et_matiere_via_forme(tmp_path):
    f, cl, get_db = _env(tmp_path); ss = _mod('shape_search'); c = get_db(); ss._ensure(c)
    d_vase = [0.04] * 24 + [0.5, 0.4, 0.6, 0.5]; d_pot = [0.041] * 24 + [0.5, 0.41, 0.6, 0.5]; d_plaque = [0.1] * 12 + [0.0] * 12 + [0.05, 0.02, 0.2, 0.3]
    for p, d in (('/src/vase.stl', d_vase), ('/src/pot.stl', d_pot), ('/src/plaque.stl', d_plaque)):
        c.execute("INSERT INTO shape_index (user_id, path, mtime, size, desc, ms, indexed_at) VALUES (1,?,1,1,?,5,1)", (p, json.dumps(d)))
    for _ in range(4): c.execute("INSERT INTO print_history (user_id, file_path, file_name, result, printer_id, filament_material) VALUES (1,'/src/pot.stl','pot.stl','success',1,'PETG')")
    c.commit(); c.close()
    r = cl.post('/api/fab/ask', json={'query': 'similar_models', 'params': {'model': 'vase'}}).get_json()
    assert r['rows'][0]['name'] == 'pot.stl' and r['rows'][0]['similarity'] > 90 and r['rows'][0]['prints'] == 4 and r['rows'][0]['rate'] == 100.0
    r = cl.post('/api/fab/ask', json={'query': 'suggest_material', 'params': {'model': 'vase'}}).get_json()
    assert any(x['material'] == 'PETG' and x['source'] == 'pièces de forme proche' for x in r['rows'])
    r = cl.post('/api/fab/ask', json={'query': 'similar_models', 'params': {'model': 'inexistant'}}).get_json()
    assert r['rows'] == [] and 'indexation' in r['notes'][0]
