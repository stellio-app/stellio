"""Stellio — règles d'auto-organisation de la bibliothèque (1.1.7).

Des règles simples (« si … alors … ») rangent la bibliothèque sans toucher aux fichiers : elles posent des ÉTIQUETTES, ajoutent à des
COLLECTIONS ou PROPOSENT un dossier (suggestion, jamais exécutée). Critères : extension, partie du nom, licence (usage commercial
oui / non / inconnu), matière ou imprimante déjà utilisée pour ce modèle, taille, jamais imprimé. Toujours en deux temps : un APERÇU
(rien n'est écrit) puis « Appliquer », qui enregistre un lot annulable en un clic (`organize_log`). Aucun fichier n'est déplacé,
renommé ni supprimé ; les règles ne voient que les fichiers des sources du compte.
"""
import json
import os
import time
import uuid

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
_OPTIONAL = ('_read_cache_json_safe', '_bulk_source_scope')
_OVERRIDABLE = ('os',)

_MAIN = {}
_is_path_within_sources = None
_bulk_source_scope = None
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None
_read_cache_json_safe = None

FIELDS = {
    'ext': ('is', 'in'),
    'name': ('contains', 'not_contains'),
    'license_commercial': ('is',),
    'material': ('is',),
    'printer': ('is',),
    'size_mb': ('gt', 'lt'),
    'printed': ('is',),
    'author': ('is', 'contains'),          # auteur déclaré dans l'origine du fichier
    'category': ('is',),                   # catégorie = étiquette déjà posée sur le fichier
    'age_days': ('gt', 'lt'),              # date : ancienneté du fichier en jours (date de modification)
}
ACTIONS = ('tag', 'collection', 'suggest_folder')
MAX_RULES = 50
MAX_ITEMS = 5000
PREVIEW_ITEMS = 200
COMMERCIAL = ('yes', 'no', 'unknown')


def _norm(p):
    return str(p or '').strip().replace('\\', '/')


def validate_rule(d):
    """Retourne (règle propre, erreur)."""
    field, op, value = str(d.get('field') or ''), str(d.get('op') or ''), str(d.get('value') if d.get('value') is not None else '').strip()
    action, target = str(d.get('action') or ''), str(d.get('target') or '').strip()
    name = str(d.get('name') or '').strip()[:60] or f"{field} {op} {value}"[:60]
    if field not in FIELDS or op not in FIELDS[field]:
        return None, 'Critère inconnu.'
    if not value or len(value) > 80:
        return None, 'Valeur manquante ou trop longue.'
    if field == 'license_commercial' and value not in COMMERCIAL:
        return None, 'Usage commercial : yes, no ou unknown.'
    if field == 'printed' and value not in ('yes', 'no'):
        return None, 'Imprimé : yes ou no.'
    if field in ('size_mb', 'age_days'):
        try:
            float(value)
        except ValueError:
            return None, 'Nombre invalide.'
    if action not in ACTIONS:
        return None, 'Action inconnue.'
    if not target or len(target) > 80 or any(c in target for c in '\\:*?"<>|\0') or target.startswith('/') or '..' in target:
        return None, 'Cible invalide (nom d\'étiquette, de collection ou dossier relatif).'
    return {'name': name, 'field': field, 'op': op, 'value': value, 'action': action, 'target': target}, None


def matches(rule, f):
    """f : {'name','ext','size_mb','license_commercial','materials','printers','printed'}."""
    field, op, value = rule['field'], rule['op'], rule['value'].lower()
    if field == 'ext':
        exts = [x.strip().lstrip('.') for x in value.split(',')]
        return f['ext'] in exts
    if field == 'name':
        has = value in f['name'].lower()
        return has if op == 'contains' else not has
    if field == 'license_commercial':
        return f['license_commercial'] == value
    if field == 'material':
        return any(value in m.lower() for m in f['materials'])
    if field == 'printer':
        return any(value == p.lower() or value in p.lower() for p in f['printers'])
    if field == 'size_mb':
        try:
            lim = float(value)
        except ValueError:
            return False
        return f['size_mb'] > lim if op == 'gt' else f['size_mb'] < lim
    if field == 'printed':
        return f['printed'] == (value == 'yes')
    if field == 'author':
        a = str(f.get('author') or '').lower()
        return bool(a) and (a == value if op == 'is' else value in a)
    if field == 'category':
        return value in [str(t).lower() for t in f.get('tags', ())]
    if field == 'age_days':
        if f.get('age_days') is None:
            return False
        try:
            lim = float(value)
        except ValueError:
            return False
        return f['age_days'] > lim if op == 'gt' else f['age_days'] < lim
    return False


