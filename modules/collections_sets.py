"""Stellio — collections de modèles (v1.1.3)

Une collection regroupe des modèles de la bibliothèque autour d'un thème (un jeu d'échecs, un décor, une gamme de pièces…),
avec une quantité par fichier. On peut ajouter la collection entière à la file d'impression en un clic (chaque fichier une fois,
déjà présents ignorés ; la quantité sert au décompte affiché) et la retrouver dans la bibliothèque. Différent d'un projet : une
collection est légère (pas de devis, pas de G-code archivé) ; un fichier peut appartenir à plusieurs collections.

Module séparé de main.py (même schéma que trash_routes.py) : main.py appelle `collections_sets.init(globals())`.
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

MAX_NAME = 80
MAX_FILES = 500
COLORS = ('#4ea1d3', '#e0a030', '#5cb85c', '#d9534f', '#9b6bd1', '#e6709b', '#3fbfae', '#8a8f98')


def _ensure(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS collections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        color TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS collection_files (
        collection_id INTEGER NOT NULL,
        file_path TEXT NOT NULL,
        quantity INTEGER DEFAULT 1,
        position INTEGER DEFAULT 0,
        PRIMARY KEY (collection_id, file_path))""")


def _norm(p):
    return (p or '').strip().replace('\\', '/')


def _native(p):
    return p.replace('/', '\\') if os.name == 'nt' else p.replace('\\', '/')


def _own(conn, cid):
    return conn.execute("SELECT * FROM collections WHERE id = ? AND user_id = ?", (cid, session['user_id'])).fetchone()


def _clean_color(c):
    c = (c or '').strip()
    return c if c in COLORS else ''


def _files_of(conn, cid):
    rows = conn.execute("SELECT file_path, quantity FROM collection_files WHERE collection_id = ? ORDER BY position, rowid", (cid,)).fetchall()
    out = []
    for r in rows:
        p = r['file_path']
        out.append({'path': p, 'name': os.path.basename(p), 'quantity': r['quantity'] or 1})
    return out


def api_collections_list():
    conn = get_db()
    try:
        _ensure(conn)
        rows = conn.execute("SELECT * FROM collections WHERE user_id = ? ORDER BY name COLLATE NOCASE", (session['user_id'],)).fetchall()
        out = []
        for r in rows:
            files = _files_of(conn, r['id'])
            out.append({'id': r['id'], 'name': r['name'], 'description': r['description'] or '', 'color': r['color'] or '',
                        'count': len(files), 'pieces': sum(f['quantity'] for f in files),
                        'preview': [f['path'] for f in files[:4]]})
        return jsonify({'collections': out, 'colors': list(COLORS)})
    finally:
        conn.close()


def api_collections_get(cid):
    conn = get_db()
    try:
        _ensure(conn)
        r = _own(conn, cid)
        if not r:
            return jsonify({'error': 'not_found'}), 404
        files = _files_of(conn, cid)
        for f in files:
            f['missing'] = not os.path.exists(_native(f['path'])) if not f['path'].startswith('//') else False
        return jsonify({'id': r['id'], 'name': r['name'], 'description': r['description'] or '', 'color': r['color'] or '',
                        'files': files, 'pieces': sum(f['quantity'] for f in files)})
    finally:
        conn.close()


def api_collections_save():
    """Crée (sans id) ou modifie (avec id) une collection : nom, description, couleur."""
    d = request.get_json(silent=True) or {}
    name = (d.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'name_required'}), 400
    if len(name) > MAX_NAME:
        return jsonify({'error': 'name_too_long'}), 400
    desc = (d.get('description') or '').strip()[:500]
    color = _clean_color(d.get('color'))
    conn = get_db()
    try:
        _ensure(conn)
        # SQLite ne compare sans casse que l'ASCII : on compare en Python (« Échecs » = « échecs »)
        dup = next((x for x in conn.execute("SELECT id, name FROM collections WHERE user_id = ?", (session['user_id'],)).fetchall()
                    if (x['name'] or '').casefold() == name.casefold()), None)
        if d.get('id'):
            r = _own(conn, int(d['id']))
            if not r:
                return jsonify({'error': 'not_found'}), 404
            if dup and dup['id'] != r['id']:
                return jsonify({'error': 'name_exists'}), 409
            conn.execute("UPDATE collections SET name=?, description=?, color=? WHERE id=?", (name, desc, color, r['id']))
            cid = r['id']
        else:
            if dup:
                return jsonify({'error': 'name_exists'}), 409
            cid = conn.execute("INSERT INTO collections (user_id, name, description, color) VALUES (?,?,?,?)",
                               (session['user_id'], name, desc, color)).lastrowid
        conn.commit()
        return jsonify({'success': True, 'id': cid})
    finally:
        conn.close()


def api_collections_delete():
    d = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        _ensure(conn)
        r = _own(conn, int(d.get('id') or 0))
        if not r:
            return jsonify({'error': 'not_found'}), 404
        conn.execute("DELETE FROM collection_files WHERE collection_id = ?", (r['id'],))
        conn.execute("DELETE FROM collections WHERE id = ?", (r['id'],))
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


