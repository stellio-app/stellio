"""Stellio — commandes

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `pro_orders.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import datetime
import json

_REQUIRED = (
    '_JOB_STATUSES',
    '_int_or0',
    '_iso_date',
    '_least_loaded_printer',
    '_num',
    '_quote_payload_path',
    '_stored_quote',
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
_OVERRIDABLE = ('datetime', 'json', )

_EXPORTS = ('_create_jobs_from_quote', '_job_margin', '_job_dict', '_job_fields')   # rendus au cœur et aux autres modules du plugin

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
_JOB_STATUSES = None
_int_or0 = None
_iso_date = None
_least_loaded_printer = None
_num = None
_quote_payload_path = None
_stored_quote = None
_trash_snapshot = None
app = None
get_db = None
jsonify = None
login_required = None
request = None
session = None
trash_record = None


def _job_margin(r, revenue, labor_rate=0.0):
    """Marge prévue (devis) et marge réelle à ce jour : matière et temps selon ce qui a été réellement imprimé,
    rebuts compris. Retourne None si la commande ne vient pas d'un devis chiffré."""
    try:
        m = json.loads(r['cost_model'] or '{}')
    except Exception:
        m = {}
    if not m or not revenue or not (m.get('m') or m.get('e') or m.get('w') or m.get('f')):
        return None
    qty = max(1, r['quantity'] or 1)
    done = min(r['qty_done'] or 0, qty)
    scrap = r['scrap'] or 0
    unit = m['m'] + m['e'] + m['w'] + m['f']
    est_cost = unit * qty
    time_cost = m['e'] + m['w']
    w_act = r['actual_weight_g']
    h_act = r['actual_hours'] or 0
    mat_pieces = (w_act / m['weight_g']) if (w_act is not None and m['weight_g'] > 0) else done
    time_pieces = (h_act / m['hours']) if (h_act > 0 and m['hours'] > 0) else done
    real_cost = (mat_pieces + scrap) * m['m'] + (time_pieces + scrap) * time_cost + m['f'] * done
    labor_est = labor_real = 0.0
    if labor_rate and labor_rate > 0:                         # v1.1.7 : temps de travail humain (préparation + par pièce) × taux horaire
        labor_est = production_planning.labor_cost(r, labor_rate, 'est')
        labor_real = production_planning.labor_cost(r, labor_rate, 'real')
        est_cost += labor_est
        real_cost += labor_real
    real_revenue = revenue * done / qty
    return {
        'revenue': round(revenue, 2), 'est_cost': round(est_cost, 2), 'est_margin': round(revenue - est_cost, 2),
        'est_margin_pct': round(100 * (revenue - est_cost) / revenue, 1),
        'real_cost': round(real_cost, 2), 'real_revenue': round(real_revenue, 2),
        'real_margin': round(real_revenue - real_cost, 2),
        'real_margin_pct': round(100 * (real_revenue - real_cost) / real_revenue, 1) if real_revenue else None,
        'measured': bool(h_act > 0 or w_act is not None),
        'labor_est': round(labor_est, 2), 'labor_real': round(labor_real, 2),
    }

def _create_jobs_from_quote(user_id, row):
    """Un devis accepté crée une tâche d'impression (pièce, quantité, matière), assignée à l'imprimante la moins chargée.
    Idempotent : rien n'est créé si le devis a déjà des tâches."""
    if (row['doc_type'] or 'quote') != 'quote':
        return 0
    conn = get_db()
    try:
        if conn.execute("SELECT 1 FROM print_jobs WHERE user_id=? AND quote_id=?", (user_id, row['id'])).fetchone():
            return 0
        data = {}
        try:
            with open(_quote_payload_path(row), 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {}
        part = str(data.get('item_name') or data.get('item_desc') or row['item_desc'] or row['number'] or 'Pièce')[:200]
        try:
            qty = max(1, int(float(str(data.get('qty') or row['qty'] or 1).replace(',', '.'))))
        except (TypeError, ValueError):
            qty = 1
        material = str(data.get('material') or '')[:40].upper()
        due = _iso_date(data.get('delivery_iso')) or ''
        model = data.get('cost_model') if isinstance(data.get('cost_model'), dict) else {}
        model = {k: _num(model.get(k)) for k in ('m', 'e', 'w', 'f', 'weight_g', 'hours')}
        conn.execute(
            "INSERT INTO print_jobs (user_id, quote_id, client, part, quantity, material, printer_id, due_date, notes, cost_model) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (user_id, row['id'], str(row['client'] or '')[:120], part, qty, material,
             _least_loaded_printer(conn, user_id), due, str(row['number'] or ''), json.dumps(model)))
        conn.commit()
        return 1
    finally:
        conn.close()

