#!/bin/bash
# ============================================================================
# Stellio — Installation pour Raspberry Pi / Linux (mode serveur headless)
# ============================================================================
#
# Astuce Raspberry Pi à faible RAM : l'installation des dépendances Python peut
# échouer faute de mémoire. Augmentez alors le swap (CONF_SWAPSIZE=2048 dans
# /etc/dphys-swapfile, puis `sudo dphys-swapfile setup && sudo dphys-swapfile swapon`)
# et relancez ce script.

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

# Tout le script est dans un bloc { ... } : bash le lit en entier avant de l'exécuter, donc la mise à jour
# du dépôt (git reset ci-dessous) ne peut pas le corrompre pendant qu'il tourne (update-stellio).
{
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
    ffmpeg \
    libjpeg-dev zlib1g-dev libpng-dev \
    libatlas-base-dev libopenblas-dev \
    libgl1-mesa-dev libosmesa6-dev libegl1

ok "Dépendances système installées."
echo ""

# unrar : Stellio a besoin du VRAI unrar (freeware RARLAB, archives RAR5 comprises).
# Il se trouve dans la section "non-free" de Debian / Raspberry Pi OS et dans "multiverse" d'Ubuntu.
# unrar-free (outil différent) n'est qu'un repli : il ne lit pas les archives RAR5.
info "Installation de unrar (extraction des archives .rar)..."
if sudo apt-get install -y unrar; then
    ok "unrar installé."
else
    warn "Le paquet 'unrar' est introuvable (section non-free / multiverse non activée ?)."
    warn "Repli sur 'unrar-free' : l'extraction des archives RAR5 ne sera PAS prise en charge."
    warn "Pour avoir le vrai unrar : activez 'non-free' (Debian / Raspberry Pi OS) ou 'multiverse'"
    warn "(Ubuntu), puis relancez ./install-pi.sh."
    if ! sudo apt-get install -y unrar-free; then
        warn "unrar-free n'a pas pu être installé non plus : les archives .rar ne pourront pas être extraites."
    fi
fi
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
# Ne jamais renoncer : sans cela, systemd abandonne apres 5 plantages en 10 s et Stellio reste arrete
StartLimitIntervalSec=0

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
# 5b. Garde-fous : Stellio reste joignable et ne sature pas la machine
#     (conteneur LXC Proxmox, Raspberry Pi, serveur Linux)
# ----------------------------------------------------------------------------
info "Mise en place des garde-fous (surveillance, limites de ressources, journaux)..."
GUARD_OK=true
sudo mkdir -p "/etc/systemd/system/${SERVICE_NAME}.service.d" || GUARD_OK=false

# a) Limites du service : en cas de manque de mémoire, c'est Stellio qui est sacrifié, pas tout le conteneur
sudo tee "/etc/systemd/system/${SERVICE_NAME}.service.d/guard.conf" > /dev/null <<'EOF' || GUARD_OK=false
[Service]
OOMScoreAdjust=300
TasksMax=512
LimitNOFILE=8192
TimeoutStopSec=20
EOF

# b) Plafonds CPU / RAM (sauf si le script LXC les a déjà posés : on ne les écrase jamais)
LIMITS_FILE="/etc/systemd/system/${SERVICE_NAME}.service.d/limits.conf"
if [ ! -f "$LIMITS_FILE" ]; then
    MEM_MB=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)
    NB_CPU=$(nproc 2>/dev/null || echo 1)
    if [ -n "$MEM_MB" ] && [ "$MEM_MB" -gt 0 ]; then
        sudo tee "$LIMITS_FILE" > /dev/null <<EOF || GUARD_OK=false
[Service]
Nice=10
CPUWeight=50
MemoryHigh=$((MEM_MB * 75 / 100))M
MemoryMax=$((MEM_MB * 85 / 100))M
CPUQuota=$((NB_CPU * 75))%
EOF
    fi
fi

# c) Journaux : ils ne doivent jamais remplir le disque du conteneur
sudo mkdir -p /etc/systemd/journald.conf.d || GUARD_OK=false
sudo tee /etc/systemd/journald.conf.d/stellio.conf > /dev/null <<'EOF' || GUARD_OK=false
[Journal]
SystemMaxUse=100M
RuntimeMaxUse=50M
MaxRetentionSec=2week
EOF
sudo systemctl restart systemd-journald 2>/dev/null || true

