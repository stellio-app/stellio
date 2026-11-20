"""Stellio — page « BigPrint » (Outils) : mise à l'échelle grandeur nature + découpe en pièces (v1.1.4)

Intègre le moteur open source **bigprint** (Michael Christopher Stone, licence AGPL‑3.0‑or‑later, https://github.com/PooterTF/bigprint),
copié tel quel dans le dossier `bigprint/` à la racine du projet (voir `bigprint/NOTICE-STELLIO.md`).

Ce module ne contient que la « colle » : sessions par utilisateur, routes Flask `/api/bigprint/*`, lecture d'un modèle depuis la
bibliothèque (dossier local ou partage SMB) et copie des fichiers générés dans le dossier choisi.
Le calcul tourne dans un processus séparé (annulable instantanément, un plantage de la bibliothèque native n'arrête pas Stellio).

Module séparé de main.py (même schéma que merge_3mf.py) : main.py appelle `bigprint_tool.init(globals())`.
"""
import os
import re
import shutil
import sys
import threading
import time

_REQUIRED = (
    'DATA_DIR',
    '_is_path_within_sources',
    '_smb_kwargs_for_path',
    'app',
    'app_logger',
    'get_db',
    'invalidate_cache',
    'jsonify',
    'login_required',
    'request',
    'send_file',
    'session',
    'smbclient',
)
_OPTIONAL = ('_ensure_optional_module',)
_OVERRIDABLE = ('os', 'shutil', 'time')

_MAIN = {}
DATA_DIR = None
_is_path_within_sources = None
_smb_kwargs_for_path = None
app = None
app_logger = None
get_db = None
invalidate_cache = None
jsonify = None
login_required = None
request = None
send_file = None
session = None
smbclient = None
_ensure_optional_module = None

MODEL_EXTS = ('.stl', '.3mf', '.obj', '.ply')
IDLE_SECONDS = 30 * 60          # une session inactive depuis 30 min est fermée (processus + fichiers temporaires)
MAX_MODEL_BYTES = 1 << 30       # 1 Go

_SESSIONS = {}                  # user_id -> {'session': bigprint.gui.Session, 'touched': float}
_SESSIONS_LOCK = threading.Lock()
# Limites réservées aux comptes invités / à la démo publique (le calcul est coûteux : on évite qu'un visiteur ou un robot sature le serveur)
VIEWER_MAX_MODEL_BYTES = 30 << 20      # modèle de 30 Mo maximum
VIEWER_MAX_ACTIVE = 2                  # calculs simultanés, tous visiteurs confondus
VIEWER_MAX_SESSIONS = 20               # sessions BigPrint de visiteurs ouvertes en même temps
VIEWER_COOLDOWN_S = 20                 # délai minimum entre deux aperçus d'un même visiteur
VIEWER_PER_HOUR = 12                   # aperçus par heure et par visiteur
VIEWER_IP_PER_HOUR = 40                # aperçus par heure et par adresse IP (plusieurs navigateurs = même personne)
VIEWER_JOB_TIMEOUT_S = 120             # un calcul de visiteur est annulé au bout de 2 min
_VIEWER_HITS = {}                      # clé (visiteur ou IP) -> horodatages des aperçus de la dernière heure
_COPY = {}                      # user_id -> {'state': 'copying'|'done'|'error', 'folder': str, 'error': str} (copie des fichiers vers la destination)


def _engine():
    """Importe le moteur à la demande (manifold3d, scipy… ne sont chargés que si la page est utilisée).
    Un module manquant est d'abord réinstallé automatiquement (version empaquetée) puis l'import est retenté."""
    def _load():
        from bigprint import gui as bp_gui
        from bigprint import strategy as bp_strategy
        from bigprint import printers as bp_printers
        return bp_gui, bp_strategy, bp_printers
    try:
        return _load()
    except ImportError as first:
        missing = getattr(first, 'name', '') or ''
        if missing.split('.')[0] == 'bigprint':
            raise RuntimeError("le moteur BigPrint (dossier « bigprint ») est absent de cette installation. Réinstallez Stellio avec la dernière version.")
        pip_name = {'skimage': 'scikit-image'}.get(missing.split('.')[0], missing.split('.')[0])
        if pip_name and _ensure_optional_module:
            try:
                if _ensure_optional_module(missing, pip_name):
                    return _load()
            except Exception:
                pass
        raise RuntimeError(f"module Python manquant « {missing or first} ». Installez-le (pip install manifold3d scipy scikit-image) puis relancez Stellio.")
    except Exception as e:
        raise RuntimeError(f"{e}")


def _is_unc(path):
    return path.startswith('//') or path.startswith('\\\\')


