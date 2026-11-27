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

> 💡 If the built-in window cannot open (WebView2 or `Python.Runtime.dll` blocked, often after a download), Stellio opens in a separate Edge/Chrome window and stops when you close it. To get the built-in window back: right-click the zip → Properties → **Unblock**, then extract again. Details are in `data\stellio.log`.

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

The left bar is an icon **rail**; clicking a category opens its **panel** on the right, which closes after your choice.

{{img:sidebar-panel}}


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

## Navigation
The left bar is a **narrow rail**: Home, Library, Printing, Filament, Tools and Tracking. Click a category to open its **panel**; it closes after you choose. The notification badges of a category's pages are **added up** on its icon. At the bottom: Workshop mode, Help, **Updates** and Settings. **Projects** and **Already printed** are in Printing.

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

## Scale a model to life size (BigPrint)
BigPrint (**Tools** menu) scales a model to the size you want — 1.8 m or more — and cuts it into pieces that fit your print bed: hollowed pieces, assembly dowels and a number engraved on every piece. The calculation is done by the open-source [bigprint](https://github.com/PooterTF/bigprint) engine (AGPL-3.0, by Michael Christopher Stone), built into Stellio.

{{img:bigprint}}

1. Choose the model: **Pick from library**, **Import a file**, or the **Send to BigPrint** button in a file's **Actions** menu (STL, 3MF, OBJ, PLY).
2. Enter the **final size** (height, width, depth or scale factor) and your **printer** (preset list or custom dimensions).
3. Set the **strength** (purpose, material, hollowing, shell thickness) and the **dowels**; advanced options (up axis, margin, smoothing…) are folded away.
4. Click **Preview**: Stellio shows the pieces in an exploded view, the filament weight, the estimated cost and the list of pieces. A calculation can be cancelled at any time.

{{img:bigprint-result}}

Choose where to save (library source, subfolder, folder creation available, network shares included), then **Save print files**: STL pieces, 3MF project, dowels, report and preview are copied to the `<model>_bigprint` folder.

If you change a setting after the preview, run it again before saving.

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
3. The **bell** warns you (finished, failed, maintenance, low stock); turn on **push notifications** (ntfy, Gotify, Pushover, Telegram, Discord, Slack, webhook) to be told with the window closed.
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

## Plan production (schedule and capacity)
The **Planning** page (**Printing** menu) works out, for each printer, the estimated end date of every order, compares available capacity with the requested load and warns you about an overload or a delay before it happens.

{{img:planning}}

1. In **Orders**, enter the **time per piece** (in hours) for each order: an order created from a quote takes it from the costing. An order without a time is not scheduled and stays flagged at the top of the page (you can fill it in right there).
2. Pick the **printer** for each order (otherwise Stellio places it, as a suggestion, on the machine that frees up first) and its **delivery date**.
3. Open **Planning**: bars show how orders follow one another on each printer (red = delay expected, orange = less than a day of margin), with each machine's **load rate**. The print in progress is taken into account through the remaining time read from the printer.
4. Set the **horizon** (7, 14 or 30 days). The cards at the top summarise capacity, load, expected delays and **on-time delivery** over 90 days.

**Printer capacity**: enter the possible printing hours per day and the working days (default 16 h, every day), machine by machine; untick a printer to leave it out of the schedule.

Stellio sends a notification when an order is about to miss its delivery date or a printer is overloaded (once per order and per day).

The calculation is deliberately simple: the times you enter, orders chained by delivery date, with no allowance for material changes or breakdowns.

## Find the best combination (traceability)
The **Traceability** page (**Printing** menu) links every print to the **exact model version** and the **slicer profile** used, then shows, for each model, the combination that works best.

{{img:trace}}

1. Print as usual from Stellio: the print is linked to the model automatically. If the file changed since the last version, Stellio saves a “Before print” version, so the link is always exact.
2. After printing, **rate the result** (success, failure, partial) in the history: these ratings feed the rates.
3. Open **Traceability**: one row per model with its versions and its **best combination** (version + profile, successes over rated prints). One click opens **Model versions**.
4. In **Model versions**, each version shows its successes, failures and rate, and the table crosses **version × profile**.

{{img:trace_versions}}

The ranking is not fooled by small samples: 8 successes out of 9 rank ahead of 1 out of 1. A best combination is only suggested from 2 rated prints and a known version.

Tracking starts with v1.1.6: older prints are not reconstructed.

## Maintain my printers

1. On a printer card, open **Maintenance** and choose the **brand**: recommended tasks are offered.
2. Add them to your tracking: they turn "due" according to print hours and days elapsed.
3. Record your **wear parts** (nozzles, plates, belts) with an alert threshold, and your **calibrations** per filament.

## Diagnose a failure: S.O.S Print and AI

1. Open **S.O.S Print** and describe the problem (photo possible).
2. Answer the questions, one at a time, with **no limit**: Stellio narrows the hypotheses (and adds new ones when needed) until it finds the cause, then gives a **final diagnosis**. If the fix does not work, answer “still not solved” and the investigation continues.
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
- **Favorites**, advanced filters (type, size, weight, print status), **saved filters**. Access: **F** key, dashboard widget or each file's star (removing a star makes the file disappear from the Favorites view immediately).
- Status filters: "Sent to slicer", "Already printed", "Already succeeded", "Already failed".
- **"Filament stock" filter**: keeps only files printable with the spools you own.
- Sort, search and filters are **remembered** when you reopen the app.
- **"Print soon" queue**, reorderable, sendable to the slicer.
- **Bulk rename** (find/replace, prefix, suffix, numbering) with a preview.
- **Undo deletions** (`Ctrl+Z`) thanks to a 5-minute temporary trash; also works for tags, projects and sources.
- **Green / red halo** around the thumbnail: green for a file already printed successfully, red for a failed print (gallery and details views).
- **Already printed** (⋯ menu of a file): record by hand a print made elsewhere — pick the printer, the settings (slicer profile) and the spool, then **Success** or **Failed**. The file joins the “Printed OK” / “Failed” filters and its details sheet (right-click) shows the printer, settings and spool. With **Failed**, an optional **Failure reason** field is saved with the print (1.1.9).
- **“Already printed” page** (Printing panel): every file you printed or marked “already printed”, with the same thumbnails and halos as the library, a search and a Successful / Failed filter. A **red cross** appears when you hover a thumbnail (on a phone: one tap shows it, a second tap opens the file); after a confirmation it removes the file from the list and it becomes “never printed” again. The **Remove** button in the file info does the same. A widget of the same name is available on the home page.
- Fast selection: `Shift+click` for a range, arrows + `Enter`.
- **Duplicate detection** (exact and similar geometry).
- **Model origin**: source link, author, license, notes, download date.
- **Drag and drop** 3D files from your file explorer, also through a browser.

{{img:library-halo}}

{{img:already-printed}}

For a **multi-plate** 3MF, the “Already printed” window offers one area per plate, each with its own spool; a **multicolor** file accepts several colors per plate (**Add a color**). The color dots match your spools, and the file info shows the details.

{{img:already-printed-plates}}

Files **sent to the slicer** get an **amber halo** (green if the print succeeded, red if it failed) as soon as they are sent, and the **Sent to slicer** chip in the library finds them in one click.

- **Collections**: group models by theme (file menu → *Add to a collection*). Each collection becomes a filter chip in the library; set a **quantity** per file and **add the whole collection to the print queue** in one click.
- **Model versions**: file menu → *Versions*. Save a copy before editing a model, **compare** it with the current file (size, triangles, dimensions, volume), download or **restore** it (the current state is saved first).

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
- **BigPrint** (**Tools** menu): scales a model to the size you want and cuts it into numbered pieces with dowels, an exploded 3D preview and a filament and cost estimate (open-source bigprint engine).
- **Merge into 3MF**: select several models (STL, 3MF, OBJ…) and Stellio builds a single 3MF file — one plate if everything fits, otherwise a multi-plate file (structure compatible with Bambu Studio / OrcaSlicer; PrusaSlicer shows all parts together). You choose the file name and folder (network shares included, folder creation possible), then Stellio offers to delete or keep the original files.
- **Spool colour sent to the slicer**: when sending, the colour and material of the chosen spool are applied to the filament profile loaded in OrcaSlicer, Bambu Studio or PrusaSlicer (an imported filament profile linked to the printer is required; in a batch send, the colour is applied only if all spools are identical).
- **Selection bar**: all buttons have the same size and fit on a single line (icons only on small screens, name in the tooltip).
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

## Large models
An STL takes about 12 times its size in memory when loaded. Beyond a threshold (256 MB, up to 1 GB if the computer has plenty of free memory), Stellio no longer loads it entirely: streamed analysis (binary and text STL), thumbnail and viewer on a **simplified version** (about 300,000 triangles), write operations (repair, conversion…) refused with a clear message.
To work on it anyway: right-click › **Create a lightweight version**. Stellio writes a simplified copy next to the original (`name (lightweight).stl`), which is never modified. The copy is for viewing, measuring, repairing or indexing, not for printing at full resolution. The action is also offered when a repair is refused because of size; it only applies to local STL files. A slicer export (OrcaSlicer…) as STL or 3MF is often much lighter.
In the Advanced Workshop, every "Model path" field offers **Choose from the library**: source, search, format filter (STL, 3MF…), thumbnails and pagination.

@@@ Printers | Printers
# Printers
{{img:printers}}

On the home page, the **Cameras** widget shows up to **4 cameras** (one per running printer): clicking a thumbnail opens a window with **the camera only** (the “Running prints” widget keeps the full tracking). The **See all** button opens the list of all cameras so you can pick the one to display.


## Supported brands

| Brand | Models | Connection |
|---|---|---|
| **Bambu Lab** | X1/X1C/X1E, X2D, P1P/P1S, P2S, A1/A1 mini, H2D/H2S/H2C | MQTT (LAN + cloud): monitoring, AMS, camera, SSDP discovery |
| **Prusa** | MK4, MK3.9, MK3.5, MINI+, XL, CORE One | PrusaLink (HTTP) |
| **Creality** | K1/K2 series, Ender-3 V3, Hi | WebSocket: monitoring, CFS, UDP discovery |
| **Elegoo** | Centauri Carbon 1 & 2, Saturn/Mars resin series | SDCP (WebSocket) |
| **Chitubox resin** | Phrozen, Uniformation GKtwo and other Chitubox boards | SDCP v3: monitoring (same protocol as Elegoo) |
| **USB printer** | Marlin, Prusa, Creality, Klipper boards… plugged into the Stellio PC | Serial port detection (the port is never opened): plugged in / absent, no status or temperatures |
| **Anycubic Photon** | Older Wi-Fi models: Mono X, Mono X 6K, Mono SQ (not the M5s / M7) | TCP 6000 text commands: state and current file only |
| **Formlabs** | Form 3 / 3L / 4 | Official web API (client_id:client_secret): status, progress, layers; sending is done with PreForm |
| **FlashForge** | Adventurer 5M/5M Pro, AD5X | Proprietary API |
| **Klipper / Moonraker** | Any Klipper machine (Voron…) | HTTP: monitoring, upload, camera, exact hours |
| **OctoPrint** | Any printer driven by OctoPrint | HTTP |
| **Duet / RepRapFirmware** | Duet 2/3, standalone or SBC (DSF) | HTTP: status, file upload, temperatures |
| **Repetier-Server** | Any printer managed by Repetier-Server | HTTP: status, file upload, temperatures (Marlin over USB serial is not supported) |

> **Resin printers: monitoring only.** Stellio never starts or stops a resin print. Please report anything that does not work on GitHub (Creality Halot: not supported yet).

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
- **Resin software**: Stellio detects CHITUBOX, CHITUBOX Pro, Anycubic Photon Workshop, PreForm (Formlabs), Voxeldance Tango and Lychee Slicer. A resin printer with no slicer chosen automatically opens the first resin software detected; you can also pick one by hand (Settings → Slicer, or the printer's form). Common install locations are checked: if your software is not recognised, select it by hand.

{{img:printer-slicer}}

**Produce with assistance (1.1.8).** In a file's menu, **Produce with assistance** proposes the most suitable printer (free, right material, short queue) and the slicer profile recommended by Intelligence, then checks the file (raw model to slice, format not matching the printer), the printer (offline, busy) and the consumables (enough filament or resin). **Nothing is sent without your validation**: the server refuses to send until you have clicked *Validate this choice*. Stellio then sends the file to the printer **without starting the print remotely** (you start it on the machine). It detects the end of the print and records it in the history; if the machine does not report it, enter the result yourself. **Followed** recommendations and their outcome correct Intelligence's ranking: a profile followed at least 3 times that succeeds less than 40 % of the time is demoted, from 80 % it is favoured (*Assisted production* card on the Statistics page).

## During the print
- **Smart plug** (Shelly, Tasmota, Home Assistant): Stellio reads the watts and records real consumption (kWh) and cost.
- **Real filament consumption** recorded after the print.
- **End-of-print photo** taken when the print reaches **100%** (the part is still on the bed), a single photo to rate *Success/Failed*.
- **AI failure watch** (Ollama with vision, 100% local): alert on spaghetti or a detached part, **never an automatic stop**.
- Automatic **timelapse** (camera → MP4 video, needs ffmpeg).
- Read-only **status share links**.

## Camera failure detection (Obico)
In *Settings → Obico*, enter the address of your Obico server (self-hosted or obico.io) and an API token. Stellio regularly checks for alerts and sends you a **push notification** as soon as Obico detects a failure. The action (pause, cancel) stays Obico's: Stellio never stops a print by itself. A *Test the connection* button checks the address and token.

## Maintenance
- **Resin maintenance**: the **Maintenance** button on resin printer cards offers suitable tasks (FEP/nFEP film, resin filtering, build plate, LCD screen, carbon filter, Z axis, wash IPA, UV/LCD wear).
- **Predictive maintenance** with brand-specific tasks.
- **Wear parts** (nozzles, plates, belts…) with stock alerts, linked to maintenance tasks.
- **Calibrations** (flow, pressure advance, temperatures) per filament and printer.

@@@ Filament | Filament
# Filament

## Resin
The sidebar category is now called **Materials** and holds two pages: **Filament** (spool inventory) and **Resin**. The resin inventory is **manual**: add your bottles (name, brand, type, colour, volume, remaining, price, storage place, notes) and use the “Use” button to remove a volume in ml. Since 1.1.8, **Automatic consumption** (bottom of the Resin page): choose the **active bottle** of each resin printer; when a print ends, Stellio removes the resin used from that bottle. The volume is read from the `.sl1` file (`usedMaterial` field); otherwise it is **estimated** from the model of the same name in your library (closed-mesh volume + 15 % margin for supports and losses) and flagged as an estimate; if nothing reliable exists, **nothing is deducted** and a notification says so. A failed print only removes the part already printed (when progress is known). Every deduction appears in the history and can be **undone**; the remaining volume never goes below zero.

As with filament, the **“To order”** reminder also works for resin: a resin (brand + name + colour, all bottles combined) is listed when its total remaining volume falls below the threshold set on the page (200 ml by default, 0 = off) or when you tick “To order” on a bottle. It also appears in the dashboard “To order” widget; **Order** opens search links to your shops (stock is not checked automatically for resin) and **Already ordered** postpones the reminder by 14 days.

## Inventory sources
| Source | Details |
|---|---|
| **Spoolman** | Automatic detection on the network. Stellio **no longer writes** consumption to it (avoids double counting). |
| **Manual** | Hand-entered spools, Excel/CSV import. |
| **TigerTag** | NFC/RFID identification. Sign in with email and password (only an encrypted token is kept) or reuse a TigerTag Studio session. **Read-only.** |
| **OpenPrintTag** | Open NFC tag standard: import/export `.bin` files, read/write from the Android app, consumed weight kept up to date. |
| **Bambu AMS / Creality CFS** | Slot reading. |

**Open Filament Database**: search a spool by brand, material and color, then create it in one click (weight, diameter and density prefilled).

In the send-to-slicer window, the spool list is sorted and has a **search field**.

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

The **Open Filament Database shops** (86) are added to **Useful links**, filtered by your country, and also used by the **Rebuy a spool** search: Stellio suggests the shops that ship to you.

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

> ⚠️ The AI is not 100% reliable: it can make mistakes (tags, descriptions, S.O.S Print diagnoses…). Treat its answers as leads to check, not as certainties.

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
1. You describe the problem (a photo is possible at every step) and, if you want, the settings used (temperatures, speeds, retraction…). **Speeds** are read from the chosen slicer profile (or typed by you); if they are missing, the AI asks for them. For **multicolor** prints the AI looks at the **purge tower** (detaching, collapsing, falling onto the part, mixed colors) and asks the relevant questions; the tower width is read from the profile. From the first step and after every answer, the AI shows its **hypotheses ranked by likelihood** (%), each with its reason or a quick check.
2. Stellio asks **one question at a time**, with no limit, and narrows a live list of hypotheses (new ones are added when the first are ruled out).
3. It gives a **final diagnosis**.

From **question 3**, the **Conclude and suggest a fix** button gives the most likely causes, then asks “Did this diagnostic solve the problem?” (**Yes, it's solved** / **No, continue the investigation**). The **Stop the investigation** button lets you abandon it at any time.

Conversations are saved: reopen them or mark them as resolved.

> ℹ️ The "Success / Failed" results you rate in the history improve the recommendations.

@@@ Costs-and-Management | Costs and management

> ⚠️ The AI is not 100% reliable: it can make mistakes. Its hypotheses are leads to check, not certainties; verify before changing your settings or your machine.

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
- **Off-peak / peak hours**: in *Settings → Electricity*, enter two per-kWh prices and your off-peak ranges (e.g. `22:00-06:00`, weekends optional). The **real cost** of measured prints takes them into account, a 30-day summary shows the **possible saving**, a simulator compares "now" with "next off-peak slot", and a reminder tells you when off-peak starts with jobs waiting. Stellio never starts a print by itself.
- **Why my prints fail**: in *Statistics*, failure rate by reason, material, printer, slicer profile, weekday and time of day, most failing files, and data-driven leads (e.g. "PETG: 45% failures versus 12% on average"). Rate your prints in the history to feed it.



{{img:stats}}
@@@ Remote-Access | Remote and mobile access
# Remote and mobile access

## Phone and tablet
- **QR code** for mobile access to the library (**installable PWA**).
- **Android companion app**: a dedicated QR code (Settings → mobile access) downloads the APK. It handles internal and external addresses with automatic switching, QR pairing, photos straight from a print, and reading/writing OpenPrintTag NFC tags.
- **Android app update**: on launch, a dialog announces the new version published on GitHub and offers to download and install it in one tap (checksum verified).
- **Updates over the existing app**: since 1.1.0 the APK is signed with a permanent key. If Android shows “package conflicts with an existing package”, uninstall the old version once and install the new one; later updates install normally.
- Full-screen **workshop mode** for tablet/phone. The printer card (1.1.9) puts the camera on the left and the details on the right on PC / server, with no scrolling; on a phone, progress comes before temperatures. In workshop mode, tapping a printer that is printing opens its card.

{{img:android-update}}

**Small-screen menu**: the bottom bar is gone; a button at the top left opens the same sidebar as on desktop (categories + panel on the right). Badges (running print, notifications, banners) shrink so they stay out of the way. The Stellio logo appears on the setup and “Server unreachable” pages.

{{img:mobile-drawer}}

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
- **Push**: ntfy, Gotify, Pushover, Telegram, Discord, Slack or webhook, even with the window closed (print finished with file name and duration, failure, maintenance, stock, printer offline).

## Home automation
- **MQTT / Home Assistant**: state publishing and automatic discovery; "Stellio" MQTT device and sensors.

@@@ Desktop-Edition | Desktop edition
# Desktop edition

The **desktop edition** is the desktop app: a Stellio window on your PC (Windows, macOS). It keeps its original behavior; only a few features designed for an always-on server are absent.

## Which edition do I have?
| System | Default edition |
|---|---|
| Windows, macOS | Desktop |
| Linux, Raspberry Pi, VM, LXC, Docker | Server |

To force the choice (tests, a Linux PC used as a desktop):
```bash
STELLIO_SERVER_EDITION=0   # desktop
STELLIO_SERVER_EDITION=1   # server (STELLIO_HEADLESS=1 also leads there)
```

## What is specific to desktop
- **Built-in window** (pywebview). On Windows, opening Stellio in a browser on the same PC is blocked (internal token): use the window. Phone, APK and tunnel stay allowed.
- Native **Windows notifications**.
- **PC slicers** detected automatically (OrcaSlicer, Bambu Studio, PrusaSlicer, Cura…).
- **Sources**: local folder, file, SMB and NFS.
- **Data** in `%APPDATA%\Stellio` on Windows; in the portable version, in the `data` folder next to `Stellio.exe`.
- **Updates** from GitHub as a `.zip` patch, verified before installation.

## Features reserved for the server edition
These features answer “reserved for the server edition” in the desktop app:

| Feature | Purpose |
|---|---|
| Online AI | Claude, ChatGPT or Gemini with your key |
| Imported slicer profiles | Import profiles exported from your slicers |
| Push notifications | ntfy, Telegram, Discord, webhook… |
| MQTT / Home Assistant | State publishing and auto-discovery |
| Periodic digest | Daily or weekly |
| Sync between two instances | Tools › Sync |
| Outgoing webhooks | Signed messages (HMAC-SHA256) to your services |
| Public API and mobile access | Scoped tokens, /api/v1 routes |

The **Sync** entry of the Tools menu is hidden on desktop since it would only show this message.

## Advanced Workshop on desktop
Everything else works as on a server. The Advanced Workshop tools are placed in the sidebar, each in its own category: **Library** (Organization, 3D diff, Similar, Licenses, Part sheet), **Print** (Compatibility, Print check, G-code archives), **Materials** (Material needs), **Tools** (Plate, Fabrication assistant) and **Administration** (Tasks, Database, Audit log, Teams, Sessions). They are reserved for the owner account; each entry has its own switch in *Settings › Navigation items*. In **Similar**, the **Skipped files** button (1.1.9) lists the files the index could not process, with thumbnails, the cause (too big above 60 MB, empty mesh, unreadable, missing) and a fix for each (re-export or simplify the model, check the source); **Retry** indexes them again.

## Switching to the server edition
For an always-on Stellio reachable from a browser, see [Server edition](en-Server-Edition) and [Installation](en-Installation).

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

## Server-only features (1.1.7)
These features do not exist in the desktop app, where their routes answer “reserved for the server edition”:

| Feature | Purpose |
|---|---|
| Online AI | Claude, ChatGPT or Gemini with your key, instead of Ollama (see [Artificial intelligence](en-AI)) |
| Slicer profiles | Import profiles exported from your slicers |
| Push notifications | ntfy, Gotify, Pushover, Telegram, Discord, Slack or webhook, even with the window closed |
| MQTT / Home Assistant | State publishing and auto-discovery |
| Periodic digest | Daily or weekly, as a notification and push |
| Sync (Advanced Workshop) | Syncs a folder with one on a paired instance: plan first, confirmed apply second, no deletion propagated, both versions kept on conflict. Both instances must be in server edition |

The rest of the tools (plate, print check, G-code archives…) work identically on both editions.

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
- **Brand themes**: Stellio, Bambu, Prusa, Voron, Creality; 33 palettes, custom accent color, adjustable background image. A Stellio image is offered by default (**Default image** button).
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

@@@ Plugins | Plugins
# Plugins

A plugin is a small Python program that reacts to a Stellio event (print finished, print failed, order late, printer overload): send a notification, write to a spreadsheet, switch on a lamp… Plugins are published by their authors on **GitHub**; Stellio shows a **public catalog** (logo + description) in the **Plugins › Catalog** menu, where you install them in one click.

Each plugin carries a badge: **Official** if it is hosted on the `stellio-app/stellio-plugins` repository, **Community** if it is hosted elsewhere (or installed from a .zip). Stellio decides the badge from the real address of the archive: always read the permissions and the code of a community plugin.

**Plugin security (1.1.8).** Before any installation, Stellio **audits the code** (static analysis: undeclared network use, process launching, dynamic code, binaries…); a blocking finding refuses the installation unless you explicitly accept the risk. The catalog and plugins can be **signed (Ed25519)**: as soon as a trusted key is configured, an invalid signature is refused, as is an unsigned official plugin and an unsigned update of a signed plugin (with no key configured only the SHA-256 sum protects, and the Plugins page says so). On **Linux** the kernel also restricts each plugin: read-only files (writing only in its `data/` folder) and no network without the `network` permission; **on Windows and macOS these restrictions are not applied**: permissions stay declarative. A signature proves origin, not harmlessness, and an audit can miss hidden code: always read the code.

**Built-in plugins.** Some Stellio features ship as built-in plugins (BigPrint, resin, USB printers, timelapse, file tools, plate studio, push notifications, webhooks, periodic digest, MQTT / Home Assistant, Obico, sharing & sync, Spoolman, AI providers and the AI assistant, Stellio Pro). They are part of the app but only load when enabled ("Built-in plugins" section of the Plugins page; the change applies after a restart). **Updating from an earlier version: nothing to do.** On the first start of 1.1.7, the plugins you were using (for example MQTT enabled, a USB printer, webhooks, a timelapse) are enabled automatically and keep exactly their settings; tools without settings (BigPrint, file tools, plate studio) are kept as they were. A fresh install enables none of them. Disabling a plugin never deletes its settings. Other built-in plugins: Sharing & sync, Spoolman, one plugin per AI provider + the AI assistant (which enables all AI features) and **Stellio Pro** (clients, quotes, invoices, orders, accounting, energy tariff, planning, material needs, parts stock): they add their pages and buttons only when enabled.

## Using a plugin
1. Open **Plugins › Catalog** (owner account only).
2. Browse the catalog and click **Install**: Stellio downloads the archive and checks its SHA-256 checksum.
3. Read the **permissions** requested and accept them. The plugin is installed **disabled**.
4. Fill in its configuration if needed, enable it, then click **Test** to trigger it with a test event. The run log shows the output and any errors.

You can also install a local `.zip` archive (a plugin under development) or point the catalog source to another catalog URL.

## Creating a plugin
### 1. Structure
A plugin is a flat folder with a `plugin.json` file and a Python script:
```
mon-plugin/
├── plugin.json     Manifest (required)
├── main.py         Entry point (any name, set in "entry")
└── ...             Other files: 100 maximum, 8 MB unpacked
```

### 2. The plugin.json manifest
```json
{
  "id": "mon-plugin",
  "name": "Mon plugin",
  "version": "1.0.0",
  "api": 1,
  "description": "Écrit une ligne à chaque impression terminée.",
  "author": "Votre nom",
  "entry": "main.py",
  "events": ["print.finished", "print.failed"],
  "permissions": ["events"]
}
```
| Field | Purpose |
|---|---|
| `id` | Unique identifier: lowercase letters, digits, `-` or `_`, 2 to 40 characters |
| `name`, `description`, `author` | Text displayed in Stellio |
| `version` | Numeric, for example `1.2.0`; used to detect updates |
| `api` | Plugin API version: `1` |
| `entry` | Python script at the root (default `main.py`) |
| `events` | Events listened to |
| `permissions` | Rights requested |
| `ui` | Page shown inside Stellio: `title`, `icon` (Font Awesome) and `entry` (an `.html` file) |

### 3. Events and permissions
| Event | Triggered when |
|---|---|
| `print.finished` | A print finishes |
| `print.failed` | A print fails |
| `order.late` | An order passes its due date |
| `printer.overload` | A printer is overloaded |

| Permission | Effect |
|---|---|
| `events` | Receive events (required if `events` is declared) |
| `api:read` | Read data through Stellio's public API |
| `api:write` | Modify data through the public API |
| `network` | Information: the plugin accesses the Internet |
| `ui` | Show a plugin page in the Plugins menu |

### 4. The script
Stellio runs `python -I main.py <event>` in a separate process and sends a JSON `{"event": "...", "data": {...}}` on standard input. The `-I` (isolated) mode does not add the plugin folder to the Python path: to import a file from your plugin, add that path yourself. Standard output is recorded in the log.
```python
import json, os, sys

payload = json.loads(sys.stdin.read() or "{}")
event, data = payload.get("event", ""), payload.get("data", {})
config = json.loads(os.environ.get("STELLIO_PLUGIN_CONFIG") or "{}")

print(f"{event}: {data.get('file_name') or data.get('printer') or '-'}")
```
To act on Stellio (`api:*` permissions), the script receives `STELLIO_API_URL` and `STELLIO_API_TOKEN` (the `api_url` and `token` keys of the plugin configuration). The Python SDK `stellio_sdk.py` (the repository's `sdk/python` folder) provides `plugin_event()`, `plugin_config()` and a ready-to-use client: copy it into your plugin and add `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` before the import. A complete example is in `sdk/examples/hello-plugin`.

Limits: 10 seconds per run, 512 MB of memory, minimal environment (`STELLIO_*` variables only, plus `PATH`). Python 3 must be installed on the machine running Stellio. The configuration is a list of key/value pairs (text, number, boolean) of at most 4,000 characters.

### 5. Testing
Zip the **contents** of the folder as `mon-plugin.zip` (2 MB maximum), install it from **Plugins › Catalog** (local archive), accept the permissions, enable it and use **Test**. Fix problems by reading the log.

## Plugin with a page

A plugin can also show **its own page** inside Stellio. It then appears in the **Plugins** menu of the sidebar, under "Catalog", in the "Installed" list: one click opens its page. The manifest below is a minimal example.

```json
{
  "id": "mon-plugin",
  "name": "Mon plugin",
  "version": "1.0.0",
  "api": 1,
  "description": "Shows your archived G-code files layer by layer.",
  "author": "Stellio",
  "permissions": ["ui", "api:read"],
  "ui": {
    "title": "Mon plugin",
    "icon": "fa-layer-group",
    "entry": "viewer.html"
  }
}
```

- The page is **a single self-contained HTML file** (CSS and JavaScript inside, images as `data:`), 1 MB maximum. Without events, the plugin does not need a Python script.
- It is displayed in an **isolated** frame: no access to the network, cookies or the rest of Stellio.
- It reads Stellio's data with `window.stellio.api(path)`: read-only (GET), the `api:read` permission is required, the result is JSON, or text with `'text'` as second argument. Settings, accounts, security and plugins are off limits.
- The theme is provided by the CSS variables `--st-bg`, `--st-panel`, `--st-card`, `--st-text`, `--st-muted`, `--st-border`, `--st-accent`, `--st-success`, `--st-warning` and `--st-danger`, and the language by `window.stellio.lang`.

```js
document.addEventListener('stellio-ready', async () => {
  const list = await window.stellio.api('/api/gcodes?limit=50');
  const id = list.gcodes[0].id;
  const text = await window.stellio.api('/api/projects/gcodes/' + id + '/download', 'text');
});
```

To try it: zip the contents of the `mon-plugin` folder, install the archive from **Plugins › Catalog**, accept the permissions, enable it, then open it from the **Plugins** menu. At least one archived G-code is needed (file sheet or project). A disabled plugin stays greyed out in the list.

## Publishing on GitHub
1. Create a public repository for your plugin with the code, a `README` and a license.
2. For each version, create a GitHub **release** and attach the archive `mon-plugin-1.0.0.zip`.
3. Compute the archive's SHA-256 checksum, needed by the catalog:
```bash
sha256sum mon-plugin-1.0.0.zip
```
4. Always increase `version` in `plugin.json` before a new release.

## Getting listed in the Stellio catalog
The official catalog is a `catalog.json` file in the `stellio-app/stellio-plugins` repository. You add your plugin to it with a **Pull Request**.

1. Fork the `stellio-app/stellio-plugins` repository.
2. Add your plugin's entry to `catalog.json`:
```json
{
  "id": "mon-plugin",
  "name": "Mon plugin",
  "version": "1.0.0",
  "description": {"fr": "Écrit une ligne à chaque impression terminée.", "en": "Writes a line when a print finishes."},
  "author": "Votre nom",
  "url": "https://github.com/vous/mon-plugin/releases/download/v1.0.0/mon-plugin-1.0.0.zip",
  "sha256": "64 caractères hexadécimaux",
  "permissions": ["events"],
  "logo": "https://raw.githubusercontent.com/vous/mon-plugin/main/logo.png",
  "homepage": "https://github.com/vous/mon-plugin"
}
```
3. Open the Pull Request: an automatic check verifies the links, the SHA-256 checksum and the logo, then the Stellio team reviews the plugin.

| Field | Rule |
|---|---|
| `description` | Short (about 140 characters); plain text or one text per language (`fr`, `en`, `de`, `es`, `pt`, `it`, `zh`, `ja`) |
| `url` | Direct `https` link to the archive; the `sha256` must match exactly |
| `logo` | `https`, PNG, JPEG or WebP, 200 KB maximum, ideally 128 × 128 (SVG is refused) |
| `homepage` | `https` link to the plugin page (optional) |
| `permissions` | Must match those of the manifest |

**Updating**: publish a new release, then open a Pull Request that changes `version`, `url` and `sha256`. If the new version requests additional permissions, the plugin is disabled on the user's side until they accept them; its configuration is kept.

## Security
- A plugin is **not sandboxed**: it runs with Stellio's rights on the machine. Only install plugins whose author you trust.
- Plugins are installed disabled, and their permissions must be accepted.
- Downloads only go over `https` to public addresses, with SHA-256 verification.
- The catalog is reviewed before publication, but this does not replace your own vigilance: read the code and the permissions.

To go further: [Contributing](en-Contributing), the repository's `docs/plugins.md` file and the `sdk/examples/hello-plugin` example.

## Administration and supervised instances
The **Administration** plugin (on by default) groups in one page (Administration › Administration) the **guest accounts and their roles**, teams, sessions, the audit log and the **instances**.
- **Standalone instance** (default): full control, nothing changes.
- **Primary instance**: the Instances sub-tab lists the paired Stellio instances and lets you supervise them.
- **Supervised instance**: once its owner **accepts**, its accounts, roles and permissions can only be managed from the primary; local content (library, printers) stays private unless the owner chooses otherwise when accepting; the owner can **leave supervision** at any time.
A supervised instance cannot supervise others, and a primary instance cannot be supervised. All other settings remain editable locally.

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
├── release-notes/     notes.txt
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
