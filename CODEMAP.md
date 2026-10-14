# CODEMAP — Stellio v0.6.9

Code navigation map. Repository: https://github.com/stellio-app/stellio (commit "V 0.6.9"). The line numbers for `main.py`, `script.js` and `index.html` match the state of those files in that commit; they drift as soon as the files are edited. To find an item, prefer `grep -n "function_name" main.py`. This file sits at the repository root and is referenced by `llms.txt`.

| File | Lines | Role |
|---|---|---|
| `main.py` | ~22,255 | Monolithic Flask backend (258 routes, ~620 functions, 9 classes) |
| `script.js` | ~18,266 | Frontend: all client-side logic (~516 top-level functions) |
| `index.html` | ~3,973 | SPA: sidebar, 14 pages, 34 modals |
| `style.css` | ~8,076 | Themes, components, gallery/details views |
| `check_deps.py` | 225 | Python dependency checker/repairer (see §9) |
| `sw.js` | 71 | PWA service worker (cache `stellio-v5`) |
| `worker.py` | 27 | 3MF worker skeleton — **not used** by `main.py` (see §9) |
| `conftest.py` | 61 | pytest configuration: stubs for heavy modules, temporary `STELLIO_DATA_DIR` |
| `requirements.txt` | 40 lines | pip dependencies |
| `stellio-setup.iss` | 242 | Inno Setup script for the Windows installer |
| `entitlements.plist` | 14 | macOS code-signing entitlements (hardened runtime) |
| `README.md` | 381 | Public presentation (EN), features, installation, shortcuts |
| `LICENSE` | 674 | Full text of the **GNU GPL v3** — ⚠️ the README announces AGPL v3 (see §13) |
| `CODE_SIGNING_POLICY.md` | 157 | Code signing policy (EN), linked from the README (see §13) |
| `assets/logo-nom-stellio.ico` | 145 KB | App icon, 7 sizes from 16 to 256 px (see §13) |
| `assets/tigertag-logo.svg` | 89 | Monochrome TigerTag logo, filament banner (see §13) |
| `stellio_manager.bat` | 284 | Windows development menu (see §14) |
| `.gitignore` | — | Repository exclusions (see §14) |
| `assets/*.png`, `assets/vendor/` | — | Logos and local fonts/icons/Three.js (see §14) |
| `library.png`, `monitoring.png`, `slicer.png`, `nesting.png` | 1920 px | README screenshots |
| `launcher.py` | 158 | Entry point of the PyInstaller builds: loads `app/main.py` via `runpy` |
| `install-pi.sh` | 180 | Raspberry Pi/Linux installer (venv + systemd service), see §10 |
| `.github/workflows/build-and-sign.yml` | 683 | GitHub Actions workflow: Windows/macOS/Linux build + release (see §10) |
| `apk/stellio.apk` | 4.8 MB | Android companion app (`com.stellioapp.companion`), WebView — see §11 |
| `docs/readme/README.{fr,de,es,it,pt,ja,zh}.md` | ~381 each | Translated READMEs (same structure as `README.md`) |
| `docs/privacy/PRIVACY[.fr,.de,…].md` | 54 each | Privacy policy in 8 languages (EN = `PRIVACY.md`) |
| `languages/{fr,en,de,es,it,ja,pt,zh}.json` | 1,793 keys each | Translations (flat `section.key` keys) |
| `languages/changelog.json` | — | Release notes per language |
| `languages/useful_links.json` | 25 links (without Nexprint, see §14) | Default useful links |
| `languages/filament_shops.json` | 4 shops | Shops used by the "Buy" button |

---

## 1. Overall architecture

```
pywebview (window) ──► http://127.0.0.1:5000 ◄── browser / mobile / APK
                              │
                    waitress (threads=16) ── Flask (main.py)
                              │
        ┌─────────────┬───────┴────────┬──────────────────┐
     SQLite       file_cache.json   thumbnails/       printers (MQTT/WS/HTTP)
   (stellio.db)   (file index)      (pyrender…)       Spoolman / TigerTag / Ollama
```

- Flask also serves the frontend: `Flask(__name__, static_folder=BASE_DIR, static_url_path='')` (l.3523); `GET /` → `index()` (l.5218).
- Auth: session cookie (30 days), `@login_required` (l.3512), CSRF `_csrf_protect` (l.3543), read-only guest role `_viewer_guard` (l.3588), security headers `_set_security_headers` (l.3612), 50 MB upload limit.
- Stellio ↔ Stellio peers: local key `require_peer_key` (l.7712), `/api/peer/*` routes.
- Data folders (`get_data_path`, l.434): `~/.stellio` | `%APPDATA%\Stellio` | `$STELLIO_DATA_DIR`. Contains `stellio.db`, `app_settings.json`, `file_cache.json`, `thumbnails/`, `uploads/`, `print_photos/`, `sosprint_conversation_photos/`, `imported_slicer_profiles/`, `trash/`, `flask_secret.key`.

---

## 2. main.py — sections (in line order)

