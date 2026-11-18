"""1.1.6 — migration : une ancienne base est mise à niveau jusqu'au même schéma qu'une base neuve ; la version est inscrite."""
import logging, os, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import load_from_main


MIGRATIONS = ['migrate_print_history', 'migrate_printer_maintenance', 'migrate_stellio_extras',
              'migrate_manual_filament_spools', 'migrate_print_photos', 'migrate_users_recovery_code']


def _upgrade(ns):
    ns['init_db']()
    for name in MIGRATIONS:
        ns[name]()
    ns['stamp_schema_version']()


def _env(path):
    def get_db():
        c = sqlite3.connect(path); c.row_factory = sqlite3.Row; return c
    ns = load_from_main(['init_db', 'DB_SCHEMA_VERSION', 'stamp_schema_version', *MIGRATIONS], {'get_db': get_db, 'app_logger': logging.getLogger('x'), 'sqlite3': sqlite3, 'logging': logging})
    return ns, get_db


def _schema(get_db):
    c = get_db()
    try:
        out = {}
        for (name,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall():
            out[name] = sorted(r[1] for r in c.execute(f"PRAGMA table_info({name})").fetchall())
        return out
    finally:
        c.close()


def test_base_neuve_inscrit_la_version(tmp_path):
    ns, get_db = _env(str(tmp_path / 'new.db'))
    _upgrade(ns)
    c = get_db()
    assert c.execute("PRAGMA user_version").fetchone()[0] == ns['DB_SCHEMA_VERSION'] >= 1
    c.close()


def test_ancienne_base_rejoint_le_schema_courant(tmp_path):
    ns_new, new_db = _env(str(tmp_path / 'new.db'))
    _upgrade(ns_new)
    old_path = str(tmp_path / 'old.db')
    c = sqlite3.connect(old_path)
    # anciennes formes : colonnes ajoutées depuis par des ALTER TABLE
    c.executescript("""
        CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT,
                            email TEXT, created_at TIMESTAMP, reset_code TEXT, reset_expiry TIMESTAMP);
        CREATE TABLE print_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, file_path TEXT, file_name TEXT,
                                    file_size INTEGER, file_ext TEXT, slicer TEXT, sent_at TIMESTAMP);
        INSERT INTO users (username, password_hash) VALUES ('romain', 'x');
        INSERT INTO print_history (user_id, file_path, file_name) VALUES (1, '/a/b.stl', 'b.stl');
    """)
    c.commit(); c.close()
    ns_old, old_db = _env(old_path)
    _upgrade(ns_old)
    a, b = _schema(old_db), _schema(new_db)
    manquantes = {t: sorted(set(cols) - set(a.get(t, []))) for t, cols in b.items() if set(cols) - set(a.get(t, []))}
    assert not manquantes, manquantes                                           # rien ne manque après mise à niveau
    cc = old_db()
    assert cc.execute("SELECT COUNT(*) FROM print_history").fetchone()[0] == 1   # les données survivent
    assert cc.execute("SELECT role FROM users WHERE username='romain'").fetchone()[0] == 'user'
    assert cc.execute("PRAGMA user_version").fetchone()[0] == ns_old['DB_SCHEMA_VERSION']
    cc.close()


def test_init_db_idempotent(tmp_path):
    ns, get_db = _env(str(tmp_path / 'i.db'))
    _upgrade(ns); first = _schema(get_db)
    _upgrade(ns); assert _schema(get_db) == first


def test_version_dans_le_diagnostic():
    main = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'main.py'), encoding='utf-8').read()
    assert "info['schema_version']" in main and 'stamp_schema_version()' in main and 'PRAGMA user_version = ' in main
