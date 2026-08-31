#!/usr/bin/env python3
"""
check_deps.py — Vérification ET correction automatique des dépendances Python
de Stellio. SOURCE DE VÉRITÉ UNIQUE de la liste des modules requis.

Pourquoi ce fichier existe
--------------------------
Avant, cette liste + cette logique de vérification vivaient UNIQUEMENT dans
main.py, et stellio_manager.bat faisait sa propre vérification, beaucoup
plus faible, en parallèle (juste `import module`, sans vérifier qu'il
exposait bien ce qui est réellement utilisé). Résultat concret : le paquet
PyPI "websocket" (obsolète, sans rapport) s'installe sous le même nom de
module que "websocket-client" (celui qu'il faut). `import websocket`
réussit très bien avec les deux, donc le .bat rapportait [OK] alors que
`WebSocketApp` était absent — Creality et Elegoo étaient cassés dans l'EXE
livré, sans qu'aucune étape du build ne le détecte.

En centralisant la liste + le contrôle "en profondeur" (import réel +
vérification d'un attribut/classe réellement utilisé dans le code) ICI,
main.py (au runtime, source de vérité si présente à côté de lui) et
stellio_manager.bat (au build, via `python check_deps.py --fix`) utilisent
exactement la même définition. Il n'y a plus qu'un seul endroit à tenir à
jour quand une dépendance change.

Utilisation en CLI (par stellio_manager.bat) :
    python check_deps.py                    # vérifie seulement, exit 0/1
    python check_deps.py --fix               # vérifie + corrige, exit 0/1
    python check_deps.py --fix --telegram    # + vérifie aussi telethon

Utilisation en import (par main.py) :
    from check_deps import (
        REQUIRED_MODULES, deep_check_module, auto_install_missing_modules,
        check_required_modules,
    )
"""

import sys
import os
import subprocess
import importlib
import importlib.util
import argparse

# Sur Windows, la sortie standard redirigee/capturee (comme le fait
# launcher.py via subprocess) utilise l'encodage ANSI de la console
# (souvent cp1252), pas UTF-8 — les emojis (✅ ❌) plantent alors avec
# UnicodeEncodeError, MEME QUAND tous les modules sont corrects, en plein
# milieu du dernier message de succes. Meme bug racine que le
# "'charmap' codec can't encode character" deja vu ailleurs dans main.py.
# On force UTF-8 explicitement des le depart pour eviter ca partout.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _safe_print(*args, **kwargs):
    """Remplace print() comme valeur par defaut de 'log' dans ce module.
    Le reconfigure() ci-dessus regle le cas normal, mais si jamais un
    environnement echappe quand meme (ancien Python sans reconfigure,
    flux deja ferme, etc.), on ne veut JAMAIS qu'un simple message de log
    fasse planter une verification de dependances par ailleurs reussie —
    on retente alors en remplaçant les caracteres non encodables plutot
    que de lever une exception.
    """
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        safe_args = [
            a.encode(sys.stdout.encoding or "ascii", errors="replace").decode(sys.stdout.encoding or "ascii")
            if isinstance(a, str) else a
            for a in args
        ]
        print(*safe_args, **kwargs)


# ============================================
# 📦 MODULES PYTHON REQUIS PAR STELLIO — TOUS OBLIGATOIRES
# ============================================
# (nom_import_exact, nom_pip, attribut_attendu_ou_None, paquets_pip_en_conflit_ou_None)
#
# nom_import_exact : le module (ou sous-module) réellement importé quelque
#   part dans le code — pas juste le paquet racine, pour que le check
#   porte sur ce qui est vraiment utilisé (ex: "paho.mqtt.client", pas
#   juste "paho").
# attribut_attendu : nom d'un attribut/fonction/classe que ce module DOIT
#   exposer, vérifié après import. Sans ça, un "import réussi" ne prouve
#   pas grand-chose : le cas réel qui a motivé cette vérification est le
#   paquet PyPI "websocket" (obsolète, sans rapport) qui s'installe sous le
#   même nom de module que "websocket-client" — l'import de "websocket"
#   réussit très bien, mais WebSocketApp n'existe pas dessus.
# paquets_en_conflit : si non-None, ces paquets pip sont désinstallés AVANT
#   de réinstaller nom_pip, pour les cas comme websocket/websocket-client
#   où le simple fait de réinstaller par-dessus ne suffit pas forcément.
#
# Chaque attribut ci-dessous a été vérifié contre l'usage réel dans le
# code (grep), pas deviné — pour ne jamais faire échouer à tort un module
# correctement installé.
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

