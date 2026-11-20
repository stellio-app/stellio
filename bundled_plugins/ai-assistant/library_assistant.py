"""Stellio — assistant de bibliothèque (v1.1.7) : poser une question qui croise bibliothèque, imprimantes, matières et historique.

Principe de sécurité : le modèle d'IA ne touche JAMAIS à la base. Il ne fait que CHOISIR, dans un catalogue fermé de requêtes
prédéfinies (`QUERIES`), laquelle répond à la question et avec quels paramètres. Sa réponse est ensuite validée : identifiant connu,
paramètres convertis et bornés selon le schéma du catalogue, imprimante vérifiée parmi celles du compte. Tout ce qui sort du schéma
est écarté. Les requêtes elles-mêmes sont écrites ici, paramétrées et limitées au compte connecté ; aucune ne modifie de donnée.
Sans IA configurée (ou si elle échoue), un routeur à règles (mots-clés, noms d'imprimantes, de matières et de modèles) choisit à sa place.

Réutilise la traçabilité de la 1.1.6/1.1.7 : « meilleur réglage » = meilleure combinaison version + profil (borne basse de Wilson).

Module séparé de main.py (même schéma que webhooks.py) : main.py appelle `library_assistant.init(globals())`. Les fonctions pures
(`fits_bed`, `validate_call`, `route_rules`, `parse_ai_reply`, `build_prompt`) sont testées sans base ni IA.
"""
import json
import os
import re

_REQUIRED = (
    '_is_path_within_sources',
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'session',
)
_OPTIONAL = ('_call_ai', 'is_ai_enabled', '_read_cache_json_safe', '_bulk_source_scope')
_OVERRIDABLE = ('json', 'os')

_MAIN = {}
_is_path_within_sources = None
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None
_call_ai = None
is_ai_enabled = None
_read_cache_json_safe = None
_bulk_source_scope = None

MESH_EXT = ('.stl', '.3mf', '.obj', '.ply', '.off')
MATERIALS = ('PLA', 'PETG', 'ABS', 'ASA', 'TPU', 'NYLON', 'PA', 'PC', 'PVA', 'HIPS')
MAX_QUESTION = 400
DEFAULT_LIMIT = 20
MAX_LIMIT = 50
MIN_RATED = 2                      # impressions notées minimum pour parler d'un taux de réussite

# Catalogue fermé : identifiant → description (montrée au modèle) et schéma des paramètres.
# type : int / str / enum ; les bornes servent à la validation.
QUERIES = {
    'find_models': {
        'doc': "Cherche des modèles de la bibliothèque en croisant des critères : tient sur une imprimante (volume d'impression), déjà imprimé "
               "dans une matière, jamais imprimé, taux de réussite minimal, partie du nom.",
        'params': {
            'printer_id': {'type': 'int', 'doc': "imprimante sur laquelle le modèle doit tenir (id de la liste fournie)"},
            'material': {'type': 'str', 'max': 20, 'doc': 'matière déjà utilisée pour imprimer le modèle (PLA, PETG…)'},
            'printed': {'type': 'enum', 'values': ('yes', 'no'), 'doc': "yes = déjà imprimé, no = jamais imprimé (dans la matière si elle est donnée)"},
            'min_rate': {'type': 'int', 'min': 1, 'max': 100, 'doc': 'taux de réussite minimal en %, avec au moins 2 impressions notées'},
            'name': {'type': 'str', 'max': 60, 'doc': 'texte contenu dans le nom du fichier'},
            'limit': {'type': 'int', 'min': 1, 'max': MAX_LIMIT, 'doc': 'nombre de résultats'},
        }},
    'best_setup': {
        'doc': "Meilleure combinaison version du modèle + profil de slicer pour un modèle donné (d'après les impressions notées).",
        'params': {'model': {'type': 'str', 'max': 80, 'required': True, 'doc': 'nom (ou partie du nom) du modèle'}}},
    'most_failed': {
        'doc': 'Modèles qui échouent le plus (taux de réussite le plus bas, au moins 2 impressions notées).',
        'params': {'limit': {'type': 'int', 'min': 1, 'max': MAX_LIMIT, 'doc': 'nombre de résultats'}}},
    'most_reliable': {
        'doc': 'Modèles les plus fiables (meilleur taux de réussite, classement prudent avec peu d\'impressions).',
        'params': {'material': {'type': 'str', 'max': 20, 'doc': 'limiter à une matière'},
                   'limit': {'type': 'int', 'min': 1, 'max': MAX_LIMIT, 'doc': 'nombre de résultats'}}},
    'recent_prints': {
        'doc': 'Impressions récentes.',
        'params': {'days': {'type': 'int', 'min': 1, 'max': 365, 'doc': 'sur les N derniers jours (défaut 30)'},
                   'printer_id': {'type': 'int', 'doc': 'limiter à une imprimante'},
                   'limit': {'type': 'int', 'min': 1, 'max': MAX_LIMIT, 'doc': 'nombre de résultats'}}},
    'printer_usage': {
        'doc': 'Utilisation de chaque imprimante : nombre d\'impressions, réussites, échecs.',
        'params': {}},
}


