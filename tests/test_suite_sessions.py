"""1.1.7 — sessions actives : suivi, liste, révocation, invités refusés, jamais bloquant."""
import importlib.util, logging, os, sqlite3, time
import pytest
flask = pytest.importorskip('flask')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _env(tmp_path):
    spec = importlib.util.spec_from_file_location('session_manager_t', os.path.join(ROOT, 'modules', 'session_manager.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    db = str(tmp_path / 's.db')
    def get_db():
        c = sqlite3.connect(db); c.row_factory = sqlite3.Row; return c
    app = flask.Flask('s'); app.secret_key = 'k'
    m.init(dict(app=app, app_logger=logging.getLogger('t'), get_db=get_db, jsonify=flask.jsonify, login_required=lambda f: f, request=flask.request, session=flask.session))
    @app.route('/api/ping')
    def ping(): return flask.jsonify({'ok': True})
    @app.route('/static/x.js')
    def st(): return 'x'
    return m, app, get_db


def _login(app, uid=1, role='user', **kw):
    cl = app.test_client()
    with cl.session_transaction() as s:
        s['user_id'] = uid; s['role'] = role; s.update(kw)
    return cl


def test_suivi_liste_et_revocation(tmp_path):
    m, app, db = _env(tmp_path)
    a, b = _login(app), _login(app)
    assert a.get('/api/ping').status_code == 200 and b.get('/api/ping', headers={'User-Agent': 'Firefox'}).status_code == 200
    ls = a.get('/api/sessions').get_json(); assert len(ls['sessions']) == 2 and sum(1 for x in ls['sessions'] if x['current']) == 1
    other = next(x['sid'] for x in ls['sessions'] if not x['current'])
    assert a.post(f'/api/sessions/{other}/revoke').get_json()['ok']
    # la session révoquée est coupée à la relecture suivante (on force l'échéance de contrôle)
    with b.session_transaction() as s: s['sid_chk'] = 0
    r = b.get('/api/ping'); assert r.status_code == 401 and r.get_json()['code'] == 'session_revoked'
    assert b.get('/api/ping').status_code in (200, 401)                       # la session est vidée : plus de suivi
    assert a.post(f'/api/sessions/{other}/revoke').status_code == 404
    assert a.post('/api/sessions/inconnue/revoke').status_code == 404


def test_revoquer_les_autres_et_delai(tmp_path):
    m, app, db = _env(tmp_path)
    cs = [_login(app) for _ in range(3)]
    for i, c in enumerate(cs): c.get('/api/ping', headers={'User-Agent': f'Appareil {i}'})          # trois appareils distincts
    assert cs[0].post('/api/sessions/revoke-others').get_json()['revoked'] == 2
    with cs[1].session_transaction() as s: s['sid_chk'] = time.time()          # contrôle récent : pas de relecture avant l'échéance
    assert cs[1].get('/api/ping').status_code == 200
    with cs[1].session_transaction() as s: s['sid_chk'] = 0
    assert cs[1].get('/api/ping').status_code == 401 and cs[0].get('/api/ping').status_code == 200


def test_invites_statiques_et_non_bloquant(tmp_path):
    m, app, db = _env(tmp_path)
    g = _login(app, role='viewer', viewer_id=5)
    assert g.get('/api/ping').status_code == 200
    assert g.get('/api/sessions').status_code == 403 and g.post('/api/sessions/revoke-others').status_code == 403
    c = db(); n = c.execute("SELECT COUNT(*) FROM active_sessions WHERE kind='viewer'").fetchone()[0]; assert n == 1
    anon = app.test_client(); assert anon.get('/api/ping').status_code == 200                                   # sans session : aucun suivi
    u = _login(app); u.get('/static/x.js')
    c = db(); assert c.execute("SELECT COUNT(*) FROM active_sessions WHERE kind='user'").fetchone()[0] == 0     # hors /api/ : pas de suivi
    m.get_db = lambda: (_ for _ in ()).throw(RuntimeError('base cassée'))
    assert u.get('/api/ping').status_code == 200                                                                # une panne de suivi ne bloque jamais


def test_requetes_simultanees_d_un_meme_navigateur_partagent_une_session(tmp_path):
    """Régression (vue sur le vrai serveur) : au chargement d'une page, ~30 requêtes partent en parallèle sans session suivie ; il ne doit y avoir qu'UNE ligne."""
    import threading
    m, app, db = _env(tmp_path)
    sids, errs = [], []
    def go():
        try:
            c = db(); sids.append(m.register(c, 1, 'user', None, '10.0.0.1', 'Firefox', time.time())); c.close()
        except Exception as e: errs.append(e)
    ts = [threading.Thread(target=go) for _ in range(30)]; [t.start() for t in ts]; [t.join() for t in ts]
    assert not errs and len(set(sids)) == 1 and db().execute("SELECT COUNT(*) FROM active_sessions").fetchone()[0] == 1
    c = db(); other = m.register(c, 1, 'user', None, '10.0.0.2', 'Firefox', time.time()); c.close()           # autre adresse : autre appareil
    assert other != sids[0]
    c = db(); late = m.register(c, 1, 'user', None, '10.0.0.1', 'Firefox', time.time() + m.MERGE_WINDOW + 5); c.close()   # plus tard : nouvelle session
    assert late != sids[0]
    c = db(); guest = m.register(c, 1, 'viewer', 7, '10.0.0.1', 'Firefox', time.time()); c.close(); assert guest != sids[0]


def test_navigateur_qui_charge_une_page_n_enregistre_qu_une_session(tmp_path):
    m, app, db = _env(tmp_path)
    cs = [_login(app) for _ in range(8)]                                  # 8 « requêtes parallèles » sans cookie de session suivie
    for c in cs: c.get('/api/ping', headers={'User-Agent': 'Chrome'})
    assert db().execute("SELECT COUNT(*) FROM active_sessions").fetchone()[0] == 1
