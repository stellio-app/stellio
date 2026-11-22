"""Stellio — durcissement des plugins externes (1.1.8) : signature, audit automatique, restrictions.

Trois couches, chacune dit honnêtement ce qu'elle garantit :

1. SIGNATURE (Ed25519). Le catalogue et chaque plugin peuvent être signés. Message signé d'un plugin :
   `stellio-plugin-v1\\n<id>\\n<version>\\n<sha256 de l'archive>` ; du catalogue : `stellio-catalog-v1\\n<octets exacts du fichier>`.
   Les clés publiques de confiance viennent de `OFFICIAL_PUBLIC_KEYS`, de la variable `STELLIO_PLUGIN_PUBKEYS` (hex, séparées par des virgules)
   et du fichier `<données>/plugins/trusted_keys.json`. Tant qu'AUCUNE clé n'est configurée, rien n'est exigé (l'empreinte SHA-256 du catalogue
   reste la seule garantie d'intégrité) et l'écran le dit. Dès qu'une clé existe : une signature invalide est toujours refusée, un plugin ou un
   catalogue OFFICIEL non signé est refusé, et une mise à jour non signée (ou signée par une autre clé) d'un plugin déjà signé est refusée.
   Ce qu'une signature prouve : que l'archive vient du détenteur de la clé. Pas que le code est sans danger.

2. AUDIT AUTOMATIQUE (analyse statique, sans exécuter le code). Imports et appels dangereux comparés aux permissions déclarées : réseau non
   déclaré, lancement de processus, code dynamique (eval/exec/__import__, pickle, ctypes), accès à l'environnement, lecture hors du dossier du plugin,
   pages HTML qui chargent des ressources externes. Un audit peut rater du code obfusqué : c'est un filet, pas une preuve. Les constats BLOQUANTS
   refusent l'installation, sauf acceptation explicite du risque par le propriétaire (ou signature d'une clé de confiance).

3. RESTRICTIONS À L'EXÉCUTION. Sous LINUX, réelles et appliquées par le noyau au processus du plugin : fichiers par Landlock (lecture seule du système
   et du dossier du plugin, écriture uniquement dans son sous-dossier `data/`, pas d'accès au reste du disque ni aux données de Stellio) ; réseau par
   seccomp (création de sockets Internet refusée, sauf permission `network` ou `api:*`). Landlock demande un noyau ≥ 5.13 : sinon la restriction de
   fichiers n'est PAS appliquée et l'écran l'indique. Sous Windows et macOS, aucune restriction du noyau n'est appliquée : les permissions
   restent déclaratives (audit + acceptation), ce que l'écran affiche. Un plugin autorisé à utiliser le réseau n'est pas limité à certains sites.
"""
import ast
import base64
import ctypes
import hashlib
import json
import os
import platform
import re
import struct
import sys
import time

_REQUIRED = ('DATA_DIR', 'app', 'app_logger', 'jsonify', 'login_required', 'session')
_OPTIONAL = ()
_OVERRIDABLE = ()

_MAIN = {}
DATA_DIR = None
app = None
app_logger = None
jsonify = None
login_required = None
session = None

# Clé publique officielle (64 caractères hex) à renseigner après `python tools/plugin_sign.py keygen` (la clé privée ne quitte JAMAIS la machine de l'éditeur).
OFFICIAL_PUBLIC_KEYS = ("01573098fb48f9f90291fda0b89b99309cb62ef2be47c728ede667fbc30d2b7a",)
SIG_RE = re.compile(r'^[0-9a-f]{128}$')
KEY_RE = re.compile(r'^[0-9a-f]{64}$')


# ── 1. signature ─────────────────────────────────────────────────────────

def plugin_message(pid, version, sha256_hex):
    return f"stellio-plugin-v1\n{pid}\n{version}\n{str(sha256_hex).lower()}".encode('utf-8')


def catalog_message(raw):
    return b"stellio-catalog-v1\n" + bytes(raw)


def fingerprint(pub_hex):
    return hashlib.sha256(bytes.fromhex(pub_hex)).hexdigest()[:16]