# ── fonctions pures ───────────────────────────────────────────────────────

def catalog(printers=None):
    """Catalogue présentable (pour l'interface et pour le modèle)."""
    return [{'id': qid, 'doc': q['doc'], 'params': {k: {kk: vv for kk, vv in v.items()} for k, v in q['params'].items()}} for qid, q in QUERIES.items()]


def fits_bed(dims, bed):
    """Le modèle (x, y, z) tient-il dans le volume (bx, by, bz) dans une orientation à plat quelconque ?
    Compare les dimensions triées : sûr pour les rotations à 90°, sans prétendre à l'orientation optimale."""
    try:
        d = sorted(float(dims[k]) for k in ('x', 'y', 'z')) if isinstance(dims, dict) else sorted(float(v) for v in dims)
        b = sorted(float(v) for v in bed)
    except (TypeError, ValueError, KeyError):
        return False
    if len(d) != 3 or len(b) != 3 or min(b) <= 0:
        return False
    return all(di <= bi for di, bi in zip(d, b))


def _coerce(spec, value):
    t = spec['type']
    if t == 'int':
        if isinstance(value, bool):
            raise ValueError
        n = int(float(str(value).strip().rstrip('%')))
        lo, hi = spec.get('min', -10 ** 9), spec.get('max', 10 ** 9)
        return max(lo, min(hi, n))
    if t == 'str':
        s = re.sub(r'\s+', ' ', str(value)).strip()[:spec.get('max', 60)]
        if not s:
            raise ValueError
        return s
    if t == 'enum':
        s = str(value).strip().lower()
        if s not in spec['values']:
            raise ValueError
        return s
    raise ValueError


def validate_call(query_id, params, printer_ids=None):
    """(requête, paramètres propres) ou lève ValueError. Tout ce qui n'est pas dans le catalogue est refusé ou écarté :
    identifiant inconnu → erreur ; paramètre inconnu ou invalide → ignoré ; paramètre obligatoire absent → erreur ;
    imprimante qui n'est pas celle du compte → erreur."""
    if query_id not in QUERIES:
        raise ValueError('unknown_query')
    schema = QUERIES[query_id]['params']
    clean = {}
    for k, v in (params if isinstance(params, dict) else {}).items():
        if k not in schema or v in (None, ''):
            continue
        try:
            clean[k] = _coerce(schema[k], v)
        except (ValueError, TypeError):
            continue
    for k, spec in schema.items():
        if spec.get('required') and k not in clean:
            raise ValueError(f'missing_{k}')
    if 'printer_id' in clean and printer_ids is not None and clean['printer_id'] not in printer_ids:
        raise ValueError('unknown_printer')
    if 'material' in clean:
        clean['material'] = clean['material'].upper()
    return query_id, clean


def build_prompt(question, printers, models=None):
    """Consigne donnée à l'IA : catalogue + imprimantes du compte + question ; elle doit répondre par un seul objet JSON."""
    cat = []
    for q in catalog():
        ps = '; '.join(f"{k} ({v['type']}{'/' + '|'.join(v['values']) if v.get('values') else ''}): {v['doc']}" for k, v in q['params'].items()) or 'aucun paramètre'
        cat.append(f"- {q['id']} : {q['doc']} Paramètres : {ps}.")
    pr = '; '.join(f"id {p['id']} = {p['name']}" for p in printers) or 'aucune'
    return ("Tu aides à interroger une bibliothèque de modèles 3D. Tu ne peux PAS écrire de requête : tu choisis UNE requête dans cette liste "
            "et ses paramètres.\n" + '\n'.join(cat) + f"\nImprimantes du compte : {pr}.\nMatières courantes : {', '.join(MATERIALS)}.\n"
            "Réponds uniquement par un objet JSON, sans texte autour : {\"query\": \"<identifiant>\", \"params\": {…}}. "
            "N'invente aucun paramètre ; omets ceux qui ne sont pas dans la question.\n\nQuestion : " + str(question)[:MAX_QUESTION])


