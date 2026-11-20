"""Stellio — journal d'audit général (1.1.7).

Enregistre qui a fait quoi d'important : modification des réglages, comptes invités, imprimantes, mises à jour, accès distant,
suppressions, équipes et permissions, plugins, synchronisation, appels d'écriture de l'API publique. Complète le journal des
connexions (login_log). Un évènement = (date, propriétaire, acteur, nature de l'acteur, action, cible, adresse, accès distant oui/non).
Jamais de mot de passe, de jeton ni de corps de requête : seulement la route et son résultat. Conservation : 5 000 lignes par propriétaire.
Branché par un after_request : une requête réussie (code < 400) qui correspond à `RULES` laisse une ligne ; le reste est ignoré.
"""
import csv
import io
import re
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

KEEP_PER_OWNER = 5000
MAX_LIMIT = 500
DEFAULT_LIMIT = 100

# (méthodes, expression de la route, action, nom de la cible dans la route ou None)
RULES = (
    (('POST',), r'^/api/auth/guests$', 'guest.create', None),
    (('PUT',), r'^/api/auth/guests/(?P<t>\d+)$', 'guest.password', 't'),
    (('DELETE',), r'^/api/auth/guests/(?P<t>\d+)$', 'guest.delete', 't'),
    (('POST',), r'^/api/settings$', 'settings.change', None),
    (('POST',), r'^/api/settings/undo$', 'settings.undo', None),
    (('POST',), r'^/api/update/(?P<t>download|install)$', 'update.run', 't'),
    (('POST', 'DELETE'), r'^/api/remote-access/(?P<t>[\w-]+)$', 'remote_access.change', 't'),
    (('POST',), r'^/api/printers$', 'printer.create', None),
    (('PUT', 'DELETE'), r'^/api/printers/(?P<t>\d+)$', 'printer.change', 't'),
    (('PUT',), r'^/api/printers/(?P<t>\d+)/power$', 'printer.power', 't'),
    (('POST',), r'^/api/printers/(?P<t>\d+)/upload$', 'printer.upload', 't'),
    (('POST',), r'^/api/slicer/send(?:-batch)?$', 'print.send', None),
    (('POST', 'DELETE'), r'^/api/accounts(?:/(?P<t>[\w-]+))?(?:/[\w-]+)?$', 'platform_account.change', 't'),
    (('DELETE',), r'^/api/print-history(?:/(?P<t>\d+|clear|by-file))?$', 'history.delete', 't'),
    (('DELETE',), r'^/api/orders/(?P<t>\d+)$', 'order.delete', 't'),
    (('DELETE',), r'^/api/projects/(?P<t>\d+)$', 'project.delete', 't'),
    (('DELETE',), r'^/api/sources/(?P<t>\d+)$', 'source.delete', 't'),
    (('POST', 'DELETE'), r'^/api/tokens(?:/(?P<t>\d+))?$', 'api_token.change', 't'),
    (('POST', 'PUT', 'DELETE'), r'^/api/webhooks(?:/(?P<t>[\w-]+))?(?:/[\w-]+)?$', 'webhook.change', 't'),
    (('POST', 'PUT', 'DELETE'), r'^/api/team(?:/.*)?$', 'team.change', None),
    (('POST', 'PUT', 'DELETE'), r'^/api/plugins(?:/(?P<t>[\w.-]+))?(?:/[\w-]+)?$', 'plugin.change', 't'),
    (('POST', 'PUT', 'DELETE'), r'^/api/sync(?:/.*)?$', 'sync.change', None),
    (('POST', 'PUT', 'DELETE'), r'^/api/community(?:/.*)?$', 'community.change', None),
    (('POST', 'PUT', 'DELETE'), r'^/api/organize/(?:apply|rules.*)$', 'organize.change', None),
    (('POST', 'PATCH'), r'^/api/v1/(?P<t>tasks(?:/\d+)?)$', 'api.write', 't'),
)
_COMPILED = tuple((m, re.compile(rx), act, tg) for m, rx, act, tg in RULES)


def classify(method, path):
    """(action, cible) ou None si la requête n'est pas à journaliser."""
    for methods, rx, action, tg in _COMPILED:
        if method in methods:
            m = rx.match(path or '')
            if m:
                return action, (m.groupdict().get(tg) if tg else None) or ''
    return None


def ensure(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, owner_id INTEGER, actor TEXT, actor_kind TEXT,
        action TEXT NOT NULL, target TEXT, method TEXT, path TEXT, status INTEGER, ip TEXT, remote INTEGER DEFAULT 0)""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_owner_ts ON audit_log(owner_id, ts DESC)")


def record(conn, owner_id, actor, actor_kind, action, target, method, path, status, ip, remote, now=None):
    try:
        ensure(conn)
        conn.execute("INSERT INTO audit_log (ts, owner_id, actor, actor_kind, action, target, method, path, status, ip, remote) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                     (now if now is not None else time.time(), owner_id, str(actor or '')[:80], actor_kind, action, str(target or '')[:80],
                      method, str(path or '')[:200], int(status), str(ip or '')[:64], 1 if remote else 0))
        conn.execute("DELETE FROM audit_log WHERE owner_id IS ? AND id NOT IN (SELECT id FROM audit_log WHERE owner_id IS ? ORDER BY ts DESC, id DESC LIMIT ?)",
                     (owner_id, owner_id, KEEP_PER_OWNER))
        conn.commit()
        return True
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        return False


def _where(owner_id, action, actor, since, remote_only):
    sql, args = " WHERE owner_id = ?", [owner_id]
    if action:
        sql += " AND action LIKE ?"
        args.append(action.replace('%', '') + '%')
    if actor:
        sql += " AND actor = ?"
        args.append(actor)
    if since:
        sql += " AND ts >= ?"
        args.append(float(since))
    if remote_only:
        sql += " AND remote = 1"
    return sql, args


