import re
import os
"""1.1.7 — Atelier avancé : branchement de l'interface (route, script, bouton, i18n) et cohérence des routes appelées."""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rd = lambda *p: open(os.path.join(ROOT, *p), encoding='utf-8').read()


def test_branchement():
    main, html, js = rd('main.py'), rd('interface', 'index.html'), rd('interface', 'suite.js')
    assert "@app.route('/suite.js')" in main and '<script src="suite.js">' in html and 'data-suite-tab="jobs"' in html and 'id="page-suite"' in html and 'data-page="suite"' in html
    from modules import plugin_host
    assert 'sharing' in {pid for pid, _d, m in plugin_host.manifests() if {'library_sync', 'community'} <= set(m['host']['modules'])}      # chargés par le plugin intégré « sharing »
    for lg in ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja'):
        d = json.loads(rd('languages', f'{lg}.json'))
        assert d['suite.title'] and all(d.get('suite.tab_' + t) for t in ('jobs', 'db', 'audit', 'team', 'compat', 'organize', 'diff', 'similar', 'plugins', 'sync', 'plate', 'community', 'fab', 'sessions', 'gcode', 'licenses', 'part', 'check', 'needs', 'admin'))


def test_les_routes_appelees_par_le_panneau_existent():
    """Chaque URL de suite.js doit correspondre à une route déclarée dans un module (sinon un onglet resterait mort)."""
    js = rd('interface', 'suite.js')
    rules = []
    import glob
    for f in glob.glob(os.path.join(ROOT, 'modules', '*.py')) + glob.glob(os.path.join(ROOT, 'bundled_plugins', '*', '*.py')):      # + modules des plugins intégrés
        rules += re.findall(r"\(\s*'(/api/[^']+)'\s*,\s*\[", open(f, encoding='utf-8').read())
    rules += re.findall(r"@app\.route\('(/api/[^']+)'", rd('main.py'))        # routes de main.py (miniatures, sources) utilisées par le sélecteur de modèle
    pats = [re.compile('^' + re.sub(r'<[^>]+>', '[^/]+', r) + '$') for r in rules]
    urls = set(re.findall(r"[`'](/api/[A-Za-z0-9_/\-\.${}()]+)", js))
    assert len(urls) >= 20
    for u in urls:
        u = re.sub(r'\$\{[^}]*\}', '1', u).split('?')[0]
        assert any(p.match(u) for p in pats), u


def test_colonnes_devis_tolerent_la_course_au_premier_lancement():
    """Deux requêtes /api/quotes simultanées sur une base neuve : le second ALTER TABLE ne doit pas provoquer de 500 (« duplicate column »)."""
    src = open(__import__('conftest').mod_path('pro_quotes'), encoding='utf-8').read()
    i = src.index('def _ensure_quote_columns')
    body = src[i:i + 2500]
    assert "duplicate column" in body and 'except sqlite3.OperationalError' in body


def test_interface_revient_a_la_connexion_si_session_revoquee():
    js = rd('interface', 'script.js')
    assert "session_revoked" in js[:1500] and 'location.reload()' in js[:1500]


