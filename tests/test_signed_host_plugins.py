"""Plugins du catalogue à code intégré (1.2.0) : `host` n'est admis QUE signé par une clé de confiance, et l'archive est revérifiée à chaque lecture."""
import hashlib
import importlib.util
import io
import json, sys
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


def test_catalogue_github_lu_sans_cache_pour_que_signature_et_fichier_restent_coherents(env, monkeypatch):
    m, ph, sec, tmp = env
    k, pub = _key()
    monkeypatch.setenv('STELLIO_PLUGIN_PUBKEYS', pub)
    raw = json.dumps({'plugins': []}).encode()
    sig = k.sign(sec.catalog_message(raw)).hex().encode()
    seen = []

    def fake(url, limit, timeout=15):
        seen.append(url)
        return sig if '.sig' in url.split('?')[0] else raw
    monkeypatch.setattr(m, 'http_get', fake)
    assert m._fetch_catalog(m.DEFAULT_CATALOG_URL) == []
    assert len(seen) == 2 and all('?t=' in u for u in seen)                               # catalogue ET signature : appels sans cache
    assert seen[1].split('?')[0].endswith('catalog.json.sig')
    assert m._fresh('https://exemple.org/catalog.json') == 'https://exemple.org/catalog.json'   # hôtes tiers inchangés


def test_catalogue_signature_en_retard_est_relue_une_fois_puis_acceptee(env, monkeypatch):
    m, ph, sec, tmp = env
    k, pub = _key()
    monkeypatch.setenv('STELLIO_PLUGIN_PUBKEYS', pub)
    monkeypatch.setattr(m, '_SIG_RETRY_DELAY', 0)
    old = json.dumps({'plugins': []}).encode()
    new = json.dumps({'plugins': [], 'v': 2}).encode()
    sig_old = k.sign(sec.catalog_message(old)).hex().encode()
    sig_new = k.sign(sec.catalog_message(new)).hex().encode()
    calls = {'n': 0}

    def fake(url, limit, timeout=15):
        base = url.split('?')[0]
        if base.endswith('.sig'):
            return sig_old if calls['n'] <= 1 else sig_new      # 1re lecture : signature en cache (ancienne) ; relecture : à jour
        calls['n'] += 1
        return new
    monkeypatch.setattr(m, 'http_get', fake)
    assert m._fetch_catalog(m.DEFAULT_CATALOG_URL) == []         # relue puis acceptée : plus de message
    # une signature réellement fausse reste refusée après la relecture
    monkeypatch.setattr(m, 'http_get', lambda url, limit, timeout=15: b'00' * 64 if url.split('?')[0].endswith('.sig') else new)
    got = m._fetch_catalog(m.DEFAULT_CATALOG_URL)
    assert got == [] or got[0].get('catalog_stale')                                    # vraie signature fausse : on garde la dernière version vérifiée (ici, aucun plugin)
    os.remove(m._cache_path(m.DEFAULT_CATALOG_URL))
    with pytest.raises(ValueError):
        m._fetch_catalog(m.DEFAULT_CATALOG_URL)                                        # sans version mémorisée : refus


def test_le_plugin_signe_reste_installe_apres_son_chargement_et_un_redemarrage(env, monkeypatch):
    """Régression : l'import écrivait un `__pycache__` dans le dossier du plugin, le contenu ne correspondait plus à l'archive signée et le plugin
    disparaissait de la liste au redémarrage suivant (il fallait le réinstaller)."""
    m, ph, sec, tmp = env
    k, pub = _key()
    monkeypatch.setenv('STELLIO_PLUGIN_PUBKEYS', pub)
    monkeypatch.setattr(sys, 'dont_write_bytecode', False)
    data = _zip({'plugin.json': json.dumps(MAN), 'ext_demo.py': CODE})
    m.install_bytes(data, signature=_sign(k, 'ext-demo', '1.0.0', data))
    ph.set_enabled('ext-demo', True)
    d = os.path.join(m._root(), 'ext-demo')
    for _ in range(3):                                   # trois « démarrages » successifs
        ph._LOADED.clear(); ph._VERIFIED.clear()
        ns = {'app_logger': None, 'DATA_DIR': str(tmp)}
        assert 'ext-demo' in ph.load_enabled(ns) and ns['EXT_LOADED'] is True
        assert [x['id'] for _d, x in m.installed()] == ['ext-demo'] and ph.verify_external('ext-demo', d)[0]
    assert not os.path.isdir(os.path.join(d, '__pycache__'))              # aucun bytecode écrit
    # un faux bytecode déposé dans __pycache__ ne change rien : il n'est jamais lu, le code vient des sources vérifiées
    os.makedirs(os.path.join(d, '__pycache__'), exist_ok=True)
    open(os.path.join(d, '__pycache__', 'ext_demo.cpython-312.pyc'), 'wb').write(b'\x00' * 64)
    ph._LOADED.clear(); ph._VERIFIED.clear()
    ns = {'app_logger': None, 'DATA_DIR': str(tmp)}
    assert 'ext-demo' in ph.load_enabled(ns) and ns['EXT_LOADED'] is True and ph.verify_external('ext-demo', d)[0]


