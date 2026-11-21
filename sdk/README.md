# SDK et plugins Stellio (1.1.7)

* `python/stellio_sdk.py` : client de l'API publique et aide pour les plugins (bibliothèque standard seulement).
* `js/stellio-sdk.mjs` : même client pour Node 18+ / navigateur.
* `examples/hello-plugin/` : plugin minimal prêt à zipper et à installer (Plugins › Catalogue).
* `examples/split-color/` : plugin signé à code intégré (`host`) avec page et routes `/api/x/split-color/` : « Séparer par couleur » (voir docs/plugins.md, « Plugins signés à code intégré »).

Documentation complète : `docs/plugins.md`, `docs/api.md` et la page « Plugins » du wiki (créer et diffuser un plugin). Modèle de dépôt du catalogue : `sdk/plugins-registry/`.
