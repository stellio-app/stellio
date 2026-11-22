/* Stellio — v1.1.7 : « Atelier avancé ». Une page (menu Outils), un onglet par fonction (tâches, journal, équipes, compatibilité, organisation, diff 3D,
   pièces similaires, plugins, synchro, plateau, communauté, sessions, archives G-code, licences, assistant de fabrication). Réservé au propriétaire ; les chemins se saisissent ou se choisissent dans la bibliothèque (source, recherche, miniatures). */
(function () {
'use strict';
const $ = (id) => document.getElementById(id);
const tr = (k, fb) => { const s = (typeof I18N !== 'undefined' && I18N.t) ? I18N.t('suite.' + k) : ''; return (s && s !== 'suite.' + k) ? s : fb; };
const ask = (msg, opts) => (typeof showConfirmDialog === 'function') ? showConfirmDialog(msg, opts || {}) : Promise.resolve(confirm(msg));
const esc = (v) => (typeof escapeHtml === 'function' ? escapeHtml(String(v)) : String(v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
async function api(url, body, method) {
    const opt = body !== undefined ? { method: method || 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : { cache: 'no-store' };
    if (!body && method) opt.method = method;
    const r = await fetch(`${API}${url}`, opt);
    const d = await r.json().catch(() => ({}));
    if (!r.ok) { const e = new Error(d.error || r.status); e.data = d; throw e; }
    return d;
}
const fmt = (ts) => { try { return new Date(ts * 1000).toLocaleString(); } catch (e) { return ''; } };
const cell = (v) => `<td>${esc(v == null || v === '' ? '—' : (typeof v === 'object' ? JSON.stringify(v) : v))}</td>`;
function table(rows, cols) {
    if (!rows || !rows.length) return `<p class="settings-hint">${esc(tr('empty', 'Rien à afficher pour le moment.'))}</p>`;
    return `<div class="suite-scroll"><table class="suite-table"><thead><tr>${cols.map(c => `<th>${esc(c[1])}</th>`).join('')}</tr></thead><tbody>${rows.map(r =>
        `<tr>${cols.map(c => cell(c[2] ? c[2](r[c[0]], r) : r[c[0]])).join('')}</tr>`).join('')}</tbody></table></div>`;
}
const note = (box, msg, bad) => { const p = box.querySelector('.suite-msg') || box.insertAdjacentElement('afterbegin', Object.assign(document.createElement('p'), { className: 'suite-msg settings-hint' })); p.textContent = msg; p.style.color = bad ? 'var(--danger, #e5484d)' : ''; };
/* 1.2.0 : un plugin à code intégré (signé) ne se charge qu'au démarrage : après chaque installation ou mise à jour, on le dit et on propose le redémarrage. */
const offerRestart = (box, pl) => { if (!(pl && pl.host)) return; note(box, '✓ ' + tr('restart_after_install', 'Plugin installé : redémarrez Stellio pour le charger (ou pour appliquer la mise à jour).')); setTimeout(() => { const b = document.getElementById('su-restart'); if (b) b.click(); }, 300); };
/* Avancement d'une tâche longue : dans le bandeau d'activité s'il existe (Diff 3D…), sinon message ordinaire. */
const prog = (box, msg) => { const wk = box.querySelector('.su-work-auto span'); if (!wk) return note(box, msg); const m = String(msg || '').trim().replace(/^[a-z_]+\s*/i, ''); wk.textContent = tr('working', 'Calcul en cours…') + (m ? ' ' + m : ''); };
const field = (id, label, ph, cls) => `<label class="suite-field${cls ? ' ' + cls : ''}"><span>${esc(label)}</span><input type="text" id="${id}" class="settings-select" placeholder="${esc(ph || '')}" autocomplete="off"></label>`;
const btn = (id, label, cls) => `<button type="button" id="${id}" class="btn ${cls || 'btn-primary'} btn-sm">${esc(label)}</button>`;
/* Champ « chemin » : saisie libre + bouton qui ouvre la bibliothèque (source, recherche, miniatures). */
const pickBtn = (id, multi) => `<button type="button" class="btn btn-secondary btn-sm suite-pick" data-pick="${id}" data-multi="${multi ? 1 : 0}"><i class="fa-solid fa-images"></i> ${esc(tr('pick', 'Choisir dans la bibliothèque'))}</button>`;
const pfield = (id, label, ph) => `<div class="suite-field"><span>${esc(label)}</span><div class="suite-path"><input type="text" id="${id}" class="settings-select" placeholder="${esc(ph || '/…/piece.stl')}" autocomplete="off">${pickBtn(id, false)}</div></div>`;
const mfield = (id, label, rows) => `<div class="suite-field"><span>${esc(label)}</span><div class="suite-path suite-path-multi"><textarea id="${id}" class="settings-select" rows="${rows || 3}"></textarea>${pickBtn(id, true)}</div></div>`;
const baseName = (p) => String(p || '').replace(/#\d+$/, '').split(/[\\/]/).pop();
const normP = (p) => String(p || '').replace(/\\/g, '/').toLowerCase();
const extOf = (f) => String(f.extension || (f.name || '').split('.').pop() || '').replace('.', '').toUpperCase();
let _srcs = null;
async function loadSrcs() {
    if (_srcs) return _srcs;
    try { _srcs = (typeof _sourcesCache !== 'undefined' && Array.isArray(_sourcesCache) && _sourcesCache.length) ? _sourcesCache : await api('/api/sources'); } catch (e) { _srcs = []; }
    return _srcs;
}
function pagerHtml(cur, n) {
    if (n <= 1) return '';
    const set = new Set([0, n - 1, cur - 1, cur, cur + 1]); if (cur < 2) { set.add(2); set.add(3); } if (cur > n - 3) { set.add(n - 3); set.add(n - 4); }
    const nums = [...set].filter(i => i >= 0 && i < n).sort((a, b) => a - b);
    const b = (i, label, dis, cls, title) => `<button type="button" class="btn btn-ghost btn-sm sp-pg${cls || ''}" data-pg="${i}"${dis ? ' disabled' : ''}${title ? ` title="${esc(title)}" aria-label="${esc(title)}"` : ''}${i === cur && !label.startsWith('<') ? ' aria-current="page"' : ''}>${label}</button>`;
    let h = b(0, '<i class="fa-solid fa-angles-left"></i>', cur === 0, '', tr('pg_first', 'Première page')) + b(Math.max(0, cur - 1), '<i class="fa-solid fa-angle-left"></i>', cur === 0, '', tr('pg_prev', 'Page précédente'));
    let last = -1; nums.forEach(i => { if (last >= 0 && i - last > 1) h += '<span class="sp-gap">…</span>'; h += b(i, String(i + 1), false, i === cur ? ' active' : ''); last = i; });
    return h + b(Math.min(n - 1, cur + 1), '<i class="fa-solid fa-angle-right"></i>', cur === n - 1, '', tr('pg_next', 'Page suivante')) + b(n - 1, '<i class="fa-solid fa-angles-right"></i>', cur === n - 1, '', tr('pg_last', 'Dernière page'));
}
function ensurePicker() {
    let dlg = $('modal-suite-picker');
    if (dlg) return dlg;
    dlg = document.createElement('div'); dlg.id = 'modal-suite-picker'; dlg.className = 'modal hidden';
    dlg.innerHTML = `<div class="modal-content sp-content"><div class="modal-header"><h3><i class="fa-solid fa-images"></i> <span>${esc(tr('pick_title', 'Choisir un modèle'))}</span></h3><button class="modal-close" type="button" id="sp-x">×</button></div>
        <div class="modal-body"><div class="sp-bar"><select id="sp-src" class="settings-select"></select><select id="sp-ext" class="settings-select"></select><input type="search" id="sp-q" class="settings-select" placeholder="${esc(tr('pick_search', 'Rechercher…'))}" autocomplete="off"></div>
        <div id="sp-grid" class="sp-grid"></div><div id="sp-pager" class="sp-pager" role="navigation"></div><div class="sp-foot"><span id="sp-count" class="settings-hint"></span><button type="button" class="btn btn-primary btn-sm" id="sp-ok">${esc(tr('pick_add', 'Ajouter la sélection'))}</button></div></div></div>`;
    document.body.appendChild(dlg);
    dlg.addEventListener('click', (e) => { if (e.target === dlg) closePicker(); });
    $('sp-x').onclick = closePicker;
    return dlg;
}
function closePicker() { if (typeof closeModal === 'function') closeModal('modal-suite-picker'); else $('modal-suite-picker').classList.add('hidden'); }
async function pickModel(multi) {
    ensurePicker();
    const srcs = (await loadSrcs()).filter(x => ['folder', 'smb', 'nfs'].includes(x.type));
    const all = (typeof allFiles !== 'undefined' && Array.isArray(allFiles)) ? allFiles.filter(f => f && f.path) : [];
    const sel = $('sp-src');
    sel.innerHTML = `<option value="">${esc(tr('pick_all', 'Toutes les sources'))} (${all.length.toLocaleString()})</option>` + srcs.map((x, i) => `<option value="${i}">${esc(x.name)}</option>`).join('');
    /* Filtre par format : la liste des extensions présentes (avec leur nombre) est lue dans la bibliothèque déjà chargée. */
    const exts = new Map(); all.forEach(f => { const e = extOf(f); if (e) exts.set(e, (exts.get(e) || 0) + 1); });
    const esel = $('sp-ext');
    esel.innerHTML = `<option value="">${esc(tr('pick_ext_all', 'Tous les formats'))}</option>` + [...exts.entries()].sort((a, b) => b[1] - a[1]).map(([e, n]) => `<option value="${esc(e)}">${esc(e)} (${n.toLocaleString()})</option>`).join('');
    $('sp-q').value = ''; $('sp-ok').style.display = multi ? '' : 'none';
    const chosen = new Set(); let page = 0, list = []; const PS = 48;
    const draw = () => {
        const q = $('sp-q').value.trim().toLowerCase(), si = sel.value, xe = esel.value;
        const root = si === '' ? '' : normP(srcs[+si].path).replace(/\/+$/, '') + '/';
        list = all.filter(f => (!xe || extOf(f) === xe) && (!q || String(f.name || f.path).toLowerCase().includes(q)) && (!root || (normP(f.path) + '/').startsWith(root)));
        const grid = $('sp-grid');
        const pages = Math.max(1, Math.ceil(list.length / PS)); if (page >= pages) page = pages - 1;
        grid.innerHTML = list.slice(page * PS, page * PS + PS).map((f, i) => `<button type="button" class="sp-item${chosen.has(f.path) ? ' sel' : ''}" data-i="${page * PS + i}" title="${esc(f.path)}"><span class="sp-thumb">${f.has_thumb === false ? '<i class="fa-solid fa-cube"></i>' : `<img src="${API}/api/thumb?path=${encodeURIComponent(f.path)}" loading="lazy" alt="" onerror="this.replaceWith(Object.assign(document.createElement('i'),{className:'fa-solid fa-cube'}))">`}</span><span class="sp-name">${esc(f.name || f.path)}</span><small>${esc(extOf(f))}</small></button>`).join('') ||
            `<p class="settings-hint">${esc(all.length ? tr('pick_none', 'Aucun modèle ne correspond.') : tr('pick_empty', 'La bibliothèque est vide ou pas encore chargée.'))}</p>`;
        $('sp-pager').innerHTML = pagerHtml(page, pages);
        $('sp-count').textContent = (list.length ? `${(page * PS + 1).toLocaleString()}–${Math.min(list.length, page * PS + PS).toLocaleString()}` : '0') + ` / ${list.length.toLocaleString()}` + (multi && chosen.size ? ` · ${chosen.size} ✓` : '');
    };
    return new Promise((resolve) => {
        let done = false; const finish = (v) => { if (done) return; done = true; closePicker(); resolve(v); };
        sel.onchange = () => { page = 0; draw(); };
        esel.onchange = () => { page = 0; draw(); };
        $('sp-q').oninput = () => { page = 0; draw(); };
        $('sp-pager').onclick = (e) => { const b = e.target.closest('[data-pg]'); if (!b || b.disabled) return; page = +b.dataset.pg; draw(); $('sp-grid').scrollTop = 0; };
        $('sp-ok').onclick = () => finish([...chosen]);
        $('sp-grid').onclick = (e) => {
            const b = e.target.closest('.sp-item'); if (!b) return;
            const f = list[+b.dataset.i]; if (!f) return;
            if (!multi) { finish([f.path]); return; }
            if (chosen.has(f.path)) chosen.delete(f.path); else chosen.add(f.path);
            b.classList.toggle('sel', chosen.has(f.path)); $('sp-count').textContent = `${(page * PS + 1).toLocaleString()}–${Math.min(list.length, page * PS + PS).toLocaleString()} / ${list.length.toLocaleString()} · ${chosen.size} ✓`;
        };
        const mo = new MutationObserver(() => { if ($('modal-suite-picker').classList.contains('hidden')) { mo.disconnect(); finish(null); } });
        mo.observe($('modal-suite-picker'), { attributes: true, attributeFilter: ['class'] });
        draw();
        if (typeof openModal === 'function') openModal('modal-suite-picker'); else $('modal-suite-picker').classList.remove('hidden');
    });
}
document.addEventListener('click', async (e) => {
    const b = e.target.closest('.suite-pick'); if (!b) return;
    const target = $(b.dataset.pick); if (!target) return;
    const multi = b.dataset.multi === '1';
    const got = await pickModel(multi);
    if (!got || !got.length) return;
    if (multi) { const cur = target.value.split(/\n|;/).map(x => x.trim()).filter(Boolean); got.forEach(p => { if (!cur.includes(p)) cur.push(p); }); target.value = cur.join('\n'); }
    else target.value = got[0];
    target.dispatchEvent(new Event('input', { bubbles: true }));
});
const val = (id) => ($(id) ? $(id).value.trim() : '');
const lines = (id) => val(id).split(/\n|;/).map(s => s.trim()).filter(Boolean);
function wire(box, id, fn) {
    const b = $(id); if (!b) return;
    b.onclick = async () => {
        /* Repère visuel : bouton « occupé » + bandeau d'activité (roue, texte, barre) tant que la tâche tourne. */
        const w = document.createElement('div');
        w.className = 'su-work su-work-auto'; w.setAttribute('role', 'status'); w.setAttribute('aria-live', 'polite');
        w.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>' + esc(tr('working', 'Calcul en cours…')) + '</span><span class="su-work-bar" aria-hidden="true"><i></i></span>';
        const anchor = b.closest('.su-line') || b;
        anchor.insertAdjacentElement('afterend', w);
        b.disabled = true; b.classList.add('su-btn-busy'); b.setAttribute('aria-busy', 'true');
        box.querySelectorAll('.suite-msg').forEach(m => { m.textContent = ''; });
        try { await fn(); } catch (e) { note(box, e.message, true); }
        w.remove(); b.disabled = false; b.classList.remove('su-btn-busy'); b.removeAttribute('aria-busy');
    };
}
/* Avancement d'une tâche : { done, total, message } (ou un nombre 0..1) → texte lisible, jamais « NaN ». */
function pct(p) {
    if (p == null) return '';
    if (typeof p === 'number') return Math.round(p * 100) + ' %';
    if (p.total) return Math.round(Math.min(1, p.done / p.total) * 100) + ' %' + (p.message ? ' — ' + p.message : '');
    return p.message || '';
}
async function waitJob(id, box) {
    for (let i = 0; i < 240; i++) {
        const j = await api(`/api/jobs/${id}`);
        prog(box, `${j.state || ''} ${pct(j.progress)}`);
        if (['done', 'failed', 'cancelled'].includes(j.state)) { if (j.state !== 'done') throw new Error(j.error || j.state); return j.result; }
        await new Promise(r => setTimeout(r, 1000));
    }
    throw new Error('timeout');
}

/* ── aides pures (testées dans un vrai navigateur) ── */
const H = {
    snap(v, step) { step = step > 0 ? step : 1; return Math.round(v / step) * step; },
    bounds(pts) {
        if (!pts.length) return { c: [0, 0, 0], r: 1 };
        const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
        for (const p of pts) for (let k = 0; k < 3; k++) { if (p[k] < lo[k]) lo[k] = p[k]; if (p[k] > hi[k]) hi[k] = p[k]; }
        const c = lo.map((v, k) => (v + hi[k]) / 2);
        return { c, r: Math.max(1e-6, Math.hypot(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]) / 2) };
    },
    /* Z vers le haut ; yaw autour de Z, pitch autour de X. Retourne [x écran, y écran (vers le bas), profondeur]. */
    project(p, c, yaw, pitch) {
        const x = p[0] - c[0], y = p[1] - c[1], z = p[2] - c[2];
        const cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
        const x1 = x * cy - y * sy, y1 = x * sy + y * cy;
        return [x1, -(z * cp + y1 * sp), y1 * cp - z * sp];
    },
    /* 12 arêtes du parallélépipède d'une pièce posée sur le plateau (x, y = coin avant-gauche, z de 0 à h). */
    boxEdges(a) {
        const x0 = a.x, x1 = a.x + a.w, y0 = a.y, y1 = a.y + a.d, z0 = 0, z1 = Math.max(0.5, a.h || 0);
        const v = [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]];
        return [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7]].map(e => [v[e[0]], v[e[1]]]);
    },
    rotate90(it) { return Object.assign({}, it, { w: it.d, d: it.w, rot: it.rot === 90 ? 0 : 90 }); },
    /* Contour réel : prisme (bas + haut + montants) d'une pièce dont le serveur a fourni les anneaux relatifs à sa boîte. */
    shapeEdges(a) {
        const z0 = 0, z1 = Math.max(0.5, a.h || 0), out = [];
        for (const ring of (a.outline || [])) {
            const n = ring.length; if (n < 3) continue;
            const P = (k, z) => [a.x + ring[k][0], a.y + ring[k][1], z], stride = Math.max(1, Math.ceil(n / 24));
            for (let k = 0; k < n; k++) { const m = (k + 1) % n; out.push([P(k, z0), P(m, z0)], [P(k, z1), P(m, z1)]); if (k % stride === 0) out.push([P(k, z0), P(k, z1)]); }
        }
        return out;
    },
    /* Deux contours (anneaux relatifs + décalage de la pièce) se recouvrent-ils ? Croisement strict d'arêtes ou sommet à l'intérieur. */
    polyOverlap(a, b) {
        const rings = (it) => (it.outline || []).map(r => r.map(q => [it.x + q[0], it.y + q[1]]));
        const A = rings(a), B = rings(b), e = 1e-6;
        const cross = (p, q, r) => (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]);
        const inter = (p1, p2, p3, p4) => { const d1 = cross(p3, p4, p1), d2 = cross(p3, p4, p2), d3 = cross(p1, p2, p3), d4 = cross(p1, p2, p4); return ((d1 > e && d2 < -e) || (d1 < -e && d2 > e)) && ((d3 > e && d4 < -e) || (d3 < -e && d4 > e)); };
        const inside = (pt, ring) => { let c = false; for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) { const pi = ring[i], pj = ring[j]; if ((pi[1] > pt[1]) !== (pj[1] > pt[1]) && pt[0] < (pj[0] - pi[0]) * (pt[1] - pi[1]) / (pj[1] - pi[1]) + pi[0]) c = !c; } return c; };
        for (const ra of A) for (const rb of B) {
            for (let i = 0; i < ra.length; i++) for (let j = 0; j < rb.length; j++) if (inter(ra[i], ra[(i + 1) % ra.length], rb[j], rb[(j + 1) % rb.length])) return true;
            if (inside(ra[0], rb) || inside(rb[0], ra)) return true;
        }
        return false;
    },
    clamp(it, plate) { return Object.assign({}, it, { x: Math.max(0, Math.min(it.x, plate.w - it.w)), y: Math.max(0, Math.min(it.y, plate.d - it.d)) }); },
    align(it, plate, mode) {
        const o = Object.assign({}, it);
        if (mode === 'left') o.x = 0; else if (mode === 'right') o.x = plate.w - it.w;
        else if (mode === 'front') o.y = 0; else if (mode === 'back') o.y = plate.d - it.d;
        else if (mode === 'center-x') o.x = (plate.w - it.w) / 2; else if (mode === 'center-y') o.y = (plate.d - it.d) / 2;
        return o;
    },
    /* Même règles que le serveur (`check_layout`) ; le serveur reste l'autorité. */
    issues(list, plate) {
        const out = [], e = 1e-6;
        list.forEach((a, i) => {
            if (a.x < -e || a.y < -e || a.x + a.w > plate.w + e || a.y + a.d > plate.d + e) out.push({ i, issue: 'out_of_plate' });
            if ((a.h || 0) > plate.z + e) out.push({ i, issue: 'too_tall' });
            for (let j = i + 1; j < list.length; j++) {
                const b = list[j];
                if (a.x < b.x + b.w - e && b.x < a.x + a.w - e && a.y < b.y + b.d - e && b.y < a.y + a.d - e) {
                    if (a.outline && b.outline && !H.polyOverlap(a, b)) continue;                 // boîtes qui se recouvrent mais pas les vraies formes : imbrication valide
                    out.push({ i, j, issue: 'overlap' });
                }
            }
        });
        return out;
    },
};
const COLORS = { removed: '#e5484d', added: '#30a46c', same: '#8b8d98' };

/* Nuage de points 3D (diff coloré) : canvas, rotation au glisser, zoom à la molette. Retourne { draw, state }. */
function cloudView(host, points, edges) {
    const all = [].concat(points.removed || [], points.added || [], points.same || []);
    const { c, r } = H.bounds(all);
    const st = { yaw: -0.6, pitch: 0.5, zoom: 1, mode: 'points', show: { removed: true, added: true, same: true } };
    const hasEdges = !!edges && ['removed', 'added', 'same'].some(k => (edges[k] || []).length);
    host.innerHTML = `<canvas class="suite-cloud" width="720" height="440" aria-label="${esc(tr('cloud_label', 'Comparaison 3D en nuage de points'))}"></canvas>
        <div class="suite-legend">${['removed', 'added', 'same'].map(k => `<label><input type="checkbox" data-k="${k}" checked> <span class="suite-dot" style="background:${COLORS[k]}"></span> ${esc(tr('cloud_' + k, { removed: 'Retiré', added: 'Ajouté', same: 'Inchangé' }[k]))} (${(points[k] || []).length})</label>`).join('')}
        <button type="button" class="btn btn-ghost btn-sm" data-view="iso">${esc(tr('view_iso', 'Vue 3D'))}</button><button type="button" class="btn btn-ghost btn-sm" data-view="top">${esc(tr('view_top', 'Dessus'))}</button><button type="button" class="btn btn-ghost btn-sm" data-view="front">${esc(tr('view_front', 'Face'))}</button>
        ${hasEdges ? `<span class="suite-mode"><button type="button" class="btn btn-primary btn-sm" data-mode="points">${esc(tr('mode_points', 'Points'))}</button><button type="button" class="btn btn-ghost btn-sm" data-mode="wire">${esc(tr('mode_wire', 'Fil de fer'))}</button></span>` : ''}</div>`;
    const cv = host.querySelector('canvas'), g = cv.getContext('2d');
    function draw() {
        g.clearRect(0, 0, cv.width, cv.height);
        const sc = Math.min(cv.width, cv.height) / (2.2 * r) * st.zoom, ox = cv.width / 2, oy = cv.height / 2;
        for (const k of ['same', 'removed', 'added']) {
            if (!st.show[k]) continue;
            if (st.mode === 'wire') {
                g.strokeStyle = COLORS[k]; g.globalAlpha = k === 'same' ? 0.4 : 0.95; g.lineWidth = k === 'same' ? 1 : 1.6; g.beginPath();
                for (const e of ((edges || {})[k] || [])) { const p = H.project([e[0], e[1], e[2]], c, st.yaw, st.pitch), q = H.project([e[3], e[4], e[5]], c, st.yaw, st.pitch); g.moveTo(ox + p[0] * sc, oy + p[1] * sc); g.lineTo(ox + q[0] * sc, oy + q[1] * sc); }
                g.stroke();
                continue;
            }
            g.fillStyle = COLORS[k]; g.globalAlpha = k === 'same' ? 0.35 : 0.95;
            const sz = k === 'same' ? 2 : 3;
            for (const p of (points[k] || [])) { const q = H.project(p, c, st.yaw, st.pitch); g.fillRect(ox + q[0] * sc - sz / 2, oy + q[1] * sc - sz / 2, sz, sz); }
        }
        g.globalAlpha = 1;
    }
    let drag = null;
    cv.onpointerdown = (e) => { drag = [e.clientX, e.clientY]; cv.setPointerCapture(e.pointerId); };
    cv.onpointermove = (e) => { if (!drag) return; st.yaw += (e.clientX - drag[0]) * 0.01; st.pitch = Math.max(-1.5, Math.min(1.5, st.pitch + (e.clientY - drag[1]) * 0.01)); drag = [e.clientX, e.clientY]; draw(); };
    cv.onpointerup = cv.onpointercancel = () => { drag = null; };
    cv.onwheel = (e) => { e.preventDefault(); st.zoom = Math.max(0.3, Math.min(8, st.zoom * (e.deltaY < 0 ? 1.15 : 1 / 1.15))); draw(); };
    host.querySelector('.suite-legend').onclick = (e) => {
        const cb = e.target.closest('input[data-k]'); if (cb) { st.show[cb.dataset.k] = cb.checked; draw(); return; }
        const md = e.target.closest('[data-mode]');
        if (md) { st.mode = md.dataset.mode; host.querySelectorAll('[data-mode]').forEach(x => { x.className = 'btn btn-sm ' + (x.dataset.mode === st.mode ? 'btn-primary' : 'btn-ghost'); }); draw(); return; }
        const b = e.target.closest('[data-view]'); if (!b) return;
        const v = { iso: [-0.6, 0.5], top: [0, 1.5], front: [0, 0] }[b.dataset.view]; st.yaw = v[0]; st.pitch = v[1]; st.zoom = 1; draw();
    };
    draw();
    return { draw, state: st, canvas: cv };
}

const TABS = {};
TABS.jobs = { fb: 'Tâches', icon: 'list-check', async render(box) {
    const d = await api('/api/jobs');
    box.innerHTML = table(d.jobs, [['kind', 'Type'], ['state', 'État'], ['progress', '%', v => pct(v)], ['name', 'Détail'], ['error', 'Erreur']]);
} };
TABS.db = { fb: 'Base de données', icon: 'database', async render(box) {
    const d = await api('/api/db/migrations');
    box.innerHTML = `<p class="settings-hint">${esc(tr('schema', 'Version du schéma'))} : <b>${esc(d.user_version)}</b> / ${esc(d.latest)} — ${d.migrations.every(m => !m.pending) ? esc(tr('db_ok', 'toutes les migrations sont appliquées')) : esc(tr('db_pending', 'des migrations sont en attente'))}</p>` +
        table(d.migrations, [['version', 'N°'], ['name', 'Migration'], ['ok', 'État', (v, r) => r.pending ? '⏳' : (v ? '✓' : '✗')], ['applied_at', 'Appliquée le', v => v ? fmt(v) : ''], ['error', 'Erreur']]);
} };
/* Journal d'audit : quelques lignes à la fois (25 par défaut), le reste se pagine ; l'affichage ne bloque jamais sur le chargement. */
let auditSize = 25;
TABS.audit = { fb: 'Journal d\'audit', icon: 'clipboard-list', async render(box, page) {
    page = page || 0;
    box.innerHTML = `<div class="su-line su-audit-bar"><label class="suite-field suite-field-sm"><span>${esc(tr('audit_rows', 'Lignes par page'))}</span><select id="su-asize" class="settings-select">${[10, 25, 50, 100, 200].map(n => `<option value="${n}"${n === auditSize ? ' selected' : ''}>${n}</option>`).join('')}</select></label>` +
        `<a class="btn btn-ghost btn-sm" href="${API}/api/audit/export.csv">${esc(tr('audit_csv', 'Exporter en CSV'))}</a></div><p class="settings-hint" id="su-ainfo"><i class="fa-solid fa-spinner fa-spin"></i> ${esc(tr('loading', 'Chargement…'))}</p><div id="su-atable"></div><div class="sp-pager" id="su-apager"></div>`;
    $('su-asize').onchange = (e) => { auditSize = Number(e.target.value) || 25; TABS.audit.render(box, 0); };
    $('su-apager').onclick = (e) => { const b = e.target.closest('[data-pg]'); if (b && !b.disabled) TABS.audit.render(box, Number(b.dataset.pg)); };
    const d = await api(`/api/audit?limit=${auditSize}&offset=${page * auditSize}`);
    const pages = Math.max(1, Math.ceil((d.total || 0) / auditSize));
    if (page > pages - 1) return TABS.audit.render(box, pages - 1);
    const from = d.total ? page * auditSize + 1 : 0, to = page * auditSize + d.count;
    $('su-ainfo').textContent = `${from}–${to} / ${d.total} ${tr('audit_events', 'évènement(s)')}${d.remote ? ' — ' + d.remote + ' ' + tr('remote', 'via API ou pair') : ''}`;
    $('su-atable').innerHTML = table(d.rows, [['ts', 'Date', fmt], ['actor', 'Acteur'], ['action', 'Action'], ['target', 'Cible'], ['ip', 'IP']]);
    $('su-apager').innerHTML = pagerHtml(page, pages);
} };
TABS.team = { fb: 'Équipes', icon: 'users', async render(box) {
    const d = await api('/api/team');
    box.innerHTML = `<h4>${esc(tr('members', 'Membres'))}</h4>` + table(d.members, [['name', 'Invité'], ['role', 'Rôle (' + d.roles.join(' / ') + ')']]) +
        `<h4>${esc(tr('workspaces', 'Espaces de travail'))}</h4>` + table(d.workspaces, [['name', 'Nom'], ['members', 'Membres', v => (v || []).length], ['items', 'Éléments', v => (v || []).length]]) +
        `<h4>${esc(tr('perms', 'Permissions'))}</h4>` + table(d.permissions, [['subject_type', 'Type'], ['subject', 'Sujet'], ['level', 'Niveau']]);
} };
TABS.sessions = { fb: 'Sessions', icon: 'shield-halved', async render(box) {
    const d = await api('/api/sessions');
    const ua = (v) => String(v || '').replace(/\(.*?\)/g, '').trim().slice(0, 60);
    box.innerHTML = `<p class="settings-hint">${esc(tr('sess_hint', 'Appareils connectés à votre compte. Une session révoquée est coupée à sa prochaine requête (au plus'))} ${esc(d.check_every_s)} s).</p>` +
        (d.sessions.length ? `<div class="suite-scroll"><table class="suite-table"><thead><tr><th>${esc(tr('s_kind', 'Type'))}</th><th>IP</th><th>${esc(tr('s_agent', 'Navigateur'))}</th><th>${esc(tr('s_last', 'Dernière activité'))}</th><th></th></tr></thead><tbody>${d.sessions.map(x =>
            `<tr><td>${esc(x.kind === 'viewer' ? tr('s_guest', 'Invité') : tr('s_owner', 'Propriétaire'))}${x.current ? ' <b>(' + esc(tr('s_current', 'cette session')) + ')</b>' : ''}</td>${cell(x.ip)}${cell(ua(x.ua))}${cell(fmt(x.last_seen))}<td>${x.current ? '' : `<button type="button" class="btn btn-ghost btn-sm" data-revoke="${esc(x.sid)}">${esc(tr('s_revoke', 'Révoquer'))}</button>`}</td></tr>`).join('')}</tbody></table></div>` :
            `<p class="settings-hint">${esc(tr('empty', 'Rien à afficher pour le moment.'))}</p>`) + btn('su-srevall', tr('s_revoke_others', 'Déconnecter tous les autres appareils'), 'btn-ghost');
    box.onclick = async (e) => { const b = e.target.closest('[data-revoke]'); if (!b) return; try { await api(`/api/sessions/${b.dataset.revoke}/revoke`, {}); await TABS.sessions.render(box); } catch (x) { note(box, x.message, true); } };
    wire(box, 'su-srevall', async () => { const r = await api('/api/sessions/revoke-others', {}); await TABS.sessions.render(box); note(box, `${r.revoked} ✓`); });
} };
/* Toutes les notifications : filtres par rubrique (filament faible, à recommander, pièces, impression…), recherche, pagination. Ouvert depuis « Tout voir » du centre de notifications. */
const NTF = { cat: '', state: 'all', q: '', source: '', page: 0, size: 25 };
const ntfSrc = (s) => s === '@license' ? tr('ntf_src_license', 'Licences') : s === '@digest' ? tr('ntf_src_digest', 'Résumé périodique') : s;
const NTF_CATS = [['filament_low', 'Filament faible', 'circle-exclamation'], ['restock', 'Filament à recommander', 'cart-shopping'], ['parts', 'Pièces à recommander', 'screwdriver-wrench'],
    ['print', 'Impressions', 'print'], ['maintenance', 'Maintenance', 'wrench'], ['planning', 'Planning', 'calendar-check'], ['update', 'Mises à jour', 'arrow-up-right-dots'], ['other', 'Autres', 'bell']];
const ntfText = (n) => (typeof window.stellioNotifText === 'function' ? window.stellioNotifText(n) : { title: n.title, message: n.message });
TABS.notifications = { fb: 'Notifications', icon: 'bell', async render(box) {
    const qs = new URLSearchParams({ limit: NTF.size, offset: NTF.page * NTF.size, state: NTF.state, q: NTF.q }); if (NTF.cat) qs.set('category', NTF.cat); if (NTF.source) qs.set('source', NTF.source);
    const d = await api('/api/notifications/all?' + qs);
    const pages = Math.max(1, Math.ceil((d.total || 0) / NTF.size));
    if (NTF.page > pages - 1) { NTF.page = pages - 1; return TABS.notifications.render(box); }
    const chip = (k, label, n, active) => `<button type="button" class="ntf-chip${active ? ' active' : ''}" data-ntf="${esc(k)}">${esc(label)} <b>${n}</b></button>`;
    const chips = chip('', tr('ntf_all', 'Toutes'), d.all, !NTF.cat && NTF.state === 'all') + chip('@unread', tr('ntf_unread', 'Non lues'), d.unread, NTF.state === 'unread' && !NTF.cat) +
        NTF_CATS.filter(c => d.counts[c[0]] > 0 || NTF.cat === c[0]).map(c => chip(c[0], tr('ntf_' + c[0], c[1]), d.counts[c[0]], NTF.cat === c[0])).join('');
    const icon = (n) => (NTF_CATS.find(c => c[0] === n.category) || NTF_CATS[7])[2];
    const when = (s) => { try { return new Date(s + 'Z').toLocaleString(); } catch (e) { return s; } };
    box.innerHTML = `<div class="su-line"><label class="suite-field suite-field-md"><span>${esc(tr('ntf_search', 'Rechercher'))}</span><input type="text" id="su-nq" class="settings-select" value="${esc(NTF.q)}" placeholder="${esc(tr('ntf_search_ph', 'Titre ou message…'))}" autocomplete="off"></label>` +
        `<label class="suite-field suite-field-sm"><span>${esc(tr('ntf_source', 'Source'))}</span><select id="su-nsrc" class="settings-select"><option value="">${esc(tr('ntf_all_sources', 'Toutes'))}</option>${Object.keys(d.sources || {}).sort().map(s => `<option value="${esc(s)}"${NTF.source === s ? ' selected' : ''}>${esc(ntfSrc(s))} (${d.sources[s]})</option>`).join('')}</select></label>` + btn('su-nreadall', tr('ntf_mark_all', 'Tout marquer comme lu'), 'btn-secondary') + btn('su-nclear', tr('ntf_clear_read', 'Supprimer les lues'), 'btn-secondary') + '</div>' +
        `<div class="ntf-chips">${chips}</div>` +
        (d.notifications.length ? `<div class="ntf-list">${d.notifications.map(n => `<div class="ntf-row${n.is_read ? '' : ' unread'}" data-nid="${n.id}" data-link="${esc(n.link_page || '')}"><i class="fa-solid fa-${icon(n)} ntf-ico"></i>` +
            `<div class="ntf-body"><div class="ntf-title">${esc(ntfText(n).title)}</div>${ntfText(n).message ? `<div class="ntf-msg">${esc(ntfText(n).message)}</div>` : ''}<div class="ntf-meta"><span class="ntf-src">${esc(ntfSrc(n.source))}</span> ${esc(when(n.created_at))} · ${esc(tr('ntf_' + n.category, (NTF_CATS.find(c => c[0] === n.category) || NTF_CATS[7])[1]))}</div></div>` +
            `<button type="button" class="ntf-del" data-ndel="${n.id}" title="${esc(tr('ntf_delete', 'Supprimer'))}" aria-label="${esc(tr('ntf_delete', 'Supprimer'))}"><i class="fa-solid fa-xmark"></i></button></div>`).join('')}</div>`
            : `<p class="settings-hint">${esc(tr('ntf_empty', 'Aucune notification dans cette rubrique.'))}</p>`) +
        `<div class="su-pager" id="su-npager">${pagerHtml(NTF.page, pages)}</div>`;
    const again = () => TABS.notifications.render(box);
    box.querySelector('.ntf-chips').onclick = (e) => { const c = e.target.closest('[data-ntf]'); if (!c) return; const k = c.dataset.ntf; NTF.page = 0;
        if (k === '') { NTF.cat = ''; NTF.state = 'all'; } else if (k === '@unread') { NTF.cat = ''; NTF.state = 'unread'; } else { NTF.cat = k; NTF.state = 'all'; } again(); };
    $('su-nsrc').onchange = (e) => { NTF.source = e.target.value; NTF.page = 0; again(); };
    let tm = null; $('su-nq').oninput = (e) => { clearTimeout(tm); tm = setTimeout(async () => { NTF.q = e.target.value.trim(); NTF.page = 0; await again(); const i = $('su-nq'); if (i) { i.focus(); i.setSelectionRange(i.value.length, i.value.length); } }, 300); };
    $('su-npager').onclick = (e) => { const b = e.target.closest('[data-pg]'); if (b && !b.disabled) { NTF.page = Number(b.dataset.pg); again(); } };
    wire(box, 'su-nreadall', async () => { await api('/api/notifications/read-all', {}); if (window.loadNotifications) window.loadNotifications(); await again(); });
    wire(box, 'su-nclear', async () => { await api('/api/notifications/clear-read', {}); await again(); });
    box.querySelector('.ntf-list')?.addEventListener('click', async (e) => {
        const del = e.target.closest('[data-ndel]');
        if (del) { e.stopPropagation(); await api(`/api/notifications/${del.dataset.ndel}`, undefined, 'DELETE'); if (window.loadNotifications) window.loadNotifications(); return again(); }
        const row = e.target.closest('[data-nid]'); if (!row) return;
        if (typeof window.handleNotificationClick === 'function') await window.handleNotificationClick(Number(row.dataset.nid), row.dataset.link || null);
        else await api(`/api/notifications/${row.dataset.nid}/read`, {});
        if (!row.dataset.link) again();
    });
} };
/* Collections : une section dépliable par collection (nom, nombre de fichiers) ; au dépliage, la liste des fichiers avec miniature, quantité et ouverture de la fiche. */
TABS.collections = { fb: 'Collections', icon: 'layer-group', plain: true, async render(box) {
    const d = await api('/api/collections');
    const open0 = new Set([...box.querySelectorAll('.inv-section:not(.inv-collapsed)')].map(s => s.dataset.cid));
    const sub = (c) => `${c.count} ${tr(c.count === 1 ? 'col_file' : 'col_files', c.count === 1 ? 'fichier' : 'fichiers')}${c.pieces > c.count ? ' · ' + c.pieces + ' ' + tr('col_pieces', 'pièces') : ''}${c.description ? ' · ' + c.description : ''}`;
    box.innerHTML = `<div class="col-root"><div class="bp-card col-new"><div class="su-line"><label class="suite-field suite-field-md"><span>${esc(tr('col_new', 'Nouvelle collection'))}</span><input type="text" id="su-cname" class="settings-select" maxlength="80" autocomplete="off"></label>` +
        btn('su-cadd', tr('col_create', 'Créer'), 'btn-primary') + '</div></div>' +
        (d.collections.length ? d.collections.map(c => `<div class="inv-section inv-collapsed" data-cid="${c.id}" style="margin-top:14px;">` +
            `<div class="source-banner source-banner-collection" style="--cc:${esc(c.color || '#4ea1d3')}">` +
            `<button type="button" class="inv-toggle" aria-expanded="false" title="${esc(tr('col_expand', 'Déplier'))}" aria-label="${esc(tr('col_expand', 'Déplier'))}"><i class="fa-solid fa-chevron-down"></i></button>` +
            `<div class="source-banner-icon"><i class="fa-solid fa-layer-group"></i></div>` +
            `<div style="flex:1; min-width:0;"><div style="font-weight:600; font-size:calc(14px * var(--fs, 1));">${esc(c.name)}</div><div class="source-banner-sub">${esc(sub(c))}</div></div>` +
            `<button type="button" class="btn btn-ghost btn-sm" data-cdel="${c.id}" data-cname="${esc(c.name)}"><i class="fa-solid fa-trash"></i> <span>${esc(tr('col_delete', 'Supprimer'))}</span></button></div>` +
            `<div class="col-body" data-cbody="${c.id}"></div></div>`).join('')
            : `<p class="settings-hint">${esc(tr('col_empty', "Aucune collection pour l'instant. Créez-en une ci-dessus, puis ajoutez-y des fichiers depuis la bibliothèque."))}</p>`) + '</div>';
    const root = box.querySelector('.col-root');   // recréé à chaque affichage : les écouteurs ne s'empilent pas
    const fill = async (sec) => {
        const body = sec.querySelector('.col-body'); body.innerHTML = '<p class="settings-hint">…</p>';
        try {
            const c = await api(`/api/collections/${sec.dataset.cid}`);
            body.innerHTML = c.files.length ? `<div class="col-files">${c.files.map(f => `<div class="col-file${f.missing ? ' missing' : ''}" data-cpath="${esc(f.path)}" role="button" tabindex="0">` +
                `<span class="col-thumb"><img src="${API}/api/thumb?path=${encodeURIComponent(f.path)}" loading="lazy" alt="" onerror="this.replaceWith(Object.assign(document.createElement('i'),{className:'fa-solid fa-cube'}))"></span>` +
                `<span class="col-name">${esc(f.name)}</span>${f.quantity > 1 ? `<span class="col-qty">×${f.quantity}</span>` : ''}${f.missing ? `<span class="col-miss" title="${esc(tr('col_missing', 'Fichier introuvable'))}"><i class="fa-solid fa-triangle-exclamation"></i></span>` : ''}</div>`).join('')}</div>`
                : `<p class="settings-hint">${esc(tr('col_no_files', 'Cette collection est vide.'))}</p>`;
        } catch (e) { body.innerHTML = `<p class="settings-hint">${esc(e.message || tr('unavailable', 'Indisponible.'))}</p>`; }
    };
    const toggle = (sec) => { const collapsed = !sec.classList.contains('inv-collapsed'); sec.classList.toggle('inv-collapsed', collapsed);
        const b = sec.querySelector('.inv-toggle'); b.setAttribute('aria-expanded', String(!collapsed)); const l = tr(collapsed ? 'col_expand' : 'col_collapse', collapsed ? 'Déplier' : 'Replier'); b.title = l; b.setAttribute('aria-label', l); if (!collapsed) fill(sec); };
    root.addEventListener('click', async (e) => {
        const del = e.target.closest('[data-cdel]');
        if (del) { e.stopPropagation();
            const ok = typeof showConfirmDialog === 'function' ? await showConfirmDialog(tr('col_delete_confirm', 'Supprimer la collection « {name} » ? Les fichiers ne sont pas supprimés.').replace('{name}', del.dataset.cname), { danger: true, confirmLabel: tr('col_delete', 'Supprimer') }) : true;
            if (!ok) return;
            try { await api('/api/collections/delete', { id: Number(del.dataset.cdel) }); await TABS.collections.render(box); } catch (x) { note(box, x.message, true); }
            return; }
        const f = e.target.closest('[data-cpath]');
        if (f) { if (typeof window.openFileInfoModal === 'function') window.openFileInfoModal(f.dataset.cpath); return; }
        const bn = e.target.closest('.source-banner-collection'); if (bn) toggle(bn.closest('.inv-section'));
    });
    root.addEventListener('keydown', (e) => { if (e.key !== 'Enter' && e.key !== ' ') return; const f = e.target.closest('[data-cpath]'); if (f && typeof window.openFileInfoModal === 'function') { e.preventDefault(); window.openFileInfoModal(f.dataset.cpath); } });
    open0.forEach(id => { const s = box.querySelector(`.inv-section[data-cid="${id}"]`); if (s) toggle(s); });
    wire(box, 'su-cadd', async () => { const n = val('su-cname').trim(); if (!n) return; await api('/api/collections/save', { name: n }); await TABS.collections.render(box); });
} };
TABS.compat = { fb: 'Compatibilité', icon: 'print', async render(box) {
    box.innerHTML = '<div class="su-line">' + pfield('su-cp', tr('path', 'Chemin du modèle'), '/…/piece.stl') + field('su-cm', tr('material', 'Matière'), 'PLA', 'suite-field-md') + btn('su-cgo', tr('check', 'Vérifier')) + '</div><div id="su-cout"></div>';
    wire(box, 'su-cgo', async () => {
        const d = await api(`/api/compat/model?path=${encodeURIComponent(val('su-cp'))}&material=${encodeURIComponent(val('su-cm'))}`);
        $('su-cout').innerHTML = table(d.printers, [['printer', 'Imprimante'], ['status', 'Verdict'], ['checks', 'Détails', v => (v || []).filter(c => c.status !== 'ok').map(c => c.message).join(' · ')]]);
    });
} };
/* Organisation : des règles « si… alors… » (étiquette, collection ou dossier suggéré). Aperçu d'abord, rien n'est écrit tant qu'on n'applique pas. */
const ORG_FIELD = { ext: ['Extension', 'stl  ou  stl, 3mf'], name: ['Nom du fichier', 'boîte'], license_commercial: ['Usage commercial', ''], material: ['Matière', 'PLA'], printer: ['Imprimante', 'Ender'],
    size_mb: ['Taille (Mo)', '50'], printed: ['Déjà imprimé', ''], author: ['Auteur', 'nom'], category: ['Catégorie (étiquette existante)', 'Figurines'], age_days: ['Ancienneté (jours)', '90'] };
const ORG_OP = { is: 'est', in: 'est parmi', contains: 'contient', not_contains: 'ne contient pas', gt: 'est supérieur à', lt: 'est inférieur à' };
const ORG_ACTION = { tag: ['Poser l\'étiquette', 'Nom de l\'étiquette'], collection: ['Ajouter à la collection', 'Nom de la collection'], suggest_folder: ['Suggérer le dossier', 'Dossier (relatif), ex. Figurines/Dragons'] };
const ORG_CHOICES = { license_commercial: [['yes', 'Oui'], ['no', 'Non'], ['unknown', 'Inconnu']], printed: [['yes', 'Oui'], ['no', 'Non']] };
TABS.organize = { fb: 'Organisation', icon: 'folder-tree', async render(box) {
    const d = await api('/api/organize/rules');
    const fl = (k) => tr('org_f_' + k, (ORG_FIELD[k] || [k])[0]), ol = (k) => tr('org_o_' + k, ORG_OP[k] || k), al = (k) => tr('org_a_' + k, (ORG_ACTION[k] || [k])[0]);
    const yn = (v) => ({ yes: tr('yes', 'Oui'), no: tr('no', 'Non'), unknown: tr('unknown', 'Inconnu') }[v] || v);
    const fields = Object.keys(d.fields).filter(k => ORG_FIELD[k]);
    const sel = (id, opts, cls) => `<select id="${id}" class="settings-select ${cls || ''}">${opts.map(o => `<option value="${esc(o[0])}">${esc(o[1])}</option>`).join('')}</select>`;
    const rules = d.rules || [];
    box.innerHTML = `<p class="settings-hint">${esc(tr('org_intro', 'Une règle dit : « si un fichier correspond à ce critère, alors lui poser une étiquette, l\'ajouter à une collection ou suggérer un dossier ». Lancez l\'aperçu pour voir ce qui changerait : rien n\'est écrit tant que vous n\'appliquez pas, et le dernier lot peut être annulé. Aucun fichier n\'est déplacé ni supprimé.'))}</p>` +
        `<h4>${esc(tr('org_rules', 'Règles'))} <span class="su-chip">${rules.length}</span></h4>` +
        (rules.length ? `<div class="suite-scroll"><table class="suite-table"><thead><tr><th>${esc(tr('org_name', 'Nom'))}</th><th>${esc(tr('org_if', 'Si…'))}</th><th>${esc(tr('org_then', 'Alors…'))}</th><th></th></tr></thead><tbody>` +
            rules.map(r => `<tr><td>${esc(r.name)}</td><td>${esc(fl(r.field))} ${esc(ol(r.op))} <b>${esc(ORG_CHOICES[r.field] ? yn(r.value) : r.value)}</b></td><td>${esc(al(r.action))} <b>${esc(r.target || '')}</b></td>` +
                `<td><button type="button" class="btn btn-ghost btn-sm su-danger" data-odel="${esc(r.id)}">${esc(tr('delete', 'Supprimer'))}</button></td></tr>`).join('') + '</tbody></table></div>'
            : `<p class="settings-hint">${esc(tr('org_none', 'Aucune règle pour l\'instant : ajoutez-en une ci-dessous.'))}</p>`) +
        `<h4>${esc(tr('org_add_title', 'Ajouter une règle'))}</h4>` +
        `<div class="su-line su-org-form">` +
        `<label class="suite-field suite-field-md"><span>${esc(tr('org_if', 'Si…'))}</span>${sel('su-of', fields.map(k => [k, fl(k)]))}</label>` +
        `<label class="suite-field suite-field-md"><span>${esc(tr('org_op', 'Condition'))}</span><select id="su-oo" class="settings-select"></select></label>` +
        `<label class="suite-field suite-field-md"><span>${esc(tr('org_value', 'Valeur'))}</span><span id="su-ovbox"></span></label>` +
        `<label class="suite-field suite-field-md"><span>${esc(tr('org_then', 'Alors…'))}</span>${sel('su-oa', (d.actions || []).filter(k => ORG_ACTION[k]).map(k => [k, al(k)]))}</label>` +
        `<label class="suite-field suite-field-md"><span id="su-otl">${esc(tr('org_target', 'Nom'))}</span><input type="text" id="su-ot" class="settings-select" maxlength="80"></label>` +
        `<label class="suite-field suite-field-md"><span>${esc(tr('org_rname', 'Nom de la règle (facultatif)'))}</span><input type="text" id="su-on" class="settings-select" maxlength="60"></label>` +
        `${btn('su-oadd', tr('org_add', 'Ajouter la règle'))}</div>` +
        `<h4>${esc(tr('org_run', 'Appliquer'))}</h4><div class="su-actions">` + btn('su-oprev', tr('preview', 'Aperçu')) + ' ' + btn('su-oapply', tr('apply', 'Appliquer l\'aperçu'), 'btn-ghost') + ' ' + btn('su-oundo', tr('undo', 'Annuler le dernier lot'), 'btn-ghost') + '</div><div id="su-oout"></div>';
    const refill = () => {
        const f = val('su-of'), ops = d.fields[f] || [];
        $('su-oo').innerHTML = ops.map(o => `<option value="${esc(o)}">${esc(ol(o))}</option>`).join('');
        $('su-ovbox').innerHTML = ORG_CHOICES[f] ? sel('su-ov', ORG_CHOICES[f].map(c => [c[0], yn(c[0])])) : `<input type="text" id="su-ov" class="settings-select" maxlength="80" placeholder="${esc((ORG_FIELD[f] || [])[1] || '')}">`;
    };
    const retarget = () => { const a = val('su-oa'); $('su-otl').textContent = tr('org_t_' + a, (ORG_ACTION[a] || [, 'Nom'])[1]); $('su-ot').placeholder = a === 'suggest_folder' ? 'Figurines/Dragons' : ''; };
    $('su-of').onchange = refill; $('su-oa').onchange = retarget; refill(); retarget();
    wire(box, 'su-oadd', async () => {
        await api('/api/organize/rules', { name: val('su-on'), field: val('su-of'), op: val('su-oo'), value: val('su-ov'), action: val('su-oa'), target: val('su-ot') });
        await TABS.organize.render(box); note(box, '✓ ' + tr('org_added', 'Règle ajoutée'));
    });
    box.onclick = async (e) => { const x = e.target.closest('[data-odel]'); if (!x) return; try { await api(`/api/organize/rules/${x.dataset.odel}`, undefined, 'DELETE'); await TABS.organize.render(box); note(box, '✓ ' + tr('org_deleted', 'Règle supprimée')); } catch (er) { note(box, er.message, true); } };
    wire(box, 'su-oprev', async () => {
        const p = await api('/api/organize/preview', {});
        $('su-oout').innerHTML = `<p class="settings-hint">${esc(p.total)} ${esc(tr('org_changes', 'changement(s) proposé(s)'))}${p.truncated ? ' (' + esc(tr('org_first', 'les premiers')) + ')' : ''} — ${esc(tr('org_nothing_written', 'rien n\'est écrit tant que vous n\'appliquez pas.'))}</p>` +
            table(p.items.slice(0, 200), [['path', tr('org_col_file', 'Fichier'), (v) => baseName(v)], ['action', tr('org_col_action', 'Action'), (v) => al(v)], ['target', tr('org_col_target', 'Cible')], ['rule', tr('org_col_rule', 'Règle')]]);
    });
    wire(box, 'su-oapply', async () => { const r = await api('/api/organize/apply', { confirm: true }); note(box, `${r.applied} ✓`); });
    wire(box, 'su-oundo', async () => { const b = (await api('/api/organize/batches')).batches.find(x => !x.undone); if (!b) throw new Error(tr('empty', 'Rien à afficher pour le moment.')); const r = await api('/api/organize/undo', { batch: b.batch }); note(box, `${r.undone} ↩`); });
} };
TABS.diff = { fb: 'Diff 3D', icon: 'code-compare', async render(box) {
    box.innerHTML = '<div class="su-line">' + pfield('su-dp', tr('path', 'Chemin du modèle'), '/…/piece.stl') + field('su-da', tr('ver_a', 'Version A (n° ou current)'), '1', 'suite-field-md') + field('su-db', tr('ver_b', 'Version B (n° ou current)'), 'current', 'suite-field-md') + btn('su-dgo', tr('compare', 'Comparer')) + '</div><div id="su-dout"></div>';
    wire(box, 'su-dgo', async () => {
        const j = await api('/api/model-diff', { path: val('su-dp'), a: val('su-da') || 'current', b: val('su-db') || 'current' });
        const r = j.job_id ? await waitJob(j.job_id, box) : (j.result || j);
        const m = [[tr('d_removed', 'Retiré'), r.removed_pct + ' %'], [tr('d_added', 'Ajouté'), r.added_pct + ' %'], [tr('d_mean', 'Écart moyen'), r.mean_distance_mm + ' mm'], [tr('d_max', 'Écart max'), r.max_distance_mm + ' mm'],
            [tr('d_vol', 'Volume'), r.delta && r.delta.volume_mm3 != null ? (r.delta.volume_mm3 > 0 ? '+' : '') + r.delta.volume_mm3 + ' mm³' : '—'], [tr('d_size', 'Dimensions Δ'), r.delta ? r.delta.size_mm.join(' × ') + ' mm' : '—']];
        $('su-dout').innerHTML = (r.identical ? `<p class="settings-hint"><b>${esc(tr('d_same', 'Les deux versions sont identiques (à la tolérance près).'))}</b></p>` : '') +
            `<div class="suite-scroll"><table class="suite-table"><tbody>${m.map(x => `<tr><th>${esc(x[0])}</th><td>${esc(x[1])}</td></tr>`).join('')}</tbody></table></div><div id="su-dcloud"></div>` +
            `<p class="settings-hint">${esc(tr('d_note', 'Comparaison par échantillonnage de la surface (rouge : matière retirée, vert : ajoutée). Glissez pour tourner, molette pour zoomer. Maillages STL/OBJ/3MF/PLY/OFF ; STEP non pris en charge.'))}</p>`;
        cloudView($('su-dcloud'), r.points || {}, r.edges);
    });
} };
TABS.similar = { fb: 'Similaires', icon: 'clone', async render(box) {
    box.innerHTML = '<p class="settings-hint" id="su-sidx"><i class="fa-solid fa-spinner fa-spin"></i> ' + esc(tr('sim_checking', 'Lecture de l\'index de similarité…')) + '</p>' +
        '<div class="su-line">' + pfield('su-sp', tr('path', 'Chemin du modèle')) + btn('su-sgo', tr('search', 'Chercher')) + btn('su-sbuild', tr('build', 'Construire l\'index'), 'btn-ghost') + '</div><div id="su-sout"></div>';
    /* L'état de l'index (nombre de modèles, temps restant) demande de compter la bibliothèque : il se remplit après l'affichage, sans le retarder. */
    const loadStatus = async () => {
        const st = await api('/api/similar/status').catch(() => null), el = $('su-sidx'); if (!el) return;
        if (!st) { el.textContent = ''; return; }
        const left = Number(st.estimated_seconds_left) > 0 ? ` — ${esc(tr('sim_left', 'reste environ'))} ${Number(st.estimated_seconds_left) >= 90 ? Math.round(st.estimated_seconds_left / 60) + ' min' : Math.round(st.estimated_seconds_left) + ' s'}` : '';
        el.innerHTML = `${esc(tr('sim_index', 'Index de similarité'))} : <b>${esc((st.indexed || 0).toLocaleString())} / ${esc((st.total || 0).toLocaleString())}</b> ${esc(tr('sim_indexed', 'modèle(s) indexé(s)'))}${st.skipped ? ` — ${esc(st.skipped.toLocaleString())} ${esc(tr('sim_skipped', 'ignoré(s) (illisible ou trop gros)'))} <button type="button" class="btn btn-secondary btn-sm su-skipbtn" id="su-sskip"><i class="fa-solid fa-triangle-exclamation"></i> ${esc(tr('skip_btn', 'Fichiers ignorés'))} (${esc(st.skipped.toLocaleString())})</button>` : ''}${left}`;
        const sb = $('su-sskip'); if (sb) sb.onclick = () => openSkipped(box, loadStatus);
    };
    loadStatus();
    wire(box, 'su-sgo', async () => {
        const d = await api(`/api/similar?path=${encodeURIComponent(val('su-sp'))}`), th = (p) => `<span class="su-thumb"><img src="${API}/api/thumb?path=${encodeURIComponent(p)}" loading="lazy" alt="" onerror="this.replaceWith(Object.assign(document.createElement('i'),{className:'fa-solid fa-cube'}))"></span>`;
        const dir = (p) => String(p || '').replace(/\\/g, '/').split('/').slice(-3, -1).join('/');
        $('su-sout').innerHTML = (d.results || []).length ? `<div class="suite-scroll"><table class="suite-table su-sim"><thead><tr><th></th><th>${esc(tr('sim_file', 'Fichier'))}</th><th>${esc(tr('sim_folder', 'Dossier'))}</th><th>${esc(tr('sim_prox', 'Proximité'))}</th></tr></thead><tbody>` +
            d.results.map(r => `<tr><td>${th(r.path)}</td><td><b>${esc(r.name || baseName(r.path))}</b></td><td class="su-dim" title="${esc(r.path)}">${esc(dir(r.path))}</td><td>${r.similarity == null ? '' : esc(r.similarity) + ' %'}</td></tr>`).join('') + '</tbody></table></div>'
            : `<p class="settings-hint">${esc(tr('empty', 'Rien à afficher pour le moment.'))}</p>`;
    });
    /* L'indexation d'une grosse bibliothèque dure plusieurs minutes : on la suit tant que l'onglet est ouvert, sans abandonner au bout de 4 min (elle continue de toute façon côté serveur). */
    wire(box, 'su-sbuild', async () => {
        const j = await api('/api/similar/build', {});
        for (let i = 0; box.isConnected; i++) {
            const st = await api(`/api/jobs/${j.job_id}`);
            note(box, `${st.state || ''} ${pct(st.progress)}`);
            if (i % 5 === 0) loadStatus();
            if (['done', 'failed', 'cancelled'].includes(st.state)) { if (st.state !== 'done') throw new Error(st.error || st.state); break; }
            await new Promise(r => setTimeout(r, 2000));
        }
        if (box.isConnected) { note(box, '✓'); loadStatus(); }
    });
} };
/* Fichiers ignorés par l'index de similarité : liste avec miniature, cause et solution ; « Réessayer » les remet dans l'indexation. */
const SKIP_CODES = ['too_big', 'empty', 'unreadable', 'missing'];
async function openSkipped(box, refresh) {
    let dlg = $('modal-suite-skipped');
    if (!dlg) {
        dlg = document.createElement('div'); dlg.id = 'modal-suite-skipped'; dlg.className = 'modal hidden';
        dlg.innerHTML = `<div class="modal-content sk-content"><div class="modal-header"><h3><i class="fa-solid fa-triangle-exclamation"></i> <span>${esc(tr('skip_title', 'Fichiers ignorés'))}</span></h3><button class="modal-close" type="button" id="sk-x">×</button></div><div class="modal-body" id="sk-body"></div></div>`;
        document.body.appendChild(dlg);
        const close = () => { if (typeof closeModal === 'function') closeModal('modal-suite-skipped'); else dlg.classList.add('hidden'); };
        dlg.addEventListener('click', (e) => { if (e.target === dlg) close(); });
        $('sk-x').onclick = close; dlg._close = close;
    }
    const body = $('sk-body'); body.innerHTML = '<p class="settings-hint"><i class="fa-solid fa-spinner fa-spin"></i></p>';
    if (typeof openModal === 'function') openModal('modal-suite-skipped'); else dlg.classList.remove('hidden');
    let d; try { d = await api('/api/similar/skipped'); } catch (e) { body.innerHTML = `<p class="settings-hint">${esc(e.message)}</p>`; return; }
    const mb = (n) => (n / 1048576).toFixed(n >= 10485760 ? 0 : 1) + ' Mo';
    const label = (c) => tr('skip_c_' + c, { too_big: 'Trop gros', empty: 'Aucune surface', unreadable: 'Illisible', missing: 'Introuvable' }[c]);
    const fix = (c) => tr('skip_f_' + c, { too_big: 'Ce modèle dépasse {max} Mo : trop lourd pour l\'empreinte de forme. Simplifiez-le dans votre logiciel 3D (réduire le nombre de triangles) puis remplacez le fichier, ou laissez-le de côté : il reste utilisable partout ailleurs dans Stellio.',
        empty: 'Le fichier ne contient aucune surface. Réexportez-le depuis votre logiciel 3D, ou essayez l\'outil Réparation.',
        unreadable: 'Le fichier est illisible ou son format n\'est pas standard. Réexportez-le en STL ou 3MF depuis votre logiciel, ou essayez l\'outil Réparation.',
        missing: 'Le fichier a été déplacé ou supprimé. Relancez l\'analyse de la bibliothèque (Paramètres, Sources), puis réessayez.' }[c]).replace('{max}', d.max_mb || 60);
    const dir = (p) => String(p || '').replace(/\\/g, '/').split('/').slice(-3, -1).join('/');
    const th = (p) => `<span class="su-thumb"><img src="${API}/api/thumb?path=${encodeURIComponent(p)}" loading="lazy" alt="" onerror="this.replaceWith(Object.assign(document.createElement('i'),{className:'fa-solid fa-cube'}))"></span>`;
    const groups = SKIP_CODES.map(c => [c, (d.files || []).filter(f => f.code === c)]).filter(g => g[1].length);
    body.innerHTML = !groups.length ? `<p class="settings-hint">${esc(tr('skip_none', 'Aucun fichier ignoré.'))}</p>` :
        `<p class="settings-hint">${esc(tr('skip_intro', 'Ces modèles n\'ont pas pu entrer dans l\'index de similarité. Ils restent dans votre bibliothèque, seule la recherche de pièces similaires les ignore.'))}</p>` +
        groups.map(([c, list]) => `<div class="sk-group"><div class="sk-head"><b>${esc(label(c))}</b> <span class="su-dim">(${list.length})</span></div><p class="settings-hint sk-fix"><i class="fa-solid fa-lightbulb"></i> ${esc(fix(c))}</p>` +
            `<div class="sk-list">${list.map(f => `<div class="sk-row" title="${esc(f.reason)}">${th(f.path)}<div class="sk-name"><b>${esc(f.name)}</b><div class="su-dim">${esc(dir(f.path))}${f.size ? ' · ' + esc(mb(f.size)) : ''}</div></div></div>`).join('')}</div></div>`).join('') +
        `<div class="sk-foot"><button type="button" class="btn btn-primary btn-sm" id="sk-retry"><i class="fa-solid fa-rotate"></i> ${esc(tr('skip_retry', 'Réessayer l\'indexation'))}</button><button type="button" class="btn btn-ghost btn-sm" id="sk-close">${esc(tr('skip_close', 'Fermer'))}</button></div>`;
    $('sk-close') && ($('sk-close').onclick = dlg._close);
    $('sk-retry') && ($('sk-retry').onclick = async () => {
        $('sk-retry').disabled = true;
        try { await api('/api/similar/skipped/retry', {}); dlg._close(); const b = $('su-sbuild'); if (b) b.click(); else if (refresh) refresh(); } catch (e) { body.insertAdjacentHTML('afterbegin', `<p class="settings-hint" style="color:var(--danger,#e5484d)">${esc(e.message)}</p>`); $('sk-retry').disabled = false; }
    });
}
const flash = (box, id) => { if (!id) return; box.querySelectorAll(`[data-pid="${id}"]`).forEach(el => { el.classList.add('su-flash'); el.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); setTimeout(() => el.classList.remove('su-flash'), 2600); }); };
const sigChip = (st) => {
    const m = { valid: ['su-chip-ok', 'fa-signature', 'sig_valid', 'Signé'], invalid: ['su-chip-warn', 'fa-triangle-exclamation', 'sig_invalid', 'Signature invalide'],
        unverifiable: ['su-chip-muted', 'fa-circle-question', 'sig_unverifiable', 'Signature non vérifiable'], unsigned: ['su-chip-muted', 'fa-circle-minus', 'sig_unsigned', 'Non signé'] }[st];
    return m ? `<span class="su-chip ${m[0]}"><i class="fa-solid ${m[1]}"></i> ${esc(tr(m[2], m[3]))}</span>` : '';
};
const auditChip = (lv) => {
    const m = { ok: ['su-chip-ok', 'audit_ok', 'Audit : rien à signaler'], warn: ['su-chip-muted', 'audit_warn', 'Audit : points à lire'], danger: ['su-chip-warn', 'audit_danger', 'Audit : code dangereux (risque accepté)'] }[lv];
    return m ? `<span class="su-chip ${m[0]}">${esc(tr(m[1], m[2]))}</span>` : '';
};
/* Pas d'avertissement quand le noyau ne restreint rien (retiré en 1.1.9) : seule la restriction réellement active est indiquée. */
const sandboxNotice = (sb) => !sb || !sb.enforced ? ''
    : (sb.filesystem ? tr('sb_full', "Sous Linux, le noyau restreint chaque plugin : fichiers (lecture seule, écriture dans son dossier data/) et réseau (selon ses permissions). Un plugin autorisé à utiliser le réseau n'est pas limité à certains sites.")
        : tr('sb_net', "Le noyau restreint le réseau des plugins sans permission « network ». Les fichiers ne sont pas restreints sur ce noyau (Landlock absent) : n'activez que du code que vous avez lu."));
