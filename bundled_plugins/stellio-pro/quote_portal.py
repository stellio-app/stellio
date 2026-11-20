"""Stellio — portail client des devis (lien public, acceptation en ligne, informations de paiement de l'acompte)

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `quote_portal.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.

Principe : le propriétaire crée un lien public pour un devis (`POST /api/quotes/<id>/portal`). Le client ouvre
`/quote/<jeton>`, consulte le devis (PDF), l'accepte ou le refuse. L'acceptation crée la tâche d'impression
(comme le bouton « Accepté » de l'application) et prévient le propriétaire. Stellio ne traite AUCUN paiement : il affiche
seulement le texte et le lien de paiement que le propriétaire a saisis dans ses réglages.
Les données publiques sont minimales : jamais de notes internes, de marge, de coût ni de prix unitaire.
"""
import datetime
import io
import json
import os
import re
import secrets
import threading
import time

_REQUIRED = (
    'QUOTES_DIR',
    'Response',
    '_build_quote_pdf_with_repair',
    '_create_jobs_from_quote',
    '_ensure_quote_columns',
    '_insert_notification_once',
    '_push_notify_async',
    '_quote_payload_path',
    '_safe_quote_pdf_filename',
    '_stored_quote',
    '_stored_quote_path',
    'app',
    'app_logger',
    'get_db',
    'get_local_ip',
    'get_remote_state',
    'jsonify',
    'load_settings',
    'login_required',
    'request',
    'save_settings',
    'send_file',
    'session',
)
_OVERRIDABLE = ('datetime', 'io', 'json', 'os', 'secrets', 'time')

_MAIN = {}
QUOTES_DIR = None
Response = None
_build_quote_pdf_with_repair = None
_create_jobs_from_quote = None
_ensure_quote_columns = None
_insert_notification_once = None
_push_notify_async = None
_quote_payload_path = None
_safe_quote_pdf_filename = None
_stored_quote = None
_stored_quote_path = None
app = None
app_logger = None
get_db = None
get_local_ip = None
get_remote_state = None
jsonify = None
load_settings = None
login_required = None
request = None
save_settings = None
send_file = None
session = None

_COLS_DONE = False
_COLS_LOCK = threading.Lock()
_DECISION_LOG = {}        # ip -> [horodatages] : limite les décisions publiques
_DECISION_LOCK = threading.Lock()
DECISION_MAX_PER_MIN = 10


def _ensure_portal_columns():
    """Colonnes du portail : jeton public, date et auteur de la décision du client."""
    global _COLS_DONE
    if _COLS_DONE:
        return
    with _COLS_LOCK:
        if _COLS_DONE:
            return
        _ensure_quote_columns()
        conn = get_db()
        try:
            cols = {r['name'] for r in conn.execute("PRAGMA table_info(quotes)").fetchall()}
            for name, ddl in (('public_token', "TEXT DEFAULT ''"), ('decision_at', "TEXT DEFAULT ''"),
                              ('decision_by', "TEXT DEFAULT ''")):
                if name not in cols:
                    conn.execute(f"ALTER TABLE quotes ADD COLUMN {name} {ddl}")
            conn.commit()
        finally:
            conn.close()
        _COLS_DONE = True


def _external_base():
    """Adresse publique (accès distant prêt), sinon None : un lien de devis doit s'ouvrir depuis Internet, jamais une adresse locale."""
    rs = get_remote_state()
    if rs.get('status') == 'ready' and rs.get('url'):
        return rs['url'].rstrip('/')
    return None


def _remote_info():
    rs = get_remote_state()
    return {'remote': bool(_external_base()), 'remote_status': rs.get('status') or 'disabled', 'remote_mode': rs.get('mode') or '',
            'remote_enabled': bool((load_settings() or {}).get('remote_access_enabled'))}


def _clean_link(url):
    """Seuls les liens http(s) sont acceptés (jamais javascript: ni data:)."""
    url = str(url or '').strip()[:500]
    return url if re.match(r'^https?://[^\s<>"\']+$', url, re.I) else ''


def _payment_settings():
    s = load_settings() or {}
    return {'payment_info': str(s.get('portal_payment_info') or '').strip()[:600],
            'payment_link': _clean_link(s.get('portal_payment_link'))}


