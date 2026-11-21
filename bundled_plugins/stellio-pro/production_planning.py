"""Stellio — planning et capacité de production (v1.1.5 ; coût, rendement et retards constatés : v1.1.7)

Pour chaque imprimante : file de commandes ouvertes (table `print_jobs`), date de fin estimée de chacune, capacité disponible
(heures par jour et jours travaillés, réglables par imprimante) comparée à la charge demandée, taux de respect des délais,
et alertes de surcharge / de retard prévisible.

Principe (volontairement simple et expliqué) :
  · durée d'une commande = pièces restantes × durée par pièce (`est_hours` saisie sur la commande, sinon `hours` du chiffrage
    du devis) ; une commande sans durée n'est pas planifiée (elle est signalée) ;
  · par imprimante, les commandes s'enchaînent dans l'ordre : en cours d'abord, puis date de livraison, puis ancienneté ;
    l'impression en cours (temps restant lu sur l'imprimante) passe avant ;
  · les commandes sans imprimante sont placées, à titre indicatif, sur l'imprimante qui se libère le plus tôt ;
  · une imprimante travaille `hours_per_day` heures les jours cochés (aujourd'hui : au plus les heures restantes de la journée).
Les fonctions de calcul sont pures (aucune base, aucune requête) : elles sont testées directement.

Module séparé de main.py (même schéma que printer_dispatch.py) : main.py appelle `production_planning.init(globals())`.
"""
import datetime
import json
import math
import threading
import time

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
_OPTIONAL = (
    '_insert_notification_once',
    '_push_notify_async',
    '_send_native_notification',
    '_server_t',
    '_webhook_emit',
)
_OVERRIDABLE = ('json',)

_MAIN = {}
_printer_status_cached = None
_insert_notification_once = None
_push_notify_async = None
_send_native_notification = None
_webhook_emit = None           # évènements order.late / printer.overload pour les webhooks
_server_t = None
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
parse_printer_config = None
request = None
session = None

DEFAULT_HOURS_PER_DAY = 16.0
DEFAULT_DAYS = (0, 1, 2, 3, 4, 5, 6)
HORIZONS = (7, 14, 30)
_OFFLINE = ('offline', 'error', 'unavailable', 'timeout', 'corrupted', 'unknown')
_MAX_DAYS = 366


# ── fonctions pures ───────────────────────────────────────────────────────

def parse_days(value, default=DEFAULT_DAYS):
    """Jours travaillés (0 = lundi … 6 = dimanche) depuis une liste ou une chaîne « 0,1,2 »."""
    if isinstance(value, str):
        value = [x for x in value.replace(';', ',').split(',') if x.strip() != '']
    try:
        days = sorted({int(x) for x in (value or []) if 0 <= int(x) <= 6})
    except (TypeError, ValueError):
        days = []
    return tuple(days) if days else tuple(default)


def clamp_hours(value, default=DEFAULT_HOURS_PER_DAY):
    try:
        h = float(value)
    except (TypeError, ValueError):
        return float(default)
    if h != h:
        return float(default)
    return min(24.0, max(0.5, h))


def hours_per_piece(job):
    """Durée d'une pièce (h) : `est_hours` de la commande, sinon `hours` du chiffrage du devis ; 0 si inconnue."""
    def _f(v):
        try:
            f = float(v)
            return f if f == f and 0 < f < 100000 else 0.0
        except (TypeError, ValueError):
            return 0.0
    keys = job.keys() if hasattr(job, 'keys') else job
    est = _f(job['est_hours']) if 'est_hours' in keys else 0.0
    if est:
        return est
    try:
        raw = job['cost_model'] if 'cost_model' in keys else ''
        model = json.loads(raw or '{}') if isinstance(raw, str) else (raw or {})
        return _f(model.get('hours'))
    except (TypeError, ValueError, AttributeError):
        return 0.0


def remaining_pieces(job):
    return max(int(job['quantity'] or 1) - int(job['qty_done'] or 0), 0)


def day_capacities(now, hours_per_day, days, n_days):
    """[(date, heures disponibles)] pour `n_days` jours à partir d'aujourd'hui. Aujourd'hui : au plus les heures qu'il reste."""
    out = []
    left_today = max(0.0, 24.0 - now.hour - now.minute / 60.0)
    for i in range(n_days):
        d = now.date() + datetime.timedelta(days=i)
        cap = hours_per_day if d.weekday() in days else 0.0
        if i == 0:
            cap = min(cap, left_today)
        out.append((d, cap))
    return out


