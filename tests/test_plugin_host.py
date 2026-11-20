"""Plugins intégrés (1.1.7) : manifestes, migration invisible depuis la 1.1.6, chargement à l'activation, refus des archives « host »."""
import json
import os
import sqlite3
import subprocess
import sys

import pytest

from conftest import ROOT
from modules import plugin_host as ph

LANGS = ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja')
A_EXTRAIRE = {'administration', 'bigprint', 'resin', 'usb-printers', 'timelapse', 'file-tools', 'plate-studio', 'push-notify', 'webhooks', 'digest', 'mqtt', 'obico', 'sharing', 'ai-assistant', 'ai-ollama', 'ai-openai', 'ai-anthropic', 'ai-gemini', 'spoolman', 'stellio-pro'}


@pytest.fixture(autouse=True)
def _sans_forcage(monkeypatch):
    monkeypatch.delenv('STELLIO_ENABLE_PLUGINS', raising=False)


def _conn(users=True, printers=(), tables=()):
    c = sqlite3.connect(':memory:')
    c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY)")
    c.execute("CREATE TABLE printers (id INTEGER PRIMARY KEY, type TEXT, config TEXT)")
    for t in tables:
        c.execute(f"CREATE TABLE {t} (id INTEGER PRIMARY KEY)")
        c.execute(f"INSERT INTO {t} (id) VALUES (1)")
    if users:
        c.execute("INSERT INTO users (id) VALUES (1)")
    for typ, cfg in printers:
        c.execute("INSERT INTO printers (type, config) VALUES (?, ?)", (typ, cfg))
    return c


def test_les_onze_plugins_sont_livres_avec_un_manifeste_complet():
    ms = {pid: m for pid, _d, m in ph.manifests()}
    assert set(ms) == A_EXTRAIRE
    for pid, m in ms.items():
        assert set(m['description']) >= set(LANGS), pid                         # une description dans chacune des 8 langues
        for mod in m['host']['modules']:
            assert any(os.path.isfile(os.path.join(ROOT, 'bundled_plugins', pid, mod + '.py')) for _ in [0]), (pid, mod)
        assert isinstance(m['host'].get('migrate'), dict) and m['host']['migrate'], pid


def test_installation_neuve_n_active_rien(tmp_path):
    done = ph.migrate({}, _conn(users=False), str(tmp_path), ph.existing_install({}, _conn(users=False)))
    assert done == [] and ph.read_state(str(tmp_path))['enabled'] == {}
    assert ph.read_state(str(tmp_path))['migrated'] == ph.STATE_VERSION
    assert {k for k, v in ph.features(str(tmp_path)).items() if v} == {'administration'}              # seul « Administration » est actif d'office


def test_migration_active_ce_que_l_utilisateur_avait_configure(tmp_path):
    """1.1.6 → 1.1.7 : MQTT activé, imprimante USB, webhooks créés, timelapse sur une imprimante… tout revient sans rien faire."""
    settings = {'mqtt_enabled': True, 'mqtt_host': 'broker.local', 'obico_enabled': True, 'digest_enabled': True, 'push_enabled': True, 'lang': 'fr', 'ai_enabled': True, 'ai_provider': 'openai'}
    conn = _conn(printers=[('usb_serial', '{}'), ('klipper', '{"timelapse": true}'), ('formlabs', '{}')], tables=['webhooks', 'share_links', 'quotes'])
    before = json.dumps(settings, sort_keys=True)
    done = ph.migrate(settings, conn, str(tmp_path), ph.existing_install(settings, conn))
    assert set(done) == {'mqtt', 'obico', 'digest', 'push-notify', 'webhooks', 'usb-printers', 'timelapse', 'resin',
                         'bigprint', 'file-tools', 'plate-studio', 'sharing', 'ai-assistant', 'ai-openai', 'stellio-pro'}                       # + les outils sans réglage, conservés tels quels
    assert json.dumps(settings, sort_keys=True) == before                                  # les réglages ne sont ni lus à la baisse ni réécrits
    ft = ph.features(str(tmp_path))
    assert all(ft[k] for k in done) and not ft['ai-ollama'] and not ft['ai-anthropic'] and not ft['ai-gemini']      # seul le fournisseur d'IA réellement choisi


def test_migration_ne_charge_pas_ce_qui_n_etait_pas_utilise(tmp_path):
    conn = _conn(printers=[('klipper', '{}')])
    done = ph.migrate({'lang': 'fr', 'mqtt_enabled': False, 'push_enabled': False}, conn, str(tmp_path), True)
    assert set(done) == {'bigprint', 'file-tools', 'plate-studio'}                         # outils sans réglage : conservés ; le reste reste absent
    ft = ph.features(str(tmp_path))
    assert ft['administration'] and not any(ft[k] for k in ('mqtt', 'obico', 'digest', 'push-notify', 'webhooks', 'usb-printers', 'timelapse', 'resin'))


