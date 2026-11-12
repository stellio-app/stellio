"""Stellio — résumé quotidien ou hebdomadaire (notification + push)

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `digest.init(globals())` une fois
toutes ses fonctions définies, puis `digest.start_worker()` au démarrage du serveur.

Le résumé rassemble : tâches terminées, commandes en retard, énergie consommée, bobines presque vides (ou bientôt vides d'après
les pesées), factures en retard, devis en attente / acceptés par le client, pièces dont le stock est bas.
Il est envoyé comme une notification Stellio et par les canaux push déjà configurés (ntfy, Telegram, Discord, webhook).
Réglages (dans les réglages généraux) : `digest_enabled`, `digest_frequency` (daily | weekly), `digest_hour`, `digest_weekday`.
Chaque résumé n'est envoyé qu'une fois par période (`digest_last_key`).
"""
import datetime
import threading
import time

_REQUIRED = (
    '_insert_notification_once',
    '_is_low_stock',
    '_push_notify_async',
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'load_settings',
    'login_required',
    'request',
    'save_settings',
    'session',
)
_OPTIONAL = ('_system_ui_lang',)
_OVERRIDABLE = ('datetime', 'threading', 'time')

_MAIN = {}
_insert_notification_once = None
_is_low_stock = None
_push_notify_async = None
_system_ui_lang = None
app = None
app_logger = None
get_db = None
jsonify = None
load_settings = None
login_required = None
request = None
save_settings = None
session = None

_STARTED = False
_SEND_LOCK = threading.Lock()
LOOP_SECONDS = 300

_TXT = {
    'fr': {'title_daily': 'Résumé du jour', 'title_weekly': 'Résumé de la semaine', 'nothing': 'Rien à signaler.',
           'done': '{n} tâche(s) terminée(s), {p} pièce(s) imprimée(s)', 'late': '{n} commande(s) en retard',
           'energy': 'Énergie : {kwh} kWh, coût {cost}', 'spools': 'Bobines à surveiller : {names}',
           'overdue': '{n} facture(s) en retard ({total})', 'pending': '{n} devis en attente de réponse',
           'accepted': '{n} devis accepté(s) par le client', 'parts': 'Stock bas : {names}'},
    'en': {'title_daily': 'Daily summary', 'title_weekly': 'Weekly summary', 'nothing': 'Nothing to report.',
           'done': '{n} job(s) finished, {p} part(s) printed', 'late': '{n} late order(s)',
           'energy': 'Energy: {kwh} kWh, cost {cost}', 'spools': 'Spools to watch: {names}',
           'overdue': '{n} overdue invoice(s) ({total})', 'pending': '{n} quote(s) awaiting an answer',
           'accepted': '{n} quote(s) accepted by the customer', 'parts': 'Low stock: {names}'},
}


def _lang():
    try:
        lg = (_system_ui_lang() if _system_ui_lang else 'en') or 'en'
    except Exception:
        lg = 'en'
    return 'fr' if lg == 'fr' else 'en'


def _one(conn, sql, args=()):
    try:
        return conn.execute(sql, args).fetchone()
    except Exception:
        return None     # table ou colonne absente (fonction pas encore utilisée)


