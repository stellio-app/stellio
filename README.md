# Tests Stellio

Suite de tests pour les fonctions critiques de `main.py` : chiffrement,
contrôle d'appartenance de fichiers (`_is_path_within_sources`), extraction
d'archives sécurisée (anti Zip-Slip), conversions d'entrée utilisateur,
checksum de l'auto-update.

## Installation

```bash
pip install pytest
```

`main.py` a besoin de ses dépendances habituelles (Flask, cryptography...).
Les dépendances lourdes non nécessaires aux tests (trimesh, pyrender,
smbclient, rarfile, pymeshfix) sont automatiquement remplacées par des stubs
minimalistes si elles ne sont pas installées (voir `conftest.py`) — inutile
de les installer juste pour lancer les tests. Si elles SONT installées (poste
de dev normal), les stubs ne sont jamais utilisés : les tests utilisent alors
les vraies bibliothèques sans rien changer à leur comportement.

## Lancer les tests

Placez ce dossier `tests/` à côté de `main.py`, puis :

```bash
cd tests
python3 -m pytest -v
```

## Ce qui est couvert

- **Chiffrement** (`TestEncryption`) : round-trip, IV aléatoire à chaque
  appel (régression du bug d'IV statique), détection de format, compatibilité
  avec les valeurs encore en clair (migration).
- **Hash de mot de passe** (`TestPasswordHashing`) : PBKDF2, sel aléatoire.
- **`_safe_int`** : jamais d'exception sur une entrée invalide.
- **Anti Zip-Slip** (`TestSafeExtract`) : traversal `../`, chemin absolu,
  extraction légitime toujours fonctionnelle.
- **`_is_path_within_sources`** (`TestPathWithinSources`) : reproduit
  précisément la faille corrigée sur `/api/file/mesh` (chemin absolu sans
  `..` mais hors de toute source déclarée).
- **Checksum auto-update** (`TestUpdateChecksum`) : fichier dédié, fichier
  récapitulatif multi-hash, absence de checksum, format invalide.

## Étendre la suite

Chaque nouvelle route touchant à des fichiers, au chiffrement, ou à
l'authentification devrait s'accompagner d'un test ici — c'est la meilleure
protection contre une régression silencieuse d'une des failles déjà corrigées.
