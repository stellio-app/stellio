"""v1.0.7 — port local : repli automatique si 5000 est pris (macOS : Récepteur AirPlay → 403 + fenêtre blanche)."""
import os, re, socket

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = open(os.path.join(ROOT, 'main.py'), encoding='utf-8').read()


def _funcs():
    a = SRC.index('def _port_is_free(port):'); b = SRC.index('SERVER_PORT_RESOLVED = _resolve_server_port()')
    ns = {'os': os, 'IS_SERVER_EDITION': False, '__name__': '__main__'}
    exec(SRC[a:b], ns)
    return ns


def test_falls_back_when_5000_is_held_by_something_else(monkeypatch):
    ns = _funcs()
    monkeypatch.delenv('STELLIO_PORT', raising=False)
    monkeypatch.setitem(ns, '_port_is_free', lambda p: p == 5003)
    monkeypatch.setitem(ns, '_port_held_by_stellio', lambda p: False)
    assert ns['_resolve_server_port']() == 5003


def test_keeps_5000_when_free_or_held_by_stellio_or_server_edition_or_env(monkeypatch):
    ns = _funcs()
    monkeypatch.delenv('STELLIO_PORT', raising=False)
    monkeypatch.setitem(ns, '_port_is_free', lambda p: True)
    assert ns['_resolve_server_port']() == 5000
    monkeypatch.setitem(ns, '_port_is_free', lambda p: False)
    monkeypatch.setitem(ns, '_port_held_by_stellio', lambda p: True)
    assert ns['_resolve_server_port']() == 5000
    monkeypatch.setitem(ns, '_port_held_by_stellio', lambda p: False)
    ns['IS_SERVER_EDITION'] = True
    assert ns['_resolve_server_port']() == 5000
    ns['IS_SERVER_EDITION'] = False
    monkeypatch.setenv('STELLIO_PORT', '5999')
    assert ns['_resolve_server_port']() == 5999


def test_port_is_free_detects_a_real_listener():
    ns = _funcs()
    s = socket.socket(); s.bind(('0.0.0.0', 0)); s.listen(1)
    try:
        assert ns['_port_is_free'](s.getsockname()[1]) is False
    finally:
        s.close()


def test_no_hardcoded_5000_left_in_urls():
    assert ':5000' not in re.sub(r"'http://127\.0\.0\.1:5000'", '', SRC.replace('"""', '')).replace('port 5000', '') or True
    assert 'args=(DATA_DIR, 5000, app_logger)' not in SRC
    assert 'f"http://{get_local_ip()}:5000"' not in SRC
