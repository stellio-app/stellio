@echo off
setlocal EnableExtensions
chcp 65001 >nul
set "PYTHONUTF8=1"
rem ====================================================================
rem  Stellio - signature des plugins
rem  A placer dans un dossier (ex. "nouveaux plugins") avec les .zip a signer.
rem  Le .bat liste les .zip du dossier : on choisit celui a signer.
rem  La cle privee stellio_plugins.key est cherchee dans le meme dossier
rem  (sinon : demandee). Elle ne doit JAMAIS aller dans un depot ni un zip.
rem  Prerequis : Python 3 (le paquet "cryptography" est installe au besoin).
rem  Fichier autonome : aucun autre fichier de Stellio n'est necessaire.
rem ====================================================================
set "PY="
set "PYOK="
rem Python de Stellio (dossier voisin, sans rien deplacer) puis Python du systeme.
call :essai "%~dp0..\stellio3.0\python\python.exe"
call :essai "%~dp0..\stellio3.0\python\venv\Scripts\python.exe"
call :essai "%~dp0..\python\python.exe"
call :essai "%~dp0python\python.exe"
call :essai "py -3"
call :essai "python"
if not defined PY set "PY=%PYOK%"
if not defined PY (
  echo [ERREUR] Aucun Python 3 utilisable n'a ete trouve.
  echo Installez-le depuis https://www.python.org/downloads/ ou placez ce fichier
  echo a cote du dossier "stellio3.0".
  goto :fin
)
echo Python utilise : %PY%
%PY% -c "import cryptography" >nul 2>nul
if errorlevel 1 (
  echo Installation du paquet "cryptography"...
  %PY% -m pip install --user cryptography
  %PY% -c "import cryptography" >nul 2>nul
  if errorlevel 1 (
    echo [ERREUR] Installation de "cryptography" impossible.
    goto :fin
  )
)
%PY% -c "import sys;t=open(sys.argv[1],encoding='utf-8').read();exec(compile(t.split('#PY'+'BEGIN')[1],'signer','exec'))" "%~f0" "%~dp0." "%~1"
:fin
echo.
pause
endlocal
exit /b
:essai
if defined PY exit /b
set "C=%~1"
if exist "%~1" set C="%~1"
%C% -c "import sys; sys.exit(0 if sys.version_info[0]==3 else 1)" >nul 2>nul || exit /b
if not defined PYOK set "PYOK=%C%"
%C% -c "import cryptography" >nul 2>nul && set "PY=%C%"
exit /b
#PYBEGIN
import glob, hashlib, io, json, os, shutil, sys, time, urllib.request, zipfile
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

folder = os.path.abspath(sys.argv[2])
OUT = os.path.join(folder, 'a-publier')      # tous les fichiers générés arrivent ici
CUR = {'cat': None}                          # catalogue en cours (plusieurs plugins signés dans la même séance)
key_arg = (sys.argv[3] if len(sys.argv) > 3 else '').strip('"')


def find_key():
    for p in (key_arg if key_arg.lower().endswith('.key') else '', os.path.join(folder, 'stellio_plugins.key'),
              os.path.join(os.path.dirname(folder), 'stellio_plugins.key'), os.path.join(os.path.expanduser('~'), 'stellio_plugins.key')):
        if p and os.path.isfile(p):
            return p
    while True:
        p = input('Chemin de la clé privée stellio_plugins.key (vide = quitter) : ').strip().strip('"')
        if not p:
            sys.exit(1)
        if os.path.isfile(p):
            return p
        print('Introuvable :', p)


def load_key(path):
    try:
        return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(open(path, encoding='utf-8').read().strip()))
    except Exception:
        sys.exit('[ERREUR] Clé privée illisible : %s (attendu : 64 caractères hexadécimaux)' % path)


def pub_hex(k):
    return k.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()


def manifest(data):
    zf = zipfile.ZipFile(io.BytesIO(data))
    names = sorted([n for n in zf.namelist() if n.endswith('plugin.json') and n.count('/') <= 1], key=len)
    if not names:
        raise ValueError("plugin.json introuvable dans l'archive")
    return json.loads(zf.read(names[0]).decode('utf-8'))


def sign_plugin(k, path):
    data = open(path, 'rb').read()
    man = manifest(data)
    pid, ver = str(man.get('id') or ''), str(man.get('version') or '0')
    sha = hashlib.sha256(data).hexdigest()
    sig = k.sign(('stellio-plugin-v1\n%s\n%s\n%s' % (pid, ver, sha)).encode('utf-8')).hex()
    out = {'id': pid, 'version': ver, 'sha256': sha, 'signature': sig}
    k.public_key().verify(bytes.fromhex(sig), ('stellio-plugin-v1\n%s\n%s\n%s' % (pid, ver, sha)).encode('utf-8'))   # contrôle de la signature produite
    os.makedirs(OUT, exist_ok=True)
    shutil.copy2(path, os.path.join(OUT, os.path.basename(path)))      # le zip à joindre à la release, tel quel
    dest = os.path.join(OUT, os.path.basename(path) + '.signature.json')
    open(dest, 'w', encoding='utf-8').write(json.dumps(out, indent=2) + '\n')
    print(json.dumps(out, indent=2))
    print('\nEnregistré dans :', dest)
    update_catalog(k, path, man, sha, sig)


CAT_URL = 'https://raw.githubusercontent.com/stellio-app/stellio-plugins/main/catalog.json'
REL_URL = 'https://github.com/stellio-app/stellio-plugins/releases/download/%s/%s'
RAW_URL = 'https://raw.githubusercontent.com/stellio-app/stellio-plugins/main/plugins/%s/%s'
TREE_URL = 'https://github.com/stellio-app/stellio-plugins/tree/main/plugins/%s'


