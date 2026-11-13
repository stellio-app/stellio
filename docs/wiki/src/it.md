@@@ Home | Home
# Wiki di Stellio
{{img:dashboard}}


**Stellio** è il gestore di file 3D per maker e proprietari di stampanti 3D. Centralizza la tua libreria (STL, 3MF, OBJ, STEP, PLY, AMF), automatizza le attività ripetitive e si integra nel tuo flusso di stampa.

> 🔒 **Filosofia**: i tuoi dati restano con te. Tutto funziona in locale; per impostazione predefinita nulla lascia il tuo computer.

## Da dove iniziare?

| Voglio… | Pagina |
|---|---|
| Installare Stellio | [Installazione](it-Installation) |
| Muovere i primi passi | [Primi passi](it-Getting-Started) |
| Gestire i miei file 3D | [Libreria](it-Library) |
| Collegare le mie stampanti | [Stampanti](it-Printers) |
| Seguire le mie bobine | [Filamento](it-Filament) |
| Scaricare modelli | [Download](it-Downloads) |
| Usare l'IA e S.O.S Print | [Intelligenza artificiale](it-AI) |
| Calcolare costi, preventivi, fatture | [Costi e gestione](it-Costs-and-Management) |
| Accedere dal telefono | [Accesso remoto e mobile](it-Remote-Access) |
| Installare su Raspberry Pi / Proxmox | [Edizione server](it-Server-Edition) |
| Configurare, fare backup, capire i miei dati | [Impostazioni e dati](it-Settings-and-Data) |
| Risolvere un problema | [Risoluzione dei problemi](it-Troubleshooting) |
| Contribuire al progetto | [Contribuire](it-Contributing) |

## Link utili

