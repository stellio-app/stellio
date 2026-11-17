"""Page BigPrint (modules/bigprint_tool.py + moteur vendorisé `bigprint/`) : routes, validation, calcul réel d'un aperçu puis enregistrement."""
import importlib.util, os, sys, time
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
trimesh = pytest.importorskip('trimesh')
flask = pytest.importorskip('flask')
pytest.importorskip('manifold3d')
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _client(tmp_path):
    spec = importlib.util.spec_from_file_location('bigprint_tool_t', os.path.join(ROOT, 'modules', 'bigprint_tool.py'))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    app = flask.Flask('t'); app.secret_key = 'x'
    services = dict(DATA_DIR=str(tmp_path), _is_path_within_sources=lambda p, u: True, _smb_kwargs_for_path=lambda u, p: None, app=app,
                    app_logger=__import__('logging').getLogger('t'), get_db=lambda: None, invalidate_cache=lambda: None,
                    jsonify=flask.jsonify, login_required=lambda f: f, request=flask.request, session={'user_id': 1}, smbclient=None)
    mod.init(services)
    return app.test_client(), mod


def _sphere(tmp_path, radius=50):
    p = tmp_path / 'boule.stl'
    trimesh.creation.icosphere(subdivisions=2, radius=radius).export(str(p))
    return p


def _wait(c, timeout=240):
    end = time.time() + timeout
    while time.time() < end:
        d = c.get('/api/bigprint/job').get_json()
        if d['job'] and d['job']['state'] != 'running':
            return d
        time.sleep(0.4)
    raise AssertionError('délai dépassé')


def _settings(model_id, **over):
    s = {"model_id": model_id, "size_mode": "height", "size_value": "0.35", "size_unit": "m", "printer": "custom", "bed": ["200", "200", "200"],
         "purpose": "display", "hollow": "auto", "wall": "4", "material": "pla", "price": "", "dowels": True, "dowel_d": "6", "dowel_depth": "15",
         "clearance": "0.4", "labels": True, "smooth": False, "smooth_angle": "60", "smooth_edge": "5", "up": "z", "margin": "5", "nozzle": "0.4",
         "merge_small": True, "even_cuts": False, "repair": True}
    s.update(over)
    return s


def test_config_expose_imprimantes_et_usages(tmp_path):
    c, _ = _client(tmp_path)
    d = c.get('/api/bigprint/config').get_json()
    assert d['available'] and 'bambu-x1' in d['printers'] and 'display' in d['purposes'] and d['license'].startswith('AGPL')


def test_chemin_invalide_et_format_refuse(tmp_path):
    c, mod = _client(tmp_path)
    assert c.post('/api/bigprint/model', json={'path': str(tmp_path / 'absent.stl')}).status_code == 400
    (tmp_path / 'x.txt').write_text('a')
    r = c.post('/api/bigprint/model', json={'path': str(tmp_path / 'x.txt')})
    assert r.status_code == 400 and 'Format' in r.get_json()['error']
    c.post('/api/bigprint/close')


def test_dossier_destination_et_nom(tmp_path):
    _, mod = _client(tmp_path)
    assert mod._clean_folder_name(' a/b:c. ') == 'a_b_c'
    f = mod._dest_dir(None, 'sous/dossier', 'boule_bigprint')
    assert f == os.path.join(str(tmp_path), 'bigprint_output', 'sous', 'dossier', 'boule_bigprint') and os.path.isdir(f)
    with pytest.raises(ValueError):
        mod._dest_dir(None, '../evasion', 'x')


def test_apercu_puis_enregistrement_reels(tmp_path):
    c, mod = _client(tmp_path)
    info = c.post('/api/bigprint/model', json={'path': str(_sphere(tmp_path))}).get_json()
    assert info['triangles'] > 0 and info['stem'] == 'boule'
    # réglage invalide refusé tout de suite
    assert c.post('/api/bigprint/preview', json={'settings': _settings(info['id'], wall='abc')}).status_code == 400
    s = _settings(info['id'])
    assert c.post('/api/bigprint/preview', json={'settings': s}).status_code == 200
    d = _wait(c)
    assert d['job']['state'] == 'done', d['job'].get('error')
    assert d['summary']['pieces'] >= 2 and d['summary']['size'][2] == 350
    html = c.get('/api/bigprint/preview.html')
    assert html.status_code == 200 and b'importmap' in html.data and 'data:' in html.headers['Content-Security-Policy']
    # enregistrer avec d'autres réglages que ceux de l'aperçu → refusé
    assert c.post('/api/bigprint/save', json={'settings': _settings(info['id'], wall='5')}).status_code == 400
    r = c.post('/api/bigprint/save', json={'settings': s, 'folder_name': 'ma_boule', 'target_subfolder': 'tests'})
    assert r.status_code == 200
    d = _wait(c)
    assert d['job']['state'] == 'done', d['job'].get('error')
    out = os.path.join(str(tmp_path), 'bigprint_output', 'tests', 'ma_boule_bigprint')   # suffixe ajouté automatiquement
    assert d['job']['out'] == out   # « terminé » n'est annoncé qu'une fois les fichiers copiés
    assert os.path.exists(os.path.join(out, 'project.3mf')) and os.path.isdir(os.path.join(out, 'pieces')) and os.path.exists(os.path.join(out, 'report.md'))
    assert os.path.basename(d['job']['out']).endswith('_bigprint')
    assert c.post('/api/bigprint/close').status_code == 200