def position_after(now, hours_per_day, days, hours):
    """Date et position (jour + fraction, 0 = aujourd'hui) atteintes après `hours` d'impression, ou None au-delà d'un an."""
    if hours <= 0:
        return None
    remaining = float(hours)
    i = 0
    while i < _MAX_DAYS:
        d = now.date() + datetime.timedelta(days=i)
        cap = hours_per_day if d.weekday() in days else 0.0
        if i == 0:
            cap = min(cap, max(0.0, 24.0 - now.hour - now.minute / 60.0))
        if cap > 0:
            if remaining <= cap + 1e-9:
                return d, i + (remaining / cap)
            remaining -= cap
        i += 1
    return None


def _pos_at(now, hours_per_day, days, hours):
    """Position (jour + fraction) après `hours` heures de travail cumulées ; 0 heure = début (aujourd'hui, ou 1er jour travaillé)."""
    if hours <= 0:
        i = 0
        while i < _MAX_DAYS:
            d = now.date() + datetime.timedelta(days=i)
            cap = hours_per_day if d.weekday() in days else 0.0
            if i == 0:
                cap = min(cap, max(0.0, 24.0 - now.hour - now.minute / 60.0))
            if cap > 0:
                return d, float(i)
            i += 1
        return None
    return position_after(now, hours_per_day, days, hours)


