"""Stellio — équipes, rôles et permissions (1.1.7).

Le compte propriétaire reste le seul à tout gérer. Ses comptes invités reçoivent un RÔLE D'ÉQUIPE (colonne `users.team_role`) :
  (vide)    lecture seule — comportement historique des invités, inchangé ;
  operator  lance des impressions, envoie des fichiers aux imprimantes, note les impressions, avance les commandes ;
  manager   operator + crée / supprime commandes, projets, file d'impression, historique ;
  admin     manager + ajoute / modifie / supprime les imprimantes.
Réglages du compte (réglages, jetons, accès distant, mises à jour, invités, sauvegardes) : propriétaire seulement, quel que soit le rôle.

Permissions fines, par imprimante, par dossier et par projet :
  - `team_permissions` : entrée directe (invité, type, cible, niveau none / view / use / manage) ;
  - ESPACES DE TRAVAIL : un groupe nommé de membres (avec un rôle propre à l'espace) et d'éléments (imprimantes, dossiers, projets).
Dès qu'un invité a au moins une entrée d'un type (directe ou via un espace), il est en liste blanche pour ce type : seuls les éléments
accordés lui sont ouverts. Sans entrée, c'est son rôle global qui décide. « none » refuse toujours. Les permissions portent sur les ACTIONS
d'écriture ; la lecture reste celle des invités (voir main.py : _VIEWER_BLOCKED_GET_PREFIXES).
`team_decision()` est appelé par `_viewer_guard` de main.py avant de refuser une écriture d'invité.
"""
import re

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
_OVERRIDABLE = ()

_MAIN = {}
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None

ROLES = ('user', 'operator', 'manager', 'admin')      # user = utilisateur simple (annote, note et photographie ses impressions) ; '' = invité (lecture seule)
RANK = {'': 0, 'user': 0.5, 'operator': 1, 'manager': 2, 'admin': 3}
LEVELS = ('none', 'view', 'use', 'manage')
LEVEL_RANK = {'none': -1, 'view': 0, 'use': 1, 'manage': 2}      # rang équivalent à un rôle (use ≈ operator, manage ≈ manager)
SUBJECT_TYPES = ('printer', 'folder', 'project')
MAX_WORKSPACES = 20

# (méthodes, expression, rôle minimum, sujets lus dans la route : {type: nom du groupe})
RULES = (
    (('POST',), r'^/api/printers/(?P<printer>\d+)/upload$', 'operator'),
    (('PUT',), r'^/api/printers/(?P<printer>\d+)/power$', 'operator'),
    (('POST',), r'^/api/printers/(?P<printer>\d+)/maintenance$', 'operator'),
    (('POST',), r'^/api/printers/maintenance/\d+/reset$', 'operator'),
    (('PUT', 'DELETE'), r'^/api/printers/maintenance/\d+$', 'manager'),
    (('POST',), r'^/api/printers/(?P<printer>\d+)/hours/add$', 'manager'),
    (('POST',), r'^/api/printers$', 'admin'),
    (('PUT', 'DELETE'), r'^/api/printers/(?P<printer>\d+)$', 'admin'),
    (('POST',), r'^/api/slicer/send(?:-batch)?$', 'operator'),
    (('POST',), r'^/api/print-history/\d+/rate$', 'user'),
    (('POST',), r'^/api/print-history/(?:\d+/cost|manual)$', 'operator'),
    (('DELETE',), r'^/api/print-history/\d+$', 'manager'),
    (('POST',), r'^/api/print-queue(?:/reorder)?$', 'operator'),
    (('DELETE',), r'^/api/print-queue$', 'manager'),
    (('POST',), r'^/api/orders$', 'manager'),
    (('PUT',), r'^/api/orders/\d+$', 'operator'),
    (('DELETE',), r'^/api/orders/\d+$', 'manager'),
    (('POST',), r'^/api/projects$', 'manager'),
    (('POST', 'PUT', 'DELETE'), r'^/api/projects/(?P<project>\d+)(?:/files)?$', 'manager'),
    (('POST',), r'^/api/print-photos$', 'user'),
    (('PATCH',), r'^/api/print-photos/\d+$', 'operator'),
    (('DELETE',), r'^/api/print-photos/\d+$', 'manager'),
)
_COMPILED = tuple((m, re.compile(rx), role) for m, rx, role in RULES)


