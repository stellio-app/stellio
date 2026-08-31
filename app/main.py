#!/usr/bin/env python3
"""
Stellio - Gestionnaire de fichiers 3D (STL, 3MF, OBJ)
Version avec Lazy Loading, téléchargements multiples + annulation + persistance des thèmes + analyse 3D + favoris + Décompression Automatique
Moteur de miniature : pyrender (rendu 3D professionnel) + fallback logo
✅ CORRECTIFS : Fix pyrender ambient_light + Telegram auth async robuste + Reconnexion auto + Intégration Cults3D complète
"""
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
from flask import Flask, request, jsonify, session, send_file
import pyrender
import trimesh.transformations as tra
import io
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import base64
import zipfile
import rarfile
import tarfile
import shutil
import xml.etree.ElementTree as ET
import time
import tempfile
from concurrent.futures import ThreadPoolExecutor
import queue
import requests
import re
from urllib.parse import urlparse, unquote, urljoin
import asyncio
import threading
import glob
import atexit
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, FloodWaitError

thumb_generation_queue = queue.Queue()
metadata_generation_queue = queue.Queue()
is_generation_running = False
ignored_files_cache = set()
thumbnail_executor = ThreadPoolExecutor(max_workers=2)
scan_lock = threading.Lock()

def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def get_data_path():
    if os.name == 'nt':
        appdata = os.environ.get('APPDATA', str(Path.home() / 'AppData' / 'Roaming'))
        data_dir = Path(appdata) / 'Stellio'
    else:
        data_dir = Path.home() / '.stellio'
    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir)

BASE_DIR = get_base_path()
DATA_DIR = get_data_path()
DB_PATH = os.path.join(DATA_DIR, "stellio.db")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
THUMBNAILS_DIR = os.path.join(DATA_DIR, "thumbnails")
CACHE_FILE = os.path.join(DATA_DIR, "file_cache.json")
CACHE_DURATION = 18000
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(THUMBNAILS_DIR, exist_ok=True)

KEY_FILE = os.path.join(DATA_DIR, 'encryption.key')
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'rb') as f:
        ENCRYPTION_KEY = f.read()
    with open(KEY_FILE.replace('.key', '.iv'), 'rb') as f:
        IV = f.read()
else:
    ENCRYPTION_KEY = os.urandom(32)
    IV = os.urandom(16)
    with open(KEY_FILE, 'wb') as f:
        f.write(ENCRYPTION_KEY)
    with open(KEY_FILE.replace('.key', '.iv'), 'wb') as f:
        f.write(IV)
    os.chmod(KEY_FILE, 0o600)
    os.chmod(KEY_FILE.replace('.key', '.iv'), 0o600)

def _setup_rar_tool():
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    unrar_paths = [
        os.path.join(base_dir, 'bin', 'UnRAR.exe'),
        os.path.join(base_dir, 'tools', 'UnRAR.exe'),
        os.path.join(base_dir, 'UnRAR.exe')
    ]
    for path in unrar_paths:
        if os.path.exists(path):
            rarfile.UNRAR_TOOL = path
            print(f"[RAR] UnRAR configuré: {path}")
            return True
    print("[RAR] UnRAR.exe non trouvé. L'extraction .rar sera désactivée.")
    return False
_setup_rar_tool()

SETTINGS_FILE = os.path.join(DATA_DIR, "app_settings.json")

_settings_cache = {}
def load_settings():
    global _settings_cache
    if not _settings_cache:
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                _settings_cache = json.load(f)
        except: _settings_cache = {"theme": "dark", "fabricant": "stellio"}
    return _settings_cache

def save_settings(settings):
    global _settings_cache
    _settings_cache = settings
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

active_downloads = {}
scan_state = {
    'new_batch': [],
    'status': 'idle',
    'found': 0,
    'total_scanned': 0
}
scan_lock = threading.Lock()

# ============================================
# 💾 SAUVEGARDE UNIQUE DU CACHE À LA FERMETURE
# ============================================
_cache_saved = False  # ✅ Évite les sauvegardes multiples

def save_cache_on_exit():
    """Sauvegarde le cache UNE SEULE FOIS à la fermeture"""
    global _cache_saved
    if _cache_saved:
        return
    _cache_saved = True
    
    print("[CACHE] 💾 Sauvegarde de fermeture...")
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            cache['timestamp'] = time.time()
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            print("[CACHE] ✅ Cache sauvegardé avec succès")
    except Exception as e:
        print(f"[CACHE] ❌ Erreur sauvegarde: {e}")

atexit.register(save_cache_on_exit)

def encrypt_password(password):
    """Chiffre un mot de passe de manière sécurisée"""
    try:
        if not password:
            return None
        padding_length = 16 - (len(password) % 16)
        padded_password = password.encode('utf-8') + bytes([padding_length] * padding_length)
        cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.CFB(IV), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(padded_password) + encryptor.finalize()
        return encrypted.hex()
    except Exception as e:
        app.logger.error(f"Erreur encrypt_password: {e}")
        return None

def decrypt_password(encrypted_data):
    """Déchiffre un mot de passe avec gestion d'erreur complète"""
    try:
        if not encrypted_data:
            return None
        if not isinstance(encrypted_data, (bytes, bytearray)):
            try:
                return str(encrypted_data)
            except:
                pass
        if isinstance(encrypted_data, str):
            try:
                encrypted_bytes = bytes.fromhex(encrypted_data)
            except ValueError:
                encrypted_bytes = encrypted_data.encode('latin-1')
        else:
            encrypted_bytes = encrypted_data

        cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.CFB(IV), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted_bytes) + decryptor.finalize()

        if len(decrypted) > 0:
            padding_length = decrypted[-1]
            if 0 < padding_length <= 16:
                if all(b == padding_length for b in decrypted[-padding_length:]):
                    decrypted = decrypted[:-padding_length]
            try:
                return decrypted.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    return decrypted.decode('latin-1')
                except:
                    app.logger.warning("Impossible de décoder, retour hex")
                    return decrypted.hex()
        else:
            return None
    except Exception as e:
        app.logger.error(f"❌ Erreur decrypt_password: {e}")
        return None

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # 🚀 Optimisations perf SQLite
    c.execute("PRAGMA journal_mode=WAL;")
    c.execute("PRAGMA synchronous=NORMAL;")
    c.execute("PRAGMA cache_size=-2000;") # 2MB cache en RAM
    c.execute("PRAGMA temp_store=MEMORY;")
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT DEFAULT '',
        reset_code TEXT,
        reset_expiry TIMESTAMP,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        path TEXT NOT NULL,
        config TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(user_id, name)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS slicer_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        file_path TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        color TEXT DEFAULT '#4ea1d3'
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS file_tags (
        file_path TEXT NOT NULL,
        tag_id INTEGER NOT NULL,
        FOREIGN KEY (tag_id) REFERENCES tags(id),
        PRIMARY KEY (file_path, tag_id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS account_credentials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        platform TEXT NOT NULL,
        email TEXT,
        password_encrypted TEXT,
        api_key TEXT,
        session_cookies TEXT,
        telegram_session TEXT,
        telegram_api_id TEXT,
        telegram_api_hash TEXT,
        last_login TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(user_id, platform)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS favorites (
        file_path TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )""")

def migrate_account_credentials():
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("PRAGMA table_info(account_credentials)")
        columns = [col[1] for col in c.fetchall()]
        new_cols = {
            'api_key': 'ALTER TABLE account_credentials ADD COLUMN api_key TEXT',
            'telegram_session': 'ALTER TABLE account_credentials ADD COLUMN telegram_session TEXT',
            'telegram_api_id': 'ALTER TABLE account_credentials ADD COLUMN telegram_api_id TEXT',
            'telegram_api_hash': 'ALTER TABLE account_credentials ADD COLUMN telegram_api_hash TEXT'
        }
        for col_name, sql in new_cols.items():
            if col_name not in columns:
                try:
                    c.execute(sql)
                except sqlite3.OperationalError:
                    pass
        if 'email' not in columns and 'username' in columns:
            c.execute("SELECT * FROM account_credentials")
            old_data = c.fetchall()
            c.execute("DROP TABLE account_credentials")
            c.execute("""
                CREATE TABLE account_credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    platform TEXT NOT NULL,
                    email TEXT,
                    password_encrypted TEXT,
                    api_key TEXT,
                    session_cookies TEXT,
                    telegram_session TEXT,
                    telegram_api_id TEXT,
                    telegram_api_hash TEXT,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE(user_id, platform)
                )
            """)
            for row in old_data:
                if len(row) >= 4:
                    c.execute("""
                        INSERT INTO account_credentials (id, user_id, platform, email, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (row[0], row[1], row[2], row[3], row[-1] if len(row) > 3 else None))
            conn.commit()
    except Exception as e:
        print(f"[ERROR] Migration: {e}")
        conn.rollback()
    finally:
        conn.close()

init_db()
migrate_account_credentials()

def migrate_printers_table():
    """Crée la table printers si elle n'existe pas"""
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("""CREATE TABLE IF NOT EXISTS printers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            ip TEXT NOT NULL,
            api_key TEXT,
            config TEXT,
            is_connected BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")
        conn.commit()
    except Exception as e:
        print(f"[Migrate Printers] Erreur: {e}")
    finally:
        conn.close()
init_db()
migrate_account_credentials()
migrate_printers_table()
# =============================================================================
# 🖨️ GESTION DES IMPRIMANTES (OCTOPRINT / KLIPPER / BAMBULAB)
# =============================================================================
try:
    import paho.mqtt.client as mqtt
    HAS_MQTT = True
except ImportError:
    HAS_MQTT = False
    print("[WARN] paho-mqtt non installé. BambuLab ne fonctionnera pas.")

class PrinterManager:
    def __init__(self):
        self.clients = {} # Stocke les connexions actives

    def connect_printer(self, db_row):
        """Teste la connexion et retourne le statut"""
        pid = db_row['id']
        ptype = db_row['type'] # octoprint, klipper, bambu
        ip = db_row['ip']
        api_key = db_row['api_key']
        
        try:
            if ptype == 'octoprint':
                # Test via HTTP
                url = f"http://{ip}/api/connection"
                headers = {'X-Api-Key': api_key}
                r = requests.get(url, headers=headers, timeout=5)
                return r.status_code == 200
                
            elif ptype == 'klipper':
                # Test via Moonraker (Port 7125 par défaut)
                port = db_row['config'].get('port', '7125') if db_row['config'] else '7125'
                url = f"http://{ip}:{port}/server/info"
                r = requests.get(url, timeout=5)
                return r.status_code == 200
                
            elif ptype == 'bambu':
                # Test via MQTT
                if not HAS_MQTT: return False
                port = 1883
                user = db_row['config'].get('user', 'bblp') if db_row['config'] else 'bblp'
                password = api_key
                
                client = mqtt.Client()
                client.username_pw_set(user, password)
                client.connect(ip, port, 60)
                client.disconnect() # Juste pour tester
                return True
                
        except Exception as e:
            print(f"[Printer] Erreur connexion {ptype} ({ip}): {e}")
            return False
        return False

    def get_status(self, db_row):
        """Récupère le statut COMPLET de l'imprimante (températures, temps, etc.)"""
        ptype = db_row['type']
        ip = db_row['ip']
        api_key = db_row['api_key']
        
        default_result = {
            'status': 'unknown', 'progress': 0, 'file': '',
            'temps': {'extruder': {'current': 0, 'target': 0}, 
                      'bed': {'current': 0, 'target': 0},
                      'chamber': {'current': 0, 'target': 0}},
            'time': {'elapsed': 0, 'remaining': 0, 'total': 0},
            'last_print': {'filename': '', 'duration': 0, 'finished_at': ''}
        }
        
        try:
            if ptype == 'octoprint':
                headers = {'X-Api-Key': api_key}
                
                # 🔥 Températures
                r_temp = requests.get(f"http://{ip}/api/printer", headers=headers, timeout=3).json()
                temps = r_temp.get('temperature', {})
                extruder = temps.get('tool0', {})
                bed = temps.get('bed', {})
                chamber = temps.get('chamber', {})
                
                # ⏱️ Job en cours
                r_job = requests.get(f"http://{ip}/api/job", headers=headers, timeout=3).json()
                state = r_job.get('state', 'Offline').lower()
                progress = r_job.get('progress', {}) or {}
                job = r_job.get('job', {}) or {}
                
                completion = progress.get('completion', 0) or 0
                print_time = progress.get('printTime', 0) or 0
                print_time_left = progress.get('printTimeLeft', 0) or 0
                
                # Mapping du statut OctoPrint
                if 'printing' in state:
                    status = 'printing'
                elif 'operational' in state or 'ready' in state:
                    status = 'idle'
                elif 'error' in state or 'closed' in state:
                    status = 'error'
                else:
                    status = state
                
                return {
                    'status': status,
                    'progress': round(completion, 1),
                    'file': job.get('file', {}).get('name', ''),
                    'temps': {
                        'extruder': {'current': round(extruder.get('actual', 0), 1),
                                     'target': round(extruder.get('target', 0), 1)},
                        'bed': {'current': round(bed.get('actual', 0), 1),
                                'target': round(bed.get('target', 0), 1)},
                        'chamber': {'current': round(chamber.get('actual', 0), 1),
                                    'target': round(chamber.get('target', 0), 1)}
                    },
                    'time': {
                        'elapsed': int(print_time),
                        'remaining': int(print_time_left),
                        'total': int(print_time + print_time_left) if print_time > 0 else 0
                    },
                    'last_print': self._get_octoprint_last_print(ip, api_key)
                }
                
            elif ptype == 'klipper':
                port = db_row['config'].get('port', '7125') if isinstance(db_row['config'], dict) else '7125'
                base = f"http://{ip}:{port}"
                
                try:
                    # ✅ CORRECTION : Séparer les objets par des & au lieu de virgules
                    # Moonraker attend : ?extruder&heater_bed&print_stats...
                    query_params = 'extruder&heater_bed&print_stats&display_status&virtual_sdcard'
                    url = f"{base}/printer/objects/query?{query_params}"
                    
                    r = requests.get(url, timeout=5)
                    r.raise_for_status()
                    
                    data = r.json()
                    
                    # Moonraker retourne {"result": {"status": {"extruder": {...}, "heater_bed": {...}, ...}}}
                    result = data.get('result', {})
                    status_data = result.get('status', {})
                    
                    # Récupérer les données de chaque objet
                    extruder = status_data.get('extruder', {})
                    bed = status_data.get('heater_bed', {})
                    stats = status_data.get('print_stats', {})
                    display = status_data.get('display_status', {})
                    v_sdcard = status_data.get('virtual_sdcard', {})
                    
                    # 🌡️ Extraction des températures
                    ext_temp = extruder.get('temperature', 0)
                    ext_target = extruder.get('target', 0)
                    bed_temp = bed.get('temperature', 0)
                    bed_target = bed.get('target', 0)
                    
                    # Fallback : certaines versions utilisent 'actual'
                    if ext_temp == 0 and 'actual' in extruder:
                        ext_temp = extruder.get('actual', 0)
                    if bed_temp == 0 and 'actual' in bed:
                        bed_temp = bed.get('actual', 0)
                    
                    # Mapping du statut
                    state = stats.get('state', 'standby').lower()
                    status_map = {
                        'printing': 'printing', 'standby': 'idle', 'paused': 'paused',
                        'complete': 'complete', 'cancelled': 'idle', 'error': 'error',
                        'busy': 'busy', 'ready': 'idle'
                    }
                    status = status_map.get(state, state)
                    
                    duration = stats.get('print_duration', 0) or 0
                    filename = stats.get('filename', '')
                    
                    if not filename and v_sdcard:
                        filename = v_sdcard.get('file', '').split('/')[-1]
                        
                    progress = (display.get('progress', 0) or 0) * 100
                    
                    remaining = 0
                    if progress > 0 and progress < 100 and duration > 0:
                        remaining = int((duration / progress) * (100 - progress))
                    
                    last_print = self._get_klipper_last_print(ip, port)
                    
                    return {
                        'status': status,
                        'progress': round(progress, 1),
                        'file': filename,
                        'temps': {
                            'extruder': {'current': round(float(ext_temp), 1), 'target': round(float(ext_target), 1)},
                            'bed': {'current': round(float(bed_temp), 1), 'target': round(float(bed_target), 1)},
                            'chamber': {'current': 0, 'target': 0}
                        },
                        'time': {
                            'elapsed': int(duration),
                            'remaining': remaining,
                            'total': int(duration + remaining)
                        },
                        'last_print': last_print
                    }
                except requests.exceptions.RequestException as e:
                    return {**default_result, 'status': 'offline'}
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    return {**default_result, 'status': 'error'}
                
            elif ptype == 'bambu':
                return {**default_result, 'status': 'bambu_mqtt_not_supported'}
        
        except requests.exceptions.Timeout:
            return {**default_result, 'status': 'timeout'}
        except requests.exceptions.ConnectionError:
            return {**default_result, 'status': 'offline'}
        except Exception as e:
            print(f"[Printer] Erreur get_status: {e}")
            return {**default_result, 'status': 'error'}
        
        return default_result


    def _get_octoprint_last_print(self, ip, api_key):
        """Récupère la dernière impression depuis l'historique OctoPrint"""
        try:
            headers = {'X-Api-Key': api_key}
            r = requests.get(f"http://{ip}/api/job", headers=headers, timeout=3).json()
            # Si en cours d'impression, pas de "dernière"
            if r.get('state', '').lower() in ['printing', 'paused']:
                return {'filename': '', 'duration': 0, 'finished_at': ''}
            
            # Récupérer via history
            history = requests.get(f"http://{ip}/api/history?limit=1", headers=headers, timeout=3).json()
            records = history.get('logs', [])
            if records:
                last = records[0]
                return {
                    'filename': last.get('printFile', {}).get('name', last.get('printFile', {}).get('path', '')),
                    'duration': int(last.get('printTime', 0) or 0),
                    'finished_at': last.get('timestamp', '')
                }
        except Exception:
            pass
        return {'filename': '', 'duration': 0, 'finished_at': ''}

    def _get_klipper_last_print(self, ip, port):
        """Récupère la dernière impression depuis l'historique Moonraker"""
        try:
            base = f"http://{ip}:{port}"
            # Endpoint Moonraker pour l'historique (limité au dernier job)
            r = requests.get(f"{base}/server/history/list?limit=1", timeout=3)
            if r.status_code == 200:
                data = r.json()
                jobs = data.get('result', {}).get('jobs', [])
                if jobs:
                    last_job = jobs[0]
                    # Moonraker renvoie end_time en timestamp Unix
                    end_time = last_job.get('end_time', 0)
                    duration = last_job.get('print_duration', 0) or 0
                    
                    # Le nom de fichier est souvent dans metadata
                    metadata = last_job.get('metadata', {})
                    filename = metadata.get('filename', last_job.get('filename', ''))
                    
                    finished_at = ""
                    if end_time:
                        finished_at = datetime.datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')
                        
                    return {
                        'filename': filename,
                        'duration': int(duration),
                        'finished_at': finished_at
                    }
        except Exception as e:
            print(f"[Klipper History] Erreur: {e}")
        return {'filename': '', 'duration': 0, 'finished_at': ''}
        
    def upload_file(self, db_row, file_path):
        """Envoie le fichier G-code à l'imprimante"""
        ptype = db_row['type']
        ip = db_row['ip']
        api_key = db_row['api_key']
        
        try:
            if ptype == 'octoprint':
                url = f"http://{ip}/api/files/local"
                headers = {'X-Api-Key': api_key}
                with open(file_path, 'rb') as f:
                    files = {'file': f}
                    r = requests.post(url, headers=headers, files=files, timeout=30)
                return r.status_code == 201

            elif ptype == 'klipper':
                port = db_row['config'].get('port', '7125') if isinstance(db_row['config'], dict) else '7125'
                base = f"http://{ip}:{port}"
                
                try:
                    # L'API Moonraker attend le fichier dans un champ multipart nommé 'file'
                    # et optionnellement 'root' pour spécifier 'gcodes' (dossier par défaut)
                    with open(file_path, 'rb') as f:
                        files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
                        data = {'root': 'gcodes'}
                        
                        r = requests.post(f"{base}/server/files/upload", files=files, data=data, timeout=60)
                        
                        if r.status_code == 200:
                            response_data = r.json()
                            # Vérifier si Moonraker confirme l'ajout
                            if response_data.get('result') == "ok" or 'accepted' in str(response_data).lower():
                                return True
                    return False
                except Exception as e:
                    print(f"[Klipper Upload] Erreur: {e}")
                    return False

            elif ptype == 'bambu':
                # L'envoi via MQTT pour Bambu est complexe (nécessite FTP ou MQTT spécifique)
                # Pour le moment, on simule un succès
                return True

        except Exception as e:
            print(f"[Printer Upload] Erreur: {e}")
            return False
        return False
    
def parse_printer_config(db_row):
    """Parse la config JSON stockée en base (string → dict)"""
    row = dict(db_row)
    config = row.get('config')
    if isinstance(config, str):
        try:
            row['config'] = json.loads(config) if config else {}
        except json.JSONDecodeError:
            row['config'] = {}
    elif not isinstance(config, dict):
        row['config'] = {}
    return row
    
printer_hub = PrinterManager()

# Ajouter la table printers au démarrage si elle n'existe pas
def is_first_launch():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return count == 0

def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "non authentifié"}), 401
        return f(*args, **kwargs)
    return decorated

app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')
app.secret_key = secrets.token_hex(32)
SUPPORTED_EXTENSIONS = {'.stl', '.3mf', '.obj'}
SUPPORTED_3D_EXTS = {'.stl', '.obj', '.3mf', '.step', '.stp', '.iges', '.igs', '.amf'}
SMTP_CONFIG = {
    'server': os.environ.get('STELLIO_SMTP_SERVER', 'smtp.mail.ovh.net'),
    'port': int(os.environ.get('STELLIO_SMTP_PORT', '465')),
    'user': os.environ.get('STELLIO_SMTP_USER', 'contact@stellio-app.com'),
    'pass': os.environ.get('STELLIO_SMTP_PASS', ''),
    'recipient': 'contact@stellio-app.com'
}

def get_cache_key(sources):
    src_str = json.dumps(sorted([f"{s['id']}:{s['path']}:{s.get('config', '')}" for s in sources]), sort_keys=True)
    return hashlib.md5(src_str.encode()).hexdigest()

