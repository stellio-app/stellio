"""Stellio — export CSV du bilan d'impression (1.2.2).

GET /api/reports/period.csv?frequency=week|month|quarter|year&date=AAAA-MM-JJ : mêmes données que le bilan à l'écran
(totaux, par imprimante, par matière, modèles les plus imprimés), au format tableur (UTF-8 avec BOM, séparateur « ; »).
"""
import csv
import datetime
import io

_REQUIRED = (
    'REPORT_FREQUENCIES',
    '_report_data_range',
    '_report_period_bounds',
    'app',
    'get_db',
    'login_required',
    'request',
    'session',
)
_OPTIONAL = ()
_OVERRIDABLE = ()

_MAIN = {}
REPORT_FREQUENCIES = None
_report_data_range = None
_report_period_bounds = None
app = None
get_db = None
login_required = None
request = None
session = None


def _num(v):
    """Nombre au format tableur français/anglais sans surprise : point décimal conservé, 2 décimales max."""
    if isinstance(v, bool) or v is None:
        return ''
    if isinstance(v, float):
        return ('%.2f' % v).rstrip('0').rstrip('.')
    return v


def _cell(v):
    """Neutralise l'injection de formules (=, +, -, @) dans les noms de fichiers, d'imprimantes ou de matières."""
    s = '' if v is None else str(v)
    return ("'" + s) if s[:1] in ('=', '+', '-', '@', '\t', '\r') else s


def build_csv(report, frequency, start, end):
    out = io.StringIO()
    w = csv.writer(out, delimiter=';', lineterminator='\r\n')
    w.writerow(['Stellio', 'bilan', frequency, start, end])
    t = report.get('totals') or {}
    w.writerow([])
    w.writerow(['totaux'])
    for k in ('prints', 'success', 'failed', 'unrated', 'grams', 'seconds', 'material_cost', 'elec_cost', 'total_cost', 'failed_cost', 'failed_grams', 'co2_g'):
        w.writerow([k, _num(t.get(k, 0))])
    prev = report.get('previous')
    if prev:
        w.writerow([])
        w.writerow(['periode_precedente'])
        for k in ('prints', 'success', 'failed', 'grams', 'seconds', 'total_cost'):
            w.writerow([k, _num(prev.get(k, 0))])
    for key, title in (('by_printer', 'par_imprimante'), ('by_material', 'par_matiere'), ('top_models', 'modeles_les_plus_imprimes')):
        rows = report.get(key) or []
        w.writerow([])
        w.writerow([title])
        w.writerow(['nom', 'impressions', 'echecs', 'grammes', 'secondes', 'cout'])
        for r in rows:
            w.writerow([_cell(r.get('name')), _num(r.get('prints', 0)), _num(r.get('failed', 0)), _num(r.get('grams', 0.0)),
                        _num(r.get('seconds', 0)), _num(r.get('cost', 0.0))])
    return '﻿' + out.getvalue()


def api_report_period_csv():
    from flask import Response
    frequency = (request.args.get('frequency') or 'month').strip().lower()
    if frequency not in REPORT_FREQUENCIES:
        frequency = 'month'
    try:
        anchor = datetime.date.fromisoformat((request.args.get('date') or '').strip())
    except ValueError:
        anchor = datetime.date.today()
    start, end = _report_period_bounds(frequency, anchor)
    prev_start, prev_end = _report_period_bounds(frequency, start - datetime.timedelta(days=1))
    conn = get_db()
    try:
        report = _report_data_range(conn, session['user_id'], start.isoformat(), end.isoformat())
        report['previous'] = _report_data_range(conn, session['user_id'], prev_start.isoformat(), prev_end.isoformat())['totals']
    finally:
        conn.close()
    last = (end - datetime.timedelta(days=1)).isoformat()
    body = build_csv(report, frequency, start.isoformat(), last)
    name = 'bilan-%s-%s.csv' % (frequency, start.isoformat())
    return Response(body, mimetype='text/csv; charset=utf-8', headers={'Content-Disposition': 'attachment; filename="%s"' % name})


_ROUTES = (
    ('/api/reports/period.csv', ['GET'], 'api_report_period_csv', ('login_required', )),
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
