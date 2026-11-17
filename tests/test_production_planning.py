"""Planning et capacité de production (modules/production_planning.py) : calcul pur + routes sur une vraie base SQLite."""
import datetime, importlib.util, os, sqlite3, sys, json
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
flask = pytest.importorskip('flask')


def _mod():
    spec = importlib.util.spec_from_file_location('production_planning_t', os.path.join(ROOT, 'modules', 'production_planning.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def J(id, part='P', qty=1, done=0, hours=1.0, printer=1, due='', status='queued', model=None):
    return {'id': id, 'part': part, 'client': 'C', 'quantity': qty, 'qty_done': done, 'est_hours': hours, 'cost_model': json.dumps(model or {}),
            'printer_id': printer, 'due_date': due, 'status': status, 'done_at': '', 'created_at': ''}


NOW = datetime.datetime(2026, 11, 16, 8, 0)      # un lundi, 8 h
PR = [{'id': 1, 'name': 'A'}, {'id': 2, 'name': 'B'}]
SET = {'default': {'hours_per_day': 10, 'days': [0, 1, 2, 3, 4]}, 'printers': {}}


def test_jours_et_heures_normalises():
    m = _mod()
    assert m.parse_days('0,2,9,x') == (0, 2) or m.parse_days('0,2,9') == (0, 2)
    assert m.parse_days([]) == m.DEFAULT_DAYS and m.parse_days(None) == m.DEFAULT_DAYS
    assert m.clamp_hours('abc') == 16.0 and m.clamp_hours(99) == 24.0 and m.clamp_hours(0) == 0.5


def test_duree_par_piece_vient_de_la_commande_sinon_du_devis():
    m = _mod()
    assert m.hours_per_piece(J(1, hours=2.5)) == 2.5
    assert m.hours_per_piece(J(1, hours=0, model={'hours': 1.25})) == 1.25
    assert m.hours_per_piece(J(1, hours=0)) == 0.0


def test_fin_estimee_enchaine_les_commandes_et_saute_le_week_end():
    m = _mod()
    # aujourd'hui lundi 8 h : 10 h dispo aujourd'hui (jusqu'à minuit : 16 h restantes, plafonné à 10)
    r = m.plan([J(1, qty=1, hours=10), J(2, qty=1, hours=25)], PR, {}, SET, NOW)
    a, b = r['jobs']
    assert a['end'] == '2026-11-16'                      # 10 h = journée de lundi
    assert b['end'] == '2026-11-19'                      # +25 h : mar (10) + mer (10) + jeu (5)
    r2 = m.plan([J(1, qty=1, hours=45)], PR, {}, SET, NOW)
    assert r2['jobs'][0]['end'] == '2026-11-20'          # lun→ven = 50 h
    r3 = m.plan([J(1, qty=1, hours=55)], PR, {}, SET, NOW)
    assert r3['jobs'][0]['end'] == '2026-11-23'          # saute samedi/dimanche


def test_retard_prevu_et_marge():
    m = _mod()
    r = m.plan([J(1, qty=1, hours=25, due='2026-11-18'), J(2, qty=1, hours=5, due='2026-11-30', printer=2)], PR, {}, SET, NOW)
    j1 = next(j for j in r['jobs'] if j['id'] == 1)
    assert j1['end'] == '2026-11-18' or j1['late_predicted'] is False
    r = m.plan([J(1, qty=1, hours=35, due='2026-11-18')], PR, {}, SET, NOW)
    j = r['jobs'][0]
    assert j['end'] == '2026-11-19' and j['late_predicted'] and j['slack_days'] == -1
    assert any(a['type'] == 'late_predicted' and a['job_id'] == 1 for a in r['alerts'])


def test_surcharge_capacite_contre_charge():
    m = _mod()
    r = m.plan([J(1, qty=100, hours=1.0)], [PR[0]], {}, SET, NOW, horizon_days=7)
    p = r['printers'][0]
    assert p['capacity_hours'] == 50.0 and p['queue_hours'] == 100.0 and p['load_pct'] == 200.0
    assert any(a['type'] == 'overload' and a['printer_id'] == 1 for a in r['alerts'])
    assert r['summary']['load_pct'] == 200.0 and r['summary']['free_hours'] == 0
    r = m.plan([J(1, qty=10, hours=1.0)], [PR[0]], {}, SET, NOW, horizon_days=7)
    assert r['printers'][0]['load_pct'] == 20.0 and not [a for a in r['alerts'] if a['type'] == 'overload']


def test_commande_sans_duree_signalee_et_non_planifiee():
    m = _mod()
    r = m.plan([J(1, hours=0), J(2, hours=2)], PR, {}, SET, NOW)
    assert [j['id'] for j in r['jobs']] == [2] and r['no_duration'][0]['id'] == 1
    assert r['summary']['no_duration'] == 1 and any(a['type'] == 'no_duration' for a in r['alerts'])


def test_commande_sans_imprimante_va_sur_la_plus_libre_a_titre_indicatif():
    m = _mod()
    r = m.plan([J(1, hours=30, printer=1), J(2, hours=5, printer=None)], PR, {}, SET, NOW)
    j2 = next(j for j in r['jobs'] if j['id'] == 2)
    assert j2['printer_id'] == 2 and j2['virtual'] is True


def test_impression_en_cours_compte_son_temps_restant():
    m = _mod()
    st = {1: {'status': 'printing', 'time': {'remaining': 3600 * 4}}}
    r = m.plan([J(1, qty=3, done=0, hours=2, status='printing')], [PR[0]], st, SET, NOW)
    p = r['printers'][0]
    assert p['busy_hours'] == 4.0
    assert p['queue_hours'] == 8.0          # 4 h restantes de la pièce en cours + 2 pièces × 2 h
    assert r['jobs'][0]['start'] == '2026-11-16'


def test_imprimante_desactivee_et_jours_par_imprimante():
    m = _mod()
    s = {'default': SET['default'], 'printers': {1: {'enabled': False}, 2: {'hours_per_day': 4, 'days': [1]}}}
    r = m.plan([J(1, hours=2, printer=1), J(2, hours=2, printer=2)], PR, {}, s, NOW)
    assert not any(p['id'] == 1 and p['enabled'] for p in r['printers'])
    j2 = next(j for j in r['jobs'] if j['id'] == 2)
    assert j2['end'] == '2026-11-17'        # seulement le mardi pour la machine B
    assert any(j['id'] == 1 for j in r['jobs']) is True  # la commande de A (désactivée) est replacée sur B
    assert next(j for j in r['jobs'] if j['id'] == 1)['printer_id'] == 2


def test_aucune_imprimante_active():
    m = _mod()
    r = m.plan([J(1, hours=2)], [], {}, SET, NOW)
    assert r['jobs'] == [] and any(a['type'] == 'no_printer' for a in r['alerts'])


def test_taux_de_respect_des_delais():
    m = _mod()
    rows = [dict(J(1, due='2026-11-10'), done_at='2026-11-09'), dict(J(2, due='2026-11-10'), done_at='2026-11-12'),
            dict(J(3, due=''), done_at='2026-11-12'), dict(J(4, due='2026-01-10'), done_at='2026-01-01')]
    r = m.on_time_rate(rows, '2026-10-01')
    assert r == {'rate': 50.0, 'on_time': 1, 'total': 2}
    assert m.on_time_rate([], '2026-10-01')['rate'] is None


# ── routes sur une vraie base ────────────────────────────────────────────

def _client(tmp_path):
    m = _mod()
    db = str(tmp_path / 't.db')

    def get_db():
        c = sqlite3.connect(db); c.row_factory = sqlite3.Row; return c
    c = get_db()
    c.execute("CREATE TABLE printers (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT)")
    c.execute("CREATE TABLE print_jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, part TEXT, client TEXT DEFAULT '', quantity INTEGER DEFAULT 1, "
              "qty_done INTEGER DEFAULT 0, printer_id INTEGER, due_date TEXT DEFAULT '', status TEXT DEFAULT 'queued', done_at TEXT DEFAULT '', cost_model TEXT DEFAULT '')")
    c.execute("INSERT INTO printers VALUES (1, 1, 'Prusa'), (2, 2, 'Autre compte')")
    c.execute("INSERT INTO print_jobs (user_id, part, quantity, printer_id, due_date) VALUES (1, 'Support', 4, 1, '2099-01-01')")
    c.commit(); c.close()
    app = flask.Flask('t'); app.secret_key = 'x'
    services = dict(app=app, app_logger=__import__('logging').getLogger('t'), get_db=get_db, jsonify=flask.jsonify, login_required=lambda f: f,
                    parse_printer_config=lambda r: {'id': r['id'], 'name': r['name']}, request=flask.request, session={'user_id': 1},
                    _printer_status_cached=lambda p: {'status': 'idle'})
    m.init(services)
    return app.test_client(), m, get_db


def test_routes_planning_reglages_et_ajout_colonne(tmp_path):
    c, m, get_db = _client(tmp_path)
    cols = {r['name'] for r in get_db().execute("PRAGMA table_info(print_jobs)").fetchall()}
    assert 'est_hours' in cols                                           # colonne ajoutée à l'initialisation
    d = c.get('/api/planning?horizon=7').get_json()
    assert d['horizon_days'] == 7 and d['printers'][0]['name'] == 'Prusa' and d['summary']['no_duration'] == 1
    db = get_db(); db.execute("UPDATE print_jobs SET est_hours=2"); db.commit(); db.close()
    d = c.get('/api/planning').get_json()
    assert d['horizon_days'] == 14 and d['jobs'][0]['hours'] == 8.0 and d['jobs'][0]['end']
    assert c.get('/api/planning?horizon=abc').status_code == 200
    s = c.get('/api/planning/settings').get_json()
    assert [p['id'] for p in s['printers']] == [1]                       # pas l'imprimante d'un autre compte
    r = c.put('/api/planning/settings', json={'default': {'hours_per_day': 8, 'days': [0, 1, 2]},
                                               'printers': [{'id': 1, 'hours_per_day': 20, 'days': [5, 6], 'enabled': True}, {'id': 2, 'hours_per_day': 3}]})
    assert r.get_json()['success']
    s = c.get('/api/planning/settings').get_json()
    assert s['default'] == {'hours_per_day': 8.0, 'days': [0, 1, 2]}
    assert s['printers'][0]['hours_per_day'] == 20.0 and s['printers'][0]['days'] == [5, 6]
    assert not get_db().execute("SELECT 1 FROM planning_capacity WHERE printer_id=2").fetchone()   # imprimante d'un autre compte ignorée
    p = c.get('/api/planning').get_json()['printers'][0]
    assert p['hours_per_day'] == 20.0 and p['days'] == [5, 6]


def test_alertes_retard_dedoublonnees(tmp_path):
    c, m, get_db = _client(tmp_path)
    db = get_db(); db.execute("UPDATE print_jobs SET est_hours=50, due_date='2026-11-17'"); db.commit(); db.close()
    sent = []
    m._insert_notification_once = lambda uid, t, title, msg, link, key: (sent.append((t, key)) or True) if (t, key) not in sent else False
    m.planning_alerts_once(NOW)
    m.planning_alerts_once(NOW)
    assert [t for t, _k in sent].count('planning_late') == 1
