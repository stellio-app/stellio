"""Stellio — plugin intégré « ChatGPT (OpenAI) » (IA en ligne)

Fournisseur d'IA en ligne : génération de texte (et d'images en entrée) et liste des modèles. La clé API est celle que l'utilisateur
enregistre dans Paramètres > IA (stockée chiffrée, jamais renvoyée au navigateur). S'enregistre auprès du hub `ai_providers` à l'activation.
"""
import re
import requests

_REQUIRED = ('app_logger',)
_ROUTES = ()          # pas de route propre : les clés et la liste des modèles passent par le hub ai_providers
PID = 'openai'
META = {'label': 'ChatGPT (OpenAI)', 'default_model': 'gpt-4o-mini', 'key_url': 'https://platform.openai.com/api-keys'}
_hub = None


def generate(model, key, prompt, system="", temperature=0.2, num_predict=200, images=None, timeout=120):
    """Texte généré par le fournisseur (lève AIProviderError en cas d'échec)."""
    h = _hub
    label = META['label']
    images = [i for i in (images or []) if isinstance(i, str) and i]
    _image_mime, _ai_http_error, AIProviderError = h._image_mime, h._ai_http_error, h.AIProviderError
    try:
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
    except requests.exceptions.Timeout:
        raise AIProviderError(f"{label} met trop de temps à répondre (plus de {timeout} secondes).")
    except requests.exceptions.RequestException as e:
        raise AIProviderError(f"Impossible de joindre {label} : {type(e).__name__}.")


def list_models(key):
    h = _hub
    label = META['label']
    _ai_http_error = h._ai_http_error
    r = requests.get('https://api.openai.com/v1/models', timeout=15, headers={'Authorization': f'Bearer {key}'})
    if not r.ok:
        raise _ai_http_error(label, r)
    skip = ('embedding', 'whisper', 'tts', 'dall-e', 'moderation', 'transcribe', 'audio', 'realtime', 'image', 'search', 'instruct')
    models = [m.get('id') for m in (r.json().get('data') or [])
              if isinstance(m, dict) and m.get('id')
              and re.match(r'^(gpt-|chatgpt-|o\d)', m['id']) and not any(x in m['id'] for x in skip)]
    return models


def init(ns, routes=True):
    global _hub
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"ai_openai.init : services manquants : {missing}")
    from modules import ai_providers
    _hub = ai_providers
    ai_providers.register_provider(PID, generate=generate, list_models=list_models, **META)
    return {}
