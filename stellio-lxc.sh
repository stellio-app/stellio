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
#             var_bridge var_ip (dhcp ou 192.168.1.50/24) var_gw var_vlan var_storage (disque du conteneur)
#             var_template_storage (modèles) var_choose_storage=1 (proposer le choix des stockages en mode par défaut)
#             var_unprivileged (1|0) var_port var_mount (hôte:conteneur) var_password
#             var_source_types (types de sources proposés dans Stellio, défaut : smb,nfs — voir plus bas)
#
# Sources : dans ce conteneur, l'ajout de dossiers / fichiers LOCAUX est masqué dans Stellio (seules les sources
# réseau SMB et NFS sont proposées). Si vous montez un dossier de l'hôte (var_mount), « dossier local » est
# automatiquement autorisé en plus. Pour changer : modifier /etc/systemd/system/stellio.service.d/sources.conf
# dans le conteneur, puis systemctl daemon-reload && systemctl restart stellio.
# ============================================================================

set -Eeuo pipefail

# ----------------------------------------------------------------------------
# Langue : celle de Proxmox (var_lang=fr|en|de|es|pt|it|zh|ja pour forcer ; repli : anglais)
# ----------------------------------------------------------------------------
detect_lang() {
    local l="${var_lang:-}"
    if [ -z "$l" ] && [ -r /etc/pve/datacenter.cfg ]; then l=$(awk -F': *' '$1=="language"{print $2; exit}' /etc/pve/datacenter.cfg 2>/dev/null || true); fi
    if [ -z "$l" ]; then l="${LC_ALL:-${LANG:-}}"; fi
    l="${l,,}"
    case "$l" in
        fr*) echo fr ;; de*) echo de ;; es*) echo es ;; pt*) echo pt ;; it*) echo it ;;
        zh*) echo zh ;; ja*) echo ja ;; *) echo en ;;
    esac
}

