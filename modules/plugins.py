"""Stellio — plugins et SDK (1.1.7).

Un plugin est un dossier `DATA_DIR/plugins/<id>/` avec un `plugin.json` (manifeste) et un script Python. Stellio lui envoie les évènements
auxquels il est abonné (print.finished, print.failed, order.late, printer.overload) : le script est lancé dans un PROCESSUS SÉPARÉ, l'évènement
arrive en JSON sur son entrée standard.

Manifeste : {"id", "name", "version", "api": 1, "description", "author", "entry": "main.py", "events": [...], "permissions": [...], "ui": {"title", "icon", "entry": "page.html"}}
Permissions déclarées (à accepter explicitement à l'activation) : `events` (recevoir les évènements), `api:read` / `api:write` (Stellio fournit alors
au script `STELLIO_API_URL` et le jeton saisi dans la configuration du plugin, pour parler à l'API publique), `network` (information : accès réseau).

Isolation, honnêtement : processus séparé, dossier de travail = celui du plugin, environnement NETTOYÉ (ni variables de Stellio ni secrets),
durée limitée (10 s), mémoire limitée (512 Mo, systèmes POSIX), sortie tronquée, aucun accès à la base de Stellio. 1.1.8 : sous LINUX le noyau
restreint en plus les fichiers (Landlock : lecture seule du dossier du plugin, écriture dans `data/` seulement) et le réseau (seccomp : sans permission
`network` ou `api:*`, pas de socket Internet) ; avant installation, signature Ed25519 et audit automatique du code (voir plugin_security.py).
Sous Windows et macOS rien n'est appliqué par le noyau : les permissions restent déclaratives. N'installez que des plugins de confiance.
Réservé au compte propriétaire. Journal des exécutions : table `plugin_log`.
"""
import hashlib
import io
import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

_REQUIRED = (
    'DATA_DIR',
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'session',
)
_OPTIONAL = ()
_OVERRIDABLE = ('os', 'subprocess', 'time', 'http_get')

_MAIN = {}
DATA_DIR = None
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None

EVENTS = ('print.finished', 'print.failed', 'order.late', 'printer.overload')
PERMISSIONS = ('events', 'api:read', 'api:write', 'network', 'ui')
MAX_UI_BYTES = 1024 * 1024
UI_ENTRY_RE = re.compile(r'^[A-Za-z0-9_][A-Za-z0-9_./-]{0,98}\.html?$')
ICON_RE = re.compile(r'^fa-[a-z0-9-]{2,40}$')
API_VERSION = 1
ID_RE = re.compile(r'^[a-z0-9][a-z0-9_-]{1,39}$')
MAX_ZIP_BYTES = 2 * 1024 * 1024
MAX_UNPACKED = 8 * 1024 * 1024
MAX_FILES = 100
# Un plugin est « officiel » s'il est hébergé sur le dépôt stellio-app/stellio-plugins ; tout le reste est « communautaire ».
# L'origine est décidée ICI d'après l'adresse réelle de l'archive (jamais d'après un champ du catalogue ou du zip).
OFFICIAL_PREFIXES = ('https://github.com/stellio-app/stellio-plugins/', 'https://raw.githubusercontent.com/stellio-app/stellio-plugins/')
MAX_CATALOG_BYTES = 256 * 1024
MAX_CATALOG_ENTRIES = 200
MAX_LOGO_BYTES = 200 * 1024
LANGS = ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja')
# Catalogue officiel : un fichier JSON dans un dépôt GitHub public (les auteurs y ajoutent leur plugin par « pull request »).
# Remplaçable par la variable d'environnement STELLIO_PLUGINS_CATALOG (https) ou, ponctuellement, depuis la page Plugins.
DEFAULT_CATALOG_URL = 'https://raw.githubusercontent.com/stellio-app/stellio-plugins/main/catalog.json'
SHA_RE = re.compile(r'^[0-9a-f]{64}$')
TIMEOUT_S = 10
MEMORY_BYTES = 512 * 1024 * 1024
OUTPUT_MAX = 4000
LOG_KEEP = 200
_slots = threading.Semaphore(4)           # exécutions simultanées


def validate_manifest(m, allow_host=False):
    """(manifeste propre, erreur). `host` (modules Python exécutés DANS Stellio) n'est admis que si allow_host : l'installation exige alors une signature valide."""
    if not isinstance(m, dict):
        return None, 'Manifeste illisible.'
    pid = str(m.get('id') or '')
    if not ID_RE.match(pid):
        return None, "Identifiant invalide (minuscules, chiffres, - et _, 2 à 40 caractères)."
    host = None
    if 'host' in m:
        if not allow_host:
            return None, "Le champ « host » est réservé aux plugins intégrés à Stellio et aux plugins signés."
        hm = m['host'].get('modules') if isinstance(m['host'], dict) else None
        if not isinstance(hm, list) or not hm or len(hm) > 8 or not all(isinstance(x, str) and x.isidentifier() for x in hm):
            return None, "« host.modules » : liste de noms de modules Python du plugin."
        host = {'modules': hm}
    if m.get('api') != API_VERSION:
        return None, f"Version d'API non prise en charge (attendu : {API_VERSION})."
    name = str(m.get('name') or '').strip()[:60]
    if not name:
        return None, 'Nom manquant.'
    events = m.get('events') or []
    perms = m.get('permissions') or []
    ui_raw = m.get('ui')
    if m.get('entry') is None and (ui_raw or host) and not events:      # plugin purement visuel ou à code intégré (`host`) : pas de script à lancer
        entry = ''
    else:
        entry = str(m.get('entry') or 'main.py')
        if '/' in entry or '\\' in entry or entry.startswith('.') or not entry.endswith('.py'):
            return None, "Le point d'entrée doit être un fichier .py à la racine du plugin."
    ui = None
    if ui_raw is not None:
        if not isinstance(ui_raw, dict):
            return None, "« ui » doit être un objet {title, icon, entry}."
        ue = str(ui_raw.get('entry') or '')
        if not UI_ENTRY_RE.match(ue) or '..' in ue.split('/') or '//' in ue:
            return None, "« ui.entry » : chemin relatif d'un fichier .html du plugin."
        icon = str(ui_raw.get('icon') or 'fa-puzzle-piece')
        if not ICON_RE.match(icon):
            return None, "« ui.icon » : nom d'icône Font Awesome (fa-…)."
        ui = {'title': (str(ui_raw.get('title') or name).strip() or name)[:40], 'icon': icon, 'entry': ue}
    if not isinstance(events, list) or any(e not in EVENTS for e in events):
        return None, 'Évènement inconnu.'
    if not isinstance(perms, list) or any(p not in PERMISSIONS for p in perms):
        return None, 'Permission inconnue.'
    if events and 'events' not in perms:
        return None, "Pour recevoir des évènements, déclarez la permission « events »."
    if ui and 'ui' not in perms:
        return None, "Pour afficher une page, déclarez la permission « ui »."
    if not entry and not ui and not host:
        return None, "Le plugin n'a ni script ni page."
    rawd = m.get('description')
    d18 = {k: str(v)[:300] for k, v in rawd.items() if k in LANGS and isinstance(v, str) and v.strip()} if isinstance(rawd, dict) else {}
    desc = (d18.get('en') or d18.get('fr') or next(iter(d18.values()), '')) if isinstance(rawd, dict) else str(rawd or '')[:300]
    return {'id': pid, 'name': name, 'version': str(m.get('version') or '0')[:20], 'description': desc, **({'description_i18n': d18} if d18 else {}),
            'author': str(m.get('author') or '')[:60], 'entry': entry, 'events': list(dict.fromkeys(events)), 'permissions': list(dict.fromkeys(perms)), 'api': API_VERSION, **({'host': host} if host else {}), **({'ui': ui} if ui else {})}, None


