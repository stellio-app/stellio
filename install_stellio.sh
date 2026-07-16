:GENERATE_LINUX_SCRIPTS
echo.
echo ============================================
echo  Generation du script Linux tout-en-un...
echo ============================================

set "SH=install_stellio.sh"
del /f /q "!SH!" 2>nul

(
echo #!/bin/bash
echo set -e
echo.
echo echo "============================================"
echo echo "  STELLIO - Installation automatique Linux"
echo echo "============================================"
echo.
echo echo "[1/6] Mise a jour du systeme..."
echo sudo apt update -y ^&^& sudo apt upgrade -y
echo.
echo echo "[2/6] Installation des dependances systeme..."
echo sudo apt install -y python3 python3-pip python3-venv zip libgtk-3-dev libwebkit2gtk-4.0-dev libgl1-mesa-dev libglu1-mesa-dev freeglut3-dev libosmesa6-dev libpython3-dev
echo.
echo echo "[3/6] Creation de l'environnement virtuel..."
echo if [ ^! -d "venv" ^]; then
echo     python3 -m venv venv
echo fi
echo source venv/bin/activate
echo.
echo echo "[4/6] Installation des dependances Python..."
echo pip install --upgrade pip
echo pip install pyinstaller flask waitress pywebview numpy pillow matplotlib trimesh pyrender telethon paho-mqtt rarfile py7zr nest-asyncio smbclient cryptography imageio
echo.
echo echo "[5/6] Compilation de l'application..."
echo python3 -m PyInstaller --name Stellio --onedir --windowed --noconfirm --clean --icon=assets/logo-nom-stellio.ico --copy-metadata imageio --copy-metadata pyrender --copy-metadata trimesh --copy-metadata Pillow --collect-all numpy --collect-all PIL --collect-all matplotlib --hidden-import flask --hidden-import waitress --hidden-import webview --hidden-import trimesh --hidden-import pyrender --hidden-import numpy --hidden-import PIL --hidden-import matplotlib --hidden-import matplotlib.pyplot --hidden-import mpl_toolkits --hidden-import mpl_toolkits.mplot3d --hidden-import mpl_toolkits.mplot3d.art3d --hidden-import matplotlib.backends --hidden-import matplotlib.backends.backend_agg --hidden-import matplotlib.figure --hidden-import matplotlib.axes --hidden-import smbclient --hidden-import cryptography --collect-all telethon --hidden-import paho.mqtt --hidden-import rarfile --hidden-import py7zr --hidden-import nest_asyncio launcher.py
echo.
echo echo "[6/6] Configuration finale..."
echo mkdir -p dist/Stellio/app
echo cp main.py dist/Stellio/app/
echo cp index.html dist/Stellio/app/
echo cp script.js dist/Stellio/app/
echo cp style.css dist/Stellio/app/
echo cp -r assets dist/Stellio/app/
echo cp -r languages dist/Stellio/app/
echo cp -r bin dist/Stellio/app/
echo.
echo echo "============================================"
echo echo "  Installation terminee avec succes ^!"
echo echo "============================================"
echo echo "Lancez l'app avec : ./dist/Stellio/Stellio"
) > "!SH!"

:: Conversion Windows -> Unix line endings
powershell -NoProfile -Command "(Get-Content '!SH!' -Raw) -replace \"`r`n\", \"`n\" | Set-Content -NoNewline -Path '!SH!'"

echo  Fichier genere : !SH!
exit /b 0
