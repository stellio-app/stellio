"""1.1.7 — vérification avant impression : surplombs, base, supports estimés, orientation conseillée (maillages construits à la main)."""
import importlib.util, io, logging, os, sqlite3
import pytest
np = pytest.importorskip('numpy'); trimesh = pytest.importorskip('trimesh'); flask = pytest.importorskip('flask'); pytest.importorskip('manifold3d')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _mod():
    spec = importlib.util.spec_from_file_location('print_check_t', os.path.join(ROOT, 'modules', 'print_check.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def _box(x, y, z, at=(0, 0, 0)):
    b = trimesh.creation.box(extents=(x, y, z)); b.apply_translation(at); return b


def _tee(upright=True):
    """Un « T » : pied 10×10×30 et plateau 50×50×5. Pied en bas = grand surplomb ; plateau à plat = aucun."""
    t = trimesh.boolean.union([_box(10, 10, 30, (0, 0, 15)), _box(50, 50, 5, (0, 0, 32.5))], engine='manifold')   # une seule coque : pas de faces internes
    if not upright:
        t.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    return t


def test_rotation_amene_la_face_au_plateau():
    m = _mod()
    for d in ([0, 0, -1], [1, 0, 0], [0, 1, 0], [0.3, -0.5, -0.8], [0, 0, 1]):
        R = m.rotation_to_down(d)
        out = R @ (np.array(d) / np.linalg.norm(d))
        assert np.allclose(out, [0, 0, -1], atol=1e-6) and abs(np.linalg.det(R) - 1) < 1e-9


def test_cube_aucun_probleme():
    m = _mod()
    r = m.analyze(_box(20, 20, 20))
    assert r['verdict'] == 'ok' and r['issues'] == []
    c = r['current']
    assert c['overhang_area'] == 0 and c['support_volume_cm3'] == 0 and c['base_ratio'] == 1 and c['size'] == [20, 20, 20]
    assert abs(r['volume_cm3'] - 8) < 1e-6


def test_tee_pied_en_bas_demande_des_supports_et_la_retourne():
    m = _mod()
    r = m.analyze(_tee(True))
    codes = [i['code'] for i in r['issues']]
    assert 'overhangs' in codes and 'better_orientation' in codes and r['verdict'] == 'warning'
    assert r['current']['overhang_area'] > 2000 * 0.8                      # dessous du plateau 50×50 moins le pied
    assert r['best']['metrics']['support_volume_cm3'] == 0 and r['best']['down'] == [0.0, 0.0, 1.0]   # le plateau repose sur le lit
    assert r['gain'] >= 0.9
    r2 = m.analyze(_tee(False))                                             # déjà à l'endroit : rien à conseiller
    assert 'overhangs' not in [i['code'] for i in r2['issues']] and 'better_orientation' not in [i['code'] for i in r2['issues']]


def test_cone_pointe_en_bas():
    m = _mod()
    cone = trimesh.creation.cone(radius=30, height=15)                      # évasé : parois à 63° de la verticale
    cone.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))        # pointe vers le bas
    r = m.analyze(cone)
    codes = [i['code'] for i in r['issues']]
    assert 'overhangs' in codes and 'small_base' in codes
    assert r['best']['metrics']['base_ratio'] > 0.5 and r['best']['metrics']['support_volume_cm3'] == 0


def test_angle_de_surplomb_reglable():
    m = _mod()
    cone = trimesh.creation.cone(radius=10, height=20)                      # parois à 26,6° de la verticale
    cone.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))        # pointe vers le bas
    assert m.analyze(cone, angle=45)['current']['overhang_area'] == 0       # acceptable sans support à 45°
    assert m.analyze(cone, angle=20)['current']['overhang_area'] > 0        # plus exigeant : surplomb