def load_file_cache():
    try:
        if not os.path.exists(CACHE_FILE):
            return None
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        if not isinstance(cache, dict) or 'timestamp' not in cache or 'files' not in cache:
            print("[WARN] Cache invalide, suppression...")
            invalidate_cache()
            return None
        if time.time() - cache.get('timestamp', 0) > CACHE_DURATION:
            return None
        return cache.get('files')
    except json.JSONDecodeError as e:
        print(f"[ERROR] Cache JSON corrompu: {e}")
        invalidate_cache()
        return None
    except Exception as e:
        print(f"[WARN] Erreur lecture cache: {e}")
        return None

def save_file_cache(files, sources):
    try:
        if not isinstance(files, list):
            print(f"[ERROR] files n'est pas une liste: {type(files)}")
            return
        cache = {
            'timestamp': time.time(),
            'cache_key': get_cache_key(sources),
            'files': files
        }
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] Échec sauvegarde cache: {e}")

def invalidate_cache():
    try:
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
    except:
        pass

def process_generation_queue():
    global is_generation_running
    if is_generation_running:
        return
    is_generation_running = True
    def worker():
        global is_generation_running
        print("[BACKGROUND] Générateur lazy démarré")
        processed_count = 0
        error_count = 0
        consecutive_errors = 0
        while True:
            try:
                if not thumb_generation_queue.empty():
                    task = thumb_generation_queue.get(timeout=1)
                    file_path = task.get('path')
                    thumb_path = task.get('thumb_path')
                    if file_path in ignored_files_cache:
                        print(f"[SKIP] Fichier déjà ignoré: {os.path.basename(file_path)}")
                        thumb_generation_queue.task_done()
                        continue
                    is_smb = file_path.startswith('//') or file_path.startswith('\\\\')
                    file_accessible = False
                    if not is_smb:
                        file_accessible = os.path.exists(file_path)
                    else:
                        try:
                            smb_path = file_path.replace('\\\\', '//').replace('\\', '/')
                            smbclient.stat(smb_path)
                            file_accessible = True
                        except:
                            file_accessible = False
                    if not file_accessible:
                        print(f"[SKIP] Fichier inaccessible: {os.path.basename(file_path)}")
                        ignored_files_cache.add(file_path)
                        error_count += 1
                        consecutive_errors += 1
                        thumb_generation_queue.task_done()
                        if consecutive_errors > 10:
                            print("[ABORT] Trop d'erreurs, pause 60s...")
                            time.sleep(60)
                            consecutive_errors = 0
                        continue
                    if not os.path.exists(thumb_path):
                        print(f"[GENERATING] {os.path.basename(file_path)}")
                        success = generate_thumbnail_pyrender(file_path, thumb_path)
                        if success:
                            processed_count += 1
                            consecutive_errors = 0
                            error_count = 0
                        else:
                            print(f"[FALLBACK] Création miniature fallback pour {os.path.basename(file_path)}")
                            create_fallback_thumbnail(thumb_path)
                            consecutive_errors = 0
                    if processed_count % 10 == 0:
                        print(f"[STATS] {processed_count} miniatures générées")
                    if consecutive_errors > 5:
                        print("[PAUSE] Trop d'erreurs consécutives, pause 30s...")
                        time.sleep(30)
                        consecutive_errors = 0
                    thumb_generation_queue.task_done()
                    continue
                if not metadata_generation_queue.empty():
                    task = metadata_generation_queue.get(timeout=1)
                    file_path = task.get('path')
                    print(f"[ANALYZING] {os.path.basename(file_path)}")
                    analyze_3d_file(file_path)
                    metadata_generation_queue.task_done()
                    continue
                conn = get_db()
                sources = conn.execute("SELECT * FROM sources").fetchall()
                conn.close()
                for source in sources:
                    if source['type'] == 'folder' and os.path.exists(source['path']):
                        for root, dirs, files in os.walk(source['path']):
                            for f in files:
                                if f.lower().endswith(('.stl', '.obj', '.3mf')):
                                    file_path = os.path.join(root, f).replace('\\', '/')
                                    if file_path in ignored_files_cache:
                                        continue
                                    normalized_path = file_path
                                    thumb_filename = hashlib.md5(normalized_path.encode()).hexdigest()
                                    thumb_path = os.path.join(THUMBNAILS_DIR, thumb_filename + '.png')
                                    if not os.path.exists(thumb_path):
                                        thumb_generation_queue.put({
                                            'path': file_path,
                                            'thumb_path': thumb_path,
                                            'priority': 'low'
                                        })
                                    break
                            break
                time.sleep(0.2)
            except queue.Empty:
                time.sleep(2)
            except Exception as e:
                print(f"[BACKGROUND ERROR] {e}")
                time.sleep(5)
    threading.Thread(target=worker, daemon=True).start()
    print("[BACKGROUND] File d'attente lazy active")

def load_3mf_mesh(file_path):
    try:
        mesh = trimesh.load(file_path, force='mesh')
        if mesh is not None and not mesh.is_empty and len(mesh.vertices) > 0:
            return mesh
    except:
        pass
    try:
        with zipfile.ZipFile(file_path, 'r') as zf:
            model_path = None
            for name in zf.namelist():
                if name.endswith('.model') and '3D/' in name:
                    model_path = name
                    break
            if model_path:
                with zf.open(model_path) as xml_file:
                    tree = ET.parse(xml_file)
                    root = tree.getroot()
                    namespaces = ['http://schemas.microsoft.com/3dmanufacturing/core/2015/02']
                    for ns_uri in namespaces:
                        ns = {'ns': ns_uri}
                        objects = root.findall('.//ns:object[@type="model"]', ns)
                        if not objects:
                            objects = root.findall('.//object[@type="model"]')
                        if objects:
                            for obj in objects:
                                pid = obj.get('pid')
                                if pid:
                                    resources = root.findall('.//ns:resource', ns)
                                    if not resources:
                                        resources = root.findall('.//resource')
                                    for res in resources:
                                        if res.get('id') == pid:
                                            return trimesh.load(file_path, force='mesh')
    except Exception as e:
        print(f"    Erreur extraction 3MF: {e}")
    return trimesh.Trimesh()