def trusted_keys(extra=()):
    """Clés publiques de confiance (hex), sans doublon, uniquement les clés bien formées."""
    keys = list(OFFICIAL_PUBLIC_KEYS) + [k.strip().lower() for k in (os.environ.get('STELLIO_PLUGIN_PUBKEYS') or '').split(',') if k.strip()] + list(extra)
    try:
        path = os.path.join(DATA_DIR, 'plugins', 'trusted_keys.json') if DATA_DIR else ''
        if path and os.path.isfile(path):
            data = json.load(open(path, encoding='utf-8'))
            keys += [str(k).strip().lower() for k in data] if isinstance(data, list) else []
    except (OSError, ValueError, TypeError):
        pass
    return list(dict.fromkeys(k for k in keys if KEY_RE.match(k)))


def verify(signature_hex, message, keys):
    """Empreinte de la clé qui a signé `message`, ou None. Ne lève jamais."""
    sig = str(signature_hex or '').strip().lower()
    if not SIG_RE.match(sig):
        return None
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except Exception:
        return None
    for k in keys:
        try:
            Ed25519PublicKey.from_public_bytes(bytes.fromhex(k)).verify(bytes.fromhex(sig), message)
            return fingerprint(k)
        except (InvalidSignature, ValueError):
            continue
    return None


def signature_status(signature_hex, pid, version, sha256_hex, keys=None):
    """{'status': 'valid'|'invalid'|'unsigned'|'unverifiable', 'key': empreinte|''}.
    `unverifiable` = signature fournie mais aucune clé de confiance configurée (on ne peut ni la croire ni la rejeter)."""
    keys = trusted_keys() if keys is None else keys
    if not str(signature_hex or '').strip():
        return {'status': 'unsigned', 'key': ''}
    if not keys:
        return {'status': 'unverifiable', 'key': ''}
    fp = verify(signature_hex, plugin_message(pid, version, sha256_hex), keys)
    return {'status': 'valid', 'key': fp} if fp else {'status': 'invalid', 'key': ''}


def signature_policy(sig, official, keys_configured, previous=None, accept_key_change=False):
    """(autorisé, code). Fonction pure.
    - signature invalide : toujours refusée ;
    - clés configurées + plugin officiel non valablement signé : refusé ;
    - plugin déjà installé avec une signature valide : la mise à jour doit l'être aussi, par la même clé (sauf acceptation explicite)."""
    st = sig.get('status')
    if st == 'invalid':
        return False, 'signature_invalid'
    if official and keys_configured and st != 'valid':
        return False, 'signature_required'
    prev = previous or {}
    if prev.get('signature') == 'valid' and not accept_key_change:
        if st != 'valid':
            return False, 'signature_downgrade'
        if prev.get('key') and sig.get('key') != prev.get('key'):
            return False, 'key_changed'
    return True, 'ok'


# ── 2. audit statique ────────────────────────────────────────────────────

# module racine → (catégorie, gravité). `network` : permission « network » ou « api:* » requise. `process`/`dynamic` : jamais déclarables.
RISKY_IMPORTS = {
    'socket': ('network', 'high'), 'ssl': ('network', 'high'), 'urllib': ('network', 'high'), 'http': ('network', 'high'), 'requests': ('network', 'high'),
    'httpx': ('network', 'high'), 'aiohttp': ('network', 'high'), 'ftplib': ('network', 'high'), 'smtplib': ('network', 'high'), 'telnetlib': ('network', 'high'),
    'websocket': ('network', 'high'), 'websockets': ('network', 'high'), 'paramiko': ('network', 'high'), 'xmlrpc': ('network', 'high'),
    'subprocess': ('process', 'high'), 'multiprocessing': ('process', 'high'), 'pty': ('process', 'high'), 'pexpect': ('process', 'high'), 'sh': ('process', 'high'),
    'ctypes': ('dynamic', 'high'), 'cffi': ('dynamic', 'high'), 'marshal': ('dynamic', 'high'), 'pickle': ('dynamic', 'medium'), 'importlib': ('dynamic', 'medium'),
    'runpy': ('dynamic', 'high'), 'code': ('dynamic', 'medium'), 'codeop': ('dynamic', 'medium'),
}
RISKY_CALLS = {
    'eval': ('dynamic', 'high'), 'exec': ('dynamic', 'high'), 'compile': ('dynamic', 'medium'), '__import__': ('dynamic', 'high'),
    'os.system': ('process', 'high'), 'os.popen': ('process', 'high'), 'os.execv': ('process', 'high'), 'os.execve': ('process', 'high'), 'os.execvp': ('process', 'high'),
    'os.spawnl': ('process', 'high'), 'os.spawnv': ('process', 'high'), 'os.fork': ('process', 'high'), 'os.kill': ('process', 'medium'),
    'shutil.rmtree': ('filesystem', 'medium'), 'os.remove': ('filesystem', 'low'), 'os.unlink': ('filesystem', 'low'),
    'os.getenv': ('environment', 'low'), 'os.environ.get': ('environment', 'low'),
    'os.path.expanduser': ('filesystem', 'medium'), 'pathlib.Path.home': ('filesystem', 'medium'),
}
BLOCKING = {'network', 'process', 'dynamic'}           # catégories qui bloquent (réseau : seulement si non déclaré)
MAX_AUDIT_BYTES = 512 * 1024
HTML_EXT = ('.html', '.htm')
EXT_URL_RE = re.compile(r'''(?:src|href)\s*=\s*["']\s*(?:https?:)?//''', re.I)
HTML_DANGER = (('eval(', 'dynamic'), ('document.cookie', 'environment'), ('new WebSocket', 'network'), ('XMLHttpRequest', 'network'), ('fetch(', 'network'))
B64_BLOB_RE = re.compile(r'[A-Za-z0-9+/=]{400,}')


