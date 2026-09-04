<div align="center">

#  <img src="https://stellio-app.com/assets/logo-nom-stellio.png" alt="Stellio Logo" width="200"/>

### Le gestionnaire de fichiers 3D ultime pour makers et imprimeurs 3D

[![Version](https://img.shields.io/github/v/release/stellio-app/stellio?color=blue)](https://github.com/stellio-app/stellio/releases)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Raspberry%20Pi%20%2F%20Linux-lightgrey.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)]()

[🇬🇧 English](../../README.md) | 🇫🇷 **Français** | [🇩🇪 Deutsch](docs/readme/README.de.md) | [🇪🇸 Español](docs/readme/README.es.md) | [🇮🇹 Italiano](docs/readme/README.it.md) | [🇵🇹 Português](docs/readme/README.pt.md) | [🇯🇵 日本語](docs/readme/README.ja.md) | [🇨🇳 中文](docs/readme/README.zh.md)

[🚀 Installation](#-installation) • [✨ Fonctionnalités](#-fonctionnalités) • [📖 Documentation](#-documentation) • [🤝 Contribuer](#-contribuer) • [📜 Licence](#-licence)

</div>

---

## 🎯 Présentation

**Stellio** est une application desktop moderne qui centralise toute votre bibliothèque 3D (STL, 3MF, OBJ), automatise les tâches répétitives et s'intègre parfaitement à votre flux de travail d'impression 3D.

Que vous soyez maker débutant ou imprimeur expérimenté avec plusieurs machines, Stellio vous fait gagner un temps précieux grâce à l'**IA locale** (Ollama), la **gestion intelligente des imprimantes** et une **interface pensée pour la productivité**.

> 💡 **Philosophie** : Vos données restent chez vous. Tout fonctionne en local.

---

## ✨ Fonctionnalités

### 📚 Gestion de bibliothèque
- 🗂️ **Sources multiples** : dossiers locaux, fichiers uniques, partages SMB/NFS
- 🖼️ **Miniatures 3D automatiques** via PyRender (rendu haute qualité) ou Matplotlib (fallback)
- 🏷️ **Tags personnalisés** avec couleurs + auto-tagging IA
- 🔍 **Recherche sémantique** assistée par IA ("je cherche un support pour...")
- ⭐ **Favoris** et filtres avancés (type, taille, poids, statut d'impression)
- 🧩 **Projets/Assemblages** : regroupez plusieurs fichiers pour un même objet
- 📊 **Statistiques** détaillées (formats, plateformes, fiabilité des profils)

### 🤖 Intelligence Artificielle (Ollama local)
- 🏷️ **Auto-tagging** intelligent des fichiers
- 📝 **Description automatique** des modèles
- 🔎 **Recherche sémantique** en langage naturel
- 🎯 **Recommandation de profil slicer** basée sur la géométrie + historique de réussite
- 🩺 **S.O.S Print** : diagnostic d'échec d'impression (avec analyse photo)

### 🖨️ Gestion des imprimantes
- 🔌 Support **OctoPrint**, **Klipper/Moonraker**, **Bambu Lab** (MQTT)
- 📡 Monitoring temps réel (températures, progression, caméra)
- 🔧 **Maintenance prédictive** avec recommandations par marque (Bambu, Prusa, Creality, etc.)
- ⏱️ Compteur d'heures d'impression automatique
- 📤 Envoi direct au slicer ou upload vers l'imprimante

### 🧵 Gestion du filament
- 🔗 Intégration **Spoolman** (serveur de gestion de bobines)
- 🟠 Support **AMS Bambu Lab** (lecture des slots)
- 🟢 Support **CFS Creality**
- ⚪ Bobines manuelles
- 📉 Décompte automatique à l'envoi au slicer
- ✅ Vérification de compatibilité (quantité suffisante ?)

### 📥 Téléchargement depuis plateformes
- 🟠 **Printables** (API GraphQL)
- 🟢 **MakerWorld** (login 2 étapes Bambu Lab)
- 🔵 **Thingiverse** (via clé API)
- 📁 Téléchargement direct vers vos sources configurées

### 🧩 Outils avancés
- 🎨 **Nesting automatique** du plateau (rectpack ou silhouette réelle via shapely)
- 🔧 **Réparation de maillage** (trimesh + pymeshfix)
- 🔄 **Convertisseur de formats** (STL ↔ 3MF ↔ OBJ)
- 🛡️ **Vérification d'intégrité** (fichiers corrompus/manquants)
- 💰 **Calcul du coût d'impression** (matériau + électricité)
- 📸 **Galerie de photos** d'impression (réussies/ratées)
- 🕒 **Historique** avec notation réussi/raté (nourrit l'IA)
- 🔍 **Détection de doublons** (exacts et similaires par géométrie)

### 🌐 Accès distant & mobile
- 📱 **QR Code** pour accès mobile (PWA installable)
- 🌍 **Accès distant** via Cloudflare Tunnel (gratuit, URL aléatoire ou fixe)
- 🔗 **Liens de partage** temporaires (24h, usage unique)

### 🎨 Personnalisation
- 🌓 Thèmes : Sombre / Clair / Système
- 🎨 Thèmes de marque : Stellio, Bambu, Prusa, Voron, Creality
- 🎯 Couleur d'accent personnalisée
- 🌍 **8 langues** : FR, EN, DE, ES, IT, PT, JA, ZH
- 🧲 Réorganisation drag & drop de la navigation

### 💾 Sauvegarde & Mises à jour
- 📦 Export/Import de sauvegarde complète (.zip)
- 🔄 Mises à jour automatiques depuis GitHub (patch `.zip` — même mécanisme sur Windows et Raspberry Pi/Linux)
- 📋 Export de logs de diagnostic (secrets masqués)

---

## 🖼️ Screenshots

<div align="center">
<table>
<tr></tr>
<td><img src="../../library.png" alt="Bibliothèque" width="400"/><br><em>Bibliothèque avec miniatures</em></td>
<td><img src="../../monitoring.png" alt="Imprimantes" width="400"/><br><em>Monitoring imprimantes</em></td>
</tr>
<tr>
<td><img src="../../slicer.png" alt="Slicer" width="400"/><br><em>Recommandation IA de profil</em></td>
<td><img src="../../nesting.png" alt="Nesting" width="400"/><br><em>Nesting automatique</em></td>
</tr>
</table>
</div>

---

## 🚀 Installation

### 🪟 Windows (recommandé)

1. Téléchargez le dernier installateur depuis les [Releases](https://github.com/stellio-app/stellio-app/releases)
2. Lancez `Stellio-Setup.exe`
3. C'est tout ! 🎉

### 🐧 Raspberry Pi / Linux

Fonctionne en mode **serveur headless** (sans interface graphique) : Stellio tourne en arrière-plan et s'utilise depuis un navigateur, sur le Pi lui-même ou depuis n'importe quel appareil du réseau local.

**Prérequis** : Raspberry Pi 4 ou 5 recommandé, Raspberry Pi OS **64 bits**.

```bash
curl -O https://raw.githubusercontent.com/stellio-app/stellio-app/main/install-pi.sh
chmod +x install-pi.sh
./install-pi.sh
```

Le script installe automatiquement :
- les dépendances système (`ffmpeg`, `unrar-free`, librairies de rendu 3D)
- un environnement virtuel Python dédié
- un **service systemd** (`stellio.service`) qui démarre Stellio au boot et le relance automatiquement en cas de crash

Une fois installé, Stellio est accessible sur `http://<ip-du-pi>:5000`.

```bash
sudo systemctl status stellio     # État du service
sudo systemctl restart stellio    # Redémarrer
sudo journalctl -u stellio -f     # Suivre les logs en direct
```

> 💡 **Mêmes mises à jour que sous Windows** : le patch `.zip` publié sur chaque release est le même pour les deux plateformes (code source pur, rien de compilé). Stellio le détecte et l'applique tout seul, puis redémarre le service — pas de réinstallation manuelle à faire.

> 🎥 Fonctionnalités identiques à la version Windows, à l'exception de la fenêtre desktop native (remplacée par l'accès navigateur) et de l'IA locale Ollama, qui nécessite un modèle raisonnable pour tourner correctement sur un Pi — pointez `ollama_url` vers un serveur Ollama distant dans les Paramètres si besoin.

### Slicers supportés

Stellio détecte automatiquement :
- ✅ OrcaSlicer
- ✅ Bambu Studio
- ✅ PrusaSlicer / SuperSlicer
- ✅ Ultimaker Cura
- ✅ Creality Print

### Imprimantes

| Type | Protocole | Fonctionnalités |
|------|-----------|-----------------|
| OctoPrint | HTTP API | Monitoring, upload, caméra |
| Klipper/Moonraker | HTTP API | Monitoring, upload, caméra, heures exactes |
| Bambu Lab | MQTT | Monitoring temps réel, AMS, caméra (JPEG A1/P1, RTSPS X1/X2/H2) |

---

## 🛠️ Technologies

| Composant | Technologie |
|-----------|-------------|
| Backend | Python 3.8+, Flask, Waitress |
| Frontend | HTML5, CSS3, JavaScript vanilla |
| Base de données | SQLite (WAL mode) |
| Desktop | pywebview (Windows) / mode headless navigateur (Raspberry Pi, Linux) |
| Rendu 3D | PyRender, Matplotlib, Three.js |
| Maillage | trimesh, pymeshfix, shapely |
| IA | Ollama (local) |
| Réseau | paho-mqtt, smbclient, requests |
| Chiffrement | cryptography (AES-CFB) |
| Archives | zipfile, rarfile, py7zr, tarfile |

---

## 📖 Documentation

### Raccourcis clavier

| Raccourci | Action |
|-----------|--------|
| `Ctrl+F` | Rechercher |
| `Ctrl+N` | Nouveau téléchargement |
| `Ctrl+,` | Paramètres |
| `Alt+1-8` | Navigation rapide |
| `F` | Toggle favoris |
| `T` | Gestionnaire de tags |
| `?` | Aide raccourcis |
| `Échap` | Fermer modale / vider recherche |

### Structure du projet
```
stellio-app/
├── main.py                 # Backend Flask + Desktop
├── script.js                # Frontend JavaScript
├── index.html                # Interface principale
├── style.css                  # Styles
├── assets/                     # Logos, icônes
├── languages/                   # Fichiers de traduction (JSON)
├── requirements-pi.txt           # Dépendances Python (installation Raspberry Pi / Linux)
├── install-pi.sh                  # Script d'installation Raspberry Pi / Linux (service systemd)
```

---

Vous avez une idée ? [Ouvrez une issue](https://github.com/stellio-app/stellio-app/issues) !

---

## 🤝 Contribuer

Les contributions sont les bienvenues ! 🎉

1. **Fork** le projet
2. Créez votre branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une **Pull Request**

### Guidelines
- Respectez le style de code existant
- Ajoutez des commentaires en français ou anglais
- Testez vos modifications sur Windows si possible
- Mettez à jour la documentation si nécessaire

### Signaler un bug
Utilisez le template de bug report et incluez :
- Version de Stellio
- Système d'exploitation
- Étapes pour reproduire
- Logs d'erreur (exportables depuis Paramètres → Diagnostic)

---

## 📜 Licence

Ce projet est sous licence libre **GNU Affero General Public License v3.0** - consultez le fichier [LICENSE](./LICENSE) pour plus de détails.

> 💡 **En résumé** : Vous êtes libre de copier, modifier et distribuer ce logiciel. Si vous modifiez Stellio ou l'utilisez pour fournir un service hébergé sur un réseau, vous devez publier l'intégralité du code source sous la même licence AGPLv3.

---

## 🔒 Confidentialité

Stellio est « local-first » : vos données restent sur votre machine, rien n'est collecté ni envoyé vers des serveurs externes par défaut. Consultez notre [Politique de confidentialité](./docs/privacy/PRIVACY.fr.md) pour tous les détails.

---

## 🔏 Politique de signature de code

Les exécutables Windows publiés dans les [Releases](https://github.com/stellio-app/stellio-app/releases) sont signés numériquement. Consultez [CODE_SIGNING_POLICY.md](./CODE_SIGNING_POLICY.md) pour plus de détails sur notre processus de signature et la protection de la clé privée.

---

## 🙏 Remerciements

- [Ollama](https://ollama.com/) pour l'IA locale
- [Flask](https://flask.palletsprojects.com/) pour le backend
- [Three.js](https://threejs.org/) pour le rendu 3D web
- [trimesh](https://github.com/mikedh/trimesh) pour le traitement de maillage
- La communauté maker pour les retours et suggestions
- Tous les contributeurs ❤️

---

## 📞 Contact & Support

- 🐛 **Bug report** : [GitHub Issues](https://github.com/stellio-app/stellio-app/issues)
- 💡 **Feature request** : [GitHub Discussions](https://github.com/stellio-app/stellio-app/discussions)
- 📧 **Email** : contact@stellio-app.com
- 🌐 **Site web** : [stellio-app.com](https://stellio-app.com)

---

## ⭐ Soutenir le projet

Si Stellio vous est utile, pensez à :
- Mettre une **étoile** ⭐ sur GitHub
- Partager le projet autour de vous
- [Contribuer au code](#-contribuer) ou à la traduction
- Signaler des bugs pour améliorer l'application

---

<div align="center">

**Fait avec ❤️ pour la communauté maker**

[⭐ Star this repo](https://github.com/stellio-app/stellio-app) • [🐛 Report a bug](https://github.com/stellio-app/stellio-app/issues) • [💡 Request a feature](https://github.com/stellio-app/stellio-app/discussions)

</div>
