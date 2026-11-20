"""Stellio — synchronisation de bibliothèques entre deux instances Stellio (1.1.7, édition serveur).

Deux dossiers (un local, un sur l'instance appairée) sont comparés fichier par fichier avec l'état du DERNIER accord (`sync_base`) : c'est ce qui permet de
distinguer « modifié ici », « modifié là-bas » et « modifié des deux côtés » (conflit), au lieu de deviner avec les seules dates.
Règles de sécurité : AUCUNE suppression n'est jamais propagée (un fichier disparu d'un côté est seulement signalé) ; jamais d'écrasement silencieux : en
cas de conflit, la version perdante est conservée à côté sous « nom (conflit …).ext » ; tout est d'abord un PLAN (lecture seule), l'application est une
seconde étape confirmée qui REFAIT le plan à neuf ; les écritures passent par un fichier temporaire vérifié (empreinte) puis un remplacement atomique ;
les chemins sont validés (pas de « .. », pas de chemin absolu, dossiers des sources uniquement) ; le dossier distant est borné par ses propres sources.
Sens : `pull` (le distant alimente le local — le plus prudent), `push`, `both`. Stratégie de conflit : `newer` (le plus récent gagne, l'autre est gardé),
`keep_both` (rien n'est écrasé : la version distante est copiée à côté), `skip` (signalé seulement).
Empreintes : SHA-256 jusqu'à 64 Mo ; au-delà, taille + date (non vérifiable : signalé). Réservé à l'édition serveur, des DEUX côtés.
"""
import datetime
import hashlib
import json
import os
import shutil
import time

_REQUIRED = (
    '_get_primary_user_id',
    '_is_path_within_sources',
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'require_peer_key',
    'session',
)
_OPTIONAL = ('IS_SERVER_EDITION', 'requests', 'send_file')
_OVERRIDABLE = ('os', 'time')

_MAIN = {}
_get_primary_user_id = None
_is_path_within_sources = None
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
require_peer_key = None
session = None
IS_SERVER_EDITION = None
requests = None
send_file = None

DIRECTIONS = ('pull', 'push', 'both')
STRATEGIES = ('newer', 'keep_both', 'skip')
HASH_MAX = 64 * 1024 * 1024
MAX_FILES = 20000
MAX_FILE = 2 * 1024 * 1024 * 1024
PLAN_ITEMS = 500
TMP = '.stellio-sync-tmp'


def safe_rel(rel):
    """Chemin relatif propre (séparateurs /) ou ValueError."""
    r = str(rel or '').replace('\\', '/')
    if r.startswith('/') or r.endswith('/'):
        raise ValueError('Chemin refusé.')
    parts = r.split('/')
    if not r or any(p in ('', '.', '..') or p.startswith(TMP) for p in parts) or ':' in parts[0] or r.startswith('/'):
        raise ValueError('Chemin refusé.')
    return r


def safe_join(root, rel):
    rel = safe_rel(rel)
    base = os.path.realpath(root)
    p = os.path.realpath(os.path.join(base, *rel.split('/')))
    if not p.startswith(base + os.sep):
        raise ValueError('Chemin hors du dossier.')
    return p


def file_sig(path, size=None, mtime=None):
    size = os.path.getsize(path) if size is None else size
    mtime = os.path.getmtime(path) if mtime is None else mtime
    if size <= HASH_MAX:
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(1 << 20), b''):
                h.update(chunk)
        return 'h:' + h.hexdigest()
    return f'm:{size}:{int(mtime)}'


