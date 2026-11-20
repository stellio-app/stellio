"""1.1.7 — plugins et SDK : manifeste, extraction sûre, exécution isolée, permissions, journal."""
import importlib.util, io, json, logging, os, sqlite3, sys, time, zipfile
import pytest
flask = pytest.importorskip('flask')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _mod(name):
    spec = importlib.util.spec_from_file_location(name + '_t', os.path.join(ROOT, 'modules', name + '.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


MANIFEST = {'id': 'demo', 'name': 'Démo', 'version': '1.0', 'api': 1, 'entry': 'main.py', 'events': ['print.finished'], 'permissions': ['events']}


def _zip(files):
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w') as z:
        for n, c in files.items():
            z.writestr(n, c)
    return b.getvalue()


def test_manifeste_valide_et_refus():
    p = _mod('plugins')
    assert p.validate_manifest(MANIFEST)[1] is None
    for bad in (dict(MANIFEST, id='Démo!'), dict(MANIFEST, api=2), dict(MANIFEST, name=''), dict(MANIFEST, entry='../x.py'), dict(MANIFEST, entry='run.sh'),
                dict(MANIFEST, events=['print.exploded']), dict(MANIFEST, permissions=['root']), dict(MANIFEST, permissions=[])):   # évènements sans permission « events »
        assert p.validate_manifest(bad)[1], bad
    assert p.validate_manifest('pas un dict')[1]


def test_extraction_sure(tmp_path):
    p = _mod('plugins')
    z = _zip({'plugin.json': json.dumps(MANIFEST), 'main.py': 'print(1)', 'lib/aide.py': 'x=1'})
    m = p.safe_extract(z, str(tmp_path / 'a')); assert m['id'] == 'demo' and (tmp_path / 'a' / 'lib' / 'aide.py').exists()
    z = _zip({'demo/plugin.json': json.dumps(MANIFEST), 'demo/main.py': 'print(1)'})                       # dossier racine unique toléré
    assert p.safe_extract(z, str(tmp_path / 'b'))['id'] == 'demo' and (tmp_path / 'b' / 'main.py').exists()
    for bad, why in ((_zip({'plugin.json': json.dumps(MANIFEST), 'main.py': 'x', '../evil.py': 'x'}), 'zip-slip'),
                     (_zip({'plugin.json': json.dumps(MANIFEST), 'main.py': 'x', '/abs.py': 'x'}), 'absolu'),
                     (_zip({'main.py': 'x'}), 'sans manifeste'), (_zip({'plugin.json': json.dumps(MANIFEST)}), 'sans entrée'),
                     (b'pas un zip', 'invalide'), (_zip({'plugin.json': json.dumps(dict(MANIFEST, id='a')), 'main.py': 'x'} | {f'f{i}.py': 'x' for i in range(120)}), 'trop de fichiers')):
        with pytest.raises(ValueError):
            p.safe_extract(bad, str(tmp_path / 'c'))
    assert not (tmp_path / 'evil.py').exists() and not os.path.exists('/abs.py')


def test_environnement_nettoye_et_jeton_selon_permission():
    p = _mod('plugins')
    os.environ['SECRET_STELLIO'] = 'oups'
    m = dict(MANIFEST, permissions=['events'])
    env = p.build_env(m, {'token': 'stl_x', 'api_url': 'http://h', 'reglage': 'a'})
    assert 'SECRET_STELLIO' not in env and 'STELLIO_API_TOKEN' not in env and 'STELLIO_API_URL' not in env
    assert json.loads(env['STELLIO_PLUGIN_CONFIG']) == {'reglage': 'a'}                                  # le jeton n'est jamais dans la config
    env2 = p.build_env(dict(m, permissions=['events', 'api:read']), {'token': 'stl_x', 'api_url': 'http://h'})
    assert env2['STELLIO_API_TOKEN'] == 'stl_x' and env2['STELLIO_API_URL'] == 'http://h'


def _plugin(tmp_path, code, **mf):
    d = tmp_path / 'p'; d.mkdir(exist_ok=True)
    m = dict(MANIFEST, **mf); (d / 'main.py').write_text(code); return str(d), p_validate(m)


def p_validate(m): return _mod('plugins').validate_manifest(m)[0]


def test_execution_recoit_evenement_sur_stdin(tmp_path):
    p = _mod('plugins')
    d, m = _plugin(tmp_path, "import sys, json\nd = json.loads(sys.stdin.read())\nprint('recu', d['event'], d['data']['file_name'], sys.argv[1])\n")
    r = p.run_plugin(d, m, 'print.finished', {'file_name': 'a.gcode'}, {})
    assert r['ok'] and r['output'].strip() == 'recu print.finished a.gcode print.finished'


def test_execution_isolee_sans_secrets_ni_jeton(tmp_path):
    p = _mod('plugins')
    os.environ['SECRET_STELLIO'] = 'oups'
    d, m = _plugin(tmp_path, "import os, json\nprint(json.dumps(sorted(k for k in os.environ if 'STELLIO' in k or 'SECRET' in k)))\n")
    r = p.run_plugin(d, m, 'print.finished', {}, {'token': 'stl_secret'})
    keys = json.loads(r['output']); assert 'SECRET_STELLIO' not in keys and 'STELLIO_API_TOKEN' not in keys and 'STELLIO_PLUGIN_ID' in keys


def test_erreur_et_delai(tmp_path):
    p = _mod('plugins')
    d, m = _plugin(tmp_path, "raise RuntimeError('boum')\n")
    r = p.run_plugin(d, m, 'print.finished', {}, {}); assert not r['ok'] and 'boum' in r['error']
    d, m = _plugin(tmp_path, "import time\ntime.sleep(5)\n")
    t0 = time.time(); r = p.run_plugin(d, m, 'print.finished', {}, {}, timeout=1)
    assert not r['ok'] and 'Délai' in r['error'] and time.time() - t0 < 4
    r = p.run_plugin(str(tmp_path / 'absent'), m, 'print.finished', {}, {}); assert not r['ok']          # ne lève jamais


def _env(tmp_path):
    p = _mod('plugins'); path = str(tmp_path / 't.db')
    def get_db():
        c = sqlite3.connect(path); c.row_factory = sqlite3.Row; return c
    app = flask.Flask('t'); app.secret_key = 'x'
    p.init(dict(app=app, app_logger=logging.getLogger('t'), get_db=get_db, jsonify=flask.jsonify, login_required=lambda f: f, request=flask.request,
                session=flask.session, DATA_DIR=str(tmp_path)))
    cl = app.test_client()
    with cl.session_transaction() as s: s['user_id'] = 1
    return p, cl, get_db


def _install(cl, code="print('ok')", **mf):
    z = _zip({'plugin.json': json.dumps(dict(MANIFEST, **mf)), 'main.py': code})
    return cl.post('/api/plugins/install', data={'file': (io.BytesIO(z), 'p.zip')}, content_type='multipart/form-data')


def test_cycle_installation_activation_evenement_journal(tmp_path):
    p, cl, get_db = _env(tmp_path)
    r = _install(cl, "import sys, json; print('E=' + json.loads(sys.stdin.read())['event'])"); assert r.status_code == 200
    lst = cl.get('/api/plugins').get_json()['plugins']; assert lst[0]['id'] == 'demo' and lst[0]['enabled'] is False
    assert cl.put('/api/plugins/demo', json={'enabled': True}).status_code == 400                         # permissions à accepter explicitement
    assert cl.put('/api/plugins/demo', json={'enabled': True, 'ack_permissions': ['network']}).status_code == 400
    assert cl.put('/api/plugins/demo', json={'enabled': True, 'ack_permissions': ['events']}).status_code == 200
    with cl.application.test_request_context():
        assert p.dispatch('print.finished', {'file_name': 'x'}, 1) == 1
        assert p.dispatch('order.late', {}, 1) == 0                                                           # pas abonné
        assert p.dispatch('print.finished', {}, 2) == 0                                                       # autre compte
        assert p.dispatch('evenement.inconnu', {}, 1) == 0
    for _ in range(100):
        log = cl.get('/api/plugins/log').get_json()['log']
        if log: break
        time.sleep(0.05)
    assert log[0]['ok'] == 1 and 'E=print.finished' in log[0]['output']
    assert p.has_active(1) and not p.has_active(2)
    assert cl.put('/api/plugins/demo', json={'enabled': False}).status_code == 200
    with cl.application.test_request_context():
        assert p.dispatch('print.finished', {}, 1) == 0                                                       # désactivé : plus rien
    assert cl.delete('/api/plugins/demo').status_code == 200 and cl.get('/api/plugins').get_json()['plugins'] == []


def test_essai_manuel_et_config_masquee(tmp_path):
    p, cl, _ = _env(tmp_path); _install(cl, "import os; print(os.environ['STELLIO_PLUGIN_CONFIG'])", permissions=['events', 'api:read'])
    assert cl.put('/api/plugins/demo', json={'config': {'token': 'stl_abc', 'api_url': 'http://h', 'x': 'y'}}).status_code == 200
    shown = cl.get('/api/plugins').get_json()['plugins'][0]['config']; assert shown['token'] == '••••' and shown['x'] == 'y'
    assert cl.put('/api/plugins/demo', json={'config': {'token': '••••', 'x': 'z'}}).status_code == 200      # le masque ne remplace pas le vrai jeton
    r = cl.post('/api/plugins/demo/test', json={}).get_json(); assert r['ok'] and json.loads(r['output']) == {'x': 'z'}
    assert cl.post('/api/plugins/inconnu/test', json={}).status_code == 404


def test_installation_refuse_archive_piegee_et_invites(tmp_path):
    p, cl, _ = _env(tmp_path)
    z = _zip({'plugin.json': json.dumps(MANIFEST), 'main.py': 'x', '../../evil.py': 'x'})
    assert cl.post('/api/plugins/install', data={'file': (io.BytesIO(z), 'p.zip')}, content_type='multipart/form-data').status_code == 400
    assert not (tmp_path / 'evil.py').exists() and cl.get('/api/plugins').get_json()['plugins'] == []
    assert cl.post('/api/plugins/install').status_code == 400
    with cl.session_transaction() as s: s['role'] = 'viewer'
    assert cl.get('/api/plugins').status_code == 403 and cl.put('/api/plugins/demo', json={}).status_code == 403


def test_main_alimente_les_plugins_avec_les_evenements():
    src = open(os.path.join(ROOT, 'main.py'), encoding='utf-8').read()
    assert '_pl.dispatch(event, data, user_id)' in src and '_pl.has_active()' in src


def test_exemple_de_plugin_et_sdk_valides(tmp_path):
    p = _mod('plugins'); ex = os.path.join(ROOT, 'sdk', 'examples', 'hello-plugin')
    m, err = p.validate_manifest(json.load(open(os.path.join(ex, 'plugin.json')))); assert err is None
    r = p.run_plugin(ex, m, 'print.finished', {'file_name': 'benchy.gcode'}, {}); assert r['ok'] and 'benchy.gcode' in r['output']
    spec = importlib.util.spec_from_file_location('sdk_t', os.path.join(ROOT, 'sdk', 'python', 'stellio_sdk.py'))
    sdk = importlib.util.module_from_spec(spec); spec.loader.exec_module(sdk)
    with pytest.raises(ValueError): sdk.Stellio('', '')
    assert sdk.Stellio('http://h/', 'stl_x').base == 'http://h'
    assert os.path.isfile(os.path.join(ROOT, 'sdk', 'js', 'stellio-sdk.mjs'))


def test_versions_et_catalogue_pur():
    p = _mod('plugins')
    assert p.compare_versions('1.10.0', '1.9.9') == 1 and p.compare_versions('1.0', '1.0.0') == 0 and p.compare_versions('0.9', '1.0') == -1
    sha = 'a' * 64
    good = {'id': 'meteo', 'name': 'Météo', 'version': '1.2', 'url': 'https://x.org/m.zip', 'sha256': sha.upper(), 'permissions': ['events', 'nimporte']}
    cat = p.validate_catalog({'plugins': [good, dict(good, id='meteo'),                                     # doublon
                                          dict(good, id='http', url='http://x.org/a.zip'), dict(good, id='nosha', sha256='abc'),
                                          dict(good, id='Bad Id'), 'texte', {}]})
    assert [e['id'] for e in cat] == ['meteo'] and cat[0]['sha256'] == sha and cat[0]['permissions'] == ['events']
    with pytest.raises(ValueError): p.validate_catalog({'x': 1})
    for bad in ('http://example.org/c.json', 'https://user:pw@example.org/c.json', 'ftp://example.org', '', 'https://localhost/c.json', 'https://127.0.0.1/c.json', 'https://192.168.1.5/c.json',
                'https://169.254.169.254/latest'):
        with pytest.raises(ValueError): p.check_url(bad)


def test_mise_a_jour_garde_config_et_exige_nouvelles_permissions(tmp_path):
    p, cl, _ = _env(tmp_path)
    assert _install(cl, version='1.0').get_json()['action'] == 'installed'
    assert cl.put('/api/plugins/demo', json={'enabled': True, 'ack_permissions': ['events'], 'config': {'x': 'garde'}}).status_code == 200
    r = _install(cl, "print('v2')", version='1.1').get_json()                                                  # même permissions
    assert r['action'] == 'updated' and r['previous_version'] == '1.0' and not r['reack_required']
    pl = cl.get('/api/plugins').get_json()['plugins'][0]; assert pl['version'] == '1.1' and pl['enabled'] and pl['config'] == {'x': 'garde'}
    r = _install(cl, version='1.2', permissions=['events', 'network']).get_json()                              # nouvelle permission
    assert r['reack_required'] and r['added_permissions'] == ['network']
    pl = cl.get('/api/plugins').get_json()['plugins'][0]; assert pl['enabled'] is False and pl['config'] == {'x': 'garde'}
    assert cl.put('/api/plugins/demo', json={'enabled': True, 'ack_permissions': ['events']}).status_code == 400   # doit accepter la nouvelle liste
    assert cl.put('/api/plugins/demo', json={'enabled': True, 'ack_permissions': ['events', 'network']}).status_code == 200
    z = _install(cl, version='0.5'); assert z.status_code == 409                                               # retour en arrière refusé
    assert cl.get('/api/plugins').get_json()['plugins'][0]['version'] == '1.2'
    z = _zip({'plugin.json': json.dumps(dict(MANIFEST, version='0.5', permissions=['events', 'network'])), 'main.py': 'print(1)'})
    ok = cl.post('/api/plugins/install', data={'file': (io.BytesIO(z), 'p.zip'), 'allow_downgrade': '1'}, content_type='multipart/form-data')
    assert ok.status_code == 200 and ok.get_json()['previous_version'] == '1.2' and cl.get('/api/plugins').get_json()['plugins'][0]['version'] == '0.5'
    assert not [n for n in os.listdir(os.path.join(str(tmp_path), 'plugins')) if n.endswith('.old')] if os.path.isdir(os.path.join(str(tmp_path), 'plugins')) else True


def test_catalogue_installation_sha_obligatoire(tmp_path, monkeypatch):
    import hashlib
    p, cl, _ = _env(tmp_path)
    z = _zip({'plugin.json': json.dumps(dict(MANIFEST, version='2.0')), 'main.py': "print('ok')"})
    sha = hashlib.sha256(z).hexdigest()
    index = {'plugins': [{'id': 'demo', 'name': 'Demo', 'version': '2.0', 'url': 'https://cdn.example.org/demo.zip', 'sha256': sha, 'permissions': ['events']},
                         {'id': 'faux', 'name': 'Faux', 'version': '1.0', 'url': 'https://cdn.example.org/faux.zip', 'sha256': 'b' * 64, 'permissions': ['events']}]}
    served = {'https://cdn.example.org/index.json': json.dumps(index).encode(), 'https://cdn.example.org/demo.zip': z, 'https://cdn.example.org/faux.zip': z}
    calls = []
    def fake(url, max_bytes, timeout=15):
        calls.append(url)
        if url not in served: raise ValueError('introuvable')
        return served[url]
    monkeypatch.setattr(p, 'http_get', fake)
    cat = cl.post('/api/plugins/catalog', json={'url': 'https://cdn.example.org/index.json'}).get_json()
    assert cat['count'] == 2 and cat['updates'] == 0 and cat['plugins'][0]['installed_version'] is None
    assert cl.post('/api/plugins/catalog', json={'url': ''}).status_code == 400
    assert cl.post('/api/plugins/catalog/install', json={'url': 'https://cdn.example.org/index.json', 'id': 'absent'}).status_code == 404
    bad = cl.post('/api/plugins/catalog/install', json={'url': 'https://cdn.example.org/index.json', 'id': 'faux'})
    assert bad.status_code == 400 and bad.get_json()['code'] == 'sha_mismatch' and cl.get('/api/plugins').get_json()['plugins'] == []   # rien d'installé
    ok = cl.post('/api/plugins/catalog/install', json={'url': 'https://cdn.example.org/index.json', 'id': 'demo'}).get_json()
    assert ok['ok'] and ok['plugin']['version'] == '2.0' and ok['action'] == 'installed'
    index['plugins'][0]['version'] = '2.1'; served['https://cdn.example.org/index.json'] = json.dumps(index).encode()
    assert cl.post('/api/plugins/catalog', json={'url': 'https://cdn.example.org/index.json'}).get_json()['updates'] == 1
    with cl.session_transaction() as s: s['role'] = 'viewer'
    assert cl.post('/api/plugins/catalog', json={'url': 'https://cdn.example.org/index.json'}).status_code == 403


def test_catalogue_par_defaut_logo_et_description_par_langue(tmp_path, monkeypatch):
    p, cl, _ = _env(tmp_path)
    png = b'\x89PNG\r\n\x1a\n' + b'0' * 40
    sha = 'a' * 64
    index = {'plugins': [
        {'id': 'meteo', 'name': 'Météo', 'version': '1.0', 'url': 'https://cdn.example.org/m.zip', 'sha256': sha, 'logo': 'https://cdn.example.org/m.png', 'homepage': 'https://github.com/x/meteo',
         'description': {'fr': 'Prévisions sur le plateau', 'en': 'Forecast on the plate', 'xx': 'ignoré'}},
        {'id': 'svg', 'name': 'Svg', 'version': '1.0', 'url': 'https://cdn.example.org/s.zip', 'sha256': sha, 'logo': 'https://cdn.example.org/s.svg', 'description': 'texte simple'},
        {'id': 'nologo', 'name': 'Sans logo', 'version': '1.0', 'url': 'https://cdn.example.org/n.zip', 'sha256': sha, 'logo': 'http://pas-https/x.png'}]}
    served = {p.DEFAULT_CATALOG_URL: json.dumps(index).encode(), 'https://cdn.example.org/m.png': png, 'https://cdn.example.org/s.svg': b'<svg onload="alert(1)"></svg>'}
    seen = []
    def fake(url, max_bytes, timeout=15):
        seen.append(url)
        if url not in served: raise ValueError('introuvable')
        return served[url]
    monkeypatch.setattr(p, 'http_get', fake)
    monkeypatch.delenv('STELLIO_PLUGINS_CATALOG', raising=False)
    cat = cl.post('/api/plugins/catalog', json={'lang': 'fr'}).get_json()                       # sans adresse : catalogue officiel
    by = {e['id']: e for e in cat['plugins']}
    assert cat['default'] is True and seen[0] == p.DEFAULT_CATALOG_URL
    assert by['meteo']['description'] == 'Prévisions sur le plateau' and by['meteo']['has_logo'] is True and by['meteo']['homepage'] == 'https://github.com/x/meteo'
    assert by['svg']['description'] == 'texte simple' and by['nologo']['has_logo'] is False and 'logo' not in by['meteo'] and 'description_i18n' not in by['meteo']
    assert cl.post('/api/plugins/catalog', json={'lang': 'de'}).get_json()['plugins'][0]['description'] == 'Forecast on the plate'      # repli anglais
    r = cl.get('/api/plugins/logo?id=meteo')
    assert r.status_code == 200 and r.mimetype == 'image/png' and r.data == png and r.headers['X-Content-Type-Options'] == 'nosniff' and 'sandbox' in r.headers['Content-Security-Policy']
    assert cl.get('/api/plugins/logo?id=svg').status_code == 415                                 # SVG refusé (peut contenir du script)
    assert cl.get('/api/plugins/logo?id=nologo').status_code == 404 and cl.get('/api/plugins/logo?id=absent').status_code == 404
    monkeypatch.setenv('STELLIO_PLUGINS_CATALOG', 'https://autre.example.org/c.json'); assert p.default_catalog_url() == 'https://autre.example.org/c.json'
    monkeypatch.setenv('STELLIO_PLUGINS_CATALOG', 'http://pas-https/c.json'); assert p.default_catalog_url() == p.DEFAULT_CATALOG_URL
    with cl.session_transaction() as s: s['role'] = 'viewer'
    assert cl.get('/api/plugins/logo?id=meteo').status_code == 403


def test_validateur_de_catalogue_du_depot_modele(tmp_path):
    import importlib.util, json, os
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sdk', 'plugins-registry')
    spec = importlib.util.spec_from_file_location('validate_catalog', os.path.join(base, 'validate_catalog.py'))
    v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
    assert v.main([os.path.join(base, 'catalog.json'), '--offline']) == 0
    ok = {'id': 'demo', 'name': 'Demo', 'version': '1.0', 'author': 'x', 'description': {'fr': 'a', 'en': 'b'},
          'url': 'https://exemple.org/d.zip', 'sha256': 'a' * 64, 'permissions': ['events'], 'logo': 'https://exemple.org/l.png'}
    assert v.check_entry(ok, True) == []
    assert v.check_entry(dict(ok, url='http://exemple.org/d.zip'), True)
    assert v.check_entry(dict(ok, sha256='zz'), True)
    assert v.check_entry(dict(ok, description={'xx': 'a'}), True)
    assert v.check_entry(dict(ok, logo='http://x/l.png'), True)
    assert v.sniff(b'\x89PNG\r\n\x1a\n....') == 'png' and v.sniff(b'<svg') is None
    bad = tmp_path / 'c.json'; bad.write_text(json.dumps({'plugins': [ok, ok]}))
    assert v.main([str(bad), '--offline']) == 1


def test_plugin_avec_page_manifeste_installation_et_service(tmp_path):
    p = _mod('plugins')
    ui = {'title': 'Ma page', 'icon': 'fa-cube', 'entry': 'page.html'}
    base = {'id': 'vue', 'name': 'Vue', 'version': '1', 'api': 1, 'permissions': ['ui'], 'ui': ui}
    m, err = p.validate_manifest(base); assert err is None and m['entry'] == '' and m['ui'] == ui          # page seule : pas de script
    for bad in (dict(base, permissions=[]), dict(base, ui={'entry': '../x.html'}), dict(base, ui={'entry': '/etc/passwd.html'}), dict(base, ui={'entry': 'x.js'}),
                dict(base, ui=dict(ui, icon='<b>')), dict(base, ui='page.html')):
        assert p.validate_manifest(bad)[1], bad
    assert p.validate_manifest(dict(base, ui={'entry': 'page.html'}))[0]['ui']['icon'] == 'fa-puzzle-piece'   # valeurs par défaut
    html = '<!doctype html><title>x</title><p id="a">bonjour</p>'
    _, cl, _ = _env(tmp_path)
    def put(files):
        return cl.post('/api/plugins/install', data={'file': (io.BytesIO(_zip(files)), 'p.zip')}, content_type='multipart/form-data')
    assert put({'plugin.json': json.dumps(base)}).status_code == 400                                       # page annoncée mais absente
    assert put({'plugin.json': json.dumps(base), 'page.html': html}).status_code == 200
    lst = cl.get('/api/plugins').get_json()['plugins']; assert lst[0]['ui']['title'] == 'Ma page'
    r = cl.get('/api/plugins/vue/ui'); assert r.status_code == 403 and r.get_json()['code'] == 'plugin_disabled'      # désactivé : rien n'est servi
    assert cl.put('/api/plugins/vue', json={'enabled': True, 'ack_permissions': ['ui']}).status_code == 200
    r = cl.get('/api/plugins/vue/ui'); assert r.status_code == 200 and 'bonjour' in r.get_data(as_text=True)
    assert 'sandbox' in r.headers['Content-Security-Policy'] and r.headers['X-Content-Type-Options'] == 'nosniff'
    assert cl.get('/api/plugins/inconnu/ui').status_code == 404
    assert cl.post('/api/plugins/vue/test', json={}).get_json()['ok'] is False                              # pas de script à lancer
    ex = os.path.join(ROOT, 'sdk', 'examples', 'gcode-viewer')
    mv, errv = p.validate_manifest(json.load(open(os.path.join(ex, 'plugin.json')))); assert errv is None and mv['ui']['entry'] == 'viewer.html'
    assert os.path.isfile(os.path.join(ex, 'viewer.html')) and 'api:read' in mv['permissions']


def test_origine_officiel_ou_communautaire_selon_l_adresse_reelle(tmp_path, monkeypatch):
    import hashlib
    p, cl, _ = _env(tmp_path)
    assert p.is_official('https://github.com/stellio-app/stellio-plugins/releases/download/x/x.zip')
    assert p.is_official('https://raw.githubusercontent.com/Stellio-App/stellio-plugins/main/x.zip')
    for u in ('https://github.com/stellio-app/stellio-plugins-evil/x.zip', 'https://github.com/auteur/mon-plugin/x.zip', 'https://evil.example/https://github.com/stellio-app/stellio-plugins/x.zip', ''):
        assert not p.is_official(u), u
    z1 = _zip({'plugin.json': json.dumps(dict(MANIFEST, id='off', version='1.0')), 'main.py': "print('ok')"})
    z2 = _zip({'plugin.json': json.dumps(dict(MANIFEST, id='comm', version='1.0')), 'main.py': "print('ok')"})
    u1, u2 = 'https://github.com/stellio-app/stellio-plugins/releases/download/off-1.0/off.zip', 'https://github.com/auteur/comm/releases/download/v1/comm.zip'
    index = {'plugins': [{'id': 'off', 'name': 'Off', 'version': '1.0', 'url': u1, 'sha256': hashlib.sha256(z1).hexdigest(), 'permissions': ['events'], 'official': True},
                         {'id': 'comm', 'name': 'Comm', 'version': '1.0', 'url': u2, 'sha256': hashlib.sha256(z2).hexdigest(), 'permissions': ['events'], 'official': True}]}
    served = {'https://x.example/c.json': json.dumps(index).encode(), u1: z1, u2: z2}
    monkeypatch.setattr(p, 'http_get', lambda url, m, timeout=15: served[url])
    cat = {e['id']: e for e in cl.post('/api/plugins/catalog', json={'url': 'https://x.example/c.json'}).get_json()['plugins']}
    assert cat['off']['official'] is True and cat['comm']['official'] is False             # le champ « official » du catalogue est ignoré
    for pid in ('off', 'comm'):
        assert cl.post('/api/plugins/catalog/install', json={'url': 'https://x.example/c.json', 'id': pid}).get_json()['ok']
    org = {x['id']: x['origin'] for x in cl.get('/api/plugins').get_json()['plugins']}
    assert org == {'off': 'official', 'comm': 'community'}
    r = cl.post('/api/plugins/install', data={'file': (io.BytesIO(z1), 'p.zip'), 'allow_downgrade': '1'}, content_type='multipart/form-data')   # zip manuel : communautaire
    assert r.status_code == 200 and cl.get('/api/plugins').get_json()['plugins'][1]['origin'] == 'community'
    assert cl.delete('/api/plugins/comm').status_code == 200 and 'comm' not in p._origins()


def test_actualiser_le_catalogue_vide_les_caches(tmp_path, monkeypatch):
    p, cl, _ = _env(tmp_path)
    n = {'v': 1}
    monkeypatch.setattr(p, 'http_get', lambda url, m, timeout=15: json.dumps({'plugins': [{'id': 'a' * 2, 'name': 'N%d' % n['v'], 'version': '1', 'url': 'https://x.example/a.zip', 'sha256': 'c' * 64}]}).encode())
    p._catalog_cache['https://x.example/c.json'] = (time.time(), []); p._logo_cache['u'] = (time.time(), b'x', 'image/png')
    assert cl.post('/api/plugins/catalog', json={'url': 'https://x.example/c.json'}).status_code == 200 and 'u' in p._logo_cache
    assert cl.post('/api/plugins/catalog', json={'url': 'https://x.example/c.json', 'refresh': True}).status_code == 200
    assert 'u' not in p._logo_cache and 'https://x.example/c.json' not in p._catalog_cache


def test_description_lue_dans_le_plugin_json_sur_github(tmp_path, monkeypatch):
    p, cl, _ = _env(tmp_path)
    assert p.manifest_url({'homepage': 'https://github.com/stellio-app/stellio-plugins/tree/main/plugins/gcode-viewer'}) == 'https://raw.githubusercontent.com/stellio-app/stellio-plugins/main/plugins/gcode-viewer/plugin.json'
    assert p.manifest_url({'homepage': 'https://github.com/ana/meteo'}) == 'https://raw.githubusercontent.com/ana/meteo/HEAD/plugin.json'
    assert p.manifest_url({'homepage': 'https://exemple.org/x'}) == '' and p.manifest_url({'manifest': 'https://exemple.org/p.json'}) == 'https://exemple.org/p.json'
    raw = 'https://raw.githubusercontent.com/ana/meteo/HEAD/plugin.json'
    cat = {'plugins': [{'id': 'meteo', 'name': 'Météo', 'version': '1', 'url': 'https://github.com/ana/meteo/a.zip', 'sha256': 'a' * 64, 'description': 'ancienne copie', 'homepage': 'https://github.com/ana/meteo'},
                       {'id': 'autre', 'name': 'Autre', 'version': '1', 'url': 'https://x.example/a.zip', 'sha256': 'b' * 64, 'description': 'repli catalogue', 'homepage': 'https://github.com/ana/autre'}]}
    pj = {'id': 'meteo', 'description': {'fr': 'Prévisions sur le plateau', 'en': 'Forecast on the plate', 'xx': 'ignoré'}}
    def fake(url, m, timeout=15):
        if url == 'https://x.example/c.json': return json.dumps(cat).encode()
        if url == raw: return json.dumps(pj).encode()
        raise ValueError('introuvable')
    monkeypatch.setattr(p, 'http_get', fake)
    def ask(lang, **kw): return {e['id']: e['description'] for e in cl.post('/api/plugins/catalog', json=dict({'url': 'https://x.example/c.json', 'lang': lang}, **kw)).get_json()['plugins']}
    assert ask('fr') == {'meteo': 'Prévisions sur le plateau', 'autre': 'repli catalogue'}       # GitHub d'abord, copie du catalogue en repli
    assert ask('de')['meteo'] == 'Forecast on the plate'
    pj['description'] = {'en': 'Updated'}
    assert ask('en')['meteo'] == 'Forecast on the plate'                                         # lecture mise en cache...
    assert ask('en', refresh=True)['meteo'] == 'Updated'                                         # ...jusqu'à « Actualiser »
    m, err = p.validate_manifest({'id': 'tt', 'name': 'T', 'version': '1', 'api': 1, 'entry': 'main.py', 'description': {'fr': 'a', 'en': 'b'}})
    assert err is None and m['description'] == 'b' and m['description_i18n']['fr'] == 'a'
