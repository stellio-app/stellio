"""Stellio — imprimantes résine (v1.1.4)

Trois types de plus, tous en lecture seule (suivi), 
  • `formlabs`        : Formlabs Form 3 / 3L / 4 via l'API web officielle (https://api.formlabs.com/developer/v1/ ; OAuth « client
                        credentials »). Champ « Clé API » = « client_id:client_secret » ; configuration facultative `slug` = numéro de
                        série ou alias de l'imprimante (à défaut : la première). Pas d'envoi de fichier : Formlabs passe par PreForm.
  • `anycubic_photon` : anciens Photon Wi-Fi (Mono X, Mono X 6K, Mono SQ…) : commandes texte sur TCP 6000 (`getstatus`, `sysinfo`).
                        Le format exact des réponses n'est pas documenté publiquement : l'analyse est tolérante (état + fichier) et
                        n'invente ni progression ni durée. Les Photon récents (M5s, M7…) utilisent un « mode LAN » MQTT signé : non géré.
  • `chitu_sdcp`      : Phrozen, Uniformation (GKtwo), Elegoo et autres cartes Chitubox en SDCP v3 : réutilise le code SDCP d'Elegoo
                        (main.py), ce module n'en fait que l'alias.
Les analyseurs (`formlabs_normalize`, `photon_parse_status`) sont purs. Jamais de lancement ni d'arrêt d'impression.
Module séparé de main.py (même schéma que printers_extra.py) ; main.py appelle `resin_printers.init(globals())` puis
`resin_printers.connect / status`.
"""
import re
import socket
import threading
import time

_REQUIRED = ('app_logger',)
_OPTIONAL = ()
_OVERRIDABLE = ('time',)

_MAIN = {}
app_logger = None

RESIN_TYPES = ('formlabs', 'anycubic_photon', 'chitu_sdcp')
SDCP_TYPES = ('elegoo_sdcp', 'chitu_sdcp')
FORMLABS_API = 'https://api.formlabs.com/developer/v1'
PHOTON_PORT = 6000
EMPTY_TEMPS = {'extruder': {'current': 0, 'target': 0}, 'bed': {'current': 0, 'target': 0}, 'chamber': {'current': 0, 'target': 0}}


def _num(v, default=0.0):
    try:
        f = float(v)
        return f if f == f else default
    except (TypeError, ValueError):
        return default


def _base_result():
    return {'status': 'unknown', 'progress': 0.0, 'file': '', 'temps': {k: dict(v) for k, v in EMPTY_TEMPS.items()},
            'time': {'elapsed': 0, 'remaining': 0, 'total': 0}, 'layers': {'current': 0, 'total': 0}, 'ams': [],
            'last_print': {'filename': '', 'duration': 0, 'finished_at': ''}}


# ── Formlabs (API web) ──────────────────────────────────────────────────────
_TOKENS = {}                      # client_id -> (jeton, expiration)
_TOKENS_LOCK = threading.Lock()
_RUN_STATES = {'PRINTING': 'printing', 'PREPRINT': 'printing', 'PREHEAT': 'printing', 'PRECOAT': 'printing', 'POSTCOAT': 'printing',
               'QUEUED': 'printing', 'PAUSING': 'paused', 'PAUSED': 'paused', 'WAITING_FOR_RESOLUTION': 'paused',
               'ERROR': 'error', 'ABORTING': 'idle', 'ABORTED': 'idle', 'FINISHED': 'idle'}


def split_credentials(api_key):
    """« client_id:client_secret » -> (id, secret) ; ('', '') si le format est mauvais."""
    a, _, b = str(api_key or '').strip().partition(':')
    return (a.strip(), b.strip()) if a.strip() and b.strip() else ('', '')


def formlabs_token(api_key, timeout=8, force=False):
    import requests
    cid, secret = split_credentials(api_key)
    if not cid:
        raise RuntimeError('unauthorized')
    with _TOKENS_LOCK:
        tok = _TOKENS.get(cid)
        if tok and tok[1] > time.time() + 60 and not force:
            return tok[0]
    try:
        r = requests.post(FORMLABS_API + '/o/token/', data={'grant_type': 'client_credentials', 'client_id': cid, 'client_secret': secret}, timeout=timeout)
    except requests.exceptions.RequestException:
        raise RuntimeError('unreachable')
    if r.status_code in (400, 401, 403):
        raise RuntimeError('unauthorized')
    if r.status_code != 200:
        raise RuntimeError('error')
    d = r.json() if r.content else {}
    token = d.get('access_token')
    if not token:
        raise RuntimeError('error')
    with _TOKENS_LOCK:
        _TOKENS[cid] = (token, time.time() + min(int(_num(d.get('expires_in'), 3600)), 86400))
    return token


def formlabs_list(api_key, timeout=8):
    import requests
    for attempt in (0, 1):
        token = formlabs_token(api_key, timeout, force=bool(attempt))
        try:
            r = requests.get(FORMLABS_API + '/printers/', headers={'Authorization': 'bearer ' + token}, timeout=timeout)
        except requests.exceptions.RequestException:
            raise RuntimeError('unreachable')
        if r.status_code == 401 and not attempt:
            continue                                   # jeton périmé : on le redemande une fois
        if r.status_code in (401, 403):
            raise RuntimeError('unauthorized')
        if r.status_code != 200:
            raise RuntimeError('error')
        data = r.json()
        return data if isinstance(data, list) else (data.get('results') if isinstance(data, dict) else []) or []
    raise RuntimeError('error')


def formlabs_pick(printers, wanted=''):
    wanted = (wanted or '').strip().lower()
    items = [p for p in printers if isinstance(p, dict)]
    for p in items:
        if wanted and wanted in (str(p.get('serial') or '').lower(), str(p.get('alias') or '').lower()):
            return p
    return None if wanted else (items[0] if items else None)


