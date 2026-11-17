"""Stellio — versions d'un modèle (v1.1.3)

Historique des versions d'un fichier 3D : « Enregistrer une version » conserve une copie du fichier (v1, v2, v3…) avec une
note, « Comparer » met deux versions côte à côte (taille, empreinte, nombre de triangles, dimensions, volume) et
« Restaurer » remet une ancienne version à la place du fichier (la version actuelle est d'abord sauvegardée : aucune perte).
Les copies sont rangées dans DATA_DIR/model_versions/ ; seuls les fichiers locaux des sources configurées sont gérés.

Module séparé de main.py (même schéma que trash_routes.py) : main.py appelle `model_versions.init(globals())`.
"""
import hashlib
import os
import shutil
import time

_REQUIRED = (
    'DATA_DIR',
    '_is_path_within_sources',
    'app',
    'app_logger',
    'get_db',
    'invalidate_cache',
    'jsonify',
    'login_required',
    'request',
    'send_file',
    'session',
)
_OPTIONAL = ('journal_log',)
_OVERRIDABLE = ('hashlib', 'os', 'shutil', 'time')

_MAIN = {}
DATA_DIR = None
_is_path_within_sources = None
app = None
app_logger = None
get_db = None
invalidate_cache = None
journal_log = None
jsonify = None
login_required = None
request = None
send_file = None
session = None

MAX_VERSIONS_PER_FILE = 50
MAX_FILE_BYTES = 1024 * 1024 * 1024          # au-delà d'1 Go on ne duplique pas
MESH_EXT = ('.stl', '.obj', '.3mf', '.ply', '.off')
MESH_STATS_MAX_BYTES = 80 * 1024 * 1024       # pas de calcul de maillage au-delà


def _dir():
    d = os.path.join(DATA_DIR, 'model_versions')
    os.makedirs(d, exist_ok=True)
    return d


def _ensure_table(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS model_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        path TEXT NOT NULL,
        version INTEGER NOT NULL,
        stored_name TEXT NOT NULL,
        size INTEGER DEFAULT 0,
        sha256 TEXT DEFAULT '',
        note TEXT DEFAULT '',
        auto INTEGER DEFAULT 0,
        created_at REAL)""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_model_versions_path ON model_versions(path)")


def _norm(p):
    return (p or '').strip().replace('\\', '/')


def _native(p):
    return p.replace('/', '\\') if os.name == 'nt' else p.replace('\\', '/')


def _file_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _check_path(raw):
    """(chemin natif, None) si le fichier est un fichier local des sources de l'utilisateur ; sinon (None, (message, code))."""
    p = _norm(raw)
    if not p:
        return None, ('path_required', 400)
    native = _native(p)
    if not _is_path_within_sources(native, session.get('user_id')):
        return None, ('forbidden', 403)
    if not os.path.isfile(native):
        return None, ('not_local', 400)
    return native, None


