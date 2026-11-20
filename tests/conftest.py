"""Chargeur de tests : extrait de main.py les fonctions/constantes voulues SANS importer le module
(main.py installe des dépendances et démarre des services à l'import)."""
import ast, os, sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('STELLIO_ENABLE_PLUGINS', 'all')   # les tests exercent les routes des plugins intégrés (activés d'office ici)
os.environ.setdefault('STELLIO_THUMB_ISOLATE', '0')   # les tests de rendu appellent le rendu intégré ; l'isolation a ses propres tests
MAIN = os.path.join(ROOT, 'main.py')


import glob as _glob
for _d in sorted(_glob.glob(os.path.join(ROOT, 'bundled_plugins', '*'))):     # plugins intégrés : leurs modules et paquets s'importent comme en production
    if os.path.isfile(os.path.join(_d, 'plugin.json')) and _d not in sys.path:
        sys.path.append(_d)


def mod_path(name):
    """Chemin du fichier d'un module, qu'il soit dans modules/ ou dans un plugin intégré (bundled_plugins/<id>/)."""
    for p in [os.path.join(ROOT, 'modules', name + '.py')] + sorted(_glob.glob(os.path.join(ROOT, 'bundled_plugins', '*', name + '.py'))):
        if os.path.isfile(p):
            return p
    raise FileNotFoundError(name)


def _source_files():
    """main.py puis les modules/*.py et ceux des plugins intégrés (le code a été déplacé de main.py vers des modules au fil des versions)."""
    return [MAIN] + sorted(_glob.glob(os.path.join(ROOT, 'modules', '*.py'))) + sorted(_glob.glob(os.path.join(ROOT, 'bundled_plugins', '*', '*.py')))


def load_from_main(names, extra_ns=None):
    want, parts = set(names), []
    for path in _source_files():
        if not want:
            break
        src = open(path, encoding='utf-8').read()
        tree = ast.parse(src)
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in want:
                parts.append(ast.get_source_segment(src, node)); want.discard(node.name)
            elif isinstance(node, ast.Assign):
                ids = {t.id for t in node.targets if isinstance(t, ast.Name)}
                if path != MAIN and isinstance(node.value, ast.Constant) and node.value.value is None:
                    continue    # marqueur `nom = None` posé par init() dans les modules : pas la vraie définition
                if ids & want:
                    parts.append(ast.get_source_segment(src, node)); want -= ids
    assert not want, f"introuvable dans main.py : {sorted(want)}"
    ns = {'os': os, 'time': __import__('time'), **(extra_ns or {})}
    try:
        import numpy as np
        ns['np'] = np
    except ImportError:
        pass
    exec(compile('\n'.join(parts), 'main_slice', 'exec'), ns)
    return ns


@pytest.fixture(scope='session')
def root():
    return ROOT


@pytest.fixture(scope='session')
def main_src():
    return open(MAIN, encoding='utf-8').read()


def boot_main(data_dir=None, skip_on_error=True):
    """Charge le VRAI main.py (sans démarrer le serveur ; `data_dir` ou dossier temporaire) et renvoie son espace de noms.
    Même principe que tools/smoke_boot.py ; permet de tester les routes avec le client de test Flask."""
    import runpy, tempfile, types
    s = open(MAIN, encoding='utf-8').read()
    s = s.replace('        print("[MODULES] Stellio ne peut pas démarrer de façon fiable sans ces modules. Arrêt.")\n        sys.exit(1)', '        pass', 1)
    s = s.replace('            print("[MODULES] Stellio ne peut pas démarrer de façon fiable sans ces modules. Arrêt.")\n            sys.exit(1)', '            pass', 1)
    s = s.replace("def _deep_check_module(import_name, expected_attr):", "def _deep_check_module(import_name, expected_attr):\n    return True, ''\ndef _deep_check_module_orig(import_name, expected_attr):", 1)
    tmp = os.path.join(ROOT, '_pytest_main_tmp.py')
    open(tmp, 'w', encoding='utf-8').write(s)
    old_env, old_cwd = dict(os.environ), os.getcwd()
    try:
        os.environ.update(STELLIO_DATA_DIR=data_dir or tempfile.mkdtemp(), STELLIO_HEADLESS='1')
        sys.modules.setdefault('pyrender', types.ModuleType('pyrender'))
        sys.path.insert(0, ROOT); os.chdir(ROOT)
        ns = runpy.run_path(tmp, run_name='pytest_boot')
    except BaseException as e:      # dépendances absentes (CI minimale) : on saute plutôt que d'échouer
        if not skip_on_error:
            raise
        pytest.skip(f"main.py ne se charge pas dans cet environnement : {type(e).__name__}: {e}")
    finally:
        try: os.remove(tmp)
        except OSError: pass
        os.chdir(old_cwd)
    return ns


@pytest.fixture(scope='session')
def stellio_app():
    """L'application Flask du VRAI main.py (voir boot_main)."""
    app = boot_main()['app']
    app.config['PROPAGATE_EXCEPTIONS'] = False
    return app
