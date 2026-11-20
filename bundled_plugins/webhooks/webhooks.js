/* Stellio — v1.1.7 : webhooks sortants (Paramètres › Webhooks) — création, test, relances, journal des envois.
   Données : /api/webhooks, /api/webhooks/deliveries (modules/webhooks.py). Dépend de script.js (I18N, escapeHtml, showToast, API). */
(function () {
'use strict';

const $ = (id) => document.getElementById(id);
const tr = (k, fb, p) => {
    let s = (typeof I18N !== 'undefined' && I18N.t) ? I18N.t('wh.' + k) : k;
    if (!s || s === 'wh.' + k) s = fb;
    if (p) Object.keys(p).forEach(n => { s = s.split('{' + n + '}').join(p[n]); });
    return s;
};
const esc = (v) => (typeof escapeHtml === 'function' ? escapeHtml(String(v)) : String(v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
const lang = () => (typeof I18N !== 'undefined' && I18N.lang) || 'fr';
const dt = (ts) => { if (!ts) return '—'; try { return new Date(ts * 1000).toLocaleString(lang(), { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }); } catch (e) { return ''; } };
const toast = (m, t) => { if (typeof showToast === 'function') showToast(m, t || 'info'); };
const evLabel = (e) => tr('ev_' + e.replace('.', '_'), e);
const EV_FALLBACK = { 'print.finished': 'Impression terminée', 'print.failed': 'Impression échouée', 'order.late': 'Commande en retard', 'printer.overload': 'Imprimante surchargée' };

async function j(url, opts) {
    const r = await fetch(`${API}${url}`, Object.assign({ cache: 'no-store' }, opts || {}));
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(d.error || r.status);
    return d;
}
const post = (url, body) => j(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) });

let errorsOnly = false;
let events = [];

async function load() {
    const box = $('wh-box');
    if (!box) return;
    try {
        const [w, l] = await Promise.all([j('/api/webhooks'), j('/api/webhooks/deliveries?limit=60' + (errorsOnly ? '&errors=1' : ''))]);
        events = w.events;
        box.innerHTML = renderForm() + renderList(w.webhooks) + renderLog(l.log);
        const f = $('wh-log-errors'); if (f) f.onchange = () => { errorsOnly = f.checked; load(); };
    } catch (e) {
        box.innerHTML = `<p class="settings-hint">${esc(tr('unavailable', 'Réservé au compte propriétaire.'))}</p>`;
    }
}

function renderForm() {
    const ev = events.map(e => `<label class="wh-ev"><input type="checkbox" value="${e}" checked> ${esc(evLabel(e) === e ? (EV_FALLBACK[e] || e) : evLabel(e))}</label>`).join('');
    return `<div class="api-create"><input type="text" id="wh-new-name" class="settings-select" maxlength="60" placeholder="${esc(tr('name_ph', 'Nom (ex. Discord atelier)'))}">
        <input type="url" id="wh-new-url" class="settings-select" placeholder="https://…"></div>
        <div class="wh-events" id="wh-new-events">${ev}</div>
        <div style="margin:8px 0 12px;"><button type="button" class="btn btn-primary btn-sm" id="wh-new-btn"><i class="fa-solid fa-plus"></i> ${esc(tr('create', 'Ajouter le webhook'))}</button></div>
        <div id="wh-new-shown"></div>`;
}

function statusChip(w) {
    if (!w.active) return `<span class="api-perm">${esc(tr('paused', 'En pause'))}</span>`;
    if (w.last_status == null) return `<span class="v13-muted">${esc(tr('never', 'Jamais utilisé'))}</span>`;
    const ok = w.last_status >= 200 && w.last_status < 300;
    return `<span class="api-perm ${ok ? '' : 'write'}">${ok ? '✓' : '✗'} ${w.last_status || '—'} · ${esc(dt(w.last_at))}</span>`;
}

function renderList(list) {
    if (!list.length) return `<p class="settings-hint">${esc(tr('none', 'Aucun webhook pour l\'instant.'))}</p>`;
    return `<table class="api-table"><thead><tr><th>${esc(tr('col_name', 'Webhook'))}</th><th>${esc(tr('col_events', 'Évènements'))}</th><th>${esc(tr('col_last', 'Dernier envoi'))}</th><th></th></tr></thead><tbody>` +
        list.map(w => `<tr class="${w.active ? '' : 'api-revoked'}"><td><b>${esc(w.name)}</b><div class="v13-muted"><code>${esc(w.url)}</code></div></td>
        <td>${w.events.map(e => `<span class="api-perm">${esc(evLabel(e) === e ? (EV_FALLBACK[e] || e) : evLabel(e))}</span>`).join(' ')}</td>
        <td>${statusChip(w)}</td>
        <td class="wh-actions"><button type="button" class="btn btn-secondary btn-sm" data-wh-test="${w.id}">${esc(tr('test', 'Tester'))}</button>
            <button type="button" class="btn btn-secondary btn-sm" data-wh-toggle="${w.id}" data-active="${w.active ? 1 : 0}">${esc(w.active ? tr('pause', 'Pause') : tr('resume', 'Reprendre'))}</button>
            <button type="button" class="btn btn-secondary btn-sm" data-wh-rotate="${w.id}">${esc(tr('rotate', 'Nouveau secret'))}</button>
            <button type="button" class="btn btn-danger btn-sm" data-wh-del="${w.id}">${esc(tr('delete', 'Supprimer'))}</button></td></tr>
        <tr class="wh-test-row" id="wh-test-${w.id}" hidden><td colspan="4"></td></tr>`).join('') + '</tbody></table>';
}

function stCell(x) {
    const label = { ok: tr('st_ok', 'Envoyé'), pending: tr('st_pending', 'En attente'), failed: tr('st_failed', 'Échec') }[x.status] || x.status;
    const retry = x.status === 'pending' && x.next_try_at ? ` · ${esc(tr('next', 'prochain essai'))} ${esc(dt(x.next_try_at))}` : '';
    return `<b>${esc(label)}</b>${retry}`;
}

function renderLog(log) {
    const rows = log.map(x => `<tr class="${x.status === 'failed' ? 'api-err' : ''}"><td>${esc(dt(x.created_at))}</td><td>${esc(x.webhook_name || '—')}</td>
        <td>${esc(evLabel(x.event) === x.event ? (EV_FALLBACK[x.event] || x.event) : evLabel(x.event))}</td><td>${stCell(x)}</td>
        <td>${x.response_code || '—'} <span class="v13-muted">${x.attempts}×</span></td><td class="v13-muted">${esc(x.error || '')}</td>
        <td>${x.status !== 'ok' ? `<button type="button" class="btn btn-secondary btn-sm" data-wh-retry="${x.id}">${esc(tr('retry', 'Renvoyer'))}</button>` : ''}</td></tr>`).join('');
    return `<h4 style="margin:18px 0 6px;">${esc(tr('log_title', 'Journal des envois'))}</h4>
        <label class="v13-muted"><input type="checkbox" id="wh-log-errors" ${errorsOnly ? 'checked' : ''}> ${esc(tr('only_errors', 'Problèmes seulement'))}</label>
        ${log.length ? `<div class="api-log-wrap"><table class="api-table"><tbody>${rows}</tbody></table></div>` : `<p class="settings-hint">${esc(tr('log_none', 'Aucun envoi pour l\'instant.'))}</p>`}
        <p class="settings-hint" style="margin-top:10px;">${esc(tr('verify_hint', 'Chaque envoi est signé (en-tête X-Stellio-Signature, HMAC-SHA256). Exemple de vérification :'))} <a href="/api/v1/docs#webhooks" target="_blank" rel="noopener">/api/v1/docs</a></p>`;
}

function shownSecret(secret) {
    const el = $('wh-new-shown');
    el.innerHTML = `<div class="api-shown"><b>${esc(tr('secret_once', 'Copiez ce secret maintenant : il ne sera plus affiché (vous pourrez en générer un nouveau).'))}</b>
        <div class="api-token-line"><code id="wh-secret-val">${esc(secret)}</code> <button type="button" class="btn btn-secondary btn-sm" id="wh-copy">${esc(tr('copy', 'Copier'))}</button></div></div>`;
    $('wh-copy').onclick = async () => { try { await navigator.clipboard.writeText(secret); toast(tr('copied', 'Copié'), 'success'); } catch (e) { const r = document.createRange(); r.selectNodeContents($('wh-secret-val')); const s = getSelection(); s.removeAllRanges(); s.addRange(r); } };
}

async function create() {
    const name = ($('wh-new-name').value || '').trim();
    const url = ($('wh-new-url').value || '').trim();
    const evs = Array.from(document.querySelectorAll('#wh-new-events input:checked')).map(i => i.value);
    if (!name || !url) { toast(tr('fill', 'Renseignez un nom et une URL.'), 'error'); return; }
    try {
        const d = await post('/api/webhooks', { name, url, events: evs });
        await load();
        shownSecret(d.secret);
    } catch (e) { toast(e.message || tr('error', 'Action impossible'), 'error'); }
}

async function test(id) {
    const row = $('wh-test-' + id); if (!row) return;
    row.hidden = false; row.firstElementChild.innerHTML = '…';
    try {
        const r = await post(`/api/webhooks/${id}/test`);
        row.firstElementChild.innerHTML = r.ok
            ? `<span class="api-perm">✓ ${esc(tr('test_ok', 'Test reçu par votre serveur'))} (HTTP ${r.code})</span>`
            : `<span class="api-perm write">✗ ${esc(tr('test_ko', 'Test échoué'))} : ${esc(r.error || r.code || '')}</span>`;
        load2();
    } catch (e) { row.firstElementChild.innerHTML = esc(e.message); }
}
// recharge le journal sans effacer le résultat du test affiché
async function load2() {
    try {
        const l = await j('/api/webhooks/deliveries?limit=60' + (errorsOnly ? '&errors=1' : ''));
        const old = document.querySelector('#wh-box .api-log-wrap');
        if (old) old.querySelector('tbody').innerHTML = renderLog(l.log).match(/<tbody>([\s\S]*?)<\/tbody>/)?.[1] || '';
    } catch (e) { /* ignoré */ }
}

document.addEventListener('click', async (e) => {
    const t = e.target.closest && e.target.closest('#wh-new-btn, [data-wh-test], [data-wh-toggle], [data-wh-rotate], [data-wh-del], [data-wh-retry]');
    if (!t) return;
    try {
        if (t.id === 'wh-new-btn') return create();
        if (t.dataset.whTest) return test(t.dataset.whTest);
        if (t.dataset.whToggle) { await j('/api/webhooks/' + t.dataset.whToggle, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ active: t.dataset.active !== '1' }) }); return load(); }
        if (t.dataset.whRotate) { const r = await post(`/api/webhooks/${t.dataset.whRotate}/rotate-secret`); await load(); return shownSecret(r.secret); }
        if (t.dataset.whDel) { await j('/api/webhooks/' + t.dataset.whDel, { method: 'DELETE' }); toast(tr('deleted', 'Webhook supprimé'), 'success'); return load(); }
        if (t.dataset.whRetry) { await post(`/api/webhooks/deliveries/${t.dataset.whRetry}/retry`); toast(tr('queued', 'Renvoi programmé'), 'success'); setTimeout(load, 1500); }
    } catch (err) { toast(err.message || tr('error', 'Action impossible'), 'error'); }
});

window.StellioWebhooks = { load };
})();
