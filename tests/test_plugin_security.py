"""Durcissement des plugins (1.1.8) : signature Ed25519, politique de mise à jour, audit statique, restrictions réelles sous Linux."""
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import zipfile

import pytest

from conftest import mod_path

crypto = pytest.importorskip('cryptography')
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def _load(name):
    spec = importlib.util.spec_from_file_location(name + '_sec_test', mod_path(name))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _key():
    k = Ed25519PrivateKey.generate()
    return k, k.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()


@pytest.fixture
def sec(tmp_path):
    m = _load('plugin_security')
    m.DATA_DIR = str(tmp_path)
    os.makedirs(tmp_path / 'plugins')
    return m


def test_signature_valide_invalide_non_signee_non_verifiable(sec):
    k, pub = _key()
    sha = hashlib.sha256(b'zip').hexdigest()
    sig = k.sign(sec.plugin_message('mon-plugin', '1.2.0', sha)).hex()
    assert sec.signature_status(sig, 'mon-plugin', '1.2.0', sha, [pub]) == {'status': 'valid', 'key': sec.fingerprint(pub)}
    assert sec.signature_status(sig, 'mon-plugin', '1.2.1', sha, [pub])['status'] == 'invalid'          # version différente : signature non transposable
    assert sec.signature_status(sig, 'autre', '1.2.0', sha, [pub])['status'] == 'invalid'
    assert sec.signature_status(sig, 'mon-plugin', '1.2.0', hashlib.sha256(b'autre').hexdigest(), [pub])['status'] == 'invalid'   # archive modifiée
    assert sec.signature_status('', 'mon-plugin', '1.2.0', sha, [pub])['status'] == 'unsigned'
    assert sec.signature_status(sig, 'mon-plugin', '1.2.0', sha, [])['status'] == 'unverifiable'        # aucune clé configurée : ni crue ni rejetée
    _k2, pub2 = _key()
    assert sec.signature_status(sig, 'mon-plugin', '1.2.0', sha, [pub2])['status'] == 'invalid'         # autre clé que celle qui a signé
    assert sec.signature_status('zz', 'mon-plugin', '1.2.0', sha, [pub])['status'] == 'invalid'


def test_signature_du_catalogue_porte_sur_les_octets_exacts(sec):
    k, pub = _key()
    raw = b'{"plugins": []}'
    sig = k.sign(sec.catalog_message(raw)).hex()
    assert sec.verify(sig, sec.catalog_message(raw), [pub])
    assert not sec.verify(sig, sec.catalog_message(raw + b' '), [pub])
    assert not sec.verify(sig, sec.plugin_message('a', '1', 'b' * 64), [pub])                           # un message de plugin n'est pas un message de catalogue


def test_cles_de_confiance_env_et_fichier(sec, tmp_path, monkeypatch):
    _k, pub = _key()
    _k2, pub2 = _key()
    assert sec.trusted_keys() == []
    monkeypatch.setenv('STELLIO_PLUGIN_PUBKEYS', pub + ', nimporte quoi')
    (tmp_path / 'plugins' / 'trusted_keys.json').write_text(json.dumps([pub2, pub, 'xx']))
    assert sec.trusted_keys() == [pub, pub2]


def test_politique_de_signature(sec):
    valid = {'status': 'valid', 'key': 'AAA'}
    assert sec.signature_policy({'status': 'invalid'}, False, False) == (False, 'signature_invalid')
    assert sec.signature_policy({'status': 'unsigned'}, False, True) == (True, 'ok')                    # communautaire non signé : autorisé (marqué non signé)
    assert sec.signature_policy({'status': 'unsigned'}, True, True) == (False, 'signature_required')
    assert sec.signature_policy({'status': 'unsigned'}, True, False) == (True, 'ok')                    # aucune clé configurée : rien d'exigé
    prev = {'signature': 'valid', 'key': 'AAA'}
    assert sec.signature_policy({'status': 'unsigned'}, False, True, prev) == (False, 'signature_downgrade')
    assert sec.signature_policy({'status': 'valid', 'key': 'BBB'}, False, True, prev) == (False, 'key_changed')
    assert sec.signature_policy({'status': 'valid', 'key': 'BBB'}, False, True, prev, accept_key_change=True) == (True, 'ok')
    assert sec.signature_policy(valid, False, True, prev) == (True, 'ok')


