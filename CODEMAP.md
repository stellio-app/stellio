# CODEMAP — Stellio v0.6.9

Carte de navigation du code. Dépôt : https://github.com/stellio-app/stellio (commit « V 0.6.9 »). Les numéros de ligne de `main.py`, `script.js` et `index.html` correspondent à l'état de ces fichiers dans ce commit ; ils dérivent dès qu'on édite. Pour retrouver un élément, préférer `grep -n "nom_de_fonction" main.py`. Ce fichier est à la racine du dépôt et référencé par `llms.txt`.

| Fichier | Lignes | Rôle |
|---|---|---|
| `main.py` | ~22 255 | Backend Flask monolithique (258 routes, ~620 fonctions, 9 classes) |
| `script.js` | ~18 266 | Frontend : toute la logique client (~516 fonctions de premier niveau) |
| `index.html` | ~3 973 | SPA : sidebar, 14 pages, 34 modales |
| `style.css` | ~8 076 | Thèmes, composants, vues galerie/détails |
| `check_deps.py` | 225 | Vérificateur/réparateur de dépendances Python (voir §9) |
| `sw.js` | 71 | Service worker PWA (cache `stellio-v5`) |
| `worker.py` | 27 | Squelette de worker 3MF — **non utilisé** par `main.py` (voir §9) |
| `conftest.py` | 61 | Configuration pytest : stubs de modules lourds, `STELLIO_DATA_DIR` temporaire |
| `requirements.txt` | 40 lignes | Dépendances pip |
| `stellio-setup.iss` | 242 | Script Inno Setup de l'installeur Windows |
| `entitlements.plist` | 14 | Droits de signature macOS (hardened runtime) |
| `README.md` | 381 | Présentation publique (EN), fonctionnalités, installation, raccourcis |
| `LICENSE` | 674 | Texte intégral de la **GNU GPL v3** — ⚠️ le README annonce l'AGPL v3 (voir §13) |
| `CODE_SIGNING_POLICY.md` | 157 | Politique de signature de code (EN), liée depuis le README (voir §13) |
| `assets/logo-nom-stellio.ico` | 145 Ko | Icône de l'app, 7 tailles de 16 à 256 px (voir §13) |
| `assets/tigertag-logo.svg` | 89 | Logo TigerTag monochrome, bannière filament (voir §13) |
| `stellio_manager.bat` | 284 | Menu de développement Windows (voir §14) |
| `.gitignore` | — | Exclusions du dépôt (voir §14) |
| `assets/*.png`, `assets/vendor/` | — | Logos et polices/icônes/Three.js locaux (voir §14) |
| `library.png`, `monitoring.png`, `slicer.png`, `nesting.png` | 1920 px | Captures d'écran du README |
| `launcher.py` | 158 | Point d'entrée des builds PyInstaller : charge `app/main.py` via `runpy` |
| `install-pi.sh` | 180 | Installeur Raspberry Pi/Linux (venv + service systemd), voir §10 |
| `.github/workflows/build-and-sign.yml` | 683 | Workflow GitHub Actions : build Windows/macOS/Linux + release (voir §10) |
| `apk/stellio.apk` | 4,8 Mo | App Android compagnon (`com.stellioapp.companion`), WebView — voir §11 |
| `docs/readme/README.{fr,de,es,it,pt,ja,zh}.md` | ~381 chacun | README traduits (même structure que `README.md`) |
| `docs/privacy/PRIVACY[.fr,.de,…].md` | 54 chacun | Politique de confidentialité en 8 langues (EN = `PRIVACY.md`) |
| `languages/{fr,en,de,es,it,ja,pt,zh}.json` | 1793 clés chacun | Traductions (clés plates `section.cle`) |
| `languages/changelog.json` | — | Notes de version par langue |
| `languages/useful_links.json` | 25 liens (sans Nexprint, voir §14) | Liens utiles par défaut |
| `languages/filament_shops.json` | 4 boutiques | Boutiques du bouton « Acheter » |

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

- Flask sert aussi le frontend : `Flask(__name__, static_folder=BASE_DIR, static_url_path='')` (l.3523) ; `GET /` → `index()` (l.5218).
- Auth : session cookie (30 jours), `@login_required` (l.3512), CSRF `_csrf_protect` (l.3543), rôle invité lecture seule `_viewer_guard` (l.3588), en-têtes sécurité `_set_security_headers` (l.3612), limite upload 50 Mo.
- Pairs Stellio ↔ Stellio : clé locale `require_peer_key` (l.7712), routes `/api/peer/*`.
- Dossiers de données (`get_data_path`, l.434) : `~/.stellio` | `%APPDATA%\Stellio` | `$STELLIO_DATA_DIR`. Contient `stellio.db`, `app_settings.json`, `file_cache.json`, `thumbnails/`, `uploads/`, `print_photos/`, `sosprint_conversation_photos/`, `imported_slicer_profiles/`, `trash/`, `flask_secret.key`.

---

## 2. main.py — sections (par ordre de lignes)

