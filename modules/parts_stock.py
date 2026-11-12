"""Stellio — stock de pièces finies (quantités, seuil, réassort par une tâche d'impression)

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `parts_stock.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.

Chaque pièce a une quantité en stock, un seuil minimal et une quantité de réassort. Quand le stock passe sous le seuil,
Stellio prévient (notification + push) et, si « réassort automatique » est coché, crée une tâche d'impression
(table `print_jobs`, colonne `stock_part_id`). Quand cette tâche avance, les pièces terminées sont ajoutées
automatiquement au stock (synchronisation paresseuse : à l'ouverture de la liste et au résumé périodique).
"""
import threading

_REQUIRED = (
    '_insert_notification_once',
    '_least_loaded_printer',
    '_push_notify_async',
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'session',
)
_OVERRIDABLE = ('threading',)

_MAIN = {}
_insert_notification_once = None
_least_loaded_printer = None
_push_notify_async = None
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None

_READY = False
_READY_LOCK = threading.Lock()
_SYNC_LOCK = threading.Lock()


def ensure_tables():
    global _READY
    if _READY:
        return
    with _READY_LOCK:
        if _READY:
            return
        conn = get_db()
        try:
            conn.execute("""CREATE TABLE IF NOT EXISTS parts_stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT NOT NULL, sku TEXT DEFAULT '',
                material TEXT DEFAULT '', qty INTEGER DEFAULT 0, min_qty INTEGER DEFAULT 0, reorder_qty INTEGER DEFAULT 10,
                auto_restock INTEGER DEFAULT 0, unit_price REAL DEFAULT 0, notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS parts_stock_moves (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, part_id INTEGER NOT NULL,
                delta INTEGER NOT NULL, reason TEXT DEFAULT '', ref TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
            cols = {r['name'] for r in conn.execute("PRAGMA table_info(print_jobs)").fetchall()}
            for name in ('stock_part_id', 'stock_credited'):
                if name not in cols:
                    conn.execute(f"ALTER TABLE print_jobs ADD COLUMN {name} INTEGER DEFAULT 0")
            conn.commit()
        finally:
            conn.close()
        _READY = True


def _int(v, default=0, lo=0, hi=1_000_000):
    try:
        return max(lo, min(hi, int(float(str(v).replace(',', '.')))))
    except (TypeError, ValueError):
        return default


def _num(v):
    try:
        f = float(str(v).replace(',', '.'))
        return f if f == f and abs(f) < 1e9 else 0.0
    except (TypeError, ValueError):
        return 0.0


def _move(conn, uid, part_id, delta, reason, ref=''):
    conn.execute("INSERT INTO parts_stock_moves (user_id, part_id, delta, reason, ref) VALUES (?,?,?,?,?)",
                 (uid, part_id, int(delta), str(reason)[:40], str(ref)[:80]))
    conn.execute("UPDATE parts_stock SET qty = MAX(qty + ?, 0), updated_at = CURRENT_TIMESTAMP WHERE id=? AND user_id=?",
                 (int(delta), part_id, uid))


def sync_completed_restocks(uid):
    """Ajoute au stock les pièces terminées des tâches de réassort (idempotent : `stock_credited` mémorise ce qui est déjà compté)."""
    ensure_tables()
    with _SYNC_LOCK:
        conn = get_db()
        try:
            rows = conn.execute(
                "SELECT id, stock_part_id, qty_done, stock_credited FROM print_jobs "
                "WHERE user_id=? AND stock_part_id>0 AND qty_done > COALESCE(stock_credited,0)", (uid,)).fetchall()
            n = 0
            for r in rows:
                delta = int(r['qty_done'] or 0) - int(r['stock_credited'] or 0)
                if not conn.execute("SELECT 1 FROM parts_stock WHERE id=? AND user_id=?", (r['stock_part_id'], uid)).fetchone():
                    conn.execute("UPDATE print_jobs SET stock_credited=qty_done WHERE id=?", (r['id'],))
                    continue
                _move(conn, uid, r['stock_part_id'], delta, 'restock', f"job:{r['id']}")
                conn.execute("UPDATE print_jobs SET stock_credited=qty_done WHERE id=?", (r['id'],))
                n += delta
            conn.commit()
            return n
        finally:
            conn.close()


def _incoming(conn, uid, part_id):
    r = conn.execute(
        "SELECT COALESCE(SUM(MAX(quantity - qty_done, 0)),0) AS n FROM print_jobs "
        "WHERE user_id=? AND stock_part_id=? AND status IN ('queued','printing')", (uid, part_id)).fetchone()
    return int(r['n'] or 0)


def _part_dict(conn, r):
    inc = _incoming(conn, r['user_id'], r['id'])
    return {'id': r['id'], 'name': r['name'], 'sku': r['sku'], 'material': r['material'], 'qty': r['qty'],
            'min_qty': r['min_qty'], 'reorder_qty': r['reorder_qty'], 'auto_restock': bool(r['auto_restock']),
            'unit_price': r['unit_price'], 'notes': r['notes'], 'incoming': inc,
            'low': int(r['qty'] or 0) <= int(r['min_qty'] or 0) and int(r['min_qty'] or 0) > 0,
            'value': round(float(r['unit_price'] or 0) * int(r['qty'] or 0), 2), 'updated_at': r['updated_at']}


def _create_restock_job(conn, uid, part, quantity):
    cur = conn.execute(
        "INSERT INTO print_jobs (user_id, quote_id, client, part, quantity, material, printer_id, notes, stock_part_id) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (uid, 0, 'Stock', str(part['name'])[:200], quantity, str(part['material'] or '')[:40].upper(),
         _least_loaded_printer(conn, uid), f"Réassort stock #{part['id']}", part['id']))
    return cur.lastrowid


def check_low_stock(uid):
    """Alerte (une fois par valeur de stock) et réassort automatique des pièces sous leur seuil. Retourne le nombre d'alertes."""
    ensure_tables()
    sync_completed_restocks(uid)
    alerts = 0
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM parts_stock WHERE user_id=? AND min_qty>0 AND qty<=min_qty", (uid,)).fetchall()
        for r in rows:
            inc = _incoming(conn, uid, r['id'])
            created = None
            if r['auto_restock'] and inc == 0 and int(r['reorder_qty'] or 0) > 0:
                created = _create_restock_job(conn, uid, r, int(r['reorder_qty']))
                conn.commit()
            title = f"Stock bas : {r['name']}"
            msg = f"{r['qty']} en stock (seuil {r['min_qty']})." + (" Une tâche de réassort a été créée." if created else (
                f" {inc} déjà en cours d'impression." if inc else ""))
            try:
                if _insert_notification_once(uid, 'warning', title, msg, 'orders', f"parts_low:{r['id']}:{r['qty']}"):
                    alerts += 1
                    _push_notify_async('warning', title, msg)
            except Exception as e:
                app_logger.warning(f"[STOCK] Notification impossible : {e}")
    finally:
        conn.close()
    return alerts


# ── Routes ──────────────────────────────────────────────────────────────────────────────────
def api_pstock_list():
    ensure_tables()
    uid = session['user_id']
    sync_completed_restocks(uid)
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM parts_stock WHERE user_id=? ORDER BY name COLLATE NOCASE", (uid,)).fetchall()
        parts = [_part_dict(conn, r) for r in rows]
    finally:
        conn.close()
    return jsonify({'parts': parts, 'low': sum(1 for p in parts if p['low']),
                    'total_value': round(sum(p['value'] for p in parts), 2)})


def _fields(data):
    return {'name': str(data.get('name') or '').strip()[:120], 'sku': str(data.get('sku') or '').strip()[:60],
            'material': str(data.get('material') or '').strip()[:40], 'min_qty': _int(data.get('min_qty')),
            'reorder_qty': _int(data.get('reorder_qty'), 10), 'auto_restock': 1 if data.get('auto_restock') else 0,
            'unit_price': round(_num(data.get('unit_price')), 2), 'notes': str(data.get('notes') or '').strip()[:300]}


def api_pstock_create():
    ensure_tables()
    data = request.get_json(silent=True) or {}
    f = _fields(data)
    if not f['name']:
        return jsonify({'success': False, 'error': 'name_required'}), 400
    uid = session['user_id']
    qty = _int(data.get('qty'))
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO parts_stock (user_id, name, sku, material, qty, min_qty, reorder_qty, auto_restock, unit_price, notes) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (uid, f['name'], f['sku'], f['material'], qty, f['min_qty'], f['reorder_qty'], f['auto_restock'], f['unit_price'], f['notes']))
        if qty:
            conn.execute("INSERT INTO parts_stock_moves (user_id, part_id, delta, reason) VALUES (?,?,?,?)", (uid, cur.lastrowid, qty, 'initial'))
        conn.commit()
        pid = cur.lastrowid
    finally:
        conn.close()
    check_low_stock(uid)
    return jsonify({'success': True, 'id': pid})


