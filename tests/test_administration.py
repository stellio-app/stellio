"""1.1.7 — plugin Administration : comptes et rôles, supervision d'instances (demande, acceptation, contrôle, contenu local, sortie)."""
import importlib.util, json, logging, os, sqlite3
import pytest
flask = pytest.importorskip('flask')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'bundled_plugins', 'administration', 'admin_console.py')


class Inst:
    def __init__(self, tmp, name, peer_key):
        spec = importlib.util.spec_from_file_location('admin_console_' + name, PATH)
        self.m = m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        self.db = str(tmp / f'{name}.db'); self.settings = {'instance_name': name}; self.key = peer_key; self.name = name
        c = sqlite3.connect(self.db)
        c.executescript("""CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, role TEXT, owner_id INTEGER, recovery_code_hash TEXT, team_role TEXT, created_at TEXT);
            CREATE TABLE remote_instances (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, url TEXT, peer_key TEXT, inbox_folder TEXT, last_status TEXT, last_seen_at TEXT, created_at TEXT);
            CREATE TABLE sources (id INTEGER PRIMARY KEY); CREATE TABLE printers (id INTEGER PRIMARY KEY);
            INSERT INTO users (id, username, role) VALUES (1, 'owner', 'user');
            INSERT INTO sources (id) VALUES (1), (2); INSERT INTO printers (id) VALUES (1);""")
        c.commit(); c.close()
        self.app = app = flask.Flask(name); app.secret_key = 'k'

        def get_db():
            c = sqlite3.connect(self.db); c.row_factory = sqlite3.Row; return c

        def require_peer_key(f):
            import functools
            @functools.wraps(f)
            def w(*a, **k):
                if flask.request.headers.get('X-Stellio-Peer-Key') != self.key:
                    return flask.jsonify({'error': 'clé'}), 403
                return f(*a, **k)
            return w
        m.init(dict(app=app, app_logger=logging.getLogger('t'), get_current_version=lambda: '1.1.7', get_db=get_db, hash_pw=lambda p: 'h:' + p, hash_pw_strong=lambda p: 'H:' + p,
                    jsonify=flask.jsonify, load_settings=lambda: dict(self.settings), login_required=lambda f: f, request=flask.request, require_peer_key=require_peer_key,
                    save_settings=lambda s: (self.settings.clear(), self.settings.update(s)), session=flask.session))
        # routes de cœur simulées : invités et équipe (ce que le verrou doit protéger)
        @app.route('/api/auth/guests', methods=['POST'])
        def g_create(): return flask.jsonify({'ok': True})

        @app.route('/api/team/members/<int:i>/role', methods=['PUT'])
        def g_role(i): return flask.jsonify({'ok': True})

        @app.route('/api/team', methods=['GET'])
        def team(): return flask.jsonify({'ok': True})

    def client(self, viewer=False):
        cl = self.app.test_client()
        with cl.session_transaction() as s:
            s['user_id'] = 1; s['role'] = 'viewer' if viewer else 'user'
        return cl

    def q(self, sql, *a):
        c = sqlite3.connect(self.db); r = c.execute(sql, a).fetchall(); c.commit(); c.close(); return r


@pytest.fixture
def duo(tmp_path, monkeypatch):
    a, b = Inst(tmp_path, 'principale', 'cle-a'), Inst(tmp_path, 'atelier', 'cle-b')
    a.q("INSERT INTO remote_instances (user_id, name, url, peer_key) VALUES (1, 'Atelier', 'http://b', 'cle-b')")
    b.q("INSERT INTO users (username, role, owner_id, team_role) VALUES ('alice', 'viewer', 1, '')")

    def fake(method, url, headers=None, json=None, timeout=None):
        assert url.startswith('http://b/')
        cl = b.app.test_client()
        r = cl.open(url[len('http://b'):], method=method, headers=headers or {}, json=json)

        class R:
            status_code = r.status_code
            def json(self_): return r.get_json()
        return R()
    monkeypatch.setattr(a.m.requests, 'request', fake)
    return a, b


