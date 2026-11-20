"""1.1.7 — fiche pièce : assemblage en lecture seule, sections tolérantes, accès limité aux sources."""
import importlib.util, logging, os, sqlite3
import pytest
flask = pytest.importorskip('flask')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = '/lib/boite.stl'


def _env(tmp_path, ok=True, schema=True):
    spec = importlib.util.spec_from_file_location('part_dossier_t', os.path.join(ROOT, 'modules', 'part_dossier.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    db = str(tmp_path / 'd.db')
    c = sqlite3.connect(db)
    if schema:
        c.executescript("""
        CREATE TABLE file_origins(file_path TEXT, user_id INT, source_url TEXT, author TEXT, license TEXT, notes TEXT, platform TEXT, license_expires TEXT);
        CREATE TABLE model_versions(id INTEGER PRIMARY KEY, user_id INT, path TEXT, version INT, stored_name TEXT, size INT, sha256 TEXT, note TEXT, auto INT, created_at REAL);
        CREATE TABLE print_history(id INTEGER PRIMARY KEY, user_id INT, file_name TEXT, sent_at TEXT, result TEXT, slicer_profile_name TEXT, printer_id INT, spool_id INT, filament_material TEXT, actual_seconds REAL);
        CREATE TABLE print_trace(history_id INT, user_id INT, model_path TEXT, model_version INT, profile_fp TEXT);
        CREATE TABLE printers(id INTEGER PRIMARY KEY, name TEXT);
        CREATE TABLE gcode_archive(history_id INTEGER PRIMARY KEY, user_id INT, name TEXT, raw_size INT, gz_size INT, sha256 TEXT, stored TEXT, created REAL);
        CREATE TABLE print_photos(id INTEGER PRIMARY KEY, user_id INT, file_path TEXT, image_filename TEXT, note TEXT, created_at TEXT);
        INSERT INTO printers VALUES (1,'Ender');
        INSERT INTO file_origins VALUES ('/lib/boite.stl',1,'https://x/y','Ana','CC-BY-4.0','','printables','2000-01-01');
        INSERT INTO model_versions VALUES (1,1,'/lib/boite.stl',1,'a.stl',10,'h','',0,1.0),(2,1,'/lib/boite.stl',2,'b.stl',12,'h2','v2',0,2.0);
        """)
        for i, (v, res) in enumerate([(1, 'failed'), (2, 'success'), (2, 'success'), (2, 'success')], start=1):
            c.execute("INSERT INTO print_history VALUES (?,?,?,?,?,?,?,?,?,?)", (i, 1, 'boite.gcode', '2026-11-0%d' % i, res, 'Standard', 1, None, 'PLA', 3600))
            c.execute("INSERT INTO print_trace VALUES (?,?,?,?,?)", (i, 1, P, v, 'fp'))
        c.execute("INSERT INTO gcode_archive VALUES (2,1,'boite.gcode',100,40,'abc','s',1.0)")
        c.execute("INSERT INTO print_photos VALUES (1,1,?,'p.jpg','ok','2026-11-02')", (P,))
        c.commit()
    c.close()
    def get_db():
        x = sqlite3.connect(db); x.row_factory = sqlite3.Row; return x
    app = flask.Flask('d'); app.secret_key = 'k'
    m.init(dict(app=app, app_logger=logging.getLogger('t'), get_db=get_db, jsonify=flask.jsonify, login_required=lambda f: f,
                request=flask.request, session=flask.session, _is_path_within_sources=lambda p, uid: ok))
    cl = app.test_client()
    with cl.session_transaction() as s:
        s['user_id'] = 1
    return m, cl


def test_fiche_complete(tmp_path):
    m, cl = _env(tmp_path)
    d = cl.get('/api/part-dossier', query_string={'path': P}).get_json()
    assert d['name'] == 'boite.stl' and d['exists'] is False
    assert d['origin']['author'] == 'Ana' and d['origin']['status'] == 'expired'
    assert [v['version'] for v in d['versions']] == [2, 1]
    v2 = d['versions'][0]; assert v2['prints'] == 3 and v2['success'] == 3
    assert d['prints']['total'] == 4 and d['prints']['success'] == 3 and d['prints']['failed'] == 1
    assert d['prints']['recent'][0]['printer'] == 'Ender'
    assert d['best']['version'] == 2 and d['best']['profile'] == 'Standard'
    assert d['gcode'][0]['history_id'] == 2 and d['photos'][0]['image_filename'] == 'p.jpg'


def test_sections_tolerantes_base_neuve(tmp_path):
    m, cl = _env(tmp_path, schema=False)
    r = cl.get('/api/part-dossier', query_string={'path': P})
    d = r.get_json(); assert r.status_code == 200
    assert d['versions'] == [] and d['prints']['total'] == 0 and d['best'] is None and d['gcode'] == [] and d['photos'] == []


def test_acces_refuse_hors_sources_et_chemin_requis(tmp_path):
    m, cl = _env(tmp_path, ok=False)
    assert cl.get('/api/part-dossier', query_string={'path': P}).status_code == 403
    assert cl.get('/api/part-dossier').status_code == 400
