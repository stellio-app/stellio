<p align="center">
  <img src="https://stellio-app.com/assets/logo-nom-stellio.png" alt="Stellio Logo" width="360">
</p>

<h3 align="center">Der ultimative 3D-Dateimanager für Maker und Besitzer von 3D-Druckern</h3>

<p align="center">
  <a href="https://github.com/stellio-app/stellio/releases"><img src="https://img.shields.io/github/v/release/stellio-app/stellio?color=blue" alt="Version"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python"></a>
  <a href="https://flask.palletsprojects.com/"><img src="https://img.shields.io/badge/flask-3.0+-green.svg" alt="Flask"></a>
  <a href="https://www.gnu.org/licenses/agpl-3.0"><img src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg" alt="License: AGPL v3"></a>
  <a href="https://github.com/stellio-app/stellio/blob/main"><img src="https://img.shields.io/badge/platform-Windows%20%7C%20Raspberry%20Pi%20%2F%20Linux-lightgrey.svg" alt="Platform"></a>
  <a href="https://github.com/stellio-app/stellio/blob/main"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"></a>
</p>

<p align="center">
  <a href="../../README.md">🇬🇧 English</a> |
  <a href="README.fr.md">🇫🇷 Français</a> |
  🇩🇪 <strong>Deutsch</strong> |
  <a href="README.es.md">🇪🇸 Español</a> |
  <a href="README.it.md">🇮🇹 Italiano</a> |
  <a href="README.pt.md">🇵🇹 Português</a> |
  <a href="README.ja.md">🇯🇵 日本語</a> |
  <a href="README.zh.md">🇨🇳 中文</a>
</p>

<p align="center">
  <a href="#-installation">🚀 Installation</a> •
  <a href="#-funktionen">✨ Funktionen</a> •
  <a href="#-dokumentation">📖 Dokumentation</a> •
  <a href="#-mitwirken">🤝 Mitwirken</a> •
  <a href="#-lizenz">📜 Lizenz</a>
</p>

---

## 🎯 Überblick

**Stellio** ist eine moderne Desktop-Anwendung, die Ihre gesamte 3D-Bibliothek (STL, 3MF, OBJ) zentralisiert, wiederkehrende Aufgaben automatisiert und sich nahtlos in Ihren 3D-Druck-Workflow integriert.

Ob Einsteiger-Maker oder erfahrener Betreiber mehrerer Drucker — Stellio spart Ihnen dank **lokaler KI** (Ollama), **intelligenter Druckerverwaltung** und einer **auf Produktivität ausgelegten Oberfläche** wertvolle Zeit.

> 💡 **Philosophie**: Ihre Daten bleiben bei Ihnen. Alles läuft lokal.

---

## ✨ Funktionen

### 🏠 Dashboard & Produktivität
- 📊 **Dashboard beim Start**: laufende Drucke, niedriger Filamentbestand, letzte Drucke und zuletzt verwendete Dateien auf einen Blick
- 🧱 **Vollständig anpassbar**: Widgets per Drag & Drop anordnen und ausblenden (12 verfügbar: laufende Drucke, niedriger Bestand, letzter S.O.S Print, Vorschläge, Stellio-Instanzen …)
- ✅ **Checkliste „Erste Schritte“** für neue Nutzer
- 💡 **Widget „Vorschläge“**: erkennt Dateien, die Sie oft erneut drucken, aber länger nicht angesehen haben, sowie Slicer-Profile mit hoher Fehlerquote
- ⌨️ **Befehlspalette (`Strg+K`)**: navigieren, Aktionen ausführen oder sofort Dateien, Tags, Spulen und Slicer-Profile finden
- 🔔 **Benachrichtigungszentrale (Glocke)**: Druckende, Fehler, anstehende Wartung, niedriger Filamentbestand und Trocknungserinnerungen an einem Ort
- 📺 **Schwebendes Widget** mit dem Fortschritt des laufenden Drucks, auf jeder Seite sichtbar
- 🧭 **Interaktive geführte Tour** zum Kennenlernen der wichtigsten Funktionen, in den Einstellungen erneut startbar
- ♿ **Barrierefreiheit**: Hochkontrastmodus, reduzierte Animationen, überall sichtbare Tastaturfokus-Markierungen

