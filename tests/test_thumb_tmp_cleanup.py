"""Disque plein sur le serveur : les copies temporaires faites pour les miniatures (fichiers SMB) ne doivent jamais s'accumuler."""
import os, sys, time
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('STELLIO_NO_AUTO_INSTALL', '1')
os.environ.setdefault('STELLIO_HEADLESS', '1')
sys.path.insert(0, ROOT)
trimesh = pytest.importorskip('trimesh')
main = pytest.importorskip('main')


class FakeSmb:
    """Faux client SMB : sert un STL local sous un chemin //nas/…"""
    def __init__(self, local): self.local = local
    def stat(self, p):
        class S: st_size = os.path.getsize(self.local)
        return S
    def open_file(self, p, mode='rb', **kw): return open(self.local, 'rb')


@pytest.fixture
def smb(tmp_path, monkeypatch):
    stl = tmp_path / 'src.stl'
    trimesh.creation.icosphere(subdivisions=3).export(str(stl))
    monkeypatch.setattr(main, 'DATA_DIR', str(tmp_path / 'data'))
    monkeypatch.setattr(main, 'smbclient', FakeSmb(str(stl)), raising=False)
    monkeypatch.setattr(main, '_smb_host_is_paused', lambda p: False)
    return tmp_path


def _leftovers(tmp):
    d = tmp / 'data' / 'tmp_thumbs'
    return list(d.iterdir()) if d.exists() else []


def test_copie_supprimee_apres_rendu_reussi(smb):
    assert main._generate_thumbnail_pyrender_impl('//nas/share/a.stl', str(smb / 't.webp'))
    assert _leftovers(smb) == []


def test_copie_supprimee_quand_le_rendu_cpu_de_secours_prend_le_relais(smb, monkeypatch):
    monkeypatch.setattr(main, '_pyrender_unavailable', True, raising=False)
    main._generate_thumbnail_pyrender_impl('//nas/share/b.stl', str(smb / 't.webp'))
    assert _leftovers(smb) == []


def test_copie_supprimee_si_le_rendu_echoue(smb, monkeypatch):
    def boom(*a, **k): raise RuntimeError('rendu impossible')
    monkeypatch.setattr(main, '_generate_thumbnail_raster', boom)
    monkeypatch.setattr(main, '_pyrender_unavailable', True, raising=False)
    main._generate_thumbnail_pyrender_impl('//nas/share/c.stl', str(smb / 't.webp'))
    assert _leftovers(smb) == []


def test_pas_de_copie_si_le_disque_est_presque_plein(smb, monkeypatch):
    monkeypatch.setattr(main, '_thumb_tmp_space_ok', lambda n: False)
    assert main._generate_thumbnail_pyrender_impl('//nas/share/d.stl', str(smb / 't.webp')) is False
    assert _leftovers(smb) == []


def test_disque_plein_ne_met_pas_le_nas_en_panne(smb, monkeypatch):
    marked = []
    monkeypatch.setattr(main, '_smb_host_mark_down', lambda *a: marked.append(a))
    monkeypatch.setattr(main.time, 'sleep', lambda s: None)
    class Full(FakeSmb):
        def open_file(self, p, mode='rb', **kw): raise OSError(28, 'No space left on device')
    monkeypatch.setattr(main, 'smbclient', Full(str(smb / 'src.stl')), raising=False)
    assert main._generate_thumbnail_pyrender_impl('//nas/share/e.stl', str(smb / 't.webp')) is False
    assert marked == [] and _leftovers(smb) == []


def test_nettoyage_des_restes(smb):
    d = main._thumb_tmp_dir()
    old, new = os.path.join(d, 'vieux.stl'), os.path.join(d, 'recent.stl')
    for f in (old, new):
        open(f, 'wb').write(b'x' * 1000)
    os.utime(old, (time.time() - 3600, time.time() - 3600))
    assert main._sweep_thumb_tmp(min_age_s=600) == 1000
    assert not os.path.exists(old) and os.path.exists(new)
    main._sweep_thumb_tmp(min_age_s=0)
    assert not os.path.exists(new)


def test_windows_copies_temporaires_hors_du_dossier_roaming(tmp_path, monkeypatch):
    monkeypatch.setattr(main.os, 'name', 'nt')
    monkeypatch.delenv('STELLIO_DATA_DIR', raising=False)
    monkeypatch.setattr(main, '_portable_data_dir', lambda: None)
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path / 'Local'))
    monkeypatch.setattr(main, 'DATA_DIR', str(tmp_path / 'Roaming' / 'Stellio'))
    p = main._thumb_tmp_path()
    assert p.startswith(str(tmp_path / 'Local')) and 'Roaming' not in p


def test_portable_ou_autre_systeme_reste_dans_le_dossier_de_donnees(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'DATA_DIR', str(tmp_path / 'data'))
    assert main._thumb_tmp_path() == os.path.join(str(tmp_path / 'data'), 'tmp_thumbs')
