"""Stellio — webhooks sortants (v1.1.7) : impression terminée / échouée, commande en retard, imprimante surchargée.

Principes
  · Chaque webhook = une URL, une liste d'évènements et un secret (`whsec_…`, affiché à la création puis seulement sur demande de
    rotation). Chaque envoi est signé en HMAC-SHA256 : en-tête `X-Stellio-Signature: t=<horodatage>,v1=<hex>` calculé sur
    `<horodatage>.<corps JSON>` — le destinataire vérifie la signature et la fraîcheur (protection contre le rejeu).
  · Les envois passent par une file en base (`webhook_deliveries`) : si le destinataire ne répond pas 2xx, nouvelle tentative avec
    un délai croissant (30 s, 2 min, 10 min, 1 h, 6 h ; 6 essais au total). Un envoi encore en attente après 24 h est abandonné
    (PC éteint pendant la nuit : on n'envoie pas « impression terminée » avec un jour de retard).
  · Journal des envois (statut, code HTTP, erreur, nombre d'essais), bouton « tester », renvoi manuel.
  · Pas de redirection suivie, pas de page de configuration externe, pas de système de plugins : une URL et un secret.

Module séparé de main.py (même schéma que public_api.py) : main.py appelle `webhooks.init(globals())`. Les autres modules déclenchent
un évènement par `_webhook_emit(evenement, données, user_id)` (fourni par main.py). Les fonctions pures (`sign`, `signature_header`,
`verify_signature`, `retry_delay`, `validate_url`, `build_envelope`, `normalize_events`) sont testées sans base ni réseau.
"""
import os
import hashlib
import hmac
import json
import re
import secrets
import threading
import time
from urllib.parse import urlsplit

_REQUIRED = (
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'send_file',
    'session',
)
_OPTIONAL = ('CURRENT_VERSION',)
_OVERRIDABLE = ('hashlib', 'hmac', 'json', 'secrets', 'time')

_MAIN = {}
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
send_file = None
session = None
CURRENT_VERSION = ''

EVENTS = ('print.finished', 'print.failed', 'order.late', 'printer.overload')
TEST_EVENT = 'webhook.test'
MAX_WEBHOOKS = 10
MAX_ATTEMPTS = 6
RETRY_DELAYS = (30, 120, 600, 3600, 21600)      # après l'essai n° 1, 2, 3, 4, 5
EXPIRE_AFTER_S = 24 * 3600
TIMEOUT_S = 10
TOLERANCE_S = 300
KEEP_DELIVERIES = 500                           # par compte
SECRET_PREFIX = 'whsec_'
_wake = threading.Event()
_post = None                                    # remplaçable dans les tests : _post(url, body_bytes, headers, timeout) -> code HTTP


# ── fonctions pures ───────────────────────────────────────────────────────

def make_secret():
    return SECRET_PREFIX + secrets.token_hex(24)


def sign(secret, ts, body):
    """HMAC-SHA256 hexadécimal de « <ts>.<corps> »."""
    if isinstance(body, str):
        body = body.encode('utf-8')
    return hmac.new(str(secret).encode('utf-8'), f"{int(ts)}.".encode('utf-8') + body, hashlib.sha256).hexdigest()


def signature_header(secret, ts, body):
    return f"t={int(ts)},v1={sign(secret, ts, body)}"


def verify_signature(secret, header, body, tolerance=TOLERANCE_S, now=None):
    """Vérifie l'en-tête reçu : signature exacte (comparaison à temps constant) et horodatage assez récent."""
    m = re.fullmatch(r"t=(\d+),v1=([0-9a-f]{64})", str(header or '').strip())
    if not m:
        return False
    ts, sig = int(m.group(1)), m.group(2)
    if abs((now if now is not None else time.time()) - ts) > tolerance:
        return False
    return hmac.compare_digest(sig, sign(secret, ts, body))


def retry_delay(attempts_done):
    """Délai avant la prochaine tentative après `attempts_done` échecs ; None = on abandonne."""
    if attempts_done >= MAX_ATTEMPTS:
        return None
    return RETRY_DELAYS[min(attempts_done, len(RETRY_DELAYS)) - 1] if attempts_done >= 1 else 0


