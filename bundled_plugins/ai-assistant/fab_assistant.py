"""Stellio — assistant de fabrication (1.1.7) : diagnostic d'échecs, choix de matière, réglages éprouvés, pièces voisines.

Prolonge l'assistant de bibliothèque (1.1.7) sans lui retirer ses garanties : même principe de CATALOGUE FERMÉ. L'IA, si elle est configurée,
ne fait que CHOISIR une analyse du catalogue et ses paramètres (validés) ; sinon un routeur à règles (fr/en) choisit. Les analyses sont en
LECTURE SEULE et calculées sur VOS impressions : aucune donnée n'est inventée. Les pistes de correction proposées (`ADVICE`) sont des conseils
généraux d'impression 3D rattachés au motif de l'échec noté, présentés comme des pistes, pas comme un diagnostic certain.
Les seules écritures possibles sont des PROPOSITIONS (poser une étiquette) que l'utilisateur doit CONFIRMER une par une (`POST /api/fab/apply`, confirm: true).
Moins de 3 impressions dans un groupe : aucune conclusion statistique n'est tirée.
"""
import json
import math
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
_OPTIONAL = ('_call_ai', 'is_ai_enabled')
_OVERRIDABLE = ('os',)

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

MIN_GROUP = 3
GAP_POINTS = 15                 # écart de taux d'échec (points) qui rend un facteur « à surveiller »
MAX_QUESTION = 400
MATERIALS = ('PLA', 'PETG', 'ABS', 'ASA', 'TPU', 'NYLON', 'PA', 'PC', 'PVA', 'HIPS')

QUERIES = {
    'diagnose_failure': {'doc': "Analyse les impressions ratées (éventuellement d'un modèle, d'une imprimante, d'une matière) : motifs fréquents, facteurs qui "
                                "dépassent la moyenne d'échec, pistes de correction.",
                         'params': {'model': {'type': 'str', 'max': 80}, 'printer_id': {'type': 'int'}, 'material': {'type': 'str', 'max': 20}}},
    'suggest_material': {'doc': "Classe les matières par fiabilité pour un modèle (et, si possible, ses pièces de forme proche), en écartant celles que l'imprimante ne supporte pas.",
                         'params': {'model': {'type': 'str', 'max': 80, 'required': True}, 'printer_id': {'type': 'int'}}},
    'suggest_settings': {'doc': "Réglages qui ont réussi pour un modèle : températures moyennes, profil de slicer le plus utilisé, matière et imprimante les plus fiables.",
                         'params': {'model': {'type': 'str', 'max': 80, 'required': True}}},
    'similar_models': {'doc': "Modèles de forme proche d'un modèle donné, avec leur taux de réussite.",
                       'params': {'model': {'type': 'str', 'max': 80, 'required': True}}},
}

# (motifs dans la raison d'échec, pistes générales)
ADVICE = (
    (('warp', 'décoll', 'decoll', 'adh', 'bed', 'plateau', 'curl'),
     ["Nettoyer le plateau (alcool isopropylique) et vérifier le réglage de la première couche.", "Augmenter la température du plateau de 5 °C.",
      "Ajouter une bordure (brim) ou un radeau.", "Éviter les courants d'air ; caisson fermé pour ABS / ASA / nylon."]),
    (('string', 'filant', 'suint', 'blob', 'oozing'),
     ["Sécher le filament (humidité).", "Baisser la température de 5 à 10 °C.", "Augmenter la rétractation ou la distance de retrait."]),
    (('sous-extr', 'sous extr', 'under', 'clog', 'bouch', 'extru', 'jam'),
     ["Vérifier que la buse n'est pas partiellement bouchée (nettoyage à chaud).", "Augmenter la température de 5 à 10 °C ou réduire la vitesse.", "Contrôler le diamètre du filament et le débit."]),
    (('shift', 'décal', 'decal', 'layer', 'couche'),
     ["Contrôler la tension des courroies et les vis des poulies.", "Réduire vitesse et accélérations.", "Vérifier qu'aucun câble ne frotte."]),
    (('spaghetti', 'détach', 'detach', 'tomb', 'fell', 'knock'),
     ["Améliorer l'adhérence de la première couche.", "Ajouter des supports ou réorienter la pièce.", "Réduire la hauteur de couche des pièces élancées."]),
    (('support',), ["Réorienter la pièce pour limiter les supports.", "Régler la distance d'interface des supports."]),
    (('coupure', 'power', 'panne', 'électr', 'electr'), ["Prévoir un onduleur ou une prise surveillée.", "Activer la reprise après coupure si l'imprimante le permet."]),
)
GENERIC_ADVICE = ["Noter la raison de chaque échec (bouton « Noter l'impression ») : sans motif, aucune piste précise n'est possible."]