lang_fr() {
    M_sub='Gestionnaire de fichiers 3D — installation LXC pour Proxmox VE'
    M_cancelled='Annulé.'
    M_e_root='Ce script doit être lancé en root sur l'\''hôte Proxmox.'
    M_e_nopve='Proxmox VE introuvable : lancez ce script sur l'\''hôte Proxmox (pas dans une VM ni un conteneur).'
    M_e_pvever='Proxmox VE 7 ou supérieur est requis (%s).'
    M_e_tool='Commande '\''%s'\'' introuvable.'
    M_e_inct='Lancez ce script sur l'\''hôte Proxmox, pas depuis un conteneur.'
    M_e_line='Erreur à la ligne %s : %s'
    M_w_ct1='Le conteneur %s a été créé mais l'\''installation n'\''est pas terminée.'
    M_w_ct2='Pour le supprimer et recommencer : pct stop %s; pct destroy %s'
    M_w_ct3='Pour inspecter : pct enter %s'
    M_w_ct4='Conteneur %s créé mais installation incomplète. Pour recommencer : pct stop %s; pct destroy %s'
    M_last_lines='--- dernières lignes du journal ---'
    M_full_log='Journal complet : %s'
    M_m_title='Installation de Stellio'
    M_m_text='Créer un conteneur LXC Stellio :'
    M_m_default='Paramètres par défaut (recommandé)'
    M_m_storage='Paramètres par défaut + choix des stockages'
    M_m_adv='Paramètres avancés (dont les stockages)'
    M_m_cancel='Annuler'
    M_a_title='Paramètres avancés'
    M_a_ctid='ID du conteneur (CTID)'
    M_a_hn='Nom d'\''hôte'
    M_a_cores='Nombre de cœurs CPU'
    M_a_ram='Mémoire (Mo)'
    M_a_disk='Taille du disque (Go)'
    M_a_bridge='Pont réseau (bridge)'
    M_a_ip='Adresse IP : dhcp, ou une IP statique avec masque (ex. 192.168.1.50/24)'
    M_a_gw='Passerelle (ex. 192.168.1.1)'
    M_a_vlan='VLAN (laisser vide si aucun)'
    M_a_port='Port de Stellio'
    M_a_priv_t='Conteneur privilégié ?'
    M_a_priv_x='Un conteneur NON privilégié est plus sûr (recommandé).\nUn conteneur privilégié simplifie l'\''accès à un dossier monté de l'\''hôte.\n\nCréer un conteneur privilégié ?'
    M_a_mount='Dossier de l'\''hôte à monter dans le conteneur, au format /chemin/hote:/chemin/conteneur (vide = aucun)\nEx. /mnt/pve/nas/modeles:/mnt/modeles'
    M_s_none='Aucun stockage actif ne gère le contenu '\''%s'\''.'
    M_s_menu='Choisissez un stockage (%s) :'
    M_s_item='type %s, libre %s Go'
    M_s_t_ct='Stockage du conteneur (disque du LXC)'
    M_s_t_tpl='Stockage des modèles (templates)'
    M_v_ctid='CTID invalide : %s'
    M_v_cores='Nombre de cœurs invalide : %s'
    M_v_ram='Mémoire invalide (minimum 1024 Mo) : %s'
    M_v_swap='Swap invalide : %s'
    M_v_disk='Disque invalide (minimum 4 Go) : %s'
    M_v_port='Port invalide : %s'
    M_v_hn='Nom d'\''hôte invalide : %s'
    M_v_used='L'\''ID %s est déjà utilisé.'
    M_v_gw='Une IP statique nécessite une passerelle (var_gw).'
    M_v_mnt='Le dossier de l'\''hôte '\''%s'\'' n'\''existe pas.'
    M_v_mntabs='Le chemin dans le conteneur doit être absolu (ex. /mnt/modeles).'
    M_v_src='var_source_types invalide : %s (valeurs : folder,file,smb,nfs)'
    M_v_stor='Le stockage « %s » n'\''existe pas, est inactif ou n'\''accepte pas les disques de conteneurs (rootdir). Disponibles : %s'
    M_v_tpl='Le stockage « %s » n'\''existe pas, est inactif ou n'\''accepte pas les modèles (vztmpl). Disponibles : %s'
    M_v_free='Le stockage « %s » n'\''a que %s Go libres pour un disque de %s Go. Choisissez un autre stockage (var_storage) ou réduisez var_disk.'
    M_r_def='Paramètres par défaut sur le nœud %s'
    M_r_adv='Paramètres avancés sur le nœud %s'
    M_l_pve='Version PVE :'
    M_l_id='ID du conteneur :'
    M_l_os='Système :'
    M_l_type='Type de conteneur :'
    M_u_unpriv='non privilégié'
    M_u_priv='privilégié'
    M_l_disk='Taille du disque :'
    M_l_stor='Stockage du conteneur :'
    M_l_tpl='Stockage des modèles :'
    M_u_stor='%s (%s, libre %s Go)'
    M_l_cpu='Cœurs CPU :'
    M_l_ram='Mémoire RAM :'
    M_u_ram='%s Mo (swap %s Mo)'
    M_l_net='Réseau :'
    M_u_net='%s%s, IP %s%s'
    M_u_vlan=' (VLAN %s)'
    M_u_via=' via %s'
    M_l_src='Sources proposées :'
    M_u_src='%s (%s)'
    M_u_lok='dossiers locaux autorisés'
    M_u_lhid='dossiers locaux masqués'
    M_l_mount='Dossier monté :'
    M_r_create='Création d'\''un conteneur LXC Stellio avec les paramètres ci-dessus'
    M_ok_stor='Stockage « %s » (%s) validé — libre : %s Go'
    M_ok_tpl='Stockage des modèles « %s » (%s) validé — libre : %s Go'
    M_st_upd='Mise à jour de la liste des modèles Proxmox'
    M_upd_fail='pveam update a échoué (réseau ?) — liste en cache utilisée'
    M_e_tplnf='Modèle Debian 12 introuvable dans la liste Proxmox.'
    M_ok_tplp='Modèle %s déjà présent'
    M_st_tpldl='Téléchargement du modèle %s'
    M_st_create='Création du conteneur LXC %s'
    M_desc='Stellio — gestionnaire de fichiers 3D (installé par stellio-lxc.sh). Mise à jour : pct exec %s -- update-stellio'
    M_st_start='Démarrage du conteneur'
    M_st_net='Attente du réseau du conteneur'
    M_net_fail='Le conteneur n'\''a pas d'\''accès réseau/DNS (IP : %s). Vérifiez le pont %s, le DHCP / l'\''IP statique, la passerelle et le DNS.'
    M_none='aucune'
    M_st_src='Configuration des sources de paquets Debian'
    M_st_base='Installation des paquets de base'
    M_st_user='Préparation de l'\''utilisateur et du script d'\''installation'
    M_st_inst='Installation de Stellio (5 à 15 minutes)'
    M_st_svc='Configuration du service et des types de sources'
    M_st_cons='Configuration de la console du conteneur'
    M_st_ver='Vérification du démarrage de Stellio'
    M_nr='Stellio ne répond pas encore sur le port %s.'
    M_g_nonfree='Activation des sections contrib / non-free'
    M_g_apt='Mise à jour de la liste des paquets'
    M_g_base='Installation de sudo, curl et git'
    M_g_user='Création de l'\''utilisateur %s'
    M_g_dl='Téléchargement du script d'\''installation officiel'
    M_g_svc='Réglage des types de sources : %s'
    M_g_cons='Configuration de la console du conteneur'
    M_b_upd='Mise à jour'
    M_f_up='Stellio répond sur le port %s'
    M_f_done='Terminé avec succès !'
    M_f_nup='Stellio ne répond pas encore (le premier lancement vérifie les modules, patientez 1 à 2 minutes)'
    M_f_logs='Journaux : pct exec %s -- journalctl -u stellio -n 80 --no-pager'
    M_f_made='Le conteneur Stellio a été créé avec succès !'
    M_f_acc='Stellio est accessible à l'\''adresse : '
    M_f_ct='Conteneur ........ %s (%s)  —  console : pct console %s (connexion automatique)'
    M_f_pw='Mot de passe root  %s'
    M_f_upd='Mettre à jour .... pct exec %s -- update-stellio'
    M_f_log='Journaux ......... pct exec %s -- journalctl -u stellio -f'
    M_f_mnt1='Dossier monté : ajoutez '\''%s'\'' comme « Dossier local » dans Stellio (Paramètres → Sources).'
    M_f_mnt2='Conteneur non privilégié : l'\''utilisateur '\''stellio'\'' (uid 1000) correspond à l'\''uid 101000 de l'\''hôte.'
    M_f_mnt3='Si le dossier n'\''est pas lisible/modifiable : chown -R 101000:101000 '\''%s'\'' (ou chmod o+rwX).'
    M_f_src1='Sources : seules les sources réseau SMB / NFS sont proposées dans Stellio (dossiers locaux masqués).'
    M_f_src2='Pour autoriser aussi un dossier monté de l'\''hôte : pct set %s -mp0 /chemin/hote,mp=/mnt/modeles, puis dans le'
    M_f_src3='conteneur éditez /etc/systemd/system/stellio.service.d/sources.conf (STELLIO_ALLOWED_SOURCE_TYPES=folder,smb,nfs)'
    M_f_src4='et lancez : systemctl daemon-reload && systemctl restart stellio'
}
lang_en() {
    M_sub='3D file manager — LXC installation for Proxmox VE'
    M_cancelled='Cancelled.'
    M_e_root='This script must be run as root on the Proxmox host.'
    M_e_nopve='Proxmox VE not found: run this script on the Proxmox host (not in a VM or a container).'
    M_e_pvever='Proxmox VE 7 or later is required (%s).'
    M_e_tool='Command '\''%s'\'' not found.'
    M_e_inct='Run this script on the Proxmox host, not from inside a container.'
    M_e_line='Error at line %s: %s'
    M_w_ct1='Container %s was created but the installation is not finished.'
    M_w_ct2='To delete it and start over: pct stop %s; pct destroy %s'
    M_w_ct3='To inspect it: pct enter %s'
    M_w_ct4='Container %s created but installation incomplete. To start over: pct stop %s; pct destroy %s'
    M_last_lines='--- last log lines ---'
    M_full_log='Full log: %s'
    M_m_title='Stellio installation'
    M_m_text='Create a Stellio LXC container:'
    M_m_default='Default settings (recommended)'
    M_m_storage='Default settings + storage choice'
    M_m_adv='Advanced settings (including storage)'
    M_m_cancel='Cancel'
    M_a_title='Advanced settings'
    M_a_ctid='Container ID (CTID)'
    M_a_hn='Hostname'
    M_a_cores='Number of CPU cores'
    M_a_ram='Memory (MB)'
    M_a_disk='Disk size (GB)'
    M_a_bridge='Network bridge'
    M_a_ip='IP address: dhcp, or a static IP with mask (e.g. 192.168.1.50/24)'
    M_a_gw='Gateway (e.g. 192.168.1.1)'
    M_a_vlan='VLAN (leave empty if none)'
    M_a_port='Stellio port'
    M_a_priv_t='Privileged container?'
    M_a_priv_x='An UNPRIVILEGED container is safer (recommended).\nA privileged container makes it easier to access a folder mounted from the host.\n\nCreate a privileged container?'
    M_a_mount='Host folder to mount in the container, as /host/path:/container/path (empty = none)\nE.g. /mnt/pve/nas/models:/mnt/models'
    M_s_none='No active storage handles the content type '\''%s'\''.'
    M_s_menu='Choose a storage (%s):'
    M_s_item='type %s, %s GB free'
    M_s_t_ct='Container storage (LXC disk)'
    M_s_t_tpl='Template storage'
    M_v_ctid='Invalid CTID: %s'
    M_v_cores='Invalid number of cores: %s'
    M_v_ram='Invalid memory (minimum 1024 MB): %s'
    M_v_swap='Invalid swap: %s'
    M_v_disk='Invalid disk (minimum 4 GB): %s'
    M_v_port='Invalid port: %s'
    M_v_hn='Invalid hostname: %s'
    M_v_used='ID %s is already in use.'
    M_v_gw='A static IP requires a gateway (var_gw).'
    M_v_mnt='The host folder '\''%s'\'' does not exist.'
    M_v_mntabs='The path inside the container must be absolute (e.g. /mnt/models).'
    M_v_src='Invalid var_source_types: %s (values: folder,file,smb,nfs)'
    M_v_stor='Storage '\''%s'\'' does not exist, is inactive or does not accept container disks (rootdir). Available: %s'
    M_v_tpl='Storage '\''%s'\'' does not exist, is inactive or does not accept templates (vztmpl). Available: %s'
    M_v_free='Storage '\''%s'\'' has only %s GB free for a %s GB disk. Choose another storage (var_storage) or reduce var_disk.'
    M_r_def='Default settings on node %s'
    M_r_adv='Advanced settings on node %s'
    M_l_pve='PVE version:'
    M_l_id='Container ID:'
    M_l_os='System:'
    M_l_type='Container type:'
    M_u_unpriv='unprivileged'
    M_u_priv='privileged'
    M_l_disk='Disk size:'
    M_l_stor='Container storage:'
    M_l_tpl='Template storage:'
    M_u_stor='%s (%s, %s GB free)'
    M_l_cpu='CPU cores:'
    M_l_ram='RAM:'
    M_u_ram='%s MB (swap %s MB)'
    M_l_net='Network:'
    M_u_net='%s%s, IP %s%s'
    M_u_vlan=' (VLAN %s)'
    M_u_via=' via %s'
    M_l_src='Offered sources:'
    M_u_src='%s (%s)'
    M_u_lok='local folders allowed'
    M_u_lhid='local folders hidden'
    M_l_mount='Mounted folder:'
    M_r_create='Creating a Stellio LXC container with the settings above'
    M_ok_stor='Storage '\''%s'\'' (%s) validated — free: %s GB'
    M_ok_tpl='Template storage '\''%s'\'' (%s) validated — free: %s GB'
    M_st_upd='Updating the Proxmox template list'
    M_upd_fail='pveam update failed (network?) — using the cached list'
    M_e_tplnf='Debian 12 template not found in the Proxmox list.'
    M_ok_tplp='Template %s already present'
    M_st_tpldl='Downloading template %s'
    M_st_create='Creating LXC container %s'
    M_desc='Stellio — 3D file manager (installed by stellio-lxc.sh). Update: pct exec %s -- update-stellio'
    M_st_start='Starting the container'
    M_st_net='Waiting for the container network'
    M_net_fail='The container has no network/DNS access (IP: %s). Check bridge %s, DHCP / static IP, gateway and DNS.'
    M_none='none'
    M_st_src='Configuring the Debian package sources'
    M_st_base='Installing base packages'
    M_st_user='Preparing the user and the install script'
    M_st_inst='Installing Stellio (5 to 15 minutes)'
    M_st_svc='Configuring the service and source types'
    M_st_cons='Configuring the container console'
    M_st_ver='Checking that Stellio started'
    M_nr='Stellio is not responding yet on port %s.'
    M_g_nonfree='Enabling the contrib / non-free sections'
    M_g_apt='Updating the package list'
    M_g_base='Installing sudo, curl and git'
    M_g_user='Creating user %s'
    M_g_dl='Downloading the official install script'
    M_g_svc='Setting the source types: %s'
    M_g_cons='Configuring the container console'
    M_b_upd='Update'
    M_f_up='Stellio is responding on port %s'
    M_f_done='Completed successfully!'
    M_f_nup='Stellio is not responding yet (the first launch checks the modules, wait 1 to 2 minutes)'
    M_f_logs='Logs: pct exec %s -- journalctl -u stellio -n 80 --no-pager'
    M_f_made='The Stellio container was created successfully!'
    M_f_acc='Stellio is available at: '
    M_f_ct='Container ........ %s (%s)  —  console: pct console %s (automatic login)'
    M_f_pw='Root password ..... %s'
    M_f_upd='Update ............ pct exec %s -- update-stellio'
    M_f_log='Logs ............. pct exec %s -- journalctl -u stellio -f'
    M_f_mnt1='Mounted folder: add '\''%s'\'' as a “Local folder” in Stellio (Settings → Sources).'
    M_f_mnt2='Unprivileged container: the '\''stellio'\'' user (uid 1000) maps to uid 101000 on the host.'
    M_f_mnt3='If the folder is not readable/writable: chown -R 101000:101000 '\''%s'\'' (or chmod o+rwX).'
    M_f_src1='Sources: only the SMB / NFS network sources are offered in Stellio (local folders hidden).'
    M_f_src2='To also allow a host folder: pct set %s -mp0 /host/path,mp=/mnt/models, then inside the'
    M_f_src3='container edit /etc/systemd/system/stellio.service.d/sources.conf (STELLIO_ALLOWED_SOURCE_TYPES=folder,smb,nfs)'
    M_f_src4='and run: systemctl daemon-reload && systemctl restart stellio'
}
lang_de() {
    M_sub='3D-Dateimanager — LXC-Installation für Proxmox VE'
    M_cancelled='Abgebrochen.'
    M_e_root='Dieses Skript muss als root auf dem Proxmox-Host ausgeführt werden.'
    M_e_nopve='Proxmox VE nicht gefunden: Führen Sie das Skript auf dem Proxmox-Host aus (nicht in einer VM oder einem Container).'
    M_e_pvever='Proxmox VE 7 oder höher ist erforderlich (%s).'
    M_e_tool='Befehl '\''%s'\'' nicht gefunden.'
    M_e_inct='Führen Sie das Skript auf dem Proxmox-Host aus, nicht in einem Container.'
    M_e_line='Fehler in Zeile %s: %s'
    M_w_ct1='Container %s wurde erstellt, die Installation ist aber nicht abgeschlossen.'
    M_w_ct2='Zum Löschen und Neustarten: pct stop %s; pct destroy %s'
    M_w_ct3='Zum Untersuchen: pct enter %s'
    M_w_ct4='Container %s erstellt, Installation aber unvollständig. Neustart: pct stop %s; pct destroy %s'
    M_last_lines='--- letzte Protokollzeilen ---'
    M_full_log='Vollständiges Protokoll: %s'
    M_m_title='Stellio-Installation'
    M_m_text='Stellio-LXC-Container erstellen:'
    M_m_default='Standardeinstellungen (empfohlen)'
    M_m_storage='Standardeinstellungen + Speicherauswahl'
    M_m_adv='Erweiterte Einstellungen (inkl. Speicher)'
    M_m_cancel='Abbrechen'
    M_a_title='Erweiterte Einstellungen'
    M_a_ctid='Container-ID (CTID)'
    M_a_hn='Hostname'
    M_a_cores='Anzahl CPU-Kerne'
    M_a_ram='Arbeitsspeicher (MB)'
    M_a_disk='Festplattengröße (GB)'
    M_a_bridge='Netzwerk-Bridge'
    M_a_ip='IP-Adresse: dhcp oder statische IP mit Maske (z. B. 192.168.1.50/24)'
    M_a_gw='Gateway (z. B. 192.168.1.1)'
    M_a_vlan='VLAN (leer lassen, wenn keins)'
    M_a_port='Stellio-Port'
    M_a_priv_t='Privilegierter Container?'
    M_a_priv_x='Ein UNPRIVILEGIERTER Container ist sicherer (empfohlen).\nEin privilegierter Container vereinfacht den Zugriff auf einen eingebundenen Host-Ordner.\n\nPrivilegierten Container erstellen?'
    M_a_mount='Host-Ordner zum Einbinden im Container im Format /host/pfad:/container/pfad (leer = keiner)\nz. B. /mnt/pve/nas/modelle:/mnt/modelle'
    M_s_none='Kein aktiver Speicher unterstützt den Inhaltstyp '\''%s'\''.'
    M_s_menu='Speicher wählen (%s):'
    M_s_item='Typ %s, %s GB frei'
    M_s_t_ct='Container-Speicher (LXC-Disk)'
    M_s_t_tpl='Vorlagen-Speicher (Templates)'
    M_v_ctid='Ungültige CTID: %s'
    M_v_cores='Ungültige Kernanzahl: %s'
    M_v_ram='Ungültiger Arbeitsspeicher (mindestens 1024 MB): %s'
    M_v_swap='Ungültiger Swap: %s'
    M_v_disk='Ungültige Festplatte (mindestens 4 GB): %s'
    M_v_port='Ungültiger Port: %s'
    M_v_hn='Ungültiger Hostname: %s'
    M_v_used='Die ID %s wird bereits verwendet.'
    M_v_gw='Eine statische IP benötigt ein Gateway (var_gw).'
    M_v_mnt='Der Host-Ordner '\''%s'\'' existiert nicht.'
    M_v_mntabs='Der Pfad im Container muss absolut sein (z. B. /mnt/modelle).'
    M_v_src='Ungültiger var_source_types: %s (Werte: folder,file,smb,nfs)'
    M_v_stor='Der Speicher '\''%s'\'' existiert nicht, ist inaktiv oder nimmt keine Container-Disks auf (rootdir). Verfügbar: %s'
    M_v_tpl='Der Speicher '\''%s'\'' existiert nicht, ist inaktiv oder nimmt keine Vorlagen auf (vztmpl). Verfügbar: %s'
    M_v_free='Der Speicher '\''%s'\'' hat nur %s GB frei für eine %s-GB-Disk. Wählen Sie einen anderen Speicher (var_storage) oder verringern Sie var_disk.'
    M_r_def='Standardeinstellungen auf Knoten %s'
    M_r_adv='Erweiterte Einstellungen auf Knoten %s'
    M_l_pve='PVE-Version:'
    M_l_id='Container-ID:'
    M_l_os='System:'
    M_l_type='Container-Typ:'
    M_u_unpriv='unprivilegiert'
    M_u_priv='privilegiert'
    M_l_disk='Festplattengröße:'
    M_l_stor='Container-Speicher:'
    M_l_tpl='Vorlagen-Speicher:'
    M_u_stor='%s (%s, %s GB frei)'
    M_l_cpu='CPU-Kerne:'
    M_l_ram='Arbeitsspeicher:'
    M_u_ram='%s MB (Swap %s MB)'
    M_l_net='Netzwerk:'
    M_u_net='%s%s, IP %s%s'
    M_u_vlan=' (VLAN %s)'
    M_u_via=' über %s'
    M_l_src='Angebotene Quellen:'
    M_u_src='%s (%s)'
    M_u_lok='lokale Ordner erlaubt'
    M_u_lhid='lokale Ordner ausgeblendet'
    M_l_mount='Eingebundener Ordner:'
    M_r_create='Erstelle einen Stellio-LXC-Container mit den obigen Einstellungen'
    M_ok_stor='Speicher '\''%s'\'' (%s) geprüft — frei: %s GB'
    M_ok_tpl='Vorlagen-Speicher '\''%s'\'' (%s) geprüft — frei: %s GB'
    M_st_upd='Proxmox-Vorlagenliste wird aktualisiert'
    M_upd_fail='pveam update fehlgeschlagen (Netzwerk?) — zwischengespeicherte Liste wird verwendet'
    M_e_tplnf='Debian-12-Vorlage in der Proxmox-Liste nicht gefunden.'
    M_ok_tplp='Vorlage %s bereits vorhanden'
    M_st_tpldl='Vorlage %s wird heruntergeladen'
    M_st_create='LXC-Container %s wird erstellt'
    M_desc='Stellio — 3D-Dateimanager (installiert von stellio-lxc.sh). Update: pct exec %s -- update-stellio'
    M_st_start='Container wird gestartet'
    M_st_net='Warte auf das Container-Netzwerk'
    M_net_fail='Der Container hat keinen Netzwerk-/DNS-Zugang (IP: %s). Prüfen Sie Bridge %s, DHCP / statische IP, Gateway und DNS.'
    M_none='keine'
    M_st_src='Debian-Paketquellen werden konfiguriert'
    M_st_base='Basispakete werden installiert'
    M_st_user='Benutzer und Installationsskript werden vorbereitet'
    M_st_inst='Stellio wird installiert (5 bis 15 Minuten)'
    M_st_svc='Dienst und Quellentypen werden konfiguriert'
    M_st_cons='Container-Konsole wird konfiguriert'
    M_st_ver='Start von Stellio wird geprüft'
    M_nr='Stellio antwortet auf Port %s noch nicht.'
    M_g_nonfree='contrib-/non-free-Bereiche werden aktiviert'
    M_g_apt='Paketliste wird aktualisiert'
    M_g_base='sudo, curl und git werden installiert'
    M_g_user='Benutzer %s wird erstellt'
    M_g_dl='Offizielles Installationsskript wird heruntergeladen'
    M_g_svc='Quellentypen werden gesetzt: %s'
    M_g_cons='Container-Konsole wird konfiguriert'
    M_b_upd='Aktualisieren'
    M_f_up='Stellio antwortet auf Port %s'
    M_f_done='Erfolgreich abgeschlossen!'
    M_f_nup='Stellio antwortet noch nicht (der erste Start prüft die Module, warten Sie 1 bis 2 Minuten)'
    M_f_logs='Protokolle: pct exec %s -- journalctl -u stellio -n 80 --no-pager'
    M_f_made='Der Stellio-Container wurde erfolgreich erstellt!'
    M_f_acc='Stellio ist erreichbar unter: '
    M_f_ct='Container ........ %s (%s)  —  Konsole: pct console %s (automatische Anmeldung)'
    M_f_pw='Root-Passwort ..... %s'
    M_f_upd='Aktualisieren .... pct exec %s -- update-stellio'
    M_f_log='Protokolle ....... pct exec %s -- journalctl -u stellio -f'
    M_f_mnt1='Eingebundener Ordner: Fügen Sie '\''%s'\'' in Stellio als „Lokaler Ordner“ hinzu (Einstellungen → Quellen).'
    M_f_mnt2='Unprivilegierter Container: Der Benutzer '\''stellio'\'' (uid 1000) entspricht uid 101000 auf dem Host.'
    M_f_mnt3='Wenn der Ordner nicht les-/schreibbar ist: chown -R 101000:101000 '\''%s'\'' (oder chmod o+rwX).'
    M_f_src1='Quellen: In Stellio werden nur die Netzwerkquellen SMB / NFS angeboten (lokale Ordner ausgeblendet).'
    M_f_src2='Um zusätzlich einen Host-Ordner zu erlauben: pct set %s -mp0 /host/pfad,mp=/mnt/modelle, dann im'
    M_f_src3='Container bearbeiten Sie /etc/systemd/system/stellio.service.d/sources.conf (STELLIO_ALLOWED_SOURCE_TYPES=folder,smb,nfs)'
    M_f_src4='und führen Sie aus: systemctl daemon-reload && systemctl restart stellio'
}
lang_es() {
    M_sub='Gestor de archivos 3D — instalación LXC para Proxmox VE'
    M_cancelled='Cancelado.'
    M_e_root='Este script debe ejecutarse como root en el host Proxmox.'
    M_e_nopve='No se encontró Proxmox VE: ejecute este script en el host Proxmox (no en una VM ni en un contenedor).'
    M_e_pvever='Se requiere Proxmox VE 7 o superior (%s).'
    M_e_tool='No se encontró el comando '\''%s'\''.'
    M_e_inct='Ejecute este script en el host Proxmox, no desde un contenedor.'
    M_e_line='Error en la línea %s: %s'
    M_w_ct1='El contenedor %s se creó pero la instalación no ha terminado.'
    M_w_ct2='Para eliminarlo y empezar de nuevo: pct stop %s; pct destroy %s'
    M_w_ct3='Para inspeccionarlo: pct enter %s'
    M_w_ct4='Contenedor %s creado pero instalación incompleta. Para reiniciar: pct stop %s; pct destroy %s'
    M_last_lines='--- últimas líneas del registro ---'
    M_full_log='Registro completo: %s'
    M_m_title='Instalación de Stellio'
    M_m_text='Crear un contenedor LXC de Stellio:'
    M_m_default='Ajustes por defecto (recomendado)'
    M_m_storage='Ajustes por defecto + elección del almacenamiento'
    M_m_adv='Ajustes avanzados (incluido el almacenamiento)'
    M_m_cancel='Cancelar'
    M_a_title='Ajustes avanzados'
    M_a_ctid='ID del contenedor (CTID)'
    M_a_hn='Nombre de host'
    M_a_cores='Número de núcleos de CPU'
    M_a_ram='Memoria (MB)'
    M_a_disk='Tamaño del disco (GB)'
    M_a_bridge='Puente de red (bridge)'
    M_a_ip='Dirección IP: dhcp, o una IP estática con máscara (p. ej. 192.168.1.50/24)'
    M_a_gw='Puerta de enlace (p. ej. 192.168.1.1)'
    M_a_vlan='VLAN (dejar vacío si no hay)'
    M_a_port='Puerto de Stellio'
    M_a_priv_t='¿Contenedor privilegiado?'
    M_a_priv_x='Un contenedor NO privilegiado es más seguro (recomendado).\nUn contenedor privilegiado facilita el acceso a una carpeta montada del host.\n\n¿Crear un contenedor privilegiado?'
    M_a_mount='Carpeta del host a montar en el contenedor, formato /ruta/host:/ruta/contenedor (vacío = ninguna)\nEj. /mnt/pve/nas/modelos:/mnt/modelos'
    M_s_none='Ningún almacenamiento activo admite el contenido '\''%s'\''.'
    M_s_menu='Elija un almacenamiento (%s):'
    M_s_item='tipo %s, %s GB libres'
    M_s_t_ct='Almacenamiento del contenedor (disco del LXC)'
    M_s_t_tpl='Almacenamiento de plantillas'
    M_v_ctid='CTID no válido: %s'
    M_v_cores='Número de núcleos no válido: %s'
    M_v_ram='Memoria no válida (mínimo 1024 MB): %s'
    M_v_swap='Swap no válido: %s'
    M_v_disk='Disco no válido (mínimo 4 GB): %s'
    M_v_port='Puerto no válido: %s'
    M_v_hn='Nombre de host no válido: %s'
    M_v_used='El ID %s ya está en uso.'
    M_v_gw='Una IP estática requiere una puerta de enlace (var_gw).'
    M_v_mnt='La carpeta del host '\''%s'\'' no existe.'
    M_v_mntabs='La ruta dentro del contenedor debe ser absoluta (p. ej. /mnt/modelos).'
    M_v_src='var_source_types no válido: %s (valores: folder,file,smb,nfs)'
    M_v_stor='El almacenamiento '\''%s'\'' no existe, está inactivo o no admite discos de contenedor (rootdir). Disponibles: %s'
    M_v_tpl='El almacenamiento '\''%s'\'' no existe, está inactivo o no admite plantillas (vztmpl). Disponibles: %s'
    M_v_free='El almacenamiento '\''%s'\'' solo tiene %s GB libres para un disco de %s GB. Elija otro almacenamiento (var_storage) o reduzca var_disk.'
    M_r_def='Ajustes por defecto en el nodo %s'
    M_r_adv='Ajustes avanzados en el nodo %s'
    M_l_pve='Versión de PVE:'
    M_l_id='ID del contenedor:'
    M_l_os='Sistema:'
    M_l_type='Tipo de contenedor:'
    M_u_unpriv='no privilegiado'
    M_u_priv='privilegiado'
    M_l_disk='Tamaño del disco:'
    M_l_stor='Almacenamiento del contenedor:'
    M_l_tpl='Almacenamiento de plantillas:'
    M_u_stor='%s (%s, %s GB libres)'
    M_l_cpu='Núcleos de CPU:'
    M_l_ram='Memoria RAM:'
    M_u_ram='%s MB (swap %s MB)'
    M_l_net='Red:'
    M_u_net='%s%s, IP %s%s'
    M_u_vlan=' (VLAN %s)'
    M_u_via=' vía %s'
    M_l_src='Fuentes ofrecidas:'
    M_u_src='%s (%s)'
    M_u_lok='carpetas locales permitidas'
    M_u_lhid='carpetas locales ocultas'
    M_l_mount='Carpeta montada:'
    M_r_create='Creando un contenedor LXC de Stellio con los ajustes anteriores'
    M_ok_stor='Almacenamiento '\''%s'\'' (%s) validado — libre: %s GB'
    M_ok_tpl='Almacenamiento de plantillas '\''%s'\'' (%s) validado — libre: %s GB'
    M_st_upd='Actualizando la lista de plantillas de Proxmox'
    M_upd_fail='pveam update falló (¿red?) — se usa la lista en caché'
    M_e_tplnf='No se encontró la plantilla Debian 12 en la lista de Proxmox.'
    M_ok_tplp='Plantilla %s ya presente'
    M_st_tpldl='Descargando la plantilla %s'
    M_st_create='Creando el contenedor LXC %s'
    M_desc='Stellio — gestor de archivos 3D (instalado por stellio-lxc.sh). Actualizar: pct exec %s -- update-stellio'
    M_st_start='Iniciando el contenedor'
    M_st_net='Esperando la red del contenedor'
    M_net_fail='El contenedor no tiene acceso a red/DNS (IP: %s). Compruebe el puente %s, DHCP / IP estática, puerta de enlace y DNS.'
    M_none='ninguna'
    M_st_src='Configurando las fuentes de paquetes de Debian'
    M_st_base='Instalando los paquetes base'
    M_st_user='Preparando el usuario y el script de instalación'
    M_st_inst='Instalando Stellio (5 a 15 minutos)'
    M_st_svc='Configurando el servicio y los tipos de fuentes'
    M_st_cons='Configurando la consola del contenedor'
    M_st_ver='Comprobando el arranque de Stellio'
    M_nr='Stellio aún no responde en el puerto %s.'
    M_g_nonfree='Activando las secciones contrib / non-free'
    M_g_apt='Actualizando la lista de paquetes'
    M_g_base='Instalando sudo, curl y git'
    M_g_user='Creando el usuario %s'
    M_g_dl='Descargando el script de instalación oficial'
    M_g_svc='Ajustando los tipos de fuentes: %s'
    M_g_cons='Configurando la consola del contenedor'
    M_b_upd='Actualizar'
    M_f_up='Stellio responde en el puerto %s'
    M_f_done='¡Completado con éxito!'
    M_f_nup='Stellio aún no responde (el primer arranque comprueba los módulos, espere 1 o 2 minutos)'
    M_f_logs='Registros: pct exec %s -- journalctl -u stellio -n 80 --no-pager'
    M_f_made='¡El contenedor de Stellio se creó con éxito!'
    M_f_acc='Stellio está disponible en: '
    M_f_ct='Contenedor ....... %s (%s)  —  consola: pct console %s (inicio de sesión automático)'
    M_f_pw='Contraseña root .. %s'
    M_f_upd='Actualizar ....... pct exec %s -- update-stellio'
    M_f_log='Registros ........ pct exec %s -- journalctl -u stellio -f'
    M_f_mnt1='Carpeta montada: añada '\''%s'\'' como «Carpeta local» en Stellio (Ajustes → Fuentes).'
    M_f_mnt2='Contenedor no privilegiado: el usuario '\''stellio'\'' (uid 1000) corresponde al uid 101000 del host.'
    M_f_mnt3='Si la carpeta no es legible/modificable: chown -R 101000:101000 '\''%s'\'' (o chmod o+rwX).'
    M_f_src1='Fuentes: Stellio solo ofrece las fuentes de red SMB / NFS (carpetas locales ocultas).'
    M_f_src2='Para permitir también una carpeta del host: pct set %s -mp0 /ruta/host,mp=/mnt/modelos, y luego en el'
    M_f_src3='contenedor edite /etc/systemd/system/stellio.service.d/sources.conf (STELLIO_ALLOWED_SOURCE_TYPES=folder,smb,nfs)'
    M_f_src4='y ejecute: systemctl daemon-reload && systemctl restart stellio'
}
lang_pt() {
    M_sub='Gestor de ficheiros 3D — instalação LXC para Proxmox VE'
    M_cancelled='Cancelado.'
    M_e_root='Este script tem de ser executado como root no anfitrião Proxmox.'
    M_e_nopve='Proxmox VE não encontrado: execute este script no anfitrião Proxmox (não numa VM nem num contentor).'
    M_e_pvever='É necessário Proxmox VE 7 ou superior (%s).'
    M_e_tool='Comando '\''%s'\'' não encontrado.'
    M_e_inct='Execute este script no anfitrião Proxmox, não dentro de um contentor.'
    M_e_line='Erro na linha %s: %s'
    M_w_ct1='O contentor %s foi criado mas a instalação não terminou.'
    M_w_ct2='Para o eliminar e recomeçar: pct stop %s; pct destroy %s'
    M_w_ct3='Para o inspecionar: pct enter %s'
    M_w_ct4='Contentor %s criado mas instalação incompleta. Para recomeçar: pct stop %s; pct destroy %s'
    M_last_lines='--- últimas linhas do registo ---'
    M_full_log='Registo completo: %s'
    M_m_title='Instalação do Stellio'
    M_m_text='Criar um contentor LXC do Stellio:'
    M_m_default='Definições por omissão (recomendado)'
    M_m_storage='Definições por omissão + escolha do armazenamento'
    M_m_adv='Definições avançadas (incluindo o armazenamento)'
    M_m_cancel='Cancelar'
    M_a_title='Definições avançadas'
    M_a_ctid='ID do contentor (CTID)'
    M_a_hn='Nome do anfitrião'
    M_a_cores='Número de núcleos de CPU'
    M_a_ram='Memória (MB)'
    M_a_disk='Tamanho do disco (GB)'
    M_a_bridge='Bridge de rede'
    M_a_ip='Endereço IP: dhcp, ou um IP estático com máscara (ex. 192.168.1.50/24)'
    M_a_gw='Gateway (ex. 192.168.1.1)'
    M_a_vlan='VLAN (deixar vazio se não houver)'
    M_a_port='Porta do Stellio'
    M_a_priv_t='Contentor privilegiado?'
    M_a_priv_x='Um contentor NÃO privilegiado é mais seguro (recomendado).\nUm contentor privilegiado facilita o acesso a uma pasta montada do anfitrião.\n\nCriar um contentor privilegiado?'
    M_a_mount='Pasta do anfitrião a montar no contentor, formato /caminho/anfitriao:/caminho/contentor (vazio = nenhuma)\nEx. /mnt/pve/nas/modelos:/mnt/modelos'
    M_s_none='Nenhum armazenamento ativo suporta o conteúdo '\''%s'\''.'
    M_s_menu='Escolha um armazenamento (%s):'
    M_s_item='tipo %s, %s GB livres'
    M_s_t_ct='Armazenamento do contentor (disco do LXC)'
    M_s_t_tpl='Armazenamento de modelos (templates)'
    M_v_ctid='CTID inválido: %s'
    M_v_cores='Número de núcleos inválido: %s'
    M_v_ram='Memória inválida (mínimo 1024 MB): %s'
    M_v_swap='Swap inválido: %s'
    M_v_disk='Disco inválido (mínimo 4 GB): %s'
    M_v_port='Porta inválida: %s'
    M_v_hn='Nome do anfitrião inválido: %s'
    M_v_used='O ID %s já está em uso.'
    M_v_gw='Um IP estático requer um gateway (var_gw).'
    M_v_mnt='A pasta do anfitrião '\''%s'\'' não existe.'
    M_v_mntabs='O caminho dentro do contentor tem de ser absoluto (ex. /mnt/modelos).'
    M_v_src='var_source_types inválido: %s (valores: folder,file,smb,nfs)'
    M_v_stor='O armazenamento '\''%s'\'' não existe, está inativo ou não aceita discos de contentor (rootdir). Disponíveis: %s'
    M_v_tpl='O armazenamento '\''%s'\'' não existe, está inativo ou não aceita modelos (vztmpl). Disponíveis: %s'
    M_v_free='O armazenamento '\''%s'\'' só tem %s GB livres para um disco de %s GB. Escolha outro armazenamento (var_storage) ou reduza var_disk.'
    M_r_def='Definições por omissão no nó %s'
    M_r_adv='Definições avançadas no nó %s'
    M_l_pve='Versão do PVE:'
    M_l_id='ID do contentor:'
    M_l_os='Sistema:'
    M_l_type='Tipo de contentor:'
    M_u_unpriv='não privilegiado'
    M_u_priv='privilegiado'
    M_l_disk='Tamanho do disco:'
    M_l_stor='Armazenamento do contentor:'
    M_l_tpl='Armazenamento de modelos:'
    M_u_stor='%s (%s, %s GB livres)'
    M_l_cpu='Núcleos de CPU:'
    M_l_ram='Memória RAM:'
    M_u_ram='%s MB (swap %s MB)'
    M_l_net='Rede:'
    M_u_net='%s%s, IP %s%s'
    M_u_vlan=' (VLAN %s)'
    M_u_via=' via %s'
    M_l_src='Fontes oferecidas:'
    M_u_src='%s (%s)'
    M_u_lok='pastas locais permitidas'
    M_u_lhid='pastas locais ocultas'
    M_l_mount='Pasta montada:'
    M_r_create='A criar um contentor LXC do Stellio com as definições acima'
    M_ok_stor='Armazenamento '\''%s'\'' (%s) validado — livre: %s GB'
    M_ok_tpl='Armazenamento de modelos '\''%s'\'' (%s) validado — livre: %s GB'
    M_st_upd='A atualizar a lista de modelos do Proxmox'
    M_upd_fail='pveam update falhou (rede?) — a usar a lista em cache'
    M_e_tplnf='Modelo Debian 12 não encontrado na lista do Proxmox.'
    M_ok_tplp='Modelo %s já presente'
    M_st_tpldl='A transferir o modelo %s'
    M_st_create='A criar o contentor LXC %s'
    M_desc='Stellio — gestor de ficheiros 3D (instalado por stellio-lxc.sh). Atualizar: pct exec %s -- update-stellio'
    M_st_start='A iniciar o contentor'
    M_st_net='A aguardar a rede do contentor'
    M_net_fail='O contentor não tem acesso à rede/DNS (IP: %s). Verifique o bridge %s, DHCP / IP estático, gateway e DNS.'
    M_none='nenhum'
    M_st_src='A configurar as fontes de pacotes do Debian'
    M_st_base='A instalar os pacotes base'
    M_st_user='A preparar o utilizador e o script de instalação'
    M_st_inst='A instalar o Stellio (5 a 15 minutos)'
    M_st_svc='A configurar o serviço e os tipos de fontes'
    M_st_cons='A configurar a consola do contentor'
    M_st_ver='A verificar o arranque do Stellio'
    M_nr='O Stellio ainda não responde na porta %s.'
    M_g_nonfree='A ativar as secções contrib / non-free'
    M_g_apt='A atualizar a lista de pacotes'
    M_g_base='A instalar sudo, curl e git'
    M_g_user='A criar o utilizador %s'
    M_g_dl='A transferir o script de instalação oficial'
    M_g_svc='A definir os tipos de fontes: %s'
    M_g_cons='A configurar a consola do contentor'
    M_b_upd='Atualizar'
    M_f_up='O Stellio responde na porta %s'
    M_f_done='Concluído com sucesso!'
    M_f_nup='O Stellio ainda não responde (o primeiro arranque verifica os módulos, aguarde 1 a 2 minutos)'
    M_f_logs='Registos: pct exec %s -- journalctl -u stellio -n 80 --no-pager'
    M_f_made='O contentor do Stellio foi criado com sucesso!'
    M_f_acc='O Stellio está acessível em: '
    M_f_ct='Contentor ........ %s (%s)  —  consola: pct console %s (início de sessão automático)'
    M_f_pw='Palavra-passe root %s'
    M_f_upd='Atualizar ........ pct exec %s -- update-stellio'
    M_f_log='Registos ......... pct exec %s -- journalctl -u stellio -f'
    M_f_mnt1='Pasta montada: adicione '\''%s'\'' como «Pasta local» no Stellio (Definições → Fontes).'
    M_f_mnt2='Contentor não privilegiado: o utilizador '\''stellio'\'' (uid 1000) corresponde ao uid 101000 do anfitrião.'
    M_f_mnt3='Se a pasta não for legível/gravável: chown -R 101000:101000 '\''%s'\'' (ou chmod o+rwX).'
    M_f_src1='Fontes: o Stellio só oferece as fontes de rede SMB / NFS (pastas locais ocultas).'
    M_f_src2='Para permitir também uma pasta do anfitrião: pct set %s -mp0 /caminho/anfitriao,mp=/mnt/modelos, depois no'
    M_f_src3='contentor edite /etc/systemd/system/stellio.service.d/sources.conf (STELLIO_ALLOWED_SOURCE_TYPES=folder,smb,nfs)'
    M_f_src4='e execute: systemctl daemon-reload && systemctl restart stellio'
}
lang_it() {
    M_sub='Gestore di file 3D — installazione LXC per Proxmox VE'
    M_cancelled='Annullato.'
    M_e_root='Questo script deve essere eseguito come root sull'\''host Proxmox.'
    M_e_nopve='Proxmox VE non trovato: eseguite lo script sull'\''host Proxmox (non in una VM né in un container).'
    M_e_pvever='È richiesto Proxmox VE 7 o superiore (%s).'
    M_e_tool='Comando '\''%s'\'' non trovato.'
    M_e_inct='Eseguite lo script sull'\''host Proxmox, non da un container.'
    M_e_line='Errore alla riga %s: %s'
    M_w_ct1='Il container %s è stato creato ma l'\''installazione non è terminata.'
    M_w_ct2='Per eliminarlo e ricominciare: pct stop %s; pct destroy %s'
    M_w_ct3='Per ispezionarlo: pct enter %s'
    M_w_ct4='Container %s creato ma installazione incompleta. Per ricominciare: pct stop %s; pct destroy %s'
    M_last_lines='--- ultime righe del registro ---'
    M_full_log='Registro completo: %s'
    M_m_title='Installazione di Stellio'
    M_m_text='Creare un container LXC di Stellio:'
    M_m_default='Impostazioni predefinite (consigliato)'
    M_m_storage='Impostazioni predefinite + scelta dello storage'
    M_m_adv='Impostazioni avanzate (incluso lo storage)'
    M_m_cancel='Annulla'
    M_a_title='Impostazioni avanzate'
    M_a_ctid='ID del container (CTID)'
    M_a_hn='Nome host'
    M_a_cores='Numero di core CPU'
    M_a_ram='Memoria (MB)'
    M_a_disk='Dimensione del disco (GB)'
    M_a_bridge='Bridge di rete'
    M_a_ip='Indirizzo IP: dhcp, oppure un IP statico con maschera (es. 192.168.1.50/24)'
    M_a_gw='Gateway (es. 192.168.1.1)'
    M_a_vlan='VLAN (lasciare vuoto se assente)'
    M_a_port='Porta di Stellio'
    M_a_priv_t='Container privilegiato?'
    M_a_priv_x='Un container NON privilegiato è più sicuro (consigliato).\nUn container privilegiato semplifica l'\''accesso a una cartella montata dall'\''host.\n\nCreare un container privilegiato?'
    M_a_mount='Cartella dell'\''host da montare nel container, formato /percorso/host:/percorso/container (vuoto = nessuna)\nEs. /mnt/pve/nas/modelli:/mnt/modelli'
    M_s_none='Nessuno storage attivo gestisce il contenuto '\''%s'\''.'
    M_s_menu='Scegliete uno storage (%s):'
    M_s_item='tipo %s, %s GB liberi'
    M_s_t_ct='Storage del container (disco LXC)'
    M_s_t_tpl='Storage dei modelli (template)'
    M_v_ctid='CTID non valido: %s'
    M_v_cores='Numero di core non valido: %s'
    M_v_ram='Memoria non valida (minimo 1024 MB): %s'
    M_v_swap='Swap non valido: %s'
    M_v_disk='Disco non valido (minimo 4 GB): %s'
    M_v_port='Porta non valida: %s'
    M_v_hn='Nome host non valido: %s'
    M_v_used='L'\''ID %s è già in uso.'
    M_v_gw='Un IP statico richiede un gateway (var_gw).'
    M_v_mnt='La cartella dell'\''host '\''%s'\'' non esiste.'
    M_v_mntabs='Il percorso nel container deve essere assoluto (es. /mnt/modelli).'
    M_v_src='var_source_types non valido: %s (valori: folder,file,smb,nfs)'
    M_v_stor='Lo storage '\''%s'\'' non esiste, è inattivo o non accetta dischi di container (rootdir). Disponibili: %s'
    M_v_tpl='Lo storage '\''%s'\'' non esiste, è inattivo o non accetta modelli (vztmpl). Disponibili: %s'
    M_v_free='Lo storage '\''%s'\'' ha solo %s GB liberi per un disco da %s GB. Scegliete un altro storage (var_storage) o riducete var_disk.'
    M_r_def='Impostazioni predefinite sul nodo %s'
    M_r_adv='Impostazioni avanzate sul nodo %s'
    M_l_pve='Versione PVE:'
    M_l_id='ID del container:'
    M_l_os='Sistema:'
    M_l_type='Tipo di container:'
    M_u_unpriv='non privilegiato'
    M_u_priv='privilegiato'
    M_l_disk='Dimensione del disco:'
    M_l_stor='Storage del container:'
    M_l_tpl='Storage dei modelli:'
    M_u_stor='%s (%s, %s GB liberi)'
    M_l_cpu='Core CPU:'
    M_l_ram='Memoria RAM:'
    M_u_ram='%s MB (swap %s MB)'
    M_l_net='Rete:'
    M_u_net='%s%s, IP %s%s'
    M_u_vlan=' (VLAN %s)'
    M_u_via=' via %s'
    M_l_src='Sorgenti proposte:'
    M_u_src='%s (%s)'
    M_u_lok='cartelle locali consentite'
    M_u_lhid='cartelle locali nascoste'
    M_l_mount='Cartella montata:'
    M_r_create='Creazione di un container LXC di Stellio con le impostazioni sopra'
    M_ok_stor='Storage '\''%s'\'' (%s) convalidato — libero: %s GB'
    M_ok_tpl='Storage dei modelli '\''%s'\'' (%s) convalidato — libero: %s GB'
    M_st_upd='Aggiornamento dell'\''elenco dei modelli Proxmox'
    M_upd_fail='pveam update non riuscito (rete?) — uso l'\''elenco in cache'
    M_e_tplnf='Modello Debian 12 non trovato nell'\''elenco Proxmox.'
    M_ok_tplp='Modello %s già presente'
    M_st_tpldl='Download del modello %s'
    M_st_create='Creazione del container LXC %s'
    M_desc='Stellio — gestore di file 3D (installato da stellio-lxc.sh). Aggiornamento: pct exec %s -- update-stellio'
    M_st_start='Avvio del container'
    M_st_net='Attesa della rete del container'
    M_net_fail='Il container non ha accesso a rete/DNS (IP: %s). Controllate il bridge %s, DHCP / IP statico, gateway e DNS.'
    M_none='nessuno'
    M_st_src='Configurazione delle sorgenti dei pacchetti Debian'
    M_st_base='Installazione dei pacchetti di base'
    M_st_user='Preparazione dell'\''utente e dello script di installazione'
    M_st_inst='Installazione di Stellio (da 5 a 15 minuti)'
    M_st_svc='Configurazione del servizio e dei tipi di sorgente'
    M_st_cons='Configurazione della console del container'
    M_st_ver='Verifica dell'\''avvio di Stellio'
    M_nr='Stellio non risponde ancora sulla porta %s.'
    M_g_nonfree='Attivazione delle sezioni contrib / non-free'
    M_g_apt='Aggiornamento dell'\''elenco dei pacchetti'
    M_g_base='Installazione di sudo, curl e git'
    M_g_user='Creazione dell'\''utente %s'
    M_g_dl='Download dello script di installazione ufficiale'
    M_g_svc='Impostazione dei tipi di sorgente: %s'
    M_g_cons='Configurazione della console del container'
    M_b_upd='Aggiornare'
    M_f_up='Stellio risponde sulla porta %s'
    M_f_done='Completato con successo!'
    M_f_nup='Stellio non risponde ancora (il primo avvio controlla i moduli, attendete 1-2 minuti)'
    M_f_logs='Log: pct exec %s -- journalctl -u stellio -n 80 --no-pager'
    M_f_made='Il container Stellio è stato creato con successo!'
    M_f_acc='Stellio è raggiungibile all'\''indirizzo: '
    M_f_ct='Container ........ %s (%s)  —  console: pct console %s (accesso automatico)'
    M_f_pw='Password root .... %s'
    M_f_upd='Aggiornare ....... pct exec %s -- update-stellio'
    M_f_log='Log .............. pct exec %s -- journalctl -u stellio -f'
    M_f_mnt1='Cartella montata: aggiungete '\''%s'\'' come «Cartella locale» in Stellio (Impostazioni → Sorgenti).'
    M_f_mnt2='Container non privilegiato: l'\''utente '\''stellio'\'' (uid 1000) corrisponde all'\''uid 101000 dell'\''host.'
    M_f_mnt3='Se la cartella non è leggibile/scrivibile: chown -R 101000:101000 '\''%s'\'' (o chmod o+rwX).'
    M_f_src1='Sorgenti: Stellio propone solo le sorgenti di rete SMB / NFS (cartelle locali nascoste).'
    M_f_src2='Per consentire anche una cartella dell'\''host: pct set %s -mp0 /percorso/host,mp=/mnt/modelli, poi nel'
    M_f_src3='container modificate /etc/systemd/system/stellio.service.d/sources.conf (STELLIO_ALLOWED_SOURCE_TYPES=folder,smb,nfs)'
    M_f_src4='ed eseguite: systemctl daemon-reload && systemctl restart stellio'
}
lang_zh() {
    M_sub='3D 文件管理器 — Proxmox VE 的 LXC 安装'
    M_cancelled='已取消。'
    M_e_root='必须在 Proxmox 主机上以 root 身份运行此脚本。'
    M_e_nopve='未找到 Proxmox VE：请在 Proxmox 主机上运行此脚本（不要在虚拟机或容器中）。'
    M_e_pvever='需要 Proxmox VE 7 或更高版本（%s）。'
    M_e_tool='未找到命令“%s”。'
    M_e_inct='请在 Proxmox 主机上运行此脚本，而不是在容器内。'
    M_e_line='第 %s 行出错：%s'
    M_w_ct1='容器 %s 已创建，但安装尚未完成。'
    M_w_ct2='删除并重新开始：pct stop %s; pct destroy %s'
    M_w_ct3='查看容器：pct enter %s'
    M_w_ct4='容器 %s 已创建但安装不完整。重新开始：pct stop %s; pct destroy %s'
    M_last_lines='--- 日志最后几行 ---'
    M_full_log='完整日志：%s'
    M_m_title='安装 Stellio'
    M_m_text='创建 Stellio LXC 容器：'
    M_m_default='默认设置（推荐）'
    M_m_storage='默认设置 + 选择存储'
    M_m_adv='高级设置（含存储）'
    M_m_cancel='取消'
    M_a_title='高级设置'
    M_a_ctid='容器 ID（CTID）'
    M_a_hn='主机名'
    M_a_cores='CPU 核心数'
    M_a_ram='内存（MB）'
    M_a_disk='磁盘大小（GB）'
    M_a_bridge='网桥（bridge）'
    M_a_ip='IP 地址：dhcp，或带掩码的静态 IP（如 192.168.1.50/24）'
    M_a_gw='网关（如 192.168.1.1）'
    M_a_vlan='VLAN（没有则留空）'
    M_a_port='Stellio 端口'
    M_a_priv_t='特权容器？'
    M_a_priv_x='非特权容器更安全（推荐）。\n特权容器更便于访问挂载的主机文件夹。\n\n要创建特权容器吗？'
    M_a_mount='要挂载到容器的主机文件夹，格式 /主机路径:/容器路径（留空 = 不挂载）\n例如 /mnt/pve/nas/models:/mnt/models'
    M_s_none='没有任何活动存储支持内容类型“%s”。'
    M_s_menu='请选择存储（%s）：'
    M_s_item='类型 %s，剩余 %s GB'
    M_s_t_ct='容器存储（LXC 磁盘）'
    M_s_t_tpl='模板存储'
    M_v_ctid='CTID 无效：%s'
    M_v_cores='核心数无效：%s'
    M_v_ram='内存无效（至少 1024 MB）：%s'
    M_v_swap='交换空间无效：%s'
    M_v_disk='磁盘无效（至少 4 GB）：%s'
    M_v_port='端口无效：%s'
    M_v_hn='主机名无效：%s'
    M_v_used='ID %s 已被使用。'
    M_v_gw='静态 IP 需要网关（var_gw）。'
    M_v_mnt='主机文件夹“%s”不存在。'
    M_v_mntabs='容器内的路径必须是绝对路径（如 /mnt/models）。'
    M_v_src='var_source_types 无效：%s（可选值：folder,file,smb,nfs）'
    M_v_stor='存储“%s”不存在、未激活或不支持容器磁盘（rootdir）。可用：%s'
    M_v_tpl='存储“%s”不存在、未激活或不支持模板（vztmpl）。可用：%s'
    M_v_free='存储“%s”仅剩 %s GB，不足以创建 %s GB 的磁盘。请选择其他存储（var_storage）或减小 var_disk。'
    M_r_def='节点 %s 上的默认设置'
    M_r_adv='节点 %s 上的高级设置'
    M_l_pve='PVE 版本：'
    M_l_id='容器 ID：'
    M_l_os='系统：'
    M_l_type='容器类型：'
    M_u_unpriv='非特权'
    M_u_priv='特权'
    M_l_disk='磁盘大小：'
    M_l_stor='容器存储：'
    M_l_tpl='模板存储：'
    M_u_stor='%s（%s，剩余 %s GB）'
    M_l_cpu='CPU 核心：'
    M_l_ram='内存：'
    M_u_ram='%s MB（交换 %s MB）'
    M_l_net='网络：'
    M_u_net='%s%s，IP %s%s'
    M_u_vlan='（VLAN %s）'
    M_u_via=' 经由 %s'
    M_l_src='提供的来源：'
    M_u_src='%s（%s）'
    M_u_lok='允许本地文件夹'
    M_u_lhid='隐藏本地文件夹'
    M_l_mount='已挂载文件夹：'
    M_r_create='使用以上设置创建 Stellio LXC 容器'
    M_ok_stor='存储“%s”（%s）已验证 — 剩余：%s GB'
    M_ok_tpl='模板存储“%s”（%s）已验证 — 剩余：%s GB'
    M_st_upd='正在更新 Proxmox 模板列表'
    M_upd_fail='pveam update 失败（网络？）— 使用缓存列表'
    M_e_tplnf='在 Proxmox 列表中未找到 Debian 12 模板。'
    M_ok_tplp='模板 %s 已存在'
    M_st_tpldl='正在下载模板 %s'
    M_st_create='正在创建 LXC 容器 %s'
    M_desc='Stellio — 3D 文件管理器（由 stellio-lxc.sh 安装）。更新：pct exec %s -- update-stellio'
    M_st_start='正在启动容器'
    M_st_net='等待容器网络'
    M_net_fail='容器无法访问网络/DNS（IP：%s）。请检查网桥 %s、DHCP / 静态 IP、网关和 DNS。'
    M_none='无'
    M_st_src='正在配置 Debian 软件源'
    M_st_base='正在安装基础软件包'
    M_st_user='正在准备用户和安装脚本'
    M_st_inst='正在安装 Stellio（5 到 15 分钟）'
    M_st_svc='正在配置服务和来源类型'
    M_st_cons='正在配置容器控制台'
    M_st_ver='正在检查 Stellio 是否启动'
    M_nr='Stellio 尚未在端口 %s 上响应。'
    M_g_nonfree='启用 contrib / non-free 软件源'
    M_g_apt='更新软件包列表'
    M_g_base='安装 sudo、curl 和 git'
    M_g_user='创建用户 %s'
    M_g_dl='下载官方安装脚本'
    M_g_svc='设置来源类型：%s'
    M_g_cons='配置容器控制台'
    M_b_upd='更新'
    M_f_up='Stellio 已在端口 %s 上响应'
    M_f_done='已成功完成！'
    M_f_nup='Stellio 尚未响应（首次启动会检查模块，请等待 1 到 2 分钟）'
    M_f_logs='日志：pct exec %s -- journalctl -u stellio -n 80 --no-pager'
    M_f_made='Stellio 容器创建成功！'
    M_f_acc='Stellio 访问地址：'
    M_f_ct='容器 ............ %s (%s)  —  控制台：pct console %s（自动登录）'
    M_f_pw='root 密码 ......... %s'
    M_f_upd='更新 ............. pct exec %s -- update-stellio'
    M_f_log='日志 ............. pct exec %s -- journalctl -u stellio -f'
    M_f_mnt1='已挂载文件夹：在 Stellio 中将“%s”添加为“本地文件夹”（设置 → 来源）。'
    M_f_mnt2='非特权容器：用户“stellio”（uid 1000）对应主机的 uid 101000。'
    M_f_mnt3='如果文件夹不可读/写：chown -R 101000:101000 '\''%s'\''（或 chmod o+rwX）。'
    M_f_src1='来源：Stellio 仅提供 SMB / NFS 网络来源（隐藏本地文件夹）。'
    M_f_src2='如需同时允许主机文件夹：pct set %s -mp0 /主机路径,mp=/mnt/models，然后在'
    M_f_src3='容器中编辑 /etc/systemd/system/stellio.service.d/sources.conf（STELLIO_ALLOWED_SOURCE_TYPES=folder,smb,nfs）'
    M_f_src4='然后运行：systemctl daemon-reload && systemctl restart stellio'
}
lang_ja() {
    M_sub='3Dファイルマネージャー — Proxmox VE 用 LXC インストール'
    M_cancelled='キャンセルしました。'
    M_e_root='このスクリプトは Proxmox ホスト上で root として実行してください。'
    M_e_nopve='Proxmox VE が見つかりません。このスクリプトは Proxmox ホスト上で実行してください（VM やコンテナ内ではなく）。'
    M_e_pvever='Proxmox VE 7 以降が必要です（%s）。'
    M_e_tool='コマンド '\''%s'\'' が見つかりません。'
    M_e_inct='このスクリプトはコンテナ内ではなく、Proxmox ホスト上で実行してください。'
    M_e_line='%s 行目でエラー：%s'
    M_w_ct1='コンテナ %s は作成されましたが、インストールが完了していません。'
    M_w_ct2='削除してやり直すには：pct stop %s; pct destroy %s'
    M_w_ct3='調査するには：pct enter %s'
    M_w_ct4='コンテナ %s は作成されましたが、インストールが不完全です。やり直すには：pct stop %s; pct destroy %s'
    M_last_lines='--- ログの最後の行 ---'
    M_full_log='完全なログ：%s'
    M_m_title='Stellio のインストール'
    M_m_text='Stellio の LXC コンテナを作成：'
    M_m_default='デフォルト設定（推奨）'
    M_m_storage='デフォルト設定＋ストレージ選択'
    M_m_adv='詳細設定（ストレージを含む）'
    M_m_cancel='キャンセル'
    M_a_title='詳細設定'
    M_a_ctid='コンテナ ID（CTID）'
    M_a_hn='ホスト名'
    M_a_cores='CPU コア数'
    M_a_ram='メモリ（MB）'
    M_a_disk='ディスクサイズ（GB）'
    M_a_bridge='ネットワークブリッジ'
    M_a_ip='IP アドレス：dhcp、またはマスク付きの固定 IP（例：192.168.1.50/24）'
    M_a_gw='ゲートウェイ（例：192.168.1.1）'
    M_a_vlan='VLAN（なければ空欄）'
    M_a_port='Stellio のポート'
    M_a_priv_t='特権コンテナにしますか？'
    M_a_priv_x='非特権コンテナの方が安全です（推奨）。\n特権コンテナはホストのマウントフォルダーへのアクセスが容易になります。\n\n特権コンテナを作成しますか？'
    M_a_mount='コンテナにマウントするホストのフォルダー（形式：/ホストのパス:/コンテナのパス、空欄＝なし）\n例：/mnt/pve/nas/models:/mnt/models'
    M_s_none='コンテンツ '\''%s'\'' を扱える有効なストレージがありません。'
    M_s_menu='ストレージを選択（%s）：'
    M_s_item='種類 %s、空き %s GB'
    M_s_t_ct='コンテナのストレージ（LXC ディスク）'
    M_s_t_tpl='テンプレートのストレージ'
    M_v_ctid='CTID が無効です：%s'
    M_v_cores='コア数が無効です：%s'
    M_v_ram='メモリが無効です（最小 1024 MB）：%s'
    M_v_swap='スワップが無効です：%s'
    M_v_disk='ディスクが無効です（最小 4 GB）：%s'
    M_v_port='ポートが無効です：%s'
    M_v_hn='ホスト名が無効です：%s'
    M_v_used='ID %s は既に使われています。'
    M_v_gw='固定 IP にはゲートウェイ（var_gw）が必要です。'
    M_v_mnt='ホストのフォルダー '\''%s'\'' が存在しません。'
    M_v_mntabs='コンテナ内のパスは絶対パスにしてください（例：/mnt/models）。'
    M_v_src='var_source_types が無効です：%s（値：folder,file,smb,nfs）'
    M_v_stor='ストレージ '\''%s'\'' が存在しない、無効、またはコンテナディスク（rootdir）に対応していません。利用可能：%s'
    M_v_tpl='ストレージ '\''%s'\'' が存在しない、無効、またはテンプレート（vztmpl）に対応していません。利用可能：%s'
    M_v_free='ストレージ '\''%s'\'' の空きは %s GB しかなく、%s GB のディスクには不足です。別のストレージ（var_storage）を選ぶか var_disk を小さくしてください。'
    M_r_def='ノード %s のデフォルト設定'
    M_r_adv='ノード %s の詳細設定'
    M_l_pve='PVE バージョン：'
    M_l_id='コンテナ ID：'
    M_l_os='システム：'
    M_l_type='コンテナの種類：'
    M_u_unpriv='非特権'
    M_u_priv='特権'
    M_l_disk='ディスクサイズ：'
    M_l_stor='コンテナのストレージ：'
    M_l_tpl='テンプレートのストレージ：'
    M_u_stor='%s（%s、空き %s GB）'
    M_l_cpu='CPU コア：'
    M_l_ram='メモリ：'
    M_u_ram='%s MB（スワップ %s MB）'
    M_l_net='ネットワーク：'
    M_u_net='%s%s、IP %s%s'
    M_u_vlan=' (VLAN %s)'
    M_u_via=' 経由 %s'
    M_l_src='提供するソース：'
    M_u_src='%s（%s）'
    M_u_lok='ローカルフォルダーを許可'
    M_u_lhid='ローカルフォルダーは非表示'
    M_l_mount='マウント済みフォルダー：'
    M_r_create='上記の設定で Stellio の LXC コンテナを作成します'
    M_ok_stor='ストレージ '\''%s'\''（%s）を確認 — 空き：%s GB'
    M_ok_tpl='テンプレートのストレージ '\''%s'\''（%s）を確認 — 空き：%s GB'
    M_st_upd='Proxmox のテンプレート一覧を更新中'
    M_upd_fail='pveam update に失敗しました（ネットワーク？）— キャッシュの一覧を使用します'
    M_e_tplnf='Proxmox の一覧に Debian 12 のテンプレートが見つかりません。'
    M_ok_tplp='テンプレート %s は既にあります'
    M_st_tpldl='テンプレート %s をダウンロード中'
    M_st_create='LXC コンテナ %s を作成中'
    M_desc='Stellio — 3Dファイルマネージャー（stellio-lxc.sh でインストール）。更新：pct exec %s -- update-stellio'
    M_st_start='コンテナを起動中'
    M_st_net='コンテナのネットワークを待機中'
    M_net_fail='コンテナにネットワーク/DNS アクセスがありません（IP：%s）。ブリッジ %s、DHCP／固定 IP、ゲートウェイ、DNS を確認してください。'
    M_none='なし'
    M_st_src='Debian のパッケージソースを設定中'
    M_st_base='基本パッケージをインストール中'
    M_st_user='ユーザーとインストールスクリプトを準備中'
    M_st_inst='Stellio をインストール中（5〜15分）'
    M_st_svc='サービスとソースの種類を設定中'
    M_st_cons='コンテナのコンソールを設定中'
    M_st_ver='Stellio の起動を確認中'
    M_nr='Stellio はポート %s でまだ応答していません。'
    M_g_nonfree='contrib / non-free セクションを有効化'
    M_g_apt='パッケージ一覧を更新'
    M_g_base='sudo・curl・git をインストール'
    M_g_user='ユーザー %s を作成'
    M_g_dl='公式インストールスクリプトをダウンロード'
    M_g_svc='ソースの種類を設定：%s'
    M_g_cons='コンテナのコンソールを設定'
    M_b_upd='更新'
    M_f_up='Stellio はポート %s で応答しています'
    M_f_done='正常に完了しました！'
    M_f_nup='Stellio はまだ応答していません（初回起動はモジュールを確認します。1〜2分お待ちください）'
    M_f_logs='ログ：pct exec %s -- journalctl -u stellio -n 80 --no-pager'
    M_f_made='Stellio コンテナを作成しました！'
    M_f_acc='Stellio のアドレス：'
    M_f_ct='コンテナ ......... %s (%s)  —  コンソール：pct console %s（自動ログイン）'
    M_f_pw='root パスワード ... %s'
    M_f_upd='更新 ............. pct exec %s -- update-stellio'
    M_f_log='ログ ............. pct exec %s -- journalctl -u stellio -f'
    M_f_mnt1='マウントしたフォルダー：Stellio（設定 → ソース）で '\''%s'\'' を「ローカルフォルダー」として追加してください。'
    M_f_mnt2='非特権コンテナ：ユーザー '\''stellio'\''（uid 1000）はホストの uid 101000 に対応します。'
    M_f_mnt3='フォルダーが読み書きできない場合：chown -R 101000:101000 '\''%s'\''（または chmod o+rwX）。'
    M_f_src1='ソース：Stellio では SMB / NFS のネットワークソースのみ提供されます（ローカルフォルダーは非表示）。'
    M_f_src2='主機のフォルダーも許可するには：pct set %s -mp0 /ホストのパス,mp=/mnt/models を実行し、'
    M_f_src3='コンテナ内で /etc/systemd/system/stellio.service.d/sources.conf を編集（STELLIO_ALLOWED_SOURCE_TYPES=folder,smb,nfs）'
    M_f_src4='その後、systemctl daemon-reload && systemctl restart stellio を実行してください。'
}