def local_manifest(root, cache=None):
    """{rel: {size, mtime, sig}} — fichiers visibles, sans liens symboliques ni dossiers cachés. cache : dict {(rel,size,mtime): sig} réutilisable."""
    out = {}
    base = os.path.realpath(root)
    for d, dirs, files in os.walk(base):
        dirs[:] = [x for x in dirs if not x.startswith('.') and not os.path.islink(os.path.join(d, x))]
        for fn in files:
            if fn.startswith('.'):
                continue
            p = os.path.join(d, fn)
            if os.path.islink(p):
                continue
            try:
                st = os.stat(p)
            except OSError:
                continue
            if st.st_size > MAX_FILE:
                continue
            rel = os.path.relpath(p, base).replace(os.sep, '/')
            key = (rel, st.st_size, int(st.st_mtime))
            sig = cache.get(key) if cache is not None else None
            if sig is None:
                sig = file_sig(p, st.st_size, st.st_mtime)
                if cache is not None:
                    cache[key] = sig
            out[rel] = {'size': st.st_size, 'mtime': st.st_mtime, 'sig': sig}
            if len(out) >= MAX_FILES:
                return out
    return out


def diff3(local, remote, base):
    """Plan à trois voies. local / remote : {rel: {size, mtime, sig}} ; base : {rel: sig} du dernier accord.
    Retourne [{'rel', 'op', 'detail'}] ; op ∈ same, pull, push, conflict, only_local_deleted_remote, only_remote_deleted_local."""
    plan = []
    for rel in sorted(set(local) | set(remote)):
        l, r, b = local.get(rel), remote.get(rel), base.get(rel)
        if l and r:
            if l['sig'] == r['sig']:
                plan.append({'rel': rel, 'op': 'same'})
            elif b == l['sig']:
                plan.append({'rel': rel, 'op': 'pull', 'detail': 'modifié sur le distant'})
            elif b == r['sig']:
                plan.append({'rel': rel, 'op': 'push', 'detail': 'modifié en local'})
            else:
                plan.append({'rel': rel, 'op': 'conflict', 'detail': 'modifié des deux côtés' if b else 'présent des deux côtés, contenus différents'})
        elif l:
            plan.append({'rel': rel, 'op': 'only_local_deleted_remote' if b else 'push', 'detail': 'supprimé sur le distant (non propagé)' if b else 'nouveau en local'})
        else:
            plan.append({'rel': rel, 'op': 'only_remote_deleted_local' if b else 'pull', 'detail': 'supprimé en local (non propagé)' if b else 'nouveau sur le distant'})
    return plan


def resolve(plan, local, remote, direction, strategy):
    """Transforme le plan en actions concrètes selon le sens et la stratégie. Retourne [{'rel','action','detail'}] ;
    action ∈ pull, push, conflict_copy_remote (copie la version distante à côté en local), conflict_local_wins, conflict_remote_wins, skip, note."""
    acts = []
    for p in plan:
        op, rel = p['op'], p['rel']
        if op == 'same':
            continue
        if op in ('only_local_deleted_remote', 'only_remote_deleted_local'):
            acts.append({'rel': rel, 'action': 'note', 'detail': p['detail']})
        elif op == 'pull':
            acts.append({'rel': rel, 'action': 'pull' if direction in ('pull', 'both') else 'skip', 'detail': p.get('detail', '')})
        elif op == 'push':
            acts.append({'rel': rel, 'action': 'push' if direction in ('push', 'both') else 'skip', 'detail': p.get('detail', '')})
        else:
            if strategy == 'skip':
                acts.append({'rel': rel, 'action': 'skip', 'detail': 'conflit non résolu (stratégie : ignorer)'})
            elif strategy == 'keep_both':
                acts.append({'rel': rel, 'action': 'conflict_copy_remote', 'detail': 'conflit : version distante copiée à côté'})
            else:
                newer_remote = remote[rel]['mtime'] > local[rel]['mtime']
                if newer_remote:
                    acts.append({'rel': rel, 'action': 'conflict_remote_wins' if direction in ('pull', 'both') else 'skip',
                                 'detail': 'conflit : le distant est plus récent (version locale conservée à côté)'})
                else:
                    acts.append({'rel': rel, 'action': 'conflict_local_wins' if direction in ('push', 'both') else 'conflict_copy_remote',
                                 'detail': 'conflit : le local est plus récent' + ('' if direction in ('push', 'both') else ' (sens pull : version distante copiée à côté)')})
    return acts