### 📚 Bibliotheksverwaltung
- 🗂️ **Mehrere Quellen**: lokale Ordner, einzelne Dateien, SMB/NFS-Freigaben — auf dem Computer erkannte 3D-Ordner werden vorgeschlagen und lassen sich mit einem Klick hinzufügen
- 🖼️ **Automatische 3D-Vorschaubilder** via PyRender (hochwertiges Rendering) oder einen numpy-CPU-Rasterizer (Fallback), mit Lade-Effekt und **vergrößerter Vorschau beim Darüberfahren**
- 🏷️ **Individuelle Tags** mit Farben + automatisches Tagging per KI, sowie **Tagging mehrerer ausgewählter Dateien mit einem Klick**
- 🔍 **KI-gestützte semantische Suche** ("ich suche eine Stütze für...") mit **gemerkten letzten Suchen**
- ⭐ **Favoriten** und erweiterte Filter (Typ, Größe, Gewicht, Druckstatus), mit einer **Nachkauf-Warnung**, wenn der Filamentbestand für Ihre Favoriten nicht ausreicht
- 🧵 **Filter „Filamentbestand“**: zeigt nur Dateien, die mit den tatsächlich vorhandenen Spulen druckbar sind (Spoolman, manuelles Inventar, TigerTag), nach Material
- 💾 **Gespeicherte Filter**: Filterkombinationen speichern und mit einem Klick wiederverwenden
- 📋 **Warteschlange „Bald drucken“**, getrennt von den Favoriten, per Drag & Drop sortierbar und direkt an den Slicer sendbar
- 🖱️ **Schnelle Auswahl**: Bereichsauswahl (`Umschalt+Klick`) und Tastaturnavigation (Pfeiltasten + `Enter`)
- ✏️ **Massenumbenennung** (Suchen/Ersetzen, Präfix, Suffix, Nummerierung) mit Vorschau vor dem Anwenden
- ↩️ **Löschungen rückgängig machen** (`Strg+Z`) dank 5-minütigem temporärem Papierkorb — auch das Löschen von Tags, Projekten oder Quellen ist rückgängig machbar, ohne blockierende Bestätigung
- 🔗 **Modellherkunft**: Quelllink, Autor, Lizenz und Notizen im Dateiblatt, ggf. mit Download-Datum
- 🧩 **Projekte/Baugruppen**: mehrere Dateien zu einem Objekt gruppieren, mit Multi-Plate-3MF-Unterstützung (Plattennavigation im Viewer)
- 🔁 **Duplikaterkennung** (exakt und geometrisch ähnlich)
- 🗜️ **Archivunterstützung**: Modelle direkt aus Archiven durchsuchen und extrahieren
- 🖱️ **Drag & Drop von 3D-Dateien** aus dem Datei-Explorer — funktioniert in der Desktop-App und auch über einen Browser (Raspberry Pi, Mobilgerät, Fernzugriff)
- 📊 **Detaillierte Statistiken** (Formate, Plattformen, Profilzuverlässigkeit)

### 🤖 Künstliche Intelligenz (lokales Ollama)
- 🏷️ Intelligentes **automatisches Tagging** von Dateien
- 📝 **Automatische Beschreibung** von Modellen
- 🔎 **Semantische Suche** in natürlicher Sprache
- 📐 **Druckbarkeitsanalyse** (Überhang-Erkennung) und **empfohlene Ausrichtungen** (weniger Überhang, Bettkontakt wird angezeigt)
- 🎯 **Slicer-Profil-Empfehlung** basierend auf Geometrie + Erfolgshistorie
- ⏱️ **Druckzeitschätzung** vor dem Slicen
- 🩺 **S.O.S Print**: adaptive, schrittweise Diagnose von Druckfehlern — Stellio stellt jeweils eine Frage, grenzt anhand Ihrer Antworten eine Liste von Hypothesen ein (max. 4 Fragen) und liefert dann eine abschließende Diagnose; Fotoanalyse ist jederzeit möglich, Gespräche werden gespeichert (wieder öffnen, als gelöst markieren)

