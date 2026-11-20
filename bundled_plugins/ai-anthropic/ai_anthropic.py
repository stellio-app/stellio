"""Stellio — plugin intégré « Claude (Anthropic) » (IA en ligne)

Fournisseur d'IA en ligne : génération de texte (et d'images en entrée) et liste des modèles. La clé API est celle que l'utilisateur
enregistre dans Paramètres > IA (stockée chiffrée, jamais renvoyée au navigateur). S'enregistre auprès du hub `ai_providers` à l'activation.
"""
import re
import requests

_REQUIRED = ('app_logger',)
_ROUTES = ()          # pas de route propre : les clés et la liste des modèles passent par le hub ai_providers
PID = 'anthropic'
META = {'label': 'Claude (Anthropic)', 'default_model': 'claude-haiku-5-5', 'key_url': 'https://console.anthropic.com/settings/keys'}
_hub = None


def generate(model, key, prompt, system="", temperature=0.2, num_predict=200, images=None, timeout=120):
    """Texte généré par le fournisseur (lève AIProviderError en cas d'échec)."""
    h = _hub
    label = META['label']
    images = [i for i in (images or []) if isinstance(i, str) and i]
    _image_mime, _ai_http_error, AIProviderError = h._image_mime, h._ai_http_error, h.AIProviderError
    try:
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
    except requests.exceptions.Timeout:
        raise AIProviderError(f"{label} met trop de temps à répondre (plus de {timeout} secondes).")
    except requests.exceptions.RequestException as e:
        raise AIProviderError(f"Impossible de joindre {label} : {type(e).__name__}.")


def list_models(key):
    h = _hub
    label = META['label']
    _ai_http_error = h._ai_http_error
    r = requests.get('https://api.anthropic.com/v1/models?limit=100', timeout=15,
                     headers={'x-api-key': key, 'anthropic-version': '2023-06-01'})
    if not r.ok:
        raise _ai_http_error(label, r)
    models = [m.get('id') for m in (r.json().get('data') or []) if isinstance(m, dict) and m.get('id')]
    return models


def init(ns, routes=True):
    global _hub
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"ai_anthropic.init : services manquants : {missing}")
    from modules import ai_providers
    _hub = ai_providers
    ai_providers.register_provider(PID, generate=generate, list_models=list_models, **META)
    return {}