LANG_SEL="$(detect_lang)"
lang_en
[ "$LANG_SEL" = "en" ] || "lang_${LANG_SEL}"

t() {  # t <clé> [arguments...]  -> texte traduit (printf)
    local k="M_$1"; shift
    # shellcheck disable=SC2059
    printf -- "${!k:-$k}" "$@"
}


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
    msg_error "$(t e_line "$line" "$cmd")"
    if [ -n "$CTID_CREATED" ]; then
        msg_warn "$(t w_ct1 "$CTID_CREATED")"
        msg_warn "$(t w_ct2 "$CTID_CREATED" "$CTID_CREATED")"
        msg_warn "$(t w_ct3 "$CTID_CREATED")"
    fi
    exit 1
}
trap 'error_handler "$LINENO" "$BASH_COMMAND"' ERR

cancel() { t cancelled; echo; exit 0; }

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
    echo -e "${RESET}  $(t sub)"
    echo ""
}
header

[ "$(id -u)" -eq 0 ] || { msg_error "$(t e_root)"; exit 1; }
command -v pveversion >/dev/null 2>&1 || { msg_error "$(t e_nopve)"; exit 1; }
if ! pveversion | grep -Eq 'pve-manager/([7-9]|[1-9][0-9])\.'; then
    msg_error "$(t e_pvever "$(pveversion)")"
    exit 1