### 🖨️ Druckerverwaltung
- 🔌 Unterstützung für **OctoPrint**, **Klipper/Moonraker**, **Bambu Lab** (MQTT), **Creality** (WebSocket), **FlashForge**, **Elegoo** (SDCP) und **PrusaLink**
- 📡 **Automatische Netzwerkerkennung**: Stellio scannt Ihr lokales Netzwerk (SSDP für Bambu Lab, UDP-Broadcast für Elegoo/Centauri/FlashForge, gezielte Abfrage für Klipper/OctoPrint/PrusaLink/Creality) und lässt Sie gefundene Drucker mit einem Klick hinzufügen
- 📡 Echtzeit-Überwachung (Temperaturen, Fortschritt, Kamera)
- 🔧 **Vorausschauende Wartung** mit markenspezifischer Aufgabenverfolgung und Empfehlungen (Bambu, Prusa, Creality usw.)
- 🔩 **Verschleißteile & Verbrauchsmaterial**: Bestand an Düsen, Druckplatten, Riemen … mit Warnungen, verknüpft mit Wartungsaufgaben (jede Wartung bucht ein Teil ab)
- ⏱️ Automatischer Druckstundenzähler
- 📤 Direktes Senden an den Slicer, mit einer Spulenauswahl, um das richtige Filament direkt im Sendedialog zuzuweisen, oder Upload zum Drucker
- 👀 **Schnellvorschau** (Gewicht, geschätzte Druckzeit) direkt im Sendedialog, vor der Bestätigung
- 🛡️ **Erweiterte Prüfung vor dem Druck**: warnt, wenn die zugewiesene Spule getrocknet werden sollte, wenn das Filament abrasiv ist (gehärtete Stahldüse empfohlen) oder wenn für diesen Drucker keine Kalibrierung existiert
- 🔁 **Drucken wie beim letzten Mal**: aus dem Verlauf öffnet ein Klick den Sendedialog erneut mit demselben Drucker, Profil und derselben Spule
- 🎛️ **Kalibrierungen**: Flow, Pressure Advance, Temperaturen … pro Filament und Drucker speichern, im Sendedialog wieder abrufbar
- 👥 **Leichter Kollaborationsmodus**: sehen Sie, ob ein anderes verbundenes Gerät bereits eine Datei ansieht, und eine Warnung verhindert, dass dieselbe Datei versehentlich zweimal an den Slicer gesendet wird

### 🧵 Filamentverwaltung
- 🔗 **Spoolman**-Integration (Server zur Spulenverwaltung), mit automatischer Erkennung in Ihrem Netzwerk
- 🟠 **Bambu Lab AMS**-Unterstützung (Slot-Auslesung)
- 🟢 **Creality CFS**-Unterstützung
- 🐯 **TigerTag**-Integration (NFC/RFID-Spulenerkennung): melden Sie sich an, um Ihre TigerTag-Spulen im Inventar zu sehen, oder lassen Sie Stellio eine bestehende TigerTag-Studio-Sitzung automatisch übernehmen — schreibgeschützt, ändert Ihr TigerTag-Inventar nie
- ⚪ Manuelle Spulen
- 📉 Automatische Verbrauchsverfolgung beim Senden an den Slicer, mit Kompatibilitätsprüfung vor dem Druck (genug Material?)
- 🔔 **Warnung bei niedrigem Bestand** beim Start, mit Direktlink zum Nachkauf
- 💨 **Spulentrocknung**: Trocknungsprotokoll, Status (trocken / muss getrocknet werden) je nach Material, empfohlene Temperatur und Dauer sowie Erinnerungen in den Benachrichtigungen
- 📈 **Spulenübersicht**: Drucke, Gramm, Kosten und nicht erfasste Differenz im Datenblatt jeder Spule

