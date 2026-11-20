"""Stellio — besoins en matière (1.1.7) : ce qu'il faut pour imprimer ce qui est prévu, face au stock.

La prévision de réapprovisionnement existante (`/api/filament/restock`) regarde le PASSÉ : « à ce rythme, il reste N jours ».
Ce module regarde l'AVENIR : la file d'impression et les projets en cours demandent X g par matière ; le stock en a Y ;
il manque Z g, soit N bobines à commander. Lecture seule, rien n'est écrit.

Poids d'un modèle, du plus fiable au moins fiable :
  1. `history`  : moyenne réellement consommée lors des impressions précédentes de ce fichier ;
  2. `slicer`   : poids annoncé par le slicer ou lu dans le G-code ;
  3. `rough`    : poids géométrique (volume × densité, pièce pleine) × ROUGH_FACTOR — un ordre de grandeur, signalé comme tel.
Route : `GET /api/filament/needs`.
"""
import math
import os

_REQUIRED = (
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'session',
)
_OPTIONAL = ('_get_required_weight_for_file', '_restock_collect_spools', 'analyze_3d_file_stored')
_OVERRIDABLE = ('os',)

_MAIN = {}
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None
_get_required_weight_for_file = None
_restock_collect_spools = None
analyze_3d_file_stored = None

ROUGH_FACTOR = 0.35          # une pièce imprimée n'est pas pleine : ~35 % du poids géométrique (parois + remplissage moyen)
SPOOL_G = 1000.0
WINDOW_DAYS = 60
DONE_STATUSES = ('done', 'archived', 'cancelled', 'canceled')
KNOWN = ('PLA', 'PETG', 'ABS', 'ASA', 'TPU', 'PA', 'NYLON', 'PC', 'PVA', 'HIPS', 'PP')


def material_key(m):
    """« PLA+ », « pla silk », « Generic PETG » → PLA, PLA, PETG ; inconnu → texte en majuscules ; vide → PLA (hypothèse signalée)."""
    t = str(m or '').strip().upper().replace('-', ' ')
    if not t:
        return ''
    for k in sorted(KNOWN, key=len, reverse=True):
        if t == k or t.startswith(k) or (' ' + k) in (' ' + t):
            return 'PA' if k == 'NYLON' else k
    return t.split()[0][:12]


def compute(items, spools, daily, spool_g=SPOOL_G):
    """items  : [{'material','grams','kind':'queue'|'project','name','source':'history'|'slicer'|'rough'|None,'assumed':bool}]
       spools : [{'material','remaining_g'}]    daily : {matière: g/jour}
       Renvoie une ligne par matière, triée : plus gros manque d'abord."""
    rows = {}

    def row(mat):
        return rows.setdefault(mat, {'material': mat, 'stock_g': 0.0, 'spools': 0, 'queue_g': 0.0, 'projects_g': 0.0, 'items': 0,
                                     'unknown_weight': 0, 'rough': 0, 'assumed_material': 0})
    for s in spools:
        try:
            g = float(s.get('remaining_g'))
        except (TypeError, ValueError):
            continue
        r = row(material_key(s.get('material')) or '?')
        r['stock_g'] += max(g, 0.0); r['spools'] += 1
    for it in items:
        mat = material_key(it.get('material')) or 'PLA'
        r = row(mat)
        r['items'] += 1
        if it.get('assumed') or not it.get('material'):
            r['assumed_material'] += 1
        g = it.get('grams')
        if g is None:
            r['unknown_weight'] += 1
            continue
        if it.get('source') == 'rough':
            r['rough'] += 1
        r['queue_g' if it.get('kind') == 'queue' else 'projects_g'] += float(g)
    out = []
    for mat, r in rows.items():
        demand = r['queue_g'] + r['projects_g']
        short = max(demand - r['stock_g'], 0.0)
        d = float(daily.get(mat) or 0)
        out.append({'material': mat, 'stock_g': round(r['stock_g']), 'spools': r['spools'], 'queue_g': round(r['queue_g']), 'projects_g': round(r['projects_g']),
                    'demand_g': round(demand), 'shortfall_g': round(short), 'spools_to_buy': int(math.ceil(short / spool_g)) if short > 0 else 0,
                    'surplus_g': round(max(r['stock_g'] - demand, 0.0)), 'items': r['items'], 'unknown_weight': r['unknown_weight'],
                    'rough': r['rough'], 'assumed_material': r['assumed_material'],
                    'daily_g': round(d, 1) if d > 0 else None,
                    'days_left': round(r['stock_g'] / d, 1) if d > 0 and r['stock_g'] > 0 else None})
    out.sort(key=lambda x: (-x['shortfall_g'], -x['demand_g'], x['material']))
    return out


def _q(conn, sql, params=()):
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    except Exception:
        return []