def _snapshot(conn, native, key, note='', auto=0):
    """Copie le fichier dans model_versions/ et enregistre la ligne. Retourne la ligne (dict)."""
    size = os.path.getsize(native)
    if size > MAX_FILE_BYTES:
        raise ValueError('too_big')
    sha = _file_sha256(native)
    last = conn.execute("SELECT MAX(version) AS v FROM model_versions WHERE path = ?", (key,)).fetchone()
    version = (last['v'] or 0) + 1
    stored = f"{hashlib.sha1(key.encode('utf-8')).hexdigest()[:12]}_v{version}_{int(time.time())}{os.path.splitext(native)[1].lower()}"
    shutil.copy2(native, os.path.join(_dir(), stored))
    cur = conn.execute(
        "INSERT INTO model_versions (user_id, path, version, stored_name, size, sha256, note, auto, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (session.get('user_id'), key, version, stored, size, sha, (note or '')[:300], 1 if auto else 0, time.time()))
    _prune(conn, key)
    return {'id': cur.lastrowid, 'version': version, 'size': size, 'sha256': sha, 'note': note or '', 'auto': bool(auto), 'created_at': time.time()}


def _prune(conn, key):
    """Garde au plus MAX_VERSIONS_PER_FILE versions (les plus anciennes automatiques partent d'abord)."""
    rows = conn.execute("SELECT id, stored_name, auto FROM model_versions WHERE path = ? ORDER BY version DESC", (key,)).fetchall()
    extra = rows[MAX_VERSIONS_PER_FILE:]
    for r in extra:
        try:
            os.remove(os.path.join(_dir(), r['stored_name']))
        except OSError:
            pass
        conn.execute("DELETE FROM model_versions WHERE id = ?", (r['id'],))


def _row_dict(r):
    return {'id': r['id'], 'version': r['version'], 'size': r['size'], 'sha256': r['sha256'], 'note': r['note'] or '',
            'auto': bool(r['auto']), 'created_at': r['created_at']}


def _mesh_stats(path):
    """Triangles, dimensions (mm) et volume (mm³) d'un maillage ; None si illisible ou trop gros."""
    try:
        if os.path.splitext(path)[1].lower() not in MESH_EXT or os.path.getsize(path) > MESH_STATS_MAX_BYTES:
            return None
        import trimesh
        m = trimesh.load(path, force='mesh')
        ext = [round(float(x), 2) for x in m.extents]
        vol = round(float(m.volume), 1) if m.is_watertight else None
        return {'triangles': int(len(m.faces)), 'size_mm': ext, 'volume_mm3': vol}
    except Exception:
        return None


def api_versions_list():
    native, err = _check_path(request.args.get('path'))
    if err:
        return jsonify({'error': err[0]}), err[1]
    key = _norm(request.args.get('path'))
    conn = get_db()
    try:
        _ensure_table(conn)
        rows = conn.execute("SELECT * FROM model_versions WHERE path = ? ORDER BY version DESC", (key,)).fetchall()
        cur_sha = _file_sha256(native) if os.path.getsize(native) <= MAX_FILE_BYTES else ''
        out = [dict(_row_dict(r), is_current=(r['sha256'] == cur_sha and cur_sha != '')) for r in rows]
        return jsonify({'path': key, 'size': os.path.getsize(native), 'mtime': os.path.getmtime(native),
                        'sha256': cur_sha, 'versions': out, 'max_versions': MAX_VERSIONS_PER_FILE})
    finally:
        conn.close()


def api_versions_save():
    data = request.get_json(silent=True) or {}
    native, err = _check_path(data.get('path'))
    if err:
        return jsonify({'error': err[0]}), err[1]
    key = _norm(data.get('path'))
    conn = get_db()
    try:
        _ensure_table(conn)
        last = conn.execute("SELECT sha256 FROM model_versions WHERE path = ? ORDER BY version DESC LIMIT 1", (key,)).fetchone()
        if last and last['sha256'] == _file_sha256(native):
            return jsonify({'error': 'unchanged'}), 409
        try:
            row = _snapshot(conn, native, key, data.get('note'))
        except ValueError:
            return jsonify({'error': 'too_big'}), 413
        conn.commit()
    finally:
        conn.close()
    if journal_log:
        journal_log('version_save', os.path.basename(native), from_path=key, detail=f"v{row['version']}")
    return jsonify({'success': True, 'version': row})


def _get_row(conn, vid):
    r = conn.execute("SELECT * FROM model_versions WHERE id = ?", (vid,)).fetchone()
    if not r:
        return None, (jsonify({'error': 'not_found'}), 404)
    native = _native(r['path'])
    if not _is_path_within_sources(native, session.get('user_id')):
        return None, (jsonify({'error': 'forbidden'}), 403)
    return r, None


def api_versions_restore():
    data = request.get_json(silent=True) or {}
    try:
        vid = int(data.get('id'))
    except (TypeError, ValueError):
        return jsonify({'error': 'id_required'}), 400
    conn = get_db()
    try:
        _ensure_table(conn)
        r, err = _get_row(conn, vid)
        if err:
            return err
        src = os.path.join(_dir(), r['stored_name'])
        if not os.path.isfile(src):
            return jsonify({'error': 'copy_missing'}), 410
        native = _native(r['path'])
        if os.path.isfile(native):
            last = conn.execute("SELECT sha256 FROM model_versions WHERE path = ? ORDER BY version DESC LIMIT 1", (r['path'],)).fetchone()
            if not last or last['sha256'] != _file_sha256(native):
                _snapshot(conn, native, r['path'], 'Avant restauration', auto=1)      # on ne perd jamais l'état actuel
        shutil.copy2(src, native)
        conn.commit()
    finally:
        conn.close()
    try:
        invalidate_cache()
    except Exception:
        pass
    if journal_log:
        journal_log('version_restore', os.path.basename(native), from_path=r['path'], detail=f"v{r['version']}")
    return jsonify({'success': True, 'version': r['version']})


def api_versions_delete():
    data = request.get_json(silent=True) or {}
    try:
        vid = int(data.get('id'))
    except (TypeError, ValueError):
        return jsonify({'error': 'id_required'}), 400
    conn = get_db()
    try:
        _ensure_table(conn)
        r, err = _get_row(conn, vid)
        if err:
            return err
        try:
            os.remove(os.path.join(_dir(), r['stored_name']))
        except OSError:
            pass
        conn.execute("DELETE FROM model_versions WHERE id = ?", (vid,))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'success': True})


