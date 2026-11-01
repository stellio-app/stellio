#!/usr/bin/env bash
# ============================================================================
# Stellio — Création automatique d'un conteneur LXC sous Proxmox VE
# ============================================================================
#
# À lancer depuis le SHELL DE L'HÔTE PROXMOX (Datacenter > nœud > Shell), en root :
#
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/stellio-app/stellio/main/stellio-lxc.sh)"
#
# Ce que fait le script :
#   1. crée un conteneur LXC Debian 12 (non privilégié) avec les ressources choisies ;
#   2. y installe Stellio avec le script officiel install-pi.sh (dépendances système,
#      environnement Python dédié, service systemd qui démarre au boot) ;
#   3. affiche l'adresse d'accès : http://<ip-du-conteneur>:5000
#
# Mise à jour de Stellio plus tard (depuis l'hôte Proxmox) :
#   pct exec <CTID> -- update-stellio
#
# Mode non interactif : toutes les valeurs peuvent être fixées par variables d'environnement, ex. :
#   var_mode=default var_ctid=120 var_cpu=4 var_ram=4096 var_disk=16 var_bridge=vmbr0 \
#   var_mount=/mnt/pve/nas/modeles:/mnt/modeles bash -c "$(curl -fsSL .../stellio-lxc.sh)"
#
# Variables : var_mode (default|advanced) var_ctid var_hostname var_cpu var_ram var_swap var_disk
#             var_bridge var_ip (dhcp ou 192.168.1.50/24) var_gw var_vlan var_storage var_template_storage
#             var_unprivileged (1|0) var_port var_mount (hôte:conteneur) var_password
#             var_source_types (types de sources proposés dans Stellio, défaut : smb,nfs — voir plus bas)
#
# Sources : dans ce conteneur, l'ajout de dossiers / fichiers LOCAUX est masqué dans Stellio (seules les sources
# réseau SMB et NFS sont proposées). Si vous montez un dossier de l'hôte (var_mount), « dossier local » est
# automatiquement autorisé en plus. Pour changer : modifier /etc/systemd/system/stellio.service.d/sources.conf
# dans le conteneur, puis systemctl daemon-reload && systemctl restart stellio.
# ============================================================================

set -Eeuo pipefail

SVC_USER="stellio"
INSTALL_URL="https://raw.githubusercontent.com/stellio-app/stellio/main/install-pi.sh"