def safe_extract(zip_bytes, dest):
    """Décompresse un plugin en refusant : chemins sortants (zip-slip), liens, trop de fichiers, trop gros. Retourne le manifeste validé."""
    if len(zip_bytes) > MAX_ZIP_BYTES:
        raise ValueError('Archive trop volumineuse.')
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile:
        raise ValueError('Archive invalide.')
    infos = [i for i in zf.infolist() if not i.is_dir()]
    if not infos or len(infos) > MAX_FILES:
        raise ValueError('Archive vide ou trop de fichiers.')
    if sum(i.file_size for i in infos) > MAX_UNPACKED:
        raise ValueError('Contenu décompressé trop volumineux.')
    names = [i.filename.replace('\\', '/') for i in infos]
    prefix = ''
    if 'plugin.json' not in names:                      # tolère un dossier racine unique
        tops = {n.split('/', 1)[0] for n in names}
        if len(tops) == 1 and f"{list(tops)[0]}/plugin.json" in names:
            prefix = list(tops)[0] + '/'
        else:
            raise ValueError('plugin.json introuvable à la racine.')
    manifest, err = validate_manifest(json.loads(zf.read(prefix + 'plugin.json').decode('utf-8', 'replace')), allow_host=True)
    if err:
        raise ValueError(err)
    for hm in (manifest.get('host') or {}).get('modules', []):
        if prefix + hm + '.py' not in names:
            raise ValueError(f"Module introuvable : {hm}.py.")
    if manifest['entry'] and prefix + manifest['entry'] not in names:
        raise ValueError(f"Fichier d'entrée introuvable : {manifest['entry']}.")
    if manifest.get('ui'):
        if prefix + manifest['ui']['entry'] not in names:
            raise ValueError(f"Page introuvable : {manifest['ui']['entry']}.")
        if next(i.file_size for i in infos if i.filename.replace('\\', '/') == prefix + manifest['ui']['entry']) > MAX_UI_BYTES:
            raise ValueError('Page trop volumineuse (1 Mo maximum).')
    root = os.path.realpath(dest)
    for info in infos:
        name = info.filename.replace('\\', '/')
        if not name.startswith(prefix):
            raise ValueError('Fichier hors du dossier du plugin.')
        rel = name[len(prefix):]
        if (info.external_attr >> 16) & 0o170000 == 0o120000:
            raise ValueError('Lien symbolique refusé.')
        target = os.path.realpath(os.path.join(root, rel))
        if not (target == root or target.startswith(root + os.sep)) or rel.startswith('/') or '..' in rel.split('/'):
            raise ValueError('Chemin refusé dans l\'archive.')
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, 'wb') as out:
            out.write(zf.read(info))
    return manifest


def build_env(manifest, config):
    """Environnement du processus : volontairement minimal. Le jeton n'est transmis qu'avec une permission api:*."""
    env = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'PYTHONIOENCODING': 'utf-8', 'PYTHONDONTWRITEBYTECODE': '1',
           'STELLIO_PLUGIN_ID': manifest['id'], 'STELLIO_API_VERSION': str(API_VERSION)}
    if os.name == 'nt':
        env['SYSTEMROOT'] = os.environ.get('SYSTEMROOT', '')
    cfg = dict(config or {})
    token = cfg.pop('token', None)
    url = cfg.get('api_url')
    if any(p in manifest['permissions'] for p in ('api:read', 'api:write')):
        if url:
            env['STELLIO_API_URL'] = str(url)[:200]
        if token:
            env['STELLIO_API_TOKEN'] = str(token)[:200]
    env['STELLIO_PLUGIN_CONFIG'] = json.dumps({k: v for k, v in cfg.items() if k != 'api_url'}, ensure_ascii=False)[:4000]
    return env


def _python():
    exe = sys.executable
    if getattr(sys, 'frozen', False) or not exe:           # application empaquetée : sys.executable est Stellio lui-même
        exe = shutil.which('python3') or shutil.which('python')
    return exe


def _limits():
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_BYTES, MEMORY_BYTES))
        resource.setrlimit(resource.RLIMIT_CPU, (TIMEOUT_S + 2, TIMEOUT_S + 2))
    except Exception:
        pass


