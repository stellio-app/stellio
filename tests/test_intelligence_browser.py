"""1.1.7 — carte « Stellio Intelligence » de la page Statistiques exécutée dans un vrai Chromium (réponses du serveur simulées)."""
import os
import pytest
sync_api = pytest.importorskip('playwright.sync_api')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = open(os.path.join(ROOT, 'interface', 'v113.js'), encoding='utf-8').read()

RECO = {'ok': True, 'readiness': {'rated': 9, 'needed': 8, 'ready': True}, 'scope': {'kind': 'material', 'widened': True}, 'sample': 9,
        'best': {'profile': 'Standard 215', 'profile_fp': 'abc', 'success': 6, 'failed': 0, 'partial': 0, 'total': 6, 'rate': 1.0, 'confidence': 'high', 'settings': {'nozzle_temp': 215, 'bed_temp': 60}},
        'alternatives': [{'profile': 'Rapide', 'profile_fp': '', 'success': 3, 'total': 4, 'rate': 0.75}], 'avoid': [{'profile': 'Froid 195 <b>x</b>', 'profile_fp': '', 'success': 1, 'total': 4, 'rate': 0.25}],
        'params': [{'param': 'nozzle_temp', 'unit': '°C', 'typical': 215, 'min': 195, 'max': 215, 'n_ok': 7}], 'reason': None}
DIAG = {'ok': True, 'failed': 4, 'reason': None, 'causes': [{'cause': 'adhesion', 'score': 1.1, 'share': 0.7, 'confidence': 'high', 'evidence': [
    {'type': 'declared', 'count': 3, 'total': 4}, {'type': 'param', 'param': 'nozzle_temp', 'unit': '°C', 'failed': 195, 'ok': 215, 'direction': 'lower'}]}],
        'contexts': [{'dimension': 'profile', 'key': 'Froid 195', 'fail_rate': 0.75, 'base_rate': 0.3, 'failed': 3, 'total': 4}]}

STUBS = """
window.__calls = []; window.__routes = {};
window.fetch = async (url, opt) => { window.__calls.push(url); const k = url.split('?')[0]; const h = window.__routes[k]; const res = typeof h === 'function' ? h(url) : (h === undefined ? {} : h);
  return { ok: true, status: 200, json: async () => res, text: async () => JSON.stringify(res) }; };
window.showToast = () => {};
"""


@pytest.fixture(scope='module')
def page():
    try:
        pw = sync_api.sync_playwright().start(); br = pw.chromium.launch()
    except Exception as e:
        pytest.skip(f'Chromium indisponible : {e}')
    pg = br.new_page(viewport={'width': 900, 'height': 900})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg._errs = errs
    pg.set_content('<html lang="fr"><body><div id="page-stats"></div></body></html>')
    pg.add_script_tag(content=STUBS); pg.add_script_tag(content=JS)
    yield pg
    br.close(); pw.stop()


def test_carte_intelligence_affiche_reco_causes_et_filtre(page):
    page.evaluate("""([reco, diag]) => { window.__routes['/api/failure-stats'] = { total: 0 };
        window.__routes['/api/intelligence/overview'] = { readiness: { rated: 9, needed: 8, ready: true }, materials: ['PLA', 'PETG'], printers: [{ id: 1, name: 'Voron' }] };
        window.__routes['/api/intelligence/recommend'] = reco; window.__routes['/api/intelligence/diagnose'] = diag; }""", [RECO, DIAG])
    page.evaluate("window.StellioV113.onStats()")
    page.wait_for_selector('#v13-intel .v13-box')
    txt = page.inner_text('#v13-intel')
    assert 'Standard 215' in txt and '6/6' in txt and 'confiance élevée' in txt and 'Température buse' in txt and '195' in txt
    assert 'Décollement' not in txt and 'Mauvaise adhérence plateau' in txt and 'Motif noté sur 3 échec(s) sur 4' in txt and 'plus basse sur les échecs (195 °C contre 215 °C' in txt
    assert 'Profil Froid 195 : 75 % d\'échec contre 30 %' in txt and 'preuves' in txt
    assert 'cette matière' in txt                                                  # périmètre élargi annoncé
    assert page.locator('#v13-intel b', has_text='x').count() == 0                  # le nom d'un profil n'est jamais interprété comme du HTML
    assert '<b>x</b>' in page.inner_text('#v13-intel')
    page.select_option('#v13-i-mat', 'PETG')
    page.wait_for_function("window.__calls.some(u => u.includes('/api/intelligence/recommend') && u.includes('material=PETG'))")
    page.wait_for_selector('#v13-i-mat')
    assert page.eval_on_selector('#v13-i-mat', 'e => e.value') == 'PETG'


def test_carte_intelligence_pas_assez_de_donnees(page):
    page.evaluate("""() => { window.__routes['/api/intelligence/overview'] = { readiness: { rated: 2, needed: 8, ready: false }, materials: [], printers: [] };
        window.__routes['/api/intelligence/recommend'] = { ok: true, best: null, reason: 'not_enough_data', params: [], scope: { kind: 'all' }, sample: 2 };
        window.__routes['/api/intelligence/diagnose'] = { ok: true, reason: 'not_enough_data', failed: 1, causes: [], contexts: [] }; }""")
    page.evaluate("window.StellioV113.onStats()")
    page.wait_for_function("document.querySelector('#v13-intel') && document.querySelector('#v13-intel').innerText.includes('2 impression')")
    txt = page.inner_text('#v13-intel')
    assert 'sur 8 nécessaires' in txt and 'Pas assez de données pour recommander' in txt and 'Pas assez d\'échecs notés' in txt and 'Profil recommandé' not in txt
    assert not page._errs