def test_migration_une_seule_fois_et_choix_de_l_utilisateur_respecte(tmp_path):
    conn = _conn()
    ph.migrate({'mqtt_enabled': True, 'mqtt_host': 'b'}, conn, str(tmp_path), True)
    assert ph.is_enabled('mqtt', str(tmp_path))
    ph.set_enabled('mqtt', False, str(tmp_path))                                           # l'utilisateur le désactive…
    assert ph.migrate({'mqtt_enabled': True, 'mqtt_host': 'b'}, conn, str(tmp_path), True) == []      # …la migration ne repasse pas
    assert not ph.is_enabled('mqtt', str(tmp_path))


def test_dossiers_et_imprimantes_detectes(tmp_path):
    (tmp_path / 'timelapse').mkdir()
    (tmp_path / 'timelapse' / 'a.mp4').write_bytes(b'x')
    done = ph.migrate({}, _conn(printers=[('anycubic_photon', '{}')]), str(tmp_path), True)
    assert 'timelapse' in done and 'resin' in done


def test_activation_prend_effet_au_redemarrage(tmp_path, monkeypatch):
    monkeypatch.setattr(ph, '_LOADED', {})
    r = ph.set_enabled('obico', True, str(tmp_path))
    assert r == {'enabled': True, 'restart_required': True}
    with pytest.raises(KeyError):
        ph.set_enabled('inconnu', True, str(tmp_path))


def test_variable_d_environnement_force_l_activation(tmp_path, monkeypatch):
    monkeypatch.setenv('STELLIO_ENABLE_PLUGINS', 'mqtt, obico')
    assert ph.is_enabled('mqtt', str(tmp_path)) and ph.is_enabled('obico', str(tmp_path)) and not ph.is_enabled('digest', str(tmp_path))
    monkeypatch.setenv('STELLIO_ENABLE_PLUGINS', 'all')
    assert all(ph.features(str(tmp_path)).values())


def test_une_archive_ne_peut_pas_declarer_host_ni_prendre_un_identifiant_integre():
    from modules import plugins
    m, err = plugins.validate_manifest({'id': 'pirate', 'name': 'X', 'version': '1.0.0', 'api': 1, 'host': {'modules': ['os']}})
    assert m is None and 'host' in err
    import io, zipfile
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w') as z:
        z.writestr('plugin.json', json.dumps({'id': 'mqtt', 'name': 'Faux MQTT', 'version': '9.0.0', 'api': 1, 'entry': 'main.py', 'permissions': []}))
        z.writestr('main.py', 'print(1)')
    plugins._MAIN['DATA_DIR'] = None
    plugins.DATA_DIR = os.path.join(ROOT, '_tmp_plugins_host_test')
    try:
        with pytest.raises(ValueError, match='intégré'):
            plugins.install_bytes(b.getvalue())
    finally:
        import shutil
        shutil.rmtree(plugins.DATA_DIR, ignore_errors=True)


def test_le_coeur_n_importe_plus_le_code_des_plugins():
    """main.py n'importe ni n'initialise directement les modules extraits : tout passe par plugin_host."""
    main = open(os.path.join(ROOT, 'main.py'), encoding='utf-8').read()
    for mod in ('mqtt_publisher', 'obico', 'digest', 'push_notify', 'webhooks', 'timelapse', 'resin_inventory', 'resin_printers', 'usb_printers',
                'file_convert', 'merge_3mf', 'plate_studio', 'bigprint_tool', 'bigprint_i18n'):
        assert f'from modules import {mod}' not in main and f'{mod}.init(globals())' not in main, mod
        assert not os.path.exists(os.path.join(ROOT, 'modules', mod + '.py')), mod


# ── démarrage réel de main.py : 1.1.6 → 1.1.7 ────────────────────────────────────────────────────

