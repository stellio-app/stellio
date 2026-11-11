"""Stellio — suivi des sessions d'impression (v1.0.4).

Module séparé de main.py (premier pas vers une architecture modulaire) :
  · prise connectée (Shelly, Tasmota, Home Assistant) → watts en direct, énergie (Wh) et coût réel par impression ;
  · photo de fin d'impression → galerie existante (table print_photos) ;
  · surveillance IA (Ollama de vision, local uniquement) → alerte « échec d'impression possible ».

Un seul « suivi de session d'impression » (_V104_SESS) alimente les trois fonctions.

Branchement : main.py appelle `print_session.init(globals())` une fois toutes ses fonctions définies ;
init() reçoit les services de main.py (base de données, journal, IA, caméra, alertes…), puis enregistre les routes.
Les tests importent ce module directement et lui injectent des faux services (voir tests/test_v104.py).
"""
import base64
import datetime
import io
import os
import re
import threading
import time
import uuid

import requests

# Services fournis par main.py (obligatoires) — voir init().
_REQUIRED = (
    'app', 'jsonify', 'request', 'session', 'login_required', 'get_db', 'app_logger', 'parse_printer_config',
    'load_settings', 'encrypt_password', 'decrypt_password', '_ws_alert', '_server_t', '_visual_call_lock',
    '_visual_ollama_opts', '_visual_local_check', '_timelapse_grab_frame', '_printer_status_cached',
    '_low_memory', '_call_ai', 'AIDisabledError', 'PRINT_PHOTOS_DIR', 'Image',
)
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
app = None
jsonify = None
request = None
session = None
login_required = None
get_db = None
app_logger = None
parse_printer_config = None
load_settings = None
encrypt_password = None
decrypt_password = None
_ws_alert = None
_server_t = None
_visual_call_lock = None
_visual_ollama_opts = None
_visual_local_check = None
_timelapse_grab_frame = None
_printer_status_cached = None
_low_memory = None
_call_ai = None
AIDisabledError = None
PRINT_PHOTOS_DIR = None
Image = None

# Modules standard que les tests peuvent remplacer (faux threads, faux temps…).
_OVERRIDABLE = ('requests', 'threading', 'time', 'io', 'base64', 'uuid', 're', 'json', 'datetime', 'os')

# ══════════════════════════════════════════════════════════════════════════════════════════════
# v1.0.4 — Consommation électrique réelle (prise connectée), photo de fin d'impression, surveillance IA
# Un seul « suivi de session d'impression » (_V104_SESS) alimente les trois fonctions :
#   · prise connectée (Shelly, Tasmota, Home Assistant) → watts en direct, énergie (Wh) et coût réel par impression ;
#   · photo de fin d'impression → galerie existante (table print_photos) ;
#   · surveillance IA (Ollama de vision, local uniquement) → alerte « échec d'impression possible ».
# ══════════════════════════════════════════════════════════════════════════════════════════════
_V104_TABLES_READY = False
_V104_LOCK = threading.Lock()
METER_KINDS = ('shelly', 'tasmota', 'homeassistant')
METER_POLL_PRINTING_S = 10        # lecture de la prise pendant une impression
METER_POLL_IDLE_S = 30            # lecture de la prise hors impression (affichage des watts en direct)
V104_MIN_SESSION_S = 120          # en dessous : annulation / test, rien n'est enregistré
V104_UNKNOWN_GRACE_S = 300        # imprimante injoignable : on garde la session ouverte ce temps-là
AI_WATCH_DEFAULT_MIN = 5          # intervalle de la surveillance IA (réglage ai_watch_interval_min)
_V104_SESS = {}                   # printer_id -> session d'impression en cours
_METER_LIVE = {}                  # printer_id -> dernière lecture de la prise
_METER_FAIL = {}                  # printer_id -> (échecs consécutifs, prochain essai)


