"""Stellio — plugin intégré « Gemini (Google) » (IA en ligne)

Fournisseur d'IA en ligne : génération de texte (et d'images en entrée) et liste des modèles. La clé API est celle que l'utilisateur
enregistre dans Paramètres > IA (stockée chiffrée, jamais renvoyée au navigateur). S'enregistre auprès du hub `ai_providers` à l'activation.
"""
import re
import requests

_REQUIRED = ('app_logger',)
_ROUTES = ()          # pas de route propre : les clés et la liste des modèles passent par le hub ai_providers
PID = 'gemini'
META = {'label': 'Gemini (Google)', 'default_model': 'gemini-2.5-flash', 'key_url': 'https://aistudio.google.com/apikey'}
_hub = None


def generate(model, key, prompt, system="", temperature=0.2, num_predict=200, images=None, timeout=120):
    """Texte généré par le fournisseur (lève AIProviderError en cas d'échec)."""
    h = _hub
    label = META['label']
    images = [i for i in (images or []) if isinstance(i, str) and i]
    _image_mime, _ai_http_error, AIProviderError = h._image_mime, h._ai_http_error, h.AIProviderError
    try:
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


def list_models(key):
    h = _hub
    label = META['label']
    _ai_http_error = h._ai_http_error
    r = requests.get('https://generativelanguage.googleapis.com/v1beta/models?pageSize=200', timeout=15,
                     headers={'x-goog-api-key': key})
    if not r.ok:
        raise _ai_http_error(label, r)
    models = [str(m.get('name', '')).replace('models/', '', 1) for m in (r.json().get('models') or [])
              if isinstance(m, dict) and 'generateContent' in (m.get('supportedGenerationMethods') or [])]
    models = [m for m in models if m.startswith('gemini')]
    return models


def init(ns, routes=True):
    global _hub
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"ai_gemini.init : services manquants : {missing}")
    from modules import ai_providers
    _hub = ai_providers
    ai_providers.register_provider(PID, generate=generate, list_models=list_models, **META)
    return {}