# ── Côté propriétaire ───────────────────────────────────────────────────────────────────────
def api_quote_portal_create(qid):
    _ensure_portal_columns()
    row = _stored_quote(qid)
    if not row:
        return jsonify({'success': False, 'error': 'not_found'}), 404
    if (row['doc_type'] or 'quote') != 'quote':
        return jsonify({'success': False, 'error': 'not_a_quote'}), 400
    base = _external_base()
    if not base:                                   # pas d'adresse publique : aucun lien n'est créé (et le devis reste en brouillon)
        return jsonify({'success': False, 'error': 'remote_required', **_remote_info()}), 409
    token = row['public_token'] or secrets.token_urlsafe(18)
    conn = get_db()
    try:
        conn.execute("UPDATE quotes SET public_token=? WHERE id=? AND user_id=?", (token, qid, session['user_id']))
        # Un devis « brouillon » devient « envoyé » dès que son lien existe (comme l'envoi par e-mail)
        if (row['status'] or 'draft') == 'draft':
            conn.execute("UPDATE quotes SET status='sent', sent_at=? WHERE id=? AND user_id=?",
                         (datetime.date.today().isoformat(), qid, session['user_id']))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'success': True, 'token': token, 'url': f"{base}/quote/{token}", 'remote': True})


def api_quote_portal_revoke(qid):
    _ensure_portal_columns()
    conn = get_db()
    try:
        conn.execute("UPDATE quotes SET public_token='' WHERE id=? AND user_id=?", (qid, session['user_id']))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'success': True})


def api_quote_portal_links():
    """Devis du propriétaire avec leur lien public éventuel (pour l'écran « Atelier »)."""
    _ensure_portal_columns()
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, number, client, item_desc, total, status, public_token, decision_at, decision_by, created_at "
            "FROM quotes WHERE user_id=? AND COALESCE(doc_type,'quote')='quote' ORDER BY id DESC LIMIT 200",
            (session['user_id'],)).fetchall()
    finally:
        conn.close()
    base = _external_base()
    out = [{'id': r['id'], 'number': r['number'], 'client': r['client'], 'desc': r['item_desc'], 'total': r['total'],
            'status': r['status'] or 'draft', 'has_link': bool(r['public_token']),
            'url': f"{base}/quote/{r['public_token']}" if (base and r['public_token']) else '',
            'decision_at': r['decision_at'] or '', 'decision_by': r['decision_by'] or '',
            'created_at': str(r['created_at'] or '')[:10]} for r in rows]
    return jsonify({'quotes': out, **_remote_info(), **_payment_settings()})


def api_quote_portal_settings():
    if request.method == 'GET':
        return jsonify(_payment_settings())
    data = request.get_json(silent=True) or {}
    s = load_settings() or {}
    if 'payment_info' in data:
        s['portal_payment_info'] = str(data.get('payment_info') or '').strip()[:600]
    if 'payment_link' in data:
        raw = str(data.get('payment_link') or '').strip()
        link = _clean_link(raw)
        if raw and not link:
            return jsonify({'success': False, 'error': 'bad_link'}), 400
        s['portal_payment_link'] = link
    save_settings(s)
    return jsonify({'success': True, **_payment_settings()})


# ── Côté client (public) ────────────────────────────────────────────────────────────────────
def _quote_by_token(token):
    if not token or len(token) < 10 or len(token) > 80:
        return None
    _ensure_portal_columns()
    conn = get_db()
    try:
        return conn.execute("SELECT * FROM quotes WHERE public_token=? AND public_token!='' AND COALESCE(doc_type,'quote')='quote'",
                            (token,)).fetchone()
    finally:
        conn.close()


def _shop_name():
    try:
        s = load_settings() or {}
    except Exception:
        s = {}
    return str(s.get('quote_company') or s.get('print_cost_quote_company') or '').strip()[:120]