| Lines | Content | Key elements |
|---|---|---|
| 1–245 | Bootstrap and dependencies | `check_deps` (optional), `_REQUIRED_MODULES`, `_auto_install_missing_modules` (l.76), `_run_startup_module_check` (l.152), imports |
| 246–430 | Thumbnail queue | `_queue_thumb_task`, generation session (`_thumb_session_*`), `get_thumb_timeout`, `_prevent_system_sleep` |
| 431–545 | Paths, trash | `get_base_path`, `get_data_path`, `BASE_DIR/DATA_DIR/DB_PATH`, `_move_file_to_trash`, `_purge_expired_trash` |
| 542–760 | Logs, external tools, settings | `setup_logging`, `_setup_rar_tool`, `_setup_ffmpeg_tool`, `load_settings/save_settings` (SETTINGS_FILE l.753) |
| 777–960 | OS auto-start | `is_startup_enabled`, `set_startup_enabled` (Windows registry, macOS LaunchAgent, Linux autostart), `save_cache_on_exit` |
| 962–1105 | Secret encryption | `encrypt_password`/`decrypt_password`, `decrypt_account_secret`, `migrate_account_passwords_to_random_iv`, `migrate_printer_api_keys` |
| 1105–1700 | Database | `get_db`, `init_db` (l.1111), `migrate_*` (print_history, maintenance, stellio_extras, print_photos, manual filament, recovery code) |
| 1759–3025 | Printer connections | `BambuPersistentConnection` (l.1827, MQTT), `ElegooSDCPConnection` (l.2384), `CrealityConnection` (l.2583), `FlashForgePersistentConnection` (l.2713), `ElegooCC2Connection` (l.2850), MJPEG/RTSP camera streams, LAN discovery (SSDP, broadcast) |
| 3026–3445 | `PrinterManager` (l.3026) | Per-brand dispatch, normalized status, Klipper/Moonraker, active Spoolman |
| 3445–3650 | Security & Flask app | `parse_printer_config`, password hashing (`hash_pw_strong`), recovery code, `app = Flask(...)` (l.3523), error handlers |
| 3648–3765 | Archives | `UnsafeArchiveError`, `safe_extract_zip/tar/rar/7z`, virtual archive paths (`make_virtual_archive_path`), `list_archive_3d_entries` |
| 3765–3985 | File cache | `load_file_cache`/`save_file_cache`/`invalidate_cache`, `_migrate_file_cache_schema`, `_backfill_multiplate_tags` |
| 3984–5115 | Thumbnail generation and 3D analysis | `process_generation_queue` (l.3984), multi-plate 3MF (`load_3mf_mesh`, `get_3mf_plate_count`), rendering `generate_thumbnail_pyrender` → `_raster` → `_matplotlib` → `create_fallback_thumbnail`, `analyze_3d_file` |
| 5115–5520 | Auth & configuration | `/api/files/analyze`, `/api/auth/*` (registration, login, guests, secret question, recovery), `/api/app-config` |
| 5520–5800 | Sources | `/api/sources*`, `/api/files/upload-drop` |
| 5800–6130 | External accounts | `/api/accounts*` (Thingiverse, Nexprint, MakerWorld), `validate_thingiverse_account` |
| 6130–6830 | Thumbnails & tags (API) | `/api/file/mesh`, `/api/thumb*`, `/api/tags*`, `reconcile_thumbnails_with_disk`, `pregenerate_thumbnails_on_startup` |
| 6826–7420 | Source scanning | `scan_local_folder`, `scan_smb_folder_recursive`, `_do_background_scan` (l.7208), `_auto_tag_new_files`, `_auto_scan_scheduler`, `GET /api/files` (l.7417) |
| 7420–8140 | Sharing and remote instances | `/api/files/share`, `/share/<token>`, `/api/remote-instances*`, `/api/peer/*`, `_scan_lan_for_stellio` |
| 8140–8810 | File operations | `/api/files/{open-with,exists,delete,delete-batch,restore-batch,rename,duplicates,duplicates/similar}` |
| 8804–9260 | Stats, history, photos | `/api/stats`, `/api/print-history*` (rating, cost), `/api/print-photos*` |
| 9255–9490 | Move / decompress | `/api/browse-folder`, `/api/files/{move,decompress}`, `/api/archive/*` |
| 9486–10650 | Slicers | detection (`detect_installed_slicers`, `_locate_slicer[_macos]`), `run_silent_slice`, G-code parsing (`parse_bambu_orca_gcode3mf`, `parse_cura_gcode`…), `/api/slicer/*`, `/api/picker/*`, `/api/test-connection` |
| 10650–12200 | Model downloads | `/api/download*`, `printables_get_*`, `nexprint_*`, `makerworld_*`, `save_download_history` |
| 12194–12740 | Favorites, queue, presence, notifications | `/api/favorites`, `/api/print-queue*`, `/api/presence/*`, `/api/notifications*`, push (`_push_deliver`, `_push_watcher_loop`) |
| 12735–13070 | Projects | `/api/projects*` |
| 13068–13660 | Repair, conversion, integrity | `/api/files/{repair,convert,convert-batch}`, `/api/integrity/*`, `_repair_mesh_inplace` |
| 13656–14290 | Backup, logs, quotes, debug | `/api/backup/*`, `/api/logs/*`, `build_quote_pdf_bytes` (l.13998), `/api/quote/export*`, `/api/debug/*` |
| 14288–14540 | Settings and onboarding | `/api/settings` (+ `/undo`), `/api/suggestions`, `/api/onboarding/*`, `CURRENT_VERSION = "0.6.9"` (l.14384), `/api/changelog/*` |
| 14550–15075 | Updates | `check_for_updates`, `download_update`, `install_update`, `/api/update/*` |
| 15075–15930 | Printers (API) | `/api/printers*` (CRUD, discovery, status, camera, power), maintenance (`/api/printers/maintenance/*`) |
| 15928–16060 | App shutdown | `/api/app/quit`, `_cleanup_before_exit`, `AIDisabledError` (l.16004), `_call_ollama`, `_call_ai` |
| 16059–17330 | AI (Ollama) & SOS Print | `/api/ollama/*`, `/api/ai/predict-print-time`, `/api/sos-print/*`, `/api/ollama/semantic-search` |
| 17327–18260 | Slicer profiles | `/api/slicer-profiles*`, `_parse_slicer_profile_file`, `_scan_dir_for_profiles`, `_autodetect_new_slicer_profiles`, profile recommendation |
| 18477–18580 | Nesting | `/api/nesting/arrange` (`_pack_polygons`, rectpack/shapely) |
| 18671–19520 | Filament | `/api/spoolman/spools`, restock, cost and eco (`_compute_estimated_cost`, `/api/eco/estimate`), TigerTag (Firebase), `/api/filament/spools` |
| 19519–20110 | Links, drying, calibrations, parts | `/api/links`, `/api/filament/{buy-links,low-stock,drying*}`, `/api/calibrations*`, `/api/parts*` |
| 20182–20330 | Reports | `/api/reports/*` (monthly PDF), `/api/filament/spool-report` |
| 20648–20790 | Model updates | `/api/model-updates*` (Printables/MakerWorld/Thingiverse) |
| 20791–21320 | Pre-print & filament inventory | `/api/files/pre-print-check`, `/api/filament/compatibility`, `/api/files/*filament*`, `/api/filament/{tigertag,manual*}`, `/api/spoolman/discover*`, `/api/slicers/discover*` |
| 21319–21660 | PWA & network | `/manifest.json`, `/api/network-info`, `/api/ping`, `/api/qrcode` |
| 21656–21810 | Remote access | `/api/remote-access*`, `start_remote_access` (cloudflared), custom address |
| 21810–22255 | Entry point | `STELLIO_*` env vars, tkinter splash, waitress (`serve`, l.21897) or `app.run`, `webview.start` (l.22245), native drag and drop |

### Classes
`BambuPersistentConnection` 1827 · `ElegooSDCPConnection` 2384 · `CrealityConnection` 2583 · `FlashForgePersistentConnection` 2713 · `ElegooCC2Connection` 2850 · `PrinterManager` 3026 · `UnsafeArchiveError` 3648 · `NexprintError` 11009 · `AIDisabledError` 16004

### SQLite tables (`init_db`, l.1111)
`users` 1118 · `sources` 1128 · `slicer_jobs` 1138 · `tags` 1145 · `file_tags` 1150 · `account_credentials` 1156 · `favorites` 1169 · `print_queue` 1175 · `notifications` 1185 · `remote_instances` 1197 · `printers` 1209 · `download_history` 1220 · `print_history` 1232 · `file_descriptions` 1243 · `print_photos` 1251 · `projects` 1260 · `project_files` 1271 · `spool_assignments` 1282 · `filament_assignments` 1294 · `manual_filament_spools` 1308 · `sos_print_diagnostics` 1320 · `sos_print_conversations` 1334 · `sos_print_messages` 1352 · `printer_maintenance_tasks` 1466 · `spool_drying_log` 1500 · `filament_calibrations` 1517 · `download_subfolders` 1569 · `model_updates` 1599 · `printer_parts` 1619

