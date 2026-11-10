"""Chargeur de tests : extrait de main.py les fonctions/constantes voulues SANS importer le module
(main.py installe des dépendances et démarre des services à l'import)."""
import ast, os, sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(ROOT, 'main.py')


def load_from_main(names, extra_ns=None):
    src = open(MAIN, encoding='utf-8').read()
    tree = ast.parse(src)
    want, parts = set(names), []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in want:
            parts.append(ast.get_source_segment(src, node)); want.discard(node.name)
        elif isinstance(node, ast.Assign):
            ids = {t.id for t in node.targets if isinstance(t, ast.Name)}
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