def api_quote_public_data(token):
    row = _quote_by_token(token)
    if not row:
        return jsonify({'error': 'Lien invalide'}), 404
    status = row['status'] or 'draft'
    pay = _payment_settings() if status == 'accepted' else {'payment_info': '', 'payment_link': ''}
    resp = jsonify({
        'shop': _shop_name(), 'number': row['number'], 'client': row['client'], 'desc': row['item_desc'],
        'qty': row['qty'], 'total': row['total'], 'due_date': row['due_date'] or '',
        'date': str(row['created_at'] or '')[:10], 'status': status,
        'decided': status in ('accepted', 'refused'), 'decision_at': row['decision_at'] or '',
        'can_decide': status in ('draft', 'sent', ''), **pay,
    })
    resp.headers['Cache-Control'] = 'no-store'
    return resp


def api_quote_public_pdf(token):
    row = _quote_by_token(token)
    if not row:
        return Response('Lien invalide', status=404, mimetype='text/plain; charset=utf-8')
    name = _safe_quote_pdf_filename(row['filename'] or row['number'])
    try:   # PDF non chiffré reconstruit depuis les données (les visionneuses intégrées refusent les PDF chiffrés)
        pj = _quote_payload_path(row)
        if pj and os.path.isfile(pj):
            with open(pj, 'r', encoding='utf-8') as f:
                payload = json.load(f)
            return send_file(io.BytesIO(_build_quote_pdf_with_repair(payload, encrypt=False)), mimetype='application/pdf',
                             as_attachment=request.args.get('dl') == '1', download_name=name)
    except Exception as e:
        app_logger.warning(f"[PORTAIL] PDF non chiffré indisponible, repli : {e}")
    path = _stored_quote_path(row)
    if not path:
        return Response('PDF introuvable', status=404, mimetype='text/plain; charset=utf-8')
    return send_file(path, mimetype='application/pdf', as_attachment=request.args.get('dl') == '1', download_name=name)


def _rate_ok(ip):
    now = time.time()
    with _DECISION_LOCK:
        hits = [t for t in _DECISION_LOG.get(ip, []) if now - t < 60]
        if len(hits) >= DECISION_MAX_PER_MIN:
            _DECISION_LOG[ip] = hits
            return False
        hits.append(now)
        _DECISION_LOG[ip] = hits
        if len(_DECISION_LOG) > 500:
            for k in [k for k, v in _DECISION_LOG.items() if not v or now - v[-1] > 60]:
                _DECISION_LOG.pop(k, None)
    return True


def api_quote_public_decision(token):
    row = _quote_by_token(token)
    if not row:
        return jsonify({'success': False, 'error': 'not_found'}), 404
    ip = (request.headers.get('CF-Connecting-IP') or request.remote_addr or '')[:64]
    if not _rate_ok(ip):
        return jsonify({'success': False, 'error': 'rate_limited'}), 429
    data = request.get_json(silent=True) or {}
    decision = str(data.get('decision') or '')
    if decision not in ('accept', 'refuse'):
        return jsonify({'success': False, 'error': 'bad_decision'}), 400
    if (row['status'] or 'draft') not in ('draft', 'sent', ''):
        return jsonify({'success': False, 'error': 'already_decided', 'status': row['status']}), 409
    who = re.sub(r'[\r\n\t<>]', ' ', str(data.get('name') or '')).strip()[:80]
    new_status = 'accepted' if decision == 'accept' else 'refused'
    conn = get_db()
    try:
        cur = conn.execute(
            "UPDATE quotes SET status=?, decision_at=?, decision_by=? WHERE id=? AND COALESCE(status,'draft') IN ('draft','sent','')",
            (new_status, datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), who, row['id']))
        conn.commit()
        changed = cur.rowcount
    finally:
        conn.close()
    if not changed:
        return jsonify({'success': False, 'error': 'already_decided'}), 409
    jobs = 0
    if new_status == 'accepted':
        try:
            jobs = _create_jobs_from_quote(row['user_id'], row)
        except Exception as e:
            app_logger.warning(f"[PORTAIL] Création de la tâche impossible : {e}")
    try:
        who_txt = f" ({who})" if who else ''
        verb = 'accepté' if new_status == 'accepted' else 'refusé'
        title = f"Devis {row['number']} {verb} par le client"
        msg = f"{row['client'] or 'Client'}{who_txt} a {verb} le devis {row['number']} depuis le lien de suivi."
        _insert_notification_once(row['user_id'], 'success' if new_status == 'accepted' else 'warning', title, msg,
                                  'quotes', f"quote_portal:{row['id']}:{new_status}")
        _push_notify_async('success' if new_status == 'accepted' else 'warning', title, msg)
    except Exception as e:
        app_logger.warning(f"[PORTAIL] Notification impossible : {e}")
    app_logger.info(f"[PORTAIL] Devis {row['number']} {new_status} par le client")
    pay = _payment_settings() if new_status == 'accepted' else {'payment_info': '', 'payment_link': ''}
    return jsonify({'success': True, 'status': new_status, 'jobs_created': jobs, **pay})


