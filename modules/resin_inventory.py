"""Stellio — inventaire manuel de résine (BÊTA, v1.1.3)

Les flacons de résine (marque, nom, famille, couleur, volume, reste, prix, rangement, notes) se saisissent à la main, comme
l'inventaire manuel de filament : pas de synchronisation avec une imprimante, pas de décompte automatique (le bouton « Utiliser »
retire un volume en ml). Une table par instance, un inventaire par utilisateur. Marqué « Bêta » dans l'interface.

Module séparé de main.py (même schéma que collections_sets.py) : main.py appelle `resin_inventory.init(globals())`.
"""
_REQUIRED = (
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'session',
    'load_settings',
    'save_settings',
    '_spool_buy_info',
)
_OPTIONAL = ()
_OVERRIDABLE = ()

_MAIN = {}
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None
load_settings = None
save_settings = None
_spool_buy_info = None

KINDS = ('standard', 'abs_like', 'tough', 'flexible', 'water_washable', 'castable', 'dental', 'high_temp', 'other')
MAX_ML = 100000.0
RESTOCK_DEFAULT_ML = 200.0           # seuil « à commander » (total restant d'une même résine) ; 0 = désactivé
SNOOZE_DEFAULT_DAYS = 14
_SEARCH_WORD = {'fr': 'résine', 'en': 'resin', 'de': 'Resin', 'es': 'resina', 'pt': 'resina', 'it': 'resina', 'zh': '树脂', 'ja': 'レジン'}