def test_buttons_moved_out_of_toolbar():
    import re
    html = open('interface/index.html', encoding='utf-8').read()
    js = open('interface/script.js', encoding='utf-8').read()
    # Atelier avancé : dans le groupe Outils, plus dans la barre de la bibliothèque
    # Chaque outil de l'Atelier avancé a son entrée dans le volet, rangée dans sa catégorie ; « Administration » regroupe les outils d'exploitation
    cats = {m.group(1): m.group(2) for m in re.finditer(r'<button[^>]*data-suite-tab="(\w+)"[^>]*data-cat="(\w+)"', html)}
    assert cats == {'organize': 'library', 'collections': 'library', 'diff': 'library', 'similar': 'library', 'licenses': 'library', 'part': 'library', 'compat': 'print', 'check': 'print', 'gcode': 'print', 'needs': 'filament',
                    'plate': 'tools', 'sync': 'tools', 'fab': 'tools', 'jobs': 'admin', 'db': 'admin', 'admin': 'admin'}, cats
    assert 'data-rail="admin"' in html and "'admin'" in js and 'id="suite-btn"' not in html and 'id="assistant-btn"' not in html
    for tab in cats:                                                              # chaque entrée a son interrupteur dans les réglages de la barre latérale
        assert f'data-nav-id="suite-{tab}"' in html
    # Assistant : première puce des collections, seulement si l'IA est activée
    i = js.index('function renderSmartCollections')
    body = js[i:i + 2500]
    assert 'window.aiEnabled' in body and 'el.innerHTML = ai + chips' in body
    j = js.index('function applyAiEnabledUI')
    assert 'renderSmartCollections' in js[j:j + 300]


def test_page_et_selecteur():
    html, js, script = rd('interface', 'index.html'), rd('interface', 'suite.js'), rd('interface', 'script.js')
    assert "window.StellioSuite?.onShow()" in script                       # la navigation appelle la page
    assert "modal-suite'" not in js.replace("modal-suite-picker", "")      # plus de popup « modal-suite »
    for f in ('su-cp', 'su-dp', 'su-sp', 'su-pp', 'su-ck', 'su-lp'):        # chaque champ « chemin » propose la bibliothèque
        assert f"pfield('{f}'" in js
    assert "mfield('su-pp'" in js and "mfield('su-cf'" in js                # plateau et communauté : sélection multiple
    # la langue a sa propre section, juste après Apparence
    a = html.index('data-i18n="settings.appearance"'); b = html.index('fa-language"></i> <span data-i18n="settings.language"')
    assert a < b and 'id="language-selector"' in html[b:b + 1500] and html.count('id="language-selector"') == 1


def test_bouton_redemarrer_sur_la_page_des_plugins():
    import json, os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    js = open(os.path.join(root, 'interface', 'suite.js'), encoding='utf-8').read()
    assert 'id="su-restart"' in js and "/api/app/quit" in js and 'restart: true' in js
    for lg in ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja'):
        d = json.load(open(os.path.join(root, 'languages', lg + '.json'), encoding='utf-8'))
        assert all(d.get('suite.' + k) for k in ('restart_btn', 'restart_confirm', 'restart_wait')), lg


def test_widgets_des_plugins_sont_masques_sans_le_plugin():
    import os, re
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    html = open(os.path.join(root, 'interface', 'index.html'), encoding='utf-8').read()
    attendu = {'instances': 'sharing', 'quotes': 'stellio-pro', 'timelapses': 'timelapse', 'mqtt': 'mqtt'}
    for wid, plugin in attendu.items():
        tag = re.search(r'<div[^>]*data-widget-id="%s"[^>]*>' % wid, html)
        assert tag and 'data-host-plugin="%s"' % plugin in tag.group(0), wid