def plan(jobs, printers, statuses, settings, now, horizon_days=14):
    """Calcule le planning.

    jobs      : lignes `print_jobs` (dict-like) ouvertes ou non ; les terminées/annulées sont ignorées.
    printers  : [{'id', 'name'}] ; statuses : {printer_id: dict d'état (clé 'status', 'time': {'remaining': s})}.
    settings  : {'default': {'hours_per_day', 'days'}, 'printers': {id: {'hours_per_day','days','enabled'}}}.
    Retourne un dict JSON-able : printers, jobs, summary, alerts, unplanned.
    """
    horizon_days = horizon_days if horizon_days in HORIZONS else 14
    dflt = (settings or {}).get('default') or {}
    d_hpd = clamp_hours(dflt.get('hours_per_day'))
    d_days = parse_days(dflt.get('days'))
    per = (settings or {}).get('printers') or {}

    plist = []
    for p in printers:
        cfg = per.get(p['id']) or per.get(str(p['id'])) or {}
        plist.append({
            'id': p['id'], 'name': p.get('name') or f"#{p['id']}",
            'enabled': bool(cfg.get('enabled', True)),
            'hpd': clamp_hours(cfg.get('hours_per_day'), d_hpd) if cfg.get('hours_per_day') not in (None, '') else d_hpd,
            'days': parse_days(cfg.get('days'), d_days) if cfg.get('days') not in (None, '', []) else d_days,
        })
    active = {p['id']: p for p in plist if p['enabled']}

    open_jobs = [j for j in jobs if j['status'] in ('queued', 'printing') and remaining_pieces(j) > 0]
    today = now.date().isoformat()

    # imprimantes : état et temps restant de l'impression en cours
    state = {}
    for p in plist:
        st = (statuses or {}).get(p['id']) or {}
        status = str(st.get('status') or 'unknown').lower()
        busy = 0.0
        if status in ('printing', 'paused'):
            try:
                busy = max(0.0, float((st.get('time') or {}).get('remaining') or 0) / 3600.0)
            except (TypeError, ValueError):
                busy = 0.0
        state[p['id']] = {'status': status, 'busy': busy, 'queue': [], 'hours': busy}

    def _order(j):
        return (0 if j['status'] == 'printing' else 1, 0 if j['due_date'] else 1, j['due_date'] or '', j['id'])

    no_duration, unassigned = [], []
    for j in sorted(open_jobs, key=_order):
        if hours_per_piece(j) <= 0:
            no_duration.append(j)
            continue
        pid = j['printer_id']
        if pid in active:
            state[pid]['queue'].append((j, False))
        else:
            unassigned.append(j)

    def _job_hours(j, pid):
        h = hours_per_piece(j) * remaining_pieces(j)
        # une impression en cours sur la machine : sa pièce en cours est déjà comptée dans le temps restant lu sur l'imprimante
        if j['status'] == 'printing' and state[pid]['busy'] > 0 and remaining_pieces(j) > 0:
            h -= hours_per_piece(j)
        return max(h, 0.0)

    # commandes sans imprimante : sur celle qui se libère le plus tôt (à titre indicatif)
    if active:
        for j in unassigned:
            def _free(pid):
                return state[pid]['hours'] + sum(_job_hours(x, pid) for x, _v in state[pid]['queue'])
            pid = min(active, key=lambda k: (_free(k), k))
            state[pid]['queue'].append((j, True))

    out_jobs, plan_printers = [], []
    for p in plist:
        s = state[p['id']]
        cap_list = day_capacities(now, p['hpd'], p['days'], horizon_days) if p['enabled'] else []
        capacity = sum(c for _d, c in cap_list)
        cum = s['busy']
        for j, virtual in s['queue']:
            h = _job_hours(j, p['id'])
            running = bool(j['status'] == 'printing' and s['busy'] > 0 and not virtual and cum == s['busy'])
            start = _pos_at(now, p['hpd'], p['days'], 0 if running else cum)
            cum_end = cum + h
            end = position_after(now, p['hpd'], p['days'], cum_end) if cum_end > 0 else start
            cum = cum_end
            end_date = end[0].isoformat() if end else None
            due = j['due_date'] or ''
            late = bool(due and end_date and end_date > due)
            slack = None
            if due and end_date:
                slack = (datetime.date.fromisoformat(due) - datetime.date.fromisoformat(end_date)).days
            out_jobs.append({
                'id': j['id'], 'part': j['part'], 'client': j['client'], 'status': j['status'],
                'printer_id': p['id'], 'printer_name': p['name'], 'virtual': virtual,
                'quantity': j['quantity'], 'qty_done': j['qty_done'], 'hours': round(h, 2),
                'start': start[0].isoformat() if start else None, 'end': end_date,
                'start_pos': round(start[1], 3) if start else None, 'end_pos': round(end[1], 3) if end else None,
                'due_date': due, 'late_predicted': late, 'overdue': bool(due and due < today),
                'slack_days': slack,
            })
        free_from = position_after(now, p['hpd'], p['days'], cum) if cum > 0 else None
        plan_printers.append({
            'id': p['id'], 'name': p['name'], 'enabled': p['enabled'], 'status': s['status'],
            'hours_per_day': p['hpd'], 'days': list(p['days']),
            'busy_hours': round(s['busy'], 2), 'queue_hours': round(cum, 2),
            'capacity_hours': round(capacity, 2),
            'load_pct': round(100.0 * cum / capacity, 1) if capacity > 0 else (None if cum <= 0 else 999.0),
            'free_hours': round(max(0.0, capacity - cum), 2),
            'free_from': free_from[0].isoformat() if free_from else (now.date().isoformat() if p['enabled'] else None),
            'jobs': [x['id'] for x in out_jobs if x['printer_id'] == p['id']],
        })

    tot_cap = sum(p['capacity_hours'] for p in plan_printers if p['enabled'])
    tot_dem = sum(p['queue_hours'] for p in plan_printers if p['enabled'])
    late_jobs = [j for j in out_jobs if j['late_predicted'] and not j['overdue']]
    overdue = [j for j in out_jobs if j['overdue']] + [
        {'id': j['id'], 'part': j['part'], 'due_date': j['due_date'], 'overdue': True, 'end': None}
        for j in no_duration if j['due_date'] and j['due_date'] < today]
    alerts = []
    for p in plan_printers:
        if p['enabled'] and p['load_pct'] is not None and p['load_pct'] > 100:
            alerts.append({'type': 'overload', 'printer_id': p['id'], 'printer_name': p['name'], 'load_pct': p['load_pct'],
                           'hours': p['queue_hours'], 'capacity': p['capacity_hours']})
    for j in late_jobs:
        alerts.append({'type': 'late_predicted', 'job_id': j['id'], 'part': j['part'], 'end': j['end'],
                       'due_date': j['due_date'], 'days_late': -j['slack_days'] if j['slack_days'] is not None else None})
    for j in overdue:
        alerts.append({'type': 'overdue', 'job_id': j['id'], 'part': j['part'], 'due_date': j['due_date']})
    if no_duration:
        alerts.append({'type': 'no_duration', 'count': len(no_duration), 'job_ids': [j['id'] for j in no_duration]})
    if open_jobs and not active:
        alerts.append({'type': 'no_printer'})

    return {
        'horizon_days': horizon_days,
        'generated': now.isoformat(timespec='minutes'),
        'summary': {
            'capacity_hours': round(tot_cap, 2), 'demand_hours': round(tot_dem, 2),
            'free_hours': round(max(0.0, tot_cap - tot_dem), 2),
            'load_pct': round(100.0 * tot_dem / tot_cap, 1) if tot_cap > 0 else None,
            'open_jobs': len(open_jobs), 'planned_jobs': len(out_jobs), 'late_predicted': len(late_jobs),
            'overdue': len(overdue), 'no_duration': len(no_duration),
        },
        'printers': plan_printers,
        'jobs': out_jobs,
        'no_duration': [{'id': j['id'], 'part': j['part'], 'client': j['client'], 'due_date': j['due_date'] or ''} for j in no_duration],
        'alerts': alerts,
    }


