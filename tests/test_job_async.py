"""1.2.2 : traitements lourds des plugins en tâche de fond (job_manager.run_view_async)."""
import importlib.util, logging, os, time
import pytest
flask = pytest.importorskip('flask')
from conftest import ROOT


def _jm():
    spec = importlib.util.spec_from_file_location('job_manager_async_t', os.path.join(ROOT, 'modules', 'job_manager.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    app = flask.Flask('t'); app.secret_key = 'k'
    m.init(dict(app=app, app_logger=logging.getLogger('t'), jsonify=flask.jsonify, login_required=lambda f: f, request=flask.request, session=flask.session))
    return app, m


def _wait(c, jid, timeout=10):
    t = time.time()
    while time.time() - t < timeout:
        d = c.get('/api/jobs/' + jid).get_json()
        if d['state'] in ('done', 'failed', 'cancelled'):
            return d
        time.sleep(0.05)
    raise AssertionError('tâche trop longue')


def _client(app):
    c = app.test_client()
    with c.session_transaction() as s:
        s['user_id'] = 7; s['role'] = 'owner'
    return c


def test_vue_executee_en_tache_de_fond_avec_la_session_et_le_corps():
    app, m = _jm()

    @app.route('/api/x/demo/run', methods=['POST'])
    def run():
        d = flask.request.get_json()
        return flask.jsonify({'echo': d, 'uid': flask.session.get('user_id'), 'role': flask.session.get('role')}), 201

    @app.route('/api/x/demo/start', methods=['POST'])
    def start():
        return m.run_view_async('demo', run)
    c = _client(app)
    r = c.post('/api/x/demo/start', json={'a': 1, 'async': True})
    assert r.status_code == 202 and r.get_json()['async']
    d = _wait(c, r.get_json()['job_id'])
    assert d['state'] == 'done' and d['result']['status'] == 201
    assert d['result']['body'] == {'echo': {'a': 1}, 'uid': 7, 'role': 'owner'}            # drapeau async retiré, session rejouée


def test_erreur_de_la_vue_remontee_dans_le_resultat():
    app, m = _jm()

    @app.route('/api/x/demo/start', methods=['POST'])
    def start():
        return m.run_view_async('demo', lambda: (flask.jsonify({'error': 'boom'}), 400))
    c = _client(app)
    d = _wait(c, c.post('/api/x/demo/start', json={}).get_json()['job_id'])
    assert d['state'] == 'done' and d['result']['status'] == 400 and d['result']['body']['error'] == 'boom'


def test_tache_visible_seulement_par_son_proprietaire():
    app, m = _jm()

    @app.route('/api/x/demo/start', methods=['POST'])
    def start():
        return m.run_view_async('demo', lambda: flask.jsonify({}))
    c = _client(app)
    jid = c.post('/api/x/demo/start', json={}).get_json()['job_id']
    other = app.test_client()
    with other.session_transaction() as s:
        s['user_id'] = 99
    assert other.get('/api/jobs/' + jid).status_code == 404