def _dotted(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return '.'.join(reversed(parts))
    return ''


def _finding(fid, sev, cat, file, line, detail, blocking=False):
    return {'id': fid, 'severity': sev, 'category': cat, 'file': file, 'line': line, 'detail': detail, 'blocking': blocking}


def audit_python(source, filename, permissions):
    """Constats d'un fichier Python (liste). Ne lève jamais : un fichier illisible est lui-même un constat."""
    perms = set(permissions or [])
    net_ok = bool(perms & {'network', 'api:read', 'api:write'})
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as e:
        return [_finding('syntax', 'medium', 'dynamic', filename, getattr(e, 'lineno', 0) or 0, 'Fichier Python illisible (syntaxe).', False)]
    out = []

    def add(cat, sev, line, fid, detail):
        blocking = cat in BLOCKING and sev == 'high' and not (cat == 'network' and net_ok)
        out.append(_finding(fid, sev, cat, filename, line, detail, blocking))

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mods = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or '']
            for m in mods:
                root = m.split('.')[0]
                if root in RISKY_IMPORTS:
                    cat, sev = RISKY_IMPORTS[root]
                    add(cat, sev, node.lineno, 'import:' + root, f"import {m}")
        elif isinstance(node, ast.Call):
            name = _dotted(node.func)
            if name in RISKY_CALLS:
                cat, sev = RISKY_CALLS[name]
                add(cat, sev, node.lineno, 'call:' + name, f"appel à {name}()")
            elif name == 'open' and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                p = node.args[0].value.replace('\\', '/')
                if p.startswith('/') or p.startswith('~') or '..' in p.split('/') or re.match(r'^[A-Za-z]:/', p):
                    add('filesystem', 'medium', node.lineno, 'open:outside', f"lecture/écriture hors du dossier du plugin : {p[:80]}")
        elif isinstance(node, ast.Attribute) and _dotted(node) == 'os.environ':
            add('environment', 'low', node.lineno, 'env:os.environ', "lit les variables d'environnement")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value) >= 400 and B64_BLOB_RE.fullmatch(node.value.strip()):
            add('dynamic', 'medium', node.lineno, 'blob:encoded', "grand bloc encodé (code possiblement masqué)")
    if 'STELLIO_API_URL' in source and not (perms & {'api:read', 'api:write'}):
        out.append(_finding('api:undeclared', 'high', 'network', filename, 0, "utilise l'API de Stellio sans permission api:read / api:write", True))
    return out