def test_autonome_par_defaut_controle_total(duo):
    a, b = duo
    assert b.client().get('/api/admin/overview').get_json()['role'] == 'standalone'
    assert b.client().post('/api/auth/guests').status_code == 200 and b.client().put('/api/team/members/2/role').status_code == 200


def test_invite_refuse_partout(duo):
    a, b = duo
    for u in ('/api/admin/overview', '/api/admin/accounts'):
        assert a.client(viewer=True).get(u).status_code == 403
    assert a.client(viewer=True).post('/api/admin/instances/1/supervise').status_code == 403


def test_demande_acceptation_et_controle(duo):
    a, b = duo
    ca, cb = a.client(), b.client()
    assert ca.post('/api/admin/instances/1/supervise', json={'keep_local': True}).get_json()['state'] == 'pending'
    assert cb.get('/api/admin/overview').get_json()['request']['name'] == 'principale'
    assert cb.get('/api/admin/overview').get_json()['role'] == 'standalone'                  # tant qu'on n'a pas accepté : rien ne change
    assert cb.post('/api/auth/guests').status_code == 200
    assert ca.post('/api/admin/instances/1/command', json={'op': 'guest_role', 'args': {'id': 2, 'role': 'admin'}}).status_code == 404   # pas encore supervisée
    assert cb.post('/api/admin/supervision/respond', json={'accept': True, 'keep_local': True}).get_json()['state'] == 'supervised'
    st = ca.get('/api/admin/instances/1/status').get_json()
    assert st['state'] == 'supervised' and st['guests'][0]['username'] == 'alice' and 'content' not in st
    assert ca.get('/api/admin/overview').get_json()['role'] == 'primary'
    # le verrou local : écritures de comptes refusées, lecture et reste libres
    r = cb.post('/api/auth/guests'); assert r.status_code == 423 and r.get_json()['code'] == 'supervised'
    assert cb.put('/api/team/members/2/role').status_code == 423 and cb.get('/api/team').status_code == 200
    assert cb.get('/api/admin/overview').get_json()['role'] == 'supervised'
    # la principale gère les comptes à distance
    assert ca.post('/api/admin/instances/1/command', json={'op': 'guest_role', 'args': {'id': 2, 'role': 'manager'}}).get_json()['ok']
    assert b.q("SELECT team_role FROM users WHERE id=2")[0][0] == 'manager'
    assert ca.post('/api/admin/instances/1/command', json={'op': 'guest_create', 'args': {'username': 'bob', 'password': 'secret', 'role': 'operator'}}).get_json()['ok']
    assert b.q("SELECT team_role, password_hash FROM users WHERE username='bob'")[0] == ('operator', 'H:secret')
    assert ca.post('/api/admin/instances/1/command', json={'op': 'guest_role', 'args': {'id': 2, 'role': 'pirate'}}).status_code == 400
    assert ca.post('/api/admin/instances/1/command', json={'op': 'guest_delete', 'args': {'id': 2}}).get_json()['ok']
    assert ca.post('/api/admin/instances/1/command', json={'op': 'rm -rf'}).status_code == 400


def test_contenu_local_conserve_ou_partage(duo):
    a, b = duo
    ca, cb = a.client(), b.client()
    ca.post('/api/admin/instances/1/supervise', json={'keep_local': True})
    cb.post('/api/admin/supervision/respond', json={'accept': True, 'keep_local': False})            # le propriétaire local tranche à l'acceptation
    st = ca.get('/api/admin/instances/1/status').get_json()
    assert st['content'] == {'sources': 2, 'printers': 1}


