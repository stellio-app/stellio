"""1.1.7 — interface de l'Atelier avancé exécutée dans un vrai Chromium (si disponible) : aides pures, nuage 3D, éditeur de plateau, onglets.
Les appels réseau sont simulés dans la page (aucun serveur) : on vérifie le comportement du JavaScript, pas celui de l'API (testée ailleurs)."""
import json, os
import pytest
sync_api = pytest.importorskip('playwright.sync_api')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = open(os.path.join(ROOT, 'interface', 'suite.js'), encoding='utf-8').read()
CSS = open(os.path.join(ROOT, 'interface', 'style.css'), encoding='utf-8').read()

STUBS = """
window.API = ''; window.IS_VIEWER = false; window.__calls = []; window.__routes = {};
window.fetch = async (url, opt) => {
  const body = opt && opt.body ? (typeof opt.body === 'string' ? JSON.parse(opt.body) : '[form]') : null;
  const method = (opt && opt.method) || 'GET';
  window.__calls.push({ url, method, body });
  const key = method + ' ' + url.split('?')[0];
  let h = window.__routes[key] || window.__routes[url.split('?')[0]];
  const res = typeof h === 'function' ? h(body, url) : (h === undefined ? {} : h);
  return { ok: !(res && res.__status >= 400), status: (res && res.__status) || 200, json: async () => res, text: async () => (typeof res === 'string' ? res : JSON.stringify(res)), arrayBuffer: async () => new ArrayBuffer(0), blob: async () => new Blob(['x']) };
};
"""


@pytest.fixture(scope='module')
def page():
    try:
        pw = sync_api.sync_playwright().start()
        br = pw.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    except Exception as e:                                   # navigateur absent : test ignoré, pas échoué
        pytest.skip(f'Chromium indisponible : {e}')
    pg = br.new_page(viewport={'width': 1000, 'height': 900})
    pg.on('pageerror', lambda e: (_ for _ in ()).throw(AssertionError(f'erreur JS : {e}')))
    pg.set_content(f'<html><head><style>{CSS}</style></head><body><div id="host"></div></body></html>')
    pg.add_script_tag(content=STUBS)
    pg.add_script_tag(content=JS)
    yield pg
    br.close(); pw.stop()


def test_aides_pures(page):
    r = page.evaluate("""() => { const H = window.StellioSuite._h, plate = { w: 100, d: 100, z: 50 };
        const a = { id: 'a', x: 10, y: 10, w: 20, d: 10, h: 5, rot: 0 };
        return {
          snap: [H.snap(12.4, 1), H.snap(12.6, 5), H.snap(3, 0)],
          rot: H.rotate90(a), rot2: H.rotate90(H.rotate90(a)),
          left: H.align(a, plate, 'left').x, right: H.align(a, plate, 'right').x, cx: H.align(a, plate, 'center-x').x, front: H.align(a, plate, 'front').y, back: H.align(a, plate, 'back').y,
          ok: H.issues([a, { id: 'b', x: 30, y: 10, w: 10, d: 10, h: 5 }], plate),                      // bord contre bord : pas de chevauchement
          over: H.issues([a, { id: 'b', x: 29, y: 10, w: 10, d: 10, h: 5 }], plate).map(x => x.issue),
          out: H.issues([{ x: 95, y: 0, w: 10, d: 10, h: 5 }], plate).map(x => x.issue), tall: H.issues([{ x: 0, y: 0, w: 1, d: 1, h: 60 }], plate).map(x => x.issue),
          clamp: H.clamp({ x: 200, y: -5, w: 10, d: 10 }, plate),
          bounds: H.bounds([[0, 0, 0], [10, 20, 0]]), empty: H.bounds([]),
          p0: H.project([1, 0, 0], [0, 0, 0], 0, 0), pz: H.project([0, 0, 1], [0, 0, 0], 0, 0), pyaw: H.project([1, 0, 0], [0, 0, 0], Math.PI / 2, 0),
        }; }""")
    assert r['snap'] == [12, 15, 3] and r['rot']['w'] == 10 and r['rot']['d'] == 20 and r['rot']['rot'] == 90 and r['rot2']['w'] == 20 and r['rot2']['rot'] == 0
    assert (r['left'], r['right'], r['cx'], r['front'], r['back']) == (0, 80, 40, 0, 90)
    assert r['ok'] == [] and r['over'] == ['overlap'] and r['out'] == ['out_of_plate'] and r['tall'] == ['too_tall'] and r['clamp'] == {'x': 90, 'y': 0, 'w': 10, 'd': 10}
    assert r['bounds']['c'] == [5, 10, 0] and abs(r['bounds']['r'] - 11.18) < 0.01 and r['empty']['r'] == 1
    assert r['p0'][0] == 1 and r['pz'][1] == -1 and abs(r['pyaw'][0]) < 1e-9 and abs(r['pyaw'][2] - 1) < 1e-9     # Z vers le haut de l'écran ; yaw 90° envoie X en profondeur