def query(conn, owner_id, limit=DEFAULT_LIMIT, action=None, actor=None, since=None, remote_only=False, offset=0):
    """Lignes du journal, les plus récentes d'abord. `offset` permet de paginer (l'interface affiche peu de lignes à la fois)."""
    ensure(conn)
    where, args = _where(owner_id, action, actor, since, remote_only)
    sql = "SELECT ts, actor, actor_kind, action, target, method, path, status, ip, remote FROM audit_log" + where + " ORDER BY ts DESC, id DESC LIMIT ? OFFSET ?"
    args += [max(1, min(int(limit or DEFAULT_LIMIT), MAX_LIMIT)), max(0, min(int(offset or 0), 1000000))]
    return [dict(r) for r in conn.execute(sql, args).fetchall()]


def count(conn, owner_id, action=None, actor=None, since=None, remote_only=False):
    ensure(conn)
    where, args = _where(owner_id, action, actor, since, remote_only)
    return conn.execute("SELECT COUNT(*) FROM audit_log" + where, args).fetchone()[0]


def to_csv(rows):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(['date', 'acteur', 'type', 'action', 'cible', 'methode', 'route', 'code', 'adresse', 'acces_distant'])
    for r in rows:
        w.writerow([time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(r['ts'])), r['actor'], r['actor_kind'], r['action'], r['target'],
                    r['method'], r['path'], r['status'], r['ip'], 'oui' if r['remote'] else 'non'])
    return out.getvalue()


def _is_remote(headers):
    return bool(headers.get('CF-Connecting-IP') or headers.get('X-Forwarded-For'))


def _after(response):
    """after_request : au mieux, ne perturbe jamais la réponse."""
    try:
        if request.method in ('GET', 'HEAD', 'OPTIONS') or response.status_code >= 400:
            return response
        hit = classify(request.method, request.path)
        if not hit:
            return response
        tok = request.environ.get('stellio.api_token')
        if tok:
            owner, actor, kind = tok['user_id'], f"jeton « {tok['name']} »", 'api'
        elif 'user_id' in session:
            owner, actor = session['user_id'], session.get('username') or ''
            kind = 'viewer' if session.get('role') == 'viewer' else 'user'
        else:
            return response
        conn = get_db()
        try:
            hdr = request.headers
            ip = (hdr.get('CF-Connecting-IP') or (hdr.get('X-Forwarded-For') or '').split(',')[0].strip() or request.remote_addr or '')
            record(conn, owner, actor, kind, hit[0], hit[1], request.method, request.path, response.status_code, ip, _is_remote(hdr))
        finally:
            conn.close()
    except Exception as e:
        try:
            app_logger.debug(f"[AUDIT] ignoré : {type(e).__name__}")
        except Exception:
            pass
    return response


def _no_viewer():
    if session.get('role') == 'viewer' and not _demo_ok():
        return jsonify({'error': 'Réservé au compte propriétaire.', 'code': 'viewer_forbidden'}), 403
    return None


def _args():
    try:
        limit = int(request.args.get('limit') or DEFAULT_LIMIT)
    except ValueError:
        limit = DEFAULT_LIMIT
    try:
        since = float(request.args.get('since')) if request.args.get('since') else None
    except ValueError:
        since = None
    try:
        offset = int(request.args.get('offset') or 0)
    except ValueError:
        offset = 0
    return dict(limit=limit, offset=offset, action=(request.args.get('action') or '').strip()[:40] or None, actor=(request.args.get('actor') or '').strip()[:80] or None,
                since=since, remote_only=request.args.get('remote') in ('1', 'true'))


def api_audit():
    r = _no_viewer()
    if r:
        return r
    conn = get_db()
    try:
        a = _args()
        rows = query(conn, session['user_id'], **a)
        total = count(conn, session['user_id'], a['action'], a['actor'], a['since'], a['remote_only'])
    finally:
        conn.close()
    if session.get('role') == 'viewer':                       # démo : jamais les adresses ni les noms des autres visiteurs
        rows = [dict(x, ip='', actor='—') for x in rows]
    return jsonify({'rows': rows, 'count': len(rows), 'total': total, 'offset': a['offset'], 'limit': a['limit'], 'remote': sum(1 for x in rows if x['remote'])})


def api_audit_csv():
    if session.get('role') == 'viewer':                       # l'export complet reste réservé au propriétaire (démo comprise)
        return jsonify({'error': 'Réservé au compte propriétaire.', 'code': 'viewer_forbidden'}), 403
    r = _no_viewer()
    if r:
        return r
    conn = get_db()
    try:
        a = _args(); a['limit'] = MAX_LIMIT; a['offset'] = 0
        rows = query(conn, session['user_id'], **a)
    finally:
        conn.close()
    return app.response_class(to_csv(rows), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=stellio-audit.csv'})


_DEMO_COMPUTE = ('/api/plate/arrange', '/api/organize/preview', '/api/model-diff')


def _demo_ok():
    """Démo publique (lecture seule, `IS_DEMO` posé par la surcouche de démo) : consultation (GET) et calculs sans écriture."""
    try:
        return bool(_MAIN.get('IS_DEMO')) and (request.method in ('GET', 'HEAD') or request.path in _DEMO_COMPUTE)
    except Exception:
        return False


_ROUTES = (
    ('/api/audit', ['GET'], 'api_audit', ('login_required', )),
    ('/api/audit/export.csv', ['GET'], 'api_audit_csv', ('login_required', )),
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
        g['app'].after_request(_after)
    return {}