_PAGE = r"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>Devis</title><style>
*{box-sizing:border-box}body{margin:0;background:#0b0e13;color:#fff;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;padding:24px 18px 40px;display:flex;justify-content:center}
.card{width:100%;max-width:560px;background:#151a23;border:2px solid #232a38;border-radius:22px;padding:26px 24px;display:flex;flex-direction:column;gap:16px}
.shop{font-size:13px;color:#8b95a8;letter-spacing:.04em;text-transform:uppercase}h1{font-size:22px;margin:0;word-break:break-word}
.pill{display:inline-block;font-size:14px;font-weight:700;padding:5px 13px;border-radius:999px;background:#232a38;color:#cbd5e1}
.s-accepted .pill{background:rgba(56,193,114,.2);color:#38c172}.s-refused .pill{background:rgba(232,93,117,.2);color:#e85d75}.s-sent .pill{background:rgba(78,161,211,.2);color:#4ea1d3}
.row{display:flex;justify-content:space-between;gap:10px;font-size:15px;color:#cbd5e1}.row b{color:#fff;text-align:right}
.total{font-size:26px;font-weight:800;text-align:right}
a.btn,button{font:inherit;font-weight:700;border:0;border-radius:12px;padding:13px 16px;cursor:pointer;text-align:center;text-decoration:none;display:block}
.pdf{background:#232a38;color:#e2e8f0}.ok{background:#38c172;color:#06210f}.no{background:#232a38;color:#e85d75}
input{font:inherit;width:100%;padding:12px;border-radius:10px;border:1px solid #2b3446;background:#0f131b;color:#fff}
.two{display:grid;grid-template-columns:1fr 1fr;gap:10px}.pay{background:#0f131b;border-left:3px solid #38c172;border-radius:8px;padding:14px;font-size:15px;white-space:pre-wrap;color:#e2e8f0}
.thanks{background:rgba(56,193,114,.15);border:1px solid #38c172;color:#7ee2a8;border-radius:12px;padding:14px;font-weight:700;text-align:center}
.refused{background:rgba(232,93,117,.12);border:1px solid #e85d75;color:#f3a1b0;border-radius:12px;padding:14px;font-weight:700;text-align:center}
.msg{text-align:center;color:#8b95a8;padding:40px 10px}footer{text-align:center;color:#5b6577;font-size:12px}
</style></head><body><div class="card" id="c"><div class="msg">…</div></div><script>
const L={fr:{st:{draft:'En attente',sent:'En attente de votre réponse',accepted:'Accepté',refused:'Refusé'},pdf:'Voir le devis (PDF)',total:'Total',date:'Date',due:'Échéance',qty:'Quantité',name:'Votre nom (facultatif)',acc:'Accepter le devis',ref:'Refuser',thanks:'Merci ! Votre acceptation est enregistrée.',refd:'Vous avez refusé ce devis.',pay:'Paiement de l’acompte',link:'Payer en ligne',err:'Lien invalide ou expiré',foot:'Page de suivi propulsée par Stellio',conf:'Confirmer ?',fail:'Action impossible, réessayez.'},
en:{st:{draft:'Pending',sent:'Waiting for your answer',accepted:'Accepted',refused:'Declined'},pdf:'View the quote (PDF)',total:'Total',date:'Date',due:'Due date',qty:'Quantity',name:'Your name (optional)',acc:'Accept the quote',ref:'Decline',thanks:'Thank you! Your acceptance is recorded.',refd:'You declined this quote.',pay:'Deposit payment',link:'Pay online',err:'Invalid or expired link',foot:'Tracking page powered by Stellio',conf:'Confirm?',fail:'Could not complete, please retry.'},
de:{st:{draft:'Ausstehend',sent:'Wartet auf Ihre Antwort',accepted:'Angenommen',refused:'Abgelehnt'},pdf:'Angebot ansehen (PDF)',total:'Gesamt',date:'Datum',due:'Fällig am',qty:'Menge',name:'Ihr Name (optional)',acc:'Angebot annehmen',ref:'Ablehnen',thanks:'Danke! Ihre Annahme wurde gespeichert.',refd:'Sie haben dieses Angebot abgelehnt.',pay:'Anzahlung',link:'Online bezahlen',err:'Ungültiger oder abgelaufener Link',foot:'Statusseite von Stellio',conf:'Bestätigen?',fail:'Nicht möglich, bitte erneut versuchen.'},
es:{st:{draft:'Pendiente',sent:'Esperando su respuesta',accepted:'Aceptado',refused:'Rechazado'},pdf:'Ver el presupuesto (PDF)',total:'Total',date:'Fecha',due:'Vencimiento',qty:'Cantidad',name:'Su nombre (opcional)',acc:'Aceptar el presupuesto',ref:'Rechazar',thanks:'¡Gracias! Su aceptación está registrada.',refd:'Ha rechazado este presupuesto.',pay:'Pago del anticipo',link:'Pagar en línea',err:'Enlace no válido o caducado',foot:'Página de seguimiento de Stellio',conf:'¿Confirmar?',fail:'No se pudo completar, inténtelo de nuevo.'},
pt:{st:{draft:'Pendente',sent:'A aguardar a sua resposta',accepted:'Aceite',refused:'Recusado'},pdf:'Ver o orçamento (PDF)',total:'Total',date:'Data',due:'Vencimento',qty:'Quantidade',name:'O seu nome (opcional)',acc:'Aceitar o orçamento',ref:'Recusar',thanks:'Obrigado! A sua aceitação foi registada.',refd:'Recusou este orçamento.',pay:'Pagamento do sinal',link:'Pagar online',err:'Ligação inválida ou expirada',foot:'Página de acompanhamento do Stellio',conf:'Confirmar?',fail:'Não foi possível concluir, tente novamente.'},
it:{st:{draft:'In attesa',sent:'In attesa della sua risposta',accepted:'Accettato',refused:'Rifiutato'},pdf:'Vedi il preventivo (PDF)',total:'Totale',date:'Data',due:'Scadenza',qty:'Quantità',name:'Il suo nome (facoltativo)',acc:'Accetta il preventivo',ref:'Rifiuta',thanks:'Grazie! La sua accettazione è registrata.',refd:'Ha rifiutato questo preventivo.',pay:'Pagamento dell’acconto',link:'Paga online',err:'Link non valido o scaduto',foot:'Pagina di tracciamento di Stellio',conf:'Confermare?',fail:'Operazione non riuscita, riprovi.'},
zh:{st:{draft:'待处理',sent:'等待您的答复',accepted:'已接受',refused:'已拒绝'},pdf:'查看报价单 (PDF)',total:'合计',date:'日期',due:'到期日',qty:'数量',name:'您的姓名（选填）',acc:'接受报价',ref:'拒绝',thanks:'谢谢！已记录您的接受。',refd:'您已拒绝此报价。',pay:'定金支付',link:'在线支付',err:'链接无效或已过期',foot:'由 Stellio 提供的跟踪页面',conf:'确认？',fail:'操作失败，请重试。'},
ja:{st:{draft:'保留中',sent:'ご回答待ち',accepted:'承認済み',refused:'辞退'},pdf:'見積書を見る (PDF)',total:'合計',date:'日付',due:'期限',qty:'数量',name:'お名前（任意）',acc:'見積を承認する',ref:'辞退する',thanks:'ありがとうございます。承認を記録しました。',refd:'この見積を辞退しました。',pay:'手付金のお支払い',link:'オンラインで支払う',err:'無効または期限切れのリンクです',foot:'Stellio による進捗ページ',conf:'確定しますか？',fail:'実行できませんでした。もう一度お試しください。'}};
const T=L[(navigator.language||'fr').slice(0,2)]||L.en,$=id=>document.getElementById(id);
const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const base=location.pathname.replace(/\/$/,'');
function safeUrl(u){return /^https?:\/\//i.test(u||'')?u:''}
function pay(d){let h='';if(d.payment_info)h+='<div class="pay"><b>'+T.pay+'</b>\n'+esc(d.payment_info)+'</div>';const u=safeUrl(d.payment_link);if(u)h+='<a class="btn ok" target="_blank" rel="noopener noreferrer" href="'+esc(u)+'">'+T.link+'</a>';return h}
async function send(dec){const nm=$('nm')?$('nm').value:'';if(dec==='refuse'&&!confirm(T.conf))return;
try{const r=await fetch(base+'/decision',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({decision:dec,name:nm})});const j=await r.json();if(!r.ok&&r.status!==409)throw 0;}catch(e){alert(T.fail);return}load()}
async function load(){try{const r=await fetch(base+'/data',{cache:'no-store'});if(!r.ok)throw 0;const d=await r.json();document.title=d.number||'';
const st=d.status||'draft';$('c').className='card s-'+st;
$('c').innerHTML=(d.shop?'<div class="shop">'+esc(d.shop)+'</div>':'')+'<h1>'+esc(d.number)+(d.client?' · '+esc(d.client):'')+'</h1><div><span class="pill">'+esc(T.st[st]||st)+'</span></div>'+
(d.desc?'<div class="row"><span>'+esc(d.desc)+'</span></div>':'')+(d.qty?'<div class="row"><span>'+T.qty+'</span><b>'+esc(d.qty)+'</b></div>':'')+
(d.date?'<div class="row"><span>'+T.date+'</span><b>'+esc(d.date)+'</b></div>':'')+(d.due_date?'<div class="row"><span>'+T.due+'</span><b>'+esc(d.due_date)+'</b></div>':'')+
'<div class="total">'+esc(d.total)+'</div><a class="btn pdf" target="_blank" rel="noopener" href="'+base+'/pdf">'+T.pdf+'</a>'+
(d.can_decide?'<input id="nm" maxlength="80" placeholder="'+esc(T.name)+'"><div class="two"><button class="ok" onclick="send(\'accept\')">'+T.acc+'</button><button class="no" onclick="send(\'refuse\')">'+T.ref+'</button></div>':'')+
(st==='accepted'?'<div class="thanks">✓ '+T.thanks+'</div>'+pay(d):'')+(st==='refused'?'<div class="refused">'+T.refd+'</div>':'')+'<footer>'+T.foot+'</footer>'}
catch(e){$('c').innerHTML='<div class="msg">'+T.err+'</div>'}}
load();
</script></body></html>"""


def quote_public_page(token):
    if not _quote_by_token(token):
        return Response("Lien invalide ou révoqué", status=404, mimetype='text/plain; charset=utf-8')
    resp = Response(_PAGE, mimetype='text/html')
    resp.headers['Cache-Control'] = 'no-store'
    resp.headers['X-Robots-Tag'] = 'noindex, nofollow'
    resp.headers['Referrer-Policy'] = 'no-referrer'
    return resp


_ROUTES = (
    ('/api/quotes/<int:qid>/portal', ['POST'], 'api_quote_portal_create', ('login_required', )),
    ('/api/quotes/<int:qid>/portal', ['DELETE'], 'api_quote_portal_revoke', ('login_required', )),
    ('/api/quote-portal/links', ['GET'], 'api_quote_portal_links', ('login_required', )),
    ('/api/quote-portal/settings', ['GET', 'POST'], 'api_quote_portal_settings', ('login_required', )),
    ('/quote/<token>/data', ['GET'], 'api_quote_public_data', ()),
    ('/quote/<token>/pdf', ['GET'], 'api_quote_public_pdf', ()),
    ('/quote/<token>/decision', ['POST'], 'api_quote_public_decision', ()),
    ('/quote/<token>', ['GET'], 'quote_public_page', ()),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"quote_portal.init : services manquants : {missing}")
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
