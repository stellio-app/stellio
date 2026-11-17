"""Stellio — imprimantes Duet (RepRapFirmware) et Repetier-Server (v1.1.3)

Deux types d'imprimantes de plus, en réseau, en lecture (état, températures, progression, durées) et envoi de fichier :
  • `duet`     : Duet 2 / 3 / Mini 5+ sous RepRapFirmware 3 (mode autonome : /rr_connect + /rr_model ; mode SBC avec
                 Duet Software Framework : /machine/status). Le mot de passe de la carte (s'il y en a un) se saisit dans le champ
                 « Clé API » ; sans mot de passe laisser vide. Envoi : /rr_upload ou /machine/file/gcodes.
  • `repetier` : Repetier-Server (port 3344 par défaut), clé API de l'utilisateur dans « Clé API », nom court (slug) de
                 l'imprimante dans la configuration (à défaut : la première imprimante en ligne). Envoi : /printer/model/<slug>?a=upload
                 (le fichier arrive dans les modèles de Repetier-Server ; Stellio ne lance jamais l'impression).
Marlin en direct par câble USB n'est pas géré (le port série est exclusif ; passer par OctoPrint ou Repetier-Server).

Les analyseurs (`duet_normalize`, `repetier_normalize`) sont purs et tolèrent les champs manquants (versions différentes).
Module séparé de main.py (même schéma que trash_routes.py) ; main.py appelle `printers_extra.init(globals())` puis utilise
`printers_extra.connect / status / upload`.
"""
import os
import time

_REQUIRED = ('app_logger',)
_OPTIONAL = ()
_OVERRIDABLE = ('os', 'time')

_MAIN = {}
app_logger = None

DUET_DEFAULT_PORT = 80
REPETIER_DEFAULT_PORT = 3344
EMPTY_TEMPS = {'extruder': {'current': 0, 'target': 0}, 'bed': {'current': 0, 'target': 0}, 'chamber': {'current': 0, 'target': 0}}

_DUET_STATES = {
    'idle': 'idle', 'processing': 'printing', 'simulating': 'printing', 'resuming': 'printing', 'changingtool': 'printing',
    'paused': 'paused', 'pausing': 'paused', 'cancelling': 'idle',
    'halted': 'error', 'off': 'offline', 'busy': 'busy', 'updating': 'busy', 'starting': 'busy',
}


def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _round1(v):
    return round(_num(v), 1)


# ───────────────────────────── Duet ─────────────────────────────
def _heater(model, idx):
    heaters = ((model.get('heat') or {}).get('heaters')) or []
    try:
        h = heaters[int(idx)]
    except (TypeError, ValueError, IndexError):
        return {'current': 0, 'target': 0}
    if not isinstance(h, dict):
        return {'current': 0, 'target': 0}
    return {'current': _round1(h.get('current')), 'target': _round1(h.get('active'))}


def duet_normalize(model, last_print=None):
    """Objet-modèle RepRapFirmware (/rr_model result ou /machine/status) -> état Stellio."""
    model = model if isinstance(model, dict) else {}
    state = model.get('state') if isinstance(model.get('state'), dict) else {}
    raw = str(state.get('status') or '').lower()
    status = _DUET_STATES.get(raw, raw or 'unknown')
    job = model.get('job') if isinstance(model.get('job'), dict) else {}
    jfile = job.get('file') if isinstance(job.get('file'), dict) else {}
    fname = os.path.basename(str(jfile.get('fileName') or '').replace('\\', '/'))
    size = _num(jfile.get('size'))
    pos = _num(job.get('filePosition'))
    progress = round(min(100.0, pos / size * 100.0), 1) if size > 0 and status in ('printing', 'paused') else 0.0
    elapsed = int(_num(job.get('duration')))
    left_raw = (job.get('timesLeft') or {}) if isinstance(job.get('timesLeft'), dict) else {}
    left = left_raw.get('file')
    if left is None:
        left = left_raw.get('filament')
    left = int(_num(left)) if left is not None else 0
    if not left and progress > 1 and elapsed:
        left = int(elapsed * (100.0 - progress) / progress)
    temps = {k: dict(v) for k, v in EMPTY_TEMPS.items()}
    heat = model.get('heat') if isinstance(model.get('heat'), dict) else {}
    beds = heat.get('bedHeaters') or []
    bed_idx = next((i for i in beds if isinstance(i, int) and i >= 0), None)
    if bed_idx is not None:
        temps['bed'] = _heater(model, bed_idx)
    chambers = heat.get('chamberHeaters') or []
    ch_idx = next((i for i in chambers if isinstance(i, int) and i >= 0), None)
    if ch_idx is not None:
        temps['chamber'] = _heater(model, ch_idx)
    tools = model.get('tools') or []
    for t in tools:
        hs = (t or {}).get('heaters') or [] if isinstance(t, dict) else []
        if hs:
            temps['extruder'] = _heater(model, hs[0])
            break
    return {'status': status, 'progress': progress, 'file': fname, 'temps': temps,
            'time': {'elapsed': elapsed, 'remaining': left, 'total': elapsed + left if (elapsed or left) else 0},
            'last_print': last_print or {'filename': os.path.basename(str(job.get('lastFileName') or '')), 'duration': int(_num(job.get('lastDuration'))), 'finished_at': ''}}


