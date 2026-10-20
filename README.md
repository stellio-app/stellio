<p align="center">
  <img src="https://stellio-app.com/assets/logo-nom-stellio.png" alt="Stellio Logo" width="360">
</p>

<h3 align="center">The ultimate 3D file manager for makers and 3D printer owners</h3>

<p align="center">
  <a href="https://github.com/stellio-app/stellio/releases"><img src="https://img.shields.io/github/v/release/stellio-app/stellio?color=blue" alt="Version"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python"></a>
  <a href="https://flask.palletsprojects.com/"><img src="https://img.shields.io/badge/flask-3.0+-green.svg" alt="Flask"></a>
  <a href="https://www.gnu.org/licenses/agpl-3.0"><img src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg" alt="License: AGPL v3"></a>
  <a href="https://github.com/stellio-app/stellio/blob/main"><img src="https://img.shields.io/badge/platform-Windows%20%7C%20Raspberry%20Pi%20%2F%20Linux-lightgrey.svg" alt="Platform"></a>
  <a href="https://github.com/stellio-app/stellio/blob/main"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"></a>
</p>

<p align="center">
  🇬🇧 <strong>English</strong> |
  <a href="docs/readme/README.fr.md">🇫🇷 Français</a> |
  <a href="docs/readme/README.de.md">🇩🇪 Deutsch</a> |
  <a href="docs/readme/README.es.md">🇪🇸 Español</a> |
  <a href="docs/readme/README.it.md">🇮🇹 Italiano</a> |
  <a href="docs/readme/README.pt.md">🇵🇹 Português</a> |
  <a href="docs/readme/README.ja.md">🇯🇵 日本語</a> |
  <a href="docs/readme/README.zh.md">🇨🇳 中文</a>
</p>

<p align="center">
  <a href="#-installation">🚀 Installation</a> •
  <a href="#-features">✨ Features</a> •
  <a href="#-documentation">📖 Documentation</a> •
  <a href="#-contributing">🤝 Contributing</a> •
  <a href="#-license">📜 License</a>
</p>

---

## 🎯 Overview

**Stellio** is a modern desktop application that centralizes your entire 3D library (STL, 3MF, OBJ), automates repetitive tasks, and integrates seamlessly with your 3D printing workflow.

Whether you're a beginner maker or an experienced printer owner running multiple machines, Stellio saves you precious time thanks to **local AI** (Ollama), **smart printer management**, and an **interface built for productivity**.

> 💡 **Philosophy**: Your data stays with you. Everything runs locally.

---

## ✨ Features

### 🏠 Dashboard & productivity
- 📊 **Dashboard on launch**: prints in progress, low filament stock, recent prints and recent files at a glance
- 🧱 **Fully customizable**: drag-and-drop reordering and hiding of widgets (12 available: current prints, low stock, latest S.O.S Print, suggestions, Stellio instances…)
- ✅ **"Getting started" checklist** for new users
- 💡 **"Suggestions" widget**: spots files you reprint often but haven't touched in a while, and slicer profiles with a high failure rate
- ⌨️ **Command palette (`Ctrl+K`)**: navigate, run an action or instantly find a file, tag, filament spool or slicer profile
- 🔔 **Notification center (bell)**: print finished, failure, upcoming maintenance, low filament stock and spool drying reminders all in one place
- 📺 **Floating widget** showing the progress of the current print, visible on every page
- 🧭 **Interactive guided tour** to discover the main features, restartable from Settings
- ♿ **Accessibility**: high-contrast mode, reduced motion, visible keyboard focus indicators everywhere