def _audit(sec, files, perms=()):
    import tempfile
    d = tempfile.mkdtemp()
    for n, c in files.items():
        os.makedirs(os.path.dirname(os.path.join(d, n)), exist_ok=True)
        open(os.path.join(d, n), 'w').write(c)
    return sec.audit_dir(d, {'permissions': list(perms)})


def test_audit_plugin_propre(sec):
    a = _audit(sec, {'main.py': "import json, sys\nprint(json.dumps({'ok': True}))\n"})
    assert a['level'] == 'ok' and a['blocking'] == 0


def test_audit_reseau_bloquant_seulement_si_non_declare(sec):
    src = "import urllib.request\nurllib.request.urlopen('https://x.test')\n"
    assert _audit(sec, {'main.py': src})['level'] == 'danger'
    assert _audit(sec, {'main.py': src}, ['network'])['level'] == 'warn'                                # déclaré : visible mais pas bloquant


def test_audit_processus_code_dynamique_et_binaire(sec):
    assert _audit(sec, {'main.py': "import subprocess\nsubprocess.run(['ls'])\n"}, ['network'])['blocking'] >= 1
    a = _audit(sec, {'main.py': "eval(open('x').read())\n"})
    assert any(f['id'] == 'call:eval' and f['blocking'] for f in a['findings'])
    assert _audit(sec, {'main.py': "import os\nos.system('id')\n"})['level'] == 'danger'
    assert _audit(sec, {'main.py': 'pass\n', 'lib/helper.so': 'x'})['level'] == 'danger'
    assert _audit(sec, {'main.py': "__import__('os')\n"})['level'] == 'danger'


def test_audit_lecture_hors_dossier_environnement_api_non_declaree_et_page(sec):
    a = _audit(sec, {'main.py': "import os\nopen('/etc/passwd').read()\nos.environ['HOME']\n"})
    cats = {f['category'] for f in a['findings']}
    assert 'filesystem' in cats and 'environment' in cats and a['level'] == 'warn'                      # constats utiles, pas bloquants
    assert _audit(sec, {'main.py': "import os\nurl = os.environ['STELLIO_API_URL']\n"})['level'] == 'danger'
    assert _audit(sec, {'main.py': "import os\nurl = os.environ['STELLIO_API_URL']\n"}, ['api:read'])['blocking'] == 0
    h = _audit(sec, {'main.py': 'pass\n', 'page.html': '<script src="https://cdn.test/x.js"></script>'})
    assert any(f['id'] == 'html:external' for f in h['findings'])


def test_audit_fichier_illisible_et_bloc_encode(sec):
    assert any(f['id'] == 'syntax' for f in _audit(sec, {'main.py': 'def (:\n'})['findings'])
    blob = 'A' * 500
    assert any(f['id'] == 'blob:encoded' for f in _audit(sec, {'main.py': f"x = '{blob}'\n"})['findings'])


def test_memoire_des_verifications(sec):
    sec.save_record('p1', {'status': 'valid', 'key': 'K'}, {'level': 'warn', 'blocking': 0, 'findings': [{'id': 'a', 'severity': 'low', 'category': 'environment', 'file': 'main.py', 'line': 1, 'detail': 'd', 'blocking': False}]})
    r = sec.load_store()['p1']
    assert r['signature'] == 'valid' and r['key'] == 'K' and r['audit'] == 'warn'
    sec.drop_record('p1')
    assert 'p1' not in sec.load_store()


def test_filtre_seccomp_bien_forme(sec):
    blob = sec.build_seccomp_filter('x86_64')
    assert len(blob) % 8 == 0 and len(blob) // 8 == 14
    # tous les sauts restent dans le programme et la dernière instruction est un refus
    import struct
    prog = [struct.unpack('=HBBI', blob[i:i + 8]) for i in range(0, len(blob), 8)]
    for i, (code, jt, jf, k) in enumerate(prog):
        if code == 0x15:
            assert i + 1 + jt < len(prog) and i + 1 + jf < len(prog)
    assert prog[-1][0] == 0x06 and prog[-1][3] & 0xFFFF0000 == 0x00050000