def conflict_name(root, rel, label, today=None):
    d = (today or datetime.date.today()).isoformat()
    base, ext = os.path.splitext(rel)
    n = 0
    while True:
        cand = f"{base} (conflit {label} {d}{'' if n == 0 else f' {n}'}){ext}"
        if not os.path.exists(safe_join(root, cand)):
            return cand
        n += 1


class PeerClient:
    """Client de l'instance appairée (clé d'appairage). Remplaçable par un faux client dans les tests."""

    def __init__(self, url, key, http=None, timeout=30):
        self.url, self.key, self.http, self.timeout = url.rstrip('/'), key, http or requests, timeout

    def _h(self, extra=None):
        return dict({'X-Stellio-Peer-Key': self.key}, **(extra or {}))

    def manifest(self, root):
        r = self.http.get(f'{self.url}/api/peer/sync/manifest', params={'root': root}, headers=self._h(), timeout=self.timeout)
        if r.status_code != 200:
            raise RuntimeError(f"Instance distante : {r.status_code} {(r.json() or {}).get('error', '') if r.headers.get('content-type', '').startswith('application/json') else ''}")
        return r.json()['files']

    def download(self, root, rel, dest):
        r = self.http.get(f'{self.url}/api/peer/sync/file', params={'root': root, 'rel': rel}, headers=self._h(), timeout=self.timeout, stream=True)
        if r.status_code != 200:
            raise RuntimeError(f'Téléchargement refusé ({r.status_code}).')
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(65536):
                f.write(chunk)

    def upload(self, root, rel, src, sig, expect_remote_sig):
        with open(src, 'rb') as f:
            r = self.http.post(f'{self.url}/api/peer/sync/file', params={'root': root, 'rel': rel}, data=f, timeout=self.timeout,
                               headers=self._h({'X-Stellio-Sig': sig, 'X-Stellio-Expect': expect_remote_sig or '', 'Content-Type': 'application/octet-stream'}))
        if r.status_code == 409:
            raise RuntimeError('Le fichier distant a changé depuis le plan : relancez la synchronisation.')
        if r.status_code != 200:
            raise RuntimeError(f"Envoi refusé ({r.status_code}).")


def _verify(path, sig):
    return not sig.startswith('h:') or file_sig(path) == sig