def wilson_lower(success, n, z=1.96):
    """Borne basse de l'intervalle de Wilson : classement fiable même avec peu d'impressions."""
    if n <= 0:
        return 0.0
    p = success / n
    d = 1 + z * z / n
    return (p + z * z / (2 * n) - z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)) / d


def advice_for(reasons):
    """Pistes pour une liste de raisons d'échec (texte libre) : [{'reason', 'count', 'tips'}] du plus fréquent au moins fréquent."""
    counts = {}
    for r in reasons:
        t = re.sub(r'\s+', ' ', str(r or '').strip().lower())
        if t:
            counts[t] = counts.get(t, 0) + 1
    out = []
    for text, n in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        tips = next((t for keys, t in ADVICE if any(k in text for k in keys)), None)
        out.append({'reason': text, 'count': n, 'tips': tips or []})
    return out


def factor_gaps(rows, baseline, keys=('material', 'printer', 'nozzle_band')):
    """rows : [{'failed': bool, 'material', 'printer', 'nozzle_band'}]. Facteurs dont le taux d'échec dépasse la moyenne de GAP_POINTS points
    (au moins MIN_GROUP impressions). Retourne [{'factor','value','prints','failed','rate','gap'}] trié par écart."""
    out = []
    for k in keys:
        groups = {}
        for r in rows:
            v = r.get(k)
            if v in (None, ''):
                continue
            g = groups.setdefault(v, [0, 0])
            g[0] += 1
            g[1] += 1 if r['failed'] else 0
        for v, (n, f) in groups.items():
            if n < MIN_GROUP:
                continue
            rate = 100 * f / n
            if rate - baseline >= GAP_POINTS:
                out.append({'factor': k, 'value': v, 'prints': n, 'failed': f, 'rate': round(rate, 1), 'gap': round(rate - baseline, 1)})
    return sorted(out, key=lambda x: (-x['gap'], x['factor'], str(x['value'])))


