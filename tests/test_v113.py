"""v1.1.3 : versions de modèles, collections, tarif heures creuses/pleines, Obico, Duet/Repetier, causes d'échec."""
import datetime, importlib.util, json, pathlib, re
import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
LANGS = ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja')


def _mod(name):
    spec = importlib.util.spec_from_file_location(name + '_v113_test', __import__('conftest').mod_path(name))
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    except ImportError as e:
        pytest.skip(f'{name} : dépendance manquante ({e})')
    return m


# ── tarif ────────────────────────────────────────────────────────────────────
def _cfg(**kw):
    et = _mod('energy_tariff')
    s = {'tariff_enabled': True, 'tariff_peak_price': 0.25, 'tariff_offpeak_price': 0.15, 'tariff_offpeak_ranges': ['22:00-06:00'], 'print_cost_elec_price': 0.2}
    s.update(kw)
    return et, et.get_config(s)


def test_tariff_ranges_cross_midnight_and_weekend():
    et, cfg = _cfg()
    assert et.parse_ranges(['22:00-06:00', 'nope', '10:00-10:00']) == [(1320, 360)]
    d = datetime.datetime
    assert et.is_offpeak(d(2026, 11, 16, 23, 0), cfg) and et.is_offpeak(d(2026, 11, 17, 5, 59), cfg)
    assert not et.is_offpeak(d(2026, 11, 16, 12, 0), cfg)
    et, cfg = _cfg(tariff_weekend_offpeak=True)
    assert et.is_offpeak(d(2026, 11, 14, 12, 0), cfg)          # samedi


def test_tariff_disabled_falls_back_to_flat_price():
    et, cfg = _cfg(tariff_enabled=False)
    assert not cfg['enabled']
    cost, share = et.cost_for_session(1_700_000_000, 3600, 1.0, cfg)
    assert cost == pytest.approx(0.2) and share == 0.0


def test_tariff_cost_splits_between_peak_and_offpeak():
    et, cfg = _cfg()
    start = datetime.datetime(2026, 11, 16, 21, 0).timestamp()      # 21h -> 23h : 1 h pleine + 1 h creuse
    cost, share = et.cost_for_session(start, 7200, 2.0, cfg)
    assert share == pytest.approx(0.5, abs=0.02)
    assert cost == pytest.approx(1.0 * 0.25 + 1.0 * 0.15, abs=0.01)


def test_tariff_advice_proposes_next_offpeak_slot():
    et, cfg = _cfg()
    now = datetime.datetime(2026, 11, 16, 12, 0).timestamp()
    a = et.advice(3 * 3600, 200, now, cfg)
    assert a['best_start'] > now and a['saving'] > 0 and a['wait_minutes'] == 600
    assert et.next_offpeak_start(datetime.datetime(2026, 11, 16, 23, 0).timestamp(), cfg) == datetime.datetime(2026, 11, 16, 23, 0).timestamp()


# ── causes d'échec ───────────────────────────────────────────────────────────
def _rows():
    out = []
    for i in range(6):
        out.append({'result': 'failed' if i < 4 else 'success', 'failure_reason': 'adhérence' if i < 3 else '', 'filament_material': 'PETG',
                    'printer_id': 1, 'slicer_profile_name': 'p', 'file_ext': '3mf', 'file_name': 'a.3mf', 'sent_at': '2026-11-%02d 23:10:00' % (i + 1)})
    for i in range(6):
        out.append({'result': 'success', 'failure_reason': '', 'filament_material': 'PLA', 'printer_id': 1, 'slicer_profile_name': 'p',
                    'file_ext': '3mf', 'file_name': 'b.3mf', 'sent_at': '2026-11-%02d 10:00:00' % (i + 1)})
    return out


def test_failure_stats_compute_rates_and_leads():
    fs = _mod('failure_stats')
    d = fs.compute(_rows(), {1: 'Ender'})
    assert d['total'] == 12 and d['failed'] == 4 and d['success'] == 8
    mat = {g['key']: g for g in d['by_material']}
    assert mat['PETG']['fail_rate'] > mat['PLA']['fail_rate'] == 0
    assert d['by_reason'][0]['key'] == 'adhérence' and d['by_reason'][0]['count'] == 3
    assert any(l['dimension'] == 'material' and l['key'] == 'PETG' for l in d['leads'])
    assert d['worst_files'][0]['file'] == 'a.3mf'


def test_failure_stats_empty_and_small_groups():
    fs = _mod('failure_stats')
    assert fs.compute([])['total'] == 0
    d = fs.compute(_rows()[:2])
    assert all(g['fail_rate'] is None for g in d['by_material'])    # sous le seuil MIN_GROUP


