#!/usr/bin/env python3
"""Génère le site de documentation de Stellio (HTML statique, 8 langues, façon docs.frigate.video).

    python tools/build_docs.py --out docs-out [--base /docs/]

Mêmes sources que le wiki GitHub (docs/wiki/src/<langue>.md, captures, changelog.json) :
un seul texte à maintenir, deux sorties. Dépendance : `pip install markdown`.

Fonctions : menu latéral par catégories (repliables), sommaire « Sur cette page », recherche instantanée
(Ctrl+K), thème clair/sombre/automatique, sélecteur de langue, page précédente/suivante, « Modifier cette page »,
bouton « copier » sur les blocs de code, tiroir mobile.
"""
import argparse
import html
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_wiki as W  # noqa: E402

try:
    import markdown
except ImportError:
    sys.exit("Module manquant : pip install markdown")

ROOT = W.ROOT
REPO = W.REPO
LANGS = W.LANGS
GROUPS = [
    ('intro', ['Home', 'Installation', 'Getting-Started']),
    ('guides', ['How-To']),
    ('usage', ['Library', 'Printers', 'Filament', 'Downloads', 'AI', 'Costs-and-Management']),
    ('config', ['Remote-Access', 'Server-Edition', 'Settings-and-Data']),
    ('help', ['Troubleshooting']),
    ('dev', ['Contributing', 'Changelog']),
]
UI = {
    'fr': dict(intro='Stellio', guides='Guides', usage='Utilisation', config='Configuration', help='Dépannage', dev='Développement',
               search='Rechercher', nosearch='Aucun résultat', toc='Sur cette page', edit='Modifier cette page', prev='Précédent', next='Suivant',
               site='Site web', demo='Démo', docs='Documentation', theme='Thème', menu='Menu', copy='Copier', copied='Copié',
               community='Communauté', download='Télécharger', rights='Stellio — logiciel libre (AGPL v3).'),
    'en': dict(intro='Stellio', guides='Guides', usage='Usage', config='Configuration', help='Troubleshooting', dev='Development',
               search='Search', nosearch='No results', toc='On this page', edit='Edit this page', prev='Previous', next='Next',
               site='Website', demo='Demo', docs='Docs', theme='Theme', menu='Menu', copy='Copy', copied='Copied',
               community='Community', download='Download', rights='Stellio — free software (AGPL v3).'),
    'de': dict(intro='Stellio', guides='Anleitungen', usage='Nutzung', config='Konfiguration', help='Fehlerbehebung', dev='Entwicklung',
               search='Suchen', nosearch='Keine Ergebnisse', toc='Auf dieser Seite', edit='Diese Seite bearbeiten', prev='Zurück', next='Weiter',
               site='Website', demo='Demo', docs='Doku', theme='Design', menu='Menü', copy='Kopieren', copied='Kopiert',
               community='Community', download='Herunterladen', rights='Stellio — freie Software (AGPL v3).'),
    'es': dict(intro='Stellio', guides='Guías', usage='Uso', config='Configuración', help='Solución de problemas', dev='Desarrollo',
               search='Buscar', nosearch='Sin resultados', toc='En esta página', edit='Editar esta página', prev='Anterior', next='Siguiente',
               site='Sitio web', demo='Demo', docs='Documentación', theme='Tema', menu='Menú', copy='Copiar', copied='Copiado',
               community='Comunidad', download='Descargar', rights='Stellio — software libre (AGPL v3).'),
    'pt': dict(intro='Stellio', guides='Guias', usage='Utilização', config='Configuração', help='Resolução de problemas', dev='Desenvolvimento',
               search='Pesquisar', nosearch='Sem resultados', toc='Nesta página', edit='Editar esta página', prev='Anterior', next='Seguinte',
               site='Site', demo='Demo', docs='Documentação', theme='Tema', menu='Menu', copy='Copiar', copied='Copiado',
               community='Comunidade', download='Transferir', rights='Stellio — software livre (AGPL v3).'),
    'it': dict(intro='Stellio', guides='Guide', usage='Utilizzo', config='Configurazione', help='Risoluzione problemi', dev='Sviluppo',
               search='Cerca', nosearch='Nessun risultato', toc='In questa pagina', edit='Modifica questa pagina', prev='Precedente', next='Successivo',
               site='Sito web', demo='Demo', docs='Documentazione', theme='Tema', menu='Menu', copy='Copia', copied='Copiato',
               community='Community', download='Scarica', rights='Stellio — software libero (AGPL v3).'),
    'zh': dict(intro='Stellio', guides='指南', usage='使用', config='配置', help='故障排除', dev='开发',
               search='搜索', nosearch='没有结果', toc='本页内容', edit='编辑此页', prev='上一页', next='下一页',
               site='官网', demo='演示', docs='文档', theme='主题', menu='菜单', copy='复制', copied='已复制',
               community='社区', download='下载', rights='Stellio — 自由软件（AGPL v3）。'),
    'ja': dict(intro='Stellio', guides='ガイド', usage='使い方', config='設定', help='トラブルシューティング', dev='開発',
               search='検索', nosearch='結果なし', toc='このページ内', edit='このページを編集', prev='前へ', next='次へ',
               site='公式サイト', demo='デモ', docs='ドキュメント', theme='テーマ', menu='メニュー', copy='コピー', copied='コピー済み',
               community='コミュニティ', download='ダウンロード', rights='Stellio — フリーソフトウェア（AGPL v3）。'),
}
ICONS = {'Home': '🏠', 'Installation': '📦', 'Getting-Started': '🚀', 'How-To': '🧭', 'Library': '🗂️', 'Printers': '🖨️',
         'Filament': '🧵', 'Downloads': '⬇️', 'AI': '🤖', 'Costs-and-Management': '💶', 'Remote-Access': '📱',
         'Server-Edition': '🖥️', 'Settings-and-Data': '⚙️', 'Troubleshooting': '🛟', 'Contributing': '🤝', 'Changelog': '📰'}


