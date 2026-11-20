"""Stellio — plugin intégré « Ollama » (IA locale)

Fournisseur d'IA local : appels à un serveur Ollama, liste des modèles installés, recommandation d'un modèle selon la machine.
S'enregistre auprès du hub `ai_providers` (cœur) à l'activation ; sans lui, aucun appel IA locale n'est possible.
"""
import datetime, json, os, re, requests, subprocess, sys, threading, time

_REQUIRED = ('app', 'app_logger', 'jsonify', 'load_settings', 'login_required', 'request')
_MAIN = {}
OLLAMA_TIMEOUT_SECONDS = 300

app = app_logger = jsonify = load_settings = login_required = request = None


def get_ollama_base_url():
    settings = load_settings() or {}
    return (settings.get('ollama_url') or 'http://localhost:11434').strip().rstrip('/')


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


def call(prompt: str, system: str = "", num_predict: int = 200, temperature: float = 0.2, images: list = None,
         extra_options: dict = None, keep_alive=None) -> tuple:
    """Appel complet à Ollama (joignabilité, délais, repli sans image) : utilisé par le hub `ai_providers._call_ai`."""
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
    ('/api/ollama/models', ['GET'], 'api_ollama_models', ('login_required', )),
    ('/api/ollama/recommend-model', ['GET'], 'api_ollama_recommend_model', ('login_required', )),
)


def init(ns, routes=True):
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"ai_ollama.init : services manquants : {missing}")
    for n in _REQUIRED + ('datetime', 'json', 'os', 're', 'requests', 'subprocess', 'sys', 'threading', 'time'):
        if n in ns:
            g[n] = ns[n]
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    from modules import ai_providers
    ai_providers.register_provider('ollama', label='Ollama', local=True, call=call, raw_call=_call_ollama, reachable=_ollama_is_reachable)
    return {}
