"""Stellio — timelapse des impressions (images périodiques, assemblage vidéo, lecture, suppression)

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `timelapse.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import datetime
import os
import re
import requests
import shutil
import subprocess
import threading
import time

_REQUIRED = (
    'BAMBU_RTSP_PORT322_MODELS',
    'DATA_DIR',
    'FFMPEG_TOOL',
    '_bambuddy_get',
    '_bambuddy_printer_id',
    '_ensure_v086_tables',
    '_generate_bambu_mjpeg_stream',
    '_generate_bambu_rtsp_mjpeg_stream',
    '_popen_kwargs_silent',
    '_printer_status_cached',
    '_resolve_printer_camera',
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'load_settings',
    'login_required',
    'parse_printer_config',
    'request',
    'save_settings',
    'send_file',
    'session',
)
_OVERRIDABLE = ('datetime', 'os', 're', 'requests', 'shutil', 'subprocess', 'threading', 'time', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
BAMBU_RTSP_PORT322_MODELS = None
DATA_DIR = None
FFMPEG_TOOL = None
_bambuddy_get = None
_bambuddy_printer_id = None
_ensure_v086_tables = None
_generate_bambu_mjpeg_stream = None
_generate_bambu_rtsp_mjpeg_stream = None
_popen_kwargs_silent = None
_printer_status_cached = None
_resolve_printer_camera = None
app = None
app_logger = None
get_db = None
jsonify = None
load_settings = None
login_required = None
parse_printer_config = None
request = None
save_settings = None
send_file = None
session = None


TIMELAPSE_DIR = None
TIMELAPSE_MAX_FRAMES = 6000

TIMELAPSE_MIN_FRAMES = 10
TIMELAPSE_LOST_GRACE_S = 180   # imprimante injoignable : on garde la capture ouverte ce temps-là avant d'assembler

_TL_STATE = {}   # printer_id -> {dir, frames, started, file, last_capture, user_id, name}

def _timelapse_interval():
    try:
        v = int((load_settings() or {}).get('timelapse_interval', 30))
    except (TypeError, ValueError):
        v = 30
    return max(5, min(300, v))

def _extract_jpeg(data):
    if not data:
        return None
    s = data.find(b'\xff\xd8')
    if s == -1:
        return None
    e = data.rfind(b'\xff\xd9')
    return bytes(data[s:e + 2]) if e > s else None

def _grab_mjpeg_frame(url, timeout=10):
    """Première image JPEG d'un flux MJPEG http(s), lue directement (sans ffmpeg) ; None si le flux ne répond pas."""
    deadline = time.time() + timeout
    try:
        with requests.get(url, stream=True, timeout=(4, 6)) as r:
            if r.status_code != 200:
                return None
            buf = b''
            for chunk in r.iter_content(4096):
                if not chunk:
                    break
                buf += chunk
                s = buf.find(b'\xff\xd8')
                if s != -1:
                    e = buf.find(b'\xff\xd9', s + 2)
                    if e != -1:
                        return bytes(buf[s:e + 2])
                if len(buf) > 4_000_000 or time.time() > deadline:
                    break
    except Exception:
        return None
    return None