BOLD=$'\033[1m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RED=$'\033[31m'; CYAN=$'\033[36m'; RESET=$'\033[0m'
msg_info()  { echo -e "${CYAN}⏳ $1${RESET}"; }
msg_ok()    { echo -e "${GREEN}✅ $1${RESET}"; }
msg_warn()  { echo -e "${YELLOW}⚠️  $1${RESET}"; }
msg_error() { echo -e "${RED}❌ $1${RESET}" >&2; }

CTID_CREATED=""
error_handler() {
    local line="$1" cmd="$2"
    msg_error "Erreur à la ligne ${line} : ${cmd}"
    if [ -n "$CTID_CREATED" ]; then
        msg_warn "Le conteneur ${CTID_CREATED} a été créé mais l'installation n'est pas terminée."
        msg_warn "Pour le supprimer et recommencer : pct stop ${CTID_CREATED}; pct destroy ${CTID_CREATED}"
        msg_warn "Pour inspecter : pct enter ${CTID_CREATED}"
    fi
    exit 1
}
trap 'error_handler "$LINENO" "$BASH_COMMAND"' ERR

cancel() { echo "Annulé."; exit 0; }

# ----------------------------------------------------------------------------
# 0. Vérifications de l'hôte
# ----------------------------------------------------------------------------
header() {
    clear 2>/dev/null || true
    echo -e "${BOLD}"
    cat <<'EOF'
   _____ __       ____ _
  / ___// /____  / / /(_)___
  \__ \/ __/ _ \/ / // / __ \
 ___/ / /_/  __/ / // / /_/ /
/____/\__/\___/_/_//_/\____/
EOF
    echo -e "${RESET}  Gestionnaire de fichiers 3D — installation LXC pour Proxmox VE"
    echo ""
}
header

[ "$(id -u)" -eq 0 ] || { msg_error "Ce script doit être lancé en root sur l'hôte Proxmox."; exit 1; }
command -v pveversion >/dev/null 2>&1 || { msg_error "Proxmox VE introuvable : lancez ce script sur l'hôte Proxmox (pas dans une VM ni un conteneur)."; exit 1; }
if ! pveversion | grep -Eq 'pve-manager/([7-9]|[1-9][0-9])\.'; then
    msg_error "Proxmox VE 7 ou supérieur est requis ($(pveversion))."
    exit 1
fi
for tool in pct pveam pvesm pvesh; do
    command -v "$tool" >/dev/null 2>&1 || { msg_error "Commande '$tool' introuvable."; exit 1; }
done
if [ -f /run/systemd/container ] || grep -qa 'container=lxc' /proc/1/environ 2>/dev/null; then
    msg_error "Lancez ce script sur l'hôte Proxmox, pas depuis un conteneur."
    exit 1
fi

HAS_WHIPTAIL=0
if command -v whiptail >/dev/null 2>&1 && [ -t 0 ] && [ -t 1 ]; then HAS_WHIPTAIL=1; fi

# ----------------------------------------------------------------------------
# 1. Paramètres
# ----------------------------------------------------------------------------
MODE="${var_mode:-}"
if [ -z "$MODE" ]; then
    if [ "$HAS_WHIPTAIL" -eq 1 ]; then
        CHOICE=$(whiptail --backtitle "Stellio — Proxmox VE" --title "Installation de Stellio" \
            --menu "\nCréer un conteneur LXC Stellio :" 15 64 3 \
            "default"  "Paramètres par défaut (recommandé)" \
            "advanced" "Paramètres avancés" \
            "cancel"   "Annuler" 3>&1 1>&2 2>&3) || cancel
        [ "$CHOICE" = "cancel" ] && cancel
        MODE="$CHOICE"
    else
        MODE="default"
    fi
fi

NEXT_ID=$(pvesh get /cluster/nextid)
CTID="${var_ctid:-$NEXT_ID}"
HN="${var_hostname:-stellio}"
CORES="${var_cpu:-2}"
RAM="${var_ram:-2048}"
SWAP="${var_swap:-512}"
DISK="${var_disk:-8}"
BRIDGE="${var_bridge:-vmbr0}"
IPCFG="${var_ip:-dhcp}"
GW="${var_gw:-}"
VLAN="${var_vlan:-}"
UNPRIV="${var_unprivileged:-1}"
PORT="${var_port:-5000}"
MOUNT="${var_mount:-}"
STORAGE="${var_storage:-}"
TEMPLATE_STORAGE="${var_template_storage:-}"
ROOT_PW="${var_password:-}"
SOURCE_TYPES="${var_source_types:-}"

ask() {  # ask "question" "défaut"
    whiptail --backtitle "Stellio — Proxmox VE" --title "Paramètres avancés" \
        --inputbox "$1" 10 66 "$2" 3>&1 1>&2 2>&3
}

# Liste les stockages Proxmox qui acceptent un type de contenu (rootdir, vztmpl)
list_storages() { pvesm status -content "$1" 2>/dev/null | awk 'NR>1 && $3=="active" {print $1}'; }

pick_storage() {  # pick_storage <content> <titre> <préféré>
    local content="$1" title="$2" preferred="$3"
    local -a stores
    mapfile -t stores < <(list_storages "$content")
    [ "${#stores[@]}" -gt 0 ] || { msg_error "Aucun stockage actif ne gère le contenu '$content'."; exit 1; }
    if [ "${#stores[@]}" -eq 1 ]; then echo "${stores[0]}"; return; fi
    if [ "$MODE" = "advanced" ] && [ "$HAS_WHIPTAIL" -eq 1 ]; then
        local -a menu=()
        local s
        for s in "${stores[@]}"; do menu+=("$s" "$(pvesm status 2>/dev/null | awk -v s="$s" '$1==s {printf "type %s, libre %.1f Go", $2, $6/1048576}')"); done
        whiptail --backtitle "Stellio — Proxmox VE" --title "$title" --menu "\nChoisissez un stockage :" 16 66 6 "${menu[@]}" 3>&1 1>&2 2>&3 || cancel
        return
    fi
    local s
    for s in "$preferred" local-lvm local-zfs local; do
        if printf '%s\n' "${stores[@]}" | grep -qx "$s"; then echo "$s"; return; fi
    done
    echo "${stores[0]}"
}

if [ "$MODE" = "advanced" ] && [ "$HAS_WHIPTAIL" -eq 1 ]; then
    CTID=$(ask "ID du conteneur (CTID)" "$CTID") || cancel
    HN=$(ask "Nom d'hôte" "$HN") || cancel
    CORES=$(ask "Nombre de cœurs CPU" "$CORES") || cancel
    RAM=$(ask "Mémoire (Mo)" "$RAM") || cancel
    DISK=$(ask "Taille du disque (Go)" "$DISK") || cancel
    BRIDGE=$(ask "Pont réseau (bridge)" "$BRIDGE") || cancel
    IPCFG=$(ask "Adresse IP : dhcp, ou une IP statique avec masque (ex. 192.168.1.50/24)" "$IPCFG") || cancel
    if [ "$IPCFG" != "dhcp" ]; then GW=$(ask "Passerelle (ex. 192.168.1.1)" "$GW") || cancel; fi
    VLAN=$(ask "VLAN (laisser vide si aucun)" "$VLAN") || cancel
    PORT=$(ask "Port de Stellio" "$PORT") || cancel
    if whiptail --backtitle "Stellio — Proxmox VE" --title "Conteneur privilégié ?" --defaultno \
        --yesno "Un conteneur NON privilégié est plus sûr (recommandé).\nUn conteneur privilégié simplifie l'accès à un dossier monté de l'hôte.\n\nCréer un conteneur privilégié ?" 12 70; then
        UNPRIV=0
    else
        UNPRIV=1
    fi
    MOUNT=$(ask "Dossier de l'hôte à monter dans le conteneur, au format /chemin/hote:/chemin/conteneur (vide = aucun)\nEx. /mnt/pve/nas/modeles:/mnt/modeles" "$MOUNT") || cancel
fi

# Validation
is_int() { [[ "$1" =~ ^[0-9]+$ ]]; }
is_int "$CTID"  || { msg_error "CTID invalide : $CTID"; exit 1; }
is_int "$CORES" && [ "$CORES" -ge 1 ] || { msg_error "Nombre de cœurs invalide : $CORES"; exit 1; }
is_int "$RAM"   && [ "$RAM" -ge 1024 ] || { msg_error "Mémoire invalide (minimum 1024 Mo) : $RAM"; exit 1; }
is_int "$SWAP"  || { msg_error "Swap invalide : $SWAP"; exit 1; }
is_int "$DISK"  && [ "$DISK" -ge 4 ] || { msg_error "Disque invalide (minimum 4 Go) : $DISK"; exit 1; }
is_int "$PORT"  && [ "$PORT" -ge 1 ] && [ "$PORT" -le 65535 ] || { msg_error "Port invalide : $PORT"; exit 1; }
[[ "$HN" =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$ ]] || { msg_error "Nom d'hôte invalide : $HN"; exit 1; }
if pvesh get /cluster/nextid --vmid "$CTID" >/dev/null 2>&1; then :; else
    msg_error "L'ID $CTID est déjà utilisé."; exit 1
fi
if [ "$IPCFG" != "dhcp" ] && [ -z "$GW" ]; then msg_error "Une IP statique nécessite une passerelle (var_gw)."; exit 1; fi

HOST_MOUNT=""; CT_MOUNT=""
if [ -n "$MOUNT" ]; then
    HOST_MOUNT="${MOUNT%%:*}"; CT_MOUNT="${MOUNT#*:}"
    [ -d "$HOST_MOUNT" ] || { msg_error "Le dossier de l'hôte '$HOST_MOUNT' n'existe pas."; exit 1; }
    [[ "$CT_MOUNT" == /* ]] || { msg_error "Le chemin dans le conteneur doit être absolu (ex. /mnt/modeles)."; exit 1; }
fi

if [ -z "$SOURCE_TYPES" ]; then
    if [ -n "$MOUNT" ]; then SOURCE_TYPES="folder,smb,nfs"; else SOURCE_TYPES="smb,nfs"; fi
fi
[[ "$SOURCE_TYPES" =~ ^(folder|file|smb|nfs)(,(folder|file|smb|nfs))*$ ]] || { msg_error "var_source_types invalide : $SOURCE_TYPES (valeurs : folder,file,smb,nfs)"; exit 1; }

[ -n "$STORAGE" ] || STORAGE=$(pick_storage rootdir "Stockage du conteneur" local-lvm)
[ -n "$TEMPLATE_STORAGE" ] || TEMPLATE_STORAGE=$(pick_storage vztmpl "Stockage des modèles (templates)" local)
[ -n "$STORAGE" ] && [ -n "$TEMPLATE_STORAGE" ] || cancel

if [ -z "$ROOT_PW" ]; then
    ROOT_PW=$(head -c 24 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 14)
fi

# ----------------------------------------------------------------------------
# Affichage « à la community-scripts » : récapitulatif, étapes avec indicateur de progression
# ----------------------------------------------------------------------------
UL=$'\033[4m'
IS_TTY=0; [ -t 1 ] && IS_TTY=1
LOG=$(mktemp /tmp/stellio-lxc-install.XXXXXX)
SPIN_FRAMES=(⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏)

kv() {  # kv <icône> <libellé> <valeur>
    printf ' %s  %s%s%s %s%s%s%s\n' "$1" "$CYAN" "$2" "$RESET" "$UL" "$GREEN" "$3" "$RESET"
}

storage_free_gb() { pvesm status 2>/dev/null | awk -v s="$1" '$1==s {printf "%.1f", $6/1048576}'; }
storage_type()    { pvesm status 2>/dev/null | awk -v s="$1" '$1==s {print $2}'; }

# step "Message" commande args...   -> exécute en arrière-plan avec un indicateur animé ; la sortie va dans $LOG
step() {
    local msg="$1"; shift
    : > "$LOG"
    "$@" >>"$LOG" 2>&1 &
    local pid=$! i=0 sub=""
    if [ "$IS_TTY" -eq 1 ]; then
        tput civis 2>/dev/null || true
        while kill -0 "$pid" 2>/dev/null; do
            sub=$(grep -a '^→' "$LOG" 2>/dev/null | tail -n1 | cut -c1-64 || true)
            printf '\r\033[K %s%s%s %s%s' "$YELLOW" "${SPIN_FRAMES[i]}" "$RESET" "$msg" "${sub:+ ${CYAN}— ${sub#→ }${RESET}}"
            i=$(( (i + 1) % ${#SPIN_FRAMES[@]} ))
            sleep 0.15
        done
        tput cnorm 2>/dev/null || true
    else
        echo " ⏳ $msg ..."
    fi
    if wait "$pid"; then
        if [ "$IS_TTY" -eq 1 ]; then printf '\r\033[K'; fi
        echo -e " ${GREEN}✔️${RESET}  $msg"
    else
        if [ "$IS_TTY" -eq 1 ]; then printf '\r\033[K'; fi
        echo -e " ${RED}✖️${RESET}  $msg" >&2
        if [ "${STEP_SOFT:-0}" = "1" ]; then return 1; fi
        echo -e "${YELLOW}--- dernières lignes du journal ---${RESET}" >&2
        tail -n 30 "$LOG" >&2 || true
        echo -e "${YELLOW}Journal complet : $LOG${RESET}" >&2
        if [ -n "$CTID_CREATED" ]; then
            msg_warn "Conteneur ${CTID_CREATED} créé mais installation incomplète. Pour recommencer : pct stop ${CTID_CREATED}; pct destroy ${CTID_CREATED}"
        fi
        exit 1
    fi
}

NODE=$(hostname)
PVE_VER=$(pveversion | sed -E 's#^pve-manager/([^/]+)/.*running kernel: ([^)]*)\).*#\1 (Kernel: \2)#')
echo -e " ⚙️  ${CYAN}Paramètres $([ "$MODE" = "advanced" ] && echo 'avancés' || echo 'par défaut') sur le nœud ${NODE}${RESET}"
kv "💡" "Version PVE :" "$PVE_VER"
kv "🆔" "ID du conteneur :" "$CTID ($HN)"
kv "🖥️ " "Système :" "debian (12)"
kv "📦" "Type de conteneur :" "$([ "$UNPRIV" = "1" ] && echo 'non privilégié' || echo 'privilégié')"
kv "💾" "Taille du disque :" "${DISK} Go"
kv "🧠" "Cœurs CPU :" "$CORES"
kv "🛠️ " "Mémoire RAM :" "${RAM} Mo (swap ${SWAP} Mo)"
kv "🌐" "Réseau :" "${BRIDGE}${VLAN:+ (VLAN $VLAN)}, IP ${IPCFG}${GW:+ via $GW}"
kv "🔒" "Sources proposées :" "$SOURCE_TYPES ($([[ ",$SOURCE_TYPES," == *,folder,* ]] && echo 'dossiers locaux autorisés' || echo 'dossiers locaux masqués'))"
[ -n "$MOUNT" ] && kv "📁" "Dossier monté :" "$HOST_MOUNT → $CT_MOUNT"
echo -e " 🚀  ${CYAN}Création d'un conteneur LXC Stellio avec les paramètres ci-dessus${RESET}"
echo ""
echo -e " ${GREEN}✔️${RESET}  Stockage « ${STORAGE} » ($(storage_type "$STORAGE")) validé — libre : $(storage_free_gb "$STORAGE") Go"
echo -e " ${GREEN}✔️${RESET}  Stockage des modèles « ${TEMPLATE_STORAGE} » ($(storage_type "$TEMPLATE_STORAGE")) validé — libre : $(storage_free_gb "$TEMPLATE_STORAGE") Go"

# ----------------------------------------------------------------------------
# 2. Modèle Debian 12
# ----------------------------------------------------------------------------
refresh_templates() { pveam update || echo "pveam update a échoué (réseau ?) — liste en cache utilisée"; }
step "Mise à jour de la liste des modèles Proxmox" refresh_templates

TEMPLATE=$(pveam available --section system | awk '$2 ~ /^debian-12-standard/ {print $2}' | sort -V | tail -n1)
[ -n "$TEMPLATE" ] || { msg_error "Modèle Debian 12 introuvable dans la liste Proxmox."; exit 1; }

if pveam list "$TEMPLATE_STORAGE" | grep -F -- "$TEMPLATE" >/dev/null; then
    echo -e " ${GREEN}✔️${RESET}  Modèle ${TEMPLATE} déjà présent"
else
    step "Téléchargement du modèle ${TEMPLATE}" pveam download "$TEMPLATE_STORAGE" "$TEMPLATE"
fi

# ----------------------------------------------------------------------------
# 3. Création du conteneur
# ----------------------------------------------------------------------------
NET0="name=eth0,bridge=${BRIDGE},ip=${IPCFG}"
[ -n "$GW" ]   && NET0+=",gw=${GW}"
[ -n "$VLAN" ] && NET0+=",tag=${VLAN}"

create_ct() {
    pct create "$CTID" "${TEMPLATE_STORAGE}:vztmpl/${TEMPLATE}" \
        --hostname "$HN" \
        --cores "$CORES" --memory "$RAM" --swap "$SWAP" \
        --rootfs "${STORAGE}:${DISK}" \
        --net0 "$NET0" \
        --unprivileged "$UNPRIV" \
        --features nesting=1 \
        --ostype debian \
        --onboot 1 \
        --tags "stellio;impression-3d" \
        --password "$ROOT_PW" \
        --description "Stellio — gestionnaire de fichiers 3D (installé par stellio-lxc.sh). Mise à jour : pct exec $CTID -- update-stellio"
    if [ -n "$MOUNT" ]; then pct set "$CTID" -mp0 "${HOST_MOUNT},mp=${CT_MOUNT}"; fi
}
step "Création du conteneur LXC ${CTID}" create_ct
CTID_CREATED="$CTID"

step "Démarrage du conteneur" pct start "$CTID"

wait_network() {
    local ip=""
    for _ in $(seq 1 40); do
        ip=$(pct exec "$CTID" -- hostname -I 2>/dev/null | awk '{print $1}' || true)
        if [ -n "$ip" ] && pct exec "$CTID" -- getent hosts deb.debian.org >/dev/null 2>&1; then return 0; fi
        sleep 2
    done
    echo "Le conteneur n'a pas d'accès réseau/DNS (IP : ${ip:-aucune}). Vérifiez le pont ${BRIDGE}, le DHCP / l'IP statique, la passerelle et le DNS."
    return 1
}
step "Attente du réseau du conteneur" wait_network
CT_IP=$(pct exec "$CTID" -- hostname -I 2>/dev/null | awk '{print $1}' || true)

# ----------------------------------------------------------------------------
# 4. Installation de Stellio dans le conteneur (par étapes)
# ----------------------------------------------------------------------------
SETUP_SCRIPT=$(mktemp); SETUP_ENV=$(mktemp)
printf 'SVC_USER=%q\nPORT=%q\nSOURCE_TYPES=%q\nINSTALL_URL=%q\n' "$SVC_USER" "$PORT" "$SOURCE_TYPES" "$INSTALL_URL" > "$SETUP_ENV"
cat > "$SETUP_SCRIPT" <<'SETUP'
#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive LC_ALL=C.UTF-8 LANG=C.UTF-8
# shellcheck disable=SC1091
source /root/stellio-setup.env

stage_sources() {
    echo "→ Activation des sections contrib / non-free"
    for f in /etc/apt/sources.list /etc/apt/sources.list.d/*.sources; do
        [ -f "$f" ] || continue
        sed -i -E '/^(deb |Components:)/{/non-free/!s/\bmain\b/main contrib non-free non-free-firmware/}' "$f"
    done
}

stage_base() {
    echo "→ Mise à jour de la liste des paquets"
    apt-get update
    echo "→ Installation de sudo, curl et git"
    apt-get install -y sudo curl git ca-certificates
}

stage_user() {
    echo "→ Création de l'utilisateur ${SVC_USER}"
    id "$SVC_USER" >/dev/null 2>&1 || useradd -m -s /bin/bash "$SVC_USER"
    echo "${SVC_USER} ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/${SVC_USER}"
    chmod 440 "/etc/sudoers.d/${SVC_USER}"
    echo "→ Téléchargement du script d'installation officiel"
    curl -fsSL "$INSTALL_URL" -o "/home/${SVC_USER}/install-pi.sh"
    chown "${SVC_USER}:${SVC_USER}" "/home/${SVC_USER}/install-pi.sh"
    chmod +x "/home/${SVC_USER}/install-pi.sh"
}

stage_install() {
    # install-pi.sh affiche ses propres étapes « → ... » : elles alimentent l'indicateur de progression
    su - "$SVC_USER" -c "STELLIO_PORT=${PORT} bash ~/install-pi.sh"
}

stage_service() {
    echo "→ Réglage des types de sources : ${SOURCE_TYPES}"
    mkdir -p /etc/systemd/system/stellio.service.d
    cat > /etc/systemd/system/stellio.service.d/sources.conf <<CONF
[Service]
Environment="STELLIO_ALLOWED_SOURCE_TYPES=${SOURCE_TYPES}"
CONF
    systemctl daemon-reload
    systemctl restart stellio
    cat > /usr/local/bin/update-stellio <<'UPD'
#!/usr/bin/env bash
# Met Stellio à jour (code source + dépendances) puis redémarre le service.
exec su - stellio -c 'bash ~/stellio/install-pi.sh'
UPD
    chmod +x /usr/local/bin/update-stellio
}

stage_console() {
    echo "→ Configuration de la console du conteneur"
    echo "STELLIO_PORT=${PORT}" > /etc/stellio-lxc.conf
    # Connexion automatique en root sur la console Proxmox (comme les scripts community-scripts)
    mkdir -p /etc/systemd/system/container-getty@1.service.d
    cat > /etc/systemd/system/container-getty@1.service.d/override.conf <<'GETTY'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear --keep-baud tty%I 115200,38400,9600 $TERM
GETTY
    # Bandeau affiché à chaque connexion
    cat > /etc/profile.d/00_stellio-details.sh <<'BANNER'
#!/bin/sh
case "$-" in *i*) ;; *) return 0 2>/dev/null || exit 0 ;; esac
[ -r /etc/stellio-lxc.conf ] && . /etc/stellio-lxc.conf
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
OSN=$( . /etc/os-release 2>/dev/null; echo "${NAME:-Debian GNU/Linux} - Version: ${VERSION_ID:-}")
printf '\n\033[1mStellio LXC Container\033[0m\n'
printf '    🌐  \033[33mProvided by: \033[32mstellio-app \033[33m| GitHub: \033[32mhttps://github.com/stellio-app/stellio\033[0m\n\n'
printf '    🖥️   \033[33mOS: \033[32m%s\033[0m\n' "$OSN"
printf '    🏠  \033[33mHostname: \033[32m%s\033[0m\n' "$(hostname)"
printf '    💡  \033[33mIP Address: \033[32m%s\033[0m\n' "${IP:-?}"
printf '    🔗  \033[33mStellio: \033[32mhttp://%s:%s\033[0m\n' "${IP:-?}" "${STELLIO_PORT:-5000}"
printf '    🔄  \033[33mMise à jour: \033[32mupdate-stellio\033[0m\n\n'
BANNER
    chmod +x /etc/profile.d/00_stellio-details.sh
    systemctl daemon-reload
    systemctl restart container-getty@1.service 2>/dev/null || true
}

stage_cleanup() {
    rm -f /root/stellio-setup.sh /root/stellio-setup.env
}

"stage_${1:?étape manquante}"
SETUP

pct push "$CTID" "$SETUP_SCRIPT" /root/stellio-setup.sh --perms 0755 >/dev/null
pct push "$CTID" "$SETUP_ENV" /root/stellio-setup.env >/dev/null
rm -f "$SETUP_SCRIPT" "$SETUP_ENV"

ct_stage() { pct exec "$CTID" -- bash /root/stellio-setup.sh "$1"; }
step "Configuration des sources de paquets Debian"              ct_stage sources
step "Installation des paquets de base"                         ct_stage base
step "Préparation de l'utilisateur et du script d'installation" ct_stage user
step "Installation de Stellio (5 à 15 minutes)"                 ct_stage install
step "Configuration du service et des types de sources"         ct_stage service
step "Configuration de la console du conteneur"                 ct_stage console

# ----------------------------------------------------------------------------
# 5. Vérification finale
# ----------------------------------------------------------------------------
wait_stellio() {
    for _ in $(seq 1 60); do
        if pct exec "$CTID" -- curl -fs -o /dev/null "http://127.0.0.1:${PORT}/api/ping" 2>/dev/null; then return 0; fi
        sleep 2
    done
    echo "Stellio ne répond pas encore sur le port ${PORT}."
    return 1
}
UP=0
if STEP_SOFT=1 step "Vérification du démarrage de Stellio" wait_stellio; then UP=1; fi
pct exec "$CTID" -- bash /root/stellio-setup.sh cleanup 2>/dev/null || true

CT_IP=$(pct exec "$CTID" -- hostname -I 2>/dev/null | awk '{print $1}' || echo "$CT_IP")
CTID_CREATED=""   # installation terminée : plus de message de suppression en cas d'erreur
rm -f "$LOG"

echo ""
if [ "$UP" -eq 1 ]; then
    echo -e " ${GREEN}✔️${RESET}  Stellio répond sur le port ${PORT}"
    echo -e " ${GREEN}✔️  Terminé avec succès !${RESET}"
else
    echo -e " ${YELLOW}⚠️${RESET}  Stellio ne répond pas encore (le premier lancement vérifie les modules, patientez 1 à 2 minutes)"
    echo -e "     Journaux : pct exec $CTID -- journalctl -u stellio -n 80 --no-pager"
fi
echo ""
echo -e " 🚀  ${GREEN}Le conteneur Stellio a été créé avec succès !${RESET}"
echo -e " 💡  ${YELLOW}Stellio est accessible à l'adresse : ${BOLD}http://${CT_IP}:${PORT}${RESET}"
echo ""
echo "     Conteneur ........ $CTID ($HN)  —  console : pct console $CTID (connexion automatique)"
echo "     Mot de passe root  $ROOT_PW"
echo "     Mettre à jour .... pct exec $CTID -- update-stellio"
echo "     Journaux ......... pct exec $CTID -- journalctl -u stellio -f"
if [ -n "$MOUNT" ]; then
    echo ""
    echo "     Dossier monté : ajoutez '$CT_MOUNT' comme « Dossier local » dans Stellio (Paramètres → Sources)."
    if [ "$UNPRIV" = "1" ]; then
        echo "     Conteneur non privilégié : l'utilisateur 'stellio' (uid 1000) correspond à l'uid 101000 de l'hôte."
        echo "     Si le dossier n'est pas lisible/modifiable : chown -R 101000:101000 '$HOST_MOUNT' (ou chmod o+rwX)."
    fi
else
    echo ""
    echo "     Sources : seules les sources réseau SMB / NFS sont proposées dans Stellio (dossiers locaux masqués)."
    echo "     Pour autoriser aussi un dossier monté de l'hôte : pct set $CTID -mp0 /chemin/hote,mp=/mnt/modeles, puis dans le"
    echo "     conteneur éditez /etc/systemd/system/stellio.service.d/sources.conf (STELLIO_ALLOWED_SOURCE_TYPES=folder,smb,nfs)"
    echo "     et lancez : systemctl daemon-reload && systemctl restart stellio"
fi
echo ""
