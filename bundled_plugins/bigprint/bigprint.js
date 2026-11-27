/* Stellio — v1.1.4 : page « BigPrint » (Outils).
   Mise à l'échelle grandeur nature + découpe en pièces, avec le moteur open source bigprint (PooterTF/bigprint, AGPL-3.0).
   Dépend des fonctions globales de script.js (I18N, openModal, closeModal, showToast, escapeHtml, loadDownloadSources, allFiles, API). */
(function () {
'use strict';

const $ = (id) => document.getElementById(id);
const tr = (k, fb, p) => {
    let s = (typeof I18N !== 'undefined' && I18N.t) ? I18N.t(k) : k;
    if (!s || s === k) s = fb;
    if (p) Object.keys(p).forEach(n => { s = s.split('{' + n + '}').join(p[n]); });
    return s;
};
const T = (k, fb, p) => tr('bigprint.' + k, fb, p);
const esc = (v) => (typeof escapeHtml === 'function' ? escapeHtml(String(v)) : String(v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));

const FIELDS = ['size_mode', 'size_value', 'size_unit', 'printer', 'purpose', 'hollow', 'wall', 'material', 'price',
    'dowel_d', 'dowel_depth', 'clearance', 'smooth_angle', 'smooth_edge', 'up', 'margin', 'nozzle'];
const CHECKS = ['dowels', 'labels', 'smooth', 'repair', 'merge_small', 'even_cuts'];
const MODEL_EXT = ['.stl', '.3mf', '.obj', '.ply'];

let cfg = null;
let cfgLang = '';
let model = null;          // {id, name, stem, extents, triangles, watertight, median_edge}
let pollTimer = null;
let lastPreviewKey = null; // réglages du dernier aperçu terminé (l'enregistrement exige les mêmes)
let busy = false;
let wired = false;
let lastKind = null;

async function api(path, body, opts) {
    const init = body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
    Object.assign(init, opts || {});
    const r = await fetch(API + path, init);
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.error || ('HTTP ' + r.status));
    return data;
}

function settings() {
    const s = { model_id: model ? model.id : null };
    FIELDS.forEach(f => { s[f] = $('bp-' + f).value; });
    CHECKS.forEach(f => { s[f] = $('bp-' + f).checked; });
    s.bed = [$('bp-bed_w').value, $('bp-bed_d').value, $('bp-bed_h').value];
    return s;
}
const keyOf = (s) => JSON.stringify(s, Object.keys(s).sort());

function bedSize() {
    const p = $('bp-printer').value;
    return p === 'custom' ? [+$('bp-bed_w').value, +$('bp-bed_d').value, +$('bp-bed_h').value] : (cfg && cfg.printers[p]) || [250, 250, 250];
}

function setStatus(text, kind) {
    const el = $('bp-status');
    el.textContent = text || '';
    el.className = 'bp-muted' + (kind ? ' bp-' + kind : '');
}

function updateButtons() {
    $('bp-preview-btn').disabled = busy || !model;
    $('bp-save-btn').disabled = busy || !model || lastPreviewKey === null || lastPreviewKey !== keyOf(settings());
    $('bp-cancel-btn').hidden = !busy;
}

function updateDerived() {
    $('bp-size_unit').hidden = $('bp-size_mode').value === 'scale';
    $('bp-custom-bed').hidden = $('bp-printer').value !== 'custom';
    $('bp-dowel-opts').hidden = !$('bp-dowels').checked;
    $('bp-smooth-opts').hidden = !$('bp-smooth').checked;
    const pr = cfg && cfg.presets[$('bp-purpose').value];
    $('bp-purpose-hint').textContent = pr ? (pr.describe + '. ' + pr.why) : '';
    // taille finale estimée
    const note = $('bp-size-note');
    note.textContent = '';
    if (model) {
        const e = model.extents.slice();
        const up = $('bp-up').value;
        const oe = (up === 'y' || up === '-y') ? [e[0], e[2], e[1]] : (up === 'x' ? [e[2], e[1], e[0]] : e);
        const mode = $('bp-size_mode').value;
        const v = parseFloat($('bp-size_value').value);
        if (v > 0) {
            const mm = { mm: 1, cm: 10, m: 1000, in: 25.4, ft: 304.8 }[$('bp-size_unit').value] || 1;
            let k = null;
            if (mode === 'scale') k = v;
            else {
                const axis = { width: 0, depth: 1, height: 2 }[mode];
                if (oe[axis] > 0) k = v * mm / oe[axis];
            }
            if (k) {
                const fin = oe.map(x => Math.round(x * k));
                const bed = bedSize();
                const grid = [0, 1, 2].map(i => Math.max(1, Math.ceil(fin[i] / Math.max(1, bed[i] - 2 * (+$('bp-margin').value || 0)))));
                note.textContent = T('size_result', '{w} × {d} × {h} mm — environ {n} pièces ({a}×{b}×{c})', {
                    w: fin[0], d: fin[1], h: fin[2], n: grid[0] * grid[1] * grid[2], a: grid[0], b: grid[1], c: grid[2],
                });
            }
        }
    }
    updateButtons();
}

function showModel(info) {
    model = info;
    lastPreviewKey = null;
    const e = info.extents.map(v => Math.round(v * 10) / 10);
    let html = '<strong>' + esc(info.name) + '</strong><br>' + esc(T('model_info', '{tri} triangles · {w} × {d} × {h} mm', { tri: info.triangles.toLocaleString(), w: e[0], d: e[1], h: e[2] }));
    if (!info.watertight) html += '<br><span class="bp-warn">' + esc(T('not_watertight', 'Le modèle a des trous ou des surfaces qui se chevauchent : laissez la réparation automatique activée.')) + '</span>';
    $('bp-model-info').innerHTML = html;
    $('bp-model-info').classList.remove('bp-muted');
    if (!$('bp-folder-name').value || $('bp-folder-name').dataset.auto === '1') {
        $('bp-folder-name').value = info.stem + '_bigprint';
        $('bp-folder-name').dataset.auto = '1';
    }
    syncDestLabel();
    $('bp-viewer').hidden = true;
    $('bp-summary').hidden = true;
    $('bp-result').hidden = true;
    updateDerived();
}

// Premier choix du sélecteur de destination : « à côté du fichier source » pour un modèle de la bibliothèque, sinon le dossier de données de Stellio.
function syncDestLabel() {
    const sel = $('bp-source'); const o = sel && sel.options[0]; if (!o || o.value !== '') return;
    o.textContent = ' ' + (model && model.from_library ? T('dest_beside', 'À côté du fichier source') : T('dest_default', 'Dossier de données de Stellio'));
}

function isViewer() { return document.body.classList.contains('role-viewer'); }   // invité / démo : aperçu seulement

function curLang() { try { return (window.I18N && I18N.lang) || 'fr'; } catch (e) { return 'fr'; } }

async function loadConfig() {
    if (cfg && cfgLang === curLang()) return cfg;
    const c = await api('/api/bigprint/config?lang=' + encodeURIComponent(curLang()));
    if (!c.available) {
        const b = $('bp-unavailable');
        b.hidden = false;
        b.textContent = T('unavailable', 'Le moteur BigPrint n\'est pas disponible sur cette installation.') + ' ' + String(c.error || '').replace(/^Le moteur BigPrint n'est pas disponible\s*:\s*/, '');
        $('bp-pick-library').disabled = true;
        $('bp-pick-upload').disabled = true;
        return null;
    }
    cfg = c; cfgLang = curLang();
    const prevPurpose = $('bp-purpose').value, prevMaterial = $('bp-material').value, prevPrinter = $('bp-printer').value;
    const pr = $('bp-printer');
    pr.innerHTML = Object.keys(c.printers).map(k => `<option value="${esc(k)}">${esc(k)} (${c.printers[k].join(' × ')} mm)</option>`).join('')
        + `<option value="custom">${esc(T('custom', 'Personnalisée…'))}</option>`;
    try { pr.value = localStorage.getItem('bp_printer') || c.default_printer; } catch (e) { pr.value = c.default_printer; }
    if (!pr.value) pr.value = c.default_printer;
    $('bp-purpose').innerHTML = c.purposes.map(k => `<option value="${esc(k)}">${esc(c.presets[k].label)}</option>`).join('');
    if (prevPurpose && c.purposes.includes(prevPurpose)) $('bp-purpose').value = prevPurpose;
    $('bp-material').innerHTML = c.materials.map(k => `<option value="${esc(k)}">${esc(k.toUpperCase())}</option>`).join('');
    if (prevMaterial && c.materials.includes(prevMaterial)) $('bp-material').value = prevMaterial;
    if (prevPrinter && (prevPrinter === 'custom' || c.printers[prevPrinter])) $('bp-printer').value = prevPrinter;
    updateDerived();
    return c;
}

function renderSummary(s) {
    const rows = (s.table || []).map(r => `<tr><td>${esc(r.id)}</td><td>${r.size.join(' × ')}</td><td>${esc(r.fill)}</td><td>${r.grams} g</td></tr>`).join('');
    const warn = (s.warnings || []).map(w => `<li>${esc(w)}</li>`).join('');
    const stats = [
        [T('s_pieces', 'Pièces'), s.pieces],
        [T('s_filament', 'Filament'), s.kg.toFixed(2) + ' kg (' + T('s_solid', 'plein : {kg} kg', { kg: s.solid_kg.toFixed(2) }) + ')'],
        [T('s_cost', 'Coût'), s.cost != null ? s.cost.toFixed(2) : '—'],
        [T('s_dowels', 'Goujons'), s.dowels],
        [T('s_size', 'Taille finale'), s.size.join(' × ') + ' mm'],
        [T('s_scale', 'Échelle'), '×' + (+s.scale).toFixed(3)],
    ].map(([k, v]) => `<div class="bp-stat"><span>${esc(k)}</span><strong>${esc(v)}</strong></div>`).join('');
    $('bp-summary').innerHTML = `<h3>${esc(T('summary', 'Résultat'))}</h3><div class="bp-stats">${stats}</div>`
        + (s.cuts ? `<p class="bp-muted">${esc(s.cuts)}</p>` : '')
        + (warn ? `<ul class="bp-warn-list">${warn}</ul>` : '')
        + `<div class="bp-table-wrap"><table class="bp-table"><thead><tr><th>${esc(T('col_piece', 'Pièce'))}</th><th>${esc(T('col_size', 'Taille (mm)'))}</th><th>${esc(T('col_fill', 'Remplissage'))}</th><th>${esc(T('col_grams', 'Poids'))}</th></tr></thead><tbody>${rows}</tbody></table></div>`;
    $('bp-summary').hidden = false;
}

function stopPolling() { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } }

async function poll(sentKey) {
    let data;
    try { data = await api('/api/bigprint/job?lang=' + encodeURIComponent(curLang())); } catch (e) { return; }
    const job = data.job;
    if (!job) return;
    const bar = $('bp-progress-bar');
    $('bp-progress').hidden = job.state !== 'running';
    bar.style.width = Math.round((job.fraction || 0) * 100) + '%';
    if (job.log && job.log.length) { $('bp-log-wrap').hidden = false; $('bp-log').textContent = job.log.join('\n'); }
    if (job.state === 'running') { setStatus(job.stage || '…'); return; }
    stopPolling();
    busy = false;
    $('bp-progress').hidden = true;
    if (job.state === 'done') {
        if (lastKind === 'preview') {
            lastPreviewKey = sentKey;
            if (data.summary) renderSummary(data.summary);
            $('bp-result').hidden = false;
            const v = $('bp-viewer');
            v.src = API + '/api/bigprint/preview.html?lang=' + encodeURIComponent(curLang()) + '&t=' + Date.now();
            v.hidden = false;
            setStatus(T('done_preview', 'Aperçu prêt. Vérifiez le résultat puis enregistrez les fichiers.'), 'ok');
            setTimeout(() => { try { $('bp-result').scrollIntoView({ behavior: 'smooth', block: 'nearest' }); } catch (e) { /* ignore */ } }, 150);
        } else {
            setStatus(T('done_save', 'Fichiers enregistrés dans {folder}', { folder: job.out || '' }), 'ok');
            if (typeof showToast === 'function') showToast(T('done_save', 'Fichiers enregistrés dans {folder}', { folder: job.out || '' }), 'success');
            if (typeof loadFiles === 'function') setTimeout(() => { try { loadFiles(); } catch (e) { /* ignore */ } }, 800);
        }
    } else if (job.state === 'cancelled') {
        setStatus(T('cancelled', 'Annulé.'));
    } else {
        setStatus(job.error || T('error', 'Erreur'), 'err');
    }
    updateButtons();
}

function startPolling(sentKey) {
    stopPolling();
    pollTimer = setInterval(() => poll(sentKey), 700);
    poll(sentKey);
}

async function runPreview() {
    if (!model || busy) return;
    const s = settings();
    busy = true; lastKind = 'preview';
    updateButtons();
    setStatus(T('running', 'Calcul en cours…'));
    $('bp-log').textContent = '';
    try {
        await api('/api/bigprint/preview', { settings: s });
        startPolling(keyOf(s));
    } catch (e) {
        busy = false;
        setStatus(e.message, 'err');
        updateButtons();
    }
}

async function runSave() {
    if (!model || busy) return;
    const s = settings();
    if (lastPreviewKey !== keyOf(s)) { setStatus(T('need_preview', 'Les réglages ont changé : relancez l\'aperçu avant d\'enregistrer.'), 'err'); return; }
    busy = true; lastKind = 'save';
    updateButtons();
    setStatus(T('saving', 'Enregistrement en cours…'));
    try {
        await api('/api/bigprint/save', {
            settings: s,
            source_id: (() => { const o = $('bp-source').options[$('bp-source').selectedIndex]; return (o && o.dataset.baseSourceId) || $('bp-source').value || ''; })(),
            target_subfolder: (() => { const o = $('bp-source').options[$('bp-source').selectedIndex]; return (o && o.dataset.relPath) || ''; })(),
            folder_name: $('bp-folder-name').value.trim(),
        });
        startPolling(keyOf(s));
    } catch (e) {
        busy = false;
        setStatus(e.message, 'err');
        updateButtons();
    }
}

async function cancel() {
    try { await api('/api/bigprint/cancel', {}); } catch (e) { /* ignore */ }
    stopPolling();
    busy = false;
    lastPreviewKey = null;
    $('bp-progress').hidden = true;
    setStatus(T('cancelled', 'Annulé.'));
    updateButtons();
}

async function chooseFromLibrary(path) {
    closeModal('modal-bp-picker');
    setStatus(T('loading', 'Lecture du modèle…'));
    try {
        showModel(await api('/api/bigprint/model', { path }));
        setStatus('');
    } catch (e) { setStatus(e.message, 'err'); }
}

const PICK_PER_PAGE = 10;
let pickPage = 1;
/* Numéros de page à afficher : tout si peu de pages, sinon première, dernière et une fenêtre autour de la page courante (« … » entre les deux). */
function pickPages(cur, total) {
    if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
    const out = new Set([1, total, cur - 1, cur, cur + 1]);
    if (cur <= 3) { out.add(2); out.add(3); out.add(4); }
    if (cur >= total - 2) { out.add(total - 1); out.add(total - 2); out.add(total - 3); }
    const nums = [...out].filter(n => n >= 1 && n <= total).sort((x, y) => x - y), res = [];
    nums.forEach((n, i) => { if (i && n - nums[i - 1] > 1) res.push('…'); res.push(n); });
    return res;
}
function renderPicker(keepPage) {
    const q = ($('bp-picker-search').value || '').trim().toLowerCase();
    const list = (typeof allFiles !== 'undefined' ? allFiles : []).filter(f => {
        const ext = (f.extension || '').toLowerCase();
        return MODEL_EXT.includes(ext) && (!q || (f.name || '').toLowerCase().includes(q));
    });
    const total = Math.max(1, Math.ceil(list.length / PICK_PER_PAGE));
    pickPage = keepPage ? Math.min(Math.max(1, pickPage), total) : 1;
    const box = $('bp-picker-list'), pager = $('bp-picker-pager');
    if (!list.length) { box.innerHTML = '<div class="bp-muted">' + esc(T('pick_none', 'Aucun modèle trouvé.')) + '</div>'; if (pager) pager.innerHTML = ''; return; }
    const pageItems = list.slice((pickPage - 1) * PICK_PER_PAGE, pickPage * PICK_PER_PAGE);
    box.scrollTop = 0;
    box.innerHTML = pageItems.map((f, i) => `<button type="button" class="bp-picker-item" data-i="${i}"><span class="bp-picker-thumb">${f.has_thumb === false ? '<i class="fa-solid fa-cube"></i>' : `<img src="${API}/api/thumb?path=${encodeURIComponent(f.path)}" loading="lazy" alt="" onerror="this.replaceWith(Object.assign(document.createElement('i'),{className:'fa-solid fa-cube'}))">`}</span><span>${esc(f.name)}</span><small>${esc((f.extension || '').replace('.', '').toUpperCase())}</small></button>`).join('');
    box.querySelectorAll('.bp-picker-item').forEach(b => b.addEventListener('click', () => chooseFromLibrary(pageItems[+b.dataset.i].path)));
    if (!pager) return;
    if (total <= 1) { pager.innerHTML = `<span class="bp-muted">${list.length} ${esc(T('pick_count', 'modèle(s)'))}</span>`; return; }
    const atFirst = pickPage === 1, atLast = pickPage === total;
    const nav = (p, icon, label, off) => `<button type="button" class="bp-page-btn" data-p="${p}" title="${esc(label)}" aria-label="${esc(label)}"${off ? ' disabled' : ''}><i class="fa-solid ${icon}"></i></button>`;
    pager.innerHTML = nav(1, 'fa-angles-left', T('pick_first', 'Première page'), atFirst) + nav(pickPage - 1, 'fa-angle-left', T('pick_prev', 'Page précédente'), atFirst) +
        pickPages(pickPage, total).map(n => n === '…' ? '<span class="bp-page-gap">…</span>' : `<button type="button" class="bp-page-btn${n === pickPage ? ' active' : ''}" data-p="${n}"${n === pickPage ? ' aria-current="page"' : ''}>${n}</button>`).join('') +
        nav(pickPage + 1, 'fa-angle-right', T('pick_next', 'Page suivante'), atLast) + nav(total, 'fa-angles-right', T('pick_last', 'Dernière page'), atLast);
    pager.querySelectorAll('[data-p]').forEach(b => b.addEventListener('click', () => { if (b.disabled) return; pickPage = +b.dataset.p; renderPicker(true); }));
}

async function uploadFile(file) {
    if (!file) return;
    const ext = '.' + (file.name.split('.').pop() || '').toLowerCase();
    if (!MODEL_EXT.includes(ext)) { setStatus(T('bad_format', 'Format non pris en charge (STL, 3MF, OBJ ou PLY).'), 'err'); return; }
    setStatus(T('loading', 'Lecture du modèle…'));
    try {
        const r = await fetch(API + '/api/bigprint/upload', { method: 'POST', headers: { 'X-Filename': encodeURIComponent(file.name), 'Content-Type': 'application/octet-stream' }, body: file });
        const data = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(data.error || ('HTTP ' + r.status));
        showModel(data);
        setStatus('');
    } catch (e) { setStatus(e.message, 'err'); }
}

function wire() {
    if (wired) return;
    wired = true;
    if (isViewer()) $('bp-viewer-note').hidden = false;
    [...FIELDS, ...CHECKS].forEach(f => {
        const el = $('bp-' + f);
        el.addEventListener('input', updateDerived);
        el.addEventListener('change', () => {
            if (f === 'printer') { try { localStorage.setItem('bp_printer', el.value); } catch (e) { /* ignore */ } }
            updateDerived();
        });
    });
    ['bed_w', 'bed_d', 'bed_h'].forEach(f => $('bp-' + f).addEventListener('input', updateDerived));
    $('bp-folder-name').addEventListener('input', () => { $('bp-folder-name').dataset.auto = '0'; });
    $('bp-folder-name').addEventListener('blur', () => {
        const el = $('bp-folder-name'); const v = el.value.trim();
        if (v && !/_bigprint$/i.test(v)) el.value = v + '_bigprint';
    });
    $('bp-pick-library').addEventListener('click', () => { $('bp-picker-search').value = ''; renderPicker(); openModal('modal-bp-picker'); setTimeout(() => $('bp-picker-search').focus(), 80); });
    $('bp-picker-search').addEventListener('input', () => renderPicker());
    $('bp-pick-upload').addEventListener('click', () => $('bp-file').click());
    $('bp-file').addEventListener('change', (e) => { uploadFile(e.target.files[0]); e.target.value = ''; });
    $('bp-preview-btn').addEventListener('click', runPreview);
    $('bp-save-btn').addEventListener('click', runSave);
    $('bp-cancel-btn').addEventListener('click', cancel);
    const page = $('page-bigprint');
    page.addEventListener('dragover', (e) => { e.preventDefault(); });
    page.addEventListener('drop', (e) => { e.preventDefault(); if (!isViewer() && e.dataTransfer.files && e.dataTransfer.files[0]) uploadFile(e.dataTransfer.files[0]); });
}

async function onShow() {
    wire();
    try { await loadConfig(); } catch (e) { setStatus(e.message, 'err'); }
    if (typeof loadDownloadSources === 'function') {
        try { await loadDownloadSources('bp-source', T('dest_default', 'Dossier de données de Stellio')); } catch (e) { /* liste de sources : sans incidence */ }
    }
    syncDestLabel();
    updateDerived();
}

async function loadPath(path) {
    wire();
    try { await loadConfig(); } catch (e) { /* géré par onShow */ }
    if (cfg) await chooseFromLibrary(path);
}

window.StellioBigPrint = { onShow, loadPath, _settings: settings, _keyOf: keyOf };
})();
