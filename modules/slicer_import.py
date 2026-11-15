"""Stellio — Profils de slicer : lecture, normalisation, import (base de slicer_profiles)

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `slicer_import.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import datetime
import difflib
import io
import json
import os
import re
import secrets
import zipfile

_REQUIRED = (
    'DATA_DIR',
    'IMPORTED_PROFILES_DIR',
    'IS_SERVER_EDITION',
    'app_logger',
    'get_db',
    'load_settings',
    'parse_printer_config',
)
_OPTIONAL = ()   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('datetime', 'difflib', 'io', 'json', 'os', 're', 'secrets', 'zipfile', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
DATA_DIR = None
IMPORTED_PROFILES_DIR = None
IS_SERVER_EDITION = None
app_logger = None
get_db = None
load_settings = None
parse_printer_config = None


SLICER_PROFILES_FILE = None
_slicer_profiles_cache = None

def load_slicer_profiles():
    global _slicer_profiles_cache
    if _slicer_profiles_cache is None:
        try:
            with open(SLICER_PROFILES_FILE, 'r', encoding='utf-8') as f:
                _slicer_profiles_cache = json.load(f)
        except Exception:
            _slicer_profiles_cache = []
    return _slicer_profiles_cache

def save_slicer_profiles(profiles):
    global _slicer_profiles_cache
    _slicer_profiles_cache = profiles
    with open(SLICER_PROFILES_FILE, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)

def _parse_kv_text(content):
    kv = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or line.startswith(';') or line.startswith('['):
            continue
        if '=' not in line:
            continue
        key, _, value = line.partition('=')
        kv[key.strip().lower()] = value.strip().strip('"')
    return kv

def _first_num(value):
    if value is None:
        return None
    m = re.search(r'-?\d+(?:\.\d+)?', str(value))
    return float(m.group()) if m else None

def _first_str(value):
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        value = value[0] if value else None
        if value is None:
            return None
    s = str(value).split(',')[0].strip().strip('"').strip("'")
    return s or None

def _to_bool(value):
    if value is None:
        return None
    s = str(value).strip().lower()
    if s in ('1', 'true', 'yes', 'on'):
        return True
    if s in ('0', 'false', 'no', 'off'):
        return False
    return None

def _pick(d, keys):
    for k in keys:
        if k in d and d[k] not in (None, ''):
            return d[k]
    return None

def _extract_compatible_printers(raw):
    val = raw.get('compatible_printers')
    if not val:
        return []
    if isinstance(val, list):
        items = val
    else:
        s = str(val)
        sep = ';' if ';' in s else (',' if ',' in s else None)
        items = s.split(sep) if sep else [s]
    return [str(v).strip().strip('"') for v in items if str(v).strip()]

def _extract_printer_from_label(label):
    if not label or '@' not in label:
        return []
    suffix = label.split('@', 1)[1].strip()
    return [suffix] if suffix else []

def _extract_printer_from_prefix(label):
    if not label or ' - ' not in label:
        return []
    prefix = label.split(' - ', 1)[0].strip()
    return [prefix] if prefix else []

def _guess_compatible_printer_names(raw, name, source_filename):
    names = _extract_compatible_printers(raw)
    if names:
        return names

    ptype = str(raw.get('type') or '').strip().lower()

    if ptype in ('machine', 'printer'):
        label = (name or source_filename or '').split('@', 1)[0].strip()
        return [label] if label else []

    names = _extract_printer_from_label(name) or _extract_printer_from_label(source_filename)
    if names:
        return names

    return _extract_printer_from_prefix(name) or _extract_printer_from_prefix(source_filename)

def _classify_profile_type(raw, hint=None):
    ptype = str(raw.get('type') or '').strip().lower()
    if ptype in ('machine', 'printer'):
        return 'printer'
    if ptype == 'filament':
        return 'filament'
    if ptype in ('process', 'print'):
        return 'process'
    if hint in ('printer', 'filament', 'process'):
        return hint
    if raw.get('filament_type') or raw.get('material_type') or raw.get('material'):
        return 'filament'
    has_nozzle_temp = _pick(raw, ['temperature', 'first_layer_temperature',
                                   'material_print_temperature', 'nozzle_temperature']) not in (None, '')
    if has_nozzle_temp:
        return 'filament'
    has_printer_only_keys = any(
        raw.get(k) not in (None, '')
        for k in ('bed_shape', 'retract_length', 'max_print_height', 'printer_technology',
                  'gcode_flavor', 'machine_max_acceleration_x', 'z_offset', 'nozzle_diameter')
    )
    if has_printer_only_keys:
        return 'printer'
    return 'process'

def _guess_material_type(name, raw_material):
    if raw_material:
        return str(raw_material).strip()
    if not name:
        return None
    name_lower = str(name).lower()
    materials = ['pla', 'petg', 'abs', 'tpu', 'asa', 'nylon', 'pc', 'hips', 'pva']
    for mat in materials:
        if mat in name_lower:
            return mat.upper()
    return None

def _normalize_profile(raw, slicer, name, source_filename, source_path=None, type_hint=None):
    def g(*keys):
        return _pick(raw, list(keys))

    wall_count   = _first_num(g('perimeters', 'wall_line_count', 'wall_loops'))
    top_layers   = _first_num(g('top_solid_layers', 'top_layers', 'top_shell_layers'))
    bottom_layers = _first_num(g('bottom_solid_layers', 'bottom_layers', 'bottom_shell_layers'))

    compatible_printers = _guess_compatible_printer_names(raw, name, source_filename)

    raw_material = _first_str(g('filament_type', 'material_type', 'material'))
    guessed_material = _guess_material_type(name, raw_material)

    return {
        "id": secrets.token_hex(8),
        "name": (name or source_filename or "Profil").strip(),
        "slicer": slicer,
        "source_filename": source_filename,
        "source_path": source_path,
        "source_mtime": (lambda: (os.path.getmtime(source_path) if source_path and os.path.isfile(source_path) else None))(),
        "imported_at": datetime.datetime.now().isoformat(timespec='seconds'),
        "printer_id": None,
        "printer_match_confirmed": False,
        "profile_type": _classify_profile_type(raw, hint=type_hint),
        "compatible_printers": compatible_printers,
        "layer_height": _first_num(g('layer_height')),
        "nozzle_diameter": _first_num(g('nozzle_diameter')),
        "material_type": guessed_material,
        "infill_density": _first_num(g('fill_density', 'infill_sparse_density', 'sparse_infill_density')),
        "infill_pattern": _first_str(g('fill_pattern', 'infill_pattern', 'sparse_infill_pattern')),
        "wall_count": int(wall_count) if wall_count is not None else None,
        "top_layers": int(top_layers) if top_layers is not None else None,
        "bottom_layers": int(bottom_layers) if bottom_layers is not None else None,
        "supports_enabled": _to_bool(g('support_material', 'support_enable', 'enable_support')),
        "print_speed": _first_num(g('perimeter_speed', 'speed_print', 'outer_wall_speed')),
        "nozzle_temp": _first_num(g('temperature', 'material_print_temperature', 'nozzle_temperature')),
        "bed_temp": _first_num(g('bed_temperature', 'material_bed_temperature', 'hot_plate_temp')),
    }

def _persist_profile_bytes(content_bytes, suggested_name):
    safe_base = re.sub(r'[^A-Za-z0-9._-]+', '_', os.path.basename(suggested_name or 'profil'))[:80] or 'profil'
    unique_name = f"{secrets.token_hex(6)}_{safe_base}"
    dest_path = os.path.join(IMPORTED_PROFILES_DIR, unique_name)
    try:
        with open(dest_path, 'wb') as f:
            f.write(content_bytes)
        return dest_path
    except Exception as e:
        app_logger.debug(f"[SlicerProfiles] Impossible de persister le profil {suggested_name}: {e}")
        return None

def _parse_zip_bundle(filename, content_bytes, slicer_hint, type_hint=None):
    try:
        zf = zipfile.ZipFile(io.BytesIO(content_bytes))
    except Exception as e:
        raise ValueError(f"Archive invalide : {e}")

    profiles = []
    json_marker_keys = ('layer_height', 'fill_density', 'sparse_infill_density',
                         'filament_type', 'nozzle_diameter', 'nozzle_temperature')

    for entry_name in zf.namelist():
        base = os.path.basename(entry_name)
        low = entry_name.lower()
        if not base:
            continue

        if low.endswith('.json'):
            try:
                entry_bytes = zf.read(entry_name)
                raw = json.loads(entry_bytes.decode('utf-8-sig', errors='ignore'))
            except Exception:
                continue
            if not isinstance(raw, dict):
                continue
            raw_lower = {str(k).lower(): v for k, v in raw.items()}
            if not any(k in raw_lower for k in json_marker_keys):
                continue
            name = raw.get('name') or os.path.splitext(base)[0]
            source_path = _persist_profile_bytes(entry_bytes, base)
            profiles.append(_normalize_profile(raw_lower, slicer_hint or 'orcaslicer', name, f"{filename}::{base}", source_path=source_path, type_hint=type_hint))

        elif low.endswith('.cfg'):
            try:
                entry_bytes = zf.read(entry_name)
                text = entry_bytes.decode('utf-8-sig', errors='ignore')
            except Exception:
                continue
            raw = _parse_kv_text(text)
            if not raw:
                continue
            name = raw.get('name') or os.path.splitext(base.replace('.inst', ''))[0]
            source_path = _persist_profile_bytes(entry_bytes, base)
            profiles.append(_normalize_profile(raw, slicer_hint or 'cura', name, f"{filename}::{base}", source_path=source_path, type_hint=type_hint))

    if not profiles:
        raise ValueError("Aucun profil exploitable trouvé dans cette archive")
    return profiles

SLICER_ZIP_EXTENSIONS = {
    'orca_filament': 'orcaslicer',
    'orca_printer': 'orcaslicer',
    'orca_process': 'orcaslicer',
    'bbscfg': 'bambustudio',
    'bbsflmt': 'bambustudio',
    'curaprofile': 'cura',
    'zip': None,
}

SLICER_EXT_TYPE_HINTS = {
    'orca_filament': 'filament',
    'orca_printer': 'printer',
    'orca_process': 'process',
    'bbscfg': 'process',
    'bbsflmt': 'filament',
}

SLICER_SUBDIR_TYPE_HINTS = {
    'process': 'process',
    'print': 'process',
    'filament': 'filament',
    'machine': 'printer',
    'printer': 'printer',
}

def _parse_slicer_profile_file(filename, content_bytes, slicer_hint=None, source_path=None, type_hint=None):
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    base_name = os.path.splitext(os.path.basename(filename))[0]
    resolved_type_hint = type_hint or SLICER_EXT_TYPE_HINTS.get(ext)

    if ext in SLICER_ZIP_EXTENSIONS:
        return _parse_zip_bundle(filename, content_bytes, SLICER_ZIP_EXTENSIONS[ext] or slicer_hint, type_hint=resolved_type_hint)

    try:
        text = content_bytes.decode('utf-8-sig')
    except Exception:
        text = content_bytes.decode('latin-1', errors='ignore')

    resolved_path = source_path or _persist_profile_bytes(content_bytes, filename)

    if ext == 'json':
        try:
            raw = json.loads(text)
        except Exception as e:
            raise ValueError(f"JSON invalide : {e}")
        if not isinstance(raw, dict):
            raise ValueError("Format JSON inattendu")
        name = raw.get('name') or base_name
        raw_lower = {str(k).lower(): v for k, v in raw.items()}
        return [_normalize_profile(raw_lower, slicer_hint or 'orcaslicer', name, filename, source_path=resolved_path, type_hint=resolved_type_hint)]

    if ext in ('ini', 'cfg'):
        raw = _parse_kv_text(text)
        if not raw:
            raise ValueError("Aucun paramètre reconnu dans ce fichier")
        if slicer_hint:
            slicer = slicer_hint
        else:
            is_cura = 'wall_line_count' in raw or 'infill_sparse_density' in raw or '[general]' in text.lower()
            slicer = 'cura' if is_cura else 'prusaslicer'
        name = raw.get('name') or base_name
        return [_normalize_profile(raw, slicer, name, filename, source_path=resolved_path, type_hint=resolved_type_hint)]

    raise ValueError(f"Extension non supportée : .{ext} (attendu : .ini, .json, .cfg, .orca_filament, .orca_printer ou .zip)")

def _guess_printer_for_profile(compatible_names, printers):
    if not compatible_names or not printers:
        return None, False

    compat_lower = [c.lower() for c in compatible_names]

    for p in printers:
        aliases = [a.lower() for a in (p.get('config') or {}).get('slicer_profile_aliases', [])]
        if any(c in aliases for c in compat_lower):
            return p['id'], True

    best_id, best_score = None, 0.0
    for p in printers:
        pname = (p.get('name') or '').lower().strip()
        if not pname:
            continue
        for c in compat_lower:
            score = 0.92 if (pname in c or c in pname) else difflib.SequenceMatcher(None, pname, c).ratio()
            if score > best_score:
                best_score, best_id = score, p['id']

    return (best_id, False) if best_id and best_score >= 0.55 else (None, False)

def _apply_printer_autoguess(profiles_subset, user_id):
    try:
        conn = get_db()
        try:
            rows = conn.execute("SELECT * FROM printers WHERE user_id = ?", (user_id,)).fetchall()
        finally:
            conn.close()
        printers = [parse_printer_config(r) for r in rows]
    except Exception as e:
        app_logger.debug(f"[SlicerProfiles] Impossible de charger les imprimantes pour l'auto-assignation: {e}")
        return
    for prof in profiles_subset:
        if prof.get('printer_id'):
            continue
        pid, confirmed = _guess_printer_for_profile(prof.get('compatible_printers') or [], printers)
        if pid:
            prof['printer_id'] = pid
            prof['printer_match_confirmed'] = confirmed

def _remember_printer_alias(printer_id, user_id, names):
    if not printer_id or not names:
        return
    try:
        conn = get_db()
        row = conn.execute(
            "SELECT config FROM printers WHERE id = ? AND user_id = ?", (printer_id, user_id)
        ).fetchone()
        if not row:
            conn.close()
            return
        try:
            config = json.loads(row['config'] or '{}')
        except Exception:
            config = {}
        existing = config.get('slicer_profile_aliases', [])
        existing_lower = {a.lower() for a in existing}
        changed = False
        for name in names:
            if name and name.lower() not in existing_lower:
                existing.append(name)
                existing_lower.add(name.lower())
                changed = True
        if changed:
            config['slicer_profile_aliases'] = existing
            conn.execute("UPDATE printers SET config = ? WHERE id = ?", (json.dumps(config), printer_id))
            conn.commit()
        conn.close()
    except Exception as e:
        app_logger.debug(f"[SlicerProfiles] Échec mémorisation alias imprimante: {e}")

SLICER_PROFILE_MAX_BYTES = 25 * 1024 * 1024

SLICER_WATCH_DIR_MAX_DEPTH = 4

SLICER_WATCH_DIR_MAX_DIRS = 400

def _get_profiles_watch_dir():
    """Dossier de profils surveillé (réglage `slicer_profiles_watch_dir`), ou '' s'il n'est pas défini / introuvable."""
    if not IS_SERVER_EDITION:
        return ''
    try:
        d = str((load_settings() or {}).get('slicer_profiles_watch_dir') or '').strip()
    except Exception:
        return ''
    return d if d and os.path.isdir(d) else ''

def _scan_watch_dir_for_profiles(root, already_imported, imported_out):
    """Parcourt le dossier surveillé (sous-dossiers compris, profondeur et nombre de dossiers limités, liens
    symboliques ignorés). Lecture seule : les fichiers ne sont jamais modifiés. Le nom du sous-dossier
    (process / filament / machine…) sert d'indice de type, comme dans le dossier utilisateur d'OrcaSlicer."""
    root = os.path.abspath(root)
    visited = 0
    for dirpath, dirnames, _files in os.walk(root, followlinks=False):
        visited += 1
        if visited > SLICER_WATCH_DIR_MAX_DIRS:
            app_logger.warning(f"[SlicerProfiles] Dossier surveillé : limite de {SLICER_WATCH_DIR_MAX_DIRS} dossiers atteinte")
            break
        depth = os.path.relpath(dirpath, root).count(os.sep) + (0 if dirpath == root else 1)
        dirnames[:] = [d for d in dirnames if not d.startswith('.')] if depth < SLICER_WATCH_DIR_MAX_DEPTH else []
        _scan_dir_for_profiles(dirpath, already_imported, imported_out,
                               type_hint=SLICER_SUBDIR_TYPE_HINTS.get(os.path.basename(dirpath).lower()),
                               max_bytes=SLICER_PROFILE_MAX_BYTES)

def _scan_dir_for_profiles(dir_path, already_imported, imported_out, slicer_hint=None, type_hint=None, max_bytes=None):
    if not dir_path or not os.path.isdir(dir_path):
        return
    try:
        entries = os.listdir(dir_path)
    except Exception as e:
        app_logger.debug(f"[SlicerProfiles] Dossier illisible {dir_path}: {e}")
        return
    for fname in entries:
        if fname in already_imported:
            continue
        ext = os.path.splitext(fname)[1].lower()
        if ext not in ('.ini', '.json', '.cfg', '.orca_filament', '.orca_printer', '.orca_process',
                       '.bbscfg', '.bbsflmt', '.curaprofile', '.zip'):
            continue
        fpath = os.path.join(dir_path, fname)
        try:
            if not os.path.isfile(fpath):
                continue
            if max_bytes and os.path.getsize(fpath) > max_bytes:
                app_logger.debug(f"[SlicerProfiles] Ignoré (trop volumineux) {fpath}")
                continue
            with open(fpath, 'rb') as f:
                content = f.read()


            new_profiles = _parse_slicer_profile_file(fname, content, slicer_hint=slicer_hint, source_path=fpath, type_hint=type_hint)
            imported_out.extend(new_profiles)
            already_imported.add(fname)
        except Exception as e:
            app_logger.debug(f"[SlicerProfiles] Ignoré {fpath}: {e}")

def _refresh_stale_slicer_profiles(profiles):
    updated_count = 0
    errors = []
    for p in profiles:
        source_path = p.get('source_path')
        if not source_path or not os.path.isfile(source_path):
            continue
        try:
            if os.path.commonpath([os.path.normpath(source_path), os.path.normpath(IMPORTED_PROFILES_DIR)]) == os.path.normpath(IMPORTED_PROFILES_DIR):
                continue  
        except ValueError:
            pass  

        try:
            current_mtime = os.path.getmtime(source_path)
        except OSError:
            continue
        if p.get('source_mtime') is not None and abs(current_mtime - p['source_mtime']) < 1:
            continue  

        try:
            with open(source_path, 'rb') as f:
                content = f.read()
            fresh_versions = _parse_slicer_profile_file(
                os.path.basename(source_path), content,
                slicer_hint=p.get('slicer'), source_path=source_path,
                type_hint=p.get('profile_type')
            )
            if not fresh_versions:
                continue
            fresh = fresh_versions[0]
            for key in ('name', 'layer_height', 'nozzle_diameter', 'material_type', 'infill_density',
                        'infill_pattern', 'wall_count', 'top_layers', 'bottom_layers',
                        'supports_enabled', 'print_speed', 'nozzle_temp', 'bed_temp'):
                if fresh.get(key) is not None:
                    p[key] = fresh[key]
            p['source_mtime'] = current_mtime
            p['last_synced_at'] = datetime.datetime.now().isoformat(timespec='seconds')
            updated_count += 1
        except Exception as e:
            errors.append({'profile': p.get('name'), 'error': str(e)})
            app_logger.debug(f"[SlicerProfiles] Rafraîchissement échoué pour {p.get('name')}: {e}")

    if updated_count:
        save_slicer_profiles(profiles)
    return updated_count, errors


_ROUTES = (
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"slicer_import.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    g['SLICER_PROFILES_FILE'] = os.path.join(DATA_DIR, "slicer_profiles.json")
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {'SLICER_PROFILES_FILE': g['SLICER_PROFILES_FILE']}
