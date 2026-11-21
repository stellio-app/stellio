"""1.1.9 — mode atelier : un appui sur une imprimante en cours d'impression ouvre sa carte, devant le mode atelier (vrai Chromium, fonctions réelles de script.js)."""
import os
import pytest
sync_api = pytest.importorskip('playwright.sync_api')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = open(os.path.join(ROOT, 'interface', 'script.js'), encoding='utf-8').read()
CSS = open(os.path.join(ROOT, 'interface', 'style.css'), encoding='utf-8').read()
WS = SRC[SRC.index('let _workshopTimer = null'):SRC.index('// Lien direct : http')]

SETUP = """
window.API = ''; window.__opened = []; window.__closed = 0;
window.escapeHtml = (s) => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
window._t3 = (k, f, p) => f; window.I18N = { t: (k) => k, lang: 'fr' };
window.formatDuration = (s) => Math.round(s / 60) + 'm'; window._findLibraryFileForPrintJob = () => null;
window.printersList = [{ id: 1, name: 'sidewinder', type: 'klipper' }, { id: 2, name: 'ender', type: 'klipper' }];
window.openPrinterMonitor = (pid) => { window.__opened.push(pid); const m = document.createElement('div'); m.id = 'modal-printer-monitor'; m.className = 'modal'; m.textContent = 'carte'; document.body.appendChild(m); };
window.closePrinterMonitor = () => { window.__closed++; document.getElementById('modal-printer-monitor')?.remove(); };
window.openStatusLinksModal = () => {};
window.fetch = async (url) => ({ ok: true, json: async () => (String(url).includes('/1/status') ? { status: 'printing', progress: 12, file: 'a_very_long_name.gcode', time: { remaining: 3600 }, temps: { extruder: { current: 200 }, bed: { current: 60 } } } : { status: 'idle' }) });
"""


@pytest.fixture(scope='module')
def page():
    try:
        pw = sync_api.sync_playwright().start(); br = pw.chromium.launch()
    except Exception as e:
        pytest.skip(f'Chromium indisponible : {e}')
    pg = br.new_page(viewport={'width': 390, 'height': 800})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg._errs = errs
    pg.set_content('<html lang="fr"><body></body></html>')
    pg.add_style_tag(content=CSS)
    pg.add_script_tag(content=SETUP + WS + '\nwindow.__open = window.openWorkshopMode;')
    yield pg
    br.close(); pw.stop()


def test_appui_sur_une_imprimante_en_cours_ouvre_sa_carte_devant_le_mode_atelier(page):
    page.evaluate('window.__open()')
    page.wait_for_selector('.ws-tile.ws-printing')
    assert page.locator('.ws-tile.ws-clickable').count() == 1                          # seule l'imprimante en cours est cliquable
    assert page.locator('.ws-tile.ws-idle.ws-clickable').count() == 0
    page.click('.ws-tile.ws-printing')
    page.wait_for_selector('#modal-printer-monitor')
    assert page.evaluate('window.__opened') == [1]
    z = lambda sel: int(page.evaluate(f"getComputedStyle(document.querySelector('{sel}')).zIndex"))
    assert z('#modal-printer-monitor') > z('#workshop-overlay')                        # la carte passe devant le mode atelier
    page.wait_for_timeout(5600)                                                         # la grille est redessinée : le clic marche encore
    page.evaluate("document.getElementById('modal-printer-monitor').remove()")
    page.click('.ws-tile.ws-printing')
    assert page.evaluate('window.__opened') == [1, 1]
    page.click('.ws-tile.ws-idle', force=True)
    assert page.evaluate('window.__opened') == [1, 1]                                  # une imprimante au repos n'ouvre rien
    page.evaluate("document.getElementById('modal-printer-monitor').remove()")


def test_echap_ferme_la_carte_puis_le_mode_atelier_et_tout_tient_dans_l_ecran(page):
    page.click('.ws-tile.ws-printing')
    page.wait_for_selector('#modal-printer-monitor')
    page.keyboard.press('Escape')
    assert page.evaluate('window.__closed') == 1 and page.locator('#workshop-overlay').count() == 1
    r = page.evaluate("() => { const t = document.querySelector('.ws-tile').getBoundingClientRect(); return [t.left, t.right, innerWidth]; }")
    assert r[0] >= 0 and r[1] <= r[2]
    page.keyboard.press('Escape')
    assert page.locator('#workshop-overlay').count() == 0 and not page._errs


