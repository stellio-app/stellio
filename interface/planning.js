/* Stellio — v1.1.5 : page « Planning » (Impression).
   Fin estimée par imprimante, capacité contre charge, alertes de surcharge / retard prévisible, respect des délais.
   Données : GET /api/planning (calcul serveur, modules/production_planning.py). Dépend de script.js (I18N, openModal, closeModal, showToast, escapeHtml, API). */
(function () {
'use strict';

const $ = (id) => document.getElementById(id);
const tr = (k, fb, p) => {
    let s = (typeof I18N !== 'undefined' && I18N.t) ? I18N.t(k) : k;
    if (!s || s === k) s = fb;
    if (p) Object.keys(p).forEach(n => { s = s.split('{' + n + '}').join(p[n]); });
    return s;
};
const T = (k, fb, p) => tr('planning.' + k, fb, p);
const esc = (v) => (typeof escapeHtml === 'function' ? escapeHtml(String(v)) : String(v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
const lang = () => (typeof I18N !== 'undefined' && I18N.lang) || 'fr';

let data = null;
let wired = false;
const hFmt = (h) => (Math.round((h || 0) * 10) / 10).toLocaleString(lang());
const dFmt = (iso, opts) => { try { return new Date(iso + 'T12:00:00').toLocaleDateString(lang(), opts || { day: 'numeric', month: 'short' }); } catch (e) { return iso; } };

async function load() {
    const h = $('pl-horizon') ? $('pl-horizon').value : '14';
    try {
        const r = await fetch(`${API}/api/planning?horizon=${encodeURIComponent(h)}`, { cache: 'no-store' });
        data = await r.json();
        if (!r.ok) throw new Error(data.error || r.status);
    } catch (e) {
        data = null;
        $('pl-kpis').innerHTML = `<div class="pl-empty">${esc(T('load_error', 'Planning indisponible pour le moment.'))}</div>`;
        $('pl-alerts').innerHTML = $('pl-gantt').innerHTML = $('pl-table').innerHTML = '';
        return;
    }
    render();
}

function kpi(label, value, cls, sub) {
    return `<div class="pl-kpi ${cls || ''}"><div class="pl-kpi-v">${value}</div><div class="pl-kpi-l">${esc(label)}</div>${sub ? `<div class="pl-kpi-s">${esc(sub)}</div>` : ''}</div>`;
}

function renderKpis() {
    const s = data.summary, ot = data.on_time || {};
    const load = s.load_pct;
    const loadCls = load == null ? '' : (load > 100 ? 'bad' : (load > 80 ? 'warn' : 'ok'));
    $('pl-kpis').innerHTML =
        kpi(T('kpi_capacity', 'Capacité disponible'), hFmt(s.capacity_hours) + ' h', '', T('kpi_capacity_sub', 'sur {d} jours', { d: data.horizon_days })) +
        kpi(T('kpi_load', 'Charge demandée'), hFmt(s.demand_hours) + ' h', '', T('kpi_free', '{h} h libres', { h: hFmt(s.free_hours) })) +
        kpi(T('kpi_rate', 'Taux de charge'), load == null ? '—' : Math.round(load) + ' %', loadCls) +
        kpi(T('kpi_late', 'Retards prévus'), String(s.late_predicted + s.overdue), (s.late_predicted + s.overdue) ? 'bad' : 'ok') +
        kpi(T('kpi_ontime', 'Respect des délais'), ot.rate == null ? '—' : Math.round(ot.rate) + ' %', ot.rate == null ? '' : (ot.rate >= 90 ? 'ok' : (ot.rate >= 70 ? 'warn' : 'bad')),
            ot.total ? T('kpi_ontime_sub', '{n} commandes sur 90 jours', { n: ot.total }) : T('kpi_ontime_none', 'pas encore de données'));
}

function renderAlerts() {
    const rows = [];
    data.alerts.forEach(a => {
        if (a.type === 'overload') rows.push(['bad', 'fa-triangle-exclamation', T('alert_overload', '{p} : {h} h à imprimer pour {c} h disponibles ({pct} %).', { p: a.printer_name, h: hFmt(a.hours), c: hFmt(a.capacity), pct: Math.round(a.load_pct) })]);
        else if (a.type === 'late_predicted') rows.push(['bad', 'fa-clock', T('alert_late', '« {part} » : fin estimée le {end}, livraison prévue le {due}.', { part: a.part, end: dFmt(a.end), due: dFmt(a.due_date) })]);
        else if (a.type === 'overdue') rows.push(['bad', 'fa-bell', T('alert_overdue', '« {part} » : la date de livraison ({due}) est dépassée.', { part: a.part, due: dFmt(a.due_date) })]);
        else if (a.type === 'no_printer') rows.push(['warn', 'fa-print', T('alert_no_printer', 'Aucune imprimante active : ajoutez-en une ou réactivez-en une dans « Capacité des imprimantes ».')]);
    });
    let html = rows.map(r => `<div class="pl-alert ${r[0]}"><i class="fa-solid ${r[1]}"></i><span>${esc(String(r[2]).replace(/\.\.$/, '.'))}</span></div>`).join('');
    if (data.no_duration.length) {
        html += `<div class="pl-alert warn"><i class="fa-solid fa-hourglass-half"></i><div style="flex:1;min-width:0;">
            <div>${esc(T('alert_no_duration', '{n} commande(s) sans durée par pièce : elles ne sont pas planifiées.', { n: data.no_duration.length }))}</div>
            <div class="pl-noduration">${data.no_duration.map(j => `<label class="pl-nd-row"><span>${esc(j.part)}${j.client ? ' · ' + esc(j.client) : ''}</span>
                <input type="number" min="0" step="0.25" class="settings-select" placeholder="h" data-job="${j.id}" title="${esc(T('hours_piece', 'Durée par pièce (heures)'))}"></label>`).join('')}
            </div></div></div>`;
    }
    $('pl-alerts').innerHTML = html;
    $('pl-alerts').querySelectorAll('input[data-job]').forEach(inp => inp.addEventListener('change', async () => {
        const v = parseFloat(inp.value);
        if (!(v > 0)) return;
        const r = await fetch(`${API}/api/orders/${inp.dataset.job}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ est_hours: v }) });
        if (r.ok) load(); else showToast(T('save_error', 'Enregistrement impossible'), 'error');
    }));
}

function jobClass(j) {
    if (j.late_predicted || j.overdue) return 'late';
    if (j.slack_days != null && j.slack_days <= 1) return 'risk';
    return '';
}

function renderGantt() {
    const n = data.horizon_days;
    const start = new Date(data.generated);
    const days = [];
    for (let i = 0; i < n; i++) { const d = new Date(start.getFullYear(), start.getMonth(), start.getDate() + i, 12); days.push(d); }
    const head = days.map(d => {
        const wk = d.getDay() === 0 || d.getDay() === 6;
        return `<div class="pl-day${wk ? ' we' : ''}"><span>${esc(d.toLocaleDateString(lang(), { weekday: 'narrow' }))}</span><b>${d.getDate()}</b></div>`;
    }).join('');
    const jobsBy = {};
    data.jobs.forEach(j => { (jobsBy[j.printer_id] = jobsBy[j.printer_id] || []).push(j); });
    const rows = data.printers.map(p => {
        const bars = (jobsBy[p.id] || []).map(j => {
            if (j.start_pos == null || j.end_pos == null || j.start_pos >= n) return '';
            const left = Math.max(0, j.start_pos) / n * 100;
            const width = Math.max(1.2, (Math.min(n, j.end_pos) - Math.max(0, j.start_pos)) / n * 100);
            const tip = `${j.part}${j.client ? ' · ' + j.client : ''}\n${hFmt(j.hours)} h · ${T('end_label', 'fin')} ${dFmt(j.end)}${j.due_date ? ' · ' + T('due_label', 'livraison') + ' ' + dFmt(j.due_date) : ''}${j.virtual ? '\n' + T('virtual', 'placée automatiquement (aucune imprimante choisie)') : ''}`;
            return `<div class="pl-bar ${jobClass(j)}${j.virtual ? ' virtual' : ''}" style="left:${left}%;width:${width}%;" title="${esc(tip)}"><span>${esc(j.part)}</span></div>`;
        }).join('');
        const loadTxt = p.load_pct == null ? '' : `${Math.round(p.load_pct)} %`;
        const cls = p.load_pct != null && p.load_pct > 100 ? 'bad' : (p.load_pct > 80 ? 'warn' : 'ok');
        const free = !p.enabled ? T('disabled', 'désactivée') : (p.queue_hours > 0 ? T('free_from', 'libre à partir du {d}', { d: dFmt(p.free_from) }) : T('free_now', 'libre'));
        return `<div class="pl-row${p.enabled ? '' : ' off'}">
            <div class="pl-label"><div class="pl-name"><i class="pl-dot st-${esc(p.status)}"></i>${esc(p.name)}</div>
              <div class="pl-sub">${esc(free)}${p.enabled && p.capacity_hours ? ` · ${hFmt(p.queue_hours)} / ${hFmt(p.capacity_hours)} h` : ''}</div>
              ${loadTxt ? `<span class="pl-chip ${cls}">${loadTxt}</span>` : ''}</div>
            <div class="pl-track" style="--n:${n}">${bars}</div></div>`;
    }).join('');
    if (!data.printers.length) { $('pl-gantt').innerHTML = `<div class="pl-empty">${esc(T('no_printers', 'Ajoutez une imprimante pour planifier.'))}</div>`; return; }
    $('pl-gantt').innerHTML = `<div class="pl-gantt"><div class="pl-row head"><div class="pl-label"></div><div class="pl-track days" style="--n:${n}">${head}</div></div>${rows}</div>`;
}

function renderTable() {
    if (!data.jobs.length) { $('pl-table').innerHTML = `<div class="pl-empty">${esc(T('no_jobs', 'Aucune commande à planifier. Ajoutez-en dans « Commandes » (durée par pièce comprise).'))}</div>`; return; }
    const rows = data.jobs.slice().sort((a, b) => (a.end || '9999').localeCompare(b.end || '9999')).map(j => {
        const c = jobClass(j);
        const slack = j.slack_days == null ? '' : (j.slack_days < 0 ? `<b class="pl-neg">${T('days_late', '{n} j de retard', { n: -j.slack_days })}</b>` : T('days_margin', '{n} j de marge', { n: j.slack_days }));
        return `<tr class="${c}"><td>${esc(j.part)}${j.client ? `<div class="pl-sub">${esc(j.client)}</div>` : ''}</td>
            <td>${esc(j.printer_name)}${j.virtual ? ` <i class="fa-solid fa-wand-magic-sparkles" title="${esc(T('virtual', 'placée automatiquement (aucune imprimante choisie)'))}"></i>` : ''}</td>
            <td>${j.qty_done}/${j.quantity}</td><td>${hFmt(j.hours)} h</td><td>${j.end ? esc(dFmt(j.end)) : '—'}</td>
            <td>${j.due_date ? esc(dFmt(j.due_date)) : '—'}</td><td>${slack}</td></tr>`;
    }).join('');
    $('pl-table').innerHTML = `<div class="pl-table-wrap"><table class="pl-table"><thead><tr>
        <th>${esc(T('col_job', 'Commande'))}</th><th>${esc(T('col_printer', 'Imprimante'))}</th><th>${esc(T('col_done', 'Faites'))}</th><th>${esc(T('col_hours', 'Reste'))}</th>
        <th>${esc(T('col_end', 'Fin estimée'))}</th><th>${esc(T('col_due', 'Livraison'))}</th><th>${esc(T('col_slack', 'Marge'))}</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

function render() { renderKpis(); renderAlerts(); renderGantt(); renderTable(); }

// ── réglages de capacité ──────────────────────────────────────────────────
function dayChecks(prefix, selected) {
    const base = new Date(2024, 0, 1);   // lundi
    let html = '';
    for (let i = 0; i < 7; i++) {
        const d = new Date(base.getFullYear(), base.getMonth(), base.getDate() + i);
        html += `<label class="pl-day-chk"><input type="checkbox" data-d="${i}" ${selected.includes(i) ? 'checked' : ''}><span>${esc(d.toLocaleDateString(lang(), { weekday: 'short' }))}</span></label>`;
    }
    return `<div class="pl-days" data-scope="${prefix}">${html}</div>`;
}
const readDays = (el) => [...el.querySelectorAll('input[data-d]:checked')].map(i => parseInt(i.dataset.d, 10));

async function openSettings() {
    let s;
    try { s = await (await fetch(`${API}/api/planning/settings`, { cache: 'no-store' })).json(); }
    catch (e) { showToast(T('load_error', 'Planning indisponible pour le moment.'), 'error'); return; }
    const d = s.default;
    const rows = s.printers.map(p => `<div class="pl-set-row" data-pid="${p.id}">
        <label class="pl-set-name"><input type="checkbox" class="pl-en" ${p.enabled ? 'checked' : ''}> ${esc(p.name)}</label>
        <input type="number" class="settings-select pl-hpd" min="0.5" max="24" step="0.5" value="${p.hours_per_day == null ? '' : p.hours_per_day}" placeholder="${d.hours_per_day}">
        <span class="pl-set-h">${esc(T('hours_day', 'h / jour'))}</span>
        ${dayChecks('p' + p.id, p.days || d.days)}</div>`).join('');
    $('pl-settings-body').innerHTML = `
        <p class="pl-sub">${esc(T('settings_help', 'Heures d’impression possibles par jour et jours travaillés. Laissez vide pour reprendre la valeur par défaut. Une imprimante décochée n’est pas planifiée.'))}</p>
        <div class="pl-set-row pl-set-default"><strong class="pl-set-name">${esc(T('default', 'Par défaut'))}</strong>
          <input type="number" class="settings-select" id="pl-def-hpd" min="0.5" max="24" step="0.5" value="${d.hours_per_day}"><span class="pl-set-h">${esc(T('hours_day', 'h / jour'))}</span>
          ${dayChecks('def', d.days)}</div>
        ${rows || `<div class="pl-empty">${esc(T('no_printers', 'Ajoutez une imprimante pour planifier.'))}</div>`}
        <div class="modal-footer" style="display:flex;justify-content:flex-end;gap:8px;margin-top:14px;">
          <button type="button" class="btn btn-secondary" onclick="closeModal('modal-planning-settings')">${esc(T('cancel', 'Annuler'))}</button>
          <button type="button" class="btn btn-primary" id="pl-save-settings">${esc(T('save', 'Enregistrer'))}</button></div>`;
    $('pl-save-settings').addEventListener('click', async () => {
        const defHpd = parseFloat($('pl-def-hpd').value) || 16;
        const defDays = readDays($('pl-settings-body').querySelector('[data-scope="def"]'));
        const printers = [...$('pl-settings-body').querySelectorAll('.pl-set-row[data-pid]')].map(row => {
            const days = readDays(row.querySelector('.pl-days'));
            const same = days.length === defDays.length && days.every((x, i) => x === defDays[i]);
            return { id: parseInt(row.dataset.pid, 10), enabled: row.querySelector('.pl-en').checked,
                     hours_per_day: row.querySelector('.pl-hpd').value, days: same ? [] : days };
        });
        const r = await fetch(`${API}/api/planning/settings`, { method: 'PUT', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ default: { hours_per_day: defHpd, days: defDays.length ? defDays : [0, 1, 2, 3, 4, 5, 6] }, printers }) });
        if (!r.ok) { showToast(T('save_error', 'Enregistrement impossible'), 'error'); return; }
        closeModal('modal-planning-settings');
        load();
    });
    openModal('modal-planning-settings');
}

function wire() {
    if (wired) return;
    wired = true;
    $('pl-horizon').addEventListener('change', load);
    $('pl-refresh').addEventListener('click', load);
    $('pl-open-settings').addEventListener('click', openSettings);
    $('pl-open-orders').addEventListener('click', async () => {
        if (typeof openOrdersModal !== 'function') return;
        await openOrdersModal();
        const m = $('modal-orders');   // à la fermeture des commandes, le planning est recalculé
        if (m && !m._plObs) {
            m._plObs = new MutationObserver(() => { if (m.classList.contains('hidden') && $('page-planning').classList.contains('active')) load(); });
            m._plObs.observe(m, { attributes: true, attributeFilter: ['class'] });
        }
    });
}

function onShow() { wire(); load(); }

window.StellioPlanning = { onShow, _data: () => data };
})();