def _job_dict(r, printer_names, revenue=0, labor_rate=0.0):
    today = datetime.date.today().isoformat()
    open_ = r['status'] in ('queued', 'printing')
    return {
        'scrap': r['scrap'] or 0, 'actual_hours': round(r['actual_hours'] or 0, 2), 'actual_weight_g': r['actual_weight_g'],
        'est_hours': round(float(r['est_hours'] or 0), 3), 'hours_piece': round(production_planning.hours_per_piece(r), 3),
        'margin': _job_margin(r, revenue, labor_rate),
        'labor_setup_min': round(float(r['labor_setup_min'] or 0), 2), 'labor_min_piece': round(float(r['labor_min_piece'] or 0), 2),
        'labor_hours_actual': round(float(r['labor_hours_actual'] or 0), 2),
        'labor_hours': round(production_planning.labor_minutes(r, 'real') / 60.0, 2),
        'labor_hours_est': round(production_planning.labor_minutes(r, 'est') / 60.0, 2),
        'id': r['id'], 'quote_id': r['quote_id'], 'client': r['client'], 'part': r['part'],
        'quantity': r['quantity'], 'qty_done': r['qty_done'], 'material': r['material'],
        'printer_id': r['printer_id'], 'printer_name': printer_names.get(r['printer_id'], ''),
        'due_date': r['due_date'], 'status': r['status'], 'notes': r['notes'],
        'late': bool(open_ and r['due_date'] and r['due_date'] < today),
        'created_at': r['created_at'], 'done_at': r['done_at'],
        'track_token': r['track_token'] or '', 'client_note': r['client_note'] or '',
    }

def api_orders_list():
    conn = get_db()
    try:
        names = {p['id']: p['name'] for p in conn.execute("SELECT id, name FROM printers WHERE user_id=?", (session['user_id'],)).fetchall()}
        totals = {q['id']: q['total_value'] or 0 for q in conn.execute("SELECT id, total_value FROM quotes WHERE user_id=?", (session['user_id'],)).fetchall()}
        rows = conn.execute(
            "SELECT * FROM print_jobs WHERE user_id=? ORDER BY CASE status WHEN 'printing' THEN 0 WHEN 'queued' THEN 1 ELSE 2 END, "
            "CASE WHEN due_date='' THEN 1 ELSE 0 END, due_date, id", (session['user_id'],)).fetchall()
    finally:
        conn.close()
    _lr = (production_planning.load_settings_for(session['user_id']) or {}).get('labor_rate', 0.0)
    jobs = [_job_dict(r, names, totals.get(r['quote_id'], 0), _lr) for r in rows]
    return jsonify({
        'jobs': jobs, 'labor_rate': _lr,
        'margin_real': round(sum(j['margin']['real_margin'] for j in jobs if j['margin'] and j['qty_done']), 2),
        'margin_est': round(sum(j['margin']['est_margin'] for j in jobs if j['margin'] and j['status'] != 'cancelled'), 2),
        'printers': [{'id': k, 'name': v} for k, v in names.items()],
        'open': sum(1 for j in jobs if j['status'] in ('queued', 'printing')),
        'late': sum(1 for j in jobs if j['late']),
    })

def _job_fields(data, partial=False):
    out = {}
    if 'part' in data or not partial:
        part = str(data.get('part') or '').strip()[:200]
        if not part and not partial:
            return None
        if part:
            out['part'] = part
    for k, lim in (('client', 120), ('material', 40), ('notes', 300), ('client_note', 300)):
        if k in data:
            out[k] = str(data.get(k) or '').strip()[:lim]
    if 'quantity' in data:
        out['quantity'] = max(1, min(100000, _int_or0(data.get('quantity')) or 1))
    if 'qty_done' in data:
        out['qty_done'] = max(0, min(100000, _int_or0(data.get('qty_done'))))
    if 'scrap' in data:
        out['scrap'] = max(0, min(100000, _int_or0(data.get('scrap'))))
    if 'actual_hours' in data:
        out['actual_hours'] = max(0.0, min(100000.0, _num(data.get('actual_hours'))))
    for _k, _lim in (('labor_setup_min', 100000.0), ('labor_min_piece', 100000.0), ('labor_hours_actual', 100000.0)):
        if _k in data:
            out[_k] = max(0.0, min(_lim, _num(data.get(_k))))     # v1.1.7 : temps de travail humain
    if 'est_hours' in data:
        out['est_hours'] = max(0.0, min(100000.0, _num(data.get('est_hours'))))   # v1.1.5 : durée par pièce (planning)
    if 'actual_weight_g' in data:
        out['actual_weight_g'] = None if data.get('actual_weight_g') in (None, '') else max(0.0, min(1e7, _num(data.get('actual_weight_g'))))
    if 'due_date' in data:
        out['due_date'] = _iso_date(data.get('due_date')) or ''
    if 'printer_id' in data:
        out['printer_id'] = _int_or0(data.get('printer_id')) or None
    if 'status' in data and data.get('status') in _JOB_STATUSES:
        out['status'] = data['status']
    return out