def test_categorie_administration_filtre_et_surbrillance_unique():
    """Régression : sans la règle CSS de filtrage, le volet « Administration » affichait TOUTES les entrées ; et toutes les entrées de l'Atelier
    (même page « suite ») s'allumaient ensemble. Une seule doit être active."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    css = open(os.path.join(root, 'interface', 'style.css'), encoding='utf-8').read()
    js = open(os.path.join(root, 'interface', 'script.js'), encoding='utf-8').read()
    assert '.sidebar[data-cat="admin"] .nav-btn[data-cat]:not([data-cat="admin"])' in css
    assert "btn.dataset.suiteTab ? el === btn : el.dataset.page === page" in js


def test_bigprint_est_range_dans_la_categorie_plugins():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    html = open(os.path.join(root, 'interface', 'index.html'), encoding='utf-8').read()
    m = re.search(r'<button[^>]*data-page="bigprint"[^>]*>', html)
    assert m and 'data-cat="tools"' in m.group(0) and 'data-host-plugin="bigprint"' in m.group(0)


def test_menu_administration_cache_par_defaut_sans_instance_reliee():
    html = open(os.path.join(ROOT, 'interface', 'index.html'), encoding='utf-8').read()
    css = open(os.path.join(ROOT, 'interface', 'style.css'), encoding='utf-8').read()
    for nid in ('suite-jobs', 'suite-db', 'suite-admin'):
        assert re.search(r'<button[^>]*data-nav-id="%s"[^>]*data-admin-net' % nid, html), nid
        assert re.search(r'<div class="nav-toggle-row"[^>]*data-nav-id="%s"[^>]*data-admin-net' % nid, html), nid
    assert 'html:not([data-net-ok]) [data-admin-net]' in css


def test_rail_ne_lit_pas_le_style_calcule_des_categories_inactives():
    js = open(os.path.join(ROOT, 'interface', 'script.js'), encoding='utf-8').read()
    i = js.index('const _any = [...sidebar.querySelectorAll(')
    ligne = js[i:js.index('\n', i)]
    assert 'getComputedStyle' not in ligne and "data-admin-net" in ligne      # le CSS du panneau masque les autres catégories : ne pas s'y fier


def test_annuler_changement_parametres_est_dans_l_en_tete():
    html = rd('interface', 'index.html'); css = rd('interface', 'style.css')
    hr = html[html.index('<div class="header-right">'):]
    assert hr.index('id="settings-undo-btn"') < hr.index('id="spool-header-material"')          # dans l'en-tête, pas dans la colonne
    assert 'settings-undo-banner' not in html
    assert 'html.settings-undo-ready body:has(#page-settings.active) .settings-undo-btn' in css


def test_centre_de_notifications_tout_voir_et_page_complete():
    html = rd('interface', 'index.html'); js = rd('interface', 'script.js'); su = rd('interface', 'suite.js')
    assert 'id="notif-panel-footer"' in html and 'openAllNotifications()' in html and 'window.openAllNotifications' in js
    assert 'TABS.notifications' in su and "'/api/notifications/all?'" in su
    for cat in ('filament_low', 'restock', 'parts', 'print', 'maintenance'):
        assert "'" + cat + "'" in su
    fr = json.loads(rd('languages', 'fr.json'))
    assert fr['notif.see_all'] == 'Tout voir' and fr['suite.tab_notifications'] and fr['suite.ntf_filament_low'] == 'Filament faible' and fr['suite.ntf_restock'] == 'Filament à recommander'


def test_rubriques_des_notifications_filament_faible_et_a_recommander():
    src = rd('main.py'); i = src.index('def _notif_category'); ns = {}
    exec(src[i:src.index('@app.route', i)], ns)
    cat = ns['_notif_category']
    assert cat('low_stock', 'low_stock_spoolman_12') == 'filament_low' and cat('low_stock', 'restock_pla_blanc') == 'restock'
    assert cat('low_stock', 'part_low_4') == 'parts' and cat('print_finished', 'print_finished_1_9') == 'print' and cat('maintenance', 'drying_due_x_1') == 'maintenance'
    assert cat('warning', 'parts_low:3:1') == 'parts' and cat('info', 'tariff:offpeak:x') == 'other' and cat('info', None) == 'other'


def test_liens_bigprint_aux_couleurs_de_l_application():
    css = rd('interface', 'style.css')
    assert '.bp-credit a' in css and 'color: var(--accent)' in css[css.index('.bp-credit a'):css.index('.bp-credit a') + 200]


def test_menu_collections_dans_bibliotheque():
    html = rd('interface', 'index.html')
    assert re.search(r'<button[^>]*data-nav-id="suite-collections"[^>]*data-suite-tab="collections"[^>]*data-cat="library"', html)
    assert 'data-nav-id="suite-collections"' in html[html.index('nav-toggle-row'):] and "TABS.collections" in rd('interface', 'suite.js')
    assert json.loads(rd('languages', 'fr.json'))['suite.tab_collections'] == 'Collections'


def test_champs_des_pages_notifications_et_collections_au_style_de_l_application():
    su = rd('interface', 'suite.js')
    for ident in ('su-nq', 'su-cname'):
        tag = re.search(r'<input[^>]*id="%s"[^>]*>' % ident, su).group(0)
        assert 'class="settings-select"' in tag, ident              # « settings-input » n'a pas de style dans cette page : champ blanc


def test_source_des_notifications_spoolman_tigertag_et_autres():
    src = rd('main.py'); i = src.index('def _notif_source'); ns = {}
    exec(src[i:src.index('@app.route', i)], ns)
    s = ns['_notif_source']
    assert s('low_stock', 'low_stock_spoolman_12') == 'Spoolman' and s('low_stock', 'low_stock_tigertag_abc') == 'TigerTag'
    assert s('maintenance', 'drying_due_tigertag_3') == 'TigerTag' and s('print_failed', 'obico:12') == 'Obico'
    assert s('warning', 'parts_low:3:1') == 'Stellio Pro' and s('warning', 'quote_portal:4:accepted') == 'Stellio Pro'
    assert s('info', 'lic:expired:ab12') == '@license' and s('info', 'digest:daily:2026-11-20') == '@digest'
    assert s('info', 'model_update_makerworld_55_2026') == 'Makerworld' and s('info', 'restock_pla') == 'Stellio' and s('info', None) == 'Stellio'


def test_source_dialogs_sit_above_the_sources_list_and_work_indicator_exists():
    import re, pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    css = (root / 'interface/style.css').read_text(encoding='utf-8')
    m = re.search(r'#modal-select-type[^{]*\{\s*z-index:\s*(\d+)', css)
    z = re.search(r'#accord-backdrop[^}]*z-index:\s*(\d+)', css) ; pop = re.search(r'position: fixed; inset: 0; margin: auto; z-index: (\d+)', css)
    assert m and pop and int(m.group(1)) > int(pop.group(1)) > int(z.group(1))   # « Ajouter une source » passe devant la liste des sources (popup de réglages)
    js = (root / 'interface/suite.js').read_text(encoding='utf-8')
    assert 'su-work-auto' in js and 'su-btn-busy' in js   # repère visuel pendant un calcul (Diff 3D, etc.)


def test_project_picker_quantity_field_keeps_its_size_inside_checkbox_rows():
    import pathlib
    css = (pathlib.Path(__file__).resolve().parent.parent / 'interface/style.css').read_text(encoding='utf-8')
    assert '.checkbox-label input.qty-needed' in css and 'width: 52px; height: auto' in css


def test_every_dialog_opened_from_a_settings_popup_sits_above_it():
    import pathlib
    css = (pathlib.Path(__file__).resolve().parent.parent / 'interface/style.css').read_text(encoding='utf-8')
    assert 'body:has(.accord-section.accord-popup) .modal:not(#modal-confirm)' in css


def test_needs_and_fab_tabs_follow_their_plugin():
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    js = (root / 'interface/suite.js').read_text(encoding='utf-8')
    html = (root / 'interface/index.html').read_text(encoding='utf-8')
    assert "needs: 'stellio-pro'" in js and "fab: 'ai-assistant'" in js
    assert 'data-host-plugin="stellio-pro" data-nav-id="suite-needs"' in html and 'data-host-plugin="ai-assistant" data-nav-id="suite-fab"' in html


def test_workshop_mode_never_overflows_a_portrait_phone():
    import pathlib
    css = (pathlib.Path(__file__).resolve().parent.parent / 'interface/style.css').read_text(encoding='utf-8')
    assert 'grid-template-columns: minmax(0, 1fr); }' in css and 'minmax(min(320px, 100%), 1fr)' in css
    assert '.workshop-overlay {' in css and 'overflow-x: hidden' in css