_BOOT = """
import json, os, sys
sys.path.insert(0, %r)
import conftest
os.environ.pop('STELLIO_ENABLE_PLUGINS', None)
ns = conftest.boot_main(data_dir=sys.argv[2], skip_on_error=False)
mode = sys.argv[1]
if mode == 'seed':
    c = ns['app'].test_client()
    r = c.post('/api/auth/register', json={'username': 'romain', 'password': 'abcd1234', 'security_question_key': 'custom',
               'security_question_custom': 'Quel est le nom de mon premier test ?', 'security_answer': 'reponse'})
    assert r.status_code == 200, r.get_data()
    s = ns['load_settings']() or {}
    s.update(mqtt_enabled=True, mqtt_host='broker.local', mqtt_base='stellio', obico_enabled=True, obico_url='http://obico.local')
    ns['save_settings'](s)
    conn = ns['get_db']()
    conn.execute("INSERT INTO printers (user_id, name, type, ip) VALUES (1, 'Boite USB', 'usb_serial', 'COM3')")
    conn.commit(); conn.close()
rules = sorted(r.rule for r in ns['app'].url_map.iter_rules())
from modules import plugin_host as ph
print('RESULT' + json.dumps({'rules': rules, 'state': ph.read_state(sys.argv[2]), 'loaded': sorted(ph._LOADED),
                             'settings': {k: v for k, v in (ns['load_settings']() or {}).items() if k.startswith(('mqtt_', 'obico_'))}}))
"""


def _boot(mode, data_dir):
    p = subprocess.run([sys.executable, '-c', _BOOT % os.path.join(ROOT, 'tests'), mode, str(data_dir)], capture_output=True, text=True, timeout=240, cwd=ROOT)
    out = [l for l in p.stdout.splitlines() if l.startswith('RESULT')]
    assert out, (p.stdout[-800:], p.stderr[-1500:])
    return json.loads(out[-1][6:])


def test_demarrage_reel_installation_neuve_puis_mise_a_jour_depuis_la_116(tmp_path):
    pytest.importorskip('flask')
    # 1) installation neuve : seul « Administration » (actif d'office) est chargé, aucune route des autres plugins
    r = _boot('fresh', tmp_path)
    assert r['loaded'] == ['administration'] and r['state']['enabled'] == {} and '/api/admin/overview' in r['rules']
    assert '/api/bigprint/config' not in r['rules'] and '/api/mqtt/status' not in r['rules'] and '/api/plugins/features' in r['rules']
    assert not any(x in r['rules'] for x in ('/api/quotes', '/api/orders', '/api/tariff', '/api/clients', '/api/planning'))      # Stellio Pro : absent sur une installation neuve
    # 2) l'utilisateur d'une 1.1.6 : compte, MQTT et Obico renseignés, imprimante USB ; pas de fichier d'état des plugins intégrés
    _boot('seed', tmp_path)
    os.remove(os.path.join(str(tmp_path), 'plugins', '.host.json'))
    # 3) premier démarrage en 1.1.7 : tout est rechargé tout seul, réglages intacts
    r = _boot('upgrade', tmp_path)
    assert {'mqtt', 'obico', 'usb-printers', 'bigprint'} <= set(r['loaded'])
    assert '/api/mqtt/status' in r['rules'] and '/api/obico' in r['rules'] and '/api/bigprint/config' in r['rules']
    assert 'timelapse' not in r['loaded'] and '/api/digest/settings' not in r['rules']           # ce qui n'était pas utilisé reste absent
    assert r['settings']['mqtt_host'] == 'broker.local' and r['settings']['obico_url'] == 'http://obico.local' and r['settings']['mqtt_enabled'] is True


def test_api_builtin_renvoie_textes_dans_la_langue_demandee():
    """Régression : la description (dict par langue) s'affichait « [object Object] » ; le nom suit aussi la langue."""
    from modules import plugins
    for lg in LANGS:
        for pid, _d, m in ph.manifests():
            assert isinstance(plugins.pick_description(m, lg), str) and plugins.pick_description(m, lg), (pid, lg)
            assert m['name_i18n'][lg], (pid, lg)
    m = ph.manifest('mqtt')
    assert plugins.pick_description(m, 'de') == m['description']['de'] and plugins.pick_description(m, 'xx') == m['description']['en']


def test_aucune_mention_beta_pour_la_resine_et_les_imprimantes_usb():
    """La résine et l'USB ne sont plus présentés comme « bêta » : ni manifestes, ni interface, ni langues, ni documentation."""
    import re
    pat = re.compile(r'b[êe]ta|ベータ|测试版|🧪', re.I)
    fichiers = [os.path.join(ROOT, 'bundled_plugins', p, f) for p in ('resin', 'usb-printers') for f in os.listdir(os.path.join(ROOT, 'bundled_plugins', p))
                if f.endswith(('.json', '.py'))]
    fichiers += [os.path.join(ROOT, 'README.md'), os.path.join(ROOT, 'interface', 'index.html'), os.path.join(ROOT, 'interface', 'v113.js')]
    fichiers += [os.path.join(ROOT, 'docs', 'wiki', 'src', l + '.md') for l in LANGS] + [os.path.join(ROOT, 'docs', 'readme', f'README_{l}.md') for l in LANGS if l != 'en']
    for f in fichiers:
        for n, ligne in enumerate(open(f, encoding='utf-8'), 1):
            if pat.search(ligne) and 'diagnostic_export_hint' not in ligne and 'testeur' not in ligne and 'tester' not in ligne:
                assert False, f'{os.path.relpath(f, ROOT)}:{n} : {ligne.strip()[:120]}'