def audit_dir(plugin_dir, manifest):
    """Audit complet d'un dossier de plugin. Retourne {'level': 'ok'|'warn'|'danger', 'findings': [...], 'blocking': n, 'files': n}.
    danger = au moins un constat bloquant ; warn = constats non bloquants ; ok = rien."""
    perms = manifest.get('permissions') or []
    findings, files = [], 0
    root = os.path.realpath(plugin_dir)
    for base, _dirs, names in os.walk(root):
        for n in sorted(names):
            path = os.path.join(base, n)
            rel = os.path.relpath(path, root).replace('\\', '/')
            low = n.lower()
            try:
                if os.path.islink(path):
                    findings.append(_finding('symlink', 'high', 'filesystem', rel, 0, 'lien symbolique', True))
                    continue
                if os.path.getsize(path) > MAX_AUDIT_BYTES and low.endswith(('.py', '.html', '.htm', '.js')):
                    findings.append(_finding('big', 'low', 'dynamic', rel, 0, 'fichier de code très volumineux : non analysé en détail', False))
                    continue
                if low.endswith('.py'):
                    files += 1
                    findings += audit_python(open(path, encoding='utf-8', errors='replace').read(), rel, perms)
                elif low.endswith(HTML_EXT + ('.js',)):
                    files += 1
                    text = open(path, encoding='utf-8', errors='replace').read()
                    if low.endswith(HTML_EXT) and EXT_URL_RE.search(text):
                        findings.append(_finding('html:external', 'medium', 'network', rel, 0, 'la page charge une ressource externe', False))
                    for needle, cat in HTML_DANGER:
                        if needle in text:
                            findings.append(_finding('html:' + needle.strip('('), 'low', cat, rel, 0, f"utilise {needle}", False))
                elif low.endswith(('.so', '.dll', '.dylib', '.pyd', '.exe', '.bat', '.sh', '.cmd')):
                    findings.append(_finding('binary', 'high', 'process', rel, 0, 'fichier exécutable ou bibliothèque native', True))
            except OSError:
                continue
    seen, uniq = set(), []
    for f in findings:                                     # un constat par (id, fichier) : pas de bruit répété
        k = (f['id'], f['file'])
        if k not in seen:
            seen.add(k)
            uniq.append(f)
    blocking = sum(1 for f in uniq if f['blocking'])
    return {'level': 'danger' if blocking else ('warn' if uniq else 'ok'), 'findings': uniq[:60], 'blocking': blocking, 'files': files}


# ── mémoire des vérifications (signature, audit) par plugin ─────────────

def _store_path():
    return os.path.join(DATA_DIR, 'plugins', '.security.json')


def load_store():
    try:
        d = json.load(open(_store_path(), encoding='utf-8'))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def save_record(pid, sig, audit, accepted_risk=False):
    d = load_store()
    d[pid] = {'signature': sig.get('status', 'unsigned'), 'key': sig.get('key', ''), 'audit': audit.get('level', 'ok'), 'blocking': audit.get('blocking', 0),
              'findings': [{k: f[k] for k in ('id', 'severity', 'category', 'file', 'line', 'detail', 'blocking')} for f in (audit.get('findings') or [])[:30]],
              'accepted_risk': bool(accepted_risk), 'at': time.time()}
    os.makedirs(os.path.dirname(_store_path()), exist_ok=True)
    tmp = _store_path() + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(d, f)
    os.replace(tmp, _store_path())


def drop_record(pid):
    d = load_store()
    if d.pop(pid, None) is not None:
        tmp = _store_path() + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(d, f)
        os.replace(tmp, _store_path())


# ── 3. restrictions à l'exécution ────────────────────────────────────────

LL_EXEC, LL_WRITE, LL_READ, LL_READDIR = 1 << 0, 1 << 1, 1 << 2, 1 << 3
LL_RMDIR, LL_RMFILE, LL_MKCHAR, LL_MKDIR, LL_MKREG, LL_MKSOCK, LL_MKFIFO, LL_MKBLOCK, LL_MKSYM = (1 << i for i in range(4, 13))
LL_REFER, LL_TRUNC, LL_IOCTL = 1 << 13, 1 << 14, 1 << 15
FILE_RIGHTS = LL_EXEC | LL_WRITE | LL_READ | LL_TRUNC | LL_IOCTL
SYS_LL_CREATE, SYS_LL_ADD, SYS_LL_RESTRICT = 444, 445, 446
PR_SET_NO_NEW_PRIVS, PR_SET_SECCOMP, SECCOMP_MODE_FILTER = 38, 22, 2
ARCH = {'x86_64': (0xC000003E, 41), 'aarch64': (0xC00000B7, 198)}       # (AUDIT_ARCH, numéro de l'appel socket)
SYS_IO_URING_SETUP = 425
BLOCKED_FAMILIES = (2, 10, 17)                                          # AF_INET, AF_INET6, AF_PACKET

_status_cache = {}


