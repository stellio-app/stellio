"""Stellio — migrations de base de données versionnées (1.1.7).

Chaque évolution du schéma est une fonction numérotée, appliquée UNE fois, dans l'ordre, et notée dans la table `schema_migrations`
(version, nom, date, résultat). Le numéro le plus élevé appliqué est inscrit dans `PRAGMA user_version`. Une migration en échec
arrête la chaîne (les suivantes dépendent d'elle) et est signalée ; Stellio démarre quand même. Les migrations historiques
(`migrate_*` de main.py, idempotentes) continuent de tourner avant ; ce module prend le relais pour tout ce qui est nouveau.
Ajouter une migration : écrire `_mNN(conn)`, l'ajouter à `MIGRATIONS` avec le numéro suivant, ne JAMAIS modifier une migration publiée.
"""
import time

_REQUIRED = (
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'session',
)
_OPTIONAL = ()
_OVERRIDABLE = ('time',)

_MAIN = {}
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
session = None


def has_table(conn, table):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def has_column(conn, table, column):
    return any(r[1] == column for r in conn.execute(f"PRAGMA table_info({table})").fetchall())


def add_column(conn, table, column, decl):
    """ALTER TABLE ADD COLUMN idempotent ; ignore une table absente (elle sera créée avec la colonne ailleurs)."""
    if has_table(conn, table) and not has_column(conn, table, column):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")


def _m2(conn):       # historique d'impression enrichi : températures réelles et version du slicer
    add_column(conn, 'print_history', 'nozzle_temp', 'REAL')
    add_column(conn, 'print_history', 'bed_temp', 'REAL')
    add_column(conn, 'print_history', 'slicer_version', "TEXT DEFAULT ''")


def _m3(conn):       # date d'expiration de la licence d'un modèle
    add_column(conn, 'file_origins', 'license_expires', 'TEXT')


def _m4(conn):       # rôle d'équipe d'un compte invité (operator / manager / admin ; vide = lecture seule)
    add_column(conn, 'users', 'team_role', "TEXT DEFAULT ''")


MIGRATIONS = (
    (2, 'print_history_temperatures_slicer', _m2),
    (3, 'license_expiry', _m3),
    (4, 'users_team_role', _m4),
)


def latest():
    return max(v for v, _n, _f in MIGRATIONS)


def _ensure(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at REAL, ok INTEGER NOT NULL DEFAULT 1, error TEXT DEFAULT '')""")


def applied(conn):
    _ensure(conn)
    return {r[0]: {'name': r[1], 'applied_at': r[2], 'ok': bool(r[3]), 'error': r[4]} for r in
            conn.execute("SELECT version, name, applied_at, ok, error FROM schema_migrations").fetchall()}


def run_pending(conn, migrations=None, now=None):
    """Applique les migrations manquantes, dans l'ordre. Retourne {'applied': [...], 'failed': None|{version, error}, 'version': n}."""
    migrations = sorted(migrations if migrations is not None else MIGRATIONS, key=lambda m: m[0])
    done = applied(conn)
    out = {'applied': [], 'failed': None}
    for version, name, fn in migrations:
        if done.get(version, {}).get('ok'):
            continue
        try:
            fn(conn)
            conn.execute("INSERT OR REPLACE INTO schema_migrations (version, name, applied_at, ok, error) VALUES (?,?,?,1,'')",
                         (version, name, now if now is not None else time.time()))
            conn.commit()
            out['applied'].append(version)
        except Exception as e:
            try:
                conn.rollback()
                conn.execute("INSERT OR REPLACE INTO schema_migrations (version, name, applied_at, ok, error) VALUES (?,?,?,0,?)",
                             (version, name, now if now is not None else time.time(), f"{type(e).__name__}: {e}"[:300]))
                conn.commit()
            except Exception:
                pass
            out['failed'] = {'version': version, 'error': f"{type(e).__name__}: {e}"[:300]}
            break
    ok_versions = [v for v, i in applied(conn).items() if i['ok']]
    out['version'] = max(ok_versions) if ok_versions else 0
    try:
        cur = conn.execute("PRAGMA user_version").fetchone()[0]
        if out['version'] > cur:
            conn.execute(f"PRAGMA user_version = {int(out['version'])}")
            conn.commit()
    except Exception:
        pass
    return out


def run_pending_safe():
    """Appelé au démarrage : au mieux, ne bloque jamais le lancement."""
    try:
        conn = get_db()
        try:
            res = run_pending(conn)
        finally:
            conn.close()
        if res['applied']:
            app_logger.info(f"[DB] Migrations appliquées : {res['applied']}")
        if res['failed']:
            app_logger.warning(f"[DB] Migration en échec : {res['failed']}")
        return res
    except Exception as e:
        try:
            app_logger.warning(f"[DB] Migrations non exécutées : {type(e).__name__}: {e}")
        except Exception:
            pass
        return None


def api_migrations():
    if session.get('role') == 'viewer':
        return jsonify({'error': 'Réservé au compte propriétaire.'}), 403
    conn = get_db()
    try:
        done = applied(conn)
        rows = [{'version': v, 'name': n, **done.get(v, {'ok': False, 'applied_at': None, 'error': ''}), 'pending': not done.get(v, {}).get('ok')}
                for v, n, _f in MIGRATIONS]
        return jsonify({'migrations': rows, 'latest': latest(), 'user_version': conn.execute("PRAGMA user_version").fetchone()[0]})
    finally:
        conn.close()


_ROUTES = (
    ('/api/db/migrations', ['GET'], 'api_migrations', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"{__name__}.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    if routes:
        run_pending_safe()
    return {}
