"""Stellio — alertes d'échec Obico (v1.1.3)

Obico (serveur auto-hébergé ou obico.io) détecte les échecs d'impression par caméra (« spaghetti »). Stellio interroge son API
REST (`GET /api/v1/printers/`), et quand une impression en cours porte une alerte Obico non acquittée et non coupée
(`current_print.alerted_at`), il crée une notification Stellio « échec possible » et l'envoie par les canaux push déjà
configurés (ntfy, Telegram, Discord, webhook…). Si Obico a mis l'impression en pause (`paused_at`) le message le dit.
Chaque alerte n'est annoncée qu'une fois. Stellio ne pilote pas l'imprimante : l'action (pause, annulation) reste celle d'Obico.

Réglages (réglages généraux) : `obico_enabled`, `obico_url` (ex. http://192.168.1.50:3334), `obico_token_enc` (jeton d'API Obico,
chiffré), `obico_interval` (secondes, 20 à 600).

Module séparé de main.py (même schéma que trash_routes.py) : main.py appelle `obico.init(globals())` puis `obico.start_worker()`.
"""
import threading
import time
import urllib.parse

_REQUIRED = (
    '_insert_notification_once',
    '_push_notify_async',
    'app',
    'app_logger',
    'decrypt_password',
    'encrypt_password',
    'get_db',
    'jsonify',
    'load_settings',
    'login_required',
    'request',
    'save_settings',
    'session',
)
_OPTIONAL = ()
_OVERRIDABLE = ('threading', 'time')

_MAIN = {}
_insert_notification_once = None
_push_notify_async = None
app = None
app_logger = None
decrypt_password = None
encrypt_password = None
get_db = None
jsonify = None
load_settings = None
login_required = None
request = None
save_settings = None
session = None

_STARTED = False
_LAST = {'ok': None, 'error': '', 'at': 0, 'printers': []}
DEFAULT_INTERVAL = 30


def clean_url(value):
    """http(s)://hôte[:port] sans chemin final ; '' si invalide."""
    v = str(value or '').strip().rstrip('/')
    if not v:
        return ''
    if '://' not in v:
        v = 'http://' + v
    try:
        p = urllib.parse.urlparse(v)
    except ValueError:
        return ''
    if p.scheme not in ('http', 'https') or not p.hostname or any(c.isspace() for c in v):
        return ''
    return f"{p.scheme}://{p.netloc}{p.path.rstrip('/')}"[:300]


def parse_printers(payload):
    """Réponse Obico (liste ou {results:[…]}) -> liste normalisée de dicts ; les entrées invalides sont ignorées."""
    items = payload.get('results') if isinstance(payload, dict) else payload
    out = []
    for it in (items or []):
        if not isinstance(it, dict):
            continue
        cp = it.get('current_print') if isinstance(it.get('current_print'), dict) else None
        st = it.get('status') if isinstance(it.get('status'), dict) else {}
        alert = None
        if cp and cp.get('alerted_at') and not cp.get('alert_acknowledged_at') and not cp.get('alert_muted_at') \
                and cp.get('alert_overwrite') != 'NOT_FAILED':
            alert = {'at': str(cp.get('alerted_at')), 'paused': bool(cp.get('paused_at')), 'print_id': cp.get('id')}
        out.append({'id': it.get('id'), 'name': str(it.get('name') or f"#{it.get('id')}"),
                    'watching': bool(it.get('watching_enabled', True)), 'state': str(st.get('state', {}).get('text') or '') if isinstance(st.get('state'), dict) else '',
                    'printing': bool(cp), 'filename': str((cp or {}).get('filename') or ''), 'alert': alert,
                    'action_on_failure': str(it.get('action_on_failure') or '')})
    return out


def new_alerts(printers, seen):
    """Alertes pas encore annoncées (clé = printer id + date d'alerte) ; met `seen` à jour."""
    fresh = []
    for p in printers:
        a = p.get('alert')
        if not a:
            continue
        key = f"{p['id']}:{a['at']}"
        if key in seen:
            continue
        seen.add(key)
        fresh.append((key, p, a))
    return fresh



def fetch_printers(url, token, timeout=8):
    """GET /api/v1/printers/ ; essaie « Token » (jeton d'API Obico) puis « Bearer » (OAuth). Lève RuntimeError(code) si échec."""
    import requests
    last = 'unreachable'
    for scheme in ('Token', 'Bearer'):
        try:
            r = requests.get(f"{url}/api/v1/printers/", headers={'Authorization': f'{scheme} {token}', 'Accept': 'application/json'}, timeout=timeout)
        except requests.RequestException:
            raise RuntimeError('unreachable')
        if r.status_code == 200:
            try:
                return parse_printers(r.json())
            except ValueError:
                raise RuntimeError('bad_response')
        last = 'unauthorized' if r.status_code in (401, 403) else f'http_{r.status_code}'
        if r.status_code not in (401, 403):
            break
    raise RuntimeError(last)