def execute(acts, local_root, remote_root, client, local, remote, base, strategy_label='distant', progress=None, today=None):
    """Applique les actions. Met `base` à jour fichier par fichier. Retourne {'done': n, 'errors': [...], 'conflicts': [...]}.
    Ne supprime jamais rien ; chaque écriture : fichier temporaire vérifié puis remplacement atomique."""
    done, errors, conflicts = 0, [], []
    tmp_dir = os.path.join(os.path.realpath(local_root), TMP)
    for i, a in enumerate(acts):
        if progress:
            progress(i, len(acts), a['rel'])
        rel, act = a['rel'], a['action']
        if act in ('note', 'skip'):
            continue
        try:
            dest = safe_join(local_root, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            os.makedirs(tmp_dir, exist_ok=True)
            tmp = os.path.join(tmp_dir, f'{abs(hash(rel))}.part')
            if act in ('pull', 'conflict_remote_wins', 'conflict_copy_remote'):
                client.download(remote_root, rel, tmp)
                if not _verify(tmp, remote[rel]['sig']):
                    raise RuntimeError('Empreinte reçue différente de celle annoncée.')
                if act == 'conflict_copy_remote':
                    keep = conflict_name(local_root, rel, 'distant', today)
                    os.replace(tmp, safe_join(local_root, keep))
                    conflicts.append({'rel': rel, 'kept_as': keep})
                else:
                    if act == 'conflict_remote_wins' and os.path.exists(dest):
                        keep = conflict_name(local_root, rel, 'local', today)
                        shutil.copy2(dest, safe_join(local_root, keep))
                        conflicts.append({'rel': rel, 'kept_as': keep})
                    os.replace(tmp, dest)
                    base[rel] = remote[rel]['sig']
            elif act in ('push', 'conflict_local_wins'):
                if act == 'conflict_local_wins':
                    keep = conflict_name(local_root, rel, 'distant', today)
                    client.download(remote_root, rel, tmp)
                    if not _verify(tmp, remote[rel]['sig']):
                        raise RuntimeError('Empreinte reçue différente de celle annoncée.')
                    os.replace(tmp, safe_join(local_root, keep))
                    conflicts.append({'rel': rel, 'kept_as': keep})
                client.upload(remote_root, rel, dest, local[rel]['sig'], remote.get(rel, {}).get('sig'))
                base[rel] = local[rel]['sig']
            done += 1
        except (OSError, RuntimeError, ValueError) as e:
            errors.append({'rel': rel, 'error': str(e)[:200]})
    shutil.rmtree(tmp_dir, ignore_errors=True)
    return {'done': done, 'errors': errors, 'conflicts': conflicts}


def summarize(acts):
    c = {}
    for a in acts:
        c[a['action']] = c.get(a['action'], 0) + 1
    return c


# ── base de données ──

def _ensure(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sync_pairs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT NOT NULL, instance_id INTEGER NOT NULL,
            local_root TEXT NOT NULL, remote_root TEXT NOT NULL, direction TEXT NOT NULL DEFAULT 'pull', strategy TEXT NOT NULL DEFAULT 'keep_both', last_run REAL, last_summary TEXT);
        CREATE TABLE IF NOT EXISTS sync_base (pair_id INTEGER NOT NULL, rel TEXT NOT NULL, sig TEXT NOT NULL, PRIMARY KEY (pair_id, rel));
    """)


def _edition_guard():
    if not (IS_SERVER_EDITION if IS_SERVER_EDITION is not None else _MAIN.get('IS_SERVER_EDITION')):
        return jsonify({'error': "Fonction réservée à l'édition serveur.", 'code': 'server_edition_only'}), 403
    return None


def _owner_guard():
    g = _edition_guard()
    if g:
        return g
    if session.get('role') == 'viewer' and not _demo_ok():
        return jsonify({'error': 'Réservé au compte propriétaire.', 'code': 'viewer_forbidden'}), 403
    return None


# ── côté « instance distante » (clé d'appairage) ──

def _peer_root(root):
    uid = _get_primary_user_id()
    if not uid or not root or not os.path.isdir(root) or not _is_path_within_sources(root, uid):
        return None
    return root


def api_peer_sync_manifest():
    g = _edition_guard()
    if g:
        return g
    root = _peer_root(request.args.get('root'))
    if not root:
        return jsonify({'error': 'Dossier invalide ou hors des sources de cette instance.'}), 400
    files = local_manifest(root)
    return jsonify({'files': files, 'count': len(files), 'truncated': len(files) >= MAX_FILES})


def api_peer_sync_file_get():
    g = _edition_guard()
    if g:
        return g
    root = _peer_root(request.args.get('root'))
    try:
        p = safe_join(root, request.args.get('rel')) if root else None
    except ValueError:
        p = None
    if not p or not os.path.isfile(p):
        return jsonify({'error': 'Fichier introuvable.'}), 404
    return send_file(p, as_attachment=True)


def api_peer_sync_file_put():
    g = _edition_guard()
    if g:
        return g
    root = _peer_root(request.args.get('root'))
    try:
        dest = safe_join(root, request.args.get('rel')) if root else None
    except ValueError:
        dest = None
    if not dest:
        return jsonify({'error': 'Chemin refusé.'}), 400
    expect = request.headers.get('X-Stellio-Expect', '')
    if os.path.exists(dest):
        if not expect or file_sig(dest) != expect:                   # le fichier distant n'est plus celui que le plan a vu : on n'écrase pas
            return jsonify({'error': 'Le fichier a changé.', 'code': 'conflict'}), 409
    elif expect:
        return jsonify({'error': 'Le fichier a disparu.', 'code': 'conflict'}), 409
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + '.stellio-part'
    with open(tmp, 'wb') as f:
        shutil.copyfileobj(request.stream, f, 1 << 20)
    sig = request.headers.get('X-Stellio-Sig', '')
    if sig.startswith('h:') and file_sig(tmp) != sig:
        os.remove(tmp)
        return jsonify({'error': 'Empreinte reçue différente.'}), 422
    os.replace(tmp, dest)
    return jsonify({'ok': True})


# ── côté « propriétaire » ──

def _pair(conn, pid):
    return conn.execute("SELECT p.*, i.url AS url, i.peer_key AS peer_key FROM sync_pairs p JOIN remote_instances i ON i.id = p.instance_id AND i.user_id = p.user_id "
                        "WHERE p.id = ? AND p.user_id = ?", (pid, session['user_id'])).fetchone()


def api_sync_pairs():
    g = _owner_guard()
    if g:
        return g
    conn = get_db()
    try:
        _ensure(conn)
        rows = conn.execute("SELECT id, name, instance_id, local_root, remote_root, direction, strategy, last_run, last_summary FROM sync_pairs WHERE user_id = ? ORDER BY id", (session['user_id'],)).fetchall()
        return jsonify({'pairs': [dict(r) for r in rows], 'directions': list(DIRECTIONS), 'strategies': list(STRATEGIES)})
    finally:
        conn.close()


def api_sync_pair_create():
    g = _owner_guard()
    if g:
        return g
    d = request.get_json(silent=True) or {}
    name, lr, rr = str(d.get('name') or '').strip()[:60], str(d.get('local_root') or '').strip(), str(d.get('remote_root') or '').strip()
    direction, strategy = d.get('direction') or 'pull', d.get('strategy') or 'keep_both'
    if not name or not lr or not rr or direction not in DIRECTIONS or strategy not in STRATEGIES:
        return jsonify({'error': 'Paramètres invalides.'}), 400
    if not os.path.isdir(lr) or not _is_path_within_sources(lr, session['user_id']):
        return jsonify({'error': 'Dossier local hors des sources.'}), 400
    conn = get_db()
    try:
        _ensure(conn)
        if not conn.execute("SELECT 1 FROM remote_instances WHERE id = ? AND user_id = ?", (d.get('instance_id'), session['user_id'])).fetchone():
            return jsonify({'error': 'Instance introuvable.'}), 404
        cur = conn.execute("INSERT INTO sync_pairs (user_id, name, instance_id, local_root, remote_root, direction, strategy) VALUES (?,?,?,?,?,?,?)",
                           (session['user_id'], name, d['instance_id'], lr, rr, direction, strategy))
        conn.commit()
        return jsonify({'ok': True, 'id': cur.lastrowid})
    finally:
        conn.close()


def api_sync_pair_delete(pid):
    g = _owner_guard()
    if g:
        return g
    conn = get_db()
    try:
        _ensure(conn)
        cur = conn.execute("DELETE FROM sync_pairs WHERE id = ? AND user_id = ?", (pid, session['user_id']))
        conn.execute("DELETE FROM sync_base WHERE pair_id = ?", (pid,))
        conn.commit()
        return jsonify({'ok': True}) if cur.rowcount else (jsonify({'error': 'Introuvable.'}), 404)
    finally:
        conn.close()


def run_pair(pair, uid, apply=False, ctx=None, client=None):
    """Plan (apply=False) ou synchronisation (apply=True) d'une paire. Retourne le résumé."""
    progress = ctx.progress if ctx else None
    client = client or PeerClient(pair['url'], pair['peer_key'])
    conn = get_db()
    try:
        base = {r['rel']: r['sig'] for r in conn.execute("SELECT rel, sig FROM sync_base WHERE pair_id = ?", (pair['id'],)).fetchall()}
        local = local_manifest(pair['local_root'])
        remote = client.manifest(pair['remote_root'])
        plan = diff3(local, remote, base)
        acts = resolve(plan, local, remote, pair['direction'], pair['strategy'])
        res = {'applied': False, 'summary': summarize(acts), 'items': acts[:PLAN_ITEMS], 'truncated': len(acts) > PLAN_ITEMS,
               'same': sum(1 for p in plan if p['op'] == 'same'), 'local': len(local), 'remote': len(remote)}
        if apply:
            out = execute(acts, pair['local_root'], pair['remote_root'], client, local, remote, base, progress=progress)
            for p in plan:                                       # les fichiers identiques deviennent l'accord de référence
                if p['op'] == 'same':
                    base[p['rel']] = local[p['rel']]['sig']
            conn.execute("DELETE FROM sync_base WHERE pair_id = ?", (pair['id'],))
            conn.executemany("INSERT INTO sync_base (pair_id, rel, sig) VALUES (?,?,?)", [(pair['id'], k, v) for k, v in base.items()])
            res.update(applied=True, result=out)
            conn.execute("UPDATE sync_pairs SET last_run = ?, last_summary = ? WHERE id = ?",
                         (time.time(), json.dumps({'done': out['done'], 'errors': len(out['errors']), 'conflicts': len(out['conflicts'])}), pair['id']))
        conn.commit()
        return res
    finally:
        conn.close()


def _submit(pair, uid, apply):
    try:
        from modules import job_manager
        return job_manager.submit(('Synchronisation : ' if apply else 'Plan de synchronisation : ') + pair['name'], lambda ctx: run_pair(pair, uid, apply, ctx),
                                  owner=uid, kind='library_sync')
    except ImportError:
        return None


def _go(pid, apply):
    g = _owner_guard()
    if g:
        return g
    if apply and (request.get_json(silent=True) or {}).get('confirm') is not True:
        return jsonify({'error': 'Confirmation requise (confirm: true) : lancez d\'abord le plan.'}), 400
    conn = get_db()
    try:
        _ensure(conn)
        row = _pair(conn, pid)
        pair = dict(row) if row else None
    finally:
        conn.close()
    if not pair:
        return jsonify({'error': 'Paire introuvable.'}), 404
    job = _submit(pair, session['user_id'], apply)
    if job is None:
        try:
            return jsonify({'result': run_pair(pair, session['user_id'], apply)})
        except RuntimeError as e:
            return jsonify({'error': str(e)}), 502
    return jsonify({'job_id': job.id}), 202


def api_sync_plan(pid):
    return _go(pid, False)


def api_sync_apply(pid):
    return _go(pid, True)


_DEMO_COMPUTE = ('/api/plate/arrange', '/api/organize/preview', '/api/model-diff')


def _demo_ok():
    """Démo publique (lecture seule, `IS_DEMO` posé par la surcouche de démo) : consultation (GET) et calculs sans écriture."""
    try:
        return bool(_MAIN.get('IS_DEMO')) and (request.method in ('GET', 'HEAD') or request.path in _DEMO_COMPUTE)
    except Exception:
        return False


_ROUTES = (
    ('/api/sync/pairs', ['GET'], 'api_sync_pairs', ('login_required', )),
    ('/api/sync/pairs', ['POST'], 'api_sync_pair_create', ('login_required', )),
    ('/api/sync/pairs/<int:pid>', ['DELETE'], 'api_sync_pair_delete', ('login_required', )),
    ('/api/sync/pairs/<int:pid>/plan', ['POST'], 'api_sync_plan', ('login_required', )),
    ('/api/sync/pairs/<int:pid>/apply', ['POST'], 'api_sync_apply', ('login_required', )),
    ('/api/peer/sync/manifest', ['GET'], 'api_peer_sync_manifest', ('require_peer_key', )),
    ('/api/peer/sync/file', ['GET'], 'api_peer_sync_file_get', ('require_peer_key', )),
    ('/api/peer/sync/file', ['POST'], 'api_peer_sync_file_put', ('require_peer_key', )),
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