# ── Obico ────────────────────────────────────────────────────────────────────
def test_obico_clean_url_and_parsers():
    ob = _mod('obico')
    assert ob.clean_url('obico.local:3334/') == 'http://obico.local:3334'
    assert ob.clean_url('https://x.io/') == 'https://x.io'
    assert ob.clean_url('ftp://x') == '' and ob.clean_url('a b') == '' and ob.clean_url('') == ''
    payload = {'results': [
        {'id': 1, 'name': 'Ender', 'current_print': {'id': 9, 'filename': 'a.gcode', 'alerted_at': '2026-11-16T10:00:00Z'}},
        {'id': 2, 'name': 'Prusa', 'current_print': {'id': 10, 'alerted_at': '2026-11-16T10:00:00Z', 'alert_muted_at': '2026-11-16T10:01:00Z'}},
        {'id': 3, 'name': 'Idle', 'current_print': None}, 'junk']}
    ps = ob.parse_printers(payload)
    assert [p['name'] for p in ps] == ['Ender', 'Prusa', 'Idle']
    assert ps[0]['alert'] and not ps[1]['alert'] and not ps[2]['printing']
    seen = set()
    assert len(ob.new_alerts(ps, seen)) == 1 and ob.new_alerts(ps, seen) == []     # une alerte n'est annoncée qu'une fois
    assert ob.parse_printers([]) == [] and ob.parse_printers(None) == []


# ── Duet / Repetier ──────────────────────────────────────────────────────────
def test_duet_normalize_printing_and_garbage():
    pe = _mod('printers_extra')
    model = {'state': {'status': 'processing'}, 'job': {'file': {'fileName': '0:/gcodes/a.gcode', 'size': 1000}, 'filePosition': 250, 'duration': 300, 'timesLeft': {'file': 900}},
             'heat': {'bedHeaters': [0], 'heaters': [{'current': 60.04, 'active': 60}, {'current': 215.5, 'active': 215}]},
             'tools': [{'heaters': [1]}]}
    r = pe.duet_normalize(model)
    assert r['status'] == 'printing' and r['file'] == 'a.gcode' and r['progress'] == 25.0
    assert r['time']['remaining'] == 900 and r['temps']['bed']['current'] == pytest.approx(60.0, abs=0.1)
    assert r['temps']['extruder']['current'] == pytest.approx(215.5, abs=0.1)
    assert pe.duet_normalize(None)['status'] == 'unknown'
    assert pe.duet_normalize({'state': {'status': 'idle'}})['status'] in ('idle', 'standby', 'ready')


def test_repetier_helpers():
    pe = _mod('printers_extra')
    ps = [{'slug': 'a', 'name': 'Alpha', 'online': False}, {'slug': 'b', 'name': 'Beta', 'online': True}]
    assert pe.repetier_pick_slug(ps) == 'b' and pe.repetier_pick_slug(ps, 'alpha') == 'a' and pe.repetier_pick_slug(ps, 'zzz') is None
    r = pe.repetier_normalize({'extruder': [{'tempRead': 200.2, 'tempSet': 200}], 'heatedBed': {'tempRead': 60, 'tempSet': 60}}, {'job': 'x.gcode', 'done': 40})
    assert r['status'] == 'printing' and r['file'] == 'x.gcode'
    assert pe.repetier_normalize({}, {})['status'] in ('idle', 'unknown', 'ready')


# ── branchement ──────────────────────────────────────────────────────────────
def test_v113_wiring_backend():
    main = (ROOT / 'main.py').read_text(encoding='utf-8')
    assert 'CURRENT_VERSION = "1.1.7"' in main and "@app.route('/v113.js')" in main
    assert "('klipper','octoprint','prusalink','duet','repetier')" in main.replace(' ', '')
    for m in ('model_versions', 'printers_extra', 'failure_stats', 'collections_sets'):
        assert f'{m}.init(globals())' in main


def test_v113_wiring_frontend():
    html = (ROOT / 'interface/index.html').read_text(encoding='utf-8')
    js = (ROOT / 'interface/script.js').read_text(encoding='utf-8')
    v = (ROOT / 'interface/v113.js').read_text(encoding='utf-8')
    sw = (ROOT / 'interface/sw.js').read_text(encoding='utf-8')
    assert '<script src="v113.js">' in html and "'/v113.js'" in sw
    for bid in ('ctx-versions-btn', 'ctx-collection-btn'):
        assert f'id="{bid}"' in html
    for fn in ('active', 'filterFiles', 'chipsHtml', 'onStats', 'onSettings', 'openVersions', 'openAddToCollection'):
        assert f'window.StellioV113' in js and re.search(r'\b%s\b' % fn, v), fn
    assert 'value="duet"' in html and 'value="repetier"' in html
    for fn in ('active', 'filterFiles', 'chipsHtml', 'onStats', 'onSettings', 'openVersions', 'openAddToCollection', 'openCollections', 'toggleCollection'):
        assert re.search(r'window\.StellioV113 = \{[^}]*\b%s\b' % fn, v), fn


def test_v113_texts_complete_in_8_languages():
    v = (ROOT / 'interface/v113.js').read_text(encoding='utf-8')
    txt = json.loads(re.search(r'const TXT = (\{.*?\});\n', v, re.S).group(1))
    assert set(txt) == set(LANGS)
    keys = set(txt['fr'])
    for l in LANGS:
        assert set(txt[l]) == keys and all(txt[l][k] for k in keys), l
        for k in keys:       # mêmes variables {x} dans toutes les langues
            assert sorted(re.findall(r'\{\w+\}', txt[l][k])) == sorted(re.findall(r'\{\w+\}', txt['fr'][k])), (l, k)
    used = set(re.findall(r"\bt\('(\w+)'", v)) | set(re.findall(r"\bt\(c\.\w+ \? '(\w+)'", v))
    assert used <= keys, used - keys