def parse_ai_reply(text):
    """Extrait {"query", "params"} de la réponse du modèle (tolère le texte autour ou un bloc de code) ; None si inexploitable."""
    t = str(text or '')
    start = t.find('{')
    while start != -1:
        depth = 0
        for i in range(start, len(t)):
            depth += (t[i] == '{') - (t[i] == '}')
            if depth == 0:
                try:
                    d = json.loads(t[start:i + 1])
                    if isinstance(d, dict) and isinstance(d.get('query'), str):
                        return {'query': d['query'].strip(), 'params': d.get('params') if isinstance(d.get('params'), dict) else {}}
                except ValueError:
                    pass
                break
        start = t.find('{', start + 1)
    return None


def _has(text, *words):
    return any(re.search(r'\b' + re.escape(w), text) for w in words)


def route_rules(question, printers, model_names=()):
    """Routeur sans IA : (requête, paramètres). Reconnaît mots-clés (fr/en), imprimante, matière et modèle cités dans la question."""
    q = ' ' + re.sub(r'\s+', ' ', str(question or '').lower()) + ' '
    params = {}
    mats = [m for m in MATERIALS if re.search(r'(?<![a-z])' + m.lower() + r'(?![a-z])', q)]
    printer = next((p for p in printers if p['name'] and p['name'].lower() in q), None)
    model = next((n for n in sorted(model_names, key=len, reverse=True) if len(n) >= 3 and n.lower() in q), None)
    n = re.search(r'\b(\d{1,3})\s*(?:%|pour ?cent|percent)', q)
    days = re.search(r'(\d{1,3})\s*(?:derniers?\s+)?(?:jours?|days?)', q)
    if model and _has(q, 'meilleur', 'meilleure', 'réglage', 'reglage', 'profil', 'version', 'best', 'setup', 'settings', 'comment'):
        return 'best_setup', {'model': model}
    if _has(q, 'échou', 'echou', 'raté', 'rate ', 'rates', 'fail', 'problème', 'probleme') and not _has(q, 'jamais', 'never'):
        return 'most_failed', {}
    if _has(q, 'utilisation', 'usage', 'utilisée', 'utilisee', 'charge de') and (_has(q, 'imprimante', 'printer', 'machine') or printer):
        return 'printer_usage', {}
    if _has(q, 'récent', 'recent', 'dernier', 'dernière', 'derniere', 'last', 'latest') and not _has(q, 'jamais', 'never'):
        if days:
            params['days'] = days.group(1)
        if printer:
            params['printer_id'] = printer['id']
        return 'recent_prints', params
    if _has(q, 'fiable', 'fiables', 'reliable', 'fiabilité', 'fiabilite') and not _has(q, 'jamais', 'never'):
        if mats:
            params['material'] = mats[0]
        return 'most_reliable', params
    # par défaut : recherche croisée de modèles
    if printer:
        params['printer_id'] = printer['id']
    if mats:
        params['material'] = mats[0]
    if _has(q, 'jamais', 'never', 'pas encore', 'not yet', 'untested', 'non testé', 'non teste'):
        params['printed'] = 'no'
    elif _has(q, 'déjà', 'deja', 'already', 'imprimé', 'imprime', 'printed') or mats:
        params['printed'] = 'yes'
    if n and _has(q, 'réussite', 'reussite', 'success', 'fiab', 'reliab', 'taux', 'rate'):
        params['min_rate'] = n.group(1)
    if model and not params:
        params['name'] = model
    return 'find_models', params


# ── requêtes (lecture seule, limitées au compte) ───────────────────────────

def _norm(p):
    return (p or '').strip().replace('\\', '/')


def _limit(params, default=DEFAULT_LIMIT):
    return max(1, min(int(params.get('limit') or default), MAX_LIMIT))


def _library_meshes(uid):
    data = _read_cache_json_safe() if _read_cache_json_safe else None
    out = []
    import contextlib
    with (_bulk_source_scope() if _bulk_source_scope else contextlib.nullcontext()):
        for f in (data or {}).get('files', []):
            p = f.get('path') or ''
            if os.path.splitext(p)[1].lower() in MESH_EXT and _is_path_within_sources(p, uid):
                out.append({'path': _norm(p), 'name': f.get('name') or os.path.basename(p)})
    return out


