<div align="center">

#  Stellio-app

### The ultimate 3D file manager for makers and 3D printing enthusiasts

[![Version](https://img.shields.io/github/v/release/stellio-app/stellio-app?style=for-the-badge&logo=github&color=4ea1d3)](https://github.com/stellio-app/stellio-app/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![Downloads](https://img.shields.io/github/downloads/stellio-app/stellio-app/total?style=for-the-badge&color=success)](https://github.com/stellio-app/stellio-app/releases)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge&logo=python)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey?style=for-the-badge)]()

[🌐 Official Website](https://stellio-app.com) • [📥 Download](https://github.com/stellio-app/stellio-app/releases/latest) • [🐛 Report a Bug](https://github.com/stellio-app/stellio-app/issues)

</div>

---

## 📖 About

**Stellio** is a modern, lightweight desktop application designed to centralize, organize, and manage your 3D files (STL, 3MF, OBJ). With its intuitive interface and advanced features, Stellio transforms your 3D printing workflow into a seamless and productive experience.

> 💡 **Why Stellio?** Because managing hundreds of 3D files scattered across multiple folders, NAS devices, and download platforms shouldn't be a headache.

---

## ✨ Features

### 📁 Multi-Source Management
- 🗂️ **Local Folders**: Browse your local directories
- 🌐 **Network Shares**: SMB/NFS access to your NAS and servers
- 📄 **Single Files**: Add individual files
- 🔄 **Automatic Scan**: Real-time detection of new files

### 🌐 Integrated Downloads
- 📨 **Printables**: Download
- 📊 **Real-Time Tracking**: Progress bar with cancellation support

### 🖼️ Automatic Thumbnails
- 🎨 **PyRender Rendering**: Professional 3D thumbnails
- ⚡ **Lazy Generation**: Optimized to keep the interface smooth and responsive
- 🛡️ **Smart Fallback**: Showcases the Stellio logo if a file is corrupted
- 📊 **Progress Bar**: Real-time tracking of thumbnail generation

### 🏷️ Advanced Organization
- 🏷️ **Custom Tags**: Categorize your files with color-coded tags
- ⭐ **Favorites**: Quick access to your favorite files
- 🔍 **Powerful Filters**: Filter by type, size, tags, or folder
- ⚡ **Instant Search**: Find any file in milliseconds
- 📂 **Folder Sorting**: Hierarchical view of your files

### ✂️ Slicer Integration
- 🖨️ **Multi-Slicers**: OrcaSlicer, Bambu Studio, PrusaSlicer, Ultimaker Cura
- 📦 **Batch Send**: Send multiple files at once
- 🔍 **Automatic Detection**: Automatically locates your installed slicers

### 🖨️ Printer Monitoring
- 🌡️ **Temperatures**: Real-time tracking of extruder, bed, and chamber temperatures
- 📈 **Progress**: Print job tracking with estimated remaining time
- 📹 **Camera**: Integrated MJPEG video stream
- 📜 **History**: Last print details and statistics
- 🎯 **Support**: Klipper/Moonraker compatible

### 🔧 Mesh Repair
- 🔍 **Automatic Detection**: Identifies non-manifold files
- 🛠️ **One-Click Repair**: Fixes geometric holes and issues
- 📐 **3D Analysis**: Displays dimensions, volume, weight, and estimated print time

### 🌍 Multi-Language
- 🇫🇷 Français | 🇬🇧 English | 🇪🇸 Español | 🇮🇹 Italiano
- 🇵🇹 Português | 🇯🇵 日本語 | 🇩🇪 Deutsch | 🇨🇳 中文

### 🔄 Automatic Updates
- 🔍 **GitHub Check**: Automatically detects new versions
- ⬇️ **Built-in Download**: No browser required
- 🚀 **Silent Installation**: Automatic restart after updating

### 🎨 Customization
- 🌓 **Themes**: Dark, Light, System (Auto)
- 🎨 **Brand Colors**: Stellio, Bambu Lab, Prusa, Voron, Creality
- 📱 **Responsive Interface**: Clean, modern, and sleek design

---

## 📥 Installation

### 🪟 Windows (Recommended)

1. Download the latest installer from the [Releases page](https://github.com/stellio-app/stellio-app/releases/latest)
2. Run `Stellio-Setup-x.x.x.exe`
3. Follow the installation wizard
4. Launch Stellio from the Start Menu or Desktop

---

## 🚀 Quick Start

### First Launch

1. **Create your account**: Enter a username + password
2. **Add a source**: Click "Add" in Settings
3. **Explore your files**: Browse your library
4. **Customize**: Choose your preferred theme and default slicer

### Initial Configuration

```
1. Settings → Sources → Add a folder
2. Settings → Slicer → Choose your slicer
3. Settings → Appearance → Theme and color
4. Settings → Language → Select your preferred language
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-------------|
| **Backend** | Python 3.10+, Flask, Waitress |
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla) |
| **Database** | SQLite3 |
| **3D Rendering** | PyRender, Trimesh, PyVista |
| **Visualization** | Three.js |
| **Protocols** | SMB (smbprotocol), NFS |
| **Encryption** | cryptography (AES-CFB) |
| **Desktop Shell** | PyWebView |
| **Packaging** | PyInstaller, Inno Setup |

---

## 📋 System Requirements

### Windows
- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4 GB minimum (8 GB recommended)
- **Storage**: 500 MB for the application + space for thumbnails
- **GPU**: OpenGL 3.3+ support for 3D rendering

---

## 🔐 Security

- 🔒 **Local Encryption**: Passwords and API tokens are encrypted locally (AES-256)
- 🏠 **No Cloud**: All your data remains strictly on your local machine
- 👁️ **Open Source**: Code is fully auditable by the community
- ✅ **Signed Updates**: Built-in integrity verification

---

## 🤝 Contributing

Contributions are welcome! Here is how you can help:

### Report a Bug
1. Check the [existing issues](https://github.com/stellio-app/stellio-app/issues)
2. Create a new issue using the "Bug Report" template
3. Include: version, OS, steps to reproduce, and logs

### Suggest a Feature
1. Open a "Feature Request" issue
2. Describe your idea and its use case
3. Discuss it with the community

---

## 💬 Community

Join the Stellio community:

- 🌐 **Website**: [stellio-app.com](https://stellio-app.com)
- 📧 **Email**: contact@stellio-app.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/stellio-app/stellio-app/issues)

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2026 Stellio Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

---

## 🙏 Acknowledgements

Stellio is made possible thanks to:

- **[PyRender](https://github.com/mmatl/pyrender)** - Professional 3D rendering
- **[Trimesh](https://github.com/mikedh/trimesh)** - 3D mesh manipulation
- **[Flask](https://flask.palletsprojects.com/)** - Lightweight web framework
- **[PyWebView](https://github.com/r0x0r/pywebview)** - Desktop UI component
- **[Three.js](https://threejs.org/)** - Web-based 3D visualization
- **The Maker Community** - Invaluable feedback and suggestions

---

## ⭐ Support the Project

If you love Stellio, consider:

- ⭐ **Starring** the repo on GitHub
- 🐦 **Sharing** it on social media
- 🐛 **Reporting** bugs
- 💡 **Suggesting** new features
- ☕ **Sponsoring** (coming soon)

---

<div align="center">

### Made with ❤️ for the 3D printing community

[🌐 stellio-app.com](https://stellio-app.com) • [📥 Download](https://github.com/stellio-app/stellio-app/releases/latest)

**© 2026 Stellio Project. All rights reserved.**

</div>