def _duet_open(base, password, timeout=5):
    """(session HTTP, mode, en-têtes) ; mode « rrf » (autonome) ou « sbc ». Lève RuntimeError('unauthorized' | 'unreachable')."""
    import requests
    s = requests.Session()
    pw = password or ''
    try:
        r = s.get(f"{base}/rr_connect", params={'password': pw or 'reprap', 'time': time.strftime('%Y-%m-%dT%H:%M:%S')}, timeout=timeout)
        if r.status_code == 200:
            j = r.json() if r.content else {}
            if j.get('err', 0) == 0:
                key = j.get('sessionKey')
                return s, 'rrf', ({'X-Session-Key': str(key)} if key is not None else {})
            if j.get('err') in (1, 2):
                raise RuntimeError('unauthorized')
        # 404 / pas de rr_connect : mode SBC
        r = s.get(f"{base}/machine/connect", params={'password': pw}, timeout=timeout)
        if r.status_code == 200:
            key = (r.json() or {}).get('sessionKey')
            return s, 'sbc', ({'X-Session-Key': str(key)} if key else {})
        if r.status_code in (401, 403):
            raise RuntimeError('unauthorized')
        if r.status_code == 404:                       # DSF sans mot de passe : /machine/status direct
            return s, 'sbc', {}
    except requests.RequestException:
        raise RuntimeError('unreachable')
    except ValueError:
        raise RuntimeError('bad_response')
    raise RuntimeError('unreachable')