| Lignes | Contenu | Éléments clés |
|---|---|---|
| 1–245 | Bootstrap et dépendances | `check_deps` (optionnel), `_REQUIRED_MODULES`, `_auto_install_missing_modules` (l.76), `_run_startup_module_check` (l.152), imports |
| 246–430 | File de miniatures | `_queue_thumb_task`, session de génération (`_thumb_session_*`), `get_thumb_timeout`, `_prevent_system_sleep` |
| 431–545 | Chemins, corbeille | `get_base_path`, `get_data_path`, `BASE_DIR/DATA_DIR/DB_PATH`, `_move_file_to_trash`, `_purge_expired_trash` |
| 542–760 | Logs, outils externes, réglages | `setup_logging`, `_setup_rar_tool`, `_setup_ffmpeg_tool`, `load_settings/save_settings` (SETTINGS_FILE l.753) |
| 777–960 | Démarrage auto OS | `is_startup_enabled`, `set_startup_enabled` (registre Windows, LaunchAgent macOS, autostart Linux), `save_cache_on_exit` |
| 962–1105 | Chiffrement secrets | `encrypt_password`/`decrypt_password`, `decrypt_account_secret`, `migrate_account_passwords_to_random_iv`, `migrate_printer_api_keys` |
| 1105–1700 | Base de données | `get_db`, `init_db` (l.1111), `migrate_*` (print_history, maintenance, stellio_extras, print_photos, filament manuel, recovery code) |
| 1759–3025 | Connexions imprimantes | `BambuPersistentConnection` (l.1827, MQTT), `ElegooSDCPConnection` (l.2384), `CrealityConnection` (l.2583), `FlashForgePersistentConnection` (l.2713), `ElegooCC2Connection` (l.2850), flux caméra MJPEG/RTSP, découverte LAN (SSDP, broadcast) |
| 3026–3445 | `PrinterManager` (l.3026) | Dispatch par marque, statut normalisé, Klipper/Moonraker, Spoolman actif |
| 3445–3650 | Sécurité & app Flask | `parse_printer_config`, hash mots de passe (`hash_pw_strong`), code de récupération, `app = Flask(...)` (l.3523), gestionnaires d'erreur |
| 3648–3765 | Archives | `UnsafeArchiveError`, `safe_extract_zip/tar/rar/7z`, chemins virtuels d'archive (`make_virtual_archive_path`), `list_archive_3d_entries` |
| 3765–3985 | Cache fichiers | `load_file_cache`/`save_file_cache`/`invalidate_cache`, `_migrate_file_cache_schema`, `_backfill_multiplate_tags` |
| 3984–5115 | Génération de miniatures et analyse 3D | `process_generation_queue` (l.3984), 3MF multi-plaques (`load_3mf_mesh`, `get_3mf_plate_count`), rendu `generate_thumbnail_pyrender` → `_raster` → `_matplotlib` → `create_fallback_thumbnail`, `analyze_3d_file` |
| 5115–5520 | Auth & configuration | `/api/files/analyze`, `/api/auth/*` (inscription, login, invités, question secrète, récupération), `/api/app-config` |
| 5520–5800 | Sources | `/api/sources*`, `/api/files/upload-drop` |
| 5800–6130 | Comptes externes | `/api/accounts*` (Thingiverse, Nexprint, MakerWorld), `validate_thingiverse_account` |
| 6130–6830 | Miniatures & tags (API) | `/api/file/mesh`, `/api/thumb*`, `/api/tags*`, `reconcile_thumbnails_with_disk`, `pregenerate_thumbnails_on_startup` |
| 6826–7420 | Scan des sources | `scan_local_folder`, `scan_smb_folder_recursive`, `_do_background_scan` (l.7208), `_auto_tag_new_files`, `_auto_scan_scheduler`, `GET /api/files` (l.7417) |
| 7420–8140 | Partage et instances distantes | `/api/files/share`, `/share/<token>`, `/api/remote-instances*`, `/api/peer/*`, `_scan_lan_for_stellio` |
| 8140–8810 | Opérations fichiers | `/api/files/{open-with,exists,delete,delete-batch,restore-batch,rename,duplicates,duplicates/similar}` |
| 8804–9260 | Stats, historique, photos | `/api/stats`, `/api/print-history*` (note, coût), `/api/print-photos*` |
| 9255–9490 | Déplacer / décompresser | `/api/browse-folder`, `/api/files/{move,decompress}`, `/api/archive/*` |
| 9486–10650 | Slicers | détection (`detect_installed_slicers`, `_locate_slicer[_macos]`), `run_silent_slice`, parsing G-code (`parse_bambu_orca_gcode3mf`, `parse_cura_gcode`…), `/api/slicer/*`, `/api/picker/*`, `/api/test-connection` |
| 10650–12200 | Téléchargement de modèles | `/api/download*`, `printables_get_*`, `nexprint_*`, `makerworld_*`, `save_download_history` |
| 12194–12740 | Favoris, file d'attente, présence, notifications | `/api/favorites`, `/api/print-queue*`, `/api/presence/*`, `/api/notifications*`, push (`_push_deliver`, `_push_watcher_loop`) |
| 12735–13070 | Projets | `/api/projects*` |
| 13068–13660 | Réparation, conversion, intégrité | `/api/files/{repair,convert,convert-batch}`, `/api/integrity/*`, `_repair_mesh_inplace` |
| 13656–14290 | Sauvegarde, logs, devis, debug | `/api/backup/*`, `/api/logs/*`, `build_quote_pdf_bytes` (l.13998), `/api/quote/export*`, `/api/debug/*` |
| 14288–14540 | Réglages et onboarding | `/api/settings` (+ `/undo`), `/api/suggestions`, `/api/onboarding/*`, `CURRENT_VERSION = "0.6.9"` (l.14384), `/api/changelog/*` |
| 14550–15075 | Mise à jour | `check_for_updates`, `download_update`, `install_update`, `/api/update/*` |
| 15075–15930 | Imprimantes (API) | `/api/printers*` (CRUD, découverte, statut, caméra, alimentation), maintenance (`/api/printers/maintenance/*`) |
| 15928–16060 | Arrêt app | `/api/app/quit`, `_cleanup_before_exit`, `AIDisabledError` (l.16004), `_call_ollama`, `_call_ai` |
| 16059–17330 | IA (Ollama) & SOS Print | `/api/ollama/*`, `/api/ai/predict-print-time`, `/api/sos-print/*`, `/api/ollama/semantic-search` |
| 17327–18260 | Profils slicer | `/api/slicer-profiles*`, `_parse_slicer_profile_file`, `_scan_dir_for_profiles`, `_autodetect_new_slicer_profiles`, recommandation de profil |
| 18477–18580 | Nesting | `/api/nesting/arrange` (`_pack_polygons`, rectpack/shapely) |
| 18671–19520 | Filament | `/api/spoolman/spools`, restock, coût et éco (`_compute_estimated_cost`, `/api/eco/estimate`), TigerTag (Firebase), `/api/filament/spools` |
| 19519–20110 | Liens, séchage, calibrations, pièces | `/api/links`, `/api/filament/{buy-links,low-stock,drying*}`, `/api/calibrations*`, `/api/parts*` |
| 20182–20330 | Rapports | `/api/reports/*` (mensuel PDF), `/api/filament/spool-report` |
| 20648–20790 | Mises à jour de modèles | `/api/model-updates*` (Printables/MakerWorld/Thingiverse) |
| 20791–21320 | Pré-impression & inventaire filament | `/api/files/pre-print-check`, `/api/filament/compatibility`, `/api/files/*filament*`, `/api/filament/{tigertag,manual*}`, `/api/spoolman/discover*`, `/api/slicers/discover*` |
| 21319–21660 | PWA & réseau | `/manifest.json`, `/api/network-info`, `/api/ping`, `/api/qrcode` |
| 21656–21810 | Accès distant | `/api/remote-access*`, `start_remote_access` (cloudflared), adresse personnalisée |
| 21810–22255 | Point d'entrée | env `STELLIO_*`, splash tkinter, waitress (`serve`, l.21897) ou `app.run`, `webview.start` (l.22245), glisser-déposer natif |

### Classes
`BambuPersistentConnection` 1827 · `ElegooSDCPConnection` 2384 · `CrealityConnection` 2583 · `FlashForgePersistentConnection` 2713 · `ElegooCC2Connection` 2850 · `PrinterManager` 3026 · `UnsafeArchiveError` 3648 · `NexprintError` 11009 · `AIDisabledError` 16004

### Tables SQLite (`init_db`, l.1111)
`users` 1118 · `sources` 1128 · `slicer_jobs` 1138 · `tags` 1145 · `file_tags` 1150 · `account_credentials` 1156 · `favorites` 1169 · `print_queue` 1175 · `notifications` 1185 · `remote_instances` 1197 · `printers` 1209 · `download_history` 1220 · `print_history` 1232 · `file_descriptions` 1243 · `print_photos` 1251 · `projects` 1260 · `project_files` 1271 · `spool_assignments` 1282 · `filament_assignments` 1294 · `manual_filament_spools` 1308 · `sos_print_diagnostics` 1320 · `sos_print_conversations` 1334 · `sos_print_messages` 1352 · `printer_maintenance_tasks` 1466 · `spool_drying_log` 1500 · `filament_calibrations` 1517 · `download_subfolders` 1569 · `model_updates` 1599 · `printer_parts` 1619

---

