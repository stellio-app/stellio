"""1.1.7 — blocs C et D : API v1 étendue et portée des jetons, journal d'audit, rôles / permissions / espaces de travail."""
import importlib.util, json, logging, os, sqlite3, time
import pytest
flask = pytest.importorskip('flask')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _mod(name):
    spec = importlib.util.spec_from_file_location(name + '_t', os.path.join(ROOT, 'modules', name + '.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _services(app, get_db, **extra):
    return dict(app=app, app_logger=logging.getLogger('t'), get_db=get_db, jsonify=flask.jsonify, login_required=lambda f: f,
                request=flask.request, session=flask.session, **extra)


def _db(tmp_path):
    path = str(tmp_path / 't.db')
    def get_db():
        c = sqlite3.connect(path); c.row_factory = sqlite3.Row; return c
    return get_db


# ───────── API v1 : portée des jetons, matières, historique, projets ─────────
class _Hub:
    def get_status(self, cfg): return {}


def _api_env(tmp_path):
    m = _mod('public_api'); get_db = _db(tmp_path)
    c = get_db()
    c.executescript("""
      CREATE TABLE printers (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, type TEXT, is_connected INTEGER, total_print_hours REAL, api_key TEXT);
      CREATE TABLE print_jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, part TEXT, status TEXT);
      CREATE TABLE manual_filament_spools (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, name TEXT, material TEXT, color_hex TEXT, remaining_g REAL, capacity_g REAL, source_label TEXT);
      CREATE TABLE print_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, file_name TEXT, sent_at TEXT, result TEXT, printer_id INT, filament_material TEXT,
                                  slicer TEXT, estimated_seconds REAL, actual_seconds REAL, total_cost REAL, nozzle_temp REAL, secret_col TEXT);
      CREATE TABLE projects (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, name TEXT, description TEXT, status TEXT, created_at TEXT, updated_at TEXT);
      CREATE TABLE project_files (project_id INT, file_path TEXT, quantity_needed INT, quantity_printed INT, notes TEXT, position INT);
      INSERT INTO manual_filament_spools (user_id, name, material, color_hex, remaining_g, capacity_g, source_label) VALUES (1,'Noir','PLA','#000',420,1000,'Manuel'),(2,'Autre','PETG','#fff',1,1,'x');
      INSERT INTO print_history (user_id, file_name, sent_at, result, printer_id, filament_material, nozzle_temp, secret_col) VALUES
          (1,'a.stl','2026-11-01','success',1,'PLA',215,'S'),(1,'b.stl','2026-11-02','failed',1,'PETG',240,'S'),(2,'c.stl','2026-11-03','success',9,'PLA',200,'S');
      INSERT INTO projects (user_id, name, status) VALUES (1,'Maquette','in_progress'),(2,'Secret','in_progress');
      INSERT INTO project_files VALUES (1,'/src/a.stl',4,1,'',0),(2,'/src/z.stl',1,0,'',0);
    """)
    c.commit(); c.close()
    app = flask.Flask('t'); app.secret_key = 'x'
    m.init(_services(app, get_db, _is_path_within_sources=lambda p, uid: True, parse_printer_config=lambda r: dict(r), printer_hub=_Hub(),
                     _read_cache_json_safe=lambda: {'files': []}, CURRENT_VERSION='1.1.7'))
    m._fails.clear()
    cl = app.test_client()
    with cl.session_transaction() as s:
        s['user_id'] = 1
    return m, cl


def _tok(cl, **body):
    r = cl.post('/api/tokens', json=dict({'name': 't', 'perm': 'read'}, **body)); assert r.status_code == 200, r.get_json()
    return r.get_json()


def H(t): return {'Authorization': 'Bearer ' + t['token']}


def test_portee_pure():
    m = _mod('public_api')
    assert m.parse_scopes('files, tasks ,inconnu,files') == ('files', 'tasks')
    assert m.parse_scopes('') == () and m.scope_allows((), 'files') and m.scope_allows(('tasks',), 'tasks') and not m.scope_allows(('tasks',), 'files')


def test_jeton_a_portee_limitee(tmp_path):
    m, cl = _api_env(tmp_path)
    t = _tok(cl, scopes=['materials', 'projects'])
    assert t['scopes'] == ['materials', 'projects']
    assert cl.get('/api/v1/materials', headers=H(t)).status_code == 200
    r = cl.get('/api/v1/files', headers=H(t)); assert r.status_code == 403 and r.get_json()['code'] == 'forbidden_scope'
    assert cl.get('/api/v1/history', headers=H(t)).status_code == 403
    assert cl.get('/api/v1/me', headers=H(t)).get_json()['scopes'] == ['materials', 'projects']
    full = _tok(cl)                                                          # sans portée : tout
    assert cl.get('/api/v1/files', headers=H(full)).status_code == 200 and cl.get('/api/v1/me', headers=H(full)).get_json()['scopes'] == list(m.RESOURCES)
    assert cl.post('/api/tokens', json={'name': 'x', 'perm': 'read', 'scopes': ['pirate']}).status_code == 400


def test_matieres_historique_projets_isoles_par_compte(tmp_path):
    m, cl = _api_env(tmp_path); t = _tok(cl)
    mats = cl.get('/api/v1/materials', headers=H(t)).get_json()['materials']
    assert [x['name'] for x in mats] == ['Noir'] and mats[0]['remaining_g'] == 420
    h = cl.get('/api/v1/history', headers=H(t)).get_json()['history']
    assert [x['file_name'] for x in h] == ['b.stl', 'a.stl'] and 'secret_col' not in h[0] and h[0]['nozzle_temp'] == 240
    assert [x['file_name'] for x in cl.get('/api/v1/history?result=failed', headers=H(t)).get_json()['history']] == ['b.stl']
    assert cl.get('/api/v1/history?result=nimporte', headers=H(t)).status_code == 400
    ps = cl.get('/api/v1/projects', headers=H(t)).get_json()['projects']
    assert [(p['name'], p['needed'], p['printed']) for p in ps] == [('Maquette', 4, 1)]
    d = cl.get('/api/v1/projects/1', headers=H(t)).get_json(); assert d['files'][0]['name'] == 'a.stl'
    assert cl.get('/api/v1/projects/2', headers=H(t)).status_code == 404            # projet d'un autre compte


def test_openapi_liste_les_nouvelles_routes(tmp_path):
    m, cl = _api_env(tmp_path)
    spec = m.build_openapi('1.1.7')
    for p in ('/api/v1/materials', '/api/v1/history', '/api/v1/projects', '/api/v1/projects/{id}'):
        assert p in spec['paths']


# ───────── journal d'audit ─────────
def test_audit_classification():
    a = _mod('audit_log')
    assert a.classify('POST', '/api/settings') == ('settings.change', '')
    assert a.classify('DELETE', '/api/auth/guests/12') == ('guest.delete', '12')
    assert a.classify('POST', '/api/remote-access/toggle') == ('remote_access.change', 'toggle')
    assert a.classify('POST', '/api/update/install') == ('update.run', 'install')
    assert a.classify('PATCH', '/api/v1/tasks/4') == ('api.write', 'tasks/4')
    assert a.classify('GET', '/api/settings') is None and a.classify('POST', '/api/files/analyze') is None


def test_audit_enregistre_filtre_et_exporte(tmp_path):
    a = _mod('audit_log'); get_db = _db(tmp_path); c = get_db()
    a.record(c, 1, 'romain', 'user', 'settings.change', '', 'POST', '/api/settings', 200, '1.1.1.1', False, now=100)
    a.record(c, 1, 'invite', 'viewer', 'print.send', '', 'POST', '/api/slicer/send', 200, '2.2.2.2', True, now=200)
    a.record(c, 2, 'autre', 'user', 'settings.change', '', 'POST', '/api/settings', 200, '3.3.3.3', False, now=300)
    rows = a.query(c, 1)
    assert [r['action'] for r in rows] == ['print.send', 'settings.change']            # plus récent d'abord, autre compte absent
    assert [r['actor'] for r in a.query(c, 1, action='print')] == ['invite'] and len(a.query(c, 1, remote_only=True)) == 1
    csv_text = a.to_csv(rows); assert 'acces_distant' in csv_text and 'oui' in csv_text and '2.2.2.2' in csv_text
    for i in range(a.KEEP_PER_OWNER + 20):
        a.record(c, 1, 'x', 'user', 'settings.change', '', 'POST', '/api/settings', 200, '', False, now=1000 + i)
    assert c.execute("SELECT COUNT(*) FROM audit_log WHERE owner_id=1").fetchone()[0] == a.KEEP_PER_OWNER


def test_audit_hook_journalise_les_succes_seulement(tmp_path):
    a = _mod('audit_log'); get_db = _db(tmp_path)
    app = flask.Flask('t'); app.secret_key = 'x'
    @app.route('/api/settings', methods=['POST'])
    def _ok(): return flask.jsonify({'ok': 1})
    @app.route('/api/auth/guests', methods=['POST'])
    def _ko(): return flask.jsonify({'e': 1}), 400
    a.init(_services(app, get_db))
    cl = app.test_client()
    with cl.session_transaction() as s:
        s['user_id'] = 1; s['username'] = 'romain'
    assert cl.post('/api/settings', json={'mot_de_passe': 'secret'}).status_code == 200
    assert cl.post('/api/auth/guests', json={}).status_code == 400
    r = cl.get('/api/audit').get_json()
    assert [x['action'] for x in r['rows']] == ['settings.change'] and r['rows'][0]['actor'] == 'romain'
    assert 'secret' not in json.dumps(r)                                                     # jamais de corps de requête
    r = cl.get('/api/audit/export.csv'); assert r.status_code == 200 and r.mimetype == 'text/csv'
    with cl.session_transaction() as s:
        s['role'] = 'viewer'
    assert cl.get('/api/audit').status_code == 403


# ───────── équipes et permissions ─────────
def test_regles_de_routes():
    ac = _mod('access_control')
    assert ac.match_rule('POST', '/api/printers/3/upload') == ('operator', {'printer': '3'})
    assert ac.match_rule('DELETE', '/api/printers/3') == ('admin', {'printer': '3'})
    assert ac.match_rule('PUT', '/api/projects/9/files') == ('manager', {'project': '9'})
    assert ac.match_rule('POST', '/api/settings') is None and ac.match_rule('POST', '/api/auth/guests') is None
    assert ac.match_rule('POST', '/api/tokens') is None and ac.match_rule('POST', '/api/remote-access/toggle') is None


def G(t, s, r): return {'type': t, 'subject': s, 'rank': r}


def test_decision_par_role_sans_restriction():
    ac = _mod('access_control')
    assert ac.decide('', 'operator', [], [])[0] is False and ac.decide('', 'operator', [('printer', '1')], [])[0] is False
    assert ac.decide('operator', 'operator', [('printer', '1')], [])[0] is True
    assert ac.decide('operator', 'manager', [], [])[0] is False
    assert ac.decide('manager', 'manager', [('project', '4')], [])[0] is True
    assert ac.decide('manager', 'admin', [('printer', '1')], [])[0] is False
    assert ac.decide('admin', 'admin', [('printer', '1')], [])[0] is True


def test_decision_liste_blanche_par_imprimante():
    ac = _mod('access_control'); grants = [G('printer', '1', 1)]
    assert ac.decide('operator', 'operator', [('printer', '1')], grants)[0] is True
    ok, why = ac.decide('operator', 'operator', [('printer', '2')], grants); assert not ok and 'accès' in why
    assert ac.decide('operator', 'operator', [('project', '9')], grants)[0] is True            # autre type : pas restreint
    assert ac.decide('manager', 'operator', [('printer', '1')], [G('printer', '1', -1)])[0] is False   # « none » refuse toujours
    assert ac.decide('manager', 'manager', [('printer', '1')], grants)[0] is False             # « use » ne suffit pas pour manager


def test_decision_dossiers_par_prefixe():
    ac = _mod('access_control'); grants = [G('folder', '/lib/atelier', 1)]
    assert ac.decide('operator', 'operator', [('folder', '/lib/atelier/a.stl')], grants)[0] is True
    assert ac.decide('operator', 'operator', [('folder', '/lib/atelier2/a.stl')], grants)[0] is False   # préfixe de nom ≠ sous-dossier
    assert ac.decide('operator', 'operator', [('folder', '/lib/prive/a.stl')], grants)[0] is False
    assert ac.folder_covers('C:\\lib\\x', 'C:/lib/x/y.stl')


def _team_env(tmp_path):
    ac = _mod('access_control'); get_db = _db(tmp_path); c = get_db()
    c.executescript("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, role TEXT, owner_id INT, team_role TEXT DEFAULT '');"
                    "INSERT INTO users VALUES (1,'owner','user',NULL,''),(2,'lecteur','viewer',1,''),(3,'op','viewer',1,''),(4,'etranger','viewer',99,'');")
    c.commit(); c.close()
    app = flask.Flask('t'); app.secret_key = 'x'
    @app.route('/api/slicer/send', methods=['POST'])
    def _send(): return 'x'
    ac.init(_services(app, get_db))
    return ac, app, get_db


def test_routes_equipe_et_decision_bout_en_bout(tmp_path):
    ac, app, get_db = _team_env(tmp_path)
    owner = app.test_client()
    with owner.session_transaction() as s: s['user_id'] = 1
    assert owner.put('/api/team/members/3/role', json={'role': 'operator'}).status_code == 200
    assert owner.put('/api/team/members/3/role', json={'role': 'roi'}).status_code == 400
    assert owner.put('/api/team/members/4/role', json={'role': 'admin'}).status_code == 404       # invité d'un autre propriétaire
    assert owner.post('/api/team/permissions', json={'user_id': 3, 'subject_type': 'printer', 'subject': '1', 'level': 'use'}).status_code == 200
    ws = owner.post('/api/team/workspaces', json={'name': 'Atelier A'}).get_json()['id']
    assert owner.post(f'/api/team/workspaces/{ws}/members', json={'user_id': 2, 'role': 'operator'}).status_code == 200
    assert owner.post(f'/api/team/workspaces/{ws}/items', json={'subject_type': 'printer', 'subject': '2'}).status_code == 200
    t = owner.get('/api/team').get_json()
    assert {m['username']: m['team_role'] for m in t['members']} == {'lecteur': '', 'op': 'operator'} and t['workspaces'][0]['name'] == 'Atelier A'

    def as_guest(gid):
        cl = app.test_client()
        with cl.session_transaction() as s: s['user_id'] = 1; s['role'] = 'viewer'; s['viewer_id'] = gid
        return cl
    def decision(cl, body):
        with app.test_request_context('/api/slicer/send', method='POST', json=body):
            flask.session.update(cl_sess(cl)); return ac.team_decision()
    def cl_sess(cl):
        with cl.session_transaction() as s: return dict(s)
    op = as_guest(3)
    assert decision(op, {'printer_id': 1}) is True                    # opérateur autorisé sur l'imprimante 1
    assert isinstance(decision(op, {'printer_id': 5}), str)           # imprimante hors de ses accès
    guest = as_guest(2)
    assert decision(guest, {'printer_id': 2}) is True                 # accordé via l'espace de travail (rôle de l'espace : operator)
    assert isinstance(decision(guest, {'printer_id': 1}), str)        # l'espace restreint aussi les imprimantes
    plain = app.test_client()
    with plain.session_transaction() as s: s['user_id'] = 1; s['role'] = 'viewer'; s['viewer_id'] = 2
    assert owner.put('/api/team/members/2/role', json={'role': ''}).status_code == 200


def test_invite_sans_role_reste_en_lecture_seule(tmp_path):
    ac, app, get_db = _team_env(tmp_path)
    with app.test_request_context('/api/slicer/send', method='POST', json={'printer_id': 1}):
        flask.session.update({'viewer_id': 2, 'role': 'viewer', 'user_id': 1}); assert ac.team_decision() is None   # None = refus historique
    with app.test_request_context('/api/settings', method='POST', json={}):
        flask.session.update({'viewer_id': 3, 'role': 'viewer', 'user_id': 1}); assert ac.team_decision() is None


def test_routes_equipe_interdites_aux_invites(tmp_path):
    ac, app, get_db = _team_env(tmp_path)
    g = app.test_client()
    with g.session_transaction() as s: s['user_id'] = 1; s['role'] = 'viewer'; s['viewer_id'] = 3
    assert g.get('/api/team').status_code == 403
    assert g.put('/api/team/members/3/role', json={'role': 'admin'}).status_code == 403          # pas d'auto-promotion
    assert g.post('/api/team/permissions', json={}).status_code == 403
    assert g.get('/api/team/me').get_json()['role'] == 'viewer'


def test_main_branche_le_garde_equipe():
    src = open(os.path.join(ROOT, 'main.py'), encoding='utf-8').read()
    assert 'access_control.team_decision()' in src and src.index('access_control.team_decision()') < src.index('Écriture refusée (lecture seule)')


def test_sdk_python_contre_un_vrai_serveur_http(tmp_path):
    """Le SDK livré parle réellement à l'API (serveur WSGI local), droits et portées compris."""
    import importlib.util, threading
    from werkzeug.serving import make_server
    m, cl = _api_env(tmp_path)
    spec = importlib.util.spec_from_file_location('stellio_sdk_t', os.path.join(ROOT, 'sdk', 'python', 'stellio_sdk.py'))
    sdk = importlib.util.module_from_spec(spec); spec.loader.exec_module(sdk)
    srv = make_server('127.0.0.1', 0, cl.application, threaded=True)
    th = threading.Thread(target=srv.serve_forever, daemon=True); th.start()
    try:
        base = f'http://127.0.0.1:{srv.server_port}'
        full, narrow = _tok(cl, perm='write'), _tok(cl, scopes=['materials'])
        s = sdk.Stellio(base, full['token'])
        assert s.me() and [x['material'] for x in s.materials()] == ['PLA']
        assert [h['file_name'] for h in s.history(result='failed')] == ['b.stl'] and 'secret_col' not in s.history()[0]
        assert [p['name'] for p in s.projects()] == ['Maquette'] and s.project(1)
        with pytest.raises(sdk.StellioError) as e: s.project(2)                                  # le projet d'un autre compte reste invisible
        assert e.value.status == 404 if hasattr(e.value, 'status') else True
        n = sdk.Stellio(base, narrow['token'])
        assert n.materials()
        with pytest.raises(sdk.StellioError) as e2: n.history()
        assert getattr(e2.value, 'code', None) == 'forbidden_scope'
        with pytest.raises(sdk.StellioError): sdk.Stellio(base, 'stl_faux').me()
    finally:
        srv.shutdown(); th.join(2)


def test_role_utilisateur_simple():
    m = _mod('access_control')
    assert m.ROLES == ('user', 'operator', 'manager', 'admin')
    assert m.decide('user', 'user', [], [])[0] and not m.decide('user', 'operator', [], [])[0] and not m.decide('', 'user', [], [])[0]
    assert m.match_rule('POST', '/api/print-photos')[1] == {} and m.match_rule('POST', '/api/print-photos')[0] == 'user'
    assert m.match_rule('POST', '/api/print-history/5/rate')[0] == 'user' and m.match_rule('POST', '/api/print-history/5/cost')[0] == 'operator'
    assert not m.decide('user', 'operator', [('printer', '3')], [{'type': 'printer', 'subject': '3', 'rank': 0}])[0]      # « view » ne suffit pas
    assert m.decide('', 'user', [('printer', '3')], [{'type': 'printer', 'subject': '3', 'rank': 1}])[0]                    # un accès « use » suffit


def test_audit_pagination_et_total(tmp_path):
    """Le journal s'affiche par petites pages : `limit` + `offset`, et le total sert au sélecteur de pages."""
    a = _mod('audit_log'); get_db = _db(tmp_path)
    app = flask.Flask('t'); app.secret_key = 'x'
    a.init(_services(app, get_db))
    c = get_db()
    for i in range(30):
        a.record(c, 1, 'romain', 'user', 'settings.change', str(i), 'POST', '/api/settings', 200, '', i % 10 == 0, now=1000 + i)
    a.record(c, 2, 'autre', 'user', 'settings.change', '', 'POST', '/api/settings', 200, '', False, now=5000)
    c.commit()
    assert a.count(c, 1) == 30 and a.count(c, 1, remote_only=True) == 3
    p1, p2 = a.query(c, 1, limit=25), a.query(c, 1, limit=25, offset=25)
    assert len(p1) == 25 and len(p2) == 5 and p1[0]['target'] == '29' and p2[-1]['target'] == '0'   # plus récent d'abord, pages contiguës
    cl = app.test_client()
    with cl.session_transaction() as s:
        s['user_id'] = 1; s['username'] = 'romain'
    r = cl.get('/api/audit?limit=10&offset=20').get_json()
    assert (r['count'], r['total'], r['offset'], r['limit']) == (10, 30, 20, 10) and r['rows'][0]['target'] == '9'
    assert cl.get('/api/audit?limit=10&offset=abc').get_json()['offset'] == 0                       # paramètre invalide : première page
