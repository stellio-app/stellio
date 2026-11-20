"""Planning et capacité de production (modules/production_planning.py) : calcul pur + routes sur une vraie base SQLite."""
import datetime, importlib.util, os, sqlite3, sys, json
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
flask = pytest.importorskip('flask')


def _mod():
    spec = importlib.util.spec_from_file_location('production_planning_t', __import__('conftest').mod_path('production_planning'))
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


# ── v1.1.7 : coût total, rendement, retards ──────────────────────────────────
def JC(id, qty=10, done=0, scrap=0, status='queued', due='', done_at='', **kw):
    j = J(id, qty=qty, done=done, status=status, due=due, model={'m': 1.0, 'e': 0.2, 'w': 0.3, 'f': 0.5, 'weight_g': 20, 'hours': 1})
    j.update({'scrap': scrap, 'actual_hours': None, 'actual_weight_g': None, 'done_at': done_at})
    j.update(kw)
    return j


class _Row(dict):
    pass


def test_order_cost_estime_et_rendement():
    m = _mod()
    c = m.order_cost(_Row(JC(1, qty=10, done=8, scrap=2, status='done')))
    assert c['est']['total'] == pytest.approx(20.0)           # (1+0.2+0.3+0.5) × 10
    assert c['done'] == 8 and c['scrap'] == 2
    assert c['yield_pct'] == pytest.approx(80.0)
    assert c['waste'] > 0


def test_order_cost_sans_devis_chiffre():
    m = _mod()
    assert m.order_cost(_Row(J(1))) is None


def test_production_stats_ignore_annulees_et_compte_retards():
    m = _mod()
    jobs = [
        _Row(JC(1, qty=10, done=10, status='done', due='2026-11-05', done_at='2026-11-08 10:00:00')),     # 3 j de retard
        _Row(JC(2, qty=5, done=4, scrap=1, status='done', due='2026-11-10', done_at='2026-11-09 10:00:00')),   # à l'heure
        _Row(JC(3, qty=5, status='cancelled')),
    ]
    s = m.production_stats(jobs, '2026-11-01', '2026-11-16')
    assert s['cost']['orders'] == 2
    assert s['yield']['done'] == 14 and s['yield']['scrap'] == 1
    assert s['delays']['late'] == 1 and s['delays']['max_days'] == 3
    assert s['cost']['est'] > 0


def test_production_stats_vide():
    m = _mod()
    s = m.production_stats([], '2026-11-01', '2026-11-16')
    assert s['cost']['orders'] == 0 and s['by_order'] == []


def test_notify_emet_le_webhook_une_seule_fois_par_cle():
    m = _mod()
    seen, got = set(), []
    m._insert_notification_once = lambda uid, t, ti, msg, page, key: (key not in seen) and not seen.add(key)
    m._webhook_emit = lambda ev, data, uid: got.append((ev, data, uid))
    m._notify(3, 'planning_late', 'T', 'M', 'k1', 'order.late', {'x': 1})
    m._notify(3, 'planning_late', 'T', 'M', 'k1', 'order.late', {'x': 1})      # même clé : notification dédoublonnée, donc pas de second webhook
    m._notify(3, 'planning_late', 'T', 'M', 'k2')                              # sans évènement : rien
    assert got == [('order.late', {'x': 1}, 3)]


