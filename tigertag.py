"""Stellio — inventaire TigerTag (session Firebase, références, étiquettes)

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `tigertag.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import requests
import threading
import time

_REQUIRED = (
    'app_logger',
    'decrypt_account_secret',
    'encrypt_password',
    'get_db',
)
_OPTIONAL = ()   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('requests', 'threading', 'time', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
app_logger = None
decrypt_account_secret = None
encrypt_password = None
get_db = None


TIGERTAG_FIREBASE_CONFIG_URL  = "https://tigertag-cdn.web.app/__/firebase/init.json"

TIGERTAG_FIREBASE_REFRESH_URL = "https://securetoken.googleapis.com/v1/token"

TIGERTAG_FIREBASE_LOOKUP_URL  = "https://identitytoolkit.googleapis.com/v1/accounts:lookup"

TIGERTAG_FIRESTORE_BASE_URL   = "https://firestore.googleapis.com/v1"

TIGERTAG_REFERENCES_BASE_URL  = "https://api.tigertag.io/api:tigertag"

TIGERTAG_REFERENCES_TTL       = 86400  

_tigertag_token_cache = {}

_tigertag_token_cache_lock = threading.Lock()

_tigertag_firebase_config = {}

_tigertag_references_cache = {"data": None, "fetched_at": 0}

def _tigertag_fs_value(field):
    for ftype in ('stringValue', 'integerValue', 'doubleValue', 'booleanValue'):
        if ftype in field:
            val = field[ftype]
            if ftype in ('integerValue', 'doubleValue'):
                try:
                    return int(val) if ftype == 'integerValue' else float(val)
                except (TypeError, ValueError):
                    return val
            return val
    if 'nullValue' in field:
        return None
    if 'mapValue' in field:
        return {k: _tigertag_fs_value(v) for k, v in field['mapValue'].get('fields', {}).items()}
    if 'arrayValue' in field:
        return [_tigertag_fs_value(v) for v in field['arrayValue'].get('values', [])]
    if 'timestampValue' in field:
        return field['timestampValue']
    return None

def _tigertag_parse_doc(doc):
    return {k: _tigertag_fs_value(v) for k, v in doc.get('fields', {}).items()}

def _tigertag_ensure_firebase_config():
    if _tigertag_firebase_config.get('project_id') and _tigertag_firebase_config.get('api_key'):
        return
    resp = requests.get(TIGERTAG_FIREBASE_CONFIG_URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    _tigertag_firebase_config['project_id'] = data.get('projectId', '')
    _tigertag_firebase_config['api_key'] = data.get('apiKey', '')

def _tigertag_refresh_id_token(refresh_token):
    _tigertag_ensure_firebase_config()
    url = f"{TIGERTAG_FIREBASE_REFRESH_URL}?key={_tigertag_firebase_config['api_key']}"
    resp = requests.post(url, json={
        "grant_type": "refresh_token", "refresh_token": refresh_token,
    }, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if 'id_token' not in data:
        raise ValueError("Refresh token TigerTag invalide")
    expires_at = time.time() + 3600
    return data['id_token'], data['refresh_token'], expires_at, data.get('user_id')

def _tigertag_get_valid_session(user_id):
    with _tigertag_token_cache_lock:
        cached = _tigertag_token_cache.get(user_id)

    if cached and time.time() < cached['expires_at'] - 300:
        return cached['id_token'], cached['firebase_uid']

    if cached and cached.get('refresh_token'):
        try:
            id_token, refresh_token, expires_at, refreshed_uid = _tigertag_refresh_id_token(cached['refresh_token'])
            firebase_uid = refreshed_uid or cached['firebase_uid']
            with _tigertag_token_cache_lock:
                _tigertag_token_cache[user_id] = {
                    'id_token': id_token, 'refresh_token': refresh_token,
                    'firebase_uid': firebase_uid, 'expires_at': expires_at,
                }
            _tigertag_persist_refresh_token(user_id, refresh_token)
            return id_token, firebase_uid
        except Exception as e:
            app_logger.warning(f"[TigerTag] Refresh token échoué (user {user_id}), ré-authentification: {e}")

    conn = get_db()
    try:
        account = conn.execute(
            "SELECT email, password_encrypted, api_key FROM account_credentials WHERE user_id = ? AND platform = 'tigertag'",
            (user_id,)
        ).fetchone()
    finally:
        conn.close()

    if not account or not account['api_key']:
        raise ValueError("Compte TigerTag non configuré — relance la détection TigerTag Studio")

    refresh_token = decrypt_account_secret(account['api_key'])
    id_token, new_refresh_token, expires_at, firebase_uid = _tigertag_refresh_id_token(refresh_token)
    if not firebase_uid:
        raise ValueError("Session TigerTag Studio invalide, relance la détection")
    with _tigertag_token_cache_lock:
        _tigertag_token_cache[user_id] = {
            'id_token': id_token, 'refresh_token': new_refresh_token,
            'firebase_uid': firebase_uid, 'expires_at': expires_at,
        }
    _tigertag_persist_refresh_token(user_id, new_refresh_token)
    return id_token, firebase_uid

def _tigertag_persist_refresh_token(user_id, refresh_token):
    try:
        conn = get_db()
        try:
            conn.execute(
                "UPDATE account_credentials SET api_key = ? WHERE user_id = ? AND platform = 'tigertag' AND api_key IS NOT NULL",
                (encrypt_password(refresh_token), user_id)
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        app_logger.warning(f"[TigerTag] Échec persistance refresh_token Google (user {user_id}): {e}")

def _tigertag_get_references():
    if _tigertag_references_cache['data'] and (time.time() - _tigertag_references_cache['fetched_at'] < TIGERTAG_REFERENCES_TTL):
        return _tigertag_references_cache['data']

    endpoints = {
        'material': f"{TIGERTAG_REFERENCES_BASE_URL}/material/filament/get/all",
        'brand': f"{TIGERTAG_REFERENCES_BASE_URL}/brand/get/all",
    }
    references = {}
    for key, url in endpoints.items():
        try:
            resp = requests.get(url, timeout=10)
            references[key] = resp.json() if resp.ok else None
        except Exception as e:
            app_logger.warning(f"[TigerTag] Référence '{key}' non récupérée: {e}")
            references[key] = None

    _tigertag_references_cache['data'] = references
    _tigertag_references_cache['fetched_at'] = time.time()
    return references

def _tigertag_resolve_reference(references, ref_type, item_id):
    if not item_id:
        return ''
    refs = references.get(ref_type)
    if not refs:
        return str(item_id)
    target = str(item_id)
    if isinstance(refs, list):
        for item in refs:
            if str(item.get('id', '')) == target:
                return item.get('label') or item.get('name') or target
    return target

def _tigertag_fetch_inventory(user_id):
    id_token, firebase_uid = _tigertag_get_valid_session(user_id)
    url = (
        f"{TIGERTAG_FIRESTORE_BASE_URL}/projects/{_tigertag_firebase_config['project_id']}"
        f"/databases/(default)/documents/users/{firebase_uid}/inventory"
    )
    resp = requests.get(url, headers={"Authorization": f"Bearer {id_token}"}, timeout=15)

    if resp.status_code in (401, 403):
        with _tigertag_token_cache_lock:
            _tigertag_token_cache.pop(user_id, None)
        id_token, firebase_uid = _tigertag_get_valid_session(user_id)
        resp = requests.get(url, headers={"Authorization": f"Bearer {id_token}"}, timeout=15)

    resp.raise_for_status()
    data = resp.json()

    docs = data.get('documents', []) if data else []
    spools = []
    for doc in docs:
        fields = _tigertag_parse_doc(doc)
        if fields.get('deleted') is True:
            continue
        raw_uid = fields.get('uid') or doc['name'].split('/')[-1]
        fields['uid'] = str(raw_uid).upper()
        spools.append(fields)
    return spools

def _get_tigertag_slots(user_id):
    slots = []
    try:
        spools = _tigertag_fetch_inventory(user_id)
    except ValueError:
        return slots
    except Exception as e:
        app_logger.warning(f"[TigerTag] Lecture inventaire impossible: {e}")
        return slots

    references = _tigertag_get_references() if spools else {}

    for d in spools:
        brand = _tigertag_resolve_reference(references, 'brand', d.get('id_brand'))
        material = _tigertag_resolve_reference(references, 'material', d.get('id_material'))
        color_hex = '#{:02x}{:02x}{:02x}'.format(
            int(d.get('color_r', 0) or 0), int(d.get('color_g', 0) or 0), int(d.get('color_b', 0) or 0)
        )
        name = d.get('name') or d.get('color_name') or f"{brand} {material}".strip() or f"TigerTag {d['uid']}"
        remaining = d.get('weight_available')
        if remaining is None:
            remaining = d.get('weight')

        slots.append({
            'source_type': 'tigertag',
            'source_id': d['uid'],
            'name': name,
            'vendor': '' if str(brand).strip().isdigit() else (brand or ''), 
            'color_name': d.get('color_name') or '',
            'material': material or '',
            'color_hex': color_hex,
            'remaining_g': remaining,
            'capacity_g': 1000,
            'source_label': 'TigerTag',
        })
    return slots


_ROUTES = (
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"tigertag.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {}
