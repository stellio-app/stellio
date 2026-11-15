"""Stellio — Corbeille : enregistrement, purge et restauration (cœur utilisé par les suppressions)

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `trash_core.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import json
import os
import shutil
import sqlite3
import time

_REQUIRED = (
    'TRASH_ITEMS_DIR',
    '_ensure_quote_columns',
    '_trash_registry',
    '_trash_registry_lock',
    '_trash_retention_seconds',
    'app_logger',
    'get_db',
)
_OPTIONAL = ()   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('json', 'os', 'shutil', 'sqlite3', 'time', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
TRASH_ITEMS_DIR = None
_ensure_quote_columns = None
_trash_registry = None
_trash_registry_lock = None
_trash_retention_seconds = None
app_logger = None
get_db = None


_trash_table_ready = False

def _ensure_trash_table(conn=None):
    """Crée la table si besoin. Avec `conn`, utilise la connexion de l'appelant (une 2e connexion bloquerait pendant sa transaction)."""
    global _trash_table_ready
    if _trash_table_ready:
        return
    own = conn is None
    if own:
        conn = get_db()
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS trash_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            kind TEXT NOT NULL,
            label TEXT DEFAULT '',
            detail TEXT DEFAULT '',
            payload TEXT DEFAULT '{}',
            deleted_at REAL NOT NULL
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_trash_items_user ON trash_items(user_id, deleted_at DESC)")
        if own:
            conn.commit()
        _trash_table_ready = True
    finally:
        if own:
            conn.close()

def _trash_snapshot(conn, table, where, params=()):
    return [dict(r) for r in conn.execute(f"SELECT * FROM {table} WHERE {where}", params).fetchall()]

def _trash_insert(conn, table, row, keep_id=True):
    """Réinsère une ligne sauvegardée (colonnes inconnues ignorées). Renvoie l'id utilisé."""
    cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    data = {k: v for k, v in row.items() if k in cols}
    if not keep_id:
        data.pop('id', None)
    names = list(data.keys())
    sql = f"INSERT INTO {table} ({','.join(names)}) VALUES ({','.join('?' * len(names))})"
    try:
        cur = conn.execute(sql, [data[n] for n in names])
    except sqlite3.IntegrityError:
        if 'id' not in data:
            raise
        data.pop('id')   # id déjà repris entre-temps : on en attribue un nouveau
        names = list(data.keys())
        cur = conn.execute(f"INSERT INTO {table} ({','.join(names)}) VALUES ({','.join('?' * len(names))})", [data[n] for n in names])
    return data.get('id') or cur.lastrowid