def _timelapse_grab_frame(printer):
    """Une image JPEG de la caméra de l'imprimante (octets) ou None."""
    pid = printer.get('id')
    ptype = printer.get('type')
    cfg = printer.get('config') or {}
    ip = printer.get('ip')
    if ptype == 'bambu':
        code = cfg.get('code') or printer.get('api_key') or ''
        if not code or not ip:
            return None
        model = (cfg.get('model') or 'A1').upper()
        gen = _generate_bambu_rtsp_mjpeg_stream(ip, code) if model in BAMBU_RTSP_PORT322_MODELS else _generate_bambu_mjpeg_stream(ip, code)
        try:
            return _extract_jpeg(next(gen, None))
        finally:
            try:
                gen.close()
            except Exception:
                pass
    if ptype == 'bambuddy':
        try:
            r = _bambuddy_get(ip, printer.get('api_key'), cfg, f"/printers/{_bambuddy_printer_id(cfg)}/camera/snapshot", timeout=8)
            return _extract_jpeg(r.content) if r.status_code == 200 else None
        except Exception:
            return None
    cam = _resolve_printer_camera(printer, pid, '')
    if not cam.get('available'):
        return None
    snap = cam.get('snapshot_url')
    stream = cam.get('stream_url')
    candidates = []
    if snap:
        candidates.append(snap)
    if stream and 'action=stream' in stream:          # mjpg-streamer / crowsnest : l'instantané se déduit du flux
        candidates.append(stream.replace('action=stream', 'action=snapshot'))
    for url in dict.fromkeys(candidates):
        try:
            r = requests.get(url, timeout=6)
            if r.status_code == 200:
                jpg = _extract_jpeg(r.content)
                if jpg:
                    return jpg
        except Exception:
            pass
    if stream and re.match(r'^https?://', stream):    # flux MJPEG lu directement : fonctionne même sans ffmpeg
        jpg = _grab_mjpeg_frame(stream)
        if jpg:
            return jpg
    if stream and FFMPEG_TOOL:
        try:
            out = subprocess.run(
                [FFMPEG_TOOL, '-loglevel', 'error', '-i', stream, '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'mjpeg', 'pipe:1'],
                capture_output=True, timeout=20, **_popen_kwargs_silent())
            return _extract_jpeg(out.stdout)
        except Exception:
            return None
    return None

def _timelapse_safe_name(text):
    return re.sub(r'[^\w\-]+', '_', os.path.splitext(str(text or 'impression'))[0])[:60] or 'impression'

def _timelapse_assemble(state):
    """Assemble les images en MP4 puis supprime les images ; enregistre le résultat en base."""
    frames_dir, n = state['dir'], state['frames']
    try:
        if n < TIMELAPSE_MIN_FRAMES or not FFMPEG_TOOL:
            if n >= TIMELAPSE_MIN_FRAMES:
                app_logger.warning("[Timelapse] ffmpeg introuvable : vidéo non générée")
            else:
                app_logger.info(f"[Timelapse] {n} image(s) seulement (minimum {TIMELAPSE_MIN_FRAMES}) : pas de vidéo")
            return
        out_dir = os.path.join(TIMELAPSE_DIR, str(state['printer_id']))
        os.makedirs(out_dir, exist_ok=True)
        stamp = datetime.datetime.fromtimestamp(state['started']).strftime('%Y%m%d_%H%M%S')
        out_path = os.path.join(out_dir, f"{stamp}_{_timelapse_safe_name(state['file'])}.mp4")
        cmd = [FFMPEG_TOOL, '-y', '-loglevel', 'error', '-framerate', '30', '-i', os.path.join(frames_dir, 'frame_%06d.jpg'),
               '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23',
               '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out_path]
        res = subprocess.run(cmd, capture_output=True, timeout=1800, **_popen_kwargs_silent())
        if res.returncode != 0 or not os.path.isfile(out_path):
            app_logger.warning(f"[Timelapse] Assemblage échoué: {(res.stderr or b'')[-300:]!r}")
            return
        _ensure_v086_tables()
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO timelapses (user_id, printer_id, printer_name, file_name, started_at, frames, duration_s, size, path) VALUES (?,?,?,?,?,?,?,?,?)",
                (state['user_id'], state['printer_id'], state['name'], state['file'],
                 datetime.datetime.fromtimestamp(state['started']).strftime('%Y-%m-%d %H:%M:%S'),
                 n, n / 30.0, os.path.getsize(out_path), out_path))
            conn.commit()
        finally:
            conn.close()
        app_logger.info(f"[Timelapse] Vidéo créée : {out_path} ({n} images)")
    except Exception as e:
        app_logger.warning(f"[Timelapse] Erreur assemblage: {e}")
    finally:
        shutil.rmtree(frames_dir, ignore_errors=True)

def _timelapse_tick():
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM printers").fetchall()
    finally:
        conn.close()
    interval = _timelapse_interval()
    now = time.time()
    active_ids = set()
    for row in rows:
        printer = parse_printer_config(row)
        if not (printer.get('config') or {}).get('timelapse'):
            continue
        pid = printer['id']
        active_ids.add(pid)
        st = _TL_STATE.get(pid)
        if st and now - st['last_poll'] < (interval if st.get('printing') else 15):
            continue
        status = _printer_status_cached(printer, ttl=2.0)
        phase = status.get('status')
        if st:
            st['last_poll'] = now
        if st and phase in ('offline', 'timeout', None, 'unknown', 'unavailable'):
            # micro-coupure réseau : on ne ferme pas la capture (sinon la vidéo est hachée en morceaux trop courts, jetés)
            st['lost_since'] = st.get('lost_since') or now
            if now - st['lost_since'] < TIMELAPSE_LOST_GRACE_S:
                continue
        if phase in ('printing', 'paused'):
            if not st:
                d = os.path.join(TIMELAPSE_DIR, f"tmp_{pid}")
                shutil.rmtree(d, ignore_errors=True)
                os.makedirs(d, exist_ok=True)
                st = _TL_STATE[pid] = {'dir': d, 'frames': 0, 'started': now, 'file': str(status.get('file') or ''),
                                       'last_poll': 0, 'printing': True, 'user_id': printer.get('user_id'),
                                       'printer_id': pid, 'name': printer.get('name') or ''}
                app_logger.info(f"[Timelapse] Début de capture : {printer.get('name')}")
            st['printing'] = True
            st['lost_since'] = None
            if status.get('file'):
                st['file'] = str(status.get('file'))
            if phase == 'printing' and st['frames'] < TIMELAPSE_MAX_FRAMES and now - st['last_poll'] >= 0:
                jpg = _timelapse_grab_frame(printer)
                if jpg:
                    st['frames'] += 1
                    st['grab_fail'] = 0
                    with open(os.path.join(st['dir'], f"frame_{st['frames']:06d}.jpg"), 'wb') as f:
                        f.write(jpg)
                else:
                    st['grab_fail'] = st.get('grab_fail', 0) + 1
                    if st['grab_fail'] == 3:
                        app_logger.warning(f"[Timelapse] {printer.get('name')} : aucune image reçue de la caméra (3 essais de suite)")
            st['last_poll'] = time.time()
        elif st:
            _TL_STATE.pop(pid, None)
            threading.Thread(target=_timelapse_assemble, args=(st,), daemon=True, name='stellio-timelapse-encode').start()
    # imprimante dont le timelapse a été désactivé pendant une capture : on assemble ce qu'on a
    for pid in list(_TL_STATE.keys()):
        if pid not in active_ids:
            st = _TL_STATE.pop(pid)
            threading.Thread(target=_timelapse_assemble, args=(st,), daemon=True).start()

def _timelapse_loop():
    os.makedirs(TIMELAPSE_DIR, exist_ok=True)
    time.sleep(20)
    while True:
        try:
            _timelapse_tick()
        except Exception as e:
            app_logger.info(f"[Timelapse] Erreur boucle: {e}")
        time.sleep(3)

def _start_timelapse_worker():
    _ensure_v086_tables()
    threading.Thread(target=_timelapse_loop, daemon=True, name='stellio-timelapse').start()

def api_list_timelapses():
    _ensure_v086_tables()
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, printer_id, printer_name, file_name, started_at, ended_at, frames, duration_s, size FROM timelapses WHERE user_id=? ORDER BY id DESC LIMIT 200",
            (session['user_id'],)).fetchall()
    finally:
        conn.close()
    recording = [{"printer_id": v['printer_id'], "printer_name": v['name'], "file": v['file'], "frames": v['frames']}
                 for v in list(_TL_STATE.values()) if v.get('user_id') == session['user_id']]
    return jsonify({"timelapses": [dict(r) for r in rows], "recording": recording,
                    "interval": _timelapse_interval(), "ffmpeg": bool(FFMPEG_TOOL)})

