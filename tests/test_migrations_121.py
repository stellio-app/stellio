"""1.2.1 : migration d'index, sauvegarde avant migration, relance idempotente."""
import os, sqlite3, importlib.util
from conftest import ROOT


def _mig():
    spec = importlib.util.spec_from_file_location('migrations_t', os.path.join(ROOT, 'modules', 'migrations.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _old_db(path):
    c = sqlite3.connect(path)
    c.executescript("""CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT);
        CREATE TABLE print_history (id INTEGER PRIMARY KEY, user_id INTEGER, file_path TEXT, sent_at TIMESTAMP);
        CREATE TABLE file_tags (file_path TEXT NOT NULL, tag_id INTEGER NOT NULL, PRIMARY KEY (file_path, tag_id));
        CREATE TABLE file_origins (file_path TEXT, user_id INTEGER);""")
    c.executemany("INSERT INTO file_tags VALUES (?,?)", [('/a%d' % i, i % 7) for i in range(400)])
    c.commit(); c.close()


def _idx(c):
    return {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='index'")}


def test_index_crees_une_seule_fois_et_donnees_intactes(tmp_path):
    m = _mig(); p = str(tmp_path / 'a.db'); _old_db(p)
    c = sqlite3.connect(p)
    r = m.run_pending(c)
    assert r['failed'] is None and r['version'] == m.latest() >= 5
    assert {'idx_file_tags_tag', 'idx_print_history_user_sent', 'idx_print_history_user_path'} <= _idx(c)
    assert c.execute("SELECT COUNT(*) FROM file_tags").fetchone()[0] == 400
    assert m.run_pending(c)['applied'] == []                                  # 2e passage : rien à refaire
    plan = ' '.join(str(x) for x in c.execute("EXPLAIN QUERY PLAN SELECT file_path FROM file_tags WHERE tag_id=3").fetchall())
    assert 'idx_file_tags_tag' in plan                                        # l'index est réellement utilisé
    c.close()


def test_tables_absentes_ne_font_pas_echouer(tmp_path):
    m = _mig(); c = sqlite3.connect(str(tmp_path / 'v.db'))
    assert m.run_pending(c)['failed'] is None


def test_sauvegarde_avant_migration_et_rotation(tmp_path):
    m = _mig(); p = str(tmp_path / 'b.db'); _old_db(p)
    c = sqlite3.connect(p)
    c.executescript("CREATE TABLE pad (x TEXT);"); c.executemany("INSERT INTO pad VALUES (?)", [('x' * 200,)] * 100); c.commit()
    paths = [m.backup_before(c, [5], now=1000 + i) for i in range(5)]
    assert all(paths) and os.path.isfile(paths[-1])
    left = os.listdir(tmp_path / 'backups_migration')
    assert len(left) == m.KEEP_BACKUPS
    b = sqlite3.connect(paths[-1]); assert b.execute("SELECT COUNT(*) FROM file_tags").fetchone()[0] == 400; b.close()
    c.close()


def test_pas_de_sauvegarde_pour_une_base_neuve(tmp_path):
    m = _mig(); c = sqlite3.connect(str(tmp_path / 'n.db'))
    assert m.backup_before(c, [5]) is None
