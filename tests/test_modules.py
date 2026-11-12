"""Modules séparés de main.py (share_link, order_tracking, …) : branchement et services requis.
Les modules sont générés par tools/split_module.py ; chacun expose _REQUIRED, _ROUTES et init(globals())."""
import ast, importlib.util, os, re
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _discover():
    src = open(os.path.join(ROOT, 'main.py'), encoding='utf-8').read()
    return sorted(set(re.findall(r'^(?:globals\(\)\.update\()?(\w+)\.init\(globals\(\)\)', src, re.M)))


MODULES = _discover()


def _load(name):
    spec = importlib.util.spec_from_file_location(name + '_under_test', os.path.join(ROOT, 'modules', name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except ImportError as e:      # dépendance absente de l'environnement de test (ex. requests en CI minimale)
        pytest.skip(f'{name} : dépendance manquante ({e})')
    return mod


def test_discovery_finds_every_split_module():
    assert {'print_session', 'share_link', 'order_tracking'} <= set(MODULES)


def test_modules_package_lists_every_module_file():
    """modules/__init__.py (ALL) = fichiers du dossier = modules branchés dans main.py."""
    files = sorted(f[:-3] for f in os.listdir(os.path.join(ROOT, 'modules')) if f.endswith('.py') and f != '__init__.py')
    spec = importlib.util.spec_from_file_location('modules_pkg_under_test', os.path.join(ROOT, 'modules', '__init__.py'))
    pkg = importlib.util.module_from_spec(spec); spec.loader.exec_module(pkg)
    assert sorted(pkg.ALL) == files == sorted(MODULES)


@pytest.mark.parametrize('name', MODULES)
def test_init_registers_every_route(name):
    flask = pytest.importorskip('flask')
    mod = _load(name)
    with pytest.raises(RuntimeError):
        mod.init({}, routes=False)
    app = flask.Flask('t')
    ns = {n: (lambda *a, **k: None) for n in mod._REQUIRED}
    ns['DATA_DIR'] = '/tmp'
    ns.update(app=app, login_required=lambda f: f)
    mod.init(dict(ns, DATA_DIR='/tmp'))
    rules = {r.rule for r in app.url_map.iter_rules()}
    for rule, methods, fname, decos in mod._ROUTES:
        assert rule in rules, (name, rule)


@pytest.mark.parametrize('name', MODULES)
def test_main_provides_every_service_before_init(name, main_src):
    tree = ast.parse(main_src)
    call = next(n.lineno for n in tree.body if isinstance(n, ast.Expr) and f'{name}.init' in ast.get_source_segment(main_src, n))
    defined = set()

    def walk(nodes):
        for n in nodes:
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
                defined.add(n.name)
            elif isinstance(n, ast.Assign):
                defined.update(t.id for t in n.targets if isinstance(t, ast.Name))
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                defined.update((a.asname or a.name).split('.')[0] for a in n.names)
            elif isinstance(n, (ast.Try, ast.If, ast.With, ast.For, ast.While)):
                for fld in ('body', 'orelse', 'finalbody'):
                    walk(getattr(n, fld, []))
                for h in getattr(n, 'handlers', []):
                    walk(h.body)

    walk([n for n in tree.body if n.lineno < call])
    assert not [x for x in _load(name)._REQUIRED if x not in defined]


@pytest.mark.parametrize('name', MODULES)
def test_module_defines_no_route_decorator_left(name):
    """Les routes passent par _ROUTES : aucun @app.route ne doit rester dans le module (il n'y a pas d'app à l'import)."""
    assert '@app.route' not in open(os.path.join(ROOT, 'modules', name + '.py'), encoding='utf-8').read()
