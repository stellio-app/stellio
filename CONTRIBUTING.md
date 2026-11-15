# Contribuer à Stellio / Contributing to Stellio

Merci de l'intérêt porté à Stellio ! / Thanks for your interest in Stellio!

## Démarrer en 5 minutes / Quick start

```bash
git clone https://github.com/stellio-app/stellio.git
cd stellio
pip install -r requirements.txt pytest
python main.py          # http://localhost:5000
python -m pytest -q     # suite de tests
```

Le guide `CODEMAP.md` explique où se trouve chaque chose (`main.py`, `modules/`, `interface/`, `languages/`).
`CODEMAP.md` explains where everything lives.

## Règles simples / Ground rules

- **Une PR = un sujet.** Petite et lisible, c'est relu plus vite.
- **Tests** : `python -m pytest -q` doit passer. Ajoutez un test pour tout comportement nouveau ou corrigé.
- **Traductions** : toute chaîne visible va dans `languages/*.json`, dans les **8 langues** (fr, en, de, es, pt, it, zh, ja). Le français et l'anglais sont obligatoires, les autres peuvent être proposées avec une traduction de bonne foi.
- **Pas de dépendance lourde** : Stellio reste léger (Flask + JS vanilla, sans framework front).
- **Sécurité** : ne jamais committer de clé, de jeton ou de fichier personnel. Pour une faille, voir `docs/SECURITY.md` (ne pas ouvrir d'issue publique).
- **Changelog** : si votre PR change ce que voient les utilisateurs, ajoutez une ligne dans `changelog.json` (et `languages/changelog.json`), en 8 langues. Les notes de release GitHub sont générées à partir de ce fichier (`tools/release_notes.py`).

## Où aider ? / Where to help

Cherchez le label **[good first issue](https://github.com/stellio-app/stellio/labels/good%20first%20issue)** : tâches courtes et bien délimitées.
Look for the **good first issue** label: short, well-scoped tasks.

Idées toujours bienvenues :
- Corriger ou améliorer une traduction (`languages/xx.json`)
- Ajouter le support d'un format de fichier ou d'une plateforme de modèles
- Améliorer la documentation (`docs/wiki/src/<langue>.md`)
- Signaler un bug avec la version, l'OS et les étapes pour le reproduire

## Proposer une modification / Submitting a change

1. Forkez le dépôt et créez une branche (`git checkout -b ma-modif`).
2. Faites vos changements, lancez les tests.
3. Ouvrez une Pull Request en décrivant le *pourquoi*.

Licence : en contribuant, vous acceptez que votre code soit publié sous la licence du dépôt (voir `LICENSE`).