fi
for tool in pct pveam pvesm pvesh; do
    command -v "$tool" >/dev/null 2>&1 || { msg_error "$(t e_tool "$tool")"; exit 1; }
done
if [ -f /run/systemd/container ] || grep -qa 'container=lxc' /proc/1/environ 2>/dev/null; then
    msg_error "$(t e_inct)"
    exit 1
fi

HAS_WHIPTAIL=0
if command -v whiptail >/dev/null 2>&1 && [ -t 0 ] && [ -t 1 ]; then HAS_WHIPTAIL=1; fi

# ----------------------------------------------------------------------------
# 1. Paramètres
# ----------------------------------------------------------------------------
MODE="${var_mode:-}"
CHOOSE_STORAGE="${var_choose_storage:-0}"   # 1 = proposer le choix des stockages même en mode par défaut
if [ "$MODE" = "storage" ]; then MODE="default"; CHOOSE_STORAGE=1; fi
if [ -z "$MODE" ]; then
    if [ "$HAS_WHIPTAIL" -eq 1 ]; then
        CHOICE=$(whiptail --backtitle "Stellio — Proxmox VE" --title "$(t m_title)" \
            --menu "\n$(t m_text)" 16 76 4 \
            "default"  "$(t m_default)" \
            "storage"  "$(t m_storage)" \
            "advanced" "$(t m_adv)" \
            "cancel"   "$(t m_cancel)" 3>&1 1>&2 2>&3) || cancel
        [ "$CHOICE" = "cancel" ] && cancel
        if [ "$CHOICE" = "storage" ]; then MODE="default"; CHOOSE_STORAGE=1; else MODE="$CHOICE"; fi
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
DISK="${var_disk:-32}"
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
    whiptail --backtitle "Stellio — Proxmox VE" --title "$(t a_title)" \
        --inputbox "$1" 10 66 "$2" 3>&1 1>&2 2>&3
}