def _ensure_v104_tables():
    global _V104_TABLES_READY
    if _V104_TABLES_READY:
        return
    with _V104_LOCK:
        if _V104_TABLES_READY:
            return
        conn = get_db()
        try:
            conn.execute("""CREATE TABLE IF NOT EXISTS print_energy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                printer_id INTEGER,
                printer_name TEXT DEFAULT '',
                file_name TEXT DEFAULT '',
                started_at TIMESTAMP,
                ended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                duration_s REAL DEFAULT 0,
                energy_wh REAL DEFAULT 0,
                avg_w REAL,
                peak_w REAL,
                price_kwh REAL,
                cost REAL,
                measured_by TEXT DEFAULT '',
                history_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )""")
            cols = [r[1] for r in conn.execute("PRAGMA table_info(print_history)").fetchall()]
            if 'energy_wh' not in cols:
                conn.execute("ALTER TABLE print_history ADD COLUMN energy_wh REAL")
            if 'energy_measured' not in cols:
                conn.execute("ALTER TABLE print_history ADD COLUMN energy_measured INTEGER DEFAULT 0")
            conn.commit()
        finally:
            conn.close()
        _V104_TABLES_READY = True


# ── Configuration d'imprimante (prise, photo de fin, surveillance IA) ───────────────────────
def _meter_clean_host(host):
    """Adresse de la prise (IP, nom ou URL http/https) nettoyée ; '' si invalide."""
    h = str(host or '').strip().rstrip('/')
    if not h or len(h) > 200:
        return ''
    scheme = 'http://'
    m = re.match(r'^(https?://)(.*)$', h, re.I)
    if m:
        scheme, h = m.group(1).lower(), m.group(2)
    if not re.fullmatch(r'[A-Za-z0-9.\-_:\[\]]+(/[A-Za-z0-9.\-_/]*)?', h):
        return ''
    if h.startswith('169.254.'):          # adresses « link-local » (métadonnées cloud) : jamais
        return ''
    return scheme + h


def _v104_clean_config(incoming, old=None):
    """Clés ajoutées à la config d'une imprimante : end_photo, ai_watch, meter {kind, host, entity, energy_entity, channel, token_enc}."""
    out = {}
    inc = incoming if isinstance(incoming, dict) else {}
    old = old if isinstance(old, dict) else {}
    if inc.get('end_photo'):
        out['end_photo'] = True
    if inc.get('ai_watch'):
        out['ai_watch'] = True
    m = inc.get('meter')
    om = old.get('meter') if isinstance(old.get('meter'), dict) else {}
    if isinstance(m, dict) and m.get('kind') in METER_KINDS:
        host = _meter_clean_host(m.get('host'))
        if host:
            meter = {'kind': m['kind'], 'host': host}
            for key in ('entity', 'energy_entity'):
                ent = str(m.get(key) or '').strip()
                if re.fullmatch(r'[A-Za-z0-9_]+\.[A-Za-z0-9_]+', ent):
                    meter[key] = ent
            try:
                ch = int(m.get('channel') or 0)
            except (TypeError, ValueError):
                ch = 0
            meter['channel'] = ch if 0 <= ch <= 7 else 0
            tok = str(m.get('token') or '').strip()
            if tok:
                meter['token_enc'] = encrypt_password(tok)
            elif om.get('token_enc') and not m.get('clear_token'):
                meter['token_enc'] = om['token_enc']
            out['meter'] = meter
    return out


def _v104_apply_config(raw_config, incoming, old=None):
    """Remplace dans raw_config les clés v1.0.4 par leur version nettoyée (le jeton n'est jamais stocké en clair)."""
    for k in ('end_photo', 'ai_watch', 'meter'):
        raw_config.pop(k, None)
    raw_config.update(_v104_clean_config(incoming, old))
    return raw_config


def _v104_public_config(cfg):
    """Config renvoyée au navigateur : le jeton chiffré est remplacé par has_token."""
    if isinstance(cfg, dict) and isinstance(cfg.get('meter'), dict):
        m = dict(cfg['meter'])
        m['has_token'] = bool(m.pop('token_enc', None))
        cfg = dict(cfg)
        cfg['meter'] = m
    return cfg


# ── Lecture des prises connectées ───────────────────────────────────────────────────────────
def _meter_token(meter):
    enc = (meter or {}).get('token_enc')
    return (decrypt_password(enc) or '') if enc else ''