def create_fallback_thumbnail(thumb_path, resolution=(512, 512)):
    try:
        logo_path = os.path.join(BASE_DIR, 'assets', 'logo-nom-stellio.png')
        img = Image.new('RGBA', resolution, (26, 29, 35, 255))
        draw = ImageDraw.Draw(img)
        center = (resolution[0] // 2, resolution[1] // 2)
        radius = min(resolution) // 3
        for r in range(radius, 0, -2):
            alpha = int(50 * (r / radius))
            draw.ellipse([
                center[0] - r, center[1] - r,
                center[0] + r, center[1] + r
            ], outline=(78, 161, 211, alpha), width=2)
        if os.path.exists(logo_path):
            try:
                logo = Image.open(logo_path).convert('RGBA')
                logo_size = int(min(resolution) * 0.6)
                logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                logo_pos = (center[0] - logo_size // 2, center[1] - logo_size // 2)
                img.paste(logo, logo_pos, logo)
                draw.text(center, "Fichier\ncorrompu", fill=(150, 150, 150, 200),
                         anchor='mm', align='center', font_size=24)
            except Exception as e:
                print(f"    Erreur chargement logo: {e}")
                _draw_fallback_cube(draw, center)
        else:
            _draw_fallback_cube(draw, center)
        draw.rectangle([0, 0, resolution[0]-1, resolution[1]-1],
                      outline=(60, 65, 75, 255), width=2)
        img_rgb = Image.new('RGB', resolution, (26, 29, 35))
        if img.mode == 'RGBA':
            img_rgb.paste(img, mask=img.split()[3])
        img_rgb.save(thumb_path, quality=90, optimize=True)
        return True
    except Exception as e:
        print(f"    Erreur création fallback: {e}")
        try:
            img = Image.new('RGB', resolution, (40, 40, 40))
            draw = ImageDraw.Draw(img)
            draw.text((resolution[0]//2, resolution[1]//2), "✗",
                     fill=(150, 150, 150), anchor='mm', font_size=48)
            img.save(thumb_path)
            return True
        except:
            return False

def _draw_fallback_cube(draw, center):
    """Fonction helper pour dessiner le cube fallback"""
    cube_size = 80
    cube_center = center
    draw.polygon([
        (cube_center[0], cube_center[1] - cube_size//2),
        (cube_center[0] + cube_size//2, cube_center[1]),
        (cube_center[0], cube_center[1] + cube_size//2),
        (cube_center[0] - cube_size//2, cube_center[1])
    ], fill=(78, 161, 211, 180), outline=(100, 180, 230, 255))
    draw.text((center[0], center[1] + 60), "Fichier corrompu",
             fill=(150, 150, 150, 200), anchor='mm', align='center', font_size=18)

def generate_thumbnail_pyrender(stl_path, thumb_path, resolution=(512, 512)):
    """Génère une miniature avec fallback automatique selon la plateforme"""
    try:
        import pyrender
        import trimesh
        import trimesh.transformations as tra
        import numpy as np
        from PIL import Image
        import tempfile
        import os
        import sys
        
        is_smb = stl_path.startswith('//') or stl_path.startswith('\\\\')
        mesh = None
        tmp_path = None
        
        # 🔹 Chargement du fichier (SMB ou local)
        try:
            if is_smb:
                smb_path = stl_path.replace('\\\\', '//').replace('\\', '/')
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        tmp_fd, tmp_path = tempfile.mkstemp(suffix=os.path.splitext(stl_path)[1])
                        os.close(tmp_fd)
                        with smbclient.open_file(smb_path, 'rb', share_access='r') as smb_file:
                            with open(tmp_path, 'wb') as local_file:
                                while True:
                                    chunk = smb_file.read(8192)
                                    if not chunk: break
                                    local_file.write(chunk)
                        break
                    except Exception as smb_err:
                        if '0xc0000043' in str(smb_err) and attempt < max_retries - 1:
                            time.sleep(1)
                            if tmp_path and os.path.exists(tmp_path): os.unlink(tmp_path)
                            continue
                        raise
                file_to_load = tmp_path
            else:
                if not os.path.exists(stl_path): return False
                file_to_load = stl_path
            
            # 🔹 Chargement du mesh selon extension
            ext = os.path.splitext(file_to_load)[1].lower()
            if ext == '.3mf':
                mesh = load_3mf_mesh(file_to_load)
            elif ext == '.obj':
                mesh = trimesh.load(file_to_load, force='mesh', process=False)
            else:
                mesh = trimesh.load(file_to_load, force='mesh')
            
            if isinstance(mesh, trimesh.Scene):
                geoms = [m for m in mesh.geometry.values() if hasattr(m, 'vertices') and len(m.vertices) > 0]
                if not geoms: return False
                mesh = trimesh.util.concatenate(geoms)
            
            if mesh.is_empty or len(mesh.vertices) == 0: return False
            
            # 🔹 Normalisation
            mesh.apply_translation(-mesh.centroid)
            rot_fix = tra.rotation_matrix(np.radians(-90), [1, 0, 0])
            mesh.apply_transform(rot_fix)
            
            # 🔹 TENTATIVE PYRENDER (avec gestion d'erreur Windows)
            try:
                # Sur Windows, éviter OSMesa et utiliser le contexte par défaut
                if sys.platform == 'win32':
                    # Ne pas forcer os.environ['PYOPENGL_PLATFORM'] ici, laisser PyRender choisir
                    scene = pyrender.Scene(bg_color=[0.1, 0.1, 0.12])
                else:
                    scene = pyrender.Scene(bg_color=[0.1, 0.1, 0.12])
                
                material = pyrender.MetallicRoughnessMaterial(
                    baseColorFactor=[0.3, 0.6, 0.9, 1.0],
                    metallicFactor=0.3,
                    roughnessFactor=0.7
                )
                render_mesh = pyrender.Mesh.from_trimesh(mesh, material=material)
                scene.add(render_mesh)
                
                max_dim = np.linalg.norm(mesh.extents)
                dist = max_dim * 1.5 if max_dim > 0 else 2.0
                
                camera = pyrender.PerspectiveCamera(yfov=np.pi / 4.0, aspectRatio=1.0)
                camera_pose = np.eye(4)
                camera_pose[2, 3] = dist
                r_x = tra.rotation_matrix(np.radians(-25), [1, 0, 0])
                r_y = tra.rotation_matrix(np.radians(45), [0, 1, 0])
                camera_pose = r_x @ r_y @ camera_pose
                scene.add(camera, pose=camera_pose)
                
                main_light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=3.0)
                scene.add(main_light, pose=camera_pose)
                
                fill_light = pyrender.DirectionalLight(color=[0.8, 0.9, 1.0], intensity=1.0)
                fill_pose = camera_pose.copy()
                fill_pose[2, 3] = dist * 0.8
                fill_pose = tra.rotation_matrix(np.radians(30), [0, 1, 0]) @ fill_pose
                scene.add(fill_light, pose=fill_pose)
                
                # 🔥 RENDU
                r = pyrender.OffscreenRenderer(resolution[0], resolution[1])
                color, _ = r.render(scene)
                r.delete()
                
                img = Image.fromarray(color)
                img.save(thumb_path, quality=95, optimize=True)
                
                if tmp_path and os.path.exists(tmp_path): os.unlink(tmp_path)
                return True
                
            except AttributeError as ae:
                if 'OSMesa' in str(ae) or 'Win32Platform' in str(ae):
                    # 🔄 Fallback vers matplotlib pour Windows
                    print(f"[FALLBACK] PyRender OSMesa non dispo, utilisation matplotlib pour {os.path.basename(stl_path)}")
                    return _generate_thumbnail_matplotlib(mesh, thumb_path, resolution)
                raise
                
        except Exception as load_err:
            print(f"[ERROR] Chargement mesh {stl_path}: {load_err}")
            if tmp_path and os.path.exists(tmp_path): os.unlink(tmp_path)
            return False
            
    except Exception as e:
        print(f"[ERROR] Rendu pyrender {stl_path}: {e}")
        import traceback
        traceback.print_exc()
        return False


def _generate_thumbnail_matplotlib(mesh, thumb_path, resolution=(512, 512)):
    """Fallback matplotlib pour générer des miniatures sur Windows sans OSMesa"""
    try:
        import matplotlib
        matplotlib.use('Agg')  # Backend non-GUI
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        import numpy as np
        
        fig = plt.figure(figsize=(resolution[0]/100, resolution[1]/100), dpi=100, facecolor='#1a1d23')
        ax = fig.add_subplot(111, projection='3d', facecolor='#1a1d23')
        
        # Récupérer les vertices et faces
        vertices = mesh.vertices
        faces = mesh.faces
        
        if len(vertices) == 0 or len(faces) == 0:
            plt.close(fig)
            return False
        
        # Normaliser pour l'affichage
        vertices_normalized = vertices.copy()
        vertices_normalized -= vertices_normalized.mean(axis=0)
        max_range = np.max(np.ptp(vertices_normalized, axis=0))
        if max_range > 0:
            vertices_normalized /= max_range
        
        # Créer les polygones
        tri = Poly3DCollection(
            vertices_normalized[faces],
            facecolors='#4ea1d3',
            edgecolors='#2a2f3a',
            linewidths=0.3,
            alpha=0.9
        )
        ax.add_collection3d(tri)
        
        # Configuration de la vue
        ax.set_xlim([-0.6, 0.6])
        ax.set_ylim([-0.6, 0.6])
        ax.set_zlim([-0.6, 0.6])
        ax.set_box_aspect([1, 1, 1])
        
        # Angles de vue isométriques
        ax.view_init(elev=25, azim=45)
        
        # Masquer les axes
        ax.set_axis_off()
        ax.grid(False)
        
        # Sauvegarder
        plt.savefig(thumb_path, bbox_inches='tight', pad_inches=0, facecolor='#1a1d23', dpi=100)
        plt.close(fig)
        return True
        
    except Exception as e:
        print(f"[ERROR] Fallback matplotlib: {e}")
        return False

def analyze_3d_file(file_path):
    try:
        mesh = trimesh.load(file_path, force='mesh')
        if isinstance(mesh, trimesh.Scene):
            geoms = [m for m in mesh.geometry.values() if hasattr(m, 'vertices') and len(m.vertices) > 0]
            if not geoms:
                return None
            mesh = trimesh.util.concatenate(geoms)
        if mesh.is_empty or len(mesh.vertices) == 0:
            return None
        bounds = mesh.bounds
        dimensions = bounds[1] - bounds[0]
        volume_cm3 = abs(mesh.volume) / 1000 if mesh.volume else 0
        surface_cm2 = mesh.area / 100 if mesh.area else 0
        triangle_count = len(mesh.faces)
        densities = {'pla': 1.24, 'petg': 1.27, 'abs': 1.04, 'tpu': 1.21, 'nylon': 1.14}
        weights = {mat: round(volume_cm3 * dens, 1) for mat, dens in densities.items()}
        volume_mm3 = abs(mesh.volume) if mesh.volume else 0
        flow_rate = 10
        if volume_mm3 > 0 and flow_rate > 0:
            estimated_time_seconds = volume_mm3 / flow_rate
            complexity_factor = 1 + (triangle_count / 100000)
            estimated_time_seconds *= complexity_factor
        else:
            estimated_time_seconds = 0
        hours = int(estimated_time_seconds // 3600)
        minutes = int((estimated_time_seconds % 3600) // 60)
        return {
            'dimensions': {'x': round(dimensions[0], 1), 'y': round(dimensions[1], 1), 'z': round(dimensions[2], 1)},
            'volume_cm3': round(volume_cm3, 2),
            'surface_cm2': round(surface_cm2, 2),
            'triangle_count': triangle_count,
            'weights': weights,
            'estimated_time': {'seconds': int(estimated_time_seconds), 'formatted': f"{hours}h {minutes}min" if hours > 0 else f"{minutes}min"},
            'is_manifold': mesh.is_watertight,
            'needs_repair': not mesh.is_watertight,  # ✅ NOUVEAU
            'is_empty': mesh.is_empty
        }
    except Exception as e:
        print(f"[WARN] Erreur analyse 3D {file_path}: {e}")
        return None

@app.route('/api/files/analyze', methods=['POST'])
@login_required
def api_analyze_file():
    data = request.json
    file_path = data.get('path')
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "Fichier non trouvé"}), 404
    normalized_path = file_path.replace('\\', '/')
    cache_key = f"analysis_{hashlib.md5(normalized_path.encode()).hexdigest()}"
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            if cache_key in cache and 'timestamp' in cache:
                if time.time() - cache['timestamp'] < 3600:
                    return jsonify({"success": True, "metadata": cache[cache_key], "cached": True})
        except:
            pass
    metadata = analyze_3d_file(file_path)
    if not metadata:
        return jsonify({"error": "Impossible d'analyser le fichier"}), 500
    try:
        cache_data = {}
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
        cache_data[cache_key] = metadata
        cache_data['timestamp'] = time.time()
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except:
        pass
    return jsonify({"success": True, "metadata": metadata, "cached": False})

@app.route('/')
def index():
    return send_file(os.path.join(BASE_DIR, 'index.html'))

@app.route('/api/auth/first-launch', methods=['GET'])
def api_first_launch():
    return jsonify({"first_launch": is_first_launch()})

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.json
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    if not username or not password:
        return jsonify({"error": "Nom et mot de passe requis"}), 400
    if len(password) < 3:
        return jsonify({"error": "Mot de passe trop court"}), 400
    conn = get_db()
    try:
        conn.execute("INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                    (username, hash_pw(password), email))
        conn.commit()
        user = conn.execute("SELECT id, username FROM users WHERE username = ?", (username,)).fetchone()
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({"message": "Compte créé", "user": {"id": user['id'], "username": user['username']}})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Nom d'utilisateur déjà utilisé"}), 409
    finally:
        conn.close()

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    conn = get_db()
    user = conn.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if user and user['password_hash'] == hash_pw(password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({"message": "Connecté", "user": {"id": user['id'], "username": user['username']}})
    return jsonify({"error": "Identifiants invalides"}), 401

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({"message": "Déconnecté"})

@app.route('/api/auth/me', methods=['GET'])
def api_me():
    if 'user_id' in session:
        return jsonify({"user": {"id": session['user_id'], "username": session['username']}})
    return jsonify({"error": "non authentifié"}), 401

@app.route('/api/auth/forgot', methods=['POST'])
def api_forgot_password():
    data = request.json
    email = data.get('email', '').strip().lower()
    conn = get_db()
    user = conn.execute("SELECT id, username, email FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    if not user:
        return jsonify({"error": "Aucun compte associé à cet email"}), 404
    import random
    code = str(random.randint(100000, 999999))
    expiry = (datetime.datetime.now() + datetime.timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
    conn = get_db()
    conn.execute("UPDATE users SET reset_code = ?, reset_expiry = ? WHERE id = ?", (code, expiry, user['id']))
    conn.commit()
    conn.close()
    if not SMTP_CONFIG['user'] or not SMTP_CONFIG['pass']:
        return jsonify({"error": "SMTP non configuré"}), 500
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_CONFIG['user']
        msg['To'] = email
        msg['Subject'] = "[Stellio] Code de réinitialisation"
        body = f"Votre code : {code}\nExpire dans 15 min."
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        if SMTP_CONFIG['port'] == 465:
            with smtplib.SMTP_SSL(SMTP_CONFIG['server'], SMTP_CONFIG['port']) as server:
                server.login(SMTP_CONFIG['user'], SMTP_CONFIG['pass'])
                server.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_CONFIG['server'], SMTP_CONFIG['port']) as server:
                server.starttls()
                server.login(SMTP_CONFIG['user'], SMTP_CONFIG['pass'])
                server.send_message(msg)
        return jsonify({"message": "Code envoyé"})
    except Exception as e:
        return jsonify({"error": f"Erreur d'envoi: {str(e)}"}), 500

@app.route('/api/auth/reset', methods=['POST'])
def api_reset_password():
    data = request.json
    email = data.get('email', '').strip().lower()
    code = data.get('code', '').strip()
    new_password = data.get('password', '')
    if not all([email, code, new_password]):
        return jsonify({"error": "Champs requis"}), 400
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    if not user:
        return jsonify({"error": "Utilisateur introuvable"}), 404
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if user['reset_code'] != code or user['reset_expiry'] < now:
        return jsonify({"error": "Code invalide ou expiré"}), 400
    conn = get_db()
    conn.execute("UPDATE users SET password_hash = ?, reset_code = NULL, reset_expiry = NULL WHERE id = ?",
                (hash_pw(new_password), user['id']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Mot de passe réinitialisé"})

@app.route('/api/sources', methods=['GET'])
@login_required
def api_get_sources():
    conn = get_db()
    sources = conn.execute("SELECT * FROM sources WHERE user_id = ?", (session['user_id'],)).fetchall()
    conn.close()
    return jsonify([dict(s) for s in sources])

@app.route('/api/sources', methods=['POST'])
@login_required
def api_add_source():
    data = request.json
    name = data.get('name', '').strip()
    src_type = data.get('type')
    path = data.get('path')
    config = json.dumps(data.get('config', {}))
    user_id = session['user_id']
    if not all([src_type, path]):
        return jsonify({"error": "Champs requis"}), 400
    conn = get_db()
    if not name:
        name = f"Source {len(conn.execute('SELECT id FROM sources WHERE user_id=?', (user_id,)).fetchall()) + 1}"
    try:
        conn.execute("INSERT INTO sources (user_id, name, type, path, config) VALUES (?, ?, ?, ?, ?)",
                    (user_id, name, src_type, path, config))
        conn.commit()
        invalidate_cache()
        return jsonify({"message": "Source ajoutée"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/sources/<int:source_id>', methods=['PUT'])
@login_required
def api_update_source(source_id):
    data = request.json
    new_name = data.get('name', '').strip()
    if not new_name:
        return jsonify({"error": "Nom requis"}), 400
    conn = get_db()
    conn.execute("UPDATE sources SET name = ? WHERE id = ? AND user_id = ?",
                (new_name, source_id, session['user_id']))
    conn.commit()
    invalidate_cache()
    conn.close()
    return jsonify({"message": "Source mise à jour"}), 200

@app.route('/api/sources/<int:source_id>', methods=['DELETE'])
@login_required
def api_delete_source(source_id):
    conn = get_db()
    conn.execute("DELETE FROM sources WHERE id = ? AND user_id = ?",
                (source_id, session['user_id']))
    conn.commit()
    invalidate_cache()
    conn.close()
    return jsonify({"message": "Source supprimée"}), 200

@app.route('/api/accounts', methods=['GET'])
@login_required
def api_get_accounts():
    conn = get_db()
    accounts = conn.execute(
        "SELECT id, platform, email, api_key, created_at, last_login FROM account_credentials WHERE user_id = ?",
        (session['user_id'],)
    ).fetchall()
    conn.close()
    accounts_list = [dict(a) for a in accounts]
    for acc in accounts_list:
        if acc.get('api_key'):
            acc['api_key'] = '••••••••'
    return jsonify(accounts_list)

@app.route('/api/accounts/<platform>', methods=['GET'])
@login_required
def api_get_account(platform):
    platform = platform.lower()
    conn = get_db()
    account = conn.execute(
        "SELECT id, platform, email, api_key, session_cookies, telegram_api_id, telegram_api_hash, created_at, last_login FROM account_credentials WHERE user_id = ? AND platform = ?",
        (session['user_id'], platform)
    ).fetchone()
    conn.close()
    if not account:
        return jsonify({"error": "Compte non trouvé"}), 404
    result = dict(account)
    if result.get('api_key'):
        result['api_key'] = '••••••••'
    if result.get('telegram_api_id'):
        result['telegram_api_id'] = '••••••••'
    if result.get('telegram_api_hash'):
        result['telegram_api_hash'] = '••••••••'
    return jsonify(result)

@app.route('/api/accounts/thingiverse/validate', methods=['POST'])
@login_required
def validate_thingiverse_account():
    """Valide le token API Thingiverse"""
    try:
        conn = get_db()
        account = conn.execute(
            "SELECT * FROM account_credentials WHERE user_id = ? AND platform = 'thingiverse'",
            (session['user_id'],)
        ).fetchone()
        conn.close()
        
        if not account:
            return jsonify({"connected": False, "error": "Aucun compte Thingiverse configuré"}), 404
        
        api_token = account['api_key']
        
        if not api_token:
            return jsonify({"connected": False, "error": "Token API manquant"}), 400
        
        api_token = api_token.strip()
        
        print(f"[THINGIVERSE] Test du token: {api_token[:10]}...")
        
        try:
            response = requests.get(
                'https://api.thingiverse.com/me',
                headers={
                    'Authorization': f'Bearer {api_token}',
                    'Content-Type': 'application/json',
                    'User-Agent': 'Stellio-App/1.0'
                },
                timeout=10
            )
            
            print(f"[THINGIVERSE] Endpoint api.thingiverse.com/me: Status {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'id' in data or 'username' in data:
                    conn = get_db()
                    conn.execute(
                        "UPDATE account_credentials SET last_login = CURRENT_TIMESTAMP WHERE user_id = ? AND platform = 'thingiverse'",
                        (session['user_id'],)
                    )
                    conn.commit()
                    conn.close()
                    return jsonify({
                        "connected": True, 
                        "message": "Connecté à Thingiverse", 
                        "username": data.get('public_name') or data.get('username') or 'Utilisateur'
                    })
            elif response.status_code == 401:
                return jsonify({"connected": False, "error": "Token invalide (401)"}), 401
            elif response.status_code == 404:
                print("[THINGIVERSE] L'API officielle n'est plus disponible")
                conn = get_db()
                conn.execute(
                    "UPDATE account_credentials SET last_login = CURRENT_TIMESTAMP WHERE user_id = ? AND platform = 'thingiverse'",
                    (session['user_id'],)
                )
                conn.commit()
                conn.close()
                return jsonify({
                    "connected": True, 
                    "message": "Token enregistré (API limitée)",
                    "warning": "L'API Thingiverse est limitée, certaines fonctionnalités peuvent ne pas être disponibles"
                })
        except requests.exceptions.RequestException as e:
            print(f"[THINGIVERSE] Erreur connexion API: {e}")
        except json.JSONDecodeError as e:
            print(f"[THINGIVERSE] Erreur parsing JSON: {e}")
        
        conn = get_db()
        conn.execute(
            "UPDATE account_credentials SET last_login = CURRENT_TIMESTAMP WHERE user_id = ? AND platform = 'thingiverse'",
            (session['user_id'],)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            "connected": True, 
            "message": "Token enregistré (validation API indisponible)",
            "warning": "Impossible de valider le token via l'API, mais il sera utilisé pour les téléchargements"
        })
        
    except Exception as e:
        print(f"[THINGIVERSE VALIDATE] Erreur: {e}")
        return jsonify({"connected": False, "error": str(e)}), 500

@app.route('/api/accounts/cults/validate', methods=['POST'])
@login_required
def validate_cults_account():
    """Valide la clé API Cults3D via GraphQL"""
    try:
        conn = get_db()
        account = conn.execute(
            "SELECT * FROM account_credentials WHERE user_id = ? AND platform = 'cults'",
            (session['user_id'],)
        ).fetchone()
        conn.close()
        
        if not account:
            return jsonify({"connected": False, "error": "Aucun compte Cults3D configuré"}), 404
        
        api_key = account['api_key']
        
        if api_key:
            try:
                api_key = decrypt_password(api_key)
                print(f"[CULTS] Clé déchiffrée: {api_key[:10]}...")
            except Exception as e:
                print(f"[CULTS] Erreur déchiffrement: {e}")
                return jsonify({"connected": False, "error": "Erreur de déchiffrement"}), 500
        
        if not api_key:
            return jsonify({"connected": False, "error": "Clé API manquante"}), 400
        
        response = requests.post(
            'https://cults3d.com/graphql',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            },
            json={'query': '{ me { id username email } }'},
            timeout=10
        )
        
        print(f"[CULTS] Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'] and 'me' in data['data']:
                conn = get_db()
                conn.execute(
                    "UPDATE account_credentials SET last_login = CURRENT_TIMESTAMP WHERE user_id = ? AND platform = 'cults'",
                    (session['user_id'],)
                )
                conn.commit()
                conn.close()
                return jsonify({"connected": True, "message": "Connecté à Cults3D"})
        
        return jsonify({"connected": False, "error": f"Clé invalide ({response.status_code})"}), 401
        
    except Exception as e:
        print(f"[CULTS VALIDATE] Erreur: {e}")
        return jsonify({"connected": False, "error": str(e)}), 500

@app.route('/api/accounts', methods=['POST'])
@login_required
def api_save_account():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Données invalides"}), 400
        platform = data.get('platform', '').lower()
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''
        api_key = (data.get('api_key') or '').strip()
        cookie_data = (data.get('cookie_data') or '').strip()
        telegram_api_id = (data.get('telegram_api_id') or '').strip()
        telegram_api_hash = (data.get('telegram_api_hash') or '').strip()
        is_edit = data.get('is_edit', False)
        
        if platform == 'cults':
            if not api_key:
                return jsonify({"error": "Clé API requise pour Cults3D"}), 400
            print(f"[CULTS] Clé API enregistrée (validation différée): {api_key[:10]}...")
            
        elif platform == 'thingiverse':
            if not api_key:
                return jsonify({"error": "Token API requis pour Thingiverse"}), 400
            print(f"[THINGIVERSE] Token API enregistré: {api_key[:10]}...")
            
        elif platform == 'telegram':
            if not telegram_api_id or not telegram_api_hash:
                return jsonify({"error": "API ID et API Hash Telegram requis"}), 400
            try:
                int(telegram_api_id)
            except ValueError:
                return jsonify({"error": "API ID doit être un nombre"}), 400
        elif platform and platform not in ['telegram', 'cults', 'thingiverse']:
            if not email and not password:
                return jsonify({"error": "Email et/ou mot de passe requis"}), 400
        
        conn = get_db()
        try:
            password_enc = encrypt_password(password) if password else None
            tg_api_id_enc = encrypt_password(telegram_api_id) if telegram_api_id else None
            tg_apiHash_enc = encrypt_password(telegram_api_hash) if telegram_api_hash else None
            
            api_key_enc = api_key
            
            conn.execute("""
                INSERT INTO account_credentials
                (user_id, platform, email, password_encrypted, api_key, session_cookies,
                telegram_api_id, telegram_api_hash, last_login)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, platform) DO UPDATE SET
                email = excluded.email,
                password_encrypted = excluded.password_encrypted,
                api_key = excluded.api_key,
                session_cookies = excluded.session_cookies,
                telegram_api_id = excluded.telegram_api_id,
                telegram_api_hash = excluded.telegram_api_hash,
                last_login = CURRENT_TIMESTAMP
            """, (
                session['user_id'],
                platform,
                email or None,
                password_enc,
                api_key_enc,
                cookie_data or None,
                tg_api_id_enc,
                tg_apiHash_enc,
                datetime.datetime.now()
            ))
            conn.commit()
            print(f"[ACCOUNT] Compte {platform} enregistré")
            return jsonify({"message": "Compte enregistré avec succès"}), 200
        except Exception as db_err:
            conn.rollback()
            print(f"[DB] Erreur: {db_err}")
            return jsonify({"error": f"Erreur BD: {str(db_err)}"}), 500
        finally:
            conn.close()
    except Exception as e:
        print(f"[ERROR] Erreur serveur: {e}")
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

@app.route('/api/thumb', methods=['GET'])
@login_required
def api_get_thumb():
    file_path = request.args.get('path')
    if not file_path:
        return jsonify({"error": "Chemin requis"}), 400
    
    if '&t=' in file_path:
        file_path = file_path.split('&t=')[0]
    
    normalized_path = file_path.replace('\\', '/')
    thumb_filename = hashlib.md5(normalized_path.encode()).hexdigest()
    thumb_path = os.path.join(THUMBNAILS_DIR, thumb_filename)
    
    for ext in ['.png', '.jpg']:
        img_path = thumb_path + ext
        if os.path.exists(img_path):
            return send_file(img_path, mimetype='image/png')
            
    return jsonify({"error": "Miniature non trouvée"}), 404

def update_cache_thumb_status(file_path, has_thumb):
    """Met à jour le statut de miniature dans le cache JSON"""
    try:
        if not os.path.exists(CACHE_FILE):
            return
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        if 'files' in cache and isinstance(cache['files'], list):
            for f in cache['files']:
                if f.get('path') == file_path:
                    f['has_thumb'] = has_thumb
                    break
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[CACHE] Erreur mise à jour thumb status: {e}")
        
def pregenerate_thumbnails_on_startup(limit=30):
    """Pré-génère les miniatures manquantes au démarrage (limité pour ne pas bloquer)"""
    print("[THUMBS] 🔄 Pré-génération des miniatures au démarrage...")
    conn = get_db()
    sources = conn.execute("SELECT * FROM sources").fetchall()
    conn.close()
    
    generated = 0
    processed = 0
    
    for source in sources:
        if processed >= limit:
            break
        try:
            if source['type'] == 'folder' and os.path.exists(source['path']):
                for root, dirs, files in os.walk(source['path']):
                    for f in files:
                        if processed >= limit:
                            break
                        if f.lower().endswith(('.stl', '.obj', '.3mf')):
                            file_path = os.path.join(root, f).replace('\\', '/')
                            normalized_path = file_path
                            thumb_filename = hashlib.md5(normalized_path.encode()).hexdigest()
                            thumb_path = os.path.join(THUMBNAILS_DIR, thumb_filename + '.png')
                            
                            if not os.path.exists(thumb_path) and file_path not in ignored_files_cache:
                                print(f"[THUMBS] Génération: {os.path.basename(file_path)}")
                                if generate_thumbnail_pyrender(file_path, thumb_path):
                                    generated += 1
                                    update_cache_thumb_status(file_path, True)  # ✅ Cache mis à jour !
                                else:
                                    create_fallback_thumbnail(thumb_path)
                                    update_cache_thumb_status(file_path, True)
                            processed += 1
        except Exception as e:
            print(f"[THUMBS] Erreur source {source['name']}: {e}")
    
    print(f"[THUMBS] ✅ {generated}/{processed} miniatures pré-générées")
    
@app.route('/api/thumb/check', methods=['POST'])
@login_required
def api_check_thumb():
    data = request.json
    file_path = data.get('path')
    if not file_path:
        return jsonify({"exists": False}), 400
    normalized_path = file_path.replace('\\', '/')
    thumb_filename = hashlib.md5(normalized_path.encode()).hexdigest()
    thumb_path = os.path.join(THUMBNAILS_DIR, thumb_filename)
    for ext in ['.png', '.jpg']:
        if os.path.exists(thumb_path + ext):
            return jsonify({
                "exists": True,
                "type": "cached",
                "url": f"/api/thumb?path={file_path}",
                "timestamp": int(os.path.getmtime(thumb_path + ext))
            })
    return jsonify({"exists": False})

@app.route('/api/thumb/progress', methods=['GET'])
@login_required
def api_thumb_progress():
    """Retourne l'état de la file d'attente de génération de miniatures"""
    pending = thumb_generation_queue.qsize()
    total_pending = pending + len(generatingThumbs if 'generatingThumbs' in dir() else set())
    
    # Compter les fichiers sans miniature dans le cache
    files_without_thumb = 0
    files_with_thumb = 0
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            for file_entry in cache.get('files', []):
                if file_entry.get('has_thumb'):
                    files_with_thumb += 1
                else:
                    files_without_thumb += 1
        except:
            pass
    
    total = files_with_thumb + files_without_thumb
    progress = (files_with_thumb / total * 100) if total > 0 else 100
    
    return jsonify({
        'pending': pending,
        'files_with_thumb': files_with_thumb,
        'files_without_thumb': files_without_thumb,
        'total': total,
        'progress': round(progress, 1),
        'is_generating': pending > 0 or is_generation_running
    })
    
@app.route('/api/accounts/<platform>', methods=['DELETE'])
@login_required
def api_delete_account(platform):
    conn = get_db()
    conn.execute("DELETE FROM account_credentials WHERE user_id = ? AND platform = ?",
                (session['user_id'], platform.lower()))
    conn.commit()
    conn.close()
    return jsonify({"message": "Compte supprimé"}), 200

def get_telegram_credentials(user_id):
    """Récupère les credentials Telegram avec validation"""
    try:
        conn = get_db()
        account = conn.execute(
            "SELECT * FROM account_credentials WHERE user_id = ? AND platform = 'telegram'",
            (user_id,)
        ).fetchone()
        conn.close()
        if not account:
            app.logger.warning(f"⚠️ Aucun compte Telegram trouvé pour user {user_id}")
            return None
        api_id = None
        if account['telegram_api_id']:
            try:
                api_id = decrypt_password(account['telegram_api_id'])
                if api_id:
                    api_id = api_id.strip()
                    if not api_id.isdigit():
                        app.logger.error(f"❌ API ID invalide: {api_id}")
                        api_id = None
            except Exception as e:
                app.logger.error(f"❌ Erreur décryptage API ID: {e}")
                api_id = None
        api_hash = None
        if account['telegram_api_hash']:
            try:
                api_hash = decrypt_password(account['telegram_api_hash'])
                if api_hash:
                    api_hash = api_hash.strip()
                    if len(api_hash) != 32 or not all(c in '0123456789abcdef' for c in api_hash.lower()):
                        app.logger.error(f"❌ API Hash invalide: {api_hash}")
                        api_hash = None
            except Exception as e:
                app.logger.error(f" Erreur décryptage API Hash: {e}")
                api_hash = None
        if not api_id or not api_hash:
            app.logger.error("Credentials Telegram invalides ou corrompus - Reconnexion requise")
            return None
        app.logger.info(f" Credentials Telegram validés pour user {user_id}")
        return {
            'api_id': api_id,
            'api_hash': api_hash,
            'session': account['telegram_session']
        }
    except Exception as e:
        app.logger.error(f"Erreur get_telegram_credentials: {e}")
        return None

telegram_loop = None
telegram_thread = None
telegram_clients = {}
telegram_lock = threading.Lock()
TEMP_SESSION_TIMEOUT = 300

def start_telegram_loop():
    """Démarre une boucle asyncio dédiée dans un thread séparé"""
    global telegram_loop, telegram_thread
    if telegram_loop is not None and telegram_loop.is_running():
        return
    telegram_loop = asyncio.new_event_loop()
    def run_loop():
        asyncio.set_event_loop(telegram_loop)
        try:
            telegram_loop.run_forever()
        finally:
            telegram_loop.close()
    telegram_thread = threading.Thread(target=run_loop, daemon=True, name="TelegramEventLoop")
    telegram_thread.start()
    print("[TELEGRAM] Boucle asyncio dédiée démarrée")

async def _async_telegram_send_code(user_id, phone, api_id, api_hash):
    """Initialise le client et demande l'envoi du code à Telegram"""
    try:
        client = TelegramClient(StringSession(), int(api_id), api_hash, loop=telegram_loop)
        await client.connect()
        result = await client.send_code_request(phone)
        phone_code_hash = result.phone_code_hash
        with telegram_lock:
            telegram_clients[user_id] = {
                "client": client,
                "phone": phone,
                "phone_code_hash": phone_code_hash,
                "api_id": api_id,
                "api_hash": api_hash,
                "timestamp": time.time()
            }
        print(f"[TELEGRAM] Code envoyé pour user {user_id} ({phone})")
        return {"success": True, "message": "Code envoyé", "phone_code_hash": phone_code_hash}
    except FloodWaitError as e:
        return {"success": False, "error": f"Trop de tentatives. Attendez {e.seconds}s", "flood_wait": e.seconds}
    except Exception as e:
        logging.error(f"[Telegram Send Code] Erreur: {e}")
        return {"success": False, "error": str(e)[:150]}

async def _async_telegram_verify_code(user_id, code, password_2fa=None):
    """Valide le code avec l'instance exacte du client"""
    with telegram_lock:
        if user_id not in telegram_clients:
            return {"success": False, "error": "Session expirée. Recommencez l'authentification."}
        session_data = telegram_clients[user_id].copy()
        client = session_data["client"]
        phone = session_data["phone"]
        phone_code_hash = session_data["phone_code_hash"]
    try:
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
    except PhoneCodeInvalidError:
        return {"success": False, "error": "Code invalide. Veuillez réessayer."}
    except SessionPasswordNeededError:
        if not password_2fa:
            return {"success": False, "error": "Authentification 2FA requise", "requires_2fa": True}
        try:
            await client.sign_in(password=password_2fa)
        except Exception:
            return {"success": False, "error": "Mot de passe 2FA incorrect"}
    except Exception as e:
        logging.error(f"[Telegram Verify] Erreur: {e}")
        return {"success": False, "error": str(e)[:150]}
    try:
        session_str = client.session.save()
        conn = get_db()
        conn.execute("""
            INSERT INTO account_credentials
            (user_id, platform, telegram_session, telegram_api_id, telegram_api_hash, last_login)
            VALUES (?, 'telegram', ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, platform) DO UPDATE SET
            telegram_session=excluded.telegram_session,
            telegram_api_id=excluded.telegram_api_id,
            telegram_api_hash=excluded.telegram_api_hash,
            last_login=CURRENT_TIMESTAMP
        """, (user_id, session_str, session_data["api_id"], session_data["api_hash"]))
        conn.commit()
        conn.close()
        await client.disconnect()
        with telegram_lock:
            telegram_clients.pop(user_id, None)
        return {
            "success": True,
            "message": "Authentification Telegram réussie !",
            "user": None
        }
    except Exception as e:
        logging.error(f"[Telegram Save] Erreur: {e}")
        return {"success": False, "error": f"Erreur sauvegarde: {str(e)[:100]}"}

@app.route('/api/telegram/send_code', methods=['POST'])
@login_required
def telegram_send_code():
    """Envoie le code de vérification Telegram"""
    try:
        data = request.json or {}
        phone = data.get('phone', '').strip()
        api_id = data.get('api_id', '').strip()
        api_hash = data.get('api_hash', '').strip()
        if not all([phone, api_id, api_hash]):
            return jsonify({"error": "Phone, API ID et API Hash requis"}), 400
        user_id = session['user_id']
        cleanup_expired_sessions()
        print(f"[TELEGRAM] Code demandé pour {phone} par user {user_id}")
        future = asyncio.run_coroutine_threadsafe(
            _async_telegram_send_code(user_id, phone, api_id, api_hash),
            telegram_loop
        )
        res = future.result(timeout=30)
        if res.get("success"):
            return jsonify(res)
        elif res.get("flood_wait"):
            return jsonify(res), 429
        return jsonify(res), 400 if "invalide" in res.get("error", "").lower() else 500
    except Exception as e:
        logging.error(f"[telegram_send_code] Erreur: {e}")
        return jsonify({"error": str(e)[:150]}), 500

@app.route('/api/telegram/verify_code', methods=['POST'])
@login_required
def telegram_verify_code():
    """Vérifie le code de connexion Telegram"""
    try:
        data = request.json or {}
        code = data.get('code', '').strip()
        password_2fa = data.get('password_2fa', '').strip()
        user_id = session['user_id']
        if not code:
            return jsonify({"error": "Code de vérification requis"}), 400
        print(f"[TELEGRAM] Vérification code pour user {user_id}")
        future = asyncio.run_coroutine_threadsafe(
            _async_telegram_verify_code(user_id, code, password_2fa),
            telegram_loop
        )
        res = future.result(timeout=30)
        if res.get("success"):
            return jsonify(res)
        elif res.get("requires_2fa"):
            return jsonify(res), 400
        return jsonify(res), 400 if "invalide" in res.get("error", "").lower() else 500
    except Exception as e:
        logging.error(f"[telegram_verify_code] Erreur: {e}")
        return jsonify({"error": str(e)[:150]}), 500

@app.route('/api/telegram/status', methods=['GET'])
@login_required
def api_telegram_status():
    """Vérifie l'état de la connexion Telegram pour l'utilisateur"""
    is_valid, error = validate_telegram_credentials(session['user_id'])
    if is_valid:
        return jsonify({
            "connected": True,
            "message": "Telegram connecté"
        }), 200
    else:
        try:
            conn = get_db()
            conn.execute(
                "DELETE FROM account_credentials WHERE user_id = ? AND platform = 'telegram'",
                (session['user_id'],)
            )
            conn.commit()
            conn.close()
            app.logger.info(f"🗑️ Credentials Telegram invalides supprimés pour user {session['user_id']}")
        except Exception as e:
            app.logger.error(f"❌ Erreur suppression credentials: {e}")
        return jsonify({
            "connected": False,
            "error": error,
            "action_required": "reconnect"
        }), 200

@app.route('/api/telegram/logout', methods=['POST'])
@login_required
def api_telegram_logout():
    try:
        conn = get_db()
        conn.execute("UPDATE account_credentials SET telegram_session = NULL WHERE user_id = ? AND platform = 'telegram'", (session['user_id'],))
        conn.commit()
        conn.close()
        with telegram_lock:
            telegram_clients.pop(session['user_id'], None)
        return jsonify({"message": "Déconnecté de Telegram"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def cleanup_expired_sessions():
    """Supprime les sessions temporaires expirées (>5 min)"""
    now = time.time()
    with telegram_lock:
        expired = [uid for uid, data in telegram_clients.items()
                  if now - data.get('timestamp', 0) > TEMP_SESSION_TIMEOUT]
        for uid in expired:
            client = telegram_clients[uid].get('client')
            if client and client.is_connected():
                asyncio.run_coroutine_threadsafe(client.disconnect(), telegram_loop)
            del telegram_clients[uid]
            print(f"[TELEGRAM] Session expirée nettoyée pour user {uid}")

@app.route('/api/telegram/reset', methods=['POST'])
@login_required
def api_reset_telegram():
    """Supprime les credentials Telegram corrompus pour forcer reconnexion"""
    try:
        conn = get_db()
        conn.execute(
            "DELETE FROM account_credentials WHERE user_id = ? AND platform = 'telegram'",
            (session['user_id'],)
        )
        conn.commit()
        conn.close()
        app.logger.info(f" Credentials Telegram supprimés pour user {session['user_id']}")
        return jsonify({"message": "Credentials supprimés. Veuillez vous reconnecter."}), 200
    except Exception as e:
        app.logger.error(f" Erreur reset Telegram: {e}")
        return jsonify({"error": str(e)}), 500

def validate_telegram_credentials(user_id):
    """
    Vérifie si les credentials Telegram sont valides et utilisables.
    Retourne: (is_valid: bool, error_message: str|None)
    """
    try:
        from telethon.sync import TelegramClient
        from telethon.sessions import StringSession
        conn = get_db()
        account = conn.execute(
            "SELECT * FROM account_credentials WHERE user_id = ? AND platform = 'telegram'",
            (user_id,)
        ).fetchone()
        conn.close()
        if not account:
            return False, "Aucun compte Telegram configuré"
        if not account['telegram_session']:
            return False, "Session Telegram manquante"
        tg_creds = get_telegram_credentials(user_id)
        if not tg_creds or not tg_creds.get('api_id') or not tg_creds.get('api_hash'):
            return False, "Credentials Telegram invalides ou corrompus"
        api_id = int(tg_creds['api_id'])
        api_hash = tg_creds['api_hash']
        string_session = account['telegram_session']
        with TelegramClient(StringSession(string_session), api_id, api_hash, timeout=5) as client:
            if not client.is_user_authorized():
                return False, "Session expirée - Reconnexion requise"
            client.get_me()
        return True, None
    except Exception as e:
        app.logger.error(f"❌ Validation Telegram échouée: {e}")
        return False, f"Erreur de validation: {str(e)[:100]}"
 
# =============================================================================
# 🖨️ IMPORTATEUR PRINTABLES (VERSION FONCTIONNELLE)
# =============================================================================
class PrintablesImporter:
    """Téléchargement depuis Printables via GraphQL - Version fonctionnelle"""
    
    MODELQUERY = """
    query ModelFiles($id: ID!) {
      model: print(id: $id) {
        id
        filesType
        gcodes {
          ...GcodeDetail
          __typename
        }
        stls {
          ...StlDetail
          __typename
        }
        slas {
          ...SlaDetail
          __typename
        }
        otherFiles {
          ...OtherFileDetail
          __typename
        }
        downloadPacks {
          id
          name
          fileSize
          fileType
          __typename
        }
        __typename
      }
    }
    fragment GcodeDetail on GCodeType {
      id
      created
      name
      folder
      note
      printer {
        id
        name
        __typename
      }
      excludeFromTotalSum
      printDuration
      layerHeight
      nozzleDiameter
      material {
        id
        name
        __typename
      }
      weight
      fileSize
      filePreviewPath
      rawDataPrinter
      order
      __typename
    }
    fragment OtherFileDetail on OtherFileType {
      id
      created
      name
      folder
      note
      fileSize
      filePreviewPath
      order
      __typename
    }
    fragment SlaDetail on SLAType {
      id
      created
      name
      folder
      note
      expTime
      firstExpTime
      printer {
        id
        name
        __typename
      }
      printDuration
      layerHeight
      usedMaterial
      fileSize
      filePreviewPath
      order
      __typename
    }
    fragment StlDetail on STLType {
      id
      created
      name
      folder
      note
      fileSize
      filePreviewPath
      order
      __typename
    }
    """

    FILEQUERY = """
    mutation GetDownloadLink($id: ID!, $modelId: ID!, $fileType: DownloadFileTypeEnum!, $source: DownloadSourceEnum!) {
      getDownloadLink(
        id: $id
        printId: $modelId
        fileType: $fileType
        source: $source
      ) {
        ok
        errors {
          ...Error
          __typename
        }
        output {
          link
          count
          ttl
          __typename
        }
        __typename
      }
    }
    fragment Error on ErrorType {
      field
      messages
      __typename
    }
    """

    def __init__(self):
        self.session = requests.Session()
        self.graphurl = "https://api.printables.com/graphql/"
        self.clientId = ""

    def _set_client_data(self, url="https://www.printables.com/"):
        """Récupère le client-uid depuis la page Printables"""
        header = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=0, i",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        }
        try:
            response = self.session.get(url, headers=header, timeout=15)
            if response.status_code != 200:
                print(f"[PRINTABLES] ❌ Erreur HTTP {response.status_code}")
                return False

            match = re.search(r'data-client-uid="(([a-z0-9-])+)', response.text)
            if match:
                self.clientId = match.group(1)
                print(f"[PRINTABLES] ✅ Client-UID: {self.clientId[:20]}...")
                return True
            else:
                print("[PRINTABLES] ⚠️ Client-UID non trouvé")
                return False
        except Exception as e:
            print(f"[PRINTABLES] ❌ Erreur _set_client_data: {e}")
            return False

    def _get_model_info(self, modelId):
        """Récupère les informations du modèle via GraphQL"""
        header = {
            "accept": "application/graphql-response+json, application/graphql+json, application/json, text/event-stream, multipart/mixed",
            "accept-language": "fr-FR,fr;q=0.9",
            "client-uid": self.clientId,
            "cache-control": "no-cache",
            "content-type": "application/json",
            "graphql-client-version": "v3.0.11",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        }
        variables = {"id": modelId}

        try:
            response = self.session.post(
                self.graphurl,
                json={"query": self.MODELQUERY, "variables": variables},
                headers=header,
                timeout=20
            )

            if response.status_code != 200:
                print(f"[PRINTABLES] ❌ Erreur GraphQL HTTP {response.status_code}")
                return None

            modelData = response.json()
            modelCollection = []
            
            # Extraire les fichiers STL
            try:
                for model in modelData["data"]["model"]["stls"]:
                    modelCollection.append({
                        "parentId": modelId,
                        "id": model["id"],
                        "name": model["name"],
                        "folder": model.get("folder", ""),
                        "fileSize": model.get("fileSize", 0),
                        "previewPath": "https://files.printables.com/" + model.get("filePreviewPath", ""),
                        "typeName": model["name"].split(".")[-1] if "." in model["name"] else "stl",
                    })
                
                print(f"[PRINTABLES] 📦 {len(modelCollection)} fichier(s) STL trouvé(s)")
                return modelCollection
            except Exception as e:
                print(f"[PRINTABLES] ❌ Erreur parsing modèle: {e}")
                return None
                
        except Exception as e:
            print(f"[PRINTABLES] ❌ Erreur _get_model_info: {e}")
            return None

    def _get_download_link(self, fileId, modelId):
        """Obtient le lien de téléchargement via GraphQL"""
        header = {
            "accept": "application/graphql-response+json, application/graphql+json, application/json, text/event-stream, multipart/mixed",
            "accept-language": "fr-FR,fr;q=0.9",
            "client-uid": self.clientId,
            "cache-control": "no-cache",
            "content-type": "application/json",
            "graphql-client-version": "v3.0.11",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        }
        variables = {
            "fileType": "stl",
            "id": fileId,
            "modelId": modelId,
            "source": "model_detail",
        }

        try:
            response = self.session.post(
                self.graphurl,
                json={"query": self.FILEQUERY, "variables": variables},
                headers=header,
                timeout=20
            )
            
            if response.status_code != 200:
                print(f"[PRINTABLES] ❌ Erreur download link HTTP {response.status_code}")
                return None
            
            fileData = response.json()
            
            try:
                fileResult = fileData["data"]["getDownloadLink"]["ok"]
                fileDownloadLink = fileData["data"]["getDownloadLink"]["output"]["link"]
                
                if fileResult:
                    print(f"[PRINTABLES] ✅ Lien obtenu: {fileDownloadLink[:80]}...")
                    return fileDownloadLink
                else:
                    print("[PRINTABLES] ❌ getDownloadLink ok=false")
                    return None
            except Exception as e:
                print(f"[PRINTABLES] ❌ Erreur parsing lien: {e}")
                return None
                
        except Exception as e:
            print(f"[PRINTABLES] ❌ Erreur _get_download_link: {e}")
            return None

    def download_model(self, url, dest_folder, download_id=None):
        """Méthode principale de téléchargement - Compatible avec Stellio"""
        try:
            # Extraire l'ID du modèle
            model_match = re.search(r'model/(\d+)', url)
            if not model_match:
                return None, "URL Printables invalide"
            
            model_id = model_match.group(1)
            print(f"[PRINTABLES] 🎯 Modèle ID: {model_id}")
            
            # Initialiser la session
            self.session = requests.Session()
            
            # Étape 1: Récupérer le client-uid
            if not self._set_client_data():
                return None, "Impossible d'initialiser la session Printables"
            
            time.sleep(0.2)
            
            # Étape 2: Récupérer les infos du modèle
            model_files = self._get_model_info(model_id)
            if not model_files:
                return None, "Modèle introuvable sur Printables"
            
            if len(model_files) == 0:
                return None, "Aucun fichier STL trouvé"
            
            # Prendre le premier fichier STL
            stl = model_files[0]
            file_id = stl.get("id")
            file_name = stl.get("name", f"printable_{model_id}.stl")
            file_size = stl.get("fileSize", 0)
            
            print(f"[PRINTABLES] 📥 Fichier: {file_name} ({file_size} bytes)")
            
            # Étape 3: Obtenir le lien de téléchargement
            download_link = self._get_download_link(file_id, model_id)
            if not download_link:
                return None, "Impossible d'obtenir le lien de téléchargement"
            
            # Étape 4: Initialiser le suivi de progression
            if download_id:
                active_downloads[download_id] = {
                    'active': True,
                    'filename': file_name,
                    'current': 0,
                    'total': file_size,
                    'percentage': 0,
                    'cancelled': False
                }
            
            # Étape 5: Télécharger le fichier avec progression
            print(f"[PRINTABLES] ⬇️ Téléchargement en cours...")
            
            fileheader = {
                "accept": "*/*",
                "accept-language": "fr-FR,fr;q=0.9",
                "client-uid": self.clientId,
                "cache-control": "no-cache",
                "pragma": "no-cache",
                "priority": "u=1, i",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            }
            
            response = self.session.get(
                download_link,
                stream=True,
                allow_redirects=True,
                headers=fileheader,
                timeout=120
            )
            response.raise_for_status()
            
            # Nettoyer le nom de fichier
            file_name = re.sub(r'[<>:"/\\|?*]', '_', file_name)
            if not file_name.lower().endswith(('.stl', '.obj', '.3mf')):
                file_name += '.stl'
            
            # Créer le chemin de sauvegarde
            save_path = os.path.join(dest_folder, file_name)
            counter = 1
            while os.path.exists(save_path):
                name, ext = os.path.splitext(file_name)
                file_name = f"{name}_{counter}{ext}"
                save_path = os.path.join(dest_folder, file_name)
                counter += 1
            
            # Télécharger avec progression
            total_size = int(response.headers.get('content-length', 0)) or file_size
            downloaded = 0
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    # Vérifier si le téléchargement a été annulé
                    if download_id and download_id in active_downloads:
                        if active_downloads[download_id].get('cancelled'):
                            f.close()
                            if os.path.exists(save_path):
                                os.unlink(save_path)
                            return None, "Téléchargement annulé"
                    
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Mettre à jour la progression
                        if download_id and download_id in active_downloads and total_size > 0:
                            active_downloads[download_id]['current'] = downloaded
                            active_downloads[download_id]['total'] = total_size
                            active_downloads[download_id]['percentage'] = (downloaded / total_size * 100)
            
            print(f"[PRINTABLES] ✅ Terminé: {save_path}")
            
            # Marquer comme terminé
            if download_id and download_id in active_downloads:
                active_downloads[download_id]['active'] = False
            
            return {
                'filename': file_name,
                'path': save_path,
                'size': downloaded
            }, None
            
        except Exception as e:
            print(f"[PRINTABLES] ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            
            if download_id and download_id in active_downloads:
                active_downloads[download_id]['active'] = False
            
            return None, str(e)
            
        finally:
            # Toujours fermer la session
            if hasattr(self, 'session') and self.session:
                self.session.close()


# =============================================================================
# 🌍 IMPORTATEUR MAKERWORLD
# =============================================================================
class MakerWorldImporter:
    """Téléchargement depuis MakerWorld - Cookie optionnel pour modèles privés"""
    
    def __init__(self):
        self.session = requests.Session()
        self.browser_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        self.allowed_exts = [".stl", ".obj", ".3mf", ".gcode", ".bgcode"]
        self.ext_priority = [".3mf", ".stl", ".obj", ".gcode", ".bgcode"]
    
    def _html_headers(self, referer=None, cookie=None):
        headers = {
            "User-Agent": self.browser_ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
        }
        if referer: headers["Referer"] = referer
        if cookie: headers["Cookie"] = cookie
        return headers
    
    def _api_headers(self, referer=None, nonce=None, cookie=None):
        headers = {
            "User-Agent": self.browser_ua,
            "Accept": "application/json",
            "X-BBL-Client-Type": "web",
            "X-BBL-Client-Version": "00.00.00.01",
            "X-BBL-App-Source": "makerworld",
            "X-BBL-Client-Name": "MakerWorld"
        }
        if referer: headers["Referer"] = referer
        if nonce: headers["X-Nonce"] = nonce
        if cookie: headers["Cookie"] = cookie
        return headers
    
    def _extract_model_id(self, url):
        match = re.search(r"/model[s]?/(\d+)", url)
        return match.group(1) if match else None
    
    def _extract_next_data(self, html):
        match = re.search(
            r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
            html, re.IGNORECASE | re.DOTALL
        )
        if not match: return None
        try:
            return json.loads(match.group(1))
        except:
            return None
    
    def _score_url(self, url):
        lower = url.lower()
        score = 0
        if "download" in lower: score += 6
        if "files" in lower: score += 2
        for idx, ext in enumerate(self.ext_priority):
            if ext in lower:
                score += (len(self.ext_priority) - idx) * 10
        return score
    
    def _is_valid_candidate(self, url):
        lower = url.lower()
        ext = os.path.splitext(urlparse(url).path)[1].lower()
        if ext in self.allowed_exts: return True
        if ext in [".html", ".htm", ".js", ".css", ".jpg", ".png", ".gif"]: return False
        return "download" in lower or any(e in lower for e in self.allowed_exts)
    
    def _find_download_url_in_json(self, data, base_url, seen=None):
        if seen is None: seen = set()
        candidates = []
        stack = [data]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                stack.extend(current.values())
            elif isinstance(current, list):
                stack.extend(current)
            elif isinstance(current, str):
                if current in seen: continue
                seen.add(current)
                if self._is_valid_candidate(current):
                    candidates.append(current)
        if not candidates: return None
        candidates.sort(key=self._score_url, reverse=True)
        return candidates[0]
    
    def _extract_download_url(self, data, base_url):
        if isinstance(data, dict):
            for key in ("url", "downloadUrl", "download_url"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value
            inner = data.get("data")
            if isinstance(inner, dict):
                for key in ("url", "downloadUrl", "download_url"):
                    value = inner.get(key)
                    if isinstance(value, str) and value.strip():
                        return value
        return self._find_download_url_in_json(data, base_url)
    
    def _get_instance_id(self, data):
        try:
            design = data.get("props", {}).get("pageProps", {}).get("design", {})
            default_instance = design.get("defaultInstanceId")
            if default_instance: return str(default_instance)
            instances = design.get("instances") or []
            if isinstance(instances, list):
                for inst in instances:
                    if isinstance(inst, dict) and inst.get("id"):
                        return str(inst["id"])
            return None
        except:
            return None
    
    def _get_nonce(self, data):
        try:
            nonce = data.get("props", {}).get("pageProps", {}).get("x-nonce")
            return nonce if isinstance(nonce, str) and nonce.strip() else None
        except:
            return None
    
    def _get_model_id_from_data(self, data):
        try:
            design = data.get("props", {}).get("pageProps", {}).get("design", {})
            design_id = design.get("id")
            return str(design_id) if design_id else None
        except:
            return None
    
    def _fetch_instance_download_url(self, instance_id, page_url, cookie=None):
        api_url = f"https://makerworld.com/api/v1/design-service/instance/{instance_id}/f3mf?type=download&fileType=3mfstl"
        try:
            r = self.session.get(api_url, headers=self._api_headers(referer=page_url, cookie=cookie), timeout=30)
            if r.status_code != 200: return None
            return self._extract_download_url(r.json(), api_url)
        except Exception as e:
            print(f"[MAKERWORLD] Erreur instance: {e}")
            return None
    
    def _fetch_model_download_url(self, model_id, page_url, nonce=None, cookie=None):
        api_url = f"https://makerworld.com/api/v1/models/{model_id}/download"
        try:
            r = self.session.get(api_url, headers=self._api_headers(referer=page_url, nonce=nonce, cookie=cookie), timeout=30)
            if r.status_code != 200: return None
            return self._extract_download_url(r.json(), api_url)
        except Exception as e:
            print(f"[MAKERWORLD] Erreur model: {e}")
            return None
    
    def download_model(self, url, dest_folder, download_id=None, cookie=None):
        try:
            print(f"[MAKERWORLD] 🌍 Démarrage: {url}")
            
            headers = self._html_headers(referer=url, cookie=cookie)
            r = self.session.get(url, headers=headers, timeout=30)
            if r.status_code != 200:
                return None, f"Erreur HTTP {r.status_code}"
            
            final_url = r.url
            content_type = r.headers.get("Content-Type", "")
            
            if "html" in content_type:
                html = r.text
                next_data = self._extract_next_data(html)
                
                download_url = None
                nonce = None
                instance_id = None
                model_id = None
                
                if next_data:
                    download_url = self._find_download_url_in_json(next_data, final_url)
                    if download_url:
                        print(f"[MAKERWORLD] ✅ URL trouvée dans __NEXT_DATA__")
                    nonce = self._get_nonce(next_data)
                    instance_id = self._get_instance_id(next_data)
                    model_id = self._get_model_id_from_data(next_data)
                
                if not download_url and instance_id:
                    print(f"[MAKERWORLD] 🔍 Essai instance ID: {instance_id}")
                    download_url = self._fetch_instance_download_url(instance_id, final_url, cookie)
                
                if not download_url:
                    model_id = model_id or self._extract_model_id(final_url)
                    if model_id:
                        print(f"[MAKERWORLD] 🔍 Essai model ID: {model_id}")
                        download_url = self._fetch_model_download_url(model_id, final_url, nonce, cookie)
                
                if not download_url and model_id:
                    for api_url in [f"https://makerworld.com/api/v1/models/{model_id}", f"https://makerworld.com/api/v1/models/{model_id}/files"]:
                        try:
                            r2 = self.session.get(api_url, headers=self._api_headers(referer=final_url, cookie=cookie), timeout=15)
                            if r2.status_code == 200:
                                download_url = self._find_download_url_in_json(r2.json(), api_url)
                                if download_url: break
                        except:
                            continue
                
                if not download_url:
                    return None, "Aucun fichier téléchargeable trouvé. Modèle privé ou cookie invalide ?"
                
                print(f"[MAKERWORLD] ⬇️ Téléchargement...")
                r = self.session.get(download_url, headers=self._html_headers(referer=final_url, cookie=cookie), stream=True, timeout=120)
                r.raise_for_status()
                final_url = download_url
            
            parsed_url = urlparse(final_url)
            filename = os.path.basename(parsed_url.path) or "makerworld_model.3mf"
            filename = unquote(filename)
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            if not filename.lower().endswith(('.stl', '.obj', '.3mf', '.gcode', '.bgcode')):
                filename += '.3mf'
            
            total_size = int(r.headers.get('content-length', 0))
            if download_id:
                active_downloads[download_id] = {
                    'active': True, 'filename': filename, 'current': 0,
                    'total': total_size, 'percentage': 0, 'cancelled': False
                }
            
            save_path = os.path.join(dest_folder, filename)
            counter = 1
            while os.path.exists(save_path):
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{counter}{ext}"
                save_path = os.path.join(dest_folder, filename)
                counter += 1
            
            downloaded = 0
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if download_id and download_id in active_downloads:
                        if active_downloads[download_id].get('cancelled'):
                            f.close()
                            if os.path.exists(save_path):
                                os.unlink(save_path)
                            return None, "Téléchargement annulé"
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if download_id and download_id in active_downloads and total_size > 0:
                            active_downloads[download_id]['current'] = downloaded
                            active_downloads[download_id]['total'] = total_size
                            active_downloads[download_id]['percentage'] = (downloaded / total_size * 100)
            
            print(f"[MAKERWORLD] ✅ Terminé: {save_path}")
            
            if download_id and download_id in active_downloads:
                active_downloads[download_id]['active'] = False
            
            return {'filename': filename, 'path': save_path, 'size': downloaded}, None
            
        except Exception as e:
            print(f"[MAKERWORLD] ❌ Erreur: {e}")
            if download_id and download_id in active_downloads:
                active_downloads[download_id]['active'] = False
            return None, str(e)


# Instances globales
printables_importer = PrintablesImporter()
makerworld_importer = MakerWorldImporter()

def detect_platform(url):
    """Détection des plateformes avec support MakerWorld"""
    url_lower = url.lower()
    if 't.me/' in url_lower or 'telegram.me/' in url_lower:
        return 'telegram'
    if 'cdn' in url_lower and 'telegram' in url_lower:
        return 'telegram'
    if 'telegram.org/file' in url_lower:
        return 'telegram'
    if 'cults3d.com' in url_lower:
        cults_match = re.search(r'cults3d\.com/(?:[a-z]{2}/)?(?:m/|[^/]+/[^/]+/)?(\d+)', url, re.IGNORECASE)
        if cults_match:
            return 'cults'
        return None
    if 'thingiverse.com' in url_lower:
        thingi_match = re.search(r'thingiverse\.com/(?:thing:|download:)?(\d+)', url, re.IGNORECASE)
        if thingi_match:
            return 'thingiverse'
        if 'cdn.thingiverse.com' in url_lower or 'thingiverse.com/assets' in url_lower:
            return 'thingiverse'
        return None
    if 'makerworld.com' in url_lower:
        mw_match = re.search(r'makerworld\.com/(?:[a-z]{2}/)?model[s]?/(\d+)', url, re.IGNORECASE)
        if mw_match:
            return 'makerworld'
        if 'makerworld.com' in url_lower:
            return 'makerworld'
        return None
    if 'printables.com' in url_lower:
        printable_match = re.search(r'printables\.com/(?:[a-z]{2}/)?model/(\d+)', url, re.IGNORECASE)
        if printable_match:
            return 'printables'
        return None
    return None

# ══════════ HEADERS COMMUNS POUR ÉVITER LES BLOCAGES ══════════
COMMON_BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1'
}

DOWNLOAD_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
}

@app.route('/api/download', methods=['POST'])
@login_required
def api_download_file():
    try:
        data = request.json
        if not data:
            app.logger.error("[Download] Données JSON invalides ou manquantes")
            return jsonify({"error": "Données invalides"}), 400
            
        url = data.get('url', '').strip()
        target_source_id = data.get('target_source_id')
        download_id = data.get('download_id', int(time.time() * 1000))
        
        app.logger.info(f"[Download] URL: {url}, Source ID: {target_source_id}")
        
        if not url:
            return jsonify({"error": "URL requise"}), 400
        
        platform = detect_platform(url)
        if not platform:
            return jsonify({"error": f"Plateforme non supportée ou URL invalide: {url}"}), 400
        
        # ✅ UNE SEULE CONNEXION DB pour tout le traitement
        conn = get_db()
        
        # ✅ DÉTERMINER LE DOSSIER DE DESTINATION
        source_name = 'Downloads'
        if target_source_id:
            source = conn.execute(
                "SELECT * FROM sources WHERE id = ? AND user_id = ?",
                (target_source_id, session['user_id'])
            ).fetchone()
            if not source:
                conn.close()
                return jsonify({"error": "Source invalide"}), 400
            dest_folder = source['path']
            if source['type'] == 'folder' and not os.path.exists(dest_folder):
                os.makedirs(dest_folder, exist_ok=True)
            source_name = source['name']
        else:
            dest_folder = UPLOADS_DIR
            source_name = 'Downloads'
            app.logger.info(f"[Download] Aucune source spécifiée, utilisation de: {dest_folder}")
        
        # ✅ GESTION DES COMPTES SELON LA PLATEFORME (UNE SEULE REQUÊTE)
        account = conn.execute(
            "SELECT * FROM account_credentials WHERE user_id = ? AND platform = ?",
            (session['user_id'], platform)
        ).fetchone()
        
        # Fermer la connexion DB AVANT les téléchargements longs
        conn.close()
        
        password = None
        email = None
        api_key = None
        session_cookies = None
        
        if account:
            password = decrypt_password(account['password_encrypted']) if account['password_encrypted'] else None
            email = account['email']
            api_key = account['api_key']
            session_cookies = account['session_cookies']
        
        # Vérifier les comptes requis
        if platform in ['cults', 'thingiverse'] and not account:
            return jsonify({"error": f"Compte {platform} non configuré"}), 400
        
        # ══════════ PRINTABLES ══════════
        if platform == 'printables':
            print(f"[PRINTABLES] 🚀 Démarrage: {url}")
            result, error = printables_importer.download_model(url, dest_folder, download_id)
            if error:
                if download_id in active_downloads:
                    active_downloads[download_id]['active'] = False
                return jsonify({"error": error}), 500
            invalidate_cache()
            if download_id in active_downloads:
                active_downloads[download_id]['active'] = False
            return jsonify({
                "message": "Succès",
                "filename": result['filename'],
                "path": result['path'],
                "source": source_name,
                "size": result['size']
            }), 200
                        
        # ══════════ MAKERWORLD ══════════
        elif platform == 'makerworld':
            print(f"[MAKERWORLD] 🌍 Démarrage: {url}")
            
            mw_cookie = session_cookies if session_cookies else None
            
            if mw_cookie:
                print(f"[MAKERWORLD] 🍪 Cookie de session utilisé")
            else:
                print(f"[MAKERWORLD] ℹ️ Aucun cookie configuré (modèles publics uniquement)")
            
            result, error = makerworld_importer.download_model(
                url, dest_folder, download_id, cookie=mw_cookie
            )
            
            if error:
                if download_id in active_downloads:
                    active_downloads[download_id]['active'] = False
                return jsonify({"error": error}), 500
            
            invalidate_cache()
            if download_id in active_downloads:
                active_downloads[download_id]['active'] = False
            
            return jsonify({
                "message": "Succès",
                "filename": result['filename'],
                "path": result['path'],
                "source": source_name,
                "size": result['size']
            }), 200
        
        # ══════════ TELEGRAM (INTACT) ══════════
        elif platform == 'telegram':
            try:
                from telethon.sync import TelegramClient as SyncClient
                from telethon.tl.types import MessageMediaDocument
                from telethon.sessions import StringSession as SyncStringSession
                from telethon.errors import FloodWaitError, ChatAdminRequiredError, ChannelPrivateError, UsernameNotOccupiedError
                
                app.logger.info(f"🔍 Tentative de téléchargement Telegram: {url}")
                
                if not account['telegram_session']:
                    return jsonify({"error": "Session Telegram manquante"}), 400
                
                tg_creds = get_telegram_credentials(session['user_id'])
                if not tg_creds:
                    return jsonify({"error": "Credentials Telegram manquants"}), 400
                
                API_ID = int(tg_creds['api_id'])
                API_HASH = tg_creds['api_hash']
                string_session = SyncStringSession(account['telegram_session'])
                
                with SyncClient(string_session, API_ID, API_HASH) as client:
                    if not client.is_user_authorized():
                        return jsonify({"error": "Non autorisé. Reconnectez-vous à Telegram."}), 401
                    
                    clean_url = url.split('?')[0].strip()
                    match = re.match(r'https?://t\.me/(?:c/)?([^/]+)/(\d+)', clean_url)
                    
                    if not match:
                        return jsonify({"error": f"URL Telegram invalide: {url}"}), 400
                    
                    chat_identifier = match.group(1)
                    message_id = int(match.group(2))
                    
                    try:
                        entity = client.get_entity(chat_identifier)
                    except (UsernameNotOccupiedError, ValueError):
                        try:
                            entity = client.get_entity(f"https://t.me/{chat_identifier}")
                        except Exception as e2:
                            return jsonify({"error": f"Channel '{chat_identifier}' introuvable."}), 404
                    except ChannelPrivateError:
                        return jsonify({"error": f"Le channel '{chat_identifier}' est privé."}), 403
                    except ChatAdminRequiredError:
                        return jsonify({"error": f"Permissions insuffisantes pour '{chat_identifier}'"}), 403
                    except Exception as e:
                        return jsonify({"error": f"Erreur accès channel: {str(e)[:100]}"}), 500
                    
                    try:
                        message = client.get_messages(entity, ids=message_id)
                    except Exception as e:
                        return jsonify({"error": f"Impossible de récupérer le message: {str(e)[:100]}"}), 500
                    
                    if not message:
                        return jsonify({"error": f"Message {message_id} non trouvé"}), 404
                    
                    if not message.media or not isinstance(message.media, MessageMediaDocument):
                        return jsonify({"error": "Ce message ne contient pas de fichier"}), 400
                    
                    filename = None
                    if message.media.document:
                        attrs = message.media.document.attributes or []
                        for attr in attrs:
                            if hasattr(attr, 'file_name') and attr.file_name:
                                filename = attr.file_name
                                break
                    
                    if not filename:
                        mime_type = message.media.document.mime_type if message.media.document else None
                        ext = '.bin'
                        if mime_type:
                            if 'zip' in mime_type: ext = '.zip'
                            elif 'stl' in mime_type: ext = '.stl'
                            elif '3mf' in mime_type: ext = '.3mf'
                            elif 'rar' in mime_type: ext = '.rar'
                        filename = f"telegram_{message_id}{ext}"
                    
                    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
                    file_size = message.media.document.size if message.media.document else 0
                    
                    active_downloads[download_id] = {
                        'active': True, 'filename': filename, 'current': 0,
                        'total': file_size, 'percentage': 0, 'cancelled': False
                    }
                    
                    def progress_callback(current, total):
                        if download_id in active_downloads and active_downloads[download_id].get('cancelled'):
                            raise InterruptedError("Cancelled")
                        if download_id in active_downloads:
                            active_downloads[download_id]['current'] = current
                            active_downloads[download_id]['total'] = total
                            active_downloads[download_id]['percentage'] = (current / total * 100) if total > 0 else 0
                    
                    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.bin')
                    os.close(tmp_fd)
                    
                    try:
                        file_path_dl = client.download_media(message, file=tmp_path, progress_callback=progress_callback)
                        
                        if not file_path_dl:
                            raise Exception("download_media a retourné None")
                        
                        with open(file_path_dl, 'rb') as f:
                            file_content = f.read()
                        
                        if os.path.exists(file_path_dl):
                            os.unlink(file_path_dl)
                        
                        save_path = os.path.join(dest_folder, filename)
                        counter = 1
                        while os.path.exists(save_path):
                            name, ext = os.path.splitext(filename)
                            filename = f"{name}_{counter}{ext}"
                            save_path = os.path.join(dest_folder, filename)
                            counter += 1
                        
                        with open(save_path, 'wb') as f:
                            f.write(file_content)
                        
                        invalidate_cache()
                        
                        if download_id in active_downloads:
                            active_downloads[download_id]['active'] = False
                        
                        return jsonify({
                            "message": "Succès",
                            "filename": filename,
                            "path": save_path,
                            "source": source_name,
                            "size": file_size
                        }), 200
                        
                    except InterruptedError:
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                        if download_id in active_downloads:
                            del active_downloads[download_id]
                        return jsonify({"error": "Téléchargement annulé"}), 499
                    except Exception as e:
                        raise
                        
            except FloodWaitError as e:
                if download_id in active_downloads:
                    active_downloads[download_id]['active'] = False
                return jsonify({"error": f"Telegram limite: réessayez dans {e.seconds} secondes"}), 429
            except Exception as e:
                app.logger.error(f"💥 Erreur Telegram: {type(e).__name__}: {e}")
                if download_id in active_downloads:
                    active_downloads[download_id]['active'] = False
                return jsonify({"error": f"Erreur Telegram: {str(e)[:200]}"}), 500
        
        # ══════════ CULTS3D ══════════
        elif platform == 'cults':
            model_id_match = re.search(r'cults3d\.com/(?:[a-z]{2}/)?(?:m/|[^/]+/[^/]+/)?(\d+)', url, re.IGNORECASE)
            
            if not model_id_match:
                return jsonify({"error": "Impossible d'extraire l'ID du modèle Cults3D."}), 400
            
            model_id = model_id_match.group(1)
            print(f"[CULTS DOWNLOAD] Modèle ID: {model_id}")
            
            # ✅ Session avec headers complets
            cults_session = requests.Session()
            cults_session.headers.update(COMMON_BROWSER_HEADERS)
            cults_session.headers.update({
                'Referer': 'https://cults3d.com/',
                'Origin': 'https://cults3d.com'
            })
            
            if api_key:
                cults_session.headers.update({'Authorization': f'Bearer {api_key}'})
            
            graphql_response = cults_session.post(
                'https://cults3d.com/graphql',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}',
                    'Accept': 'application/json'
                },
                json={
                    'query': f'''
                    query {{
                        model(id: {model_id}) {{
                            id
                            name
                            media {{
                                url
                            }}
                        }}
                    }}
                    '''
                },
                timeout=30
            )
            
            if graphql_response.status_code != 200:
                return jsonify({"error": f"Erreur API Cults3D: {graphql_response.status_code}"}), 400
            
            graphql_data = graphql_response.json()
            
            if 'errors' in graphql_data:
                return jsonify({"error": f"Erreur GraphQL: {graphql_data['errors'][0]['message']}"}), 400
            
            model_data = graphql_data.get('data', {}).get('model', {})
            if not model_data:
                return jsonify({"error": "Modèle non trouvé sur Cults3D"}), 404
            
            download_url = None
            for media in model_data.get('media', []):
                media_url = media.get('url', '')
                if any(ext in media_url.lower() for ext in ['.stl', '.obj', '.3mf', '.zip']):
                    download_url = media_url
                    break
            
            if not download_url:
                return jsonify({"error": "Aucun fichier 3D trouvé pour ce modèle"}), 404
            
            url = download_url
            
            # ✅ Télécharger avec la même session (garde les cookies)
            active_downloads[download_id] = {
                'active': True, 'filename': '', 'current': 0,
                'total': 0, 'percentage': 0, 'cancelled': False
            }
            
            response = cults_session.get(url, stream=True, timeout=120)
            if response.status_code == 401:
                if download_id in active_downloads:
                    del active_downloads[download_id]
                return jsonify({"error": "Authentification requise"}), 401
            response.raise_for_status()
            
            content_disposition = response.headers.get('content-disposition', '')
            filename_match = re.findall('filename="?([^";]+)"?', content_disposition)
            filename = unquote(filename_match[0]) if filename_match else os.path.basename(unquote(urlparse(url).path)) or f"cults_{model_id}.stl"
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            if not filename.endswith(('.stl', '.obj', '.3mf', '.zip')):
                filename += '.stl'
            
            if download_id in active_downloads:
                active_downloads[download_id]['filename'] = filename
            
            save_path = os.path.join(dest_folder, filename)
            counter = 1
            while os.path.exists(save_path):
                filename = f"{os.path.splitext(filename)[0]}_{counter}{os.path.splitext(filename)[1]}"
                save_path = os.path.join(dest_folder, filename)
                counter += 1
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if download_id in active_downloads and active_downloads[download_id].get('cancelled'):
                        f.close()
                        if os.path.exists(save_path):
                            os.unlink(save_path)
                        if download_id in active_downloads:
                            del active_downloads[download_id]
                        return jsonify({"error": "Téléchargement annulé"}), 499
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if download_id in active_downloads and total_size > 0:
                            active_downloads[download_id]['current'] = downloaded
                            active_downloads[download_id]['total'] = total_size
                            active_downloads[download_id]['percentage'] = (downloaded / total_size * 100)
            
            invalidate_cache()
            if download_id in active_downloads:
                active_downloads[download_id]['active'] = False
            
            cults_session.close()
            
            return jsonify({
                "message": "Succès",
                "filename": filename,
                "path": save_path,
                "source": source_name,
                "size": downloaded
            }), 200

        # ══════════ THINGIVERSE ══════════
        elif platform == 'thingiverse':
            if not api_key:
                return jsonify({"error": "Token API Thingiverse manquant"}), 400
            
            thing_id_match = re.search(r'thingiverse\.com/(?:thing:|download:)?(\d+)', url, re.IGNORECASE)
            
            if not thing_id_match:
                if 'cdn.thingiverse.com' in url or 'thingiverse.com/assets' in url:
                    print(f"[THINGIVERSE] Téléchargement direct depuis CDN")
                else:
                    return jsonify({"error": "Impossible d'extraire l'ID du modèle Thingiverse"}), 400
            else:
                thing_id = thing_id_match.group(1)
                print(f"[THINGIVERSE DOWNLOAD] Thing ID: {thing_id}")
                
                # ✅ Session avec headers complets
                thingi_session = requests.Session()
                thingi_session.headers.update(COMMON_BROWSER_HEADERS)
                thingi_session.headers.update({
                    'Authorization': f'Bearer {api_key}',
                    'Referer': 'https://www.thingiverse.com/',
                    'Origin': 'https://www.thingiverse.com'
                })
                
                try:
                    files_response = thingi_session.get(
                        f'https://api.thingiverse.com/things/{thing_id}/files',
                        timeout=30
                    )
                    
                    if files_response.status_code == 200:
                        files_data = files_response.json()
                        
                        download_url = None
                        filename = f"thing_{thing_id}"
                        
                        if isinstance(files_data, list) and len(files_data) > 0:
                            for file_obj in files_data:
                                file_url = file_obj.get('download_url') or file_obj.get('public_url') or file_obj.get('url', '')
                                file_name = file_obj.get('name', '')
                                
                                if any(ext in file_url.lower() for ext in ['.stl', '.obj', '.3mf']):
                                    download_url = file_url
                                    filename = file_name or f"thing_{thing_id}"
                                    break
                            
                            if download_url:
                                url = download_url
                            else:
                                return jsonify({"error": "Aucun fichier 3D trouvé"}), 404
                        else:
                            thing_response = thingi_session.get(
                                f'https://api.thingiverse.com/things/{thing_id}',
                                timeout=30
                            )
                            
                            if thing_response.status_code == 200:
                                thing_data = thing_response.json()
                                filename = thing_data.get('name', f'thing_{thing_id}')
                                
                                if 'files' in thing_data and isinstance(thing_data['files'], list):
                                    for file_obj in thing_data['files']:
                                        file_url = file_obj.get('public_url', '')
                                        if any(ext in file_url.lower() for ext in ['.stl', '.obj', '.3mf', '.zip']):
                                            url = file_url
                                            if not filename.endswith(('.stl', '.obj', '.3mf', '.zip')):
                                                filename = os.path.basename(urlparse(file_url).path) or filename
                                            break
                                else:
                                    return jsonify({"error": "Aucun fichier disponible"}), 404
                            else:
                                return jsonify({"error": f"Erreur API Thingiverse: {thing_response.status_code}"}), 400
                    else:
                        return jsonify({"error": f"Erreur API Thingiverse: {files_response.status_code}"}), 400
                        
                except Exception as e:
                    return jsonify({"error": f"Erreur Thingiverse: {str(e)}"}), 500
            
            # ✅ Télécharger avec la même session
            active_downloads[download_id] = {
                'active': True, 'filename': '', 'current': 0,
                'total': 0, 'percentage': 0, 'cancelled': False
            }
            
            response = thingi_session.get(url, stream=True, timeout=120)
            if response.status_code == 401:
                if download_id in active_downloads:
                    del active_downloads[download_id]
                return jsonify({"error": "Authentification requise"}), 401
            response.raise_for_status()
            
            content_disposition = response.headers.get('content-disposition', '')
            filename_match = re.findall('filename="?([^";]+)"?', content_disposition)
            filename = unquote(filename_match[0]) if filename_match else os.path.basename(unquote(urlparse(url).path)) or f"thing_{thing_id}.stl"
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            if not filename.endswith(('.stl', '.obj', '.3mf', '.zip')):
                filename += '.stl'
            
            if download_id in active_downloads:
                active_downloads[download_id]['filename'] = filename
            
            save_path = os.path.join(dest_folder, filename)
            counter = 1
            while os.path.exists(save_path):
                filename = f"{os.path.splitext(filename)[0]}_{counter}{os.path.splitext(filename)[1]}"
                save_path = os.path.join(dest_folder, filename)
                counter += 1
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if download_id in active_downloads and active_downloads[download_id].get('cancelled'):
                        f.close()
                        if os.path.exists(save_path):
                            os.unlink(save_path)
                        if download_id in active_downloads:
                            del active_downloads[download_id]
                        return jsonify({"error": "Téléchargement annulé"}), 499
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if download_id in active_downloads and total_size > 0:
                            active_downloads[download_id]['current'] = downloaded
                            active_downloads[download_id]['total'] = total_size
                            active_downloads[download_id]['percentage'] = (downloaded / total_size * 100)
            
            invalidate_cache()
            if download_id in active_downloads:
                active_downloads[download_id]['active'] = False
            
            thingi_session.close()
            
            return jsonify({
                "message": "Succès",
                "filename": filename,
                "path": save_path,
                "source": source_name,
                "size": downloaded
            }), 200
        
        else:
            return jsonify({"error": f"Plateforme non gérée: {platform}"}), 400
        
    except Exception as e:
        app.logger.error(f"[Download] Erreur: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)[:200]}), 500

@app.route('/api/download/progress/<int:download_id>', methods=['GET'])
@login_required
def api_download_progress(download_id):
    if download_id in active_downloads:
        data = active_downloads[download_id]
        return jsonify({
            'active': data.get('active', False),
            'download_id': download_id,
            'filename': data.get('filename', ''),
            'current': data.get('current', 0),
            'total': data.get('total', 0),
            'percentage': round(data.get('percentage', 0), 1)
        })
    return jsonify({'active': False, 'download_id': download_id})

@app.route('/api/download/cancel/<int:download_id>', methods=['POST'])
@login_required
def api_cancel_download(download_id):
    if download_id in active_downloads:
        active_downloads[download_id]['cancelled'] = True
        active_downloads[download_id]['active'] = False
        return jsonify({"message": "Annulation demandée"}), 200
    return jsonify({"error": "Téléchargement non trouvé"}), 404

def scan_local_folder(folder_path):
    files = []
    if not os.path.exists(folder_path):
        return files
    extensions_3d = {'.stl', '.obj', '.3mf'}
    extensions_archive = {'.zip', '.rar', '.7z', '.tar.gz', '.tgz'}
    for root, dirs, filenames in os.walk(folder_path):
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            file_path = os.path.join(root, filename)
            try:
                file_size = os.path.getsize(file_path)
            except Exception:
                continue
            if ext in extensions_archive or filename.lower().endswith('.tar.gz'):
                try:
                    if filename.lower().endswith('.tar.gz'):
                        extract_folder = os.path.join(root, filename[:-7])
                    else:
                        extract_folder = os.path.splitext(file_path)[0]
                    os.makedirs(extract_folder, exist_ok=True)
                    extracted_count = 0
                    if ext == '.zip':
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            zip_ref.extractall(extract_folder)
                            extracted_count = len(zip_ref.namelist())
                    elif ext == '.rar':
                        if rarfile.UNRAR_TOOL and os.path.exists(rarfile.UNRAR_TOOL):
                            with rarfile.RarFile(file_path, 'r') as rf:
                                rf.extractall(extract_folder)
                                extracted_count = len(rf.namelist())
                    elif ext == '.7z':
                        try:
                            import py7zr
                            with py7zr.SevenZipFile(file_path, mode='r') as z:
                                z.extractall(path=extract_folder)
                                extracted_count = len(z.getnames())
                        except ImportError:
                            continue
                    elif ext in ['.tar.gz', '.tgz', '.tar.bz2', '.tar.xz', '.tar']:
                        with tarfile.open(file_path, 'r:*') as tar_ref:
                            tar_ref.extractall(extract_folder)
                            extracted_count = len(tar_ref.getnames())
                    for extracted_file in os.listdir(extract_folder):
                        extracted_ext = os.path.splitext(extracted_file)[1].lower()
                        if extracted_ext in extensions_3d:
                            extracted_path = os.path.join(extract_folder, extracted_file)
                            normalized_path = extracted_path.replace('\\', '/')
                            thumb_filename = hashlib.md5(normalized_path.encode()).hexdigest()
                            thumb_path = os.path.join(THUMBNAILS_DIR, thumb_filename + '.png')
                            files.append({
                                'name': extracted_file,
                                'path': normalized_path,
                                'extension': extracted_ext,
                                'size': os.path.getsize(extracted_path),
                                'source': os.path.basename(folder_path),
                                'date_added': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'has_thumb': os.path.exists(thumb_path),
                                'has_metadata': False
                            })
                    if extracted_count > 0:
                        os.remove(file_path)
                except Exception as e:
                    print(f"    Erreur extraction: {e}")
                    continue
            if ext in extensions_3d:
                try:
                    normalized_path = file_path.replace('\\', '/')
                    thumb_filename = hashlib.md5(normalized_path.encode()).hexdigest()
                    thumb_path = os.path.join(THUMBNAILS_DIR, thumb_filename + '.png')
                    files.append({
                        'name': filename,
                        'path': normalized_path,
                        'extension': ext,
                        'size': file_size,
                        'source': os.path.basename(folder_path),
                        'date_added': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'has_thumb': os.path.exists(thumb_path),
                        'has_metadata': False
                    })
                except Exception as e:
                    print(f"    Erreur lecture {filename}: {e}")
    return files

def scan_smb_folder_recursive(base_path, current_subdir, kwargs, source_name):
    files = []
    current_path = f"{base_path}/{current_subdir}" if current_subdir else base_path
    folders_to_skip = ['.recycle', '$recycle.bin', 'system volume information', '@eaDir', '.@__thumb']
    try:
        if any(skip_folder in current_path.lower() for skip_folder in folders_to_skip):
            print(f"[SMB] Dossier système ignoré: {current_path}")
            return files
        if not smbclient.path.exists(current_path, **kwargs):
            print(f"[SMB] Chemin inaccessible: {current_path}")
            return files
        entries = smbclient.listdir(current_path, **kwargs)
        for entry in entries:
            if entry.startswith('.') or entry.startswith('$'):
                continue
            entry_path = f"{current_subdir}/{entry}" if current_subdir else entry
            full_path = f"{base_path}/{entry_path}"
            try:
                info = smbclient.stat(full_path, **kwargs)
                if (info.st_mode & 0o170000) == 0o040000:  # C'est un dossier
                    if entry.lower() not in folders_to_skip:
                        files.extend(scan_smb_folder_recursive(base_path, entry_path, kwargs, source_name))
                elif entry.lower().endswith(('.stl', '.obj', '.3mf')):
                    normalized_path = full_path.replace('\\', '/')
                    thumb_filename = hashlib.md5(normalized_path.encode()).hexdigest()
                    thumb_path = os.path.join(THUMBNAILS_DIR, thumb_filename + '.png')
                    files.append({
                        'name': entry,
                        'path': normalized_path,
                        'extension': f".{entry.split('.')[-1]}",
                        'size': info.st_size,
                        'source': source_name,
                        'date_added': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'subdir': current_subdir,
                        'has_thumb': os.path.exists(thumb_path),
                        'has_metadata': False
                    })
            except Exception as e:
                if "ACCESS_DENIED" not in str(e):
                    print(f"[SMB] Erreur lecture {entry}: {e}")
                continue
    except Exception as e:
        error_msg = str(e)
        if "ACCESS_DENIED" not in error_msg:
            print(f"[SMB] Erreur connexion: {e}")
    return files

def check_source_changes(sources_list, cache_timestamp):
    try:
        for src in sources_list:
            if src['type'] == 'folder' and os.path.exists(src['path']) and os.path.getmtime(src['path']) > cache_timestamp:
                return True
            elif src['type'] == 'smb' and time.time() - cache_timestamp > 120:
                return True
        return False
    except:
        return True

def deduplicate_files_hybrid(files):
    seen_names = set()
    candidates = []
    for f in files:
        key = (f['name'].lower(), f['extension'].lower())
        if key not in seen_names:
            seen_names.add(key)
            candidates.append(f)
    size_groups = {}
    for f in candidates:
        size_groups.setdefault(f.get('size', 0), []).append(f)
    final_unique = []
    md5_candidates = []
    for size, group in size_groups.items():
        if len(group) == 1:
            final_unique.append(group[0])
        else:
            md5_candidates.extend(group)
    if md5_candidates:
        seen_hashes = {}
        for f in md5_candidates:
            md5 = hashlib.md5(f.get('path', '').encode()).hexdigest()
            if md5 not in seen_hashes:
                seen_hashes[md5] = f
        final_unique.extend(seen_hashes.values())
    return sorted(final_unique, key=lambda x: x.get('path', ''))

@app.route('/api/files/decompress', methods=['POST'])
@login_required
def api_decompress_archive():
    data = request.json
    archive_path = data.get('file_path')
    if not archive_path or not os.path.exists(archive_path):
        return jsonify({"error": "Archive non trouvée"}), 404
    ext = os.path.splitext(archive_path)[1].lower()
    extract_dir = os.path.dirname(archive_path)
    archive_name = os.path.splitext(os.path.basename(archive_path))[0]
    target_dir = os.path.join(extract_dir, archive_name)
    os.makedirs(target_dir, exist_ok=True)
    try:
        if ext == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
                extracted_files = zip_ref.namelist()
        elif ext in ['.tar.gz', '.tgz', '.tar.bz2', '.tar.xz', '.tar']:
            with tarfile.open(archive_path, 'r:*') as tar_ref:
                tar_ref.extractall(target_dir)
                extracted_files = tar_ref.getnames()
        elif ext == '.7z':
            try:
                import py7zr
                with py7zr.SevenZipFile(archive_path, mode='r') as z:
                    z.extractall(path=target_dir)
                    extracted_files = z.getnames()
            except ImportError:
                shutil.rmtree(target_dir, ignore_errors=True)
                return jsonify({"error": "Module 'py7zr' manquant"}), 500
        elif ext == '.rar':
            try:
                with rarfile.RarFile(archive_path, 'r') as rf:
                    rf.extractall(path=target_dir)
                    extracted_files = rf.namelist()
            except ImportError:
                shutil.rmtree(target_dir, ignore_errors=True)
                return jsonify({"error": "Module 'rarfile' manquant"}), 500
        else:
            return jsonify({"error": "Format non supporté"}), 400
        found_3d_files = []
        for f in extracted_files:
            full_path = os.path.join(target_dir, f)
            if os.path.isfile(full_path) and os.path.splitext(f)[1].lower() in SUPPORTED_3D_EXTS:
                found_3d_files.append(full_path)
        return jsonify({
            "success": True,
            "archive_path": archive_path,
            "extracted_folder": target_dir,
            "found_3d_files": found_3d_files,
            "message": f"Extraction terminée. {len(found_3d_files)} fichier(s) 3D trouvé(s)."
        }), 200
    except Exception as e:
        if os.path.exists(target_dir) and not os.listdir(target_dir):
            os.rmdir(target_dir)
        return jsonify({"error": f"Erreur extraction: {str(e)}"}), 500

@app.route('/api/files/cleanup-archive', methods=['POST'])
@login_required
def api_cleanup_archive():
    data = request.json
    archive_path = data.get('archive_path')
    if not archive_path or not os.path.exists(archive_path):
        return jsonify({"error": "Archive déjà supprimée"}), 404
    try:
        os.remove(archive_path)
        invalidate_cache()
        return jsonify({"success": True, "message": "Archive supprimée"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tags', methods=['GET'])
@login_required
def api_get_tags():
    conn = get_db()
    tags = conn.execute(
        "SELECT t.id, t.name, t.color, COUNT(ft.file_path) as count FROM tags t LEFT JOIN file_tags ft ON t.id = ft.tag_id GROUP BY t.id ORDER BY t.name"
    ).fetchall()
    conn.close()
    return jsonify([dict(t) for t in tags])

@app.route('/api/tags', methods=['POST'])
@login_required
def api_create_tag():
    data = request.json
    name = data.get('name', '').strip()
    color = data.get('color', '#4ea1d3')
    if not name:
        return jsonify({"error": "Nom requis"}), 400
    conn = get_db()
    try:
        conn.execute("INSERT INTO tags (name, color) VALUES (?, ?)", (name, color))
        conn.commit()
        return jsonify({
            "id": conn.execute("SELECT last_insert_rowid()").fetchone()[0],
            "name": name,
            "color": color
        }), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Existant"}), 409
    finally:
        conn.close()

@app.route('/api/tags/<int:tag_id>', methods=['PUT'])
@login_required
def api_update_tag(tag_id):
    data = request.json
    name = data.get('name', '').strip()
    color = data.get('color')
    if not name:
        return jsonify({"error": "Nom requis"}), 400
    conn = get_db()
    try:
        if color:
            conn.execute("UPDATE tags SET name = ?, color = ? WHERE id = ?", (name, color, tag_id))
        else:
            conn.execute("UPDATE tags SET name = ? WHERE id = ?", (name, tag_id))
        conn.commit()
        return jsonify({"message": "Mis à jour"}), 200
    except:
        return jsonify({"error": "Erreur"}), 500
    finally:
        conn.close()

@app.route('/api/tags/<int:tag_id>', methods=['DELETE'])
@login_required
def api_delete_tag(tag_id):
    conn = get_db()
    conn.execute("DELETE FROM file_tags WHERE tag_id = ?", (tag_id,))
    conn.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Supprimé"}), 200

@app.route('/api/files/tags', methods=['POST'])
@login_required
def api_assign_tags():
    data = request.json
    file_path = data.get('path')
    tags = data.get('tags', [])
    if not file_path:
        return jsonify({"error": "Chemin requis"}), 400
    conn = get_db()
    try:
        conn.execute("DELETE FROM file_tags WHERE file_path = ?", (file_path,))
        for tag_name in tags:
            tag_name = tag_name.strip()
            if not tag_name:
                continue
            conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
            tid = conn.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()[0]
            conn.execute("INSERT OR IGNORE INTO file_tags (file_path, tag_id) VALUES (?, ?)", (file_path, tid))
        conn.commit()
        return jsonify({"message": "Assignés"}), 200
    except:
        return jsonify({"error": "Erreur"}), 500
    finally:
        conn.close()

@app.route('/api/files', methods=['GET'])
@login_required
def api_get_files():
    try:
        conn = get_db()
        sources = conn.execute("SELECT * FROM sources WHERE user_id = ?", (session['user_id'],)).fetchall()
        sources_list = [dict(s) for s in sources]
        last_check = float(request.args.get('since', 0))
        tag_filter = request.args.get('tags', '')
        cached_files = load_file_cache()
        cache_data = None
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
            except json.JSONDecodeError:
                print("[WARN] Cache corrompu, recréation...")
                invalidate_cache()
                cache_data = None
        needs_rescan = (cached_files is None or
                       (last_check > 0 and cache_data and cache_data.get('timestamp', 0) < last_check) or
                       check_source_changes(sources_list, cache_data.get('timestamp', 0) if cache_data else 0))
        if needs_rescan:
            print(f"[*] Scan rapide (lazy)...")
            all_files = []
            for source in sources_list:
                try:
                    if source['type'] == 'folder':
                        all_files.extend(scan_local_folder(source['path']))
                    elif source['type'] == 'smb':
                        unc_path = source['path'].replace('\\\\', '//').replace('\\', '/')
                        kwargs = {}
                        config = json.loads(source['config']) if source['config'] else {}
                        if config.get('username'):
                            kwargs['username'] = config['username']
                        if config.get('password'):
                            kwargs['password'] = config['password']
                        all_files.extend(scan_smb_folder_recursive(unc_path, '', kwargs, source['name']))
                    elif source['type'] == 'file' and os.path.exists(source['path']):
                        normalized_path = source['path'].replace('\\', '/')
                        thumb_filename = hashlib.md5(normalized_path.encode()).hexdigest()
                        thumb_path = os.path.join(THUMBNAILS_DIR, thumb_filename + '.png')
                        all_files.append({
                            'name': os.path.basename(source['path']),
                            'path': normalized_path,
                            'extension': f".{source['path'].split('.')[-1]}",
                            'size': os.path.getsize(source['path']),
                            'source': source['name'],
                            'date_added': source.get('created_at') or datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'has_thumb': os.path.exists(thumb_path),
                            'has_metadata': False
                        })
                except Exception as e:
                    print(f"    Erreur source {source['name']}: {e}")
                    import traceback
                    traceback.print_exc()
            all_files = deduplicate_files_hybrid(all_files)
            file_paths = [f['path'] for f in all_files]
            if file_paths:
                try:
                    placeholders = ','.join('?' * len(file_paths))
                    tag_results = conn.execute(
                        f"SELECT ft.file_path, t.name, t.color FROM file_tags ft JOIN tags t ON ft.tag_id = t.id WHERE ft.file_path IN ({placeholders})",
                        file_paths
                    ).fetchall()
                    tags_by_file = {}
                    for row in tag_results:
                        tags_by_file.setdefault(row['file_path'], []).append({'name': row['name'], 'color': row['color']})
                    for f in all_files:
                        f['tags'] = tags_by_file.get(f['path'], [])
                except Exception as e:
                    print(f"[WARN] Erreur chargement tags: {e}")
            try:
                save_file_cache(all_files, sources_list)
            except Exception as e:
                print(f"[ERROR] Échec sauvegarde cache: {e}")
            cached_files = all_files
            for f in cached_files:
                if not f.get('has_thumb'):
                    normalized_path = f['path']
                    thumb_filename = hashlib.md5(normalized_path.encode()).hexdigest()
                    thumb_path = os.path.join(THUMBNAILS_DIR, thumb_filename + '.png')
                    if f['path'] not in ignored_files_cache:
                        thumb_generation_queue.put({
                            'path': f['path'],
                            'thumb_path': thumb_path,
                            'priority': 'low'
                        })
        else:
            if cached_files:
                file_paths = [f['path'] for f in cached_files]
                if file_paths:
                    try:
                        placeholders = ','.join('?' * len(file_paths))
                        tag_results = conn.execute(
                            f"SELECT ft.file_path, t.name, t.color FROM file_tags ft JOIN tags t ON ft.tag_id = t.id WHERE ft.file_path IN ({placeholders})",
                            file_paths
                        ).fetchall()
                        tags_by_file = {}
                        for row in tag_results:
                            tags_by_file.setdefault(row['file_path'], []).append({'name': row['name'], 'color': row['color']})
                        for f in cached_files:
                            f['tags'] = tags_by_file.get(f['path'], [])
                    except Exception as e:
                        print(f"[WARN] Erreur rechargement tags: {e}")
        if tag_filter.strip():
            required_tags = set(t.strip().lower() for t in tag_filter.split(',') if t.strip())
            if required_tags:
                cached_files = [f for f in cached_files if required_tags.issubset(set(t['name'].lower() for t in f.get('tags', [])))]
        conn.close()
        if not isinstance(cached_files, list):
            print(f"[ERROR] cached_files n'est pas une liste: {type(cached_files)}")
            cached_files = []
        return jsonify(cached_files)
    except Exception as e:
        print(f"[api_get_files] Erreur: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([]), 500

@app.route('/api/download/create-folder', methods=['POST'])
@login_required
def api_create_download_folder():
    """Crée un nouveau dossier et optionnellement l'ajoute comme source"""
    try:
        data = request.json
        folder_path = data.get('folder_path')  # ✅ Chemin complet du nouveau dossier
        folder_name = data.get('folder_name', '').strip()
        add_as_source = data.get('add_as_source', False)  # ✅ Ajouter comme source
        
        if not folder_path or not folder_name:
            return jsonify({"error": "Chemin et nom requis"}), 400
        
        # Nettoyer le nom de dossier (sécurité)
        folder_name = re.sub(r'[<>:"/\\|?*]', '_', folder_name)
        if not folder_name:
            return jsonify({"error": "Nom de dossier invalide"}), 400
        
        # Vérifier si c'est un chemin SMB/NFS ou local
        is_smb = folder_path.startswith('//') or folder_path.startswith('\\\\')
        is_local = not is_smb
        
        if is_smb:
            # Pour SMB, utiliser smbclient
            import smbclient
            base_path = folder_path.replace('\\\\', '//').replace('\\', '/')
            config = json.loads(source['config']) if source.get('config') else {}
            
            kwargs = {}
            if config.get('username'):
                kwargs['username'] = config['username']
            if config.get('password'):
                kwargs['password'] = config['password']
            
            try:
                if not smbclient.path.exists(base_path, **kwargs):
                    smbclient.makedirs(base_path, exist_ok=True, **kwargs)
                return jsonify({
                    "success": True,
                    "message": "Dossier SMB créé",
                    "path": base_path,
                    "is_local": False,
                    "added_as_source": False  # On n'ajoute pas automatiquement les SMB
                }), 200
            except Exception as smb_err:
                return jsonify({"error": f"Erreur SMB: {str(smb_err)}"}), 500
        else:
            # Pour les dossiers locaux
            if not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)
            
            # ✅ Ajouter automatiquement comme source si demandé
            added_as_source = False
            if add_as_source and is_local:
                try:
                    conn = get_db()
                    # Vérifier si la source existe déjà
                    existing = conn.execute(
                        "SELECT id FROM sources WHERE user_id = ? AND path = ?",
                        (session['user_id'], folder_path)
                    ).fetchone()
                    
                    if not existing:
                        # Créer un nom unique
                        source_name = folder_name
                        counter = 1
                        while conn.execute(
                            "SELECT id FROM sources WHERE user_id = ? AND name = ?",
                            (session['user_id'], source_name)
                        ).fetchone():
                            source_name = f"{folder_name} ({counter})"
                            counter += 1
                        
                        conn.execute(
                            "INSERT INTO sources (user_id, name, type, path, config) VALUES (?, ?, ?, ?, ?)",
                            (session['user_id'], source_name, 'folder', folder_path, '{}')
                        )
                        conn.commit()
                        added_as_source = True
                        invalidate_cache()
                    
                    conn.close()
                except Exception as db_err:
                    app.logger.error(f"Erreur ajout source: {db_err}")
                    # Continuer même si l'ajout échoue
            
            return jsonify({
                "success": True,
                "message": "Dossier créé",
                "path": folder_path.replace('\\', '/'),
                "is_local": True,
                "added_as_source": added_as_source
            }), 200
        
    except Exception as e:
        app.logger.error(f"[create-folder] Erreur: {e}")
        return jsonify({"error": str(e)}), 500
        
@app.route('/api/files/changes', methods=['GET'])
@login_required
def api_check_changes():
    try:
        last_check = float(request.args.get('since', 0))
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                cache_time = cache_data.get('timestamp', 0)
                files = cache_data.get('files', [])
                if not isinstance(files, list):
                    files = []
                return jsonify({
                    'has_changes': cache_time > last_check,
                    'timestamp': cache_time,
                    'count': len(files)
                })
            except json.JSONDecodeError:
                print("[WARN] Cache corrompu dans api_check_changes")
                invalidate_cache()
                return jsonify({'has_changes': True, 'timestamp': 0, 'count': 0})
        return jsonify({'has_changes': True, 'timestamp': 0, 'count': 0})
    except Exception as e:
        print(f"[ERROR] api_check_changes: {e}")
        return jsonify({'has_changes': False, 'timestamp': 0, 'count': 0}), 500

@app.route('/api/files/invalidate-cache', methods=['POST'])
@login_required
def api_invalidate_cache_route():
    invalidate_cache()
    return jsonify({"message": "Cache vidé"}), 200

@app.route('/api/thumb/generate-now', methods=['POST'])
@login_required
def api_generate_thumb_now():
    data = request.json
    file_path = data.get('path')
    if not file_path:
        return jsonify({"error": "Chemin requis"}), 400
    normalized_path = file_path.replace('\\', '/')
    thumb_filename = hashlib.md5(normalized_path.encode()).hexdigest()
    thumb_path = os.path.join(THUMBNAILS_DIR, thumb_filename + '.png')
    if os.path.exists(thumb_path):
        return jsonify({"success": True, "cached": True})
    thumb_generation_queue.put({
        'path': file_path,
        'thumb_path': thumb_path,
        'priority': 'high'
    })
    return jsonify({"success": True, "message": "Génération démarrée"})

@app.route('/api/files/analyze-now', methods=['POST'])
@login_required
def api_analyze_now():
    data = request.json
    file_path = data.get('path')
    if not file_path:
        return jsonify({"error": "Chemin requis"}), 400
    metadata_generation_queue.put({'path': file_path, 'priority': 'high'})
    return jsonify({"success": True, "message": "Analyse démarrée"})

@app.route('/api/scan/delta', methods=['GET'])
@login_required
def scan_delta():
    """Retourne le dernier paquet de 50 fichiers trouvés"""
    with scan_lock:
        batch = scan_state.get('new_batch', [])
        status = scan_state.get('status', 'done')  # Par défaut 'done' au lieu de 'idle'
        found = scan_state.get('found', 0)
        total_scanned = scan_state.get('total_scanned', 0)
        scan_state['new_batch'] = []
        
        # Si rien en cours, retourner done
        if status == 'idle' and found == 0:
            status = 'done'
        
        return jsonify({
            "status": status,
            "found": found,
            "total_scanned": total_scanned,
            "new_files": batch
        })
   
@app.route('/api/files/folder/<source_id>', methods=['GET'])
@login_required
def api_get_folder_files(source_id):
    """Récupère tous les fichiers 3D d'une source/dossier spécifique"""
    try:
        conn = get_db()
        source = conn.execute(
            "SELECT * FROM sources WHERE id = ? AND user_id = ?",
            (source_id, session['user_id'])
        ).fetchone()
        if not source:
            conn.close()
            return jsonify({"error": "Source non trouvée"}), 404
        files = []
        if source['type'] == 'folder' and os.path.exists(source['path']):
            extensions_3d = {'.stl', '.obj', '.3mf'}
            for root, dirs, filenames in os.walk(source['path']):
                for filename in filenames:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in extensions_3d:
                        file_path = os.path.join(root, filename)
                        try:
                            normalized_path = file_path.replace('\\', '/')
                            thumb_filename = hashlib.md5(normalized_path.encode()).hexdigest()
                            thumb_path = os.path.join(THUMBNAILS_DIR, thumb_filename + '.png')
                            files.append({
                                'name': filename,
                                'path': normalized_path,
                                'extension': ext,
                                'size': os.path.getsize(file_path),
                                'source': source['name'],
                                'subdir': os.path.relpath(root, source['path']).replace('\\', '/'),
                                'has_thumb': os.path.exists(thumb_path),
                                'date_added': datetime.datetime.fromtimestamp(
                                    os.path.getmtime(file_path)
                                ).strftime('%Y-%m-%d %H:%M:%S')
                            })
                        except Exception as e:
                            print(f"[WARN] Erreur lecture {filename}: {e}")
                            continue
        elif source['type'] == 'smb':
            unc_path = source['path'].replace('\\\\', '//').replace('\\', '/')
            kwargs = {}
            config = json.loads(source['config']) if source['config'] else {}
            if config.get('username'):
                kwargs['username'] = config['username']
            if config.get('password'):
                kwargs['password'] = config['password']
            extensions_3d = {'.stl', '.obj', '.3mf'}
            def scan_smb_files(base_path, current_subdir=''):
                current_path = f"{base_path}/{current_subdir}" if current_subdir else base_path
                folder_files = []
                try:
                    if not smbclient.path.exists(current_path, **kwargs):
                        return folder_files
                    entries = smbclient.listdir(current_path, **kwargs)
                    for entry in entries:
                        if entry.startswith('.') or entry.startswith('$'):
                            continue
                        entry_path = f"{current_subdir}/{entry}" if current_subdir else entry
                        full_path = f"{base_path}/{entry_path}"
                        try:
                            info = smbclient.stat(full_path, **kwargs)
                            if (info.st_mode & 0o170000) == 0o040000:  # Dossier : récursif
                                folder_files.extend(scan_smb_files(base_path, entry_path))
                            elif entry.lower().endswith(tuple(extensions_3d)):
                                normalized_path = full_path.replace('\\', '/')
                                thumb_filename = hashlib.md5(normalized_path.encode()).hexdigest()
                                thumb_path = os.path.join(THUMBNAILS_DIR, thumb_filename + '.png')
                                folder_files.append({
                                    'name': entry,
                                    'path': normalized_path,
                                    'extension': f".{entry.split('.')[-1]}",
                                    'size': info.st_size,
                                    'source': source['name'],
                                    'subdir': current_subdir,
                                    'has_thumb': os.path.exists(thumb_path),
                                    'date_added': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                })
                        except Exception as e:
                            if "ACCESS_DENIED" not in str(e):
                                print(f"[SMB] Erreur lecture {entry}: {e}")
                            continue
                except Exception as e:
                    print(f"[SMB] Erreur connexion: {e}")
                return folder_files
            files = scan_smb_files(unc_path)
        conn.close()
        if files:
            file_paths = [f['path'] for f in files]
            try:
                placeholders = ','.join('?' * len(file_paths))
                tag_results = conn.execute(
                    f"SELECT ft.file_path, t.name, t.color FROM file_tags ft JOIN tags t ON ft.tag_id = t.id WHERE ft.file_path IN ({placeholders})",
                    file_paths
                ).fetchall() if conn else []
                tags_by_file = {}
                for row in tag_results:
                    tags_by_file.setdefault(row['file_path'], []).append({
                        'name': row['name'],
                        'color': row['color']
                    })
                for f in files:
                    f['tags'] = tags_by_file.get(f['path'], [])
            except:
                pass
        return jsonify({
            "source": {
                "id": source['id'],
                "name": source['name'],
                "type": source['type'],
                "path": source['path']
            },
            "files": files,
            "count": len(files)
        })
    except Exception as e:
        print(f"[ERROR] api_get_folder_files: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/slicer/send-batch', methods=['POST'])
@login_required
def api_send_batch_to_slicer():
    """Envoie plusieurs fichiers au slicer en une seule requête"""
    try:
        data = request.json
        file_paths = data.get('files', [])
        slicer_path = data.get('slicer_path')
        if not file_paths:
            return jsonify({"error": "Aucun fichier sélectionné"}), 400
        results = {
            'success': [],
            'failed': [],
            'total': len(file_paths)
        }
        for file_path in file_paths:
            try:
                if not os.path.exists(file_path):
                    results['failed'].append({
                        'path': file_path,
                        'error': 'Fichier non trouvé'
                    })
                    continue
                if sys.platform == 'win32':
                    if slicer_path and os.path.exists(slicer_path):
                        subprocess.Popen([slicer_path, file_path],
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
                    else:
                        os.startfile(file_path)
                else:
                    subprocess.Popen(['xdg-open' if sys.platform != 'darwin' else 'open', file_path],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                results['success'].append({
                    'path': file_path,
                    'name': os.path.basename(file_path)
                })
                time.sleep(0.1)
            except Exception as e:
                results['failed'].append({
                    'path': file_path,
                    'error': str(e)
                })
        print(f"[SLICER BATCH] {len(results['success'])}/{results['total']} fichiers envoyés")
        return jsonify({
            "message": f"{len(results['success'])}/{results['total']} fichiers envoyés au slicer",
            "results": results
        }), 200
    except Exception as e:
        print(f"[ERROR] api_send_batch_to_slicer: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/slicer/batch-preview', methods=['POST'])
@login_required
def api_batch_preview():
    """Prévisualisation d'un envoi en masse (sans ouvrir)"""
    try:
        data = request.json
        file_paths = data.get('files', [])
        if not file_paths:
            return jsonify({"error": "Aucun fichier sélectionné"}), 400
        preview = []
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    preview.append({
                        'name': os.path.basename(file_path),
                        'path': file_path,
                        'size': os.path.getsize(file_path),
                        'extension': os.path.splitext(file_path)[1].lower(),
                        'valid': True
                    })
                else:
                    preview.append({
                        'name': os.path.basename(file_path),
                        'path': file_path,
                        'valid': False,
                        'error': 'Fichier non trouvé'
                    })
            except Exception as e:
                preview.append({
                    'name': os.path.basename(file_path),
                    'path': file_path,
                    'valid': False,
                    'error': str(e)
                })
        return jsonify({
            "count": len(preview),
            "valid_count": sum(1 for f in preview if f.get('valid')),
            "files": preview
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def find_slicer_by_name(slicer_name):
    """Tente de trouver le chemin d'un slicer connu sous Windows"""
    if not slicer_name or slicer_name == 'system_default':
        return None
    known_slicers = {
        'orca-slicer.exe': [r"C:\Program Files\OrcaSlicer\orca-slicer.exe"],
        'bambu-studio.exe': [r"C:\Program Files\Bambu Studio\bambu-studio.exe"],
        'prusa-slicer.exe': [r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer.exe"],
        'Cura.exe': [r"C:\Program Files\Ultimaker Cura 5.7\Cura.exe", r"C:\Program Files\Ultimaker Cura 5.6\Cura.exe", r"C:\Program Files\Ultimaker Cura 5.5\Cura.exe"]
    }
    paths_to_check = known_slicers.get(slicer_name, [])
    for path in paths_to_check:
        if os.path.exists(path):
            return path
    return None

@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    try:
        settings = load_settings() or {}
        # ✅ Valeurs par défaut si absentes
        settings.setdefault('default_slicer', 'system_default')
        settings.setdefault('lang', 'fr')
        return jsonify(settings), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/settings', methods=['POST'])
def api_save_settings():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Données JSON requises"}), 400

        # ✅ Fusionner avec l'existant pour ne pas écraser theme, fabricant, etc.
        current_settings = load_settings() or {}
        current_settings.update(data)

        save_settings(current_settings)
        return jsonify({"message": "Paramètres sauvegardés", "settings": current_settings}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/slicer/send', methods=['POST'])
@login_required
def api_send_to_slicer():
    data = request.json
    file_path = data.get('file_path', '')
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "Fichier non trouvé"}), 404
    try:
        settings = load_settings()
        slicer_name = settings.get('default_slicer', 'system_default')
        slicer_path = find_slicer_by_name(slicer_name)
        if slicer_path:
            subprocess.Popen([slicer_path, file_path])
            return jsonify({"message": f"Envoyé via {os.path.basename(slicer_path)}"}), 200
        else:
            if sys.platform == 'win32':
                os.startfile(file_path)
            else:
                subprocess.run(['xdg-open', file_path], check=False)
            return jsonify({"message": "Envoyé (Défaut système)"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/picker/folder', methods=['POST'])
@login_required
def api_pick_folder():
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        root.update()
        folder = filedialog.askdirectory(title="Sélectionner un dossier", initialdir=os.path.expanduser("~"))
        root.destroy()
        if folder:
            return jsonify({"path": folder.replace("\\", "/")})
        else:
            return jsonify({"error": "Annulé"}), 400
    except ImportError as e:
        return jsonify({"error": "tkinter manquant"}), 500
    except Exception as e:
        return jsonify({"error": f"Erreur: {str(e)}"}), 500

@app.route('/api/picker/file', methods=['POST'])
@login_required
def api_pick_file():
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        root.update()
        files = filedialog.askopenfilenames(
            title="Sélectionner des fichiers 3D",
            initialdir=os.path.expanduser("~"),
            filetypes=[("Fichiers 3D", "*.stl *.3mf *.obj"), ("STL", "*.stl"), ("3MF", "*.3mf"), ("OBJ", "*.obj"), ("Tous", "*.*")]
        )
        root.destroy()
        if files:
            return jsonify({"paths": [f.replace("\\", "/") for f in files]})
        else:
            return jsonify({"error": "Annulé"}), 400
    except ImportError as e:
        return jsonify({"error": "tkinter manquant"}), 500
    except Exception as e:
        return jsonify({"error": f"Erreur: {str(e)}"}), 500

@app.route('/api/slicer/send-batch', methods=['POST'])
@login_required
def api_slicer_send_batch():
    """
    Envoie plusieurs fichiers au slicer en UNE SEULE instance.
    Compatible OrcaSlicer, BambuStudio, PrusaSlicer, Cura.
    """
    try:
        data = request.json
        file_paths = data.get('files', [])
        if not file_paths:
            return jsonify({"error": "Aucun fichier sélectionné"}), 400
        if sys.platform == 'win32':
            file_paths = [p.replace('/', '\\') for p in file_paths]
        slicer_path = None
        standard_paths = [
            r"C:\Program Files\OrcaSlicer\orca-slicer.exe",
            r"C:\Program Files (x86)\OrcaSlicer\orca-slicer.exe",
            r"C:\Program Files\Bambu Studio\bambu-studio.exe",
            r"C:\Program Files (x86)\Bambu Studio\bambu-studio.exe",
            r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer.exe",
            r"C:\Program Files (x86)\Prusa3D\PrusaSlicer\prusa-slicer.exe",
        ]
        for path in standard_paths:
            if os.path.exists(path):
                slicer_path = path
                print(f"[Slicer] Détecté: {path}")
                break
        if not slicer_path and sys.platform == 'win32':
            import glob
            cura_paths = glob.glob(r"C:\Program Files\Ultimaker Cura*\Cura.exe")
            cura_paths_x86 = glob.glob(r"C:\Program Files (x86)\Ultimaker Cura*\Cura.exe")
            all_cura = cura_paths + cura_paths_x86
            if all_cura:
                slicer_path = all_cura[0]
                print(f"[Slicer] Détecté (Cura): {slicer_path}")
        if not slicer_path:
            return jsonify({
                "error": "Aucun slicer trouvé. Installez OrcaSlicer, BambuStudio, PrusaSlicer ou Cura."
            }), 404
        print(f"[Slicer] Lancement avec {len(file_paths)} fichiers...")
        try:
            subprocess.Popen([slicer_path] + file_paths)
        except Exception as e:
            print(f"[Slicer] Erreur ouverture multiple: {e}")
            subprocess.Popen([slicer_path, file_paths[0]])
        return jsonify({
            "message": f"{len(file_paths)} fichiers ouverts dans le slicer",
            "count": len(file_paths)
        }), 200
    except Exception as e:
        print(f"[ERROR] api_slicer_send_batch: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-connection', methods=['POST'])
@login_required
def api_test_connection():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalide"}), 400
        conn_type = data.get('type', '')
        host = data.get('host', '').strip()
        if not host:
            return jsonify({"error": "Hôte requis"}), 400
        if conn_type in ['smb', 'nfs']:
            return jsonify({"success": True, "message": "OK"}), 200
        return jsonify({"error": "Non supporté"}), 400
    except:
        return jsonify({"error": "Erreur"}), 500

def update_cache_thumb_status(file_path, has_thumb):
    """Met à jour le statut de miniature dans le cache JSON"""
    try:
        if not os.path.exists(CACHE_FILE):
            return
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        if 'files' in cache and isinstance(cache['files'], list):
            for f in cache['files']:
                if f.get('path') == file_path:
                    f['has_thumb'] = has_thumb
                    break
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[CACHE] Erreur mise à jour thumb status: {e}")
        
def pregenerate_thumbnails_on_startup(limit=30):
    """Pré-génère les miniatures manquantes au démarrage (limité pour ne pas bloquer)"""
    print("[THUMBS] 🔄 Pré-génération des miniatures au démarrage...")
    conn = get_db()
    sources = conn.execute("SELECT * FROM sources").fetchall()
    conn.close()
    
    generated = 0
    processed = 0
    
    for source in sources:
        if processed >= limit:
            break
        try:
            if source['type'] == 'folder' and os.path.exists(source['path']):
                for root, dirs, files in os.walk(source['path']):
                    for f in files:
                        if processed >= limit:
                            break
                        if f.lower().endswith(('.stl', '.obj', '.3mf')):
                            file_path = os.path.join(root, f).replace('\\', '/')
                            normalized_path = file_path
                            thumb_filename = hashlib.md5(normalized_path.encode()).hexdigest()
                            thumb_path = os.path.join(THUMBNAILS_DIR, thumb_filename + '.png')
                            
                            if not os.path.exists(thumb_path) and file_path not in ignored_files_cache:
                                print(f"[THUMBS] Génération: {os.path.basename(file_path)}")
                                if generate_thumbnail_pyrender(file_path, thumb_path):
                                    generated += 1
                                    update_cache_thumb_status(file_path, True)  # ✅ Cache mis à jour !
                                else:
                                    create_fallback_thumbnail(thumb_path)
                                    update_cache_thumb_status(file_path, True)
                            processed += 1
        except Exception as e:
            print(f"[THUMBS] Erreur source {source['name']}: {e}")
    
    print(f"[THUMBS] ✅ {generated}/{processed} miniatures pré-générées")
    


@app.route('/api/file/data', methods=['GET'])
@login_required
def api_get_file_data():
    file_path = request.args.get('path')
    if not file_path:
        return jsonify({"error": "Chemin requis"}), 400
    try:
        file_path = unquote(file_path)
    except:
        pass
    if not os.path.exists(file_path):
        print(f"[WARN] Fichier non trouvé: {file_path}")
        return jsonify({"error": "Fichier non trouvé"}), 404
    if not os.access(file_path, os.R_OK):
        print(f"[WARN] Permission refusée: {file_path}")
        return jsonify({"error": "Permission refusée"}), 403
    try:
        return send_file(file_path)
    except Exception as e:
        print(f"[ERROR] Erreur envoi fichier: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/favorites', methods=['GET'])
@login_required
def api_get_favorites():
    """Récupère la liste des favoris"""
    try:
        conn = get_db()
        favorites = conn.execute(
            "SELECT file_path FROM favorites WHERE user_id = ?",
            (session['user_id'],)
        ).fetchall()
        conn.close()
        favorite_paths = [f['file_path'] for f in favorites]
        return jsonify(favorite_paths)
    except Exception as e:
        print(f"[ERROR] api_get_favorites: {e}")
        return jsonify([]), 500

@app.route('/api/favorites', methods=['POST'])
@login_required
def api_toggle_favorite():
    """Ajoute ou retire un fichier des favoris"""
    try:
        data = request.json
        file_path = data.get('path')
        if not file_path:
            return jsonify({"error": "Chemin requis"}), 400
        conn = get_db()
        existing = conn.execute(
            "SELECT file_path FROM favorites WHERE user_id = ? AND file_path = ?",
            (session['user_id'], file_path)
        ).fetchone()
        if existing:
            conn.execute(
                "DELETE FROM favorites WHERE user_id = ? AND file_path = ?",
                (session['user_id'], file_path)
            )
            conn.commit()
            conn.close()
            return jsonify({"favorited": False, "message": "Retiré des favoris"})
        else:
            conn.execute(
                "INSERT INTO favorites (user_id, file_path) VALUES (?, ?)",
                (session['user_id'], file_path)
            )
            conn.commit()
            conn.close()
            return jsonify({"favorited": True, "message": "Ajouté aux favoris"})
    except Exception as e:
        print(f"[ERROR] api_toggle_favorite: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/contact/send', methods=['POST'])
@login_required
def api_send_contact():
    """Envoie le message via Formspree (proxy)"""
    data = request.json
    
    FORMSPREE_URL = 'https://formspree.io/f/mdavogan'
    
    try:
        res = requests.post(
            FORMSPREE_URL,
            json={
                'name': data.get('name', ''),
                'email': data.get('email', ''),
                'message': data.get('message', ''),
                'subject': data.get('subject', ''),
                '_subject': f"[Stellio] {data.get('subject', 'Contact')}",
                '_template': 'table'
            },
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        
        if res.ok:
            return jsonify({"message": "Envoyé"}), 200
        else:
            error_msg = res.json().get('error', 'Erreur Formspree')
            print(f"[Contact] Erreur Formspree: {error_msg}")
            return jsonify({"error": error_msg}), 500
            
    except requests.exceptions.RequestException as e:
        print(f"[Contact] Erreur connexion Formspree: {e}")
        return jsonify({"error": f"Erreur de connexion: {str(e)}"}), 500
    except Exception as e:
        print(f"[Contact] Erreur générale: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/accounts/status', methods=['GET'])
@login_required
def api_accounts_status():
    """Retourne l'état de connexion de tous les comptes externes au démarrage"""
    status = {
        'thingiverse': False,
        'cults': False,
        'telegram': False
    }

    conn = get_db()
    accounts = conn.execute(
        "SELECT platform, api_key, last_login FROM account_credentials WHERE user_id = ?",
        (session['user_id'],)
    ).fetchall()
    conn.close()

    for acc in accounts:
        platform = acc['platform']
        if platform == 'thingiverse' and acc['api_key']:
            status['thingiverse'] = True
        elif platform == 'cults' and acc['api_key']:
            status['cults'] = True
        elif platform == 'telegram' and acc['last_login']:
            status['telegram'] = True

    return jsonify(status)

# ============================================
# 🔧 RÉPARATION DE MAILLAGE (MESH REPAIR)
# ============================================
@app.route('/api/files/repair', methods=['POST'])
@login_required
def api_repair_file():
    """Analyse et répare un fichier 3D non-manifold"""
    data = request.json
    file_path = data.get('path')
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "Fichier non trouvé"}), 404

    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.3mf':
            mesh = load_3mf_mesh(file_path)
        elif ext == '.obj':
            mesh = trimesh.load(file_path, force='mesh', process=False)
        else:
            mesh = trimesh.load(file_path, force='mesh')

        if isinstance(mesh, trimesh.Scene):
            geoms = [m for m in mesh.geometry.values() if hasattr(m, 'vertices') and len(m.vertices) > 0]
            if not geoms: return jsonify({"error": "Maillage vide"}), 400
            mesh = trimesh.util.concatenate(geoms)

        if mesh.is_watertight:
            return jsonify({"success": True, "message": "Déjà valide (watertight)"})

        # ✅ Sauvegarde de sécurité
        backup_path = file_path + ".bak"
        if not os.path.exists(backup_path):
            shutil.copy2(file_path, backup_path)

        # ✅ Application des réparations
        trimesh.repair.fix_winding(mesh)
        trimesh.repair.fix_normals(mesh)
        trimesh.repair.fill_holes(mesh)
        trimesh.repair.fix_normals(mesh)  # Re-check après remplissage

        # ✅ Export
        if ext in ['.stl', '.obj']:
            mesh.export(file_path, file_type=ext[1:])
        else:
            # Fallback pour formats complexes (3MF, etc.)
            out_path = os.path.splitext(file_path)[0] + "_repaired.stl"
            mesh.export(out_path, file_type='stl')
            return jsonify({"success": True, "message": "Exporté en STL réparé (format original non supporté)", "new_path": out_path})

        invalidate_cache()
        return jsonify({"success": True, "message": "Réparé avec succès"})
    except Exception as e:
        app.logger.error(f"[Repair] Erreur: {e}")
        return jsonify({"error": f"Échec: {str(e)}"}), 500

# =============================================================================
# 🔄 SYSTÈME DE MISE À JOUR AUTOMATIQUE
# =============================================================================
import tempfile
from packaging import version

GITHUB_REPO = "stellio-app/stellio-app"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
CURRENT_VERSION = "0.0.1"  # ⚠️ METTEZ À JOUR à chaque release

def get_current_version():
    """Retourne la version actuelle de l'application"""
    return CURRENT_VERSION

def check_for_updates():
    """Vérifie si une nouvelle version est disponible sur GitHub"""
    try:
        print("[UPDATE] 🔍 Vérification des mises à jour...")
        
        response = requests.get(GITHUB_API_URL, timeout=10, headers={
            'User-Agent': f'Stellio-App/{CURRENT_VERSION}'
        })
        
        if response.status_code != 200:
            print(f"[UPDATE] ⚠️ Impossible de vérifier (HTTP {response.status_code})")
            return None
        
        release_data = response.json()
        latest_version = release_data.get('tag_name', '').replace('v', '')
        current_version = get_current_version()
        
        print(f"[UPDATE] Version actuelle: {current_version}")
        print(f"[UPDATE] Dernière version GitHub: {latest_version}")
        
        # Comparer les versions
        if version.parse(latest_version) > version.parse(current_version):
            print(f"[UPDATE] ✅ Nouvelle version disponible: {latest_version}")
            
            # Extraire l'URL de téléchargement de l'installateur Windows
            download_url = None
            for asset in release_data.get('assets', []):
                if asset['name'].endswith('.exe'):
                    download_url = asset['browser_download_url']
                    break
            
            if not download_url:
                print("[UPDATE] ⚠️ Aucun installateur .exe trouvé")
                return None
            
            return {
                'version': latest_version,
                'current_version': current_version,
                'download_url': download_url,
                'release_notes': release_data.get('body', 'Corrections de bugs et améliorations.'),
                'published_at': release_data.get('published_at', ''),
                'release_url': release_data.get('html_url', '')
            }
        else:
            print("[UPDATE] ✅ Application à jour")
            return None
            
    except Exception as e:
        print(f"[UPDATE] ❌ Erreur: {e}")
        return None

def download_update(download_url, progress_callback=None):
    """Télécharge la mise à jour avec suivi de progression"""
    try:
        print(f"[UPDATE] ⬇️ Téléchargement depuis: {download_url}")
        
        # Créer un fichier temporaire
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f"Stellio-Update-{int(time.time())}.exe")
        
        # Télécharger avec progression
        response = requests.get(download_url, stream=True, timeout=60, headers={
            'User-Agent': f'Stellio-App/{CURRENT_VERSION}'
        })
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(temp_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        progress = (downloaded / total_size) * 100
                        progress_callback(progress, downloaded, total_size)
        
        print(f"[UPDATE] ✅ Téléchargement terminé: {temp_file}")
        return temp_file
        
    except Exception as e:
        print(f"[UPDATE] ❌ Erreur téléchargement: {e}")
        return None

def install_update(installer_path):
    """Lance l'installateur de mise à jour en mode silencieux"""
    try:
        print(f"[UPDATE] 🚀 Lancement de l'installateur: {installer_path}")
        ext = os.path.splitext(installer_path)[1].lower()
        
        if sys.platform == 'win32':
            if ext == '.exe':
                # Inno Setup / NSIS
                subprocess.Popen(
                    [installer_path, '/VERYSILENT', '/NORESTART'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            elif ext == '.msi':
                # MSI Windows
                subprocess.Popen(
                    ['msiexec', '/i', installer_path, '/qn', '/norestart'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            elif ext == '.zip':
                # Décompresser et lancer l'exe contenu
                import zipfile
                extract_dir = os.path.join(tempfile.gettempdir(), 'stellio-update')
                os.makedirs(extract_dir, exist_ok=True)
                with zipfile.ZipFile(installer_path, 'r') as z:
                    z.extractall(extract_dir)
                # Chercher un .exe dans le dossier extrait
                for f in os.listdir(extract_dir):
                    if f.endswith('.exe'):
                        subprocess.Popen(
                            [os.path.join(extract_dir, f)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        break
            else:
                # Fallback : ouvrir normalement
                subprocess.Popen([installer_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL)
        
        print("[UPDATE] ✅ Installateur lancé, fermeture de l'application...")
        time.sleep(2)
        os._exit(0)
    except Exception as e:
        print(f"[UPDATE] ❌ Erreur installation: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/api/printers/<int:pid>/camera', methods=['GET'])
@login_required
def api_printer_camera(pid):
    """Récupère les informations de la caméra de l'imprimante"""
    conn = get_db()
    p = conn.execute(
        "SELECT * FROM printers WHERE id = ? AND user_id = ?",
        (pid, session['user_id'])
    ).fetchone()
    conn.close()
    
    if not p:
        return jsonify({"available": False}), 404
    
    printer = parse_printer_config(p)
    ptype = printer['type']
    ip = printer['ip']
    
    camera_info = {"available": False, "stream_url": None, "snapshot_url": None, "name": "Camera"}
    
    try:
        if ptype == 'klipper':
            port = printer.get('config', {}).get('port', '7125')
            try:
                r = requests.get(f"http://{ip}:{port}/server/webcams/list", timeout=3)
                if r.status_code == 200:
                    webcams = r.json().get('result', {}).get('webcams', [])
                    if webcams:
                        cam = webcams[0]
                        stream_url = cam.get('stream_url', '')
                        snapshot_url = cam.get('snapshot_url', '')
                        
                        if stream_url and stream_url.startswith('/'):
                            webcam_ports = [80, 4408, 8080, 8181]
                            for wport in webcam_ports:
                                test_url = f"http://{ip}:{wport}{stream_url}"
                                try:
                                    test_r = requests.get(test_url, timeout=2, stream=True)
                                    if test_r.status_code == 200:
                                        stream_url = test_url
                                        break
                                except:
                                    continue
                            else:
                                stream_url = f"http://{ip}:80{stream_url}"
                        
                        if snapshot_url and snapshot_url.startswith('/'):
                            snapshot_url = f"http://{ip}:80{snapshot_url}"
                        
                        camera_info.update({
                            "available": True,
                            "stream_url": stream_url,
                            "snapshot_url": snapshot_url,
                            "name": cam.get('name', 'Klipper Camera')
                        })
                        # ✅ Logs supprimés pour éviter le spam
            except Exception as e:
                pass  # Silencieux
                
        elif ptype == 'octoprint':
            headers = {'X-Api-Key': printer.get('api_key', '')}
            try:
                r = requests.get(f"http://{ip}/api/settings", headers=headers, timeout=3)
                if r.status_code == 200:
                    settings = r.json()
                    webcam = settings.get('webcam', {})
                    if webcam.get('streamUrl'):
                        stream_url = webcam.get('streamUrl')
                        if stream_url.startswith('/'):
                            stream_url = f"http://{ip}{stream_url}"
                        camera_info.update({
                            "available": True,
                            "stream_url": stream_url,
                            "snapshot_url": webcam.get('snapshotUrl', ''),
                            "name": "OctoPrint Camera"
                        })
            except Exception as e:
                pass
                
    except Exception as e:
        pass
    
    return jsonify(camera_info)
    
# =============================================================================
# 🌐 API ENDPOINTS POUR LE FRONTEND (MISE À JOUR)
# =============================================================================

@app.route('/api/update/check', methods=['GET'])
@login_required
def api_check_update():
    """Vérifie si une mise à jour est disponible"""
    update_info = check_for_updates()
    if update_info:
        return jsonify({
            'update_available': True,
            'version': update_info['version'],
            'current_version': update_info['current_version'],
            'release_notes': update_info['release_notes'],
            'download_url': update_info['download_url'],
            'published_at': update_info['published_at'],
            'release_url': update_info['release_url']
        }), 200
    else:
        return jsonify({
            'update_available': False,
            'current_version': get_current_version()
        }), 200

@app.route('/api/update/version', methods=['GET'])
def api_get_version():
    """Retourne la version actuelle (pas besoin d'être connecté)"""
    return jsonify({
        'version': get_current_version(),
        'app_name': 'Stellio'
    }), 200

@app.route('/api/update/download', methods=['POST'])
@login_required
def api_download_update():
    """Télécharge la mise à jour"""
    data = request.json
    download_url = data.get('download_url')
    
    if not download_url:
        return jsonify({'error': 'URL manquante'}), 400
    
    installer_path = download_update(download_url)
    if installer_path:
        return jsonify({
            'success': True,
            'installer_path': installer_path
        }), 200
    else:
        return jsonify({'error': 'Échec du téléchargement'}), 500

@app.route('/api/update/install', methods=['POST'])
@login_required
def api_install_update():
    """Lance l'installation de la mise à jour"""
    data = request.json
    installer_path = data.get('installer_path')
    
    if not installer_path or not os.path.exists(installer_path):
        return jsonify({'error': 'Installateur introuvable'}), 404
    
    # Lancer dans un thread pour ne pas bloquer la réponse
    def do_install():
        time.sleep(1)  # Laisser le temps à la réponse HTTP de partir
        install_update(installer_path)
    
    threading.Thread(target=do_install, daemon=True).start()
    
    return jsonify({'success': True, 'message': 'Installation en cours'}), 200

@app.route('/api/update/changelog', methods=['GET'])
@login_required
def api_get_changelog():
    """Récupère le changelog de la dernière version"""
    try:
        response = requests.get(GITHUB_API_URL, timeout=10, headers={
            'User-Agent': f'Stellio-App/{CURRENT_VERSION}'
        })
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'version': data.get('tag_name', ''),
                'changelog': data.get('body', ''),
                'published_at': data.get('published_at', ''),
                'url': data.get('html_url', '')
            }), 200
        return jsonify({'error': 'Impossible de récupérer le changelog'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============================================================================
# 🖨️ API IMPRIMANTES
# =============================================================================
@app.route('/api/printers', methods=['GET'])
@login_required
def api_get_printers():
    conn = get_db()
    printers = conn.execute(
        "SELECT * FROM printers WHERE user_id = ?", (session['user_id'],)
    ).fetchall()
    conn.close()
    return jsonify([parse_printer_config(p) for p in printers])

@app.route('/api/printers', methods=['POST'])
@login_required
def api_add_printer():
    data = request.json
    name = data.get('name')
    ptype = data.get('type')  # octoprint, klipper, bambu
    ip = data.get('ip')
    api_key = data.get('api_key')
    config = json.dumps(data.get('config', {}))
    
    # ❌ SUPPRIMEZ CETTE LIGNE : conn.execute("INSERT INTO printers ... config ...", (..., config, ...))
    
    if not name or not ip or not ptype:
        return jsonify({"error": "Champs requis"}), 400
    
    conn = get_db()
    try:
        # Test de connexion
        is_connected = printer_hub.connect_printer({
            'id': 0, 'type': ptype, 'ip': ip, 'api_key': api_key,
            'config': json.loads(config) if config else {}
        })
        
        conn.execute("""
        INSERT INTO printers (user_id, name, type, ip, api_key, config, is_connected)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session['user_id'], name, ptype, ip, api_key, config, is_connected))
        
        conn.commit()
        return jsonify({"message": "Imprimante ajoutée", "connected": is_connected}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/printers/<int:pid>/status', methods=['GET'])
@login_required
def api_printer_status(pid):
    conn = get_db()
    p = conn.execute(
        "SELECT * FROM printers WHERE id = ? AND user_id = ?",
        (pid, session['user_id'])
    ).fetchone()
    conn.close()
    if not p:
        return jsonify({"error": "Not found"}), 404
    
    printer = parse_printer_config(p)
    status = printer_hub.get_status(printer)
    
    # Mettre à jour l'état de connexion
    conn = get_db()
    is_online = status.get('status') not in ['error', 'offline', 'timeout']
    conn.execute("UPDATE printers SET is_connected = ? WHERE id = ?",
                 (is_online, pid))
    conn.commit()
    conn.close()
    return jsonify(status)

@app.route('/api/printers/<int:pid>/upload', methods=['POST'])
@login_required
def api_printer_upload(pid):
    data = request.json
    file_path = data.get('file_path')
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "Fichier non trouvé"}), 404
    
    conn = get_db()
    p = conn.execute(
        "SELECT * FROM printers WHERE id = ? AND user_id = ?",
        (pid, session['user_id'])
    ).fetchone()
    conn.close()
    if not p:
        return jsonify({"error": "Not found"}), 404
    
    printer = parse_printer_config(p)
    success = printer_hub.upload_file(printer, file_path)
    return jsonify({
        "success": success,
        "message": "Fichier envoyé" if success else "Échec de l'envoi"
    })

@app.route('/api/printers/<int:pid>', methods=['DELETE'])
@login_required
def api_delete_printer(pid):
    conn = get_db()
    try:
        conn.execute("DELETE FROM printers WHERE id = ? AND user_id = ?", 
                     (pid, session['user_id']))
        conn.commit()
        return jsonify({"message": "Imprimante supprimée"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()     
 # ============================================
# 🚪 FERMETURE DE L'APPLICATION
# ============================================
_app_window = None  # Référence à la fenêtre PyWebView

@app.route('/api/app/quit', methods=['POST'])
@login_required
def api_quit_app():
    """Ferme l'application proprement après sauvegarde du cache"""
    def do_quit():
        time.sleep(0.5)  # Laisser le temps à la réponse HTTP de partir
        save_cache_on_exit()
        print("[APP] 🛑 Fermeture demandée par l'utilisateur")
        os._exit(0)
    
    threading.Thread(target=do_quit, daemon=True).start()
    return jsonify({"success": True, "message": "Fermeture en cours"}), 200

@app.route('/api/app/save-cache', methods=['POST'])
@login_required
def api_save_cache():
    """Sauvegarde forcée du cache (appelée avant fermeture depuis le JS)"""
    try:
        save_cache_on_exit()
        return jsonify({"success": True, "message": "Cache sauvegardé"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
if __name__ == '__main__':
    import sys, os, threading, time, urllib.request, json
    import tkinter as tk
    from tkinter import ttk

    # ✅ Correction UTF-8 sûre (Python 3.7+)
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass

    SERVER_URL = 'http://127.0.0.1:5000'
    print("[*] Démarrage Stellio...")

    # ══════════ 🌍 CHARGEMENT DES TRADUCTIONS (AVANT LE SPLASH) ══════════
    def load_splash_translations():
        """Charge les traductions pour le splash screen depuis les fichiers JSON"""
        lang = 'fr'
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    lang = settings.get('lang', 'fr')
        except:
            pass
        
        translations = {}
        lang_file = os.path.join(BASE_DIR, 'languages', f'{lang}.json')
        fallback_file = os.path.join(BASE_DIR, 'languages', 'fr.json')
        
        for file_path in [lang_file, fallback_file]:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        translations.update(json.load(f))
                    if file_path == lang_file:
                        break
                except:
                    pass
        
        return {
            'init': translations.get('splash.init', 'Initialisation du moteur 3D...'),
            'database': translations.get('splash.database', 'Chargement de la base de données...'),
            'server': translations.get('splash.server', 'Démarrage du serveur web...'),
            'thumbnails': translations.get('splash.thumbnails', 'Préparation des miniatures 3D...'),
            'version': translations.get('splash.version', 'Version {version}')
        }
    
    SPLASH_TEXTS = load_splash_translations()

    # ══════════ 🎨 1. CRÉATION DU SPLASH SCREEN ══════════
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes('-topmost', True)
    root.configure(bg='#1a1d23')

    width, height = 650, 500
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = (screen_w - width) // 2
    y = (screen_h - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")

    logo_path = os.path.join(BASE_DIR, 'assets', 'logo-nom-stellio.png')
    if os.path.exists(logo_path):
        try:
            from PIL import Image, ImageTk
            img = Image.open(logo_path)
            photo = ImageTk.PhotoImage(img)
            lbl_logo = tk.Label(root, image=photo, bg='#1a1d23')
            lbl_logo.image = photo
            lbl_logo.pack(pady=(40, 10))
        except Exception as e:
            print(f"[Splash] Erreur chargement logo: {e}")

    tk.Label(root, text=SPLASH_TEXTS['version'].format(version=CURRENT_VERSION), 
             font=("Segoe UI", 10), fg="#9ca3af", bg='#1a1d23').pack(pady=(5, 20))

    lbl_status = tk.Label(root, text=SPLASH_TEXTS['init'], 
                          font=("Segoe UI", 11), fg="#e6e6e6", bg='#1a1d23')
    lbl_status.pack(pady=10)

    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Custom.Horizontal.TProgressbar", 
                    troughcolor='#2a2f3a',
                    background='#4ea1d3',
                    thickness=8)
    progress = ttk.Progressbar(root, style="Custom.Horizontal.TProgressbar", 
                               mode='indeterminate', length=400)
    progress.pack(pady=15)
    progress.start(20)

    # ══════════ 🖼️ 2. FONCTIONS DE PRÉ-GÉNÉRATION ══════════
    def pregenerate_thumbnails_on_startup(limit=30):
        """Pré-génère les miniatures manquantes au démarrage"""
        print("[THUMBS] 🔄 Pré-génération des miniatures au démarrage...")
        conn = get_db()
        sources = conn.execute("SELECT * FROM sources").fetchall()
        conn.close()
        
        generated = 0
        processed = 0
        
        for source in sources:
            if processed >= limit: break
            try:
                if source['type'] == 'folder' and os.path.exists(source['path']):
                    for root_dir, dirs, files in os.walk(source['path']): 
                        for f in files:
                            if processed >= limit: break
                            if f.lower().endswith(('.stl', '.obj', '.3mf')):
                                file_path = os.path.join(root_dir, f).replace('\\', '/')
                                if file_path in ignored_files_cache: continue
                                
                                thumb_filename = hashlib.md5(file_path.encode()).hexdigest()
                                thumb_path = os.path.join(THUMBNAILS_DIR, thumb_filename + '.png')
                                
                                if not os.path.exists(thumb_path):
                                    print(f"[THUMBS] Génération: {os.path.basename(file_path)}")
                                    if generate_thumbnail_pyrender(file_path, thumb_path):
                                        generated += 1
                                        update_cache_thumb_status(file_path, True)
                                    else:
                                        create_fallback_thumbnail(thumb_path)
                                        update_cache_thumb_status(file_path, True)
                                processed += 1
                        break 
            except Exception as e:
                print(f"[THUMBS] Erreur source {source['name']}: {e}")
        print(f"[THUMBS] ✅ {generated}/{processed} miniatures pré-générées")

    def update_cache_thumb_status(file_path, has_thumb):
        """Met à jour le statut has_thumb dans le cache JSON"""
        try:
            if not os.path.exists(CACHE_FILE): return
            with open(CACHE_FILE, 'r', encoding='utf-8') as f: cache = json.load(f)
            if 'files' in cache and isinstance(cache['files'], list):
                for f in cache['files']:
                    if f.get('path') == file_path:
                        f['has_thumb'] = has_thumb
                        break
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[CACHE] Erreur mise à jour thumb status: {e}")

    # ══════════ ⚙️ 3. TÂCHES LOURDES EN ARRIÈRE-PLAN ══════════
    def heavy_backend_startup():
        """S'exécute en thread pendant que l'utilisateur regarde le Splash Screen"""
        try:
            root.after(0, lambda: lbl_status.config(text=SPLASH_TEXTS['database']))
            start_telegram_loop()
            process_generation_queue()
            
            if os.path.exists(CACHE_FILE):
                try:
                    with open(CACHE_FILE, 'r', encoding='utf-8') as f: json.load(f)
                except Exception: invalidate_cache()
            
            root.after(0, lambda: lbl_status.config(text=SPLASH_TEXTS['server']))
            def run_server():
                try:
                    from waitress import serve
                    # ✅ 16 threads au lieu de 4 pour réduire les warnings de queue depth
                    serve(app, host='127.0.0.1', port=5000, threads=16, channel_timeout=300)
                except ImportError:
                    app.run(host='127.0.0.1', port=5000, debug=False)
            threading.Thread(target=run_server, daemon=True).start()
            
            server_ready = False
            for _ in range(30):
                try:
                    urllib.request.urlopen(SERVER_URL, timeout=1)
                    server_ready = True
                    break
                except Exception:
                    time.sleep(0.5)
                    
            if server_ready:
                root.after(0, lambda: lbl_status.config(text=SPLASH_TEXTS['thumbnails']))
                pregenerate_thumbnails_on_startup(limit=30) 
                
                # ✅ Délai réduit à 1.5s si tout est prêt
                root.after(1500, root.destroy)
            else:
                root.after(5000, root.destroy)
            
        except Exception as e:
            print(f"[Splash Error] Le démarrage a rencontré un problème: {e}")
            import traceback; traceback.print_exc()
            root.after(10000, root.destroy)

    # ══════════ 🎬 4. DÉMARRAGE ══════════
    threading.Thread(target=heavy_backend_startup, daemon=True).start()
    root.mainloop()

    # ══════════ 🖥️ 5. LANCEMENT DE L'INTERFACE PRINCIPALE (PYWEBVIEW) ══════════
    print("[OK] Splash fermé, lancement de l'interface principale...")
    try:
        import webview
        
        # ✅ Confirmation native simple (fonctionne à 100%)
        window = webview.create_window(
            'Stellio',
            SERVER_URL,
            width=1280,
            height=800,
            resizable=True,
            text_select=True,
            background_color='#1a1d23',
            min_size=(1024, 768),
            maximized=True,
            confirm_close=True  # ✅ Confirmation native au clic sur la croix
        )
        
        # ✅ Stocker la référence pour l'API quit
        _app_window = window
        
        webview.start(debug=False)
        print("[INFO] Stellio s'est arrêté.")
        
    except Exception as e:
        print(f"[WARN] PyWebView échec ({type(e).__name__}: {e})")
        print("[INFO] Ouverture de secours dans le navigateur par défaut...")
        import webbrowser
        webbrowser.open(SERVER_URL)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[INFO] Arrêt propre.")