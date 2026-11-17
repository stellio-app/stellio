"""Stellio — widget « Dernières miniatures générées » du tableau de bord (v1.1.4)

`GET /api/thumb/recent?limit=10` : les miniatures les plus récemment générées (date du fichier image dans le dossier des
miniatures), rattachées à leur fichier de la bibliothèque (la clé de la miniature est le MD5 du chemin, comme /api/thumb).
Les miniatures de remplacement (rendu échoué ou trop long) et les fichiers masqués ne sont pas listés. Lecture seule.
`recent_items()` est pure (liste des miniatures et fichiers injectés) : testée sans disque.
Module séparé de main.py (même schéma que resin_printers.py) ; main.py appelle `thumb_recent.init(globals())`.
"""
import hashlib
import os

_REQUIRED = ('THUMBNAILS_DIR', 'app', 'jsonify', 'login_required', 'request', 'session', 'get_db',
             '_read_cache_json_safe', '_drop_disabled_type_files', '_is_hidden_plate_path')
_OPTIONAL = ()
_OVERRIDABLE = ()

_MAIN = {}
THUMBNAILS_DIR = None
app = None
jsonify = None
login_required = None
request = None
session = None
get_db = None
_read_cache_json_safe = None
_drop_disabled_type_files = None
_is_hidden_plate_path = None

DEFAULT_LIMIT = 10
MAX_LIMIT = 30


def _key(path):
    return hashlib.md5(str(path).replace('\\', '/').encode()).hexdigest()


def recent_items(thumbs, files, limit=DEFAULT_LIMIT, hidden=lambda p: False):
    """thumbs : [(nom_de_fichier_image, mtime)] ; files : dicts de la bibliothèque. Retourne les `limit` plus récentes,
    la plus récente d'abord : {name, path, generated_at, size}."""
    by_key = {}
    for f in files or []:
        p = f.get('path')
        if p and f.get('has_thumb') and not f.get('thumb_fallback') and not hidden(p):
            by_key[_key(p)] = f
    out, seen = [], set()
    for fname, mtime in sorted(thumbs, key=lambda t: t[1], reverse=True):
        stem, ext = os.path.splitext(fname)
        if ext.lower() not in ('.webp', '.png', '.jpg') or stem in seen:
            continue
        f = by_key.get(stem)
        if f is None:
            continue
        seen.add(stem)
        out.append({'name': f.get('name') or os.path.basename(f['path']), 'path': f['path'], 'generated_at': int(mtime), 'size': f.get('size') or 0})
        if len(out) >= limit:
            break
    return out


def _list_thumbs():
    res = []
    try:
        with os.scandir(THUMBNAILS_DIR) as it:
            for e in it:
                if e.is_file():
                    try:
                        res.append((e.name, e.stat().st_mtime))
                    except OSError:
                        pass
    except OSError:
        pass
    return res


def api_thumb_recent():
    try:
        limit = max(1, min(MAX_LIMIT, int(request.args.get('limit') or DEFAULT_LIMIT)))
    except ValueError:
        limit = DEFAULT_LIMIT
    cache = _read_cache_json_safe()
    files = (cache or {}).get('files') or []
    conn = get_db()
    try:
        sources = [dict(s) for s in conn.execute("SELECT * FROM sources WHERE user_id = ?", (session['user_id'],)).fetchall()]
    finally:
        conn.close()
    files = _drop_disabled_type_files(files, sources)
    return jsonify({'items': recent_items(_list_thumbs(), files, limit, _is_hidden_plate_path)})


_ROUTES = (
    ('/api/thumb/recent', ['GET'], 'api_thumb_recent', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre la route Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"thumb_recent.init : services manquants : {missing}")
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