def _meter_read(meter, timeout=4):
    """Lit la prise : {'power_w': float|None, 'energy_wh': float|None}. Lève une exception si injoignable."""
    kind = meter.get('kind')
    base = meter.get('host') or ''
    ch = int(meter.get('channel') or 0)
    if kind == 'shelly':
        # Gen2 / Gen3 / Plus : RPC
        for path in (f"/rpc/Switch.GetStatus?id={ch}", f"/rpc/PM1.GetStatus?id={ch}", f"/rpc/EM1.GetStatus?id={ch}"):
            r = requests.get(base + path, timeout=timeout)
            if r.status_code == 200:
                j = r.json()
                p = j.get('apower', j.get('act_power'))
                en = (j.get('aenergy') or {}).get('total', j.get('total_act_energy'))
                if p is not None:
                    return {'power_w': float(p), 'energy_wh': float(en) if en is not None else None}
            elif r.status_code in (401, 403):
                raise PermissionError('auth')
        # Gen1 (Plug S, 1PM…) : /status, total en watt-minutes
        r = requests.get(base + '/status', timeout=timeout)
        r.raise_for_status()
        meters = r.json().get('meters') or []
        if ch >= len(meters):
            raise ValueError('no_meter')
        mt = meters[ch]
        tot = mt.get('total')
        return {'power_w': float(mt.get('power') or 0), 'energy_wh': float(tot) / 60.0 if tot is not None else None}
    if kind == 'tasmota':
        r = requests.get(base + '/cm', params={'cmnd': 'Status 8'}, timeout=timeout)
        r.raise_for_status()
        e = ((r.json().get('StatusSNS') or {}).get('ENERGY')) or {}
        if 'Power' not in e:
            raise ValueError('no_energy')
        pw = e['Power']
        if isinstance(pw, list):
            pw = pw[ch] if ch < len(pw) else pw[0]
        total = e.get('Total')
        if isinstance(total, list):
            total = total[0] if total else None
        return {'power_w': float(pw), 'energy_wh': float(total) * 1000.0 if total is not None else None}
    if kind == 'homeassistant':
        tok = _meter_token(meter)
        if not tok:
            raise PermissionError('auth')
        headers = {'Authorization': f'Bearer {tok}'}
        out = {'power_w': None, 'energy_wh': None}

        def _state(entity):
            rr = requests.get(f"{base}/api/states/{entity}", headers=headers, timeout=timeout)
            if rr.status_code in (401, 403):
                raise PermissionError('auth')
            rr.raise_for_status()
            js = rr.json()
            st = js.get('state')
            if st in (None, '', 'unknown', 'unavailable'):
                raise ValueError('unavailable')
            return float(st), str((js.get('attributes') or {}).get('unit_of_measurement') or '').strip()

        def _to_w(v, u):
            return v * 1000.0 if u == 'kW' else (v / 1000.0 if u == 'mW' else v)

        def _to_wh(v, u):
            return v * 1000.0 if u == 'kWh' else (v * 1000000.0 if u == 'MWh' else v)

        if meter.get('entity'):
            v, u = _state(meter['entity'])
            if u in ('kWh', 'Wh', 'MWh'):
                out['energy_wh'] = _to_wh(v, u)
            else:
                out['power_w'] = _to_w(v, u)
        if meter.get('energy_entity'):
            v, u = _state(meter['energy_entity'])
            out['energy_wh'] = _to_wh(v, u)
        if out['power_w'] is None and out['energy_wh'] is None:
            raise ValueError('no_entity')
        return out
    raise ValueError('kind')


def _v104_poll_meter(pid, meter, now, force=False):
    """Lit la prise d'une imprimante en tenant compte des échecs (on espace les essais) ; met à jour _METER_LIVE."""
    nfail, nxt = _METER_FAIL.get(pid, (0, 0))
    if now < nxt and not force:
        return _METER_LIVE.get(pid)
    try:
        d = _meter_read(meter)
        live = {'power_w': d.get('power_w'), 'energy_wh': d.get('energy_wh'), 'ts': now, 'ok': True}
        _METER_FAIL.pop(pid, None)
    except Exception as e:
        nfail += 1
        _METER_FAIL[pid] = (nfail, now + (0 if nfail < 3 else 60))
        live = {'power_w': None, 'energy_wh': None, 'ts': now, 'ok': False, 'err': (str(e) or type(e).__name__)[:120]}
    _METER_LIVE[pid] = live
    return live


# ── Rapprochement avec l'historique d'impression ────────────────────────────────────────────
def _v104_stem(name):
    s = os.path.basename(str(name or '').replace('\\', '/')).lower()
    for _ in range(3):
        for ext in ('.gcode', '.3mf', '.bgcode', '.ufp', '.gco', '.g'):
            if s.endswith(ext):
                s = s[:-len(ext)]
    return s.strip()


