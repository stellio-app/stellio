"""STL géants (plusieurs Go) : lecture en flux, simplification pour l'aperçu, refus des opérations d'écriture."""
import os, sys
import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('STELLIO_NO_AUTO_INSTALL', '1')
os.environ.setdefault('STELLIO_HEADLESS', '1')
sys.path.insert(0, ROOT)
trimesh = pytest.importorskip('trimesh')
main = pytest.importorskip('main')


def _write_stl(mesh, path):
    mesh.export(path)
    return str(path)


@pytest.fixture
def sphere(tmp_path):
    return _write_stl(trimesh.creation.icosphere(subdivisions=4, radius=20), tmp_path / 'sphere.stl')


def test_stats_en_flux_exactes(sphere):
    ref = trimesh.load(sphere, force='mesh', process=True)
    st = main.stl_stream_stats(sphere, chunk=1000)      # petits morceaux : exerce la boucle
    assert st['triangles'] == len(ref.faces)
    assert st['volume_mm3'] == pytest.approx(abs(ref.volume), rel=1e-4)
    assert st['area_mm2'] == pytest.approx(ref.area, rel=1e-4)
    assert np.allclose(st['bounds'][1] - st['bounds'][0], ref.bounds[1] - ref.bounds[0], atol=1e-3)


def test_stats_ignore_les_stl_ascii(tmp_path):
    p = tmp_path / 'a.stl'
    p.write_text('solid x\nendsolid x\n')
    assert main.stl_stream_stats(str(p)) is None


def test_simplification_bornee_et_fidele(sphere):
    m = main.stl_cluster_decimate(sphere, target_faces=2000, chunk=1000)
    assert 0 < len(m.faces) < 8000
    assert m.metadata['stellio_decimated_from'] > len(m.faces)
    assert np.allclose(m.bounds[1] - m.bounds[0], [40, 40, 40], atol=3)


def test_chargement_refuse_si_geant_sauf_apercu(sphere, monkeypatch):
    monkeypatch.setattr(main, 'STL_HUGE_BYTES', 1000)
    with pytest.raises(main.ModelTooLargeError):
        main.load_model_mesh(sphere)
    m = main.load_model_mesh(sphere, preview=True)
    assert len(m.faces) > 0


def test_analyse_en_flux(sphere, monkeypatch):
    monkeypatch.setattr(main, 'STL_HUGE_BYTES', 1000)
    r = main.analyze_3d_file(sphere)
    assert r.get('streamed')
    assert r['triangle_count'] > 1000
    assert r['dimensions']['x'] == pytest.approx(40, abs=0.1)


def test_petit_stl_inchange(sphere):
    assert not main._stl_is_huge(sphere)
    assert len(main.load_model_mesh(sphere).faces) > 1000


def test_autres_formats_refuses_si_la_memoire_ne_suffit_pas(tmp_path, monkeypatch):
    p = tmp_path / 'enorme.obj'
    p.write_bytes(b'v 0 0 0\n')
    monkeypatch.setattr(main.os.path, 'getsize', lambda _p: 3 * 1024 ** 3)
    psutil = pytest.importorskip('psutil')
    class VM:  available = 8 * 1024 ** 3
    monkeypatch.setattr(psutil, 'virtual_memory', lambda: VM)
    with pytest.raises(main.ModelTooLargeError):
        main.load_model_mesh(str(p))
    VM.available = 64 * 1024 ** 3                                  # assez de mémoire : on tente le chargement (échec du contenu, pas de la taille)
    try:
        main.load_model_mesh(str(p))
    except main.ModelTooLargeError:
        pytest.fail('refusé alors que la mémoire suffit')
    except Exception:
        pass                                                       # contenu minimal : une autre erreur est sans importance ici


def test_seuil_stl_geant_adaptatif_a_la_memoire_libre(monkeypatch):
    """Le seuil monte avec la mémoire libre (40 % / 16), entre 256 Mo et 1 Go ; un seuil imposé est respecté."""
    import types
    mo = 1024 * 1024
    for libre_go, attendu in ((4, 256), (16, 409), (32, 819), (128, 1024)):
        monkeypatch.setitem(sys.modules, 'psutil', types.SimpleNamespace(virtual_memory=lambda g=libre_go: types.SimpleNamespace(available=g * 1024 * mo)))
        assert abs(main._stl_huge_limit() // mo - attendu) <= 1, libre_go
    monkeypatch.setattr(main, 'STL_HUGE_BYTES', 1000)
    assert main._stl_huge_limit() == 1000


def test_stl_ascii_lu_par_blocs_comme_le_binaire(sphere, tmp_path):
    """Demande de l'utilisateur : un STL texte volumineux peut être analysé et allégé (blocs, mémoire constante)."""
    ref = trimesh.load(sphere, force='mesh', process=True)
    pa = str(tmp_path / 'ascii.stl'); ref.export(pa, file_type='stl_ascii')
    assert main._stl_is_ascii(pa) and main._stl_binary_count(pa) is None
    orig = main._stl_ascii_chunks
    st = main.stl_stream_stats(pa, chunk=700)
    assert st['triangles'] == len(ref.faces) and st['volume_mm3'] == pytest.approx(abs(ref.volume), rel=1e-3)
    blocs = list(main._stl_ascii_chunks(pa, chunk=500, block=20000))          # petits blocs : exerce la coupe sur « endfacet »
    assert sum(len(b) for b in blocs) == len(ref.faces) and max(len(b) for b in blocs) <= 500
    m = main.stl_cluster_decimate(pa, target_faces=2000, chunk=700)
    assert 0 < len(m.faces) < 8000 and np.allclose(m.bounds[1] - m.bounds[0], [40, 40, 40], atol=3)


def test_stl_binaire_au_compteur_faux_est_reconnu_par_sa_taille(sphere, tmp_path):
    raw = bytearray(open(sphere, 'rb').read()); n = (len(raw) - 84) // 50
    raw[80:84] = (0).to_bytes(4, 'little')                                    # compteur nul (certains exportateurs)
    p = tmp_path / 'zero.stl'; p.write_bytes(bytes(raw))
    assert main._stl_binary_count(str(p)) == n and not main._stl_is_ascii(str(p))
