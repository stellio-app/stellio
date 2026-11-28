"""Stellio — séchage des bobines, calibrations et pièces d'usure (1.2.2)

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `workshop_logs.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import datetime
import re

_REQUIRED = (
    'app',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'session',
)
_OPTIONAL = ()   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('datetime', 're', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
app = None
get_db = None
jsonify = None
login_required = None
request = None
session = None


_DRYING_ADVICE = {
    'PLA':  {'temp_c': 45, 'hours': 6,  'interval_days': 90, 'sensitivity': 'low'},
    'PETG': {'temp_c': 65, 'hours': 6,  'interval_days': 45, 'sensitivity': 'medium'},
    'ABS':  {'temp_c': 80, 'hours': 4,  'interval_days': 90, 'sensitivity': 'low'},
    'ASA':  {'temp_c': 80, 'hours': 4,  'interval_days': 90, 'sensitivity': 'low'},
    'TPU':  {'temp_c': 50, 'hours': 8,  'interval_days': 30, 'sensitivity': 'high'},
    'PC':   {'temp_c': 80, 'hours': 8,  'interval_days': 30, 'sensitivity': 'high'},
    'PA':   {'temp_c': 75, 'hours': 10, 'interval_days': 14, 'sensitivity': 'high'},
    'PVA':  {'temp_c': 50, 'hours': 8,  'interval_days': 10, 'sensitivity': 'high'},
    'BVOH': {'temp_c': 50, 'hours': 8,  'interval_days': 10, 'sensitivity': 'high'},
}

_DRYING_ALIASES = {
    'NYLON': 'PA', 'PA6': 'PA', 'PA12': 'PA', 'PA66': 'PA', 'PAHT': 'PA', 'PPA': 'PA',
    'TPE': 'TPU', 'PCTG': 'PETG', 'PET': 'PETG', 'PETG': 'PETG',
}

_DRYING_SOURCES = ('spoolman', 'manual', 'tigertag')

_DRYING_KINDS = ('dried', 'opened', 'sealed')

_DRYING_DEFAULT_INTERVAL_DAYS = 60

def _drying_advice_for(material):
    token = ''
    for part in re.split(r'[^A-Za-z0-9]+', str(material or '').upper()):
        if part:
            token = part
            break
    token = _DRYING_ALIASES.get(token, token)
    advice = _DRYING_ADVICE.get(token)
    return dict(advice, material_class=token) if advice else None

def _drying_state(last_event, material):
    advice = _drying_advice_for(material)
    interval = advice['interval_days'] if advice else _DRYING_DEFAULT_INTERVAL_DAYS
    if not last_event:
        return {"state": "none", "interval_days": interval, "days_since": None}
    if last_event['kind'] == 'sealed':
        return {"state": "sealed", "interval_days": interval, "days_since": None}
    try:
        days = (datetime.datetime.now() - datetime.datetime.fromisoformat(last_event['event_at'])).total_seconds() / 86400
    except Exception:
        return {"state": "none", "interval_days": interval, "days_since": None}
    days = max(days, 0)
    return {"state": "due" if days >= interval else "ok", "interval_days": interval, "days_since": round(days, 1)}

def _drying_opt_float(value, lo, hi):
    if value in (None, ''):
        return None
    v = float(value)
    if v < lo or v > hi:
        raise ValueError("hors limites")
    return v

def api_drying_get():
    source_type = (request.args.get('source_type') or '').strip()
    source_id = str(request.args.get('source_id') or '').strip()
    material = (request.args.get('material') or '').strip()
    if source_type not in _DRYING_SOURCES or not source_id:
        return jsonify({"error": "Bobine invalide"}), 400
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, kind, event_at, temp_c, duration_h, humidity_pct, notes, material FROM spool_drying_log "
            "WHERE user_id=? AND source_type=? AND source_id=? ORDER BY event_at DESC, id DESC LIMIT 30",
            (session['user_id'], source_type, source_id)
        ).fetchall()
    finally:
        conn.close()
    events = [dict(r) for r in rows]
    material = material or (events[0]['material'] if events else '')
    return jsonify({
        "events": events,
        "status": _drying_state(events[0] if events else None, material),
        "advice": _drying_advice_for(material),
    }), 200

def api_drying_add():
    data = request.json or {}
    source_type = (data.get('source_type') or '').strip()
    source_id = str(data.get('source_id') or '').strip()
    kind = (data.get('kind') or 'dried').strip()
    if source_type not in _DRYING_SOURCES or not source_id:
        return jsonify({"error": "Bobine invalide"}), 400
    if kind not in _DRYING_KINDS:
        return jsonify({"error": "Type d'événement invalide"}), 400
    try:
        temp_c = _drying_opt_float(data.get('temp_c'), 20, 120)
        duration_h = _drying_opt_float(data.get('duration_h'), 0.1, 72)
        humidity = _drying_opt_float(data.get('humidity_pct'), 0, 100)
    except (TypeError, ValueError):
        return jsonify({"error": "Valeur numérique invalide"}), 400
    event_at = (data.get('event_at') or '').strip()
    if event_at:
        try:
            parsed = datetime.datetime.fromisoformat(event_at)
            if parsed > datetime.datetime.now() + datetime.timedelta(days=1):
                return jsonify({"error": "Date dans le futur"}), 400
            event_at = parsed.isoformat(timespec='seconds')
        except ValueError:
            return jsonify({"error": "Date invalide"}), 400
    else:
        event_at = datetime.datetime.now().isoformat(timespec='seconds')
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO spool_drying_log (user_id, source_type, source_id, source_label, material, kind, event_at, temp_c, duration_h, humidity_pct, notes) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (session['user_id'], source_type, source_id, (data.get('source_label') or '')[:120],
             (data.get('material') or '')[:40], kind, event_at, temp_c, duration_h, humidity,
             (data.get('notes') or '')[:300])
        )
        conn.commit()
    finally:
        conn.close()
    return jsonify({"success": True}), 201

def api_drying_delete(event_id):
    conn = get_db()
    try:
        cur = conn.execute("DELETE FROM spool_drying_log WHERE id=? AND user_id=?", (event_id, session['user_id']))
        conn.commit()
        found = cur.rowcount > 0
    finally:
        conn.close()
    if not found:
        return jsonify({"error": "Événement introuvable"}), 404
    return jsonify({"success": True}), 200

def api_drying_due():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT l.* FROM spool_drying_log l "
            "JOIN (SELECT source_type, source_id, MAX(event_at) AS m FROM spool_drying_log WHERE user_id=? GROUP BY source_type, source_id) x "
            "ON x.source_type=l.source_type AND x.source_id=l.source_id AND x.m=l.event_at "
            "WHERE l.user_id=? ORDER BY l.id DESC",
            (session['user_id'], session['user_id'])
        ).fetchall()
    finally:
        conn.close()
    due, seen = [], set()
    for r in rows:
        key = (r['source_type'], r['source_id'])
        if key in seen:
            continue
        seen.add(key)
        status = _drying_state(r, r['material'])
        if status['state'] == 'due':
            due.append({
                "source_type": r['source_type'], "source_id": r['source_id'],
                "name": r['source_label'] or r['source_id'], "material": r['material'],
                "days_since": status['days_since'], "interval_days": status['interval_days'],
            })
    return jsonify({"due": due}), 200

_CAL_LIMITS = {
    'nozzle_diameter': (0.1, 2.0), 'nozzle_temp': (100, 500), 'bed_temp': (0, 150),
    'flow_ratio': (0.5, 1.5), 'pressure_advance': (0, 2), 'max_flow': (1, 100), 'retraction_mm': (0, 15),
}

def _clean_calibration(data, conn, partial=False):
    out = {}
    for field, (lo, hi) in _CAL_LIMITS.items():
        if field not in data and partial:
            continue
        raw = data.get(field)
        if raw in (None, ''):
            out[field] = 0.4 if field == 'nozzle_diameter' else None
            continue
        try:
            v = float(raw)
        except (TypeError, ValueError):
            return None, f"Valeur invalide : {field}"
        if v < lo or v > hi:
            return None, f"Valeur hors limites : {field}"
        out[field] = v
    for field, maxlen in (('brand', 60), ('material', 40), ('color_name', 60), ('notes', 400)):
        if field in data or not partial:
            out[field] = str(data.get(field) or '').strip()[:maxlen]
    if 'material' in out and not out['material']:
        return None, "Matière requise"
    if 'printer_id' in data or not partial:
        pid = data.get('printer_id')
        if pid in (None, ''):
            out['printer_id'] = None
        else:
            try:
                pid = int(pid)
            except (TypeError, ValueError):
                return None, "Imprimante invalide"
            if not conn.execute("SELECT id FROM printers WHERE id=? AND user_id=?", (pid, session['user_id'])).fetchone():
                return None, "Imprimante introuvable"
            out['printer_id'] = pid
    return out, None

_CAL_SELECT = (
    "SELECT c.*, p.name AS printer_name FROM filament_calibrations c "
    "LEFT JOIN printers p ON p.id = c.printer_id "
)

def api_calibrations_list():
    brand = (request.args.get('brand') or '').strip().lower()
    material = (request.args.get('material') or '').strip().lower()
    conn = get_db()
    try:
        rows = conn.execute(
            _CAL_SELECT + "WHERE c.user_id=? ORDER BY c.validated_at DESC, c.id DESC", (session['user_id'],)
        ).fetchall()
    finally:
        conn.close()
    items = [dict(r) for r in rows]
    if material:
        items = [c for c in items if (c['material'] or '').lower() == material]
    if brand:
        items = [c for c in items if (c['brand'] or '').lower() in ('', brand)]
    return jsonify({"calibrations": items}), 200

def api_calibrations_save():
    data = request.json or {}
    conn = get_db()
    try:
        vals, err = _clean_calibration(data, conn)
        if err:
            return jsonify({"error": err}), 400
        vals['validated_at'] = datetime.datetime.now().isoformat(timespec='seconds')
        existing = conn.execute(
            "SELECT id FROM filament_calibrations WHERE user_id=? AND COALESCE(printer_id,0)=COALESCE(?,0) "
            "AND lower(brand)=lower(?) AND lower(material)=lower(?) AND nozzle_diameter=?",
            (session['user_id'], vals['printer_id'], vals['brand'], vals['material'], vals['nozzle_diameter'])
        ).fetchone()
        if existing:
            cols = list(vals.keys())
            conn.execute(
                f"UPDATE filament_calibrations SET {', '.join(c + '=?' for c in cols)} WHERE id=?",
                [vals[c] for c in cols] + [existing['id']]
            )
            cid = existing['id']
        else:
            cols = list(vals.keys()) + ['user_id']
            cur = conn.execute(
                f"INSERT INTO filament_calibrations ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
                [vals[c] for c in vals] + [session['user_id']]
            )
            cid = cur.lastrowid
        conn.commit()
    finally:
        conn.close()
    return jsonify({"success": True, "id": cid, "updated": bool(existing)}), 200

def api_calibrations_delete(cal_id):
    conn = get_db()
    try:
        cur = conn.execute("DELETE FROM filament_calibrations WHERE id=? AND user_id=?", (cal_id, session['user_id']))
        conn.commit()
        found = cur.rowcount > 0
    finally:
        conn.close()
    if not found:
        return jsonify({"error": "Calibration introuvable"}), 404
    return jsonify({"success": True}), 200

def api_calibrations_suggest():
    brand = (request.args.get('brand') or '').strip().lower()
    material = (request.args.get('material') or '').strip().lower()
    try:
        printer_id = int(request.args.get('printer_id')) if request.args.get('printer_id') not in (None, '') else None
    except ValueError:
        printer_id = None
    if not material:
        return jsonify({"calibration": None, "match": None}), 200
    conn = get_db()
    try:
        rows = conn.execute(
            _CAL_SELECT + "WHERE c.user_id=? AND lower(c.material)=? ORDER BY c.validated_at DESC, c.id DESC",
            (session['user_id'], material)
        ).fetchall()
    finally:
        conn.close()
    best, best_score, best_match = None, -1, None
    for r in rows:
        same_printer = printer_id is not None and r['printer_id'] == printer_id
        same_brand = bool(brand) and (r['brand'] or '').lower() == brand
        score = (2 if same_printer else 0) + (1 if same_brand else 0)
        if score > best_score:
            best, best_score = r, score
            best_match = 'exact' if (same_printer and same_brand) else ('printer' if same_printer else ('brand' if same_brand else 'material'))
    return jsonify({"calibration": dict(best) if best else None, "match": best_match}), 200

def _owned_part_id(conn, raw):
    try:
        pid = int(raw)
    except (TypeError, ValueError):
        return None
    row = conn.execute("SELECT id FROM printer_parts WHERE id=? AND user_id=?", (pid, session['user_id'])).fetchone()
    return row['id'] if row else None

def _serialize_part(r):
    d = dict(r)
    d['low'] = (d.get('stock_qty') or 0) <= (d.get('alert_qty') or 0)
    return d

def _clean_part(data, conn):
    name = str(data.get('name') or '').strip()[:100]
    if not name:
        return None, "Nom requis"
    try:
        stock = int(data.get('stock_qty') or 0)
        alert = int(data.get('alert_qty') if data.get('alert_qty') not in (None, '') else 1)
    except (TypeError, ValueError):
        return None, "Quantité invalide"
    if stock < 0 or stock > 100000 or alert < 0 or alert > 100000:
        return None, "Quantité hors limites"
    printer_id = data.get('printer_id')
    if printer_id in (None, '', 0, '0'):
        printer_id = None
    else:
        try:
            printer_id = int(printer_id)
        except (TypeError, ValueError):
            return None, "Imprimante invalide"
        if not conn.execute("SELECT id FROM printers WHERE id=? AND user_id=?", (printer_id, session['user_id'])).fetchone():
            return None, "Imprimante introuvable"
    buy_url = str(data.get('buy_url') or '').strip()[:500]
    if buy_url and not buy_url.lower().startswith(('http://', 'https://')):
        return None, "Lien d'achat invalide (http/https)"
    return {
        'name': name, 'category': str(data.get('category') or 'other').strip()[:30] or 'other',
        'stock_qty': stock, 'alert_qty': alert, 'printer_id': printer_id,
        'buy_url': buy_url, 'notes': str(data.get('notes') or '').strip()[:300],
    }, None

_PARTS_SELECT = (
    "SELECT pt.*, p.name AS printer_name FROM printer_parts pt "
    "LEFT JOIN printers p ON p.id = pt.printer_id "
)

def api_parts_list():
    conn = get_db()
    try:
        rows = conn.execute(_PARTS_SELECT + "WHERE pt.user_id=? ORDER BY pt.name COLLATE NOCASE", (session['user_id'],)).fetchall()
    finally:
        conn.close()
    return jsonify({"parts": [_serialize_part(r) for r in rows]}), 200

def api_parts_create():
    conn = get_db()
    try:
        vals, err = _clean_part(request.json or {}, conn)
        if err:
            return jsonify({"error": err}), 400
        cols = list(vals.keys()) + ['user_id']
        cur = conn.execute(
            f"INSERT INTO printer_parts ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            [vals[c] for c in vals] + [session['user_id']]
        )
        conn.commit()
        pid = cur.lastrowid
    finally:
        conn.close()
    return jsonify({"success": True, "id": pid}), 201

def api_parts_update(part_id):
    conn = get_db()
    try:
        if not conn.execute("SELECT id FROM printer_parts WHERE id=? AND user_id=?", (part_id, session['user_id'])).fetchone():
            return jsonify({"error": "Pièce introuvable"}), 404
        vals, err = _clean_part(request.json or {}, conn)
        if err:
            return jsonify({"error": err}), 400
        cols = list(vals.keys())
        conn.execute(
            f"UPDATE printer_parts SET {', '.join(c + '=?' for c in cols)} WHERE id=? AND user_id=?",
            [vals[c] for c in cols] + [part_id, session['user_id']]
        )
        conn.commit()
    finally:
        conn.close()
    return jsonify({"success": True}), 200

def api_parts_adjust(part_id):
    try:
        delta = int((request.json or {}).get('delta'))
    except (TypeError, ValueError):
        return jsonify({"error": "Variation invalide"}), 400
    if delta == 0 or abs(delta) > 1000:
        return jsonify({"error": "Variation invalide"}), 400
    conn = get_db()
    try:
        row = conn.execute("SELECT stock_qty, alert_qty FROM printer_parts WHERE id=? AND user_id=?", (part_id, session['user_id'])).fetchone()
        if not row:
            return jsonify({"error": "Pièce introuvable"}), 404
        new_stock = max(0, (row['stock_qty'] or 0) + delta)
        conn.execute("UPDATE printer_parts SET stock_qty=? WHERE id=?", (new_stock, part_id))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"success": True, "stock_qty": new_stock, "low": new_stock <= (row['alert_qty'] or 0)}), 200

def api_parts_delete(part_id):
    conn = get_db()
    try:
        cur = conn.execute("DELETE FROM printer_parts WHERE id=? AND user_id=?", (part_id, session['user_id']))
        conn.execute("UPDATE printer_maintenance_tasks SET part_id=NULL WHERE part_id=? AND user_id=?", (part_id, session['user_id']))
        conn.commit()
        found = cur.rowcount > 0
    finally:
        conn.close()
    if not found:
        return jsonify({"error": "Pièce introuvable"}), 404
    return jsonify({"success": True}), 200

def api_parts_low():
    conn = get_db()
    try:
        rows = conn.execute(
            _PARTS_SELECT + "WHERE pt.user_id=? AND pt.stock_qty <= pt.alert_qty ORDER BY pt.name COLLATE NOCASE",
            (session['user_id'],)
        ).fetchall()
    finally:
        conn.close()
    return jsonify({"parts": [_serialize_part(r) for r in rows]}), 200

def _month_bounds_ok(month):
    return bool(re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', month or ''))


_ROUTES = (
    ('/api/filament/drying', ['GET'], 'api_drying_get', ('login_required', )),
    ('/api/filament/drying', ['POST'], 'api_drying_add', ('login_required', )),
    ('/api/filament/drying/<int:event_id>', ['DELETE'], 'api_drying_delete', ('login_required', )),
    ('/api/filament/drying/due', ['GET'], 'api_drying_due', ('login_required', )),
    ('/api/calibrations', ['GET'], 'api_calibrations_list', ('login_required', )),
    ('/api/calibrations', ['POST'], 'api_calibrations_save', ('login_required', )),
    ('/api/calibrations/<int:cal_id>', ['DELETE'], 'api_calibrations_delete', ('login_required', )),
    ('/api/calibrations/suggest', ['GET'], 'api_calibrations_suggest', ('login_required', )),
    ('/api/parts', ['GET'], 'api_parts_list', ('login_required', )),
    ('/api/parts', ['POST'], 'api_parts_create', ('login_required', )),
    ('/api/parts/<int:part_id>', ['PUT'], 'api_parts_update', ('login_required', )),
    ('/api/parts/<int:part_id>/adjust', ['POST'], 'api_parts_adjust', ('login_required', )),
    ('/api/parts/<int:part_id>', ['DELETE'], 'api_parts_delete', ('login_required', )),
    ('/api/parts/low', ['GET'], 'api_parts_low', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"workshop_logs.init : services manquants : {missing}")
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
