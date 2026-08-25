#!/usr/bin/env python3
import os
import sys
import multiprocessing  
from pathlib import Path
import runpy
import logging
from logging.handlers import RotatingFileHandler

def _setup_early_env() -> Path:
    base = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    app_dir = base / "app"
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))
    return app_dir

app_dir = _setup_early_env()
# ---------------------------------------------------------

def _app_dir() -> Path:
    base = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    return base / "app"


def _setup_bootstrap_logger(app_dir: Path) -> logging.Logger:
    log_dir = app_dir.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("stellio.launcher")
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(
        log_dir / "launcher.log", maxBytes=2_000_000, backupCount=2, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)-8s %(message)s"))
    logger.addHandler(handler)
    return logger


def _show_fatal_error(message: str) -> None:
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, "Stellio — Erreur au demarrage", 0x10)
    except Exception:
        print(message, file=sys.stderr)


_PRELOAD_MODULES = [
    "sqlite3", "ssl", "hashlib", "tkinter", "tkinter.ttk", "webbrowser",
    "difflib", "multiprocessing", "concurrent.futures", "secrets", "shlex",
    "calendar",
    "flask", "werkzeug", "waitress", "webview", "imageio", "trimesh",
    "pyrender", "OpenGL", "OpenGL.GL", "numpy", "PIL", "PIL.Image",
    "matplotlib", "mpl_toolkits.mplot3d", "mpl_toolkits.mplot3d.art3d",
    "fast_simplification", "pymeshfix", "shapely", "rectpack",
    "smbclient", "smbprotocol", "paho.mqtt.client", "requests",
    "cryptography", "cryptography.hazmat.primitives.ciphers", "rarfile",
    "py7zr", "defusedxml", "defusedxml.ElementTree", "nest_asyncio",
    "psutil", "packaging", "packaging.version", "qrcode", "websocket",
    "flashforge",
]


def _try_import(module_name: str):
    try:
        __import__(module_name)
        return module_name, None
    except Exception as e:
        return module_name, e


def _preload_dependencies(log) -> None:
    if os.environ.get("STELLIO_DIAG_PRELOAD", "").strip().lower() not in ("1", "true", "yes"):
        log("[PRELOAD] Verification des dependances ignoree (demarrage plus rapide). "
            "Definir STELLIO_DIAG_PRELOAD=1 pour la reactiver en cas de probleme d'installation.")
        return

    modules = list(_PRELOAD_MODULES)
    if os.environ.get("STELLIO_TELEGRAM_VARIANT", "").strip().lower() in ("1", "true", "yes"):
        modules.append("telethon")

    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for module_name, err in pool.map(_try_import, modules):
            if err is not None:
                log(f"[PRELOAD] ⚠️ {module_name} indisponible a l'import : {err}")



def main() -> int:
    app_dir = _app_dir()
    logger = _setup_bootstrap_logger(app_dir)
    log = logger.info

    main_py = app_dir / "main.py"
    if not main_py.exists():
        _show_fatal_error(f"main.py introuvable dans {app_dir}.\nInstallation corrompue.")
        return 1

    log("=== Demarrage de Stellio (launcher, sans runtime Python separe) ===")
    log(f"app_dir : {app_dir}")

    launcher_exe = sys.executable if getattr(sys, "frozen", False) else str(Path(__file__).resolve())
    os.environ["STELLIO_LAUNCHER_EXE"] = launcher_exe

    sys.path.insert(0, str(app_dir))
    os.chdir(str(app_dir))

    _preload_dependencies(log)

    log("Lancement de main.py (in-process, meme interpreteur que le launcher)...")
    try:
        runpy.run_path(str(main_py), run_name="stellio_main")
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
        log(f"main.py a demande une sortie explicite (code {code})")
        return code
    except Exception as e:
        logger.exception("Erreur fatale dans main.py")
        _show_fatal_error(
            "Stellio a rencontre une erreur fatale au demarrage :\n"
            f"{e}\n\nVoir logs\\launcher.log pour le detail complet."
        )
        return 1

    log("main.py termine normalement")
    return 0


if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    sys.exit(main())
