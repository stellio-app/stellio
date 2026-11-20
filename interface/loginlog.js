/* Stellio — 1.1.6 : journal des connexions (Paramètres › Sécurité du compte). Réservé au propriétaire. */
(function () {
'use strict';
const tr = (k, fb) => { const s = (typeof I18N !== 'undefined' && I18N.t) ? I18N.t('authlog.' + k) : ''; return (s && s !== 'authlog.' + k) ? s : fb; };
const esc = (v) => (typeof escapeHtml === 'function' ? escapeHtml(String(v)) : String(v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
function fmt(ts) { try { return new Date(ts * 1000).toLocaleString(); } catch (e) { return ''; } }
function evLabel(e) { return e === 'login_ok' ? tr('ev_ok', 'Connexion') : e === 'login_fail' ? tr('ev_fail', 'Échec') : tr('ev_out', 'Déconnexion'); }

async function load(box) {
    box.innerHTML = '<p class="settings-hint">…</p>';
    try {
        const r = await fetch(`${API}/api/auth/log?limit=50`, { cache: 'no-store' });
        const d = await r.json();
        if (!r.ok) throw new Error(d.error || r.status);
        const s = d.summary || {};
        const head = `<p class="settings-hint">${esc(tr('summary', '24 h : {ok} connexion(s), {fail} échec(s), {ips} adresse(s)')
            .replace('{ok}', s.ok || 0).replace('{fail}', s.fail || 0).replace('{ips}', s.ips || 0))}</p>`;
        if (!(d.rows || []).length) { box.innerHTML = head + `<p class="settings-hint">${esc(tr('empty', 'Aucune connexion enregistrée pour le moment.'))}</p>`; return; }
        box.innerHTML = head + `<div class="authlog-scroll"><table class="authlog-table"><tbody>${d.rows.map(x =>
            `<tr class="${x.event === 'login_fail' ? 'authlog-fail' : ''}"><td>${esc(fmt(x.ts))}</td><td>${esc(evLabel(x.event))}</td><td>${esc(x.username || '—')}</td><td>${esc(x.ip || '—')}</td></tr>`).join('')}</tbody></table></div>`;
    } catch (e) {
        box.innerHTML = `<p class="settings-hint">${esc(tr('unavailable', 'Journal indisponible.'))}</p>`;
    }
}

function mount() {
    try { if (typeof IS_VIEWER !== 'undefined' && IS_VIEWER) return; } catch (e) { return; }
    const body = document.querySelector('#account-security-section .accord-body');
    if (!body || document.getElementById('authlog-details')) return;
    const det = document.createElement('details');
    det.id = 'authlog-details';
    det.className = 'authlog-details';
    det.innerHTML = `<summary><i class="fa-solid fa-clock-rotate-left"></i> <span data-i18n="authlog.title">${esc(tr('title', 'Journal des connexions'))}</span></summary><div id="authlog-box" class="authlog-box"></div>`;
    body.appendChild(det);
    det.addEventListener('toggle', () => { if (det.open) load(document.getElementById('authlog-box')); });
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
})();
