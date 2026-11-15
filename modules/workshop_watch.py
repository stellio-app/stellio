"""Stellio — Surveillance atelier : maintenance prédictive, dérive, alertes d'impression

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `workshop_watch.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import datetime
import time

_REQUIRED = (
    '_insert_notification_once',
    '_push_notify_async',
    '_send_native_notification',
    '_server_t',
    'app_logger',
    'get_db',
    'load_settings',
    'parse_printer_config',
    'printer_hub',
)
_OPTIONAL = ()   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('datetime', 'time', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
_insert_notification_once = None
_push_notify_async = None
_send_native_notification = None
_server_t = None
app_logger = None
get_db = None
load_settings = None
parse_printer_config = None
printer_hub = None


def _printer_hours_per_day(conn, pid, window_days=30):
    try:
        since = (datetime.datetime.now() - datetime.timedelta(days=window_days)).strftime('%Y-%m-%d %H:%M:%S')
        r = conn.execute(
            "SELECT COALESCE(SUM(actual_seconds),0) AS s, MIN(sent_at) AS first FROM print_history "
            "WHERE printer_id=? AND actual_seconds>0 AND sent_at>=?", (pid, since)).fetchone()
        if not r or not r['s']:
            return None
        span = window_days
        try:
            first = datetime.datetime.fromisoformat(str(r['first']).replace('Z', ''))
            span = min(window_days, max(7.0, (datetime.datetime.now() - first).total_seconds() / 86400))
        except Exception:
            pass
        return (r['s'] / 3600.0) / span
    except Exception:
        return None

def _maintenance_eta(task, total_hours, rate):
    """Jours restants avant échéance (None si inconnu) : min entre l'échéance en heures (au rythme réel) et celle en jours."""
    etas = []
    if task['interval_hours']:
        left_h = task['interval_hours'] - (total_hours - (task['hours_at_last_reset'] or 0))
        if left_h <= 0:
            etas.append(0.0)
        elif rate and rate > 0.05:
            etas.append(left_h / rate)
    if task['interval_days']:
        try:
            last = datetime.datetime.fromisoformat(task['last_reset_at'])
            etas.append(max(0.0, task['interval_days'] - (datetime.datetime.now() - last).total_seconds() / 86400))
        except Exception:
            pass
    return round(min(etas), 1) if etas else None

_ws_state = {}

_WS_DRIFT_DELTA_C = 15.0

_WS_DRIFT_SECONDS = 120

_WS_STALL_SECONDS = 15 * 60

def _ws_alert(user_id, ntype, title, message, key, link='printers'):
    if _insert_notification_once(user_id, ntype, title, message, link, key):
        _send_native_notification(title, message)
        _push_notify_async(ntype, title, message)

def _ws_job_progress(p, st, status, hours=0.0):
    """Option « avancement auto » : une impression terminée compte pour 1 pièce de la plus ancienne commande ouverte de l'imprimante."""
    conn = get_db()
    try:
        job = conn.execute(
            "SELECT * FROM print_jobs WHERE user_id=? AND printer_id=? AND status IN ('queued','printing') "
            "ORDER BY CASE WHEN due_date='' THEN 1 ELSE 0 END, due_date, id LIMIT 1", (p['user_id'], p['id'])).fetchone()
        if not job:
            return
        if st == 'start':
            if job['status'] == 'queued':
                conn.execute("UPDATE print_jobs SET status='printing' WHERE id=?", (job['id'],))
        elif st == 'finish':
            done = min(job['qty_done'] + 1, job['quantity'])
            fin = done >= job['quantity']
            conn.execute("UPDATE print_jobs SET qty_done=?, status=?, done_at=?, actual_hours=COALESCE(actual_hours,0)+? WHERE id=?",
                         (done, 'done' if fin else 'printing', datetime.date.today().isoformat() if fin else '', max(0.0, hours), job['id']))
        conn.commit()
    finally:
        conn.close()

