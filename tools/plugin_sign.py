#!/usr/bin/env python3
"""Stellio — signature Ed25519 des plugins et du catalogue (1.1.8). À lancer sur la machine de l'éditeur : la clé privée n'en sort jamais.

  python tools/plugin_sign.py keygen  <fichier_clé_privée>             crée la clé (droits 600) et affiche la clé PUBLIQUE à publier
  python tools/plugin_sign.py plugin  <fichier_clé_privée> <plugin.zip> affiche sha256 et signature à mettre dans catalog.json
  python tools/plugin_sign.py catalog <fichier_clé_privée> <catalog.json>  écrit <catalog.json>.sig (à publier à côté du catalogue)
  python tools/plugin_sign.py pub     <fichier_clé_privée>             réaffiche la clé PUBLIQUE d'une clé existante
  python tools/plugin_sign.py verify  <clé_publique_hex> <plugin.zip> <signature_hex>   contrôle une signature

La clé publique se renseigne dans `OFFICIAL_PUBLIC_KEYS` (modules/plugin_security.py), ou chez l'utilisateur dans STELLIO_PLUGIN_PUBKEYS
ou <données>/plugins/trusted_keys.json. Les messages signés sont définis dans modules/plugin_security.py (plugin_message / catalog_message).
"""
import hashlib
import io
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


def _sec():
    import importlib.util
    spec = importlib.util.spec_from_file_location('plugin_security_tool', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'modules', 'plugin_security.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _manifest(zip_bytes):
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    names = [n for n in zf.namelist() if n.endswith('plugin.json') and n.count('/') <= 1]
    if not names:
        sys.exit('plugin.json introuvable dans l\'archive.')
    return json.loads(zf.read(sorted(names, key=len)[0]).decode('utf-8'))


def main(argv):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
    sec = _sec()
    if len(argv) < 3:
        sys.exit(__doc__)
    cmd = argv[1]
    if cmd == 'keygen':
        path = argv[2]
        if os.path.exists(path):
            sys.exit(f'{path} existe déjà : refus d\'écraser une clé.')
        k = Ed25519PrivateKey.generate()
        raw = k.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(raw.hex() + '\n')
        pub = k.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
        print('Clé privée écrite dans', path, '(à sauvegarder hors ligne, ne jamais publier).')
        print('Clé publique :', pub)
        print('Empreinte    :', sec.fingerprint(pub))
        return
    if cmd == 'verify':
        pub, zpath, sig = argv[2], argv[3], argv[4]
        data = open(zpath, 'rb').read()
        man = _manifest(data)
        ok = sec.verify(sig, sec.plugin_message(man['id'], str(man.get('version') or '0'), hashlib.sha256(data).hexdigest()), [pub.lower()])
        print('VALIDE' if ok else 'INVALIDE')
        sys.exit(0 if ok else 1)
    priv = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(open(argv[2]).read().strip()))
    if cmd == 'pub':
        pub = priv.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
        print('Clé publique :', pub)
        print('Empreinte    :', sec.fingerprint(pub))
        return
    if cmd == 'plugin':
        data = open(argv[3], 'rb').read()
        man = _manifest(data)
        sha = hashlib.sha256(data).hexdigest()
        sig = priv.sign(sec.plugin_message(man['id'], str(man.get('version') or '0'), sha)).hex()
        print(json.dumps({'id': man['id'], 'version': str(man.get('version') or '0'), 'sha256': sha, 'signature': sig}, indent=2))
    elif cmd == 'catalog':
        raw = open(argv[3], 'rb').read()
        out = argv[3] + '.sig'
        open(out, 'w').write(priv.sign(sec.catalog_message(raw)).hex() + '\n')
        print('Écrit :', out, '(republier à chaque modification du catalogue)')
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main(sys.argv)
