"""Stellio — recherche géométrique « pièces similaires » (1.1.7).

Chaque modèle reçoit une EMPREINTE de forme : histogramme D2 (distribution des distances entre paires de points de la surface, normalisé
par l'échelle), proportions de la boîte englobante, compacité (volume de la boîte occupé par la surface) et nombre de triangles (log).
Deux modèles dont les empreintes se ressemblent ont des formes proches, indépendamment de leur taille, de leur position et de leur rotation.
C'est une aide au tri, pas une preuve d'identité : deux pièces différentes de même silhouette peuvent sortir proches.

Index : table `shape_index` (une ligne par fichier, invalidée si la date ou la taille change), construit en tâche de fond (job_manager) pour les
modèles de moins de 60 Mo. `GET /api/similar/status` donne le chiffrage : modèles indexés, durée moyenne par modèle, taille de l'index, durée restante estimée.
Un modèle absent de l'index est calculé à la demande.
"""
import json
import math
import os
import time

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
_OPTIONAL = ('_read_cache_json_safe',)
_OVERRIDABLE = ('os', 'time')

_MAIN = {}
_is_path_within_sources = None
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None
_read_cache_json_safe = None

MESH_EXT = ('.stl', '.obj', '.3mf', '.ply', '.off')
MAX_BYTES = 60 * 1024 * 1024
MAX_INDEX = 5000
BINS = 24
PAIRS = 6000
POINTS = 2500
DEFAULT_LIMIT = 10
MAX_LIMIT = 50


def _np():
    import numpy as np
    return np


def descriptor(vertices, faces, seed=11):
    """Empreinte (liste de floats) invariante à l'échelle, à la position et à la rotation (D2, proportions triées, compacité)."""
    np = _np()
    v = np.asarray(vertices, dtype=float)
    f = np.asarray(faces, dtype=int)
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    cross = np.cross(b - a, c - a)
    area = np.linalg.norm(cross, axis=1) / 2
    total = float(area.sum())
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(f), size=POINTS, p=(area / total) if total > 0 else None)
    r1, r2 = rng.random(POINTS), rng.random(POINTS)
    s = np.sqrt(r1)[:, None]
    pts = a[idx] * (1 - s) + b[idx] * (s * (1 - r2)[:, None]) + c[idx] * (s * r2[:, None])
    i, j = rng.integers(0, POINTS, PAIRS), rng.integers(0, POINTS, PAIRS)
    d = np.linalg.norm(pts[i] - pts[j], axis=1)
    mean = float(d.mean()) or 1.0
    hist, _ = np.histogram(d / mean, bins=BINS, range=(0, 3.0))
    hist = hist / max(1, hist.sum())
    # proportions de la boîte alignée sur les axes principaux (PCA) : indépendantes de l'orientation du modèle
    centered = pts - pts.mean(axis=0)
    _w, axes = np.linalg.eigh(np.cov(centered.T))
    proj = v @ axes
    ext = np.sort(proj.max(axis=0) - proj.min(axis=0))[::-1]
    mx = float(ext[0]) or 1.0
    boxvol = float(ext.prod()) or 1.0
    compact = min(1.0, total / (2 * (ext[0] * ext[1] + ext[1] * ext[2] + ext[0] * ext[2]) or 1.0))
    return [round(float(x), 5) for x in hist] + [round(float(ext[1] / mx), 5), round(float(ext[2] / mx), 5), round(float(compact), 5),
                                                  round(math.log10(len(f) + 1) / 7, 5)]


def distance(d1, d2):
    """Distance entre deux empreintes : L1 sur l'histogramme D2 (poids 0,6) + écart des proportions et de la compacité (poids 0,4)."""
    h = sum(abs(x - y) for x, y in zip(d1[:BINS], d2[:BINS])) / 2          # 0..1
    r = sum(abs(x - y) for x, y in zip(d1[BINS:BINS + 3], d2[BINS:BINS + 3])) / 3
    return round(0.6 * h + 0.4 * r, 5)


