"""Stellio — API publique, partie 1 (v1.1.7) : jetons d'accès, routes /api/v1 réduites, documentation OpenAPI, journal.

Principes
  · Un jeton = une clé longue (`stl_` + 40 caractères aléatoires) rattachée à un compte. Seule son empreinte SHA-256 est stockée :
    le jeton n'est montré qu'à sa création, jamais relisible ensuite. Droit « read » (GET) ou « write » (GET + écriture).
    Révocation immédiate ; un jeton révoqué reste dans la liste (traçabilité) mais n'ouvre plus rien.
  · Liste VOLONTAIREMENT réduite de routes : fichiers, imprimantes, état d'impression, tâches (commandes d'impression).
    Tout le reste de l'application reste réservé à la session de l'interface.
  · Journal des accès et des erreurs (table `api_log`, 2000 dernières lignes) ; limite de tentatives avec un mauvais jeton.
  · La description OpenAPI est générée depuis la même table de routes que celle qui sert à les enregistrer : elle ne peut pas
    se désynchroniser.

Module séparé de main.py (même schéma que print_traceability.py) : main.py appelle `public_api.init(globals())`.
Les fonctions pures (`make_token`, `hash_token`, `parse_bearer`, `perm_allows`, `build_openapi`) sont testées sans base.
"""
import hashlib
import json
import os
import secrets
import time
from functools import wraps

_REQUIRED = (
    '_is_path_within_sources',
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'parse_printer_config',
    'printer_hub',
    'request',
    'session',
)
_OPTIONAL = ('_read_cache_json_safe', 'CURRENT_VERSION')
_OVERRIDABLE = ('hashlib', 'json', 'os', 'secrets', 'time')

_MAIN = {}
_is_path_within_sources = None
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
parse_printer_config = None
printer_hub = None
request = None
session = None
_read_cache_json_safe = None
CURRENT_VERSION = ''

TOKEN_PREFIX = 'stl_'
PERMS = ('read', 'write')
RESOURCES = ('files', 'printers', 'tasks', 'materials', 'history', 'projects')   # portée d'un jeton ; liste vide = tout
RESOURCE_OF = {'v1_files': 'files', 'v1_printers': 'printers', 'v1_printer_status': 'printers', 'v1_tasks': 'tasks', 'v1_task': 'tasks',
               'v1_task_create': 'tasks', 'v1_task_update': 'tasks', 'v1_materials': 'materials', 'v1_history': 'history',
               'v1_projects': 'projects', 'v1_project': 'projects',
               'v1_material_create': 'materials', 'v1_material_update': 'materials', 'v1_project_create': 'projects', 'v1_project_update': 'projects'}
MAX_ACTIVE_TOKENS = 20
LOG_KEEP = 2000
FAIL_LIMIT = 20            # mauvais jetons par minute et par adresse avant 429
FILES_MAX = 500
TASK_STATUS = ('queued', 'printing', 'done', 'cancelled')
_SECRET_HINTS = ('token', 'secret', 'password', 'passwd', 'api_key', 'apikey', 'access_code', 'cookie', 'credential', 'private', 'code')
_fails = {}


# ── fonctions pures ───────────────────────────────────────────────────────

def make_token():
    """Nouveau jeton : (jeton complet, préfixe affichable)."""
    tok = TOKEN_PREFIX + secrets.token_hex(20)
    return tok, tok[:len(TOKEN_PREFIX) + 4]


def hash_token(token):
    return hashlib.sha256(str(token or '').encode('utf-8')).hexdigest()


def parse_bearer(header):
    """'Bearer stl_xxx' → 'stl_xxx' ; '' si l'en-tête est absent ou mal formé."""
    h = str(header or '').strip()
    if h[:7].lower() != 'bearer ':
        return ''
    t = h[7:].strip()
    return t if t.startswith(TOKEN_PREFIX) and len(t) >= len(TOKEN_PREFIX) + 16 else ''


def perm_allows(perm, method):
    """« read » n'autorise que la lecture ; « write » autorise tout."""
    if perm == 'write':
        return True
    return perm == 'read' and str(method).upper() in ('GET', 'HEAD')


def _clean(obj):
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items() if not any(h in str(k).lower() for h in _SECRET_HINTS)}
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    return obj


# ── description des routes publiques (source unique : enregistrement + OpenAPI) ──

def _P(name, where, typ, desc, required=False):
    return {'name': name, 'in': where, 'required': required, 'schema': {'type': typ}, 'description': desc}