def on_time_rate(done_rows, since_iso):
    """Taux de respect des délais : part des commandes terminées avec une date de livraison, rendues à temps (done_at <= due_date).
    Retourne {'rate': pourcentage ou None, 'on_time', 'total'}."""
    total = on_time = 0
    for r in done_rows:
        due, done = (r['due_date'] or ''), (r['done_at'] or '')
        if not due or not done or done < since_iso:
            continue
        total += 1
        if done <= due:
            on_time += 1
    return {'rate': round(100.0 * on_time / total, 1) if total else None, 'on_time': on_time, 'total': total}


# ── coût, rendement, retards constatés ───────────────────────────

def _num(v):
    try:
        f = float(v)
        return f if f == f and abs(f) < 1e9 else 0.0
    except (TypeError, ValueError):
        return 0.0


def _cost_model(job):
    keys = job.keys() if hasattr(job, 'keys') else job
    try:
        raw = job['cost_model'] if 'cost_model' in keys else ''
        m = json.loads(raw or '{}') if isinstance(raw, str) else (raw or {})
    except (TypeError, ValueError):
        m = {}
    return {k: _num(m.get(k)) for k in ('m', 'e', 'w', 'f', 'weight_g', 'hours')}


LABOR_RATE_MAX = 1000.0


def clean_rate(v):
    """Taux horaire (€/h) du temps de travail humain : nombre entre 0 et 1000, 0 si absent ou invalide."""
    r = _num(v)
    return round(min(max(r, 0.0), LABOR_RATE_MAX), 2) if r == r else 0.0


def labor_minutes(job, basis='real'):
    """Temps de travail humain d'une commande, en minutes : préparation (`labor_setup_min`, une fois par commande) + `labor_min_piece`
    par pièce (retrait du plateau, ébavurage, assemblage, emballage…). `basis='est'` : toutes les pièces demandées ;
    `basis='real'` : pièces faites (la préparation compte dès que la commande est commencée) ; un temps mesuré
    (`labor_hours_actual`) remplace l'estimation réelle."""
    setup = max(_num(_g(job, 'labor_setup_min')), 0.0)
    per = max(_num(_g(job, 'labor_min_piece')), 0.0)
    qty = max(int(_g(job, 'quantity') or 1), 1)
    if basis == 'est':
        return setup + per * qty
    act = _num(_g(job, 'labor_hours_actual'))
    if act > 0:
        return act * 60.0
    done = min(max(int(_g(job, 'qty_done') or 0), 0), qty)
    started = done > 0 or _g(job, 'status') in ('printing', 'done')
    return (setup if started else 0.0) + per * done


def labor_cost(job, rate, basis='real'):
    return round(labor_minutes(job, basis) / 60.0 * clean_rate(rate), 2)


def order_cost(job, labor_rate=0.0):
    """Coût d'une commande, même modèle que la marge des commandes (devis chiffré : matière m, électricité e, machine w, frais fixes f
    par pièce). Estimé = devis × quantité ; réel à ce jour = pièces réellement faites + rebuts, au poids/temps mesurés quand ils
    existent. Retourne None si la commande ne vient pas d'un devis chiffré.
    {'est': {material, energy, machine, fixed, total}, 'real': {...}, 'waste': coût des rebuts, 'scrap', 'done', 'yield_pct'}"""
    m = _cost_model(job)
    if not (m['m'] or m['e'] or m['w'] or m['f']):
        return None
    qty = max(1, int(job['quantity'] or 1))
    done = min(max(int(job['qty_done'] or 0), 0), qty)
    scrap = max(int(job['scrap'] or 0), 0) if 'scrap' in (job.keys() if hasattr(job, 'keys') else job) else 0
    w_act = job['actual_weight_g'] if 'actual_weight_g' in job.keys() else None
    h_act = _num(job['actual_hours']) if 'actual_hours' in job.keys() else 0.0
    mat_pieces = (_num(w_act) / m['weight_g']) if (w_act is not None and m['weight_g'] > 0) else done
    time_pieces = (h_act / m['hours']) if (h_act > 0 and m['hours'] > 0) else done

    def _split(mat, ene, mach, fix):
        return {'material': round(mat, 2), 'energy': round(ene, 2), 'machine': round(mach, 2), 'fixed': round(fix, 2),
                'total': round(mat + ene + mach + fix, 2)}
    est = _split(m['m'] * qty, m['e'] * qty, m['w'] * qty, m['f'] * qty)
    real = _split((mat_pieces + scrap) * m['m'], (time_pieces + scrap) * m['e'], (time_pieces + scrap) * m['w'], m['f'] * done)
    if clean_rate(labor_rate) > 0 and (labor_minutes(job, 'est') > 0 or labor_minutes(job, 'real') > 0):
        for part, basis in ((est, 'est'), (real, 'real')):       # le temps de travail s'ajoute au coût (clé « labor » seulement s'il y en a)
            part['labor'] = labor_cost(job, labor_rate, basis)
            part['total'] = round(part['total'] + part['labor'], 2)
    return {'est': est, 'real': real, 'waste': round(scrap * (m['m'] + m['e'] + m['w']), 2), 'scrap': scrap, 'done': done,
            'yield_pct': round(100.0 * done / (done + scrap), 1) if (done + scrap) else None}


