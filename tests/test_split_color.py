"""Séparer par couleur (sdk/examples/split-color/split_color.py, plugin signé du catalogue) : un 3MF multicolore → un 3MF avec un plateau par couleur."""
import importlib.util, io, os, zipfile
import pytest

trimesh = pytest.importorskip('trimesh')
np = pytest.importorskip('numpy')
flask = pytest.importorskip('flask')
from conftest import load_from_main, ROOT


def _three_mf(path, boxes, vertex_paint=False):
    """3MF coloré (matières de base) : boxes = [(origine x, couleur #RRGGBB)] ; un objet par boîte."""
    mats = ''.join(f'<base name="m{i}" displaycolor="{c}FF"/>' for i, (_x, c) in enumerate(boxes))
    objs, items = [], []
    for i, (x, _c) in enumerate(boxes):
        m = trimesh.creation.box(extents=(10, 10, 10)); m.apply_translation([x, 0, 5])
        v = ''.join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a, b, c in m.vertices)
        t = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}" pid="1" p1="{i}"/>' for a, b, c in m.faces)
        objs.append(f'<object id="{i + 2}" type="model"><mesh><vertices>{v}</vertices><triangles>{t}</triangles></mesh></object>')
        items.append(f'<item objectid="{i + 2}"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<resources><basematerials id="1">{mats}</basematerials>{"".join(objs)}</resources><build>{"".join(items)}</build></model>')
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        zf.writestr('_rels/.rels', '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="r0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        zf.writestr('3D/3dmodel.model', model)


def _client(tmp_path, resolver=True):
    import re, logging
    ns = load_from_main(['_resolve_3mf_plate_mesh', '_read_3mf_color_context', '_read_3mf_material_groups', '_decode_paint_state', '_hex_to_rgb',
                         '_fast_parse_mesh_block', '_concatenate_filtering_outliers', '_thumb_base_rgb'],
                        extra_ns={'json': __import__('json'), 'trimesh': trimesh, 'io': io, 'zipfile': zipfile, 're': re, 'app_logger': logging.getLogger('t'),
                                  '_safe_xml_parse': __import__('xml.etree.ElementTree', fromlist=['parse']).parse, 'load_settings': lambda: {}, 'THUMB_DEFAULT_COLOR': '#4ea1d3'})
    spec = importlib.util.spec_from_file_location('split_color_t', os.path.join(ROOT, 'sdk', 'examples', 'split-color', 'split_color.py'))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    app = flask.Flask('t'); app.secret_key = 'x'
    import trimesh.transformations as tra
    services = dict(DATA_DIR=str(tmp_path), _is_path_within_sources=lambda p, u: True, app=app,
                    app_logger=logging.getLogger('t'), invalidate_cache=lambda: None, get_db=lambda: None,
                    _smb_kwargs_for_path=lambda u, p: None, smbclient=None,
                    jsonify=flask.jsonify, login_required=lambda f: f, np=np, request=flask.request, session={'user_id': 1},
                    _resolve_3mf_plate_mesh=ns['_resolve_3mf_plate_mesh'], _thumb_base_rgb=ns['_thumb_base_rgb'])
    mod.init(services)
    return app.test_client(), mod


def test_analyse_liste_les_couleurs(tmp_path):
    c, _ = _client(tmp_path)
    src = tmp_path / 'm.3mf'; _three_mf(str(src), [(0, 'FF0000'), (20, '00FF00'), (40, 'FF0000')])
    d = c.post('/api/x/split-color/split', json={'path': str(src), 'dry_run': True}).get_json()
    assert d['color_count'] == 2
    assert {x['hex'] for x in d['colors']} == {'#FF0000', '#00FF00'}
    assert d['colors'][0]['hex'] == '#FF0000' and d['colors'][0]['percent'] > d['colors'][1]['percent']   # la plus grande d'abord


def test_un_plateau_par_couleur(tmp_path):
    c, _ = _client(tmp_path)
    src = tmp_path / 'm.3mf'; _three_mf(str(src), [(0, 'FF0000'), (20, '00FF00'), (40, '0000FF')])
    r = c.post('/api/x/split-color/split', json={'path': str(src), 'filename': 'sortie'})
    d = r.get_json()
    assert r.status_code == 200 and d['plate_count'] == 3 and d['output_filename'] == 'sortie.3mf'
    with zipfile.ZipFile(d['output_path']) as zf:
        cfg = zf.read('Metadata/model_settings.config').decode()
        assert cfg.count('<plate>') == 3 and '#FF0000' in cfg and '#0000FF' in cfg
        assert zf.read('3D/3dmodel.model').count(b'<item ') == 3


def test_chaque_plateau_une_seule_couleur_et_faces_conservees(tmp_path):
    c, _ = _client(tmp_path)
    src = tmp_path / 'm.3mf'; _three_mf(str(src), [(0, 'FF0000'), (20, '00FF00')])
    d = c.post('/api/x/split-color/split', json={'path': str(src)}).get_json()
    out = tmp_path / 'relu.3mf'
    os.replace(d['output_path'], out)
    # relecture avec le même lecteur : 2 objets, 12 triangles chacun (boîte), les deux couleurs d'origine
    _c, mod = _client(tmp_path)
    mesh, rgb = mod._load_colored_mesh(str(out))
    assert len(mesh.faces) == 24
    assert {tuple(x) for x in np.unique(rgb, axis=0)} == {(255, 0, 0), (0, 255, 0)}
    # un plateau par couleur : chaque objet garde SA couleur et les deux plateaux ne se chevauchent pas
    with zipfile.ZipFile(out) as zf:
        model = zf.read('3D/3dmodel.model').decode()
    assert model.count('<basematerials') == 2 and '#FF0000FF' in model and '#00FF00FF' in model


def test_tolerance_fusionne_les_couleurs_proches(tmp_path):
    c, _ = _client(tmp_path)
    src = tmp_path / 'm.3mf'; _three_mf(str(src), [(0, 'FF0000'), (20, 'FA0504'), (40, '0000FF')])
    assert c.post('/api/x/split-color/split', json={'path': str(src), 'dry_run': True}).get_json()['color_count'] == 3
    d = c.post('/api/x/split-color/split', json={'path': str(src), 'dry_run': True, 'tolerance': 12}).get_json()
    assert d['color_count'] == 2


def test_une_seule_couleur_et_formats_refuses(tmp_path):
    c, _ = _client(tmp_path)
    src = tmp_path / 'm.3mf'; _three_mf(str(src), [(0, 'FF0000'), (20, 'FF0000')])
    r = c.post('/api/x/split-color/split', json={'path': str(src)})
    assert r.status_code == 400 and 'rien à séparer' in r.get_json()['error']
    stl = tmp_path / 'a.stl'; trimesh.creation.box().export(str(stl))
    assert c.post('/api/x/split-color/split', json={'path': str(stl)}).status_code == 400
    assert c.post('/api/x/split-color/split', json={}).status_code == 400
    assert c.post('/api/x/split-color/split', json={'path': str(tmp_path / 'nope.3mf')}).status_code == 404


def test_trop_de_couleurs_demande_une_tolerance(tmp_path):
    c, mod = _client(tmp_path)
    src = tmp_path / 'm.3mf'
    _three_mf(str(src), [(i * 12, '%02X%02X%02X' % (i * 10, 255 - i * 10, 7)) for i in range(mod.MAX_COLORS + 2)])
    r = c.post('/api/x/split-color/split', json={'path': str(src)})
    assert r.status_code == 400 and 'tolérance' in r.get_json()['error']


def test_bambu_peinture_par_triangle_et_extrudeur(tmp_path):
    """3MF Bambu/Orca : couleurs de filaments + peinture par triangle (paint_color) → une plaque par filament peint."""
    m = trimesh.creation.box(extents=(10, 10, 10)); m.apply_translation([0, 0, 5])
    v = ''.join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a, b, c in m.vertices)
    paints = ['4' if i % 2 == 0 else '8' for i in range(len(m.faces))]    # « 4 » = filament 1, « 8 » = filament 2
    t = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}" paint_color="{p}"/>' for (a, b, c), p in zip(m.faces, paints))
    model = ('<?xml version="1.0"?><model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<resources><object id="1" type="model"><mesh><vertices>{v}</vertices><triangles>{t}</triangles></mesh></object></resources>'
             '<build><item objectid="1"/></build></model>')
    src = tmp_path / 'b.3mf'
    with zipfile.ZipFile(src, 'w') as zf:
        zf.writestr('3D/3dmodel.model', model)
        zf.writestr('Metadata/project_settings.config', '{"filament_colour": ["#112233", "#FFAA00"]}')
    c, _ = _client(tmp_path)
    d = c.post('/api/x/split-color/split', json={'path': str(src), 'dry_run': True}).get_json()
    assert d['color_count'] == 2 and {x['hex'] for x in d['colors']} == {'#112233', '#FFAA00'}
    assert all(x['faces'] == 6 for x in d['colors'])


def test_selecteur_de_fichiers_3mf_et_refus_aux_comptes_invites(tmp_path):
    c, mod = _client(tmp_path)
    cache = tmp_path / 'cache.json'
    mod.CACHE_FILE = str(cache); mod._read_cache_json_safe = lambda: {'files': [
        {'path': '/a/Pion.3mf', 'name': 'Pion.3mf'}, {'path': '/a/pion.stl', 'name': 'pion.stl'}, {'path': '/a/Tour.3MF', 'name': 'Tour.3MF'}]}
    cache.write_text('{}')
    d = c.get('/api/x/split-color/files?q=pi').get_json()
    assert [f['name'] for f in d['files']] == ['Pion.3mf']
    assert {f['name'] for f in c.get('/api/x/split-color/files').get_json()['files']} == {'Pion.3mf', 'Tour.3MF'}
    mod.session['role'] = 'viewer'
    try:
        assert c.get('/api/x/split-color/files').status_code == 403
        assert c.post('/api/x/split-color/split', json={'path': 'x.3mf'}).status_code == 403
    finally:
        mod.session.pop('role', None)
