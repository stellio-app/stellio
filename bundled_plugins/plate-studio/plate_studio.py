"""Stellio — atelier multi-modèles : disposition de plusieurs pièces sur un ou plusieurs plateaux (1.1.7).

Algorithme : MaxRects (heuristique « meilleur côté court »), rotation de 90° autour de Z facultative, marge entre pièces, plusieurs plateaux
si tout ne tient pas, contrôle de hauteur (une pièce plus haute que le volume d'impression est signalée, jamais tronquée).
Deux modes. « box » : l'empreinte d'une pièce est sa boîte englobante (MaxRects ci-dessus). « shape » (par défaut) : imbrication de la
VRAIE empreinte (projection du maillage sur le plateau, trous remplis) par grille de cellules : chaque pièce est dessinée en cellules de
~1 mm, élargie d'une demi-marge, et placée à la première position libre (bas puis gauche) parmi plusieurs rotations (pas de 90°, 45°, 30° ou
15° autour de Z). Une pièce concave peut loger une petite pièce dans son creux ; les trous fermés (anneau) restent inutilisés.
Limites assumées : l'empreinte est la projection vue de dessus (pas d'orientation automatique de la pièce à plat, pas de pièces superposées
en hauteur) ; au-delà de 400 000 triangles l'empreinte est l'enveloppe convexe. Sortie : disposition JSON, et export 3MF (un objet par pièce,
déjà tourné et positionné sur son plateau).
"""
import io
import os
import zipfile

_REQUIRED = (
    '_is_path_within_sources',
    'app',
    'app_logger',
    'jsonify',
    'login_required',
    'request',
    'session',
)
_OPTIONAL = ('send_file',)
_OVERRIDABLE = ('os',)

_MAIN = {}
_is_path_within_sources = None
app = None
app_logger = None
jsonify = None
login_required = None
request = None
session = None
send_file = None

MESH_EXT = ('.stl', '.obj', '.3mf', '.ply', '.off')
MAX_ITEMS = 200
MAX_BYTES = 80 * 1024 * 1024
DEFAULT_PLATE = {'w': 256.0, 'd': 256.0, 'z': 256.0}


# ── cœur : empaquetage MaxRects (fonctions pures, testables sans Flask) ──
class _Plate:
    def __init__(self, w, d):
        self.w, self.d = float(w), float(d)
        self.free = [(0.0, 0.0, self.w, self.d)]
        self.placed = []

    def _best(self, w, d, rotate):
        best = None
        for rot in ((False, True) if rotate and abs(w - d) > 1e-9 else (False,)):
            iw, id_ = (d, w) if rot else (w, d)
            for fx, fy, fw, fd in self.free:
                if iw <= fw + 1e-9 and id_ <= fd + 1e-9:
                    score = (min(fw - iw, fd - id_), max(fw - iw, fd - id_), fy, fx)
                    if best is None or score < best[0]:
                        best = (score, fx, fy, iw, id_, rot)
        return best

    def put(self, item, rotate):
        b = self._best(item['w'], item['d'], rotate)
        if not b:
            return None
        _, x, y, iw, id_, rot = b
        self._split(x, y, iw, id_)
        p = {'id': item['id'], 'x': round(x, 3), 'y': round(y, 3), 'w': round(iw, 3), 'd': round(id_, 3), 'h': item.get('h', 0), 'rot': 90 if rot else 0}
        self.placed.append(p)
        return p

    def _split(self, x, y, w, d):
        out = []
        for fx, fy, fw, fd in self.free:
            if x >= fx + fw - 1e-9 or x + w <= fx + 1e-9 or y >= fy + fd - 1e-9 or y + d <= fy + 1e-9:
                out.append((fx, fy, fw, fd))
                continue
            if x > fx + 1e-9:
                out.append((fx, fy, x - fx, fd))
            if x + w < fx + fw - 1e-9:
                out.append((x + w, fy, fx + fw - x - w, fd))
            if y > fy + 1e-9:
                out.append((fx, fy, fw, y - fy))
            if y + d < fy + fd - 1e-9:
                out.append((fx, y + d, fw, fy + fd - y - d))
        self.free = [r for i, r in enumerate(out) if not any(
            j != i and o[0] <= r[0] + 1e-9 and o[1] <= r[1] + 1e-9 and o[0] + o[2] >= r[0] + r[2] - 1e-9 and o[1] + o[3] >= r[1] + r[3] - 1e-9
            and (o != r or j < i) for j, o in enumerate(out))]


