# Sécurité / Security

## Protections intégrées / Built-in protections
- Connexion obligatoire sur toute l'API (seules quelques routes publiques : `/api/ping`, `/api/auth/*`…) · Login required on the whole API
- Blocage des tentatives de connexion répétées (par identifiant) · Login rate limiting
- Jeton CSRF sur toutes les écritures (`X-CSRF-Token`) · CSRF token on every write
- Chemins limités aux sources configurées (anti `../`) · Paths restricted to configured sources
- Cookies `HttpOnly` + `SameSite=Lax`, en-têtes `X-Frame-Options`, `nosniff`, CSP · Hardened cookies and headers

## Ajouts 1.1.7 / Added in 1.1.7
- **Sessions** : liste des appareils connectés, révocation (coupure à la requête suivante, 15 s au plus) · Active-session list and revocation
- **Plugins** : processus séparé, environnement nettoyé, 10 s, 512 Mo — **pas un bac à sable** ; catalogue https public + SHA-256 obligatoire · Plugins are separate processes, **not a sandbox**; catalog needs public https + mandatory SHA-256
- **Rôles** (admin / gestionnaire / opérateur / utilisateur simple / invité) et permissions par imprimante, projet, dossier · Roles and fine-grained permissions
- **Journal d'audit** : adresse IP et acteur masqués pour les invités · Audit log hides IP and actor from guests
- **Archive G-code** et **plateau** : réservés au propriétaire (le démo n'y accède pas) · Owner-only
- **Démo publique** : lecture seule, aucun fichier récupérable · Read-only public demo

## Mettre Stellio derrière HTTPS (édition serveur) / Serving Stellio over HTTPS
Ne publiez jamais Stellio en HTTP simple sur Internet. / Never expose plain HTTP to the Internet.

**Option 1 — Caddy (certificat automatique / automatic certificate)**
```
stellio.example.com {
    reverse_proxy 127.0.0.1:5000
}
```

**Option 2 — Cloudflare Tunnel** : `cloudflared tunnel --url http://127.0.0.1:5000` (ou tunnel nommé / or a named tunnel).

Puis, dans l'environnement de Stellio / then in Stellio's environment:
```
STELLIO_COOKIE_SECURE=1
```
Le cookie de session ne voyage alors qu'en HTTPS ; l'en-tête HSTS est ajouté automatiquement quand le proxy envoie `X-Forwarded-Proto: https`.
The session cookie then travels over HTTPS only; HSTS is added automatically when the proxy sends `X-Forwarded-Proto: https`.

## Signaler une faille / Reporting a vulnerability
Ouvrez un signalement privé : onglet **Security → Report a vulnerability** du dépôt GitHub (pas d'issue publique).
Open a private report: **Security → Report a vulnerability** on the GitHub repository (no public issue).
