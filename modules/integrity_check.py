"""Stellio — Vérification d'intégrité des fichiers (état, progression, annulation)

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `integrity_check.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import hashlib
import json
import os
import threading
import time

_REQUIRED = (
    'CONVERT_SUPPORTED_FORMATS',
    'DATA_DIR',
    'FIRST_COMPLETED',
    'FuturesTimeoutError',
    'ThreadPoolExecutor',
    '_effective_cpu_count',
    '_load_mesh_for_conversion',
    'app',
    'app_logger',
    'futures_wait',
    'jsonify',
    'load_file_cache',
    'login_required',
    'request',
)
_OPTIONAL = ()   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('hashlib', 'json', 'os', 'threading', 'time', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
CONVERT_SUPPORTED_FORMATS = None
DATA_DIR = None
FIRST_COMPLETED = None
FuturesTimeoutError = None
ThreadPoolExecutor = None
_effective_cpu_count = None
_load_mesh_for_conversion = None
app = None
app_logger = None
futures_wait = None
jsonify = None
load_file_cache = None
login_required = None
request = None


INTEGRITY_CHECK_WORKERS = None
INTEGRITY_REPORT_FILE = None
INTEGRITY_CHECK_BASE_TIMEOUT = 120

INTEGRITY_CHECK_TIMEOUT_PER_MB = 3.0

INTEGRITY_CHECK_TIMEOUT_MAX = 900

INTEGRITY_CHECKSUM_MAX_MB = 64

def get_integrity_timeout(file_path):
    try:
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
    except Exception:
        return INTEGRITY_CHECK_BASE_TIMEOUT
    timeout = INTEGRITY_CHECK_BASE_TIMEOUT + size_mb * INTEGRITY_CHECK_TIMEOUT_PER_MB
    return min(timeout, INTEGRITY_CHECK_TIMEOUT_MAX)

integrity_check_state = {
    'running': False,
    'total': 0,
    'checked': 0,
    'ok': 0,
    'corrupted': 0,
    'empty': 0,
    'missing': 0,
    'started_at': None,
    'finished_at': None,
    'problems': []
}

integrity_check_lock = threading.Lock()

def compute_file_checksum(file_path, algo='sha256'):
    h = hashlib.new(algo)
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def check_single_file_integrity(file_path):
    result = {'path': file_path, 'status': 'ok', 'error': None, 'checksum': None}

    if not os.path.exists(file_path):
        result['status'] = 'missing'
        result['error'] = "Fichier introuvable sur le disque"
        return result

    try:
        size = os.path.getsize(file_path)
    except Exception as e:
        result['status'] = 'corrupted'
        result['error'] = str(e)[:300]
        return result

    if size == 0:
        result['status'] = 'empty'
        result['error'] = "Fichier vide (0 octet)"
        return result

    ext = os.path.splitext(file_path)[1].lower().lstrip('.')
    if ext in CONVERT_SUPPORTED_FORMATS:
        try:
            _load_mesh_for_conversion(file_path)
        except Exception as e:
            result['status'] = 'corrupted'
            result['error'] = str(e)[:300]
            return result
    else:
        try:
            with open(file_path, 'rb') as f:
                f.read(64)
        except Exception as e:
            result['status'] = 'corrupted'
            result['error'] = str(e)[:300]
            return result

    if size <= INTEGRITY_CHECKSUM_MAX_MB * 1024 * 1024:
        try:
            result['checksum'] = compute_file_checksum(file_path)
        except Exception:
            pass
    return result

def _save_integrity_report():
    try:
        with open(INTEGRITY_REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'finished_at': integrity_check_state['finished_at'],
                'total': integrity_check_state['total'],
                'ok': integrity_check_state['ok'],
                'corrupted': integrity_check_state['corrupted'],
                'empty': integrity_check_state['empty'],
                'missing': integrity_check_state['missing'],
                'problems': integrity_check_state['problems']
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        app_logger.warning(f"[INTEGRITY] Échec sauvegarde rapport: {e}")

def _run_integrity_check(paths):
    global integrity_check_state
    with integrity_check_lock:
        integrity_check_state.update({
            'running': True, 'total': len(paths), 'checked': 0,
            'ok': 0, 'corrupted': 0, 'empty': 0, 'missing': 0,
            'started_at': time.time(), 'finished_at': None, 'problems': [], 'cancel': False, 'cancelled': False
        })

    executor = ThreadPoolExecutor(max_workers=INTEGRITY_CHECK_WORKERS)
    paths_iter = iter(paths)
    pending = {}
    started_at = {}
    retry_paths = []

    def _timed_check(p):
        # Le délai ne démarre qu'à la prise en charge réelle par un worker (pas pendant l'attente en file)
        started_at[p] = time.time()
        return check_single_file_integrity(p)

    def _submit_next():
        try:
            p = next(paths_iter)
        except StopIteration:
            return False
        fut = executor.submit(_timed_check, p)
        pending[fut] = p
        return True

    for _ in range(INTEGRITY_CHECK_WORKERS):
        if not _submit_next():
            break

    while pending:
        if integrity_check_state.get('cancel'):
            for _f in list(pending):
                _f.cancel()
            pending.clear()
            retry_paths = []
            break
        done, _ = futures_wait(list(pending.keys()), timeout=1, return_when=FIRST_COMPLETED)
        now = time.time()
        to_process = list(done) + [
            f for f, p in pending.items()
            if f not in done and p in started_at and now >= started_at[p] + get_integrity_timeout(p)
        ]

        for fut in to_process:
            p = pending.pop(fut)
            if fut.done():
                try:
                    result = fut.result()
                except Exception as e:
                    result = {'path': p, 'status': 'corrupted', 'error': str(e)[:300]}
            else:
                # Fichier lent : on ne le déclare pas corrompu, on le retente à la fin, seul, avec un délai triplé
                retry_paths.append(p)
                fut.cancel()
                _submit_next()
                continue

            with integrity_check_lock:
                integrity_check_state['checked'] += 1
                status = result.get('status', 'corrupted')
                if status == 'ok':
                    integrity_check_state['ok'] += 1
                else:
                    integrity_check_state[status] = integrity_check_state.get(status, 0) + 1
                    integrity_check_state['problems'].append({
                        'path': p,
                        'name': os.path.basename(p),
                        'status': status,
                        'error': result.get('error')
                    })
            _submit_next()

    executor.shutdown(wait=False)

    # Seconde chance pour les fichiers lents : un seul à la fois (plus de contention CPU/disque), délai x3
    for p in retry_paths:
        if integrity_check_state.get('cancel'):
            break
        retry_timeout = get_integrity_timeout(p) * 3
        retry_pool = ThreadPoolExecutor(max_workers=1)
        try:
            fut = retry_pool.submit(check_single_file_integrity, p)
            try:
                result = fut.result(timeout=retry_timeout)
            except FuturesTimeoutError:
                result = {'path': p, 'status': 'corrupted',
                          'error': f"Délai dépassé (>{retry_timeout:.0f}s) : fichier très volumineux ou partage réseau trop lent — le fichier n'est pas forcément corrompu"}
            except Exception as e:
                result = {'path': p, 'status': 'corrupted', 'error': str(e)[:300]}
        finally:
            retry_pool.shutdown(wait=False)
        with integrity_check_lock:
            integrity_check_state['checked'] += 1
            status = result.get('status', 'corrupted')
            if status == 'ok':
                integrity_check_state['ok'] += 1
            else:
                integrity_check_state[status] = integrity_check_state.get(status, 0) + 1
                integrity_check_state['problems'].append({
                    'path': p, 'name': os.path.basename(p), 'status': status, 'error': result.get('error')
                })

    with integrity_check_lock:
        integrity_check_state['cancelled'] = bool(integrity_check_state.get('cancel'))
        integrity_check_state['running'] = False
        integrity_check_state['finished_at'] = time.time()
        _save_integrity_report()

    app_logger.info(
        f"[INTEGRITY] Vérification {'annulée' if integrity_check_state['cancelled'] else 'terminée'}: {integrity_check_state['ok']} OK, "
        f"{integrity_check_state['corrupted'] + integrity_check_state['empty']} corrompu(s), "
        f"{integrity_check_state['missing']} manquant(s)"
    )

def api_integrity_check():
    if integrity_check_state['running']:
        return jsonify({"error": "Une vérification est déjà en cours"}), 409

    data = request.json or {}
    paths = data.get('paths')
    if not paths:
        cached = load_file_cache()
        if not cached:
            return jsonify({"error": "Aucun fichier à vérifier. Ouvrez la bibliothèque d'abord."}), 400
        paths = [f['path'] for f in cached if f.get('path')]

    if not isinstance(paths, list) or not paths:
        return jsonify({"error": "Aucun fichier à vérifier"}), 400

    threading.Thread(target=_run_integrity_check, args=(paths,), daemon=True).start()
    app_logger.info(f"[INTEGRITY] 🛡️ Démarrage de la vérification pour {len(paths)} fichier(s)")
    return jsonify({"started": True, "total": len(paths)})

def api_integrity_cancel():
    """Arrête la vérification après les fichiers en cours ; ce qui a déjà été vérifié reste dans le rapport."""
    with integrity_check_lock:
        if integrity_check_state.get('running'):
            integrity_check_state['cancel'] = True
    return jsonify({"success": True})

def api_integrity_progress():
    with integrity_check_lock:
        return jsonify({
            'running': integrity_check_state['running'],
            'cancelled': bool(integrity_check_state.get('cancelled')),
            'total': integrity_check_state['total'],
            'checked': integrity_check_state['checked'],
            'ok': integrity_check_state['ok'],
            'corrupted': integrity_check_state['corrupted'],
            'empty': integrity_check_state['empty'],
            'missing': integrity_check_state['missing'],
            'problems': integrity_check_state['problems']
        })


_ROUTES = (
    ('/api/integrity/check', ['POST'], 'api_integrity_check', ('login_required', )),
    ('/api/integrity/cancel', ['POST'], 'api_integrity_cancel', ('login_required', )),
    ('/api/integrity/progress', ['GET'], 'api_integrity_progress', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"integrity_check.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    g['INTEGRITY_CHECK_WORKERS'] = max(1, min(3, _effective_cpu_count() // 2))
    g['INTEGRITY_REPORT_FILE'] = os.path.join(DATA_DIR, "integrity_report.json")
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {'INTEGRITY_CHECK_WORKERS': g['INTEGRITY_CHECK_WORKERS'], 'INTEGRITY_REPORT_FILE': g['INTEGRITY_REPORT_FILE']}
