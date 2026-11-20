"""1.1.7 — nesting de la vraie géométrie : pièces concaves imbriquées, rotation libre, contrôle et export."""
import importlib.util, os, zipfile, io
import pytest
flask = pytest.importorskip('flask'); np = pytest.importorskip('numpy'); trimesh = pytest.importorskip('trimesh')
shapely = pytest.importorskip('shapely'); pytest.importorskip('scipy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _mod():
    spec = importlib.util.spec_from_file_location('plate_n', __import__('conftest').mod_path('plate_studio'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def _L(h=10):
    """Pièce en L (concave) : 100x100 avec un coin de 60x60 retiré."""
    a = trimesh.creation.box(extents=(100, 40, h)); a.apply_translation((50, 20, h / 2))
    b = trimesh.creation.box(extents=(40, 60, h)); b.apply_translation((20, 70, h / 2))
    return trimesh.util.concatenate([a, b])


def _items(m, mesh, n):
    from shapely import affinity
    g = m.footprint(mesh); x0, y0, _, _ = m._bounds(g); g = affinity.translate(g, -x0, -y0)
    return [{'id': f'L{i}', 'poly': g, 'h': 10} for i in range(n)]


def test_empreinte_concave_et_plus_petite_que_la_boite():
    m = _mod(); g = m.footprint(_L())
    assert abs(g.area - (100 * 40 + 40 * 60)) < 5 and g.area < 100 * 100 * 0.7


def test_imbrication_concave_gagne_de_la_place_et_sans_chevauchement():
    m = _mod(); items = _items(m, _L(), 4); plate = {'w': 170, 'd': 170, 'z': 100}
    r = m.arrange_shapes(items, plate, margin=2, step=90)
    placed = sum(len(p['placements']) for p in r['plates'])
    assert placed == 4 and not r['unplaced'] and r['mode'] == 'shape'
    box = m.arrange([{'id': i['id'], 'w': 100, 'd': 100, 'h': 10} for i in items], plate, margin=2)
    assert len(r['plates']) <= len(box['plates'])
    for p in r['plates']:
        assert not [i for i in m.check_layout({'plate': plate, 'plates': [p]}) if i['issue'] in ('overlap', 'out_of_plate')]


def test_rotation_libre_acceptee_et_export_3mf(tmp_path):
    m = _mod(); mesh = _L(); mesh.export(str(tmp_path / 'l.stl'))
    w, d = m._rotated_extents(mesh, 45)
    assert w == pytest.approx(98.995, abs=0.01) and d > 100                                # L tourné à 45° : boîte différente
    assert m._rotated_extents(mesh, 90)[0] == pytest.approx(100, abs=1e-6)
    ok = m.clean_layout({'plate': {'w': 250, 'd': 250}, 'plates': [{'placements': [{'id': 'a', 'x': 5, 'y': 5, 'w': w, 'd': d, 'h': 10, 'rot': 45}]}]})
    assert ok['plates'][0]['placements'][0]['rot'] == 45


def test_sans_rotation_ne_tourne_jamais():
    m = _mod(); r = m.arrange_shapes(_items(m, _L(), 3), {'w': 400, 'd': 400, 'z': 100}, margin=2, step=0)
    assert all(a['rot'] == 0 for p in r['plates'] for a in p['placements'])


def test_piece_trop_grande_refusee():
    m = _mod(); r = m.arrange_shapes(_items(m, _L(), 1), {'w': 60, 'd': 60, 'z': 100}, margin=0, step=15)
    assert r['unplaced'] and r['unplaced'][0]['reason'] == 'too_large'


def test_determinisme_et_temps():
    import time
    m = _mod(); items = _items(m, _L(), 8); plate = {'w': 256, 'd': 256, 'z': 100}
    t = time.time(); a = m.arrange_shapes(items, plate, margin=2, step=45); dt = time.time() - t
    assert a == m.arrange_shapes(items, plate, margin=2, step=45) and dt < 30


def _app(tmp_path):
    import logging
    m = _mod(); app = flask.Flask('pn'); app.secret_key = 'x'
    m.init(dict(app=app, app_logger=logging.getLogger('t'), jsonify=flask.jsonify, login_required=lambda f: f, request=flask.request, session=flask.session,
                send_file=flask.send_file, _is_path_within_sources=lambda p, uid: str(p).startswith(str(tmp_path))))
    return app


def test_routes_mode_forme_controle_et_export(tmp_path):
    _L().export(str(tmp_path / 'l.stl'))
    app = _app(tmp_path); cl = app.test_client()
    with cl.session_transaction() as s_: s_['user_id'] = 1
    p = str(tmp_path / 'l.stl'); plate = {'w': 170, 'd': 170, 'z': 100}
    r = cl.post('/api/plate/arrange', json={'paths': [p], 'copies': 4, 'plate': plate, 'margin': 2}).get_json()
    assert r['ok'] and r['mode'] == 'shape' and r['issues'] == [] and sum(len(x['placements']) for x in r['plates']) == 4
    assert p in r['shapes'] and r['shapes'][p]['outline']
    rb = cl.post('/api/plate/arrange', json={'paths': [p], 'copies': 4, 'plate': plate, 'margin': 2, 'mode': 'box'}).get_json()
    assert rb['mode'] != 'shape' and len(r['plates']) <= len(rb['plates'])
    # la disposition retouchée (avec contours) repart telle quelle ; une rotation libre est acceptée
    assert cl.post('/api/plate/check', json={'plate': plate, 'plates': r['plates']}).get_json()['issues'] == []
    e = cl.post('/api/plate/export', json={'paths': [p], 'copies': 4, 'layout': {'plate': plate, 'plates': r['plates']}, 'plate_index': 1})
    assert e.status_code == 200 and zipfile.is_zipfile(io.BytesIO(e.data))
    free = {'plate': {'w': 250, 'd': 250, 'z': 100}, 'plates': [{'index': 1, 'placements': [{'id': p, 'x': 20, 'y': 20, 'w': 98.99, 'd': 141.4, 'h': 10, 'rot': 45}]}]}
    e = cl.post('/api/plate/export', json={'paths': [p], 'layout': free, 'plate_index': 1})
    assert e.status_code == 200 and zipfile.is_zipfile(io.BytesIO(e.data))


def test_route_rotation_serveur(tmp_path):
    _L().export(str(tmp_path / 'l.stl'))
    app = _app(tmp_path); cl = app.test_client()
    with cl.session_transaction() as s_: s_['user_id'] = 1
    p = str(tmp_path / 'l.stl')
    r = cl.post('/api/plate/rotate', json={'id': p + '#3', 'rot': 90}).get_json()
    assert r['ok'] and r['w'] == pytest.approx(100, abs=0.01) and r['outline']
    r = cl.post('/api/plate/rotate', json={'id': p, 'rot': 45}).get_json()
    assert r['w'] == pytest.approx(98.995, abs=0.02) and r['rot'] == 45
    assert cl.post('/api/plate/rotate', json={'id': p, 'rot': 'abc'}).status_code == 400
    assert cl.post('/api/plate/rotate', json={'id': str(tmp_path / 'absent.stl'), 'rot': 0}).status_code in (400, 404)


def test_dossier_avec_diese_et_exemplaires_par_modele(tmp_path):
    d = tmp_path / 'biplane-297#588'; d.mkdir()
    _L().export(str(d / 'a.STL')); trimesh.creation.box(extents=(40, 30, 10)).export(str(tmp_path / 'b.stl'))
    app = _app(tmp_path); cl = app.test_client()
    with cl.session_transaction() as s_: s_['user_id'] = 1
    a, b = str(d / 'a.STL'), str(tmp_path / 'b.stl'); plate = {'w': 300, 'd': 300, 'z': 400}
    r = cl.post('/api/plate/arrange', json={'paths': [a, b], 'counts': {a: 3, b: 2}, 'plate': plate, 'margin': 10}).get_json()
    ids = sorted(x['id'] for p in r['plates'] for x in p['placements'])
    assert r['ok'] and len(ids) == 5 and ids.count(a) == 0 and sum(i.startswith(a + '#') for i in ids) == 3 and r['issues'] == []
    assert cl.post('/api/plate/rotate', json={'id': a + '#2', 'rot': 30}).get_json()['ok']          # le « # » du dossier n'est pas un exemplaire
    e = cl.post('/api/plate/export', json={'paths': [a, b], 'layout': {'plate': plate, 'plates': r['plates']}, 'plate_index': 1})
    assert e.status_code == 200
    r2 = cl.post('/api/plate/arrange', json={'paths': [a, a], 'plate': plate}).get_json()           # même pièce saisie deux fois = 2 exemplaires
    assert sum(len(p['placements']) for p in r2['plates']) == 2


def test_jamais_hors_du_plateau_meme_si_la_taille_n_est_pas_multiple_de_la_grille():
    m = _mod(); items = _items(m, _L(), 9)
    for plate in ({'w': 300, 'd': 300, 'z': 400}, {'w': 257, 'd': 301, 'z': 100}, {'w': 180, 'd': 233, 'z': 100}):
        r = m.arrange_shapes(items, plate, margin=10, step=45)
        assert not [i for i in m.check_layout(r) if i['issue'] == 'out_of_plate'], plate
        assert sum(len(p['placements']) for p in r['plates']) + len(r['unplaced']) == 9