def _unc(path):
    return path.replace('\\', '/')


def _is_viewer():
    return session.get('role') == 'viewer'


def _sess_key():
    """Clé de session BigPrint : l'utilisateur ; pour un invité / la démo, un identifiant propre au navigateur
    (tous les visiteurs de la démo partagent le même compte : sans cela ils verraient les modèles et aperçus des autres)."""
    if _is_viewer():
        import uuid
        if 'bp_vid' not in session:
            session['bp_vid'] = uuid.uuid4().hex
        return ('viewer', session['bp_vid'])
    return session['user_id']


def _viewer_preview_allowed():
    """None si l'aperçu d'un invité peut démarrer, sinon (message, code HTTP)."""
    now = time.time()
    key_v, key_ip = ('v', _sess_key()), ('ip', request.remote_addr or '?')
    with _SESSIONS_LOCK:
        active = sum(1 for k, e in _SESSIONS.items() if isinstance(k, tuple) and e['session'].busy())
        for k in list(_VIEWER_HITS):
            _VIEWER_HITS[k] = [t for t in _VIEWER_HITS[k] if now - t < 3600]
            if not _VIEWER_HITS[k]:
                del _VIEWER_HITS[k]
        mine, ip = _VIEWER_HITS.get(key_v, []), _VIEWER_HITS.get(key_ip, [])
        if mine and now - mine[-1] < VIEWER_COOLDOWN_S:
            return f"Démo : patientez {int(VIEWER_COOLDOWN_S - (now - mine[-1])) + 1} s avant un nouvel aperçu", 429
        if len(mine) >= VIEWER_PER_HOUR or len(ip) >= VIEWER_IP_PER_HOUR:
            return "Démo : limite d'aperçus atteinte pour cette heure, réessayez plus tard", 429
        if active >= VIEWER_MAX_ACTIVE:
            return "Démo : le serveur est occupé par d'autres visiteurs, réessayez dans un instant", 429
        _VIEWER_HITS.setdefault(key_v, []).append(now)
        _VIEWER_HITS.setdefault(key_ip, []).append(now)
    return None


def _reap_idle():
    now = time.monotonic()
    with _SESSIONS_LOCK:
        for uid in list(_SESSIONS):
            entry = _SESSIONS[uid]
            sess = entry['session']
            if now - entry['touched'] > IDLE_SECONDS and not sess.busy():
                _SESSIONS.pop(uid, None)
                try:
                    sess.close()
                except Exception:
                    pass


def _get_session():
    """Session BigPrint de l'utilisateur connecté (créée à la demande, sans processus « de réserve » pour économiser la mémoire)."""
    bp_gui, _s, _p = _engine()
    _reap_idle()
    uid = _sess_key()
    with _SESSIONS_LOCK:
        entry = _SESSIONS.get(uid)
        if entry is None:
            if isinstance(uid, tuple) and sum(1 for k in _SESSIONS if isinstance(k, tuple)) >= VIEWER_MAX_SESSIONS:
                raise RuntimeError("Démo : trop de visiteurs en ce moment, réessayez dans quelques minutes")
            entry = {'session': bp_gui.Session(warm_spare=False), 'touched': time.monotonic()}
            _SESSIONS[uid] = entry
        entry['touched'] = time.monotonic()
        return entry['session']


def _spawn_safely(fn):
    """Lance un processus « spawn » sans que Python ne ré‑importe le script principal de Stellio dans le processus enfant
    (en développement, `python main.py` serait sinon réexécuté ; dans l'exécutable, c'est sans effet)."""
    main_mod = sys.modules.get('__main__')
    saved = {}
    if main_mod is not None:
        for attr in ('__spec__', '__file__'):
            if hasattr(main_mod, attr):
                saved[attr] = getattr(main_mod, attr)
        main_mod.__spec__ = None
        if hasattr(main_mod, '__file__'):
            try:
                del main_mod.__file__
            except AttributeError:
                pass
    try:
        return fn()
    finally:
        if main_mod is not None:
            for attr, val in saved.items():
                setattr(main_mod, attr, val)