# Liste les stockages Proxmox qui acceptent un type de contenu (rootdir, vztmpl)
list_storages() { pvesm status -content "$1" 2>/dev/null | awk 'NR>1 && $3=="active" {print $1}'; }
storage_free_gb() { pvesm status 2>/dev/null | awk -v s="$1" '$1==s {printf "%.1f", $6/1048576}'; }
storage_type()    { pvesm status 2>/dev/null | awk -v s="$1" '$1==s {print $2}'; }

pick_storage() {  # pick_storage <content> <titre> <préféré>
    local content="$1" title="$2" preferred="$3"
    local -a stores
    mapfile -t stores < <(list_storages "$content")
    [ "${#stores[@]}" -gt 0 ] || { msg_error "$(t s_none "$content")"; exit 1; }
    if [ "${#stores[@]}" -eq 1 ]; then echo "${stores[0]}"; return; fi
    if { [ "$MODE" = "advanced" ] || [ "$CHOOSE_STORAGE" = "1" ]; } && [ "$HAS_WHIPTAIL" -eq 1 ]; then
        local -a menu=()
        local s def="${stores[0]}" p
        for s in "${stores[@]}"; do menu+=("$s" "$(t s_item "$(storage_type "$s")" "$(storage_free_gb "$s")")"); done
        for p in "$preferred" local-lvm local-zfs local; do
            if printf '%s\n' "${stores[@]}" | grep -qx "$p"; then def="$p"; break; fi
        done
        whiptail --backtitle "Stellio — Proxmox VE" --title "$title" --default-item "$def" \
            --menu "\n$(t s_menu "$content")" 18 72 8 "${menu[@]}" 3>&1 1>&2 2>&3 || cancel
        return
    fi
    local s
    for s in "$preferred" local-lvm local-zfs local; do
        if printf '%s\n' "${stores[@]}" | grep -qx "$s"; then echo "$s"; return; fi
    done
    echo "${stores[0]}"
}