def test_v113_printer_i18n_keys_in_8_languages():
    for l in LANGS:
        d = json.loads((ROOT / 'languages' / f'{l}.json').read_text(encoding='utf-8'))
        for k in ('printers.duet_hint', 'printers.repetier_hint', 'printers.repetier_slug', 'printers.port_generic', 'v113.versions_action', 'v113.collection_action'):
            assert d.get(k), (l, k)


# ── routes de bout en bout (instance de test, vraie base, vraie source) ──────
def _csrf(c):
    c.get('/api/auth/me')
    ck = c.get_cookie('stellio_csrf')
    return {'X-CSRF-Token': ck.value if ck else ''}


@pytest.fixture(scope='module')
def v113_client(stellio_app, tmp_path_factory):
    c = stellio_app.test_client()
    user = {'username': 'v113user', 'password': 'abcd1234', 'security_question_key': 'custom',
            'security_question_custom': 'Quel est le nom de mon premier test ?', 'security_answer': 'reponse'}
    r = c.post('/api/auth/register', json=user)
    if r.status_code != 200:                               # un compte existe déjà (autre module de test) : connexion avec ce compte
        r = c.post('/api/auth/login', json={'username': 'testeur', 'password': 'abcd1234'})
    assert r.status_code == 200, r.get_data()
    folder = tmp_path_factory.mktemp('v113src')
    (folder / 'a.stl').write_bytes(b'solid a\nendsolid a\n')
    (folder / 'b.stl').write_bytes(b'solid b\nendsolid b\n')
    r = c.post('/api/sources', json={'name': 'v113', 'type': 'folder', 'path': str(folder)}, headers=_csrf(c))
    assert r.status_code == 200, r.get_data()
    return c, folder


def test_v113_versions_flow(v113_client):
    c, folder = v113_client
    h = _csrf(c)
    p = str(folder / 'a.stl').replace('\\', '/')
    assert c.get('/api/versions?path=' + p).get_json()['versions'] == []
    r = c.post('/api/versions/save', json={'path': p, 'note': 'v1'}, headers=h)
    assert r.status_code == 200 and r.get_json()['version']['version'] == 1
    assert c.post('/api/versions/save', json={'path': p}, headers=h).status_code == 409        # inchangé
    (folder / 'a.stl').write_bytes(b'solid a\n  facet normal 0 0 1\nendsolid a\n')
    vs = c.get('/api/versions?path=' + p).get_json()['versions']
    assert len(vs) == 1 and not vs[0]['is_current']
    cmp = c.get(f'/api/versions/compare?path={p}&a={vs[0]["id"]}&b=0').get_json()
    assert cmp['diff']['identical'] is False and cmp['diff']['size'] > 0
    assert c.get(f'/api/versions/{vs[0]["id"]}/download').data == b'solid a\nendsolid a\n'
    r = c.post('/api/versions/restore', json={'id': vs[0]['id']}, headers=h)
    assert r.status_code == 200
    assert (folder / 'a.stl').read_bytes() == b'solid a\nendsolid a\n'
    assert len(c.get('/api/versions?path=' + p).get_json()['versions']) == 2            # l'état d'avant la restauration est sauvegardé
    assert c.get('/api/versions?path=/etc/passwd').status_code in (400, 403)            # hors des sources


def test_v113_collections_flow(v113_client):
    c, folder = v113_client
    h = _csrf(c)
    pa, pb = (str(folder / n).replace('\\', '/') for n in ('a.stl', 'b.stl'))
    cid = c.post('/api/collections/save', json={'name': 'Échecs', 'description': 'jeu'}, headers=h).get_json()['id']
    assert c.post('/api/collections/save', json={'name': 'échecs'}, headers=h).status_code == 409   # nom déjà pris (sans tenir compte de la casse)
    r = c.post('/api/collections/add-files', json={'id': cid, 'paths': [pa, pb, pa, '/etc/passwd']}, headers=h).get_json()
    assert r['added'] == 2 and r['skipped'] == 2
    assert c.post('/api/collections/quantity', json={'id': cid, 'path': pa, 'quantity': 4}, headers=h).get_json()['quantity'] == 4
    d = c.get(f'/api/collections/{cid}').get_json()
    assert d['pieces'] == 5 and len(d['files']) == 2 and not any(f['missing'] for f in d['files'])
    assert [x['name'] for x in c.get('/api/collections/of-file?path=' + pa).get_json()['collections']] == ['Échecs']
    q = c.post('/api/collections/queue', json={'id': cid}, headers=h).get_json()
    assert q['added'] == 2 and q['already'] == 0
    q = c.post('/api/collections/queue', json={'id': cid}, headers=h).get_json()
    assert q['added'] == 0 and q['already'] == 2                                         # pas de doublon dans la file
    assert c.post('/api/collections/remove-file', json={'id': cid, 'path': pb}, headers=h).status_code == 200
    assert c.get('/api/collections').get_json()['collections'][0]['count'] == 1
    assert c.post('/api/collections/delete', json={'id': cid}, headers=h).status_code == 200
    assert c.get(f'/api/collections/{cid}').status_code == 404


