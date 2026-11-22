"""Stellio — plugin signé « Séparer par couleur » (catalogue stellio-plugins, 1.2.0)

Un 3MF multicolore (Bambu / Orca / PrusaSlicer, matières 3MF, peinture par triangle) → un NOUVEAU 3MF avec un plateau par couleur.
La pièce garde sa position sur chaque plateau et chaque objet porte sa couleur. Le fichier d'origine n'est jamais modifié.
Plugin du catalogue qui déclare `host` : il s'exécute DANS Stellio, donc n'est installé que signé par une clé de confiance (voir docs/plugins.md).
Routes dans l'espace réservé aux plugins : /api/x/split-color/… ; page : split.html (cadre isolé, écriture via le pont `stellio.api(..., 'json', {method:'POST'})`).
"""
import base64
import io
import math
import os
import re
import zipfile
from xml.sax.saxutils import quoteattr

_REQUIRED = (
    'DATA_DIR',
    '_is_path_within_sources',
    '_smb_kwargs_for_path',
    '_resolve_3mf_plate_mesh',
    '_thumb_base_rgb',
    'app',
    'app_logger',
    'get_db',
    'invalidate_cache',
    'jsonify',
    'login_required',
    'np',
    'request',
    'session',
    'smbclient',
)
_OPTIONAL = ('CACHE_FILE', '_read_cache_json_safe', '_wv_dialog')
_OVERRIDABLE = ("os", )

_MAIN = {}
DATA_DIR = None
_is_path_within_sources = None
_smb_kwargs_for_path = None
_resolve_3mf_plate_mesh = None
_thumb_base_rgb = None
app = None
app_logger = None
get_db = None
invalidate_cache = None
jsonify = None
login_required = None
np = None
request = None
session = None
smbclient = None
CACHE_FILE = None
_read_cache_json_safe = None
_wv_dialog = None

PLATE_GAP = 0.2   # écart logique entre plateaux dans l'espace Bambu (20 % de la taille du plateau)
MAX_COLORS = 24

def _plate_columns(count):
    """Nombre de colonnes de la grille de plateaux (même règle que Bambu Studio)."""
    value = math.sqrt(count)
    rounded = round(value)
    return rounded + 1 if value > rounded else max(1, rounded)


def _plate_origin(index, count, bed_w, bed_d):
    cols = _plate_columns(count)
    row, col = divmod(index, cols)
    return col * bed_w * (1 + PLATE_GAP), -row * bed_d * (1 + PLATE_GAP)


def _safe_name(path):
    base = os.path.splitext(os.path.basename(path))[0]
    return re.sub(r'[\x00-\x1f<>]', '', base).strip() or 'piece'


def _repair_core(vertices, faces, max_loops=4000):
    """Répare un maillage avant livraison : soude les sommets, retire les faces dégénérées ou en double, referme les trous
    (chaque bord ouvert est comblé par un éventail depuis son centre, dans le bon sens), oriente le volume vers l'extérieur.
    Renvoie (sommets, faces, {'filled': trous refermés, 'open': arêtes encore ouvertes, 'nonmanifold': arêtes partagées par > 2 faces})."""
    v = np.asarray(vertices, dtype=float)
    f = np.asarray(faces, dtype=np.int64).reshape(-1, 3)
    if len(f) == 0:
        return v, f, {'filled': 0, 'open': 0, 'nonmanifold': 0}
    uniq, inv = np.unique(np.round(v, 4), axis=0, return_inverse=True)
    f = np.asarray(inv).reshape(-1)[f]
    v = uniq
    f = f[(f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])]
    if len(f):
        _, first = np.unique(np.sort(f, axis=1), axis=0, return_index=True)
        f = f[np.sort(first)]
        area = np.linalg.norm(np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]), axis=1)
        f = f[area > 1e-12]
    de = {}
    for a, b, c in f.tolist():
        for e in ((a, b), (b, c), (c, a)):
            de[e] = de.get(e, 0) + 1
    nxt = {}
    for (a, b), n in de.items():
        if (b, a) not in de:
            nxt.setdefault(b, []).append(a)       # bord ouvert a→b : le comblement le parcourt dans le sens b→a
    new_v, new_f, filled = [], [], 0
    base = len(v)
    while nxt and filled < max_loops:
        start = next(iter(nxt))
        loop, cur = [start], start
        while True:
            outs = nxt.get(cur)
            if not outs:
                loop = None
                break
            nx = outs.pop()
            if not outs:
                del nxt[cur]
            if nx == start:
                break
            loop.append(nx)
            cur = nx
            if len(loop) > 200000:
                loop = None
                break
        if loop is None or len(loop) < 3:
            nxt.pop(start, None)
            continue
        if len(loop) == 3:
            new_f.append(loop)
        else:
            c = v[loop].mean(axis=0)
            ci = base + len(new_v)
            new_v.append(c)
            for i in range(len(loop)):
                new_f.append([ci, loop[i], loop[(i + 1) % len(loop)]])
        filled += 1
    if new_v:
        v = np.vstack([v, np.asarray(new_v)])
    if new_f:
        f = np.vstack([f, np.asarray(new_f, dtype=np.int64)])
    if len(f):
        tri = v[f]
        vol = float(np.einsum('ij,ij->', tri[:, 0], np.cross(tri[:, 1], tri[:, 2])) / 6.0)
        if vol < 0:
            f = f[:, ::-1].copy()
    cnt = {}
    for a, b, c in f.tolist():
        for e in ((a, b), (b, c), (c, a)):
            k = e if e[0] < e[1] else (e[1], e[0])
            cnt[k] = cnt.get(k, 0) + 1
    return v, f, {'filled': filled, 'open': sum(1 for n in cnt.values() if n == 1), 'nonmanifold': sum(1 for n in cnt.values() if n > 2)}


def _edge_stats(v, f):
    cnt = {}
    for a, b, c in np.asarray(f).tolist():
        for e in ((a, b), (b, c), (c, a)):
            k = e if e[0] < e[1] else (e[1], e[0])
            cnt[k] = cnt.get(k, 0) + 1
    return {'open': sum(1 for n in cnt.values() if n == 1), 'nonmanifold': sum(1 for n in cnt.values() if n > 2)}


def _repair_mesh(vertices, faces, max_loops=4000):
    """Répare un maillage (voir _repair_core) puis, s'il reste des arêtes ouvertes ou partagées par plus de 2 faces (contours pincés
    de surfaces peintes), termine avec pymeshfix (livré avec Stellio) : le résultat est un volume fermé, orienté vers l'extérieur."""
    v, f, st = _repair_core(vertices, faces, max_loops)
    if (st['open'] or st['nonmanifold']) and len(f) >= 4:
        try:
            import pymeshfix
            mf = pymeshfix.MeshFix(np.ascontiguousarray(v, dtype=float), np.ascontiguousarray(f, dtype=np.int32))
            mf.repair(joincomp=False, remove_smallest_components=False)
            v2, f2 = np.asarray(mf.points, dtype=float), np.asarray(mf.faces, dtype=np.int64).reshape(-1, 3)
            if len(f2) >= 4:
                tri = v2[f2]
                if float(np.einsum('ij,ij->', tri[:, 0], np.cross(tri[:, 1], tri[:, 2])) / 6.0) < 0:
                    f2 = f2[:, ::-1].copy()
                es = _edge_stats(v2, f2)
                if es['open'] + es['nonmanifold'] < st['open'] + st['nonmanifold']:
                    v, f = v2, f2
                    st = {'filled': st['filled'], 'open': es['open'], 'nonmanifold': es['nonmanifold']}
        except Exception as e:
            try:
                app_logger.info(f"[Séparation couleur] pymeshfix indisponible : {e}")
            except Exception:
                pass
    return v, f, st


def _components(faces):
    """Composantes connexes d'un maillage (faces reliées par un sommet commun) : liste de tableaux d'indices de faces."""
    f = np.asarray(faces, dtype=np.int64).reshape(-1, 3)
    n = int(f.max()) + 1 if len(f) else 0
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b, c in f.tolist():
        ra, rb, rc = find(a), find(b), find(c)
        if ra != rb:
            parent[rb] = ra
        if find(rc) != find(ra):
            parent[find(rc)] = find(ra)
    roots = np.array([find(int(x)) for x in f[:, 0]], dtype=np.int64) if len(f) else np.zeros(0, dtype=np.int64)
    out = []
    for r in np.unique(roots):
        out.append(np.nonzero(roots == r)[0])
    return out


