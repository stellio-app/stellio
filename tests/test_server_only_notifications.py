"""Push externes, résumé périodique et MQTT : réservés à l'édition serveur (Linux / headless)."""
import importlib.util, logging, os
import pytest
flask = pytest.importorskip('flask')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, edition):
    spec = importlib.util.spec_from_file_location(name + '_t', __import__('conftest').mod_path(name))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    app = flask.Flask('t'); app.secret_key = 'x'
    ns = dict(app=app, app_logger=logging.getLogger('t'), get_db=lambda: None, jsonify=flask.jsonify, login_required=lambda f: f,
              request=flask.request, session=flask.session, load_settings=lambda: {'push_enabled': True, 'digest_enabled': True},
              save_settings=lambda s: None, parse_printer_config=lambda p: {}, printer_hub=None, _server_t=lambda k, d: d,
              _PUSH_DEFAULT_TYPES=['print_finished'], _PUSH_TAGS={}, _insert_notification_once=lambda *a, **k: None,
              _is_low_stock=lambda *a, **k: False, _push_notify_async=lambda *a, **k: None, IS_SERVER_EDITION=edition)
    m.init(ns)
    return m, app.test_client()


def test_push_non_envoye_hors_edition_serveur():
    m, cl = _load('push_notify', False)
    sent = []
    m._push_deliver = lambda *a, **k: sent.append(a)
    m._push_notify_async('print_finished', 'T', 'M')
    assert sent == []
    r = cl.post('/api/push/test', json={})
    assert r.status_code == 404 and r.get_json()['code'] == 'server_edition_only'


def test_push_envoye_en_edition_serveur():
    m, cl = _load('push_notify', True)
    sent = []
    m._push_deliver = lambda *a, **k: sent.append(a)
    class T:
        def __init__(s, target=None, **k): s.t = target
        def start(s): s.t()
    m.threading = type('Th', (), {'Thread': T})
    m._push_notify_async('print_finished', 'T', 'M')
    assert len(sent) == 1


def test_resume_periodique_hors_edition_serveur():
    m, cl = _load('digest', False)
    for url, meth in (('/api/digest/settings', 'get'), ('/api/digest/preview', 'get'), ('/api/digest/send-now', 'post')):
        r = getattr(cl, meth)(url)
        assert r.status_code == 404 and r.get_json()['code'] == 'server_edition_only', url
    assert m.tick() is False


def test_interface_masque_push_hors_serveur_et_mqtt_deja_reserve():
    html = open(os.path.join(ROOT, 'interface', 'index.html'), encoding='utf-8').read()
    assert 'id="push-server-block" style="display:none;"' in html
    js = open(os.path.join(ROOT, 'interface', 'script.js'), encoding='utf-8').read()
    assert "'push-server-block': 'block'" in js and "'mqtt-server-block': 'block'" in js
    mq = open(__import__('conftest').mod_path('mqtt_publisher'), encoding='utf-8').read()
    assert 'if not IS_SERVER_EDITION or not HAS_MQTT' in mq and mq.count('_server_edition_only()') >= 3
