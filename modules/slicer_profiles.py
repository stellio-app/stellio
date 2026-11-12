"""Stellio — profils de slicer (import, affectation, détection automatique, synchronisation)

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `slicer_profiles.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import json
import numpy as np
import os
import re
import threading
import time

_REQUIRED = (
    'SLICER_SUBDIR_TYPE_HINTS',
    '_apply_printer_autoguess',
    '_get_primary_user_id',
    '_get_profiles_watch_dir',
    '_parse_slicer_profile_file',
    '_refresh_stale_slicer_profiles',
    '_remember_printer_alias',
    '_safe_int',
    '_scan_dir_for_profiles',
    '_scan_watch_dir_for_profiles',
    '_server_edition_only',
    'app',
    'app_logger',
    'jsonify',
    'load_slicer_profiles',
    'login_required',
    'request',
    'save_slicer_profiles',
    'session',
    'version',
)
_OPTIONAL = ()   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('json', 'np', 'os', 're', 'threading', 'time', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
SLICER_SUBDIR_TYPE_HINTS = None
_apply_printer_autoguess = None
_get_primary_user_id = None
_get_profiles_watch_dir = None
_parse_slicer_profile_file = None
_refresh_stale_slicer_profiles = None
_remember_printer_alias = None
_safe_int = None
_scan_dir_for_profiles = None
_scan_watch_dir_for_profiles = None
_server_edition_only = None
app = None
app_logger = None
jsonify = None
load_slicer_profiles = None
login_required = None
request = None
save_slicer_profiles = None
session = None
version = None


def api_slicer_profiles_list():
    profiles = load_slicer_profiles()
    _refresh_stale_slicer_profiles(profiles)  
    newly_imported = []
    try:
        newly_imported = _autodetect_new_slicer_profiles(profiles, session['user_id'])  
    except Exception as e:
        app_logger.debug(f"[SlicerProfiles] Auto-détection silencieuse ignorée: {e}")
    return jsonify({"profiles": profiles, "newly_imported": newly_imported}), 200

def api_slicer_profiles_import():
    files = request.files.getlist('profiles')
    if not files:
        return jsonify({"error": "Aucun fichier reçu"}), 400

    printer_id_raw = request.form.get('printer_id')
    printer_id = _safe_int(printer_id_raw)

    profiles = load_slicer_profiles()
    imported, errors = [], []

    for file in files:
        if not file or not file.filename:
            continue
        try:
            content = file.read()
            new_profiles = _parse_slicer_profile_file(file.filename, content)
            for np in new_profiles:
                if printer_id:
                    np['printer_id'] = printer_id
                    np['printer_match_confirmed'] = True
            profiles.extend(new_profiles)
            imported.extend(new_profiles)
        except Exception as e:
            errors.append({"filename": file.filename, "error": str(e)})

    if imported:
        if not printer_id:
            _apply_printer_autoguess(imported, session['user_id'])
        save_slicer_profiles(profiles)
        app_logger.info(f"[SlicerProfiles] {len(imported)} profil(s) importé(s) manuellement")

    if not imported:
        return jsonify({"error": "Aucun profil valide importé", "errors": errors}), 400

    return jsonify({"imported": imported, "errors": errors, "profiles": profiles}), 200

def api_slicer_profiles_import_json():
    """Édition serveur : importe un profil collé en texte (bouton « Copy raw JSON » du site Orca Cloud)."""
    blocked = _server_edition_only()
    if blocked:
        return blocked
    data = request.get_json(silent=True) or {}
    text = str(data.get('json') or '').strip()
    if not text or len(text) > 2_000_000:
        return jsonify({"error": "JSON vide ou trop volumineux", "code": "invalid_json"}), 400
    try:
        raw = json.loads(text)
    except ValueError:
        return jsonify({"error": "JSON invalide", "code": "invalid_json"}), 400
    if not isinstance(raw, dict):
        return jsonify({"error": "Ce JSON n'est pas un profil", "code": "invalid_json"}), 400
    raw_lower = {str(k).lower(): v for k, v in raw.items()}
    profile_markers = ('layer_height', 'fill_density', 'sparse_infill_density', 'filament_type', 'nozzle_diameter',
                       'nozzle_temperature', 'temperature', 'wall_loops', 'outer_wall_speed', 'perimeters',
                       'bed_temperature', 'hot_plate_temp', 'support_enable', 'inherits')
    if str(raw_lower.get('type') or '').lower() not in ('process', 'filament', 'machine', 'print') \
            and not any(k in raw_lower for k in profile_markers):
        return jsonify({"error": "Ce JSON ne ressemble pas à un profil de slicer", "code": "invalid_profile"}), 400
    name = re.sub(r'\s+', ' ', str(raw.get('name') or '')).strip()[:120] or 'Orca Cloud profile'
    filename = f"orca-cloud-{re.sub(r'[^A-Za-z0-9._-]+', '_', name)[:70]}.json"
    try:
        new_profiles = _parse_slicer_profile_file(filename, text.encode('utf-8'))
    except Exception as e:
        return jsonify({"error": f"Profil non reconnu : {e}", "code": "invalid_profile"}), 400
    if not new_profiles:
        return jsonify({"error": "Profil non reconnu", "code": "invalid_profile"}), 400
    profiles = [p for p in load_slicer_profiles() if p.get('source_filename') != filename]
    profiles.extend(new_profiles)
    _apply_printer_autoguess(new_profiles, session['user_id'])
    save_slicer_profiles(profiles)
    app_logger.info(f"[SlicerProfiles] Profil collé importé ({len(new_profiles)})")
    return jsonify({"imported": new_profiles, "profiles": profiles}), 200

def api_slicer_profiles_assign_printer(profile_id):
    data = request.json or {}
    printer_id_raw = data.get('printer_id')
    printer_id = _safe_int(printer_id_raw)

    profiles = load_slicer_profiles()
    target = None
    for p in profiles:
        if p.get('id') == profile_id:
            p['printer_id'] = printer_id
            p['printer_match_confirmed'] = bool(printer_id)
            target = p
            break
    if not target:
        return jsonify({"error": "Profil introuvable"}), 404

    save_slicer_profiles(profiles)

    if printer_id and target.get('compatible_printers'):
        _remember_printer_alias(printer_id, session['user_id'], target['compatible_printers'])

    return jsonify({"success": True, "profiles": profiles}), 200

def api_slicer_profiles_assign_type(profile_id):
    data = request.json or {}
    new_type = str(data.get('profile_type') or '').strip().lower()
    if new_type not in ('printer', 'filament', 'process'):
        return jsonify({"error": "Type de profil invalide (attendu : printer, filament ou process)"}), 400

    profiles = load_slicer_profiles()
    target = None
    for p in profiles:
        if p.get('id') == profile_id:
            p['profile_type'] = new_type


            p['profile_type_confirmed'] = True
            target = p
            break
    if not target:
        return jsonify({"error": "Profil introuvable"}), 404

    save_slicer_profiles(profiles)
    return jsonify({"success": True, "profiles": profiles}), 200

def api_slicer_profiles_delete(profile_id):
    profiles = load_slicer_profiles()
    new_profiles = [p for p in profiles if p.get('id') != profile_id]
    if len(new_profiles) == len(profiles):
        return jsonify({"error": "Profil introuvable"}), 404
    save_slicer_profiles(new_profiles)
    return jsonify({"success": True, "profiles": new_profiles}), 200

SLICER_AUTODETECT_DIRS = {
    'prusaslicer': ('PrusaSlicer', ['print', 'filament', 'printer']),
    'superslicer': ('SuperSlicer', ['print', 'filament', 'printer']),
}

SLICER_VERSIONED_USER_DIRS = {
    'orcaslicer':  ('OrcaSlicer\\user', ['process', 'filament', 'machine']),
    'bambustudio': ('BambuStudio\\user', ['process', 'filament', 'machine']),
    'qidistudio': ('QIDIStudio\\user', ['process', 'filament', 'machine']),
}

SLICER_CURA_FAMILY_DIRS = {
    'cura': 'cura',
    'anycubic_slicer_next': 'Anycubic Slicer Next',
}

def _scan_versioned_user_dir(base_path, subdirs, already_imported, imported_out, slicer_hint=None):
    if not os.path.isdir(base_path):
        return
    try:
        entries = os.listdir(base_path)
    except Exception as e:
        app_logger.debug(f"[SlicerProfiles] Dossier illisible {base_path}: {e}")
        return
    for entry in entries:
        versioned = os.path.join(base_path, entry)
        if not os.path.isdir(versioned):
            continue
        for sd in subdirs:
            _scan_dir_for_profiles(os.path.join(versioned, sd), already_imported, imported_out, slicer_hint=slicer_hint,
                                    type_hint=SLICER_SUBDIR_TYPE_HINTS.get(sd))

def _scan_creality_print_dir(base_path, already_imported, imported_out):
    if not os.path.isdir(base_path):
        return
    try:
        versions = os.listdir(base_path)
    except Exception as e:
        app_logger.debug(f"[SlicerProfiles] Dossier illisible {base_path}: {e}")
        return
    for version in versions:
        user_dir = os.path.join(base_path, version, 'user')
        if not os.path.isdir(user_dir):
            continue
        try:
            user_ids = os.listdir(user_dir)
        except Exception as e:
            app_logger.debug(f"[SlicerProfiles] Dossier illisible {user_dir}: {e}")
            continue
        for uid in user_ids:
            uid_dir = os.path.join(user_dir, uid)
            if not os.path.isdir(uid_dir):
                continue
            for sd in ('process', 'filament', 'machine'):
                _scan_dir_for_profiles(os.path.join(uid_dir, sd), already_imported, imported_out, slicer_hint='creality_print',
                                        type_hint=SLICER_SUBDIR_TYPE_HINTS.get(sd))

def api_slicer_profiles_refresh():
    profiles = load_slicer_profiles()
    updated_count, errors = _refresh_stale_slicer_profiles(profiles)
    return jsonify({"updated": updated_count, "total": len(profiles), "profiles": profiles, "errors": errors}), 200

def _autodetect_new_slicer_profiles(profiles, user_id):
    appdata = os.environ.get('APPDATA')
    watch_dir = _get_profiles_watch_dir()
    if not appdata and not watch_dir:
        return []  

    already_imported = {p.get('source_filename') for p in profiles}
    imported = []

    for slicer, (base_rel, subdirs) in (SLICER_AUTODETECT_DIRS.items() if appdata else ()):
        base_path = os.path.join(appdata, base_rel)
        for sd in subdirs:
            _scan_dir_for_profiles(os.path.join(base_path, sd), already_imported, imported, slicer_hint=slicer,
                                    type_hint=SLICER_SUBDIR_TYPE_HINTS.get(sd))

    for slicer, (base_rel, subdirs) in (SLICER_VERSIONED_USER_DIRS.items() if appdata else ()):
        _scan_versioned_user_dir(os.path.join(appdata, base_rel), subdirs, already_imported, imported, slicer_hint=slicer)

    for slicer, folder_name in (SLICER_CURA_FAMILY_DIRS.items() if appdata else ()):
        family_base = os.path.join(appdata, folder_name)
        if not os.path.isdir(family_base):
            continue
        try:
            versions = os.listdir(family_base)
        except Exception as e:
            versions = []
            app_logger.debug(f"[SlicerProfiles] Dossier {folder_name} illisible: {e}")
        for entry in versions:
            versioned = os.path.join(family_base, entry)
            if os.path.isdir(versioned):
                _scan_dir_for_profiles(os.path.join(versioned, 'quality_changes'), already_imported, imported, slicer_hint=slicer,
                                        type_hint='process')
                _scan_dir_for_profiles(os.path.join(versioned, 'user'), already_imported, imported, slicer_hint=slicer)

    if appdata:
        _scan_creality_print_dir(os.path.join(appdata, 'Creality', 'Creality Print'), already_imported, imported)

    if watch_dir:
        _scan_watch_dir_for_profiles(watch_dir, already_imported, imported)

    seen_cura_keys = set()
    deduped = []
    for p in imported:
        if p.get('slicer') == 'cura':
            key = (p.get('name', '').strip().lower(), p.get('profile_type'))
            if key in seen_cura_keys:
                continue
            seen_cura_keys.add(key)
        deduped.append(p)
    imported = deduped

    if imported:
        _apply_printer_autoguess(imported, user_id)
        profiles.extend(imported)
        save_slicer_profiles(profiles)
        app_logger.info(f"[SlicerProfiles] {len(imported)} profil(s) importé(s) automatiquement (tous slicers)")

    return imported

_profile_sync_lock = threading.Lock()

_profile_sync_last = 0.0

PROFILE_SYNC_MIN_INTERVAL = 15  

def _sync_slicer_profiles(user_id, force=False):
    global _profile_sync_last
    result = {'updated': 0, 'imported': 0}
    if user_id is None:
        return result
    now = time.time()
    if not _profile_sync_lock.acquire(blocking=False):
        return result   
    try:
        if not force and now - _profile_sync_last < PROFILE_SYNC_MIN_INTERVAL:
            return result
        _profile_sync_last = now
        profiles = load_slicer_profiles()
        updated, _errors = _refresh_stale_slicer_profiles(profiles)
        imported = _autodetect_new_slicer_profiles(profiles, user_id)
        result = {'updated': updated, 'imported': len(imported)}
        if updated or imported:
            app_logger.info(f"[SlicerProfiles] Synchronisation : {updated} actualisé(s), {len(imported)} importé(s)")
    except Exception as e:
        app_logger.warning(f"[SlicerProfiles] Synchronisation impossible : {e}")
    finally:
        _profile_sync_lock.release()
    return result

def _startup_sync_slicer_profiles():
    try:
        _sync_slicer_profiles(_get_primary_user_id(), force=True)
    except Exception as e:
        app_logger.debug(f"[SlicerProfiles] Synchronisation au démarrage ignorée : {e}")

def api_slicer_profiles_autodetect():
    try:
        profiles = load_slicer_profiles()
        if not os.environ.get('APPDATA') and not _get_profiles_watch_dir():
            return jsonify({"error": "Aucun dossier de slicer à analyser : la détection automatique lit les dossiers du slicer sous Windows. Importez vos fichiers de profils ou indiquez un dossier de profils surveillé.", "code": "no_source"}), 400
        imported = _autodetect_new_slicer_profiles(profiles, session['user_id'])
        return jsonify({"imported": imported, "count": len(imported), "profiles": profiles}), 200
    except Exception as e:
        app_logger.error(f"[SlicerProfiles] Auto-détection échouée: {e}", exc_info=True)
        return jsonify({"error": f"Échec de la détection automatique : {e}"}), 500


_ROUTES = (
    ('/api/slicer-profiles', ['GET'], 'api_slicer_profiles_list', ('login_required', )),
    ('/api/slicer-profiles/import', ['POST'], 'api_slicer_profiles_import', ('login_required', )),
    ('/api/slicer-profiles/import-json', ['POST'], 'api_slicer_profiles_import_json', ('login_required', )),
    ('/api/slicer-profiles/<profile_id>/printer', ['PATCH'], 'api_slicer_profiles_assign_printer', ('login_required', )),
    ('/api/slicer-profiles/<profile_id>/type', ['PATCH'], 'api_slicer_profiles_assign_type', ('login_required', )),
    ('/api/slicer-profiles/<profile_id>', ['DELETE'], 'api_slicer_profiles_delete', ('login_required', )),
    ('/api/slicer-profiles/refresh', ['POST'], 'api_slicer_profiles_refresh', ('login_required', )),
    ('/api/slicer-profiles/auto-detect', ['POST'], 'api_slicer_profiles_autodetect', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"slicer_profiles.init : services manquants : {missing}")
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