def match_rule(method, path):
    """(rôle minimum, {type: id}) ou None si cette écriture n'est pas ouverte aux comptes d'équipe."""
    for methods, rx, role in _COMPILED:
        if method in methods:
            m = rx.match(path or '')
            if m:
                return role, {k: v for k, v in m.groupdict().items() if v}
    return None


def norm_dir(p):
    return str(p or '').replace('\\', '/').rstrip('/')


def folder_covers(folder, path):
    folder, path = norm_dir(folder), norm_dir(path)
    return bool(folder) and (path == folder or path.startswith(folder + '/'))


def grants_for(subject_type, subject, grants):
    """grants : liste de {type, subject, rank}. Retourne les entrées qui visent ce sujet (dossier : préfixe)."""
    out = []
    for g in grants:
        if g['type'] != subject_type:
            continue
        if subject_type == 'folder':
            if folder_covers(g['subject'], subject):
                out.append(g)
        elif str(g['subject']) == str(subject):
            out.append(g)
    return out


def decide(role, need_role, subjects, grants):
    """Cœur de la décision (pur). role : rôle global du compte ; need_role : rôle minimum de l'action ;
    subjects : liste de (type, id) visés par la requête ; grants : permissions de ce compte (directes + espaces).
    Retourne (True, '') ou (False, raison)."""
    need = RANK[need_role]
    if RANK.get(role, 0) < 0.5 and not grants:          # ni rôle global ni accès via un espace / une permission : lecture seule
        return False, 'Compte en lecture seule.'
    for stype, sid in subjects:
        typed = [g for g in grants if g['type'] == stype]
        if not typed:                                    # pas de restriction pour ce type : le rôle global décide
            if RANK.get(role, 0) < need:
                return False, f"Le rôle « {role or 'invité'} » ne permet pas cette action."
            continue
        hits = grants_for(stype, sid, grants)
        if any(g['rank'] < 0 for g in hits):
            return False, f"Accès refusé à cet élément ({stype})."
        if not hits:
            return False, f"Cet élément ({stype}) ne fait pas partie de vos accès."
        best = max(g['rank'] for g in hits)
        # un accès « use » (1) suffit pour une action d'opérateur, « manage » (2) pour manager et admin
        if best < min(need, 2):
            return False, f"Niveau d'accès insuffisant sur cet élément ({stype})."
        if RANK.get(role, 0) < need and best < need:
            return False, f"Le rôle « {role} » ne permet pas cette action."
    if not subjects and RANK.get(role, 0) < need:
        return False, f"Le rôle « {role} » ne permet pas cette action."
    return True, ''


# ── base ──