def _centered(pls, pl):
    """Regroupe les pièces d'un plateau autour de son centre : on garde la disposition compacte (coin bas-gauche, la plus dense), puis on
    décale l'ensemble pour que la boîte englobante soit centrée sur le plateau. Les écarts entre pièces ne changent pas."""
    if not pls:
        return pls
    x0, x1 = min(q['x'] for q in pls), max(q['x'] + q['w'] for q in pls)
    y0, y1 = min(q['y'] for q in pls), max(q['y'] + q['d'] for q in pls)
    dx, dy = (pl['w'] - (x1 - x0)) / 2.0 - x0, (pl['d'] - (y1 - y0)) / 2.0 - y0
    for q in pls:
        q['x'] = round(q['x'] + dx, 3)
        q['y'] = round(q['y'] + dy, 3)
    return pls


def arrange(items, plate=None, margin=3.0, rotate=True, max_plates=20):
    """items : [{id, w, d, h}] (mm). Retourne {plates:[{index, placements, fill}], unplaced:[{id, reason}], plate}.
    Une pièce est « trop haute » si h > plate.z, « trop grande » si elle ne tient pas seule sur un plateau vide."""
    pl = dict(DEFAULT_PLATE)
    pl.update({k: float(v) for k, v in (plate or {}).items() if k in pl and float(v) > 0})
    margin = max(0.0, float(margin))
    unplaced, todo = [], []
    for it in items:
        w, d, h = float(it['w']), float(it['d']), float(it.get('h', 0))
        if h > pl['z'] + 1e-9:
            unplaced.append({'id': it['id'], 'reason': 'too_tall'})
            continue
        probe = _Plate(pl['w'] + margin, pl['d'] + margin)
        if not probe.put({'id': it['id'], 'w': w + margin, 'd': d + margin}, rotate):
            unplaced.append({'id': it['id'], 'reason': 'too_large'})
            continue
        todo.append({'id': it['id'], 'w': w + margin, 'd': d + margin, 'h': h, 'rw': w, 'rd': d})
    todo.sort(key=lambda i: (-(i['w'] * i['d']), str(i['id'])))
    plates = []
    for it in todo:
        done = False
        for p in plates:
            if p.put(it, rotate):
                done = True
                break
        if not done:
            if len(plates) >= max_plates:
                unplaced.append({'id': it['id'], 'reason': 'too_many_plates'})
                continue
            p = _Plate(pl['w'] + margin, pl['d'] + margin)
            p.put(it, rotate)
            plates.append(p)
    out = []
    for i, p in enumerate(plates, 1):
        pls = []
        for q in p.placed:
            pls.append({'id': q['id'], 'x': round(q['x'] + margin / 2, 3), 'y': round(q['y'] + margin / 2, 3),
                        'w': round(q['w'] - margin, 3), 'd': round(q['d'] - margin, 3), 'h': q['h'], 'rot': q['rot']})
        _centered(pls, pl)
        area = sum(q['w'] * q['d'] for q in pls)
        out.append({'index': i, 'placements': pls, 'fill': round(area / (pl['w'] * pl['d']), 4)})
    return {'plate': pl, 'margin': margin, 'plates': out, 'unplaced': unplaced}


# ── imbrication de la vraie empreinte (mode « shape ») ──
SHAPE_MAX_FACES = 400_000
ROTATION_STEPS = (90, 45, 30, 15)
MAX_CELLS = 700 * 700


def _rot_cw(geom, deg):
    """Rotation de `deg` degrés dans le sens horaire (vue de dessus) autour de l'origine : (x, y) → (x·cos + y·sin, −x·sin + y·cos).
    Même sens que l'export 3MF (90° : (x, y) → (y, −x))."""
    from shapely import affinity
    return affinity.rotate(geom, -deg, origin=(0, 0))


def _fill_holes(geom):
    from shapely.geometry import Polygon, MultiPolygon
    parts = list(geom.geoms) if hasattr(geom, 'geoms') else [geom]
    polys = [Polygon(g.exterior) for g in parts if g.geom_type == 'Polygon' and not g.is_empty]
    return polys[0] if len(polys) == 1 else MultiPolygon(polys)


