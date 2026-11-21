"""Stellio Intelligence (v1.1.7) — recommandation de réglages et causes probables d'échec, apprises de TES impressions notées.

Ce n'est pas un modèle d'IA : ce sont des statistiques sur l'historique noté (réussite / échec / partiel, motif d'échec) croisées
avec les réglages des profils de slicer utilisés. Chaque conclusion dit sur combien d'impressions elle repose ; sous les seuils
(`MIN_SCOPE`, `MIN_FAILED`) le module répond « pas assez de données » plutôt que d'inventer. Ce sont des corrélations, pas des
preuves : une cause « probable » est une piste à vérifier.

  - `recommend(rows, profiles, material, printer_id, model_path)` : meilleur profil de slicer (borne basse de Wilson du taux de
    réussite), alternatives, profils à éviter, valeurs typiques des réglages numériques des impressions réussies.
  - `diagnose(rows, profiles, material, printer_id, model_path, target)` : causes probables classées (motifs déclarés + écarts de
    réglages entre impressions ratées et réussies + contexte : matière / imprimante / profil qui échouent plus que la moyenne).

Fonctions de calcul pures (testées sans base). Module séparé de main.py : `intelligence.init(globals())`.
"""
import math
import statistics

_REQUIRED = ('app', 'get_db', 'jsonify', 'login_required', 'request', 'session')
_OPTIONAL = ('app_logger', )
_OVERRIDABLE = ()

_MAIN = {}
app = None
get_db = None
jsonify = None
login_required = None
request = None
session = None
app_logger = None

RATED = ('success', 'failed', 'partial')
MIN_GLOBAL = 8           # impressions notées minimum pour que le module prétende « avoir appris » quelque chose
MIN_SCOPE = 3            # impressions notées minimum dans un périmètre pour recommander
MIN_BEST = 2             # impressions minimum d'un profil pour être proposé
MIN_PARAM_OK = 3         # réussites (avec ce réglage connu) minimum pour donner une valeur typique
MIN_FAILED = 2           # échecs minimum pour parler de causes
AVOID_MAX_RATE = 0.4     # un profil sous ce taux de réussite (avec ≥ 3 impressions) est déconseillé
LEAD_MIN_GAP = 0.25      # écart de taux d'échec avec la moyenne pour signaler un contexte
FB_MIN = 3               # retours « recommandation suivie » minimum pour corriger le classement (1.1.8)
FB_DEMOTE_RATE = 0.4     # une recommandation suivie qui réussit moins souvent que ça est rétrogradée
FB_PROMOTE_RATE = 0.8    # … et au-dessus de ça, légèrement favorisée
REASONS = ('warping', 'stringing', 'layer_shift', 'spaghetti', 'support_failure', 'adhesion', 'other')

# réglage → (unité, écart absolu minimum, écart relatif minimum) pour dire que deux groupes diffèrent
NUM_PARAMS = {
    'nozzle_temp': ('°C', 5.0, 0.0), 'bed_temp': ('°C', 5.0, 0.0), 'print_speed': ('mm/s', 0.0, 0.15), 'outer_wall_speed': ('mm/s', 0.0, 0.15),
    'inner_wall_speed': ('mm/s', 0.0, 0.15), 'infill_speed': ('mm/s', 0.0, 0.2), 'first_layer_speed': ('mm/s', 0.0, 0.2), 'travel_speed': ('mm/s', 0.0, 0.2),
    'layer_height': ('mm', 0.04, 0.0), 'retraction_distance': ('mm', 0.5, 0.0), 'retraction_speed': ('mm/s', 0.0, 0.25), 'fan_speed': ('%', 15.0, 0.0),
    'infill_density': ('%', 10.0, 0.0), 'wall_count': ('', 1.0, 0.0),
}
# (réglage, sens sur les impressions ratées) → causes que cet écart rend plausibles
HYPOTHESES = {
    ('nozzle_temp', 'lower'): ('adhesion', 'layer_shift'), ('nozzle_temp', 'higher'): ('stringing', ),
    ('bed_temp', 'lower'): ('adhesion', 'warping'), ('bed_temp', 'higher'): ('stringing', ),
    ('print_speed', 'higher'): ('layer_shift', 'spaghetti'), ('outer_wall_speed', 'higher'): ('layer_shift', 'spaghetti'),
    ('inner_wall_speed', 'higher'): ('layer_shift', ), ('travel_speed', 'higher'): ('layer_shift', 'stringing'),
    ('first_layer_speed', 'higher'): ('adhesion', 'warping'), ('retraction_distance', 'lower'): ('stringing', ),
    ('retraction_speed', 'lower'): ('stringing', ), ('fan_speed', 'higher'): ('warping', 'adhesion'),
    ('layer_height', 'higher'): ('support_failure', 'adhesion'), ('infill_density', 'lower'): ('support_failure', ),
    ('wall_count', 'lower'): ('support_failure', ),
}


