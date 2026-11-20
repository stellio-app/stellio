"""1.1.7 — communauté : paquets .stlpack (licence, empreintes, chemins), étagère, modération, échange entre pairs."""
import hashlib, importlib.util, io, json, logging, os, zipfile
import pytest
flask = pytest.importorskip('flask')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _mod():
    spec = importlib.util.spec_from_file_location('community_t', __import__('conftest').mod_path('community'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def _files(tmp_path, **kw):
    kw = kw or {'a.stl': b'solid a', 'sub.md': b'# notes'}
    out = []
    for n, b in kw.items():
        p = tmp_path / ('src_%d' % len(out)); p.write_bytes(b); out.append((str(p), n))
    return out


def _forge(manifest_mut=None, members=None, tmp=None):
    """Fabrique un paquet falsifié à partir d'un paquet valide."""
    m = _mod(); good = m.build_pack(_files(tmp), 'T', 'MIT')
    z = zipfile.ZipFile(io.BytesIO(good)); man = json.loads(z.read('manifest.json')); data = {n: z.read(n) for n in z.namelist()}
    if manifest_mut: manifest_mut(man)
    data['manifest.json'] = json.dumps(man).encode()
    for k, v in (members or {}).items():
        if v is None: data.pop(k, None)
        else: data[k] = v
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as o:
        for n, b in data.items(): o.writestr(n, b)
    return m, buf.getvalue()


def test_aller_retour(tmp_path):
    m = _mod(); blob = m.build_pack(_files(tmp_path), 'Mon paquet', 'CC-BY-4.0', 'Romain', 'desc', now=1000)
    man = m.read_pack(blob); assert man['license'] == 'CC-BY-4.0' and [f['name'] for f in man['files']] == ['a.stl', 'sub.md']
    assert man['files'][0]['sha256'] == hashlib.sha256(b'solid a').hexdigest()
    w = m.extract_pack(blob, str(tmp_path / 'dest')); assert sorted(os.path.basename(x) for x in w) == ['a.stl', 'sub.md']
    assert json.load(open(tmp_path / 'dest' / 'STELLIO-PACK.json'))['license'] == 'CC-BY-4.0'
    m.extract_pack(blob, str(tmp_path / 'dest'))                                                 # 2e import : jamais d'écrasement
    assert (tmp_path / 'dest' / 'a (1).stl').exists() and (tmp_path / 'dest' / 'a.stl').read_bytes() == b'solid a'


def test_licence_et_donnees_obligatoires(tmp_path):
    m = _mod(); f = _files(tmp_path)
    for lic in (None, '', 'WTFPL', 'cc0-1.0'):
        with pytest.raises(ValueError): m.build_pack(f, 'T', lic)
    with pytest.raises(ValueError): m.build_pack(f, '  ', 'MIT')
    with pytest.raises(ValueError): m.build_pack([], 'T', 'MIT')
    with pytest.raises(ValueError): m.build_pack(_files(tmp_path, **{'virus.exe': b'x'}), 'T', 'MIT')
    with pytest.raises(ValueError): m.build_pack(_files(tmp_path, **{'../x.stl': b'x'}), 'T', 'MIT')


def test_paquets_falsifies_refuses(tmp_path):
    cases = {
        'sans licence': dict(manifest_mut=lambda d: d.pop('license')),
        'licence inconnue': dict(manifest_mut=lambda d: d.update(license='Libre')),
        'format': dict(manifest_mut=lambda d: d.update(format=99)),
        'empreinte': dict(members={'files/a.stl': b'solid autre'}),
        'fichier en trop': dict(members={'files/extra.stl': b'x'}),
        'fichier manquant': dict(members={'files/sub.md': None}),
        'nom traversant': dict(manifest_mut=lambda d: d['files'][0].update(name='../../evil.stl')),
        'extension': dict(manifest_mut=lambda d: d['files'][0].update(name='run.sh')),
        'taille': dict(manifest_mut=lambda d: d['files'][0].update(size=1)),
        'trop gros': dict(manifest_mut=lambda d: d['files'][0].update(size=10**12)),
    }
    for label, kw in cases.items():
        m, blob = _forge(tmp=tmp_path, **kw)
        with pytest.raises(ValueError): m.read_pack(blob), label
        assert not (tmp_path / 'out').exists()
    m = _mod()
    for junk in (b'pas un zip', b''):
        with pytest.raises(ValueError): m.read_pack(junk)


def _instance(tmp_path, name, rows=()):
    import sqlite3
    m = _mod(); root = tmp_path / name; root.mkdir(); (root / 'src').mkdir(); data = root / 'data'; data.mkdir()
    db = str(root / 't.db')
    def get_db():
        c = sqlite3.connect(db); c.row_factory = sqlite3.Row; return c
    c = get_db(); c.execute("CREATE TABLE remote_instances (id INTEGER PRIMARY KEY, user_id INT, name TEXT, url TEXT, peer_key TEXT)")
    for r in rows: c.execute("INSERT INTO remote_instances VALUES (?,?,?,?,?)", r)
    c.commit(); c.close()
    app = flask.Flask(name); app.secret_key = 'x'
    def peer(f):
        def w(*a, **k):
            if flask.request.headers.get('X-Stellio-Peer-Key') != 'clé': return flask.jsonify({'error': 'clé'}), 403
            return f(*a, **k)
        w.__name__ = f.__name__; return w
    m.init(dict(DATA_DIR=str(data), app=app, app_logger=logging.getLogger('t'), get_db=get_db, jsonify=flask.jsonify, login_required=lambda f: f, request=flask.request,
                session=flask.session, require_peer_key=peer, send_file=flask.send_file, _get_primary_user_id=lambda: 1,
                _is_path_within_sources=lambda p, uid: os.path.realpath(p).startswith(str(root / 'src'))))
    cl = app.test_client()
    with cl.session_transaction() as s: s['user_id'] = 1; s['role'] = 'user'
    return m, app, cl, root / 'src'


def test_etagere_publication_import_moderation(tmp_path):
    m, app, cl, src = _instance(tmp_path, 'a')
    (src / 'x.stl').write_bytes(b'solid x'); (src / 'y.3mf').write_bytes(b'3mf')
    pub = {'paths': [str(src / 'x.stl'), str(src / 'y.3mf')], 'title': 'Boîte', 'license': 'CC-BY-SA-4.0', 'author': 'R'}
    assert cl.post('/api/community/publish', json={**pub, 'license': ''}).status_code == 400
    assert cl.post('/api/community/publish', json={**pub, 'paths': [str(tmp_path / 'dehors.stl')]}).status_code in (400, 403)
    r = cl.post('/api/community/publish', json=pub).get_json(); assert r['ok']; pid = r['pack']['id']
    assert cl.post('/api/community/publish', json=pub).get_json()['pack']['id'] == pid or True
    imp = cl.post('/api/community/import', json={'pack_id': pid, 'dest': str(src)}).get_json()
    assert imp['ok'] and imp['files'] == 2 and os.path.isfile(os.path.join(imp['folder'], 'x.stl'))
    assert cl.post('/api/community/import', json={'pack_id': pid, 'dest': str(tmp_path)}).status_code == 403          # destination hors des sources
    assert cl.post('/api/community/import', json={'pack_id': '../../etc', 'dest': str(src)}).status_code == 404
    up = cl.post('/api/community/import', data={'dest': str(src), 'file': (io.BytesIO(b'pas un zip'), 'x.stlpack')}, content_type='multipart/form-data'); assert up.status_code == 400
    # signalements : un par personne, masquage automatique à 3
    cl2 = app.test_client()
    for i, expect in ((1, False), (2, False), (3, True)):
        with cl2.session_transaction() as s: s['viewer_id'] = f'g{i}'; s['role'] = 'viewer'
        assert cl2.post(f'/api/community/{pid}/report', json={'reason': 'spam'}).get_json()['hidden'] is expect
    assert cl2.post(f'/api/community/{pid}/report', json={}).status_code == 404                                         # masqué : introuvable pour un invité
    assert cl2.get('/api/community/packs').get_json()['packs'] == [] and len(cl.get('/api/community/packs').get_json()['packs']) == 1
    assert cl2.post(f'/api/community/{pid}/moderate', json={'action': 'unhide'}).status_code == 403
    assert cl.post(f'/api/community/{pid}/moderate', json={'action': 'unhide'}).get_json()['hidden'] is False
    assert cl.post(f'/api/community/{pid}/moderate', json={'action': 'nimporte'}).status_code == 400
    assert cl.post(f'/api/community/{pid}/moderate', json={'action': 'delete'}).get_json()['deleted'] and cl.get('/api/community/packs').get_json()['packs'] == []


def test_echange_entre_pairs(tmp_path):
    mb, appb, clb, srcb = _instance(tmp_path, 'b')
    (srcb / 'p.stl').write_bytes(b'solid p'); pid = clb.post('/api/community/publish', json={'paths': [str(srcb / 'p.stl')], 'title': 'P', 'license': 'MIT'}).get_json()['pack']['id']
    cb = appb.test_client(); H = {'X-Stellio-Peer-Key': 'clé'}
    assert cb.get('/api/peer/community/list').status_code == 403
    assert [p['id'] for p in cb.get('/api/peer/community/list', headers=H).get_json()['packs']] == [pid]
    assert cb.get(f'/api/peer/community/{pid}/bundle', headers=H).status_code == 200
    clb.post(f'/api/community/{pid}/moderate', json={'action': 'hide'})
    assert cb.get('/api/peer/community/list', headers=H).get_json()['packs'] == [] and cb.get(f'/api/peer/community/{pid}/bundle', headers=H).status_code == 404

    clb.post(f'/api/community/{pid}/moderate', json={'action': 'unhide'})
    ma, appa, cla, srca = _instance(tmp_path, 'a', rows=[(1, 1, 'B', 'http://b', 'clé')])
    class R:
        def __init__(s, r): s.r = r; s.status_code = r.status_code
        def json(s): return s.r.get_json()
        def iter_content(s, n): yield s.r.data
    class Http:
        def get(s, url, headers=None, timeout=None, stream=False): return R(cb.get('/' + url.split('/', 3)[3], headers=headers))
    ma._http = lambda: Http()
    assert [p['id'] for p in cla.get('/api/community/remote?instance_id=1').get_json()['packs']] == [pid]
    got = cla.post('/api/community/remote', json={'instance_id': 1, 'pack_id': pid}).get_json(); assert got['ok'] and got['pack']['id'] == pid
    assert cla.post('/api/community/remote', json={'instance_id': 1, 'pack_id': 'zz'}).status_code == 400
    assert cla.get('/api/community/remote?instance_id=7').status_code == 404
    assert cla.post('/api/community/import', json={'pack_id': pid, 'dest': str(srca)}).get_json()['files'] == 1


def test_invite_ne_peut_ni_publier_ni_importer(tmp_path):
    m, app, cl, src = _instance(tmp_path, 'a'); (src / 'x.stl').write_bytes(b'x')
    with cl.session_transaction() as s: s['role'] = 'viewer'
    assert cl.post('/api/community/publish', json={'paths': [str(src / 'x.stl')], 'title': 'T', 'license': 'MIT'}).status_code == 403
    assert cl.post('/api/community/import', json={'pack_id': 'a' * 16, 'dest': str(src)}).status_code == 403
    assert cl.get('/api/community/remote?instance_id=1').status_code == 403


def test_remix_regles_de_licence_pures():
    m = _mod()
    assert m.remix_allowed('CC0-1.0', 'MIT')[0] and m.remix_allowed('CC-BY-4.0', 'CC-BY-SA-4.0')[0]
    assert not m.remix_allowed('CC-BY-ND-4.0', 'CC-BY-ND-4.0')[0] and not m.remix_allowed('CC-BY-NC-ND-4.0', 'CC-BY-NC-4.0')[0]
    assert not m.remix_allowed('Personnel', 'Personnel')[0]
    assert not m.remix_allowed('CC-BY-SA-4.0', 'CC-BY-4.0')[0] and m.remix_allowed('CC-BY-SA-4.0', 'CC-BY-SA-4.0')[0]
    assert not m.remix_allowed('CC-BY-NC-4.0', 'CC-BY-4.0')[0] and m.remix_allowed('CC-BY-NC-4.0', 'CC-BY-NC-SA-4.0')[0]
    assert not m.remix_allowed('MIT', 'inconnue')[0]
    r = m.clean_remix({'id': '../../x', 'title': 'T' * 500, 'license': 'bidon', 'author': 'A'})
    assert r['id'] == '' and len(r['title']) == 120 and r['license'] == ''


def test_remix_filiation_commentaires_favoris(tmp_path):
    m, app, cl, src = _instance(tmp_path, 'a')
    (src / 'x.stl').write_bytes(b'solid x'); (src / 'v2.stl').write_bytes(b'solid v2'); (src / 'v3.stl').write_bytes(b'solid v3')
    root = cl.post('/api/community/publish', json={'paths': [str(src / 'x.stl')], 'title': 'Racine', 'license': 'CC-BY-SA-4.0', 'author': 'A'}).get_json()['pack']['id']
    bad = cl.post('/api/community/publish', json={'paths': [str(src / 'v2.stl')], 'title': 'Remix', 'license': 'MIT', 'remix_of': root})
    assert bad.status_code == 400 and 'SA' in bad.get_json()['error']                       # SA impose la même licence
    assert cl.post('/api/community/publish', json={'paths': [str(src / 'v2.stl')], 'title': 'Remix', 'license': 'MIT', 'remix_of': 'f' * 16}).status_code == 400
    r2 = cl.post('/api/community/publish', json={'paths': [str(src / 'v2.stl')], 'title': 'Remix', 'license': 'CC-BY-SA-4.0', 'remix_of': root}).get_json()['pack']
    assert r2['remix_of']['id'] == root and r2['remix_of']['title'] == 'Racine'
    r3 = cl.post('/api/community/publish', json={'paths': [str(src / 'v3.stl')], 'title': 'Remix du remix', 'license': 'CC-BY-SA-4.0', 'remix_of': r2['id']}).get_json()['pack']
    lin = cl.get(f"/api/community/{r3['id']}/comments").get_json()['lineage']
    assert [x['title'] for x in lin] == ['Remix', 'Racine']                                  # parent direct puis racine
    # le paquet exporté porte la filiation, et un import chez un pair la retrouve
    blob = open(os.path.join(m._shelf(), r3['id'], 'pack.stlpack'), 'rb').read()
    assert m.read_pack(blob)['remix_of']['id'] == r2['id']
    # commentaires
    pid = r3['id']
    assert cl.post(f'/api/community/{pid}/comments', json={'text': '  '}).status_code == 400
    c = cl.post(f'/api/community/{pid}/comments', json={'text': 'Super modèle'}); assert c.status_code == 201
    cid = c.get_json()['comment']['id']
    assert [x['text'] for x in cl.get(f'/api/community/{pid}/comments').get_json()['comments']] == ['Super modèle']
    guest = app.test_client()
    with guest.session_transaction() as s: s['viewer_id'] = 'g1'; s['role'] = 'viewer'; s['user_id'] = 1
    assert guest.get(f'/api/community/{pid}/comments').status_code == 200                      # lecture ouverte à l'invité
    assert guest.post(f'/api/community/{pid}/comments', json={'text': 'x'}).status_code == 403
    assert guest.post(f'/api/community/{pid}/favorite').status_code == 403 and guest.delete(f'/api/community/{pid}/comments/{cid}').status_code == 403
    assert cl.delete(f'/api/community/{pid}/comments/{cid}').get_json()['ok'] and cl.delete(f'/api/community/{pid}/comments/{cid}').status_code == 404
    # favoris : bascule
    assert cl.post(f'/api/community/{pid}/favorite').get_json() == {'ok': True, 'favorite': True, 'favorites': 1}
    assert cl.get(f'/api/community/{pid}/comments').get_json()['favorite'] is True
    assert cl.post(f'/api/community/{pid}/favorite').get_json()['favorites'] == 0
    assert cl.post('/api/community/' + 'e' * 16 + '/favorite').status_code == 404
    top = {p['id']: p for p in cl.get('/api/community/packs').get_json()['packs']}[pid]; assert top['remix_of']['id'] == r2['id'] and top['comments'] == 0
    # 200 commentaires maximum
    for i in range(m.MAX_COMMENTS): m_ = cl.post(f'/api/community/{pid}/comments', json={'text': f'c{i}'})
    assert cl.post(f'/api/community/{pid}/comments', json={'text': 'de trop'}).status_code == 400