- 🌐 Sito: [stellio-app.com](https://stellio-app.com) — ▶ [demo online (sola lettura)](https://demo.stellio-app.com)
- 📦 [Download (Releases)](https://github.com/stellio-app/stellio/releases)
- 🐛 [Segnalare un bug](https://github.com/stellio-app/stellio/issues) · 💡 [Proporre un'idea](https://github.com/stellio-app/stellio/discussions) · 💬 [Discord](https://discord.gg/ySxpHvS6bd)
- 📜 Licenza **AGPL v3**

@@@ Installation | Installazione
# Installazione

| Piattaforma | File / metodo | Modalità |
|---|---|---|
| 🪟 Windows | `Stellio-Setup-<version>.exe` | App desktop |
| 🪟 Windows portatile | `Stellio-v<version>-portable-win64.zip` | App desktop, senza installazione |
| 🍎 macOS | `.dmg` (Apple Silicon `arm64` o Intel `x86_64`) | App desktop |
| 🐧 Linux | `Stellio-v<version>-x86_64.AppImage` | App desktop |
| 🍓 Raspberry Pi / Linux | `install-pi.sh` | Server (browser) |
| 🖥️ Proxmox VE | `stellio-lxc.sh` | Container LXC con un solo comando |
| 📲 Android | APK companion | Vedi [Accesso remoto e mobile](it-Remote-Access) |

Tutti i file sono nella pagina [Releases](https://github.com/stellio-app/stellio/releases), ognuno con un checksum `.sha256`.

## Windows

1. Scarica il programma di installazione dalle Releases.
2. Avvia `Stellio-Setup-<version>.exe`.
3. Fatto.

**Versione portatile**: decomprimi dove vuoi (disco, chiavetta USB) e avvia `Stellio.exe`. I tuoi dati restano nella cartella `data` accanto all'eseguibile (conserva il file `portable.flag`).

> ⚠️ Il programma di installazione **non è firmato**: Windows SmartScreen può mostrare un avviso. Controlla il `.sha256` se vuoi; l'aggiornamento integrato lo verifica prima di installare.

## macOS

Apri il `.dmg` e trascina Stellio in Applicazioni. Scegli il file adatto al tuo Mac: `arm64` (M1, M2, M3…) o `x86_64` (Intel). Le build non sono notarizzate: al primo avvio, clic destro → **Apri**.

> Se la schermata resta bianca: la porta 5000 potrebbe essere occupata dal «Ricevitore AirPlay» di macOS. Stellio sceglie allora automaticamente un'altra porta libera. Vedi [Risoluzione dei problemi](it-Troubleshooting).

## Linux (AppImage)

```bash
chmod +x Stellio-v*-x86_64.AppImage
./Stellio-v*-x86_64.AppImage
```
L'AppImage include le sue informazioni di aggiornamento (`.zsync`).

## Raspberry Pi / server Linux

Modalità **server senza interfaccia**: Stellio gira in background e si usa da un browser. Dettagli in [Edizione server](it-Server-Edition).

```bash
curl -O https://raw.githubusercontent.com/stellio-app/stellio/main/install-pi.sh
chmod +x install-pi.sh
./install-pi.sh
```

## Proxmox VE

Nella **Shell dell'host Proxmox**:
```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/stellio-app/stellio/main/stellio-lxc.sh)"
```
Dettagli in [Edizione server](it-Server-Edition).

## Aggiornamenti

- **Desktop**: Stellio rileva le nuove versioni su GitHub e applica una patch `.zip` (stesso meccanismo su Windows, macOS e Linux). Il widget «Aggiornamento» della dashboard apre la finestra di aggiornamento.
- **Server**: lo stesso aggiornamento automatico, oppure `update-stellio` (container LXC) / `./install-pi.sh` (Raspberry Pi).
- Al primo avvio di ogni versione, i moduli mancanti (preventivi PDF, importazione di fogli di calcolo, notifiche…) vengono scaricati automaticamente.

@@@ Getting-Started | Primi passi
# Primi passi
{{img:library}}


## 1. Primo avvio
Stellio mostra un **tour guidato** e una lista «Primi passi». Puoi riavviare il tour in qualsiasi momento dalle Impostazioni.

## 2. Creare il tuo account
Gli account sono **locali**: password + codice di recupero + domanda segreta. Il ripristino della password è al 100 % locale, senza e-mail né internet.

## 3. Aggiungere le tue fonti
Una **fonte** è una cartella o una condivisione che contiene i tuoi modelli:
- cartella locale, file singolo, condivisione **SMB** o **NFS**;
- le cartelle 3D rilevate sul tuo computer ti vengono **suggerite** e si aggiungono con un clic;
- per ogni fonte scegli i tipi di file visualizzati.

Stellio analizza quindi i tuoi file e genera le miniature 3D in background.

## 4. Aggiungere una stampante (facoltativo)
Apri la pagina **Stampanti**: il rilevamento di rete propone le macchine trovate. Vedi [Stampanti](it-Printers).

## 5. Scegliere il tuo slicer
Stellio rileva automaticamente gli slicer installati (OrcaSlicer, Bambu Studio, PrusaSlicer, Cura…). Il pulsante di invio apre il file direttamente nello slicer.

## Dashboard
La home riunisce stampe in corso, scorte basse, stampe recenti e file recenti. I **widget** (una ventina) si riordinano con il trascinamento e si possono nascondere: stampe in corso, scorte basse, ultimi S.O.S Print, suggerimenti, istanze di Stellio, progetti completati, galleria, preventivi…

## Strumenti di tutti i giorni
- **Palette dei comandi** `Ctrl+K`: navigare, eseguire un'azione, trovare un file, un'etichetta, una bobina o un profilo.
- **Centro notifiche** (campanella): fine stampa, errore, manutenzione, scorte basse, essiccazione delle bobine.
- **Widget mobile** con l'avanzamento della stampa in corso, visibile in tutte le pagine.
- **Scorciatoie da tastiera**: vedi [Impostazioni e dati](it-Settings-and-Data).

@@@ Library | Libreria
# Libreria
{{img:library}}


## Fonti e miniature
- Più fonti: cartelle locali, file, condivisioni SMB/NFS.
- **Miniature 3D automatiche** (PyRender, o un renderer CPU di riserva) con anteprima ingrandita al passaggio del mouse.
- La generazione **si mette in pausa appena usi l'app** e riprende dopo.
- Impostazione **Prestazioni delle miniature**: Automatico / Eco / Normale / Veloce.
- Formati: STL, 3MF (anche multipiatto e PrusaSlicer), OBJ, STEP/STP, PLY, AMF (convertiti in STL per gli slicer che non li leggono) e archivi (ZIP, RAR, 7z, TAR) esplorabili direttamente.

## Organizzare
- **Etichette** colorate, con etichettatura automatica tramite IA; etichetta più file con un clic.
- **Preferiti**, filtri avanzati (tipo, dimensione, peso, stato di stampa), **filtri salvati**.
- Filtri di stato: «Inviato allo slicer», «Già stampato», «Già riuscito», «Già fallito».
- **Filtro «Scorte di filamento»**: tiene solo i file stampabili con le bobine che possiedi.
- Ordinamento, ricerca e filtri vengono **memorizzati** alla riapertura dell'app.
- Coda **«Da stampare presto»**, riordinabile e inviabile allo slicer.
- **Rinomina di massa** (trova/sostituisci, prefisso, suffisso, numerazione) con anteprima.
- **Annulla eliminazioni** (`Ctrl+Z`) grazie a un cestino temporaneo di 5 minuti; vale anche per etichette, progetti e fonti.
- Selezione rapida: `Maiusc+clic` per un intervallo, frecce + `Invio`.
- **Rilevamento dei duplicati** (esatti e di geometria simile).
- **Origine del modello**: link di origine, autore, licenza, note, data di download.
- **Trascinamento** dei file 3D da Esplora risorse, anche tramite browser.

## Ricerca
- Ricerca classica e **ricerca semantica con IA** («cerco un supporto per…»), con le ricerche recenti memorizzate.
- **Raccolte intelligenti**.

## Progetti / assiemi
Raggruppa più file per un singolo oggetto.
- 3MF **multipiatto**: aggiungendolo a un progetto viene diviso in un 3MF per piatto (6 piatti = 6 file), archiviati in una cartella nascosta.
- Azione **«Dividi i piatti»** nel menu ⋯ di un file.
- Scheda del progetto: clic sulla miniatura = visualizzatore 3D; il filtro «Tutti / In corso / Completati» viene memorizzato; **Costo del progetto** con un pulsante.

{{img:projects}}

## Visualizzatore 3D e strumenti
- **Visualizzatore 3D** (Three.js, funziona offline), navigazione tra i piatti.
- **Disposizione automatica** sul piatto (rectpack, o sagoma reale con shapely).
- **Riparazione della mesh** (trimesh + pymeshfix) con confronto prima/dopo.
- **Convertitore** STL ↔ 3MF ↔ OBJ.
- **Analisi di stampabilità** (sporgenze) e **orientamenti suggeriti**.
- **Controllo di integrità** (file danneggiati o mancanti).
- **Statistiche** dettagliate (formati, piattaforme, affidabilità dei profili).

{{img:viewer}}

## Cronologia e foto
- **Cronologia** paginata per settimana, con valutazione riuscito/fallito (che alimenta l'IA), pulsanti **Vedi file** e **Ristampa**, filtri per piattaforma, risultato e date.
- **Galleria di foto** di stampa. La foto di fine stampa si imposta poi come *Riuscito* o *Fallito* con un clic.
- **I miei G-code**: G-code collegati a un file, download e pulsante **Apri nello slicer**.
- **Backup** della libreria: vedi [Impostazioni e dati](it-Settings-and-Data).

@@@ Printers | Stampanti
# Stampanti
{{img:printers}}


## Marchi supportati

| Marchio | Modelli | Connessione |
|---|---|---|
| **Bambu Lab** | X1/X1C/X1E, X2D, P1P/P1S, P2S, A1/A1 mini, H2D/H2S/H2C | MQTT (LAN + cloud): monitoraggio, AMS, camera, rilevamento SSDP |
| **Prusa** | MK4, MK3.9, MK3.5, MINI+, XL, CORE One | PrusaLink (HTTP) |
| **Creality** | Serie K1/K2, Ender-3 V3, Hi | WebSocket: monitoraggio, CFS, rilevamento UDP |
| **Elegoo** | Centauri Carbon 1 e 2, serie resina Saturn/Mars | SDCP (WebSocket) |
| **FlashForge** | Adventurer 5M/5M Pro, AD5X | API proprietaria |
| **Klipper / Moonraker** | Qualsiasi macchina Klipper (Voron…) | HTTP: monitoraggio, invio, camera, ore esatte |
| **OctoPrint** | Qualsiasi stampante controllata da OctoPrint | HTTP |

Gli altri modelli che parlano lo stesso protocollo di solito funzionano. Dicci su GitHub se il tuo funziona.

## Aggiungere una stampante
- **Rilevamento automatico** della rete locale (SSDP, broadcast UDP, sonde mirate): le stampanti trovate si aggiungono con un clic.
- Altrimenti, inserimento manuale (tipo, modello, indirizzo, chiave di accesso).
- Indica il **volume di stampa** (X, Y, Z): Stellio avvisa prima dell'invio se il pezzo è troppo grande.

## Monitoraggio
- Temperatura, avanzamento, camera in diretta; miniatura e nome del file in corso sulla scheda.
- Contatore automatico delle ore di stampa.
- **Widget mobile** di avanzamento; si posiziona a sinistra della freccia «torna su» quando questa compare.

## Inviare allo slicer / alla stampante
- Finestra di invio con **anteprima rapida** (peso, tempo stimato), **scelta della bobina** e calibrazioni richiamate.
- **Controllo prima della stampa**: bobina da essiccare, filamento abrasivo (si consiglia l'ugello in acciaio temprato), calibrazione assente, volume di stampa, materiale sufficiente.
- **Ristampa come l'ultima volta** dalla cronologia.
- **Modalità collaborativa leggera**: avvisa se un altro dispositivo sta guardando il file o prima di un doppio invio.
- **Apri nello slicer** da «I miei G-code».

## Durante la stampa
- **Presa smart** (Shelly, Tasmota, Home Assistant): Stellio legge i watt e registra il consumo reale (kWh) e il costo.
- **Consumo reale di filamento**, registrato dopo la stampa.
- **Foto di fine stampa** scattata quando la stampa raggiunge il **100 %** (il pezzo è ancora sul piatto), una sola foto da valutare *Riuscito/Fallito*.
- **Sorveglianza dei guasti con IA** (Ollama con visione, 100 % locale): avviso in caso di spaghetti o pezzo staccato, **mai un arresto automatico**.
- **Timelapse** automatico (camera → video MP4, richiede ffmpeg).
- **Link di condivisione dello stato**, in sola lettura.

## Manutenzione
- **Manutenzione predittiva** con attività specifiche per ogni marchio.
- **Parti di usura** (ugelli, piatti, cinghie…) con avvisi di scorta, collegate alle attività di manutenzione.
- **Calibrazioni** (flusso, pressure advance, temperature) per filamento e stampante.

@@@ Filament | Filamento
# Filamento

## Fonti di inventario
| Fonte | Dettagli |
|---|---|
| **Spoolman** | Rilevamento automatico in rete. Stellio **non vi scrive più** il consumo (evita il doppio conteggio). |
| **Manuale** | Bobine inserite a mano, importazione Excel/CSV. |
| **TigerTag** | Identificazione NFC/RFID. Accesso con e-mail e password (viene conservato solo un token cifrato) o riuso di una sessione TigerTag Studio. **Sola lettura.** |
| **OpenPrintTag** | Standard aperto di etichette NFC: importazione/esportazione di file `.bin`, lettura/scrittura dall'app Android, peso consumato sempre aggiornato. |
| **Bambu AMS / Creality CFS** | Lettura degli slot. |

**Open Filament Database**: cerca una bobina per marchio, materiale e colore e creala con un clic (peso, diametro e densità precompilati).

## Ogni giorno
- **Consumo automatico** all'invio allo slicer, con controllo di compatibilità (c'è abbastanza materiale?).
- **Avvisi di scorta bassa** all'avvio, soglia regolabile, casella «Da ordinare» e link di acquisto.
- **Ricomprare una bobina**: prima il negozio del produttore (Arianeplast, Bambu Lab, Polymaker, eSUN, Sunlu…), poi i negozi generici; la disponibilità viene verificata automaticamente quando il sito lo consente.
- **Essiccazione**: registro, stato (asciutta / da essiccare) secondo il materiale, temperatura e durata suggerite, promemoria.
- **Scheda bobina**: stampe, grammi, costo e differenza non tracciata.

## Pesatura e previsione
Il blocco **Pesatura e previsione del filamento** stima la **data di esaurimento** di ogni bobina in base al consumo giornaliero.
- Il peso residuo proviene da una pesatura manuale o da TigerTag.
- I pesi TigerTag alimentano **solo la previsione**: compaiono qui solo per una bobina **in esaurimento** (14 giorni o meno). Il resto è nell'inventario.
- Un modulo di pesatura manuale è sempre disponibile.

{{img:filament}}

## Previsione dei consumi
La libreria può mostrare un **avviso di rifornimento** quando le scorte non bastano per i tuoi preferiti.

@@@ Downloads | Download
# Download

Scarica modelli direttamente nelle tue fonti da diverse piattaforme:

| Piattaforma | Accesso |
|---|---|
| **Printables** | API GraphQL |
| **MakerWorld** | Accesso Bambu Lab in 2 passaggi |
| **Thingiverse** | Chiave API |
| **Nexprint** (Elegoo) | E-mail e password dell'account, memorizzate cifrate |
| **Creality Cloud** | Dalle Impostazioni (credenziali cifrate; accesso con Google non supportato) |
| **Snapmaker Space** | Come sopra |

- **Ctrl+N** apre un nuovo download.
- Il file arriva nella fonte che scegli e l'**origine del modello** (link, autore, licenza) viene registrata.
- **Nuova versione**: ogni giorno Stellio controlla se i modelli scaricati (Printables, MakerWorld, Thingiverse) sono stati aggiornati.
- **I miei like / Le mie creazioni**: gli account collegati vengono testati a ogni avvio del desktop (ogni 24 h sul server).
- **Link utili**: negozi, produttori, siti di modelli e risorse, in sezioni comprimibili.

@@@ AI | Intelligenza artificiale
# Intelligenza artificiale

## IA locale (Ollama)
Per impostazione predefinita l'IA funziona **al 100 % in locale** con [Ollama](https://ollama.com/). Può essere disattivata.

Funzioni:
- **Etichettatura automatica** e **descrizione** dei modelli;
- **Ricerca semantica** in linguaggio naturale;
- **Analisi di stampabilità** e **orientamenti suggeriti**;
- **Raccomandazione del profilo slicer** (geometria + storico dei successi);
- **Stima del tempo di stampa** prima dello slicing;
- **Sorveglianza dei guasti** (modello di visione).

L'indirizzo del server Ollama si imposta nelle Impostazioni (`ollama_url`): puoi puntare a una macchina remota più potente (utile su un Raspberry Pi).

## IA online (edizione server, facoltativa)
Al posto di Ollama usa **Claude** (Anthropic), **ChatGPT** (OpenAI) o **Gemini** (Google) con la **tua chiave API** (Impostazioni → Intelligenza artificiale).
- La chiave è cifrata sul server e non viene mai rimandata al browser.
- Le richieste (nomi di file, etichette, descrizioni, foto di S.O.S Print) vanno al fornitore scelto e sono fatturate sulla tua chiave.
- Ollama resta la scelta predefinita.

## S.O.S Print
Diagnosi **adattiva** di un guasto di stampa:
1. Descrivi il problema (foto possibile a ogni passaggio) e, se vuoi, le impostazioni usate (temperature, velocità, retrazione…).
2. Stellio pone **una domanda alla volta** (al massimo 4) e restringe in diretta una lista di ipotesi.
3. Fornisce una **diagnosi finale**.

Le conversazioni vengono salvate: riaprile o segnale come risolte.

> ℹ️ I risultati «Riuscito / Fallito» che valuti nella cronologia migliorano le raccomandazioni.

@@@ Costs-and-Management | Costi e gestione
# Costi e gestione
{{img:management}}


## Calcolo del costo di stampa
Materiale, elettricità, usura della macchina (all'ora), spese fisse, margine in % e quantità: prezzo unitario e totale al centesimo.
- Il **margine predefinito** si imposta una volta in *Impostazioni → Prezzi di stampa*; la cronologia mostra il **prezzo di vendita** accanto al costo, mentre le statistiche mantengono il costo reale.
- **Costo del progetto**: lo stesso calcolo per tutti i file di un progetto.
- **Presa smart**: la potenza misurata sostituisce la stima dell'elettricità.
- **Impronta di CO₂** delle tue stampe (materiale + elettricità).

## Preventivi PDF
Generati dal calcolatore: cliente, descrizione, note; intestazione configurabile (nome/azienda, logo, indirizzo, telefono, e-mail, sito, partita IVA) e avvisi legali a piè di pagina. Ogni preventivo viene conservato (copia PDF) e consultabile nel widget **Preventivi**.

## Schermata «Gestione»
Visibile quando è spuntata l'opzione *Attiva le funzioni di costi, preventivi e fatturazione*:
- **Preventivi clienti**: un **link di tracciamento** permette al cliente di vedere, accettare o rifiutare il preventivo online; l'accettazione crea l'attività di stampa e mostra i tuoi dati per l'acconto. **Stellio non gestisce alcun pagamento.** I link sono sempre esterni; se l'accesso remoto è disattivato, la schermata propone di attivarlo con un clic.
- **Contabilità**: esportazione mensile ZIP (CSV dei documenti, PDF delle fatture, totali per mese).
- **Scorta di pezzi finiti**: soglia di avviso e rifornimento (attività creata a mano o automaticamente).

## Laboratorio
- **Coda degli ordini** con margine reale, rubrica clienti, pagamenti, fatture di acconto e note di credito, e-mail SMTP, esportazione CSV.
- **Pagina pubblica di tracciamento** per ordine, senza account: mai prezzi, margini o note interne.
- **Assegnazione intelligente**: Stellio propone la stampante più adatta per ogni attività (libera, materiale caricato, coda) **senza mai avviare una stampa**.
- **Riepilogo giornaliero o settimanale** tramite notifica e push (attività, ritardi, energia, bobine, fatture, scorte).
- **Condivisione dei profili slicer** con un'istanza associata.

## Rapporti
- **Affidabilità**: tasso di successo e costo dei guasti per profilo, materiale, stampante o bobina.
- **Rapporto mensile** confrontato con il mese precedente, esportabile in PDF.
- **Rapporto di stampa** condivisibile (immagine PNG) dalla cronologia.
- **Energia** reale per presa smart.



{{img:stats}}
@@@ Remote-Access | Accesso remoto e mobile
# Accesso remoto e mobile

## Telefono e tablet
- **Codice QR** per l'accesso mobile alla libreria (**PWA installabile**).
- **App Android companion**: un codice QR dedicato (Impostazioni → accesso mobile) scarica l'APK. Gestisce indirizzo interno ed esterno con passaggio automatico, associazione tramite QR, foto direttamente da una stampa e lettura/scrittura di etichette NFC OpenPrintTag.
- **Modalità officina** a schermo intero per tablet/telefono.

## Accesso remoto
- **Cloudflare Tunnel** (gratuito, indirizzo casuale o fisso), oppure un **indirizzo personalizzato** (nome di dominio, DynDNS, VPN, Tailscale…) per evitare Cloudflare, con ritorno a Cloudflare con un clic.
- **Link di condivisione** temporanei (24 h, uso singolo).

## Account
- **Account locali** con codice di recupero e domanda segreta.
- **Conferma della sessione**: aprendo l'app con una sessione salvata, Stellio chiede di confermare l'account.
- **Account ospite in sola lettura**: condividi libreria, stampanti e scorte senza rischi.
- Su PC, l'accesso via browser all'app Windows è bloccato (token interno): usa la finestra dell'applicazione.

## Più istanze di Stellio
- Le altre installazioni della rete locale vengono **rilevate** e si aggiungono con un clic (inserisci la loro chiave locale).
- **Inviare un file** a un'altra istanza, nella cartella che scegli.
- Widget di stato delle istanze sulla dashboard.

## Notifiche
- Notifiche native di **Windows**, notifiche del **browser** (Pi, telefono).
- **Push**: ntfy, Telegram, Discord o webhook, anche a finestra chiusa (fine stampa, guasto, manutenzione, scorte).

## Domotica
- **MQTT / Home Assistant**: pubblicazione dello stato e rilevamento automatico; dispositivo MQTT «Stellio» e sensori.

@@@ Server-Edition | Edizione server
# Edizione server

L'**edizione server** si attiva su Linux (Raspberry Pi, VM, LXC, Docker) o con `STELLIO_HEADLESS=1`. Windows e macOS mantengono l'app desktop. Stellio gira in background e si usa da un browser: `http://<ip>:5000`.

## Raspberry Pi / Linux
Requisiti: consigliato Raspberry Pi 4 o 5, Raspberry Pi OS a **64 bit**.

`install-pi.sh` installa le dipendenze di sistema (`ffmpeg`, `unrar`, librerie di rendering 3D), un ambiente Python dedicato e un **servizio systemd** `stellio` che parte all'avvio e riparte in caso di crash.

```bash
sudo systemctl status stellio
sudo systemctl restart stellio
sudo journalctl -u stellio -f
```
Poca RAM? Aumenta lo swap se l'installazione delle dipendenze Python fallisce e rilancia lo script.

## Proxmox VE (container LXC)
Lo script `stellio-lxc.sh` propone impostazioni **predefinite** o **avanzate** (CTID, core, RAM, disco, bridge, VLAN, DHCP o IP fisso, storage, cartella dell'host da montare), poi:
- crea un container **Debian 12 non privilegiato** (2 core, 2 GB di RAM, 32 GB di disco, avvio automatico);
- vi installa Stellio con `install-pi.sh`;
- mostra l'indirizzo `http://<ip-del-container>:5000` e la password di root.

```bash
pct exec <CTID> -- update-stellio              # aggiornare
pct exec <CTID> -- journalctl -u stellio -f    # log
```
- **Modalità non interattiva**: variabili `var_mode=default var_cpu=4 var_ram=4096 var_disk=16 var_ip=192.168.1.50/24 var_gw=192.168.1.1` (elenco all'inizio dello script).
- **Storage**: `var_choose_storage=1`, `var_storage`, `var_template_storage`.
- **Lingua** dello script: `var_lang=it` (fr, en, de, es, pt, it, zh, ja).
- **Fonti**: in questo container vengono proposte solo le condivisioni **SMB/NFS**. Con `var_mount=/host:/mnt/models` è consentita anche la «Cartella locale». Impostazione: `/etc/systemd/system/stellio.service.d/sources.conf` (`STELLIO_ALLOWED_SOURCE_TYPES`).

## Salvaguardie (1.0.7)
`install-pi.sh` configura:
- una **sorveglianza ogni minuto** (`stellio-watchdog`): riavvia Stellio se non risponde più (3 controlli falliti, 3 minuti di tolleranza dopo un avvio), lo avvia se è fermo, riavvia la rete se l'indirizzo IP va perso e pulisce log e cache di apt se il disco ha meno di 300 MB liberi;
- un servizio che **non rinuncia mai** a riavviarsi;
- limiti **CPU 75 %**, **RAM 75 % (rallentamento) / 85 % (limite rigido)**, priorità bassa, e Stellio viene sacrificato per primo quando manca la memoria;
- log limitati a **100 MB**.

Interventi della sorveglianza: `journalctl -t stellio-watchdog`. I container esistenti ricevono tutto questo con `update-stellio`.

## Particolarità dell'edizione server
- ☁️ **IA online** facoltativa (vedi [Intelligenza artificiale](it-AI)).
- 📥 **Profili slicer**: Stellio non vede gli slicer sul tuo PC e non si collega ai cloud degli slicer (Orca Cloud, Bambu Cloud…). Esporta i tuoi profili (OrcaSlicer: File → Esporta → Esporta pacchetto preset) e importali in *Impostazioni → I miei profili slicer*, oppure usa una **cartella di profili sorvegliata** (Syncthing, condivisione di rete, scp…).
- 🐯 **TigerTag**: accesso ufficiale con e-mail e password; account Google? Imposta prima una password con «Password dimenticata» nell'app TigerTag. Alternativa: copiare la cartella dati di TigerTag Studio sul server.
- Dopo un aggiornamento, il browser si ricarica automaticamente.

## Variabili d'ambiente
| Variabile | Funzione |
|---|---|
| `STELLIO_HEADLESS` | Forza la modalità server |
| `STELLIO_PORT` | Porta (predefinita 5000) |
| `STELLIO_SERVER_URL` | Indirizzo pubblico del server |
| `STELLIO_DATA_DIR` | Cartella dei dati |
| `STELLIO_ALLOWED_SOURCE_TYPES` | Tipi di fonte consentiti (`folder,smb,nfs`) |
| `STELLIO_START_MINIMIZED` | Avvia ridotto a icona |
| `STELLIO_NO_AUTO_INSTALL` | Disattiva l'installazione automatica dei moduli |

@@@ Settings-and-Data | Impostazioni e dati
# Impostazioni e dati

## Aspetto
- **Tema**: Scuro / Chiaro / Sistema. Per impostazione predefinita **chiaro**; scuro solo se il sistema (o tu) lo richiede.
- **Temi di marca**: Stellio, Bambu, Prusa, Voron, Creality; 33 palette, colore di accento personalizzato, immagine di sfondo regolabile.
- **Accessibilità**: alto contrasto, animazioni ridotte, focus da tastiera visibile, dimensione del testo, modalità daltonici.
- **8 lingue**: fr, en, de, es, it, pt, ja, zh.
- Navigazione riordinabile con il trascinamento; **annulla l'ultima impostazione modificata**.

{{img:settings}}

## Scorciatoie da tastiera
| Scorciatoia | Azione |
|---|---|
| `Ctrl+K` | Palette dei comandi |
| `Ctrl+F` | Ricerca |
| `Ctrl+N` | Nuovo download |
| `Ctrl+,` | Impostazioni |
| `Ctrl+Z` | Annulla l'ultima eliminazione |
| `Alt+1-8` | Navigazione rapida |
| `Maiusc+clic` | Seleziona un intervallo |
| `↑ ↓ ← →` + `Invio` | Navigare e aprire |
| `F` | Preferiti |
| `T` | Gestore etichette |
| `?` | Aiuto sulle scorciatoie |
| `Esc` | Chiudi / cancella la ricerca |

## Dove sono i miei dati?
| Sistema | Cartella |
|---|---|
| Windows | `%APPDATA%\Stellio` |
| macOS / Linux | `~/.stellio` |
| Windows portatile | `data` accanto a `Stellio.exe` |
| Personalizzato | variabile `STELLIO_DATA_DIR` |

Contenuto: database `stellio.db` (SQLite), impostazioni `app_settings.json`, registro `stellio.log`, moduli scaricati `extra_libs`. Il codice resta separato dai dati e un aggiornamento non lo tocca mai.

## Backup
- **Esportazione / importazione completa** (.zip) dei tuoi dati.
- **Backup automatici** programmabili.
- **Cestino** di 5 minuti, registro delle operazioni con annullamento.
- Gli aggiornamenti non fanno mai perdere dati.

## Log e diagnostica
- Il livello di log predefinito è **avviso**; il file `stellio.log` viene ricreato a ogni avvio.
- **Modalità debug**: attivala nelle Impostazioni; si applica al prossimo avvio.
- **Esporta la diagnostica** (Impostazioni → Diagnostica): segreti mascherati, stampanti integrate elencate (tipo, modello, stato — senza nome, indirizzo né chiave).
- Blocco **Salute di Stellio**: stato generale dell'app.

## Suggerimenti e bug
Dall'applicazione: **Suggerimenti e bug** nella barra laterale. Il messaggio diventa una issue GitHub (anonima, tramite una GitHub App), con un badge «Nuova risposta».

@@@ Troubleshooting | Risoluzione dei problemi
# Risoluzione dei problemi

Prima di tutto: esporta la **diagnostica** (Impostazioni → Diagnostica) e conservala per una segnalazione.

## La schermata resta bianca all'avvio (macOS)
La porta **5000** è spesso occupata dal *Ricevitore AirPlay* (un 403 in Safari). Stellio sceglie ora **automaticamente** una porta libera (5001–5030). Altrimenti: Impostazioni di Sistema → Generali → AirDrop e Handoff → disattiva *Ricevitore AirPlay*. Log: `~/.stellio/stellio.log` (vuoto al livello normale: attiva la modalità debug).

## Il container LXC diventa irraggiungibile
Dalla shell di Proxmox:
1. `pct status <CTID>`, poi `pct start <CTID>` se è fermo.
2. `pvesm status`: **storage pieno**? È la causa più frequente quando lo storage è condiviso.
3. `pct exec <CTID> -- free -m` e `dmesg -T | grep -i "oom\|killed process"`: memoria esaurita.
4. `pct exec <CTID> -- ip -4 a`: l'IP DHCP è cambiato? Riservalo sul router.
5. `pct exec <CTID> -- systemctl status stellio` e `journalctl -u stellio -n 100`.

Dalla 1.0.7, la sorveglianza automatica gestisce i casi comuni; vedi `journalctl -t stellio-watchdog`.

## Le miniature sono lente o non compaiono
- Scegli *Impostazioni → Prestazioni delle miniature*: **Eco** su una macchina piccola.
- I file molto pesanti mantengono una miniatura sostitutiva dopo un timeout.
- La generazione si mette in pausa mentre usi l'app: è normale.

## La mia stampante non viene rilevata
- Verifica che sia sulla stessa rete (VLAN, Wi-Fi ospiti).
- Aggiungila a mano con il suo indirizzo IP e la sua chiave.
- Bambu Lab: attiva la modalità LAN; Klipper: l'API Moonraker deve essere raggiungibile.

## Manca la foto di fine stampa
Attiva la casella *Foto di fine stampa* sulla stampante (come la sorveglianza IA e la presa smart) e verifica che la camera risponda.

## «Modulo mancante»
Al primo avvio di ogni versione, Stellio scarica i moduli mancanti. Controlla la connessione a internet; non impostare `STELLIO_NO_AUTO_INSTALL` se non necessario.

## Windows SmartScreen / macOS blocca l'app
I programmi di installazione non sono firmati. Controlla il `.sha256`, poi *Ulteriori informazioni → Esegui comunque* (Windows) o clic destro → *Apri* (macOS).

## Ottenere aiuto
[GitHub Issues](https://github.com/stellio-app/stellio/issues), [Discord](https://discord.gg/ySxpHvS6bd) o **Suggerimenti e bug** nell'app. Indica: versione di Stellio, sistema, passaggi per riprodurre, log esportato.

@@@ Contributing | Contribuire
# Contribuire

I contributi sono benvenuti. 🎉

1. Fai un **fork** del repository.
2. Crea il tuo branch: `git checkout -b feature/MiaFunzione`.
3. Fai commit: `git commit -m "Aggiunge MiaFunzione"`.
4. Fai push: `git push origin feature/MiaFunzione`.
5. Apri una **Pull Request**.

Regole: rispettare lo stile esistente, commentare in francese o inglese, testare su Windows se possibile, aggiornare la documentazione. Ogni nuova stringa dell'interfaccia va aggiunta in **tutti gli 8 file di lingua**.

## Tecnologie
| Componente | Tecnologia |
|---|---|
| Backend | Python 3.8+, Flask, Waitress |
| Frontend | HTML5, CSS3, JavaScript puro (senza build) |
| Database | SQLite (modalità WAL) |
| Desktop | pywebview (Windows, macOS) / browser (server) |
| 3D | PyRender, rasterizzatore CPU numpy, Three.js |
| Mesh | trimesh, pymeshfix, shapely, rectpack |
| IA | Ollama (locale) |
| Rete | paho-mqtt, smbclient, requests |
| Cifratura | cryptography (AES) |

## Struttura del repository
```
stellio/
├── main.py            Nucleo Flask: database, auth, libreria, stampanti, IA, avvio
├── modules/           Funzioni separate da main.py (print_session, timelapse, quote_portal…)
├── interface/         index.html, script.js, style.css, management.js (JavaScript puro)
├── packaging/         launcher.py, installer Windows (.iss), permessi macOS
├── languages/         Traduzioni (8 lingue) e changelog.json
├── tests/  tools/     Test pytest, strumenti di manutenzione
├── release-notes/     notes_version_X.Y.Z.txt
├── install-pi.sh      Installazione Raspberry Pi / Linux
└── stellio-lxc.sh     Installazione Proxmox LXC
```
Un modulo dichiara i servizi di `main.py` che usa (`_REQUIRED`), le sue rotte (`_ROUTES`) e una funzione `init`. Controllo prima della pubblicazione: `python -m pytest tests -q`.

## Sicurezza e privacy
- Stellio è **local-first**: per impostazione predefinita nulla viene raccolto o inviato. Unica eccezione, se la attivi: l'IA online dell'edizione server.
- I file di codice e configurazione non sono raggiungibili dal browser; l'API è protetta da sessione e CSRF; gli ospiti sono in sola lettura; i segreti sono cifrati.
- Ogni versione è pubblicata con un checksum `.sha256` verificato dall'aggiornamento integrato.

## Licenza
**GNU AGPL v3**: puoi copiare, modificare e distribuire Stellio; se lo modifichi o lo offri come servizio di rete, devi pubblicare il codice sorgente con la stessa licenza.

## Partnership e ringraziamenti
Stellio è partner ufficiale di integrazione di **TigerTag** ([tigersystem.io](https://tigersystem.io)). Grazie a Ollama, Flask, Three.js, trimesh, Spoolman e alla community dei maker. ☕ Sostieni: [Ko-fi](https://ko-fi.com/E6J828RYVD).
