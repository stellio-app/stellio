/* Stellio — v1.1.6 : traçabilité d'impression (page « Traçabilité » + encart dans « Versions du modèle »).
   Modèle → version → profil de slicer → résultat ; meilleure combinaison par modèle.
   Données : /api/trace/overview, /api/trace/model (modules/print_traceability.py). Dépend de script.js (I18N, escapeHtml, API). */
(function () {
'use strict';

const $ = (id) => document.getElementById(id);
const tr = (k, fb, p) => {
    let s = (typeof I18N !== 'undefined' && I18N.t) ? I18N.t(k) : k;
    if (!s || s === k) s = fb;
    if (p) Object.keys(p).forEach(n => { s = s.split('{' + n + '}').join(p[n]); });
    return s;
};
const T = (k, fb, p) => tr('trace.' + k, fb, p);
const esc = (v) => (typeof escapeHtml === 'function' ? escapeHtml(String(v)) : String(v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
const lang = () => (typeof I18N !== 'undefined' && I18N.lang) || 'fr';
const pct = (r) => (r == null ? '—' : Math.round(r * 100) + ' %');
const rateCls = (r) => (r == null ? '' : (r >= 0.85 ? 'ok' : (r >= 0.6 ? 'warn' : 'bad')));
const dFmt = (s) => { try { return new Date(String(s).replace(' ', 'T')).toLocaleDateString(lang(), { day: 'numeric', month: 'short', year: 'numeric' }); } catch (e) { return s || ''; } };

async function getJson(url) {
    const r = await fetch(`${API}${url}`, { cache: 'no-store' });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(d.error || r.status);
    return d;
}

function bestLine(b) {
    if (!b) return esc(T('best_none', 'Pas encore assez d\'impressions notées pour désigner la meilleure combinaison.'));
    const prof = b.profile ? ` · ${esc(b.profile)}` : ` · ${esc(T('no_profile', 'profil non renseigné'))}`;
    return `<b>v${b.version}</b>${prof} — <span class="tr-rate ${rateCls(b.rate)}">${b.success}/${b.total} (${pct(b.rate)})</span>`;
}

/* ---------- page ---------- */
let timer = null, wired = false;
async function loadPage() {
    const box = $('tr-list');
    if (!box) return;
    const q = ($('tr-search') && $('tr-search').value || '').trim();
    try {
        const d = await getJson('/api/trace/overview?q=' + encodeURIComponent(q));
        if (!d.models.length) {
            box.innerHTML = `<div class="pl-empty">${esc(q ? T('none_match', 'Aucun modèle ne correspond.') : T('empty', 'Aucune impression tracée pour l\'instant. Chaque impression lancée depuis Stellio sera reliée à la version du modèle et au profil utilisés ; notez le résultat dans l\'historique pour voir apparaître les taux de réussite.'))}</div>`;
            return;
        }
        box.innerHTML = `<div class="pl-card"><div class="v13-scroll"><table class="v13-tbl"><thead><tr>
            <th>${esc(T('col_model', 'Modèle'))}</th><th>${esc(T('col_prints', 'Impressions'))}</th><th>${esc(T('col_versions', 'Versions'))}</th><th>${esc(T('col_best', 'Meilleure combinaison'))}</th></tr></thead><tbody>` +
            d.models.map((m, i) => `<tr class="tr-row" data-i="${i}" tabindex="0"><td><b>${esc(m.name)}</b></td><td>${m.prints}${m.rated !== m.prints ? ` <span class="v13-muted">(${esc(T('rated', '{n} notées', { n: m.rated }))})</span>` : ''}</td>
            <td>${m.versions.length ? m.versions.map(v => 'v' + v).join(', ') : '—'}</td><td>${bestLine(m.best)}</td></tr>`).join('') + `</tbody></table></div></div>`;
        box.querySelectorAll('.tr-row').forEach(tr_ => {
            const open = () => { const m = d.models[Number(tr_.dataset.i)]; window.StellioV113 && window.StellioV113.openVersions(m.path, m.name); };
            tr_.onclick = open;
            tr_.onkeydown = (e) => { if (e.key === 'Enter') open(); };
        });
    } catch (e) {
        box.innerHTML = `<div class="pl-empty">${esc(T('load_error', 'Traçabilité indisponible pour le moment.'))}</div>`;
    }
}

function onShow() {
    if (!wired && $('tr-search')) {
        wired = true;
        $('tr-search').addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(loadPage, 250); });
    }
    loadPage();
}

/* ---------- encart dans « Versions du modèle » ---------- */
async function decorate(mb, path) {
    let d;
    try { d = await getJson('/api/trace/model?path=' + encodeURIComponent(path)); } catch (e) { return; }
    const old = mb.querySelector('.tr-box');
    if (old) old.remove();
    // badge de réussite sur chaque version
    mb.querySelectorAll('.v13-row').forEach(row => {
        const v = d.versions.find(x => x.id === Number(row.dataset.id));
        const main = row.querySelector('.v13-row-main .v13-muted');
        if (!v || !main || row.querySelector('.tr-badge')) return;
        const s = v.stats;
        const txt = s && s.total ? `${s.success}✓ ${s.failed}✗${s.partial ? ' ' + s.partial + '~' : ''} · ${pct(s.rate)}` : (v.prints ? T('unrated', '{n} impr. non notée(s)', { n: v.prints }) : T('never', 'jamais imprimée'));
        main.insertAdjacentHTML('afterend', `<div class="tr-badge ${s && s.total ? rateCls(s.rate) : ''}">${esc(txt)}</div>`);
    });
    if (!d.prints) {
        mb.insertAdjacentHTML('afterbegin', `<div class="v13-box tr-box"><h4>${esc(T('title', 'Traçabilité'))}</h4><p class="v13-muted">${esc(T('model_none', 'Aucune impression tracée pour ce modèle pour l\'instant.'))}</p></div>`);
        return;
    }
    const combos = d.combos.map(c => `<tr><td>${c.version == null ? esc(T('unsaved', 'non enregistrée')) : 'v' + c.version}</td><td>${c.profile ? esc(c.profile) : '—'}</td>
        <td>${c.success}</td><td>${c.failed}</td><td>${c.partial}</td><td><span class="tr-rate ${rateCls(c.rate)}">${pct(c.rate)}</span>${c.confident ? '' : ` <span class="v13-muted">${esc(T('low_sample', 'peu de données'))}</span>`}</td></tr>`).join('');
    mb.insertAdjacentHTML('afterbegin', `<div class="v13-box tr-box"><h4>${esc(T('title', 'Traçabilité'))}</h4>
        <p><i class="fa-solid fa-trophy"></i> ${esc(T('best', 'Meilleure combinaison'))} : ${bestLine(d.best)}</p>
        ${combos ? `<div class="v13-scroll"><table class="v13-tbl"><thead><tr><th>${esc(T('col_version', 'Version'))}</th><th>${esc(T('col_profile', 'Profil'))}</th><th>✓</th><th>✗</th><th>~</th><th>${esc(T('col_rate', 'Réussite'))}</th></tr></thead><tbody>${combos}</tbody></table></div>` : `<p class="v13-muted">${esc(T('unrated_all', 'Impressions tracées, mais aucune n\'est encore notée dans l\'historique.'))}</p>`}
        <p class="v13-muted">${esc(T('hint', 'Une version automatique « Avant impression » est enregistrée quand le fichier a changé depuis la dernière version.'))}</p></div>`);
}

window.StellioTrace = { onShow, decorate };
})();
