"""Stellio — alertes d'expiration de licence (1.1.7).

Une licence peut avoir une date d'expiration (colonne `file_origins.license_expires`, migration 3) : licence commerciale à durée
limitée, autorisation temporaire d'un auteur… `/api/licenses/expiring` liste ce qui est expiré ou expire bientôt ; le nombre sert de badge.
Dates au format AAAA-MM-JJ. Aucune action automatique : Stellio prévient, il ne supprime rien.
"""
import datetime
import hashlib
import os
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
_OPTIONAL = ('_insert_notification_once', '_push_notify_async', '_send_native_notification', '_server_t')
_OVERRIDABLE = ('datetime', 'time')

_MAIN = {}
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None
_insert_notification_once = None
_push_notify_async = None
_send_native_notification = None
_server_t = None

DEFAULT_DAYS = 30
MAX_DAYS = 365


def parse_date(s):
    try:
        return datetime.date.fromisoformat(str(s or '').strip()[:10])
    except ValueError:
        return None


def classify(expires, today=None, days=DEFAULT_DAYS):
    """'expired' | 'soon' | 'ok' | None (date absente ou invalide) + jours restants (négatif = déjà expiré)."""
    d = parse_date(expires)
    if d is None:
        return None, None
    today = today or datetime.date.today()
    left = (d - today).days
    if left < 0:
        return 'expired', left
    return ('soon' if left <= days else 'ok'), left


def expiring(rows, today=None, days=DEFAULT_DAYS):
    """rows : dicts {file_path, license, license_expires}. Retourne expirés d'abord, puis par échéance."""
    out = []
    for r in rows:
        status, left = classify(r.get('license_expires'), today, days)
        if status in ('expired', 'soon'):
            out.append({'path': r['file_path'], 'name': os.path.basename(r['file_path']), 'license': r.get('license') or '',
                        'expires': str(r['license_expires'])[:10], 'status': status, 'days_left': left})
    return sorted(out, key=lambda x: x['days_left'])


def _has_col(conn):
    return any(r[1] == 'license_expires' for r in conn.execute("PRAGMA table_info(file_origins)").fetchall())


def api_licenses_expiring():
    try:
        days = max(1, min(int(request.args.get('days') or DEFAULT_DAYS), MAX_DAYS))
    except ValueError:
        days = DEFAULT_DAYS
    conn = get_db()
    try:
        if not _has_col(conn):
            return jsonify({'items': [], 'count': 0, 'days': days})
        rows = [dict(r) for r in conn.execute("SELECT file_path, license, license_expires FROM file_origins WHERE user_id=? AND COALESCE(license_expires,'')<>''",
                                              (session['user_id'],)).fetchall()]
        items = expiring(rows, days=days)
        return jsonify({'items': items, 'count': len(items), 'expired': sum(1 for i in items if i['status'] == 'expired'), 'days': days})
    finally:
        conn.close()


def api_license_expiry_set():
    if session.get('role') == 'viewer' and not _demo_ok():
        return jsonify({'error': 'Réservé au compte propriétaire.', 'code': 'viewer_forbidden'}), 403
    data = request.get_json(silent=True) or {}
    path = str(data.get('path') or '').replace('\\', '/').strip()
    date = str(data.get('date') or '').strip()
    if not path:
        return jsonify({'error': 'Fichier manquant.'}), 400
    if date and parse_date(date) is None:
        return jsonify({'error': 'Date invalide (AAAA-MM-JJ).'}), 400
    conn = get_db()
    try:
        if not _has_col(conn):
            return jsonify({'error': 'Base non migrée (redémarrez Stellio).'}), 409
        exists = conn.execute("SELECT 1 FROM file_origins WHERE file_path=? AND user_id=?", (path, session['user_id'])).fetchone()
        if not exists:
            conn.execute("INSERT INTO file_origins (file_path, user_id, updated_at) VALUES (?,?,CURRENT_TIMESTAMP)", (path, session['user_id']))
        conn.execute("UPDATE file_origins SET license_expires=? WHERE file_path=? AND user_id=?", (date or None, path, session['user_id']))
        conn.commit()
        return jsonify({'ok': True, 'status': classify(date)[0] if date else None})
    finally:
        conn.close()


def _tx(key, default):
    try:
        return _server_t(key, default) if _server_t else default
    except Exception:
        return default


def alerts_once(today=None, days=DEFAULT_DAYS):
    """Crée une notification (centre de notifications + notification native + push si configurés) pour chaque licence qui expire bientôt ou a expiré.
    Dédoublonnage : une seule fois par fichier, par état (« bientôt » puis « expirée ») et par date d'expiration. Retourne le nombre de nouvelles notifications."""
    if _insert_notification_once is None:
        return 0
    conn = get_db()
    try:
        if not _has_col(conn):
            return 0
        rows = [dict(r) for r in conn.execute("SELECT user_id, file_path, license, license_expires FROM file_origins WHERE COALESCE(license_expires,'')<>''").fetchall()]
    finally:
        conn.close()
    created = 0
    for uid in sorted({r['user_id'] for r in rows}):
        for it in expiring([r for r in rows if r['user_id'] == uid], today, days):
            kind = 'license_expired' if it['status'] == 'expired' else 'license_soon'
            key = 'lic:%s:%s' % (kind, hashlib.sha1(('%s|%s' % (it['path'], it['expires'])).encode('utf-8', 'replace')).hexdigest()[:16])
            if it['status'] == 'expired':
                title = _tx('notif.license_expired_title', 'Licence expirée')
                msg = '%s — %s (%s)' % (it['name'], it['license'] or '?', it['expires'])
            else:
                title = _tx('notif.license_soon_title', 'Licence bientôt expirée')
                msg = '%s — %s (%s, J-%d)' % (it['name'], it['license'] or '?', it['expires'], it['days_left'])
            try:
                if _insert_notification_once(uid, kind, title, msg, 'library', key):
                    created += 1
                    if _send_native_notification:
                        _send_native_notification(title, msg)
                    if _push_notify_async:
                        _push_notify_async(kind, title, msg)
            except Exception as e:
                try:
                    _MAIN['app_logger'].debug('license alerts: %s', e)
                except Exception:
                    pass
    return created


def _loop():
    time.sleep(120)
    while True:
        try:
            alerts_once()
        except Exception as e:
            try:
                _MAIN['app_logger'].debug('license loop: %s', e)
            except Exception:
                pass
        time.sleep(6 * 3600)


_DEMO_COMPUTE = ('/api/plate/arrange', '/api/organize/preview', '/api/model-diff')


def _demo_ok():
    """Démo publique (lecture seule, `IS_DEMO` posé par la surcouche de démo) : consultation (GET) et calculs sans écriture."""
    try:
        return bool(_MAIN.get('IS_DEMO')) and (request.method in ('GET', 'HEAD') or request.path in _DEMO_COMPUTE)
    except Exception:
        return False


_ROUTES = (
    ('/api/licenses/expiring', ['GET'], 'api_licenses_expiring', ('login_required', )),
    ('/api/files/license-expiry', ['PUT'], 'api_license_expiry_set', ('login_required', )),
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
    return {}
