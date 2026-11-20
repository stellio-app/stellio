"""Stellio — plugin intégré « Spoolman »

Section Spoolman de l'inventaire des filaments : lecture des bobines d'un serveur Spoolman (réglage `spoolman_url`), découverte automatique sur le
réseau local, reste en grammes par bobine. Le cœur garde l'assignation de bobines et leur historique (colonnes de base inchangées) ;
sans ce plugin, aucune bobine Spoolman n'est lue et la section disparaît de l'interface.
"""
import threading

import requests

_REQUIRED = ('app', 'app_logger', 'get_db', 'get_local_ip', 'jsonify', 'load_settings', 'login_required', 'request', 'save_settings')
_MAIN = {}
app = app_logger = get_db = get_local_ip = jsonify = load_settings = login_required = request = save_settings = None


def api_spoolman_spools():
    url = request.args.get('url', '').rstrip('/')
    if not url:
        return jsonify({"error": "URL manquante"}), 400
    try:
        app_logger.info(f"[Spoolman] GET {url}/api/v1/spool")
        res = requests.get(f"{url}/api/v1/spool", timeout=8, headers={"Accept": "application/json"})
        app_logger.info(f"[Spoolman] Status: {res.status_code}")
        if res.status_code == 404:
            res2 = requests.get(f"{url}/api/spool", timeout=5, headers={"Accept": "application/json"})
            if res2.ok:
                data = res2.json()
                return jsonify(data.get('items', data) if isinstance(data, dict) else data), 200
            return jsonify({"error": f"Endpoint introuvable sur {url}"}), 404
        if not res.ok:
            return jsonify({"error": f"Spoolman a répondu {res.status_code}"}), res.status_code
        data = res.json()
        return jsonify(data.get('items', data) if isinstance(data, dict) and 'items' in data else data), 200
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Connexion refusée — Spoolman démarré sur {url} ?"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": "Timeout"}), 504
    except Exception as e:
        app_logger.error(f"[Spoolman] Erreur: {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500


def remaining_g(source_id, user_id):
    """Poids restant (g) d'une bobine Spoolman déjà assignée, ou None."""
    try:
        conn = get_db()
        row = conn.execute(
            """SELECT spoolman_url FROM filament_assignments
               WHERE source_type='spoolman' AND source_id=? AND user_id=?
               ORDER BY assigned_at DESC LIMIT 1""",
            (str(source_id), user_id)
        ).fetchone()
        conn.close()
        if not row or not row['spoolman_url']:
            return None
        r = requests.get(f"{row['spoolman_url']}/api/v1/spool/{source_id}", timeout=5,
                          headers={"Accept": "application/json"})
        if not r.ok:
            return None
        return r.json().get('remaining_weight')
    except Exception:
        return None


def get_slots(url):
    slots = []
    if not url:
        return slots, None
    try:
        res = requests.get(f"{url}/api/v1/spool", timeout=8, headers={"Accept": "application/json"})
        if not res.ok:
            return slots, f"Spoolman a répondu {res.status_code}"
        data = res.json()
        spools = data.get('items', data) if isinstance(data, dict) and 'items' in data else data
        for s in spools:
            if s.get('archived'):
                continue
            filament = s.get('filament', {}) or {}
            vendor = filament.get('vendor', {}) or {}
            color = filament.get('color_hex')
            price = s.get('price')
            if price is None:
                price = filament.get('price')
            slots.append({
                'source_type': 'spoolman',
                'source_id': str(s.get('id')),
                'name': filament.get('name') or vendor.get('name') or f"Bobine #{s.get('id')}",
                'vendor': vendor.get('name') or '',
                'material': filament.get('material') or '',
                'color_hex': f"#{str(color).replace('#', '')}" if color else '#888888',
                'remaining_g': s.get('remaining_weight'),
                'capacity_g': filament.get('weight') or s.get('initial_weight') or 1000,
                'spoolman_url': url,
                'price': price if isinstance(price, (int, float)) else None,
            })
    except requests.exceptions.ConnectionError:
        return slots, f"Connexion refusée — Spoolman démarré sur {url} ?"
    except Exception as e:
        return slots, str(e)
    return slots, None


def _scan_lan_for_spoolman(timeout=0.35, port=7912, max_parallel=64):
    local_ip = get_local_ip()
    if local_ip == '127.0.0.1' or local_ip.count('.') != 3:
        return None
    prefix = '.'.join(local_ip.split('.')[:3])
    candidates = [f"{prefix}.{i}" for i in range(1, 255)]

    found = {'url': None}
    lock = threading.Lock()

    def _check(ip):
        if found['url']:
            return
        try:
            r = requests.get(f"http://{ip}:{port}/api/v1/info", timeout=timeout)
            if r.ok:
                data = r.json()
                if isinstance(data, dict) and ('version' in data or 'debug_mode' in data):
                    with lock:
                        if not found['url']:
                            found['url'] = f"http://{ip}:{port}"
        except Exception:
            pass

    batch = []
    for ip in candidates:
        if found['url']:
            break
        t = threading.Thread(target=_check, args=(ip,), daemon=True)
        batch.append(t)
        t.start()
        if len(batch) >= max_parallel:
            for th in batch:
                th.join(timeout=timeout + 0.5)
            batch = []
    for th in batch:
        th.join(timeout=timeout + 0.5)

    return found['url']


def api_spoolman_discover():
    settings = load_settings() or {}
    if settings.get('spoolman_url'):
        return jsonify({"found": False, "reason": "already_configured"}), 200
    if settings.get('spoolman_discover_declined'):
        return jsonify({"found": False, "reason": "declined"}), 200
    url = _scan_lan_for_spoolman()
    if url:
        return jsonify({"found": True, "url": url}), 200
    return jsonify({"found": False}), 200


def api_spoolman_discover_decline():
    settings = load_settings() or {}
    settings['spoolman_discover_declined'] = True
    save_settings(settings)
    return jsonify({"ok": True}), 200


_ROUTES = (
    ('/api/spoolman/spools', ['GET'], 'api_spoolman_spools', ('login_required', )),
    ('/api/spoolman/discover', ['GET'], 'api_spoolman_discover', ('login_required', )),
    ('/api/spoolman/discover/decline', ['POST'], 'api_spoolman_discover_decline', ('login_required', )),
)


def init(ns, routes=True):
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"spoolman.init : services manquants : {missing}")
    for n in _REQUIRED:
        g[n] = ns[n]
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {}