### 📚 Library management
- 🗂️ **Multiple sources**: local folders, single files, SMB/NFS shares — 3D folders detected on your computer are suggested and can be added in one click
- 🖼️ **Automatic 3D thumbnails** via PyRender (high-quality rendering) or a numpy CPU rasterizer (fallback), with loading-effect placeholders and an **enlarged preview on hover**
- 🏷️ **Custom tags** with colors + AI auto-tagging, and **one-click tagging of several selected files** at once
- 🔍 **AI-assisted semantic search** ("I'm looking for a support for...") with **recent searches remembered**
- ⭐ **Favorites** and advanced filters (type, size, weight, print status), with a **restock warning** when filament stock is insufficient for your favorites
- 🧵 **"Filament stock" filter**: keeps only the files printable with the spools you actually have (Spoolman, manual inventory, TigerTag), by material
- 💾 **Saved filters**: save any combination of library filters and reuse it in one click
- 📋 **"Print soon" queue**, separate from favorites, reorderable by drag-and-drop and sendable straight to the slicer
- 🖱️ **Fast selection**: range selection (`Shift+click`) and keyboard navigation (arrows + `Enter`)
- ✏️ **Bulk rename** (find/replace, prefix, suffix, numbering) with a preview before applying
- ↩️ **Undo deletions** (`Ctrl+Z`) thanks to a 5-minute temporary trash — deleting a tag, project or source is also undoable, with no blocking confirmation
- 🔗 **Model origin**: source link, author, license and notes on each file sheet, with the download date when applicable
- 🧩 **Projects/Assemblies**: group several files for a single object, with multi-plate 3MF support (plate navigation in the viewer)
- 🔁 **Duplicate detection** (exact and geometry-similar)
- 🗜️ **Archive support**: browse and extract models directly from archives
- 🖱️ **Drag & drop 3D files** from your file explorer — works on the desktop app and also through a browser (Raspberry Pi, mobile, remote access)
- 📊 **Detailed statistics** (formats, platforms, profile reliability)

### 🤖 Artificial Intelligence (local Ollama)
- 🏷️ Smart **auto-tagging** of files
- 📝 **Automatic description** of models
- 🔎 **Natural-language semantic search**
- 📐 **Printability analysis** (overhang detection) and **suggested orientations** (less overhang, bed contact shown)
- 🎯 **Slicer profile recommendation** based on geometry + success history
- ⏱️ **Print time estimation** before slicing
- 🩺 **S.O.S Print**: adaptive, step-by-step print-failure diagnosis — Stellio asks one question at a time, narrows down a live list of hypotheses as you answer (max 4 questions), then gives a final diagnosis; photo analysis supported throughout, with saved conversations you can reopen or mark as resolved

### 🖨️ Printer management
- 🔌 Support for **OctoPrint**, **Klipper/Moonraker**, **Bambu Lab** (MQTT), **Creality** (WebSocket), **FlashForge**, **Elegoo** (SDCP) and **PrusaLink**
- 📡 **Automatic network discovery**: Stellio scans your local network (SSDP for Bambu Lab, UDP broadcast for Elegoo/Centauri/FlashForge, targeted probing for Klipper/OctoPrint/PrusaLink/Creality) and lets you add detected printers with one click
- 📡 Real-time monitoring (temperatures, progress, camera)
- 🔧 **Predictive maintenance** with brand-specific task tracking and recommendations (Bambu, Prusa, Creality, etc.)
- 🔩 **Wear parts & consumables**: stock of nozzles, plates, belts… with low-stock alerts, linked to maintenance tasks (each service deducts one part)
- ⏱️ Automatic print-hour counter
- 📤 Direct send to slicer, with a spool selector so you assign the right filament straight from the send dialog, or upload to the printer
- 👀 **Quick preview** (weight, estimated print time) directly in the send-to-slicer window before confirming
- 🛡️ **Smarter pre-print check**: warns if the assigned spool needs drying, if the filament is abrasive (hardened steel nozzle advised) or if no calibration exists for this printer
- 🔁 **Reprint like last time**: from the history, one click reopens the send window with the same printer, profile and spool
- 🎛️ **Calibrations**: save flow, pressure advance, temperatures… per filament and printer, recalled in the send-to-slicer window
- 👥 **Light collaborative mode**: see if another connected device is already viewing a file, and get warned before accidentally sending the same file to the slicer twice