def _g(row, key, default=None):
    try:
        v = row[key]
    except (KeyError, IndexError):
        return default
    return default if v is None else v


def printer_profit(jobs, quote_totals, printers, since_iso, labor_rate=0.0):
    """Rentabilité par imprimante sur la période (commandes terminées depuis `since_iso` + en cours, annulées ignorées).
    Revenu d'une commande = total du devis réparti entre les commandes de ce devis au prorata des pièces faites ;
    coût = coût réel du modèle de coût (matière + électricité + machine + frais fixes, rebuts compris) ;
    heures = heures réellement saisies, sinon durée estimée × pièces faites. Une commande sans devis chiffré n'a ni revenu ni coût :
    elle est comptée à part (`unpriced`), jamais valorisée à zéro en silence. Sans imprimante : ligne « id = None »."""
    names = {p['id']: (p.get('name') or f"#{p['id']}") for p in printers}
    pieces_by_quote = {}
    for j in jobs:
        if j['status'] != 'cancelled' and _g(j, 'quote_id'):
            pieces_by_quote[_g(j, 'quote_id')] = pieces_by_quote.get(_g(j, 'quote_id'), 0) + max(int(j['quantity'] or 1), 1)
    rows = {}
    for j in jobs:
        if j['status'] == 'cancelled':
            continue
        done_at = (_g(j, 'done_at') or '')[:10]
        if j['status'] == 'done' and (not done_at or done_at < since_iso[:10]):
            continue
        pid = _g(j, 'printer_id')
        r = rows.setdefault(pid, {'printer_id': pid, 'name': names.get(pid, '—'), 'orders': 0, 'priced': 0, 'unpriced': 0, 'done': 0, 'scrap': 0,
                                  'hours': 0.0, 'revenue': 0.0, 'cost': 0.0, 'waste': 0.0, 'labor_hours': 0.0, 'labor_cost': 0.0})
        r['orders'] += 1
        qty = max(int(j['quantity'] or 1), 1)
        done = min(max(int(j['qty_done'] or 0), 0), qty)
        scrap = max(int(_g(j, 'scrap') or 0), 0)
        r['done'] += done
        r['scrap'] += scrap
        h = _num(_g(j, 'actual_hours'))
        if h <= 0:
            h = _num(_g(j, 'est_hours')) * done
        r['hours'] += h
        r['labor_hours'] += labor_minutes(j, 'real') / 60.0      # le temps humain est compté même sans devis chiffré (c'est du temps réel)
        c = order_cost(j, labor_rate)
        if not c:
            r['unpriced'] += 1
            continue
        r['priced'] += 1
        r['cost'] += c['real']['total']
        r['labor_cost'] += c['real'].get('labor', 0.0)
        r['waste'] += c['waste']
        total = _num(quote_totals.get(_g(j, 'quote_id'))) if _g(j, 'quote_id') else 0.0
        denom = pieces_by_quote.get(_g(j, 'quote_id'), 0)
        if total > 0 and denom:
            r['revenue'] += total * done / denom
    out = []
    for r in rows.values():
        margin = r['revenue'] - r['cost']
        out.append({**r, 'hours': round(r['hours'], 1), 'revenue': round(r['revenue'], 2), 'cost': round(r['cost'], 2), 'waste': round(r['waste'], 2),
                    'labor_hours': round(r['labor_hours'], 2), 'labor_cost': round(r['labor_cost'], 2),
                    'margin': round(margin, 2), 'margin_per_hour': round(margin / r['hours'], 2) if r['hours'] > 0 and r['priced'] else None,
                    'yield_pct': round(100.0 * r['done'] / (r['done'] + r['scrap']), 1) if (r['done'] + r['scrap']) else None})
    out.sort(key=lambda r: (r['margin_per_hour'] is None, -(r['margin_per_hour'] or 0), -r['orders']))
    return out


