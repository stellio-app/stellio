"""Stellio — plugin Administration : page d'administration, comptes et rôles, instances supervisées (1.1.7).

Trois situations pour une instance :
  • autonome (par défaut) : contrôle total sur elle-même, rien ne change ;
  • principale (instance d'administration) : elle a au moins une instance appairée qui a accepté sa supervision ;
  • supervisée : elle a accepté la supervision d'une instance principale. Les comptes invités, leurs rôles, leurs permissions et les espaces
    d'équipe ne se modifient plus qu'à partir de la principale (le propriétaire local garde la main sur tout le reste, et peut quitter la supervision).

Le contenu local (bibliothèque, imprimantes, dossiers) reste local par défaut : l'instance principale n'en voit que des totaux si le propriétaire de
l'instance supervisée l'a explicitement permis à l'acceptation.

Appairage : on réutilise celui des instances distantes (table `remote_instances`, clé d'appairage de l'autre instance). La demande exige la clé
d'appairage ; la supervision exige en plus l'ACCEPTATION du propriétaire de l'instance visée, qui reçoit un jeton propre à ce lien (seul son
empreinte est conservée). Les commandes envoyées par la principale exigent la clé d'appairage ET ce jeton.
Les modules d'application des droits (access_control, session_manager, audit_log) restent dans le cœur : désactiver ce plugin retire la page,
jamais les protections.
"""
import hashlib
import os
import secrets
import time

import requests

_REQUIRED = (
    'app',
    'app_logger',
    'get_current_version',
    'get_db',
    'hash_pw',
    'hash_pw_strong',
    'jsonify',
    'load_settings',
    'login_required',
    'request',
    'require_peer_key',
    'save_settings',
    'session',
)
_OPTIONAL = ('_get_primary_user_id',)
_OVERRIDABLE = ('requests', 'time')

_MAIN = {}
app = None
app_logger = None
get_current_version = None
get_db = None
hash_pw = None
hash_pw_strong = None
jsonify = None
load_settings = None
login_required = None
request = None
require_peer_key = None
save_settings = None
session = None
_get_primary_user_id = None

ROLES = ('user', 'operator', 'manager', 'admin')
SETTING = 'supervision'
TIMEOUT = 6
LOCKED_PREFIXES = ('/api/auth/guests', '/api/team/')       # écritures verrouillées sur une instance supervisée
WRITE = ('POST', 'PUT', 'PATCH', 'DELETE')


