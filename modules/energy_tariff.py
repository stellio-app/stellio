"""Stellio — tarif d'électricité heures creuses / heures pleines et coût réel (v1.1.3)

Réglages (réglages généraux) : `tariff_enabled`, `tariff_peak_price` (€/kWh heures pleines), `tariff_offpeak_price` (€/kWh heures
creuses), `tariff_offpeak_ranges` (ex. ["22:00-06:00", "12:30-14:30"]), `tariff_weekend_offpeak` (tout le week-end en heures
creuses), `tariff_remind` (rappel quand les heures creuses commencent et que des tâches attendent).
Sans tarif activé, le prix unique `print_cost_elec_price` reste utilisé.

Stellio ne lance jamais une impression tout seul : il calcule le coût réel d'une impression selon l'heure où elle tourne
(la consommation est répartie à la minute entre heures creuses et pleines), indique le gain possible d'un départ aux heures
creuses et envoie au besoin un rappel au début de la plage.

Module séparé de main.py (même schéma que trash_routes.py) : main.py appelle `energy_tariff.init(globals())`.
Les fonctions de calcul (`price_at`, `cost_for_session`, `next_offpeak_start`, `advice`) sont pures et utilisables sans init.
"""
import datetime
import re
import threading
import time

_REQUIRED = (
    '_insert_notification_once',
    '_push_notify_async',
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'load_settings',
    'login_required',
    'request',
    'save_settings',
    'session',
)
_OPTIONAL = ()
_OVERRIDABLE = ('datetime', 'threading', 'time')

_MAIN = {}
_insert_notification_once = None
_push_notify_async = None
app = None
app_logger = None
get_db = None
jsonify = None
load_settings = None
login_required = None
request = None
save_settings = None
session = None

_STARTED = False
LOOP_SECONDS = 60
_RANGE_RE = re.compile(r'^\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$')


def parse_ranges(ranges):
    """['22:00-06:00'] -> [(1320, 360)] (minutes depuis minuit) ; les plages invalides sont ignorées."""
    out = []
    for r in (ranges or []):
        m = _RANGE_RE.match(str(r))
        if not m:
            continue
        a, b = int(m.group(1)) * 60 + int(m.group(2)), int(m.group(3)) * 60 + int(m.group(4))
        if 0 <= a < 1440 and 0 <= b <= 1440 and a != b:
            out.append((a, b))
    return out


def _num(v):
    try:
        f = float(v)
        return f if f >= 0 else None
    except (TypeError, ValueError):
        return None


def get_config(settings):
    s = settings or {}
    flat = _num(s.get('print_cost_elec_price')) or 0.0
    peak = _num(s.get('tariff_peak_price'))
    off = _num(s.get('tariff_offpeak_price'))
    ranges = s.get('tariff_offpeak_ranges')
    if not isinstance(ranges, list):
        ranges = []
    enabled = bool(s.get('tariff_enabled')) and peak is not None and off is not None
    return {'enabled': enabled, 'flat': flat, 'peak': peak if peak is not None else flat, 'offpeak': off if off is not None else flat,
            'ranges': parse_ranges(ranges), 'ranges_raw': [str(r) for r in ranges],
            'weekend': bool(s.get('tariff_weekend_offpeak')), 'remind': bool(s.get('tariff_remind'))}


def is_offpeak(dt, cfg):
    if cfg['weekend'] and dt.weekday() >= 5:
        return True
    m = dt.hour * 60 + dt.minute
    for a, b in cfg['ranges']:
        if a < b:
            if a <= m < b:
                return True
        elif m >= a or m < b:          # plage qui passe minuit
            return True
    return False


def price_at(dt, cfg):
    if not cfg['enabled']:
        return cfg['flat']
    return cfg['offpeak'] if is_offpeak(dt, cfg) else cfg['peak']


