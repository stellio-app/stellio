import ast, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
LANGS = ["fr", "en", "de", "es", "pt", "it", "zh", "ja"]


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


import re


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
    assert html.count('data-i18n="sosprint.ai_warning"') == 2          # enquête + résultat
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