### 📥 Download von Plattformen
- 🟠 **Printables** (GraphQL-API)
- 🟢 **MakerWorld** (zweistufiger Bambu-Lab-Login)
- 🔵 **Thingiverse** (via API-Schlüssel)
- 📁 Direkter Download in Ihre konfigurierten Quellen
- 🆕 **Erkennung neuer Versionen**: Stellio prüft täglich, ob heruntergeladene Modelle (Printables, MakerWorld, Thingiverse) aktualisiert wurden
- 🛒 **Nützliche Links**: Shops, Hersteller, 3D-Modell-Seiten und Ressourcen in einklappbaren Abschnitten

### 🧩 Erweiterte Werkzeuge
- 🎨 **Automatisches Nesting** auf dem Druckbett (rectpack oder reale Silhouette via shapely)
- 🔧 **Mesh-Reparatur** (trimesh + pymeshfix) mit **Vorher/Nachher-Vergleich** (Wasserdichtheit, Dreiecke, Eckpunkte, Größe)
- 🔄 **Formatkonverter** (STL ↔ 3MF ↔ OBJ)
- 🛡️ **Integritätsprüfung** (beschädigte/fehlende Dateien)
- 💰 **Druckkostenberechnung**: Material, Strom, Maschinenverschleiß (pro Stunde), Fixkosten, Marge in % und Stückzahl — Stückpreis und Gesamtpreis auf den Cent genau
- 🧾 **PDF-Angebote**: aus der Kostenberechnung erzeugt, mit anpassbarem Kunden, Bezeichnung und Notizen; konfigurierbarer Angebotskopf (Name/Firma, Logo, Adresse, Telefon, E-Mail, Website, Steuernummer) und rechtliche Hinweise in der Fußzeile
- 🌱 **Umweltschätzung**: CO₂-Fußabdruck Ihrer Drucke (Material + Strom)
- 📸 **Foto-Galerie der Drucke** (erfolgreich/fehlgeschlagen)
- 🕒 **Verlauf** mit Erfolgs-/Fehlerbewertung (fließt in die KI ein), Schaltflächen **„Datei anzeigen“** und **„Erneut drucken“** in jeder Zeile (mit Erkennung verschobener/gelöschter Dateien) sowie Filtern nach Plattform, Ergebnis (erfolgreich/fehlgeschlagen/teilweise/nicht bewertet) und Zeitraum

### 📈 Berichte & Zuverlässigkeit
- 🧮 **Druckzuverlässigkeit**: Erfolgsquote und Fehlerkosten, geordnet nach Slicer-Profil, Material, Drucker oder Spule
- 🗓️ **Monatsbericht**: Drucke, Erfolgsquote, Filament, Kosten, Fehler und CO₂ des Monats im Vergleich zum Vormonat, als PDF exportierbar

### 🔔 Benachrichtigungen
- 🪟 **Native Windows-Benachrichtigungen**
- 🌐 **Browser-Benachrichtigungen**, aktivierbar für den Zugriff über Raspberry Pi oder Mobilgerät
- 📣 **Push-Benachrichtigungen** (ntfy, Telegram, Discord oder Webhook): Druckende und Fehler werden auch bei geschlossenem Fenster erkannt, dazu Wartungs- und Bestandswarnungen

### 🌐 Fern- und mobiler Zugriff
- 📱 **QR-Code** für den mobilen Zugriff auf Ihre Bibliothek (installierbare PWA)
- 📲 **Android-Begleit-App**: ein eigener QR-Code ermöglicht den Download und die Installation der Stellio-Begleit-APK direkt aus den Einstellungen für den mobilen Zugriff, mit der Möglichkeit, Fotos direkt von einem Druck aus aufzunehmen
- 🌍 **Fernzugriff** via Cloudflare Tunnel (kostenlos, zufällige oder feste URL) oder **eigene Adresse** (Domainname, DynDNS, VPN, Tailscale …), um Cloudflare zu umgehen, mit Rückkehr zu Cloudflare per Klick
- 🔗 Temporäre **Freigabelinks** (24 Std., einmalige Nutzung)