### 🧵 Filament management
- 🔗 **Spoolman** integration (spool management server), with automatic detection on your network
- 🟠 **Bambu Lab AMS** support (slot reading)
- 🟢 **Creality CFS** support
- 🐯 **TigerTag** integration (NFC/RFID spool identification): sign in to see your TigerTag spools in the inventory, or let Stellio pick up an existing TigerTag Studio session automatically — read-only, never modifies your TigerTag inventory
- ⚪ Manual spools
- 📉 Automatic consumption tracking on send-to-slicer, with a compatibility check before printing (enough material left?)
- 🔔 **Low-stock alerts** on startup, with a quick link to buy more
- 💨 **Spool drying**: drying log, status (dry / needs drying) based on the material, suggested temperature and duration, and reminders in notifications
- 📈 **Spool summary**: prints, grams, cost and untracked difference in each spool's sheet

### 📥 Download from platforms
- 🟠 **Printables** (GraphQL API)
- 🟢 **MakerWorld** (2-step Bambu Lab login)
- 🔵 **Thingiverse** (via API key)
- 📁 Direct download to your configured sources
- 🆕 **New version detection**: Stellio checks every day whether the models you downloaded (Printables, MakerWorld, Thingiverse) have been updated
- 🛒 **Useful links**: shops, printer manufacturers, 3D model sites and resources grouped in collapsible sections

### 🧩 Advanced tools
- 🎨 **Automatic bed nesting** (rectpack or real silhouette via shapely)
- 🔧 **Mesh repair** (trimesh + pymeshfix) with a **before/after comparison** (watertightness, triangles, vertices, size)
- 🔄 **Format converter** (STL ↔ 3MF ↔ OBJ)
- 🛡️ **Integrity check** (corrupted/missing files)
- 💰 **Print cost calculation**: material, electricity, machine wear (per hour), fixed fee, margin in % and quantity — unit price and total computed to the cent
- 🧾 **PDF quotes**: generated from the cost calculator with customizable client, item name and notes; configurable quote header (name/company, logo, address, phone, email, website, tax ID) and legal notices in the footer
- 🌱 **Environmental estimate**: CO₂ footprint of your prints (material + electricity)
- 📸 **Print photo gallery** (successful/failed)
- 🕒 **History** with success/failure rating (feeds the AI), a **"View file"** and **"Reprint"** button on each row (with detection of moved/deleted files), and filters by platform, result (successful/failed/partial/unrated) and date range

### 📈 Reports & reliability
- 🧮 **Print reliability**: success rate and cost of failures ranked by slicer profile, material, printer or spool
- 🗓️ **Monthly report**: prints, success rate, filament, cost, failures and CO₂ for the month, compared with the previous one, exportable as PDF

### 🔔 Notifications
- 🪟 **Native Windows notifications**
- 🌐 **Browser notifications** you can enable for Raspberry Pi or mobile access
- 📣 **Push notifications** (ntfy, Telegram, Discord or webhook): print completion and failure detected even with the window closed, plus maintenance and stock alerts

### 🌐 Remote & mobile access
- 📱 **QR code** for mobile access to your library (installable PWA)
- 📲 **Android companion app**: a dedicated QR code lets you download and install the Stellio companion APK directly from the mobile access settings, with the ability to take photos straight from a print
- 🌍 **Remote access** via Cloudflare Tunnel (free, random or fixed URL), or a **custom address** (domain name, DynDNS, VPN, Tailscale…) to avoid Cloudflare, with one-click return to Cloudflare
- 🔗 Temporary **share links** (24h, one-time use)

### 👥 Accounts & multi-instance
- 🔐 **Local accounts** with a recovery code and a secret question: 100% local password reset, no email or internet needed
- 👤 **Read-only guest accounts**: share your library, printers and stock with family or friends without any risk
- 🔄 **Stellio instances**: other installations on your local network are detected automatically and added in one click (you only need to enter their local key)
- 📨 **Send a file to another instance**: choose the destination folder on the target instance — the received file shows up in its library right away
- ✅ **Instance status widget** on the dashboard (green check or red cross for each saved instance)

### 🎨 Customization
- 🌓 Themes: Dark / Light / System
- 🎨 Brand themes: Stellio, Bambu, Prusa, Voron, Creality
- 🎯 Custom accent color
- 🌍 **8 languages**: FR, EN, DE, ES, IT, PT, JA, ZH
- 🧲 Drag & drop navigation reordering
- ↩️ **Settings undo**: revert the very last configuration change you made

