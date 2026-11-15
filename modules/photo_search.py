"""Stellio — Recherche par photo (modèle de vision local)

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `photo_search.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import base64
import json
import math
import os
import re
import requests
import threading
import time

_REQUIRED = (
    'AIDisabledError',
    'CACHE_FILE',
    'Image',
    '_call_ai',
    '_effective_cpu_count',
    '_has_thumb_on_disk',
    '_low_memory',
    '_thumb_base_path',
    '_thumb_paused',
    '_trim_memory',
    '_user_is_active',
    'app',
    'app_logger',
    'get_ai_provider',
    'get_db',
    'get_ollama_base_url',
    'is_ai_enabled',
    'is_virtual_archive_path',
    'jsonify',
    'load_settings',
    'login_required',
    'request',
    'session',
)
_OPTIONAL = ()   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('base64', 'json', 'math', 'os', 're', 'requests', 'threading', 'time', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
AIDisabledError = None
CACHE_FILE = None
Image = None
_call_ai = None
_effective_cpu_count = None
_has_thumb_on_disk = None
_low_memory = None
_thumb_base_path = None
_thumb_paused = None
_trim_memory = None
_user_is_active = None
app = None
app_logger = None
get_ai_provider = None
get_db = None
get_ollama_base_url = None
is_ai_enabled = None
is_virtual_archive_path = None
jsonify = None
load_settings = None
login_required = None
request = None
session = None


# ── Recherche par photo (modèle de vision local) ────────────────────────────────────────────
# Principe économe : chaque miniature de la bibliothèque est décrite UNE fois en mots-clés par le modèle de vision
# (indexation en arrière-plan, pausable, une image à la fois, interrompue si la mémoire manque). Ensuite une recherche
# ne coûte qu'UN appel au modèle (la photo envoyée) : le classement se fait en local par recoupement de mots-clés.
_VISUAL_PROMPT = ("Describe this 3D printed object (or photo of one) with 8 to 14 lowercase English keywords, comma-separated: "
                  "object type, shape, function, style, notable parts. Keywords only, no sentence.")

_VISUAL_SYSTEM = "You index a 3D model library. Reply only with comma-separated lowercase English keywords."

_visual_state = {'running': False, 'stop': False, 'done': 0, 'total': 0, 'error': '', 'current': '', 'mode': 'gentle', 'waiting': ''}

_visual_call_lock = threading.Lock()   # un seul appel au modèle de vision à la fois (indexation ou recherche)

def _visual_ollama_opts(mode):
    """Limite les threads du modèle : mode doux = la moitié des cœurs, rapide = tous sauf un."""
    n = max(1, _effective_cpu_count())
    return {'num_thread': max(1, n // 2) if mode == 'gentle' else max(1, n - 1)}

def _visual_machine_busy():
    """Raison pour laquelle l'indexation doit patienter (CPU déjà chargé), sinon ''."""
    try:
        import psutil
        if psutil.cpu_percent(interval=0.5) > 70:
            return 'load'
    except Exception:
        try:
            if os.getloadavg()[0] / max(1, _effective_cpu_count()) > 0.8:
                return 'load'
        except Exception:
            pass
    return ''

def _visual_unload_model():
    """Libère la RAM : demande à Ollama de décharger le modèle de vision."""
    try:
        model = (load_settings() or {}).get('ollama_model') or ''
        if model:
            requests.post(f"{get_ollama_base_url()}/api/generate", json={"model": model, "keep_alive": 0}, timeout=10)
    except Exception:
        pass

_visual_lock = threading.Lock()

_VISUAL_STOP_WORDS = {'a', 'an', 'the', 'of', 'and', 'or', 'with', 'for', 'object', 'objects', 'printed', 'print', 'model', 'models',
                      '3d', 'piece', 'part', 'parts', 'item', 'shape', 'style', 'white', 'gray', 'grey'}

def _visual_tokens(text):
    out = set()
    for w in re.findall(r"[a-z0-9]+", (text or '').lower()):
        if len(w) < 3 or w in _VISUAL_STOP_WORDS:
            continue
        if len(w) > 4 and w.endswith('s') and not w.endswith('ss'):
            w = w[:-1]
        out.add(w)
    return out