## 3. main.py — routes API par domaine

Notation : `M` méthode, ligne de la déclaration `@app.route`.

**Auth** (5217–5510) — `GET /` · `GET /api/auth/first-launch` · `POST register|login|logout` · `GET me` · `GET|POST /guests`, `PUT|DELETE /guests/<id>` · `GET security-question` · `POST recovery-code/regenerate` · `POST reset-with-recovery`

**Config / sources** — `GET /api/app-config` · `GET|POST /api/sources`, `PUT|DELETE /api/sources/<id>`, `POST /api/sources/drop`, `POST /api/files/upload-drop` · `POST /api/browse-folder`, `/api/picker/folder|file`, `/api/test-connection`

**Fichiers / bibliothèque** — `GET /api/files` (7417) · `GET /api/files/changes` · `POST /api/files/invalidate-cache` · `GET /api/scan/delta` · `POST /api/files/{analyze, analyze-now, open-with, delete, delete-batch, restore-batch, rename, move, decompress, cleanup-archive, share, repair, convert, convert-batch}` · `GET /api/files/{exists, duplicates, duplicates/similar}` · `GET /api/file/{mesh, plate-count, data}` · `POST /api/archive/extract-entry` · `GET /share/<token>`

**Miniatures** — `GET /api/thumb` (6272) · `GET /api/thumb/{failures, progress, summary}` · `POST /api/thumb/{check, generate-now, regen-batch}`

**Tags / projets / favoris / file d'attente** — `/api/tags` (GET, POST, PUT/DELETE `<id>`, `POST /restore`) · `POST /api/files/tags`, `/api/files/tags/bulk-add` · `/api/projects` (CRUD + `/restore` + `/<id>/files` POST/PUT/DELETE) · `/api/favorites` (GET, POST) · `/api/print-queue` (GET, POST, DELETE, `POST /reorder`)

**Instances distantes & pairs** — `/api/remote-instances` (GET, POST, DELETE `<id>`, `POST <id>/ping|send`, `GET <id>/folders`, `GET /status`, `GET /discover`) · `/api/peer/{folders, identify, handshake, receive-file}`

**Historique / stats / photos** — `GET /api/stats` · `/api/print-history` (GET, `file-status`, DELETE `<id>`, `DELETE /clear`, `POST <id>/rate|cost`) · `/api/print-photos` (GET, POST, `GET <id>/image`, DELETE `<id>`) · `/api/download-history` (GET, `DELETE /clear`)

**Slicers & profils** — `POST /api/slicer/{send, send-batch, pre-slice-estimate}` (+GET estimate) · `GET /api/slicers/discover` + `POST /decline` · `/api/slicer-profiles` (GET, `import`, `refresh`, `auto-detect`, PATCH `<id>/printer|type`, DELETE `<id>`) · `POST /api/nesting/arrange`

**Téléchargement de modèles / comptes** — `GET /api/download/targets`, `POST /api/download/create-folder`, `POST /api/download`, `GET /api/download/progress/<id>`, `POST /api/download/cancel/<id>` · `/api/accounts` (GET, POST, `/<platform>` GET/DELETE, `/<platform>/key`, `/thingiverse/validate`, `/nexprint/browser-login[/status]`, `/makerworld/{login,verify,disconnect}`, `/tigertag/auto-detect-studio`, `/status`)

**Imprimantes** — `/api/printers` (GET, POST, `discover`, `<pid>` PUT/DELETE, `<pid>/{status, upload, brand, power, camera, camera/stream, hours/add}`, `<pid>/maintenance` GET/POST, `maintenance/{<task_id>, <task_id>/reset, due}`)

**Filament / Stellio extras** — `/api/spoolman/{spools, discover, discover/decline}` · `/api/filament/{spools, tigertag, manual[/<id>], buy-links, low-stock, compatibility, spool-report, drying[/<id>, /due]}` · `/api/files/{assign-filament, filament-assignment, unassign-filament, pre-print-check}` · `/api/calibrations[/<id>, /suggest]` · `/api/parts[/<id>, /<id>/adjust, /low]` · `/api/ai/restock-check` · `/api/eco/estimate`

**Rapports / devis / sauvegarde / logs** — `/api/reports/{monthly, export, export-native}` · `/api/quote/{export, export-native}` · `/api/backup/{export, export-native, import}` · `/api/logs/{export, export-native, tail}` · `/api/integrity/{check, progress}`

**Notifications / présence** — `/api/notifications` (GET, POST, `<id>` DELETE, `<id>/read`, `read-all`) · `POST /api/push/test` · `/api/presence/{heartbeat, active}`

**IA / SOS Print** — `/api/ollama/{models, recommend-model, auto-tag, explain-orientation, describe-file, semantic-search, recommend-profile, recommend-profile-batch, sos-print, sos-print/questions, sos-print/next-question}` · `POST /api/ai/predict-print-time` · `GET /api/file-description` · `/api/sos-print/conversations[/<id>, /<id>/photo, /<id>/resolve, /<id>/reopen, /photo/<filename>]`

**Système** — `/api/settings` (GET, POST, `POST /undo`) · `/api/suggestions` · `/api/onboarding/{status, dismiss}` · `/api/changelog/{latest, seen}` · `/api/update/{check, version, download, install}` · `/api/model-updates[/check, /<id>/dismiss]` · `/api/links` · `/api/debug/{session, enable}` · `/api/app/{quit, save-cache}` · `/manifest.json` · `/api/network-info` · `/api/ping` · `/api/qrcode` · `/api/remote-access[/toggle, /custom, /disable-custom, /configure, /disable-fixed]` · `/api/model-updates`

---

## 4. index.html

- `<head>` (l.1–60) : script d'init thème, `style.css?v=…`, Inter (Google Fonts), Font Awesome et MDI locaux (`assets/vendor/`), Three.js r128 + OrbitControls, TrackballControls, STL/OBJ/3MF loaders (CDN). `<script src="script.js">` à la fin (l.3972).
- Sidebar : boutons `data-page` (l.221–317) : dashboard, library, stats, projects, print-queue, gallery, history, repair, converter, sosprint, printers, spoolman, settings.
- Pages (`id="page-*"`) : dashboard 502 · library 693 · stats 702 · projects 813 · print-queue 833 · gallery 853 · history 875 · filters 932 · settings 964 · repair 1977 · converter 2014 · sosprint 2078 · printers 2235 · spoolman 2244 (Inventaire filament : Spoolman / manuel / TigerTag).
- Modales (`id="modal-*"`) : select-type 2418 · backup-options 2440 · local-manual 2491 · smb 2517 · nfs 2562 · slicer-import-assign 2599 · slicer 2618 · nesting 2664 · confirm 2723 · 3d-viewer 2741 · partners 2804 · about 2816 · shortcuts 2845 · rename-source 2882 · filters 2906 · tag-manager 3027 · bulk-tag 3077 · download 3107 · add-remote-instance 3250 · add-printer 3285 · file-actions 3437 · file-metadata 3509 · print-photos 3519 · photo-source 3551 · share-file 3574 · move-file 3611 · delete-file 3640 · rename-file 3658 · duplicates 3680 · qrcode-remote 3715 · qrcode-apk 3768 · whats-new 3814 · bulk-rename 3845 · repair-diff 3916

