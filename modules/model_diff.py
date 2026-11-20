"""Stellio — diff 3D visuel entre deux versions d'un modèle (1.1.7).

Compare deux maillages sans dépendance lourde : on échantillonne la surface de chacun (points répartis selon l'aire), puis on mesure,
pour chaque point, la distance au point le plus proche de l'autre maillage. Un point de B plus loin que la tolérance de tout point de A est
« ajouté » ; un point de A plus loin que la tolérance de tout point de B est « retiré ». Résultat : métriques (dimensions, volume, triangles,
décalage du centre, distance moyenne, part ajoutée / retirée) et un nuage de points coloré pour l'aperçu (retiré en rouge, ajouté en vert,
commun en gris). L'échantillonnage est déterministe (graine fixe) : deux comparaisons identiques donnent le même résultat.
Le calcul tourne comme tâche de fond (job_manager) : `POST /api/model-diff` rend un identifiant, `/api/jobs/<id>` donne l'avancement puis le résultat.
Alignement : « none » (les modèles sont comparés là où ils sont) ou « center » (centres des boîtes englobantes ramenés ensemble).
"""
import os
import sqlite3

_REQUIRED = (
    'DATA_DIR',
    '_is_path_within_sources',
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'session',
)
_OPTIONAL = ('_step_to_trimesh',)
_OVERRIDABLE = ('os',)

_MAIN = {}
DATA_DIR = None
_is_path_within_sources = None
_step_to_trimesh = None      # service de main.py (cascadio, déjà utilisé pour les miniatures et la conversion) ; sinon repli sur OCP
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None

MESH_EXT = ('.stl', '.obj', '.3mf', '.ply', '.off')
STEP_EXT = ('.step', '.stp')
STEP_DEFLECTION = 0.1        # mm : finesse du maillage tiré d'un solide STEP
MAX_BYTES = 120 * 1024 * 1024
SAMPLES = 6000
SHOW_POINTS = 1200
DEFAULT_TOL = 0.005          # fraction de la diagonale de la boîte englobante


def _np():
    import numpy as np
    return np


def load_step(path, deflection=STEP_DEFLECTION):
    """Lit un fichier STEP (solide CAO) et le maille en triangles. Repli quand le lecteur de l'application (cascadio) n'est pas fourni (module testé seul) : demande le paquet facultatif « cadquery-ocp » ;
    sans lui : ValueError (message d'installation). Unités : celles du fichier (mm en pratique)."""
    try:
        from OCP.STEPControl import STEPControl_Reader
        from OCP.BRepMesh import BRepMesh_IncrementalMesh
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopAbs import TopAbs_FACE
        from OCP.TopoDS import TopoDS
        from OCP.BRep import BRep_Tool
        from OCP.TopLoc import TopLoc_Location
        from OCP.IFSelect import IFSelect_RetDone
    except ImportError:
        raise ValueError('Lecture STEP indisponible : installe le paquet facultatif « cadquery-ocp » (pip install cadquery-ocp).')
    np = _np()
    rd = STEPControl_Reader()
    if rd.ReadFile(str(path)) != IFSelect_RetDone:
        raise ValueError('STEP illisible.')
    rd.TransferRoots()
    shape = rd.OneShape()
    BRepMesh_IncrementalMesh(shape, float(deflection), False, 0.5, True)
    verts, faces, base = [], [], 0
    ex = TopExp_Explorer(shape, TopAbs_FACE)
    while ex.More():
        face = (getattr(TopoDS, 'Face_s', None) or TopoDS.Face)(ex.Current())
        loc = TopLoc_Location()
        tri = (getattr(BRep_Tool, 'Triangulation_s', None) or BRep_Tool.Triangulation)(face, loc)
        if tri is not None:
            tr = loc.Transformation()
            for i in range(1, tri.NbNodes() + 1):
                pnt = tri.Node(i).Transformed(tr)
                verts.append((pnt.X(), pnt.Y(), pnt.Z()))
            rev = face.Orientation().name == 'TopAbs_REVERSED' if hasattr(face.Orientation(), 'name') else False
            for i in range(1, tri.NbTriangles() + 1):
                a, b, c = tri.Triangle(i).Get()
                a, b, c = base + a - 1, base + b - 1, base + c - 1
                faces.append((a, c, b) if rev else (a, b, c))
            base += tri.NbNodes()
        ex.Next()
    if not faces:
        raise ValueError('Maillage vide.')
    import trimesh
    m = trimesh.Trimesh(vertices=np.array(verts), faces=np.array(faces), process=False)
    m.merge_vertices()      # les faces CAO ne partagent pas leurs sommets : on les soude pour avoir un solide fermé
    return m


