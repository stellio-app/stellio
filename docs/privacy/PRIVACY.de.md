# Datenschutzerklärung

**Letzte Aktualisierung:** 1. September 2026  
**Anwendung:** Stellio  
**Website:** [stellio-app.com](https://stellio-app.com)  
**Repository:** [github.com/stellio-app/stellio](https://github.com/stellio-app/stellio)

## 1. Einleitung
Willkommen bei der Datenschutzerklärung von Stellio. Stellio ist eine Anwendung zur Verwaltung von 3D-Dateien und 3D-Druck. Diese Richtlinie beschreibt, wie wir Daten verarbeiten.

Unsere grundlegende Philosophie ist einfach: **Ihre Daten bleiben bei Ihnen. Alles läuft lokal.**

## 2. Grundprinzip: "Local-First"
Standardmäßig sammelt, überträgt oder speichert Stellio **keine Daten** auf externen Servern. Alle Ihre 3D-Dateien (STL, 3MF, OBJ), Ihre Druckermodelle, Druckverlauf, Tags und Einstellungen werden ausschließlich auf Ihrem eigenen Gerät (Windows, Raspberry Pi oder Linux) in einer lokalen SQLite-Datenbank gespeichert.

## 3. Lokal gespeicherte Daten
Folgende Elemente werden nur auf Ihrem Gerät gespeichert:
- Ihre 3D-Dateibibliothek und deren Metadaten (Tags, Beschreibungen, Statistiken).
- Lokal generierte 3D-Thumbnails (über PyRender oder Matplotlib).
- Ihre Drucker- und Slicer-Konfigurationen.
- Ihre API-Schlüssel und Anmeldedaten (lokal gespeichert und über AES-CFB verschlüsselt).
- Druckverlauf und zugehörige Fotos.
- Aktivitätsprotokolle zur Diagnose.

## 4. Interaktionen mit Drittanbieterdiensten (Optional)
Um zu funktionieren, können bestimmte *optionale* Funktionen von Stellio mit externen Diensten kommunizieren. Sie behalten die volle Kontrolle über die Aktivierung dieser Funktionen:

- **Automatische Updates**: Stellio kann GitHub-Repositories (`github.com/stellio-app/stellio`) abfragen, um die Verfügbarkeit neuer Versionen zu prüfen. Bei dieser Prüfung werden keine persönlichen Identifikatoren übertragen.
- **3D-Modell-Plattformen**: Wenn Sie die Download-Funktion verwenden, verbindet sich Stellio direkt mit den APIs von Printables, MakerWorld oder Thingiverse unter Verwendung **Ihrer eigenen Anmeldedaten oder API-Schlüssel**. Diese Informationen werden niemals an Stellio-Server gesendet.
- **Druckerverwaltung**: Stellio kommuniziert direkt mit Ihren lokalen/Netzwerk-Druckern oder Druckservern (OctoPrint, Klipper/Moonraker, Bambu Lab über MQTT). Diese Kommunikation bleibt auf Ihr lokales Netzwerk beschränkt, es sei denn, Sie konfigurieren ausdrücklich den Fernzugriff.
- **Fernzugriff (Cloudflare Tunnel)**: Wenn Sie den Fernzugriff aktivieren, wird Ihr Datenverkehr sicher über Cloudflare-Server geleitet. Bitte beachten Sie die [Datenschutzerklärung von Cloudflare](https://www.cloudflare.com/privacypolicy/) für Details.
- **Künstliche Intelligenz (Ollama)**: Standardmäßig läuft die KI (Ollama) lokal auf Ihrem Gerät. Wenn Sie sich dafür entscheiden, eine entfernte Ollama-URL in den Einstellungen zu konfigurieren, werden Ihre Anfragen (Modellbeschreibungen, semantische Suche) an diesen von Ihnen gewählten Drittanbieter-Server gesendet.
- **Spoolman**: Wenn Sie Stellio mit einem externen Spoolman-Server verbinden, werden Filament-Verbrauchsdaten an diesen von Ihnen kontrollierten oder gewählten Server gesendet.

## 5. Datensicherheit
- **Verschlüsselung**: Sensible Daten (wie API-Schlüssel oder Druckerpasswörter) werden lokal mit dem AES-CFB-Algorithmus verschlüsselt.
- **Diagnose**: Wenn Sie auf einen Fehler stoßen, können Sie ein Diagnoseprotokoll aus den Einstellungen exportieren. Stellio maskiert automatisch Geheimnisse und sensible Informationen vor dem Export. Wir sammeln diese Protokolle nicht automatisch.

## 6. Ihre Rechte
Da alle Ihre Daten lokal gespeichert sind, haben Sie die absolute Kontrolle darüber:
- Sie können jederzeit alle Ihre Daten über die Backup-Funktion exportieren (`.zip`).
- Sie können jede Datei, jeden Verlaufseintrag oder jede Einstellung direkt über die Oberfläche löschen.
- Die Deinstallation der Anwendung entfernt die Programmdateien, aber Sie müssen den lokalen Datenordner manuell löschen, wenn Sie Ihren Verlauf und Ihre Datenbank dauerhaft löschen möchten.

## 7. Änderungen dieser Richtlinie
Wir können diese Datenschutzerklärung aktualisieren, um Änderungen in Stellios Funktionen oder gesetzlichen Verpflichtungen widerzuspiegeln. Das Datum "Letzte Aktualisierung" oben in diesem Dokument wird entsprechend überarbeitet. Wir empfehlen Ihnen, diese Seite regelmäßig zu überprüfen.

## 8. Kontakt
Wenn Sie Fragen oder Bedenken bezüglich dieser Datenschutzerklärung oder der Verwaltung Ihrer Daten haben, können Sie uns kontaktieren:
-  E-Mail: [contact@stellio-app.com](mailto:contact@stellio-app.com)
- 🐛 Fehlerbericht: [GitHub Issues](https://github.com/stellio-app/stellio/issues)
- 💬 Diskussionen: [GitHub Discussions](https://github.com/stellio-app/stellio/discussions)

---
*Dieses Projekt ist Open-Source. Sie sind eingeladen, den Quellcode in unserem GitHub-Repository zu prüfen, um die Einhaltung dieser Richtlinie selbst zu verifizieren.*