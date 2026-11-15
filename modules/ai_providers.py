"""Stellio — Fournisseurs IA (Ollama, Anthropic, OpenAI, Gemini), clés, modèles recommandés

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

def _ollama_is_reachable(base_url: str, timeout: int = 4) -> bool:
    try:
        return requests.get(f"{base_url}/api/tags", timeout=timeout).ok
    except Exception:
        return False

def _call_ollama(base_url: str, model: str, prompt: str, system: str = "",
                 temperature: float = 0.2, num_predict: int = 200,
                 timeout: int = 300, images: list = None, extra_options: dict = None, keep_alive=None) -> str:
    payload = {"model": model, "prompt": prompt, "stream": False,
               "think": False,
               "options": {"temperature": temperature, "num_predict": num_predict}}
    if extra_options:
        payload["options"].update(extra_options)
    if keep_alive is not None:
        payload["keep_alive"] = keep_alive
    if system:
        payload["system"] = system
    if images:
        payload["images"] = images
    r = requests.post(f"{base_url}/api/generate", json=payload, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    text = (data.get('response') or '').strip()
    if not text and (data.get('thinking') or '').strip():
        app_logger.info("[AI] Réponse vide (budget consumé en thinking), nouvel essai avec num_predict élargi")
        payload["options"]["num_predict"] = max(num_predict * 4, 1024)
        r = requests.post(f"{base_url}/api/generate", json=payload, timeout=timeout)
        r.raise_for_status()
        text = (r.json().get('response') or '').strip()
    return text

# ---------------------------------------------------------------------------
# Fournisseurs d'IA en ligne (facultatif) : Claude (Anthropic), ChatGPT (OpenAI), Gemini (Google).
# Par défaut Stellio reste 100 % local (Ollama). Un fournisseur en ligne n'est utilisé que si l'utilisateur
# l'a choisi et a enregistré sa propre clé API. La clé est stockée chiffrée (ai_secrets.json), n'est jamais
# renvoyée au navigateur ni écrite dans les logs.
# ---------------------------------------------------------------------------
AI_PROVIDER_IDS = ('ollama', 'anthropic', 'openai', 'gemini')

AI_CLOUD_PROVIDERS = {
    'anthropic': {'label': 'Claude (Anthropic)', 'default_model': 'claude-haiku-5-5',
                  'key_url': 'https://console.anthropic.com/settings/keys'},
    'openai':    {'label': 'ChatGPT (OpenAI)', 'default_model': 'gpt-4o-mini',
                  'key_url': 'https://platform.openai.com/api-keys'},
    'gemini':    {'label': 'Gemini (Google)', 'default_model': 'gemini-2.5-flash',
                  'key_url': 'https://aistudio.google.com/apikey'},
}

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

def _cloud_generate(provider, model, key, prompt, system="", temperature=0.2, num_predict=200,
                    images=None, timeout=AI_CLOUD_TIMEOUT_SECONDS) -> str:
    label = AI_CLOUD_PROVIDERS[provider]['label']
    images = [i for i in (images or []) if isinstance(i, str) and i]
    try:
        if provider == 'anthropic':
            content = [{'type': 'image', 'source': {'type': 'base64', 'media_type': _image_mime(i), 'data': i}} for i in images]
            content.append({'type': 'text', 'text': prompt})
            body = {'model': model, 'max_tokens': max(int(num_predict), 64), 'temperature': temperature,
                    'messages': [{'role': 'user', 'content': content}]}
            if system:
                body['system'] = system
            r = requests.post('https://api.anthropic.com/v1/messages', json=body, timeout=timeout,
                              headers={'x-api-key': key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'})
            if not r.ok:
                raise _ai_http_error(label, r)
            blocks = r.json().get('content') or []
            return ''.join(b.get('text', '') for b in blocks if isinstance(b, dict) and b.get('type') == 'text').strip()

        if provider == 'openai':
            msgs = [{'role': 'system', 'content': system}] if system else []
            if images:
                user_content = [{'type': 'text', 'text': prompt}] + [
                    {'type': 'image_url', 'image_url': {'url': f"data:{_image_mime(i)};base64,{i}"}} for i in images]
            else:
                user_content = prompt
            msgs.append({'role': 'user', 'content': user_content})
            body = {'model': model, 'messages': msgs, 'temperature': temperature,
                    'max_completion_tokens': max(int(num_predict) * 4, 512)}
            headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
            r = requests.post('https://api.openai.com/v1/chat/completions', json=body, headers=headers, timeout=timeout)
            if r.status_code == 400 and 'temperature' in (r.text or '').lower():
                body.pop('temperature', None)   # certains modèles n'acceptent que la température par défaut
                r = requests.post('https://api.openai.com/v1/chat/completions', json=body, headers=headers, timeout=timeout)
            if not r.ok:
                raise _ai_http_error(label, r)
            choices = r.json().get('choices') or []
            return str(((choices[0] or {}).get('message') or {}).get('content') or '').strip() if choices else ''

        if provider == 'gemini':
            from urllib.parse import quote
            parts = [{'inline_data': {'mime_type': _image_mime(i), 'data': i}} for i in images] + [{'text': prompt}]
            body = {'contents': [{'role': 'user', 'parts': parts}],
                    'generationConfig': {'temperature': temperature, 'maxOutputTokens': max(int(num_predict) * 4, 1024)}}
            if system:
                body['systemInstruction'] = {'parts': [{'text': system}]}
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{quote(model, safe='')}:generateContent",
                              json=body, timeout=timeout,
                              headers={'x-goog-api-key': key, 'Content-Type': 'application/json'})
            if not r.ok:
                raise _ai_http_error(label, r)
            data = r.json()
            block = (data.get('promptFeedback') or {}).get('blockReason')
            if block:
                raise AIProviderError(f"{label} a bloqué la requête ({block}).")
            cands = data.get('candidates') or []
            if not cands:
                return ''
            return ''.join(p.get('text', '') for p in ((cands[0].get('content') or {}).get('parts') or [])
                           if isinstance(p, dict)).strip()
    except requests.exceptions.Timeout:
        raise AIProviderError(f"{label} met trop de temps à répondre (plus de {timeout} secondes).")
    except requests.exceptions.RequestException as e:
        raise AIProviderError(f"Impossible de joindre {label} : {type(e).__name__}.")
    raise AIProviderError("Fournisseur d'IA inconnu.")

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
    providers = [{'id': 'ollama', 'label': 'Ollama', 'local': True}]
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

def api_ai_cloud_models():
    blocked = _server_edition_only()
    if blocked:
        return blocked
    provider = request.args.get('provider', '')
    if provider not in AI_CLOUD_PROVIDERS:
        return jsonify({"error": "Fournisseur inconnu", "code": "unknown_provider"}), 400
    key = _get_ai_key(provider)
    if not key:
        return jsonify({"error": "Aucune clé API enregistrée", "code": "no_key"}), 400
    label = AI_CLOUD_PROVIDERS[provider]['label']
    try:
        if provider == 'anthropic':
            r = requests.get('https://api.anthropic.com/v1/models?limit=100', timeout=15,
                             headers={'x-api-key': key, 'anthropic-version': '2023-06-01'})
            if not r.ok:
                raise _ai_http_error(label, r)
            models = [m.get('id') for m in (r.json().get('data') or []) if isinstance(m, dict) and m.get('id')]
        elif provider == 'openai':
            r = requests.get('https://api.openai.com/v1/models', timeout=15, headers={'Authorization': f'Bearer {key}'})
            if not r.ok:
                raise _ai_http_error(label, r)
            skip = ('embedding', 'whisper', 'tts', 'dall-e', 'moderation', 'transcribe', 'audio', 'realtime', 'image', 'search', 'instruct')
            models = [m.get('id') for m in (r.json().get('data') or [])
                      if isinstance(m, dict) and m.get('id')
                      and re.match(r'^(gpt-|chatgpt-|o\d)', m['id']) and not any(x in m['id'] for x in skip)]
        else:
            r = requests.get('https://generativelanguage.googleapis.com/v1beta/models?pageSize=200', timeout=15,
                             headers={'x-goog-api-key': key})
            if not r.ok:
                raise _ai_http_error(label, r)
            models = [str(m.get('name', '')).replace('models/', '', 1) for m in (r.json().get('models') or [])
                      if isinstance(m, dict) and 'generateContent' in (m.get('supportedGenerationMethods') or [])]
            models = [m for m in models if m.startswith('gemini')]
        models = sorted({m for m in models if m and AI_MODEL_NAME_RE.match(m)})
        return jsonify({"models": models}), 200
    except AIProviderError as e:
        return jsonify({"error": str(e), "code": "provider_error"}), 502
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Impossible de joindre {label} : {type(e).__name__}.", "code": "unreachable"}), 502

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

def is_ai_enabled() -> bool:
    settings = load_settings() or {}
    return settings.get('ai_enabled') is True

OLLAMA_TIMEOUT_SECONDS = 300

def _call_ai(prompt: str, system: str = "",
             num_predict: int = 200, temperature: float = 0.2, images: list = None,
             extra_options: dict = None, keep_alive=None) -> tuple:
    if not is_ai_enabled():
        raise AIDisabledError("Les fonctionnalités IA sont désactivées dans les Paramètres.")

    provider = get_ai_provider()
    if provider != 'ollama':
        return _call_cloud_ai(provider, prompt, system=system, num_predict=num_predict,
                              temperature=temperature, images=images)

    settings = load_settings() or {}
    base_url = get_ollama_base_url()
    model    = settings.get('ollama_model') or 'qwen3.5:4b'

    if not _ollama_is_reachable(base_url):
        app_logger.info(f"[AI] ❌ Ollama injoignable ({base_url})")
        raise RuntimeError(
            f"Ollama n'est pas accessible à l'adresse {base_url}. Vérifiez qu'Ollama est bien "
            f"lancé sur cette machine (ou changez l'adresse du serveur dans Paramètres > IA)."
        )

    try:
        text = _call_ollama(base_url, model, prompt, system=system, temperature=temperature,
                            num_predict=num_predict, timeout=OLLAMA_TIMEOUT_SECONDS, images=images,
                            extra_options=extra_options, keep_alive=keep_alive)
        if text:
            app_logger.info(f"[AI] ✅ Ollama ({model})")
            return text, 'ollama'
        app_logger.warning("[AI] ⚠️ Ollama a répondu sans contenu exploitable")
        raise RuntimeError("Ollama a répondu, mais sans contenu exploitable. Réessayez.")
    except requests.exceptions.Timeout:
        app_logger.warning(f"[AI] ⚠️ Ollama timeout après {OLLAMA_TIMEOUT_SECONDS}s (modèle: {model})")
        raise RuntimeError(
            f"Ollama met trop de temps à répondre (plus de {OLLAMA_TIMEOUT_SECONDS // 60} minutes). "
            f"Le modèle « {model} » est peut-être trop lourd pour cette machine (CPU seul, sans carte "
            f"graphique dédiée), ou une autre génération est déjà en cours. Essayez un modèle plus "
            f"léger dans Paramètres > IA, ou réessayez dans quelques instants."
        )
    except requests.exceptions.RequestException as e:
        if images:
            app_logger.warning(f"[AI] ⚠️ Échec avec image (modèle probablement non multimodal): {e} — nouvelle tentative en texte seul")
            try:
                text = _call_ollama(base_url, model, prompt, system=system, temperature=temperature,
                                    num_predict=num_predict, timeout=OLLAMA_TIMEOUT_SECONDS, images=None)
                if text:
                    app_logger.info(f"[AI] ✅ Ollama ({model}, sans image)")
                    return text, 'ollama_no_vision'
            except Exception:
                pass
        app_logger.error(f"[AI] ❌ Ollama: {e}")
        raise RuntimeError(f"Erreur de connexion à Ollama : {e}")

def api_ollama_models():
    base_url = get_ollama_base_url()
    try:
        r = requests.get(f"{base_url}/api/tags", timeout=8)
        r.raise_for_status()
        models = [m.get('name', '') for m in r.json().get('models', []) if m.get('name')]
        return jsonify({"models": models}), 200
    except requests.exceptions.ConnectionError:
        return jsonify({"error_code": "ollama_unreachable", "error_params": {"url": base_url},
                         "error": f"Impossible de joindre Ollama sur {base_url}."}), 502
    except requests.exceptions.Timeout:
        return jsonify({"error_code": "ollama_timeout",
                         "error": "Ollama ne répond pas (timeout)."}), 504
    except Exception as e:
        app_logger.error(f"[API] Erreur non gérée: {e}")
        return jsonify({"error_code": "internal_error",
                         "error": "Une erreur interne est survenue lors du traitement de la requête"}), 500

def _detect_hardware():
    info = {
        'cpu_cores': os.cpu_count() or 4,
        'ram_gb': None,
        'gpu_name': None,
        'vram_gb': None,
    }
    try:
        import psutil
        info['ram_gb'] = round(psutil.virtual_memory().total / (1024 ** 3), 1)
    except Exception as e:
        app_logger.info(f"[HW] RAM non détectée (psutil manquant ?): {e}")

    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            first_line = result.stdout.strip().splitlines()[0]
            parts = [p.strip() for p in first_line.split(',')]
            if len(parts) >= 2:
                info['gpu_name'] = parts[0]
                info['vram_gb'] = round(float(parts[1]) / 1024, 1)
    except FileNotFoundError:
        pass
    except Exception as e:
        app_logger.info(f"[HW] Détection GPU NVIDIA échouée: {e}")

    if not info['gpu_name'] and sys.platform == 'win32':
        try:
            ps_cmd = (
                "Get-CimInstance Win32_VideoController | "
                "Select-Object Name, AdapterRAM | ConvertTo-Json -Compress"
            )
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', ps_cmd],
                capture_output=True, text=True, timeout=8
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout.strip())
                candidates = data if isinstance(data, list) else [data]
                dedicated = [
                    c for c in candidates
                    if c.get('Name') and (
                        'nvidia' in c['Name'].lower()
                        or ('radeon' in c['Name'].lower() and 'graphics' not in c['Name'].lower())
                    )
                ]
                if dedicated:
                    best = dedicated[0]
                    info['gpu_name'] = best['Name'].strip()
                    ram_bytes = best.get('AdapterRAM') or 0
                    vram_gb = ram_bytes / (1024 ** 3)
                    if 0 < vram_gb <= 32:
                        info['vram_gb'] = round(vram_gb, 1)
                    else:
                        info['vram_gb'] = 4.0
                        app_logger.info(
                            f"[HW] VRAM WMI non fiable pour {info['gpu_name']} "
                            f"(valeur brute {ram_bytes}) → estimation prudente à 4 Go"
                        )
                    app_logger.info(f"[HW] GPU détectée via repli WMI: {info['gpu_name']} (~{info['vram_gb']} Go)")
        except Exception as e:
            app_logger.info(f"[HW] Repli WMI GPU échoué: {e}")

    if not info['gpu_name'] and sys.platform == 'darwin':
        try:
            result = subprocess.run(
                ['system_profiler', 'SPDisplaysDataType', '-json'],
                capture_output=True, text=True, timeout=8
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout.strip())
                displays = data.get('SPDisplaysDataType', [])
                if displays:
                    gpu = displays[0]
                    info['gpu_name'] = gpu.get('sppci_model') or gpu.get('_name')
                    vram_str = gpu.get('spdisplays_vram') or gpu.get('spdisplays_vram_shared', '')
                    digits = ''.join(c for c in vram_str if c.isdigit())
                    if digits:
                        vram_val = float(digits)
                        info['vram_gb'] = round(vram_val / 1024, 1) if vram_val > 256 else round(vram_val, 1)
                    app_logger.info(f"[HW] GPU détectée via system_profiler: {info['gpu_name']} (~{info['vram_gb']} Go)")
        except Exception as e:
            app_logger.info(f"[HW] Repli system_profiler GPU échoué: {e}")

    return info

OLLAMA_MODEL_TIERS = [
    {'min_vram_gb': 16, 'model': 'gemma3:27b',  'vision': True,
     'label_key': 'ollama.rec_gpu_high'},
    {'min_vram_gb': 8,  'model': 'gemma4:12b',  'vision': False,
     'label_key': 'ollama.rec_gpu_good'},
    {'min_vram_gb': 4,  'model': 'llama3.1:8b', 'vision': False,
     'label_key': 'ollama.rec_gpu_modest'},
    {'min_vram_gb': 0, 'min_ram_gb': 16, 'model': 'qwen3.5:4b', 'vision': True,
     'label_key': 'ollama.rec_cpu_ok'},
    {'min_vram_gb': 0, 'min_ram_gb': 0,  'model': 'smollm3:3b', 'vision': False,
     'label_key': 'ollama.rec_cpu_low'},
]

def _recommend_ollama_model(hw):
    vram = hw.get('vram_gb') or 0
    ram = hw.get('ram_gb') if hw.get('ram_gb') is not None else 8

    for tier in OLLAMA_MODEL_TIERS:
        if vram >= tier['min_vram_gb'] and ram >= tier.get('min_ram_gb', 0):
            return {
                'model': tier['model'],
                'vision': tier['vision'],
                'label_key': tier['label_key'],
                'pull_command': f"ollama pull {tier['model']}"
            }
    return {
        'model': 'smollm3:3b', 'vision': False,
        'label_key': 'ollama.rec_cpu_low',
        'pull_command': 'ollama pull smollm3:3b'
    }

def api_ollama_recommend_model():
    hw = _detect_hardware()
    rec = _recommend_ollama_model(hw)

    installed = []
    try:
        base_url = get_ollama_base_url()
        r = requests.get(f"{base_url}/api/tags", timeout=5)
        if r.ok:
            installed = [m.get('name', '') for m in r.json().get('models', []) if m.get('name')]
    except Exception:
        pass

    rec['already_installed'] = any(
        installed_name.split(':')[0] == rec['model'].split(':')[0] for installed_name in installed
    )

    return jsonify({'hardware': hw, 'recommendation': rec}), 200


_ROUTES = (
    ('/api/ai/providers', ['GET'], 'api_ai_providers', ('login_required', )),
    ('/api/ai/provider-key', ['POST'], 'api_ai_provider_key_save', ('login_required', )),
    ('/api/ai/provider-key/delete', ['POST'], 'api_ai_provider_key_delete', ('login_required', )),
    ('/api/ai/cloud-models', ['GET'], 'api_ai_cloud_models', ('login_required', )),
    ('/api/ai/test', ['POST'], 'api_ai_test', ('login_required', )),
    ('/api/ollama/models', ['GET'], 'api_ollama_models', ('login_required', )),
    ('/api/ollama/recommend-model', ['GET'], 'api_ollama_recommend_model', ('login_required', )),
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
