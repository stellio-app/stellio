"""1.1.7 — alertes d'expiration de licence : notifications dédoublonnées, par compte, jamais de suppression."""
import datetime, importlib.util, logging, os, sqlite3
import pytest
flask = pytest.importorskip('flask')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _setup(tmp_path):
    spec = importlib.util.spec_from_file_location('license_watch_t', os.path.join(ROOT, 'modules', 'license_watch.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    db = str(tmp_path / 'l.db')
    def get_db():
        c = sqlite3.connect(db); c.row_factory = sqlite3.Row; return c
    c = get_db()
    c.execute("CREATE TABLE file_origins (file_path TEXT, user_id INT, license TEXT, license_expires TEXT)")
    for row in (('/s/a.stl', 1, 'CC-BY', '2026-11-10'), ('/s/b.stl', 1, 'Commerciale', '2026-11-25'), ('/s/c.stl', 1, 'MIT', '2027-06-01'), ('/s/d.stl', 2, 'CC0', '2026-11-01'), ('/s/e.stl', 1, 'X', '')):
        c.execute("INSERT INTO file_origins VALUES (?,?,?,?)", row)
    c.commit(); c.close()
    store, push, native = set(), [], []
    sent = []
    def once(uid, t, title, msg, page, key):
        if (uid, key) in store: return False
        store.add((uid, key)); sent.append((uid, t, title, msg, page)); return True
    app = flask.Flask('l')
    m.init(dict(app=app, app_logger=logging.getLogger('t'), get_db=get_db, jsonify=flask.jsonify, login_required=lambda f: f, request=flask.request, session=flask.session,
                _insert_notification_once=once, _push_notify_async=lambda *a: push.append(a), _send_native_notification=lambda *a: native.append(a)))
    return m, sent, push, native, get_db


def test_alertes_creees_une_fois_par_compte_et_par_etat(tmp_path):
    m, sent, push, native, db = _setup(tmp_path)
    today = datetime.date(2026, 11, 18)
    assert m.alerts_once(today) == 3                                               # a (expirée), b (J-7), d (autre compte, expirée) ; c trop loin, e sans date
    kinds = sorted((u, t) for u, t, *_ in sent); assert kinds == [(1, 'license_expired'), (1, 'license_soon'), (2, 'license_expired')]
    assert len(push) == 3 and len(native) == 3 and all(s[4] == 'library' for s in sent)
    assert m.alerts_once(today) == 0 and m.alerts_once(today + datetime.timedelta(days=1)) == 0     # pas de répétition tant que rien ne change d'état
    assert m.alerts_once(datetime.date(2026, 11, 26)) == 1                                           # b passe d'« bientôt » à « expirée » : nouvelle alerte
    assert 'b.stl' in sent[-1][3] and sent[-1][1] == 'license_expired'
    n = db().execute("SELECT COUNT(*) FROM file_origins").fetchone()[0]; assert n == 5               # aucune suppression
    assert m.alerts_once(today, days=400) == 1                                                       # c entre dans la fenêtre élargie


def test_sans_service_de_notification_ou_colonne_rien_ne_casse(tmp_path):
    m, *_ = _setup(tmp_path)
    m._insert_notification_once = None
    assert m.alerts_once() == 0
    spec = importlib.util.spec_from_file_location('lw2', os.path.join(ROOT, 'modules', 'license_watch.py'))
    m2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(m2)
    db = sqlite3.connect(str(tmp_path / 'vide.db')); db.row_factory = sqlite3.Row; db.execute("CREATE TABLE file_origins (file_path TEXT, user_id INT)")
    m2.init(dict(app=flask.Flask('x'), app_logger=logging.getLogger('t'), get_db=lambda: type('C', (), {'execute': lambda s, *a: db.execute(*a), 'close': lambda s: None})(),
                 jsonify=flask.jsonify, login_required=lambda f: f, request=flask.request, session=flask.session, _insert_notification_once=lambda *a: True))
    assert m2.alerts_once() == 0                                                                     # base non migrée : aucune erreur


def test_boucle_et_branchement_main():
    src = open(os.path.join(ROOT, 'main.py'), encoding='utf-8').read()
    assert 'license_watch._loop' in src
