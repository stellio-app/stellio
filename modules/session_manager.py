"""Stellio — sessions actives : liste, révocation d'une session ou de toutes les autres (1.1.7).

Une session Flask est un cookie signé : sans suivi côté serveur on ne peut pas la révoquer. Chaque session connectée reçoit donc un identifiant
(`session['sid']`) et une ligne dans `active_sessions` (adresse IP, navigateur, dernière activité). Une session révoquée est coupée à sa requête
suivante ; pour ne pas ajouter une lecture de base à chaque appel, l'état est relu au plus toutes les 15 s (la révocation prend donc au plus 15 s).
Réservé au propriétaire. Les invités et la démo ne peuvent ni lister ni révoquer.
"""
import threading
import time
import uuid

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

CHECK_EVERY = 15          # secondes entre deux relectures de l'état « révoquée »
TOUCH_EVERY = 60          # secondes entre deux mises à jour de « dernière activité »
KEEP_DAYS = 90
MERGE_WINDOW = 30         # secondes : des requêtes simultanées d'un même navigateur (chargement de page) partagent UNE session
_reg_lock = threading.Lock()
MAX_ROWS = 500


def ensure(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS active_sessions (
        sid TEXT PRIMARY KEY, user_id INTEGER NOT NULL, kind TEXT, viewer_id INTEGER, ip TEXT, ua TEXT,
        created REAL, last_seen REAL, revoked INTEGER NOT NULL DEFAULT 0, revoked_at REAL)""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON active_sessions(user_id, last_seen DESC)")


def _purge(conn, now):
    conn.execute("DELETE FROM active_sessions WHERE last_seen < ?", (now - KEEP_DAYS * 86400,))
    conn.execute("DELETE FROM active_sessions WHERE sid NOT IN (SELECT sid FROM active_sessions ORDER BY last_seen DESC LIMIT ?)", (MAX_ROWS,))


def register(conn, uid, kind, viewer_id, ip, ua, now):
    """Crée la session suivie (ou retrouve celle que viennent de créer, il y a moins de 30 s, des requêtes simultanées du même navigateur :
    au chargement d'une page l'interface envoie des dizaines de requêtes en parallèle, sans cookie de session suivie au départ)."""
    ip, ua = (ip or '')[:64], (ua or '')[:200]
    with _reg_lock:
        ensure(conn)
        r = conn.execute("SELECT sid FROM active_sessions WHERE user_id = ? AND kind = ? AND COALESCE(viewer_id, 0) = COALESCE(?, 0) AND ip = ? AND ua = ? AND revoked = 0 AND created > ? "
                         "ORDER BY created DESC LIMIT 1", (uid, kind, viewer_id, ip, ua, now - MERGE_WINDOW)).fetchone()
        if r:
            return r[0]
        sid = uuid.uuid4().hex
        conn.execute("INSERT INTO active_sessions (sid, user_id, kind, viewer_id, ip, ua, created, last_seen) VALUES (?,?,?,?,?,?,?,?)", (sid, uid, kind, viewer_id, ip, ua, now, now))
        _purge(conn, now)
        conn.commit()
        return sid


def is_revoked(conn, sid):
    r = conn.execute("SELECT revoked FROM active_sessions WHERE sid = ?", (sid,)).fetchone()
    return bool(r and r[0])


def revoke(conn, uid, sid, now):
    return conn.execute("UPDATE active_sessions SET revoked = 1, revoked_at = ? WHERE sid = ? AND user_id = ? AND revoked = 0", (now, sid, uid)).rowcount


def revoke_others(conn, uid, keep_sid, now):
    return conn.execute("UPDATE active_sessions SET revoked = 1, revoked_at = ? WHERE user_id = ? AND sid <> ? AND revoked = 0", (now, uid, keep_sid or '')).rowcount


def _before():
    """before_request : suit la session connectée et coupe une session révoquée. Ne casse jamais la requête."""
    try:
        if 'user_id' not in session or not request.path.startswith('/api/'):
            return None
        now = time.time()
        sid = session.get('sid')
        if sid and now - session.get('sid_chk', 0) < CHECK_EVERY:
            return None
        conn = get_db()
        try:
            ensure(conn)
            if not sid:
                kind = 'viewer' if session.get('role') == 'viewer' else 'user'
                session['sid'] = register(conn, session['user_id'], kind, session.get('viewer_id'), request.remote_addr, request.headers.get('User-Agent', ''), now)
            else:
                row = conn.execute("SELECT revoked FROM active_sessions WHERE sid = ?", (sid,)).fetchone()
                if row and row[0]:
                    session.clear()
                    conn.commit()
                    return jsonify({'error': 'Session révoquée : reconnectez-vous.', 'code': 'session_revoked'}), 401
                if row is None:                                   # ligne purgée : on la recrée plutôt que de déconnecter
                    session['sid'] = register(conn, session['user_id'], 'viewer' if session.get('role') == 'viewer' else 'user', session.get('viewer_id'),
                                              request.remote_addr, request.headers.get('User-Agent', ''), now)
                elif now - session.get('sid_touch', 0) >= TOUCH_EVERY:
                    conn.execute("UPDATE active_sessions SET last_seen = ?, ip = ? WHERE sid = ?", (now, (request.remote_addr or '')[:64], sid))
                    session['sid_touch'] = now
            session['sid_chk'] = now
            conn.commit()
        finally:
            conn.close()
    except Exception as e:      # le suivi est un confort de sécurité, il ne doit jamais bloquer l'appli
        try:
            app_logger.warning('session_manager: %s', e)
        except Exception:
            pass
    return None


def _owner_only():
    if session.get('role') == 'viewer':
        return jsonify({'error': 'Réservé au compte propriétaire.', 'code': 'viewer_forbidden'}), 403
    return None


def api_sessions():
    r = _owner_only()
    if r:
        return r
    conn = get_db()
    try:
        ensure(conn)
        rows = conn.execute("SELECT sid, kind, viewer_id, ip, ua, created, last_seen, revoked FROM active_sessions WHERE user_id = ? AND revoked = 0 ORDER BY last_seen DESC LIMIT 100",
                            (session['user_id'],)).fetchall()
        cur = session.get('sid')
        return jsonify({'sessions': [dict(x, current=(x['sid'] == cur)) for x in rows], 'current': cur, 'check_every_s': CHECK_EVERY})
    finally:
        conn.close()


def api_session_revoke(sid):
    r = _owner_only()
    if r:
        return r
    conn = get_db()
    try:
        ensure(conn)
        n = revoke(conn, session['user_id'], sid, time.time())
        conn.commit()
    finally:
        conn.close()
    if not n:
        return jsonify({'error': 'Session introuvable ou déjà révoquée.'}), 404
    return jsonify({'ok': True, 'self': sid == session.get('sid')})


def api_session_revoke_others():
    r = _owner_only()
    if r:
        return r
    conn = get_db()
    try:
        ensure(conn)
        n = revoke_others(conn, session['user_id'], session.get('sid'), time.time())
        conn.commit()
    finally:
        conn.close()
    return jsonify({'ok': True, 'revoked': n})


_ROUTES = (
    ('/api/sessions', ['GET'], 'api_sessions', ('login_required', )),
    ('/api/sessions/<sid>/revoke', ['POST'], 'api_session_revoke', ('login_required', )),
    ('/api/sessions/revoke-others', ['POST'], 'api_session_revoke_others', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"{__name__}.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
        g['app'].before_request(_before)
    return {}
