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

### 📚 Library management
- 🗂️ **Multiple sources**: local folders, single files, SMB/NFS shares
- 🖼️ **Automatic 3D thumbnails** via PyRender (high-quality rendering) or a numpy CPU rasterizer (fallback)
- 🏷️ **Custom tags** with colors + AI auto-tagging
- 🔍 **AI-assisted semantic search** ("I'm looking for a support for...")
- ⭐ **Favorites** and advanced filters (type, size, weight, print status)
- 🧩 **Projects/Assemblies**: group several files for a single object, with multi-plate 3MF support (plate navigation in the viewer)
- 🔁 **Duplicate detection** (exact and geometry-similar)
- 📊 **Detailed statistics** (formats, platforms, profile reliability)

### 🤖 Artificial Intelligence (local Ollama)
- 🏷️ Smart **auto-tagging** of files
- 📝 **Automatic description** of models
- 🔎 **Natural-language semantic search**
- 📐 **Printability analysis** (overhang detection)
- 🎯 **Slicer profile recommendation** based on geometry + success history
- 🩺 **S.O.S Print**: adaptive, step-by-step print-failure diagnosis — Stellio asks one question at a time, narrows down a live list of hypotheses as you answer (max 4 questions), then gives a final diagnosis; photo analysis supported throughout

### 🖨️ Printer management
- 🔌 Support for **OctoPrint**, **Klipper/Moonraker**, **Bambu Lab** (MQTT), **Creality** (WebSocket), **FlashForge**
- 📡 **Automatic network discovery**: Stellio scans your local network (SSDP for Bambu Lab, UDP broadcast for Elegoo/Centauri/FlashForge, targeted probing for Klipper/OctoPrint/PrusaLink/Creality) and lets you add detected printers with one click
- 📡 Real-time monitoring (temperatures, progress, camera)
- 🔧 **Predictive maintenance** with brand-specific task tracking and recommendations (Bambu, Prusa, Creality, etc.)
- ⏱️ Automatic print-hour counter
- 📤 Direct send to slicer, with a spool selector so you assign the right filament straight from the send dialog, or upload to the printer

### 🧵 Filament management
- 🔗 **Spoolman** integration (spool management server)
- 🏷️ **TigerTag** inventory integration (read-only)
- 🟠 **Bambu Lab AMS** support (slot reading)
- 🟢 **Creality CFS** support
- ⚪ Manual spools
- 📉 Automatic consumption tracking on send-to-slicer, with a compatibility check before printing (enough material left?)
- 🔔 **Low-stock alerts** on startup, with a quick link to buy more

### 📥 Download from platforms
- 🟠 **Printables** (GraphQL API)
- 🟢 **MakerWorld** (2-step Bambu Lab login)
- 🔵 **Thingiverse** (via API key)
- 🟣 **Cults3D**
- 📁 Direct download to your configured sources

### 🧩 Advanced tools
- 🎨 **Automatic bed nesting** (rectpack or real silhouette via shapely)
- 🔧 **Mesh repair** (trimesh + pymeshfix)
- 🔄 **Format converter** (STL ↔ 3MF ↔ OBJ)
- 🛡️ **Integrity check** (corrupted/missing files)
- 💰 **Print cost calculation** (material + electricity)
- 📸 **Print photo gallery** (successful/failed)
- 🕒 **History** with success/failure rating (feeds the AI)

### 🌐 Remote & mobile access
- 📱 **QR code** for mobile access to your library (installable PWA)
- 📲 **Android companion app**: a dedicated QR code lets you download and install the Stellio companion APK directly from the mobile access settings
- 🌍 **Remote access** via Cloudflare Tunnel (free, random or fixed URL)
- 🔗 Temporary **share links** (24h, one-time use)

### 🎨 Customization
- 🌓 Themes: Dark / Light / System
- 🎨 Brand themes: Stellio, Bambu, Prusa, Voron, Creality
- 🎯 Custom accent color
- 🌍 **8 languages**: FR, EN, DE, ES, IT, PT, JA, ZH
- 🧲 Drag & drop navigation reordering

### 💾 Backup & Updates
- 📦 Full backup export/import (.zip)
- 🔄 Automatic updates from GitHub (`.zip` patch — same mechanism on Windows and Raspberry Pi/Linux)
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
2. Run `Stellio-Setup.exe`
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
- system dependencies (`ffmpeg`, `unrar-free`, 3D rendering libraries)
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
| `Ctrl+F` | Search |
| `Ctrl+N` | New download |
| `Ctrl+,` | Settings |
| `Alt+1-8` | Quick navigation |
| `F` | Toggle favorites |
| `T` | Tag manager |
| `?` | Shortcuts help |
| `Esc` | Close modal / clear search |

### Project structure

```
stellio/
├── main.py                 # Flask + Desktop backend
├── script.js                # Frontend JavaScript
├── index.html                # Main interface
├── style.css                  # Styles
├── launcher.py                  # Thin launcher / runtime bootstrapper
├── check_deps.py                 # Self-healing dependency checker
├── worker.py                       # Background worker (thumbnails, scans)
├── assets/                          # Logos, icons
├── languages/                        # Translation files (JSON)
├── apk/                                # Android companion app package
├── docs/                                # Documentation, privacy policy, translated READMEs
├── requirements.txt                      # Python dependencies
├── install-pi.sh                          # Raspberry Pi / Linux install script (systemd service)
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

Windows executables published in [Releases](https://github.com/stellio-app/stellio/releases) are digitally signed. See [CODE_SIGNING_POLICY.md](CODE_SIGNING_POLICY.md) for details on our signing process and private key protection practices.

---

## 🙏 Acknowledgments

- [Ollama](https://ollama.com/) for local AI
- [Flask](https://flask.palletsprojects.com/) for the backend
- [Three.js](https://threejs.org/) for web 3D rendering
- [trimesh](https://github.com/mikedh/trimesh) for mesh processing
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