---

## 3. main.py — API routes by domain

Notation: `M` method, line of the `@app.route` declaration.

**Auth** (5217–5510) — `GET /` · `GET /api/auth/first-launch` · `POST register|login|logout` · `GET me` · `GET|POST /guests`, `PUT|DELETE /guests/<id>` · `GET security-question` · `POST recovery-code/regenerate` · `POST reset-with-recovery`

**Config / sources** — `GET /api/app-config` · `GET|POST /api/sources`, `PUT|DELETE /api/sources/<id>`, `POST /api/sources/drop`, `POST /api/files/upload-drop` · `POST /api/browse-folder`, `/api/picker/folder|file`, `/api/test-connection`

**Files / library** — `GET /api/files` (7417) · `GET /api/files/changes` · `POST /api/files/invalidate-cache` · `GET /api/scan/delta` · `POST /api/files/{analyze, analyze-now, open-with, delete, delete-batch, restore-batch, rename, move, decompress, cleanup-archive, share, repair, convert, convert-batch}` · `GET /api/files/{exists, duplicates, duplicates/similar}` · `GET /api/file/{mesh, plate-count, data}` · `POST /api/archive/extract-entry` · `GET /share/<token>`

**Thumbnails** — `GET /api/thumb` (6272) · `GET /api/thumb/{failures, progress, summary}` · `POST /api/thumb/{check, generate-now, regen-batch}`

**Tags / projects / favorites / queue** — `/api/tags` (GET, POST, PUT/DELETE `<id>`, `POST /restore`) · `POST /api/files/tags`, `/api/files/tags/bulk-add` · `/api/projects` (CRUD + `/restore` + `/<id>/files` POST/PUT/DELETE) · `/api/favorites` (GET, POST) · `/api/print-queue` (GET, POST, DELETE, `POST /reorder`)

**Remote instances & peers** — `/api/remote-instances` (GET, POST, DELETE `<id>`, `POST <id>/ping|send`, `GET <id>/folders`, `GET /status`, `GET /discover`) · `/api/peer/{folders, identify, handshake, receive-file}`

**History / stats / photos** — `GET /api/stats` · `/api/print-history` (GET, `file-status`, DELETE `<id>`, `DELETE /clear`, `POST <id>/rate|cost`) · `/api/print-photos` (GET, POST, `GET <id>/image`, DELETE `<id>`) · `/api/download-history` (GET, `DELETE /clear`)

**Slicers & profiles** — `POST /api/slicer/{send, send-batch, pre-slice-estimate}` (+GET estimate) · `GET /api/slicers/discover` + `POST /decline` · `/api/slicer-profiles` (GET, `import`, `refresh`, `auto-detect`, PATCH `<id>/printer|type`, DELETE `<id>`) · `POST /api/nesting/arrange`

**Model downloads / accounts** — `GET /api/download/targets`, `POST /api/download/create-folder`, `POST /api/download`, `GET /api/download/progress/<id>`, `POST /api/download/cancel/<id>` · `/api/accounts` (GET, POST, `/<platform>` GET/DELETE, `/<platform>/key`, `/thingiverse/validate`, `/nexprint/browser-login[/status]`, `/makerworld/{login,verify,disconnect}`, `/tigertag/auto-detect-studio`, `/status`)

**Printers** — `/api/printers` (GET, POST, `discover`, `<pid>` PUT/DELETE, `<pid>/{status, upload, brand, power, camera, camera/stream, hours/add}`, `<pid>/maintenance` GET/POST, `maintenance/{<task_id>, <task_id>/reset, due}`)

**Filament / Stellio extras** — `/api/spoolman/{spools, discover, discover/decline}` · `/api/filament/{spools, tigertag, manual[/<id>], buy-links, low-stock, compatibility, spool-report, drying[/<id>, /due]}` · `/api/files/{assign-filament, filament-assignment, unassign-filament, pre-print-check}` · `/api/calibrations[/<id>, /suggest]` · `/api/parts[/<id>, /<id>/adjust, /low]` · `/api/ai/restock-check` · `/api/eco/estimate`

**Reports / quotes / backup / logs** — `/api/reports/{monthly, export, export-native}` · `/api/quote/{export, export-native}` · `/api/backup/{export, export-native, import}` · `/api/logs/{export, export-native, tail}` · `/api/integrity/{check, progress}`

**Notifications / presence** — `/api/notifications` (GET, POST, `<id>` DELETE, `<id>/read`, `read-all`) · `POST /api/push/test` · `/api/presence/{heartbeat, active}`

**AI / SOS Print** — `/api/ollama/{models, recommend-model, auto-tag, explain-orientation, describe-file, semantic-search, recommend-profile, recommend-profile-batch, sos-print, sos-print/questions, sos-print/next-question}` · `POST /api/ai/predict-print-time` · `GET /api/file-description` · `/api/sos-print/conversations[/<id>, /<id>/photo, /<id>/resolve, /<id>/reopen, /photo/<filename>]`

**System** — `/api/settings` (GET, POST, `POST /undo`) · `/api/suggestions` · `/api/onboarding/{status, dismiss}` · `/api/changelog/{latest, seen}` · `/api/update/{check, version, download, install}` · `/api/model-updates[/check, /<id>/dismiss]` · `/api/links` · `/api/debug/{session, enable}` · `/api/app/{quit, save-cache}` · `/manifest.json` · `/api/network-info` · `/api/ping` · `/api/qrcode` · `/api/remote-access[/toggle, /custom, /disable-custom, /configure, /disable-fixed]` · `/api/model-updates`

---

## 4. index.html

- `<head>` (l.1–60): theme init script, `style.css?v=…`, Inter (Google Fonts), local Font Awesome and MDI (`assets/vendor/`), Three.js r128 + OrbitControls, TrackballControls, STL/OBJ/3MF loaders (CDN). `<script src="script.js">` at the end (l.3972).
- Sidebar: `data-page` buttons (l.221–317): dashboard, library, stats, projects, print-queue, gallery, history, repair, converter, sosprint, printers, spoolman, settings.
- Pages (`id="page-*"`): dashboard 502 · library 693 · stats 702 · projects 813 · print-queue 833 · gallery 853 · history 875 · filters 932 · settings 964 · repair 1977 · converter 2014 · sosprint 2078 · printers 2235 · spoolman 2244 (Filament inventory: Spoolman / manual / TigerTag).
- Modals (`id="modal-*"`): select-type 2418 · backup-options 2440 · local-manual 2491 · smb 2517 · nfs 2562 · slicer-import-assign 2599 · slicer 2618 · nesting 2664 · confirm 2723 · 3d-viewer 2741 · partners 2804 · about 2816 · shortcuts 2845 · rename-source 2882 · filters 2906 · tag-manager 3027 · bulk-tag 3077 · download 3107 · add-remote-instance 3250 · add-printer 3285 · file-actions 3437 · file-metadata 3509 · print-photos 3519 · photo-source 3551 · share-file 3574 · move-file 3611 · delete-file 3640 · rename-file 3658 · duplicates 3680 · qrcode-remote 3715 · qrcode-apk 3768 · whats-new 3814 · bulk-rename 3845 · repair-diff 3916