def ensure(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS supervision_links (
        instance_id INTEGER PRIMARY KEY, token TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'pending',
        keep_local INTEGER NOT NULL DEFAULT 1, requested_at REAL, accepted_at REAL)""")


def _hash(token):
    return hashlib.sha256((token or '').encode('utf-8')).hexdigest()


def _local():
    """État de supervision de CETTE instance (côté instance visée) : {'state': 'none'|'pending'|'supervised', ...}."""
    v = (load_settings() or {}).get(SETTING)
    return v if isinstance(v, dict) and v.get('state') in ('pending', 'supervised') else {'state': 'none'}


def _set_local(v):
    s = load_settings()
    if v and v.get('state') in ('pending', 'supervised'):
        s[SETTING] = v
    else:
        s.pop(SETTING, None)
    save_settings(s)


def role_of(conn=None):
    """'supervised' | 'primary' | 'standalone'."""
    if _local()['state'] == 'supervised':
        return 'supervised'
    own = conn is None
    conn = conn or get_db()
    try:
        ensure(conn)
        n = conn.execute("SELECT COUNT(*) FROM supervision_links WHERE state = 'supervised'").fetchone()[0]
        return 'primary' if n else 'standalone'
    finally:
        if own:
            conn.close()


def _owner_only():
    if session.get('role') == 'viewer':
        return jsonify({'error': 'Réservé au compte propriétaire.', 'code': 'viewer_forbidden'}), 403
    return None


def _owner_id():
    if _get_primary_user_id:
        try:
            return _get_primary_user_id()
        except Exception:
            pass
    conn = get_db()
    try:
        r = conn.execute("SELECT id FROM users ORDER BY id LIMIT 1").fetchone()
        return r[0] if r else None
    finally:
        conn.close()


def _lock():
    """before_request : sur une instance supervisée, les écritures de comptes/équipes ne passent que par la principale."""
    try:
        if request.method in WRITE and any(request.path.startswith(p) for p in LOCKED_PREFIXES):
            st = _local()
            if st['state'] == 'supervised':
                return jsonify({'error': f"Comptes et rôles gérés par l'instance principale « {st.get('name') or '?'} ».",
                                'code': 'supervised', 'supervisor': st.get('name')}), 423
    except Exception as e:
        try:
            app_logger.warning('admin_console: %s', e)
        except Exception:
            pass
    return None


# ── côté instance principale ─────────────────────────────────────────────────────────────────────

def _inst(conn, iid):
    return conn.execute("SELECT id, name, url, peer_key FROM remote_instances WHERE id = ? AND user_id = ?", (iid, session['user_id'])).fetchone()


def _call(inst, method, path, link=None, body=None):
    h = {'X-Stellio-Peer-Key': inst['peer_key']}
    if link:
        h['X-Stellio-Supervisor-Token'] = link['token']
    try:
        r = requests.request(method, f"{inst['url'].rstrip('/')}{path}", headers=h, json=body, timeout=TIMEOUT)
    except Exception:
        return None, {'error': 'Instance injoignable.', 'code': 'offline'}
    try:
        d = r.json()
    except Exception:
        d = {}
    return r.status_code, d


def adm_overview():
    r = _owner_only()
    if r:
        return r
    conn = get_db()
    try:
        ensure(conn)
        rows = conn.execute("SELECT i.id, i.name, i.url, i.last_status, i.last_seen_at, l.state, l.keep_local, l.requested_at, l.accepted_at FROM remote_instances i "
                            "LEFT JOIN supervision_links l ON l.instance_id = i.id WHERE i.user_id = ? ORDER BY i.id", (session['user_id'],)).fetchall()
        st = _local()
        return jsonify({'role': role_of(conn), 'name': (load_settings() or {}).get('instance_name') or '', 'version': get_current_version(),
                        'supervisor': {'name': st.get('name'), 'keep_local': bool(st.get('keep_local', True)), 'accepted_at': st.get('accepted_at')} if st['state'] == 'supervised' else None,
                        'request': {'name': st.get('name'), 'keep_local': bool(st.get('keep_local', True)), 'requested_at': st.get('requested_at')} if st['state'] == 'pending' else None,
                        'instances': [{'id': x['id'], 'name': x['name'], 'url': x['url'], 'last_status': x['last_status'], 'last_seen_at': x['last_seen_at'],
                                       'supervision': x['state'] or 'none', 'keep_local': bool(x['keep_local']) if x['keep_local'] is not None else None} for x in rows]})
    finally:
        conn.close()


def adm_accounts():
    """Comptes de cette instance : propriétaire et invités, avec leur rôle."""
    r = _owner_only()
    if r:
        return r
    conn = get_db()
    try:
        owner = conn.execute("SELECT id, username FROM users WHERE id = ?", (session['user_id'],)).fetchone()
        guests = conn.execute("SELECT id, username, COALESCE(team_role,'') AS team_role, created_at FROM users WHERE role='viewer' AND owner_id=? ORDER BY username COLLATE NOCASE",
                              (session['user_id'],)).fetchall()
        st = _local()
        return jsonify({'owner': dict(owner) if owner else None, 'guests': [dict(g) for g in guests], 'roles': list(ROLES),
                        'locked': st['state'] == 'supervised', 'supervisor': st.get('name') if st['state'] == 'supervised' else None})
    finally:
        conn.close()


def adm_supervise(iid):
    r = _owner_only()
    if r:
        return r
    keep = bool((request.get_json(silent=True) or {}).get('keep_local', True))
    conn = get_db()
    try:
        ensure(conn)
        inst = _inst(conn, iid)
        if not inst:
            return jsonify({'error': 'Instance introuvable.'}), 404
        if role_of(conn) == 'supervised':
            return jsonify({'error': "Cette instance est elle-même supervisée : elle ne peut pas en superviser une autre.", 'code': 'is_supervised'}), 409
        token = secrets.token_urlsafe(32)
        name = (load_settings() or {}).get('instance_name') or 'Stellio'
        code, d = _call(inst, 'POST', '/api/peer/supervision/request', body={'name': name, 'token': token, 'keep_local': keep})
        if code is None:
            return jsonify(d), 502
        if code == 403:
            return jsonify({'error': "Clé d'appairage refusée par l'autre instance."}), 502
        if code != 200:
            return jsonify({'error': d.get('error') or f'Réponse HTTP {code}', 'code': d.get('code')}), 409 if code == 409 else 502
        conn.execute("INSERT OR REPLACE INTO supervision_links (instance_id, token, state, keep_local, requested_at) VALUES (?,?,?,?,?)", (iid, token, 'pending', int(keep), time.time()))
        conn.commit()
        return jsonify({'ok': True, 'state': 'pending'})
    finally:
        conn.close()


def _link(conn, iid):
    return conn.execute("SELECT instance_id, token, state, keep_local FROM supervision_links WHERE instance_id = ?", (iid,)).fetchone()


def adm_instance_status(iid):
    """Interroge l'instance : met à jour l'état du lien (acceptée, refusée, quittée) et renvoie comptes, rôles et totaux autorisés."""
    r = _owner_only()
    if r:
        return r
    conn = get_db()
    try:
        ensure(conn)
        inst, link = _inst(conn, iid), _link(conn, iid)
        if not inst:
            return jsonify({'error': 'Instance introuvable.'}), 404
        if not link:
            return jsonify({'state': 'none'})
        code, d = _call(inst, 'GET', '/api/peer/supervision/status', link)
        if code is None:
            return jsonify({'state': link['state'], 'online': False, 'error': d['error']})
        remote = d.get('state', 'none')
        if remote == 'supervised' and link['state'] != 'supervised':
            conn.execute("UPDATE supervision_links SET state='supervised', accepted_at=? WHERE instance_id=?", (time.time(), iid))
            conn.commit()
        elif remote == 'none':                                  # refusée ou quittée côté instance visée
            conn.execute("DELETE FROM supervision_links WHERE instance_id=?", (iid,))
            conn.commit()
            return jsonify({'state': 'none', 'online': True, 'released': True})
        d['online'] = True
        return jsonify(d)
    finally:
        conn.close()


def adm_instance_command(iid):
    """Commande de gestion de comptes envoyée à une instance supervisée."""
    r = _owner_only()
    if r:
        return r
    body = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        ensure(conn)
        inst, link = _inst(conn, iid), _link(conn, iid)
        if not inst or not link or link['state'] != 'supervised':
            return jsonify({'error': "Instance non supervisée."}), 404
        code, d = _call(inst, 'POST', '/api/peer/supervision/command', link, {'op': body.get('op'), 'args': body.get('args') or {}})
        if code is None:
            return jsonify(d), 502
        return jsonify(d), code
    finally:
        conn.close()


def adm_release(iid):
    """La principale met fin à la supervision."""
    r = _owner_only()
    if r:
        return r
    conn = get_db()
    try:
        ensure(conn)
        inst, link = _inst(conn, iid), _link(conn, iid)
        if not inst:
            return jsonify({'error': 'Instance introuvable.'}), 404
        if link:
            _call(inst, 'POST', '/api/peer/supervision/release', link)       # au mieux : si injoignable, le lien est quand même supprimé ici
            conn.execute("DELETE FROM supervision_links WHERE instance_id=?", (iid,))
            conn.commit()
        return jsonify({'ok': True})
    finally:
        conn.close()


# ── côté instance supervisée (propriétaire local) ────────────────────────────────────────────────

def adm_respond():
    r = _owner_only()
    if r:
        return r
    d = request.get_json(silent=True) or {}
    st = _local()
    if st['state'] != 'pending':
        return jsonify({'error': 'Aucune demande en attente.'}), 404
    if not d.get('accept'):
        _set_local(None)
        return jsonify({'ok': True, 'state': 'none'})
    _set_local({'state': 'supervised', 'name': st.get('name'), 'token_hash': st.get('token_hash'),
                'keep_local': bool(d.get('keep_local', st.get('keep_local', True))), 'accepted_at': time.time()})
    return jsonify({'ok': True, 'state': 'supervised'})


def adm_leave():
    """Échappatoire du propriétaire local : quitter la supervision, à tout moment."""
    r = _owner_only()
    if r:
        return r
    if _local()['state'] == 'none':
        return jsonify({'error': 'Cette instance n\'est pas supervisée.'}), 404
    _set_local(None)
    return jsonify({'ok': True, 'state': 'none'})


def _supervisor_ok():
    st = _local()
    t = request.headers.get('X-Stellio-Supervisor-Token', '')
    return st['state'] == 'supervised' and bool(t) and secrets.compare_digest(_hash(t), st.get('token_hash') or '')


def adm_peer_request():
    d = request.get_json(silent=True) or {}
    token, name = str(d.get('token') or ''), str(d.get('name') or '')[:80]
    if len(token) < 20 or not name:
        return jsonify({'error': 'Demande invalide.'}), 400
    conn = get_db()
    try:
        ensure(conn)
        if conn.execute("SELECT COUNT(*) FROM supervision_links").fetchone()[0]:          # liens actifs OU demandes envoyées non encore tranchées
            return jsonify({'error': "Cette instance supervise déjà d'autres instances.", 'code': 'is_primary'}), 409
    finally:
        conn.close()
    if _local()['state'] == 'supervised':
        return jsonify({'error': 'Cette instance est déjà supervisée.', 'code': 'already_supervised'}), 409
    _set_local({'state': 'pending', 'name': name, 'token_hash': _hash(token), 'keep_local': bool(d.get('keep_local', True)), 'requested_at': time.time()})
    return jsonify({'ok': True, 'state': 'pending'})


def adm_peer_status():
    st = _local()
    if not _pending_token_ok():                                  # sans le jeton de CE lien : rien n'est révélé
        return jsonify({'state': 'none'})
    if st['state'] == 'pending':
        return jsonify({'state': 'pending'})
    conn = get_db()
    try:
        owner = _owner_id()
        guests = [dict(x) for x in conn.execute("SELECT id, username, COALESCE(team_role,'') AS team_role FROM users WHERE role='viewer' AND owner_id=? ORDER BY username COLLATE NOCASE", (owner,)).fetchall()]
        out = {'state': 'supervised', 'name': (load_settings() or {}).get('instance_name') or '', 'version': get_current_version(), 'roles': list(ROLES), 'guests': guests,
               'keep_local': bool(st.get('keep_local', True)), 'sessions': None}
        try:
            out['sessions'] = conn.execute("SELECT COUNT(*) FROM active_sessions WHERE revoked = 0").fetchone()[0]
        except Exception:
            pass
        if not st.get('keep_local', True):                      # totaux de contenu : seulement si le propriétaire local l'a permis
            def n(sql):
                try:
                    return conn.execute(sql).fetchone()[0]
                except Exception:
                    return None
            out['content'] = {'sources': n("SELECT COUNT(*) FROM sources"), 'printers': n("SELECT COUNT(*) FROM printers")}
        return jsonify(out)
    finally:
        conn.close()


def _pending_token_ok():
    t = request.headers.get('X-Stellio-Supervisor-Token', '')
    return bool(t) and secrets.compare_digest(_hash(t), _local().get('token_hash') or '')


def adm_peer_command():
    if not _supervisor_ok():
        return jsonify({'error': 'Supervision non autorisée.', 'code': 'not_supervisor'}), 403
    d = request.get_json(silent=True) or {}
    op, a = d.get('op'), d.get('args') or {}
    owner = _owner_id()
    conn = get_db()
    try:
        if op == 'guest_role':
            role = str(a.get('role') or '')
            if role and role not in ROLES:
                return jsonify({'error': 'Rôle inconnu.'}), 400
            n = conn.execute("UPDATE users SET team_role=? WHERE id=? AND role='viewer' AND owner_id=?", (role, int(a.get('id') or 0), owner)).rowcount
        elif op == 'guest_create':
            u, p = str(a.get('username') or '').strip()[:60], str(a.get('password') or '')
            if not u or len(p) < 4:
                return jsonify({'error': 'Nom et mot de passe (4 caractères minimum) requis.'}), 400
            try:
                conn.execute("INSERT INTO users (username, password_hash, role, owner_id, recovery_code_hash, team_role) VALUES (?,?,'viewer',?,?,?)",
                             (u, hash_pw_strong(p), owner, hash_pw(secrets.token_hex(16)), a.get('role') if a.get('role') in ROLES else ''))
            except Exception:
                return jsonify({'error': "Nom d'utilisateur déjà utilisé."}), 409
            n = 1
        elif op == 'guest_delete':
            n = conn.execute("DELETE FROM users WHERE id=? AND role='viewer' AND owner_id=?", (int(a.get('id') or 0), owner)).rowcount
        elif op == 'guest_password':
            p = str(a.get('password') or '')
            if len(p) < 4:
                return jsonify({'error': 'Mot de passe trop court (4 caractères minimum).'}), 400
            n = conn.execute("UPDATE users SET password_hash=? WHERE id=? AND role='viewer' AND owner_id=?", (hash_pw_strong(p), int(a.get('id') or 0), owner)).rowcount
        else:
            return jsonify({'error': 'Commande inconnue.'}), 400
        conn.commit()
        if not n:
            return jsonify({'error': 'Invité introuvable.'}), 404
        try:
            app_logger.info('supervision: commande %s appliquée par « %s »', op, _local().get('name'))
        except Exception:
            pass
        return jsonify({'ok': True})
    finally:
        conn.close()


def adm_peer_release():
    if not _supervisor_ok():
        return jsonify({'error': 'Supervision non autorisée.', 'code': 'not_supervisor'}), 403
    _set_local(None)
    return jsonify({'ok': True})


def adm_ui_script():
    return app.response_class(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'administration.js'), 'rb').read(), mimetype='application/javascript')


_ROUTES = (
    ('/administration.js', ['GET'], 'adm_ui_script', ()),
    ('/api/admin/overview', ['GET'], 'adm_overview', ('login_required', )),
    ('/api/admin/accounts', ['GET'], 'adm_accounts', ('login_required', )),
    ('/api/admin/instances/<int:iid>/supervise', ['POST'], 'adm_supervise', ('login_required', )),
    ('/api/admin/instances/<int:iid>/status', ['GET'], 'adm_instance_status', ('login_required', )),
    ('/api/admin/instances/<int:iid>/command', ['POST'], 'adm_instance_command', ('login_required', )),
    ('/api/admin/instances/<int:iid>/release', ['POST'], 'adm_release', ('login_required', )),
    ('/api/admin/supervision/respond', ['POST'], 'adm_respond', ('login_required', )),
    ('/api/admin/supervision/leave', ['POST'], 'adm_leave', ('login_required', )),
    ('/api/peer/supervision/request', ['POST'], 'adm_peer_request', ('require_peer_key', )),
    ('/api/peer/supervision/status', ['GET'], 'adm_peer_status', ('require_peer_key', )),
    ('/api/peer/supervision/command', ['POST'], 'adm_peer_command', ('require_peer_key', )),
    ('/api/peer/supervision/release', ['POST'], 'adm_peer_release', ('require_peer_key', )),
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
        try:
            c = g['get_db']()
            try:
                ensure(c)
                c.commit()
            finally:
                c.close()
        except Exception:
            pass
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
        g['app'].before_request(_lock)
    return {}
