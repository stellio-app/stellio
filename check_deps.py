#!/usr/bin/env python3
import sys
import os
import subprocess
import importlib
import importlib.util
import argparse

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        safe_args = [
            a.encode(sys.stdout.encoding or "ascii", errors="replace").decode(sys.stdout.encoding or "ascii")
            if isinstance(a, str) else a
            for a in args
        ]
        print(*safe_args, **kwargs)


REQUIRED_MODULES = [
    ("flask",                                  "Flask",                  "Flask",              None),
    ("werkzeug",                                "Werkzeug",               None,                 None),
    ("cryptography.hazmat.primitives.ciphers",  "cryptography",           "Cipher",             None),
    ("numpy",                                   "numpy",                  "array",              None),
    ("PIL.Image",                               "Pillow",                 "open",               None),
    ("trimesh",                                 "trimesh",                "load",               None),
    ("requests",                                "requests",               "get",                None),
    ("packaging.version",                       "packaging",              "parse",              None),
    ("nest_asyncio",                            "nest_asyncio",           "apply",              None),
    ("webview",                                 "pywebview",              "create_window",      None),
    ("smbclient",                               "smbprotocol",            "open_file",          None),
    ("rarfile",                                 "rarfile",                "RarFile",            None),
    ("waitress",                                "waitress",               "serve",              None),
    ("pymeshfix",                               "pymeshfix",              "MeshFix",            None),
    ("defusedxml.ElementTree",                  "defusedxml",             "parse",              None),
    ("paho.mqtt.client",                        "paho-mqtt",              "Client",             None),
    ("rectpack",                                "rectpack",               "newPacker",          None),
    ("shapely.affinity",                        "shapely",                None,                 None),
    ("py7zr",                                   "py7zr",                  "SevenZipFile",       None),
    ("fast_simplification",                     "fast-simplification",    None,                 None),
    ("pyrender",                                "pyrender",               "OffscreenRenderer",  None),
    ("matplotlib",                              "matplotlib",             "use",                None),
    ("psutil",                                  "psutil",                 "virtual_memory",     None),
    ("qrcode",                                  "qrcode",                 "QRCode",             None),
    ("websocket",                               "websocket-client",       "WebSocketApp",       ["websocket", "websocket-client"]),
    ("flashforge",                              "flashforge-python-api",  "FlashForgeClient",   None),
]

TELEGRAM_MODULES = [
    ("telethon", "telethon", "TelegramClient", None),
]


def find_owning_packages(top_level_import_name):
    try:
        import importlib.metadata as importlib_metadata
        mapping = importlib_metadata.packages_distributions()
        return list(mapping.get(top_level_import_name, []))
    except Exception:
        return []


def deep_check_module(import_name, expected_attr):
    try:
        mod = importlib.import_module(import_name)
    except Exception as e:
        return False, f"échec d'import ({e})"
    if expected_attr and not hasattr(mod, expected_attr):
        return False, f"importé mais '{expected_attr}' absent (mauvais paquet installé sous ce nom ?)"
    return True, None