def _printers(conn, uid):
    rows = conn.execute("SELECT id, name, config FROM printers WHERE user_id = ? ORDER BY id", (uid,)).fetchall()
    out = []
    for r in rows:
        bed = None
        try:
            cfg = json.loads(r['config'] or '{}')
            b = [float(cfg.get('bed_x') or 0), float(cfg.get('bed_y') or 0), float(cfg.get('bed_z') or 0)]
            bed = b if all(v > 0 for v in b) else None
        except (ValueError, TypeError):
            bed = None
        out.append({'id': r['id'], 'name': r['name'] or f"#{r['id']}", 'bed': bed})
    return out


def _stats_by_model(conn, uid, material=None, printer_id=None, since=None):
    """Par modèle (fichier ou, quand il est connu, modèle de la traçabilité) : impressions, notées, réussites, dernière date."""
    sql = ("SELECT COALESCE(t.model_path, h.file_path) AS mp, h.result, h.sent_at FROM print_history h "
           "LEFT JOIN print_trace t ON t.history_id = h.id WHERE h.user_id = ?")
    args = [uid]
    if material:
        sql += " AND UPPER(COALESCE(h.filament_material, '')) LIKE ?"
        args.append('%' + material.upper() + '%')
    if printer_id:
        sql += " AND h.printer_id = ?"
        args.append(printer_id)
    if since:
        sql += " AND h.sent_at >= ?"
        args.append(since)
    stats = {}
    for r in conn.execute(sql, args).fetchall():
        k = _norm(r['mp'])
        s = stats.setdefault(k, {'prints': 0, 'rated': 0, 'success': 0, 'failed': 0, 'last': ''})
        s['prints'] += 1
        if r['result'] in ('success', 'failed', 'partial'):
            s['rated'] += 1
            if r['result'] == 'success':
                s['success'] += 1
            elif r['result'] == 'failed':
                s['failed'] += 1
        s['last'] = max(s['last'], str(r['sent_at'] or ''))
    for s in stats.values():
        s['rate'] = round(s['success'] / s['rated'], 3) if s['rated'] >= MIN_RATED else None
    return stats


def _dims(conn, paths):
    out = {}
    paths = list(paths)
    for i in range(0, len(paths), 400):
        chunk = paths[i:i + 400]
        for r in conn.execute("SELECT path, data FROM file_analysis WHERE failed = 0 AND path IN (%s)" % ','.join('?' * len(chunk)), chunk).fetchall():
            try:
                d = json.loads(r['data'] or '{}').get('dimensions')
                if d and all(k in d for k in ('x', 'y', 'z')):
                    out[_norm(r['path'])] = d
            except (ValueError, AttributeError):
                pass
    return out


def q_find_models(conn, uid, p):
    notes = []
    files = _library_meshes(uid)
    printers = {x['id']: x for x in _printers(conn, uid)}
    dims = {}
    if p.get('printer_id'):
        pr = printers.get(p['printer_id'])
        if not pr or not pr['bed']:
            return {'rows': [], 'notes': ['bed_unknown'], 'printer': pr['name'] if pr else None}
        dims = _dims(conn, [f['path'] for f in files])
        files = [f for f in files if f['path'] in dims and fits_bed(dims[f['path']], pr['bed'])] if dims else []
        unk = sum(1 for f in _library_meshes(uid) if f['path'] not in dims)
        if unk:
            notes.append(f'dims_unknown:{unk}')
    stats = _stats_by_model(conn, uid, material=p.get('material'))
    needle = (p.get('name') or '').lower()
    rows = []
    for f in files:
        s = stats.get(f['path'], {'prints': 0, 'rated': 0, 'success': 0, 'failed': 0, 'last': '', 'rate': None})
        if needle and needle not in f['name'].lower():
            continue
        if p.get('printed') == 'yes' and s['prints'] == 0:
            continue
        if p.get('printed') == 'no' and s['prints'] > 0:
            continue
        if p.get('material') and not p.get('printed') and s['prints'] == 0:
            continue                                     # « imprimés en PETG » : au moins une impression dans cette matière
        if p.get('min_rate') and (s['rate'] is None or s['rate'] * 100 < p['min_rate']):
            continue
        rows.append({'name': f['name'], 'path': f['path'], 'dims': dims.get(f['path']), 'prints': s['prints'], 'success': s['success'],
                     'failed': s['failed'], 'rate': s['rate'], 'last': s['last']})
    rows.sort(key=lambda r: (-(r['rate'] if r['rate'] is not None else -1), -r['prints'], r['name'].lower()))
    return {'rows': rows[:_limit(p)], 'total': len(rows), 'notes': notes}