def _cfg():
    s = load_settings() or {}
    token = ''
    try:
        token = decrypt_password(s.get('obico_token_enc')) or ''
    except Exception:
        token = ''
    try:
        interval = max(20, min(600, int(s.get('obico_interval') or DEFAULT_INTERVAL)))
    except (TypeError, ValueError):
        interval = DEFAULT_INTERVAL
    return {'enabled': bool(s.get('obico_enabled')), 'url': clean_url(s.get('obico_url')), 'token': token, 'interval': interval}


def _user_ids():
    conn = get_db()
    try:
        return [r['id'] for r in conn.execute("SELECT id FROM users WHERE COALESCE(role,'') != 'viewer'").fetchall()]
    except Exception:
        return []
    finally:
        conn.close()


_SEEN = set()


def poll_once():
    cfg = _cfg()
    if not (cfg['enabled'] and cfg['url'] and cfg['token']):
        return 0
    try:
        printers = fetch_printers(cfg['url'], cfg['token'])
        _LAST.update(ok=True, error='', at=time.time(), printers=printers)
    except RuntimeError as e:
        _LAST.update(ok=False, error=str(e), at=time.time())
        return 0
    n = 0
    for key, p, a in new_alerts(printers, _SEEN):
        title = f"Obico : échec possible sur {p['name']}"
        msg = f"Obico a détecté un problème sur « {p['filename'] or p['name']} »" + (" ; l'impression a été mise en pause." if a['paused'] else ". Vérifiez l'imprimante.")
        for uid in _user_ids():
            try:
                _insert_notification_once(uid, 'print_failed', title, msg, 'printers', f"obico:{key}")
            except Exception as e:
                app_logger.info(f"[Obico] notification : {e}")
        try:
            _push_notify_async('print_failed', title, msg)
        except Exception:
            pass
        n += 1
    return n


def _loop():
    while True:
        try:
            poll_once()
        except Exception as e:
            app_logger.info(f"[Obico] {e}")
        time.sleep(_cfg()['interval'])


def start_worker():
    global _STARTED
    if _STARTED:
        return
    _STARTED = True
    threading.Thread(target=_loop, daemon=True, name='obico-watch').start()


def api_obico_get():
    c = _cfg()
    return jsonify({'enabled': c['enabled'], 'url': c['url'], 'has_token': bool(c['token']), 'interval': c['interval'],
                    'last': {'ok': _LAST['ok'], 'error': _LAST['error'], 'at': _LAST['at'], 'printers': _LAST['printers']}})


def api_obico_set():
    d = request.get_json(silent=True) or {}
    url = clean_url(d.get('url'))
    if d.get('url') and not url:
        return jsonify({'error': 'bad_url'}), 400
    try:
        interval = max(20, min(600, int(d.get('interval') or DEFAULT_INTERVAL)))
    except (TypeError, ValueError):
        return jsonify({'error': 'bad_interval'}), 400
    s = load_settings()
    s['obico_enabled'] = bool(d.get('enabled'))
    s['obico_url'] = url
    s['obico_interval'] = interval
    tok = (d.get('token') or '').strip()
    if d.get('clear_token'):
        s.pop('obico_token_enc', None)
    elif tok:
        s['obico_token_enc'] = encrypt_password(tok)
    if s['obico_enabled'] and not (url and s.get('obico_token_enc')):
        return jsonify({'error': 'url_and_token_required'}), 400
    save_settings(s)
    if s['obico_enabled']:
        start_worker()
    return jsonify({'success': True})


def api_obico_test():
    d = request.get_json(silent=True) or {}
    c = _cfg()
    url = clean_url(d.get('url')) or c['url']
    token = (d.get('token') or '').strip() or c['token']
    if not url or not token:
        return jsonify({'ok': False, 'error': 'url_and_token_required'}), 400
    try:
        printers = fetch_printers(url, token)
    except RuntimeError as e:
        return jsonify({'ok': False, 'error': str(e)})
    return jsonify({'ok': True, 'printers': printers})


def autostart():
    """Démarre la surveillance Obico si elle est activée dans les réglages (appelé par plugin_host)."""
    if _cfg()['enabled']:
        start_worker()


_ROUTES = (
    ('/api/obico', ['GET'], 'api_obico_get', ('login_required', )),
    ('/api/obico', ['POST'], 'api_obico_set', ('login_required', )),
    ('/api/obico/test', ['POST'], 'api_obico_test', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"obico.init : services manquants : {missing}")
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