def auto_install_missing_modules(modules=None, python_executable=None, log=_safe_print):
    modules = REQUIRED_MODULES if modules is None else modules
    python_executable = python_executable or sys.executable

    log("[MODULES] === Vérification complète (import réel + signature) de tous les modules requis ===")
    problems = []
    for import_name, pip_name, expected_attr, conflicting in modules:
        ok, reason = deep_check_module(import_name, expected_attr)
        log(f"[MODULES]   {import_name:<42} -> {'OK' if ok else 'PROBLÈME : ' + reason}")
        if not ok:
            problems.append((import_name, pip_name, expected_attr, conflicting, reason))

    if not problems:
        log("[MODULES] ✅ Tous les modules requis sont présents et fonctionnels")
        return True, []

    log(f"[MODULES] {len(problems)} module(s) manquant(s) ou cassé(s) — correction automatique en cours...")
    still_broken = []
    for import_name, pip_name, expected_attr, conflicting, reason in problems:
        top_level = import_name.split('.')[0]

        wrong_module_installed = "attribut" in reason
        bad_packages = set(conflicting or [])
        if wrong_module_installed:
            bad_packages.update(find_owning_packages(top_level))
        bad_packages.discard(pip_name)

        for bad_pkg in bad_packages:
            log(f"[MODULES]   Désinstallation de '{bad_pkg}' (occupe le nom '{top_level}')...")
            subprocess.run(
                [python_executable, '-m', 'pip', 'uninstall', '-y', bad_pkg],
                capture_output=True, timeout=120
            )

        force_reinstall = bool(bad_packages) or wrong_module_installed
        base_cmd = [python_executable, '-m', 'pip', 'install', '--disable-pip-version-check', '--no-input']
        base_cmd += ['--force-reinstall'] if force_reinstall else ['--upgrade']
        base_cmd += [pip_name]

        installed_ok = False
        for extra_args in ([], ['--break-system-packages']):
            try:
                subprocess.run(base_cmd + extra_args, check=True, timeout=900)
                installed_ok = True
                break
            except Exception:
                continue

        if not installed_ok:
            still_broken.append((import_name, pip_name, "échec de la commande pip install"))
            continue

        importlib.invalidate_caches()
        for mod_name in list(sys.modules):
            if mod_name == top_level or mod_name.startswith(top_level + '.'):
                del sys.modules[mod_name]

        ok, reason = deep_check_module(import_name, expected_attr)
        if ok:
            log(f"[MODULES] ✅ {pip_name} corrigé")
        else:
            still_broken.append((import_name, pip_name, reason))

    if still_broken:
        log("[MODULES] ❌ Modules toujours en échec après tentative de correction automatique :")
        for import_name, pip_name, reason in still_broken:
            log(f"[MODULES]     - {import_name} ({pip_name}) : {reason}")
        return False, still_broken

    log("[MODULES] ✅ Tous les modules corrigés avec succès")
    return True, []


def check_required_modules(modules=None, log=_safe_print, include_versions=True):
    modules = REQUIRED_MODULES if modules is None else modules
    try:
        import importlib.metadata as importlib_metadata
    except ImportError:
        importlib_metadata = None

    results = []
    for import_name, pip_name, expected_attr, _conflicting in modules:
        ok, reason = deep_check_module(import_name, expected_attr)

        version_str = None
        if ok and include_versions and importlib_metadata is not None:
            try:
                version_str = importlib_metadata.version(pip_name)
            except Exception:
                version_str = "?"

        results.append({
            "import": import_name,
            "pip": pip_name,
            "installed": ok,
            "reason": reason,
            "version": version_str,
        })
    return results


def _cli_main():
    parser = argparse.ArgumentParser(
        description="Vérifie (et optionnellement corrige) les dépendances Python de Stellio."
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Tente de corriger automatiquement (uninstall du mauvais paquet + réinstallation du bon)."
    )
    parser.add_argument(
        "--telegram", action="store_true",
        help="Inclut aussi les dépendances de la variante Telegram (telethon)."
    )
    args = parser.parse_args()

    modules = list(REQUIRED_MODULES)
    if args.telegram:
        modules += TELEGRAM_MODULES

    if args.fix:
        all_ok, still_broken = auto_install_missing_modules(modules=modules)
    else:
        results = check_required_modules(modules=modules)
        still_broken = [
            (r["import"], r["pip"], r["reason"]) for r in results if not r["installed"]
        ]
        all_ok = not still_broken
        for r in results:
            status = f"OK (v{r['version']})" if r["installed"] and r["version"] not in (None, "?") else (
                "OK" if r["installed"] else f"PROBLÈME ({r['reason']})"
            )
            _safe_print(f"[MODULES]   {r['import']:<42} -> {status}")

    if not all_ok:
        _safe_print("[MODULES] ❌ Au moins une dépendance manque ou ne fonctionne pas correctement.")
        sys.exit(1)

    _safe_print("[MODULES] ✅ Toutes les dépendances requises sont présentes et fonctionnelles.")
    sys.exit(0)


if __name__ == "__main__":
    _cli_main()
