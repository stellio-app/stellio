"""Tests v1.0.6 : devis client en ligne, ZIP comptable, stock de pièces, répartition, résumé, pesées, partage de profils.
Chaque module est chargé à part (nouvelle copie), initialisé avec de faux services de main.py et une base SQLite temporaire."""
import base64, datetime, importlib.util, io, logging, os, sqlite3, sys, zipfile
import pytest
from flask import Flask, Response, jsonify, request, send_file, session
from werkzeug.utils import secure_filename

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_module(name):
    spec = importlib.util.spec_from_file_location(f'_t_{name}', os.path.join(ROOT, 'modules', f'{name}.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Env:
    def __init__(self, tmp_path):
        self.db = str(tmp_path / 't.db')
        self.app = Flask('t')
        self.app.secret_key = 'x'
        self.settings = {}
        self.notifs = []
        self.pushes = []
        self.logger = logging.getLogger('t106')
        conn = self.conn()
        conn.executescript("""
        CREATE TABLE users (id INTEGER PRIMARY KEY, role TEXT DEFAULT 'admin');
        INSERT INTO users (id, role) VALUES (1,'admin'),(2,'viewer');
        CREATE TABLE quotes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, number TEXT, client TEXT DEFAULT '',
          item_desc TEXT DEFAULT '', qty INTEGER DEFAULT 1, total TEXT DEFAULT '', total_value REAL DEFAULT 0,
          status TEXT DEFAULT 'draft', doc_type TEXT DEFAULT 'quote', created_at TEXT DEFAULT '2026-10-05 10:00:00',
          due_date TEXT DEFAULT '', filename TEXT DEFAULT '', sent_at TEXT DEFAULT '');
        CREATE TABLE print_jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, quote_id INTEGER DEFAULT 0,
          client TEXT DEFAULT '', part TEXT DEFAULT '', quantity INTEGER DEFAULT 1, qty_done INTEGER DEFAULT 0,
          material TEXT DEFAULT '', printer_id INTEGER, notes TEXT DEFAULT '', status TEXT DEFAULT 'queued',
          due_date TEXT DEFAULT '', done_at TEXT DEFAULT '', cost_model TEXT DEFAULT '{}');
        CREATE TABLE manual_filament_spools (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT,
          remaining_g REAL, capacity_g REAL DEFAULT 1000, archived INTEGER DEFAULT 0, updated_at TEXT);
        CREATE TABLE remote_instances (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, url TEXT, peer_key TEXT);
        """)
        conn.commit(); conn.close()
        self.ns = {
            'app': self.app, 'app_logger': self.logger, 'get_db': self.conn, 'jsonify': jsonify, 'request': request,
            'session': session, 'Response': Response, 'send_file': send_file, 'secure_filename': secure_filename,
            'login_required': self.login_required, 'require_peer_key': self.peer_key,
            'load_settings': lambda: dict(self.settings), 'save_settings': lambda d: self.settings.update(d),
            '_insert_notification_once': self.notify_once, '_push_notify_async': lambda *a: self.pushes.append(a),
            '_ensure_quote_columns': lambda: None, '_least_loaded_printer': lambda c, u: 7,
        }

    def conn(self):
        c = sqlite3.connect(self.db)
        c.row_factory = sqlite3.Row
        return c

    @staticmethod
    def login_required(f):
        from functools import wraps
        @wraps(f)
        def w(*a, **k):
            if not session.get('user_id'):
                return jsonify({'error': 'auth'}), 401
            return f(*a, **k)
        return w

    @staticmethod
    def peer_key(f):
        from functools import wraps
        @wraps(f)
        def w(*a, **k):
            if request.headers.get('X-Stellio-Peer-Key') != 'secret':
                return jsonify({'error': 'forbidden'}), 403
            return f(*a, **k)
        return w

    def notify_once(self, uid, typ, title, msg, page, key):
        if any(n[5] == key for n in self.notifs):
            return False
        self.notifs.append((uid, typ, title, msg, page, key))
        return True

    def client(self, logged=True):
        c = self.app.test_client()
        if logged:
            with c.session_transaction() as s:
                s['user_id'] = 1
        return c

    def sql(self, q, a=()):
        c = self.conn(); cur = c.execute(q, a); c.commit(); rows = cur.fetchall() if cur.description else []; c.close(); return rows


@pytest.fixture
def env(tmp_path):
    return Env(tmp_path)


# ── 1. Devis client en ligne ──
def _portal(env, tmp_path):
    def stored(qid):
        r = env.sql("SELECT * FROM quotes WHERE id=? AND user_id=?", (qid, 1))
        return r[0] if r else None
    env.ns.update({
        'QUOTES_DIR': str(tmp_path), '_build_quote_pdf_with_repair': lambda p, encrypt=False: b'%PDF', '_stored_quote': stored,
        '_create_jobs_from_quote': lambda uid, row: 2, '_quote_payload_path': lambda r: None,
        '_safe_quote_pdf_filename': lambda n: 'q.pdf', '_stored_quote_path': lambda r: None,
        'get_local_ip': lambda: '10.0.0.5', 'get_remote_state': lambda: {'status': 'ready', 'url': 'https://stellio.example.org', 'mode': 'custom'}})
    m = load_module('quote_portal'); m.init(env.ns)
    env.sql("INSERT INTO quotes (user_id, number, client, item_desc, total) VALUES (1,'D-001','Zoé','Support','12,00 €')")
    return m


def test_portal_flow(env, tmp_path):
    m = _portal(env, tmp_path)
    c = env.client()
    r = c.post('/api/quotes/1/portal').get_json()
    assert r['success'] and '/quote/' in r['url']
    token = r['token']
    assert env.sql("SELECT status FROM quotes")[0]['status'] == 'sent'
    pub = env.client(logged=False)
    c.post('/api/quote-portal/settings', json={'payment_info': 'IBAN FR76', 'payment_link': 'https://pay.example/x'})
    d = pub.get(f'/quote/{token}/data').get_json()
    assert d['can_decide'] and d['payment_info'] == '' and d['payment_link'] == ''
    assert 'user_id' not in d and 'public_token' not in d
    assert pub.get(f'/quote/{token}').status_code == 200
    res = pub.post(f'/quote/{token}/decision', json={'decision': 'accept', 'name': 'Zoé <b>'}).get_json()
    assert res['success'] and res['status'] == 'accepted' and res['jobs_created'] == 2
    assert res['payment_info'] == 'IBAN FR76'
    assert env.notifs and 'accepté' in env.notifs[0][2]
    again = pub.post(f'/quote/{token}/decision', json={'decision': 'refuse'})
    assert again.status_code == 409
    assert pub.get(f'/quote/{token}/data').get_json()['payment_info'] == 'IBAN FR76'
    assert '<' not in env.sql("SELECT decision_by FROM quotes")[0]['decision_by']


def test_portal_security(env, tmp_path):
    m = _portal(env, tmp_path)
    c, pub = env.client(), env.client(logged=False)
    assert pub.post('/api/quotes/1/portal').status_code == 401
    assert pub.get('/quote/not-a-token-xx/data').status_code == 404
    assert c.post('/api/quote-portal/settings', json={'payment_link': 'javascript:alert(1)'}).status_code == 400
    token = c.post('/api/quotes/1/portal').get_json()['token']
    assert pub.post(f'/quote/{token}/decision', json={'decision': 'x'}).status_code == 400
    c.delete('/api/quotes/1/portal')
    assert pub.get(f'/quote/{token}/data').status_code == 404


def test_portal_rate_limit(env, tmp_path):
    m = _portal(env, tmp_path)
    token = env.client().post('/api/quotes/1/portal').get_json()['token']
    pub = env.client(logged=False)
    codes = [pub.post(f'/quote/{token}/decision', json={'decision': 'bad'}).status_code for _ in range(12)]
    assert codes[:10] == [400] * 10 and 429 in codes[10:]


# ── 2. ZIP comptable ──
def test_accounting_zip(env, tmp_path):
    pdf = tmp_path / 'f1.pdf'; pdf.write_bytes(b'%PDF-1')
    env.ns.update({
        '_csv_args': lambda src: (src.get('from', ''), src.get('to', ''), [], src.get('lang', 'fr')),
        '_iso_date': lambda x: x, '_quote_eff_status': lambda r: r['status'],
        '_quotes_csv_bytes': lambda *a: b'a;b\n', '_wv_save_dialog': lambda w: 1,
        '_stored_quote_path': lambda r: str(pdf) if r['doc_type'] != 'quote' else None})
    m = load_module('accounting_zip'); m.init(env.ns)
    env.sql("INSERT INTO quotes (user_id, number, doc_type, total_value, status, created_at) VALUES "
            "(1,'F-1','invoice',100,'paid','2026-09-10 10:00:00'),(1,'F-2','invoice',50,'sent','2026-09-20 10:00:00'),"
            "(1,'A-1','credit',-30,'sent','2026-09-25 10:00:00'),(1,'F-3','invoice',70,'paid','2026-10-02 10:00:00')")
    r = env.client().get('/api/quotes/export-zip?month=2026-09&lang=fr')
    assert r.status_code == 200 and r.headers['X-Stellio-Documents'] == '3'
    z = zipfile.ZipFile(io.BytesIO(r.data))
    names = set(z.namelist())
    assert {'documents.csv', 'recapitulatif.csv', 'LISEZMOI.txt', 'pdf/invoice/F-1.pdf', 'pdf/invoice/F-2.pdf', 'pdf/credit/A-1.pdf'} <= names
    assert 'pdf/invoice/F-3.pdf' not in names
    recap = z.read('recapitulatif.csv').decode('utf-8-sig')
    assert 'NET' in recap and '120,00' in recap          # 100 + 50 − 30
    assert env.client(logged=False).get('/api/quotes/export-zip').status_code == 401


# ── 3. Stock de pièces ──
def test_parts_stock(env):
    m = load_module('parts_stock'); m.init(env.ns)
    c = env.client()
    pid = c.post('/api/parts-stock', json={'name': 'Clip', 'min_qty': 5, 'reorder_qty': 20, 'auto_restock': True, 'material': 'pla'}).get_json()['id']
    assert c.post(f'/api/parts-stock/{pid}/adjust', json={'set': 8}).get_json()['qty'] == 8
    assert c.post(f'/api/parts-stock/{pid}/adjust', json={'delta': -4}).get_json()['qty'] == 4
    assert [n for n in env.notifs if n[5].startswith('parts_low:')]   # l'ajustement a déjà déclenché l'alerte
    jobs = env.sql("SELECT * FROM print_jobs WHERE stock_part_id=?", (pid,))
    assert len(jobs) == 1 and jobs[0]['quantity'] == 20 and jobs[0]['printer_id'] == 7
    assert m.check_low_stock(1) == 0                       # même valeur de stock : pas de doublon
    assert len(env.sql("SELECT * FROM print_jobs WHERE stock_part_id=?", (pid,))) == 1
    env.sql("UPDATE print_jobs SET qty_done=12, status='done' WHERE stock_part_id=?", (pid,))
    assert m.sync_completed_restocks(1) == 12
    assert m.sync_completed_restocks(1) == 0               # idempotent
    assert c.get('/api/parts-stock').get_json()['parts'][0]['qty'] == 16
    assert c.post(f'/api/parts-stock/{pid}/restock', json={'quantity': 5}).get_json()['success']
    assert c.delete(f'/api/parts-stock/{pid}').get_json()['success']
    assert c.post('/api/parts-stock', json={'name': ''}).status_code == 400


# ── 4. Répartition ──
def _disp(env):
    env.ns.update({'_printer_status_cached': lambda p: {}, 'parse_printer_config': lambda r: dict(r)})
    m = load_module('printer_dispatch'); m.init(env.ns); return m


def test_score_printer(env):
    m = _disp(env)
    job = {'material': 'PLA', 'cost_model': '{"weight_g": 100}', 'quantity': 2, 'qty_done': 0}

    class J(dict):
        pass
    job = J(job)
    assert m.score_printer(job, {}, {'status': 'offline'}, 0) is None
    idle = m.score_printer(job, {}, {'status': 'idle', 'ams': [{'material': 'pla', 'remaining_g': 500}]}, 0)
    busy = m.score_printer(job, {}, {'status': 'printing'}, 0)
    assert idle[0] == 150 and 'material_loaded' in idle[1] and busy[0] == -20
    chg = m.score_printer(job, {}, {'status': 'idle', 'ams': [{'material': 'PETG'}]}, 2)
    assert chg[0] == 100 - 30 - 10 and 'material_change' in chg[2]
    low = m.score_printer(job, {}, {'status': 'idle', 'ams': [{'material': 'PLA', 'remaining_g': 50}]}, 0)
    assert 'not_enough_filament' in low[2] and low[0] == 130


def test_dispatch_apply(env):
    env.sql("CREATE TABLE printers (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT)")
    env.sql("INSERT INTO printers VALUES (1,1,'A'),(2,1,'B')")
    env.sql("INSERT INTO print_jobs (user_id, part, material, printer_id) VALUES (1,'p1','PLA',1)")
    m = _disp(env)
    m._printer_status_cached = lambda p: {'status': 'printing'} if p['id'] == 1 else {'status': 'idle'}
    c = env.client()
    s = c.get('/api/dispatch/suggestions').get_json()['suggestions']
    assert s[0]['best']['printer_id'] == 2 and s[0]['change']
    assert c.post('/api/dispatch/apply', json={}).get_json()['changed'] == 1
    assert env.sql("SELECT printer_id, status FROM print_jobs")[0]['printer_id'] == 2
    assert env.sql("SELECT status FROM print_jobs")[0]['status'] == 'queued'       # jamais lancée


# ── 5. Résumé ──
def _digest(env):
    env.ns.update({'_is_low_stock': lambda r, c: False})
    m = load_module('digest'); m.init(env.ns); return m


def test_digest_period_and_tick(env):
    m = _digest(env)
    cfg = {'frequency': 'daily', 'hour': 8, 'weekday': 0}
    assert m.period_key(datetime.datetime(2026, 11, 3, 7, 59), cfg) is None
    assert m.period_key(datetime.datetime(2026, 11, 3, 8, 0), cfg) == 'daily:2026-11-03'
    w = {'frequency': 'weekly', 'hour': 9, 'weekday': 2}
    assert m.period_key(datetime.datetime(2026, 11, 3, 12), w) is None       # mardi, avant mercredi
    assert m.period_key(datetime.datetime(2026, 11, 4, 9), w).startswith('weekly:2026-W')
    env.sql("INSERT INTO quotes (user_id, number, status) VALUES (1,'D-9','sent')")
    env.settings.update({'digest_enabled': True, 'digest_hour': 8})
    now = datetime.datetime(2026, 11, 3, 9, 0)
    assert m.tick(now) is True
    assert m.tick(now) is False                                            # déjà envoyé pour cette période
    assert len([n for n in env.notifs if n[5].startswith('digest:')]) == 1
    assert env.pushes


def test_digest_disabled_and_render(env):
    m = _digest(env)
    assert m.tick(datetime.datetime(2026, 11, 3, 9)) is False
    title, text = m.render({}, 'daily', 'fr')
    assert title and text
    t2, x2 = m.render({'pending': {'n': 2}}, 'weekly', 'en')
    assert '2' in x2
    c = env.client()
    assert c.post('/api/digest/settings', json={'enabled': True, 'frequency': 'weekly', 'hour': 99, 'weekday': 3}).get_json()['success'] is not False
    cfg = c.get('/api/digest/settings').get_json()
    assert cfg['frequency'] == 'weekly' and cfg['hour'] == 23 and cfg['weekday'] == 3 and cfg['enabled']
    assert c.post('/api/digest/send-now', json={}).get_json()['sent']


# ── 6. Pesées de bobines ──
def test_consumption_rate(env):
    env.ns.update({'_get_tigertag_slots': lambda uid: []})
    m = load_module('filament_weighing'); m.init(env.ns)
    d0 = datetime.datetime(2026, 11, 1)
    D = lambda days, g: (d0 + datetime.timedelta(days=days), g)
    assert m.consumption_rate([D(0, 1000)])[0] is None
    rate, n = m.consumption_rate([D(0, 1000), D(5, 750), D(10, 500)])
    assert abs(rate - 50) < 0.01 and n == 3
    rate, n = m.consumption_rate([D(0, 100), D(1, 1000), D(3, 900), D(5, 800)])      # remplacement de bobine au jour 1
    assert abs(rate - 50) < 0.01 and n == 3
    assert m.consumption_rate([D(0, 500), D(0.1, 499)])[0] is None                  # intervalle trop court


def test_weigh_and_forecast(env):
    slots = [{'source_id': 'tt1', 'name': 'PLA noir', 'remaining_g': 800, 'capacity_g': 1000}]
    env.ns.update({'_get_tigertag_slots': lambda uid: slots})
    m = load_module('filament_weighing'); m.init(env.ns)
    c = env.client()
    assert c.post('/api/filament/weigh-sync').get_json()['recorded'] == 1
    assert c.post('/api/filament/weigh-sync').get_json()['recorded'] == 0            # variation < 1 g
    old = (datetime.datetime.now() - datetime.timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S')
    env.sql("UPDATE spool_weighings SET remaining_g=1000, recorded_at=?", (old,))
    slots[0]['remaining_g'] = 800
    c.post('/api/filament/weigh-sync')
    f = c.get('/api/filament/forecast').get_json()['spools'][0]
    assert abs(f['g_per_day'] - 20) < 1 and abs(f['days_left'] - 40) < 3
    env.sql("INSERT INTO manual_filament_spools (user_id, name, remaining_g) VALUES (1,'Manuel',900)")
    r = c.post('/api/filament/weigh', json={'source_id': 1, 'gross_g': 1250, 'tare_g': 250}).get_json()
    assert r['success'] and r['remaining_g'] == 1000
    assert env.sql("SELECT remaining_g FROM manual_filament_spools")[0]['remaining_g'] == 1000
    assert c.post('/api/filament/weigh', json={'source_id': 99, 'remaining_g': 5}).status_code == 404
    assert c.post('/api/filament/weigh', json={'source_id': 1}).status_code == 400


# ── 7. Partage de profils ──
def test_profile_receive_and_send(env, tmp_path):
    store = []
    env.ns.update({
        'IMPORTED_PROFILES_DIR': str(tmp_path), 'requests': None,
        '_parse_slicer_profile_file': lambda fn, blob: [{'name': blob.decode().strip(), 'slicer': 'orca'}] if blob.strip() else [],
        'load_slicer_profiles': lambda: list(store), 'save_slicer_profiles': lambda p: (store.clear(), store.extend(p))})
    m = load_module('profile_share'); m.init(env.ns)
    pub = env.client(logged=False)
    body = {'filename': 'a.json', 'content_b64': base64.b64encode(b'PLA fin').decode()}
    assert pub.post('/api/peer/receive-profile', json=body).status_code == 403
    H = {'X-Stellio-Peer-Key': 'secret'}
    assert pub.post('/api/peer/receive-profile', json=body, headers=H).get_json()['imported'] == 1
    assert pub.post('/api/peer/receive-profile', json=body, headers=H).get_json()['already_present'] is True
    assert pub.post('/api/peer/receive-profile', json={**body, 'filename': 'evil.py'}, headers=H).status_code == 400
    assert pub.post('/api/peer/receive-profile', json={**body, 'content_b64': '***'}, headers=H).status_code == 400
    assert pub.post('/api/peer/receive-profile', json={**body, 'content_b64': base64.b64encode(b'x' * 2_100_000).decode()}, headers=H).status_code == 413
    # envoi : le fichier doit rester dans le dossier des profils importés
    inside = tmp_path / 'p.json'; inside.write_text('PETG')
    outside = tmp_path.parent / 'secret.json'; outside.write_text('x')
    store.extend([{'id': 'ok', 'name': 'n', 'source_path': str(inside), 'source_filename': 'p.json'},
                  {'id': 'bad', 'name': 'n2', 'source_path': str(outside), 'source_filename': 'secret.json'}])
    c = env.client()
    assert c.get('/api/slicer-profiles/ok/export').status_code == 200
    assert c.get('/api/slicer-profiles/bad/export').status_code == 404
    assert c.post('/api/slicer-profiles/bad/send-to-instance', json={'instance_id': 1}).status_code == 404
    assert c.post('/api/slicer-profiles/ok/send-to-instance', json={}).status_code == 400
    assert c.post('/api/slicer-profiles/ok/send-to-instance', json={'instance_id': 5}).status_code == 404


def test_portal_never_creates_a_local_link(env, tmp_path):
    m = _portal(env, tmp_path)
    c = env.client()
    m.get_remote_state = lambda: {'status': 'off'}
    r = c.post('/api/quotes/1/portal')
    assert r.status_code == 409 and r.get_json()['error'] == 'remote_required' and r.get_json()['remote'] is False
    assert env.sql("SELECT status FROM quotes WHERE id=1")[0][0] == 'draft'              # aucun lien : le devis reste brouillon
    assert not env.sql("SELECT public_token FROM quotes WHERE id=1")[0][0]
    m.get_remote_state = lambda: {'status': 'starting', 'mode': 'quick'}
    assert c.post('/api/quotes/1/portal').get_json()['remote_status'] == 'starting'
    m.get_remote_state = lambda: {'status': 'ready', 'url': 'https://abc.trycloudflare.com/', 'mode': 'quick'}
    r = c.post('/api/quotes/1/portal').get_json()
    assert r['success'] and r['url'].startswith('https://abc.trycloudflare.com/quote/') and r['remote'] is True
    d = c.get('/api/quote-portal/links').get_json()
    assert d['remote'] is True and d['remote_mode'] == 'quick' and d['quotes'][0]['url'] == r['url']
    m.get_remote_state = lambda: {'status': 'off'}                                      # l'accès distant tombe : lien masqué, jamais d'adresse locale
    d = c.get('/api/quote-portal/links').get_json()
    assert d['remote'] is False and d['quotes'][0]['url'] == '' and d['quotes'][0]['has_link'] is True
    assert '10.0.0.5' not in str(d)
