"""Plugins du catalogue à code intégré (1.2.0) : `host` n'est admis QUE signé par une clé de confiance, et l'archive est revérifiée à chaque lecture."""
import hashlib
import importlib.util
import io
import json
import os
import zipfile

import pytest

from conftest import mod_path, ROOT

pytest.importorskip('cryptography')
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def _key():
    k = Ed25519PrivateKey.generate()
    return k, k.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()


def _zip(files):
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w') as z:
        for n, c in files.items():
            z.writestr(n, c)
    return b.getvalue()


def _sign(k, pid, version, data):
    from modules import plugin_security as sec
    return k.sign(sec.plugin_message(pid, version, hashlib.sha256(data).hexdigest())).hex()


MAN = {'id': 'ext-demo', 'name': 'Démo', 'version': '1.0.0', 'api': 1, 'host': {'modules': ['ext_demo'], 'default_on': True, 'migrate': {'always': True}},
       'permissions': []}
CODE = "def init(ns):\n    return {'EXT_LOADED': True}\n"


@pytest.fixture
def env(tmp_path, monkeypatch):
    import modules.plugin_security as sec
    import modules.plugin_host as ph
    sec.DATA_DIR = str(tmp_path)
    sec._status_cache.clear()
    ph._MAIN['DATA_DIR'] = str(tmp_path)
    ph._VERIFIED.clear()
    ph._LOADED.clear()
    os.makedirs(tmp_path / 'plugins', exist_ok=True)
    spec = importlib.util.spec_from_file_location('plugins_host_ext_test', mod_path('plugins'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.DATA_DIR = str(tmp_path)
    monkeypatch.delenv('STELLIO_PLUGIN_PUBKEYS', raising=False)
    monkeypatch.delenv('STELLIO_ENABLE_PLUGINS', raising=False)
    yield m, ph, sec, tmp_path
    sec.DATA_DIR = None
    ph._MAIN.pop('DATA_DIR', None)
    ph._VERIFIED.clear()
    ph._LOADED.clear()


def test_host_refuse_par_defaut_dans_le_manifeste(env):
    m = env[0]
    mm, err = m.validate_manifest(dict(MAN))
    assert mm is None and 'host' in err
    mm, err = m.validate_manifest(dict(MAN), allow_host=True)
    assert err is None and mm['host'] == {'modules': ['ext_demo']}
    for bad in ({'modules': []}, {'modules': ['a b']}, {'modules': ['../x']}, 'x'):
        assert m.validate_manifest(dict(MAN, host=bad), allow_host=True)[0] is None


def test_installation_refusee_sans_cle_ou_sans_signature_valide(env):
    m, ph, sec, tmp = env
    data = _zip({'plugin.json': json.dumps(MAN), 'ext_demo.py': CODE})
    k, pub = _key()
    with pytest.raises(m.PluginRefused) as e:
        m.install_bytes(data, signature=_sign(k, 'ext-demo', '1.0.0', data))     # signé, mais AUCUNE clé de confiance configurée
    assert e.value.code == 'host_no_key'
    os.environ['STELLIO_PLUGIN_PUBKEYS'] = pub
    try:
        with pytest.raises(m.PluginRefused) as e:
            m.install_bytes(data)                                                # clé configurée, archive non signée
        assert e.value.code == 'host_unsigned'
        with pytest.raises(m.PluginRefused):
            m.install_bytes(data, signature='00' * 64)                           # signature invalide
        with pytest.raises(m.PluginRefused) as e:
            m.install_bytes(data, signature=_sign(_key()[0], 'ext-demo', '1.0.0', data))   # signée par une AUTRE clé
        assert e.value.code in ('signature_invalid', 'host_unsigned')
        with pytest.raises(m.PluginRefused) as e:
            m.install_bytes(data, accept_risk=True)                              # « accepter le risque » ne contourne pas la règle
        assert e.value.code == 'host_unsigned'
    finally:
        os.environ.pop('STELLIO_PLUGIN_PUBKEYS', None)
    assert not os.path.exists(os.path.join(m._root(), 'ext-demo')) and ph.external_dirs() == []


def test_signe_installe_liste_et_charge_puis_toute_modification_le_neutralise(env, monkeypatch):
    m, ph, sec, tmp = env
    k, pub = _key()
    monkeypatch.setenv('STELLIO_PLUGIN_PUBKEYS', pub)
    data = _zip({'plugin.json': json.dumps(MAN), 'ext_demo.py': CODE})
    res = m.install_bytes(data, signature=_sign(k, 'ext-demo', '1.0.0', data))
    assert res['security']['signature'] == 'valid'
    assert [x['id'] for _d, x in m.installed()] == ['ext-demo']
    assert [p for p, _d in ph.external_dirs()] == ['ext-demo']
    mf = {p: x for p, _d, x in ph.manifests()}['ext-demo']
    assert mf['_external'] is True
    # un plugin du catalogue ne s'active jamais tout seul : `default_on` et `migrate` de son manifeste sont ignorés
    assert not ph.is_enabled('ext-demo') and 'ext-demo' not in ph.migrate({}, None, str(tmp), True)
    ph.set_enabled('ext-demo', True)
    ns = {'app_logger': None, 'DATA_DIR': str(tmp)}
    assert 'ext-demo' in ph.load_enabled(ns) and ns['EXT_LOADED'] is True
    # modification d'un fichier après installation : ni listé, ni chargé
    ph._LOADED.clear()
    p = os.path.join(m._root(), 'ext-demo', 'ext_demo.py')
    open(p, 'a').write("\nimport os\n")
    ns2 = {'app_logger': None, 'DATA_DIR': str(tmp)}
    assert ph.external_dirs() == [] and m.installed() == [] and 'ext-demo' not in ph.load_enabled(ns2) and 'EXT_LOADED' not in ns2


def test_fichier_ajoute_cle_retiree_ou_preuve_supprimee_neutralisent_le_plugin(env, monkeypatch):
    m, ph, sec, tmp = env
    k, pub = _key()
    monkeypatch.setenv('STELLIO_PLUGIN_PUBKEYS', pub)
    data = _zip({'plugin.json': json.dumps(MAN), 'ext_demo.py': CODE})
    m.install_bytes(data, signature=_sign(k, 'ext-demo', '1.0.0', data))
    d = os.path.join(m._root(), 'ext-demo')
    assert ph.verify_external('ext-demo', d)[0]
    open(os.path.join(d, 'extra.py'), 'w').write('x = 1\n')                      # fichier ajouté
    assert not ph.verify_external('ext-demo', d)[0]
    os.remove(os.path.join(d, 'extra.py'))
    assert ph.verify_external('ext-demo', d)[0]
    monkeypatch.delenv('STELLIO_PLUGIN_PUBKEYS')                                  # plus aucune clé de confiance : refus par défaut
    assert ph.verify_external('ext-demo', d) == (False, 'aucune clé de confiance configurée')
    monkeypatch.setenv('STELLIO_PLUGIN_PUBKEYS', pub)
    os.remove(ph._proof_paths('ext-demo')[0])                                     # preuve supprimée
    assert not ph.verify_external('ext-demo', d)[0]


def test_remplacement_par_une_version_sans_code_integre_retire_la_preuve(env, monkeypatch):
    m, ph, sec, tmp = env
    k, pub = _key()
    monkeypatch.setenv('STELLIO_PLUGIN_PUBKEYS', pub)
    data = _zip({'plugin.json': json.dumps(MAN), 'ext_demo.py': CODE})
    m.install_bytes(data, signature=_sign(k, 'ext-demo', '1.0.0', data))
    plain = dict(MAN, version='1.1.0'); plain.pop('host'); plain.update(entry='main.py')
    d2 = _zip({'plugin.json': json.dumps(plain), 'main.py': "print('ok')\n"})
    m.install_bytes(d2, signature=_sign(k, 'ext-demo', '1.1.0', d2))
    assert not os.path.exists(ph._proof_paths('ext-demo')[1]) and ph.external_dirs() == []


def test_le_vrai_plugin_split_color_s_installe_signe(env, monkeypatch):
    m, ph, sec, tmp = env
    k, pub = _key()
    monkeypatch.setenv('STELLIO_PLUGIN_PUBKEYS', pub)
    src = os.path.join(ROOT, 'sdk', 'examples', 'split-color')
    data = _zip({n: open(os.path.join(src, n), 'rb').read() for n in ('plugin.json', 'split_color.py', 'split.html')})
    res = m.install_bytes(data, signature=_sign(k, 'split-color', '1.0.0', data))
    man = res['manifest']
    assert man['host'] == {'modules': ['split_color']} and man['ui']['entry'] == 'split.html'
    assert set(man['permissions']) == {'ui', 'api:read', 'api:write'}
    assert [p for p, _d in ph.external_dirs()] == ['split-color']


def test_le_pont_ecriture_est_limite_aux_plugins_signes_et_a_leur_espace():
    js = open(os.path.join(ROOT, 'interface', 'suite.js'), encoding='utf-8').read()
    assert "pl.host && (pl.permissions || []).includes('api:write') && path.startsWith(['', 'api', 'x', pl.id, ''].join('/'))" in js
    assert "m.method === 'POST'" in js
