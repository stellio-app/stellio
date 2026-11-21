# Plugins Stellio (1.1.7)

Un plugin réagit à des évènements : `print.finished`, `print.failed`, `order.late`, `printer.overload`.

## Structure
Une archive `.zip` (2 Mo max, 100 fichiers max) contenant `plugin.json` et un script Python :

```json
{ "id": "mon-plugin", "name": "Mon plugin", "version": "1.0.0", "api": 1,
  "entry": "main.py", "events": ["print.failed"], "permissions": ["events", "api:read"] }
```

Le script reçoit l'évènement en JSON sur son entrée standard. Aide : `sdk/python/stellio_sdk.py` (`plugin_event()`, `plugin_config()`, `from_env()`). Exemple prêt à zipper : `sdk/examples/hello-plugin/`.

## Permissions
`events` (recevoir les évènements) · `api:read` / `api:write` (Stellio fournit `STELLIO_API_URL` et le jeton saisi dans la configuration du plugin) · `network` (information). L'activation exige d'accepter les permissions ; un plugin est **désactivé à l'installation**.

## Isolation — ce qu'elle est et n'est pas
Processus séparé, dossier de travail = celui du plugin, environnement nettoyé (aucune variable ni secret de Stellio), 10 s maximum, 512 Mo de mémoire (POSIX), sortie tronquée, aucun accès à la base de Stellio. Réservé au compte propriétaire ; menu **Plugins › Catalogue** (page dédiée), avec le journal des exécutions.

**Restrictions du noyau (1.1.8) — réelles sous Linux seulement.**

| | Linux (noyau ≥ 5.13) | Linux sans Landlock | Windows / macOS |
|---|---|---|---|
| Fichiers | lecture seule du système et du dossier du plugin, écriture uniquement dans `data/` (variable `STELLIO_PLUGIN_DATA`) ; le reste du disque et les données de Stellio sont inaccessibles ; le code du plugin ne peut plus se modifier | non restreints | non restreints |
| Réseau | sans permission `network` ni `api:*` : création de sockets Internet refusée (seccomp) | idem | non restreint |

Un plugin autorisé à utiliser le réseau n'est **pas** limité à certains sites. Là où le noyau n'applique rien, les permissions restent **déclaratives** (audit + acceptation) et la page Plugins l'affiche. `STELLIO_PLUGIN_SANDBOX=off` désactive les restrictions (dépannage). Les plugins qui écrivaient à la racine de leur dossier doivent écrire dans `data/`. N'installez que du code que vous avez lu.