/* Installation avec les deux confirmations explicites du serveur : risque détecté par l'audit, changement de clé de signature. */
async function installFlow(send, opts) {
    let extra = {};
    for (let i = 0; i < 4; i++) {
        try { return await send(extra); } catch (e) {
            const code = e.data && e.data.code;
            if (code === 'audit_blocked' && !extra.accept_risk) {
                const list = ((e.data.audit && e.data.audit.findings) || []).filter(f => f.blocking).slice(0, 6).map(f => `• ${f.file}${f.line ? ':' + f.line : ''} — ${f.detail}`).join('\n');
                if (!await ask(`${tr('risk_title', 'Code dangereux détecté')}\n\n${list}\n\n${tr('risk_confirm', 'Installer malgré ce risque ?')}`, { danger: true })) throw e;
                extra = Object.assign({}, extra, { accept_risk: true });
            } else if ((code === 'host_unsigned' || code === 'host_no_key') && opts && opts.unsigned && !extra.accept_unsigned) {
                /* installation directe depuis un .zip : la signature n'est pas exigée, mais l'utilisateur doit accepter la responsabilité */
                if (!await ask(`${tr('unsigned_title', 'Plugin non signé')}\n\n${tr('unsigned_body', "Ce plugin n'est pas signé : son auteur et son contenu ne sont pas vérifiés, et il exécutera du code directement dans Stellio, avec accès à vos fichiers et à votre compte.\n\nStellio et l'équipe de développement ne peuvent en aucun cas être tenus pour responsables des dégâts, pertes de données ou failles causés par ce plugin. N'installez que du code dont vous avez confiance en la source.")}\n\n${tr('unsigned_confirm', 'Je comprends et j\'accepte ce risque : installer quand même ?')}`, { danger: true })) throw e;
                extra = Object.assign({}, extra, { accept_unsigned: true });
            } else if (code === 'key_changed' && !extra.accept_key_change) {
                if (!await ask(`${e.message}\n\n${tr('key_confirm', 'La clé de signature a changé. Installer quand même ?')}`, { danger: true })) throw e;
                extra = Object.assign({}, extra, { accept_key_change: true });
            } else throw e;
        }
    }
}
const plOpen = new Set();   // sections dépliées pendant la visite en cours (vide à chaque ouverture de la page)
let plSource = null;      // source de catalogue choisie pendant la session (le stockage du navigateur n'est qu'un confort)
TABS.plugins = { fb: 'Plugins', icon: 'puzzle-piece', async render(box) {
    const lang = (window.I18N && I18N.lang) || 'fr';
    const d = await api('/api/plugins?lang=' + encodeURIComponent(lang));
    let custom = plSource; if (custom === null) { try { custom = localStorage.getItem('stellio-plugins-source') || ''; } catch (e) { custom = ''; } }
    const perms = (l) => (l && l.length) ? l.map(x => `<span class="su-chip">${esc(x)}</span>`).join('') : `<span class="su-chip su-chip-muted">${esc(tr('no_perms', 'aucune permission'))}</span>`;
    const badge = (official) => official ? `<span class="su-badge su-badge-official" title="${esc(tr('badge_official_tip', 'Hébergé sur le dépôt officiel stellio-plugins'))}"><i class="fa-solid fa-circle-check"></i> ${esc(tr('badge_official', 'Officiel'))}</span>` : `<span class="su-badge su-badge-community" title="${esc(tr('badge_community_tip', 'Hébergé en dehors du dépôt officiel : vérifiez l\'auteur et le code'))}"><i class="fa-solid fa-users"></i> ${esc(tr('badge_community', 'Communautaire'))}</span>`;
    const item = (p, actions, extra) => `<div class="su-plugin" data-pid="${esc(p.id)}"><div class="su-plugin-head"><strong>${esc(p.name)}</strong><span class="su-chip">v${esc(p.version || '?')}</span></div><div class="su-plugin-tags">${badge(p.origin === 'official')}${extra || ''}</div>` +
        (p.description ? `<p class="settings-hint">${esc(p.description)}</p>` : '') + `<div class="su-plugin-perms"><small>${esc(tr('perms', 'Permissions'))}</small>${perms(p.permissions)}</div><div class="su-actions">${actions}</div></div>`;
    let bust = 0;
    const srcQ = custom ? '&url=' + encodeURIComponent(custom) : '';
    const logo = (p) => p.has_logo ? `<img class="su-logo" src="${API}/api/plugins/logo?id=${encodeURIComponent(p.id)}${srcQ}${bust ? '&t=' + bust : ''}" loading="lazy" alt="">` : '<span class="su-logo su-logo-ph"><i class="fa-solid fa-puzzle-piece"></i></span>';
    const card = (p) => `<article class="su-store-card" data-pid="${esc(p.id)}">${logo(p)}<div class="su-store-body"><div class="su-plugin-head"><strong>${esc(p.name)}</strong><span class="su-chip">v${esc(p.version || '?')}</span></div><div class="su-plugin-tags">${badge(p.official)}` +
        (p.installed_version ? `<span class="su-chip su-chip-ok">${esc(tr('installed', 'installé'))} ${esc(p.installed_version)}</span>` : '') + sigChip(p.signature_status) + `</div>` +
        `<p class="su-store-desc">${esc(p.description || '')}</p>` +
        `<div class="su-plugin-perms">${perms(p.permissions)}</div>` +
        `<div class="su-actions su-store-actions"><div class="su-store-btns">${p.update_available || !p.installed_version ? `<button type="button" class="btn btn-primary btn-sm" data-cat="${esc(p.id)}">${esc(p.update_available ? tr('update', 'Mettre à jour') : tr('install', 'Installer'))}</button>` : `<button type="button" class="btn btn-secondary btn-sm" data-cat="${esc(p.id)}">${esc(tr('reinstall', 'Réinstaller'))}</button>`}` +
        `${p.homepage ? `<a class="btn btn-ghost btn-sm" href="${esc(p.homepage)}" target="_blank" rel="noopener noreferrer"><i class="fa-brands fa-github"></i> ${esc(tr('plugin_page', 'Page du plugin'))}</a>` : ''}</div>` +
        `${p.author ? `<small class="su-store-author">${esc(tr('by', 'par'))} ${esc(p.author)}</small>` : ''}</div></div></article>`;
    const instHtml = (d) => `<summary><h4><i class="fa-solid fa-puzzle-piece"></i> ${esc(tr('installed_title', 'Plugins installés'))} <span class="su-chip">${d.plugins.length}</span></h4></summary>` +
        (d.plugins.length ? `<div class="su-plugins">${d.plugins.map(p => item(p,
            `<button type="button" class="btn btn-ghost btn-sm" data-pl="${p.enabled ? 'off' : 'on'}" data-id="${esc(p.id)}" data-perms="${esc((p.permissions || []).join(','))}">${esc(p.enabled ? tr('disable', 'Désactiver') : tr('enable', 'Activer'))}</button>` +
            `<button type="button" class="btn btn-ghost btn-sm" data-pl="test" data-id="${esc(p.id)}">${esc(tr('test', 'Essai'))}</button><button type="button" class="btn btn-ghost btn-sm su-danger" data-pl="del" data-id="${esc(p.id)}">${esc(tr('delete', 'Supprimer'))}</button>`,
            `<span class="su-chip ${p.enabled ? 'su-chip-ok' : 'su-chip-muted'}">${esc(p.enabled ? tr('active', 'Actif') : tr('inactive', 'Inactif'))}</span>${p.restart_required ? `<span class="su-chip su-chip-warn">${esc(tr('restart_needed', 'Redémarrage requis'))}</span>` : ''}${p.security ? sigChip(p.security.signature) + auditChip(p.security.audit) : ''}`)).join('')}</div>` : `<p class="settings-hint">${esc(tr('no_plugin', 'Aucun plugin installé.'))}</p>`) +
        ((d.trusted_keys || []).length ? '' : `<p class="settings-hint"><i class="fa-solid fa-circle-info"></i> ${esc(tr('keys_none', "Aucune clé de confiance configurée : les téléchargements ne sont protégés que par l'empreinte SHA-256 du catalogue."))}</p>`);
    const builtHtml = (d) => { const b = d.builtin || []; return `<summary><h4><i class="fa-solid fa-cubes"></i> ${esc(tr('builtin_title', 'Plugins intégrés'))} <span class="su-chip">${b.filter(x => x.enabled).length}/${b.length}</span></h4></summary>` +
        `<p class="settings-hint">${esc(tr('builtin_hint', 'Livrés avec Stellio, ils ne se chargent que lorsqu\'ils sont activés. Vos réglages sont conservés quand vous désactivez un plugin. Le changement s\'applique au redémarrage de Stellio.'))}</p>` +
        (b.length ? `<div class="su-plugins">${b.map(p => `<div class="su-plugin" data-pid="${esc(p.id)}"><div class="su-plugin-head"><i class="fa-solid ${esc(p.icon || 'fa-puzzle-piece')}"></i><strong>${esc(p.name)}</strong><span class="su-chip">v${esc(p.version)}</span></div><div class="su-plugin-tags">${badge(true)}` +
            `<span class="su-chip ${p.enabled ? 'su-chip-ok' : 'su-chip-muted'}">${esc(p.enabled ? tr('active', 'Actif') : tr('inactive', 'Inactif'))}</span>${p.restart_required ? `<span class="su-chip su-chip-warn">${esc(tr('restart_needed', 'Redémarrage requis'))}</span>` : ''}</div>` +
            (p.description ? `<p class="settings-hint">${esc(p.description)}</p>` : '') +
            `<div class="su-actions"><button type="button" class="btn btn-${p.enabled ? 'ghost' : 'secondary'} btn-sm" data-hp="${p.enabled ? 'off' : 'on'}" data-id="${esc(p.id)}">${esc(p.enabled ? tr('disable', 'Désactiver') : tr('enable', 'Activer'))}</button></div></div>`).join('')}</div>` : '') +
        `<div class="su-actions"><button type="button" class="btn btn-${b.some(x => x.restart_required) ? 'primary' : 'ghost'} btn-sm" id="su-restart"><i class="fa-solid fa-rotate"></i> ${esc(tr('restart_btn', 'Redémarrer Stellio'))}</button></div>`; };
    const op = (id) => (plOpen.has(id) ? ' open' : '');
    const builtSection = (d) => `<details class="su-card su-fold" id="su-plbuilt"${op('su-plbuilt')}>${builtHtml(d)}</details>`;
    const instSection = (d) => `<details class="su-card su-fold" id="su-plinst"${op('su-plinst')}>${instHtml(d)}</details>`;
    box.innerHTML = (sandboxNotice(d.sandbox) ? `<div class="su-notice"><i class="fa-solid fa-shield-halved"></i><span>${esc(sandboxNotice(d.sandbox))}</span></div>` : '') +
        `<details class="su-card su-fold" id="su-plcat"${op('su-plcat')}><summary><h4><i class="fa-solid fa-store"></i> ${esc(tr('catalog', 'Catalogue'))} <span id="su-plcn" class="su-chip" hidden></span><span id="su-plupd" class="su-chip su-chip-upd" hidden style="display:none"><i class="fa-solid fa-arrow-up"></i> ${esc(tr('update_badge', 'Mise à jour disponible'))}</span><button type="button" class="btn btn-ghost btn-sm su-refresh" id="su-plref" title="${esc(tr('refresh', 'Actualiser le catalogue'))}" aria-label="${esc(tr('refresh', 'Actualiser le catalogue'))}"><i class="fa-solid fa-rotate"></i> ${esc(tr('refresh_btn', 'Actualiser'))}</button></h4></summary><p class="settings-hint">${esc(tr('store_hint', 'Plugins proposés par la communauté, hébergés sur GitHub. Installer un plugin ne l\'active pas : vous lisez ses permissions d\'abord.'))}</p><div id="su-plstore" class="su-store"><p class="settings-hint">…</p></div>` +
        `<div class="su-sub"><details class="su-fold su-fold-in" id="su-plzip"${op('su-plzip')}><summary><h4><i class="fa-solid fa-file-zipper"></i> ${esc(tr('install_zip', 'Installer ou mettre à jour depuis un .zip'))}</h4></summary>` +
        `<div class="su-actions"><label class="btn btn-secondary btn-sm suite-file"><i class="fa-solid fa-folder-open"></i> ${esc(tr('choose_file', 'Choisir un fichier'))}<input type="file" id="su-plf" accept=".zip,.json,.sig" multiple hidden></label><span id="su-plfn" class="settings-hint">${esc(tr('no_file', 'Aucun fichier sélectionné'))}</span></div><p class="settings-hint">${esc(tr('sig_hint', "Plugin signé : sélectionnez en même temps le .zip et son fichier .signature.json (créé par signer-plugin.bat)."))}</p>` +
        `<label class="suite-inline"><input type="checkbox" id="su-pldg"> ${esc(tr('allow_downgrade', 'autoriser le retour à une version plus ancienne'))}</label><div class="su-actions">${btn('su-plup', tr('install', 'Installer'))}</div></details>` +
        `<details class="su-fold su-fold-in" id="su-plsrc"${op('su-plsrc')}><summary><h4><i class="fa-solid fa-link"></i> ${esc(tr('source_title', 'Source du catalogue'))}</h4></summary><p class="settings-hint">${esc(tr('source_hint', 'Par défaut, le catalogue officiel de Stellio. Vous pouvez lire un autre catalogue (adresse https d\'un fichier JSON), par exemple celui de votre équipe.'))}</p>` +
        field('su-plcu', tr('catalog_url', 'Adresse https du catalogue (JSON)'), 'https://…/catalog.json') +
        `<div class="su-actions">${btn('su-plcuse', tr('source_use', 'Utiliser cette source'), 'btn-secondary')}${btn('su-plcdef', tr('source_default', 'Catalogue officiel'), 'btn-ghost')}</div></details></div></details>` +
        builtSection(d) + instSection(d);
    if (!box._plToggle) { box._plToggle = true; box.addEventListener('toggle', (e) => { const el = e.target; if (el && el.tagName === 'DETAILS' && el.id) { if (el.open) plOpen.add(el.id); else plOpen.delete(el.id); } }, true); }
    if ($('su-plcu')) $('su-plcu').value = custom;
    if ($('su-plf')) $('su-plf').onchange = () => { $('su-plfn').textContent = Array.from($('su-plf').files).map(x => x.name).join(' + ') || tr('no_file', 'Aucun fichier sélectionné'); };
    const loadStore = async (refresh) => {
        const host = $('su-plstore'); if (!host) return;
        const rb = $('su-plref'); if (refresh) { bust = Date.now(); if (rb) { rb.disabled = true; rb.querySelector('i').classList.add('fa-spin'); } host.classList.add('su-loading'); }
        try {
            const c = await api('/api/plugins/catalog', Object.assign({ lang }, custom ? { url: custom } : {}, refresh ? { refresh: true } : {}));
            if (!$('su-plstore')) return;
            loadStore._soft = 0; clearTimeout(loadStore._t);
            if ($('su-plcn')) { $('su-plcn').hidden = false; $('su-plcn').textContent = c.count; }
            if ($('su-plupd')) { const nu = c.plugins.filter(x => x.update_available).length; $('su-plupd').hidden = !nu; $('su-plupd').style.display = nu ? '' : 'none'; $('su-plupd').title = nu ? String(nu) : ''; }
            /* pas de redessin (donc pas de clignotement ni de rechargement des logos) quand le catalogue n'a pas changé */
            const gridHtml = c.plugins.length ? `<div class="su-store-grid">${c.plugins.map(card).join('')}</div>` : `<p class="settings-hint">${esc(tr('store_empty', 'Aucun plugin dans ce catalogue pour le moment.'))}</p>`;
            const gridSig = gridHtml.replace(/&t=\d+/g, '');
            if (host.dataset.sig !== gridSig || (!c.stale && host.querySelector('.su-soft')) || refresh) { host.innerHTML = gridHtml; host.dataset.sig = gridSig; }
            /* catalogue toujours consultable : en cas de lecture difficile (hors connexion, GitHub en retard), la dernière version vérifiée s'affiche avec un bandeau calme ;
               relecture automatique (15 s, puis toutes les 2 min), et actualisation silencieuse toutes les 5 min quand tout va bien */
            clearTimeout(loadStore._t);
            if (c.stale) {
                if (!host.querySelector('.su-soft')) host.insertAdjacentHTML('afterbegin', `<div class="su-soft su-soft-slim"><i class="fa-solid fa-rotate fa-spin"></i><div><b>${esc(tr('catalog_updating', 'Le catalogue se met à jour…'))}</b> <span class="settings-hint">${esc(tr('catalog_stale_hint', 'Dernière version vérifiée affichée ; nouvelle lecture automatique.'))}</span></div></div>`);
                loadStore._stale = (refresh ? 0 : (loadStore._stale || 0)) + 1;
                loadStore._t = setTimeout(() => { if ($('su-plstore')) loadStore(); }, loadStore._stale <= 6 ? 15000 : 120000);
            } else {
                loadStore._stale = 0;
                loadStore._t = setTimeout(() => { if ($('su-plstore')) loadStore(); }, 300000);
            }
            host.querySelectorAll('img.su-logo').forEach(im => im.addEventListener('error', () => im.replaceWith(Object.assign(document.createElement('span'), { className: 'su-logo su-logo-ph', innerHTML: '<i class="fa-solid fa-puzzle-piece"></i>' }))));
        } catch (x) {
            if ($('su-plstore') && (x.data && x.data.code === 'catalog_signature')) {
                /* Juste après une publication, GitHub peut servir un instant le catalogue et sa signature de deux versions différentes : ce n'est pas une panne.
                   Message rassurant avec repère visuel, et nouvelle tentative automatique (4 fois, toutes les 15 s) avant de proposer de réessayer soi-même. */
                const n = refresh ? 0 : (loadStore._soft || 0);
                const waiting = n < 4;
                host.dataset.sig = '';
                host.innerHTML = `<div class="su-soft"><i class="fa-solid ${waiting ? 'fa-rotate fa-spin' : 'fa-clock'}"></i><div><b>${esc(waiting ? tr('catalog_updating', 'Le catalogue se met à jour…') : tr('catalog_later', 'La mise à jour du catalogue prend un peu de temps'))}</b>` +
                    `<div class="settings-hint">${esc(waiting ? tr('catalog_updating_hint', 'Une publication vient d\'avoir lieu : nouvelle vérification dans quelques secondes.') : tr('catalog_later_hint', 'Rien n\'est cassé. Réessayez dans quelques minutes.'))}</div></div>` +
                    (waiting ? '' : `<button type="button" class="btn btn-ghost btn-sm" data-retry="1">${esc(tr('retry', 'Réessayer'))}</button>`) + `</div>`;
                if (waiting) { loadStore._soft = n + 1; clearTimeout(loadStore._t); loadStore._t = setTimeout(() => { if ($('su-plstore')) loadStore(); }, 15000); }
            } else if ($('su-plstore')) { loadStore._soft = 0; host.dataset.sig = ''; host.innerHTML = `<p class="settings-hint">${esc(tr('store_fail', 'Catalogue indisponible'))} — ${esc(x.message || '')} <button type="button" class="btn btn-ghost btn-sm" data-retry="1">${esc(tr('retry', 'Réessayer'))}</button></p>`; }
        } finally {
            const rb2 = $('su-plref'); if (rb2) { rb2.disabled = false; rb2.querySelector('i').classList.remove('fa-spin'); }
            if ($('su-plstore')) $('su-plstore').classList.remove('su-loading');
        }
    };
    // mise à jour « en douceur » : on ne redessine que la liste des installés (et le catalogue en arrière-plan), sans reconstruire toute la page
    const reloadInstalled = async () => { const nd = await api('/api/plugins?lang=' + encodeURIComponent(lang)); const sec = $('su-plinst'); if (sec) sec.innerHTML = instHtml(nd); const sb = $('su-plbuilt'); if (sb) sb.innerHTML = builtHtml(nd); };
    box.onclick = async (e) => {
        if (e.target.closest('#su-plref')) { e.preventDefault(); await loadStore(true); if (!box.querySelector('.su-soft')) note(box, '✓ ' + tr('refreshed', 'Catalogue actualisé')); return; }
        if (e.target.closest('[data-retry]')) { loadStore._soft = 0; $('su-plstore').innerHTML = '<p class="settings-hint">…</p>'; loadStore(); return; }
        if (e.target.closest('#su-restart')) {
            const rb = e.target.closest('#su-restart');
            const okR = (typeof showConfirmDialog === 'function') ? await showConfirmDialog(tr('restart_confirm', 'Redémarrer Stellio maintenant ?'), { title: tr('restart_btn', 'Redémarrer Stellio'), confirmLabel: tr('restart_btn', 'Redémarrer Stellio') }) : true;
            if (!okR) return;
            rb.disabled = true; note(box, tr('restart_wait', 'Redémarrage en cours… la page va se recharger.'));
            fetch(`${API}/api/app/quit`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ restart: true }), keepalive: true }).catch(() => {});
            const t0 = Date.now(); let down = false;
            const poll = setInterval(async () => {
                try { const r = await fetch(`${API}/api/plugins/features`, { cache: 'no-store' }); if (r.ok && down) { clearInterval(poll); location.reload(); } else if (r.ok && Date.now() - t0 > 4000) { /* toujours l'ancien processus */ } }
                catch (_) { down = true; }
                if (Date.now() - t0 > 120000) { clearInterval(poll); rb.disabled = false; }
            }, 1500);
            return;
        }
        const hb = e.target.closest('[data-hp]'); if (hb) {
            try { hb.disabled = true; const r = await api(`/api/plugins/${hb.dataset.id}`, { enabled: hb.dataset.hp === 'on' }, 'PUT'); await reloadInstalled(); applyHostFeatures(); note(box, '✓ ' + (r.restart_required ? tr('restart_note', 'Pris en compte au redémarrage de Stellio.') : tr('saved', 'Enregistré'))); }
            catch (x) { hb.disabled = false; note(box, x.message, true); }
            return;
        }
        const b = e.target.closest('[data-pl]'); if (b) {
            const id = b.dataset.id;
            try {
                if (b.dataset.pl === 'on') { const perms = b.dataset.perms ? b.dataset.perms.split(',') : []; if (!await ask(`${tr('ack_perms', 'Permissions demandées par ce plugin')} : ${perms.join(', ') || '—'}`, { title: tr('ack_title', 'Activer ce plugin ?'), confirmLabel: tr('ack_ok', 'Activer') })) return; await api(`/api/plugins/${id}`, { enabled: true, ack_permissions: perms }, 'PUT'); }
                else if (b.dataset.pl === 'off') await api(`/api/plugins/${id}`, { enabled: false }, 'PUT');
                else if (b.dataset.pl === 'test') { const r = await api(`/api/plugins/${id}/test`, {}); note(box, `${r.ok ? '✓' : '✗'} ${r.output || r.error || ''}`.slice(0, 300), !r.ok); return; }
                else if (b.dataset.pl === 'del') { if (!await ask(tr('confirm_delete', 'Supprimer ce plugin ?'), { danger: true, title: tr('confirm_delete_title', 'Supprimer le plugin') })) return; const row = box.querySelector(`.su-plugin[data-pid="${id}"]`); b.disabled = true; b.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> ' + esc(tr('deleting', 'Suppression…')); if (row) row.classList.add('su-removing'); await api(`/api/plugins/${id}`, undefined, 'DELETE'); await reloadInstalled(); note(box, '✓ ' + tr('deleted', 'Plugin supprimé')); loadStore(); refreshPluginNav(); return; }
                await reloadInstalled(); refreshPluginNav();
            } catch (x) { note(box, x.message, true); }
            return;
        }
        const c = e.target.closest('[data-cat]'); if (c) {
            const label = c.innerHTML; c.disabled = true; c.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> ' + esc(tr('installing', 'Installation…'));
            try { const r = await installFlow((x) => api('/api/plugins/catalog/install', Object.assign({ id: c.dataset.cat }, custom ? { url: custom } : {}, x))); await reloadInstalled(); await loadStore(); note(box, '✓ ' + (r.note || tr('installed_ok', 'Plugin installé'))); flash(box, c.dataset.cat); refreshPluginNav(); offerRestart(box, r.plugin); } catch (x) { c.disabled = false; c.innerHTML = label; note(box, x.message, true); }
        }
    };
    wire(box, 'su-plup', async () => {
        const all = Array.from($('su-plf').files);
        const f = all.find(x => /\.zip$/i.test(x.name)); if (!f) throw new Error(tr('pick_zip', 'Choisissez un fichier .zip.'));
        /* signature détachée (fichier .signature.json de signer-plugin.bat, ou hexadécimal brut) : nécessaire pour un plugin qui exécute du code dans Stellio */
        let sig = ''; const sf = all.find(x => x !== f);
        if (sf) { const raw = (await sf.text()).trim(); try { const o = JSON.parse(raw); sig = String(o.signature || ''); } catch (e) { sig = raw.replace(/\s+/g, ''); } }
        const j = await installFlow(async (x) => {
            const fd = new FormData(); fd.append('file', f); if (sig) fd.append('signature', sig); if ($('su-pldg').checked) fd.append('allow_downgrade', '1');
            Object.keys(x).forEach(k => fd.append(k, '1'));
            const r = await fetch(`${API}/api/plugins/install`, { method: 'POST', body: fd }); const jj = await r.json().catch(() => ({}));
            if (!r.ok) { const e = new Error(jj.error || r.status); e.data = jj; throw e; }
            return jj;
        }, { unsigned: true });
        await reloadInstalled(); loadStore(); note(box, '✓ ' + (j.note || tr('installed_ok', 'Plugin installé'))); flash(box, j.plugin && j.plugin.id); refreshPluginNav(); offerRestart(box, j.plugin);
    });
    wire(box, 'su-plcuse', async () => { custom = plSource = val('su-plcu'); try { localStorage.setItem('stellio-plugins-source', custom); } catch (e) { /* facultatif */ } await TABS.plugins.render(box); });
    wire(box, 'su-plcdef', async () => { plSource = ''; try { localStorage.removeItem('stellio-plugins-source'); } catch (e) { /* facultatif */ } await TABS.plugins.render(box); });
    loadStore();
    refreshPluginNav();
} };
TABS.sync = { fb: 'Synchro', icon: 'arrows-rotate', async render(box) {
    const d = await api('/api/sync/pairs');
    box.innerHTML = table(d.pairs, [['name', 'Paire'], ['local_root', 'Local'], ['remote_root', 'Distant'], ['direction', 'Sens'], ['strategy', 'Conflits']]) +
        '<div class="su-line">' + field('su-yid', tr('pair_id', 'N° de paire'), '', 'suite-field-sm') + btn('su-yplan', tr('plan', 'Voir le plan')) + btn('su-yapply', tr('apply_plan', 'Appliquer (aucune suppression)'), 'btn-ghost') + '</div><div id="su-yout"></div>';
    wire(box, 'su-yplan', async () => { const p = await api(`/api/sync/pairs/${val('su-yid')}/plan`, {}); $('su-yout').innerHTML = `<pre class="suite-pre">${esc(JSON.stringify(p.summary))}</pre>` + table(p.items, [['rel', 'Fichier'], ['action', 'Action']]); });
    wire(box, 'su-yapply', async () => { const r = await api(`/api/sync/pairs/${val('su-yid')}/apply`, { confirm: true }); note(box, JSON.stringify(r.result || r)); });
} };
TABS.plate = { fb: 'Plateau', icon: 'table-cells-large', async render(box) {
    let printers = []; try { printers = await api('/api/printers'); } catch (e) { printers = []; }
    const bed = (p) => { const c = p.config || {}; return [Number(c.bed_x), Number(c.bed_y), Number(c.bed_z)]; };
    const withBed = (Array.isArray(printers) ? printers : []).filter(p => { const v = bed(p); return v[0] > 0 && v[1] > 0; });
    const num = (id, label, v) => `<label class="suite-field suite-field-sm"><span>${esc(label)}</span><input type="number" id="${id}" class="settings-select" min="1" step="1" value="${v}"></label>`;
    box.innerHTML = mfield('su-pp', tr('paths_n', 'Modèles (un chemin par ligne). Plusieurs exemplaires : « chemin ×3 » ou la même ligne répétée'), 4) +
        `<div class="suite-row suite-row-sm"><label class="suite-field suite-field-md"><span>${esc(tr('plate_printer', 'Imprimante'))}</span><select id="su-ppr" class="settings-select"><option value="">${esc(tr('printer_manual', 'Saisie manuelle'))}</option>` +
        withBed.map(p => { const v = bed(p); return `<option value="${esc(p.id)}" data-x="${v[0]}" data-y="${v[1]}" data-z="${v[2] > 0 ? v[2] : ''}">${esc(p.name)} (${v[0]}×${v[1]}${v[2] > 0 ? '×' + v[2] : ''})</option>`; }).join('') + '</select></label>' +
        num('su-pwl', tr('plate_l', 'Largeur (mm)'), 256) + num('su-pwd', tr('plate_p', 'Profondeur (mm)'), 256) + num('su-pwh', tr('plate_h', 'Hauteur (mm)'), 256) + num('su-pm', tr('margin', 'Marge entre pièces (mm)'), 3) +
        `<label class="suite-field suite-field-md"><span>${esc(tr('nest_mode', 'Disposition'))}</span><select id="su-pmode" class="settings-select"><option value="shape">${esc(tr('nest_shape', 'Forme réelle (imbrication)'))}</option><option value="box">${esc(tr('nest_box', 'Boîte englobante'))}</option></select></label>` +
        `<label class="suite-field suite-field-sm"><span>${esc(tr('nest_rot', 'Rotation automatique'))}</span><select id="su-pstep" class="settings-select"><option value="90">90°</option><option value="45">45°</option><option value="30">30°</option><option value="15">15°</option><option value="0">${esc(tr('nest_norot', 'Aucune'))}</option></select></label>` +
        `<div class="su-actions">${btn('su-pgo', tr('arrange', 'Disposer automatiquement'))}<span id="su-pbusy" class="settings-hint su-busy" hidden><i class="fa-solid fa-spinner fa-spin"></i> ${esc(tr('computing', 'Calcul de la disposition…'))}</span></div></div><div id="su-pout"></div>`;
    /* Liste des modèles : une ligne par fichier avec son bouton « retirer » (le champ texte reste modifiable à la main). */
    const splitLine = (l) => { const m = l.match(/^(.*\S)\s+[x×]\s*(\d+)$/i); return { path: m ? m[1].trim() : l, n: m ? Math.max(1, Math.min(50, +m[2])) : 1 }; };
    const drawList = () => {
        const cnt = {}, ord = []; lines('su-pp').forEach(l => { const q = splitLine(l); if (!(q.path in cnt)) { cnt[q.path] = 0; ord.push(q.path); } cnt[q.path] += q.n; });
        const host = $('su-pp-list'); if (!host) return;
        host.hidden = !ord.length;
        host.innerHTML = ord.length ? `<div class="su-pp-head"><span class="settings-hint">${esc(ord.length)} ${esc(tr('pp_files', 'modèle(s)'))}</span><button type="button" class="btn btn-ghost btn-sm" data-pp-clear="1"><i class="fa-solid fa-trash"></i> ${esc(tr('pp_clear', 'Tout retirer'))}</button></div>` +
            ord.map((q, i) => `<div class="su-pp-row"><span class="su-pp-name" title="${esc(q)}">${esc(baseName(q))}</span>${cnt[q] > 1 ? `<span class="su-chip">×${cnt[q]}</span>` : ''}<button type="button" class="btn btn-ghost btn-sm su-pp-del" data-pp-del="${i}" aria-label="${esc(tr('pp_remove', 'Retirer de la liste'))}" title="${esc(tr('pp_remove', 'Retirer de la liste'))}"><i class="fa-solid fa-xmark"></i></button></div>`).join('') : '';
        host._paths = ord;
    };
    $('su-pp').closest('.suite-field').insertAdjacentHTML('afterend', '<div id="su-pp-list" class="su-pp-list" hidden></div>');
    $('su-pp').addEventListener('input', drawList);
    $('su-pp-list').onclick = (e) => {
        const host = $('su-pp-list'), d = e.target.closest('[data-pp-del]'), c = e.target.closest('[data-pp-clear]');
        if (c) { $('su-pp').value = ''; }
        else if (d) { const gone = host._paths[+d.dataset.ppDel]; $('su-pp').value = lines('su-pp').filter(l => splitLine(l).path !== gone).join('\n'); }
        else return;
        drawList();
    };
    drawList();
    $('su-ppr').onchange = (e) => { const o = e.target.selectedOptions[0]; if (!o || !o.value) return; $('su-pwl').value = o.dataset.x; $('su-pwd').value = o.dataset.y; if (o.dataset.z) $('su-pwh').value = o.dataset.z; };
    const body = () => {
        const counts = {}, order = [];
        lines('su-pp').forEach(l => { const m = l.match(/^(.*\S)\s+[x×]\s*(\d+)$/i), path = m ? m[1].trim() : l, n = m ? Math.max(1, Math.min(50, +m[2])) : 1; if (!(path in counts)) { counts[path] = 0; order.push(path); } counts[path] += n; });
        const step = Number(val('su-pstep') || 90), L = Number(val('su-pwl')) || 256, P = Number(val('su-pwd')) || L, H = Number(val('su-pwh')) || 256;
        return { paths: order, counts, plate: { w: L, d: P, z: H }, margin: Number(val('su-pm') || 3), mode: val('su-pmode') === 'box' ? 'box' : 'shape', rotate: step > 0, rotation_step: step || 90 };
    };
    /* « Organisation automatique » de l'éditeur : redispose, avec les réglages du formulaire, les pièces qui restent sur les plateaux. */
    const rearrange = async (placements) => {
        const counts = {}, order = []; placements.forEach(a => { if (!(a.id in counts)) { counts[a.id] = 0; order.push(a.id); } counts[a.id]++; });
        const d = await api('/api/plate/arrange', Object.assign(body(), { paths: order, counts }));
        return { plate: d.plate, plates: d.plates.map(p => ({ index: p.index, placements: p.placements.map(a => Object.assign({}, a)) })), cur: 1, sel: -1, snap: 1, mode: d.mode || 'box', unplaced: d.unplaced || [] };
    };
    wire(box, 'su-pgo', async () => {
        $('su-pbusy').hidden = false; $('su-pout').innerHTML = '';
        try {
            const d = await api('/api/plate/arrange', body());
            const state = { plate: d.plate, plates: d.plates.map(p => ({ index: p.index, placements: p.placements.map(a => Object.assign({}, a)) })), cur: 1, sel: -1, snap: 1, mode: d.mode || 'box' };
            plateEditor($('su-pout'), state, d.unplaced || [], rearrange);
        } finally { $('su-pbusy').hidden = true; }
    });
} };
function plateEditor(host, st, unplaced, rearrange) {
    const cur = () => st.plates.find(p => p.index === st.cur) || st.plates[0];
    host.innerHTML = `<div class="suite-plate">
        <div class="suite-plate-tabs">${st.plates.map(p => `<button type="button" class="btn btn-ghost btn-sm" data-plate="${p.index}">${esc(tr('plate_n', 'Plateau'))} ${p.index}</button>`).join('')}</div>
        <div class="suite-plate-main"><div class="suite-plate-view">
        <svg class="suite-bed" viewBox="0 0 ${st.plate.w} ${st.plate.d}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="${esc(tr('plate_label', 'Éditeur de plateau (vue de dessus)'))}"><g id="su-bed-g"></g></svg>
        <canvas class="suite-cloud suite-bed3d" id="su-bed3d" width="720" height="440" hidden aria-label="${esc(tr('plate_3d_label', 'Plateau en vue 3D'))}"></canvas></div>
        <aside class="suite-plate-legend" id="su-plegend" aria-label="${esc(tr('plate_legend', 'Pièces du plateau'))}"></aside></div>
        <div class="suite-plate-tools">
            ${btn('su-prot', tr('rotate', 'Pivoter de'), 'btn-ghost')} <input type="number" id="su-pang" class="settings-select" value="90" min="-359" max="359" step="5" style="width:5em" aria-label="${esc(tr('angle', 'Angle (°)'))}"> °
            <select id="su-palign" class="settings-select"><option value="">${esc(tr('align', 'Aligner…'))}</option>${['left', 'right', 'front', 'back', 'center-x', 'center-y'].map(m => `<option value="${m}">${esc(tr('al_' + m, { left: 'À gauche', right: 'À droite', front: 'Devant', back: 'Derrière', 'center-x': 'Centrer en X', 'center-y': 'Centrer en Y' }[m]))}</option>`).join('')}</select>
            <label class="suite-inline">${esc(tr('snap', 'Pas (mm)'))} <input type="number" id="su-psnap" class="settings-select" value="1" min="0.1" step="0.5" style="width:5em"></label>
            ${btn('su-pauto', tr('auto_organize', 'Organisation automatique'), 'btn-secondary')} ${btn('su-pdel', tr('remove_part', 'Retirer la pièce'), 'btn-ghost')} ${btn('su-p3d', tr('view3d_plate', 'Vue 3D'), 'btn-ghost')} ${btn('su-pcheck', tr('check_layout', 'Contrôler'), 'btn-ghost')} ${btn('su-pex', tr('export3mf', 'Exporter ce plateau (3MF)'))}
        </div>
        <div id="su-pwork" class="su-work" role="status" aria-live="polite" hidden><i class="fa-solid fa-spinner fa-spin"></i> <span></span><span class="su-work-bar" aria-hidden="true"><i></i></span></div>
        <div id="su-pinfo" class="settings-hint"></div><div id="su-pissues"></div>
        ${unplaced && unplaced.length ? `<p class="settings-hint">${esc(tr('unplaced', 'Non placées'))} : ${esc(unplaced.map(u => baseName(u.id) + ' (' + u.reason + ')').join(', '))}</p>` : ''}
        <p class="settings-hint">${esc(tr('plate_help', 'Glissez une pièce pour la déplacer ; flèches du clavier = pas fin. En mode forme réelle, les pièces peuvent s\'imbriquer (contour exact, rotation libre) ; en mode boîte, l\'empreinte est la boîte englobante. Le serveur contrôle la disposition avant l\'export 3MF.'))}</p></div>`;
    const svg = host.querySelector('svg'), g = host.querySelector('#su-bed-g');
    const name = (a) => baseName(a.id);
    function info() {
        const a = cur().placements[st.sel];
        $('su-pinfo').textContent = a ? `${name(a)} — X ${a.x.toFixed(1)} · Y ${a.y.toFixed(1)} · ${a.w.toFixed(1)} × ${a.d.toFixed(1)} × ${(a.h || 0).toFixed(1)} mm${a.rot ? ' · ' + Math.round(a.rot * 10) / 10 + '°' : ''}` : tr('select_hint', 'Sélectionnez une pièce.');
    }
    function draw() {
        const pl = st.plate, list = cur().placements, bad = new Set();
        H.issues(list, pl).forEach(x => { bad.add(x.i); if (x.j != null) bad.add(x.j); });
        g.innerHTML = `<rect x="0" y="0" width="${pl.w}" height="${pl.d}" class="suite-bed-bg"/>` + list.map((a, i) =>
            `<g data-i="${i}" class="suite-part${i === st.sel ? ' sel' : ''}${bad.has(i) ? ' bad' : ''}">` + (a.outline && a.outline.length
                ? a.outline.map(r => `<polygon points="${r.map(q => (a.x + q[0]).toFixed(2) + ',' + (pl.d - a.y - q[1]).toFixed(2)).join(' ')}"/>`).join('') + `<rect class="suite-part-box" x="${a.x}" y="${pl.d - a.y - a.d}" width="${a.w}" height="${a.d}"/>`
                : `<rect x="${a.x}" y="${pl.d - a.y - a.d}" width="${a.w}" height="${a.d}"/>`) +
            `<text x="${a.x + a.w / 2}" y="${pl.d - a.y - a.d / 2}" text-anchor="middle" dominant-baseline="middle" font-size="${Math.max(4, Math.min(a.w, a.d) / 3, pl.w / 18)}" font-weight="700">${i + 1}</text></g>`).join('');
        $('su-plegend').innerHTML = `<h5>${esc(tr('plate_n', 'Plateau'))} ${cur().index}</h5><ol>` + list.map((a, i) => `<li><button type="button" class="suite-legend-item${i === st.sel ? ' sel' : ''}${bad.has(i) ? ' bad' : ''}" data-i="${i}" title="${esc(String(a.id).replace(/#\d+$/, ''))}"><b>${i + 1}</b><span>${esc(name(a))}</span></button></li>`).join('') + '</ol>';
        host.querySelectorAll('[data-plate]').forEach(b => b.classList.toggle('active', Number(b.dataset.plate) === st.cur));
        info(); if (!cv3.hidden) draw3d(bad);
    }
    /* Vue 3D : plateau + pièces en fil de fer (hauteurs réelles), rotation au glisser, molette = zoom ; en rouge ce qui pose problème. */
    const cv3 = host.querySelector('#su-bed3d'), g3 = cv3.getContext('2d'), v3 = { yaw: -0.6, pitch: 0.7, zoom: 1 };
    function draw3d(bad) {
        const pl = st.plate, list = cur().placements, c = [pl.w / 2, pl.d / 2, Math.min(pl.z, 60) / 2], r = Math.hypot(pl.w, pl.d, Math.min(pl.z, 60)) / 2;
        const sc = Math.min(cv3.width, cv3.height) / (2.1 * r) * v3.zoom, ox = cv3.width / 2, oy = cv3.height / 2;
        g3.clearRect(0, 0, cv3.width, cv3.height); g3.lineWidth = 1.5;
        const seg = (e, col, w) => { const a = H.project(e[0], c, v3.yaw, v3.pitch), b = H.project(e[1], c, v3.yaw, v3.pitch); g3.strokeStyle = col; g3.lineWidth = w || 1.5; g3.beginPath(); g3.moveTo(ox + a[0] * sc, oy + a[1] * sc); g3.lineTo(ox + b[0] * sc, oy + b[1] * sc); g3.stroke(); };
        H.boxEdges({ x: 0, y: 0, w: pl.w, d: pl.d, h: 0.5 }).slice(0, 4).forEach(e => seg(e, '#8b8d98', 2));
        list.forEach((a, i) => { const col = bad && bad.has(i) ? '#e5484d' : (i === st.sel ? '#4ea1d3' : '#30a46c'); (a.outline && a.outline.length ? H.shapeEdges(a) : H.boxEdges(a)).forEach(e => seg(e, col, i === st.sel ? 2.5 : 1.5)); });
        g3.font = 'bold 16px sans-serif'; g3.textAlign = 'center'; g3.textBaseline = 'middle'; g3.fillStyle = '#e6eaf0';
        list.forEach((a, i) => { const q = H.project([a.x + a.w / 2, a.y + a.d / 2, Math.max(0.5, a.h || 0)], c, v3.yaw, v3.pitch); g3.fillText(String(i + 1), ox + q[0] * sc, oy + q[1] * sc - 10); });
    }
    cv3.onpointerdown = (e) => { cv3._d = [e.clientX, e.clientY]; cv3.setPointerCapture(e.pointerId); };
    cv3.onpointermove = (e) => { if (!cv3._d) return; v3.yaw += (e.clientX - cv3._d[0]) * 0.01; v3.pitch = Math.max(-1.5, Math.min(1.5, v3.pitch + (e.clientY - cv3._d[1]) * 0.01)); cv3._d = [e.clientX, e.clientY]; draw(); };
    cv3.onpointerup = cv3.onpointercancel = () => { cv3._d = null; };
    cv3.onwheel = (e) => { e.preventDefault(); v3.zoom = Math.max(0.3, Math.min(6, v3.zoom * (e.deltaY < 0 ? 1.15 : 1 / 1.15))); draw(); };
    wire(host, 'su-p3d', async () => { cv3.hidden = !cv3.hidden; svg.style.display = cv3.hidden ? '' : 'none'; $('su-p3d').textContent = cv3.hidden ? tr('view3d_plate', 'Vue 3D') : tr('view2d_plate', 'Vue de dessus'); draw(); });
    const mm = (e) => { const m = svg.getScreenCTM().inverse(), pt = svg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY; const q = pt.matrixTransform(m); return [q.x, st.plate.d - q.y]; };
    let drag = null;
    svg.onpointerdown = (e) => {
        const el = e.target.closest('[data-i]'); if (!el) { st.sel = -1; draw(); return; }
        st.sel = Number(el.dataset.i); const a = cur().placements[st.sel], p0 = mm(e); drag = { p0, x: a.x, y: a.y }; svg.setPointerCapture(e.pointerId); draw();
    };
    svg.onpointermove = (e) => {
        if (!drag) return; const a = cur().placements[st.sel], p = mm(e), step = Number($('su-psnap').value) || 1;
        a.x = H.snap(drag.x + p[0] - drag.p0[0], step); a.y = H.snap(drag.y + p[1] - drag.p0[1], step); draw();
    };
    svg.onpointerup = svg.onpointercancel = () => { if (drag) { drag = null; serverCheck(); } };
    svg.tabIndex = 0;
    svg.onkeydown = (e) => {
        const a = cur().placements[st.sel], k = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, 1], ArrowDown: [0, -1] }[e.key]; if (!a || !k) return;
        e.preventDefault(); const step = (Number($('su-psnap').value) || 1) * (e.shiftKey ? 10 : 1); a.x += k[0] * step; a.y += k[1] * step; draw(); serverCheck();
    };
    host.onclick = (e) => { const lg = e.target.closest('.suite-legend-item'); if (lg) { st.sel = Number(lg.dataset.i); draw(); return; } const b = e.target.closest('[data-plate]'); if (b) { st.cur = Number(b.dataset.plate); st.sel = -1; draw(); serverCheck(); } };
    const edit = (fn) => { const l = cur().placements; if (st.sel < 0 || !l[st.sel]) throw new Error(tr('select_hint', 'Sélectionnez une pièce.')); l[st.sel] = fn(l[st.sel]); draw(); return serverCheck(); };
    /* Rotation : le serveur renvoie la taille et le contour exacts ; on garde le centre de la boîte puis on rentre la pièce dans le plateau. */
    wire(host, 'su-prot', async () => {
        const l = cur().placements, a0 = l[st.sel]; if (st.sel < 0 || !a0) throw new Error(tr('select_hint', 'Sélectionnez une pièce.'));
        const ang = Number($('su-pang').value); if (!Number.isFinite(ang) || !ang) throw new Error(tr('angle_bad', 'Angle invalide.'));
        const rot = ((a0.rot || 0) + ang) % 360, r = await api('/api/plate/rotate', { id: a0.id, rot: rot < 0 ? rot + 360 : rot });
        const cx = a0.x + a0.w / 2, cy = a0.y + a0.d / 2;
        const n = H.clamp(Object.assign({}, a0, { rot: r.rot, w: r.w, d: r.d, h: r.h, x: cx - r.w / 2, y: cy - r.d / 2 }, st.mode === 'shape' || a0.outline ? { outline: r.outline } : {}), st.plate);
        l[st.sel] = n; draw(); await serverCheck();
    });
    $('su-palign').onchange = async (e) => { const m = e.target.value; e.target.value = ''; if (m) { try { await edit(a => H.align(a, st.plate, m)); } catch (x) { note(host, x.message, true); } } };
    const layoutBody = () => ({ layout: { plate: st.plate, plates: st.plates }, plate_index: st.cur });
    async function serverCheck() {
        try {
            const r = await api('/api/plate/check', layoutBody().layout);
            const iss = r.issues || [];
            $('su-pissues').innerHTML = iss.length ? `<ul class="suite-issues">${iss.map(x => `<li>${esc(tr('is_' + x.issue, { overlap: 'Chevauchement', out_of_plate: 'Hors du plateau', too_tall: 'Trop haute' }[x.issue] || x.issue))} — ${esc(baseName(x.id))}${x.other ? ' / ' + esc(baseName(x.other)) : ''}</li>`).join('')}</ul>` : `<p class="settings-hint">✓ ${esc(tr('layout_ok', 'Disposition valide.'))}</p>`;
        } catch (e) { note(host, e.message, true); }
    }
    wire(host, 'su-pcheck', serverCheck);
    /* Repère visuel pendant un calcul long : bandeau animé + bouton grisé en rotation (retiré à la fin, succès ou erreur). */
    const working = async (id, msg, fn) => {
        const w = $('su-pwork'), b = $(id); w.querySelector('span').textContent = msg; w.hidden = false; host.classList.add('su-busy-plate');
        if (b) { b.classList.add('su-btn-busy'); b.setAttribute('aria-busy', 'true'); }
        try { return await fn(); } finally { w.hidden = true; host.classList.remove('su-busy-plate'); if (b) { b.classList.remove('su-btn-busy'); b.removeAttribute('aria-busy'); } }
    };
    wire(host, 'su-pex', () => working('su-pex', tr('exporting', 'Export 3MF en cours…'), async () => {
        const r = await fetch(`${API}/api/plate/export`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(layoutBody()) });
        if (!r.ok) { const d = await r.json().catch(() => ({})); await serverCheck(); throw new Error(d.error || r.status); }
        const nm = `plateau-${st.cur}.3mf`, a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(await r.blob()), download: nm }); a.click();
        note(host, '✓ ' + nm + ' — ' + tr('exported', 'exporté'));
    }));
    /* Retirer la pièce sélectionnée du plateau (un plateau vidé disparaît, les autres sont renumérotés). */
    wire(host, 'su-pdel', async () => {
        const l = cur().placements; if (st.sel < 0 || !l[st.sel]) throw new Error(tr('select_hint', 'Sélectionnez une pièce.'));
        l.splice(st.sel, 1); st.sel = -1;
        if (!l.length && st.plates.length > 1) { st.plates = st.plates.filter(p => p !== cur()); st.plates.forEach((p, i) => { p.index = i + 1; }); st.cur = 1; }
        plateEditor(host, st, unplaced, rearrange);
    });
    /* Organisation automatique : toutes les pièces restantes sont redisposées, regroupées au centre de chaque plateau. */
    wire(host, 'su-pauto', async () => {
        const all = st.plates.flatMap(p => p.placements); if (!all.length || !rearrange) return;
        const n = await working('su-pauto', tr('computing', 'Calcul de la disposition…'), () => rearrange(all));
        plateEditor(host, n, n.unplaced, rearrange);
    });
    draw(); serverCheck();
}
TABS.community = { fb: 'Communauté', icon: 'people-group', async render(box) {
    const d = await api('/api/community/packs');
    const lic = d.licenses.map(l => `<option>${esc(l)}</option>`).join('');
    box.innerHTML = (d.packs.length ? `<div class="suite-scroll"><table class="suite-table"><thead><tr><th>${esc(tr('pack', 'Paquet'))}</th><th>${esc(tr('author', 'Auteur'))}</th><th>${esc(tr('license', 'Licence'))}</th><th>★</th><th>💬</th><th>Remix</th><th></th></tr></thead><tbody>${d.packs.map(p =>
        `<tr><td>${esc(p.title)}${p.hidden ? ' <i>(' + esc(tr('hidden', 'masqué')) + ')</i>' : ''}</td>${cell(p.author)}${cell(p.license)}${cell(p.favorites)}${cell(p.comments)}${cell(p.remix_of ? p.remix_of.title : '')}<td><button type="button" class="btn btn-ghost btn-sm" data-open="${esc(p.id)}">${esc(tr('open', 'Ouvrir'))}</button></td></tr>`).join('')}</tbody></table></div>` : `<p class="settings-hint">${esc(tr('empty', 'Rien à afficher pour le moment.'))}</p>`) +
        '<div id="su-cdetail"></div>' +
        `<h4>${esc(tr('publish', 'Publier un paquet'))}</h4>` + field('su-ct', tr('pack_title', 'Titre')) + `<label class="suite-field"><span>${esc(tr('license', 'Licence (obligatoire)'))}</span><select id="su-cl" class="settings-select">${lic}</select></label>` +
        `<label class="suite-field"><span>${esc(tr('remix_of', 'Remix de… (facultatif)'))}</span><select id="su-cr" class="settings-select"><option value="">—</option>${d.packs.map(p => `<option value="${esc(p.id)}">${esc(p.title)} (${esc(p.license)})</option>`).join('')}</select></label>` +
        mfield('su-cf', tr('paths', 'Fichiers (un chemin par ligne)'), 3) + btn('su-cpub', tr('publish_go', 'Publier')) +
        `<p class="settings-hint">${esc(tr('remix_rule', 'Le remix suit la licence d\'origine : ND et « Personnel » l\'interdisent, SA impose la même licence, NC impose NC. Garde-fou simple, pas un avis juridique. Commentaires et favoris restent sur cette instance.'))}</p>`;
    wire(box, 'su-cpub', async () => { const r = await api('/api/community/publish', { title: val('su-ct'), license: val('su-cl'), paths: lines('su-cf'), remix_of: val('su-cr') || undefined }); await TABS.community.render(box); note(box, '✓ ' + r.pack.title); });
    box.onclick = async (e) => {
        const b = e.target.closest('[data-open]'); if (!b) return;
        const id = b.dataset.open, host = $('su-cdetail');
        async function load() {
            const c = await api(`/api/community/${id}/comments`);
            host.innerHTML = `<h4>${esc(tr('discussion', 'Discussion'))}</h4>` + (c.lineage.length ? `<p class="settings-hint">${esc(tr('lineage', 'Filiation'))} : ${c.lineage.map(x => esc(x.title || '?') + ' (' + esc(x.license) + ')').join(' ← ')}</p>` : '') +
                `<p>${btn('su-cfav', (c.favorite ? '★ ' : '☆ ') + tr('favorite', 'Favori') + ' (' + c.favorites + ')', 'btn-ghost')}</p>` +
                (c.comments.length ? `<ul class="suite-comments">${c.comments.map(x => `<li>${esc(x.text)} <small>${esc(fmt(x.at))}</small> <button type="button" class="btn btn-ghost btn-sm" data-del="${x.id}">×</button></li>`).join('')}</ul>` : `<p class="settings-hint">${esc(tr('no_comment', 'Aucun commentaire.'))}</p>`) +
                field('su-ctext', tr('comment', 'Votre commentaire')) + btn('su-csend', tr('send', 'Envoyer'), 'btn-ghost') + ' ' + field('su-cdest', tr('dest', 'Dossier de destination (import)'), '/…/sources/') + btn('su-cimp', tr('import', 'Importer ce paquet'), 'btn-ghost');
            wire(host, 'su-cfav', async () => { await api(`/api/community/${id}/favorite`, {}); await load(); });
            wire(host, 'su-csend', async () => { await api(`/api/community/${id}/comments`, { text: val('su-ctext') }); await load(); });
            wire(host, 'su-cimp', async () => { const r = await api('/api/community/import', { pack_id: id, dest: val('su-cdest') }); note(host, `✓ ${r.files} · ${r.folder}`); });
            host.onclick = async (ev) => { const x = ev.target.closest('[data-del]'); if (x) { try { await api(`/api/community/${id}/comments/${x.dataset.del}`, undefined, 'DELETE'); await load(); } catch (er) { note(host, er.message, true); } } };
        }
        try { await load(); } catch (x) { note(box, x.message, true); }
    };
} };
TABS.gcode = { fb: 'Archives G-code', icon: 'file-zipper', async render(box) {
    box.innerHTML = `<div class="su-notice su-notice-info"><i class="fa-solid fa-circle-info"></i><span>${esc(tr('gcode_hint', 'Conserve (compressé, empreinte SHA-256) le G-code réellement imprimé, rattaché à une ligne de l\'historique. 200 Mo maximum par archive.'))}</span></div>` +
        `<section class="su-card"><h4><i class="fa-solid fa-file-zipper"></i> ${esc(tr('gcode_title', 'Archive d\'une impression'))}</h4>` +
        `<input type="hidden" id="su-gpath"><div class="su-inline"><button type="button" class="btn btn-secondary btn-sm suite-pick" data-pick="su-gpath" data-multi="0"><i class="fa-solid fa-images"></i> ${esc(tr('pick_printed', 'Choisir le fichier imprimé'))}</button><span id="su-gname" class="settings-hint">${esc(tr('no_file', 'Aucun fichier sélectionné'))}</span>` +
        `<select id="su-gid" class="settings-select su-gsel" aria-label="${esc(tr('hist_pick', 'Impression de l\'historique'))}" disabled><option value="">${esc(tr('hist_pick', 'Impression de l\'historique'))}</option></select>` +
        `<label class="btn btn-secondary btn-sm suite-file"><i class="fa-solid fa-folder-open"></i> ${esc(tr('gcode_file_opt', 'G-code (facultatif)'))}<input type="file" id="su-gf" accept=".gcode,.bgcode,.gco,.g" hidden></label><span id="su-gfn" class="settings-hint"></span>` +
        `${btn('su-gst', tr('archive', 'Archiver'))}${btn('su-ginfo', tr('status', 'État'), 'btn-secondary')}${btn('su-gdl', tr('download', 'Télécharger'), 'btn-secondary')}${btn('su-gdel', tr('delete', 'Supprimer'), 'btn-ghost su-danger')}</div></section><div id="su-gout"></div>`;
    $('su-gf').onchange = () => { $('su-gfn').textContent = ($('su-gf').files[0] || {}).name || ''; };
    $('su-gpath').addEventListener('input', async () => {
        const path = $('su-gpath').value, sel = $('su-gid'); $('su-gname').textContent = baseName(path) || tr('no_file', 'Aucun fichier sélectionné');
        sel.disabled = true; sel.innerHTML = `<option value="">${esc(tr('hist_pick', 'Impression de l\'historique'))}</option>`;
        if (!path) return;
        try {
            const d = await api('/api/print-history/by-file?path=' + encodeURIComponent(path)), h = d.history || [];
            sel.innerHTML = h.length ? h.map(x => `<option value="${esc(x.id)}">${esc([String(x.sent_at || '').slice(0, 16), x.result || '', x.printer_name || ''].filter(Boolean).join(' · '))}</option>`).join('') : `<option value="">${esc(tr('hist_none', 'Aucune impression enregistrée pour ce fichier'))}</option>`;
            sel.disabled = !h.length;
        } catch (e) { note(box, e.message, true); }
    });
    const id = () => { const v = parseInt(val('su-gid'), 10); if (!v) throw new Error(tr('hist_choose', 'Choisissez d\'abord le fichier imprimé.')); return v; };
    wire(box, 'su-gst', async () => {
        const f = $('su-gf').files[0], fd = new FormData(); if (f) fd.append('file', f);
        const r = await fetch(`${API}/api/print-history/${id()}/gcode`, { method: 'POST', body: fd }); const j = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(j.error || r.status);
        $('su-gout').innerHTML = `<p class="settings-hint">✓ ${esc(j.name)} — ${esc(j.raw_size)} → ${esc(j.gz_size)} octets<br>SHA-256 ${esc(j.sha256)}</p>`;
    });
    wire(box, 'su-ginfo', async () => { const d = await api(`/api/print-history/${id()}/gcode`); $('su-gout').innerHTML = d.archived ? `<p class="settings-hint">${esc(d.archive.name)} — ${esc(d.archive.raw_size)} → ${esc(d.archive.gz_size)}<br>SHA-256 ${esc(d.archive.sha256)}</p>` : `<p class="settings-hint">${esc(tr('not_archived', 'Pas d\'archive pour cette impression.'))}</p>`; });
    wire(box, 'su-gdl', async () => {
        const r = await fetch(`${API}/api/print-history/${id()}/gcode/download`); if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || r.status);
        const a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(await r.blob()), download: `impression-${id()}.gcode` }); a.click();
    });
    wire(box, 'su-gdel', async () => { await api(`/api/print-history/${id()}/gcode`, undefined, 'DELETE'); note(box, '✓'); });
} };
/* Dates : on les AFFICHE dans le format de l'utilisateur (réglage de sa langue / de son système), on les ENVOIE toujours en AAAA-MM-JJ. */
const dayFmt = (iso) => { const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso || '')); if (!m) return iso || ''; try { return new Date(+m[1], +m[2] - 1, +m[3]).toLocaleDateString(); } catch (e) { return iso; } };
TABS.licenses = { fb: 'Licences', icon: 'file-contract', async render(box) {
    const d = await api('/api/licenses/expiring?days=60');
    box.innerHTML = `<p class="settings-hint">${esc(d.count)} ${esc(tr('lic_count', 'licence(s) expirée(s) ou proche(s) de l\'échéance (60 jours)'))} — ${esc(d.expired || 0)} ${esc(tr('lic_expired', 'expirée(s)'))}. ${esc(tr('lic_notify', 'Une notification est créée une fois par fichier et par état ; rien n\'est supprimé automatiquement.'))}</p>` +
        table(d.items, [['name', 'Fichier'], ['license', 'Licence'], ['expires', 'Échéance', dayFmt], ['status', 'État', v => v === 'expired' ? tr('lic_expired1', 'expirée') : tr('lic_soon', 'bientôt')], ['days_left', 'Jours']]) +
        `<h4>${esc(tr('lic_set', 'Définir une échéance'))}</h4>` + '<div class="su-line">' + pfield('su-lp', tr('path', 'Chemin du fichier')) +
        `<label class="suite-field suite-field-md"><span>${esc(tr('lic_date2', 'Date d\'échéance (vide pour effacer)'))}</span><input type="date" id="su-ld" class="settings-select"></label>` + btn('su-lgo', tr('save', 'Enregistrer')) + '</div>' +
        `<p class="settings-hint">${esc(tr('lic_date_hint', 'La date s\'affiche dans le format de votre système ; vous pouvez la choisir au calendrier ou la saisir.'))}</p>`;
    wire(box, 'su-lgo', async () => { await api('/api/files/license-expiry', { path: val('su-lp'), date: val('su-ld') }, 'PUT'); await TABS.licenses.render(box); note(box, '✓'); });
} };
TABS.part = { fb: 'Fiche pièce', icon: 'cube', async render(box) {
    box.innerHTML = `<p class="settings-hint">${esc(tr('part_hint', 'Tout ce que Stellio sait d\'un modèle : origine et licence, versions, impressions, meilleure combinaison, G-code archivés, photos.'))}</p>` + '<div class="su-line">' + pfield('su-pp', tr('path', 'Chemin du modèle'), '/…/piece.stl') + btn('su-ppgo', tr('part_open', 'Ouvrir la fiche')) + '</div><div id="su-ppout"></div>';
    wire(box, 'su-ppgo', async () => {
        const d = await api(`/api/part-dossier?path=${encodeURIComponent(val('su-pp'))}`), o = d.origin || {}, p = d.prints || {};
        const kb = (n) => n == null ? '—' : (n / 1024).toFixed(n > 1048576 ? 0 : 1) + ' Ko';
        const lic = o.license ? esc(o.license) + (o.expires ? ` — ${esc(tr('part_until', 'jusqu\'au'))} ${esc(o.expires)}${o.status === 'expired' ? ' ⚠ ' + esc(tr('lic_expired1', 'expirée')) : (o.status === 'soon' ? ' ⚠ ' + esc(tr('lic_soon', 'bientôt')) : '')}` : '') : '—';
        $('su-ppout').innerHTML = `<h4>${esc(d.name)} <small>${esc(kb(d.size))}</small></h4>` +
            `<p class="settings-hint">${esc(tr('author', 'Auteur'))} : ${esc(o.author || '—')} · ${esc(tr('license', 'Licence'))} : ${lic}${o.source_url ? ' · <a href="' + esc(o.source_url) + '" target="_blank" rel="noopener noreferrer">' + esc(tr('part_source', 'source')) + '</a>' : ''}</p>` +
            `<p>${esc(tr('part_prints', 'Impressions'))} : <b>${esc(p.total || 0)}</b> — ✓ ${esc(p.success || 0)} · ✗ ${esc(p.failed || 0)}</p>` +
            (d.best ? `<p class="settings-hint">★ ${esc(tr('part_best', 'Meilleure combinaison'))} : v${esc(d.best.version)} + ${esc(d.best.profile || '—')} (${esc(d.best.success)}/${esc(d.best.total)})</p>` : '') +
            `<h4>${esc(tr('part_versions', 'Versions'))}</h4>` + table(d.versions, [['version', 'Version', v => 'v' + v], ['note', 'Note'], ['created_at', 'Date', v => fmt(v)], ['prints', tr('part_prints', 'Impressions')], ['success', '✓']]) +
            `<h4>${esc(tr('part_recent', 'Dernières impressions'))}</h4>` + table(p.recent, [['sent_at', 'Date'], ['model_version', 'Version', v => v == null ? '—' : 'v' + v], ['profile', 'Profil'], ['printer', 'Imprimante'], ['result', 'Résultat']]) +
            `<h4>${esc(tr('part_gcode', 'G-code archivés'))}</h4>` + table(d.gcode, [['history_id', '#'], ['name', 'Fichier'], ['gz_size', 'Taille', v => kb(v)], ['sha256', 'SHA-256', v => String(v || '').slice(0, 12) + '…']]) +
            `<h4>${esc(tr('part_photos', 'Photos du résultat'))}</h4><p class="settings-hint">${esc((d.photos || []).length)} ${esc(tr('part_photos_n', 'photo(s) rattachée(s)'))}</p>`;
    });
} };
TABS.check = { fb: 'Vérif. impression', icon: 'clipboard-check', async render(box) {
    let printers = []; try { printers = await api('/api/printers'); } catch (e) { printers = []; }
    const bed = (p) => { const c = p.config || {}; return [Number(c.bed_x), Number(c.bed_y), Number(c.bed_z)]; };
    const withBed = (Array.isArray(printers) ? printers : []).filter(p => { const v = bed(p); return v[0] > 0 && v[1] > 0; });
    const nf = (id, label, v) => `<label class="suite-field suite-field-sm"><span>${esc(label)}</span><input type="number" id="${id}" class="settings-select" min="1" step="1" value="${v}"></label>`;
    box.innerHTML = `<p class="settings-hint">${esc(tr('check_hint', 'Avant d\'imprimer : surplombs, supports estimés, accroche de la base, stabilité, et le meilleur sens pour poser la pièce.'))}</p>` + `<div class="su-line">${pfield('su-ck', tr('path', 'Chemin du modèle'), '/…/piece.stl')}<label class="suite-field suite-field-md"><span>${esc(tr('plate_printer', 'Imprimante'))}</span><select id="su-ckpr" class="settings-select"><option value="">${esc(tr('printer_manual', 'Saisie manuelle'))}</option>${withBed.map(p => { const v = bed(p); return `<option value="${esc(p.id)}" data-x="${v[0]}" data-y="${v[1]}" data-z="${v[2] > 0 ? v[2] : ''}">${esc(p.name)} (${v[0]}×${v[1]}${v[2] > 0 ? '×' + v[2] : ''})</option>`; }).join('')}</select></label>` +
        `${nf('su-ckx', tr('check_bed', 'Plateau X (mm)'), 220)}${nf('su-cky', 'Y (mm)', 220)}${nf('su-ckz', 'Z (mm)', 250)}${nf('su-cka', tr('check_angle', 'Angle de surplomb (°)'), 45)}${btn('su-ckgo', tr('check_run', 'Vérifier'))}</div><div id="su-ckout"></div>`;
    $('su-ckpr').onchange = (e) => { const o = e.target.selectedOptions[0]; if (!o || !o.value) return; $('su-ckx').value = o.dataset.x; $('su-cky').value = o.dataset.y; if (o.dataset.z) $('su-ckz').value = o.dataset.z; };
    wire(box, 'su-ckgo', async () => {
        const body = { path: val('su-ck') }, x = +val('su-ckx'), y = +val('su-cky'), z = +val('su-ckz'), a = +val('su-cka');
        if (x > 0 && y > 0 && z > 0) body.bed = { x, y, z };
        if (a > 0) body.angle = a;
        const d = await api('/api/print-check', body), c = d.current || {}, b = d.best || {}, bm = b.metrics || {};
        const msg = { not_watertight: tr('ck_not_watertight', 'Maillage non étanche : le slicer devra le réparer.'), inverted_normals: tr('ck_inverted', 'Normales inversées : le volume est négatif.'),
            too_big: tr('ck_too_big', 'La pièce ne tient dans le plateau dans aucune orientation.'), fits_only_rotated: tr('ck_fits_rotated', 'Ne tient dans le plateau que dans une autre orientation.'),
            overhangs: tr('ck_overhangs', 'Surplombs importants : des supports seront nécessaires.'), small_base: tr('ck_small_base', 'Petite surface de contact avec le plateau : risque de décollement.'),
            tall_thin: tr('ck_tall_thin', 'Pièce haute et fine : risque de vibration ou de chute.'), better_orientation: tr('ck_better', 'Une autre orientation réduit nettement les supports.') };
        const ico = { error: '✗', warning: '⚠', info: 'ℹ' };
        const issues = (d.issues || []).map(i => `<li>${ico[i.level] || ''} ${esc(msg[i.code] || i.code)}</li>`).join('') || `<li>✓ ${esc(tr('ck_ok', 'Aucun problème détecté.'))}</li>`;
        const dl = (o) => `<button type="button" class="btn btn-ghost btn-sm" id="su-ckdl" data-down="${esc((o.down || []).join(','))}"><i class="fa-solid fa-download"></i> ${esc(tr('check_download', 'Télécharger la copie orientée'))}</button>`;
        $('su-ckout').innerHTML = `<h4>${esc(d.name)} <small>${esc((d.triangles || 0).toLocaleString())} ${esc(tr('check_tris', 'triangles'))} · ${esc(d.volume_cm3)} cm³</small></h4><ul class="suite-list">${issues}</ul>` +
            `<p>${esc(tr('check_now', 'Orientation actuelle'))} : ${esc((c.size || []).join(' × '))} mm · ${esc(tr('check_over', 'surplombs'))} ${esc(Math.round((c.overhang_ratio || 0) * 100))} % · ${esc(tr('check_support', 'supports estimés'))} ${esc(c.support_volume_cm3)} cm³ · ${esc(tr('check_base', 'base'))} ${esc(c.base_area)} mm²</p>` +
            `<h4>${esc(tr('check_best', 'Orientation conseillée'))}${d.gain != null ? ` <small>−${esc(Math.round(d.gain * 100))} %</small>` : ''}</h4>` +
            `<p>${esc((bm.size || []).join(' × '))} mm · ${esc(tr('check_over', 'surplombs'))} ${esc(Math.round((bm.overhang_ratio || 0) * 100))} % · ${esc(tr('check_support', 'supports estimés'))} ${esc(bm.support_volume_cm3)} cm³ · ${esc(tr('check_base', 'base'))} ${esc(bm.base_area)} mm²</p><p>${dl(b)}</p>` +
            `<h4>${esc(tr('check_others', 'Autres orientations'))}</h4>` + table((d.orientations || []).map(o => ({ down: o.label + ' ' + (o.down || []).map(v => (+v).toFixed(2)).join(' '), h: o.metrics.height, over: Math.round(o.metrics.overhang_ratio * 100) + ' %', sup: o.metrics.support_volume_cm3, base: o.metrics.base_area, fits: o.fits ? '✓' : '✗' })),
                [['down', tr('check_down', 'Posée sur')], ['h', tr('check_height', 'Hauteur (mm)')], ['over', tr('check_over', 'surplombs')], ['sup', tr('check_support', 'supports estimés') + ' (cm³)'], ['base', tr('check_base', 'base') + ' (mm²)'], ['fits', tr('check_fits', 'Tient')]]) +
            `<p class="settings-hint">${esc(tr('check_note', 'Estimation de pré-contrôle : le volume de supports est une borne haute, pas le résultat de votre slicer.'))}</p>`;
        wire(box, 'su-ckdl', async () => {
            const r = await fetch(`${API}/api/print-check/oriented?path=${encodeURIComponent(d.path)}&down=${encodeURIComponent($('su-ckdl').dataset.down)}`);
            if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || r.status);
            const nm = (d.name || 'modele').replace(/\.[^.]+$/, '') + '_oriente.stl';
            Object.assign(document.createElement('a'), { href: URL.createObjectURL(await r.blob()), download: nm }).click();
            note(box, '✓ ' + nm);
        });
    });
} };
TABS.needs = { fb: 'Besoins matière', icon: 'weight-hanging', async render(box) {
    box.innerHTML = `<p class="settings-hint">${esc(tr('needs_hint', 'Ce qu\'il faut de matière pour la file d\'impression et les projets en cours, face au stock : manque et bobines à commander.'))}</p><div id="su-nout"><p class="settings-hint">…</p></div>`;
    const d = await api('/api/filament/needs'), rows = d.materials || [], g = (v) => v == null ? '—' : v + ' g';
    const warn = rows.reduce((a, r) => a + (r.unknown_weight || 0), 0), rough = rows.reduce((a, r) => a + (r.rough || 0), 0), assumed = rows.reduce((a, r) => a + (r.assumed_material || 0), 0);
    $('su-nout').innerHTML = (rows.length ? table(rows.map(r => ({ ...r, short: r.shortfall_g > 0 ? '⚠ ' + r.shortfall_g + ' g' : '✓', buy: r.spools_to_buy > 0 ? r.spools_to_buy : '—', days: r.days_left == null ? '—' : r.days_left + ' ' + tr('needs_days', 'j') })),
            [['material', tr('needs_material', 'Matière')], ['stock_g', tr('needs_stock', 'Stock'), g], ['queue_g', tr('needs_queue', 'File'), g], ['projects_g', tr('needs_projects', 'Projets'), g], ['short', tr('needs_short', 'Manque')], ['buy', tr('needs_buy', 'Bobines à commander')], ['days', tr('needs_days_left', 'Autonomie')]])
        : `<p class="settings-hint">${esc(tr('needs_empty', 'Rien de prévu : la file d\'impression et les projets sont vides.'))}</p>`) +
        (rough ? `<p class="settings-hint">≈ ${esc(rough)} ${esc(tr('needs_rough', 'poids estimé(s) à partir de la géométrie (ordre de grandeur, pas le résultat du slicer)'))}</p>` : '') +
        (warn ? `<p class="settings-hint">⚠ ${esc(warn)} ${esc(tr('needs_unknown', 'modèle(s) sans poids connu : non comptés'))}</p>` : '') +
        (assumed ? `<p class="settings-hint">ℹ ${esc(assumed)} ${esc(tr('needs_assumed', 'modèle(s) sans matière indiquée : comptés en PLA'))}</p>` : '') +
        `<p class="settings-hint">${esc(tr('needs_spool', 'Bobine de référence'))} : ${esc(d.spool_g)} g</p>`;
} };
const FAB_TITLE = { diagnose_failure: ['Analyse des échecs', 'Pourquoi des impressions ratent, et quoi corriger'], suggest_material: ['Matière conseillée', 'Matières classées par fiabilité pour ce modèle'], suggest_settings: ['Réglages qui ont réussi', 'Ce qui a marché pour ce modèle'], similar_models: ['Modèles de forme proche', 'Pièces qui ressemblent à ce modèle, avec leur taux de réussite'] };
const FAB_FACTOR = { material: 'Matière', printer: 'Imprimante', nozzle_band: 'Température de buse' };
const FAB_AI = { ai_unreadable: 'La réponse de l\'IA n\'a pas pu être lue : la question a été analysée avec les règles intégrées.', ai_error: 'L\'IA n\'a pas répondu : la question a été analysée avec les règles intégrées.' };
TABS.fab = { fb: 'Assistant fabrication', icon: 'robot', async render(box) {
    const ex = [tr('fab_ex1', 'Pourquoi mes impressions échouent-elles ?'), tr('fab_ex2', 'Quels réglages ont marché pour Bolt ?'), tr('fab_ex3', 'Quelle matière pour Bolt ?'), tr('fab_ex4', 'Quelles pièces ressemblent à Bolt ?')];
    box.innerHTML = `<p class="settings-hint">${esc(tr('fab_intro', 'Posez une question sur vos impressions passées : l\'assistant lit votre historique (réussites, échecs, matières, réglages). Citez le nom d\'un fichier pour une réponse sur un modèle précis. Rien n\'est modifié sans votre accord.'))}</p>` +
        '<div class="su-line">' + field('su-fq', tr('question', 'Question'), ex[0]) + btn('su-fgo', tr('ask', 'Demander')) + '</div>' +
        `<div class="su-chips">${ex.map(x => `<button type="button" class="su-chip su-chip-btn" data-fex="${esc(x)}">${esc(x)}</button>`).join('')}</div><div id="su-fout"></div>`;
    const fmtVal = (v) => v == null || v === '' ? '—' : esc(v);
    const show = (d) => {
        const q = d.query, ttl = FAB_TITLE[q], pr = d.params || {}, sm = d.summary || {};
        const chips = [pr.model ? `${tr('fab_model', 'Modèle')} : ${pr.model}` : '', pr.material ? `${tr('fab_material', 'Matière')} : ${pr.material}` : '', pr.printer_id ? `${tr('fab_printer', 'Imprimante')} #${pr.printer_id}` : ''].filter(Boolean);
        let h = '';
        if (d.error) h += `<p class="settings-hint su-warn">${esc(tr('fab_error', 'Je n\'ai pas compris la question.'))} ${esc(d.error)}</p>`;
        if (ttl) h += `<h4>${esc(tr('fab_q_' + q, ttl[0]))} <small class="su-dim">${esc(tr('fab_qd_' + q, ttl[1]))}</small></h4>` + (chips.length ? `<p>${chips.map(c => `<span class="su-chip">${esc(c)}</span>`).join(' ')}</p>` : '');
        const ai = String(d.ai_note || ''); if (ai) h += `<p class="settings-hint">ℹ ${esc(ai.startsWith('ai_rejected') ? tr('fab_ai_rejected', 'L\'IA a proposé une analyse non valable : les règles intégrées ont pris le relais.') : tr('fab_' + ai, FAB_AI[ai] || ai))}</p>`;
        if (q === 'diagnose_failure' && sm.rated != null) h += `<p>${esc(sm.rated)} ${esc(tr('fab_rated', 'impression(s) notée(s)'))} — ${esc(sm.failed || 0)} ${esc(tr('fab_failed', 'échouée(s)'))}${sm.failure_rate != null ? ` (${esc(sm.failure_rate)} %)` : ''}</p>`;
        if (q === 'suggest_settings' && sm.successes != null) h += `<p>${esc(sm.successes)} ${esc(tr('fab_successes', 'impression(s) réussie(s)'))}${sm.rated != null ? ' / ' + esc(sm.rated) : ''}</p>`;
        const rows = d.rows || [];
        if (rows.length) {
            if (q === 'diagnose_failure') h += `<p class="settings-hint">${esc(tr('fab_watch', 'Facteurs à surveiller (taux d\'échec supérieur à la moyenne)'))}</p>` + table(rows, [['factor', tr('fab_factor', 'Facteur'), v => tr('fab_f_' + v, FAB_FACTOR[v] || v)], ['value', tr('fab_value', 'Valeur')], ['prints', tr('fab_prints', 'Impressions')], ['failed', tr('fab_failed2', 'Échecs')], ['rate', tr('fab_rate', 'Taux d\'échec'), v => v + ' %']]);
            else if (q === 'suggest_material') h += table(rows, [['material', tr('fab_material', 'Matière')], ['prints', tr('fab_prints', 'Impressions')], ['success', tr('fab_ok', 'Réussies')], ['rate', tr('fab_rate_ok', 'Taux de réussite'), v => v + ' %'], ['source', tr('fab_source', 'Source')]]);
            else if (q === 'suggest_settings') h += table(rows, [['setting', tr('fab_setting', 'Réglage')], ['value', tr('fab_value', 'Valeur')]]);
            else if (q === 'similar_models') h += table(rows, [['name', tr('fab_file', 'Fichier')], ['similarity', tr('sim_prox', 'Proximité'), v => v == null ? '' : v + ' %'], ['prints', tr('fab_prints', 'Impressions')], ['rate', tr('fab_rate_ok', 'Taux de réussite'), v => v == null ? '—' : v + ' %']]);
        }
        if ((d.tips || []).length) h += `<h4>${esc(tr('fab_tips', 'Pistes'))}</h4><ul class="suite-list">${d.tips.map(t => `<li>${esc(t)}</li>`).join('')}</ul>`;
        (d.notes || []).forEach(n => { h += `<p class="settings-hint">ℹ ${esc(n)}</p>`; });
        if (ttl && !rows.length && !(d.tips || []).length) h += `<p class="settings-hint">${esc(tr('fab_hint_model', 'Pas de résultat. Citez le nom exact d\'un fichier déjà imprimé (par exemple « Bolt ») et pensez à noter vos impressions (réussie / ratée) : l\'assistant s\'appuie sur cet historique.'))}</p>`;
        if ((d.proposals || []).length) h += `<h4>${esc(tr('fab_proposals', 'Propositions'))}</h4>` + d.proposals.map((x, i) => `<p><button type="button" class="btn btn-secondary btn-sm" data-fprop="${i}">${esc(x.label || x.target)}</button></p>`).join('');
        $('su-fout').innerHTML = h || `<p class="settings-hint">${esc(tr('empty', 'Rien à afficher pour le moment.'))}</p>`;
        $('su-fout')._props = d.proposals || [];
    };
    const ask = async () => { $('su-fout').innerHTML = `<p class="settings-hint"><i class="fa-solid fa-spinner fa-spin"></i> ${esc(tr('fab_thinking', 'Analyse en cours…'))}</p>`; show(await api('/api/fab/ask', { question: val('su-fq') || ex[0] })); };
    wire(box, 'su-fgo', ask);
    box.onclick = async (e) => {
        const x = e.target.closest('[data-fex]'); if (x) { $('su-fq').value = x.dataset.fex; try { await ask(); } catch (er) { note(box, er.message, true); } return; }
        const p = e.target.closest('[data-fprop]'); if (!p) return; const pr = $('su-fout')._props[+p.dataset.fprop];
        try { await api('/api/fab/apply', { action: pr.action, path: pr.path, target: pr.target, confirm: true }); p.disabled = true; note(box, '✓ ' + tr('fab_applied', 'Proposition appliquée')); } catch (er) { note(box, er.message, true); }
    };
} };