def footprint(mesh, max_faces=SHAPE_MAX_FACES):
    """Empreinte d'un maillage sur le plateau : union des triangles projetés sur XY, trous fermés remplis (géométrie shapely, mm).
    Au-delà de `max_faces` triangles, ou si l'union échoue : enveloppe convexe."""
    import numpy as np
    import shapely
    from shapely.geometry import MultiPoint
    v = np.asarray(mesh.vertices, dtype=float)[:, :2]
    f = np.asarray(mesh.faces)
    if len(f) <= max_faces:
        try:
            tri = v[f]
            area = 0.5 * np.abs((tri[:, 1, 0] - tri[:, 0, 0]) * (tri[:, 2, 1] - tri[:, 0, 1]) - (tri[:, 2, 0] - tri[:, 0, 0]) * (tri[:, 1, 1] - tri[:, 0, 1]))
            tri = tri[area > 1e-9]
            if len(tri):
                u = shapely.union_all(shapely.polygons(shapely.linearrings(tri))).buffer(0)
                if not u.is_empty:
                    return _fill_holes(u)
        except Exception:
            pass
    return MultiPoint(v).convex_hull


def _bounds(geom):
    x0, y0, x1, y1 = geom.bounds
    return x0, y0, x1, y1


def _mask(geom, res):
    """Cellules (ligne = Y, colonne = X) touchées par `geom` (coin bas-gauche de sa boîte en (0, 0)) : image PIL, bord compris."""
    import numpy as np
    from PIL import Image, ImageDraw
    x0, y0, x1, y1 = _bounds(geom)
    nx, ny = int((x1 - x0) / res) + 2, int((y1 - y0) / res) + 2
    img = Image.new('L', (nx, ny), 0)
    dr = ImageDraw.Draw(img)
    for g in (list(geom.geoms) if hasattr(geom, 'geoms') else [geom]):
        pts = [((x - x0) / res, (y - y0) / res) for x, y in g.exterior.coords]
        if len(pts) >= 3:
            dr.polygon(pts, fill=1, outline=1)
    return np.asarray(img, dtype=bool)


def _dilate(mask, n):
    if n <= 0:
        return mask
    from scipy.ndimage import binary_dilation
    return binary_dilation(mask, structure=np_ones3(), iterations=n)


def np_ones3():
    import numpy as np
    return np.ones((3, 3), dtype=bool)


def _angles(step):
    if int(step) == 0:
        return [0]                                              # rotation désactivée
    step = int(step) if int(step) in ROTATION_STEPS else 90
    return [a for a in range(0, 360, step)]


def _prepare(geom, step, res, dil):
    """Pour chaque angle : géométrie tournée ramenée à (0, 0), masque élargi, taille en mm. Angles redondants (symétries) retirés."""
    from shapely import affinity
    out, seen = [], set()
    for ang in _angles(step):
        g = _rot_cw(geom, ang)
        x0, y0, x1, y1 = _bounds(g)
        g = affinity.translate(g, -x0, -y0)
        m = _mask(g, res)
        key = (m.shape, m.tobytes())
        if key in seen:
            continue
        seen.add(key)
        out.append({'rot': ang, 'geom': g, 'w': x1 - x0, 'd': y1 - y0, 'mask': m, 'dmask': _dilate(m, dil)})
    return out


def _free_positions(occ, dmask, nx, ny, dil, W, D):
    """Positions (ligne, colonne) de la pièce non élargie, dans le plateau de W × D cellules, où le masque élargi ne touche aucune cellule occupée.
    `occ` est le plateau entouré de `dil` cellules libres (la demi-marge peut dépasser du bord)."""
    import numpy as np
    from scipy.signal import fftconvolve
    h, w = dmask.shape
    if occ.shape[0] < h or occ.shape[1] < w:
        return None
    over = fftconvolve(occ.astype(np.float64), dmask[::-1, ::-1].astype(np.float64), mode='valid')
    ok = over < 0.5
    ok = ok[:max(D - ny, -1) + 1, :max(W - nx, -1) + 1]      # la pièce non élargie reste dans le plateau
    return ok if ok.size and ok.any() else None