def api_versions_download(vid):
    conn = get_db()
    try:
        _ensure_table(conn)
        r, err = _get_row(conn, vid)
        if err:
            return err
        src = os.path.join(_dir(), r['stored_name'])
    finally:
        conn.close()
    if not os.path.isfile(src):
        return jsonify({'error': 'copy_missing'}), 410
    base, ext = os.path.splitext(os.path.basename(r['path']))
    return send_file(src, as_attachment=True, download_name=f"{base}_v{r['version']}{ext}")


def api_versions_compare():
    """Compare deux versions (ids) ; id « 0 » ou « current » = le fichier actuel."""
    native, err = _check_path(request.args.get('path'))
    if err:
        return jsonify({'error': err[0]}), err[1]
    key = _norm(request.args.get('path'))

    def side(token):
        if str(token) in ('0', 'current', ''):
            return {'label': 'current', 'size': os.path.getsize(native), 'sha256': _file_sha256(native), 'mesh': _mesh_stats(native)}
        conn = get_db()
        try:
            _ensure_table(conn)
            r = conn.execute("SELECT * FROM model_versions WHERE id = ? AND path = ?", (int(token), key)).fetchone()
        finally:
            conn.close()
        if not r:
            return None
        src = os.path.join(_dir(), r['stored_name'])
        if not os.path.isfile(src):
            return None
        return {'label': f"v{r['version']}", 'version': r['version'], 'size': r['size'], 'sha256': r['sha256'], 'mesh': _mesh_stats(src)}

    try:
        a, b = side(request.args.get('a', '0')), side(request.args.get('b', '0'))
    except ValueError:
        return jsonify({'error': 'bad_id'}), 400
    if not a or not b:
        return jsonify({'error': 'not_found'}), 404
    diff = {'size': b['size'] - a['size'], 'identical': a['sha256'] == b['sha256']}
    if a['mesh'] and b['mesh']:
        diff['triangles'] = b['mesh']['triangles'] - a['mesh']['triangles']
        diff['size_mm'] = [round(y - x, 2) for x, y in zip(a['mesh']['size_mm'], b['mesh']['size_mm'])]
        if a['mesh']['volume_mm3'] is not None and b['mesh']['volume_mm3'] is not None:
            diff['volume_mm3'] = round(b['mesh']['volume_mm3'] - a['mesh']['volume_mm3'], 1)
    return jsonify({'a': a, 'b': b, 'diff': diff})


_ROUTES = (
    ('/api/versions', ['GET'], 'api_versions_list', ('login_required', )),
    ('/api/versions/save', ['POST'], 'api_versions_save', ('login_required', )),
    ('/api/versions/restore', ['POST'], 'api_versions_restore', ('login_required', )),
    ('/api/versions/delete', ['POST'], 'api_versions_delete', ('login_required', )),
    ('/api/versions/compare', ['GET'], 'api_versions_compare', ('login_required', )),
    ('/api/versions/<int:vid>/download', ['GET'], 'api_versions_download', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"model_versions.init : services manquants : {missing}")
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