needs_linux = pytest.mark.skipif(not sys.platform.startswith('linux'), reason='restrictions du noyau : Linux seulement')


@pytest.fixture
def sandbox_plugin(tmp_path):
    d = tmp_path / 'plug'
    (d / 'data').mkdir(parents=True)
    (d / 'main.py').write_text("""
import socket, os, json
res = {}
def t(name, fn):
    try:
        fn(); res[name] = 'ok'
    except Exception as e:
        res[name] = type(e).__name__
t('inet', lambda: socket.socket(socket.AF_INET, socket.SOCK_STREAM))
t('inet6', lambda: socket.socket(socket.AF_INET6, socket.SOCK_STREAM))
t('unix', lambda: socket.socketpair())
t('read_own', lambda: open(__file__).read())
t('write_data', lambda: open('data/x.txt', 'w').write('1'))
t('write_root', lambda: open('rootfile.txt', 'w').write('1'))
t('modify_own_code', lambda: open(__file__, 'a').write('#'))
t('read_etc_passwd', lambda: open('/etc/passwd').read())
t('list_home', lambda: os.listdir(os.path.expanduser('~')))
t('list_tmp', lambda: os.listdir('/tmp'))
print(json.dumps(res))
""")
    return d


def _run(sec, d, net):
    fn, st = sec.make_preexec(str(d), str(d / 'data'), net, sys.executable)
    p = subprocess.run([sys.executable, '-I', str(d / 'main.py')], cwd=str(d), capture_output=True, preexec_fn=fn, timeout=30)
    assert p.returncode == 0, p.stderr.decode()[-400:]
    return json.loads(p.stdout.decode().strip().splitlines()[-1]), st


@needs_linux
def test_restrictions_reelles_sans_permission_reseau(sec, sandbox_plugin):
    if not sec.sandbox_status()['filesystem']:
        pytest.skip('Landlock indisponible sur ce noyau')
    r, st = _run(sec, sandbox_plugin, False)
    assert r['inet'] == 'PermissionError' and r['inet6'] == 'PermissionError' and r['unix'] == 'ok'       # sockets locaux non concernés
    assert r['read_own'] == 'ok' and r['write_data'] == 'ok'
    assert r['write_root'] == 'PermissionError' and r['modify_own_code'] == 'PermissionError'              # le code audité ne peut plus changer
    assert r['read_etc_passwd'] == 'PermissionError' and r['list_home'] == 'PermissionError' and r['list_tmp'] == 'PermissionError'
    assert st['network_restricted'] and st['filesystem_restricted']


@needs_linux
def test_permission_reseau_ouvre_les_sockets_mais_pas_les_fichiers(sec, sandbox_plugin):
    if not sec.sandbox_status()['filesystem']:
        pytest.skip('Landlock indisponible sur ce noyau')
    r, st = _run(sec, sandbox_plugin, True)
    assert r['inet'] == 'ok' and r['inet6'] in ('ok', 'OSError') and r['write_root'] == 'PermissionError' and r['list_home'] == 'PermissionError'
    assert not st['network_restricted']


def test_statut_honnete_hors_linux_et_desactive(sec, monkeypatch):
    monkeypatch.setenv('STELLIO_PLUGIN_SANDBOX', 'off')
    sec._status_cache.clear()
    st = sec.sandbox_status()
    assert st['enforced'] is False and st['reason'] == 'disabled'
    fn, s2 = sec.make_preexec('/tmp', '/tmp', False)
    assert fn is None and not s2['filesystem_restricted'] and not s2['network_restricted']
    monkeypatch.delenv('STELLIO_PLUGIN_SANDBOX')
    sec._status_cache.clear()
    monkeypatch.setattr(sys, 'platform', 'win32')
    sec._status_cache.clear()
    st = sec.sandbox_status()
    assert st['platform'] in ('windows', 'linux') or st['enforced'] is False
    if st['platform'] == 'windows' or os.name == 'nt':
        assert st['reason'] == 'platform' and not st['filesystem'] and not st['network']
    sec._status_cache.clear()


# ── installation complète : signature + audit + exécution restreinte ──
def _plugins(tmp_path, sec):
    """Module plugins avec un dossier de données isolé, branché sur le même plugin_security que le test."""
    m = _load('plugins')
    m.DATA_DIR = str(tmp_path)
    sys.modules['modules'].plugin_security = sec if 'modules' in sys.modules else None
    return m


