#!/usr/bin/env python3

import os
import sys
import runpy
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


def _app_dir() -> Path:
    base = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) \
        else Path(__file__).resolve().parent
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


def _preload_dependencies(log) -> None:
    try:
        import sqlite3  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ sqlite3 indisponible a l'import : {e}")
    try:
        import ssl  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ ssl indisponible a l'import : {e}")
    try:
        import hashlib  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ hashlib indisponible a l'import : {e}")
    try:
        import tkinter  
        from tkinter import ttk  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ tkinter/ttk indisponible a l'import : {e}")

    try:
        import webbrowser  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ webbrowser indisponible a l'import : {e}")
    try:
        import difflib  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ difflib indisponible a l'import : {e}")
    try:
        import multiprocessing  
        import concurrent.futures  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ multiprocessing/concurrent.futures indisponible a l'import : {e}")
    try:
        import secrets  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ secrets indisponible a l'import : {e}")
    try:
        import shlex  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ shlex indisponible a l'import : {e}")
    try:
        import calendar  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ calendar indisponible a l'import : {e}")

    # --- dependances tierces (requirements.txt) ---
    try:
        import flask  
        import werkzeug  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ flask/werkzeug indisponible a l'import : {e}")
    try:
        import waitress  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ waitress indisponible a l'import : {e}")
    try:
        import webview  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ webview (pywebview) indisponible a l'import : {e}")
    try:
        import imageio  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ imageio indisponible a l'import : {e}")
    try:
        import trimesh  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ trimesh indisponible a l'import : {e}")
    try:
        import pyrender  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ pyrender indisponible a l'import : {e}")
    try:
        import OpenGL  
        import OpenGL.GL  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ OpenGL (PyOpenGL) indisponible a l'import : {e}")
    try:
        import numpy  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ numpy indisponible a l'import : {e}")
    try:
        import PIL  
        import PIL.Image  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ PIL (Pillow) indisponible a l'import : {e}")
    try:
        import matplotlib 
    except Exception as e:
        log(f"[PRELOAD] ⚠️ matplotlib indisponible a l'import : {e}")
    try:
        import mpl_toolkits  
        import mpl_toolkits.mplot3d  
        import mpl_toolkits.mplot3d.art3d  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ mpl_toolkits.mplot3d indisponible a l'import : {e}")
    try:
        import fast_simplification  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ fast_simplification indisponible a l'import : {e}")
    try:
        import pymeshfix 
    except Exception as e:
        log(f"[PRELOAD] ⚠️ pymeshfix indisponible a l'import : {e}")
    try:
        import shapely  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ shapely indisponible a l'import : {e}")
    try:
        import rectpack  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ rectpack indisponible a l'import : {e}")
    try:
        import smbclient  
        import smbprotocol  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ smbclient/smbprotocol indisponible a l'import : {e}")
    try:
        import paho.mqtt.client 
    except Exception as e:
        log(f"[PRELOAD] ⚠️ paho-mqtt indisponible a l'import : {e}")
    try:
        import requests  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ requests indisponible a l'import : {e}")
    try:
        import cryptography  
        from cryptography.hazmat.primitives.ciphers import Cipher  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ cryptography indisponible a l'import : {e}")
    try:
        import rarfile  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ rarfile indisponible a l'import : {e}")
    try:
        import py7zr  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ py7zr indisponible a l'import : {e}")
    try:
        import defusedxml  
        import defusedxml.ElementTree  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ defusedxml indisponible a l'import : {e}")
    try:
        import nest_asyncio  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ nest_asyncio indisponible a l'import : {e}")
    try:
        import psutil  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ psutil indisponible a l'import : {e}")
    try:
        import packaging  
        import packaging.version  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ packaging indisponible a l'import : {e}")
    try:
        import qrcode  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ qrcode indisponible a l'import : {e}")
    try:
        import websocket  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ websocket-client indisponible a l'import : {e}")
    try:
        import flashforge  
    except Exception as e:
        log(f"[PRELOAD] ⚠️ flashforge-python-api indisponible a l'import : {e}")

    if os.environ.get("STELLIO_TELEGRAM_VARIANT", "").strip().lower() in ("1", "true", "yes"):
        try:
            import telethon  
        except Exception as e:
            log(f"[PRELOAD] ⚠️ telethon indisponible a l'import : {e}")


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
    sys.exit(main())
