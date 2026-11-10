# Démo publique de Stellio (lecture seule)

La démo est **le `main.py` officiel de GitHub, sans aucun code démo**, lancé à travers un petit lanceur (`stellio_demo.py`) qui y branche un fichier de bridage (`stellio_demo_overlay.py`). Ces deux fichiers vivent hors du dépôt, uniquement dans le conteneur de démo.

## Ce que fait le bridage
- Ouvre l'interface en **invité (lecture seule)** en un clic, sans écran de connexion, avec un bandeau « Démo publique en lecture seule ».
- Fabrique une douzaine de **modèles 3D libres** (générés par le code, domaine public) et des **données fictives** : imprimantes, bobines, historique, projets, devis, commandes, maintenance.
- Remplit **« Mes likes » et « Mes créations »** avec des modèles inventés sur les 6 plateformes (MakerWorld, Thingiverse, Printables, Creality Cloud, Snapmaker Space, Nexprint) ; vignettes dessinées par le code, aucune connexion réelle, téléchargement refusé.
- Bloque : toute écriture, inscriptions, fonctions IA ou lourdes, synchronisation des comptes, accès aux secrets, **toute connexion vers le réseau local**.
- Masque changelog, widget Nouveautés et recherche de mise à jour.
- **Fail-closed** : si `main.py` n'est plus compatible, le lanceur refuse de démarrer.

## Mise en place et mises à jour
Voir `GUIDE-COMPLET-DEMO-ET-STATS.md` (partie 1). Avant chaque release : `python check_overlay.py main.py` → COMPATIBLE.

## Isolation du réseau local
Deux protections se cumulent : le blocage dans l'application (10/8, 172.16/12, 192.168/16, lien local, multicast refusés) et le pare-feu Proxmox créé par `stellio-demo-lxc.sh` (pare-feu du datacenter à activer).

## Bonnes pratiques
- Conteneur dédié (2 vCPU, 2 Go), exposé uniquement par un tunnel Cloudflare, règle de limitation de débit sur `/`.
- Aucune imprimante, aucun compte, aucune clé API réels sur cette instance.
