"""Stellio — hub des fournisseurs IA : registre, clés, aiguillage des appels (le code de chaque fournisseur est un plugin intégré)

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `ai_providers.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import datetime
import json
import os
import re
import requests
import subprocess
import sys
import threading
import time

_REQUIRED = (
    'DATA_DIR',
    'IS_SERVER_EDITION',
    '_atomic_replace',
    'app',
    'app_logger',
    'decrypt_password',
    'encrypt_password',
    'jsonify',
    'load_settings',
    'login_required',
    'request',
)
_OPTIONAL = ()   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('datetime', 'json', 'os', 're', 'requests', 'subprocess', 'sys', 'threading', 'time', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
DATA_DIR = None
IS_SERVER_EDITION = None
_atomic_replace = None
app = None
app_logger = None
decrypt_password = None
encrypt_password = None
jsonify = None
load_settings = None
login_required = None
request = None


AI_SECRETS_FILE = None
def get_ollama_base_url():
    settings = load_settings() or {}
    url = (settings.get('ollama_url') or 'http://localhost:11434').strip().rstrip('/')
    return url

def get_user_lang() -> str:
    try:
        settings = load_settings() or {}
        return (settings.get('lang') or 'fr').strip().lower()[:2]
    except Exception:
        return 'fr'

LANG_NAMES = {
    'fr': 'français', 'en': 'English', 'de': 'Deutsch',
    'es': 'español',  'it': 'italiano', 'pt': 'português',
    'nl': 'Nederlands', 'pl': 'polski', 'ru': 'русский',
}

AI_PROVIDER_IDS = ('ollama', 'anthropic', 'openai', 'gemini')

AI_CLOUD_PROVIDERS = {}      # rempli par register_provider() à l'activation des plugins ai-openai / ai-anthropic / ai-gemini

AI_CLOUD_TIMEOUT_SECONDS = 120

AI_MODEL_NAME_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,99}$')

AI_KEY_RE = re.compile(r'^[\x21-\x7e]{8,400}$')

_ai_secrets_lock = threading.Lock()

def _server_edition_only():
    """Réponse 404 pour les fonctions réservées à l'édition serveur (Linux / headless)."""
    if IS_SERVER_EDITION:
        return None
    return jsonify({"error": "Fonction réservée à l'édition serveur (Linux)", "code": "server_edition_only"}), 404

class AIProviderError(RuntimeError):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status

def get_ai_provider() -> str:
    if not IS_SERVER_EDITION:
        return 'ollama'
    try:
        p = str((load_settings() or {}).get('ai_provider') or 'ollama').strip().lower()
    except Exception:
        return 'ollama'
    return p if p in AI_PROVIDER_IDS else 'ollama'

