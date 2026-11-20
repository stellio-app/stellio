"""1.1.7 — démo publique : tout se consulte (lecture seule), rien ne s'écrit ; hors démo un invité reste refusé."""
import importlib.util, io, logging, os, re
import pytest
flask = pytest.importorskip('flask')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODS = 'job_manager audit_log access_control compat auto_organize model_diff shape_search plugins fab_assistant license_watch library_sync public_api webhooks plate_studio'.split()


def _load(name):
    spec = importlib.util.spec_from_file_location(name + '_t', __import__('conftest').mod_path(name))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def _app(m, demo, **extra):
    app = flask.Flask('d'); app.secret_key = 'x'
    ns = dict(app=app, app_logger=logging.getLogger('t'), jsonify=flask.jsonify, login_required=lambda f: f, request=flask.request, session=flask.session,
              IS_DEMO=demo, send_file=flask.send_file, _is_path_within_sources=lambda p, uid: True)
    ns.update(extra)
    for n in m._REQUIRED:
        ns.setdefault(n, None if n not in ('DATA_DIR',) else '/tmp')
    m.init(ns)
    cl = app.test_client()
    with cl.session_transaction() as s: s['user_id'] = 1; s['role'] = 'viewer'
    return cl


def test_chaque_module_connait_la_demo():
    for n in MODS:
        s = open(__import__('conftest').mod_path(n), encoding='utf-8').read()
        assert 'def _demo_ok' in s and "_MAIN.get('IS_DEMO')" in s, n


def test_ecriture_refusee_meme_en_demo_et_lecture_refusee_hors_demo():
    j = _load('job_manager')
    cl = _app(j, True)
    assert cl.get('/api/jobs').status_code == 200
    assert cl.post('/api/jobs/abc/cancel').status_code == 403                      # une écriture reste interdite en démo
    j2 = _load('job_manager'); cl2 = _app(j2, False)
    assert cl2.post('/api/jobs/abc/cancel').status_code == 403


def test_demo_plateau_calcul_oui_export_non(tmp_path):
    trimesh = pytest.importorskip('trimesh')
    trimesh.creation.box(extents=(20, 20, 5)).export(str(tmp_path / 'a.stl'))
    p = _load('plate_studio'); cl = _app(p, True)
    r = cl.post('/api/plate/arrange', json={'paths': [str(tmp_path / 'a.stl')]}); assert r.status_code == 200 and r.get_json()['ok']
    assert cl.post('/api/plate/export', json={'paths': [str(tmp_path / 'a.stl')]}).status_code == 403     # pas de récupération de fichiers
    p2 = _load('plate_studio'); cl2 = _app(p2, False)
    assert cl2.post('/api/plate/arrange', json={'paths': [str(tmp_path / 'a.stl')]}).status_code == 403   # invité ordinaire : toujours refusé


def test_audit_demo_masque_ip_et_acteurs_et_csv_ferme():
    import sqlite3
    a = _load('audit_log')
    db = sqlite3.connect(':memory:', check_same_thread=False); db.row_factory = sqlite3.Row
    class C:
        def __getattr__(s, n): return getattr(db, n)
        def close(s): pass
    cl = _app(a, True, get_db=lambda: C())
    a.ensure(db)
    db.execute("INSERT INTO audit_log (ts, owner_id, actor, actor_kind, action, target, method, path, status, ip, remote) VALUES (1,1,'romain','user','token.create','x','POST','/api/tokens',200,'203.0.113.9',1)"); db.commit()
    r = cl.get('/api/audit'); assert r.status_code == 200
    rows = r.get_json()['rows']; assert rows and all(x['ip'] == '' and x['actor'] == '—' for x in rows)
    assert cl.get('/api/audit/export.csv').status_code == 403


def test_boutons_et_demo_cote_interface():
    js = open(os.path.join(ROOT, 'interface', 'suite.js'), encoding='utf-8').read()
    assert 'IS_VIEWER && !window.STELLIO_DEMO' in js
    main = open(os.path.join(ROOT, 'main.py'), encoding='utf-8').read()
    assert "('POST', '/api/model-diff')" in main


def test_demo_plateau_controle_pur_ouvert_export_ferme(tmp_path):
    trimesh = pytest.importorskip('trimesh')
    trimesh.creation.box(extents=(20, 20, 5)).export(str(tmp_path / 'a.stl'))
    lay = {'plate': {'w': 100, 'd': 100, 'z': 50}, 'plates': [{'index': 1, 'placements': [{'id': str(tmp_path / 'a.stl'), 'x': 0, 'y': 0, 'w': 20, 'd': 20, 'h': 5, 'rot': 0}]}]}
    p = _load('plate_studio'); cl = _app(p, True)
    assert cl.post('/api/plate/check', json=lay).get_json()['issues'] == []
    assert cl.post('/api/plate/export', json={'layout': lay}).status_code == 403
    p2 = _load('plate_studio'); assert _app(p2, False).post('/api/plate/check', json=lay).status_code == 403
