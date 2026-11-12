"""Stellio — partage de profils de slicer entre instances Stellio

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `profile_share.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.

Envoi : `POST /api/slicer-profiles/<id>/send-to-instance` {instance_id} envoie le fichier d'origine du profil à une instance
appairée (même clé d'appairage que l'envoi de fichiers). Réception : `POST /api/peer/receive-profile`, protégé par la clé
d'appairage, qui n'accepte que des fichiers de profil (.json, .ini, .cfg, .orca_filament, .orca_printer) de 2 Mo au plus
et ignore un profil déjà présent (même nom, même slicer). Rien n'est exécuté : le fichier est seulement analysé comme profil.
"""
import base64
import os

_REQUIRED = (
    'IMPORTED_PROFILES_DIR',
    '_parse_slicer_profile_file',
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'load_slicer_profiles',
    'login_required',
    'request',
    'requests',
    'require_peer_key',
    'save_slicer_profiles',
    'secure_filename',
    'send_file',
    'session',
)
_OVERRIDABLE = ('base64', 'os')

_MAIN = {}
IMPORTED_PROFILES_DIR = None
_parse_slicer_profile_file = None
app = None
app_logger = None
get_db = None
jsonify = None
load_slicer_profiles = None
login_required = None
request = None
requests = None
require_peer_key = None
save_slicer_profiles = None
secure_filename = None
send_file = None
session = None

MAX_PROFILE_BYTES = 2_000_000
ALLOWED_EXT = ('.json', '.ini', '.cfg', '.orca_filament', '.orca_printer')


def _profile_file(profile):
    """Chemin du fichier d'origine d'un profil, uniquement s'il se trouve dans le dossier des profils importés."""
    path = profile.get('source_path') or ''
    if not path or not os.path.isfile(path):
        return None
    try:
        root = os.path.realpath(IMPORTED_PROFILES_DIR)
        real = os.path.realpath(path)
        if os.path.commonpath([root, real]) != root:
            return None
    except (ValueError, TypeError):
        return None
    return real


def _find(profile_id):
    return next((p for p in load_slicer_profiles() if p.get('id') == profile_id), None)


def api_profile_export(profile_id):
    """Télécharge le fichier d'origine d'un profil (partage à la main, par exemple par e-mail)."""
    profile = _find(profile_id)
    path = _profile_file(profile) if profile else None
    if not path:
        return jsonify({'error': 'Fichier du profil introuvable'}), 404
    name = profile.get('source_filename') or os.path.basename(path)
    return send_file(path, as_attachment=True, download_name=secure_filename(name) or 'profil.json')


def api_profile_send(profile_id):
    data = request.get_json(silent=True) or {}
    try:
        instance_id = int(data.get('instance_id'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'instance_required'}), 400
    profile = _find(profile_id)
    if not profile:
        return jsonify({'success': False, 'error': 'profile_not_found'}), 404
    path = _profile_file(profile)
    if not path:
        return jsonify({'success': False, 'error': 'no_source_file'}), 404
    filename = secure_filename(profile.get('source_filename') or os.path.basename(path)) or 'profil.json'
    if not filename.lower().endswith(ALLOWED_EXT):
        return jsonify({'success': False, 'error': 'unsupported_type'}), 400
    with open(path, 'rb') as f:
        blob = f.read(MAX_PROFILE_BYTES + 1)
    if len(blob) > MAX_PROFILE_BYTES:
        return jsonify({'success': False, 'error': 'too_large'}), 413
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM remote_instances WHERE id=? AND user_id=?", (instance_id, session['user_id'])).fetchone()
    finally:
        conn.close()
    if not row:
        return jsonify({'success': False, 'error': 'instance_not_found'}), 404
    try:
        r = requests.post(f"{row['url']}/api/peer/receive-profile", timeout=20,
                          headers={'X-Stellio-Peer-Key': row['peer_key']},
                          json={'filename': filename, 'content_b64': base64.b64encode(blob).decode('ascii'),
                                'name': profile.get('name') or ''})
    except Exception as e:
        app_logger.warning(f"[ProfilShare] Envoi vers '{row['name']}' échoué : {e}")
        return jsonify({'success': False, 'error': 'unreachable'}), 503
    if r.status_code == 403:
        return jsonify({'success': False, 'error': 'peer_key_refused'}), 502
    try:
        body = r.json() or {}
    except Exception:
        body = {}
    if not r.ok:
        return jsonify({'success': False, 'error': body.get('error') or f'http_{r.status_code}'}), 502
    app_logger.info(f"[ProfilShare] Profil '{profile.get('name')}' envoyé vers '{row['name']}'")
    return jsonify({'success': True, 'already_present': bool(body.get('already_present'))})


def api_peer_receive_profile():
    data = request.get_json(silent=True) or {}
    filename = secure_filename(str(data.get('filename') or '')) or ''
    if not filename.lower().endswith(ALLOWED_EXT):
        return jsonify({'error': 'Type de fichier non accepté'}), 400
    try:
        blob = base64.b64decode(str(data.get('content_b64') or ''), validate=True)
    except Exception:
        return jsonify({'error': 'Contenu invalide'}), 400
    if not blob or len(blob) > MAX_PROFILE_BYTES:
        return jsonify({'error': 'Fichier vide ou trop volumineux'}), 413
    try:
        new_profiles = _parse_slicer_profile_file(filename, blob)
    except Exception as e:
        return jsonify({'error': f'Profil non reconnu : {e}'}), 400
    if not new_profiles:
        return jsonify({'error': 'Profil non reconnu'}), 400
    existing = load_slicer_profiles()
    have = {(str(p.get('name') or '').strip().lower(), p.get('slicer')) for p in existing}
    fresh = [p for p in new_profiles if (str(p.get('name') or '').strip().lower(), p.get('slicer')) not in have]
    if not fresh:
        return jsonify({'success': True, 'already_present': True, 'imported': 0})
    existing.extend(fresh)
    save_slicer_profiles(existing)
    app_logger.info(f"[ProfilShare] {len(fresh)} profil(s) reçu(s) d'une instance appairée")
    return jsonify({'success': True, 'already_present': False, 'imported': len(fresh)})


_ROUTES = (
    ('/api/slicer-profiles/<profile_id>/export', ['GET'], 'api_profile_export', ('login_required', )),
    ('/api/slicer-profiles/<profile_id>/send-to-instance', ['POST'], 'api_profile_send', ('login_required', )),
    ('/api/peer/receive-profile', ['POST'], 'api_peer_receive_profile', ('require_peer_key', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"profile_share.init : services manquants : {missing}")
    for n in _REQUIRED + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {}
