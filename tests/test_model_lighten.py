"""1.1.7 — version allégée d'un STL volumineux : copie simplifiée à côté de l'original, jamais de remplacement."""
import importlib.util, logging, os, sys
import pytest
flask = pytest.importorskip('flask')
trimesh = pytest.importorskip('trimesh')
np = pytest.importorskip('numpy')
sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _main_funcs():
    import test_stl_huge as t
    return t.main


def _mod(tmp_extra=None, role=None):
    spec = importlib.util.spec_from_file_location('model_lighten_t', os.path.join(ROOT, 'modules', 'model_lighten.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    main = _main_funcs()
    app = flask.Flask('t'); app.secret_key = 'x'
    jobs = []
    ns = dict(app=app, app_logger=logging.getLogger('t'), jsonify=flask.jsonify, login_required=lambda f: f, request=flask.request, session=flask.session,
              _is_path_within_sources=lambda p, uid: True, stl_cluster_decimate=main.stl_cluster_decimate, _stl_binary_count=main._stl_binary_count, _stl_is_ascii=main._stl_is_ascii,
              invalidate_cache=lambda: jobs.append('inv'))
    m.init(ns)
    cl = app.test_client()
    with cl.session_transaction() as s:
        s['user_id'] = 1
        if role: s['role'] = role
    return m, cl, jobs


class Ctx:
    def progress(self, *a, **k): pass
    def check(self): pass


def _stl(path, subdiv=5):
    m = trimesh.creation.icosphere(subdivisions=subdiv, radius=20); m.export(path); return len(m.faces)


def test_copie_allegee_a_cote_de_l_original(tmp_path):
    m, cl, jobs = _mod()
    src = str(tmp_path / 'gros.stl'); n = _stl(src, 6)
    avant = open(src, 'rb').read()
    r = m.lighten(Ctx(), 1, src, 20000)
    assert r['name'] == 'gros (allégé).stl' and os.path.isfile(r['path']) and r['triangles_before'] == n and 0 < r['triangles_after'] < n
    assert open(src, 'rb').read() == avant                                        # l'original n'est jamais touché
    assert not [f for f in os.listdir(tmp_path) if f.endswith('.part')] and 'inv' in jobs
    r2 = m.lighten(Ctx(), 1, src, 20000)                                           # nom pris : jamais de remplacement
    assert r2['name'] == 'gros (allégé) 2.stl' and os.path.isfile(r['path'])
    chargé = trimesh.load(r['path'], force='mesh'); assert abs(chargé.volume - 4 / 3 * np.pi * 20 ** 3) / (4 / 3 * np.pi * 20 ** 3) < 0.1


def test_route_refus_clairs(tmp_path):
    m, cl, _ = _mod()
    assert cl.post('/api/files/lighten', json={'path': str(tmp_path / 'absent.stl')}).status_code == 404
    obj = tmp_path / 'a.obj'; obj.write_text('v 0 0 0')
    assert cl.post('/api/files/lighten', json={'path': str(obj)}).get_json()['code'] == 'not_stl'
    asc = tmp_path / 'a.stl'; asc.write_text('solid x\nendsolid x\n' * 10)
    assert cl.post('/api/files/lighten', json={'path': str(asc)}).get_json()['code'] == 'not_binary'
    ok = str(tmp_path / 'b.stl'); _stl(ok, 3)
    r = cl.post('/api/files/lighten', json={'path': ok, 'faces': 5})
    assert r.status_code == 202 and r.get_json()['faces'] == 20000 and r.get_json()['target'].endswith('b (allégé).stl')      # borne basse
    m2, cl2, _ = _mod(role='viewer')
    assert cl2.post('/api/files/lighten', json={'path': ok}).status_code == 403    # un invité ne peut rien écrire


def test_depart_hors_sources_refuse(tmp_path):
    m, cl, _ = _mod(); m._is_path_within_sources = lambda p, uid: False
    ok = str(tmp_path / 'c.stl'); _stl(ok, 3)
    assert cl.post('/api/files/lighten', json={'path': ok}).status_code == 403
