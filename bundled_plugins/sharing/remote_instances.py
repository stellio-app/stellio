"""Stellio — instances Stellio distantes (liste, envoi de fichiers, découverte du réseau local)

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `remote_instances.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import os
import platform
import requests
import secrets
import threading
import time

_REQUIRED = (
    '_cleanup_expired_shares',
    '_get_or_create_local_peer_key',
    '_get_primary_user_id',
    '_is_path_within_sources',
    '_share_links',
    '_share_lock',
    'app',
    'app_logger',
    'get_current_version',
    'get_db',
    'get_local_ip',
    'jsonify',
    'load_settings',
    'login_required',
    'request',
    'require_peer_key',
    'session',
)
_OPTIONAL = ()   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('os', 'platform', 'requests', 'secrets', 'threading', 'time', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
_cleanup_expired_shares = None
_get_or_create_local_peer_key = None
_get_primary_user_id = None
_is_path_within_sources = None
_share_links = None
_share_lock = None
app = None
app_logger = None
get_current_version = None
get_db = None
get_local_ip = None
jsonify = None
load_settings = None
login_required = None
request = None
require_peer_key = None
session = None


def api_remote_instances_list():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, name, url, inbox_folder, last_status, last_seen_at, created_at FROM remote_instances WHERE user_id=? ORDER BY created_at ASC",
            (session['user_id'],)
        ).fetchall()
        return jsonify({"instances": [dict(r) for r in rows], "local_peer_key": _get_or_create_local_peer_key()}), 200
    finally:
        conn.close()

def api_remote_instances_add():
    data = request.json or {}
    name = (data.get('name') or '').strip()
    url = (data.get('url') or '').strip().rstrip('/')
    peer_key = (data.get('peer_key') or '').strip()
    inbox_folder = (data.get('inbox_folder') or '').strip() or None

    if not name or not url or not peer_key:
        return jsonify({"error": "Nom, adresse et clé d'appairage requis"}), 400
    if not url.startswith('http://') and not url.startswith('https://'):
        url = f"http://{url}"

    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO remote_instances (user_id, name, url, peer_key, inbox_folder) VALUES (?,?,?,?,?)",
            (session['user_id'], name, url, peer_key, inbox_folder)
        )
        conn.commit()
        return jsonify({"success": True, "id": cur.lastrowid}), 200
    finally:
        conn.close()

def api_remote_instances_delete(instance_id):
    conn = get_db()
    try:
        conn.execute("DELETE FROM remote_instances WHERE id=? AND user_id=?", (instance_id, session['user_id']))
        conn.commit()
        return jsonify({"success": True}), 200
    finally:
        conn.close()

def api_remote_instances_ping(instance_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM remote_instances WHERE id=? AND user_id=?", (instance_id, session['user_id'])
        ).fetchone()
        if not row:
            return jsonify({"error": "Instance introuvable"}), 404

        try:
            r = requests.get(
                f"{row['url']}/api/peer/handshake", timeout=5,
                headers={"X-Stellio-Peer-Key": row['peer_key']}
            )
            if r.ok:
                remote_info = r.json()
                conn.execute(
                    "UPDATE remote_instances SET last_status='online', last_seen_at=CURRENT_TIMESTAMP WHERE id=?",
                    (instance_id,)
                )
                conn.commit()
                return jsonify({"status": "online", "remote": remote_info}), 200
            conn.execute("UPDATE remote_instances SET last_status='error' WHERE id=?", (instance_id,))
            conn.commit()
            if r.status_code == 403:
                return jsonify({"status": "error", "error": "Clé d'appairage refusée par l'autre instance"}), 200
            return jsonify({"status": "error", "error": f"Réponse HTTP {r.status_code}"}), 200
        except Exception as e:
            conn.execute("UPDATE remote_instances SET last_status='offline' WHERE id=?", (instance_id,))
            conn.commit()
            return jsonify({"status": "offline", "error": "Instance injoignable"}), 200
    finally:
        conn.close()

def api_remote_instances_send(instance_id):
    data = request.json or {}
    file_path = (data.get('file_path') or '').strip()
    if not file_path or not os.path.isfile(file_path):
        return jsonify({"error": "Fichier introuvable"}), 404
    if not _is_path_within_sources(file_path, session['user_id']):
        return jsonify({"error": "Ce fichier n'appartient à aucune source configurée"}), 403

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM remote_instances WHERE id=? AND user_id=?", (instance_id, session['user_id'])
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return jsonify({"error": "Instance introuvable"}), 404

    _cleanup_expired_shares()
    token = secrets.token_urlsafe(24)
    with _share_lock:
        _share_links[token] = {
            'path': file_path, 'name': os.path.basename(file_path), 'created': time.time(),
        }
    local_ip = get_local_ip()
    share_url = f"http://{local_ip}:{_MAIN.get('SERVER_PORT') or _MAIN.get('SERVER_PORT_RESOLVED') or 5000}/share/{token}"

    try:
        r = requests.post(
            f"{row['url']}/api/peer/receive-file", timeout=20,
            headers={"X-Stellio-Peer-Key": row['peer_key']},
            json={"url": share_url, "filename": os.path.basename(file_path),
                  "dest_folder": (data.get('dest_folder') or '').strip()}
        )
        if r.ok:
            app_logger.info(f"[RemoteInstance] Fichier {os.path.basename(file_path)} envoyé vers '{row['name']}'")
            return jsonify({"success": True}), 200
        with _share_lock:
            _share_links.pop(token, None)
        if r.status_code == 403:
            return jsonify({"error": "Clé d'appairage refusée par l'autre instance"}), 502
        try:
            remote_reason = (r.json() or {}).get('error') or ''
        except Exception:
            remote_reason = ''
        app_logger.warning(f"[RemoteInstance] '{row['name']}' a répondu HTTP {r.status_code}: {remote_reason}")
        if remote_reason:
            return jsonify({"error": f"L'autre instance a refusé le fichier (HTTP {r.status_code}) : {remote_reason}"}), 502
        return jsonify({"error": f"L'autre instance a refusé le fichier (HTTP {r.status_code})"}), 502
    except Exception as e:
        with _share_lock:
            _share_links.pop(token, None)
        app_logger.warning(f"[RemoteInstance] Envoi échoué vers '{row['name']}': {e}")
        return jsonify({"error": "Instance injoignable"}), 503

def api_remote_instances_folders(instance_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM remote_instances WHERE id=? AND user_id=?", (instance_id, session['user_id'])
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return jsonify({"error": "Instance introuvable"}), 404
    try:
        r = requests.get(
            f"{row['url']}/api/peer/folders", timeout=15,
            headers={"X-Stellio-Peer-Key": row['peer_key']},
            params={"path": request.args.get('path', '')}
        )
        if r.status_code == 404:
            return jsonify({"error": "L'autre instance n'est pas à jour (version sans choix de dossier)", "code": "peer_outdated"}), 502
        try:
            body = r.json()
        except Exception:
            body = {"error": f"Réponse invalide de l'autre instance (HTTP {r.status_code})"}
        if r.status_code == 403:
            return jsonify({"error": "Clé d'appairage refusée par l'autre instance"}), 502
        return jsonify(body), (200 if r.ok else 502)
    except Exception as e:
        app_logger.warning(f"[RemoteInstance] Liste des dossiers échouée vers '{row['name']}': {e}")
        return jsonify({"error": "Instance injoignable"}), 503

def api_peer_folders():
    user_id = _get_primary_user_id()
    if not user_id:
        return jsonify({"error": "Aucun utilisateur configuré sur cette instance"}), 500
    req_path = (request.args.get('path') or '').strip()

    roots = []
    conn = get_db()
    try:
        rows = conn.execute("SELECT name, path FROM sources WHERE user_id=? AND type='folder' ORDER BY id", (user_id,)).fetchall()
    finally:
        conn.close()
    for r_ in rows:
        if r_['path'] and os.path.isdir(r_['path']) and os.access(r_['path'], os.W_OK):
            roots.append({"name": r_['name'] or os.path.basename(r_['path'].rstrip('/\\')) or r_['path'], "path": r_['path']})

    if not req_path:
        return jsonify({"path": "", "parent": None, "folders": roots}), 200

    if not os.path.isdir(req_path) or not _is_path_within_sources(req_path, user_id):
        return jsonify({"error": "Dossier hors des sources de cette instance"}), 403

    norm = lambda p: os.path.realpath(p).replace('\\', '/').rstrip('/').lower()
    cur = norm(req_path)
    parent = None
    if not any(cur == norm(x['path']) for x in roots):
        par = os.path.dirname(req_path.rstrip('/\\'))
        if par and _is_path_within_sources(par, user_id):
            parent = par
    folders = []
    try:
        with os.scandir(req_path) as it:
            for e in it:
                if e.is_dir(follow_symlinks=False) and not e.name.startswith('.') and os.access(e.path, os.W_OK):
                    folders.append({"name": e.name, "path": e.path})
                if len(folders) >= 500:
                    break
    except Exception as e:
        return jsonify({"error": f"Lecture du dossier impossible : {e}"}), 500
    folders.sort(key=lambda x: x['name'].lower())
    return jsonify({"path": req_path, "parent": parent, "folders": folders}), 200

def _is_lan_request():
    import ipaddress
    if request.headers.get('Cf-Connecting-Ip') or request.headers.get('X-Forwarded-For'):
        return False
    try:
        ip = ipaddress.ip_address(request.remote_addr or '')
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local

def api_peer_identify():
    if not _is_lan_request():
        return jsonify({"error": "Réseau local uniquement"}), 403
    settings = load_settings() or {}
    return jsonify({
        "stellio": True,
        "name": settings.get('instance_name') or platform.node(),
        "version": get_current_version(),
    }), 200

_LAN_SCAN_CACHE = {"at": 0.0, "found": []}

_LAN_SCAN_CACHE_SECONDS = 60

_lan_scan_lock = threading.Lock()

def _scan_lan_for_stellio(timeout=0.4, port=None, max_parallel=64, force=False):
    if port is None:
        port = _MAIN.get('SERVER_PORT') or int(os.environ.get('STELLIO_PORT', '5000'))
    with _lan_scan_lock:
        if not force and time.time() - _LAN_SCAN_CACHE["at"] < _LAN_SCAN_CACHE_SECONDS:
            return list(_LAN_SCAN_CACHE["found"])
        found = _scan_lan_for_stellio_uncached(timeout, port, max_parallel)
        _LAN_SCAN_CACHE["at"] = time.time()
        _LAN_SCAN_CACHE["found"] = list(found)
        return found

def _scan_lan_for_stellio_uncached(timeout, port, max_parallel):
    local_ip = get_local_ip()
    if local_ip == '127.0.0.1' or local_ip.count('.') != 3:
        return []
    prefix = '.'.join(local_ip.split('.')[:3])
    found = []
    lock = threading.Lock()

    def _check(ip):
        try:
            r = requests.get(f"http://{ip}:{port}/api/peer/identify", timeout=timeout)
            if r.ok:
                d = r.json()
                if isinstance(d, dict) and d.get('stellio'):
                    with lock:
                        found.append({"name": d.get('name') or ip, "version": d.get('version') or '',
                                      "url": f"http://{ip}:{port}"})
        except Exception:
            pass

    batch = []
    for i in range(1, 255):
        ip = f"{prefix}.{i}"
        if ip == local_ip:
            continue
        t = threading.Thread(target=_check, args=(ip,), daemon=True)
        batch.append(t)
        t.start()
        if len(batch) >= max_parallel:
            for th in batch:
                th.join(timeout=timeout + 0.5)
            batch = []
    for th in batch:
        th.join(timeout=timeout + 0.5)
    return found

def api_remote_instances_status():
    conn = get_db()
    try:
        rows = [dict(r) for r in conn.execute(
            "SELECT id, name, url, peer_key FROM remote_instances WHERE user_id=? ORDER BY created_at ASC",
            (session['user_id'],)).fetchall()]
    finally:
        conn.close()

    results = {}

    def _probe(row):
        try:
            r = requests.get(f"{row['url']}/api/peer/handshake", timeout=3,
                             headers={"X-Stellio-Peer-Key": row['peer_key']})
            results[row['id']] = 'online' if r.ok else 'error'
        except Exception:
            results[row['id']] = 'offline'

    threads = [threading.Thread(target=_probe, args=(r,), daemon=True) for r in rows]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=4)

    out = []
    try:
        conn = get_db()
        try:
            for r in rows:
                st = results.get(r['id'], 'offline')
                if st == 'online':
                    conn.execute("UPDATE remote_instances SET last_status='online', last_seen_at=CURRENT_TIMESTAMP WHERE id=?", (r['id'],))
                else:
                    conn.execute("UPDATE remote_instances SET last_status=? WHERE id=?", (st, r['id']))
                out.append({"id": r['id'], "name": r['name'], "url": r['url'], "status": st, "online": st == 'online'})
            conn.commit()
        finally:
            conn.close()
    except Exception:
        out = [{"id": r['id'], "name": r['name'], "url": r['url'],
                "status": results.get(r['id'], 'offline'), "online": results.get(r['id']) == 'online'} for r in rows]
    return jsonify({"instances": out}), 200

def api_remote_instances_discover():
    found = _scan_lan_for_stellio(force=request.args.get('refresh') == '1')
    conn = get_db()
    try:
        known = {(r['url'] or '').rstrip('/').lower() for r in conn.execute(
            "SELECT url FROM remote_instances WHERE user_id=?", (session['user_id'],)).fetchall()}
    finally:
        conn.close()
    found = [f for f in found if f['url'].lower() not in known]
    found.sort(key=lambda f: f['name'].lower())
    return jsonify({"instances": found}), 200


_ROUTES = (
    ('/api/remote-instances', ['GET'], 'api_remote_instances_list', ('login_required', )),
    ('/api/remote-instances', ['POST'], 'api_remote_instances_add', ('login_required', )),
    ('/api/remote-instances/<int:instance_id>', ['DELETE'], 'api_remote_instances_delete', ('login_required', )),
    ('/api/remote-instances/<int:instance_id>/ping', ['POST'], 'api_remote_instances_ping', ('login_required', )),
    ('/api/remote-instances/<int:instance_id>/send', ['POST'], 'api_remote_instances_send', ('login_required', )),
    ('/api/remote-instances/<int:instance_id>/folders', ['GET'], 'api_remote_instances_folders', ('login_required', )),
    ('/api/peer/folders', ['GET'], 'api_peer_folders', ('require_peer_key', )),
    ('/api/peer/identify', ['GET'], 'api_peer_identify', ()),
    ('/api/remote-instances/status', ['GET'], 'api_remote_instances_status', ('login_required', )),
    ('/api/remote-instances/discover', ['GET'], 'api_remote_instances_discover', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"remote_instances.init : services manquants : {missing}")
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
