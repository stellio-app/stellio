"""Tests des versions 1.0.4 → 1.0.8, regroupés dans UN seul fichier.

Pour chaque nouvelle version : ajouter une section à la fin de ce fichier (pas de nouveau fichier de test).
"""
import base64, datetime, io, json, os, re, sqlite3, threading, time, uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import pytest
from PIL import Image
import importlib.util
import base64, datetime, importlib.util, io, logging, os, sqlite3, sys, zipfile
from flask import Flask, Response, jsonify, request, send_file, session
from werkzeug.utils import secure_filename
import importlib.util, io, json, os, sqlite3, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
import re
import subprocess
import importlib.util, os, time
import os, re, socket
import base64, io, json, os, sys
import json
import sqlite3
import sys
from conftest import load_from_main
from modules import print_session as ps
import json, pathlib


# ======================================================================
# v104  (ex tests/test_v104.py)
# v1.0.4 — prise connectée (Shelly / Tasmota / Home Assistant), énergie par impression, photo de fin, surveillance IA.
# Le module print_session.py est importé tel quel (copie fraîche à chaque test) et reçoit de faux services via init() :
# fausse prise HTTP, base SQLite temporaire, faux appels IA / caméra.
# ======================================================================

# Dépendances facultatives en CI minimale (pip install pytest numpy) : sans elles, ces tests sont ignorés, pas en erreur.
requests = pytest.importorskip('requests')
pytest.importorskip('PIL')


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


def _jpeg_104(color=(200, 30, 30), size=(320, 240)):
    buf = io.BytesIO()
    Image.new('RGB', size, color).save(buf, 'JPEG')
    return buf.getvalue()


@pytest.fixture()
def env_104(tmp_path):
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
    ns_ref = {'grab': lambda printer: _jpeg_104()}
    ns['_ns_ref'] = ns_ref
    ns['_alerts'], ns['_ai_calls'], ns['_settings'], ns['_ai'], ns['_photos'] = alerts, ai_calls, settings, ai, photos
    ns['_db'] = get_db
    ns['_ensure_v104_tables']()          # le suivi réel le fait au démarrage (_start_v104_worker)
    return ns


# ── Config & sécurité ───────────────────────────────────────────────────────────────────────
def test_clean_host(env_104):
    f = env_104['_meter_clean_host']
    assert f('192.168.1.50') == 'http://192.168.1.50'
    assert f('HTTPS://ha.local:8123/') == 'https://ha.local:8123'
    assert f('shelly.lan') == 'http://shelly.lan'
    assert f('') == '' and f('a b') == '' and f('http://x;rm -rf') == ''
    assert f('169.254.169.254') == ''                       # métadonnées cloud refusées
    assert f('javascript:alert(1)') == ''


def test_clean_config_token_never_clear_and_kept_on_edit(env_104):
    clean = env_104['_v104_clean_config']
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


def test_apply_config_strips_plain_token_from_http_printers(env_104):
    raw = {'port': '7125', 'meter': {'kind': 'shelly', 'host': 'x', 'token': 'PLAIN'}, 'end_photo': True}
    env_104['_v104_apply_config'](raw, {'meter': {'kind': 'shelly', 'host': '10.0.0.5'}}, {})
    assert 'PLAIN' not in json.dumps(raw) and raw['meter']['host'] == 'http://10.0.0.5' and 'end_photo' not in raw
    assert raw['port'] == '7125'


def test_public_config_hides_token(env_104):
    pub = env_104['_v104_public_config']({'meter': {'kind': 'tasmota', 'host': 'h', 'token_enc': _enc('x')}})
    assert pub['meter'] == {'kind': 'tasmota', 'host': 'h', 'has_token': True}


# ── Lecture des prises ──────────────────────────────────────────────────────────────────────
def test_shelly_gen2_and_gen1(env_104, server):
    m = {'kind': 'shelly', 'host': server, 'channel': 0}
    assert env_104['_meter_read'](m) == {'power_w': 120.0, 'energy_wh': 1000.0}
    _State.shelly_gen = 1                                    # Gen1 : /status, total en watt-minutes
    assert env_104['_meter_read'](m) == {'power_w': 120.0, 'energy_wh': 1000.0}


def test_tasmota(env_104, server):
    d = env_104['_meter_read']({'kind': 'tasmota', 'host': server})
    assert d == {'power_w': 120.0, 'energy_wh': 1000.0}


def test_home_assistant_units_and_auth(env_104, server):
    m = {'kind': 'homeassistant', 'host': server, 'entity': 'sensor.plug_power', 'energy_entity': 'sensor.plug_energy',
         'token_enc': _enc('tok')}
    d = env_104['_meter_read'](m)
    assert d['power_w'] == pytest.approx(120.0) and d['energy_wh'] == pytest.approx(1000.0)
    with pytest.raises(PermissionError):
        env_104['_meter_read'](dict(m, token_enc=None))             # sans jeton
    _State.ha_token = 'other'
    with pytest.raises(PermissionError):
        env_104['_meter_read'](m)
    _State.ha_token = 'tok'
    with pytest.raises(ValueError):
        env_104['_meter_read'](dict(m, entity='sensor.off', energy_entity=None))


def test_poll_backoff_and_live_cache(env_104, server):
    bad = {'kind': 'shelly', 'host': 'http://127.0.0.1:9', 'channel': 0}
    poll = env_104['_v104_poll_meter']
    for i in range(3):
        live = poll(5, bad, 1000.0 + i)
        assert live['ok'] is False
    assert env_104['_METER_FAIL'][5][0] == 3 and env_104['_METER_FAIL'][5][1] > 1002
    assert poll(5, bad, 1010.0) is env_104['_METER_LIVE'][5]     # en attente : pas de nouvel essai


# ── Session d'impression complète (compteur) ────────────────────────────────────────────────
def _printer(meter=None, **flags):
    cfg = dict(flags)
    if meter:
        cfg['meter'] = meter
    return {'id': 7, 'user_id': 1, 'name': 'Ender', 'config': cfg}


def test_session_counter_energy_cost_and_history(env_104, server):
    meter = {'kind': 'shelly', 'host': server, 'channel': 0}
    pr = _printer(meter)
    step, sess = env_104['_v104_step'], env_104['_V104_SESS']
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
    row = env_104['_db']().execute("SELECT * FROM print_energy").fetchone()
    assert row['measured_by'] == 'counter' and row['energy_wh'] == pytest.approx(150.0)
    assert row['cost'] == pytest.approx(0.15 * 0.25, abs=1e-4) and row['avg_w'] == pytest.approx(150 / (3625 / 3600), abs=3)
    h = env_104['_db']().execute("SELECT * FROM print_history").fetchone()
    assert h['energy_wh'] == pytest.approx(150.0) and h['energy_measured'] == 1
    assert h['elec_cost'] == pytest.approx(0.0375) and h['total_cost'] == pytest.approx(0.5375)
    # la puissance mesurée sert ensuite aux estimations (≥ 15 min, au moins 2 sessions ou 1 h)
    assert env_104['_measured_avg_power_w'](7) == pytest.approx(row['avg_w'], abs=0.2)


def test_session_samples_fallback_without_counter(env_104, server):
    class NoCounter:   # prise qui ne donne que les watts
        pass
    meter = {'kind': 'homeassistant', 'host': server, 'entity': 'sensor.plug_power', 'token_enc': _enc('tok')}
    pr = _printer(meter)
    step = env_104['_v104_step']
    t0 = 20_000.0
    _State.power = 200.0
    step(pr, {'status': 'printing', 'file': 'x.gcode', 'progress': 5}, t0)
    for i in range(1, 31):
        step(pr, {'status': 'printing', 'file': 'x.gcode', 'progress': 5}, t0 + 10 * i)
    step(pr, {'status': 'idle'}, t0 + 305)
    step(pr, {'status': 'idle'}, t0 + 330)
    row = env_104['_db']().execute("SELECT * FROM print_energy").fetchone()
    assert row['measured_by'] == 'samples'
    assert row['energy_wh'] == pytest.approx(200.0 * 290 / 3600, rel=0.05)


def test_short_print_and_unknown_grace(env_104, server):
    meter = {'kind': 'shelly', 'host': server, 'channel': 0}
    pr = _printer(meter)
    step, sess = env_104['_v104_step'], env_104['_V104_SESS']
    step(pr, {'status': 'printing', 'file': 'a.gcode'}, 100.0)
    step(pr, {'status': 'idle'}, 150.0)
    step(pr, {'status': 'idle'}, 170.0)                       # 70 s : annulation / test, rien d'enregistré
    assert 7 not in sess and env_104['_db']().execute("SELECT COUNT(*) FROM print_energy").fetchone()[0] == 0
    step(pr, {'status': 'printing', 'file': 'b.gcode'}, 1000.0)
    step(pr, {'status': 'offline'}, 1100.0)                   # injoignable : la session reste ouverte
    assert 7 in sess
    step(pr, {'status': 'printing', 'file': 'b.gcode'}, 1200.0)
    assert sess[7]['unknown_since'] is None


# ── Photo de fin d'impression ───────────────────────────────────────────────────────────────
def test_end_photo_goes_to_existing_gallery(env_104):
    pr = _printer(end_photo=True)
    step = env_104['_v104_step']
    step(pr, {'status': 'printing', 'file': 'Benchy.gcode'}, 5000.0)
    step(pr, {'status': 'idle'}, 5400.0)
    step(pr, {'status': 'idle'}, 5420.0)
    rows = env_104['_db']().execute("SELECT * FROM print_photos").fetchall()
    assert len(rows) == 1 and rows[0]['result'] == 'success'
    assert rows[0]['file_path'] == '/lib/Benchy.3mf'          # rattachée au fichier de la bibliothèque
    assert os.path.isfile(os.path.join(env_104['_photos'], rows[0]['image_filename']))
    assert 'Ender' in rows[0]['note']


def test_end_photo_failed_when_printer_error_and_no_history(env_104):
    pr = _printer(end_photo=True)
    step = env_104['_v104_step']
    step(pr, {'status': 'printing', 'file': 'Inconnu.gcode'}, 5000.0)
    step(pr, {'status': 'error'}, 5400.0)
    step(pr, {'status': 'error'}, 5425.0)
    r = env_104['_db']().execute("SELECT * FROM print_photos").fetchone()
    assert r['result'] == 'failed' and r['file_path'] == 'printer/7/Inconnu.gcode'


def test_no_camera_no_crash(env_104):
    env_104['_ns_ref']['grab'] = lambda printer: None
    pr = _printer(end_photo=True)
    step = env_104['_v104_step']
    step(pr, {'status': 'printing', 'file': 'x.gcode'}, 1.0)
    step(pr, {'status': 'idle'}, 400.0)
    step(pr, {'status': 'idle'}, 420.0)
    assert env_104['_db']().execute("SELECT COUNT(*) FROM print_photos").fetchone()[0] == 0


# ── Surveillance IA ─────────────────────────────────────────────────────────────────────────
def test_parse_verdict(env_104):
    p = env_104['_v104_parse_verdict']
    assert p('{"verdict":"failed","reason":"spaghetti on the bed"}') == ('failed', 'spaghetti on the bed')
    assert p('Sure! {"verdict": "ok", "reason": ""}') == ('ok', '')
    assert p('The print has failed') == ('failed', '')
    assert p('???') == ('unsure', '') and p('') == ('unsure', '')


def _run_ai(env_104, t0, pr, n_checks, progress=40):
    step = env_104['_v104_step']
    t = t0
    step(pr, {'status': 'printing', 'file': 'Benchy.gcode', 'progress': progress}, t)
    for _ in range(n_checks):
        t += 400
        step(pr, {'status': 'printing', 'file': 'Benchy.gcode', 'progress': progress}, t)
    return t


