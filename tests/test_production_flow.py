"""Flux de production (1.1.8) : contrôles, validation humaine obligatoire, envoi, résultat, retour d'expérience d'Intelligence."""
import importlib.util
import os
import sqlite3

import pytest

from conftest import mod_path

flask = pytest.importorskip('flask')


def _load(name):
    spec = importlib.util.spec_from_file_location(name + '_pf_test', mod_path(name))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_controles_fichier_et_imprimante():
    pf = _load('production_flow')
    assert pf.check_file('a.stl', False) == ('block', 'needs_slicing')
    assert pf.check_file('a.gcode', True) == ('block', 'wrong_kind')
    assert pf.check_file('a.sl1', False) == ('block', 'wrong_kind')
    assert pf.check_file('a.sl1', True) == ('ok', 'file_ready')
    assert pf.check_file('a.bgcode', False) == ('ok', 'file_ready')
    assert pf.check_file('a.3mf', False) == ('warn', 'project_3mf')
    assert pf.check_printer_state({'status': 'offline'}) == ('block', 'printer_offline')
    assert pf.check_printer_state({'status': 'printing'}) == ('warn', 'printer_busy')
    assert pf.check_printer_state({'status': 'idle'}) == ('ok', 'printer_idle')


def test_classement_bonus_intelligence_et_departage():
    pf = _load('production_flow')
    r = pf.rank([{'printer_id': 2, 'score': 100, 'rec_bonus': 0}, {'printer_id': 1, 'score': 90, 'rec_bonus': 25}, {'printer_id': 3, 'score': 100, 'rec_bonus': 0}])
    assert [c['printer_id'] for c in r] == [1, 2, 3]


def _combo(name, score=0.6):
    return {'profile': name, 'profile_fp': '', 'score': score, 'total': 6, 'last': '', 'success': 5, 'failed': 1, 'partial': 0, 'rate': 0.83, 'settings': {}}


def test_retour_d_experience_retrograde_et_favorise():
    it = _load('intelligence')
    fb = [{'profile': 'A', 'followed': True, 'result': 'failed'}] * 3 + [{'profile': 'B', 'followed': True, 'result': 'success'}] * 3
    out = it.apply_feedback([_combo('A', 0.7), _combo('B', 0.6), _combo('C', 0.55)], fb)
    names = [c['profile'] for c in out]
    assert names == ['B', 'C', 'A']                        # A rétrogradé : suivi 3 fois, 3 échecs
    byname = {c['profile']: c for c in out}
    assert byname['A']['feedback']['effect'] == 'demoted' and byname['B']['feedback']['effect'] == 'promoted'
    assert 'feedback' not in byname['C']


def test_retour_d_experience_pas_de_correction_sous_le_seuil_ni_si_ignore():
    it = _load('intelligence')
    fb = [{'profile': 'A', 'followed': True, 'result': 'failed'}] * 2 + [{'profile': 'A', 'followed': False, 'result': 'failed'}] * 5
    out = it.apply_feedback([_combo('A', 0.7)], fb)
    assert out[0]['score'] == 0.7 and out[0]['feedback']['effect'] == 'none' and out[0]['feedback']['followed'] == 2
    st = it.feedback_stats(fb)
    assert st['followed']['total'] == 2 and st['ignored']['total'] == 5 and st['ignored']['rate'] == 0.0


def test_enregistrement_suivi_ou_non_et_resultat():
    it = _load('intelligence')
    c = sqlite3.connect(':memory:')
    c.row_factory = sqlite3.Row
    assert it.record_feedback(c, 1, 5, 2, 'PLA', '/m.stl', '', '', 'X') is None            # pas de recommandation : rien à suivre
    a = it.record_feedback(c, 1, 5, 2, 'PLA', '/m.stl', 'Std', '', 'Std')
    b = it.record_feedback(c, 1, 6, 2, 'PLA', '/m.stl', 'Std', '', 'Autre')
    assert a and b
    assert it.finish_feedback(c, 5, 'success') == 1 and it.finish_feedback(c, 6, 'failed') == 1
    fb = {f['followed']: f for f in it.load_feedback(c, 1)}
    assert fb[True]['result'] == 'success' and fb[False]['result'] == 'failed'
    assert it.finish_feedback(c, 5, 'success') == 0                                         # déjà clos : rien ne change