def test_v113_tariff_failure_obico_routes(v113_client):
    c, _ = v113_client
    h = _csrf(c)
    assert c.post('/api/tariff', json={'enabled': True, 'peak_price': 0.25, 'offpeak_price': 0.15, 'ranges': ['25:99']}, headers=h).status_code == 400
    assert c.post('/api/tariff', json={'enabled': True, 'peak_price': 0.25}, headers=h).status_code == 400
    assert c.post('/api/tariff', json={'enabled': True, 'peak_price': 0.25, 'offpeak_price': 0.15, 'ranges': ['22:00-06:00']}, headers=h).status_code == 200
    g = c.get('/api/tariff').get_json()
    assert g['enabled'] and g['ranges'] == ['22:00-06:00'] and g['peak_price'] == 0.25
    a = c.get('/api/tariff/advice?duration_s=7200&watts=150').get_json()
    assert a['kwh'] == 0.3 and 'now_cost' in a
    assert c.get('/api/tariff/advice?duration_s=0&watts=1').status_code == 400
    assert c.get('/api/tariff/summary').get_json()['prints'] == 0
    assert c.get('/api/failure-stats?days=30').get_json()['total'] == 0
    o = c.get('/api/obico').get_json()
    assert o['enabled'] is False and o['has_token'] is False and 'token' not in o
    assert c.post('/api/obico', json={'enabled': True, 'url': 'http://obico.local'}, headers=h).status_code == 400   # jeton manquant
    assert c.post('/api/obico', json={'enabled': False, 'url': 'ftp://x'}, headers=h).status_code == 400


# ── imprimantes résine ────────────────────────────────────────────────
def test_resin_formlabs_normalize():
    rp = _mod('resin_printers')
    p = {'serial': 'Form4-abc', 'alias': 'Atelier', 'printer_status': {'status': 'PRINTING', 'current_temperature': 31.46,
         'current_print_run': {'name': 'Figurine', 'status': 'PRINTING', 'currently_printing_layer': 250, 'layer_count': 1000,
                               'elapsed_duration_ms': 1800000, 'estimated_duration_ms': 7200000, 'estimated_time_remaining_ms': 5400000}},
         'previous_print_run': {'name': 'Ancienne', 'elapsed_duration_ms': 60000, 'print_finished_at': '2026-11-15T10:00:00Z'}}
    r = rp.formlabs_normalize(p)
    assert r['status'] == 'printing' and r['file'] == 'Figurine' and r['progress'] == 25.0
    assert r['layers'] == {'current': 250, 'total': 1000} and r['time']['remaining'] == 5400 and r['temps']['chamber']['current'] == 31.5
    assert r['last_print']['filename'] == 'Ancienne'
    assert rp.formlabs_normalize({'printer_status': {'status': 'IDLE'}})['status'] == 'idle'
    assert rp.formlabs_normalize({'printer_status': {'status': 'OFFLINE'}})['status'] == 'offline'
    assert rp.formlabs_normalize({'printer_status': {'current_print_run': {'status': 'PAUSED'}}})['status'] == 'paused'
    assert rp.formlabs_normalize(None)['status'] == 'idle'                                  # tolère l'absence de données
    ps = [{'serial': 'A', 'alias': 'one'}, {'serial': 'B', 'alias': 'two'}]
    assert rp.formlabs_pick(ps)['serial'] == 'A' and rp.formlabs_pick(ps, 'TWO')['serial'] == 'B' and rp.formlabs_pick(ps, 'zz') is None
    assert rp.split_credentials('id:sec') == ('id', 'sec') and rp.split_credentials('nosecret') == ('', '')


def test_resin_photon_parse_status():
    rp = _mod('resin_printers')
    r = rp.photon_parse_status('getstatus,print,Boule.pwmx,12,3,0,end')
    assert r['status'] == 'printing' and r['file'] == 'Boule.pwmx' and r['progress'] == 0.0      # pas de progression inventée
    assert rp.photon_parse_status('getstatus,stop,end')['status'] == 'idle'
    assert rp.photon_parse_status('getstatus,pause,a.pwmb,end')['status'] == 'paused'
    assert rp.photon_parse_status('n importe quoi')['status'] == 'unknown'