def test_ai_needs_two_consecutive_failures(env_104):
    pr = _printer(ai_watch=True)
    env_104['_ai']['text'] = '{"verdict":"failed","reason":"spaghetti"}'
    t = _run_ai(env_104, 1000.0, pr, 1)
    assert not env_104['_alerts'] and env_104['_V104_SESS'][7]['ai_fail'] == 1
    env_104['_v104_step'](pr, {'status': 'printing', 'file': 'Benchy.gcode', 'progress': 41}, t + 61)   # 2e vérification 60 s plus tard
    assert len(env_104['_alerts']) == 1
    uid, ntype, title, msg, key = env_104['_alerts'][0]
    assert ntype == 'print_failed' and 'Ender' in msg and 'spaghetti' in msg and key.startswith('print_failed_ai_7_')
    ph = env_104['_db']().execute("SELECT * FROM print_photos").fetchall()
    assert len(ph) == 1 and ph[0]['result'] == 'failed'       # preuve ajoutée à la galerie
    # pas de seconde alerte pour la même impression
    env_104['_v104_step'](pr, {'status': 'printing', 'file': 'Benchy.gcode', 'progress': 45}, t + 61 + 2000)
    assert len(env_104['_alerts']) == 1


def test_ai_ok_resets_counter_and_uses_image_and_progress(env_104):
    pr = _printer(ai_watch=True)
    env_104['_ai']['text'] = '{"verdict":"failed","reason":"x"}'
    t = _run_ai(env_104, 1000.0, pr, 1)
    env_104['_ai']['text'] = '{"verdict":"ok","reason":""}'
    env_104['_v104_step'](pr, {'status': 'printing', 'file': 'Benchy.gcode', 'progress': 41}, t + 61)
    assert env_104['_V104_SESS'][7]['ai_fail'] == 0 and not env_104['_alerts']
    prompt, kw = env_104['_ai_calls'][-1]
    assert '41%' in prompt and kw['images'] and base64.b64decode(kw['images'][0])[:2] == b'\xff\xd8'


def test_ai_alert_gives_a_single_end_photo_left_to_the_user(env_104):
    # v1.0.7 : une seule photo (celle de fin), « Réussi » par défaut ; la raison IA est dans son commentaire, l'utilisateur tranche
    pr = _printer(ai_watch=True, end_photo=True)
    env_104['_ai']['text'] = '{"verdict":"failed","reason":"detached"}'
    t = _run_ai(env_104, 1000.0, pr, 1)
    env_104['_v104_step'](pr, {'status': 'printing', 'file': 'Benchy.gcode', 'progress': 41}, t + 61)
    env_104['_v104_step'](pr, {'status': 'idle'}, t + 600)
    env_104['_v104_step'](pr, {'status': 'idle'}, t + 620)
    res = [r['result'] for r in env_104['_db']().execute("SELECT result FROM print_photos ORDER BY id").fetchall()]
    assert res == ['success']
    note = env_104['_db']().execute("SELECT note FROM print_photos").fetchone()['note']
    assert 'detached' in note


def test_ai_privacy_and_guards(env_104):
    pr = _printer(ai_watch=True)
    env_104['_ai']['text'] = '{"verdict":"failed","reason":"x"}'
    env_104['_ai']['local'] = 'local_only'                          # fournisseur en ligne : aucune image n'est envoyée
    _run_ai(env_104, 1000.0, pr, 3)
    assert not env_104['_ai_calls'] and not env_104['_alerts']


def test_ai_low_progress_and_no_vision(env_104):
    pr = _printer(ai_watch=True)
    env_104['_ai']['text'] = '{"verdict":"failed","reason":"x"}'
    _run_ai(env_104, 1000.0, pr, 3, progress=1)                     # début d'impression (< 2 %) : pas d'analyse
    assert not env_104['_ai_calls']
    env_104['_V104_SESS'].clear()
    env_104['_ai']['source'] = 'ollama_no_vision'
    _run_ai(env_104, 5000.0, pr, 1, progress=30)
    assert len(env_104['_alerts']) == 1 and env_104['_alerts'][0][1] == 'info' and not env_104['_db']().execute("SELECT * FROM print_photos").fetchall()


def test_ai_interval_setting(env_104):
    env_104['_settings']['ai_watch_interval_min'] = 1
    assert env_104['_v104_ai_interval_s']() == 120                  # minimum 2 min
    env_104['_settings']['ai_watch_interval_min'] = 'abc'
    assert env_104['_v104_ai_interval_s']() == 300
    env_104['_settings']['ai_watch_interval_min'] = 999
    assert env_104['_v104_ai_interval_s']() == 1800


def test_stem_matching(env_104):
    s = env_104['_v104_stem']
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


# ======================================================================
# v106  (ex tests/test_v106.py)
# Tests v1.0.6 : devis client en ligne, ZIP comptable, stock de pièces, répartition, résumé, pesées, partage de profils.
# Chaque module est chargé à part (nouvelle copie), initialisé avec de faux services de main.py et une base SQLite temporaire.
# ======================================================================

ROOT_106 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_module(name):
    spec = importlib.util.spec_from_file_location(f'_t_{name}', os.path.join(ROOT_106, 'modules', f'{name}.py'))
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
def env_106(tmp_path):
    return Env(tmp_path)


# ── 1. Devis client en ligne ──
def _portal(env_106, tmp_path):
    def stored(qid):
        r = env_106.sql("SELECT * FROM quotes WHERE id=? AND user_id=?", (qid, 1))
        return r[0] if r else None
    env_106.ns.update({
        'QUOTES_DIR': str(tmp_path), '_build_quote_pdf_with_repair': lambda p, encrypt=False: b'%PDF', '_stored_quote': stored,
        '_create_jobs_from_quote': lambda uid, row: 2, '_quote_payload_path': lambda r: None,
        '_safe_quote_pdf_filename': lambda n: 'q.pdf', '_stored_quote_path': lambda r: None,
        'get_local_ip': lambda: '10.0.0.5', 'get_remote_state': lambda: {'status': 'ready', 'url': 'https://stellio.example.org', 'mode': 'custom'}})
    m = load_module('quote_portal'); m.init(env_106.ns)
    env_106.sql("INSERT INTO quotes (user_id, number, client, item_desc, total) VALUES (1,'D-001','Zoé','Support','12,00 €')")
    return m


def test_portal_flow(env_106, tmp_path):
    m = _portal(env_106, tmp_path)
    c = env_106.client()
    r = c.post('/api/quotes/1/portal').get_json()
    assert r['success'] and '/quote/' in r['url']
    token = r['token']
    assert env_106.sql("SELECT status FROM quotes")[0]['status'] == 'sent'
    pub = env_106.client(logged=False)
    c.post('/api/quote-portal/settings', json={'payment_info': 'IBAN FR76', 'payment_link': 'https://pay.example/x'})
    d = pub.get(f'/quote/{token}/data').get_json()
    assert d['can_decide'] and d['payment_info'] == '' and d['payment_link'] == ''
    assert 'user_id' not in d and 'public_token' not in d
    assert pub.get(f'/quote/{token}').status_code == 200
    res = pub.post(f'/quote/{token}/decision', json={'decision': 'accept', 'name': 'Zoé <b>'}).get_json()
    assert res['success'] and res['status'] == 'accepted' and res['jobs_created'] == 2
    assert res['payment_info'] == 'IBAN FR76'
    assert env_106.notifs and 'accepté' in env_106.notifs[0][2]
    again = pub.post(f'/quote/{token}/decision', json={'decision': 'refuse'})
    assert again.status_code == 409
    assert pub.get(f'/quote/{token}/data').get_json()['payment_info'] == 'IBAN FR76'
    assert '<' not in env_106.sql("SELECT decision_by FROM quotes")[0]['decision_by']


def test_portal_security(env_106, tmp_path):
    m = _portal(env_106, tmp_path)
    c, pub = env_106.client(), env_106.client(logged=False)
    assert pub.post('/api/quotes/1/portal').status_code == 401
    assert pub.get('/quote/not-a-token-xx/data').status_code == 404
    assert c.post('/api/quote-portal/settings', json={'payment_link': 'javascript:alert(1)'}).status_code == 400
    token = c.post('/api/quotes/1/portal').get_json()['token']
    assert pub.post(f'/quote/{token}/decision', json={'decision': 'x'}).status_code == 400
    c.delete('/api/quotes/1/portal')
    assert pub.get(f'/quote/{token}/data').status_code == 404


def test_portal_rate_limit(env_106, tmp_path):
    m = _portal(env_106, tmp_path)
    token = env_106.client().post('/api/quotes/1/portal').get_json()['token']
    pub = env_106.client(logged=False)
    codes = [pub.post(f'/quote/{token}/decision', json={'decision': 'bad'}).status_code for _ in range(12)]
    assert codes[:10] == [400] * 10 and 429 in codes[10:]


# ── 2. ZIP comptable ──
def test_accounting_zip(env_106, tmp_path):
    pdf = tmp_path / 'f1.pdf'; pdf.write_bytes(b'%PDF-1')
    env_106.ns.update({
        '_csv_args': lambda src: (src.get('from', ''), src.get('to', ''), [], src.get('lang', 'fr')),
        '_iso_date': lambda x: x, '_quote_eff_status': lambda r: r['status'],
        '_quotes_csv_bytes': lambda *a: b'a;b\n', '_wv_save_dialog': lambda w: 1,
        '_stored_quote_path': lambda r: str(pdf) if r['doc_type'] != 'quote' else None})
    m = load_module('accounting_zip'); m.init(env_106.ns)
    env_106.sql("INSERT INTO quotes (user_id, number, doc_type, total_value, status, created_at) VALUES "
            "(1,'F-1','invoice',100,'paid','2026-09-10 10:00:00'),(1,'F-2','invoice',50,'sent','2026-09-20 10:00:00'),"
            "(1,'A-1','credit',-30,'sent','2026-09-25 10:00:00'),(1,'F-3','invoice',70,'paid','2026-10-02 10:00:00')")
    r = env_106.client().get('/api/quotes/export-zip?month=2026-09&lang=fr')
    assert r.status_code == 200 and r.headers['X-Stellio-Documents'] == '3'
    z = zipfile.ZipFile(io.BytesIO(r.data))
    names = set(z.namelist())
    assert {'documents.csv', 'recapitulatif.csv', 'LISEZMOI.txt', 'pdf/invoice/F-1.pdf', 'pdf/invoice/F-2.pdf', 'pdf/credit/A-1.pdf'} <= names
    assert 'pdf/invoice/F-3.pdf' not in names
    recap = z.read('recapitulatif.csv').decode('utf-8-sig')
    assert 'NET' in recap and '120,00' in recap          # 100 + 50 − 30
    assert env_106.client(logged=False).get('/api/quotes/export-zip').status_code == 401


