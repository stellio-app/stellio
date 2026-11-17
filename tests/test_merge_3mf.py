"""Fusion de plusieurs modèles en un 3MF (modules/merge_3mf.py) : un plateau si ça tient, sinon plusieurs plateaux."""
import importlib.util, os, zipfile
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
trimesh = pytest.importorskip('trimesh')
np = pytest.importorskip('numpy')
flask = pytest.importorskip('flask')
shapely = pytest.importorskip('shapely')
from conftest import load_from_main


def _client(tmp_path):
    from shapely.geometry import MultiPoint
    from shapely import affinity as shapely_affinity
    ns = load_from_main(['_pack_footprints_shelf', '_pack_footprints', '_get_polygon_footprint', '_pack_polygons'],
                        extra_ns={'MultiPoint': MultiPoint, 'shapely_affinity': shapely_affinity, 'HAS_SHAPELY': True,
                                  'math': __import__('math')})
    spec = importlib.util.spec_from_file_location('merge_3mf_t', os.path.join(ROOT, 'modules', 'merge_3mf.py'))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    app = flask.Flask('t'); app.secret_key = 'x'
    import trimesh.transformations as tra
    services = dict(DATA_DIR=str(tmp_path), HAS_SHAPELY=True, _get_polygon_footprint=ns['_get_polygon_footprint'],
                    _is_path_within_sources=lambda p, u: True, _load_mesh_for_conversion=lambda p: trimesh.load(p, force='mesh'),
                    _pack_footprints=ns['_pack_footprints'], _pack_polygons=ns['_pack_polygons'], app=app,
                    app_logger=__import__('logging').getLogger('t'), invalidate_cache=lambda: None, get_db=lambda: None, _smb_kwargs_for_path=lambda u, p: None,
                    load_3mf_mesh=lambda s: None, load_model_mesh=lambda s, e: trimesh.load(__import__('io').BytesIO(s), file_type=e.lstrip('.'), force='mesh'), smbclient=None,
                    jsonify=flask.jsonify, login_required=lambda f: f, np=np, request=flask.request, session={'user_id': 1},
                    tra=tra, trimesh=trimesh)
    mod.init(services)
    return app.test_client(), mod


def _boxes(tmp_path, sizes):
    paths = []
    for i, (x, y, z) in enumerate(sizes):
        p = tmp_path / f'p{i}.stl'
        trimesh.creation.box(extents=(x, y, z)).export(str(p))
        paths.append(str(p))
    return paths


def test_trois_pieces_un_seul_plateau(tmp_path):
    c, _ = _client(tmp_path)
    r = c.post('/api/files/merge-3mf', json={'paths': _boxes(tmp_path, [(40, 40, 10)] * 3), 'bed_width': 220, 'bed_height': 220})
    d = r.get_json()
    assert r.status_code == 200 and d['plate_count'] == 1 and d['piece_count'] == 3
    assert sorted(d['merged_paths']) == sorted(os.path.join(str(tmp_path), f'p{i}.stl') for i in range(3))
    with zipfile.ZipFile(d['output_path']) as zf:
        assert {'3D/3dmodel.model', 'Metadata/model_settings.config', '[Content_Types].xml'} <= set(zf.namelist())
        assert zf.read('3D/3dmodel.model').count(b'<item ') == 3


def test_pieces_trop_nombreuses_plusieurs_plateaux(tmp_path):
    c, _ = _client(tmp_path)
    r = c.post('/api/files/merge-3mf', json={'paths': _boxes(tmp_path, [(100, 100, 10)] * 5), 'bed_width': 220, 'bed_height': 220})
    d = r.get_json()
    assert r.status_code == 200 and d['plate_count'] >= 2 and d['piece_count'] == 5
    assert sum(len(p) for p in d['plates']) == 5
    # Stellio relit le fichier comme un 3MF multi-plateaux
    import sys; sys.path.insert(0, ROOT)
    ns = load_from_main(['_parse_3mf_plate_object_ids'], extra_ns={'zipfile': zipfile, 'io': __import__('io'),
                        '_safe_xml_parse': __import__('xml.etree.ElementTree', fromlist=['x']).parse})
    plates = ns['_parse_3mf_plate_object_ids'](d['output_path'])
    assert plates and len(plates) == d['plate_count']


def test_trimesh_relit_le_3mf_fusionne(tmp_path):
    c, _ = _client(tmp_path)
    d = c.post('/api/files/merge-3mf', json={'paths': _boxes(tmp_path, [(30, 30, 10), (20, 20, 5)])}).get_json()
    scene = trimesh.load(d['output_path'])
    geoms = scene.geometry if hasattr(scene, 'geometry') else {'m': scene}
    assert len(geoms) == 2


def test_refus_pieces_trop_hautes_et_selection_trop_petite(tmp_path):
    c, _ = _client(tmp_path)
    assert c.post('/api/files/merge-3mf', json={'paths': _boxes(tmp_path, [(10, 10, 10)])}).status_code == 400
    r = c.post('/api/files/merge-3mf', json={'paths': _boxes(tmp_path, [(10, 10, 300)] * 2), 'bed_height_z': 250})
    assert r.status_code == 400 and r.get_json()['errors']