def api_orders_create():
    f = _job_fields(request.get_json(silent=True) or {})
    if f is None:
        return jsonify({'success': False, 'error': 'part_required'}), 400
    conn = get_db()
    try:
        if f.get('printer_id') is None:
            f['printer_id'] = _least_loaded_printer(conn, session['user_id'])
        elif not conn.execute("SELECT 1 FROM printers WHERE id=? AND user_id=?", (f['printer_id'], session['user_id'])).fetchone():
            f['printer_id'] = None
        f.setdefault('quantity', 1)
        cols = list(f.keys())
        cur = conn.execute(
            f"INSERT INTO print_jobs (user_id, {', '.join(cols)}) VALUES (?, {', '.join('?' * len(cols))})",
            (session['user_id'], *[f[c] for c in cols]))
        conn.commit()
        return jsonify({'success': True, 'id': cur.lastrowid})
    finally:
        conn.close()

def api_orders_update(jid):
    f = _job_fields(request.get_json(silent=True) or {}, partial=True)
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM print_jobs WHERE id=? AND user_id=?", (jid, session['user_id'])).fetchone()
        if not row:
            return jsonify({'success': False, 'error': 'not_found'}), 404
        if 'printer_id' in f and f['printer_id'] and not conn.execute(
                "SELECT 1 FROM printers WHERE id=? AND user_id=?", (f['printer_id'], session['user_id'])).fetchone():
            f['printer_id'] = None
        qty = f.get('quantity', row['quantity'])
        done = min(f.get('qty_done', row['qty_done']), qty)
        f['qty_done'] = done
        status = f.get('status', row['status'])
        if 'qty_done' in f and status in ('queued', 'printing'):
            if done >= qty:
                status = 'done'
            elif done > 0:
                status = 'printing'
        if status == 'done' and done < qty and 'qty_done' not in (request.get_json(silent=True) or {}):
            f['qty_done'] = done = qty
        f['status'] = status
        f['done_at'] = datetime.date.today().isoformat() if status == 'done' else ''
        conn.execute(f"UPDATE print_jobs SET {', '.join(k + '=?' for k in f)} WHERE id=?", (*f.values(), jid))
        conn.commit()
        return jsonify({'success': True, 'status': status})
    finally:
        conn.close()

def api_orders_delete(jid):
    conn = get_db()
    try:
        rows = _trash_snapshot(conn, 'print_jobs', 'id = ? AND user_id = ?', (jid, session['user_id']))
        tid = None
        if rows:
            r = rows[0]
            tid = trash_record(conn, session['user_id'], 'order', r.get('part') or r.get('client') or f"#{jid}", {'row': r},
                               detail=str(r.get('client') or ''))
        conn.execute("DELETE FROM print_jobs WHERE id=? AND user_id=?", (jid, session['user_id']))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'success': True, 'trash_key': f"row:{tid}" if tid else None})

def api_orders_from_quote(qid):
    row = _stored_quote(qid)
    if not row:
        return jsonify({'success': False, 'error': 'not_found'}), 404
    return jsonify({'success': True, 'created': _create_jobs_from_quote(session['user_id'], row)})


_ROUTES = (
    ('/api/orders', ['GET'], 'api_orders_list', ('login_required', )),
    ('/api/orders', ['POST'], 'api_orders_create', ('login_required', )),
    ('/api/orders/<int:jid>', ['PUT'], 'api_orders_update', ('login_required', )),
    ('/api/orders/<int:jid>', ['DELETE'], 'api_orders_delete', ('login_required', )),
    ('/api/orders/from-quote/<int:qid>', ['POST'], 'api_orders_from_quote', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    import importlib
    g['production_planning'] = importlib.import_module('modules.production_planning')
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"pro_orders.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {k: g[k] for k in _EXPORTS}