def _v104_find_history(conn, user_id, printer_id, file_name):
    """Dernière ligne d'historique (72 h) dont le nom correspond au fichier imprimé : (id, file_path, material_cost) ou None."""
    stem = _v104_stem(file_name)
    if not stem:
        return None
    rows = conn.execute(
        """SELECT id, file_path, file_name, material_cost, COALESCE(energy_measured, 0) AS em FROM print_history
           WHERE user_id=? AND sent_at >= datetime('now', '-3 days') AND (printer_id IS NULL OR printer_id=?)
           ORDER BY sent_at DESC LIMIT 80""", (user_id, printer_id)).fetchall()
    for r in rows:
        if r['em']:
            continue
        if _v104_stem(r['file_name']) == stem or _v104_stem(r['file_path']) == stem:
            return r
    return None


# ── Enregistrement de l'énergie d'une impression ────────────────────────────────────────────
def _v104_record_energy(sess, energy_wh, by, duration_s):
    _ensure_v104_tables()
    settings = load_settings() or {}
    try:
        price = float(settings.get('print_cost_elec_price') or 0)
    except (TypeError, ValueError):
        price = 0.0
    kwh = energy_wh / 1000.0
    cost = round(kwh * price, 4) if price > 0 else None
    hours = duration_s / 3600.0 if duration_s else 0
    avg_w = round(energy_wh / hours, 1) if hours > 0 else None
    conn = get_db()
    try:
        hist = _v104_find_history(conn, sess['user_id'], sess['printer_id'], sess['file'])
        hist_id = hist['id'] if hist else None
        conn.execute(
            """INSERT INTO print_energy (user_id, printer_id, printer_name, file_name, started_at, duration_s, energy_wh,
                                         avg_w, peak_w, price_kwh, cost, measured_by, history_id)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (sess['user_id'], sess['printer_id'], sess['name'], sess['file'],
             datetime.datetime.fromtimestamp(sess['start']).strftime('%Y-%m-%d %H:%M:%S'),
             round(duration_s, 1), round(energy_wh, 2), avg_w, round(sess.get('peak') or 0, 1) or None,
             price or None, cost, by, hist_id))
        if hist:
            if cost is not None:
                conn.execute("UPDATE print_history SET energy_wh=?, energy_measured=1, elec_cost=?, total_cost=? WHERE id=?",
                             (round(energy_wh, 2), cost, round((hist['material_cost'] or 0) + cost, 4), hist['id']))
            else:
                conn.execute("UPDATE print_history SET energy_wh=?, energy_measured=1 WHERE id=?",
                             (round(energy_wh, 2), hist['id']))
        conn.commit()
    finally:
        conn.close()
    app_logger.info(f"[Énergie] {sess['name']} : {energy_wh / 1000.0:.3f} kWh en {duration_s / 60:.0f} min ({by})")
    return {'energy_wh': energy_wh, 'cost': cost, 'history_id': hist_id}


def _measured_avg_power_w(printer_id, days=90):
    """Puissance moyenne réellement mesurée (W) sur les impressions récentes de cette imprimante ; None s'il y en a trop peu."""
    try:
        _ensure_v104_tables()
        conn = get_db()
        try:
            r = conn.execute(
                """SELECT COUNT(*) AS n, SUM(energy_wh) AS wh, SUM(duration_s) AS s FROM print_energy
                   WHERE printer_id=? AND duration_s >= 900 AND energy_wh > 0 AND ended_at >= datetime('now', ?)""",
                (printer_id, f'-{int(days)} days')).fetchone()
        finally:
            conn.close()
        if not r or not r['n'] or not r['s'] or (r['n'] < 2 and r['s'] < 3600):
            return None
        return round(r['wh'] / (r['s'] / 3600.0), 1)
    except Exception:
        return None


# ── Photo de fin d'impression ───────────────────────────────────────────────────────────────
def _v104_jpeg_b64(jpg, max_side=640):
    """Image JPEG réduite (pour le modèle de vision) en base64."""
    img = Image.open(io.BytesIO(jpg)).convert('RGB')
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=72)
    return base64.b64encode(buf.getvalue()).decode('ascii')


