# Démo publique de Stellio (lecture seule)

`STELLIO_DEMO=1` transforme une instance en démo : elle fabrique 12 modèles 3D libres (générés par le code, domaine public), les indexe, et ouvre l'interface en **invité (lecture seule)** en un clic, sans écran de connexion. Un bandeau « Démo publique en lecture seule » est affiché.

## Ce qui est bloqué
- Toute écriture (rôle invité) : sources, tags, commandes, paramètres, etc.
- Inscriptions (`/api/auth/register`) et fonctions coûteuses : recherche sémantique/photo IA, imbrication (nesting), génération de miniatures à la demande, prédiction de temps IA.
- Accès aux secrets (comptes, accès distant, logs, sauvegardes, mises à jour) : déjà masqués pour les invités.

## Installation automatique (recommandée)
Sur l'hôte Proxmox, en root :
```
CF_TOKEN=<jeton du tunnel> bash stellio-demo-lxc.sh
```
Le script crée le conteneur Debian 12, installe Stellio, active `STELLIO_DEMO=1`, limite les ressources, ajoute le Benchy dans `demo_models/Benchy/` (avec un fichier `CREDITS.txt`) et installe le tunnel Cloudflare si `CF_TOKEN` est fourni. Variables : `CTID`, `HN`, `STORAGE` (sinon menu de choix), `TEMPLATE_STORAGE`, `BRIDGE`, `CORES`, `RAM`, `DISK`. Mise à jour : `pct exec <CTID> -- update-stellio`.

## Installation manuelle
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

## Isolation du réseau local
La démo ne doit jamais pouvoir joindre tes appareils (NAS, imprimantes, PC). Deux protections se cumulent :
- **Dans l'application** : en mode démo, toute connexion sortante vers 10/8, 172.16/12, 192.168/16, lien local ou multicast est refusée (seuls la boucle locale et le DNS passent). Les imprimantes de la démo sont fictives, et la détection réseau est désactivée.
- **Dans Proxmox** : `stellio-demo-lxc.sh` crée un pare-feu pour le conteneur qui interdit les réseaux privés (hors DNS). Il faut que le **pare-feu du datacenter soit activé** (Datacenter → Pare-feu → Options). Pour aller plus loin, mets le conteneur dans un VLAN dédié.

## Bonnes pratiques
- Limite le conteneur (2 vCPU, 2 Go RAM) et ajoute une règle de limitation de débit Cloudflare (WAF → Rate limiting) sur `/`.
- Remets l'instance à zéro si besoin : `systemctl stop stellio && rm -rf /opt/stellio_demo_data && systemctl start stellio`.
- Ne connecte aucune imprimante, aucun compte, aucune clé API sur cette instance.
- Mets-la à jour avec la même commande que ton installation normale.

## Captures du README
`docs/demo.gif` et `docs/screenshots/*.png` ont été générés depuis cette démo (thème sombre, 1400×820). Pour les refaire : lance la démo en local, puis capture les pages Bibliothèque, Visionneuse, Filtres, Réparation, Convertisseur.
