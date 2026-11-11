"""Stellio — lien d'état partageable (lecture seule, sans compte)

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `share_link.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import os
import secrets
import time

_REQUIRED = (
    'Response',
    '_ensure_v086_tables',
    '_printer_status_cached',
    'app',
    'get_db',
    'get_local_ip',
    'get_remote_state',
    'jsonify',
    'login_required',
    'parse_printer_config',
    'request',
    'session',
)
_OVERRIDABLE = ('os', 'secrets', 'time', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
Response = None
_ensure_v086_tables = None
_printer_status_cached = None
app = None
get_db = None
get_local_ip = None
get_remote_state = None
jsonify = None
login_required = None
parse_printer_config = None
request = None
session = None


# ── Lien d'état partageable (lecture seule, sans compte) ────────────────────────────────────
STATUS_MAX_LINKS = 10

def api_list_status_links():
    _ensure_v086_tables()
    conn = get_db()
    try:
        rows = conn.execute("SELECT id, token, label, show_files, created_at, last_view_at FROM share_links WHERE user_id=? ORDER BY id DESC",
                            (session['user_id'],)).fetchall()
    finally:
        conn.close()
    remote_state = get_remote_state()
    if remote_state.get('status') == 'ready' and remote_state.get('url'):
        base_url, remote = remote_state['url'].rstrip('/'), True
    else:
        base_url, remote = f"http://{get_local_ip()}:{_MAIN.get('SERVER_PORT') or int(os.environ.get('STELLIO_PORT', '5000'))}", False
    return jsonify({"links": [{**dict(r), "url": f"{base_url}/status/{r['token']}"} for r in rows], "remote": remote})

def api_create_status_link():
    _ensure_v086_tables()
    data = request.json or {}
    label = str(data.get('label') or '').strip()[:60]
    show_files = 1 if data.get('show_files') else 0
    conn = get_db()
    try:
        n = conn.execute("SELECT COUNT(*) FROM share_links WHERE user_id=?", (session['user_id'],)).fetchone()[0]
        if n >= STATUS_MAX_LINKS:
            return jsonify({"error": f"Maximum {STATUS_MAX_LINKS} liens"}), 400
        token = secrets.token_urlsafe(24)
        conn.execute("INSERT INTO share_links (user_id, token, label, show_files) VALUES (?,?,?,?)",
                     (session['user_id'], token, label, show_files))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"token": token}), 200

def api_delete_status_link(lid):
    _ensure_v086_tables()
    conn = get_db()
    try:
        conn.execute("DELETE FROM share_links WHERE id=? AND user_id=?", (lid, session['user_id']))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"message": "Lien révoqué"})

def _status_link_by_token(token):
    _ensure_v086_tables()
    if not token or len(token) > 80:
        return None
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM share_links WHERE token=?", (token,)).fetchone()
        if row:
            conn.execute("UPDATE share_links SET last_view_at=CURRENT_TIMESTAMP WHERE id=?", (row['id'],))
            conn.commit()
        return row
    finally:
        conn.close()

def api_status_share_data(token):
    link = _status_link_by_token(token)
    if not link:
        return jsonify({"error": "Lien invalide"}), 404
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM printers WHERE user_id=? ORDER BY id", (link['user_id'],)).fetchall()
    finally:
        conn.close()
    out = []
    for row in rows:
        p = parse_printer_config(row)
        st = _printer_status_cached(p)
        active = st.get('status') in ('printing', 'paused')
        t = st.get('time') or {}
        temps = st.get('temps') or {}
        item = {
            "name": p.get('name') or '', "status": st.get('status') or 'offline',
            "progress": round(float(st.get('progress') or 0), 1) if active else 0,
            "remaining": t.get('remaining') if active else None,
            "extruder": (temps.get('extruder') or {}).get('current'),
            "bed": (temps.get('bed') or {}).get('current'),
        }
        if link['show_files'] and active and st.get('file'):
            item["file"] = os.path.basename(str(st.get('file')).replace('\\', '/'))
        out.append(item)
    resp = jsonify({"label": link['label'] or '', "printers": out, "now": int(time.time())})
    resp.headers['Cache-Control'] = 'no-store'
    return resp

_STATUS_SHARE_PAGE = r"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>Stellio</title><style>
*{box-sizing:border-box}body{margin:0;background:#0b0e13;color:#fff;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;padding:18px 20px 30px}
header{display:flex;align-items:center;gap:12px;margin-bottom:18px}h1{font-size:20px;margin:0;flex:1}.clock{font-size:28px;font-weight:700;font-variant-numeric:tabular-nums}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
.tile{background:#151a23;border:2px solid #232a38;border-radius:20px;padding:16px 18px;display:flex;flex-direction:column;gap:10px}
.printing{border-color:#4ea1d3}.paused{border-color:#f5a623}.error{border-color:#e85d75}.offline{opacity:.5}
.head{display:flex;justify-content:space-between;gap:10px;align-items:center}.name{font-size:20px;font-weight:700;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pill{font-size:13px;font-weight:600;padding:4px 11px;border-radius:999px;background:#232a38;color:#cbd5e1;white-space:nowrap}
.printing .pill{background:rgba(78,161,211,.2);color:#4ea1d3}.paused .pill{background:rgba(245,166,35,.2);color:#f5a623}.idle .pill{background:rgba(56,193,114,.18);color:#38c172}.error .pill{background:rgba(232,93,117,.2);color:#e85d75}
.pct{font-size:60px;font-weight:800;line-height:1}.pct small{font-size:24px;color:#8b95a8}.rem{font-size:20px;color:#cbd5e1}
.bar{height:12px;background:#232a38;border-radius:8px;overflow:hidden}.bar div{height:100%;background:#4ea1d3;border-radius:8px;transition:width .6s}
.paused .bar div{background:#f5a623}.file{font-size:14px;color:#8b95a8;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.temps{display:flex;gap:18px;font-size:16px;color:#cbd5e1}
.msg{text-align:center;color:#8b95a8;padding:50px 10px}footer{margin-top:22px;text-align:center;color:#5b6577;font-size:12px}
</style></head><body><header><h1 id="t">Stellio</h1><div class="clock" id="c"></div></header><div class="grid" id="g"><div class="msg">…</div></div>
<footer id="f"></footer><script>
const L={fr:{printing:'Impression',paused:'En pause',idle:'Disponible',complete:'Terminée',error:'Erreur',offline:'Hors ligne',none:'Aucune imprimante',err:'Lien invalide ou révoqué',foot:'Affichage en lecture seule'},
en:{printing:'Printing',paused:'Paused',idle:'Available',complete:'Done',error:'Error',offline:'Offline',none:'No printer',err:'Invalid or revoked link',foot:'Read-only view'},
de:{printing:'Druckt',paused:'Pausiert',idle:'Verfügbar',complete:'Fertig',error:'Fehler',offline:'Offline',none:'Kein Drucker',err:'Ungültiger oder widerrufener Link',foot:'Nur-Lese-Ansicht'},
es:{printing:'Imprimiendo',paused:'En pausa',idle:'Disponible',complete:'Terminada',error:'Error',offline:'Sin conexión',none:'Sin impresoras',err:'Enlace no válido o revocado',foot:'Vista de solo lectura'},
pt:{printing:'A imprimir',paused:'Em pausa',idle:'Disponível',complete:'Concluída',error:'Erro',offline:'Offline',none:'Sem impressoras',err:'Ligação inválida ou revogada',foot:'Vista só de leitura'},
it:{printing:'In stampa',paused:'In pausa',idle:'Disponibile',complete:'Completata',error:'Errore',offline:'Offline',none:'Nessuna stampante',err:'Link non valido o revocato',foot:'Vista in sola lettura'},
zh:{printing:'打印中',paused:'已暂停',idle:'空闲',complete:'已完成',error:'错误',offline:'离线',none:'没有打印机',err:'链接无效或已撤销',foot:'只读视图'},
ja:{printing:'印刷中',paused:'一時停止',idle:'待機中',complete:'完了',error:'エラー',offline:'オフライン',none:'プリンターなし',err:'リンクが無効か取り消されました',foot:'閲覧専用'}};
const lg=(navigator.language||'fr').slice(0,2),T=L[lg]||L.en,$=id=>document.getElementById(id);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function dur(s){if(!s||s<=0)return'';const h=Math.floor(s/3600),m=Math.floor(s%3600/60);return h?h+'h '+String(m).padStart(2,'0')+'m':m+'m'}
async function load(){try{const r=await fetch(location.pathname.replace(/\/$/,'')+'/data',{cache:'no-store'});if(!r.ok)throw 0;const d=await r.json();
$('t').textContent=d.label||'Stellio';$('f').textContent=T.foot+' · Stellio';
$('g').innerHTML=d.printers.length?d.printers.map(p=>{const st=['printing','paused','idle','complete','error'].includes(p.status)?p.status:'offline';const act=st==='printing'||st==='paused';
return '<div class="tile '+st+'"><div class="head"><span class="name">'+esc(p.name)+'</span><span class="pill">'+T[st]+'</span></div>'+
(act?'<div class="pct">'+Math.round(p.progress)+'<small>%</small></div>'+(p.remaining>0?'<div class="rem">⏱ '+dur(p.remaining)+'</div>':'')+'<div class="bar"><div style="width:'+Math.round(p.progress)+'%"></div></div>'+(p.file?'<div class="file">'+esc(p.file)+'</div>':''):'')+
(p.extruder!=null?'<div class="temps"><span>🔥 '+Math.round(p.extruder)+'°C</span><span>🛏️ '+Math.round(p.bed||0)+'°C</span></div>':'')+'</div>'}).join(''):'<div class="msg">'+T.none+'</div>'}
catch(e){$('g').innerHTML='<div class="msg">'+T.err+'</div>'}}
setInterval(()=>{$('c').textContent=new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})},10000);$('c').textContent=new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
load();setInterval(load,6000);
</script></body></html>"""

def status_share_page(token):
    if not _status_link_by_token(token):
        return Response("Lien invalide ou révoqué", status=404, mimetype='text/plain; charset=utf-8')
    resp = Response(_STATUS_SHARE_PAGE, mimetype='text/html')
    resp.headers['Cache-Control'] = 'no-store'
    resp.headers['X-Robots-Tag'] = 'noindex, nofollow'
    resp.headers['Referrer-Policy'] = 'no-referrer'
    return resp


_ROUTES = (
    ('/api/status-links', ['GET'], 'api_list_status_links', ('login_required', )),
    ('/api/status-links', ['POST'], 'api_create_status_link', ('login_required', )),
    ('/api/status-links/<int:lid>', ['DELETE'], 'api_delete_status_link', ('login_required', )),
    ('/status/<token>/data', ['GET'], 'api_status_share_data', ()),
    ('/status/<token>', ['GET'], 'status_share_page', ()),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"share_link.init : services manquants : {missing}")
    for n in _REQUIRED + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