def test_resin_wiring_everywhere():
    html = (ROOT / 'interface/index.html').read_text(encoding='utf-8')
    js = (ROOT / 'interface/script.js').read_text(encoding='utf-8')
    main = (ROOT / 'main.py').read_text(encoding='utf-8')
    for t in ('chitu_sdcp', 'anycubic_photon', 'formlabs'):
        assert f'<option value="{t}"' in html and t in js
    assert "_hosted('resin_printers')" in main and "('elegoo_sdcp', 'chitu_sdcp')" in main
    assert 'group-resin-beta' not in html and 'beta-badge' not in (ROOT / 'interface/style.css').read_text(encoding='utf-8') and '_betaBadgeHtml' not in js      # plus aucune mention « bêta » pour la résine
    assert js.count('_isResin(') >= 2                                                         # sélecteur de caméra, définition (+ maintenance)
    for l in LANGS:
        d = json.loads((ROOT / 'languages' / f'{l}.json').read_text(encoding='utf-8'))
        for k in ('printers.chitu_sdcp_model', 'printers.anycubic_photon_model',
                  'printers.formlabs_model', 'printers.chitu_hint', 'printers.photon_hint', 'printers.formlabs_hint', 'printers.note_elegoo_resin'):
            assert d.get(k), (l, k)
        for k in ('printers.elegoo_sdcp_model', 'printers.chitu_sdcp_model', 'printers.anycubic_photon_model', 'printers.formlabs_model', 'printers.usb_serial_model', 'printers.usb_hint', 'printers.note_elegoo_resin'):
            assert not re.search(r'b[êe]ta|beta|测试版|ベータ', d[k], re.I), (l, k)         # plus aucune mention « bêta » (résine, USB)
        doc = (ROOT / 'docs/wiki/src' / f'{l}.md').read_text(encoding='utf-8')
        assert '🧪' not in doc and not re.search(r'Formlabs\*\* \*\((b[êe]ta|beta|测试版|ベータ)\)', doc, re.I), l


def test_resin_inventory_flow(v113_client):
    c, _ = v113_client
    h = _csrf(c)
    assert c.post('/api/resin/save', json={'name': ''}, headers=h).status_code == 400
    assert c.post('/api/resin/save', json={'name': 'X', 'volume_ml': 500, 'remaining_ml': 900}, headers=h).get_json()['error'] == 'remaining_over_volume'
    assert c.post('/api/resin/save', json={'name': 'X', 'volume_ml': 'abc'}, headers=h).get_json()['error'] == 'bad_number'
    rid = c.post('/api/resin/save', json={'name': 'Grise', 'brand': 'Elegoo', 'kind': 'standard', 'volume_ml': 1000,
                                          'remaining_ml': 800, 'price': 25, 'color_hex': '#888888'}, headers=h).get_json()['id']
    d = c.get('/api/resin').get_json()
    assert any(b['id'] == rid for b in d['bottles']) and d['total_remaining_ml'] >= 800
    assert c.post('/api/resin/save', json={'id': rid, 'name': 'Grise v2', 'volume_ml': 1000, 'remaining_ml': 700}, headers=h).status_code == 200
    assert c.post('/api/resin/use', json={'id': rid, 'ml': 250}, headers=h).get_json()['remaining_ml'] == 450
    assert c.post('/api/resin/use', json={'id': rid, 'ml': 9999}, headers=h).get_json()['remaining_ml'] == 0     # jamais négatif
    assert c.post('/api/resin/save', json={'id': 999999, 'name': 'Z'}, headers=h).status_code == 404
    assert c.post('/api/resin/delete', json={'id': rid}, headers=h).status_code == 200
    assert not any(b['id'] == rid for b in c.get('/api/resin').get_json()['bottles'])


def test_resin_inventory_wiring_and_i18n():
    html = (ROOT / 'interface/index.html').read_text(encoding='utf-8')
    js = (ROOT / 'interface/script.js').read_text(encoding='utf-8')
    v = (ROOT / 'interface/v113.js').read_text(encoding='utf-8')
    assert 'id="page-resin"' in html and 'v13-resin-host' in html and 'data-i18n="nav.resin"' in html
    assert "page === 'resin'" in js and 'onResin' in v and re.search(r'window\.StellioV113 = \{ onResin', v)
    for l in LANGS:
        d = json.loads((ROOT / 'languages' / f'{l}.json').read_text(encoding='utf-8'))
        for k in ('nav.cat_filament', 'nav.spoolman', 'nav.resin'):
            assert d.get(k), (l, k)
    fr = json.loads((ROOT / 'languages/fr.json').read_text(encoding='utf-8'))
    assert fr['nav.cat_filament'] == 'Matières' and fr['nav.spoolman'] == 'Filament'