### 👥 Konten & Multi-Instanz
- 🔐 **Lokale Konten** mit Wiederherstellungscode und Geheimfrage: 100 % lokales Zurücksetzen des Passworts, ohne E-Mail oder Internet
- 👤 **Gastkonten mit Lesezugriff**: teilen Sie Bibliothek, Drucker und Bestand ohne jedes Risiko
- 🔄 **Stellio-Instanzen**: andere Installationen im lokalen Netzwerk werden automatisch erkannt und mit einem Klick hinzugefügt (Sie müssen nur deren lokalen Schlüssel eingeben)
- 📨 **Datei an eine andere Instanz senden**: Zielordner auf der Zielinstanz wählbar, die empfangene Datei erscheint sofort in deren Bibliothek
- ✅ **Instanzstatus-Widget** im Dashboard (grünes Häkchen oder rotes Kreuz für jede gespeicherte Instanz)

### 🎨 Anpassung
- 🌓 Themes: Dunkel / Hell / System
- 🎨 Marken-Themes: Stellio, Bambu, Prusa, Voron, Creality
- 🎯 Individuelle Akzentfarbe
- 🌍 **8 Sprachen**: FR, EN, DE, ES, IT, PT, JA, ZH
- 🧲 Navigation per Drag & Drop neu anordnen
- ↩️ **Einstellungen rückgängig machen**: die zuletzt vorgenommene Konfigurationsänderung zurücknehmen

### 💾 Backup & Updates
- 📦 Vollständiger Backup-Export/-Import (.zip)
- 🔄 Automatische Updates von GitHub (`.zip`-Patch — gleicher Mechanismus unter Windows und Raspberry Pi/Linux)
- 🔁 Zuverlässiger Neustart nach einem Update oder nach dem Aktivieren des Debug-Modus, unter Windows und Raspberry Pi/Linux
- 📋 Export des Diagnoseprotokolls (Geheimnisse maskiert)

---

## 🖼️ Screenshots

| | |
|---|---|
| ![Bibliothek](../../library.png) *Bibliothek mit Vorschaubildern* | ![Drucker](../../monitoring.png) *Drucker-Überwachung* |
| ![Slicer](../../slicer.png) *KI-Profilempfehlung* | ![Nesting](../../nesting.png) *Automatisches Nesting* |

---

## 🚀 Installation

### 🪟 Windows (empfohlen)

