/* Stellio — v1.1.7 : assistant de bibliothèque. Pose une question qui croise bibliothèque, imprimantes, matières et historique.
   Le modèle d'IA (si configuré) ne fait que choisir une requête prédéfinie ; sans IA, des règles prennent le relais (modules/library_assistant.py). */
(function () {
'use strict';
const $ = (id) => document.getElementById(id);
const tr = (k, fb, p) => {
    let s = (typeof I18N !== 'undefined' && I18N.t) ? I18N.t('assistant.' + k) : k;
    if (!s || s === 'assistant.' + k) s = fb;
    if (p) Object.keys(p).forEach(n => { s = s.split('{' + n + '}').join(p[n]); });
    return s;
};
const esc = (v) => (typeof escapeHtml === 'function' ? escapeHtml(String(v)) : String(v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
async function j(url, body) {
    const r = await fetch(`${API}${url}`, body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : { cache: 'no-store' });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(d.error || r.status);
    return d;
}
let meta = null;

function chips() {
    const p = (meta.printers.find(x => x.has_bed) || meta.printers[0]);
    const list = [];
    if (p) list.push({ k: 'chip_fit', fb: 'Modèles qui tiennent sur {name}', q: 'Quels modèles tiennent sur ' + p.name + ' ?', p: { name: p.name } });
    list.push({ k: 'chip_petg', fb: 'Déjà imprimés en PETG', q: 'Quels modèles ai-je déjà imprimés en PETG ?' });
    list.push({ k: 'chip_never', fb: 'Jamais imprimés', q: 'Quels modèles ai-je jamais imprimés ? pas encore' });
    list.push({ k: 'chip_failed', fb: 'Ceux qui échouent le plus', q: 'Quels modèles échouent le plus ?' });
    list.push({ k: 'chip_reliable', fb: 'Les plus fiables', q: 'Quels sont les modèles les plus fiables ?' });
    list.push({ k: 'chip_recent', fb: 'Impressions des 30 derniers jours', q: 'Mes impressions récentes' });
    return list;
}
// la 3e pastille ne passe pas par la question libre : requête directe du catalogue (pas d'ambiguïté de langue)
const DIRECT = { chip_never: { query: 'find_models', params: { printed: 'no' } }, chip_failed: { query: 'most_failed', params: {} },
                 chip_reliable: { query: 'most_reliable', params: {} }, chip_recent: { query: 'recent_prints', params: { days: 30 } },
                 chip_petg: { query: 'find_models', params: { material: 'PETG', printed: 'yes' } } };

function ensure() {
    let dlg = $('modal-assistant');
    if (dlg) return dlg;
    dlg = document.createElement('div');
    dlg.id = 'modal-assistant';
    dlg.className = 'modal hidden';
    dlg.innerHTML = `<div class="modal-content" style="width:min(760px,95vw);max-width:760px;">
        <div class="modal-header"><h3><i class="fa-solid fa-wand-magic-sparkles"></i> <span>${esc(tr('title', 'Assistant de bibliothèque'))}</span></h3>
          <button class="modal-close" type="button" id="as-x">×</button></div>
        <div class="modal-body">
          <p class="settings-hint" id="as-hint"></p>
          <div class="as-chips" id="as-chips"></div>
          <form class="as-form" id="as-form"><input type="text" id="as-q" class="settings-select" maxlength="400" autocomplete="off" placeholder="${esc(tr('ph', 'Ex. : quels modèles tiennent sur ma plus petite imprimante et ont déjà réussi en PETG ?'))}">
            <button type="submit" class="btn btn-primary btn-sm"><i class="fa-solid fa-paper-plane"></i> ${esc(tr('ask', 'Demander'))}</button></form>
          <div id="as-result" class="as-result"></div>
        </div></div>`;
    document.body.appendChild(dlg);
    $('as-x').onclick = () => (typeof closeModal === 'function' ? closeModal('modal-assistant') : dlg.classList.add('hidden'));
    $('as-form').onsubmit = (e) => { e.preventDefault(); const q = $('as-q').value.trim(); if (q) run({ question: q }); };
    return dlg;
}

const fmtRate = (r) => (r == null ? '—' : Math.round(r * 100) + ' %');
const fmtDate = (s) => (s ? String(s).slice(0, 10) : '—');
function cell(v) { return `<td>${esc(v == null || v === '' ? '—' : v)}</td>`; }

function table(d) {
    const rows = d.rows || [];
    if (!rows.length) return `<p class="settings-hint">${esc(tr('empty', 'Aucun résultat pour cette question.'))}</p>`;
    let head, body;
    const t = (k, fb) => esc(tr(k, fb));
    switch (d.query) {
    case 'best_setup':
        head = [t('c_version', 'Version'), t('c_profile', 'Profil'), t('c_prints', 'Impressions'), t('c_rate', 'Réussite'), ''];
        body = rows.map(r => `<tr class="${r.best ? 'as-best' : ''}">${cell(r.version == null ? '?' : 'v' + r.version)}${cell(r.profile || '—')}${cell(r.total)}${cell(fmtRate(r.rate))}<td>${r.best ? '★ ' + t('best', 'Meilleur réglage') : (r.confident ? '' : '<span class="v13-muted">' + t('few', 'peu de données') + '</span>')}</td></tr>`).join('');
        break;
    case 'recent_prints':
        head = [t('c_name', 'Modèle'), t('c_date', 'Date'), t('c_result', 'Résultat'), t('c_material', 'Matière'), t('c_printer', 'Imprimante')];
        body = rows.map(r => `<tr>${cell(r.name)}${cell(fmtDate(r.sent_at))}${cell(r.result)}${cell(r.material)}${cell(r.printer)}</tr>`).join('');
        break;
    case 'printer_usage':
        head = [t('c_printer', 'Imprimante'), t('c_prints', 'Impressions'), t('c_ok', 'Réussies'), t('c_ko', 'Échouées'), t('c_rate', 'Réussite')];
        body = rows.map(r => `<tr>${cell(r.name)}${cell(r.prints)}${cell(r.success)}${cell(r.failed)}${cell(fmtRate(r.rate))}</tr>`).join('');
        break;
    default:
        head = [t('c_name', 'Modèle'), t('c_prints', 'Impressions'), t('c_ok', 'Réussies'), t('c_ko', 'Échouées'), t('c_rate', 'Réussite'), t('c_last', 'Dernière')];
        body = rows.map(r => `<tr>${cell(r.name)}${cell(r.prints)}${cell(r.success)}${cell(r.failed)}${cell(fmtRate(r.rate))}${cell(fmtDate(r.last))}</tr>`).join('');
    }
    return `<div class="as-scroll"><table class="as-table"><thead><tr>${head.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>${body}</tbody></table></div>`;
}

function describe(d) {
    const how = d.via === 'ai' ? tr('via_ai', 'Requête choisie par l\'IA') : (d.via === 'direct' ? '' : tr('via_rules', 'Requête choisie par les règles intégrées'));
    const q = tr('q_' + d.query, d.query);
    const ps = Object.keys(d.params || {}).map(k => `${k} = ${d.params[k]}`).join(', ');
    return `<div class="as-meta"><b>${esc(q)}</b>${ps ? ' · <code>' + esc(ps) + '</code>' : ''}${how ? ' · ' + esc(how) : ''}${d.total > (d.rows || []).length ? ' · ' + esc(tr('more', '{n} résultats au total', { n: d.total })) : ''}</div>`;
}

function noteText(n) {
    const [k, v] = String(n).split(':');
    const m = { bed_unknown: 'Le volume d\'impression de cette imprimante n\'est pas renseigné.', dims_unknown: '{n} modèle(s) sans dimensions connues ont été écartés (lancez l\'analyse).',
                no_data: 'Pas encore assez d\'impressions notées.', no_best: 'Aucune combinaison n\'a encore assez d\'impressions réussies pour être recommandée.', trace_unavailable: 'Traçabilité indisponible.' };
    return tr('n_' + k, m[k] || k, { n: v });
}

async function run(body) {
    const box = $('as-result');
    box.innerHTML = `<p class="settings-hint"><i class="fa-solid fa-spinner fa-spin"></i> ${esc(tr('thinking', 'Recherche…'))}</p>`;
    try {
        const d = await j('/api/assistant/ask', body);
        if (d.error) { box.innerHTML = `<p class="settings-hint">${esc(tr('unclear', 'Je n\'ai pas compris la question. Essayez une des suggestions ci-dessus.'))}</p>`; return; }
        const notes = (d.notes || []).map(n => `<p class="settings-hint">ℹ ${esc(noteText(n))}</p>`).join('');
        box.innerHTML = describe(d) + table(d) + notes;
    } catch (e) {
        box.innerHTML = `<p class="settings-hint">${esc(tr('unavailable', 'Réservé au compte propriétaire.'))}</p>`;
    }
}

async function open() {
    const dlg = ensure();
    try { meta = await j('/api/assistant/queries'); } catch (e) { meta = null; }
    if (!meta) { if (typeof showToast === 'function') showToast(tr('unavailable', 'Réservé au compte propriétaire.'), 'error'); return; }
    $('as-hint').textContent = meta.ai ? tr('hint_ai', 'L\'IA choisit la bonne requête parmi une liste fermée : elle n\'accède jamais directement à vos données.')
                                       : tr('hint_rules', 'IA non configurée : des règles intégrées comprennent les questions courantes.');
    $('as-chips').innerHTML = chips().map((c, i) => `<button type="button" class="as-chip" data-i="${i}">${esc(tr(c.k, c.fb, c.p))}</button>`).join('');
    const cl = chips();
    $('as-chips').querySelectorAll('.as-chip').forEach(b => b.onclick = () => { const c = cl[+b.dataset.i]; run(DIRECT[c.k] || { question: c.q }); });
    $('as-result').innerHTML = '';
    if (typeof openModal === 'function') openModal('modal-assistant'); else dlg.classList.remove('hidden');
    setTimeout(() => { const q = $('as-q'); if (q) q.focus(); }, 50);
}
window.StellioAssistant = { open };
})();
document.addEventListener('DOMContentLoaded', () => { try { if (typeof IS_VIEWER !== 'undefined' && IS_VIEWER) { const b = document.getElementById('assistant-btn'); if (b) b.style.display = 'none'; } } catch (e) {} });
