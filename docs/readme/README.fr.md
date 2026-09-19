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

### 📚 Gestion de bibliothèque
- 🗂️ **Sources multiples** : dossiers locaux, fichiers uniques, partages SMB/NFS
- 🖼️ **Miniatures 3D automatiques** via PyRender (rendu haute qualité) ou un rasteriseur CPU numpy (solution de repli)
- 🏷️ **Tags personnalisés** avec couleurs + auto-tagging par IA
- 🔍 **Recherche sémantique assistée par IA** ("je cherche un support pour...")
- ⭐ **Favoris** et filtres avancés (type, taille, poids, statut d'impression)
- 🧩 **Projets/Assemblages** : regrouper plusieurs fichiers pour un même objet, avec support multi-plateaux 3MF (navigation entre plateaux dans le viewer)
- 🔁 **Détection de doublons** (exacts et similaires par géométrie)
- 📊 **Statistiques détaillées** (formats, plateformes, fiabilité des profils)

### 🤖 Intelligence artificielle (Ollama local)
- 🏷️ **Auto-tagging** intelligent des fichiers
- 📝 **Description automatique** des modèles
- 🔎 **Recherche sémantique** en langage naturel
- 📐 **Analyse d'imprimabilité** (détection des porte-à-faux)
- 🎯 **Recommandation de profil slicer** basée sur la géométrie + l'historique de réussite
- 🩺 **S.O.S Print** : diagnostic de raté d'impression adaptatif, question par question — Stellio pose une question à la fois, réduit une liste d'hypothèses au fur et à mesure de vos réponses (4 questions maximum), puis délivre un diagnostic final ; l'analyse photo est disponible à tout moment

### 🖨️ Gestion des imprimantes
- 🔌 Support **OctoPrint**, **Klipper/Moonraker**, **Bambu Lab** (MQTT), **Creality** (WebSocket), **FlashForge**
- 📡 **Détection automatique sur le réseau** : Stellio scanne votre réseau local (SSDP pour Bambu Lab, broadcast UDP pour Elegoo/Centauri/FlashForge, sondage ciblé pour Klipper/OctoPrint/PrusaLink/Creality) et vous permet d'ajouter les imprimantes détectées en un clic
- 📡 Suivi en temps réel (températures, progression, caméra)
- 🔧 **Maintenance prédictive** avec suivi des tâches et recommandations par marque (Bambu, Prusa, Creality, etc.)
- ⏱️ Compteur d'heures d'impression automatique
- 📤 Envoi direct au slicer, avec un sélecteur de bobine pour assigner le bon filament directement depuis la fenêtre d'envoi, ou upload vers l'imprimante

### 🧵 Gestion du filament
- 🔗 Intégration **Spoolman** (serveur de gestion de bobines)
- 🏷️ Intégration de l'inventaire **TigerTag** (lecture seule)
- 🟠 Support **AMS Bambu Lab** (lecture des slots)
- 🟢 Support **CFS Creality**
- ⚪ Bobines manuelles
- 📉 Suivi automatique de la consommation lors de l'envoi au slicer, avec vérification de compatibilité avant impression (quantité suffisante ?)
- 🔔 **Alertes de stock faible** au démarrage, avec un lien rapide pour racheter

### 📥 Téléchargement depuis les plateformes
- 🟠 **Printables** (API GraphQL)
- 🟢 **MakerWorld** (connexion Bambu Lab en 2 étapes)
- 🔵 **Thingiverse** (via clé API)
- 🟣 **Cults3D**
- 📁 Téléchargement direct vers vos sources configurées

### 🧩 Outils avancés
- 🎨 **Nesting automatique sur plateau** (rectpack ou silhouette réelle via shapely)
- 🔧 **Réparation de mesh** (trimesh + pymeshfix)
- 🔄 **Convertisseur de format** (STL ↔ 3MF ↔ OBJ)
- 🛡️ **Vérification d'intégrité** (fichiers corrompus/manquants)
- 💰 **Calcul du coût d'impression** (matière + électricité)
- 📸 **Galerie photo d'impressions** (réussies/échouées)
- 🕒 **Historique** avec notation succès/échec (nourrit l'IA)

### 🌐 Accès mobile et à distance
- 📱 **QR code** pour accéder à votre bibliothèque depuis mobile (PWA installable)
- 📲 **App compagnon Android** : un QR code dédié permet de télécharger et installer l'APK de l'app compagnon Stellio directement depuis les paramètres d'accès mobile
- 🌍 **Accès à distance** via Cloudflare Tunnel (gratuit, URL aléatoire ou fixe)
- 🔗 **Liens de partage** temporaires (24h, usage unique)

### 🎨 Personnalisation
- 🌓 Thèmes : Sombre / Clair / Système
- 🎨 Thèmes de marque : Stellio, Bambu, Prusa, Voron, Creality
- 🎯 Couleur d'accent personnalisée
- 🌍 **8 langues** : FR, EN, DE, ES, IT, PT, JA, ZH
- 🧲 Réorganisation de la navigation par glisser-déposer

### 💾 Sauvegarde et mises à jour
- 📦 Export/import de sauvegarde complète (.zip)
- 🔄 Mises à jour automatiques depuis GitHub (patch `.zip` — même mécanisme sur Windows et Raspberry Pi/Linux)
- 📋 Export de logs de diagnostic (secrets masqués)

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
2. Lancez `Stellio-Setup.exe`
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
- les dépendances système (`ffmpeg`, `unrar-free`, bibliothèques de rendu 3D)
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
| `Ctrl+F` | Recherche |
| `Ctrl+N` | Nouveau téléchargement |
| `Ctrl+,` | Paramètres |
| `Alt+1-8` | Navigation rapide |
| `F` | Basculer les favoris |
| `T` | Gestionnaire de tags |
| `?` | Aide raccourcis |
| `Échap` | Fermer la modale / vider la recherche |

### Structure du projet

```
stellio/
├── main.py                 # Backend Flask + Desktop
├── script.js                # JavaScript frontend
├── index.html                # Interface principale
├── style.css                  # Styles
├── launcher.py                  # Lanceur léger / bootstrap runtime
├── check_deps.py                 # Vérificateur de dépendances auto-réparant
├── worker.py                       # Worker en arrière-plan (miniatures, scans)
├── assets/                          # Logos, icônes
├── languages/                        # Fichiers de traduction (JSON)
├── apk/                                # Package de l'app compagnon Android
├── docs/                                # Documentation, politique de confidentialité, READMEs traduits
├── requirements.txt                      # Dépendances Python
├── install-pi.sh                          # Script d'installation Raspberry Pi / Linux (service systemd)
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

Les exécutables Windows publiés dans les [Releases](https://github.com/stellio-app/stellio/releases) sont signés numériquement. Voir [CODE_SIGNING_POLICY.md](../../CODE_SIGNING_POLICY.md) pour le détail de notre procédure de signature et la protection de la clé privée.

---

## 🙏 Remerciements

- [Ollama](https://ollama.com/) pour l'IA locale
- [Flask](https://flask.palletsprojects.com/) pour le backend
- [Three.js](https://threejs.org/) pour le rendu 3D web
- [trimesh](https://github.com/mikedh/trimesh) pour le traitement de mesh
- La communauté des makers pour ses retours et suggestions
- Tous les contributeurs ❤️

---

## 📞 Contact et support

- 🐛 **Signaler un bug** : [GitHub Issues](https://github.com/stellio-app/stellio/issues)
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

---

<p align="center"><strong>Fait avec ❤️ pour la communauté des makers</strong></p>

<p align="center">
  <a href="https://github.com/stellio-app/stellio">⭐ Star ce dépôt</a> •
  <a href="https://github.com/stellio-app/stellio/issues">🐛 Signaler un bug</a> •
  <a href="https://github.com/stellio-app/stellio/discussions">💡 Proposer une fonctionnalité</a>
</p>