def _v104_save_photo(user_id, printer_id, file_name, jpg, result, note):
    """Range une photo dans la galerie existante (print_photos), rattachée au fichier de la bibliothèque si on le retrouve."""
    img = Image.open(io.BytesIO(jpg)).convert('RGB')
    img.thumbnail((1600, 1600))
    fname = f"{uuid.uuid4().hex}.jpg"
    img.save(os.path.join(PRINT_PHOTOS_DIR, fname), 'JPEG', quality=85, optimize=True)
    conn = get_db()
    try:
        hist = None
        try:
            hist = _v104_find_history(conn, user_id, printer_id, file_name)
        except Exception:
            hist = None
        file_path = (hist['file_path'] if hist else '') or f"printer/{printer_id}/{file_name or 'impression'}"
        conn.execute("INSERT INTO print_photos (user_id, file_path, image_filename, note, result) VALUES (?,?,?,?,?)",
                     (user_id, str(file_path).replace('\\', '/'), fname, (note or '')[:300], result))
        conn.commit()
    finally:
        conn.close()


# ── Surveillance IA des échecs ──────────────────────────────────────────────────────────────
_V104_AI_SYSTEM = "You are a careful 3D printing monitor. You only answer with one line of JSON."
_V104_AI_PROMPT = (
    "This image comes from the camera of an FDM 3D printer that is currently printing (about {progress}% done). "
    "Decide whether the print has FAILED. Failure signs: spaghetti (loose tangled filament), the part detached from "
    "the bed or knocked over, a big blob of filament stuck to the nozzle, the print floating in the air, or an empty "
    "bed although a print should be running. Small stringing, minor surface flaws, a part partly hidden by the "
    "toolhead, or a dark/blurry image are NOT failures (answer unsure for an unusable image). "
    'Reply with ONE line of strict JSON and nothing else: {{"verdict":"ok" or "failed" or "unsure","reason":"max 12 words"}}'
)


def _v104_parse_verdict(text):
    """('ok'|'failed'|'unsure', raison) à partir de la réponse du modèle ; 'unsure' si illisible."""
    t = str(text or '')
    m = re.search(r'"verdict"\s*:\s*"(ok|failed|unsure)"', t, re.I)
    if not m:
        m2 = re.search(r'\b(failed|unsure|ok)\b', t, re.I)
        if not m2:
            return 'unsure', ''
        verdict = m2.group(1).lower()
    else:
        verdict = m.group(1).lower()
    r = re.search(r'"reason"\s*:\s*"([^"]{0,160})"', t)
    return verdict, (r.group(1).strip() if r else '')


def _v104_ai_interval_s():
    try:
        v = float((load_settings() or {}).get('ai_watch_interval_min', AI_WATCH_DEFAULT_MIN))
    except (TypeError, ValueError):
        v = AI_WATCH_DEFAULT_MIN
    return int(max(2, min(30, v)) * 60)


def _v104_ai_check(printer, sess, status, now):
    """Une analyse de l'image de la caméra. Alerte après DEUX « failed » consécutifs (2e vérification 60 s plus tard)."""
    interval = _v104_ai_interval_s()
    sess['ai_next'] = now + interval
    if _visual_local_check():             # IA coupée ou fournisseur en ligne : les images ne quittent jamais la machine
        sess['ai_next'] = now + 3600
        return
    if _low_memory():
        sess['ai_next'] = now + 120
        return
    jpg = _timelapse_grab_frame(printer)
    if not jpg:
        return
    try:
        b64 = _v104_jpeg_b64(jpg)
    except Exception:
        return
    try:
        progress = int(float(status.get('progress') or 0))
    except (TypeError, ValueError):
        progress = 0
    if not _visual_call_lock.acquire(timeout=2):
        sess['ai_next'] = now + 60
        return
    try:
        text, source = _call_ai(_V104_AI_PROMPT.format(progress=progress), system=_V104_AI_SYSTEM, num_predict=60,
                                temperature=0.1, images=[b64], extra_options=_visual_ollama_opts('gentle'), keep_alive='60s')
    except AIDisabledError:
        sess['ai_next'] = now + 3600
        return
    except Exception as e:
        app_logger.info(f"[Surveillance IA] {printer.get('name')} : {str(e)[:120]}")
        return
    finally:
        _visual_call_lock.release()
    uid, name = sess['user_id'], sess['name']
    if source == 'ollama_no_vision':
        sess['ai_next'] = now + 24 * 3600
        _ws_alert(uid, 'info', _server_t('notif.ai_watch_novision_title', 'Surveillance IA indisponible'),
                  _server_t('notif.ai_watch_novision_msg', "Le modèle Ollama choisi ne sait pas lire les images : choisissez un modèle de vision dans Paramètres > IA."),
                  f"ai_watch_novision_{datetime.date.today().isoformat()}")
        return
    verdict, reason = _v104_parse_verdict(text)
    if verdict == 'failed':
        sess['ai_fail'] += 1
        sess['ai_next'] = now + 60
        if sess['ai_fail'] >= 2 and not sess['ai_alerted']:
            sess['ai_alerted'] = True
            sess['ai_reason'] = reason
            sess['ai_next'] = now + interval * 2
            _ws_alert(uid, 'print_failed', _server_t('notif.ai_failure_title', "Échec d'impression possible"),
                      f"{name} — {sess['file'] or '?'}" + (f" · {reason}" if reason else ''),
                      f"print_failed_ai_{sess['printer_id']}_{int(sess['start'])}")
            try:
                _v104_save_photo(uid, sess['printer_id'], sess['file'], jpg, 'failed',
                                 _server_t('photo.ai_failure_note', 'Détection IA') + (f" : {reason}" if reason else ''))
            except Exception as e:
                app_logger.info(f"[Surveillance IA] photo non enregistrée : {e}")
    else:
        sess['ai_fail'] = 0