def validate_url(url):
    """(ok, message). http/https uniquement, pas d'identifiants dans l'URL, pas l'adresse de métadonnées du cloud (link-local).
    Les adresses du réseau local restent permises : on envoie volontairement vers Home Assistant, Node-RED, etc."""
    u = str(url or '').strip()
    if not u or len(u) > 500:
        return False, 'URL absente ou trop longue.'
    try:
        p = urlsplit(u)
    except ValueError:
        return False, 'URL invalide.'
    if p.scheme not in ('http', 'https') or not p.hostname:
        return False, 'URL invalide (http ou https attendu).'
    if p.username or p.password:
        return False, "Pas d'identifiants dans l'URL."
    if p.hostname.startswith('169.254.') or p.hostname.lower() in ('metadata.google.internal',):
        return False, 'Adresse non autorisée.'
    return True, ''


def normalize_events(events):
    """Liste filtrée sur les évènements connus, sans doublon, ordre stable."""
    if isinstance(events, str):
        events = [e.strip() for e in events.split(',')]
    seen = []
    for e in events or []:
        if e in EVENTS and e not in seen:
            seen.append(e)
    return [e for e in EVENTS if e in seen]


def build_envelope(event, data, delivery_id, now=None):
    return {'id': delivery_id, 'event': event, 'created': int(now if now is not None else time.time()),
            'source': 'stellio', 'version': CURRENT_VERSION or '', 'data': data or {}}


# ── base ──────────────────────────────────────────────────────────────────

def _ensure_tables(conn=None):
    own = conn is None
    conn = conn or get_db()
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS webhooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT NOT NULL, url TEXT NOT NULL, secret TEXT NOT NULL,
            events TEXT NOT NULL DEFAULT '', active INTEGER NOT NULL DEFAULT 1, created_at REAL,
            last_status INTEGER, last_at REAL, fail_count INTEGER NOT NULL DEFAULT 0)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS webhook_deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT, webhook_id INTEGER NOT NULL, user_id INTEGER NOT NULL, event TEXT NOT NULL,
            payload TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0, next_try_at REAL,
            response_code INTEGER, error TEXT, created_at REAL, delivered_at REAL)""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_whd_due ON webhook_deliveries(status, next_try_at)")
        conn.commit()
    finally:
        if own:
            conn.close()


def has_active(user_id=None):
    """Y a-t-il au moins un webhook actif ? (sert à la surveillance des impressions, même si les notifications push sont coupées)"""
    try:
        conn = get_db()
        try:
            _ensure_tables(conn)
            if user_id is None:
                return conn.execute("SELECT 1 FROM webhooks WHERE active = 1 LIMIT 1").fetchone() is not None
            return conn.execute("SELECT 1 FROM webhooks WHERE active = 1 AND user_id = ? LIMIT 1", (user_id,)).fetchone() is not None
        finally:
            conn.close()
    except Exception:
        return False


def emit(event, data=None, user_id=None):
    """Met un évènement en file pour chaque webhook actif abonné (du compte `user_id`, ou de tous si None). Retourne le nombre d'envois créés."""
    if event not in EVENTS:
        return 0
    n = 0
    conn = get_db()
    try:
        _ensure_tables(conn)
        sql, args = "SELECT * FROM webhooks WHERE active = 1", []
        if user_id is not None:
            sql += " AND user_id = ?"
            args.append(user_id)
        now = time.time()
        for w in conn.execute(sql, args).fetchall():
            if event not in normalize_events(w['events']):
                continue
            cur = conn.execute("INSERT INTO webhook_deliveries (webhook_id, user_id, event, payload, status, attempts, next_try_at, created_at) "
                               "VALUES (?,?,?,?,?,?,?,?)", (w['id'], w['user_id'], event, '', 'pending', 0, now, now))
            env = build_envelope(event, data, cur.lastrowid, now)
            conn.execute("UPDATE webhook_deliveries SET payload = ? WHERE id = ?", (json.dumps(env, ensure_ascii=False, separators=(',', ':')), cur.lastrowid))
            conn.execute("DELETE FROM webhook_deliveries WHERE user_id = ? AND id <= (SELECT MAX(id) FROM webhook_deliveries WHERE user_id = ?) - ?",
                         (w['user_id'], w['user_id'], KEEP_DELIVERIES))
            n += 1
        conn.commit()
    finally:
        conn.close()
    if n:
        _wake.set()
    return n


def _do_post(url, body, headers):
    if _post is not None:
        return _post(url, body, headers, TIMEOUT_S)
    import requests
    return requests.post(url, data=body, headers=headers, timeout=TIMEOUT_S, allow_redirects=False).status_code