def _timelapse_row(tid):
    _ensure_v086_tables()
    conn = get_db()
    try:
        return conn.execute("SELECT * FROM timelapses WHERE id=? AND user_id=?", (tid, session['user_id'])).fetchone()
    finally:
        conn.close()

def api_timelapse_video(tid):
    row = _timelapse_row(tid)
    if not row or not os.path.isfile(row['path']):
        return jsonify({"error": "Introuvable"}), 404
    return send_file(row['path'], mimetype='video/mp4', conditional=True,
                     as_attachment=request.args.get('download') == '1',
                     download_name=os.path.basename(row['path']))

def api_delete_timelapse(tid):
    row = _timelapse_row(tid)
    if not row:
        return jsonify({"error": "Introuvable"}), 404
    try:
        if os.path.isfile(row['path']):
            os.remove(row['path'])
    except Exception as e:
        app_logger.info(f"[Timelapse] Suppression fichier impossible: {e}")
    conn = get_db()
    try:
        conn.execute("DELETE FROM timelapses WHERE id=? AND user_id=?", (tid, session['user_id']))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"message": "Supprimé"})

def api_timelapse_settings():
    data = request.json or {}
    try:
        iv = max(5, min(300, int(data.get('interval', 30))))
    except (TypeError, ValueError):
        return jsonify({"error": "Intervalle invalide"}), 400
    settings = load_settings() or {}
    settings['timelapse_interval'] = iv
    save_settings(settings)
    return jsonify({"interval": iv})


_ROUTES = (
    ('/api/timelapses', ['GET'], 'api_list_timelapses', ('login_required', )),
    ('/api/timelapses/<int:tid>/video', ['GET'], 'api_timelapse_video', ('login_required', )),
    ('/api/timelapses/<int:tid>', ['DELETE'], 'api_delete_timelapse', ('login_required', )),
    ('/api/timelapse/settings', ['PUT'], 'api_timelapse_settings', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"timelapse.init : services manquants : {missing}")
    for n in _REQUIRED + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    g['TIMELAPSE_DIR'] = os.path.join(DATA_DIR, 'timelapse')
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {'TIMELAPSE_DIR': g['TIMELAPSE_DIR']}