def test_refus_et_sortie(duo):
    a, b = duo
    ca, cb = a.client(), b.client()
    ca.post('/api/admin/instances/1/supervise', json={})
    assert cb.post('/api/admin/supervision/respond', json={'accept': False}).get_json()['state'] == 'none'
    assert ca.get('/api/admin/instances/1/status').get_json()['released'] is True and a.q("SELECT COUNT(*) FROM supervision_links")[0][0] == 0
    ca.post('/api/admin/instances/1/supervise', json={}); cb.post('/api/admin/supervision/respond', json={'accept': True})
    assert cb.post('/api/auth/guests').status_code == 423
    assert cb.post('/api/admin/supervision/leave').get_json()['state'] == 'none'                       # échappatoire locale
    assert cb.post('/api/auth/guests').status_code == 200
    assert ca.get('/api/admin/instances/1/status').get_json()['released'] is True
    ca.post('/api/admin/instances/1/supervise', json={}); cb.post('/api/admin/supervision/respond', json={'accept': True})
    assert ca.post('/api/admin/instances/1/release').get_json()['ok'] and cb.post('/api/auth/guests').status_code == 200   # la principale libère


def test_securite_des_routes_pair(duo):
    a, b = duo
    cl = b.app.test_client()
    assert cl.post('/api/peer/supervision/request', json={'name': 'x', 'token': 'y' * 30}).status_code == 403            # sans clé d'appairage
    h = {'X-Stellio-Peer-Key': 'cle-b'}
    assert cl.post('/api/peer/supervision/request', json={'name': 'x', 'token': 'court'}, headers=h).status_code == 400
    assert cl.post('/api/peer/supervision/request', json={'name': 'x', 'token': 'y' * 30}, headers=h).status_code == 200
    assert cl.get('/api/peer/supervision/status', headers=h).get_json() == {'state': 'none'}                             # clé seule : rien de révélé
    assert cl.post('/api/peer/supervision/command', json={'op': 'guest_delete', 'args': {'id': 2}}, headers=h).status_code == 403
    b.client().post('/api/admin/supervision/respond', json={'accept': True})
    assert cl.post('/api/peer/supervision/command', json={'op': 'guest_delete', 'args': {'id': 2}}, headers={**h, 'X-Stellio-Supervisor-Token': 'z' * 30}).status_code == 403
    assert cl.post('/api/peer/supervision/release', headers={**h, 'X-Stellio-Supervisor-Token': 'y' * 30}).status_code == 200
    assert b.client().get('/api/admin/overview').get_json()['role'] == 'standalone'


def test_pas_de_cascade_ni_double_supervision(duo):
    a, b = duo
    ca, cb = a.client(), b.client()
    ca.post('/api/admin/instances/1/supervise', json={}); cb.post('/api/admin/supervision/respond', json={'accept': True})
    # une instance supervisée ne supervise personne ; une principale ne devient pas supervisée
    b.q("INSERT INTO remote_instances (user_id, name, url, peer_key) VALUES (1, 'A', 'http://a', 'cle-a')")
    assert cb.post('/api/admin/instances/1/supervise', json={}).status_code == 409
    h = {'X-Stellio-Peer-Key': 'cle-a'}
    assert a.app.test_client().post('/api/peer/supervision/request', json={'name': 'z', 'token': 'q' * 30}, headers=h).status_code == 409
    assert b.app.test_client().post('/api/peer/supervision/request', json={'name': 'z', 'token': 'q' * 30}, headers={'X-Stellio-Peer-Key': 'cle-b'}).status_code == 409


def test_instance_injoignable(duo, monkeypatch):
    a, b = duo
    def boom(*x, **k): raise OSError('down')
    monkeypatch.setattr(a.m.requests, 'request', boom)
    r = a.client().post('/api/admin/instances/1/supervise', json={})
    assert r.status_code == 502 and a.q("SELECT COUNT(*) FROM supervision_links")[0][0] == 0


def test_comptes_liste_et_verrou(duo):
    a, b = duo
    d = b.client().get('/api/admin/accounts').get_json()
    assert d['owner']['username'] == 'owner' and d['guests'][0]['username'] == 'alice' and d['locked'] is False and 'admin' in d['roles']
    a.client().post('/api/admin/instances/1/supervise', json={}); b.client().post('/api/admin/supervision/respond', json={'accept': True})
    d = b.client().get('/api/admin/accounts').get_json(); assert d['locked'] is True and d['supervisor'] == 'principale'