---

## 5. script.js — functional areas

| Lines | Area | Main functions |
|---|---|---|
| 1–200 | `I18N` | `I18N` object (init, `_loadLang`, `t`, `apply`), supported languages zh/en/es/fr/de/it/ja/pt, `/languages` folder |
| 203–360 | Init & PWA | `installStellioApp`, `_getCsrfCookie`, `DOMContentLoaded` (l.335) |
| 356–600 | Config, backup | `loadAppConfig`, `applyAllowedSourceTypes`, `exportBackup`, `importBackup`, `showConfirmDialog` |
| 596–760 | Integrity | `startIntegrityCheck`, `pollIntegrityProgress`, `renderIntegrityResults` |
| 761–990 | Keyboard & hover | `setupKeyboardShortcuts` (l.794), arrow-key navigation, `setupHoverDelegation` |
| 991–1360 | Languages, thumbnails, favorites | `populateLanguageSelectors`, `generateVisibleThumbnails`, `refreshFileThumbnail`, `loadFavorites`, `checkFavoritesRestock` |
| 1363–1520 | "Print soon" queue | `loadPrintQueue`, `renderPrintQueue`, `setupPrintQueueDragDrop` |
| 1603–1830 | Archives, auth, what's new | `decompressFile`, `checkAuth` (l.1732), `showPanel` (auth panels, l.1751), `showApp` (l.1758), `checkWhatsNew` |
| 1836–2400 | Dashboard | `loadDashboard` (l.1841), widget config/order (`applyDashboardConfig`, `_setupDashboardDragAndDrop`), `_loadDashboard*` (sos, favorites, projects, stats, maintenance, queue, downloads, instances, update, suggestions, printers, history, stock, recent files) |
| 2400–2660 | Notifications & presence | `loadNotifications`, `createNotification`, `startPresence`, `maybeFireBrowserNotifications` |
| 2660–2810 | Guided tour | `getTourSteps`, `_showTourStepAt`, `endTour` |
| 2809–3020 | Ctrl+K command palette | `_staticCommands`, `_navCommands`, `_fileCommands`, `_tagCommands`, `_executeCommand` |
| 3162–3330 | Toasts | `showToast`, `showUndoToast`, `showGenericUndoToast` |
| 3336–3480 | Discovery & startup | `checkSpoolmanAutoDiscovery`, `checkSlicerDefaultDiscovery`, `checkAccountsStatusOnStartup`, `startAutoFileMonitor` |
| 3510–3720 | UI utilities, sources | `escapeHtml`, `formatSize`, `openModal`/`closeModal`, `pickPhoto` (camera/gallery), `addSource` |
| 3720–4050 | Remote instances | `loadRemoteInstances`, `discoverRemoteInstances`, `sendFileToRemoteInstance`, `_openRemoteFolderPicker` |
| 4044–5050 | Library | `loadSources`, `loadFiles` (l.4118), `pollScanProgress`, `renderFileCard` (4385), `renderFiles` (4675), `buildFolderBlock`, `renderChunk`, thumbnail generation/tracking |
| 5048–5430 | Tags & bulk rename | `loadTags`, `openTagManagerModal`, `applyTagsToFile`, `openBulkRenameModal`, `_computeBulkRenameName`, `applyTagsToSelection` |
| 5429–5620 | Model downloads | `openDownloadModal`, `handleDownload`, `startDownload`, progress toasts, `cancelDownload` |
| 5766–5995 | Filters | `applyFilters` (l.5766), `openFiltersModal`, saved filters (`_loadSavedFilters`, `renderSavedFiltersList`) |
| 5994–6130 | Slicer (send) | `openFileWith`, `sendToSlicer` (6020), `_loadSlicerQuickEstimate`, `_runPrePrintCheck`, `_loadSlicerSpoolBox` |
| 6126–6735 | 3D viewer | `open3DViewer`, `load3DModel` (6579), orientation (`computeOverhangVertexColors`, `computeOrientationSuggestions`, `suggestBestOrientation`), multi-plate (`goToPlate`) |
| 6735–7210 | Slicer profiles | `loadSlicerProfiles`, `renderSlicerProfiles`, `importSlicerProfiles`, `autoDetectSlicerProfiles` |
| 7213–7410 | Profile recommendation & nesting | `requestProfileRecommendation`, `openNestingModal`, `runNesting`, `renderNestingPreview` |
| 7413–8210 | Settings | theme/accent (`applyTheme`, `applyFabricant`), `initSettings` (7444), Spoolman, Ollama/AI, auto scan, auto start, print costs, quote settings (8110+) |
| 8209–8470 | Ollama | `testOllamaConnection`, `recommendOllamaModel`, `ollamaAutoTag` |
| 8472–9010 | SOS Print | `runSosprintDiagnosis`, `renderSosprintQuestionStep`, `loadSosprintHistory`, `resumeSosprintConversation` |
| 9208–9645 | Filament inventory | `loadSpoolmanPage` (9219), `loadManualSpoolInventory`, `renderManualSpoolGrid`, `openSpoolInventoryModal`, `saveSpoolInventoryEntry` |
| 9642–10125 | Extras (drying, calibrations, parts) | `applyRoleUI`, `_loadSpoolDrying`, `_loadSpoolCalib`, `openPartsModal`, `loadParts`, `checkPartsLowAlerts`, `checkDryingDueAlerts` |
| 10122–10245 | Guests, pre-print check, reliability | `loadGuests`, `_prePrintWarningHtml`, `_renderStatsReliability` |
| 10245–10360 | Push | `loadPushSettings`, `savePushSettings`, `testPush`, `_applyReprintContext` |
| 10362–10535 | Monthly report | `openMonthlyReport`, `loadMonthlyReport`, `exportMonthlyReport`, `_loadSpoolReport` |
| 10537–10625 | Model updates | `loadModelUpdates`, `autoCheckModelUpdates` |
| 10625–10862 | Spool sheet & Spoolman grid | `showSpoolDetailPopup` (10697), `_detailFromSpoolman/Manual/TigerTag`, `renderSpoolmanGrid` |
| 10862–11260 | External accounts & TigerTag | `saveAccountKey`, `nexprintBrowserLogin`, `makerWorldStep1/2`, `loadTigerTagSpools`, `renderTigerTagGrid` |
| 11256–11410 | Side navigation | `setupNavDragAndDrop`, `applyNavOrderToSidebar`, `setupEventListeners` (11349) |
| 11406–11540 | Auth UI | `loadSecurityQuestionFor`, `showRecoveryCodeModal` |
| 11539–11700 | Header, search, mobile | `updateHeaderVisibilityForPage`, `resetGlobalSearch`, `toggleMobileSidebar` |
| 11714–11950 | Drag and drop / upload | `_uploadDroppedFiles`, `handleFilePicker` |
| 11946–12210 | Search | `isSemanticQuery`, `runSemanticSearch`, `handleSearchInput`, recent searches |
| 12211–12430 | Mobile nav, slicer send, selection | `toggleNavItem`, mobile bar scroll arrows (12239), `_confirmSendToSlicer`, `updateFolderSelectionBar` |
| 12485–12780 | Repair & converter | `loadRepairFiles`, `showRepairDiff` (12568), `loadConverterFiles`, `renderConverterFiles` |
| 13162–13200 | Printer compatibility | `checkPrinterCompatibility` |
| 13465–13800 | History | rating, cost, failure reason, `_populateHistoryPlatformFilter`, `_checkHistoryFileExists`, `loadDownloadHistory` |
| 13942–14250 | Printers | `loadPrinters`, `renderPrinters`, card cameras, `refreshAllPrinters` |
| 14244–14680 | Maintenance | `openMaintenanceModal`, tasks, `checkMaintenanceDueGlobal`, alert popups |
| 14675–14800 | Low stock | `checkLowStockOnStartup`, `showLowStockToast`, `showLowStockShopPopup` |
| 14796–15060 | Printer monitor | `openPrinterMonitor`, `fetchAndUpdateMonitor`, `updateMonitorUI`, `loadPrinterCamera` |
| 15428–15570 | Diagnostics | `loadAppVersion`, `enableDebugSessionAndRestart`, `pollDiagnosticConsole`, `exportDiagnosticLogs` |
| 17014–17030 | Cost | `_applyCostSpoolSelection`, `_applyCostPrinterSelection` |
| 17365–17560 | Projects | `loadProjects`, `renderProjectCard`, `refreshProjectDetail` |
| 17834–17940 | PWA / QR | `_detectMobileBrowserContext`, `_renderPwaBrowserHint`, `_loadQrCode` |