def ensure(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS workspaces (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER NOT NULL, name TEXT NOT NULL, created_at REAL);
        CREATE TABLE IF NOT EXISTS workspace_members (workspace_id INTEGER NOT NULL, user_id INTEGER NOT NULL, role TEXT NOT NULL, PRIMARY KEY (workspace_id, user_id));
        CREATE TABLE IF NOT EXISTS workspace_items (workspace_id INTEGER NOT NULL, subject_type TEXT NOT NULL, subject TEXT NOT NULL, PRIMARY KEY (workspace_id, subject_type, subject));
        CREATE TABLE IF NOT EXISTS team_permissions (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
            subject_type TEXT NOT NULL, subject TEXT NOT NULL, level TEXT NOT NULL, UNIQUE (user_id, subject_type, subject));
    """)


def load_grants(conn, user_id):
    """Permissions effectives d'un compte : entrées directes + éléments de ses espaces (rang = rôle dans l'espace)."""
    ensure(conn)
    out = [{'type': r[0], 'subject': r[1], 'rank': LEVEL_RANK.get(r[2], -1)} for r in
           conn.execute("SELECT subject_type, subject, level FROM team_permissions WHERE user_id = ?", (user_id,)).fetchall()]
    for r in conn.execute("SELECT i.subject_type, i.subject, m.role FROM workspace_members m JOIN workspace_items i ON i.workspace_id = m.workspace_id "
                          "WHERE m.user_id = ?", (user_id,)).fetchall():
        out.append({'type': r[0], 'subject': r[1], 'rank': min(RANK.get(r[2], 0), 2) if RANK.get(r[2], 0) else 0})
    return out


def team_role(conn, guest_id):
    try:
        row = conn.execute("SELECT team_role FROM users WHERE id = ? AND role = 'viewer'", (guest_id,)).fetchone()
    except Exception:
        return ''
    return (row[0] or '') if row else ''


def request_subjects(captured, body):
    subs = []
    if captured.get('printer'):
        subs.append(('printer', captured['printer']))
    if captured.get('project'):
        subs.append(('project', captured['project']))
    if isinstance(body, dict):
        if body.get('printer_id') not in (None, '') and not captured.get('printer'):
            subs.append(('printer', str(body['printer_id'])))
        pth = body.get('path') or body.get('file_path')
        if pth:
            subs.append(('folder', str(pth)))
        for p in (body.get('paths') or [])[:200] if isinstance(body.get('paths'), list) else []:
            subs.append(('folder', str(p)))
    return subs


def team_decision():
    """Appelé par `_viewer_guard` pour une écriture d'invité. Retourne None (non concerné : refus historique), True (autorisé)
    ou un message (refusé pour une raison propre à l'équipe)."""
    hit = match_rule(request.method, request.path)
    if not hit:
        return None
    conn = get_db()
    try:
        role = team_role(conn, session.get('viewer_id'))
        grants = load_grants(conn, session.get('viewer_id'))
        if not role and not grants:
            return None
    finally:
        conn.close()
    need_role, captured = hit
    body = request.get_json(silent=True) if request.is_json else None
    ok, why = decide(role, need_role, request_subjects(captured, body), grants)
    return True if ok else why


# ── routes (propriétaire) ──

def _owner_only():
    if session.get('role') == 'viewer' and not _demo_ok():
        return jsonify({'error': 'Réservé au compte propriétaire.', 'code': 'viewer_forbidden'}), 403
    return None


def _guest_ids(conn, owner):
    return {r[0] for r in conn.execute("SELECT id FROM users WHERE role = 'viewer' AND owner_id = ?", (owner,)).fetchall()}


def api_team():
    r = _owner_only()
    if r:
        return r
    uid = session['user_id']
    conn = get_db()
    try:
        ensure(conn)
        members = [dict(x) for x in conn.execute("SELECT id, username, COALESCE(team_role,'') AS team_role FROM users WHERE role='viewer' AND owner_id=? ORDER BY username COLLATE NOCASE", (uid,)).fetchall()]
        ws = []
        for w in conn.execute("SELECT id, name FROM workspaces WHERE owner_id = ? ORDER BY id", (uid,)).fetchall():
            ws.append({'id': w['id'], 'name': w['name'],
                       'members': [dict(x) for x in conn.execute("SELECT user_id, role FROM workspace_members WHERE workspace_id=?", (w['id'],)).fetchall()],
                       'items': [dict(x) for x in conn.execute("SELECT subject_type, subject FROM workspace_items WHERE workspace_id=?", (w['id'],)).fetchall()]})
        perms = [dict(x) for x in conn.execute("SELECT id, user_id, subject_type, subject, level FROM team_permissions WHERE owner_id=? ORDER BY id", (uid,)).fetchall()]
        return jsonify({'roles': list(ROLES), 'levels': list(LEVELS), 'subject_types': list(SUBJECT_TYPES), 'members': members, 'workspaces': ws, 'permissions': perms})
    finally:
        conn.close()


def api_team_set_role(guest_id):
    r = _owner_only()
    if r:
        return r
    role = str((request.get_json(silent=True) or {}).get('role') or '')
    if role and role not in ROLES:
        return jsonify({'error': 'Rôle inconnu.'}), 400
    conn = get_db()
    try:
        cur = conn.execute("UPDATE users SET team_role = ? WHERE id = ? AND role = 'viewer' AND owner_id = ?", (role, guest_id, session['user_id']))
        conn.commit()
        if not cur.rowcount:
            return jsonify({'error': 'Invité introuvable.'}), 404
        return jsonify({'ok': True, 'role': role})
    finally:
        conn.close()


def api_team_me():
    """Rôle et permissions du compte connecté (l'interface s'en sert pour griser les actions interdites)."""
    if session.get('role') != 'viewer':
        return jsonify({'role': 'owner', 'grants': []})
    conn = get_db()
    try:
        return jsonify({'role': team_role(conn, session.get('viewer_id')) or 'viewer', 'grants': load_grants(conn, session.get('viewer_id'))})
    finally:
        conn.close()


def _subject_ok(stype, subject):
    return stype in SUBJECT_TYPES and 0 < len(str(subject or '')) <= 500


def api_team_permission_set():
    r = _owner_only()
    if r:
        return r
    d = request.get_json(silent=True) or {}
    stype, subject, level = str(d.get('subject_type') or ''), str(d.get('subject') or '').strip(), str(d.get('level') or '')
    if not _subject_ok(stype, subject) or level not in LEVELS:
        return jsonify({'error': 'Permission invalide.'}), 400
    if stype == 'folder':
        subject = norm_dir(subject)
    conn = get_db()
    try:
        ensure(conn)
        try:
            gid = int(d.get('user_id'))
        except (TypeError, ValueError):
            return jsonify({'error': 'Invité manquant.'}), 400
        if gid not in _guest_ids(conn, session['user_id']):
            return jsonify({'error': 'Invité introuvable.'}), 404
        conn.execute("INSERT INTO team_permissions (owner_id, user_id, subject_type, subject, level) VALUES (?,?,?,?,?) "
                     "ON CONFLICT(user_id, subject_type, subject) DO UPDATE SET level = excluded.level", (session['user_id'], gid, stype, subject, level))
        conn.commit()
        return jsonify({'ok': True})
    finally:
        conn.close()


def api_team_permission_delete(pid):
    r = _owner_only()
    if r:
        return r
    conn = get_db()
    try:
        ensure(conn)
        cur = conn.execute("DELETE FROM team_permissions WHERE id = ? AND owner_id = ?", (pid, session['user_id']))
        conn.commit()
        return jsonify({'ok': True}) if cur.rowcount else (jsonify({'error': 'Introuvable.'}), 404)
    finally:
        conn.close()


def _ws_owned(conn, wid):
    return conn.execute("SELECT id FROM workspaces WHERE id = ? AND owner_id = ?", (wid, session['user_id'])).fetchone()


def api_workspace_create():
    r = _owner_only()
    if r:
        return r
    name = str((request.get_json(silent=True) or {}).get('name') or '').strip()[:60]
    if not name:
        return jsonify({'error': "Donnez un nom à l'espace."}), 400
    conn = get_db()
    try:
        ensure(conn)
        if conn.execute("SELECT COUNT(*) FROM workspaces WHERE owner_id = ?", (session['user_id'],)).fetchone()[0] >= MAX_WORKSPACES:
            return jsonify({'error': f'{MAX_WORKSPACES} espaces au maximum.'}), 400
        cur = conn.execute("INSERT INTO workspaces (owner_id, name, created_at) VALUES (?,?,strftime('%s','now'))", (session['user_id'], name))
        conn.commit()
        return jsonify({'ok': True, 'id': cur.lastrowid})
    finally:
        conn.close()


def api_workspace_delete(wid):
    r = _owner_only()
    if r:
        return r
    conn = get_db()
    try:
        ensure(conn)
        if not _ws_owned(conn, wid):
            return jsonify({'error': 'Espace introuvable.'}), 404
        for t in ('workspace_members', 'workspace_items'):
            conn.execute(f"DELETE FROM {t} WHERE workspace_id = ?", (wid,))
        conn.execute("DELETE FROM workspaces WHERE id = ?", (wid,))
        conn.commit()
        return jsonify({'ok': True})
    finally:
        conn.close()


def api_workspace_member_set(wid):
    r = _owner_only()
    if r:
        return r
    d = request.get_json(silent=True) or {}
    role = str(d.get('role') or '')
    if role not in ROLES:
        return jsonify({'error': 'Rôle inconnu.'}), 400
    conn = get_db()
    try:
        ensure(conn)
        if not _ws_owned(conn, wid):
            return jsonify({'error': 'Espace introuvable.'}), 404
        try:
            gid = int(d.get('user_id'))
        except (TypeError, ValueError):
            return jsonify({'error': 'Invité manquant.'}), 400
        if gid not in _guest_ids(conn, session['user_id']):
            return jsonify({'error': 'Invité introuvable.'}), 404
        conn.execute("INSERT INTO workspace_members (workspace_id, user_id, role) VALUES (?,?,?) ON CONFLICT(workspace_id, user_id) DO UPDATE SET role = excluded.role", (wid, gid, role))
        conn.commit()
        return jsonify({'ok': True})
    finally:
        conn.close()


def api_workspace_member_delete(wid, gid):
    r = _owner_only()
    if r:
        return r
    conn = get_db()
    try:
        ensure(conn)
        if not _ws_owned(conn, wid):
            return jsonify({'error': 'Espace introuvable.'}), 404
        conn.execute("DELETE FROM workspace_members WHERE workspace_id = ? AND user_id = ?", (wid, gid))
        conn.commit()
        return jsonify({'ok': True})
    finally:
        conn.close()


def api_workspace_item_set(wid):
    r = _owner_only()
    if r:
        return r
    d = request.get_json(silent=True) or {}
    stype, subject = str(d.get('subject_type') or ''), str(d.get('subject') or '').strip()
    if not _subject_ok(stype, subject):
        return jsonify({'error': 'Élément invalide.'}), 400
    if stype == 'folder':
        subject = norm_dir(subject)
    conn = get_db()
    try:
        ensure(conn)
        if not _ws_owned(conn, wid):
            return jsonify({'error': 'Espace introuvable.'}), 404
        conn.execute("INSERT OR IGNORE INTO workspace_items (workspace_id, subject_type, subject) VALUES (?,?,?)", (wid, stype, subject))
        conn.commit()
        return jsonify({'ok': True})
    finally:
        conn.close()


def api_workspace_item_delete(wid):
    r = _owner_only()
    if r:
        return r
    d = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        ensure(conn)
        if not _ws_owned(conn, wid):
            return jsonify({'error': 'Espace introuvable.'}), 404
        conn.execute("DELETE FROM workspace_items WHERE workspace_id = ? AND subject_type = ? AND subject = ?",
                     (wid, str(d.get('subject_type') or ''), norm_dir(d.get('subject')) if d.get('subject_type') == 'folder' else str(d.get('subject') or '')))
        conn.commit()
        return jsonify({'ok': True})
    finally:
        conn.close()


_DEMO_COMPUTE = ('/api/plate/arrange', '/api/organize/preview', '/api/model-diff')


def _demo_ok():
    """Démo publique (lecture seule, `IS_DEMO` posé par la surcouche de démo) : consultation (GET) et calculs sans écriture."""
    try:
        return bool(_MAIN.get('IS_DEMO')) and (request.method in ('GET', 'HEAD') or request.path in _DEMO_COMPUTE)
    except Exception:
        return False


_ROUTES = (
    ('/api/team', ['GET'], 'api_team', ('login_required', )),
    ('/api/team/me', ['GET'], 'api_team_me', ('login_required', )),
    ('/api/team/members/<int:guest_id>/role', ['PUT'], 'api_team_set_role', ('login_required', )),
    ('/api/team/permissions', ['POST'], 'api_team_permission_set', ('login_required', )),
    ('/api/team/permissions/<int:pid>', ['DELETE'], 'api_team_permission_delete', ('login_required', )),
    ('/api/team/workspaces', ['POST'], 'api_workspace_create', ('login_required', )),
    ('/api/team/workspaces/<int:wid>', ['DELETE'], 'api_workspace_delete', ('login_required', )),
    ('/api/team/workspaces/<int:wid>/members', ['POST'], 'api_workspace_member_set', ('login_required', )),
    ('/api/team/workspaces/<int:wid>/members/<int:gid>', ['DELETE'], 'api_workspace_member_delete', ('login_required', )),
    ('/api/team/workspaces/<int:wid>/items', ['POST'], 'api_workspace_item_set', ('login_required', )),
    ('/api/team/workspaces/<int:wid>/items', ['DELETE'], 'api_workspace_item_delete', ('login_required', )),
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