def load_mesh(path):
    import trimesh
    if os.path.splitext(path)[1].lower() in STEP_EXT:
        if _step_to_trimesh is not None:                       # chemin normal : le lecteur STEP de l'application (cascadio)
            m = _step_to_trimesh(path)
            if hasattr(m, 'geometry'):
                m = m.to_geometry() if hasattr(m, 'to_geometry') else m.dump(concatenate=True)
            m.merge_vertices()
            if m is None or len(m.faces) == 0:
                raise ValueError('Maillage vide.')
            return m
        return load_step(path)
    m = trimesh.load(path, force='mesh')
    if m is None or len(m.vertices) == 0 or len(m.faces) == 0:
        raise ValueError('Maillage vide.')
    return m


def sample_surface(vertices, faces, n=SAMPLES, seed=7):
    """n points répartis selon l'aire des triangles (déterministe)."""
    np = _np()
    v = np.asarray(vertices, dtype=float)
    f = np.asarray(faces, dtype=int)
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    area = np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2
    total = area.sum()
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(f), size=n, p=(area / total) if total > 0 else None)
    r1, r2 = rng.random(n), rng.random(n)
    s = np.sqrt(r1)[:, None]
    return a[idx] * (1 - s) + b[idx] * (s * (1 - r2)[:, None]) + c[idx] * (s * r2[:, None])


def surface_area(vertices, faces):
    np = _np()
    v = np.asarray(vertices, dtype=float)
    f = np.asarray(faces, dtype=int)
    return float((np.linalg.norm(np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]), axis=1) / 2).sum())


def nearest_dist(pts, ref, chunk=500):
    """Distance de chaque point de `pts` au point le plus proche de `ref` (force brute par blocs, sans scipy)."""
    np = _np()
    out = np.empty(len(pts))
    for i in range(0, len(pts), chunk):
        d = pts[i:i + chunk, None, :] - ref[None, :, :]
        out[i:i + chunk] = np.sqrt((d * d).sum(axis=2).min(axis=1))
    return out


def mesh_metrics(vertices, faces):
    np = _np()
    v = np.asarray(vertices, dtype=float)
    mn, mx = v.min(axis=0), v.max(axis=0)
    return {'triangles': int(len(faces)), 'size_mm': [round(float(x), 3) for x in (mx - mn)], 'center': [round(float(x), 3) for x in (mn + mx) / 2]}


def volume(vertices, faces):
    """Volume signé par la formule de la divergence (valide pour un maillage fermé) ; None si le maillage n'est pas fermé."""
    np = _np()
    v = np.asarray(vertices, dtype=float)
    f = np.asarray(faces, dtype=int)
    edges = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1)
    _, counts = np.unique(edges, axis=0, return_counts=True)
    if (counts != 2).any():
        return None
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    return abs(float((np.einsum('ij,ij->i', a, np.cross(b, c))).sum() / 6))


def diff_meshes(va, fa, vb, fb, align='none', tol=DEFAULT_TOL, n=SAMPLES, show=SHOW_POINTS, progress=None):
    """Comparaison complète de A (avant) et B (après). Retourne un dict JSON-sérialisable."""
    np = _np()
    va, vb = np.asarray(va, dtype=float), np.asarray(vb, dtype=float)
    ma, mb = mesh_metrics(va, fa), mesh_metrics(vb, fb)
    if align == 'center':
        vb = vb - (np.asarray(mb['center']) - np.asarray(ma['center']))
        mb = mesh_metrics(vb, fb)
    if progress:
        progress(1, 5, 'échantillonnage')
    pa, pb = sample_surface(va, fa, n), sample_surface(vb, fb, n)
    diag = float(np.linalg.norm(np.maximum(va.max(axis=0), vb.max(axis=0)) - np.minimum(va.min(axis=0), vb.min(axis=0)))) or 1.0
    spacing = max((surface_area(va, fa) / n) ** 0.5, (surface_area(vb, fb) / n) ** 0.5)     # écart moyen entre échantillons voisins
    eps = max(diag * float(tol), 1.5 * spacing)             # la tolérance ne descend pas sous la densité d'échantillonnage (sinon faux écarts)
    if progress:
        progress(2, 5, 'distances A → B')
    da = nearest_dist(pa, pb)
    if progress:
        progress(3, 5, 'distances B → A')
    db = nearest_dist(pb, pa)
    removed, added = pa[da > eps], pb[db > eps]
    same = pb[db <= eps]
    if progress:
        progress(4, 5, 'volumes')
    vol_a, vol_b = volume(va, fa), volume(vb, fb)

    def cloud(points, k):
        if len(points) > k:
            points = points[np.linspace(0, len(points) - 1, k).astype(int)]
        return [[round(float(x), 2) for x in p] for p in points]

    res = {
        'a': ma, 'b': mb, 'align': align, 'tolerance_mm': round(eps, 4),
        'delta': {'triangles': mb['triangles'] - ma['triangles'], 'size_mm': [round(y - x, 3) for x, y in zip(ma['size_mm'], mb['size_mm'])],
                  'center_shift_mm': round(float(np.linalg.norm(np.asarray(mb['center']) - np.asarray(ma['center']))), 3),
                  'volume_mm3': round(vol_b - vol_a, 1) if vol_a is not None and vol_b is not None else None},
        'volume_a_mm3': round(vol_a, 1) if vol_a is not None else None, 'volume_b_mm3': round(vol_b, 1) if vol_b is not None else None,
        'mean_distance_mm': round(float((da.mean() + db.mean()) / 2), 4), 'max_distance_mm': round(float(max(da.max(), db.max())), 3),
        'removed_pct': round(100 * len(removed) / n, 1), 'added_pct': round(100 * len(added) / n, 1),
        'identical': bool(len(removed) == 0 and len(added) == 0),
        'points': {'removed': cloud(removed, show), 'added': cloud(added, show), 'same': cloud(same, show)},
    }
    if progress:
        progress(5, 5, 'terminé')
    return res


