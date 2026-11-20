"""Garde-fou « plantage au démarrage » : un gros fichier dont le rendu a tué l'application est mis de côté au démarrage suivant."""
import json, os, sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('STELLIO_NO_AUTO_INSTALL', '1')
os.environ.setdefault('STELLIO_HEADLESS', '1')
sys.path.insert(0, ROOT)
main = pytest.importorskip('main')


@pytest.fixture
def guard(tmp_path, monkeypatch):
    monkeypatch.setattr(main, '_THUMB_INFLIGHT_FILE', str(tmp_path / 'inflight.json'))
    monkeypatch.setattr(main, '_THUMB_CRASHED_FILE', str(tmp_path / 'crashed.json'))
    monkeypatch.setattr(main, '_thumb_crash_state', {'init': False, 'inflight': {}, 'crashed': {}})
    f = tmp_path / 'gros.stl'
    f.write_bytes(b'x' * 100)
    return f, tmp_path


def test_rendu_note_puis_efface(guard):
    f, tmp = guard
    main._thumb_inflight_mark(str(f), True)
    assert list(json.load(open(tmp / 'inflight.json'))) == [str(f).replace('\\', '/')]
    main._thumb_inflight_mark(str(f), False)
    assert json.load(open(tmp / 'inflight.json')) == {}
    assert not main._thumb_crashed_before(str(f))


def test_rendu_interrompu_par_un_plantage_est_mis_de_cote(guard, monkeypatch):
    f, tmp = guard
    main._thumb_inflight_mark(str(f), True)                    # le processus meurt ici : jamais effacé
    monkeypatch.setattr(main, '_thumb_crash_state', {'init': False, 'inflight': {}, 'crashed': {}})   # « redémarrage »
    assert main._thumb_crashed_before(str(f))
    assert json.load(open(tmp / 'inflight.json')) == {}
    monkeypatch.setattr(main, '_thumb_crash_state', {'init': False, 'inflight': {}, 'crashed': {}})   # et il le reste
    assert main._thumb_crashed_before(str(f))


def test_fichier_modifie_est_reessaye(guard, monkeypatch):
    f, tmp = guard
    main._thumb_inflight_mark(str(f), True)
    monkeypatch.setattr(main, '_thumb_crash_state', {'init': False, 'inflight': {}, 'crashed': {}})
    assert main._thumb_crashed_before(str(f))
    f.write_bytes(b'y' * 200)                                   # remplacé par une autre version
    assert not main._thumb_crashed_before(str(f))


def test_rendu_gros_fichier_saute_si_deja_plante(guard, monkeypatch):
    f, tmp = guard
    monkeypatch.setattr(main, 'THUMB_HEAVY_BYTES', 10)
    main._thumb_inflight_mark(str(f), True)
    monkeypatch.setattr(main, '_thumb_crash_state', {'init': False, 'inflight': {}, 'crashed': {}})
    called = []
    monkeypatch.setattr(main, '_generate_thumbnail_pyrender_impl', lambda *a, **k: called.append(1) or True)
    assert main.generate_thumbnail_pyrender(str(f), str(tmp / 't.webp'), timeout_s=5) is False
    assert not called


def test_rendu_normal_laisse_aucune_trace(guard, monkeypatch):
    f, tmp = guard
    monkeypatch.setattr(main, 'THUMB_HEAVY_BYTES', 10)
    monkeypatch.setattr(main, '_generate_thumbnail_pyrender_impl', lambda *a, **k: True)
    assert main.generate_thumbnail_pyrender(str(f), str(tmp / 't.webp'), timeout_s=5) is True
    assert json.load(open(tmp / 'inflight.json')) == {}


# ── Rendu isolé : un plantage du rendu ne doit jamais emporter l'application ────────────────────────────────────────
import subprocess, textwrap


def _fake_worker(monkeypatch, body):
    """Remplace le processus de rendu par un petit script Python (arguments : source, miniature)."""
    script = textwrap.dedent(body)
    monkeypatch.setattr(main, '_thumb_worker_cmd', lambda src, out: [sys.executable, '-c', script, src, out])
    monkeypatch.setattr(main, 'THUMB_ISOLATE', True)
    monkeypatch.setattr(main, 'THUMB_HEAVY_BYTES', 10)