def formlabs_normalize(p):
    """Objet imprimante de l'API Formlabs -> état Stellio. Tolère les champs absents."""
    out = _base_result()
    p = p if isinstance(p, dict) else {}
    ps = p.get('printer_status') if isinstance(p.get('printer_status'), dict) else {}
    run = ps.get('current_print_run') if isinstance(ps.get('current_print_run'), dict) else None
    raw = str(ps.get('status') or '').upper()
    if 'OFFLINE' in raw:
        out['status'] = 'offline'
    elif run and str(run.get('status') or '').upper() in _RUN_STATES:
        out['status'] = _RUN_STATES[str(run.get('status')).upper()]
    elif 'ERROR' in raw:
        out['status'] = 'error'
    elif 'PRINT' in raw:
        out['status'] = 'printing'
    elif 'PAUS' in raw:
        out['status'] = 'paused'
    else:
        out['status'] = 'idle'
    if run and out['status'] in ('printing', 'paused'):
        cur, tot = int(_num(run.get('currently_printing_layer'))), int(_num(run.get('layer_count')))
        elapsed, est, left = _num(run.get('elapsed_duration_ms')) / 1000, _num(run.get('estimated_duration_ms')) / 1000, _num(run.get('estimated_time_remaining_ms')) / 1000
        if not left and est > elapsed:
            left = est - elapsed
        out['file'] = str(run.get('name') or '')
        out['layers'] = {'current': cur, 'total': tot}
        out['progress'] = round(min(100.0, cur / tot * 100.0), 1) if tot > 0 else (round(min(100.0, elapsed / est * 100.0), 1) if est > 0 else 0.0)
        out['time'] = {'elapsed': int(elapsed), 'remaining': int(left), 'total': int(elapsed + left)}
    temp = ps.get('current_temperature')
    if isinstance(temp, (int, float)):
        out['temps']['chamber']['current'] = round(float(temp), 1)
    prev = p.get('previous_print_run') if isinstance(p.get('previous_print_run'), dict) else None
    if prev:
        out['last_print'] = {'filename': str(prev.get('name') or ''), 'duration': int(_num(prev.get('elapsed_duration_ms')) / 1000),
                             'finished_at': str(prev.get('print_finished_at') or '')}
    return out


# ── Anycubic Photon (TCP 6000) ──────────────────────────────────────────────
_PHOTON_LOCK = threading.Lock()
_FILE_RE = re.compile(r'\.(pwmx|pwmb|pwms|pwma|pwmo|pws|pw0|pwx|photon|photons|pm3|pm3m|pm3r|pwc|dlp)$', re.I)


def photon_command(ip, cmd, timeout=4):
    """Une commande texte (« getstatus,end ») ; renvoie la réponse (texte). Port 6000 : un seul client à la fois, on referme après."""
    with _PHOTON_LOCK:
        try:
            s = socket.create_connection((ip, PHOTON_PORT), timeout=timeout)
        except OSError:
            raise RuntimeError('unreachable')
        try:
            s.settimeout(timeout)
            s.sendall(cmd.encode('ascii'))
            buf = b''
            while len(buf) < 4096:
                try:
                    chunk = s.recv(1024)
                except socket.timeout:
                    break
                if not chunk:
                    break
                buf += chunk
                if buf.rstrip().endswith(b'end'):
                    break
            return buf.decode('utf-8', 'replace').strip()
        except OSError:
            raise RuntimeError('unreachable')
        finally:
            try:
                s.close()
            except OSError:
                pass


def photon_parse_status(text):
    """« getstatus,<état>,<fichier>,…,end » -> état Stellio (état + fichier seulement : la signification des autres champs n'est pas publique)."""
    out = _base_result()
    parts = [x.strip() for x in str(text or '').split(',')]
    if not parts or parts[0].lower() != 'getstatus':
        out['status'] = 'unknown'
        return out
    state = (parts[1] if len(parts) > 1 else '').lower()
    if state in ('stop', 'stopped', 'idle', 'finish', 'finished', 'ready', 'standby', ''):
        out['status'] = 'idle'
    elif 'pause' in state:
        out['status'] = 'paused'
    elif state.startswith('print') or state in ('start', 'running', 'busy'):
        out['status'] = 'printing'
    elif 'err' in state or 'fail' in state:
        out['status'] = 'error'
    else:
        out['status'] = 'idle'
    if out['status'] in ('printing', 'paused'):
        out['file'] = next((x for x in parts[2:] if _FILE_RE.search(x)), '') or (parts[2] if len(parts) > 2 and parts[2] and parts[2].lower() != 'end' else '')
    return out


# ── point d'entrée pour main.py ─────────────────────────────────────────────
def connect(ptype, ip, api_key, config):
    try:
        if ptype == 'formlabs':
            return formlabs_pick(formlabs_list(api_key, 6), (config or {}).get('slug')) is not None
        if ptype == 'anycubic_photon':
            return photon_command(ip, 'getstatus,end', 4).lower().startswith('getstatus')
    except Exception as e:
        if app_logger:
            app_logger.info(f"[Printer] {ptype} connexion : {e}")
    return False


def status(ptype, ip, api_key, config):
    """État normalisé ; lève RuntimeError('unreachable' | 'unauthorized'…) (main.py la traduit en offline / error)."""
    if ptype == 'formlabs':
        p = formlabs_pick(formlabs_list(api_key, 6), (config or {}).get('slug'))
        if p is None:
            raise RuntimeError('error')
        return formlabs_normalize(p)
    return photon_parse_status(photon_command(ip, 'getstatus,end', 4))


_ROUTES = ()


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) ; ce module n'ajoute aucune route."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"resin_printers.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    return {}
