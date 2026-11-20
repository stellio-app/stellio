## Stellio v1.1.7
<details>
<summary><b>🇫🇷 Français</b></summary>

✓ Plugins intégrés : BigPrint, résine, imprimantes USB, timelapse, outils de fichiers, atelier plateau, partage et synchro, Spoolman, IA (Ollama, OpenAI, Anthropic, Gemini + Assistant IA), Stellio Pro (clients, devis, factures, commandes, compta, tarif d'énergie, planning, besoins en matière, stock de pièces), notifications push, webhooks, résumé périodique, MQTT / Home Assistant et Obico sortent du cœur : ils sont livrés avec Stellio et ne se chargent que s'ils sont activés (Plugins › Plugins intégrés, au redémarrage)  
✓ Mise à jour depuis la 1.1.6 sans rien perdre : au premier lancement, les plugins intégrés que vous utilisiez sont réactivés automatiquement, réglages, bases et fichiers inchangés (jamais contre un choix ultérieur)  
✓ Édition serveur (Linux) : notifications push externes, résumé périodique, MQTT / Home Assistant, webhooks, API publique, synchronisation entre instances et accès mobile ; ces fonctions sont masquées et désactivées sous Windows  
✓ Atelier avancé : nouvelles fonctions rangées dans la barre latérale, chacune dans sa catégorie — Bibliothèque (Organisation, Diff 3D, Similaires, Licences, Fiche pièce), Impression (Compatibilité, Vérif. impression, Archives G-code), Matières (Besoins matière), Outils (Plateau, Synchro, Assistant de fabrication) et la nouvelle catégorie Administration (Tâches, Base de données, Journal d'audit, Équipes, Sessions) ; chaque entrée a son interrupteur dans Paramètres › Éléments de navigation  
✓ Organisation automatique de la bibliothèque : règles par extension, nom, licence, matière, taille, auteur, catégorie ou âge du fichier, créées et supprimées depuis un formulaire, avec aperçu lisible, confirmation et annulation  
✓ Diff 3D visuel entre deux versions d'un modèle (nuage de points coloré : retiré, ajouté, inchangé ; STEP compris) et recherche de pièces similaires par forme, avec miniatures  
✓ Licences : suggestions de licences courantes, badge « usage commercial autorisé / interdit / à vérifier », date d'expiration par fichier et notifications quand une licence expire bientôt ou a expiré  
✓ Fiche pièce : tout ce que Stellio sait d'un modèle sur une page (origine et licence, versions, impressions, meilleure combinaison, G-code archivés, photos)  
✓ Impression : compatibilité modèle ↔ imprimantes (volume, buse, matière), vérification avant impression (surplombs, supports estimés, base, maillage, tenue dans le plateau, orientation conseillée avec copie orientée) et archive du G-code de chaque impression (compressé, empreinte SHA-256) ; nouvelle page Timelapses dans le menu Impression  
✓ Plateau multi-modèles : disposition sur la vraie géométrie (imbrication, rotation libre), plusieurs plateaux, éditeur 2D et vue 3D, plusieurs exemplaires d'une pièce, liste des modèles avec retrait, bouton « Organisation automatique », taille prise d'une imprimante, export 3MF avec indicateur de progression  
✓ Matières et production : besoins en matière (file d'impression et projets contre stock : manque en grammes, bobines à commander) ; Planning avec coût total par commande, rendement et déchets, retards, rentabilité par imprimante (marge, marge par heure) et temps de travail humain × taux horaire  
✓ Traçabilité : « Rattacher à une version » sur chaque impression, « Associer à un modèle » sur un G-code, profils de slicer reconnus par l'empreinte de leurs réglages, historique enrichi (températures, slicer lus dans le G-code)  
✓ Statistiques › Stellio Intelligence : réglages recommandés (meilleur profil par matière / imprimante) et causes probables d'échec, appris de vos impressions notées — des statistiques, pas un modèle d'IA, avec le nombre d'impressions sur lesquelles chaque résultat repose  
✓ Assistants : assistant de bibliothèque (baguette, 1re puce des collections) et assistant de fabrication, réponses lisibles ; l'IA, si elle est configurée, choisit seulement une requête dans une liste fermée, en lecture seule, sans accéder directement à vos données  
✓ API publique (Paramètres › API publique) : jetons à portée limitée, routes /api/v1 (fichiers, imprimantes, matières, historique, projets, tâches ; écriture des bobines et des projets), documentation OpenAPI, SDK Python et JavaScript ; webhooks sortants signés (HMAC-SHA256) avec nouvelles tentatives et journal  
✓ Équipes et sécurité : rôles (administrateur, gestionnaire, opérateur, utilisateur simple, invité), permissions par dossier, projet et imprimante, espaces de travail partagés, sessions actives révocables, journal des connexions, journal d'audit paginé et exportable en CSV  
✓ Plugins : nouveau menu Plugins (catalogue, plugins installés), plugins qui affichent leur propre page (exemple : visionneuse de G-code 3D), badges « Officiel » / « Communautaire », mise à jour avec permissions à réaccepter, catalogue https avec empreinte SHA-256 obligatoire, exécution en processus séparé ; l'onglet Communauté de l'Atelier est grisé (« Bientôt »)  
✓ Plugin Administration : une page unique (comptes invités et rôles, équipes, sessions, journal d'audit) et supervision d'instances — l'instance principale liste les instances Stellio appairées ; une instance n'est supervisée qu'après acceptation de son propriétaire (comptes, rôles et permissions gérés depuis la principale, contenu local conservé, sortie possible à tout moment) ; une instance non connectée garde le contrôle total  
✓ Centre de notifications : « Tout voir » ouvre une page avec toutes les notifications, filtrables par rubrique (filament faible, filament à recommander, pièces, impressions, maintenance) et par recherche  
✓ Page Collections dans la Bibliothèque : chaque collection est une section dépliable (nom, nombre de fichiers) qui affiche ses fichiers, avec création rapide  
✓ Coût d'une impression : si un G-code est joint au fichier, son poids et sa durée réels servent au calcul, au lieu d'une estimation  
✓ Grandes bibliothèques : testées à 50 000 modèles (étiquettes perdues au-delà de 32 000 fichiers, grille entière dessinée, analyses trop lentes : corrigés) ; sélecteur de modèle avec source, recherche, filtre par format (STL, 3MF…), miniatures et pagination ; BigPrint, déplacé dans Outils, pagine son sélecteur  
✓ Fichiers STL géants : lecture en flux (binaire et texte), miniature et viewer sur une version simplifiée, seuil de chargement adapté à la mémoire libre (256 Mo à 1 Go) et action « Créer une version allégée » (copie simplifiée à côté de l'original, jamais modifié), proposée aussi quand une réparation est refusée pour taille  
✓ Robustesse : miniatures des gros fichiers dessinées dans un processus séparé (un plantage ou une saturation ne fait plus tomber l'application, le fichier est mis de côté), garde-fou au démarrage et crash_trace.log ; les copies temporaires des fichiers du NAS (SMB) ne remplissent plus le disque ; miniature par défaut épurée  
✓ Base de données : migrations versionnées avec reprise automatique, gestionnaire unique des tâches de fond (progression, annulation), tests de mise à niveau d'une ancienne base  
✓ Interface : popup des alertes du widget Santé, badge « Mise à jour disponible », « Réessayer » avec indicateur sur l'application téléphone, langue dans sa propre section des réglages, barre latérale qui ne reste plus à moitié ouverte ; imprimantes résine et USB ne sont plus étiquetées bêta ; nouveaux textes traduits dans les 8 langues  
✓ Paramètres : chaque menu s'ouvre dans une popup qui montre tous ses réglages, sans animation ; Administration : demande de supervision en popup Accepter / Refuser sur l'instance visée, badge d'état mis à jour tout seul, ajout des comptes aux équipes  
✓ MQTT / Home Assistant : la disponibilité est republiée à chaque cycle et au démarrage de Home Assistant (entités restées « indisponibles »)  
✓ Correctifs : favoris MakerWorld non importés (erreur « '<' not supported between int and NoneType »), erreur 500 possible au premier lancement sur la liste des devis  
</details>

<details>
<summary><b>🇬🇧 English</b></summary>

✓ Built-in plugins: BigPrint, resin, USB printers, timelapse, file tools, plate studio, sharing & sync, Spoolman, AI (Ollama, OpenAI, Anthropic, Gemini + AI assistant), Stellio Pro (clients, quotes, invoices, orders, accounting, energy rates, planning, material needs, parts stock), push notifications, webhooks, periodic digest, MQTT / Home Assistant and Obico move out of the core: they ship with Stellio and load only when enabled (Plugins › Built-in plugins, after a restart)  
✓ Updating from 1.1.6 loses nothing: on first launch, the built-in plugins you were using are re-enabled automatically, with settings, databases and files unchanged (never against a later choice of yours)  
✓ Server edition (Linux): external push notifications, periodic digest, MQTT / Home Assistant, webhooks, public API, sync between instances and mobile access; these are hidden and disabled on Windows  
✓ Advanced workshop: new tools placed in the sidebar, each in its own category — Library (Organization, 3D diff, Similar, Licenses, Part sheet), Print (Compatibility, Print check, G-code archives), Materials (Material needs), Tools (Plate, Sync, Fabrication assistant) and the new Administration category (Tasks, Database, Audit log, Teams, Sessions); each entry has its own switch in Settings › Navigation items  
✓ Automatic library organization: rules by extension, name, license, material, size, author, category or file age, created and deleted from a form, with a readable preview, confirmation and undo  
✓ Visual 3D diff between two versions of a model (colored point cloud: removed, added, unchanged; STEP included) and similar-part search by shape, with thumbnails  
✓ Licenses: common license suggestions, a "commercial use allowed / forbidden / to check" badge, an expiry date per file and notifications when a license is about to expire or has expired  
✓ Part sheet: everything Stellio knows about a model on one page (origin and license, versions, prints, best combination, archived G-code, photos)  
✓ Printing: model ↔ printer compatibility (volume, nozzle, material), pre-print check (overhangs, estimated supports, base, mesh, fit on the bed, suggested orientation with an oriented copy) and an archive of each print's G-code (compressed, SHA-256 fingerprint); new Timelapses page in the Print menu  
✓ Multi-model plate: layout on the real geometry (nesting, free rotation), several plates, 2D editor and 3D view, several copies of a part, model list with removal, "Automatic layout" button, size taken from a printer, 3MF export with a progress indicator  
✓ Materials and production: material needs (print queue and projects against stock: shortfall in grams, spools to order); Planning with total cost per order, yield and waste, delays, profitability per printer (margin, margin per hour) and human labor time × hourly rate  
✓ Traceability: "Attach to a version" on every print, "Link to a model" on a G-code, slicer profiles recognized by the fingerprint of their settings, richer history (temperatures and slicer read from the G-code)  
✓ Statistics › Stellio Intelligence: recommended settings (best profile per material / printer) and likely causes of failure, learned from your rated prints — statistics, not an AI model, showing how many prints each result rests on  
✓ Assistants: library assistant (magic wand, first chip of the collections) and fabrication assistant, with readable answers; the AI, if configured, only picks a query from a closed list, read-only, without direct access to your data  
✓ Public API (Settings › Public API): scoped tokens, /api/v1 routes (files, printers, materials, history, projects, tasks; writing spools and projects), OpenAPI documentation, Python and JavaScript SDKs; signed outgoing webhooks (HMAC-SHA256) with retries and a log  
✓ Teams and security: roles (administrator, manager, operator, simple user, guest), per-folder, project and printer permissions, shared workspaces, revocable active sessions, login log, audit log with pagination and CSV export  
✓ Plugins: new Plugins menu (catalog, installed plugins), plugins that show their own page (example: 3D G-code viewer), "Official" / "Community" badges, updates with permissions to re-accept, https catalog with mandatory SHA-256 fingerprint, separate-process execution; the workshop's Community tab is greyed out ("Coming soon")  
✓ Administration plugin: a single page (guest accounts and roles, teams, sessions, audit log) and instance supervision — the primary instance lists the paired Stellio instances; an instance is only supervised once its owner accepts (accounts, roles and permissions managed from the primary, local content kept, can leave at any time); an unconnected instance keeps full control  
✓ Notification center: “See all” opens a page with every notification, filterable by category (low filament, filament to reorder, parts, prints, maintenance) and searchable  
✓ Collections page in the Library: each collection is a collapsible section (name, file count) that shows its files, with quick creation  
✓ Print cost: when a G-code is attached to the file, its real weight and duration are used for the calculation instead of an estimate  
✓ Large libraries: tested at 50,000 models (labels lost beyond 32,000 files, whole grid drawn, slow analyses: fixed); model picker with source, search, format filter (STL, 3MF…), thumbnails and pagination; BigPrint, moved to Tools, paginates its picker  
✓ Giant STL files: streamed reading (binary and text), thumbnail and viewer on a simplified version, load threshold adapted to free memory (256 MB to 1 GB) and a "Create a lightweight version" action (a simplified copy next to the original, which is never modified), also offered when a repair is refused because of size  
✓ Robustness: thumbnails of large files drawn in a separate process (a crash or memory exhaustion no longer takes the app down, the file is set aside), startup guard and crash_trace.log; temporary copies of NAS (SMB) files no longer fill the disk; cleaner default thumbnail  
✓ Database: versioned migrations with automatic resume, a single background-task manager (progress, cancel), upgrade tests from an old database  
✓ Interface: Health widget alerts popup, "Update available" badge, "Retry" with an indicator on the phone app, language in its own settings section, sidebar that no longer stays half-open; resin and USB printers are no longer labeled beta; new texts translated into all 8 languages  
✓ Settings: each menu opens in a popup showing all its settings, without animation; Administration: supervision request as an Accept / Refuse popup on the target instance, status badge updating by itself, adding accounts to teams  
✓ MQTT / Home Assistant: availability is republished every cycle and when Home Assistant starts (entities that stayed "unavailable")  
✓ Fixes: MakerWorld favorites not imported ("'<' not supported between int and NoneType" error), possible 500 error on first launch on the quotes list  
</details>

<details>
<summary><b>🇩🇪 Deutsch</b></summary>

✓ Integrierte Plugins: BigPrint, Resin, USB-Drucker, Timelapse, Dateitools, Plattenstudio, Teilen & Sync, Spoolman, KI (Ollama, OpenAI, Anthropic, Gemini + KI-Assistent), Stellio Pro (Kunden, Angebote, Rechnungen, Aufträge, Buchhaltung, Stromtarif, Planung, Materialbedarf, Teilelager), Push-Benachrichtigungen, Webhooks, periodische Zusammenfassung, MQTT / Home Assistant und Obico verlassen den Kern: Sie werden mit Stellio ausgeliefert und nur geladen, wenn sie aktiviert sind (Plugins › Integrierte Plugins, nach einem Neustart)  
✓ Update von 1.1.6 ohne Verlust: Beim ersten Start werden die integrierten Plugins, die Sie genutzt haben, automatisch wieder aktiviert, Einstellungen, Datenbanken und Dateien bleiben unverändert (nie gegen eine spätere Entscheidung von Ihnen)  
✓ Server-Edition (Linux): externe Push-Benachrichtigungen, periodische Zusammenfassung, MQTT / Home Assistant, Webhooks, öffentliche API, Synchronisierung zwischen Instanzen und mobiler Zugriff; unter Windows ausgeblendet und deaktiviert  
✓ Erweiterte Werkstatt: neue Werkzeuge in der Seitenleiste, jeweils in ihrer Kategorie — Bibliothek (Organisation, 3D-Diff, Ähnliche, Lizenzen, Teileblatt), Druck (Kompatibilität, Druckprüfung, G-Code-Archive), Materialien (Materialbedarf), Werkzeuge (Platte, Sync, Fertigungsassistent) und die neue Kategorie Administration (Aufgaben, Datenbank, Audit-Protokoll, Teams, Sitzungen); jeder Eintrag hat in Einstellungen › Navigationselemente einen eigenen Schalter  
✓ Automatische Bibliotheksorganisation: Regeln nach Erweiterung, Name, Lizenz, Material, Größe, Autor, Kategorie oder Dateialter, per Formular erstellt und gelöscht, mit lesbarer Vorschau, Bestätigung und Rückgängig  
✓ Visueller 3D-Diff zwischen zwei Modellversionen (farbige Punktwolke: entfernt, hinzugefügt, unverändert; STEP inklusive) und Suche ähnlicher Teile nach Form, mit Vorschaubildern  
✓ Lizenzen: Vorschläge gängiger Lizenzen, Abzeichen „kommerzielle Nutzung erlaubt / verboten / prüfen“, Ablaufdatum pro Datei und Benachrichtigungen, wenn eine Lizenz bald abläuft oder abgelaufen ist  
✓ Teileblatt: alles, was Stellio über ein Modell weiß, auf einer Seite (Herkunft und Lizenz, Versionen, Drucke, beste Kombination, archivierter G-Code, Fotos)  
✓ Druck: Kompatibilität Modell ↔ Drucker (Volumen, Düse, Material), Prüfung vor dem Druck (Überhänge, geschätzte Stützen, Basis, Netz, Passung auf der Platte, empfohlene Ausrichtung mit ausgerichteter Kopie) und Archiv des G-Codes jedes Drucks (komprimiert, SHA-256-Fingerabdruck); neue Seite Timelapses im Druckmenü  
✓ Mehrmodell-Platte: Anordnung auf der echten Geometrie (Verschachtelung, freie Drehung), mehrere Platten, 2D-Editor und 3D-Ansicht, mehrere Kopien eines Teils, Modellliste mit Entfernen, Schaltfläche „Automatische Anordnung“, Größe aus einem Drucker übernommen, 3MF-Export mit Fortschrittsanzeige  
✓ Materialien und Produktion: Materialbedarf (Druckwarteschlange und Projekte gegen Bestand: Fehlmenge in Gramm, zu bestellende Spulen); Planung mit Gesamtkosten pro Auftrag, Ausbeute und Ausschuss, Verzögerungen, Rentabilität pro Drucker (Marge, Marge pro Stunde) und menschlicher Arbeitszeit × Stundensatz  
✓ Rückverfolgbarkeit: „An eine Version anhängen“ bei jedem Druck, „Mit einem Modell verknüpfen“ bei einem G-Code, Slicer-Profile anhand des Fingerabdrucks ihrer Einstellungen erkannt, reicherer Verlauf (Temperaturen und Slicer aus dem G-Code gelesen)  
✓ Statistik › Stellio Intelligence: empfohlene Einstellungen (bestes Profil je Material / Drucker) und wahrscheinliche Fehlerursachen, gelernt aus Ihren bewerteten Drucken — Statistik, kein KI-Modell, mit der Anzahl der Drucke, auf denen jedes Ergebnis beruht  
✓ Assistenten: Bibliotheksassistent (Zauberstab, erster Chip der Sammlungen) und Fertigungsassistent mit lesbaren Antworten; die KI wählt, falls konfiguriert, nur eine Abfrage aus einer geschlossenen Liste, nur lesend und ohne direkten Zugriff auf Ihre Daten  
✓ Öffentliche API (Einstellungen › Öffentliche API): Tokens mit begrenztem Umfang, /api/v1-Routen (Dateien, Drucker, Materialien, Verlauf, Projekte, Aufgaben; Schreiben von Spulen und Projekten), OpenAPI-Dokumentation, Python- und JavaScript-SDKs; signierte ausgehende Webhooks (HMAC-SHA256) mit Wiederholungen und Protokoll  
✓ Teams und Sicherheit: Rollen (Administrator, Manager, Bediener, einfacher Benutzer, Gast), Berechtigungen pro Ordner, Projekt und Drucker, gemeinsame Arbeitsbereiche, widerrufbare aktive Sitzungen, Anmeldeprotokoll, seitenweises Audit-Protokoll mit CSV-Export  
✓ Plugins: neues Plugins-Menü (Katalog, installierte Plugins), Plugins mit eigener Seite (Beispiel: 3D-G-Code-Viewer), Abzeichen „Offiziell“ / „Community“, Updates mit erneut zu bestätigenden Berechtigungen, https-Katalog mit verpflichtendem SHA-256-Fingerabdruck, Ausführung in separatem Prozess; der Tab Community der Werkstatt ist ausgegraut („Demnächst“)  
✓ Plugin Administration: eine einzige Seite (Gastkonten und Rollen, Teams, Sitzungen, Audit-Protokoll) und Instanzüberwachung — die Hauptinstanz listet die gekoppelten Stellio-Instanzen; eine Instanz wird erst nach Zustimmung ihres Besitzers überwacht (Konten, Rollen und Berechtigungen von der Hauptinstanz verwaltet, lokale Inhalte bleiben erhalten, Austritt jederzeit möglich); eine nicht verbundene Instanz behält die volle Kontrolle  
✓ Benachrichtigungen: „Alle anzeigen“ öffnet eine Seite mit allen Benachrichtigungen, filterbar nach Rubrik (Filament fast leer, Filament nachbestellen, Teile, Drucke, Wartung) und durchsuchbar  
✓ Seite „Sammlungen“ in der Bibliothek: Jede Sammlung ist ein aufklappbarer Abschnitt (Name, Dateianzahl) mit ihren Dateien, inklusive schnellem Anlegen  
✓ Druckkosten: Ist der Datei ein G-Code angehängt, werden dessen reales Gewicht und reale Dauer statt einer Schätzung verwendet  
✓ Große Bibliotheken: mit 50.000 Modellen getestet (verlorene Tags ab 32.000 Dateien, komplett gezeichnetes Raster, langsame Analysen: behoben); Modellauswahl mit Quelle, Suche, Formatfilter (STL, 3MF …), Vorschaubildern und Seiten; BigPrint, jetzt unter Werkzeuge, paginiert seine Auswahl  
✓ Riesige STL-Dateien: Streaming-Lesen (binär und Text), Vorschaubild und Viewer auf einer vereinfachten Version, Ladeschwelle passend zum freien Speicher (256 MB bis 1 GB) und Aktion „Leichte Version erstellen“ (vereinfachte Kopie neben dem Original, das nie verändert wird), auch angeboten, wenn eine Reparatur wegen der Größe abgelehnt wird  
✓ Robustheit: Vorschaubilder großer Dateien werden in einem separaten Prozess gezeichnet (Absturz oder Speicherüberlauf reißt die App nicht mehr mit, die Datei wird beiseitegelegt), Startschutz und crash_trace.log; temporäre Kopien von NAS-Dateien (SMB) füllen die Platte nicht mehr; schlichteres Standard-Vorschaubild  
✓ Datenbank: versionierte Migrationen mit automatischer Wiederaufnahme, ein einziger Manager für Hintergrundaufgaben (Fortschritt, Abbrechen), Upgrade-Tests einer alten Datenbank  
✓ Oberfläche: Popup der Health-Widget-Warnungen, Abzeichen „Update verfügbar“, „Erneut versuchen“ mit Anzeige in der Handy-App, Sprache in eigenem Einstellungsabschnitt, Seitenleiste, die nicht mehr halb geöffnet bleibt; Resin- und USB-Drucker sind nicht mehr als Beta gekennzeichnet; neue Texte in allen 8 Sprachen übersetzt  
✓ Einstellungen: Jedes Menü öffnet sich in einem Popup mit allen Einstellungen, ohne Animation; Administration: Überwachungsanfrage als Popup Annehmen / Ablehnen auf der Zielinstanz, Statusanzeige aktualisiert sich selbst, Konten zu Teams hinzufügen  
✓ MQTT / Home Assistant: Die Verfügbarkeit wird bei jedem Zyklus und beim Start von Home Assistant neu veröffentlicht (Entitäten blieben „nicht verfügbar“)  
✓ Korrekturen: MakerWorld-Favoriten wurden nicht importiert (Fehler „'<' not supported between int and NoneType“), möglicher 500-Fehler beim ersten Start in der Angebotsliste  
</details>

<details>
<summary><b>🇪🇸 Español</b></summary>

✓ Plugins integrados: BigPrint, resina, impresoras USB, timelapse, herramientas de archivos, estudio de bandeja, compartir y sincronizar, Spoolman, IA (Ollama, OpenAI, Anthropic, Gemini + asistente de IA), Stellio Pro (clientes, presupuestos, facturas, pedidos, contabilidad, tarifa de energía, planificación, necesidades de material, stock de piezas), notificaciones push, webhooks, resumen periódico, MQTT / Home Assistant y Obico salen del núcleo: se entregan con Stellio y solo se cargan si están activados (Plugins › Plugins integrados, tras reiniciar)  
✓ Actualizar desde la 1.1.6 sin perder nada: en el primer inicio, los plugins integrados que usabas se reactivan solos, con ajustes, bases de datos y archivos intactos (nunca contra una elección posterior tuya)  
✓ Edición servidor (Linux): notificaciones push externas, resumen periódico, MQTT / Home Assistant, webhooks, API pública, sincronización entre instancias y acceso móvil; ocultos y desactivados en Windows  
✓ Taller avanzado: las nuevas herramientas se colocan en la barra lateral, cada una en su categoría — Biblioteca (Organización, Diff 3D, Similares, Licencias, Ficha de pieza), Impresión (Compatibilidad, Verificación de impresión, Archivos G-code), Materiales (Necesidades de material), Herramientas (Bandeja, Sincronización, Asistente de fabricación) y la nueva categoría Administración (Tareas, Base de datos, Registro de auditoría, Equipos, Sesiones); cada entrada tiene su interruptor en Ajustes › Elementos de navegación  
✓ Organización automática de la biblioteca: reglas por extensión, nombre, licencia, material, tamaño, autor, categoría o antigüedad del archivo, creadas y eliminadas desde un formulario, con vista previa legible, confirmación y deshacer  
✓ Diff 3D visual entre dos versiones de un modelo (nube de puntos en color: eliminado, añadido, sin cambios; STEP incluido) y búsqueda de piezas similares por forma, con miniaturas  
✓ Licencias: sugerencias de licencias comunes, insignia «uso comercial permitido / prohibido / por comprobar», fecha de caducidad por archivo y notificaciones cuando una licencia caduca pronto o ha caducado  
✓ Ficha de pieza: todo lo que Stellio sabe de un modelo en una página (origen y licencia, versiones, impresiones, mejor combinación, G-code archivados, fotos)  
✓ Impresión: compatibilidad modelo ↔ impresoras (volumen, boquilla, material), verificación previa (voladizos, soportes estimados, base, malla, ajuste en la bandeja, orientación aconsejada con copia orientada) y archivo del G-code de cada impresión (comprimido, huella SHA-256); nueva página Timelapses en el menú Impresión  
✓ Bandeja multimodelo: disposición sobre la geometría real (anidado, rotación libre), varias bandejas, editor 2D y vista 3D, varias copias de una pieza, lista de modelos con botón de retirar, botón «Organización automática», tamaño tomado de una impresora, exportación 3MF con indicador de progreso  
✓ Materiales y producción: necesidades de material (cola de impresión y proyectos frente al stock: falta en gramos, bobinas por pedir); Planificación con coste total por pedido, rendimiento y desperdicio, retrasos, rentabilidad por impresora (margen, margen por hora) y tiempo de trabajo humano × tarifa horaria  
✓ Trazabilidad: «Asociar a una versión» en cada impresión, «Vincular a un modelo» en un G-code, perfiles de slicer reconocidos por la huella de sus ajustes, historial enriquecido (temperaturas y slicer leídos del G-code)  
✓ Estadísticas › Stellio Intelligence: ajustes recomendados (mejor perfil por material / impresora) y causas probables de fallo, aprendidos de tus impresiones valoradas — estadísticas, no un modelo de IA, indicando en cuántas impresiones se basa cada resultado  
✓ Asistentes: asistente de biblioteca (varita mágica, primer chip de las colecciones) y asistente de fabricación, con respuestas legibles; la IA, si está configurada, solo elige una consulta de una lista cerrada, en solo lectura y sin acceso directo a tus datos  
✓ API pública (Ajustes › API pública): tokens de alcance limitado, rutas /api/v1 (archivos, impresoras, materiales, historial, proyectos, tareas; escritura de bobinas y proyectos), documentación OpenAPI, SDK de Python y JavaScript; webhooks salientes firmados (HMAC-SHA256) con reintentos y registro  
✓ Equipos y seguridad: roles (administrador, gestor, operador, usuario simple, invitado), permisos por carpeta, proyecto e impresora, espacios de trabajo compartidos, sesiones activas revocables, registro de conexiones, registro de auditoría paginado y exportable a CSV  
✓ Plugins: nuevo menú Plugins (catálogo, plugins instalados), plugins que muestran su propia página (ejemplo: visor de G-code 3D), insignias «Oficial» / «Comunitario», actualización con permisos que hay que volver a aceptar, catálogo https con huella SHA-256 obligatoria, ejecución en proceso aparte; la pestaña Comunidad del taller está atenuada («Próximamente»)  
✓ Plugin Administración: una sola página (cuentas de invitado y roles, equipos, sesiones, registro de auditoría) y supervisión de instancias — la instancia principal lista las instancias Stellio emparejadas; una instancia solo se supervisa tras la aceptación de su propietario (cuentas, roles y permisos gestionados desde la principal, contenido local conservado, salida posible en cualquier momento); una instancia no conectada conserva el control total  
✓ Centro de notificaciones: «Ver todo» abre una página con todas las notificaciones, filtrables por categoría (filamento bajo, filamento por reponer, piezas, impresiones, mantenimiento) y con búsqueda  
✓ Página Colecciones en la Biblioteca: cada colección es una sección desplegable (nombre, número de archivos) que muestra sus archivos, con creación rápida  
✓ Coste de una impresión: si hay un G-code adjunto al archivo, su peso y duración reales se usan en el cálculo en lugar de una estimación  
✓ Bibliotecas grandes: probadas con 50 000 modelos (etiquetas perdidas a partir de 32 000 archivos, cuadrícula entera dibujada, análisis lentos: corregidos); selector de modelo con origen, búsqueda, filtro por formato (STL, 3MF…), miniaturas y paginación; BigPrint, ahora en Herramientas, pagina su selector  
✓ Archivos STL gigantes: lectura en flujo (binario y texto), miniatura y visor sobre una versión simplificada, umbral de carga adaptado a la memoria libre (256 MB a 1 GB) y acción «Crear una versión ligera» (copia simplificada junto al original, que nunca se modifica), también propuesta cuando se rechaza una reparación por tamaño  
✓ Robustez: miniaturas de archivos grandes dibujadas en un proceso aparte (un fallo o una saturación de memoria ya no tumba la aplicación, el archivo se aparta), protección al arrancar y crash_trace.log; las copias temporales de archivos del NAS (SMB) ya no llenan el disco; miniatura por defecto más sobria  
✓ Base de datos: migraciones versionadas con reanudación automática, gestor único de tareas en segundo plano (progreso, cancelación), pruebas de actualización desde una base antigua  
✓ Interfaz: ventana emergente de las alertas del widget Salud, insignia «Actualización disponible», «Reintentar» con indicador en la aplicación del teléfono, idioma en su propia sección de ajustes, barra lateral que ya no queda medio abierta; las impresoras de resina y USB ya no se etiquetan como beta; textos nuevos traducidos a los 8 idiomas  
✓ Ajustes: cada menú se abre en una ventana con todos sus ajustes, sin animación; Administración: solicitud de supervisión como ventana Aceptar / Rechazar en la instancia destino, insignia de estado que se actualiza sola, añadir cuentas a los equipos  
✓ MQTT / Home Assistant: la disponibilidad se vuelve a publicar en cada ciclo y al arrancar Home Assistant (entidades que seguían «no disponibles»)  
✓ Correcciones: favoritos de MakerWorld que no se importaban (error «'<' not supported between int and NoneType»), posible error 500 en el primer inicio en la lista de presupuestos  
</details>

<details>
<summary><b>🇵🇹 Português</b></summary>

✓ Plugins integrados: BigPrint, resina, impressoras USB, timelapse, ferramentas de ficheiros, estúdio de mesa, partilha e sincronização, Spoolman, IA (Ollama, OpenAI, Anthropic, Gemini + assistente de IA), Stellio Pro (clientes, orçamentos, faturas, encomendas, contabilidade, tarifa de energia, planeamento, necessidades de material, stock de peças), notificações push, webhooks, resumo periódico, MQTT / Home Assistant e Obico saem do núcleo: vêm com o Stellio e só são carregados se estiverem ativados (Plugins › Plugins integrados, após reiniciar)  
✓ Atualizar da 1.1.6 sem perder nada: no primeiro arranque, os plugins integrados que utilizava são reativados automaticamente, com definições, bases de dados e ficheiros inalterados (nunca contra uma escolha sua posterior)  
✓ Edição servidor (Linux): notificações push externas, resumo periódico, MQTT / Home Assistant, webhooks, API pública, sincronização entre instâncias e acesso móvel; ocultos e desativados no Windows  
✓ Oficina avançada: as novas ferramentas ficam na barra lateral, cada uma na sua categoria — Biblioteca (Organização, Diff 3D, Semelhantes, Licenças, Ficha da peça), Impressão (Compatibilidade, Verificação de impressão, Arquivos G-code), Materiais (Necessidades de material), Ferramentas (Mesa, Sincronização, Assistente de fabrico) e a nova categoria Administração (Tarefas, Base de dados, Registo de auditoria, Equipas, Sessões); cada entrada tem o seu interruptor em Definições › Elementos de navegação  
✓ Organização automática da biblioteca: regras por extensão, nome, licença, material, tamanho, autor, categoria ou idade do ficheiro, criadas e eliminadas num formulário, com pré-visualização legível, confirmação e anulação  
✓ Diff 3D visual entre duas versões de um modelo (nuvem de pontos colorida: removido, adicionado, inalterado; STEP incluído) e pesquisa de peças semelhantes pela forma, com miniaturas  
✓ Licenças: sugestões de licenças comuns, distintivo «uso comercial permitido / proibido / a verificar», data de validade por ficheiro e notificações quando uma licença está prestes a expirar ou expirou  
✓ Ficha da peça: tudo o que o Stellio sabe sobre um modelo numa página (origem e licença, versões, impressões, melhor combinação, G-code arquivados, fotografias)  
✓ Impressão: compatibilidade modelo ↔ impressoras (volume, bico, material), verificação antes de imprimir (saliências, suportes estimados, base, malha, ajuste na mesa, orientação aconselhada com cópia orientada) e arquivo do G-code de cada impressão (comprimido, impressão digital SHA-256); nova página Timelapses no menu Impressão  
✓ Mesa multimodelo: disposição sobre a geometria real (encaixe, rotação livre), várias mesas, editor 2D e vista 3D, várias cópias de uma peça, lista de modelos com botão para retirar, botão «Organização automática», tamanho tirado de uma impressora, exportação 3MF com indicador de progresso  
✓ Materiais e produção: necessidades de material (fila de impressão e projetos contra o stock: falta em gramas, bobinas a encomendar); Planeamento com custo total por encomenda, rendimento e desperdício, atrasos, rentabilidade por impressora (margem, margem por hora) e tempo de trabalho humano × taxa horária  
✓ Rastreabilidade: «Associar a uma versão» em cada impressão, «Ligar a um modelo» num G-code, perfis de slicer reconhecidos pela impressão digital das suas definições, histórico enriquecido (temperaturas e slicer lidos do G-code)  
✓ Estatísticas › Stellio Intelligence: definições recomendadas (melhor perfil por material / impressora) e causas prováveis de falha, aprendidas com as suas impressões avaliadas — estatísticas, não um modelo de IA, indicando em quantas impressões cada resultado se baseia  
✓ Assistentes: assistente de biblioteca (varinha mágica, primeira etiqueta das coleções) e assistente de fabrico, com respostas legíveis; a IA, se estiver configurada, só escolhe uma consulta de uma lista fechada, em leitura apenas e sem acesso direto aos seus dados  
✓ API pública (Definições › API pública): tokens de âmbito limitado, rotas /api/v1 (ficheiros, impressoras, materiais, histórico, projetos, tarefas; escrita de bobinas e projetos), documentação OpenAPI, SDK Python e JavaScript; webhooks de saída assinados (HMAC-SHA256) com novas tentativas e registo  
✓ Equipas e segurança: funções (administrador, gestor, operador, utilizador simples, convidado), permissões por pasta, projeto e impressora, espaços de trabalho partilhados, sessões ativas revogáveis, registo de ligações, registo de auditoria paginado e exportável em CSV  
✓ Plugins: novo menu Plugins (catálogo, plugins instalados), plugins que mostram a sua própria página (exemplo: visualizador de G-code 3D), distintivos «Oficial» / «Comunitário», atualização com permissões a reaceitar, catálogo https com impressão digital SHA-256 obrigatória, execução em processo separado; o separador Comunidade da oficina está esbatido («Brevemente»)  
✓ Plugin Administração: uma página única (contas de convidado e funções, equipas, sessões, registo de auditoria) e supervisão de instâncias — a instância principal lista as instâncias Stellio emparelhadas; uma instância só é supervisionada após aceitação do seu proprietário (contas, funções e permissões geridas a partir da principal, conteúdo local mantido, saída possível a qualquer momento); uma instância não ligada mantém o controlo total  
✓ Central de notificações: «Ver tudo» abre uma página com todas as notificações, filtráveis por categoria (filamento baixo, filamento a reabastecer, peças, impressões, manutenção) e com pesquisa  
✓ Página Coleções na Biblioteca: cada coleção é uma seção expansível (nome, número de arquivos) que mostra seus arquivos, com criação rápida  
✓ Custo de uma impressão: se houver um G-code anexado ao arquivo, o peso e a duração reais dele são usados no cálculo, em vez de uma estimativa  
✓ Bibliotecas grandes: testadas com 50 000 modelos (etiquetas perdidas a partir de 32 000 ficheiros, grelha inteira desenhada, análises lentas: corrigido); seletor de modelo com origem, pesquisa, filtro por formato (STL, 3MF…), miniaturas e paginação; BigPrint, agora em Ferramentas, pagina o seu seletor  
✓ Ficheiros STL gigantes: leitura em fluxo (binário e texto), miniatura e visualizador numa versão simplificada, limiar de carregamento adaptado à memória livre (256 MB a 1 GB) e ação «Criar uma versão leve» (cópia simplificada junto ao original, que nunca é alterado), também proposta quando uma reparação é recusada por tamanho  
✓ Robustez: miniaturas de ficheiros grandes desenhadas num processo separado (uma falha ou saturação de memória já não derruba a aplicação, o ficheiro é posto de lado), proteção no arranque e crash_trace.log; as cópias temporárias de ficheiros do NAS (SMB) já não enchem o disco; miniatura predefinida mais limpa  
✓ Base de dados: migrações versionadas com retoma automática, gestor único de tarefas em segundo plano (progresso, cancelamento), testes de atualização de uma base antiga  
✓ Interface: janela dos alertas do widget Saúde, distintivo «Atualização disponível», «Tentar novamente» com indicador na aplicação do telemóvel, idioma na sua própria secção das definições, barra lateral que já não fica meio aberta; as impressoras de resina e USB já não são marcadas como beta; textos novos traduzidos nos 8 idiomas  
✓ Definições: cada menu abre numa janela com todas as suas definições, sem animação; Administração: pedido de supervisão como janela Aceitar / Recusar na instância visada, distintivo de estado que se atualiza sozinho, adicionar contas às equipas  
✓ MQTT / Home Assistant: a disponibilidade é republicada a cada ciclo e no arranque do Home Assistant (entidades que ficavam «indisponíveis»)  
✓ Correções: favoritos do MakerWorld que não eram importados (erro «'<' not supported between int and NoneType»), possível erro 500 no primeiro arranque na lista de orçamentos  
</details>

<details>
<summary><b>🇮🇹 Italiano</b></summary>

✓ Plugin integrati: BigPrint, resina, stampanti USB, timelapse, strumenti per file, studio del piatto, condivisione e sincronizzazione, Spoolman, IA (Ollama, OpenAI, Anthropic, Gemini + assistente IA), Stellio Pro (clienti, preventivi, fatture, ordini, contabilità, tariffa energetica, pianificazione, fabbisogno di materiale, magazzino pezzi), notifiche push, webhook, riepilogo periodico, MQTT / Home Assistant e Obico escono dal nucleo: sono forniti con Stellio e si caricano solo se attivati (Plugin › Plugin integrati, dopo il riavvio)  
✓ Aggiornamento dalla 1.1.6 senza perdere nulla: al primo avvio i plugin integrati che usavi vengono riattivati automaticamente, con impostazioni, database e file invariati (mai contro una tua scelta successiva)  
✓ Edizione server (Linux): notifiche push esterne, riepilogo periodico, MQTT / Home Assistant, webhook, API pubblica, sincronizzazione tra istanze e accesso mobile; nascosti e disattivati su Windows  
✓ Laboratorio avanzato: i nuovi strumenti sono collocati nella barra laterale, ciascuno nella sua categoria — Libreria (Organizzazione, Diff 3D, Simili, Licenze, Scheda pezzo), Stampa (Compatibilità, Verifica di stampa, Archivi G-code), Materiali (Fabbisogno di materiale), Strumenti (Piatto, Sincronizzazione, Assistente di fabbricazione) e la nuova categoria Amministrazione (Attività, Database, Registro di controllo, Team, Sessioni); ogni voce ha il suo interruttore in Impostazioni › Elementi di navigazione  
✓ Organizzazione automatica della libreria: regole per estensione, nome, licenza, materiale, dimensione, autore, categoria o età del file, create ed eliminate da un modulo, con anteprima leggibile, conferma e annullamento  
✓ Diff 3D visivo tra due versioni di un modello (nuvola di punti colorata: rimosso, aggiunto, invariato; STEP incluso) e ricerca di pezzi simili per forma, con miniature  
✓ Licenze: suggerimenti di licenze comuni, badge «uso commerciale consentito / vietato / da verificare», data di scadenza per file e notifiche quando una licenza sta per scadere o è scaduta  
✓ Scheda pezzo: tutto ciò che Stellio sa di un modello in una pagina (origine e licenza, versioni, stampe, migliore combinazione, G-code archiviati, foto)  
✓ Stampa: compatibilità modello ↔ stampanti (volume, ugello, materiale), verifica prima della stampa (sporgenze, supporti stimati, base, mesh, adattamento al piatto, orientamento consigliato con copia orientata) e archivio del G-code di ogni stampa (compresso, impronta SHA-256); nuova pagina Timelapse nel menu Stampa  
✓ Piatto multimodello: disposizione sulla geometria reale (nesting, rotazione libera), più piatti, editor 2D e vista 3D, più copie di un pezzo, elenco dei modelli con rimozione, pulsante «Organizzazione automatica», dimensioni prese da una stampante, esportazione 3MF con indicatore di avanzamento  
✓ Materiali e produzione: fabbisogno di materiale (coda di stampa e progetti contro la scorta: mancanza in grammi, bobine da ordinare); Pianificazione con costo totale per ordine, resa e scarti, ritardi, redditività per stampante (margine, margine orario) e tempo di lavoro umano × tariffa oraria  
✓ Tracciabilità: «Collega a una versione» su ogni stampa, «Associa a un modello» su un G-code, profili di slicer riconosciuti dall'impronta delle loro impostazioni, cronologia arricchita (temperature e slicer letti dal G-code)  
✓ Statistiche › Stellio Intelligence: impostazioni consigliate (miglior profilo per materiale / stampante) e cause probabili di errore, apprese dalle tue stampe valutate — statistiche, non un modello di IA, con il numero di stampe su cui poggia ogni risultato  
✓ Assistenti: assistente della libreria (bacchetta magica, primo chip delle raccolte) e assistente di fabbricazione, con risposte leggibili; l'IA, se configurata, sceglie solo una richiesta da un elenco chiuso, in sola lettura e senza accesso diretto ai tuoi dati  
✓ API pubblica (Impostazioni › API pubblica): token con ambito limitato, rotte /api/v1 (file, stampanti, materiali, cronologia, progetti, attività; scrittura di bobine e progetti), documentazione OpenAPI, SDK Python e JavaScript; webhook in uscita firmati (HMAC-SHA256) con nuovi tentativi e registro  
✓ Team e sicurezza: ruoli (amministratore, responsabile, operatore, utente semplice, ospite), permessi per cartella, progetto e stampante, spazi di lavoro condivisi, sessioni attive revocabili, registro degli accessi, registro di controllo paginato ed esportabile in CSV  
✓ Plugin: nuovo menu Plugin (catalogo, plugin installati), plugin che mostrano una propria pagina (esempio: visualizzatore G-code 3D), badge «Ufficiale» / «Community», aggiornamento con permessi da riaccettare, catalogo https con impronta SHA-256 obbligatoria, esecuzione in processo separato; la scheda Community del laboratorio è disattivata («Prossimamente»)  
✓ Plugin Amministrazione: una pagina unica (account ospite e ruoli, team, sessioni, registro di controllo) e supervisione delle istanze — l'istanza principale elenca le istanze Stellio abbinate; un'istanza è supervisionata solo dopo l'accettazione del proprietario (account, ruoli e permessi gestiti dalla principale, contenuto locale conservato, uscita possibile in qualsiasi momento); un'istanza non connessa mantiene il controllo totale  
✓ Centro notifiche: «Vedi tutto» apre una pagina con tutte le notifiche, filtrabili per categoria (filamento in esaurimento, filamento da riordinare, parti, stampe, manutenzione) e con ricerca  
✓ Pagina Collezioni nella Libreria: ogni collezione è una sezione espandibile (nome, numero di file) che mostra i suoi file, con creazione rapida  
✓ Costo di una stampa: se al file è allegato un G-code, il suo peso e la sua durata reali vengono usati nel calcolo al posto di una stima  
✓ Grandi librerie: provate con 50.000 modelli (etichette perse oltre 32.000 file, griglia disegnata per intero, analisi lente: corretti); selettore di modello con origine, ricerca, filtro per formato (STL, 3MF…), miniature e paginazione; BigPrint, ora in Strumenti, impagina il suo selettore  
✓ File STL giganti: lettura in streaming (binario e testo), miniatura e visualizzatore su una versione semplificata, soglia di caricamento adattata alla memoria libera (da 256 MB a 1 GB) e azione «Crea una versione leggera» (copia semplificata accanto all'originale, mai modificato), proposta anche quando una riparazione viene rifiutata per dimensione  
✓ Robustezza: miniature dei file grandi disegnate in un processo separato (un arresto anomalo o una saturazione di memoria non fa più cadere l'applicazione, il file viene messo da parte), protezione all'avvio e crash_trace.log; le copie temporanee dei file del NAS (SMB) non riempiono più il disco; miniatura predefinita più sobria  
✓ Database: migrazioni versionate con ripresa automatica, gestore unico delle attività in background (avanzamento, annullamento), test di aggiornamento da un vecchio database  
✓ Interfaccia: popup degli avvisi del widget Salute, badge «Aggiornamento disponibile», «Riprova» con indicatore nell'app del telefono, lingua in una sezione propria delle impostazioni, barra laterale che non resta più semiaperta; le stampanti a resina e USB non sono più etichettate beta; nuovi testi tradotti nelle 8 lingue  
✓ Impostazioni: ogni menu si apre in una finestra con tutte le sue impostazioni, senza animazione; Amministrazione: richiesta di supervisione come finestra Accetta / Rifiuta sull'istanza di destinazione, badge di stato che si aggiorna da solo, aggiunta degli account ai team  
✓ MQTT / Home Assistant: la disponibilità viene ripubblicata a ogni ciclo e all'avvio di Home Assistant (entità rimaste «non disponibili»)  
✓ Correzioni: preferiti di MakerWorld non importati (errore «'<' not supported between int and NoneType»), possibile errore 500 al primo avvio nell'elenco dei preventivi  
</details>

<details>
<summary><b>🇨🇳 中文</b></summary>

✓ 内置插件：BigPrint、树脂、USB 打印机、延时摄影、文件工具、打印板工作室、共享与同步、Spoolman、AI（Ollama、OpenAI、Anthropic、Gemini + AI 助手）、Stellio Pro（客户、报价、发票、订单、会计、电价、排产、材料需求、零件库存）、推送通知、Webhook、定期摘要、MQTT / Home Assistant 和 Obico 从核心中分离：它们随 Stellio 一起提供，仅在启用后加载（插件 › 内置插件，重启后生效）  
✓ 从 1.1.6 升级不丢失任何内容：首次启动时，您使用过的内置插件会自动重新启用，设置、数据库和文件保持不变（绝不会违背您之后的选择）  
✓ 服务器版（Linux）：外部推送通知、定期摘要、MQTT / Home Assistant、Webhook、公共 API、实例间同步和移动访问；在 Windows 上隐藏并停用  
✓ 高级工坊：新工具按类别放入侧边栏 — 库（整理、3D 对比、相似件、许可证、零件档案）、打印（兼容性、打印检查、G-code 归档）、材料（材料需求）、工具（打印板、同步、制造助手），以及新的「管理」类别（任务、数据库、审计日志、团队、会话）；每个条目在 设置 › 导航项 中都有独立开关  
✓ 库自动整理：按扩展名、名称、许可证、材料、大小、作者、类别或文件年龄设置规则，通过表单创建和删除，带可读预览、确认和撤销  
✓ 模型两个版本之间的可视化 3D 对比（彩色点云：已删除、已添加、未变化；支持 STEP），以及按形状查找相似零件（带缩略图）  
✓ 许可证：常用许可证建议、「允许 / 禁止 / 待确认商业使用」徽章、每个文件的到期日期，以及许可证即将到期或已到期时的通知  
✓ 零件档案：Stellio 掌握的关于某个模型的全部信息集中在一页（来源与许可证、版本、打印记录、最佳组合、已归档的 G-code、照片）  
✓ 打印：模型 ↔ 打印机兼容性（体积、喷嘴、材料）、打印前检查（悬垂、预估支撑、底面、网格、是否放得进打印板、建议朝向及朝向后的副本），以及每次打印 G-code 的归档（压缩，SHA-256 指纹）；打印菜单新增「延时摄影」页面  
✓ 多模型打印板：按真实几何形状排布（嵌套、自由旋转）、多块打印板、2D 编辑器和 3D 视图、同一零件多个副本、带移除按钮的模型列表、「自动排布」按钮、可从打印机获取尺寸、带进度指示的 3MF 导出  
✓ 材料与生产：材料需求（打印队列和项目对比库存：缺少的克数、需订购的料盘）；排产页面提供每个订单的总成本、良率与浪费、延误、按打印机统计的盈利能力（利润、每小时利润）以及人工时间 × 小时费率  
✓ 可追溯性：每次打印可「关联到版本」，G-code 可「关联到模型」，切片配置按设置指纹识别，历史记录更丰富（从 G-code 读取温度和切片软件）  
✓ 统计 › Stellio Intelligence：根据您已评分的打印学习，给出推荐设置（每种材料 / 打印机的最佳配置）和可能的失败原因 — 这是统计而非 AI 模型，并显示每个结果基于多少次打印  
✓ 助手：库助手（魔法棒，合集的第一个标签）和制造助手，回答更易读；AI（如已配置）只能从封闭列表中选择一个查询，只读，且不会直接访问您的数据  
✓ 公共 API（设置 › 公共 API）：限定范围的令牌、/api/v1 路由（文件、打印机、材料、历史、项目、任务；可写入料盘和项目）、OpenAPI 文档、Python 和 JavaScript SDK；带重试和日志的签名出站 Webhook（HMAC-SHA256）  
✓ 团队与安全：角色（管理员、经理、操作员、普通用户、访客）、按文件夹、项目和打印机的权限、共享工作区、可撤销的活动会话、登录日志、可分页并导出为 CSV 的审计日志  
✓ 插件：新增「插件」菜单（目录、已安装插件），插件可显示自己的页面（示例：3D G-code 查看器），「官方」/「社区」徽章，更新时需重新接受权限，必须带 SHA-256 指纹的 https 目录，独立进程运行；工坊中的「社区」标签已置灰（「即将推出」）  
✓ 管理插件：单一页面（访客账户与角色、团队、会话、审计日志）和实例监督——主实例列出已配对的 Stellio 实例；只有所有者接受后实例才会被监督（账户、角色和权限由主实例管理，保留本地内容，可随时退出）；未连接的实例保持完全控制  
✓ 通知中心：“查看全部”打开包含所有通知的页面，可按类别（耗材不足、耗材需补货、配件、打印、维护）筛选并搜索  
✓ 库中新增“收藏集”页面：每个收藏集是一个可展开的分区（名称、文件数），展开后显示其文件，并可快速新建  
✓ 打印成本：文件附有 G-code 时，使用其真实重量和时长计算，而不是估算值  
✓ 大型库：已在 50,000 个模型下测试（超过 32,000 个文件时标签丢失、整个网格一次绘制、分析过慢：均已修复）；模型选择器支持来源、搜索、格式筛选（STL、3MF…）、缩略图和分页；BigPrint 移至「工具」，其选择器已分页  
✓ 超大 STL 文件：流式读取（二进制和文本）、缩略图和查看器使用简化版本、加载阈值随可用内存调整（256 MB 至 1 GB），以及「创建轻量版本」操作（在原文件旁生成简化副本，原文件绝不修改），当修复因文件过大被拒绝时也会提示  
✓ 稳定性：大文件的缩略图在独立进程中绘制（崩溃或内存耗尽不再拖垮应用，该文件会被搁置）、启动保护和 crash_trace.log；NAS（SMB）文件的临时副本不再占满磁盘；默认缩略图更简洁  
✓ 数据库：带自动续作的版本化迁移、统一的后台任务管理器（进度、取消）、旧数据库升级测试  
✓ 界面：健康小组件警报弹窗、「有可用更新」徽章、手机应用中带指示的「重试」、语言拥有独立的设置分区、侧边栏不再停留在半开状态；树脂和 USB 打印机不再标记为测试版；新文本已翻译为 8 种语言  
✓ 设置：每个菜单在弹窗中显示全部设置，无动画；管理：目标实例上以“接受 / 拒绝”弹窗显示监管请求，状态徽章自动更新，可将账户添加到团队  
✓ MQTT / Home Assistant：每个周期以及 Home Assistant 启动时重新发布可用性（实体一直显示“不可用”）  
✓ 修复：MakerWorld 收藏未导入（错误「'<' not supported between int and NoneType」）、首次启动时报价列表可能出现 500 错误  
</details>

<details>
<summary><b>🇯🇵 日本語</b></summary>

✓ 内蔵プラグイン：BigPrint、レジン、USB プリンター、タイムラプス、ファイルツール、プレートスタジオ、共有と同期、Spoolman、AI（Ollama、OpenAI、Anthropic、Gemini + AI アシスタント）、Stellio Pro（顧客、見積、請求書、注文、会計、電力料金、計画、材料所要量、部品在庫）、プッシュ通知、Webhook、定期サマリー、MQTT / Home Assistant、Obico がコアから分離されました。Stellio に同梱され、有効にしたときだけ読み込まれます（プラグイン › 内蔵プラグイン、再起動後）  
✓ 1.1.6 からの更新で何も失いません：初回起動時に、使っていた内蔵プラグインが自動的に再び有効になり、設定・データベース・ファイルはそのままです（あとからのあなたの選択には決して逆らいません）  
✓ サーバー版（Linux）：外部プッシュ通知、定期サマリー、MQTT / Home Assistant、Webhook、公開 API、インスタンス間の同期、モバイルアクセス。Windows では非表示かつ無効です  
✓ 高度なワークショップ：新しいツールをサイドバーのカテゴリごとに配置 — ライブラリ（整理、3D 差分、類似、ライセンス、パーツシート）、印刷（互換性、印刷チェック、G-code アーカイブ）、材料（材料所要量）、ツール（プレート、同期、製造アシスタント）、そして新カテゴリ「管理」（タスク、データベース、監査ログ、チーム、セッション）。各項目は 設定 › ナビゲーション項目 に個別のスイッチがあります  
✓ ライブラリの自動整理：拡張子、名前、ライセンス、材料、サイズ、作者、カテゴリ、ファイルの経過時間によるルールを、フォームで作成・削除でき、読みやすいプレビュー、確認、元に戻す機能付き  
✓ モデルの 2 つのバージョン間のビジュアル 3D 差分（色付き点群：削除、追加、変更なし。STEP 対応）と、形状による類似パーツ検索（サムネイル付き）  
✓ ライセンス：一般的なライセンスの候補、「商用利用 可 / 不可 / 要確認」バッジ、ファイルごとの有効期限、ライセンスがまもなく期限切れ・期限切れになったときの通知  
✓ パーツシート：モデルについて Stellio が把握している情報を 1 ページに集約（出典とライセンス、バージョン、印刷、最良の組み合わせ、アーカイブ済み G-code、写真）  
✓ 印刷：モデル ↔ プリンターの互換性（体積、ノズル、材料）、印刷前チェック（オーバーハング、推定サポート、ベース、メッシュ、プレートに収まるか、推奨の向きと向き調整済みコピー）、各印刷の G-code のアーカイブ（圧縮、SHA-256 フィンガープリント）。印刷メニューに新しい「タイムラプス」ページ  
✓ マルチモデルプレート：実際の形状に基づく配置（ネスティング、自由回転）、複数プレート、2D エディターと 3D ビュー、同じパーツの複数コピー、削除ボタン付きモデル一覧、「自動配置」ボタン、プリンターからのサイズ取得、進行表示付きの 3MF エクスポート  
✓ 材料と生産：材料所要量（印刷キューとプロジェクトを在庫と照合：不足グラム数、発注すべきスプール）。計画ページに注文ごとの総コスト、歩留まりと廃棄、遅延、プリンターごとの収益性（利益、時間あたり利益）、人件費時間 × 時間単価  
✓ トレーサビリティ：各印刷を「バージョンに関連付け」、G-code を「モデルに関連付け」、スライサープロファイルを設定のフィンガープリントで識別、より豊富な履歴（G-code から温度とスライサーを読み取り）  
✓ 統計 › Stellio Intelligence：評価済みの印刷から学習した推奨設定（材料 / プリンターごとの最良プロファイル）と失敗の推定原因。AI モデルではなく統計で、各結果が何回の印刷に基づくかを表示します  
✓ アシスタント：ライブラリアシスタント（魔法の杖、コレクションの最初のチップ）と製造アシスタントで、回答が読みやすくなりました。AI は、設定されている場合、閉じたリストからクエリを 1 つ選ぶだけで、読み取り専用、あなたのデータへ直接アクセスしません  
✓ 公開 API（設定 › 公開 API）：スコープ付きトークン、/api/v1 ルート（ファイル、プリンター、材料、履歴、プロジェクト、タスク。スプールとプロジェクトの書き込み）、OpenAPI ドキュメント、Python と JavaScript の SDK。再試行とログ付きの署名付き送信 Webhook（HMAC-SHA256）  
✓ チームとセキュリティ：ロール（管理者、マネージャー、オペレーター、一般ユーザー、ゲスト）、フォルダー・プロジェクト・プリンター単位の権限、共有ワークスペース、取り消せるアクティブセッション、ログインログ、ページ分割され CSV で書き出せる監査ログ  
✓ プラグイン：新しい「プラグイン」メニュー（カタログ、インストール済み）、独自のページを表示できるプラグイン（例：3D G-code ビューア）、「公式」/「コミュニティ」バッジ、権限の再承認が必要な更新、SHA-256 フィンガープリント必須の https カタログ、別プロセスでの実行。ワークショップの「コミュニティ」タブはグレー表示（「近日公開」）  
✓ 管理プラグイン：1 つのページ（ゲストアカウントとロール、チーム、セッション、監査ログ）とインスタンスの監督 — プライマリインスタンスがペアリング済みの Stellio インスタンスを一覧表示。インスタンスはオーナーが承諾して初めて監督対象になります（アカウント・ロール・権限はプライマリから管理、ローカルコンテンツは保持、いつでも終了可能）。未接続のインスタンスは完全な制御を保ちます  
✓ 通知センター：「すべて表示」で全通知のページを開き、カテゴリ（フィラメント残量少、再注文、部品、プリント、メンテナンス）で絞り込み・検索できます  
✓ ライブラリに「コレクション」ページを追加：各コレクションは展開可能なセクション（名前・ファイル数）で、ファイルを表示し、すばやく作成できます  
✓ プリントコスト：ファイルにG-codeが添付されている場合、推定値ではなくその実際の重量と時間で計算します  
✓ 大規模ライブラリ：50,000 モデルでテスト済み（32,000 ファイルを超えるとタグが失われる、グリッド全体を一度に描画、分析が遅い：いずれも修正）。ソース、検索、形式フィルター（STL、3MF…）、サムネイル、ページ分割付きのモデル選択。BigPrint は「ツール」に移動し、選択画面がページ分割されました  
✓ 巨大な STL ファイル：ストリーミング読み込み（バイナリとテキスト）、簡略化版でのサムネイルとビューア、空きメモリに応じた読み込みしきい値（256 MB〜1 GB）、「軽量版を作成」アクション（元のファイルは変更せず、隣に簡略化コピーを作成）。サイズが理由で修復が拒否されたときにも提案されます  
✓ 安定性：大きなファイルのサムネイルを別プロセスで描画（クラッシュやメモリ逼迫でもアプリは落ちず、そのファイルは除外）、起動時の保護と crash_trace.log。NAS（SMB）のファイルの一時コピーがディスクを埋めなくなりました。既定のサムネイルをすっきりさせました  
✓ データベース：自動再開付きのバージョン管理されたマイグレーション、バックグラウンドタスクの一元管理（進捗、キャンセル）、古いデータベースからの更新テスト  
✓ インターフェース：ヘルスウィジェットの警告ポップアップ、「更新があります」バッジ、スマホアプリの「再試行」インジケーター、言語を独立した設定セクションに、サイドバーが半開きのままにならない。レジンと USB プリンターのベータ表記を撤廃。新しいテキストを 8 言語に翻訳  
✓ 設定：各メニューはすべての設定を表示するポップアップで開き、アニメーションはありません。管理：対象インスタンスで「承認 / 拒否」ポップアップとして監視リクエストを表示、状態バッジは自動更新、アカウントをチームに追加可能  
✓ MQTT / Home Assistant：可用性を毎サイクルと Home Assistant 起動時に再公開（「利用不可」のままだったエンティティ）  
✓ 修正：MakerWorld のお気に入りがインポートされない問題（エラー「'<' not supported between int and NoneType」）、初回起動時に見積一覧で 500 エラーが出る可能性  
</details>

Full changelog / Historique complet : https://github.com/stellio-app/stellio/blob/main/changelog.json