# ── calculs purs ──────────────────────────────────────────────────────────

def wilson_low(success, total, z=1.96):
    """Borne basse de l'intervalle de Wilson du taux de réussite (0 si aucune donnée)."""
    if total <= 0:
        return 0.0
    p = success / total
    d = 1 + z * z / total
    centre = p + z * z / (2 * total)
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total)
    return max(0.0, (centre - spread) / d)


def _num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _mat(v):
    return str(v or '').strip().upper()


def _prepare(rows, profiles):
    """Lignes notées enrichies des réglages du profil utilisé (`profiles` : {id: dict})."""
    out = []
    for r in rows or []:
        if r.get('result') not in RATED:
            continue
        prof = (profiles or {}).get(r.get('slicer_profile_id') or '') or {}
        q = dict(r)
        q['_mat'] = _mat(r.get('filament_material'))
        q['_pname'] = (r.get('slicer_profile_name') or prof.get('name') or '').strip()
        q['_set'] = {k: _num(prof.get(k)) for k in NUM_PARAMS if _num(prof.get(k)) is not None}
        q['_fp'] = r.get('profile_fp') or ''
        out.append(q)
    return out


def _scopes(material, printer_id, model_path):
    """Périmètres du plus précis au plus large (seulement ceux que les filtres demandés permettent)."""
    mat, pid, mp = _mat(material), printer_id, (model_path or '')
    chain = []
    if mp and mat and pid:
        chain.append(('model_material_printer', mp, mat, pid))
    if mp:
        chain.append(('model', mp, '', None))
    if mat and pid:
        chain.append(('material_printer', '', mat, pid))
    if mat:
        chain.append(('material', '', mat, None))
    if pid:
        chain.append(('printer', '', '', pid))
    chain.append(('all', '', '', None))
    seen, out = set(), []
    for c in chain:
        if c[1:] not in seen:
            seen.add(c[1:])
            out.append(c)
    return out


def _select(rows, scope):
    _, mp, mat, pid = scope
    return [r for r in rows if (not mp or r.get('model_path') == mp) and (not mat or r['_mat'] == mat) and (not pid or r.get('printer_id') == pid)]


def _pick_scope(rows, material, printer_id, model_path, need):
    """Premier périmètre (du plus précis) qui contient au moins `need` impressions notées ; sinon le plus large."""
    chain = _scopes(material, printer_id, model_path)
    for sc in chain:
        sel = _select(rows, sc)
        if need(sel):
            return sc, sel, chain[0][0]
    sc = chain[-1]
    return sc, _select(rows, sc), chain[0][0]


def _scope_info(sc, wanted):
    return {'kind': sc[0], 'model_path': sc[1] or None, 'material': sc[2] or None, 'printer_id': sc[3], 'wanted': wanted, 'widened': sc[0] != wanted}


def readiness(rows):
    rated = [r for r in rows or [] if r.get('result') in RATED]
    n = len(rated)
    return {'rated': n, 'needed': MIN_GLOBAL, 'ready': n >= MIN_GLOBAL, 'failed': sum(1 for r in rated if r['result'] == 'failed')}


def _median(vals):
    return round(statistics.median(vals), 2) if vals else None