def collect(uid, days):
    """Chiffres du résumé sur les `days` derniers jours (dict ; chaque entrée absente = rien à signaler)."""
    today = datetime.date.today()
    since_day = (today - datetime.timedelta(days=days)).isoformat()
    since_dt = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    out = {}
    conn = get_db()
    try:
        r = _one(conn, "SELECT COUNT(*) AS n, COALESCE(SUM(qty_done),0) AS p FROM print_jobs WHERE user_id=? AND status='done' "
                       "AND substr(done_at,1,10)>=?", (uid, since_day))
        if r and r['n']:
            out['done'] = {'n': r['n'], 'p': int(r['p'] or 0)}
        r = _one(conn, "SELECT COUNT(*) AS n FROM print_jobs WHERE user_id=? AND status IN ('queued','printing') "
                       "AND due_date!='' AND due_date<?", (uid, today.isoformat()))
        if r and r['n']:
            out['late'] = {'n': r['n']}
        r = _one(conn, "SELECT COALESCE(SUM(energy_wh),0) AS wh, COALESCE(SUM(energy_wh*COALESCE(price_kwh,0)/1000.0),0) AS cost "
                       "FROM print_energy WHERE user_id=? AND ended_at>=?", (uid, since_dt))
        if r and (r['wh'] or 0) > 0:
            out['energy'] = {'kwh': round(r['wh'] / 1000.0, 2), 'cost': round(r['cost'] or 0, 2)}
        names = []
        try:
            for s in conn.execute("SELECT name, remaining_g, capacity_g FROM manual_filament_spools WHERE user_id=? AND archived=0", (uid,)).fetchall():
                if _is_low_stock(s['remaining_g'], s['capacity_g']):
                    names.append(s['name'])
        except Exception:
            pass
        try:
            from modules import filament_weighing as fw
            for f in fw.build_forecast(uid):
                if f['days_left'] is not None and f['days_left'] <= 7 and f['name'] not in names:
                    names.append(f"{f['name']} (~{int(f['days_left'])} j)")
        except Exception:
            pass
        if names:
            out['spools'] = {'names': names[:6], 'more': max(len(names) - 6, 0)}
        r = _one(conn, "SELECT COUNT(*) AS n, COALESCE(SUM(total_value),0) AS t FROM quotes WHERE user_id=? "
                       "AND doc_type IN ('invoice','deposit') AND COALESCE(status,'')!='paid' AND due_date!='' AND due_date<?",
                 (uid, today.isoformat()))
        if r and r['n']:
            out['overdue'] = {'n': r['n'], 'total': round(r['t'] or 0, 2)}
        r = _one(conn, "SELECT COUNT(*) AS n FROM quotes WHERE user_id=? AND COALESCE(doc_type,'quote')='quote' AND status='sent'", (uid,))
        if r and r['n']:
            out['pending'] = {'n': r['n']}
        r = _one(conn, "SELECT COUNT(*) AS n FROM quotes WHERE user_id=? AND status='accepted' AND decision_at!='' AND substr(decision_at,1,10)>=?",
                 (uid, since_day))
        if r and r['n']:
            out['accepted'] = {'n': r['n']}
        try:
            rows = conn.execute("SELECT name FROM parts_stock WHERE user_id=? AND min_qty>0 AND qty<=min_qty ORDER BY name", (uid,)).fetchall()
            if rows:
                out['parts'] = {'names': [x['name'] for x in rows][:6]}
        except Exception:
            pass
    finally:
        conn.close()
    return out


def render(data, frequency, lang=None):
    t = _TXT[lang or _lang()]
    lines = []
    if 'done' in data:
        lines.append(t['done'].format(**data['done']))
    if 'late' in data:
        lines.append(t['late'].format(**data['late']))
    if 'energy' in data:
        e = data['energy']
        lines.append(t['energy'].format(kwh=e['kwh'], cost=f"{e['cost']:.2f}"))
    if 'spools' in data:
        names = ', '.join(data['spools']['names']) + (f" +{data['spools']['more']}" if data['spools']['more'] else '')
        lines.append(t['spools'].format(names=names))
    if 'overdue' in data:
        lines.append(t['overdue'].format(n=data['overdue']['n'], total=f"{data['overdue']['total']:.2f}"))
    if 'pending' in data:
        lines.append(t['pending'].format(**data['pending']))
    if 'accepted' in data:
        lines.append(t['accepted'].format(**data['accepted']))
    if 'parts' in data:
        lines.append(t['parts'].format(names=', '.join(data['parts']['names'])))
    title = t['title_weekly'] if frequency == 'weekly' else t['title_daily']
    return title, ('\n'.join(lines) if lines else t['nothing'])


def get_config():
    s = load_settings() or {}
    freq = s.get('digest_frequency') if s.get('digest_frequency') in ('daily', 'weekly') else 'daily'
    try:
        hour = max(0, min(23, int(s.get('digest_hour', 8))))
    except (TypeError, ValueError):
        hour = 8
    try:
        wd = max(0, min(6, int(s.get('digest_weekday', 0))))
    except (TypeError, ValueError):
        wd = 0
    return {'enabled': bool(s.get('digest_enabled', False)), 'frequency': freq, 'hour': hour, 'weekday': wd}


def period_key(now, cfg):
    """Clé de la période en cours si le résumé est dû maintenant, sinon None."""
    if cfg['frequency'] == 'weekly':
        due = now.weekday() > cfg['weekday'] or (now.weekday() == cfg['weekday'] and now.hour >= cfg['hour'])
        iso = now.isocalendar()
        return f"weekly:{iso[0]}-W{iso[1]:02d}" if due else None
    return f"daily:{now.date().isoformat()}" if now.hour >= cfg['hour'] else None


