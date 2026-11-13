"""Stellio — catalogue Open Filament Database (OFD)

Open Filament Database (https://openfilamentdatabase.org, Open Filament Collective, licence MIT) est une base ouverte
de bobines de filament : marques, matières, couleurs, tailles. Stellio télécharge son catalogue public au format
« Spoolman » (`filaments.json`, une ligne par bobine achetable, identifiant `ofd_<uuid>`), le garde en cache dans sa base
et permet de créer une bobine d'un clic (marque, matière, couleur, poids, diamètre, densité déjà remplis).

L'identifiant OFD est conservé sur la bobine (`manual_filament_spools.ofd_id`) ; il est aussi réutilisable avec les tags
OpenPrintTag. Pour une installation sans accès Internet, le fichier `filaments.json` peut être importé à la main.

Module séparé de main.py (même schéma que filament_weighing.py) : main.py appelle `open_filament_db.init(globals())`.
"""
import json
import threading
import time
import urllib.error
import urllib.request

_REQUIRED = (
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'session',
)
_OVERRIDABLE = ('threading', 'time')

_MAIN = {}
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None

SOURCE_URL = 'https://api.openfilamentdatabase.org/spoolman/filaments.json'
ATTRIBUTION = 'Open Filament Database — https://openfilamentdatabase.org (MIT)'
MAX_BYTES = 60 * 1024 * 1024
REFRESH_AFTER = 7 * 86400          # secondes : au-delà, une actualisation en arrière-plan est lancée à la première recherche
_LOCK = threading.Lock()
_READY = False
_REFRESHING = False


def ensure_tables():
    global _READY
    if _READY:
        return
    with _LOCK:
        if _READY:
            return
        conn = get_db()
        try:
            conn.execute("""CREATE TABLE IF NOT EXISTS ofd_catalog (
                id TEXT PRIMARY KEY, manufacturer TEXT DEFAULT '', name TEXT DEFAULT '', material TEXT DEFAULT '',
                density REAL, weight REAL, spool_weight REAL, diameter REAL, color_hex TEXT DEFAULT '',
                color_hexes TEXT DEFAULT '', extruder_temp REAL, bed_temp REAL, flags TEXT DEFAULT '',
                search TEXT DEFAULT '')""")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ofd_material ON ofd_catalog (material)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ofd_brand ON ofd_catalog (manufacturer)")
            conn.execute("CREATE TABLE IF NOT EXISTS ofd_meta (k TEXT PRIMARY KEY, v TEXT)")
            have = {r[1] for r in conn.execute("PRAGMA table_info(manual_filament_spools)").fetchall()}
            if have and 'ofd_id' not in have:
                conn.execute("ALTER TABLE manual_filament_spools ADD COLUMN ofd_id TEXT DEFAULT ''")
            if have and 'opt_json' not in have:
                conn.execute("ALTER TABLE manual_filament_spools ADD COLUMN opt_json TEXT DEFAULT ''")
            conn.commit()
        finally:
            conn.close()
        _READY = True


def _f(v):
    try:
        x = float(v)
        return x if x == x else None
    except (TypeError, ValueError):
        return None


def _hex(v):
    v = (str(v or '')).strip().lstrip('#').lower()
    return v if len(v) in (6, 8) and all(c in '0123456789abcdef' for c in v) else ''


def parse_catalog(raw):
    """Liste Spoolman (JSON) → lignes normalisées. Les entrées sans identifiant ou sans nom sont ignorées."""
    data = json.loads(raw) if isinstance(raw, (bytes, str)) else raw
    if isinstance(data, dict):
        data = data.get('filaments') or []
    rows = []
    for e in data:
        if not isinstance(e, dict):
            continue
        fid = str(e.get('id') or '').strip()
        name = str(e.get('name') or '').strip()
        if not fid or not name:
            continue
        brand = str(e.get('manufacturer') or '').strip()
        mat = str(e.get('material') or '').strip()
        hexes = [h for h in (_hex(x) for x in (e.get('color_hexes') or [])) if h]
        flags = {k: e[k] for k in ('finish', 'pattern') if e.get(k)}
        for k in ('translucent', 'glow'):
            if e.get(k):
                flags[k] = True
        rows.append((fid, brand, name, mat, _f(e.get('density')), _f(e.get('weight')), _f(e.get('spool_weight')),
                     _f(e.get('diameter')), _hex(e.get('color_hex')), ','.join(hexes), _f(e.get('extruder_temp')),
                     _f(e.get('bed_temp')), json.dumps(flags) if flags else '', f"{brand} {name} {mat}".lower()))
    return rows


