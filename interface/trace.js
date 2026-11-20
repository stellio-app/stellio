/* Stellio — v1.1.6 : traçabilité d'impression ; v1.1.7 : rattacher une impression à une version, associer un G-code à son modèle, empreinte du profil (page « Traçabilité » + encart dans « Versions du modèle »).
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
const dFmt = (s) => { const n = Number(s); const d = (s !== '' && s != null && isFinite(n)) ? new Date(n < 1e12 ? n * 1000 : n) : new Date(String(s || '').replace(' ', 'T')); return isNaN(d) ? '' : d.toLocaleDateString(lang(), { day: 'numeric', month: 'short', year: 'numeric' }); };

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
    const combos = d.combos.map(c => `<tr><td>${c.version == null ? esc(T('unsaved', 'non enregistrée')) : 'v' + c.version}</td><td>${c.profile ? esc(c.profile) : '—'}${c.profile_fp ? ` <span class="tr-fp" title="${esc(T('fp_title', 'Empreinte des réglages du profil : {fp}', { fp: c.profile_fp }))}">#${esc(c.profile_fp.slice(0, 6))}</span>` : ''}</td>
        <td>${c.success}</td><td>${c.failed}</td><td>${c.partial}</td><td><span class="tr-rate ${rateCls(c.rate)}">${pct(c.rate)}</span>${c.confident ? '' : ` <span class="v13-muted">${esc(T('low_sample', 'peu de données'))}</span>`}</td></tr>`).join('');
    const fpByName = {};
    d.combos.forEach(c => { if (c.profile && c.profile_fp) (fpByName[c.profile] = fpByName[c.profile] || new Set()).add(c.profile_fp); });
    const fpWarn = Object.keys(fpByName).some(k => fpByName[k].size > 1);
    mb.insertAdjacentHTML('afterbegin', `<div class="v13-box tr-box"><h4>${esc(T('title', 'Traçabilité'))}</h4>
        ${fpWarn ? `<p class="v13-muted"><i class="fa-solid fa-fingerprint"></i> ${esc(T('fp_diff', 'Réglages différents sous le même nom de profil : ils sont comptés séparément.'))}</p>` : ''}
        <p><i class="fa-solid fa-trophy"></i> ${esc(T('best', 'Meilleure combinaison'))} : ${bestLine(d.best)}</p>
        ${combos ? `<div class="v13-scroll"><table class="v13-tbl"><thead><tr><th>${esc(T('col_version', 'Version'))}</th><th>${esc(T('col_profile', 'Profil'))}</th><th>✓</th><th>✗</th><th>~</th><th>${esc(T('col_rate', 'Réussite'))}</th></tr></thead><tbody>${combos}</tbody></table></div>` : `<p class="v13-muted">${esc(T('unrated_all', 'Impressions tracées, mais aucune n\'est encore notée dans l\'historique.'))}</p>`}
        <p class="v13-muted">${esc(T('hint', 'Une version automatique « Avant impression » est enregistrée quand le fichier a changé depuis la dernière version.'))}</p></div>`);
}

/* ---------- rattacher une impression / associer un G-code ---------- */
const MODEL_EXT = /\.(stl|3mf|obj|ply|off)$/i;
let dlg = null;

function ensureDialog() {
    if (dlg) return dlg;
    dlg = document.createElement('div');
    dlg.id = 'modal-trace-attach';
    dlg.className = 'modal hidden';
    dlg.innerHTML = `<div class="modal-content" style="max-width:560px;">
        <div class="modal-header"><h3><i class="fa-solid fa-code-branch"></i> <span id="tr-dlg-title"></span></h3>
          <button class="modal-close" type="button" id="tr-dlg-x">×</button></div>
        <div class="modal-body">
          <p class="v13-muted" id="tr-dlg-help"></p>
          <input type="text" class="settings-select" id="tr-dlg-search" style="width:100%;margin-bottom:8px;">
          <div class="tr-dlg-list" id="tr-dlg-list"></div>
          <div id="tr-dlg-ver" class="tr-dlg-ver" hidden></div>
          <div class="modal-footer" style="display:flex;justify-content:flex-end;gap:8px;margin-top:14px;">
            <button type="button" class="btn btn-secondary" id="tr-dlg-cancel"></button>
            <button type="button" class="btn btn-primary" id="tr-dlg-ok" disabled></button></div>
        </div></div>`;
    document.body.appendChild(dlg);
    const close = () => { if (typeof closeModal === 'function') closeModal('modal-trace-attach'); else dlg.classList.add('hidden'); };
    dlg.querySelector('#tr-dlg-x').onclick = close;
    dlg.querySelector('#tr-dlg-cancel').onclick = close;
    dlg.addEventListener('click', (e) => { if (e.target === dlg) close(); });
    return dlg;
}