def _load_ai_secrets() -> dict:
    try:
        with open(AI_SECRETS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception as e:
        app_logger.warning(f"[AI] ai_secrets.json illisible: {e}")
        return {}

def _save_ai_secrets(data: dict):
    tmp_path = AI_SECRETS_FILE + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    try:
        os.chmod(tmp_path, 0o600)
    except Exception:
        pass
    _atomic_replace(tmp_path, AI_SECRETS_FILE)

def _get_ai_key(provider: str):
    with _ai_secrets_lock:
        entry = _load_ai_secrets().get(provider) or {}
    return decrypt_password(entry.get('key')) if entry.get('key') else None

def _get_ai_model(provider: str) -> str:
    meta = AI_CLOUD_PROVIDERS[provider]
    value = str((load_settings() or {}).get(f'ai_model_{provider}') or '').strip()
    return value if value and AI_MODEL_NAME_RE.match(value) else meta['default_model']

def _image_mime(b64: str) -> str:
    head = (b64 or '')[:12]
    if head.startswith('iVBOR'):
        return 'image/png'
    if head.startswith('UklGR'):
        return 'image/webp'
    if head.startswith('R0lGOD'):
        return 'image/gif'
    return 'image/jpeg'

def _ai_http_error(label: str, resp) -> 'AIProviderError':
    status = resp.status_code
    detail = ''
    try:
        body = resp.json()
        err = body.get('error') if isinstance(body, dict) else None
        if isinstance(err, dict):
            detail = str(err.get('message') or '')
        elif isinstance(err, str):
            detail = err
    except Exception:
        pass
    detail = re.sub(r'\s+', ' ', detail).strip()[:300]
    if status in (401, 403):
        text = f"{label} a refusé la clé API : vérifiez-la dans Paramètres > IA."
        detail = ''   # le message d'erreur peut citer une partie de la clé : on ne le répercute jamais
    elif status == 429:
        text = f"{label} : limite de requêtes ou crédit épuisé (HTTP 429)."
    elif status == 404:
        text = f"{label} : modèle introuvable (HTTP 404). Vérifiez le nom du modèle dans Paramètres > IA."
    else:
        text = f"{label} a répondu HTTP {status}."
    if detail:
        text += f" {detail}"
    return AIProviderError(text, status)

def _call_cloud_ai(provider, prompt, system="", num_predict=200, temperature=0.2, images=None) -> tuple:
    meta = AI_CLOUD_PROVIDERS[provider]
    key = _get_ai_key(provider)
    if not key:
        raise RuntimeError(f"Aucune clé API {meta['label']} enregistrée : ajoutez-la dans Paramètres > IA.")
    model = _get_ai_model(provider)
    try:
        text = _cloud_generate(provider, model, key, prompt, system, temperature, num_predict, images)
        source = provider
    except AIProviderError as e:
        if images and e.status == 400:
            app_logger.warning(f"[AI] ⚠️ {meta['label']} a refusé l'image ({model}) — nouvelle tentative en texte seul")
            text = _cloud_generate(provider, model, key, prompt, system, temperature, num_predict, None)
            source = f"{provider}_no_vision"
        else:
            app_logger.warning(f"[AI] ❌ {meta['label']} ({model}) : {e}")
            raise RuntimeError(str(e))
    if not text:
        raise RuntimeError(f"{meta['label']} a répondu, mais sans contenu exploitable. Réessayez.")
    app_logger.info(f"[AI] ✅ {meta['label']} ({model})")
    return text, source

def api_ai_providers():
    blocked = _server_edition_only()
    if blocked:
        return blocked
    secrets_ = _load_ai_secrets()
    providers = [{'id': 'ollama', 'label': 'Ollama', 'local': True}] if 'ollama' in PROVIDERS else []
    for pid, meta in AI_CLOUD_PROVIDERS.items():
        entry = secrets_.get(pid) or {}
        providers.append({'id': pid, 'label': meta['label'], 'local': False,
                          'configured': bool(entry.get('key')),
                          'last4': str(entry.get('last4') or '') if entry.get('key') else '',
                          'model': _get_ai_model(pid), 'default_model': meta['default_model'],
                          'key_url': meta['key_url']})
    return jsonify({'provider': get_ai_provider(), 'providers': providers}), 200

def api_ai_provider_key_save():
    blocked = _server_edition_only()
    if blocked:
        return blocked
    data = request.get_json(silent=True) or {}
    provider = str(data.get('provider') or '')
    key = str(data.get('key') or '').strip()
    if provider not in AI_CLOUD_PROVIDERS:
        return jsonify({"error": "Fournisseur inconnu", "code": "unknown_provider"}), 400
    if not AI_KEY_RE.match(key):
        return jsonify({"error": "Clé API invalide (8 à 400 caractères, sans espace)", "code": "invalid_key"}), 400
    encrypted = encrypt_password(key)
    if not encrypted:
        return jsonify({"error": "Impossible de chiffrer la clé API"}), 500
    with _ai_secrets_lock:
        secrets_ = _load_ai_secrets()
        secrets_[provider] = {'key': encrypted, 'last4': key[-4:],
                              'saved_at': datetime.datetime.now().isoformat(timespec='seconds')}
        _save_ai_secrets(secrets_)
    app_logger.info(f"[AI] Clé API enregistrée pour {AI_CLOUD_PROVIDERS[provider]['label']}")
    return jsonify({"success": True, "configured": True, "last4": key[-4:]}), 200

def api_ai_provider_key_delete():
    blocked = _server_edition_only()
    if blocked:
        return blocked
    provider = str((request.get_json(silent=True) or {}).get('provider') or '')
    if provider not in AI_CLOUD_PROVIDERS:
        return jsonify({"error": "Fournisseur inconnu", "code": "unknown_provider"}), 400
    with _ai_secrets_lock:
        secrets_ = _load_ai_secrets()
        secrets_.pop(provider, None)
        _save_ai_secrets(secrets_)
    app_logger.info(f"[AI] Clé API supprimée pour {AI_CLOUD_PROVIDERS[provider]['label']}")
    return jsonify({"success": True, "configured": False}), 200

def api_ai_test():
    blocked = _server_edition_only()
    if blocked:
        return blocked
    provider = str((request.get_json(silent=True) or {}).get('provider') or '')
    if provider not in AI_CLOUD_PROVIDERS:
        return jsonify({"error": "Fournisseur inconnu", "code": "unknown_provider"}), 400
    key = _get_ai_key(provider)
    if not key:
        return jsonify({"error": "Aucune clé API enregistrée", "code": "no_key"}), 400
    model = _get_ai_model(provider)
    started = time.time()
    try:
        reply = _cloud_generate(provider, model, key, "Réponds uniquement par le mot OK.", "", 0, 16, None, timeout=45)
    except AIProviderError as e:
        return jsonify({"ok": False, "error": str(e), "provider": provider, "model": model}), 200
    return jsonify({"ok": True, "provider": provider, "model": model,
                    "ms": int((time.time() - started) * 1000), "reply": reply[:40]}), 200

class AIDisabledError(RuntimeError):
    pass


# ── Registre des fournisseurs ─────────────────────────────────────────────────────────────────────────────
# Le cœur ne contient plus le code d'aucun fournisseur : chaque fournisseur est un plugin intégré (ai-ollama, ai-openai, ai-anthropic,
# ai-gemini) qui s'enregistre ici à son activation. Sans plugin, `is_ai_enabled()` est faux et les fonctions IA répondent « désactivée ».
PROVIDERS = {}            # id -> {'label', 'local', 'call' | 'generate', 'list_models', 'default_model', 'key_url', …}


def register_provider(pid, label, local=False, default_model='', key_url='', generate=None, list_models=None, call=None, raw_call=None, reachable=None):
    PROVIDERS[pid] = {'id': pid, 'label': label, 'local': bool(local), 'default_model': default_model, 'key_url': key_url,
                      'generate': generate, 'list_models': list_models, 'call': call, 'raw_call': raw_call, 'reachable': reachable}
    if not local:
        AI_CLOUD_PROVIDERS[pid] = {'label': label, 'default_model': default_model, 'key_url': key_url}


def _assistant_loaded():
    """Vrai si le plugin « Assistant IA » est actif (il active toutes les fonctions IA)."""
    try:
        from modules import plugin_host
        return plugin_host.loaded('ai-assistant')
    except Exception:
        return True


def _ollama_is_reachable(base_url: str, timeout: int = 4) -> bool:
    p = PROVIDERS.get('ollama')
    return bool(p and p['reachable'](base_url, timeout))


def _call_ollama(*a, **k):
    p = PROVIDERS.get('ollama')
    if not p:
        raise AIDisabledError("Le plugin Ollama n'est pas activé (Plugins › Plugins intégrés).")
    return p['raw_call'](*a, **k)


def _cloud_generate(provider, model, key, prompt, system="", temperature=0.2, num_predict=200, images=None, timeout=AI_CLOUD_TIMEOUT_SECONDS) -> str:
    p = PROVIDERS.get(provider)
    if not p or not p.get('generate'):
        raise AIProviderError("Fournisseur d'IA inconnu ou plugin non activé.")
    return p['generate'](model, key, prompt, system, temperature, num_predict, images, timeout)


def api_ai_cloud_models():
    blocked = _server_edition_only()
    if blocked:
        return blocked
    provider = request.args.get('provider', '')
    p = PROVIDERS.get(provider)
    if provider not in AI_CLOUD_PROVIDERS or not p:
        return jsonify({"error": "Fournisseur inconnu", "code": "unknown_provider"}), 400
    key = _get_ai_key(provider)
    if not key:
        return jsonify({"error": "Aucune clé API enregistrée", "code": "no_key"}), 400
    label = p['label']
    try:
        models = p['list_models'](key) or []
        models = sorted({m for m in models if m and AI_MODEL_NAME_RE.match(m)})
        return jsonify({"models": models}), 200
    except AIProviderError as e:
        return jsonify({"error": str(e), "code": "provider_error"}), 502
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Impossible de joindre {label} : {type(e).__name__}.", "code": "unreachable"}), 502

def is_ai_enabled() -> bool:
    settings = load_settings() or {}
    return settings.get('ai_enabled') is True and _assistant_loaded()


def _call_ai(prompt: str, system: str = "",
             num_predict: int = 200, temperature: float = 0.2, images: list = None,
             extra_options: dict = None, keep_alive=None) -> tuple:
    if not is_ai_enabled():
        raise AIDisabledError("Les fonctionnalités IA sont désactivées (Paramètres, ou plugin « Assistant IA » non activé).")
    provider = get_ai_provider()
    p = PROVIDERS.get(provider)
    if not p:
        raise AIDisabledError("Le plugin du fournisseur d'IA choisi n'est pas activé (Plugins › Plugins intégrés).")
    if not p['local']:
        return _call_cloud_ai(provider, prompt, system=system, num_predict=num_predict, temperature=temperature, images=images)
    return p['call'](prompt, system, num_predict, temperature, images, extra_options, keep_alive)


_ROUTES = (
    ('/api/ai/providers', ['GET'], 'api_ai_providers', ('login_required', )),
    ('/api/ai/provider-key', ['POST'], 'api_ai_provider_key_save', ('login_required', )),
    ('/api/ai/provider-key/delete', ['POST'], 'api_ai_provider_key_delete', ('login_required', )),
    ('/api/ai/cloud-models', ['GET'], 'api_ai_cloud_models', ('login_required', )),
    ('/api/ai/test', ['POST'], 'api_ai_test', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"ai_providers.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    g['AI_SECRETS_FILE'] = os.path.join(DATA_DIR, "ai_secrets.json")
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {'AI_SECRETS_FILE': g['AI_SECRETS_FILE']}
