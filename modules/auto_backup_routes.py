"""Stellio — sauvegarde automatique : routes de configuration, liste, restauration

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `auto_backup_routes.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import datetime
import os
import secrets
import zipfile

_REQUIRED = (
    'BACKUP_DEFAULT_INCLUDE',
    '_auto_backup_config_response',
    '_auto_backup_folder',
    '_auto_backup_lock',
    '_auto_backup_missed_info',
    '_list_backups',
    '_load_auto_backup_config',
    '_next_scheduled_run',
    '_prune_auto_backups',
    '_resolve_backup_file',
    '_restore_backup_zip',
    '_sanitize_auto_backup_config',
    '_save_auto_backup_config',
    'app',
    'app_logger',
    'jsonify',
    'login_required',
    'request',
    'run_auto_backup',
)
_OPTIONAL = ()   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('datetime', 'os', 'secrets', 'zipfile', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
BACKUP_DEFAULT_INCLUDE = None
_auto_backup_config_response = None
_auto_backup_folder = None
_auto_backup_lock = None
_auto_backup_missed_info = None
_list_backups = None
_load_auto_backup_config = None
_next_scheduled_run = None
_prune_auto_backups = None
_resolve_backup_file = None
_restore_backup_zip = None
_sanitize_auto_backup_config = None
_save_auto_backup_config = None
app = None
app_logger = None
jsonify = None
login_required = None
request = None
run_auto_backup = None


def api_auto_backup_get_config():
    with _auto_backup_lock:
        return jsonify(_auto_backup_config_response(_load_auto_backup_config())), 200

def api_auto_backup_set_config():
    data = request.get_json(silent=True) or {}
    with _auto_backup_lock:
        cfg = _load_auto_backup_config()
        was_enabled = cfg['enabled']
        for key in ('enabled', 'frequency', 'time', 'weekday', 'day_of_month', 'keep', 'include', 'folder'):
            if key in data:
                cfg[key] = data[key]
        cfg = _sanitize_auto_backup_config(cfg)
        if cfg['folder']:
            try:
                if not os.path.isabs(cfg['folder']):
                    return jsonify({"error": "Le dossier de sauvegarde doit être un chemin absolu."}), 400
                os.makedirs(cfg['folder'], exist_ok=True)
                probe = os.path.join(cfg['folder'], f'.stellio_write_test_{secrets.token_hex(4)}')
                with open(probe, 'w') as f:
                    f.write('ok')
                os.remove(probe)
            except Exception as e:
                return jsonify({"error": f"Dossier inaccessible en écriture : {e}"}), 400
        if cfg['enabled'] and not was_enabled:
            cfg['last_run'] = datetime.datetime.now().isoformat(timespec='seconds')   
        _save_auto_backup_config(cfg)
        if cfg['enabled']:
            _prune_auto_backups(_auto_backup_folder(cfg, create=False), cfg['keep'])
        return jsonify(_auto_backup_config_response(cfg)), 200

def api_auto_backup_missed():
    with _auto_backup_lock:
        cfg = _load_auto_backup_config()
        now = datetime.datetime.now()
        scheduled = _auto_backup_missed_info(cfg, now)
        return jsonify({
            'missed': scheduled is not None,
            'scheduled': scheduled.isoformat(timespec='minutes') if scheduled else None,
            'next_run': _next_scheduled_run(cfg, now).isoformat(timespec='minutes') if cfg['enabled'] else None,
        }), 200

def api_auto_backup_missed_answer():
    data = request.get_json(silent=True) or {}
    action = data.get('action')
    with _auto_backup_lock:
        if action == 'run':
            path, err = run_auto_backup('auto')
            if err:
                return jsonify({"error": err}), 500
            return jsonify({"success": True, "name": os.path.basename(path)}), 200
        if action == 'skip':
            cfg = _load_auto_backup_config()
            cfg['last_run'] = datetime.datetime.now().isoformat(timespec='seconds')   
            _save_auto_backup_config(cfg)
            return jsonify({"success": True, "next_run": _next_scheduled_run(cfg, datetime.datetime.now()).isoformat(timespec='minutes')}), 200
    return jsonify({"error": "Action inconnue"}), 400

def api_auto_backup_list():
    with _auto_backup_lock:
        cfg = _load_auto_backup_config()
        return jsonify({'backups': _list_backups(_auto_backup_folder(cfg, create=False)),
                        'folder': _auto_backup_folder(cfg, create=False)}), 200

def api_auto_backup_run_now():
    data = request.get_json(silent=True) or {}
    include = data.get('include')
    if isinstance(include, dict):
        include = {c: bool(include.get(c, True)) for c in BACKUP_DEFAULT_INCLUDE}
    else:
        include = None
    path, err = run_auto_backup('manual', include_override=include)
    if err:
        return jsonify({"error": err}), 500
    return jsonify({"success": True, "name": os.path.basename(path)}), 200

def api_auto_backup_restore():
    data = request.get_json(silent=True) or {}
    path = _resolve_backup_file(data.get('name'))
    if not path:
        return jsonify({"error": "Sauvegarde introuvable"}), 404
    try:
        with _auto_backup_lock:
            info, err = _restore_backup_zip(path)
        if err:
            return jsonify({"error": err[0]}), err[1]
        return jsonify({"success": True, "restart_required": True, **info}), 200
    except zipfile.BadZipFile:
        return jsonify({"error": "Fichier .zip invalide ou corrompu"}), 400
    except Exception as e:
        app_logger.error(f"[BACKUP] Échec restauration depuis la liste : {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500

def api_auto_backup_delete():
    data = request.get_json(silent=True) or {}
    path = _resolve_backup_file(data.get('name'))
    if not path:
        return jsonify({"error": "Sauvegarde introuvable"}), 404
    try:
        os.remove(path)
        return jsonify({"success": True}), 200
    except Exception as e:
        app_logger.error(f"[BACKUP] Suppression impossible : {e}")
        return jsonify({"error": "Suppression impossible"}), 500


_ROUTES = (
    ('/api/backup/auto/config', ['GET'], 'api_auto_backup_get_config', ('login_required', )),
    ('/api/backup/auto/config', ['POST'], 'api_auto_backup_set_config', ('login_required', )),
    ('/api/backup/auto/missed', ['GET'], 'api_auto_backup_missed', ('login_required', )),
    ('/api/backup/auto/missed', ['POST'], 'api_auto_backup_missed_answer', ('login_required', )),
    ('/api/backup/auto/list', ['GET'], 'api_auto_backup_list', ('login_required', )),
    ('/api/backup/auto/run', ['POST'], 'api_auto_backup_run_now', ('login_required', )),
    ('/api/backup/auto/restore', ['POST'], 'api_auto_backup_restore', ('login_required', )),
    ('/api/backup/auto/delete', ['POST'], 'api_auto_backup_delete', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"auto_backup_routes.init : services manquants : {missing}")
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
