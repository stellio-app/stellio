<div align="center">

#  <img src="https://stellio-app.com/assets/logo-nom-stellio.png" alt="Stellio Logo" width="200"/>

### Der ultimative 3D-Dateimanager für Maker und 3D-Druck-Besitzer

[![Version](https://img.shields.io/badge/version-0.5.9-blue.svg)](https://github.com/stellio-app/stellio-app/releases)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Raspberry%20Pi%20%2F%20Linux-lightgrey.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)]()

[🇬🇧 English](README.md) | [🇫🇷 Français](README.fr.md) | 🇩🇪 **Deutsch** | [🇪🇸 Español](README.es.md) | [🇮🇹 Italiano](README.it.md) | [🇵🇹 Português](README.pt.md) | [🇯🇵 日本語](README.ja.md) | [🇨🇳 中文](README.zh.md)

[🚀 Installation](#-installation) • [✨ Funktionen](#-funktionen) • [📖 Dokumentation](#-dokumentation) • [🤝 Mitwirken](#-mitwirken) • [📜 Lizenz](#-lizenz)

</div>

---

## 🎯 Überblick

**Stellio** ist eine moderne Desktop-Anwendung, die Ihre gesamte 3D-Bibliothek (STL, 3MF, OBJ) zentralisiert, wiederkehrende Aufgaben automatisiert und sich nahtlos in Ihren 3D-Druck-Workflow einfügt.

Ob Sie Einsteiger oder erfahrener Betreiber mehrerer Drucker sind – Stellio spart Ihnen wertvolle Zeit dank **lokaler KI** (Ollama), **intelligenter Druckerverwaltung** und einer **auf Produktivität ausgelegten Oberfläche**.

> 💡 **Philosophie**: Ihre Daten bleiben bei Ihnen. Alles läuft lokal.

---

## ✨ Funktionen

### 📚 Bibliotheksverwaltung
- 🗂️ **Mehrere Quellen**: lokale Ordner, einzelne Dateien, SMB/NFS-Freigaben
- 🖼️ **Automatische 3D-Vorschaubilder** via PyRender (hochwertiges Rendering) oder Matplotlib (Fallback)
- 🏷️ **Benutzerdefinierte Tags** mit Farben + KI-Auto-Tagging
- 🔍 **KI-gestützte semantische Suche** ("ich suche eine Stütze für...")
- ⭐ **Favoriten** und erweiterte Filter (Typ, Größe, Gewicht, Druckstatus)
- 🧩 **Projekte/Baugruppen**: mehrere Dateien für dasselbe Objekt gruppieren
- 📊 **Detaillierte Statistiken** (Formate, Plattformen, Profilzuverlässigkeit)

### 🤖 Künstliche Intelligenz (lokales Ollama)
- 🏷️ Intelligentes **Auto-Tagging** von Dateien
- 📝 **Automatische Beschreibung** von Modellen
- 🔎 **Semantische Suche** in natürlicher Sprache
- 🎯 **Slicer-Profil-Empfehlung** basierend auf Geometrie + Erfolgshistorie
- 🩺 **S.O.S Print**: Diagnose von Druckfehlern (mit Fotoanalyse)

### 🖨️ Druckerverwaltung
- 🔌 Unterstützung für **OctoPrint**, **Klipper/Moonraker**, **Bambu Lab** (MQTT)
- 📡 Echtzeit-Monitoring (Temperaturen, Fortschritt, Kamera)
- 🔧 **Vorausschauende Wartung** mit markenspezifischen Empfehlungen (Bambu, Prusa, Creality usw.)
- ⏱️ Automatischer Druckstundenzähler
- 📤 Direkter Versand an den Slicer oder Upload zum Drucker

### 🧵 Filamentverwaltung
- 🔗 **Spoolman**-Integration (Spulen-Verwaltungsserver)
- 🟠 Unterstützung für **Bambu Lab AMS** (Slot-Auslesung)
- 🟢 Unterstützung für **Creality CFS**
- ⚪ Manuelle Spulen
- 📉 Automatische Verbrauchszählung beim Senden an den Slicer
- ✅ Kompatibilitätsprüfung (ausreichende Menge?)

### 📥 Download von Plattformen
- 🟠 **Printables** (GraphQL-API)
- 🟢 **MakerWorld** (2-Schritt-Bambu-Lab-Login)
- 🔵 **Thingiverse** (über API-Schlüssel)
- 📁 Direkter Download in Ihre konfigurierten Quellen

### 🧩 Erweiterte Werkzeuge
- 🎨 **Automatisches Nesting** der Druckplatte (rectpack oder reale Silhouette via shapely)
- 🔧 **Mesh-Reparatur** (trimesh + pymeshfix)
- 🔄 **Formatkonverter** (STL ↔ 3MF ↔ OBJ)
- 🛡️ **Integritätsprüfung** (beschädigte/fehlende Dateien)
- 💰 **Druckkostenberechnung** (Material + Strom)
- 📸 **Foto-Galerie** von Drucken (erfolgreich/fehlgeschlagen)
- 🕒 **Verlauf** mit Erfolg/Misserfolg-Bewertung (speist die KI)
- 🔍 **Duplikaterkennung** (exakt und geometrisch ähnlich)

### 🌐 Fernzugriff & Mobil
- 📱 **QR-Code** für mobilen Zugriff (installierbare PWA)
- 🌍 **Fernzugriff** via Cloudflare Tunnel (kostenlos, zufällige oder feste URL)
- 🔗 Temporäre **Freigabelinks** (24 h, einmalige Nutzung)

### 🎨 Anpassung
- 🌓 Themes: Dunkel / Hell / System
- 🎨 Marken-Themes: Stellio, Bambu, Prusa, Voron, Creality
- 🎯 Individuelle Akzentfarbe
- 🌍 **8 Sprachen**: FR, EN, DE, ES, IT, PT, JA, ZH
- 🧲 Drag & Drop-Neuanordnung der Navigation

### 💾 Backup & Updates
- 📦 Export/Import kompletter Backups (.zip)
- 🔄 Automatische Updates von GitHub (`.zip`-Patch — gleicher Mechanismus unter Windows und Raspberry Pi/Linux)
- 📋 Export von Diagnoseprotokollen (Geheimnisse maskiert)

---

## 🖼️ Screenshots

<div align="center">
<table>
<tr></tr>
<td><img src="library.png" alt="Bibliothek" width="400"/><br><em>Bibliothek mit Vorschaubildern</em></td>
<td><img src="monitoring.png" alt="Drucker" width="400"/><br><em>Drucker-Monitoring</em></td>
</tr>
<tr>
<td><img src="slicer.png" alt="Slicer" width="400"/><br><em>KI-Profilempfehlung</em></td>
<td><img src="nesting.png" alt="Nesting" width="400"/><br><em>Automatisches Nesting</em></td>
</tr>
</table>
</div>

---

## 🚀 Installation

### 🪟 Windows (empfohlen)

1. Laden Sie den neuesten Installer von den [Releases](https://github.com/stellio-app/stellio-app/releases) herunter
2. Starten Sie `Stellio-Setup.exe`
3. Fertig! 🎉

### 🐧 Raspberry Pi / Linux

Läuft im **Headless-Server-Modus** (ohne grafische Oberfläche): Stellio läuft im Hintergrund und wird über einen Browser genutzt, entweder direkt auf dem Pi oder von jedem Gerät im lokalen Netzwerk.

**Voraussetzungen**: Raspberry Pi 4 oder 5 empfohlen, **64-Bit**-Raspberry Pi OS.

```bash
curl -O https://raw.githubusercontent.com/stellio-app/stellio-app/main/install-pi.sh
chmod +x install-pi.sh
./install-pi.sh
```

Das Skript installiert automatisch:
- Systemabhängigkeiten (`ffmpeg`, `unrar-free`, 3D-Rendering-Bibliotheken)
- eine dedizierte Python-Virtualenv
- einen **systemd-Dienst** (`stellio.service`), der Stellio beim Booten startet und bei Abstürzen automatisch neu startet

Nach der Installation ist Stellio unter `http://<pi-ip>:5000` erreichbar.

```bash
sudo systemctl status stellio     # Dienststatus
sudo systemctl restart stellio    # Neustart
sudo journalctl -u stellio -f     # Logs live verfolgen
```

> 💡 **Gleiche Updates wie unter Windows**: Der mit jedem Release veröffentlichte `.zip`-Patch ist auf beiden Plattformen identisch (reiner Quellcode, nichts Kompiliertes). Stellio erkennt und wendet ihn automatisch an und startet den Dienst neu — keine manuelle Neuinstallation nötig.

> 🎥 Gleiche Funktionen wie die Windows-Version, mit Ausnahme des nativen Desktop-Fensters (ersetzt durch Browserzugriff) und der lokalen Ollama-KI, die ein angemessen leistungsfähiges Modell benötigt, um auf einem Pi gut zu laufen — verweisen Sie `ollama_url` bei Bedarf in den Einstellungen auf einen entfernten Ollama-Server.

### Unterstützte Slicer

Stellio erkennt automatisch:
- ✅ OrcaSlicer
- ✅ Bambu Studio
- ✅ PrusaSlicer / SuperSlicer
- ✅ Ultimaker Cura
- ✅ Creality Print

### Drucker

| Typ | Protokoll | Funktionen |
|------|-----------|-----------------|
| OctoPrint | HTTP-API | Monitoring, Upload, Kamera |
| Klipper/Moonraker | HTTP-API | Monitoring, Upload, Kamera, exakte Stunden |
| Bambu Lab | MQTT | Echtzeit-Monitoring, AMS, Kamera (JPEG A1/P1, RTSPS X1/X2/H2) |

---

## 🛠️ Technologien

| Komponente | Technologie |
|-----------|-------------|
| Backend | Python 3.8+, Flask, Waitress |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Datenbank | SQLite (WAL-Modus) |
| Desktop | pywebview (Windows) / Headless-Browser-Modus (Raspberry Pi, Linux) |
| 3D-Rendering | PyRender, Matplotlib, Three.js |
| Mesh | trimesh, pymeshfix, shapely |
| KI | Ollama (lokal) |
| Netzwerk | paho-mqtt, smbclient, requests |
| Verschlüsselung | cryptography (AES-CFB) |
| Archive | zipfile, rarfile, py7zr, tarfile |

---

## 📖 Dokumentation

### Tastenkombinationen

| Tastenkombination | Aktion |
|-----------|--------|
| `Strg+F` | Suchen |
| `Strg+N` | Neuer Download |
| `Strg+,` | Einstellungen |
| `Alt+1-8` | Schnellnavigation |
| `F` | Favoriten umschalten |
| `T` | Tag-Manager |
| `?` | Hilfe zu Tastenkürzeln |
| `Esc` | Modal schließen / Suche leeren |

### Projektstruktur
```
stellio-app/
├── main.py                 # Flask + Desktop-Backend
├── script.js                # Frontend-JavaScript
├── index.html                # Hauptoberfläche
├── style.css                  # Styles
├── assets/                     # Logos, Icons
├── languages/                   # Übersetzungsdateien (JSON)
├── requirements-pi.txt           # Python-Abhängigkeiten (Raspberry Pi / Linux-Installation)
├── install-pi.sh                  # Installationsskript für Raspberry Pi / Linux (systemd-Dienst)
```

---

Sie haben eine Idee? [Erstellen Sie ein Issue](https://github.com/stellio-app/stellio-app/issues)!

---

## 🤝 Mitwirken

Beiträge sind willkommen! 🎉

1. **Fork** des Projekts erstellen
2. Erstellen Sie Ihren Branch (`git checkout -b feature/AmazingFeature`)
3. Committen Sie Ihre Änderungen (`git commit -m 'Add AmazingFeature'`)
4. Pushen Sie den Branch (`git push origin feature/AmazingFeature`)
5. Öffnen Sie einen **Pull Request**

### Richtlinien
- Halten Sie sich an den bestehenden Code-Stil
- Fügen Sie Kommentare auf Französisch oder Englisch hinzu
- Testen Sie Ihre Änderungen wenn möglich unter Windows
- Aktualisieren Sie bei Bedarf die Dokumentation

### Einen Fehler melden
Verwenden Sie die Bug-Report-Vorlage und geben Sie an:
- Stellio-Version
- Betriebssystem
- Schritte zur Reproduktion
- Fehlerprotokolle (exportierbar über Einstellungen → Diagnose)

---

## 📜 Lizenz

Dieses Projekt steht unter der freien Lizenz **GNU Affero General Public License v3.0** — Details finden Sie in der Datei [LICENSE](./LICENSE).

> 💡 **Kurz gesagt**: Sie dürfen diese Software frei kopieren, verändern und weitergeben. Wenn Sie Stellio verändern oder damit einen netzwerkbasierten Dienst anbieten, müssen Sie den vollständigen Quellcode unter derselben AGPLv3-Lizenz veröffentlichen.

---

## 🙏 Danksagungen

- [Ollama](https://ollama.com/) für die lokale KI
- [Flask](https://flask.palletsprojects.com/) für das Backend
- [Three.js](https://threejs.org/) für 3D-Rendering im Web
- [trimesh](https://github.com/mikedh/trimesh) für die Mesh-Verarbeitung
- Die Maker-Community für Feedback und Vorschläge
- Alle Mitwirkenden ❤️

---

## 📞 Kontakt & Support

- 🐛 **Bug-Report**: [GitHub Issues](https://github.com/stellio-app/stellio-app/issues)
- 💡 **Feature-Wunsch**: [GitHub Discussions](https://github.com/stellio-app/stellio-app/discussions)
- 📧 **E-Mail**: contact@stellio-app.com
- 🌐 **Website**: [stellio-app.com](https://stellio-app.com)

---

## ⭐ Projekt unterstützen

Wenn Ihnen Stellio nützlich ist, denken Sie daran:
- Vergeben Sie einen **Stern** ⭐ auf GitHub
- Teilen Sie das Projekt in Ihrem Umfeld
- [Am Code mitwirken](#-mitwirken) oder bei der Übersetzung helfen
- Fehler melden, um die App zu verbessern

---

<div align="center">

**Mit ❤️ für die Maker-Community entwickelt**

[⭐ Star this repo](https://github.com/stellio-app/stellio-app) • [🐛 Report a bug](https://github.com/stellio-app/stellio-app/issues) • [💡 Request a feature](https://github.com/stellio-app/stellio-app/discussions)

</div>