def arrange_shapes(items, plate=None, margin=3.0, step=90, max_plates=20, res=None):
    """items : [{id, poly (géométrie shapely, mm, coin bas-gauche de la boîte en (0, 0)), h}]. Retourne le même format que `arrange`,
    avec `rot` en degrés (sens horaire) et `fill` = aire réelle des empreintes / aire du plateau."""
    import numpy as np
    pl = dict(DEFAULT_PLATE)
    pl.update({k: float(v) for k, v in (plate or {}).items() if k in pl and float(v) > 0})
    margin = max(0.0, float(margin))
    if res is None:
        res = max(0.5, max(pl['w'], pl['d']) / 256.0)
    res = float(res)
    while (pl['w'] / res) * (pl['d'] / res) > MAX_CELLS:        # grille raisonnable même sur un très grand plateau
        res *= 1.5
    dil = max(1, int(np.ceil(margin / 2.0 / res)))
    W, D = int(np.floor(pl['w'] / res + 1e-9)), int(np.floor(pl['d'] / res + 1e-9))   # jamais plus large que le plateau
    unplaced, todo = [], []
    for it in items:
        h = float(it.get('h', 0))
        if h > pl['z'] + 1e-9:
            unplaced.append({'id': it['id'], 'reason': 'too_tall'})
            continue
        variants = _prepare(it['poly'], step, res, dil)
        fits = [v for v in variants if v['mask'].shape[0] <= D and v['mask'].shape[1] <= W]
        if not fits:
            unplaced.append({'id': it['id'], 'reason': 'too_large'})
            continue
        todo.append({'id': it['id'], 'h': h, 'variants': fits, 'area': float(it['poly'].area)})
    todo.sort(key=lambda t: (-t['area'], str(t['id'])))
    plates = []

    def empty():
        return {'occ': np.zeros((D + 2 * dil, W + 2 * dil), dtype=bool), 'placed': []}

    def try_place(p, t):
        best = None
        for v in t['variants']:
            ny, nx = v['mask'].shape
            ok = _free_positions(p['occ'], v['dmask'], nx, ny, dil, W, D)
            if ok is None:
                continue
            ii, jj = np.nonzero(ok)
            key = (ii + ny) * (W + 2) + jj                           # arête haute la plus basse, puis la plus à gauche
            k = int(np.argmin(key))
            cand = (int(key[k]), v['rot'], int(ii[k]), int(jj[k]), v)
            if best is None or cand[:2] < best[:2]:
                best = cand
        if best is None:
            return False
        _, _, i, j, v = best
        dh, dw = v['dmask'].shape
        p['occ'][i:i + dh, j:j + dw] |= v['dmask']
        p['placed'].append({'id': t['id'], 'x': round(j * res, 3), 'y': round(i * res, 3), 'w': round(v['w'], 3), 'd': round(v['d'], 3),
                            'h': t['h'], 'rot': v['rot'], 'geom': v['geom'], 'outline': _rel_rings(v['geom'], 0.05, 400)})
        return True

    for t in todo:
        if any(try_place(p, t) for p in plates):
            continue
        if len(plates) >= max_plates:
            unplaced.append({'id': t['id'], 'reason': 'too_many_plates'})
            continue
        p = empty()
        if not try_place(p, t):
            unplaced.append({'id': t['id'], 'reason': 'too_large'})
            continue
        plates.append(p)
    out = []
    for n, p in enumerate(plates, 1):
        area = sum(q['geom'].area for q in p['placed'])
        out.append({'index': n, 'placements': _centered([{k: v for k, v in q.items() if k != 'geom'} for q in p['placed']], pl),
                    'fill': round(area / (pl['w'] * pl['d']), 4)})
    return {'plate': pl, 'margin': margin, 'plates': out, 'unplaced': unplaced, 'mode': 'shape', 'resolution': round(res, 3)}


def _rel_rings(geom, tol=0.2, max_pts=300):
    """Contours (liste d'anneaux [[x, y], …]) d'une géométrie dont la boîte commence en (0, 0), simplifiés à `tol` mm."""
    g = geom.simplify(tol, preserve_topology=True) if tol else geom
    rings = []
    for part in (list(g.geoms) if hasattr(g, 'geoms') else [g]):
        if part.geom_type != 'Polygon' or part.is_empty:
            continue
        pts = [[round(x, 2), round(y, 2)] for x, y in list(part.exterior.coords)[:-1]]
        if len(pts) > max_pts:
            pts = pts[::int(np_ceil(len(pts) / max_pts))]
        rings.append(pts)
    return rings


def np_ceil(x):
    import math
    return math.ceil(x)


