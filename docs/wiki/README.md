# Wiki de Stellio

Le wiki GitHub (8 langues : fr, en, de, es, pt, it, zh, ja) est **généré** depuis ce dossier et publié automatiquement.

## Quand est-il mis à jour ?
Le workflow `.github/workflows/wiki.yml` s'exécute :
- à chaque push sur `main` qui touche `docs/wiki/**`, `changelog.json` ou `tools/build_wiki.py` ;
- à chaque release publiée ;
- à la demande (onglet Actions → wiki → Run workflow).

La page « Nouveautés » de chaque langue est produite à partir de `changelog.json` : elle suit donc chaque version sans rien faire.

## Première fois (une seule fois)
GitHub n'ouvre le dépôt du wiki qu'à la création d'une première page :
1. `Settings → Features` : cocher **Wikis**.
2. Onglet **Wiki** → *Create the first page* → enregistrer (contenu quelconque, il sera remplacé).
3. Relancer le workflow `wiki` (Actions → wiki → Run workflow). Tant que le wiki n'est pas initialisé, le workflow se termine avec un avertissement, sans erreur.

## Modifier le texte
Un fichier par langue : `docs/wiki/src/<langue>.md`. Les pages sont séparées par `@@@ Slug | Titre`.
Les 8 fichiers (dont « Guide pas à pas » = page `How-To`) doivent garder la même structure (titres, tableaux, blocs de code, liens) : `python tools/build_wiki.py --check`.

## Captures d'écran
- Dans une page, écrire `{{img:nom}}` sur sa propre ligne (noms : dashboard, library, viewer, projects, printers, filament, stats, management, settings, library-halo, already-printed, printer-slicer, android-update).
- Les images sont rangées par version et par langue : `docs/wiki/images/v1.0.7/<langue>/<nom>.png`.
- Pour une nouvelle version, ajoutez un dossier `docs/wiki/images/v<version>/` avec **uniquement les captures qui ont changé** : le wiki prend automatiquement la plus récente (langue de la page, sinon anglais, sinon français).
- Une nouvelle capture : ajouter son nom dans `CAPTIONS` (légendes des 8 langues) de `tools/build_wiki.py` et placer `{{img:nom}}` dans les 8 sources.

## Tester en local
```
python tools/build_wiki.py --check
python tools/build_wiki.py --out wiki-out
python -m pytest tests/test_wiki.py
```


## Site de documentation (façon docs.frigate.video)
Les **mêmes sources** produisent aussi un site HTML statique (menu par catégories, sommaire, recherche, thème clair/sombre, 8 langues) :
```
pip install markdown
python tools/build_docs.py --out docs-out --base /docs/
```
Le workflow `.github/workflows/docs.yml` le régénère à chaque modification de `docs/wiki/**` ou de `changelog.json` et le publie comme artefact `docs-site` (onglet Actions). Déposez son contenu dans le dossier `docs/` du site stellio-app.com.

### Captures 1.0.9 à remplacer (images provisoires « CAPTURE À REMPLACER »)
Dossier `docs/wiki/images/v1.0.9/<langue>/` (1280×800, 8 langues) :
- `library-halo.png` : bibliothèque avec fichiers réussis (halo vert) et ratés (halo rouge)
- `already-printed.png` : menu ⋯ d'un fichier → « Déjà imprimé », popup ouvert
- `printer-slicer.png` : slicer par défaut d'une imprimante + profils rattachés
- `android-update.png` : fenêtre « mise à jour disponible » de l'application Android
Il suffit d'écraser le fichier avec la vraie capture (même nom) : wiki et site de documentation la reprennent seuls.