def run_plugin(plugin_dir, manifest, event, payload, config, timeout=None):
    """Exécute le plugin pour un évènement. Retourne {'ok','ms','output','error'} ; ne lève jamais."""
    py = _python()
    t0 = time.time()
    if not py:
        return {'ok': False, 'ms': 0, 'output': '', 'error': 'Python introuvable sur cette machine (plugins indisponibles).'}
    if not manifest['entry']:
        return {'ok': False, 'ms': 0, 'output': '', 'error': "Ce plugin n'a pas de script : il n'a qu'une page."}
    entry = os.path.join(plugin_dir, manifest['entry'])
    if not os.path.isfile(entry):
        return {'ok': False, 'ms': 0, 'output': '', 'error': "Fichier d'entrée absent."}
    try:
        from modules import plugin_security
        data_dir = os.path.join(plugin_dir, 'data')
        os.makedirs(data_dir, exist_ok=True)
        net_ok = bool(set(manifest['permissions']) & {'network', 'api:read', 'api:write'})
        sandbox, sb = plugin_security.make_preexec(plugin_dir, data_dir, net_ok, py)
        env = build_env(manifest, config)
        env['STELLIO_PLUGIN_DATA'] = data_dir
        if os.name == 'posix':
            def _pre():
                _limits()
                if sandbox:
                    sandbox()
            kw = {'preexec_fn': _pre}
        else:
            kw = {}
        p = subprocess.run([py, '-I', entry, event], input=json.dumps({'event': event, 'data': payload}, ensure_ascii=False).encode('utf-8'),
                           cwd=plugin_dir, env=env, capture_output=True, timeout=timeout or TIMEOUT_S, **kw)
        out = (p.stdout or b'').decode('utf-8', 'replace')[-OUTPUT_MAX:]
        err = (p.stderr or b'').decode('utf-8', 'replace')[-OUTPUT_MAX:]
        return {'ok': p.returncode == 0, 'ms': int((time.time() - t0) * 1000), 'output': out, 'error': '' if p.returncode == 0 else (err or f'code {p.returncode}')[-500:],
                'sandbox': {'filesystem': bool(sb.get('filesystem_restricted')), 'network': bool(sb.get('network_restricted')), 'reason': sb.get('reason')}}
    except subprocess.TimeoutExpired:
        return {'ok': False, 'ms': int((time.time() - t0) * 1000), 'output': '', 'error': f'Délai dépassé ({timeout or TIMEOUT_S} s).'}
    except Exception as e:
        return {'ok': False, 'ms': int((time.time() - t0) * 1000), 'output': '', 'error': f'{type(e).__name__}: {e}'[:300]}


# ── base ──

def _root():
    d = os.path.join(DATA_DIR, 'plugins')
    os.makedirs(d, exist_ok=True)
    return d


