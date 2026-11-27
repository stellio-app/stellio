"""1.2.1 : un plugin signé du catalogue ne reçoit que les services qu'il déclare (jamais les secrets)."""
import types
import pytest
from modules import plugin_host as ph


def _mod(req=(), opt=(), over=()):
    m = types.SimpleNamespace(_REQUIRED=tuple(req), _OPTIONAL=tuple(opt), _OVERRIDABLE=tuple(over)); return m


NS = {'app': 1, 'get_db': 2, 'jsonify': 3, 'SECRET_KEY': 'x', 'cipher_password': 'y', 'load_settings': 4}


def test_seuls_les_services_declares_sont_transmis():
    got = ph.scoped_services(_mod(['app', 'get_db'], ['jsonify', 'absent']), NS)
    assert got == {'app': 1, 'get_db': 2, 'jsonify': 3}


@pytest.mark.parametrize('name', ['SECRET_KEY', 'cipher_password', 'api_key_store', 'decrypt_credential'])
def test_noms_sensibles_refuses(name):
    with pytest.raises(RuntimeError):
        ph.scoped_services(_mod(['app', name]), dict(NS, **{name: 1}))


def test_manifeste_borne_les_services():
    man = {'host': {'services': ['app']}}
    assert ph.scoped_services(_mod(['app']), NS, man) == {'app': 1}
    with pytest.raises(RuntimeError):
        ph.scoped_services(_mod(['app', 'get_db']), NS, man)

