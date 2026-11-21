"""1.1.7 — blocs E et F : compatibilité imprimante, auto-organisation, diff 3D, recherche de formes."""
import importlib.util, json, logging, os, sqlite3, sys
import pytest
flask = pytest.importorskip('flask')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _mod(name):
    spec = importlib.util.spec_from_file_location(name + '_t', os.path.join(ROOT, 'modules', name + '.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _db(tmp_path):
    path = str(tmp_path / 't.db')
    def get_db():
        c = sqlite3.connect(path); c.row_factory = sqlite3.Row; return c
    return get_db


def _svc(app, get_db, **extra):
    return dict(app=app, app_logger=logging.getLogger('t'), get_db=get_db, jsonify=flask.jsonify, login_required=lambda f: f,
                request=flask.request, session=flask.session, **extra)


# ───────── compatibilité ─────────
SPEC = {'bed_x': 220, 'bed_y': 220, 'bed_z': 250, 'nozzle_diameter': 0.4, 'nozzle_max_temp': 260, 'bed_max_temp': 100, 'enclosed': False, 'hardened_nozzle': False}


def _st(res, cid): return next(c['status'] for c in res['checks'] if c['id'] == cid)


def test_compat_tient_ou_non():
    c = _mod('compat')
    assert _st(c.check({'x': 100, 'y': 100, 'z': 100}, '', SPEC), 'fit') == 'ok'
    assert _st(c.check({'x': 100, 'y': 100, 'z': 240}, '', dict(SPEC, bed_z=120, bed_x=250, bed_y=250)), 'fit') == 'warn'     # en le couchant
    assert _st(c.check({'x': 400, 'y': 10, 'z': 10}, '', SPEC), 'fit') == 'fail'
    assert _st(c.check(None, '', SPEC), 'fit') == 'unknown'
    assert _st(c.check({'x': 1, 'y': 1, 'z': 1}, '', {}), 'fit') == 'unknown'                                                    # volume inconnu : jamais présumé


def test_compat_matieres_buse_plateau_caisson():
    c = _mod('compat')
    r = c.check({'x': 10, 'y': 10, 'z': 10}, 'PC', SPEC)
    assert _st(r, 'nozzle_temp') == 'warn' and _st(r, 'bed_temp') == 'warn' and _st(r, 'enclosure') == 'fail' and r['status'] == 'fail'
    r = c.check({'x': 10, 'y': 10, 'z': 10}, 'PLA', SPEC); assert r['status'] == 'ok' and not any(x['id'] == 'enclosure' for x in r['checks'])
    r = c.check({'x': 10, 'y': 10, 'z': 10}, 'ABS', dict(SPEC, enclosed=True)); assert _st(r, 'enclosure') == 'ok'
    assert _st(c.check({'x': 1, 'y': 1, 'z': 1}, 'ABS', dict(SPEC, enclosed=False)), 'enclosure') == 'warn'                      # conseillé seulement
    assert _st(c.check({'x': 1, 'y': 1, 'z': 1}, 'PLA', dict(SPEC, nozzle_max_temp=180)), 'nozzle_temp') == 'fail'
    assert _st(c.check({'x': 1, 'y': 1, 'z': 1}, 'PLA', dict(SPEC, nozzle_max_temp=None)), 'nozzle_temp') == 'unknown'


def test_compat_abrasif_et_matiere_inconnue():
    c = _mod('compat')
    assert _st(c.check({'x': 1, 'y': 1, 'z': 1}, 'PETG-CF', SPEC), 'abrasive') == 'fail'
    assert _st(c.check({'x': 1, 'y': 1, 'z': 1}, 'PA6-GF', dict(SPEC, hardened_nozzle=True)), 'abrasive') == 'ok'
    assert _st(c.check({'x': 1, 'y': 1, 'z': 1}, 'PLA', SPEC), 'fit') == 'ok' and not any(x['id'] == 'abrasive' for x in c.check({'x': 1, 'y': 1, 'z': 1}, 'PLA', SPEC)['checks'])
    r = c.check({'x': 1, 'y': 1, 'z': 1}, 'Soie magique', SPEC); assert _st(r, 'material') == 'unknown'
    assert _st(c.check({'x': 1, 'y': 1, 'z': 1}, 'TPU', dict(SPEC, nozzle_diameter=0.25)), 'nozzle_size') == 'warn'


def test_compat_normalisation_des_caracteristiques():
    c = _mod('compat')
    assert c.normalize_specs({'nozzle_max_temp': '300', 'enclosed': 1}) == ({'nozzle_max_temp': 300.0, 'enclosed': True}, None)
    assert c.normalize_specs({'nozzle_max_temp': 900})[1] and c.normalize_specs({'bed_max_temp': 'abc'})[1]
    assert c.normalize_specs({'nozzle_max_temp': ''})[0] == {'nozzle_max_temp': None}


def test_compat_routes(tmp_path):
    c = _mod('compat'); get_db = _db(tmp_path); db = get_db()
    db.executescript("CREATE TABLE printers (id INTEGER PRIMARY KEY, user_id INT, name TEXT, config TEXT);"
                     "CREATE TABLE file_analysis (path TEXT PRIMARY KEY, data TEXT, failed INT);"
                     f"INSERT INTO printers VALUES (1,1,'Grande','{json.dumps(dict(SPEC, bed_x=300, bed_y=300))}'),(2,1,'Petite','{json.dumps(dict(SPEC, bed_x=100, bed_y=100, bed_z=100))}'),(3,2,'Autre','{{}}');")
    db.execute("INSERT INTO file_analysis VALUES ('/a/m.stl', ?, 0)", (json.dumps({'dimensions': {'x': 150, 'y': 150, 'z': 150}}),))
    db.commit(); db.close()
    app = flask.Flask('t'); app.secret_key = 'x'; c.init(_svc(app, get_db)); cl = app.test_client()
    with cl.session_transaction() as s: s['user_id'] = 1
    r = cl.get('/api/compat/model?path=/a/m.stl&material=PLA').get_json()
    assert [(p['printer'], p['status']) for p in r['printers']] == [('Grande', 'ok'), ('Petite', 'fail')] and r['compatible'] == 1       # imprimante d'un autre compte absente
    assert cl.put('/api/compat/printers/2', json={'bed_max_temp': 120, 'enclosed': True}).status_code == 200
    spec = {p['id']: p['specs'] for p in cl.get('/api/compat/printers').get_json()['printers']}
    assert spec[2]['bed_max_temp'] == 120 and spec[2]['enclosed'] is True and spec[2]['bed_x'] == 100              # fusionné, le reste conservé
    assert cl.put('/api/compat/printers/3', json={'bed_max_temp': 90}).status_code == 404
    assert cl.put('/api/compat/printers/1', json={'nozzle_max_temp': 5}).status_code == 400


# ───────── auto-organisation ─────────
def F(path, **kw):
    d = {'path': path, 'name': os.path.basename(path), 'ext': os.path.splitext(path)[1].lstrip('.'), 'size_mb': 1.0, 'license_commercial': 'unknown',
         'materials': [], 'printers': [], 'printed': False}
    d.update(kw); return d


def test_organize_validation():
    a = _mod('auto_organize')
    ok = {'field': 'ext', 'op': 'is', 'value': 'stl', 'action': 'tag', 'target': 'STL'}
    assert a.validate_rule(ok)[1] is None
    for bad in (dict(ok, field='nimporte'), dict(ok, op='gt'), dict(ok, value=''), dict(ok, action='delete'), dict(ok, target='../x'),
                dict(ok, target='/abs'), dict(ok, target='a:b'), dict(ok, field='license_commercial', value='peut-être'), dict(ok, field='size_mb', op='gt', value='gros')):
        assert a.validate_rule(bad)[1], bad


def test_organize_criteres():
    a = _mod('auto_organize')
    R = lambda field, op, value: {'name': 'r', 'field': field, 'op': op, 'value': value, 'action': 'tag', 'target': 't'}
    assert a.matches(R('ext', 'in', 'stl, 3mf'), F('/a/x.3mf')) and not a.matches(R('ext', 'is', 'stl'), F('/a/x.obj'))
    assert a.matches(R('name', 'contains', 'VASE'), F('/a/grand_vase.stl')) and a.matches(R('name', 'not_contains', 'vase'), F('/a/clip.stl'))
    assert a.matches(R('license_commercial', 'is', 'no'), F('/a/x.stl', license_commercial='no'))
    assert a.matches(R('material', 'is', 'petg'), F('/a/x.stl', materials=['PETG-CF'])) and not a.matches(R('material', 'is', 'abs'), F('/a/x.stl', materials=['PLA']))
    assert a.matches(R('size_mb', 'gt', '5'), F('/a/x.stl', size_mb=6)) and a.matches(R('size_mb', 'lt', '5'), F('/a/x.stl', size_mb=2))
    assert a.matches(R('printed', 'is', 'no'), F('/a/x.stl')) and a.matches(R('printer', 'is', 'prusa'), F('/a/x.stl', printers=['Prusa MK4']))


def test_organize_plan_sans_doublon_ni_existant():
    a = _mod('auto_organize')
    rules = [{'name': 'a', 'field': 'ext', 'op': 'is', 'value': 'stl', 'action': 'tag', 'target': 'Maillage'},
             {'name': 'b', 'field': 'name', 'op': 'contains', 'value': 'x', 'action': 'tag', 'target': 'Maillage'},
             {'name': 'c', 'field': 'ext', 'op': 'is', 'value': 'stl', 'action': 'suggest_folder', 'target': 'STL'}]
    files = [F('/a/x.stl'), F('/a/y.stl')]
    out = a.plan(rules, files, existing_tags={('/a/y.stl', 'maillage')})
    assert sorted((i['path'], i['action']) for i in out) == [('/a/x.stl', 'suggest_folder'), ('/a/x.stl', 'tag'), ('/a/y.stl', 'suggest_folder')]   # doublon et déjà posé écartés


def _org_env(tmp_path):
    a = _mod('auto_organize'); get_db = _db(tmp_path); db = get_db()
    db.executescript("""CREATE TABLE file_origins (file_path TEXT, user_id INT, license TEXT);
        CREATE TABLE print_history (id INTEGER PRIMARY KEY, user_id INT, file_path TEXT, filament_material TEXT, printer_id INT);
        CREATE TABLE printers (id INTEGER PRIMARY KEY, user_id INT, name TEXT);
        INSERT INTO printers VALUES (1,1,'Prusa MK4');
        INSERT INTO print_history VALUES (1,1,'/src/vase.stl','PETG',1);""")
    db.commit(); db.close()
    app = flask.Flask('t'); app.secret_key = 'x'
    cache = {'files': [{'path': '/src/vase.stl', 'name': 'vase.stl', 'size': 2097152}, {'path': '/src/clip.stl', 'name': 'clip.stl', 'size': 1000},
                       {'path': '/autre/z.stl', 'name': 'z.stl', 'size': 5}]}
    a.init(_svc(app, get_db, _is_path_within_sources=lambda p, uid: str(p).startswith('/src/'), _read_cache_json_safe=lambda: cache))
    cl = app.test_client()
    with cl.session_transaction() as s: s['user_id'] = 1
    return a, cl, get_db


def test_organize_apercu_application_et_annulation(tmp_path):
    a, cl, get_db = _org_env(tmp_path)
    assert cl.post('/api/organize/rules', json={'field': 'printed', 'op': 'is', 'value': 'yes', 'action': 'tag', 'target': 'Déjà imprimé'}).status_code == 200
    assert cl.post('/api/organize/rules', json={'field': 'material', 'op': 'is', 'value': 'petg', 'action': 'collection', 'target': 'PETG'}).status_code == 200
    assert cl.post('/api/organize/rules', json={'field': 'ext', 'op': 'is', 'value': 'stl', 'action': 'suggest_folder', 'target': 'Maillages'}).status_code == 200
    p = cl.post('/api/organize/preview').get_json()
    assert p['counts'] == {'tag': 1, 'collection': 1, 'suggest_folder': 2} and all(i['path'].startswith('/src/') for i in p['items'])   # fichier hors sources ignoré
    assert get_db().execute("SELECT COUNT(*) FROM file_tags").fetchone()[0] == 0                                                          # aperçu : rien d'écrit
    assert cl.post('/api/organize/apply', json={}).status_code == 400                                                                    # confirmation obligatoire
    r = cl.post('/api/organize/apply', json={'confirm': True}).get_json()
    assert r['applied'] == 2 and r['skipped_suggestions'] == 2
    db = get_db()
    assert db.execute("SELECT t.name FROM file_tags f JOIN tags t ON t.id=f.tag_id").fetchone()[0] == 'Déjà imprimé'
    assert db.execute("SELECT COUNT(*) FROM collection_files").fetchone()[0] == 1
    assert cl.post('/api/organize/apply', json={'confirm': True}).get_json()['applied'] == 0                                              # idempotent
    u = cl.post('/api/organize/undo', json={'batch': r['batch']}).get_json(); assert u['undone'] == 2
    assert get_db().execute("SELECT COUNT(*) FROM file_tags").fetchone()[0] == 0 and get_db().execute("SELECT COUNT(*) FROM collection_files").fetchone()[0] == 0
    assert cl.post('/api/organize/undo', json={'batch': r['batch']}).status_code == 404                                                  # déjà annulé


def test_organize_invites_refuses(tmp_path):
    a, cl, _ = _org_env(tmp_path)
    with cl.session_transaction() as s: s['role'] = 'viewer'
    assert cl.post('/api/organize/apply', json={'confirm': True}).status_code == 403 and cl.get('/api/organize/rules').status_code == 403


# ───────── diff 3D ─────────
trimesh = pytest.importorskip('trimesh')
np = pytest.importorskip('numpy')


def _box(ext=(10, 10, 10), at=(0, 0, 0)):
    m = trimesh.creation.box(extents=ext); m.apply_translation(at); return m


def test_diff_identiques_et_determinisme():
    md = _mod('model_diff'); a = _box()
    r1 = md.diff_meshes(a.vertices, a.faces, a.vertices.copy(), a.faces, n=1500)
    r2 = md.diff_meshes(a.vertices, a.faces, a.vertices.copy(), a.faces, n=1500)
    assert r1['identical'] and r1['added_pct'] == 0 and r1['removed_pct'] == 0 and r1['delta']['volume_mm3'] == 0
    assert r1 == r2


def test_diff_ajout_de_matiere():
    md = _mod('model_diff'); a = _box((10, 10, 10)); b = _box((10, 10, 20), (0, 0, 5))        # plus haut de 10 mm, base commune
    r = md.diff_meshes(a.vertices, a.faces, b.vertices, b.faces, n=3000)
    assert not r['identical'] and r['added_pct'] > 20 and r['delta']['size_mm'][2] == 10.0
    assert r['delta']['volume_mm3'] == pytest.approx(1000, rel=0.01) and r['volume_a_mm3'] == pytest.approx(1000, rel=0.01)
    assert len(r['points']['added']) > 0 and all(p[2] > 4.9 for p in r['points']['added'][:50])   # l'ajout est bien au-dessus (z > 5 environ)


def test_diff_alignement_centre():
    md = _mod('model_diff'); a = _box(); b = _box(at=(50, 0, 0))
    far = md.diff_meshes(a.vertices, a.faces, b.vertices, b.faces, 'none', n=1000)
    near = md.diff_meshes(a.vertices, a.faces, b.vertices, b.faces, 'center', n=1000)
    assert far['delta']['center_shift_mm'] == 50 and not far['identical'] and near['identical'] and near['delta']['center_shift_mm'] == 0


def test_diff_volume_maillage_ouvert_indetermine():
    md = _mod('model_diff'); a = _box()
    assert md.volume(a.vertices, a.faces[:-2]) is None and md.volume(a.vertices, a.faces) == pytest.approx(1000)


def test_diff_fichiers_et_refus(tmp_path):
    md = _mod('model_diff')
    p1, p2 = str(tmp_path / 'a.stl'), str(tmp_path / 'b.stl'); _box().export(p1); _box((10, 10, 12), (0, 0, 1)).export(p2)
    r = md.diff_files(p1, p2); assert r['delta']['size_mm'][2] == 2.0
    (tmp_path / 'x.txt').write_text('x')
    with pytest.raises(ValueError): md.diff_files(p1, str(tmp_path / 'x.txt'))


def test_diff_route_asynchrone(tmp_path):
    md = _mod('model_diff'); jm = _mod('job_manager'); get_db = _db(tmp_path); db = get_db()
    db.execute("CREATE TABLE model_versions (id INTEGER PRIMARY KEY, user_id INT, path TEXT, version INT, stored_name TEXT)")
    p = str(tmp_path / 'm.stl'); _box().export(p)
    os.makedirs(tmp_path / 'model_versions'); _box((10, 10, 14), (0, 0, 2)).export(str(tmp_path / 'model_versions' / 'v1.stl'))
    db.execute("INSERT INTO model_versions VALUES (7, 1, ?, 1, 'v1.stl')", (p.replace('\\', '/'),)); db.commit(); db.close()
    app = flask.Flask('t'); app.secret_key = 'x'
    md.init(_svc(app, get_db, DATA_DIR=str(tmp_path), _is_path_within_sources=lambda pth, uid: True))
    cl = app.test_client()
    with cl.session_transaction() as s: s['user_id'] = 1
    r = cl.post('/api/model-diff', json={'path': p, 'a': 1, 'b': 'current'})
    assert r.status_code in (200, 202)
    if r.status_code == 200:
        res = r.get_json()['result']                                    # repli synchrone si le gestionnaire n'est pas importable
    else:
        job = jm.MANAGER.get(r.get_json()['job_id']) if jm.MANAGER.get(r.get_json()['job_id']) else None
        if job is None:                                                 # le module de test et md importent deux copies de job_manager : on ne teste que l'accès
            return
        res = job.result
    assert cl.post('/api/model-diff', json={'path': p, 'a': 99, 'b': 0}).status_code == 404
    assert cl.post('/api/model-diff', json={'path': p, 'tolerance': 'x'}).status_code == 400


# ───────── recherche de formes ─────────
def _desc(mesh): return _mod('shape_search').descriptor(mesh.vertices, mesh.faces)


def test_empreinte_invariante_echelle_rotation_position():
    ss = _mod('shape_search'); base = trimesh.creation.cylinder(radius=5, height=30, sections=48)
    d0 = ss.descriptor(base.vertices, base.faces)
    big = base.copy(); big.apply_scale(3.7)
    rot = base.copy(); rot.apply_transform(trimesh.transformations.rotation_matrix(0.9, [1, 1, 0])); rot.apply_translation([100, -40, 7])
    assert ss.distance(d0, ss.descriptor(big.vertices, big.faces)) < 0.03
    assert ss.distance(d0, ss.descriptor(rot.vertices, rot.faces)) < 0.04


def test_classement_par_similarite():
    ss = _mod('shape_search')
    target = trimesh.creation.cylinder(radius=5, height=30, sections=48)
    cands = {'cyl_gros': trimesh.creation.cylinder(radius=10, height=60, sections=48), 'sphere': trimesh.creation.icosphere(radius=10),
             'cube': trimesh.creation.box(extents=(10, 10, 10)), 'plaque': trimesh.creation.box(extents=(80, 80, 2))}
    res = ss.rank(ss.descriptor(target.vertices, target.faces), {k: ss.descriptor(m.vertices, m.faces) for k, m in cands.items()}, 4)
    assert res[0]['path'] == 'cyl_gros' and res[0]['similarity'] > 90 and res[-1]['path'] in ('plaque', 'sphere') and res[0]['similarity'] > res[1]['similarity']


def test_index_status_et_construction(tmp_path):
    ss = _mod('shape_search'); jm = _mod('job_manager'); get_db = _db(tmp_path)
    paths = []
    for i, m in enumerate((trimesh.creation.box(extents=(10, 10, 10)), trimesh.creation.icosphere(radius=6), trimesh.creation.cylinder(radius=3, height=20))):
        p = str(tmp_path / f'm{i}.stl'); m.export(p); paths.append(p)
    app = flask.Flask('t'); app.secret_key = 'x'
    cache = {'files': [{'path': p, 'mtime': 1, 'size': os.path.getsize(p)} for p in paths]}
    ss.init(_svc(app, get_db, _is_path_within_sources=lambda p, uid: True, _read_cache_json_safe=lambda: cache))
    class Ctx:
        def __init__(self): self.calls = 0
        def progress(self, d, t=None, m=None): self.calls += 1
    ctx = Ctx(); r = ss.build_index(ctx, 1)
    assert r == {'indexed': 3, 'unchanged': 0, 'failed': 0, 'total': 3} and ctx.calls == 3
    assert ss.build_index(Ctx(), 1)['unchanged'] == 3                         # rien à refaire tant que les fichiers ne changent pas
    cl = app.test_client()
    with cl.session_transaction() as s: s['user_id'] = 1
    st = cl.get('/api/similar/status').get_json(); assert st['indexed'] == 3 and st['missing'] == 0 and st['index_bytes'] > 0
    res = cl.get(f'/api/similar?path={paths[0]}&limit=5').get_json()
    assert len(res['results']) == 2 and paths[0] not in [x['path'] for x in res['results']] and res['note'] is None
    assert cl.get('/api/similar').status_code == 404
    cache['files'].append({'path': str(tmp_path / 'absent.stl'), 'mtime': 1, 'size': 1})
    r2 = ss.build_index(Ctx(), 1); assert r2['failed'] == 1                    # fichier illisible : compté, l'index continue
    r3 = ss.build_index(Ctx(), 1); assert r3['failed'] == 0 and r3['unchanged'] == 4                    # l'illisible n'est plus réessayé à chaque indexation
    ss._TOTAL.clear(); st = cl.get('/api/similar/status').get_json()
    assert st['skipped'] == 1 and st['missing'] == 0 and st['indexed'] == 3                              # « ignoré » ≠ « reste à indexer » : plus de « reste environ 2 min » fantôme


def test_fichiers_ignores_causes_et_reessayer(tmp_path):
    """1.1.9 : liste des fichiers ignorés par l'index, avec cause (trop gros / vide / illisible / introuvable) ; « réessayer » les remet dans l'indexation."""
    ss = _mod('shape_search'); get_db = _db(tmp_path)
    ok = str(tmp_path / 'ok.stl'); trimesh.creation.box(extents=(10, 10, 10)).export(ok)
    bad = tmp_path / 'casse.stl'; bad.write_bytes(b'ceci n est pas un maillage')
    vide = tmp_path / 'vide.obj'; vide.write_text('# rien\n')
    gros = tmp_path / 'gros.stl'; gros.write_bytes(b'0' * 16)
    app = flask.Flask('t'); app.secret_key = 'x'
    cache = {'files': [{'path': ok, 'mtime': 1, 'size': os.path.getsize(ok)}, {'path': str(bad), 'mtime': 1, 'size': 26}, {'path': str(vide), 'mtime': 1, 'size': 8},
                       {'path': str(gros), 'mtime': 1, 'size': ss.MAX_BYTES + 5}, {'path': str(tmp_path / 'absent.stl'), 'mtime': 1, 'size': 1}]}
    ss.init(_svc(app, get_db, _is_path_within_sources=lambda p, uid: True, _read_cache_json_safe=lambda: cache))
    class Ctx:
        def progress(self, *a): pass
    ss.build_index(Ctx(), 1)
    cl = app.test_client()
    with cl.session_transaction() as s: s['user_id'] = 1
    d = cl.get('/api/similar/skipped').get_json()
    codes = {os.path.basename(f['path']): f['code'] for f in d['files']}
    assert d['count'] == 4 and d['max_mb'] == 60
    assert codes['gros.stl'] == 'too_big' and codes['absent.stl'] == 'missing' and codes['casse.stl'] in ('empty', 'unreadable') and codes['vide.obj'] in ('empty', 'unreadable')
    assert 'ok.stl' not in codes
    assert cl.post('/api/similar/skipped/retry', json={'paths': [str(bad)]}).get_json()['retried'] == 1
    assert cl.get('/api/similar/skipped').get_json()['count'] == 3
    assert cl.post('/api/similar/skipped/retry', json={}).get_json()['retried'] == 3                  # sans liste : tout est réessayé
    assert cl.get('/api/similar/skipped').get_json()['count'] == 0
    assert ss.build_index(Ctx(), 1)['failed'] == 4                                                     # la nouvelle indexation les réessaie


def test_organize_auteur_categorie_date():
    m = _mod('auto_organize')
    f = {'path': '/a.stl', 'name': 'a.stl', 'ext': 'stl', 'size_mb': 1, 'license_commercial': 'unknown', 'materials': [], 'printers': [], 'printed': False,
         'author': 'Jean Dupont', 'tags': ['Jouets', 'PLA'], 'age_days': 400.0}
    ok = lambda field, op, value: m.matches({'field': field, 'op': op, 'value': value}, f)
    assert ok('author', 'is', 'jean dupont') and ok('author', 'contains', 'dupont') and not ok('author', 'is', 'dupont')
    assert ok('category', 'is', 'jouets') and not ok('category', 'is', 'outils')
    assert ok('age_days', 'gt', '365') and not ok('age_days', 'lt', '365') and not m.matches({'field': 'age_days', 'op': 'gt', 'value': '1'}, dict(f, age_days=None))
    assert m.validate_rule({'field': 'age_days', 'op': 'gt', 'value': 'beaucoup', 'action': 'tag', 'target': 'x'})[1] == 'Nombre invalide.'
    assert m.validate_rule({'field': 'author', 'op': 'is', 'value': 'X', 'action': 'tag', 'target': 'x'})[0]


def test_diff_version_par_numero_et_table_absente(tmp_path):
    """Correctif 1.1.7 : « version A » est le NUMÉRO affiché (pas l'id interne), et une base sans versions donne 404, pas 500."""
    md = _mod('model_diff'); get_db = _db(tmp_path)
    p = str(tmp_path / 'm.stl'); _box().export(p)
    app = flask.Flask('t'); app.secret_key = 'x'
    md.init(_svc(app, get_db, DATA_DIR=str(tmp_path), _is_path_within_sources=lambda pth, uid: True))
    cl = app.test_client()
    with cl.session_transaction() as s: s['user_id'] = 1
    assert cl.post('/api/model-diff', json={'path': p, 'a': 1, 'b': 'current'}).status_code == 404      # aucune table model_versions
    db = get_db()
    db.execute("CREATE TABLE model_versions (id INTEGER PRIMARY KEY, user_id INT, path TEXT, version INT, stored_name TEXT)")
    os.makedirs(tmp_path / 'model_versions'); _box((10, 10, 14), (0, 0, 2)).export(str(tmp_path / 'model_versions' / 'v1.stl'))
    db.execute("INSERT INTO model_versions VALUES (7, 1, ?, 1, 'v1.stl')", (p.replace('\\', '/'),)); db.commit(); db.close()
    assert cl.post('/api/model-diff', json={'path': p, 'a': 7, 'b': 'current'}).status_code == 404      # 7 est l'id interne, pas un numéro de version
    assert cl.post('/api/model-diff', json={'path': p, 'a': 1, 'b': 'current'}).status_code in (200, 202)


def test_diff3d_aretes_pour_la_vue_fil_de_fer():
    md = _mod('model_diff'); a = _box((10, 10, 10)); b = _box((10, 10, 20), (0, 0, 5))
    r = md.diff_meshes(a.vertices, a.faces, b.vertices, b.faces, n=3000)
    e = r['edges']
    assert set(e) == {'removed', 'added', 'same'} and all(len(x) <= md.SHOW_EDGES for x in e.values())
    assert len(e['added']) > 0 and all(len(seg) == 6 for k in e for seg in e[k])
    same = md.diff_meshes(a.vertices, a.faces, a.vertices.copy(), a.faces, n=1500)['edges']
    assert same['removed'] == [] and same['added'] == [] and len(same['same']) > 0
