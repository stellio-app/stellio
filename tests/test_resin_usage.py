"""Déduction automatique de la résine (1.1.8) : volume, déduction, échec partiel, doublon, annulation."""
import importlib.util
import os
import sqlite3
import zipfile

import pytest

from conftest import mod_path


def _mod():
    spec = importlib.util.spec_from_file_location('resin_usage_under_test', mod_path('resin_usage'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m._insert_notification_once = None
    return m


def _db():
    c = sqlite3.connect(':memory:')
    c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE resin_bottles (id INTEGER PRIMARY KEY, user_id INT, name TEXT, volume_ml REAL, remaining_ml REAL)")
    c.execute("INSERT INTO resin_bottles VALUES (1, 7, 'Grise', 1000, 500)")
    m = _mod()
    m._ensure(c)
    c.execute("INSERT INTO resin_printer_bottle VALUES (3, 7, 1)")
    c.commit()
    return m, c


def _sl1(path, ml):
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('config.ini', f"action = print\nusedMaterial = {ml}\n")
    return str(path)


def test_sl1_lit_usedmaterial(tmp_path):
    m = _mod()
    assert m.sl1_used_ml(_sl1(tmp_path / 'a.sl1', 42.5)) == 42.5
    assert m.sl1_used_ml(str(tmp_path / 'absent.sl1')) is None
    bad = tmp_path / 'b.sl1'
    with zipfile.ZipFile(bad, 'w') as z:
        z.writestr('config.ini', 'x = 1\n')
    assert m.sl1_used_ml(str(bad)) is None


def test_deduction_sl1_et_pas_de_double_deduction(tmp_path):
    m, c = _db()
    files = [{'name': 'piece.sl1', 'path': _sl1(tmp_path / 'piece.sl1', 40)}]
    r = m.apply_usage(c, 7, 3, 'piece.sl1', 'finished', 100, 'k1', files=files)
    assert r['status'] == 'deducted' and r['ml'] == 40 and r['source'] == 'sl1' and r['left'] == 460
    assert m.apply_usage(c, 7, 3, 'piece.sl1', 'finished', 100, 'k1', files=files)['status'] == 'duplicate'
    assert c.execute("SELECT remaining_ml FROM resin_bottles").fetchone()[0] == 460


def test_echec_deduit_la_part_imprimee_seulement_si_progression_connue(tmp_path):
    m, c = _db()
    files = [{'name': 'p.sl1', 'path': _sl1(tmp_path / 'p.sl1', 100)}]
    assert m.apply_usage(c, 7, 3, 'p.sl1', 'failed', None, 'a', files=files)['status'] == 'no_progress'
    r = m.apply_usage(c, 7, 3, 'p.sl1', 'failed', 30, 'b', files=files)
    assert r['ml'] == 30 and r['source'] == 'sl1+partial'


def test_modele_stl_estimation_avec_marge(tmp_path):
    trimesh = pytest.importorskip('trimesh')
    m, c = _db()
    p = tmp_path / 'cube.stl'
    trimesh.creation.box(extents=(20, 20, 20)).export(str(p))      # 8 000 mm³ = 8 ml
    files = [{'name': 'cube.stl', 'path': str(p)}]
    r = m.apply_usage(c, 7, 3, 'cube.sl1', 'finished', 100, 'm', overhead_pct=25, files=files)
    assert r['status'] == 'deducted' and r['source'] == 'model' and r['ml'] == 10.0


def test_rien_n_est_invente(tmp_path):
    m, c = _db()
    assert m.apply_usage(c, 7, 3, 'inconnu.sl1', 'finished', 100, 'z', files=[])['status'] == 'no_volume'
    assert c.execute("SELECT remaining_ml FROM resin_bottles").fetchone()[0] == 500
    assert m.apply_usage(c, 7, 99, 'x.sl1', 'finished', 100, 'y', files=[])['status'] == 'no_bottle'


def test_ne_descend_jamais_sous_zero(tmp_path):
    m, c = _db()
    c.execute("UPDATE resin_bottles SET remaining_ml = 10")
    files = [{'name': 'g.sl1', 'path': _sl1(tmp_path / 'g.sl1', 80)}]
    assert m.apply_usage(c, 7, 3, 'g.sl1', 'finished', 100, 'g', files=files)['ml'] == 10
    assert c.execute("SELECT remaining_ml FROM resin_bottles").fetchone()[0] == 0