def api_pstock_update(pid):
    ensure_tables()
    data = request.get_json(silent=True) or {}
    f = _fields(data)
    if not f['name']:
        return jsonify({'success': False, 'error': 'name_required'}), 400
    uid = session['user_id']
    conn = get_db()
    try:
        cur = conn.execute(
            "UPDATE parts_stock SET name=?, sku=?, material=?, min_qty=?, reorder_qty=?, auto_restock=?, unit_price=?, notes=?, "
            "updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?",
            (f['name'], f['sku'], f['material'], f['min_qty'], f['reorder_qty'], f['auto_restock'], f['unit_price'], f['notes'], pid, uid))
        conn.commit()
        if not cur.rowcount:
            return jsonify({'success': False, 'error': 'not_found'}), 404
    finally:
        conn.close()
    check_low_stock(uid)
    return jsonify({'success': True})


def api_pstock_delete(pid):
    ensure_tables()
    uid = session['user_id']
    conn = get_db()
    try:
        conn.execute("DELETE FROM parts_stock_moves WHERE part_id=? AND user_id=?", (pid, uid))
        conn.execute("UPDATE print_jobs SET stock_part_id=0 WHERE stock_part_id=? AND user_id=?", (pid, uid))
        cur = conn.execute("DELETE FROM parts_stock WHERE id=? AND user_id=?", (pid, uid))
        conn.commit()
        if not cur.rowcount:
            return jsonify({'success': False, 'error': 'not_found'}), 404
    finally:
        conn.close()
    return jsonify({'success': True})