def _history_avg(conn, uid, path):
    r = _q(conn, "SELECT AVG(spool_weight_used_g) AS g, COUNT(*) AS n FROM print_history WHERE user_id = ? AND file_path = ? AND spool_weight_used_g > 0", (uid, path))
    return (float(r[0]['g']), 'history') if r and r[0]['n'] else (None, None)


def weight_and_source(conn, uid, path):
    g, src = _history_avg(conn, uid, path)
    if g:
        return g, src
    if _get_required_weight_for_file:
        try:
            w, s = _get_required_weight_for_file(path)
            if w:
                return (float(w) * ROUGH_FACTOR, 'rough') if s == 'geometric' else (float(w), 'slicer')
        except Exception:
            pass
    if analyze_3d_file_stored and os.path.isfile(path):          # pas encore analysé : on l'analyse (rapide) et on le garde en base
        try:
            meta = analyze_3d_file_stored(path)
            w = ((meta or {}).get('weights') or {}).get('pla')
            if w:
                return float(w) * ROUGH_FACTOR, 'rough'
        except Exception:
            pass
    return None, None


def _material_of(conn, uid, path):
    a = _q(conn, "SELECT material FROM filament_assignments WHERE file_path = ? AND user_id = ?", (path, uid))
    if a and a[0]['material']:
        return a[0]['material'], False
    h = _q(conn, "SELECT filament_material FROM print_history WHERE user_id = ? AND file_path = ? AND COALESCE(filament_material,'') != '' ORDER BY id DESC LIMIT 1", (uid, path))
    if h:
        return h[0]['filament_material'], False
    return '', True


def collect_items(conn, uid):
    items = []
    for r in _q(conn, "SELECT file_path FROM print_queue WHERE user_id = ? ORDER BY position", (uid,)):
        p = r['file_path']
        g, src = weight_and_source(conn, uid, p)
        mat, assumed = _material_of(conn, uid, p)
        items.append({'material': mat, 'grams': g, 'kind': 'queue', 'name': os.path.basename(p), 'source': src, 'assumed': assumed})
    projects = _q(conn, "SELECT id, name, status FROM projects WHERE user_id = ?", (uid,))
    for pr in projects:
        if str(pr.get('status') or '').lower() in DONE_STATUSES:
            continue
        for f in _q(conn, "SELECT file_path, quantity_needed, quantity_printed FROM project_files WHERE project_id = ?", (pr['id'],)):
            left = max(int(f['quantity_needed'] or 0) - int(f['quantity_printed'] or 0), 0)
            if not left:
                continue
            g, src = weight_and_source(conn, uid, f['file_path'])
            mat, assumed = _material_of(conn, uid, f['file_path'])
            items.append({'material': mat, 'grams': None if g is None else g * left, 'kind': 'project', 'name': f"{pr['name']} · {os.path.basename(f['file_path'])} ×{left}",
                          'source': src, 'assumed': assumed})
    return items


def daily_use(conn, uid):
    """Grammes par jour et par matière, sur les 60 derniers jours (fenêtre réellement observée, 14 jours minimum)."""
    import datetime
    rows = _q(conn, "SELECT filament_material AS m, SUM(spool_weight_used_g) AS g, MIN(sent_at) AS first FROM print_history "
                    "WHERE user_id = ? AND spool_weight_used_g > 0 AND COALESCE(filament_material,'') != '' AND sent_at >= datetime('now', ?) GROUP BY filament_material",
              (uid, f'-{WINDOW_DAYS} days'))
    tot, first = {}, {}
    for r in rows:
        k = material_key(r['m'])
        tot[k] = tot.get(k, 0.0) + float(r['g'] or 0)
        try:
            d = datetime.datetime.strptime(str(r['first'])[:19], '%Y-%m-%d %H:%M:%S')
            first[k] = min(first.get(k, d), d)
        except ValueError:
            pass
    now = datetime.datetime.now()
    out = {}
    for k, g in tot.items():
        if g < 20:
            continue
        span = (now - first[k]).total_seconds() / 86400 if k in first else WINDOW_DAYS
        out[k] = g / max(14.0, min(float(WINDOW_DAYS), span))
    return out


def api_material_needs():
    uid = session['user_id']
    conn = get_db()
    try:
        items = collect_items(conn, uid)
        daily = daily_use(conn, uid)
    finally:
        conn.close()
    spools = []
    if _restock_collect_spools:
        try:
            spools = _restock_collect_spools(uid)
        except Exception as e:
            app_logger.info(f"[Besoins] stock illisible : {e}")
    rows = compute(items, spools, daily)
    return jsonify({'materials': rows, 'spool_g': SPOOL_G, 'rough_factor': ROUGH_FACTOR,
                    'items': len(items), 'unknown_weight': sum(r['unknown_weight'] for r in rows), 'detail': items[:60]})


_ROUTES = (
    ('/api/filament/needs', ['GET'], 'api_material_needs', ('login_required', )),
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