if [ "$MODE" = "advanced" ] && [ "$HAS_WHIPTAIL" -eq 1 ]; then
    CTID=$(ask "$(t a_ctid)" "$CTID") || cancel
    HN=$(ask "$(t a_hn)" "$HN") || cancel
    CORES=$(ask "$(t a_cores)" "$CORES") || cancel
    RAM=$(ask "$(t a_ram)" "$RAM") || cancel
    DISK=$(ask "$(t a_disk)" "$DISK") || cancel
    BRIDGE=$(ask "$(t a_bridge)" "$BRIDGE") || cancel
    IPCFG=$(ask "$(t a_ip)" "$IPCFG") || cancel
    if [ "$IPCFG" != "dhcp" ]; then GW=$(ask "$(t a_gw)" "$GW") || cancel; fi
    VLAN=$(ask "$(t a_vlan)" "$VLAN") || cancel
    PORT=$(ask "$(t a_port)" "$PORT") || cancel
    if whiptail --backtitle "Stellio — Proxmox VE" --title "$(t a_priv_t)" --defaultno \
        --yesno "$(t a_priv_x)" 12 70; then
        UNPRIV=0
    else
        UNPRIV=1
    fi
    MOUNT=$(ask "$(t a_mount)" "$MOUNT") || cancel
