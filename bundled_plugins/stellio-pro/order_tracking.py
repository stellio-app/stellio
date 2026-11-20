"""Stellio — page de suivi client (un lien public par commande)

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `order_tracking.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import os
import secrets
import time

_REQUIRED = (
    'Response',
    '_JOB_STATUSES',
    '_printer_status_cached',
    'app',
    'get_db',
    'get_local_ip',
    'get_remote_state',
    'jsonify',
    'load_settings',
    'login_required',
    'parse_printer_config',
    'request',
    'session',
)
_OVERRIDABLE = ('secrets', 'time', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
Response = None
_JOB_STATUSES = None
_printer_status_cached = None
app = None
get_db = None
get_local_ip = None
get_remote_state = None
jsonify = None
load_settings = None
login_required = None
parse_printer_config = None
request = None
session = None


# ── Page de suivi client : un lien public par commande ──────────────────────────────────────
def _share_base_url():
    remote_state = get_remote_state()
    if remote_state.get('status') == 'ready' and remote_state.get('url'):
        return remote_state['url'].rstrip('/'), True
    return f"http://{get_local_ip()}:{_MAIN.get('SERVER_PORT') or int(os.environ.get('STELLIO_PORT', '5000'))}", False

def api_orders_track_create(jid):
    """Crée (ou renvoie) le lien de suivi public d'une commande ; enregistre au passage le message au client."""
    data = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        row = conn.execute("SELECT track_token FROM print_jobs WHERE id=? AND user_id=?", (jid, session['user_id'])).fetchone()
        if not row:
            return jsonify({'success': False, 'error': 'not_found'}), 404
        token = row['track_token'] or secrets.token_urlsafe(18)
        if 'client_note' in data:
            conn.execute("UPDATE print_jobs SET track_token=?, client_note=? WHERE id=?",
                         (token, str(data.get('client_note') or '').strip()[:300], jid))
        else:
            conn.execute("UPDATE print_jobs SET track_token=? WHERE id=?", (token, jid))
        conn.commit()
    finally:
        conn.close()
    base, remote = _share_base_url()
    rs = get_remote_state()
    return jsonify({'success': True, 'token': token, 'url': f"{base}/order/{token}", 'remote': remote,
                    'remote_status': rs.get('status'), 'remote_mode': rs.get('mode'), 'remote_error': rs.get('error')})

def api_orders_track_revoke(jid):
    conn = get_db()
    try:
        conn.execute("UPDATE print_jobs SET track_token='' WHERE id=? AND user_id=?", (jid, session['user_id']))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'success': True})

def _order_by_track_token(token):
    # Un jeton vide ne doit jamais correspondre : les commandes sans lien ont track_token = ''
    if not token or len(token) < 10 or len(token) > 80:
        return None
    conn = get_db()
    try:
        return conn.execute("SELECT * FROM print_jobs WHERE track_token=? AND track_token!=''", (token,)).fetchone()
    finally:
        conn.close()

def api_order_track_data(token):
    """Données publiques minimales : jamais de prix, de marge, de notes internes ni de nom d'imprimante."""
    job = _order_by_track_token(token)
    if not job:
        return jsonify({"error": "Lien invalide"}), 404
    try:
        settings = load_settings() or {}
    except Exception:
        settings = {}
    shop = str(settings.get('quote_company') or settings.get('print_cost_quote_company') or '').strip()[:120]
    qty = max(1, int(job['quantity'] or 1))
    done = max(0, min(int(job['qty_done'] or 0), qty))
    status = job['status'] if job['status'] in _JOB_STATUSES else 'queued'
    live = None
    if status == 'printing' and job['printer_id']:
        try:
            conn = get_db()
            try:
                prow = conn.execute("SELECT * FROM printers WHERE id=? AND user_id=?", (job['printer_id'], job['user_id'])).fetchone()
            finally:
                conn.close()
            if prow:
                st = _printer_status_cached(parse_printer_config(prow))
                if st.get('status') in ('printing', 'paused'):
                    live = round(float(st.get('progress') or 0), 1)
        except Exception:
            live = None
    resp = jsonify({
        "shop": shop, "part": job['part'], "quantity": qty, "qty_done": done, "status": status,
        "due_date": job['due_date'] or '', "created_at": (job['created_at'] or '')[:10], "done_at": job['done_at'] or '',
        "note": job['client_note'] or '', "live_progress": live, "now": int(time.time()),
    })
    resp.headers['Cache-Control'] = 'no-store'
    return resp