def version():
    try:
        m = re.search(r'CURRENT_VERSION\s*=\s*"([^"]+)"', open(os.path.join(ROOT, 'main.py'), encoding='utf-8').read())
        return m.group(1) if m else ''
    except OSError:
        return ''


def prep_md(text):
    """Comme GitHub : une liste peut suivre directement un paragraphe (python-markdown exige une ligne vide)."""
    out, prev, in_code = [], '', False
    for line in text.split('\n'):
        if line.lstrip().startswith('```'):
            in_code = not in_code
        elif not in_code and re.match(r'^\s*([-*+]|\d+\.)\s', line) and prev.strip() and not re.match(r'^\s*([-*+]|\d+\.)\s', prev) \
                and not prev.lstrip().startswith(('|', '>', '#')) and not prev.startswith((' ', '\t')):
            out.append('')
        out.append(line)
        prev = line
    return '\n'.join(out)


def render(lang, slug, md_text, base, used):
    def img(m):
        name = m.group(1)
        found = W.find_image(lang, name)
        if not found:
            return ''
        ver, lg = found
        used.add((ver, lg, name))
        cap = html.escape(W.CAPTIONS[lang].get(name, name), quote=True)
        url = f'{base}assets/img/{ver}/{lg}/{name}.png'
        return f'\n\n<figure class="shot"><a href="{url}" target="_blank" rel="noopener"><img src="{url}" alt="{cap}" loading="lazy"></a><figcaption>{cap}</figcaption></figure>\n\n'
    md_text = re.sub(r'\n*\{\{img:([\w-]+)\}\}\n*', img, md_text)
    md_text = re.sub(r'\]\((%s)-([A-Za-z-]+)\)' % lang, lambda m: f']({base}{lang}/{m.group(2)}/)', md_text)
    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'toc', 'attr_list', 'sane_lists', 'md_in_html'],
                           extension_configs={'toc': {'permalink': '#', 'toc_depth': '2-3', 'permalink_title': ''}})
    body = md.convert(prep_md(md_text))
    toc = [(t['level'], t['id'], re.sub(r'<[^>]+>', '', t['name'])) for t in _flat(md.toc_tokens)]
    body = re.sub(r'<h1[^>]*>.*?</h1>', '', body, count=1, flags=re.S)           # le titre est rendu par le gabarit
    body = body.replace('<table>', '<div class="tbl"><table>').replace('</table>', '</table></div>')
    body = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', body)
    return body, toc