def plan(rules, files, existing_tags=None, existing_collections=None):
    """Aperçu pur : [{'path','action','target','rule'}], sans doublon ni élément déjà en place."""
    existing_tags = existing_tags or set()
    existing_collections = existing_collections or set()
    seen, out = set(), []
    for rule in rules:
        for f in files:
            if not matches(rule, f):
                continue
            key = (f['path'], rule['action'], rule['target'].lower())
            if key in seen:
                continue
            if rule['action'] == 'tag' and (f['path'], rule['target'].lower()) in existing_tags:
                continue
            if rule['action'] == 'collection' and (f['path'], rule['target'].lower()) in existing_collections:
                continue
            seen.add(key)
            out.append({'path': f['path'], 'action': rule['action'], 'target': rule['target'], 'rule': rule['name']})
    return out


def _license_commercial(text):
    try:
        from modules import file_origin_delete
        return file_origin_delete.license_info(text)['commercial']
    except Exception:
        return 'unknown'


def build_context(conn, uid):
    """Une entrée par fichier du compte, avec licence, matières, imprimantes et état « imprimé »."""
    data = _read_cache_json_safe() if _read_cache_json_safe else None
    lic = {_norm(r['file_path']): r['license'] for r in conn.execute("SELECT file_path, license FROM file_origins WHERE user_id = ?", (uid,)).fetchall()}
    try:
        authors = {_norm(r['file_path']): r['author'] for r in conn.execute("SELECT file_path, author FROM file_origins WHERE user_id = ?", (uid,)).fetchall()}
    except Exception:
        authors = {}
    try:
        ftags = {}
        for r in conn.execute("SELECT f.file_path, t.name FROM file_tags f JOIN tags t ON t.id = f.tag_id").fetchall():
            ftags.setdefault(_norm(r[0]), []).append(r[1])
    except Exception:
        ftags = {}
    now = time.time()
    mats, prn, printed = {}, {}, set()
    for r in conn.execute("SELECT file_path, filament_material, printer_id FROM print_history WHERE user_id = ?", (uid,)).fetchall():
        p = _norm(r['file_path'])
        printed.add(p)
        if r['filament_material']:
            mats.setdefault(p, set()).add(str(r['filament_material']))
        if r['printer_id']:
            prn.setdefault(p, set()).add(int(r['printer_id']))
    names = {r['id']: (r['name'] or '') for r in conn.execute("SELECT id, name FROM printers WHERE user_id = ?", (uid,)).fetchall()}
    out = []
    import contextlib
    with (_bulk_source_scope() if _bulk_source_scope else contextlib.nullcontext()):
        for f in (data or {}).get('files', []):
            p = _norm(f.get('path'))
            if not p or not _is_path_within_sources(f.get('path'), uid):
                continue
            out.append({'path': p, 'name': f.get('name') or os.path.basename(p), 'ext': os.path.splitext(p)[1].lower().lstrip('.'),
                        'size_mb': round((f.get('size') or 0) / 1048576, 3), 'license_commercial': _license_commercial(lic.get(p, '')) if lic.get(p) else 'unknown',
                        'materials': sorted(mats.get(p, ())), 'printers': [names.get(i, '') for i in sorted(prn.get(p, ()))] + [str(i) for i in sorted(prn.get(p, ()))],
                        'printed': p in printed, 'author': authors.get(p, ''), 'tags': ftags.get(p, []),
                        'age_days': round((now - float(f['mtime'])) / 86400, 1) if f.get('mtime') else None})
    return out