function openAttach(opts) {
    const link = !opts.historyId;          // sans ligne d'historique : on associe un G-code à son modèle
    const el = ensureDialog();
    const $d = (sel) => el.querySelector(sel);
    $d('#tr-dlg-title').textContent = link ? T('link_title', 'Associer à un modèle') : T('attach_title', 'Rattacher à une version du modèle');
    $d('#tr-dlg-help').textContent = link ? T('link_help', 'Ce G-code a été découpé depuis un modèle : choisissez-le.') : T('attach_help', 'Choisissez le modèle imprimé puis la version utilisée.');
    $d('#tr-dlg-search').placeholder = T('search', 'Rechercher un modèle…');
    $d('#tr-dlg-search').value = '';
    $d('#tr-dlg-cancel').textContent = T('cancel', 'Annuler');
    $d('#tr-dlg-ok').textContent = link ? T('link_btn', 'Associer') : T('attach_btn', 'Rattacher');
    $d('#tr-dlg-ok').disabled = true;
    $d('#tr-dlg-ver').hidden = true;
    let chosen = null;
    const models = (typeof allFiles !== 'undefined' ? allFiles : []).filter(f => f.path && MODEL_EXT.test(f.name || f.path));
    const draw = () => {
        const q = $d('#tr-dlg-search').value.trim().toLowerCase();
        const list = models.filter(f => !q || (f.name || '').toLowerCase().includes(q)).slice(0, 80);
        $d('#tr-dlg-list').innerHTML = list.length ? list.map((f, i) => `<button type="button" class="tr-dlg-item${chosen && chosen.path === f.path ? ' sel' : ''}" data-i="${i}"><i class="fa-solid fa-cube"></i> <span>${esc(f.name)}</span></button>`).join('')
            : `<div class="v13-muted" style="padding:10px;">${esc(T('no_models', 'Aucun modèle.'))}</div>`;
        $d('#tr-dlg-list').querySelectorAll('.tr-dlg-item').forEach(b => b.onclick = () => pick(list[Number(b.dataset.i)]));
    };
    const pick = async (f) => {
        chosen = f; draw();
        $d('#tr-dlg-ok').disabled = false;
        if (link) return;
        const box = $d('#tr-dlg-ver');
        box.hidden = false;
        box.innerHTML = '<div class="v13-muted">…</div>';
        try {
            const d = await getJson('/api/trace/model?path=' + encodeURIComponent(f.path.replace(/\\/g, '/')));
            if (!d.versions.length) { box.innerHTML = `<p class="v13-muted">${esc(T('no_versions', 'Ce modèle n\'a pas encore de version enregistrée : l\'impression sera rattachée au modèle seul.'))}</p>`; return; }
            box.innerHTML = `<label class="v13-muted" for="tr-dlg-version">${esc(T('pick_version', 'Version'))}</label>
                <select id="tr-dlg-version" class="settings-select" style="width:100%;">${d.versions.map(v => `<option value="${v.version}">v${v.version}${v.note ? ' — ' + esc(v.note) : ''} · ${esc(dFmt(v.created_at))}</option>`).join('')}
                <option value="">${esc(T('version_unknown', 'Version inconnue (modèle seulement)'))}</option></select>`;
        } catch (e) { box.innerHTML = ''; }
    };
    $d('#tr-dlg-search').oninput = draw;
    $d('#tr-dlg-ok').onclick = async () => {
        if (!chosen) return;
        const mp = chosen.path.replace(/\\/g, '/');
        $d('#tr-dlg-ok').disabled = true;
        try {
            let res, out;
            if (link) {
                res = await fetch(`${API}/api/trace/link`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ file_path: opts.filePath, model_path: mp }) });
            } else {
                const sel = $d('#tr-dlg-version');
                res = await fetch(`${API}/api/trace/entry`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ history_id: opts.historyId, model_path: mp, version: sel ? sel.value : '' }) });
            }
            out = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(out.error || res.status);
            if (typeof closeModal === 'function') closeModal('modal-trace-attach');
            const v = !link && $d('#tr-dlg-version') && $d('#tr-dlg-version').value ? ' v' + $d('#tr-dlg-version').value : '';
            if (typeof showToast === 'function') showToast(link ? T('link_done', 'G-code associé à {m} ({n} impression(s) rattachée(s))', { m: chosen.name, n: out.relinked || 0 }) : T('attach_done', 'Impression rattachée à {m}{v}', { m: chosen.name, v }), 'success');
            if (opts.onDone) opts.onDone(out);
        } catch (e) {
            $d('#tr-dlg-ok').disabled = false;
            if (typeof showToast === 'function') showToast(T('attach_error', 'Rattachement impossible'), 'error');
        }
    };
    draw();
    if (typeof openModal === 'function') openModal('modal-trace-attach'); else el.classList.remove('hidden');
}

window.StellioTrace = { onShow, decorate, openAttach };

})();