def q_best_setup(conn, uid, p):
    try:
        from modules import print_traceability as pt
    except Exception:
        return {'rows': [], 'notes': ['trace_unavailable']}
    needle = p['model'].lower()
    rows = [dict(r) for r in conn.execute(
        "SELECT t.model_path, t.model_version, t.profile_fp, h.result, h.slicer_profile_name AS profile_name, h.sent_at "
        "FROM print_trace t JOIN print_history h ON h.id = t.history_id WHERE t.user_id = ? AND h.user_id = ?", (uid, uid)).fetchall()]
    rows = [r for r in rows if needle in os.path.basename(_norm(r['model_path'])).lower()]
    if not rows:
        return {'rows': [], 'notes': ['no_data']}
    by = {}
    for r in rows:
        by.setdefault(_norm(r['model_path']), []).append(r)
    path, mrows = max(by.items(), key=lambda kv: len(kv[1]))
    combos = pt.aggregate(mrows)
    best = pt.pick_best(combos)
    out = []
    for c in combos[:8]:
        out.append({'model': os.path.basename(path), 'path': path, 'version': c['version'], 'profile': c['profile'], 'profile_fp': c['profile_fp'],
                    'success': c['success'], 'failed': c['failed'], 'total': c['total'], 'rate': c['rate'], 'confident': c['confident'],
                    'best': bool(best and c is best)})
    return {'rows': out, 'notes': ([] if best else ['no_best'])}


def _ranked(conn, uid, material=None, worst=False, limit=DEFAULT_LIMIT):
    from_files = {f['path']: f['name'] for f in _library_meshes(uid)}
    stats = _stats_by_model(conn, uid, material=material)
    rows = []
    for path, s in stats.items():
        if s['rated'] < MIN_RATED:
            continue
        rows.append({'name': from_files.get(path) or os.path.basename(path), 'path': path, 'prints': s['prints'], 'success': s['success'],
                     'failed': s['failed'], 'rate': s['rate'], 'last': s['last']})
    if worst:
        rows = [r for r in rows if r['failed'] > 0]
        rows.sort(key=lambda r: (r['rate'], -r['failed'], r['name'].lower()))
    else:
        try:
            from modules.print_traceability import wilson_low
        except Exception:
            def wilson_low(a, b):
                return a / b if b else 0
        rows.sort(key=lambda r: (-wilson_low(r['success'], r['success'] + r['failed']), -r['prints'], r['name'].lower()))
    return {'rows': rows[:limit], 'notes': [] if rows else ['no_data']}


def q_most_failed(conn, uid, p):
    return _ranked(conn, uid, worst=True, limit=_limit(p, 10))


def q_most_reliable(conn, uid, p):
    return _ranked(conn, uid, material=p.get('material'), limit=_limit(p, 10))


def q_recent_prints(conn, uid, p, now=None):
    import datetime
    now = now or datetime.datetime.now()
    since = (now - datetime.timedelta(days=p.get('days') or 30)).strftime('%Y-%m-%d %H:%M:%S')
    sql = "SELECT file_name, file_path, result, sent_at, filament_material, printer_id FROM print_history WHERE user_id = ? AND sent_at >= ?"
    args = [uid, since]
    if p.get('printer_id'):
        sql += " AND printer_id = ?"
        args.append(p['printer_id'])
    names = {x['id']: x['name'] for x in _printers(conn, uid)}
    rows = [{'name': r['file_name'] or os.path.basename(r['file_path'] or ''), 'path': _norm(r['file_path']), 'result': r['result'] or '', 'sent_at': r['sent_at'],
             'material': r['filament_material'] or '', 'printer': names.get(r['printer_id'], '')}
            for r in conn.execute(sql + " ORDER BY sent_at DESC LIMIT ?", args + [_limit(p)]).fetchall()]
    return {'rows': rows, 'notes': [] if rows else ['no_data']}