def shape_info(mesh, geom, max_edges=500):
    """Données d'affichage d'une pièce (non tournée, boîte en (0, 0, 0)) : contour simplifié, enveloppe convexe (pour la boîte d'une
    rotation quelconque) et arêtes vives du maillage (aperçu 3D de la vraie géométrie)."""
    import numpy as np
    x0, y0, _, _ = _bounds(geom)
    lo = mesh.bounds[0]
    out = {'outline': _rel_rings(geom), 'hull': _rel_rings(geom.convex_hull, 0.05, 120)[0] if not geom.is_empty else [], 'edges': []}
    try:
        if len(mesh.faces) <= 150_000 and max_edges > 0:
            ang = np.asarray(mesh.face_adjacency_angles)
            e = np.asarray(mesh.face_adjacency_edges)[ang > np.radians(25)]
            if len(e):
                v = np.asarray(mesh.vertices, dtype=float) - lo
                seg = np.concatenate([v[e[:, 0]], v[e[:, 1]]], axis=1)
                if len(seg) > max_edges:
                    ln = np.linalg.norm(seg[:, 3:] - seg[:, :3], axis=1)
                    seg = seg[np.argsort(-ln)[:max_edges]]
                out['edges'] = np.round(seg, 1).tolist()
    except Exception:
        out['edges'] = []
    return out


def check_layout(layout):
    """Vérifie une disposition (aussi après retouche manuelle) : sortie de plateau, chevauchement, hauteur. Liste de problèmes."""
    pl, issues = layout.get('plate') or DEFAULT_PLATE, []
    for p in layout.get('plates', []):
        pts = p['placements']
        for a in pts:
            if a['x'] < -1e-6 or a['y'] < -1e-6 or a['x'] + a['w'] > pl['w'] + 1e-6 or a['y'] + a['d'] > pl['d'] + 1e-6:
                issues.append({'plate': p['index'], 'id': a['id'], 'issue': 'out_of_plate'})
            if a.get('h', 0) > pl['z'] + 1e-6:
                issues.append({'plate': p['index'], 'id': a['id'], 'issue': 'too_tall'})
        shapes = {}
        for i, a in enumerate(pts):
            for b in pts[i + 1:]:
                if a['x'] < b['x'] + b['w'] - 1e-6 and b['x'] < a['x'] + a['w'] - 1e-6 and a['y'] < b['y'] + b['d'] - 1e-6 and b['y'] < a['y'] + a['d'] - 1e-6:
                    if a.get('outline') and b.get('outline') and not _outlines_overlap(a, b, shapes):
                        continue                                   # les boîtes se recouvrent mais pas les vraies empreintes : imbrication valide
                    issues.append({'plate': p['index'], 'id': a['id'], 'other': b['id'], 'issue': 'overlap'})
    return issues


OVERLAP_TOL_MM2 = 0.05


def _outline_geom(a, cache):
    """Empreinte d'une pièce posée (contours relatifs + position) en géométrie shapely ; None si le contour est inexploitable."""
    key = id(a)
    if key not in cache:
        try:
            from shapely.geometry import Polygon
            from shapely.ops import unary_union
            polys = [Polygon([(a['x'] + px, a['y'] + py) for px, py in ring]) for ring in a['outline'] if len(ring) >= 3]
            polys = [q.buffer(0) for q in polys]
            cache[key] = unary_union(polys) if polys else None
        except Exception:
            cache[key] = None
    return cache[key]


def _outlines_overlap(a, b, cache):
    ga, gb = _outline_geom(a, cache), _outline_geom(b, cache)
    if ga is None or gb is None:
        return True                                                # contour illisible : on retombe sur la boîte (prudent)
    return ga.intersection(gb).area > OVERLAP_TOL_MM2


def _num(v, lo=-1e6, hi=1e6):
    f = float(v)
    if f != f or f in (float('inf'), float('-inf')):
        raise ValueError('Nombre invalide.')
    return max(lo, min(f, hi))


def _clean_outline(raw):
    """Contours relatifs envoyés par l'éditeur : au plus 8 anneaux de 400 points, nombres finis."""
    if not isinstance(raw, list) or len(raw) > 8:
        raise ValueError('Contour invalide.')
    rings = []
    for ring in raw:
        if not isinstance(ring, list) or len(ring) > 400:
            raise ValueError('Contour invalide.')
        rings.append([[_num(pt[0], -5000, 5000), _num(pt[1], -5000, 5000)] for pt in ring])
    return rings