def api_collections_add_files():
    """Ajoute des fichiers (paths) à une collection ; les fichiers hors des sources sont refusés, les doublons ignorés."""
    d = request.get_json(silent=True) or {}
    paths = [_norm(p) for p in (d.get('paths') or []) if isinstance(p, str)]
    if not paths:
        return jsonify({'error': 'paths_required'}), 400
    conn = get_db()
    try:
        _ensure(conn)
        r = _own(conn, int(d.get('id') or 0))
        if not r:
            return jsonify({'error': 'not_found'}), 404
        have = {x['file_path'] for x in conn.execute("SELECT file_path FROM collection_files WHERE collection_id = ?", (r['id'],)).fetchall()}
        pos = conn.execute("SELECT COALESCE(MAX(position), -1) AS m FROM collection_files WHERE collection_id = ?", (r['id'],)).fetchone()['m']
        added = skipped = 0
        for p in paths:
            if p in have or len(have) >= MAX_FILES:
                skipped += 1
                continue
            if not _is_path_within_sources(_native(p), session['user_id']):
                skipped += 1
                continue
            pos += 1
            conn.execute("INSERT INTO collection_files (collection_id, file_path, quantity, position) VALUES (?,?,?,?)", (r['id'], p, 1, pos))
            have.add(p)
            added += 1
        conn.commit()
        return jsonify({'success': True, 'added': added, 'skipped': skipped})
    finally:
        conn.close()


def api_collections_remove_file():
    d = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        _ensure(conn)
        r = _own(conn, int(d.get('id') or 0))
        if not r:
            return jsonify({'error': 'not_found'}), 404
        conn.execute("DELETE FROM collection_files WHERE collection_id = ? AND file_path = ?", (r['id'], _norm(d.get('path'))))
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


def api_collections_set_quantity():
    d = request.get_json(silent=True) or {}
    try:
        q = max(1, min(999, int(d.get('quantity'))))
    except (TypeError, ValueError):
        return jsonify({'error': 'bad_quantity'}), 400
    conn = get_db()
    try:
        _ensure(conn)
        r = _own(conn, int(d.get('id') or 0))
        if not r:
            return jsonify({'error': 'not_found'}), 404
        conn.execute("UPDATE collection_files SET quantity = ? WHERE collection_id = ? AND file_path = ?", (q, r['id'], _norm(d.get('path'))))
        conn.commit()
        return jsonify({'success': True, 'quantity': q})
    finally:
        conn.close()


def api_collections_queue():
    """Ajoute à la file d'impression tous les fichiers de la collection (ceux déjà en file sont ignorés)."""
    d = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        _ensure(conn)
        r = _own(conn, int(d.get('id') or 0))
        if not r:
            return jsonify({'error': 'not_found'}), 404
        files = _files_of(conn, r['id'])
        if not files:
            return jsonify({'error': 'empty'}), 400
        queued = {x['file_path'] for x in conn.execute("SELECT file_path FROM print_queue WHERE user_id = ?", (session['user_id'],)).fetchall()}
        pos = conn.execute("SELECT COALESCE(MAX(position), -1) AS m FROM print_queue WHERE user_id = ?", (session['user_id'],)).fetchone()['m']
        added = already = 0
        for f in files:
            if f['path'] in queued:
                already += 1
                continue
            pos += 1
            note = f"{r['name']} ×{f['quantity']}" if f['quantity'] > 1 else r['name']
            conn.execute("INSERT INTO print_queue (user_id, file_path, position, note) VALUES (?,?,?,?)", (session['user_id'], f['path'], pos, note))
            added += 1
        conn.commit()
        return jsonify({'success': True, 'added': added, 'already': already})
    finally:
        conn.close()


def api_collections_of_file():
    """Collections qui contiennent un fichier (pour l'afficher dans la fiche du fichier)."""
    p = _norm(request.args.get('path'))
    conn = get_db()
    try:
        _ensure(conn)
        rows = conn.execute("""SELECT c.id, c.name, c.color FROM collections c JOIN collection_files f ON f.collection_id = c.id
                               WHERE c.user_id = ? AND f.file_path = ? ORDER BY c.name COLLATE NOCASE""", (session['user_id'], p)).fetchall()
        return jsonify({'collections': [dict(r) for r in rows]})
    finally:
        conn.close()


_ROUTES = (
    ('/api/collections', ['GET'], 'api_collections_list', ('login_required', )),
    ('/api/collections/<int:cid>', ['GET'], 'api_collections_get', ('login_required', )),
    ('/api/collections/save', ['POST'], 'api_collections_save', ('login_required', )),
    ('/api/collections/delete', ['POST'], 'api_collections_delete', ('login_required', )),
    ('/api/collections/add-files', ['POST'], 'api_collections_add_files', ('login_required', )),
    ('/api/collections/remove-file', ['POST'], 'api_collections_remove_file', ('login_required', )),
    ('/api/collections/quantity', ['POST'], 'api_collections_set_quantity', ('login_required', )),
    ('/api/collections/queue', ['POST'], 'api_collections_queue', ('login_required', )),
    ('/api/collections/of-file', ['GET'], 'api_collections_of_file', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"collections_sets.init : services manquants : {missing}")
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
