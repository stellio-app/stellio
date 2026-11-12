"""Stellio — clients (carnet de clients, import)

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `clients.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""

_REQUIRED = (
    '_client_clean',
    '_ensure_quote_columns',
    '_quote_eff_status',
    '_trash_snapshot',
    'app',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'session',
    'trash_record',
)
_OPTIONAL = ()   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ()

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
_client_clean = None
_ensure_quote_columns = None
_quote_eff_status = None
_trash_snapshot = None
app = None
get_db = None
jsonify = None
login_required = None
request = None
session = None
trash_record = None


def api_clients_list():
    _ensure_quote_columns()
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM clients WHERE user_id = ? ORDER BY name COLLATE NOCASE", (session['user_id'],)).fetchall()
        stats = {}
        for r in conn.execute("""SELECT client_id, COUNT(*) AS n, COALESCE(SUM(CASE WHEN doc_type IN ('invoice','deposit','credit') THEN total_value ELSE 0 END),0) AS billed
                                 FROM quotes WHERE user_id = ? AND client_id > 0 GROUP BY client_id""", (session['user_id'],)).fetchall():
            stats[r['client_id']] = (r['n'], r['billed'])
    finally:
        conn.close()
    out = []
    for r in rows:
        d = dict(r)
        d['docs'], d['billed'] = stats.get(r['id'], (0, 0))
        out.append(d)
    return jsonify({"clients": out})

def api_clients_create():
    _ensure_quote_columns()
    c = _client_clean(request.get_json(silent=True) or {})
    if not c['name']:
        return jsonify({"success": False, "error": "name_required"}), 400
    conn = get_db()
    try:
        if conn.execute("SELECT 1 FROM clients WHERE user_id = ? AND lower(name) = lower(?)", (session['user_id'], c['name'])).fetchone():
            return jsonify({"success": False, "error": "exists"}), 409
        cur = conn.execute("INSERT INTO clients (user_id, name, email, phone, address, tax_id, notes) VALUES (?,?,?,?,?,?,?)",
                           (session['user_id'], c['name'], c['email'], c['phone'], c['address'], c['tax_id'], c['notes']))
        conn.commit()
        return jsonify({"success": True, "id": cur.lastrowid})
    finally:
        conn.close()

def api_client_detail(cid):
    _ensure_quote_columns()
    conn = get_db()
    try:
        cl = conn.execute("SELECT * FROM clients WHERE id = ? AND user_id = ?", (cid, session['user_id'])).fetchone()
        if not cl:
            return jsonify({"error": "not_found"}), 404
        docs = conn.execute("""SELECT * FROM quotes WHERE user_id = ? AND (client_id = ? OR (client_id = 0 AND lower(client) = lower(?)))
                               ORDER BY id DESC LIMIT 200""", (session['user_id'], cid, cl['name'])).fetchall()
    finally:
        conn.close()
    history, billed, paid, outstanding = [], 0.0, 0.0, 0.0
    for r in docs:
        dt = r['doc_type'] or 'quote'
        st = _quote_eff_status(r)
        history.append({"id": r['id'], "number": r['number'], "doc_type": dt, "status": st, "total": r['total'],
                        "created_at": r['created_at'], "due_date": r['due_date'], "item_desc": r['item_desc']})
        if dt in ('invoice', 'deposit', 'credit'):
            v = float(r['total_value'] or 0)
            billed += v
            if dt == 'credit':
                continue
            if (r['status'] or 'draft') == 'paid':
                paid += v
            else:
                outstanding += v
    return jsonify({"client": dict(cl), "history": history, "billed": round(billed, 2), "paid": round(paid, 2), "outstanding": round(outstanding, 2)})

def api_client_update(cid):
    c = _client_clean(request.get_json(silent=True) or {})
    if not c['name']:
        return jsonify({"success": False, "error": "name_required"}), 400
    conn = get_db()
    try:
        dup = conn.execute("SELECT 1 FROM clients WHERE user_id = ? AND lower(name) = lower(?) AND id != ?", (session['user_id'], c['name'], cid)).fetchone()
        if dup:
            return jsonify({"success": False, "error": "exists"}), 409
        conn.execute("UPDATE clients SET name=?, email=?, phone=?, address=?, tax_id=?, notes=? WHERE id=? AND user_id=?",
                     (c['name'], c['email'], c['phone'], c['address'], c['tax_id'], c['notes'], cid, session['user_id']))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"success": True})

def api_client_delete(cid):
    conn = get_db()
    try:
        _ensure_quote_columns()
        rows = _trash_snapshot(conn, 'clients', 'id = ? AND user_id = ?', (cid, session['user_id']))
        tid = None
        if rows:
            qids = [r[0] for r in conn.execute("SELECT id FROM quotes WHERE client_id = ? AND user_id = ?", (cid, session['user_id'])).fetchall()]
            tid = trash_record(conn, session['user_id'], 'client', rows[0].get('name') or f"#{cid}", {'row': rows[0], 'quote_ids': qids})
        conn.execute("DELETE FROM clients WHERE id = ? AND user_id = ?", (cid, session['user_id']))
        conn.execute("UPDATE quotes SET client_id = 0 WHERE client_id = ? AND user_id = ?", (cid, session['user_id']))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"success": True, "trash_key": f"row:{tid}" if tid else None})

def api_clients_import():
    """Crée une fiche pour chaque nom de client déjà utilisé dans l'historique et rattache les documents."""
    _ensure_quote_columns()
    uid = session['user_id']
    conn = get_db()
    try:
        names = [r[0] for r in conn.execute("SELECT DISTINCT trim(client) FROM quotes WHERE user_id = ? AND trim(client) != '' AND client_id = 0", (uid,)).fetchall()]
        created = 0
        for n in names:
            ex = conn.execute("SELECT id FROM clients WHERE user_id = ? AND lower(name) = lower(?)", (uid, n)).fetchone()
            if ex:
                cid = ex['id']
            else:
                cid = conn.execute("INSERT INTO clients (user_id, name) VALUES (?, ?)", (uid, n[:120])).lastrowid
                created += 1
            conn.execute("UPDATE quotes SET client_id = ? WHERE user_id = ? AND client_id = 0 AND lower(trim(client)) = lower(?)", (cid, uid, n))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"success": True, "created": created})


_ROUTES = (
    ('/api/clients', ['GET'], 'api_clients_list', ('login_required', )),
    ('/api/clients', ['POST'], 'api_clients_create', ('login_required', )),
    ('/api/clients/<int:cid>', ['GET'], 'api_client_detail', ('login_required', )),
    ('/api/clients/<int:cid>', ['PUT'], 'api_client_update', ('login_required', )),
    ('/api/clients/<int:cid>', ['DELETE'], 'api_client_delete', ('login_required', )),
    ('/api/clients/import-from-quotes', ['POST'], 'api_clients_import', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"clients.init : services manquants : {missing}")
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
