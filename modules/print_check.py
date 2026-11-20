"""Stellio — vérification avant impression et orientation conseillée (1.1.7).

Avant d'envoyer une pièce au slicer, on veut savoir : ai-je besoin de supports, la base accroche-t-elle, la pièce tient-elle debout,
et dans quel sens la poser ? Ce module répond à partir de la géométrie réelle du maillage (STL, 3MF, OBJ, PLY, STEP) :

* surface en surplomb (faces dont la pente dépasse l'angle choisi, 45° par défaut) et volume de supports ESTIMÉ ;
* surface de contact avec le plateau, élancement, maillage étanche, tient dans le volume d'impression ;
* essai de ~16 orientations (6 axes + les plus grandes faces planes de l'enveloppe convexe) et classement.

C'est une estimation de pré-contrôle, pas une simulation de slicer : le volume de supports est une borne haute (supports posés depuis
le plateau). Rien n'est écrit : le module ne modifie jamais le fichier d'origine ; l'orientation conseillée peut être téléchargée
dans une copie. Routes : `POST /api/print-check`, `GET /api/print-check/oriented`.
"""
import io
import math
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

MESH_EXT = ('.stl', '.obj', '.3mf', '.ply', '.off', '.step', '.stp')
DEFAULT_ANGLE = 45.0         # degrés par rapport à la verticale : au-delà, la face demande un support
BASE_TOL = 0.2               # mm : une face « posée » est à moins de 0,2 mm du plateau
FLAT_COS = 0.99              # face considérée horizontale (≈ 8°)
OVERHANG_WARN = 0.15         # part de la surface en surplomb au-delà de laquelle on prévient
SMALL_BASE_WARN = 0.15       # surface de contact / emprise
TALL_THIN_WARN = 4.0         # hauteur / racine de l'emprise
MAX_FACES = 3_000_000
HULL_CANDIDATES = 10


def _np():
    import numpy as np
    return np


def rotation_to_down(d):
    """Matrice 3×3 qui amène le vecteur `d` (côté posé sur le plateau) vers -Z."""
    np = _np()
    d = np.asarray(d, dtype=float)
    d = d / (np.linalg.norm(d) or 1.0)
    t = np.array([0.0, 0.0, -1.0])
    c = float(np.dot(d, t))
    if c > 1 - 1e-9:
        return np.eye(3)
    if c < -1 + 1e-9:                                   # opposé : demi-tour autour de X
        return np.array([[1.0, 0, 0], [0, -1.0, 0], [0, 0, -1.0]])
    v = np.cross(d, t)
    s = np.linalg.norm(v)
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + k + k @ k * ((1 - c) / (s * s))


def evaluate(vertices, faces, normals, areas, R, angle=DEFAULT_ANGLE):
    """Mesures de la pièce une fois tournée par R (posée sur le plateau)."""
    np = _np()
    v = vertices @ R.T
    n = normals @ R.T
    zmin = float(v[:, 2].min())
    zmax = float(v[:, 2].max())
    tri_z = v[faces][:, :, 2]
    zc = tri_z.mean(axis=1)
    size = v.max(axis=0) - v.min(axis=0)
    nz = n[:, 2]
    base = (nz < -FLAT_COS) & (tri_z.max(axis=1) <= zmin + BASE_TOL)
    thr = -math.sin(math.radians(angle))
    over = (nz < thr) & ~base
    base_area = float(areas[base].sum())
    over_area = float(areas[over].sum())
    total = float(areas.sum()) or 1.0
    support = float((areas[over] * np.abs(nz[over]) * np.maximum(zc[over] - zmin, 0.0)).sum())
    footprint = float(size[0] * size[1]) or 1e-9
    return {
        'size': [round(float(size[0]), 2), round(float(size[1]), 2), round(float(size[2]), 2)],
        'height': round(zmax - zmin, 2),
        'base_area': round(base_area, 1),
        'base_ratio': round(min(base_area / footprint, 1.0), 3),
        'overhang_area': round(over_area, 1),
        'overhang_ratio': round(over_area / total, 3),
        'support_volume_cm3': round(support / 1000.0, 2),
        'tall_thin': round((zmax - zmin) / math.sqrt(footprint), 2),
    }


def _cost(m):
    """Plus c'est petit, mieux c'est : supports d'abord, puis surface en surplomb, puis stabilité (élancement, petite base)."""
    bbox = m['size'][0] * m['size'][1] * max(m['height'], 1.0)
    return (m['support_volume_cm3'] * 1000.0 + 0.2 * m['overhang_area']
            + 0.0005 * bbox * (1.0 - m['base_ratio'])
            + 0.02 * bbox * max(0.0, m['tall_thin'] - 2.0))


