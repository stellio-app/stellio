"""Stellio — corbeille (liste, restauration, purge)

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `trash_routes.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import os
import shutil
import time

_REQUIRED = (
    'TRASH_DIR',
    'TRASH_ITEMS_DIR',
    'TRASH_RETENTION_SECONDS',
    '_ensure_trash_table',
    '_purge_expired_trash',
    '_trash_list_for_user',
    '_trash_purge_expired_rows',
    '_trash_purge_row',
    '_trash_registry',
    '_trash_registry_lock',
    '_trash_restore_row',
    '_trash_retention_seconds',
    'api_restore_trash_batch_core',
    'app',
    'app_logger',
    'get_db',
    'journal_log',
    'jsonify',
    'login_required',
    'request',
    'session',
)
_OPTIONAL = ()   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('os', 'shutil', 'time', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
TRASH_DIR = None
TRASH_ITEMS_DIR = None
TRASH_RETENTION_SECONDS = None
_ensure_trash_table = None
_purge_expired_trash = None
_trash_list_for_user = None
_trash_purge_expired_rows = None
_trash_purge_row = None
_trash_registry = None
_trash_registry_lock = None
_trash_restore_row = None
_trash_retention_seconds = None
api_restore_trash_batch_core = None
app = None
app_logger = None
get_db = None
journal_log = None
jsonify = None
login_required = None
request = None
session = None


def api_trash_items():
    try:
        _purge_expired_trash()
        _trash_purge_expired_rows()
        items = _trash_list_for_user(session['user_id'])
        return jsonify({'items': items, 'retention_days': _trash_retention_seconds() // 86400}), 200
    except Exception as e:
        app_logger.error(f"[API] Erreur api_trash_items: {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500

def _trash_parse_key(key):
    kind, _, ident = (key or '').partition(':')
    return kind, ident

def api_trash_restore():
    try:
        key = (request.get_json(silent=True) or {}).get('key', '')
        kind, ident = _trash_parse_key(key)
        uid = session['user_id']
        if kind == 'files':
            return api_restore_trash_batch_core(ident)
        if kind != 'row' or not ident.isdigit():
            return jsonify({'error': 'Élément invalide'}), 400
        _ensure_trash_table()
        conn = get_db()
        try:
            item = conn.execute("SELECT * FROM trash_items WHERE id = ? AND user_id = ?", (int(ident), uid)).fetchone()
            if not item:
                return jsonify({'error': "Cet élément n'est plus dans la corbeille"}), 404
            ok, err = _trash_restore_row(conn, item)
            if not ok:
                conn.rollback()
                return jsonify({'error': err}), 400
            conn.execute("DELETE FROM trash_items WHERE id = ?", (item['id'],))
            conn.commit()
            try:
                os.rmdir(os.path.join(TRASH_ITEMS_DIR, str(item['id'])))
            except OSError:
                pass
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        return jsonify({'success': True, 'kind': item['kind'], 'label': item['label']}), 200
    except Exception as e:
        app_logger.error(f"[Trash] Restauration impossible: {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500

def _trash_purge_batch(batch_id):
    with _trash_registry_lock:
        _trash_registry.pop(batch_id, None)
    shutil.rmtree(os.path.join(TRASH_DIR, batch_id), ignore_errors=True)

def _trash_purge_key(conn, uid, key):
    kind, ident = _trash_parse_key(key)
    if kind == 'files':
        with _trash_registry_lock:
            entry = _trash_registry.get(ident)
        if not entry or entry.get('user_id') != uid:
            return False
        _trash_purge_batch(ident)
        return True
    if kind == 'row' and ident.isdigit():
        r = conn.execute("SELECT id FROM trash_items WHERE id = ? AND user_id = ?", (int(ident), uid)).fetchone()
        if not r:
            return False
        _trash_purge_row(conn, r['id'])
        return True
    return False

def api_trash_purge():
    """Supprime définitivement un élément de la corbeille (ou tous : {"all": true})."""
    try:
        data = request.get_json(silent=True) or {}
        uid = session['user_id']
        _ensure_trash_table()
        conn = get_db()
        try:
            keys = [i['key'] for i in _trash_list_for_user(uid)] if data.get('all') else [data.get('key', '')]
            n = sum(1 for k in keys if _trash_purge_key(conn, uid, k))
            conn.commit()
        finally:
            conn.close()
        if n:
            journal_log('purge', f'{n} élément(s)', detail='suppression définitive depuis la corbeille')
        return jsonify({'success': True, 'purged': n}), 200
    except Exception as e:
        app_logger.error(f"[Trash] Suppression définitive impossible: {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500

def api_trash_list():
    """Lots présents dans la corbeille (restaurables pendant TRASH_RETENTION_SECONDS) pour l'utilisateur courant."""
    try:
        _purge_expired_trash()
        now = time.time()
        uid = session.get('user_id')
        out = []
        with _trash_registry_lock:
            items = list(_trash_registry.items())
        for bid, entry in items:
            if entry.get('user_id') != uid:
                continue
            names = [os.path.basename(e.get('original', '')) for e in entry.get('entries', [])]
            left = int(TRASH_RETENTION_SECONDS - (now - entry.get('created_at', now)))
            if left <= 0 or not names:
                continue
            out.append({'batch_id': bid, 'count': len(names), 'names': names[:3], 'seconds_left': left})
        out.sort(key=lambda b: -b['seconds_left'])
        return jsonify({'batches': out, 'retention_seconds': TRASH_RETENTION_SECONDS}), 200
    except Exception as e:
        app_logger.error(f"[API] Erreur api_trash_list: {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500


_ROUTES = (
    ('/api/trash/items', ['GET'], 'api_trash_items', ('login_required', )),
    ('/api/trash/restore', ['POST'], 'api_trash_restore', ('login_required', )),
    ('/api/trash/purge', ['POST'], 'api_trash_purge', ('login_required', )),
    ('/api/trash', ['GET'], 'api_trash_list', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"trash_routes.init : services manquants : {missing}")
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