> Lines 15060–15428, 15570–17014 and 17030–17365 contain no named top-level functions: the code there is organized as event-listener blocks (`DOMContentLoaded` at l.12228, 13232, 15370, 15655) and nested functions (stats, print cost/quote, history, etc.). Use `grep` on DOM ids (`getElementById('…')`) to locate things.

---

## 6. style.css — landmarks

- 1–60: download history
- 62–131: variables (`:root`, `[data-theme="light"]`, `[data-fabricant="bambu|prusa|voron|creality"]`)
- 134–227: reset, `.btn*`
- 229–450: authentication screen, `.input-group` fields
- 452–600: `.app-screen` layout, `.sidebar`, `.nav-btn`
- 604–920: header, search (`.search-box`, history), view selectors, thumbnail progress
- 921–970: `.main-content`, drop zone, pages
- 972–2000: file grids (gallery/details), `.file-card`, badges, action buttons, metadata tooltips
- 2000–8076: later components (modals, dashboard, printers, filament, etc.) — not mapped line by line; search by class name.

---

## 7. i18n

- `languages/<code>.json` files: flat dictionary, `section.key` keys (e.g. `spoolman.sort_name`), plus `__dir`, `__name`, `__native`. 1,793 keys in each of the 8 languages (fr, en, de, es, it, ja, pt, zh).
- HTML: `data-i18n*` attributes; JS: `I18N.t('key')`; backend: reads `languages/<lang>.json` directly for push notifications and the splash screen (l.12484, 22049); the frontend fetches them via `/languages/<lang>.json` (served by Flask's static folder).
- `changelog.json`: `[{version, items:{<lang>:[…]}}]`; current version `0.6.9` (Nexprint entry), read via `load_changelog` (l.14388).

## 8. Quick recipes

- **Add an API route**: `@app.route` decorator + `@login_required` in the domain's section (section 3), taking `_viewer_guard` into account for writes.
- **Add a table**: `init_db` (l.1111) + a `migrate_*` function if needed for existing databases; remember the backup export/import (l.13592–13770).
- **Add a page**: `<div class="page" id="page-xxx">` in `index.html`, a `data-page="xxx"` button in the sidebar, click handling of `.nav-btn[data-page]` in `setupEventListeners` (l.11349, to be verified: `showPanel` only serves the authentication panels), an entry in `_navCommands` (palette).
- **New UI string**: add the key to the 8 `languages/*.json` files.
- **New printer brand**: a `*Connection` class + `_build_*_result` + `_ensure_*/_stop_*_connection` + discovery, then dispatch in `PrinterManager` (l.3026).
- **New Python dependency**: `requirements.txt`, `check_deps.REQUIRED_MODULES` and the fallback list in `main.py` (l.20–60).
- **New version**: `CURRENT_VERSION` (l.14384) + an entry at the top of `changelog.json`; the workflow only publishes a release if this version changes.
- **New model download site**: see the Nexprint example — `NexprintError` (l.11009) and `nexprint_get_model_files` (l.11059) in `main.py`, login through a window via `POST /api/accounts/nexprint/browser-login` (l.6051) + `/status` (l.6113), account card in `index.html` l.1793, `nexprintBrowserLogin` (`script.js` l.10930), startup status (`script.js` l.3460), link in `_DEFAULT_USEFUL_LINKS` (l.19491) **and** in `languages/useful_links.json`, label in the download history.

---

## 9. Ancillary files (build, tests, PWA, installer)

### check_deps.py
- `REQUIRED_MODULES` (l.28): 28 tuples `(import name, pip package, expected attribute, conflicting packages)`; `TELEGRAM_MODULES` (l.60, `telethon`) optional.
- Functions: `find_owning_packages` (65), `deep_check_module` (74, checks the real import **and** an attribute to detect a wrong package installed under the same name), `auto_install_missing_modules` (84, uninstalls the wrong package then runs `pip install --force-reinstall/--upgrade`, retries with `--break-system-packages`), `check_required_modules` (157), `_cli_main` (185).
- CLI: `python check_deps.py [--fix] [--telegram]`; exit code 1 if a dependency is missing.
- `main.py` imports it at the top (l.11–19, `try` block) and keeps a fallback copy of `_REQUIRED_MODULES` if the import fails (l.20–60): **any new dependency must be added in both places** (plus `requirements.txt`).

### requirements.txt
- Contains, in addition to `check_deps`: `pyinstaller`, `PyOpenGL-accelerate`, `telethon`.
- Linux: `pywebview[gtk]` + system packages `libgtk-3-0 libwebkit2gtk-4.1-0` (not installable via pip). macOS: pyobjc is installed automatically.
- ⚠️ `plyer` (used by `_send_native_notification`, main.py l.12460, and listed in `check_deps.REQUIRED_MODULES`) **does not appear** in `requirements.txt` — to be checked.

### sw.js (service worker, registered in script.js l.192–194)
- Caches `stellio-v5-shell` and `stellio-v5-assets`; old `stellio-*` caches are deleted on activation; change `CACHE_VERSION` to force a refresh.
- Strategy: `/api/*` and `/share/*` are never intercepted; `/assets/*` is cache-first; everything else is network-first with fallback to the cache, then `/index.html`. Only same-origin GET requests.
- Pre-cache: `/`, `/index.html`, `/script.js`, `/style.css`. Served at `/sw.js` by Flask's static folder.

### worker.py
- Contains only `process_3mf_task(file_path, plate_index=0)`, which returns **hard-coded** values (15000 vertices, 30000 faces): it is a skeleton. No reference in `main.py` (the only "worker" is `thumb_worker` in `process_generation_queue`, l.3990). The README nevertheless describes it as a "background worker (thumbnails, scans)".

### conftest.py (pytest tests)
- `_try_real_or_stub` replaces `trimesh`, `pyrender`, `pymeshfix`, `smbclient`, `rarfile` with stubs if they are not installed.
- Sets `STELLIO_DATA_DIR` to a temporary folder and `STELLIO_PORT=0` before importing `main.py` so the real data is never touched. The test files themselves were not provided.

### stellio-setup.iss (Inno Setup, Windows)
- Version injected at compile time via `/DMyAppVersion=…` (default `0.0.0-dev`); output `output/Stellio-Setup-<version>.exe`.
- Installs `dist\Stellio\*` (PyInstaller output) into `{commonappdata}\Stellio-app`, executable `Stellio.exe`, `users-full` permissions on the folder so that `.zip` patches (automatic updates without admin) can be applied.
- Prerequisites downloaded when needed (PowerShell): VC++ Redistributable x64 ≥ 14.40 and WebView2 (without WebView2, Stellio falls back to browser mode).
- If an installation already exists (AppId `{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}`): choose repair/update, uninstall then reinstall, or cancel. Languages: French, English. Desktop shortcut unchecked by default; `/LAUNCH=1` launches the app after a silent install.

### entitlements.plist (macOS)
- `allow-jit`, `allow-unsigned-executable-memory`, `disable-library-validation`, `allow-dyld-environment-variables` (required by the signed/notarized PyInstaller app).

### README.md — useful information
- Announced license AGPL v3 (⚠️ the provided `LICENSE` is the GPL v3, see §13); Python 3.8+, Flask 3.0+; announced platforms: Windows and Raspberry Pi/Linux (64-bit); supported models: STL, 3MF, OBJ.
- Printers: OctoPrint, PrusaLink, Klipper/Moonraker (HTTP), Bambu Lab (MQTT, AMS), Creality (WebSocket, CFS), FlashForge, Elegoo (SDCP).
- Shortcuts: `Ctrl+K` palette, `Ctrl+F` search, `Ctrl+N` download, `Ctrl+,` settings, `Ctrl+Z` undo deletion, `Alt+1-8` navigation, `F` favorites, `T` tag manager, `?` help, `Esc`.
- Files cited in the README and **absent from the repository**: `bin/` (ffmpeg/unrar binaries per OS, optional — ignored by `.gitignore`), test files. Everything else (`assets/`, the `library/monitoring/slicer/nesting.png` screenshots, `LICENSE`, `CODE_SIGNING_POLICY.md`) is in the repository (see §13–14).

---

## 10. Launch, CI/CD and installation

### launcher.py (entry point of the frozen builds)
- This is the script that PyInstaller compiles (`launcher.py` → `Stellio.exe` / `Stellio.app` / Linux binary); **`main.py` is not compiled**: it is copied next to it in an `app/` folder so it can be replaced by the auto-update `.zip` patches.
- `_app_dir()` (l.10): locates `app/` — next to the executable (Windows/Linux `--onedir`), `Stellio.app/Contents/Resources/app` (macOS), or next to the script in source mode.
- `_setup_early_env()` (l.33) adds `app/` to `sys.path`; `_setup_bootstrap_logger` (l.43) writes `launcher.log` (2 MB rotation ×2) into `<app_dir>/../logs/`; `_show_fatal_error` (l.56): Windows MessageBox, otherwise Tk, otherwise stderr.
- `_preload_dependencies` (l.98): parallel import of `_PRELOAD_MODULES` for diagnostics, **disabled by default** (enable with `STELLIO_DIAG_PRELOAD=1`); `STELLIO_TELEGRAM_VARIANT=1` adds `telethon`.
- `main()` (l.116): sets `STELLIO_LAUNCHER_EXE` (path of the executable, read by `install_update` main.py l.14699 and by the auto-start handling l.778/789), does `chdir(app_dir)` then `runpy.run_path(main.py, run_name="stellio_main")` — hence the `__name__ in ('__main__', 'stellio_main')` condition in `main.py` (l.21810).
- Pitfall: the `_PRELOAD_MODULES` list is a 3rd dependency list (in addition to `check_deps` and `requirements.txt`); it does not contain `plyer`.

### .github/workflows/build-and-sign.yml (GitHub Actions, "Build, sign and release Stellio")
- Triggers: push to `main` touching `main.py`, `index.html`, `script.js`, `style.css`, `launcher.py`, `check_deps.py`, `requirements.txt`, `stellio-setup.iss`, `assets/**`, `languages/**`, `bin/**`; or manual run with `dry_run` (build without release).
- Jobs: `check-version` (reads `CURRENT_VERSION` in `main.py`, only publishes if the tag `v<version>` does not exist yet → **`CURRENT_VERSION` must be incremented to trigger a release**) → `build` (Windows: PyInstaller `--onedir --windowed`, copies the patchable files into `dist\Stellio\app`, downloads ffmpeg + UnRAR, creates `Stellio-v<version>-patch.zip` + `.sha256`, compiles the Inno Setup installer) ‖ `build-macos` (matrix: `arm64` on `macos-latest`, `x86_64` on `macos-15-intel`; `.app` signed with Developer ID if the secrets `MACOS_CERTIFICATE`, `MACOS_CERTIFICATE_PWD`, `MACOS_SIGNING_IDENTITY` exist, otherwise ad-hoc signature; `.dmg` + sha256) ‖ `build-linux` (x86_64 AppImage with GTK/WebKit, ffmpeg, unrar) → `release` (GitHub draft `v<version>` with `.exe`, `.dmg`, `.AppImage`, `.zip`, `.sha256`).
- Every job runs `check_deps.py --fix` then `check_deps.py`; Python 3.11 everywhere.
- "Patchable" files copied into `app/`: `main.py`, `check_deps.py`, `index.html`, `script.js`, `style.css`, `assets/`, `languages/`, `bin/` (`launcher.py` is **not** included). `worker.py` is copied nowhere → confirms it is unused.
- ⚠️ The shared patch `.zip` is created in the **Windows** job: it therefore also contains `app\bin\` (ffmpeg.exe, DLLs, UnRAR.exe). The README announces a "pure source code" patch identical for Raspberry Pi/Linux — to be verified in the patch installation logic (`install_update`, main.py l.14694).
- ⚠️ The Windows artifact is named `stellio-installer-unsigned`: no Authenticode signing step appears in this workflow despite its name and the README's `CODE_SIGNING_POLICY` (signing is probably done outside CI or by hand on the release draft).
- `entitlements.plist` is also rewritten by the workflow (same content as the repository file).

### install-pi.sh (Raspberry Pi / Linux headless)
- 180-line bash script (`bash -n` passes; the git merge conflict from the previous version is resolved). The header gives the "swap" tip for low-RAM Raspberry Pis (`CONF_SWAPSIZE=2048` in `/etc/dphys-swapfile`).
- Content: refuses root, checks `sudo` and RAM (<1.5 GB → warning), `apt-get install` (git, python3-venv, build-essential, ffmpeg, unrar-free, JPEG/PNG libs, OpenBLAS/ATLAS, OSMesa/EGL), `git clone`/`reset --hard origin/main` into `~/stellio` (variable `STELLIO_DIR`), venv `~/stellio/venv`, `pip install -r requirements.txt` (failure tolerated, `check_deps.py` repairs at startup), creates `~/.stellio`, writes `/etc/systemd/system/stellio.service` (`STELLIO_HEADLESS=1`, `STELLIO_DATA_DIR`, `STELLIO_PORT`, `Restart=always`, `ExecStart=venv/bin/python3 main.py`), enables it and waits up to 30 s, then prints `http://<ip>:5000`.
- Re-running the script updates the code (`git reset --hard` + `git clean -fd`: any local modification in `~/stellio` is lost; data stays in `~/.stellio`).
- Note: the installer uses `unrar-free` whereas the Linux AppImage build embeds the real `unrar`.

---

## 11. Android companion app (apk/stellio.apk)

- Package `com.stellioapp.companion`, version `1.0.0` (code 1), minSdk 24, targetSdk 34, label "Stellio". Written in Kotlin (coroutines, AndroidX, Material), 912 entries, `classes.dex` ≈ 9 MB. **Only the APK is provided, not the Android Studio project.**
- Activities: `MainActivity` (launcher) and `com.journeyapps.barcodescanner.CaptureActivity` (ZXing, QR code scanning). Providers: `androidx.core.content.FileProvider` (sharing the captured photo) and `InitializationProvider`.
- Permissions: `INTERNET`, `ACCESS_NETWORK_STATE`, `ACCESS_WIFI_STATE`, `CAMERA`, `WRITE_EXTERNAL_STORAGE`.
- App classes (from names in the dex): `MainActivity` (WebView: `setupWebView`, `connectToStellio`, `findReachableUrl`, `registerNetworkMonitor`, `scheduleOfflineCheck`, `startReconnectLoop`, `setupLanguageSpinner`) and `ConnectionPrefs` (remembered server address). Principle: the app remembers the Stellio server URL (typed or scanned via QR code, cf. `/api/qrcode`), tests that it is reachable, loads the web interface in a WebView and reconnects automatically after a drop.
- Distribution: `STELLIO_COMPANION_APK_URL` (main.py l.3521) points to `https://www.github.com/stellio-app/stellio/raw/main/apk/stellio.apk`; `GET /api/qrcode?source=apk` (l.21586) generates the download QR code; on the web side, taking a photo goes through `pickPhoto` (script.js l.3634) and the `modal-photo-source` modal.
- To change the native behavior (camera, mobile bar arrows…), the Android project (`MainActivity.kt`, `AndroidManifest.xml`) is required — not included here; the scrollable mobile navigation bar on the web side is in `script.js` (l.12239) and `style.css`.

---

## 12. Translated documentation

- `docs/readme/README.<lang>.md` (fr, de, es, it, pt, ja, zh): full translations of `README.md` (same sections, same project structure); relative links: `../../README.md`, `../../LICENSE`, `../privacy/PRIVACY.md`, `../../library.png`… Any new feature documented in `README.md` must be carried over to the 7 translations (and to `languages/changelog.json`).
- `docs/privacy/`: `PRIVACY.md` (EN) + `PRIVACY.{fr,de,es,it,pt,ja,zh}.md`, "last updated" September 1, 2026. Content: "local-first" principle, locally stored data (library, thumbnails, configs, AES-CFB-encrypted API keys, history, logs), optional third-party services (GitHub updates, Printables/MakerWorld/Thingiverse, printers, Cloudflare Tunnel, remote Ollama, Spoolman), security, rights, contact `contact@stellio-app.com`.
- ⚠️ Consistency gaps noted: the privacy policy does not mention TigerTag (Firebase), push notifications (ntfy/Telegram/Discord/webhook), remote Stellio instances or new-model-version detection — services that contact third parties according to the code and the README; the README announces `Stellio-Setup.exe` whereas the produced file is named `Stellio-Setup-<version>.exe`; it describes `worker.py` as a thumbnail worker although it is unused.

---

## 13. License, code signing and assets

### LICENSE
- Standard text of the **GNU General Public License v3** (June 29, 2007, 674 lines), with no project-specific copyright line and no "or any later version" wording.
- ⚠️ **License inconsistency**: `README.md` ("License: AGPL v3" badge + "📜 License" section) and its translations say **AGPL v3** and link to this file; the file is the **GPL v3** (clause 13 only allows combining with AGPL). Third version: the "About" modal (`index.html` l.2838–2840, key `about.legal`) displays "© 2026 Stellio Project. All rights reserved". A license must be chosen, `LICENSE` replaced with the AGPL v3 text if that is the one, and the README, translations and `about.legal` (8 `languages/*.json` files) aligned.

### CODE_SIGNING_POLICY.md
- Linked from the README's "🔏 Code Signing Policy" section ("Windows executables published in Releases are digitally signed").
- Content (9 sections): §1 scope (Windows exe, installer, `bin/` binaries, CI); §2 why sign (local server + JS/Python bridge, third-party credentials encrypted with AES using `encryption.key`, TLS disabled for some MQTT brokers, auto-start via the `Run` key); §3 certificate from a public CA, EV recommended, OV as a transitional option; §4 non-exportable key (hardware token, cloud HSM or a service such as Azure Trusted Signing / DigiCert KeyLocker / SignPath); §5 process (build from a tag, antivirus scan, signing in CI with approval, RFC 3161 timestamp, SHA-256 of third-party binaries verified, `signtool verify /pa /v`); §6 update chain integrity; §7 compromise; §8 Author/Reviewer/Approver roles (a single maintainer may hold all of them, documented); §9 review.
- ⚠️ Gaps with the provided code:
  - `build-and-sign.yml` contains **no** Windows signing step (artifact `stellio-installer-unsigned`, no `signtool`, no SignPath), no antivirus scan and no SHA-256 verification of the `bin/` binaries: §3–5 describe a process that does not appear in the CI (it may happen outside CI, not verifiable here).
  - §6 says "if an automatic update mechanism is added in the future" whereas one already exists (`install_update` l.14694, `download_update`). `download_update(download_url, progress_callback, expected_sha256=None)` can verify a SHA-256 (deletes the file and aborts on mismatch) but only if `expected_sha256` is provided; I found **no** Authenticode verification of the downloaded file, and the `.zip` patch is not a signed executable.
  - §5.1 refers to `check_deps`/`REQUIRED_MODULES` as "locked dependencies": these are lists of module names, not pinned versions (`requirements.txt` pins no version: package names only, so the build is not reproducible).
  - The policy covers "Windows"; macOS is signed/notarized in the CI (Developer ID if secrets exist, otherwise ad-hoc) without being mentioned — yet §9 plans to update it when a platform is added.

### assets/logo-nom-stellio.ico
- Multi-size ICO file (16, 24, 32, 48, 64, 128, 256 px), ~145 KB.
- Uses: `stellio-setup.iss` (`SetupIconFile`); `.github/workflows/build-and-sign.yml` l.142 (`--icon` PyInstaller Windows), l.261–270 (conversion via Pillow + `iconutil` into `assets/logo-nom-stellio.icns` for macOS, l.322 `--icon`), l.602 (AppImage: `Image.open(...).resize((256, 256))` → `stellio.png`).
- ⚠️ To check: `Image.open()` on a multi-size ICO loads only the largest image by default; if that is not 256×256, `resize((256, 256))` stretches it.
- The logo `assets/logo-nom-stellio.png` (256×233, real PNG; displayed in `index.html` l.57, the PDF report in `main.py` and the `script.js` fallback) is not square.

### assets/tigertag-logo.svg
- "potrace" SVG (vector stencil generated from a bitmap): 92×92 pt, `viewBox 0 0 92 92`, group `translate(0,92) scale(0.1,-0.1)`, 11 `<path>` elements filled in black `#000000`, no `<style>` and no `currentColor`.
- Usage: `index.html` l.2297, `<img src="assets/tigertag-logo.svg" class="tigertag-banner-logo" onerror="…hides the image…">` in the TigerTag banner of the inventory; `style.css` l.5347 (`height: 26px; width: auto; flex-shrink: 0`). No CSS filter is applied.
- ⚠️ Being solid black with no filter, it will be barely visible on the dark theme if the banner background is dark (to be checked visually); if so, add `filter: invert(1)` in dark theme or switch the SVG to `fill="currentColor"` (requires inlining it or using a CSS mask).
- The service worker caches `/assets/*` cache-first: after replacing the logo or the icon, bump `stellio-v5` in `sw.js` to force the refresh.

---

## 14. GitHub repository: ancillary files

The public repository (`stellio-app/stellio`, branch `main`, 84 files, last commit "V 0.6.9") contains, in addition to what is described above:

### stellio_manager.bat (284 lines, Windows)
- Relaunches its own console (`cmd /k`), switches to UTF-8, reads `CURRENT_VERSION` from `main.py` via `findstr`, then shows a menu: [1] run in test mode, [2] test mode DEBUG (detailed logs), [3] run the `test/` folder (new features, folder ignored by git), [4] check/install dependencies, [5] quit.
- `:CHECK_VENV` creates `venv\` with the embedded `python\python.exe` if present; `:INSTALL_AND_CHECK_DEPS` runs `pip install --upgrade pip`, `pip install --upgrade -r requirements.txt` then `venv\Scripts\python.exe check_deps.py --fix`. Launch: `venv\Scripts\python.exe main.py`.

### .gitignore
- Ignores `python/`, `Lib/`, `Scripts/`, `redist/`, `venv/`, `env/`, **`bin/`**, `build/`, `dist/`, `output/`, `release/`, `test/`, `stellio-data*/`, `*.log`, `*.sqlite`, `*.db`, `StellioCompanion/` (local Android project), WebView2/VC++ installers, `token*.txt`, `.env`, `*.p12|*.pfx|*.pem`.
- `bin/` is ignored although the workflow triggers on that path: ffmpeg and UnRAR do not come from the repository, the workflow downloads them on every build ("Download ffmpeg (not committed to the repo, fetched fresh each build)" and "Download UnRAR" steps).

### assets/
- Logos: `logo-stellio.png` (234×256, favicon + apple-touch-icon `index.html` l.34–35, sidebar l.217, About l.2824), `nom-stellio.png` (256×48, sidebar logotype l.218), `logo-nom-stellio.png` (256×233, l.57, PDF reports), `logo-nom-stellio.ico`, `tigertag-logo.svg`, `tigertag-logo.png` (270×68 PNG, not referenced).
- These `.png` files are now real PNGs. ⚠️ `logo-stellio - Copie.png` is still an **ICO file with a .png extension** and an unused duplicate: it should be deleted.
- `vendor/`: `fontawesome/` (css + webfonts), `inter/` (5 latin weights), `mdi/` (Material Design Icons), `threejs/` (`three.min.js`, `controls/OrbitControls.js`, `controls/TrackballControls.js`, `loaders/{STL,OBJ,3MF}Loader.js`) each with a `LICENSE.txt`.
- `index.html` l.46–51 now loads Three.js and its loaders from `assets/vendor/threejs/` (no more CDN): the 3D viewer works offline once the assets are cached (`sw.js` caches them cache-first on first load, without pre-caching).

### Gaps noted in the repository (v0.6.9)
- **Nexprint / useful links**: the 0.6.9 changelog says Nexprint joins the "3D models" links. This is true for `_DEFAULT_USEFUL_LINKS` (`main.py` l.19491), but `languages/useful_links.json` (25 links, "3D models" group: Printables, MakerWorld, Thingiverse, Cults) does not contain Nexprint; if that file takes precedence, the link does not appear.
- **README / PRIVACY**: neither `README.md` (and its translations) nor `docs/privacy/PRIVACY.md` mention Nexprint; `PRIVACY.md` also does not cite the third-party site contacted for downloading nor the login through the official site's window.
- **License**: `LICENSE` is still the GPL v3 whereas the README announces AGPL v3, and `about.legal` displays "All rights reserved" (see §13).
- **Windows signing**: still no Authenticode signing step in the workflow (see §13).
- **`plyer`**: still absent from `requirements.txt` although `main.py` uses it (l.12460) and `check_deps.REQUIRED_MODULES` lists it.