## Signature et audit (1.1.8)
* **Signature Ed25519.** Le catalogue (`catalog.json.sig`, sur les octets exacts du fichier) et chaque plugin (`signature` dans l'entrée du catalogue : `stellio-plugin-v1\n<id>\n<version>\n<sha256>`) peuvent être signés. Clés de confiance : `OFFICIAL_PUBLIC_KEYS` (modules/plugin_security.py), `STELLIO_PLUGIN_PUBKEYS` (hex, séparées par des virgules) ou `<données>/plugins/trusted_keys.json`. **Sans clé configurée rien n'est exigé** (l'empreinte SHA-256 reste la seule protection ; la page l'indique). Avec une clé : signature invalide = refus ; catalogue ou plugin officiel non signé = refus ; mise à jour non signée d'un plugin signé = refus ; clé différente de celle de la version installée = refus sauf confirmation explicite. Une signature prouve l'origine de l'archive, pas l'innocuité du code.
* **Outil de l'éditeur** : `python tools/plugin_sign.py keygen|plugin|catalog|verify` (la clé privée ne quitte jamais la machine de l'éditeur).
* **Audit automatique** avant installation (analyse statique, le code n'est pas exécuté) : réseau non déclaré, lancement de processus, code dynamique (`eval`, `exec`, `__import__`, `ctypes`…), binaires, lecture hors du dossier, pages HTML chargeant du contenu externe. Les constats **bloquants** refusent l'installation sauf acceptation explicite du risque (ou signature d'une clé de confiance). Un audit peut rater du code obfusqué : c'est un filet, pas une preuve. Résultat visible par plugin (`Signé` / `Non signé`, `Audit : …`).

## Mises à jour
Réinstaller une archive d'un plugin déjà présent la **met à jour** :
* version plus récente → mise à jour ; même version → réinstallation ; version plus ancienne → refus (`409`) sauf case « autoriser le retour en arrière » ;
* la **configuration est conservée** (jeton compris) ;
* si la nouvelle version demande des **permissions supplémentaires**, le plugin est **désactivé** et il faut les accepter à nouveau ;
* le remplacement est atomique : si le déplacement échoue, l'ancienne version reste en place.
Les versions se comparent par leurs nombres (`1.10` > `1.9`) ; les pré-versions (`-beta`) ne sont pas distinguées.

## Catalogue
**Plugins › Catalogue** affiche un catalogue public sous forme de cartes (logo, description, auteur, lien vers la page du plugin). Par défaut c'est le fichier `catalog.json` du dépôt `stellio-app/stellio-plugins` ; on peut le remplacer (section « Source du catalogue » de la page, ou variable d'environnement `STELLIO_PLUGINS_CATALOG`, adresse **https**). Les plugins eux-mêmes sont hébergés sur le GitHub de leurs auteurs. Guide complet pour créer et diffuser un plugin : page **Plugins** du wiki.
```json
{ "plugins": [ { "id": "meteo", "name": "Météo", "version": "1.1",
                 "description": {"fr": "…", "en": "…"}, "author": "…",
                 "url": "https://exemple.org/meteo-1.1.zip", "sha256": "<64 caractères hexadécimaux>", "permissions": ["events"],
                 "logo": "https://exemple.org/logo.png", "homepage": "https://exemple.org/meteo" } ] }
```
* `description` : texte simple ou un texte par langue (langue de l'interface, sinon anglais, sinon français). `logo` : https, PNG/JPEG/WebP, 200 Ko maximum (le SVG est refusé) ; il est servi par Stellio, le navigateur ne contacte pas l'hébergeur. `homepage` : lien https facultatif.
* Stellio indique, pour chaque entrée, la version installée et si une mise à jour existe.
* L'adresse du zip vient **du catalogue relu par le serveur**, jamais du navigateur ; l'empreinte **SHA-256 est obligatoire** : une entrée sans empreinte est ignorée, une empreinte différente refuse l'installation.
* Seules les adresses https publiques sont acceptées (localhost, réseaux privés, lien-local, identifiants dans l'URL refusés ; les redirections sont revérifiées). Archive : 2 Mo maximum.
* L'empreinte prouve que le fichier est celui annoncé par le catalogue, **pas que le code est sûr** : le catalogue est une source de confiance que vous choisissez.


## Plugin avec une page (permission `ui`)
Un plugin peut afficher sa propre page : il apparaît dans le menu **Plugins** de la barre latérale (liste « Installés », sous « Catalogue »). Manifeste : `"permissions": ["ui", …], "ui": {"title": "…", "icon": "fa-layer-group", "entry": "viewer.html"}`.
* **Un seul fichier HTML autonome** (CSS/JS dedans, images en `data:`), 1 Mo maximum ; sans évènement, pas de script Python (`entry` facultatif).
* Affichée dans un `<iframe sandbox="allow-scripts">` (origine opaque : ni cookies, ni stockage, ni accès au DOM de Stellio) avec une politique CSP qui interdit tout réseau (`connect-src 'none'`). Le plugin doit être **activé** ; le fichier est servi par `GET /api/plugins/<id>/ui`.
* Données : `window.stellio.api(chemin[, 'json'|'text'|'arraybuffer'])` (promesse). Lecture seule (GET `/api/…`), permission `api:read` obligatoire ; refus pour `/api/plugins`, `/api/auth`, `/api/settings`, `/api/accounts`, `/api/security`, `/api/sessions`, `/api/guests`, `/api/backup`, `/api/audit`, `/api/diagnostic`, `/api/update`, `/api/smtp`, `/api/mqtt`, `/api/push`, `/api/users`, `/api/tokens`. La page reçoit le thème (`--st-bg`, `--st-panel`, `--st-card`, `--st-text`, `--st-muted`, `--st-border`, `--st-accent`, `--st-success`, `--st-warning`, `--st-danger`), `window.stellio.lang` et l'évènement `stellio-ready`.
* Exemple complet : `sdk/examples/gcode-viewer/` (visionneuse de G-code archivés, vue 3D, 8 langues).

## Plugins intégrés (1.1.7)
Plusieurs fonctions de Stellio sont livrées comme **plugins intégrés** (dossier `bundled_plugins/<id>/` de l'application) : `administration` (actif d'office), `bigprint`, `resin`, `usb-printers`, `timelapse`, `file-tools`, `plate-studio`, `push-notify`, `webhooks`, `digest`, `mqtt`, `obico`, `sharing`, `spoolman`, `ai-assistant`, `ai-ollama`, `ai-openai`, `ai-anthropic`, `ai-gemini`, `stellio-pro`. Ils font partie de l'application (signés avec elle) mais ne se chargent, avec leurs routes, leurs tâches de fond et leurs dépendances, que lorsqu'ils sont **activés** (**Plugins › Plugins intégrés** ; l'activation s'applique au redémarrage). Désactiver un plugin ne supprime aucun réglage.
* **Migration invisible** : au premier démarrage en 1.1.7 d'une installation existante, chaque plugin dont l'usage est reconnu (réglage renseigné, table remplie, dossier non vide, imprimante d'un type géré) est activé automatiquement ; les réglages restent à leur place, rien à ressaisir. Les outils sans réglage (BigPrint, outils de fichiers, atelier plateau) sont conservés. Une installation neuve n'en active aucun. L'état est dans `<données>/plugins/.host.json`.
* **Stellio Pro** (`stellio-pro`) regroupe toute la partie commerciale et financière : clients, devis et portail de devis, factures, commandes et suivi, export comptable (ZIP), tarif d'énergie, planning de production (coûts, marge, rentabilité), besoins en matière et stock de pièces. Il ajoute les pages (Gestion, Planning), les boutons de devis et les réglages associés ; sans lui, ils n'apparaissent pas. Le coût d'impression par tirage reste dans le cœur.
* **Édition serveur uniquement** : `push-notify` (notifications push externes), `webhooks`, `mqtt`, `digest` et les IA cloud sont masqués et désactivés sous Windows (`"server_only": true` dans le manifeste, vérifié par l'hôte de plugins).
* **IA** (OpenAI, Anthropic et Gemini sont réservés à l'édition serveur : sous Windows seul Ollama, local, est proposé) : un plugin par fournisseur (`ai-ollama`, `ai-openai`, `ai-anthropic`, `ai-gemini`) et `ai-assistant`, qui active toutes les fonctions IA (étiquetage, assistant de bibliothèque, recherche par photo, atelier FAB). **Partage & synchro** (`sharing`) : liens de partage, instances distantes, synchronisation, communauté. **Spoolman** (`spoolman`) : la section Spoolman de l'inventaire des filaments.
* Ils s'exécutent **dans le processus de Stellio** (contrairement aux plugins tiers, isolés) : seuls ceux livrés avec l'application sont admis. Un manifeste d'archive qui déclare `host`, ou qui reprend l'identifiant d'un plugin intégré, est refusé.
* Manifeste : `"host": {"modules": [...], "migrate": {...}}` ; chaque module expose `init(globals())` et, facultativement, `autostart()` (tâches de fond). Variable d'environnement `STELLIO_ENABLE_PLUGINS` (`all` ou une liste d'identifiants) : active des plugins pour les tests et la démo.
* L'interface masque les menus et sections d'un plugin désactivé (attribut `data-host-plugin="<id>"`).