def _zip(files):
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w') as z:
        for n, c in files.items():
            z.writestr(n, c)
    return b.getvalue()


MAN = {'id': 'demo', 'name': 'Démo', 'version': '1.0', 'api': 1, 'entry': 'main.py', 'events': ['print.finished'], 'permissions': ['events']}


@pytest.fixture
def plug(tmp_path, monkeypatch):
    import modules.plugin_security as real
    real.DATA_DIR = str(tmp_path)
    real._status_cache.clear()
    os.makedirs(tmp_path / 'plugins', exist_ok=True)
    m = _load('plugins')
    m.DATA_DIR = str(tmp_path)
    monkeypatch.delenv('STELLIO_PLUGIN_PUBKEYS', raising=False)
    yield m, real
    real.DATA_DIR = None


def test_installation_audit_bloquant_puis_risque_accepte(plug):
    m, sec = plug
    bad = _zip({'plugin.json': json.dumps(MAN), 'main.py': "import subprocess\nsubprocess.run(['id'])\n"})
    with pytest.raises(m.PluginRefused) as e:
        m.install_bytes(bad)
    assert e.value.code == 'audit_blocked' and e.value.audit['blocking'] >= 1 and not os.path.exists(os.path.join(m._root(), 'demo'))
    res = m.install_bytes(bad, accept_risk=True)                                   # le propriétaire a explicitement accepté
    assert res['security']['accepted_risk'] and res['security']['audit'] == 'danger'
    assert sec.load_store()['demo']['accepted_risk'] is True


def test_installation_signature_exigee_pour_officiel_et_mise_a_jour_non_signee_refusee(plug, monkeypatch):
    m, sec = plug
    k, pub = _key()
    monkeypatch.setenv('STELLIO_PLUGIN_PUBKEYS', pub)
    good = _zip({'plugin.json': json.dumps(MAN), 'main.py': "print('ok')\n"})
    with pytest.raises(m.PluginRefused) as e:
        m.install_bytes(good, origin='official')                                    # officiel, clé configurée, non signé
    assert e.value.code == 'signature_required'
    sig = k.sign(sec.plugin_message('demo', '1.0', hashlib.sha256(good).hexdigest())).hex()
    assert m.install_bytes(good, origin='official', signature=sig)['security']['signature'] == 'valid'
    new = _zip({'plugin.json': json.dumps(dict(MAN, version='1.1')), 'main.py': "print('v2')\n"})
    with pytest.raises(m.PluginRefused) as e:
        m.install_bytes(new)                                                        # mise à jour non signée d'un plugin signé
    assert e.value.code == 'signature_downgrade'
    with pytest.raises(m.PluginRefused) as e:
        m.install_bytes(new, signature='00' * 64)                                   # signature invalide : toujours refusée
    assert e.value.code == 'signature_invalid'
    sig2 = k.sign(sec.plugin_message('demo', '1.1', hashlib.sha256(new).hexdigest())).hex()
    r = m.install_bytes(new, signature=sig2)
    assert r['action'] == 'updated' and r['security']['signature'] == 'valid'


def test_changement_de_cle_refuse_sauf_acceptation(plug, monkeypatch):
    m, sec = plug
    k1, p1 = _key()
    k2, p2 = _key()
    monkeypatch.setenv('STELLIO_PLUGIN_PUBKEYS', p1 + ',' + p2)
    a = _zip({'plugin.json': json.dumps(MAN), 'main.py': 'pass\n'})
    m.install_bytes(a, signature=k1.sign(sec.plugin_message('demo', '1.0', hashlib.sha256(a).hexdigest())).hex())
    b = _zip({'plugin.json': json.dumps(dict(MAN, version='1.2')), 'main.py': 'pass\n'})
    sb = k2.sign(sec.plugin_message('demo', '1.2', hashlib.sha256(b).hexdigest())).hex()
    with pytest.raises(m.PluginRefused) as e:
        m.install_bytes(b, signature=sb)
    assert e.value.code == 'key_changed'
    assert m.install_bytes(b, signature=sb, accept_key_change=True)['security']['signature'] == 'valid'


