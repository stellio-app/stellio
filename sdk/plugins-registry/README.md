# Catalogue des plugins Stellio

Ce dossier est le **modèle du dépôt `stellio-app/stellio-plugins`** : `catalog.json` est le catalogue public affiché dans Stellio (Plugins › Catalogue). Les plugins sont hébergés sur le GitHub de leurs auteurs ; seul leur descriptif est ici.

## Proposer un plugin
1. Publiez votre plugin (release GitHub avec une archive `.zip`, voir la page « Plugins » du wiki).
2. Forkez ce dépôt et ajoutez votre entrée dans `catalog.json` :
```json
{ "id": "mon-plugin", "name": "Mon plugin", "version": "1.0.0",
  "description": {"fr": "…", "en": "…"}, "author": "Votre nom",
  "url": "https://github.com/vous/mon-plugin/releases/download/v1.0.0/mon-plugin-1.0.0.zip",
  "sha256": "<sha256sum de l'archive>", "permissions": ["events"],
  "logo": "https://raw.githubusercontent.com/vous/mon-plugin/main/logo.png",
  "homepage": "https://github.com/vous/mon-plugin" }
```
3. Vérifiez en local : `python validate_catalog.py catalog.json`.
4. Ouvrez une Pull Request : l'action GitHub rejoue ce contrôle (liens, sha256, cohérence avec `plugin.json`, logo).

## Règles de relecture
* Code lisible, sans obfuscation ; dépôt public avec licence et README.
* Permissions strictement nécessaires, décrites dans le README du plugin.
* Pas de collecte de données cachée, pas de téléchargement de code à l'exécution.
* Logo : PNG, JPEG ou WebP, 200 Ko maximum, idéalement 128 × 128 (SVG refusé).
* Mise à jour : nouvelle release, puis Pull Request qui change `version`, `url` et `sha256`.

Un plugin n'est pas isolé (voir `docs/plugins.md`) : la relecture réduit le risque, elle ne le supprime pas.

`template/` contient un plugin minimal à copier.
