/* Stellio — v1.1.7 : API publique (Paramètres › API publique) — jetons, droits, révocation, journal.
   Données : /api/tokens, /api/tokens/log (modules/public_api.py). Dépend de script.js (I18N, escapeHtml, showToast, API). */
(function () {
'use strict';

const $ = (id) => document.getElementById(id);
const tr = (k, fb, p) => {
    let s = (typeof I18N !== 'undefined' && I18N.t) ? I18N.t('api.' + k) : k;
    if (!s || s === 'api.' + k) s = fb;
    if (p) Object.keys(p).forEach(n => { s = s.split('{' + n + '}').join(p[n]); });
    return s;
};
const esc = (v) => (typeof escapeHtml === 'function' ? escapeHtml(String(v)) : String(v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
const lang = () => (typeof I18N !== 'undefined' && I18N.lang) || 'fr';
const dt = (ts) => { if (!ts) return '—'; try { return new Date(ts * 1000).toLocaleString(lang(), { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }); } catch (e) { return ''; } };
const toast = (m, t) => { if (typeof showToast === 'function') showToast(m, t || 'info'); };

async function j(url, opts) {
    const r = await fetch(`${API}${url}`, Object.assign({ cache: 'no-store' }, opts || {}));
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(d.error || r.status);
    return d;
}

let errorsOnly = false;

async function load() {
    const box = $('api-tokens-box');
    if (!box) return;
    try {
        const [t, l] = await Promise.all([j('/api/tokens'), j('/api/tokens/log?limit=60' + (errorsOnly ? '&errors=1' : ''))]);
        box.innerHTML = renderTokens(t.tokens) + renderLog(l.log);
        const f = $('api-log-errors'); if (f) f.onchange = () => { errorsOnly = f.checked; load(); };
    } catch (e) {
        box.innerHTML = `<p class="settings-hint">${esc(tr('unavailable', 'Réservé au compte propriétaire.'))}</p>`;
    }
}

function renderTokens(list) {
    const rows = list.map(t => `<tr class="${t.revoked_at ? 'api-revoked' : ''}">
        <td><b>${esc(t.name)}</b><div class="v13-muted"><code>${esc(t.prefix)}…</code></div></td>
        <td><span class="api-perm ${t.perm}">${esc(t.perm === 'write' ? tr('perm_write', 'Lecture + écriture') : tr('perm_read', 'Lecture seule'))}</span></td>
        <td>${esc(dt(t.created_at))}</td><td>${esc(t.last_used_at ? dt(t.last_used_at) : tr('never', 'Jamais'))}</td>
        <td>${t.revoked_at ? `<span class="v13-muted">${esc(tr('revoked', 'Révoqué'))} ${esc(dt(t.revoked_at))}</span>`
            : `<button type="button" class="btn btn-danger btn-sm" data-revoke="${t.id}">${esc(tr('revoke', 'Révoquer'))}</button>`}</td></tr>`).join('');
    return `<div class="api-create">
        <input type="text" id="api-new-name" class="settings-select" maxlength="60" placeholder="${esc(tr('name_ph', 'Nom du jeton (ex. script atelier)'))}">
        <select id="api-new-perm" class="settings-select"><option value="read">${esc(tr('perm_read', 'Lecture seule'))}</option><option value="write">${esc(tr('perm_write', 'Lecture + écriture'))}</option></select>
        <button type="button" class="btn btn-primary btn-sm" id="api-new-btn"><i class="fa-solid fa-plus"></i> ${esc(tr('create', 'Créer le jeton'))}</button></div>
        <div id="api-new-shown"></div>
        ${list.length ? `<table class="api-table"><thead><tr><th>${esc(tr('col_name', 'Jeton'))}</th><th>${esc(tr('col_perm', 'Droit'))}</th><th>${esc(tr('col_created', 'Créé'))}</th><th>${esc(tr('col_used', 'Dernier usage'))}</th><th></th></tr></thead><tbody>${rows}</tbody></table>`
            : `<p class="settings-hint">${esc(tr('none', 'Aucun jeton pour l\'instant.'))}</p>`}`;
}

function renderLog(log) {
    const rows = log.map(x => `<tr class="${x.status >= 400 ? 'api-err' : ''}"><td>${esc(dt(x.ts))}</td><td>${esc(x.token_name || '—')}</td><td><code>${esc(x.method)} ${esc(x.path)}</code></td>
        <td><b>${x.status}</b></td><td>${x.ms} ms</td><td class="v13-muted">${esc(x.error || '')}</td></tr>`).join('');
    return `<h4 style="margin:18px 0 6px;">${esc(tr('log_title', 'Journal des accès'))}</h4>
        <label class="v13-muted"><input type="checkbox" id="api-log-errors" ${errorsOnly ? 'checked' : ''}> ${esc(tr('only_errors', 'Erreurs seulement'))}</label>
        ${log.length ? `<div class="api-log-wrap"><table class="api-table"><tbody>${rows}</tbody></table></div>` : `<p class="settings-hint">${esc(tr('log_none', 'Aucun appel pour l\'instant.'))}</p>`}`;
}

async function create() {
    const name = ($('api-new-name').value || '').trim();
    if (!name) { toast(tr('name_required', 'Donnez un nom au jeton.'), 'error'); return; }
    try {
        const d = await j('/api/tokens', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, perm: $('api-new-perm').value }) });
        await load();
        const shown = $('api-new-shown');
        shown.innerHTML = `<div class="api-shown"><b>${esc(tr('shown_once', 'Copiez ce jeton maintenant : il ne sera plus jamais affiché.'))}</b>
            <div class="api-token-line"><code id="api-token-val">${esc(d.token)}</code> <button type="button" class="btn btn-secondary btn-sm" id="api-copy">${esc(tr('copy', 'Copier'))}</button></div>
            <div class="v13-muted">${esc(tr('usage', 'Utilisation : en-tête Authorization: Bearer <jeton> sur'))} <a href="/api/v1/docs" target="_blank" rel="noopener">/api/v1/docs</a></div></div>`;
        $('api-copy').onclick = async () => { try { await navigator.clipboard.writeText(d.token); toast(tr('copied', 'Copié'), 'success'); } catch (e) { const r = document.createRange(); r.selectNodeContents($('api-token-val')); const s = getSelection(); s.removeAllRanges(); s.addRange(r); } };
    } catch (e) { toast(e.message || tr('error', 'Action impossible'), 'error'); }
}

async function revoke(id) {
    try { await j('/api/tokens/' + id, { method: 'DELETE' }); toast(tr('revoked_ok', 'Jeton révoqué'), 'success'); load(); }
    catch (e) { toast(e.message, 'error'); }
}

document.addEventListener('click', (e) => {
    const t = e.target.closest && e.target.closest('#api-new-btn, [data-revoke]');
    if (!t) return;
    if (t.id === 'api-new-btn') create(); else revoke(Number(t.dataset.revoke));
});

window.StellioApi = { load };
})();
