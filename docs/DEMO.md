# Démo publique de Stellio (lecture seule)

`STELLIO_DEMO=1` transforme une instance en démo : elle fabrique 12 modèles 3D libres (générés par le code, domaine public), les indexe, et ouvre l'interface en **invité (lecture seule)** en un clic, sans écran de connexion. Un bandeau « Démo publique en lecture seule » est affiché.

## Ce qui est bloqué
- Toute écriture (rôle invité) : sources, tags, commandes, paramètres, etc.
- Inscriptions (`/api/auth/register`) et fonctions coûteuses : recherche sémantique/photo IA, imbrication (nesting), génération de miniatures à la demande, prédiction de temps IA.
- Accès aux secrets (comptes, accès distant, logs, sauvegardes, mises à jour) : déjà masqués pour les invités.

## Mise en place sur un LXC Proxmox (Debian 13)
1. Installe Stellio comme d'habitude (`install-pi.sh`) dans un conteneur **dédié** (jamais avec tes vraies données).
2. Dans `/etc/systemd/system/stellio.service`, ajoute dans `[Service]` :
   ```
   Environment="STELLIO_DEMO=1"
   Environment="STELLIO_DATA_DIR=/opt/stellio_demo_data"
   ```
3. `systemctl daemon-reload && systemctl restart stellio`. Au premier démarrage, les modèles sont créés dans `/opt/stellio_demo_data/demo_models` puis indexés (1 à 2 minutes).
4. Expose-la avec un tunnel Cloudflare (nom fixe, ex. `demo.stellio-app.com`) : **Zero Trust → Tunnels → Public hostname → `http://IP_DU_CONTENEUR:5000`**. Ne redirige aucun port de ta box.
5. Dans le README, l'URL `https://demo.stellio-app.com` doit correspondre à ce nom.

## Bonnes pratiques
- Limite le conteneur (2 vCPU, 2 Go RAM) et ajoute une règle de limitation de débit Cloudflare (WAF → Rate limiting) sur `/`.
- Remets l'instance à zéro si besoin : `systemctl stop stellio && rm -rf /opt/stellio_demo_data && systemctl start stellio`.
- Ne connecte aucune imprimante, aucun compte, aucune clé API sur cette instance.
- Mets-la à jour avec la même commande que ton installation normale.

## Captures du README
`docs/demo.gif` et `docs/screenshots/*.png` ont été générés depuis cette démo (thème sombre, 1400×820). Pour les refaire : lance la démo en local, puis capture les pages Bibliothèque, Visionneuse, Filtres, Réparation, Convertisseur.