def test_elancement_et_volume_d_impression():
    m = _mod()
    r = m.analyze(_box(5, 5, 60), bed=[200, 200, 200])
    assert 'tall_thin' in [i['code'] for i in r['issues']]
    assert r['best']['metrics']['height'] <= 5.0 + 1e-6                     # couchée : plus d'élancement
    big = m.analyze(_box(300, 300, 300), bed=[200, 200, 200])
    assert big['verdict'] == 'error' and 'too_big' in [i['code'] for i in big['issues']]
    # ne rentre que couchée : le conseil respecte le volume
    long = m.analyze(_box(10, 10, 250), bed=[260, 260, 100])
    assert long['best']['fits'] and long['best']['metrics']['height'] <= 100
    assert 'fits_only_rotated' in [i['code'] for i in long['issues']]


def test_maillage_non_etanche_signale():
    m = _mod()
    b = _box(10, 10, 10); b.update_faces(np.arange(len(b.faces) - 2))       # on retire deux triangles
    assert 'not_watertight' in [i['code'] for i in m.analyze(b)['issues']]


def test_copie_orientee_posee_a_zero():
    m = _mod()
    data = m.oriented_stl_bytes(_tee(True), [0, 0, 1])
    out = trimesh.load(io.BytesIO(data), file_type='stl')
    assert abs(out.bounds[0][2]) < 1e-4 and abs(out.bounds[1][2] - 35) < 1e-4
    assert m.analyze(out)['current']['overhang_area'] == 0


def _env(tmp_path, ok=True):
    m = _mod()
    db = str(tmp_path / 'd.db')
    c = sqlite3.connect(db); c.execute("CREATE TABLE printers(id INTEGER PRIMARY KEY, user_id INT, config TEXT)")
    c.execute("INSERT INTO printers VALUES (1,1,'{\"bed_x\":220,\"bed_y\":220,\"bed_z\":250}')"); c.commit(); c.close()
    def get_db():
        x = sqlite3.connect(db); x.row_factory = sqlite3.Row; return x
    app = flask.Flask('pc'); app.secret_key = 'k'
    m.init(dict(app=app, app_logger=logging.getLogger('t'), get_db=get_db, jsonify=flask.jsonify, login_required=lambda f: f,
                request=flask.request, session=flask.session, _is_path_within_sources=lambda p, uid: ok))
    m._load = lambda native: trimesh.load(native, force='mesh')
    cl = app.test_client()
    with cl.session_transaction() as s:
        s['user_id'] = 1
    return m, cl


def test_routes(tmp_path):
    m, cl = _env(tmp_path)
    p = tmp_path / 'tee.stl'; _tee(True).export(str(p))
    r = cl.post('/api/print-check', json={'path': str(p), 'printer_id': 1})
    d = r.get_json()
    assert r.status_code == 200 and d['verdict'] == 'warning' and d['bed'] == [220.0, 220.0, 250.0] and d['name'] == 'tee.stl'
    assert cl.post('/api/print-check', json={'path': str(p), 'bed': {'x': 30, 'y': 30, 'z': 30}}).get_json()['verdict'] == 'error'
    down = ','.join(str(x) for x in d['best']['down'])
    g = cl.get('/api/print-check/oriented', query_string={'path': str(p), 'down': down})
    assert g.status_code == 200 and 'tee_oriented.stl' in g.headers['Content-Disposition']
    assert abs(trimesh.load(io.BytesIO(g.data), file_type='stl').bounds[1][2] - 35) < 1e-3
    assert cl.get('/api/print-check/oriented', query_string={'path': str(p), 'down': 'a,b'}).status_code == 400


def test_routes_refus(tmp_path):
    m, cl = _env(tmp_path)
    assert cl.post('/api/print-check', json={}).status_code == 400
    assert cl.post('/api/print-check', json={'path': '/x/a.txt'}).status_code == 400
    assert cl.post('/api/print-check', json={'path': str(tmp_path / 'absent.stl')}).status_code == 404
    m2, cl2 = _env(tmp_path / 'sub' if (tmp_path / 'sub').mkdir() is None else tmp_path, ok=False)
    p = tmp_path / 'a.stl'; _box(5, 5, 5).export(str(p))
    assert cl2.post('/api/print-check', json={'path': str(p)}).status_code == 403
    assert cl2.get('/api/print-check/oriented', query_string={'path': str(p)}).status_code == 403