def cost_for_session(start_ts, duration_s, kwh, cfg):
    """Coût (€) et part d'énergie en heures creuses (0..1) d'une impression ; la consommation est supposée régulière."""
    if kwh is None or kwh <= 0:
        return 0.0, 0.0
    if not cfg['enabled'] or not duration_s or duration_s <= 0:
        return round(kwh * (cfg['flat'] if not cfg['enabled'] else price_at(datetime.datetime.fromtimestamp(start_ts), cfg)), 4), \
            (1.0 if cfg['enabled'] and is_offpeak(datetime.datetime.fromtimestamp(start_ts), cfg) else 0.0)
    minutes = max(1, int(round(duration_s / 60.0)))
    step = duration_s / minutes
    off = 0
    cost = 0.0
    kwh_step = kwh / minutes
    for i in range(minutes):
        dt = datetime.datetime.fromtimestamp(start_ts + i * step)
        if is_offpeak(dt, cfg):
            off += 1
            cost += kwh_step * cfg['offpeak']
        else:
            cost += kwh_step * cfg['peak']
    return round(cost, 4), round(off / minutes, 3)


def next_offpeak_start(now_ts, cfg, horizon_h=48):
    """Instant (timestamp) du prochain passage en heures creuses (now si on y est déjà) ; None si aucune plage."""
    if not cfg['enabled']:
        return None
    dt = datetime.datetime.fromtimestamp(now_ts).replace(second=0, microsecond=0)
    if is_offpeak(dt, cfg):
        return now_ts
    for _ in range(horizon_h * 60):
        dt += datetime.timedelta(minutes=1)
        if is_offpeak(dt, cfg):
            return dt.timestamp()
    return None