PUBLIC_ROUTES = (
    # (règle Flask, méthode, fonction, droit, résumé, paramètres, schéma du corps)
    ('/api/v1/me', 'GET', 'v1_me', 'read', 'Identité et droit du jeton utilisé', (), None),
    ('/api/v1/files', 'GET', 'v1_files', 'read', 'Fichiers de la bibliothèque',
     (_P('q', 'query', 'string', 'Texte contenu dans le nom'), _P('type', 'query', 'string', 'Extension sans point (stl, 3mf, gcode…)'),
      _P('limit', 'query', 'integer', 'Nombre maximum (défaut 100, max 500)'), _P('offset', 'query', 'integer', 'Décalage')), None),
    ('/api/v1/printers', 'GET', 'v1_printers', 'read', 'Imprimantes', (), None),
    ('/api/v1/printers/{id}/status', 'GET', 'v1_printer_status', 'read', "État d'impression d'une imprimante",
     (_P('id', 'path', 'integer', "Identifiant de l'imprimante", True),), None),
    ('/api/v1/tasks', 'GET', 'v1_tasks', 'read', "Tâches (commandes d'impression)",
     (_P('status', 'query', 'string', 'queued, printing, done ou cancelled'),), None),
    ('/api/v1/tasks/{id}', 'GET', 'v1_task', 'read', 'Une tâche', (_P('id', 'path', 'integer', 'Identifiant', True),), None),
    ('/api/v1/tasks', 'POST', 'v1_task_create', 'write', 'Créer une tâche', (),
     {'part': 'string (obligatoire)', 'quantity': 'integer', 'client': 'string', 'due_date': 'YYYY-MM-DD', 'material': 'string',
      'printer_id': 'integer', 'est_hours': 'number (heures par pièce)'}),
    ('/api/v1/tasks/{id}', 'PATCH', 'v1_task_update', 'write', 'Mettre à jour une tâche',
     (_P('id', 'path', 'integer', 'Identifiant', True),),
     {'qty_done': 'integer', 'scrap': 'integer', 'status': 'queued|printing|done|cancelled', 'due_date': 'YYYY-MM-DD'}),
    ('/api/v1/materials', 'GET', 'v1_materials', 'read', 'Bobines de matière (reste et capacité)', (), None),
    ('/api/v1/materials', 'POST', 'v1_material_create', 'write', 'Ajouter une bobine', (),
     {'name': 'string (obligatoire)', 'material': 'string (PLA, PETG…)', 'color_hex': '#rrggbb', 'capacity_g': 'number', 'remaining_g': 'number'}),
    ('/api/v1/materials/{id}', 'PATCH', 'v1_material_update', 'write', 'Mettre à jour une bobine (reste, nom, couleur)',
     (_P('id', 'path', 'integer', 'Identifiant', True),), {'remaining_g': 'number', 'name': 'string', 'color_hex': '#rrggbb', 'capacity_g': 'number'}),
    ('/api/v1/projects', 'POST', 'v1_project_create', 'write', 'Créer un projet', (),
     {'name': 'string (obligatoire)', 'description': 'string', 'status': 'in_progress|done|paused'}),
    ('/api/v1/projects/{id}', 'PATCH', 'v1_project_update', 'write', 'Modifier un projet',
     (_P('id', 'path', 'integer', 'Identifiant', True),), {'name': 'string', 'description': 'string', 'status': 'in_progress|done|paused'}),
    ('/api/v1/history', 'GET', 'v1_history', 'read', "Historique d'impression",
     (_P('result', 'query', 'string', 'success, failed ou partial'), _P('printer_id', 'query', 'integer', 'Imprimante'),
      _P('limit', 'query', 'integer', 'Nombre maximum (défaut 100, max 500)')), None),
    ('/api/v1/projects', 'GET', 'v1_projects', 'read', 'Projets et avancement', (), None),
    ('/api/v1/projects/{id}', 'GET', 'v1_project', 'read', 'Un projet et ses pièces', (_P('id', 'path', 'integer', 'Identifiant', True),), None),
)


def build_openapi(version='', base=''):
    paths = {}
    for rule, method, fname, perm, summary, params, body in PUBLIC_ROUTES:
        op = {'operationId': fname, 'summary': summary, 'security': [{'bearer': []}],
              'x-permission': perm, 'parameters': list(params),
              'responses': {'200': {'description': 'OK'}, '401': {'description': 'Jeton absent, invalide ou révoqué'},
                            '403': {'description': 'Droit insuffisant'}, '429': {'description': 'Trop de tentatives'}}}
        if body:
            op['requestBody'] = {'required': True, 'content': {'application/json': {'schema': {
                'type': 'object', 'properties': {k: {'type': 'string', 'description': v} for k, v in body.items()}}}}}
        paths.setdefault(rule, {})[method.lower()] = op
    return {'openapi': '3.0.3',
            'info': {'title': 'Stellio — API publique', 'version': version or '1',
                     'description': "Jetons créés dans Paramètres › API. En-tête : Authorization: Bearer stl_…  "
                                    "Liste volontairement réduite : fichiers, imprimantes, état d'impression, tâches."},
            'servers': [{'url': base or '/'}], 'paths': paths,
            'components': {'securitySchemes': {'bearer': {'type': 'http', 'scheme': 'bearer'}}}}