def deliver(conn, d, now=None):
    """Tente un envoi ; met à jour la ligne (ok / nouvelle tentative / abandon). Retourne la ligne à jour."""
    now = now if now is not None else time.time()
    w = conn.execute("SELECT * FROM webhooks WHERE id = ?", (d['webhook_id'],)).fetchone()
    code, err = None, ''
    if not w:
        err = 'webhook supprimé'
        conn.execute("UPDATE webhook_deliveries SET status='failed', error=? WHERE id=?", (err, d['id']))
        conn.commit()
        return conn.execute("SELECT * FROM webhook_deliveries WHERE id = ?", (d['id'],)).fetchone()
    body = d['payload'].encode('utf-8')
    headers = {'Content-Type': 'application/json', 'User-Agent': f"Stellio/{CURRENT_VERSION or '1'}",
               'X-Stellio-Event': d['event'], 'X-Stellio-Delivery': str(d['id']),
               'X-Stellio-Signature': signature_header(w['secret'], now, body)}
    ok_url, msg = validate_url(w['url'])
    if not ok_url:
        err = msg
    else:
        try:
            code = int(_do_post(w['url'], body, headers))
            if not 200 <= code < 300:
                err = f"HTTP {code}"
        except Exception as e:
            err = f"{type(e).__name__}: {str(e)[:60]}"
    attempts = d['attempts'] + 1
    if not err:
        conn.execute("UPDATE webhook_deliveries SET status='ok', attempts=?, response_code=?, error='', delivered_at=?, next_try_at=NULL WHERE id=?",
                     (attempts, code, now, d['id']))
        conn.execute("UPDATE webhooks SET last_status=?, last_at=?, fail_count=0 WHERE id=?", (code, now, w['id']))
    else:
        delay = retry_delay(attempts)
        if not ok_url:
            delay = None                       # une URL invalide ne se corrige pas en réessayant
        if delay is None:
            conn.execute("UPDATE webhook_deliveries SET status='failed', attempts=?, response_code=?, error=?, next_try_at=NULL WHERE id=?",
                         (attempts, code, err, d['id']))
        else:
            conn.execute("UPDATE webhook_deliveries SET status='pending', attempts=?, response_code=?, error=?, next_try_at=? WHERE id=?",
                         (attempts, code, err, now + delay, d['id']))
        conn.execute("UPDATE webhooks SET last_status=?, last_at=?, fail_count=fail_count+1 WHERE id=?", (code or 0, now, w['id']))
    conn.commit()
    return conn.execute("SELECT * FROM webhook_deliveries WHERE id = ?", (d['id'],)).fetchone()


def process_due(now=None, limit=20):
    """Envoie ce qui est dû ; abandonne ce qui attend depuis plus de 24 h. Retourne le nombre d'envois tentés."""
    now = now if now is not None else time.time()
    conn = get_db()
    try:
        _ensure_tables(conn)
        conn.execute("UPDATE webhook_deliveries SET status='failed', error='expiré (non envoyé en 24 h)', next_try_at=NULL "
                     "WHERE status='pending' AND created_at < ?", (now - EXPIRE_AFTER_S,))
        conn.commit()
        rows = conn.execute("SELECT * FROM webhook_deliveries WHERE status='pending' AND next_try_at <= ? ORDER BY id LIMIT ?", (now, limit)).fetchall()
        for d in rows:
            deliver(conn, d, now)
        return len(rows)
    finally:
        conn.close()


def _loop():
    while True:
        try:
            process_due()
        except Exception as e:
            try:
                app_logger.debug(f"[WEBHOOKS] boucle : {e}")
            except Exception:
                pass
        _wake.wait(5)
        _wake.clear()


def start_worker():
    threading.Thread(target=_loop, daemon=True, name='stellio-webhooks').start()


autostart = start_worker      # appelé par plugin_host


def ui_webhooks_script():
    """Script de la section Webhooks des réglages : fourni par le plugin."""
    return send_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webhooks.js'), mimetype='application/javascript')


# ── gestion (session de l'interface) ───────────────────────────────────────

def _no_viewer():
    if session.get('role') == 'viewer' and not _demo_ok():
        return jsonify({'error': 'Réservé au compte propriétaire.'}), 403
    return None


def _public(w):
    return {'id': w['id'], 'name': w['name'], 'url': w['url'], 'events': normalize_events(w['events']), 'active': bool(w['active']),
            'created_at': w['created_at'], 'last_status': w['last_status'], 'last_at': w['last_at'], 'fail_count': w['fail_count']}


def _mine(conn, wid):
    return conn.execute("SELECT * FROM webhooks WHERE id = ? AND user_id = ?", (wid, session['user_id'])).fetchone()


