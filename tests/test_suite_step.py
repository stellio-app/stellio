"""Diff 3D de fichiers STEP (1.1.7) : lecture CAO facultative (cadquery-ocp)."""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))
import model_diff as M

OCP = pytest.importorskip('OCP')


def _write_step(shape, path):
    from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
    w = STEPControl_Writer()
    w.Transfer(shape, STEPControl_AsIs)
    w.Write(str(path))


@pytest.fixture
def steps(tmp_path):
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
    from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir
    box = BRepPrimAPI_MakeBox(40, 30, 20).Shape()
    cyl = BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(20, 15, -1), gp_Dir(0, 0, 1)), 6, 30).Shape()
    a, b = tmp_path / 'a.step', tmp_path / 'b.stp'
    _write_step(box, a)
    _write_step(BRepAlgoAPI_Cut(box, cyl).Shape(), b)
    return str(a), str(b)


def test_step_dimensions_et_volume(steps):
    m = M.load_mesh(steps[0])
    assert [round(x) for x in m.extents] == [40, 30, 20]
    assert m.is_watertight and abs(m.volume - 24000) < 1


def test_diff_step_detecte_le_trou(steps):
    r = M.diff_files(*steps)
    assert not r['identical']
    assert r['volume_a_mm3'] == pytest.approx(24000, abs=1)
    assert r['volume_b_mm3'] == pytest.approx(24000 - 3.14159 * 36 * 20, rel=0.01)
    assert r['removed_pct'] > 0 and r['delta']['size_mm'] == [0.0, 0.0, 0.0]


def test_step_identique(steps):
    assert M.diff_files(steps[0], steps[0])['identical']


def test_step_absent_message_clair(monkeypatch, steps):
    import builtins
    real = builtins.__import__

    def fake(name, *a, **k):
        if name.startswith('OCP'):
            raise ImportError(name)
        return real(name, *a, **k)
    monkeypatch.setattr(builtins, '__import__', fake)
    with pytest.raises(ValueError, match='cadquery-ocp'):
        M.load_step(steps[0])


def test_step_illisible(tmp_path):
    bad = tmp_path / 'x.step'
    bad.write_text('pas un step')
    with pytest.raises(Exception):
        M.load_mesh(str(bad))


def test_step_passe_par_le_lecteur_de_l_application(monkeypatch, tmp_path):
    """Dans l'application, le STEP est lu par le service de main.py (cascadio) : le module l'utilise en priorité, scène ou maillage."""
    import trimesh
    called = []

    def fake(path):
        called.append(path)
        return trimesh.Scene([trimesh.creation.box(extents=(10, 20, 30))])
    monkeypatch.setattr(M, '_step_to_trimesh', fake)
    f = tmp_path / 'x.step'; f.write_text('x')
    m = M.load_mesh(str(f))
    assert called == [str(f)] and [round(v) for v in m.extents] == [10, 20, 30]