def param_summary(sel):
    """Valeurs typiques (médiane et plage) des impressions réussies, et écart avec les impressions ratées pour chaque réglage connu."""
    out = []
    for k, (unit, abs_gap, rel_gap) in NUM_PARAMS.items():
        ok = [r['_set'][k] for r in sel if r['result'] == 'success' and k in r['_set']]
        ko = [r['_set'][k] for r in sel if r['result'] == 'failed' and k in r['_set']]
        if len(ok) < MIN_PARAM_OK:
            continue
        med = _median(ok)
        item = {'param': k, 'unit': unit, 'typical': med, 'min': round(min(ok), 2), 'max': round(max(ok), 2), 'n_ok': len(ok), 'n_failed': len(ko), 'failed_median': None, 'direction': None}
        if len(ko) >= MIN_FAILED:
            fm = _median(ko)
            item['failed_median'] = fm
            gap = fm - med
            if abs(gap) >= max(abs_gap, rel_gap * abs(med)) and abs(gap) > 1e-9:
                item['direction'] = 'higher' if gap > 0 else 'lower'
        out.append(item)
    return out


def _combos(sel):
    groups = {}
    for r in sel:
        name, fp = r['_pname'], r['_fp']
        if not name and not fp:
            continue
        key = (name, fp)
        g = groups.setdefault(key, {'profile': name, 'profile_fp': fp, 'success': 0, 'failed': 0, 'partial': 0, 'settings': {}, 'last': ''})
        g[r['result']] += 1
        g['last'] = max(g['last'], str(r.get('sent_at') or ''))
        if r['_set'] and not g['settings']:
            g['settings'] = dict(r['_set'])
    out = []
    for g in groups.values():
        n = g['success'] + g['failed'] + g['partial']
        g['total'] = n
        g['rate'] = round(g['success'] / n, 3)
        g['score'] = round(wilson_low(g['success'], n), 4)
        out.append(g)
    out.sort(key=lambda g: (g['score'], g['total'], g['last']), reverse=True)
    return out


def _confidence(total, rate):
    if total >= 6 and rate >= 0.8:
        return 'high'
    return 'medium' if total >= MIN_SCOPE else 'low'


def apply_feedback(combos, feedback):
    """Corrige le classement avec le retour réel des recommandations déjà SUIVIES (1.1.8) : pas d'apprentissage opaque, une règle lisible.
    Un profil recommandé puis utilisé au moins `FB_MIN` fois : taux de réussite ≤ 40 % → score × 0,5 ; ≥ 80 % → score × 1,1 (plafonné à 1).
    Chaque combinaison porte `feedback` = {followed, success, effect} pour que l'écran explique la correction. Les recommandations ignorées ne servent qu'aux statistiques."""
    if not feedback:
        return combos
    for c in combos:
        mine = [f for f in feedback if f.get('followed') and f.get('result') in ('success', 'failed')
                and ((c['profile'] and f.get('profile') == c['profile']) or (c['profile_fp'] and f.get('profile_fp') == c['profile_fp']))]
        if not mine:
            continue
        ok = sum(1 for f in mine if f['result'] == 'success')
        effect = 'none'
        if len(mine) >= FB_MIN:
            rate = ok / len(mine)
            if rate <= FB_DEMOTE_RATE:
                c['score'] = round(c['score'] * 0.5, 4)
                effect = 'demoted'
            elif rate >= FB_PROMOTE_RATE:
                c['score'] = round(min(1.0, c['score'] * 1.1), 4)
                effect = 'promoted'
        c['feedback'] = {'followed': len(mine), 'success': ok, 'effect': effect}
    combos.sort(key=lambda g: (g['score'], g['total'], g['last']), reverse=True)
    return combos


def feedback_stats(feedback):
    """Résumé du retour d'expérience : combien de recommandations suivies / ignorées et leur taux de réussite (pour juger si Stellio avait raison)."""
    def agg(items):
        rated = [f for f in items if f.get('result') in ('success', 'failed')]
        ok = sum(1 for f in rated if f['result'] == 'success')
        return {'total': len(items), 'rated': len(rated), 'success': ok, 'rate': round(ok / len(rated), 3) if rated else None}
    fb = feedback or []
    return {'followed': agg([f for f in fb if f.get('followed')]), 'ignored': agg([f for f in fb if not f.get('followed')]), 'pending': sum(1 for f in fb if not f.get('result'))}