def clean_layout(raw):
    """Valide et normalise une disposition envoyée par l'éditeur : {plate:{w,d,z}, plates:[{index, placements:[{id,x,y,w,d,h,rot}]}]}."""
    if not isinstance(raw, dict):
        raise ValueError('Disposition invalide.')
    pl = dict(DEFAULT_PLATE)
    for k, v in (raw.get('plate') or {}).items():
        if k in pl:
            pl[k] = _num(v, 1, 2000)
    plates, total = [], 0
    for n, p in enumerate(raw.get('plates') or [], 1):
        pts = []
        for a in (p.get('placements') or []):
            total += 1
            if total > MAX_ITEMS:
                raise ValueError(f'Maximum {MAX_ITEMS} pièces par disposition.')
            rot = _num(a.get('rot') or 0, -3600, 3600) % 360.0
            rot = int(rot) if rot == int(rot) else round(rot, 3)
            q = {'id': str(a.get('id') or '')[:500], 'x': _num(a.get('x')), 'y': _num(a.get('y')), 'w': _num(a.get('w'), 0, 5000),
                 'd': _num(a.get('d'), 0, 5000), 'h': _num(a.get('h', 0), 0, 5000), 'rot': rot}
            if a.get('outline'):
                q['outline'] = _clean_outline(a['outline'])
            pts.append(q)
        plates.append({'index': int(p.get('index') or n), 'placements': pts})
    if not plates:
        raise ValueError('Aucun plateau.')
    return {'plate': pl, 'plates': plates}


# ── maillages ──
def _load(path):
    import trimesh
    m = trimesh.load(path, force='mesh')
    if m is None or len(m.vertices) == 0 or len(m.faces) == 0:
        raise ValueError('Maillage vide.')
    return m


def _item_from_mesh(item_id, mesh):
    lo, hi = mesh.bounds
    e = hi - lo
    return {'id': item_id, 'w': float(e[0]), 'd': float(e[1]), 'h': float(e[2])}


def export_3mf(entries, plate_index):
    """entries : [(mesh, placement)] d'UN plateau → octets 3MF (unité mm, un objet par pièce, posé sur Z=0)."""
    import numpy as np
    res, items = [], []
    for n, (mesh, p) in enumerate(entries, 1):
        v = np.asarray(mesh.vertices, dtype=float).copy()
        lo = v.min(axis=0)
        v -= lo
        f = np.asarray(mesh.faces)
        rot = float(p.get('rot') or 0) % 360.0
        if rot:
            c, sn = np.cos(np.radians(rot)), np.sin(np.radians(rot))
            v = np.column_stack([v[:, 0] * c + v[:, 1] * sn, -v[:, 0] * sn + v[:, 1] * c, v[:, 2]])   # sens horaire (90° : (x, y) → (y, −x)) ; orientation des triangles conservée
            v[:, 0] -= v[:, 0].min()
            v[:, 1] -= v[:, 1].min()
        v[:, 0] += p['x']
        v[:, 1] += p['y']
        vs = ''.join(f'<vertex x="{a:.5f}" y="{b:.5f}" z="{c:.5f}"/>' for a, b, c in v)
        ts = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in f)
        name = str(p['id']).replace('&', '&amp;').replace('<', '&lt;').replace('"', '&quot;')
        res.append(f'<object id="{n}" type="model" name="{name}"><mesh><vertices>{vs}</vertices><triangles>{ts}</triangles></mesh></object>')
        items.append(f'<item objectid="{n}"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="fr" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<metadata name="Title">Stellio — plateau {plate_index}</metadata><resources>{"".join(res)}</resources><build>{"".join(items)}</build></model>')
    ct = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ct)
        z.writestr('_rels/.rels', rels)
        z.writestr('3D/3dmodel.model', model)
    return buf.getvalue()


# ── routes ──
_DEMO_COMPUTE = ('/api/plate/arrange', '/api/plate/check')


def _demo_ok():
    """Démo publique (`IS_DEMO`) : le calcul de disposition est permis, jamais l'export (pas de récupération de fichiers)."""
    try:
        return bool(_MAIN.get('IS_DEMO')) and request.path in _DEMO_COMPUTE
    except Exception:
        return False


def _owner_ok():
    return session.get('role') != 'viewer' or _demo_ok()


def _src_id(i):
    """Chemin d'un identifiant de pièce : seul un suffixe « #N » final désigne un exemplaire (un dossier peut contenir « # »)."""
    import re
    return re.sub(r'#\d+$', '', str(i))