@needs_linux
def test_plugin_installe_s_execute_dans_le_bac_a_sable(plug):
    m, sec = plug
    if not sec.sandbox_status()['filesystem']:
        pytest.skip('Landlock indisponible sur ce noyau')
    code = ("import socket, json, os\nr = {}\n"
            "try:\n    socket.socket(socket.AF_INET); r['net'] = 'ok'\nexcept PermissionError:\n    r['net'] = 'refused'\n"
            "try:\n    open('/etc/passwd').read(); r['etc'] = 'ok'\nexcept PermissionError:\n    r['etc'] = 'refused'\n"
            "open(os.path.join(os.environ['STELLIO_PLUGIN_DATA'], 'etat.txt'), 'w').write('1'); r['data'] = 'ok'\nprint(json.dumps(r))\n")
    m.install_bytes(_zip({'plugin.json': json.dumps(MAN), 'main.py': code}), accept_risk=True)     # code volontairement « risqué » : l'audit le bloquerait sinon
    d, man = next((d, mm) for d, mm in m.installed() if mm['id'] == 'demo')
    res = m.run_plugin(d, man, 'print.finished', {}, {})
    assert res['ok'], res['error']
    assert json.loads(res['output']) == {'net': 'refused', 'etc': 'refused', 'data': 'ok'}
    assert res['sandbox']['network'] and res['sandbox']['filesystem']


def test_catalogue_signe_refuse_si_invalide_ou_absent_pour_l_officiel(plug, monkeypatch):
    m, sec = plug
    k, pub = _key()
    raw = json.dumps({'plugins': [{'id': 'demo', 'name': 'D', 'version': '1.0', 'url': 'https://github.com/stellio-app/stellio-plugins/demo.zip', 'sha256': 'a' * 64}]}).encode()
    sig = k.sign(sec.catalog_message(raw)).hex()
    store = {m.default_catalog_url(): raw, 'https://exemple.test/c.json': raw}
    sigs = {m.default_catalog_url() + '.sig': sig.encode()}

    def fake(url, max_bytes, timeout=15):
        url = url.split('?t=')[0]        # le paramètre anti-cache n'a pas d'incidence sur le contenu servi
        if url in store:
            return store[url]
        if url in sigs:
            return sigs[url]
        raise ValueError('404')
    m.http_get = fake
    assert m._fetch_catalog(m.default_catalog_url())[0]['catalog_signature'] == 'unverified'            # aucune clé : non vérifié, pas refusé
    monkeypatch.setenv('STELLIO_PLUGIN_PUBKEYS', pub)
    assert m._fetch_catalog(m.default_catalog_url())[0]['catalog_signature'] == 'valid'
    sigs[m.default_catalog_url() + '.sig'] = ('00' * 64).encode()
    got = m._fetch_catalog(m.default_catalog_url())                                                     # signature invalide : jamais de contenu non vérifié…
    assert got[0]['catalog_stale'] is True and got[0]['catalog_signature'] == 'valid'                    # …mais la dernière version VÉRIFIÉE reste consultable
    os.remove(m._cache_path(m.default_catalog_url()))                                                   # sans version mémorisée : refus net
    with pytest.raises(ValueError):
        m._fetch_catalog(m.default_catalog_url())                                                       # signature invalide
    del sigs[m.default_catalog_url() + '.sig']
    with pytest.raises(ValueError):
        m._fetch_catalog(m.default_catalog_url())                                                       # catalogue officiel non signé
    assert m._fetch_catalog('https://exemple.test/c.json')[0]['catalog_signature'] == 'unsigned'        # catalogue communautaire non signé : autorisé, signalé


def test_outil_pub_reaffiche_la_cle_publique(tmp_path):
    import subprocess, sys, pathlib
    tool = pathlib.Path(__file__).resolve().parent.parent / 'tools' / 'plugin_sign.py'
    key = tmp_path / 'k.key'
    a = subprocess.run([sys.executable, str(tool), 'keygen', str(key)], capture_output=True, text=True, check=True).stdout
    b = subprocess.run([sys.executable, str(tool), 'pub', str(key)], capture_output=True, text=True, check=True).stdout
    assert a.splitlines()[1] == b.splitlines()[0]          # même clé publique qu'à la création