def landlock_abi():
    """Version de Landlock du noyau (≥ 1), 0 si indisponible."""
    if not sys.platform.startswith('linux') or platform.machine() not in ARCH:
        return 0
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        libc.syscall.restype = ctypes.c_long
        r = libc.syscall(SYS_LL_CREATE, None, 0, 1)
        return int(r) if r > 0 else 0
    except Exception:
        return 0


def sandbox_status():
    """Ce que cette machine sait réellement appliquer. {'platform', 'filesystem', 'network', 'enforced', 'landlock_abi', 'reason'}.
    `reason` : 'ok' | 'platform' (pas Linux) | 'arch' | 'kernel' (Landlock absent) | 'disabled' (STELLIO_PLUGIN_SANDBOX=off)."""
    if 'v' in _status_cache:
        return dict(_status_cache['v'])
    plat = 'linux' if sys.platform.startswith('linux') else ('windows' if os.name == 'nt' else ('macos' if sys.platform == 'darwin' else sys.platform))
    st = {'platform': plat, 'filesystem': False, 'network': False, 'enforced': False, 'landlock_abi': 0, 'reason': 'ok'}
    if str(os.environ.get('STELLIO_PLUGIN_SANDBOX') or '').lower() in ('0', 'off', 'false', 'no'):
        st['reason'] = 'disabled'
    elif plat != 'linux':
        st['reason'] = 'platform'
    elif platform.machine() not in ARCH:
        st['reason'] = 'arch'
    else:
        st['network'] = True
        st['landlock_abi'] = landlock_abi()
        st['filesystem'] = st['landlock_abi'] > 0
        st['reason'] = 'ok' if st['filesystem'] else 'kernel'
        st['enforced'] = True
    _status_cache['v'] = st
    return dict(st)


def build_seccomp_filter(arch=None):
    """Programme BPF (octets) : refuse (EPERM) socket(AF_INET/AF_INET6/AF_PACKET) et io_uring_setup ; toute autre architecture que l'architecture native est refusée."""
    audit_arch, nr_socket = ARCH[arch or platform.machine()]
    EPERM_RET = 0x00050000 | 1
    ALLOW = 0x7FFF0000
    LD, JEQ, RET = 0x20, 0x15, 0x06
    prog = []

    def ins(code, jt, jf, k):
        prog.append((code, jt, jf, k))
    ins(LD, 0, 0, 4)                                        # arch
    ins(JEQ, 1, 0, audit_arch)                              # bonne architecture : on saute le refus
    ins(RET, 0, 0, EPERM_RET)
    ins(LD, 0, 0, 0)                                        # numéro d'appel
    ins(JEQ, 0, 1, SYS_IO_URING_SETUP)                      # io_uring permettrait de créer des sockets sans passer par socket()
    ins(RET, 0, 0, EPERM_RET)
    ins(JEQ, 1, 0, nr_socket)                               # socket(domain, …)
    ins(RET, 0, 0, ALLOW)
    ins(LD, 0, 0, 16)                                       # args[0] (octets bas, petit-boutiste)
    for i, fam in enumerate(BLOCKED_FAMILIES):
        remaining = len(BLOCKED_FAMILIES) - i - 1
        ins(JEQ, remaining + 1, 0, fam)                     # famille bloquée : saute au refus (placé après les comparaisons)
    ins(RET, 0, 0, ALLOW)
    ins(RET, 0, 0, EPERM_RET)
    return b''.join(struct.pack('=HBBI', *i) for i in prog)


class _Rule(ctypes.Structure):
    _pack_ = 1
    _fields_ = [('allowed_access', ctypes.c_uint64), ('parent_fd', ctypes.c_int32)]