@pytest.fixture
def client(tmp_path):
    pf = _load('production_flow')
    db = str(tmp_path / 't.db')
    c0 = sqlite3.connect(db)
    c0.execute("CREATE TABLE print_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, file_path TEXT, file_name TEXT, file_size INT, file_ext TEXT, slicer TEXT, source_platform TEXT, slicer_profile_name TEXT, printer_id INT, filament_material TEXT, result TEXT DEFAULT '', rated_at TEXT, slicer_profile_id TEXT, failure_reason TEXT, sent_at TEXT)")
    c0.execute("CREATE TABLE printers (id INTEGER PRIMARY KEY, user_id INT, name TEXT, type TEXT)")
    c0.execute("INSERT INTO printers VALUES (2, 1, 'Voron', 'klipper')")
    c0.commit()
    c0.close()

    def get_db():
        c = sqlite3.connect(db)
        c.row_factory = sqlite3.Row
        return c

    app = flask.Flask('t')
    app.secret_key = 'x'
    sent = []
    ns = {n: (lambda *a, **k: None) for n in pf._REQUIRED}
    ns.update(app=app, get_db=get_db, jsonify=flask.jsonify, login_required=lambda f: f, request=flask.request, session=flask.session,
              app_logger=type('L', (), {'info': lambda *a, **k: None, 'debug': lambda *a, **k: None, 'error': lambda *a, **k: None})(),
              _is_path_within_sources=lambda p, u: True, parse_printer_config=lambda r: dict(r),
              _printer_status_cached=lambda p: {'status': 'idle'},
              printer_hub=type('H', (), {'upload_file': lambda self, p, f: sent.append(f) or True})())
    pf.init(ns)
    f = tmp_path / 'piece.gcode'
    f.write_text('G1 X0')
    c = app.test_client()
    with c.session_transaction() as s:
        s['user_id'] = 1
    # un run « proposé » écrit directement (la proposition complète dépend de tout main.py, testée à part)
    import json
    conn = get_db()
    pf._ensure(conn)
    prop = {'candidates': [{'printer_id': 2, 'printer_name': 'Voron', 'resin': False, 'profile': 'Std', 'profile_fp': ''}], 'chosen': {'printer_id': 2}}
    conn.execute("INSERT INTO production_runs (user_id, file_path, file_name, material, status, printer_id, printer_name, profile, proposal_json, created_at) VALUES (1,?,?,?,?,?,?,?,?,1)",
                 (str(f), 'piece.gcode', 'PLA', 'proposed', 2, 'Voron', 'Std', json.dumps(prop)))
    conn.commit()
    conn.close()
    return c, pf, sent, get_db


def test_envoi_refuse_sans_validation_humaine(client):
    c, pf, sent, _ = client
    r = c.post('/api/production/1/send')
    assert r.status_code == 409 and r.get_json()['error'] == 'not_validated' and sent == []


def test_validation_puis_envoi_puis_resultat(client):
    c, pf, sent, get_db = client
    assert c.post('/api/production/1/validate', json={'printer_id': 99}).status_code == 400
    assert c.post('/api/production/1/validate', json={'printer_id': 2}).get_json()['status'] == 'validated'
    r = c.post('/api/production/1/send').get_json()
    assert r['status'] == 'sent' and len(sent) == 1 and r['history_id']
    pf.on_print_event({'event': 'finished', 'printer': {'id': 2, 'name': 'Voron'}, 'file': '/gcodes/PIECE.gcode', 'ts': 1})
    conn = get_db()
    assert conn.execute("SELECT status FROM production_runs WHERE id=1").fetchone()[0] == 'finished'
    assert conn.execute("SELECT result FROM print_history WHERE id=?", (r['history_id'], )).fetchone()[0] == 'success'
    assert conn.execute("SELECT followed, result FROM intel_feedback WHERE run_id=1").fetchone()[:] == (1, "success")


def test_echec_d_envoi_ne_marque_pas_envoye(client):
    c, pf, sent, get_db = client
    c.post('/api/production/1/validate', json={'printer_id': 2})
    pf.printer_hub = type('H', (), {'upload_file': lambda self, p, f: False})()
    r = c.post('/api/production/1/send')
    assert r.status_code == 502
    assert get_db().execute("SELECT status FROM production_runs WHERE id=1").fetchone()[0] == 'send_failed'


def test_resultat_manuel_et_annulation(client):
    c, pf, sent, get_db = client
    assert c.post('/api/production/1/result', json={'result': 'success'}).status_code == 409      # pas encore envoyé
    c.post('/api/production/1/validate', json={'printer_id': 2})
    c.post('/api/production/1/send')
    assert c.post('/api/production/1/result', json={'result': 'oups'}).status_code == 400
    assert c.post('/api/production/1/result', json={'result': 'failed'}).get_json()['status'] == 'failed'
    assert c.post('/api/production/1/cancel').status_code == 409


def test_proposition_complete_classe_et_controle(client, tmp_path):
    c, pf, sent, get_db = client
    g = tmp_path / 'ok.gcode'
    g.write_text('G1')
    r = c.post('/api/production/propose', json={'file_path': str(g), 'material': 'PLA'}).get_json()
    assert r['status'] == 'proposed' and r['printer_id'] == 2
    assert r['proposal']['chosen']['printer_name'] == 'Voron' and not r['proposal']['blocked']
    stl = tmp_path / 'm.stl'
    stl.write_text('solid')
    b = c.post('/api/production/propose', json={'file_path': str(stl)}).get_json()
    assert b['proposal']['blocked'] and b['proposal']['chosen'] is None           # un maillage brut ne peut pas partir : il faut le découper
    assert c.post('/api/production/propose', json={'file_path': str(tmp_path / 'absent.gcode')}).status_code == 404