---

## 5. script.js — zones fonctionnelles

| Lignes | Zone | Fonctions principales |
|---|---|---|
| 1–200 | `I18N` | objet `I18N` (init, `_loadLang`, `t`, `apply`), langues supportées zh/en/es/fr/de/it/ja/pt, dossier `/languages` |
| 203–360 | Init & PWA | `installStellioApp`, `_getCsrfCookie`, `DOMContentLoaded` (l.335) |
| 356–600 | Config, sauvegarde | `loadAppConfig`, `applyAllowedSourceTypes`, `exportBackup`, `importBackup`, `showConfirmDialog` |
| 596–760 | Intégrité | `startIntegrityCheck`, `pollIntegrityProgress`, `renderIntegrityResults` |
| 761–990 | Clavier & survol | `setupKeyboardShortcuts` (l.794), navigation fléchée, `setupHoverDelegation` |
| 991–1360 | Langues, miniatures, favoris | `populateLanguageSelectors`, `generateVisibleThumbnails`, `refreshFileThumbnail`, `loadFavorites`, `checkFavoritesRestock` |
| 1363–1520 | File d'attente « à imprimer bientôt » | `loadPrintQueue`, `renderPrintQueue`, `setupPrintQueueDragDrop` |
| 1603–1830 | Archives, auth, nouveautés | `decompressFile`, `checkAuth` (l.1732), `showPanel` (panneaux d'auth, l.1751), `showApp` (l.1758), `checkWhatsNew` |
| 1836–2400 | Tableau de bord | `loadDashboard` (l.1841), config/ordre des widgets (`applyDashboardConfig`, `_setupDashboardDragAndDrop`), `_loadDashboard*` (sos, favoris, projets, stats, maintenance, file, téléchargements, instances, mise à jour, suggestions, imprimantes, historique, stock, fichiers récents) |
| 2400–2660 | Notifications & présence | `loadNotifications`, `createNotification`, `startPresence`, `maybeFireBrowserNotifications` |
| 2660–2810 | Visite guidée | `getTourSteps`, `_showTourStepAt`, `endTour` |
| 2809–3020 | Palette de commandes Ctrl+K | `_staticCommands`, `_navCommands`, `_fileCommands`, `_tagCommands`, `_executeCommand` |
| 3162–3330 | Toasts | `showToast`, `showUndoToast`, `showGenericUndoToast` |
| 3336–3480 | Découverte & démarrage | `checkSpoolmanAutoDiscovery`, `checkSlicerDefaultDiscovery`, `checkAccountsStatusOnStartup`, `startAutoFileMonitor` |
| 3510–3720 | Utilitaires UI, sources | `escapeHtml`, `formatSize`, `openModal`/`closeModal`, `pickPhoto` (appareil photo/galerie), `addSource` |
| 3720–4050 | Instances distantes | `loadRemoteInstances`, `discoverRemoteInstances`, `sendFileToRemoteInstance`, `_openRemoteFolderPicker` |
| 4044–5050 | Bibliothèque | `loadSources`, `loadFiles` (l.4118), `pollScanProgress`, `renderFileCard` (4385), `renderFiles` (4675), `buildFolderBlock`, `renderChunk`, génération/suivi de miniatures |
| 5048–5430 | Tags & renommage en masse | `loadTags`, `openTagManagerModal`, `applyTagsToFile`, `openBulkRenameModal`, `_computeBulkRenameName`, `applyTagsToSelection` |
| 5429–5620 | Téléchargement de modèles | `openDownloadModal`, `handleDownload`, `startDownload`, toasts de progression, `cancelDownload` |
| 5766–5995 | Filtres | `applyFilters` (l.5766), `openFiltersModal`, filtres sauvegardés (`_loadSavedFilters`, `renderSavedFiltersList`) |
| 5994–6130 | Slicer (envoi) | `openFileWith`, `sendToSlicer` (6020), `_loadSlicerQuickEstimate`, `_runPrePrintCheck`, `_loadSlicerSpoolBox` |
| 6126–6735 | Visionneuse 3D | `open3DViewer`, `load3DModel` (6579), orientation (`computeOverhangVertexColors`, `computeOrientationSuggestions`, `suggestBestOrientation`), multi-plaques (`goToPlate`) |
| 6735–7210 | Profils slicer | `loadSlicerProfiles`, `renderSlicerProfiles`, `importSlicerProfiles`, `autoDetectSlicerProfiles` |
| 7213–7410 | Recommandation de profil & nesting | `requestProfileRecommendation`, `openNestingModal`, `runNesting`, `renderNestingPreview` |
| 7413–8210 | Paramètres | thème/accent (`applyTheme`, `applyFabricant`), `initSettings` (7444), Spoolman, Ollama/IA, scan auto, démarrage auto, coûts d'impression, réglages du devis (8110+) |
| 8209–8470 | Ollama | `testOllamaConnection`, `recommendOllamaModel`, `ollamaAutoTag` |
| 8472–9010 | SOS Print | `runSosprintDiagnosis`, `renderSosprintQuestionStep`, `loadSosprintHistory`, `resumeSosprintConversation` |
| 9208–9645 | Inventaire filament | `loadSpoolmanPage` (9219), `loadManualSpoolInventory`, `renderManualSpoolGrid`, `openSpoolInventoryModal`, `saveSpoolInventoryEntry` |
| 9642–10125 | Extras (séchage, calibrations, pièces) | `applyRoleUI`, `_loadSpoolDrying`, `_loadSpoolCalib`, `openPartsModal`, `loadParts`, `checkPartsLowAlerts`, `checkDryingDueAlerts` |
| 10122–10245 | Invités, vérif pré-impression, fiabilité | `loadGuests`, `_prePrintWarningHtml`, `_renderStatsReliability` |
| 10245–10360 | Push | `loadPushSettings`, `savePushSettings`, `testPush`, `_applyReprintContext` |
| 10362–10535 | Rapport mensuel | `openMonthlyReport`, `loadMonthlyReport`, `exportMonthlyReport`, `_loadSpoolReport` |
| 10537–10625 | Mises à jour de modèles | `loadModelUpdates`, `autoCheckModelUpdates` |
| 10625–10862 | Fiche bobine & grille Spoolman | `showSpoolDetailPopup` (10697), `_detailFromSpoolman/Manual/TigerTag`, `renderSpoolmanGrid` |
| 10862–11260 | Comptes externes & TigerTag | `saveAccountKey`, `nexprintBrowserLogin`, `makerWorldStep1/2`, `loadTigerTagSpools`, `renderTigerTagGrid` |
| 11256–11410 | Navigation latérale | `setupNavDragAndDrop`, `applyNavOrderToSidebar`, `setupEventListeners` (11349) |
| 11406–11540 | Auth UI | `loadSecurityQuestionFor`, `showRecoveryCodeModal` |
| 11539–11700 | En-tête, recherche, mobile | `updateHeaderVisibilityForPage`, `resetGlobalSearch`, `toggleMobileSidebar` |
| 11714–11950 | Glisser-déposer / upload | `_uploadDroppedFiles`, `handleFilePicker` |
| 11946–12210 | Recherche | `isSemanticQuery`, `runSemanticSearch`, `handleSearchInput`, recherches récentes |
| 12211–12430 | Nav mobile, envoi slicer, sélection | `toggleNavItem`, flèches de défilement de la barre mobile (12239), `_confirmSendToSlicer`, `updateFolderSelectionBar` |
| 12485–12780 | Réparation & convertisseur | `loadRepairFiles`, `showRepairDiff` (12568), `loadConverterFiles`, `renderConverterFiles` |
| 13162–13200 | Compatibilité imprimante | `checkPrinterCompatibility` |
| 13465–13800 | Historique | notation, coût, raison d'échec, `_populateHistoryPlatformFilter`, `_checkHistoryFileExists`, `loadDownloadHistory` |
| 13942–14250 | Imprimantes | `loadPrinters`, `renderPrinters`, caméras de cartes, `refreshAllPrinters` |
| 14244–14680 | Maintenance | `openMaintenanceModal`, tâches, `checkMaintenanceDueGlobal`, popups d'alerte |
| 14675–14800 | Stock bas | `checkLowStockOnStartup`, `showLowStockToast`, `showLowStockShopPopup` |
| 14796–15060 | Moniteur imprimante | `openPrinterMonitor`, `fetchAndUpdateMonitor`, `updateMonitorUI`, `loadPrinterCamera` |
| 15428–15570 | Diagnostic | `loadAppVersion`, `enableDebugSessionAndRestart`, `pollDiagnosticConsole`, `exportDiagnosticLogs` |
| 17014–17030 | Coût | `_applyCostSpoolSelection`, `_applyCostPrinterSelection` |
| 17365–17560 | Projets | `loadProjects`, `renderProjectCard`, `refreshProjectDetail` |
| 17834–17940 | PWA / QR | `_detectMobileBrowserContext`, `_renderPwaBrowserHint`, `_loadQrCode` |

> Les lignes 15060–15428, 15570–17014 et 17030–17365 ne contiennent pas de fonctions de premier niveau nommées : le code y est organisé en blocs d'écouteurs d'événements (`DOMContentLoaded` aux l.12228, 13232, 15370, 15655) et en fonctions imbriquées (stats, coût d'impression/devis, historique, etc.). Utiliser `grep` sur les ids du DOM (`getElementById('…')`) pour les retrouver.

---

## 6. style.css — repères

- 1–60 : historique de téléchargement
- 62–131 : variables (`:root`, `[data-theme="light"]`, `[data-fabricant="bambu|prusa|voron|creality"]`)
- 134–227 : reset, `.btn*`
- 229–450 : écran d'authentification, champs `.input-group`
- 452–600 : layout `.app-screen`, `.sidebar`, `.nav-btn`
- 604–920 : en-tête, recherche (`.search-box`, historique), sélecteurs de vue, progression de miniatures
- 921–970 : `.main-content`, zone de dépôt, pages
- 972–2000 : grilles de fichiers (gallery/details), `.file-card`, badges, boutons d'action, infobulles de métadonnées
- 2000–8076 : composants suivants (modales, tableau de bord, imprimantes, filament, etc.) — non cartographiés ligne par ligne ; chercher par nom de classe.

---

## 7. i18n

- Fichiers `languages/<code>.json` : dictionnaire plat, clés `section.cle` (ex. `spoolman.sort_name`), plus `__dir`, `__name`, `__native`. 1793 clés dans chacune des 8 langues (fr, en, de, es, it, ja, pt, zh).
- HTML : attributs `data-i18n*` ; JS : `I18N.t('clé')` ; backend : lit `languages/<lang>.json` directement pour les notifications push et le splash (l.12484, 22049) ; le frontend les récupère via `/languages/<lang>.json` (servi par le dossier statique Flask).
- `changelog.json` : `[{version, items:{<lang>:[…]}}]` ; version courante `0.6.9` (entrée Nexprint), lue via `load_changelog` (l.14388).

## 8. Recettes rapides

- **Ajouter une route API** : décorateur `@app.route` + `@login_required` dans la section du domaine (section 3), en tenant compte de `_viewer_guard` pour les écritures.
- **Ajouter une table** : `init_db` (l.1111) + éventuelle fonction `migrate_*` pour les bases existantes ; penser à l'export/import de sauvegarde (l.13592–13770).
- **Ajouter une page** : `<div class="page" id="page-xxx">` dans `index.html`, bouton `data-page="xxx"` dans la sidebar, gestion du clic `.nav-btn[data-page]` dans `setupEventListeners` (l.11349, à vérifier : `showPanel` ne sert qu'aux panneaux d'authentification), entrée dans `_navCommands` (palette).
- **Nouvelle chaîne UI** : ajouter la clé aux 8 fichiers `languages/*.json`.
- **Nouvelle marque d'imprimante** : classe `*Connection` + `_build_*_result` + `_ensure_*/_stop_*_connection` + découverte, puis dispatch dans `PrinterManager` (l.3026).
- **Nouvelle dépendance Python** : `requirements.txt`, `check_deps.REQUIRED_MODULES` et la liste de repli de `main.py` (l.20–60).
- **Nouvelle version** : `CURRENT_VERSION` (l.14384) + entrée en tête de `changelog.json` ; le workflow ne publie une release que si cette version change.
- **Nouveau site de téléchargement de modèles** : voir l'exemple Nexprint — `NexprintError` (l.11009) et `nexprint_get_model_files` (l.11059) dans `main.py`, connexion via fenêtre `POST /api/accounts/nexprint/browser-login` (l.6051) + `/status` (l.6113), carte de compte `index.html` l.1793, `nexprintBrowserLogin` (`script.js` l.10930), statut au démarrage (`script.js` l.3460), lien dans `_DEFAULT_USEFUL_LINKS` (l.19491) **et** dans `languages/useful_links.json`, étiquette dans l'historique de téléchargements.

---

## 9. Fichiers annexes (build, tests, PWA, installeur)

### check_deps.py
- `REQUIRED_MODULES` (l.28) : 28 tuples `(nom d'import, paquet pip, attribut attendu, paquets conflictuels)` ; `TELEGRAM_MODULES` (l.60, `telethon`) optionnel.
- Fonctions : `find_owning_packages` (65), `deep_check_module` (74, vérifie l'import réel **et** un attribut pour détecter un mauvais paquet installé sous le même nom), `auto_install_missing_modules` (84, désinstalle le mauvais paquet puis `pip install --force-reinstall/--upgrade`, retente avec `--break-system-packages`), `check_required_modules` (157), `_cli_main` (185).
- CLI : `python check_deps.py [--fix] [--telegram]` ; code de sortie 1 si une dépendance manque.
- `main.py` l'importe en tête (l.11–19, bloc `try`) et possède une copie de repli de `_REQUIRED_MODULES` si l'import échoue (l.20–60) : **toute nouvelle dépendance doit être ajoutée aux deux endroits** (plus `requirements.txt`).

### requirements.txt
- Contient en plus de `check_deps` : `pyinstaller`, `PyOpenGL-accelerate`, `telethon`.
- Linux : `pywebview[gtk]` + paquets système `libgtk-3-0 libwebkit2gtk-4.1-0` (non installables par pip). macOS : pyobjc installé automatiquement.
- ⚠️ `plyer` (utilisé par `_send_native_notification`, main.py l.12460, et listé dans `check_deps.REQUIRED_MODULES`) **n'apparaît pas** dans `requirements.txt` — à vérifier.

### sw.js (service worker, enregistré dans script.js l.192–194)
- Caches `stellio-v5-shell` et `stellio-v5-assets` ; les anciens caches `stellio-*` sont supprimés à l'activation ; changer `CACHE_VERSION` pour forcer un renouvellement.
- Stratégie : `/api/*` et `/share/*` jamais interceptés ; `/assets/*` cache-first ; le reste réseau d'abord avec repli sur le cache puis `/index.html`. Seulement les requêtes GET de même origine.
- Pré-cache : `/`, `/index.html`, `/script.js`, `/style.css`. Servi à `/sw.js` par le dossier statique Flask.

### worker.py
- Contient uniquement `process_3mf_task(file_path, plate_index=0)` qui renvoie des valeurs **codées en dur** (15000 sommets, 30000 faces) : c'est un squelette. Aucune référence dans `main.py` (le seul « worker » est `thumb_worker` dans `process_generation_queue`, l.3990). Le README le décrit pourtant comme « background worker (thumbnails, scans) ».

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
- Licence annoncée AGPL v3 (⚠️ le `LICENSE` fourni est la GPL v3, voir §13) ; Python 3.8+, Flask 3.0+ ; plateformes annoncées : Windows et Raspberry Pi/Linux (64 bits) ; modèles supportés : STL, 3MF, OBJ.
- Imprimantes : OctoPrint, PrusaLink, Klipper/Moonraker (HTTP), Bambu Lab (MQTT, AMS), Creality (WebSocket, CFS), FlashForge, Elegoo (SDCP).
- Raccourcis : `Ctrl+K` palette, `Ctrl+F` recherche, `Ctrl+N` téléchargement, `Ctrl+,` réglages, `Ctrl+Z` annuler suppression, `Alt+1-8` navigation, `F` favoris, `T` gestionnaire de tags, `?` aide, `Esc`.
- Fichiers cités dans le README et **absents du dépôt** : `bin/` (binaires ffmpeg/unrar par OS, optionnel — ignoré par `.gitignore`), fichiers de tests. Tout le reste (`assets/`, captures `library/monitoring/slicer/nesting.png`, `LICENSE`, `CODE_SIGNING_POLICY.md`) est dans le dépôt (voir §13–14).

---

## 10. Lancement, CI/CD et installation

### launcher.py (point d'entrée des builds figés)
- C'est le script que PyInstaller compile (`launcher.py` → `Stellio.exe` / `Stellio.app` / binaire Linux) ; **`main.py` n'est pas compilé** : il est copié à côté dans un dossier `app/` pour pouvoir être remplacé par les patchs `.zip` d'auto-mise à jour.
- `_app_dir()` (l.10) : localise `app/` — à côté de l'exécutable (Windows/Linux `--onedir`), `Stellio.app/Contents/Resources/app` (macOS), ou à côté du script en mode source.
- `_setup_early_env()` (l.33) ajoute `app/` à `sys.path` ; `_setup_bootstrap_logger` (l.43) écrit `launcher.log` (rotation 2 Mo ×2) dans `<app_dir>/../logs/` ; `_show_fatal_error` (l.56) : MessageBox Windows, sinon Tk, sinon stderr.
- `_preload_dependencies` (l.98) : import parallèle de `_PRELOAD_MODULES` pour diagnostic, **désactivé par défaut** (activer avec `STELLIO_DIAG_PRELOAD=1`) ; `STELLIO_TELEGRAM_VARIANT=1` ajoute `telethon`.
- `main()` (l.116) : positionne `STELLIO_LAUNCHER_EXE` (chemin de l'exécutable, lu par `install_update` main.py l.14699 et par la gestion du démarrage auto l.778/789), fait `chdir(app_dir)` puis `runpy.run_path(main.py, run_name="stellio_main")` — d'où la condition `__name__ in ('__main__', 'stellio_main')` de `main.py` (l.21810).
- Piège : la liste `_PRELOAD_MODULES` est une 3ᵉ liste de dépendances (en plus de `check_deps` et `requirements.txt`) ; elle ne contient pas `plyer`.

### .github/workflows/build-and-sign.yml (GitHub Actions, « Build, sign and release Stellio »)
- Déclencheurs : push sur `main` touchant `main.py`, `index.html`, `script.js`, `style.css`, `launcher.py`, `check_deps.py`, `requirements.txt`, `stellio-setup.iss`, `assets/**`, `languages/**`, `bin/**` ; ou lancement manuel avec `dry_run` (build sans release).
- Jobs : `check-version` (lit `CURRENT_VERSION` dans `main.py`, publie seulement si le tag `v<version>` n'existe pas encore → **il faut incrémenter `CURRENT_VERSION` pour déclencher une release**) → `build` (Windows : PyInstaller `--onedir --windowed`, copie des fichiers patchables dans `dist\Stellio\app`, télécharge ffmpeg + UnRAR, crée `Stellio-v<version>-patch.zip` + `.sha256`, compile l'installeur Inno Setup) ‖ `build-macos` (matrice `arm64` sur `macos-latest`, `x86_64` sur `macos-15-intel` ; `.app` signée Developer ID si les secrets `MACOS_CERTIFICATE`, `MACOS_CERTIFICATE_PWD`, `MACOS_SIGNING_IDENTITY` existent, sinon signature ad-hoc ; `.dmg` + sha256) ‖ `build-linux` (AppImage x86_64 avec GTK/WebKit, ffmpeg, unrar) → `release` (brouillon GitHub `v<version>` avec `.exe`, `.dmg`, `.AppImage`, `.zip`, `.sha256`).
- Chaque job exécute `check_deps.py --fix` puis `check_deps.py` ; Python 3.11 partout.
- Les fichiers « patchables » copiés dans `app/` : `main.py`, `check_deps.py`, `index.html`, `script.js`, `style.css`, `assets/`, `languages/`, `bin/` (+ `launcher.py` n'y est **pas**). `worker.py` n'est copié nulle part → confirme qu'il est inutilisé.
- ⚠️ Le patch `.zip` commun est créé dans le job **Windows** : il contient donc aussi `app\bin\` (ffmpeg.exe, DLL, UnRAR.exe). Le README annonce un patch « code source pur » identique pour Raspberry Pi/Linux — à vérifier côté logique d'installation du patch (`install_update`, main.py l.14694).
- ⚠️ L'artefact Windows s'appelle `stellio-installer-unsigned` : aucune étape de signature Authenticode n'apparaît dans ce workflow malgré son nom et la `CODE_SIGNING_POLICY` du README (signature probablement faite hors CI ou à la main sur le brouillon de release).
- `entitlements.plist` est aussi réécrit par le workflow (même contenu que le fichier du dépôt).

### install-pi.sh (Raspberry Pi / Linux headless)
- Script bash de 180 lignes (`bash -n` passe ; le conflit de fusion git de la version précédente est résolu). L'en-tête donne le conseil « swap » pour les Raspberry Pi à faible RAM (`CONF_SWAPSIZE=2048` dans `/etc/dphys-swapfile`).
- Contenu : refuse root, vérifie `sudo` et la RAM (<1,5 Go → avertissement), `apt-get install` (git, python3-venv, build-essential, ffmpeg, unrar-free, libs JPEG/PNG, OpenBLAS/ATLAS, OSMesa/EGL), `git clone`/`reset --hard origin/main` dans `~/stellio` (variable `STELLIO_DIR`), venv `~/stellio/venv`, `pip install -r requirements.txt` (échec toléré, `check_deps.py` répare au démarrage), crée `~/.stellio`, écrit `/etc/systemd/system/stellio.service` (`STELLIO_HEADLESS=1`, `STELLIO_DATA_DIR`, `STELLIO_PORT`, `Restart=always`, `ExecStart=venv/bin/python3 main.py`), l'active et attend jusqu'à 30 s, puis affiche `http://<ip>:5000`.
- Relancer le script met à jour le code (`git reset --hard` + `git clean -fd` : toute modification locale dans `~/stellio` est perdue ; les données restent dans `~/.stellio`).
- Note : l'installeur utilise `unrar-free` alors que le build Linux AppImage embarque le vrai `unrar`.

---

## 11. App Android compagnon (apk/stellio.apk)

- Paquet `com.stellioapp.companion`, version `1.0.0` (code 1), minSdk 24, targetSdk 34, libellé « Stellio ». Écrit en Kotlin (coroutines, AndroidX, Material), 912 entrées, `classes.dex` ≈ 9 Mo. **Seul l'APK est fourni, pas le projet Android Studio.**
- Activités : `MainActivity` (lanceur) et `com.journeyapps.barcodescanner.CaptureActivity` (ZXing, scan de QR code). Providers : `androidx.core.content.FileProvider` (partage de la photo prise) et `InitializationProvider`.
- Permissions : `INTERNET`, `ACCESS_NETWORK_STATE`, `ACCESS_WIFI_STATE`, `CAMERA`, `WRITE_EXTERNAL_STORAGE`.
- Classes de l'app (par noms dans le dex) : `MainActivity` (WebView : `setupWebView`, `connectToStellio`, `findReachableUrl`, `registerNetworkMonitor`, `scheduleOfflineCheck`, `startReconnectLoop`, `setupLanguageSpinner`) et `ConnectionPrefs` (adresse du serveur mémorisée). Principe : l'app mémorise l'URL du serveur Stellio (saisie ou scannée par QR code, cf. `/api/qrcode`), teste son accessibilité, charge l'interface web dans une WebView et se reconnecte automatiquement en cas de coupure.
- Distribution : `STELLIO_COMPANION_APK_URL` (main.py l.3521) pointe vers `https://www.github.com/stellio-app/stellio/raw/main/apk/stellio.apk` ; `GET /api/qrcode?source=apk` (l.21586) génère le QR code de téléchargement ; côté web, la prise de photo passe par `pickPhoto` (script.js l.3634) et la modale `modal-photo-source`.
- Pour modifier le comportement natif (appareil photo, flèches de la barre mobile…), il faut le projet Android (`MainActivity.kt`, `AndroidManifest.xml`) — non inclus ici ; la barre de navigation mobile défilable côté web est dans `script.js` (l.12239) et `style.css`.

---

## 12. Documentation traduite

- `docs/readme/README.<lang>.md` (fr, de, es, it, pt, ja, zh) : traductions complètes du `README.md` (mêmes sections, même structure de projet) ; liens relatifs : `../../README.md`, `../../LICENSE`, `../privacy/PRIVACY.md`, `../../library.png`… Toute nouvelle fonctionnalité documentée dans `README.md` doit être reportée dans les 7 traductions (et dans `languages/changelog.json`).
- `docs/privacy/` : `PRIVACY.md` (EN) + `PRIVACY.{fr,de,es,it,pt,ja,zh}.md`, « dernière mise à jour » 1ᵉʳ septembre 2026. Contenu : principe « local-first », données stockées localement (bibliothèque, miniatures, configs, clés API chiffrées AES-CFB, historique, logs), services tiers optionnels (mises à jour GitHub, Printables/MakerWorld/Thingiverse, imprimantes, Cloudflare Tunnel, Ollama distant, Spoolman), sécurité, droits, contact `contact@stellio-app.com`.
- ⚠️ Écarts de cohérence relevés : la politique de confidentialité ne mentionne pas TigerTag (Firebase), les notifications push (ntfy/Telegram/Discord/webhook), les instances Stellio distantes ni la détection de nouvelles versions des modèles — services qui contactent des tiers d'après le code et le README ; le README annonce `Stellio-Setup.exe` alors que le fichier produit s'appelle `Stellio-Setup-<version>.exe` ; il décrit `worker.py` comme un worker de miniatures alors qu'il est inutilisé.

---

## 13. Licence, signature de code et assets

### LICENSE
- Texte standard de la **GNU General Public License v3** (29 juin 2007, 674 lignes), sans ligne de copyright propre au projet ni mention « or any later version ».
- ⚠️ **Incohérence de licence** : `README.md` (badge « License: AGPL v3 » + section « 📜 License ») et ses traductions disent **AGPL v3** et renvoient vers ce fichier ; le fichier est la **GPL v3** (la clause 13 ne fait qu'autoriser le mélange avec de l'AGPL). Troisième version : la modale « À propos » (`index.html` l.2838–2840, clé `about.legal`) affiche « © 2026 Stellio Project. Tous droits réservés ». Il faut choisir une licence, remplacer `LICENSE` par le texte AGPL v3 si c'est elle, et aligner README, traductions et `about.legal` (8 fichiers `languages/*.json`).

### CODE_SIGNING_POLICY.md
- Liée depuis la section « 🔏 Code Signing Policy » du README (« Windows executables published in Releases are digitally signed »).
- Contenu (9 sections) : §1 périmètre (exe Windows, installeur, binaires de `bin/`, CI) ; §2 pourquoi signer (serveur local + pont JS/Python, identifiants tiers chiffrés AES avec `encryption.key`, TLS désactivé pour certains brokers MQTT, démarrage auto via la clé `Run`) ; §3 certificat d'une AC publique, EV recommandé, OV transitoire ; §4 clé jamais exportable (token matériel, HSM cloud ou service type Azure Trusted Signing / DigiCert KeyLocker / SignPath) ; §5 processus (build depuis un tag, scan antivirus, signature en CI avec approbation, horodatage RFC 3161, SHA-256 des binaires tiers vérifié, `signtool verify /pa /v`) ; §6 intégrité de la chaîne de mise à jour ; §7 compromission ; §8 rôles Author/Reviewer/Approver (un mainteneur unique peut cumuler, documenté) ; §9 relecture.
- ⚠️ Écarts avec le code fourni :
  - `build-and-sign.yml` ne contient **aucune** étape de signature Windows (artefact `stellio-installer-unsigned`, pas de `signtool`, ni SignPath) ni scan antivirus ni vérification SHA-256 des binaires de `bin/` : les §3–5 décrivent un processus qui n'apparaît pas dans la CI (il peut se faire hors CI, non vérifiable ici).
  - §6 dit « si un mécanisme de mise à jour automatique est ajouté à l'avenir » alors qu'il existe déjà (`install_update` l.14694, `download_update`). `download_update(download_url, progress_callback, expected_sha256=None)` sait vérifier un SHA-256 (supprime le fichier et annule en cas d'écart) mais seulement si `expected_sha256` est fourni ; je n'ai repéré **aucune** vérification Authenticode du fichier téléchargé, et le patch `.zip` n'est pas un exécutable signé.
  - §5.1 renvoie à `check_deps`/`REQUIRED_MODULES` comme « dépendances verrouillées » : ce sont des listes de noms de modules, pas des versions figées (`requirements.txt` ne fige aucune version : noms de paquets seuls, donc build non reproductible).
  - La politique couvre « Windows » ; macOS est signé/notarisé dans la CI (Developer ID si secrets, sinon ad-hoc) sans être mentionné — §9 prévoit pourtant de la mettre à jour quand une plateforme est ajoutée.

### assets/logo-nom-stellio.ico
- Fichier ICO multi-tailles (16, 24, 32, 48, 64, 128, 256 px), ~145 Ko.
- Utilisations : `stellio-setup.iss` (`SetupIconFile`) ; `.github/workflows/build-and-sign.yml` l.142 (`--icon` PyInstaller Windows), l.261–270 (conversion via Pillow + `iconutil` en `assets/logo-nom-stellio.icns` pour macOS, l.322 `--icon`), l.602 (AppImage : `Image.open(...).resize((256, 256))` → `stellio.png`).
- ⚠️ À vérifier : `Image.open()` sur un ICO multi-tailles ne charge par défaut que l'image la plus grande ; si ce n'est pas du 256×256, `resize((256, 256))` l'étire.
- Le logo `assets/logo-nom-stellio.png` (256×233, vrai PNG ; affiché dans `index.html` l.57, le rapport PDF `main.py` et le repli de `script.js`) n'est pas carré.

### assets/tigertag-logo.svg
- SVG « potrace » (pochoir vectoriel généré depuis un bitmap) : 92×92 pt, `viewBox 0 0 92 92`, groupe `translate(0,92) scale(0.1,-0.1)`, 11 `<path>` remplis en noir `#000000`, sans `<style>` ni `currentColor`.
- Utilisation : `index.html` l.2297, `<img src="assets/tigertag-logo.svg" class="tigertag-banner-logo" onerror="…masque l'image…">` dans la bannière TigerTag de l'inventaire ; `style.css` l.5347 (`height: 26px; width: auto; flex-shrink: 0`). Aucun filtre CSS n'est appliqué.
- ⚠️ Étant noir uni et sans filtre, il sera très peu visible sur le thème sombre si le fond de la bannière est sombre (à vérifier visuellement) ; si c'est le cas, ajouter `filter: invert(1)` en thème sombre ou passer le SVG en `fill="currentColor"` (nécessite de l'inliner ou d'utiliser un masque CSS).
- Le service worker met `/assets/*` en cache-first : après remplacement du logo ou de l'icône, incrémenter `stellio-v5` dans `sw.js` pour forcer le rafraîchissement.

---

## 14. Dépôt GitHub : fichiers annexes

Le dépôt public (`stellio-app/stellio`, branche `main`, 84 fichiers, dernier commit « V 0.6.9 ») contient en plus de ce qui précède :

### stellio_manager.bat (284 lignes, Windows)
- Relance sa propre console (`cmd /k`), passe en UTF-8, lit `CURRENT_VERSION` dans `main.py` via `findstr`, puis affiche un menu : [1] lancer en mode test, [2] mode test DEBUG (logs détaillés), [3] lancer le dossier `test/` (nouvelles fonctionnalités, dossier ignoré par git), [4] vérifier/installer les dépendances, [5] quitter.
- `:CHECK_VENV` crée `venv\` avec `python\python.exe` embarqué si présent ; `:INSTALL_AND_CHECK_DEPS` fait `pip install --upgrade pip`, `pip install --upgrade -r requirements.txt` puis `venv\Scripts\python.exe check_deps.py --fix`. Lancement : `venv\Scripts\python.exe main.py`.

### .gitignore
- Ignore `python/`, `Lib/`, `Scripts/`, `redist/`, `venv/`, `env/`, **`bin/`**, `build/`, `dist/`, `output/`, `release/`, `test/`, `stellio-data*/`, `*.log`, `*.sqlite`, `*.db`, `StellioCompanion/` (projet Android local), installeurs WebView2/VC++, `token*.txt`, `.env`, `*.p12|*.pfx|*.pem`.
- `bin/` est ignoré alors que le workflow déclenche sur ce chemin : ffmpeg et UnRAR ne viennent pas du dépôt, le workflow les télécharge à chaque build (étapes « Download ffmpeg (not committed to the repo, fetched fresh each build) » et « Download UnRAR »).

### assets/
- Logos : `logo-stellio.png` (234×256, favicon + apple-touch-icon `index.html` l.34–35, sidebar l.217, À propos l.2824), `nom-stellio.png` (256×48, logotype sidebar l.218), `logo-nom-stellio.png` (256×233, l.57, rapports PDF), `logo-nom-stellio.ico`, `tigertag-logo.svg`, `tigertag-logo.png` (PNG 270×68, non référencé).
- Ces fichiers `.png` sont désormais de vrais PNG. ⚠️ `logo-stellio - Copie.png` reste un fichier **ICO avec l'extension .png** et un doublon inutilisé : à supprimer.
- `vendor/` : `fontawesome/` (css + webfonts), `inter/` (5 graisses latin), `mdi/` (Material Design Icons), `threejs/` (`three.min.js`, `controls/OrbitControls.js`, `controls/TrackballControls.js`, `loaders/{STL,OBJ,3MF}Loader.js`) avec une `LICENSE.txt` chacun.
- `index.html` l.46–51 charge désormais Three.js et ses loaders depuis `assets/vendor/threejs/` (plus de CDN) : la visionneuse 3D fonctionne hors ligne, une fois les assets en cache (`sw.js` les met en cache-first au premier chargement, sans pré-cache).

### Écarts constatés dans le dépôt (v0.6.9)
- **Nexprint / liens utiles** : le changelog 0.6.9 dit que Nexprint rejoint les liens « Modèles 3D ». C'est vrai pour `_DEFAULT_USEFUL_LINKS` (`main.py` l.19491), mais `languages/useful_links.json` (25 liens, groupe « Modèles 3D » : Printables, MakerWorld, Thingiverse, Cults) ne contient pas Nexprint ; si ce fichier est lu en priorité, le lien n'apparaît pas.
- **README / PRIVACY** : ni `README.md` (et ses traductions) ni `docs/privacy/PRIVACY.md` ne mentionnent Nexprint ; `PRIVACY.md` ne cite pas non plus le site tiers contacté pour le téléchargement ni la connexion via fenêtre du site officiel.
- **Licence** : `LICENSE` est toujours la GPL v3 alors que le README annonce l'AGPL v3, et `about.legal` affiche « Tous droits réservés » (voir §13).
- **Signature Windows** : toujours aucune étape de signature Authenticode dans le workflow (voir §13).
- **`plyer`** : toujours absent de `requirements.txt` alors que `main.py` l'utilise (l.12460) et que `check_deps.REQUIRED_MODULES` le liste.
