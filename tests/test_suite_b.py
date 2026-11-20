"""1.1.7 — bloc B : tâches de fond, migrations versionnées, historique enrichi, alertes de licence."""
import datetime, importlib.util, os, sqlite3, threading, time
import pytest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _mod(name):
    spec = importlib.util.spec_from_file_location(name + '_t', os.path.join(ROOT, 'modules', name + '.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _conn():
    c = sqlite3.connect(':memory:'); c.row_factory = sqlite3.Row; return c


# ── gestionnaire de tâches ──
def test_jobs_execution_et_resultat():
    jm = _mod('job_manager'); m = jm.JobManager(autostart=False)
    j = m.submit('a', lambda ctx, x: x * 2, owner=1, args=(21,))
    assert j.state == 'queued'
    m.run_pending_inline()
    assert j.state == 'done' and j.result == 42 and j.finished >= j.started


def test_jobs_echec_isole():
    jm = _mod('job_manager'); m = jm.JobManager(autostart=False)
    bad = m.submit('bad', lambda ctx: 1 / 0, owner=1); ok = m.submit('ok', lambda ctx: 'fine', owner=1)
    m.run_pending_inline()
    assert bad.state == 'failed' and 'ZeroDivisionError' in bad.error and ok.state == 'done'


def test_jobs_annulation_file_et_cooperative():
    jm = _mod('job_manager'); m = jm.JobManager(autostart=False)
    q = m.submit('q', lambda ctx: 1, owner=1)
    assert m.cancel(q.id, 1) and q.state == 'cancelled'
    assert not m.cancel(q.id, 1)                                  # déjà terminée
    def long(ctx):
        for i in range(100):
            ctx.progress(i, 100)
            if i == 3:
                m.cancel(job.id, 1)
        return 'fini'
    job = m.submit('long', long, owner=1); m.run_pending_inline()
    assert job.state == 'cancelled' and job.progress['done'] <= 4


def test_jobs_pause_et_reprise():
    jm = _mod('job_manager'); m = jm.JobManager(workers=1)
    ev = threading.Event()
    def work(ctx):
        ev.set()
        for i in range(50):
            ctx.progress(i, 50); time.sleep(0.01)
        return 'ok'
    j = m.submit('p', work, owner=1)
    assert ev.wait(2)
    assert m.pause(j.id, 1)
    for _ in range(100):
        if j.state == 'paused':
            break
        time.sleep(0.02)
    assert j.state == 'paused'
    done_at = j.progress['done']; time.sleep(0.2); assert j.progress['done'] == done_at      # figée
    assert m.resume(j.id, 1)
    for _ in range(300):
        if j.state == 'done':
            break
        time.sleep(0.02)
    assert j.state == 'done' and j.result == 'ok'


def test_jobs_isolation_proprietaire_limite_et_purge():
    jm = _mod('job_manager'); m = jm.JobManager(autostart=False, keep=3)
    a = m.submit('a', lambda c: 1, owner=1); b = m.submit('b', lambda c: 1, owner=2)
    assert [x['name'] for x in m.list(1)] == ['a'] and not m.cancel(b.id, 1)
    for i in range(6):
        m.submit(f'n{i}', lambda c: 1, owner=1)
    m.run_pending_inline(); m.submit('z', lambda c: 1, owner=1)
    assert len([x for x in m.list() if x['state'] == 'done']) <= 3 + 1
    assert m.summary(1)['queued'] == 1


def test_jobs_concurrence_bornee():
    jm = _mod('job_manager'); m = jm.JobManager(workers=2)
    cur = {'n': 0, 'max': 0}; lock = threading.Lock()
    def w(ctx):
        with lock:
            cur['n'] += 1; cur['max'] = max(cur['max'], cur['n'])
        time.sleep(0.05)
        with lock:
            cur['n'] -= 1
    jobs = [m.submit(str(i), w, owner=1) for i in range(6)]
    for _ in range(200):
        if all(j.state == 'done' for j in jobs):
            break
        time.sleep(0.02)
    assert all(j.state == 'done' for j in jobs) and cur['max'] <= 2


# ── migrations ──
def test_migrations_appliquees_une_fois_dans_l_ordre():
    mg = _mod('migrations'); c = _conn()
    c.execute("CREATE TABLE print_history (id INTEGER PRIMARY KEY)")
    c.execute("CREATE TABLE file_origins (file_path TEXT)")
    c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY)")
    r = mg.run_pending(c, now=1)
    assert r['applied'] == [2, 3, 4] and r['failed'] is None and r['version'] == 4
    assert c.execute("PRAGMA user_version").fetchone()[0] == 4
    assert {'nozzle_temp', 'bed_temp', 'slicer_version'} <= {x[1] for x in c.execute("PRAGMA table_info(print_history)")}
    assert mg.run_pending(c)['applied'] == []                      # idempotent


def test_migration_en_echec_arrete_la_chaine_puis_reprend():
    mg = _mod('migrations'); c = _conn(); calls = []
    def ok2(conn): calls.append(2)
    state = {'boom': True}
    def bad3(conn):
        if state['boom']:
            raise RuntimeError('disque plein')
        calls.append(3)
    def ok4(conn): calls.append(4)
    ms = ((2, 'a', ok2), (3, 'b', bad3), (4, 'c', ok4))
    r = mg.run_pending(c, ms)
    assert r['failed']['version'] == 3 and calls == [2] and r['version'] == 2
    state['boom'] = False
    r = mg.run_pending(c, ms)
    assert calls == [2, 3, 4] and r['failed'] is None and r['version'] == 4


def test_migrations_ajout_de_colonne_tolere_table_absente():
    mg = _mod('migrations'); c = _conn()
    mg.add_column(c, 'inexistante', 'x', 'TEXT')                   # ne lève pas
    c.execute("CREATE TABLE t (a)"); mg.add_column(c, 't', 'b', 'INTEGER'); mg.add_column(c, 't', 'b', 'INTEGER')
    assert [x[1] for x in c.execute("PRAGMA table_info(t)")] == ['a', 'b']


def test_numeros_de_migration_uniques_et_croissants():
    mg = _mod('migrations'); nums = [v for v, _n, _f in mg.MIGRATIONS]
    assert nums == sorted(set(nums)) and nums[0] >= 2 and mg.latest() == nums[-1]


# ── historique enrichi ──
PRUSA = """; generated by PrusaSlicer 2.7.1 on 2026-01-01
G28
M104 S215
M140 S60
; temperature = 215
; bed_temperature = 60
"""
CURA = ";FLAVOR:Marlin\n;Generated with Cura_SteamEngine 5.6.0\n;EXTRUDER_TRAIN.0.INITIAL_TEMPERATURE:200\n;BUILD_PLATE.INITIAL_TEMPERATURE:55\n"
ORCA = "; generated by OrcaSlicer 2.1.1 on 2026\n; nozzle_temperature = 250\n; hot_plate_temp = 100\n"


def test_lecture_des_gcode():
    pe = _mod('print_enrich')
    assert pe.parse_gcode(PRUSA) == {'slicer': 'PrusaSlicer', 'slicer_version': '2.7.1', 'nozzle_temp': 215.0, 'bed_temp': 60.0}
    c = pe.parse_gcode(CURA); assert (c['slicer'], c['slicer_version'], c['nozzle_temp'], c['bed_temp']) == ('Cura', '5.6.0', 200.0, 55.0)
    o = pe.parse_gcode(ORCA); assert (o['slicer'], o['nozzle_temp'], o['bed_temp']) == ('OrcaSlicer', 250.0, 100.0)


def test_repli_sur_les_commandes_m_et_valeurs_absurdes_ignorees():
    pe = _mod('print_enrich')
    r = pe.parse_gcode("G28\nM109 S205\nM190 S50\n")
    assert r['slicer'] is None and r['nozzle_temp'] == 205.0 and r['bed_temp'] == 50.0
    r = pe.parse_gcode("M104 S0\nM140 S0\n; temperature = 9999\n")        # extinction / hors bornes : rien d'inventé
    assert r['nozzle_temp'] is None and r['bed_temp'] is None
    assert pe.parse_gcode('')['slicer_version'] is None


def test_enrichissement_ne_remplace_pas_une_valeur_deja_saisie(tmp_path):
    pe = _mod('print_enrich'); c = _conn()
    c.execute("CREATE TABLE print_history (id INTEGER PRIMARY KEY, user_id INT, file_path TEXT, file_ext TEXT, nozzle_temp REAL, bed_temp REAL, slicer_version TEXT)")
    c.execute("INSERT INTO print_history VALUES (1, 7, '/x/a.gcode', '.gcode', 230, NULL, '')")
    found = pe.enrich_row(c, 7, 1, text=PRUSA)
    row = c.execute("SELECT nozzle_temp, bed_temp, slicer_version FROM print_history").fetchone()
    assert tuple(row) == (230.0, 60.0, '2.7.1') and found['bed_temp'] == 60.0         # la buse saisie à la main est conservée
    assert pe.enrich_row(c, 8, 1, text=PRUSA) is None                                  # autre compte : introuvable


def test_lecture_tete_et_pied_d_un_gros_fichier(tmp_path):
    pe = _mod('print_enrich')
    f = tmp_path / 'big.gcode'
    f.write_text(PRUSA + ('G1 X1 Y1\n' * 200000) + '; bed_temperature = 61\n')
    text = pe.read_gcode_text(str(f))
    assert 'PrusaSlicer 2.7.1' in text and len(text) < pe.HEAD_BYTES + pe.TAIL_BYTES + 10


# ── licences ──
def test_classification_des_echeances():
    lw = _mod('license_watch'); today = datetime.date(2026, 11, 18)
    assert lw.classify('2026-11-17', today) == ('expired', -1)
    assert lw.classify('2026-11-18', today) == ('soon', 0)
    assert lw.classify('2026-12-18', today) == ('soon', 30)
    assert lw.classify('2026-12-19', today) == ('ok', 31)
    assert lw.classify('', today) == (None, None) and lw.classify('pas une date', today) == (None, None)


def test_liste_des_licences_a_surveiller_triee():
    lw = _mod('license_watch'); today = datetime.date(2026, 11, 18)
    rows = [{'file_path': '/a/ok.stl', 'license': 'CC0', 'license_expires': '2030-01-01'},
            {'file_path': '/a/vieux.stl', 'license': 'Commercial', 'license_expires': '2026-01-01'},
            {'file_path': '/a/bientot.stl', 'license': 'Commercial', 'license_expires': '2026-11-25'}]
    out = lw.expiring(rows, today)
    assert [o['name'] for o in out] == ['vieux.stl', 'bientot.stl'] and out[0]['status'] == 'expired' and out[1]['days_left'] == 7


def test_gestionnaire_manuel_ne_lance_aucun_fil():
    import threading
    jm = _mod('job_manager'); m = jm.JobManager(autostart=False, keep=50)
    before = threading.active_count()
    for i in range(8):
        m.submit(f'n{i}', lambda c: 1, owner=1)
    m.run_pending_inline()
    m.submit('z', lambda c: 1, owner=1)
    assert threading.active_count() <= before and m.summary(1)['queued'] == 1 and m.summary(1)['done'] == 8