def _ensure(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS organize_rules (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT, field TEXT, op TEXT, value TEXT,
            action TEXT, target TEXT, enabled INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS organize_log (id INTEGER PRIMARY KEY AUTOINCREMENT, batch TEXT NOT NULL, user_id INTEGER NOT NULL, kind TEXT NOT NULL,
            path TEXT NOT NULL, target TEXT NOT NULL, ts REAL, undone INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS tags (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, color TEXT DEFAULT '#4ea1d3');
        CREATE TABLE IF NOT EXISTS file_tags (file_path TEXT NOT NULL, tag_id INTEGER NOT NULL, PRIMARY KEY (file_path, tag_id));
        CREATE TABLE IF NOT EXISTS collections (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT NOT NULL, description TEXT DEFAULT '',
            color TEXT DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS collection_files (collection_id INTEGER NOT NULL, file_path TEXT NOT NULL, quantity INTEGER DEFAULT 1, position INTEGER DEFAULT 0,
            PRIMARY KEY (collection_id, file_path));
    """)


def _existing(conn, uid):
    tags = {(r[0], r[1].lower()) for r in conn.execute("SELECT f.file_path, t.name FROM file_tags f JOIN tags t ON t.id = f.tag_id").fetchall()}
    cols = {(r[0], r[1].lower()) for r in conn.execute("SELECT cf.file_path, c.name FROM collection_files cf JOIN collections c ON c.id = cf.collection_id WHERE c.user_id = ?", (uid,)).fetchall()}
    return tags, cols


def _rules(conn, uid, only_enabled=True):
    return [dict(r) for r in conn.execute("SELECT id, name, field, op, value, action, target, enabled FROM organize_rules WHERE user_id = ? "
                                          + ("AND enabled = 1 " if only_enabled else "") + "ORDER BY id", (uid,)).fetchall()]


def apply_plan(conn, uid, items, now=None):
    """Écrit les étiquettes / collections (les suggestions de dossier ne s'appliquent pas). Retourne (batch, n)."""
    batch = uuid.uuid4().hex[:12]
    n = 0
    for it in items[:MAX_ITEMS]:
        if it['action'] == 'tag':
            row = conn.execute("SELECT id FROM tags WHERE lower(name) = lower(?)", (it['target'],)).fetchone()
            tid = row[0] if row else conn.execute("INSERT INTO tags (name) VALUES (?)", (it['target'],)).lastrowid
            cur = conn.execute("INSERT OR IGNORE INTO file_tags (file_path, tag_id) VALUES (?,?)", (it['path'], tid))
        elif it['action'] == 'collection':
            row = conn.execute("SELECT id FROM collections WHERE user_id = ? AND lower(name) = lower(?)", (uid, it['target'])).fetchone()
            cid = row[0] if row else conn.execute("INSERT INTO collections (user_id, name) VALUES (?,?)", (uid, it['target'])).lastrowid
            cur = conn.execute("INSERT OR IGNORE INTO collection_files (collection_id, file_path) VALUES (?,?)", (cid, it['path']))
        else:
            continue
        if cur.rowcount:
            conn.execute("INSERT INTO organize_log (batch, user_id, kind, path, target, ts) VALUES (?,?,?,?,?,?)",
                         (batch, uid, it['action'], it['path'], it['target'], now if now is not None else time.time()))
            n += 1
    conn.commit()
    return batch, n


def undo_batch(conn, uid, batch):
    rows = conn.execute("SELECT id, kind, path, target FROM organize_log WHERE batch = ? AND user_id = ? AND undone = 0", (batch, uid)).fetchall()
    for r in rows:
        if r['kind'] == 'tag':
            conn.execute("DELETE FROM file_tags WHERE file_path = ? AND tag_id = (SELECT id FROM tags WHERE lower(name) = lower(?))", (r['path'], r['target']))
        else:
            conn.execute("DELETE FROM collection_files WHERE file_path = ? AND collection_id IN (SELECT id FROM collections WHERE user_id = ? AND lower(name) = lower(?))",
                         (r['path'], uid, r['target']))
        conn.execute("UPDATE organize_log SET undone = 1 WHERE id = ?", (r['id'],))
    conn.commit()
    return len(rows)


def _no_viewer():
    if session.get('role') == 'viewer' and not _demo_ok():
        return jsonify({'error': 'Réservé au compte propriétaire.', 'code': 'viewer_forbidden'}), 403
    return None


def api_organize_rules():
    r = _no_viewer()
    if r:
        return r
    conn = get_db()
    try:
        _ensure(conn)
        return jsonify({'rules': _rules(conn, session['user_id'], False), 'fields': {k: list(v) for k, v in FIELDS.items()}, 'actions': list(ACTIONS)})
    finally:
        conn.close()


def api_organize_rule_create():
    r = _no_viewer()
    if r:
        return r
    rule, err = validate_rule(request.get_json(silent=True) or {})
    if err:
        return jsonify({'error': err}), 400
    conn = get_db()
    try:
        _ensure(conn)
        if conn.execute("SELECT COUNT(*) FROM organize_rules WHERE user_id = ?", (session['user_id'],)).fetchone()[0] >= MAX_RULES:
            return jsonify({'error': f'{MAX_RULES} règles au maximum.'}), 400
        cur = conn.execute("INSERT INTO organize_rules (user_id, name, field, op, value, action, target) VALUES (?,?,?,?,?,?,?)",
                           (session['user_id'], rule['name'], rule['field'], rule['op'], rule['value'], rule['action'], rule['target']))
        conn.commit()
        return jsonify({'ok': True, 'id': cur.lastrowid})
    finally:
        conn.close()


def api_organize_rule_delete(rid):
    r = _no_viewer()
    if r:
        return r
    conn = get_db()
    try:
        _ensure(conn)
        cur = conn.execute("DELETE FROM organize_rules WHERE id = ? AND user_id = ?", (rid, session['user_id']))
        conn.commit()
        return jsonify({'ok': True}) if cur.rowcount else (jsonify({'error': 'Règle introuvable.'}), 404)
    finally:
        conn.close()


def api_organize_preview():
    r = _no_viewer()
    if r:
        return r
    uid = session['user_id']
    conn = get_db()
    try:
        _ensure(conn)
        items = plan(_rules(conn, uid), build_context(conn, uid), *_existing(conn, uid))
        counts = {a: sum(1 for i in items if i['action'] == a) for a in ACTIONS}
        return jsonify({'total': len(items), 'counts': counts, 'items': items[:PREVIEW_ITEMS], 'truncated': len(items) > PREVIEW_ITEMS,
                        'note': "Aperçu : rien n'est écrit. Les suggestions de dossier ne sont jamais appliquées."})
    finally:
        conn.close()


def api_organize_apply():
    r = _no_viewer()
    if r:
        return r
    if (request.get_json(silent=True) or {}).get('confirm') is not True:
        return jsonify({'error': 'Confirmation requise (confirm: true) : lancez d\'abord un aperçu.'}), 400
    uid = session['user_id']
    conn = get_db()
    try:
        _ensure(conn)
        items = plan(_rules(conn, uid), build_context(conn, uid), *_existing(conn, uid))
        batch, n = apply_plan(conn, uid, items)
        return jsonify({'ok': True, 'batch': batch, 'applied': n, 'skipped_suggestions': sum(1 for i in items if i['action'] == 'suggest_folder')})
    finally:
        conn.close()


def api_organize_undo():
    r = _no_viewer()
    if r:
        return r
    batch = str((request.get_json(silent=True) or {}).get('batch') or '')
    conn = get_db()
    try:
        _ensure(conn)
        n = undo_batch(conn, session['user_id'], batch)
        return jsonify({'ok': True, 'undone': n}) if n else (jsonify({'error': 'Lot introuvable ou déjà annulé.'}), 404)
    finally:
        conn.close()


def api_organize_batches():
    r = _no_viewer()
    if r:
        return r
    conn = get_db()
    try:
        _ensure(conn)
        rows = conn.execute("SELECT batch, MIN(ts) AS ts, COUNT(*) AS n, SUM(undone) AS undone FROM organize_log WHERE user_id = ? GROUP BY batch ORDER BY ts DESC LIMIT 20",
                            (session['user_id'],)).fetchall()
        return jsonify({'batches': [dict(x) for x in rows]})
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
    ('/api/organize/rules', ['GET'], 'api_organize_rules', ('login_required', )),
    ('/api/organize/rules', ['POST'], 'api_organize_rule_create', ('login_required', )),
    ('/api/organize/rules/<int:rid>', ['DELETE'], 'api_organize_rule_delete', ('login_required', )),
    ('/api/organize/preview', ['POST'], 'api_organize_preview', ('login_required', )),
    ('/api/organize/apply', ['POST'], 'api_organize_apply', ('login_required', )),
    ('/api/organize/undo', ['POST'], 'api_organize_undo', ('login_required', )),
    ('/api/organize/batches', ['GET'], 'api_organize_batches', ('login_required', )),
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
