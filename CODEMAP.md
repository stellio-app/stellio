# CODEMAP — Stellio v0.7.2

Carte de navigation du code. Dépôt : https://github.com/stellio-app/stellio. Les numéros de ligne de `main.py`, `script.js`, `index.html` et `style.css` correspondent aux fichiers analysés pour cette version (`CURRENT_VERSION = "0.7.2"`, `main.py` l.14289) ; ils dérivent dès qu'on édite. Pour retrouver un élément, préférer `grep -n "nom_de_fonction" main.py`. Ce fichier est à la racine du dépôt et référencé par `llms.txt`.

> **Modifications d'octobre 2026** (Qidi Studio, bulle de survol des cartes, import de bobines depuis un tableur, logo TigerTag, `plyer`) : les numéros de ligne cités plus bas correspondent aux fichiers **avant** ces modifications ; pour retrouver une ligne dans les fichiers actuels, ajouter le décalage suivant (nombre de lignes ajoutées avant la ligne citée).
> - `main.py` (24 207 lignes) : **+3** à partir de l.54, **+17** à partir de l.1248 (table `file_origins`), **+168** à partir de l.8310 (route `/api/files/origin` et helpers), **+169** à partir de l.8573 (hook renommage), **+170** à partir de l.9276 (hook déplacement), **+178** à partir de l.9586, **+181** à partir de l.10257, **+182** à partir de l.18744, **+184** à partir de l.20372, **+211** à partir de l.20387 (liste de secours des liens utiles agrandie), **+213** à partir de l.22012, **+199** à partir de l.22035 (lecture de `filament_shops.json` supprimée), **+463** à partir de l.22630, **+464** à partir de l.22742 (à ±1 près dans les zones modifiées). Repères actuels : `_SLICER_CANDIDATES` l.9741, `CURRENT_VERSION` l.15321, `_spool_import_*` l.22832–23084, point d'entrée l.23760.
> - `script.js` (19 290 lignes) : **+4** à partir de l.5139, **+5** à partir de l.7502, **+7** à partir de l.10124, **+9** à partir de l.10128, **+102** à partir de l.10486, **+46** à partir de l.13705 (une partie de ces écarts vient de modifications de `script.js` faites en dehors de cette carte).
> - `index.html` (4 136 lignes) : **+1** à partir de l.1367, **+2** à partir de l.1394, **+5** à partir de l.2362.
> - `style.css` (8 278 lignes) : **+5** à partir de l.5358, **+10** à partir de l.8269.
>
> **Mise à jour 0.7.2 + fonctions restaurées de la 0.6.9** : cette carte décrit les fichiers `main.py`, `script.js`, `index.html`, `style.css` et `languages/*.json` **après** le portage dans la 0.7.2 de sept fonctions de la 0.6.9 qui avaient disparu : séchage des bobines, calibrations, pièces d'usure, rapports mensuels, mises à jour de modèles, notifications push, rôle invité (et le téléchargement Nexprint). Les numéros de ligne sont ceux des fichiers fusionnés (`CURRENT_VERSION = "0.7.2"`, `main.py` l.15140). Les fichiers non refournis (`sw.js`, `launcher.py`, `worker.py`, workflow, `.iss`, `install-pi.sh`, APK, docs traduites, LICENSE…) sont décrits dans les §9–14 d'après la version précédente ; les points non revérifiés sont signalés. La liste de ce qui a été (ou n'a pas été) restauré est au §15.

> **Corrections du 18/10/2026** : (1) licence — `LICENSE` remplacé par le texte de l'AGPL v3 (README et traductions déjà conformes) et clé `about.legal` des 8 fichiers `languages/*.json` + texte de repli d'`index.html` l.3002 remplacés par « © 2026 Stellio Project. Distribué sous licence GNU AGPL v3 » (traduit dans les 7 autres langues) ; (2) signature — décision de ne pas signer Windows pour l'instant : `CODE_SIGNING_POLICY.md` réécrite, section « Code Signing » des 8 README corrigée, et `build-and-sign.yml` modifié (ffmpeg épinglé par version + SHA-256 sur Windows/Linux/macOS, contrôle SHA-256 d'UnRAR à renseigner) ; (3) route `/api/files/origin` restaurée dans `main.py` (+167 lignes : table `file_origins`, routes GET/POST, helper `_follow_file_origin` appelé par le renommage et le déplacement) — le tableau de décalages de `main.py` ci-dessus a été étendu en conséquence ; (4) dépendances — `openpyxl` et `xlrd` ajoutés à `check_deps.REQUIRED_MODULES` (listes synchronisées, 31 entrées), `plyer`/`openpyxl`/`xlrd` ajoutés à `launcher._PRELOAD_MODULES`, `--collect-all` pour `reportlab`, `psutil`, `plyer`, `openpyxl`, `xlrd`, `pyaes` ajoutés aux 3 jobs du workflow ; `telethon` et l'absence de versions dans `requirements.txt` conservés sur décision ; (5) confidentialité (19/10/2026) — les 8 `PRIVACY*.md` mis à jour (date, Nexprint, 7 nouvelles puces : push, TigerTag, signalements, mises à jour de modèles, boutiques, instances distantes, ressources web des CDN) ; (6) vérification de `script.js` : les doublons de `addPrinter`, `openAddPrinterModal` et `togglePrinterFields` n'existent plus dans le fichier fourni (rien à corriger, seule la documentation est mise à jour) ; (7) `install-pi.sh` installe le vrai `unrar` avec repli sur `unrar-free` (README mis à jour dans les 8 langues) ; (8) README (8 langues) : `worker.py` décrit comme squelette non utilisé (l.284, fichier conservé) et `Stellio-Setup-<version>.exe` (l.184) ; (9) liens utiles — `filament_shops.json` supprimé, `_DEFAULT_USEFUL_LINKS` = copie complète du JSON, `bambuwiki` ajouté (`main.py` +17 lignes, décalages recalculés ci-dessus) ; (10) ressources web en local (20/10/2026) — `index.html` l.43 et l.46–51 pointent vers `assets/vendor/`, `sw.js` en `stellio-v6`, puce « CDN » retirée des 8 `PRIVACY*` (date 20 octobre 2026), `changelog.json` 0.7.2 complété (+8 éléments, 8 langues) ; images `tigertag-logo.png` et `logo-stellio - Copie.png` supprimées par l'auteur ; CSP de `main.py` laissée inchangée ; (11) UnRAR Windows (20/10/2026) — SHA-256 de l'`UnRAR.exe` extrait (7.22.0, signé win.rar GmbH / DigiCert) épinglé dans le workflow ; reste le SHA-256 des archives macOS ; (12) `.gitignore` réécrit (20/10/2026, voir §14). `script.js` et `style.css` sont inchangés ; `index.html` et `languages/*.json` ne changent que par le texte `about.legal` (une ligne remplacée, aucun décalage). Les numéros de ligne de `build-and-sign.yml` cités ont été recalculés (763 lignes).