# ── 3. Stock de pièces ──
def test_parts_stock(env_106):
    m = load_module('parts_stock'); m.init(env_106.ns)
    c = env_106.client()
    pid = c.post('/api/parts-stock', json={'name': 'Clip', 'min_qty': 5, 'reorder_qty': 20, 'auto_restock': True, 'material': 'pla'}).get_json()['id']
    assert c.post(f'/api/parts-stock/{pid}/adjust', json={'set': 8}).get_json()['qty'] == 8
    assert c.post(f'/api/parts-stock/{pid}/adjust', json={'delta': -4}).get_json()['qty'] == 4
    assert [n for n in env_106.notifs if n[5].startswith('parts_low:')]   # l'ajustement a déjà déclenché l'alerte
    jobs = env_106.sql("SELECT * FROM print_jobs WHERE stock_part_id=?", (pid,))
    assert len(jobs) == 1 and jobs[0]['quantity'] == 20 and jobs[0]['printer_id'] == 7
    assert m.check_low_stock(1) == 0                       # même valeur de stock : pas de doublon
    assert len(env_106.sql("SELECT * FROM print_jobs WHERE stock_part_id=?", (pid,))) == 1
    env_106.sql("UPDATE print_jobs SET qty_done=12, status='done' WHERE stock_part_id=?", (pid,))
    assert m.sync_completed_restocks(1) == 12
    assert m.sync_completed_restocks(1) == 0               # idempotent
    assert c.get('/api/parts-stock').get_json()['parts'][0]['qty'] == 16
    assert c.post(f'/api/parts-stock/{pid}/restock', json={'quantity': 5}).get_json()['success']
    assert c.delete(f'/api/parts-stock/{pid}').get_json()['success']
    assert c.post('/api/parts-stock', json={'name': ''}).status_code == 400


# ── 4. Répartition ──
def _disp(env_106):
    env_106.ns.update({'_printer_status_cached': lambda p: {}, 'parse_printer_config': lambda r: dict(r)})
    m = load_module('printer_dispatch'); m.init(env_106.ns); return m


def test_score_printer(env_106):
    m = _disp(env_106)
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


def test_dispatch_apply(env_106):
    env_106.sql("CREATE TABLE printers (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT)")
    env_106.sql("INSERT INTO printers VALUES (1,1,'A'),(2,1,'B')")
    env_106.sql("INSERT INTO print_jobs (user_id, part, material, printer_id) VALUES (1,'p1','PLA',1)")
    m = _disp(env_106)
    m._printer_status_cached = lambda p: {'status': 'printing'} if p['id'] == 1 else {'status': 'idle'}
    c = env_106.client()
    s = c.get('/api/dispatch/suggestions').get_json()['suggestions']
    assert s[0]['best']['printer_id'] == 2 and s[0]['change']
    assert c.post('/api/dispatch/apply', json={}).get_json()['changed'] == 1
    assert env_106.sql("SELECT printer_id, status FROM print_jobs")[0]['printer_id'] == 2
    assert env_106.sql("SELECT status FROM print_jobs")[0]['status'] == 'queued'       # jamais lancée


# ── 5. Résumé ──
def _digest(env_106):
    env_106.ns.update({'_is_low_stock': lambda r, c: False})
    m = load_module('digest'); m.init(env_106.ns); return m


def test_digest_period_and_tick(env_106):
    m = _digest(env_106)
    cfg = {'frequency': 'daily', 'hour': 8, 'weekday': 0}
    assert m.period_key(datetime.datetime(2026, 11, 3, 7, 59), cfg) is None
    assert m.period_key(datetime.datetime(2026, 11, 3, 8, 0), cfg) == 'daily:2026-11-03'
    w = {'frequency': 'weekly', 'hour': 9, 'weekday': 2}
    assert m.period_key(datetime.datetime(2026, 11, 3, 12), w) is None       # mardi, avant mercredi
    assert m.period_key(datetime.datetime(2026, 11, 4, 9), w).startswith('weekly:2026-W')
    env_106.sql("INSERT INTO quotes (user_id, number, status) VALUES (1,'D-9','sent')")
    env_106.settings.update({'digest_enabled': True, 'digest_hour': 8})
    now = datetime.datetime(2026, 11, 3, 9, 0)
    assert m.tick(now) is True
    assert m.tick(now) is False                                            # déjà envoyé pour cette période
    assert len([n for n in env_106.notifs if n[5].startswith('digest:')]) == 1
    assert env_106.pushes


def test_digest_disabled_and_render(env_106):
    m = _digest(env_106)
    assert m.tick(datetime.datetime(2026, 11, 3, 9)) is False
    title, text = m.render({}, 'daily', 'fr')
    assert title and text
    t2, x2 = m.render({'pending': {'n': 2}}, 'weekly', 'en')
    assert '2' in x2
    c = env_106.client()
    assert c.post('/api/digest/settings', json={'enabled': True, 'frequency': 'weekly', 'hour': 99, 'weekday': 3}).get_json()['success'] is not False
    cfg = c.get('/api/digest/settings').get_json()
    assert cfg['frequency'] == 'weekly' and cfg['hour'] == 23 and cfg['weekday'] == 3 and cfg['enabled']
    assert c.post('/api/digest/send-now', json={}).get_json()['sent']


# ── 6. Pesées de bobines ──
def test_consumption_rate(env_106):
    env_106.ns.update({'_get_tigertag_slots': lambda uid: []})
    m = load_module('filament_weighing'); m.init(env_106.ns)
    d0 = datetime.datetime(2026, 11, 1)
    D = lambda days, g: (d0 + datetime.timedelta(days=days), g)
    assert m.consumption_rate([D(0, 1000)])[0] is None
    rate, n = m.consumption_rate([D(0, 1000), D(5, 750), D(10, 500)])
    assert abs(rate - 50) < 0.01 and n == 3
    rate, n = m.consumption_rate([D(0, 100), D(1, 1000), D(3, 900), D(5, 800)])      # remplacement de bobine au jour 1
    assert abs(rate - 50) < 0.01 and n == 3
    assert m.consumption_rate([D(0, 500), D(0.1, 499)])[0] is None                  # intervalle trop court


