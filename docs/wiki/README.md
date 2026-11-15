# Wiki de Stellio

La documentation (8 langues : fr, en, de, es, pt, it, zh, ja) est **générée** depuis ce dossier et publiée sur `https://stellio-app.com/docs/`.
L'onglet Wiki de GitHub est désactivé : plus de workflow `wiki`.

## Quand est-elle générée ?
Le workflow `.github/workflows/docs.yml` s'exécute à chaque push sur `main` qui touche `docs/wiki/**`, `changelog.json` ou `tools/build_*.py`, à chaque release et à la demande. Il produit l'artefact `docs-site` (Actions → docs), à déposer dans le dossier `/docs/` du site.
La page « Nouveautés » de chaque langue est produite à partir de `changelog.json`.

## Modifier le texte
Un fichier par langue : `docs/wiki/src/<langue>.md`. Les pages sont séparées par `@@@ Slug | Titre`.
Les 8 fichiers (dont « Guide pas à pas » = page `How-To`) doivent garder la même structure (titres, tableaux, blocs de code, liens) : `python tools/build_wiki.py --check`.

## Captures d'écran
- Dans une page, écrire `{{img:nom}}` sur sa propre ligne (noms : dashboard, library, viewer, projects, printers, filament, stats, management, settings, library-halo, already-printed, printer-slicer, android-update).
- Les images sont dans un seul dossier, les mêmes pour les 8 langues : `docs/wiki/images/<nom>.png`.
- Pour mettre une capture à jour, remplacez simplement le fichier (même nom) : le wiki et le site de documentation la reprennent seuls.
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

### Captures
Toutes les captures sont dans `docs/wiki/images/` (dashboard, library, library-halo, already-printed, viewer, projects, printers, printer-slicer, filament, stats, management, settings, android-update).
