"""1.1.7 — atelier multi-modèles : disposition, plateaux multiples, contrôles, export 3MF."""
import importlib.util, io, logging, os, zipfile
import pytest
flask = pytest.importorskip('flask'); np = pytest.importorskip('numpy'); trimesh = pytest.importorskip('trimesh')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _mod():
    spec = importlib.util.spec_from_file_location('plate_t', __import__('conftest').mod_path('plate_studio'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def I(i, w, d, h=10): return {'id': i, 'w': w, 'd': d, 'h': h}


def test_tout_tient_sans_chevauchement():
    m = _mod(); items = [I(i, 40 + (i % 3) * 15, 30 + (i % 4) * 10) for i in range(12)]
    r = m.arrange(items, {'w': 256, 'd': 256, 'z': 200}, margin=4)
    assert not r['unplaced'] and m.check_layout(r) == [] and sum(len(p['placements']) for p in r['plates']) == 12
    for p in r['plates']:
        for a in p['placements']:                                                        # marge respectée entre toutes les paires
            for b in p['placements']:
                if a is not b:
                    gx = max(b['x'] - (a['x'] + a['w']), a['x'] - (b['x'] + b['w'])); gy = max(b['y'] - (a['y'] + a['d']), a['y'] - (b['y'] + b['d']))
                    assert max(gx, gy) >= 4 - 1e-6


def test_plusieurs_plateaux_et_determinisme():
    m = _mod(); items = [I(i, 120, 120) for i in range(9)]
    r = m.arrange(items, {'w': 256, 'd': 256}, margin=2)
    assert len(r['plates']) == 3 and [len(p['placements']) for p in r['plates']] == [4, 4, 1]
    assert r == m.arrange(items, {'w': 256, 'd': 256}, margin=2)


def test_rotation_utile_et_refus_honnetes():
    m = _mod()
    r = m.arrange([I('long', 300, 20)], {'w': 256, 'd': 320}, margin=0, rotate=True)
    assert r['plates'][0]['placements'][0]['rot'] == 90 and not r['unplaced']
    assert m.arrange([I('long', 300, 20)], {'w': 256, 'd': 320}, margin=0, rotate=False)['unplaced'][0]['reason'] == 'too_large'
    r = m.arrange([I('haut', 10, 10, 300), I('ok', 10, 10, 5), I('immense', 500, 500)], {'w': 256, 'd': 256, 'z': 256})
    assert {u['id']: u['reason'] for u in r['unplaced']} == {'haut': 'too_tall', 'immense': 'too_large'} and len(r['plates'][0]['placements']) == 1


def test_controle_dune_disposition_retouchee():
    m = _mod(); r = m.arrange([I('a', 50, 50), I('b', 50, 50)], {'w': 256, 'd': 256})
    pl = r['plates'][0]['placements']; pl[1]['x'], pl[1]['y'] = pl[0]['x'] + 10, pl[0]['y']
    assert [i['issue'] for i in m.check_layout(r)] == ['overlap']
    pl[1]['x'] = 250; assert 'out_of_plate' in [i['issue'] for i in m.check_layout(r)]


def test_export_3mf_valide_et_positions(tmp_path):
    m = _mod(); box = trimesh.creation.box(extents=(20, 10, 5)); box.apply_translation((100, -50, 7))
    entries = [(box, {'id': 'a', 'x': 30, 'y': 40, 'rot': 0}), (box, {'id': 'b<&"', 'x': 100, 'y': 100, 'rot': 90})]
    blob = m.export_3mf(entries, 1)
    z = zipfile.ZipFile(io.BytesIO(blob)); assert set(z.namelist()) == {'[Content_Types].xml', '_rels/.rels', '3D/3dmodel.model'}
    import xml.etree.ElementTree as ET
    root = ET.fromstring(z.read('3D/3dmodel.model')); ns = {'c': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
    objs = root.findall('.//c:object', ns); assert len(objs) == 2
    def bbox(o):
        v = np.array([[float(x.get(k)) for k in 'xyz'] for x in o.findall('.//c:vertex', ns)]); return v.min(0), v.max(0)
    lo, hi = bbox(objs[0]); assert np.allclose(lo, [30, 40, 0]) and np.allclose(hi, [50, 50, 5])        # posé sur Z=0 à la position demandée
    lo, hi = bbox(objs[1]); assert np.allclose(lo, [100, 100, 0]) and np.allclose(hi, [110, 120, 5])    # tourné de 90° : 10×20
    tri = lambda o: np.array([[int(t.get(k)) for k in ('v1', 'v2', 'v3')] for t in o.findall('.//c:triangle', ns)])
    mesh2 = trimesh.Trimesh(vertices=np.array([[float(x.get(k)) for k in 'xyz'] for x in objs[1].findall('.//c:vertex', ns)]), faces=tri(objs[1]))
    assert mesh2.is_watertight and mesh2.volume > 0 and abs(mesh2.volume - 1000) < 1e-3                  # orientation conservée, volume intact
    assert 'b&lt;&amp;&quot;' in z.read('3D/3dmodel.model').decode()                                       # nom échappé


def _app(tmp_path):
    m = _mod(); app = flask.Flask('p'); app.secret_key = 'x'
    m.init(dict(app=app, app_logger=logging.getLogger('t'), jsonify=flask.jsonify, login_required=lambda f: f, request=flask.request, session=flask.session,
                send_file=flask.send_file, _is_path_within_sources=lambda p, uid: str(p).startswith(str(tmp_path))))
    return app


def test_routes(tmp_path):
    for i in range(3): trimesh.creation.box(extents=(60, 40, 10)).export(str(tmp_path / f'b{i}.stl'))
    outside = tmp_path.parent / 'dehors.stl'; trimesh.creation.box().export(str(outside))
    app = _app(tmp_path); cl = app.test_client()
    with cl.session_transaction() as s_: s_['user_id'] = 1
    paths = [str(tmp_path / f'b{i}.stl') for i in range(3)]
    r = cl.post('/api/plate/arrange', json={'paths': paths, 'copies': 2, 'plate': {'w': 150, 'd': 100, 'z': 100}}).get_json()
    assert r['ok'] and sum(len(p['placements']) for p in r['plates']) == 6 and r['issues'] == [] and len(r['plates']) >= 2
    assert cl.post('/api/plate/arrange', json={'paths': [str(outside)]}).status_code == 403
    assert cl.post('/api/plate/arrange', json={'paths': [str(tmp_path / 'absent.stl')]}).status_code == 400
    assert cl.post('/api/plate/arrange', json={'paths': paths + paths, 'copies': 99}).status_code == 400
    assert cl.post('/api/plate/arrange', json={}).status_code == 400
    e = cl.post('/api/plate/export', json={'paths': paths, 'plate_index': 1}); assert e.status_code == 200 and zipfile.is_zipfile(io.BytesIO(e.data))
    assert cl.post('/api/plate/export', json={'paths': paths, 'plate_index': 9}).status_code == 404
    with cl.session_transaction() as s: s['role'] = 'viewer'
    assert cl.post('/api/plate/arrange', json={'paths': paths}).status_code == 403


def test_editeur_controle_et_export_depuis_disposition_manuelle(tmp_path):
    trimesh.creation.box(extents=(60, 40, 10)).export(str(tmp_path / 'a.stl')); trimesh.creation.box(extents=(30, 30, 300)).export(str(tmp_path / 'haute.stl'))
    app = _app(tmp_path); cl = app.test_client()
    with cl.session_transaction() as s_: s_['user_id'] = 1
    a, h = str(tmp_path / 'a.stl'), str(tmp_path / 'haute.stl')
    plate = {'w': 200, 'd': 100, 'z': 100}
    ok = {'plate': plate, 'plates': [{'index': 1, 'placements': [{'id': a, 'x': 5, 'y': 5, 'w': 60, 'd': 40, 'h': 10, 'rot': 0}, {'id': a + '#2', 'x': 100, 'y': 5, 'w': 40, 'd': 60, 'h': 10, 'rot': 90}]}]}
    assert cl.post('/api/plate/check', json=ok).get_json()['issues'] == []
    bad = {'plate': plate, 'plates': [{'index': 1, 'placements': [{'id': 'x', 'x': 0, 'y': 0, 'w': 60, 'd': 40, 'h': 10, 'rot': 0}, {'id': 'y', 'x': 30, 'y': 10, 'w': 60, 'd': 40, 'h': 10, 'rot': 0},
                                                                  {'id': 'z', 'x': 190, 'y': 0, 'w': 60, 'd': 40, 'h': 200, 'rot': 0}]}]}
    kinds = {i['issue'] for i in cl.post('/api/plate/check', json=bad).get_json()['issues']}; assert kinds == {'overlap', 'out_of_plate', 'too_tall'}
    for junk in ({}, {'plates': []}, {'plates': [{'placements': [{'id': 'a', 'x': 'abc', 'y': 0, 'w': 1, 'd': 1}]}]},
                 {'plates': [{'placements': [{'id': 'a', 'x': 0, 'y': 0, 'w': 1, 'd': 1, 'rot': 'abc'}]}]}, {'plates': [{'placements': [{'id': 'a', 'x': float('nan'), 'y': 0, 'w': 1, 'd': 1}]}]}):
        assert cl.post('/api/plate/check', json=junk).status_code == 400
    # export : tailles relues sur les maillages (le navigateur ne peut pas tricher), rotation prise en compte
    e = cl.post('/api/plate/export', json={'layout': ok, 'plate_index': 1}); assert e.status_code == 200
    xml = zipfile.ZipFile(io.BytesIO(e.data)).read('3D/3dmodel.model').decode()
    xs = [float(v) for v in __import__('re').findall(r' x="([-0-9.]+)"', xml)]; ys = [float(v) for v in __import__('re').findall(r' y="([-0-9.]+)"', xml)]
    assert xml.count('<object ') == 2 and abs(min(xs) - 5) < 1e-3 and abs(max(xs) - 140) < 1e-3 and abs(max(ys) - 65) < 1e-3
    liar = {'plate': plate, 'plates': [{'index': 1, 'placements': [{'id': a, 'x': 0, 'y': 0, 'w': 1, 'd': 1, 'h': 1, 'rot': 0}, {'id': a + '#2', 'x': 10, 'y': 10, 'w': 1, 'd': 1, 'h': 1, 'rot': 0}]}]}
    r = cl.post('/api/plate/export', json={'layout': liar}); assert r.status_code == 400 and r.get_json()['issues'][0]['issue'] == 'overlap'   # tailles déclarées fausses : détecté
    tall = {'plate': plate, 'plates': [{'index': 1, 'placements': [{'id': h, 'x': 0, 'y': 0, 'w': 1, 'd': 1, 'h': 1, 'rot': 0}]}]}
    assert cl.post('/api/plate/export', json={'layout': tall}).get_json()['issues'][0]['issue'] == 'too_tall'
    outside = tmp_path.parent / 'hors.stl'; trimesh.creation.box().export(str(outside))
    out = {'plate': plate, 'plates': [{'index': 1, 'placements': [{'id': str(outside), 'x': 0, 'y': 0, 'w': 1, 'd': 1, 'h': 1, 'rot': 0}]}]}
    assert cl.post('/api/plate/export', json={'layout': out}).status_code == 403
    assert cl.post('/api/plate/export', json={'layout': ok, 'plate_index': 7}).status_code == 404
    with cl.session_transaction() as s: s['role'] = 'viewer'
    assert cl.post('/api/plate/check', json=ok).status_code == 403 and cl.post('/api/plate/export', json={'layout': ok}).status_code == 403


def test_page_timelapses_menu_impression_et_confirmation_au_premier_plan():
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    html = open(os.path.join(root, 'interface', 'index.html'), encoding='utf-8').read()
    js = open(os.path.join(root, 'interface', 'script.js'), encoding='utf-8').read()
    css = open(os.path.join(root, 'interface', 'style.css'), encoding='utf-8').read()
    assert 'data-page="timelapses"' in html and 'data-cat="print"' in html.split('data-page="timelapses"')[1].split('</button>')[0]
    assert 'id="page-timelapses"' in html and 'id="tlp-body"' in html and 'data-nav-id="timelapses"' in html
    assert "if (page === 'timelapses') loadTimelapsesPage();" in js and 'async function loadTimelapsesPage' in js
    assert '#modal-confirm { z-index: 100500; }' in css                    # devant le cadre des timelapses (z-index 100000)


def test_volet_lateral_transitions_limitees_a_l_animation():
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    js = open(os.path.join(root, 'interface', 'script.js'), encoding='utf-8').read()
    css = open(os.path.join(root, 'interface', 'style.css'), encoding='utf-8').read()
    assert "sidebar.classList.add('nav-anim')" in js and "classList.remove('nav-anim')" in js
    assert '.sidebar:not(.nav-anim) .sidebar-nav, .sidebar:not(.nav-anim)::after { transition: none !important; }' in css