def test_rentabilite_par_imprimante():
    m = _mod()
    # devis 1 : 100 € pour 10 pièces réparties sur deux commandes (imprimante 1 : 6 pièces, imprimante 2 : 4)
    a = JC(1, qty=6, done=6, status='done', printer_id=1, done_at='2026-11-10', quote_id=7, actual_hours=6.0)
    b = JC(2, qty=4, done=2, scrap=1, status='printing', printer_id=2, quote_id=7, actual_hours=2.0)
    c = J(3, qty=2, done=2, status='done', printer=2); c['done_at'] = '2026-11-11'              # sans devis chiffré : ni revenu ni coût
    old = JC(4, qty=5, done=5, status='done', printer_id=1, done_at='2026-01-01', quote_id=8)   # hors période
    ann = JC(5, status='cancelled', printer_id=1, quote_id=7)
    rows = m.printer_profit([_Row(x) for x in (a, b, c, old, ann)], {7: 100.0, 8: 500.0}, PR, '2026-09-01')
    by = {r['printer_id']: r for r in rows}
    assert set(by) == {1, 2} and by[1]['orders'] == 1 and by[2]['orders'] == 2
    p1, p2 = by[1], by[2]
    assert p1['revenue'] == pytest.approx(100.0 * 6 / 10) and p1['done'] == 6 and p1['hours'] == 6.0 and p1['unpriced'] == 0
    assert p1['cost'] == pytest.approx(6 * 2.0) and p1['margin'] == pytest.approx(60 - 12) and p1['margin_per_hour'] == pytest.approx(8.0)
    assert p2['revenue'] == pytest.approx(100.0 * 2 / 10) and p2['unpriced'] == 1 and p2['scrap'] == 1 and p2['waste'] == pytest.approx(1 * 1.5)
    assert p2['done'] == 4 and p2['hours'] == 4.0 and p2['cost'] == pytest.approx(5.5) and p2['margin'] == pytest.approx(14.5) and p2['yield_pct'] == pytest.approx(80.0)
    assert rows[0]['printer_id'] == 1                                                      # meilleure marge par heure d'abord
    assert m.printer_profit([], {}, PR, '2026-09-01') == []
    # imprimante non attribuée : ligne à part, jamais fusionnée avec une autre
    n = m.printer_profit([_Row(JC(6, qty=1, done=1, status='done', printer_id=None, done_at='2026-11-12'))], {}, PR, '2026-09-01')
    assert len(n) == 1 and n[0]['printer_id'] is None and n[0]['revenue'] == 0 and n[0]['name'] == '—'


def test_route_expose_la_rentabilite_meme_sans_table_de_devis(tmp_path):
    c, m, get_db = _client(tmp_path)
    d = c.get('/api/planning').get_json()
    assert 'printer_profit' in d and isinstance(d['printer_profit'], list)
    assert d['printer_profit'][0]['printer_id'] == 1 and d['printer_profit'][0]['revenue'] == 0 and d['printer_profit'][0]['unpriced'] == 1
    # avec devis et colonnes complètes
    x = get_db()
    x.execute("CREATE TABLE quotes (id INTEGER PRIMARY KEY, user_id INTEGER, total_value REAL)"); x.execute("INSERT INTO quotes VALUES (9, 1, 80.0)")
    for col in ("quote_id INTEGER DEFAULT 0", "scrap INTEGER DEFAULT 0", "actual_hours REAL DEFAULT 0", "actual_weight_g REAL"):
        x.execute("ALTER TABLE print_jobs ADD COLUMN " + col)
    x.execute("UPDATE print_jobs SET quote_id = 9, qty_done = 2, est_hours = 1.5, cost_model = ?", (json.dumps({'m': 1, 'e': 0, 'w': 1, 'f': 0, 'weight_g': 10, 'hours': 1.5}),))
    x.commit(); x.close()
    r = c.get('/api/planning').get_json()['printer_profit'][0]
    assert r['revenue'] == pytest.approx(80.0 * 2 / 4) and r['cost'] == pytest.approx(2 * 2.0) and r['margin'] == pytest.approx(36.0) and r['hours'] == 3.0 and r['margin_per_hour'] == pytest.approx(12.0)


# ── temps de travail humain (v1.1.7) ───────────────────────────────────────────────────────────────────────────────

def test_temps_de_travail_estime_et_reel():
    m = _mod()
    j = _Row(JC(1, qty=10, done=4, status='printing', labor_setup_min=30, labor_min_piece=6))
    assert m.labor_minutes(j, 'est') == 30 + 6 * 10                  # préparation + toutes les pièces demandées
    assert m.labor_minutes(j, 'real') == 30 + 6 * 4                  # préparation (commencée) + pièces faites
    pas_commencee = _Row(JC(2, qty=10, done=0, status='queued', labor_setup_min=30, labor_min_piece=6))
    assert m.labor_minutes(pas_commencee, 'real') == 0               # rien de fait : rien de compté
    mesure = _Row(JC(3, qty=10, done=4, status='printing', labor_setup_min=30, labor_min_piece=6, labor_hours_actual=2.0))
    assert m.labor_minutes(mesure, 'real') == 120                    # un temps mesuré remplace l'estimation réelle
    assert m.labor_minutes(_Row(JC(4)), 'est') == 0 and m.labor_minutes(_Row(JC(5, labor_min_piece=-5)), 'est') == 0   # absent / négatif : 0


def test_taux_horaire_borne():
    m = _mod()
    assert m.clean_rate('abc') == 0 and m.clean_rate(None) == 0 and m.clean_rate(-3) == 0
    assert m.clean_rate(25.456) == 25.46 and m.clean_rate(99999) == 1000.0 and m.clean_rate(float('nan')) == 0