def _workshop_watch_once():
    cfg = load_settings() or {}
    try:
        min_g = float(cfg.get('alert_spool_min_g', 80) or 0)
    except (TypeError, ValueError):
        min_g = 80.0
    drift_on = cfg.get('alert_drift_enabled', True) not in (False, 0, '0', 'false')
    auto_prog = cfg.get('workshop_auto_progress') in (True, 1, '1', 'true')
    conn = get_db()
    try:
        printers = conn.execute("SELECT * FROM printers").fetchall()
    finally:
        conn.close()
    now = time.time()
    today = datetime.date.today().isoformat()
    for p in printers:
        pid, uid, name = p['id'], p['user_id'], p['name']
        try:
            status = printer_hub.get_status(parse_printer_config(p)) or {}
        except Exception:
            continue
        st = status.get('status')
        stt = _ws_state.setdefault(pid, {'status': None, 'start': None, 'heat': None, 'prog': None, 'prog_ts': now, 'low': set()})
        stt['drift'] = False
        if st in ('error', 'offline', 'timeout', None):
            stt['status'] = st
            continue

        # bobine presque vide (AMS / Spoolman)
        if min_g > 0:
            for tray in status.get('ams') or []:
                rem = tray.get('remaining_g')
                if rem is None or not tray.get('material'):
                    continue
                tid = str(tray.get('id', ''))
                if rem < min_g:
                    if (tid) not in stt['low']:
                        stt['low'].add(tid)
                        _ws_alert(uid, 'spool_low',
                                  _server_t('notif.spool_low_title', 'Bobine presque vide'),
                                  f"{name} — {tray.get('material')} ({tid}) : {int(rem)} g",
                                  f"spool_low_{pid}_{tid}_{today}")
                elif rem > min_g * 1.5:
                    stt['low'].discard(tid)

        # démarrage / fin d'impression (avancement auto des commandes)
        if st == 'printing' and stt['status'] != 'printing':
            stt['start'] = now
            stt['prog'], stt['prog_ts'], stt['heat'] = None, now, None
            if auto_prog:
                _ws_job_progress(p, 'start', status)
        elif st == 'idle' and stt['status'] == 'printing':
            if auto_prog and stt.get('start') and now - stt['start'] > 120:
                _ws_job_progress(p, 'finish', status, (now - stt['start']) / 3600.0)
        stt['status'] = st

        # dérive : température hors consigne, avancement bloqué
        if st == 'printing' and drift_on:
            start = int(stt.get('start') or now)
            try:
                progress = float(status.get('progress') or 0)
            except (TypeError, ValueError):
                progress = 0.0
            temps = status.get('temps') or {}
            ext = temps.get('extruder') or {}
            bed = temps.get('bed') or {}
            off = False
            if progress >= 3:
                for t_, lim in ((ext, _WS_DRIFT_DELTA_C), (bed, _WS_DRIFT_DELTA_C)):
                    try:
                        tg, cu = float(t_.get('target') or 0), float(t_.get('current') or 0)
                    except (TypeError, ValueError):
                        continue
                    if tg > 0 and abs(cu - tg) > lim:
                        off = True
            if off:
                stt['heat'] = stt['heat'] or now
                if now - stt['heat'] >= _WS_DRIFT_SECONDS:
                    stt['drift'] = True
                    _ws_alert(uid, 'print_drift', _server_t('notif.drift_temp_title', 'Dérive de température'),
                              f"{name} — {int(ext.get('current') or 0)}/{int(ext.get('target') or 0)} °C",
                              f"print_drift_temp_{pid}_{start}")
            else:
                stt['heat'] = None
            if progress != stt['prog']:
                stt['prog'], stt['prog_ts'] = progress, now
            elif 0 < progress < 100 and now - stt['prog_ts'] >= _WS_STALL_SECONDS:
                stt['drift'] = True
                _ws_alert(uid, 'print_drift', _server_t('notif.drift_stall_title', 'Impression bloquée ?'),
                          f"{name} — {int(progress)} %", f"print_drift_stall_{pid}_{start}")

    _workshop_maintenance_check()

def _workshop_maintenance_check():
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT t.*, p.name AS pname, p.total_print_hours AS total FROM printer_maintenance_tasks t
               JOIN printers p ON p.id = t.printer_id""").fetchall()
        rates = {}
        for t in rows:
            if t['printer_id'] not in rates:
                rates[t['printer_id']] = _printer_hours_per_day(conn, t['printer_id'])
    finally:
        conn.close()
    for t in rows:
        eta = _maintenance_eta(t, t['total'] or 0, rates.get(t['printer_id']))
        if eta is None:
            continue
        mark = str(t['last_reset_at'] or '')[:19]
        if eta <= 0:
            _ws_alert(t['user_id'], 'maintenance', _server_t('notif.maintenance_title', 'Maintenance à prévoir'),
                      f"{t['pname']} — {t['name']}", f"maintenance_due_{t['id']}_{mark}")
        elif eta <= 3:
            _ws_alert(t['user_id'], 'maintenance', _server_t('notif.maintenance_soon_title', 'Maintenance bientôt due'),
                      f"{t['pname']} — {t['name']} (~{max(1, round(eta))} j)", f"maintenance_soon_{t['id']}_{mark}")

def _workshop_watch_loop():
    time.sleep(45)
    while True:
        try:
            _workshop_watch_once()
        except Exception as e:
            app_logger.debug(f"[Atelier] Surveillance: {e}")
        time.sleep(30)


_ROUTES = (
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"workshop_watch.init : services manquants : {missing}")
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
