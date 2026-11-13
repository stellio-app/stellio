# Stellio Companion (Android)

Application qui ouvre un serveur Stellio (**Raspberry Pi / LXC**) en plein écran. L'édition Windows n'est pas accessible depuis le téléphone.

## Adresses
- **Interne** (réseau local, ex. `http://192.168.1.50:5000`) et **externe** (accès distant, `https://…`) : une seule ou les deux.
- L'application essaie d'abord l'interne, sinon l'externe, et **bascule toute seule** de l'une à l'autre (changement de réseau détecté tout de suite, contrôle toutes les 20 s). Elle revient sur l'interne dès qu'elle est joignable. Les deux adresses sont deux « sites » différents pour le navigateur intégré : la connexion (identifiant) est demandée une fois pour chacune.
- **Liaison par QR code** : dans Stellio, QR code au format « App » (`stellio://connect?local=…&remote=…`). Bouton « Scanner le QR code de liaison » dans l'app (scanner de Google Play Services, sans permission caméra), ou simplement l'appareil photo du téléphone qui ouvre le lien dans l'app. Une adresse absente du QR ne remplace pas celle déjà enregistrée.
- Si la connexion échoue : écran « Serveur injoignable » (nouvel essai toutes les 8 s) avec **Modifier les adresses**.

## Photos
Les champs photo de Stellio (fichiers terminés, S.O.S Print…) ouvrent l'appareil photo (permission demandée une fois) ; les champs image sans « capture » proposent galerie ou appareil photo. Les photos prises sont enregistrées dans Pictures/Stellio. Android 10 minimum.

## Mise à jour depuis l'application
À chaque ouverture (et au retour au premier plan si le dernier contrôle date de plus de 6 h), l'application lit `apk/version.json` sur GitHub (écrit par la CI avec `apk/stellio.apk`). Si le `versionCode` publié est plus récent que celui installé, une boîte de dialogue propose **Mettre à jour** / **Plus tard**. Le téléchargement passe par le gestionnaire de téléchargements d'Android, la somme SHA-256 est vérifiée, puis l'installateur du système demande confirmation. La première fois, Android demande d'autoriser Stellio à installer des applications. Seul GitHub est contacté (jamais votre serveur).
- Pour publier une mise à jour : augmenter `versionCode` (et `versionName`) dans `app/build.gradle`, puis lancer *Build APK* (ou publier une release).
- La signature doit rester la même d'une version à l'autre (secrets `ANDROID_KEYSTORE_*`), sinon Android refuse l'installation par-dessus.
- Les versions installées avant cette fonction ne se mettent pas à jour toutes seules : installer une fois la nouvelle APK à la main.

## Compiler
- GitHub : onglet *Actions* → **Build APK** → *Run workflow* (ou push dans `apk-src/`). Résultat copié dans `apk/stellio.apk` (lien du QR code de Stellio).
- Signature : secrets `ANDROID_KEYSTORE_B64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`. Sans eux, clé de debug (une mise à jour par-dessus une APK signée autrement demande de désinstaller l'ancienne).
- En local : Android Studio, ouvrir `apk-src/`, ou `gradle assembleRelease`.
- Une seule dépendance : `play-services-code-scanner` (scanner de QR).