def _ensure(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS plugin_state (user_id INTEGER NOT NULL, plugin_id TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 0, config TEXT DEFAULT '{}',
            PRIMARY KEY (user_id, plugin_id));
        CREATE TABLE IF NOT EXISTS plugin_log (id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, user_id INTEGER, plugin_id TEXT, event TEXT, ok INTEGER, ms INTEGER, output TEXT, error TEXT);
    """)


def is_official(url):
    return str(url or '').lower().startswith(OFFICIAL_PREFIXES)


def _origins_path():
    return os.path.join(_root(), '.origins.json')


def _origins():
    try:
        d = json.load(open(_origins_path(), encoding='utf-8'))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _set_origin(pid, origin):
    d = _origins()
    if origin is None:
        d.pop(pid, None)
    else:
        d[pid] = origin
    tmp = _origins_path() + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(d, f)
    os.replace(tmp, _origins_path())


def installed():
    """[(dossier, manifeste)] des plugins valides présents sur disque."""
    out = []
    root = _root()
    for name in sorted(os.listdir(root)):
        d = os.path.join(root, name)
        mf = os.path.join(d, 'plugin.json')
        if os.path.isfile(mf):
            try:
                m, err = validate_manifest(json.load(open(mf, encoding='utf-8')), allow_host=True)
            except (OSError, ValueError):
                continue
            if m and m.get('host'):      # plugin signé à code intégré : listé seulement si l'archive signée est toujours intacte
                from modules import plugin_host
                if not plugin_host.verify_external(name, d)[0]:
                    continue
            if not err and m['id'] == name:
                out.append((d, m))
    return out


def _log(conn, uid, pid, event, res):
    conn.execute("INSERT INTO plugin_log (ts, user_id, plugin_id, event, ok, ms, output, error) VALUES (?,?,?,?,?,?,?,?)",
                 (time.time(), uid, pid, event, 1 if res['ok'] else 0, res['ms'], res['output'][:OUTPUT_MAX], res['error'][:500]))
    conn.execute("DELETE FROM plugin_log WHERE user_id = ? AND id NOT IN (SELECT id FROM plugin_log WHERE user_id = ? ORDER BY id DESC LIMIT ?)", (uid, uid, LOG_KEEP))
    conn.commit()


def has_active(user_id=None):
    try:
        conn = get_db()
        try:
            _ensure(conn)
            sql, args = "SELECT 1 FROM plugin_state WHERE enabled = 1", []
            if user_id is not None:
                sql += " AND user_id = ?"
                args.append(user_id)
            return conn.execute(sql + " LIMIT 1", args).fetchone() is not None
        finally:
            conn.close()
    except Exception:
        return False


def dispatch(event, data=None, user_id=None):
    """Envoie un évènement aux plugins activés et abonnés (en tâche de fond). Ne lève jamais. Retourne le nombre de plugins sollicités."""
    if event not in EVENTS:
        return 0
    try:
        conn = get_db()
        try:
            _ensure(conn)
            sql, args = "SELECT user_id, plugin_id, config FROM plugin_state WHERE enabled = 1", []
            if user_id is not None:
                sql += " AND user_id = ?"
                args.append(user_id)
            rows = conn.execute(sql, args).fetchall()
        finally:
            conn.close()
        by_id = {m['id']: (d, m) for d, m in installed()}
        n = 0
        for r in rows:
            d, m = by_id.get(r['plugin_id'], (None, None))
            if not m or event not in m['events'] or 'events' not in m['permissions']:
                continue
            try:
                cfg = json.loads(r['config'] or '{}')
            except ValueError:
                cfg = {}
            threading.Thread(target=_run_logged, args=(r['user_id'], d, m, event, data, cfg), daemon=True).start()
            n += 1
        return n
    except Exception as e:
        try:
            app_logger.debug(f"[PLUGINS] évènement ignoré : {type(e).__name__}")
        except Exception:
            pass
        return 0


def _run_logged(uid, d, m, event, data, cfg):
    with _slots:
        res = run_plugin(d, m, event, data, cfg)
    try:
        conn = get_db()
        try:
            _ensure(conn)
            _log(conn, uid, m['id'], event, res)
        finally:
            conn.close()
    except Exception:
        pass



# ── versions, mise à jour, catalogue ──
def parse_version(v):
    """'1.2.10' -> (1, 2, 10, 0) ; ignore tout ce qui n'est pas numérique (pas de comparaison de pré-versions)."""
    nums = [int(x) for x in re.findall(r'\d+', str(v or ''))[:4]]
    return tuple(nums + [0] * (4 - len(nums)))


def compare_versions(a, b):
    pa, pb = parse_version(a), parse_version(b)
    return (pa > pb) - (pa < pb)


def _public_host(host):
    """Refuse localhost, réseaux privés, lien-local et réservés (protège le réseau local d'une URL de catalogue piégée)."""
    try:
        infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
    except OSError:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            return False
    return bool(infos)


def check_url(url):
    u = urllib.parse.urlparse(str(url or ''))
    if u.scheme != 'https' or not u.hostname or u.username or u.password:
        raise ValueError('Adresse https obligatoire (sans identifiants).')
    if not _public_host(u.hostname):
        raise ValueError("Adresse refusée : elle doit pointer vers un site public.")
    return u.geturl()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(urllib.parse.urljoin(req.full_url, newurl))      # une redirection doit rester en https public
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def http_get(url, max_bytes, timeout=15):
    """Téléchargement borné (https public uniquement, redirections revérifiées). Lève ValueError."""
    url = check_url(url)
    op = urllib.request.build_opener(_NoRedirect)
    try:
        with op.open(urllib.request.Request(url, headers={'User-Agent': 'Stellio-plugins'}), timeout=timeout) as r:
            data = r.read(max_bytes + 1)
    except (urllib.error.URLError, OSError) as e:
        raise ValueError('Téléchargement impossible : %s' % getattr(e, 'reason', e))
    if len(data) > max_bytes:
        raise ValueError('Fichier trop volumineux.')
    return data


def default_catalog_url():
    u = str(os.environ.get('STELLIO_PLUGINS_CATALOG') or '').strip()
    return u if u.startswith('https://') else DEFAULT_CATALOG_URL


def _https(v):
    v = str(v or '').strip()
    return v[:300] if v.startswith('https://') else ''


def pick_description(entry, lang=None):
    """Description dans la langue demandée (repli : anglais, français, puis la première disponible)."""
    d = entry.get('description_i18n') or {}
    if not d and isinstance(entry.get('description'), dict):          # plugins intégrés : description par langue directement dans le manifeste
        d = entry['description']
    lg = str(lang or '').lower()
    for k in (lg, lg[:2], 'en', 'fr'):
        if k and d.get(k):
            return d[k]
    desc = entry.get('description')
    return (desc if isinstance(desc, str) else '') or next(iter(d.values()), '')


_manifest_cache = {}      # url du plugin.json -> (heure, description, descriptions par langue)


def manifest_url(e):
    """Adresse du plugin.json publié sur GitHub : champ « manifest » du catalogue, sinon déduite de la page du plugin (github.com/<auteur>/<dépôt>[/tree/<branche>/<dossier>])."""
    if e.get('manifest'):
        return e['manifest']
    m = re.match(r'^https://github\.com/([\w.-]+)/([\w.-]+?)(?:/tree/([\w./-]+?))?/?$', str(e.get('homepage') or ''))
    if not m:
        return ''
    o, r, rest = m.groups()
    return 'https://raw.githubusercontent.com/%s/%s/%s/plugin.json' % (o, r, rest or 'HEAD')


def _remote_description(url):
    hit = _manifest_cache.get(url)
    now = time.time()
    if hit and now - hit[0] < 600:
        return hit[1], hit[2]
    desc, i18n = '', {}
    try:
        raw = json.loads(http_get(url, 32 * 1024, timeout=5).decode('utf-8', 'replace')).get('description')
        if isinstance(raw, dict):
            i18n = {k: str(v)[:300] for k, v in raw.items() if k in LANGS and isinstance(v, str) and v.strip()}
        elif isinstance(raw, str):
            desc = raw.strip()[:300]
    except (ValueError, TypeError, AttributeError):
        pass
    _manifest_cache[url] = (now, desc, i18n)
    if len(_manifest_cache) > 400:
        _manifest_cache.pop(next(iter(_manifest_cache)))
    return desc, i18n


def apply_remote_descriptions(entries):
    """La description d'un plugin est celle de son plugin.json sur GitHub ; celle du catalogue n'est qu'un repli (réseau coupé, fichier absent)."""
    todo = [(e, manifest_url(e)) for e in entries]
    todo = [(e, u) for e, u in todo if u]
    if not todo:
        return
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as ex:
        for (e, _u), (desc, i18n) in zip(todo, ex.map(lambda t: _remote_description(t[1]), todo)):
            if i18n:
                e['description_i18n'] = i18n
                e['description'] = i18n.get('en') or i18n.get('fr') or next(iter(i18n.values()))
            elif desc:
                e['description'] = desc
                e['description_i18n'] = {}


def validate_catalog(obj):
    """Entrées valides d'un catalogue {"plugins": [{id, name, version, description, url, sha256, permissions}]} ; les entrées douteuses sont ignorées."""
    items = obj.get('plugins') if isinstance(obj, dict) else None
    if not isinstance(items, list):
        raise ValueError('Catalogue illisible (clé « plugins » manquante).')
    out, seen = [], set()
    for it in items[:MAX_CATALOG_ENTRIES]:
        if not isinstance(it, dict):
            continue
        pid, url, sha = str(it.get('id') or ''), str(it.get('url') or ''), str(it.get('sha256') or '').lower()
        if not ID_RE.match(pid) or pid in seen or not SHA_RE.match(sha) or not url.startswith('https://'):
            continue
        perms = it.get('permissions') if isinstance(it.get('permissions'), list) else []
        raw = it.get('description')
        i18n = {k: str(v)[:300] for k, v in raw.items() if k in LANGS and isinstance(v, str) and v.strip()} if isinstance(raw, dict) else {}
        seen.add(pid)
        sig = str(it.get('signature') or '').strip().lower()
        out.append({'signature': sig if re.match(r'^[0-9a-f]{128}$', sig) else '', 'id': pid, 'name': str(it.get('name') or pid)[:60], 'version': str(it.get('version') or '0')[:20],
                    'description': (str(raw)[:300] if isinstance(raw, str) else (i18n.get('en') or i18n.get('fr') or next(iter(i18n.values()), ''))), 'description_i18n': i18n,
                    'author': str(it.get('author') or '')[:60], 'url': url, 'sha256': sha, 'permissions': [p for p in perms if p in PERMISSIONS],
                    'logo': _https(it.get('logo')), 'homepage': _https(it.get('homepage')), 'manifest': _https(it.get('manifest'))})
    return out


class PluginRefused(ValueError):
    """Installation refusée par la signature ou l'audit : `code` pour l'interface, `audit` = constats éventuels."""
    def __init__(self, message, code, audit=None):
        super().__init__(message)
        self.code = code
        self.audit = audit


REFUSALS = {
    'signature_invalid': "Signature invalide : l'archive n'a pas été signée par une clé de confiance. Installation refusée.",
    'signature_required': "Ce plugin officiel n'est pas signé (ou sa signature est inconnue) : installation refusée.",
    'signature_downgrade': "Ce plugin était signé et cette version ne l'est pas : mise à jour refusée.",
    'key_changed': "Cette version est signée par une autre clé que celle de la version installée : mise à jour refusée.",
    'host_no_key': "Ce plugin exécute du code DANS Stellio : il n'est admis que signé par une clé de confiance, et aucune clé de confiance n'est configurée. Installation refusée.",
    'host_unsigned': "Ce plugin exécute du code DANS Stellio : sa signature est absente ou n'est pas celle d'une clé de confiance. Installation refusée.",
    'audit_blocked': "L'audit automatique a trouvé du code dangereux (voir le détail). Installation refusée, sauf acceptation explicite du risque.",
}


def install_bytes(data, allow_downgrade=False, origin='community', signature='', accept_risk=False, accept_key_change=False):
    """Installe ou met à jour un plugin depuis une archive. Remplacement atomique (l'ancienne version est restaurée si le déplacement échoue).
    Retourne {'manifest', 'action', 'previous_version', 'added_permissions'}. Lève ValueError."""
    tmp = os.path.join(_root(), '.install-tmp')
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    try:
        manifest = safe_extract(data, tmp)
        from modules import plugin_host, plugin_security
        if plugin_host.is_bundled(manifest['id']):
            raise ValueError("Cet identifiant est celui d'un plugin intégré à Stellio : il ne peut pas être remplacé par une archive.")
        keys = plugin_security.trusted_keys()
        sig = plugin_security.signature_status(signature, manifest['id'], manifest['version'], hashlib.sha256(data).hexdigest(), keys)
        if manifest.get('host'):                     # code exécuté dans le processus de Stellio : signature de confiance OBLIGATOIRE, sans exception ni acceptation de risque
            if not keys:
                raise PluginRefused(REFUSALS['host_no_key'], 'host_no_key')
            if sig['status'] != 'valid':
                raise PluginRefused(REFUSALS['host_unsigned'], 'host_unsigned')
        ok, code = plugin_security.signature_policy(sig, origin == 'official', bool(keys), plugin_security.load_store().get(manifest['id']), accept_key_change)
        if not ok:
            raise PluginRefused(REFUSALS[code], code)
        audit = plugin_security.audit_dir(tmp, manifest)
        if audit['blocking'] and not accept_risk and sig['status'] != 'valid':
            raise PluginRefused(REFUSALS['audit_blocked'], 'audit_blocked', audit)
        dest = os.path.join(_root(), manifest['id'])
        prev = {m['id']: m for _d, m in installed()}.get(manifest['id'])
        action, added = 'installed', []
        if prev:
            c = compare_versions(manifest['version'], prev['version'])
            if c < 0 and not allow_downgrade:
                raise ValueError(f"Version {manifest['version']} plus ancienne que celle installée ({prev['version']}). Cochez « autoriser le retour en arrière » pour continuer.")
            action = 'updated' if c > 0 else 'reinstalled'
            added = [p for p in manifest['permissions'] if p not in prev['permissions']]
        old = dest + '.old'
        shutil.rmtree(old, ignore_errors=True)
        if os.path.isdir(dest):
            os.rename(dest, old)
        try:
            shutil.move(tmp, dest)
        except OSError:
            if os.path.isdir(old):
                os.rename(old, dest)
            raise ValueError("Remplacement impossible, l'ancienne version est conservée.")
        shutil.rmtree(old, ignore_errors=True)
        _set_origin(manifest['id'], 'official' if origin == 'official' else 'community')
        plugin_security.save_record(manifest['id'], sig, audit, bool(audit['blocking'] and (accept_risk or sig['status'] == 'valid')))
        if manifest.get('host'):
            plugin_host.save_external_proof(manifest['id'], manifest['version'], signature, data)
        else:
            plugin_host.drop_external_proof(manifest['id'])     # une version sans code intégré remplace une version signée : la preuve n'a plus d'objet
        return {'manifest': manifest, 'action': action, 'previous_version': prev['version'] if prev else None, 'added_permissions': added,
                'security': {'signature': sig['status'], 'key': sig['key'], 'audit': audit['level'], 'findings': audit['findings'][:20], 'accepted_risk': bool(audit['blocking'])}}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _after_install(res):
    """Une mise à jour qui demande de NOUVELLES permissions désactive le plugin : il faut les accepter à nouveau. La configuration est conservée."""
    res['reack_required'] = False
    if res['added_permissions']:
        conn = get_db()
        try:
            _ensure(conn)
            n = conn.execute("UPDATE plugin_state SET enabled = 0 WHERE plugin_id = ? AND enabled = 1", (res['manifest']['id'],)).rowcount
            conn.commit()
            res['reack_required'] = True
            res['was_disabled'] = bool(n)
        finally:
            conn.close()
    if res['action'] == 'installed':
        res['note'] = "Installé, désactivé : lisez les permissions puis activez-le."
    elif res['reack_required']:
        res['note'] = 'Mis à jour : de nouvelles permissions sont demandées (%s). Le plugin est désactivé jusqu\'à ce que vous les acceptiez ; sa configuration est conservée.' % ', '.join(res['added_permissions'])
    else:
        res['note'] = 'Mis à jour (configuration et activation conservées).'
    return res


def _owner_only():
    if session.get('role') == 'viewer' and not _demo_ok():
        return jsonify({'error': 'Réservé au compte propriétaire.', 'code': 'viewer_forbidden'}), 403
    return None


def api_plugins_list():
    r = _owner_only()
    if r:
        return r
    conn = get_db()
    try:
        _ensure(conn)
        st = {x['plugin_id']: x for x in conn.execute("SELECT plugin_id, enabled, config FROM plugin_state WHERE user_id = ?", (session['user_id'],)).fetchall()}
        out, org = [], _origins()
        from modules import plugin_security
        _sec = plugin_security.load_store()
        for d, m in installed():
            s = st.get(m['id'])
            cfg = json.loads(s['config'] or '{}') if s else {}
            out.append(dict(m, security=_sec.get(m['id']), description=pick_description(m, request.args.get('lang')), origin=org.get(m['id']) if org.get(m['id']) == 'official' else 'community', enabled=bool(s and s['enabled']), config={k: ('••••' if k == 'token' and v else v) for k, v in cfg.items()}))
            if m.get('host'):      # plugin signé à code intégré : activation à l'échelle de l'installation (comme les plugins intégrés), effective au redémarrage
                from modules import plugin_host as _ph
                en_h = _ph.is_enabled(m['id'])
                out[-1].update(enabled=en_h, host=True, loaded=_ph.loaded(m['id']), restart_required=en_h != _ph.loaded(m['id']))
        from modules import plugin_host
        builtin = []
        for pid, _d, m in plugin_host.manifests():
            if m.get('_external') or not plugin_host.available(m):          # (signés du catalogue : listés avec les plugins installés) ; fournisseurs d'IA à clé d'API : édition serveur seulement
                continue
            en = plugin_host.is_enabled(pid)
            builtin.append({'id': pid, 'name': str(((m.get('name_i18n') or {}).get(str(request.args.get('lang') or '').lower()[:2])) or m.get('name') or pid)[:60], 'version': str(m.get('version') or '1.0.0')[:20], 'author': str(m.get('author') or 'Stellio')[:60],
                            'description': pick_description(m, request.args.get('lang')), 'icon': m.get('icon') or 'fa-puzzle-piece', 'origin': 'official', 'builtin': True,
                            'enabled': en, 'loaded': plugin_host.loaded(pid), 'restart_required': en != plugin_host.loaded(pid)})
        keys = plugin_security.trusted_keys()
        return jsonify({'builtin': builtin, 'plugins': out, 'events': list(EVENTS), 'permissions': list(PERMISSIONS), 'python': bool(_python()),
                        'sandbox': plugin_security.sandbox_status(), 'trusted_keys': [plugin_security.fingerprint(k) for k in keys],
                        'isolation': "Processus séparé, environnement nettoyé, 10 s, 512 Mo. Fichiers et réseau restreints par le noyau sous Linux seulement ; ailleurs, permissions déclaratives. N'installez que des plugins de confiance."})
    finally:
        conn.close()


def api_plugins_install():
    r = _owner_only()
    if r:
        return r
    f = request.files.get('file')
    if not f:
        return jsonify({'error': 'Archive .zip manquante.'}), 400
    data = f.read(MAX_ZIP_BYTES + 1)
    allow = str(request.form.get('allow_downgrade') or '') in ('1', 'true', 'on')
    flag = lambda k: str(request.form.get(k) or '') in ('1', 'true', 'on')
    try:
        res = _after_install(install_bytes(data, allow, 'community', str(request.form.get('signature') or ''), flag('accept_risk'), flag('accept_key_change')))
    except PluginRefused as e:
        return jsonify({'error': str(e), 'code': e.code, 'audit': e.audit}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 409 if 'plus ancienne' in str(e) else 400
    return jsonify({'ok': True, 'plugin': res['manifest'], 'action': res['action'], 'previous_version': res['previous_version'],
                    'added_permissions': res['added_permissions'], 'reack_required': res['reack_required'], 'note': res['note'], 'security': res['security']})


def _fetch_catalog(url):
    """Catalogue validé. Signé (`<url>.sig`, Ed25519 sur les octets exacts du fichier) : si des clés de confiance existent, une signature invalide est
    toujours refusée et le catalogue officiel doit être signé ; sans clé configurée, aucune exigence (l'écran indique « non vérifié »)."""
    from modules import plugin_security
    raw = http_get(url, MAX_CATALOG_BYTES)
    keys = plugin_security.trusted_keys()
    st = 'unsigned'
    if keys:
        try:
            sigtxt = http_get(url + '.sig', 1024).decode('ascii', 'ignore').strip()
        except ValueError:
            sigtxt = ''
        if sigtxt:
            st = 'valid' if plugin_security.verify(sigtxt, plugin_security.catalog_message(raw), keys) else 'invalid'
        if st == 'invalid' or (st != 'valid' and (url == default_catalog_url() or is_official(url))):
            raise ValueError("Signature du catalogue absente ou invalide : catalogue refusé." if st != 'invalid' else "Signature du catalogue invalide : catalogue refusé.")
    else:
        st = 'unverified'
    entries = validate_catalog(json.loads(raw.decode('utf-8', 'replace')))
    for e in entries:
        e['catalog_signature'] = st
    return entries


def plugin_security_status(entry):
    """État de la signature d'une entrée du catalogue (sans télécharger l'archive) : valid | invalid | unsigned | unverifiable."""
    from modules import plugin_security
    return plugin_security.signature_status(entry.get('signature'), entry['id'], entry['version'], entry['sha256'])['status']


def api_plugins_catalog():
    """Lit un catalogue (JSON à une adresse https) et indique, pour chaque plugin, s'il est installé et s'il existe une version plus récente."""
    r = _owner_only()
    if r:
        return r
    d = request.get_json(silent=True) or {}
    url = str(d.get('url') or '').strip() or default_catalog_url()
    if d.get('refresh'):                                   # bouton « Actualiser » : on oublie les lectures en mémoire (catalogue, descriptions et logos)
        _catalog_cache.pop(url, None)
        _logo_cache.clear()
        _manifest_cache.clear()
    try:
        entries = _fetch_catalog(url)
    except (ValueError, TypeError) as e:
        return jsonify({'error': str(e)}), 400
    apply_remote_descriptions(entries)
    have = {m['id']: m for _d, m in installed()}
    for e in entries:
        e['description'] = pick_description(e, d.get('lang'))
        e['official'] = is_official(e['url'])
        e['signature_status'] = plugin_security_status(e)
        e['has_logo'] = bool(e.pop('logo', ''))
        e.pop('description_i18n', None)
        e.pop('manifest', None)
        cur = have.get(e['id'])
        e['installed_version'] = cur['version'] if cur else None
        e['update_available'] = bool(cur and compare_versions(e['version'], cur['version']) > 0)
        e['new_permissions'] = [p for p in e['permissions'] if cur and p not in cur['permissions']]
    return jsonify({'plugins': entries, 'count': len(entries), 'updates': sum(1 for e in entries if e['update_available']), 'url': url, 'default': url == default_catalog_url()})


def api_plugins_catalog_install():
    """Installe un plugin du catalogue. Le catalogue est relu côté serveur (l'adresse du zip ne vient jamais du navigateur) et l'empreinte SHA-256 est OBLIGATOIRE."""
    r = _owner_only()
    if r:
        return r
    d = request.get_json(silent=True) or {}
    try:
        entry = next((e for e in _fetch_catalog(str(d.get('url') or '').strip() or default_catalog_url()) if e['id'] == d.get('id')), None)
        if not entry:
            return jsonify({'error': 'Plugin absent du catalogue.'}), 404
        data = http_get(entry['url'], MAX_ZIP_BYTES)
        if hashlib.sha256(data).hexdigest() != entry['sha256']:
            return jsonify({'error': "Empreinte SHA-256 différente de celle du catalogue : installation refusée.", 'code': 'sha_mismatch'}), 400
        res = _after_install(install_bytes(data, bool(d.get('allow_downgrade')), 'official' if is_official(entry['url']) else 'community',
                                           entry.get('signature') or '', bool(d.get('accept_risk')), bool(d.get('accept_key_change'))))
    except PluginRefused as e:
        return jsonify({'error': str(e), 'code': e.code, 'audit': e.audit}), 400
    except (ValueError, TypeError) as e:
        return jsonify({'error': str(e)}), 400
    return jsonify({'ok': True, 'plugin': res['manifest'], 'action': res['action'], 'previous_version': res['previous_version'],
                    'added_permissions': res['added_permissions'], 'reack_required': res['reack_required'], 'note': res['note'], 'security': res['security']})


_catalog_cache = {}        # url -> (heure, entrées) : la page lit le catalogue une fois, puis chaque logo réutilise cette lecture
_logo_cache = {}           # url du logo -> (heure, octets, type MIME)


def _sniff_image(b):
    """PNG, JPEG ou WebP uniquement (pas de SVG : il peut contenir du script)."""
    if b[:8] == b'\x89PNG\r\n\x1a\n':
        return 'image/png'
    if b[:3] == b'\xff\xd8\xff':
        return 'image/jpeg'
    if b[:4] == b'RIFF' and b[8:12] == b'WEBP':
        return 'image/webp'
    return None


def api_plugins_logo():
    """Logo d'un plugin du catalogue, relayé par le serveur : le navigateur ne contacte jamais le site de l'auteur."""
    r = _owner_only()
    if r:
        return r
    url = str(request.args.get('url') or '').strip() or default_catalog_url()
    pid = str(request.args.get('id') or '')
    now = time.time()
    try:
        hit = _catalog_cache.get(url)
        if not hit or now - hit[0] > 60:
            hit = (now, _fetch_catalog(url))
            _catalog_cache[url] = hit
            if len(_catalog_cache) > 8:
                _catalog_cache.pop(next(iter(_catalog_cache)))
        entry = next((e for e in hit[1] if e['id'] == pid), None)
        if not entry or not entry.get('logo'):
            return jsonify({'error': 'Pas de logo.'}), 404
        got = _logo_cache.get(entry['logo'])
        if not got or now - got[0] > 3600:
            data = http_get(entry['logo'], MAX_LOGO_BYTES)
            mime = _sniff_image(data)
            if not mime:
                return jsonify({'error': 'Format de logo non pris en charge (PNG, JPEG ou WebP).'}), 415
            got = (now, data, mime)
            _logo_cache[entry['logo']] = got
            if len(_logo_cache) > 100:
                _logo_cache.pop(next(iter(_logo_cache)))
    except (ValueError, TypeError) as e:
        return jsonify({'error': str(e)}), 404
    resp = app.response_class(got[1], mimetype=got[2])
    resp.headers['Cache-Control'] = 'private, max-age=3600'
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['Content-Security-Policy'] = "default-src 'none'; sandbox"
    return resp


def api_plugin_update(pid):
    r = _owner_only()
    if r:
        return r
    from modules import plugin_host
    if plugin_host.manifest(pid):            # plugin intégré : activation à l'échelle de l'installation, effective au redémarrage
        d = request.get_json(silent=True) or {}
        if 'enabled' not in d:
            return jsonify({'error': 'Champ « enabled » manquant.'}), 400
        try:
            res = plugin_host.set_enabled(pid, bool(d['enabled']))
        except PermissionError:
            return jsonify({'error': "Fonction réservée à l'édition serveur (Linux)", 'code': 'server_edition_only'}), 404
        return jsonify({'ok': True, **res})
    by_id = {m['id']: m for _d, m in installed()}
    m = by_id.get(pid)
    if not m:
        return jsonify({'error': 'Plugin introuvable.'}), 404
    d = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        _ensure(conn)
        row = conn.execute("SELECT enabled, config FROM plugin_state WHERE user_id = ? AND plugin_id = ?", (session['user_id'], pid)).fetchone()
        enabled = bool(row['enabled']) if row else False
        cfg = json.loads(row['config'] or '{}') if row else {}
        if 'config' in d:
            if not isinstance(d['config'], dict) or len(json.dumps(d['config'])) > 4000:
                return jsonify({'error': 'Configuration invalide.'}), 400
            new = {str(k)[:40]: v for k, v in d['config'].items() if isinstance(v, (str, int, float, bool)) or v is None}
            if new.get('token') == '••••':
                new['token'] = cfg.get('token')
            cfg = {k: v for k, v in new.items() if v not in (None, '')}
        if 'enabled' in d:
            if d['enabled'] and set(d.get('ack_permissions') or []) != set(m['permissions']):
                return jsonify({'error': 'Acceptez explicitement les permissions du plugin pour l\'activer.', 'permissions': m['permissions']}), 400
            enabled = bool(d['enabled'])
        conn.execute("INSERT INTO plugin_state (user_id, plugin_id, enabled, config) VALUES (?,?,?,?) ON CONFLICT(user_id, plugin_id) DO UPDATE SET enabled = excluded.enabled, config = excluded.config",
                     (session['user_id'], pid, 1 if enabled else 0, json.dumps(cfg, ensure_ascii=False)))
        conn.commit()
        return jsonify({'ok': True, 'enabled': enabled})
    finally:
        conn.close()


def api_plugins_features():
    """Plugins intégrés activés ({id: bool}) : l'interface masque les menus et sections de ceux qui ne le sont pas. Lisible par tout compte connecté."""
    from modules import plugin_host
    ft = plugin_host.features()
    return jsonify({'features': ft, 'loaded': {k: plugin_host.loaded(k) for k in ft}})


def api_plugin_delete(pid):
    r = _owner_only()
    if r:
        return r
    if not ID_RE.match(pid) or not os.path.isdir(os.path.join(_root(), pid)):
        return jsonify({'error': 'Plugin introuvable.'}), 404
    shutil.rmtree(os.path.join(_root(), pid), ignore_errors=True)
    try:
        from modules import plugin_host
        plugin_host.drop_external_proof(pid)
    except Exception:
        pass
    _set_origin(pid, None)
    try:
        from modules import plugin_security
        plugin_security.drop_record(pid)
    except Exception:
        pass
    conn = get_db()
    try:
        _ensure(conn)
        conn.execute("DELETE FROM plugin_state WHERE plugin_id = ?", (pid,))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'ok': True})


