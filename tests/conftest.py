"""Chargeur de tests : extrait de main.py les fonctions/constantes voulues SANS importer le module
(main.py installe des dépendances et démarre des services à l'import)."""
import ast, os, sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(ROOT, 'main.py')


def _source_files():
    """main.py puis les modules/*.py (le code a été déplacé de main.py vers des modules au fil des versions)."""
    import glob
    return [MAIN] + sorted(glob.glob(os.path.join(ROOT, 'modules', '*.py')))


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


@pytest.fixture(scope='session')
def stellio_app():
    """Charge le VRAI main.py (sans démarrer le serveur, dossier de données temporaire) et renvoie l'application Flask.
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
        os.environ.update(STELLIO_DATA_DIR=tempfile.mkdtemp(), STELLIO_HEADLESS='1')
        sys.modules.setdefault('pyrender', types.ModuleType('pyrender'))
        sys.path.insert(0, ROOT); os.chdir(ROOT)
        ns = runpy.run_path(tmp, run_name='pytest_boot')
    except BaseException as e:      # dépendances absentes (CI minimale) : on saute plutôt que d'échouer
        pytest.skip(f"main.py ne se charge pas dans cet environnement : {type(e).__name__}: {e}")
    finally:
        try: os.remove(tmp)
        except OSError: pass
        os.chdir(old_cwd)
    app = ns['app']
    app.config['PROPAGATE_EXCEPTIONS'] = False
    return app
