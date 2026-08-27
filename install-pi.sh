#!/bin/bash
set -e

INSTALL_DIR="${1:-/opt/stellio}"
SERVICE_USER="${SUDO_USER:-$USER}"
REPO_URL="https://github.com/stellio-app/stellio-app.git"
BRANCH="${STELLIO_BRANCH:-main}"

# Le dossier de données vit HORS du dépôt git, comme sur Windows (%APPDATA%\Stellio)
DATA_DIR="/home/$SERVICE_USER/.stellio"

echo "==> Installation de Stellio dans $INSTALL_DIR"
echo "==> Données stockées dans $DATA_DIR"

sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip \
    ffmpeg unrar-free \
    libosmesa6 libgl1 libglu1-mesa \
    git

# --- Clonage ou mise à jour ---
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "==> Mise à jour du dépôt existant (fetch + reset --hard, ne plante jamais sur un conflit)"
    sudo -u "$SERVICE_USER" git -C "$INSTALL_DIR" fetch --all --prune
    sudo -u "$SERVICE_USER" git -C "$INSTALL_DIR" reset --hard "origin/$BRANCH"
    sudo -u "$SERVICE_USER" git -C "$INSTALL_DIR" clean -fd -e data
else
    echo "==> Clonage du dépôt"
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown "$SERVICE_USER":"$SERVICE_USER" "$INSTALL_DIR"
    sudo -u "$SERVICE_USER" git clone --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
fi

# --- Migration automatique des anciennes données (si présentes dans l'ancien INSTALL_DIR/data) ---
OLD_DATA_DIR="$INSTALL_DIR/data"
if [ -d "$OLD_DATA_DIR" ] && [ ! -d "$DATA_DIR" ]; then
    echo "==> Ancien dossier de données détecté dans le dépôt : migration vers $DATA_DIR"
    sudo -u "$SERVICE_USER" mkdir -p "$DATA_DIR"
    sudo -u "$SERVICE_USER" cp -a "$OLD_DATA_DIR/." "$DATA_DIR/"
    sudo -u "$SERVICE_USER" rm -rf "$OLD_DATA_DIR"
    echo "==> Migration terminée, anciennes données conservées dans $DATA_DIR"
fi
sudo -u "$SERVICE_USER" mkdir -p "$DATA_DIR"

cd "$INSTALL_DIR"
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
Environment=STELLIO_DATA_DIR=$DATA_DIR
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

# --- Raccourci dans le dossier personnel, pour retrouver l'appli facilement avec un simple ls ---
sudo -u "$SERVICE_USER" ln -sfn "$INSTALL_DIR" "/home/$SERVICE_USER/stellio"

echo ""
echo "==> ✅ Stellio est installé et démarré."
echo "    Code de l'appli   : $INSTALL_DIR  (raccourci : ~/stellio)"
echo "    Données           : $DATA_DIR"
echo "    Accessible sur    : http://$(hostname -I | awk '{print $1}'):5000"
echo "    Logs              : sudo journalctl -u stellio -f"
echo "    Redémarrer        : sudo systemctl restart stellio"