def api_plugin_test(pid):
    """Lance le plugin avec un évènement d'essai (même s'il est désactivé : c'est l'essai explicite du propriétaire)."""
    r = _owner_only()
    if r:
        return r
    by_id = {m['id']: (d, m) for d, m in installed()}
    if pid not in by_id:
        return jsonify({'error': 'Plugin introuvable.'}), 404
    d, m = by_id[pid]
    event = (request.get_json(silent=True) or {}).get('event') or (m['events'][0] if m['events'] else 'print.finished')
    if event not in EVENTS:
        return jsonify({'error': 'Évènement inconnu.'}), 400
    conn = get_db()
    try:
        _ensure(conn)
        row = conn.execute("SELECT config FROM plugin_state WHERE user_id = ? AND plugin_id = ?", (session['user_id'], pid)).fetchone()
        cfg = json.loads(row['config'] or '{}') if row else {}
        res = run_plugin(d, m, event, {'test': True, 'file_name': 'exemple.gcode', 'printer': 'Imprimante test'}, cfg)
        _log(conn, session['user_id'], pid, event + ' (essai)', res)
        return jsonify(res)
    finally:
        conn.close()


def api_plugin_ui(pid):
    """Page (HTML autonome) d'un plugin activé : affichée par l'interface dans un cadre isolé (sans accès aux cookies ni au réseau)."""
    r = _owner_only()
    if r:
        return r
    by_id = {m['id']: (d, m) for d, m in installed()}
    if pid not in by_id or not by_id[pid][1].get('ui'):
        return jsonify({'error': "Ce plugin n'a pas de page."}), 404
    d, m = by_id[pid]
    conn = get_db()
    try:
        _ensure(conn)
        row = conn.execute("SELECT enabled FROM plugin_state WHERE user_id = ? AND plugin_id = ?", (session['user_id'], pid)).fetchone()
    finally:
        conn.close()
    if m.get('host'):                      # plugin signé à code intégré : actif seulement s'il est activé ET chargé (donc vérifié au démarrage)
        from modules import plugin_host as _ph
        row = {'enabled': _ph.is_enabled(pid) and _ph.loaded(pid)}
    if not (row and row['enabled']):
        return jsonify({'error': 'Plugin désactivé : activez-le dans Plugins › Catalogue.', 'code': 'plugin_disabled'}), 403
    path = os.path.realpath(os.path.join(d, m['ui']['entry']))
    if not path.startswith(os.path.realpath(d) + os.sep) or not os.path.isfile(path) or os.path.getsize(path) > MAX_UI_BYTES:
        return jsonify({'error': 'Page introuvable.'}), 404
    with open(path, encoding='utf-8', errors='replace') as f:
        html = f.read()
    resp = app.response_class(html, mimetype='text/html')
    resp.headers['Content-Security-Policy'] = "default-src 'none'; sandbox"
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['Cache-Control'] = 'no-store'
    return resp