def _visual_thumb_b64(file_path, size=448):
    """Miniature du fichier en JPEG réduit (base64) pour le modèle de vision ; None si absente."""
    base = _thumb_base_path(file_path)
    for ext in ('.webp', '.png', '.jpg'):
        p = base + ext
        if os.path.exists(p):
            try:
                from PIL import Image
                import io as _io
                with Image.open(p) as im:
                    im = im.convert('RGB')
                    im.thumbnail((size, size))
                    buf = _io.BytesIO()
                    im.save(buf, 'JPEG', quality=80)
                return base64.b64encode(buf.getvalue()).decode('ascii')
            except Exception:
                return None
    return None

def _visual_local_check():
    """Erreur (code) si la recherche par photo ne peut pas tourner : IA coupée, ou fournisseur en ligne (on garde les images en local)."""
    if not is_ai_enabled():
        return 'ai_disabled'
    if get_ai_provider() != 'ollama':
        return 'local_only'
    return ''

def _visual_library_paths():
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
    except Exception:
        return []
    out = []
    for fobj in (cache.get('files') if isinstance(cache, dict) else None) or []:
        p = (fobj.get('path') or '').replace('\\', '/')
        if p and not is_virtual_archive_path(p):
            out.append(p)
    return out

def _visual_index_worker(user_id, paths):
    model = (load_settings() or {}).get('ollama_model') or ''
    try:
        for p in paths:
            if _visual_state['stop']:
                break
            mode = _visual_state['mode']
            while not _visual_state['stop']:   # patiente tant que l'utilisateur ou la machine a besoin du CPU
                if _thumb_paused:
                    why = 'paused'
                elif mode == 'gentle' and _user_is_active():
                    why = 'active'
                else:
                    why = _visual_machine_busy()
                _visual_state['waiting'] = why
                if not why:
                    break
                time.sleep(2)
            if _visual_state['stop']:
                break
            if _low_memory():
                _visual_state['error'] = 'low_memory'
                break
            b64 = _visual_thumb_b64(p)
            _visual_state['current'] = os.path.basename(p)
            if not b64:
                continue
            t0 = time.time()
            try:
                with _visual_call_lock:
                    text, source = _call_ai(_VISUAL_PROMPT, system=_VISUAL_SYSTEM, num_predict=70, temperature=0.1,
                                            images=[b64], extra_options=_visual_ollama_opts(mode), keep_alive='30s')
            except AIDisabledError:
                _visual_state['error'] = 'ai_disabled'
                break
            except Exception as e:
                _visual_state['error'] = 'ai_error'
                app_logger.info(f"[VisualIndex] Arrêt : {e}")
                break
            if source == 'ollama_no_vision':
                _visual_state['error'] = 'no_vision'
                break
            caption = ', '.join(sorted(_visual_tokens(text)))[:300]
            if caption:
                conn = get_db()
                try:
                    conn.execute("""INSERT INTO visual_index (file_path, user_id, caption, model) VALUES (?,?,?,?)
                                    ON CONFLICT(file_path, user_id) DO UPDATE SET caption=excluded.caption, model=excluded.model, indexed_at=CURRENT_TIMESTAMP""",
                                 (p, user_id, caption, model))
                    conn.commit()
                finally:
                    conn.close()
            _visual_state['done'] += 1
            # cycle de service : on dort aussi longtemps que l'appel (≈ 50 % de CPU max en mode doux, ≈ 25 % en rapide)
            time.sleep(max(0.5, (time.time() - t0) * (1.0 if mode == 'gentle' else 0.3)))
    finally:
        _visual_state['running'] = False
        _visual_state['current'] = ''
        _visual_state['waiting'] = ''
        _visual_unload_model()
        _trim_memory(force=True)

def _visual_counts(user_id):
    paths = [p for p in _visual_library_paths() if _has_thumb_on_disk(p)]
    conn = get_db()
    try:
        have = {r['file_path'] for r in conn.execute("SELECT file_path FROM visual_index WHERE user_id=?", (user_id,)).fetchall()}
    finally:
        conn.close()
    return paths, have