def test_carte_imprimante_sur_telephone_progression_puis_temperatures_en_une_colonne(page):
    page.set_content('<html><body></body></html>'); page.add_style_tag(content=CSS)
    page.evaluate("""() => { document.body.innerHTML = '<div class="monitor-modal-content"><div class="monitor-grid"><div class="monitor-card monitor-card-temps">T</div><div class="monitor-card monitor-card-progress">P</div><div class="monitor-card full">D</div></div></div>'; }""")
    r = page.evaluate("""() => { const q = (s) => document.querySelector(s).getBoundingClientRect(); const t = q('.monitor-card-temps'), p = q('.monitor-card-progress'), d = q('.monitor-card.full'); return [p.top, t.top, d.top, p.left, t.left, innerWidth, t.right]; }""")
    assert r[0] < r[1] < r[2]                      # progression, puis températures, puis dernière impression
    assert r[3] == r[4] and r[6] <= r[5]           # même colonne, dans l'écran
    page.set_viewport_size({'width': 1000, 'height': 700})
    r2 = page.evaluate("""() => { const q = (s) => document.querySelector(s).getBoundingClientRect(); return [q('.monitor-card-temps').left, q('.monitor-card-progress').left]; }""")
    assert r2[0] < r2[1]                           # sur grand écran : températures à gauche, progression à droite, comme avant
    page.set_viewport_size({'width': 390, 'height': 800})


SCRIPT = SRC
_MON = SRC[SRC.index('function initMonitorUI(printer) {'):]
_MON = _MON[:_MON.index('\nfunction ', 10)]


def test_carte_imprimante_tient_dans_l_ecran_sans_defiler_sur_pc(page):
    setup = ("window.I18N={t:(k)=>({'printers.camera':'Caméra','printers.temperatures':'Températures','printers.progression':'Progression','printers.elapsed':'Écoulé',"
             "'printers.remaining':'Restant','printers.total_estimated':'Total estimé','printers.last_print':'Dernière impression','common.loading':'Chargement'}[k]||k)};"
             "window._t3=(k,f)=>f;window.loadPrinterCamera=()=>{};")
    for (w, h) in ((1920, 1024), (1366, 768), (1280, 720)):
        page.set_viewport_size({'width': w, 'height': h})
        page.set_content('<html><body><div class="modal"><div class="modal-content monitor-modal-content"><div class="modal-header"><h3>sidewinder</h3></div><div class="modal-body" id="monitor-body"></div></div></div></body></html>')
        page.add_style_tag(content=CSS)
        page.add_script_tag(content=setup + _MON + "\ninitMonitorUI({type:'klipper',ip:'1.2.3.4'});")
        page.evaluate("""() => { document.getElementById('printer-camera-container').style.display = 'block';
            document.getElementById('monitor-temps-container').innerHTML = '<div class=stat-row><span class=stat-label>Extrudeur</span><span class=stat-value>200.2°C / 200°C</span></div>'; }""")
        r = page.evaluate("() => { const m = document.querySelector('.modal-content'); return [m.scrollHeight, m.clientHeight, m.getBoundingClientRect().height, innerHeight, document.documentElement.scrollWidth, innerWidth]; }")
        assert r[0] <= r[1] + 1, (w, h, r)                 # rien à faire défiler dans la fenêtre
        assert r[2] <= r[3] and r[4] <= r[5]               # ni plus haute ni plus large que l'écran
        cam = page.evaluate("document.getElementById('printer-camera-container').getBoundingClientRect().left")
        pro = page.evaluate("document.querySelector('.monitor-card-progress').getBoundingClientRect().left")
        assert cam < pro                                   # caméra à gauche, infos à droite
    page.set_viewport_size({'width': 390, 'height': 800})