def recommend(rows, profiles=None, material='', printer_id=None, model_path='', feedback=None):
    """Recommandation de réglages pour (modèle, matière, imprimante) — tous facultatifs ; le périmètre s'élargit si les données manquent."""
    rows = _prepare(rows, profiles)
    ready = readiness(rows)
    wanted = _scopes(material, printer_id, model_path)[0][0]
    sc, sel, _ = _pick_scope(rows, material, printer_id, model_path, lambda s: len(s) >= MIN_SCOPE and any(c['total'] >= MIN_BEST and c['success'] > 0 for c in _combos(s)))
    res = {'ok': True, 'readiness': ready, 'scope': _scope_info(sc, wanted), 'sample': len(sel), 'best': None, 'alternatives': [], 'avoid': [], 'params': [], 'reason': None}
    combos = apply_feedback(_combos(sel), feedback)
    cands = [c for c in combos if c['total'] >= MIN_BEST and c['success'] > 0]
    if len(sel) < MIN_SCOPE or not cands:
        res['reason'] = 'not_enough_data'
        res['params'] = param_summary(sel) if len(sel) >= MIN_SCOPE else []
        return res
    best = max(cands, key=lambda c: (c['score'], c['total'], c['last']))
    best = dict(best, confidence=_confidence(best['total'], best['rate']))
    res['best'] = best
    res['alternatives'] = [c for c in cands if c is not best and (c['profile'], c['profile_fp']) != (best['profile'], best['profile_fp'])][:3]
    res['avoid'] = [c for c in combos if c['total'] >= 3 and c['rate'] <= AVOID_MAX_RATE and (c['profile'], c['profile_fp']) != (best['profile'], best['profile_fp'])][:3]
    res['params'] = param_summary(sel)
    return res


def _leads(sel, base_rate):
    """Contexte : matière / imprimante / profil dont le taux d'échec dépasse nettement la moyenne du périmètre."""
    out = []
    if len(sel) < 2 * MIN_SCOPE:
        return out
    for dim, fn in (('material', lambda r: r['_mat']), ('printer', lambda r: r.get('printer_id') or ''), ('profile', lambda r: r['_pname'])):
        groups = {}
        for r in sel:
            k = fn(r)
            if k in ('', None):
                continue
            g = groups.setdefault(k, [0, 0])
            g[1] += 1
            if r['result'] == 'failed':
                g[0] += 1
        if len(groups) < 2:                      # un seul groupe : rien à comparer
            continue
        for k, (f, n) in groups.items():
            if n >= MIN_SCOPE and f >= 2 and f / n - base_rate >= LEAD_MIN_GAP:
                out.append({'dimension': dim, 'key': k, 'fail_rate': round(f / n, 3), 'base_rate': round(base_rate, 3), 'failed': f, 'total': n})
    out.sort(key=lambda x: -x['fail_rate'])
    return out[:4]


