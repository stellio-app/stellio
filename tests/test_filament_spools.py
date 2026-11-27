"""1.2.1 : module filament_spools (extrait de main.py) — mêmes routes, mêmes réponses : bobines manuelles et affectation d'une bobine à un fichier."""
import importlib.util, logging, os, sqlite3, sys
import pytest
flask = pytest.importorskip('flask')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import ROOT
from test_schema_migration import _env, _upgrade


@pytest.fixture
def cl(tmp_path):
    ns, get_db = _env(str(tmp_path / 's.db'))
    _upgrade(ns)
    c = get_db(); c.execute("INSERT INTO users (username, password_hash) VALUES ('romain','x')"); c.commit(); c.close()
    spec = importlib.util.spec_from_file_location('filament_spools_t', os.path.join(ROOT, 'modules', 'filament_spools.py'))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    app = flask.Flask('t'); app.secret_key = 'x'
    trashed = []
    def trash_record(conn, uid, kind, label, payload):
        trashed.append((kind, label)); return len(trashed)
    mod.init(dict(app=app, app_logger=logging.getLogger('t'), get_db=get_db, jsonify=flask.jsonify, login_required=lambda f: f,
                  request=flask.request, session={'user_id': 1}, trash_record=trash_record,
                  _trash_snapshot=lambda conn, table, where, params=(): [dict(r) for r in conn.execute(f"SELECT * FROM {table} WHERE {where}", params).fetchall()]))
    return app.test_client(), trashed


def test_cycle_bobine_manuelle(cl):
    c, trashed = cl
    r = c.post('/api/filament/manual', json={'name': 'Rouge', 'material': 'PLA', 'color_hex': '#ff0000', 'remaining_g': 800, 'capacity_g': 1000})
    assert r.status_code in (200, 201), r.get_json()
    lst = c.get('/api/filament/manual').get_json()
    spools = lst if isinstance(lst, list) else lst.get('spools')
    assert len(spools) == 1 and spools[0]['name'] == 'Rouge'
    sid = spools[0]['id']
    assert c.put(f'/api/filament/manual/{sid}', json={'remaining_g': 500}).status_code == 200
    spools = c.get('/api/filament/manual').get_json(); spools = spools if isinstance(spools, list) else spools['spools']
    assert spools[0]['remaining_g'] == 500
    d = c.delete(f'/api/filament/manual/{sid}')
    assert d.status_code == 200 and d.get_json()['trash_key'] == 'row:1' and trashed == [('spool', 'Rouge')]      # suppression = corbeille
    assert (c.get('/api/filament/manual').get_json() or []) in ([], {'spools': []}) or not (c.get('/api/filament/manual').get_json().get('spools'))


def test_affectation_fichier_aller_retour(cl):
    c, _ = cl
    assert c.post('/api/files/assign-filament', json={'path': 'C:\\m\\a.3mf', 'source_type': 'manual', 'source_id': '3', 'name': 'Rouge', 'material': 'PLA', 'color_hex': '#f00'}).status_code == 200
    got = c.get('/api/files/filament-assignment?path=C:/m/a.3mf')
    assert got.status_code == 200 and 'Rouge' in got.get_data(as_text=True)
    assert c.post('/api/files/unassign-filament', json={'path': 'C:/m/a.3mf'}).status_code == 200
    assert c.post('/api/files/assign-filament', json={'path': ''}).status_code == 400


def test_routes_toujours_declarees_une_seule_fois():
    import route_contract as rc
    snap = rc.load_snapshot()
    for r in ('POST /api/filament/manual', 'GET /api/filament/manual', 'PUT /api/filament/manual/<int:spool_id>', 'DELETE /api/filament/manual/<int:spool_id>', 'POST /api/files/assign-filament'):
        assert r in snap and r in rc.collect()
