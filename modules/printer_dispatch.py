"""Stellio — répartition intelligente des tâches d'impression entre les imprimantes

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `printer_dispatch.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.

Pour chaque tâche en attente (table `print_jobs`), Stellio note chaque imprimante :
  + libre (état « idle »), + matière déjà chargée (AMS / multi-matériaux), – matière à changer, – filament insuffisant,
  – file d'attente déjà longue ; une imprimante hors ligne est exclue.
La suggestion est toujours expliquée (liste de raisons). `POST /api/dispatch/apply` assigne la meilleure imprimante ;
Stellio ne lance JAMAIS une impression tout seul : il ne fait qu'assigner l'imprimante de la tâche.
"""
import json

_REQUIRED = (
    '_printer_status_cached',
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'parse_printer_config',
    'request',
    'session',
)
_OVERRIDABLE = ('json',)

_MAIN = {}
_printer_status_cached = None
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
parse_printer_config = None
request = None
session = None

_OFFLINE = ('offline', 'error', 'unavailable', 'timeout', 'corrupted', 'unknown')


def _job_need_g(job):
    """Poids de filament restant à imprimer (g) d'après le modèle de coût de la tâche ; 0 si inconnu."""
    try:
        model = json.loads(job['cost_model'] or '{}') if 'cost_model' in job.keys() else {}
        per = float(model.get('weight_g') or 0)
    except (TypeError, ValueError):
        per = 0.0
    left = max(int(job['quantity'] or 1) - int(job['qty_done'] or 0), 0)
    return per * left


def score_printer(job, printer, status, queued):
    """Retourne (score, raisons, avertissements) ou None si l'imprimante est inutilisable. Fonction pure : testable sans base."""
    st = str((status or {}).get('status') or 'unknown').lower()
    if st in _OFFLINE:
        return None
    score, reasons, warns = 0, [], []
    if st == 'idle':
        score += 100
        reasons.append('idle')
    elif st in ('printing', 'paused'):
        score -= 20
        reasons.append('busy')
    mat = str(job['material'] or '').strip().upper()
    trays = [t for t in ((status or {}).get('ams') or []) if isinstance(t, dict)]
    if mat and trays:
        match = [t for t in trays if str(t.get('material') or t.get('type') or '').strip().upper() == mat]
        if match:
            score += 50
            reasons.append('material_loaded')
            need = _job_need_g(job)
            best = max((t.get('remaining_g') or 0) for t in match)
            if need and best and best < need:
                score -= 20
                warns.append('not_enough_filament')
        else:
            score -= 30
            warns.append('material_change')
    score -= min(queued, 10) * 5
    if queued:
        reasons.append('queue')
    return score, reasons, warns


def build_suggestions(uid):
    conn = get_db()
    try:
        printers = [parse_printer_config(r) for r in conn.execute("SELECT * FROM printers WHERE user_id=? ORDER BY id", (uid,)).fetchall()]
        jobs = conn.execute("SELECT * FROM print_jobs WHERE user_id=? AND status='queued' AND quantity>qty_done ORDER BY "
                            "CASE WHEN due_date='' THEN 1 ELSE 0 END, due_date, id", (uid,)).fetchall()
        load = {}
        for r in conn.execute("SELECT printer_id, COUNT(*) AS n FROM print_jobs WHERE user_id=? AND status IN ('queued','printing') "
                              "AND printer_id IS NOT NULL GROUP BY printer_id", (uid,)).fetchall():
            load[r['printer_id']] = r['n']
    finally:
        conn.close()
    statuses = {}
    for p in printers:
        try:
            statuses[p['id']] = _printer_status_cached(p) or {}
        except Exception as e:
            statuses[p['id']] = {'status': 'offline', 'error': str(e)}
    out = []
    pending = dict(load)       # charge simulée : chaque suggestion alourdit l'imprimante choisie
    for job in jobs:
        cands = []
        for p in printers:
            sc = score_printer(job, p, statuses.get(p['id']), pending.get(p['id'], 0))
            if sc is None:
                continue
            cands.append({'printer_id': p['id'], 'printer_name': p.get('name') or f"#{p['id']}", 'score': sc[0],
                          'reasons': sc[1], 'warnings': sc[2], 'status': str((statuses.get(p['id']) or {}).get('status') or '')})
        cands.sort(key=lambda c: (-c['score'], c['printer_id']))
        best = cands[0] if cands else None
        if best:
            pending[best['printer_id']] = pending.get(best['printer_id'], 0) + 1
        out.append({'job_id': job['id'], 'part': job['part'], 'client': job['client'], 'material': job['material'],
                    'quantity': job['quantity'], 'qty_done': job['qty_done'], 'due_date': job['due_date'],
                    'current_printer_id': job['printer_id'], 'best': best, 'alternatives': cands[1:3],
                    'change': bool(best and best['printer_id'] != job['printer_id'])})
    return out


def apply_suggestions(uid, job_ids=None):
    """Assigne la meilleure imprimante aux tâches en attente (toutes, ou celles de `job_ids`). Retourne le nombre de tâches modifiées."""
    wanted = {int(j) for j in (job_ids or [])}
    changed = 0
    conn = get_db()
    try:
        for s in build_suggestions(uid):
            if wanted and s['job_id'] not in wanted:
                continue
            if s['best'] and s['change']:
                conn.execute("UPDATE print_jobs SET printer_id=? WHERE id=? AND user_id=? AND status='queued'",
                             (s['best']['printer_id'], s['job_id'], uid))
                changed += 1
        conn.commit()
    finally:
        conn.close()
    return changed


def api_dispatch_suggestions():
    try:
        return jsonify({'suggestions': build_suggestions(session['user_id'])})
    except Exception as e:
        app_logger.error(f"[DISPATCH] Suggestions impossibles : {e}")
        return jsonify({'suggestions': [], 'error': 'internal'}), 500


def api_dispatch_apply():
    data = request.get_json(silent=True) or {}
    ids = data.get('job_ids') if isinstance(data.get('job_ids'), list) else None
    try:
        n = apply_suggestions(session['user_id'], ids)
    except Exception as e:
        app_logger.error(f"[DISPATCH] Assignation impossible : {e}")
        return jsonify({'success': False, 'error': 'internal'}), 500
    return jsonify({'success': True, 'changed': n})


_ROUTES = (
    ('/api/dispatch/suggestions', ['GET'], 'api_dispatch_suggestions', ('login_required', )),
    ('/api/dispatch/apply', ['POST'], 'api_dispatch_apply', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"printer_dispatch.init : services manquants : {missing}")
    for n in _REQUIRED + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {}