# ── base ──────────────────────────────────────────────────────────────────

def _ensure_tables(conn=None):
    own = conn is None
    conn = conn or get_db()
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS api_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT NOT NULL, prefix TEXT NOT NULL,
            token_hash TEXT NOT NULL UNIQUE, perm TEXT NOT NULL DEFAULT 'read',
            created_at REAL, last_used_at REAL, revoked_at REAL, scopes TEXT NOT NULL DEFAULT '')""")
        if not any(r[1] == 'scopes' for r in conn.execute("PRAGMA table_info(api_tokens)").fetchall()):
            conn.execute("ALTER TABLE api_tokens ADD COLUMN scopes TEXT NOT NULL DEFAULT ''")
        conn.execute("""CREATE TABLE IF NOT EXISTS api_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, token_id INTEGER, user_id INTEGER, method TEXT, path TEXT,
            status INTEGER, ms INTEGER, ip TEXT, error TEXT)""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_api_log_ts ON api_log(ts)")
        conn.commit()
    finally:
        if own:
            conn.close()


def _log(conn, token_id, uid, status, started, error=''):
    try:
        conn.execute("INSERT INTO api_log (ts, token_id, user_id, method, path, status, ms, ip, error) VALUES (?,?,?,?,?,?,?,?,?)",
                     (time.time(), token_id, uid, request.method, (request.path or '')[:200], int(status),
                      int((time.time() - started) * 1000), (request.remote_addr or '')[:64], (error or '')[:200]))
        conn.execute("DELETE FROM api_log WHERE id <= (SELECT MAX(id) FROM api_log) - ?", (LOG_KEEP,))
        conn.commit()
    except Exception as e:
        try:
            app_logger.debug(f"[API] journal non écrit : {e}")
        except Exception:
            pass


def _too_many_fails(ip):
    now = time.time()
    lst = [t for t in _fails.get(ip, []) if now - t < 60]
    _fails[ip] = lst
    return len(lst) >= FAIL_LIMIT


def parse_scopes(raw):
    """'files,tasks' → ('files', 'tasks') ; valeurs inconnues écartées ; vide = toutes les ressources."""
    return tuple(x for x in dict.fromkeys(str(raw or '').replace(' ', '').split(',')) if x in RESOURCES)


def scope_allows(scopes, resource):
    return not scopes or resource is None or resource in scopes


def token_perm(need, resource=None):
    """Décorateur des routes /api/v1 : vérifie le jeton, le droit, journalise. Place `g_token` dans `request.environ`."""
    def deco(view):
        @wraps(view)
        def wrapped(*a, **kw):
            started = time.time()
            ip = request.remote_addr or ''
            conn = get_db()
            try:
                _ensure_tables(conn)
                if _too_many_fails(ip):
                    _log(conn, None, None, 429, started, 'trop de tentatives')
                    return jsonify({'error': 'Trop de tentatives avec un mauvais jeton, réessayez dans une minute.', 'code': 'rate_limited'}), 429
                tok = parse_bearer(request.headers.get('Authorization', ''))
                row = conn.execute("SELECT * FROM api_tokens WHERE token_hash = ?", (hash_token(tok),)).fetchone() if tok else None
                if not row or row['revoked_at']:
                    _fails.setdefault(ip, []).append(time.time())
                    _log(conn, row['id'] if row else None, row['user_id'] if row else None, 401, started,
                         'jeton révoqué' if row else ('jeton absent' if not tok else 'jeton inconnu'))
                    return jsonify({'error': 'Jeton absent, invalide ou révoqué.', 'code': 'unauthorized'}), 401
                if need == 'write' and not perm_allows(row['perm'], 'POST'):
                    _log(conn, row['id'], row['user_id'], 403, started, 'droit lecture seule')
                    return jsonify({'error': "Ce jeton est en lecture seule.", 'code': 'forbidden'}), 403
                if not scope_allows(parse_scopes(dict(row).get('scopes')), resource):
                    _log(conn, row['id'], row['user_id'], 403, started, f"portée du jeton : {resource} non autorisé")
                    return jsonify({'error': f"Ce jeton n'a pas accès à « {resource} ».", 'code': 'forbidden_scope'}), 403
                conn.execute("UPDATE api_tokens SET last_used_at = ? WHERE id = ?", (time.time(), row['id']))
                conn.commit()
                request.environ['stellio.api_token'] = dict(row)
                try:
                    resp = view(*a, **kw)
                except Exception as e:
                    _log(conn, row['id'], row['user_id'], 500, started, f"{type(e).__name__}: {e}")
                    try:
                        app_logger.warning(f"[API] {request.path} : {e}")
                    except Exception:
                        pass
                    return jsonify({'error': 'Erreur interne.', 'code': 'server_error'}), 500
                code = resp[1] if isinstance(resp, tuple) else getattr(resp, 'status_code', 200)
                err = ''
                if code >= 400:
                    try:
                        body = resp[0] if isinstance(resp, tuple) else resp
                        err = (body.get_json(silent=True) or {}).get('error', '')
                    except Exception:
                        pass
                _log(conn, row['id'], row['user_id'], code, started, err)
                return resp
            finally:
                conn.close()
        return wrapped
    return deco