def _read_library_file(path, max_bytes=None):
    """Octets d'un fichier de la bibliothèque (local ou SMB)."""
    if not isinstance(path, str) or not path:
        raise ValueError("Chemin invalide")
    if not _is_path_within_sources(path, session['user_id']):
        raise ValueError("Fichier hors des sources de la bibliothèque")
    ext = os.path.splitext(path)[1].lower()
    if ext not in MODEL_EXTS:
        raise ValueError("Format non pris en charge (STL, 3MF, OBJ ou PLY)")
    cap = min(max_bytes or MAX_MODEL_BYTES, MAX_MODEL_BYTES)
    too_big = f"Fichier trop volumineux (maximum {cap >> 20} Mo{' en démo' if max_bytes else ''})" if max_bytes else "Fichier trop volumineux (maximum 1 Go)"
    if _is_unc(path):
        kw = _smb_kwargs_for_path(session['user_id'], path)
        if kw is None:
            raise ValueError("Source réseau introuvable pour ce fichier")
        with smbclient.open_file(_unc(path), mode='rb', share_access='r', **kw) as fh:
            data = fh.read(cap + 1)
    else:
        if not os.path.isfile(path):
            raise ValueError("Fichier introuvable")
        if os.path.getsize(path) > cap:
            raise ValueError(too_big)
        with open(path, 'rb') as fh:
            data = fh.read()
    if len(data) > cap:
        raise ValueError(too_big)
    return data


def _clean_folder_name(name):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', (name or '').strip()).strip('. ')
    return name[:120]


def _dest_dir(source_id, sub_rel, folder_name):
    """Dossier final : source choisie + sous‑dossier + dossier « <modèle>_bigprint ».
    Sans source, les fichiers sont écrits dans le dossier de données de Stellio (`bigprint_output`)."""
    parts = [x for x in (sub_rel or '').replace('\\', '/').strip('/').split('/') if x]
    if any(x in ('.', '..') or re.search(r'[<>:"|?*]', x) for x in parts):
        raise ValueError("Dossier de destination invalide")
    parts.append(folder_name)
    if not source_id:
        folder = os.path.join(DATA_DIR, 'bigprint_output', *parts)
        os.makedirs(folder, exist_ok=True)
        return folder
    conn = get_db()
    try:
        row = conn.execute("SELECT path FROM sources WHERE id = ? AND user_id = ?", (source_id, session['user_id'])).fetchone()
    finally:
        conn.close()
    if not row or not row['path']:
        raise ValueError("Dossier de destination introuvable")
    base = row['path']
    if _is_unc(base):
        folder = '/'.join([_unc(base).rstrip('/')] + parts)
        kw = _smb_kwargs_for_path(session['user_id'], folder)
        if kw is None:
            raise ValueError("Source réseau introuvable pour ce dossier")
        smbclient.makedirs(folder, exist_ok=True, **kw)
    else:
        folder = os.path.join(base, *parts)
        os.makedirs(folder, exist_ok=True)
    return folder


def _deliver(tmp_dir, folder, uid):
    """Copie le contenu de `tmp_dir` dans `folder` (local ou SMB), sous‑dossiers compris."""
    if not _is_unc(folder):
        shutil.copytree(tmp_dir, folder, dirs_exist_ok=True)
        return
    kw = _smb_kwargs_for_path(uid, folder)
    if kw is None:
        raise ValueError("Source réseau introuvable pour ce dossier")
    for root, _dirs, files in os.walk(tmp_dir):
        rel = os.path.relpath(root, tmp_dir)
        target = folder if rel == '.' else folder.rstrip('/') + '/' + rel.replace(os.sep, '/')
        smbclient.makedirs(target, exist_ok=True, **kw)
        for name in files:
            with open(os.path.join(root, name), 'rb') as src, smbclient.open_file(target + '/' + name, mode='wb', **kw) as dst:
                shutil.copyfileobj(src, dst, 1 << 20)


# ── routes ────────────────────────────────────────────────────────────────

def _lang():
    """Langue demandée par l'interface (?lang=fr…) ; « en »/inconnue = textes d'origine du moteur."""
    from modules import bigprint_i18n
    return bigprint_i18n, (request.args.get('lang') or '')[:2].lower()


def api_bigprint_config():
    i18n, lang = _lang()
    try:
        bp_gui, bp_strategy, bp_printers = _engine()
    except RuntimeError as e:
        return jsonify({"available": False, "error": str(e)}), 200
    return jsonify({
        "available": True,
        "printers": {k: list(v) for k, v in bp_printers.PRINTERS.items()},
        "default_printer": bp_printers.DEFAULT_PRINTER,
        "materials": list(bp_strategy.MATERIAL_DENSITY),
        "purposes": list(bp_strategy.PURPOSES),
        "units": list(bp_gui.UNITS),
        "presets": {k: dict(zip(("label", "why"), i18n.preset(k, lang, p.label, p.why)), describe=i18n.describe(p.describe(), lang))
                    for k, p in bp_strategy.PURPOSES.items()},
        "source": "https://github.com/PooterTF/bigprint",
        "license": "AGPL-3.0-or-later",
    })