def api_webhooks_list():
    r = _no_viewer()
    if r:
        return r
    conn = get_db()
    try:
        _ensure_tables(conn)
        rows = conn.execute("SELECT * FROM webhooks WHERE user_id = ? ORDER BY id DESC", (session['user_id'],)).fetchall()
        return jsonify({'webhooks': [_public(w) for w in rows], 'events': list(EVENTS), 'max': MAX_WEBHOOKS})
    finally:
        conn.close()


def _read_body(d, partial=False):
    out, err = {}, None
    if 'name' in d or not partial:
        out['name'] = str(d.get('name') or '').strip()[:60]
        if not out['name']:
            err = 'Donnez un nom au webhook.'
    if 'url' in d or not partial:
        out['url'] = str(d.get('url') or '').strip()
        ok, msg = validate_url(out['url'])
        if not ok:
            err = msg
    if 'events' in d or not partial:
        out['events'] = normalize_events(d.get('events'))
        if not out['events']:
            err = 'Choisissez au moins un évènement.'
    if 'active' in d:
        out['active'] = 1 if d.get('active') else 0
    return out, err


def api_webhooks_create():
    r = _no_viewer()
    if r:
        return r
    d = request.get_json(silent=True) or {}
    out, err = _read_body(d)
    if err:
        return jsonify({'error': err}), 400
    conn = get_db()
    try:
        _ensure_tables(conn)
        if conn.execute("SELECT COUNT(*) FROM webhooks WHERE user_id = ?", (session['user_id'],)).fetchone()[0] >= MAX_WEBHOOKS:
            return jsonify({'error': f'{MAX_WEBHOOKS} webhooks au maximum.'}), 400
        sec = make_secret()
        cur = conn.execute("INSERT INTO webhooks (user_id, name, url, secret, events, active, created_at) VALUES (?,?,?,?,?,?,?)",
                           (session['user_id'], out['name'], out['url'], sec, ','.join(out['events']), out.get('active', 1), time.time()))
        conn.commit()
        res = _public(_mine(conn, cur.lastrowid))
        res['secret'] = sec                    # seule fois où il est visible (avec la rotation)
        return jsonify(res)
    finally:
        conn.close()


def api_webhooks_update(wid):
    r = _no_viewer()
    if r:
        return r
    d = request.get_json(silent=True) or {}
    out, err = _read_body(d, partial=True)
    if err:
        return jsonify({'error': err}), 400
    if not out:
        return jsonify({'error': 'Rien à modifier.'}), 400
    if 'events' in out:
        out['events'] = ','.join(out['events'])
    conn = get_db()
    try:
        _ensure_tables(conn)
        if not _mine(conn, wid):
            return jsonify({'error': 'Webhook introuvable.'}), 404
        conn.execute("UPDATE webhooks SET " + ', '.join(f"{k} = ?" for k in out) + " WHERE id = ?", list(out.values()) + [wid])
        conn.commit()
        return jsonify(_public(_mine(conn, wid)))
    finally:
        conn.close()


def api_webhooks_delete(wid):
    r = _no_viewer()
    if r:
        return r
    conn = get_db()
    try:
        _ensure_tables(conn)
        if not _mine(conn, wid):
            return jsonify({'error': 'Webhook introuvable.'}), 404
        conn.execute("DELETE FROM webhook_deliveries WHERE webhook_id = ?", (wid,))
        conn.execute("DELETE FROM webhooks WHERE id = ?", (wid,))
        conn.commit()
        return jsonify({'ok': True})
    finally:
        conn.close()


def api_webhooks_rotate(wid):
    r = _no_viewer()
    if r:
        return r
    conn = get_db()
    try:
        _ensure_tables(conn)
        if not _mine(conn, wid):
            return jsonify({'error': 'Webhook introuvable.'}), 404
        sec = make_secret()
        conn.execute("UPDATE webhooks SET secret = ? WHERE id = ?", (sec, wid))
        conn.commit()
        return jsonify({'id': wid, 'secret': sec})
    finally:
        conn.close()


