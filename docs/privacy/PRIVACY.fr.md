# Politique de Confidentialité (Privacy Policy)

**Dernière mise à jour :** 20 octobre 2026  
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
- **Plateformes de modèles 3D** : Si vous utilisez la fonction de téléchargement, Stellio se connecte directement aux API de Printables, MakerWorld, Thingiverse ou Nexprint (la bibliothèque d'Elegoo) en utilisant **vos propres identifiants ou clés API**. Ces informations ne sont jamais envoyées aux serveurs de Stellio.
- **Gestion des imprimantes** : Stellio communique directement avec vos imprimantes ou serveurs d'impression locaux/réseau (OctoPrint, Klipper/Moonraker, Bambu Lab via MQTT). Ces communications restent confinées à votre réseau local, sauf si vous configurez explicitement un accès distant.
- **Accès à distance (Cloudflare Tunnel)** : Si vous activez l'accès à distance, votre trafic est acheminé de manière sécurisée via les serveurs de Cloudflare. Veuillez consulter la [politique de confidentialité de Cloudflare](https://www.cloudflare.com/privacypolicy/) pour plus de détails.
- **Intelligence Artificielle (Ollama)** : Par défaut, l'IA (Ollama) s'exécute localement sur votre machine. Si vous choisissez de configurer une URL Ollama distante dans les paramètres, vos requêtes (descriptions de modèles, recherche sémantique) seront envoyées à ce serveur tiers que vous avez vous-même choisi.
- **Spoolman** : Si vous connectez Stellio à un serveur Spoolman externe, les données de consommation de filament sont envoyées à ce serveur que vous contrôlez ou avez choisi.
- **Notifications push (optionnelles, désactivées par défaut)** : Si vous les activez dans les paramètres, Stellio envoie le titre et le texte des notifications que vous avez choisies (par exemple la fin ou l'échec d'une impression, qui peut mentionner un nom de fichier ou d'imprimante) au service que vous sélectionnez : ntfy (le serveur public `ntfy.sh` ou votre propre serveur), Telegram (avec le jeton de bot et l'identifiant de conversation que vous fournissez), un webhook Discord ou une URL de webhook de votre choix. La politique de confidentialité de ce service s'applique alors. Sur un serveur ntfy public, toute personne connaissant le nom de votre sujet peut lire les messages : choisissez un sujet difficile à deviner ou hébergez votre propre serveur.
- **TigerTag (optionnel)** : Si vous utilisez l'intégration TigerTag, Stellio se connecte à votre compte TigerTag via les services d'authentification et de base de données de Google (Firebase : `securetoken.googleapis.com`, `identitytoolkit.googleapis.com`, `firestore.googleapis.com`, ainsi que `tigertag-cdn.web.app`) pour lire l'inventaire de vos bobines, et à `api.tigertag.io` pour télécharger les tables de référence publiques. Le jeton de session est stocké chiffré sur votre machine.
- **Signalements et suggestions (optionnels)** : Rien n'est envoyé tant que vous ne validez pas le formulaire en donnant votre consentement explicite. Le type, le titre et la description que vous rédigez sont envoyés à un relais hébergé sur Cloudflare Workers, qui crée une issue **publique** dans le dépôt GitHub du projet : n'y mettez ni information personnelle ni secret. Si vous cochez la case des informations techniques, la version de Stellio, le système d'exploitation et la langue de l'interface sont ajoutés. Stellio interroge ensuite l'API publique de GitHub pour afficher l'état et les commentaires de vos demandes, et conserve localement un jeton de gestion.
- **Suivi des mises à jour de modèles (activé par défaut, désactivable dans les paramètres)** : Stellio demande automatiquement à Printables, MakerWorld ou Thingiverse (avec votre jeton Thingiverse si vous en avez configuré un) si les modèles que vous avez téléchargés ont une nouvelle version. Seul l'identifiant de chaque modèle est envoyé.
- **Recherche de bobines en boutique (uniquement quand vous l'utilisez)** : Lorsque vous vérifiez la disponibilité d'une bobine en boutique, Stellio envoie vos termes de recherche (marque, matière, couleur) aux sites des boutiques (par exemple Atome3D, Rainbow3D, Amazon, la boutique Bambu Lab et les boutiques de votre liste de liens utiles).
- **Autres instances Stellio (optionnel)** : Si vous ajoutez une instance Stellio distante ou utilisez la fonction de découverte (qui analyse votre réseau local), Stellio contacte les adresses concernées. Les fichiers ou dossiers que vous choisissez d'envoyer vont directement à l'instance que vous avez désignée, authentifiés par sa clé d'accès, et ne transitent jamais par nos serveurs.

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