<div align="center">

#  Stellio-app

### Le gestionnaire de fichiers 3D ultime pour makers et imprimeurs 3D

[![Version](https://img.shields.io/github/v/release/stellio-app/stellio-app?style=for-the-badge&logo=github&color=4ea1d3)](https://github.com/stellio-app/stellio-app/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![Downloads](https://img.shields.io/github/downloads/stellio-app/stellio-app/total?style=for-the-badge&color=success)](https://github.com/stellio-app/stellio-app/releases)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge&logo=python)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey?style=for-the-badge)]()

[🌐 Site Officiel](https://stellio-app.com) • [📥 Télécharger](https://github.com/stellio-app/stellio-app/releases/latest) • [🐛 Signaler un bug](https://github.com/stellio-app/stellio-app/issues)

</div>

---

## 📖 À propos

**Stellio** est une application desktop moderne et légère conçue pour centraliser, organiser et gérer vos fichiers 3D (STL, 3MF, OBJ). Avec son interface intuitive et ses fonctionnalités avancées, Stellio transforme votre workflow d'impression 3D en une expérience fluide et productive.

> 💡 **Pourquoi Stellio ?** Parce que gérer des centaines de fichiers 3D répartis entre plusieurs dossiers, NAS et plateformes de téléchargement ne devrait pas être un casse-tête.

---

## ✨ Fonctionnalités

### 📁 Gestion Multi-Sources
- 🗂️ **Dossiers locaux** : Parcourez vos répertoires locaux
- 🌐 **Partages réseau** : Accès SMB/NFS à vos NAS et serveurs
- 📄 **Fichiers uniques** : Ajoutez des fichiers individuels
- 🔄 **Scan automatique** : Détection des nouveaux fichiers en temps réel

### 🌐 Téléchargements Intégrés
- 📨 **Telegram** : Téléchargez depuis channels et groupes
- 📊 **Suivi en temps réel** : Barre de progression avec annulation

### 🖼️ Miniatures Automatiques
- 🎨 **Rendu PyRender** : Miniatures 3D professionnelles
- ⚡ **Génération lazy** : Optimisée pour ne pas bloquer l'interface
- 🛡️ **Fallback intelligent** : Logo Stellio si le fichier est corrompu
- 📊 **Barre de progression** : Suivi de la génération en temps réel

### 🏷️ Organisation Avancée
- 🏷️ **Tags personnalisés** : Catégorisez avec des couleurs
- ⭐ **Favoris** : Accès rapide à vos fichiers préférés
- 🔍 **Filtres puissants** : Par type, taille, tags, dossier
- ⚡ **Recherche instantanée** : Trouvez n'importe quel fichier en millisecondes
- 📂 **Tri par dossier** : Vue hiérarchique de vos fichiers

### ✂️ Intégration Slicer
- 🖨️ **Multi-slicers** : OrcaSlicer, Bambu Studio, PrusaSlicer, Ultimaker Cura
- 📦 **Envoi en lot** : Envoyez plusieurs fichiers d'un coup
- 🔍 **Détection automatique** : Trouve vos slicers installés

### 🖨️ Monitoring Imprimantes
- 🌡️ **Températures** : Extrudeur, plateau, chambre en temps réel
- 📈 **Progression** : Suivi d'impression avec estimation de temps
- 📹 **Caméra** : Flux vidéo MJPEG intégré
- 📜 **Historique** : Dernière impression et statistiques
- 🎯 **Support** : Klipper/Moonraker

### 🔧 Réparation de Maillage
- 🔍 **Détection automatique** : Fichiers non-manifold
- 🛠️ **Réparation en un clic** : Correction des trous géométriques
- 📐 **Analyse 3D** : Dimensions, volume, poids, temps d'impression estimé

### 🌍 Multi-Langue
- 🇫🇷 Français | 🇬🇧 English | 🇪🇸 Español | 🇮🇹 Italiano
- 🇵🇹 Português | 🇯🇵 日本語 | 🇩🇪 Deutsch | 🇨🇳 中文

### 🔄 Mise à Jour Automatique
- 🔍 **Vérification GitHub** : Détecte les nouvelles versions
- ⬇️ **Téléchargement intégré** : Pas besoin de navigateur
- 🚀 **Installation silencieuse** : Redémarrage automatique

### 🎨 Personnalisation
- 🌓 **Thèmes** : Sombre, Clair, Système (Auto)
- 🎨 **Couleurs de marque** : Stellio, Bambu Lab, Prusa, Voron, Creality
- 📱 **Interface responsive** : Design épuré et moderne

## 📥 Installation

### 🪟 Windows (Recommandé)

1. Téléchargez le dernier installateur depuis [la page Releases](https://github.com/stellio-app/stellio-app/releases/latest)
2. Lancez `Stellio-Setup-x.x.x.exe`
3. Suivez l'assistant d'installation
4. Lancez Stellio depuis le menu Démarrer ou le bureau

---

## 🚀 Démarrage Rapide

### Premier Lancement

1. **Créez votre compte** : Nom d'utilisateur + mot de passe
2. **Ajoutez une source** : Cliquez sur "Ajouter" dans Paramètres
3. **Explorez vos fichiers** : Naviguez dans la bibliothèque
4. **Personnalisez** : Choisissez votre thème et slicer par défaut

### Configuration Initiale

```
1. Paramètres → Sources → Ajouter un dossier
2. Paramètres → Slicer → Choisissez votre slicer
3. Paramètres → Apparence → Thème et couleur
4. Paramètres → Langue → Votre langue préférée
```

---

## 🛠️ Technologies

| Composant | Technologie |
|-----------|-------------|
| **Backend** | Python 3.10+, Flask, Waitress |
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla) |
| **Base de données** | SQLite3 |
| **Rendu 3D** | PyRender, Trimesh, PyVista |
| **Visualisation** | Three.js |
| **API Externes** | Telegram (Telethon)|
| **Protocoles** | SMB (smbprotocol), NFS |
| **Chiffrement** | cryptography (AES-CFB) |
| **Interface Desktop** | PyWebView |
| **Packaging** | PyInstaller, Inno Setup |

---

## 📋 Configuration Requise

### Windows
- **OS** : Windows 10/11 (64-bit)
- **RAM** : 4 GB minimum (8 GB recommandé)
- **Stockage** : 500 MB pour l'application + espace pour les miniatures
- **GPU** : Support OpenGL 3.3+ pour le rendu 3D

---

## 🔐 Sécurité

- 🔒 **Chiffrement local** : Mots de passe et tokens API chiffrés (AES-256)
- 🏠 **Pas de cloud** : Toutes les données restent sur votre machine
- 👁️ **Open source** : Code auditable par la communauté
- ✅ **Mises à jour signées** : Vérification d'intégrité

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Voici comment participer :

### Signaler un Bug
1. Vérifiez les [issues existantes](https://github.com/stellio-app/stellio-app/issues)
2. Créez une nouvelle issue avec le template "Bug Report"
3. Incluez : version, OS, étapes de reproduction, logs

### Proposer une Fonctionnalité
1. Ouvrez une issue "Feature Request"
2. Décrivez votre idée et son cas d'usage
3. Discutez avec la communauté

---

## 🗺️ Roadmap

### Version 1.1
- [ ] Support Linux complet (AppImage + .deb)
- [ ] Intégration Bambu Lab (MQTT)
- [ ] Export de statistiques d'impression
- [ ] Thèmes personnalisables

### Version 1.2
- [ ] Synchronisation multi-appareils (optionnel)
- [ ] Éditeur de tags en masse
- [ ] Recherche avancée (métadonnées 3D)
- [ ] Plugin system

### Version 2.0
- [ ] Version mobile (Android/iOS)
- [ ] Intégration cloud (Printables, MakerWorld)
- [ ] Collaboration en équipe
- [ ] API publique

---

## 💬 Communauté

Rejoignez la communauté Stellio :

- 🌐 **Site web** : [stellio-app.com](https://stellio-app.com)
- 📧 **Email** : contact@stellio-app.com
- 🐛 **Issues** : [GitHub Issues](https://github.com/stellio-app/stellio-app/issues)

---

## 📄 Licence

Ce projet est sous licence **MIT** - voir le fichier [LICENSE](LICENSE) pour plus de détails.

```
MIT License

Copyright (c) 2026 Stellio Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

---

## 🙏 Remerciements

Stellio est rendu possible grâce à :

- **[PyRender](https://github.com/mmatl/pyrender)** - Rendu 3D professionnel
- **[Trimesh](https://github.com/mikedh/trimesh)** - Manipulation de maillages 3D
- **[Flask](https://flask.palletsprojects.com/)** - Framework web léger
- **[Telethon](https://github.com/LonamiWebs/Telethon)** - Client Telegram
- **[PyWebView](https://github.com/r0x0r/pywebview)** - Interface desktop
- **[Three.js](https://threejs.org/)** - Visualisation 3D web
- **La communauté Maker** - Feedback et suggestions précieux

---

## ⭐ Soutenir le Projet

Si vous aimez Stellio, pensez à :

- ⭐ **Starrer** le repo sur GitHub
- 🐦 **Partager** sur les réseaux sociaux
- 🐛 **Signaler** les bugs
- 💡 **Proposer** des fonctionnalités
- ☕ **Sponsoriser** (bientôt disponible)

---

<div align="center">

### Fait avec ❤️ pour la communauté impression 3D

[🌐 stellio-app.com](https://stellio-app.com) • [📥 Télécharger](https://github.com/stellio-app/stellio-app/releases/latest) • [💬 Discord](https://discord.gg/stellio)

**© 2026 Stellio Project. Tous droits réservés.**

</div>