def _resolve_paths(paths):
    out = []
    for p in paths:
        p = os.path.realpath(str(p))
        if not p.lower().endswith(MESH_EXT) or not os.path.isfile(p):
            raise ValueError(f'Fichier non pris en charge : {os.path.basename(p)}')
        if not _is_path_within_sources(p, session['user_id']):
            raise PermissionError('Fichier hors des sources.')
        if os.path.getsize(p) > MAX_BYTES:
            raise ValueError(f'Fichier trop volumineux : {os.path.basename(p)}')
        out.append(p)
    return out


def _parse(data):
    paths = data.get('paths') or []
    if not isinstance(paths, list) or not paths:
        raise ValueError('Aucun modèle.')
    copies = max(1, min(int(data.get('copies') or 1), 50))
    counts = data.get('counts') if isinstance(data.get('counts'), dict) else {}
    resolved = _resolve_paths(paths)
    per = {}
    for orig, r in zip(paths, resolved):                      # nombre d'exemplaires propre à chaque modèle (sinon le nombre commun)
        try:
            n = int(counts.get(orig) or copies)
        except (TypeError, ValueError):
            n = copies
        per[r] = per.get(r, 0) + max(1, min(n, 50))
    if sum(per.values()) > MAX_ITEMS:
        raise ValueError(f'Maximum {MAX_ITEMS} pièces par disposition.')
    return list(per), per