def api_pstock_adjust(pid):
    """Ajoute ou retire des pièces (`delta` > 0 : entrée, < 0 : sortie/vente) ; `set` fixe la quantité après un inventaire."""
    ensure_tables()
    data = request.get_json(silent=True) or {}
    uid = session['user_id']
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM parts_stock WHERE id=? AND user_id=?", (pid, uid)).fetchone()
        if not row:
            return jsonify({'success': False, 'error': 'not_found'}), 404
        if 'set' in data:
            delta = _int(data.get('set')) - int(row['qty'] or 0)
            reason = 'inventory'
        else:
            delta = _int(data.get('delta'), 0, -1_000_000, 1_000_000)
            reason = str(data.get('reason') or ('in' if delta > 0 else 'out'))[:40]
        if delta == 0:
            return jsonify({'success': True, 'qty': row['qty']})
        _move(conn, uid, pid, delta, reason, str(data.get('ref') or ''))
        conn.commit()
        qty = conn.execute("SELECT qty FROM parts_stock WHERE id=?", (pid,)).fetchone()['qty']
    finally:
        conn.close()
    check_low_stock(uid)
    return jsonify({'success': True, 'qty': qty})


def api_pstock_restock(pid):
    """Crée tout de suite une tâche d'impression de réassort (quantité demandée, sinon la quantité de réassort de la pièce)."""
    ensure_tables()
    data = request.get_json(silent=True) or {}
    uid = session['user_id']
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM parts_stock WHERE id=? AND user_id=?", (pid, uid)).fetchone()
        if not row:
            return jsonify({'success': False, 'error': 'not_found'}), 404
        qty = _int(data.get('quantity'), int(row['reorder_qty'] or 0), 0, 100000) or int(row['reorder_qty'] or 0)
        if qty <= 0:
            return jsonify({'success': False, 'error': 'quantity_required'}), 400
        jid = _create_restock_job(conn, uid, row, qty)
        conn.commit()
    finally:
        conn.close()
    return jsonify({'success': True, 'job_id': jid, 'quantity': qty})


def api_pstock_moves(pid):
    ensure_tables()
    conn = get_db()
    try:
        rows = conn.execute("SELECT delta, reason, ref, created_at FROM parts_stock_moves WHERE part_id=? AND user_id=? "
                            "ORDER BY id DESC LIMIT 100", (pid, session['user_id'])).fetchall()
    finally:
        conn.close()
    return jsonify({'moves': [dict(r) for r in rows]})


_ROUTES = (
    ('/api/parts-stock', ['GET'], 'api_pstock_list', ('login_required', )),
    ('/api/parts-stock', ['POST'], 'api_pstock_create', ('login_required', )),
    ('/api/parts-stock/<int:pid>', ['PUT'], 'api_pstock_update', ('login_required', )),
    ('/api/parts-stock/<int:pid>', ['DELETE'], 'api_pstock_delete', ('login_required', )),
    ('/api/parts-stock/<int:pid>/adjust', ['POST'], 'api_pstock_adjust', ('login_required', )),
    ('/api/parts-stock/<int:pid>/restock', ['POST'], 'api_pstock_restock', ('login_required', )),
    ('/api/parts-stock/<int:pid>/moves', ['GET'], 'api_pstock_moves', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"parts_stock.init : services manquants : {missing}")
    for n in _REQUIRED + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {}