def _pack(sizes, bed_w, gap=6.0):
    """Range des rectangles (largeur, profondeur) en rangées, sans chevauchement. Renvoie ([(x, y) coin bas-gauche], largeur, profondeur) ;
    l'ensemble est ensuite centré sur le plateau par l'appelant."""
    order = sorted(range(len(sizes)), key=lambda i: -sizes[i][1])
    limit = max(bed_w * 0.9, max((s[0] for s in sizes), default=0))
    pos = [None] * len(sizes)
    x = y = row_h = total_w = 0.0
    for i in order:
        w, d = sizes[i]
        if x > 0 and x + w > limit:
            x, y, row_h = 0.0, y + row_h + gap, 0.0
        pos[i] = (x, y)
        x += w + gap
        row_h = max(row_h, d)
        total_w = max(total_w, x - gap)
    return pos, total_w, y + row_h


def _rot_to_down(d):
    """Rotation envoyant le vecteur unitaire d vers -z."""
    d = np.asarray(d, dtype=float)
    d = d / (np.linalg.norm(d) or 1.0)
    t = np.array([0.0, 0.0, -1.0])
    c = float(np.dot(d, t))
    if c > 0.999999:
        return np.eye(3)
    if c < -0.999999:
        return np.diag([1.0, -1.0, -1.0])
    ax = np.cross(d, t)
    k = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + k + k @ k / (1.0 + c)


def _overhang_area(v, f, R):
    """Aire (mm²) des faces en surplomb (> 45°) une fois la pièce tournée par R et posée à z = 0 ; la face posée sur le plateau n'en fait pas partie."""
    w = v @ R.T
    z0 = w[:, 2].min()
    tri = w[f]
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ar = np.linalg.norm(nrm, axis=1) / 2.0
    nz = nrm[:, 2] / (2.0 * ar + 1e-12)
    low = tri[:, :, 2].max(axis=1) - z0 < 0.2
    return float(ar[(nz < -0.7071) & ~low].sum())


