"""v1.1.6 — traçabilité d'impression : calculs purs, association version/modèle, routes sur une vraie base sqlite."""
import importlib.util, os, sqlite3, sys, logging
import pytest
import flask

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, 'modules', name + '.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _mod():
    return _load('print_traceability')


def R(v, result, profile='P', ver=None):
    return {'model_path': '/m/a.stl', 'model_version': v, 'profile_name': profile, 'result': result, 'sent_at': '2026-11-01 10:00:00'}


def test_wilson_un_sur_un_ne_bat_pas_huit_sur_neuf():
    m = _mod()
    assert m.wilson_low(0, 0) == 0
    assert m.wilson_low(8, 9) > m.wilson_low(1, 1)
    assert 0 <= m.wilson_low(5, 5) < 1


def test_resolve_version_par_empreinte():
    m = _mod()
    vs = [{'version': 1, 'sha256': 'a'}, {'version': 2, 'sha256': 'b'}, {'version': 3, 'sha256': 'a'}]
    assert m.resolve_version(vs, 'b') == 2
    assert m.resolve_version(vs, 'a') == 3          # doublon : la plus récente
    assert m.resolve_version(vs, 'zzz') is None
    assert m.resolve_version(vs, '') is None


def test_aggregate_ignore_les_non_notees_et_classe():
    m = _mod()
    rows = [R(1, 'failed'), R(1, 'failed'), R(1, 'success'),
            R(2, 'success'), R(2, 'success'), R(2, 'success'), R(2, 'partial'),
            R(2, ''), R(2, None)]
    combos = m.aggregate(rows)
    assert [c['version'] for c in combos] == [2, 1]
    assert combos[0]['total'] == 4 and combos[0]['success'] == 3 and combos[0]['confident'] is True
    assert combos[1]['rate'] == pytest.approx(0.333, abs=1e-3)


def test_meilleure_combinaison_exige_version_connue_et_assez_de_donnees():
    m = _mod()
    assert m.pick_best([]) is None
    only_one = m.aggregate([R(1, 'success')])
    assert m.pick_best(only_one) is None                      # 1 impression : pas assez
    unsaved = m.aggregate([R(None, 'success'), R(None, 'success'), R(None, 'success')])
    assert m.pick_best(unsaved) is None                       # version inconnue : non identifiable
    rows = [R(1, 'success'), R(1, 'success'), R(2, 'success'), R(2, 'success'), R(2, 'success'), R(2, 'failed', profile='Q')]
    best = m.pick_best(m.aggregate(rows))
    assert best['version'] == 2 and best['profile'] == 'P'      # 3/3 bat 2/2 (Wilson)
    assert m.pick_best(m.aggregate([R(1, 'failed'), R(1, 'failed')])) is None   # jamais de réussite


def test_stats_par_version():
    m = _mod()
    s = m.version_stats([R(1, 'success'), R(1, 'failed'), R(2, 'success'), R(None, 'success'), R(2, '')])
    assert s[1]['total'] == 2 and s[1]['rate'] == 0.5
    assert s[2]['total'] == 1 and None not in s


# ── base réelle ──────────────────────────────────────────────────────────

def _env(tmp_path):
    tm = _mod()
    mv = _load('model_versions')
    db = str(tmp_path / 't.db')
    data = tmp_path / 'data'
    src = tmp_path / 'src'
    data.mkdir(); src.mkdir()

    def get_db():
        c = sqlite3.connect(db); c.row_factory = sqlite3.Row; return c
    c = get_db()
    c.execute("CREATE TABLE printers (id INTEGER PRIMARY KEY, name TEXT)")
    c.execute("CREATE TABLE print_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, file_path TEXT, file_name TEXT, result TEXT DEFAULT '', "
              "slicer_profile_name TEXT DEFAULT '', sent_at TEXT DEFAULT '2026-11-01 10:00:00', printer_id INTEGER)")
    c.execute("INSERT INTO printers VALUES (1, 'Prusa')")
    c.commit(); c.close()
    app = flask.Flask('t'); app.secret_key = 'x'
    sess = {'user_id': 1}
    within = lambda p, uid=None: str(p).replace('\\', '/').startswith(str(src).replace('\\', '/'))
    services = dict(app=app, app_logger=logging.getLogger('t'), get_db=get_db, jsonify=flask.jsonify, login_required=lambda f: f,
                    request=flask.request, session=sess, _is_path_within_sources=within, DATA_DIR=str(data),
                    invalidate_cache=lambda: None, send_file=flask.send_file)
    mv.init(services, routes=False)
    tm.init(services)
    # model_versions.py importe `modules.model_versions` depuis print_traceability : on lui donne le module déjà initialisé
    sys.modules.setdefault('modules', type(sys)('modules'))
    sys.modules['modules'].model_versions = mv
    return tm, mv, app.test_client(), get_db, src


