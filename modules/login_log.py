"""Stellio — journal des connexions (1.1.6) : qui s'est connecté, quand, depuis quelle adresse, et les tentatives échouées.

Table `auth_log` créée à la demande. Chaque événement est rattaché au compte propriétaire (un invité qui se connecte apparaît
dans le journal de son propriétaire, sous son propre nom). Les échecs sur un nom inconnu sont gardés sans propriétaire : ils ne sont
affichés à personne (pas de fuite d'information) mais comptent pour le diagnostic. Conservation : 500 lignes par propriétaire.
Aucune donnée sensible : ni mot de passe ni jeton ; l'agent navigateur est tronqué.
"""
import time

_REQUIRED = (
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'session',
)
_OPTIONAL = ()
_OVERRIDABLE = ('time',)

_MAIN = {}
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None

EVENTS = ('login_ok', 'login_fail', 'logout')
KEEP_PER_OWNER = 500
DEFAULT_LIMIT = 100
MAX_LIMIT = 200


def ensure(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS auth_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL NOT NULL,
        owner_id INTEGER,
        username TEXT,
        event TEXT NOT NULL,
        ip TEXT,
        agent TEXT)""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_log_owner_ts ON auth_log(owner_id, ts DESC)")


def client_ip(headers, remote_addr):
    """Adresse du client : en-têtes du tunnel Cloudflare / proxy si présents, sinon l'adresse de la connexion."""
    for h in ('CF-Connecting-IP', 'X-Forwarded-For'):
        v = (headers.get(h) or '').split(',')[0].strip()
        if v:
            return v[:64]
    return (remote_addr or '').replace('::ffff:', '')[:64]


def record(conn, event, username, owner_id, ip, agent, now=None):
    """Ajoute un événement ; ne lève jamais (le journal ne doit pas empêcher de se connecter)."""
    if event not in EVENTS:
        return False
    try:
        ensure(conn)
        conn.execute("INSERT INTO auth_log (ts, owner_id, username, event, ip, agent) VALUES (?,?,?,?,?,?)",
                     (now if now is not None else time.time(), owner_id, str(username or '')[:80], event, str(ip or '')[:64],
                      str(agent or '')[:160]))
        if owner_id is not None:
            conn.execute("DELETE FROM auth_log WHERE owner_id = ? AND id NOT IN "
                         "(SELECT id FROM auth_log WHERE owner_id = ? ORDER BY ts DESC, id DESC LIMIT ?)", (owner_id, owner_id, KEEP_PER_OWNER))
        else:
            conn.execute("DELETE FROM auth_log WHERE owner_id IS NULL AND id NOT IN "
                         "(SELECT id FROM auth_log WHERE owner_id IS NULL ORDER BY ts DESC, id DESC LIMIT 200)")
        conn.commit()
        return True
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        return False


def recent(conn, owner_id, limit=DEFAULT_LIMIT):
    ensure(conn)
    limit = max(1, min(int(limit or DEFAULT_LIMIT), MAX_LIMIT))
    return [{'ts': r[0], 'username': r[1], 'event': r[2], 'ip': r[3], 'agent': r[4]} for r in conn.execute(
        "SELECT ts, username, event, ip, agent FROM auth_log WHERE owner_id = ? ORDER BY ts DESC, id DESC LIMIT ?", (owner_id, limit)).fetchall()]


def summary(rows, now=None, hours=24):
    """Compte sur les dernières `hours` heures : connexions réussies, échecs, adresses distinctes."""
    now = now if now is not None else time.time()
    recent_rows = [r for r in rows if now - r['ts'] <= hours * 3600]
    return {'ok': sum(1 for r in recent_rows if r['event'] == 'login_ok'),
            'fail': sum(1 for r in recent_rows if r['event'] == 'login_fail'),
            'ips': len({r['ip'] for r in recent_rows if r['ip']}), 'hours': hours}


def log_event(event, username, owner_id):
    """Appelé par main.py pendant une requête de connexion / déconnexion : au mieux, jamais bloquant."""
    try:
        conn = get_db()
        try:
            record(conn, event, username, owner_id, client_ip(request.headers, request.remote_addr), request.headers.get('User-Agent', ''))
        finally:
            conn.close()
    except Exception as e:
        try:
            app_logger.debug(f"[AUTH-LOG] Écriture ignorée : {type(e).__name__}")
        except Exception:
            pass


def api_auth_log():
    if session.get('role') == 'viewer':
        return jsonify({'error': 'Réservé au compte propriétaire.', 'code': 'viewer_forbidden'}), 403
    try:
        limit = int(request.args.get('limit') or DEFAULT_LIMIT)
    except ValueError:
        limit = DEFAULT_LIMIT
    conn = get_db()
    try:
        rows = recent(conn, session['user_id'], limit)
    finally:
        conn.close()
    return jsonify({'rows': rows, 'summary': summary(rows)})


_ROUTES = (
    ('/api/auth/log', ['GET'], 'api_auth_log', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"login_log.init : services manquants : {missing}")
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