def test_le_travail_s_ajoute_au_cout_sans_changer_le_reste():
    m = _mod()
    base = m.order_cost(_Row(JC(1, qty=10, done=5, status='printing')))
    sans = m.order_cost(_Row(JC(1, qty=10, done=5, status='printing', labor_min_piece=6)), 0)       # taux 0 : rien ne change
    assert sans == base and 'labor' not in sans['real']
    avec = m.order_cost(_Row(JC(1, qty=10, done=5, status='printing', labor_setup_min=30, labor_min_piece=6)), 30.0)
    assert avec['est']['labor'] == pytest.approx((30 + 60) / 60 * 30) and avec['est']['total'] == pytest.approx(base['est']['total'] + 45.0)
    assert avec['real']['labor'] == pytest.approx((30 + 30) / 60 * 30) and avec['real']['total'] == pytest.approx(base['real']['total'] + 30.0)


def test_rentabilite_avec_travail_humain():
    m = _mod()
    a = JC(1, qty=6, done=6, status='done', printer_id=1, done_at='2026-11-10', quote_id=7, actual_hours=6.0, labor_setup_min=60, labor_min_piece=10)
    sans_devis = J(3, qty=2, done=2, status='done', printer=2); sans_devis['done_at'] = '2026-11-11'; sans_devis['labor_min_piece'] = 30
    rows = m.printer_profit([_Row(a), _Row(sans_devis)], {7: 100.0}, PR, '2026-09-01', labor_rate=24.0)
    by = {r['printer_id']: r for r in rows}
    h = (60 + 6 * 10) / 60                                           # 2 h de travail sur la commande chiffrée
    assert by[1]['labor_hours'] == pytest.approx(h) and by[1]['labor_cost'] == pytest.approx(h * 24)
    assert by[1]['cost'] == pytest.approx(6 * 2.0 + h * 24) and by[1]['margin'] == pytest.approx(100 - 12 - 48)   # revenu 100 (le seul lot du devis)
    assert by[2]['labor_hours'] == pytest.approx(1.0) and by[2]['labor_cost'] == 0 and by[2]['unpriced'] == 1      # heures comptées, pas valorisées sans devis
    zero = {r['printer_id']: r for r in m.printer_profit([_Row(a)], {7: 100.0}, PR, '2026-09-01')}
    assert zero[1]['labor_cost'] == 0 and zero[1]['margin'] == pytest.approx(88.0)                                     # taux 0 : marge inchangée


def test_route_taux_horaire_et_commandes(tmp_path):
    c, m, get_db = _client(tmp_path)
    assert c.get('/api/planning/settings').get_json()['labor_rate'] == 0
    assert c.put('/api/planning/settings', json={'default': {'hours_per_day': 6, 'days': [0, 1]}, 'printers': []}).status_code == 200
    assert c.put('/api/planning/settings', json={'labor_rate': 27.5}).status_code == 200                     # seul le taux change
    s = c.get('/api/planning/settings').get_json()
    assert s['labor_rate'] == 27.5 and s['default']['hours_per_day'] == 6 and s['default']['days'] == [0, 1]   # heures et jours conservés
    assert c.put('/api/planning/settings', json={'labor_rate': 5000}).status_code == 200
    assert c.get('/api/planning/settings').get_json()['labor_rate'] == 1000.0                                # borné
    assert c.get('/api/planning').get_json()['labor_rate'] == 1000.0


def test_marge_des_commandes_avec_travail():
    from conftest import load_from_main
    import importlib.util, os, sys
    sys.path.insert(0, os.path.dirname(__file__))
    ns = load_from_main(['_job_margin'], {'json': json, 'production_planning': _mod()})
    r = JC(1, qty=10, done=5, status='printing', labor_setup_min=30, labor_min_piece=6)
    r = _Row(r)
    r['cost_model'] = json.dumps({'m': 1.0, 'e': 0.2, 'w': 0.3, 'f': 0.5, 'weight_g': 20, 'hours': 1})
    base = ns['_job_margin'](r, 100.0)
    avec = ns['_job_margin'](r, 100.0, 30.0)
    assert base['labor_est'] == 0 and base['labor_real'] == 0
    assert avec['labor_est'] == pytest.approx(45.0) and avec['labor_real'] == pytest.approx(30.0)
    assert avec['est_margin'] == pytest.approx(base['est_margin'] - 45.0) and avec['real_margin'] == pytest.approx(base['real_margin'] - 30.0)