def _tok():
    return request.environ['stellio.api_token']


# ── gestion des jetons (session de l'interface) ────────────────────────────

def _no_viewer():
    if session.get('role') == 'viewer' and not _demo_ok():
        return jsonify({'error': 'Réservé au compte propriétaire.'}), 403
    return None


def api_tokens_list():
    r = _no_viewer()
    if r:
        return r
    conn = get_db()
    try:
        _ensure_tables(conn)
        rows = conn.execute("SELECT id, name, prefix, perm, created_at, last_used_at, revoked_at, scopes FROM api_tokens WHERE user_id = ? ORDER BY id DESC",
                            (session['user_id'],)).fetchall()
        return jsonify({'tokens': [dict(x, scopes=list(parse_scopes(x['scopes']))) for x in rows], 'max': MAX_ACTIVE_TOKENS, 'resources': list(RESOURCES)})
    finally:
        conn.close()


def api_tokens_create():
    r = _no_viewer()
    if r:
        return r
    data = request.get_json(silent=True) or {}
    name = str(data.get('name') or '').strip()[:60]
    perm = str(data.get('perm') or 'read')
    raw_scopes = data.get('scopes') or []
    if isinstance(raw_scopes, str):
        raw_scopes = raw_scopes.split(',')
    scopes = parse_scopes(','.join(str(x) for x in raw_scopes))
    if len(scopes) != len([x for x in dict.fromkeys(str(x).strip() for x in raw_scopes) if x]):
        return jsonify({'error': 'Ressource inconnue dans la portée du jeton.'}), 400
    if not name:
        return jsonify({'error': 'Donnez un nom au jeton.'}), 400
    if perm not in PERMS:
        return jsonify({'error': 'Droit inconnu.'}), 400
    conn = get_db()
    try:
        _ensure_tables(conn)
        n = conn.execute("SELECT COUNT(*) FROM api_tokens WHERE user_id = ? AND revoked_at IS NULL", (session['user_id'],)).fetchone()[0]
        if n >= MAX_ACTIVE_TOKENS:
            return jsonify({'error': f'{MAX_ACTIVE_TOKENS} jetons actifs au maximum : révoquez-en un.'}), 400
        tok, prefix = make_token()
        cur = conn.execute("INSERT INTO api_tokens (user_id, name, prefix, token_hash, perm, created_at, scopes) VALUES (?,?,?,?,?,?,?)",
                           (session['user_id'], name, prefix, hash_token(tok), perm, time.time(), ','.join(scopes)))
        conn.commit()
        return jsonify({'id': cur.lastrowid, 'name': name, 'perm': perm, 'scopes': list(scopes), 'prefix': prefix, 'token': tok})   # seule fois où il est visible
    finally:
        conn.close()


def api_tokens_revoke(tid):
    r = _no_viewer()
    if r:
        return r
    conn = get_db()
    try:
        _ensure_tables(conn)
        cur = conn.execute("UPDATE api_tokens SET revoked_at = ? WHERE id = ? AND user_id = ? AND revoked_at IS NULL",
                           (time.time(), tid, session['user_id']))
        conn.commit()
        if not cur.rowcount:
            return jsonify({'error': 'Jeton introuvable ou déjà révoqué.'}), 404
        return jsonify({'ok': True})
    finally:
        conn.close()


def api_tokens_log():
    r = _no_viewer()
    if r:
        return r
    try:
        limit = max(1, min(int(request.args.get('limit', 100)), 500))
    except ValueError:
        limit = 100
    only_err = request.args.get('errors') in ('1', 'true')
    conn = get_db()
    try:
        _ensure_tables(conn)
        q = ("SELECT l.id, l.ts, l.token_id, t.name AS token_name, l.method, l.path, l.status, l.ms, l.ip, l.error "
             "FROM api_log l LEFT JOIN api_tokens t ON t.id = l.token_id WHERE (l.user_id = ? OR l.user_id IS NULL)")
        if only_err:
            q += " AND l.status >= 400"
        rows = conn.execute(q + " ORDER BY l.id DESC LIMIT ?", (session['user_id'], limit)).fetchall()
        return jsonify({'log': [dict(x) for x in rows]})
    finally:
        conn.close()


# ── routes publiques ──────────────────────────────────────────────────────

def v1_openapi():
    base = request.host_url.rstrip('/')
    return jsonify(build_openapi(CURRENT_VERSION, base))