def api_bigprint_model():
    """Charge un modèle de la bibliothèque : {"path": "..."}."""
    data = request.json or {}
    try:
        bp_gui, _s, _p = _engine()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    try:
        sess = _get_session()
    except RuntimeError as e:   # démo : trop de visiteurs
        return jsonify({"error": str(e)}), 429
    if sess.busy():
        return jsonify({"error": "Un calcul est déjà en cours"}), 409
    try:
        raw = _read_library_file(data.get('path'), VIEWER_MAX_MODEL_BYTES if _is_viewer() else None)
        info = sess.add_model(os.path.basename(_unc(data['path'])), raw)
    except bp_gui.SettingsError as e:
        return jsonify({"error": str(e)}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app_logger.warning(f"[BigPrint] lecture du modèle impossible : {e}")
        return jsonify({"error": f"Lecture impossible : {e}"}), 500
    info = {k: v for k, v in info.items() if k != 'default_out'}
    info['stem'] = os.path.splitext(info['name'])[0]
    return jsonify(info)


def api_bigprint_upload():
    """Charge un modèle envoyé depuis le navigateur (corps brut, nom dans l'en‑tête X-Filename)."""
    if session.get('role') == 'viewer':   # démo publique / invité : aperçu seulement, aucun fichier ne sort ni n'entre
        return jsonify({"error": "Compte invité : lecture seule", "code": "viewer_readonly"}), 403
    from urllib.parse import unquote
    try:
        bp_gui, _s, _p = _engine()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    sess = _get_session()
    if sess.busy():
        return jsonify({"error": "Un calcul est déjà en cours"}), 409
    name = unquote(request.headers.get('X-Filename') or 'model.stl')
    if os.path.splitext(name)[1].lower() not in MODEL_EXTS:
        return jsonify({"error": "Format non pris en charge (STL, 3MF, OBJ ou PLY)"}), 400
    try:
        info = sess.add_model(name, request.get_data())
    except bp_gui.SettingsError as e:
        return jsonify({"error": str(e)}), 400
    info = {k: v for k, v in info.items() if k != 'default_out'}
    info['stem'] = os.path.splitext(info['name'])[0]
    return jsonify(info)


def api_bigprint_preview():
    data = request.json or {}
    try:
        bp_gui, _s, _p = _engine()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    try:
        sess = _get_session()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 429
    if _is_viewer() and not sess.busy():
        denied = _viewer_preview_allowed()
        if denied:
            return jsonify({"error": denied[0], "code": "viewer_limit"}), denied[1]
    try:
        with sess.lock:
            if sess.busy():
                raise bp_gui.SettingsError("Un calcul est déjà en cours")
            _spawn_safely(lambda: sess.start_preview(data.get('settings') or {}))
        if _is_viewer():
            _t = threading.Timer(VIEWER_JOB_TIMEOUT_S, lambda: sess.cancel())   # calcul d'invité trop long : annulé
            _t.daemon = True
            _t.start()
    except bp_gui.SettingsError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app_logger.warning(f"[BigPrint] démarrage impossible : {e}")
        return jsonify({"error": f"Démarrage impossible : {e}"}), 500
    return jsonify({"ok": True})


def api_bigprint_job():
    i18n, lang = _lang()
    sess = _get_session()
    uid = session['user_id']
    with sess.lock:
        job = sess.job.to_json() if sess.job else None
        summary = sess.summary
        key = sess.result_key
    cp = _COPY.get(uid)
    if job and job.get('kind') == 'save' and cp:
        # Le calcul est fini mais les fichiers ne sont pas encore tous copiés dans le dossier choisi : la page attend.
        if cp['state'] == 'copying' and job['state'] == 'done':
            job['state'], job['stage'], job['fraction'] = 'running', 'Copie des fichiers…', 0.97
        elif cp['state'] == 'done':
            job['out'] = cp['folder']
        elif cp['state'] == 'error':
            job['state'], job['error'] = 'error', cp['error']
    return jsonify({"job": i18n.job_log(job, lang), "summary": i18n.summary(summary, lang), "result_key": key})


def api_bigprint_cancel():
    _get_session().cancel()
    return jsonify({"ok": True})


def api_bigprint_preview_html():
    i18n, lang = _lang()
    sess = _get_session()
    if not sess.preview_path.exists():
        return "Aucun aperçu", 404
    from flask import Response
    html = i18n.preview_html(sess.preview_path.read_text(encoding='utf-8'), lang)
    resp = Response(html.encode('utf-8'), mimetype='text/html')
    # L'aperçu embarque three.js (import map en data:) : on lui donne sa propre politique, plus étroite que celle de Stellio.
    resp.headers['Content-Security-Policy'] = "default-src 'none'; script-src 'unsafe-inline' data:; style-src 'unsafe-inline'; img-src data: blob:"
    resp.headers['Cache-Control'] = 'no-store'
    return resp


def api_bigprint_save():
    """Écrit les fichiers (pièces STL, project.3mf, goujons, rapport, aperçu) dans le dossier choisi.
    Corps : {settings, source_id?, target_subfolder?, folder_name?}."""
    if session.get('role') == 'viewer':   # démo publique / invité : aperçu seulement, aucun fichier ne sort ni n'entre
        return jsonify({"error": "Compte invité : lecture seule", "code": "viewer_readonly"}), 403
    data = request.json or {}
    try:
        bp_gui, _s, _p = _engine()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    sess = _get_session()
    settings = data.get('settings') or {}
    model = sess.models.get(settings.get('model_id', ''))
    stem = os.path.splitext(model['name'])[0] if model else 'modele'
    folder_name = _clean_folder_name(data.get('folder_name')) or _clean_folder_name(stem) or 'modele'
    if not folder_name.lower().endswith('_bigprint'):
        folder_name += '_bigprint'   # suffixe obligatoire : il sert au badge BigPrint de la bibliothèque
    try:
        folder = _dest_dir(str(data.get('source_id') or '').strip() or None, data.get('target_subfolder'), folder_name)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Dossier de destination inutilisable : {e}"}), 500
    # Le moteur écrit d'abord dans un dossier temporaire local ; on copie ensuite (local ou SMB).
    tmp = os.path.join(sess.workdir, 'out')
    shutil.rmtree(tmp, ignore_errors=True)
    try:
        with sess.lock:
            if sess.busy():
                raise bp_gui.SettingsError("Un calcul est déjà en cours")
            sess.start_save(settings, tmp)
    except bp_gui.SettingsError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Enregistrement impossible : {e}"}), 500
    uid = session['user_id']   # `session` (Flask) n'existe pas hors requête : on capture l'identifiant
    _COPY[uid] = {'state': 'copying', 'folder': folder, 'error': ''}
    # La copie vers la destination est faite par le thread ci‑dessous dès que l'écriture locale est terminée.
    def _finish():
        deadline = time.monotonic() + 3600
        while time.monotonic() < deadline:
            with sess.lock:
                job = sess.job
                state = job.state if job else 'error'
            if state == 'running':
                time.sleep(0.3)
                continue
            if state != 'done':
                _COPY.pop(uid, None)
                return
            try:
                _deliver(tmp, folder, uid)
                _COPY[uid] = {'state': 'done', 'folder': folder, 'error': ''}
                try:
                    invalidate_cache()
                except Exception:
                    pass
            except Exception as e:
                app_logger.warning(f"[BigPrint] copie vers {folder} impossible : {e}")
                _COPY[uid] = {'state': 'error', 'folder': folder, 'error': f"Copie vers le dossier impossible : {e}"}
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
            return
        _COPY.pop(uid, None)

    threading.Thread(target=_finish, daemon=True).start()
    return jsonify({"ok": True, "folder": folder})


def api_bigprint_close():
    uid = _sess_key()
    with _SESSIONS_LOCK:
        entry = _SESSIONS.pop(uid, None)
    if entry:
        try:
            entry['session'].close()
        except Exception:
            pass
    return jsonify({"ok": True})


def ui_bigprint_script():
    """Script de la page BigPrint : fourni par le plugin (la page n'existe que s'il est activé)."""
    return send_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bigprint.js'), mimetype='application/javascript')


_ROUTES = (
    ('/bigprint.js', ['GET'], 'ui_bigprint_script', ()),
    ('/api/bigprint/config', ['GET'], 'api_bigprint_config', ('login_required', )),
    ('/api/bigprint/model', ['POST'], 'api_bigprint_model', ('login_required', )),
    ('/api/bigprint/upload', ['POST'], 'api_bigprint_upload', ('login_required', )),
    ('/api/bigprint/preview', ['POST'], 'api_bigprint_preview', ('login_required', )),
    ('/api/bigprint/job', ['GET'], 'api_bigprint_job', ('login_required', )),
    ('/api/bigprint/cancel', ['POST'], 'api_bigprint_cancel', ('login_required', )),
    ('/api/bigprint/preview.html', ['GET'], 'api_bigprint_preview_html', ('login_required', )),
    ('/api/bigprint/save', ['POST'], 'api_bigprint_save', ('login_required', )),
    ('/api/bigprint/close', ['POST'], 'api_bigprint_close', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"bigprint_tool.init : services manquants : {missing}")
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
