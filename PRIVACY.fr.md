# Politique de Confidentialité (Privacy Policy)

**Dernière mise à jour :** 1er septembre 2026  
**Application :** Stellio  
**Site web :** [stellio-app.com](https://stellio-app.com)  
**Dépôt :** [github.com/stellio-app/stellio](https://github.com/stellio-app/stellio)

## 1. Introduction
Bienvenue dans la politique de confidentialité de Stellio. Stellio est une application de gestion de fichiers 3D et d'impression 3D. Cette politique décrit comment nous traitons les données. 

Notre philosophie fondamentale est simple : **Vos données restent chez vous. Tout s'exécute en local.**

## 2. Principe Fondamental : "Local-First"
Par défaut, Stellio ne collecte, ne transmet et ne stocke **aucune donnée** sur des serveurs externes. Tous vos fichiers 3D (STL, 3MF, OBJ), vos modèles d'imprimante, vos historiques d'impression, vos tags et vos paramètres sont stockés exclusivement sur votre propre machine (Windows, Raspberry Pi ou Linux) dans une base de données SQLite locale.

## 3. Données Stockées Localement
Les éléments suivants sont enregistrés uniquement sur votre appareil :
- Votre bibliothèque de fichiers 3D et leurs métadonnées (tags, descriptions, statistiques).
- Les miniatures 3D générées localement (via PyRender ou Matplotlib).
- Vos configurations d'imprimantes et de slicers.
- Vos clés API et identifiants (stockés localement et chiffrés via AES-CFB).
- L'historique de vos impressions et les photos associées.
- Les journaux d'activité (logs) pour le diagnostic.

## 4. Interactions avec des Services Tiers (Optionnelles)
Pour fonctionner, certaines fonctionnalités *optionnelles* de Stellio peuvent communiquer avec des services externes. Vous gardez le contrôle total sur l'activation de ces fonctionnalités :

- **Mises à jour automatiques** : Stellio peut interroger les dépôts GitHub (`github.com/stellio-app/stellio`) pour vérifier la disponibilité de nouvelles versions. Aucun identifiant personnel n'est transmis lors de cette vérification.
- **Plateformes de modèles 3D** : Si vous utilisez la fonction de téléchargement, Stellio se connecte directement aux API de Printables, MakerWorld ou Thingiverse en utilisant **vos propres identifiants ou clés API**. Ces informations ne sont jamais envoyées aux serveurs de Stellio.
- **Gestion des imprimantes** : Stellio communique directement avec vos imprimantes ou serveurs d'impression locaux/réseau (OctoPrint, Klipper/Moonraker, Bambu Lab via MQTT). Ces communications restent confinées à votre réseau local, sauf si vous configurez explicitement un accès distant.
- **Accès à distance (Cloudflare Tunnel)** : Si vous activez l'accès à distance, votre trafic est acheminé de manière sécurisée via les serveurs de Cloudflare. Veuillez consulter la [politique de confidentialité de Cloudflare](https://www.cloudflare.com/privacypolicy/) pour plus de détails.
- **Intelligence Artificielle (Ollama)** : Par défaut, l'IA (Ollama) s'exécute localement sur votre machine. Si vous choisissez de configurer une URL Ollama distante dans les paramètres, vos requêtes (descriptions de modèles, recherche sémantique) seront envoyées à ce serveur tiers que vous avez vous-même choisi.
- **Spoolman** : Si vous connectez Stellio à un serveur Spoolman externe, les données de consommation de filament sont envoyées à ce serveur que vous contrôlez ou avez choisi.

## 5. Sécurité des Données
- **Chiffrement** : Les données sensibles (comme les clés API ou les mots de passe des imprimantes) sont chiffrées localement à l'aide de l'algorithme AES-CFB.
- **Diagnostics** : Si vous rencontrez un bug, vous pouvez exporter un journal de diagnostic depuis les paramètres. Stellio masque automatiquement les secrets et les informations sensibles avant l'exportation. Nous ne collectons pas ces journaux automatiquement.

## 6. Vos Droits
Puisque toutes vos données sont stockées localement, vous avez un contrôle absolu sur celles-ci :
- Vous pouvez exporter l'intégralité de vos données à tout moment via la fonction de sauvegarde (`.zip`).
- Vous pouvez supprimer n'importe quel fichier, historique ou paramètre directement depuis l'interface.
- La désinstallation de l'application supprime les fichiers du programme, mais vous devrez supprimer manuellement le dossier de données local si vous souhaitez effacer définitivement votre historique et votre base de données.

## 7. Modifications de cette Politique
Nous pouvons mettre à jour cette politique de confidentialité pour refléter les changements dans les fonctionnalités de Stellio ou les obligations légales. La date de "Dernière mise à jour" en haut de ce document sera révisée en conséquence. Nous vous encourageons à consulter cette page périodiquement.

## 8. Contact
Si vous avez des questions ou des préoccupations concernant cette politique de confidentialité ou la gestion de vos données, vous pouvez nous contacter :
- 📧 Email : [contact@stellio-app.com](mailto:contact@stellio-app.com)
- 🐛 Signalement de bug : [GitHub Issues](https://github.com/stellio-app/stellio/issues)
- 💬 Discussions : [GitHub Discussions](https://github.com/stellio-app/stellio/discussions)

---
*Ce projet est open-source. Vous êtes invité à auditer le code source sur notre dépôt GitHub pour vérifier par vous-même le respect de cette politique.*