_WEBHOOK_DOC = """<h2 id="webhooks">Webhooks</h2>
<p>Paramètres › Webhooks : Stellio envoie un POST JSON à votre URL pour <code>print.finished</code>, <code>print.failed</code>, <code>order.late</code>
et <code>printer.overload</code>. Chaque envoi porte <code>X-Stellio-Signature: t=&lt;horodatage&gt;,v1=&lt;hex&gt;</code> :
HMAC-SHA256 du texte <code>&lt;horodatage&gt;.&lt;corps brut&gt;</code> avec votre secret <code>whsec_…</code>. Vérifiez la signature
<b>et</b> que l'horodatage date de moins de 5 minutes. Répondez par un code 2xx ; sinon Stellio réessaie (30 s, 2 min, 10 min, 1 h, 6 h).</p>
<pre>import hmac, hashlib, time
def verifie(secret, en_tete, corps: bytes):
    t, v1 = (p.split('=', 1)[1] for p in en_tete.split(','))
    if abs(time.time() - int(t)) &gt; 300: return False
    attendu = hmac.new(secret.encode(), t.encode() + b'.' + corps, hashlib.sha256).hexdigest()
    return hmac.compare_digest(attendu, v1)</pre>"""


def v1_docs():
    spec = build_openapi(CURRENT_VERSION)
    rows = []
    for rule, ops in spec['paths'].items():
        for m, op in ops.items():
            rows.append(f"<tr><td><b>{m.upper()}</b></td><td><code>{rule}</code></td><td>{op['summary']}</td><td>{op['x-permission']}</td></tr>")
    html = ("<!doctype html><meta charset=utf-8><title>Stellio API</title><style>body{font:15px system-ui;max-width:860px;margin:2rem auto;padding:0 1rem}"
            "table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #8884;padding:6px;text-align:left}code,pre{background:#8882;padding:1px 4px;border-radius:4px}pre{padding:10px;overflow:auto}</style>"
            "<h1>Stellio — API publique</h1><p>En-tête : <code>Authorization: Bearer stl_…</code> — jetons créés dans Paramètres › API. "
            "Description complète : <a href=\"/api/v1/openapi.json\">openapi.json</a>.</p>"
            "<table><tr><th>Méthode</th><th>Route</th><th>Rôle</th><th>Droit</th></tr>" + ''.join(rows) + "</table>" + _WEBHOOK_DOC)
    return app.response_class(html, mimetype='text/html')


def v1_me():
    t = _tok()
    return jsonify({'token': t['name'], 'prefix': t['prefix'], 'permission': t['perm'], 'scopes': list(parse_scopes(t.get('scopes'))) or list(RESOURCES),
                    'version': CURRENT_VERSION})


def _int_arg(name, default, lo, hi):
    try:
        return max(lo, min(int(request.args.get(name, default)), hi))
    except (TypeError, ValueError):
        return default


def v1_files():
    uid = _tok()['user_id']
    q = (request.args.get('q') or '').strip().lower()
    typ = (request.args.get('type') or '').strip().lower().lstrip('.')
    limit = _int_arg('limit', 100, 1, FILES_MAX)
    offset = _int_arg('offset', 0, 0, 10 ** 7)
    data = _read_cache_json_safe() if _read_cache_json_safe else None
    files = (data or {}).get('files', [])
    files = sorted(files, key=lambda f: f.get('mtime') or 0, reverse=True)
    out, skipped = [], 0
    for f in files:
        name = f.get('name') or os.path.basename(f.get('path', ''))
        if q and q not in name.lower():
            continue
        if typ and (f.get('type') or '').lower() != typ and (f.get('ext') or '').lower().lstrip('.') != typ:
            continue
        if not _is_path_within_sources(f.get('path', ''), uid):
            continue
        if skipped < offset:
            skipped += 1
            continue
        out.append({'name': name, 'path': f.get('path'), 'size': f.get('size'), 'type': f.get('type'), 'modified': f.get('mtime')})
        if len(out) >= limit:
            break
    return jsonify({'files': out, 'count': len(out), 'offset': offset})


def _printer_public(p):
    d = parse_printer_config(p)
    return {'id': d.get('id'), 'name': d.get('name'), 'type': d.get('type'), 'model': d.get('model') or d.get('brand'),
            'connected': bool(d.get('is_connected')), 'total_print_hours': d.get('total_print_hours')}


def v1_printers():
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM printers WHERE user_id = ? ORDER BY id", (_tok()['user_id'],)).fetchall()
    finally:
        conn.close()
    return jsonify({'printers': [_printer_public(r) for r in rows]})


def v1_printer_status(pid):
    conn = get_db()
    try:
        p = conn.execute("SELECT * FROM printers WHERE id = ? AND user_id = ?", (pid, _tok()['user_id'])).fetchone()
    finally:
        conn.close()
    if not p:
        return jsonify({'error': 'Imprimante introuvable.', 'code': 'not_found'}), 404
    status = printer_hub.get_status(parse_printer_config(p)) or {}
    return jsonify({'printer_id': pid, 'name': p['name'], 'state': _clean(status)})


