@@@ Home | Startseite
# 🧊 Stellio, Ihre 3D-Werkstatt an einem Ort
{{img:dashboard}}

> **Bibliothek, Drucker, Spulen, Kosten und Angebote: alles ist geordnet, nur einen Klick entfernt und bleibt bei Ihnen.**

🔒 **100 % lokal** · 🆓 **Kostenlos und Open Source** (AGPL v3) · 🌍 **8 Sprachen** · 🖥️ Windows, macOS, Linux, Raspberry Pi, Proxmox · 📱 Android

**[⬇️ Stellio herunterladen](https://github.com/stellio-app/stellio/releases)** · **[▶ Online-Demo ausprobieren](https://demo.stellio-app.com)** · **[💬 Dem Discord beitreten](https://discord.gg/ySxpHvS6bd)**

## ✨ Warum Sie es lieben werden

| Für Sie… | Was Stellio ändert |
|---|---|
| 🗂️ **Eine Bibliothek, die sich selbst ordnet** | Automatische 3D-Vorschaubilder, KI-Tags, Suche in natürlicher Sprache, erkannte Duplikate. |
| 🖨️ **Alle Drucker auf einem Bildschirm** | Bambu Lab, Prusa, Klipper, OctoPrint, Creality … Temperatur, Kamera, Fortschritt, Foto am Druckende und Zeitraffer. |
| 🚀 **Von der Bibliothek zur Maschine mit einem Klick** | Senden an den Slicer mit den richtigen Profilen und der richtigen Spule (ein Slicer pro Drucker), Prüfungen vor dem Druck. |
| 🧵 **Ihre Spulen im Griff** | Bestand, Spoolman, TigerTag, OpenPrintTag, Prognose des Leerwerdens, Trocknungs-Erinnerungen. |
| 💶 **Kosten, Angebote und Aufträge** | Echte Kosten (Material, Strom, Verschleiß), PDF-Angebote, Online-Kundenverfolgung, Rechnungen. |
| 🤖 **Eine KI, die zu Hause bleibt** | Lokales Ollama: Tagging, Suche, Druckbarkeit, Fehlerüberwachung, S.O.S Print. |
| 🛠️ **Werkzeuge, die ein Teil retten** | 3D-Viewer, Netzreparatur, Konvertierung, automatische Platzierung, empfohlene Ausrichtungen. |
| 📱 **Überall dabei** | Smartphone (PWA und Android-App), Fernzugriff, Push-Benachrichtigungen, Home Assistant. |

## 🚀 In 3 Minuten loslegen

1. **Installieren** Sie Stellio: ein Installer, ein AppImage oder ein Befehl auf Raspberry Pi und Proxmox ([Installation](de-Installation)).
2. **Fügen Sie einen Ordner** mit Ihren Modellen hinzu: Stellio sortiert sie und erstellt die 3D-Vorschaubilder von selbst.
3. **Fügen Sie einen Drucker hinzu** (optional): Er wird in Ihrem Netzwerk automatisch erkannt.

👉 Weiter mit den [Erste Schritte](de-Getting-Started) und der [Schritt-für-Schritt-Anleitung](de-How-To), die **jede Funktion und ihre Bedienung** erklärt.

## 🧭 Das Wiki entdecken

| Ich möchte… | Seite |
|---|---|
| Jede Funktion bedienen lernen | [Schritt-für-Schritt-Anleitung](de-How-To) |
| Stellio installieren | [Installation](de-Installation) |
| Meine ersten Schritte machen | [Erste Schritte](de-Getting-Started) |
| Meine 3D-Dateien verwalten | [Bibliothek](de-Library) |
| Meine Drucker verbinden | [Drucker](de-Printers) |
| Meine Spulen verfolgen | [Filament](de-Filament) |
| Modelle herunterladen | [Downloads](de-Downloads) |
| KI und S.O.S Print nutzen | [Künstliche Intelligenz](de-AI) |
| Kosten, Angebote, Rechnungen berechnen | [Kosten und Verwaltung](de-Costs-and-Management) |
| Vom Smartphone darauf zugreifen | [Fernzugriff und Mobil](de-Remote-Access) |
| Auf Raspberry Pi / Proxmox installieren | [Server-Edition](de-Server-Edition) |
| Einstellen, sichern, meine Daten verstehen | [Einstellungen und Daten](de-Settings-and-Data) |
| Ein Problem lösen | [Fehlerbehebung](de-Troubleshooting) |
| Zum Projekt beitragen | [Mitwirken](de-Contributing) |
| Sehen, was jede Version bringt | [Neuigkeiten](de-Changelog) |

> 🔒 **Philosophie**: Ihre Daten bleiben bei Ihnen. Alles läuft lokal; standardmäßig verlässt nichts Ihren Rechner.

## Nützliche Links

- 🌐 Website: [stellio-app.com](https://stellio-app.com) · ▶ [Online-Demo (nur Lesen)](https://demo.stellio-app.com)
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

> 💡 Kann das integrierte Fenster nicht geöffnet werden (WebView2 oder `Python.Runtime.dll` blockiert, oft nach einem Download), öffnet sich Stellio in einem eigenen Edge/Chrome-Fenster und beendet sich beim Schließen. Das integrierte Fenster kommt zurück, wenn Sie die ZIP-Datei per Rechtsklick → Eigenschaften → **Zulassen** entsperren und neu entpacken. Details stehen in `data\stellio.log`.

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

Die linke Leiste ist eine **Symbolleiste**; ein Klick auf eine Kategorie öffnet rechts ihr **Panel**, das sich nach der Auswahl wieder schließt.

{{img:sidebar-panel}}


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

## Navigation
Die linke Leiste ist eine **schmale Schiene**: Start, Bibliothek, Drucken, Filament, Werkzeuge und Verfolgung. Klicken Sie auf eine Kategorie, um ihr **Panel** zu öffnen; es schließt sich nach Ihrer Auswahl. Die Benachrichtigungs-Badges der Seiten einer Kategorie werden auf ihrem Symbol **addiert**. Unten: Werkstattmodus, Hilfe, **Updates** und Einstellungen. **Projekte** und **Bereits gedruckt** befinden sich unter Drucken.

## Werkzeuge für den Alltag
- **Befehlspalette** `Strg+K`: navigieren, Aktion ausführen, Datei, Tag, Spule oder Profil finden.
- **Benachrichtigungszentrum** (Glocke): Druck beendet, Fehler, Wartung, niedriger Bestand, Spulentrocknung.
- **Schwebendes Widget** mit dem Fortschritt des aktuellen Drucks, auf jeder Seite sichtbar.
- **Tastenkürzel**: siehe [Einstellungen und Daten](de-Settings-and-Data).

@@@ How-To | Schritt-für-Schritt-Anleitung
# Schritt-für-Schritt-Anleitung

Jede Funktion von Stellio: **wofür sie da ist und wie man sie benutzt**. Technische Details stehen auf den anderen Seiten; hier wird gemacht.

> 💡 In der ganzen App: `Strg+K` öffnet die **Befehlspalette** (irgendwohin gehen, eine Aktion starten, eine Datei, ein Tag, eine Spule finden) und `?` zeigt die Tastenkürzel.

## Sich in Stellio zurechtfinden

| Menü | Wofür es da ist |
|---|---|
| **Dashboard** | Laufende Drucke, niedriger Bestand, letzte Dateien; verschiebbare Widgets. |
| **Bibliothek** | Alle Ihre 3D-Modelle mit Vorschaubildern, Tags, Filtern und Suche. |
| **Bald drucken** | Ihre Druck-Warteliste, umsortierbar. |
| **Projekte** | Mehrere Dateien für ein Objekt gebündelt. |
| **Drucker** | Live-Überwachung, Senden, Wartung, Verschleißteile. |
| **Filament-Bestand** | Ihre Spulen, die Prognose des Leerwerdens, Trocknung. |
| **Verlauf** | Jeder gesendete Druck, als Erfolg oder Fehlschlag bewertet. |
| **Galerie** | Die Fotos Ihrer Drucke. |
| **Statistiken** | Zuverlässigkeit, Verbrauch, Formate, Berichte. |
| **Verwaltung** | Kosten, Kundenangebote, Aufträge, Buchhaltung. |
| **Werkstattmodus** | Vollbildanzeige für Tablet oder Smartphone. |
| **S.O.S Print** | Geführte Diagnose eines fehlgeschlagenen Drucks. |
| **Download** | Modelle von Printables, MakerWorld, Thingiverse … holen. |
| **Reparatur** | Beschädigte Netze finden und reparieren. |
| **Konverter** | Von einem 3D-Format in ein anderes wechseln. |
| **Duplikate** | Doppelte Dateien aufspüren. |
| **Papierkorb** | Gelöschtes wiederherstellen. |
| **Einstellungen** | Erscheinungsbild, Slicer, KI, Sicherungen, Fernzugriff. |

## Meine Dateien hinzufügen und finden

1. Klicken Sie auf **Quelle hinzufügen** (oder `Strg+K` und dann „Quelle hinzufügen“) und wählen Sie einen **Ordner**, eine einzelne Datei oder eine **SMB-/NFS**-Freigabe. Auf Ihrem Computer gefundene 3D-Ordner werden vorgeschlagen.
2. Stellio scannt und erstellt die **3D-Vorschaubilder** im Hintergrund; die Erzeugung pausiert, solange Sie die App benutzen.
3. Ein Modell finden: in die **Suchleiste** tippen oder es mit der KI-Suche in normaler Sprache beschreiben („ein Kopfhörerständer“).
4. Ziehen Sie 3D-Dateien aus dem Datei-Explorer per Drag-and-drop hinein, um sie direkt hinzuzufügen.

💡 Archive (ZIP, RAR, 7z, TAR) lassen sich durchsuchen, ohne sie zu entpacken.

## Mit Tags, Favoriten und Filtern ordnen

1. Öffnen Sie das **⋯**-Menü einer Datei oder wählen Sie mehrere aus (`Umschalt+Klick` für einen Bereich), um in einem Zug zu handeln.
2. Fügen Sie farbige **Tags** von Hand hinzu oder lassen Sie sie von der KI vorschlagen; `T` öffnet die Tag-Verwaltung.
3. Klicken Sie auf den Stern, um ein Modell zum **Favoriten** zu machen (`F` öffnet die Favoriten).
4. Kombinieren Sie **Filter** (Typ, Größe, Gewicht, Druckstatus, „Filamentbestand“) und **speichern** Sie den Filter zur Wiederverwendung.
5. Viele Dateien umbenennen: **Massenumbenennung** (Suchen/Ersetzen, Präfix, Suffix, Nummerierung) mit Vorschau vor der Bestätigung.

## Ein Modell in 3D ansehen und vorbereiten

1. Klicken Sie auf das Vorschaubild einer Datei: Der **3D-Viewer** öffnet sich (er funktioniert offline).
2. Drehen und zoomen Sie; bei einem 3MF mit mehreren Platten wechseln Sie zwischen den Platten.
3. Starten Sie die **Druckbarkeitsanalyse** (Überhänge): Stellio schlägt empfohlene **Ausrichtungen** vor.
4. Nutzen Sie die **automatische Platzierung**, um mehrere Teile auf dem Druckbett anzuordnen.
5. Senden Sie das Ergebnis aus dem Viewer an den Slicer.

## Ein beschädigtes Netz reparieren

1. Öffnen Sie **Reparatur**: Stellio listet Dateien mit Löchern oder offenen Kanten auf (die Analyse läuft auch im Hintergrund, wenn Vorschaubilder erstellt werden).
2. Wählen Sie eine Datei und starten Sie die **Reparatur**; vergleichen Sie **vorher / nachher**.
3. Die Datei wird an Ort und Stelle repariert; eine `.bak`-Sicherheitskopie bleibt zur Sicherheit erhalten.

## Dateien konvertieren

1. Öffnen Sie den **Konverter** und wählen Sie eine oder mehrere Dateien (STL, 3MF, OBJ, PLY, AMF, STEP).
2. Wählen Sie das Ausgabeformat: STL, 3MF, OBJ, PLY, OFF oder GLB.
3. Haken Sie bei Bedarf **Netz automatisch reparieren** und **Originaldatei löschen** an.
4. Starten Sie. Eine Stapelkonvertierung lässt sich jederzeit abbrechen: bereits konvertierte Dateien bleiben erhalten.

## Ein Modell in Originalgröße vergrößern (BigPrint)
BigPrint (Menü **Werkzeuge**) skaliert ein Modell auf die gewünschte Größe — 1,8 m oder mehr — und zerlegt es in Teile, die auf Ihr Druckbett passen: ausgehöhlte Teile, Verbindungsstifte und eine eingravierte Nummer auf jedem Teil. Die Berechnung übernimmt die Open-Source-Engine [bigprint](https://github.com/PooterTF/bigprint) (AGPL-3.0, von Michael Christopher Stone), die in Stellio eingebaut ist.

{{img:bigprint}}

1. Modell wählen: **Aus der Bibliothek wählen**, **Datei importieren** oder die Schaltfläche **An BigPrint senden** im Menü **Aktionen** einer Datei (STL, 3MF, OBJ, PLY).
2. **Endgröße** (Höhe, Breite, Tiefe oder Skalierungsfaktor) und **Drucker** (Vorgaben oder eigene Maße) angeben.
3. **Stabilität** (Verwendungszweck, Material, Aushöhlen, Wandstärke) und **Stifte** einstellen; die erweiterten Optionen (obere Achse, Rand, Glätten …) sind eingeklappt.
4. Auf **Vorschau** klicken: Stellio zeigt die Teile in der Explosionsansicht, das Filamentgewicht, die geschätzten Kosten und die Teileliste. Eine Berechnung lässt sich jederzeit abbrechen.

{{img:bigprint-result}}

Speicherort wählen (Bibliotheksquelle, Unterordner, Ordner anlegen möglich, Netzwerkfreigaben inklusive) und **Druckdateien speichern**: STL-Teile, 3MF-Projekt, Stifte, Bericht und Vorschau werden in den Ordner `<Modell>_bigprint` kopiert.

Wenn Sie nach der Vorschau eine Einstellung ändern, starten Sie die Vorschau vor dem Speichern erneut.

## Aufräumen: Duplikate und Papierkorb

1. Öffnen Sie **Duplikate**: identische Dateien und solche mit **ähnlicher Geometrie** (dasselbe Modell umbenannt oder neu exportiert) werden gruppiert.
2. Behalten Sie die gewünschte Datei und löschen Sie die anderen.
3. Versehentlich gelöscht? `Strg+Z` macht es 5 Minuten lang rückgängig; der **Papierkorb** behält Elemente länger und erlaubt, sie wiederherzustellen oder endgültig zu löschen.

## Dateien zu Projekten bündeln

1. Öffnen Sie **Projekte** und legen Sie ein Projekt an; fügen Sie die Dateien eines Objekts hinzu (Körper, Deckel, Stützen …).
2. Ein 3MF mit **mehreren Platten**, das einem Projekt hinzugefügt wird, wird in ein 3MF pro Platte aufgeteilt (auch verfügbar: **Platten aufteilen** im ⋯-Menü).
3. Verfolgen Sie den Fortschritt („In Arbeit“ / „Fertig“) und klicken Sie auf **Projektkosten**, um das ganze Set zu kalkulieren.

## Modelle herunterladen

1. Öffnen Sie **Download** (oder `Strg+N`) und fügen Sie den Link eines Modells ein (Printables, MakerWorld, Thingiverse, Nexprint, Creality Cloud, Snapmaker Space).
2. Verbinden Sie das verlangte Konto einmalig (siehe [Downloads](de-Downloads)).
3. Wählen Sie die Ziel-**Quelle**: Die Datei kommt mit ihrer **Herkunft** (Link, Autor, Lizenz).
4. Stellio prüft täglich, ob es eine **neue Version** des Modells gibt; **Meine Likes** und **Meine Kreationen** finden Ihre Modelle auf verbundenen Konten.

## Einen Drucker verbinden

1. Öffnen Sie **Drucker → Hinzufügen**: Die **Netzwerkerkennung** schlägt gefundene Maschinen vor; andernfalls geben Sie Typ, Adresse und Zugangsschlüssel ein.
2. Geben Sie das **Druckvolumen** (X, Y, Z) an: Stellio warnt vor dem Senden, wenn ein Teil zu groß ist.
3. Wählen Sie auf Wunsch den **Slicer dieses Druckers** (1.0.8): Dieser öffnet sich für diese Maschine.
4. Aktivieren Sie die nützlichen Optionen: **Zeitraffer**, **Foto am Druckende**, **KI-Überwachung**, **smarte Steckdose** (realer Verbrauch).

## Eine Datei an den Slicer senden

1. Klicken Sie in der Bibliothek oder im Viewer auf **An Slicer senden**.
2. Im Fenster: Sehen Sie sich die **Schätzung** (Gewicht, Zeit) an, wählen Sie **Drucker**, **Spule** und **Einstellungsprofil** oder lassen Sie „Automatisch“.
3. Lesen Sie die **Prüfungen vor dem Druck**: Spule zu trocknen, abrasives Filament, Volumen überschritten, zu wenig Material.
4. Klicken Sie auf **Senden**: Die Datei öffnet sich im Slicer des Druckers (oder dem aus den Einstellungen) mit den der Maschine zugeordneten Profilen. Die Spule wird abgebucht, wenn Sie es verlangt haben.

💡 Um Profile einem Drucker zuzuordnen, importieren Sie sie unter Einstellungen → Slicer.

## Das Nächste vorbereiten: „Bald drucken“

1. Wählen Sie im **⋯**-Menü einer Datei **Zu „Bald drucken“ hinzufügen**.
2. Öffnen Sie **Bald drucken**: Ziehen Sie zum **Umsortieren**.
3. Senden Sie ein Element direkt an den Slicer oder entfernen Sie es aus der Liste.

## Einen Druck verfolgen

1. Auf der Druckerkarte: Temperatur, Fortschritt, **Live-Kamera** und Name der aktuellen Datei.
2. Ein **schwebendes Widget** zeigt den Fortschritt auf jeder Seite.
3. Die **Glocke** benachrichtigt Sie (fertig, fehlgeschlagen, Wartung, niedriger Bestand); aktivieren Sie **Push-Benachrichtigungen** (ntfy, Gotify, Pushover, Telegram, Discord, Slack, Webhook), um auch bei geschlossenem Fenster informiert zu werden.
4. Bei 100 % macht Stellio das **Abschlussfoto**: Markieren Sie es mit einem Klick als *Erfolg* oder *Fehlschlag*. Der **Zeitraffer** wird automatisch erstellt.

## Bewerten, erneut drucken, Fotos wiederfinden

1. Öffnen Sie den **Verlauf**: Filtern Sie nach Plattform, Ergebnis oder Datum.
2. Bewerten Sie jeden Druck als **Erfolg** oder **Fehlschlag**: Das speist Empfehlungen und Statistiken.
3. **Datei ansehen** oder **Erneut drucken** wie beim letzten Mal (gleiche Einstellungen).
4. Ihre Fotos finden Sie in der **Galerie**; **Meine G-Codes** hält die mit einer Datei verknüpften G-Codes bereit, mit der Schaltfläche **Im Slicer öffnen**.

## Meine Spulen verfolgen

1. Öffnen Sie den **Filament-Bestand**: Fügen Sie Spulen von Hand hinzu (oder per Excel/CSV-Import), verbinden Sie **Spoolman**, **TigerTag** oder **OpenPrintTag** oder suchen Sie eine Spule in der **Open Filament Database**.
2. Wählen Sie beim Senden an den Slicer die Spule: Stellio **bucht** den Verbrauch **ab** und prüft, ob genug übrig ist.
3. Wiegen Sie unter **Wiegen und Prognose** eine Spule: Stellio schätzt ihr **Leerdatum** und warnt, wenn es näher rückt.
4. Tragen Sie die **Trocknung** einer Spule ein, um ihren Zustand zu verfolgen; über **Nachkaufen** öffnen Sie den Shop des Herstellers.

## Kosten berechnen und ein Angebot erstellen

1. Öffnen Sie den Rechner aus einer Datei (**Kosten**) oder einem Projekt (**Projektkosten**).
2. Prüfen Sie Material, Strom, **Maschinenverschleiß**, **Fixkosten**, **Marge** und **Menge**: Stückpreis und Gesamtpreis werden angezeigt.
3. Klicken Sie auf **Angebot erstellen (PDF)**: Tragen Sie Kunde und Bezeichnung ein. Das PDF wird aufbewahrt und ist im Widget **Angebote** zu finden.
4. Legen Sie die Standardmarge unter **Einstellungen → Druckpreise** fest.

## Aufträge, Kunden und Rechnungen verwalten

1. Aktivieren Sie in den Einstellungen *Kosten-, Angebots- und Rechnungsfunktionen aktivieren*: Der Bildschirm **Verwaltung** erscheint.
2. Senden Sie dem Kunden ein Angebot mit seinem **Tracking-Link**: Er kann es online annehmen oder ablehnen; die Annahme erstellt die Druckaufgabe. **Stellio wickelt keine Zahlung ab.**
3. Verfolgen Sie die **Auftragswarteschlange**, Zahlungen, Anzahlungsrechnungen und Gutschriften; die **intelligente Zuteilung** schlägt den passenden Drucker vor, ohne je einen Druck zu starten.
4. Exportieren Sie jeden Monat die **Buchhaltung** (ZIP mit CSV und PDF).

## Produktion planen (Planung und Kapazität)
Die Seite **Planung** (Menü **Druck**) berechnet für jeden Drucker das voraussichtliche Ende jedes Auftrags, vergleicht die verfügbare Kapazität mit der geforderten Last und warnt Sie vor Überlastung oder Verspätung, bevor sie eintritt.

{{img:planning}}

1. Tragen Sie unter **Aufträge** für jeden Auftrag die **Dauer pro Teil** (in Stunden) ein: Ein Auftrag aus einem Angebot übernimmt sie aus der Kalkulation. Ein Auftrag ohne Dauer wird nicht eingeplant und oben auf der Seite angezeigt (dort können Sie sie direkt nachtragen).
2. Wählen Sie den **Drucker** jedes Auftrags (sonst setzt Stellio ihn als Vorschlag auf die Maschine, die als Erste frei wird) und das **Lieferdatum**.
3. Öffnen Sie **Planung**: Balken zeigen die Reihenfolge der Aufträge je Drucker (rot = Verspätung erwartet, orange = weniger als ein Tag Puffer) samt **Auslastung** jeder Maschine. Der laufende Druck wird über die vom Drucker gelesene Restzeit berücksichtigt.
4. Stellen Sie den **Zeitraum** ein (7, 14 oder 30 Tage). Die Karten oben fassen Kapazität, Last, erwartete Verspätungen und die **Termintreue** der letzten 90 Tage zusammen.

**Druckerkapazität**: Geben Sie je Maschine die möglichen Druckstunden pro Tag und die Arbeitstage an (Standard 16 Std., jeden Tag); einen Drucker abwählen, um ihn aus der Planung zu nehmen.

Stellio benachrichtigt Sie, wenn ein Auftrag sein Lieferdatum zu verfehlen droht oder ein Drucker überlastet ist (einmal je Auftrag und Tag).

Die Berechnung ist bewusst einfach: eingegebene Dauern, Aufträge nach Lieferdatum aneinandergereiht, ohne Materialwechsel oder Ausfälle.

## Die beste Kombination finden (Rückverfolgbarkeit)
Die Seite **Rückverfolgbarkeit** (Menü **Druck**) verknüpft jeden Druck mit der **genauen Modellversion** und dem **Slicer-Profil** und zeigt je Modell die erfolgreichste Kombination.

{{img:trace}}

1. Drucken Sie wie gewohnt aus Stellio: Der Druck wird automatisch mit dem Modell verknüpft. Hat sich die Datei seit der letzten Version geändert, speichert Stellio eine Version „Vor dem Druck“ – die Zuordnung ist also immer exakt.
2. **Bewerten Sie das Ergebnis** (Erfolg, Fehlschlag, teilweise) nach dem Druck im Verlauf: Diese Bewertungen speisen die Quoten.
3. Öffnen Sie **Rückverfolgbarkeit**: eine Zeile je Modell mit Versionen und **bester Kombination** (Version + Profil, Erfolge bei bewerteten Drucken). Ein Klick öffnet **Modellversionen**.
4. In **Modellversionen** zeigt jede Version Erfolge, Fehlschläge und Quote; die Tabelle kreuzt **Version × Profil**.

{{img:trace_versions}}

Die Rangfolge lässt sich nicht von kleinen Stichproben täuschen: 8 Erfolge bei 9 Drucken stehen vor 1 bei 1. Eine beste Kombination wird erst ab 2 bewerteten Drucken und bekannter Version vorgeschlagen.

Die Erfassung beginnt mit v1.1.6: ältere Drucke werden nicht rekonstruiert.

## Meine Drucker warten

1. Öffnen Sie auf einer Druckerkarte **Wartung** und wählen Sie die **Marke**: Empfohlene Aufgaben werden angeboten.
2. Fügen Sie sie Ihrer Verfolgung hinzu: Sie werden je nach Druckstunden und vergangenen Tagen „fällig“.
3. Erfassen Sie Ihre **Verschleißteile** (Düsen, Platten, Riemen) mit Warnschwelle und Ihre **Kalibrierungen** je Filament.

## Einen Fehler diagnostizieren: S.O.S Print und KI

1. Öffnen Sie **S.O.S Print** und beschreiben Sie das Problem (Foto möglich).
2. Beantworten Sie die Fragen, eine nach der anderen, **ohne Limit**: Stellio grenzt die Hypothesen ein (und ergänzt bei Bedarf neue), bis die Ursache gefunden ist, und liefert dann eine **abschließende Diagnose**. Hilft die Lösung nicht, antworten Sie „immer noch nicht gelöst“ – die Untersuchung geht weiter.
3. Für lokale KI installieren Sie [Ollama](https://ollama.com/) und richten es unter **Einstellungen → Künstliche Intelligenz** ein. Die **Fehlerüberwachung** warnt Sie, ohne den Druck je zu stoppen.

## Stellio auf dem Smartphone und aus der Ferne nutzen

1. Scannen Sie unter **Einstellungen → Mobiler Zugriff** den **QR-Code**: Die Bibliothek öffnet sich auf Ihrem Smartphone (wie eine App installierbar).
2. Für die **Android**-App scannen Sie den speziellen QR-Code.
3. Unterwegs: Aktivieren Sie den **Fernzugriff** (Cloudflare Tunnel oder eigene Adresse) oder erstellen Sie einen temporären **Freigabelink**.
4. Teilen Sie schreibgeschützt mit einem **Gastkonto**.

## Sichern und wiederherstellen

1. Öffnen Sie **Einstellungen → Sicherung und Daten** und **exportieren** Sie Ihre Daten (.zip).
2. Planen Sie **automatische Sicherungen**.
3. Zum Wiederherstellen **importieren** Sie die .zip-Datei. Ein Stellio-Update berührt Ihre Daten nie.

## Nützliche Tastenkürzel

| Kürzel | Aktion |
|---|---|
| `Strg+K` | Befehlspalette |
| `Strg+N` | Neuer Download |
| `Strg+Z` | Letzte Löschung rückgängig |
| `F` · `T` | Favoriten · Tag-Verwaltung |
| `?` | Hilfe zu Tastenkürzeln |

Vollständige Liste: [Einstellungen und Daten](de-Settings-and-Data).

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
- **Favoriten**, erweiterte Filter (Typ, Größe, Gewicht, Druckstatus), **gespeicherte Filter**. Zugriff: Taste **F**, Dashboard-Widget oder Stern jeder Datei (ein entfernter Stern lässt die Datei sofort aus der Favoritenansicht verschwinden).
- Statusfilter: „An Slicer gesendet", „Bereits gedruckt", „Bereits erfolgreich", „Bereits fehlgeschlagen".
- **Filter „Filamentbestand"**: zeigt nur Dateien, die mit Ihren vorhandenen Spulen druckbar sind.
- Sortierung, Suche und Filter werden beim erneuten Öffnen **gemerkt**.
- Warteschlange **„Bald drucken"**, umsortierbar, an den Slicer sendbar.
- **Mehrfach umbenennen** (Suchen/Ersetzen, Präfix, Suffix, Nummerierung) mit Vorschau.
- **Löschen rückgängig machen** (`Strg+Z`) dank 5-Minuten-Papierkorb; gilt auch für Tags, Projekte und Quellen.
- **Grüner / roter Schimmer** um die Vorschau: grün für erfolgreich gedruckte Dateien, rot für fehlgeschlagene Drucke (Galerie- und Detailansicht).
- **Schon gedruckt** (⋯-Menü einer Datei): einen anderswo gemachten Druck von Hand erfassen — Drucker, Einstellungen (Slicer-Profil) und Spule wählen, dann **Erfolgreich** oder **Fehlgeschlagen**. Die Datei erscheint in den Filtern „Erfolgreich gedruckt“ / „Fehlgeschlagen“, ihr Detailblatt (Rechtsklick) zeigt Drucker, Einstellungen und Spule.
- **Seite „Bereits gedruckt“** (Panel Drucken): alle gedruckten oder als „bereits gedruckt“ markierten Dateien, mit denselben Vorschaubildern und Rahmen wie die Bibliothek, einer Suche und einem Filter Erfolgreich / Fehlgeschlagen. Beim Überfahren einer Vorschau erscheint ein **rotes Kreuz** (am Smartphone: ein Tippen zeigt es an, ein zweites öffnet die Datei); nach einer Bestätigung entfernt es die Datei aus der Liste, sie gilt wieder als „nie gedruckt“. Die Schaltfläche **Entfernen** in den Dateiinfos macht dasselbe. Ein gleichnamiges Widget gibt es auf der Startseite.
- Schnelle Auswahl: `Umschalt+Klick` für einen Bereich, Pfeiltasten + `Enter`.
- **Duplikaterkennung** (exakt und ähnliche Geometrie).
- **Modellherkunft**: Quelllink, Autor, Lizenz, Notizen, Download-Datum.
- **Drag & Drop** von 3D-Dateien aus dem Datei-Explorer, auch im Browser.

{{img:library-halo}}

{{img:already-printed}}

Bei einer 3MF mit **mehreren Platten** bietet das Fenster „Bereits gedruckt“ einen Bereich pro Platte, jeweils mit eigener Spule; eine **mehrfarbige** Datei akzeptiert mehrere Farben pro Platte (**Farbe hinzufügen**). Die Farbpunkte entsprechen Ihren Spulen, die Dateiinfos zeigen die Details.

{{img:already-printed-plates}}

An den **an den Slicer gesendeten** Dateien erscheint sofort ein **bernsteinfarbener Rahmen** (grün bei Erfolg, rot bei Fehlschlag); der Filter **An Slicer gesendet** der Bibliothek findet sie mit einem Klick.

- **Sammlungen**: Modelle nach Thema gruppieren (Dateimenü → *Zu einer Sammlung hinzufügen*). Jede Sammlung wird in der Bibliothek zu einem Filter-Chip; legen Sie pro Datei eine **Menge** fest und setzen Sie die **ganze Sammlung mit einem Klick in die Druckwarteschlange**.
- **Modellversionen**: Dateimenü → *Versionen*. Speichern Sie vor dem Bearbeiten eine Kopie, **vergleichen** Sie sie mit der aktuellen Datei (Größe, Dreiecke, Abmessungen, Volumen), laden Sie sie herunter oder **stellen** Sie sie **wieder her** (der aktuelle Stand wird zuerst gesichert).

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
- **BigPrint** (Menü **Werkzeuge**): skaliert ein Modell auf die gewünschte Größe und zerlegt es in nummerierte Teile mit Stiften, explodierter 3D-Vorschau sowie Filament- und Kostenschätzung (Open-Source-Engine bigprint).
- **Zu 3MF zusammenführen**: Mehrere Modelle (STL, 3MF, OBJ …) auswählen, und Stellio erstellt daraus eine einzige 3MF-Datei — eine Platte, wenn alles passt, sonst eine Datei mit mehreren Platten (kompatibel mit Bambu Studio / OrcaSlicer; PrusaSlicer zeigt alle Teile zusammen). Dateiname und Ordner sind frei wählbar (auch Netzwerkfreigaben, Ordner anlegen möglich); danach fragt Stellio, ob die Originaldateien gelöscht oder behalten werden sollen.
- **Spulenfarbe an den Slicer**: Beim Senden werden Farbe und Material der gewählten Spule auf das in OrcaSlicer, Bambu Studio oder PrusaSlicer geladene Filamentprofil angewendet (ein importiertes, dem Drucker zugeordnetes Filamentprofil ist nötig; beim Sammelversand nur, wenn alle Spulen gleich sind).
- **Auswahlleiste**: alle Schaltflächen gleich groß und in einer Zeile (auf kleinen Bildschirmen nur Symbole, Name im Tooltip).
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

## Große Modelle
Eine STL-Datei belegt beim Laden etwa das 12-Fache ihrer Größe im Speicher. Ab einer Schwelle (256 MB, bis 1 GB bei viel freiem Speicher) lädt Stellio sie nicht mehr vollständig: Analyse im Datenstrom (binäre und Text-STL), Vorschaubild und Viewer auf einer **vereinfachten Version** (etwa 300 000 Dreiecke), Schreibvorgänge (Reparatur, Konvertierung …) werden mit klarer Meldung abgelehnt.
Um trotzdem damit zu arbeiten: Rechtsklick › **Leichte Version erstellen**. Stellio schreibt eine vereinfachte Kopie neben das Original (`Name (leicht).stl`), das nie verändert wird. Die Kopie dient zum Ansehen, Messen, Reparieren oder Indizieren, nicht zum Drucken in voller Auflösung. Die Aktion wird auch angeboten, wenn eine Reparatur wegen der Größe abgelehnt wird; sie gilt nur für lokale STL-Dateien. Ein Export des Slicers (OrcaSlicer …) als STL oder 3MF ist oft viel kleiner.
In der Erweiterten Werkstatt bietet jedes Feld „Modellpfad“ **Aus der Bibliothek wählen**: Quelle, Suche, Formatfilter (STL, 3MF …), Vorschaubilder und Seiten.

@@@ Printers | Drucker
# Drucker
{{img:printers}}

Auf der Startseite zeigt das Widget **Kameras** bis zu **4 Kameras** (eine pro laufendem Drucker): Ein Klick auf eine Vorschau öffnet ein Fenster mit **nur der Kamera** (das Widget „Laufende Drucke“ behält die komplette Anzeige). Mit **Alle anzeigen** öffnet sich die Liste aller Kameras zur Auswahl.


## Unterstützte Marken

| Marke | Modelle | Verbindung |
|---|---|---|
| **Bambu Lab** | X1/X1C/X1E, X2D, P1P/P1S, P2S, A1/A1 mini, H2D/H2S/H2C | MQTT (LAN + Cloud): Überwachung, AMS, Kamera, SSDP-Erkennung |
| **Prusa** | MK4, MK3.9, MK3.5, MINI+, XL, CORE One | PrusaLink (HTTP) |
| **Creality** | Serien K1/K2, Ender-3 V3, Hi | WebSocket: Überwachung, CFS, UDP-Erkennung |
| **Elegoo** | Centauri Carbon 1 & 2, Resin-Serien Saturn/Mars | SDCP (WebSocket) |
| **Chitubox-Harz** | Phrozen, Uniformation GKtwo und andere Chitubox-Boards | SDCP v3: Überwachung (gleiches Protokoll wie Elegoo) |
| **USB-Drucker** | Marlin, Prusa, Creality, Klipper-Boards… am Stellio-PC angeschlossen | Erkennung serieller Ports (der Port wird nie geöffnet): angesteckt / fehlt, ohne Status oder Temperaturen |
| **Anycubic Photon** | Ältere WLAN-Modelle: Mono X, Mono X 6K, Mono SQ (nicht M5s / M7) | TCP-6000-Textbefehle: nur Status und aktuelle Datei |
| **Formlabs** | Form 3 / 3L / 4 | Offizielle Web-API (client_id:client_secret): Status, Fortschritt, Schichten; Senden mit PreForm |
| **FlashForge** | Adventurer 5M/5M Pro, AD5X | Proprietäre API |
| **Klipper / Moonraker** | Jede Klipper-Maschine (Voron …) | HTTP: Überwachung, Upload, Kamera, genaue Stunden |
| **OctoPrint** | Jeder über OctoPrint gesteuerte Drucker | HTTP |
| **Duet / RepRapFirmware** | Duet 2/3, Standalone oder SBC (DSF) | HTTP: Status, Dateiversand, Temperaturen |
| **Repetier-Server** | Jeder von Repetier-Server verwaltete Drucker | HTTP: Status, Dateiversand, Temperaturen (Marlin über USB-Seriell wird nicht unterstützt) |

> **Harzdrucker: nur Überwachung.** Stellio startet oder stoppt nie einen Harzdruck. Bitte melden Sie Probleme auf GitHub (Creality Halot: noch nicht unterstützt).

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
- **Slicer pro Drucker**: Jeder Drucker kann seinen eigenen Standard-Slicer haben (OrcaSlicer, QIDIStudio, Bambu Studio…). Das Senden nutzt ihn mit den diesem Drucker zugeordneten Profilen (Einstellungen, Filament), die Profilliste passt sich an.
- **Harz-Software**: Stellio erkennt CHITUBOX, CHITUBOX Pro, Anycubic Photon Workshop, PreForm (Formlabs), Voxeldance Tango und Lychee Slicer. Ein Harzdrucker ohne gewählten Slicer öffnet automatisch die erste erkannte Harz-Software; Sie können auch manuell eine wählen (Einstellungen → Slicer oder Druckerformular). Übliche Installationspfade werden geprüft: Wird Ihre Software nicht erkannt, wählen Sie sie manuell aus.

{{img:printer-slicer}}

## Während des Drucks
- **Smarte Steckdose** (Shelly, Tasmota, Home Assistant): Stellio liest die Watt und speichert den realen Verbrauch (kWh) und die Kosten.
- **Realer Filamentverbrauch**, nach dem Druck erfasst.
- **Foto am Druckende**, aufgenommen bei **100 %** (das Teil liegt noch auf dem Bett), ein einziges Foto zur Bewertung *Erfolgreich/Fehlgeschlagen*.
- **KI-Fehlerüberwachung** (Ollama mit Bildmodell, 100 % lokal): Alarm bei Spaghetti oder abgelöstem Teil, **nie ein automatischer Stopp**.
- Automatischer **Zeitraffer** (Kamera → MP4-Video, benötigt ffmpeg).
- **Statuslinks zum Teilen** (nur Lesezugriff).

## Fehlererkennung per Kamera (Obico)
Geben Sie unter *Einstellungen → Obico* die Adresse Ihres Obico-Servers (selbst gehostet oder obico.io) und einen API-Token an. Stellio prüft regelmäßig auf Alarme und sendet eine **Push-Benachrichtigung**, sobald Obico einen Fehler erkennt. Die Aktion (Pause, Abbruch) bleibt bei Obico: Stellio bricht nie von selbst einen Druck ab. Mit *Verbindung testen* werden Adresse und Token geprüft.

## Wartung
- **Harz-Wartung**: Die Schaltfläche **Wartung** auf den Karten von Harzdruckern bietet passende Aufgaben (FEP-/nFEP-Folie, Harz filtern, Bauplattform, LCD, Kohlefilter, Z-Achse, IPA, UV-/LCD-Verschleiß).
- **Vorausschauende Wartung** mit markenspezifischen Aufgaben.
- **Verschleißteile** (Düsen, Platten, Riemen …) mit Bestandswarnungen, verknüpft mit Wartungsaufgaben.
- **Kalibrierungen** (Fluss, Pressure Advance, Temperaturen) pro Filament und Drucker.

@@@ Filament | Filament
# Filament

## Harz
Die Kategorie in der Seitenleiste heißt jetzt **Materialien** und enthält zwei Seiten: **Filament** (Spulen-Inventar) und **Harz**. Das Harz-Inventar ist **manuell**: Erfassen Sie Ihre Flaschen (Name, Marke, Art, Farbe, Volumen, Rest, Preis, Lagerort, Notizen) und ziehen Sie mit „Verbrauchen“ ein Volumen in ml ab. Stellio verknüpft Flaschen noch nicht mit Harzdruckern und zieht nichts automatisch ab.

Wie beim Filament funktioniert die **„Nachzubestellen“**-Erinnerung auch für Harz: Ein Harz (Marke + Name + Farbe, alle Flaschen zusammen) erscheint in der Liste, sobald sein Gesamtrest unter die auf der Seite eingestellte Schwelle fällt (Standard 200 ml, 0 = aus) oder wenn Sie bei einer Flasche „Nachbestellen“ ankreuzen. Es erscheint auch im Dashboard-Widget „Nachzubestellen“; **Bestellen** öffnet Suchlinks zu Ihren Shops (der Bestand wird bei Harz nicht automatisch geprüft), **Bereits bestellt** verschiebt die Erinnerung um 14 Tage.

## Bestandsquellen
| Quelle | Details |
|---|---|
| **Spoolman** | Automatische Erkennung im Netzwerk. Stellio **schreibt den Verbrauch nicht mehr** dorthin (vermeidet doppelte Zählung). |
| **Manuell** | Von Hand erfasste Spulen, Excel-/CSV-Import. |
| **TigerTag** | NFC-/RFID-Identifikation. Anmeldung mit E-Mail und Passwort (nur ein verschlüsseltes Token wird gespeichert) oder Übernahme einer TigerTag-Studio-Sitzung. **Nur Lesezugriff.** |
| **OpenPrintTag** | Offener NFC-Tag-Standard: Import/Export von `.bin`-Dateien, Lesen/Schreiben über die Android-App, verbrauchtes Gewicht bleibt aktuell. |
| **Bambu AMS / Creality CFS** | Auslesen der Slots. |

**Open Filament Database**: Spule nach Marke, Material und Farbe suchen und mit einem Klick anlegen (Gewicht, Durchmesser und Dichte vorausgefüllt).

Im Fenster „An Slicer senden“ ist die Spulenliste sortiert und hat ein **Suchfeld**.

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

Die **Shops der Open Filament Database** (86) sind in den **Nützlichen Links** enthalten, nach Ihrem Land gefiltert, und werden auch von der Suche **Spule nachkaufen** genutzt: Stellio schlägt die Shops vor, die zu Ihnen liefern.

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

> ⚠️ Die KI ist nicht zu 100 % zuverlässig und kann sich irren (Tags, Beschreibungen, S.O.S-Print-Diagnosen …). Betrachten Sie ihre Antworten als Hinweise zum Überprüfen, nicht als Gewissheiten.

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
1. Sie beschreiben das Problem (bei jedem Schritt ist ein Foto möglich) und, wenn Sie möchten, die verwendeten Einstellungen (Temperaturen, Geschwindigkeiten, Rückzug …). Die **Geschwindigkeiten** werden aus dem gewählten Slicer-Profil gelesen (oder von Ihnen eingegeben); fehlen sie, fragt die KI danach. Bei **Mehrfarbdrucken** prüft die KI den **Reinigungsturm** (löst sich, kippt, fällt aufs Teil, Farben vermischen sich) und stellt die passenden Fragen; die Turmbreite wird aus dem Profil gelesen. Ab dem ersten Schritt und nach jeder Antwort zeigt die KI ihre **Hypothesen nach Wahrscheinlichkeit sortiert** (%), jeweils mit Begründung oder Schnelltest.
2. Stellio stellt **eine Frage nach der anderen**, ohne Limit, und grenzt eine Liste von Hypothesen live ein (neue kommen hinzu, wenn die ersten ausgeschlossen sind).
3. Es liefert eine **endgültige Diagnose**.

Ab **Frage 3** liefert **Abschließen und Lösung vorschlagen** die wahrscheinlichsten Ursachen und fragt dann „Hat diese Diagnose das Problem gelöst?“ (**Ja, gelöst** / **Nein, Untersuchung fortsetzen**). Mit **Untersuchung beenden** brechen Sie jederzeit ab.

Unterhaltungen werden gespeichert: erneut öffnen oder als gelöst markieren.

> ℹ️ Die Ergebnisse „Erfolgreich / Fehlgeschlagen", die Sie im Verlauf bewerten, verbessern die Empfehlungen.

@@@ Costs-and-Management | Kosten und Verwaltung

> ⚠️ Die KI ist nicht zu 100 % zuverlässig und kann sich irren. Ihre Hypothesen sind Hinweise zum Überprüfen, keine Gewissheiten; prüfen Sie nach, bevor Sie Einstellungen oder Ihre Maschine ändern.

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
- **Nebenzeit / Hauptzeit**: Tragen Sie unter *Einstellungen → Strom* zwei kWh-Preise und Ihre Nebenzeiten ein (z. B. `22:00-06:00`, Wochenende optional). Die **tatsächlichen Kosten** gemessener Drucke berücksichtigen sie, eine 30-Tage-Übersicht zeigt die **mögliche Ersparnis**, ein Simulator vergleicht „jetzt“ mit „nächstem Nebenzeit-Fenster“, und eine Erinnerung meldet den Beginn der Nebenzeit bei wartenden Aufträgen. Stellio startet nie selbst einen Druck.
- **Warum meine Drucke scheitern**: unter *Statistiken* Fehlerquote nach Grund, Material, Drucker, Slicer-Profil, Wochentag und Tageszeit, am häufigsten fehlgeschlagene Dateien und belegte Hinweise (z. B. „PETG: 45 % Fehler gegenüber 12 % im Schnitt“). Bewerten Sie Ihre Drucke im Verlauf, um den Bereich zu füllen.



{{img:stats}}
@@@ Remote-Access | Fern- und mobiler Zugriff
# Fern- und mobiler Zugriff

## Smartphone und Tablet
- **QR-Code** für den mobilen Zugriff auf die Bibliothek (**installierbare PWA**).
- **Android-Begleit-App**: Ein eigener QR-Code (Einstellungen → Mobiler Zugriff) lädt die APK herunter. Sie verwaltet interne und externe Adresse mit automatischem Wechsel, Kopplung per QR, Fotos direkt von einem Druck sowie Lesen/Schreiben von OpenPrintTag-NFC-Tags.
- **Update der Android-App**: Beim Start meldet ein Dialog die neue, auf GitHub veröffentlichte Version und bietet an, sie mit einem Tipp herunterzuladen und zu installieren (Prüfsumme wird kontrolliert).
- **Updates über die bestehende App**: Seit 1.1.0 ist die APK mit einem dauerhaften Schlüssel signiert. Zeigt Android „Paket steht in Konflikt mit einem vorhandenen Paket“, deinstallieren Sie die alte Version einmal und installieren Sie die neue; spätere Updates werden normal installiert.
- **Werkstattmodus** im Vollbild für Tablet/Smartphone.

{{img:android-update}}

**Menü auf kleinen Bildschirmen**: Die untere Leiste entfällt; eine Schaltfläche oben links öffnet dieselbe Seitenleiste wie am Computer (Kategorien + Panel rechts). Badges (laufender Druck, Benachrichtigungen, Banner) schrumpfen, damit sie nicht stören. Das Stellio-Logo erscheint auf den Einrichtungsseiten und bei „Server nicht erreichbar“.

{{img:mobile-drawer}}

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
- **Push**: ntfy, Gotify, Pushover, Telegram, Discord, Slack oder Webhook, auch bei geschlossenem Fenster (Druck beendet mit Dateiname und Dauer, Fehler, Wartung, Bestand, Drucker offline).

## Hausautomation
- **MQTT / Home Assistant**: Zustandsveröffentlichung und automatische Erkennung; MQTT-Gerät „Stellio" und Sensoren.

@@@ Desktop-Edition | Desktop-Edition
# Desktop-Edition

Die **Desktop-Edition** ist die Desktop-App: ein Stellio-Fenster auf Ihrem PC (Windows, macOS). Sie behält ihr ursprüngliches Verhalten; nur einige Funktionen für einen dauerhaft laufenden Server fehlen.

## Welche Edition habe ich?
| System | Standard-Edition |
|---|---|
| Windows, macOS | Desktop |
| Linux, Raspberry Pi, VM, LXC, Docker | Server |

Um die Wahl zu erzwingen (Tests, ein Linux-PC als Desktop):
```bash
STELLIO_SERVER_EDITION=0   # Desktop
STELLIO_SERVER_EDITION=1   # Server (auch STELLIO_HEADLESS=1 führt dorthin)
```

## Was für den Desktop typisch ist
- **Integriertes Fenster** (pywebview). Unter Windows ist das Öffnen von Stellio im Browser desselben PCs gesperrt (internes Token): Nutzen Sie das Fenster. Smartphone, APK und Tunnel bleiben erlaubt.
- Native **Windows-Benachrichtigungen**.
- **Slicer auf dem PC** werden automatisch erkannt (OrcaSlicer, Bambu Studio, PrusaSlicer, Cura…).
- **Quellen**: lokaler Ordner, Datei, SMB und NFS.
- **Daten** unter `%APPDATA%\Stellio` in Windows; in der portablen Version im Ordner `data` neben `Stellio.exe`.
- **Updates** von GitHub als `.zip`-Patch, vor der Installation geprüft.

## Der Server-Edition vorbehaltene Funktionen
Diese Funktionen antworten in der Desktop-App mit „der Server-Edition vorbehalten“:

| Funktion | Zweck |
|---|---|
| Online-KI | Claude, ChatGPT oder Gemini mit Ihrem Schlüssel |
| Importierte Slicer-Profile | Import aus Ihren Slicern exportierter Profile |
| Push-Benachrichtigungen | ntfy, Telegram, Discord, Webhook… |
| MQTT / Home Assistant | Statusveröffentlichung und automatische Erkennung |
| Periodische Zusammenfassung | Täglich oder wöchentlich |
| Sync zwischen zwei Instanzen | Werkzeuge › Sync |
| Ausgehende Webhooks | Signierte Nachrichten (HMAC-SHA256) an Ihre Dienste |
| Öffentliche API und mobiler Zugriff | Tokens mit begrenztem Umfang, /api/v1-Routen |

Der Eintrag **Sync** im Menü Werkzeuge ist am Desktop ausgeblendet, da er nur diese Meldung anzeigen würde.

## Erweiterte Werkstatt am Desktop
Alles andere funktioniert wie auf einem Server. Die Werkzeuge der Erweiterten Werkstatt stehen in der Seitenleiste, jedes in seiner Kategorie: **Bibliothek** (Organisation, 3D-Diff, Ähnliche, Lizenzen, Teileblatt), **Druck** (Kompatibilität, Druckprüfung, G-Code-Archive), **Materialien** (Materialbedarf), **Werkzeuge** (Platte, Fertigungsassistent) und **Administration** (Aufgaben, Datenbank, Audit-Protokoll, Teams, Sitzungen). Sie sind dem Besitzerkonto vorbehalten; jeder Eintrag hat in *Einstellungen › Navigationselemente* einen eigenen Schalter.

## Wechsel zur Server-Edition
Für ein dauerhaft laufendes Stellio, erreichbar über einen Browser, siehe [Server-Edition](de-Server-Edition) und [Installation](de-Installation).

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

## Nur dem Server vorbehaltene Funktionen (1.1.7)
Diese Funktionen gibt es in der Desktop-App nicht; ihre Routen antworten dort „der Server-Edition vorbehalten“:

| Funktion | Zweck |
|---|---|
| Online-KI | Claude, ChatGPT oder Gemini mit Ihrem Schlüssel statt Ollama (siehe [Künstliche Intelligenz](de-AI)) |
| Slicer-Profile | Import aus Ihren Slicern exportierter Profile |
| Push-Benachrichtigungen | ntfy, Gotify, Pushover, Telegram, Discord, Slack oder Webhook, auch bei geschlossenem Fenster |
| MQTT / Home Assistant | Statusveröffentlichung und automatische Erkennung |
| Periodische Zusammenfassung | Täglich oder wöchentlich, als Benachrichtigung und Push |
| Sync (Erweiterte Werkstatt) | Synchronisiert einen Ordner mit dem einer gekoppelten Instanz: erst Plan, dann bestätigte Anwendung, keine Löschung wird übertragen, bei Konflikt bleiben beide Versionen. Beide Instanzen müssen in der Server-Edition laufen |

Der Rest der Werkzeuge (Platte, Druckprüfung, G-Code-Archive …) funktioniert in beiden Editionen gleich.

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
- **Markendesigns**: Stellio, Bambu, Prusa, Voron, Creality; 33 Farbpaletten, eigene Akzentfarbe, einstellbares Hintergrundbild. Standardmäßig wird ein Stellio-Bild angeboten (Schaltfläche **Standardbild**).
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

@@@ Plugins | Plugins
# Plugins

Ein Plugin ist ein kleines Python-Programm, das auf ein Ereignis in Stellio reagiert (Druck beendet, Druck fehlgeschlagen, Auftrag verspätet, Drucker überlastet): eine Benachrichtigung senden, in eine Tabelle schreiben, eine Lampe einschalten … Plugins werden von ihren Autoren auf **GitHub** veröffentlicht; Stellio zeigt einen **öffentlichen Katalog** (Logo + Beschreibung) im Menü **Plugins › Katalog**, wo man sie mit einem Klick installiert.

Jedes Plugin trägt ein Badge: **Offiziell**, wenn es im Repository `stellio-app/stellio-plugins` gehostet wird, **Community**, wenn es anderswo gehostet (oder aus einer .zip installiert) wird. Stellio bestimmt das Badge anhand der tatsächlichen Adresse des Archivs: Lesen Sie bei Community-Plugins immer Berechtigungen und Code.

**Integrierte Plugins.** Einige Stellio-Funktionen werden als integrierte Plugins geliefert (BigPrint, Harz, USB-Drucker, Zeitraffer, Dateiwerkzeuge, Plattenstudio, Push-Benachrichtigungen, Webhooks, periodische Zusammenfassung, MQTT / Home Assistant, Obico, Teilen & Sync, Spoolman, KI-Anbieter und KI-Assistent, Stellio Pro). Sie sind Teil der App, werden aber nur geladen, wenn sie aktiviert sind (Abschnitt „Integrierte Plugins“ auf der Plugins-Seite; die Änderung gilt nach einem Neustart). **Update von einer früheren Version: nichts zu tun.** Beim ersten Start von 1.1.7 werden die Plugins, die Sie genutzt haben (z. B. aktiviertes MQTT, ein USB-Drucker, Webhooks, ein Zeitraffer), automatisch aktiviert und behalten genau ihre Einstellungen; Werkzeuge ohne Einstellungen (BigPrint, Dateiwerkzeuge, Plattenstudio) bleiben wie sie waren. Eine Neuinstallation aktiviert keines davon. Das Deaktivieren eines Plugins löscht nie seine Einstellungen. Weitere integrierte Plugins: Teilen & Sync, Spoolman, ein Plugin je KI-Anbieter + der KI-Assistent (aktiviert alle KI-Funktionen) und **Stellio Pro** (Kunden, Angebote, Rechnungen, Aufträge, Buchhaltung, Stromtarif, Planung, Materialbedarf, Teilelager): Sie fügen ihre Seiten und Schaltflächen nur im aktivierten Zustand hinzu.

## Ein Plugin verwenden
1. Öffnen Sie **Plugins › Katalog** (nur für das Besitzerkonto).
2. Durchsuchen Sie den Katalog und klicken Sie auf **Installieren**: Stellio lädt das Archiv herunter und prüft seine SHA-256-Prüfsumme.
3. Lesen Sie die angeforderten **Berechtigungen** und akzeptieren Sie sie. Das Plugin wird **deaktiviert** installiert.
4. Tragen Sie bei Bedarf die Konfiguration ein, aktivieren Sie das Plugin und klicken Sie auf **Test**, um es mit einem Testereignis auszulösen. Das Ausführungsprotokoll zeigt Ausgabe und Fehler.

Sie können auch ein lokales `.zip`-Archiv installieren (Plugin in Entwicklung) oder die Katalogquelle auf die URL eines anderen Katalogs ändern.

## Ein Plugin erstellen
### 1. Struktur
Ein Plugin ist ein flacher Ordner mit einer Datei `plugin.json` und einem Python-Skript:
```
mon-plugin/
├── plugin.json     Manifest (Pflicht)
├── main.py         Einstiegspunkt (beliebiger Name, in "entry" angegeben)
└── ...             Weitere Dateien: höchstens 100, 8 MB entpackt
```

### 2. Das Manifest plugin.json
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
| Feld | Zweck |
|---|---|
| `id` | Eindeutige Kennung: Kleinbuchstaben, Ziffern, `-` oder `_`, 2 bis 40 Zeichen |
| `name`, `description`, `author` | In Stellio angezeigter Text |
| `version` | Numerisch, zum Beispiel `1.2.0`; dient zum Erkennen von Updates |
| `api` | Version der Plugin-API: `1` |
| `entry` | Python-Skript im Hauptordner (Standard `main.py`) |
| `events` | Abonnierte Ereignisse |
| `permissions` | Angeforderte Rechte |
| `ui` | In Stellio angezeigte Seite: `title`, `icon` (Font Awesome) und `entry` (eine `.html`-Datei) |

### 3. Ereignisse und Berechtigungen
| Ereignis | Wird ausgelöst, wenn |
|---|---|
| `print.finished` | Ein Druck beendet ist |
| `print.failed` | Ein Druck fehlschlägt |
| `order.late` | Ein Auftrag seine Frist überschreitet |
| `printer.overload` | Ein Drucker überlastet ist |

| Berechtigung | Wirkung |
|---|---|
| `events` | Ereignisse empfangen (Pflicht, wenn `events` deklariert ist) |
| `api:read` | Daten über die öffentliche Stellio-API lesen |
| `api:write` | Daten über die öffentliche API ändern |
| `network` | Hinweis: Das Plugin greift auf das Internet zu |
| `ui` | Eine Plugin-Seite im Menü Plugins anzeigen |

### 4. Das Skript
Stellio startet `python -I main.py <Ereignis>` in einem separaten Prozess und sendet über die Standardeingabe ein JSON `{"event": "...", "data": {...}}`. Der Modus `-I` (isoliert) fügt den Plugin-Ordner nicht zum Python-Pfad hinzu: Um eine Datei Ihres Plugins zu importieren, fügen Sie diesen Pfad selbst hinzu. Die Standardausgabe wird im Protokoll gespeichert.
```python
import json, os, sys

payload = json.loads(sys.stdin.read() or "{}")
event, data = payload.get("event", ""), payload.get("data", {})
config = json.loads(os.environ.get("STELLIO_PLUGIN_CONFIG") or "{}")

print(f"{event}: {data.get('file_name') or data.get('printer') or '-'}")
```
Um auf Stellio zuzugreifen (Berechtigungen `api:*`), erhält das Skript `STELLIO_API_URL` und `STELLIO_API_TOKEN` (die Schlüssel `api_url` und `token` der Plugin-Konfiguration). Das Python-SDK `stellio_sdk.py` (Ordner `sdk/python` des Repositorys) bietet `plugin_event()`, `plugin_config()` und einen fertigen Client: Kopieren Sie es in Ihr Plugin und fügen Sie vor dem Import `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` hinzu. Ein vollständiges Beispiel finden Sie in `sdk/examples/hello-plugin`.

Grenzen: 10 Sekunden pro Ausführung, 512 MB Speicher, minimale Umgebung (nur `STELLIO_*`-Variablen sowie `PATH`). Auf dem Rechner, auf dem Stellio läuft, muss Python 3 installiert sein. Die Konfiguration ist eine Liste von Schlüssel/Wert-Paaren (Text, Zahl, Boolean) mit höchstens 4.000 Zeichen.

### 5. Testen
Packen Sie den **Inhalt** des Ordners als `mon-plugin.zip` (maximal 2 MB), installieren Sie es über **Plugins › Katalog** (lokales Archiv), akzeptieren Sie die Berechtigungen, aktivieren Sie es und nutzen Sie **Test**. Beheben Sie Fehler anhand des Protokolls.

## Plugin mit eigener Seite: Beispiel G-code-Betrachter

Ein Plugin kann auch **eine eigene Seite** in Stellio anzeigen. Es erscheint dann im Menü **Plugins** der Seitenleiste, unter „Katalog“, in der Liste „Installiert“: Ein Klick öffnet die Seite. Das Beispiel `sdk/examples/gcode-viewer` ist ein 3D-G-code-Betrachter: 3D-Ansicht (Drehen, Zoom), Schichtbereich, Wiedergabe der Bewegungen, Farben nach Typ, Geschwindigkeit oder Fluss, Leerfahrten und Retractions; in 8 Sprachen.

```json
{
  "id": "gcode-viewer",
  "name": "G-code viewer",
  "version": "1.0.0",
  "api": 1,
  "description": "Shows your archived G-code files layer by layer.",
  "author": "Stellio",
  "permissions": ["ui", "api:read"],
  "ui": {
    "title": "G-code viewer",
    "icon": "fa-layer-group",
    "entry": "viewer.html"
  }
}
```

- Die Seite ist **eine einzige eigenständige HTML-Datei** (CSS und JavaScript darin, Bilder als `data:`), höchstens 1 MB. Ohne Ereignisse braucht das Plugin kein Python-Skript.
- Sie wird in einem **isolierten** Rahmen angezeigt: kein Zugriff auf Netzwerk, Cookies oder den Rest von Stellio.
- Sie liest Stellio-Daten mit `window.stellio.api(Pfad)`: nur lesend (GET), die Berechtigung `api:read` ist Pflicht, das Ergebnis ist JSON oder Text mit `'text'` als zweitem Argument. Einstellungen, Konten, Sicherheit und Plugins sind tabu.
- Das Design liefern die CSS-Variablen `--st-bg`, `--st-panel`, `--st-card`, `--st-text`, `--st-muted`, `--st-border`, `--st-accent`, `--st-success`, `--st-warning` und `--st-danger`, die Sprache `window.stellio.lang`.

```js
document.addEventListener('stellio-ready', async () => {
  const list = await window.stellio.api('/api/gcodes?limit=50');
  const id = list.gcodes[0].id;
  const text = await window.stellio.api('/api/projects/gcodes/' + id + '/download', 'text');
});
```

Zum Ausprobieren: Packen Sie den Inhalt des Ordners `gcode-viewer`, installieren Sie das Archiv unter **Plugins › Katalog**, akzeptieren Sie die Berechtigungen, aktivieren Sie es und öffnen Sie es im Menü **Plugins**. Es wird mindestens ein archivierter G-code benötigt (Dateiblatt oder Projekt). Ein deaktiviertes Plugin bleibt in der Liste ausgegraut.

## Auf GitHub veröffentlichen
1. Erstellen Sie ein öffentliches Repository für Ihr Plugin mit Code, einer `README` und einer Lizenz.
2. Erstellen Sie für jede Version ein GitHub-**Release** und hängen Sie das Archiv `mon-plugin-1.0.0.zip` an.
3. Berechnen Sie die SHA-256-Prüfsumme des Archivs, die der Katalog benötigt:
```bash
sha256sum mon-plugin-1.0.0.zip
```
4. Erhöhen Sie vor jedem neuen Release stets `version` in `plugin.json`.

## Im Stellio-Katalog gelistet werden
Der offizielle Katalog ist eine Datei `catalog.json` im Repository `stellio-app/stellio-plugins`. Ihr Plugin fügen Sie per **Pull Request** hinzu.

1. Forken Sie das Repository `stellio-app/stellio-plugins`.
2. Fügen Sie den Eintrag Ihres Plugins in `catalog.json` hinzu:
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
3. Öffnen Sie den Pull Request: Eine automatische Prüfung kontrolliert Links, SHA-256-Prüfsumme und Logo, danach prüft das Stellio-Team das Plugin.

| Feld | Regel |
|---|---|
| `description` | Kurz (etwa 140 Zeichen); einfacher Text oder ein Text pro Sprache (`fr`, `en`, `de`, `es`, `pt`, `it`, `zh`, `ja`) |
| `url` | Direkter `https`-Link zum Archiv; `sha256` muss exakt übereinstimmen |
| `logo` | `https`, PNG, JPEG oder WebP, höchstens 200 KB, idealerweise 128 × 128 (SVG wird abgelehnt) |
| `homepage` | `https`-Link zur Plugin-Seite (optional) |
| `permissions` | Müssen mit denen des Manifests übereinstimmen |

**Aktualisieren**: Veröffentlichen Sie ein neues Release und öffnen Sie dann einen Pull Request, der `version`, `url` und `sha256` ändert. Verlangt die neue Version zusätzliche Berechtigungen, wird das Plugin beim Nutzer deaktiviert, bis er sie akzeptiert; seine Konfiguration bleibt erhalten.

## Sicherheit
- Ein Plugin läuft **nicht in einer Sandbox**: Es wird mit den Rechten von Stellio auf dem Rechner ausgeführt. Installieren Sie nur Plugins, deren Autor Sie vertrauen.
- Plugins werden deaktiviert installiert, und ihre Berechtigungen müssen akzeptiert werden.
- Downloads erfolgen nur über `https` von öffentlichen Adressen, mit SHA-256-Prüfung.
- Der Katalog wird vor der Veröffentlichung geprüft, ersetzt aber nicht Ihre eigene Sorgfalt: Lesen Sie Code und Berechtigungen.

Weiterführend: [Mitwirken](de-Contributing), die Datei `docs/plugins.md` des Repositorys und das Beispiel `sdk/examples/hello-plugin`.

## Administration und überwachte Instanzen
Das Plugin **Administration** (standardmäßig aktiv) bündelt auf einer Seite (Administration › Administration) die **Gastkonten und ihre Rollen**, Teams, Sitzungen, das Audit-Protokoll und die **Instanzen**.
- **Eigenständige Instanz** (Standard): volle Kontrolle, nichts ändert sich.
- **Hauptinstanz**: Der Unterreiter Instanzen listet die gekoppelten Stellio-Instanzen und erlaubt, sie zu überwachen.
- **Überwachte Instanz**: Nach der **Annahme** durch ihren Besitzer werden Konten, Rollen und Berechtigungen nur noch von der Hauptinstanz verwaltet; lokale Inhalte (Bibliothek, Drucker) bleiben privat, sofern der Besitzer bei der Annahme nichts anderes wählt; der Besitzer kann die **Überwachung jederzeit verlassen**.
Eine überwachte Instanz kann keine anderen überwachen, und eine Hauptinstanz kann nicht überwacht werden. Alle übrigen Einstellungen bleiben lokal änderbar.

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
├── release-notes/     notes.txt
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