def test_adresse_spoolman_garde_son_chemin_et_le_port_n_est_ajoute_qu_au_besoin(page):
    """1.2.0 : « http://hôte:port/spoolman » (FilaMan + plugin Spoolman API) ne perd plus « /spoolman » à l'enregistrement."""
    fn = SRC[SRC.index('function normalizeSpoolmanUrl(raw) {'):SRC.index('async function saveSpoolmanUrl()')]
    r = page.evaluate("(src) => { const f = new Function(src + '; return normalizeSpoolmanUrl;')(); return ['http://filaman.lan:8080/spoolman', 'http://filaman.lan:8080/spoolman/', 'https://filaman.example.com/spoolman', '192.168.1.5', '192.168.1.5:7912', 'http://192.168.1.5', 'http://h:1/a/b//', '  ', null].map(f); }", fn)
    assert r == ['http://filaman.lan:8080/spoolman', 'http://filaman.lan:8080/spoolman', 'https://filaman.example.com/spoolman',
                 'http://192.168.1.5:7912', 'http://192.168.1.5:7912', 'http://192.168.1.5', 'http://h:1/a/b', '', '']


def test_pesee_filament_sans_mention_manuelle_quand_l_inventaire_manuel_est_desactive(page):
    """1.2.0 : section « Pesée et prévision » (vrai management.js dans Chromium) — inventaire manuel désactivé : pas de carte « Peser une bobine manuelle »,
    pas de bobine manuelle dans les alertes, sous-titre limité à TigerTag ; réactivé : tout revient."""
    mg = open(os.path.join(ROOT, 'interface', 'management.js'), encoding='utf-8').read()
    pg = page.context.browser.new_page()
    try:
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.set_content('<html lang="fr"><body><h3 data-mg-slot-title="fil"></h3><p data-mg-slot-sub="fil"></p><div data-mg-slot="fil"></div><div id="mg-body"></div></body></html>')
        pg.add_script_tag(content="""delete window.IntersectionObserver; window.manualInventoryEnabled = false;
          window.fetch = async (u) => { const U = String(u); const body = U.includes('/forecast') ? { spools: [
              { source_type: 'manual', source_id: '1', name: 'Manuelle', remaining_g: 50, capacity_g: 1000, g_per_day: 10, days_left: 5, empty_on: '2026-12-01' },
              { source_type: 'tigertag', source_id: 't', name: 'TT bobine', remaining_g: 60, capacity_g: 1000, g_per_day: 10, days_left: 6, empty_on: '2026-12-02' }] }
            : U.includes('/manual') ? [{ id: 1, name: 'Manuelle', material: 'PLA' }] : [{ source_id: 't', name: 'TT bobine', material: 'PETG' }];
            return { ok: true, json: async () => body }; };""")
        pg.add_script_tag(content=mg)
        pg.evaluate("window.StellioManagement.initSlots()"); pg.wait_for_selector('[data-mg-slot="fil"] .spool-card')
        txt = pg.inner_text('[data-mg-slot="fil"]')
        assert 'TT bobine' in txt and 'Manuelle' not in txt and pg.locator('.mg-weigh-card').count() == 0 and '#fw-id' not in txt
        assert 'manuelles' not in pg.inner_text('[data-mg-slot-sub]') and 'TigerTag' in pg.inner_text('[data-mg-slot-sub]')
        pg.evaluate("window.manualInventoryEnabled = true; document.querySelector('[data-mg-slot=\"fil\"]').innerHTML = ''; window.StellioManagement.filRefresh()")
        pg.wait_for_selector('.mg-weigh-card')
        assert 'Manuelle' in pg.inner_text('[data-mg-slot="fil"]') and pg.locator('#fw-id').count() == 1
        assert 'manuelles' in pg.inner_text('[data-mg-slot-sub]')
        assert not errs, errs
    finally:
        pg.close()


def _fresh(page):
    pg = page.context.browser.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg._errs = errs
    pg.set_content('<html lang="fr"><body></body></html>')
    return pg


def test_likes_sections_repliees_au_retour_sur_la_page(page):
    """1.2.0 : « Mes likes » / « Mes créations » — l'état ouvert d'une section ne survit pas à une sortie de la page (et l'autre page n'est pas touchée)."""
    a = SRC.index("const _acctKey = 'stellio_acct_open';"); b = SRC.index('function _acctResetOpen(kind) {'); e = SRC.index('\n', b)
    fn = SRC[a:e]          # clé, lecture, écriture et remise à zéro (fonctions réelles de script.js)
    pg = _fresh(page)
    try:
        r = pg.evaluate("""(src) => { const mem = {}; Object.defineProperty(window, 'localStorage', { configurable: true, value: { getItem: (k) => (k in mem ? mem[k] : null), setItem: (k, v) => { mem[k] = String(v); } } });
            const f = new Function(src + '; return {reset: _acctResetOpen, get: _acctCollapsedState, save: _acctSaveCollapsed};')();
            f.save({'likes:makerworld': true, 'likes:printables': true, 'creations:makerworld': true});
            const before = Object.keys(f.get()).sort();
            f.reset('likes'); const after = Object.keys(f.get()).sort();
            f.reset('likes'); return [before, after, Object.keys(f.get()).sort()]; }""", fn)
        assert r[0] == ['creations:makerworld', 'likes:makerworld', 'likes:printables'] and r[1] == ['creations:makerworld'] and r[2] == ['creations:makerworld']
        assert "_acctResetOpen('likes')" in SRC and "_acctResetOpen('creations')" in SRC          # branché à l'entrée sur chaque page
        assert not pg._errs, pg._errs
    finally:
        pg.close()


