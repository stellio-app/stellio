:: ============================================================
::  GENERATION DU SCRIPT LINUX TOUT-EN-UN
:: ============================================================
:GENERATE_LINUX_SCRIPTS
echo.
echo ============================================
echo  Generation du script Linux tout-en-un...
echo ============================================

set "SH=install_stellio.sh"
del /f /q "!SH!" 2>nul

> "!SH!" echo #!/bin/bash
>>"!SH!" echo set -e
>>"!SH!" echo.
>>"!SH!" echo echo "============================================"
>>"!SH!" echo echo "  STELLIO - Installation automatique Linux"
>>"!SH!" echo echo "============================================"
>>"!SH!" echo.
>>"!SH!" echo echo "[1/6] Mise a jour du systeme..."
>>"!SH!" echo sudo apt update -y ^&^& sudo apt upgrade -y
>>"!SH!" echo.
>>"!SH!" echo echo "[2/6] Installation des dependances systeme..."
>>"!SH!" echo sudo apt install -y python3 python3-pip python3-venv zip libgtk-3-dev libwebkit2gtk-4.0-dev libgl1-mesa-dev libglu1-mesa-dev freeglut3-dev libosmesa6-dev libpython3-dev
>>"!SH!" echo.
>>"!SH!" echo echo "[3/6] Creation de l'environnement virtuel..."
>>"!SH!" echo if [ ! -d "venv" ]; then
>>"!SH!" echo     python3 -m venv venv
>>"!SH!" echo fi
>>"!SH!" echo source venv/bin/activate
>>"!SH!" echo.
>>"!SH!" echo echo "[4/6] Installation des dependances Python..."
>>"!SH!" echo pip install --upgrade pip
>>"!SH!" echo pip install pyinstaller flask waitress pywebview numpy pillow matplotlib trimesh pyrender telethon paho-mqtt rarfile py7zr nest-asyncio smbclient cryptography imageio
>>"!SH!" echo.
>>"!SH!" echo echo "[5/6] Compilation de l'application..."
>>"!SH!" echo python3 -m PyInstaller --name Stellio --onedir --windowed --noconfirm --clean --icon=assets/logo-nom-stellio.ico --copy-metadata imageio --copy-metadata pyrender --copy-metadata trimesh --copy-metadata Pillow --collect-all numpy --collect-all PIL --collect-all matplotlib --hidden-import flask --hidden-import waitress --hidden-import webview --hidden-import trimesh --hidden-import pyrender --hidden-import numpy --hidden-import PIL --hidden-import matplotlib --hidden-import matplotlib.pyplot --hidden-import mpl_toolkits --hidden-import mpl_toolkits.mplot3d --hidden-import mpl_toolkits.mplot3d.art3d --hidden-import matplotlib.backends --hidden-import matplotlib.backends.backend_agg --hidden-import matplotlib.figure --hidden-import matplotlib.axes --hidden-import smbclient --hidden-import cryptography --collect-all telethon --hidden-import paho.mqtt --hidden-import rarfile --hidden-import py7zr --hidden-import nest_asyncio launcher.py
>>"!SH!" echo.
>>"!SH!" echo echo "[6/6] Configuration finale..."
>>"!SH!" echo mkdir -p dist/Stellio/app
>>"!SH!" echo cp main.py dist/Stellio/app/
>>"!SH!" echo cp index.html dist/Stellio/app/
>>"!SH!" echo cp script.js dist/Stellio/app/
>>"!SH!" echo cp style.css dist/Stellio/app/
>>"!SH!" echo cp -r assets dist/Stellio/app/
>>"!SH!" echo cp -r languages dist/Stellio/app/
>>"!SH!" echo cp -r bin dist/Stellio/app/
>>"!SH!" echo.
>>"!SH!" echo echo "============================================"
>>"!SH!" echo echo "  Installation terminee avec succes !"
>>"!SH!" echo echo "============================================"
>>"!SH!" echo echo "Lancez l'app avec : ./dist/Stellio/Stellio"

:: Conversion fins de ligne Windows -> Unix
powershell -NoProfile -Command "(Get-Content '!SH!' -Raw) -replace \"`r`n\", \"`n\" | Set-Content -NoNewline -Path '!SH!'"

echo  Fichier genere : !SH!
exit /b 0
