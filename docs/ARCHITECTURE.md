# Architecture du dépôt Stellio

## Structure actuelle (1.0.5 : dossiers `modules/`, `interface/`, `packaging/`, `release-notes/`)

```
stellio/
├── main.py                  Noyau Flask : base de données, authentification, bibliothèque, imprimantes, IA, démarrage
├── check_deps.py            Vérification et réparation des dépendances (importé par main.py)
├── requirements.txt         Dépendances Python
├── modules/                 Fonctions séparées de main.py (une fonction = un fichier)
│   ├── __init__.py            liste ALL des modules
│   ├── print_session.py       prise connectée, consommation réelle, photo de fin, surveillance IA
│   ├── timelapse.py  mqtt_publisher.py  push_notify.py  share_link.py  order_tracking.py
│   ├── auto_backup_routes.py  feedback.py  remote_instances.py  slicer_profiles.py
│   └── clients.py  trash_routes.py  tigertag.py  sosprint_helpers.py
├── interface/               Interface (JavaScript pur, sans compilation)
│   ├── index.html  script.js  style.css
│   └── sw.js                  service worker (servi à /sw.js)
├── packaging/               Empaquetage de l'application de bureau
│   ├── launcher.py            lanceur (PyInstaller)
│   ├── stellio-setup.iss      installateur Windows (Inno Setup)
│   └── entitlements.plist     droits macOS (signature)
├── languages/               Traductions (8 langues) et changelog.json
├── assets/                  Images, icônes, polices (vendor/)
├── tests/                   Tests pytest
├── tools/                   split_module.py, range.py, smoke_boot.py, stellio_manager.bat (lancement de test sous Windows)
├── release-notes/           notes_version_X.Y.Z.txt (texte des releases)
├── docs/                    ARCHITECTURE.md, DEMO.md, captures d'écran
├── i18n/                    scripts de traduction
├── apk/  relay/             application Android compagnon, relais
├── install-pi.sh            installation Raspberry Pi / Linux (adresse publiée, voir ci-dessous)
├── stellio-lxc.sh           installation Proxmox LXC (adresse publiée, voir ci-dessous)
├── CODEMAP.md  llms.txt  README*.md  LICENSE  THIRD_PARTY_LICENSES.md  CODE_SIGNING_POLICY.md
└── .github/workflows/       build-and-sign.yml (compilation, signature, release), tests.yml (pytest)
```

Restent à la racine, volontairement : `install-pi.sh` et `stellio-lxc.sh` (leurs adresses `raw.githubusercontent.com/.../main/…` sont publiées dans les README et
utilisées par les conteneurs déjà installés : leur commande `update-stellio` lance `~/stellio/install-pi.sh`), `requirements.txt`, `LICENSE`,
`CODE_SIGNING_POLICY.md` (lu par GitHub et par SignPath) et `check_deps.py` (importé par main.py, le lanceur et le workflow).

Règle d'un module : il déclare les services qu'il utilise de main.py (`_REQUIRED`), ses routes (`_ROUTES`) et une fonction `init(globals())`
appelée par main.py. Créer un module : `python tools/split_module.py <nom> <ligne_début> <ligne_fin> "<description>"`
(les bornes se trouvent avec `python tools/range.py <première_fonction> <dernière_fonction>`).
Contrôle complet avant publication : `python -m pytest tests -q` puis `python tools/smoke_boot.py main.py routes.json`.

## Étapes suivantes proposées (non faites)

| Étape | Déplacement | Ce qu'il faut modifier | Risque |
|---|---|---|---|
| B | `stellio-setup.iss`, `entitlements.plist`, `stellio_manager.bat`, `install-pi.sh`, `stellio-lxc.sh` vers `packaging/` | workflow, scripts d'installation (adresse du script publiée dans les README) | Moyen |

Remarque : l'application sert son dossier comme fichiers statiques ; depuis la 1.0.5 un filtre (`_block_source_files`) renvoie 404 pour `.py`, `.sh`, `.yml`, `.db`…,
`/modules/`, `/tests/` et `/tools/`. Les adresses `/script.js` et `/style.css` sont servies depuis `interface/` : elles ne changent pas.
