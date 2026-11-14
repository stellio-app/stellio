@@@ Home | Home
# 🧊 Stellio, your 3D workshop in one place
{{img:dashboard}}

> **Library, printers, spools, costs and quotes: everything is organised, one click away, and stays on your own machine.**

🔒 **100% local** · 🆓 **Free and open source** (AGPL v3) · 🌍 **8 languages** · 🖥️ Windows, macOS, Linux, Raspberry Pi, Proxmox · 📱 Android

**[⬇️ Download Stellio](https://github.com/stellio-app/stellio/releases)** · **[▶ Try the online demo](https://demo.stellio-app.com)** · **[💬 Join the Discord](https://discord.gg/ySxpHvS6bd)**

## ✨ Why you will love it

| For you… | What Stellio changes |
|---|---|
| 🗂️ **A library that organises itself** | Automatic 3D thumbnails, AI tags, natural-language search, duplicates spotted. |
| 🖨️ **All your printers on one screen** | Bambu Lab, Prusa, Klipper, OctoPrint, Creality… temperature, camera, progress, end-of-print photo and timelapse. |
| 🚀 **From library to machine in one click** | Send to the slicer with the right profiles and the right spool (one slicer per printer), checks before printing. |
| 🧵 **Your spools under control** | Inventory, Spoolman, TigerTag, OpenPrintTag, run-out forecast, drying reminders. |
| 💶 **Costs, quotes and orders** | Real cost (material, power, wear), PDF quotes, online customer tracking, invoices. |
| 🤖 **An AI that stays at home** | Local Ollama: tagging, search, printability, failure watch, S.O.S Print. |
| 🛠️ **Tools that save a part** | 3D viewer, mesh repair, conversion, auto-placement, suggested orientations. |
| 📱 **With you everywhere** | Phone (PWA and Android app), remote access, push notifications, Home Assistant. |

## 🚀 Get started in 3 minutes

1. **Install** Stellio: an installer, an AppImage, or one command on Raspberry Pi and Proxmox ([Installation](en-Installation)).
2. **Add a folder** with your models: Stellio sorts them and creates the 3D thumbnails by itself.
3. **Add a printer** (optional): it is detected automatically on your network.

👉 Next: [Getting started](en-Getting-Started), then the [Step-by-step guide](en-How-To) that explains **every feature and how to use it**.

## 🧭 Explore the wiki

| I want to… | Page |
|---|---|
| Learn how to use every feature | [Step-by-step guide](en-How-To) |
| Install Stellio | [Installation](en-Installation) |
| Take my first steps | [Getting started](en-Getting-Started) |
| Manage my 3D files | [Library](en-Library) |
| Connect my printers | [Printers](en-Printers) |
| Track my spools | [Filament](en-Filament) |
| Download models | [Downloads](en-Downloads) |
| Use AI and S.O.S Print | [Artificial intelligence](en-AI) |
| Work out costs, quotes, invoices | [Costs and management](en-Costs-and-Management) |
| Reach it from my phone | [Remote access and mobile](en-Remote-Access) |
| Install on Raspberry Pi / Proxmox | [Server edition](en-Server-Edition) |
| Configure, back up, understand my data | [Settings and data](en-Settings-and-Data) |
| Fix a problem | [Troubleshooting](en-Troubleshooting) |
| Contribute to the project | [Contributing](en-Contributing) |
| See what each version brings | [What's new](en-Changelog) |

> 🔒 **Philosophy**: your data stays with you. Everything works locally; by default, nothing leaves your machine.

## Useful links

- 🌐 Website: [stellio-app.com](https://stellio-app.com) · ▶ [online demo (read-only)](https://demo.stellio-app.com)
- 📦 [Downloads (Releases)](https://github.com/stellio-app/stellio/releases)
- 🐛 [Report a bug](https://github.com/stellio-app/stellio/issues) · 💡 [Suggest an idea](https://github.com/stellio-app/stellio/discussions) · 💬 [Discord](https://discord.gg/ySxpHvS6bd)
- 📜 **AGPL v3** licence

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

@@@ How-To | Step-by-step guide
# Step-by-step guide

Every Stellio feature, **what it is for and how to use it**. Technical details are on the other pages; here, we do.

> 💡 Everywhere in the app: `Ctrl+K` opens the **command palette** (go somewhere, run an action, find a file, a tag, a spool) and `?` shows the shortcuts.

## Finding your way around Stellio

| Menu | What it is for |
|---|---|
| **Dashboard** | Running prints, low stock, recent files; rearrangeable widgets. |
| **Library** | All your 3D models, with thumbnails, tags, filters and search. |
| **Favorites** | Your favourite models, one click away. |
| **Print soon** | Your print waiting list, reorderable. |
| **Projects** | Several files grouped for one object. |
| **Printers** | Live monitoring, sending, maintenance, wear parts. |
| **Filament inventory** | Your spools, the run-out forecast, drying. |
| **History** | Every print sent, rated success or failure. |
| **Gallery** | The photos of your prints. |
| **Statistics** | Reliability, consumption, formats, reports. |
| **Management** | Costs, customer quotes, orders, accounting. |
| **Workshop mode** | Full-screen display for tablet or phone. |
| **S.O.S Print** | Guided diagnosis of a failed print. |
| **Download** | Fetch models from Printables, MakerWorld, Thingiverse… |
| **Repair** | Find and repair damaged meshes. |
| **Converter** | Switch from one 3D format to another. |
| **Duplicates** | Spot duplicate files. |
| **Trash** | Restore what you deleted. |
| **Settings** | Appearance, slicer, AI, backups, remote access. |

## Add and find my files

1. Click **Add a source** (or `Ctrl+K` then "Add a source") and choose a **folder**, a single file or an **SMB / NFS** share. The 3D folders found on your computer are suggested.
2. Stellio scans and creates the **3D thumbnails** in the background; generation pauses while you use the app.
3. To find a model: type in the **search** bar, or describe it in plain language ("a headphone stand") with AI search.
4. Drag and drop 3D files from your file explorer to add them directly.

💡 Archives (ZIP, RAR, 7z, TAR) can be browsed without extracting them.

## Organise with tags, favorites and filters

1. Open a file's **⋯** menu, or select several (`Shift+click` for a range) to act in bulk.
2. Add coloured **tags** by hand, or let the AI suggest them; `T` opens the tag manager.
3. Click the star to make a model a **favorite** (`F` opens favorites).
4. Combine **filters** (type, size, weight, print status, "Filament stock") then **save** the filter to reuse it.
5. To rename many files: **Bulk rename** (find/replace, prefix, suffix, numbering), with a preview before you confirm.

## View and prepare a model in 3D

1. Click a file's thumbnail: the **3D viewer** opens (it works offline).
2. Rotate and zoom; for a multi-plate 3MF, switch between plates.
3. Run the **printability analysis** (overhangs): Stellio suggests recommended **orientations**.
4. Use **auto-placement** to arrange several parts on your printer's bed.
5. Send the result to the slicer from the viewer.

## Repair a damaged mesh

1. Open **Repair**: Stellio lists files with holes or open edges (the analysis also runs in the background when thumbnails are created).
2. Pick a file and start the **repair**; compare **before / after**.
3. The file is repaired in place; a `.bak` safety copy is kept just in case.

## Convert files

1. Open **Converter** and choose one or more files (STL, 3MF, OBJ, PLY, AMF, STEP).
2. Select the output format: STL, 3MF, OBJ, PLY, OFF or GLB.
3. If needed, tick **Automatically repair the mesh** and **Delete the original file**.
4. Start. A batch conversion can be cancelled at any time: files already converted are kept.

## Tidy up: duplicates and trash

1. Open **Duplicates**: identical files, and those with **similar geometry** (same model renamed or re-exported), are grouped.
2. Keep the one you want and delete the others.
3. Deleted by mistake? `Ctrl+Z` undoes it for 5 minutes; the **Trash** keeps items longer and lets you restore them or delete them permanently.

## Group files into projects

1. Open **Projects** and create a project; add the files of one object (body, lid, supports…).
2. A **multi-plate** 3MF added to a project is split into one 3MF per plate (also available: **Split plates**, in the ⋯ menu).
3. Track progress ("In progress" / "Done") and click **Project cost** to price the whole set.

## Download models

1. Open **Download** (or `Ctrl+N`) and paste a model link (Printables, MakerWorld, Thingiverse, Nexprint, Creality Cloud, Snapmaker Space).
2. Connect the requested account once (see [Downloads](en-Downloads)).
3. Pick the destination **source**: the file arrives with its **origin** (link, author, licence).
4. Stellio checks every day whether a **new version** of the model exists; **My likes** and **My creations** find your models on connected accounts.

## Connect a printer

1. Open **Printers → Add**: **network detection** suggests the machines it finds; otherwise enter type, address and access key.
2. Enter the **print volume** (X, Y, Z): Stellio warns you before sending if a part is too big.
3. If you like, choose the **slicer for this printer** (1.0.8): that is the one that opens for this machine.
4. Turn on the useful options: **timelapse**, **end-of-print photo**, **AI watch**, **smart plug** (real consumption).

## Send a file to the slicer

1. From the library or the viewer, click **Send to slicer**.
2. In the window: look at the **estimate** (weight, time), choose the **printer**, the **spool** and the **settings profile**, or leave "Automatic".
3. Read the **pre-print checks**: spool to dry, abrasive filament, volume exceeded, not enough material.
4. Click **Send**: the file opens in the printer's slicer (or the one from Settings), with the profiles linked to the machine. The spool is deducted if you asked for it.

💡 To link profiles to a printer, import them from Settings → Slicer.

## Prepare what comes next: "Print soon"

1. In a file's **⋯** menu, choose **Add to print soon**.
2. Open **Print soon**: drag to **reorder**.
3. Send an item straight to the slicer or remove it from the list.

## Follow a print

1. On the printer card: temperature, progress, **live camera** and the name of the current file.
2. A **floating widget** shows progress on every page.
3. The **bell** warns you (finished, failed, maintenance, low stock); turn on **push notifications** (ntfy, Telegram, Discord, webhook) to be told with the window closed.
4. At 100%, Stellio takes the **end photo**: mark it *Success* or *Failure* in one click. The **timelapse** is assembled automatically.

## Rate, reprint, find your photos

1. Open **History**: filter by platform, result or dates.
2. Rate each print **success** or **failure**: this feeds recommendations and statistics.
3. **View the file** or **Reprint** as last time (same settings).
4. Find your photos in the **Gallery**; **My G-codes** keeps the G-codes linked to a file with the **Open in slicer** button.

## Track my spools

1. Open **Filament inventory**: add spools by hand (or import Excel/CSV), link **Spoolman**, **TigerTag** or **OpenPrintTag**, or look a spool up in the **Open Filament Database**.
2. When sending to the slicer, pick the spool: Stellio **deducts** the consumption and checks that enough is left.
3. In **Weighing and forecast**, weigh a spool: Stellio estimates its **run-out date** and warns you as it gets close.
4. Log a spool's **drying** to track its state; use **Rebuy** to open the maker's shop.

## Work out a cost and make a quote

1. Open the calculator from a file (**Cost**) or a project (**Project cost**).
2. Check material, power, **machine wear**, **fixed fees**, **margin** and **quantity**: unit price and total are shown.
3. Click **Generate the quote (PDF)**: fill in the customer and description. The PDF is kept and found in the **Quotes** widget.
4. Set the default margin in **Settings → Print pricing**.

## Manage orders, customers and invoices

1. Turn on *Enable cost, quote and invoicing features* in Settings: the **Management** screen appears.
2. Send a quote to the customer with its **tracking link**: they can accept or decline online; acceptance creates the print task. **Stellio processes no payment.**
3. Follow the **order queue**, payments, deposit invoices and credit notes; **smart dispatch** suggests the right printer without ever starting a print.
4. Every month, export the **accounting** (ZIP with CSV and PDF).

## Maintain my printers

1. On a printer card, open **Maintenance** and choose the **brand**: recommended tasks are offered.
2. Add them to your tracking: they turn "due" according to print hours and days elapsed.
3. Record your **wear parts** (nozzles, plates, belts) with an alert threshold, and your **calibrations** per filament.

## Diagnose a failure: S.O.S Print and AI

1. Open **S.O.S Print** and describe the problem (photo possible).
2. Answer the questions, one at a time (4 at most): Stellio narrows the hypotheses and gives a **final diagnosis**.
3. For local AI, install [Ollama](https://ollama.com/) then set it up in **Settings → Artificial intelligence**. **Failure watch** alerts you without ever stopping the print.

## Use Stellio on a phone and remotely

1. In **Settings → Mobile access**, scan the **QR code**: the library opens on your phone (installable like an app).
2. For the **Android** app, scan the dedicated QR code.
3. Away from home: turn on **remote access** (Cloudflare Tunnel or custom address), or create a temporary **share link**.
4. Share read-only with a **guest account**.

## Back up and restore

1. Open **Settings → Backup and data** and **export** your data (.zip).
2. Schedule **automatic backups**.
3. To restore, **import** the .zip file. A Stellio update never touches your data.

## Shortcuts worth knowing

| Shortcut | Action |
|---|---|
| `Ctrl+K` | Command palette |
| `Ctrl+N` | New download |
| `Ctrl+Z` | Undo the last deletion |
| `F` · `T` | Favorites · tag manager |
| `?` | Shortcut help |

Full list: [Settings and data](en-Settings-and-Data).

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
- **Green / red halo** around the thumbnail: green for a file already printed successfully, red for a failed print (gallery and details views).
- **Already printed** (⋯ menu of a file): record by hand a print made elsewhere — pick the printer, the settings (slicer profile) and the spool, then **Success** or **Failed**. The file joins the “Printed OK” / “Failed” filters and its details sheet (right-click) shows the printer, settings and spool.
- Fast selection: `Shift+click` for a range, arrows + `Enter`.
- **Duplicate detection** (exact and similar geometry).
- **Model origin**: source link, author, license, notes, download date.
- **Drag and drop** 3D files from your file explorer, also through a browser.

{{img:library-halo}}

{{img:already-printed}}

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
- **Slicer per printer**: each printer can have its own default slicer (OrcaSlicer, QIDIStudio, Bambu Studio…). Sending uses it with the profiles (settings, filament) attached to that printer, and the profile list adapts.

{{img:printer-slicer}}

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
- **Android app update**: on launch, a dialog announces the new version published on GitHub and offers to download and install it in one tap (checksum verified).
- Full-screen **workshop mode** for tablet/phone.

{{img:android-update}}

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
