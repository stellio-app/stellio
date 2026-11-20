"""v1.1.9 — webhooks sortants : signature HMAC, relances à délai croissant, journal, test, isolation, branchements."""
import importlib.util, json, logging, os, sqlite3, sys
import pytest
flask = pytest.importorskip('flask')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _mod():
    spec = importlib.util.spec_from_file_location('webhooks_t', __import__('conftest').mod_path('webhooks'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def test_signature_verifiable_et_rejouable_seulement_dans_la_fenetre():
    m = _mod()
    body = b'{"a":1}'
    h = m.signature_header('whsec_x', 1000, body)
    assert h.startswith('t=1000,v1=') and len(h) == len('t=1000,v1=') + 64
    assert m.verify_signature('whsec_x', h, body, now=1100)
    assert not m.verify_signature('whsec_x', h, body, now=1000 + m.TOLERANCE_S + 1)          # trop vieux : rejeu refusé
    assert not m.verify_signature('whsec_x', h, b'{"a":2}', now=1100)                      # corps modifié
    assert not m.verify_signature('autre', h, body, now=1100)                              # mauvais secret
    assert not m.verify_signature('whsec_x', 'n’importe quoi', body, now=1100)
    assert m.sign('s', 5, 'x') == m.sign('s', 5, b'x')


def test_delais_de_relance_croissants_puis_abandon():
    m = _mod()
    ds = [m.retry_delay(n) for n in range(1, m.MAX_ATTEMPTS)]
    assert ds == sorted(ds) and ds[0] == 30 and ds[-1] == 21600 and len(set(ds)) == len(ds)
    assert m.retry_delay(m.MAX_ATTEMPTS) is None


def test_validation_url_et_evenements():
    m = _mod()
    assert m.validate_url('https://exemple.fr/hook')[0] and m.validate_url('http://192.168.1.20:8123/api/webhook/x')[0]
    for bad in ('', 'ftp://x', 'javascript:alert(1)', 'https://user:pw@x.fr/', 'http://169.254.169.254/latest', 'http:///x', 'a' * 600):
        assert not m.validate_url(bad)[0], bad
    assert m.normalize_events('order.late, print.finished, inconnu, order.late') == ['print.finished', 'order.late']
    assert m.normalize_events(None) == []


def _env(tmp_path):
    m = _mod()
    db = str(tmp_path / 't.db')

    def get_db():
        c = sqlite3.connect(db); c.row_factory = sqlite3.Row; return c
    app = flask.Flask('t'); app.secret_key = 'x'
    m.init(dict(app=app, app_logger=logging.getLogger('t'), get_db=get_db, jsonify=flask.jsonify, login_required=lambda f: f,
                request=flask.request, session=flask.session, send_file=flask.send_file, CURRENT_VERSION='1.1.9'))
    sent = []
    state = {'code': 200}

    def fake_post(url, body, headers, timeout):
        sent.append((url, body, headers))
        if state['code'] == 'boom':
            raise ConnectionError('refusé')
        return state['code']
    m._post = fake_post
    cl = app.test_client()
    with cl.session_transaction() as s:
        s['user_id'] = 1
    return m, cl, get_db, sent, state


def _mk(cl, events=('print.finished', 'order.late'), url='https://exemple.fr/h', name='Discord'):
    r = cl.post('/api/webhooks', json={'name': name, 'url': url, 'events': list(events)})
    assert r.status_code == 200, r.get_json()
    return r.get_json()


def test_creation_secret_une_fois_et_validations(tmp_path):
    m, cl, db, _, _ = _env(tmp_path)
    w = _mk(cl)
    assert w['secret'].startswith('whsec_') and w['active'] and w['events'] == ['print.finished', 'order.late']
    lst = cl.get('/api/webhooks').get_json()['webhooks']
    assert len(lst) == 1 and 'secret' not in lst[0]
    assert cl.post('/api/webhooks', json={'name': '', 'url': 'https://x.fr', 'events': ['order.late']}).status_code == 400
    assert cl.post('/api/webhooks', json={'name': 'a', 'url': 'ftp://x', 'events': ['order.late']}).status_code == 400
    assert cl.post('/api/webhooks', json={'name': 'a', 'url': 'https://x.fr', 'events': ['inconnu']}).status_code == 400
    for i in range(m.MAX_WEBHOOKS - 1):
        _mk(cl, name=f'w{i}')
    assert cl.post('/api/webhooks', json={'name': 'trop', 'url': 'https://x.fr', 'events': ['order.late']}).status_code == 400


def test_emit_signe_et_envoie_seulement_aux_abonnes_actifs(tmp_path):
    m, cl, db, sent, _ = _env(tmp_path)
    w = _mk(cl)
    off = _mk(cl, name='coupé'); cl.put(f"/api/webhooks/{off['id']}", json={'active': False})
    only_fail = _mk(cl, events=('print.failed',), name='échecs')
    assert m.emit('print.finished', {'file': 'a.gcode'}, 1) == 1
    assert m.emit('inconnu', {}, 1) == 0
    assert m.process_due() == 1
    url, body, headers = sent[0]
    assert url == 'https://exemple.fr/h'
    env = json.loads(body)
    assert env['event'] == 'print.finished' and env['data']['file'] == 'a.gcode' and env['id'] == int(headers['X-Stellio-Delivery'])
    assert headers['X-Stellio-Event'] == 'print.finished' and m.verify_signature(w['secret'], headers['X-Stellio-Signature'], body)
    log = cl.get('/api/webhooks/deliveries').get_json()['log']
    assert log[0]['status'] == 'ok' and log[0]['response_code'] == 200 and log[0]['attempts'] == 1


def test_echec_puis_relance_puis_succes_et_abandon(tmp_path):
    m, cl, db, sent, state = _env(tmp_path)
    _mk(cl)
    state['code'] = 500
    m.emit('order.late', {'x': 1}, 1)
    t0 = 1_000_000.0
    import time as _t
    now = _t.time()
    assert m.process_due(now) == 1
    d = db().execute("SELECT * FROM webhook_deliveries").fetchone()
    assert d['status'] == 'pending' and d['attempts'] == 1 and d['error'] == 'HTTP 500' and d['next_try_at'] == pytest.approx(now + 30, abs=1)
    assert m.process_due(now + 10) == 0                                  # pas encore l'heure
    state['code'] = 200
    assert m.process_due(now + 31) == 1
    assert db().execute("SELECT status, attempts FROM webhook_deliveries").fetchone()[:] == ('ok', 2)
    # abandon après MAX_ATTEMPTS échecs
    state['code'] = 'boom'
    m.emit('order.late', {'x': 2}, 1)
    t = now + 100
    for _ in range(m.MAX_ATTEMPTS):
        m.process_due(t)
        nt = db().execute("SELECT next_try_at FROM webhook_deliveries ORDER BY id DESC").fetchone()[0]
        t = nt if nt else t
    d = db().execute("SELECT * FROM webhook_deliveries ORDER BY id DESC").fetchone()
    assert d['status'] == 'failed' and d['attempts'] == m.MAX_ATTEMPTS and 'ConnectionError' in d['error']
    assert db().execute("SELECT fail_count FROM webhooks").fetchone()[0] >= m.MAX_ATTEMPTS


def test_envoi_perime_abandonne_apres_24h(tmp_path):
    m, cl, db, sent, state = _env(tmp_path)
    _mk(cl)
    m.emit('order.late', {}, 1)
    import time as _t
    assert m.process_due(_t.time() + m.EXPIRE_AFTER_S + 60) == 0
    d = db().execute("SELECT * FROM webhook_deliveries").fetchone()
    assert d['status'] == 'failed' and 'expiré' in d['error'] and not sent


def test_bouton_tester_renvoie_le_resultat_sans_relance_en_fond(tmp_path):
    m, cl, db, sent, state = _env(tmp_path)
    w = _mk(cl, events=('print.failed',))
    r = cl.post(f"/api/webhooks/{w['id']}/test").get_json()
    assert r['ok'] and r['code'] == 200 and json.loads(sent[0][1])['event'] == 'webhook.test'
    state['code'] = 503
    r = cl.post(f"/api/webhooks/{w['id']}/test").get_json()
    assert not r['ok'] and r['code'] == 503 and r['status'] == 'failed'
    assert db().execute("SELECT COUNT(*) FROM webhook_deliveries WHERE status='pending'").fetchone()[0] == 0
    assert cl.post('/api/webhooks/999/test').status_code == 404


def test_rotation_modification_suppression_isolation(tmp_path):
    m, cl, db, sent, _ = _env(tmp_path)
    w = _mk(cl)
    s2 = cl.post(f"/api/webhooks/{w['id']}/rotate-secret").get_json()['secret']
    assert s2 != w['secret'] and s2.startswith('whsec_')
    assert cl.put(f"/api/webhooks/{w['id']}", json={'events': ['printer.overload'], 'name': 'Renommé'}).get_json()['events'] == ['printer.overload']
    assert cl.put(f"/api/webhooks/{w['id']}", json={}).status_code == 400
    m.emit('order.late', {}, 1)
    assert m.process_due() == 0                                          # plus abonné à order.late
    with cl.session_transaction() as s:
        s['user_id'] = 2
    assert cl.get('/api/webhooks').get_json()['webhooks'] == []
    assert cl.delete(f"/api/webhooks/{w['id']}").status_code == 404
    assert cl.post(f"/api/webhooks/{w['id']}/test").status_code == 404
    with cl.session_transaction() as s:
        s['user_id'] = 1
    assert cl.delete(f"/api/webhooks/{w['id']}").status_code == 200
    assert db().execute("SELECT COUNT(*) FROM webhook_deliveries").fetchone()[0] == 0


def test_renvoi_manuel_et_filtre_erreurs(tmp_path):
    m, cl, db, sent, state = _env(tmp_path)
    _mk(cl)
    state['code'] = 'boom'
    m.emit('order.late', {}, 1)
    import time as _t
    t = _t.time()
    for _ in range(m.MAX_ATTEMPTS):
        m.process_due(t)
        nt = db().execute("SELECT next_try_at FROM webhook_deliveries").fetchone()[0]
        t = nt if nt else t
    assert db().execute("SELECT attempts FROM webhook_deliveries").fetchone()[0] == m.MAX_ATTEMPTS
    did = cl.get('/api/webhooks/deliveries?errors=1').get_json()['log'][0]['id']
    state['code'] = 200
    assert cl.post(f'/api/webhooks/deliveries/{did}/retry').status_code == 200
    m.process_due()
    assert cl.get('/api/webhooks/deliveries?errors=1').get_json()['log'] == []
    assert cl.post(f'/api/webhooks/deliveries/{did}/retry').status_code == 400      # déjà réussi
    assert cl.post('/api/webhooks/deliveries/999/retry').status_code == 404


def test_url_devenue_invalide_n_est_pas_reessayee(tmp_path):
    m, cl, db, sent, _ = _env(tmp_path)
    w = _mk(cl)
    c = db(); c.execute("UPDATE webhooks SET url='ftp://x' WHERE id=?", (w['id'],)); c.commit(); c.close()
    m.emit('order.late', {}, 1)
    m.process_due()
    d = db().execute("SELECT * FROM webhook_deliveries").fetchone()
    assert d['status'] == 'failed' and not sent


def test_invite_ne_gere_pas_les_webhooks(tmp_path):
    m, cl, *_ = _env(tmp_path)
    with cl.session_transaction() as s:
        s['role'] = 'viewer'
    assert cl.get('/api/webhooks').status_code == 403
    assert cl.post('/api/webhooks', json={}).status_code == 403


def test_branchements_dans_main_planning_et_push():
    main = open(os.path.join(ROOT, 'main.py'), encoding='utf-8').read()
    assert 'def _webhook_emit(' in main and "_hosted('webhooks')" in main and 'autostart = start_worker' in open(__import__('conftest').mod_path('webhooks'), encoding='utf-8').read()
    plan = open(__import__('conftest').mod_path('production_planning'), encoding='utf-8').read()
    assert "'order.late'" in plan and "'printer.overload'" in plan
    push = open(__import__('conftest').mod_path('print_events'), encoding='utf-8').read()
    assert "'print.finished' if st == 'idle' else 'print.failed'" in push and '_webhook_active()' in push


def test_surveillance_impression_emet_les_evenements_sans_push(tmp_path):
    """Passage imprimante « printing » → « idle » / « error » : évènement émis même si les notifications push sont coupées."""
    spec = importlib.util.spec_from_file_location('print_events_t', __import__('conftest').mod_path('print_events'))
    pn = importlib.util.module_from_spec(spec); spec.loader.exec_module(pn)
    db = str(tmp_path / 'p.db')

    def get_db():
        c = sqlite3.connect(db); c.row_factory = sqlite3.Row; return c
    c = get_db(); c.execute("CREATE TABLE printers (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT)")
    c.execute("INSERT INTO printers VALUES (1, 7, 'Prusa')"); c.commit(); c.close()
    states = iter(['printing', 'idle', 'printing', 'error'])
    cur = {}

    class Hub:
        def get_status(self, p):
            return {'status': cur['s'], 'file': 'boite.gcode', 'time': {'elapsed': 5040}}
    got = []
    ns = {n: None for n in pn._REQUIRED}
    ns.update(_PUSH_DEFAULT_TYPES=[], _push_notify_async=lambda *a: None, _push_wanted=lambda: False, _server_t=lambda k, d: d, app_logger=logging.getLogger('t'), get_db=get_db,
             load_settings=lambda: {}, parse_printer_config=lambda r: dict(r), printer_hub=Hub(),
             _webhook_emit=lambda ev, data, uid: got.append((ev, data, uid)), _webhook_active=lambda: True)
    pn.init(ns, routes=False)
    for s in states:
        cur['s'] = s
        pn._push_watch_once({})
    assert [g[0] for g in got] == ['print.finished', 'print.failed']
    assert got[0][1] == {'printer': {'id': 1, 'name': 'Prusa'}, 'file': 'boite.gcode', 'duration_s': 5040} and got[0][2] == 7