def candidates(vertices, normals, areas):
    """Directions « posé sur le plateau » à essayer : 6 axes + grandes faces planes de l'enveloppe convexe."""
    np = _np()
    out = [np.array(a, dtype=float) for a in ((0, 0, -1), (0, 0, 1), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0))]
    try:
        import trimesh
        pts = vertices
        if len(pts) > 200000:
            pts = pts[np.random.default_rng(3).choice(len(pts), 200000, replace=False)]
        hull = trimesh.convex.convex_hull(pts)
        hn = hull.face_normals
        ha = hull.area_faces
        order = np.argsort(-ha)
        picked = []
        for i in order:
            d = hn[i]
            if any(float(np.dot(d, p)) > math.cos(math.radians(6)) for p in out + picked):
                continue
            picked.append(d)
            if len(picked) >= HULL_CANDIDATES:
                break
        out.extend(picked)
    except Exception:
        pass
    return out


def _fits(size, bed):
    if not bed:
        return True
    w, d, h = size
    bx, by, bz = bed
    return h <= bz + 1e-6 and ((w <= bx and d <= by) or (w <= by and d <= bx))


def analyze(mesh, angle=DEFAULT_ANGLE, bed=None):
    """Contrôle complet d'un maillage trimesh : mesures actuelles, problèmes, orientations classées."""
    np = _np()
    V = np.asarray(mesh.vertices, dtype=float)
    F = np.asarray(mesh.faces, dtype=int)
    if len(F) == 0:
        raise ValueError('Maillage vide.')
    N = np.asarray(mesh.face_normals, dtype=float)
    A = np.asarray(mesh.area_faces, dtype=float)
    cur = evaluate(V, F, N, A, np.eye(3), angle)
    # posé tel quel : on le descend au plateau, ce que fait un slicer ; l'orientation courante n'est pas modifiée
    ranked = []
    for d in candidates(V, N, A):
        R = rotation_to_down(d)
        m = evaluate(V, F, N, A, R, angle)
        ranked.append({'down': [round(float(x), 4) for x in d], 'metrics': m, 'fits': _fits(m['size'], bed), 'cost': _cost(m)})
    ranked.sort(key=lambda r: (not r['fits'], r['cost']))
    best = ranked[0]
    for r in ranked:
        r['label'] = _label(r['down'])
    cur_cost = _cost(cur)
    gain = None
    if cur_cost > 0:
        gain = round(max(0.0, (cur_cost - best['cost']) / cur_cost), 3)
    issues = []
    try:
        vol = float(mesh.volume)
    except Exception:
        vol = 0.0
    if not bool(getattr(mesh, 'is_watertight', True)):
        issues.append({'level': 'warning', 'code': 'not_watertight'})
    if vol < 0:
        issues.append({'level': 'warning', 'code': 'inverted_normals'})
    if bed and not _fits(cur['size'], bed):
        if not any(r['fits'] for r in ranked):
            issues.append({'level': 'error', 'code': 'too_big', 'size': cur['size'], 'bed': list(bed)})
        else:
            issues.append({'level': 'info', 'code': 'fits_only_rotated'})
    if cur['overhang_ratio'] > OVERHANG_WARN:
        issues.append({'level': 'warning', 'code': 'overhangs', 'ratio': cur['overhang_ratio'], 'support_volume_cm3': cur['support_volume_cm3']})
    if cur['base_ratio'] < SMALL_BASE_WARN:
        issues.append({'level': 'warning', 'code': 'small_base', 'ratio': cur['base_ratio']})
    if cur['tall_thin'] > TALL_THIN_WARN:
        issues.append({'level': 'warning', 'code': 'tall_thin', 'ratio': cur['tall_thin']})
    if gain is not None and gain >= 0.25 and best['down'] != [0.0, 0.0, -1.0]:
        issues.append({'level': 'info', 'code': 'better_orientation', 'gain': gain})
    verdict = 'error' if any(i['level'] == 'error' for i in issues) else ('warning' if any(i['level'] == 'warning' for i in issues) else 'ok')
    return {'verdict': verdict, 'angle': angle, 'current': cur, 'issues': issues, 'best': best, 'gain': gain,
            'orientations': ranked[:4], 'volume_cm3': round(abs(vol) / 1000.0, 2), 'triangles': int(len(F)),
            'note': 'estimate'}


