"""Stellio — Fonctions IA : correction du temps d'impression, étiquettes auto, descriptions

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `ai_features.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import os
import re

_REQUIRED = (
    'AIDisabledError',
    'LANG_NAMES',
    '_call_ai',
    '_get_cached_slice_estimate_seconds',
    'app',
    'app_logger',
    'get_cached_3d_analysis',
    'get_db',
    'get_user_lang',
    'jsonify',
    'login_required',
    'request',
    'session',
)
_OPTIONAL = ()   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('os', 're', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
AIDisabledError = None
LANG_NAMES = None
_call_ai = None
_get_cached_slice_estimate_seconds = None
app = None
app_logger = None
get_cached_3d_analysis = None
get_db = None
get_user_lang = None
jsonify = None
login_required = None
request = None
session = None


MIN_SAMPLES_FOR_CORRECTION = 3

CORRECTION_FACTOR_BOUNDS = (0.5, 2.0)

def _get_print_time_correction_factor(user_id, printer_id=None, slicer_profile_id=None):
    conn = get_db()
    try:
        def _fetch(where_extra, params_extra):
            query = """SELECT estimated_seconds, actual_seconds FROM print_history
                       WHERE user_id=? AND estimated_seconds IS NOT NULL AND estimated_seconds > 0
                       AND actual_seconds IS NOT NULL AND actual_seconds > 0""" + where_extra
            return conn.execute(query, (user_id, *params_extra)).fetchall()

        rows, scope = [], 'global'
        if printer_id and slicer_profile_id:
            rows = _fetch(" AND printer_id=? AND slicer_profile_id=?", (printer_id, slicer_profile_id))
            scope = 'printer+profile'
        if len(rows) < MIN_SAMPLES_FOR_CORRECTION and printer_id:
            rows = _fetch(" AND printer_id=?", (printer_id,))
            scope = 'printer'
        if len(rows) < MIN_SAMPLES_FOR_CORRECTION:
            rows = _fetch("", ())
            scope = 'global'
    finally:
        conn.close()

    if len(rows) < MIN_SAMPLES_FOR_CORRECTION:
        return {'factor': 1.0, 'confidence': 'low', 'sample_size': len(rows), 'scope': scope}

    ratios = sorted(r['actual_seconds'] / r['estimated_seconds'] for r in rows)
    median = ratios[len(ratios) // 2] if len(ratios) % 2 == 1 else \
        (ratios[len(ratios) // 2 - 1] + ratios[len(ratios) // 2]) / 2
    factor = max(CORRECTION_FACTOR_BOUNDS[0], min(CORRECTION_FACTOR_BOUNDS[1], median))
    confidence = 'high' if len(rows) >= 10 else 'medium'
    return {'factor': round(factor, 3), 'confidence': confidence, 'sample_size': len(rows), 'scope': scope}

def _autofill_actual_print_time(user_id, printer_id, file_name, duration_seconds, finished_at=None):
    if not duration_seconds or duration_seconds < 60 or not file_name:
        return
    conn = get_db()
    try:
        row = conn.execute(
            """SELECT id FROM print_history
               WHERE user_id=? AND file_name=? AND actual_seconds IS NULL
               AND sent_at >= datetime('now', '-72 hours')
               ORDER BY sent_at DESC LIMIT 1""",
            (user_id, file_name)
        ).fetchone()
        if not row:
            return
        conn.execute(
            """UPDATE print_history SET actual_seconds=?, printer_id=COALESCE(printer_id, ?),
               time_recorded_at=CURRENT_TIMESTAMP WHERE id=?""",
            (duration_seconds, printer_id, row['id'])
        )
        conn.commit()
    except Exception as e:
        app_logger.info(f"[AI][PrintTime] autofill ignoré: {e}")
    finally:
        conn.close()

def api_ai_predict_print_time():
    data = request.json or {}
    file_path = (data.get('path') or '').strip()
    printer_id = data.get('printer_id')
    slicer_profile_id = data.get('slicer_profile_id')
    if not file_path:
        return jsonify({"error": "Chemin requis"}), 400

    estimated_seconds = _get_cached_slice_estimate_seconds(file_path.replace('\\', '/'))
    if estimated_seconds is None:
        return jsonify({"status": "pending",
                         "message": "Estimation du slicer pas encore disponible pour ce fichier."}), 202

    correction = _get_print_time_correction_factor(session['user_id'], printer_id, slicer_profile_id)
    corrected_seconds = int(estimated_seconds * correction['factor'])

    def _fmt(seconds):
        h, m = seconds // 3600, (seconds % 3600) // 60
        return f"{h}h {m}min" if h > 0 else f"{m}min"

    return jsonify({
        "status": "done",
        "estimated_seconds": int(estimated_seconds),
        "estimated_formatted": _fmt(int(estimated_seconds)),
        "corrected_seconds": corrected_seconds,
        "corrected_formatted": _fmt(corrected_seconds),
        "correction_factor": correction['factor'],
        "confidence": correction['confidence'],
        "sample_size": correction['sample_size'],
        "scope": correction['scope'],
    }), 200

def api_ollama_auto_tag():
    data          = request.json or {}
    filename      = (data.get('filename') or '').strip()
    existing_tags = data.get('existing_tags') or []

    if not filename:
        return jsonify({"error": "Nom de fichier requis"}), 400

    lang      = get_user_lang()
    lang_name = LANG_NAMES.get(lang, lang)
    existing_str = ', '.join(existing_tags[:15]) if existing_tags else 'none'

    prompt = (
        f"3D file: \"{filename}\"\n"
        f"Existing tags: {existing_str}\n"
        f"Give 3 to 5 short tags separated by commas. "
        f"Reply ONLY with the tags in {lang_name}, nothing else.\n"
        f"Example ({lang_name}): visserie, mecanique, support"
    )
    system = f"You generate short tags for a 3D printing file library. Always reply in {lang_name}."

    try:
        raw_text, source = _call_ai(prompt, system=system, num_predict=60)
        raw_tags = re.split(r'[, \n]', raw_text)
        tags = []
        for t in raw_tags:
            t = re.sub(r'^\d+[\.\)]\s*', '', t.strip().strip('.-•*').strip())
            if t and len(t) <= 30 and t.lower() not in [x.lower() for x in tags]:
                tags.append(t)
                if len(tags) >= 5:
                    break

        if not tags:
            return jsonify({"error": "L'IA n'a retourné aucun tag exploitable", "raw": raw_text}), 502

        return jsonify({"tags": tags, "source": source}), 200

    except AIDisabledError as e:
        return jsonify({"error": str(e), "ai_disabled": True}), 403
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        app_logger.error(f"[AutoTag] {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500

def api_ollama_explain_orientation():
    data = request.json or {}
    filename = (data.get('filename') or '').strip()
    suggestions = data.get('suggestions') or []
    if not suggestions:
        return jsonify({"error": "Aucune suggestion à expliquer"}), 400

    lang = get_user_lang()
    lang_name = LANG_NAMES.get(lang, lang)

    lines = []
    for i, s in enumerate(suggestions[:3]):
        lines.append(
            f"{i+1}. {s.get('key', '?')} — surplomb: {s.get('overhangPct', 0)}%, "
            f"contact plateau: {s.get('contactPct', 0)}%"
        )
    prompt = (
        f"3D print file: \"{filename}\"\n"
        f"Geometric analysis already computed locally (not by you) ranked these plate orientations, "
        f"best first:\n" + "\n".join(lines) +
        f"\nIn 2-3 short sentences, explain in {lang_name} why orientation #1 is the best choice here "
        f"(less overhang = less support material, more bed contact = better adhesion). "
        f"Reply ONLY with the explanation, in {lang_name}, no preamble."
    )
    system = f"You explain 3D printing orientation trade-offs simply, for a hobbyist. Always reply in {lang_name}."

    try:
        text, source = _call_ai(prompt, system=system, num_predict=180)
        return jsonify({"explanation": text, "source": source}), 200
    except AIDisabledError as e:
        return jsonify({"error": str(e), "ai_disabled": True}), 403
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        app_logger.error(f"[ExplainOrientation] {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500

def api_get_file_description():
    file_path = request.args.get('path', '').replace('\\', '/')
    if not file_path:
        return jsonify({"error": "Chemin requis"}), 400
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT description, generated_at FROM file_descriptions WHERE file_path=? AND user_id=?",
            (file_path, session['user_id'])
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return jsonify({"description": None}), 200
    return jsonify({"description": row["description"], "generated_at": row["generated_at"]}), 200

def api_ollama_describe_file():
    data = request.json or {}
    file_path = (data.get('path') or '').replace('\\', '/')
    if not file_path:
        return jsonify({"error": "Chemin requis"}), 400

    filename = os.path.basename(file_path)
    user_id = session['user_id']

    conn = get_db()
    tag_rows = conn.execute(
        "SELECT t.name FROM file_tags ft JOIN tags t ON ft.tag_id = t.id WHERE ft.file_path=?",
        (file_path,)
    ).fetchall()
    conn.close()
    tags = [r["name"] for r in tag_rows]

    geometry_bits = []
    try:
        analysis = get_cached_3d_analysis(file_path)
        if analysis:
            dims = analysis.get('dimensions') or {}
            if dims:
                geometry_bits.append(f"dimensions {dims.get('x')}x{dims.get('y')}x{dims.get('z')} mm")
            if analysis.get('volume_cm3'):
                geometry_bits.append(f"volume {analysis['volume_cm3']} cm3")
    except Exception:
        pass

    lang = get_user_lang()
    lang_name = LANG_NAMES.get(lang, lang)

    prompt = (
        f"3D printable file named \"{filename}\".\n"
        f"Tags: {', '.join(tags) if tags else 'none'}\n"
        f"Geometry: {', '.join(geometry_bits) if geometry_bits else 'unknown'}\n"
        f"Write a short, useful 1-2 sentence description of what this object likely is and what "
        f"it could be used for. Be concrete, avoid generic filler. Reply ONLY with the description "
        f"in {lang_name}, no preamble."
    )
    system = f"You write short, concrete descriptions for a 3D printing file library. Always reply in {lang_name}."

    try:
        description, source = _call_ai(prompt, system=system, num_predict=120)
        description = description.strip().strip('"')

        conn = get_db()
        conn.execute(
            """INSERT INTO file_descriptions (file_path, user_id, description, generated_at)
               VALUES (?, ?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(file_path, user_id) DO UPDATE SET description=excluded.description, generated_at=CURRENT_TIMESTAMP""",
            (file_path, user_id, description)
        )
        conn.commit()
        conn.close()

        return jsonify({"description": description, "source": source}), 200

    except AIDisabledError as e:
        return jsonify({"error": str(e), "ai_disabled": True}), 403
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        app_logger.error(f"[DescribeFile] {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500

MATERIAL_RANGES = {
    "PLA":  {"buse": "190-220°C", "plateau": "50-60°C",  "vitesse": "40-60 mm/s", "ventilation": "100%"},
    "PETG": {"buse": "230-250°C", "plateau": "70-80°C",  "vitesse": "30-50 mm/s", "ventilation": "30-50%"},
    "ABS":  {"buse": "230-250°C", "plateau": "95-110°C", "vitesse": "30-50 mm/s", "ventilation": "0-10%"},
    "TPU":  {"buse": "210-230°C", "plateau": "30-50°C",  "vitesse": "15-30 mm/s", "ventilation": "50-100%"},
}

def _material_ref_block(material: str) -> str:
    ref = MATERIAL_RANGES.get((material or "").upper())
    if ref:
        return (f"Normal settings for {material}: nozzle {ref['buse']}, "
                f"bed {ref['plateau']}, speed {ref['vitesse']}, fan {ref['ventilation']}.")
    return f"No known reference ranges for {material}: use general knowledge of this material."


_ROUTES = (
    ('/api/ai/predict-print-time', ['POST'], 'api_ai_predict_print_time', ('login_required', )),
    ('/api/ollama/auto-tag', ['POST'], 'api_ollama_auto_tag', ('login_required', )),
    ('/api/ollama/explain-orientation', ['POST'], 'api_ollama_explain_orientation', ('login_required', )),
    ('/api/file-description', ['GET'], 'api_get_file_description', ('login_required', )),
    ('/api/ollama/describe-file', ['POST'], 'api_ollama_describe_file', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"ai_features.init : services manquants : {missing}")
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
