<p align="center">
  <img src="https://stellio-app.com/assets/logo-nom-stellio.png" alt="Logo Stellio" width="360">
</p>

<h3 align="center">Le gestionnaire de fichiers 3D ultime pour les makers et propriétaires d'imprimantes 3D</h3>

<p align="center">
  <a href="https://github.com/stellio-app/stellio/releases"><img src="https://img.shields.io/github/v/release/stellio-app/stellio?color=blue" alt="Version"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python"></a>
  <a href="https://flask.palletsprojects.com/"><img src="https://img.shields.io/badge/flask-3.0+-green.svg" alt="Flask"></a>
  <a href="https://www.gnu.org/licenses/agpl-3.0"><img src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg" alt="License: AGPL v3"></a>
  <a href="https://github.com/stellio-app/stellio/blob/main"><img src="https://img.shields.io/badge/platform-Windows%20%7C%20Raspberry%20Pi%20%2F%20Linux-lightgrey.svg" alt="Platform"></a>
  <a href="https://github.com/stellio-app/stellio/blob/main"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"></a>
</p>

<p align="center">
  <a href="../../README.md">🇬🇧 English</a> |
  🇫🇷 <strong>Français</strong> |
  <a href="README.de.md">🇩🇪 Deutsch</a> |
  <a href="README.es.md">🇪🇸 Español</a> |
  <a href="README.it.md">🇮🇹 Italiano</a> |
  <a href="README.pt.md">🇵🇹 Português</a> |
  <a href="README.ja.md">🇯🇵 日本語</a> |
  <a href="README.zh.md">🇨🇳 中文</a>
</p>

<p align="center">
  <a href="#-installation">🚀 Installation</a> •
  <a href="#-fonctionnalités">✨ Fonctionnalités</a> •
  <a href="#-documentation">📖 Documentation</a> •
  <a href="#-contribuer">🤝 Contribuer</a> •
  <a href="#-licence">📜 Licence</a>
</p>

---

## 🎯 Présentation

**Stellio** est une application de bureau moderne qui centralise toute votre bibliothèque 3D (STL, 3MF, OBJ), automatise les tâches répétitives et s'intègre parfaitement à votre workflow d'impression 3D.

Que vous soyez un maker débutant ou un propriétaire expérimenté gérant plusieurs machines, Stellio vous fait gagner un temps précieux grâce à l'**IA locale** (Ollama), une **gestion intelligente des imprimantes** et une **interface pensée pour la productivité**.

> 💡 **Philosophie** : Vos données restent chez vous. Tout tourne en local.

---

## ✨ Fonctionnalités

### 🏠 Tableau de bord et productivité
- 📊 **Tableau de bord au lancement** : impressions en cours, stock filament faible, dernières impressions et fichiers récents en un coup d'œil
- 🧱 **Entièrement personnalisable** : glisser-déposer et masquage des widgets (12 disponibles : impressions en cours, stock faible, dernier S.O.S Print, suggestions, instances Stellio…)
- ✅ **Checklist « Premiers pas »** pour les nouveaux utilisateurs
- 💡 **Widget « Suggestions »** : repère les fichiers souvent réimprimés mais pas revus récemment, et les profils slicer avec un taux d'échec élevé
- ⌨️ **Palette de commandes (`Ctrl+K`)** : naviguer, lancer une action ou retrouver instantanément un fichier, un tag, une bobine ou un profil slicer
- 🔔 **Centre de notifications (cloche)** : fin d'impression, échec, maintenance à prévoir, stock filament bas et rappels de séchage regroupés au même endroit
- 📺 **Widget flottant** affichant la progression de l'impression en cours, visible sur toutes les pages
- 🧭 **Visite guidée interactive** pour découvrir les fonctionnalités principales, relançable depuis les Paramètres
- ♿ **Accessibilité** : mode contraste élevé, réduction des animations, indicateurs de focus clavier visibles partout

