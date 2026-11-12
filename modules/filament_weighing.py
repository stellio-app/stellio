"""Stellio — pesées de bobines (TigerTag, pesée manuelle) et prévision de rupture de filament

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `filament_weighing.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.

Source principale : le poids restant mesuré par TigerTag (`weight_available`, déjà lu par `_get_tigertag_slots`). Stellio en garde
un historique (une ligne à chaque changement d'au moins 1 g) et en déduit la consommation par jour et la date de rupture.
Une bobine manuelle peut aussi être pesée à la main (poids brut moins la tare) : sa quantité restante est alors mise à jour.
Une hausse de poids entre deux mesures signifie « bobine remplacée » : la prévision repart de ce point.
"""
import datetime
import threading
import time

_REQUIRED = (
    '_get_tigertag_slots',
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'session',
)
_OVERRIDABLE = ('datetime', 'threading', 'time')

_MAIN = {}
_get_tigertag_slots = None
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None

_READY = False
_LOCK = threading.Lock()
_LAST_SYNC = {}
SYNC_MIN_INTERVAL = 600     # secondes entre deux lectures TigerTag pour un même utilisateur
MIN_STEP_G = 1.0            # variation minimale (g) pour enregistrer une nouvelle pesée


def ensure_tables():
    global _READY
    if _READY:
        return
    with _LOCK:
        if _READY:
            return
        conn = get_db()
        try:
            conn.execute("""CREATE TABLE IF NOT EXISTS spool_weighings (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, source_type TEXT NOT NULL,
                source_id TEXT NOT NULL, name TEXT DEFAULT '', remaining_g REAL NOT NULL, capacity_g REAL DEFAULT 1000,
                origin TEXT DEFAULT '', recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_spool_weighings ON spool_weighings (user_id, source_type, source_id, id)")
            conn.commit()
        finally:
            conn.close()
        _READY = True


def _num(v):
    try:
        f = float(str(v).replace(',', '.'))
        return f if f == f and 0 <= f < 100000 else None
    except (TypeError, ValueError):
        return None


def _record(conn, uid, stype, sid, name, remaining, capacity, origin, force=False):
    last = conn.execute("SELECT remaining_g FROM spool_weighings WHERE user_id=? AND source_type=? AND source_id=? "
                        "ORDER BY id DESC LIMIT 1", (uid, stype, str(sid))).fetchone()
    if last is not None and not force and abs(float(last['remaining_g']) - remaining) < MIN_STEP_G:
        return False
    conn.execute("INSERT INTO spool_weighings (user_id, source_type, source_id, name, remaining_g, capacity_g, origin) "
                 "VALUES (?,?,?,?,?,?,?)", (uid, stype, str(sid), str(name)[:120], round(remaining, 1), capacity or 1000, origin))
    return True


def sync_tigertag(uid, force=False):
    """Enregistre le poids restant des bobines TigerTag ; au plus une lecture toutes les 10 minutes (sauf `force`)."""
    ensure_tables()
    now = time.time()
    if not force and now - _LAST_SYNC.get(uid, 0) < SYNC_MIN_INTERVAL:
        return 0
    _LAST_SYNC[uid] = now
    try:
        slots = _get_tigertag_slots(uid) or []
    except Exception as e:
        app_logger.warning(f"[PESEE] Lecture TigerTag impossible : {e}")
        return 0
    n = 0
    conn = get_db()
    try:
        for s in slots:
            rem = _num(s.get('remaining_g'))
            if rem is None:
                continue
            if _record(conn, uid, 'tigertag', s.get('source_id'), s.get('name') or '', rem, _num(s.get('capacity_g')) or 1000, 'tigertag'):
                n += 1
        conn.commit()
    finally:
        conn.close()
    return n


def consumption_rate(points):
    """`points` : liste [(datetime, grammes)] du plus ancien au plus récent.
    Retourne (g/jour, nombre de points utilisés) ou (None, n) si les données ne suffisent pas.
    On remonte depuis la mesure la plus récente tant que le poids décroît ; une hausse = bobine remplacée, on s'arrête."""
    if len(points) < 2:
        return None, len(points)
    seg = [points[-1]]
    for p in reversed(points[:-1]):
        if p[1] < seg[0][1] - 0.01:       # poids plus petit dans le passé : la bobine a été remplacée
            break
        seg.insert(0, p)
    if len(seg) < 2:
        return None, len(seg)
    days = (seg[-1][0] - seg[0][0]).total_seconds() / 86400.0
    used = seg[0][1] - seg[-1][1]
    if days < 0.5 or used <= 0:
        return None, len(seg)
    return used / days, len(seg)


def _parse_ts(s):
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.datetime.strptime(str(s)[:19], fmt)
        except ValueError:
            continue
    return None


def build_forecast(uid, days_window=90):
    ensure_tables()
    since = (datetime.datetime.now() - datetime.timedelta(days=days_window)).strftime('%Y-%m-%d %H:%M:%S')
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM spool_weighings WHERE user_id=? AND recorded_at>=? ORDER BY id", (uid, since)).fetchall()
    finally:
        conn.close()
    groups = {}
    for r in rows:
        groups.setdefault((r['source_type'], r['source_id']), []).append(r)
    out = []
    today = datetime.date.today()
    for (stype, sid), items in groups.items():
        pts = [(_parse_ts(i['recorded_at']), float(i['remaining_g'])) for i in items]
        pts = [p for p in pts if p[0]]
        if not pts:
            continue
        rate, n = consumption_rate(pts)
        last = items[-1]
        remaining = float(last['remaining_g'])
        days_left = round(remaining / rate, 1) if rate else None
        out.append({'source_type': stype, 'source_id': sid, 'name': last['name'], 'remaining_g': round(remaining, 1),
                    'capacity_g': last['capacity_g'], 'last_weighed': last['recorded_at'], 'points': n,
                    'g_per_day': round(rate, 1) if rate else None, 'days_left': days_left,
                    'empty_on': (today + datetime.timedelta(days=int(days_left))).isoformat() if days_left is not None else None,
                    'origin': last['origin']})
    out.sort(key=lambda x: (x['days_left'] is None, x['days_left'] if x['days_left'] is not None else 0))
    return out


# ── Routes ──────────────────────────────────────────────────────────────────────────────────
def api_filament_forecast():
    uid = session['user_id']
    sync_tigertag(uid)
    return jsonify({'spools': build_forecast(uid)})


def api_filament_weigh_sync():
    n = sync_tigertag(session['user_id'], force=True)
    return jsonify({'success': True, 'recorded': n})


def api_filament_weigh():
    """Pesée manuelle d'une bobine du stock manuel : `gross_g` (poids sur la balance) et `tare_g` (bobine vide), ou `remaining_g` direct."""
    ensure_tables()
    data = request.get_json(silent=True) or {}
    uid = session['user_id']
    try:
        sid = int(data.get('source_id'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'source_required'}), 400
    if _num(data.get('remaining_g')) is not None:
        remaining = _num(data.get('remaining_g'))
    else:
        gross = _num(data.get('gross_g'))
        if gross is None:
            return jsonify({'success': False, 'error': 'weight_required'}), 400
        remaining = max(gross - (_num(data.get('tare_g')) or 0.0), 0.0)
    conn = get_db()
    try:
        row = conn.execute("SELECT id, name, capacity_g FROM manual_filament_spools WHERE id=? AND user_id=?", (sid, uid)).fetchone()
        if not row:
            return jsonify({'success': False, 'error': 'not_found'}), 404
        conn.execute("UPDATE manual_filament_spools SET remaining_g=?, updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?",
                     (round(remaining, 1), sid, uid))
        _record(conn, uid, 'manual', sid, row['name'], remaining, row['capacity_g'] or 1000, 'manual', force=True)
        conn.commit()
    finally:
        conn.close()
    return jsonify({'success': True, 'remaining_g': round(remaining, 1)})


def api_filament_weighings():
    ensure_tables()
    stype = str(request.args.get('source_type') or '')[:20]
    sid = str(request.args.get('source_id') or '')[:80]
    conn = get_db()
    try:
        rows = conn.execute("SELECT remaining_g, origin, recorded_at FROM spool_weighings WHERE user_id=? AND source_type=? "
                            "AND source_id=? ORDER BY id DESC LIMIT 200", (session['user_id'], stype, sid)).fetchall()
    finally:
        conn.close()
    return jsonify({'weighings': [dict(r) for r in rows]})


_ROUTES = (
    ('/api/filament/forecast', ['GET'], 'api_filament_forecast', ('login_required', )),
    ('/api/filament/weigh-sync', ['POST'], 'api_filament_weigh_sync', ('login_required', )),
    ('/api/filament/weigh', ['POST'], 'api_filament_weigh', ('login_required', )),
    ('/api/filament/weighings', ['GET'], 'api_filament_weighings', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"filament_weighing.init : services manquants : {missing}")
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