let current = 'jobs';
/* Onglets présents mais grisés (pas encore proposés dans cette version). Les tests peuvent les rouvrir. */
const SOON = { community: true };
/* « Plugins » n'est plus un onglet de l'Atelier avancé : il a sa propre page dans le menu Outils. */
const HIDDEN = { plugins: true };
/* Onglets fournis par un plugin intégré : masqués tant que ce plugin n'est pas activé (voir applyHostFeatures) */
const TAB_PLUGIN = { plate: 'plate-studio', sync: 'sharing', community: 'sharing', needs: 'stellio-pro', fab: 'ai-assistant' };
function serverEdition() { try { return !!(typeof stellioAppConfig !== 'undefined' && stellioAppConfig && stellioAppConfig.server_edition); } catch (e) { return false; } }
const serverOnly = (k) => k === 'sync' && !serverEdition();
function build(root) {
    root.innerHTML = '<div id="su-body" class="suite-body bp-card"></div>';
}
/* Bouton « Réinitialiser » : remet les champs à leur valeur d'origine et efface les résultats affichés. */
function addReset(box) {
    if (box.querySelector('.su-audit-bar')) return;                              // le journal n'a pas de champs à vider : sa liste « lignes par page » doit rester
    const host = box.querySelector('.su-line, .su-actions'); if (!host || host.querySelector('.su-reset')) return;
    const b = Object.assign(document.createElement('button'), { type: 'button', className: 'btn btn-ghost btn-sm su-reset', title: tr('reset_tip', 'Vider les champs et les résultats') });
    b.innerHTML = '<i class="fa-solid fa-rotate-left"></i> ' + esc(tr('reset', 'Réinitialiser'));
    b.onclick = () => {
        box.querySelectorAll('input, textarea').forEach(i => { if (i.type !== 'button') i.value = i.defaultValue; });
        box.querySelectorAll('textarea').forEach(i => i.dispatchEvent(new Event('input', { bubbles: true })));
        box.querySelectorAll('select').forEach(x => { x.selectedIndex = 0; x.dispatchEvent(new Event('change')); });
        box.querySelectorAll('[id^="su-"][id$="out"], #su-pissues, .suite-msg').forEach(o => { o.innerHTML = ''; });
        const bz = $('su-pbusy'); if (bz) bz.hidden = true;
    };
    host.appendChild(b);
}
let showSeq = 0;
async function show(k) {
    current = k;
    const my = ++showSeq;                                   // un onglet lent (Similaires…) ne doit pas écraser celui qu'on vient d'ouvrir
    const h = document.getElementById('suite-page-title'); if (h && TABS[k]) h.innerHTML = `<i class="fa-solid fa-${TABS[k].icon}"></i> ${esc(tr('tab_' + k, TABS[k].fb))}`;
    const host = $('su-body'); host.innerHTML = '';
    const need = TAB_PLUGIN[k];
    if (need && window.STELLIO_FEATURES && window.STELLIO_FEATURES[need] === false) {      // plugin désactivé : message clair au lieu d'une erreur « 404 »
        host.innerHTML = `<div class="su-pane"><p class="settings-hint"><i class="fa-solid fa-puzzle-piece"></i> ${esc(tr('needs_plugin', 'Cette page est fournie par un plugin intégré qui n\'est pas activé. Activez-le dans Plugins, puis redémarrez Stellio.'))}</p></div>`;
        return;
    }
    host.classList.toggle('su-plain', !!(TABS[k] && TABS[k].plain));   // page sans cadre global (Collections : bannières posées directement sur la page, comme Filament)
    const box = Object.assign(document.createElement('div'), { className: 'su-pane' }); box.innerHTML = '<p class="settings-hint">…</p>'; host.appendChild(box);
    try { await TABS[k].render(box); if (my === showSeq) addReset(box); } catch (e) { if (my !== showSeq) return; box.innerHTML = `<p class="settings-hint">${esc(e.data && e.data.code === 'server_edition_only' ? tr('server_only', 'Fonction réservée à l\'édition serveur.') : (e.message || tr('unavailable', 'Indisponible.')))}</p>`; }
}
/* Appelée par la navigation quand la page « Atelier avancé » s'affiche. */
let pendingTab = '';
function onShow() {
    let root = $('suite-root');
    if (!root) { root = Object.assign(document.createElement('div'), { id: 'suite-root' }); document.body.appendChild(root); }
    try { if (typeof IS_VIEWER !== 'undefined' && IS_VIEWER && !window.STELLIO_DEMO) { root.innerHTML = `<p class="settings-hint">${esc(tr('owner_only', 'Réservé au propriétaire.'))}</p>`; return; } } catch (e) { return; }
    if (!root.querySelector('#su-body')) build(root);
    const nb = document.querySelector('.nav-btn.active[data-suite-tab]');
    if (pendingTab) { current = pendingTab; pendingTab = ''; } else if (nb) current = nb.dataset.suiteTab;   // un onglet demandé sans entrée de menu (Notifications) ne doit pas être écrasé par l'entrée active
    return show(TABS[current] && !SOON[current] && !HIDDEN[current] && !serverOnly(current) ? current : 'jobs');
}
/* Page « Plugins » du menu Outils. */
function onShowPlugins() {
    plOpen.clear();   // sections repliées à chaque nouvelle visite de la page
    let root = $('plugins-root');
    if (!root) { root = Object.assign(document.createElement('div'), { id: 'plugins-root', className: 'suite-body bp-card' }); document.body.appendChild(root); }
    try { if (typeof IS_VIEWER !== 'undefined' && IS_VIEWER && !window.STELLIO_DEMO) { root.innerHTML = `<p class="settings-hint">${esc(tr('owner_only', 'Réservé au propriétaire.'))}</p>`; return; } } catch (e) { return; }
    root.classList.add('suite-body', 'bp-card');
    const box = Object.assign(document.createElement('div'), { className: 'su-pane' }); box.innerHTML = '<p class="settings-hint">…</p>'; root.innerHTML = ''; root.appendChild(box);
    return TABS.plugins.render(box).catch((e) => { box.innerHTML = `<p class="settings-hint">${esc(e.message || tr('unavailable', 'Indisponible.'))}</p>`; });
}
/* Ouvre la page (et l'onglet demandé). Sans navigation dans la page (tests), la zone est créée sur place. */
function open(tab) {
    if (tab === 'plugins') { const nb = document.querySelector('.nav-btn[data-page="plugins"]'); if (nb) { nb.click(); return; } return onShowPlugins(); }
    if (tab && TABS[tab] && !SOON[tab] && !serverOnly(tab)) { current = tab; pendingTab = tab; setTimeout(() => { pendingTab = ''; }, 1000); }
    const nav = document.querySelector(`.nav-btn[data-suite-tab="${current}"]`) || document.querySelector('.nav-btn[data-page="suite"]');
    if (nav) { nav.click(); return; }
    return onShow();
}