### 📚 Gestion de bibliothèque
- 🗂️ **Sources multiples** : dossiers locaux, fichiers uniques, partages SMB/NFS — les dossiers 3D détectés sur l'ordinateur sont proposés et ajoutables en un clic
- 🖼️ **Miniatures 3D automatiques** via PyRender (rendu haute qualité) ou un rasteriseur CPU numpy (solution de repli), avec effet de chargement et **aperçu agrandi au survol**
- 🏷️ **Tags personnalisés** avec couleurs + auto-tagging par IA, et **tag en un clic sur plusieurs fichiers sélectionnés**
- 🔍 **Recherche sémantique assistée par IA** ("je cherche un support pour...") avec **recherches récentes mémorisées**
- ⭐ **Favoris** et filtres avancés (type, taille, poids, statut d'impression), avec une **alerte de réassort** quand le stock de filament est insuffisant pour vos favoris
- 🧵 **Filtre « Stock de filament »** : ne garde que les fichiers imprimables avec les bobines que vous avez réellement (Spoolman, inventaire manuel, TigerTag), par matière
- 💾 **Filtres sauvegardés** : enregistrez une combinaison de filtres et réutilisez-la en un clic
- 📋 **File « À imprimer bientôt »**, distincte des favoris, réordonnable par glisser-déposer et envoyable directement au slicer
- 🖱️ **Sélection rapide** : sélection par plage (`Maj+clic`) et navigation au clavier (flèches + `Entrée`)
- ✏️ **Renommage en masse** (rechercher/remplacer, préfixe, suffixe, numérotation) avec aperçu avant validation
- ↩️ **Annulation des suppressions** (`Ctrl+Z`) grâce à une corbeille temporaire de 5 minutes — la suppression d'un tag, d'un projet ou d'une source est aussi annulable, sans confirmation bloquante
- 🔗 **Origine du modèle** : lien d'origine, auteur, licence et notes dans la fiche fichier, avec la date de téléchargement le cas échéant
- 🧩 **Projets/Assemblages** : regrouper plusieurs fichiers pour un même objet, avec support multi-plateaux 3MF (navigation entre plateaux dans le viewer)
- 🔁 **Détection de doublons** (exacts et similaires par géométrie)
- 🗜️ **Support des archives** : parcourir et extraire des modèles directement depuis les archives
- 🖱️ **Glisser-déposer de fichiers 3D** depuis l'explorateur — fonctionne sur l'app de bureau et aussi via un navigateur (Raspberry Pi, mobile, accès distant)
- 📊 **Statistiques détaillées** (formats, plateformes, fiabilité des profils)

### 🤖 Intelligence artificielle (Ollama local)
- 🏷️ **Auto-tagging** intelligent des fichiers
- 📝 **Description automatique** des modèles
- 🔎 **Recherche sémantique** en langage naturel
- 📐 **Analyse d'imprimabilité** (détection des porte-à-faux) et **orientations suggérées** (moins de porte-à-faux, contact avec le plateau affiché)
- 🎯 **Recommandation de profil slicer** basée sur la géométrie + l'historique de réussite
- ⏱️ **Estimation du temps d'impression** avant le slicing
- 🩺 **S.O.S Print** : diagnostic de raté d'impression adaptatif, question par question — Stellio pose une question à la fois, réduit une liste d'hypothèses au fur et à mesure de vos réponses (4 questions maximum), puis délivre un diagnostic final ; l'analyse photo est disponible à tout moment, et les conversations sont sauvegardées (réouverture, marquage « résolu »)

### 🖨️ Gestion des imprimantes
- 🔌 Support **OctoPrint**, **Klipper/Moonraker**, **Bambu Lab** (MQTT), **Creality** (WebSocket), **FlashForge**, **Elegoo** (SDCP) et **PrusaLink**
- 📡 **Détection automatique sur le réseau** : Stellio scanne votre réseau local (SSDP pour Bambu Lab, broadcast UDP pour Elegoo/Centauri/FlashForge, sondage ciblé pour Klipper/OctoPrint/PrusaLink/Creality) et vous permet d'ajouter les imprimantes détectées en un clic
- 📡 Suivi en temps réel (températures, progression, caméra)
- 🔧 **Maintenance prédictive** avec suivi des tâches et recommandations par marque (Bambu, Prusa, Creality, etc.)
- 🔩 **Pièces d'usure et consommables** : stock de buses, plateaux, courroies… avec alertes, lié aux tâches de maintenance (chaque intervention décompte une pièce)
- ⏱️ Compteur d'heures d'impression automatique
- 📤 Envoi direct au slicer, avec un sélecteur de bobine pour assigner le bon filament directement depuis la fenêtre d'envoi, ou upload vers l'imprimante
- 👀 **Aperçu rapide** (poids, temps d'impression estimé) directement dans la fenêtre d'envoi au slicer, avant de valider
- 🛡️ **Vérification avant impression renforcée** : alerte si la bobine assignée doit être séchée, si le filament est abrasif (buse en acier trempé conseillée) ou si aucune calibration n'existe pour cette imprimante
- 🔁 **Réimprimer comme la dernière fois** : depuis l'historique, un clic rouvre la fenêtre d'envoi avec la même imprimante, le même profil et la même bobine
- 🎛️ **Calibrations** : enregistrez flow, pressure advance, températures… par filament et par imprimante, rappelées dans la fenêtre d'envoi au slicer
- 👥 **Mode collaboratif léger** : voyez si un autre appareil connecté consulte déjà un fichier, et une alerte évite d'envoyer deux fois le même fichier au slicer par erreur

### 🧵 Gestion du filament
- 🔗 Intégration **Spoolman** (serveur de gestion de bobines), avec détection automatique sur votre réseau
- 🟠 Support **AMS Bambu Lab** (lecture des slots)
- 🟢 Support **CFS Creality**
- 🐯 Intégration **TigerTag** (identification NFC/RFID des bobines) : connectez-vous pour voir vos bobines TigerTag dans l'inventaire, ou laissez Stellio récupérer automatiquement une session TigerTag Studio existante — en lecture seule, ne modifie jamais votre inventaire TigerTag
- ⚪ Bobines manuelles
- 📉 Suivi automatique de la consommation lors de l'envoi au slicer, avec vérification de compatibilité avant impression (quantité suffisante ?)
- 🔔 **Alertes de stock faible** au démarrage, avec un lien rapide pour racheter
- 💨 **Séchage des bobines** : journal de séchage, état (sèche / à sécher) selon la matière, température et durée suggérées, et rappels dans les notifications
- 📈 **Résumé par bobine** : impressions, grammes, coût et écart non suivi dans la fiche de chaque bobine

### 📥 Téléchargement depuis les plateformes
- 🟠 **Printables** (API GraphQL)
- 🟢 **MakerWorld** (connexion Bambu Lab en 2 étapes)
- 🔵 **Thingiverse** (via clé API)
- 🟣 **Nexprint** (bibliothèque de modèles d'Elegoo ; connexion avec l'email et le mot de passe du compte, stockés chiffrés)
- 📁 Téléchargement direct vers vos sources configurées
- 🆕 **Détection de nouvelles versions** : Stellio vérifie chaque jour si les modèles téléchargés (Printables, MakerWorld, Thingiverse) ont été mis à jour
- 🛒 **Liens utiles** : boutiques, constructeurs, sites de modèles 3D et ressources regroupés en sections dépliantes

### 🧩 Outils avancés
- 🎨 **Nesting automatique sur plateau** (rectpack ou silhouette réelle via shapely)
- 🔧 **Réparation de mesh** (trimesh + pymeshfix) avec **comparatif avant/après** (étanchéité, triangles, sommets, taille)
- 🔄 **Convertisseur de format** (STL ↔ 3MF ↔ OBJ)
- 🛡️ **Vérification d'intégrité** (fichiers corrompus/manquants)
- 💰 **Calcul du coût d'impression** : matière, électricité, usure machine (par heure), frais fixes, marge en % et quantité — prix unitaire et total calculés au centime
- 🧾 **Devis PDF** : générés depuis le calcul de coût, avec client, désignation et notes personnalisables ; en-tête de devis configurable (nom/société, logo, adresse, téléphone, e-mail, site web, SIRET / N° TVA) et mentions légales en pied de page
- 🌱 **Estimation environnementale** : empreinte CO₂ de vos impressions (matière + électricité)
- 📸 **Galerie photo d'impressions** (réussies/échouées)
- 🕒 **Historique** avec notation succès/échec (nourrit l'IA), boutons **« Voir le fichier »** et **« Réimprimer »** sur chaque ligne (avec détection des fichiers déplacés/supprimés), et filtres par plateforme, résultat (réussi/raté/partiel/non noté) et plage de dates

### 📈 Rapports et fiabilité
- 🧮 **Fiabilité d'impression** : taux de réussite et coût des échecs classés par profil slicer, matière, imprimante ou bobine
- 🗓️ **Rapport mensuel** : impressions, taux de réussite, filament, coût, échecs et CO₂ du mois, comparés au mois précédent, exportable en PDF

### 🔔 Notifications
- 🪟 **Notifications natives Windows**
- 🌐 **Notifications navigateur** activables pour un accès via Raspberry Pi ou mobile
- 📣 **Notifications push** (ntfy, Telegram, Discord ou webhook) : fin et échec d'impression détectés même fenêtre fermée, ainsi que les alertes de maintenance et de stock

### 🌐 Accès mobile et à distance
- 📱 **QR code** pour accéder à votre bibliothèque depuis mobile (PWA installable)
- 📲 **App compagnon Android** : un QR code dédié permet de télécharger et installer l'APK de l'app compagnon Stellio directement depuis les paramètres d'accès mobile, avec la possibilité de prendre des photos directement depuis une impression
- 🌍 **Accès à distance** via Cloudflare Tunnel (gratuit, URL aléatoire ou fixe), ou **adresse personnalisée** (nom de domaine, DynDNS, VPN, Tailscale…) pour se passer de Cloudflare, avec retour à Cloudflare en un clic
- 🔗 **Liens de partage** temporaires (24h, usage unique)

### 👥 Comptes et multi-instance
- 🔐 **Comptes locaux** avec code de récupération et question secrète : réinitialisation du mot de passe 100 % locale, sans e-mail ni internet
- 👤 **Comptes invités en lecture seule** : partagez votre bibliothèque, vos imprimantes et votre stock sans aucun risque
- 🔄 **Instances Stellio** : détection automatique des autres installations sur le réseau local, ajout en un clic (il ne reste qu'à saisir leur clé locale)
- 📨 **Envoi de fichier vers une autre instance** : choix du dossier de destination sur l'instance cible, le fichier reçu apparaît immédiatement dans sa bibliothèque
- ✅ **Widget d'état des instances** sur le tableau de bord (coche verte ou croix rouge pour chaque instance enregistrée)

### 🎨 Personnalisation
- 🌓 Thèmes : Sombre / Clair / Système
- 🎨 Thèmes de marque : Stellio, Bambu, Prusa, Voron, Creality
- 🎯 Couleur d'accent personnalisée
- 🌍 **8 langues** : FR, EN, DE, ES, IT, PT, JA, ZH
- 🧲 Réorganisation de la navigation par glisser-déposer
- ↩️ **Annulation des paramètres** : revenez sur le tout dernier changement de configuration effectué

### 💾 Sauvegarde et mises à jour
- 📦 Export/import de sauvegarde complète (.zip)
- 🔄 Mises à jour automatiques depuis GitHub (patch `.zip` — même mécanisme sur Windows et Raspberry Pi/Linux)
- 🔁 Redémarrage fiable après une mise à jour ou l'activation du mode debug, sur Windows comme sur Raspberry Pi/Linux
- 📋 Export de logs de diagnostic (secrets masqués)
- 💬 **Suggestions et signalements depuis l'app** : envoyez une suggestion ou un bug sans quitter Stellio — une issue GitHub est créée pour vous (de façon anonyme, via une application GitHub dédiée), avec un lien vers l'issue et un badge « Nouvelle réponse » quand vous recevez une réponse

---

## 🖼️ Captures d'écran

| | |
|---|---|
| ![Bibliothèque](../../library.png) *Bibliothèque avec miniatures* | ![Imprimantes](../../monitoring.png) *Suivi d'imprimante* |
| ![Slicer](../../slicer.png) *Recommandation de profil par IA* | ![Nesting](../../nesting.png) *Nesting automatique* |

---

## 🚀 Installation

### 🪟 Windows (recommandé)

1. Téléchargez le dernier installeur depuis les [Releases](https://github.com/stellio-app/stellio/releases)
2. Lancez `Stellio-Setup-<version>.exe`
3. C'est fait ! 🎉

### 🐧 Raspberry Pi / Linux

Fonctionne en **mode serveur headless** (sans interface graphique) : Stellio tourne en arrière-plan et se pilote depuis un navigateur, que ce soit sur le Pi lui-même ou depuis n'importe quel appareil du réseau local.

**Prérequis** : Raspberry Pi 4 ou 5 recommandé, Raspberry Pi OS **64 bits**.

```bash
curl -O https://raw.githubusercontent.com/stellio-app/stellio/main/install-pi.sh
chmod +x install-pi.sh
./install-pi.sh
```

Le script installe automatiquement :
- les dépendances système (`ffmpeg`, `unrar`, bibliothèques de rendu 3D)
- un environnement virtuel Python dédié
- un **service systemd** (`stellio.service`) qui démarre Stellio au boot et le redémarre automatiquement en cas de crash

Une fois installé, Stellio est accessible sur `http://<ip-du-pi>:5000`.

```bash
sudo systemctl status stellio     # Statut du service
sudo systemctl restart stellio    # Redémarrer
sudo journalctl -u stellio -f     # Suivre les logs en direct
```

> 💡 **Mêmes mises à jour que sur Windows** : le patch `.zip` publié à chaque version est identique sur les deux plateformes (code source pur, rien de compilé). Stellio le détecte et l'applique automatiquement, puis redémarre le service — aucune réinstallation manuelle nécessaire.
>
> 🎥 Mêmes fonctionnalités que la version Windows, à l'exception de la fenêtre de bureau native (remplacée par l'accès navigateur) et de l'IA Ollama locale, qui nécessite un modèle raisonnablement performant pour bien tourner sur un Pi — pointez `ollama_url` vers un serveur Ollama distant dans les Paramètres si besoin.

### Slicers supportés

Stellio détecte automatiquement :
- ✅ OrcaSlicer
- ✅ Bambu Studio
- ✅ PrusaSlicer / SuperSlicer
- ✅ Ultimaker Cura
- ✅ Creality Print

### Imprimantes

| Type | Protocole | Fonctionnalités |
|---|---|---|
| OctoPrint / PrusaLink | API HTTP | Suivi, upload, caméra |
| Klipper/Moonraker | API HTTP | Suivi, upload, caméra, heures exactes |
| Bambu Lab | MQTT (cloud + LAN) | Suivi temps réel, AMS, caméra (JPEG A1/P1, RTSPS X1/X2/H2), détection SSDP |
| Creality | WebSocket | Suivi, CFS, détection UDP |
| FlashForge | API propriétaire | Suivi, détection UDP |
| Elegoo | SDCP sur WebSocket | Suivi, détection UDP |

---

## 🛠️ Technologie

| Composant | Technologie |
|---|---|
| Backend | Python 3.8+, Flask, Waitress |
| Frontend | HTML5, CSS3, JavaScript vanilla |
| Base de données | SQLite (mode WAL) |
| Bureau | pywebview (Windows) / mode navigateur headless (Raspberry Pi, Linux) |
| Rendu 3D | PyRender, rasteriseur CPU numpy, Three.js |
| Mesh et nesting | trimesh, pymeshfix, shapely, rectpack |
| IA | Ollama (local) |
| Réseau | paho-mqtt, smbclient, requests |
| Chiffrement | cryptography (AES, IV aléatoire par appel) |
| Archives | zipfile, rarfile, py7zr, tarfile |

---

## 📖 Documentation

### Raccourcis clavier

| Raccourci | Action |
|---|---|
| `Ctrl+K` | Palette de commandes |
| `Ctrl+F` | Recherche |
| `Ctrl+N` | Nouveau téléchargement |
| `Ctrl+,` | Paramètres |
| `Ctrl+Z` | Annuler la dernière suppression (corbeille de 5 min) |
| `Alt+1-8` | Navigation rapide |
| `Maj+Clic` | Sélectionner une plage de fichiers |
| `↑ ↓ ← →` + `Enter` | Naviguer et ouvrir les fichiers dans la bibliothèque |
| `F` | Basculer les favoris |
| `T` | Gestionnaire de tags |
| `?` | Aide raccourcis |
| `Échap` | Fermer la modale / vider la recherche |

### Structure du projet

```
stellio/
├── main.py             # Backend Flask + Desktop
├── script.js           # JavaScript frontend
├── index.html          # Interface principale
├── style.css           # Styles
├── launcher.py         # Lanceur léger / bootstrap runtime
├── check_deps.py       # Vérificateur de dépendances auto-réparant
├── worker.py           # Squelette de worker 3MF non utilisé (provisoire)
├── assets/             # Logos, icônes
├── languages/          # Fichiers de traduction (JSON)
├── apk/                # Package de l'app compagnon Android
├── docs/               # Documentation, politique de confidentialité, READMEs traduits
├── requirements.txt    # Dépendances Python
└── install-pi.sh       # Script d'installation Raspberry Pi / Linux (service systemd)
```

Une idée ? [Ouvrez une issue](https://github.com/stellio-app/stellio/issues) !

---

## 🤝 Contribuer

Les contributions sont les bienvenues ! 🎉

1. **Forkez** le projet
2. Créez votre branche (`git checkout -b feature/MaSuperFonctionnalite`)
3. Commitez vos changements (`git commit -m 'Ajout de MaSuperFonctionnalite'`)
4. Poussez la branche (`git push origin feature/MaSuperFonctionnalite`)
5. Ouvrez une **Pull Request**

### Recommandations
- Respectez le style de code existant
- Ajoutez des commentaires en français ou en anglais
- Testez vos changements sur Windows si possible
- Mettez à jour la documentation si nécessaire

### Signaler un bug

Le plus simple est de le faire directement depuis l'app : ouvrez **Suggestions & bugs** dans la barre latérale et décrivez le problème — il est envoyé sous forme d'issue GitHub à votre place. Vous pouvez aussi ouvrir une issue vous-même sur GitHub.

Utilisez le modèle de rapport de bug et incluez :
- La version de Stellio
- Le système d'exploitation
- Les étapes de reproduction
- Les logs d'erreur (exportables depuis Paramètres → Diagnostic)

---

## 📜 Licence

Ce projet est sous licence **GNU Affero General Public License v3.0** — voir le fichier [LICENSE](../../LICENSE) pour les détails.

> 💡 **En résumé** : vous êtes libre de copier, modifier et distribuer ce logiciel. Si vous modifiez Stellio ou l'utilisez pour proposer un service hébergé en réseau, vous devez publier le code source complet sous la même licence AGPLv3.

---

## 🔒 Confidentialité

Stellio est local-first : vos données restent sur votre machine, rien n'est collecté ni envoyé vers des serveurs externes par défaut. Consultez notre [Politique de confidentialité](../privacy/PRIVACY.md) pour tous les détails.

---

## 🔏 Politique de signature de code

L'installeur Windows et l'AppImage Linux publiés dans les [Releases](https://github.com/stellio-app/stellio/releases) ne sont **pas encore signés numériquement** : Windows SmartScreen peut afficher un avertissement. Les builds macOS ne sont pas notarisés. Chaque fichier d'une release est accompagné d'une somme de contrôle SHA-256 (`.sha256`) que vous pouvez vérifier, et le système de mise à jour intégré la contrôle avant d'installer. Voir [CODE_SIGNING_POLICY.md](../../CODE_SIGNING_POLICY.md) pour l'état actuel, la vérification d'un téléchargement et nos projets de signature.

---

## 🙏 Remerciements

- [Ollama](https://ollama.com/) pour l'IA locale
- [Flask](https://flask.palletsprojects.com/) pour le backend
- [Three.js](https://threejs.org/) pour le rendu 3D web
- [trimesh](https://github.com/mikedh/trimesh) pour le traitement de mesh
- [Spoolman](https://github.com/Donkie/Spoolman) pour la gestion des bobines de filament
- [TigerTag](https://tigersystem.io) pour l'identification NFC/RFID des filaments
- La communauté des makers pour ses retours et suggestions
- Tous les contributeurs ❤️

---

## 📞 Contact et support

- 🐛 **Signaler un bug** : [GitHub Issues](https://github.com/stellio-app/stellio/issues) ou directement depuis l'app (**Suggestions & bugs**)
- 💡 **Demande de fonctionnalité** : [GitHub Discussions](https://github.com/stellio-app/stellio/discussions)
- 📧 **Email** : contact@stellio-app.com
- 🌐 **Site web** : [stellio-app.com](https://stellio-app.com)

---

## ⭐ Soutenir le projet

Si Stellio vous est utile, pensez à :
- Lui mettre une **star** ⭐ sur GitHub
- Partager le projet autour de vous
- [Contribuer au code](#-contribuer) ou aux traductions
- Signaler des bugs pour aider à améliorer l'app
- Soutenir le développement avec un petit don sur Ko-fi ☕

<p align="center">
  <a href="https://ko-fi.com/E6J828RYVD">
    <img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="Soutenir Stellio sur Ko-fi">
  </a>
</p>

---

<p align="center"><strong>Fait avec ❤️ pour la communauté des makers</strong></p>

<p align="center">
  <a href="https://github.com/stellio-app/stellio">⭐ Star ce dépôt</a> •
  <a href="https://github.com/stellio-app/stellio/issues">🐛 Signaler un bug</a> •
  <a href="https://github.com/stellio-app/stellio/discussions">💡 Proposer une fonctionnalité</a>
</p>