def _hist(get_db, path, result='', profile=''):
    c = get_db()
    cur = c.execute("INSERT INTO print_history (user_id, file_path, file_name, result, slicer_profile_name) VALUES (1,?,?,?,?)",
                    (path, os.path.basename(path), result, profile))
    c.commit(); hid = cur.lastrowid; c.close()
    return hid


def test_record_cree_une_version_automatique_puis_la_reutilise(tmp_path):
    tm, mv, client, get_db, src = _env(tmp_path)
    f = src / 'piece.stl'
    f.write_bytes(b'solid v1')
    path = str(f).replace('\\', '/')
    conn = get_db()
    h1 = _hist(get_db, path)
    r1 = tm.record(conn, 1, h1, path, str(f)); conn.commit()
    assert r1 == {'model_path': path, 'version': 1}
    h2 = _hist(get_db, path)
    r2 = tm.record(conn, 1, h2, path, str(f)); conn.commit()
    assert r2['version'] == 1                                  # fichier inchangé : même version, pas de doublon
    f.write_bytes(b'solid v2 modifie')
    h3 = _hist(get_db, path)
    r3 = tm.record(conn, 1, h3, path, str(f)); conn.commit()
    assert r3['version'] == 2                                  # fichier modifié : nouvelle version automatique
    notes = [r['note'] for r in conn.execute("SELECT note FROM model_versions ORDER BY version").fetchall()]
    assert notes == ['Avant impression', 'Avant impression']
    conn.close()


def test_gcode_sans_lien_n_a_pas_de_modele_puis_lien_rattache_l_existant(tmp_path):
    tm, mv, client, get_db, src = _env(tmp_path)
    g = src / 'piece.gcode'; g.write_text('G1 X0')
    model = src / 'piece.stl'; model.write_bytes(b'solid m')
    gp, mp = str(g).replace('\\', '/'), str(model).replace('\\', '/')
    conn = get_db()
    hid = _hist(get_db, gp, 'success', 'PETG 0.2')
    assert tm.record(conn, 1, hid, gp, str(g))['model_path'] == ''
    conn.commit(); conn.close()
    r = client.post('/api/trace/link', json={'file_path': gp, 'model_path': mp})
    assert r.status_code == 200 and r.get_json()['relinked'] == 1 and r.get_json()['version'] == 1
    d = client.get('/api/trace/model', query_string={'path': mp}).get_json()
    assert d['prints'] == 1 and d['versions'][0]['stats']['success'] == 1
    # un nouveau tir du même G-code est maintenant relié d'office
    conn = get_db()
    h2 = _hist(get_db, gp, 'failed', 'PETG 0.2')
    assert tm.record(conn, 1, h2, gp, str(g))['model_path'] == mp
    conn.commit(); conn.close()