def test_migration_ia_fournisseur_choisi_et_assistant(tmp_path):
    """1.1.6 → 1.1.7 : IA activée → Assistant IA + le fournisseur réellement utilisé ; IA coupée → rien."""
    cas = {'ollama par défaut': ({'ai_enabled': True}, {'ai-assistant', 'ai-ollama'}),
           'ollama explicite': ({'ai_enabled': True, 'ai_provider': 'ollama'}, {'ai-assistant', 'ai-ollama'}),
           'claude': ({'ai_enabled': True, 'ai_provider': 'anthropic'}, {'ai-assistant', 'ai-anthropic'}),
           'gemini': ({'ai_enabled': True, 'ai_provider': 'gemini'}, {'ai-assistant', 'ai-gemini'}),
           'ia coupée': ({'ai_enabled': False, 'ai_provider': 'openai'}, set())}
    for nom, (st, attendu) in cas.items():
        d = tmp_path / nom.replace(' ', '_'); d.mkdir()
        done = set(ph.migrate(st, _conn(), str(d), True))
        assert {p for p in done if p.startswith('ai-')} == attendu, nom


def test_fournisseurs_d_ia_a_cle_d_api_reserves_a_l_edition_serveur(tmp_path):
    from modules import plugin_host as ph
    cloud = {'ai-openai', 'ai-anthropic', 'ai-gemini'}
    mans = {pid: m for pid, _d, m in ph.manifests()}
    assert cloud <= set(mans) and all(mans[p].get('server_only') for p in cloud)
    assert not mans['ai-ollama'].get('server_only')            # Ollama (local) reste dispo sous Windows
    ancien = dict(ph._MAIN)
    try:
        ph._MAIN['IS_SERVER_EDITION'] = False
        ph.write_state({'enabled': {p: True for p in cloud | {'ai-ollama'}}, 'migrated': ph.STATE_VERSION}, str(tmp_path))
        f = ph.features(str(tmp_path))
        assert not any(f[p] for p in cloud) and f['ai-ollama']
        assert not ph.is_enabled('ai-openai', str(tmp_path))
        import pytest
        with pytest.raises(PermissionError):
            ph.set_enabled('ai-gemini', True, str(tmp_path))
        ph._MAIN['IS_SERVER_EDITION'] = True
        assert all(ph.features(str(tmp_path))[p] for p in cloud)
    finally:
        ph._MAIN.clear(); ph._MAIN.update(ancien)


def test_mqtt_notifications_push_et_webhooks_reserves_a_l_edition_serveur(tmp_path):
    """Demande de l'utilisateur : ces trois fonctions n'existent que dans l'édition serveur (jamais proposées, activées ni chargées sous Windows)."""
    from modules import plugin_host as ph
    srv = {'mqtt', 'push-notify', 'webhooks'}
    mans = {pid: m for pid, _d, m in ph.manifests()}
    assert all(mans[p].get('server_only') for p in srv)
    ancien = dict(ph._MAIN)
    try:
        ph._MAIN['IS_SERVER_EDITION'] = False
        ph.write_state({'enabled': {p: True for p in srv}, 'migrated': ph.STATE_VERSION}, str(tmp_path))
        assert not any(ph.features(str(tmp_path))[p] for p in srv)
        ph._MAIN['IS_SERVER_EDITION'] = True
        assert all(ph.features(str(tmp_path))[p] for p in srv)
    finally:
        ph._MAIN.clear(); ph._MAIN.update(ancien)


def test_la_migration_couvre_tous_les_types_d_imprimantes_gerees_par_les_plugins():
    """Régression trouvée en vérifiant la migration 1.1.6 → 1.1.7 : `chitu_sdcp` (Elegoo Saturn/Mars…) manquait dans la règle de la résine,
    ces imprimantes auraient disparu de l'interface après la mise à jour. Les types sont lus dans les modules : plus de liste à tenir à la main."""
    import re
    for pid, module, const in (('resin', 'resin_printers.py', 'RESIN_TYPES'), ('usb-printers', 'usb_printers.py', 'USB_TYPE')):
        src = open(os.path.join(ROOT, 'bundled_plugins', pid, module), encoding='utf-8').read()
        val = eval(re.search(const + r"\s*=\s*(\(.*?\)|'[a-z_]+')", src).group(1))
        types = {val} if isinstance(val, str) else set(val)
        assert types <= set(ph.manifest(pid)['host']['migrate']['printer_types']), (pid, types)
