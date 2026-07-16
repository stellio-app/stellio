#!/usr/bin/env python3
import sys
import os
import importlib.util

def _ensure_bundled_dependencies():
    import nest_asyncio
    nest_asyncio.apply()
    import os
    import sys
    if sys.platform != 'win32':
        os.environ['PYOPENGL_PLATFORM'] = 'osmesa'
        os.environ['PYRENDER_OFFSCREEN'] = '1'
    import sqlite3
    import hashlib
    import json
    import subprocess
    import secrets
    import datetime
    import logging
    from logging.handlers import RotatingFileHandler
    import smtplib
    import trimesh
    import numpy as np
    import smbclient
    import smbprotocol
    from smbprotocol.exceptions import SMBOSError
    from PIL import Image, ImageDraw, ImageFont
    import base64
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from pathlib import Path
    from functools import wraps
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders
    from flask import Flask, request, jsonify, session, send_file
    from flask import Response
    import pyrender
    import trimesh.transformations as tra
    import io
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import padding
    import zipfile
    import rarfile
    import tarfile
    import shutil
    import xml.etree.ElementTree as ET
    import time
    import tempfile
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
    import queue
    import requests
    import re
    from bs4 import BeautifulSoup
    from urllib.parse import urlparse, unquote, urljoin
    import asyncio
    import threading
    import glob
    import atexit  
    import ctypes
    import webview
    import webbrowser
    import threading, time, urllib.request, json
    import tkinter as tk
    from tkinter import ttk
    import qrcode
    import io, base64
    import socket


def get_app_dir():
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'app')


def main():
    _ensure_bundled_dependencies()

    app_dir = get_app_dir()
    main_path = os.path.join(app_dir, 'main.py')

    if not os.path.isfile(main_path):
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                f"Fichier introuvable :\n{main_path}\n\n"
                f"Le dossier 'app' doit se trouver à côté de Stellio.exe.",
                "Stellio — Erreur de démarrage",
                0x10
            )
        except Exception:
            print(f"[Launcher] main.py introuvable : {main_path}")
        sys.exit(1)

    sys.path.insert(0, app_dir)
    os.chdir(app_dir)

    spec = importlib.util.spec_from_file_location("stellio_main", main_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["stellio_main"] = module
    spec.loader.exec_module(module)


if __name__ == "__main__":
    main()