def _apply_landlock(libc, abi, ro, rw, rw_files=(), ro_files=()):
    handled = (1 << 13) - 1 | (LL_REFER if abi >= 2 else 0) | (LL_TRUNC if abi >= 3 else 0) | (LL_IOCTL if abi >= 5 else 0)
    attr = ctypes.c_uint64(handled)
    fd = libc.syscall(SYS_LL_CREATE, ctypes.byref(attr), 8, 0)
    if fd < 0:
        raise OSError(ctypes.get_errno(), 'landlock_create_ruleset')
    try:
        read_dir = LL_EXEC | LL_READ | LL_READDIR
        write_dir = LL_READ | LL_READDIR | LL_WRITE | LL_RMDIR | LL_RMFILE | LL_MKDIR | LL_MKREG | LL_TRUNC
        for paths, access, files in ((ro, read_dir, False), (rw, write_dir, False), (ro_files, (LL_READ | LL_EXEC), True), (rw_files, (LL_READ | LL_WRITE | LL_TRUNC), True)):
            for p in paths:
                try:
                    pfd = os.open(p, os.O_PATH | os.O_CLOEXEC)
                except OSError:
                    continue                                 # chemin absent sur cette machine : rien à autoriser
                try:
                    acc = (access & FILE_RIGHTS & handled) if files else (access & handled)
                    rule = _Rule(acc, pfd)
                    if libc.syscall(SYS_LL_ADD, fd, 1, ctypes.byref(rule), 0) < 0:
                        raise OSError(ctypes.get_errno(), 'landlock_add_rule ' + p)
                finally:
                    os.close(pfd)
        if libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), 'no_new_privs')
        if libc.syscall(SYS_LL_RESTRICT, fd, 0) < 0:
            raise OSError(ctypes.get_errno(), 'landlock_restrict_self')
    finally:
        os.close(fd)


def _apply_seccomp(libc, blob):
    n = len(blob) // 8
    buf = ctypes.create_string_buffer(blob, len(blob))

    class Prog(ctypes.Structure):
        _fields_ = [('len', ctypes.c_ushort), ('filter', ctypes.c_void_p)]
    prog = Prog(n, ctypes.cast(buf, ctypes.c_void_p))
    if libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), 'no_new_privs')
    if libc.prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, ctypes.byref(prog), 0, 0) != 0:
        raise OSError(ctypes.get_errno(), 'seccomp')


def system_read_paths(python_exe=None):
    """Dossiers que le processus Python d'un plugin doit pouvoir LIRE pour démarrer (système, interpréteur)."""
    paths = ['/usr', '/lib', '/lib64', '/lib32', '/bin', '/sbin', '/opt', sys.prefix, sys.base_prefix, sys.exec_prefix]
    if python_exe:
        real = os.path.realpath(python_exe)
        paths += [os.path.dirname(os.path.dirname(real)), os.path.dirname(real)]
    return [p for p in dict.fromkeys(os.path.realpath(p) for p in paths) if os.path.isdir(p)]


def make_preexec(plugin_dir, data_dir, allow_network, python_exe=None, extra=None):
    """Fonction à passer à subprocess (preexec_fn) : applique les restrictions du noyau avant l'exécution du plugin.
    Retourne (fonction | None, état) ; None si rien n'est applicable ici (l'état dit pourquoi)."""
    st = sandbox_status()
    st['network_restricted'] = bool(st['network'] and not allow_network)
    st['filesystem_restricted'] = bool(st['filesystem'])
    if not st['enforced']:
        return None, st
    abi = st['landlock_abi']
    ro = system_read_paths(python_exe) + [os.path.realpath(plugin_dir)]
    ro_files = ['/etc/ld.so.cache', '/etc/localtime', '/etc/resolv.conf', '/etc/hosts', '/etc/nsswitch.conf', '/etc/ssl/certs', '/dev/urandom', '/dev/random', '/dev/zero']
    ro_dirs_extra = ['/etc/ssl', '/etc/pki', '/etc/ca-certificates']
    rw_files = ['/dev/null']
    rw = [os.path.realpath(data_dir)]
    blob = build_seccomp_filter() if st['network_restricted'] else None
    ro_all = ro + [p for p in ro_dirs_extra if os.path.isdir(p)] + list(extra or [])
    ro_files = [p for p in ro_files if os.path.exists(p) and not os.path.isdir(p)]

    def apply():
        libc = ctypes.CDLL(None, use_errno=True)
        libc.syscall.restype = ctypes.c_long
        if blob:
            _apply_seccomp(libc, blob)
        if abi:
            _apply_landlock(libc, abi, ro_all, rw, rw_files, ro_files)
    return apply, st


# ── routes ───────────────────────────────────────────────────────────────

def api_plugins_security():
    keys = trusted_keys()
    return jsonify({'sandbox': sandbox_status(), 'keys': [fingerprint(k) for k in keys], 'signature_required_for_official': bool(keys)})


_ROUTES = (
    ('/api/plugins/security', ['GET'], 'api_plugins_security', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre la route d'état."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"plugin_security.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {}