_TASK_COLS = ('id', 'client', 'part', 'quantity', 'qty_done', 'scrap', 'material', 'printer_id', 'due_date', 'status', 'est_hours', 'created_at', 'done_at')


def _task_row(r):
    return {k: r[k] for k in _TASK_COLS if k in r.keys()}


def v1_tasks():
    st = (request.args.get('status') or '').strip()
    conn = get_db()
    try:
        if st and st not in TASK_STATUS:
            return jsonify({'error': 'Statut inconnu.', 'code': 'bad_request'}), 400
        sql, args = "SELECT * FROM print_jobs WHERE user_id = ?", [_tok()['user_id']]
        if st:
            sql += " AND status = ?"
            args.append(st)
        rows = conn.execute(sql + " ORDER BY id DESC LIMIT 500", args).fetchall()
        return jsonify({'tasks': [_task_row(r) for r in rows]})
    finally:
        conn.close()


def v1_task(tid):
    conn = get_db()
    try:
        r = conn.execute("SELECT * FROM print_jobs WHERE id = ? AND user_id = ?", (tid, _tok()['user_id'])).fetchone()
        if not r:
            return jsonify({'error': 'Tâche introuvable.', 'code': 'not_found'}), 404
        return jsonify(_task_row(r))
    finally:
        conn.close()


def v1_materials():
    conn = get_db()
    try:
        rows = conn.execute("SELECT id, name, material, color_hex, remaining_g, capacity_g, source_label FROM manual_filament_spools WHERE user_id = ? ORDER BY id",
                            (_tok()['user_id'],)).fetchall()
        return jsonify({'materials': [dict(r) for r in rows]})
    finally:
        conn.close()


_HISTORY_COLS = ('id', 'file_name', 'sent_at', 'result', 'printer_id', 'filament_material', 'slicer', 'estimated_seconds', 'actual_seconds',
                 'total_cost', 'nozzle_temp', 'bed_temp', 'slicer_version')


def v1_history():
    res = (request.args.get('result') or '').strip()
    if res and res not in ('success', 'failed', 'partial'):
        return jsonify({'error': 'Résultat inconnu.', 'code': 'bad_request'}), 400
    limit = _int_arg('limit', 100, 1, FILES_MAX)
    pid = _int_arg('printer_id', 0, 0, 10 ** 9)
    conn = get_db()
    try:
        have = {r[1] for r in conn.execute("PRAGMA table_info(print_history)").fetchall()}
        cols = [c for c in _HISTORY_COLS if c in have]
        sql, args = f"SELECT {', '.join(cols)} FROM print_history WHERE user_id = ?", [_tok()['user_id']]
        if res:
            sql += " AND result = ?"
            args.append(res)
        if pid:
            sql += " AND printer_id = ?"
            args.append(pid)
        rows = conn.execute(sql + " ORDER BY id DESC LIMIT ?", args + [limit]).fetchall()
        return jsonify({'history': [dict(r) for r in rows], 'count': len(rows)})
    finally:
        conn.close()


def v1_projects():
    conn = get_db()
    try:
        rows = conn.execute("SELECT p.id, p.name, p.description, p.status, p.created_at, p.updated_at, "
                            "COALESCE(SUM(f.quantity_needed), 0) AS needed, COALESCE(SUM(f.quantity_printed), 0) AS printed "
                            "FROM projects p LEFT JOIN project_files f ON f.project_id = p.id WHERE p.user_id = ? GROUP BY p.id ORDER BY p.id DESC",
                            (_tok()['user_id'],)).fetchall()
        return jsonify({'projects': [dict(r) for r in rows]})
    finally:
        conn.close()


def v1_project(tid):
    conn = get_db()
    try:
        p = conn.execute("SELECT id, name, description, status, created_at, updated_at FROM projects WHERE id = ? AND user_id = ?",
                         (tid, _tok()['user_id'])).fetchone()
        if not p:
            return jsonify({'error': 'Projet introuvable.', 'code': 'not_found'}), 404
        files = conn.execute("SELECT file_path, quantity_needed, quantity_printed, notes FROM project_files WHERE project_id = ? ORDER BY position, file_path",
                             (tid,)).fetchall()
        out = dict(p)
        out['files'] = [dict(f, name=os.path.basename(f['file_path'])) for f in files]
        return jsonify(out)
    finally:
        conn.close()


def _int(v, lo, hi, default=None):
    try:
        n = int(v)
    except (TypeError, ValueError):
        return default
    return max(lo, min(n, hi))