def q_printer_usage(conn, uid, p):
    rows = []
    for pr in _printers(conn, uid):
        r = conn.execute("SELECT COUNT(*) AS n, SUM(result = 'success') AS ok, SUM(result = 'failed') AS ko, MAX(sent_at) AS last "
                         "FROM print_history WHERE user_id = ? AND printer_id = ?", (uid, pr['id'])).fetchone()
        rated = (r['ok'] or 0) + (r['ko'] or 0)
        rows.append({'printer_id': pr['id'], 'name': pr['name'], 'prints': r['n'] or 0, 'success': r['ok'] or 0, 'failed': r['ko'] or 0,
                     'rate': round((r['ok'] or 0) / rated, 3) if rated >= MIN_RATED else None, 'last': r['last'] or ''})
    rows.sort(key=lambda r: -r['prints'])
    return {'rows': rows, 'notes': [] if rows else ['no_data']}


_RUNNERS = {'find_models': q_find_models, 'best_setup': q_best_setup, 'most_failed': q_most_failed, 'most_reliable': q_most_reliable,
            'recent_prints': q_recent_prints, 'printer_usage': q_printer_usage}


def run_query(conn, uid, query_id, params):
    """Exécute une requête DÉJÀ validée ; ne reçoit jamais de SQL, seulement un identifiant du catalogue."""
    return _RUNNERS[query_id](conn, uid, params)


def ask(conn, uid, question, ai_choose=None):
    """Question libre → (requête choisie, résultat). `ai_choose(prompt) -> texte` est appelé seulement si fourni ; en cas d'échec ou de
    réponse hors catalogue, le routeur à règles prend le relais."""
    q = str(question or '').strip()[:MAX_QUESTION]
    printers = _printers(conn, uid)
    pids = {p['id'] for p in printers}
    via, query_id, params, note = 'rules', None, {}, ''
    if ai_choose:
        try:
            choice = parse_ai_reply(ai_choose(build_prompt(q, printers)))
            if choice:
                query_id, params = validate_call(choice['query'], choice['params'], pids)
                via = 'ai'
            else:
                note = 'ai_unreadable'
        except ValueError as e:
            note = f'ai_rejected:{e}'
        except Exception as e:
            note = 'ai_error'
            try:
                app_logger.info(f"[ASSISTANT] IA indisponible : {type(e).__name__}")
            except Exception:
                pass
    if via != 'ai':
        names = [os.path.splitext(f['name'])[0] for f in _library_meshes(uid)]
        query_id, params = route_rules(q, printers, names)
        try:
            query_id, params = validate_call(query_id, params, pids)
        except ValueError as e:
            return {'query': None, 'params': {}, 'via': via, 'error': str(e), 'rows': [], 'notes': [], 'ai_note': note}
    res = run_query(conn, uid, query_id, params)
    res.update({'query': query_id, 'params': params, 'via': via, 'ai_note': note})
    return res


# ── routes ────────────────────────────────────────────────────────────────

def _no_viewer():
    if session.get('role') == 'viewer':
        return jsonify({'error': 'Réservé au compte propriétaire.'}), 403
    return None


def api_assistant_queries():
    r = _no_viewer()
    if r:
        return r
    conn = get_db()
    try:
        ps = _printers(conn, session['user_id'])
    finally:
        conn.close()
    ai = False
    try:
        ai = bool(is_ai_enabled and is_ai_enabled())
    except Exception:
        pass
    return jsonify({'queries': catalog(), 'printers': [{'id': p['id'], 'name': p['name'], 'has_bed': bool(p['bed'])} for p in ps],
                    'materials': list(MATERIALS), 'ai': ai})


def api_assistant_ask():
    r = _no_viewer()
    if r:
        return r
    d = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        uid = session['user_id']
        if d.get('query'):                                     # relance directe d'une requête du catalogue (pastilles, tri) : pas d'IA
            ps = {p['id'] for p in _printers(conn, uid)}
            try:
                qid, params = validate_call(str(d['query']), d.get('params') or {}, ps)
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
            res = run_query(conn, uid, qid, params)
            res.update({'query': qid, 'params': params, 'via': 'direct', 'ai_note': ''})
            return jsonify(res)
        question = str(d.get('question') or '').strip()
        if not question:
            return jsonify({'error': 'question_required'}), 400
        choose = None
        try:
            if _call_ai and is_ai_enabled and is_ai_enabled():
                choose = lambda prompt: _call_ai(prompt, num_predict=200, temperature=0.0)[0]
        except Exception:
            choose = None
        return jsonify(ask(conn, uid, question, choose))
    finally:
        conn.close()


_ROUTES = (
    ('/api/assistant/queries', ['GET'], 'api_assistant_queries', ('login_required', )),
    ('/api/assistant/ask', ['POST'], 'api_assistant_ask', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"library_assistant.init : services manquants : {missing}")
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