/* ───────── Plugins avec une page : menu « Plugins » + cadre isolé ─────────
   La page du plugin est un HTML autonome affiché dans un <iframe sandbox="allow-scripts"> (origine opaque : ni cookies, ni stockage de Stellio)
   avec une politique CSP qui lui interdit tout accès réseau. Elle ne parle à Stellio que par cette passerelle (postMessage), en LECTURE SEULE
   (GET /api/…), et seulement si le plugin a la permission « api:read ». */
const PV_DENY = ['plugins', 'auth', 'settings', 'accounts', 'account-models', 'security', 'sessions', 'guests', 'backup', 'audit', 'diagnostic', 'update', 'smtp', 'mqtt', 'push', 'users', 'tokens', 'api-keys'].map(d => '/api/' + d);
const PV_CSP = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; media-src data: blob:; worker-src blob:; connect-src 'none'; form-action 'none'; frame-src 'none'; base-uri 'none'";
const PV_CLIENT = "(function(){var n=0,w={};var S=window.stellio={theme:{},lang:'fr',ready:false,api:function(p,as,o){return new Promise(function(ok,ko){var i=++n;w[i]={ok:ok,ko:ko};parent.postMessage({type:'stellio.api',id:i,path:p,as:as||'json',method:(o&&o.method)||'GET',body:(o&&o.body)},'*');});}};" +
    "function th(t){var r=document.documentElement.style;for(var k in t)r.setProperty('--st-'+k,t[k]);}" +
    "window.addEventListener('message',function(e){var d=e.data||{};if(d.type==='stellio.reply'&&w[d.id]){var f=w[d.id];delete w[d.id];if(d.ok)f.ok(d.data);else f.ko(new Error(d.error||('HTTP '+d.status)));}" +
    "else if(d.type==='stellio.init'){S.theme=d.theme||{};S.lang=d.lang||'fr';S.ready=true;th(S.theme);document.dispatchEvent(new Event('stellio-ready'));}});})();";