def diagnose(rows, profiles=None, material='', printer_id=None, model_path='', target=None):
    """Causes probables des échecs d'un périmètre. `target` (ligne d'historique ratée, facultative) : son motif déclaré compte en premier."""
    rows = _prepare(rows, profiles)
    ready = readiness(rows)
    wanted = _scopes(material, printer_id, model_path)[0][0]
    sc, sel, _ = _pick_scope(rows, material, printer_id, model_path, lambda s: sum(1 for r in s if r['result'] == 'failed') >= MIN_FAILED and len(s) >= MIN_SCOPE)
    failed = [r for r in sel if r['result'] == 'failed']
    res = {'ok': True, 'readiness': ready, 'scope': _scope_info(sc, wanted), 'sample': len(sel), 'failed': len(failed), 'causes': [], 'contexts': [], 'reason': None,
           'this_print': None}
    tgt_reason = ''
    if target and target.get('result') == 'failed':
        tgt_reason = (target.get('failure_reason') or '').strip()
        res['this_print'] = {'failure_reason': tgt_reason or None}
    if len(failed) < MIN_FAILED and not tgt_reason:
        res['reason'] = 'not_enough_data'
        return res
    base = len(failed) / len(sel) if sel else 0.0
    score, ev = {}, {}

    def add(code, w, e):
        score[code] = score.get(code, 0.0) + w
        ev.setdefault(code, []).append(e)

    declared = {}
    for r in failed:
        k = (r.get('failure_reason') or '').strip()
        if k and k != 'other':
            declared[k] = declared.get(k, 0) + 1
    n_decl = sum(declared.values())
    for k, c in declared.items():
        add(k, 0.6 * (c / n_decl) * min(1.0, c / 3.0), {'type': 'declared', 'count': c, 'total': len(failed)})
    if tgt_reason and tgt_reason != 'other':
        add(tgt_reason, 0.25, {'type': 'this_print'})
    for p in param_summary(sel):
        if not p['direction']:
            continue
        for code in HYPOTHESES.get((p['param'], p['direction']), ()):
            add(code, 0.18, {'type': 'param', 'param': p['param'], 'unit': p['unit'], 'failed': p['failed_median'], 'ok': p['typical'], 'direction': p['direction'],
                             'n_failed': p['n_failed'], 'n_ok': p['n_ok']})
    res['contexts'] = _leads(sel, base)
    ranked = sorted(score.items(), key=lambda kv: -kv[1])[:3]
    total = sum(v for _, v in ranked) or 1.0
    for code, s in ranked:
        n_ev = len(ev[code])
        res['causes'].append({'cause': code, 'score': round(s, 3), 'share': round(s / total, 3), 'evidence': ev[code],
                              'confidence': 'high' if s >= 0.6 and n_ev >= 2 else ('medium' if s >= 0.3 else 'low')})
    if not res['causes']:
        res['reason'] = 'no_clear_cause'
    return res


# ── accès base ────────────────────────────────────────────────────────────

def _profiles():
    try:
        from modules import slicer_import
        return {p.get('id'): p for p in (slicer_import.load_slicer_profiles() or []) if isinstance(p, dict) and p.get('id')}
    except Exception:
        return {}


def _load_rows(conn, uid):
    try:
        from modules import print_traceability
        print_traceability._ensure_tables(conn)
        join = "LEFT JOIN print_trace t ON t.history_id = h.id AND t.user_id = h.user_id"
        extra = ", t.model_path AS model_path, t.profile_fp AS profile_fp"
    except Exception:
        join, extra = '', ", '' AS model_path, '' AS profile_fp"
    sql = ("SELECT h.id, h.result, h.failure_reason, h.filament_material, h.printer_id, h.slicer_profile_id, h.slicer_profile_name, h.sent_at, h.file_name, h.file_path"
           f"{extra} FROM print_history h {join} WHERE h.user_id = ? AND h.result IN ('success','failed','partial')")
    return [dict(r) for r in conn.execute(sql, (uid, )).fetchall()]