def _label(d):
    names = {(0, 0, -1): 'z-', (0, 0, 1): 'z+', (1, 0, 0): 'x+', (-1, 0, 0): 'x-', (0, 1, 0): 'y+', (0, -1, 0): 'y-'}
    key = tuple(int(round(x)) for x in d)
    if all(abs(a - b) < 1e-3 for a, b in zip(d, key)) and key in names:
        return names[key]
    return 'face'


def oriented_stl_bytes(mesh, down):
    """Copie du maillage tournée pour que la face `down` repose sur le plateau, posée à Z = 0 (STL binaire)."""
    np = _np()
    import trimesh
    R = rotation_to_down(down)
    v = np.asarray(mesh.vertices, dtype=float) @ R.T
    v[:, 2] -= v[:, 2].min()
    out = trimesh.Trimesh(vertices=v, faces=np.asarray(mesh.faces), process=False)
    return out.export(file_type='stl')


def _norm(p):
    return str(p or '').strip().replace('\\', '/')


def _native(p):
    return p.replace('/', os.sep) if os.sep != '/' else p


def _load(native):
    from modules import model_diff
    return model_diff.load_mesh(native)


def _bed_for(conn, uid, printer_id):
    try:
        import json
        r = conn.execute("SELECT config FROM printers WHERE id = ? AND user_id = ?", (int(printer_id), uid)).fetchone()
        cfg = json.loads((r['config'] if r else '') or '{}')
        b = [float(cfg.get('bed_x') or 0), float(cfg.get('bed_y') or 0), float(cfg.get('bed_z') or 0)]
        return b if all(v > 0 for v in b) else None
    except Exception:
        return None


def _parse_bed(d):
    try:
        b = [float(d.get('x')), float(d.get('y')), float(d.get('z'))]
        return b if all(v > 0 for v in b) else None
    except Exception:
        return None


def _check_path(path):
    if not path:
        return None, (jsonify({'error': 'path_required'}), 400)
    native = _native(path)
    if os.path.splitext(path)[1].lower() not in MESH_EXT:
        return None, (jsonify({'error': 'unsupported_format'}), 400)
    if not _is_path_within_sources(native, session['user_id']):
        return None, (jsonify({'error': 'forbidden'}), 403)
    if not os.path.isfile(native):
        return None, (jsonify({'error': 'not_found'}), 404)
    return native, None


def api_print_check():
    data = request.get_json(silent=True) or {}
    path = _norm(data.get('path'))
    native, err = _check_path(path)
    if err:
        return err
    try:
        angle = max(20.0, min(float(data.get('angle') or DEFAULT_ANGLE), 80.0))
    except (TypeError, ValueError):
        angle = DEFAULT_ANGLE
    bed = _parse_bed(data['bed']) if isinstance(data.get('bed'), dict) else None
    if not bed and data.get('printer_id'):
        conn = get_db()
        try:
            bed = _bed_for(conn, session['user_id'], data.get('printer_id'))
        finally:
            conn.close()
    try:
        mesh = _load(native)
        if len(mesh.faces) > MAX_FACES:
            return jsonify({'error': 'too_many_triangles', 'triangles': int(len(mesh.faces))}), 413
        res = analyze(mesh, angle=angle, bed=bed)
    except ValueError as e:
        return jsonify({'error': 'unreadable', 'message': str(e)}), 422
    except Exception as e:
        app_logger.info(f"[PrintCheck] échec {path}: {e}")
        return jsonify({'error': 'check_failed', 'message': str(e)[:200]}), 500
    res.update({'path': path, 'name': os.path.basename(path), 'bed': bed})
    return jsonify(res)


def api_print_check_oriented():
    path = _norm(request.args.get('path'))
    native, err = _check_path(path)
    if err:
        return err
    try:
        down = [float(x) for x in str(request.args.get('down', '0,0,-1')).split(',')]
        if len(down) != 3 or not any(down):
            raise ValueError
    except ValueError:
        return jsonify({'error': 'bad_direction'}), 400
    try:
        mesh = _load(native)
        data = oriented_stl_bytes(mesh, down)
    except Exception as e:
        return jsonify({'error': 'check_failed', 'message': str(e)[:200]}), 500
    from flask import send_file
    base = os.path.splitext(os.path.basename(path))[0]
    return send_file(io.BytesIO(data), mimetype='model/stl', as_attachment=True, download_name=f'{base}_oriented.stl')


_ROUTES = (
    ('/api/print-check', ['POST'], 'api_print_check', ('login_required', )),
    ('/api/print-check/oriented', ['GET'], 'api_print_check_oriented', ('login_required', )),
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
