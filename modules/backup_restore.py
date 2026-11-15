"""Stellio — Sauvegarde : export, import, restauration, planification automatique (helpers)

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `backup_restore.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
from pathlib import Path
import datetime
import io
import json
import os
import re
import secrets
import shutil
import sqlite3
import tempfile
import threading
import time
import zipfile

_REQUIRED = (
    'DATA_DIR',
    'DB_PATH',
    'KEY_FILE',
    'SETTINGS_FILE',
    '_lower_thread_priority',
    '_settings_cache',
    '_wv_save_dialog',
    'app',
    'app_logger',
    'get_current_version',
    'invalidate_cache',
    'jsonify',
    'login_required',
    'request',
    'send_file',
)
_OPTIONAL = ('webview', )   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('Path', 'datetime', 'io', 'json', 'os', 're', 'secrets', 'shutil', 'sqlite3', 'tempfile', 'threading', 'time', 'zipfile', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
webview = None
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
DATA_DIR = None
DB_PATH = None
KEY_FILE = None
SETTINGS_FILE = None
_lower_thread_priority = None
_settings_cache = None
_wv_save_dialog = None
app = None
app_logger = None
get_current_version = None
invalidate_cache = None
jsonify = None
login_required = None
request = None
send_file = None


AUTO_BACKUP_CONFIG_FILE = None
AUTO_BACKUP_DEFAULT_DIR = None
BACKUP_MANIFEST_VERSION = 1

BACKUP_CATEGORY_TABLES = {
    'library': ['sources', 'tags', 'file_tags', 'favorites', 'projects', 'project_files'],
    'accounts': ['account_credentials'],
    'printers': ['printers'],
    'history': ['download_history', 'print_history', 'slicer_jobs'],
}

BACKUP_DEFAULT_INCLUDE = {'library': True, 'accounts': True, 'printers': True, 'history': True, 'settings': True}

def build_backup_zip_bytes(include=None):
    include = {**BACKUP_DEFAULT_INCLUDE, **(include or {})}
    tmp_db = None
    try:
        tmp_db = os.path.join(tempfile.gettempdir(), f'stellio_backup_{secrets.token_hex(6)}.db')

        src_conn = sqlite3.connect(DB_PATH)
        dst_conn = sqlite3.connect(tmp_db)
        with dst_conn:
            src_conn.backup(dst_conn)
        src_conn.close()

        tables_to_clear = []
        for category, tables in BACKUP_CATEGORY_TABLES.items():
            if not include.get(category, True):
                tables_to_clear.extend(tables)
        if tables_to_clear:
            cur = dst_conn.cursor()
            for table in tables_to_clear:
                try:
                    cur.execute(f"DELETE FROM {table}")
                except Exception as e:
                    app_logger.warning(f"[BACKUP] Impossible de vider la table {table}: {e}")
            dst_conn.commit()
            try:
                dst_conn.execute("VACUUM")
            except Exception:
                pass
        dst_conn.close()

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(tmp_db, 'stellio.db')

            if include.get('settings', True) and os.path.exists(SETTINGS_FILE):
                zf.write(SETTINGS_FILE, 'app_settings.json')

            if include.get('accounts', True):
                if os.path.exists(KEY_FILE):
                    zf.write(KEY_FILE, 'encryption.key')
                iv_file = KEY_FILE.replace('.key', '.iv')
                if os.path.exists(iv_file):
                    zf.write(iv_file, 'encryption.iv')

            manifest = {
                'app': 'stellio',
                'manifest_version': BACKUP_MANIFEST_VERSION,
                'app_version': get_current_version(),
                'exported_at': datetime.datetime.now().isoformat(),
                'included': include
            }
            zf.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))

        buf.seek(0)
        filename = f'stellio_backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
        return buf.getvalue(), filename
    finally:
        if tmp_db and os.path.exists(tmp_db):
            try:
                os.remove(tmp_db)
            except Exception:
                pass

def api_backup_export():
    try:
        data = request.get_json(silent=True) or {}
        include = data.get('include') or {}
        zip_bytes, filename = build_backup_zip_bytes(include=include)
        app_logger.info(f"[BACKUP] 📦 Export de sauvegarde généré: {filename} (inclus: {include})")
        return send_file(io.BytesIO(zip_bytes), mimetype='application/zip', as_attachment=True, download_name=filename)
    except Exception as e:
        app_logger.error(f"[BACKUP] Échec export: {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500

def api_backup_export_native():
    try:
        data = request.get_json(silent=True) or {}
        include = data.get('include') or {}
        zip_bytes, suggested_name = build_backup_zip_bytes(include=include)
    except Exception as e:
        app_logger.error(f"[BACKUP] Échec génération pour Enregistrer sous : {e}")
        return jsonify({"success": False, "error": str(e)}), 500

    try:
        import webview
        result = webview.windows[0].create_file_dialog(
            _wv_save_dialog(webview),
            directory=str(Path.home() / 'Downloads'),
            save_filename=suggested_name,
            file_types=('Archive ZIP (*.zip)', 'Tous les fichiers (*.*)')
        )
    except Exception as e:
        app_logger.error(f"[BACKUP] Échec ouverture boîte de dialogue : {e}")
        return jsonify({"success": False, "error": str(e)}), 500

    dest_path = result[0] if isinstance(result, (list, tuple)) else result
    if not dest_path:
        return jsonify({"success": False, "cancelled": True}), 200

    try:
        with open(dest_path, 'wb') as f:
            f.write(zip_bytes)
        app_logger.info(f"[BACKUP] 📦 Sauvegarde enregistrée : {dest_path}")
        return jsonify({"success": True, "path": dest_path}), 200
    except Exception as e:
        app_logger.error(f"[BACKUP] Échec écriture fichier : {e}")
        return jsonify({"success": False, "error": str(e)}), 500

def api_backup_import():
    if 'backup' not in request.files:
        return jsonify({"error": "Aucun fichier reçu"}), 400

    file = request.files['backup']
    if not file.filename.lower().endswith('.zip'):
        return jsonify({"error": "Le fichier doit être une archive .zip"}), 400

    tmp_zip = os.path.join(tempfile.gettempdir(), f'stellio_import_{secrets.token_hex(6)}.zip')
    file.save(tmp_zip)

    try:
        with _auto_backup_lock:
            info, err = _restore_backup_zip(tmp_zip)
        if err:
            return jsonify({"error": err[0]}), err[1]
        return jsonify({"success": True, "restart_required": True, "backed_up_to": info['backed_up_to']})
    except zipfile.BadZipFile:
        return jsonify({"error": "Fichier .zip invalide ou corrompu"}), 400
    except Exception as e:
        app_logger.error(f"[BACKUP] Échec import: {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500
    finally:
        try:
            os.remove(tmp_zip)
        except Exception:
            pass

AUTO_BACKUP_NAME_RE = re.compile(r'^stellio_(auto|manual)_\d{8}_\d{6}\.zip$')

AUTO_BACKUP_DEFAULTS = {
    'enabled': False,
    'frequency': 'daily',          
    'time': '03:00',              
    'weekday': 0,                  
    'day_of_month': 1,             
    'keep': 7,                     
    'include': dict(BACKUP_DEFAULT_INCLUDE),
    'folder': '',                  
    'last_run': None,
    'last_status': None,           
    'last_error': '',
}

_auto_backup_lock = threading.RLock()

def _load_auto_backup_config():
    cfg = json.loads(json.dumps(AUTO_BACKUP_DEFAULTS))
    try:
        with open(AUTO_BACKUP_CONFIG_FILE, 'r', encoding='utf-8') as f:
            saved = json.load(f)
        if isinstance(saved, dict):
            for k, v in saved.items():
                if k == 'include' and isinstance(v, dict):
                    cfg['include'].update({c: bool(v.get(c, True)) for c in BACKUP_DEFAULT_INCLUDE})
                elif k in cfg:
                    cfg[k] = v
    except FileNotFoundError:
        pass
    except Exception as e:
        app_logger.warning(f"[AUTO-BACKUP] Configuration illisible, valeurs par défaut utilisées : {e}")
    return _sanitize_auto_backup_config(cfg)

def _sanitize_auto_backup_config(cfg):
    cfg['enabled'] = bool(cfg.get('enabled'))
    if cfg.get('frequency') not in ('daily', 'weekly', 'monthly'):
        cfg['frequency'] = 'daily'
    m = re.match(r'^(\d{1,2}):(\d{2})$', str(cfg.get('time') or ''))
    if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
        cfg['time'] = '03:00'
    else:
        cfg['time'] = f"{int(m.group(1)):02d}:{m.group(2)}"
    try:
        cfg['weekday'] = min(6, max(0, int(cfg.get('weekday', 0))))
    except (TypeError, ValueError):
        cfg['weekday'] = 0
    try:
        cfg['day_of_month'] = min(28, max(1, int(cfg.get('day_of_month', 1))))
    except (TypeError, ValueError):
        cfg['day_of_month'] = 1
    try:
        cfg['keep'] = min(100, max(1, int(cfg.get('keep', 7))))
    except (TypeError, ValueError):
        cfg['keep'] = 7
    inc = cfg.get('include') if isinstance(cfg.get('include'), dict) else {}
    cfg['include'] = {c: bool(inc.get(c, True)) for c in BACKUP_DEFAULT_INCLUDE}
    cfg['folder'] = str(cfg.get('folder') or '').strip()
    return cfg

def _save_auto_backup_config(cfg):
    tmp = AUTO_BACKUP_CONFIG_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    os.replace(tmp, AUTO_BACKUP_CONFIG_FILE)

def _auto_backup_folder(cfg, create=True):
    folder = cfg.get('folder') or AUTO_BACKUP_DEFAULT_DIR
    if create:
        os.makedirs(folder, exist_ok=True)
    return folder

def _at_time(day, hhmm):
    h, m = (int(x) for x in hhmm.split(':'))
    return datetime.datetime.combine(day, datetime.time(h, m))

def _month_occurrence(year, month, dom, hhmm):
    return _at_time(datetime.date(year, month, min(dom, 28)), hhmm)

def _last_scheduled_run(cfg, now):
    freq, hhmm = cfg['frequency'], cfg['time']
    if freq == 'daily':
        cand = _at_time(now.date(), hhmm)
        return cand if cand <= now else cand - datetime.timedelta(days=1)
    if freq == 'weekly':
        back = (now.weekday() - cfg['weekday']) % 7
        cand = _at_time(now.date() - datetime.timedelta(days=back), hhmm)
        return cand if cand <= now else cand - datetime.timedelta(days=7)
    cand = _month_occurrence(now.year, now.month, cfg['day_of_month'], hhmm)
    if cand <= now:
        return cand
    y, mth = (now.year - 1, 12) if now.month == 1 else (now.year, now.month - 1)
    return _month_occurrence(y, mth, cfg['day_of_month'], hhmm)

def _next_scheduled_run(cfg, now):
    freq, hhmm = cfg['frequency'], cfg['time']
    last = _last_scheduled_run(cfg, now)
    if freq == 'daily':
        return last + datetime.timedelta(days=1)
    if freq == 'weekly':
        return last + datetime.timedelta(days=7)
    y, mth = (last.year + 1, 1) if last.month == 12 else (last.year, last.month + 1)
    return _month_occurrence(y, mth, cfg['day_of_month'], hhmm)

def _auto_backup_is_due(cfg, now):
    if not cfg['enabled']:
        return False
    try:
        last_run = datetime.datetime.fromisoformat(cfg['last_run']) if cfg.get('last_run') else None
    except ValueError:
        last_run = None
    if last_run is None:
        return False   
    return last_run < _last_scheduled_run(cfg, now)

def _create_backup_file(include, kind, folder):
    zip_bytes, _ = build_backup_zip_bytes(include=include)
    name = f"stellio_{kind}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    path = os.path.join(folder, name)
    tmp = path + '.part'
    with open(tmp, 'wb') as f:
        f.write(zip_bytes)
    os.replace(tmp, path)
    return path

def _prune_auto_backups(folder, keep):
    try:
        autos = sorted((n for n in os.listdir(folder) if AUTO_BACKUP_NAME_RE.match(n) and n.startswith('stellio_auto_')),
                       reverse=True)
        for old in autos[keep:]:
            try:
                os.remove(os.path.join(folder, old))
                app_logger.info(f"[AUTO-BACKUP] Ancienne sauvegarde supprimée : {old}")
            except Exception as e:
                app_logger.warning(f"[AUTO-BACKUP] Suppression impossible de {old} : {e}")
    except Exception as e:
        app_logger.warning(f"[AUTO-BACKUP] Rotation impossible : {e}")

def run_auto_backup(kind='auto', include_override=None):
    with _auto_backup_lock:
        cfg = _load_auto_backup_config()
        include = include_override if include_override is not None else cfg['include']
        try:
            folder = _auto_backup_folder(cfg)
            path = _create_backup_file(include, kind, folder)
            if kind == 'auto':
                _prune_auto_backups(folder, cfg['keep'])
                cfg['last_run'] = datetime.datetime.now().isoformat(timespec='seconds')
                cfg['last_status'], cfg['last_error'] = 'ok', ''
                _save_auto_backup_config(cfg)
            app_logger.info(f"[AUTO-BACKUP] ✅ Sauvegarde {kind} créée : {path}")
            return path, None
        except Exception as e:
            app_logger.error(f"[AUTO-BACKUP] Échec de la sauvegarde {kind} : {e}")
            if kind == 'auto':
                cfg['last_run'] = datetime.datetime.now().isoformat(timespec='seconds')
                cfg['last_status'], cfg['last_error'] = 'error', str(e)[:300]
                try:
                    _save_auto_backup_config(cfg)
                except Exception:
                    pass
            return None, str(e)

AUTO_BACKUP_GRACE_SECONDS = 600   

def _auto_backup_missed_info(cfg, now):
    if not _auto_backup_is_due(cfg, now):
        return None
    scheduled = _last_scheduled_run(cfg, now)
    if (now - scheduled).total_seconds() > AUTO_BACKUP_GRACE_SECONDS:
        return scheduled
    return None

def _auto_backup_scheduler():
    _lower_thread_priority()
    app_logger.info("[AUTO-BACKUP] Planificateur démarré")
    time.sleep(20) 
    while True:
        try:
            cfg = _load_auto_backup_config()
            now = datetime.datetime.now()
            if _auto_backup_is_due(cfg, now):
                if _auto_backup_missed_info(cfg, now) is None:
                    run_auto_backup('auto')  
        except Exception as e:
            app_logger.warning(f"[AUTO-BACKUP] Erreur du planificateur : {e}")
        time.sleep(60)

def _list_backups(folder):
    items = []
    try:
        names = sorted((n for n in os.listdir(folder) if AUTO_BACKUP_NAME_RE.match(n)), reverse=True)
    except FileNotFoundError:
        return items
    for name in names:
        path = os.path.join(folder, name)
        try:
            st = os.stat(path)
            item = {'name': name, 'kind': 'auto' if name.startswith('stellio_auto_') else 'manual',
                    'size': st.st_size,
                    'created': datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec='seconds'),
                    'include': None, 'app_version': None, 'valid': True}
            try:
                with zipfile.ZipFile(path, 'r') as zf:
                    manifest = json.loads(zf.read('manifest.json').decode('utf-8'))
                    item['include'] = manifest.get('included')
                    item['app_version'] = manifest.get('app_version')
                    if manifest.get('exported_at'):
                        item['created'] = manifest['exported_at'][:19]
            except Exception:
                item['valid'] = False
            items.append(item)
        except Exception:
            continue
    return items

def _merge_backup_categories(backup_db_path, categories):
    conn = sqlite3.connect(DB_PATH, timeout=30)
    try:
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute("ATTACH DATABASE ? AS bk", (backup_db_path,))
        for cat in categories:
            for table in BACKUP_CATEGORY_TABLES.get(cat, []):
                cols_main = [r[1] for r in conn.execute(f"PRAGMA main.table_info({table})")]
                cols_bk = [r[1] for r in conn.execute(f"PRAGMA bk.table_info({table})")]
                common = [c for c in cols_main if c in cols_bk]
                if not common:
                    continue
                col_sql = ', '.join(f'"{c}"' for c in common)
                conn.execute(f"DELETE FROM main.{table}")
                conn.execute(f"INSERT INTO main.{table} ({col_sql}) SELECT {col_sql} FROM bk.{table}")
        conn.commit()
        conn.execute("DETACH DATABASE bk")
    finally:
        conn.close()

def _restore_backup_zip(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zf:
        names = zf.namelist()
        if 'manifest.json' not in names or 'stellio.db' not in names:
            return None, ("Archive invalide : ce n'est pas une sauvegarde Stellio.", 400)

        manifest = json.loads(zf.read('manifest.json').decode('utf-8'))
        included = manifest.get('included')
        partial = isinstance(included, dict) and not all(included.get(c, True) for c in BACKUP_DEFAULT_INCLUDE)

        backup_dir = os.path.join(DATA_DIR, 'backups', datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(backup_dir, exist_ok=True)
        for existing, dest_name in [(DB_PATH, 'stellio.db'), (SETTINGS_FILE, 'app_settings.json'),
                                      (KEY_FILE, 'encryption.key'), (KEY_FILE.replace('.key', '.iv'), 'encryption.iv')]:
            if os.path.exists(existing):
                shutil.copy2(existing, os.path.join(backup_dir, dest_name))

        if partial:
            tmp_db = os.path.join(tempfile.gettempdir(), f'stellio_restore_{secrets.token_hex(6)}.db')
            try:
                with zf.open('stellio.db') as src, open(tmp_db, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
                cats = [c for c in BACKUP_CATEGORY_TABLES if included.get(c, True)]
                _merge_backup_categories(tmp_db, cats)
            finally:
                try:
                    os.remove(tmp_db)
                except Exception:
                    pass
        else:
            zf.extract('stellio.db', DATA_DIR)
            os.replace(os.path.join(DATA_DIR, 'stellio.db'), DB_PATH)

        if 'app_settings.json' in names and (not partial or included.get('settings', True)):
            zf.extract('app_settings.json', DATA_DIR)
            os.replace(os.path.join(DATA_DIR, 'app_settings.json'), SETTINGS_FILE)

        if 'encryption.key' in names and 'encryption.iv' in names and (not partial or included.get('accounts', True)):
            zf.extract('encryption.key', DATA_DIR)
            zf.extract('encryption.iv', DATA_DIR)
            os.replace(os.path.join(DATA_DIR, 'encryption.key'), KEY_FILE)
            os.replace(os.path.join(DATA_DIR, 'encryption.iv'), KEY_FILE.replace('.key', '.iv'))

    global _settings_cache
    _settings_cache = {}
    invalidate_cache()
    app_logger.info(f"[BACKUP] ✅ Sauvegarde restaurée (créée le {manifest.get('exported_at', '?')}, "
                    f"{'partielle' if partial else 'complète'}). Copie de sécurité: {backup_dir}")
    return {'exported_at': manifest.get('exported_at'), 'backed_up_to': backup_dir, 'partial': partial}, None

def _auto_backup_config_response(cfg):
    now = datetime.datetime.now()
    folder = _auto_backup_folder(cfg, create=False)
    return {**cfg, 'folder_effective': folder, 'folder_is_default': not cfg.get('folder'),
            'next_run': _next_scheduled_run(cfg, now).isoformat(timespec='minutes') if cfg['enabled'] else None}

def _resolve_backup_file(name):
    name = os.path.basename(str(name or ''))
    if not AUTO_BACKUP_NAME_RE.match(name):
        return None
    path = os.path.join(_auto_backup_folder(_load_auto_backup_config(), create=False), name)
    return path if os.path.isfile(path) else None


_ROUTES = (
    ('/api/backup/export', ['POST'], 'api_backup_export', ('login_required', )),
    ('/api/backup/export-native', ['POST'], 'api_backup_export_native', ('login_required', )),
    ('/api/backup/import', ['POST'], 'api_backup_import', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"backup_restore.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    g['AUTO_BACKUP_CONFIG_FILE'] = os.path.join(DATA_DIR, 'auto_backup.json')
    g['AUTO_BACKUP_DEFAULT_DIR'] = os.path.join(DATA_DIR, 'auto_backups')
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {'AUTO_BACKUP_CONFIG_FILE': g['AUTO_BACKUP_CONFIG_FILE'], 'AUTO_BACKUP_DEFAULT_DIR': g['AUTO_BACKUP_DEFAULT_DIR']}