def api_plugins_log():
    r = _owner_only()
    if r:
        return r
    conn = get_db()
    try:
        _ensure(conn)
        rows = conn.execute("SELECT ts, plugin_id, event, ok, ms, output, error FROM plugin_log WHERE user_id = ? ORDER BY id DESC LIMIT 100", (session['user_id'],)).fetchall()
        return jsonify({'log': [dict(x) for x in rows]})
    finally:
        conn.close()


_DEMO_COMPUTE = ('/api/plate/arrange', '/api/organize/preview', '/api/model-diff')


def _demo_ok():
    """Démo publique (lecture seule, `IS_DEMO` posé par la surcouche de démo) : consultation (GET) et calculs sans écriture."""
    try:
        return bool(_MAIN.get('IS_DEMO')) and (request.method in ('GET', 'HEAD') or request.path in _DEMO_COMPUTE)
    except Exception:
        return False


_ROUTES = (
    ('/api/plugins', ['GET'], 'api_plugins_list', ('login_required', )),
    ('/api/plugins/features', ['GET'], 'api_plugins_features', ('login_required', )),
    ('/api/plugins/install', ['POST'], 'api_plugins_install', ('login_required', )),
    ('/api/plugins/log', ['GET'], 'api_plugins_log', ('login_required', )),
    ('/api/plugins/catalog', ['POST'], 'api_plugins_catalog', ('login_required', )),
    ('/api/plugins/logo', ['GET'], 'api_plugins_logo', ('login_required', )),
    ('/api/plugins/catalog/install', ['POST'], 'api_plugins_catalog_install', ('login_required', )),
    ('/api/plugins/<pid>', ['PUT'], 'api_plugin_update', ('login_required', )),
    ('/api/plugins/<pid>', ['DELETE'], 'api_plugin_delete', ('login_required', )),
    ('/api/plugins/<pid>/test', ['POST'], 'api_plugin_test', ('login_required', )),
    ('/api/plugins/<pid>/ui', ['GET'], 'api_plugin_ui', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"{__name__}.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    try:
        from modules import plugin_security
        if plugin_security.DATA_DIR is None:
            plugin_security.DATA_DIR = ns['DATA_DIR']          # même dossier de données, même quand plugin_security n'a pas encore reçu ses services
    except Exception:
        pass
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {}