def v1_task_create():
    d = request.get_json(silent=True) or {}
    part = str(d.get('part') or '').strip()[:120]
    if not part:
        return jsonify({'error': 'Le champ « part » est obligatoire.', 'code': 'bad_request'}), 400
    qty = _int(d.get('quantity'), 1, 100000, 1)
    try:
        est = max(0.0, min(float(d.get('est_hours') or 0), 10000.0))
    except (TypeError, ValueError):
        est = 0.0
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO print_jobs (user_id, quote_id, client, part, quantity, qty_done, material, printer_id, due_date, status, notes, created_at, scrap, est_hours) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (_tok()['user_id'], 0, str(d.get('client') or '')[:120], part, qty, 0, str(d.get('material') or '')[:60],
             _int(d.get('printer_id'), 1, 10 ** 9, None), str(d.get('due_date') or '')[:10], 'queued', 'API',
             time.strftime('%Y-%m-%d %H:%M:%S'), 0, est))
        conn.commit()
        r = conn.execute("SELECT * FROM print_jobs WHERE id = ?", (cur.lastrowid,)).fetchone()
        return jsonify(_task_row(r)), 201
    finally:
        conn.close()


def v1_task_update(tid):
    d = request.get_json(silent=True) or {}
    sets, args = [], []
    if 'qty_done' in d:
        sets.append('qty_done = ?'); args.append(_int(d['qty_done'], 0, 100000, 0))
    if 'scrap' in d:
        sets.append('scrap = ?'); args.append(_int(d['scrap'], 0, 100000, 0))
    if 'status' in d:
        if d['status'] not in TASK_STATUS:
            return jsonify({'error': 'Statut inconnu.', 'code': 'bad_request'}), 400
        sets.append('status = ?'); args.append(d['status'])
        if d['status'] == 'done':
            sets.append('done_at = ?'); args.append(time.strftime('%Y-%m-%d %H:%M:%S'))
    if 'due_date' in d:
        sets.append('due_date = ?'); args.append(str(d['due_date'] or '')[:10])
    if not sets:
        return jsonify({'error': 'Rien à modifier.', 'code': 'bad_request'}), 400
    conn = get_db()
    try:
        cur = conn.execute("UPDATE print_jobs SET " + ', '.join(sets) + " WHERE id = ? AND user_id = ?", args + [tid, _tok()['user_id']])
        conn.commit()
        if not cur.rowcount:
            return jsonify({'error': 'Tâche introuvable.', 'code': 'not_found'}), 404
        r = conn.execute("SELECT * FROM print_jobs WHERE id = ?", (tid,)).fetchone()
        return jsonify(_task_row(r))
    finally:
        conn.close()


_HEX = __import__('re').compile(r'^#[0-9a-fA-F]{6}$')
PROJECT_STATUS = ('in_progress', 'done', 'paused')


def _num(v, lo, hi):
    try:
        n = float(v)
    except (TypeError, ValueError):
        return None
    if n != n:
        return None
    return max(lo, min(n, hi))


def v1_material_create():
    d = request.get_json(silent=True) or {}
    name = str(d.get('name') or '').strip()[:80]
    if not name:
        return jsonify({'error': 'Le champ « name » est obligatoire.', 'code': 'bad_request'}), 400
    color = str(d.get('color_hex') or '#888888')
    if not _HEX.match(color):
        return jsonify({'error': 'color_hex doit être de la forme #rrggbb.', 'code': 'bad_request'}), 400
    cap = _num(d.get('capacity_g', 1000), 1, 100000)
    rem = _num(d.get('remaining_g', cap), 0, 100000)
    if cap is None or rem is None:
        return jsonify({'error': 'Poids invalide.', 'code': 'bad_request'}), 400
    conn = get_db()
    try:
        cur = conn.execute("INSERT INTO manual_filament_spools (user_id, name, material, color_hex, remaining_g, capacity_g, source_label) VALUES (?,?,?,?,?,?,?)",
                           (_tok()['user_id'], name, str(d.get('material') or '')[:40], color, min(rem, max(cap, rem)), cap, 'API'))
        conn.commit()
        r = conn.execute("SELECT id, name, material, color_hex, remaining_g, capacity_g, source_label FROM manual_filament_spools WHERE id = ?", (cur.lastrowid,)).fetchone()
        return jsonify(dict(r)), 201
    finally:
        conn.close()


def v1_material_update(tid):
    d = request.get_json(silent=True) or {}
    sets, args = [], []
    if 'remaining_g' in d:
        n = _num(d['remaining_g'], 0, 100000)
        if n is None:
            return jsonify({'error': 'remaining_g invalide.', 'code': 'bad_request'}), 400
        sets.append('remaining_g = ?'); args.append(n)
    if 'capacity_g' in d:
        n = _num(d['capacity_g'], 1, 100000)
        if n is None:
            return jsonify({'error': 'capacity_g invalide.', 'code': 'bad_request'}), 400
        sets.append('capacity_g = ?'); args.append(n)
    if 'name' in d:
        nm = str(d['name'] or '').strip()[:80]
        if not nm:
            return jsonify({'error': 'Nom vide.', 'code': 'bad_request'}), 400
        sets.append('name = ?'); args.append(nm)
    if 'color_hex' in d:
        if not _HEX.match(str(d['color_hex'])):
            return jsonify({'error': 'color_hex doit être de la forme #rrggbb.', 'code': 'bad_request'}), 400
        sets.append('color_hex = ?'); args.append(d['color_hex'])
    if not sets:
        return jsonify({'error': 'Rien à modifier.', 'code': 'bad_request'}), 400
    conn = get_db()
    try:
        cur = conn.execute("UPDATE manual_filament_spools SET " + ', '.join(sets) + " WHERE id = ? AND user_id = ?", args + [tid, _tok()['user_id']])
        conn.commit()
        if not cur.rowcount:
            return jsonify({'error': 'Bobine introuvable.', 'code': 'not_found'}), 404
        r = conn.execute("SELECT id, name, material, color_hex, remaining_g, capacity_g, source_label FROM manual_filament_spools WHERE id = ?", (tid,)).fetchone()
        return jsonify(dict(r))
    finally:
        conn.close()


