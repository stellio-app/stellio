# API publique Stellio — `/api/v1` (1.1.7)

Spécification machine : `GET /api/v1/openapi.json` ; page lisible : `GET /api/v1/docs`.

## Authentification
Jeton créé dans **Paramètres › Jetons d'API** (affiché une seule fois), envoyé en `Authorization: Bearer stl_…`.
* **Droit** : `read` (lecture seule) ou `write` (lecture + création/mise à jour de tâches, bobines et projets).
* **Portée** : liste de ressources parmi `files`, `printers`, `tasks`, `materials`, `history`, `projects`. Liste vide = tout. Hors portée → `403` avec `code: forbidden_scope`.
* 20 jetons actifs au maximum ; un jeton révoqué cesse de fonctionner immédiatement.

## Routes
| Méthode | Route | Droit | Ressource |
|---|---|---|---|
| GET | `/api/v1/me` | read | — |
| GET | `/api/v1/files` (`q`, `type`, `limit`, `offset`) | read | files |
| GET | `/api/v1/printers`, `/printers/{id}/status` | read | printers |
| GET / POST / PATCH | `/api/v1/tasks`, `/tasks/{id}` | read / write | tasks |
| GET / POST / PATCH | `/api/v1/materials`, `/materials/{id}` | read / write | materials |
| GET | `/api/v1/history` (`result`, `printer_id`, `limit`) | read | history |
| GET / POST / PATCH | `/api/v1/projects`, `/projects/{id}` | read / write | projects |

### Écritures (droit `write`)
| Route | Corps JSON | Notes |
|---|---|---|
| `POST /api/v1/materials` | `name` (obligatoire), `material`, `color_hex` (`#rrggbb`), `capacity_g`, `remaining_g` | Crée une bobine « source : API ». |
| `PATCH /api/v1/materials/{id}` | `remaining_g`, `capacity_g`, `name`, `color_hex` | Valeurs plafonnées ; une bobine d'un autre compte donne `404`. |
| `POST /api/v1/projects` | `name` (obligatoire), `description`, `status` (`in_progress`, `done`, `paused`) | |
| `PATCH /api/v1/projects/{id}` | `name`, `description`, `status` | |

Pas de suppression par l'API : supprimer reste une action de l'interface. Un jeton limité aux ressources `tasks` ne peut pas écrire les bobines (`403 forbidden_scope`).

## Journal d'audit
Chaque appel d'écriture (interface, API, pair) est journalisé : acteur, action, cible, adresse IP, origine distante. Consultable dans l'Atelier avancé › Journal d'audit, exportable : `GET /api/audit/export.csv`. Réservé au propriétaire.

## SDK
* Python (bibliothèque standard seulement) : `sdk/python/stellio_sdk.py`

```python
from stellio_sdk import Stellio
s = Stellio("http://localhost:5000", "stl_votre_jeton")
for m in s.materials(): print(m)
```
* JavaScript (Node 18+ / navigateur) : `sdk/js/stellio-sdk.mjs`

```js
import { Stellio } from './stellio-sdk.mjs';
const s = new Stellio('http://localhost:5000', 'stl_votre_jeton');
console.log(await s.history({ result: 'failed' }));
```
Écritures : `createTask`, `updateTask`, `createMaterial`, `updateMaterial`, `createProject`, `updateProject` (Python : `create_task`, `update_task`, `create_material`, `update_material`, `create_project`, `update_project`).