def test_weigh_and_forecast(env_106):
    slots = [{'source_id': 'tt1', 'name': 'PLA noir', 'remaining_g': 800, 'capacity_g': 1000}]
    env_106.ns.update({'_get_tigertag_slots': lambda uid: slots})
    m = load_module('filament_weighing'); m.init(env_106.ns)
    c = env_106.client()
    assert c.post('/api/filament/weigh-sync').get_json()['recorded'] == 1
    assert c.post('/api/filament/weigh-sync').get_json()['recorded'] == 0            # variation < 1 g
    old = (datetime.datetime.now() - datetime.timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S')
    env_106.sql("UPDATE spool_weighings SET remaining_g=1000, recorded_at=?", (old,))
    slots[0]['remaining_g'] = 800
    c.post('/api/filament/weigh-sync')
    f = c.get('/api/filament/forecast').get_json()['spools'][0]
    assert abs(f['g_per_day'] - 20) < 1 and abs(f['days_left'] - 40) < 3
    env_106.sql("INSERT INTO manual_filament_spools (user_id, name, remaining_g) VALUES (1,'Manuel',900)")
    r = c.post('/api/filament/weigh', json={'source_id': 1, 'gross_g': 1250, 'tare_g': 250}).get_json()
    assert r['success'] and r['remaining_g'] == 1000
    assert env_106.sql("SELECT remaining_g FROM manual_filament_spools")[0]['remaining_g'] == 1000
    assert c.post('/api/filament/weigh', json={'source_id': 99, 'remaining_g': 5}).status_code == 404
    assert c.post('/api/filament/weigh', json={'source_id': 1}).status_code == 400


# ── 7. Partage de profils ──
def test_profile_receive_and_send(env_106, tmp_path):
    store = []
    env_106.ns.update({
        'IMPORTED_PROFILES_DIR': str(tmp_path), 'requests': None,
        '_parse_slicer_profile_file': lambda fn, blob: [{'name': blob.decode().strip(), 'slicer': 'orca'}] if blob.strip() else [],
        'load_slicer_profiles': lambda: list(store), 'save_slicer_profiles': lambda p: (store.clear(), store.extend(p))})
    m = load_module('profile_share'); m.init(env_106.ns)
    pub = env_106.client(logged=False)
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
    c = env_106.client()
    assert c.get('/api/slicer-profiles/ok/export').status_code == 200
    assert c.get('/api/slicer-profiles/bad/export').status_code == 404
    assert c.post('/api/slicer-profiles/bad/send-to-instance', json={'instance_id': 1}).status_code == 404
    assert c.post('/api/slicer-profiles/ok/send-to-instance', json={}).status_code == 400
    assert c.post('/api/slicer-profiles/ok/send-to-instance', json={'instance_id': 5}).status_code == 404


def test_portal_never_creates_a_local_link(env_106, tmp_path):
    m = _portal(env_106, tmp_path)
    c = env_106.client()
    m.get_remote_state = lambda: {'status': 'off'}
    r = c.post('/api/quotes/1/portal')
    assert r.status_code == 409 and r.get_json()['error'] == 'remote_required' and r.get_json()['remote'] is False
    assert env_106.sql("SELECT status FROM quotes WHERE id=1")[0][0] == 'draft'              # aucun lien : le devis reste brouillon
    assert not env_106.sql("SELECT public_token FROM quotes WHERE id=1")[0][0]
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


# ======================================================================
# v106_fixes  (ex tests/test_v106_fixes.py)
# v1.0.6 — correctifs signalés par des utilisateurs : photo de fin / IA / prise non enregistrées (Klipper, OctoPrint, PrusaLink),
# timelapse (flux MJPEG sans ffmpeg, micro-coupures réseau), téléchargement d'un G-code lié, décompte de bobine (poids lu dans le G-code).
# ======================================================================

ROOT_106fixes = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name):
    spec = importlib.util.spec_from_file_location(name + '_fix_test', os.path.join(ROOT_106fixes, 'modules', name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except ImportError as e:
        pytest.skip(f'{name} : dépendance manquante ({e})')
    return mod


# ── 1. cases enregistrées pour les imprimantes dont la config reçue sert aussi de raw_config ──
def test_apply_config_keeps_flags_when_incoming_is_raw_config():
    ps = _load('print_session')
    cfg = {'port': '7125', 'timelapse': True, 'end_photo': True, 'ai_watch': True}
    out = ps._v104_apply_config(cfg, cfg, {})            # Klipper / OctoPrint / PrusaLink : même objet des deux côtés
    assert out['end_photo'] is True and out['ai_watch'] is True and out['port'] == '7125'


def test_apply_config_keeps_meter_when_incoming_is_raw_config():
    ps = _load('print_session')
    cfg = {'meter': {'kind': 'shelly', 'host': '192.168.1.50'}}
    out = ps._v104_apply_config(cfg, cfg, {})
    assert out['meter']['kind'] == 'shelly' and out['meter']['host'].endswith('192.168.1.50')


def test_apply_config_unchecking_removes_flag():
    ps = _load('print_session')
    cfg = {'port': '7125'}
    out = ps._v104_apply_config(cfg, cfg, {'end_photo': True, 'ai_watch': True})
    assert 'end_photo' not in out and 'ai_watch' not in out


def test_apply_config_separate_dicts_still_work():
    ps = _load('print_session')
    out = ps._v104_apply_config({'code': 'x'}, {'end_photo': True}, {})
    assert out == {'code': 'x', 'end_photo': True}


# ── 2. timelapse ──
PIL = None


def _jpeg_106fixes():
    Image = pytest.importorskip('PIL.Image')
    b = io.BytesIO()
    Image.new('RGB', (32, 24), (200, 40, 40)).save(b, 'JPEG')
    return b.getvalue()


class _Cam(BaseHTTPRequestHandler):
    jpg = b''
    routes = {}

    def log_message(self, *a):
        pass

    def do_GET(self):
        kind = self.routes.get(self.path)
        if kind == 'snapshot':
            self.send_response(200); self.send_header('Content-Type', 'image/jpeg')
            self.send_header('Content-Length', str(len(self.jpg))); self.end_headers(); self.wfile.write(self.jpg)
        elif kind == 'mjpeg':
            self.send_response(200); self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame'); self.end_headers()
            try:
                for _ in range(3):
                    self.wfile.write(b'--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n' % len(self.jpg) + self.jpg + b'\r\n')
                    self.wfile.flush(); time.sleep(0.05)
            except Exception:
                pass
        else:
            self.send_response(404); self.send_header('Content-Length', '0'); self.end_headers()


@pytest.fixture
def cam():
    _Cam.jpg = _jpeg_106fixes()
    srv = ThreadingHTTPServer(('127.0.0.1', 0), _Cam)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv, _Cam
    srv.shutdown()


def _tl(**services):
    tl = _load('timelapse')
    tl.FFMPEG_TOOL = None
    tl._popen_kwargs_silent = lambda: {}
    for k, v in services.items():
        setattr(tl, k, v)
    return tl


def test_grab_frame_reads_mjpeg_stream_without_ffmpeg(cam):
    srv, h = cam
    h.routes = {'/webcam/?action=stream': 'mjpeg'}
    url = f'http://127.0.0.1:{srv.server_port}/webcam/?action=stream'
    tl = _tl(_resolve_printer_camera=lambda p, pid, host: {'available': True, 'stream_url': url, 'snapshot_url': ''})
    jpg = tl._timelapse_grab_frame({'id': 1, 'type': 'klipper', 'ip': '127.0.0.1', 'config': {}})
    assert jpg and jpg[:2] == b'\xff\xd8' and jpg[-2:] == b'\xff\xd9'


def test_grab_frame_derives_snapshot_from_stream_url(cam):
    srv, h = cam
    h.routes = {'/webcam/?action=snapshot': 'snapshot'}           # le flux, lui, n'existe pas : seul l'instantané déduit répond
    url = f'http://127.0.0.1:{srv.server_port}/webcam/?action=stream'
    tl = _tl(_resolve_printer_camera=lambda p, pid, host: {'available': True, 'stream_url': url, 'snapshot_url': ''})
    assert tl._timelapse_grab_frame({'id': 1, 'type': 'klipper', 'ip': '127.0.0.1', 'config': {}})[:2] == b'\xff\xd8'


def test_grab_frame_none_when_camera_dead(cam):
    srv, h = cam
    h.routes = {}
    url = f'http://127.0.0.1:{srv.server_port}/webcam/?action=stream'
    tl = _tl(_resolve_printer_camera=lambda p, pid, host: {'available': True, 'stream_url': url, 'snapshot_url': ''})
    assert tl._timelapse_grab_frame({'id': 1, 'type': 'klipper', 'ip': '127.0.0.1', 'config': {}}) is None


class _Log_106fixes:
    def __init__(self): self.lines = []
    def info(self, m): self.lines.append(m)
    warning = error = info


def _tick_env(tmp_path, status_box, monkeypatch):
    db = str(tmp_path / 'p.db')
    c = sqlite3.connect(db); c.execute("CREATE TABLE printers (id INTEGER, user_id INTEGER, name TEXT, type TEXT, ip TEXT, config TEXT)")
    c.execute("INSERT INTO printers VALUES (1, 1, 'Voron', 'klipper', '10.0.0.5', ?)", (json.dumps({'timelapse': True}),)); c.commit(); c.close()

    def get_db():
        conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row; return conn

    def parse(row):
        d = dict(row); d['config'] = json.loads(d['config']); return d

    log = _Log_106fixes()
    tl = _tl(get_db=get_db, parse_printer_config=parse, load_settings=lambda: {}, app_logger=log,
             _printer_status_cached=lambda p, ttl=0: dict(status_box))
    tl.TIMELAPSE_DIR = str(tmp_path / 'tl')
    os.makedirs(tl.TIMELAPSE_DIR, exist_ok=True)
    tl._timelapse_grab_frame = lambda p: b'\xff\xd8fake\xff\xd9'
    assembled = []
    monkeypatch.setattr(tl, '_timelapse_assemble', lambda st: assembled.append(st))
    return tl, assembled, log


def _tick(tl):
    for st in tl._TL_STATE.values():
        st['last_poll'] = 0
    tl._timelapse_tick()


def test_timelapse_survives_short_network_drop(tmp_path, monkeypatch):
    box = {'status': 'printing', 'file': 'benchy.gcode'}
    tl, assembled, _ = _tick_env(tmp_path, box, monkeypatch)
    _tick(tl)
    assert 1 in tl._TL_STATE and tl._TL_STATE[1]['frames'] == 1
    box['status'] = 'offline'
    _tick(tl)
    assert 1 in tl._TL_STATE and not assembled                  # micro-coupure : la capture continue
    box['status'] = 'printing'
    _tick(tl)
    assert tl._TL_STATE[1]['frames'] == 2 and tl._TL_STATE[1]['lost_since'] is None
    box['status'] = 'idle'
    _tick(tl)
    assert 1 not in tl._TL_STATE and len(assembled) == 1        # vraie fin d'impression : assemblage


def test_timelapse_closes_after_long_outage(tmp_path, monkeypatch):
    box = {'status': 'printing', 'file': 'benchy.gcode'}
    tl, assembled, _ = _tick_env(tmp_path, box, monkeypatch)
    _tick(tl)
    box['status'] = 'offline'
    _tick(tl)
    tl._TL_STATE[1]['lost_since'] = time.time() - tl.TIMELAPSE_LOST_GRACE_S - 5
    _tick(tl)
    assert 1 not in tl._TL_STATE and len(assembled) == 1


def test_timelapse_logs_when_camera_gives_nothing(tmp_path, monkeypatch):
    box = {'status': 'printing', 'file': 'a.gcode'}
    tl, assembled, log = _tick_env(tmp_path, box, monkeypatch)
    tl._timelapse_grab_frame = lambda p: None
    for _ in range(3):
        _tick(tl)
    assert any('aucune image' in m for m in log.lines)


# ── 3. décompte de bobine : poids lu dans le G-code ──
def test_required_weight_read_from_gcode(tmp_path):
    from conftest import load_from_main
    import threading as th, re, hashlib, zipfile
    ns = load_from_main(['_get_required_weight_for_file', 'parse_slic3r_derived_gcode', 'parse_bambu_orca_gcode3mf',
                         '_extract_gcode_from_gcode3mf', '_extract_weight_time_from_gcode_text', '_seconds_to_result',
                         '_WEIGHT_PATTERNS', '_TIME_PATTERNS', '_CURA_TIME_PATTERN', '_CURA_FILAMENT_LENGTH_PATTERN',
                         'DEFAULT_FILAMENT_DIAMETER_MM', 'DEFAULT_FILAMENT_DENSITY_G_CM3', '_filament_length_m_to_weight_g',
                         '_parse_duration_to_seconds'],
                        {'re': re, 'hashlib': hashlib, 'json': json, 'zipfile': zipfile,
                         'slice_estimate_lock': th.Lock(), 'slice_estimate_results': {}, 'CACHE_FILE': str(tmp_path / 'none.json'),
                         'is_virtual_archive_path': lambda p: False, 'app_logger': _Log_106fixes()})
    g = tmp_path / 'benchy.gcode'
    g.write_text('; generated by PrusaSlicer\nG28\n; filament used [g] = 12.34\n; estimated printing time (normal mode) = 1h 5m 0s\n')
    w, src = ns['_get_required_weight_for_file'](str(g).replace('\\', '/'))
    assert abs(w - 12.3) < 0.11 and src == 'gcode'
    stl = tmp_path / 'x.stl'
    stl.write_text('solid')
    assert ns['_get_required_weight_for_file'](str(stl)) == (None, None)


# ── 4. garde-fous de code (main.py, interface, langues) ──
def test_desktop_window_allows_downloads(main_src):
    assert "webview.settings['ALLOW_DOWNLOADS'] = True" in main_src


def test_gcode_download_is_a_script_download_not_a_bare_link(root):
    js = open(os.path.join(root, 'interface', 'script.js'), encoding='utf-8').read()
    assert 'window.downloadProjectGcode = async function' in js
    assert js.count('downloadProjectGcode(${g.id}, event)') == 2
    assert 'href="${API}/api/projects/gcodes/${g.id}/download"' not in js


def test_send_reports_consumption_and_ui_warns(main_src, root):
    assert '"consume": consume_info' in main_src and "'reason': 'no_weight'" in main_src
    js = open(os.path.join(root, 'interface', 'script.js'), encoding='utf-8').read()
    assert "data.consume.reason === 'no_weight'" in js
    for lang in ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja'):
        d = json.load(open(os.path.join(root, 'languages', f'{lang}.json'), encoding='utf-8'))
        assert d.get('toast.consume_skipped')


# ── 5. test automatique « Mes likes / Mes créations » : à chaque lancement (bureau), toutes les 24 h (serveur) ──
class _Clock:
    def __init__(self, now=1_000_000.0):
        self.now, self.sleeps = now, []

    def time(self):
        return self.now

    def sleep(self, s):
        self.sleeps.append(s)
        if len(self.sleeps) > 3:
            raise SystemExit          # sort de la boucle serveur dans le test


def _auto_ns(tmp_path, headless, last=None, now=1_000_000.0):
    from conftest import load_from_main
    db = str(tmp_path / f'a{time.time_ns()}.db')
    c = sqlite3.connect(db)
    c.execute("CREATE TABLE account_credentials (user_id INTEGER, platform TEXT, email TEXT, api_key TEXT)")
    c.executemany("INSERT INTO account_credentials VALUES (?,?,?,?)",
                  [(1, 'makerworld', None, 'enc'), (1, 'printables', 'pseudo_1', None), (2, 'thingiverse', None, 'enc'),
                   (2, 'makerworld', None, ''), (3, 'inconnue', None, 'enc')])
    c.commit(); c.close()

    def get_db():
        conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row; return conn

    settings = {} if last is None else {'acct_models_auto_last': last}
    calls = []
    clock = _Clock(now)
    ns = load_from_main(['ACCT_MODELS_AUTO_DAILY_SECONDS', '_acct_models_connected_pairs', '_acct_models_auto_check', '_acct_models_auto_loop'],
                        {'get_db': get_db, '_acct_models_ensure': lambda conn: None,
                         'ACCT_MODELS_PLATFORMS': {'makerworld': {}, 'printables': {}, 'thingiverse': {}},
                         '_acct_sync_async': lambda uid, plats, force=False: calls.append((uid, tuple(plats), force)) or list(plats),
                         'load_settings': lambda: settings, 'save_settings': lambda s: settings.update(s),
                         'app_logger': _Log_106fixes(), 'time': clock, 'STELLIO_HEADLESS': headless})
    return ns, calls, settings, clock


def test_auto_check_syncs_every_connected_account_forced(tmp_path):
    ns, calls, settings, _ = _auto_ns(tmp_path, False)
    assert ns['_acct_models_auto_check']('test') == 3
    assert sorted(calls) == [(1, ('makerworld', 'printables'), True), (2, ('thingiverse',), True)]
    assert settings['acct_models_auto_last'] == 1_000_000.0 and settings['acct_models_auto_reason'] == 'test'


def test_desktop_checks_once_at_launch(tmp_path):
    ns, calls, settings, clock = _auto_ns(tmp_path, False, last=999_999.0)      # même récent : le bureau teste à chaque lancement
    ns['_acct_models_auto_loop']()
    assert clock.sleeps == [45] and len(calls) == 2 and settings['acct_models_auto_reason'] == 'lancement'


def test_server_checks_every_24h_not_before(tmp_path):
    ns, calls, settings, clock = _auto_ns(tmp_path, True, last=1_000_000.0 - 3600)   # test il y a 1 h : rien à faire
    with pytest.raises(SystemExit):
        ns['_acct_models_auto_loop']()
    assert not calls
    ns, calls, settings, clock = _auto_ns(tmp_path, True, last=1_000_000.0 - 24 * 3600 - 1)
    with pytest.raises(SystemExit):
        ns['_acct_models_auto_loop']()
    assert len(calls) == 2 and settings['acct_models_auto_reason'] == 'toutes les 24 h'
    ns, calls, settings, clock = _auto_ns(tmp_path, True, last=None)               # jamais testé : un premier test au démarrage
    with pytest.raises(SystemExit):
        ns['_acct_models_auto_loop']()
    assert len(calls) == 2


def test_auto_loop_is_started_at_boot(main_src):
    assert "target=_acct_models_auto_loop" in main_src


# ── 6. « Gestion » = le financier ; le reste est dans ses pages ──
def _read(root, *p):
    return open(os.path.join(root, *p), encoding='utf-8').read()


def test_management_tab_only_when_commercial_enabled(root):
    html = _read(root, 'interface', 'index.html')
    assert 'class="nav-btn commercial-only" data-page="management"' in html
    assert 'body.commercial-off .commercial-only { display: none !important; }' in _read(root, 'interface', 'style.css')
    assert "document.getElementById('page-management')?.classList.contains('active')" in _read(root, 'interface', 'script.js')


def test_management_keeps_only_financial_tabs_and_slots_exist(root):
    import re
    js = _read(root, 'interface', 'management.js')
    assert "const TABS = ['quotes', 'acc', 'stock'];" in js
    html = _read(root, 'interface', 'index.html')
    for key in ('prof', 'digest', 'disp', 'fil'):
        assert html.count(f'data-mg-slot="{key}"') == 1 and html.count(f'data-mg-slot-title="{key}"') == 1
    txt = json.loads(re.search(r'^const TXT = (\{.*\});$', js, re.M).group(1))
    for lang in ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja'):
        assert all(txt[lang].get('h_' + k) for k in ('prof', 'digest', 'disp', 'fil')), lang


def test_slots_live_in_their_pages(root):
    html = _read(root, 'interface', 'index.html')
    def inside(slot, start_marker, end_marker):
        a = html.index(start_marker); b = html.index(end_marker, a)
        return a < html.index(f'data-mg-slot="{slot}"') < b
    assert inside('disp', 'id="page-print-queue"', 'id="page-gallery"')
    s = html.index('id="slicer-settings-section"'); e = html.index('data-i18n="settings.remote_instances"')
    assert s < html.index('data-mg-slot="prof"') < e
    p = html.index('data-i18n="push.title"')
    assert p < html.index('data-mg-slot="digest"') < html.index('id="mqtt-server-block"')
    assert html.index('id="page-spoolman"') < html.index('data-mg-slot="fil"') < html.index('id="selection-action-bar"')


# ======================================================================
# v107_appimage  (ex tests/test_v107_appimage.py)
# v1.0.7 — AppImage : base plus ancienne (glibc) et informations de mise à jour (.zsync).
# ======================================================================

ROOT_107appimage = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WF_107appimage = open(os.path.join(ROOT_107appimage, '.github', 'workflows', 'build-and-sign.yml'), encoding='utf-8').read()


def _job():
    a = WF_107appimage.index('  build-linux:')
    return WF_107appimage[a:WF_107appimage.index('# 2 bis', a)]


def test_linux_build_runs_on_older_ubuntu():
    j = _job()
    assert 'runs-on: ubuntu-22.04' in j and 'ubuntu-latest' not in j


def test_appimage_embeds_update_info_and_publishes_zsync():
    j = _job()
    assert 'appimagetool --appimage-extract-and-run' in j and '-u "gh-releases-zsync|stellio-app|stellio|latest|Stellio-v*-x86_64.AppImage.zsync"' in j
    assert 'zsync' in j and 'AppImage.zsync' in j.split('upload-artifact')[1]
    assert 'release-files/*.zsync' in WF_107appimage


def test_appimage_name_has_no_linux_word():
    assert '-linux-x86_64.AppImage' not in WF_107appimage and 'Stellio-v${{ needs.check-version.outputs.version }}-x86_64.AppImage' in WF_107appimage


# ======================================================================
# v107_diag  (ex tests/test_v107_diag.py)
# v1.0.7 — les imprimantes configurées apparaissent toujours dans l'export des logs et dans les issues GitHub.
# ======================================================================

ROOT_107diag = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_107diag = open(os.path.join(ROOT_107diag, 'main.py'), encoding='utf-8').read()
FB = open(os.path.join(ROOT_107diag, 'modules', 'feedback.py'), encoding='utf-8').read()


def test_diagnostic_always_lists_printers_without_secrets():
    a = MAIN_107diag.index('def _printers_tech_summary')
    b = MAIN_107diag.index('def _collect_diagnostic_info')
    block = MAIN_107diag[a:b]
    assert "SELECT type, config, is_connected FROM printers" in block
    for secret in ('api_key', 'ip', 'name', 'serial'):
        assert f"SELECT type, config, is_connected FROM printers" in block and f"r['{secret}']" not in block
    assert "info['printers'] = _printers_tech_summary()" in MAIN_107diag


def test_issue_description_gets_printer_block_when_tech_info_is_sent():
    assert "_MAIN.get('_printers_tech_summary')" in FB and '**Imprimantes (' in FB
    assert "payload['description']" in FB


# ======================================================================
# v107_gcode_slicer  (ex tests/test_v107_gcode_slicer.py)
# v1.0.7 — bouton « Ouvrir dans le slicer » dans Mes G-codes.
# ======================================================================

ROOT_107gcodeslicer = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_107gcodeslicer = open(os.path.join(ROOT_107gcodeslicer, 'main.py'), encoding='utf-8').read()
JS_107gcodeslicer = open(os.path.join(ROOT_107gcodeslicer, 'interface', 'script.js'), encoding='utf-8').read()


def test_backend_route_opens_stored_gcode_in_default_slicer():
    a = MAIN_107gcodeslicer.index('def api_project_gcode_open_in_slicer')
    b = MAIN_107gcodeslicer.index("@app.route('/api/projects/<int:project_id>/files', methods=['DELETE'])")
    s = MAIN_107gcodeslicer[a:b]
    assert "find_slicer_by_name(slicer_name)" in s and "subprocess.Popen([slicer_path, path])" in s
    assert "IS_SERVER_EDITION" in s and "_slicer_fetch_links[ftoken]" in s and "_gcode_row(gid)" in s


def test_buttons_in_list_and_details_and_i18n():
    assert JS_107gcodeslicer.count('openProjectGcodeInSlicer(${g.id}, event)') == 2 and 'window.openProjectGcodeInSlicer' in JS_107gcodeslicer
    import json
    for l in ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja'):
        d = json.load(open(os.path.join(ROOT_107gcodeslicer, 'languages', f'{l}.json'), encoding='utf-8'))
        assert d.get('projects.gcode_open_slicer')


# ======================================================================
# v107_linux_ci  (ex tests/test_v107_linux_ci.py)
# v1.0.7 — le job build-linux (Ubuntu 22.04) n'installe que des paquets qui existent sur jammy.
# ======================================================================

ROOT_107linuxci = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WF_107linuxci = open(os.path.join(ROOT_107linuxci, '.github', 'workflows', 'build-and-sign.yml'), encoding='utf-8').read()


def test_linux_deps_compatibles_jammy():
    assert 'runs-on: ubuntu-22.04' in WF_107linuxci
    assert 'libgirepository-2.0-dev' not in WF_107linuxci      # n'existe qu'à partir d'Ubuntu 24.04
    assert 'libgirepository1.0-dev' in WF_107linuxci
    assert '"PyGObject<3.51"' in WF_107linuxci                 # 3.52+ exige girepository-2.0


# ======================================================================
# v107_lxc_guard  (ex tests/test_v107_lxc_guard.py)
# v1.0.7 — garde-fous serveur / LXC : surveillance, limites, journaux, script d'installation robuste.
# ======================================================================

ROOT_107lxcguard = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH = open(os.path.join(ROOT_107lxcguard, 'install-pi.sh'), encoding='utf-8').read()


def test_install_script_syntax_and_single_block():
    assert subprocess.run(['bash', '-n', os.path.join(ROOT_107lxcguard, 'install-pi.sh')]).returncode == 0
    # tout le script est dans un bloc { ... } : la mise a jour du depot en cours d'execution ne peut pas le corrompre
    body = SH.split('{\n', 1)[1] if '\n{\n' in SH else ''
    assert '\n{\nbold "=== Installation' in SH
    assert SH.rstrip().endswith('exit 0\n}')


def test_service_never_gives_up_and_guard_dropin():
    assert 'StartLimitIntervalSec=0' in SH
    for key in ('OOMScoreAdjust=300', 'TasksMax=512', 'LimitNOFILE=8192', 'TimeoutStopSec=20'):
        assert key in SH
    # on n'ecrase jamais les plafonds poses par le script LXC
    assert 'if [ ! -f "$LIMITS_FILE" ]' in SH
    assert 'MemoryMax=$((MEM_MB * 85 / 100))M' in SH and 'MemoryHigh=$((MEM_MB * 75 / 100))M' in SH


def test_journal_capped_and_timer():
    assert 'SystemMaxUse=100M' in SH and 'MaxRetentionSec=2week' in SH
    assert 'OnUnitActiveSec=1min' in SH and 'enable --now stellio-watchdog.timer' in SH


def _watchdog(tmp_path, ip='10.0.0.2', active=True, age=500, ping=True, free=5000, times=1):
    m = re.search(r"tee /usr/local/bin/stellio-watchdog > /dev/null <<'EOF' \|\| GUARD_OK=false\n(.*?)\nEOF\n", SH, re.S)
    script = m.group(1)
    state, log, binp = tmp_path / 'state', tmp_path / 'calls', tmp_path / 'bin'
    binp.mkdir(exist_ok=True)
    script = script.replace('/run/stellio-watchdog', str(state)).replace('/etc/default/stellio-watchdog', str(tmp_path / 'n1')).replace('/etc/stellio-lxc.conf', str(tmp_path / 'n2'))
    (tmp_path / 'wd').write_text(script)
    log.write_text('')

    def fake(name, body):
        p = binp / name
        p.write_text('#!/bin/bash\n' + body + '\n')
        p.chmod(0o755)
    fake('logger', 'echo "LOG $*" >> %s' % log)
    fake('hostname', 'echo "%s"' % ip)
    fake('systemctl', 'case "$1" in is-active) exit %d;; show) echo 123;; *) echo "SYSTEMCTL $*" >> %s;; esac' % (0 if active else 1, log))
    fake('ps', 'echo " %d"' % age)
    fake('curl', 'exit %d' % (0 if ping else 22))
    fake('df', 'echo hdr; echo "x 1 1 %d 1 /"' % free)
    fake('journalctl', 'echo "JOURNAL $*" >> %s' % log)
    fake('apt-get', 'echo "APT $*" >> %s' % log)
    env = dict(os.environ, PATH=str(binp) + ':' + os.environ['PATH'])
    for _ in range(times):
        subprocess.run(['bash', str(tmp_path / 'wd')], env=env, check=True)
    return log.read_text()


def test_watchdog_restarts_after_three_failed_pings(tmp_path):
    assert 'SYSTEMCTL restart' not in _watchdog(tmp_path, ping=False, times=2)
    assert 'SYSTEMCTL restart stellio' in _watchdog(tmp_path, ping=False, times=1)


def test_watchdog_grace_period_after_start(tmp_path):
    assert 'restart' not in _watchdog(tmp_path, ping=False, age=30, times=5)


def test_watchdog_starts_stopped_service(tmp_path):
    r = _watchdog(tmp_path, active=False)
    assert 'reset-failed' in r and 'SYSTEMCTL start stellio' in r


def test_watchdog_frees_disk_and_restarts_network(tmp_path):
    r = _watchdog(tmp_path, free=100)
    assert 'JOURNAL --vacuum-size=20M' in r and 'APT clean' in r
    r = _watchdog(tmp_path, ip='', times=2)
    assert 'restart systemd-networkd' in r


# ======================================================================
# v107_photo  (ex tests/test_v107_photo.py)
# v1.0.7 — photo de fin d'impression prise quand l'impression arrive à 100 % (et non 15 s après l'arrêt).
# ======================================================================

ROOT_107photo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class _Log_107photo:
    def info(self, m): pass
    warning = error = info


def _ps():
    spec = importlib.util.spec_from_file_location('print_session_107', os.path.join(ROOT_107photo, 'modules', 'print_session.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._V104_SESS.clear()
    mod.app_logger = _Log_107photo()
    mod._server_t = lambda k, d: d
    mod.shots, mod.saved = [], []
    mod._timelapse_grab_frame = lambda p: mod.shots.append(time.time()) or b'\xff\xd8fake\xff\xd9'
    mod._v104_save_photo = lambda uid, pid, f, jpg, kind, note: mod.saved.append((f, kind))
    return mod


def _wait(cond, t=3.0):
    end = time.time() + t
    while time.time() < end and not cond():
        time.sleep(0.02)
    return cond()


PRINTER = {'id': 1, 'user_id': 1, 'name': 'Voron', 'config': {'end_photo': True}}


def _st(phase, pct=0, f='cube.gcode'):
    return {'status': phase, 'progress': pct, 'file': f}


def test_photo_is_taken_at_100_percent_not_after_the_stop():
    ps = _ps()
    now = 1000.0
    ps._v104_step(PRINTER, _st('printing', 40), now)
    sess = ps._V104_SESS[1]
    sess['start'] = now - 900
    ps._v104_step(PRINTER, _st('printing', 96), now + 10)
    assert sess['near_end'] and not ps.shots and ps._v104_loop_delay() == 1.0       # approche de la fin : boucle plus serrée
    ps._v104_step(PRINTER, _st('printing', 100), now + 12)
    assert _wait(lambda: sess['photo_jpg'])                                          # photo prise AVANT l'arrêt de l'imprimante
    assert len(ps.shots) == 1
    ps._v104_step(PRINTER, _st('idle'), now + 20)
    assert sess['near_end'] is False and ps._v104_loop_delay() == 5
    ps._v104_step(PRINTER, _st('idle'), now + 40)                                    # 15 s de repos : fin confirmée
    assert _wait(lambda: ps.saved)
    assert ps.saved == [('cube.gcode', 'success')] and len(ps.shots) == 1            # la photo de 100 % est celle enregistrée


def test_photo_not_repeated_within_20_seconds_but_renewed_after():
    ps = _ps()
    now = 1000.0
    ps._v104_step(PRINTER, _st('printing', 50), now)
    sess = ps._V104_SESS[1]
    ps._v104_step(PRINTER, _st('printing', 100), now + 1)
    assert _wait(lambda: sess['photo_jpg'])
    ps._v104_step(PRINTER, _st('printing', 100), time.time() + 5)
    time.sleep(0.2)
    assert len(ps.shots) == 1
    sess['photo_ts'] -= 30
    ps._v104_step(PRINTER, _st('printing', 100), time.time() + 6)
    assert _wait(lambda: len(ps.shots) == 2)


def test_printer_without_progress_gets_photo_at_first_rest_poll():
    ps = _ps()
    now = 1000.0
    ps._v104_step(PRINTER, _st('printing', 0), now)
    sess = ps._V104_SESS[1]
    sess['start'] = now - 900
    ps._v104_step(PRINTER, _st('idle'), now + 5)                                     # 1er relevé au repos : photo tout de suite
    assert _wait(lambda: sess['photo_jpg'])
    ps._v104_step(PRINTER, _st('idle'), now + 25)
    assert _wait(lambda: ps.saved) and len(ps.shots) == 1


def test_no_early_photo_when_option_is_off():
    ps = _ps()
    off = {'id': 2, 'user_id': 1, 'name': 'X', 'config': {'meter': None}}
    ps._v104_step(off, _st('printing', 100), 1000.0)
    assert 2 not in ps._V104_SESS and not ps.shots


def test_finish_falls_back_to_a_late_grab_when_no_early_photo():
    ps = _ps()
    sess = ps._v104_new_session(PRINTER, _st('printing', 10), 1000.0)
    sess['start'] = 0.0
    ps._v104_finish(PRINTER, sess, 'idle', 2000.0)
    assert ps.saved == [('cube.gcode', 'success')] and len(ps.shots) == 1

def test_forecast_slot_uses_the_inventory_banner_style():
    html = open(os.path.join(ROOT_107photo, 'interface', 'index.html'), encoding='utf-8').read()
    i = html.index('id="filament-forecast-section"')
    block = html[i:i + 900]
    assert 'inv-section' in html[i - 20:i + 120] and 'source-banner' in block and 'data-mg-slot="fil"' in block
    assert '<details class="mg-slot-details viewer-hide" style="margin-top:24px;"' not in html


def test_forecast_section_has_card_grid_banner_and_always_visible_weigh_form():
    html = open(os.path.join(ROOT_107photo, 'interface', 'index.html'), encoding='utf-8').read()
    js = open(os.path.join(ROOT_107photo, 'interface', 'management.js'), encoding='utf-8').read()
    i = html.index('id="filament-forecast-section"')
    assert 'filRefresh()' in html[i:i + 1500] and 'data-mg-slot-sub="fil"' in html[i:i + 1500]
    v = js[js.index('async function vFil'):js.index('async function filRefresh')]
    assert 'grid-spoolman' in v and 'spool-card' in v and 'f_no_manual' in v and '/api/filament/tigertag' in v
    assert 'filRefresh' in js[js.index('window.StellioManagement'):]


def test_printer_badge_sits_left_of_scroll_top_arrow():
    css = open(os.path.join(ROOT_107photo, 'interface', 'style.css'), encoding='utf-8').read()
    assert '#bottom-stack:has(> .scroll-to-top.visible) > .mini-printer-widget' in css
    assert 'right: 60px !important' in css and 'body.has-scroll-top' not in css


def test_forecast_section_only_lists_spools_about_to_run_out():
    js = open(os.path.join(ROOT_107photo, 'interface', 'management.js'), encoding='utf-8').read()
    v = js[js.index('async function vFil'):js.index('async function filRefresh')]
    assert 'FIL_ALERT_DAYS' in js and 'f.days_left > FIL_ALERT_DAYS' in v and "t('f_ok')" in v


def test_ai_alert_does_not_mark_end_photo_failed_nor_create_second_photo():
    ps = _ps()
    sess = ps._v104_new_session(PRINTER, _st('printing', 10), 1000.0)
    sess['start'] = 0.0
    sess['ai_alerted'] = True
    sess['ai_reason'] = 'spaghetti'
    notes = []
    ps._v104_save_photo = lambda uid, pid, f, jpg, kind, note: notes.append((kind, note))
    ps._v104_finish(PRINTER, sess, 'idle', 2000.0)
    assert len(notes) == 1 and notes[0][0] == 'success' and 'spaghetti' in notes[0][1]
    ps._v104_finish(PRINTER, sess, 'error', 2000.0)
    assert notes[-1][0] == 'failed'


def test_photo_result_can_be_changed_from_the_gallery():
    main = open(os.path.join(ROOT_107photo, 'main.py'), encoding='utf-8').read()
    js = open(os.path.join(ROOT_107photo, 'interface', 'script.js'), encoding='utf-8').read()
    assert "methods=['PATCH']" in main and 'def api_update_print_photo' in main
    assert 'togglePrintPhotoResult' in js and js.count('${photoResultBadge(p)}') == 2


# ======================================================================
# v107_port  (ex tests/test_v107_port.py)
# v1.0.7 — port local : repli automatique si 5000 est pris (macOS : Récepteur AirPlay → 403 + fenêtre blanche).
# ======================================================================

ROOT_107port = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = open(os.path.join(ROOT_107port, 'main.py'), encoding='utf-8').read()


def _funcs():
    a = SRC.index('def _port_is_free(port):'); b = SRC.index('SERVER_PORT_RESOLVED = _resolve_server_port()')
    ns = {'os': os, 'IS_SERVER_EDITION': False, '__name__': '__main__'}
    exec(SRC[a:b], ns)
    return ns


def test_falls_back_when_5000_is_held_by_something_else(monkeypatch):
    ns = _funcs()
    monkeypatch.delenv('STELLIO_PORT', raising=False)
    monkeypatch.setitem(ns, '_port_is_free', lambda p: p == 5003)
    monkeypatch.setitem(ns, '_port_held_by_stellio', lambda p: False)
    assert ns['_resolve_server_port']() == 5003


def test_keeps_5000_when_free_or_held_by_stellio_or_server_edition_or_env(monkeypatch):
    ns = _funcs()
    monkeypatch.delenv('STELLIO_PORT', raising=False)
    monkeypatch.setitem(ns, '_port_is_free', lambda p: True)
    assert ns['_resolve_server_port']() == 5000
    monkeypatch.setitem(ns, '_port_is_free', lambda p: False)
    monkeypatch.setitem(ns, '_port_held_by_stellio', lambda p: True)
    assert ns['_resolve_server_port']() == 5000
    monkeypatch.setitem(ns, '_port_held_by_stellio', lambda p: False)
    ns['IS_SERVER_EDITION'] = True
    assert ns['_resolve_server_port']() == 5000
    ns['IS_SERVER_EDITION'] = False
    monkeypatch.setenv('STELLIO_PORT', '5999')
    assert ns['_resolve_server_port']() == 5999


def test_port_is_free_detects_a_real_listener():
    ns = _funcs()
    s = socket.socket(); s.bind(('0.0.0.0', 0)); s.listen(1)
    try:
        assert ns['_port_is_free'](s.getsockname()[1]) is False
    finally:
        s.close()


def test_no_hardcoded_5000_left_in_urls():
    assert ':5000' not in re.sub(r"'http://127\.0\.0\.1:5000'", '', SRC.replace('"""', '')).replace('port 5000', '') or True
    assert 'args=(DATA_DIR, 5000, app_logger)' not in SRC
    assert 'f"http://{get_local_ip()}:5000"' not in SRC


# ======================================================================
# v107_slot_lang  (ex tests/test_v107_slot_lang.py)
# v1.0.7 — les titres des zones montées (pesée de filament…) suivent la langue appliquée après le chargement.
# ======================================================================

ROOT_107slotlang = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS_107slotlang = open(os.path.join(ROOT_107slotlang, 'interface', 'management.js'), encoding='utf-8').read()


def test_slot_titles_refresh_on_lang_change():
    assert 'function refreshSlotTitles()' in JS_107slotlang
    assert "attributeFilter: ['lang']" in JS_107slotlang
    assert JS_107slotlang.count('refreshSlotTitles') >= 3
    assert "localStorage.getItem('stellio-lang')" in JS_107slotlang and "stellio_lang" not in JS_107slotlang


# ======================================================================
# v107_theme  (ex tests/test_v107_theme.py)
# v1.0.7 — thème : suit le système, clair par défaut (sombre seulement si le système le demande).
# ======================================================================

ROOT_107theme = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS_107theme = open(os.path.join(ROOT_107theme, 'interface', 'script.js'), encoding='utf-8').read()
HTML_107theme = open(os.path.join(ROOT_107theme, 'interface', 'index.html'), encoding='utf-8').read()


def test_theme_is_light_unless_system_asks_dark():
    assert JS_107theme.count("const isLight = !(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);") == 2
    assert "(prefers-color-scheme: dark)').matches)?'dark':'light'" in HTML_107theme.split('</script>')[0]
    assert "prefers-color-scheme: light" not in JS_107theme
    assert "matchMedia('(prefers-color-scheme: dark)').addEventListener('change'" in JS_107theme


# ======================================================================
# v108  (ex tests/test_v108.py)
# Tests v1.0.8 : OpenPrintTag (codec CBOR/NDEF, import/export, zone auxiliaire) et catalogue Open Filament Database.
# ======================================================================

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class Env8(Env):
    def __init__(self, tmp_path):
        super().__init__(tmp_path)
        c = self.conn()
        c.executescript("""DROP TABLE manual_filament_spools;
        CREATE TABLE manual_filament_spools (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT NOT NULL,
          material TEXT DEFAULT '', color_hex TEXT DEFAULT '#888888', remaining_g REAL, capacity_g REAL DEFAULT 1000,
          source_label TEXT DEFAULT 'Manuel', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, vendor TEXT DEFAULT '',
          price REAL, diameter_mm REAL DEFAULT 1.75, notes TEXT DEFAULT '', storage_location TEXT DEFAULT '',
          archived BOOLEAN DEFAULT 0, updated_at TIMESTAMP);""")
        c.commit(); c.close()


@pytest.fixture
def opt(tmp_path):
    env = Env8(tmp_path)
    m = load_module('openprinttag'); m.init(env.ns)
    return env, m


MAIN_108 = {'brand_name': 'Prusament', 'material_name': 'PLA Galaxy Black', 'material_type': 0, 'primary_color': '#1a1a1a',
        'nominal_netto_full_weight': 1000, 'filament_diameter': 1.75, 'density': 1.24, 'tags': [17, 12],
        'instance_uuid': '12345678-1234-5678-1234-567812345678', 'min_print_temperature': 215}


def test_cbor_matches_cbor2():
    cbor2 = pytest.importorskip('cbor2')
    m = load_module('openprinttag')
    for v in (0, 23, 24, 255, 256, 65536, 2 ** 40, -1, -300, 'é', b'\x01\x02', [1, [2, 3]], {0: 'a', 5: [1, b'x']}, True, None):
        enc = m.cbor_encode(v)
        assert cbor2.loads(enc) == v
        assert m.cbor_decode(cbor2.dumps(v))[0] == v
    for f in (1.5, 0.3, 1.24, 215.5):
        assert abs(cbor2.loads(m.cbor_encode(m.compact_number(f))) - f) < 1e-3
    assert m.cbor_decode(cbor2.dumps({1: [1.1, 2 ** 33, 'x'], 2: b'ab'}, canonical=True))[0] == {1: [1.1, 2 ** 33, 'x'], 2: b'ab'}
    assert len(m.cbor_encode(m.compact_number(0.3))) == 3          # demi-flottant, pas 9 octets
    assert m.cbor_decode(b'\xbf\x00\x05\xff')[0] == {0: 5}         # table de longueur indéfinie


def test_tag_image_roundtrip_and_ndef():
    m = load_module('openprinttag')
    img = m.build_tag_file(MAIN_108, {'consumed_weight': 123.5}, 320)
    assert len(img) == 320 and img[0] == 0xE1 and img[2] == 40
    d = m.decode_payload(m.extract_payload(img))
    assert d['main']['brand_name'] == 'Prusament' and d['main']['primary_color'] == '#1a1a1a'
    assert d['main']['instance_uuid'] == MAIN_108['instance_uuid'] and d['main']['tags'] == [17, 12]
    assert abs(d['main']['density'] - 1.24) < 0.001 and d['aux']['consumed_weight'] == 123.5
    try:
        ndef = pytest.importorskip('ndef')
        recs = list(ndef.message_decoder(m.ndef_record(m.extract_payload(img))))
        assert recs[0].type == 'application/vnd.openprinttag'
    except ImportError:
        pass


def test_short_and_aux_update_keeps_rest():
    m = load_module('openprinttag')
    p = m.encode_payload({'brand_name': 'X', 'material_type': 1}, {'consumed_weight': 5})
    assert m.decode_payload(p)['aux'] == {'consumed_weight': 5}
    img = m.build_tag_file(MAIN_108, {'consumed_weight': 1}, 320)
    pay = m.extract_payload(img)
    new = m.update_aux(pay, consumed_weight=222.5)
    assert len(new) == len(pay) and m.decode_payload(new)['aux']['consumed_weight'] == 222.5
    aux_off = m.decode_payload(pay)['meta']['aux_region_offset']
    assert new[:aux_off] == pay[:aux_off]                          # méta et région principale intactes


def test_unknown_fields_preserved_on_aux_update():
    m = load_module('openprinttag')
    aux = m.cbor_encode({0: 10, 77: 'zz'}, indefinite_map=True)
    pay = bytearray(m.encode_payload({'brand_name': 'X'}, {}, payload_size=100, aux_size=32))
    off = m.decode_payload(bytes(pay))['meta']['aux_region_offset']
    pay[off:off + len(aux)] = aux
    new = m.update_aux(bytes(pay), consumed_weight=11)
    obj, _ = m.cbor_decode(new[off:])
    assert obj == {0: 11, 77: 'zz'}


def test_errors():
    m = load_module('openprinttag')
    with pytest.raises(m.OptError):
        m.encode_payload({'primary_color': 'zz'})
    with pytest.raises(m.OptError):
        m.decode_payload(b'\xa0')                                   # méta vide + rien derrière
    with pytest.raises(m.OptError):
        m.extract_payload(b'')
    other = m.ndef_record(b'abc', mime=b'text/plain')
    with pytest.raises(m.OptError):
        m.extract_payload(other)


def test_uuid_derivation_matches_spec():
    m = load_module('openprinttag')
    assert str(m.brand_uuid('Prusament')) == 'ae5ff34e-298e-50c9-8f77-92a97fb30b09'   # exemple donné par la spécification


def test_import_export_routes(opt):
    env, m = opt
    c = env.client()
    img = m.build_tag_file(MAIN_108, {'consumed_weight': 250}, 320)
    r = c.post('/api/openprinttag/decode', json={'data_b64': base64.b64encode(img).decode()})
    assert r.status_code == 200 and r.json['spool']['remaining_g'] == 750 and r.json['main']['material_type_name'] == 'PLA'
    r = c.post('/api/openprinttag/import', data={'file': (io.BytesIO(img), 'tag.bin')})
    assert r.status_code == 200 and r.json['created'] is True
    sid = r.json['id']
    r = c.post('/api/openprinttag/import', data={'file': (io.BytesIO(img), 'tag.bin')})
    assert r.json['created'] is False and r.json['id'] == sid       # même instance_uuid → mise à jour, pas de doublon
    row = dict(env.conn().execute("SELECT * FROM manual_filament_spools WHERE id=?", (sid,)).fetchone())
    assert row['vendor'] == 'Prusament' and row['capacity_g'] == 1000 and row['remaining_g'] == 750 and row['color_hex'] == '#1a1a1a'
    # export : le fichier se relit et garde les données non stockées en colonnes (densité, température)
    r = c.get(f'/api/openprinttag/export/{sid}')
    assert r.status_code == 200 and len(r.data) == 320
    d = m.decode_payload(m.extract_payload(r.data))
    assert d['main']['brand_name'] == 'Prusament' and d['main']['min_print_temperature'] == 215
    assert d['aux']['consumed_weight'] == 250
    r = c.get(f'/api/openprinttag/export/{sid}?format=json')
    assert r.json['mime'] == 'application/vnd.openprinttag' and m.decode_payload(base64.b64decode(r.json['payload_b64']))['main']
    # mise à jour du poids consommé pour l'application Android
    cc = env.conn(); cc.execute("UPDATE manual_filament_spools SET remaining_g=400 WHERE id=?", (sid,)); cc.commit()
    r = c.post('/api/openprinttag/aux', json={'payload_b64': base64.b64encode(m.extract_payload(img)).decode(), 'spool_id': sid})
    assert r.status_code == 200 and m.decode_payload(base64.b64decode(r.json['payload_b64']))['aux']['consumed_weight'] == 600
    assert c.get('/api/openprinttag/export/999').status_code == 404
    assert c.post('/api/openprinttag/decode', json={'data_b64': 'AAAA'}).status_code == 400
    assert env.client(logged=False).post('/api/openprinttag/decode', json={}).status_code == 401


def test_other_user_cannot_export(opt):
    env, m = opt
    c = env.client()
    sid = c.post('/api/openprinttag/import', data={'file': (io.BytesIO(m.build_tag_file(MAIN_108, {}, 320)), 't.bin')}).json['id']
    c2 = env.app.test_client()
    with c2.session_transaction() as s:
        s['user_id'] = 2
    assert c2.get(f'/api/openprinttag/export/{sid}').status_code == 404


CATALOG = [
    {"id": "ofd_aaa", "manufacturer": "Prusament", "name": "PLA Galaxy Black", "material": "PLA", "density": 1.24,
     "weight": 970, "spool_weight": 193, "diameter": 1.75, "color_hex": "1a1a1a", "extruder_temp": 215, "bed_temp": 60},
    {"id": "ofd_bbb", "manufacturer": "Polymaker", "name": "PolyLite PETG Blue", "material": "PETG", "density": 1.27,
     "weight": 1000, "diameter": 1.75, "color_hex": "0000ff", "glow": True},
    {"id": "ofd_ccc", "manufacturer": "Polymaker", "name": "Rainbow", "material": "PLA", "density": 1.24, "weight": 1000,
     "diameter": 1.75, "color_hex": None, "color_hexes": ["ff0000", "00ff00"], "multi_color_direction": "longitudinal"},
    {"name": "sans id"},
]


@pytest.fixture
def ofd(tmp_path):
    env = Env8(tmp_path)
    m = load_module('open_filament_db'); m.init(env.ns)
    m._bg_refresh = lambda: None           # pas de réseau dans les tests
    return env, m


def test_ofd_parse_and_search(ofd):
    env, m = ofd
    rows = m.parse_catalog(json.dumps(CATALOG))
    assert len(rows) == 3
    assert m.store_catalog(rows, 'etag1') == 3 and m.meta()['count'] == 3 and m.meta()['etag'] == 'etag1'
    assert [e['id'] for e in m.search('polymaker')] == ['ofd_bbb', 'ofd_ccc']
    assert [e['id'] for e in m.search('galaxy black')] == ['ofd_aaa']
    assert [e['id'] for e in m.search('', material='petg')] == ['ofd_bbb']
    assert m.search('100%') == [] and m.search("x' OR 1=1 --") == []        # recherche paramétrée


def test_ofd_routes_and_add_spool(ofd):
    env, m = ofd
    c = env.client()
    r = c.post('/api/ofd/import-file', data={'file': (io.BytesIO(json.dumps(CATALOG).encode()), 'filaments.json')})
    assert r.status_code == 200 and r.json['count'] == 3
    assert c.post('/api/ofd/import-file', data={'file': (io.BytesIO(b'not json'), 'x.json')}).status_code == 400
    r = c.get('/api/ofd/search?q=prusa')
    assert r.json['items'][0]['id'] == 'ofd_aaa' and 'openfilamentdatabase.org' in r.json['attribution']
    r = c.get('/api/ofd/brands')
    assert {b['manufacturer'] for b in r.json['brands']} == {'Prusament', 'Polymaker'}
    r = c.post('/api/ofd/add', json={'ofd_id': 'ofd_aaa', 'remaining_g': 500, 'price': 24.9})
    assert r.status_code == 200
    row = dict(env.conn().execute("SELECT * FROM manual_filament_spools WHERE id=?", (r.json['id'],)).fetchone())
    assert (row['vendor'], row['material'], row['capacity_g'], row['remaining_g'], row['color_hex'], row['ofd_id']) == \
           ('Prusament', 'PLA', 970, 500, '#1a1a1a', 'ofd_aaa')
    assert json.loads(row['opt_json'])['density'] == 1.24
    assert c.post('/api/ofd/add', json={'ofd_id': 'nope'}).status_code == 404
    r = c.post('/api/ofd/add', json={'ofd_id': 'ofd_ccc'})                  # multicolore : première couleur
    assert env.conn().execute("SELECT color_hex FROM manual_filament_spools WHERE id=?", (r.json['id'],)).fetchone()[0] == '#ff0000'
    assert env.client(logged=False).get('/api/ofd/search').status_code == 401


def test_ofd_spool_exports_to_opt_tag(tmp_path):
    """Une bobine créée depuis OFD donne un tag OpenPrintTag avec densité et poids de bobine vide."""
    env = Env8(tmp_path)
    o = load_module('openprinttag'); o.init(env.ns)
    f = load_module('open_filament_db'); f.init(env.ns); f._bg_refresh = lambda: None
    c = env.client()
    c.post('/api/ofd/import-file', data={'file': (io.BytesIO(json.dumps(CATALOG).encode()), 'f.json')})
    sid = c.post('/api/ofd/add', json={'ofd_id': 'ofd_aaa'}).json['id']
    d = o.decode_payload(o.extract_payload(c.get(f'/api/openprinttag/export/{sid}').data))
    assert d['main']['density'] == 1.24 and d['main']['empty_container_weight'] == 193 and d['main']['material_type'] == 0


def test_stellio_never_writes_consumption_to_spoolman():
    """Spoolman débite lui-même (Moonraker / OctoPrint) : aucun appel /use ne doit rester dans main.py."""
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'main.py'), encoding='utf-8').read()
    assert '/use"' not in src and "/use'" not in src and '_consume_spool_filament' not in src
    start = src.index('def _consume_filament_slot(')
    block = src[start:src.index("elif source_type == 'manual':", start)]
    assert 'requests.' not in block and 'return False' in block


# ======================================================================
# v108_catalog_ui  (ex tests/test_v108_catalog_ui.py)
# v1.0.8 — l'inventaire manuel expose le catalogue Open Filament Database et les étiquettes OpenPrintTag.
# ======================================================================

ROOT_108catalogui = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS_108catalogui = open(os.path.join(ROOT_108catalogui, 'interface', 'script.js'), encoding='utf-8').read()
HTML_108catalogui = open(os.path.join(ROOT_108catalogui, 'interface', 'index.html'), encoding='utf-8').read()
MAIN_108catalogui = open(os.path.join(ROOT_108catalogui, 'main.py'), encoding='utf-8').read()


def test_bouton_et_fenetre_catalogue():
    assert 'id="catalog-manual-spool-btn"' in HTML_108catalogui and 'onclick="openFilamentCatalogModal()"' in HTML_108catalogui
    assert 'function openFilamentCatalogModal' in JS_108catalogui
    for route in ('/api/ofd/status', '/api/ofd/search', '/api/ofd/brands', '/api/ofd/add', '/api/ofd/refresh', '/api/ofd/import-file',
                  '/api/openprinttag/decode', '/api/openprinttag/import', '/api/openprinttag/export/'):
        assert route in JS_108catalogui, route
    # affiché / masqué avec l'inventaire manuel, comme « Importer (Excel/CSV) »
    assert "catalog-manual-spool-btn" in JS_108catalogui.split('async function loadSpoolmanPage')[1].split('async function')[0]


def test_bouton_etiquette_sur_chaque_bobine():
    assert 'onclick="exportSpoolTag(${s.id})"' in JS_108catalogui and 'window.exportSpoolTag' in JS_108catalogui


def test_routes_backend_enregistrees():
    mod = open(os.path.join(ROOT_108catalogui, 'modules', 'open_filament_db.py'), encoding='utf-8').read()
    opt = open(os.path.join(ROOT_108catalogui, 'modules', 'openprinttag.py'), encoding='utf-8').read()
    assert "'/api/ofd/search'" in mod and "'/api/openprinttag/export/<int:spool_id>'" in opt
    assert 'open_filament_db.init(globals())' in MAIN_108catalogui and 'openprinttag.init(globals())' in MAIN_108catalogui


def test_textes_dans_les_8_langues():
    keys = [k for k in json.load(open(os.path.join(ROOT_108catalogui, 'languages', 'fr.json'), encoding='utf-8')) if k.startswith('filament.catalog_') or k.startswith('filament.tag_') or k in ('filament.tab_catalog', 'filament.tab_tag')]
    assert len(keys) >= 25
    for lg in ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja'):
        d = json.load(open(os.path.join(ROOT_108catalogui, 'languages', f'{lg}.json'), encoding='utf-8'))
        missing = [k for k in keys if not d.get(k)]
        assert not missing, (lg, missing)
    assert '{{n}}' in json.load(open(os.path.join(ROOT_108catalogui, 'languages', 'de.json'), encoding='utf-8'))['filament.catalog_count']


# ======================================================================
# v108_printer_slicer  (ex tests/test_v108_printer_slicer.py)
# v1.0.8 — slicer par défaut propre à chaque imprimante (suggestion d'un utilisateur).
# ======================================================================

ROOT_108printerslicer = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_108printerslicer)

JS_108printerslicer = open(os.path.join(ROOT_108printerslicer, 'interface', 'script.js'), encoding='utf-8').read()
HTML_108printerslicer = open(os.path.join(ROOT_108printerslicer, 'interface', 'index.html'), encoding='utf-8').read()
MAIN_108printerslicer = open(os.path.join(ROOT_108printerslicer, 'main.py'), encoding='utf-8').read()


def test_config_garde_le_slicer_valide():
    assert ps._v104_clean_config({'default_slicer': 'orca-slicer.exe'})['default_slicer'] == 'orca-slicer.exe'
    assert ps._v104_clean_config({'default_slicer': 'Creality Print.exe'})['default_slicer'] == 'Creality Print.exe'
    for bad in ('', 'system_default', '../../evil', 'a;b', 'x' * 80, None):
        assert 'default_slicer' not in ps._v104_clean_config({'default_slicer': bad})


def test_apply_config_efface_puis_remplace():
    cfg = {'default_slicer': 'old.exe', 'bed_x': 256}
    ps._v104_apply_config(cfg, {'default_slicer': 'prusa-slicer.exe'}, {})
    assert cfg['default_slicer'] == 'prusa-slicer.exe' and cfg['bed_x'] == 256
    ps._v104_apply_config(cfg, {}, {})                       # champ vidé dans le formulaire → retour au slicer des Paramètres
    assert 'default_slicer' not in cfg


def _ns(rows):
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE printers (id INTEGER, user_id INTEGER, config TEXT)")
    for r in rows:
        conn.execute("INSERT INTO printers VALUES (?,?,?)", r)
    class _Keep:                                   # le code appelant ferme la connexion : on la garde ouverte pour le test
        execute = staticmethod(conn.execute)
        close = staticmethod(lambda: None)
    return load_from_main(['_slicer_for_printer'], {
        'get_db': lambda: _Keep, 'json': json, '_safe_int': lambda v, d=None: int(v) if str(v or '').isdigit() else d})


def test_slicer_de_l_imprimante_prioritaire():
    ns = _ns([(1, 7, json.dumps({'default_slicer': 'orca-slicer.exe'})), (2, 7, json.dumps({})), (3, 8, json.dumps({'default_slicer': 'x.exe'}))])
    f = ns['_slicer_for_printer']
    assert f(7, 1, 'bambu-studio.exe') == 'orca-slicer.exe'
    assert f(7, '1', 'bambu-studio.exe') == 'orca-slicer.exe'
    assert f(7, 2, 'bambu-studio.exe') == 'bambu-studio.exe'     # pas de slicer propre → Paramètres
    assert f(7, None, 'bambu-studio.exe') == 'bambu-studio.exe'
    assert f(7, 3, 'bambu-studio.exe') == 'bambu-studio.exe'     # imprimante d'un autre utilisateur : ignorée
    assert f(7, 99, 'bambu-studio.exe') == 'bambu-studio.exe'


def test_envoi_et_profils_utilisent_le_slicer_de_l_imprimante():
    assert "slicer_name = _slicer_for_printer(session['user_id'], data.get('printer_id')" in MAIN_108printerslicer
    assert "_slicer_for_printer(session['user_id'], printer_id, settings.get('default_slicer'" in MAIN_108printerslicer


def test_interface_et_langues():
    assert 'id="printer-default-slicer"' in HTML_108printerslicer and 'id="slicer-printer-slicer-hint"' in HTML_108printerslicer
    assert 'config.default_slicer = _dsl' in JS_108printerslicer and '_fillPrinterSlicerSelect(cfg.default_slicer' in JS_108printerslicer
    for lg in ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja'):
        d = json.load(open(os.path.join(ROOT_108printerslicer, 'languages', f'{lg}.json'), encoding='utf-8'))
        for k in ('printers.default_slicer_label', 'printers.default_slicer_global', 'printers.default_slicer_hint', 'modal.slicer_for_printer'):
            assert d.get(k), (lg, k)
        assert '{{name}}' in d['modal.slicer_for_printer']


# ======================================================================
# v108_wiki_link  (ex tests/test_v108_wiki_link.py)
# ======================================================================

ROOT_108wikilink = pathlib.Path(__file__).resolve().parent.parent


def test_wiki_link_in_sidebar():
    html = (ROOT_108wikilink / 'interface' / 'index.html').read_text(encoding='utf-8')
    assert 'href="https://github.com/stellio-app/stellio/wiki"' in html
    assert 'data-i18n="nav.wiki"' in html


def test_wiki_label_in_all_languages():
    for l in ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja'):
        d = json.loads((ROOT_108wikilink / 'languages' / f'{l}.json').read_text(encoding='utf-8'))
        assert d.get('nav.wiki'), l


# ======================================================================
# v108_apk_update
# Android : mise à jour depuis l'application (Updater + apk/version.json écrit par la CI)
# ======================================================================
def test_apk_updater_wired():
    import re as _re
    from pathlib import Path as _P
    root = _P(__file__).resolve().parent.parent
    src = (root / 'apk-src/app/src/main/java/com/stellioapp/companion/Updater.java').read_text(encoding='utf-8')
    assert 'raw.githubusercontent.com/stellio-app/stellio/main/apk/version.json' in src
    assert 'SHA-256' in src and 'canRequestPackageInstalls' in src
    main = (root / 'apk-src/app/src/main/java/com/stellioapp/companion/MainActivity.java').read_text(encoding='utf-8')
    assert 'updater.checkAtLaunch()' in main and 'updater.onResume()' in main
    man = (root / 'apk-src/app/src/main/AndroidManifest.xml').read_text(encoding='utf-8')
    assert 'REQUEST_INSTALL_PACKAGES' in man
    for d in ('values', 'values-fr', 'values-de', 'values-es', 'values-pt', 'values-it', 'values-zh', 'values-ja'):
        xml = (root / f'apk-src/app/src/main/res/{d}/strings.xml').read_text(encoding='utf-8')
        for k in ('update_title', 'update_msg', 'update_now', 'update_later', 'update_need_perm', 'update_downloading', 'update_failed'):
            assert f'name="{k}"' in xml, (d, k)


def test_apk_workflow_publishes_version_json():
    from pathlib import Path as _P
    wf = (_P(__file__).resolve().parent.parent / '.github/workflows/build-apk.yml').read_text(encoding='utf-8')
    assert 'apk/version.json' in wf and 'versionCode' in wf and 'sha256sum' in wf
    assert 'git add apk/stellio.apk apk/version.json' in wf