def _orient_for_print(v, f):
    """Pose la pièce sur sa meilleure face (plus grande face plane de l'enveloppe convexe) si cela réduit nettement les surplombs
    (donc les supports) ; sinon elle garde son orientation d'origine. Renvoie les sommets tournés."""
    try:
        from scipy.spatial import ConvexHull
        pts = v[np.unique(f)]
        hull = ConvexHull(pts[::max(1, len(pts) // 60000)])
        eq = hull.equations
        simp = hull.simplices
        tri = pts[::max(1, len(pts) // 60000)][simp]
        area = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) / 2.0
        cand, seen = [], []
        for i in np.argsort(-area):
            n = eq[i, :3]
            if any(np.dot(n, q) > 0.985 for q in seen):
                continue
            seen.append(n)
            cand.append(n)
            if len(cand) >= 8:
                break
        base = _overhang_area(v, f, np.eye(3))
        best, best_s = np.eye(3), base
        for n in cand:
            R = _rot_to_down(-n)
            sc = _overhang_area(v, f, R)
            if sc < best_s:
                best, best_s = R, sc
        if best_s < 0.7 * base:
            return v @ best.T
    except Exception:
        pass
    return v


def _arrange(shells, bed_w, bed_d):
    """shells = [(sommets, faces)] d'une couleur → objets prêts pour son plateau : chaque morceau est posé sur le plateau (z = 0) et rangé
    près du centre, sans chevauchement. Renvoie (objets, tient_sur_le_plateau)."""
    items = []
    for v, f in shells:
        v = _orient_for_print(v, f)
        lo, hi = v.min(axis=0), v.max(axis=0)
        items.append((v - np.array([(lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0, lo[2]]), f, float(hi[0] - lo[0]), float(hi[1] - lo[1])))
    pos, tw, td = _pack([(w, d) for _v, _f, w, d in items], bed_w)
    objs = []
    for (v, f, w, d), (px, py) in zip(items, pos):
        objs.append({'vertices': v, 'faces': f, 'cx': bed_w / 2.0 + px + w / 2.0 - tw / 2.0, 'cy': bed_d / 2.0 + py + d / 2.0 - td / 2.0})
    return objs, tw <= bed_w and td <= bed_d


def _drop_pieces(piece, bed_w, bed_d):
    """Une couleur (maillage éventuellement en plusieurs morceaux) → objets réparés, posés au sol et rangés. Renvoie (objets, bilan de réparation, tient)."""
    v0 = np.asarray(piece['vertices'], dtype=float)
    f0 = np.asarray(piece['faces'], dtype=np.int64).reshape(-1, 3)
    stats = {'filled': 0, 'open': 0, 'nonmanifold': 0}
    shells = []
    for idx in _components(f0):
        if len(idx) < 4:
            continue
        used, inv = np.unique(f0[idx], return_inverse=True)
        v, f, st = _repair_mesh(v0[used], inv.reshape(-1, 3))
        for k in stats:
            stats[k] += st[k]
        shells.append((v, f))
    if not shells:
        shells = [(v0, f0)]
    objs, ok = _arrange(shells, bed_w, bed_d)
    return objs, stats, ok


# ── Connecteurs d'emboîtement : un tenon sur la plus petite pièce, le trou correspondant (avec du jeu) dans celle qui la reçoit ──

def _solid(v, f):
    """Manifold (manifold3d, livré avec Stellio) d'un maillage fermé ; None s'il n'est pas utilisable."""
    from manifold3d import Manifold, Mesh
    m = Manifold(Mesh(vert_properties=np.ascontiguousarray(v, dtype=np.float32), tri_verts=np.ascontiguousarray(f, dtype=np.uint32)))
    return None if (m.is_empty() or not str(m.status()).endswith('NoError')) else m


def _unsolid(m):
    mesh = m.to_mesh()
    return np.array(mesh.vert_properties[:, :3], dtype=float), np.array(mesh.tri_verts, dtype=np.int64)


def _regions(mesh, labels):
    """Régions = morceaux d'une même couleur, d'un seul tenant. Renvoie (région par face, couleur de chaque région, sommets soudés par face, coordonnées soudées)."""
    verts = np.asarray(mesh.vertices, dtype=float)
    faces = np.asarray(mesh.faces)
    uniq, inv = np.unique(np.round(verts, 4), axis=0, return_inverse=True)
    f_ids = np.asarray(inv).reshape(-1)[faces]
    region = np.full(len(faces), -1, dtype=np.int64)
    colors = []
    for k in range(int(labels.max()) + 1 if len(labels) else 0):
        idx = np.nonzero(labels == k)[0]
        if not len(idx):
            continue
        for comp in _components(f_ids[idx]):
            if len(comp) < 4:
                continue
            region[idx[comp]] = len(colors)
            colors.append(k)
    return region, colors, f_ids, uniq


def _joints(f_ids, region, coords):
    """Contacts entre régions voisines : liste de {a, b, pts (sommets de la frontière), ca, cb (centres des faces de chaque côté)}."""
    nf = len(f_ids)
    e = np.sort(np.concatenate([f_ids[:, [0, 1]], f_ids[:, [1, 2]], f_ids[:, [2, 0]]]), axis=1)
    owner = np.tile(np.arange(nf), 3)
    key = e[:, 0].astype(np.int64) * (int(f_ids.max()) + 1) + e[:, 1]
    order = np.argsort(key, kind='stable')
    ks, ow, ee = key[order], owner[order], e[order]
    i0 = np.nonzero(ks[1:] == ks[:-1])[0]
    fa, fb = ow[i0], ow[i0 + 1]
    ra, rb = region[fa], region[fb]
    ok = (ra != rb) & (ra >= 0) & (rb >= 0)
    i0, fa, fb, ra, rb = i0[ok], fa[ok], fb[ok], ra[ok], rb[ok]
    lo, hi = np.minimum(ra, rb), np.maximum(ra, rb)
    out = []
    for pair in sorted(set(zip(lo.tolist(), hi.tolist()))):
        m = (lo == pair[0]) & (hi == pair[1])
        edges = ee[i0[m]]
        parent = {}

        def find(x):
            while parent.setdefault(x, x) != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        for a, b in edges.tolist():
            parent[find(a)] = find(b)
        groups = {}
        for j, (a, b) in enumerate(edges.tolist()):
            groups.setdefault(find(a), []).append(j)
        fm_a = np.where(ra[m] == pair[0], fa[m], fb[m])
        fm_b = np.where(ra[m] == pair[0], fb[m], fa[m])
        for js in groups.values():
            js = np.array(js)
            vids = np.unique(edges[js])
            out.append({'a': pair[0], 'b': pair[1], 'pts': coords[vids], 'fa': fm_a[js], 'fb': fm_b[js]})
    return out


def _frame(e1, e2, n):
    """Repère droit (colonnes e1', e2', n) dont l'axe z est n et dont x suit au mieux e1 : le tenon carré s'aligne sur le contact."""
    n = n / (np.linalg.norm(n) or 1.0)
    x = e1 - n * float(np.dot(e1, n))
    if np.linalg.norm(x) < 1e-9:
        x = e2 - n * float(np.dot(e2, n))
    x = x / (np.linalg.norm(x) or 1.0)
    y = np.cross(n, x)
    return np.column_stack([x, y, n])


def _place(m, r, c):
    mat = np.zeros((3, 4))
    mat[:, :3] = r
    mat[:, 3] = c
    return m.transform(mat)


def _square_peg(side, length, embed, bevel):
    """Tenon carré le long de +z : enfoncé de `embed` dans la pièce porteuse, dépasse de `length`, extrémité biseautée."""
    from manifold3d import Manifold, CrossSection
    sq = CrossSection.square([side, side], True)
    body = Manifold.extrude(sq, embed + length - bevel + 0.05).translate([0, 0, -embed])     # léger recouvrement avec l'embout : une seule pièce
    tip = Manifold.extrude(sq, bevel, 0, 0.0, ((side - 2 * bevel) / side, (side - 2 * bevel) / side)).translate([0, 0, length - bevel])
    return body + tip


def _square_hole(side, depth, back):
    from manifold3d import Manifold, CrossSection
    return Manifold.extrude(CrossSection.square([side, side], True), depth + back).translate([0, 0, -back])


def add_connectors(solids, joints, centers, size=0.0, length=0.0, clearance=0.2):
    """Pour chaque contact entre deux pièces : un tenon CARRÉ, soudé à la plus petite pièce (il n'en est pas détachable), et le trou
    correspondant (jeu `clearance`) dans celle qui la reçoit. Le côté s'adapte à la taille du contact (size = 0), la longueur au côté (length = 0).
    solids : {région: Manifold}, mis à jour. Renvoie (nombre de tenons, nombre de contacts ignorés)."""
    made, skipped = 0, 0
    for jn in sorted(joints, key=lambda j: -len(j['pts'])):
        a, b = jn['a'], jn['b']
        if a not in solids or b not in solids or len(jn['pts']) < 3:
            continue
        P = jn['pts']
        c = P.mean(axis=0)
        _u, _s, vt = np.linalg.svd(P - c, full_matrices=False)
        n = vt[2] / (np.linalg.norm(vt[2]) or 1.0)
        e1, e2 = vt[0], vt[1]
        ext1 = float(np.ptp((P - c) @ e1)); ext2 = float(np.ptp((P - c) @ e2))
        ca = centers[jn['fa']].mean(axis=0); cb = centers[jn['fb']].mean(axis=0)
        if float(np.dot(n, cb - ca)) < 0:
            n = -n                                         # n va de la région a vers la région b
        va, vb = solids[a].volume(), solids[b].volume()
        owner, recv, direction = (a, b, n) if va <= vb else (b, a, -n)   # tenon sur la plus petite pièce, trou dans l'autre
        frame = _frame(e1, e2, direction)
        base = float(size) if size and size > 0 else min(max(0.35 * min(ext1, ext2), 2.0), 0.55 * min(ext1, ext2), 14.0)
        done = False
        for k in (1.0, 0.7, 0.5):
            side = base * k
            if side < 1.2 or min(ext1, ext2) < side + 0.8:
                continue
            ln = float(length) if length and length > 0 else min(max(side * 1.1, 3.0), 12.0)
            embed = max(2.0, ln * 0.6)
            bevel = min(0.6, side / 4.0)
            count = max(1, min(3, int(ext1 // (2.6 * side))))
            offs = [(i - (count - 1) / 2.0) * (ext1 / count) for i in range(count)]
            good = 0
            for off in offs:
                spot = c + e1 * off
                peg = _place(_square_peg(side, ln, embed, bevel), frame, spot)
                hole = _place(_square_hole(side + 2 * clearance, ln + 0.5, 0.4), frame, spot)
                p_in = _place(_square_hole(side * 0.9, embed, 0.0).translate([0, 0, -embed]), frame, spot)
                p_out = _place(_square_hole(side + 2 * clearance, ln + 0.4, 0.0), frame, spot)
                fi, fo = (solids[owner] ^ p_in).volume() / max(p_in.volume(), 1e-9), (solids[recv] ^ p_out).volume() / max(p_out.volume(), 1e-9)
                if fi < 0.9 or fo < 0.9:
                    continue
                solids[owner] = solids[owner] + peg
                solids[recv] = solids[recv] - hole
                good += 1
            if good:
                made += good
                done = True
                break
        if not done:
            skipped += 1
    return made, skipped


def _bbox_overlap(a, b, tol=0.5):
    return bool(np.all(np.asarray(a[:3]) <= np.asarray(b[3:]) + tol) and np.all(np.asarray(b[:3]) <= np.asarray(a[3:]) + tol))


def overlap_connectors(solids, region_color, size=0.0, length=0.0, clearance=0.2, min_volume=2.0):
    """Pièces de couleurs différentes qui s'interpénètrent (une corne enfoncée dans la tête…) : la plus petite est coupée à la surface de l'autre
    (elle ne la traverse plus), puis un tenon CARRÉ, soudé à sa face de contact, entre dans un trou creusé dans la grande pièce (avec du jeu).
    solids : {région: Manifold}, mis à jour. Renvoie (tenons créés, contacts ignorés)."""
    ids = sorted(solids)
    boxes = {r: solids[r].bounding_box() for r in ids}
    pairs = []
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if region_color[a] == region_color[b] or not _bbox_overlap(boxes[a], boxes[b]):
                continue
            inter = solids[a] ^ solids[b]
            vol = inter.volume()
            if vol >= min_volume:
                pairs.append((vol, a, b, inter))
    made, skipped = 0, 0
    for vol, a, b, inter in sorted(pairs, key=lambda x: -x[0]):
        small, big = (a, b) if solids[a].volume() <= solids[b].volume() else (b, a)
        if vol > 0.3 * solids[small].volume():             # corps largement imbriqués : on garde leurs formes intactes
            skipped += 1
            continue
        pts = np.array(inter.to_mesh().vert_properties[:, :3], dtype=float)
        c = pts.mean(axis=0)
        sm = np.array(solids[small].to_mesh().vert_properties[:, :3], dtype=float)
        n = c - sm.mean(axis=0)
        if np.linalg.norm(n) < 1e-6:
            skipped += 1
            continue
        n = n / np.linalg.norm(n)
        proj = (pts - c) @ n
        t_lo, t_hi = float(proj.min()), float(proj.max())
        plane = (pts - c) - np.outer(proj, n)
        _u, _s, vt = np.linalg.svd(plane - plane.mean(axis=0), full_matrices=False)
        e1, e2 = vt[0] - n * float(vt[0] @ n), vt[1] - n * float(vt[1] @ n)
        e1 = e1 / (np.linalg.norm(e1) or 1.0)
        e2 = np.cross(n, e1)
        ext1 = float(np.ptp(plane @ e1)); ext2 = float(np.ptp(plane @ e2))
        thick = t_hi - t_lo
        cut = solids[small] - solids[big]                 # la petite pièce ne traverse plus la grande
        if cut.is_empty() or cut.volume() < 0.5 * solids[small].volume() * 0.1:
            skipped += 1
            continue
        base = float(size) if size and size > 0 else min(max(0.35 * min(ext1, ext2), 2.5), 14.0)
        # positions candidates : sommets de la zone d'interpénétration proches de la face d'entrée, du centre vers l'extérieur
        near = pts[proj <= t_lo + 0.3 * max(thick, 1e-6)]
        if len(near) < 3:
            near = pts
        near = near[np.argsort(np.linalg.norm(near - c, axis=1))][::max(1, len(near) // 40)][:40]
        done = False
        for k in (1.0, 0.7, 0.5):
            side = base * k
            ln = float(length) if length and length > 0 else min(max(side * 1.1, 3.0), 12.0)
            if side < 1.4 or min(ext1, ext2) < side + 1.0:
                continue
            embed = max(2.0, ln * 0.6)
            bevel = min(0.6, side / 4.0)
            frame = _frame(e1, e2, n)
            good, cur_small, cur_big, placed = 0, cut, solids[big], []
            for spot in near:
                if any(np.linalg.norm(spot - q) < 2.6 * side for q in placed):
                    continue
                peg = _place(_square_peg(side, ln, embed, bevel), frame, spot)
                hole = _place(_square_hole(side + 2 * clearance, ln + 0.5, 0.4), frame, spot)
                p_in = _place(_square_hole(side * 0.9, embed, 0.0).translate([0, 0, -embed]), frame, spot)
                p_out = _place(_square_hole(side + 2 * clearance, ln + 0.4, 0.0), frame, spot)
                fi = (cur_small ^ p_in).volume() / max(p_in.volume(), 1e-9)
                fo = (cur_big ^ p_out).volume() / max(p_out.volume(), 1e-9)
                if fi < 0.7 or fo < 0.6:
                    continue
                cur_small = cur_small + peg
                cur_big = cur_big - hole
                placed.append(spot)
                good += 1
                if good >= 2:
                    break
            if good:
                solids[small], solids[big] = cur_small, cur_big
                made += good
                done = True
                break
        if not done:
            skipped += 1
    return made, skipped


def _group_shells(shells, gap):
    """Regroupe les morceaux d'une même couleur qui se touchent presque (distance < gap mm) : ils restent ensemble, dans leurs positions
    d'origine, comme UNE pièce. gap = 0 : chaque morceau séparé reste une pièce à part. Renvoie une liste de (sommets, faces)."""
    n = len(shells)
    if n <= 1 or gap <= 0:
        return list(shells)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    boxes = [(v.min(axis=0), v.max(axis=0)) for v, _f in shells]
    trees = {}
    try:
        from scipy.spatial import cKDTree
    except Exception:
        cKDTree = None
    for i in range(n):
        for j in range(i + 1, n):
            if find(i) == find(j):
                continue
            lo = np.maximum(boxes[i][0], boxes[j][0]); hi = np.minimum(boxes[i][1], boxes[j][1])
            d = np.maximum(lo - hi, 0.0)
            if float(np.linalg.norm(d)) >= gap:
                continue                                          # boîtes englobantes trop éloignées
            if cKDTree is not None and n <= 600:
                for q in (i, j):
                    if q not in trees:
                        trees[q] = cKDTree(shells[q][0])
                small, big = (i, j) if len(shells[i][0]) <= len(shells[j][0]) else (j, i)
                dist = float(trees[big].query(shells[small][0], k=1)[0].min())
                if dist >= gap:
                    continue
            parent[find(j)] = find(i)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    out = []
    for idxs in groups.values():
        vs, fs, off = [], [], 0
        for i in idxs:
            v, f = shells[i]
            vs.append(v)
            fs.append(f + off)
            off += len(v)
        out.append((np.vstack(vs), np.vstack(fs)))
    return out


def _bodies(f_ids):
    """Corps d'un seul tenon (faces reliées par un sommet soudé) : liste de tableaux d'indices de faces (scipy, rapide)."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    n = int(f_ids.max()) + 1
    a = np.concatenate([f_ids[:, 0], f_ids[:, 1]]); b = np.concatenate([f_ids[:, 1], f_ids[:, 2]])
    _k, lab = connected_components(coo_matrix((np.ones(len(a), dtype=np.int8), (a, b)), shape=(n, n)), directed=False)
    fl = lab[f_ids[:, 0]]
    order = np.argsort(fl, kind='stable')
    cuts = np.nonzero(np.diff(fl[order]))[0] + 1
    return np.split(order, cuts)


def _absorb_strays(labels, f_ids, frac=0.006, min_faces=80, verts=None, faces=None, tiny_volume=40.0):
    """Un corps déjà fermé et (presque) monocolore reste ENTIER, avec sa couleur dominante : quelques faces d'une autre couleur
    (franges de peinture) ne le découpent pas. Renvoie (étiquettes corrigées, corps réellement multicolores)."""
    labels = labels.copy()
    mixed = []
    for comp in _bodies(f_ids):
        cnt = np.bincount(labels[comp])
        nz = np.nonzero(cnt)[0]
        if len(nz) <= 1:
            continue
        main = int(cnt.argmax())
        for k in nz:
            if k != main and cnt[k] < max(min_faces, frac * len(comp)):
                labels[comp[labels[comp] == k]] = main
        for k in np.unique(labels[comp]):                  # îlots minuscules d'une couleur dans un même corps : absorbés aussi
            if k == main:
                continue
            idx = comp[labels[comp] == k]
            for part in _components(f_ids[idx]):
                if len(part) < min_faces:
                    labels[idx[part]] = main
        if len(np.unique(labels[comp])) > 1 and verts is not None:
            t = verts[faces[comp]]                          # volume (mm³) du corps : trop petit pour être coupé en deux pièces imprimables
            vol = abs(float(np.einsum('ij,ij->', t[:, 0], np.cross(t[:, 1], t[:, 2])) / 6.0))
            if vol < tiny_volume:
                u = np.unique(labels[comp])
                cnt2 = np.bincount(labels[comp], minlength=int(u.max()) + 1)
                labels[comp] = int(cnt2.argmax())           # petit corps (griffe…) : une seule pièce, couleur dominante
        if len(np.unique(labels[comp])) > 1:
            mixed.append(comp)
    return labels, mixed


def _split_body_by_planes(verts, faces, f_ids, coords, labels, comp):
    """Corps peint de plusieurs couleurs : on coupe le VOLUME plein par un plan passant par la frontière de chaque zone (coupe plane, pièces pleines
    et non des coques creuses). {couleur: (sommets, faces)} ; None si la frontière n'est pas assez plane (on retombe alors sur les coques)."""
    used, inv = np.unique(faces[comp], return_inverse=True)
    v, f, _st = _repair_mesh(verts[used], inv.reshape(-1, 3))
    S = _solid(v, f)
    if S is None:
        return None
    labs = labels[comp]
    ks = [int(k) for k in np.unique(labs)]
    ks.sort(key=lambda k: -int((labs == k).sum()))
    remaining, out, down = S, {}, {}
    for k in ks[1:]:
        fk, fo = comp[labs == k], comp[labs != k]
        bd = np.array(sorted(set(f_ids[fk].ravel().tolist()) & set(f_ids[fo].ravel().tolist())))
        if len(bd) < 3:
            return None
        P = coords[bd]
        c = P.mean(axis=0)
        _u, sv, vt = np.linalg.svd(P - c, full_matrices=False)
        n = vt[2] / (np.linalg.norm(vt[2]) or 1.0)
        if sv[2] > 0.15 * sv[0]:
            return None
        side = float(np.dot(verts[faces[fk]].reshape(-1, 3).mean(axis=0) - c, n))
        if side < 0:
            n = -n
        above, below = remaining.split_by_plane(n.tolist(), float(np.dot(n, c)))
        if above.is_empty() or below.is_empty():
            return None
        if above.volume() < 8.0:                           # reflet minuscule : on creuse un peu plus pour avoir au moins 0,5 mm d'épaisseur (imprimable)
            pa = np.array(above.to_mesh().vert_properties[:, :3], dtype=float)
            depth = float((pa @ n).max() - np.dot(n, c))
            if depth < 0.5:
                a2, b2 = remaining.split_by_plane(n.tolist(), float(np.dot(n, c)) - (0.5 - depth))
                if not a2.is_empty() and not b2.is_empty():
                    above, below = a2, b2
        out[k], remaining = above, below
        down[k] = -n                                       # sa face de coupe (plane) vers le plateau
    out[ks[0]] = remaining
    return {k: _unsolid(m) for k, m in out.items()}, down


def _rot_down(d):
    """Matrice de rotation qui amène le vecteur d sur -Z (la face de coupe vers le plateau)."""
    a = np.asarray(d, dtype=float); a = a / (np.linalg.norm(a) or 1.0)
    b = np.array([0.0, 0.0, -1.0])
    c = float(a @ b)
    if c > 1 - 1e-9:
        return np.eye(3)
    if c < -1 + 1e-9:
        return np.diag([1.0, -1.0, -1.0])
    v = np.cross(a, b)
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + k + k @ k / (1 + c)


def _trim_rim(v, f, max_frac=0.02, max_faces=250000):
    """Bord vif plan (orbite d'un œil, ouverture d'un creux) : son pourtour est déchiqueté dans le modèle d'origine. On le coupe par un plan
    juste en dessous du bruit : face droite et lisse. Renvoie ((sommets, faces), direction de la face coupée) ou None."""
    if len(f) > max_faces:
        return None
    import trimesh
    m = trimesh.Trimesh(v, f, process=False)
    sel = m.face_adjacency_angles > np.radians(40)
    vs = np.unique(m.face_adjacency_edges[sel])
    if len(vs) < 40:
        return None
    P = v[vs]
    c = P.mean(axis=0)
    _u, sv, vt = np.linalg.svd(P - c, full_matrices=False)
    if sv[2] > 0.08 * sv[0] or float(np.ptp((P - c) @ vt[0])) < 6.0:
        return None
    n = vt[2] / (np.linalg.norm(vt[2]) or 1.0)
    if float(np.dot(v.mean(axis=0) - c, n)) < 0:
        n = -n                                             # n pointe vers le corps
    S = _solid(v, f)
    if S is None:
        return None
    off = float(np.dot(n, c)) + float(((P - c) @ n).max())
    above, _below = S.split_by_plane(n.tolist(), off)
    if above.is_empty() or S.volume() - above.volume() > max_frac * S.volume():
        return None
    return _unsolid(above), -n


def _bbox_inside(a, b, tol=0.5):
    """Vrai si la boîte `a` est (presque) entièrement contenue dans la boîte `b` : pièce imbriquée dans une autre (pupille dans l'œil)."""
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    return bool(np.all(a[:3] >= b[:3] - tol) and np.all(a[3:] <= b[3:] + tol))


def carve_seats(solids, region_color, clearance=0.15, min_volume=2.0, depth_pct=25.0, spec=None):
    """Deux pièces de couleurs différentes qui s'interpénètrent (œuf dans l'orbite, corne dans la tête…), taillées COMME AU CUTTER :
    la petite pièce est tranchée par un plan plat à sa base (la partie enfouie, cachée, est supprimée) ; la grande est creusée de la forme de ce
    qui reste (agrandie du jeu), avec un fond plan. Au contact : un plan et les parois lisses de la petite pièce, jamais la texture de l'autre.
    Renvoie ({région creusée ou tranchée}, {région tranchée : direction de sa face plane}) ; solids est mis à jour."""
    orig = dict(solids)
    ids = sorted(orig)
    boxes = {r: orig[r].bounding_box() for r in ids}
    touched, down, pegs, pegged = [], {}, 0, set()
    pairs = []
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if region_color[a] == region_color[b] or not _bbox_overlap(boxes[a], boxes[b]):
                continue
            inter = orig[a] ^ orig[b]
            sv = min(orig[a].volume(), orig[b].volume())
            if inter.volume() >= min_volume or (inter.volume() >= 0.5 and sv >= 3.0):   # petites pièces (griffes…) : contact plus faible accepté
                pairs.append((inter.volume(), a, b, inter))
            elif sv >= 3.0 and sv < 60.0:                    # pièce qui ne fait que TOUCHER l'autre (griffe posée sur l'orteil) : contact mesuré en la gonflant de 0,5 mm
                sa, ba = (a, b) if orig[a].volume() <= orig[b].volume() else (b, a)
                bb = np.asarray(boxes[sa], dtype=float); ctr = (bb[:3] + bb[3:]) / 2.0
                grown = orig[sa].translate((-ctr).tolist()).scale([1.0 + 0.5 / max(float((bb[3:] - bb[:3]).min()) / 2.0, 0.5)] * 3).translate(ctr.tolist())
                inter = grown ^ orig[ba]
                if inter.volume() >= 0.3:
                    pairs.append((inter.volume(), a, b, inter))
    for _vol, a, b, inter in sorted(pairs, key=lambda x: -x[0]):          # le plus gros contact d'abord : c'est lui qui reçoit le tenon
        if True:
            small, big = (a, b) if orig[a].volume() <= orig[b].volume() else (b, a)
            pts = np.array(inter.to_mesh().vert_properties[:, :3], dtype=float)
            c = pts.mean(axis=0)
            sm = np.array(solids[small].to_mesh().vert_properties[:, :3], dtype=float)
            n = sm.mean(axis=0) - c                          # sens dans lequel la petite pièce sort de la grande
            if np.linalg.norm(n) < 1e-3:
                continue
            n = n / np.linalg.norm(n)
            pr = (pts - c) @ n
            level = float(np.dot(n, c)) + float(pr.min() + depth_pct / 100.0 * (pr.max() - pr.min()))     # plan à 25 % de l'épaisseur enfouie
            top, _bottom = solids[small].split_by_plane(n.tolist(), level)
            if top.is_empty() or top.volume() < 0.3 * solids[small].volume():
                top = solids[small]                          # trop peu de matière au-dessus du plan : on garde la pièce entière
            else:
                solids[small] = top
                down[small] = -n                             # face plane de la petite pièce = dessous (vers le plateau)
                if small not in touched:
                    touched.append(small)
            bb = np.asarray(top.bounding_box(), dtype=float)
            ctr = (bb[:3] + bb[3:]) / 2.0
            half = float(((bb[3:] - bb[:3]) / 2.0).min())
            f = 1.0 + clearance / max(half, 0.5)
            cutter = top.translate((-ctr).tolist()).scale((f, f, f)).translate(ctr.tolist())
            res = solids[big] - cutter
            if res.is_empty() or res.volume() < 0.2 * solids[big].volume():
                continue
            nested = any(o != small and orig[o].volume() > orig[small].volume() and region_color[o] != region_color[small] and region_color[o] != region_color[big]
                         and _bbox_inside(boxes[small], boxes[o]) for o in ids)
            if spec and small in down and small not in pegged and not nested:   # UN seul tenon par pièce rapportée (corne, œil…), sur son plus gros contact
                pegged.add(small)
                # tenons de positionnement : sur le fond du logement (grande pièce), trou dans la base plane de la petite
                try:
                    res, top, k = _seat_pegs(res, top, n, level, **spec)
                    if k:
                        solids[small] = top
                        pegs += k
                except Exception:
                    pass
            solids[big] = res
            if big not in touched:
                touched.append(big)
    return touched, down, pegs


def _seat_pegs(big, small, n, level, size=0.0, length=0.0, clearance=0.2):
    """Un ou deux tenons carrés plantés dans le fond plan du logement de `big`, et les trous correspondants (avec jeu) dans la base plane de `small`.
    Renvoie (big, small, nombre de tenons)."""
    pts = np.array(small.to_mesh().vert_properties[:, :3], dtype=float)
    base = pts[(pts @ n) - level < (0.4 if np.ptp(pts @ n) > 3.0 else 0.25)]
    if len(base) < 3:
        return big, small, 0
    c0 = base.mean(axis=0)
    c0 = c0 + n * (level - float(c0 @ n))
    _u, _s, vt = np.linalg.svd(base - base.mean(axis=0), full_matrices=False)
    e1, e2 = vt[0] - n * float(vt[0] @ n), vt[1] - n * float(vt[1] @ n)
    e1 = e1 / (np.linalg.norm(e1) or 1.0)
    ext1 = float(np.ptp((base - c0) @ e1)); ext2 = float(np.ptp((base - c0) @ (np.cross(n, e1))))
    side = float(size) if size and size > 0 else min(max(0.4 * min(ext1, ext2), 1.0), 4.0)
    if min(ext1, ext2) < side + 0.9:
        return big, small, 0
    ln = float(length) if length and length > 0 else min(max(side * 1.1, 1.6), 5.0)
    embed, bevel = 1.5, min(0.5, side / 4.0)
    frame = _frame(e1, np.cross(n, e1), n)
    offs = [0.0]                                             # un seul tenon, centré
    made = 0
    for off in offs:
        spot = c0 + e1 * off
        peg = _place(_square_peg(side, ln, embed, bevel), frame, spot)
        hole = _place(_square_hole(side + 2 * clearance, ln + 0.5, 0.3), frame, spot)
        p_in = _place(_square_hole(side * 0.9, embed, 0.0).translate([0, 0, -embed]), frame, spot)
        p_out = _place(_square_hole(side * 0.9, ln * 0.8, 0.0), frame, spot)
        if (big ^ p_in).volume() < 0.7 * p_in.volume() or (small ^ p_out).volume() < 0.7 * p_out.volume():
            continue
        big, small = big + peg, small - hole
        made += 1
    return big, small, made


def _regions_pipeline(mesh, face_rgb, tol, spec, bed_w, bed_d, merge_gap=5.0):
    """Découpe en régions, répare chacune, ajoute les connecteurs demandés, regroupe les morceaux voisins d'une même couleur,
    puis range chaque couleur sur son plateau. Renvoie (objets par couleur {k: [objets]}, bilan de réparation, tient, connecteurs)."""
    labels, colors, _sizes = _group_colors(face_rgb, tol)
    region, region_color, f_ids, coords = _regions(mesh, labels)
    verts = np.asarray(mesh.vertices, dtype=float)
    faces = np.asarray(mesh.faces)
    labels, mixed = _absorb_strays(labels, f_ids, verts=verts, faces=faces)
    region, region_color, f_ids, coords = _regions(mesh, labels)
    stats = {'filled': 0, 'open': 0, 'nonmanifold': 0}
    shells = {}
    orient = {}
    for comp in mixed:
        try:
            res = _split_body_by_planes(verts, faces, f_ids, coords, labels, comp)
            pieces, pdown = res if res else (None, {})
            regs = {}
            for r in np.unique(region[comp]):
                if r >= 0:
                    regs.setdefault(region_color[r], []).append(int(r))
            if pieces is None or any(len(regs.get(k, [])) != 1 for k in pieces) or set(regs) != set(pieces):
                continue
            for k, (v, f) in pieces.items():
                shells[regs[k][0]] = (v, f)
                if k in pdown:
                    orient[regs[k][0]] = pdown[k]
        except Exception as e:
            app_logger.warning(f"[Séparation couleur] coupe plane impossible : {e}")
    for r in range(len(region_color)):
        if r in shells:
            continue
        idx = np.nonzero(region == r)[0]
        used, inv = np.unique(faces[idx], return_inverse=True)
        v, f, st = _repair_mesh(verts[used], inv.reshape(-1, 3))
        for k in stats:
            stats[k] += st[k]
        shells[r] = (v, f)
    fixed_orient = set(orient)
    for r in list(shells):
        if r in orient:
            continue
        try:
            res = _trim_rim(*shells[r])
        except Exception as e:
            app_logger.warning(f"[Séparation couleur] bord non redressé : {e}")
            res = None
        if res:
            shells[r], orient[r] = res
    conn = {'made': 0, 'skipped': 0, 'error': None, 'seats': 0}
    if len(region_color) > 1:
        try:
            solids = {}
            for r, (v, f) in shells.items():
                m = _solid(v, f)
                if m is not None:
                    solids[r] = m
            carved, sdown, pegs = carve_seats(solids, region_color, spec=spec)   # coupes au cutter : base plane de la petite pièce, logement à fond plan, tenons
            conn['seats'] = len(carved)
            conn['made'] = pegs
            changed = set(carved)
            for r, d in sdown.items():
                if r not in fixed_orient:
                    orient[r] = d
            for r in changed:
                shells[r] = _unsolid(solids[r])
        except ImportError:
            conn['error'] = 'manifold3d'
        except Exception as e:
            app_logger.warning(f"[Séparation couleur] logements/connecteurs impossibles : {e}")
            conn['error'] = str(e)
    per_color, fits = {}, True
    for k in range(len(colors)):
        keep, flat = [], []
        for r in range(len(region_color)):
            if region_color[r] != k:
                continue
            v, f = shells[r]
            if r in orient:                                 # pièce à face de coupe plane : posée à plat sur le plateau, hors regroupement
                R = _rot_down(orient[r])
                ctr = v.mean(axis=0)
                flat.append(((v - ctr) @ R.T, f))
                continue
            try:
                from scipy.sparse import coo_matrix
                from scipy.sparse.csgraph import connected_components
                n = len(v)
                lab = connected_components(coo_matrix((np.ones(len(f) * 2, dtype=np.int8), (np.concatenate([f[:, 0], f[:, 1]]), np.concatenate([f[:, 1], f[:, 2]]))), shape=(n, n)), directed=False)[1]
                fl = lab[f[:, 0]]
                for c in np.unique(fl):
                    ff = f[fl == c]
                    vol = abs(float(np.einsum('ij,ij->', v[ff[:, 0]], np.cross(v[ff[:, 1]], v[ff[:, 2]])) / 6.0))
                    if vol > 0.5 or len(ff) > 400:      # éclats de coupe sans volume : écartés
                        if len(np.unique(fl)) == 1:
                            keep.append((v, f))
                        else:
                            u, inv = np.unique(ff, return_inverse=True)
                            keep.append((v[u], inv.reshape(-1, 3)))
            except Exception:
                keep.append((v, f))
        sh = _group_shells(keep, merge_gap) + flat
        if not sh:
            continue
        objs, ok = _arrange(sh, bed_w, bed_d)
        per_color[k] = objs
        fits = fits and ok
    return per_color, stats, fits, conn


def build_3mf(plates, bed_w, bed_d, out_path, plate_names=None):
    """Écrit le 3MF. `plates` = liste de plateaux ; chaque plateau = liste de dict
    {name, vertices (Nx3, centrés en XY, z ≥ 0), faces (Mx3), cx, cy (centre dans le plateau, mm)}."""
    count = len(plates)
    objects_xml, build_xml, config_objects, config_plates, materials_xml = [], [], [], [], []
    obj_id = 0
    filaments = []   # couleurs distinctes, dans l'ordre : le n° de filament d'un objet = sa position ici (1, 2, 3…)
    for pieces in plates:
        for piece in pieces:
            if piece.get('rgb') is not None and tuple(int(x) for x in piece['rgb']) not in filaments:
                filaments.append(tuple(int(x) for x in piece['rgb']))
    for p_idx, pieces in enumerate(plates):
        ox, oy = _plate_origin(p_idx, count, bed_w, bed_d)
        instances = []
        for piece in pieces:
            obj_id += 1
            v = piece['vertices']
            f = piece['faces']
            verts = ''.join(f'<vertex x="{x:.5f}" y="{y:.5f}" z="{z:.5f}"/>' for x, y, z in v)
            tris = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in f)
            name = quoteattr(piece['name'])
            pid = ''
            if piece.get('rgb') is not None:     # couleur de la pièce (séparation par couleur) : matière de base 3MF, lue aussi par Stellio
                mat_id = 100000 + obj_id
                r, g_, b_ = (int(x) for x in piece['rgb'])
                materials_xml.append(f'<basematerials id="{mat_id}"><base name="{r:02X}{g_:02X}{b_:02X}" displaycolor="#{r:02X}{g_:02X}{b_:02X}FF"/></basematerials>')
                pid = f' pid="{mat_id}" pindex="0"'
            objects_xml.append(f'<object id="{obj_id}" name={name}{pid} type="model"><mesh><vertices>{verts}</vertices>'
                               f'<triangles>{tris}</triangles></mesh></object>')
            tx, ty = ox + piece['cx'], oy + piece['cy']
            build_xml.append(f'<item objectid="{obj_id}" transform="1 0 0 0 1 0 0 0 1 {tx:.4f} {ty:.4f} 0" printable="1"/>')
            ext = ''
            if piece.get('rgb') is not None:
                ext = f'<metadata key="extruder" value="{filaments.index(tuple(int(x) for x in piece["rgb"])) + 1}"/>'
            config_objects.append(f'<object id="{obj_id}"><metadata key="name" value={name}/>{ext}</object>')
            instances.append(f'<model_instance><metadata key="object_id" value="{obj_id}"/>'
                             f'<metadata key="instance_id" value="0"/><metadata key="identify_id" value="{obj_id}"/></model_instance>')
        config_plates.append(f'<plate><metadata key="plater_id" value="{p_idx + 1}"/>'
                             f'<metadata key="plater_name" value={quoteattr((plate_names[p_idx] if plate_names and p_idx < len(plate_names) else "") or "")}/><metadata key="locked" value="false"/>'
                             + ''.join(instances) + '</plate>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
             'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" requiredextensions="">\n'
             '<metadata name="Application">Stellio</metadata>\n<metadata name="BambuStudio:3mfVersion">1</metadata>\n'
             '<resources>' + ''.join(materials_xml) + ''.join(objects_xml) + '</resources>\n<build>' + ''.join(build_xml) + '</build>\n</model>')
    config = '<?xml version="1.0" encoding="UTF-8"?>\n<config>' + ''.join(config_objects) + ''.join(config_plates) + '</config>'
    content_types = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
                     '<Default Extension="config" ContentType="text/xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    project = None
    if filaments:
        import json
        w, d = int(round(bed_w)), int(round(bed_d))
        project = json.dumps({'from': 'project', 'filament_colour': ['#%02X%02X%02X' % c for c in filaments],
                              'filament_type': ['PLA'] * len(filaments),
                              'printable_area': ['0x0', f'{w}x0', f'{w}x{d}', f'0x{d}']}, indent=2)
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types)
        zf.writestr('_rels/.rels', rels)
        zf.writestr('3D/3dmodel.model', model)
        zf.writestr('Metadata/model_settings.config', config)
        if project:
            zf.writestr('Metadata/project_settings.config', project)
    return obj_id


def _is_unc(path):
    return path.startswith('//') or path.startswith('\\\\')


def _unc(path):
    return path.replace('\\', '/')


def _clean_filename(name):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', (name or '').strip()).strip('. ')
    if name.lower().endswith('.3mf'):
        name = name[:-4].rstrip('. ')
    return name[:120]


def _dest_dir(paths, source_id, sub_rel):
    """Dossier de sortie : source + sous-dossier choisis dans la fenêtre ; sinon dossier du premier fichier
    (si on peut y écrire) ; sinon dossier de données de Stellio. Les dossiers réseau (SMB) sont acceptés.
    Lève ValueError si le choix est invalide."""
    folder = None
    if source_id:
        conn = get_db()
        try:
            row = conn.execute("SELECT path FROM sources WHERE id = ? AND user_id = ?", (source_id, session['user_id'])).fetchone()
        finally:
            conn.close()
        if not row or not row['path']:
            raise ValueError("Dossier de destination introuvable")
        base = row['path']
        parts = [x for x in (sub_rel or '').replace('\\', '/').strip('/').split('/') if x]
        if any(x in ('.', '..') or re.search(r'[<>:"|?*]', x) for x in parts):
            raise ValueError("Dossier de destination invalide")
        if _is_unc(base):
            folder = '/'.join([_unc(base).rstrip('/')] + parts)
            kw = _smb_kwargs_for_path(session['user_id'], folder)
            if kw is None:
                raise ValueError("Source réseau introuvable pour ce dossier")
            smbclient.makedirs(folder, exist_ok=True, **kw)
        else:
            folder = os.path.join(base, *parts)
            os.makedirs(folder, exist_ok=True)
    if not folder:
        first = paths[0]
        if _is_unc(first):
            folder = _unc(first).rsplit('/', 1)[0]
        else:
            folder = os.path.dirname(first)
            if not (folder and os.path.isdir(folder) and os.access(folder, os.W_OK)):
                folder = os.path.join(DATA_DIR, 'nesting_output')
                os.makedirs(folder, exist_ok=True)
    return folder


def _resolve_dir(source_id, sub_rel):
    """(dossier, parties) d'un sous-dossier d'une source, SANS rien créer. Lève ValueError si le choix est invalide."""
    conn = get_db()
    try:
        row = conn.execute("SELECT path FROM sources WHERE id = ? AND user_id = ?", (source_id, session['user_id'])).fetchone()
    finally:
        conn.close()
    if not row or not row['path']:
        raise ValueError("Source introuvable")
    base = row['path']
    parts = [x for x in (sub_rel or '').replace('\\', '/').strip('/').split('/') if x]
    if any(x in ('.', '..') or re.search(r'[<>:"|?*\x00-\x1f]', x) for x in parts):
        raise ValueError("Dossier invalide")
    if _is_unc(base):
        folder = '/'.join([_unc(base).rstrip('/')] + parts)
        kw = _smb_kwargs_for_path(session['user_id'], folder)
        if kw is None:
            raise ValueError("Source réseau introuvable pour ce dossier")
        return folder, parts, kw
    return os.path.join(base, *parts), parts, None


def api_split_color_folders():
    """Sous-dossiers d'un dossier d'une source (pour choisir où enregistrer, comme pour les téléchargements)."""
    try:
        folder, parts, kw = _resolve_dir(str(request.args.get('source_id') or ''), request.args.get('sub'))
        names = []
        if kw is not None:
            for e in smbclient.scandir(folder, **kw):
                if e.is_dir() and not e.name.startswith(('.', '$')):
                    names.append(e.name)
        else:
            with os.scandir(folder) as it:
                for e in it:
                    if e.is_dir() and not e.name.startswith('.'):
                        names.append(e.name)
        names.sort(key=str.lower)
        return jsonify({"sub": '/'.join(parts), "folders": names[:500], "truncated": len(names) > 500})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app_logger.warning(f"[Séparation couleur] dossiers illisibles : {e}")
        return jsonify({"error": "Dossier illisible"}), 400


def api_split_color_mkdir():
    """Crée un sous-dossier dans une source (un seul niveau à la fois) et renvoie son chemin relatif."""
    data = request.json or {}
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', str(data.get('name') or '')).strip('. ')[:80]
    if not name:
        return jsonify({"error": "Nom de dossier invalide"}), 400
    try:
        _f, parts, _kw = _resolve_dir(str(data.get('source_id') or ''), data.get('sub'))
        folder, parts2, kw = _resolve_dir(str(data.get('source_id') or ''), '/'.join(parts + [name]))
        if kw is not None:
            smbclient.makedirs(folder, exist_ok=True, **kw)
        else:
            os.makedirs(folder, exist_ok=True)
        return jsonify({"ok": True, "sub": '/'.join(parts2)})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app_logger.warning(f"[Séparation couleur] création de dossier impossible : {e}")
        return jsonify({"error": "Création du dossier impossible"}), 400


def _out_path(folder, name, count):
    base = _clean_filename(name) or f'fusion_{count}_pieces'
    unc = _is_unc(folder)
    kw = (_smb_kwargs_for_path(session['user_id'], folder) or {}) if unc else {}
    join = (lambda n: _unc(folder).rstrip('/') + '/' + n) if unc else (lambda n: os.path.join(folder, n))
    exists = (lambda p: smbclient.path.exists(p, **kw)) if unc else os.path.exists
    candidate = join(base + '.3mf')
    n = 2
    while exists(candidate):
        candidate = join(f'{base}_{n}.3mf')
        n += 1
    return candidate


def _write_output(plates, bed_w, bed_d, out_path, plate_names=None):
    if not _is_unc(out_path):
        build_3mf(plates, bed_w, bed_d, out_path, plate_names)
        return
    kw = _smb_kwargs_for_path(session['user_id'], out_path)
    if kw is None:
        raise ValueError("Source réseau introuvable pour ce dossier")
    buf = io.BytesIO()
    build_3mf(plates, bed_w, bed_d, buf, plate_names)
    with smbclient.open_file(out_path, mode='wb', **kw) as fh:
        fh.write(buf.getvalue())


# ── Séparer par couleur (1.2.0) : un 3MF multicolore → un 3MF avec un plateau par couleur ──

def _hex(rgb):
    return '#%02X%02X%02X' % tuple(int(x) for x in rgb)


def _group_colors(face_rgb, tolerance):
    """Regroupe les faces par couleur. Renvoie (étiquette par face, couleurs [(r,g,b)], effectifs).
    tolerance (0-100) : des couleurs proches (distance RVB ≤ tolérance) sont fusionnées dans la plus fréquente."""
    uniq, inv, counts = np.unique(np.asarray(face_rgb, dtype=np.int32), axis=0, return_inverse=True, return_counts=True)
    inv = np.asarray(inv).reshape(-1)
    order = np.argsort(-counts, kind='stable')
    reps, remap = [], np.zeros(len(uniq), dtype=np.int32)
    for i in order:
        target = None
        if tolerance > 0:
            for k, r in enumerate(reps):
                if float(np.linalg.norm(uniq[i] - uniq[r])) <= tolerance:
                    target = k
                    break
        if target is None:
            reps.append(int(i))
            target = len(reps) - 1
        remap[i] = target
    labels = remap[inv]
    sizes = np.bincount(labels, minlength=len(reps))
    return labels, [tuple(int(x) for x in uniq[r]) for r in reps], [int(x) for x in sizes]


def _load_colored_mesh(path):
    """Maillage 3MF de TOUS les plateaux, avec la couleur de chaque face (metadata['stellio_face_rgb'])."""
    if _resolve_3mf_plate_mesh is None:
        raise ValueError("Lecture des couleurs 3MF indisponible")
    if _is_unc(path):
        kw = _smb_kwargs_for_path(session['user_id'], path)
        if kw is None:
            raise ValueError("Source réseau introuvable pour ce fichier")
        with smbclient.open_file(_unc(path), mode='rb', share_access='r', **kw) as fh:
            source = fh.read()
    else:
        source = path
    mesh = _resolve_3mf_plate_mesh(source, None, True, None)
    if mesh is None or len(getattr(mesh, 'faces', [])) == 0:
        raise ValueError("Maillage 3MF vide ou illisible")
    rgb = mesh.metadata.get('stellio_face_rgb') if hasattr(mesh, 'metadata') else None
    if rgb is None or len(rgb) != len(mesh.faces):
        raise ValueError("Ce 3MF ne contient aucune information de couleur")
    return mesh, np.asarray(rgb)


def split_mesh_by_color(mesh, face_rgb, tolerance=0.0):
    """Une pièce par couleur : [{'rgb', 'vertices', 'faces', 'count'}], de la plus grande à la plus petite."""
    labels, colors, sizes = _group_colors(face_rgb, tolerance)
    verts = np.asarray(mesh.vertices, dtype=float)
    faces = np.asarray(mesh.faces)
    out = []
    for k, rgb in enumerate(colors):
        sel = faces[labels == k]
        used, inv = np.unique(sel, return_inverse=True)
        out.append({'rgb': rgb, 'vertices': verts[used], 'faces': inv.reshape(-1, 3), 'count': int(sizes[k]), 'label': k})
    return out


def _preview(pieces, max_tris=30000):
    """Aperçu léger pour la page : triangles de chaque couleur, recentrés et quantifiés en entiers 16 bits (base64).
    Au-delà de `max_tris` au total, chaque couleur est échantillonnée régulièrement (le rendu reste fidèle à l'échelle d'une vignette)."""
    import numpy as np
    allv = np.vstack([np.asarray(p['vertices'], dtype=float) for p in pieces])
    lo, hi = allv.min(axis=0), allv.max(axis=0)
    center = np.array([(lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0, lo[2]])
    half = max(float(np.max(hi - lo)) / 2.0, 1e-6)
    q = 12000.0 / half
    total = sum(len(p['faces']) for p in pieces) or 1
    out = []
    for p in pieces:
        f = np.asarray(p['faces'])
        v = np.asarray(p['vertices'], dtype=float)
        budget = max(300, int(max_tris * len(f) / total))
        if len(f) > budget:
            f = f[np.linspace(0, len(f) - 1, budget).astype(int)]
        tri = np.clip(np.round((v[f] - center) * q), -32000, 32000).astype('<i2')
        out.append({"hex": _hex(p['rgb']), "tris": base64.b64encode(tri.tobytes()).decode('ascii')})
    return {"q": q, "extent": [float(x) for x in (hi - lo)], "pieces": out}


def _preview_or_none(pieces):
    try:
        return _preview(pieces)
    except Exception as e:
        app_logger.warning(f"[Séparation couleur] aperçu indisponible : {e}")
        return None


def api_split_color_3mf():
    data = request.json or {}
    path = data.get('path')
    if not isinstance(path, str) or not path:
        return jsonify({"error": "Sélectionnez un fichier 3MF"}), 400
    if os.path.splitext(path)[1].lower() != '.3mf':
        return jsonify({"error": "Seuls les fichiers 3MF multicolores sont pris en charge"}), 400
    try:
        bed_w = float(data.get('bed_width') or 220)
        bed_d = float(data.get('bed_height') or 220)
        tol = min(max(float(data.get('tolerance') or 0), 0.0), 100.0)
        use_conn = data.get('connectors') not in (False, 0, '0', 'false')      # tenons de positionnement (actifs par défaut)
        csize = min(max(float(data.get('conn_size') or 0), 0.0), 30.0)
        clen = min(max(float(data.get('conn_length') or 0), 0.0), 30.0)
        mgap = min(max(float(data.get('merge_gap') if data.get('merge_gap') not in (None, '') else 5), 0.0), 500.0)
        cclear = min(max(float(data.get('conn_clearance') if data.get('conn_clearance') not in (None, '') else 0.2), 0.0), 1.0)
    except (TypeError, ValueError):
        return jsonify({"error": "Paramètres invalides"}), 400
    if bed_w < 20 or bed_d < 20:
        return jsonify({"error": "Dimensions de plateau invalides"}), 400
    if not _is_path_within_sources(path, session['user_id']):
        return jsonify({"error": "Fichier hors des sources de la bibliothèque"}), 400
    if not _is_unc(path) and not os.path.exists(path):
        return jsonify({"error": "Fichier introuvable"}), 404
    try:
        mesh, face_rgb = _load_colored_mesh(path)
        pieces = split_mesh_by_color(mesh, face_rgb, tol)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app_logger.warning(f"[Séparation couleur] lecture impossible : {e}")
        return jsonify({"error": f"Lecture du fichier impossible : {e}"}), 500
    default_rgb = None
    try:
        default_rgb = tuple(_thumb_base_rgb()) if _thumb_base_rgb else None
    except Exception:
        default_rgb = None
    total_faces = sum(p['count'] for p in pieces) or 1
    colors = [{"hex": _hex(p['rgb']), "faces": p['count'], "percent": round(100.0 * p['count'] / total_faces, 1),
               "default": default_rgb is not None and tuple(p['rgb']) == default_rgb} for p in pieces]
    if len(pieces) > MAX_COLORS:
        return jsonify({"error": f"Trop de couleurs distinctes ({len(pieces)}, maximum {MAX_COLORS}) : augmentez la tolérance de regroupement",
                        "colors": colors[:MAX_COLORS], "color_count": len(pieces)}), 400
    if data.get('dry_run'):
        return jsonify({"color_count": len(pieces), "colors": colors, "preview": _preview_or_none(pieces) if len(pieces) > 1 else None}), 200
    if len(pieces) < 2:
        return jsonify({"error": "Une seule couleur détectée : rien à séparer", "colors": colors, "color_count": len(pieces)}), 400

    base = _safe_name(path)
    plates, names = [], []
    try:
        spec = {'size': csize, 'length': clen, 'clearance': cclear} if use_conn else None
        per_color, repaired, fits, conn = _regions_pipeline(mesh, face_rgb, tol, spec, bed_w, bed_d, mgap)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app_logger.warning(f"[Séparation couleur] échec : {e}")
        return jsonify({"error": f"Échec de la préparation des pièces : {e}"}), 500
    for p in pieces:
        objs = per_color.get(p['label'])
        if not objs:
            continue
        plate = []
        for j, o in enumerate(objs, 1):
            label = f"{base} {_hex(p['rgb'])}" + (f" ({j})" if len(objs) > 1 else '')
            plate.append({'name': label, 'vertices': o['vertices'], 'faces': o['faces'], 'cx': o['cx'], 'cy': o['cy'], 'rgb': p['rgb']})
        plates.append(plate)
        names.append(_hex(p['rgb']))
    try:
        folder = _dest_dir([path], str(data.get('source_id') or '').strip() or None, data.get('target_subfolder'))
        out_path = _out_path(folder, data.get('filename') or f'{base}_couleurs', len(plates))
        _write_output(plates, bed_w, bed_d, out_path, names)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app_logger.warning(f"[Séparation couleur] échec : {e}")
        return jsonify({"error": f"Échec de la création du fichier 3MF : {e}"}), 500
    try:
        invalidate_cache()
    except Exception:
        pass
    return jsonify({
        "output_path": out_path,
        "output_filename": os.path.basename(_unc(out_path)),
        "plate_count": len(plates),
        "repair": repaired,
        "connectors": conn,
        "colors": colors,
        "preview": _preview_or_none(pieces),
        "too_big": not fits,
    }), 200


def api_split_color_files():
    """Fichiers 3MF de la bibliothèque (cache de Stellio), filtrés par nom : sélecteur de la page du plugin."""
    if session.get('role') == 'viewer':
        return jsonify({"error": "Réservé au compte propriétaire"}), 403
    q = (request.args.get('q') or '').strip().lower()
    files = []
    try:
        data = _read_cache_json_safe() if (CACHE_FILE and _read_cache_json_safe and os.path.exists(CACHE_FILE)) else None
        files = (data or {}).get('files') or []
    except Exception:
        files = []
    out = []
    for f in files:
        p = str(f.get('path') or '')
        name = str(f.get('name') or os.path.basename(p))
        if p.lower().endswith('.3mf') and q in name.lower() and _is_path_within_sources(p, session['user_id']):
            out.append({"path": p, "name": name})
            if len(out) >= 60:
                break
    return jsonify({"files": out})


def _owner_post(fn):
    def wrapper(*a, **k):
        if session.get('role') == 'viewer':
            return jsonify({"error": "Réservé au compte propriétaire"}), 403
        return fn(*a, **k)
    wrapper.__name__ = fn.__name__
    return wrapper


def api_split_color_browse():
    """Ouvre l'explorateur de fichiers de Stellio (application de bureau) pour choisir le dossier d'enregistrement.
    Le dossier doit se trouver dans une source de la bibliothèque : on renvoie la source et le sous-dossier correspondants."""
    try:
        import webview
        dlg = _wv_dialog(webview, 'FOLDER') if _wv_dialog else webview.FOLDER_DIALOG
        result = webview.windows[0].create_file_dialog(dlg)
    except (ImportError, IndexError, AttributeError):
        return jsonify({"error": "L'explorateur n'est disponible que dans l'application de bureau", "code": "no_picker"}), 501
    except Exception as e:
        app_logger.warning(f"[Séparation couleur] explorateur : {e}")
        return jsonify({"error": "Impossible d'ouvrir l'explorateur"}), 500
    folder = (result[0] if result else None)
    if not folder:
        return jsonify({"error": "Annulé", "code": "cancelled"}), 400
    norm = str(folder).replace('\\', '/').rstrip('/')
    conn = get_db()
    try:
        rows = conn.execute("SELECT id, path FROM sources WHERE user_id = ?", (session['user_id'],)).fetchall()
    finally:
        conn.close()
    best = None
    for r in rows:
        base = str(r['path'] or '').replace('\\', '/').rstrip('/')
        if base and (norm.lower() == base.lower() or norm.lower().startswith(base.lower() + '/')):
            if best is None or len(base) > len(best[1]):
                best = (r['id'], base)
    if best is None:
        return jsonify({"error": "Ce dossier n'est dans aucune de tes sources : ajoute-le d'abord comme source, ou choisis un dossier de la liste.", "code": "outside"}), 400
    return jsonify({"source_id": str(best[0]), "sub": norm[len(best[1]):].strip('/'), "path": norm})


_ROUTES = (
    ('/api/x/split-color/files', ['GET'], 'api_split_color_files', ('login_required', )),
    ('/api/x/split-color/folders', ['GET'], 'api_split_color_folders', ('login_required', )),
    ('/api/x/split-color/browse', ['POST'], 'api_split_color_browse', ('login_required', '_owner_post')),
    ('/api/x/split-color/mkdir', ['POST'], 'api_split_color_mkdir', ('login_required', '_owner_post')),
    ('/api/x/split-color/split', ['POST'], 'api_split_color_3mf', ('login_required', '_owner_post')),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"split_color.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = g[d](view)
            g['app'].add_url_rule(rule, endpoint='split_color_' + fname, view_func=view, methods=methods)
    return {}