fi

# Validation
is_int() { [[ "$1" =~ ^[0-9]+$ ]]; }
is_int "$CTID"  || { msg_error "$(t v_ctid "$CTID")"; exit 1; }
is_int "$CORES" && [ "$CORES" -ge 1 ] || { msg_error "$(t v_cores "$CORES")"; exit 1; }
is_int "$RAM"   && [ "$RAM" -ge 1024 ] || { msg_error "$(t v_ram "$RAM")"; exit 1; }
is_int "$SWAP"  || { msg_error "$(t v_swap "$SWAP")"; exit 1; }
is_int "$DISK"  && [ "$DISK" -ge 4 ] || { msg_error "$(t v_disk "$DISK")"; exit 1; }
is_int "$PORT"  && [ "$PORT" -ge 1 ] && [ "$PORT" -le 65535 ] || { msg_error "$(t v_port "$PORT")"; exit 1; }
[[ "$HN" =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$ ]] || { msg_error "$(t v_hn "$HN")"; exit 1; }
if pvesh get /cluster/nextid --vmid "$CTID" >/dev/null 2>&1; then :; else
    msg_error "$(t v_used "$CTID")"; exit 1
fi
if [ "$IPCFG" != "dhcp" ] && [ -z "$GW" ]; then msg_error "$(t v_gw)"; exit 1; fi

