"""v1.0.4 — prise connectée (Shelly / Tasmota / Home Assistant), énergie par impression, photo de fin, surveillance IA.
Le module print_session.py est importé tel quel (copie fraîche à chaque test) et reçoit de faux services via init() :
fausse prise HTTP, base SQLite temporaire, faux appels IA / caméra."""
import base64, datetime, io, json, os, re, sqlite3, threading, time, uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

import pytest

# Dépendances facultatives en CI minimale (pip install pytest numpy) : sans elles, ces tests sont ignorés, pas en erreur.
requests = pytest.importorskip('requests')
pytest.importorskip('PIL')
from PIL import Image

import importlib.util

PS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'modules', 'print_session.py')


def _load_module():
    spec = importlib.util.spec_from_file_location('print_session_under_test', PS_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _enc(s):
    return 'enc:' + base64.b64encode(s.encode()).decode() if s else None


def _dec(s):
    return base64.b64decode(s[4:]).decode() if s and s.startswith('enc:') else None


# ── Fausse prise HTTP ───────────────────────────────────────────────────────────────────────
class _State:
    shelly_gen = 2
    power = 120.0
    energy_wh = 1000.0
    ha_token = 'tok'


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == '/rpc/Switch.GetStatus' and _State.shelly_gen == 2:
            return self._send(200, {'apower': _State.power, 'aenergy': {'total': _State.energy_wh}})
        if u.path.startswith('/rpc/'):
            return self._send(404, {})
        if u.path == '/status':
            return self._send(200, {'meters': [{'power': _State.power, 'total': _State.energy_wh * 60}]})
        if u.path == '/cm':
            assert parse_qs(u.query)['cmnd'] == ['Status 8']
            return self._send(200, {'StatusSNS': {'ENERGY': {'Power': _State.power, 'Total': _State.energy_wh / 1000.0}}})
        if u.path.startswith('/api/states/'):
            if self.headers.get('Authorization') != f'Bearer {_State.ha_token}':
                return self._send(401, {})
            ent = u.path.rsplit('/', 1)[1]
            if ent == 'sensor.plug_power':
                return self._send(200, {'state': str(_State.power / 1000.0), 'attributes': {'unit_of_measurement': 'kW'}})
            if ent == 'sensor.plug_energy':
                return self._send(200, {'state': str(_State.energy_wh / 1000.0), 'attributes': {'unit_of_measurement': 'kWh'}})
            if ent == 'sensor.off':
                return self._send(200, {'state': 'unavailable', 'attributes': {}})
        return self._send(404, {})


@pytest.fixture(scope='module')
def server():
    srv = HTTPServer(('127.0.0.1', 0), _Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f'http://127.0.0.1:{srv.server_address[1]}'
    srv.shutdown()


@pytest.fixture(autouse=True)
def _reset_state():
    _State.shelly_gen, _State.power, _State.energy_wh, _State.ha_token = 2, 120.0, 1000.0, 'tok'


# ── Environnement simulé pour les fonctions extraites ───────────────────────────────────────
class _SyncThread:
    def __init__(self, target=None, args=(), kwargs=None, **kw):
        self.t, self.a, self.k = target, args, kwargs or {}

    def start(self):
        self.t(*self.a, **self.k)


class _FakeThreading:
    Thread = _SyncThread
    Lock = threading.Lock


def _jpeg(color=(200, 30, 30), size=(320, 240)):
    buf = io.BytesIO()
    Image.new('RGB', size, color).save(buf, 'JPEG')
    return buf.getvalue()


@pytest.fixture()
def env(tmp_path):
    db = str(tmp_path / 't.db')
    c = sqlite3.connect(db)
    c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY)")
    c.execute("INSERT INTO users (id) VALUES (1)")
    c.execute("""CREATE TABLE print_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, file_path TEXT, file_name TEXT,
                 sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, printer_id INTEGER, material_cost REAL, elec_cost REAL, total_cost REAL)""")
    c.execute("CREATE TABLE print_photos (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, file_path TEXT, image_filename TEXT, note TEXT, result TEXT)")
    c.execute("INSERT INTO print_history (user_id, file_path, file_name, printer_id, material_cost) VALUES (1, '/lib/Benchy.3mf', 'Benchy.3mf', 7, 0.5)")
    c.commit()
    c.close()

    def get_db():
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        return conn

    photos = tmp_path / 'photos'
    photos.mkdir()
    alerts, ai_calls = [], []
    settings = {'print_cost_elec_price': 0.25}

    class _Log:
        def info(self, *a, **k): pass
        warning = error = info

    ai = {'text': '{"verdict":"ok","reason":""}', 'source': 'ollama', 'local': '', 'lowmem': False}

    def _call_ai(prompt, **kw):
        ai_calls.append((prompt, kw))
        return ai['text'], ai['source']

    class _Lock:
        def acquire(self, timeout=None): return True
        def release(self): pass

    ns_extra = dict(
        get_db=get_db, load_settings=lambda: settings, app_logger=_Log(), requests=requests, Image=Image, io=io,
        base64=base64, uuid=uuid, re=re, json=json, datetime=datetime, threading=_FakeThreading, time=time,
        PRINT_PHOTOS_DIR=str(photos),
        encrypt_password=lambda s: _enc(s),
        decrypt_password=lambda s: _dec(s),
        _timelapse_grab_frame=lambda printer: ns_ref['grab'](printer),
        _ws_alert=lambda uid, ntype, title, msg, key, link='printers': alerts.append((uid, ntype, title, msg, key)),
        _server_t=lambda k, d: d, _call_ai=_call_ai, _visual_call_lock=_Lock(), _visual_local_check=lambda: ai['local'],
        _low_memory=lambda: ai['lowmem'], _visual_ollama_opts=lambda m: {},
        AIDisabledError=type('AIDisabledError', (RuntimeError,), {}),
    )
    mod = _load_module()
    ns_extra.update(app=None, jsonify=None, request=None, session=None, login_required=lambda f: f,
                    parse_printer_config=lambda row: json.loads(row['config']) if row['config'] else {},
                    _printer_status_cached=lambda *a, **k: None)
    mod.init(ns_extra, routes=False)
    ns = vars(mod)
    ns_ref = {'grab': lambda printer: _jpeg()}
    ns['_ns_ref'] = ns_ref
    ns['_alerts'], ns['_ai_calls'], ns['_settings'], ns['_ai'], ns['_photos'] = alerts, ai_calls, settings, ai, photos
    ns['_db'] = get_db
    ns['_ensure_v104_tables']()          # le suivi réel le fait au démarrage (_start_v104_worker)
    return ns


# ── Config & sécurité ───────────────────────────────────────────────────────────────────────
def test_clean_host(env):
    f = env['_meter_clean_host']
    assert f('192.168.1.50') == 'http://192.168.1.50'
    assert f('HTTPS://ha.local:8123/') == 'https://ha.local:8123'
    assert f('shelly.lan') == 'http://shelly.lan'
    assert f('') == '' and f('a b') == '' and f('http://x;rm -rf') == ''
    assert f('169.254.169.254') == ''                       # métadonnées cloud refusées
    assert f('javascript:alert(1)') == ''


def test_clean_config_token_never_clear_and_kept_on_edit(env):
    clean = env['_v104_clean_config']
    cfg = clean({'end_photo': 1, 'ai_watch': True, 'meter': {'kind': 'homeassistant', 'host': 'ha.local:8123',
                 'entity': 'sensor.plug_power', 'energy_entity': 'sensor.plug_energy', 'token': 'SECRET'}}, {})
    m = cfg['meter']
    assert cfg['end_photo'] and cfg['ai_watch']
    assert 'token' not in m and 'SECRET' not in json.dumps(cfg) and m['token_enc'] == _enc('SECRET')
    # édition sans nouveau jeton : l'ancien est conservé
    cfg2 = clean({'meter': {'kind': 'homeassistant', 'host': 'ha.local:8123', 'entity': 'sensor.plug_power'}}, cfg)
    assert cfg2['meter']['token_enc'] == _enc('SECRET') and 'end_photo' not in cfg2
    # effacement explicite
    cfg3 = clean({'meter': {'kind': 'homeassistant', 'host': 'ha.local:8123', 'clear_token': True}}, cfg)
    assert 'token_enc' not in cfg3['meter']
    # prise supprimée / type inconnu / hôte invalide
    assert 'meter' not in clean({'meter': {'kind': 'none'}}, cfg)
    assert 'meter' not in clean({'meter': {'kind': 'shelly', 'host': '!!'}}, cfg)
    assert clean({'meter': {'kind': 'shelly', 'host': '10.0.0.5', 'channel': 99}})['meter']['channel'] == 0


def test_apply_config_strips_plain_token_from_http_printers(env):
    raw = {'port': '7125', 'meter': {'kind': 'shelly', 'host': 'x', 'token': 'PLAIN'}, 'end_photo': True}
    env['_v104_apply_config'](raw, {'meter': {'kind': 'shelly', 'host': '10.0.0.5'}}, {})
    assert 'PLAIN' not in json.dumps(raw) and raw['meter']['host'] == 'http://10.0.0.5' and 'end_photo' not in raw
    assert raw['port'] == '7125'


def test_public_config_hides_token(env):
    pub = env['_v104_public_config']({'meter': {'kind': 'tasmota', 'host': 'h', 'token_enc': _enc('x')}})
    assert pub['meter'] == {'kind': 'tasmota', 'host': 'h', 'has_token': True}


# ── Lecture des prises ──────────────────────────────────────────────────────────────────────
def test_shelly_gen2_and_gen1(env, server):
    m = {'kind': 'shelly', 'host': server, 'channel': 0}
    assert env['_meter_read'](m) == {'power_w': 120.0, 'energy_wh': 1000.0}
    _State.shelly_gen = 1                                    # Gen1 : /status, total en watt-minutes
    assert env['_meter_read'](m) == {'power_w': 120.0, 'energy_wh': 1000.0}


def test_tasmota(env, server):
    d = env['_meter_read']({'kind': 'tasmota', 'host': server})
    assert d == {'power_w': 120.0, 'energy_wh': 1000.0}


def test_home_assistant_units_and_auth(env, server):
    m = {'kind': 'homeassistant', 'host': server, 'entity': 'sensor.plug_power', 'energy_entity': 'sensor.plug_energy',
         'token_enc': _enc('tok')}
    d = env['_meter_read'](m)
    assert d['power_w'] == pytest.approx(120.0) and d['energy_wh'] == pytest.approx(1000.0)
    with pytest.raises(PermissionError):
        env['_meter_read'](dict(m, token_enc=None))             # sans jeton
    _State.ha_token = 'other'
    with pytest.raises(PermissionError):
        env['_meter_read'](m)
    _State.ha_token = 'tok'
    with pytest.raises(ValueError):
        env['_meter_read'](dict(m, entity='sensor.off', energy_entity=None))


def test_poll_backoff_and_live_cache(env, server):
    bad = {'kind': 'shelly', 'host': 'http://127.0.0.1:9', 'channel': 0}
    poll = env['_v104_poll_meter']
    for i in range(3):
        live = poll(5, bad, 1000.0 + i)
        assert live['ok'] is False
    assert env['_METER_FAIL'][5][0] == 3 and env['_METER_FAIL'][5][1] > 1002
    assert poll(5, bad, 1010.0) is env['_METER_LIVE'][5]     # en attente : pas de nouvel essai


# ── Session d'impression complète (compteur) ────────────────────────────────────────────────
def _printer(meter=None, **flags):
    cfg = dict(flags)
    if meter:
        cfg['meter'] = meter
    return {'id': 7, 'user_id': 1, 'name': 'Ender', 'config': cfg}


def test_session_counter_energy_cost_and_history(env, server):
    meter = {'kind': 'shelly', 'host': server, 'channel': 0}
    pr = _printer(meter)
    step, sess = env['_v104_step'], env['_V104_SESS']
    t0 = 10_000.0
    _State.energy_wh = 1000.0
    step(pr, {'status': 'printing', 'file': 'Benchy.gcode', 'progress': 1}, t0)
    assert 7 in sess and sess[7]['cnt_start'] == 1000.0
    for i in range(1, 7):                                    # 1 h simulée : 150 W
        _State.power, _State.energy_wh = 150.0, 1000.0 + 25.0 * i
        step(pr, {'status': 'printing', 'file': 'Benchy.gcode', 'progress': 10 * i}, t0 + 600 * i)
    # imprimante au repos : d'abord rien (anti-parasite 15 s), puis fin
    step(pr, {'status': 'idle'}, t0 + 3600 + 5)
    assert 7 in sess
    step(pr, {'status': 'idle'}, t0 + 3600 + 25)
    assert 7 not in sess
    row = env['_db']().execute("SELECT * FROM print_energy").fetchone()
    assert row['measured_by'] == 'counter' and row['energy_wh'] == pytest.approx(150.0)
    assert row['cost'] == pytest.approx(0.15 * 0.25, abs=1e-4) and row['avg_w'] == pytest.approx(150 / (3625 / 3600), abs=3)
    h = env['_db']().execute("SELECT * FROM print_history").fetchone()
    assert h['energy_wh'] == pytest.approx(150.0) and h['energy_measured'] == 1
    assert h['elec_cost'] == pytest.approx(0.0375) and h['total_cost'] == pytest.approx(0.5375)
    # la puissance mesurée sert ensuite aux estimations (≥ 15 min, au moins 2 sessions ou 1 h)
    assert env['_measured_avg_power_w'](7) == pytest.approx(row['avg_w'], abs=0.2)


def test_session_samples_fallback_without_counter(env, server):
    class NoCounter:   # prise qui ne donne que les watts
        pass
    meter = {'kind': 'homeassistant', 'host': server, 'entity': 'sensor.plug_power', 'token_enc': _enc('tok')}
    pr = _printer(meter)
    step = env['_v104_step']
    t0 = 20_000.0
    _State.power = 200.0
    step(pr, {'status': 'printing', 'file': 'x.gcode', 'progress': 5}, t0)
    for i in range(1, 31):
        step(pr, {'status': 'printing', 'file': 'x.gcode', 'progress': 5}, t0 + 10 * i)
    step(pr, {'status': 'idle'}, t0 + 305)
    step(pr, {'status': 'idle'}, t0 + 330)
    row = env['_db']().execute("SELECT * FROM print_energy").fetchone()
    assert row['measured_by'] == 'samples'
    assert row['energy_wh'] == pytest.approx(200.0 * 290 / 3600, rel=0.05)


def test_short_print_and_unknown_grace(env, server):
    meter = {'kind': 'shelly', 'host': server, 'channel': 0}
    pr = _printer(meter)
    step, sess = env['_v104_step'], env['_V104_SESS']
    step(pr, {'status': 'printing', 'file': 'a.gcode'}, 100.0)
    step(pr, {'status': 'idle'}, 150.0)
    step(pr, {'status': 'idle'}, 170.0)                       # 70 s : annulation / test, rien d'enregistré
    assert 7 not in sess and env['_db']().execute("SELECT COUNT(*) FROM print_energy").fetchone()[0] == 0
    step(pr, {'status': 'printing', 'file': 'b.gcode'}, 1000.0)
    step(pr, {'status': 'offline'}, 1100.0)                   # injoignable : la session reste ouverte
    assert 7 in sess
    step(pr, {'status': 'printing', 'file': 'b.gcode'}, 1200.0)
    assert sess[7]['unknown_since'] is None


# ── Photo de fin d'impression ───────────────────────────────────────────────────────────────
def test_end_photo_goes_to_existing_gallery(env):
    pr = _printer(end_photo=True)
    step = env['_v104_step']
    step(pr, {'status': 'printing', 'file': 'Benchy.gcode'}, 5000.0)
    step(pr, {'status': 'idle'}, 5400.0)
    step(pr, {'status': 'idle'}, 5420.0)
    rows = env['_db']().execute("SELECT * FROM print_photos").fetchall()
    assert len(rows) == 1 and rows[0]['result'] == 'success'
    assert rows[0]['file_path'] == '/lib/Benchy.3mf'          # rattachée au fichier de la bibliothèque
    assert os.path.isfile(os.path.join(env['_photos'], rows[0]['image_filename']))
    assert 'Ender' in rows[0]['note']


def test_end_photo_failed_when_printer_error_and_no_history(env):
    pr = _printer(end_photo=True)
    step = env['_v104_step']
    step(pr, {'status': 'printing', 'file': 'Inconnu.gcode'}, 5000.0)
    step(pr, {'status': 'error'}, 5400.0)
    step(pr, {'status': 'error'}, 5425.0)
    r = env['_db']().execute("SELECT * FROM print_photos").fetchone()
    assert r['result'] == 'failed' and r['file_path'] == 'printer/7/Inconnu.gcode'


def test_no_camera_no_crash(env):
    env['_ns_ref']['grab'] = lambda printer: None
    pr = _printer(end_photo=True)
    step = env['_v104_step']
    step(pr, {'status': 'printing', 'file': 'x.gcode'}, 1.0)
    step(pr, {'status': 'idle'}, 400.0)
    step(pr, {'status': 'idle'}, 420.0)
    assert env['_db']().execute("SELECT COUNT(*) FROM print_photos").fetchone()[0] == 0


# ── Surveillance IA ─────────────────────────────────────────────────────────────────────────
def test_parse_verdict(env):
    p = env['_v104_parse_verdict']
    assert p('{"verdict":"failed","reason":"spaghetti on the bed"}') == ('failed', 'spaghetti on the bed')
    assert p('Sure! {"verdict": "ok", "reason": ""}') == ('ok', '')
    assert p('The print has failed') == ('failed', '')
    assert p('???') == ('unsure', '') and p('') == ('unsure', '')


def _run_ai(env, t0, pr, n_checks, progress=40):
    step = env['_v104_step']
    t = t0
    step(pr, {'status': 'printing', 'file': 'Benchy.gcode', 'progress': progress}, t)
    for _ in range(n_checks):
        t += 400
        step(pr, {'status': 'printing', 'file': 'Benchy.gcode', 'progress': progress}, t)
    return t


def test_ai_needs_two_consecutive_failures(env):
    pr = _printer(ai_watch=True)
    env['_ai']['text'] = '{"verdict":"failed","reason":"spaghetti"}'
    t = _run_ai(env, 1000.0, pr, 1)
    assert not env['_alerts'] and env['_V104_SESS'][7]['ai_fail'] == 1
    env['_v104_step'](pr, {'status': 'printing', 'file': 'Benchy.gcode', 'progress': 41}, t + 61)   # 2e vérification 60 s plus tard
    assert len(env['_alerts']) == 1
    uid, ntype, title, msg, key = env['_alerts'][0]
    assert ntype == 'print_failed' and 'Ender' in msg and 'spaghetti' in msg and key.startswith('print_failed_ai_7_')
    ph = env['_db']().execute("SELECT * FROM print_photos").fetchall()
    assert len(ph) == 1 and ph[0]['result'] == 'failed'       # preuve ajoutée à la galerie
    # pas de seconde alerte pour la même impression
    env['_v104_step'](pr, {'status': 'printing', 'file': 'Benchy.gcode', 'progress': 45}, t + 61 + 2000)
    assert len(env['_alerts']) == 1


def test_ai_ok_resets_counter_and_uses_image_and_progress(env):
    pr = _printer(ai_watch=True)
    env['_ai']['text'] = '{"verdict":"failed","reason":"x"}'
    t = _run_ai(env, 1000.0, pr, 1)
    env['_ai']['text'] = '{"verdict":"ok","reason":""}'
    env['_v104_step'](pr, {'status': 'printing', 'file': 'Benchy.gcode', 'progress': 41}, t + 61)
    assert env['_V104_SESS'][7]['ai_fail'] == 0 and not env['_alerts']
    prompt, kw = env['_ai_calls'][-1]
    assert '41%' in prompt and kw['images'] and base64.b64decode(kw['images'][0])[:2] == b'\xff\xd8'


def test_ai_alert_gives_a_single_end_photo_left_to_the_user(env):
    # v1.0.7 : une seule photo (celle de fin), « Réussi » par défaut ; la raison IA est dans son commentaire, l'utilisateur tranche
    pr = _printer(ai_watch=True, end_photo=True)
    env['_ai']['text'] = '{"verdict":"failed","reason":"detached"}'
    t = _run_ai(env, 1000.0, pr, 1)
    env['_v104_step'](pr, {'status': 'printing', 'file': 'Benchy.gcode', 'progress': 41}, t + 61)
    env['_v104_step'](pr, {'status': 'idle'}, t + 600)
    env['_v104_step'](pr, {'status': 'idle'}, t + 620)
    res = [r['result'] for r in env['_db']().execute("SELECT result FROM print_photos ORDER BY id").fetchall()]
    assert res == ['success']
    note = env['_db']().execute("SELECT note FROM print_photos").fetchone()['note']
    assert 'detached' in note


def test_ai_privacy_and_guards(env):
    pr = _printer(ai_watch=True)
    env['_ai']['text'] = '{"verdict":"failed","reason":"x"}'
    env['_ai']['local'] = 'local_only'                          # fournisseur en ligne : aucune image n'est envoyée
    _run_ai(env, 1000.0, pr, 3)
    assert not env['_ai_calls'] and not env['_alerts']


def test_ai_low_progress_and_no_vision(env):
    pr = _printer(ai_watch=True)
    env['_ai']['text'] = '{"verdict":"failed","reason":"x"}'
    _run_ai(env, 1000.0, pr, 3, progress=1)                     # début d'impression (< 2 %) : pas d'analyse
    assert not env['_ai_calls']
    env['_V104_SESS'].clear()
    env['_ai']['source'] = 'ollama_no_vision'
    _run_ai(env, 5000.0, pr, 1, progress=30)
    assert len(env['_alerts']) == 1 and env['_alerts'][0][1] == 'info' and not env['_db']().execute("SELECT * FROM print_photos").fetchall()


def test_ai_interval_setting(env):
    env['_settings']['ai_watch_interval_min'] = 1
    assert env['_v104_ai_interval_s']() == 120                  # minimum 2 min
    env['_settings']['ai_watch_interval_min'] = 'abc'
    assert env['_v104_ai_interval_s']() == 300
    env['_settings']['ai_watch_interval_min'] = 999
    assert env['_v104_ai_interval_s']() == 1800


def test_stem_matching(env):
    s = env['_v104_stem']
    assert s('C:\\x\\Benchy.gcode.3mf') == 'benchy' and s('/a/b/Piece.BGCODE') == 'piece' and s('') == ''


# ── Branchement module ↔ main.py ────────────────────────────────────────────────────────────
def test_init_registers_routes_and_requires_services():
    flask = pytest.importorskip('flask')
    mod = _load_module()
    with pytest.raises(RuntimeError):
        mod.init({}, routes=False)
    app = flask.Flask('t')
    ns = {n: (lambda *a, **k: None) for n in mod._REQUIRED}
    ns.update(app=app, login_required=lambda f: f)
    mod.init(ns)
    rules = {r.rule for r in app.url_map.iter_rules()}
    assert {'/api/printers/<int:pid>/meter/test', '/api/printers/meters/live', '/api/energy/summary',
            '/api/energy/sessions/<int:sid>'} <= rules


def test_main_provides_every_service_before_init(main_src):
    """main.py doit définir (ou importer) chaque service avant l'appel print_session.init(globals())."""
    import ast
    tree = ast.parse(main_src)
    call = next(n.lineno for n in tree.body if isinstance(n, ast.Expr) and 'print_session.init' in ast.get_source_segment(main_src, n))
    defined = set()
    for n in tree.body:
        if n.lineno >= call:
            continue
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            defined.add(n.name)
        elif isinstance(n, ast.Assign):
            defined |= {t.id for t in n.targets if isinstance(t, ast.Name)}
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            defined |= {(a.asname or a.name).split('.')[0] for a in n.names}
    assert not [x for x in _load_module()._REQUIRED if x not in defined]