def nozzle_band(t):
    if not t:
        return None
    lo = int(t // 10 * 10)
    return f"{lo}–{lo + 9} °C"


# ── validation du catalogue ──

def validate_call(query_id, params, printer_ids=None):
    if query_id not in QUERIES:
        raise ValueError('unknown_query')
    schema, clean = QUERIES[query_id]['params'], {}
    for k, v in (params if isinstance(params, dict) else {}).items():
        spec = schema.get(k)
        if not spec or v in (None, ''):
            continue
        try:
            if spec['type'] == 'int':
                if isinstance(v, bool):
                    continue
                clean[k] = int(float(str(v)))
            else:
                s = re.sub(r'\s+', ' ', str(v)).strip()[:spec.get('max', 60)]
                if s:
                    clean[k] = s
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


def route_rules(question, printers, model_names=()):
    q = ' ' + re.sub(r'\s+', ' ', str(question or '').lower()) + ' '
    params = {}
    model = next((n for n in sorted(model_names, key=len, reverse=True) if len(n) >= 3 and n.lower() in q), None)
    printer = next((p for p in printers if p['name'] and p['name'].lower() in q), None)
    mats = [m for m in MATERIALS if re.search(r'(?<![a-z])' + m.lower() + r'(?![a-z])', q)]
    if model:
        params['model'] = model
    if printer:
        params['printer_id'] = printer['id']
    if mats:
        params['material'] = mats[0]
    has = lambda *w: any(x in q for x in w)
    if has('similaire', 'ressemble', 'proche', 'similar', 'looks like') and model:
        return 'similar_models', {'model': model}
    if has('quelle matière', 'quelle matiere', 'which material', 'matière pour', 'matiere pour', 'material for') and model:
        return 'suggest_material', {k: v for k, v in params.items() if k in ('model', 'printer_id')}
    if has('réglage', 'reglage', 'température', 'temperature', 'settings', 'profil', 'profile') and model:
        return 'suggest_settings', {'model': model}
    return 'diagnose_failure', params


# ── analyses (lecture seule, limitées au compte) ──

def _norm(p):
    return str(p or '').strip().replace('\\', '/')


def _cols(conn):
    return {r[1] for r in conn.execute("PRAGMA table_info(print_history)").fetchall()}


def _history(conn, uid, model=None, printer_id=None, material=None):
    have = _cols(conn)
    sel = ["h.id", "h.file_path", "h.file_name", "h.result", "h.printer_id", "h.filament_material", "h.failure_reason", "h.slicer_profile_name"]
    sel += [f"h.{c}" if c in have else f"NULL AS {c}" for c in ('nozzle_temp', 'bed_temp')]
    sql, args = f"SELECT {', '.join(sel)}, p.name AS printer FROM print_history h LEFT JOIN printers p ON p.id = h.printer_id WHERE h.user_id = ? AND h.result IN ('success','failed','partial')", [uid]
    if printer_id:
        sql += " AND h.printer_id = ?"
        args.append(printer_id)
    if material:
        sql += " AND UPPER(COALESCE(h.filament_material,'')) LIKE ?"
        args.append('%' + material.upper() + '%')
    rows = [dict(r) for r in conn.execute(sql + " ORDER BY h.id DESC LIMIT 5000", args).fetchall()]
    if model:
        m = model.lower()
        rows = [r for r in rows if m in os.path.basename(_norm(r['file_path'])).lower() or m in str(r['file_name'] or '').lower()]
    return rows


def q_diagnose_failure(conn, uid, p):
    rows = _history(conn, uid, p.get('model'), p.get('printer_id'), p.get('material'))
    n = len(rows)
    failed = [r for r in rows if r['result'] == 'failed']
    notes = []
    if n < MIN_GROUP:
        return {'rows': [], 'summary': {'rated': n, 'failed': len(failed)}, 'notes': [f"Seulement {n} impression(s) notée(s) : trop peu pour une analyse (minimum {MIN_GROUP})."], 'tips': [], 'proposals': []}
    baseline = 100 * len(failed) / n
    data = [{'failed': r['result'] == 'failed', 'material': (r['filament_material'] or '').upper() or None, 'printer': r['printer'], 'nozzle_band': nozzle_band(r.get('nozzle_temp'))} for r in rows]
    gaps = factor_gaps(data, baseline)
    reasons = advice_for([r['failure_reason'] for r in failed])
    if failed and not reasons:
        notes.append("Aucune raison d'échec n'est notée : les pistes restent générales.")
    if not any(r.get('nozzle_temp') for r in rows):
        notes.append("Températures réelles absentes : lancez « Compléter l'historique » pour les lire dans les G-code.")
    proposals = []
    if p.get('model'):
        for g in gaps[:2]:
            if g['factor'] == 'material':
                path = next((r['file_path'] for r in rows), None)
                if path:
                    proposals.append({'action': 'tag', 'path': path, 'target': f"Fragile en {g['value']}"[:40], 'label': f"Étiqueter « Fragile en {g['value']} »"})
    return {'summary': {'rated': n, 'failed': len(failed), 'failure_rate': round(baseline, 1)}, 'rows': gaps, 'tips': reasons[:5], 'notes': notes, 'proposals': proposals}


def _model_rows(conn, uid, model):
    rows = _history(conn, uid, model)
    paths = {}
    for r in rows:
        paths.setdefault(_norm(r['file_path']), []).append(r)
    return rows, paths


def q_suggest_material(conn, uid, p):
    rows, _paths = _model_rows(conn, uid, p['model'])
    notes = []
    by = {}
    for r in rows:
        m = (r['filament_material'] or '').upper().strip()
        if m:
            g = by.setdefault(m, [0, 0])
            g[0] += 1
            g[1] += 1 if r['result'] == 'success' else 0
    out = [{'material': m, 'prints': n, 'success': s, 'rate': round(100 * s / n, 1), 'score': round(100 * wilson_lower(s, n), 1), 'source': 'ce modèle'} for m, (n, s) in by.items()]
    try:                                   # pièces de forme proche : leur matière compte aussi (marquée comme telle)
        from modules import shape_search
        names = {_norm(r['file_path']) for r in rows}
        if names:
            ref = conn.execute("SELECT desc FROM shape_index WHERE user_id = ? AND path IN (%s) LIMIT 1" % ','.join('?' * len(names)), [uid, *names]).fetchone()
            if ref:
                cands = {r['path']: json.loads(r['desc']) for r in conn.execute("SELECT path, desc FROM shape_index WHERE user_id = ?", (uid,)).fetchall() if r['path'] not in names}
                close = {x['path'] for x in shape_search.rank(json.loads(ref['desc']), cands, 5) if x['similarity'] >= 85}
                seen = {o['material'] for o in out}
                nb = {}
                for r in _history(conn, uid):
                    if _norm(r['file_path']) in close and r['filament_material']:
                        g = nb.setdefault(r['filament_material'].upper(), [0, 0])
                        g[0] += 1
                        g[1] += 1 if r['result'] == 'success' else 0
                for m, (n, s) in nb.items():
                    if m not in seen:
                        out.append({'material': m, 'prints': n, 'success': s, 'rate': round(100 * s / n, 1), 'score': round(100 * wilson_lower(s, n), 1), 'source': 'pièces de forme proche'})
    except Exception:
        pass
    if p.get('printer_id'):
        try:
            from modules import compat
            specs = next((x['specs'] for x in compat.printers_specs(conn, uid) if x['id'] == p['printer_id']), None)
            kept = []
            for o in out:
                st = compat.check(None, o['material'], specs or {})['status'] if specs is not None else 'unknown'
                if st == 'fail':
                    notes.append(f"{o['material']} écarté : incompatible avec cette imprimante.")
                else:
                    kept.append(o)
            out = kept
        except Exception:
            pass
    if not out:
        notes.append('Aucune impression de ce modèle avec une matière renseignée.')
    out.sort(key=lambda o: (-o['score'], o['material']))
    return {'rows': out, 'notes': notes, 'summary': {'model': p['model']}, 'proposals': []}


def q_suggest_settings(conn, uid, p):
    rows, _ = _model_rows(conn, uid, p['model'])
    ok = [r for r in rows if r['result'] == 'success']
    notes = []
    if not ok:
        return {'rows': [], 'notes': ['Aucune impression réussie notée pour ce modèle.'], 'summary': {'model': p['model'], 'successes': 0}, 'proposals': []}
    avg = lambda key: round(sum(r[key] for r in ok if r.get(key)) / max(1, len([r for r in ok if r.get(key)])), 1) if any(r.get(key) for r in ok) else None
    top = lambda key: max(({r[key] for r in ok if r.get(key)} or {None}), key=lambda v: sum(1 for r in ok if r.get(key) == v)) if any(r.get(key) for r in ok) else None
    out = [{'setting': 'Température de buse moyenne (°C)', 'value': avg('nozzle_temp')}, {'setting': 'Température du plateau moyenne (°C)', 'value': avg('bed_temp')},
           {'setting': 'Profil de slicer le plus utilisé', 'value': top('slicer_profile_name')}, {'setting': 'Matière la plus utilisée', 'value': (top('filament_material') or None)},
           {'setting': 'Imprimante la plus utilisée', 'value': top('printer')}]
    if avg('nozzle_temp') is None:
        notes.append("Températures non enregistrées : « Compléter l'historique » les lit dans les G-code.")
    return {'rows': [o for o in out if o['value'] is not None], 'notes': notes, 'summary': {'model': p['model'], 'successes': len(ok), 'rated': len(rows)}, 'proposals': []}


def q_similar_models(conn, uid, p):
    try:
        from modules import shape_search
    except Exception:
        return {'rows': [], 'notes': ['Recherche de formes indisponible.'], 'summary': {}, 'proposals': []}
    shape_search._ensure(conn)
    m = p['model'].lower()
    row = next((r for r in conn.execute("SELECT path, desc FROM shape_index WHERE user_id = ?", (uid,)).fetchall() if m in os.path.basename(r['path']).lower()), None)
    if not row:
        return {'rows': [], 'notes': ["Modèle absent de l'index de formes : lancez l'indexation (Atelier avancé › Pièces similaires)."], 'summary': {}, 'proposals': []}
    cands = {r['path']: json.loads(r['desc']) for r in conn.execute("SELECT path, desc FROM shape_index WHERE user_id = ? AND path <> ?", (uid, row['path'])).fetchall()}
    hist = {}
    for r in _history(conn, uid):
        g = hist.setdefault(_norm(r['file_path']), [0, 0])
        g[0] += 1
        g[1] += 1 if r['result'] == 'success' else 0
    out = []
    for x in shape_search.rank(json.loads(row['desc']), cands, 10):
        n, s = hist.get(x['path'], (0, 0))
        out.append({'name': os.path.basename(x['path']), 'path': x['path'], 'similarity': x['similarity'], 'prints': n, 'rate': round(100 * s / n, 1) if n >= 1 else None})
    return {'rows': out, 'notes': [], 'summary': {'model': os.path.basename(row['path'])}, 'proposals': []}


_RUNNERS = {'diagnose_failure': q_diagnose_failure, 'suggest_material': q_suggest_material, 'suggest_settings': q_suggest_settings, 'similar_models': q_similar_models}


def parse_ai_reply(text):
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


def build_prompt(question, printers):
    cat = '\n'.join(f"- {qid} : {q['doc']} Paramètres : {', '.join(q['params'])}." for qid, q in QUERIES.items())
    pr = '; '.join(f"id {p['id']} = {p['name']}" for p in printers) or 'aucune'
    return ("Tu aides à comprendre des impressions 3D. Tu ne peux PAS écrire de requête : tu choisis UNE analyse dans cette liste.\n" + cat +
            f"\nImprimantes : {pr}.\nRéponds uniquement par un objet JSON : {{\"query\": \"<identifiant>\", \"params\": {{…}}}}.\n\nQuestion : " + str(question)[:MAX_QUESTION])


def _printers(conn, uid):
    return [{'id': r['id'], 'name': r['name'] or f"#{r['id']}"} for r in conn.execute("SELECT id, name FROM printers WHERE user_id = ? ORDER BY id", (uid,)).fetchall()]


def ask(conn, uid, question, ai_choose=None, model_names=()):
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
        except Exception:
            note = 'ai_error'
    if via != 'ai':
        query_id, params = route_rules(q, printers, model_names)
        try:
            query_id, params = validate_call(query_id, params, pids)
        except ValueError as e:
            return {'query': None, 'params': {}, 'via': via, 'error': str(e), 'rows': [], 'notes': [], 'ai_note': note}
    res = _RUNNERS[query_id](conn, uid, params)
    res.update({'query': query_id, 'params': params, 'via': via, 'ai_note': note})
    return res


def _no_viewer():
    if session.get('role') == 'viewer' and not _demo_ok():
        return jsonify({'error': 'Réservé au compte propriétaire.', 'code': 'viewer_forbidden'}), 403
    return None


def api_fab_queries():
    r = _no_viewer()
    if r:
        return r
    return jsonify({'queries': [{'id': k, 'doc': v['doc'], 'params': v['params']} for k, v in QUERIES.items()]})


def api_fab_ask():
    r = _no_viewer()
    if r:
        return r
    d = request.get_json(silent=True) or {}
    uid = session['user_id']
    conn = get_db()
    try:
        if d.get('query'):
            try:
                qid, params = validate_call(str(d['query']), d.get('params') or {}, {p['id'] for p in _printers(conn, uid)})
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
            res = _RUNNERS[qid](conn, uid, params)
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
        names = sorted({os.path.splitext(os.path.basename(_norm(r['file_path'])))[0] for r in conn.execute("SELECT DISTINCT file_path FROM print_history WHERE user_id = ? LIMIT 2000", (uid,)).fetchall()})
        return jsonify(ask(conn, uid, question, choose, names))
    finally:
        conn.close()


def api_fab_apply():
    """Applique UNE proposition (étiquette), seulement avec confirm: true."""
    r = _no_viewer()
    if r:
        return r
    d = request.get_json(silent=True) or {}
    if d.get('confirm') is not True:
        return jsonify({'error': 'Confirmation requise (confirm: true).'}), 400
    uid = session['user_id']
    path, target = str(d.get('path') or ''), str(d.get('target') or '').strip()
    if d.get('action') != 'tag' or not target or len(target) > 40 or not path or not _is_path_within_sources(path, uid):
        return jsonify({'error': 'Proposition invalide.'}), 400
    conn = get_db()
    try:
        conn.executescript("CREATE TABLE IF NOT EXISTS tags (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, color TEXT DEFAULT '#4ea1d3');"
                           "CREATE TABLE IF NOT EXISTS file_tags (file_path TEXT NOT NULL, tag_id INTEGER NOT NULL, PRIMARY KEY (file_path, tag_id));")
        row = conn.execute("SELECT id FROM tags WHERE lower(name) = lower(?)", (target,)).fetchone()
        tid = row[0] if row else conn.execute("INSERT INTO tags (name) VALUES (?)", (target,)).lastrowid
        conn.execute("INSERT OR IGNORE INTO file_tags (file_path, tag_id) VALUES (?,?)", (_norm(path), tid))
        conn.commit()
        return jsonify({'ok': True})
    finally:
        conn.close()


_DEMO_COMPUTE = ('/api/plate/arrange', '/api/organize/preview', '/api/model-diff')


def _demo_ok():
    """Démo publique (lecture seule, `IS_DEMO` posé par la surcouche de démo) : consultation (GET) et calculs sans écriture."""
    try:
        return bool(_MAIN.get('IS_DEMO')) and (request.method in ('GET', 'HEAD') or request.path in _DEMO_COMPUTE)
    except Exception:
        return False


_ROUTES = (
    ('/api/fab/queries', ['GET'], 'api_fab_queries', ('login_required', )),
    ('/api/fab/ask', ['POST'], 'api_fab_ask', ('login_required', )),
    ('/api/fab/apply', ['POST'], 'api_fab_apply', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"{__name__}.init : services manquants : {missing}")
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
