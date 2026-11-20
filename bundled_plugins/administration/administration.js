/* Stellio — v1.1.7 : plugin Administration — page unique (Comptes, Équipes, Sessions, Audit, Instances) et supervision d'instances.
   Données : /api/admin/* (admin_console.py) + les routes existantes d'équipes, de sessions, d'audit et d'invités. Dépend de suite.js (StellioSuite.registerTab). */
(function () {
'use strict';
const S = window.StellioSuite;
if (!S || !S.registerTab) return;
const $ = (id) => document.getElementById(id);
const tr = (k, fb, p) => {
    let s = (typeof I18N !== 'undefined' && I18N.t) ? I18N.t('suite.adm_' + k) : '';
    if (!s || s === 'suite.adm_' + k) s = fb;
    if (p) Object.keys(p).forEach(n => { s = s.split('{' + n + '}').join(p[n]); });
    return s;
};
const esc = (v) => (typeof escapeHtml === 'function' ? escapeHtml(String(v)) : String(v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
async function api(url, body, method) {
    const opt = body !== undefined ? { method: method || 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : { cache: 'no-store' };
    if (body === undefined && method) opt.method = method;
    const r = await fetch(`${API}${url}`, opt);
    const d = await r.json().catch(() => ({}));
    if (!r.ok) { const e = new Error(d.error || r.status); e.data = d; throw e; }
    return d;
}
const SUBS = ['accounts', 'teams', 'sessions', 'audit', 'instances'];
const SUB_FB = { accounts: 'Comptes', teams: 'Équipes', sessions: 'Sessions', audit: 'Journal d\'audit', instances: 'Instances' };
const ROLE_FB = { '': 'Invité (lecture seule)', user: 'Utilisateur simple', operator: 'Opérateur', manager: 'Gestionnaire', admin: 'Administrateur' };
const roleLabel = (r) => tr('role_' + (r || 'guest'), ROLE_FB[r || ''] || r);
const roleSelect = (roles, cur, attrs, off) => `<select class="settings-select" ${attrs}${off ? ' disabled' : ''}>${['', ...roles].map(r => `<option value="${esc(r)}"${r === (cur || '') ? ' selected' : ''}>${esc(roleLabel(r))}</option>`).join('')}</select>`;
const msg = (box, text, bad) => { let p = box.querySelector('.adm-msg'); if (!p) { p = Object.assign(document.createElement('p'), { className: 'adm-msg settings-hint' }); box.insertAdjacentElement('afterbegin', p); } p.textContent = text; p.style.color = bad ? 'var(--danger, #e5484d)' : ''; };
const badge = (t, c) => `<span class="adm-badge" style="padding:2px 8px;border-radius:10px;font-size:.8em;background:var(--bg-hover);color:${c || 'inherit'}">${esc(t)}</span>`;
let sub = 'accounts', ov = null, managed = 0;
const refreshNav = () => { try { S._applyHostFeatures(); } catch (e) { /* facultatif */ } };

function banner(o) {
    if (o.request) {
        return `<div class="suite-card adm-req" style="border:1px solid var(--warning,#d99a00);border-radius:8px;padding:12px;margin-bottom:12px"><b>${esc(tr('req_title', 'L\'instance « {name} » demande à superviser celle-ci.', { name: o.request.name }))}</b>` +
            `<p class="settings-hint">${esc(tr('req_hint', 'Si vous acceptez, les comptes invités, leurs rôles et leurs permissions ne se géreront plus que depuis cette instance. Vous pourrez quitter la supervision à tout moment.'))}</p>` +
            `<label class="settings-hint"><input type="checkbox" id="adm-keep"${o.request.keep_local ? ' checked' : ''}> ${esc(tr('keep_local', 'Garder le contenu local (bibliothèque, imprimantes) : l\'instance principale n\'en voit rien'))}</label><div class="su-line" style="margin-top:8px">` +
            `<button type="button" class="btn btn-primary btn-sm" data-adm="accept">${esc(tr('accept', 'Accepter'))}</button> <button type="button" class="btn btn-ghost btn-sm" data-adm="refuse">${esc(tr('refuse', 'Refuser'))}</button></div></div>`;
    }
    if (o.role === 'supervised') {
        return `<div class="suite-card" style="border:1px solid var(--accent);border-radius:8px;padding:12px;margin-bottom:12px">${badge(tr('role_supervised', 'Instance supervisée'))} ` +
            `<span class="settings-hint">${esc(tr('locked', 'Comptes et rôles gérés par l\'instance principale « {name} ».', { name: o.supervisor.name }))} ${esc(o.supervisor.keep_local ? tr('local_kept', 'Le contenu local reste privé.') : tr('local_shared', 'Les totaux de contenu sont visibles de l\'instance principale.'))}</span> ` +
            `<button type="button" class="btn btn-ghost btn-sm" data-adm="leave">${esc(tr('leave', 'Quitter la supervision'))}</button></div>`;
    }
    if (o.role === 'primary') return `<p class="settings-hint">${badge(tr('role_primary', 'Instance principale'))} ${esc(tr('primary_hint', 'Cette instance administre les instances supervisées listées dans l\'onglet Instances.'))}</p>`;
    return `<p class="settings-hint">${badge(tr('role_standalone', 'Instance autonome'))} ${esc(tr('standalone_hint', 'Contrôle total. Appairez une autre instance (Partage & synchro) pour la superviser depuis ici.'))}</p>`;
}

async function accounts(box) {
    const d = await api('/api/admin/accounts');
    const off = d.locked;
    box.innerHTML = (off ? `<p class="settings-hint">${esc(tr('locked', 'Comptes et rôles gérés par l\'instance principale « {name} ».', { name: d.supervisor }))}</p>` : '') +
        `<p class="settings-hint">${esc(tr('owner', 'Propriétaire'))} : <b>${esc(d.owner ? d.owner.username : '—')}</b></p>` +
        (d.guests.length ? `<div class="suite-scroll"><table class="suite-table"><thead><tr><th>${esc(tr('guest', 'Invité'))}</th><th>${esc(tr('role', 'Rôle'))}</th><th></th></tr></thead><tbody>${d.guests.map(g =>
            `<tr><td>${esc(g.username)}</td><td>${roleSelect(d.roles, g.team_role, `data-role="${g.id}"`, off)}</td><td><button type="button" class="btn btn-ghost btn-sm" data-del="${g.id}"${off ? ' disabled' : ''}>${esc(tr('delete', 'Supprimer'))}</button></td></tr>`).join('')}</tbody></table></div>` :
            `<p class="settings-hint">${esc(tr('no_guests', 'Aucun compte invité.'))}</p>`) +
        `<h4>${esc(tr('add_guest', 'Ajouter un compte invité'))}</h4><div class="su-line"><input id="adm-u" class="settings-select" placeholder="${esc(tr('username', 'Nom'))}" autocomplete="off"${off ? ' disabled' : ''}>` +
        `<input id="adm-p" type="password" class="settings-select" placeholder="${esc(tr('password', 'Mot de passe'))}" autocomplete="new-password"${off ? ' disabled' : ''}>${roleSelect(d.roles, '', 'id="adm-r"', off)}` +
        `<button type="button" class="btn btn-primary btn-sm" id="adm-add"${off ? ' disabled' : ''}>${esc(tr('create', 'Créer'))}</button></div>`;
    box.onchange = async (e) => { const s = e.target.closest('[data-role]'); if (!s) return; try { await api(`/api/team/members/${s.dataset.role}/role`, { role: s.value }, 'PUT'); msg(box, '✓'); } catch (x) { msg(box, x.message, true); } };
    box.onclick = async (e) => {
        const del = e.target.closest('[data-del]');
        try {
            if (del && await confirmDlg(tr('del_confirm', 'Supprimer ce compte invité ?'))) { await api(`/api/auth/guests/${del.dataset.del}`, undefined, 'DELETE'); await accounts(box); }
            if (e.target.closest('#adm-add')) { const c = await api('/api/auth/guests', { username: $('adm-u').value.trim(), password: $('adm-p').value }); const role = $('adm-r').value; if (role && c.id) await api(`/api/team/members/${c.id}/role`, { role }, 'PUT'); await accounts(box); }
        } catch (x) { msg(box, x.message, true); }
    };
}
const confirmDlg = (m) => (typeof showConfirmDialog === 'function') ? showConfirmDialog(m, {}) : Promise.resolve(window.confirm(m));

async function instances(box) {
    ov = await api('/api/admin/overview');
    // met à jour l'état des liens en attente / actifs (acceptation, départ) avant l'affichage
    const live = ov.instances.filter(i => i.supervision !== 'none');
    if (live.length) {
        const rs = await Promise.allSettled(live.map(i => api(`/api/admin/instances/${i.id}/status`)));
        if (rs.some((r, k) => r.status === 'fulfilled' && ((r.value.released) || (r.value.state === 'supervised' && live[k].supervision !== 'supervised')))) ov = await api('/api/admin/overview');
    }
    const blocked = ov.role === 'supervised';
    box.innerHTML = `<p class="settings-hint">${esc(tr('instances_hint', 'Instances Stellio appairées. Une instance supervisée accepte que ses comptes et rôles soient gérés ici ; une instance non supervisée reste autonome.'))}</p>` +
        (blocked ? `<p class="settings-hint">${esc(tr('is_supervised', 'Cette instance est supervisée : elle ne peut pas en superviser d\'autres.'))}</p>` :
         `<label class="settings-hint"><input type="checkbox" id="adm-keepnew" checked> ${esc(tr('keep_local_ask', 'Demander à garder le contenu local sur les instances supervisées'))}</label>`) +
        (ov.instances.length ? `<div class="suite-scroll"><table class="suite-table"><thead><tr><th>${esc(tr('instance', 'Instance'))}</th><th>${esc(tr('state', 'État'))}</th><th>${esc(tr('supervision', 'Supervision'))}</th><th></th></tr></thead><tbody>${ov.instances.map(i => {
            const sv = i.supervision === 'supervised' ? badge(tr('supervised', 'Supervisée'), 'var(--success,#2e9e5b)') : i.supervision === 'pending' ? badge(tr('pending', 'En attente d\'acceptation'), 'var(--warning,#d99a00)') : badge(tr('standalone', 'Autonome'));
            const act = i.supervision === 'supervised' ? `<button type="button" class="btn btn-secondary btn-sm" data-manage="${i.id}">${esc(tr('manage', 'Gérer'))}</button> <button type="button" class="btn btn-ghost btn-sm" data-release="${i.id}">${esc(tr('release', 'Libérer'))}</button>` :
                i.supervision === 'pending' ? `<button type="button" class="btn btn-ghost btn-sm" data-release="${i.id}">${esc(tr('cancel', 'Annuler'))}</button>` :
                `<button type="button" class="btn btn-primary btn-sm" data-sup="${i.id}"${blocked ? ' disabled' : ''}>${esc(tr('supervise', 'Superviser'))}</button>`;
            return `<tr><td>${esc(i.name)}<br><small class="settings-hint">${esc(i.url)}</small></td><td>${esc(i.last_status || '—')}</td><td>${sv}</td><td>${act}</td></tr>`;
        }).join('')}</tbody></table></div>` : `<p class="settings-hint">${esc(tr('no_instances', 'Aucune instance appairée. Ajoutez-en une dans Partage & synchro.'))}</p>`) + '<div id="adm-manage"></div>';
    box.onclick = async (e) => {
        const b = e.target.closest('[data-sup],[data-release],[data-manage]'); if (!b) return;
        try {
            if (b.dataset.sup) { await api(`/api/admin/instances/${b.dataset.sup}/supervise`, { keep_local: $('adm-keepnew') ? $('adm-keepnew').checked : true }); refreshNav(); await instances(box); msg(box, tr('sent', 'Demande envoyée : elle doit être acceptée sur l\'autre instance.')); }
            else if (b.dataset.release) { if (await confirmDlg(tr('release_confirm', 'Mettre fin à la supervision de cette instance ?'))) { await api(`/api/admin/instances/${b.dataset.release}/release`, {}); await instances(box); } }
            else { managed = Number(b.dataset.manage); await manage(box); }
        } catch (x) { msg(box, x.message, true); }
    };
    if (managed && ov.instances.some(i => i.id === managed && i.supervision === 'supervised')) manage(box);
    watchPending(box);
}

/* Demandes en attente : on interroge l'état tant que la liste est affichée (toutes les 4 s et au retour sur la fenêtre), et on rafraîchit dès qu'une instance accepte ou refuse. */
let pendTimer = null, pendBox = null, pendIds = [];
async function pollPending() {
    const box = pendBox;
    if (!box || !box.isConnected || $('adm-sub') !== box) return;
    clearTimeout(pendTimer);
    const pend = pendIds.map(id => ({ id }));
    if (!pend.length) return;
    let changed = false;
    try {
        const rs = await Promise.allSettled(pend.map(i => api(`/api/admin/instances/${i.id}/status`)));
        rs.forEach(r => { if (r.status === 'fulfilled' && (r.value.state === 'supervised' || r.value.state === 'none' || r.value.released)) changed = true; });
        if (!changed) { const o = await api('/api/admin/overview'); changed = o.instances.some(i => pend.some(p => p.id === i.id && i.supervision !== 'pending')); }
    } catch (e) { /* réessai au prochain tour */ }
    if (pendBox !== box || !box.isConnected) return;
    if (changed) { refreshNav(); await instances(box); } else pendTimer = setTimeout(pollPending, 4000);
}
function watchPending(box) {
    clearTimeout(pendTimer); pendBox = box;
    pendIds = (ov.instances || []).filter(i => i.supervision === 'pending').map(i => i.id);
    if (pendIds.length) pendTimer = setTimeout(pollPending, 4000);
}
window.addEventListener('focus', () => { if (pendBox) pollPending(); });

async function manage(box) {
    const host = $('adm-manage'); if (!host) return;
    host.innerHTML = '<p class="settings-hint">…</p>';
    const d = await api(`/api/admin/instances/${managed}/status`);
    if (!d.online && d.online !== undefined) { host.innerHTML = `<p class="settings-hint">${esc(tr('offline', 'Instance injoignable.'))}</p>`; return; }
    const inst = ov.instances.find(i => i.id === managed);
    const cmd = (op, args) => api(`/api/admin/instances/${managed}/command`, { op, args });
    host.innerHTML = `<h4>${esc(tr('manage_title', 'Comptes de « {name} »', { name: inst ? inst.name : '' }))}</h4>` +
        (d.content ? `<p class="settings-hint">${esc(tr('content_totals', 'Contenu'))} : ${esc(JSON.stringify(d.content))}</p>` : `<p class="settings-hint">${esc(tr('local_kept', 'Le contenu local reste privé.'))}</p>`) +
        (d.guests.length ? `<div class="suite-scroll"><table class="suite-table"><thead><tr><th>${esc(tr('guest', 'Invité'))}</th><th>${esc(tr('role', 'Rôle'))}</th><th></th></tr></thead><tbody>${d.guests.map(g =>
            `<tr><td>${esc(g.username)}</td><td>${roleSelect(d.roles, g.team_role, `data-rrole="${g.id}"`)}</td><td><button type="button" class="btn btn-ghost btn-sm" data-rdel="${g.id}">${esc(tr('delete', 'Supprimer'))}</button></td></tr>`).join('')}</tbody></table></div>` : `<p class="settings-hint">${esc(tr('no_guests', 'Aucun compte invité.'))}</p>`) +
        `<div class="su-line"><input id="adm-ru" class="settings-select" placeholder="${esc(tr('username', 'Nom'))}" autocomplete="off"><input id="adm-rp" type="password" class="settings-select" placeholder="${esc(tr('password', 'Mot de passe'))}" autocomplete="new-password">${roleSelect(d.roles, '', 'id="adm-rr"')}<button type="button" class="btn btn-primary btn-sm" id="adm-radd">${esc(tr('create', 'Créer'))}</button></div>`;
    host.onchange = async (e) => { const s = e.target.closest('[data-rrole]'); if (!s) return; try { await cmd('guest_role', { id: Number(s.dataset.rrole), role: s.value }); msg(host, '✓'); } catch (x) { msg(host, x.message, true); } };
    host.onclick = async (e) => {
        try {
            const del = e.target.closest('[data-rdel]');
            if (del && await confirmDlg(tr('del_confirm', 'Supprimer ce compte invité ?'))) { await cmd('guest_delete', { id: Number(del.dataset.rdel) }); await manage(box); }
            if (e.target.closest('#adm-radd')) { await cmd('guest_create', { username: $('adm-ru').value.trim(), password: $('adm-rp').value, role: $('adm-rr').value }); await manage(box); }
        } catch (x) { msg(host, x.message, true); }
    };
}

/* Équipes (espaces de travail) : création, suppression, ajout et retrait de comptes invités avec leur rôle dans l'équipe. */
async function teams(box) {
    const d = await api('/api/team');
    const off = ov && ov.role === 'supervised';
    const name = (id) => { const m = d.members.find(x => x.id === id); return m ? m.username : '#' + id; };
    const rsel = (cur, attrs) => `<select class="settings-select" ${attrs}${off ? ' disabled' : ''}>${d.roles.map(r => `<option value="${esc(r)}"${r === cur ? ' selected' : ''}>${esc(roleLabel(r))}</option>`).join('')}</select>`;
    box.innerHTML = (off ? `<p class="settings-hint">${esc(tr('locked', 'Comptes et rôles gérés par l\'instance principale « {name} ».', { name: (ov.supervisor || {}).name || '' }))}</p>` : '') +
        `<p class="settings-hint">${esc(tr('teams_hint', 'Une équipe regroupe des comptes invités ; chaque membre y a un rôle.'))}</p>` +
        (d.workspaces.length ? d.workspaces.map(w => {
            const free = d.members.filter(m => !w.members.some(x => x.user_id === m.id));
            return `<div class="suite-card adm-team" data-ws="${w.id}" style="border:1px solid var(--border);border-radius:8px;padding:12px;margin-bottom:12px">` +
                `<div class="su-line" style="justify-content:space-between"><b>${esc(w.name)}</b><button type="button" class="btn btn-ghost btn-sm" data-wdel="${w.id}"${off ? ' disabled' : ''}>${esc(tr('team_delete', 'Supprimer l\'équipe'))}</button></div>` +
                (w.members.length ? `<div class="suite-scroll"><table class="suite-table"><thead><tr><th>${esc(tr('guest', 'Invité'))}</th><th>${esc(tr('role', 'Rôle'))}</th><th></th></tr></thead><tbody>${w.members.map(m =>
                    `<tr><td>${esc(name(m.user_id))}</td><td>${rsel(m.role, `data-mrole="${w.id}:${m.user_id}"`)}</td><td><button type="button" class="btn btn-ghost btn-sm" data-mdel="${w.id}:${m.user_id}"${off ? ' disabled' : ''}>${esc(tr('team_remove', 'Retirer'))}</button></td></tr>`).join('')}</tbody></table></div>` :
                    `<p class="settings-hint">${esc(tr('team_empty', 'Aucun membre dans cette équipe.'))}</p>`) +
                (free.length ? `<div class="su-line"><select class="settings-select" data-madd-user="${w.id}"${off ? ' disabled' : ''}>${free.map(m => `<option value="${m.id}">${esc(m.username)}</option>`).join('')}</select>${rsel('user', `data-madd-role="${w.id}"`)}` +
                    `<button type="button" class="btn btn-primary btn-sm" data-madd="${w.id}"${off ? ' disabled' : ''}>${esc(tr('team_add', 'Ajouter à l\'équipe'))}</button></div>` :
                    `<p class="settings-hint">${esc(d.members.length ? tr('team_all', 'Tous les comptes invités sont déjà dans cette équipe.') : tr('no_guests', 'Aucun compte invité.'))}</p>`) + '</div>';
        }).join('') : `<p class="settings-hint">${esc(tr('team_none', 'Aucune équipe.'))}</p>`) +
        `<h4>${esc(tr('team_new', 'Nouvelle équipe'))}</h4><div class="su-line"><input id="adm-tn" class="settings-select" placeholder="${esc(tr('team_name', 'Nom de l\'équipe'))}" autocomplete="off"${off ? ' disabled' : ''}>` +
        `<button type="button" class="btn btn-primary btn-sm" id="adm-tadd"${off ? ' disabled' : ''}>${esc(tr('create', 'Créer'))}</button></div>`;
    box.onchange = async (e) => {
        const s = e.target.closest('[data-mrole]'); if (!s) return; const [w, u] = s.dataset.mrole.split(':');
        try { await api(`/api/team/workspaces/${w}/members`, { user_id: Number(u), role: s.value }); msg(box, '✓'); } catch (x) { msg(box, x.message, true); }
    };
    box.onclick = async (e) => {
        try {
            const add = e.target.closest('[data-madd]'), rm = e.target.closest('[data-mdel]'), del = e.target.closest('[data-wdel]');
            if (add) { const w = add.dataset.madd; await api(`/api/team/workspaces/${w}/members`, { user_id: Number(box.querySelector(`[data-madd-user="${w}"]`).value), role: box.querySelector(`[data-madd-role="${w}"]`).value }); await teams(box); }
            else if (rm) { const [w, u] = rm.dataset.mdel.split(':'); await api(`/api/team/workspaces/${w}/members/${u}`, undefined, 'DELETE'); await teams(box); }
            else if (del) { if (await confirmDlg(tr('team_delete_confirm', 'Supprimer cette équipe ?'))) { await api(`/api/team/workspaces/${del.dataset.wdel}`, undefined, 'DELETE'); await teams(box); } }
            else if (e.target.closest('#adm-tadd')) { const n = $('adm-tn').value.trim(); if (!n) return; await api('/api/team/workspaces', { name: n }); await teams(box); }
        } catch (x) { msg(box, x.message, true); }
    };
}

async function render(box) {
    ov = await api('/api/admin/overview');
    box.innerHTML = '<div id="adm-banner"></div><div class="su-line adm-subs" id="adm-subs" role="tablist"></div><div id="adm-sub"></div>';
    const paint = async () => {
        try { ov = await api('/api/admin/overview'); } catch (e) { /* on garde l'état précédent */ }
        $('adm-banner').innerHTML = banner(ov);
        $('adm-subs').innerHTML = SUBS.map(k => `<button type="button" role="tab" class="btn ${k === sub ? 'btn-primary' : 'btn-ghost'} btn-sm" data-sub="${k}">${esc(tr('sub_' + k, SUB_FB[k]))}</button>`).join(' ');
        const inner = $('adm-sub'); inner.innerHTML = '<p class="settings-hint">…</p>';
        const T = S._tabs || {};
        try {
            if (sub === 'accounts') await accounts(inner);
            else if (sub === 'instances') await instances(inner);
            else if (sub === 'teams') await teams(inner);
            else if (T[{ teams: 'team', sessions: 'sessions', audit: 'audit' }[sub]]) await T[{ teams: 'team', sessions: 'sessions', audit: 'audit' }[sub]].render(inner);
        } catch (e) { inner.innerHTML = `<p class="settings-hint">${esc(e.message || '')}</p>`; }
    };
    box.addEventListener('click', async (e) => {
        const s = e.target.closest('[data-sub]'); if (s) { sub = s.dataset.sub; return paint(); }
        const a = e.target.closest('[data-adm]'); if (!a) return;
        try {
            if (a.dataset.adm === 'leave') { if (!await confirmDlg(tr('leave_confirm', 'Quitter la supervision ? Les comptes et rôles seront de nouveau gérés ici.'))) return; await api('/api/admin/supervision/leave', {}); }
            else await api('/api/admin/supervision/respond', { accept: a.dataset.adm === 'accept', keep_local: $('adm-keep') ? $('adm-keep').checked : true });
            ov = await api('/api/admin/overview'); refreshNav(); await paint();
        } catch (x) { msg(box, x.message, true); }
    });
    await paint();
}
S.registerTab('admin', { fb: 'Administration', icon: 'user-shield', render });

/* Demande de supervision reçue : fenêtre Accepter / Refuser affichée dès l'arrivée de la demande, sans passer par l'onglet. */
let popupOpen = false;
function requestPopup(rq) {
    if (popupOpen || $('adm-req-popup')) return;
    popupOpen = true;
    const overlay = document.createElement('div');
    overlay.id = 'adm-req-popup';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.75);display:flex;align-items:center;justify-content:center;z-index:100001;backdrop-filter:blur(5px)';
    overlay.innerHTML = `<div style="background:var(--bg-secondary);color:var(--text-primary);padding:28px;border-radius:14px;max-width:460px;width:90%;box-shadow:0 12px 35px rgba(0,0,0,.6);border:1px solid var(--border);text-align:center">` +
        `<h3 style="margin:0 0 10px;font-weight:600"><i class="fa-solid fa-user-shield" style="color:var(--accent,#4f8cff)"></i> ${esc(tr('req_popup_title', 'Demande de couplage'))}</h3>` +
        `<p style="margin:0 0 10px;line-height:1.5"><b>${esc(rq.name || '')}</b><br>${esc(tr('req_popup_text', 'souhaite superviser cette instance.'))}</p>` +
        `<p style="color:var(--text-muted);margin:0 0 14px;line-height:1.5;font-size:.9em">${esc(tr('req_hint', 'Si vous acceptez, les comptes invités, leurs rôles et leurs permissions ne se géreront plus que depuis cette instance. Vous pourrez quitter la supervision à tout moment.'))}</p>` +
        `<label style="display:flex;gap:8px;align-items:flex-start;text-align:left;color:var(--text-muted);font-size:.9em;margin:0 0 20px"><input type="checkbox" id="adm-pop-keep"${rq.keep_local ? ' checked' : ''}> <span>${esc(tr('keep_local', 'Garder le contenu local (bibliothèque, imprimantes) : l\'instance principale n\'en voit rien'))}</span></label>` +
        `<p id="adm-pop-err" style="color:var(--danger,#e5484d);margin:0 0 10px;display:none"></p>` +
        `<div style="display:flex;gap:10px;justify-content:center"><button type="button" class="btn btn-ghost" data-pop="refuse">${esc(tr('refuse', 'Refuser'))}</button><button type="button" class="btn btn-primary" data-pop="accept">${esc(tr('accept', 'Accepter'))}</button></div></div>`;
    document.body.appendChild(overlay);
    overlay.querySelector('[data-pop="accept"]').focus();
    overlay.addEventListener('click', async (e) => {
        const b = e.target.closest('[data-pop]'); if (!b) return;
        overlay.querySelectorAll('button').forEach(x => { x.disabled = true; });
        try {
            await api('/api/admin/supervision/respond', { accept: b.dataset.pop === 'accept', keep_local: $('adm-pop-keep') ? $('adm-pop-keep').checked : true });
            overlay.remove(); popupOpen = false; refreshNav();
            if (typeof showToast === 'function') showToast(b.dataset.pop === 'accept' ? tr('accepted', 'Supervision acceptée') : tr('refused', 'Demande refusée'), 'success');        } catch (x) {
            overlay.querySelectorAll('button').forEach(y => { y.disabled = false; });
            const er = $('adm-pop-err'); if (er) { er.textContent = x.message; er.style.display = ''; }
        }
    });
}
async function checkRequest() {
    if (popupOpen) return;
    try {
        const o = await api('/api/admin/overview');
        if (o && o.request) requestPopup(o.request);
    } catch (e) { /* pas connecté, pas propriétaire ou plugin inactif : rien à afficher */ }
}
setTimeout(checkRequest, 1500);
setInterval(checkRequest, 20000);
window.addEventListener('focus', checkRequest);
})();
