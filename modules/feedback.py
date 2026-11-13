"""Stellio — suggestions et signalements envoyés comme issues GitHub

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `feedback.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import datetime
import platform
import re
import requests
import time

_REQUIRED = (
    'CURRENT_VERSION',
    'FEEDBACK_LIMITS',
    'FEEDBACK_MIN_SUBMIT_INTERVAL',
    'FEEDBACK_TYPES',
    '_feedback_find',
    '_feedback_last_submit',
    '_feedback_load',
    '_feedback_lock',
    '_feedback_public',
    '_feedback_refresh',
    '_feedback_relay',
    '_feedback_repo',
    '_feedback_save',
    '_feedback_status',
    '_gh_headers',
    'app',
    'app_logger',
    'get_user_lang',
    'jsonify',
    'login_required',
    'request',
)
_OPTIONAL = ()   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('datetime', 'platform', 're', 'requests', 'time', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
CURRENT_VERSION = None
FEEDBACK_LIMITS = None
FEEDBACK_MIN_SUBMIT_INTERVAL = None
FEEDBACK_TYPES = None
_feedback_find = None
_feedback_last_submit = None
_feedback_load = None
_feedback_lock = None
_feedback_public = None
_feedback_refresh = None
_feedback_relay = None
_feedback_repo = None
_feedback_save = None
_feedback_status = None
_gh_headers = None
app = None
app_logger = None
get_user_lang = None
jsonify = None
login_required = None
request = None


def api_feedback_submit():
    global _feedback_last_submit
    d = request.get_json(silent=True) or {}
    ftype = d.get('type')
    title = re.sub(r'\s+', ' ', str(d.get('title') or '')).strip()
    desc = str(d.get('description') or '').strip()
    L = FEEDBACK_LIMITS
    if ftype not in FEEDBACK_TYPES:
        return jsonify({"error": "invalid_type"}), 400
    if not (L['title_min'] <= len(title) <= L['title_max']):
        return jsonify({"error": "invalid_title"}), 400
    if not (L['desc_min'] <= len(desc) <= L['desc_max']):
        return jsonify({"error": "invalid_description"}), 400
    if d.get('consent') is not True:
        return jsonify({"error": "consent_required"}), 400
    relay = _feedback_relay()
    if not relay:
        return jsonify({"error": "relay_not_configured"}), 503

    with _feedback_lock:
        if time.time() - _feedback_last_submit < FEEDBACK_MIN_SUBMIT_INTERVAL:
            return jsonify({"error": "too_fast"}), 429
        _feedback_last_submit = time.time()

    include_tech = bool(d.get('include_tech'))
    payload = {'type': ftype, 'title': title, 'description': desc, 'consent': True,
               'include_tech': include_tech, 'website': ''}
    if include_tech:
        try:
            summary = _MAIN.get('_printers_tech_summary')
            printers = summary() if summary else []
        except Exception:
            printers = []
        block = f"\n\n**Imprimantes ({len(printers)})**\n" + ("\n".join(
            f"- {p['type']}" + (f" · {p['model']}" if p.get('model') else '') + (" · connectée" if p.get('connected') else " · hors ligne")
            for p in printers[:20]) if printers else "- aucune")
        room = max(0, FEEDBACK_LIMITS['desc_max'] - len(desc))
        if room >= 40:                                    # la liste complète n'est jamais coupée au milieu d'une ligne
            payload['description'] = desc + block[:room].rsplit('\n', 1)[0] if len(block) > room else desc + block
        payload.update({'version': CURRENT_VERSION, 'os': f"{platform.system()} {platform.release()}".strip(),
                        'lang': get_user_lang()})
    try:
        res = requests.post(f"{relay}/issue", json=payload, timeout=25,
                            headers={'User-Agent': f'Stellio-App/{CURRENT_VERSION}'})
    except Exception as e:
        app_logger.warning(f"[FEEDBACK] Relais injoignable : {e}")
        return jsonify({"error": "relay_unreachable"}), 502
    if res.status_code == 429:
        return jsonify({"error": "too_fast"}), 429
    if res.status_code != 201:
        app_logger.warning(f"[FEEDBACK] Le relais a répondu {res.status_code} : {res.text[:200]}")
        return jsonify({"error": "relay_error"}), 502
    issue = res.json()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry = {'number': int(issue['number']), 'title': title, 'type': ftype, 'url': issue.get('url'),
             'manage_token': issue.get('manage_token'), 'created_at': now_iso, 'updated_at': now_iso,
             'state': 'open', 'state_reason': None, 'labels': [], 'comments': 0,
             'seen_status': 'sent', 'seen_comments': 0, 'checked_at': time.time()}
    with _feedback_lock:
        entries = _feedback_load()
        entries.insert(0, entry)
        _feedback_save(entries)
    app_logger.info(f"[FEEDBACK] Demande #{entry['number']} créée ({ftype})")
    return jsonify({"success": True, "request": _feedback_public(entry)}), 201

def api_feedback_requests():
    with _feedback_lock:
        entries = _feedback_load()
        changed, limited = [], False
        if request.args.get('refresh') == '1' and entries:
            changed, limited = _feedback_refresh(entries)
            _feedback_save(entries)
        return jsonify({'requests': [_feedback_public(e) for e in entries], 'changed': changed,
                        'rate_limited': limited}), 200

def api_feedback_detail(number):
    with _feedback_lock:
        entries = _feedback_load()
        e = _feedback_find(entries, number)
        if not e:
            return jsonify({"error": "not_found"}), 404
    body, comments = '', []
    try:
        base = f"https://api.github.com/repos/{_feedback_repo()}/issues/{number}"
        r1 = requests.get(base, headers=_gh_headers(), timeout=10)
        if r1.status_code == 200:
            body = (r1.json().get('body') or '')
            body = body.split('\n---\n')[0].strip()   
        r2 = requests.get(base + '/comments?per_page=50', headers=_gh_headers(), timeout=10)
        if r2.status_code == 200:
            for c in r2.json():
                comments.append({'author': (c.get('user') or {}).get('login', ''),
                                 'is_team': c.get('author_association') in ('OWNER', 'MEMBER', 'COLLABORATOR'),
                                 'body': c.get('body') or '', 'created_at': c.get('created_at')})
    except Exception as ex:
        app_logger.debug(f"[FEEDBACK] Détail indisponible (#{number}) : {ex}")
    with _feedback_lock:
        entries = _feedback_load()
        e = _feedback_find(entries, number)
        if e:
            if comments:
                e['comments'] = max(e.get('comments', 0), len(comments))
            e['seen_status'] = _feedback_status(e)
            e['seen_comments'] = e.get('comments', 0)
            _feedback_save(entries)
            return jsonify({'request': _feedback_public(e), 'body': body, 'comments': comments}), 200
    return jsonify({"error": "not_found"}), 404

def api_feedback_close():
    number = (request.get_json(silent=True) or {}).get('number')
    with _feedback_lock:
        entries = _feedback_load()
        e = _feedback_find(entries, number)
        if not e or not e.get('manage_token'):
            return jsonify({"error": "not_found"}), 404
    relay = _feedback_relay()
    if not relay:
        return jsonify({"error": "relay_not_configured"}), 503
    try:
        res = requests.post(f"{relay}/issue/close", json={'number': number, 'manage_token': e['manage_token']},
                            timeout=20, headers={'User-Agent': f'Stellio-App/{CURRENT_VERSION}'})
    except Exception as ex:
        app_logger.warning(f"[FEEDBACK] Fermeture impossible : {ex}")
        return jsonify({"error": "relay_unreachable"}), 502
    if res.status_code != 200:
        return jsonify({"error": "relay_error"}), 502
    with _feedback_lock:
        entries = _feedback_load()
        e = _feedback_find(entries, number)
        if e:
            e.update({'state': 'closed', 'state_reason': 'not_planned', 'closed_by_user': True,
                      'etag': None, 'checked_at': 0, 'seen_status': 'closed_by_you',
                      'seen_comments': e.get('comments', 0) + 1, 'comments': e.get('comments', 0) + 1})
            _feedback_save(entries)
            return jsonify({'request': _feedback_public(e)}), 200
    return jsonify({"error": "not_found"}), 404

def api_feedback_remove():
    number = (request.get_json(silent=True) or {}).get('number')
    with _feedback_lock:
        entries = [e for e in _feedback_load() if e.get('number') != number]
        _feedback_save(entries)
    return jsonify({"success": True}), 200


_ROUTES = (
    ('/api/feedback/submit', ['POST'], 'api_feedback_submit', ('login_required', )),
    ('/api/feedback/requests', ['GET'], 'api_feedback_requests', ('login_required', )),
    ('/api/feedback/request/<int:number>', ['GET'], 'api_feedback_detail', ('login_required', )),
    ('/api/feedback/close', ['POST'], 'api_feedback_close', ('login_required', )),
    ('/api/feedback/remove', ['POST'], 'api_feedback_remove', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"feedback.init : services manquants : {missing}")
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