def test_signature_du_catalogue_en_retard_message_rassurant_cote_page(env, monkeypatch):
    """Un catalogue momentanément incohérent (cache GitHub) n'est pas une panne : l'API le signale par un code, la page affiche un message calme avec repère visuel
    et relit seule le catalogue ; les vraies erreurs gardent le message d'erreur."""
    m, ph, sec, tmp = env
    import flask
    app = flask.Flask('t'); app.secret_key = 'x'
    k, pub = _key()
    monkeypatch.setenv('STELLIO_PLUGIN_PUBKEYS', pub)
    monkeypatch.setattr(m, '_SIG_RETRY_DELAY', 0)
    raw = json.dumps({'plugins': []}).encode()
    monkeypatch.setattr(m, 'http_get', lambda url, limit, timeout=15: b'00' * 64 if url.split('?')[0].endswith('.sig') else raw)
    with pytest.raises(ValueError) as e:
        m._fetch_catalog(m.DEFAULT_CATALOG_URL)
    assert str(e.value).startswith('Signature du catalogue')                        # c'est ce préfixe qui déclenche le code `catalog_signature`
    src = open(os.path.join(ROOT, 'modules', 'plugins.py'), encoding='utf-8').read()
    assert "'catalog_signature' if str(e).startswith('Signature du catalogue')" in src
    js = open(os.path.join(ROOT, 'interface', 'suite.js'), encoding='utf-8').read()
    assert "x.data.code === 'catalog_signature'" in js and 'su-soft' in js and 'fa-rotate fa-spin' in js and 'setTimeout(() => { if ($(\'su-plstore\')) loadStore(); }, 15000)' in js
    css = open(os.path.join(ROOT, 'interface', 'style.css'), encoding='utf-8').read()
    assert '.su-soft' in css
    import re
    for lg in ('fr', 'en', 'de', 'es', 'it', 'pt', 'zh', 'ja'):
        d = json.load(open(os.path.join(ROOT, 'languages', lg + '.json'), encoding='utf-8'))
        assert all(d.get('suite.' + k2) for k2 in ('catalog_updating', 'catalog_updating_hint', 'catalog_later', 'catalog_later_hint')), lg


def test_catalogue_reste_consultable_hors_connexion_avec_la_derniere_version_verifiee(env, monkeypatch):
    m, ph, sec, tmp = env
    k, pub = _key()
    monkeypatch.setenv('STELLIO_PLUGIN_PUBKEYS', pub)
    raw = json.dumps({'plugins': [{'id': 'demo', 'name': 'D', 'version': '1.0', 'url': 'https://github.com/stellio-app/stellio-plugins/demo.zip', 'sha256': 'a' * 64}]}).encode()
    sig = k.sign(sec.catalog_message(raw)).hex().encode()
    monkeypatch.setattr(m, 'http_get', lambda url, limit, timeout=15: sig if url.split('?')[0].endswith('.sig') else raw)
    first = m._fetch_catalog(m.DEFAULT_CATALOG_URL)
    assert first[0]['id'] == 'demo' and not first[0].get('catalog_stale')

    def down(url, limit, timeout=15):
        raise ValueError('Téléchargement impossible : hors connexion')
    monkeypatch.setattr(m, 'http_get', down)
    off = m._fetch_catalog(m.DEFAULT_CATALOG_URL)                                       # plus d'internet : le catalogue reste là
    assert off[0]['id'] == 'demo' and off[0]['catalog_stale'] is True and off[0]['catalog_signature'] == 'valid'
    # fichier mémorisé altéré, ou clé de confiance retirée : il n'est plus montré
    p = m._cache_path(m.DEFAULT_CATALOG_URL)
    d = json.load(open(p)); d['raw'] = __import__('base64').b64encode(raw.replace(b'1.0', b'9.9')).decode(); json.dump(d, open(p, 'w'))
    with pytest.raises(ValueError):
        m._fetch_catalog(m.DEFAULT_CATALOG_URL)
    m._cache_save(m.DEFAULT_CATALOG_URL, raw, sig.decode())
    assert m._fetch_catalog(m.DEFAULT_CATALOG_URL)[0]['id'] == 'demo'
    monkeypatch.delenv('STELLIO_PLUGIN_PUBKEYS')
    sec._status_cache.clear()
    assert m._fetch_catalog(m.DEFAULT_CATALOG_URL)[0]['catalog_signature'] == 'unverified'   # sans clé : comme avant, non vérifié
    # le dossier du cache n'est pas pris pour un plugin
    assert [x['id'] for _d, x in m.installed()] == []


def test_page_catalogue_bandeau_calme_et_relecture_automatique():
    js = open(os.path.join(ROOT, 'interface', 'suite.js'), encoding='utf-8').read()
    assert 'if (c.stale)' in js and 'su-soft-slim' in js and 'loadStore._stale <= 6 ? 15000 : 120000' in js and '}, 300000);' in js
    for lg in ('fr', 'en', 'de', 'es', 'it', 'pt', 'zh', 'ja'):
        assert json.load(open(os.path.join(ROOT, 'languages', lg + '.json'), encoding='utf-8')).get('suite.catalog_stale_hint'), lg


def test_installation_directe_non_signee_exige_acceptation_explicite(env):
    m, ph, sec, tmp = env
    data = _zip({'plugin.json': json.dumps(MAN), 'ext_demo.py': CODE})
    with pytest.raises(m.PluginRefused) as e:
        m.install_bytes(data)                                                    # par défaut : refus
    assert e.value.code in ('host_no_key', 'host_unsigned')
    with pytest.raises(m.PluginRefused):
        m.install_bytes(data, accept_unsigned=True, origin='official')           # jamais depuis le catalogue officiel
    m.install_bytes(data, accept_unsigned=True)                                  # .zip direct + acceptation : installé
    assert ph.external_dirs() != []
    proof = json.load(open(os.path.join(m._root(), '.host-proofs', 'ext-demo.json'))) if os.path.exists(os.path.join(m._root(), '.host-proofs', 'ext-demo.json')) else {}
    assert proof.get('unsigned') is True