# ── Suivi de session d'impression ───────────────────────────────────────────────────────────
def _v104_new_session(printer, status, now):
    return {'printer_id': printer['id'], 'user_id': printer.get('user_id'), 'name': printer.get('name') or '',
            'file': str(status.get('file') or ''), 'start': now, 'last_ts': now, 'last_w': None, 'wh': 0.0, 'peak': 0.0,
            'samples': 0, 'cnt_start': None, 'next_meter': 0, 'ai_next': now + 120, 'ai_fail': 0, 'ai_alerted': False,
            'ai_reason': '', 'unknown_since': None, 'error_since': None, 'rest_since': None}


def _v104_sample(pid, meter, sess, now):
    live = _v104_poll_meter(pid, meter, now)
    if not live or not live.get('ok'):
        return
    if sess['cnt_start'] is None and live.get('energy_wh') is not None:
        sess['cnt_start'] = live['energy_wh']
    w = live.get('power_w')
    if w is not None:
        if sess['last_w'] is not None:
            dt = max(0.0, min(now - sess['last_ts'], 60.0))
            sess['wh'] += (sess['last_w'] + w) / 2.0 * dt / 3600.0
        sess['last_w'], sess['last_ts'] = w, now
        sess['peak'] = max(sess['peak'], w)
        sess['samples'] += 1


def _v104_finish(printer, sess, end_phase, end_ts):
    """Fin d'une impression (dans un thread) : énergie mesurée, photo de fin."""
    cfg = printer.get('config') or {}
    pid = printer['id']
    dur = max(0.0, end_ts - sess['start'])
    if dur < V104_MIN_SESSION_S:
        return
    failed = bool(sess['ai_alerted']) or end_phase == 'error'
    try:
        meter = cfg.get('meter') if isinstance(cfg.get('meter'), dict) and cfg['meter'].get('kind') in METER_KINDS else None
        if meter:
            energy, by = None, ''
            final = _v104_poll_meter(pid, meter, time.time(), force=True)
            if final and final.get('ok') and final.get('energy_wh') is not None and sess['cnt_start'] is not None \
                    and final['energy_wh'] >= sess['cnt_start']:
                energy, by = final['energy_wh'] - sess['cnt_start'], 'counter'
            elif sess['samples'] >= 3:
                energy, by = sess['wh'], 'samples'
            if energy is not None and energy >= 1.0:
                _v104_record_energy(sess, energy, by, dur)
    except Exception as e:
        app_logger.warning(f"[Énergie] enregistrement impossible : {e}")
    try:
        if cfg.get('end_photo'):
            jpg = _timelapse_grab_frame(printer)
            if jpg:
                note = _server_t('photo.auto_end', "Photo automatique de fin d'impression") + f" · {sess['name']}"
                _v104_save_photo(sess['user_id'], pid, sess['file'], jpg, 'failed' if failed else 'success', note)
                app_logger.info(f"[Photo de fin] {sess['name']} : photo enregistrée")
    except Exception as e:
        app_logger.warning(f"[Photo de fin] échec : {e}")


