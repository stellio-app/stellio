"""1.1.7 — synchronisation de bibliothèques : plan à trois voies, conflits, jamais de suppression, côté pair, bout en bout."""
import datetime, importlib.util, io, json, logging, os, sqlite3
import pytest
flask = pytest.importorskip('flask')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _mod():
    spec = importlib.util.spec_from_file_location('library_sync_t', __import__('conftest').mod_path('library_sync'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def E(sig, mtime=100.0, size=1): return {'size': size, 'mtime': mtime, 'sig': sig}


def test_chemins_surs(tmp_path):
    m = _mod()
    assert m.safe_rel('a/b.stl') == 'a/b.stl' and m.safe_rel('a\\b.stl') == 'a/b.stl'
    for bad in ('', '../x', 'a/../../x', '/etc/passwd', 'C:/x', 'a//b', m.TMP + '/x', '.'):
        with pytest.raises(ValueError): m.safe_rel(bad)
    with pytest.raises(ValueError): m.safe_join(str(tmp_path), '../dehors')
    os.symlink('/tmp', str(tmp_path / 'lien'))
    with pytest.raises(ValueError): m.safe_join(str(tmp_path), 'lien/x')                # un lien ne permet pas de sortir du dossier


def test_plan_trois_voies():
    m = _mod()
    local = {'same': E('a'), 'modloc': E('L2'), 'modrem': E('b'), 'conf': E('L'), 'onlyloc': E('x'), 'delrem': E('y'), 'both_nobase': E('p')}
    remote = {'same': E('a'), 'modloc': E('b0'), 'modrem': E('R2'), 'conf': E('R'), 'onlyrem': E('z'), 'dellocal': E('w'), 'both_nobase': E('q')}
    base = {'same': 'a', 'modloc': 'b0', 'modrem': 'b', 'conf': 'c0', 'delrem': 'y', 'dellocal': 'w'}
    ops = {p['rel']: p['op'] for p in m.diff3(local, remote, base)}
    assert ops == {'same': 'same', 'modloc': 'push', 'modrem': 'pull', 'conf': 'conflict', 'onlyloc': 'push', 'delrem': 'only_local_deleted_remote',
                   'onlyrem': 'pull', 'dellocal': 'only_remote_deleted_local', 'both_nobase': 'conflict'}


def test_resolution_selon_sens_et_strategie():
    m = _mod()
    local, remote = {'c': E('L', 100)}, {'c': E('R', 200)}
    plan = [{'rel': 'c', 'op': 'conflict'}, {'rel': 'p', 'op': 'pull'}, {'rel': 'u', 'op': 'push'}, {'rel': 'd', 'op': 'only_remote_deleted_local', 'detail': 'x'}]
    A = lambda direction, strategy: {a['rel']: a['action'] for a in m.resolve(plan, local, remote, direction, strategy)}
    assert A('pull', 'newer') == {'c': 'conflict_remote_wins', 'p': 'pull', 'u': 'skip', 'd': 'note'}
    assert A('push', 'newer')['c'] == 'skip' and A('push', 'newer')['u'] == 'push' and A('push', 'newer')['p'] == 'skip'
    assert A('both', 'keep_both')['c'] == 'conflict_copy_remote' and A('both', 'skip')['c'] == 'skip'
    local['c'] = E('L', 300)                                                           # local plus récent
    assert A('both', 'newer')['c'] == 'conflict_local_wins' and A('pull', 'newer')['c'] == 'conflict_copy_remote'
    assert A('pull', 'newer')['d'] == 'note'                                           # une suppression n'est jamais propagée


def test_empreintes_et_nom_de_conflit(tmp_path):
    m = _mod(); p = tmp_path / 'a.stl'; p.write_bytes(b'abc')
    assert m.file_sig(str(p)).startswith('h:') and m.file_sig(str(p)) == m.file_sig(str(p))
    old = m.HASH_MAX; m.HASH_MAX = 1
    assert m.file_sig(str(p)).startswith('m:3:'); m.HASH_MAX = old
    d = datetime.date(2026, 11, 18)
    assert m.conflict_name(str(tmp_path), 'a.stl', 'local', d) == 'a (conflit local 2026-11-18).stl'
    (tmp_path / 'a (conflit local 2026-11-18).stl').write_bytes(b'x')
    assert m.conflict_name(str(tmp_path), 'a.stl', 'local', d) == 'a (conflit local 2026-11-18 1).stl'


def test_manifeste_ignore_caches_liens_et_reutilise_le_cache(tmp_path):
    m = _mod(); (tmp_path / 'sub').mkdir(); (tmp_path / '.cache').mkdir()
    (tmp_path / 'a.stl').write_bytes(b'1'); (tmp_path / 'sub' / 'b.3mf').write_bytes(b'22'); (tmp_path / '.cache' / 'c').write_bytes(b'3'); (tmp_path / '.cache_f').write_bytes(b'4')
    os.symlink(str(tmp_path / 'a.stl'), str(tmp_path / 'lien.stl'))
    cache = {}; man = m.local_manifest(str(tmp_path), cache)
    assert sorted(man) == ['a.stl', 'sub/b.3mf'] and len(cache) == 2
    cache[('a.stl', 1, int(os.path.getmtime(tmp_path / 'a.stl')))] = 'h:marqueur'
    assert m.local_manifest(str(tmp_path), cache)['a.stl']['sig'] == 'h:marqueur'


# ── bout en bout : deux « instances » (deux apps Flask) reliées par un client HTTP simulé ──
class _Resp:
    def __init__(self, r): self.r = r; self.status_code = r.status_code; self.headers = {'content-type': r.mimetype or ''}
    def json(self): return self.r.get_json()
    def iter_content(self, n): yield self.r.data


class _Http:
    """Fait croire à PeerClient qu'il parle à l'instance distante (client de test Flask)."""
    def __init__(self, client): self.c = client
    def get(self, url, params=None, headers=None, timeout=None, stream=False):
        return _Resp(self.c.get('/' + url.split('/', 3)[3], query_string=params, headers=headers))
    def post(self, url, params=None, data=None, headers=None, timeout=None):
        return _Resp(self.c.post('/' + url.split('/', 3)[3], query_string=params, data=data.read(), headers=headers))


def _instance(tmp_path, name, server=True, sources=None):
    m = _mod(); root = tmp_path / name; root.mkdir(); (root / 'lib').mkdir()
    db = str(root / 't.db')
    def get_db():
        c = sqlite3.connect(db); c.row_factory = sqlite3.Row; return c
    c = get_db(); c.execute("CREATE TABLE remote_instances (id INTEGER PRIMARY KEY, user_id INT, name TEXT, url TEXT, peer_key TEXT)"); c.execute("INSERT INTO remote_instances VALUES (1,1,'B','http://b','clé')"); c.commit(); c.close()
    app = flask.Flask(name); app.secret_key = 'x'
    def require_peer_key(f):
        def w(*a, **k):
            if flask.request.headers.get('X-Stellio-Peer-Key') != 'clé': return flask.jsonify({'error': 'clé'}), 403
            return f(*a, **k)
        w.__name__ = f.__name__; return w
    m.init(dict(app=app, app_logger=logging.getLogger('t'), get_db=get_db, jsonify=flask.jsonify, login_required=lambda f: f, request=flask.request, session=flask.session,
                require_peer_key=require_peer_key, _get_primary_user_id=lambda: 1, send_file=flask.send_file, IS_SERVER_EDITION=server,
                _is_path_within_sources=lambda p, uid: os.path.realpath(p).startswith(str(root)) or True if sources is None else sources(p)))
    return m, app, root / 'lib', get_db


def test_synchronisation_bout_en_bout(tmp_path):
    ma, appa, liba, dba = _instance(tmp_path, 'a'); mb, appb, libb, dbb = _instance(tmp_path, 'b')
    (liba / 'commun.stl').write_bytes(b'v1'); (libb / 'commun.stl').write_bytes(b'v1')
    (libb / 'nouveau_distant.stl').write_bytes(b'nd'); (liba / 'nouveau_local.stl').write_bytes(b'nl')
    (libb / 'dossier').mkdir(); (libb / 'dossier' / 'sous.3mf').write_bytes(b'sous')
    client = ma.PeerClient('http://b', 'clé', http=_Http(appb.test_client()))
    pair = {'id': 1, 'name': 'test', 'local_root': str(liba), 'remote_root': str(libb), 'direction': 'both', 'strategy': 'keep_both', 'url': 'http://b', 'peer_key': 'clé'}
    c = dba(); ma._ensure(c); c.commit(); c.close()
    plan = ma.run_pair(pair, 1, apply=False, client=client)
    assert plan['summary'] == {'pull': 2, 'push': 1} and plan['applied'] is False and not (liba / 'nouveau_distant.stl').exists()      # le plan n'écrit rien
    done = ma.run_pair(pair, 1, apply=True, client=client)
    assert done['result']['done'] == 3 and not done['result']['errors']
    assert (liba / 'nouveau_distant.stl').read_bytes() == b'nd' and (liba / 'dossier' / 'sous.3mf').read_bytes() == b'sous' and (libb / 'nouveau_local.stl').read_bytes() == b'nl'
    assert not os.path.exists(liba / ma.TMP) and not [f for f in os.listdir(libb) if f.endswith('.stellio-part')]                        # aucun fichier temporaire
    again = ma.run_pair(pair, 1, apply=True, client=client); assert again['summary'] == {} and again['same'] == 4                          # idempotent
    # modification locale seule → poussée ; suppression locale → jamais propagée
    (liba / 'commun.stl').write_bytes(b'v2'); os.remove(liba / 'nouveau_local.stl')
    r = ma.run_pair(pair, 1, apply=True, client=client)
    assert (libb / 'commun.stl').read_bytes() == b'v2' and (libb / 'nouveau_local.stl').exists() and r['summary'].get('push') == 1 and r['summary'].get('note') == 1
    assert not (liba / 'nouveau_local.stl').exists()                                                                                         # et la suppression n'a pas été « réparée » en local


def test_conflit_aucune_version_perdue(tmp_path):
    ma, appa, liba, dba = _instance(tmp_path, 'a'); mb, appb, libb, dbb = _instance(tmp_path, 'b')
    client = ma.PeerClient('http://b', 'clé', http=_Http(appb.test_client()))
    (liba / 'p.stl').write_bytes(b'base'); (libb / 'p.stl').write_bytes(b'base')
    pair = {'id': 1, 'name': 't', 'local_root': str(liba), 'remote_root': str(libb), 'direction': 'both', 'strategy': 'keep_both', 'url': 'x', 'peer_key': 'clé'}
    c = dba(); ma._ensure(c); c.commit(); c.close()
    ma.run_pair(pair, 1, True, client=client)
    (liba / 'p.stl').write_bytes(b'LOCAL'); (libb / 'p.stl').write_bytes(b'REMOTE')
    r = ma.run_pair(pair, 1, True, client=client)
    kept = r['result']['conflicts']; assert len(kept) == 1
    assert (liba / 'p.stl').read_bytes() == b'LOCAL' and (liba / kept[0]['kept_as']).read_bytes() == b'REMOTE'                              # les DEUX versions existent
    r2 = ma.run_pair(pair, 1, True, client=client)                                                                                           # la copie de conflit part au distant au tour suivant
    assert any(f.startswith('p (conflit') for f in os.listdir(libb)) and (libb / 'p.stl').read_bytes() == b'REMOTE'
    # stratégie « le plus récent » : le distant gagne, la version locale est gardée à côté
    pair2 = dict(pair, id=2, strategy='newer'); c = dba(); c.commit(); c.close()
    (liba / 'q.stl').write_bytes(b'x1'); (libb / 'q.stl').write_bytes(b'x1'); ma.run_pair(pair2, 1, True, client=client)
    (liba / 'q.stl').write_bytes(b'LOC'); os.utime(liba / 'q.stl', (1000, 1000)); (libb / 'q.stl').write_bytes(b'REM'); os.utime(libb / 'q.stl', (2000, 2000))
    r = ma.run_pair(dict(pair2, direction='pull'), 1, True, client=client)
    assert (liba / 'q.stl').read_bytes() == b'REM' and any(open(liba / c['kept_as'], 'rb').read() == b'LOC' for c in r['result']['conflicts'])


def test_pair_refuse_ecrasement_si_le_distant_a_change_depuis_le_plan(tmp_path):
    ma, appa, liba, dba = _instance(tmp_path, 'a'); mb, appb, libb, dbb = _instance(tmp_path, 'b')
    (libb / 'f.stl').write_bytes(b'v1'); sig = mb.file_sig(str(libb / 'f.stl'))
    cl = appb.test_client(); H = {'X-Stellio-Peer-Key': 'clé', 'X-Stellio-Expect': sig, 'X-Stellio-Sig': mb.file_sig(str(libb / 'f.stl'))}
    (libb / 'f.stl').write_bytes(b'modifie entre-temps')
    r = cl.post('/api/peer/sync/file', query_string={'root': str(libb), 'rel': 'f.stl'}, data=b'nouveau', headers=H); assert r.status_code == 409
    assert (libb / 'f.stl').read_bytes() == b'modifie entre-temps'
    r = cl.post('/api/peer/sync/file', query_string={'root': str(libb), 'rel': 'g.stl'}, data=b'x', headers={'X-Stellio-Peer-Key': 'clé', 'X-Stellio-Sig': 'h:00'}); assert r.status_code == 422
    assert not (libb / 'g.stl').exists() and not (libb / 'g.stl.stellio-part').exists()                                                    # empreinte fausse : rien écrit
    r = cl.post('/api/peer/sync/file', query_string={'root': str(libb), 'rel': '../evil.stl'}, data=b'x', headers={'X-Stellio-Peer-Key': 'clé'}); assert r.status_code == 400
    assert cl.get('/api/peer/sync/manifest', query_string={'root': str(libb)}).status_code == 403                                           # sans clé d'appairage


def test_edition_serveur_obligatoire_et_proprietaire(tmp_path):
    ma, appa, liba, dba = _instance(tmp_path, 'a', server=False)
    cl = appa.test_client()
    with cl.session_transaction() as s: s['user_id'] = 1
    r = cl.get('/api/sync/pairs'); assert r.status_code == 403 and r.get_json()['code'] == 'server_edition_only'
    assert cl.get('/api/peer/sync/manifest', headers={'X-Stellio-Peer-Key': 'clé'}, query_string={'root': str(liba)}).status_code == 403
    mb, appb, libb, dbb = _instance(tmp_path, 'b', server=True)
    cl = appb.test_client()
    with cl.session_transaction() as s: s['user_id'] = 1; s['role'] = 'viewer'
    assert cl.get('/api/sync/pairs').status_code == 403
    with cl.session_transaction() as s: s['role'] = 'user'
    assert cl.post('/api/sync/pairs', json={'name': 'x', 'instance_id': 1, 'local_root': str(libb), 'remote_root': '/r', 'direction': 'pull', 'strategy': 'invalide'}).status_code == 400
    assert cl.post('/api/sync/pairs', json={'name': 'x', 'instance_id': 9, 'local_root': str(libb), 'remote_root': '/r'}).status_code == 404
    ok = cl.post('/api/sync/pairs', json={'name': 'x', 'instance_id': 1, 'local_root': str(libb), 'remote_root': '/r'}).get_json(); assert ok['ok']
    assert cl.post(f"/api/sync/pairs/{ok['id']}/apply", json={}).status_code == 400                                                         # confirmation obligatoire
    assert cl.delete(f"/api/sync/pairs/{ok['id']}").status_code == 200 and cl.get('/api/sync/pairs').get_json()['pairs'] == []