def test_routes_meilleure_combinaison_et_apercu(tmp_path):
    tm, mv, client, get_db, src = _env(tmp_path)
    f = src / 'support.stl'; f.write_bytes(b'solid 1')
    path = str(f).replace('\\', '/')
    conn = get_db()
    for res, prof in [('failed', 'Rapide'), ('failed', 'Rapide'), ('success', 'Rapide')]:
        tm.record(conn, 1, _hist(get_db, path, res, prof), path, str(f)); conn.commit()
    f.write_bytes(b'solid 2 renforce')
    for res, prof in [('success', 'Fin'), ('success', 'Fin'), ('success', 'Fin')]:
        tm.record(conn, 1, _hist(get_db, path, res, prof), path, str(f)); conn.commit()
    conn.commit(); conn.close()
    d = client.get('/api/trace/model', query_string={'path': path}).get_json()
    assert d['best']['version'] == 2 and d['best']['profile'] == 'Fin'
    assert {v['version']: v['stats']['total'] for v in d['versions']} == {1: 3, 2: 3}
    o = client.get('/api/trace/overview').get_json()
    assert o['total'] == 1 and o['models'][0]['name'] == 'support.stl' and o['models'][0]['best']['version'] == 2
    assert client.get('/api/trace/overview', query_string={'q': 'zzz'}).get_json()['total'] == 0


def test_routes_refusent_hors_sources_et_entree_manuelle(tmp_path):
    tm, mv, client, get_db, src = _env(tmp_path)
    assert client.get('/api/trace/model').status_code == 400
    assert client.get('/api/trace/model', query_string={'path': '/etc/passwd'}).status_code == 403
    f = src / 'a.stl'; f.write_bytes(b'solid')
    path = str(f).replace('\\', '/')
    conn = get_db(); mv._ensure_table(conn); mv._snapshot(conn, str(f), path, 'v1 manuelle'); conn.commit(); conn.close()
    hid = _hist(get_db, str(src / 'ancienne.gcode').replace('\\', '/'), 'success', 'X')
    assert client.post('/api/trace/entry', json={'history_id': hid, 'model_path': path, 'version': 9}).status_code == 404
    assert client.post('/api/trace/entry', json={'history_id': 9999, 'model_path': path, 'version': 1}).status_code == 404
    assert client.post('/api/trace/entry', json={'history_id': hid, 'model_path': path, 'version': 1}).status_code == 200
    d = client.get('/api/trace/model', query_string={'path': path}).get_json()
    assert d['prints'] == 1 and d['versions'][0]['stats']['success'] == 1
    assert client.post('/api/trace/link', json={'file_path': path, 'model_path': str(src / 'x.gcode')}).status_code == 400


def test_record_ne_leve_jamais(tmp_path):
    tm, *_ = _env(tmp_path)
    assert tm.record(None, 1, 5, '/x.stl') is None
    assert tm.record(None, 1, None, '/x.stl') is None


def test_projets_meme_piece_plusieurs_fois():
    """1.1.6 : ré-ajouter une pièce déjà dans le projet cumule la quantité (au lieu d'être ignoré) ; quantité modifiable dans l'interface."""
    import sqlite3
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main = open(os.path.join(root, 'main.py'), encoding='utf-8').read()
    assert 'ON CONFLICT(project_id, file_path) DO UPDATE SET quantity_needed = quantity_needed + excluded.quantity_needed' in main
    c = sqlite3.connect(':memory:')
    c.execute("CREATE TABLE project_files (project_id INTEGER, file_path TEXT, quantity_needed INTEGER DEFAULT 1, position INTEGER DEFAULT 0, PRIMARY KEY (project_id, file_path))")
    sql = ("INSERT INTO project_files (project_id, file_path, quantity_needed, position) VALUES (?, ?, ?, ?) "
           "ON CONFLICT(project_id, file_path) DO UPDATE SET quantity_needed = quantity_needed + excluded.quantity_needed")
    c.execute(sql, (1, 'a.stl', 2, 0)); c.execute(sql, (1, 'a.stl', 3, 1)); c.execute(sql, (1, 'b.stl', 1, 2))
    assert c.execute("SELECT quantity_needed FROM project_files WHERE file_path='a.stl'").fetchone()[0] == 5
    assert c.execute("SELECT COUNT(*) FROM project_files").fetchone()[0] == 2
    js = open(os.path.join(root, 'interface', 'script.js'), encoding='utf-8').read()
    assert 'window.setProjectFileNeeded' in js and 'class="qty-needed"' in js and '_projectPickerQty.get(el.value)' in js
