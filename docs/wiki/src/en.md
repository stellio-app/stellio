@@@ Home | Home
# Stellio Wiki
{{img:dashboard}}


**Stellio** is the 3D file manager for makers and 3D printer owners. It centralizes your library (STL, 3MF, OBJ, STEP, PLY, AMF), automates repetitive tasks and plugs into your printing workflow.

> 🔒 **Philosophy**: your data stays with you. Everything runs locally; by default, nothing leaves your machine.

## Where to start

| I want to… | Page |
|---|---|
| Install Stellio | [Installation](en-Installation) |
| Take my first steps | [Getting started](en-Getting-Started) |
| Manage my 3D files | [Library](en-Library) |
| Connect my printers | [Printers](en-Printers) |
| Track my spools | [Filament](en-Filament) |
| Download models | [Downloads](en-Downloads) |
| Use AI and S.O.S Print | [Artificial intelligence](en-AI) |
| Calculate costs, quotes, invoices | [Costs and management](en-Costs-and-Management) |
| Reach it from my phone | [Remote and mobile access](en-Remote-Access) |
| Install on Raspberry Pi / Proxmox | [Server edition](en-Server-Edition) |
| Configure, back up, understand my data | [Settings and data](en-Settings-and-Data) |
| Fix a problem | [Troubleshooting](en-Troubleshooting) |
| Contribute to the project | [Contributing](en-Contributing) |

## Useful links