def v1_project_create():
    d = request.get_json(silent=True) or {}
    name = str(d.get('name') or '').strip()[:120]
    if not name:
        return jsonify({'error': 'Le champ « name » est obligatoire.', 'code': 'bad_request'}), 400
    st = d.get('status') or 'in_progress'
    if st not in PROJECT_STATUS:
        return jsonify({'error': 'Statut inconnu.', 'code': 'bad_request'}), 400
    conn = get_db()
    try:
        cur = conn.execute("INSERT INTO projects (user_id, name, description, status) VALUES (?,?,?,?)",
                           (_tok()['user_id'], name, str(d.get('description') or '')[:2000], st))
        conn.commit()
        r = conn.execute("SELECT id, name, description, status, created_at, updated_at FROM projects WHERE id = ?", (cur.lastrowid,)).fetchone()
        return jsonify(dict(r)), 201
    finally:
        conn.close()


def v1_project_update(tid):
    d = request.get_json(silent=True) or {}
    sets, args = [], []
    if 'name' in d:
        nm = str(d['name'] or '').strip()[:120]
        if not nm:
            return jsonify({'error': 'Nom vide.', 'code': 'bad_request'}), 400
        sets.append('name = ?'); args.append(nm)
    if 'description' in d:
        sets.append('description = ?'); args.append(str(d['description'] or '')[:2000])
    if 'status' in d:
        if d['status'] not in PROJECT_STATUS:
            return jsonify({'error': 'Statut inconnu.', 'code': 'bad_request'}), 400
        sets.append('status = ?'); args.append(d['status'])
    if not sets:
        return jsonify({'error': 'Rien à modifier.', 'code': 'bad_request'}), 400
    sets.append("updated_at = CURRENT_TIMESTAMP")
    conn = get_db()
    try:
        cur = conn.execute("UPDATE projects SET " + ', '.join(sets) + " WHERE id = ? AND user_id = ?", args + [tid, _tok()['user_id']])
        conn.commit()
        if not cur.rowcount:
            return jsonify({'error': 'Projet introuvable.', 'code': 'not_found'}), 404
        r = conn.execute("SELECT id, name, description, status, created_at, updated_at FROM projects WHERE id = ?", (tid,)).fetchone()
        return jsonify(dict(r))
    finally:
        conn.close()


# ── enregistrement ────────────────────────────────────────────────────────

_DEMO_COMPUTE = ('/api/plate/arrange', '/api/organize/preview', '/api/model-diff')


def _demo_ok():
    """Démo publique (lecture seule, `IS_DEMO` posé par la surcouche de démo) : consultation (GET) et calculs sans écriture."""
    try:
        return bool(_MAIN.get('IS_DEMO')) and (request.method in ('GET', 'HEAD') or request.path in _DEMO_COMPUTE)
    except Exception:
        return False


_ROUTES = (
    ('/api/tokens', ['GET'], 'api_tokens_list', ('login_required', )),
    ('/api/tokens', ['POST'], 'api_tokens_create', ('login_required', )),
    ('/api/tokens/<int:tid>', ['DELETE'], 'api_tokens_revoke', ('login_required', )),
    ('/api/tokens/log', ['GET'], 'api_tokens_log', ('login_required', )),
    ('/api/v1/openapi.json', ['GET'], 'v1_openapi', ()),
    ('/api/v1/docs', ['GET'], 'v1_docs', ()),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"public_api.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if routes:
        try:
            _ensure_tables()
        except Exception as e:
            try:
                app_logger.warning(f"[API] Tables non préparées : {e}")
            except Exception:
                pass
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
        for rule, method, fname, perm, _s, _p, _b in PUBLIC_ROUTES:
            flask_rule = rule.replace('{id}', '<int:%s>' % ('pid' if 'printers' in rule else 'tid'))
            ep = fname
            view = token_perm(perm, RESOURCE_OF.get(fname))(g[fname])
            g['app'].add_url_rule(flask_rule, endpoint=ep, view_func=view, methods=[method])
    return {}