def send_digest(uid, frequency, force=False):
    """Compose et envoie le résumé. Sans `force`, un résumé entièrement vide n'est pas envoyé (quotidien). Retourne (envoyé, titre, texte)."""
    days = 7 if frequency == 'weekly' else 1
    data = collect(uid, days)
    title, text = render(data, frequency)
    if not data and frequency != 'weekly' and not force:
        return False, title, text
    now = datetime.datetime.now()
    if force:
        key = f"digest:{frequency}:now:{now.strftime('%Y%m%d%H%M%S')}"
    elif frequency == 'weekly':
        iso = now.isocalendar()
        key = f"digest:weekly:{iso[0]}-W{iso[1]:02d}"
    else:
        key = f"digest:daily:{now.date().isoformat()}"
    _insert_notification_once(uid, 'info', title, text, 'dashboard', key)
    _push_notify_async('info', title, text)
    return True, title, text


def _user_ids():
    conn = get_db()
    try:
        return [r['id'] for r in conn.execute("SELECT id FROM users WHERE COALESCE(role,'') != 'viewer'").fetchall()]
    except Exception:
        return []
    finally:
        conn.close()


def tick(now=None):
    """Une passe du planificateur (testable) : envoie le résumé s'il est dû et pas encore envoyé pour cette période."""
    cfg = get_config()
    # tâches de fond liées : alertes de stock de pièces, comptage des réassorts terminés
    try:
        from modules import parts_stock
        for uid in _user_ids():
            parts_stock.check_low_stock(uid)
    except Exception as e:
        app_logger.debug(f"[RÉSUMÉ] Stock de pièces ignoré : {e}")
    if not cfg['enabled']:
        return False
    now = now or datetime.datetime.now()
    key = period_key(now, cfg)
    if not key:
        return False
    with _SEND_LOCK:
        s = load_settings() or {}
        if s.get('digest_last_key') == key:
            return False
        sent_any = False
        for uid in _user_ids():
            try:
                ok, _t, _x = send_digest(uid, cfg['frequency'])
                sent_any = sent_any or ok
            except Exception as e:
                app_logger.warning(f"[RÉSUMÉ] Envoi impossible (utilisateur {uid}) : {e}")
        s['digest_last_key'] = key
        save_settings(s)
        return sent_any


def _loop():
    time.sleep(60)
    while True:
        try:
            tick()
        except Exception as e:
            app_logger.warning(f"[RÉSUMÉ] Passe ignorée : {e}")
        time.sleep(LOOP_SECONDS)


def start_worker():
    global _STARTED
    if _STARTED:
        return
    _STARTED = True
    threading.Thread(target=_loop, daemon=True, name='stellio-digest').start()


# ── Routes ──────────────────────────────────────────────────────────────────────────────────
def api_digest_settings():
    if request.method == 'GET':
        return jsonify(get_config())
    data = request.get_json(silent=True) or {}
    s = load_settings() or {}
    if 'enabled' in data:
        s['digest_enabled'] = bool(data.get('enabled'))
    if data.get('frequency') in ('daily', 'weekly'):
        s['digest_frequency'] = data['frequency']
    for key, name, hi in (('hour', 'digest_hour', 23), ('weekday', 'digest_weekday', 6)):
        if key in data:
            try:
                s[name] = max(0, min(hi, int(data[key])))
            except (TypeError, ValueError):
                return jsonify({'success': False, 'error': f'bad_{key}'}), 400
    save_settings(s)
    return jsonify({'success': True, **get_config()})


def api_digest_preview():
    freq = 'weekly' if request.args.get('frequency') == 'weekly' else 'daily'
    data = collect(session['user_id'], 7 if freq == 'weekly' else 1)
    title, text = render(data, freq)
    return jsonify({'frequency': freq, 'title': title, 'text': text, 'data': data})


def api_digest_send_now():
    freq = 'weekly' if (request.get_json(silent=True) or {}).get('frequency') == 'weekly' else 'daily'
    sent, title, text = send_digest(session['user_id'], freq, force=True)
    return jsonify({'success': True, 'sent': sent, 'title': title, 'text': text})


_ROUTES = (
    ('/api/digest/settings', ['GET', 'POST'], 'api_digest_settings', ('login_required', )),
    ('/api/digest/preview', ['GET'], 'api_digest_preview', ('login_required', )),
    ('/api/digest/send-now', ['POST'], 'api_digest_send_now', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"digest.init : services manquants : {missing}")
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