def test_fichiers_recents_sans_mtime_se_classent_par_date_d_ajout(page):
    """1.2.0 : fichiers SMB / anciens caches sans « mtime » → classés par date d'ajout au lieu de l'ordre alphabétique ; un fichier plus récent passe en tête."""
    fn = SRC[SRC.index('const _recentFirstSeen'):SRC.index('function _recentSignature')]
    pg = _fresh(page)
    try:
        r = pg.evaluate("""(src) => { const f = new Function(src + '; return _recentFilesTop;')();
            const files = [{path:'a', name:'Bolt', date_added:'2026-11-01 10:00:00'}, {path:'b', name:'Box', date_added:'2026-11-20 10:00:00'},
                           {path:'c', name:'Key', date_added:'2026-11-21 09:00:00'}, {path:'d', name:'Lid', mtime: 1700000000}, {path:'e', name:'Zed'}];
            return f(files).map(x => x.name); }""", fn)
        assert r[:3] == ['Key', 'Box', 'Bolt'] or r[:3] == ['Key', 'Box', 'Lid'], r
        assert r[0] == 'Key' and r.index('Box') < r.index('Bolt')
    finally:
        pg.close()


def test_telechargements_recents_se_rafraichissent_seuls(page):
    """1.2.0 : le widget « Téléchargements récents » se met à jour quand l'historique change, sans redessiner s'il n'a pas bougé."""
    fn = SRC[SRC.index('let _dlWidgetSig = null;'):SRC.index('let _dashboardUpdateChecked')]
    pg = _fresh(page)
    try:
        pg.set_content('<html lang="fr"><body><div id="dashboard-downloads-body"></div></body></html>')
        r = pg.evaluate("""async (src) => {
            window.API = ''; window.I18N = { lang: 'fr', t: (k) => k }; window._t2 = (k, f) => f; window.escapeHtml = (s) => String(s);
            let data = [{ id: 1, file_name: 'Ancien', platform: 'MakerWorld', downloaded_at: '2026-11-20 10:00:00' }];
            window.fetch = async () => ({ ok: true, json: async () => data });
            const f = new Function(src + '; return _loadDashboardDownloads;')();
            const body = document.getElementById('dashboard-downloads-body');
            await f(); const t1 = body.textContent; const node = body.firstElementChild;
            await f(); const same = body.firstElementChild === node;             // inchangé : pas de redessin
            data = [{ id: 2, file_name: 'Nouveau', platform: 'Printables', downloaded_at: '2026-11-21 14:00:00' }].concat(data);
            await f(); return [t1.includes('Ancien'), same, body.textContent.includes('Nouveau'), body.querySelectorAll('.dashboard-row').length]; }""", fn)
        assert r == [True, True, True, 2], r
        assert 'setInterval' in SRC[SRC.index('/* 1.2.0 : « Téléchargements récents »'):][:400]
        assert not pg._errs, pg._errs
    finally:
        pg.close()


def test_toute_entree_de_bibliotheque_porte_sa_date_de_modification():
    """1.2.0 : fichiers SMB, extraits d'archives et sources « fichier unique » avaient une entrée sans « mtime » → « Fichiers récents » restait par ordre alphabétique."""
    import re
    main = open(os.path.join(ROOT, 'main.py'), encoding='utf-8').read()
    blocks = [m.start() for m in re.finditer(r"'date_added':", main)]
    assert len(blocks) >= 5
    for i in blocks:
        start = main.rfind('.append({', 0, i); end = main.index('})', i)
        assert "'mtime'" in main[start:end], main[start:start + 80]