def test_nom_et_dossier_choisis(tmp_path):
    import sqlite3
    c, mod = _client(tmp_path)
    dest = tmp_path / 'mes modeles'; dest.mkdir()
    db = sqlite3.connect(':memory:'); db.row_factory = sqlite3.Row
    db.execute('CREATE TABLE sources (id INTEGER, user_id INTEGER, path TEXT)'); db.execute('INSERT INTO sources VALUES (7, 1, ?)', (str(dest),))
    mod.get_db = lambda: type('C', (), {'execute': lambda self, *a: db.execute(*a), 'close': lambda self: None})()
    paths = _boxes(tmp_path, [(30, 30, 10), (20, 20, 5)])
    d = c.post('/api/files/merge-3mf', json={'paths': paths, 'source_id': 7, 'target_subfolder': 'Echecs/pions', 'filename': 'Mon jeu: v2.3mf'}).get_json()
    assert d['output_path'] == str(dest / 'Echecs' / 'pions' / 'Mon jeu_ v2.3mf'), d
    d2 = c.post('/api/files/merge-3mf', json={'paths': paths, 'source_id': 7, 'target_subfolder': 'Echecs/pions', 'filename': 'Mon jeu: v2'}).get_json()
    assert d2['output_path'].endswith('Mon jeu_ v2_2.3mf')            # jamais d'écrasement
    assert c.post('/api/files/merge-3mf', json={'paths': paths, 'source_id': 7, 'target_subfolder': '../x'}).status_code == 400


def test_fichiers_et_dossier_sur_partage_reseau(tmp_path):
    """Sources SMB : lecture en mémoire et écriture du 3MF sur le partage (smbclient simulé)."""
    import io
    c, mod = _client(tmp_path)
    share = {}
    local = _boxes(tmp_path, [(30, 30, 10), (20, 20, 5)])
    for i, lp in enumerate(local):
        share[f'//nas/stl/porte-carte/p{i}.stl'] = open(lp, 'rb').read()

    class _F(io.BytesIO):
        def __init__(self, store, key, mode):
            super().__init__(store.get(key, b'') if 'r' in mode else b''); self.store, self.key, self.mode = store, key, mode
        def __exit__(self, *a):
            if 'w' in self.mode: self.store[self.key] = self.getvalue()
            return super().__exit__(*a)
    fake = type('S', (), {})()
    fake.open_file = lambda p, mode='rb', **k: _F(share, p, mode)
    fake.makedirs = lambda p, exist_ok=True, **k: None
    fake.path = type('P', (), {'exists': staticmethod(lambda p, **k: p in share)})
    mod.smbclient = fake
    mod._smb_kwargs_for_path = lambda uid, p: {'username': 'u'}
    d = c.post('/api/files/merge-3mf', json={'paths': ['//nas/stl/porte-carte/p0.stl', '//nas/stl/porte-carte/p1.stl'], 'filename': 'porte-carte'}).get_json()
    assert d['output_path'] == '//nas/stl/porte-carte/porte-carte.3mf' and d['piece_count'] == 2, d
    assert zipfile.is_zipfile(io.BytesIO(share['//nas/stl/porte-carte/porte-carte.3mf']))


def test_suppression_sur_partage_reseau_avec_identifiants_de_la_source(tmp_path):
    """Fichiers SMB : copie locale en corbeille puis suppression avec smbclient ; les miniatures ne partent qu'en cas de succès."""
    import io, sys
    spec = importlib.util.spec_from_file_location('fod_t', os.path.join(ROOT, 'modules', 'file_origin_delete.py'))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    app = flask.Flask('t2'); app.secret_key = 'x'
    share = {'//nas/stl/a.stl': b'solid a'}
    class _F(io.BytesIO):
        def __init__(self, data): super().__init__(data)
    fake = type('S', (), {})()
    fake.open_file = lambda p, mode='rb', **k: _F(share[p])
    fake.remove = lambda p, **k: share.pop(p)
    fake.path = type('P', (), {'isfile': staticmethod(lambda p, **k: p in share)})
    thumbs = tmp_path / 'thumbs'; thumbs.mkdir()
    import hashlib
    th = thumbs / (hashlib.md5(b'//nas/stl/a.stl').hexdigest() + '.webp'); th.write_bytes(b'x')
    ns = {n: (lambda *a, **k: None) for n in mod._REQUIRED}
    ns.update(THUMBNAILS_DIR=str(thumbs), TRASH_DIR=str(tmp_path / 'trash'), TRASH_UNDO_SECONDS=10, app=app, app_logger=__import__('logging').getLogger('t'),
              login_required=lambda f: f, jsonify=flask.jsonify, request=flask.request, session={'user_id': 1}, smbclient=fake,
              _smb_kwargs_for_path=lambda u, p: {'username': 'u'}, _is_path_within_sources=lambda p, u: True,
              is_virtual_archive_path=lambda p: False, _get_source_root_paths=lambda u: [], _trash_registry={}, _trash_registry_lock=__import__('threading').Lock(),
              _trash_save_manifest=lambda b: None, journal_log=lambda *a, **k: None, _move_file_to_trash=None)
    mod.init(ns)
    r = app.test_client().post('/api/files/delete-batch', json={'file_paths': ['//nas/stl/a.stl', '//nas/stl/absent.stl']})
    d = r.get_json()
    assert d['deleted_count'] == 1 and len(d['errors']) == 1 and not share        # supprimé sur le partage
    assert not th.exists()                                                          # miniature retirée après succès
    assert any((tmp_path / 'trash').rglob('a.stl'))                                  # copie en corbeille (annulable)