### 💾 Backup & Updates
- 📦 Full backup export/import (.zip)
- 🔄 Automatic updates from GitHub (`.zip` patch — same mechanism on Windows and Raspberry Pi/Linux)
- 🔁 Reliable restart after an update or after enabling debug mode, on Windows and Raspberry Pi/Linux
- 📋 Diagnostic log export (secrets masked)

---

## 🖼️ Screenshots

| | |
|---|---|
| ![Library](library.png) *Library with thumbnails* | ![Printers](monitoring.png) *Printer monitoring* |
| ![Slicer](slicer.png) *AI profile recommendation* | ![Nesting](nesting.png) *Automatic nesting* |

---

## 🚀 Installation

### 🪟 Windows (recommended)

1. Download the latest installer from [Releases](https://github.com/stellio-app/stellio/releases)
2. Run `Stellio-Setup-<version>.exe`
3. That's it! 🎉

### 🐧 Raspberry Pi / Linux

Runs in **headless server mode** (no graphical interface): Stellio runs in the background and is accessed from a browser, either on the Pi itself or from any device on the local network.

**Requirements**: Raspberry Pi 4 or 5 recommended, **64-bit** Raspberry Pi OS.

```bash
curl -O https://raw.githubusercontent.com/stellio-app/stellio/main/install-pi.sh
chmod +x install-pi.sh
./install-pi.sh
```

The script automatically installs:
- system dependencies (`ffmpeg`, `unrar`, 3D rendering libraries)
- a dedicated Python virtual environment
- a **systemd service** (`stellio.service`) that starts Stellio at boot and automatically restarts it on crash

Once installed, Stellio is accessible at `http://<pi-ip>:5000`.

```bash
sudo systemctl status stellio     # Service status
sudo systemctl restart stellio    # Restart
sudo journalctl -u stellio -f     # Follow logs live
```

> 💡 **Same updates as on Windows**: the `.zip` patch published with each release is identical on both platforms (pure source code, nothing compiled). Stellio detects and applies it automatically, then restarts the service — no manual reinstall needed.
>
> 🎥 Same features as the Windows version, except for the native desktop window (replaced by browser access) and the local Ollama AI, which needs a reasonably capable model to run well on a Pi — point `ollama_url` to a remote Ollama server in Settings if needed.

### Supported slicers

Stellio automatically detects:
- ✅ OrcaSlicer
- ✅ Bambu Studio
- ✅ PrusaSlicer / SuperSlicer
- ✅ Ultimaker Cura
- ✅ Creality Print

### Printers

| Type | Protocol | Features |
|---|---|---|
| OctoPrint / PrusaLink | HTTP API | Monitoring, upload, camera |
| Klipper/Moonraker | HTTP API | Monitoring, upload, camera, exact hours |
| Bambu Lab | MQTT (cloud + LAN) | Real-time monitoring, AMS, camera (JPEG A1/P1, RTSPS X1/X2/H2), SSDP auto-discovery |
| Creality | WebSocket | Monitoring, CFS, UDP auto-discovery |
| FlashForge | Proprietary API | Monitoring, UDP auto-discovery |
| Elegoo | SDCP over WebSocket | Monitoring, UDP auto-discovery |

---

## 🛠️ Technology

| Component | Technology |
|---|---|
| Backend | Python 3.8+, Flask, Waitress |
| Frontend | HTML5, CSS3, vanilla JavaScript |
| Database | SQLite (WAL mode) |
| Desktop | pywebview (Windows) / headless browser mode (Raspberry Pi, Linux) |
| 3D rendering | PyRender, numpy CPU rasterizer, Three.js |
| Mesh & nesting | trimesh, pymeshfix, shapely, rectpack |
| AI | Ollama (local) |
| Networking | paho-mqtt, smbclient, requests |
| Encryption | cryptography (AES, per-call random IVs) |
| Archives | zipfile, rarfile, py7zr, tarfile |

---

## 📖 Documentation

### Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+K` | Command palette |
| `Ctrl+F` | Search |
| `Ctrl+N` | New download |
| `Ctrl+,` | Settings |
| `Ctrl+Z` | Undo the last deletion (5-minute trash) |
| `Alt+1-8` | Quick navigation |
| `Shift+Click` | Select a range of files |
| `↑ ↓ ← →` + `Enter` | Navigate and open files in the library |
| `F` | Toggle favorites |
| `T` | Tag manager |
| `?` | Shortcuts help |
| `Esc` | Close modal / clear search |

### Project structure

```
stellio/
├── main.py                 # Flask + Desktop backend
├── script.js               # Frontend JavaScript
├── index.html              # Main interface
├── style.css               # Styles
├── launcher.py             # Thin launcher / runtime bootstrapper
├── check_deps.py           # Self-healing dependency checker
├── worker.py               # Unused 3MF worker skeleton (placeholder, not wired in yet)
├── assets/                 # Logos, icons
├── languages/              # Translation files (JSON)
├── apk/                    # Android companion app package
├── docs/                   # Documentation, privacy policy, translated READMEs
├── requirements.txt        # Python dependencies
└── install-pi.sh           # Raspberry Pi / Linux install script (systemd service)
```

Got an idea? [Open an issue](https://github.com/stellio-app/stellio/issues)!

---

## 🤝 Contributing

Contributions are welcome! 🎉

1. **Fork** the project
2. Create your branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a **Pull Request**

### Guidelines
- Follow the existing code style
- Add comments in French or English
- Test your changes on Windows if possible
- Update the documentation if needed

### Reporting a bug

Use the bug report template and include:
- Stellio version
- Operating system
- Steps to reproduce
- Error logs (exportable from Settings → Diagnostics)

---

## 📜 License

This project is licensed under the **GNU Affero General Public License v3.0** — see the [LICENSE](LICENSE) file for details.

> 💡 **In short**: You are free to copy, modify, and distribute this software. If you modify Stellio or use it to provide a network-hosted service, you must publish the full source code under the same AGPLv3 license.

---

## 🔒 Privacy

Stellio is local-first: your data stays on your machine, nothing is collected or sent to external servers by default. See our [Privacy Policy](docs/privacy/PRIVACY.md) for full details.

---

## 🔏 Code Signing Policy

The Windows installer and the Linux AppImage published in [Releases](https://github.com/stellio-app/stellio/releases) are **not code-signed yet**, so Windows SmartScreen may show a warning. macOS builds are not notarized. Every release file comes with a SHA-256 checksum (`.sha256`) that you can verify, and the built-in updater checks it before installing. See [CODE_SIGNING_POLICY.md](CODE_SIGNING_POLICY.md) for the current status, how to verify a download, and our signing plans.

---

## 🙏 Acknowledgments

- [Ollama](https://ollama.com/) for local AI
- [Flask](https://flask.palletsprojects.com/) for the backend
- [Three.js](https://threejs.org/) for web 3D rendering
- [trimesh](https://github.com/mikedh/trimesh) for mesh processing
- [Spoolman](https://github.com/Donkie/Spoolman) for filament spool management
- [TigerTag](https://tigersystem.io) for NFC/RFID filament identification
- The maker community for feedback and suggestions
- All contributors ❤️

---

## 📞 Contact & Support

- 🐛 **Bug report**: [GitHub Issues](https://github.com/stellio-app/stellio/issues)
- 💡 **Feature request**: [GitHub Discussions](https://github.com/stellio-app/stellio/discussions)
- 📧 **Email**: contact@stellio-app.com
- 🌐 **Website**: [stellio-app.com](https://stellio-app.com)

---

## ⭐ Support the project

If Stellio is useful to you, consider:
- Giving it a **star** ⭐ on GitHub
- Sharing the project around you
- [Contributing code](#-contributing) or translations
- Reporting bugs to help improve the app

---

<p align="center"><strong>Made with ❤️ for the maker community</strong></p>

<p align="center">
  <a href="https://github.com/stellio-app/stellio">⭐ Star this repo</a> •
  <a href="https://github.com/stellio-app/stellio/issues">🐛 Report a bug</a> •
  <a href="https://github.com/stellio-app/stellio/discussions">💡 Request a feature</a>
</p>