def api_webhooks_test(wid):
    """Envoie tout de suite un évènement « webhook.test » et renvoie le résultat (statut, code HTTP, erreur)."""
    r = _no_viewer()
    if r:
        return r
    conn = get_db()
    try:
        _ensure_tables(conn)
        w = _mine(conn, wid)
        if not w:
            return jsonify({'error': 'Webhook introuvable.'}), 404
        now = time.time()
        cur = conn.execute("INSERT INTO webhook_deliveries (webhook_id, user_id, event, payload, status, attempts, next_try_at, created_at) VALUES (?,?,?,?,?,?,?,?)",
                           (wid, w['user_id'], TEST_EVENT, '', 'pending', 0, now, now))
        env = build_envelope(TEST_EVENT, {'message': 'Test de webhook Stellio', 'webhook': w['name']}, cur.lastrowid, now)
        conn.execute("UPDATE webhook_deliveries SET payload = ? WHERE id = ?", (json.dumps(env, ensure_ascii=False, separators=(',', ':')), cur.lastrowid))
        conn.commit()
        d = deliver(conn, conn.execute("SELECT * FROM webhook_deliveries WHERE id = ?", (cur.lastrowid,)).fetchone(), now)
        if d['status'] == 'pending':           # un test n'est pas relancé en fond : le résultat s'affiche, point
            conn.execute("UPDATE webhook_deliveries SET status='failed', next_try_at=NULL WHERE id=?", (d['id'],))
            conn.commit()
            d = conn.execute("SELECT * FROM webhook_deliveries WHERE id = ?", (d['id'],)).fetchone()
        return jsonify({'ok': d['status'] == 'ok', 'status': d['status'], 'code': d['response_code'], 'error': d['error'] or ''})
    finally:
        conn.close()


def api_webhooks_log():
    r = _no_viewer()
    if r:
        return r
    try:
        limit = max(1, min(int(request.args.get('limit', 60)), 300))
    except ValueError:
        limit = 60
    q = ("SELECT d.id, d.webhook_id, w.name AS webhook_name, d.event, d.status, d.attempts, d.next_try_at, d.response_code, d.error, d.created_at, d.delivered_at "
         "FROM webhook_deliveries d LEFT JOIN webhooks w ON w.id = d.webhook_id WHERE d.user_id = ?")
    args = [session['user_id']]
    wid = request.args.get('webhook_id')
    if wid and wid.isdigit():
        q += " AND d.webhook_id = ?"
        args.append(int(wid))
    if request.args.get('errors') in ('1', 'true'):
        q += " AND d.status != 'ok'"
    conn = get_db()
    try:
        _ensure_tables(conn)
        return jsonify({'log': [dict(x) for x in conn.execute(q + " ORDER BY d.id DESC LIMIT ?", args + [limit]).fetchall()]})
    finally:
        conn.close()


def api_webhooks_retry(did):
    r = _no_viewer()
    if r:
        return r
    conn = get_db()
    try:
        _ensure_tables(conn)
        d = conn.execute("SELECT * FROM webhook_deliveries WHERE id = ? AND user_id = ?", (did, session['user_id'])).fetchone()
        if not d:
            return jsonify({'error': 'Envoi introuvable.'}), 404
        if d['status'] == 'ok':
            return jsonify({'error': 'Cet envoi a déjà réussi.'}), 400
        now = time.time()
        conn.execute("UPDATE webhook_deliveries SET status='pending', attempts=0, next_try_at=?, created_at=?, error='' WHERE id=?", (now, now, did))
        conn.commit()
    finally:
        conn.close()
    _wake.set()
    return jsonify({'ok': True})


_DEMO_COMPUTE = ('/api/plate/arrange', '/api/organize/preview', '/api/model-diff')


def _demo_ok():
    """Démo publique (lecture seule, `IS_DEMO` posé par la surcouche de démo) : consultation (GET) et calculs sans écriture."""
    try:
        return bool(_MAIN.get('IS_DEMO')) and (request.method in ('GET', 'HEAD') or request.path in _DEMO_COMPUTE)
    except Exception:
        return False


_ROUTES = (
    ('/webhooks.js', ['GET'], 'ui_webhooks_script', ()),
    ('/api/webhooks', ['GET'], 'api_webhooks_list', ('login_required', )),
    ('/api/webhooks', ['POST'], 'api_webhooks_create', ('login_required', )),
    ('/api/webhooks/<int:wid>', ['PUT'], 'api_webhooks_update', ('login_required', )),
    ('/api/webhooks/<int:wid>', ['DELETE'], 'api_webhooks_delete', ('login_required', )),
    ('/api/webhooks/<int:wid>/rotate-secret', ['POST'], 'api_webhooks_rotate', ('login_required', )),
    ('/api/webhooks/<int:wid>/test', ['POST'], 'api_webhooks_test', ('login_required', )),
    ('/api/webhooks/deliveries', ['GET'], 'api_webhooks_log', ('login_required', )),
    ('/api/webhooks/deliveries/<int:did>/retry', ['POST'], 'api_webhooks_retry', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"webhooks.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if routes:
        try:
            _ensure_tables()
        except Exception as e:
            try:
                app_logger.warning(f"[WEBHOOKS] Tables non préparées : {e}")
            except Exception:
                pass
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {}