def test_resin_restock_flow(v113_client):
    c, _ = v113_client
    h = _csrf(c)
    assert c.post('/api/resin/restock/threshold', json={'ml': 300}, headers=h).get_json()['threshold_ml'] == 300
    assert c.post('/api/resin/restock/threshold', json={'ml': 'x'}, headers=h).status_code == 400
    a = c.post('/api/resin/save', json={'name': 'Rouge R', 'brand': 'Anycubic', 'volume_ml': 1000, 'remaining_ml': 250, 'color_hex': '#ff0000'}, headers=h).get_json()['id']
    b = c.post('/api/resin/save', json={'name': 'Bleue R', 'brand': 'Elegoo', 'volume_ml': 1000, 'remaining_ml': 900}, headers=h).get_json()['id']
    items = {i['name']: i for i in c.get('/api/resin/restock').get_json()['items']}
    assert 'Rouge R' in items and 'Bleue R' not in items                       # seuil : 250 ml <= 300 ml
    assert items['Rouge R']['total_ml'] == 250 and isinstance(items['Rouge R']['shops'], list)
    assert c.post('/api/resin/restock/flag', json={'id': b, 'flagged': True}, headers=h).status_code == 200
    d = c.get('/api/resin').get_json()
    assert [x['to_order'] for x in d['bottles'] if x['id'] == b] == [True]
    assert 'Bleue R' in {i['name'] for i in c.get('/api/resin/restock').get_json()['items']}
    key = items['Rouge R']['key']
    assert c.post('/api/resin/restock/snooze', json={'key': key, 'days': 14}, headers=h).status_code == 200      # « déjà commandé »
    assert 'Rouge R' not in {i['name'] for i in c.get('/api/resin/restock').get_json()['items']}
    assert 'Rouge R' in {i['name'] for i in c.get('/api/resin/restock?all=1').get_json()['items']}
    assert c.post('/api/resin/restock/flag', json={'id': 999999, 'flagged': True}, headers=h).status_code == 404
    c.post('/api/resin/restock/flag', json={'id': b, 'flagged': False}, headers=h)
    c.post('/api/resin/restock/snooze', json={'key': key, 'days': 0}, headers=h)
    for i in (a, b):
        c.post('/api/resin/delete', json={'id': i}, headers=h)
    c.post('/api/resin/restock/threshold', json={'ml': 200}, headers=h)


def test_resin_restock_wiring():
    js = (ROOT / 'interface/script.js').read_text(encoding='utf-8')
    v = (ROOT / 'interface/v113.js').read_text(encoding='utf-8')
    assert '/api/resin/restock' in js and 'it.resin' in js and 'resinShops' in v and '/api/resin/restock/flag' in v


def test_logiciels_resine_declares_partout():
    main = (ROOT / 'main.py').read_text(encoding='utf-8')
    html = (ROOT / 'interface/index.html').read_text(encoding='utf-8')
    for sid, exe in (('chitubox', 'CHITUBOX.exe'), ('chituboxpro', 'CHITUBOXPro.exe'), ('photonworkshop', 'AnycubicPhotonWorkshop.exe'),
                     ('preform', 'PreForm.exe'), ('voxeldance', 'VoxeldanceTango.exe')):
        assert f"    '{sid}': {{" in main and f"'{sid}': '{exe}'" in main and f"'{sid}'" in main.split('RESIN_SLICER_IDS = ')[1][:120], sid
        assert f'<option value="{sid}">' in html and f'<option value="{exe}">' in html, sid


def test_maintenance_resine_sur_les_cartes():
    js = (ROOT / 'interface/script.js').read_text(encoding='utf-8')
    assert 'resin: [' in js and "(_isResin(p) ? 'resin' : '')" in js and 'value="resin"' in js
    keys = re.findall(r"nameKey: '(printers\.maintenance_task\.[a-z_]+)'", js.split('resin: [')[1].split('],')[0])
    assert len(keys) == 9
    for l in LANGS:
        d = json.loads((ROOT / 'languages' / f'{l}.json').read_text(encoding='utf-8'))
        assert d.get('printers.maintenance_brand_resin'), l
        for k in keys:
            assert d.get(k), (l, k)


def test_slicers_installed_route(v113_client):
    c, _ = v113_client
    d = c.get('/api/slicers/installed').get_json()
    assert isinstance(d['slicers'], list) and 'beta_resin' not in d and 'resin_default' in d
    for s in d['slicers']:
        assert {'id', 'name', 'default_value', 'resin'} <= set(s)


def test_fenetre_integree_repli_explique():
    import ast
    src = (ROOT / 'main.py').read_text(encoding='utf-8')
    tree = ast.parse(src)
    names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    assert {'_webview2_runtime_version', '_tell_window_fallback'} <= names
    assert 'os._exit(0)\n                _tell_window_fallback()' in src          # le repli navigateur n'est plus silencieux
    d = next(n for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '') == '_WINDOW_FALLBACK_TEXT')
    assert {k.value for k in d.value.keys} == set(LANGS)
    p = next(n for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "_WINDOW_FALLBACK_PRESENT")
    assert {k.value for k in p.value.keys} == set(LANGS)


def test_fenetre_de_secours_mode_application():
    src = (pathlib.Path(__file__).resolve().parent.parent / 'main.py').read_text(encoding='utf-8')
    assert 'def _open_app_window_fallback(' in src and 'def _find_chromium_app_browser(' in src
    assert '--app={url}' in src and "'appwin'" in src
    i = src.index('if _open_app_window_fallback(')
    assert 'os._exit(0)' in src[i:i + 600] and 'webbrowser.open' in src[i:i + 900]


def test_sosprint_questions_sans_limite():
    src = (ROOT / 'main.py').read_text(encoding='utf-8')
    helpers = (ROOT / 'modules' / 'sosprint_helpers.py').read_text(encoding='utf-8')
    assert 'SOSPRINT_SOFT_QUESTIONS' not in src and 'SOSPRINT_SOFT_QUESTIONS' not in helpers
    assert re.search(r'SOSPRINT_HARD_MAX_QUESTIONS = (\d+)', helpers) and int(re.search(r'SOSPRINT_HARD_MAX_QUESTIONS = (\d+)', helpers).group(1)) >= 500
    assert 'NEW_CAUSES:' in src and 'failed_attempts' in src
    js = (ROOT / 'interface' / 'script.js').read_text(encoding='utf-8')
    assert js.count('failed_attempts: sosprintFailedAttempts') == 3 and 'sosprintFailedAttempts += 1' in js