def production_stats(jobs, since_iso, today_iso):
    """Indicateurs de production sur la période : coût total des commandes (réel et estimé), rendement (pièces livrées contre rebuts),
    gaspillage (coût des rebuts) et retards constatés (commandes rendues après leur date de livraison).
    Périmètre : commandes terminées depuis `since_iso` + commandes en cours (coût à ce jour) ; les annulées sont ignorées."""
    est = real = waste = 0.0
    done_p = scrap_p = costed = 0
    by_order = []
    late_days = []
    due_total = 0
    for j in jobs:
        status = j['status']
        if status == 'cancelled':
            continue
        done_at = (j['done_at'] or '')[:10]
        if status == 'done' and (not done_at or done_at < since_iso[:10]):
            continue
        c = order_cost(j)
        scrap = max(int(j['scrap'] or 0), 0) if 'scrap' in j.keys() else 0
        qd = min(max(int(j['qty_done'] or 0), 0), max(1, int(j['quantity'] or 1)))
        done_p += qd
        scrap_p += scrap
        if c:
            costed += 1
            est += c['est']['total']
            real += c['real']['total']
            waste += c['waste']
            by_order.append({'id': j['id'], 'part': j['part'], 'client': j['client'], 'status': status,
                             'est': c['est']['total'], 'real': c['real']['total'], 'waste': c['waste'],
                             'scrap': c['scrap'], 'yield_pct': c['yield_pct'], 'done': c['done'], 'quantity': j['quantity']})
        due = (j['due_date'] or '')[:10]
        if status == 'done' and due and done_at:
            due_total += 1
            if done_at > due:
                try:
                    late_days.append((datetime.date.fromisoformat(done_at) - datetime.date.fromisoformat(due)).days)
                except ValueError:
                    pass
    by_order.sort(key=lambda r: (-r['real'], r['id']))
    return {
        'cost': {'est': round(est, 2), 'real': round(real, 2), 'waste': round(waste, 2), 'orders': costed},
        'yield': {'rate': round(100.0 * done_p / (done_p + scrap_p), 1) if (done_p + scrap_p) else None, 'done': done_p, 'scrap': scrap_p},
        'delays': {'late': len(late_days), 'total': due_total,
                   'avg_days': round(sum(late_days) / len(late_days), 1) if late_days else 0,
                   'max_days': max(late_days) if late_days else 0},
        'by_order': by_order[:12],
    }


# ── accès base ────────────────────────────────────────────────────────────

