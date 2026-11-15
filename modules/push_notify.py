"""Stellio — notifications push (ntfy, Telegram, Discord, webhook)

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `push_notify.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import datetime
import re
import requests
import threading
import time

_REQUIRED = (
    '_PUSH_DEFAULT_TYPES',
    '_PUSH_TAGS',
    '_server_t',
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'load_settings',
    'login_required',
    'parse_printer_config',
    'printer_hub',
    'request',
)
_OPTIONAL = ()   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('datetime', 're', 'requests', 'threading', 'time', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
_PUSH_DEFAULT_TYPES = None
_PUSH_TAGS = None
_server_t = None
app = None
app_logger = None
get_db = None
jsonify = None
load_settings = None
login_required = None
parse_printer_config = None
printer_hub = None
request = None


def _push_http_post(url, body, headers=None):
    if not re.match(r'^https?://', url or '', re.I):
        raise ValueError("URL invalide (http/https attendu)")
    r = requests.post(url, json=body, headers=headers or {}, timeout=8)
    if r.status_code >= 300:
        raise RuntimeError(f"HTTP {r.status_code}")

def _push_deliver(cfg, title, message, notif_type='info'):
    provider = (cfg.get('push_provider') or 'ntfy').strip()
    title = str(title or 'Stellio')[:120]
    message = str(message or '')[:900]
    if provider == 'ntfy':
        server = (cfg.get('push_ntfy_server') or 'https://ntfy.sh').strip().rstrip('/')
        topic = (cfg.get('push_ntfy_topic') or '').strip()
        if not topic:
            raise ValueError("Sujet ntfy manquant")
        headers = {}
        if (cfg.get('push_ntfy_token') or '').strip():
            headers['Authorization'] = f"Bearer {cfg['push_ntfy_token'].strip()}"
        body = {"topic": topic, "title": title, "message": message,
                "tags": _PUSH_TAGS.get(notif_type, ['bell']), "priority": 4 if notif_type == 'print_failed' else 3}
        _push_http_post(server, body, headers)
    elif provider == 'telegram':
        token = (cfg.get('push_telegram_token') or '').strip()
        chat = str(cfg.get('push_telegram_chat_id') or '').strip()
        if not token or not chat:
            raise ValueError("Jeton ou identifiant de conversation Telegram manquant")
        _push_http_post(f"https://api.telegram.org/bot{token}/sendMessage", {"chat_id": chat, "text": f"{title}\n{message}"})
    elif provider == 'discord':
        url = (cfg.get('push_discord_url') or '').strip()
        if not url:
            raise ValueError("URL du webhook Discord manquante")
        _push_http_post(url, {"username": "Stellio", "content": f"**{title}**\n{message}"[:1900]})
    elif provider == 'gotify':
        server = (cfg.get('push_gotify_url') or '').strip().rstrip('/')
        token = (cfg.get('push_gotify_token') or '').strip()
        if not server or not token:
            raise ValueError("URL ou jeton Gotify manquant")
        _push_http_post(f"{server}/message", {"title": title, "message": message, "priority": 8 if notif_type in ('print_failed', 'printer_offline') else 5},
                        {"X-Gotify-Key": token})
    elif provider == 'pushover':
        token = (cfg.get('push_pushover_token') or '').strip()
        user = (cfg.get('push_pushover_user') or '').strip()
        if not token or not user:
            raise ValueError("Jeton d'application ou clé utilisateur Pushover manquant")
        _push_http_post("https://api.pushover.net/1/messages.json",
                        {"token": token, "user": user, "title": title, "message": message,
                         "priority": 1 if notif_type in ('print_failed', 'printer_offline') else 0})
    elif provider == 'slack':
        url = (cfg.get('push_slack_url') or '').strip()
        if not url:
            raise ValueError("URL du webhook Slack manquante")
        _push_http_post(url, {"text": f"*{title}*\n{message}"[:3000]})
    elif provider == 'webhook':
        url = (cfg.get('push_webhook_url') or '').strip()
        if not url:
            raise ValueError("URL du webhook manquante")
        _push_http_post(url, {"source": "stellio", "type": notif_type, "title": title, "message": message,
                              "timestamp": datetime.datetime.now().isoformat(timespec='seconds')})
    else:
        raise ValueError("Service inconnu")

def _push_notify_async(notif_type, title, message):
    cfg = load_settings() or {}
    if not cfg.get('push_enabled'):
        return
    types = cfg.get('push_types') if isinstance(cfg.get('push_types'), list) else _PUSH_DEFAULT_TYPES
    if notif_type not in types:
        return

    def _run():
        try:
            _push_deliver(cfg, title, message, notif_type)
        except Exception as e:
            app_logger.warning(f"[Push] Envoi échoué ({type(e).__name__}: {str(e)[:80]})")
    threading.Thread(target=_run, daemon=True).start()

def api_push_test():
    cfg = dict(load_settings() or {})
    for k, v in (request.json or {}).items():
        if str(k).startswith('push_'):
            cfg[k] = v
    try:
        _push_deliver(cfg, _server_t('push.test_title', 'Stellio — test'),
                      _server_t('push.test_message', 'Les notifications push fonctionnent.'), 'info')
        return jsonify({"success": True}), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"Connexion impossible ({type(e).__name__})"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)[:120]}), 200

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
            if cfg.get('push_enabled'):
                _push_watch_once(cfg)
        except Exception as e:
            app_logger.debug(f"[Push] Surveillance imprimantes: {e}")
        time.sleep(20)


_ROUTES = (
    ('/api/push/test', ['POST'], 'api_push_test', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"push_notify.init : services manquants : {missing}")
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
