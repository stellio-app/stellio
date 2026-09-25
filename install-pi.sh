#!/bin/bash
# ============================================================================
# Stellio — Installation pour Raspberry Pi / Linux (mode serveur headless)
# ============================================================================

set -e

STELLIO_REPO="https://github.com/stellio-app/stellio.git"
STELLIO_BRANCH="main"
STELLIO_DIR="${STELLIO_DIR:-$HOME/stellio}"
STELLIO_DATA_DIR="${STELLIO_DATA_DIR:-$HOME/.stellio}"
SERVICE_NAME="stellio"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
STELLIO_PORT="${STELLIO_PORT:-5000}"

bold()  { echo -e "\033[1m$1\033[0m"; }
info()  { echo -e "→ $1"; }
ok()    { echo -e "\033[32m✅ $1\033[0m"; }
warn()  { echo -e "\033[33m⚠️  $1\033[0m"; }
err()   { echo -e "\033[31m❌ $1\033[0m"; }

bold "=== Installation de Stellio pour Raspberry Pi / Linux ==="
echo ""

# ----------------------------------------------------------------------------
# 0. Vérifications préalables
# ----------------------------------------------------------------------------
if [ "$(id -u)" -eq 0 ]; then
    err "Ne lancez pas ce script en root/sudo directement."
    echo "   Lancez-le avec votre utilisateur normal — il demandera sudo lui-même si besoin :"
    echo "   ./install-pi.sh"
    exit 1
fi

if ! command -v sudo &> /dev/null; then
    err "sudo est requis mais introuvable sur ce système."
    exit 1
fi

TOTAL_RAM_MB=$(free -m | awk '/^Mem:/{print $2}')
if [ -n "$TOTAL_RAM_MB" ] && [ "$TOTAL_RAM_MB" -lt 1500 ]; then
    warn "RAM détectée : ${TOTAL_RAM_MB} Mo. Sur un Pi 3 ou similaire, l'installation des"
    warn "dépendances Python peut être lente. Si elle échoue, augmentez le swap (voir"
    warn "commentaire dans ce script) puis relancez ./install-pi.sh."
    echo ""
fi

# ----------------------------------------------------------------------------
# 1. Dépendances système
# ----------------------------------------------------------------------------
info "Installation des dépendances système (peut prendre plusieurs minutes)..."
sudo apt-get update
sudo apt-get install -y \
    git curl \
    python3 python3-venv python3-pip python3-dev \
    build-essential \
    ffmpeg unrar-free \
    libjpeg-dev zlib1g-dev libpng-dev \
    libatlas-base-dev libopenblas-dev \
    libgl1-mesa-dev libosmesa6-dev libegl1

ok "Dépendances système installées."
echo ""

# ----------------------------------------------------------------------------
# 2. Récupération / mise à jour du code source
# ----------------------------------------------------------------------------
if [ -d "$STELLIO_DIR/.git" ]; then
    info "Dépôt existant détecté dans $STELLIO_DIR — mise à jour..."
    cd "$STELLIO_DIR"
    git fetch origin "$STELLIO_BRANCH"
    git reset --hard "origin/$STELLIO_BRANCH"
    git clean -fd
else
    info "Clonage du dépôt Stellio dans $STELLIO_DIR..."
    git clone --branch "$STELLIO_BRANCH" "$STELLIO_REPO" "$STELLIO_DIR"
    cd "$STELLIO_DIR"
fi
ok "Code source à jour."
echo ""

# ----------------------------------------------------------------------------
# 3. Environnement virtuel Python dédié
# ----------------------------------------------------------------------------
info "Préparation de l'environnement virtuel Python..."
if [ ! -d "$STELLIO_DIR/venv" ]; then
    python3 -m venv "$STELLIO_DIR/venv"
fi
# shellcheck disable=SC1091
source "$STELLIO_DIR/venv/bin/activate"
pip install --upgrade pip --quiet

info "Installation des dépendances Python (peut être long sur Raspberry Pi)..."
if ! pip install -r requirements.txt; then
    warn "Certaines dépendances ont échoué à l'installation ici."
    warn "Ce n'est pas forcément bloquant : Stellio tente de les corriger tout seul"
    warn "au démarrage (check_deps.py). S'il échoue aussi, relancez ce script après"
    warn "avoir augmenté le swap (voir en haut de ce script)."
fi
deactivate
ok "Environnement Python prêt."
echo ""

# ----------------------------------------------------------------------------
# 4. Dossier de données (séparé du code, jamais touché par une mise à jour)
# ----------------------------------------------------------------------------
mkdir -p "$STELLIO_DATA_DIR"
ok "Dossier de données : $STELLIO_DATA_DIR"
echo ""

# ----------------------------------------------------------------------------
# 5. Service systemd
# ----------------------------------------------------------------------------
info "Configuration du service systemd..."
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Stellio - Gestionnaire de fichiers 3D
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$STELLIO_DIR
Environment="STELLIO_HEADLESS=1"
Environment="STELLIO_DATA_DIR=$STELLIO_DATA_DIR"
Environment="STELLIO_PORT=$STELLIO_PORT"
ExecStart=$STELLIO_DIR/venv/bin/python3 $STELLIO_DIR/main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"
ok "Service systemd '$SERVICE_NAME' configuré et démarré."
echo ""

# ----------------------------------------------------------------------------
# 6. Vérification
# ----------------------------------------------------------------------------
info "Vérification du démarrage (jusqu'à 30s, le premier lancement scanne les dépendances)..."
STARTED=false
for _ in $(seq 1 15); do
    sleep 2
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        STARTED=true
        break
    fi
done

echo ""
if [ "$STARTED" = true ]; then
    IP_ADDR=$(hostname -I | awk '{print $1}')
    ok "Stellio est installé et démarré !"
    echo ""
    bold "  Accès : http://${IP_ADDR}:${STELLIO_PORT}"
    echo ""
    echo "Commandes utiles :"
    echo "  sudo systemctl status $SERVICE_NAME      # Statut du service"
    echo "  sudo systemctl restart $SERVICE_NAME     # Redémarrer manuellement"
    echo "  sudo journalctl -u $SERVICE_NAME -f      # Suivre les logs en direct"
    echo ""
    echo "Pour mettre à jour Stellio plus tard, relancez simplement ce script :"
    echo "  ./install-pi.sh"
else
    err "Le service ne semble pas actif. Consultez les logs pour comprendre pourquoi :"
    echo "  sudo journalctl -u $SERVICE_NAME -n 80 --no-pager"
    exit 1
fi