def test_isole_rendu_reussi(guard, monkeypatch):
    f, tmp = guard
    _fake_worker(monkeypatch, "import sys; open(sys.argv[2], 'wb').write(b'ok')")
    assert main.generate_thumbnail_pyrender(str(f), str(tmp / 't.webp'), timeout_s=30) is True
    assert (tmp / 't.webp').exists()


def test_isole_plantage_brutal_met_le_fichier_de_cote(guard, monkeypatch):
    f, tmp = guard
    _fake_worker(monkeypatch, "import os; os._exit(0xC0000005 if os.name == 'nt' else 139)")     # violation d'accès
    assert main.generate_thumbnail_pyrender(str(f), str(tmp / 't.webp'), timeout_s=30) is False     # l'application survit
    assert main._thumb_crashed_before(str(f))                                                        # et n'y retouche plus
    called = []
    monkeypatch.setattr(main, '_render_thumb_isolated', lambda *a: called.append(1))
    assert main.generate_thumbnail_pyrender(str(f), str(tmp / 't.webp'), timeout_s=30) is False
    assert not called


def test_isole_processus_tue_par_le_systeme(guard, monkeypatch):
    f, tmp = guard
    _fake_worker(monkeypatch, "import os, signal; os.kill(os.getpid(), signal.SIGTERM if os.name != 'nt' else signal.SIGABRT)")
    assert main.generate_thumbnail_pyrender(str(f), str(tmp / 't.webp'), timeout_s=30) is False
    assert main._thumb_crashed_before(str(f))


def test_isole_blocage_arrete_pour_de_bon(guard, monkeypatch):
    f, tmp = guard
    _fake_worker(monkeypatch, "import time; time.sleep(120)")
    import time as _t
    t0 = _t.time()
    assert main.generate_thumbnail_pyrender(str(f), str(tmp / 't.webp'), timeout_s=1.5) is False
    assert _t.time() - t0 < 20                                                                      # tué, pas attendu
    assert not main._thumb_crashed_before(str(f))                                                    # un délai dépassé n'est pas un plantage


def test_isole_echec_normal_sans_mise_de_cote(guard, monkeypatch):
    f, tmp = guard
    _fake_worker(monkeypatch, "import os; os._exit(3)")
    assert main.generate_thumbnail_pyrender(str(f), str(tmp / 't.webp'), timeout_s=30) is False
    assert not main._thumb_crashed_before(str(f))


def test_isole_demarrage_impossible_retombe_sur_le_rendu_integre(guard, monkeypatch):
    f, tmp = guard
    _fake_worker(monkeypatch, "import os; os._exit(4)")
    monkeypatch.setattr(main, '_generate_thumbnail_pyrender_impl', lambda *a, **k: True)
    assert main.generate_thumbnail_pyrender(str(f), str(tmp / 't.webp'), timeout_s=30) is True


def test_isole_jeton_gros_fichier_rendu(guard, monkeypatch):
    f, tmp = guard
    _fake_worker(monkeypatch, "import os; os._exit(139 if os.name != 'nt' else 3221225477)")
    main.generate_thumbnail_pyrender(str(f), str(tmp / 't.webp'), timeout_s=30)
    assert main._thumb_heavy_sem.acquire(timeout=1)                                                  # pas resté bloqué
    main._thumb_heavy_sem.release()


def test_vrai_processus_de_rendu_sur_un_stl(tmp_path):
    """Le vrai point d'entrée (--stellio-thumb-worker) démarre, charge main.py sans lancer l'application, et écrit la miniature."""
    trimesh = pytest.importorskip('trimesh')
    src = tmp_path / 'b.stl'
    trimesh.creation.box((10, 10, 10)).export(str(src))
    out = tmp_path / 'b.webp'
    env = dict(os.environ, STELLIO_NO_AUTO_INSTALL='1', STELLIO_HEADLESS='1', STELLIO_DATA_DIR=str(tmp_path / 'data'))
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'main.py'), '--stellio-thumb-worker', str(src), str(out)],
                       env=env, timeout=180, capture_output=True)
    assert r.returncode in (0, 3), r.stderr[-500:]            # 3 = rendu impossible ici (pas de moteur 3D), jamais 4 (démarrage raté)
    if r.returncode == 0:
        assert out.exists() and out.stat().st_size > 0