def rank(target, candidates, limit=DEFAULT_LIMIT):
    """candidates : {chemin: empreinte}. Retourne [(chemin, distance, similarité %)] du plus proche au plus éloigné."""
    out = sorted(((p, distance(target, d)) for p, d in candidates.items()), key=lambda x: (x[1], x[0]))
    return [{'path': p, 'distance': dist, 'similarity': round(100 * max(0.0, 1 - dist * 2), 1)} for p, dist in out[:limit]]


def _ensure(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS shape_index (user_id INTEGER NOT NULL, path TEXT NOT NULL, mtime REAL, size INTEGER, desc TEXT NOT NULL, ms INTEGER, indexed_at REAL,
            PRIMARY KEY (user_id, path));
        CREATE TABLE IF NOT EXISTS shape_skip (user_id INTEGER NOT NULL, path TEXT NOT NULL, mtime REAL, size INTEGER, reason TEXT, PRIMARY KEY (user_id, path));
    """)


def _norm(p):
    return str(p or '').replace('\\', '/')


def compute_file(path):
    import trimesh
    if os.path.splitext(path)[1].lower() not in MESH_EXT or os.path.getsize(path) > MAX_BYTES:
        raise ValueError('Fichier non indexable.')
    m = trimesh.load(path, force='mesh')
    if m is None or len(m.faces) == 0:
        raise ValueError('Maillage vide.')
    return descriptor(m.vertices, m.faces)


def library_files(uid):
    data = _read_cache_json_safe() if _read_cache_json_safe else None
    out = []
    for f in (data or {}).get('files', []):
        p = f.get('path') or ''
        if os.path.splitext(p)[1].lower() in MESH_EXT and _is_path_within_sources(p, uid):
            out.append({'path': p, 'mtime': f.get('mtime') or 0, 'size': f.get('size') or 0})
    return out[:MAX_INDEX]


def build_index(ctx, uid):
    """Tâche de fond : indexe les modèles nouveaux ou modifiés. Retourne un résumé."""
    files = library_files(uid)
    conn = get_db()
    done = skipped = failed = 0
    try:
        _ensure(conn)
        known = {r['path']: (r['mtime'], r['size']) for r in conn.execute("SELECT path, mtime, size FROM shape_index WHERE user_id = ?", (uid,)).fetchall()}
        skip = {r['path']: (r['mtime'], r['size']) for r in conn.execute("SELECT path, mtime, size FROM shape_skip WHERE user_id = ?", (uid,)).fetchall()}   # illisibles ou trop gros : inutile de les réessayer à chaque indexation
        for i, f in enumerate(files):
            ctx.progress(i, len(files), os.path.basename(f['path']))
            key = _norm(f['path'])
            if known.get(key) == (f['mtime'], f['size']) or skip.get(key) == (f['mtime'], f['size']):
                skipped += 1
                continue
            t0 = time.time()
            try:
                d = compute_file(f['path'])
            except Exception as e:
                failed += 1
                conn.execute("INSERT OR REPLACE INTO shape_skip (user_id, path, mtime, size, reason) VALUES (?,?,?,?,?)", (uid, key, f['mtime'], f['size'], str(e)[:200]))
                conn.commit()
                continue
            conn.execute("DELETE FROM shape_skip WHERE user_id = ? AND path = ?", (uid, key))
            conn.execute("INSERT OR REPLACE INTO shape_index (user_id, path, mtime, size, desc, ms, indexed_at) VALUES (?,?,?,?,?,?,?)",
                         (uid, key, f['mtime'], f['size'], json.dumps(d), int((time.time() - t0) * 1000), time.time()))
            conn.commit()
            done += 1
        live = {_norm(f['path']) for f in files}
        for p in list(known):
            if p not in live:
                conn.execute("DELETE FROM shape_index WHERE user_id = ? AND path = ?", (uid, p))
        for p in list(skip):
            if p not in live:
                conn.execute("DELETE FROM shape_skip WHERE user_id = ? AND path = ?", (uid, p))
        conn.commit()
    finally:
        conn.close()
    return {'indexed': done, 'unchanged': skipped, 'failed': failed, 'total': len(files)}


def status(conn, uid, total):
    _ensure(conn)
    r = conn.execute("SELECT COUNT(*) AS n, COALESCE(AVG(ms),0) AS avg_ms, COALESCE(SUM(LENGTH(desc)),0) AS bytes FROM shape_index WHERE user_id = ?", (uid,)).fetchone()
    skipped = conn.execute("SELECT COUNT(*) FROM shape_skip WHERE user_id = ?", (uid,)).fetchone()[0]
    left = max(0, total - r['n'] - skipped)          # les modèles illisibles ou trop gros (« ignorés ») ne sont plus « à indexer »
    return {'indexed': r['n'], 'total': total, 'missing': left, 'skipped': skipped, 'avg_ms_per_model': round(r['avg_ms']), 'index_bytes': r['bytes'],
            'estimated_seconds_left': round(left * r['avg_ms'] / 1000) if r['avg_ms'] else None}


_TOTAL = {}          # uid → (horodatage, nombre de modèles) : compter la bibliothèque relit tout le cache et teste chaque chemin, on ne le refait pas à chaque affichage


def _library_total(uid, ttl=30.0):
    import time as _t
    hit = _TOTAL.get(uid)
    if hit and _t.time() - hit[0] < ttl:
        return hit[1]
    n = len(library_files(uid))
    _TOTAL[uid] = (_t.time(), n)
    return n


def _no_viewer():
    if session.get('role') == 'viewer' and not _demo_ok():
        return jsonify({'error': 'Réservé au compte propriétaire.', 'code': 'viewer_forbidden'}), 403
    return None


def api_similar_status():
    r = _no_viewer()
    if r:
        return r
    uid = session['user_id']
    conn = get_db()
    try:
        return jsonify(status(conn, uid, _library_total(uid)))
    finally:
        conn.close()


def api_similar_build():
    r = _no_viewer()
    if r:
        return r
    uid = session['user_id']
    try:
        from modules import job_manager
        job = job_manager.submit('Index de formes', build_index, owner=uid, kind='shape_index', args=(uid,))
        return jsonify({'job_id': job.id}), 202
    except ImportError:
        return jsonify({'error': 'Gestionnaire de tâches indisponible.'}), 503


def api_similar():
    r = _no_viewer()
    if r:
        return r
    uid = session['user_id']
    path = (request.args.get('path') or '').strip()
    try:
        limit = max(1, min(int(request.args.get('limit') or DEFAULT_LIMIT), MAX_LIMIT))
    except ValueError:
        limit = DEFAULT_LIMIT
    if not path or not _is_path_within_sources(path, uid):
        return jsonify({'error': 'Fichier introuvable.'}), 404
    conn = get_db()
    try:
        _ensure(conn)
        key = _norm(path)
        row = conn.execute("SELECT desc FROM shape_index WHERE user_id = ? AND path = ?", (uid, key)).fetchone()
        if row:
            target = json.loads(row['desc'])
        else:
            try:
                target = compute_file(path)
            except Exception as e:
                return jsonify({'error': f'Empreinte impossible : {e}'}), 422
        cands = {r['path']: json.loads(r['desc']) for r in conn.execute("SELECT path, desc FROM shape_index WHERE user_id = ? AND path <> ?", (uid, key)).fetchall()}
        st = status(conn, uid, len(library_files(uid)))
        res = rank(target, cands, limit)
        for x in res:
            x['name'] = os.path.basename(x['path'])
        return jsonify({'path': path, 'results': res, 'index': st,
                        'note': None if st['missing'] == 0 else f"{st['missing']} modèle(s) pas encore indexé(s) : lancez l'indexation pour une recherche complète."})
    finally:
        conn.close()


_DEMO_COMPUTE = ('/api/plate/arrange', '/api/organize/preview', '/api/model-diff')


def _demo_ok():
    """Démo publique (lecture seule, `IS_DEMO` posé par la surcouche de démo) : consultation (GET) et calculs sans écriture."""
    try:
        return bool(_MAIN.get('IS_DEMO')) and (request.method in ('GET', 'HEAD') or request.path in _DEMO_COMPUTE)
    except Exception:
        return False


_ROUTES = (
    ('/api/similar', ['GET'], 'api_similar', ('login_required', )),
    ('/api/similar/status', ['GET'], 'api_similar_status', ('login_required', )),
    ('/api/similar/build', ['POST'], 'api_similar_build', ('login_required', )),
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