def test_meme_regles_que_le_serveur(page):
    """La détection locale (coloration) doit donner les mêmes verdicts que check_layout du serveur."""
    import importlib.util, random
    spec = importlib.util.spec_from_file_location('plate_t', __import__('conftest').mod_path('plate_studio'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    rnd = random.Random(7)
    plate = {'w': 100, 'd': 80, 'z': 50}
    for _ in range(40):
        pts = [{'id': f'p{i}', 'x': rnd.choice([0, 10, 20, 30, 95]), 'y': rnd.choice([0, 10, 20, 75]), 'w': rnd.choice([10, 20, 30]), 'd': rnd.choice([10, 20]), 'h': rnd.choice([5, 60]), 'rot': 0} for i in range(rnd.randint(1, 5))]
        srv = sorted((i['issue'], i['id'], i.get('other', '')) for i in m.check_layout({'plate': plate, 'plates': [{'index': 1, 'placements': pts}]}))
        loc = page.evaluate("([pts, plate]) => window.StellioSuite._h.issues(pts, plate)", [pts, plate])
        mine = sorted((x['issue'], pts[x['i']]['id'], pts[x['j']]['id'] if 'j' in x else '') for x in loc)
        assert srv == mine, (pts, srv, mine)


def _count(page, rgb):
    return page.evaluate("""(rgb) => { const c = document.querySelector('canvas.suite-cloud'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let n = 0;
        for (let i = 0; i < d.length; i += 4) if (d[i + 3] > 200 && Math.abs(d[i] - rgb[0]) < 12 && Math.abs(d[i + 1] - rgb[1]) < 12 && Math.abs(d[i + 2] - rgb[2]) < 12) n++; return n; }""", rgb)


def test_nuage_3d_couleurs_bascule_et_rotation(page):
    pts = {'removed': [[i, 0, 0] for i in range(0, 40, 2)], 'added': [[0, i, 10] for i in range(0, 40, 2)], 'same': [[i, i, i] for i in range(0, 40, 2)]}
    page.evaluate("(pts) => { document.getElementById('host').innerHTML = ''; window.__cv = window.StellioSuite._cloudView(document.getElementById('host'), pts); }", pts)
    red, green = _count(page, (229, 72, 77)), _count(page, (48, 164, 108))
    assert red > 20 and green > 20                                               # rouge = retiré, vert = ajouté, réellement dessinés
    page.click('input[data-k="removed"]')
    assert _count(page, (229, 72, 77)) == 0 and _count(page, (48, 164, 108)) == green
    page.click('input[data-k="removed"]')
    assert _count(page, (229, 72, 77)) == red
    before = page.evaluate("window.__cv.state.yaw")
    box = page.locator('canvas.suite-cloud').bounding_box()
    page.mouse.move(box['x'] + 100, box['y'] + 100); page.mouse.down(); page.mouse.move(box['x'] + 200, box['y'] + 140, steps=4); page.mouse.up()
    assert page.evaluate("window.__cv.state.yaw") > before + 0.5                  # glisser fait tourner
    page.click('[data-view="top"]'); assert page.evaluate("window.__cv.state.pitch") == 1.5
    z = page.evaluate("window.__cv.state.zoom"); page.mouse.move(box['x'] + 300, box['y'] + 200); page.mouse.wheel(0, -300)
    assert page.evaluate("window.__cv.state.zoom") > z


def test_nuage_3d_vue_fil_de_fer(page):
    pts = {'removed': [[i, 0, 0] for i in range(0, 40, 4)], 'added': [[0, i, 10] for i in range(0, 40, 4)], 'same': [[i, i, i] for i in range(0, 40, 4)]}
    edges = {'removed': [[0, 0, 0, 30, 0, 0], [0, 5, 0, 30, 5, 0]], 'added': [[0, 0, 10, 0, 30, 10], [5, 0, 10, 5, 30, 10]], 'same': [[0, 0, 0, 30, 30, 30]]}
    page.evaluate("([pts, e]) => { document.getElementById('host').innerHTML = ''; window.__cv = window.StellioSuite._cloudView(document.getElementById('host'), pts, e); }", [pts, edges])
    assert page.locator('[data-mode="points"]').count() == 1 and page.locator('[data-mode="wire"]').count() == 1
    pointes = _count(page, (229, 72, 77))
    page.click('[data-mode="wire"]')
    fil = _count(page, (229, 72, 77))
    assert fil > 20 and fil != pointes                                                   # des traits rouges sont dessinés à la place des points
    page.click('input[data-k="removed"]'); assert _count(page, (229, 72, 77)) == 0       # les filtres restent actifs
    page.click('input[data-k="removed"]'); page.click('[data-mode="points"]')
    assert _count(page, (229, 72, 77)) == pointes
    page.evaluate("() => { document.getElementById('host').innerHTML = ''; window.StellioSuite._cloudView(document.getElementById('host'), { removed: [[0, 0, 0]], added: [], same: [] }); }")
    assert page.locator('[data-mode]').count() == 0                                      # sans arêtes (ancien résultat), pas de bouton


def test_editeur_de_plateau_glisser_pivoter_aligner_controle(page):
    page.evaluate("""() => { window.__calls.length = 0; window.__routes['POST /api/plate/check'] = (b) => ({ ok: true, issues: [] });
        window.__routes['POST /api/plate/export'] = {};
        window.__routes['POST /api/plate/rotate'] = (b) => ({ ok: true, rot: b.rot, w: b.rot % 180 ? 20 : 40, d: b.rot % 180 ? 40 : 20, h: 10, outline: [] });
        const st = { plate: { w: 200, d: 100, z: 100 }, cur: 1, sel: -1, snap: 1, plates: [{ index: 1, placements: [
            { id: '/s/a.stl', x: 10, y: 10, w: 40, d: 20, h: 10, rot: 0 }, { id: '/s/b.stl', x: 100, y: 10, w: 40, d: 20, h: 10, rot: 0 }] }, { index: 2, placements: [{ id: '/s/c.stl', x: 0, y: 0, w: 10, d: 10, h: 5, rot: 0 }] }] };
        document.getElementById('host').innerHTML = ''; window.__st = st; window.StellioSuite._plateEditor(document.getElementById('host'), st, [{ id: '/s/zzz.stl', reason: 'too_large' }]); }""")
    assert page.locator('.suite-part').count() == 2 and 'zzz.stl (too_large)' in page.inner_text('#host')
    assert any(c['url'] == '/api/plate/check' for c in page.evaluate("window.__calls"))          # contrôle serveur dès l'ouverture
    # glisser a de 90 mm vers la droite (échelle : 200 mm sur la largeur du SVG)
    svg = page.locator('svg.suite-bed').bounding_box(); sc = svg['width'] / 200
    a = page.locator('.suite-part').nth(0).bounding_box()
    page.mouse.move(a['x'] + a['width'] / 2, a['y'] + a['height'] / 2); page.mouse.down(); page.mouse.move(a['x'] + a['width'] / 2 + 90 * sc, a['y'] + a['height'] / 2, steps=5); page.mouse.up()
    x = page.evaluate("window.__st.plates[0].placements[0].x"); assert abs(x - 100) <= 2                  # a est maintenant sur b
    assert page.locator('.suite-part.bad').count() == 2                                                # chevauchement immédiatement en rouge
    n = len(page.evaluate("window.__calls")); page.wait_for_timeout(50)
    last = [c for c in page.evaluate("window.__calls") if c['url'] == '/api/plate/check'][-1]
    assert abs(last['body']['plates'][0]['placements'][0]['x'] - 100) <= 2                              # le serveur reçoit la nouvelle disposition
    # pivoter : empreinte échangée
    page.click('#su-prot'); page.wait_for_function("window.__st.plates[0].placements[0].rot === 90"); p = page.evaluate("window.__st.plates[0].placements[0]"); assert (p['w'], p['d'], p['rot']) == (20, 40, 90)
    # aligner à gauche
    page.select_option('#su-palign', 'left'); assert page.evaluate("window.__st.plates[0].placements[0].x") == 0
    assert page.locator('.suite-part.bad').count() == 0
    # clavier : flèche droite = +1 pas ; Maj = ×10
    page.focus('svg.suite-bed'); page.keyboard.press('ArrowRight'); assert page.evaluate("window.__st.plates[0].placements[0].x") == 1
    page.keyboard.press('Shift+ArrowRight'); assert page.evaluate("window.__st.plates[0].placements[0].x") == 11
    # changer de plateau
    page.click('[data-plate="2"]'); assert page.locator('.suite-part').count() == 1
    # export : la disposition complète et l'index du plateau partent au serveur
    page.evaluate("window.__calls.length = 0"); page.click('#su-pex'); page.wait_for_timeout(100)
    ex = [c for c in page.evaluate("window.__calls") if c['url'] == '/api/plate/export'][0]['body']
    assert ex['plate_index'] == 2 and len(ex['layout']['plates']) == 2
    # sélection requise pour pivoter
    page.click('svg.suite-bed', position={'x': 5, 'y': 5}); page.click('#su-prot'); page.wait_for_selector('#host .suite-msg'); assert 'Sélectionnez' in page.inner_text('#host .suite-msg')


def test_onglets_sessions_et_plugins_et_archives(page):
    page.evaluate("""() => {
      window.__calls.length = 0; const R = window.__routes;
      R['GET /api/sessions'] = { sessions: [{ sid: 's1', kind: 'user', ip: '1.2.3.4', ua: 'Firefox (X11)', last_seen: 1700000000, current: true }, { sid: 's2', kind: 'viewer', ip: '5.6.7.8', ua: 'Chrome', last_seen: 1700000100, current: false }], current: 's1', check_every_s: 15 };
      R['POST /api/sessions/s2/revoke'] = { ok: true }; R['POST /api/sessions/revoke-others'] = { ok: true, revoked: 1 };
      R['GET /api/plugins'] = { plugins: [{ id: 'meteo', name: 'Météo', version: '1.0', description: 'd', enabled: false, origin: 'community', permissions: ['events', 'network'] }] };
      R['PUT /api/plugins/meteo'] = { ok: true }; window.confirm = () => true;
      R['POST /api/plugins/catalog'] = { updates: 1, count: 1, plugins: [{ id: 'meteo', name: 'Météo', version: '1.1', description: 'Prévisions', author: 'Ana', homepage: 'https://github.com/ana/meteo', has_logo: true, official: true, installed_version: '1.0', update_available: true, permissions: ['events'] }] };
      R['POST /api/plugins/catalog/install'] = { ok: true, note: 'Mis à jour' };
      R['POST /api/print-history/7/gcode'] = { name: 'a.gcode', raw_size: 1000, gz_size: 100, sha256: 'ab' };
      R['GET /api/print-history/7/gcode'] = { archived: true, archive: { name: 'a.gcode', raw_size: 1000, gz_size: 100, sha256: 'ab' } };
      R['GET /api/licenses/expiring'] = { count: 1, expired: 1, items: [{ name: 'a.stl', license: 'CC-BY', expires: '2026-01-01', status: 'expired', days_left: -5 }] };
    }""")
    page.evaluate("window.StellioSuite.open('sessions')"); page.wait_for_selector('[data-revoke="s2"]')
    assert 'cette session' in page.inner_text('#su-body') and page.locator('[data-revoke]').count() == 1       # on ne peut pas révoquer sa propre session depuis la liste
    page.click('[data-revoke="s2"]'); page.wait_for_timeout(100)
    assert any(c['url'] == '/api/sessions/s2/revoke' and c['method'] == 'POST' for c in page.evaluate("window.__calls"))
    page.click('#su-srevall'); page.wait_for_timeout(100)
    assert any(c['url'] == '/api/sessions/revoke-others' for c in page.evaluate("window.__calls"))
    assert page.locator('#su-tabs').count() == 0                                                         # plus de barre d'onglets : chaque outil a son entrée dans le volet latéral
    page.evaluate("window.StellioSuite.open('plugins')")                                               # sans menu (test) : la page se crée sur place
    page.wait_for_selector('#plugins-root [data-pl="on"]'); page.wait_for_selector('#plugins-root .su-store-card')
    card = page.inner_text('#plugins-root .su-store-card')
    assert 'Météo' in card and 'Mettre à jour' in card and 'installé 1.0' in card and 'par Ana' in card and page.locator('#plugins-root .su-store-card .su-logo').count() == 1 and 'Page du plugin' in card
    page.evaluate("window.__calls.length = 0"); page.click('#su-plref'); page.wait_for_function("window.__calls.some(c => c.url === '/api/plugins/catalog' && c.body && c.body.refresh === true)")   # bouton Actualiser
    page.wait_for_selector('#plugins-root .su-store-card')
    assert 'Officiel' in card and 'su-badge-official' in page.inner_html('#plugins-root .su-store-card')                  # hébergé sur stellio-plugins
    assert page.locator('#plugins-root .su-plugin .su-badge-community').count() == 1 and 'Communautaire' in page.inner_text('#plugins-root .su-plugin')
    page.wait_for_selector('#plugins-root .su-store-card .su-logo-ph')
    assert page.locator('#plugins-root .su-store-card .su-logo-ph').count() == 1                                   # logo injoignable (ici : pas de serveur) -> icône de repli
    page.evaluate("document.querySelector('#plugins-root .su-store-card').__keep = 1")
    page.click('[data-pl="on"]'); page.wait_for_function("window.__calls.some(c => c.method === 'PUT' && c.url === '/api/plugins/meteo')"); page.wait_for_timeout(150)
    assert page.evaluate("!!document.querySelector('#plugins-root .su-store-card').__keep")          # activer ne reconstruit pas la page (pas de « flash »)
    put = [c for c in page.evaluate("window.__calls") if c['method'] == 'PUT' and c['url'] == '/api/plugins/meteo'][0]['body']
    assert put == {'enabled': True, 'ack_permissions': ['events', 'network']}                               # les permissions affichées sont celles acceptées
    cat_call = [c for c in page.evaluate("window.__calls") if c['url'] == '/api/plugins/catalog'][0]['body']
    assert 'url' not in cat_call and cat_call['lang']                                                       # sans source perso : catalogue officiel
    page.click('#plugins-root [data-cat="meteo"]'); page.wait_for_timeout(100)
    assert any(c['url'] == '/api/plugins/catalog/install' and c['body'] == {'id': 'meteo'} for c in page.evaluate("window.__calls"))
    page.evaluate("document.querySelectorAll('#plugins-root details.su-fold').forEach(d => d.open = true)")                 # sections repliables
    page.fill('#su-plcu', 'https://x.org/c.json'); page.click('#su-plcat'); page.wait_for_timeout(200)       # source personnalisée
    page.click('#plugins-root [data-cat="meteo"]'); page.wait_for_timeout(100)
    assert any(c['url'] == '/api/plugins/catalog/install' and c['body'] == {'id': 'meteo', 'url': 'https://x.org/c.json'} for c in page.evaluate("window.__calls"))
    page.click('#su-plcdef'); page.wait_for_timeout(200); assert page.input_value('#su-plcu') == ''
    page.evaluate("document.getElementById('plugins-root').remove()")
    page.evaluate("document.getElementById('suite-root').innerHTML = ''; window.StellioSuite.open('gcode')")
    page.wait_for_selector('#su-gid'); assert page.locator('#su-body .su-card').count() == 1 and page.evaluate("document.getElementById('su-gf').hidden") is True   # même style que les autres onglets
    page.evaluate("""() => { window.__routes['GET /api/print-history/by-file'] = { history: [{ id: 7, sent_at: '2026-11-18 21:00:00', result: 'success', printer_name: 'Voron' }] }; }""")
    assert page.evaluate("document.getElementById('su-gid').disabled") is True and page.locator('#su-body .su-inline').count() == 1     # tout sur une ligne, pas de numéro à saisir
    page.evaluate("() => { const i = document.getElementById('su-gpath'); i.value = '//nas/stl/dossier#5/a.gcode'; i.dispatchEvent(new Event('input')); }")
    page.wait_for_function("!document.getElementById('su-gid').disabled"); assert 'Voron' in page.inner_text('#su-gid') and page.inner_text('#su-gname') == 'a.gcode'
    page.click('#su-ginfo'); page.wait_for_selector('#su-gout p')
    assert any(c['url'].startswith('/api/print-history/7/gcode') for c in page.evaluate("window.__calls")) and 'ab' in page.inner_text('#su-gout')
    assert any(c['url'].startswith('/api/print-history/by-file?path=') and 'dossier%235' in c['url'] for c in page.evaluate("window.__calls"))
    page.evaluate("window.StellioSuite.open('licenses')"); page.wait_for_selector('#su-lgo'); assert 'expirée' in page.inner_text('#su-body') and 'a.stl' in page.inner_text('#su-body')


def test_diff_onglet_affiche_metriques_et_nuage(page):
    page.evaluate("""() => { window.__routes['POST /api/model-diff'] = { result: { removed_pct: 4.5, added_pct: 12.5, mean_distance_mm: 0.12, max_distance_mm: 3.4, identical: false,
        delta: { volume_mm3: 1500, size_mm: [1, 0, 2] }, points: { removed: [[0, 0, 0], [1, 1, 1]], added: [[5, 5, 5]], same: [[2, 2, 2]] } } }; }""")
    page.evaluate("window.StellioSuite.open('diff')"); page.wait_for_selector('#su-dgo')
    page.fill('#su-dp', '/s/a.stl'); page.click('#su-dgo'); page.wait_for_selector('#su-dout canvas.suite-cloud')
    t = page.inner_text('#su-dout'); assert '4.5 %' in t and '12.5 %' in t and '+1500 mm³' in t and 'Retiré (2)' in t and 'Ajouté (1)' in t


def test_plateau_vue_3d_bascule_et_arêtes(page):
    e = page.evaluate("window.StellioSuite._h.boxEdges({ x: 1, y: 2, w: 10, d: 20, h: 5 })")
    assert len(e) == 12 and min(p[2] for a in e for p in a) == 0 and max(p[2] for a in e for p in a) == 5
    xs = {p[0] for a in e for p in a}; ys = {p[1] for a in e for p in a}; assert xs == {1, 11} and ys == {2, 22}
    page.evaluate("document.getElementById('modal-suite') && document.getElementById('modal-suite').classList.add('hidden')")      # le panneau des tests précédents recouvre la page
    page.evaluate("""() => { window.__routes['POST /api/plate/check'] = { ok: true, issues: [] };
        const st = { plate: { w: 200, d: 100, z: 100 }, cur: 1, sel: -1, snap: 1, plates: [{ index: 1, placements: [{ id: '/s/a.stl', x: 10, y: 10, w: 40, d: 20, h: 30, rot: 0 }, { id: '/s/b.stl', x: 30, y: 10, w: 40, d: 20, h: 10, rot: 0 }] }] };
        document.getElementById('host').innerHTML = ''; window.StellioSuite._plateEditor(document.getElementById('host'), st, []); }""")
    assert page.locator('#su-bed3d').is_hidden() and page.locator('svg.suite-bed').is_visible()
    page.click('#su-p3d'); page.wait_for_timeout(50)
    assert page.locator('#su-bed3d').is_visible() and page.locator('svg.suite-bed').is_hidden()
    def px():                                                                    # des pixels sont réellement tracés, dont du rouge (chevauchement)
        return page.evaluate("""() => { const c = document.getElementById('su-bed3d'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let red = 0, any = 0;
            for (let i = 0; i < d.length; i += 4) { if (d[i + 3] > 0) any++; if (d[i] > 200 && d[i + 1] < 120 && d[i + 3] > 200) red++; } return [any, red]; }""")
    any_, red = px(); assert any_ > 500 and red > 100
    box = page.locator('#su-bed3d').bounding_box(); before = px()[0]
    page.mouse.move(box['x'] + 300, box['y'] + 200); page.mouse.down(); page.mouse.move(box['x'] + 380, box['y'] + 230, steps=4); page.mouse.up()
    assert px()[0] > 500                                                         # rotation : toujours dessiné
    page.click('#su-p3d'); assert page.locator('svg.suite-bed').is_visible()


def test_onglet_fiche_piece(page):
    page.evaluate("""() => { window.__calls.length = 0; window.__routes['GET /api/part-dossier'] = { path: '/l/boite.stl', name: 'boite.stl', size: 2048, exists: true,
        origin: { author: 'Ana', license: 'CC-BY-4.0', expires: '2026-01-01', status: 'expired', source_url: 'https://x/y' },
        versions: [{ version: 2, note: 'v2', created_at: 1700000000, prints: 3, success: 3 }, { version: 1, note: '', created_at: 1690000000, prints: 1, success: 0 }],
        best: { version: 2, profile: 'Standard', success: 3, total: 3 }, prints: { total: 4, success: 3, failed: 1, recent: [{ sent_at: '2026-11-04', model_version: 2, profile: 'Standard', printer: 'Ender', result: 'success' }] },
        gcode: [{ history_id: 2, name: 'boite.gcode', gz_size: 4096, sha256: 'abcdef0123456789' }], photos: [{ id: 1 }] }; }""")
    page.evaluate("window.StellioSuite.open('part')"); page.wait_for_selector('#su-ppgo')
    page.fill('#su-pp', '/l/boite.stl'); page.click('#su-ppgo'); page.wait_for_selector('#su-ppout h4')
    t = page.inner_text('#su-ppout')
    assert 'boite.stl' in t and 'Ana' in t and 'CC-BY-4.0' in t and 'expirée' in t and 'Standard' in t and 'Ender' in t and 'abcdef012345' in t and '1 photo' in t
    assert any(c['url'].startswith('/api/part-dossier?path=%2Fl%2Fboite.stl') for c in page.evaluate("window.__calls"))


def test_avancement_des_taches_jamais_nan(page):
    r = page.evaluate("""() => { const f = window.StellioSuite._pct; return [f(null), f(0.5), f({ done: 2, total: 5, message: 'étape' }), f({ done: 0, total: null, message: 'début' }), f({ done: 7, total: 5 })]; }""")
    assert r == ['', '50 %', '40 % — étape', 'début', '100 %'] and not any('NaN' in x for x in r)


def test_onglet_verification_avant_impression(page):
    page.evaluate("""() => { window.__calls.length = 0; window.__routes['POST /api/print-check'] = { path: '/l/tee.stl', name: 'tee.stl', triangles: 28, volume_cm3: 15.5, verdict: 'warning', bed: null,
        current: { size: [50, 50, 35], height: 35, base_area: 100, base_ratio: 0.04, overhang_area: 2400, overhang_ratio: 0.6, support_volume_cm3: 31.2, tall_thin: 0.7 },
        issues: [{ level: 'warning', code: 'overhangs' }, { level: 'warning', code: 'small_base' }, { level: 'info', code: 'better_orientation', gain: 0.9 }], gain: 0.9,
        best: { down: [0, 0, 1], label: 'z+', fits: true, metrics: { size: [50, 50, 35], height: 35, base_area: 2400, base_ratio: 0.96, overhang_area: 0, overhang_ratio: 0, support_volume_cm3: 0, tall_thin: 0.7 } },
        orientations: [{ down: [0, 0, 1], label: 'z+', fits: true, metrics: { height: 35, base_area: 2400, overhang_ratio: 0, support_volume_cm3: 0 } }, { down: [0, 0, -1], label: 'z-', fits: true, metrics: { height: 35, base_area: 100, overhang_ratio: 0.6, support_volume_cm3: 31.2 } }] }; }""")
    page.set_viewport_size({'width': 1500, 'height': 900})
    page.evaluate("window.__routes['GET /api/printers'] = [{ id: 3, name: 'Voron', config: { bed_x: 300, bed_y: 280, bed_z: 400 } }]")
    page.evaluate("window.StellioSuite.open('check')"); page.wait_for_selector('#su-ckgo')
    page.select_option('#su-ckpr', '3')                                          # l'imprimante remplit le plateau
    assert [page.input_value(i) for i in ('#su-ckx', '#su-cky', '#su-ckz')] == ['300', '280', '400']
    ys = {page.evaluate(f"document.querySelector('{i}').getBoundingClientRect().top|0") for i in ('#su-ck', '#su-ckpr', '#su-ckx', '#su-ckgo')}
    assert max(ys) - min(ys) < 40                                                # tout sur une seule ligne
    page.fill('#su-ck', '/l/tee.stl'); page.fill('#su-ckx', '220'); page.fill('#su-cky', '220'); page.fill('#su-ckz', '250'); page.click('#su-ckgo'); page.wait_for_selector('#su-ckout h4')
    t = page.inner_text('#su-ckout')
    assert 'tee.stl' in t and 'Surplombs importants' in t and 'Petite surface de contact' in t and 'Une autre orientation' in t and '−90 %' in t and '31.2' in t
    assert page.locator('#su-ckout a[href*="oriented"]').count() == 0 and page.locator('#su-ckdl').count() == 1      # plus de lien brut : même téléchargement que le reste
    call = [c for c in page.evaluate("window.__calls") if c['url'] == '/api/print-check'][0]
    assert call['body']['path'] == '/l/tee.stl' and call['body']['bed'] == {'x': 220, 'y': 220, 'z': 250}
    page.evaluate("window.__calls.length = 0"); page.click('#su-ckdl'); page.wait_for_function("document.querySelector('.suite-msg') && document.querySelector('.suite-msg').textContent.includes('tee_oriente.stl')")
    assert any(c['url'].startswith('/api/print-check/oriented?path=%2Fl%2Ftee.stl&down=0%2C0%2C1') for c in page.evaluate("window.__calls"))


def test_onglet_besoins_matiere(page):
    page.evaluate("""() => { window.__calls.length = 0; window.__routes['GET /api/filament/needs'] = { spool_g: 1000, rough_factor: 0.35, items: 5, unknown_weight: 1, materials: [
        { material: 'PLA', stock_g: 500, spools: 2, queue_g: 650, projects_g: 900, demand_g: 1550, shortfall_g: 1050, spools_to_buy: 2, items: 3, unknown_weight: 0, rough: 1, assumed_material: 1, daily_g: 50, days_left: 10 },
        { material: 'PETG', stock_g: 800, spools: 1, queue_g: 100, projects_g: 0, demand_g: 100, shortfall_g: 0, spools_to_buy: 0, items: 1, unknown_weight: 1, rough: 0, assumed_material: 0, daily_g: null, days_left: null }] }; }""")
    page.evaluate("window.StellioSuite.open('needs')"); page.wait_for_selector('#su-nout table')
    t = page.inner_text('#su-nout')
    assert 'PLA' in t and '1050 g' in t and 'PETG' in t and '✓' in t and '10 j' in t and 'sans poids connu' in t and 'comptés en PLA' in t and 'ordre de grandeur' in t
    assert page.locator('#su-nout tbody tr').count() == 2


def test_selecteur_de_modele_source_recherche_miniatures(page):
    """Chaque champ « Chemin du modèle » ouvre la bibliothèque : on choisit la source, on cherche, on clique une miniature."""
    page.evaluate("""() => { window._sourcesCache = [{ id: 1, name: 'Maison', type: 'folder', path: 'C:\\\\Modeles\\\\Maison' }, { id: 2, name: 'NAS', type: 'smb', path: '//nas/stl' }];
        window.allFiles = [{ path: 'C:\\\\Modeles\\\\Maison\\\\dragon.stl', name: 'dragon.stl', extension: '.stl' }, { path: 'C:\\\\Modeles\\\\Maison\\\\vase.3mf', name: 'vase.3mf', extension: '.3mf', has_thumb: false },
                          { path: '//nas/stl/robot.stl', name: 'robot.stl', extension: '.stl' }]; }""")
    page.evaluate("window.StellioSuite.open('diff')"); page.wait_for_selector('#su-dgo')
    assert page.locator('#su-dp ~ .suite-pick').count() == 1
    page.click('#su-dp ~ .suite-pick'); page.wait_for_selector('#sp-grid .sp-item')
    assert page.locator('#sp-grid .sp-item').count() == 3
    assert page.locator('#sp-src option').count() == 3                     # toutes + 2 sources
    assert page.locator('#sp-ext option').count() == 3 and 'STL (2)' in page.inner_text('#sp-ext') and '3MF (1)' in page.inner_text('#sp-ext')      # tous + STL + 3MF
    page.select_option('#sp-ext', '3MF'); assert page.locator('#sp-grid .sp-item').count() == 1 and 'vase' in page.inner_text('#sp-grid')
    page.select_option('#sp-ext', 'STL'); assert page.locator('#sp-grid .sp-item').count() == 2
    page.select_option('#sp-ext', '')
    page.select_option('#sp-src', '1'); assert page.locator('#sp-grid .sp-item').count() == 1 and 'robot' in page.inner_text('#sp-grid')
    page.select_option('#sp-src', '0'); assert page.locator('#sp-grid .sp-item').count() == 2
    page.fill('#sp-q', 'vase'); assert page.locator('#sp-grid .sp-item').count() == 1
    assert page.locator('#sp-grid .sp-thumb i.fa-cube').count() == 1       # sans miniature : icône
    page.click('#sp-grid .sp-item'); page.wait_for_function("!document.getElementById('modal-suite-picker') || document.getElementById('modal-suite-picker').classList.contains('hidden')")
    assert page.input_value('#su-dp') == 'C:\\Modeles\\Maison\\vase.3mf'
    # sélection multiple (plateau) : ajoute les chemins, sans doublon
    page.evaluate("window.StellioSuite.open('plate')"); page.wait_for_selector('#su-pgo')
    page.click('#su-pp ~ .suite-pick'); page.wait_for_selector('#sp-grid .sp-item')
    page.click('#sp-grid .sp-item >> nth=0'); page.click('#sp-grid .sp-item >> nth=2'); page.click('#sp-ok')
    assert page.input_value('#su-pp').split('\n') == ['C:\\Modeles\\Maison\\dragon.stl', '//nas/stl/robot.stl']


def test_editeur_de_plateau_formes_imbriquees(page):
    """Deux L imbriqués : les boîtes se recouvrent mais pas les contours → valide ; en les rapprochant → chevauchement ; la rotation vient du serveur."""
    page.evaluate("""() => { window.__calls.length = 0; window.__routes['POST /api/plate/check'] = (b) => ({ ok: true, issues: [] });
        window.__routes['POST /api/plate/rotate'] = (b) => ({ ok: true, rot: b.rot, w: 100, d: 100, h: 10, outline: [[[0, 0], [100, 0], [100, 40], [40, 40], [40, 100], [0, 100]]] });
        const L = [[0, 0], [100, 0], [100, 40], [40, 40], [40, 100], [0, 100]];
        const Lr = [[60, 60], [100, 60], [100, 100], [0, 100], [0, 0], [60, 0]].map(q => q);      // L tourné de 180° rangé à côté
        const st = { plate: { w: 300, d: 300, z: 100 }, cur: 1, sel: -1, snap: 1, mode: 'shape', plates: [{ index: 1, placements: [
            { id: '/s/l.stl', x: 0, y: 0, w: 100, d: 100, h: 10, rot: 0, outline: [L] },
            { id: '/s/l.stl#2', x: 50, y: 50, w: 100, d: 100, h: 10, rot: 0, outline: [[[60, 60], [100, 60], [100, 100], [0, 100], [0, 60]].slice(0, 0).concat([[0, 60], [60, 60], [60, 0], [100, 0], [100, 100], [0, 100]])] }] }] };
        document.getElementById('host').innerHTML = ''; window.__st = st; window.StellioSuite._plateEditor(document.getElementById('host'), st, []); }""")
    assert page.locator('.suite-part polygon').count() == 2
    r = page.evaluate("""() => { const H = window.StellioSuite._h, l = window.__st.plates[0].placements;
        const a = l[0], far = Object.assign({}, l[1], { x: 200, y: 200 });
        return { boxes: l[0].x < l[1].x + l[1].w && l[1].x < l[0].x + l[0].w, edges: H.shapeEdges(a).length, far: H.issues([a, far], window.__st.plate).length,
                 hit: H.polyOverlap(a, { outline: [[[0, 0], [30, 0], [30, 30], [0, 30]]], x: 10, y: 10 }), miss: H.polyOverlap(a, { outline: [[[0, 0], [20, 0], [20, 20], [0, 20]]], x: 60, y: 60 }) }; }""")
    assert r['boxes'] and r['edges'] > 12 and r['far'] == 0 and r['hit'] is True and r['miss'] is False
    page.locator('.suite-part polygon').nth(0).click(position={'x': 5, 'y': 5}); page.fill('#su-pang', '45'); page.click('#su-prot')
    page.wait_for_function("window.__st.plates[0].placements[0].rot === 45")
    last = [c for c in page.evaluate("window.__calls") if c['url'] == '/api/plate/rotate'][-1]['body']
    assert last['rot'] == 45 and last['id'] == '/s/l.stl'
    assert page.evaluate("window.__st.plates[0].placements[0].outline[0].length") == 6


def test_onglet_plateau_champs_separes_imprimante_exemplaires_et_legende(page):
    page.evaluate("""() => { window.__calls.length = 0;
        window.__routes['GET /api/printers'] = [{ id: 3, name: 'Voron', config: { bed_x: 300, bed_y: 280, bed_z: 400 } }, { id: 4, name: 'Sans volume', config: {} }];
        window.__routes['POST /api/plate/check'] = { ok: true, issues: [] };
        window.__routes['POST /api/plate/arrange'] = (b) => ({ ok: true, mode: 'shape', plate: b.plate, unplaced: [], plates: [{ index: 1, placements: [
            { id: '//nas/a#1/p.stl#1', x: 0, y: 0, w: 40, d: 40, h: 10, rot: 0 }, { id: '//nas/a#1/p.stl#2', x: 50, y: 0, w: 40, d: 40, h: 10, rot: 0 }] }] }); }""")
    page.evaluate("window.StellioSuite.open('plate')"); page.wait_for_selector('#su-pwl')
    assert page.locator('#su-pwl, #su-pwd, #su-pwh').count() == 3 and page.locator('#su-pw').count() == 0
    assert 'Sans volume' not in page.inner_text('#su-ppr')                                                    # une imprimante sans volume connu n'est pas proposée
    page.select_option('#su-ppr', '3'); assert [page.input_value(i) for i in ('#su-pwl', '#su-pwd', '#su-pwh')] == ['300', '280', '400']
    page.fill('#su-pp', '//nas/a#1/p.stl x2\n//nas/a#1/q.stl\n//nas/a#1/q.stl'); page.click('#su-pgo'); page.wait_for_selector('.suite-legend-item')
    b = [c for c in page.evaluate("window.__calls") if c['url'] == '/api/plate/arrange'][0]['body']
    assert b['plate'] == {'w': 300, 'd': 280, 'z': 400} and b['paths'] == ['//nas/a#1/p.stl', '//nas/a#1/q.stl'] and b['counts'] == {'//nas/a#1/p.stl': 2, '//nas/a#1/q.stl': 2}
    leg = page.inner_text('#su-plegend'); assert leg.count('p.stl') == 2 and '1' in leg and '#' not in leg.split('Plateau')[1]       # nom du fichier + position, sans le chemin
    assert page.evaluate("document.querySelectorAll('.suite-part text')[1].textContent") == '2'
    page.click('.suite-legend-item >> nth=1'); assert page.evaluate("document.querySelectorAll('.suite-part')[1].classList.contains('sel')")
    assert page.evaluate("getComputedStyle(document.getElementById('su-pout')).marginTop") != '' and page.evaluate("document.getElementById('su-pbusy').hidden") is True


def test_selecteur_pagination_visuelle(page):
    page.evaluate("""() => { window._sourcesCache = []; window.allFiles = Array.from({ length: 130 }, (_, i) => ({ path: '/m/p' + i + '.stl', name: 'p' + i + '.stl', extension: '.stl' })); }""")
    page.evaluate("window.StellioSuite.open('diff')"); page.wait_for_selector('#su-dgo')
    page.click('#su-dp ~ .suite-pick'); page.wait_for_selector('#sp-grid .sp-item')
    assert page.locator('#sp-grid .sp-item').count() == 48 and page.locator('#sp-more').count() == 0
    assert page.evaluate("parseFloat(getComputedStyle(document.getElementById('sp-q')).borderTopLeftRadius)") > 0      # champ de recherche arrondi comme les autres
    assert page.locator('#sp-pager .sp-pg.active').inner_text() == '1' and '1–48 / 130' in page.inner_text('#sp-count')
    assert page.locator('#sp-pager [data-pg="0"]').first.is_disabled()
    page.click('#sp-pager .sp-pg:has-text("3")'); assert page.locator('#sp-grid .sp-item').count() == 34 and '97–130 / 130' in page.inner_text('#sp-count')
    page.click('#sp-pager [data-pg="0"] >> nth=0'); assert page.locator('#sp-pager .sp-pg.active').inner_text() == '1'
    page.fill('#sp-q', 'p12'); assert page.locator('#sp-pager .sp-pg').count() == 0 or page.locator('#sp-pager').inner_text().strip() == ''   # 1 page : pas de pagination
    page.evaluate("document.getElementById('sp-x').click()")


def test_pagination_condensee_avec_points_de_suspension(page):
    h = page.evaluate("() => { const d = document.createElement('div'); d.innerHTML = window.StellioSuite._pager(10, 40); return d.textContent; }")
    assert '1' in h and '11' in h and '40' in h and '…' in h


def test_sous_onglets_sur_une_ligne_et_synchro_masquee_en_desktop(page):
    page.evaluate("window.stellioAppConfig = { server_edition: false }")
    assert 'sync' in page.evaluate("window.StellioSuite.tabs")
    page.evaluate("document.getElementById('suite-root') && document.getElementById('suite-root').remove()")
    page.evaluate("window.StellioSuite.onShow()"); page.wait_for_selector('#su-body')
    assert page.locator('#su-tabs').count() == 0
    for tab, ids in (('diff', ('#su-dp', '#su-da', '#su-db', '#su-dgo')), ('compat', ('#su-cp', '#su-cm', '#su-cgo')), ('similar', ('#su-sp', '#su-sgo', '#su-sbuild'))):
        page.evaluate(f"window.StellioSuite.open('{tab}')"); page.wait_for_selector(ids[-1])
        ys = {page.evaluate(f"document.querySelector('{i}').getBoundingClientRect().top|0") for i in ids}
        assert max(ys) - min(ys) < 40, (tab, ys)


def test_bouton_reinitialiser_et_champs_de_taille_adaptee(page):
    page.set_viewport_size({'width': 1500, 'height': 900})
    page.evaluate("window.__routes['POST /api/model-diff'] = { result: { removed_pct: 1, added_pct: 2, mean_distance_mm: 0.1, max_distance_mm: 1, identical: false, delta: null, points: {} } }")
    page.evaluate("window.__routes['GET /api/compat/model'] = { printers: [{ printer: 'Voron', status: 'ok', checks: [] }] }")
    page.evaluate("window.StellioSuite.open('compat')"); page.wait_for_selector('#su-cgo')
    page.fill('#su-cp', '/l/a.stl'); page.fill('#su-cm', 'PETG'); page.click('#su-cgo'); page.wait_for_selector('#su-cout table')
    assert page.locator('#su-cout table').count() == 1
    page.click('.su-reset')
    assert page.input_value('#su-cp') == '' and page.input_value('#su-cm') == '' and page.inner_text('#su-cout').strip() == ''
    w = page.evaluate("document.querySelector('#su-cm').getBoundingClientRect().width")
    assert w < 260                                                                # champ « Matière » plus petit qu'avant (pleine largeur)
    # Vérif. impression : les cases numériques ne se chevauchent pas
    page.evaluate("window.StellioSuite.open('check')"); page.wait_for_selector('#su-ckgo')
    boxes = page.evaluate("['#su-ckx', '#su-cky', '#su-ckz', '#su-cka'].map(i => { const r = document.querySelector(i).getBoundingClientRect(); return [r.left, r.right]; })")
    assert all(boxes[i][1] <= boxes[i + 1][0] + 1 for i in range(3)), boxes
    # Plateau : tout sur une ligne, cases petites
    page.evaluate("window.StellioSuite.open('plate')"); page.wait_for_selector('#su-pgo')
    ys = {page.evaluate(f"document.querySelector('{i}').getBoundingClientRect().top|0") for i in ('#su-ppr', '#su-pwl', '#su-pwd', '#su-pwh', '#su-pm', '#su-pmode', '#su-pstep')}
    assert max(ys) - min(ys) < 10, ys
    assert page.evaluate("document.querySelector('#su-pwl').getBoundingClientRect().width") < 140
    page.click('.su-reset'); assert page.input_value('#su-pwl') == '256'


def test_similaires_message_lisible(page):
    page.evaluate("window.__routes['GET /api/similar/status'] = { indexed: 12, total: 1906, estimated_seconds_left: 600 }")
    page.evaluate("window.StellioSuite.open('similar')"); page.wait_for_selector('#su-sgo')
    t = page.inner_text('#su-body')
    assert '12 / 1' in t and '{' not in t and '10 min' in t


def test_similaires_fichiers_ignores_bouton_popup_causes_et_reessayer(page):
    page.evaluate("""() => { window.__routes['GET /api/similar/status'] = () => ({ indexed: 1, total: 5, skipped: 4 });
        window.__routes['GET /api/similar/skipped'] = () => ({ max_mb: 60, count: 4, files: [
          { path: '/s/gros.stl', name: 'gros.stl', size: 90000000, reason: 'Fichier non indexable.', code: 'too_big', ext: 'stl' },
          { path: '/s/casse.stl', name: 'casse.stl', size: 26, reason: 'bad', code: 'unreadable', ext: 'stl' },
          { path: '/s/vide.obj', name: 'vide.obj', size: 8, reason: 'Maillage vide.', code: 'empty', ext: 'obj' },
          { path: '/s/absent.stl', name: 'absent.stl', size: 1, reason: 'No such file', code: 'missing', ext: 'stl' }] });
        window.__routes['POST /api/similar/skipped/retry'] = () => ({ ok: true, retried: 4 }); window.__routes['POST /api/similar/build'] = () => ({ job_id: 'j1' });
        window.__routes['GET /api/jobs/j1'] = () => ({ state: 'done', progress: 1 }); }""")
    page.evaluate("window.__calls.length = 0")
    page.evaluate("window.StellioSuite.open('similar')"); page.wait_for_selector('#su-sskip')
    assert 'Fichiers ignorés (4)' in page.inner_text('#su-sskip')
    page.click('#su-sskip'); page.wait_for_selector('#modal-suite-skipped .sk-row')
    t = page.inner_text('#modal-suite-skipped')
    assert page.locator('#modal-suite-skipped .sk-row').count() == 4 and page.locator('#modal-suite-skipped .sk-row .su-thumb').count() == 4          # une miniature par fichier
    assert 'Trop gros' in t and 'Aucune surface' in t and 'Illisible' in t and 'Introuvable' in t
    assert 'dépasse 60 Mo' in t and 'Réexportez' in t and 'Simplifiez' in t and '{max}' not in t                                            # une solution par cause
    page.click('#sk-retry')
    page.wait_for_function("window.__calls.some(c => c.url === '/api/similar/build')")
    assert any(c['url'] == '/api/similar/skipped/retry' and c['method'] == 'POST' for c in page.evaluate('window.__calls'))
    assert page.locator('#modal-suite-skipped.hidden').count() == 1


def test_onglet_lent_n_ecrase_pas_l_onglet_ouvert_ensuite(page):
    """Cliquer « Archives G-code » pendant que « Similaires » charge : l'onglet affiché reste celui sur lequel on est."""
    page.evaluate("""() => { window.__release = null; window.__routes['GET /api/similar/status'] = () => ({ indexed: 1, total: 2 });
        const f = window.__fetch0 = window.fetch; window.fetch = (u, o) => String(u).startsWith('/api/similar/status') ? new Promise(r => { window.__release = () => r(f(u, o)); }) : f(u, o); }""")
    page.evaluate("void window.StellioSuite.open('jobs')"); page.wait_for_timeout(100)
    page.evaluate("void window.StellioSuite.open('similar')"); page.wait_for_timeout(100)
    page.evaluate("void window.StellioSuite.open('gcode')"); page.wait_for_selector('#su-gst')
    page.evaluate("window.__release()"); page.wait_for_timeout(300)
    assert page.locator('#su-gst').count() == 1 and page.locator('#su-sgo').count() == 0
    page.evaluate("() => { window.fetch = window.__fetch0; }")                                  # ne pas laisser le délai artificiel aux tests suivants



def _gcode_exemple(layers=40):
    """G-code de démonstration : un vase carré (3 périmètres) puis un cylindre, 0,2 mm par couche, extrusion relative."""
    import math
    out = ['; test', 'G21', 'G90', 'M83', 'G92 E0']
    for i in range(layers):
        z = round(0.2 * (i + 1), 3)
        out.append(f'G1 Z{z} F600')
        for k, r in enumerate((20, 19.2, 18.4)):
            if i < layers // 2:
                pts = [(110 - r, 110 - r), (110 + r, 110 - r), (110 + r, 110 + r), (110 - r, 110 + r), (110 - r, 110 - r)]
            else:
                pts = [(110 + r * math.cos(a * math.pi / 18), 110 + r * math.sin(a * math.pi / 18)) for a in range(37)]
            out.append(f'G0 X{pts[0][0]:.2f} Y{pts[0][1]:.2f}')
            for (x, y) in pts[1:]:
                out.append(f'G1 X{x:.2f} Y{y:.2f} E0.4 F1800')
        out.append('G1 E-0.8 F2400 ; retract')
    return '\n'.join(out)


def test_plugin_avec_page_menu_cadre_isole_et_visionneuse_gcode(page):
    viewer = open(os.path.join(ROOT, 'sdk', 'examples', 'gcode-viewer', 'viewer.html'), encoding='utf-8').read()
    manifest = json.load(open(os.path.join(ROOT, 'sdk', 'examples', 'gcode-viewer', 'plugin.json'), encoding='utf-8'))
    page.set_viewport_size({'width': 1300, 'height': 800})
    page.evaluate("""() => { document.body.insertAdjacentHTML('beforeend', '<h1 id="header-page-title"></h1><div id="plugin-nav-list"></div><div id="page-plugin-view" class="page active"><div id="pv-msg" hidden></div><iframe id="pv-frame" sandbox="allow-scripts" style="width:100%;height:600px;border:0"></iframe></div>'); }""")
    page.evaluate("""([m, html, gc]) => {
      const R = window.__routes;
      R['GET /api/plugins'] = { plugins: [Object.assign({}, m, { enabled: true, config: {} }), { id: 'sans-page', name: 'Sans page', version: '1', enabled: true, permissions: ['events'], events: ['print.finished'] }] };
      R['GET /api/plugins/gcode-viewer/ui'] = html;
      R['GET /api/gcodes'] = { total: 2, gcodes: [{ id: 7, name: 'vase_carre.gcode', size: 52000, project_name: 'Déco' }, { id: 8, name: 'autre.gcode', size: 1000 }] };
      R['GET /api/projects/gcodes/7/download'] = gc;
      R['GET /api/settings'] = { secret: 'ne doit jamais sortir' };
    }""", [manifest, viewer, _gcode_exemple()])
    page.evaluate("window.StellioSuite._refreshPluginNav()")
    page.wait_for_selector('#plugin-nav-list [data-plugin-ui="gcode-viewer"]')
    assert page.locator('#plugin-nav-list [data-plugin-ui]').count() == 1                          # seul un plugin qui a une page est listé
    assert 'G-code viewer' in page.inner_text('#plugin-nav-list')
    page.click('#plugin-nav-list [data-plugin-ui="gcode-viewer"]')
    fr = page.frame_locator('#pv-frame')
    fr.locator('.item').first.wait_for()
    assert fr.locator('.item').count() == 2 and 'vase_carre.gcode' in fr.locator('.item').first.inner_text()
    fr.locator('.item').first.click()
    fr.locator('#stats b').first.wait_for(timeout=20000)
    assert fr.locator('#stats b').first.inner_text() == '40'                                       # 40 couches reconnues
    frame = [f for f in page.frames if f != page.main_frame][0]
    assert frame.evaluate("document.getElementById('lmax').max") == '40' and frame.evaluate("document.getElementById('lmax').value") == '40'
    assert 'G1 X' in frame.evaluate("document.getElementById('code').textContent")                  # ligne de G-code courante
    px = frame.evaluate("(() => { const c = document.getElementById('gl'), t = document.createElement('canvas'); t.width = c.width; t.height = c.height; const x = t.getContext('2d'); x.drawImage(c, 0, 0); const d = x.getImageData(0, 0, t.width, t.height).data; let n = 0; for (let i = 0; i < d.length; i += 4) if (Math.abs(d[i] - d[0]) + Math.abs(d[i + 1] - d[1]) + Math.abs(d[i + 2] - d[2]) > 60) n++; return n; })()")
    assert px > 500                                                                                  # le modèle 3D est dessiné (WebGL 2)
    frame.evaluate("document.getElementById('lmax').value = 5; document.getElementById('lmax').dispatchEvent(new Event('input'))")
    assert '5/40' in frame.evaluate("document.getElementById('lmaxl').textContent")
    frame.evaluate("document.getElementById('ocol').value = 'speed'; document.getElementById('ocol').dispatchEvent(new Event('change'))")
    frame.evaluate("document.querySelector('[data-v=top]').click()")
    assert frame.evaluate("document.getElementById('play').click(), document.getElementById('play').textContent") == '⏸'
    frame.evaluate("document.getElementById('play').click()")
    gc = os.path.join(os.path.dirname(__file__), '_local_exemple.gcode')                           # G-code choisi depuis le PC
    open(gc, 'w').write(_gcode_exemple())
    try:
        frame.set_input_files('#fin', gc)
        frame.wait_for_function("document.querySelector('.item.on') && document.querySelector('.item.on').textContent.indexOf('_local_exemple') >= 0", timeout=20000)
        assert frame.evaluate("document.getElementById('lmax').max") == '40'
    finally:
        os.remove(gc)
    # isolation : aucun réseau direct, aucun cookie/stockage de Stellio, passerelle en lecture seule avec liste noire
    assert frame.evaluate("fetch('/api/settings').then(() => 'ouvert', () => 'bloque')") == 'bloque'
    assert frame.evaluate("(() => { try { return parent.document.title, 'acces'; } catch (e) { return 'bloque'; } })()") == 'bloque'
    assert frame.evaluate("window.stellio.api('/api/settings').then(() => 'ok', e => e.message)") == 'Chemin non autorisé.'
    assert frame.evaluate("window.stellio.api('/api/plugins').then(() => 'ok', e => e.message)") == 'Chemin non autorisé.'
    assert frame.evaluate("window.stellio.api('/api/../x').then(() => 'ok', e => e.message)") == 'Chemin non autorisé.'
    assert frame.evaluate("window.stellio.theme.accent") != ''                                      # le thème de Stellio est transmis
    # sans la permission api:read, la passerelle refuse tout
    page.evaluate("window.__routes['GET /api/plugins'].plugins[0].permissions = ['ui']; window.StellioSuite._refreshPluginNav()")
    page.wait_for_timeout(100)
    page.evaluate("window.StellioSuite._openPluginView('gcode-viewer')")
    page.wait_for_timeout(600)
    frame = [f for f in page.frames if f != page.main_frame][0]
    assert 'api:read' in frame.evaluate("window.stellio.api('/api/gcodes').then(() => 'ok', e => e.message)")
    page.evaluate("['plugin-nav-list', 'page-plugin-view', 'header-page-title'].forEach(i => document.getElementById(i).remove())")


def test_liste_des_modeles_du_plateau_avec_bouton_retirer(page):
    page.evaluate("window.StellioSuite.open('plate')"); page.wait_for_selector('#su-pp')
    page.fill('#su-pp', '//nas/a/Bolt.STL\n//nas/a/Key.STL x3\n//nas/a/Bolt.STL')
    page.wait_for_selector('#su-pp-list .su-pp-row')
    assert page.locator('#su-pp-list .su-pp-row').count() == 2 and '×2' in page.inner_text('#su-pp-list') and '×3' in page.inner_text('#su-pp-list')
    page.click('#su-pp-list [data-pp-del="0"]')                                   # retire Bolt (toutes ses lignes)
    assert page.input_value('#su-pp').strip() == '//nas/a/Key.STL x3' and page.locator('#su-pp-list .su-pp-row').count() == 1
    page.click('#su-pp-list [data-pp-clear]')
    assert page.input_value('#su-pp') == '' and page.locator('#su-pp-list').is_hidden()


def test_export_3mf_affiche_un_repere_de_travail_en_cours(page):
    """Pendant l'export 3MF (calcul serveur parfois long) : bandeau animé + bouton marqué occupé, retirés ensuite, puis confirmation."""
    page.evaluate("""() => { window.__routes['POST /api/plate/check'] = () => ({ ok: true, issues: [] }); window.__routes['POST /api/plate/export'] = {};
        const st = { plate: { w: 200, d: 100, z: 100 }, cur: 1, sel: -1, snap: 1, plates: [{ index: 1, placements: [{ id: '/s/a.stl', x: 10, y: 10, w: 40, d: 20, h: 10, rot: 0 }] }] };
        document.getElementById('host').innerHTML = ''; window.__gate = new Promise(r => { window.__open = r; }); const f = window.fetch;
        window.fetch = (u, o) => String(u).includes('/api/plate/export') ? window.__gate.then(() => ({ ok: true, status: 200, blob: async () => new Blob(['x']) })) : f(u, o);
        window.StellioSuite._plateEditor(document.getElementById('host'), st, []); }""")
    assert page.locator('#su-pwork').is_hidden()
    page.click('#su-pex')
    page.wait_for_selector('#su-pwork', state='visible'); assert 'Export 3MF' in page.inner_text('#su-pwork')
    assert page.get_attribute('#su-pex', 'aria-busy') == 'true' and 'su-btn-busy' in page.get_attribute('#su-pex', 'class')
    page.evaluate("window.__open()")
    page.wait_for_selector('#su-pwork', state='hidden'); assert page.get_attribute('#su-pex', 'aria-busy') is None
    page.wait_for_selector('#host .suite-msg'); assert 'plateau-1.3mf' in page.inner_text('#host .suite-msg')


def _ouvrir(page, tab):
    page.evaluate("window.__calls.length = 0"); page.evaluate(f"void window.StellioSuite.open('{tab}')")


def test_organisation_ajouter_et_supprimer_une_regle(page):
    page.evaluate("""() => { window.__rules = [{ id: 7, name: 'PLA en vrac', field: 'material', op: 'is', value: 'PLA', action: 'tag', target: 'PLA' }];
        window.__routes['GET /api/organize/rules'] = () => ({ rules: window.__rules, actions: ['tag', 'collection', 'suggest_folder'], fields: { ext: ['is', 'in'], name: ['contains', 'not_contains'], license_commercial: ['is'], material: ['is'], size_mb: ['gt', 'lt'], printed: ['is'] } });
        window.__routes['POST /api/organize/rules'] = (b) => { window.__rules.push(Object.assign({ id: 8 }, b)); return { ok: true, id: 8 }; };
        window.__routes['DELETE /api/organize/rules/7'] = () => { window.__rules = window.__rules.filter(r => r.id !== 7); return { ok: true }; };
        window.__routes['POST /api/organize/preview'] = () => ({ total: 1, items: [{ path: '/s/a/Bolt.stl', action: 'tag', target: 'PLA', rule: 'PLA en vrac' }], truncated: false }); }""")
    _ouvrir(page, 'organize'); page.wait_for_selector('#su-oadd')
    assert 'PLA en vrac' in page.inner_text('#su-body') and page.locator('[data-odel="7"]').count() == 1
    page.select_option('#su-of', 'ext'); assert page.locator('#su-oo option').count() == 2            # les conditions suivent le critère
    page.select_option('#su-of', 'printed'); assert page.evaluate("document.getElementById('su-ov').tagName") == 'SELECT'   # valeur oui/non : liste
    page.select_option('#su-of', 'ext'); page.select_option('#su-oo', 'in'); page.fill('#su-ov', 'stl, 3mf'); page.select_option('#su-oa', 'collection'); page.fill('#su-ot', 'À trier')
    page.click('#su-oadd'); page.wait_for_function("document.querySelectorAll('[data-odel]').length === 2")
    sent = [c for c in page.evaluate("window.__calls") if c['method'] == 'POST' and c['url'] == '/api/organize/rules'][0]['body']
    assert (sent['field'], sent['op'], sent['value'], sent['action'], sent['target']) == ('ext', 'in', 'stl, 3mf', 'collection', 'À trier')
    page.click('[data-odel="7"]'); page.wait_for_function("document.querySelectorAll('[data-odel]').length === 1")
    page.click('#su-oprev'); page.wait_for_selector('#su-oout table'); assert 'Bolt.stl' in page.inner_text('#su-oout') and 'PLA en vrac' in page.inner_text('#su-oout')


def test_licences_champ_date_natif_et_dates_localisees(page):
    page.evaluate("""() => { window.__routes['GET /api/licenses/expiring'] = () => ({ count: 1, expired: 0, items: [{ name: 'a.stl', license: 'CC BY', expires: '2027-01-31', status: 'soon', days_left: 20 }] }); }""")
    _ouvrir(page, 'licenses'); page.wait_for_selector('#su-ld')
    assert page.get_attribute('#su-ld', 'type') == 'date'
    txt = page.inner_text('#su-body'); assert '2027-01-31' not in txt and '2027' in txt            # date affichée selon la langue du système, plus en AAAA-MM-JJ brut
    page.fill('#su-lp', '/s/a.stl'); page.fill('#su-ld', '2027-02-15'); page.evaluate("window.__calls.length = 0"); page.click('#su-lgo')
    page.wait_for_function("window.__calls.some(c => c.url === '/api/files/license-expiry')")
    assert [c for c in page.evaluate("window.__calls") if c['url'] == '/api/files/license-expiry'][0]['body']['date'] == '2027-02-15'   # toujours envoyée en ISO


def test_similaires_miniature_a_cote_du_fichier(page):
    page.evaluate("""() => { window.__routes['GET /api/similar/status'] = () => ({ indexed: 2, total: 2 });
        window.__routes['GET /api/similar'] = () => ({ results: [{ path: '//nas/stl/Box/Bolt.STL', name: 'Bolt.STL', similarity: 100 }, { path: '//nas/stl/Other/Key.STL', name: 'Key.STL', similarity: 91.5 }] }); }""")
    _ouvrir(page, 'similar'); page.wait_for_timeout(100); page.evaluate("window.__release && window.__release()")   # le test précédent a laissé un délai sur /api/similar/status
    page.wait_for_selector('#su-sp'); page.fill('#su-sp', '//nas/stl/Box/Bolt.STL'); page.click('#su-sgo'); page.wait_for_selector('#su-sout .su-thumb')
    assert page.locator('#su-sout .su-thumb').count() == 2
    # la miniature (introuvable dans ce décor) est remplacée par une icône dès son erreur : on lit donc son adresse avant, ou on accepte l'icône
    assert page.locator('#su-sout .su-thumb img[src*="/api/thumb?path="], #su-sout .su-thumb i.fa-cube').count() == 2 and 'Bolt.STL' in page.inner_text('#su-sout') and 'Other' in page.inner_text('#su-sout')   # dossier visible : deux « Bolt » se distinguent


def test_assistant_fabrication_reponse_lisible_et_pas_de_json_brut(page):
    page.evaluate("""() => { window.__routes['POST /api/fab/ask'] = () => ({ ai_note: '', notes: ['Aucune impression réussie notée pour ce modèle.'], params: { model: 'pièce' }, proposals: [], query: 'suggest_settings', rows: [], summary: { model: 'pièce', successes: 0 }, via: 'ai' }); }""")
    _ouvrir(page, 'fab'); page.wait_for_selector('#su-fgo'); page.fill('#su-fq', 'quelle pièce a réussi'); page.click('#su-fgo'); page.wait_for_selector('#su-fout h4')
    t = page.inner_text('#su-fout'); assert 'Réglages qui ont réussi' in t and 'pièce' in t and 'Aucune impression réussie' in t and '"query"' not in t and '{' not in t
    assert page.locator('[data-fex]').count() == 4                                                   # exemples de questions cliquables
    page.evaluate("""() => { window.__routes['POST /api/fab/ask'] = () => ({ query: 'suggest_material', params: { model: 'Bolt' }, notes: [], proposals: [], via: 'rules', ai_note: 'ai_unreadable', summary: { model: 'Bolt' }, rows: [{ material: 'PETG', prints: 5, success: 4, rate: 80, score: 40, source: 'ce modèle' }] }); }""")
    page.click('[data-fex]'); page.wait_for_selector('#su-fout table'); t = page.inner_text('#su-fout'); assert 'PETG' in t and '80 %' in t and "n'a pas pu être lue" in t


def test_journal_audit_par_pages_et_similaires_s_affiche_sans_attendre(page):
    page.evaluate("""() => { window.__routes['GET /api/audit'] = (b, u) => { const q = new URLSearchParams(u.split('?')[1] || ''), lim = +q.get('limit'), off = +q.get('offset');
          const rows = Array.from({ length: Math.max(0, Math.min(lim, 60 - off)) }, (_, i) => ({ ts: 1700000000 + off + i, actor: 'romain', action: 'settings.change', target: 'r' + (off + i), ip: '' }));
          return { rows, count: rows.length, total: 60, remote: 0, offset: off, limit: lim }; }; }""")
    _ouvrir(page, 'audit'); page.wait_for_selector('#su-atable tbody tr')
    assert page.locator('#su-atable tbody tr').count() == 25 and '1–25 / 60' in page.inner_text('#su-ainfo')          # 25 lignes par défaut
    page.click('#su-apager [data-pg="2"]'); page.wait_for_function("document.querySelectorAll('#su-atable tbody tr').length === 10")
    assert '51–60 / 60' in page.inner_text('#su-ainfo')
    page.select_option('#su-asize', '10'); page.wait_for_function("document.querySelectorAll('#su-atable tbody tr').length === 10 && document.querySelector('#su-ainfo').textContent.startsWith('1–10')")
    # Similaires : le formulaire est là tout de suite, même si l'état de l'index tarde
    page.evaluate("""() => { window.__release2 = null; window.__routes['GET /api/similar/status'] = () => ({ indexed: 3, total: 9 });
        const f = window.__fetch1 = window.fetch; window.fetch = (u, o) => String(u).startsWith('/api/similar/status') ? new Promise(r => { window.__release2 = () => r(f(u, o)); }) : f(u, o); }""")
    _ouvrir(page, 'similar'); page.wait_for_selector('#su-sgo', timeout=2000)
    assert 'Lecture' in page.inner_text('#su-sidx')
    page.evaluate("window.__release2()"); page.wait_for_function("document.querySelector('#su-sidx').textContent.includes('3 / 9')")
    page.evaluate("() => { window.fetch = window.__fetch1; }")


ADMIN_JS = open(os.path.join(ROOT, 'bundled_plugins', 'administration', 'administration.js'), encoding='utf-8').read()


def test_administration_comptes_roles_instances_et_supervision(page):
    if not page.evaluate("!!window.StellioSuite._tabs.admin"):
        page.add_script_tag(content=ADMIN_JS)
    page.evaluate("""() => { window.__ov = { role: 'standalone', name: 'Atelier', supervisor: null, request: null, instances: [
          { id: 4, name: 'Garage', url: 'http://g', last_status: 'online', supervision: 'none' }, { id: 5, name: 'Cave', url: 'http://c', last_status: 'online', supervision: 'supervised' }] };
        window.__routes['GET /api/admin/overview'] = () => window.__ov;
        window.__routes['GET /api/admin/accounts'] = () => ({ owner: { id: 1, username: 'romain' }, guests: [{ id: 9, username: 'alice', team_role: 'operator' }], roles: ['user', 'operator', 'manager', 'admin'], locked: window.__ov.role === 'supervised', supervisor: 'Siège' });
        window.__routes['PUT /api/team/members/9/role'] = () => ({ ok: true });
        window.__routes['GET /api/admin/instances/5/status'] = () => ({ state: 'supervised', online: true, guests: [{ id: 3, username: 'bob', team_role: '' }], roles: ['user', 'operator', 'manager', 'admin'], keep_local: true });
        window.__routes['GET /api/admin/instances/4/status'] = () => ({ state: 'none' });
        window.__routes['POST /api/admin/instances/5/command'] = () => ({ ok: true });
        window.__routes['POST /api/admin/instances/4/supervise'] = (b) => { window.__ov.instances[0].supervision = 'pending'; return { ok: true, state: 'pending' }; };
        window.__routes['POST /api/admin/supervision/respond'] = (b) => { window.__ov.request = null; window.__ov.role = b.accept ? 'supervised' : 'standalone'; window.__ov.supervisor = { name: 'Siège', keep_local: b.keep_local }; return { ok: true }; };
        window.__calls.length = 0; }""")
    _ouvrir(page, 'admin'); page.wait_for_selector('[data-role="9"]')
    assert 'Instance autonome' in page.inner_text('#adm-banner') and 'alice' in page.inner_text('#adm-sub') and 'romain' in page.inner_text('#adm-sub')
    assert page.locator('#adm-subs [data-sub]').count() == 5
    page.select_option('[data-role="9"]', 'manager')
    page.wait_for_function("window.__calls.some(c => c.method === 'PUT' && c.url === '/api/team/members/9/role')")
    assert [c for c in page.evaluate("window.__calls") if c['method'] == 'PUT'][0]['body'] == {'role': 'manager'}
    page.click('[data-sub="instances"]'); page.wait_for_selector('[data-sup="4"]')
    assert page.locator('[data-manage="5"]').count() == 1 and page.locator('[data-release="5"]').count() == 1
    page.click('[data-manage="5"]'); page.wait_for_selector('[data-rrole="3"]')
    page.select_option('[data-rrole="3"]', 'admin')
    page.wait_for_function("window.__calls.some(c => c.url === '/api/admin/instances/5/command')")
    cmd = [c for c in page.evaluate("window.__calls") if c['url'] == '/api/admin/instances/5/command'][0]['body']
    assert cmd == {'op': 'guest_role', 'args': {'id': 3, 'role': 'admin'}}
    page.click('[data-sup="4"]'); page.wait_for_selector('[data-release="4"]')
    assert [c for c in page.evaluate("window.__calls") if c['url'] == '/api/admin/instances/4/supervise'][0]['body'] == {'keep_local': True}
    # côté instance visée : la demande s'affiche, l'acceptation verrouille les comptes
    page.evaluate("() => { window.__ov = { role: 'standalone', name: 'Cave', supervisor: null, request: { name: 'Siège', keep_local: true }, instances: [] }; }")
    page.click('[data-sub="accounts"]'); page.wait_for_selector('[data-adm="accept"]')
    assert 'Siège' in page.inner_text('#adm-banner')
    page.evaluate("() => { const p = document.getElementById('adm-req-popup'); if (p) p.remove(); }")   # la fenêtre de demande est testée à part
    page.click('[data-adm="accept"]'); page.wait_for_selector('[data-adm="leave"]')
    assert page.locator('[data-role="9"]:disabled').count() == 1 and 'Siège' in page.inner_text('#adm-banner')


def test_demande_de_supervision_en_fenetre_accepter_refuser(page):
    if not page.evaluate("!!window.StellioSuite._tabs.admin"):
        page.add_script_tag(content=ADMIN_JS)
    page.evaluate("""() => { document.querySelectorAll('#adm-req-popup').forEach(e => e.remove());
        window.__ov = { role: 'standalone', name: 'Cave', supervisor: null, request: null, instances: [] };
        window.__routes['GET /api/admin/overview'] = () => window.__ov;
        window.__routes['POST /api/admin/supervision/respond'] = (b) => { window.__ov.request = null; window.__ov.role = b.accept ? 'supervised' : 'standalone'; return { ok: true }; };
        window.__calls.length = 0; }""")
    page.wait_for_timeout(1800)                                                                            # une instance sans demande : aucune fenêtre
    assert page.locator('#adm-req-popup').count() == 0
    page.evaluate("() => { window.__ov.request = { name: 'Siège', keep_local: true }; window.dispatchEvent(new Event('focus')); }")
    page.wait_for_selector('#adm-req-popup')
    assert 'Siège' in page.inner_text('#adm-req-popup') and page.locator('#adm-req-popup [data-pop]').count() == 2
    page.click('#adm-req-popup [data-pop="refuse"]'); page.wait_for_selector('#adm-req-popup', state='detached')
    assert [c for c in page.evaluate("window.__calls") if c['url'] == '/api/admin/supervision/respond'][-1]['body'] == {'accept': False, 'keep_local': True}
    page.evaluate("() => { window.__ov.request = { name: 'Siège', keep_local: true }; window.dispatchEvent(new Event('focus')); }")
    page.wait_for_selector('#adm-req-popup'); page.uncheck('#adm-pop-keep'); page.click('#adm-req-popup [data-pop="accept"]')
    page.wait_for_selector('#adm-req-popup', state='detached')
    assert [c for c in page.evaluate("window.__calls") if c['url'] == '/api/admin/supervision/respond'][-1]['body'] == {'accept': True, 'keep_local': False}


def test_administration_badge_en_attente_passe_a_supervise_sans_changer_d_onglet(page):
    if not page.evaluate("!!window.StellioSuite._tabs.admin"):
        page.add_script_tag(content=ADMIN_JS)
    page.evaluate("""() => { document.querySelectorAll('#adm-req-popup').forEach(e => e.remove());
        window.__ov = { role: 'primary', name: 'Siège', supervisor: null, request: null, instances: [{ id: 7, name: 'Windows', url: 'http://w', last_status: 'online', supervision: 'pending' }] };
        window.__routes['GET /api/admin/overview'] = () => window.__ov;
        window.__routes['GET /api/admin/accounts'] = () => ({ owner: { id: 1, username: 'romain' }, guests: [], roles: [], locked: false });
        window.__routes['GET /api/admin/instances/7/status'] = () => ({ state: window.__ov.instances[0].supervision === 'pending' ? 'pending' : 'supervised', online: true, guests: [], roles: [] });
        window.__calls.length = 0; }""")
    _ouvrir(page, 'admin'); page.click('[data-sub="instances"]'); page.wait_for_selector('[data-release="7"]')
    assert 'attente' in page.inner_text('#adm-sub')
    page.evaluate("() => { window.__ov.instances[0].supervision = 'supervised'; }")
    page.wait_for_function("document.querySelector('#adm-sub') && document.querySelector('#adm-sub').textContent.includes('Supervisée')", timeout=9000)
    assert page.locator('[data-manage="7"]').count() == 1


def test_administration_equipes_ajout_de_comptes(page):
    if not page.evaluate("!!window.StellioSuite._tabs.admin"):
        page.add_script_tag(content=ADMIN_JS)
    page.evaluate("""() => { document.querySelectorAll('#adm-req-popup').forEach(e => e.remove());
        window.__ov = { role: 'standalone', name: 'Atelier', supervisor: null, request: null, instances: [] };
        window.__t = { roles: ['user', 'operator', 'manager', 'admin'], members: [{ id: 9, username: 'alice', team_role: '' }, { id: 10, username: 'bob', team_role: '' }], workspaces: [{ id: 1, name: 'Atelier A', members: [{ user_id: 9, role: 'user' }], items: [] }], permissions: [] };
        window.__routes['GET /api/admin/overview'] = () => window.__ov;
        window.__routes['GET /api/admin/accounts'] = () => ({ owner: { id: 1, username: 'romain' }, guests: [], roles: [], locked: false });
        window.__routes['GET /api/team'] = () => window.__t;
        window.__routes['POST /api/team/workspaces/1/members'] = (b) => { const m = window.__t.workspaces[0].members.find(x => x.user_id === b.user_id); if (m) m.role = b.role; else window.__t.workspaces[0].members.push({ user_id: b.user_id, role: b.role }); return { ok: true }; };
        window.__routes['DELETE /api/team/workspaces/1/members/9'] = () => { window.__t.workspaces[0].members = window.__t.workspaces[0].members.filter(x => x.user_id !== 9); return { ok: true }; };
        window.__routes['POST /api/team/workspaces'] = (b) => { window.__t.workspaces.push({ id: 2, name: b.name, members: [], items: [] }); return { ok: true, id: 2 }; };
        window.__calls.length = 0; }""")
    _ouvrir(page, 'admin'); page.click('[data-sub="teams"]'); page.wait_for_selector('[data-madd="1"]')
    assert 'Atelier A' in page.inner_text('#adm-sub') and 'alice' in page.inner_text('#adm-sub')
    page.select_option('[data-madd-role="1"]', 'operator'); page.click('[data-madd="1"]')
    page.wait_for_function("document.querySelector('#adm-sub').textContent.includes('bob')")
    assert [c for c in page.evaluate("window.__calls") if c['url'] == '/api/team/workspaces/1/members'][-1]['body'] == {'user_id': 10, 'role': 'operator'}
    page.select_option('[data-mrole="1:10"]', 'manager')
    page.wait_for_function("window.__calls.filter(c => c.url === '/api/team/workspaces/1/members').length === 2")
    assert [c for c in page.evaluate("window.__calls") if c['url'] == '/api/team/workspaces/1/members'][-1]['body'] == {'user_id': 10, 'role': 'manager'}
    page.click('[data-mdel="1:9"]'); page.wait_for_function("!document.querySelector('#adm-sub').textContent.includes('alice') || document.querySelector('[data-madd-user=\"1\"]')")
    page.fill('#adm-tn', 'Atelier B'); page.click('#adm-tadd'); page.wait_for_function("document.querySelector('#adm-sub').textContent.includes('Atelier B')")


SCRIPT_JS = open(os.path.join(ROOT, 'interface', 'script.js'), encoding='utf-8').read()
_A0 = SCRIPT_JS.index('// Paramètres : une section de premier niveau')
ACCORD_JS = SCRIPT_JS[_A0:SCRIPT_JS.index('window.toggleAccord = toggleAccord;', _A0)] + 'window.toggleAccord = toggleAccord;'


def test_parametres_section_ouverte_en_fenetre(page):
    page.evaluate("""(js) => { document.getElementById('host').innerHTML = `<div id="page-settings" class="page active"><div class="settings-grid"><div class="settings-col">
        <div class="accord-section" id="s1"><div class="accord-header" onclick="toggleAccord(this)"><span>Apparence</span><i class="fa-solid fa-chevron-down accord-arrow"></i></div>
          <div class="accord-body"><div class="settings-row"><label>Thème</label><select id="t1"><option>a</option></select></div>
            <div class="accord-section" id="n1"><div class="accord-header" onclick="toggleAccord(this)"><span>Sous-menu</span><i class="fa-solid fa-chevron-down accord-arrow"></i></div><div class="accord-body"><p id="n1p">dedans</p></div></div></div></div>
        <div class="accord-section" id="s2"><div class="accord-header" onclick="toggleAccord(this)"><span>Réseau</span><i class="fa-solid fa-chevron-down accord-arrow"></i></div><div class="accord-body"><p>réseau</p></div></div>
      </div></div></div>`; window.loadAutoBackupSettings = () => {}; window.loadBackupList = () => {}; (0, eval)(js); }""", ACCORD_JS)
    page.click('#s1 > .accord-header')
    assert page.evaluate("getComputedStyle(document.querySelector('#s1 > .accord-body')).transitionDuration") in ('0s', '0s, 0s')       # aucune animation d'ouverture
    assert page.locator('#accord-backdrop').count() == 1 and page.evaluate("document.getElementById('s1').classList.contains('accord-popup')")
    box = page.evaluate("(() => { const r = document.getElementById('s1').getBoundingClientRect(); return [r.left, r.right, r.top, r.bottom, innerWidth, innerHeight]; })()")
    assert box[0] > 0 and box[1] < box[4] and abs((box[0] + box[1]) / 2 - box[4] / 2) < 2 and abs((box[2] + box[3]) / 2 - box[5] / 2) < 2        # centrée
    assert page.is_visible('#t1')                                                                                # réglages visibles d'emblée
    page.click('#n1 > .accord-header'); assert page.is_visible('#n1p')                                           # un sous-menu reste un dépliant, dans la fenêtre
    assert page.locator('#accord-backdrop').count() == 1
    page.keyboard.press('Escape')
    assert page.locator('#accord-backdrop').count() == 0 and not page.evaluate("document.getElementById('s1').classList.contains('open')")
    page.click('#s1 > .accord-header'); page.click('#accord-backdrop', position={'x': 5, 'y': 5})
    assert page.locator('#accord-backdrop').count() == 0
    page.click('#s2 > .accord-header'); page.click('#s2 > .accord-header')                                      # l'en-tête referme aussi
    assert page.locator('#accord-backdrop').count() == 0
    page.click('#s1 > .accord-header'); page.evaluate("document.getElementById('s2').querySelector('.accord-header').click()")
    assert page.evaluate("[document.getElementById('s1').classList.contains('open'), document.getElementById('s2').classList.contains('open')]") == [False, True]
    page.screenshot(path='/tmp/rn/popup-reglages.png'); page.keyboard.press('Escape')
    page.evaluate("document.getElementById('host').innerHTML = ''")


def test_menu_administration_visible_seulement_si_des_instances_sont_reliees(page):
    page.evaluate("""() => { window.__ov = { role: 'standalone', instances: [], request: null };
        window.__routes['GET /api/plugins/features'] = () => ({ features: { administration: true } });
        window.__routes['GET /api/admin/overview'] = () => window.__ov; }""")
    net = "document.documentElement.dataset.netOk || ''"
    page.evaluate("window.StellioSuite._applyHostFeatures()"); page.wait_for_function("window.__calls.some(c => c.url === '/api/admin/overview')")
    page.wait_for_timeout(100); assert page.evaluate(net) == ''                                             # instance seule : pas de menu
    page.evaluate("() => { window.__ov.instances = [{ id: 1 }]; window.StellioSuite._applyHostFeatures(); }"); page.wait_for_function(f"{net} === '1'")   # une instance appairée
    page.evaluate("() => { window.__ov = { role: 'standalone', instances: [], request: { name: 'Siège' } }; window.StellioSuite._applyHostFeatures(); }")
    page.wait_for_timeout(150); assert page.evaluate(net) == '1'                                            # demande de supervision reçue
    page.evaluate("() => { window.__ov = { role: 'supervised', instances: [], request: null }; window.StellioSuite._applyHostFeatures(); }"); page.wait_for_function(f"{net} === ''")   # instance supervisée : menu caché
    page.evaluate("() => { window.__ov = { role: 'standalone', instances: [], request: null }; window.StellioSuite._applyHostFeatures(); }"); page.wait_for_function(f"{net} === ''")


def test_page_toutes_les_notifications_filtres_et_actions(page):
    page.evaluate("""() => { window.__n = [
        { id: 1, type: 'low_stock', title: 'Stock filament faible', message: 'PLA noir — 80g restants', link_page: 'spoolman', is_read: 0, created_at: '2026-11-20 10:00:00', category: 'filament_low', source: 'Spoolman' },
        { id: 2, type: 'low_stock', title: 'Filament à commander', message: 'PETG gris — 120 g', link_page: 'spoolman', is_read: 1, created_at: '2026-11-19 10:00:00', category: 'restock', source: 'TigerTag' },
        { id: 3, type: 'print_finished', title: 'Impression terminée', message: 'Bolt', link_page: 'printers', is_read: 0, created_at: '2026-11-18 10:00:00', category: 'print' }];
      window.__routes['GET /api/notifications/all'] = (b, u) => { const q = new URLSearchParams(u.split('?')[1] || ''); let r = window.__n.filter(n => (!q.get('category') || n.category === q.get('category')) && (q.get('state') !== 'unread' || !n.is_read));
        const counts = { filament_low: 0, restock: 0, parts: 0, print: 0, maintenance: 0, planning: 0, update: 0, other: 0 }; window.__n.forEach(n => counts[n.category]++);
        return { notifications: r, total: r.length, all: window.__n.length, unread: window.__n.filter(n => !n.is_read).length, counts, sources: { Spoolman: 1, TigerTag: 1, Stellio: 1 } }; };
      window.__routes['DELETE /api/notifications/2'] = () => { window.__n = window.__n.filter(n => n.id !== 2); return { message: 'ok' }; };
      window.__calls.length = 0; }""")
    _ouvrir(page, 'notifications'); page.wait_for_selector('.ntf-row')
    assert page.locator('.ntf-row').count() == 3 and page.locator('.ntf-row.unread').count() == 2
    assert page.locator('.ntf-chip').count() == 5                                                    # Toutes, Non lues + 3 rubriques non vides
    page.click('[data-ntf="filament_low"]'); page.wait_for_function("document.querySelectorAll('.ntf-row').length === 1")
    assert 'PLA noir' in page.inner_text('.ntf-list')
    page.click('[data-ntf="restock"]'); page.wait_for_function("document.querySelectorAll('.ntf-row').length === 1 && document.querySelector('.ntf-list').textContent.includes('PETG')")
    assert page.locator('.ntf-src').count() == 1 and page.inner_text('.ntf-src') == 'TigerTag' and page.locator('#su-nsrc option').count() == 4   # source en pastille et filtre
    page.click('[data-ndel="2"]'); page.wait_for_function("window.__calls.some(c => c.method === 'DELETE' && c.url === '/api/notifications/2')")


def test_tout_voir_ouvre_notifications_meme_si_une_autre_entree_du_menu_est_active(page):
    page.evaluate("""() => { window.__routes['GET /api/notifications/all'] = () => ({ notifications: [], total: 0, all: 0, unread: 0, counts: {} });
        document.body.insertAdjacentHTML('beforeend', '<button class="nav-btn active" data-page="suite" data-suite-tab="organize" id="nv-org"></button>');
        document.getElementById('nv-org').onclick = () => window.StellioSuite.onShow(); }""")
    page.evaluate("window.StellioSuite.open('notifications')")
    page.wait_for_selector('#su-body .ntf-chips')                                      # et non la page Organisation, dont l'entrée de menu est active


def test_page_collections_style_filament_depliage_et_suppression(page):
    page.evaluate("""() => { window.__col = [{ id: 1, name: 'Boîtes', color: '#4ea1d3', count: 2, pieces: 3, preview: [] }, { id: 2, name: 'Vide', color: '', count: 0, pieces: 0, preview: [] }];
      window.__opened = []; window.showConfirmDialog = async () => true;
      window.openFileInfoModal = (p) => window.__opened.push(p);
      window.__routes['GET /api/collections'] = () => ({ collections: window.__col, colors: [] });
      window.__routes['GET /api/collections/1'] = () => ({ id: 1, name: 'Boîtes', description: 'Rangement', files: [{ path: '/m/Bolt.stl', name: 'Bolt.stl', quantity: 2 }, { path: '/m/Gone.stl', name: 'Gone.stl', quantity: 1, missing: true }] });
      window.__routes['GET /api/collections/2'] = () => ({ id: 2, name: 'Vide', files: [] });
      window.__routes['POST /api/collections/save'] = (b) => { window.__col.push({ id: 3, name: b.name, color: '', count: 0, pieces: 0, preview: [] }); return { ok: true, id: 3 }; };
      window.__routes['POST /api/collections/delete'] = (b) => { window.__col = window.__col.filter(c => c.id !== b.id); return { success: true }; }; window.__calls.length = 0; }""")
    _ouvrir(page, 'collections'); page.wait_for_selector('.inv-section .source-banner-collection')
    assert page.evaluate("document.getElementById('su-body').classList.contains('su-plain')") and page.locator('.col-new #su-cadd').count() == 1 and page.locator('.col-new .inv-section').count() == 0   # formulaire dans son cadre, collections hors du cadre
    assert page.locator('.inv-section').count() == 2 and page.locator('.inv-section.inv-collapsed').count() == 2 and '2 fichiers' in page.inner_text('#su-body')
    page.click('[data-cid="1"] .source-banner-collection'); page.wait_for_selector('.col-file')           # clic sur la bannière ou le chevron
    assert page.locator('.col-file').count() == 2 and '×2' in page.inner_text('.col-files') and page.locator('.col-file.missing').count() == 1
    page.click('.col-file >> nth=0'); assert page.evaluate("window.__opened") == ['/m/Bolt.stl']
    page.click('[data-cid="1"] .inv-toggle'); assert page.locator('[data-cid="1"].inv-collapsed').count() == 1        # un seul basculement (pas d'écouteur en double)
    page.click('[data-cid="2"] .inv-toggle'); page.wait_for_function("document.querySelector('[data-cbody=\"2\"]').textContent.includes('vide')")
    page.fill('#su-cname', 'Nouvelle'); page.click('#su-cadd'); page.wait_for_function("document.querySelectorAll('.inv-section').length === 3")
    assert page.locator('.inv-section:not(.inv-collapsed)').count() == 1                                            # la section ouverte le reste
    page.click('[data-cdel="2"]'); page.wait_for_function("document.querySelectorAll('.inv-section').length === 2")
    assert [c['body'] for c in page.evaluate("window.__calls") if c['url'] == '/api/collections/delete'] == [{'id': 2}]


def test_plugins_signature_audit_restrictions_et_confirmation_du_risque(page):
    page.evaluate("""() => {
      window.__calls.length = 0; const R = window.__routes; window.confirm = () => true;
      R['GET /api/plugins'] = { sandbox: { platform: 'windows', enforced: false, filesystem: false, network: false, reason: 'platform' }, trusted_keys: [],
        plugins: [{ id: 'a', name: 'Alpha', version: '1.0', enabled: false, origin: 'community', permissions: ['events'], security: { signature: 'valid', audit: 'warn' } },
                  { id: 'b', name: 'Beta', version: '1.0', enabled: false, origin: 'community', permissions: ['events'], security: { signature: 'unsigned', audit: 'danger' } }] };
      R['POST /api/plugins/catalog'] = { updates: 0, count: 1, plugins: [{ id: 'c', name: 'Gamma', version: '1.0', description: 'x', official: false, installed_version: null, update_available: false, permissions: ['events'], signature_status: 'invalid' }] };
      let n = 0;
      R['POST /api/plugins/catalog/install'] = (body) => body.accept_risk ? { ok: true, note: 'Installé' } : { __status: 400, error: 'Audit refuse', code: 'audit_blocked', audit: { findings: [{ blocking: true, file: 'main.py', line: 3, detail: 'import subprocess' }] } };
    }""")
    page.evaluate("document.getElementById('plugins-root') && document.getElementById('plugins-root').remove(); window.StellioSuite.open('plugins')")
    page.wait_for_selector('#plugins-root .su-store-card')
    txt = page.inner_text('#plugins-root')
    assert 'Aucune restriction du noyau' not in txt                                                      # plus d'avertissement hors Linux (1.1.9)
    assert 'Aucune clé de confiance configurée' in txt
    alpha = page.inner_text('#plugins-root .su-plugin[data-pid="a"]')
    beta = page.inner_text('#plugins-root .su-plugin[data-pid="b"]')
    assert 'Signé' in alpha and 'Audit : points à lire' in alpha and 'Non signé' in beta and 'code dangereux (risque accepté)' in beta
    assert 'Signature invalide' in page.inner_text('#plugins-root .su-store-card')
    page.click('#plugins-root [data-cat="c"]')
    page.wait_for_function("window.__calls.filter(c => c.url === '/api/plugins/catalog/install').length === 2")
    bodies = [c['body'] for c in page.evaluate("window.__calls") if c['url'] == '/api/plugins/catalog/install']
    assert bodies[0] == {'id': 'c'} and bodies[1] == {'id': 'c', 'accept_risk': True}                    # le risque n'est accepté qu'après confirmation
    page.evaluate("document.getElementById('plugins-root').remove()")
    page.evaluate("window.__routes['GET /api/plugins'] = { sandbox: { platform: 'linux', enforced: true, filesystem: true, network: true, reason: 'ok', landlock_abi: 7 }, trusted_keys: ['abc'], plugins: [] }")
    page.evaluate("window.StellioSuite.open('plugins')")
    page.wait_for_selector('#plugins-root .su-notice')
    t2 = page.inner_text('#plugins-root .su-notice')
    assert 'le noyau restreint chaque plugin' in t2 and 'pas limité à certains sites' in t2
    page.evaluate("document.getElementById('plugins-root').remove()")
    page.evaluate("window.__routes['GET /api/plugins'] = { sandbox: { platform: 'windows', enforced: false, filesystem: false, network: false, reason: 'unsupported' }, trusted_keys: [], plugins: [], builtin: [], restart_required: false }")
    page.evaluate("window.StellioSuite.open('plugins')"); page.wait_for_selector('#plugins-root .su-card')
    assert page.locator('#plugins-root .su-notice').count() == 0                                       # 1.1.9 : plus d'avertissement « aucune restriction du noyau »
    assert 'Aucune restriction du noyau' not in page.inner_text('#plugins-root')
    page.evaluate("document.getElementById('plugins-root').remove()")
