#!/bin/bash
set -e

echo "============================================"
echo "  STELLIO - Installation automatique Linux"
echo "============================================"
echo ""

echo "[1/6] Mise a jour du systeme..."
sudo apt update -y && sudo apt upgrade -y

echo ""
echo "[2/6] Installation des dependances systeme..."
sudo apt install -y python3 python3-pip python3-venv zip libgtk-3-dev libwebkit2gtk-4.1-dev libgl1-mesa-dev libglu1-mesa-dev freeglut3-dev libosmesa6-dev libpython3-dev

echo ""
echo "[3/6] Creation de l'environnement virtuel..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo ""
echo "[4/6] Installation des dependances Python..."
pip install --upgrade pip
pip install pyinstaller flask waitress pywebview numpy pillow matplotlib trimesh pyrender telethon paho-mqtt rarfile py7zr nest-asyncio smbclient cryptography imageio

echo ""
echo "[5/6] Compilation de l'application..."
python3 -m PyInstaller --name Stellio --onedir --windowed --noconfirm --clean --icon=assets/logo-nom-stellio.ico --copy-metadata imageio --copy-metadata pyrender --copy-metadata trimesh --copy-metadata Pillow --collect-all numpy --collect-all PIL --collect-all matplotlib --hidden-import flask --hidden-import waitress --hidden-import webview --hidden-import trimesh --hidden-import pyrender --hidden-import numpy --hidden-import PIL --hidden-import matplotlib --hidden-import matplotlib.pyplot --hidden-import mpl_toolkits --hidden-import mpl_toolkits.mplot3d --hidden-import mpl_toolkits.mplot3d.art3d --hidden-import matplotlib.backends --hidden-import matplotlib.backends.backend_agg --hidden-import matplotlib.figure --hidden-import matplotlib.axes --hidden-import smbclient --hidden-import cryptography --collect-all telethon --hidden-import paho.mqtt --hidden-import rarfile --hidden-import py7zr --hidden-import nest_asyncio launcher.py

echo ""
echo "[6/6] Configuration finale..."
mkdir -p dist/Stellio/app
cp main.py dist/Stellio/app/
cp index.html dist/Stellio/app/
cp script.js dist/Stellio/app/
cp style.css dist/Stellio/app/
cp -r assets dist/Stellio/app/
cp -r languages dist/Stellio/app/
cp -r bin dist/Stellio/app/

echo ""
echo "============================================"
echo "  Installation terminee avec succes !"
echo "============================================"
echo "Lancez l'app avec : ./dist/Stellio/Stellio"