def _ensure_tables():
    conn = get_db()
    if conn is None:
        return
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS planning_capacity (
            user_id INTEGER NOT NULL,
            printer_id INTEGER NOT NULL DEFAULT 0,
            hours_per_day REAL,
            days TEXT DEFAULT '',
            enabled INTEGER DEFAULT 1,
            PRIMARY KEY (user_id, printer_id)
        )""")
        pc = {r['name'] for r in conn.execute("PRAGMA table_info(planning_capacity)").fetchall()}
        if 'labor_rate' not in pc:
            conn.execute("ALTER TABLE planning_capacity ADD COLUMN labor_rate REAL DEFAULT 0")     # taux horaire du temps de travail humain
        cols = {r['name'] for r in conn.execute("PRAGMA table_info(print_jobs)").fetchall()}
        if cols and 'est_hours' not in cols:
            conn.execute("ALTER TABLE print_jobs ADD COLUMN est_hours REAL DEFAULT 0")
        for name in ('labor_setup_min', 'labor_min_piece', 'labor_hours_actual'):
            if cols and name not in cols:
                conn.execute(f"ALTER TABLE print_jobs ADD COLUMN {name} REAL DEFAULT 0")
        conn.commit()
    finally:
        conn.close()


def load_settings_for(uid):
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM planning_capacity WHERE user_id=?", (uid,)).fetchall()
    finally:
        conn.close()
    out = {'default': {'hours_per_day': DEFAULT_HOURS_PER_DAY, 'days': list(DEFAULT_DAYS)}, 'printers': {}, 'labor_rate': 0.0}
    for r in rows:
        entry = {'hours_per_day': r['hours_per_day'], 'days': parse_days(r['days']) if r['days'] else None,
                 'enabled': bool(r['enabled'])}
        if r['printer_id'] == 0:
            out['default'] = {'hours_per_day': clamp_hours(r['hours_per_day']), 'days': list(parse_days(r['days']))}
            try:
                out['labor_rate'] = clean_rate(r['labor_rate'])
            except (IndexError, KeyError):
                pass
        else:
            out['printers'][r['printer_id']] = entry
    return out


def _statuses(printers_cfg):
    """États des imprimantes (en parallèle, avec le cache habituel) ; une imprimante qui ne répond pas est « offline »."""
    result = {}

    def _one(p):
        try:
            result[p['id']] = _printer_status_cached(p) or {}
        except Exception as e:
            result[p['id']] = {'status': 'offline', 'error': str(e)}
    threads = [threading.Thread(target=_one, args=(p,), daemon=True) for p in printers_cfg]
    for t in threads:
        t.start()
    deadline = time.monotonic() + 8
    for t in threads:
        t.join(timeout=max(0.1, deadline - time.monotonic()))
    for p in printers_cfg:
        result.setdefault(p['id'], {'status': 'offline'})
    return result


def build_plan(uid, horizon=14, now=None):
    now = now or datetime.datetime.now()
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM print_jobs WHERE user_id=?", (uid,)).fetchall()
        try:
            quote_totals = {q['id']: q['total_value'] for q in conn.execute("SELECT id, total_value FROM quotes WHERE user_id=?", (uid,)).fetchall()}
        except Exception:
            quote_totals = {}
        prows = conn.execute("SELECT * FROM printers WHERE user_id=? ORDER BY id", (uid,)).fetchall()
    finally:
        conn.close()
    printers_cfg = [parse_printer_config(r) for r in prows]
    statuses = _statuses(printers_cfg)
    result = plan(rows, [{'id': p['id'], 'name': p.get('name')} for p in printers_cfg], statuses,
                  load_settings_for(uid), now, horizon)
    since = (now.date() - datetime.timedelta(days=90)).isoformat()
    result['on_time'] = on_time_rate([r for r in rows if r['status'] == 'done'], since)
    result['stats'] = production_stats(rows, since, now.date().isoformat())
    lrate = (load_settings_for(uid) or {}).get('labor_rate', 0.0)
    result['labor_rate'] = lrate
    result['printer_profit'] = printer_profit(rows, quote_totals, [{'id': p['id'], 'name': p.get('name')} for p in printers_cfg], since, lrate)
    costs = {r['id']: order_cost(r, lrate) for r in rows if r['status'] in ('queued', 'printing')}
    for j in result['jobs']:
        c = costs.get(j['id'])
        j['cost_est'] = c['est']['total'] if c else None
    return result


# ── routes ────────────────────────────────────────────────────────────────

def api_planning():
    try:
        horizon = int(request.args.get('horizon') or 14)
    except (TypeError, ValueError):
        horizon = 14
    try:
        return jsonify(build_plan(session['user_id'], horizon))
    except Exception as e:
        app_logger.error(f"[PLANNING] Calcul impossible : {e}")
        return jsonify({'error': 'internal'}), 500


def api_planning_settings_get():
    uid = session['user_id']
    s = load_settings_for(uid)
    conn = get_db()
    try:
        printers = [{'id': r['id'], 'name': r['name']} for r in conn.execute(
            "SELECT id, name FROM printers WHERE user_id=? ORDER BY id", (uid,)).fetchall()]
    finally:
        conn.close()
    items = []
    for p in printers:
        cfg = s['printers'].get(p['id']) or {}
        items.append({'id': p['id'], 'name': p['name'], 'enabled': cfg.get('enabled', True),
                      'hours_per_day': cfg.get('hours_per_day'), 'days': list(cfg['days']) if cfg.get('days') else None})
    return jsonify({'default': s['default'], 'printers': items, 'labor_rate': s.get('labor_rate', 0.0)})


def api_planning_settings_put():
    uid = session['user_id']
    data = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        d = data.get('default') if isinstance(data.get('default'), dict) else None
        old_row = conn.execute("SELECT * FROM planning_capacity WHERE user_id=? AND printer_id=0", (uid,)).fetchone()
        rate = clean_rate(data['labor_rate']) if 'labor_rate' in data else clean_rate(old_row['labor_rate'] if old_row else 0)
        if d is None and 'labor_rate' in data:                    # seul le taux change : on garde les heures et les jours déjà réglés
            d = {'hours_per_day': old_row['hours_per_day'] if old_row else None, 'days': (old_row['days'] if old_row else '') or None}
        if d is not None:
            conn.execute("INSERT OR REPLACE INTO planning_capacity (user_id, printer_id, hours_per_day, days, enabled, labor_rate) VALUES (?,?,?,?,1,?)",
                         (uid, 0, clamp_hours(d.get('hours_per_day')), ','.join(map(str, parse_days(d.get('days')))), rate))
        mine = {r['id'] for r in conn.execute("SELECT id FROM printers WHERE user_id=?", (uid,)).fetchall()}
        for item in (data.get('printers') or []):
            try:
                pid = int(item.get('id'))
            except (TypeError, ValueError, AttributeError):
                continue
            if pid not in mine:
                continue
            hpd = item.get('hours_per_day')
            hpd = None if hpd in (None, '') else clamp_hours(hpd)
            days = item.get('days')
            days_s = ','.join(map(str, parse_days(days))) if days else ''
            conn.execute("INSERT OR REPLACE INTO planning_capacity (user_id, printer_id, hours_per_day, days, enabled) VALUES (?,?,?,?,?)",
                         (uid, pid, hpd, days_s, 0 if item.get('enabled') in (False, 0, '0', 'false') else 1))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'success': True})


# ── alertes (notifications) ───────────────────────────────────────────────

def _tx(key, default):
    try:
        return _server_t(key, default) if _server_t else default
    except Exception:
        return default


def _notify(uid, ntype, title, message, key, event=None, data=None):
    if _insert_notification_once and _insert_notification_once(uid, ntype, title, message, 'planning', key):
        if event and _webhook_emit:        # même dédoublonnage que la notification : une fois par commande / par jour
            try:
                _webhook_emit(event, data or {}, uid)
            except Exception:
                pass
        try:
            if _send_native_notification:
                _send_native_notification(title, message)
            if _push_notify_async:
                _push_notify_async(ntype, title, message)
        except Exception:
            pass


def planning_alerts_once(now=None):
    """Crée les notifications de surcharge et de retard prévisible (une par commande/imprimante et par jour : dédoublonnage)."""
    now = now or datetime.datetime.now()
    conn = get_db()
    try:
        uids = [r['user_id'] for r in conn.execute(
            "SELECT DISTINCT user_id FROM print_jobs WHERE status IN ('queued','printing')").fetchall()]
    finally:
        conn.close()
    today = now.date().isoformat()
    for uid in uids:
        try:
            res = build_plan(uid, 14, now)
        except Exception as e:
            app_logger.debug(f"[PLANNING] Alertes ignorées ({uid}) : {e}")
            continue
        for a in res['alerts']:
            if a['type'] == 'late_predicted':
                _notify(uid, 'planning_late', _tx('notif.plan_late_title', 'Retard prévisible'),
                        f"{a['part']} — {a['end']} > {a['due_date']}", f"plan_late_{a['job_id']}_{a['end']}",
                        'order.late', {'order': {'id': a['job_id'], 'part': a['part']}, 'estimated_end': a['end'], 'due_date': a['due_date']})
            elif a['type'] == 'overload':
                _notify(uid, 'planning_overload', _tx('notif.plan_overload_title', 'Imprimante surchargée'),
                        f"{a['printer_name']} — {a['hours']:g} h / {a['capacity']:g} h", f"plan_over_{a['printer_id']}_{today}",
                        'printer.overload', {'printer': {'id': a['printer_id'], 'name': a['printer_name']}, 'load_hours': a['hours'], 'capacity_hours': a['capacity']})


def _planning_loop():
    time.sleep(90)
    while True:
        try:
            planning_alerts_once()
        except Exception as e:
            app_logger.debug(f"[PLANNING] Boucle d'alertes : {e}")
        time.sleep(1800)


def autostart():
    threading.Thread(target=_planning_loop, daemon=True, name='stellio-planning').start()


_ROUTES = (
    ('/api/planning', ['GET'], 'api_planning', ('login_required', )),
    ('/api/planning/settings', ['GET'], 'api_planning_settings_get', ('login_required', )),
    ('/api/planning/settings', ['PUT'], 'api_planning_settings_put', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"production_planning.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if routes:
        try:
            _ensure_tables()
        except Exception as e:
            try:
                app_logger.warning(f"[PLANNING] Tables non préparées : {e}")
            except Exception:
                pass
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {}