def api_photo_index_status():
    paths, have = _visual_counts(session['user_id'])
    return jsonify({"total": len(paths), "indexed": sum(1 for p in paths if p in have),
                    "running": _visual_state['running'], "run_done": _visual_state['done'], "run_total": _visual_state['total'],
                    "error": _visual_state['error'], "current": _visual_state['current'],
                    "waiting": _visual_state['waiting'], "mode": _visual_state['mode'],
                    "blocked": _visual_local_check()}), 200

def api_photo_index_control():
    data = request.get_json(silent=True) or {}
    if data.get('action') == 'stop':
        _visual_state['stop'] = True
        return jsonify({"success": True}), 200
    blocked = _visual_local_check()
    if blocked:
        return jsonify({"success": False, "error": blocked}), 403
    user_id = session['user_id']
    with _visual_lock:
        if _visual_state['running']:
            return jsonify({"success": True, "already": True}), 200
        paths, have = _visual_counts(user_id)
        todo = [p for p in paths if p not in have]
        try:
            limit = int(data.get('limit') or 0)
        except (TypeError, ValueError):
            limit = 0
        if limit > 0:
            todo = todo[:limit]
        _visual_state.update(running=True, stop=False, done=0, total=len(todo), error='', current='', waiting='',
                             mode='fast' if data.get('mode') == 'fast' else 'gentle')
    if not todo:
        _visual_state['running'] = False
        return jsonify({"success": True, "total": 0}), 200
    threading.Thread(target=_visual_index_worker, args=(user_id, todo), daemon=True, name='visual-index').start()
    return jsonify({"success": True, "total": len(todo)}), 200

def api_photo_search():
    """Reçoit une photo (data-URL ou base64) ; renvoie les chemins de la bibliothèque les plus ressemblants."""
    blocked = _visual_local_check()
    if blocked:
        return jsonify({"error": blocked}), 403
    data = request.get_json(silent=True) or {}
    raw = str(data.get('image') or '')
    if ',' in raw[:80]:
        raw = raw.split(',', 1)[1]
    if len(raw) < 100 or len(raw) > 6_000_000:
        return jsonify({"error": "bad_image"}), 400
    try:
        base64.b64decode(raw, validate=True)
    except Exception:
        return jsonify({"error": "bad_image"}), 400
    user_id = session['user_id']
    conn = get_db()
    try:
        rows = conn.execute("SELECT file_path, caption FROM visual_index WHERE user_id=?", (user_id,)).fetchall()
    finally:
        conn.close()
    if not rows:
        return jsonify({"error": "not_indexed"}), 409
    if _low_memory():
        return jsonify({"error": "low_memory"}), 503
    try:
        with _visual_call_lock:
            text, source = _call_ai(_VISUAL_PROMPT, system=_VISUAL_SYSTEM, num_predict=70, temperature=0.1, images=[raw],
                                    extra_options=_visual_ollama_opts('gentle'),
                                    keep_alive='30s' if _visual_state['running'] else 0)
    except AIDisabledError:
        return jsonify({"error": "ai_disabled"}), 403
    except RuntimeError as e:
        return jsonify({"error": "ai_error", "detail": str(e)[:200]}), 503
    if source == 'ollama_no_vision':
        return jsonify({"error": "no_vision"}), 422
    qtok = _visual_tokens(text)
    if not qtok:
        return jsonify({"results": [], "keywords": []}), 200
    docs = {r['file_path']: _visual_tokens(r['caption']) for r in rows}
    n = len(docs)
    df = {}
    for toks in docs.values():
        for t in toks:
            df[t] = df.get(t, 0) + 1
    scored = []
    for p, toks in docs.items():
        common = qtok & toks
        if not common:
            continue
        score = sum(math.log(1 + n / df[t]) for t in common) / math.sqrt(len(toks) or 1)
        scored.append((score, p))
    scored.sort(reverse=True)
    return jsonify({"results": [p for _s, p in scored[:30]], "keywords": sorted(qtok)}), 200


_ROUTES = (
    ('/api/ai/photo-index', ['GET'], 'api_photo_index_status', ('login_required', )),
    ('/api/ai/photo-index', ['POST'], 'api_photo_index_control', ('login_required', )),
    ('/api/ai/photo-search', ['POST'], 'api_photo_search', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"photo_search.init : services manquants : {missing}")
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
