"""1.1.6 — journal des connexions : enregistrement, conservation, isolation entre comptes, jamais bloquant."""
import importlib.util, logging, os, sqlite3, sys
import pytest
flask = pytest.importorskip('flask')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _mod():
    spec = importlib.util.spec_from_file_location('login_log_t', os.path.join(ROOT, 'modules', 'login_log.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _conn():
    c = sqlite3.connect(':memory:'); c.row_factory = sqlite3.Row; return c


def test_adresse_du_client():
    m = _mod()
    assert m.client_ip({'CF-Connecting-IP': '1.2.3.4'}, '127.0.0.1') == '1.2.3.4'
    assert m.client_ip({'X-Forwarded-For': '5.6.7.8, 10.0.0.1'}, '127.0.0.1') == '5.6.7.8'
    assert m.client_ip({}, '::ffff:192.168.1.5') == '192.168.1.5'


def test_enregistrement_lecture_et_resume():
    m = _mod(); c = _conn()
    assert m.record(c, 'login_ok', 'romain', 1, '1.1.1.1', 'UA', now=1000)
    assert m.record(c, 'login_fail', 'romain', 1, '2.2.2.2', 'UA', now=1100)
    assert m.record(c, 'logout', 'romain', 1, '1.1.1.1', 'UA', now=1200)
    assert not m.record(c, 'pirate', 'x', 1, '', '')                            # événement inconnu refusé
    rows = m.recent(c, 1)
    assert [r['event'] for r in rows] == ['logout', 'login_fail', 'login_ok']   # plus récent d'abord
    s = m.summary(rows, now=2000)
    assert s == {'ok': 1, 'fail': 1, 'ips': 2, 'hours': 24}
    assert m.summary(rows, now=1000 + 90000)['ok'] == 0                         # hors fenêtre de 24 h


def test_isolation_et_conservation():
    m = _mod(); c = _conn()
    m.record(c, 'login_ok', 'a', 1, '1.1.1.1', '', now=1)
    m.record(c, 'login_fail', 'inconnu', None, '9.9.9.9', '', now=2)           # nom inconnu : gardé sans propriétaire
    m.record(c, 'login_ok', 'b', 2, '3.3.3.3', '', now=3)
    assert [r['username'] for r in m.recent(c, 1)] == ['a'] and [r['username'] for r in m.recent(c, 2)] == ['b']
    for i in range(m.KEEP_PER_OWNER + 30):
        m.record(c, 'login_ok', 'a', 1, '1.1.1.1', '', now=10 + i)
    n = c.execute("SELECT COUNT(*) FROM auth_log WHERE owner_id = 1").fetchone()[0]
    assert n == m.KEEP_PER_OWNER
    assert len(m.recent(c, 1, 99999)) == m.MAX_LIMIT


def test_donnees_tronquees_et_jamais_bloquant():
    m = _mod(); c = _conn()
    m.record(c, 'login_ok', 'x' * 500, 1, '1' * 200, 'u' * 900, now=5)
    r = c.execute("SELECT username, ip, agent FROM auth_log").fetchone()
    assert len(r[0]) == 80 and len(r[1]) == 64 and len(r[2]) == 160
    c.close()
    assert m.record(c, 'login_ok', 'a', 1, '', '') is False                      # base fermée : False, pas d'exception


def _app(rows_conn, role='user', uid=1):
    m = _mod()
    app = flask.Flask('t'); app.secret_key = 'k'
    m.init(dict(app=app, app_logger=logging.getLogger('t'), get_db=lambda: rows_conn, jsonify=flask.jsonify, login_required=lambda f: f,
                request=flask.request, session=flask.session))
    cl = app.test_client()
    with cl.session_transaction() as s:
        s['user_id'] = uid; s['role'] = role
    return m, cl


def test_route_proprietaire_et_invite_refuse():
    c = _conn()
    class Keep:                      # la route ferme la connexion : on la garde ouverte pour le test
        def __getattr__(s, n): return getattr(c, n) if n != 'close' else (lambda: None)
    keep = Keep()
    m, cl = _app(keep)
    m.record(c, 'login_ok', 'romain', 1, '1.1.1.1', '')
    m.record(c, 'login_ok', 'autre', 2, '2.2.2.2', '')
    d = cl.get('/api/auth/log').get_json()
    assert [r['username'] for r in d['rows']] == ['romain'] and d['summary']['ok'] == 1
    m2, cl2 = _app(keep, role='viewer')
    assert cl2.get('/api/auth/log').status_code == 403


def test_branchements():
    main = open(os.path.join(ROOT, 'main.py'), encoding='utf-8').read()
    assert 'login_log.init(globals())' in main and "login_log.log_event('login_ok'" in main and "login_log.log_event('login_fail'" in main
    assert "login_log.log_event('logout'" in main and "@app.route('/loginlog.js')" in main
    assert "'login_log'" in open(os.path.join(ROOT, 'modules', '__init__.py')).read()
    assert '<script src="loginlog.js">' in open(os.path.join(ROOT, 'interface', 'index.html'), encoding='utf-8').read()
    for lg in ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja'):
        d = __import__('json').load(open(os.path.join(ROOT, 'languages', lg + '.json'), encoding='utf-8'))
        assert d['authlog.title'] and d['authlog.summary']