def _ensure_fb(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS intel_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        run_id INTEGER,
        printer_id INTEGER,
        material TEXT DEFAULT '',
        model_path TEXT DEFAULT '',
        profile TEXT DEFAULT '',
        profile_fp TEXT DEFAULT '',
        used_profile TEXT DEFAULT '',
        followed INTEGER DEFAULT 0,
        result TEXT DEFAULT '',
        created_at REAL,
        ended_at REAL)""")


def record_feedback(conn, uid, run_id, printer_id, material, model_path, rec_profile, rec_fp, used_profile, used_fp=''):
    """Enregistre qu'une recommandation a été (ou non) suivie. Rien n'est écrit s'il n'y avait pas de recommandation. Retourne l'id ou None."""
    import time as _t
    if not (rec_profile or rec_fp):
        return None
    _ensure_fb(conn)
    followed = int(bool((rec_profile and used_profile == rec_profile) or (rec_fp and used_fp == rec_fp)))
    cur = conn.execute("INSERT INTO intel_feedback (user_id, run_id, printer_id, material, model_path, profile, profile_fp, used_profile, followed, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (uid, run_id, printer_id, material or '', model_path or '', rec_profile or '', rec_fp or '', used_profile or '', followed, _t.time()))
    conn.commit()
    return cur.lastrowid


def finish_feedback(conn, run_id, result):
    """Associe le résultat réel (success / failed / partial) au retour enregistré pour ce flux de production."""
    import time as _t
    if result not in RATED:
        return 0
    _ensure_fb(conn)
    n = conn.execute("UPDATE intel_feedback SET result = ?, ended_at = ? WHERE run_id = ? AND result = ''", (result, _t.time(), run_id)).rowcount
    conn.commit()
    return n


def load_feedback(conn, uid):
    _ensure_fb(conn)
    return [{'profile': r['profile'], 'profile_fp': r['profile_fp'], 'followed': bool(r['followed']), 'result': r['result'], 'printer_id': r['printer_id'], 'material': r['material']}
            for r in conn.execute("SELECT * FROM intel_feedback WHERE user_id = ?", (uid, )).fetchall()]


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def api_intelligence_recommend():
    a = request.args
    conn = get_db()
    try:
        rows = _load_rows(conn, session['user_id'])
        fb = load_feedback(conn, session['user_id'])
    finally:
        conn.close()
    return jsonify(recommend(rows, _profiles(), a.get('material') or '', _int(a.get('printer_id')), (a.get('path') or '').replace('\\', '/'), fb))


def api_intelligence_diagnose():
    a = request.args
    conn = get_db()
    try:
        rows = _load_rows(conn, session['user_id'])
    finally:
        conn.close()
    target, material, pid, mp = None, a.get('material') or '', _int(a.get('printer_id')), (a.get('path') or '').replace('\\', '/')
    hid = _int(a.get('history_id'))
    if hid is not None:
        target = next((r for r in rows if r['id'] == hid), None)
        if not target:
            return jsonify({'error': 'not_found'}), 404
        material, pid, mp = target.get('filament_material') or '', target.get('printer_id'), target.get('model_path') or ''
    return jsonify(diagnose(rows, _profiles(), material, pid, mp, target))


def api_intelligence_overview():
    conn = get_db()
    try:
        rows = _load_rows(conn, session['user_id'])
        printers = {r['id']: r['name'] for r in conn.execute("SELECT id, name FROM printers").fetchall()}
    finally:
        conn.close()
    mats = sorted({_mat(r.get('filament_material')) for r in rows if _mat(r.get('filament_material'))})
    pids = sorted({r['printer_id'] for r in rows if r.get('printer_id')})
    return jsonify({'readiness': readiness(rows), 'materials': mats, 'printers': [{'id': i, 'name': printers.get(i) or f'#{i}'} for i in pids]})


def api_intelligence_feedback():
    conn = get_db()
    try:
        fb = load_feedback(conn, session['user_id'])
    finally:
        conn.close()
    return jsonify(feedback_stats(fb))


def api_intelligence_feedback_add():
    """Retour manuel (impression lancée hors du flux de production) : {profile, followed, result, material, printer_id}."""
    d = request.get_json(silent=True) or {}
    result = d.get('result') or ''
    if result and result not in RATED:
        return jsonify({'error': 'bad_result'}), 400
    prof = str(d.get('profile') or '').strip()[:200]
    if not prof:
        return jsonify({'error': 'bad_profile'}), 400
    import time as _t
    conn = get_db()
    try:
        _ensure_fb(conn)
        conn.execute("INSERT INTO intel_feedback (user_id, run_id, printer_id, material, profile, used_profile, followed, result, created_at, ended_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                     (session['user_id'], None, _int(d.get('printer_id')), str(d.get('material') or '')[:40], prof, prof if d.get('followed') else '', int(bool(d.get('followed'))),
                      result, _t.time(), _t.time() if result else None))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'success': True})


_ROUTES = (
    ('/api/intelligence/feedback', ['GET'], 'api_intelligence_feedback', ('login_required', )),
    ('/api/intelligence/feedback/add', ['POST'], 'api_intelligence_feedback_add', ('login_required', )),
    ('/api/intelligence/overview', ['GET'], 'api_intelligence_overview', ('login_required', )),
    ('/api/intelligence/recommend', ['GET'], 'api_intelligence_recommend', ('login_required', )),
    ('/api/intelligence/diagnose', ['GET'], 'api_intelligence_diagnose', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"intelligence.init : services manquants : {missing}")
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
