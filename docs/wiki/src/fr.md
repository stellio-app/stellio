@@@ Home | Accueil
# Wiki Stellio
{{img:dashboard}}


**Stellio** est le gestionnaire de fichiers 3D pour makers et propriétaires d'imprimantes 3D. Il centralise votre bibliothèque (STL, 3MF, OBJ, STEP, PLY, AMF), automatise les tâches répétitives et s'intègre à votre flux d'impression.

> 🔒 **Philosophie** : vos données restent chez vous. Tout fonctionne en local ; par défaut, rien ne quitte votre machine.

## Par où commencer ?

| Je veux… | Page |
|---|---|
| Installer Stellio | [Installation](fr-Installation) |
| Faire mes premiers pas | [Premiers pas](fr-Getting-Started) |
| Gérer mes fichiers 3D | [Bibliothèque](fr-Library) |
| Connecter mes imprimantes | [Imprimantes](fr-Printers) |
| Suivre mes bobines | [Filament](fr-Filament) |
| Télécharger des modèles | [Téléchargements](fr-Downloads) |
| Utiliser l'IA et S.O.S Print | [Intelligence artificielle](fr-AI) |
| Calculer coûts, devis, factures | [Coûts et gestion](fr-Costs-and-Management) |
| Y accéder depuis mon téléphone | [Accès distant et mobile](fr-Remote-Access) |
| Installer sur Raspberry Pi / Proxmox | [Édition serveur](fr-Server-Edition) |
| Régler, sauvegarder, comprendre mes données | [Réglages et données](fr-Settings-and-Data) |
| Résoudre un problème | [Dépannage](fr-Troubleshooting) |
| Contribuer au projet | [Contribuer](fr-Contributing) |

## Liens utiles

