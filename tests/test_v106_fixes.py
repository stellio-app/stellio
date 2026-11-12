"""v1.0.6 — correctifs signalés par des utilisateurs : photo de fin / IA / prise non enregistrées (Klipper, OctoPrint, PrusaLink),
timelapse (flux MJPEG sans ffmpeg, micro-coupures réseau), téléchargement d'un G-code lié, décompte de bobine (poids lu dans le G-code)."""
import importlib.util, io, json, os, sqlite3, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name):
    spec = importlib.util.spec_from_file_location(name + '_fix_test', os.path.join(ROOT, 'modules', name + '.py'))
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


def _jpeg():
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
    _Cam.jpg = _jpeg()
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


class _Log:
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

    log = _Log()
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
                         'is_virtual_archive_path': lambda p: False, 'app_logger': _Log()})
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
                         'app_logger': _Log(), 'time': clock, 'STELLIO_HEADLESS': headless})
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