def _v104_step(printer, status, now):
    cfg = printer.get('config') or {}
    pid = printer['id']
    meter = cfg.get('meter') if isinstance(cfg.get('meter'), dict) and cfg['meter'].get('kind') in METER_KINDS else None
    want_photo, want_ai = bool(cfg.get('end_photo')), bool(cfg.get('ai_watch'))
    phase = status.get('status')
    sess = _V104_SESS.get(pid)
    active = phase in ('printing', 'paused')
    unknown = phase in ('offline', 'timeout', None, 'unknown', 'unavailable')

    if active and not sess and (meter or want_photo or want_ai):
        sess = _V104_SESS[pid] = _v104_new_session(printer, status, now)
    if sess:
        if status.get('file'):
            sess['file'] = str(status.get('file'))
        if active:
            sess['unknown_since'] = sess['error_since'] = sess['rest_since'] = None
        elif unknown:
            sess['unknown_since'] = sess['unknown_since'] or now
        elif phase == 'error':
            sess['error_since'] = sess['error_since'] or now
        else:
            sess['rest_since'] = sess['rest_since'] or now

        done = False
        if not active and not unknown and phase != 'error' and now - (sess['rest_since'] or now) >= 15:
            done = True                                      # au repos depuis 15 s (anti-parasite) : impression terminée
        elif phase == 'error' and now - (sess['error_since'] or now) >= 20:
            done = True
        elif unknown and now - (sess['unknown_since'] or now) >= V104_UNKNOWN_GRACE_S:
            done = True
        if done:
            _V104_SESS.pop(pid, None)
            threading.Thread(target=_v104_finish, args=(printer, sess, phase, now), daemon=True,
                             name='stellio-print-finish').start()
            sess = None

    if sess:
        if meter and now >= sess['next_meter']:
            sess['next_meter'] = now + METER_POLL_PRINTING_S
            _v104_sample(pid, meter, sess, now)
        if want_ai and phase == 'printing' and now >= sess['ai_next']:
            try:
                progress = float(status.get('progress') or 0)
            except (TypeError, ValueError):
                progress = 0.0
            if progress >= 2:
                _v104_ai_check(printer, sess, status, now)
            else:
                sess['ai_next'] = now + 60
    elif meter:                                               # hors impression : watts en direct (carte de l'imprimante)
        last = _METER_LIVE.get(pid)
        if not last or now - last['ts'] >= METER_POLL_IDLE_S:
            _v104_poll_meter(pid, meter, now)
    if not meter:
        _METER_LIVE.pop(pid, None)


def _v104_tick():
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM printers").fetchall()
    finally:
        conn.close()
    now = time.time()
    seen = set()
    for row in rows:
        printer = parse_printer_config(row)
        cfg = printer.get('config') or {}
        pid = printer['id']
        seen.add(pid)
        if not (cfg.get('meter') or cfg.get('end_photo') or cfg.get('ai_watch') or pid in _V104_SESS):
            continue
        status = _printer_status_cached(printer, ttl=3.0)
        _v104_step(printer, status, now)
    for pid in list(_V104_SESS.keys()):                      # imprimante supprimée pendant une impression
        if pid not in seen:
            _V104_SESS.pop(pid, None)


def _v104_loop():
    time.sleep(25)
    try:
        _ensure_v104_tables()
    except Exception as e:
        app_logger.warning(f"[v1.0.4] tables : {e}")
    while True:
        try:
            _v104_tick()
        except Exception as e:
            app_logger.info(f"[v1.0.4] Erreur boucle: {e}")
        time.sleep(5)


def _start_v104_worker():
    _ensure_v104_tables()
    threading.Thread(target=_v104_loop, daemon=True, name='stellio-print-sessions').start()


# ── Routes : prise connectée, énergie ───────────────────────────────────────────────────────
def _v104_user_printer(pid):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM printers WHERE id=? AND user_id=?", (pid, session['user_id'])).fetchone()
    finally:
        conn.close()
    return parse_printer_config(row) if row else None


