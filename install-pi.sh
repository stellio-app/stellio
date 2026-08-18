#!/bin/bash
# Installation de Stellio sur Raspberry Pi (Raspberry Pi OS 64 bits recommandé).
# Usage : ./install-pi.sh [/chemin/install]  (par défaut : /opt/stellio)
set -e

INSTALL_DIR="${1:-/opt/stellio}"
SERVICE_USER="${SUDO_USER:-$USER}"
REPO_URL="https://github.com/stellio-app/stellio-app.git"

echo "==> Installation de Stellio dans $INSTALL_DIR"

# --- Dépendances système ---
# ffmpeg      : flux caméra RTSPS Bambu X1/X2/H2 (voir _setup_ffmpeg_tool)
# unrar-free  : extraction .rar (voir _setup_rar_tool)
# libosmesa6, libgl1 : rendu offscreen des miniatures via pyrender
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip \
    ffmpeg unrar-free \
    libosmesa6 libgl1 libglu1-mesa \
    git

# --- Récupération de l'app ---
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "==> Mise à jour du dépôt existant"
    sudo -u "$SERVICE_USER" git -C "$INSTALL_DIR" pull
else
    echo "==> Clonage du dépôt"
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown "$SERVICE_USER":"$SERVICE_USER" "$INSTALL_DIR"
    sudo -u "$SERVICE_USER" git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# --- Environnement virtuel Python ---
sudo -u "$SERVICE_USER" python3 -m venv "$INSTALL_DIR/venv"
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --upgrade pip
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir -r requirements-pi.txt

# --- Service systemd ---
SERVICE_FILE=/etc/systemd/system/stellio.service
echo "==> Écriture de $SERVICE_FILE"
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Stellio - Gestionnaire de fichiers d'impression 3D
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=STELLIO_HEADLESS=1
Environment=STELLIO_DATA_DIR=$INSTALL_DIR/data
Environment=STELLIO_PORT=5000
ExecStart=$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable stellio.service
sudo systemctl restart stellio.service

echo ""
echo "==> ✅ Stellio est installé et démarré."
echo "    Accessible sur http://$(hostname -I | awk '{print $1}'):5000"
echo "    Logs : sudo journalctl -u stellio -f"
echo "    Redémarrer : sudo systemctl restart stellio"