_ORDER_TRACK_PAGE = r"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>Suivi de commande</title><style>
*{box-sizing:border-box}body{margin:0;background:#0b0e13;color:#fff;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;padding:24px 18px 40px;display:flex;justify-content:center}
.card{width:100%;max-width:520px;background:#151a23;border:2px solid #232a38;border-radius:22px;padding:26px 24px;display:flex;flex-direction:column;gap:18px}
.shop{font-size:13px;color:#8b95a8;letter-spacing:.04em;text-transform:uppercase}h1{font-size:24px;margin:0;word-break:break-word}
.pill{display:inline-block;font-size:15px;font-weight:700;padding:6px 14px;border-radius:999px;background:#232a38;color:#cbd5e1}
.s-printing .pill{background:rgba(78,161,211,.2);color:#4ea1d3}.s-done .pill{background:rgba(56,193,114,.2);color:#38c172}.s-cancelled .pill{background:rgba(232,93,117,.2);color:#e85d75}
.steps{display:flex;align-items:flex-start;gap:0}.step{flex:1;text-align:center;font-size:12px;color:#5b6577;position:relative}
.dot{width:22px;height:22px;border-radius:50%;background:#232a38;margin:0 auto 6px;border:2px solid #232a38;position:relative;z-index:1}
.step:not(:last-child):after{content:"";position:absolute;top:10px;left:50%;width:100%;height:3px;background:#232a38}
.step.on{color:#e2e8f0}.step.on .dot{background:#4ea1d3;border-color:#4ea1d3}.step.on:not(:last-child):after{background:#4ea1d3}
.s-done .step.on .dot{background:#38c172;border-color:#38c172}.s-done .step.on:not(:last-child):after{background:#38c172}
.bar{height:12px;background:#232a38;border-radius:8px;overflow:hidden}.bar div{height:100%;background:#4ea1d3;border-radius:8px;transition:width .6s}.s-done .bar div{background:#38c172}
.row{display:flex;justify-content:space-between;gap:10px;font-size:15px;color:#cbd5e1}.row b{color:#fff}
.note{background:#0f131b;border-left:3px solid #4ea1d3;border-radius:8px;padding:12px 14px;font-size:15px;color:#e2e8f0;white-space:pre-wrap}
.ready{background:rgba(56,193,114,.15);border:1px solid #38c172;color:#7ee2a8;border-radius:12px;padding:14px;font-size:17px;font-weight:700;text-align:center}
.msg{text-align:center;color:#8b95a8;padding:40px 10px}footer{text-align:center;color:#5b6577;font-size:12px}
</style></head><body><div class="card" id="c"><div class="msg">…</div></div><script>
const L={fr:{st:{queued:'En file d’attente',printing:'En cours d’impression',done:'Terminée',cancelled:'Annulée'},s1:'Reçue',s2:'Impression',s3:'Prête',ready:'Votre commande est prête à être retirée',qty:'Quantité',done:'Pièces terminées',due:'Livraison prévue',since:'Commande du',doneat:'Terminée le',err:'Lien invalide ou révoqué',foot:'Suivi en lecture seule'},
en:{st:{queued:'Queued',printing:'Printing',done:'Done',cancelled:'Cancelled'},s1:'Received',s2:'Printing',s3:'Ready',ready:'Your order is ready for pickup',qty:'Quantity',done:'Parts finished',due:'Expected on',since:'Ordered on',doneat:'Finished on',err:'Invalid or revoked link',foot:'Read-only tracking'},
de:{st:{queued:'In der Warteschlange',printing:'Wird gedruckt',done:'Fertig',cancelled:'Storniert'},s1:'Erhalten',s2:'Druck',s3:'Bereit',ready:'Ihre Bestellung ist abholbereit',qty:'Menge',done:'Fertige Teile',due:'Voraussichtlich am',since:'Bestellt am',doneat:'Fertig am',err:'Ungültiger oder widerrufener Link',foot:'Nur-Lese-Verfolgung'},
es:{st:{queued:'En cola',printing:'Imprimiendo',done:'Terminado',cancelled:'Cancelado'},s1:'Recibido',s2:'Impresión',s3:'Listo',ready:'Su pedido está listo para recoger',qty:'Cantidad',done:'Piezas terminadas',due:'Entrega prevista',since:'Pedido el',doneat:'Terminado el',err:'Enlace no válido o revocado',foot:'Seguimiento de solo lectura'},
pt:{st:{queued:'Em fila',printing:'A imprimir',done:'Concluído',cancelled:'Cancelado'},s1:'Recebido',s2:'Impressão',s3:'Pronto',ready:'A sua encomenda está pronta para levantamento',qty:'Quantidade',done:'Peças concluídas',due:'Entrega prevista',since:'Encomendado em',doneat:'Concluído em',err:'Ligação inválida ou revogada',foot:'Acompanhamento só de leitura'},
it:{st:{queued:'In coda',printing:'In stampa',done:'Completato',cancelled:'Annullato'},s1:'Ricevuto',s2:'Stampa',s3:'Pronto',ready:'Il suo ordine è pronto per il ritiro',qty:'Quantità',done:'Pezzi completati',due:'Consegna prevista',since:'Ordinato il',doneat:'Completato il',err:'Link non valido o revocato',foot:'Monitoraggio in sola lettura'},
zh:{st:{queued:'排队中',printing:'打印中',done:'已完成',cancelled:'已取消'},s1:'已接收',s2:'打印',s3:'可取',ready:'您的订单已可取货',qty:'数量',done:'已完成件数',due:'预计交付',since:'下单日期',doneat:'完成日期',err:'链接无效或已撤销',foot:'只读跟踪'},
ja:{st:{queued:'順番待ち',printing:'印刷中',done:'完了',cancelled:'キャンセル'},s1:'受付',s2:'印刷',s3:'受取可',ready:'ご注文の品はお受け取りいただけます',qty:'数量',done:'完成数',due:'お渡し予定',since:'注文日',doneat:'完了日',err:'リンクが無効か取り消されました',foot:'閲覧専用の追跡'}};
const T=L[(navigator.language||'fr').slice(0,2)]||L.en,$=id=>document.getElementById(id);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fd=s=>{if(!s)return'';const d=new Date(s+'T00:00:00');return isNaN(d)?esc(s):d.toLocaleDateString()};
async function load(){try{const r=await fetch(location.pathname.replace(/\/$/,'')+'/data',{cache:'no-store'});if(!r.ok)throw 0;const d=await r.json();
document.title=d.part;const st=d.status,step=st==='done'?3:st==='printing'?2:1;
let pct=Math.round(100*d.qty_done/d.quantity);if(st==='printing'&&d.live_progress!=null&&d.qty_done<d.quantity)pct=Math.round(100*(d.qty_done+d.live_progress/100)/d.quantity);if(st==='done')pct=100;
$('c').className='card s-'+st;
$('c').innerHTML=(d.shop?'<div class="shop">'+esc(d.shop)+'</div>':'')+'<h1>'+esc(d.part)+'</h1><div><span class="pill">'+T.st[st]+'</span></div>'+
(st==='done'?'<div class="ready">✓ '+T.ready+'</div>':'')+
(st!=='cancelled'?'<div class="steps"><div class="step on"><div class="dot"></div>'+T.s1+'</div><div class="step '+(step>=2?'on':'')+'"><div class="dot"></div>'+T.s2+'</div><div class="step '+(step>=3?'on':'')+'"><div class="dot"></div>'+T.s3+'</div></div><div class="bar"><div style="width:'+pct+'%"></div></div>':'')+
'<div class="row"><span>'+T.done+'</span><b>'+d.qty_done+' / '+d.quantity+'</b></div>'+
(d.due_date&&st!=='done'&&st!=='cancelled'?'<div class="row"><span>'+T.due+'</span><b>'+fd(d.due_date)+'</b></div>':'')+
(d.created_at?'<div class="row"><span>'+T.since+'</span><b>'+fd(d.created_at)+'</b></div>':'')+
(st==='done'&&d.done_at?'<div class="row"><span>'+T.doneat+'</span><b>'+fd(d.done_at)+'</b></div>':'')+
(d.note?'<div class="note">'+esc(d.note)+'</div>':'')+'<footer>'+T.foot+'</footer>'}
catch(e){$('c').innerHTML='<div class="msg">'+T.err+'</div>'}}
load();setInterval(load,15000);
</script></body></html>"""

def order_track_page(token):
    if not _order_by_track_token(token):
        return Response("Lien invalide ou révoqué", status=404, mimetype='text/plain; charset=utf-8')
    resp = Response(_ORDER_TRACK_PAGE, mimetype='text/html')
    resp.headers['Cache-Control'] = 'no-store'
    resp.headers['X-Robots-Tag'] = 'noindex, nofollow'
    resp.headers['Referrer-Policy'] = 'no-referrer'
    return resp


_ROUTES = (
    ('/api/orders/<int:jid>/track', ['POST'], 'api_orders_track_create', ('login_required', )),
    ('/api/orders/<int:jid>/track', ['DELETE'], 'api_orders_track_revoke', ('login_required', )),
    ('/order/<token>/data', ['GET'], 'api_order_track_data', ()),
    ('/order/<token>', ['GET'], 'order_track_page', ()),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"order_tracking.init : services manquants : {missing}")
    for n in _REQUIRED + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