def _build(data):
    paths, per = _parse(data)
    mode = 'box' if data.get('mode') == 'box' else 'shape'
    meshes, items, shapes = {}, [], {}
    for p in paths:
        m = _load(p)
        meshes[p] = m
        base = _item_from_mesh(p, m)
        if mode == 'shape':
            from shapely import affinity
            geom = footprint(m)
            x0, y0, _, _ = _bounds(geom)
            geom = affinity.translate(geom, -x0, -y0)
            shapes[p] = shape_info(m, geom, max_edges=max(0, min(500, 20000 // max(1, len(paths)))))
        for c in range(per[p]):
            iid = f'{p}#{c + 1}' if per[p] > 1 else p
            if mode == 'shape':
                items.append({'id': iid, 'poly': geom, 'h': base['h']})
            else:
                items.append(_item_from_mesh(iid, m))
    plate = data.get('plate') or {}
    if mode == 'shape':
        step = 0 if not bool(data.get('rotate', True)) else int(data.get('rotation_step') or 90)
        layout = arrange_shapes(items, plate, margin=data.get('margin', 3.0), step=step)
        layout['shapes'] = shapes
    else:
        layout = arrange(items, plate, margin=data.get('margin', 3.0), rotate=bool(data.get('rotate', True)))
        layout['mode'] = 'box'
    return layout, meshes


def api_plate_arrange():
    if not _owner_ok():
        return jsonify({'error': 'Accès refusé.'}), 403
    try:
        layout, _ = _build(request.get_json(silent=True) or {})
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except (ValueError, TypeError) as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        app_logger.warning('plate arrange: %s', e)
        return jsonify({'error': 'Disposition impossible.'}), 500
    layout['issues'] = check_layout(layout)
    return jsonify({'ok': True, **layout})


def _rotated_extents(mesh, rot):
    """Largeur et profondeur (mm) de la boîte d'un maillage tourné de `rot` degrés (sens horaire) autour de Z."""
    import numpy as np
    v = np.asarray(mesh.vertices, dtype=float)[:, :2]
    r = np.radians(float(rot) % 360.0)
    c, sn = np.cos(r), np.sin(r)
    x = v[:, 0] * c + v[:, 1] * sn
    y = -v[:, 0] * sn + v[:, 1] * c
    return float(x.max() - x.min()), float(y.max() - y.min())


def _server_outline(mesh, rot, cache):
    """Contours (relatifs à la boîte) de la pièce tournée, calculés par le serveur ; l'empreinte non tournée est mise en cache."""
    from shapely import affinity
    key = id(mesh)
    if key not in cache:
        cache[key] = footprint(mesh)
    g = _rot_cw(cache[key], float(rot) % 360.0)
    x0, y0, _, _ = _bounds(g)
    return _rel_rings(affinity.translate(g, -x0, -y0))


def _export_from_layout(data):
    """Export d'une disposition retouchée à la main. Les tailles viennent des maillages (jamais du navigateur) ; la disposition doit être valide."""
    lay = clean_layout(data['layout'])
    idx = int(data.get('plate_index') or lay['plates'][0]['index'])
    plate = next((p for p in lay['plates'] if p['index'] == idx), None)
    if not plate or not plate['placements']:
        raise LookupError('Plateau introuvable.')
    entries, cache, shapes_cache = [], {}, {}
    for a in plate['placements']:
        src = _resolve_paths([_src_id(a['id'])])[0]
        if src not in cache:
            cache[src] = _load(src)
        e = _item_from_mesh(a['id'], cache[src])
        a['w'], a['d'], a['h'] = _rotated_extents(cache[src], a['rot'])[0], _rotated_extents(cache[src], a['rot'])[1], e['h']
        if a.get('outline'):                                       # contour relu sur le maillage (le navigateur ne peut pas tricher)
            a['outline'] = _server_outline(cache[src], a['rot'], shapes_cache)
        entries.append((cache[src], a))
    issues = check_layout({'plate': lay['plate'], 'plates': [plate]})
    if issues:
        return None, issues, idx
    return export_3mf(entries, idx), [], idx


def api_plate_check():
    """Contrôle pur d'une disposition (sortie de plateau, chevauchement, hauteur) : aucun fichier lu, utilisable aussi en démo."""
    if not _owner_ok():
        return jsonify({'error': 'Accès refusé.'}), 403
    try:
        lay = clean_layout(request.get_json(silent=True) or {})
    except (ValueError, TypeError, AttributeError) as e:
        return jsonify({'error': str(e)}), 400
    return jsonify({'ok': True, 'issues': check_layout(lay), 'plate': lay['plate']})


def api_plate_rotate():
    """Taille et contour d'une pièce tournée de `rot` degrés (sens horaire) : l'éditeur ne calcule jamais la géométrie lui-même."""
    if not _owner_ok():
        return jsonify({'error': 'Accès refusé.'}), 403
    data = request.get_json(silent=True) or {}
    try:
        rot = float(data.get('rot', 0)) % 360.0
        if rot != rot or abs(rot) == float('inf'):
            raise ValueError('Angle invalide.')
        src = _resolve_paths([_src_id(data.get('id', ''))])[0]
        mesh = _load(src)
        w, d = _rotated_extents(mesh, rot)
        return jsonify({'ok': True, 'rot': round(rot, 3), 'w': round(w, 3), 'd': round(d, 3), 'h': _item_from_mesh('x', mesh)['h'],
                        'outline': _server_outline(mesh, rot, {})})
    except LookupError as e:
        return jsonify({'error': str(e)}), 404
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except (ValueError, TypeError, AttributeError) as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        app_logger.warning('plate rotate: %s', e)
        return jsonify({'error': 'Rotation impossible.'}), 500


def api_plate_export():
    if not _owner_ok() or _demo_ok():
        return jsonify({'error': 'Accès refusé.'}), 403
    data = request.get_json(silent=True) or {}
    try:
        if data.get('layout'):
            blob, issues, idx = _export_from_layout(data)
            if issues:
                return jsonify({'error': 'La disposition a des problèmes : corrigez-les avant l\'export.', 'issues': issues}), 400
        else:
            layout, meshes = _build(data)
            idx = int(data.get('plate_index') or 1)
            plate = next((p for p in layout['plates'] if p['index'] == idx), None)
            if not plate:
                return jsonify({'error': 'Plateau introuvable.'}), 404
            entries = []
            for pl in plate['placements']:
                entries.append((meshes[_src_id(pl['id'])], pl))
            blob = export_3mf(entries, idx)
    except LookupError as e:
        return jsonify({'error': str(e)}), 404
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except (ValueError, TypeError, AttributeError) as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        app_logger.warning('plate export: %s', e)
        return jsonify({'error': 'Export impossible.'}), 500
    return send_file(io.BytesIO(blob), mimetype='model/3mf', as_attachment=True, download_name=f'plateau-{idx}.3mf')


_ROUTES = (
    ('/api/plate/arrange', ['POST'], 'api_plate_arrange', ('login_required', )),
    ('/api/plate/check', ['POST'], 'api_plate_check', ('login_required', )),
    ('/api/plate/rotate', ['POST'], 'api_plate_rotate', ('login_required', )),
    ('/api/plate/export', ['POST'], 'api_plate_export', ('login_required', )),
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
