"""v1.1.8 — API publique : jetons hachés, droits lecture/écriture, révocation, journal, OpenAPI, routes /api/v1."""
import importlib.util, json, logging, os, sqlite3, sys
import pytest
flask = pytest.importorskip('flask')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _mod():
    spec = importlib.util.spec_from_file_location('public_api_t', os.path.join(ROOT, 'modules', 'public_api.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def test_pures():
    m = _mod()
    t, pre = m.make_token()
    assert t.startswith('stl_') and len(t) == 44 and pre == t[:8]
    assert m.hash_token(t) == m.hash_token(t) != t and len(m.hash_token(t)) == 64
    assert m.parse_bearer('Bearer ' + t) == t and m.parse_bearer('bearer ' + t) == t
    assert m.parse_bearer('') == '' and m.parse_bearer('Basic abc') == '' and m.parse_bearer('Bearer abc') == ''
    assert m.perm_allows('read', 'GET') and not m.perm_allows('read', 'POST') and m.perm_allows('write', 'PATCH') and not m.perm_allows('x', 'GET')
    assert m._clean({'a': 1, 'api_key': 'x', 'n': {'password': 'p', 'ok': 2}}) == {'a': 1, 'n': {'ok': 2}}


def test_openapi_couvre_les_routes():
    m = _mod()
    spec = m.build_openapi('1.1.8')
    assert spec['openapi'].startswith('3.') and spec['info']['version'] == '1.1.8'
    pairs = {(p, meth.upper()) for p, ops in spec['paths'].items() for meth in ops}
    assert pairs == {(r[0], r[1]) for r in m.PUBLIC_ROUTES}
    assert all(p.startswith('/api/v1/') for p, _ in pairs)
    assert len({r[2] for r in m.PUBLIC_ROUTES}) == len(m.PUBLIC_ROUTES)    # un point d'entrée par route


class _Hub:
    def get_status(self, p):
        return {'status': 'printing', 'progress': 42, 'api_key': 'secret', 'filename': 'a.gcode'}


def _env(tmp_path, as_user=1):
    m = _mod()
    db = str(tmp_path / 't.db')

    def get_db():
        c = sqlite3.connect(db); c.row_factory = sqlite3.Row; return c
    c = get_db()
    c.execute("CREATE TABLE printers (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, type TEXT, is_connected INTEGER, total_print_hours REAL, api_key TEXT)")
    c.execute("INSERT INTO printers VALUES (1, 1, 'Prusa', 'prusalink', 1, 12.5, 'SECRET')")
    c.execute("INSERT INTO printers VALUES (2, 2, 'Autre', 'klipper', 0, 0, 'S2')")
    c.execute("CREATE TABLE print_jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, quote_id INTEGER, client TEXT, part TEXT, quantity INTEGER, "
              "qty_done INTEGER, material TEXT, printer_id INTEGER, due_date TEXT, status TEXT, notes TEXT, created_at TEXT, done_at TEXT, scrap INTEGER, est_hours REAL)")
    c.execute("INSERT INTO print_jobs (user_id, part, quantity, qty_done, status, scrap) VALUES (2, 'Pas à moi', 1, 0, 'queued', 0)")
    c.execute("CREATE TABLE manual_filament_spools (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT NOT NULL, material TEXT DEFAULT '', "
              "color_hex TEXT DEFAULT '#888888', remaining_g REAL, capacity_g REAL DEFAULT 1000, source_label TEXT DEFAULT 'Manuel', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    c.execute("INSERT INTO manual_filament_spools (user_id, name, remaining_g) VALUES (2, 'Autre bobine', 500)")
    c.execute("CREATE TABLE projects (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT NOT NULL, description TEXT DEFAULT '', color TEXT DEFAULT '#4ea1d3', "
              "status TEXT DEFAULT 'in_progress', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    c.execute("INSERT INTO projects (user_id, name) VALUES (2, 'Projet autre')")
    c.commit(); c.close()
    app = flask.Flask('t'); app.secret_key = 'x'
    sess = {'user_id': 1}
    cache = {'files': [{'path': '/src/a.stl', 'name': 'a.stl', 'size': 5, 'type': 'stl', 'ext': '.stl', 'mtime': 10},
                       {'path': '/src/b.3mf', 'name': 'b.3mf', 'size': 7, 'type': '3mf', 'ext': '.3mf', 'mtime': 20},
                       {'path': '/ailleurs/c.stl', 'name': 'c.stl', 'size': 1, 'type': 'stl', 'ext': '.stl', 'mtime': 30}]}
    services = dict(app=app, app_logger=logging.getLogger('t'), get_db=get_db, jsonify=flask.jsonify, login_required=lambda f: f,
                    request=flask.request, session=flask.session, _is_path_within_sources=lambda p, uid: str(p).startswith('/src/'),
                    parse_printer_config=lambda row: dict(row), printer_hub=_Hub(), _read_cache_json_safe=lambda: cache, CURRENT_VERSION='1.1.8')
    m.init(services)
    m._fails.clear()
    cl = app.test_client()
    with cl.session_transaction() as s:
        s['user_id'] = 1
    return m, cl, get_db


def _mk(cl, name='mon-script', perm='read'):
    r = cl.post('/api/tokens', json={'name': name, 'perm': perm})
    assert r.status_code == 200
    return r.get_json()


def H(t):
    return {'Authorization': 'Bearer ' + t}


def test_jeton_affiche_une_fois_et_stocke_hache(tmp_path):
    m, cl, db = _env(tmp_path)
    j = _mk(cl)
    assert j['token'].startswith('stl_')
    lst = cl.get('/api/tokens').get_json()['tokens']
    assert len(lst) == 1 and 'token' not in lst[0] and 'token_hash' not in lst[0] and lst[0]['prefix'] == j['token'][:8]
    row = db().execute("SELECT token_hash FROM api_tokens").fetchone()
    assert row[0] == m.hash_token(j['token']) and j['token'] not in json.dumps(dict(row))


def test_creation_validations_et_plafond(tmp_path):
    m, cl, _ = _env(tmp_path)
    assert cl.post('/api/tokens', json={'name': '', 'perm': 'read'}).status_code == 400
    assert cl.post('/api/tokens', json={'name': 'x', 'perm': 'admin'}).status_code == 400
    for i in range(m.MAX_ACTIVE_TOKENS):
        _mk(cl, f't{i}')
    assert cl.post('/api/tokens', json={'name': 'de trop', 'perm': 'read'}).status_code == 400


def test_lecture_ok_sans_jeton_401_ecriture_refusee_en_lecture(tmp_path):
    m, cl, _ = _env(tmp_path)
    anon = flask.Flask('x').test_client()
    assert cl.application.test_client().get('/api/v1/files').status_code == 401          # sans en-tête (pas même la session)
    r = _mk(cl, perm='read')['token']
    assert cl.application.test_client().get('/api/v1/me', headers=H(r)).get_json()['permission'] == 'read'
    c2 = cl.application.test_client()
    assert c2.post('/api/v1/tasks', json={'part': 'x'}, headers=H(r)).status_code == 403
    w = _mk(cl, perm='write')['token']
    assert c2.post('/api/v1/tasks', json={'part': 'x'}, headers=H(w)).status_code == 201


def test_revocation_immediate(tmp_path):
    m, cl, _ = _env(tmp_path)
    j = _mk(cl)
    c2 = cl.application.test_client()
    assert c2.get('/api/v1/me', headers=H(j['token'])).status_code == 200
    assert cl.delete(f"/api/tokens/{j['id']}").status_code == 200
    assert c2.get('/api/v1/me', headers=H(j['token'])).status_code == 401
    assert cl.delete(f"/api/tokens/{j['id']}").status_code == 404
    assert cl.get('/api/tokens').get_json()['tokens'][0]['revoked_at']


def test_fichiers_filtres_et_limites_aux_sources(tmp_path):
    m, cl, _ = _env(tmp_path)
    t = _mk(cl)['token']; c2 = cl.application.test_client()
    d = c2.get('/api/v1/files', headers=H(t)).get_json()
    assert [f['name'] for f in d['files']] == ['b.3mf', 'a.stl']          # c.stl hors sources, plus récent d'abord
    assert [f['name'] for f in c2.get('/api/v1/files?type=stl', headers=H(t)).get_json()['files']] == ['a.stl']
    assert c2.get('/api/v1/files?q=b.&limit=1', headers=H(t)).get_json()['count'] == 1
    assert c2.get('/api/v1/files?offset=1', headers=H(t)).get_json()['files'][0]['name'] == 'a.stl'


def test_imprimantes_isolees_et_secrets_absents(tmp_path):
    m, cl, _ = _env(tmp_path)
    t = _mk(cl)['token']; c2 = cl.application.test_client()
    ps = c2.get('/api/v1/printers', headers=H(t)).get_json()['printers']
    assert [p['name'] for p in ps] == ['Prusa'] and 'SECRET' not in json.dumps(ps)
    st = c2.get('/api/v1/printers/1/status', headers=H(t)).get_json()
    assert st['state']['status'] == 'printing' and 'api_key' not in st['state']
    assert c2.get('/api/v1/printers/2/status', headers=H(t)).status_code == 404


def test_taches_cycle_complet_et_isolation(tmp_path):
    m, cl, _ = _env(tmp_path)
    w = _mk(cl, perm='write')['token']; c2 = cl.application.test_client()
    r = c2.post('/api/v1/tasks', json={'part': 'Clip', 'quantity': 10, 'client': 'Zoé', 'est_hours': 0.5}, headers=H(w))
    tid = r.get_json()['id']
    assert r.get_json()['status'] == 'queued' and r.get_json()['quantity'] == 10
    assert c2.post('/api/v1/tasks', json={'quantity': 3}, headers=H(w)).status_code == 400
    u = c2.patch(f'/api/v1/tasks/{tid}', json={'qty_done': 10, 'status': 'done'}, headers=H(w)).get_json()
    assert u['qty_done'] == 10 and u['status'] == 'done' and u['done_at']
    assert c2.patch(f'/api/v1/tasks/{tid}', json={'status': 'nimporte'}, headers=H(w)).status_code == 400
    assert c2.patch(f'/api/v1/tasks/{tid}', json={}, headers=H(w)).status_code == 400
    assert [t['part'] for t in c2.get('/api/v1/tasks', headers=H(w)).get_json()['tasks']] == ['Clip']      # la tâche de l'utilisateur 2 est invisible
    assert c2.get('/api/v1/tasks/1', headers=H(w)).status_code == 404
    assert c2.patch('/api/v1/tasks/1', json={'qty_done': 1}, headers=H(w)).status_code == 404
    assert len(c2.get('/api/v1/tasks?status=done', headers=H(w)).get_json()['tasks']) == 1


def test_journal_acces_et_erreurs(tmp_path):
    m, cl, _ = _env(tmp_path)
    t = _mk(cl, 'ci')['token']; c2 = cl.application.test_client()
    c2.get('/api/v1/me', headers=H(t))
    c2.get('/api/v1/me', headers=H('Bearer pas-un-jeton'))
    c2.get('/api/v1/tasks/999', headers=H(t))
    log = cl.get('/api/tokens/log').get_json()['log']
    assert {(x['path'], x['status']) for x in log} >= {('/api/v1/me', 200), ('/api/v1/me', 401), ('/api/v1/tasks/999', 404)}
    assert any(x['token_name'] == 'ci' for x in log)
    errs = cl.get('/api/tokens/log?errors=1').get_json()['log']
    assert errs and all(x['status'] >= 400 for x in errs)
    assert t not in json.dumps(log)


def test_limite_de_tentatives(tmp_path):
    m, cl, _ = _env(tmp_path)
    c2 = cl.application.test_client()
    codes = [c2.get('/api/v1/me', headers={'Authorization': 'Bearer stl_' + 'a' * 40}).status_code for _ in range(m.FAIL_LIMIT + 2)]
    assert codes[0] == 401 and codes[-1] == 429


def test_openapi_et_docs_publics(tmp_path):
    m, cl, _ = _env(tmp_path)
    c2 = cl.application.test_client()
    spec = c2.get('/api/v1/openapi.json').get_json()
    assert spec['info']['version'] == '1.1.8' and '/api/v1/tasks/{id}' in spec['paths']
    assert b'/api/v1/files' in c2.get('/api/v1/docs').data


def test_compte_invite_ne_gere_pas_les_jetons(tmp_path):
    m, cl, _ = _env(tmp_path)
    with cl.session_transaction() as s:
        s['role'] = 'viewer'
    assert cl.get('/api/tokens').status_code == 403
    assert cl.post('/api/tokens', json={'name': 'x', 'perm': 'read'}).status_code == 403


def test_ecriture_bobines_et_projets(tmp_path):
    m, cl, _ = _env(tmp_path)
    r = _mk(cl, perm='read')['token']; w = _mk(cl, perm='write')['token']; c2 = cl.application.test_client()
    assert c2.post('/api/v1/materials', json={'name': 'PLA'}, headers=H(r)).status_code == 403
    assert c2.post('/api/v1/projects', json={'name': 'P'}, headers=H(r)).status_code == 403
    assert c2.post('/api/v1/materials', json={'name': ''}, headers=H(w)).status_code == 400
    assert c2.post('/api/v1/materials', json={'name': 'x', 'color_hex': 'rouge'}, headers=H(w)).status_code == 400
    assert c2.post('/api/v1/materials', json={'name': 'x', 'capacity_g': 'abc'}, headers=H(w)).status_code == 400
    b = c2.post('/api/v1/materials', json={'name': 'PETG noir', 'material': 'PETG', 'color_hex': '#111111', 'capacity_g': 750}, headers=H(w))
    assert b.status_code == 201 and b.get_json()['remaining_g'] == 750 and b.get_json()['source_label'] == 'API'
    bid = b.get_json()['id']
    assert c2.patch(f'/api/v1/materials/{bid}', json={'remaining_g': 420}, headers=H(w)).get_json()['remaining_g'] == 420
    assert c2.patch(f'/api/v1/materials/{bid}', json={'remaining_g': -5}, headers=H(w)).get_json()['remaining_g'] == 0
    assert c2.patch(f'/api/v1/materials/{bid}', json={}, headers=H(w)).status_code == 400
    assert c2.patch('/api/v1/materials/1', json={'remaining_g': 1}, headers=H(w)).status_code == 404        # bobine de l'utilisateur 2
    assert [x['name'] for x in c2.get('/api/v1/materials', headers=H(r)).get_json()['materials']] == ['PETG noir']
    p = c2.post('/api/v1/projects', json={'name': 'Boîtier', 'description': 'v2'}, headers=H(w))
    assert p.status_code == 201 and p.get_json()['status'] == 'in_progress'
    pid = p.get_json()['id']
    assert c2.patch(f'/api/v1/projects/{pid}', json={'status': 'done'}, headers=H(w)).get_json()['status'] == 'done'
    assert c2.patch(f'/api/v1/projects/{pid}', json={'status': 'nimporte'}, headers=H(w)).status_code == 400
    assert c2.patch('/api/v1/projects/1', json={'name': 'vol'}, headers=H(w)).status_code == 404
    # un jeton limité aux « tasks » ne peut pas écrire les bobines
    lim = cl.post('/api/tokens', json={'name': 'lim', 'perm': 'write', 'scopes': ['tasks']}).get_json()['token']
    assert c2.post('/api/v1/materials', json={'name': 'z'}, headers=H(lim)).status_code == 403