def _flat(tokens):
    for t in tokens:
        yield t
        yield from _flat(t.get('children', []))


def search_entries(lang, title, url, body):
    parts = re.split(r'(?=<h2 )', body)
    out = []
    for p in parts:
        m = re.match(r'<h2[^>]*id="([^"]+)"[^>]*>(.*?)</h2>', p, re.S)
        head = re.sub(r'<[^>]+>', '', m.group(2)).replace('#', '').strip() if m else ''
        txt = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', p))).replace('#', '').strip()
        if len(txt) < 3:
            continue
        out.append({'t': title, 'h': head, 'u': url + (f'#{m.group(1)}' if m else ''), 'x': txt[:1400]})
    return out


CSS = r"""
:root{--bg:#fff;--bg2:#f6f8fb;--fg:#1c1e21;--mut:#5b6472;--line:#e3e8ef;--acc:#2563eb;--acc2:#1d4ed8;--accbg:#eaf1ff;--code:#f3f5f9;--nav:#fff;--shadow:0 1px 2px rgba(15,23,42,.08)}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#15171c;--bg2:#1b1e25;--fg:#e6e8ec;--mut:#9aa3b2;--line:#2b303b;--acc:#60a5fa;--acc2:#93c5fd;--accbg:#1c2740;--code:#1f232c;--nav:#1b1e25;--shadow:0 1px 2px rgba(0,0,0,.5);color-scheme:dark}}
:root[data-theme=dark]{--bg:#15171c;--bg2:#1b1e25;--fg:#e6e8ec;--mut:#9aa3b2;--line:#2b303b;--acc:#60a5fa;--acc2:#93c5fd;--accbg:#1c2740;--code:#1f232c;--nav:#1b1e25;--shadow:0 1px 2px rgba(0,0,0,.5);color-scheme:dark}
*{box-sizing:border-box}html{scroll-padding-top:76px;-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.65 Inter,system-ui,-apple-system,"Segoe UI","Noto Sans CJK SC","Noto Sans JP",sans-serif}
a{color:var(--acc);text-decoration:none}a:hover{text-decoration:underline}
.nav{position:sticky;top:0;z-index:50;height:60px;display:flex;align-items:center;gap:14px;padding:0 max(16px,env(safe-area-inset-left));background:var(--nav);border-bottom:1px solid var(--line);box-shadow:var(--shadow)}
.brand{display:flex;align-items:center;gap:10px;color:var(--fg);font-weight:700;font-size:18px}.brand:hover{text-decoration:none}.brand img{height:30px;width:auto}
.ver{font-size:12px;padding:2px 8px;border-radius:99px;background:var(--accbg);color:var(--acc);font-weight:600}
.nav .links{display:flex;gap:4px;margin-left:8px}.nav .links a{color:var(--fg);padding:6px 10px;border-radius:8px;font-weight:500;font-size:15px}.nav .links a:hover{background:var(--bg2);text-decoration:none}
.sp{flex:1}
.btn{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);background:var(--bg);color:var(--fg);padding:6px 10px;border-radius:8px;font:inherit;font-size:14px;cursor:pointer}.btn:hover{background:var(--bg2);text-decoration:none}
select.btn{padding-right:4px}
.sbtn{min-width:210px;justify-content:space-between;color:var(--mut)}.sbtn kbd{font:12px/1 ui-monospace,monospace;border:1px solid var(--line);border-radius:5px;padding:2px 5px;background:var(--bg2)}
.burger{display:none}
.layout{display:grid;grid-template-columns:292px minmax(0,1fr) 250px;max-width:1500px;margin:0 auto}
.side{position:sticky;top:60px;align-self:start;height:calc(100vh - 60px);overflow:auto;padding:18px 10px 40px max(16px,env(safe-area-inset-left));border-right:1px solid var(--line)}
.side details{margin-bottom:4px}.side summary{list-style:none;cursor:pointer;padding:7px 10px;border-radius:8px;font-weight:700;font-size:14px;display:flex;align-items:center;justify-content:space-between}
.side summary::-webkit-details-marker{display:none}.side summary:hover{background:var(--bg2)}.side summary::after{content:"›";transition:transform .15s;color:var(--mut);font-size:18px}.side details[open]>summary::after{transform:rotate(90deg)}
.side .it{display:block;padding:6px 10px 6px 14px;margin:1px 0 1px 8px;border-radius:8px;color:var(--fg);font-size:14.5px}.side .it:hover{background:var(--bg2);text-decoration:none}
.side .it.on{background:var(--accbg);color:var(--acc);font-weight:600}
main{min-width:0;padding:30px 44px 60px}
article{max-width:820px;margin:0 auto}
.crumb{font-size:13px;color:var(--mut);margin-bottom:10px}
article h1.title{font-size:2.15rem;line-height:1.2;margin:0 0 18px;letter-spacing:-.01em}
article h2{font-size:1.55rem;margin:2.2em 0 .6em;padding-top:.3em;border-top:1px solid var(--line);line-height:1.3}article h3{font-size:1.2rem;margin:1.8em 0 .4em}
article h2 .headerlink,article h3 .headerlink{opacity:0;margin-left:8px;font-size:.8em}article h2:hover .headerlink,article h3:hover .headerlink{opacity:.7}
article p,article li{overflow-wrap:anywhere}article li{margin:.25em 0}article img{max-width:100%;height:auto}
.shot{margin:1.4em 0;text-align:center}.shot img{border:1px solid var(--line);border-radius:12px;box-shadow:0 6px 24px rgba(0,0,0,.12)}.shot figcaption{font-size:13px;color:var(--mut);margin-top:6px}
blockquote{margin:1.2em 0;padding:12px 18px;border-left:4px solid var(--acc);background:var(--accbg);border-radius:0 10px 10px 0}blockquote p{margin:.3em 0}
.tbl{overflow-x:auto;margin:1.2em 0;border:1px solid var(--line);border-radius:10px}table{border-collapse:collapse;width:100%;font-size:14.5px}
th,td{padding:9px 13px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}th{background:var(--bg2);font-weight:700}tr:last-child td{border-bottom:0}
code{font:.88em ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--code);padding:.15em .4em;border-radius:6px}
pre{position:relative;background:var(--code);border:1px solid var(--line);border-radius:10px;padding:14px 16px;overflow:auto;line-height:1.5}pre code{background:none;padding:0}
pre .cp{position:absolute;top:8px;right:8px;opacity:0;font-size:12px;padding:3px 8px}pre:hover .cp{opacity:1}
hr{border:0;border-top:1px solid var(--line);margin:2em 0}
.edit{margin-top:40px;font-size:14px}
.pn{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:28px}.pn a{border:1px solid var(--line);border-radius:10px;padding:12px 16px;color:var(--fg)}.pn a:hover{border-color:var(--acc);text-decoration:none}
.pn small{display:block;color:var(--mut);font-size:12px}.pn b{color:var(--acc)}.pn .n{text-align:right;grid-column:2}
.toc{position:sticky;top:60px;align-self:start;max-height:calc(100vh - 60px);overflow:auto;padding:30px 18px 30px 8px;font-size:13.5px}
.toc b{display:block;margin-bottom:8px;font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--mut)}
.toc a{display:block;color:var(--mut);padding:3px 0 3px 10px;border-left:2px solid var(--line)}.toc a.l3{padding-left:22px}.toc a.on{color:var(--acc);border-left-color:var(--acc);font-weight:600}.toc a:hover{color:var(--fg);text-decoration:none}
footer{border-top:1px solid var(--line);background:var(--bg2);padding:28px max(16px,env(safe-area-inset-left));font-size:14px;color:var(--mut)}
footer .in{max-width:1200px;margin:0 auto;display:flex;flex-wrap:wrap;gap:12px 36px;justify-content:space-between}footer a{color:var(--mut)}footer b{color:var(--fg)}
.ov{position:fixed;inset:0;background:rgba(0,0,0,.5);display:none;align-items:flex-start;justify-content:center;padding-top:10vh;z-index:100}.ov.show{display:flex}
.sbox{width:min(640px,92vw);background:var(--bg);border:1px solid var(--line);border-radius:14px;box-shadow:0 20px 60px rgba(0,0,0,.4);overflow:hidden}
.sbox input{width:100%;border:0;border-bottom:1px solid var(--line);background:transparent;color:var(--fg);font:inherit;font-size:17px;padding:16px 18px;outline:none}
.res{max-height:55vh;overflow:auto}.res a{display:block;padding:10px 18px;color:var(--fg);border-bottom:1px solid var(--line)}.res a:hover,.res a.sel{background:var(--accbg);text-decoration:none}
.res b{display:block;font-size:14px}.res span{display:block;font-size:13px;color:var(--mut);margin-top:2px}.res mark{background:#fde68a;color:#000;border-radius:3px}.res .none{padding:18px;color:var(--mut)}
@media(max-width:1180px){.layout{grid-template-columns:270px minmax(0,1fr)}.toc{display:none}}
@media(max-width:900px){.layout{grid-template-columns:minmax(0,1fr)}.burger{display:inline-flex}.nav .links,.sbtn kbd,.sbtn span{display:none}.sbtn{min-width:0}
.side{position:fixed;left:0;top:60px;bottom:0;width:min(86vw,320px);height:auto;background:var(--bg);z-index:60;transform:translateX(-102%);transition:transform .2s;box-shadow:var(--shadow)}body.open .side{transform:none}
main{padding:22px max(16px,env(safe-area-inset-left)) 50px}.gh{display:none}#lg{max-width:112px}.nav{gap:8px}.ver{display:none}.pn{grid-template-columns:1fr}.pn .n{grid-column:1}article h1.title{font-size:1.7rem}}
"""