def store_catalog(rows, etag=''):
    ensure_tables()
    conn = get_db()
    try:
        conn.execute("DELETE FROM ofd_catalog")
        conn.executemany("INSERT OR REPLACE INTO ofd_catalog (id, manufacturer, name, material, density, weight, spool_weight, "
                         "diameter, color_hex, color_hexes, extruder_temp, bed_temp, flags, search) "
                         "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
        for k, v in (('fetched_at', str(int(time.time()))), ('count', str(len(rows))), ('etag', etag or '')):
            conn.execute("INSERT OR REPLACE INTO ofd_meta (k, v) VALUES (?, ?)", (k, v))
        conn.commit()
    finally:
        conn.close()
    return len(rows)


def meta():
    ensure_tables()
    conn = get_db()
    try:
        m = {r['k']: r['v'] for r in conn.execute("SELECT k, v FROM ofd_meta").fetchall()}
    finally:
        conn.close()
    return {'count': int(m.get('count') or 0), 'fetched_at': int(m.get('fetched_at') or 0), 'etag': m.get('etag', ''),
            'source': SOURCE_URL, 'attribution': ATTRIBUTION}


def refresh(force=False, url=None):
    """Télécharge le catalogue (tient compte de l'ETag). Retourne {'updated': bool, 'count': n}."""
    m = meta()
    req = urllib.request.Request(url or SOURCE_URL, headers={'User-Agent': 'Stellio (+https://stellio-app.com)',
                                                              'Accept': 'application/json'})
    if m['etag'] and m['count'] and not force:
        req.add_header('If-None-Match', m['etag'])
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read(MAX_BYTES + 1)
            etag = r.headers.get('ETag', '')
    except urllib.error.HTTPError as e:
        if e.code == 304:
            store_catalog_touch()
            return {'updated': False, 'count': m['count']}
        raise
    if len(raw) > MAX_BYTES:
        raise ValueError('Catalogue trop volumineux')
    return {'updated': True, 'count': store_catalog(parse_catalog(raw), etag)}


def store_catalog_touch():
    conn = get_db()
    try:
        conn.execute("INSERT OR REPLACE INTO ofd_meta (k, v) VALUES ('fetched_at', ?)", (str(int(time.time())),))
        conn.commit()
    finally:
        conn.close()


def _bg_refresh():
    global _REFRESHING
    if _REFRESHING:
        return
    _REFRESHING = True

    def run():
        global _REFRESHING
        try:
            refresh()
        except Exception as e:
            app_logger.info(f"[OFD] Actualisation du catalogue impossible : {e}")
            try:
                store_catalog_touch()          # évite de réessayer à chaque recherche quand le réseau est coupé
            except Exception:
                pass
        finally:
            _REFRESHING = False
    threading.Thread(target=run, daemon=True).start()


def _like(s):
    return '%' + s.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'


def search(q='', material='', brand='', limit=30):
    ensure_tables()
    where, params = [], []
    for term in (q or '').lower().split()[:6]:
        where.append("search LIKE ? ESCAPE '\\'")
        params.append(_like(term))
    if material:
        where.append("LOWER(material) = ?")
        params.append(material.lower())
    if brand:
        where.append("LOWER(manufacturer) = ?")
        params.append(brand.lower())
    sql = ("SELECT id, manufacturer, name, material, density, weight, spool_weight, diameter, color_hex, color_hexes, "
           "extruder_temp, bed_temp FROM ofd_catalog" + (" WHERE " + " AND ".join(where) if where else "") +
           " ORDER BY manufacturer, name LIMIT ?")
    conn = get_db()
    try:
        return [dict(r) for r in conn.execute(sql, params + [max(1, min(int(limit), 100))]).fetchall()]
    finally:
        conn.close()


def spool_from_entry(e, remaining_g=None):
    """Champs d'une bobine Stellio depuis une ligne du catalogue."""
    cap = e.get('weight') or 1000.0
    color = e.get('color_hex') or (e.get('color_hexes') or '').split(',')[0]
    return {
        'name': e.get('name') or '', 'vendor': e.get('manufacturer') or '', 'material': e.get('material') or '',
        'color_hex': ('#' + color[:6]) if color else '#888888', 'capacity_g': float(cap),
        'remaining_g': float(cap if remaining_g is None else remaining_g), 'diameter_mm': float(e.get('diameter') or 1.75),
        'ofd_id': e.get('id') or '',
    }


# ── Routes ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def api_ofd_status():
    m = meta()
    if m['count'] == 0 or time.time() - m['fetched_at'] > REFRESH_AFTER:
        _bg_refresh()
    m['refreshing'] = _REFRESHING
    return jsonify(m), 200


def api_ofd_refresh():
    try:
        return jsonify(dict(refresh(force=bool((request.get_json(silent=True) or {}).get('force'))), **meta())), 200
    except Exception as e:
        app_logger.warning(f"[OFD] Actualisation : {e}")
        return jsonify({"error": "Catalogue Open Filament Database inaccessible (connexion Internet ?)"}), 502


def api_ofd_import_file():
    """Importe un `filaments.json` téléchargé à la main (installation sans accès Internet)."""
    f = request.files.get('file') if request.files else None
    try:
        raw = f.read(MAX_BYTES + 1) if f is not None else (request.get_data() or b'')
        if not raw or len(raw) > MAX_BYTES:
            return jsonify({"error": "Fichier absent ou trop volumineux"}), 400
        rows = parse_catalog(raw)
        if not rows:
            return jsonify({"error": "Aucune bobine reconnue (format Spoolman attendu)"}), 400
        return jsonify(dict({"success": True, "count": store_catalog(rows)}, **meta())), 200
    except (ValueError, TypeError):
        return jsonify({"error": "JSON invalide"}), 400


def api_ofd_search():
    m = meta()
    if m['count'] == 0 or time.time() - m['fetched_at'] > REFRESH_AFTER:
        _bg_refresh()
    items = search(request.args.get('q', ''), request.args.get('material', ''), request.args.get('brand', ''),
                   request.args.get('limit') or 30)
    return jsonify({"items": items, "count": m['count'], "refreshing": _REFRESHING, "attribution": ATTRIBUTION}), 200


def api_ofd_brands():
    ensure_tables()
    conn = get_db()
    try:
        rows = conn.execute("SELECT manufacturer, COUNT(*) AS n FROM ofd_catalog WHERE manufacturer != '' "
                            "GROUP BY manufacturer ORDER BY manufacturer").fetchall()
        mats = conn.execute("SELECT material, COUNT(*) AS n FROM ofd_catalog WHERE material != '' "
                            "GROUP BY material ORDER BY n DESC").fetchall()
    finally:
        conn.close()
    return jsonify({"brands": [dict(r) for r in rows], "materials": [dict(r) for r in mats]}), 200


def api_ofd_add():
    """Crée une bobine manuelle depuis une entrée du catalogue : {ofd_id, remaining_g?, price?, storage_location?}."""
    body = request.get_json(silent=True) or {}
    ensure_tables()
    conn = get_db()
    try:
        r = conn.execute("SELECT * FROM ofd_catalog WHERE id=?", (str(body.get('ofd_id') or ''),)).fetchone()
        if not r:
            return jsonify({"error": "Entrée introuvable dans le catalogue"}), 404
        e = dict(r)
        rem = _f(body.get('remaining_g'))
        s = spool_from_entry(e, rem)
        extra = {}
        if e.get('density'):
            extra['density'] = e['density']
        if e.get('spool_weight') is not None:
            extra['empty_container_weight'] = e['spool_weight']
        price = _f(body.get('price'))
        cur = conn.execute("INSERT INTO manual_filament_spools (user_id, name, material, color_hex, remaining_g, capacity_g, "
                           "source_label, vendor, price, diameter_mm, storage_location, ofd_id, opt_json) "
                           "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                           (session['user_id'], s['name'], s['material'], s['color_hex'], s['remaining_g'], s['capacity_g'],
                            'Open Filament Database', s['vendor'], price, s['diameter_mm'],
                            str(body.get('storage_location') or '').strip()[:80], s['ofd_id'],
                            json.dumps(extra, sort_keys=True) if extra else ''))
        conn.commit()
        return jsonify({"success": True, "id": cur.lastrowid, "spool": s}), 200
    finally:
        conn.close()


_ROUTES = (
    ('/api/ofd/status', ['GET'], 'api_ofd_status', ('login_required', )),
    ('/api/ofd/refresh', ['POST'], 'api_ofd_refresh', ('login_required', )),
    ('/api/ofd/import-file', ['POST'], 'api_ofd_import_file', ('login_required', )),
    ('/api/ofd/search', ['GET'], 'api_ofd_search', ('login_required', )),
    ('/api/ofd/brands', ['GET'], 'api_ofd_brands', ('login_required', )),
    ('/api/ofd/add', ['POST'], 'api_ofd_add', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"open_filament_db.init : services manquants : {missing}")
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
