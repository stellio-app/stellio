"""Stellio — surveillance des imprimantes : source des évènements d'impression (1.1.7).

Observe l'état des imprimantes et détecte les transitions (impression terminée, échouée, imprimante hors ligne). Ces évènements alimentent
les webhooks et les plugins (`_webhook_emit`) et, si le plugin « Notifications push » est actif, les notifications push (`_push_notify_async`,
passerelle de main.py : sans effet quand le plugin est absent). Reste dans le cœur : sans lui, ni les webhooks ni les plugins ne recevraient
`print.finished` / `print.failed`. Extrait de push_notify.py lors du passage des notifications push en plugin intégré.
"""
import time

_REQUIRED = (
    '_PUSH_DEFAULT_TYPES',
    '_push_notify_async',
    '_push_wanted',
    '_server_t',
    'app_logger',
    'get_db',
    'load_settings',
    'parse_printer_config',
    'printer_hub',
)
_OPTIONAL = ('_webhook_emit', '_webhook_active')
_OVERRIDABLE = ('time', )

_MAIN = {}
_PUSH_DEFAULT_TYPES = None
_push_notify_async = None
_push_wanted = None
_server_t = None
_webhook_emit = None
_webhook_active = None
app_logger = None
get_db = None
load_settings = None
parse_printer_config = None
printer_hub = None


_push_watch_state = {}

def _push_fmt_duration(seconds):
    """3725 -> « 1 h 02 min » ; 540 -> « 9 min » ; 0/inconnu -> chaîne vide."""
    try:
        minutes = int(float(seconds or 0)) // 60
    except (TypeError, ValueError):
        return ''
    if minutes <= 0:
        return ''
    h, m = divmod(minutes, 60)
    return f"{h} h {m:02d} min" if h else f"{m} min"

def _push_job_message(printer_name, job):
    """« Ender 3 — boite.3mf (1 h 24 min) » : machine, fichier et durée quand ils sont connus."""
    parts = [str(printer_name or '')]
    f = str((job or {}).get('file') or '').strip()
    if f:
        parts.append(f)
    msg = ' — '.join(x for x in parts if x)
    d = _push_fmt_duration((job or {}).get('elapsed'))
    return f"{msg} ({d})" if d else msg

_PUSH_OFFLINE_AFTER_SECONDS = 180      # une imprimante injoignable depuis 3 min (après avoir été vue en ligne) = alerte « hors ligne »
_push_seen_online = set()
_push_offline_since = {}

def _push_check_offline(pid, name, online, now, types):
    if online:
        _push_seen_online.add(pid)
        _push_offline_since.pop(pid, None)
        return
    if pid not in _push_seen_online:
        return                             # jamais vue en ligne depuis le démarrage : pas d'alerte (machine éteinte volontairement)
    since = _push_offline_since.setdefault(pid, {'ts': now, 'notified': False})
    if not since['notified'] and now - since['ts'] >= _PUSH_OFFLINE_AFTER_SECONDS:
        since['notified'] = True
        if 'printer_offline' in types:
            _push_notify_async('printer_offline', _server_t('notif.printer_offline_title', 'Imprimante hors ligne'), name)

def _push_watch_once(cfg):
    types = cfg.get('push_types') if isinstance(cfg.get('push_types'), list) else _PUSH_DEFAULT_TYPES
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM printers").fetchall()
    finally:
        conn.close()
    now = time.time()
    for p in rows:
        pid = p['id']
        try:
            status = printer_hub.get_status(parse_printer_config(p)) or {}
        except Exception:
            _push_check_offline(pid, p['name'], False, now, types)
            continue
        st = status.get('status')
        _push_check_offline(pid, p['name'], st not in ('offline', 'timeout', None), now, types)
        prev = _push_watch_state.get(pid)
        if st == 'printing':
            tm = status.get('time') or {}
            _push_watch_state[pid] = {'status': 'printing', 'ts': now, 'file': status.get('file') or '',
                                      'elapsed': tm.get('elapsed') or 0}
        elif st in ('idle', 'error'):
            if prev and prev['status'] == 'printing' and now - prev['ts'] < 600:
                if _webhook_emit:      # v1.1.7 : indépendant des réglages push
                    try:
                        _webhook_emit('print.finished' if st == 'idle' else 'print.failed',
                                      {'printer': {'id': pid, 'name': p['name']}, 'file': prev.get('file') or '',
                                       'duration_s': int(prev.get('elapsed') or 0)}, p['user_id'] if 'user_id' in p.keys() else None)
                    except Exception:
                        pass
                if st == 'idle' and 'print_finished' in types:
                    _push_notify_async('print_finished', _server_t('notif.print_finished_title', 'Impression terminée'), _push_job_message(p['name'], prev))
                elif st == 'error' and 'print_failed' in types:
                    _push_notify_async('print_failed', _server_t('notif.print_failed_title', "Échec d'impression"), _push_job_message(p['name'], prev))
            _push_watch_state[pid] = {'status': st, 'ts': now}
        elif st == 'paused':
            if prev and prev['status'] == 'printing':
                prev['ts'] = now
        elif not prev:
            _push_watch_state[pid] = {'status': st, 'ts': now}

def _push_watcher_loop():
    time.sleep(30)
    while True:
        try:
            cfg = load_settings() or {}
            if _push_wanted() or (_webhook_active and _webhook_active()):
                _push_watch_once(cfg)
        except Exception as e:
            app_logger.debug(f"[Push] Surveillance imprimantes: {e}")
        time.sleep(20)


_ROUTES = ()


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals)."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"print_events.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    return {}
