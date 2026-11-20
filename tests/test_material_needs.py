"""1.1.7 — besoins en matière : file + projets contre stock, manque, bobines à commander, fiabilité du poids."""
import importlib.util, logging, os, sqlite3
import pytest
flask = pytest.importorskip('flask')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _mod():
    spec = importlib.util.spec_from_file_location('material_needs_t', __import__('conftest').mod_path('material_needs'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def test_noms_de_matiere():
    m = _mod()
    assert [m.material_key(x) for x in ('PLA+', 'pla silk', 'Generic PETG', 'eSUN PLA-CF', 'nylon', 'PA12', '', None, 'Wood')] == ['PLA', 'PLA', 'PETG', 'PLA', 'PA', 'PA', '', '', 'WOOD']


def test_calcul_manque_et_bobines():
    m = _mod()
    items = [{'material': 'PLA', 'grams': 600, 'kind': 'queue', 'source': 'history'}, {'material': 'PLA+', 'grams': 900, 'kind': 'project', 'source': 'slicer'},
             {'material': 'PETG', 'grams': 100, 'kind': 'queue', 'source': 'rough'}, {'material': 'ABS', 'grams': None, 'kind': 'queue', 'source': None},
             {'material': '', 'grams': 50, 'kind': 'queue', 'source': 'history', 'assumed': True}]
    spools = [{'material': 'PLA', 'remaining_g': 400}, {'material': 'pla', 'remaining_g': 100}, {'material': 'PETG', 'remaining_g': 800}, {'material': 'PLA', 'remaining_g': None}]
    r = {x['material']: x for x in m.compute(items, spools, {'PLA': 50.0})}
    p = r['PLA']
    assert (p['stock_g'], p['spools'], p['queue_g'], p['projects_g'], p['demand_g']) == (500, 2, 650, 900, 1550)     # 50 g sans matière comptés en PLA
    assert p['shortfall_g'] == 1050 and p['spools_to_buy'] == 2 and p['surplus_g'] == 0 and p['days_left'] == 10.0 and p['assumed_material'] == 1
    t = r['PETG']
    assert t['shortfall_g'] == 0 and t['spools_to_buy'] == 0 and t['surplus_g'] == 700 and t['rough'] == 1 and t['days_left'] is None
    assert r['ABS']['unknown_weight'] == 1 and r['ABS']['demand_g'] == 0 and r['ABS']['shortfall_g'] == 0           # poids inconnu : jamais inventé
    ordered = [x['material'] for x in m.compute(items, spools, {})]
    assert ordered[0] == 'PLA'                                                                                     # plus gros manque d'abord


def _env(tmp_path):
    m = _mod()
    db = str(tmp_path / 'n.db')
    c = sqlite3.connect(db)
    c.executescript("""
    CREATE TABLE print_queue(id INTEGER PRIMARY KEY, user_id INT, file_path TEXT, position INT);
    CREATE TABLE projects(id INTEGER PRIMARY KEY, user_id INT, name TEXT, status TEXT);
    CREATE TABLE project_files(project_id INT, file_path TEXT, quantity_needed INT, quantity_printed INT);
    CREATE TABLE filament_assignments(file_path TEXT, user_id INT, material TEXT);
    CREATE TABLE print_history(id INTEGER PRIMARY KEY, user_id INT, file_path TEXT, sent_at TEXT DEFAULT CURRENT_TIMESTAMP, spool_weight_used_g REAL, filament_material TEXT);
    INSERT INTO print_queue VALUES (1,1,'/l/a.stl',1),(2,1,'/l/b.stl',2),(3,2,'/l/autre.stl',1);
    INSERT INTO projects VALUES (1,1,'Salon','in_progress'),(2,1,'Fini','done');
    INSERT INTO project_files VALUES (1,'/l/c.stl',10,4),(2,'/l/d.stl',5,0),(1,'/l/e.stl',2,2);
    INSERT INTO filament_assignments VALUES ('/l/a.stl',1,'PETG');
    INSERT INTO print_history(user_id,file_path,spool_weight_used_g,filament_material) VALUES (1,'/l/a.stl',30,'PLA'),(1,'/l/a.stl',50,'PLA'),(1,'/l/c.stl',20,'PLA'),(1,'/l/c.stl',20,'PLA');
    """)
    c.commit(); c.close()
    def get_db():
        x = sqlite3.connect(db); x.row_factory = sqlite3.Row; return x
    app = flask.Flask('mn'); app.secret_key = 'k'
    weights = {'/l/b.stl': (100.0, 'geometric'), '/l/c.stl': (999.0, 'slicer')}
    m.init(dict(app=app, app_logger=logging.getLogger('t'), get_db=get_db, jsonify=flask.jsonify, login_required=lambda f: f, request=flask.request, session=flask.session,
                _get_required_weight_for_file=lambda p: weights.get(p, (None, None)),
                _restock_collect_spools=lambda uid: [{'material': 'PETG', 'remaining_g': 30}, {'material': 'PLA', 'remaining_g': 500}]))
    cl = app.test_client()
    with cl.session_transaction() as s:
        s['user_id'] = 1
    return m, cl, get_db


def test_collecte_file_et_projets(tmp_path):
    m, cl, get_db = _env(tmp_path)
    conn = get_db()
    it = {i['name']: i for i in m.collect_items(conn, 1)}
    a = it['a.stl']
    assert a['material'] == 'PETG' and a['grams'] == 40 and a['source'] == 'history' and a['assumed'] is False           # affectation > historique ; moyenne réelle 30/50
    b = it['b.stl']
    assert b['grams'] == 35 and b['source'] == 'rough' and b['material'] == '' and b['assumed'] is True                  # géométrique × 0,35, matière supposée
    c = [v for k, v in it.items() if 'c.stl' in k][0]
    assert c['grams'] == 20 * 6 and c['source'] == 'history' and c['material'] == 'PLA' and '×6' in c['name']            # 10 voulues − 4 faites ; moyenne réelle 20 g
    assert not any('d.stl' in k or 'e.stl' in k or 'autre' in k for k in it)                                              # projet terminé, quantité atteinte, autre utilisateur
    conn.close()


def test_route(tmp_path):
    m, cl, _ = _env(tmp_path)
    d = cl.get('/api/filament/needs').get_json()
    by = {r['material']: r for r in d['materials']}
    assert by['PETG']['demand_g'] == 40 and by['PETG']['stock_g'] == 30 and by['PETG']['shortfall_g'] == 10 and by['PETG']['spools_to_buy'] == 1
    assert by['PLA']['demand_g'] == 155 and by['PLA']['shortfall_g'] == 0 and by['PLA']['rough'] == 1
    assert d['items'] == 3 and d['rough_factor'] == 0.35 and d['materials'][0]['material'] == 'PETG'


def test_jamais_de_poids_invente(tmp_path):
    m, cl, get_db = _env(tmp_path)
    c = get_db(); c.execute("DELETE FROM print_history"); c.commit(); c.close()
    m._get_required_weight_for_file = lambda p: (None, None)
    d = cl.get('/api/filament/needs').get_json()
    assert d['unknown_weight'] == 3 and all(r['demand_g'] == 0 for r in d['materials'])


def test_analyse_a_la_demande_quand_le_poids_manque(tmp_path):
    m, cl, get_db = _env(tmp_path)
    f = tmp_path / 'x.stl'; f.write_bytes(b'x')
    m._get_required_weight_for_file = lambda p: (None, None)
    m.analyze_3d_file_stored = lambda p: {'weights': {'pla': 200.0}}
    conn = get_db()
    assert m.weight_and_source(conn, 1, str(f)) == (70.0, 'rough')
    assert m.weight_and_source(conn, 1, str(tmp_path / 'absent.stl')) == (None, None)       # fichier introuvable : poids inconnu, rien d'inventé
    m.analyze_3d_file_stored = lambda p: (_ for _ in ()).throw(RuntimeError('illisible'))
    assert m.weight_and_source(conn, 1, str(f)) == (None, None)
    conn.close()