def test_sosprint_vitesses_profil_et_prompt():
    import json as _json
    root = pathlib.Path(__file__).resolve().parent.parent
    helpers = (root / 'modules' / 'sosprint_helpers.py').read_text(encoding='utf-8')
    imp = (root / 'modules' / 'slicer_import.py').read_text(encoding='utf-8')
    js = (root / 'interface' / 'script.js').read_text(encoding='utf-8')
    html = (root / 'interface' / 'index.html').read_text(encoding='utf-8')
    new = ('outer_wall_speed', 'inner_wall_speed', 'infill_speed', 'travel_speed')
    for k in new:
        assert f"'{k}'" in helpers and f'"{k}"' in imp and f"'{k}'" in js and f'id="sosprint-set-{k}"' in html
        for l in ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja'):
            assert f'sosprint.set_{k}' in _json.loads((root / 'languages' / f'{l}.json').read_text(encoding='utf-8'))
    assert 'speeds_v' in imp and 'SOSPRINT_SPEED_RULE_ASK' in helpers and 'SOSPRINT_SPEED_RULE_USE' in helpers


def test_sosprint_bloc_reglages_vitesses():
    import importlib
    h = importlib.import_module('modules.sosprint_helpers')
    vide = h._sosprint_settings_block({})
    assert 'ASK the user' in vide                       # aucune vitesse connue : l'IA doit les demander
    avec = h._sosprint_settings_block({'print_speed': 80, 'travel_speed': 200, 'outer_wall_speed': 40})
    assert 'Travel speed: 200 mm/s' in avec and 'Outer wall speed: 40 mm/s' in avec and 'Take the speeds into account' in avec
    sans = h._sosprint_settings_block({'nozzle_temp': 210})
    assert 'ASK the user' in sans                       # réglages donnés mais sans vitesse : on les demande


def test_sosprint_multicolore_tour_de_purge():
    import importlib, json as _json
    root = pathlib.Path(__file__).resolve().parent.parent
    h = importlib.import_module('modules.sosprint_helpers')
    for s in ({}, {'print_speed': 60}):
        b = h._sosprint_settings_block(s)
        assert 'purge / prime / wipe tower' in b and 'multicolor' in b.lower()
    assert 'Purge / prime tower width: 35 mm' in h._sosprint_settings_block({'prime_tower_width': 35})
    assert 'id="sosprint-set-prime_tower_width"' in (root / 'interface' / 'index.html').read_text(encoding='utf-8')
    assert "'prime_tower_width'" in (root / 'interface' / 'script.js').read_text(encoding='utf-8')
    for l in ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja'):
        assert 'sosprint.set_prime_tower_width' in _json.loads((root / 'languages' / f'{l}.json').read_text(encoding='utf-8'))


def test_sosprint_hypotheses_avec_probabilite():
    import importlib
    root = pathlib.Path(__file__).resolve().parent.parent
    h = importlib.import_module('modules.sosprint_helpers')
    bloc = "- Buse trop basse | 55 % | Vérifier le Z-offset\n- Plateau sale | 30 | Nettoyer à l'IPA\n2. Humidité | ~15% |\n- Sans détail"
    hyp = h._sosprint_parse_hypotheses(bloc)
    assert [x['cause'] for x in hyp] == ['Buse trop basse', 'Plateau sale', 'Humidité', 'Sans détail']
    assert [x['pct'] for x in hyp] == [55, 30, 15, None] and hyp[0]['why'] == 'Vérifier le Z-offset'
    assert h._sosprint_parse_causes(bloc)[0] == 'Buse trop basse'        # le libellé reste seul dans la liste des suspects
    src = (root / 'main.py').read_text(encoding='utf-8')
    assert src.count('"hypotheses": hypotheses') == 3 and 'LIKELIHOOD:' in src
    js = (root / 'interface' / 'script.js').read_text(encoding='utf-8')
    assert js.count('mergeSosprintHypotheses(data);') == 4 and 'sosprint-pct' in js
    assert '.sosprint-pct' in (root / 'interface' / 'style.css').read_text(encoding='utf-8')


def test_sosprint_avertissement_ia_pas_fiable():
    import json as _json
    root = pathlib.Path(__file__).resolve().parent.parent
    html = (root / 'interface' / 'index.html').read_text(encoding='utf-8')
    assert html.count('data-i18n="sosprint.ai_warning"') == 2          # encart du haut + résultat
    for l in ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja'):
        assert _json.loads((root / 'languages' / f'{l}.json').read_text(encoding='utf-8')).get('sosprint.ai_warning')
        assert '⚠️' in (root / 'docs' / 'wiki' / 'src' / f'{l}.md').read_text(encoding='utf-8')
    assert '.sosprint-ai-warning' in (root / 'interface' / 'style.css').read_text(encoding='utf-8')


