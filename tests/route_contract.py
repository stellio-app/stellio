"""Inventaire statique des routes (main.py, modules/, plugins intégrés) : sert aux tests de non-régression pendant la modularisation.
Régénérer l'instantané :  python tests/route_contract.py --update"""
import ast, glob, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'routes_snapshot.txt')


def _files():
    return [os.path.join(ROOT, 'main.py')] + sorted(glob.glob(os.path.join(ROOT, 'modules', '*.py'))) + sorted(glob.glob(os.path.join(ROOT, 'bundled_plugins', '*', '*.py')))


def collect():
    out = set()
    for path in _files():
        try:
            tree = ast.parse(open(path, encoding='utf-8').read())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for d in node.decorator_list:
                    if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr == 'route' and d.args and isinstance(d.args[0], ast.Constant):
                        ms = ['GET']
                        for k in d.keywords:
                            if k.arg == 'methods':
                                try:
                                    ms = list(ast.literal_eval(k.value))
                                except Exception:
                                    pass
                        out.update(f"{m} {d.args[0].value}" for m in ms)
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '_ROUTES' for t in node.targets):
                try:
                    for row in ast.literal_eval(node.value):
                        out.update(f"{m} {row[0]}" for m in row[1])
                except Exception:
                    pass
    return out


def load_snapshot():
    return {l.strip() for l in open(SNAP, encoding='utf-8') if l.strip() and not l.startswith('#')}


if __name__ == '__main__':
    if '--update' in sys.argv:
        with open(SNAP, 'w', encoding='utf-8') as f:
            f.write('# Routes connues (METHODE chemin). Une route retirée casse test_route_contract ; régénérer : python tests/route_contract.py --update\n')
            f.write('\n'.join(sorted(collect())) + '\n')
    print(len(collect()))
