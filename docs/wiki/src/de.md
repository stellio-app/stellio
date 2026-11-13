@@@ Home | Startseite
# Stellio-Wiki
{{img:dashboard}}


**Stellio** ist der 3D-Dateimanager für Maker und 3D-Drucker-Besitzer. Er bündelt Ihre Bibliothek (STL, 3MF, OBJ, STEP, PLY, AMF), automatisiert wiederkehrende Aufgaben und fügt sich in Ihren Druck-Workflow ein.

> 🔒 **Philosophie**: Ihre Daten bleiben bei Ihnen. Alles läuft lokal; standardmäßig verlässt nichts Ihren Rechner.

## Wo anfangen?

| Ich möchte … | Seite |
|---|---|
| Stellio installieren | [Installation](de-Installation) |
| Erste Schritte machen | [Erste Schritte](de-Getting-Started) |
| Meine 3D-Dateien verwalten | [Bibliothek](de-Library) |
| Meine Drucker verbinden | [Drucker](de-Printers) |
| Meine Spulen verfolgen | [Filament](de-Filament) |
| Modelle herunterladen | [Downloads](de-Downloads) |
| KI und S.O.S Print nutzen | [Künstliche Intelligenz](de-AI) |
| Kosten, Angebote, Rechnungen berechnen | [Kosten und Verwaltung](de-Costs-and-Management) |
| Vom Smartphone zugreifen | [Fern- und mobiler Zugriff](de-Remote-Access) |
| Auf Raspberry Pi / Proxmox installieren | [Server-Edition](de-Server-Edition) |
| Einstellen, sichern, meine Daten verstehen | [Einstellungen und Daten](de-Settings-and-Data) |
| Ein Problem lösen | [Fehlerbehebung](de-Troubleshooting) |
| Zum Projekt beitragen | [Mitwirken](de-Contributing) |

## Nützliche Links