def _ensure(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS resin_bottles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        brand TEXT DEFAULT '',
        kind TEXT DEFAULT 'standard',
        color_hex TEXT DEFAULT '',
        volume_ml REAL DEFAULT 1000,
        remaining_ml REAL DEFAULT 1000,
        price REAL,
        location TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")


def _num(v, lo=0.0, hi=MAX_ML):
    """Nombre dans [lo, hi] ; None si vide ; ValueError si invalide."""
    if v is None or str(v).strip() == '':
        return None
    f = float(str(v).replace(',', '.'))
    if f != f or f < lo or f > hi:
        raise ValueError('range')
    return f


def _color(v):
    v = str(v or '').strip()
    return v if len(v) == 7 and v[0] == '#' and all(c in '0123456789abcdefABCDEF' for c in v[1:]) else ''


def _row(r):
    return {'id': r['id'], 'name': r['name'], 'brand': r['brand'] or '', 'kind': r['kind'] or 'standard', 'color_hex': r['color_hex'] or '',
            'volume_ml': r['volume_ml'] or 0, 'remaining_ml': r['remaining_ml'] or 0, 'price': r['price'],
            'location': r['location'] or '', 'notes': r['notes'] or '', 'created_at': r['created_at']}


def _clean(d):
    """Valide le corps d'une requête ; renvoie (champs, None) ou (None, code d'erreur)."""
    name = str(d.get('name') or '').strip()
    if not name:
        return None, 'name_required'
    if len(name) > 120:
        return None, 'name_too_long'
    kind = str(d.get('kind') or 'standard')
    if kind not in KINDS:
        kind = 'other'
    try:
        volume = _num(d.get('volume_ml'), 1.0)
        remaining = _num(d.get('remaining_ml'), 0.0)
        price = _num(d.get('price'), 0.0, 1000000.0)
    except ValueError:
        return None, 'bad_number'
    volume = volume if volume is not None else 1000.0
    remaining = remaining if remaining is not None else volume
    if remaining > volume:
        return None, 'remaining_over_volume'
    return {'name': name, 'brand': str(d.get('brand') or '').strip()[:80], 'kind': kind, 'color_hex': _color(d.get('color_hex')),
            'volume_ml': volume, 'remaining_ml': remaining, 'price': price, 'location': str(d.get('location') or '').strip()[:80],
            'notes': str(d.get('notes') or '').strip()[:500]}, None


def api_resin_list():
    conn = get_db()
    try:
        _ensure(conn)
        rows = conn.execute("SELECT * FROM resin_bottles WHERE user_id = ? ORDER BY name COLLATE NOCASE, id", (session['user_id'],)).fetchall()
        manual = (load_settings() or {}).get('resin_restock_manual')
        manual = manual if isinstance(manual, dict) else {}
        items = [_row(r) for r in rows]
        for it, r in zip(items, rows):
            it['to_order'] = _key(r['brand'], r['name'], r['color_hex']) in manual
        return jsonify({'bottles': items, 'kinds': list(KINDS), 'total_remaining_ml': round(sum(i['remaining_ml'] for i in items), 1), 'beta': True})
    finally:
        conn.close()


def api_resin_save():
    d = request.get_json(silent=True) or {}
    f, err = _clean(d)
    if err:
        return jsonify({'error': err}), 400
    conn = get_db()
    try:
        _ensure(conn)
        if d.get('id'):
            r = conn.execute("SELECT id FROM resin_bottles WHERE id = ? AND user_id = ?", (int(d['id']), session['user_id'])).fetchone()
            if not r:
                return jsonify({'error': 'not_found'}), 404
            conn.execute("UPDATE resin_bottles SET name=?, brand=?, kind=?, color_hex=?, volume_ml=?, remaining_ml=?, price=?, location=?, notes=? WHERE id=?",
                         (f['name'], f['brand'], f['kind'], f['color_hex'], f['volume_ml'], f['remaining_ml'], f['price'], f['location'], f['notes'], r['id']))
            rid = r['id']
        else:
            rid = conn.execute("INSERT INTO resin_bottles (user_id, name, brand, kind, color_hex, volume_ml, remaining_ml, price, location, notes) VALUES (?,?,?,?,?,?,?,?,?,?)",
                               (session['user_id'], f['name'], f['brand'], f['kind'], f['color_hex'], f['volume_ml'], f['remaining_ml'], f['price'], f['location'], f['notes'])).lastrowid
        conn.commit()
        return jsonify({'success': True, 'id': rid})
    finally:
        conn.close()


def api_resin_use():
    """Retire un volume (ml) du reste d'un flacon ; ne descend jamais sous 0."""
    d = request.get_json(silent=True) or {}
    try:
        ml = _num(d.get('ml'), 0.0)
        rid = int(d.get('id') or 0)
    except (ValueError, TypeError):
        return jsonify({'error': 'bad_number'}), 400
    if not ml:
        return jsonify({'error': 'bad_number'}), 400
    conn = get_db()
    try:
        _ensure(conn)
        r = conn.execute("SELECT * FROM resin_bottles WHERE id = ? AND user_id = ?", (rid, session['user_id'])).fetchone()
        if not r:
            return jsonify({'error': 'not_found'}), 404
        left = round(max(0.0, (r['remaining_ml'] or 0) - ml), 1)
        conn.execute("UPDATE resin_bottles SET remaining_ml = ? WHERE id = ?", (left, rid))
        conn.commit()
        return jsonify({'success': True, 'remaining_ml': left})
    finally:
        conn.close()


def api_resin_delete():
    d = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        _ensure(conn)
        cur = conn.execute("DELETE FROM resin_bottles WHERE id = ? AND user_id = ?", (int(d.get('id') or 0), session['user_id']))
        conn.commit()
        if not cur.rowcount:
            return jsonify({'error': 'not_found'}), 404
        return jsonify({'success': True})
    finally:
        conn.close()


# ---------- À commander (même circuit que les filaments : seuil bas, case manuelle, boutiques, « commandé ») ----------
def _key(brand, name, color):
    return f"{(brand or '').strip().lower()}|{(name or '').strip().lower()}|{(color or '').strip().lower()}"


def _threshold_ml():
    try:
        v = float((load_settings() or {}).get('resin_restock_ml', RESTOCK_DEFAULT_ML))
        return v if v >= 0 else RESTOCK_DEFAULT_ML
    except (TypeError, ValueError):
        return RESTOCK_DEFAULT_ML


def api_resin_restock():
    """Résines (marque + nom + couleur, tous flacons confondus) sous le seuil, ou cochées « à commander » à la main."""
    import time
    st = load_settings() or {}
    manual = st.get('resin_restock_manual') if isinstance(st.get('resin_restock_manual'), dict) else {}
    snoozed = st.get('resin_restock_snoozed') if isinstance(st.get('resin_restock_snoozed'), dict) else {}
    include_snoozed = request.args.get('all') == '1'
    threshold = _threshold_ml()
    conn = get_db()
    try:
        _ensure(conn)
        rows = conn.execute("SELECT * FROM resin_bottles WHERE user_id = ?", (session['user_id'],)).fetchall()
    finally:
        conn.close()
    groups = {}
    for r in rows:
        k = _key(r['brand'], r['name'], r['color_hex'])
        g = groups.setdefault(k, {'key': k, 'name': r['name'], 'vendor': r['brand'] or '', 'kind': r['kind'] or 'standard',
                                  'color_hex': r['color_hex'] or '#888888', 'total_ml': 0.0, 'bottle_count': 0, 'ids': []})
        g['total_ml'] += max(float(r['remaining_ml'] or 0), 0.0)
        g['bottle_count'] += 1
        g['ids'].append(r['id'])
    for mk, meta in manual.items():                      # cochée à la main : listée même sans flacon
        if mk not in groups and isinstance(meta, dict):
            groups[mk] = {'key': mk, 'name': meta.get('name') or '', 'vendor': meta.get('vendor') or '', 'kind': 'standard',
                          'color_hex': meta.get('color_hex') or '#888888', 'total_ml': 0.0, 'bottle_count': 0, 'ids': []}
    word = _SEARCH_WORD.get(str((st or {}).get('lang', 'fr')), 'resin')
    now, items = time.time(), []
    for g in groups.values():
        is_manual = g['key'] in manual
        if not is_manual and (threshold <= 0 or g['total_ml'] > threshold):
            continue
        until = snoozed.get(g['key'])
        is_snoozed = bool(until) and float(until) > now
        if is_snoozed and not include_snoozed and not is_manual:
            continue
        g['total_ml'] = round(g['total_ml'], 1)
        g['manual'] = is_manual
        g['snoozed_until'] = float(until) if (is_snoozed and not is_manual) else None
        try:
            g.update(_spool_buy_info(g['vendor'], word, g['name']))
        except Exception as e:
            app_logger.info(f"[Resin] Boutiques ignorées: {e}")
            g['shops'] = []
        g['material'] = word
        items.append(g)
    items.sort(key=lambda x: (not x['manual'], x['total_ml']))
    return jsonify({'threshold_ml': threshold, 'items': items, 'manual_keys': list(manual.keys()), 'beta': True})


def api_resin_restock_flag():
    import time
    d = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        _ensure(conn)
        r = conn.execute("SELECT * FROM resin_bottles WHERE id = ? AND user_id = ?", (int(d.get('id') or 0), session['user_id'])).fetchone()
    finally:
        conn.close()
    if not r:
        return jsonify({'error': 'not_found'}), 404
    key = _key(r['brand'], r['name'], r['color_hex'])
    st = load_settings() or {}
    manual = dict(st.get('resin_restock_manual') or {})
    if d.get('flagged'):
        manual[key] = {'name': r['name'], 'vendor': r['brand'] or '', 'color_hex': r['color_hex'] or '', 'at': time.time()}
        snoozed = dict(st.get('resin_restock_snoozed') or {})
        if snoozed.pop(key, None) is not None:
            st['resin_restock_snoozed'] = snoozed
    else:
        manual.pop(key, None)
    st['resin_restock_manual'] = manual
    save_settings(st)
    return jsonify({'key': key, 'flagged': bool(d.get('flagged'))})


def api_resin_restock_snooze():
    """« Déjà commandé » : le rappel est mis en veille N jours (0 = réactiver) ; sort aussi la résine de la liste manuelle."""
    import time
    d = request.get_json(silent=True) or {}
    key = str(d.get('key') or '').strip()
    if not key or len(key) > 400:
        return jsonify({'error': 'bad_key'}), 400
    try:
        days = float(d.get('days', SNOOZE_DEFAULT_DAYS))
    except (TypeError, ValueError):
        return jsonify({'error': 'bad_number'}), 400
    days = max(0.0, min(days, 365.0))
    st = load_settings() or {}
    now = time.time()
    snoozed = {k: v for k, v in (st.get('resin_restock_snoozed') or {}).items() if isinstance(v, (int, float)) and v > now}
    if days > 0:
        snoozed[key] = now + days * 86400
        manual = dict(st.get('resin_restock_manual') or {})
        if manual.pop(key, None) is not None:
            st['resin_restock_manual'] = manual
    else:
        snoozed.pop(key, None)
    st['resin_restock_snoozed'] = snoozed
    save_settings(st)
    return jsonify({'success': True, 'snoozed_until': snoozed.get(key)})


def api_resin_restock_threshold():
    d = request.get_json(silent=True) or {}
    try:
        ml = _num(d.get('ml'), 0.0, 20000.0)
    except ValueError:
        return jsonify({'error': 'bad_number'}), 400
    st = load_settings() or {}
    st['resin_restock_ml'] = ml if ml is not None else RESTOCK_DEFAULT_ML
    save_settings(st)
    return jsonify({'success': True, 'threshold_ml': st['resin_restock_ml']})


_ROUTES = (
    ('/api/resin', ['GET'], 'api_resin_list', ('login_required', )),
    ('/api/resin/save', ['POST'], 'api_resin_save', ('login_required', )),
    ('/api/resin/use', ['POST'], 'api_resin_use', ('login_required', )),
    ('/api/resin/delete', ['POST'], 'api_resin_delete', ('login_required', )),
    ('/api/resin/restock', ['GET'], 'api_resin_restock', ('login_required', )),
    ('/api/resin/restock/flag', ['POST'], 'api_resin_restock_flag', ('login_required', )),
    ('/api/resin/restock/snooze', ['POST'], 'api_resin_restock_snooze', ('login_required', )),
    ('/api/resin/restock/threshold', ['POST'], 'api_resin_restock_threshold', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"resin_inventory.init : services manquants : {missing}")
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