def duet_model(base, password, timeout=5):
    s, mode, hdr = _duet_open(base, password, timeout)
    import requests
    try:
        if mode == 'rrf':
            r = s.get(f"{base}/rr_model", params={'flags': 'd99f'}, headers=hdr, timeout=timeout)
            r.raise_for_status()
            j = r.json()
            return j.get('result', j)
        r = s.get(f"{base}/machine/status", headers=hdr, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        raise RuntimeError('unreachable')
    finally:
        _duet_close(s, base, mode, hdr)


def _duet_close(s, base, mode, hdr):
    try:
        s.get(f"{base}/rr_disconnect" if mode == 'rrf' else f"{base}/machine/disconnect", headers=hdr, timeout=2)
    except Exception:
        pass


def duet_upload(base, password, file_path, timeout=120):
    import requests
    s, mode, hdr = _duet_open(base, password)
    name = os.path.basename(file_path)
    try:
        with open(file_path, 'rb') as f:
            if mode == 'rrf':
                r = s.post(f"{base}/rr_upload", params={'name': f"0:/gcodes/{name}", 'time': time.strftime('%Y-%m-%dT%H:%M:%S')},
                           data=f, headers=hdr, timeout=timeout)
                return r.status_code == 200 and (r.json() or {}).get('err', 1) == 0
            r = s.put(f"{base}/machine/file/gcodes/{name}", data=f, headers=hdr, timeout=timeout)
            return r.status_code in (200, 201)
    finally:
        _duet_close(s, base, mode, hdr)


# ───────────────────────── Repetier-Server ─────────────────────────
def _rep_headers(api_key):
    return {'x-api-key': api_key} if api_key else {}


def repetier_list(base, api_key, timeout=5):
    """Imprimantes déclarées dans Repetier-Server : [{slug, name, online, job}]."""
    import requests
    try:
        r = requests.get(f"{base}/printer/api/", params={'a': 'listPrinter'}, headers=_rep_headers(api_key), timeout=timeout)
    except requests.RequestException:
        raise RuntimeError('unreachable')
    if r.status_code in (401, 403):
        raise RuntimeError('unauthorized')
    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        raise RuntimeError('bad_response')
    items = j.get('data') if isinstance(j, dict) and 'data' in j else j
    return [{'slug': str(p.get('slug') or ''), 'name': str(p.get('name') or ''), 'online': bool(p.get('online')), 'job': str(p.get('job') or ''),
             'paused': bool(p.get('paused')), 'done': p.get('done')}
            for p in (items or []) if isinstance(p, dict) and p.get('slug')]


def repetier_pick_slug(printers, wanted=''):
    wanted = (wanted or '').strip()
    for p in printers:
        if wanted and wanted.lower() in (p['slug'].lower(), p['name'].lower()):
            return p['slug']
    if wanted:
        return None
    online = [p for p in printers if p['online']]
    return (online or printers or [{}])[0].get('slug')


def _rep_temp(v):
    if isinstance(v, list):
        v = v[0] if v else {}
    v = v if isinstance(v, dict) else {}
    return {'current': _round1(v.get('tempRead')), 'target': _round1(v.get('tempSet'))}


def repetier_normalize(state, entry=None):
    """stateList (dict de l'imprimante, ou {slug: dict}) + entrée listPrinter -> état Stellio."""
    state = state if isinstance(state, dict) else {}
    if state and 'extruder' not in state and 'heatedBed' not in state and len(state) == 1:
        inner = next(iter(state.values()))
        if isinstance(inner, dict):
            state = inner
    entry = entry if isinstance(entry, dict) else {}
    job = str(entry.get('job') or state.get('job') or '')
    printing = job.lower() not in ('', 'none')
    paused = bool(entry.get('paused') or state.get('paused'))
    if entry and not entry.get('online', True):
        status = 'offline'
    elif paused and printing:
        status = 'paused'
    elif printing:
        status = 'printing'
    else:
        status = 'idle'
    progress = None
    for src in (state, entry):
        if src.get('done') is not None:
            progress = _num(src.get('done'))
            break
    if progress is None and _num(state.get('totalLines')) > 0:
        progress = _num(state.get('linesSent')) / _num(state.get('totalLines')) * 100.0
    if progress is None and _num(state.get('ofLayer')) > 0:
        progress = _num(state.get('layer')) / _num(state.get('ofLayer')) * 100.0
    progress = round(max(0.0, min(100.0, progress or 0.0)), 1) if printing else 0.0
    temps = {'extruder': _rep_temp(state.get('extruder')), 'bed': _rep_temp(state.get('heatedBed')), 'chamber': _rep_temp(state.get('heatedChamber'))}
    elapsed = int(_num(state.get('printTime') or state.get('printedTimeComp')))
    left = int(_num(state.get('printTimeLeft') or state.get('remainingTime')))
    return {'status': status, 'progress': progress, 'file': job if printing else '', 'temps': temps,
            'time': {'elapsed': elapsed, 'remaining': left, 'total': elapsed + left if (elapsed or left) else 0},
            'last_print': {'filename': '', 'duration': 0, 'finished_at': ''}}


def repetier_status(base, api_key, slug_wanted='', timeout=5):
    import requests
    plist = repetier_list(base, api_key, timeout)
    slug = repetier_pick_slug(plist, slug_wanted)
    if not slug:
        raise RuntimeError('printer_not_found')
    entry = next((p for p in plist if p['slug'] == slug), {})
    try:
        r = requests.get(f"{base}/printer/api/{slug}", params={'a': 'stateList'}, headers=_rep_headers(api_key), timeout=timeout)
        r.raise_for_status()
        j = r.json()
    except (requests.RequestException, ValueError):
        raise RuntimeError('unreachable')
    j = j.get('data') if isinstance(j, dict) and isinstance(j.get('data'), dict) else j
    return repetier_normalize(j.get(slug) if isinstance(j, dict) and isinstance(j.get(slug), dict) else j, entry)


def repetier_upload(base, api_key, file_path, slug_wanted='', timeout=120):
    import requests
    slug = repetier_pick_slug(repetier_list(base, api_key), slug_wanted)
    if not slug:
        return False
    with open(file_path, 'rb') as f:
        r = requests.post(f"{base}/printer/model/{slug}", params={'a': 'upload', 'name': os.path.basename(file_path), 'group': 'Stellio', 'overwrite': 'true'},
                          files={'filename': (os.path.basename(file_path), f, 'application/octet-stream')}, headers=_rep_headers(api_key), timeout=timeout)
    return r.status_code == 200


# ───────────────────── points d'entrée pour main.py ─────────────────────
def connect(ptype, base, api_key, config):
    try:
        if ptype == 'duet':
            duet_model(base, api_key, 4)
            return True
        plist = repetier_list(base, api_key, 4)
        return repetier_pick_slug(plist, (config or {}).get('slug')) is not None
    except Exception as e:
        if app_logger:
            app_logger.info(f"[Printer] {ptype} connexion : {e}")
        return False


def status(ptype, base, api_key, config):
    """État normalisé ; lève RuntimeError('unreachable' | 'unauthorized'…) (main.py la traduit en offline / error)."""
    if ptype == 'duet':
        return duet_normalize(duet_model(base, api_key, 4))
    return repetier_status(base, api_key, (config or {}).get('slug'), 4)


def upload(ptype, base, api_key, config, file_path):
    try:
        if ptype == 'duet':
            return bool(duet_upload(base, api_key, file_path))
        return bool(repetier_upload(base, api_key, file_path, (config or {}).get('slug')))
    except Exception as e:
        if app_logger:
            app_logger.info(f"[Printer Upload] {ptype} : {e}")
        return False


_ROUTES = ()


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) ; ce module n'ajoute aucune route."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"printers_extra.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    return {}