def _trash_rm(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        elif os.path.exists(path):
            os.remove(path)
    except OSError:
        pass

def trash_record(conn, user_id, kind, label, payload, detail='', files=()):
    """Met un élément en corbeille. `files` : fichiers ou dossiers associés, déplacés dans la corbeille avec lui."""
    _ensure_trash_table(conn)
    payload = dict(payload or {})
    tid = conn.execute("INSERT INTO trash_items (user_id, kind, label, detail, payload, deleted_at) VALUES (?,?,?,?,?,?)",
                       (user_id, kind, (label or '')[:200], (detail or '')[:200], '{}', time.time())).lastrowid
    moved = []
    dest_dir = os.path.join(TRASH_ITEMS_DIR, str(tid))
    for i, p in enumerate(files or []):
        if not p or not os.path.exists(p):
            continue
        try:
            os.makedirs(dest_dir, exist_ok=True)
            _base = os.path.basename(p.rstrip('/\\'))   # hors de l'f-string : un antislash y est interdit avant Python 3.12
            stored = os.path.join(dest_dir, f"{i}_{_base}")
            shutil.move(p, stored)
            moved.append({'orig': p, 'stored': stored})
        except Exception as e:
            app_logger.warning(f"[Trash] Pièce jointe non déplacée ({p}): {e}")
    payload['files'] = moved
    conn.execute("UPDATE trash_items SET payload = ? WHERE id = ?", (json.dumps(payload, ensure_ascii=False, default=str), tid))
    return tid

def _trash_purge_row(conn, tid):
    conn.execute("DELETE FROM trash_items WHERE id = ?", (tid,))
    _trash_rm(os.path.join(TRASH_ITEMS_DIR, str(tid)))

def _trash_purge_expired_rows():
    keep = _trash_retention_seconds()
    if keep <= 0:
        return
    try:
        _ensure_trash_table()
        conn = get_db()
        try:
            for r in conn.execute("SELECT id FROM trash_items WHERE deleted_at < ?", (time.time() - keep,)).fetchall():
                _trash_purge_row(conn, r['id'])
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        app_logger.warning(f"[Trash] Purge des éléments expirés impossible: {e}")

def _trash_restore_files_of(payload):
    for f in payload.get('files', []):
        stored, orig = f.get('stored'), f.get('orig')
        if not stored or not orig or not os.path.exists(stored):
            continue
        try:
            os.makedirs(os.path.dirname(orig), exist_ok=True)
            if os.path.exists(orig):
                continue
            shutil.move(stored, orig)
        except Exception as e:
            app_logger.warning(f"[Trash] Pièce jointe non restaurée ({orig}): {e}")

def _trash_restore_row(conn, item):
    """Restaure un élément. Renvoie (ok, message_d_erreur)."""
    kind = item['kind']
    p = json.loads(item['payload'] or '{}')
    uid = item['user_id']
    if kind == 'quote':
        _trash_insert(conn, 'quotes', p['row'])
        _trash_restore_files_of(p)
    elif kind == 'client':
        _ensure_quote_columns()
        new_id = _trash_insert(conn, 'clients', p['row'])
        qids = [int(x) for x in p.get('quote_ids', [])]
        if qids:
            conn.execute(f"UPDATE quotes SET client_id = ? WHERE user_id = ? AND client_id = 0 AND id IN ({','.join('?' * len(qids))})", [new_id, uid] + qids)
    elif kind == 'order':
        _trash_insert(conn, 'print_jobs', p['row'])
    elif kind == 'spool':
        _trash_insert(conn, 'manual_filament_spools', p['row'])
    elif kind == 'project':
        old_id = p['row'].get('id')
        new_id = _trash_insert(conn, 'projects', p['row'])
        for r in p.get('project_files', []):
            r = dict(r); r['project_id'] = new_id
            try:
                _trash_insert(conn, 'project_files', r)
            except sqlite3.IntegrityError:
                pass
        for r in p.get('gcodes', []):
            r = dict(r); r['project_id'] = new_id
            _trash_insert(conn, 'project_gcodes', r, keep_id=False)
        for f in p.get('files', []):   # dossier des G-codes : suit le nouvel identifiant du projet
            if f.get('orig') and old_id is not None and os.path.basename(f['orig'].rstrip('/\\')) == str(old_id):
                f['orig'] = os.path.join(os.path.dirname(f['orig'].rstrip('/\\')), str(new_id))
        _trash_restore_files_of(p)
    else:
        return False, 'Type inconnu'
    return True, ''

_TRASH_KIND_ICONS = {'files': 'fa-file', 'quote': 'fa-file-invoice', 'client': 'fa-address-book', 'order': 'fa-box',
                     'project': 'fa-diagram-project', 'spool': 'fa-circle-nodes'}

def _trash_list_for_user(uid):
    now = time.time()
    keep = _trash_retention_seconds()
    out = []
    with _trash_registry_lock:
        batches = list(_trash_registry.items())
    for bid, entry in batches:
        if entry.get('user_id') != uid:
            continue
        names = [os.path.basename(e.get('original', '')) for e in entry.get('entries', [])]
        if not names:
            continue
        deleted_at = entry.get('created_at', now)
        out.append({'key': f'files:{bid}', 'kind': 'files', 'label': names[0] if len(names) == 1 else f'{names[0]} (+{len(names) - 1})',
                    'detail': '', 'count': len(names), 'names': names[:5], 'deleted_at': deleted_at,
                    'seconds_left': int(keep - (now - deleted_at)) if keep > 0 else None})
    try:
        _ensure_trash_table()
        conn = get_db()
        try:
            rows = conn.execute("SELECT id, kind, label, detail, deleted_at FROM trash_items WHERE user_id = ? ORDER BY deleted_at DESC", (uid,)).fetchall()
        finally:
            conn.close()
        for r in rows:
            out.append({'key': f"row:{r['id']}", 'kind': r['kind'], 'label': r['label'], 'detail': r['detail'], 'count': 1,
                        'names': [], 'deleted_at': r['deleted_at'],
                        'seconds_left': int(keep - (now - r['deleted_at'])) if keep > 0 else None})
    except Exception as e:
        app_logger.warning(f"[Trash] Lecture des éléments impossible: {e}")
    out.sort(key=lambda x: -x['deleted_at'])
    return out


_ROUTES = (
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"trash_core.init : services manquants : {missing}")
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