const PV = { id: '', plugin: null, loaded: 0 };
const PV_VARS = { bg: '--bg-primary', panel: '--bg-secondary', card: '--bg-card', hover: '--bg-hover', text: '--text-primary', muted: '--text-secondary', border: '--border', accent: '--accent', success: '--success', warning: '--warning', danger: '--danger' };
function pvTheme() {
    const cs = getComputedStyle(document.documentElement), t = {};
    Object.keys(PV_VARS).forEach(k => { t[k] = (cs.getPropertyValue(PV_VARS[k]) || '').trim(); });
    return t;
}
function pvPost(msg) { const f = $('pv-frame'); try { f.contentWindow.postMessage(msg, '*'); } catch (e) { /* cadre fermé */ } }
async function pvApi(m) {
    const path = String(m.path || ''), pl = PV.plugin;
    const reply = (o) => pvPost(Object.assign({ type: 'stellio.reply', id: m.id }, o));
    if (!pl || !(pl.permissions || []).includes('api:read')) return reply({ ok: false, error: 'Permission « api:read » absente du plugin.' });
    // 1.2.0 : écriture (POST JSON) réservée aux plugins SIGNÉS à code intégré, et uniquement vers leur propre espace /api/x/<id>/ (permission « api:write »)
    const post = m.method === 'POST';
    if (post && !(pl.host && (pl.permissions || []).includes('api:write') && path.startsWith(['', 'api', 'x', pl.id, ''].join('/')) && !path.includes('..') && /^\/api\/x\/[a-z0-9_-]+\/[A-Za-z0-9_\-./]*$/.test(path))) return reply({ ok: false, error: 'Écriture non autorisée pour ce plugin.' });
    if (!/^\/api\/[A-Za-z0-9_\-./?=&%:,+~@]*$/.test(path) || path.includes('..') || path.includes('//') || PV_DENY.some(d => path === d || path.startsWith(d + '/') || path.startsWith(d + '?'))) return reply({ ok: false, error: 'Chemin non autorisé.' });
    try {
        const r = post ? await fetch(API + path, { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(m.body == null ? {} : m.body) })
            : await fetch(API + path, { credentials: 'same-origin' });
        const as = m.as === 'text' ? 'text' : (m.as === 'arraybuffer' ? 'arraybuffer' : 'json');
        let data = null;
        if (r.ok) data = await (as === 'text' ? r.text() : as === 'arraybuffer' ? r.arrayBuffer() : r.json());
        else { const j = await r.json().catch(() => ({})); return reply({ ok: false, status: r.status, error: j.error || ('HTTP ' + r.status) }); }
        reply({ ok: true, status: r.status, data });
    } catch (e) { reply({ ok: false, error: String(e && e.message || e) }); }
}
window.addEventListener('message', (e) => {
    const f = $('pv-frame'); if (!f || e.source !== f.contentWindow) return;
    const m = e.data || {}; if (m.type === 'stellio.api') pvApi(m);
});
async function openPluginView(id) {
    const p = (PV.list || []).find(x => x.id === id); if (!p) return;
    PV.id = id; PV.plugin = p;
    const msg = $('pv-msg'), fr = $('pv-frame'); if (!fr) return;
    msg.hidden = true; fr.hidden = false; fr.srcdoc = '';
    try {
        const r = await fetch(`${API}/api/plugins/${encodeURIComponent(id)}/ui`, { credentials: 'same-origin' });
        if (!r.ok) { const j = await r.json().catch(() => ({})); throw new Error(j.error || ('HTTP ' + r.status)); }
        const html = await r.text();
        const my = ++PV.loaded;
        fr.onload = () => { if (my === PV.loaded) pvPost({ type: 'stellio.init', theme: pvTheme(), lang: (window.I18N && I18N.lang) || 'fr' }); };
        fr.srcdoc = `<!doctype html><meta http-equiv="Content-Security-Policy" content="${PV_CSP}"><script>${PV_CLIENT}<\/script>` + html;
    } catch (e) { fr.hidden = true; msg.hidden = false; msg.textContent = `${tr('pv_error', 'Impossible d\'afficher ce plugin')} : ${e.message || e}`; }
}
async function refreshPluginNav() {
    try { if (typeof IS_VIEWER !== 'undefined' && IS_VIEWER && !window.STELLIO_DEMO) return; } catch (e) { return; }
    const box = $('plugin-nav-list'); if (!box) return;
    let d; try { const r = await fetch(`${API}/api/plugins`, { credentials: 'same-origin' }); if (!r.ok) return; d = await r.json(); } catch (e) { return; }
    const items = (d.plugins || []).filter(p => p.ui);
    PV.list = items;
    box.innerHTML = items.length ? `<div class="plugin-nav-sub" data-cat="plugins">${esc(tr('installed_ui', 'Installés'))}</div>` + items.map(p => `<button type="button" class="nav-btn${p.enabled ? '' : ' plugin-off'}" data-cat="plugins" data-plugin-ui="${esc(p.id)}" data-icon="${esc(p.ui.icon)}" title="${esc(p.enabled ? p.name : tr('pv_off', 'Désactivé : activez-le dans le catalogue'))}"><i class="fa-solid ${esc(p.ui.icon)}"></i><span>${esc(p.ui.title)}</span></button>`).join('') : '';
    box.querySelectorAll('[data-plugin-ui]').forEach(b => b.addEventListener('click', () => {
        if (b.classList.contains('plugin-off')) { document.getElementById('plugins-btn')?.click(); return; }      // désactivé : on va l'activer dans le catalogue
        document.querySelectorAll('.nav-btn').forEach(x => x.classList.remove('active')); b.classList.add('active');
        document.querySelectorAll('.page').forEach(x => x.classList.remove('active')); $('page-plugin-view')?.classList.add('active');
        const h = $('header-page-title'); if (h) h.innerHTML = `<i class="fa-solid ${esc(b.dataset.icon)}"></i> ${esc(b.querySelector('span').textContent)}`;
        if (typeof updateHeaderVisibilityForPage === 'function') updateHeaderVisibilityForPage('plugin-view');
        if (typeof closeMobileSidebar === 'function') closeMobileSidebar();
        openPluginView(b.dataset.pluginUi);
    }));
}
document.getElementById('sidebar-rail')?.addEventListener('click', (e) => { if (e.target.closest('[data-rail="plugins"]')) refreshPluginNav(); });
// Plugins intégrés : tout élément portant data-host-plugin="<id>" disparaît tant que ce plugin n'est pas activé (une feuille de style, donc aussi pour les éléments créés plus tard)
async function applyHostFeatures() {
    try {
        const r = await fetch(`${API}/api/plugins/features`, { credentials: 'same-origin' }); if (!r.ok) return;
        const d = await r.json(); window.STELLIO_FEATURES = d.features || {};
        const off = Object.keys(d.features || {}).filter(k => !d.features[k]);
        let st = document.getElementById('hp-style'); if (!st) { st = document.createElement('style'); st.id = 'hp-style'; document.head.appendChild(st); }
        st.textContent = off.map(k => `[data-host-plugin="${k}"]{display:none !important}`).join('\n');
        document.documentElement.dataset.hpOff = off.join(' ');
        // Menu Administration : visible seulement sur une instance reliée à d'autres (appairée, ou sollicitée pour être supervisée), jamais sur une instance supervisée
        let net = false;
        if (d.features && d.features.administration) {
            try {
                const o = await fetch(`${API}/api/admin/overview`, { credentials: 'same-origin', cache: 'no-store' });
                if (o.ok) { const ov = await o.json(); net = ov.role !== 'supervised' && !!((ov.instances || []).length || ov.request); }
            } catch (e) { /* injoignable : on garde l'état précédent */ net = document.documentElement.dataset.netOk === '1'; }
        }
        if (net) document.documentElement.dataset.netOk = '1'; else delete document.documentElement.dataset.netOk;
        try { document.dispatchEvent(new Event('stellio-features')); } catch (e) { /* facultatif */ }
    } catch (e) { /* facultatif : sans réponse, tout reste visible */ }
    finally { document.documentElement.dataset.hpReady = '1'; }
}
applyHostFeatures();
// la liaison entre instances peut changer (appairage, acceptation) : on relit au retour sur la page et chaque minute
window.addEventListener('focus', () => applyHostFeatures());
setInterval(() => { if (!document.hidden) applyHostFeatures(); }, 60000);
[1500, 5000].forEach(ms => setTimeout(refreshPluginNav, ms));
function registerTab(k, def) { if (k && def && typeof def.render === 'function') { TABS[k] = def; window.StellioSuite.tabs = Object.keys(TABS); } }
window.StellioSuite = { registerTab, _tabs: TABS, _applyHostFeatures: applyHostFeatures, _refreshPluginNav: refreshPluginNav, _openPluginView: openPluginView, _pvTheme: pvTheme, _pct: pct, open, onShow, onShowPlugins, _soon: SOON, tabs: Object.keys(TABS), _h: H, _pager: pagerHtml, _cloudView: cloudView, _plateEditor: plateEditor };
})();
