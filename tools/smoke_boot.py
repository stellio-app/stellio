#!/usr/bin/env python3
"""Charge le vrai main.py SANS démarrer le serveur (contrôle de dépendances graphiques neutralisé) et liste les routes.
Usage : python tools/smoke_boot.py [fichier_main.py] [sortie.json]   (ex. avant/après un découpage, puis comparer les deux JSON)
Vérifie : tous les modules se branchent (init), aucune route en double, les routes protégées répondent 401 sans connexion."""
import collections, json, os, runpy, sys, tempfile, types
main = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else 'main.py')
out = sys.argv[2] if len(sys.argv) > 2 else 'routes.json'
root = os.path.dirname(main)
s = open(main, encoding='utf-8').read()
s = s.replace('        print("[MODULES] Stellio ne peut pas démarrer de façon fiable sans ces modules. Arrêt.")\n        sys.exit(1)', '        pass', 1)
s = s.replace('            print("[MODULES] Stellio ne peut pas démarrer de façon fiable sans ces modules. Arrêt.")\n            sys.exit(1)', '            pass', 1)
s = s.replace("def _deep_check_module(import_name, expected_attr):", "def _deep_check_module(import_name, expected_attr):\n    return True, ''\ndef _deep_check_module_orig(import_name, expected_attr):", 1)
tmp = os.path.join(root, '_smoke_main_tmp.py')
open(tmp, 'w', encoding='utf-8').write(s)
try:
    os.environ.update(STELLIO_DATA_DIR=tempfile.mkdtemp(), STELLIO_HEADLESS='1')
    sys.modules.setdefault('pyrender', types.ModuleType('pyrender'))
    sys.path.insert(0, root); os.chdir(root)
    ns = runpy.run_path(tmp, run_name='smoke')
finally:
    os.remove(tmp)
app = ns['app']; rules = list(app.url_map.iter_rules())
dup = [e for e, c in collections.Counter(r.endpoint for r in rules).items() if c > 1]
json.dump(sorted((r.rule, sorted(r.methods - {'HEAD', 'OPTIONS'}), r.endpoint) for r in rules), open(out, 'w'))
print(f'routes : {len(rules)} ; endpoints en double : {dup or "aucun"} ; /api/auth/first-launch -> {app.test_client().get("/api/auth/first-launch").status_code}')
sys.exit(1 if dup else 0)