| Fichier | Lignes | Rôle |
|---|---|---|
| `main.py` | 23 743 | Backend Flask monolithique (277 routes, 699 fonctions de premier niveau, 833 au total, 9 classes de premier niveau + 4 imbriquées) |
| `script.js` | 19 244 | Frontend : toute la logique client (562 fonctions `function` de premier niveau + de nombreux `window.xxx = function`) |
| `index.html` | 4 131 | SPA : sidebar, 14 pages, 35 modales |
| `style.css` | 8 268 | Thèmes, composants, vues galerie/détails |
| `check_deps.py` | 227 | Vérificateur/réparateur de dépendances Python (voir §9 ; `openpyxl` et `xlrd` ajoutés à sa liste le 18/10/2026) |
| `requirements.txt` | 44 lignes | Dépendances pip (ajout de `pyaes` depuis la 0.6.9, puis de `openpyxl` et `xlrd` pour l'import de bobines) |
| `sw.js` | 71 | Service worker PWA (cache `stellio-v6` depuis le 20/10/2026 ; fichier relu) |
| `worker.py` | 27 | Squelette de worker 3MF — **non utilisé** par `main.py` (voir §9) |
| `conftest.py` | 61 | Configuration pytest : stubs de modules lourds, `STELLIO_DATA_DIR` temporaire |
| `stellio-setup.iss` | 242 | Script Inno Setup de l'installeur Windows |
| `entitlements.plist` | 14 | Droits de signature macOS (hardened runtime) |
| `README.md` | 381 | Présentation publique (EN), fonctionnalités, installation, raccourcis |
| `LICENSE` | 661 | Texte intégral de la **GNU AGPL v3** (19 novembre 2007), cohérent avec le README (voir §13) |
| `CODE_SIGNING_POLICY.md` | 126 | Politique de signature de code (EN), réécrite le 18/10/2026 selon l'état réel : Windows/Linux non signés, mesures d'intégrité en place, politique cible (voir §13) |
| `assets/logo-nom-stellio.ico` | 145 Ko | Icône de l'app, 7 tailles de 16 à 256 px (voir §13) |
| `assets/tigertag-logo.svg` | 89 | Logo TigerTag monochrome, bannière filament (voir §13) |
| `stellio_manager.bat` | 284 | Menu de développement Windows (voir §14) |
| `.gitignore` | 76 | Exclusions du dépôt, réécrit le 20/10/2026 (voir §14) |
| `assets/*.png`, `assets/vendor/` | — | Logos et polices/icônes locaux (voir §14) |
| `library.png`, `monitoring.png`, `slicer.png`, `nesting.png` | 1920 px | Captures d'écran du README |
| `launcher.py` | 159 | Point d'entrée des builds PyInstaller : charge `app/main.py` via `runpy` |
| `install-pi.sh` | 197 | Installeur Raspberry Pi/Linux (venv + service systemd), voir §10 |
| `.github/workflows/build-and-sign.yml` | 763 | Workflow GitHub Actions : build Windows/macOS/Linux + release ; binaires ffmpeg épinglés par SHA-256 (voir §10) |
| `apk/stellio.apk` | 4,8 Mo | App Android compagnon (`com.stellioapp.companion`), WebView — voir §11 |
| `docs/readme/README.{fr,de,es,it,pt,ja,zh}.md` | ~381 chacun | README traduits |
| `docs/privacy/PRIVACY[.fr,.de,…].md` | 62 chacun | Politique de confidentialité en 8 langues (EN = `PRIVACY.md`) |
| `languages/{fr,en,de,es,it,ja,pt,zh}.json` | 1948 clés chacun (+ 3 métadonnées) | Traductions (clés plates `section.cle`), jeux de clés identiques dans les 8 langues |
| `languages/changelog.json` | 5 entrées | Notes de version par langue (0.7.2 : 21 éléments par langue dont 8 ajoutés le 20/10/2026, 0.7.1, 0.7.0, 0.6.9, 0.6.8) |
| `languages/useful_links.json` | 41 liens (23 avec `search_url`) | Liens utiles par défaut, également source des boutiques du stock bas ; « Bambu Lab Wiki » ajouté le 19/10/2026 (groupe Ressources) |

---

## 1. Architecture générale

```
pywebview (fenêtre) ──► http://127.0.0.1:5000 ◄── navigateur / mobile / APK
                              │
                    waitress (threads=16) ── Flask (main.py)
                              │
        ┌─────────────┬───────┴────────┬──────────────────┐
     SQLite       file_cache.json   thumbnails/       imprimantes (MQTT/WS/HTTP)
   (stellio.db)   (index fichiers)  (pyrender…)       Spoolman / TigerTag / Ollama
```

- Flask sert aussi le frontend : `Flask(__name__, static_folder=BASE_DIR, static_url_path='')` (l.3482) ; `GET /` → `index()` (l.5175).
- Auth : session cookie (30 jours), `@login_required` (l.3471), CSRF `_csrf_protect` (l.3502, en-tête `X-CSRF-Token` ↔ cookie `stellio_csrf`), en-têtes de sécurité + CSP `_set_security_headers` (l.3571), limite upload 50 Mo, anti-brute-force `_check_rate_limit` (l.5188). **Rôle « invité » en lecture seule** : `_is_viewer` (l.3535), `_viewer_sanitize` (l.3538) et `_viewer_guard` (l.3547, `before_request` : 403 sur toute écriture hors liste blanche) ; la session d'un invité pointe vers les données du propriétaire (`users.owner_id`), routes `/api/auth/guests*` (l.5311–5390).
- Pairs Stellio ↔ Stellio : clé locale `require_peer_key` (l.7657), routes `/api/peer/*`.
- Dossiers de données (`get_data_path`, l.434) : `~/.stellio` | `%APPDATA%\Stellio` | `$STELLIO_DATA_DIR`. Contient `stellio.db`, `app_settings.json`, `file_cache.json`, `thumbnails/`, `uploads/`, `print_photos/`, `sosprint_conversation_photos/`, `imported_slicer_profiles/`, `trash/`, `flask_secret.key`, ainsi que les sauvegardes automatiques (dossier configurable, `_auto_backup_folder` l.13796) et le logo de devis.
- Variables d'environnement lues par `main.py` : `STELLIO_DATA_DIR` (l.435), `STELLIO_ALLOWED_SOURCE_TYPES` (l.450), `STELLIO_NO_AUTO_INSTALL` (l.79), `STELLIO_LAUNCHER_EXE` (l.778, 789, 15455), `STELLIO_HEADLESS` (l.5475, 23299), `STELLIO_START_MINIMIZED` (l.23303), `STELLIO_SERVER_URL` (l.23315), `STELLIO_PORT` (l.7922, 23316), `STELLIO_FEEDBACK_RELAY` (l.14190).

---

## 2. main.py — sections (par ordre de lignes)

| Lignes | Contenu | Éléments clés |
|---|---|---|
| 1–245 | Bootstrap et dépendances | `check_deps` (optionnel, import l.11–19), copie de repli de `_REQUIRED_MODULES` (l.25–60), `_auto_install_missing_modules` (l.76), `_run_startup_module_check` (l.152), imports |
| 246–430 | File de miniatures | `_queue_thumb_task`, `mark_repair_attempted`, session de génération (`_thumb_session_*`), `get_thumb_timeout`, `_prevent_system_sleep` (l.396) |
| 431–541 | Chemins, corbeille | `get_base_path` (431), `get_data_path` (434), `BASE_DIR/DATA_DIR/DB_PATH` (446–457), `_purge_expired_trash` (487), `_move_file_to_trash` (502) |
| 542–776 | Logs, outils externes, réglages | `setup_logging`, `_check_required_modules` (601), `_setup_rar_tool` (677), `_setup_ffmpeg_tool` (707), `SETTINGS_FILE` (753), `load_settings/save_settings` (756/766) |
| 777–961 | Démarrage auto OS | `is_startup_enabled`, `set_startup_enabled` (838 : registre Windows, LaunchAgent macOS, autostart Linux), `save_cache_on_exit` (922), `_cleanup_expired_shares` (954) |
| 962–1104 | Chiffrement secrets | `encrypt_password`/`decrypt_password`, `decrypt_account_secret`, `migrate_account_passwords_to_random_iv`, `migrate_printer_api_keys` |
| 1105–1717 | Base de données | `get_db` (1105), `init_db` (1111), `migrate_*` (print_history 1407, printer_maintenance 1451, print_photos 1599, manual_filament_spools 1613, users_recovery_code 1645) |
| 1718–2984 | Connexions imprimantes | `_build_bambu_result_from_state` (1718), `BambuPersistentConnection` (1786, MQTT), flux caméra MJPEG/RTSP (1901/1963), découverte LAN (SSDP, broadcast, FlashForge : 2017–2318), `ElegooSDCPConnection` (2343), `CrealityConnection` (2542), `FlashForgePersistentConnection` (2672), `ElegooCC2Connection` (2809), Klipper/Spoolman actif (2942) |
| 2985–3403 | `PrinterManager` (l.2985) | Dispatch par type (`octoprint`, `prusalink`, `klipper`, `bambu`, `elegoo_sdcp`, `elegoo_cc2`, `creality`, `flashforge`), statut normalisé |
| 3404–3606 | Sécurité & app Flask | `parse_printer_config` (3404), `is_first_launch`, hash mots de passe (`hash_pw_strong` 3434), code de récupération, `login_required` (3471), `STELLIO_COMPANION_APK_URL` (3480), `app = Flask(...)` (3482), CSRF, en-têtes, gestionnaires 413/500 |
| 3607–3723 | Archives | `UnsafeArchiveError` (3607), `safe_extract_zip/tar/rar/7z`, chemins virtuels d'archive (`make_virtual_archive_path` 3661), `list_archive_3d_entries` (3664), `read_archive_entry_bytes` (3703) |
| 3724–3941 | Cache fichiers | `load_file_cache`/`save_file_cache`/`invalidate_cache`, `_migrate_file_cache_schema` (3797), `_backfill_multiplate_tags` (3869), `mark_download_complete_and_refresh_thumbnail` (3928) |
| 3942–5110 | Miniatures et analyse 3D | `process_generation_queue` (3942, `thumb_worker` 3948), 3MF multi-plaques (`load_3mf_mesh` 4380, `get_3mf_plate_count` 4198), rendu `generate_thumbnail_pyrender` (4615) → `_raster` (4837) → `_matplotlib` (4949) → `create_fallback_thumbnail` (4559), `analyze_3d_file` (5014) |
| 5111–5478 | Auth & configuration | `POST /api/files/analyze`, `/api/auth/*` (inscription, login, question secrète, récupération), `/api/app-config` |
| 5479–5833 | Sources | `/api/sources*` (suggestions 5511, ajout 5565, drop 5607), `/api/files/upload-drop` (5678) |
| 5834–6163 | Comptes externes | `/api/accounts*` (Thingiverse, MakerWorld), `validate_thingiverse_account` (5901) |
| 6164–6857 | Mesh, miniatures & tags (API) | `/api/file/mesh` (6166), `/api/thumb*` (6306–6684), `reconcile_thumbnails_with_disk` (6488), `pregenerate_thumbnails_on_startup` (6379), `/api/tags*` (6696–6857) |
| 6858–7586 | Scan des sources | `extract_archive_to_disk` (6858), `scan_local_folder` (6929), `scan_smb_folder_recursive` (6983), `deduplicate_files_hybrid` (7048), `_auto_tag_new_files` (7113), `_do_background_scan` (7160), `_auto_scan_scheduler` (7337), `GET /api/files` (7363), `/api/files/changes`, `/api/scan/delta` (7566) |
| 7587–8114 | Partage et instances distantes | `/api/files/share`, `/share/<token>`, `/api/remote-instances*`, `/api/peer/*`, `_scan_lan_for_stellio` (7920) |
| 8115–8743 | Opérations fichiers | `_get_all_source_paths`, `_is_path_within_sources` (8131), `/api/files/{open-with,exists,delete,delete-batch,restore-batch,rename,duplicates,duplicates/similar}`, `GET/POST /api/files/origin` (« Origine du modèle » : `api_get_file_origin`, `api_set_file_origin`, `_origin_norm_path`, `_origin_path_allowed`, ajoutés le 18/10/2026 juste après `/api/files/exists`), `_follow_file_origin` (appelé par `rename` et `move`) |
| 8744–9189 | Stats, historique, photos | `/api/stats` (8744), `/api/print-history*` (8886, note, coût), `/api/print-photos*` (9068) |
| 9190–9420 | Déplacer / décompresser | `/api/browse-folder`, `/api/files/{move,decompress,cleanup-archive}` (`move` appelle `_follow_file_origin`), `/api/archive/extract-entry` |
| 9421–10714 | Slicers | `get_slice_temp_dir`, détection (`_SLICER_CANDIDATES` 9571, `_locate_slicer[_macos]`, `detect_installed_slicers` 9751), `run_silent_slice` (9950), estimation (`process_slice_estimate_queue` 10088), parsing G-code (`parse_bambu_orca_gcode3mf`, `parse_cura_gcode`…), `/api/slicer/*` (10199–10516), `/api/picker/*`, `/api/test-connection` (10648) |
| 10715–12193 | Téléchargement de modèles | `/api/download*` (dossier, progression, annulation), `printables_get_*` (10904), `makerworld_*` (11197–11445, token 11353), `api_download_file` (11446–12079), `save_download_history` (12115), `/api/download-history` (12129), `/api/file/data` (12162) |
| 12194–12396 | Favoris, file d'attente, présence | `/api/favorites`, `/api/print-queue*`, `/api/presence/*` |
| 12397–12721 | Notifications | `/api/notifications*`, `_send_native_notification` (12424, `plyer`) ; **dédoublonnage par sujet** : `_normalize_dedup_key` (l.12588) retire un suffixe de date, `api_create_notification` ne crée qu'une notification par `dedup_key` quelle que soit sa date (met seulement à jour le message), `_dedupe_notifications_once` (l.12594, appelée au chargement l.12618) fusionne les anciens doublons |
| 12722–13021 | Projets | `/api/projects*` |
| 13022–13056 | Statut des comptes | `/api/accounts/status` |
| 13057–13578 | Réparation, conversion, intégrité | `/api/files/{repair,convert,convert-batch}`, `_repair_mesh_inplace` (13185), `/api/integrity/*` (13365–13578) |
| 13579–14184 | Sauvegarde | `build_backup_zip_bytes` (13579), `/api/backup/{export,export-native,import}`, **sauvegarde automatique** (`_load_auto_backup_config` 13744, `_auto_backup_scheduler` 13914, `run_auto_backup` 13876, `_restore_backup_zip` 13980, `/api/backup/auto/*` 14046–14160) |
| 14185–14443 | Suggestions & signalements | `_feedback_*` (14185–14285) : issues GitHub via relais, `/api/feedback/{config,submit,requests,request/<n>,close,remove}` (14284–14429) |
| 14444–14621 | Diagnostic et logs | `_redact_secrets` (14444), `_collect_diagnostic_info` (14484), `build_diagnostic_zip_bytes` (14566), `/api/logs/export[-native]` |
| 14622–15043 | Devis et débogage | logo du devis (`_load_quote_logo` 14673, `/api/quote/logo` 14688–14714), `_quote_pdf_encryption` (14726, `pyaes` optionnel), `build_quote_pdf_bytes` (14754), `/api/quote/export[-native]`, `/api/logs/tail` (14985), `/api/debug/*` (15025–15031) |
| 15044–15305 | Réglages, onboarding, changelog | `/api/settings` (+ `/undo`), `CURRENT_VERSION = "0.7.2"` (15140), `load_changelog` (15144), `/api/suggestions` (15162), `/api/onboarding/*`, `/api/changelog/*` |
| 15306–15832 | Mise à jour | `_fetch_expected_sha256` (15306), `check_for_updates` (15355), `install_update` (15450), `download_update` (15713), `/api/update/*` (15762–15815) |
| 15833–16656 | Imprimantes (API) | `/api/printers*` (CRUD, découverte, statut, caméra, alimentation, heures), maintenance (`_serialize_maintenance_task` 16365, `/api/printers/maintenance/*`, `.../due` 16610) |
| 16657–16713 | Arrêt app | `_cleanup_before_exit` (16657), `/api/app/quit`, `/api/app/save-cache` |
| 16714–17254 | IA (Ollama) | `get_ollama_base_url`, `_call_ollama` (16738), `AIDisabledError` (16760), `_call_ai` (16769), `/api/ollama/models`, `_detect_hardware` (16835), `/api/ollama/recommend-model`, `/api/ai/predict-print-time` (17037), `auto-tag`, `explain-orientation`, `describe-file`, `/api/file-description` |
| 17255–18148 | SOS Print | `_sosprint_*` (17265–17429), `/api/ollama/sos-print[/questions|/next-question]`, `/api/sos-print/conversations*` (17934–18073), `/api/ollama/semantic-search` (18085) |
| 18149–19237 | Profils slicer | `load_slicer_profiles` (18149), parsing (`_parse_slicer_profile_file` 18426, `_parse_zip_bundle` 18350), `/api/slicer-profiles*` (18621–18895), `_autodetect_new_slicer_profiles` (18803), `_analyze_mesh_for_recommendation` (18909), `/api/ollama/recommend-profile` (19115) |
| 19238–19470 | Nesting | `_pack_footprints_shelf`, `_pack_polygons` (19310), `/api/nesting/arrange` (19366) |
| 19471–19561 | Recommandation de profil par lot | `/api/ollama/recommend-profile-batch` (19469) |
| 19562–20390 | Filament, coût, TigerTag | `/api/spoolman/spools` (19560), restock (19621–19674), `_compute_estimated_cost` (19695), `/api/eco/estimate` (19830), AMS / manuel (19860–19943), TigerTag Firebase (19944–20322, `tigertag_auto_detect_studio` 20265), `_get_spoolman_slots` (20323), `/api/filament/spools` (20360) |
| 20391–22207 | Liens utiles et boutiques | `USEFUL_LINKS_FILE` (20371), `_DEFAULT_USEFUL_LINKS` (20372, copie complète des 41 liens du JSON depuis le 19/10/2026), `load_useful_links` (20391), `/api/links`, `/api/filament/buy-links` (20467), moteur de recherche en boutique (`_shop_search_shopify/prestashop/woocommerce` 21834–21979, `load_filament_shops` 22011 (ne lit plus `filament_shops.json`), `_search_spool_in_shops` 22038), `/api/filament/shop-availability` (22138), `/api/filament/low-stock` (22152) |
| 22208–22662 | Pré-impression & inventaire filament | `/api/files/pre-print-check` (22208), `/api/filament/{compatibility,printable-files}`, `/api/files/{assign-filament,filament-assignment,unassign-filament}`, `/api/filament/{tigertag,manual[/<id>]}`, `_consume_filament_slot` (22630) |
| 22663–22804 | Découverte LAN | `get_local_ip`, `_scan_lan_for_spoolman` (22675), `/api/spoolman/discover*`, `/api/slicers/discover*` |
| 22805–22888 | PWA & réseau | `/manifest.json`, `/api/network-info`, `/api/ping`, état d'accès distant |
| 22889–23295 | Accès distant & QR | `_get_cloudflared_path`, `start_remote_access` (22922), `stop_remote_access` (23054), `/api/qrcode` (23072, `source=apk` l.23083), `/api/remote-access*` (23142–23277), adresse personnalisée |
| 23296–23743 | Point d'entrée | `if __name__ in ('__main__', 'stellio_main')` (23296), env `STELLIO_*`, waitress `serve` (23385) ou `app.run` (23387), splash tkinter (23524), `StellioDesktopAPI` (23606), `webview.create_window` (23677), `_bind_drag_drop` (23709), `webview.start` (23733) |

### Classes
Premier niveau : `BambuPersistentConnection` 1786 · `ElegooSDCPConnection` 2343 · `CrealityConnection` 2542 · `FlashForgePersistentConnection` 2672 · `ElegooCC2Connection` 2809 · `PrinterManager` 2985 · `UnsafeArchiveError` 3607 · `NexprintError` 10992 · `AIDisabledError` 16760. Imbriquées : `OPENASINFO` 8220 (ctypes, « ouvrir avec » Windows) · `MEMORYSTATUSEX` 14463 · `_LockedEncryption` 14734 (chiffrement du PDF de devis) · `StellioDesktopAPI` 23606 (pont pywebview).

### Tables SQLite (`init_db`, l.1111)
`users` 1118 · `sources` 1128 · `slicer_jobs` 1138 · `tags` 1145 · `file_tags` 1150 · `account_credentials` 1156 · `favorites` 1169 · `print_queue` 1175 · `notifications` 1185 · `remote_instances` 1197 · `printers` 1209 · `download_history` 1220 · `print_history` 1232 · `file_descriptions` 1243 · `file_origins` (ajoutée le 18/10/2026, l.1254 actuelle ; colonnes `file_path`, `user_id`, `source_url`, `author`, `license`, `notes`, `from_download`, `downloaded_at`, `platform`, `updated_at` ; clé `(file_path, user_id)`) · `print_photos` 1251 · `projects` 1260 · `project_files` 1271 · `spool_assignments` 1282 · `filament_assignments` 1294 · `manual_filament_spools` 1308 · `sos_print_diagnostics` 1320 · `sos_print_conversations` 1334 · `sos_print_messages` 1352 · `printer_maintenance_tasks` 1466 · `spool_drying_log`, `filament_calibrations`, `model_updates`, `printer_parts` (créées par `migrate_stellio_extras`, l.1484 ; 29 tables).

### Fonctions restaurées de la 0.6.9 (repères dans le `main.py` fusionné)

| Lignes | Contenu |
|---|---|
| 1484–1599 | `migrate_stellio_extras` (appelée l.1641) : `users.owner_id` et `users.role`, colonnes de `print_history` (`filament_material`, `filament_label`, `spool_source_type`, `spool_source_id`, `assignment_json`), `printer_maintenance_tasks.part_id`, tables `spool_drying_log`, `filament_calibrations`, `printer_parts`, `model_updates` |
| 3535–3569 | Rôle invité : `_is_viewer`, `_viewer_sanitize` (retire les clés dont le nom contient un indice de secret : clés API, mots de passe, jetons ; appliqué à `/api/settings` et au statut des imprimantes), `_viewer_guard` (`before_request`, vérifie aussi que le compte invité existe encore) |
| 5311–5390 | `/api/auth/guests` (liste, création, mise à jour, suppression) ; `api_login` (5295) et `api_me` (5308) renvoient `role` ; la session d'un invité porte `viewer_id` |
| 6049–6160 | Nexprint : `_nexprint_save_token`, `_nexprint_cookie_from_window`, `/api/accounts/nexprint/browser-login[/status]` (fenêtre pywebview sur le site officiel), clé manuelle via `/api/accounts` |
| 10974–11196 | Nexprint : `NexprintError` (10992), `_nexprint_clean_token`, `_nexprint_json`, `_nexprint_auth_strategies`, `nexprint_get_model_files` (11042) ; branche `nexprint` de `api_download_file` (l.10176 pour l'historique, couleur l.7085) |
| 12440–12622 | Notifications push (`_PUSH_TAGS`, `_server_t` l.12445) : `_push_http_post`, `_push_deliver` (ntfy, Telegram, Discord, webhook), `_push_notify_async` (appelée à la création d'une notification), `/api/push/test` (l.12520), `_push_watch_once` / `_push_watcher_loop` (thread démarré l.23368) |
| 20496–20649 | Séchage : `_drying_advice_for`, `_drying_state`, `/api/filament/drying` (GET, POST, DELETE `<id>`), `/api/filament/drying/due` |
| 20651–20791 | Calibrations : `_clean_calibration`, `/api/calibrations` (GET, POST, DELETE `<id>`), `/api/calibrations/suggest` |
| 20793–20956 | Pièces d'usure : `_clean_part`, `/api/parts` (GET, POST, PUT/DELETE `<id>`, `/<id>/adjust`, `/low`) ; lien avec les tâches de maintenance (`part_id`, décrémentation du stock à la remise à zéro) |
| 20958–21163 | Rapports : `_monthly_report_data`, `/api/reports/monthly`, `build_report_pdf_bytes` (21037), `/api/reports/export[-native]` |
| 21164–21354 | Bilan d'une bobine : `/api/filament/spool-report` (21164) |
| 21355–21546 | Mises à jour de modèles : `_model_updates_collect`, `_check_one_model_update`, `_model_updates_run` (thread), `/api/model-updates` (GET), `/check`, `/<id>/dismiss` |
| 21548–21693 | `_append_stock_aware_warnings` (avertissements de pré-impression : buse abrasive, séchage, calibration manquante ; appelée par `/api/files/pre-print-check`) et `_filament_info_for_file` (matière/bobine associées à un fichier, écrites dans `print_history` aux deux `INSERT`, l.10499 et l.10590) |

---

## 3. main.py — routes API par domaine

Notation : ligne de la déclaration `@app.route` ; 249 routes.

**Auth** (5175–5470) — `GET /` · `GET /api/auth/first-launch` · `POST register|login|logout` · `GET me` · `GET security-question` · `POST recovery-code/regenerate` · `POST reset-with-recovery`

**Invités** (5311–5390) — `GET|POST /api/auth/guests` · `PUT|DELETE /api/auth/guests/<id>`

**Config / sources** — `GET /api/app-config` (5470) · `GET|POST /api/sources`, `GET /api/sources/suggestions`, `PUT|DELETE /api/sources/<id>`, `POST /api/sources/drop`, `POST /api/files/upload-drop` · `POST /api/browse-folder`, `/api/picker/folder|file`, `/api/test-connection`

**Fichiers / bibliothèque** — `GET /api/files` (7363) · `GET /api/files/changes` · `POST /api/files/invalidate-cache` · `GET /api/scan/delta` · `POST /api/files/{analyze, analyze-now, open-with, delete, delete-batch, restore-batch, rename, move, decompress, cleanup-archive, share, repair, convert, convert-batch}` · `GET /api/files/{exists, duplicates, duplicates/similar}` · `GET, POST /api/files/origin` · `GET /api/file/{mesh, plate-count, data}` · `POST /api/archive/extract-entry` · `GET /share/<token>`

**Miniatures** — `GET /api/thumb` (6304) · `GET /api/thumb/{failures, progress, summary}` · `POST /api/thumb/{check, generate-now, regen-batch}`

**Tags / projets / favoris / file d'attente** — `/api/tags` (GET, POST, PUT/DELETE `<id>`, `POST /restore`) · `POST /api/files/tags`, `/api/files/tags/bulk-add` · `/api/projects` (CRUD + `/restore` + `/<id>/files` POST/PUT/DELETE) · `/api/favorites` (GET, POST) · `/api/print-queue` (GET, POST, DELETE, `POST /reorder`)

**Instances distantes & pairs** — `/api/remote-instances` (GET, POST, DELETE `<id>`, `POST <id>/ping|send`, `GET <id>/folders`, `GET /status`, `GET /discover`) · `/api/peer/{folders, identify, handshake, receive-file}`

**Historique / stats / photos** — `GET /api/stats` (8744) · `/api/print-history` (GET, DELETE `<id>`, `DELETE /clear`, `POST <id>/rate|cost`) · `/api/print-photos` (GET, POST, `GET <id>/image`, DELETE `<id>`) · `/api/download-history` (GET, `DELETE /clear`)

**Slicers & profils** — `POST|GET /api/slicer/pre-slice-estimate` · `GET /api/slicer/process-profiles` (nouveau : choix du profil de réglages à l'envoi/devis) · `POST /api/slicer/{send, send-batch}` · `GET /api/slicers/discover` + `POST /decline` · `/api/slicer-profiles` (GET, `import`, `refresh`, `auto-detect`, PATCH `<id>/printer|type`, DELETE `<id>`) · `POST /api/nesting/arrange`

**Téléchargement de modèles / comptes** — `POST /api/download/create-folder`, `POST /api/download` (11444), `GET /api/download/progress/<id>`, `POST /api/download/cancel/<id>` · `/api/accounts` (GET, POST, `/nexprint/browser-login[/status]`, `/<platform>` GET/DELETE, `/<platform>/key`, `/thingiverse/validate`, `/makerworld/{login,verify,disconnect}`, `/tigertag/auto-detect-studio`, `/status`). Plateformes de téléchargement : Printables, MakerWorld, Thingiverse, Nexprint.

**Imprimantes** — `/api/printers` (GET, POST, `discover`, `<pid>` PUT/DELETE, `<pid>/{status, upload, brand, power, camera, camera/stream, hours/add}`, `<pid>/maintenance` GET/POST, `maintenance/{<task_id> PUT/DELETE, <task_id>/reset, due}`)

**Filament** — `/api/spoolman/{spools, discover, discover/decline}` · `/api/filament/{spools, tigertag, manual[/<id>], manual/import, manual/import/preview, buy-links, shop-availability, low-stock, compatibility, printable-files}` · `/api/files/{assign-filament, filament-assignment, unassign-filament, pre-print-check}` · `/api/ai/restock-check` · `/api/eco/estimate`

**Sauvegarde / devis / logs / diagnostic** — `/api/backup/{export, export-native, import}` · `/api/backup/auto/{config GET|POST, missed GET|POST, list, run, restore, delete}` · `/api/quote/{export, export-native, logo GET|POST|DELETE}` · `/api/logs/{export, export-native, tail}` · `/api/integrity/{check, progress}`

**Suggestions & signalements (GitHub)** — `/api/feedback/{config, submit, requests, request/<n>, close, remove}`

**Séchage / calibrations / pièces / rapports / modèles** — `/api/filament/drying` (GET, POST, `DELETE <id>`, `GET /due`) · `/api/calibrations` (GET, POST, `DELETE <id>`, `GET /suggest`) · `/api/parts` (GET, POST, `PUT|DELETE <id>`, `POST <id>/adjust`, `GET /low`) · `/api/reports/{monthly, export, export-native}` · `GET /api/filament/spool-report` · `/api/model-updates` (GET, `POST /check`, `POST <id>/dismiss`)

**Push** — `POST /api/push/test` (réglages `push_*` dans `/api/settings`)

**Notifications / présence** — `/api/notifications` (GET, POST, `<id>` DELETE, `<id>/read`, `read-all`) · `/api/presence/{heartbeat, active}`

**IA / SOS Print** — `/api/ollama/{models, recommend-model, auto-tag, explain-orientation, describe-file, semantic-search, recommend-profile, recommend-profile-batch, sos-print, sos-print/questions, sos-print/next-question}` · `POST /api/ai/predict-print-time` · `GET /api/file-description` · `/api/sos-print/conversations[/<id>, /<id>/photo, /<id>/resolve, /<id>/reopen, /photo/<filename>]`

**Système** — `/api/settings` (GET, POST, `POST /undo`) · `/api/suggestions` · `/api/onboarding/{status, dismiss}` · `/api/changelog/{latest, seen}` · `/api/update/{check, version, download, install}` · `/api/links` · `/api/debug/{session, enable}` · `/api/app/{quit, save-cache}` · `/manifest.json` · `/api/network-info` · `/api/ping` · `/api/qrcode` · `/api/remote-access[/toggle, /custom, /disable-custom, /configure, /disable-fixed]`

**Boutiques (stock bas)** — `load_filament_shops` (l.22011) ne garde que les entrées de `useful_links.json` qui ont un `search_url` contenant `{q}` (23 aujourd'hui), dédoublonnées par `id` ; `languages/filament_shops.json` a été supprimé le 19/10/2026 (il était redondant : ses 4 boutiques figuraient déjà dans les liens utiles). Les adaptateurs de recherche sont Shopify, PrestaShop et WooCommerce (`_SHOP_ADAPTERS`, l.21975).

---

## 4. index.html

- `<head>` (l.1–60) : script d'init thème (l.4), manifest PWA (l.36), `style.css?v=20260513` (l.42), Inter (`assets/vendor/inter/inter.css`, l.43), Font Awesome et MDI (`assets/vendor/`, l.44–45), Three.js r128 + OrbitControls, TrackballControls, STL/OBJ/3MF loaders (`assets/vendor/threejs/`, l.46–51) : **tout est local depuis le 20/10/2026** (auparavant Google Fonts et CDN cdnjs/jsdelivr). `<script src="script.js">` à la fin (l.4158).
- Sidebar : boutons `.nav-btn[data-page]` (l.221–322) : dashboard, library, stats, projects, print-queue, history, gallery, repair, converter, sosprint, printers, spoolman, settings ; bouton Ko-fi `#nav-kofi-btn` en bas (l.335). Une barre de navigation mobile répète les entrées (l.2449–2506).
- Pages (`id="page-*"`) : dashboard 511 · library 738 · stats 747 · projects 848 · print-queue 868 · gallery 888 · history 910 · filters 967 · settings 999 · repair 2072 · converter 2109 · sosprint 2173 · printers 2330 · spoolman 2339 (Inventaire filament : Spoolman / manuel / TigerTag).
- Modales (`id="modal-*"`, 35) : select-type 2513 · backup-options 2535 · local-manual 2586 · smb 2612 · nfs 2657 · slicer-import-assign 2694 · slicer 2713 · nesting 2764 · confirm 2823 · 3d-viewer 2841 · partners 2904 · **feedback 2916** · about 2974 · shortcuts 3003 · rename-source 3040 · filters 3064 · tag-manager 3185 · bulk-tag 3235 · download 3265 · add-remote-instance 3408 · add-printer 3443 · file-actions 3595 · file-metadata 3667 · print-photos 3677 · photo-source 3709 · share-file 3732 · move-file 3769 · delete-file 3798 · rename-file 3816 · duplicates 3838 · qrcode-remote 3873 · qrcode-apk 3926 · whats-new 3972 · bulk-rename 4003 · repair-diff 4074
- Éléments restaurés (0.6.9) : bouton « Rapport mensuel » `openMonthlyReport` (l.751), carte `#model-updates-card` (l.956), accordéons Paramètres « Notifications push » (l.1717–1769) et « Comptes invités » (l.1770–1786), tous deux `.viewer-hide`, carte de compte Nexprint (l.1822–1841, bouton `#nexprint-login-btn` → `nexprintBrowserLogin()`, clé manuelle `#nexprint-api-key`), bouton « Pièces d'usure » `openPartsModal` (l.2335) et `.viewer-hide` sur « Ajouter une imprimante » (l.2332), bloc `#slicer-calib-box` dans la modale slicer (l.2723). Les fenêtres des pièces et du rapport mensuel sont construites dynamiquement par `script.js`.
- Widget « Comptes externes » (`#dashboard-widget-accounts`, l.683–693, id de widget `accounts`) : liste Thingiverse, MakerWorld, Nexprint et TigerTag avec leur état de connexion ; rempli par `_loadDashboardAccounts` (script.js l.2993) à partir de `/api/accounts/status`. Fonctionne comme les autres widgets (déplaçable, masquable, ordre mémorisé).

---

## 5. script.js — zones fonctionnelles

| Lignes | Zone | Fonctions principales |
|---|---|---|
| 1–200 | `I18N` | objet `I18N` (l.1–104 : `init` 31, `t` 79, `apply` 96), `_supportedLangs` zh/en/es/fr/de/it/ja/pt, dossier `/languages`, repli `fr` ; `API` ; enregistrement du service worker (l.192–196) |
| 203–350 | Init & PWA | `installStellioApp`, `_getCsrfCookie` (215), `let IS_VIEWER` (219), `window.fetch` surchargé (222, ajoute le jeton CSRF et affiche un toast « lecture seule » sur un 403 d'invité), `DOMContentLoaded` (l.331) |
| 352–607 | Config, sauvegarde manuelle | `loadAppConfig`, `applyAllowedSourceTypes`, `exportBackup`, `runBackupExport`, `importBackup`, `showConfirmDialog` (529), `showBackupRestartPopup`, `initKofiButton` (594) |
| 608–892 | Suggestions & signalements | `_fb*`, `openFeedbackModal` (678), `submitFeedback` (713), `loadFeedbackList`, `openFeedbackDetail`, `closeFeedbackRequest`, `checkFeedbackUpdatesOnStartup` (878) |
| 893–1013 | Widgets tableau de bord « Sauvegardes » / « Demandes GitHub » | `openBackupSettings`, `_loadDashboardBackups` (905), `dashboardBackupNow`, `_loadDashboardIssues` (968) |
| 1014–1306 | Sauvegarde automatique | `loadAutoBackupSettings` (1069), `saveAutoBackupSettings`, `runBackupNow`, `checkMissedBackupOnStartup` (1176), `loadBackupList`, `restoreBackupFromList`, `deleteBackupFromList` |
| 1307–1471 | Intégrité | `startIntegrityCheck`, `pollIntegrityProgress`, `renderIntegrityResults`, `deleteFileFromIntegrity`, `repairFileFromIntegrity` |
| 1472–1671 | Clavier & survol | `setupKeyboardShortcuts` (l.1505), navigation fléchée, `setupHoverDelegation` |
| 1672–2283 | Langues, miniatures, favoris, file d'attente | `populateLanguageSelectors`, `generateVisibleThumbnails`, `toggleHighContrast`/`toggleReduceMotion` (1779/1784), `undoLastSettingsChange`, `refreshFileThumbnail`, `checkFavoritesRestock`, `loadFavorites`, `loadPrintQueue`, `renderPrintQueue`, `setupPrintQueueDragDrop` |
| 2284–2524 | Archives, auth, nouveautés | `decompressFile`, `extractArchiveEntry`, `checkAuth` (2413), `showPanel` (2432, panneaux d'auth), `showApp` (2439), `checkWhatsNew` (2491) |
| 2525–3114 | Tableau de bord | `loadDashboard` (2525), checklist d'onboarding, config/ordre des widgets (`applyDashboardConfig`, `_setupDashboardDragAndDrop` 2706), `_loadDashboard*` (sos, favoris, projets, stats, maintenance, file, téléchargements, instances, comptes externes, mise à jour, suggestions) ; les widgets imprimantes/historique/stock/fichiers récents sont plus bas (l.3748–3888) |
| 3115–3388 | Notifications & présence | `goToFileInLibrary`, `loadNotifications`, `createNotification`, `startPresence`, `maybeFireBrowserNotifications` |
| 3389–3538 | Visite guidée | `getTourSteps`, `_showTourStepAt`, `endTour` |
| 3539–3747 | Palette de commandes Ctrl+K | `_staticCommands`, `_navCommands`, `_fileCommands`, `_tagCommands`, `_filamentCommands`, `_slicerProfileCommands`, `_executeCommand` (3708) |
| 3748–3888 | Widgets tableau de bord (suite) | `_loadDashboardPrinters`, `_loadDashboardHistory`, `_loadDashboardStock`, `_loadDashboardRecentFiles` |
| 3889–4062 | Toasts | `showToast`, `showUndoToast`, `showGenericUndoToast` |
| 4063–4236 | Découverte & démarrage | `checkSpoolmanAutoDiscovery`, `checkSlicerDefaultDiscovery`, `checkAccountsStatusOnStartup`, `startAutoFileMonitor` |
| 4237–4446 | Utilitaires UI, sources | `escapeHtml`, `formatSize`, `openLinksModal` (4259), `openModal`/`closeModal`, `loadSourceSuggestions`, `pickPhoto` (4361), `addSource` |
| 4447–4770 | Instances distantes | `loadRemoteInstances`, `discoverRemoteInstances`, `sendFileToRemoteInstance`, `_openRemoteFolderPicker` |
| 4771–5772 | Bibliothèque | `loadSources`, `loadFiles` (4845), `pollScanProgress`, `renderFileCard` (5111), sélection multiple (`window.toggleSelectionMode` 5179…), `renderFiles` (5400), `buildFolderBlock`, `renderChunk`, génération/suivi de miniatures |
| 5773–6153 | Tags & renommage en masse | `loadTags`, `openTagManagerModal`, `applyTagsToFile`, `openBulkRenameModal`, `_computeBulkRenameName`, `applyTagsToSelection` |
| 6154–6472 | Téléchargement de modèles | `loadDownloadSources`, `openDownloadModal` (6187), `handleDownload`, `startDownload`, toasts de progression, `cancelDownload` |
| 6473–6700 | Filtres | `applyFilters` (6473), `openFiltersModal`, filtres sauvegardés (`_loadSavedFilters`, `renderSavedFiltersList`) |
| 6701–6870 | Slicer (envoi) | `openFileWith`, `sendToSlicer` (6727), `_loadSlicerQuickEstimate`, `_runPrePrintCheck`, `_loadProcessProfileSelect` (6811, choix « Réglages du slicer »), `_loadSlicerSpoolBox` |
| 6871–7479 | Visionneuse 3D | `open3DViewer` (6940), `load3DModel` (7324), orientation (`computeOverhangVertexColors`, `computeOrientationSuggestions`, `suggestBestOrientation`), multi-plaques (`goToPlate`) |
| 7480–8128 | Profils slicer & recommandation | `loadSlicerProfiles`, `renderSlicerProfiles`, `importSlicerProfiles`, `autoDetectSlicerProfiles`, `requestProfileRecommendation` (7958), `renderProfileSuggestions` (8005), `_refineSuggestionTime` (8064) |
| 8129–8256 | Nesting | `openNestingModal`, `runNesting`, `renderNestingPreview`, `sendNestedPlateToSlicer` |
| 8257–9079 | Paramètres | thème/accent (`applyTheme`, `applyFabricant`), `initSettings` (8292), Spoolman (8383), Ollama/IA (8467–8571), scan auto (8572), inventaire manuel (8638), démarrage auto (8675), tarifs d'impression (8761–8964), devis et logo (8965–9079) |
| 9080–9342 | Ollama | `testOllamaConnection`, `recommendOllamaModel`, `ollamaAutoTag` |
| 9343–10078 | SOS Print | `runSosprintDiagnosis` (9448), `renderSosprintQuestionStep`, `loadSosprintHistory`, `resumeSosprintConversation` |
| 10079–11630 | Inventaire filament | `loadSpoolmanPage` (10090), `loadManualSpoolInventory`, `renderManualSpoolGrid`, `openSpoolInventoryModal`, `showSpoolDetailPopup` (11466), `renderSpoolmanGrid` (11578) |
| 10523–11393 | **Fonctions restaurées (0.6.9)** | `applyRoleUI` (10523, classe `body.role-viewer` + masquage des `.viewer-hide`) ; extras de la fiche bobine : `_initSpoolDetailExtras` (10562), séchage `_loadSpoolDrying` (10582), calibrations `_loadSpoolCalib` (10695), `_loadSlicerCalibBox` (10769) ; pièces d'usure `openPartsModal` (10806), `loadParts`, choix de pièce dans la maintenance (`_maintenancePartOptions` 10920, `_handleMaintenanceResetPart` 10941) ; alertes `checkPartsLowAlerts` / `checkDryingDueAlerts` / `checkStellioExtrasAlerts` (10954–10983, appelée l.2469) ; invités `loadGuests` (10993), `createGuest` ; push `loadPushSettings` (11083), `savePushSettings`, `testPush` ; rapport mensuel `openMonthlyReport` (11169), `loadMonthlyReport`, `exportMonthlyReport` ; bilan de bobine `_loadSpoolReport` (11267) ; modèles `loadModelUpdates` (11306), `autoCheckModelUpdates` (11378) ; `_prePrintWarningHtml` (11052) |
| 11394–11580 | Détail d'une bobine | `_detailFromSpoolman`, `showSpoolDetailPopup` (11466) |
| 11699–11740 | Nexprint | `nexprintBrowserLogin` (11699) : ouvre la fenêtre de connexion et interroge `/api/accounts/nexprint/browser-login/status` |
| 11631–12024 | Comptes externes & TigerTag | `saveAccountKey`, `makerWorldStep1/2`, `tigerTagAutoDetectStudio`, `loadTigerTagSpools`, `renderTigerTagGrid`, `loadAccountBadges` |
| 12025–12174 | Navigation latérale | `setupNavDragAndDrop`, `applyNavOrderToSidebar`, `setupEventListeners` (12118) |
| 12175–12307 | Auth UI | `loadSecurityQuestionFor`, `showRecoveryCodeModal` |
| 12308–12482 | En-tête, recherche, navigation, mobile | `updateHeaderVisibilityForPage`, `resetGlobalSearch`, **gestionnaire de clic des `.nav-btn` (l.12354–~12393)**, `toggleMobileSidebar` |
| 12483–12714 | Glisser-déposer / upload | `_uploadDroppedFiles`, `__stellioHandleDroppedPaths` (12513), `handleFilePicker` |
| 12715–12979 | Recherche | `isSemanticQuery`, `runSemanticSearch`, `handleSearchInput`, recherches récentes |
| 12980–13259 | Nav mobile, envoi slicer, sélection de dossier | `toggleNavItem` (12980), `DOMContentLoaded` (12997), `_confirmSendToSlicer` (13060), `updateFolderSelectionBar` |
| 13260–13936 | Réparation & convertisseur | `loadRepairFiles`, `showRepairDiff` (13343), `loadConverterFiles`, `renderConverterFiles`, ajout/édition d'imprimante (`window.addPrinter` défini **une seule fois** (l.14067 dans le `script.js` fourni le 19/10/2026 ; l'ancien doublon n'existe plus)) |
| 13937–14256 | Compatibilité imprimante, statistiques | `checkPrinterCompatibility`, `displayCompatibilityIndicator`, `DOMContentLoaded` (14007), `window.loadStats` (14141) |
| 14257–14740 | Historique | notation, coût, raison d'échec, `window.loadHistory` (14464), `_checkHistoryFileExists`, `loadDownloadHistory` (14592) |
| 14741–15019 | Imprimantes | `loadPrinters`, `renderPrinters`, caméras de cartes, `refreshAllPrinters` (14935) |
| 15020–15473 | Maintenance | `openMaintenanceModal` (15043), tâches, `checkMaintenanceDueGlobal`, popups d'alerte |
| 15474–15678 | Stock bas | `checkLowStockOnStartup`, `showLowStockToast`, `showLowStockListPopup`, `showLowStockShopPopup` (15560, recherche de la bobine exacte en boutique) |
| 15679–16252 | Moniteur imprimante, ajout/découverte | `openPrinterMonitor`, `fetchAndUpdateMonitor`, `updateMonitorUI`, `loadPrinterCamera`, `deletePrinter`, `_printerTypeLabel` (15941), `window.discoverPrinters` (15946) |
| 16253–16450 | Mise à jour, quitter, diagnostic | `manualCheckUpdate` (16035), `showQuitConfirmation` (16264), `loadAppVersion` (16311), `enableDebugSessionAndRestart`, `pollDiagnosticConsole`, `exportDiagnosticLogs` (16445) |
| 17943–17955 | Coût | `_applyCostSpoolSelection`, `_applyCostPrinterSelection` |
| 18343–18533 | Projets | `loadProjects`, `renderProjectCard`, `refreshProjectDetail`, `openProjectFormModal` (18408) |
| 18812–19244 | PWA / QR | `_detectMobileBrowserContext`, `_renderPwaBrowserHint`, `_loadQrCode` (18910) |

> Les lignes 16450–17943, 17955–18343 et 18533–18812 ne contiennent pas de fonctions de premier niveau nommées : le code y est organisé en blocs d'écouteurs d'événements (`DOMContentLoaded` aux l.16253 et 16538) et en fonctions imbriquées (coût d'impression/devis, historique, etc.). Utiliser `grep` sur les ids du DOM (`getElementById('…')`) pour les retrouver.

---

## 6. style.css — repères

- 1–60 : historique de téléchargement (`.download-history-section`)
- 62–131 : variables (`:root` 62, `[data-theme="light"]` 94, `[data-fabricant="bambu|prusa|voron|creality"]` 109/115/121/127)
- 134–227 : reset, `.auth-*` (154), `.btn*` (165)
- 229–450 : écran d'authentification, champs `.input-group` (338)
- 452–600 : layout `.app-screen` (452), `.sidebar` (457), `.nav-btn` (519)
- 604–920 : en-tête, recherche (`.search-box` 650), sélecteurs de vue, progression de miniatures
- 921–2000 : `.main-content` (923), grilles de fichiers (gallery/details), `.file-card` (991), badges, boutons d'action, infobulles de métadonnées
- 2678 modales · 2713 visionneuse 3D · 2845 toasts · 3743 historique · 4293 bobines · 4450 cartes d'imprimante · 4545 moniteur · 5354 `.tigertag-banner-logo` · 5543 SOS Print · 6732 tableau de bord · 7235 visite guidée · 7468 palette de commandes
- 7833 accessibilité (contraste élevé 7846, réduction des animations 7886) · 7932 présence légère · 7965 sauvegarde automatique et liste des sauvegardes · 8063 suggestions & signalements · 8114 bouton Ko-fi `.kofi-btn`
- Le reste (2000–7800) n'est pas cartographié ligne par ligne ; chercher par nom de classe.

---

## 7. i18n

- Fichiers `languages/<code>.json` : dictionnaire plat, clés `section.cle` (ex. `spoolman.sort_name`), plus `__dir`, `__name`, `__native`. **1948 clés** (1951 entrées avec les métadonnées) dans chacune des 8 langues (fr, en, de, es, it, ja, pt, zh) ; les jeux de clés sont strictement identiques (aucune clé manquante ni en trop).
- HTML : attributs `data-i18n*` ; JS : `I18N.t('clé')` ; backend : lit `languages/<lang>.json` directement pour le splash (`load_splash_translations`, main.py l.23527–23556) ; le frontend les récupère via `/languages/<lang>.json` (servi par le dossier statique Flask).
- `changelog.json` : `[{version, items:{<lang>:[…]}}]`, lu par `load_changelog` (main.py l.15144, tri par version décroissante). Entrées : 0.7.2 (21 éléments par langue ; 8 ajoutés le 20/10/2026 : licence AGPL v3, origine du modèle, ressources web locales, modules embarqués, `unrar` de l'installeur Linux, liens utiles, confidentialité, builds), 0.7.1 (8), 0.7.0, 0.6.9, 0.6.8 ; la version courante `CURRENT_VERSION` (0.7.2) a donc son entrée.

## 8. Recettes rapides

- **Ajouter une route API** : décorateur `@app.route` + `@login_required` dans la section du domaine (§3). Les méthodes d'écriture exigent le jeton CSRF (`X-CSRF-Token`, ajouté automatiquement par le `window.fetch` surchargé de `script.js` l.222).
- **Ajouter une table** : `init_db` (l.1111) + éventuelle fonction `migrate_*` pour les bases existantes ; penser à l'export/import de sauvegarde (`build_backup_zip_bytes` l.13540, `_restore_backup_zip` l.13941, catégories de la sauvegarde automatique `_merge_backup_categories` l.13920).
- **Ajouter une page** : `<div class="page" id="page-xxx">` dans `index.html`, bouton `data-page="xxx"` dans la sidebar ; le clic est géré par le gestionnaire de `.nav-btn` (`script.js` l.12354) qui affiche `#page-xxx` et appelle les `load*` de la page ; ajouter l'entrée dans `_navCommands` (l.3552, palette) et, si besoin, dans la barre mobile (index.html l.2449+).
- **Nouvelle chaîne UI** : ajouter la clé aux 8 fichiers `languages/*.json`.
- **Nouvelle marque d'imprimante** : classe `*Connection` + `_build_*_result` + `_ensure_*/_stop_*_connection` + découverte, puis dispatch dans `PrinterManager` (l.2985) et dans les routes `/api/printers*` (l.15812–16178).
- **Nouvelle dépendance Python** : `requirements.txt`, `check_deps.REQUIRED_MODULES`, la liste de repli de `main.py` (l.25–63) **et** les `--collect-all` des 3 jobs du workflow (PyInstaller n'analyse pas `main.py`, copié à côté de l'exécutable) ; `launcher._PRELOAD_MODULES` (diagnostic) est une 4ᵉ liste facultative. `pyaes` (optionnel, utilisé l.14742) n'est volontairement que dans `requirements.txt` et dans les `--collect-all`.
- **Nouvelle version** : `CURRENT_VERSION` (l.15101) + entrée en tête de `changelog.json` (⚠️ ne pas dupliquer la version) ; le workflow ne publie une release que si cette version change.
- **Nouveau site de téléchargement de modèles** : s'inspirer de MakerWorld (le plus complet) — `makerworld_get_model_files` (main.py l.11197), connexion en 2 étapes `makerworld_login_step1/2` (11372/11405) + routes `/api/accounts/makerworld/*` (11370–11432), branche dans `api_download_file` (11446), `makerWorldStep1/2` (`script.js` l.11741/11771), carte de compte dans `index.html` (chercher `makerworld`), lien dans `languages/useful_links.json` **et** `_DEFAULT_USEFUL_LINKS` (Nexprint est un deuxième exemple : `nexprint_get_model_files` l.11054, connexion par fenêtre `api_nexprint_browser_login` l.6097, clé manuelle via `/api/accounts`) (main.py l.20372), étiquette/couleur dans l'historique de téléchargements.

---

## 9. Fichiers annexes (build, tests, PWA, installeur)

### check_deps.py
- `REQUIRED_MODULES` (l.28) : 31 tuples `(nom d'import, paquet pip, attribut attendu, paquets conflictuels)`, dont `openpyxl` et `xlrd` (ajoutés le 18/10/2026) ; `TELEGRAM_MODULES` (l.62, `telethon`) optionnel.
- Fonctions : `find_owning_packages` (65), `deep_check_module` (74, vérifie l'import réel **et** un attribut pour détecter un mauvais paquet installé sous le même nom), `auto_install_missing_modules` (84, désinstalle le mauvais paquet puis `pip install --force-reinstall/--upgrade`, retente avec `--break-system-packages`), `check_required_modules` (157), `_cli_main` (185).
- CLI : `python check_deps.py [--fix] [--telegram]` ; code de sortie 1 si une dépendance manque.
- `main.py` l'importe en tête (l.11–19, bloc `try`) et possède une copie de repli de `_REQUIRED_MODULES` si l'import échoue (l.25–63, 31 entrées) : les deux listes sont **identiques depuis le 18/10/2026** (vérifié) ; toute nouvelle dépendance doit être ajoutée aux deux endroits (plus `requirements.txt` et le workflow). `TELEGRAM_MODULES` (`telethon`) n'a pas d'usage dans `main.py` 0.7.2 (aucune référence à Telegram) : `telethon` est **conservé volontairement** (variante Telegram prévue, décision du 18/10/2026) dans `requirements.txt`, `check_deps.py` (`--telegram`) et `launcher.py` (`STELLIO_TELEGRAM_VARIANT`).

### requirements.txt
- Contient en plus de `check_deps` : `pyinstaller`, `PyOpenGL-accelerate`, `telethon`, et depuis la 0.6.9 `pyaes` (optionnel : force de chiffrement AES-256 du PDF de devis, `main.py` l.14742 ; absent de `check_deps`, mais collecté par PyInstaller via `--collect-all pyaes`).
- Linux : `pywebview[gtk]` + paquets système `libgtk-3-0 libwebkit2gtk-4.1-0` (non installables par pip). macOS : pyobjc installé automatiquement.
- `plyer` (utilisé par `_send_native_notification`, main.py l.12424, et listé dans `check_deps.REQUIRED_MODULES`) a été ajouté à `requirements.txt` ; il figure désormais aussi dans la liste de repli de `main.py` (l.25–61).

### sw.js (service worker, enregistré dans script.js l.192–194)
- Caches `stellio-v6-shell` et `stellio-v6-assets` ; les anciens caches `stellio-*` sont supprimés à l'activation ; changer `CACHE_VERSION` pour forcer un renouvellement.
- Stratégie : `/api/*` et `/share/*` jamais interceptés ; `/assets/*` cache-first ; le reste réseau d'abord avec repli sur le cache puis `/index.html`. Seulement les requêtes GET de même origine.
- Pré-cache : `/`, `/index.html`, `/script.js`, `/style.css`. Servi à `/sw.js` par le dossier statique Flask.

### worker.py
- Contient uniquement `process_3mf_task(file_path, plate_index=0)` qui renvoie des valeurs **codées en dur** (15000 sommets, 30000 faces) : c'est un squelette. Aucune référence dans `main.py` (le seul « worker » est `thumb_worker` dans `process_generation_queue`, l.3777). Le README le décrit pourtant comme « background worker (thumbnails, scans) ». Gardé volontairement (décision du 19/10/2026) ; le README (l.284) le décrit désormais comme un squelette non utilisé.

### conftest.py (tests pytest)
- `_try_real_or_stub` remplace par des stubs `trimesh`, `pyrender`, `pymeshfix`, `smbclient`, `rarfile` s'ils ne sont pas installés.
- Définit `STELLIO_DATA_DIR` sur un dossier temporaire et `STELLIO_PORT=0` avant l'import de `main.py` pour ne pas toucher aux vraies données. Les fichiers de tests eux-mêmes n'ont pas été fournis.

### stellio-setup.iss (Inno Setup, Windows)
- Version injectée à la compilation via `/DMyAppVersion=…` (défaut `0.0.0-dev`) ; sortie `output/Stellio-Setup-<version>.exe`.
- Installe `dist\Stellio\*` (sortie PyInstaller) dans `{commonappdata}\Stellio-app`, exécutable `Stellio.exe`, droits `users-full` sur le dossier pour permettre les patchs `.zip` (mises à jour automatiques sans admin).
- Prérequis téléchargés au besoin (PowerShell) : VC++ Redistributable x64 ≥ 14.40 et WebView2 (sans WebView2, Stellio retombe en mode navigateur).
- Si une installation existe (AppId `{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}`) : choix réparer/mettre à jour, désinstaller puis réinstaller, ou annuler. Langues : français, anglais. Option de bureau décochée par défaut ; `/LAUNCH=1` pour lancer l'app après une installation silencieuse.

### entitlements.plist (macOS)
- `allow-jit`, `allow-unsigned-executable-memory`, `disable-library-validation`, `allow-dyld-environment-variables` (nécessaires à l'app PyInstaller signée/notarisée).

### README.md — informations utiles
- Licence AGPL v3 (`LICENSE` aligné le 18/10/2026, voir §13) ; Python 3.8+, Flask 3.0+ ; plateformes annoncées : Windows et Raspberry Pi/Linux (64 bits) ; modèles supportés : STL, 3MF, OBJ.
- Imprimantes : OctoPrint, PrusaLink, Klipper/Moonraker (HTTP), Bambu Lab (MQTT, AMS), Creality (WebSocket, CFS), FlashForge, Elegoo (SDCP).
- Raccourcis : `Ctrl+K` palette, `Ctrl+F` recherche, `Ctrl+N` téléchargement, `Ctrl+,` réglages, `Ctrl+Z` annuler suppression, `Alt+1-8` navigation, `F` favoris, `T` gestionnaire de tags, `?` aide, `Esc`.
- Fichiers cités dans le README et **absents du dépôt** : `bin/` (binaires ffmpeg/unrar par OS, optionnel — ignoré par `.gitignore`), fichiers de tests. Tout le reste (`assets/`, captures `library/monitoring/slicer/nesting.png`, `LICENSE`, `CODE_SIGNING_POLICY.md`) est dans le dépôt (voir §13–14).

---

## 10. Lancement, CI/CD et installation

### launcher.py (point d'entrée des builds figés)
- C'est le script que PyInstaller compile (`launcher.py` → `Stellio.exe` / `Stellio.app` / binaire Linux) ; **`main.py` n'est pas compilé** : il est copié à côté dans un dossier `app/` pour pouvoir être remplacé par les patchs `.zip` d'auto-mise à jour.
- `_app_dir()` (l.10) : localise `app/` — à côté de l'exécutable (Windows/Linux `--onedir`), `Stellio.app/Contents/Resources/app` (macOS), ou à côté du script en mode source.
- `_setup_early_env()` (l.33) ajoute `app/` à `sys.path` ; `_setup_bootstrap_logger` (l.43) écrit `launcher.log` (rotation 2 Mo ×2) dans `<app_dir>/../logs/` ; `_show_fatal_error` (l.56) : MessageBox Windows, sinon Tk, sinon stderr.
- `_preload_dependencies` (l.99) : import parallèle de `_PRELOAD_MODULES` pour diagnostic, **désactivé par défaut** (activer avec `STELLIO_DIAG_PRELOAD=1`) ; `STELLIO_TELEGRAM_VARIANT=1` ajoute `telethon`.
- `main()` (l.116) : positionne `STELLIO_LAUNCHER_EXE` (chemin de l'exécutable, lu par `install_update` main.py l.15455 et par la gestion du démarrage auto l.778/789), fait `chdir(app_dir)` puis `runpy.run_path(main.py, run_name="stellio_main")` — d'où la condition `__name__ in ('__main__', 'stellio_main')` de `main.py` (l.23296).
- La liste `_PRELOAD_MODULES` (l.74) est une 4ᵉ liste de dépendances (en plus de `check_deps`, de la copie de repli de `main.py` et de `requirements.txt`) ; elle contient depuis le 18/10/2026 `plyer`, `openpyxl` et `xlrd` (pas `pyaes`, optionnel).

### .github/workflows/build-and-sign.yml (GitHub Actions, « Build, sign and release Stellio »)
- Déclencheurs : push sur `main` touchant `main.py`, `index.html`, `script.js`, `style.css`, `launcher.py`, `check_deps.py`, `requirements.txt`, `stellio-setup.iss`, `assets/**`, `languages/**`, `bin/**` ; ou lancement manuel avec `dry_run` (build sans release).
- Jobs : `check-version` (lit `CURRENT_VERSION` dans `main.py`, publie seulement si le tag `v<version>` n'existe pas encore → **il faut incrémenter `CURRENT_VERSION` pour déclencher une release**) → `build` (Windows : PyInstaller `--onedir --windowed`, copie des fichiers patchables dans `dist\Stellio\app`, télécharge ffmpeg (version épinglée, SHA-256 vérifié) + UnRAR (SHA-256 de l'`UnRAR.exe` extrait vérifié), crée `Stellio-v<version>-patch.zip` + `.sha256`, compile l'installeur Inno Setup) ‖ `build-macos` (matrice `arm64` sur `macos-latest`, `x86_64` sur `macos-15-intel` ; `.app` signée Developer ID si les secrets `MACOS_CERTIFICATE`, `MACOS_CERTIFICATE_PWD`, `MACOS_SIGNING_IDENTITY` existent, sinon signature ad-hoc, sans notarisation ; ffmpeg `b6.0` + SHA-256 vérifié ; `.dmg` + sha256) ‖ `build-linux` (AppImage x86_64 avec GTK/WebKit, ffmpeg épinglé + SHA-256 vérifié, unrar via apt) → `release` (brouillon GitHub `v<version>` avec `.exe`, `.dmg`, `.AppImage`, `.zip`, `.sha256`).
- Chaque job exécute `check_deps.py --fix` puis `check_deps.py` ; Python 3.11 partout.
- **Modules embarqués par PyInstaller** : chaque job a des `--collect-all` (+ `--hidden-import` `sqlite3`, `ssl`, `hashlib`, `tkinter`, `nest_asyncio`, et des `--copy-metadata` pour `imageio`, `pyrender`, `trimesh`, `Pillow`, `PyOpenGL`, `numpy`). Depuis le 18/10/2026 ils incluent aussi `reportlab`, `psutil`, `plyer`, `openpyxl`, `xlrd` et `pyaes`, **absents auparavant** (alors que `main.py` les importe : devis PDF, widget ressources, notifications natives, import de bobines, chiffrement du PDF) : `main.py` n'étant pas analysé par PyInstaller, ils n'étaient pas garantis dans les builds. ⚠️ `packaging` (import l.15317, mise à jour) n'est pas collecté explicitement : il est probablement tiré par matplotlib, **non vérifié** ; seul un vrai build confirmera le contenu final.
- Les fichiers « patchables » copiés dans `app/` : `main.py`, `check_deps.py`, `index.html`, `script.js`, `style.css`, `assets/`, `languages/`, `bin/` (+ `launcher.py` n'y est **pas**). `worker.py` n'est copié nulle part → confirme qu'il est inutilisé.
- ⚠️ Le patch `.zip` commun est créé dans le job **Windows** : il contient donc aussi `app\bin\` (ffmpeg.exe, DLL, UnRAR.exe). Le README annonce un patch « code source pur » identique pour Raspberry Pi/Linux — à vérifier côté logique d'installation du patch (`install_update`, main.py l.14599).
- L'artefact Windows s'appelle `stellio-installer-unsigned` et le workflow ne contient **aucune** étape de signature Windows (ni `signtool`, ni SignPath, ni scan antivirus) : décision du 18/10/2026 de ne pas signer pour l'instant ; `CODE_SIGNING_POLICY.md` et le README ont été alignés sur cet état. macOS : signature Developer ID si les secrets existent, sinon ad-hoc, sans étape de notarisation.
- Binaires tierces épinglés (18/10/2026) : ffmpeg Windows/Linux = BtbN `autobuild-2026-10-18-13-01` (`ffmpeg-N-127650-geceaa54a38-win64-gpl-shared.zip`, `ffmpeg-N-127651-gb60ab6c9a4-linux64-gpl.tar.xz`), ffmpeg macOS = eugeneware `b6.0` ; SHA-256 calculés sur les fichiers téléchargés, le build échoue en cas d'écart. UnRAR Windows : SHA-256 `a9333c4e…92c3` de l'`UnRAR.exe` **extrait** de `unrarw64.exe` (version 7.22.0, signé Authenticode par win.rar GmbH / DigiCert, fichier fourni par l'auteur le 20/10/2026), contrôle bloquant ; la signature Authenticode est seulement journalisée. L'URL de RARLAB n'ayant pas de numéro de version, une nouvelle version fait échouer le build volontairement jusqu'à vérification et mise à jour de la valeur. UnRAR macOS (`rarmacos-<arch>-723.tar.gz`, variable `RAR_SHA`) : valeurs **vides** → avertissement `::warning::` avec le hash obtenu, **à renseigner** ; UnRAR Linux via apt (signature du dépôt). ⚠️ BtbN purge ses anciens tags `autobuild-*` : l'URL ffmpeg Windows/Linux devra être mise à jour (procédure en commentaire dans le workflow).
- `entitlements.plist` est aussi réécrit par le workflow (même contenu que le fichier du dépôt).

### install-pi.sh (Raspberry Pi / Linux headless)
- Script bash de 180 lignes (`bash -n` passe ; le conflit de fusion git de la version précédente est résolu). L'en-tête donne le conseil « swap » pour les Raspberry Pi à faible RAM (`CONF_SWAPSIZE=2048` dans `/etc/dphys-swapfile`).
- Contenu : refuse root, vérifie `sudo` et la RAM (<1,5 Go → avertissement), `apt-get install` (git, python3-venv, build-essential, ffmpeg, libs JPEG/PNG, OpenBLAS/ATLAS, OSMesa/EGL), puis `apt-get install unrar` à part (voir la note ci-dessous), `git clone`/`reset --hard origin/main` dans `~/stellio` (variable `STELLIO_DIR`), venv `~/stellio/venv`, `pip install -r requirements.txt` (échec toléré, `check_deps.py` répare au démarrage), crée `~/.stellio`, écrit `/etc/systemd/system/stellio.service` (`STELLIO_HEADLESS=1`, `STELLIO_DATA_DIR`, `STELLIO_PORT`, `Restart=always`, `ExecStart=venv/bin/python3 main.py`), l'active et attend jusqu'à 30 s, puis affiche `http://<ip>:5000`.
- Relancer le script met à jour le code (`git reset --hard` + `git clean -fd` : toute modification locale dans `~/stellio` est perdue ; les données restent dans `~/.stellio`).
- `unrar` (corrigé le 19/10/2026) : le script installe le **vrai** `unrar` (section `non-free` de Debian / Raspberry Pi OS, `multiverse` d'Ubuntu), comme le build AppImage ; si le paquet est introuvable il se replie sur `unrar-free` avec un avertissement (RAR5 non pris en charge, options en ligne de commande différentes de celles qu'attend `rarfile`). `main.py` (`_setup_rar_tool`, l.680) ne cherche qu'un binaire nommé `unrar` (`bin/` ou PATH). Le README (8 langues, l.200) parle désormais de `unrar`.

---

## 11. App Android compagnon (apk/stellio.apk)

- Paquet `com.stellioapp.companion`, version `1.0.0` (code 1), minSdk 24, targetSdk 34, libellé « Stellio ». Écrit en Kotlin (coroutines, AndroidX, Material), 912 entrées, `classes.dex` ≈ 9 Mo. **Seul l'APK est fourni, pas le projet Android Studio.**
- Activités : `MainActivity` (lanceur) et `com.journeyapps.barcodescanner.CaptureActivity` (ZXing, scan de QR code). Providers : `androidx.core.content.FileProvider` (partage de la photo prise) et `InitializationProvider`.
- Permissions : `INTERNET`, `ACCESS_NETWORK_STATE`, `ACCESS_WIFI_STATE`, `CAMERA`, `WRITE_EXTERNAL_STORAGE`.
- Classes de l'app (par noms dans le dex) : `MainActivity` (WebView : `setupWebView`, `connectToStellio`, `findReachableUrl`, `registerNetworkMonitor`, `scheduleOfflineCheck`, `startReconnectLoop`, `setupLanguageSpinner`) et `ConnectionPrefs` (adresse du serveur mémorisée). Principe : l'app mémorise l'URL du serveur Stellio (saisie ou scannée par QR code, cf. `/api/qrcode`), teste son accessibilité, charge l'interface web dans une WebView et se reconnecte automatiquement en cas de coupure.
- Distribution : `STELLIO_COMPANION_APK_URL` (main.py l.3480) pointe vers `https://www.github.com/stellio-app/stellio/raw/main/apk/stellio.apk` ; `GET /api/qrcode?source=apk` (l.23083) génère le QR code de téléchargement ; côté web, la prise de photo passe par `pickPhoto` (script.js l.4361) et la modale `modal-photo-source`.
- Pour modifier le comportement natif (appareil photo, flèches de la barre mobile…), il faut le projet Android (`MainActivity.kt`, `AndroidManifest.xml`) — non inclus ici ; la barre de navigation mobile défilable côté web est dans `script.js` (`toggleNavItem` l.12980, non revérifié) et `style.css`.

---

## 12. Documentation traduite

- `docs/readme/README.<lang>.md` (fr, de, es, it, pt, ja, zh) : traductions complètes du `README.md` (mêmes sections, même structure de projet) ; liens relatifs : `../../README.md`, `../../LICENSE`, `../privacy/PRIVACY.md`, `../../library.png`… Toute nouvelle fonctionnalité documentée dans `README.md` doit être reportée dans les 7 traductions (et dans `languages/changelog.json`).
- `docs/privacy/` : `PRIVACY.md` (EN) + `PRIVACY.{fr,de,es,it,pt,ja,zh}.md`, « dernière mise à jour » **20 octobre 2026** (62 lignes chacun, mêmes 8 sections). Contenu : principe « local-first », données stockées localement (bibliothèque, miniatures, configs, clés API chiffrées AES-CFB, historique, logs), services tiers (mises à jour GitHub, Printables/MakerWorld/Thingiverse/**Nexprint**, imprimantes, Cloudflare Tunnel, Ollama distant, Spoolman) et, ajoutés le 19/10/2026 dans la section 4 : **notifications push** (ntfy/Telegram/Discord/webhook, désactivées par défaut), **TigerTag** (Firebase/Google + `api.tigertag.io`), **signalements** (relais Cloudflare Workers → issue GitHub **publique**, consentement explicite, interrogation de l'API GitHub pour le suivi), **suivi des mises à jour de modèles** (activé par défaut, réglage `model_updates_auto`), **recherche de bobines en boutique** et **autres instances Stellio** (dont scan du réseau local) ; la puce « ressources web chargées par l'interface » (CDN Three.js, Google Fonts) a été retirée le 20/10/2026 puisque tout est désormais local ; puis sécurité, droits, contact `contact@stellio-app.com`.
- Politique de confidentialité alignée sur le code le 19/10/2026 (voir ci-dessus). Le README (8 langues) a aussi été corrigé le 19/10/2026 : `Stellio-Setup-<version>.exe` (l.184) et `worker.py` décrit comme squelette non utilisé (l.284). La mention des CDN a été retirée de la politique le 20/10/2026 (Three.js et Inter sont servis en local).

---

## 13. Licence, signature de code et assets

### LICENSE
- Texte officiel de la **GNU Affero General Public License v3** (19 novembre 2007, 661 lignes), remplaçant la GPL v3 le 18/10/2026 ; corps du texte vérifié identique à la version SPDX `AGPL-3.0-only` (la section 13 « Remote Network Interaction » est présente). Aucune ligne de copyright propre au projet n'y figure (usage : l'ajouter dans l'en-tête des sources, p. ex. `main.py`).
- Licence désormais cohérente : `README.md` et ses 7 traductions (badge « License: AGPL v3 » + section « 📜 License ») annonçaient déjà l'**AGPL v3** et renvoient vers ce fichier. La modale « À propos » (`index.html` l.3002, clé `about.legal`) affiche depuis le 18/10/2026 « © 2026 Stellio Project. Distribué sous licence GNU AGPL v3 » (texte de repli en français dans `index.html`, traductions dans les 8 `languages/*.json` ; l'ancienne phrase « Développé avec passion pour la communauté Maker » a été retirée à ta demande).

### CODE_SIGNING_POLICY.md
- Réécrite le 18/10/2026 (126 lignes, EN) pour décrire l'état réel : la signature Windows n'est **pas** en place (choix de ne pas signer pour l'instant). Liée depuis la section « 🔏 Code Signing Policy » du README, dont le texte (8 langues) dit désormais : installeur Windows et AppImage non signés, SmartScreen possible, builds macOS non notarisés, checksums `.sha256` vérifiables.
- Contenu (8 sections) : §1 périmètre ; §2 statut par plateforme (Windows non signé ; macOS Developer ID si secrets sinon ad-hoc, sans notarisation ; Linux non signé) ; §3 mesures d'intégrité en place (`.sha256` de chaque fichier de release, vérification SHA-256 par la mise à jour intégrée — HTTPS seul si aucun checksum publié —, ffmpeg épinglé, release en brouillon publiée à la main) ; §4 limites connues (pas d'Authenticode, checksum issu de la même release, pas de scan antivirus, `requirements.txt` sans versions, purge des tags BtbN) ; §5 vérifier un téléchargement (`Get-FileHash`, `sha256sum`, `shasum`) ; §6 politique cible si la signature est introduite (certificat EV/OV, clé sur HSM/token/service, horodatage RFC 3161, `signtool verify`, vérification Authenticode par le système de mise à jour, rôles Author/Reviewer/Approver tenus par un seul mainteneur) ; §7 réponse à compromission ; §8 relecture.
- ⚠️ Reste à faire : renseigner les SHA-256 des archives UnRAR macOS (arm64/x86_64) dans le workflow (UnRAR Windows épinglé le 20/10/2026) ; la policy §3 le mentionne ; ajouter un scan antivirus ou une signature relèverait d'une décision future (la policy §6 décrit la cible).

### assets/logo-nom-stellio.ico
- Fichier ICO multi-tailles (16, 24, 32, 48, 64, 128, 256 px), ~145 Ko.
- Utilisations : `stellio-setup.iss` (`SetupIconFile`) ; `.github/workflows/build-and-sign.yml` l.148 (`--icon` PyInstaller Windows), l.287–297 (conversion via Pillow + `iconutil` en `assets/logo-nom-stellio.icns` pour macOS, l.353 `--icon`), l.681 (AppImage : `Image.open(...).resize((256, 256))` → `stellio.png`).
- ⚠️ À vérifier : `Image.open()` sur un ICO multi-tailles ne charge par défaut que l'image la plus grande ; si ce n'est pas du 256×256, `resize((256, 256))` l'étire.
- Le logo `assets/logo-nom-stellio.png` (256×233, vrai PNG ; affiché dans `index.html` l.57, le rapport PDF `main.py` et le repli de `script.js`) n'est pas carré.

### assets/tigertag-logo.svg
- SVG « potrace » (pochoir vectoriel généré depuis un bitmap) : 92×92 pt, `viewBox 0 0 92 92`, groupe `translate(0,92) scale(0.1,-0.1)`, 11 `<path>` remplis en noir `#000000`, sans `<style>` ni `currentColor`.
- Utilisation : `index.html` l.2392, `<img src="assets/tigertag-logo.svg" class="tigertag-banner-logo" onerror="…masque l'image…">` dans la bannière TigerTag de l'inventaire ; `style.css` l.5354 (`height: 26px; width: auto; flex-shrink: 0; filter: invert(1)`), avec `filter: none` en thème clair (`[data-theme="light"]`).
- Le SVG étant noir uni, `filter: invert(1)` le rend blanc sur la bannière du thème sombre ; il reste noir en thème clair (corrigé).
- Le service worker met `/assets/*` en cache-first : après remplacement du logo ou de l'icône, incrémenter `stellio-v6` (version actuelle) dans `sw.js` pour forcer le rafraîchissement.

---

## 14. Dépôt GitHub : fichiers annexes

Le dépôt public (`stellio-app/stellio`, branche `main`, 84 fichiers, dernier commit connu « V 0.6.9 » — non revérifié pour la 0.7.2) contient en plus de ce qui précède :

### stellio_manager.bat (284 lignes, Windows)
- Relance sa propre console (`cmd /k`), passe en UTF-8, lit `CURRENT_VERSION` dans `main.py` via `findstr`, puis affiche un menu : [1] lancer en mode test, [2] mode test DEBUG (logs détaillés), [3] lancer le dossier `test/` (nouvelles fonctionnalités, dossier ignoré par git), [4] vérifier/installer les dépendances, [5] quitter.
- `:CHECK_VENV` crée `venv\` avec `python\python.exe` embarqué si présent ; `:INSTALL_AND_CHECK_DEPS` fait `pip install --upgrade pip`, `pip install --upgrade -r requirements.txt` puis `venv\Scripts\python.exe check_deps.py --fix`. Lancement : `venv\Scripts\python.exe main.py`.

### .gitignore
- Réécrit le 20/10/2026 d'après l'arborescence réelle du dossier de travail (testé avec `git` sur une copie de cette arborescence). Dossiers de la racine **ancrés** par un `/` initial (`/venv/`, `/env/`, `/.venv/`, `/python/`, `/Lib/`, `/Scripts/`, `/nodejs/`, `/build/`, `/dist/`, `/output/`, `/release/`, `/bin/`, `/redist/`, `/stellio-data*/`, `/test/`, `/logs/`, `/StellioCompanion/`) ; partout : `__pycache__/`, `*.py[cod]`, `*.egg-info/`, `.pytest_cache/`, `node_modules/`, `.wrangler/`, `.dev.vars`, `*.spec`, `*.log`, `*.db`, `*.sqlite(3)`, `app_settings.json`, `encryption.key`, `.env` / `.env.*` (sauf `.env.example`), `token*.txt`, `*.p12`, `*.pfx`, `*.pem`, `*.key`, installeurs `VC_redist*.exe` et `MicrosoftEdgeWebview2*.exe`, fichiers d'éditeurs et du système. `relay/` (relais Cloudflare Workers), `apk/`, `docs/`, `assets/`, `languages/` et `.github/` restent **versionnés**. ⚠️ Un `.gitignore` n'enlève pas les fichiers déjà suivis : `git ls-files -ci --exclude-standard` liste ceux à retirer avec `git rm -r --cached <chemin>`. Autres remarques : `FUNDING.yml` est à la racine alors que GitHub ne lit que `.github/FUNDING.yml` ; `PYINSTALLER.txt` (racine) est à supprimer si inutile (décision de l'auteur) ; le workflow se déclenche sur `bin/**` alors que ce dossier est ignoré.
- `bin/` est ignoré alors que le workflow déclenche sur ce chemin : ffmpeg et UnRAR ne viennent pas du dépôt, le workflow les télécharge à chaque build (étapes « Download ffmpeg (not committed to the repo, fetched fresh each build) » et « Download UnRAR »).

### assets/
- Logos : `logo-stellio.png` (234×256, favicon + apple-touch-icon `index.html` l.34–35, sidebar l.217, À propos l.2982), `nom-stellio.png` (256×48, logotype sidebar l.218), `logo-nom-stellio.png` (256×233, l.57, rapports PDF), `logo-nom-stellio.ico`, `tigertag-logo.svg` (le `tigertag-logo.png` inutilisé a été supprimé le 20/10/2026).
- Ces fichiers `.png` sont de vrais PNG. Le doublon inutilisé `logo-stellio - Copie.png` (ICO renommé en .png) a été supprimé le 20/10/2026.
- `vendor/` : `fontawesome/` (css + webfonts), `inter/` (`inter.css` + `files/`, 5 graisses latin), `mdi/` (Material Design Icons), `threejs/` (`three.min.js`, `controls/` avec `OrbitControls.js` et `TrackballControls.js`, `loaders/` avec `{STL,OBJ,3MF}Loader.js`), avec une `LICENSE.txt` chacun. Contenu de `controls/`, `loaders/` et `inter/files/` confirmé seulement par les noms de dossiers (captures du 20/10/2026) : vérifier les noms de fichiers au premier lancement.
- Corrigé le 20/10/2026 : `index.html` charge désormais Three.js r128 et ses loaders (l.46–51) depuis `assets/vendor/threejs/` et Inter (l.43) depuis `assets/vendor/inter/inter.css`, au lieu de cdnjs/jsdelivr et Google Fonts : la visionneuse 3D fonctionne hors ligne et l'application ne contacte plus de CDN. La CSP de `_set_security_headers` (main.py l.3571) autorise **toujours** ces CDN (laissée telle quelle sur décision du 20/10/2026) ; `sw.js` est passé à `stellio-v6` pour purger les anciens caches.

### Écarts constatés dans le dépôt (v0.7.2)
- Voir le §15 pour la liste complète (restauration des fonctions de la 0.6.9, changelog, licence, signature, Three.js).
- **README / PRIVACY** : le README fourni (381 lignes) ne mentionne pas Nexprint ; `worker.py` (l.284, désormais « squelette non utilisé ») et `Stellio-Setup-<version>.exe` (l.184) sont corrigés depuis le 19/10/2026. Les 8 politiques de confidentialité ont été mises à jour le 19/10/2026 (voir §13).
- **Licence** : `LICENSE` est maintenant l'AGPL v3 (18/10/2026), cohérent avec le README et avec la modale « À propos » (`about.legal`, voir §13).
- **Signature Windows** : volontairement absente pour l'instant ; `CODE_SIGNING_POLICY.md` et README alignés le 18/10/2026 (voir §10 et §13).
- **Import de bobines depuis un tableur** : `POST /api/filament/manual/import/preview` (fichier `.xls`/`.xlsx`/`.csv` → aperçu, colonnes reconnues par synonymes, couleurs converties en hex) puis `POST /api/filament/manual/import` (insertion dans `manual_filament_spools`), code `_spool_import_*` dans `main.py` (constantes l.22648, `_spool_import_read_table` l.22716, `_spool_import_parse` l.22777, routes `api_manual_spools_import_preview` l.22844 et `api_manual_spools_import` l.22866, juste avant `_consume_filament_slot` l.22909) ; bouton `#import-manual-spool-btn` (`index.html` l.2365) et modale `openSpoolImportModal` (`script.js` l.10497, puis `previewSpoolImport` l.10530 et `confirmSpoolImport` l.10566, après `saveSpoolInventoryEntry`) ; clés i18n `spoolimport.*` (8). Limites : 5 Mo, 2000 lignes ; lignes sans matière ni couleur ignorées ; une bobine créée par ligne (pas de fusion des doublons). Dépendances `xlrd` (.xls) et `openpyxl` (.xlsx) : présentes dans `requirements.txt` et dans la liste de repli de `main.py` ; **à vérifier dans `check_deps.REQUIRED_MODULES`** (`check_deps.py` n'a pas été fourni).
- **Qidi Studio** : ajouté comme slicer détecté (`_SLICER_CANDIDATES`, id `qidistudio`, exécutable `qidi-studio.exe`), famille « fork Bambu Studio » (`--load-settings`, préslice, `SLICER_VERSIONED_USER_DIRS` → `QIDIStudio\\user`), listes déroulantes d'`index.html` et libellé de `script.js`. Chemins d'installation et dossier utilisateur déduits de la convention des forks Bambu Studio : à vérifier sur une machine avec Qidi Studio installé.
- **Bulle de survol des cartes** : n'affiche plus dimensions/poids/temps mais « Envoyé au slicer » (une ligne dans `print_history`) et « Imprimé » (résultat `success`), d'après `print_status` (main.py ~l.7494) ; clés `card.tooltip_sent_slicer`, `card.tooltip_printed`, `card.yes`, `card.no`.
- **`plyer`** : présent dans `requirements.txt`, dans la liste de repli de `main.py`, dans `check_deps.REQUIRED_MODULES`, dans `launcher._PRELOAD_MODULES` et dans les `--collect-all` du workflow (corrigé).

---

## 15. Statut du portage 0.6.9 → 0.7.2 et écarts restants

**Restauré dans la 0.7.2** (code repris de la 0.6.9, testé côté serveur avec le client de test Flask : création/lecture des données, PDF du rapport, liaison pièce ↔ maintenance, avertissement de buse abrasive, rôle invité en lecture seule) : séchage des bobines, calibrations, pièces d'usure, rapports mensuels et bilan de bobine, mises à jour de modèles, notifications push, rôle invité, téléchargement Nexprint. Repères au §2 (tableau « Fonctions restaurées »), §3, §4 et §5. Non testé en conditions réelles : l'envoi vers ntfy/Telegram/Discord/webhook, la vérification des mises à jour de modèles auprès des plateformes, la connexion Nexprint (fenêtre pywebview) et l'interface dans un navigateur.

**Volontairement non repris de la 0.6.9** (hors périmètre demandé, ou remplacé par du code 0.7.x) : statut « envoyé/réussi » des cartes (`/api/print-history/file-status` ; seule une version simplifiée existe, la bulle de survol « Envoyé au slicer / Imprimé » basée sur `print_status`), fiabilité croisée par matière/bobine, « réimprimer comme la dernière fois », sous-dossiers de téléchargement (`/api/download/targets`), dédoublonnage des sources imbriquées. Les clés i18n correspondantes n'ont pas été réintégrées ; seules celles des fonctions restaurées l'ont été (préfixes `parts.`, `push.`, `report.`, `drying.`, `calib.`, `modelupdate.`, `guests.`, `spoolreport.`, `preprint.`, `viewer.`).

- **Correctif (file « à imprimer bientôt »)** : le bouton « Ajouter à imprimer bientôt » du menu Actions (`#ctx-queue-btn`, script.js l.2191) appelait `togglePrintQueue(_ctxPath)` alors que `_ctxPath` n'existe que dans la fonction anonyme de `openFileCtxMenu` (l.16469) : ReferenceError au clic, rien n'était ajouté et la file restait vide. Le gestionnaire lit désormais `window._ctxFilePath`, renseigné par `openFileCtxMenu` (l.16475). Même cause possible dans la 0.6.9 (code identique).
- **Correctif (notifications en double)** : les clés de dédoublonnage des alertes de stock bas, pièce à recommander, bobine à sécher et maintenance se terminaient par la date du jour (`..._${today}`) et le serveur ne dédoublonnait que sur 24 h : la même alerte réapparaissait chaque jour. Les clés n'ont plus de date (script.js l.3841, 10963, 10978, 15037) et `api_create_notification` ignore toute nouvelle notification dont le sujet existe déjà, lue ou non, quelle que soit sa date ; seul le message est mis à jour (ex. grammes restants). Au démarrage, `_dedupe_notifications_once` ne garde que la plus récente des anciennes notifications au même sujet. Les notifications d'événement (`print_finished_*`, `print_failed_*`, clé avec `Date.now()`) restent individuelles. Si l'utilisateur supprime une notification alors que la condition persiste, elle peut réapparaître au contrôle suivant.
- **Nexprint** : l'interface (carte de compte, libellés) est en français codé en dur, comme dans la 0.6.9 ; aucune clé i18n dédiée. Le lien Nexprint a été ajouté à `languages/useful_links.json` (groupe « Modèles 3D ») et existe aussi dans la liste de repli `_DEFAULT_USEFUL_LINKS` (main.py l.20372).
- **Changelog** : corrigé — la seconde entrée `0.7.1` (16 éléments) est devenue l'entrée `0.7.2` et ne garde que ses 8 éléments propres (les 8 autres, identiques, restent dans `0.7.1`). Un 9ᵉ élément, ajouté dans les 8 langues, annonce le retour des fonctions restaurées de la 0.6.9.
- **Three.js et Inter** : servis depuis `assets/vendor/` (corrigé le 20/10/2026) ; la CSP autorise encore les CDN.
- **Boutiques du stock bas** : corrigé le 19/10/2026 — `filament_shops.json` supprimé (et sa lecture dans `load_filament_shops`), `_DEFAULT_USEFUL_LINKS` = copie complète des 41 liens de `useful_links.json` (à garder synchronisée avec ce fichier ; commentaire ajouté au-dessus de la liste), « Bambu Lab Wiki » ajouté au JSON.
- **`/api/files/origin`** : route restaurée le 18/10/2026 (GET/POST). Table `file_origins` ; la lecture fusionne la fiche saisie avec `download_history` (lien source, date et plateforme du téléchargement → `from_download`) ; l'écriture valide l'URL (`http(s)://`, `url_invalid`) et les longueurs (URL 500, auteur 120, licence 120, notes 1000 → `url_too_long`, `author_too_long`, `license_too_long`, `notes_too_long`) et refuse les chemins hors sources (403) ; une fiche entièrement vide est supprimée (sauf lien de téléchargement). `_follow_file_origin` fait suivre la fiche (et recopie le lien de téléchargement) lors d'un renommage ou d'un déplacement ; la corbeille n'efface pas la fiche (annulation possible).
- **Doublons** dans `script.js` : corrigé — dans le fichier fourni le 19/10/2026, `window.addPrinter` (l.14067), `window.openAddPrinterModal` (l.15970) et `window.togglePrinterFields` (l.16058) ne sont définis qu'une fois (aucune modification n'a été nécessaire).
- **Dépendances** : `telethon` conservé volontairement (variante Telegram prévue) alors que le push Telegram passe par des requêtes HTTP (`_push_deliver`, main.py l.12468) ; `pyaes` seulement dans `requirements.txt` et les `--collect-all` ; `requirements.txt` sans versions (choix du 18/10/2026 de les laisser libres).
- **Licence** : `LICENSE` = AGPL v3 (18/10/2026), README = AGPL v3, À propos = « Distribué sous licence GNU AGPL v3 » (voir §13). **Signature Windows** : non signé par choix, policy et README alignés ; SHA-256 d'UnRAR Windows épinglé, celui des archives macOS reste à renseigner (voir §10 et §13). **README** : `worker.py` (squelette non utilisé) et le nom de l'installeur corrigés dans les 8 langues.