def test_avertissement_ia_pas_fiable():
    root = pathlib.Path(__file__).resolve().parent.parent
    html = (root / 'interface' / 'index.html').read_text(encoding='utf-8')
    assert html.count('data-i18n="sosprint.ai_warning"') == 2          # formulaire, enquête, résultat
    for f in ['README.md'] + [f'docs/readme/README_{l}.md' for l in ('fr', 'de', 'es', 'pt', 'it', 'zh', 'ja')]:
        txt = (root / f).read_text(encoding='utf-8').split('### 🤖', 1)[1][:700]
        assert '⚠️' in txt, f
    for l in ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja'):
        wiki = (root / 'docs' / 'wiki' / 'src' / f'{l}.md').read_text(encoding='utf-8')
        assert wiki.count('> ⚠️') >= 2, l                               # section IA + S.O.S Print


def test_notes_de_mise_a_jour_dans_la_langue_de_stellio():
    import re as _re, sys as _sys
    root = pathlib.Path(__file__).resolve().parent.parent
    _sys.path.insert(0, str(root / 'tools'))
    import release_notes as rn
    src = (root / 'main.py').read_text(encoding='utf-8')
    ns = {'re': _re}
    exec(src[src.index('_RELEASE_LANG_TITLES ='):src.index('def get_current_app_language')], ns)
    f = ns['_extract_release_notes_for_lang']
    body = rn.build('1.1.3')
    sections = rn.parse((root / 'release-notes' / 'notes.txt').read_text(encoding='utf-8'))
    for l in ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja'):
        out = f(body, l)
        assert [x.strip() for x in out.splitlines() if x.strip()] == sections[l]
        assert '<details' not in out and 'Full changelog' not in out
    assert f(body, 'xx') == f(body, 'en')                           # langue inconnue : anglais
    assert f('<!--fr-->\nA\n<!--en-->\nB', 'en') == 'B'            # ancien format toujours géré


def test_sosprint_conclusion_possible_des_la_question_3():
    src = (ROOT / 'main.py').read_text(encoding='utf-8')
    js = (ROOT / 'interface' / 'script.js').read_text(encoding='utf-8')
    assert 'elif asked_count < 2:' in src and 'you may conclude from now on (question 3' in src
    assert "questionNumber >= 3 ? '' : 'none'" in js


def test_couleur_de_la_bobine_appliquee_au_profil_filament(tmp_path):
    """Envoi au slicer : la couleur de la bobine assignée est écrite dans une copie du profil de filament."""
    import json
    from conftest import load_from_main
    import logging
    ns = load_from_main(['_normalize_hex_colour', '_filament_profiles_with_colour', '_SLICER_LOAD_INI_FAMILIES'],
                        extra_ns={'re': __import__('re'), 'json': json, 'hashlib': __import__('hashlib'),
                                  'DATA_DIR': str(tmp_path), 'app_logger': logging.getLogger('t')})
    assert ns['_normalize_hex_colour']('000') == '#000000' and ns['_normalize_hex_colour']('zz') is None
    src = tmp_path / 'pla.json'
    src.write_text(json.dumps({'name': 'PLA Générique', 'filament_colour': ['#FFFFFF'], 'filament_settings_id': ['PLA Générique']}), encoding='utf-8')
    out = ns['_filament_profiles_with_colour']([str(src)], 'orcaslicer', '#111111')
    prof = json.loads(open(out[0], encoding='utf-8').read())
    assert out[0] != str(src) and prof['filament_colour'] == ['#111111'] and '#111111' in prof['name']
    assert json.loads(src.read_text(encoding='utf-8'))['filament_colour'] == ['#FFFFFF']   # l'original n'est pas modifié
    ini = tmp_path / 'p.ini'; ini.write_text('filament_type = PLA\nfilament_colour = #FFFFFF\n', encoding='utf-8')
    out = ns['_filament_profiles_with_colour']([str(ini)], 'prusaslicer', '000000')
    assert 'filament_colour = #000000' in open(out[0], encoding='utf-8').read()
    assert ns['_filament_profiles_with_colour']([str(src)], 'orcaslicer', None) == [str(src)]


def test_fichiers_supprimes_ne_reviennent_pas_apres_un_scan_en_retard(tmp_path):
    """Un scan commencé avant la suppression (partage réseau lent) ne doit pas remettre le fichier dans la bibliothèque."""
    import threading, time
    from conftest import load_from_main
    ns = load_from_main(['note_deleted_paths', 'drop_recently_deleted', '_recently_deleted', '_recently_deleted_lock', '_RECENTLY_DELETED_TTL'],
                        extra_ns={'threading': threading, 'time': time})
    gone, kept = tmp_path / 'a.stl', tmp_path / 'b.stl'
    kept.write_bytes(b'x')
    files = [{'path': str(gone)}, {'path': str(kept)}]
    assert len(ns['drop_recently_deleted'](files)) == 2          # rien de supprimé : liste intacte
    ns['note_deleted_paths']([str(gone), str(kept)])
    assert [f['path'] for f in ns['drop_recently_deleted'](files)] == [str(kept)]   # a.stl absent du disque : retiré ; b.stl restauré/présent : gardé