JS = r"""
(function(){
var D=document,R=D.documentElement,$=function(s,c){return(c||D).querySelector(s)};
function theme(t){try{if(t)localStorage.setItem('stellio-docs-theme',t);else localStorage.removeItem('stellio-docs-theme')}catch(e){}
 if(t)R.setAttribute('data-theme',t);else R.removeAttribute('data-theme')}
try{var s=localStorage.getItem('stellio-docs-theme');if(s)R.setAttribute('data-theme',s)}catch(e){}
$('#th').onclick=function(){var cur=R.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');theme(cur==='dark'?'light':'dark')};
$('#bg').onclick=function(){D.body.classList.toggle('open')};
D.addEventListener('click',function(e){if(D.body.classList.contains('open')&&!e.target.closest('.side,#bg'))D.body.classList.remove('open')});
$('#lg').onchange=function(){location.href=this.value};
var act=$('.side .it.on');if(act&&act.scrollIntoView)act.scrollIntoView({block:'center'});
D.querySelectorAll('pre').forEach(function(p){var b=D.createElement('button');b.className='btn cp';b.type='button';b.textContent=B.copy;
 b.onclick=function(){var t=p.querySelector('code');navigator.clipboard&&navigator.clipboard.writeText((t||p).innerText).then(function(){b.textContent=B.copied;setTimeout(function(){b.textContent=B.copy},1400)})};p.appendChild(b)});
var links=[].slice.call(D.querySelectorAll('.toc a'));
if(links.length&&'IntersectionObserver'in window){var map={};links.forEach(function(a){map[a.getAttribute('href').slice(1)]=a});
 var io=new IntersectionObserver(function(en){en.forEach(function(x){if(x.isIntersecting){links.forEach(function(a){a.classList.remove('on')});var a=map[x.target.id];if(a)a.classList.add('on')}})},{rootMargin:'-70px 0px -70% 0px'});
 D.querySelectorAll('article h2[id],article h3[id]').forEach(function(h){io.observe(h)})}
var ov=$('#ov'),inp=$('#q'),res=$('#res'),idx=null,sel=0,hits=[];
function norm(x){return x.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'')}
function load(cb){if(idx)return cb();fetch(B.search).then(function(r){return r.json()}).then(function(j){idx=j.map(function(e){e.n=norm(e.t+' '+e.h+' '+e.x);e.nh=norm(e.t+' '+e.h);return e});cb()}).catch(function(){idx=[];cb()})}
function esc(x){return x.replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function snip(e,ts){var low=norm(e.x),p=-1;for(var i=0;i<ts.length&&p<0;i++)p=low.indexOf(ts[i]);if(p<0)p=0;var a=Math.max(0,p-40),t=e.x.substr(a,130);return(a?'… ':'')+esc(t)}
function run(){var q=norm(inp.value.trim());if(!q){res.innerHTML='';hits=[];return}var ts=q.split(/\s+/);
 hits=idx.map(function(e){var sc=0;for(var i=0;i<ts.length;i++){if(e.n.indexOf(ts[i])<0)return null;sc+=(e.nh.indexOf(ts[i])>=0?5:1)}return{e:e,sc:sc}}).filter(Boolean).sort(function(a,b){return b.sc-a.sc}).slice(0,9);
 sel=0;res.innerHTML=hits.length?hits.map(function(h,i){return'<a href="'+h.e.u+'" class="'+(i?'':'sel')+'"><b>'+esc(h.e.t)+(h.e.h?' › '+esc(h.e.h):'')+'</b><span>'+snip(h.e,ts)+'</span></a>'}).join(''):'<div class="none">'+B.nosearch+'</div>'}
function open(){ov.classList.add('show');load(function(){inp.focus();inp.select();run()})}
function close(){ov.classList.remove('show')}
$('#sb').onclick=open;ov.onclick=function(e){if(e.target===ov)close()};inp.oninput=run;
function mark(){[].forEach.call(res.children,function(a,i){a.classList.toggle('sel',i===sel)})}
D.addEventListener('keydown',function(e){
 if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'||(e.key==='/'&&!/INPUT|TEXTAREA|SELECT/.test(D.activeElement.tagName))){e.preventDefault();open()}
 else if(e.key==='Escape')close();
 else if(ov.classList.contains('show')){if(e.key==='ArrowDown'){sel=Math.min(sel+1,hits.length-1);mark();e.preventDefault()}else if(e.key==='ArrowUp'){sel=Math.max(sel-1,0);mark();e.preventDefault()}else if(e.key==='Enter'&&hits[sel]){location.href=hits[sel].e.u}}});
})();
"""