HOST_MOUNT=""; CT_MOUNT=""
if [ -n "$MOUNT" ]; then
    HOST_MOUNT="${MOUNT%%:*}"; CT_MOUNT="${MOUNT#*:}"
    [ -d "$HOST_MOUNT" ] || { msg_error "$(t v_mnt "$HOST_MOUNT")"; exit 1; }
    [[ "$CT_MOUNT" == /* ]] || { msg_error "$(t v_mntabs)"; exit 1; }
fi

if [ -z "$SOURCE_TYPES" ]; then
    if [ -n "$MOUNT" ]; then SOURCE_TYPES="folder,smb,nfs"; else SOURCE_TYPES="smb,nfs"; fi
fi
[[ "$SOURCE_TYPES" =~ ^(folder|file|smb|nfs)(,(folder|file|smb|nfs))*$ ]] || { msg_error "$(t v_src "$SOURCE_TYPES")"; exit 1; }

[ -n "$STORAGE" ] || STORAGE=$(pick_storage rootdir "$(t s_t_ct)" local-lvm)
[ -n "$TEMPLATE_STORAGE" ] || TEMPLATE_STORAGE=$(pick_storage vztmpl "$(t s_t_tpl)" local)
[ -n "$STORAGE" ] && [ -n "$TEMPLATE_STORAGE" ] || cancel
# Un stockage imposé par var_storage / var_template_storage doit exister et accepter le bon contenu
list_storages rootdir | grep -qx -- "$STORAGE" || { msg_error "$(t v_stor "$STORAGE" "$(list_storages rootdir | paste -sd, -)")"; exit 1; }
list_storages vztmpl  | grep -qx -- "$TEMPLATE_STORAGE" || { msg_error "$(t v_tpl "$TEMPLATE_STORAGE" "$(list_storages vztmpl | paste -sd, -)")"; exit 1; }

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
        echo -e "${YELLOW}$(t last_lines)${RESET}" >&2
        tail -n 30 "$LOG" >&2 || true
        echo -e "${YELLOW}$(t full_log "$LOG")${RESET}" >&2
        if [ -n "$CTID_CREATED" ]; then
            msg_warn "$(t w_ct4 "$CTID_CREATED" "$CTID_CREATED" "$CTID_CREATED")"
        fi
        exit 1
    fi
}

NODE=$(hostname)
PVE_VER=$(pveversion | sed -E 's#^pve-manager/([^/]+)/.*running kernel: ([^)]*)\).*#\1 (Kernel: \2)#')
echo -e " ⚙️  ${CYAN}$([ "$MODE" = "advanced" ] && t r_adv "$NODE" || t r_def "$NODE")${RESET}"
kv "💡" "$(t l_pve)" "$PVE_VER"
kv "🆔" "$(t l_id)" "$CTID ($HN)"
kv "🖥️ " "$(t l_os)" "debian (12)"
kv "📦" "$(t l_type)" "$([ "$UNPRIV" = "1" ] && t u_unpriv || t u_priv)"
kv "💾" "$(t l_disk)" "${DISK} GB"
kv "🗄️ " "$(t l_stor)" "$(t u_stor "$STORAGE" "$(storage_type "$STORAGE")" "$(storage_free_gb "$STORAGE")")"
kv "📚" "$(t l_tpl)" "$(t u_stor "$TEMPLATE_STORAGE" "$(storage_type "$TEMPLATE_STORAGE")" "$(storage_free_gb "$TEMPLATE_STORAGE")")"
kv "🧠" "$(t l_cpu)" "$CORES"
kv "🛠️ " "$(t l_ram)" "$(t u_ram "$RAM" "$SWAP")"
kv "🌐" "$(t l_net)" "$(t u_net "$BRIDGE" "${VLAN:+$(t u_vlan "$VLAN")}" "$IPCFG" "${GW:+$(t u_via "$GW")}")"
kv "🔒" "$(t l_src)" "$(t u_src "$SOURCE_TYPES" "$([[ ",$SOURCE_TYPES," == *,folder,* ]] && t u_lok || t u_lhid)")"
[ -n "$MOUNT" ] && kv "📁" "$(t l_mount)" "$HOST_MOUNT → $CT_MOUNT"
echo -e " 🚀  ${CYAN}$(t r_create)${RESET}"
echo ""
FREE_INT=$(storage_free_gb "$STORAGE" | cut -d. -f1)
if [ -n "$FREE_INT" ] && [ "$FREE_INT" -lt "$DISK" ]; then
    msg_error "$(t v_free "$STORAGE" "$FREE_INT" "$DISK")"
    exit 1
fi
echo -e " ${GREEN}✔️${RESET}  $(t ok_stor "$STORAGE" "$(storage_type "$STORAGE")" "$(storage_free_gb "$STORAGE")")"
echo -e " ${GREEN}✔️${RESET}  $(t ok_tpl "$TEMPLATE_STORAGE" "$(storage_type "$TEMPLATE_STORAGE")" "$(storage_free_gb "$TEMPLATE_STORAGE")")"

# ----------------------------------------------------------------------------
# 2. Modèle Debian 12
# ----------------------------------------------------------------------------
refresh_templates() { pveam update || t upd_fail; }
step "$(t st_upd)" refresh_templates

TEMPLATE=$(pveam available --section system | awk '$2 ~ /^debian-12-standard/ {print $2}' | sort -V | tail -n1)
[ -n "$TEMPLATE" ] || { msg_error "$(t e_tplnf)"; exit 1; }

if pveam list "$TEMPLATE_STORAGE" | grep -F -- "$TEMPLATE" >/dev/null; then
    echo -e " ${GREEN}✔️${RESET}  $(t ok_tplp "$TEMPLATE")"
else
    step "$(t st_tpldl "$TEMPLATE")" pveam download "$TEMPLATE_STORAGE" "$TEMPLATE"
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
        --description "$(t desc "$CTID")"
    if [ -n "$MOUNT" ]; then pct set "$CTID" -mp0 "${HOST_MOUNT},mp=${CT_MOUNT}"; fi
}
step "$(t st_create "$CTID")" create_ct
CTID_CREATED="$CTID"

step "$(t st_start)" pct start "$CTID"

wait_network() {
    local ip=""
    for _ in $(seq 1 40); do
        ip=$(pct exec "$CTID" -- hostname -I 2>/dev/null | awk '{print $1}' || true)
        if [ -n "$ip" ] && pct exec "$CTID" -- getent hosts deb.debian.org >/dev/null 2>&1; then return 0; fi
        sleep 2
    done
    t net_fail "${ip:-$(t none)}" "$BRIDGE"; echo
    return 1
}
step "$(t st_net)" wait_network
CT_IP=$(pct exec "$CTID" -- hostname -I 2>/dev/null | awk '{print $1}' || true)

# ----------------------------------------------------------------------------
# 4. Installation de Stellio dans le conteneur (par étapes)
# ----------------------------------------------------------------------------
SETUP_SCRIPT=$(mktemp); SETUP_ENV=$(mktemp)
printf 'SVC_USER=%q\nPORT=%q\nSOURCE_TYPES=%q\nINSTALL_URL=%q\n' "$SVC_USER" "$PORT" "$SOURCE_TYPES" "$INSTALL_URL" > "$SETUP_ENV"
for _k in g_nonfree g_apt g_base g_user g_dl g_svc g_cons b_upd; do
    _v="M_${_k}"; printf 'M_%s=%q\n' "$_k" "${!_v}" >> "$SETUP_ENV"
done
cat > "$SETUP_SCRIPT" <<'SETUP'
#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive LC_ALL=C.UTF-8 LANG=C.UTF-8
# shellcheck disable=SC1091
source /root/stellio-setup.env

stage_sources() {
    echo "→ ${M_g_nonfree}"
    for f in /etc/apt/sources.list /etc/apt/sources.list.d/*.sources; do
        [ -f "$f" ] || continue
        sed -i -E '/^(deb |Components:)/{/non-free/!s/\bmain\b/main contrib non-free non-free-firmware/}' "$f"
    done
}

stage_base() {
    echo "→ ${M_g_apt}"
    apt-get update
    echo "→ ${M_g_base}"
    apt-get install -y sudo curl git ca-certificates
}

stage_user() {
    echo "→ ${M_g_user//%s/${SVC_USER}}"
    id "$SVC_USER" >/dev/null 2>&1 || useradd -m -s /bin/bash "$SVC_USER"
    echo "${SVC_USER} ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/${SVC_USER}"
    chmod 440 "/etc/sudoers.d/${SVC_USER}"
    echo "→ ${M_g_dl}"
    curl -fsSL "$INSTALL_URL" -o "/home/${SVC_USER}/install-pi.sh"
    chown "${SVC_USER}:${SVC_USER}" "/home/${SVC_USER}/install-pi.sh"
    chmod +x "/home/${SVC_USER}/install-pi.sh"
}

stage_install() {
    # install-pi.sh affiche ses propres étapes « → ... » : elles alimentent l'indicateur de progression
    su - "$SVC_USER" -c "STELLIO_PORT=${PORT} bash ~/install-pi.sh"
}

stage_service() {
    echo "→ ${M_g_svc//%s/${SOURCE_TYPES}}"
    mkdir -p /etc/systemd/system/stellio.service.d
    cat > /etc/systemd/system/stellio.service.d/sources.conf <<CONF
[Service]
Environment="STELLIO_ALLOWED_SOURCE_TYPES=${SOURCE_TYPES}"
Nice=10
CPUWeight=50
IOSchedulingClass=best-effort
IOSchedulingPriority=7
CONF
    # Plafonds de ressources : Stellio ne peut pas dépasser ~75 % de la RAM et du CPU du conteneur
    # (MemoryHigh = ralentissement progressif, MemoryMax = limite dure avant que le noyau ne tue tout le conteneur)
    mem_mb=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)
    cpus=$(nproc 2>/dev/null || echo 1)
    cat > /etc/systemd/system/stellio.service.d/limits.conf <<LIM
[Service]
MemoryHigh=$((mem_mb * 75 / 100))M
MemoryMax=$((mem_mb * 85 / 100))M
CPUQuota=$((cpus * 75))%
LIM
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
    echo "→ ${M_g_cons}"
    printf 'STELLIO_PORT=%s\nSTELLIO_UPD=%q\n' "${PORT}" "${M_b_upd}" > /etc/stellio-lxc.conf
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
printf '    🔄  \033[33m%s: \033[32mupdate-stellio\033[0m\n\n' "${STELLIO_UPD:-Update}"
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
step "$(t st_src)"  ct_stage sources
step "$(t st_base)" ct_stage base
step "$(t st_user)" ct_stage user
step "$(t st_inst)" ct_stage install
step "$(t st_svc)" ct_stage service
step "$(t st_cons)" ct_stage console

# ----------------------------------------------------------------------------
# 5. Vérification finale
# ----------------------------------------------------------------------------
wait_stellio() {
    for _ in $(seq 1 60); do
        if pct exec "$CTID" -- curl -fs -o /dev/null "http://127.0.0.1:${PORT}/api/ping" 2>/dev/null; then return 0; fi
        sleep 2
    done
    t nr "$PORT"; echo
    return 1
}
UP=0
if STEP_SOFT=1 step "$(t st_ver)" wait_stellio; then UP=1; fi
pct exec "$CTID" -- bash /root/stellio-setup.sh cleanup 2>/dev/null || true

CT_IP=$(pct exec "$CTID" -- hostname -I 2>/dev/null | awk '{print $1}' || echo "$CT_IP")
CTID_CREATED=""   # installation terminée : plus de message de suppression en cas d'erreur
rm -f "$LOG"

echo ""
if [ "$UP" -eq 1 ]; then
    echo -e " ${GREEN}✔️${RESET}  $(t f_up "$PORT")"
    echo -e " ${GREEN}✔️  $(t f_done)${RESET}"
else
    echo -e " ${YELLOW}⚠️${RESET}  $(t f_nup)"
    echo -e "     $(t f_logs "$CTID")"
fi
echo ""
echo -e " 🚀  ${GREEN}$(t f_made)${RESET}"
echo -e " 💡  ${YELLOW}$(t f_acc)${BOLD}http://${CT_IP}:${PORT}${RESET}"
echo ""
echo "     $(t f_ct "$CTID" "$HN" "$CTID")"
echo "     $(t f_pw "$ROOT_PW")"
echo "     $(t f_upd "$CTID")"
echo "     $(t f_log "$CTID")"
if [ -n "$MOUNT" ]; then
    echo ""
    echo "     $(t f_mnt1 "$CT_MOUNT")"
    if [ "$UNPRIV" = "1" ]; then
        echo "     $(t f_mnt2)"
        echo "     $(t f_mnt3 "$HOST_MOUNT")"
    fi
else
    echo ""
    echo "     $(t f_src1)"
    echo "     $(t f_src2 "$CTID")"
    echo "     $(t f_src3)"
    echo "     $(t f_src4)"
fi
echo ""
