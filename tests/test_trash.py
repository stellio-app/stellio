"""Corbeille unifiée : mise en corbeille puis restauration / suppression définitive (SQLite réel, fichiers réels)."""
import json, logging, os, shutil, sqlite3, time
import pytest
from conftest import load_from_main

NAMES = ['_ensure_trash_table', '_trash_snapshot', '_trash_insert', '_trash_rm', 'trash_record', '_trash_purge_row',
         '_trash_restore_files_of', '_trash_restore_row', '_trash_list_for_user', '_trash_retention_seconds',
         'TRASH_ITEMS_DIR', 'TRASH_RETENTION_DAYS', '_trash_table_ready']


@pytest.fixture()
def env(tmp_path):
    db = str(tmp_path / 'db.sqlite')
    def get_db():
        c = sqlite3.connect(db); c.row_factory = sqlite3.Row; return c
    c = get_db()
    c.executescript("""
      CREATE TABLE quotes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, number TEXT, client TEXT, pdf_file TEXT, client_id INT DEFAULT 0);
      CREATE TABLE clients (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, name TEXT, email TEXT DEFAULT '');
      CREATE TABLE projects (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, name TEXT);
      CREATE TABLE project_files (project_id INT, file_path TEXT, PRIMARY KEY(project_id,file_path));
      CREATE TABLE project_gcodes (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INT, user_id INT, name TEXT);
    """); c.commit(); c.close()
    ns = load_from_main(NAMES, {
        'get_db': get_db, 'sqlite3': sqlite3, 'json': json, 'shutil': shutil, 'time': time,
        'app_logger': logging.getLogger('t'), 'load_settings': lambda: {},
        'TRASH_DIR': str(tmp_path / 'trash'), '_trash_registry': {}, '_trash_registry_lock': __import__('threading').Lock(), '_ensure_quote_columns': lambda: None, 'PROJECT_GCODES_DIR': str(tmp_path / 'gc'),
    })
    # TRASH_ITEMS_DIR est calculé à partir de TRASH_DIR à l'import réel : on le fixe ici
    ns['TRASH_ITEMS_DIR'] = str(tmp_path / 'trash' / 'items')
    return ns, get_db, tmp_path


def test_quote_roundtrip_with_files(env):
    ns, get_db, tp = env
    pdf = tp / 'q.pdf'; pdf.write_bytes(b'%PDF')
    conn = get_db()
    qid = conn.execute("INSERT INTO quotes (user_id, number, client, pdf_file) VALUES (1,'D-1','Marie','q.pdf')").lastrowid
    row = dict(conn.execute("SELECT * FROM quotes WHERE id=?", (qid,)).fetchone())
    tid = ns['trash_record'](conn, 1, 'quote', 'D-1', {'row': row}, files=[str(pdf)])
    conn.execute("DELETE FROM quotes WHERE id=?", (qid,)); conn.commit()
    assert not pdf.exists()
    assert [i['label'] for i in ns['_trash_list_for_user'](1)] == ['D-1']
    assert ns['_trash_list_for_user'](2) == []
    item = conn.execute("SELECT * FROM trash_items WHERE id=?", (tid,)).fetchone()
    ok, err = ns['_trash_restore_row'](conn, item); conn.commit()
    assert ok, err
    assert pdf.read_bytes() == b'%PDF'
    r = conn.execute("SELECT * FROM quotes").fetchone()
    assert (r['id'], r['number'], r['client']) == (qid, 'D-1', 'Marie')


def test_restore_when_id_already_reused(env):
    ns, get_db, tp = env
    conn = get_db()
    cid = conn.execute("INSERT INTO clients (user_id, name) VALUES (1,'A')").lastrowid
    row = dict(conn.execute("SELECT * FROM clients").fetchone())
    tid = ns['trash_record'](conn, 1, 'client', 'A', {'row': row, 'quote_ids': []})
    conn.execute("DELETE FROM clients"); conn.execute("INSERT INTO clients (id, user_id, name) VALUES (?,1,'B')", (cid,)); conn.commit()
    item = conn.execute("SELECT * FROM trash_items WHERE id=?", (tid,)).fetchone()
    ok, _ = ns['_trash_restore_row'](conn, item); conn.commit()
    assert ok
    assert sorted(r['name'] for r in conn.execute("SELECT name FROM clients")) == ['A', 'B']   # rien n'est écrasé


def test_client_restore_relinks_quotes(env):
    ns, get_db, tp = env
    conn = get_db()
    cid = conn.execute("INSERT INTO clients (user_id, name) VALUES (1,'A')").lastrowid
    q = conn.execute("INSERT INTO quotes (user_id, number, client_id) VALUES (1,'D',?)", (cid,)).lastrowid
    row = dict(conn.execute("SELECT * FROM clients").fetchone())
    tid = ns['trash_record'](conn, 1, 'client', 'A', {'row': row, 'quote_ids': [q]})
    conn.execute("DELETE FROM clients"); conn.execute("UPDATE quotes SET client_id=0"); conn.commit()
    item = conn.execute("SELECT * FROM trash_items WHERE id=?", (tid,)).fetchone()
    ns['_trash_restore_row'](conn, item); conn.commit()
    assert conn.execute("SELECT client_id FROM quotes").fetchone()[0] == cid


def test_project_roundtrip_with_gcode_folder(env):
    ns, get_db, tp = env
    gdir = tp / 'gc' / '1'; gdir.mkdir(parents=True); (gdir / 'a.gcode').write_text('G1')
    conn = get_db()
    pid = conn.execute("INSERT INTO projects (user_id, name) VALUES (1,'Boîte')").lastrowid
    conn.execute("INSERT INTO project_files VALUES (?, '/x/a.stl')", (pid,))
    conn.execute("INSERT INTO project_gcodes (project_id, user_id, name) VALUES (?,1,'a.gcode')", (pid,))
    payload = {'row': ns['_trash_snapshot'](conn, 'projects', 'id=?', (pid,))[0],
               'project_files': ns['_trash_snapshot'](conn, 'project_files', 'project_id=?', (pid,)),
               'gcodes': ns['_trash_snapshot'](conn, 'project_gcodes', 'project_id=?', (pid,))}
    tid = ns['trash_record'](conn, 1, 'project', 'Boîte', payload, files=[str(gdir)])
    for t in ('project_files', 'projects', 'project_gcodes'):
        conn.execute(f"DELETE FROM {t}")
    conn.commit()
    assert not gdir.exists()
    item = conn.execute("SELECT * FROM trash_items WHERE id=?", (tid,)).fetchone()
    ok, err = ns['_trash_restore_row'](conn, item); conn.commit()
    assert ok, err
    assert (gdir / 'a.gcode').read_text() == 'G1'
    assert conn.execute("SELECT count(*) FROM project_files").fetchone()[0] == 1
    assert conn.execute("SELECT count(*) FROM project_gcodes").fetchone()[0] == 1


def test_purge_removes_attachments(env):
    ns, get_db, tp = env
    f = tp / 'doc.pdf'; f.write_bytes(b'x')
    conn = get_db()
    tid = ns['trash_record'](conn, 1, 'quote', 'X', {'row': {}}, files=[str(f)])
    stored = tp / 'trash' / 'items' / str(tid)
    assert stored.exists()
    ns['_trash_purge_row'](conn, tid); conn.commit()
    assert not stored.exists()
    assert conn.execute("SELECT count(*) FROM trash_items").fetchone()[0] == 0