def build(out_dir, base):
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir)
    if not base.endswith('/'):
        base += '/'
    ver = version()
    used = set()
    pages_all = {l: W.parse(l) for l, _, _ in LANGS}
    order = [s for _, g in GROUPS for s in g]
    changed = 0
    for lang, lname, flag in LANGS:
        ui = UI[lang]
        pg = pages_all[lang]
        titles = {s: pg[s][0] for s in W.PAGES}
        titles['Changelog'] = W.CHANGELOG_TITLE[lang]
        rendered, search = {}, []
        for slug in order:
            md = W.changelog_page(lang) if slug == 'Changelog' else pg[slug][1]
            body, toc = render(lang, slug, md, base, used)
            rendered[slug] = (body, toc)
            search += search_entries(lang, titles[slug], f'{base}{lang}/{slug}/', body)
        os.makedirs(os.path.join(out_dir, lang), exist_ok=True)
        json.dump(search, open(os.path.join(out_dir, lang, 'search.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        for i, slug in enumerate(order):
            body, toc = rendered[slug]
            gkey = next(k for k, g in GROUPS if slug in g)
            side = ''
            for k, g in GROUPS:
                items = ''.join(f'<a class="it{" on" if s == slug else ""}" href="{base}{lang}/{s}/">{ICONS[s]} {html.escape(titles[s])}</a>' for s in g)
                side += f'<details{" open" if k == gkey else ""}><summary>{html.escape(ui[k])}</summary>{items}</details>'
            tocs = ''.join(f'<a class="l{lv}" href="#{id_}">{html.escape(tx.replace("¶", "").strip())}</a>' for lv, id_, tx in toc if lv in (2, 3))
            tochtml = f'<aside class="toc"><b>{html.escape(ui["toc"])}</b>{tocs}</aside>' if tocs else '<aside class="toc"></aside>'
            prev = order[i - 1] if i else None
            nxt = order[i + 1] if i + 1 < len(order) else None
            pn = '<div class="pn">' + (f'<a href="{base}{lang}/{prev}/"><small>« {html.escape(ui["prev"])}</small><b>{html.escape(titles[prev])}</b></a>' if prev else '<span></span>') \
                + (f'<a class="n" href="{base}{lang}/{nxt}/"><small>{html.escape(ui["next"])} »</small><b>{html.escape(titles[nxt])}</b></a>' if nxt else '') + '</div>'
            src = f'docs/wiki/src/{lang}.md' if slug != 'Changelog' else 'changelog.json'
            edit = f'<p class="edit">✏️ <a href="https://github.com/{REPO}/edit/main/{src}" target="_blank" rel="noopener">{html.escape(ui["edit"])}</a></p>'
            langsel = ''.join(f'<option value="{base}{c}/{slug}/"{" selected" if c == lang else ""}>{fl} {nm}</option>' for c, nm, fl in LANGS)
            alts = ''.join(f'<link rel="alternate" hreflang="{c}" href="{base}{c}/{slug}/">' for c, _, _ in LANGS)
            title = titles[slug]
            B = json.dumps({'copy': ui['copy'], 'copied': ui['copied'], 'nosearch': ui['nosearch'], 'search': f'{base}{lang}/search.json'}, ensure_ascii=False)
            page = f'''<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{html.escape(title)} | Stellio</title><meta name="description" content="{html.escape(title)} — Stellio, 3D printing file manager">
<link rel="icon" href="https://stellio-app.com/assets/favicon.png">{alts}
<style>{CSS}</style></head><body>
<header class="nav">
<button class="btn burger" id="bg" aria-label="{html.escape(ui["menu"])}">☰</button>
<a class="brand" href="{base}{lang}/Home/"><img src="https://stellio-app.com/assets/logo-nom-stellio.png" alt="Stellio" onerror="this.outerHTML='&lt;b&gt;Stellio&lt;/b&gt;'"><span class="ver">v{html.escape(ver)}</span></a>
<nav class="links"><a href="{base}{lang}/Home/">{html.escape(ui["docs"])}</a><a href="https://stellio-app.com" target="_blank" rel="noopener">{html.escape(ui["site"])}</a><a href="https://demo.stellio-app.com" target="_blank" rel="noopener">{html.escape(ui["demo"])}</a></nav>
<span class="sp"></span>
<button class="btn sbtn" id="sb" type="button">🔍 <span>{html.escape(ui["search"])}</span><kbd>Ctrl K</kbd></button>
<select class="btn" id="lg" aria-label="Language">{langsel}</select>
<button class="btn" id="th" type="button" title="{html.escape(ui["theme"])}" aria-label="{html.escape(ui["theme"])}">◐</button>
<a class="btn gh" href="https://github.com/{REPO}" target="_blank" rel="noopener" aria-label="GitHub">GitHub</a>
</header>
<div class="layout"><nav class="side">{side}</nav>
<main><article><div class="crumb">{html.escape(ui[gkey])} › {html.escape(title)}</div><h1 class="title">{html.escape(title)}</h1>
{body}{edit}{pn}</article></main>{tochtml}</div>
<footer><div class="in"><div><b>Stellio</b><br>{html.escape(ui["rights"])}<br>© 2026 Stellio</div>
<div><b>{html.escape(ui["community"])}</b><br><a href="https://github.com/{REPO}" target="_blank" rel="noopener">GitHub</a> · <a href="https://discord.gg/ySxpHvS6bd" target="_blank" rel="noopener">Discord</a> · <a href="https://github.com/{REPO}/issues" target="_blank" rel="noopener">Issues</a></div>
<div><b>{html.escape(ui["download"])}</b><br><a href="https://github.com/{REPO}/releases" target="_blank" rel="noopener">GitHub Releases</a> · <a href="https://stellio-app.com" target="_blank" rel="noopener">stellio-app.com</a></div></div></footer>
<div class="ov" id="ov"><div class="sbox"><input id="q" type="search" placeholder="{html.escape(ui["search"])}…" autocomplete="off"><div class="res" id="res"></div></div></div>
<script>var B={B};</script><script>{JS}</script></body></html>'''
            os.makedirs(os.path.join(out_dir, lang, slug), exist_ok=True)
            open(os.path.join(out_dir, lang, slug, 'index.html'), 'w', encoding='utf-8', newline='\n').write(page)
            changed += 1
    for ver_, lg, name in sorted(used):
        dst = os.path.join(out_dir, 'assets', 'img', ver_, lg)
        os.makedirs(dst, exist_ok=True)
        shutil.copyfile(os.path.join(W.IMG, ver_, lg, f'{name}.png'), os.path.join(dst, f'{name}.png'))
    langs_js = json.dumps([c for c, _, _ in LANGS])
    open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8', newline='\n').write(
        f'<!doctype html><meta charset="utf-8"><title>Stellio docs</title><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<script>var L={langs_js},l=(navigator.language||"en").slice(0,2);location.replace("{base}"+(L.indexOf(l)>=0?l:"en")+"/Home/")</script>'
        f'<noscript><a href="{base}en/Home/">Stellio docs</a></noscript>')
    open(os.path.join(out_dir, '.nojekyll'), 'w').close()
    # liens internes
    broken = []
    for lang, _, _ in LANGS:
        for slug in order:
            h = open(os.path.join(out_dir, lang, slug, 'index.html'), encoding='utf-8').read()
            for m in re.findall(r'href="%s([a-z]{2}/[A-Za-z-]+)/"' % re.escape(base), h):
                if not os.path.exists(os.path.join(out_dir, m, 'index.html')):
                    broken.append((lang, slug, m))
    return broken, changed, len(used)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--base', default='/')
    a = ap.parse_args()
    errs = W.check()
    for e in errs:
        print('ERREUR', e)
    if errs:
        sys.exit(1)
    broken, n, ni = build(a.out, a.base)
    print(f'{n} pages, {ni} captures, liens cassés : {sorted(set(broken))[:5]}')
    if broken:
        sys.exit(1)


if __name__ == '__main__':
    main()