def fetch_catalog():
    if CUR['cat'] is not None:
        return CUR['cat']
    local = os.path.join(OUT, 'catalog.json') if os.path.isfile(os.path.join(OUT, 'catalog.json')) else os.path.join(folder, 'catalog.json')
    try:
        req = urllib.request.Request(CAT_URL + '?t=%d' % time.time(), headers={'User-Agent': 'stellio-signer', 'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(req, timeout=30) as r:
            cat = json.loads(r.read().decode('utf-8'))
        print('Catalogue récupéré depuis GitHub.')
        return cat
    except Exception as e:
        print('[ATTENTION] Récupération du catalogue GitHub impossible :', e)
    if os.path.isfile(local):
        rep = input('Utiliser le catalog.json local (%s) ? (o/N) ' % local).strip().lower()
        if rep in ('o', 'oui', 'y'):
            return json.loads(open(local, encoding='utf-8').read())
    raise RuntimeError('catalogue indisponible : rien n\'a été modifié')


def update_catalog(k, zpath, man, sha, sig):
    cat = fetch_catalog()
    plugins = cat.setdefault('plugins', [])
    pid, ver = str(man.get('id') or ''), str(man.get('version') or '0')
    name = man.get('name')
    if isinstance(name, dict):
        name = name.get('en') or name.get('fr') or pid
    zname = os.path.basename(zpath)
    fields = {'name': str(name or pid), 'version': ver, 'author': str(man.get('author') or 'Stellio'),
              'url': REL_URL % (os.path.splitext(zname)[0], zname), 'sha256': sha, 'signature': sig,
              'permissions': list(man.get('permissions') or [])}
    entry = next((e for e in plugins if e.get('id') == pid), None)
    if entry is None:
        entry = {'id': pid}
        entry.update(fields)
        entry['logo'] = RAW_URL % (pid, 'logo.png')
        entry['homepage'] = TREE_URL % pid
        plugins.append(entry)
        print("Nouvelle entrée ajoutée au catalogue : %s %s" % (pid, ver))
    else:
        entry.update(fields)
        print("Entrée mise à jour dans le catalogue : %s -> %s" % (pid, ver))
    CUR['cat'] = cat
    os.makedirs(OUT, exist_ok=True)
    dest = os.path.join(OUT, 'catalog.json')
    open(dest, 'w', encoding='utf-8', newline='\n').write(json.dumps(cat, indent=2, ensure_ascii=False) + '\n')
    print('Enregistré :', dest)
    sign_catalog(k, dest)
    print('\nÀ FAIRE :')
    print('  1. Release GitHub, tag "%s" : joindre CE zip tel quel (%s).' % (os.path.splitext(zname)[0], zname))
    print('  2. Dans le dépôt stellio-plugins : envoyer catalog.json et catalog.json.sig du dossier a-publier')
    print('     (téléverser les fichiers, sans copier-coller : la signature porte sur les octets exacts).')
    print('  3. Ajouter plugins/%s/ (plugin.json, logo.png...) si ce n\'est pas déjà fait.' % pid)


def sign_catalog(k, path):
    os.makedirs(OUT, exist_ok=True)
    if os.path.dirname(os.path.abspath(path)) != OUT:
        shutil.copy2(path, os.path.join(OUT, os.path.basename(path)))
        path = os.path.join(OUT, os.path.basename(path))
    raw = open(path, 'rb').read()
    sig = k.sign(b'stellio-catalog-v1\n' + raw).hex()
    dest = path + '.sig'
    open(dest, 'w', encoding='utf-8').write(sig + '\n')
    print('Signature écrite :', dest)


def main():
    print('Dossier :', folder)
    keyfile = find_key()
    k = load_key(keyfile)
    print('Clé     :', keyfile)
    print('Clé publique (à mettre dans OFFICIAL_PUBLIC_KEYS) :', pub_hex(k))
    while True:
        zips = sorted(glob.glob(os.path.join(folder, '*.zip')), key=lambda p: os.path.basename(p).lower())
        cat = os.path.join(OUT, 'catalog.json') if os.path.isfile(os.path.join(OUT, 'catalog.json')) else os.path.join(folder, 'catalog.json')
        items = [('plugin', z) for z in zips] + ([('catalog', cat)] if os.path.isfile(cat) else [])
        print()
        if not items:
            print('Aucun fichier .zip dans ce dossier. Placez-y les plugins à signer.')
            return
        print('Fichiers à signer :')
        for i, (kind, p) in enumerate(items, 1):
            lab = ''
            if kind == 'catalog':
                lab = '   (re-signer le catalogue seulement)'
            print('  %d) %s%s' % (i, os.path.basename(p), lab))
        if len(zips) > 1:
            print('  T) Tout signer (tous les .zip, un seul catalogue mis à jour)')
        print('  0) Quitter')
        c = input('Votre choix : ').strip()
        if c in ('0', 'q', ''):
            if os.path.isdir(OUT):
                print('Fichiers générés dans :', OUT)
                try:
                    os.startfile(OUT)
                except Exception:
                    pass
            return
        if c.lower() == 't' and len(zips) > 1:
            for z in zips:
                print('\n==== %s ====' % os.path.basename(z))
                try:
                    sign_plugin(k, z)
                except Exception as e:
                    print('[ERREUR]', e)
            continue
        if not c.isdigit() or not (1 <= int(c) <= len(items)):
            print('Choix invalide.')
            continue
        kind, p = items[int(c) - 1]
        print()
        try:
            (sign_catalog if kind == 'catalog' else sign_plugin)(k, p)
        except Exception as e:
            print('[ERREUR]', e)


main()
