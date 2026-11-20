"""Stellio — version allégée d'un STL volumineux (1.1.7).

Un STL géant (plusieurs Go) ne peut pas être chargé en entier sans saturer la mémoire : réparation, diff 3D, indexation… sont refusés.
Ce module écrit, À CÔTÉ de l'original, une copie simplifiée (regroupement de sommets par cellules, par morceaux : la mémoire ne dépend pas de
la taille du fichier). L'original n'est JAMAIS modifié ni remplacé. La copie est approximative : elle sert à regarder, mesurer, réparer, indexer ;
pour imprimer à pleine résolution il faut garder l'original.

POST /api/files/lighten {path, faces?} → 202 {job_id} ; le résultat de la tâche donne le chemin et les chiffres avant/après.
STL binaires ET texte (ASCII) locaux ; un partage réseau est refusé avec un message clair.
"""
import os

_REQUIRED = (
    '_is_path_within_sources',
    'app',
    'app_logger',
    'jsonify',
    'login_required',
    'request',
    'session',
)
_OPTIONAL = ('invalidate_cache',)
_OVERRIDABLE = ()

_MAIN = {}
_is_path_within_sources = None
app = None
app_logger = None
invalidate_cache = None
jsonify = None
login_required = None
request = None
session = None

DEFAULT_FACES = 300_000
MIN_FACES = 20_000
MAX_FACES = 2_000_000
SUFFIX = ' (allégé)'


def _is_local(path):
    p = str(path or '')
    return not (p.startswith('//') or p.startswith('\\\\') or '::' in p)


def target_path(src, taken=os.path.exists):
    """`<nom> (allégé).stl` dans le dossier de l'original ; ` 2`, ` 3`… si le nom est pris. Ne remplace jamais un fichier."""
    folder, base = os.path.split(src)
    stem = os.path.splitext(base)[0]
    cand = os.path.join(folder, f'{stem}{SUFFIX}.stl')
    n = 2
    while taken(cand):
        cand = os.path.join(folder, f'{stem}{SUFFIX} {n}.stl')
        n += 1
    return cand


def lighten(ctx, uid, path, faces):
    """Tâche de fond : lit l'original par morceaux, écrit la copie simplifiée (fichier temporaire puis renommage)."""
    main = _MAIN
    ctx.progress(0, 3, os.path.basename(path))
    mesh = main['stl_cluster_decimate'](path, target_faces=faces)
    ctx.check()
    before = int(mesh.metadata.get('stellio_decimated_from') or 0)
    if len(mesh.faces) == 0:
        raise ValueError('La simplification n\'a laissé aucun triangle.')
    ctx.progress(1, 3, 'écriture')
    out = target_path(path)
    tmp = out + '.part'
    try:
        with open(tmp, 'wb') as fh:
            mesh.export(file_obj=fh, file_type='stl')
        os.replace(tmp, out)
    finally:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass
    ctx.progress(2, 3, 'bibliothèque')
    if invalidate_cache:
        try:
            invalidate_cache()
        except Exception:
            pass
    app_logger.info(f"[LIGHTEN] {os.path.basename(path)} → {os.path.basename(out)} ({before} → {len(mesh.faces)} triangles)")
    return {'path': out, 'name': os.path.basename(out), 'triangles_before': before, 'triangles_after': int(len(mesh.faces)),
            'size_before': os.path.getsize(path), 'size_after': os.path.getsize(out)}


def api_lighten():
    if session.get('role') == 'viewer':
        return jsonify({'error': 'Réservé au compte propriétaire.', 'code': 'viewer_forbidden'}), 403
    data = request.get_json(silent=True) or {}
    path = str(data.get('path') or '')
    if not path or not os.path.isfile(path):
        return jsonify({'error': 'Fichier non trouvé.'}), 404
    uid = session['user_id']
    if not _is_path_within_sources(path, uid):
        return jsonify({'error': "Ce fichier n'appartient à aucune source configurée."}), 403
    if os.path.splitext(path)[1].lower() != '.stl':
        return jsonify({'error': 'Seuls les fichiers STL peuvent être allégés.', 'code': 'not_stl'}), 422
    if not _is_local(path):
        return jsonify({'error': 'Copiez d\'abord le fichier en local : un partage réseau ne peut pas être allégé directement.', 'code': 'not_local'}), 422
    try:
        faces = int(data.get('faces') or DEFAULT_FACES)
    except (TypeError, ValueError):
        faces = DEFAULT_FACES
    faces = max(MIN_FACES, min(MAX_FACES, faces))
    try:
        if _MAIN['_stl_binary_count'](path) is None and not _MAIN['_stl_is_ascii'](path):
            return jsonify({'error': 'Fichier STL invalide : ni binaire ni texte lisible.', 'code': 'not_binary'}), 422
    except Exception:
        return jsonify({'error': 'Fichier illisible.', 'code': 'unreadable'}), 422
    try:
        from modules import job_manager
        job = job_manager.submit('Version allégée', lighten, owner=uid, kind='lighten', args=(uid, path, faces))
    except ImportError:
        return jsonify({'error': 'Gestionnaire de tâches indisponible.'}), 503
    return jsonify({'job_id': job.id, 'target': target_path(path), 'faces': faces}), 202


_ROUTES = (
    ('/api/files/lighten', ['POST'], 'api_lighten', ('login_required', )),
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