- 🌐 Site : [stellio-app.com](https://stellio-app.com) — ▶ [démo en ligne (lecture seule)](https://demo.stellio-app.com)
- 📦 [Téléchargements (Releases)](https://github.com/stellio-app/stellio/releases)
- 🐛 [Signaler un bug](https://github.com/stellio-app/stellio/issues) · 💡 [Proposer une idée](https://github.com/stellio-app/stellio/discussions) · 💬 [Discord](https://discord.gg/ySxpHvS6bd)
- 📜 Licence **AGPL v3**

@@@ Installation | Installation
# Installation

| Plateforme | Fichier / méthode | Mode |
|---|---|---|
| 🪟 Windows | `Stellio-Setup-<version>.exe` | Application de bureau |
| 🪟 Windows portable | `Stellio-v<version>-portable-win64.zip` | Application de bureau, sans installation |
| 🍎 macOS | `.dmg` (Apple Silicon `arm64` ou Intel `x86_64`) | Application de bureau |
| 🐧 Linux | `Stellio-v<version>-x86_64.AppImage` | Application de bureau |
| 🍓 Raspberry Pi / Linux | `install-pi.sh` | Serveur (navigateur) |
| 🖥️ Proxmox VE | `stellio-lxc.sh` | Conteneur LXC en une commande |
| 📲 Android | APK compagnon | Voir [Accès distant et mobile](fr-Remote-Access) |

Tous les fichiers sont sur la page [Releases](https://github.com/stellio-app/stellio/releases) et accompagnés d'une somme de contrôle `.sha256`.

## Windows

1. Téléchargez l'installateur depuis les Releases.
2. Lancez `Stellio-Setup-<version>.exe`.
3. Terminé.

**Version portable** : dézippez où vous voulez (disque, clé USB) et lancez `Stellio.exe`. Vos données restent dans le dossier `data` à côté de l'exécutable (gardez le fichier `portable.flag`).

> ⚠️ L'installateur n'est **pas signé** : Windows SmartScreen peut afficher un avertissement. Vérifiez le `.sha256` si vous le souhaitez ; la mise à jour intégrée le contrôle avant d'installer.

## macOS

Ouvrez le `.dmg` et glissez Stellio dans Applications. Choisissez le fichier adapté à votre Mac : `arm64` (M1, M2, M3…) ou `x86_64` (Intel). Les versions ne sont pas notariées : au premier lancement, clic droit → **Ouvrir**.

> Si l'écran reste blanc : le port 5000 est peut-être pris par le « Récepteur AirPlay » de macOS. Stellio choisit alors automatiquement un autre port libre. Voir [Dépannage](fr-Troubleshooting).

## Linux (AppImage)

```bash
chmod +x Stellio-v*-x86_64.AppImage
./Stellio-v*-x86_64.AppImage
```
L'AppImage embarque ses informations de mise à jour (`.zsync`).

## Raspberry Pi / serveur Linux

Mode **serveur sans interface** : Stellio tourne en arrière-plan et s'utilise depuis un navigateur. Voir [Édition serveur](fr-Server-Edition) pour le détail.

```bash
curl -O https://raw.githubusercontent.com/stellio-app/stellio/main/install-pi.sh
chmod +x install-pi.sh
./install-pi.sh
```

## Proxmox VE

Dans le **Shell de l'hôte Proxmox** :
```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/stellio-app/stellio/main/stellio-lxc.sh)"
```
Détails dans [Édition serveur](fr-Server-Edition).

## Mises à jour

- **Bureau** : Stellio détecte les nouvelles versions depuis GitHub et applique un patch `.zip` (même mécanisme sur Windows, macOS et Linux). Le widget « Mise à jour » du tableau de bord ouvre la fenêtre de mise à jour.
- **Serveur** : même mise à jour automatique, ou `update-stellio` (conteneur LXC) / `./install-pi.sh` (Raspberry Pi).
- Au premier lancement de chaque version, les modules manquants (devis PDF, import de tableur, notifications…) sont téléchargés automatiquement.

@@@ Getting-Started | Premiers pas
# Premiers pas
{{img:library}}


## 1. Premier lancement
Stellio affiche une **visite guidée** et une liste de démarrage (« Premiers pas »). Vous pouvez relancer la visite à tout moment depuis les Réglages.

## 2. Créer votre compte
Les comptes sont **locaux** : mot de passe + code de récupération + question secrète. La réinitialisation du mot de passe est 100 % locale, sans e-mail ni internet.

## 3. Ajouter vos sources
Une **source** est un dossier ou un partage qui contient vos modèles :
- dossier local, fichier isolé, partage **SMB** ou **NFS** ;
- les dossiers 3D détectés sur votre ordinateur vous sont **suggérés** et s'ajoutent en un clic ;
- pour chaque source, vous choisissez les types de fichiers affichés.

Stellio scanne alors vos fichiers et génère les miniatures 3D en arrière-plan.

## 4. Ajouter une imprimante (facultatif)
Allez dans la page **Imprimantes** : la découverte réseau propose les machines détectées. Voir [Imprimantes](fr-Printers).

## 5. Choisir votre slicer
Stellio détecte automatiquement vos slicers installés (OrcaSlicer, Bambu Studio, PrusaSlicer, Cura…). Le bouton d'envoi ouvre le fichier directement dans le slicer.

## Tableau de bord
La page d'accueil réunit impressions en cours, stock bas, impressions et fichiers récents. Les **widgets** (une vingtaine) se réorganisent par glisser-déposer et peuvent être masqués : impressions en cours, stock bas, derniers S.O.S Print, suggestions, instances Stellio, projets terminés, galerie, devis…

## Outils du quotidien
- **Palette de commandes** `Ctrl+K` : naviguer, lancer une action, retrouver un fichier, une étiquette, une bobine ou un profil.
- **Centre de notifications** (cloche) : fin d'impression, échec, maintenance, stock bas, séchage de bobine.
- **Widget flottant** de progression de l'impression en cours, visible sur toutes les pages.
- **Raccourcis clavier** : voir [Réglages et données](fr-Settings-and-Data).

@@@ Library | Bibliothèque
# Bibliothèque
{{img:library}}


## Sources et miniatures
- Sources multiples : dossiers locaux, fichiers, partages SMB/NFS.
- **Miniatures 3D automatiques** (PyRender, ou rendu CPU de repli) avec aperçu agrandi au survol.
- La génération se met **en pause dès que vous utilisez l'application** et reprend ensuite.
- Réglage **Performance des miniatures** : Automatique / Éco / Normal / Rapide.
- Formats : STL, 3MF (y compris multi-plateaux et PrusaSlicer), OBJ, STEP/STP, PLY, AMF (convertis en STL pour les slicers qui ne les lisent pas), et archives (ZIP, RAR, 7z, TAR) explorables directement.

## Organiser
- **Étiquettes** colorées, avec étiquetage automatique par IA ; étiquetage de plusieurs fichiers en un clic.
- **Favoris**, filtres avancés (type, taille, poids, statut d'impression), **filtres enregistrés**.
- Filtres de statut : « Envoyé au slicer », « Déjà imprimé », « Déjà réussi », « Déjà raté ».
- **Filtre « Stock de filament »** : ne garde que les fichiers imprimables avec les bobines que vous possédez.
- Tri, recherche et filtres **mémorisés** à la réouverture.
- **File « À imprimer bientôt »**, réordonnable, envoyable au slicer.
- **Renommage en masse** (rechercher/remplacer, préfixe, suffixe, numérotation) avec aperçu.
- **Annuler une suppression** (`Ctrl+Z`) grâce à une corbeille temporaire de 5 minutes ; vaut aussi pour étiquettes, projets et sources.
- Sélection rapide : `Maj+clic` pour une plage, flèches + `Entrée`.
- **Détection de doublons** (exacts et de géométrie proche).
- **Origine du modèle** : lien source, auteur, licence, notes, date de téléchargement.
- **Glisser-déposer** de fichiers 3D depuis l'explorateur, y compris via navigateur.

## Recherche
- Recherche classique et **recherche sémantique par IA** (« je cherche un support pour… »), avec recherches récentes mémorisées.
- **Collections intelligentes**.

## Projets / assemblages
Regroupez plusieurs fichiers pour un même objet.
- 3MF **multi-plateaux** : l'ajout à un projet le découpe en un 3MF par plateau (6 plateaux = 6 fichiers), rangés dans un dossier caché.
- Action **« Découper les plateaux »** dans le menu ⋯ d'un fichier.
- Carte de projet : clic sur la miniature = visionneuse 3D ; filtre « Tous / En cours / Terminés » mémorisé ; **Coût du projet** en un bouton.

{{img:projects}}

## Visionneuse 3D et outils
- **Visionneuse 3D** (Three.js, fonctionne hors ligne), navigation entre plateaux.
- **Placement automatique** sur le plateau (rectpack, ou silhouette réelle avec shapely).
- **Réparation de maillage** (trimesh + pymeshfix) avec comparaison avant/après.
- **Convertisseur** STL ↔ 3MF ↔ OBJ.
- **Analyse d'imprimabilité** (surplombs) et **orientations suggérées**.
- **Contrôle d'intégrité** (fichiers corrompus ou manquants).
- **Statistiques** détaillées (formats, plateformes, fiabilité des profils).

{{img:viewer}}

## Historique et photos
- **Historique** paginé par semaine, avec notation réussi/raté (qui nourrit l'IA), boutons **Voir le fichier** et **Réimprimer**, filtres par plateforme, résultat et dates.
- **Galerie de photos** d'impression. La photo de fin d'impression se choisit ensuite *Réussi* ou *Raté* d'un clic.
- **Mes G-codes** : G-codes liés à un fichier, téléchargement, et bouton **Ouvrir dans le slicer**.
- **Sauvegarde** de la bibliothèque : voir [Réglages et données](fr-Settings-and-Data).

@@@ Printers | Imprimantes
# Imprimantes
{{img:printers}}


## Marques prises en charge

| Marque | Modèles | Connexion |
|---|---|---|
| **Bambu Lab** | X1/X1C/X1E, X2D, P1P/P1S, P2S, A1/A1 mini, H2D/H2S/H2C | MQTT (LAN + cloud) : suivi, AMS, caméra, découverte SSDP |
| **Prusa** | MK4, MK3.9, MK3.5, MINI+, XL, CORE One | PrusaLink (HTTP) |
| **Creality** | Séries K1/K2, Ender-3 V3, Hi | WebSocket : suivi, CFS, découverte UDP |
| **Elegoo** | Centauri Carbon 1 & 2, séries résine Saturn/Mars | SDCP (WebSocket) |
| **FlashForge** | Adventurer 5M/5M Pro, AD5X | API propriétaire |
| **Klipper / Moonraker** | Toute machine Klipper (Voron…) | HTTP : suivi, envoi, caméra, heures exactes |
| **OctoPrint** | Toute imprimante pilotée par OctoPrint | HTTP |

Les autres modèles qui parlent le même protocole fonctionnent en général. Dites-nous sur GitHub si le vôtre marche.

## Ajouter une imprimante
- **Découverte automatique** du réseau local (SSDP, diffusion UDP, sondes ciblées) : les imprimantes détectées s'ajoutent en un clic.
- Sinon, saisie manuelle (type, modèle, adresse, clé d'accès).
- Indiquez le **volume d'impression** (X, Y, Z) : Stellio avertit avant l'envoi si la pièce est trop grande.

## Suivi
- Température, progression, caméra en temps réel ; miniature et nom du fichier en cours sur la carte.
- Compteur automatique des heures d'impression.
- **Widget flottant** de progression ; il se place à gauche de la flèche « haut de page » quand elle s'affiche.

## Envoyer au slicer / à l'imprimante
- Fenêtre d'envoi avec **aperçu rapide** (poids, temps estimé), **choix de la bobine** et calibrations rappelées.
- **Vérification avant impression** : bobine à sécher, filament abrasif (buse en acier trempé conseillée), absence de calibration, volume d'impression, matière suffisante.
- **Réimprimer comme la dernière fois** depuis l'historique.
- **Mode collaboratif léger** : prévient si un autre appareil regarde le fichier ou avant un double envoi.
- **Ouvrir dans le slicer** depuis « Mes G-codes ».

## Pendant l'impression
- **Prise connectée** (Shelly, Tasmota, Home Assistant) : Stellio lit les watts, enregistre la consommation réelle (kWh) et le coût.
- **Consommation réelle de filament** relevée après l'impression.
- **Photo de fin d'impression** prise quand l'impression atteint **100 %** (la pièce est encore sur le plateau), une seule photo à classer *Réussi/Raté*.
- **Surveillance IA des échecs** (Ollama avec vision, 100 % local) : alerte en cas de spaghetti ou de pièce décollée, **jamais d'arrêt automatique**.
- **Timelapse** automatique (caméra → vidéo MP4, nécessite ffmpeg).
- **Liens de partage d'état** en lecture seule.

## Maintenance
- **Maintenance prédictive** avec tâches propres à chaque marque.
- **Pièces d'usure** (buses, plaques, courroies…) avec alertes de stock, liées aux tâches de maintenance.
- **Calibrations** (débit, pressure advance, températures) par filament et imprimante.

@@@ Filament | Filament
# Filament

## Sources d'inventaire
| Source | Détails |
|---|---|
| **Spoolman** | Détection automatique sur le réseau. Stellio **ne lui écrit plus** la consommation (évite un double décompte). |
| **Manuel** | Bobines saisies à la main, import Excel/CSV. |
| **TigerTag** | Identification NFC/RFID. Connexion par e-mail et mot de passe (seul un jeton chiffré est conservé) ou reprise d'une session TigerTag Studio. **Lecture seule.** |
| **OpenPrintTag** | Standard ouvert d'étiquettes NFC : import/export de fichiers `.bin`, lecture/écriture depuis l'app Android, poids consommé tenu à jour. |
| **Bambu AMS / Creality CFS** | Lecture des emplacements. |

**Open Filament Database** : cherchez une bobine par marque, matière et couleur, puis créez-la en un clic (poids, diamètre et densité préremplis).

## Au quotidien
- **Consommation automatique** à l'envoi au slicer, avec contrôle de compatibilité (assez de matière ?).
- **Alertes de stock bas** au démarrage, seuil réglable, case « À commander » et lien d'achat.
- **Racheter une bobine** : boutique du fabricant en tête (Arianeplast, Bambu Lab, Polymaker, eSUN, Sunlu…), puis boutiques générales ; stock vérifié automatiquement quand le site le permet.
- **Séchage** : journal, état (sec / à sécher) selon la matière, température et durée suggérées, rappels.
- **Fiche bobine** : impressions, grammes, coût et écart non suivi.

## Pesée et prévision
Le bloc **Pesée et prévision de filament** estime la **date de rupture** de chaque bobine d'après sa consommation par jour.
- Le poids restant vient d'une pesée manuelle ou de TigerTag.
- Les poids TigerTag alimentent **uniquement la prévision** : ils ne s'affichent ici que pour une bobine **bientôt à court** (14 jours ou moins). Le reste est dans l'inventaire.
- Formulaire de pesée manuelle toujours disponible.

{{img:filament}}

## Prévision de consommation
La bibliothèque peut afficher un **avertissement de réassort** quand le stock ne suffit pas pour vos favoris.

@@@ Downloads | Téléchargements
# Téléchargements

Téléchargez des modèles directement dans vos sources depuis plusieurs plateformes :

| Plateforme | Connexion |
|---|---|
| **Printables** | API GraphQL |
| **MakerWorld** | Connexion Bambu Lab en 2 étapes |
| **Thingiverse** | Clé d'API |
| **Nexprint** (Elegoo) | E-mail et mot de passe du compte, stockés chiffrés |
| **Creality Cloud** | Depuis les Réglages (identifiants chiffrés ; connexion Google non prise en charge) |
| **Snapmaker Space** | Idem |

- **Ctrl+N** ouvre un nouveau téléchargement.
- Le fichier arrive dans la source de votre choix et l'**origine du modèle** (lien, auteur, licence) est enregistrée.
- **Nouvelle version** : chaque jour, Stellio vérifie si les modèles téléchargés (Printables, MakerWorld, Thingiverse) ont été mis à jour.
- **Mes likes / Mes créations** : les comptes connectés sont testés à chaque lancement du bureau (toutes les 24 h sur serveur).
- **Liens utiles** : boutiques, constructeurs, sites de modèles et ressources, en sections repliables.

@@@ AI | Intelligence artificielle
# Intelligence artificielle

## IA locale (Ollama)
Par défaut, l'IA tourne **100 % en local** avec [Ollama](https://ollama.com/). Elle est désactivable.

Fonctions :
- **Étiquetage automatique** et **description** des modèles ;
- **Recherche sémantique** en langage naturel ;
- **Analyse d'imprimabilité** et **orientations suggérées** ;
- **Recommandation de profil de slicer** (géométrie + historique de réussite) ;
- **Estimation du temps d'impression** avant découpe ;
- **Surveillance des échecs** (modèle de vision).

L'adresse du serveur Ollama se règle dans les Réglages (`ollama_url`) : vous pouvez viser une machine distante plus puissante (utile sur Raspberry Pi).

## IA en ligne (édition serveur, facultatif)
Au lieu d'Ollama, utilisez **Claude** (Anthropic), **ChatGPT** (OpenAI) ou **Gemini** (Google) avec **votre propre clé d'API** (Réglages → Intelligence artificielle).
- La clé est chiffrée sur le serveur et jamais renvoyée au navigateur.
- Les requêtes (noms de fichiers, étiquettes, descriptions, photos S.O.S Print) partent chez le fournisseur choisi et sont facturées sur votre clé.
- Ollama reste le choix par défaut.

## S.O.S Print
Diagnostic **adaptatif** d'un échec d'impression :
1. Vous décrivez le problème (photo possible à chaque étape) et, si vous voulez, les réglages utilisés (températures, vitesses, rétraction…).
2. Stellio pose **une question à la fois** (4 au maximum) et réduit une liste d'hypothèses en direct.
3. Il rend un **diagnostic final**.

Les conversations sont enregistrées : rouvrez-les ou marquez-les comme résolues.

> ℹ️ Les résultats « Réussi / Raté » que vous notez dans l'historique améliorent les recommandations.

@@@ Costs-and-Management | Coûts et gestion
# Coûts et gestion
{{img:management}}


## Calcul du coût d'impression
Matière, électricité, usure machine (par heure), frais fixes, marge en % et quantité : prix unitaire et total au centime près.
- La **marge par défaut** se règle une fois dans *Réglages → Tarification d'impression* ; l'historique affiche le **prix de vente** à côté du coût, tandis que les statistiques gardent le coût réel.
- **Coût du projet** : même calcul pour tous les fichiers d'un projet.
- **Prise connectée** : la puissance mesurée remplace l'estimation d'électricité.
- **Empreinte CO₂** de vos impressions (matière + électricité).

## Devis PDF
Générés depuis le calculateur : client, désignation, notes ; en-tête configurable (nom/société, logo, adresse, téléphone, e-mail, site, n° fiscal) et mentions légales en pied de page. Chaque devis est conservé (copie PDF) et consultable dans le widget **Devis**.

## Écran « Gestion »
Visible quand l'option *Activer les fonctions de coût, devis et facturation* est cochée :
- **Devis clients** : un **lien de suivi** permet au client de consulter, accepter ou refuser le devis en ligne ; l'acceptation crée la tâche d'impression et affiche vos infos d'acompte. **Stellio ne traite aucun paiement.** Les liens sont toujours externes ; si l'accès à distance est inactif, l'écran propose de l'activer en un clic.
- **Comptabilité** : export mensuel ZIP (CSV des documents, PDF des factures, totaux par mois).
- **Stock de pièces finies** : seuil d'alerte et réassort (tâche créée à la main ou automatiquement).

## Atelier
- **File de commandes** avec marge réelle, carnet de clients, paiements, factures d'acompte et avoirs, e-mail SMTP, export CSV.
- **Page de suivi client** publique par commande, sans compte : jamais de prix, de marge ni de notes internes.
- **Répartition intelligente** : Stellio propose l'imprimante la plus adaptée à chaque tâche (libre, matière chargée, file) **sans jamais lancer d'impression**.
- **Résumé quotidien ou hebdomadaire** par notification et push (tâches, retards, énergie, bobines, factures, stock).
- **Partage de profils de slicer** vers une autre instance appairée.

## Rapports
- **Fiabilité** : taux de réussite et coût des échecs par profil, matière, imprimante ou bobine.
- **Rapport mensuel** comparé au mois précédent, exportable en PDF.
- **Rapport d'impression** partageable (image PNG) depuis l'historique.
- **Énergie** réelle par prise connectée.



{{img:stats}}
@@@ Remote-Access | Accès distant et mobile
# Accès distant et mobile

## Téléphone et tablette
- **QR code** d'accès mobile à la bibliothèque (**PWA installable**).
- **Application Android compagnon** : un QR code dédié (Réglages → accès mobile) permet de télécharger l'APK. Elle gère adresse interne et externe avec bascule automatique, liaison par QR, photos directement depuis une impression, et lecture/écriture d'étiquettes NFC OpenPrintTag.
- **Mode atelier** plein écran pour tablette/téléphone.

## Accès à distance
- **Cloudflare Tunnel** (gratuit, adresse aléatoire ou fixe), ou **adresse personnalisée** (nom de domaine, DynDNS, VPN, Tailscale…) pour éviter Cloudflare, avec retour à Cloudflare en un clic.
- **Liens de partage** temporaires (24 h, usage unique).

## Comptes
- **Comptes locaux** avec code de récupération et question secrète.
- **Confirmation de session** : à l'ouverture avec une session enregistrée, Stellio demande de confirmer le compte.
- **Comptes invités en lecture seule** : partagez bibliothèque, imprimantes et stock sans risque.
- Sur PC, l'accès par navigateur à l'application Windows est bloqué (jeton interne) : utilisez la fenêtre de l'application.

## Plusieurs instances Stellio
- Les autres installations du réseau local sont **détectées** et s'ajoutent en un clic (saisissez leur clé locale).
- **Envoyer un fichier** à une autre instance, dans le dossier de votre choix.
- Widget d'état des instances sur le tableau de bord.

## Notifications
- Notifications **Windows** natives, notifications **navigateur** (Pi, mobile).
- **Push** : ntfy, Telegram, Discord ou webhook, même fenêtre fermée (fin d'impression, échec, maintenance, stock).

## Domotique
- **MQTT / Home Assistant** : publication d'état et découverte automatique ; appareil MQTT « Stellio » et capteurs.

@@@ Server-Edition | Édition serveur
# Édition serveur

L'**édition serveur** s'active sur Linux (Raspberry Pi, VM, LXC, Docker) ou avec `STELLIO_HEADLESS=1`. Windows et macOS gardent l'application de bureau. Stellio tourne en arrière-plan et s'utilise depuis un navigateur : `http://<ip>:5000`.

## Raspberry Pi / Linux
Prérequis : Raspberry Pi 4 ou 5 recommandé, Raspberry Pi OS **64 bits**.

`install-pi.sh` installe les dépendances système (`ffmpeg`, `unrar`, bibliothèques de rendu 3D), un environnement Python dédié et un **service systemd** `stellio` qui démarre au boot et redémarre en cas de plantage.

```bash
sudo systemctl status stellio
sudo systemctl restart stellio
sudo journalctl -u stellio -f
```
Peu de RAM ? Augmentez le swap si l'installation des dépendances Python échoue, puis relancez le script.

## Proxmox VE (conteneur LXC)
Le script `stellio-lxc.sh` propose des réglages **par défaut** ou **avancés** (CTID, cœurs, RAM, disque, pont, VLAN, DHCP ou IP fixe, stockage, dossier hôte à monter), puis :
- crée un conteneur **Debian 12 non privilégié** (2 cœurs, 2 Go de RAM, 32 Go de disque, démarrage automatique) ;
- y installe Stellio avec `install-pi.sh` ;
- affiche l'adresse `http://<ip-du-conteneur>:5000` et le mot de passe root.

```bash
pct exec <CTID> -- update-stellio              # mettre à jour
pct exec <CTID> -- journalctl -u stellio -f    # logs
```
- **Mode non interactif** : variables `var_mode=default var_cpu=4 var_ram=4096 var_disk=16 var_ip=192.168.1.50/24 var_gw=192.168.1.1` (liste en tête du script).
- **Stockage** : `var_choose_storage=1`, `var_storage`, `var_template_storage`.
- **Langue** du script : `var_lang=fr` (fr, en, de, es, pt, it, zh, ja).
- **Sources** : dans ce conteneur, seuls les partages **SMB/NFS** sont proposés. Avec `var_mount=/hote:/mnt/modeles`, « Dossier local » est autorisé aussi. Réglage : `/etc/systemd/system/stellio.service.d/sources.conf` (`STELLIO_ALLOWED_SOURCE_TYPES`).

## Garde-fous (1.0.7)
`install-pi.sh` met en place :
- une **surveillance chaque minute** (`stellio-watchdog`) : redémarre Stellio s'il ne répond plus (3 contrôles ratés, 3 minutes de grâce après un démarrage), le relance s'il est arrêté, relance le réseau si l'adresse IP est perdue, nettoie journaux et cache apt si le disque a moins de 300 Mo libres ;
- un service qui **ne renonce jamais** à redémarrer ;
- des plafonds **CPU 75 %**, **RAM 75 % (ralentissement) / 85 % (limite dure)**, priorité basse, et Stellio sacrifié en premier en cas de manque de mémoire ;
- des journaux limités à **100 Mo**.

Interventions de la surveillance : `journalctl -t stellio-watchdog`. Les conteneurs existants reçoivent tout cela avec `update-stellio`.

## Spécificités de l'édition serveur
- ☁️ **IA en ligne** facultative (voir [Intelligence artificielle](fr-AI)).
- 📥 **Profils de slicer** : Stellio ne voit pas les slicers de votre PC et ne se connecte pas aux clouds (Orca Cloud, Bambu Cloud…). Exportez vos profils (OrcaSlicer : Fichier → Exporter → Exporter le lot de préréglages) puis importez-les dans *Réglages → Mes profils de slicer*, ou utilisez un **dossier de profils surveillé** (Syncthing, partage réseau, scp…).
- 🐯 **TigerTag** : connexion officielle par e-mail et mot de passe ; compte Google ? définissez d'abord un mot de passe via « Mot de passe oublié » dans l'app TigerTag. Repli : copier le dossier de données de TigerTag Studio sur le serveur.
- Après une mise à jour, le navigateur se recharge automatiquement.

## Variables d'environnement
| Variable | Rôle |
|---|---|
| `STELLIO_HEADLESS` | Force le mode serveur |
| `STELLIO_PORT` | Port (défaut 5000) |
| `STELLIO_SERVER_URL` | Adresse publique du serveur |
| `STELLIO_DATA_DIR` | Dossier de données |
| `STELLIO_ALLOWED_SOURCE_TYPES` | Types de sources autorisés (`folder,smb,nfs`) |
| `STELLIO_START_MINIMIZED` | Démarrer réduit |
| `STELLIO_NO_AUTO_INSTALL` | Désactive l'installation automatique de modules |

@@@ Settings-and-Data | Réglages et données
# Réglages et données

## Apparence
- **Thème** : Sombre / Clair / Système. Par défaut, **clair** ; sombre seulement si le système (ou vous) le demande.
- **Thèmes de marque** : Stellio, Bambu, Prusa, Voron, Creality ; 33 palettes, couleur d'accent personnalisée, image de fond réglable.
- **Accessibilité** : contraste élevé, animations réduites, focus clavier visible, taille du texte, mode daltonien.
- **8 langues** : fr, en, de, es, it, pt, ja, zh.
- Navigation réordonnable par glisser-déposer ; **annuler le dernier réglage modifié**.

{{img:settings}}

## Raccourcis clavier
| Raccourci | Action |
|---|---|
| `Ctrl+K` | Palette de commandes |
| `Ctrl+F` | Recherche |
| `Ctrl+N` | Nouveau téléchargement |
| `Ctrl+,` | Réglages |
| `Ctrl+Z` | Annuler la dernière suppression |
| `Alt+1-8` | Navigation rapide |
| `Maj+clic` | Sélectionner une plage |
| `↑ ↓ ← →` + `Entrée` | Naviguer et ouvrir |
| `F` | Favoris |
| `T` | Gestionnaire d'étiquettes |
| `?` | Aide des raccourcis |
| `Échap` | Fermer / effacer la recherche |

## Où sont mes données ?
| Système | Dossier |
|---|---|
| Windows | `%APPDATA%\Stellio` |
| macOS / Linux | `~/.stellio` |
| Windows portable | `data` à côté de `Stellio.exe` |
| Personnalisé | variable `STELLIO_DATA_DIR` |

Contenu : base `stellio.db` (SQLite), réglages `app_settings.json`, journal `stellio.log`, modules téléchargés `extra_libs`. Le code reste séparé des données et n'est jamais touché par une mise à jour.

## Sauvegarde
- **Export / import complet** (.zip) des données.
- **Sauvegardes automatiques** programmables.
- **Corbeille** de 5 minutes, journal des opérations avec annulation.
- Mise à jour : jamais de perte de données.

## Journaux et diagnostic
- Le niveau de journal par défaut est **avertissement** ; le fichier `stellio.log` est recréé à chaque démarrage.
- **Mode debug** : activez-le dans les Réglages ; il s'applique au prochain démarrage.
- **Exporter le diagnostic** (Réglages → Diagnostics) : secrets masqués, imprimantes intégrées listées (type, modèle, état — sans nom, adresse ni clé).
- Bloc **Santé de Stellio** : état général de l'application.

## Suggestions et bugs
Depuis l'application : **Suggestions & bugs** dans la barre latérale. Le message devient un ticket GitHub (anonyme, via une GitHub App), avec un badge « Nouvelle réponse ».

@@@ Troubleshooting | Dépannage
# Dépannage

Avant tout : exportez le **diagnostic** (Réglages → Diagnostics) et gardez-le pour un signalement.

## L'écran reste blanc au lancement (macOS)
Le port **5000** est souvent pris par le *Récepteur AirPlay* (réponse 403 dans Safari). Stellio choisit désormais **automatiquement** un port libre (5001–5030). Sinon : Réglages Système → Général → AirDrop et Handoff → désactivez *Récepteur AirPlay*. Journal : `~/.stellio/stellio.log` (vide en niveau normal : activez le mode debug).

## Le conteneur LXC devient injoignable
Depuis le shell Proxmox :
1. `pct status <CTID>` puis `pct start <CTID>` s'il est arrêté.
2. `pvesm status` : **stockage plein** ? C'est la cause la plus fréquente si le stockage est partagé.
3. `pct exec <CTID> -- free -m` et `dmesg -T | grep -i "oom\|killed process"` : manque de mémoire.
4. `pct exec <CTID> -- ip -4 a` : l'IP DHCP a-t-elle changé ? Réservez-la sur le routeur.
5. `pct exec <CTID> -- systemctl status stellio` et `journalctl -u stellio -n 100`.

Depuis la 1.0.7, la surveillance automatique traite les cas courants ; voir `journalctl -t stellio-watchdog`.

## Les miniatures sont lentes ou ne s'affichent pas
- Choisissez *Réglages → Performance des miniatures* : **Éco** sur une petite machine.
- Les fichiers très lourds gardent une miniature de remplacement après un dépassement de délai.
- La génération se met en pause quand vous utilisez l'application : c'est normal.

## Mon imprimante n'est pas détectée
- Vérifiez qu'elle est sur le même réseau (VLAN, Wi-Fi invité).
- Ajoutez-la à la main avec son adresse IP et sa clé.
- Bambu Lab : activez le mode LAN ; Klipper : l'API Moonraker doit être joignable.

## La photo de fin d'impression manque
Activez la case *Photo de fin d'impression* sur l'imprimante (comme la surveillance IA et la prise connectée) et vérifiez que la caméra répond.

## « Module manquant »
Au premier lancement de chaque version, Stellio télécharge les modules manquants. Vérifiez la connexion internet ; ne définissez pas `STELLIO_NO_AUTO_INSTALL` sauf besoin.

## Windows SmartScreen / macOS bloque l'application
Les installateurs ne sont pas signés. Vérifiez le `.sha256`, puis *Informations complémentaires → Exécuter quand même* (Windows) ou clic droit → *Ouvrir* (macOS).

## Obtenir de l'aide
[GitHub Issues](https://github.com/stellio-app/stellio/issues), [Discord](https://discord.gg/ySxpHvS6bd), ou **Suggestions & bugs** dans l'application. Indiquez : version de Stellio, système, étapes pour reproduire, journal exporté.

@@@ Contributing | Contribuer
# Contribuer

Les contributions sont les bienvenues. 🎉

1. **Forkez** le dépôt.
2. Créez votre branche : `git checkout -b feature/MaFonction`.
3. Commitez : `git commit -m "Ajoute MaFonction"`.
4. Poussez : `git push origin feature/MaFonction`.
5. Ouvrez une **Pull Request**.

Règles : respecter le style existant, commenter en français ou en anglais, tester si possible sous Windows, mettre la documentation à jour. Toute nouvelle chaîne d'interface doit être ajoutée dans les **8 fichiers de langue**.

## Technologies
| Composant | Technologie |
|---|---|
| Backend | Python 3.8+, Flask, Waitress |
| Frontend | HTML5, CSS3, JavaScript pur (sans compilation) |
| Base de données | SQLite (mode WAL) |
| Bureau | pywebview (Windows, macOS) / navigateur (serveur) |
| 3D | PyRender, rendu CPU numpy, Three.js |
| Maillage | trimesh, pymeshfix, shapely, rectpack |
| IA | Ollama (local) |
| Réseau | paho-mqtt, smbclient, requests |
| Chiffrement | cryptography (AES) |

## Structure du dépôt
```
stellio/
├── main.py            Noyau Flask : base, auth, bibliothèque, imprimantes, IA, démarrage
├── modules/           Fonctions séparées de main.py (print_session, timelapse, quote_portal…)
├── interface/         index.html, script.js, style.css, management.js (JavaScript pur)
├── packaging/         launcher.py, installateur Windows (.iss), droits macOS
├── languages/         Traductions (8 langues) et changelog.json
├── tests/  tools/     Tests pytest, outils de maintenance
├── release-notes/     notes_version_X.Y.Z.txt
├── install-pi.sh      Installation Raspberry Pi / Linux
└── stellio-lxc.sh     Installation Proxmox LXC
```
Un module déclare les services de `main.py` qu'il utilise (`_REQUIRED`), ses routes (`_ROUTES`) et une fonction `init`. Contrôle avant publication : `python -m pytest tests -q`.

## Sécurité et confidentialité
- Stellio est **local-first** : rien n'est collecté ni envoyé par défaut. Seule exception, si vous l'activez : l'IA en ligne de l'édition serveur.
- Les fichiers de code et de configuration ne sont pas accessibles depuis le navigateur ; API protégée par session et CSRF ; invités en lecture seule ; secrets chiffrés.
- Chaque version est publiée avec une somme `.sha256` vérifiée par la mise à jour intégrée.

## Licence
**GNU AGPL v3** : vous pouvez copier, modifier et distribuer Stellio ; si vous le modifiez ou l'offrez comme service réseau, vous devez publier le code source sous la même licence.

## Partenariat et remerciements
Stellio est partenaire d'intégration officiel de **TigerTag** ([tigersystem.io](https://tigersystem.io)). Merci à Ollama, Flask, Three.js, trimesh, Spoolman et à la communauté des makers. ☕ Soutenir : [Ko-fi](https://ko-fi.com/E6J828RYVD).