def diff_files(path_a, path_b, align='none', tol=DEFAULT_TOL, progress=None):
    for p in (path_a, path_b):
        if os.path.splitext(p)[1].lower() not in MESH_EXT + STEP_EXT:
            raise ValueError('Format non pris en charge.')
        if os.path.getsize(p) > MAX_BYTES:
            raise ValueError('Fichier trop volumineux pour la comparaison.')
    ma, mb = load_mesh(path_a), load_mesh(path_b)
    return diff_meshes(ma.vertices, ma.faces, mb.vertices, mb.faces, align, tol, progress=progress)


# ── routes ──

def _version_file(conn, uid, path, token):
    """Fichier d'une version (son NUMÉRO, tel qu'affiché dans la liste des versions du fichier) ou du fichier actuel (« current » / 0).
    None si la version n'existe pas (ou si aucune version n'a jamais été enregistrée : la table peut ne pas exister)."""
    if str(token) in ('0', 'current', ''):
        return path
    try:
        r = conn.execute("SELECT stored_name FROM model_versions WHERE version = ? AND path = ? AND user_id = ?", (int(token), path.replace('\\', '/'), uid)).fetchone()
    except sqlite3.OperationalError:
        return None
    if not r:
        return None
    p = os.path.join(DATA_DIR, 'model_versions', r['stored_name'])
    return p if os.path.isfile(p) else None


def api_model_diff():
    if session.get('role') == 'viewer' and not _demo_ok():
        return jsonify({'error': 'Réservé au compte propriétaire.', 'code': 'viewer_forbidden'}), 403
    d = request.get_json(silent=True) or {}
    path = str(d.get('path') or '').strip()
    align = d.get('align') if d.get('align') in ('none', 'center') else 'none'
    try:
        tol = max(0.0005, min(float(d.get('tolerance', DEFAULT_TOL)), 0.05))
    except (TypeError, ValueError):
        return jsonify({'error': 'Tolérance invalide.'}), 400
    uid = session['user_id']
    if not path or not _is_path_within_sources(path, uid) or not os.path.isfile(path):
        return jsonify({'error': 'Fichier introuvable.'}), 404
    conn = get_db()
    try:
        try:
            fa, fb = _version_file(conn, uid, path, d.get('a', '0')), _version_file(conn, uid, path, d.get('b', '0'))
        except ValueError:
            return jsonify({'error': 'Version invalide.'}), 400
    finally:
        conn.close()
    if not fa or not fb:
        return jsonify({'error': 'Version introuvable.'}), 404
    try:
        from modules import job_manager
        submit = job_manager.submit
    except Exception:
        submit = None
    if submit is None:
        try:
            return jsonify({'result': diff_files(fa, fb, align, tol)})
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    def work(ctx):
        return diff_files(fa, fb, align, tol, progress=ctx.progress)
    job = submit(f"Diff 3D : {os.path.basename(path)}", work, owner=uid, kind='model_diff')
    return jsonify({'job_id': job.id}), 202


_DEMO_COMPUTE = ('/api/plate/arrange', '/api/organize/preview', '/api/model-diff')


def _demo_ok():
    """Démo publique (lecture seule, `IS_DEMO` posé par la surcouche de démo) : consultation (GET) et calculs sans écriture."""
    try:
        return bool(_MAIN.get('IS_DEMO')) and (request.method in ('GET', 'HEAD') or request.path in _DEMO_COMPUTE)
    except Exception:
        return False


_ROUTES = (
    ('/api/model-diff', ['POST'], 'api_model_diff', ('login_required', )),
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