- 🌐 Website: [stellio-app.com](https://stellio-app.com) — ▶ [live demo (read-only)](https://demo.stellio-app.com)
- 📦 [Downloads (Releases)](https://github.com/stellio-app/stellio/releases)
- 🐛 [Report a bug](https://github.com/stellio-app/stellio/issues) · 💡 [Suggest an idea](https://github.com/stellio-app/stellio/discussions) · 💬 [Discord](https://discord.gg/ySxpHvS6bd)
- 📜 **AGPL v3** license

@@@ Installation | Installation
# Installation

| Platform | File / method | Mode |
|---|---|---|
| 🪟 Windows | `Stellio-Setup-<version>.exe` | Desktop app |
| 🪟 Windows portable | `Stellio-v<version>-portable-win64.zip` | Desktop app, no installation |
| 🍎 macOS | `.dmg` (Apple Silicon `arm64` or Intel `x86_64`) | Desktop app |
| 🐧 Linux | `Stellio-v<version>-x86_64.AppImage` | Desktop app |
| 🍓 Raspberry Pi / Linux | `install-pi.sh` | Server (browser) |
| 🖥️ Proxmox VE | `stellio-lxc.sh` | One-command LXC container |
| 📲 Android | Companion APK | See [Remote and mobile access](en-Remote-Access) |

All files are on the [Releases](https://github.com/stellio-app/stellio/releases) page, each with a `.sha256` checksum.

## Windows

1. Download the installer from the Releases.
2. Run `Stellio-Setup-<version>.exe`.
3. Done.

**Portable version**: unzip anywhere (disk, USB drive) and run `Stellio.exe`. Your data stays in the `data` folder next to the executable (keep the `portable.flag` file).

> ⚠️ The installer is **not code-signed**: Windows SmartScreen may show a warning. Check the `.sha256` if you wish; the built-in updater verifies it before installing.

## macOS

Open the `.dmg` and drag Stellio to Applications. Pick the file that matches your Mac: `arm64` (M1, M2, M3…) or `x86_64` (Intel). Builds are not notarized: on first launch, right-click → **Open**.

> If the screen stays white: port 5000 may be taken by macOS "AirPlay Receiver". Stellio then automatically picks another free port. See [Troubleshooting](en-Troubleshooting).

## Linux (AppImage)

```bash
chmod +x Stellio-v*-x86_64.AppImage
./Stellio-v*-x86_64.AppImage
```
The AppImage embeds its update information (`.zsync`).

## Raspberry Pi / Linux server

**Headless server** mode: Stellio runs in the background and is used from a browser. See [Server edition](en-Server-Edition) for details.

```bash
curl -O https://raw.githubusercontent.com/stellio-app/stellio/main/install-pi.sh
chmod +x install-pi.sh
./install-pi.sh
```

## Proxmox VE

In the **Proxmox host Shell**:
```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/stellio-app/stellio/main/stellio-lxc.sh)"
```
Details in [Server edition](en-Server-Edition).

## Updates

- **Desktop**: Stellio detects new versions from GitHub and applies a `.zip` patch (same mechanism on Windows, macOS and Linux). The dashboard "Update" widget opens the update window.
- **Server**: same automatic update, or `update-stellio` (LXC container) / `./install-pi.sh` (Raspberry Pi).
- On the first launch of each version, missing modules (PDF quotes, spreadsheet import, notifications…) are downloaded automatically.

@@@ Getting-Started | Getting started
# Getting started
{{img:library}}


## 1. First launch
Stellio shows a **guided tour** and a "Getting started" checklist. You can restart the tour at any time from Settings.

## 2. Create your account
Accounts are **local**: password + recovery code + secret question. Password reset is 100% local, with no email or internet.

## 3. Add your sources
A **source** is a folder or share that holds your models:
- local folder, single file, **SMB** or **NFS** share;
- 3D folders detected on your computer are **suggested** and added in one click;
- for each source, you choose which file types are shown.

Stellio then scans your files and generates 3D thumbnails in the background.

## 4. Add a printer (optional)
Open the **Printers** page: network discovery offers the machines it detects. See [Printers](en-Printers).

## 5. Choose your slicer
Stellio automatically detects your installed slicers (OrcaSlicer, Bambu Studio, PrusaSlicer, Cura…). The send button opens the file directly in the slicer.

## Dashboard
The home page gathers prints in progress, low stock, recent prints and recent files. The **widgets** (about twenty) can be reordered by drag and drop and hidden: current prints, low stock, latest S.O.S Print, suggestions, Stellio instances, completed projects, gallery, quotes…

## Everyday tools
- **Command palette** `Ctrl+K`: navigate, run an action, find a file, tag, spool or profile.
- **Notification center** (bell): print finished, failure, maintenance, low stock, spool drying.
- **Floating widget** showing the current print's progress, visible on every page.
- **Keyboard shortcuts**: see [Settings and data](en-Settings-and-Data).

@@@ Library | Library
# Library
{{img:library}}


## Sources and thumbnails
- Multiple sources: local folders, files, SMB/NFS shares.
- **Automatic 3D thumbnails** (PyRender, or a CPU fallback renderer) with an enlarged preview on hover.
- Generation **pauses as soon as you use the app** and resumes afterwards.
- **Thumbnail performance** setting: Automatic / Eco / Normal / Fast.
- Formats: STL, 3MF (including multi-plate and PrusaSlicer), OBJ, STEP/STP, PLY, AMF (converted to STL for slicers that cannot read them), and archives (ZIP, RAR, 7z, TAR) browsable directly.

## Organize
- Colored **tags**, with AI auto-tagging; tag several files in one click.
- **Favorites**, advanced filters (type, size, weight, print status), **saved filters**.
- Status filters: "Sent to slicer", "Already printed", "Already succeeded", "Already failed".
- **"Filament stock" filter**: keeps only files printable with the spools you own.
- Sort, search and filters are **remembered** when you reopen the app.
- **"Print soon" queue**, reorderable, sendable to the slicer.
- **Bulk rename** (find/replace, prefix, suffix, numbering) with a preview.
- **Undo deletions** (`Ctrl+Z`) thanks to a 5-minute temporary trash; also works for tags, projects and sources.
- Fast selection: `Shift+click` for a range, arrows + `Enter`.
- **Duplicate detection** (exact and similar geometry).
- **Model origin**: source link, author, license, notes, download date.
- **Drag and drop** 3D files from your file explorer, also through a browser.

## Search
- Classic search and **AI semantic search** ("I'm looking for a support for…"), with recent searches remembered.
- **Smart collections**.

## Projects / assemblies
Group several files for a single object.
- **Multi-plate** 3MF: adding it to a project splits it into one 3MF per plate (6 plates = 6 files), stored in a hidden folder.
- **"Split plates"** action in a file's ⋯ menu.
- Project card: click the thumbnail = 3D viewer; "All / In progress / Completed" filter remembered; **Project cost** in one button.

{{img:projects}}

## 3D viewer and tools
- **3D viewer** (Three.js, works offline), plate navigation.
- **Automatic bed nesting** (rectpack, or real silhouette with shapely).
- **Mesh repair** (trimesh + pymeshfix) with before/after comparison.
- **Converter** STL ↔ 3MF ↔ OBJ.
- **Printability analysis** (overhangs) and **suggested orientations**.
- **Integrity check** (corrupted or missing files).
- Detailed **statistics** (formats, platforms, profile reliability).

{{img:viewer}}

## History and photos
- **History** paginated by week, with success/failure rating (which feeds the AI), **View file** and **Reprint** buttons, filters by platform, result and dates.
- **Print photo gallery**. The end-of-print photo is then set to *Success* or *Failed* with one click.
- **My G-codes**: G-codes linked to a file, download, and an **Open in slicer** button.
- Library **backup**: see [Settings and data](en-Settings-and-Data).

@@@ Printers | Printers
# Printers
{{img:printers}}


## Supported brands

| Brand | Models | Connection |
|---|---|---|
| **Bambu Lab** | X1/X1C/X1E, X2D, P1P/P1S, P2S, A1/A1 mini, H2D/H2S/H2C | MQTT (LAN + cloud): monitoring, AMS, camera, SSDP discovery |
| **Prusa** | MK4, MK3.9, MK3.5, MINI+, XL, CORE One | PrusaLink (HTTP) |
| **Creality** | K1/K2 series, Ender-3 V3, Hi | WebSocket: monitoring, CFS, UDP discovery |
| **Elegoo** | Centauri Carbon 1 & 2, Saturn/Mars resin series | SDCP (WebSocket) |
| **FlashForge** | Adventurer 5M/5M Pro, AD5X | Proprietary API |
| **Klipper / Moonraker** | Any Klipper machine (Voron…) | HTTP: monitoring, upload, camera, exact hours |
| **OctoPrint** | Any printer driven by OctoPrint | HTTP |

Other models that speak the same protocol usually work. Tell us on GitHub if yours does.

## Add a printer
- **Automatic discovery** of the local network (SSDP, UDP broadcast, targeted probes): detected printers are added in one click.
- Otherwise, manual entry (type, model, address, access key).
- Set the **build volume** (X, Y, Z): Stellio warns before sending if the part is too large.

## Monitoring
- Temperature, progress, live camera; thumbnail and name of the current file on the card.
- Automatic print-hour counter.
- **Floating progress widget**; it sits to the left of the "back to top" arrow when that arrow is shown.

## Send to slicer / printer
- Send window with **quick preview** (weight, estimated time), **spool selection** and recalled calibrations.
- **Pre-print check**: spool needs drying, abrasive filament (hardened steel nozzle advised), missing calibration, build volume, enough material.
- **Reprint like last time** from the history.
- **Light collaborative mode**: warns if another device is viewing the file or before a double send.
- **Open in slicer** from "My G-codes".

## During the print
- **Smart plug** (Shelly, Tasmota, Home Assistant): Stellio reads the watts and records real consumption (kWh) and cost.
- **Real filament consumption** recorded after the print.
- **End-of-print photo** taken when the print reaches **100%** (the part is still on the bed), a single photo to rate *Success/Failed*.
- **AI failure watch** (Ollama with vision, 100% local): alert on spaghetti or a detached part, **never an automatic stop**.
- Automatic **timelapse** (camera → MP4 video, needs ffmpeg).
- Read-only **status share links**.

## Maintenance
- **Predictive maintenance** with brand-specific tasks.
- **Wear parts** (nozzles, plates, belts…) with stock alerts, linked to maintenance tasks.
- **Calibrations** (flow, pressure advance, temperatures) per filament and printer.

@@@ Filament | Filament
# Filament

## Inventory sources
| Source | Details |
|---|---|
| **Spoolman** | Automatic detection on the network. Stellio **no longer writes** consumption to it (avoids double counting). |
| **Manual** | Hand-entered spools, Excel/CSV import. |
| **TigerTag** | NFC/RFID identification. Sign in with email and password (only an encrypted token is kept) or reuse a TigerTag Studio session. **Read-only.** |
| **OpenPrintTag** | Open NFC tag standard: import/export `.bin` files, read/write from the Android app, consumed weight kept up to date. |
| **Bambu AMS / Creality CFS** | Slot reading. |

**Open Filament Database**: search a spool by brand, material and color, then create it in one click (weight, diameter and density prefilled).

## Day to day
- **Automatic consumption** on send-to-slicer, with a compatibility check (enough material?).
- **Low-stock alerts** at startup, adjustable threshold, "To order" checkbox and buy link.
- **Buy a spool again**: the manufacturer's shop first (Arianeplast, Bambu Lab, Polymaker, eSUN, Sunlu…), then general shops; stock checked automatically when the site allows it.
- **Drying**: log, status (dry / needs drying) by material, suggested temperature and duration, reminders.
- **Spool sheet**: prints, grams, cost and untracked difference.

## Weighing and forecast
The **Filament weighing and forecast** block estimates each spool's **run-out date** from its daily consumption.
- The remaining weight comes from a manual weighing or from TigerTag.
- TigerTag weights feed **the forecast only**: they appear here only for a spool **about to run out** (14 days or less). The rest is in the inventory.
- A manual weighing form is always available.

{{img:filament}}

## Consumption forecast
The library can show a **restock warning** when stock is not enough for your favorites.

@@@ Downloads | Downloads
# Downloads

Download models straight into your sources from several platforms:

| Platform | Sign-in |
|---|---|
| **Printables** | GraphQL API |
| **MakerWorld** | Two-step Bambu Lab login |
| **Thingiverse** | API key |
| **Nexprint** (Elegoo) | Account email and password, stored encrypted |
| **Creality Cloud** | From Settings (encrypted credentials; Google sign-in not supported) |
| **Snapmaker Space** | Same |

- **Ctrl+N** opens a new download.
- The file lands in the source of your choice and the **model origin** (link, author, license) is recorded.
- **New version**: every day, Stellio checks whether downloaded models (Printables, MakerWorld, Thingiverse) have been updated.
- **My likes / My creations**: connected accounts are tested at each desktop launch (every 24 h on server).
- **Useful links**: shops, manufacturers, model sites and resources, in collapsible sections.

@@@ AI | Artificial intelligence
# Artificial intelligence

## Local AI (Ollama)
By default, AI runs **100% locally** with [Ollama](https://ollama.com/). It can be turned off.

Features:
- **Auto-tagging** and **description** of models;
- Natural-language **semantic search**;
- **Printability analysis** and **suggested orientations**;
- **Slicer profile recommendation** (geometry + success history);
- **Print time estimation** before slicing;
- **Failure watch** (vision model).

The Ollama server address is set in Settings (`ollama_url`): you can point to a more powerful remote machine (useful on a Raspberry Pi).

## Online AI (server edition, optional)
Instead of Ollama, use **Claude** (Anthropic), **ChatGPT** (OpenAI) or **Gemini** (Google) with **your own API key** (Settings → Artificial intelligence).
- The key is encrypted on the server and never sent back to the browser.
- Requests (file names, tags, descriptions, S.O.S Print photos) go to the provider you chose and are billed on your key.
- Ollama remains the default.

## S.O.S Print
**Adaptive** diagnosis of a print failure:
1. You describe the problem (a photo is possible at every step) and, if you want, the settings used (temperatures, speeds, retraction…).
2. Stellio asks **one question at a time** (4 at most) and narrows a live list of hypotheses.
3. It gives a **final diagnosis**.

Conversations are saved: reopen them or mark them as resolved.

> ℹ️ The "Success / Failed" results you rate in the history improve the recommendations.

@@@ Costs-and-Management | Costs and management
# Costs and management
{{img:management}}


## Print cost calculation
Material, electricity, machine wear (per hour), fixed fee, margin in % and quantity: unit price and total to the cent.
- Set the **default margin** once in *Settings → Print pricing*; the history shows the **sale price** next to the cost, while statistics keep using the real cost.
- **Project cost**: the same calculation for all files in a project.
- **Smart plug**: the measured power replaces the electricity estimate.
- **CO₂ footprint** of your prints (material + electricity).

## PDF quotes
Generated from the calculator: client, item name, notes; configurable header (name/company, logo, address, phone, email, website, tax ID) and legal notices in the footer. Every quote is kept (PDF copy) and browsable in the **Quotes** widget.

## "Management" screen
Visible when *Enable cost, quote and invoicing features* is checked:
- **Client quotes**: a **tracking link** lets the client view, accept or decline the quote online; acceptance creates the print task and shows your deposit information. **Stellio processes no payment.** Links are always external; if remote access is off, the screen offers to turn it on in one click.
- **Accounting**: monthly ZIP export (CSV of documents, invoice PDFs, totals by month).
- **Finished-parts stock**: alert threshold and restock (task created by hand or automatically).

## Workshop
- **Order queue** with real margin, client book, payments, deposit invoices and credit notes, SMTP email, CSV export.
- Public **client tracking page** per order, no account needed: never any price, margin or internal notes.
- **Smart dispatch**: Stellio suggests the best printer for each task (free, material loaded, queue) **without ever starting a print**.
- **Daily or weekly summary** by notification and push (tasks, delays, energy, spools, invoices, stock).
- **Slicer profile sharing** to a paired instance.

## Reports
- **Reliability**: success rate and cost of failures by profile, material, printer or spool.
- **Monthly report** compared with the previous month, exportable as PDF.
- Shareable **print report** (PNG image) from the history.
- Real **energy** per smart plug.



{{img:stats}}
@@@ Remote-Access | Remote and mobile access
# Remote and mobile access

## Phone and tablet
- **QR code** for mobile access to the library (**installable PWA**).
- **Android companion app**: a dedicated QR code (Settings → mobile access) downloads the APK. It handles internal and external addresses with automatic switching, QR pairing, photos straight from a print, and reading/writing OpenPrintTag NFC tags.
- Full-screen **workshop mode** for tablet/phone.

## Remote access
- **Cloudflare Tunnel** (free, random or fixed address), or a **custom address** (domain name, DynDNS, VPN, Tailscale…) to avoid Cloudflare, with a one-click return to Cloudflare.
- Temporary **share links** (24 h, single use).

## Accounts
- **Local accounts** with a recovery code and secret question.
- **Session confirmation**: when the app opens with a saved session, Stellio asks you to confirm the account.
- **Read-only guest accounts**: share library, printers and stock without risk.
- On a PC, browser access to the Windows app is blocked (internal token): use the app window.

## Several Stellio instances
- Other installations on the local network are **detected** and added in one click (enter their local key).
- **Send a file** to another instance, into the folder of your choice.
- Instance status widget on the dashboard.

## Notifications
- Native **Windows** notifications, **browser** notifications (Pi, mobile).
- **Push**: ntfy, Telegram, Discord or webhook, even with the window closed (print finished, failure, maintenance, stock).

## Home automation
- **MQTT / Home Assistant**: state publishing and automatic discovery; "Stellio" MQTT device and sensors.

@@@ Server-Edition | Server edition
# Server edition

The **server edition** turns on for Linux (Raspberry Pi, VM, LXC, Docker) or with `STELLIO_HEADLESS=1`. Windows and macOS keep the desktop app. Stellio runs in the background and is used from a browser: `http://<ip>:5000`.

## Raspberry Pi / Linux
Requirements: Raspberry Pi 4 or 5 recommended, **64-bit** Raspberry Pi OS.

`install-pi.sh` installs system dependencies (`ffmpeg`, `unrar`, 3D rendering libraries), a dedicated Python environment and a `stellio` **systemd service** that starts at boot and restarts on crash.

```bash
sudo systemctl status stellio
sudo systemctl restart stellio
sudo journalctl -u stellio -f
```
Low on RAM? Increase swap if installing the Python dependencies fails, then rerun the script.

## Proxmox VE (LXC container)
The `stellio-lxc.sh` script offers **default** or **advanced** settings (CTID, cores, RAM, disk, bridge, VLAN, DHCP or static IP, storage, host folder to mount), then:
- creates an **unprivileged Debian 12** container (2 cores, 2 GB RAM, 32 GB disk, start on boot);
- installs Stellio in it with `install-pi.sh`;
- prints the address `http://<container-ip>:5000` and the root password.

```bash
pct exec <CTID> -- update-stellio              # update
pct exec <CTID> -- journalctl -u stellio -f    # logs
```
- **Non-interactive mode**: variables `var_mode=default var_cpu=4 var_ram=4096 var_disk=16 var_ip=192.168.1.50/24 var_gw=192.168.1.1` (list at the top of the script).
- **Storage**: `var_choose_storage=1`, `var_storage`, `var_template_storage`.
- Script **language**: `var_lang=en` (fr, en, de, es, pt, it, zh, ja).
- **Sources**: in this container, only **SMB/NFS** shares are offered. With `var_mount=/host:/mnt/models`, "Local folder" is allowed too. Setting: `/etc/systemd/system/stellio.service.d/sources.conf` (`STELLIO_ALLOWED_SOURCE_TYPES`).

## Safeguards (1.0.7)
`install-pi.sh` sets up:
- a **check every minute** (`stellio-watchdog`): restarts Stellio if it stops responding (3 failed checks, 3 minutes of grace after a start), starts it if it is stopped, restarts the network if the IP address is lost, cleans logs and the apt cache if the disk has under 300 MB free;
- a service that **never gives up** restarting;
- **CPU 75%**, **RAM 75% (slowdown) / 85% (hard limit)** caps, low priority, and Stellio sacrificed first when memory runs out;
- logs limited to **100 MB**.

Watchdog interventions: `journalctl -t stellio-watchdog`. Existing containers get all of this with `update-stellio`.

## Server edition specifics
- ☁️ Optional **online AI** (see [Artificial intelligence](en-AI)).
- 📥 **Slicer profiles**: Stellio cannot see the slicers on your PC and does not connect to slicer clouds (Orca Cloud, Bambu Cloud…). Export your profiles (OrcaSlicer: File → Export → Export Preset Bundle), then import them in *Settings → My slicer profiles*, or use a **watched profiles folder** (Syncthing, network share, scp…).
- 🐯 **TigerTag**: official sign-in with email and password; Google account? First set a password with "Forgot password" in the TigerTag app. Fallback: copy the TigerTag Studio data folder to the server.
- After an update, the browser reloads automatically.

## Environment variables
| Variable | Purpose |
|---|---|
| `STELLIO_HEADLESS` | Forces server mode |
| `STELLIO_PORT` | Port (default 5000) |
| `STELLIO_SERVER_URL` | Public address of the server |
| `STELLIO_DATA_DIR` | Data folder |
| `STELLIO_ALLOWED_SOURCE_TYPES` | Allowed source types (`folder,smb,nfs`) |
| `STELLIO_START_MINIMIZED` | Start minimized |
| `STELLIO_NO_AUTO_INSTALL` | Disables automatic module installation |

@@@ Settings-and-Data | Settings and data
# Settings and data

## Appearance
- **Theme**: Dark / Light / System. **Light** by default; dark only if the system (or you) asks for it.
- **Brand themes**: Stellio, Bambu, Prusa, Voron, Creality; 33 palettes, custom accent color, adjustable background image.
- **Accessibility**: high contrast, reduced motion, visible keyboard focus, text size, color-blind mode.
- **8 languages**: fr, en, de, es, it, pt, ja, zh.
- Navigation reorderable by drag and drop; **undo the last setting you changed**.

{{img:settings}}

## Keyboard shortcuts
| Shortcut | Action |
|---|---|
| `Ctrl+K` | Command palette |
| `Ctrl+F` | Search |
| `Ctrl+N` | New download |
| `Ctrl+,` | Settings |
| `Ctrl+Z` | Undo the last deletion |
| `Alt+1-8` | Quick navigation |
| `Shift+Click` | Select a range |
| `↑ ↓ ← →` + `Enter` | Navigate and open |
| `F` | Favorites |
| `T` | Tag manager |
| `?` | Shortcuts help |
| `Esc` | Close / clear search |

## Where is my data?
| System | Folder |
|---|---|
| Windows | `%APPDATA%\Stellio` |
| macOS / Linux | `~/.stellio` |
| Windows portable | `data` next to `Stellio.exe` |
| Custom | `STELLIO_DATA_DIR` variable |

Contents: `stellio.db` database (SQLite), `app_settings.json` settings, `stellio.log` log, downloaded `extra_libs` modules. Code stays separate from data and is never touched by an update.

## Backup
- **Full export / import** (.zip) of your data.
- Schedulable **automatic backups**.
- 5-minute **trash**, operations journal with undo.
- Updates never lose data.

## Logs and diagnostics
- The default log level is **warning**; the `stellio.log` file is recreated at every start.
- **Debug mode**: turn it on in Settings; it applies at the next start.
- **Export diagnostics** (Settings → Diagnostics): secrets masked, built-in printers listed (type, model, status — no name, address or key).
- **Stellio health** block: overall state of the app.

## Suggestions and bugs
From the app: **Suggestions & bugs** in the sidebar. The message becomes a GitHub issue (anonymous, via a GitHub App), with a "New reply" badge.

@@@ Troubleshooting | Troubleshooting
# Troubleshooting

First of all: export the **diagnostics** (Settings → Diagnostics) and keep them for a report.

## The screen stays white at launch (macOS)
Port **5000** is often taken by the *AirPlay Receiver* (a 403 in Safari). Stellio now picks a free port **automatically** (5001–5030). Otherwise: System Settings → General → AirDrop & Handoff → turn off *AirPlay Receiver*. Log: `~/.stellio/stellio.log` (empty at the normal level: turn on debug mode).

## The LXC container becomes unreachable
From the Proxmox shell:
1. `pct status <CTID>`, then `pct start <CTID>` if it is stopped.
2. `pvesm status`: **storage full**? This is the most frequent cause when the storage is shared.
3. `pct exec <CTID> -- free -m` and `dmesg -T | grep -i "oom\|killed process"`: out of memory.
4. `pct exec <CTID> -- ip -4 a`: did the DHCP IP change? Reserve it on the router.
5. `pct exec <CTID> -- systemctl status stellio` and `journalctl -u stellio -n 100`.

Since 1.0.7, the automatic watchdog handles the common cases; see `journalctl -t stellio-watchdog`.

## Thumbnails are slow or missing
- Choose *Settings → Thumbnail performance*: **Eco** on a small machine.
- Very heavy files keep a placeholder thumbnail after a timeout.
- Generation pauses while you use the app: this is normal.

## My printer is not detected
- Check that it is on the same network (VLAN, guest Wi-Fi).
- Add it by hand with its IP address and key.
- Bambu Lab: enable LAN mode; Klipper: the Moonraker API must be reachable.

## The end-of-print photo is missing
Turn on the *End-of-print photo* checkbox on the printer (like AI watch and smart plug) and check that the camera responds.

## "Missing module"
On the first launch of each version, Stellio downloads missing modules. Check your internet connection; do not set `STELLIO_NO_AUTO_INSTALL` unless needed.

## Windows SmartScreen / macOS blocks the app
The installers are not signed. Check the `.sha256`, then *More info → Run anyway* (Windows) or right-click → *Open* (macOS).

## Getting help
[GitHub Issues](https://github.com/stellio-app/stellio/issues), [Discord](https://discord.gg/ySxpHvS6bd), or **Suggestions & bugs** in the app. Include: Stellio version, system, steps to reproduce, exported log.

@@@ Contributing | Contributing
# Contributing

Contributions are welcome. 🎉

1. **Fork** the repository.
2. Create your branch: `git checkout -b feature/MyFeature`.
3. Commit: `git commit -m "Add MyFeature"`.
4. Push: `git push origin feature/MyFeature`.
5. Open a **Pull Request**.

Rules: follow the existing style, comment in French or English, test on Windows if possible, update the documentation. Every new UI string must be added to **all 8 language files**.

## Technologies
| Component | Technology |
|---|---|
| Backend | Python 3.8+, Flask, Waitress |
| Frontend | HTML5, CSS3, vanilla JavaScript (no build step) |
| Database | SQLite (WAL mode) |
| Desktop | pywebview (Windows, macOS) / browser (server) |
| 3D | PyRender, numpy CPU rasterizer, Three.js |
| Mesh | trimesh, pymeshfix, shapely, rectpack |
| AI | Ollama (local) |
| Network | paho-mqtt, smbclient, requests |
| Encryption | cryptography (AES) |

## Repository structure
```
stellio/
├── main.py            Flask core: database, auth, library, printers, AI, startup
├── modules/           Functions split out of main.py (print_session, timelapse, quote_portal…)
├── interface/         index.html, script.js, style.css, management.js (vanilla JavaScript)
├── packaging/         launcher.py, Windows installer (.iss), macOS entitlements
├── languages/         Translations (8 languages) and changelog.json
├── tests/  tools/     pytest tests, maintenance tools
├── release-notes/     notes_version_X.Y.Z.txt
├── install-pi.sh      Raspberry Pi / Linux install
└── stellio-lxc.sh     Proxmox LXC install
```
A module declares the `main.py` services it uses (`_REQUIRED`), its routes (`_ROUTES`) and an `init` function. Check before publishing: `python -m pytest tests -q`.

## Security and privacy
- Stellio is **local-first**: nothing is collected or sent by default. The only exception, if you enable it: the server edition's online AI.
- Code and configuration files are not reachable from the browser; the API is protected by session and CSRF; guests are read-only; secrets are encrypted.
- Every release ships with a `.sha256` checksum verified by the built-in updater.

## License
**GNU AGPL v3**: you may copy, modify and distribute Stellio; if you modify it or offer it as a network service, you must publish the source code under the same license.

## Partnership and thanks
Stellio is an official integration partner of **TigerTag** ([tigersystem.io](https://tigersystem.io)). Thanks to Ollama, Flask, Three.js, trimesh, Spoolman and the maker community. ☕ Support: [Ko-fi](https://ko-fi.com/E6J828RYVD).
