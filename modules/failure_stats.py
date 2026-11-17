"""Stellio — statistiques des échecs d'impression : « pourquoi mes impressions ratent » (v1.1.3)

Agrège l'historique d'impression noté (réussite / échec / partiel, motif d'échec) et le ventile par motif, matière, imprimante,
profil de slicer, jour de la semaine, tranche horaire et type de fichier, avec le taux de réussite de chaque groupe et les
fichiers qui échouent le plus. Les groupes trop petits (< 3 impressions notées) ne donnent pas de taux, pour ne pas conclure
sur trop peu de données. Une « piste » en une phrase signale les écarts nets (ex. une matière dont le taux d'échec est
très au-dessus de la moyenne).

Module séparé de main.py (même schéma que trash_routes.py) : main.py appelle `failure_stats.init(globals())`.
`compute(rows, ...)` est pur (testé sans base).
"""
import datetime

_REQUIRED = (
    'app',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'session',
)
_OPTIONAL = ()
_OVERRIDABLE = ('datetime',)

_MAIN = {}
app = None
get_db = None
jsonify = None
login_required = None
request = None
session = None

MIN_GROUP = 3            # impressions notées minimum pour afficher un taux
LEAD_MIN_GAP = 0.25      # écart de taux d'échec avec la moyenne pour proposer une piste
HOUR_BUCKETS = ((0, 6, 'night'), (6, 12, 'morning'), (12, 18, 'afternoon'), (18, 24, 'evening'))


def _bucket_hour(h):
    for a, b, name in HOUR_BUCKETS:
        if a <= h < b:
            return name
    return 'night'


def _group(rows, keyfn):
    groups = {}
    for r in rows:
        k = keyfn(r)
        if k in (None, ''):
            k = '_unknown'
        g = groups.setdefault(k, {'key': k, 'success': 0, 'failed': 0, 'partial': 0})
        g[r['result']] += 1
    out = []
    for g in groups.values():
        n = g['success'] + g['failed'] + g['partial']
        g['total'] = n
        g['fail_rate'] = round(g['failed'] / n, 3) if n >= MIN_GROUP else None
        out.append(g)
    out.sort(key=lambda g: (-g['failed'], -g['total'], str(g['key'])))
    return out


def compute(rows, printers=None):
    """rows : dicts {result, failure_reason, filament_material, printer_id, slicer_profile_name, file_ext, file_name, sent_at}."""
    printers = printers or {}
    rated = [r for r in rows if r.get('result') in ('success', 'failed', 'partial')]
    total = len(rated)
    failed = sum(1 for r in rated if r['result'] == 'failed')
    partial = sum(1 for r in rated if r['result'] == 'partial')
    base_rate = (failed / total) if total else 0.0

    def when(r):
        try:
            return datetime.datetime.strptime(str(r.get('sent_at'))[:19], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None

    for r in rated:
        r['_dt'] = when(r)
    reasons = {}
    for r in rated:
        if r['result'] == 'failed':
            k = (r.get('failure_reason') or '').strip() or '_unspecified'
            reasons[k] = reasons.get(k, 0) + 1
    by_reason = [{'key': k, 'count': v, 'share': round(v / failed, 3) if failed else 0} for k, v in sorted(reasons.items(), key=lambda kv: -kv[1])]
    by_material = _group(rated, lambda r: (r.get('filament_material') or '').strip().upper())
    by_printer = _group(rated, lambda r: printers.get(r.get('printer_id')) or (None if not r.get('printer_id') else f"#{r['printer_id']}"))
    by_profile = _group(rated, lambda r: (r.get('slicer_profile_name') or '').strip())
    by_ext = _group(rated, lambda r: (r.get('file_ext') or '').strip().lower().lstrip('.'))
    by_weekday = _group([r for r in rated if r['_dt']], lambda r: r['_dt'].weekday())
    by_weekday.sort(key=lambda g: g['key'])
    by_hour = _group([r for r in rated if r['_dt']], lambda r: _bucket_hour(r['_dt'].hour))

    files = {}
    for r in rated:
        f = files.setdefault(r.get('file_name') or '?', {'file': r.get('file_name') or '?', 'failed': 0, 'total': 0})
        f['total'] += 1
        if r['result'] == 'failed':
            f['failed'] += 1
    worst = sorted((f for f in files.values() if f['failed'] >= 2), key=lambda f: (-f['failed'], -f['total']))[:8]

    leads = []
    if total >= 2 * MIN_GROUP:
        for dim, groups in (('material', by_material), ('printer', by_printer), ('profile', by_profile)):
            for g in groups:
                if g['key'] == '_unknown' or g['fail_rate'] is None:
                    continue
                if g['fail_rate'] - base_rate >= LEAD_MIN_GAP and g['failed'] >= 2:
                    leads.append({'dimension': dim, 'key': g['key'], 'fail_rate': g['fail_rate'], 'base_rate': round(base_rate, 3), 'failed': g['failed'], 'total': g['total']})
        top = by_reason[0] if by_reason and by_reason[0]['key'] != '_unspecified' else None
        if top and top['count'] >= 2 and top['share'] >= 0.4:
            leads.append({'dimension': 'reason', 'key': top['key'], 'share': top['share'], 'failed': top['count'], 'total': failed})
    leads.sort(key=lambda l: -(l.get('fail_rate', l.get('share', 0)) or 0))

    return {'total': total, 'success': total - failed - partial, 'failed': failed, 'partial': partial,
            'fail_rate': round(base_rate, 3) if total else None, 'min_group': MIN_GROUP,
            'by_reason': by_reason, 'by_material': by_material, 'by_printer': by_printer, 'by_profile': by_profile,
            'by_ext': by_ext, 'by_weekday': by_weekday, 'by_hour': by_hour, 'worst_files': worst, 'leads': leads[:4]}


def api_failure_stats():
    try:
        days = max(0, min(3650, int(request.args.get('days') or 0)))
    except ValueError:
        days = 0
    conn = get_db()
    try:
        sql = ("SELECT result, failure_reason, filament_material, printer_id, slicer_profile_name, file_ext, file_name, sent_at "
               "FROM print_history WHERE user_id = ? AND result IN ('success','failed','partial')")
        params = [session['user_id']]
        if days:
            sql += " AND sent_at >= ?"
            params.append((datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S'))
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
        printers = {r['id']: r['name'] for r in conn.execute("SELECT id, name FROM printers").fetchall()}
    finally:
        conn.close()
    out = compute(rows, printers)
    out['days'] = days
    return jsonify(out)


_ROUTES = (
    ('/api/failure-stats', ['GET'], 'api_failure_stats', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"failure_stats.init : services manquants : {missing}")
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