# d) Surveillance : toutes les minutes, vérifie le réseau, le disque et la réponse de Stellio
echo "STELLIO_PORT=$STELLIO_PORT" | sudo tee /etc/default/stellio-watchdog > /dev/null || GUARD_OK=false
sudo tee /usr/local/bin/stellio-watchdog > /dev/null <<'EOF' || GUARD_OK=false
#!/bin/bash
# Surveillance de Stellio (lancée chaque minute par stellio-watchdog.timer).
SVC=stellio
STATE=/run/stellio-watchdog
mkdir -p "$STATE"
[ -r /etc/default/stellio-watchdog ] && . /etc/default/stellio-watchdog
[ -r /etc/stellio-lxc.conf ] && . /etc/stellio-lxc.conf
PORT="${STELLIO_PORT:-5000}"

log()   { logger -t stellio-watchdog "$*"; }
bump()  { local n=$(( $(cat "$STATE/$1" 2>/dev/null || echo 0) + 1 )); echo "$n" > "$STATE/$1"; echo "$n"; }
reset() { rm -f "$STATE/$1"; }

# 1. Réseau : plus d'adresse IP (bail DHCP perdu, interface tombée) -> on relance le réseau
if [ -z "$(hostname -I 2>/dev/null | tr -d ' ')" ]; then
    if [ "$(bump net)" -ge 2 ]; then
        log "aucune adresse IP : relance du réseau"
        systemctl restart systemd-networkd 2>/dev/null || systemctl restart networking 2>/dev/null
        reset net
    fi
else
    reset net
fi

# 2. Disque : presque plein -> on libère ce qui peut l'être sans toucher aux données de Stellio
FREE_MB=$(df -Pm / 2>/dev/null | awk 'NR==2 {print $4}')
if [ -n "$FREE_MB" ] && [ "$FREE_MB" -lt 300 ]; then
    if [ "$(bump disk)" -eq 1 ]; then log "disque presque plein (${FREE_MB} Mo libres) : nettoyage des journaux et du cache apt"; fi
    journalctl --vacuum-size=20M >/dev/null 2>&1
    apt-get clean >/dev/null 2>&1
else
    reset disk
fi

# 3. Service arrêté (plantage, arrêt par le noyau) -> redémarrage
if ! systemctl is-active --quiet "$SVC"; then
    log "service arrêté : démarrage"
    systemctl reset-failed "$SVC" 2>/dev/null
    systemctl start "$SVC"
    reset ping
    exit 0
fi

# 4. Service actif mais figé : on laisse 3 minutes de grâce après un démarrage (premier scan, dépendances)
PID=$(systemctl show -p MainPID --value "$SVC" 2>/dev/null)
AGE=$(ps -o etimes= -p "$PID" 2>/dev/null | tr -d ' ')
if [ -n "$AGE" ] && [ "$AGE" -lt 180 ]; then exit 0; fi

if curl -fs -m 20 -o /dev/null "http://127.0.0.1:${PORT}/api/ping"; then
    reset ping
else
    N=$(bump ping)
    log "Stellio ne répond pas ($N/3)"
    if [ "$N" -ge 3 ]; then
        log "Stellio ne répond plus : redémarrage"
        systemctl restart "$SVC"
        reset ping
    fi
fi
EOF
sudo chmod +x /usr/local/bin/stellio-watchdog || GUARD_OK=false

sudo tee /etc/systemd/system/stellio-watchdog.service > /dev/null <<'EOF' || GUARD_OK=false
[Unit]
Description=Surveillance de Stellio (joignabilité, réseau, disque)

[Service]
Type=oneshot
ExecStart=/usr/local/bin/stellio-watchdog
TimeoutStartSec=90
EOF
sudo tee /etc/systemd/system/stellio-watchdog.timer > /dev/null <<'EOF' || GUARD_OK=false
[Unit]
Description=Surveillance de Stellio toutes les minutes

[Timer]
OnBootSec=3min
OnUnitActiveSec=1min
AccuracySec=10s

[Install]
WantedBy=timers.target
EOF

if [ "$GUARD_OK" = true ]; then
    sudo systemctl daemon-reload
    sudo systemctl enable --now stellio-watchdog.timer
    sudo systemctl restart "$SERVICE_NAME"
    ok "Garde-fous actifs (surveillance toutes les minutes, limites CPU/RAM, journaux plafonnés)."
else
    warn "Les garde-fous n'ont pas pu être entièrement installés. Stellio fonctionne quand même ; relancez ./install-pi.sh pour réessayer."
fi
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
    echo "  sudo journalctl -t stellio-watchdog      # Interventions de la surveillance automatique"
    echo ""
    echo "Pour mettre à jour Stellio plus tard, relancez simplement ce script :"
    echo "  ./install-pi.sh"
else
    err "Le service ne semble pas actif. Consultez les logs pour comprendre pourquoi :"
    echo "  sudo journalctl -u $SERVICE_NAME -n 80 --no-pager"
    exit 1
fi
exit 0
}
