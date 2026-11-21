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