# Modules optionnels, requis uniquement pour la variante Telegram.
# Ajoutés à la vérification via --telegram (CLI) ou telegram=True (import).
TELEGRAM_MODULES = [
    ("telethon", "telethon", "TelegramClient", None),
]


def find_owning_packages(top_level_import_name):
    """Retourne les paquets pip qui fournissent RÉELLEMENT ce nom de module
    en ce moment, d'après les métadonnées d'installation — plutôt que de se
    fier à une liste de collisions connues à l'avance (utile ici : la liste
    "conflicting" de REQUIRED_MODULES ne couvre que le cas
    websocket/websocket-client déjà rencontré, alors qu'une autre collision
    de nom, non anticipée, doit être corrigeable de la même façon)."""
    try:
        import importlib.metadata as importlib_metadata
        mapping = importlib_metadata.packages_distributions()
        return list(mapping.get(top_level_import_name, []))
    except Exception:
        return []


def deep_check_module(import_name, expected_attr):
    """Tente un import RÉEL (pas juste find_spec — ça ne détecterait ni les
    erreurs d'import, ni les bibliothèques partagées manquantes type OSMesa,
    ni un mauvais paquet installé sous le même nom), puis vérifie la
    présence de l'attribut attendu si spécifié. Retourne (ok, raison)."""
    try:
        mod = importlib.import_module(import_name)
    except Exception as e:
        return False, f"échec d'import ({e})"
    if expected_attr and not hasattr(mod, expected_attr):
        return False, f"importé mais '{expected_attr}' absent (mauvais paquet installé sous ce nom ?)"
    return True, None


def auto_install_missing_modules(modules=None, python_executable=None, log=_safe_print):
    """Vérification ULTRA COMPLÈTE des modules requis — tous obligatoires,
    aucun optionnel. Pour chacun : import réel + vérification de signature
    (pas juste "le paquet existe sur le disque"). Tout ce qui échoue est
    automatiquement réinstallé (avec désinstallation préalable des paquets
    en conflit, connus ou détectés dynamiquement), puis RE-vérifié de la
    même façon après installation.

    Retourne (all_ok: bool, still_broken: list[(import_name, pip_name, reason)]).
    N'appelle jamais sys.exit() — c'est à l'appelant (main.py en runtime,
    check_deps.py en CLI) de décider quoi faire d'un échec persistant.
    """
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

        # Un module "importé mais attribut manquant" signifie qu'un AUTRE
        # paquet occupe ce nom — on identifie précisément lequel (plutôt
        # que de se limiter à la liste "conflicting" connue à l'avance) et
        # on le désinstalle avant de réinstaller le bon, pour n'importe
        # quelle collision, même une qu'on n'a jamais rencontrée.
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
        # Un module déjà importé une première fois (même en échec partiel)
        # reste en cache dans sys.modules : on force sa relecture pour que
        # la re-vérification ci-dessous porte bien sur le fichier fraîchement
        # installé, pas sur une version partiellement chargée en mémoire.
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
    """Rapport de diagnostic (version incluse) sur l'état de tous les
    modules requis, sans tenter de corriger quoi que ce soit — utilisé pour
    un rapport purement informatif (ex : log runtime dans un exe packagé où
    pip n'est pas utilisable). Utilise le même check profond (import réel +
    attribut attendu), pas juste find_spec."""
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