1. Laden Sie den neuesten Installer von [Releases](https://github.com/stellio-app/stellio/releases) herunter
2. Führen Sie `Stellio-Setup.exe` aus
3. Fertig! 🎉

### 🐧 Raspberry Pi / Linux

Läuft im **Headless-Server-Modus** (ohne grafische Oberfläche): Stellio läuft im Hintergrund und wird über einen Browser bedient, entweder auf dem Pi selbst oder von jedem Gerät im lokalen Netzwerk.

**Voraussetzungen**: Raspberry Pi 4 oder 5 empfohlen, **64-Bit** Raspberry Pi OS.

```bash
curl -O https://raw.githubusercontent.com/stellio-app/stellio/main/install-pi.sh
chmod +x install-pi.sh
./install-pi.sh
```

Das Skript installiert automatisch:
- Systemabhängigkeiten (`ffmpeg`, `unrar-free`, 3D-Rendering-Bibliotheken)
- eine dedizierte Python-Virtual-Environment
- einen **systemd-Dienst** (`stellio.service`), der Stellio beim Booten startet und bei einem Absturz automatisch neu startet

Nach der Installation ist Stellio unter `http://<pi-ip>:5000` erreichbar.

```bash
sudo systemctl status stellio     # Dienststatus
sudo systemctl restart stellio    # Neustart
sudo journalctl -u stellio -f     # Logs live verfolgen
```

> 💡 **Gleiche Updates wie unter Windows**: Der mit jedem Release veröffentlichte `.zip`-Patch ist auf beiden Plattformen identisch (reiner Quellcode, nichts Kompiliertes). Stellio erkennt und wendet ihn automatisch an und startet den Dienst danach neu — keine manuelle Neuinstallation nötig.
>
> 🎥 Gleiche Funktionen wie die Windows-Version, außer dem nativen Desktop-Fenster (ersetzt durch Browserzugriff) und der lokalen Ollama-KI, die ein einigermaßen leistungsfähiges Modell benötigt, um auf einem Pi gut zu laufen — weisen Sie `ollama_url` bei Bedarf in den Einstellungen auf einen entfernten Ollama-Server.

### Unterstützte Slicer

Stellio erkennt automatisch:
- ✅ OrcaSlicer
- ✅ Bambu Studio
- ✅ PrusaSlicer / SuperSlicer
- ✅ Ultimaker Cura
- ✅ Creality Print

### Drucker

| Typ | Protokoll | Funktionen |
|---|---|---|
| OctoPrint / PrusaLink | HTTP-API | Überwachung, Upload, Kamera |
| Klipper/Moonraker | HTTP-API | Überwachung, Upload, Kamera, exakte Stunden |
| Bambu Lab | MQTT (Cloud + LAN) | Echtzeit-Überwachung, AMS, Kamera (JPEG A1/P1, RTSPS X1/X2/H2), SSDP-Autoerkennung |
| Creality | WebSocket | Überwachung, CFS, UDP-Autoerkennung |
| FlashForge | Proprietäre API | Überwachung, UDP-Autoerkennung |
| Elegoo | SDCP über WebSocket | Überwachung, UDP-Autoerkennung |

---

## 🛠️ Technologie

| Komponente | Technologie |
|---|---|
| Backend | Python 3.8+, Flask, Waitress |
| Frontend | HTML5, CSS3, reines JavaScript |
| Datenbank | SQLite (WAL-Modus) |
| Desktop | pywebview (Windows) / Headless-Browser-Modus (Raspberry Pi, Linux) |
| 3D-Rendering | PyRender, numpy-CPU-Rasterizer, Three.js |
| Mesh & Nesting | trimesh, pymeshfix, shapely, rectpack |
| KI | Ollama (lokal) |
| Netzwerk | paho-mqtt, smbclient, requests |
| Verschlüsselung | cryptography (AES, zufälliger IV pro Aufruf) |
| Archive | zipfile, rarfile, py7zr, tarfile |

---

## 📖 Dokumentation

### Tastenkürzel

| Kürzel | Aktion |
|---|---|
| `Strg+K` | Befehlspalette |
| `Strg+F` | Suche |
| `Strg+N` | Neuer Download |
| `Strg+,` | Einstellungen |
| `Strg+Z` | Letzte Löschung rückgängig machen (5-Minuten-Papierkorb) |
| `Alt+1-8` | Schnellnavigation |
| `Umschalt+Klick` | Dateibereich auswählen |
| `↑ ↓ ← →` + `Enter` | In der Bibliothek navigieren und Dateien öffnen |
| `F` | Favoriten umschalten |
| `T` | Tag-Manager |
| `?` | Hilfe zu Tastenkürzeln |
| `Esc` | Modal schließen / Suche leeren |

### Projektstruktur

```
stellio/
├── main.py             # Flask- + Desktop-Backend
├── script.js           # Frontend-JavaScript
├── index.html          # Hauptoberfläche
├── style.css           # Styles
├── launcher.py         # Schlanker Launcher / Runtime-Bootstrap
├── check_deps.py       # Selbstheilende Abhängigkeitsprüfung
├── worker.py           # Hintergrund-Worker (Vorschaubilder, Scans)
├── assets/             # Logos, Icons
├── languages/          # Übersetzungsdateien (JSON)
├── apk/                # Paket der Android-Begleit-App
├── docs/               # Dokumentation, Datenschutzrichtlinie, übersetzte READMEs
├── requirements.txt    # Python-Abhängigkeiten
└── install-pi.sh       # Installationsskript für Raspberry Pi / Linux (systemd-Dienst)
```

Eine Idee? [Erstellen Sie ein Issue](https://github.com/stellio-app/stellio/issues)!

---

## 🤝 Mitwirken

Beiträge sind willkommen! 🎉

1. **Forken** Sie das Projekt
2. Erstellen Sie Ihren Branch (`git checkout -b feature/TollesFeature`)
3. Committen Sie Ihre Änderungen (`git commit -m 'TollesFeature hinzugefügt'`)
4. Pushen Sie den Branch (`git push origin feature/TollesFeature`)
5. Öffnen Sie einen **Pull Request**

### Richtlinien
- Halten Sie sich an den bestehenden Code-Stil
- Fügen Sie Kommentare auf Französisch oder Englisch hinzu
- Testen Sie Ihre Änderungen nach Möglichkeit unter Windows
- Aktualisieren Sie bei Bedarf die Dokumentation

### Einen Fehler melden

Nutzen Sie die Bug-Report-Vorlage und geben Sie an:
- Stellio-Version
- Betriebssystem
- Schritte zur Reproduktion
- Fehlerprotokolle (exportierbar über Einstellungen → Diagnose)

---

## 📜 Lizenz

Dieses Projekt steht unter der **GNU Affero General Public License v3.0** — siehe die Datei [LICENSE](../../LICENSE) für Details.

> 💡 **Kurz gesagt**: Sie dürfen diese Software frei kopieren, verändern und weitergeben. Wenn Sie Stellio verändern oder damit einen netzwerkbasierten Dienst anbieten, müssen Sie den vollständigen Quellcode unter derselben AGPLv3-Lizenz veröffentlichen.

---

## 🔒 Datenschutz

Stellio ist local-first: Ihre Daten bleiben auf Ihrem Gerät, standardmäßig wird nichts an externe Server gesendet oder gesammelt. Details finden Sie in unserer [Datenschutzrichtlinie](../privacy/PRIVACY.md).

---

## 🔏 Code-Signing-Richtlinie

Die unter [Releases](https://github.com/stellio-app/stellio/releases) veröffentlichten Windows-Executables sind digital signiert. Details zu unserem Signaturprozess und dem Schutz des privaten Schlüssels finden Sie in [CODE_SIGNING_POLICY.md](../../CODE_SIGNING_POLICY.md).

---

## 🙏 Danksagungen

- [Ollama](https://ollama.com/) für lokale KI
- [Flask](https://flask.palletsprojects.com/) für das Backend
- [Three.js](https://threejs.org/) für 3D-Rendering im Web
- [trimesh](https://github.com/mikedh/trimesh) für die Mesh-Verarbeitung
- [Spoolman](https://github.com/Donkie/Spoolman) für die Verwaltung von Filamentspulen
- [TigerTag](https://tigersystem.io) für die NFC/RFID-Filamenterkennung
- Der Maker-Community für Feedback und Vorschläge
- Allen Mitwirkenden ❤️

---

## 📞 Kontakt & Support

- 🐛 **Fehler melden**: [GitHub Issues](https://github.com/stellio-app/stellio/issues)
- 💡 **Funktionswunsch**: [GitHub Discussions](https://github.com/stellio-app/stellio/discussions)
- 📧 **E-Mail**: contact@stellio-app.com
- 🌐 **Website**: [stellio-app.com](https://stellio-app.com)

---

## ⭐ Projekt unterstützen

Wenn Ihnen Stellio nützlich ist, können Sie:
- ihm einen **Stern** ⭐ auf GitHub geben
- das Projekt in Ihrem Umfeld teilen
- [Code beitragen](#-mitwirken) oder Übersetzungen liefern
- Fehler melden, um die App zu verbessern
- Die Entwicklung mit einer kleinen Spende auf Ko-fi unterstützen ☕

<p align="center">
  <a href="https://ko-fi.com/E6J828RYVD">
    <img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="Stellio auf Ko-fi unterstützen">
  </a>
</p>

---

<p align="center"><strong>Mit ❤️ für die Maker-Community gemacht</strong></p>

<p align="center">
  <a href="https://github.com/stellio-app/stellio">⭐ Repo mit Stern versehen</a> •
  <a href="https://github.com/stellio-app/stellio/issues">🐛 Fehler melden</a> •
  <a href="https://github.com/stellio-app/stellio/discussions">💡 Funktion vorschlagen</a>
</p>