def api_printer_meter_test(pid):
    """Teste une prise (réglages envoyés par le formulaire ; le jeton déjà enregistré est réutilisé s'il est laissé vide)."""
    data = request.json or {}
    old_cfg = {}
    if pid:
        p = _v104_user_printer(pid)
        if not p:
            return jsonify({"error": "Imprimante introuvable"}), 404
        old_cfg = p.get('config') or {}
    cfg = _v104_clean_config({'meter': data.get('meter')}, old_cfg)
    meter = cfg.get('meter')
    if not meter:
        return jsonify({"ok": False, "error": "config"}), 200
    try:
        d = _meter_read(meter, timeout=5)
        return jsonify({"ok": True, "power_w": d.get('power_w'), "energy_wh": d.get('energy_wh')})
    except PermissionError:
        return jsonify({"ok": False, "error": "auth"})
    except requests.exceptions.Timeout:
        return jsonify({"ok": False, "error": "timeout"})
    except requests.exceptions.RequestException:
        return jsonify({"ok": False, "error": "unreachable"})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)[:40] or "invalid"})
    except Exception as e:
        app_logger.info(f"[Énergie] test prise : {e}")
        return jsonify({"ok": False, "error": "invalid"})


def api_printers_meters_live():
    """Watts en direct de toutes les prises de l'utilisateur : {printer_id: {power_w, ts, ok}} (dernière lecture du suivi)."""
    conn = get_db()
    try:
        ids = [r['id'] for r in conn.execute("SELECT id FROM printers WHERE user_id=?", (session['user_id'],)).fetchall()]
    finally:
        conn.close()
    now = time.time()
    out = {}
    for pid in ids:
        live = _METER_LIVE.get(pid)
        if live and now - live['ts'] < 180:
            out[str(pid)] = {"power_w": live.get('power_w'), "ok": bool(live.get('ok')),
                             "age": int(now - live['ts']), "printing": pid in _V104_SESS}
    return jsonify(out)


def api_energy_summary():
    _ensure_v104_tables()
    try:
        days = max(1, min(365, int(request.args.get('days', 30))))
    except (TypeError, ValueError):
        days = 30
    uid = session['user_id']
    conn = get_db()
    try:
        tot = conn.execute(
            """SELECT COUNT(*) AS n, COALESCE(SUM(energy_wh),0) AS wh, COALESCE(SUM(cost),0) AS cost, COALESCE(SUM(duration_s),0) AS s
               FROM print_energy WHERE user_id=? AND ended_at >= datetime('now', ?)""", (uid, f'-{days} days')).fetchone()
        per = conn.execute(
            """SELECT printer_id, MAX(printer_name) AS name, COUNT(*) AS n, SUM(energy_wh) AS wh, SUM(cost) AS cost, SUM(duration_s) AS s
               FROM print_energy WHERE user_id=? AND ended_at >= datetime('now', ?) GROUP BY printer_id ORDER BY wh DESC""",
            (uid, f'-{days} days')).fetchall()
        sess = conn.execute(
            """SELECT id, printer_id, printer_name, file_name, started_at, ended_at, duration_s, energy_wh, avg_w, peak_w, cost, measured_by
               FROM print_energy WHERE user_id=? ORDER BY id DESC LIMIT 40""", (uid,)).fetchall()
    finally:
        conn.close()
    printers = []
    for r in per:
        pw = _measured_avg_power_w(r['printer_id']) if r['printer_id'] else None
        printers.append({"printer_id": r['printer_id'], "name": r['name'], "sessions": r['n'],
                         "kwh": round((r['wh'] or 0) / 1000.0, 3), "cost": round(r['cost'] or 0, 2),
                         "hours": round((r['s'] or 0) / 3600.0, 1), "avg_w": pw})
    return jsonify({
        "days": days, "sessions": tot['n'], "kwh": round(tot['wh'] / 1000.0, 3), "cost": round(tot['cost'], 2),
        "hours": round(tot['s'] / 3600.0, 1), "printers": printers,
        "recent": [dict(r) for r in sess],
    })


def api_energy_session_delete(sid):
    _ensure_v104_tables()
    conn = get_db()
    try:
        conn.execute("DELETE FROM print_energy WHERE id=? AND user_id=?", (sid, session['user_id']))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True})


_ROUTES = (
    ('/api/printers/<int:pid>/meter/test', ['POST'], 'api_printer_meter_test', ('login_required',)),
    ('/api/printers/meters/live', ['GET'], 'api_printers_meters_live', ('login_required',)),
    ('/api/energy/summary', ['GET'], 'api_energy_summary', ('login_required',)),
    ('/api/energy/sessions/<int:sid>', ['DELETE'], 'api_energy_session_delete', ('login_required',)),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"print_session.init : services manquants : {missing}")
    for n in _REQUIRED + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
