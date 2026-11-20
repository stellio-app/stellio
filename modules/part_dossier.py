"""Stellio — fiche pièce (1.1.7) : tout ce que Stellio sait d'un modèle, sur une seule page.

Une pièce n'est plus « un fichier » : c'est son origine (auteur, source, licence et échéance), ses versions, ses impressions
(version utilisée, profil de slicer, résultat, imprimante), la meilleure combinaison version + profil, les G-code archivés et les photos
du résultat. Ce module ne stocke rien : il ASSEMBLE, en lecture seule, ce que les autres modules (versions, traçabilité, archives
G-code, licences) ont déjà enregistré. Une seule route : `GET /api/part-dossier?path=…`.
Chaque section est indépendante : si une table manque (instance neuve) la section est simplement vide.
"""
import os

_REQUIRED = (
    '_is_path_within_sources',
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'session',
)
_OPTIONAL = ()
_OVERRIDABLE = ('os',)

_MAIN = {}
_is_path_within_sources = None
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None


def _norm(p):
    return str(p or '').strip().replace('\\', '/')


def _native(p):
    return p.replace('/', os.sep) if os.sep != '/' else p


def _q(conn, sql, params=()):
    """Lecture tolérante : une table absente donne une liste vide au lieu d'une erreur."""
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    except Exception:
        return []


def build(conn, uid, path, native):
    """Assemble la fiche d'un modèle (fonction testable : reçoit la connexion)."""
    out = {'path': path, 'name': os.path.basename(path), 'ext': os.path.splitext(path)[1].lower()}
    try:
        out['size'] = os.path.getsize(native)
        out['exists'] = True
    except OSError:
        out['size'], out['exists'] = None, False
    # origine et licence
    o = _q(conn, "SELECT * FROM file_origins WHERE file_path = ? AND user_id = ?", (path, uid))
    origin = o[0] if o else {}
    lic = {'license': origin.get('license') or '', 'author': origin.get('author') or '', 'source_url': origin.get('source_url') or '',
           'platform': origin.get('platform') or '', 'notes': origin.get('notes') or '', 'expires': str(origin.get('license_expires') or '')[:10],
           'status': '', 'days_left': None}
    if lic['expires']:
        try:
            from modules import license_watch
            lic['status'], lic['days_left'] = license_watch.classify(lic['expires'])
        except Exception:
            pass
    out['origin'] = lic
    # versions
    vers = _q(conn, "SELECT id, version, note, auto, created_at, size FROM model_versions WHERE path = ? ORDER BY version DESC", (path,))
    for v in vers:
        v['auto'] = bool(v['auto'])
    # impressions rattachées (traçabilité) + meilleure combinaison
    rows = _q(conn, "SELECT t.history_id, t.model_version, t.profile_fp, h.result, h.slicer_profile_name AS profile, h.sent_at, h.printer_id, "
                    "h.spool_id, h.filament_material, h.actual_seconds FROM print_trace t JOIN print_history h ON h.id = t.history_id "
                    "WHERE t.user_id = ? AND h.user_id = ? AND t.model_path = ? ORDER BY h.sent_at DESC", (uid, uid, path))
    printers = {r['id']: r['name'] for r in _q(conn, "SELECT id, name FROM printers")}
    for r in rows:
        r['printer'] = printers.get(r.pop('printer_id', None)) or ''
    for v in vers:
        mine = [r for r in rows if r['model_version'] == v['version']]
        v['prints'] = len(mine)
        v['success'] = sum(1 for r in mine if r['result'] == 'success')
    out['versions'] = vers
    best = None
    try:
        from modules import print_traceability as pt
        best = pt.pick_best(pt.aggregate(_q(conn, "SELECT t.model_version, t.profile_fp, h.result, h.slicer_profile_name AS profile_name "
                                                 "FROM print_trace t JOIN print_history h ON h.id = t.history_id "
                                                 "WHERE t.user_id = ? AND h.user_id = ? AND t.model_path = ?", (uid, uid, path))))
    except Exception:
        best = None
    out['best'] = best
    out['prints'] = {'total': len(rows), 'success': sum(1 for r in rows if r['result'] == 'success'),
                     'failed': sum(1 for r in rows if r['result'] == 'failed'), 'recent': rows[:15]}
    # G-code archivés des impressions de ce modèle
    ids = [r['history_id'] for r in rows]
    gc = []
    if ids:
        gc = _q(conn, "SELECT history_id, name, raw_size, gz_size, sha256, created FROM gcode_archive WHERE user_id = ? AND history_id IN (%s)" % ','.join('?' * len(ids)),
                [uid] + ids)
    out['gcode'] = gc
    out['photos'] = _q(conn, "SELECT id, image_filename, note, created_at FROM print_photos WHERE user_id = ? AND file_path = ? ORDER BY id DESC LIMIT 12", (uid, path))
    return out


def api_part_dossier():
    path = _norm(request.args.get('path'))
    if not path:
        return jsonify({'error': 'path_required'}), 400
    uid = session['user_id']
    native = _native(path)
    if not _is_path_within_sources(native, uid):
        return jsonify({'error': 'forbidden'}), 403
    conn = get_db()
    try:
        return jsonify(build(conn, uid, path, native))
    finally:
        conn.close()


_ROUTES = (
    ('/api/part-dossier', ['GET'], 'api_part_dossier', ('login_required', )),
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
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {}
