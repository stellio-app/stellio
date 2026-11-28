"""1.2.2 : module workshop_logs (extrait de main.py) — pièces d'usure, calibrations, séchage : mêmes routes, mêmes règles."""
import importlib.util, logging, os, sys
import pytest
flask = pytest.importorskip('flask')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import ROOT
from test_schema_migration import _env, _upgrade


@pytest.fixture
def c(tmp_path):
    ns, get_db = _env(str(tmp_path / 'w.db'))
    _upgrade(ns)
    db = get_db(); db.execute("INSERT INTO users (username, password_hash) VALUES ('romain','x')"); db.commit(); db.close()
    spec = importlib.util.spec_from_file_location('workshop_logs_t', os.path.join(ROOT, 'modules', 'workshop_logs.py'))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    app = flask.Flask('t'); app.secret_key = 'x'
    mod.init(dict(app=app, get_db=get_db, jsonify=flask.jsonify, login_required=lambda f: f, request=flask.request, session=flask.session))
    cl = app.test_client()
    with cl.session_transaction() as s:
        s['user_id'] = 1
    return cl


def _items(r):
    j = r.get_json()
    return j if isinstance(j, list) else next(v for v in j.values() if isinstance(v, list))


def test_pieces_cycle_et_stock_bas(c):
    r = c.post('/api/parts', json={'name': 'Buse 0.4', 'stock_qty': 1, 'alert_qty': 2, 'category': 'nozzle'})
    assert r.status_code in (200, 201), r.get_json()
    parts = _items(c.get('/api/parts')); assert len(parts) == 1 and parts[0]['name'] == 'Buse 0.4'
    pid = parts[0]['id']
    assert [p['id'] for p in _items(c.get('/api/parts/low'))] == [pid]                  # 1 ≤ seuil 2
    assert c.post(f'/api/parts/{pid}/adjust', json={'delta': 5}).status_code == 200
    assert _items(c.get('/api/parts/low')) == []
    assert c.put(f'/api/parts/{pid}', json={'name': 'Buse 0.6', 'stock_qty': 9}).status_code == 200
    assert c.delete(f'/api/parts/{pid}').status_code == 200 and _items(c.get('/api/parts')) == []


@pytest.mark.parametrize('body', [{'name': ''}, {'name': 'x', 'stock_qty': -1}, {'name': 'x', 'buy_url': 'ftp://x'}, {'name': 'x', 'printer_id': 99}])
def test_pieces_refuse_les_entrees_invalides(c, body):
    assert c.post('/api/parts', json=body).status_code == 400


def test_calibrations_cycle(c):
    r = c.post('/api/calibrations', json={'material': 'PLA', 'brand': 'Bambu', 'nozzle_temp': 215})
    assert r.status_code in (200, 201), r.get_json()
    cal = _items(c.get('/api/calibrations'))
    assert len(cal) == 1 and cal[0]['material'] == 'PLA'
    assert c.post('/api/calibrations', json={'material': ''}).status_code == 400            # matière requise
    assert c.delete(f"/api/calibrations/{cal[0]['id']}").status_code == 200 and _items(c.get('/api/calibrations')) == []


def test_sechage_evenement(c):
    r = c.post('/api/filament/drying', json={'source_type': 'manual', 'source_id': '1', 'material': 'PA', 'kind': 'dried', 'temp_c': 70, 'duration_h': 8})
    assert r.status_code in (200, 201), r.get_json()
    assert c.post('/api/filament/drying', json={'source_type': 'manual', 'source_id': '1', 'kind': 'dried', 'temp_c': 999}).status_code == 400   # hors limites
    assert c.get('/api/filament/drying/due').status_code == 200
