<div align="center">

#  <img src="https://stellio-app.com/assets/logo-nom-stellio.png" alt="Stellio Logo" width="200"/>

### Le gestionnaire de fichiers 3D ultime pour makers et imprimeurs 3D

[![Version](https://img.shields.io/badge/version-0.2.6-blue.svg)](https://github.com/stellio-app/stellio-app/releases)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)]()

[🚀 Installation](#-installation) • [✨ Fonctionnalités](#-fonctionnalités) • [📖 Documentation](#-documentation) • [🤝 Contribuer](#-contribuer) • [📜 Licence](#-licence)

<img src="assets/logo-nom-stellio.png" alt="Stellio Logo" width="200"/>

</div>

---

## 🎯 Présentation

**Stellio** est une application desktop moderne qui centralise toute votre bibliothèque 3D (STL, 3MF, OBJ), automatise les tâches répétitives et s'intègre parfaitement à votre flux de travail d'impression 3D.

Que vous soyez maker débutant ou imprimeur expérimenté avec plusieurs machines, Stellio vous fait gagner un temps précieux grâce à l'**IA locale** (Ollama), la **gestion intelligente des imprimantes** et une **interface pensée pour la productivité**.

> 💡 **Philosophie** : Vos données restent chez vous. Tout fonctionne en local, sans dépendance cloud obligatoire.

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
- ☁️ Fallback cloud gratuit (Pollinations) si Ollama indisponible

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
- 🔄 Mises à jour automatiques depuis GitHub
- 📋 Export de logs de diagnostic (secrets masqués)

---

## 🖼️ Screenshots

<div align="center">
<table>
<tr>
<td><img src="library.png" alt="Bibliothèque" width="400"/><br><em>Bibliothèque avec miniatures</em></td>
<td><img src="monitoring.png" alt="Imprimantes" width="400"/><br><em>Monitoring imprimantes</em></td>
</tr>
<tr>
<td><img src="slicer.png" alt="Slicer" width="400"/><br><em>Recommandation IA de profil</em></td>
<td><img src="nesting.png" alt="Nesting" width="400"/><br><em>Nesting automatique</em></td>
</tr>
</table>
</div>

---

## 🚀 Installation

### 🪟 Windows (recommandé)

1. Téléchargez le dernier installateur depuis les [Releases](https://github.com/stellio-app/stellio-app/releases)
2. Lancez `Stellio-Setup.exe`
3. C'est tout ! 🎉

### Slicers supportés

Stellio détecte automatiquement :
- ✅ OrcaSlicer
- ✅ Bambu Studio
- ✅ PrusaSlicer / SuperSlicer
- ✅ Ultimaker Cura
- ✅ Creality Print
- ✅ Slicers personnalisés (configurables)

### Imprimantes

| Type | Protocole | Fonctionnalités |<br>
|------|-----------|-----------------|<br>
| OctoPrint | HTTP API | Monitoring, upload, caméra |<br>
| Klipper/Moonraker | HTTP API | Monitoring, upload, caméra, heures exactes |<br>
| Bambu Lab | MQTT | Monitoring temps réel, AMS, caméra |

---

## 🛠️ Technologies

| Composant | Technologie |
|-----------|-------------|
| Backend | Python 3.8+, Flask, Waitress |
| Frontend | HTML5, CSS3, JavaScript vanilla |
| Base de données | SQLite (WAL mode) |
| Desktop | pywebview |
| Rendu 3D | PyRender, Matplotlib, Three.js |
| Maillage | trimesh, pymeshfix, shapely |
| IA | Ollama (local), Pollinations (cloud) |
| Réseau | paho-mqtt, smbclient, requests |
| Chiffrement | cryptography (AES-CFB) |
| Archives | zipfile, rarfile, py7zr, tarfile |

---

## 📖 Documentation

### Raccourcis clavier

| Raccourci | Action |<br>
|-----------|--------|<br>
| `Ctrl+F` | Rechercher |<br>
| `Ctrl+N` | Nouveau téléchargement |<br>
| `Ctrl+,` | Paramètres |<br>
| `Alt+1-8` | Navigation rapide |<br>
| `F` | Toggle favoris |<br>
| `T` | Gestionnaire de tags |<br>
| `?` | Aide raccourcis |<br>
| `Échap` | Fermer modale / vider recherche |<br>

### Structure du projet
stellio-app/ <br>
├── main.py                 # Backend Flask + Desktop<br>
├── script.js               # Frontend<br> JavaScript
├── index.html              # Interface principale<br>
├── style.css               # Styles<br>
├── assets/                 # Logos, icônes<br>
├── languages/              # Fichiers de traduction (JSON)<br>
├── requirements.txt        # Dépendances Python

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
