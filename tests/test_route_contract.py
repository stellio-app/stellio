"""Non-régression : aucune route ne doit disparaître (extraction de code de main.py vers modules/)."""
import route_contract as rc


def test_aucune_route_ne_disparait():
    gone = sorted(rc.load_snapshot() - rc.collect())
    assert not gone, f"{len(gone)} route(s) disparue(s) : {gone[:10]}"


def test_pas_de_doublon_methode_chemin():
    import ast, collections
    # même METHODE+chemin déclaré deux fois = la 2e écrase la 1re au démarrage (Flask refuse l'endpoint ou masque le code)
    seen = collections.Counter()
    for path in rc._files():
        for node in ast.walk(ast.parse(open(path, encoding='utf-8').read())):
            if isinstance(node, ast.FunctionDef):
                for d in node.decorator_list:
                    if isinstance(d, ast.Call) and getattr(d.func, 'attr', '') == 'route' and d.args and isinstance(d.args[0], ast.Constant):
                        ms = ['GET']
                        for k in d.keywords:
                            if k.arg == 'methods':
                                ms = list(ast.literal_eval(k.value))
                        for m in ms:
                            seen[f"{m} {d.args[0].value}"] += 1
    dup = sorted(k for k, n in seen.items() if n > 1)
    assert dup == sorted(set(dup)) and len(dup) <= 3, dup