- 🌐 Website: [stellio-app.com](https://stellio-app.com) — ▶ [Live-Demo (nur Lesezugriff)](https://demo.stellio-app.com)
- 📦 [Downloads (Releases)](https://github.com/stellio-app/stellio/releases)
- 🐛 [Fehler melden](https://github.com/stellio-app/stellio/issues) · 💡 [Idee vorschlagen](https://github.com/stellio-app/stellio/discussions) · 💬 [Discord](https://discord.gg/ySxpHvS6bd)
- 📜 Lizenz **AGPL v3**

@@@ Installation | Installation
# Installation

| Plattform | Datei / Methode | Modus |
|---|---|---|
| 🪟 Windows | `Stellio-Setup-<version>.exe` | Desktop-App |
| 🪟 Windows portabel | `Stellio-v<version>-portable-win64.zip` | Desktop-App, ohne Installation |
| 🍎 macOS | `.dmg` (Apple Silicon `arm64` oder Intel `x86_64`) | Desktop-App |
| 🐧 Linux | `Stellio-v<version>-x86_64.AppImage` | Desktop-App |
| 🍓 Raspberry Pi / Linux | `install-pi.sh` | Server (Browser) |
| 🖥️ Proxmox VE | `stellio-lxc.sh` | LXC-Container mit einem Befehl |
| 📲 Android | Begleit-APK | Siehe [Fern- und mobiler Zugriff](de-Remote-Access) |

Alle Dateien finden Sie auf der Seite [Releases](https://github.com/stellio-app/stellio/releases), jeweils mit einer `.sha256`-Prüfsumme.

## Windows

1. Laden Sie das Installationsprogramm von den Releases herunter.
2. Starten Sie `Stellio-Setup-<version>.exe`.
3. Fertig.

**Portable Version**: an beliebiger Stelle entpacken (Festplatte, USB-Stick) und `Stellio.exe` starten. Ihre Daten bleiben im Ordner `data` neben der ausführbaren Datei (behalten Sie die Datei `portable.flag`).

> ⚠️ Das Installationsprogramm ist **nicht signiert**: Windows SmartScreen kann eine Warnung anzeigen. Prüfen Sie bei Bedarf die `.sha256`; die integrierte Aktualisierung kontrolliert sie vor der Installation.

## macOS

Öffnen Sie die `.dmg` und ziehen Sie Stellio nach „Programme". Wählen Sie die zu Ihrem Mac passende Datei: `arm64` (M1, M2, M3 …) oder `x86_64` (Intel). Die Builds sind nicht notariell beglaubigt: Beim ersten Start Rechtsklick → **Öffnen**.

> Bleibt der Bildschirm weiß: Port 5000 ist möglicherweise vom macOS-„AirPlay-Empfänger" belegt. Stellio wählt dann automatisch einen anderen freien Port. Siehe [Fehlerbehebung](de-Troubleshooting).

## Linux (AppImage)

```bash
chmod +x Stellio-v*-x86_64.AppImage
./Stellio-v*-x86_64.AppImage
```
Das AppImage enthält seine Update-Informationen (`.zsync`).

## Raspberry Pi / Linux-Server

Modus **Server ohne Oberfläche**: Stellio läuft im Hintergrund und wird über einen Browser bedient. Details unter [Server-Edition](de-Server-Edition).

```bash
curl -O https://raw.githubusercontent.com/stellio-app/stellio/main/install-pi.sh
chmod +x install-pi.sh
./install-pi.sh
```

## Proxmox VE

In der **Shell des Proxmox-Hosts**:
```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/stellio-app/stellio/main/stellio-lxc.sh)"
```
Details unter [Server-Edition](de-Server-Edition).

## Aktualisierungen

- **Desktop**: Stellio erkennt neue Versionen auf GitHub und spielt einen `.zip`-Patch ein (gleicher Mechanismus unter Windows, macOS und Linux). Das Dashboard-Widget „Update" öffnet das Update-Fenster.
- **Server**: dieselbe automatische Aktualisierung oder `update-stellio` (LXC-Container) / `./install-pi.sh` (Raspberry Pi).
- Beim ersten Start jeder Version werden fehlende Module (PDF-Angebote, Tabellenimport, Benachrichtigungen …) automatisch heruntergeladen.

@@@ Getting-Started | Erste Schritte
# Erste Schritte
{{img:library}}


## 1. Erster Start
Stellio zeigt eine **geführte Tour** und eine Checkliste „Erste Schritte". Die Tour lässt sich jederzeit in den Einstellungen neu starten.

## 2. Konto erstellen
Konten sind **lokal**: Passwort + Wiederherstellungscode + Geheimfrage. Das Zurücksetzen des Passworts erfolgt zu 100 % lokal, ohne E-Mail und ohne Internet.

## 3. Quellen hinzufügen
Eine **Quelle** ist ein Ordner oder eine Freigabe mit Ihren Modellen:
- lokaler Ordner, einzelne Datei, **SMB**- oder **NFS**-Freigabe;
- auf Ihrem Computer erkannte 3D-Ordner werden **vorgeschlagen** und mit einem Klick hinzugefügt;
- für jede Quelle legen Sie fest, welche Dateitypen angezeigt werden.

Stellio durchsucht dann Ihre Dateien und erzeugt im Hintergrund 3D-Vorschaubilder.

## 4. Drucker hinzufügen (optional)
Öffnen Sie die Seite **Drucker**: Die Netzwerkerkennung schlägt gefundene Geräte vor. Siehe [Drucker](de-Printers).

## 5. Slicer wählen
Stellio erkennt Ihre installierten Slicer automatisch (OrcaSlicer, Bambu Studio, PrusaSlicer, Cura …). Die Senden-Schaltfläche öffnet die Datei direkt im Slicer.

## Dashboard
Die Startseite zeigt laufende Drucke, niedrigen Bestand, letzte Drucke und letzte Dateien. Die **Widgets** (etwa zwanzig) lassen sich per Drag & Drop neu anordnen und ausblenden: laufende Drucke, niedriger Bestand, letzte S.O.S Print, Vorschläge, Stellio-Instanzen, abgeschlossene Projekte, Galerie, Angebote …

## Werkzeuge für den Alltag
- **Befehlspalette** `Strg+K`: navigieren, Aktion ausführen, Datei, Tag, Spule oder Profil finden.
- **Benachrichtigungszentrum** (Glocke): Druck beendet, Fehler, Wartung, niedriger Bestand, Spulentrocknung.
- **Schwebendes Widget** mit dem Fortschritt des aktuellen Drucks, auf jeder Seite sichtbar.
- **Tastenkürzel**: siehe [Einstellungen und Daten](de-Settings-and-Data).

@@@ Library | Bibliothek
# Bibliothek
{{img:library}}


## Quellen und Vorschaubilder
- Mehrere Quellen: lokale Ordner, Dateien, SMB-/NFS-Freigaben.
- **Automatische 3D-Vorschaubilder** (PyRender oder CPU-Ersatzrenderer) mit vergrößerter Vorschau beim Überfahren.
- Die Erzeugung **pausiert, sobald Sie die App benutzen**, und läuft danach weiter.
- Einstellung **Vorschaubild-Leistung**: Automatisch / Eco / Normal / Schnell.
- Formate: STL, 3MF (auch Mehrplatten und PrusaSlicer), OBJ, STEP/STP, PLY, AMF (für Slicer, die sie nicht lesen können, in STL umgewandelt) sowie direkt durchsuchbare Archive (ZIP, RAR, 7z, TAR).

## Organisieren
- Farbige **Tags** mit automatischer KI-Vergabe; mehrere Dateien mit einem Klick taggen.
- **Favoriten**, erweiterte Filter (Typ, Größe, Gewicht, Druckstatus), **gespeicherte Filter**.
- Statusfilter: „An Slicer gesendet", „Bereits gedruckt", „Bereits erfolgreich", „Bereits fehlgeschlagen".
- **Filter „Filamentbestand"**: zeigt nur Dateien, die mit Ihren vorhandenen Spulen druckbar sind.
- Sortierung, Suche und Filter werden beim erneuten Öffnen **gemerkt**.
- Warteschlange **„Bald drucken"**, umsortierbar, an den Slicer sendbar.
- **Mehrfach umbenennen** (Suchen/Ersetzen, Präfix, Suffix, Nummerierung) mit Vorschau.
- **Löschen rückgängig machen** (`Strg+Z`) dank 5-Minuten-Papierkorb; gilt auch für Tags, Projekte und Quellen.
- Schnelle Auswahl: `Umschalt+Klick` für einen Bereich, Pfeiltasten + `Enter`.
- **Duplikaterkennung** (exakt und ähnliche Geometrie).
- **Modellherkunft**: Quelllink, Autor, Lizenz, Notizen, Download-Datum.
- **Drag & Drop** von 3D-Dateien aus dem Datei-Explorer, auch im Browser.

## Suche
- Klassische Suche und **semantische KI-Suche** („Ich suche eine Halterung für …") mit gemerkten letzten Suchen.
- **Intelligente Sammlungen**.

## Projekte / Baugruppen
Mehrere Dateien für ein Objekt gruppieren.
- **Mehrplatten**-3MF: Beim Hinzufügen zu einem Projekt wird es in ein 3MF pro Platte aufgeteilt (6 Platten = 6 Dateien), abgelegt in einem versteckten Ordner.
- Aktion **„Platten aufteilen"** im ⋯-Menü einer Datei.
- Projektkarte: Klick auf das Vorschaubild = 3D-Viewer; Filter „Alle / Laufend / Abgeschlossen" wird gemerkt; **Projektkosten** mit einer Schaltfläche.

{{img:projects}}

## 3D-Viewer und Werkzeuge
- **3D-Viewer** (Three.js, funktioniert offline), Navigation zwischen Platten.
- **Automatische Bauplatten-Anordnung** (rectpack oder echte Silhouette mit shapely).
- **Netzreparatur** (trimesh + pymeshfix) mit Vorher-Nachher-Vergleich.
- **Konverter** STL ↔ 3MF ↔ OBJ.
- **Druckbarkeitsanalyse** (Überhänge) und **vorgeschlagene Ausrichtungen**.
- **Integritätsprüfung** (beschädigte oder fehlende Dateien).
- Detaillierte **Statistiken** (Formate, Plattformen, Profilzuverlässigkeit).

{{img:viewer}}

## Verlauf und Fotos
- **Verlauf** nach Wochen gegliedert, mit Bewertung Erfolg/Fehlschlag (speist die KI), Schaltflächen **Datei anzeigen** und **Erneut drucken**, Filter nach Plattform, Ergebnis und Datum.
- **Druckfoto-Galerie**. Das Foto am Druckende wird danach mit einem Klick auf *Erfolgreich* oder *Fehlgeschlagen* gesetzt.
- **Meine G-Codes**: mit einer Datei verknüpfte G-Codes, Download und Schaltfläche **Im Slicer öffnen**.
- **Sicherung** der Bibliothek: siehe [Einstellungen und Daten](de-Settings-and-Data).

@@@ Printers | Drucker
# Drucker
{{img:printers}}


## Unterstützte Marken

| Marke | Modelle | Verbindung |
|---|---|---|
| **Bambu Lab** | X1/X1C/X1E, X2D, P1P/P1S, P2S, A1/A1 mini, H2D/H2S/H2C | MQTT (LAN + Cloud): Überwachung, AMS, Kamera, SSDP-Erkennung |
| **Prusa** | MK4, MK3.9, MK3.5, MINI+, XL, CORE One | PrusaLink (HTTP) |
| **Creality** | Serien K1/K2, Ender-3 V3, Hi | WebSocket: Überwachung, CFS, UDP-Erkennung |
| **Elegoo** | Centauri Carbon 1 & 2, Resin-Serien Saturn/Mars | SDCP (WebSocket) |
| **FlashForge** | Adventurer 5M/5M Pro, AD5X | Proprietäre API |
| **Klipper / Moonraker** | Jede Klipper-Maschine (Voron …) | HTTP: Überwachung, Upload, Kamera, genaue Stunden |
| **OctoPrint** | Jeder über OctoPrint gesteuerte Drucker | HTTP |

Andere Modelle mit demselben Protokoll funktionieren in der Regel. Sagen Sie uns auf GitHub, ob Ihres läuft.

## Drucker hinzufügen
- **Automatische Erkennung** im lokalen Netzwerk (SSDP, UDP-Broadcast, gezielte Abfragen): erkannte Drucker werden mit einem Klick hinzugefügt.
- Andernfalls manuelle Eingabe (Typ, Modell, Adresse, Zugangsschlüssel).
- Geben Sie das **Bauvolumen** (X, Y, Z) an: Stellio warnt vor dem Senden, wenn das Teil zu groß ist.

## Überwachung
- Temperatur, Fortschritt, Live-Kamera; Vorschaubild und Name der aktuellen Datei auf der Karte.
- Automatischer Druckstundenzähler.
- **Schwebendes Fortschritts-Widget**; es sitzt links neben dem Pfeil „nach oben", wenn dieser angezeigt wird.

## An Slicer / Drucker senden
- Sendefenster mit **Schnellvorschau** (Gewicht, geschätzte Zeit), **Spulenauswahl** und abgerufenen Kalibrierungen.
- **Prüfung vor dem Druck**: Spule muss getrocknet werden, abrasives Filament (gehärtete Stahldüse empfohlen), fehlende Kalibrierung, Bauvolumen, genug Material.
- **Erneut drucken wie beim letzten Mal** aus dem Verlauf.
- **Leichter Mehrbenutzermodus**: warnt, wenn ein anderes Gerät die Datei ansieht oder vor einem doppelten Senden.
- **Im Slicer öffnen** aus „Meine G-Codes".

## Während des Drucks
- **Smarte Steckdose** (Shelly, Tasmota, Home Assistant): Stellio liest die Watt und speichert den realen Verbrauch (kWh) und die Kosten.
- **Realer Filamentverbrauch**, nach dem Druck erfasst.
- **Foto am Druckende**, aufgenommen bei **100 %** (das Teil liegt noch auf dem Bett), ein einziges Foto zur Bewertung *Erfolgreich/Fehlgeschlagen*.
- **KI-Fehlerüberwachung** (Ollama mit Bildmodell, 100 % lokal): Alarm bei Spaghetti oder abgelöstem Teil, **nie ein automatischer Stopp**.
- Automatischer **Zeitraffer** (Kamera → MP4-Video, benötigt ffmpeg).
- **Statuslinks zum Teilen** (nur Lesezugriff).

## Wartung
- **Vorausschauende Wartung** mit markenspezifischen Aufgaben.
- **Verschleißteile** (Düsen, Platten, Riemen …) mit Bestandswarnungen, verknüpft mit Wartungsaufgaben.
- **Kalibrierungen** (Fluss, Pressure Advance, Temperaturen) pro Filament und Drucker.

@@@ Filament | Filament
# Filament

## Bestandsquellen
| Quelle | Details |
|---|---|
| **Spoolman** | Automatische Erkennung im Netzwerk. Stellio **schreibt den Verbrauch nicht mehr** dorthin (vermeidet doppelte Zählung). |
| **Manuell** | Von Hand erfasste Spulen, Excel-/CSV-Import. |
| **TigerTag** | NFC-/RFID-Identifikation. Anmeldung mit E-Mail und Passwort (nur ein verschlüsseltes Token wird gespeichert) oder Übernahme einer TigerTag-Studio-Sitzung. **Nur Lesezugriff.** |
| **OpenPrintTag** | Offener NFC-Tag-Standard: Import/Export von `.bin`-Dateien, Lesen/Schreiben über die Android-App, verbrauchtes Gewicht bleibt aktuell. |
| **Bambu AMS / Creality CFS** | Auslesen der Slots. |

**Open Filament Database**: Spule nach Marke, Material und Farbe suchen und mit einem Klick anlegen (Gewicht, Durchmesser und Dichte vorausgefüllt).

## Im Alltag
- **Automatischer Verbrauch** beim Senden an den Slicer, mit Kompatibilitätsprüfung (genug Material?).
- **Warnungen bei niedrigem Bestand** beim Start, einstellbare Schwelle, Kästchen „Zu bestellen" und Kauflink.
- **Spule nachkaufen**: zuerst der Shop des Herstellers (Arianeplast, Bambu Lab, Polymaker, eSUN, Sunlu …), dann allgemeine Shops; Lagerbestand wird automatisch geprüft, wenn die Seite es zulässt.
- **Trocknung**: Protokoll, Status (trocken / muss getrocknet werden) je nach Material, empfohlene Temperatur und Dauer, Erinnerungen.
- **Spulenblatt**: Drucke, Gramm, Kosten und nicht erfasste Differenz.

## Wiegen und Prognose
Der Block **Filament wiegen und Prognose** schätzt das **Aufbrauchdatum** jeder Spule anhand des Tagesverbrauchs.
- Das Restgewicht stammt aus einer manuellen Wägung oder von TigerTag.
- TigerTag-Gewichte speisen **nur die Prognose**: Sie erscheinen hier nur für eine Spule, die **bald leer ist** (14 Tage oder weniger). Der Rest steht im Bestand.
- Ein Formular für die manuelle Wägung ist immer verfügbar.

{{img:filament}}

## Verbrauchsprognose
Die Bibliothek kann eine **Nachbestell-Warnung** anzeigen, wenn der Bestand für Ihre Favoriten nicht reicht.

@@@ Downloads | Downloads
# Downloads

Laden Sie Modelle von mehreren Plattformen direkt in Ihre Quellen herunter:

| Plattform | Anmeldung |
|---|---|
| **Printables** | GraphQL-API |
| **MakerWorld** | Zweistufige Bambu-Lab-Anmeldung |
| **Thingiverse** | API-Schlüssel |
| **Nexprint** (Elegoo) | E-Mail und Passwort des Kontos, verschlüsselt gespeichert |
| **Creality Cloud** | In den Einstellungen (verschlüsselte Zugangsdaten; Google-Anmeldung nicht unterstützt) |
| **Snapmaker Space** | Ebenso |

- **Strg+N** öffnet einen neuen Download.
- Die Datei landet in der Quelle Ihrer Wahl, und die **Modellherkunft** (Link, Autor, Lizenz) wird gespeichert.
- **Neue Version**: Stellio prüft täglich, ob heruntergeladene Modelle (Printables, MakerWorld, Thingiverse) aktualisiert wurden.
- **Meine Likes / Meine Kreationen**: verbundene Konten werden bei jedem Desktop-Start getestet (auf dem Server alle 24 h).
- **Nützliche Links**: Shops, Hersteller, Modellseiten und Ressourcen in einklappbaren Abschnitten.

@@@ AI | Künstliche Intelligenz
# Künstliche Intelligenz

## Lokale KI (Ollama)
Standardmäßig läuft die KI **zu 100 % lokal** mit [Ollama](https://ollama.com/). Sie lässt sich deaktivieren.

Funktionen:
- **Automatisches Taggen** und **Beschreibung** von Modellen;
- **Semantische Suche** in natürlicher Sprache;
- **Druckbarkeitsanalyse** und **vorgeschlagene Ausrichtungen**;
- **Slicer-Profilempfehlung** (Geometrie + Erfolgshistorie);
- **Druckzeitschätzung** vor dem Slicen;
- **Fehlerüberwachung** (Bildmodell).

Die Adresse des Ollama-Servers wird in den Einstellungen festgelegt (`ollama_url`): Sie können auf einen leistungsfähigeren entfernten Rechner verweisen (nützlich auf einem Raspberry Pi).

## Online-KI (Server-Edition, optional)
Statt Ollama nutzen Sie **Claude** (Anthropic), **ChatGPT** (OpenAI) oder **Gemini** (Google) mit **Ihrem eigenen API-Schlüssel** (Einstellungen → Künstliche Intelligenz).
- Der Schlüssel wird auf dem Server verschlüsselt und nie an den Browser zurückgesendet.
- Anfragen (Dateinamen, Tags, Beschreibungen, S.O.S-Print-Fotos) gehen an den gewählten Anbieter und werden über Ihren Schlüssel abgerechnet.
- Ollama bleibt die Voreinstellung.

## S.O.S Print
**Adaptive** Diagnose eines Druckfehlers:
1. Sie beschreiben das Problem (bei jedem Schritt ist ein Foto möglich) und, wenn Sie möchten, die verwendeten Einstellungen (Temperaturen, Geschwindigkeiten, Rückzug …).
2. Stellio stellt **eine Frage nach der anderen** (höchstens 4) und grenzt eine Liste von Hypothesen live ein.
3. Es liefert eine **endgültige Diagnose**.

Unterhaltungen werden gespeichert: erneut öffnen oder als gelöst markieren.

> ℹ️ Die Ergebnisse „Erfolgreich / Fehlgeschlagen", die Sie im Verlauf bewerten, verbessern die Empfehlungen.

@@@ Costs-and-Management | Kosten und Verwaltung
# Kosten und Verwaltung
{{img:management}}


## Druckkostenberechnung
Material, Strom, Maschinenverschleiß (pro Stunde), Fixkosten, Marge in % und Menge: Stückpreis und Gesamtpreis auf den Cent genau.
- Die **Standardmarge** stellen Sie einmal unter *Einstellungen → Druckpreise* ein; der Verlauf zeigt den **Verkaufspreis** neben den Kosten, während die Statistiken die echten Kosten nutzen.
- **Projektkosten**: dieselbe Berechnung für alle Dateien eines Projekts.
- **Smarte Steckdose**: Die gemessene Leistung ersetzt die Stromschätzung.
- **CO₂-Fußabdruck** Ihrer Drucke (Material + Strom).

## PDF-Angebote
Aus dem Rechner erzeugt: Kunde, Bezeichnung, Notizen; konfigurierbarer Kopf (Name/Firma, Logo, Adresse, Telefon, E-Mail, Website, Steuernummer) und rechtliche Hinweise in der Fußzeile. Jedes Angebot wird aufbewahrt (PDF-Kopie) und im Widget **Angebote** durchsuchbar.

## Bildschirm „Verwaltung"
Sichtbar, wenn *Kosten-, Angebots- und Rechnungsfunktionen aktivieren* angehakt ist:
- **Kundenangebote**: Ein **Tracking-Link** lässt den Kunden das Angebot online ansehen, annehmen oder ablehnen; die Annahme erzeugt die Druckaufgabe und zeigt Ihre Anzahlungsangaben. **Stellio wickelt keine Zahlung ab.** Links sind immer extern; ist der Fernzugriff aus, bietet der Bildschirm an, ihn mit einem Klick zu aktivieren.
- **Buchhaltung**: monatlicher ZIP-Export (CSV der Dokumente, Rechnungs-PDFs, Summen pro Monat).
- **Bestand fertiger Teile**: Warnschwelle und Nachschub (Aufgabe von Hand oder automatisch erzeugt).

## Werkstatt
- **Auftragswarteschlange** mit echter Marge, Kundenbuch, Zahlungen, Anzahlungsrechnungen und Gutschriften, SMTP-E-Mail, CSV-Export.
- Öffentliche **Kunden-Trackingseite** pro Auftrag, ohne Konto: nie Preis, Marge oder interne Notizen.
- **Intelligente Verteilung**: Stellio schlägt für jede Aufgabe den passendsten Drucker vor (frei, Material geladen, Warteschlange) **und startet nie einen Druck**.
- **Tägliche oder wöchentliche Zusammenfassung** per Benachrichtigung und Push (Aufgaben, Verspätungen, Energie, Spulen, Rechnungen, Bestand).
- **Teilen von Slicer-Profilen** mit einer gekoppelten Instanz.

## Berichte
- **Zuverlässigkeit**: Erfolgsquote und Fehlerkosten nach Profil, Material, Drucker oder Spule.
- **Monatsbericht** im Vergleich zum Vormonat, als PDF exportierbar.
- Teilbarer **Druckbericht** (PNG-Bild) aus dem Verlauf.
- Realer **Energieverbrauch** pro smarter Steckdose.



{{img:stats}}
@@@ Remote-Access | Fern- und mobiler Zugriff
# Fern- und mobiler Zugriff

## Smartphone und Tablet
- **QR-Code** für den mobilen Zugriff auf die Bibliothek (**installierbare PWA**).
- **Android-Begleit-App**: Ein eigener QR-Code (Einstellungen → Mobiler Zugriff) lädt die APK herunter. Sie verwaltet interne und externe Adresse mit automatischem Wechsel, Kopplung per QR, Fotos direkt von einem Druck sowie Lesen/Schreiben von OpenPrintTag-NFC-Tags.
- **Werkstattmodus** im Vollbild für Tablet/Smartphone.

## Fernzugriff
- **Cloudflare Tunnel** (kostenlos, zufällige oder feste Adresse) oder eine **eigene Adresse** (Domainname, DynDNS, VPN, Tailscale …), um Cloudflare zu umgehen, mit Rückkehr zu Cloudflare per Klick.
- Temporäre **Freigabelinks** (24 h, einmalige Nutzung).

## Konten
- **Lokale Konten** mit Wiederherstellungscode und Geheimfrage.
- **Sitzungsbestätigung**: Wird die App mit gespeicherter Sitzung geöffnet, bittet Stellio um Bestätigung des Kontos.
- **Gastkonten mit Lesezugriff**: Bibliothek, Drucker und Bestand risikolos teilen.
- Am PC ist der Browserzugriff auf die Windows-App gesperrt (internes Token): Nutzen Sie das App-Fenster.

## Mehrere Stellio-Instanzen
- Andere Installationen im lokalen Netzwerk werden **erkannt** und mit einem Klick hinzugefügt (lokalen Schlüssel eingeben).
- **Datei senden** an eine andere Instanz, in den Ordner Ihrer Wahl.
- Statuswidget der Instanzen im Dashboard.

## Benachrichtigungen
- Native **Windows**-Benachrichtigungen, **Browser**-Benachrichtigungen (Pi, Smartphone).
- **Push**: ntfy, Telegram, Discord oder Webhook, auch bei geschlossenem Fenster (Druck beendet, Fehler, Wartung, Bestand).

## Hausautomation
- **MQTT / Home Assistant**: Zustandsveröffentlichung und automatische Erkennung; MQTT-Gerät „Stellio" und Sensoren.

@@@ Server-Edition | Server-Edition
# Server-Edition

Die **Server-Edition** wird unter Linux (Raspberry Pi, VM, LXC, Docker) oder mit `STELLIO_HEADLESS=1` aktiv. Windows und macOS behalten die Desktop-App. Stellio läuft im Hintergrund und wird über einen Browser bedient: `http://<ip>:5000`.

## Raspberry Pi / Linux
Voraussetzungen: Raspberry Pi 4 oder 5 empfohlen, **64-Bit**-Raspberry-Pi-OS.

`install-pi.sh` installiert die Systemabhängigkeiten (`ffmpeg`, `unrar`, 3D-Render-Bibliotheken), eine eigene Python-Umgebung und einen **systemd-Dienst** `stellio`, der beim Booten startet und nach einem Absturz neu startet.

```bash
sudo systemctl status stellio
sudo systemctl restart stellio
sudo journalctl -u stellio -f
```
Wenig RAM? Erhöhen Sie den Swap, falls die Installation der Python-Abhängigkeiten scheitert, und starten Sie das Skript erneut.

## Proxmox VE (LXC-Container)
Das Skript `stellio-lxc.sh` bietet **Standard-** oder **erweiterte** Einstellungen (CTID, Kerne, RAM, Festplatte, Bridge, VLAN, DHCP oder feste IP, Speicher, einzubindender Host-Ordner) und dann:
- erstellt es einen **unprivilegierten Debian-12**-Container (2 Kerne, 2 GB RAM, 32 GB Festplatte, Start beim Booten);
- installiert darin Stellio mit `install-pi.sh`;
- zeigt die Adresse `http://<container-ip>:5000` und das Root-Passwort an.

```bash
pct exec <CTID> -- update-stellio              # aktualisieren
pct exec <CTID> -- journalctl -u stellio -f    # Logs
```
- **Nicht interaktiver Modus**: Variablen `var_mode=default var_cpu=4 var_ram=4096 var_disk=16 var_ip=192.168.1.50/24 var_gw=192.168.1.1` (Liste am Anfang des Skripts).
- **Speicher**: `var_choose_storage=1`, `var_storage`, `var_template_storage`.
- **Sprache** des Skripts: `var_lang=de` (fr, en, de, es, pt, it, zh, ja).
- **Quellen**: In diesem Container werden nur **SMB/NFS**-Freigaben angeboten. Mit `var_mount=/host:/mnt/models` ist auch „Lokaler Ordner" erlaubt. Einstellung: `/etc/systemd/system/stellio.service.d/sources.conf` (`STELLIO_ALLOWED_SOURCE_TYPES`).

## Schutzmechanismen (1.0.7)
`install-pi.sh` richtet ein:
- eine **minütliche Prüfung** (`stellio-watchdog`): startet Stellio neu, wenn es nicht mehr antwortet (3 fehlgeschlagene Prüfungen, 3 Minuten Schonfrist nach einem Start), startet es, wenn es gestoppt ist, startet das Netzwerk neu, wenn die IP-Adresse verloren geht, und bereinigt Logs und apt-Cache, wenn weniger als 300 MB Speicher frei sind;
- einen Dienst, der **nie aufgibt**, neu zu starten;
- Obergrenzen **CPU 75 %**, **RAM 75 % (Verlangsamung) / 85 % (harte Grenze)**, niedrige Priorität, und Stellio wird bei Speichermangel zuerst beendet;
- auf **100 MB** begrenzte Logs.

Eingriffe der Prüfung: `journalctl -t stellio-watchdog`. Bestehende Container erhalten all das mit `update-stellio`.

## Besonderheiten der Server-Edition
- ☁️ Optionale **Online-KI** (siehe [Künstliche Intelligenz](de-AI)).
- 📥 **Slicer-Profile**: Stellio sieht die Slicer auf Ihrem PC nicht und verbindet sich nicht mit Slicer-Clouds (Orca Cloud, Bambu Cloud …). Exportieren Sie Ihre Profile (OrcaSlicer: Datei → Exportieren → Preset-Bundle exportieren) und importieren Sie sie unter *Einstellungen → Meine Slicer-Profile*, oder nutzen Sie einen **überwachten Profilordner** (Syncthing, Netzwerkfreigabe, scp …).
- 🐯 **TigerTag**: offizielle Anmeldung mit E-Mail und Passwort; Google-Konto? Legen Sie zuerst über „Passwort vergessen" in der TigerTag-App ein Passwort fest. Ersatz: den Datenordner von TigerTag Studio auf den Server kopieren.
- Nach einer Aktualisierung lädt der Browser automatisch neu.

## Umgebungsvariablen
| Variable | Zweck |
|---|---|
| `STELLIO_HEADLESS` | Erzwingt den Servermodus |
| `STELLIO_PORT` | Port (Standard 5000) |
| `STELLIO_SERVER_URL` | Öffentliche Adresse des Servers |
| `STELLIO_DATA_DIR` | Datenordner |
| `STELLIO_ALLOWED_SOURCE_TYPES` | Erlaubte Quellentypen (`folder,smb,nfs`) |
| `STELLIO_START_MINIMIZED` | Minimiert starten |
| `STELLIO_NO_AUTO_INSTALL` | Deaktiviert die automatische Modulinstallation |

@@@ Settings-and-Data | Einstellungen und Daten
# Einstellungen und Daten

## Darstellung
- **Design**: Dunkel / Hell / System. Standardmäßig **hell**; dunkel nur, wenn das System (oder Sie) es wünscht.
- **Markendesigns**: Stellio, Bambu, Prusa, Voron, Creality; 33 Farbpaletten, eigene Akzentfarbe, einstellbares Hintergrundbild.
- **Barrierefreiheit**: hoher Kontrast, reduzierte Animationen, sichtbarer Tastaturfokus, Textgröße, Farbenblindmodus.
- **8 Sprachen**: fr, en, de, es, it, pt, ja, zh.
- Navigation per Drag & Drop umsortierbar; **letzte geänderte Einstellung rückgängig machen**.

{{img:settings}}

## Tastenkürzel
| Kürzel | Aktion |
|---|---|
| `Strg+K` | Befehlspalette |
| `Strg+F` | Suche |
| `Strg+N` | Neuer Download |
| `Strg+,` | Einstellungen |
| `Strg+Z` | Letztes Löschen rückgängig machen |
| `Alt+1-8` | Schnellnavigation |
| `Umschalt+Klick` | Bereich auswählen |
| `↑ ↓ ← →` + `Enter` | Navigieren und öffnen |
| `F` | Favoriten |
| `T` | Tag-Verwaltung |
| `?` | Hilfe zu Tastenkürzeln |
| `Esc` | Schließen / Suche leeren |

## Wo liegen meine Daten?
| System | Ordner |
|---|---|
| Windows | `%APPDATA%\Stellio` |
| macOS / Linux | `~/.stellio` |
| Windows portabel | `data` neben `Stellio.exe` |
| Benutzerdefiniert | Variable `STELLIO_DATA_DIR` |

Inhalt: Datenbank `stellio.db` (SQLite), Einstellungen `app_settings.json`, Protokoll `stellio.log`, heruntergeladene Module `extra_libs`. Der Code bleibt von den Daten getrennt und wird von einer Aktualisierung nie angetastet.

## Sicherung
- **Vollständiger Export / Import** (.zip) Ihrer Daten.
- Planbare **automatische Sicherungen**.
- 5-Minuten-**Papierkorb**, Vorgangsprotokoll mit Rückgängig.
- Aktualisierungen verlieren nie Daten.

## Protokolle und Diagnose
- Die Standard-Protokollstufe ist **Warnung**; die Datei `stellio.log` wird bei jedem Start neu angelegt.
- **Debug-Modus**: in den Einstellungen aktivieren; er gilt ab dem nächsten Start.
- **Diagnose exportieren** (Einstellungen → Diagnose): Geheimnisse maskiert, integrierte Drucker aufgelistet (Typ, Modell, Status — ohne Name, Adresse oder Schlüssel).
- Block **Stellio-Zustand**: Gesamtzustand der App.

## Vorschläge und Fehler
In der App: **Vorschläge & Fehler** in der Seitenleiste. Die Nachricht wird zu einem GitHub-Issue (anonym, über eine GitHub App), mit einem Badge „Neue Antwort".

@@@ Troubleshooting | Fehlerbehebung
# Fehlerbehebung

Zuerst: Exportieren Sie die **Diagnose** (Einstellungen → Diagnose) und heben Sie sie für eine Meldung auf.

## Der Bildschirm bleibt beim Start weiß (macOS)
Port **5000** ist oft vom *AirPlay-Empfänger* belegt (ein 403 in Safari). Stellio wählt jetzt **automatisch** einen freien Port (5001–5030). Andernfalls: Systemeinstellungen → Allgemein → AirDrop & Handoff → *AirPlay-Empfänger* ausschalten. Protokoll: `~/.stellio/stellio.log` (auf normaler Stufe leer: Debug-Modus aktivieren).

## Der LXC-Container ist nicht mehr erreichbar
In der Proxmox-Shell:
1. `pct status <CTID>`, dann `pct start <CTID>`, falls er gestoppt ist.
2. `pvesm status`: **Speicher voll**? Das ist bei geteiltem Speicher die häufigste Ursache.
3. `pct exec <CTID> -- free -m` und `dmesg -T | grep -i "oom\|killed process"`: Speichermangel.
4. `pct exec <CTID> -- ip -4 a`: Hat sich die DHCP-IP geändert? Reservieren Sie sie im Router.
5. `pct exec <CTID> -- systemctl status stellio` und `journalctl -u stellio -n 100`.

Seit 1.0.7 behandelt die automatische Überwachung die häufigen Fälle; siehe `journalctl -t stellio-watchdog`.

## Vorschaubilder sind langsam oder fehlen
- Wählen Sie *Einstellungen → Vorschaubild-Leistung*: **Eco** auf einem kleinen Rechner.
- Sehr schwere Dateien behalten nach einer Zeitüberschreitung ein Ersatz-Vorschaubild.
- Die Erzeugung pausiert, während Sie die App benutzen: Das ist normal.

## Mein Drucker wird nicht erkannt
- Prüfen Sie, ob er im selben Netzwerk ist (VLAN, Gast-WLAN).
- Fügen Sie ihn von Hand mit IP-Adresse und Schlüssel hinzu.
- Bambu Lab: LAN-Modus aktivieren; Klipper: Die Moonraker-API muss erreichbar sein.

## Das Foto am Druckende fehlt
Aktivieren Sie am Drucker das Kästchen *Foto am Druckende* (wie KI-Überwachung und smarte Steckdose) und prüfen Sie, ob die Kamera antwortet.

## „Modul fehlt"
Beim ersten Start jeder Version lädt Stellio fehlende Module herunter. Prüfen Sie Ihre Internetverbindung; setzen Sie `STELLIO_NO_AUTO_INSTALL` nur bei Bedarf.

## Windows SmartScreen / macOS blockiert die App
Die Installationsprogramme sind nicht signiert. Prüfen Sie die `.sha256`, dann *Weitere Informationen → Trotzdem ausführen* (Windows) oder Rechtsklick → *Öffnen* (macOS).

## Hilfe erhalten
[GitHub Issues](https://github.com/stellio-app/stellio/issues), [Discord](https://discord.gg/ySxpHvS6bd) oder **Vorschläge & Fehler** in der App. Geben Sie an: Stellio-Version, System, Schritte zur Reproduktion, exportiertes Protokoll.

@@@ Contributing | Mitwirken
# Mitwirken

Beiträge sind willkommen. 🎉

1. **Forken** Sie das Repository.
2. Erstellen Sie Ihren Branch: `git checkout -b feature/MeineFunktion`.
3. Committen Sie: `git commit -m "Füge MeineFunktion hinzu"`.
4. Pushen Sie: `git push origin feature/MeineFunktion`.
5. Öffnen Sie einen **Pull Request**.

Regeln: bestehenden Stil beachten, auf Französisch oder Englisch kommentieren, wenn möglich unter Windows testen, Dokumentation aktualisieren. Jeder neue Oberflächentext muss in **allen 8 Sprachdateien** ergänzt werden.

## Technologien
| Komponente | Technologie |
|---|---|
| Backend | Python 3.8+, Flask, Waitress |
| Frontend | HTML5, CSS3, reines JavaScript (ohne Build-Schritt) |
| Datenbank | SQLite (WAL-Modus) |
| Desktop | pywebview (Windows, macOS) / Browser (Server) |
| 3D | PyRender, numpy-CPU-Rasterizer, Three.js |
| Mesh | trimesh, pymeshfix, shapely, rectpack |
| KI | Ollama (lokal) |
| Netzwerk | paho-mqtt, smbclient, requests |
| Verschlüsselung | cryptography (AES) |

## Repository-Struktur
```
stellio/
├── main.py            Flask-Kern: Datenbank, Auth, Bibliothek, Drucker, KI, Start
├── modules/           Aus main.py ausgelagerte Funktionen (print_session, timelapse, quote_portal …)
├── interface/         index.html, script.js, style.css, management.js (reines JavaScript)
├── packaging/         launcher.py, Windows-Installer (.iss), macOS-Berechtigungen
├── languages/         Übersetzungen (8 Sprachen) und changelog.json
├── tests/  tools/     pytest-Tests, Wartungswerkzeuge
├── release-notes/     notes_version_X.Y.Z.txt
├── install-pi.sh      Installation Raspberry Pi / Linux
└── stellio-lxc.sh     Installation Proxmox-LXC
```
Ein Modul deklariert die genutzten `main.py`-Dienste (`_REQUIRED`), seine Routen (`_ROUTES`) und eine `init`-Funktion. Prüfung vor der Veröffentlichung: `python -m pytest tests -q`.

## Sicherheit und Datenschutz
- Stellio ist **local-first**: Standardmäßig wird nichts erfasst oder gesendet. Einzige Ausnahme, wenn Sie sie aktivieren: die Online-KI der Server-Edition.
- Code- und Konfigurationsdateien sind vom Browser aus nicht erreichbar; die API ist durch Sitzung und CSRF geschützt; Gäste haben nur Lesezugriff; Geheimnisse sind verschlüsselt.
- Jede Version wird mit einer `.sha256`-Prüfsumme veröffentlicht, die die integrierte Aktualisierung prüft.

## Lizenz
**GNU AGPL v3**: Sie dürfen Stellio kopieren, ändern und verbreiten; wenn Sie es ändern oder als Netzwerkdienst anbieten, müssen Sie den Quellcode unter derselben Lizenz veröffentlichen.

## Partnerschaft und Dank
Stellio ist offizieller Integrationspartner von **TigerTag** ([tigersystem.io](https://tigersystem.io)). Dank an Ollama, Flask, Three.js, trimesh, Spoolman und die Maker-Community. ☕ Unterstützen: [Ko-fi](https://ko-fi.com/E6J828RYVD).
