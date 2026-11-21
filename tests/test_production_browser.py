"""1.1.8 — production assistée et consommation de résine exécutées dans un vrai Chromium (réponses du serveur simulées)."""
import os
import pytest
sync_api = pytest.importorskip('playwright.sync_api')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = open(os.path.join(ROOT, 'interface', 'v113.js'), encoding='utf-8').read()

STUBS = """
window.__calls = []; window.__bodies = []; window.__routes = {};
window.fetch = async (url, opt) => { window.__calls.push((opt && opt.method || 'GET') + ' ' + url); if (opt && opt.body) window.__bodies.push(JSON.parse(opt.body));
  const k = url.split('?')[0]; const h = window.__routes[k]; const res = typeof h === 'function' ? h(url, opt) : (h === undefined ? {} : h);
  return { ok: true, status: 200, json: async () => res, text: async () => JSON.stringify(res) }; };
window.showToast = () => {};
"""

PROP = {'candidates': [{'printer_id': 2, 'printer_name': 'Voron <i>x</i>', 'resin': False, 'profile': 'Standard 215', 'profile_fp': '', 'confidence': 'high', 'sample': 9,
                        'feedback': {'followed': 3, 'success': 3, 'effect': 'promoted'}}, {'printer_id': 3, 'printer_name': 'Prusa', 'resin': False, 'profile': '', 'profile_fp': ''}],
        'chosen': {'printer_id': 2}, 'blocked': False,
        'checks': [{'id': 'file', 'level': 'ok', 'code': 'file_ready'}, {'id': 'printer', 'level': 'warn', 'code': 'printer_busy'}, {'id': 'filament', 'level': 'ok', 'code': 'filament_ok'}]}


def run(status, **kw):
    r = {'id': 5, 'file_name': 'piece.gcode', 'status': status, 'printer_id': 2, 'printer_name': 'Voron', 'profile': 'Standard 215', 'proposal': PROP}
    r.update(kw)
    return r


@pytest.fixture(scope='module')
def page():
    try:
        pw = sync_api.sync_playwright().start(); br = pw.chromium.launch()
    except Exception as e:
        pytest.skip(f'Chromium indisponible : {e}')
    pg = br.new_page(viewport={'width': 900, 'height': 900})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg._errs = errs
    pg.set_content('<html lang="fr"><body><div id="page-stats"></div><div id="v13-resin-host"></div></body></html>')
    pg.add_script_tag(content=STUBS); pg.add_script_tag(content=JS)
    yield pg
    br.close(); pw.stop()


def test_production_proposer_valider_envoyer_resultat(page):
    page.evaluate("""(r) => { window.__routes['/api/production/propose'] = r.p;
        window.__routes['/api/production/5/validate'] = r.v; window.__routes['/api/production/5/send'] = r.s; window.__routes['/api/production/5/result'] = r.f; }""",
                  {'p': run('proposed'), 'v': run('validated'), 's': run('sent'), 'f': run('finished')})
    page.evaluate("window.StellioV113.openProduction('/lib/piece.gcode', 'PLA')")
    page.wait_for_selector('.v13-modal [data-a="validate"]')
    txt = page.inner_text('.v13-modal')
    assert 'Standard 215' in txt and 'confiance élevée' in txt and 'Favorisé : suivi 3 fois, 3 réussites' in txt and 'Imprimante occupée' in txt and 'rien n\'est envoyé sans votre clic' in txt
    assert page.locator('.v13-modal i', has_text='x').count() == 0                            # le nom d'une imprimante n'est jamais interprété comme du HTML
    assert page.locator('[data-a="send"]').count() == 0                                        # pas d'envoi avant validation
    page.click('[data-a="validate"]')
    page.wait_for_selector('[data-a="send"]')
    assert page.locator('[data-a="validate"]').count() == 0
    assert not any('/send' in c for c in page.evaluate('window.__calls'))
    page.click('[data-a="send"]')
    page.wait_for_selector('[data-a="result"]')
    assert 'Lancez l\'impression sur l\'imprimante' in page.inner_text('.v13-modal')
    page.click('[data-r="success"]')
    page.wait_for_function("document.querySelector('.v13-modal') && document.querySelector('.v13-modal').innerText.includes('Terminée')")
    assert {'result': 'success'} in page.evaluate('window.__bodies')
    assert not page._errs


def test_production_controle_bloquant_pas_de_validation(page):
    blocked = dict(PROP, blocked=True, checks=[{'id': 'file', 'level': 'block', 'code': 'needs_slicing'}])
    page.evaluate("(r) => { window.__routes['/api/production/propose'] = r; }", run('proposed', proposal=blocked))
    page.evaluate("window.StellioV113.openProduction('/lib/m.stl')")
    page.wait_for_selector('.v13-modal .v13-box')
    assert 'Modèle brut' in page.inner_text('.v13-modal') and page.locator('[data-a="validate"]').count() == 0
    page.click('.v13-x')


def test_resine_consommation_flacon_actif_et_annulation(page):
    page.evaluate("""() => { window.__calls.length = 0; window.__bodies.length = 0;
        window.__routes['/api/resin'] = { bottles: [{ id: 1, name: 'Grise', brand: 'X', kind: 'standard', volume_ml: 1000, remaining_ml: 460 }], total_remaining_ml: 460 };
        window.__routes['/api/resin/restock'] = { items: [], threshold_ml: 200 };
        window.__routes['/api/resin/printers'] = { printers: [{ id: 3, name: 'Photon <b>z</b>', bottle_id: null }] };
        window.__routes['/api/resin/usage'] = { usage: [{ id: 9, file: 'p.sl1', ml: 40, source: 'sl1', bottle: 'Grise', undone: false }, { id: 8, file: 'c.sl1', ml: 8.5, source: 'model+partial', bottle: 'Grise', undone: false }] };
        window.__routes['/api/resin/printer-bottle'] = { success: true }; window.__routes['/api/resin/usage/undo'] = { success: true }; }""")
    page.evaluate("window.StellioV113.onResin()")
    page.wait_for_selector('#v13-ru-host select')
    txt = page.inner_text('#v13-ru-host')
    assert 'Consommation automatique' in txt and '40 ml' in txt and 'fichier .sl1' in txt and 'estimation (modèle) · partielle' in txt
    assert page.locator('#v13-ru-host b', has_text='z').count() == 0
    page.select_option('#v13-ru-host select', '1')
    page.wait_for_function("window.__bodies.some(b => b.printer_id === 3 && b.bottle_id === 1)")
    page.click('#v13-ru-host [data-uid="9"] [data-a="undo"]')
    page.wait_for_function("window.__bodies.some(b => b.id === 9)")
    assert not page._errs