def advice(duration_s, watts, now_ts, cfg):
    """Coût si on lance maintenant, coût si on lance au prochain créneau creux, et gain."""
    kwh = (watts or 0) * (duration_s or 0) / 3600.0 / 1000.0
    now_cost, now_off = cost_for_session(now_ts, duration_s, kwh, cfg)
    out = {'enabled': cfg['enabled'], 'kwh': round(kwh, 3), 'now_cost': now_cost, 'now_offpeak_share': now_off,
           'offpeak_now': cfg['enabled'] and is_offpeak(datetime.datetime.fromtimestamp(now_ts), cfg)}
    nxt = next_offpeak_start(now_ts, cfg)
    if nxt is not None:
        c, share = cost_for_session(nxt, duration_s, kwh, cfg)
        out.update(best_start=nxt, best_cost=c, best_offpeak_share=share, saving=round(max(0.0, now_cost - c), 4),
                   wait_minutes=int(max(0, nxt - now_ts) // 60))
    return out


def api_tariff_get():
    cfg = get_config(load_settings())
    return jsonify({'enabled': cfg['enabled'], 'flat_price': cfg['flat'], 'peak_price': cfg['peak'] if cfg['enabled'] else None,
                    'offpeak_price': cfg['offpeak'] if cfg['enabled'] else None, 'ranges': cfg['ranges_raw'],
                    'weekend': cfg['weekend'], 'remind': cfg['remind'],
                    'offpeak_now': cfg['enabled'] and is_offpeak(datetime.datetime.now(), cfg)})


def api_tariff_set():
    d = request.get_json(silent=True) or {}
    peak, off = _num(d.get('peak_price')), _num(d.get('offpeak_price'))
    ranges = d.get('ranges') if isinstance(d.get('ranges'), list) else []
    ranges = [str(r).strip() for r in ranges]
    if any(not _RANGE_RE.match(r) for r in ranges):
        return jsonify({'error': 'bad_range'}), 400
    if len(parse_ranges(ranges)) != len(ranges):
        return jsonify({'error': 'bad_range'}), 400
    if d.get('enabled') and (peak is None or off is None):
        return jsonify({'error': 'price_required'}), 400
    s = load_settings()
    s['tariff_enabled'] = bool(d.get('enabled'))
    s['tariff_peak_price'] = peak if peak is not None else ''
    s['tariff_offpeak_price'] = off if off is not None else ''
    s['tariff_offpeak_ranges'] = ranges
    s['tariff_weekend_offpeak'] = bool(d.get('weekend'))
    s['tariff_remind'] = bool(d.get('remind'))
    save_settings(s)
    return jsonify({'success': True})


def api_tariff_advice():
    try:
        duration = float(request.args.get('duration_s') or 0)
        watts = float(request.args.get('watts') or 0)
    except ValueError:
        return jsonify({'error': 'bad_value'}), 400
    if duration <= 0 or watts <= 0:
        return jsonify({'error': 'bad_value'}), 400
    return jsonify(advice(duration, watts, time.time(), get_config(load_settings())))


def api_tariff_summary():
    """Bilan des impressions mesurées : énergie, coût réel et gain si tout avait tourné aux heures creuses (30 derniers jours)."""
    cfg = get_config(load_settings())
    since = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
    conn = get_db()
    try:
        try:
            rows = conn.execute("SELECT started_at, duration_s, energy_wh FROM print_energy WHERE user_id = ? AND started_at >= ?",
                                (session.get('user_id'), since)).fetchall()
        except Exception:
            rows = []
    finally:
        conn.close()
    kwh_tot = cost_tot = kwh_off = best = 0.0
    for r in rows:
        try:
            ts = datetime.datetime.strptime(r['started_at'], '%Y-%m-%d %H:%M:%S').timestamp()
        except (TypeError, ValueError):
            continue
        kwh = (r['energy_wh'] or 0) / 1000.0
        c, share = cost_for_session(ts, r['duration_s'] or 0, kwh, cfg)
        kwh_tot += kwh
        cost_tot += c
        kwh_off += kwh * share
        best += kwh * cfg['offpeak'] if cfg['enabled'] else c
    return jsonify({'enabled': cfg['enabled'], 'prints': len(rows), 'kwh': round(kwh_tot, 2), 'cost': round(cost_tot, 2),
                    'offpeak_kwh': round(kwh_off, 2), 'offpeak_share': round(kwh_off / kwh_tot, 3) if kwh_tot else 0,
                    'potential_saving': round(max(0.0, cost_tot - best), 2) if cfg['enabled'] else 0})


def _waiting_jobs():
    """{user_id: nombre de tâches d'impression en file} (table print_jobs, statut « queued »)."""
    conn = get_db()
    try:
        rows = conn.execute("SELECT user_id, COUNT(*) AS n FROM print_jobs WHERE status = 'queued' GROUP BY user_id").fetchall()
        return {r['user_id']: int(r['n']) for r in rows if r['n']}
    except Exception:
        return {}
    finally:
        conn.close()


def check_reminder(now_ts=None, _state={'prev': None}):
    """Au passage heures pleines -> creuses, rappelle les tâches en attente (une seule fois par plage et par utilisateur)."""
    cfg = get_config(load_settings())
    if not (cfg['enabled'] and cfg['remind']):
        _state['prev'] = None
        return False
    now = now_ts or time.time()
    off_now = is_offpeak(datetime.datetime.fromtimestamp(now), cfg)
    prev, _state['prev'] = _state['prev'], off_now
    if not (off_now and prev is False):
        return False
    waiting = _waiting_jobs()
    if not waiting:
        return False
    title = 'Heures creuses'
    stamp = datetime.datetime.fromtimestamp(now).strftime('%Y%m%d%H%M')
    for uid, n in waiting.items():
        msg = f"Les heures creuses commencent : {n} tâche(s) d'impression en attente. Bon moment pour les lancer."
        try:
            _insert_notification_once(uid, 'info', title, msg, 'management', f"tariff:offpeak:{stamp}")
        except Exception as e:
            app_logger.info(f"[Tariff] notification : {e}")
    try:
        _push_notify_async('info', title, f"Les heures creuses commencent : {sum(waiting.values())} tâche(s) en attente.")
    except Exception:
        pass
    return True


def _loop():
    while True:
        try:
            check_reminder()
        except Exception as e:
            app_logger.info(f"[Tariff] rappel : {e}")
        time.sleep(LOOP_SECONDS)


def start_worker():
    global _STARTED
    if _STARTED:
        return
    _STARTED = True
    threading.Thread(target=_loop, daemon=True, name='tariff-reminder').start()


_ROUTES = (
    ('/api/tariff', ['GET'], 'api_tariff_get', ('login_required', )),
    ('/api/tariff', ['POST'], 'api_tariff_set', ('login_required', )),
    ('/api/tariff/advice', ['GET'], 'api_tariff_advice', ('login_required', )),
    ('/api/tariff/summary', ['GET'], 'api_tariff_summary', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"energy_tariff.init : services manquants : {missing}")
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
