<p align="center">
  <img src="https://stellio-app.com/assets/logo-nom-stellio.png" alt="Logo Stellio" width="360">
</p>

<h3 align="center">Il gestore di file 3D definitivo per maker e proprietari di stampanti 3D</h3>

<p align="center">
  <a href="https://github.com/stellio-app/stellio/releases"><img src="https://img.shields.io/github/v/release/stellio-app/stellio?color=blue" alt="Versione"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python"></a>
  <a href="https://flask.palletsprojects.com/"><img src="https://img.shields.io/badge/flask-3.0+-green.svg" alt="Flask"></a>
  <a href="https://www.gnu.org/licenses/agpl-3.0"><img src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg" alt="License: AGPL v3"></a>
  <a href="https://github.com/stellio-app/stellio/blob/main"><img src="https://img.shields.io/badge/platform-Windows%20%7C%20Raspberry%20Pi%20%2F%20Linux-lightgrey.svg" alt="Platform"></a>
  <a href="https://github.com/stellio-app/stellio/blob/main"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"></a>
</p>

<p align="center">
  <a href="../../README.md">🇬🇧 English</a> |
  <a href="README.fr.md">🇫🇷 Français</a> |
  <a href="README.de.md">🇩🇪 Deutsch</a> |
  <a href="README.es.md">🇪🇸 Español</a> |
  🇮🇹 <strong>Italiano</strong> |
  <a href="README.pt.md">🇵🇹 Português</a> |
  <a href="README.ja.md">🇯🇵 日本語</a> |
  <a href="README.zh.md">🇨🇳 中文</a>
</p>

<p align="center">
  <a href="#-installazione">🚀 Installazione</a> •
  <a href="#-funzionalità">✨ Funzionalità</a> •
  <a href="#-documentazione">📖 Documentazione</a> •
  <a href="#-contribuire">🤝 Contribuire</a> •
  <a href="#-licenza">📜 Licenza</a>
</p>

---

## 🎯 Panoramica

**Stellio** è un'applicazione desktop moderna che centralizza tutta la tua libreria 3D (STL, 3MF, OBJ), automatizza le attività ripetitive e si integra perfettamente nel tuo flusso di lavoro di stampa 3D.

Che tu sia un maker alle prime armi o un utente esperto con più macchine, Stellio ti fa risparmiare tempo prezioso grazie all'**IA locale** (Ollama), a una **gestione intelligente delle stampanti** e a un'**interfaccia pensata per la produttività**.

> 💡 **Filosofia**: I tuoi dati restano con te. Tutto funziona in locale.

---

## ✨ Funzionalità

### 🏠 Dashboard e produttività
- 📊 **Dashboard all'avvio**: stampe in corso, scorte di filamento basse, ultime stampe e file recenti a colpo d'occhio
- 🧱 **Completamente personalizzabile**: riordino e nascondimento dei widget con drag & drop (12 disponibili: stampe in corso, scorte basse, ultimo S.O.S Print, suggerimenti, istanze Stellio…)
- ✅ **Checklist «Primi passi»** per i nuovi utenti
- 💡 **Widget «Suggerimenti»**: individua i file che ristampi spesso ma che non rivedi da tempo e i profili slicer con un alto tasso di fallimento
- ⌨️ **Palette comandi (`Ctrl+K`)**: naviga, avvia un'azione o trova all'istante un file, un tag, una bobina o un profilo slicer
- 🔔 **Centro notifiche (campanella)**: fine stampa, fallimenti, manutenzione in arrivo, scorte di filamento basse e promemoria di essiccazione in un unico posto
- 📺 **Widget mobile** che mostra l'avanzamento della stampa in corso, visibile in tutte le pagine
- 🧭 **Tour guidato interattivo** per scoprire le funzionalità principali, riavviabile dalle Impostazioni
- ♿ **Accessibilità**: modalità ad alto contrasto, riduzione delle animazioni, indicatori di focus da tastiera visibili ovunque

### 📚 Gestione della libreria
- 🗂️ **Sorgenti multiple**: cartelle locali, singoli file, condivisioni SMB/NFS — le cartelle 3D rilevate sul computer vengono proposte e aggiungibili con un clic
- 🖼️ **Miniature 3D automatiche** tramite PyRender (rendering di alta qualità) o un rasterizzatore CPU numpy (soluzione di riserva), con effetto di caricamento e **anteprima ingrandita al passaggio del mouse**
- 🏷️ **Tag personalizzati** con colori + tagging automatico via IA, e **tagging con un clic di più file selezionati**
- 🔍 **Ricerca semantica assistita dall'IA** ("cerco un supporto per...") con **ricerche recenti memorizzate**
- ⭐ **Preferiti** e filtri avanzati (tipo, dimensione, peso, stato di stampa), con un **avviso di rifornimento** quando le scorte di filamento non bastano per i tuoi preferiti
- 🧵 **Filtro «Scorte di filamento»**: mantiene solo i file stampabili con le bobine che hai davvero (Spoolman, inventario manuale, TigerTag), per materiale
- 💾 **Filtri salvati**: salva qualsiasi combinazione di filtri e riutilizzala con un clic
- 📋 **Coda «Da stampare presto»**, separata dai preferiti, riordinabile con drag & drop e inviabile direttamente allo slicer
- 🖱️ **Selezione rapida**: selezione a intervallo (`Maiusc+clic`) e navigazione da tastiera (frecce + `Invio`)
- ✏️ **Rinomina in blocco** (cerca/sostituisci, prefisso, suffisso, numerazione) con anteprima prima di applicare
- ↩️ **Annulla le eliminazioni** (`Ctrl+Z`) grazie a un cestino temporaneo di 5 minuti — anche l'eliminazione di un tag, di un progetto o di una sorgente è annullabile, senza conferma bloccante
- 🔗 **Origine del modello**: link di origine, autore, licenza e note nella scheda del file, con la data di download se applicabile
- 🧩 **Progetti/Assemblaggi**: raggruppa più file in un unico oggetto, con supporto multi-piatto 3MF (navigazione tra i piatti nel visualizzatore)
- 🔁 **Rilevamento duplicati** (esatti e simili per geometria)
- 🗜️ **Supporto agli archivi**: sfoglia ed estrai i modelli direttamente dagli archivi
- 🖱️ **Drag & drop di file 3D** da esplora risorse — funziona nell'app desktop e anche tramite browser (Raspberry Pi, mobile, accesso remoto)
- 📊 **Statistiche dettagliate** (formati, piattaforme, affidabilità dei profili)

### 🤖 Intelligenza artificiale (Ollama locale)
- 🏷️ **Tagging automatico** intelligente dei file
- 📝 **Descrizione automatica** dei modelli
- 🔎 **Ricerca semantica** in linguaggio naturale
- 📐 **Analisi di stampabilità** (rilevamento degli sbalzi) e **orientamenti suggeriti** (meno sbalzi, contatto con il piatto mostrato)
- 🎯 **Raccomandazione del profilo slicer** basata su geometria + storico dei successi
- ⏱️ **Stima del tempo di stampa** prima dello slicing
- 🩺 **S.O.S Print**: diagnosi adattiva dei fallimenti di stampa, passo dopo passo — Stellio pone una domanda alla volta, restringe una lista di ipotesi in base alle tue risposte (massimo 4 domande) e infine fornisce una diagnosi finale; l'analisi delle foto è disponibile in qualsiasi momento e le conversazioni vengono salvate (riapertura, segno «risolto»)

### 🖨️ Gestione delle stampanti
- 🔌 Supporto per **OctoPrint**, **Klipper/Moonraker**, **Bambu Lab** (MQTT), **Creality** (WebSocket), **FlashForge**, **Elegoo** (SDCP) e **PrusaLink**
- 📡 **Rilevamento automatico in rete**: Stellio scansiona la tua rete locale (SSDP per Bambu Lab, broadcast UDP per Elegoo/Centauri/FlashForge, probing mirato per Klipper/OctoPrint/PrusaLink/Creality) e ti permette di aggiungere le stampanti rilevate con un clic
- 📡 Monitoraggio in tempo reale (temperature, avanzamento, telecamera)
- 🔧 **Manutenzione predittiva** con tracciamento delle attività e raccomandazioni specifiche per marca (Bambu, Prusa, Creality, ecc.)
- 🔩 **Parti soggette a usura e materiali di consumo**: scorte di ugelli, piatti, cinghie… con avvisi, collegate alle attività di manutenzione (ogni intervento scala un pezzo)
- ⏱️ Contatore automatico delle ore di stampa
- 📤 Invio diretto allo slicer, con un selettore di bobina per assegnare il filamento giusto direttamente dalla finestra di invio, oppure upload alla stampante
- 👀 **Anteprima rapida** (peso, tempo di stampa stimato) direttamente nella finestra di invio allo slicer, prima di confermare
- 🛡️ **Controllo pre-stampa potenziato**: avvisa se la bobina assegnata deve essere essiccata, se il filamento è abrasivo (consigliato ugello in acciaio temprato) o se non esiste una calibrazione per questa stampante
- 🔁 **Ristampa come l'ultima volta**: dalla cronologia, un clic riapre la finestra di invio con la stessa stampante, lo stesso profilo e la stessa bobina
- 🎛️ **Calibrazioni**: salva flow, pressure advance, temperature… per filamento e per stampante, richiamate nella finestra di invio allo slicer
- 👥 **Modalità collaborativa leggera**: vedi se un altro dispositivo connesso sta già consultando un file, e un avviso evita di inviare due volte lo stesso file allo slicer per errore

### 🧵 Gestione del filamento
- 🔗 Integrazione **Spoolman** (server di gestione bobine), con rilevamento automatico sulla tua rete
- 🟠 Supporto **AMS Bambu Lab** (lettura degli slot)
- 🟢 Supporto **CFS Creality**
- 🐯 Integrazione **TigerTag** (identificazione NFC/RFID delle bobine): accedi per vedere le tue bobine TigerTag nell'inventario, oppure lascia che Stellio recuperi automaticamente una sessione TigerTag Studio esistente — sola lettura, non modifica mai il tuo inventario TigerTag
- ⚪ Bobine manuali
- 📉 Tracciamento automatico del consumo all'invio allo slicer, con verifica di compatibilità prima della stampa (materiale sufficiente?)
- 🔔 **Avvisi di scorte basse** all'avvio, con un link rapido per riacquistare
- 💨 **Essiccazione delle bobine**: registro di essiccazione, stato (asciutta / da essiccare) in base al materiale, temperatura e durata suggerite e promemoria nelle notifiche
- 📈 **Riepilogo per bobina**: stampe, grammi, costo e differenza non tracciata nella scheda di ogni bobina

### 📥 Download dalle piattaforme
- 🟠 **Printables** (API GraphQL)
- 🟢 **MakerWorld** (login Bambu Lab in 2 passaggi)
- 🔵 **Thingiverse** (tramite chiave API)
- 📁 Download diretto nelle sorgenti configurate
- 🆕 **Rilevamento di nuove versioni**: Stellio controlla ogni giorno se i modelli scaricati (Printables, MakerWorld, Thingiverse) sono stati aggiornati
- 🛒 **Link utili**: negozi, produttori, siti di modelli 3D e risorse raggruppati in sezioni comprimibili

### 🧩 Strumenti avanzati
- 🎨 **Nesting automatico** sul piatto (rectpack o sagoma reale tramite shapely)
- 🔧 **Riparazione mesh** (trimesh + pymeshfix) con **confronto prima/dopo** (tenuta stagna, triangoli, vertici, dimensione)
- 🔄 **Convertitore di formato** (STL ↔ 3MF ↔ OBJ)
- 🛡️ **Verifica dell'integrità** (file corrotti/mancanti)
- 💰 **Calcolo del costo di stampa**: materiale, elettricità, usura della macchina (all'ora), costi fissi, margine in % e quantità — prezzo unitario e totale calcolati al centesimo
- 🧾 **Preventivi PDF**: generati dal calcolo dei costi, con cliente, descrizione e note personalizzabili; intestazione del preventivo configurabile (nome/azienda, logo, indirizzo, telefono, e-mail, sito web, partita IVA) e note legali a piè di pagina
- 🌱 **Stima ambientale**: impronta di CO₂ delle tue stampe (materiale + elettricità)
- 📸 **Galleria fotografica delle stampe** (riuscite/fallite)
- 🕒 **Cronologia** con valutazione successo/fallimento (alimenta l'IA), pulsanti **«Vedi file»** e **«Ristampa»** su ogni riga (con rilevamento dei file spostati/eliminati) e filtri per piattaforma, risultato (riuscita/fallita/parziale/non valutata) e intervallo di date

### 📈 Report e affidabilità
- 🧮 **Affidabilità di stampa**: tasso di successo e costo dei fallimenti classificati per profilo slicer, materiale, stampante o bobina
- 🗓️ **Report mensile**: stampe, tasso di successo, filamento, costo, fallimenti e CO₂ del mese, confrontati con il mese precedente, esportabile in PDF

### 🔔 Notifiche
- 🪟 **Notifiche native di Windows**
- 🌐 **Notifiche del browser**, attivabili per l'accesso da Raspberry Pi o da mobile
- 📣 **Notifiche push** (ntfy, Telegram, Discord o webhook): fine e fallimento della stampa rilevati anche a finestra chiusa, oltre agli avvisi di manutenzione e di scorte

### 🌐 Accesso mobile e remoto
- 📱 **QR code** per accedere alla libreria da mobile (PWA installabile)
- 📲 **App companion Android**: un QR code dedicato consente di scaricare e installare l'APK dell'app companion Stellio direttamente dalle impostazioni di accesso mobile, con la possibilità di scattare foto direttamente da una stampa
- 🌍 **Accesso remoto** tramite Cloudflare Tunnel (gratuito, URL casuale o fisso), oppure **indirizzo personalizzato** (nome di dominio, DynDNS, VPN, Tailscale…) per fare a meno di Cloudflare, con ritorno a Cloudflare in un clic
- 🔗 **Link di condivisione** temporanei (24 ore, uso singolo)

### 👥 Account e multi-istanza
- 🔐 **Account locali** con codice di recupero e domanda segreta: reimpostazione della password al 100 % in locale, senza e-mail né internet
- 👤 **Account ospite in sola lettura**: condividi libreria, stampanti e scorte senza alcun rischio
- 🔄 **Istanze Stellio**: rilevamento automatico delle altre installazioni sulla rete locale e aggiunta con un clic (devi solo inserire la loro chiave locale)
- 📨 **Invio di un file a un'altra istanza**: scelta della cartella di destinazione sull'istanza di destinazione, il file ricevuto compare subito nella sua libreria
- ✅ **Widget di stato delle istanze** nella dashboard (spunta verde o croce rossa per ogni istanza salvata)

### 🎨 Personalizzazione
- 🌓 Temi: Scuro / Chiaro / Sistema
- 🎨 Temi del brand: Stellio, Bambu, Prusa, Voron, Creality
- 🎯 Colore d'accento personalizzato
- 🌍 **8 lingue**: FR, EN, DE, ES, IT, PT, JA, ZH
- 🧲 Riordino della navigazione tramite drag & drop
- ↩️ **Annulla impostazioni**: ripristina l'ultima modifica di configurazione effettuata

### 💾 Backup e aggiornamenti
- 📦 Esportazione/importazione di backup completo (.zip)
- 🔄 Aggiornamenti automatici da GitHub (patch `.zip` — stesso meccanismo su Windows e Raspberry Pi/Linux)
- 🔁 Riavvio affidabile dopo un aggiornamento o dopo l'attivazione della modalità debug, su Windows e Raspberry Pi/Linux
- 📋 Esportazione dei log diagnostici (segreti oscurati)

---

## 🖼️ Screenshot

| | |
|---|---|
| ![Libreria](../../library.png) *Libreria con miniature* | ![Stampanti](../../monitoring.png) *Monitoraggio stampanti* |
| ![Slicer](../../slicer.png) *Raccomandazione profilo via IA* | ![Nesting](../../nesting.png) *Nesting automatico* |

---

## 🚀 Installazione

### 🪟 Windows (consigliato)

1. Scarica l'ultimo installer dalle [Releases](https://github.com/stellio-app/stellio/releases)
2. Esegui `Stellio-Setup-<version>.exe`
3. Fatto! 🎉

### 🐧 Raspberry Pi / Linux

Funziona in **modalità server headless** (senza interfaccia grafica): Stellio gira in background e viene gestito da browser, sia sul Pi stesso sia da qualsiasi dispositivo sulla rete locale.

**Requisiti**: consigliato Raspberry Pi 4 o 5, Raspberry Pi OS a **64 bit**.

```bash
curl -O https://raw.githubusercontent.com/stellio-app/stellio/main/install-pi.sh
chmod +x install-pi.sh
./install-pi.sh
```

Lo script installa automaticamente:
- le dipendenze di sistema (`ffmpeg`, `unrar`, librerie di rendering 3D)
- un ambiente virtuale Python dedicato
- un **servizio systemd** (`stellio.service`) che avvia Stellio al boot e lo riavvia automaticamente in caso di crash

Una volta installato, Stellio è raggiungibile su `http://<ip-del-pi>:5000`.

```bash
sudo systemctl status stellio     # Stato del servizio
sudo systemctl restart stellio    # Riavvio
sudo journalctl -u stellio -f     # Segui i log in diretta
```

> 💡 **Stessi aggiornamenti di Windows**: la patch `.zip` pubblicata a ogni release è identica su entrambe le piattaforme (puro codice sorgente, nulla di compilato). Stellio la rileva e la applica automaticamente, poi riavvia il servizio — nessuna reinstallazione manuale necessaria.
>
> 🎥 Stesse funzionalità della versione Windows, ad eccezione della finestra desktop nativa (sostituita dall'accesso via browser) e dell'IA Ollama locale, che richiede un modello ragionevolmente potente per funzionare bene su un Pi — punta `ollama_url` a un server Ollama remoto nelle Impostazioni se necessario.

### Slicer supportati

Stellio rileva automaticamente:
- ✅ OrcaSlicer
- ✅ Bambu Studio
- ✅ PrusaSlicer / SuperSlicer
- ✅ Ultimaker Cura
- ✅ Creality Print

### Stampanti

| Tipo | Protocollo | Funzionalità |
|---|---|---|
| OctoPrint / PrusaLink | API HTTP | Monitoraggio, upload, telecamera |
| Klipper/Moonraker | API HTTP | Monitoraggio, upload, telecamera, ore esatte |
| Bambu Lab | MQTT (cloud + LAN) | Monitoraggio in tempo reale, AMS, telecamera (JPEG A1/P1, RTSPS X1/X2/H2), rilevamento SSDP |
| Creality | WebSocket | Monitoraggio, CFS, rilevamento UDP |
| FlashForge | API proprietaria | Monitoraggio, rilevamento UDP |
| Elegoo | SDCP su WebSocket | Monitoraggio, rilevamento UDP |

---

## 🛠️ Tecnologia

| Componente | Tecnologia |
|---|---|
| Backend | Python 3.8+, Flask, Waitress |
| Frontend | HTML5, CSS3, JavaScript vanilla |
| Database | SQLite (modalità WAL) |
| Desktop | pywebview (Windows) / modalità browser headless (Raspberry Pi, Linux) |
| Rendering 3D | PyRender, rasterizzatore CPU numpy, Three.js |
| Mesh e nesting | trimesh, pymeshfix, shapely, rectpack |
| IA | Ollama (locale) |
| Rete | paho-mqtt, smbclient, requests |
| Crittografia | cryptography (AES, IV casuale per ogni chiamata) |
| Archivi | zipfile, rarfile, py7zr, tarfile |

---

## 📖 Documentazione

### Scorciatoie da tastiera

| Scorciatoia | Azione |
|---|---|
| `Ctrl+K` | Palette comandi |
| `Ctrl+F` | Ricerca |
| `Ctrl+N` | Nuovo download |
| `Ctrl+,` | Impostazioni |
| `Ctrl+Z` | Annulla l'ultima eliminazione (cestino da 5 min) |
| `Alt+1-8` | Navigazione rapida |
| `Maiusc+Clic` | Seleziona un intervallo di file |
| `↑ ↓ ← →` + `Enter` | Naviga e apri i file nella libreria |
| `F` | Attiva/disattiva preferiti |
| `T` | Gestore dei tag |
| `?` | Guida scorciatoie |
| `Esc` | Chiudi modale / svuota ricerca |

### Struttura del progetto

```
stellio/
├── main.py             # Backend Flask + Desktop
├── script.js           # JavaScript frontend
├── index.html          # Interfaccia principale
├── style.css           # Stili
├── launcher.py         # Launcher leggero / bootstrap del runtime
├── check_deps.py       # Verifica dipendenze auto-riparante
├── worker.py           # Scheletro di worker 3MF non utilizzato (provvisorio)
├── assets/             # Loghi, icone
├── languages/          # File di traduzione (JSON)
├── apk/                # Pacchetto dell'app companion Android
├── docs/               # Documentazione, informativa sulla privacy, README tradotti
├── requirements.txt    # Dipendenze Python
└── install-pi.sh       # Script di installazione per Raspberry Pi / Linux (servizio systemd)
```

Hai un'idea? [Apri una issue](https://github.com/stellio-app/stellio/issues)!

---

## 🤝 Contribuire

I contributi sono benvenuti! 🎉

1. **Forka** il progetto
2. Crea il tuo branch (`git checkout -b feature/MiaFunzionalita`)
3. Esegui il commit delle modifiche (`git commit -m 'Aggiunta MiaFunzionalita'`)
4. Esegui il push del branch (`git push origin feature/MiaFunzionalita`)
5. Apri una **Pull Request**

### Linee guida
- Segui lo stile di codice esistente
- Aggiungi commenti in francese o inglese
- Se possibile, testa le modifiche su Windows
- Aggiorna la documentazione se necessario

### Segnalare un bug

Usa il template di segnalazione bug e includi:
- Versione di Stellio
- Sistema operativo
- Passaggi per riprodurre il problema
- Log degli errori (esportabili da Impostazioni → Diagnostica)

---

## 📜 Licenza

Questo progetto è distribuito con licenza **GNU Affero General Public License v3.0** — vedi il file [LICENSE](../../LICENSE) per i dettagli.

> 💡 **In breve**: sei libero di copiare, modificare e distribuire questo software. Se modifichi Stellio o lo usi per offrire un servizio in rete, devi pubblicare il codice sorgente completo con la stessa licenza AGPLv3.

---

## 🔒 Privacy

Stellio è local-first: i tuoi dati restano sul tuo dispositivo, per impostazione predefinita nulla viene raccolto o inviato a server esterni. Consulta la nostra [Informativa sulla privacy](../privacy/PRIVACY.md) per tutti i dettagli.

---

## 🔏 Policy di firma del codice

Il programma di installazione Windows e l'AppImage Linux pubblicati nelle [Releases](https://github.com/stellio-app/stellio/releases) **non sono ancora firmati digitalmente**, quindi Windows SmartScreen può mostrare un avviso. Le build macOS non sono notarizzate. Ogni file di una release è accompagnato da un checksum SHA-256 (`.sha256`) che puoi verificare, e l'aggiornatore integrato lo controlla prima dell'installazione. Vedi [CODE_SIGNING_POLICY.md](../../CODE_SIGNING_POLICY.md) per lo stato attuale, come verificare un download e i nostri piani di firma.

---

## 🙏 Ringraziamenti

- [Ollama](https://ollama.com/) per l'IA locale
- [Flask](https://flask.palletsprojects.com/) per il backend
- [Three.js](https://threejs.org/) per il rendering 3D sul web
- [trimesh](https://github.com/mikedh/trimesh) per l'elaborazione delle mesh
- [Spoolman](https://github.com/Donkie/Spoolman) per la gestione delle bobine di filamento
- [TigerTag](https://tigersystem.io) per l'identificazione NFC/RFID dei filamenti
- Alla community dei maker per feedback e suggerimenti
- A tutti i contributori ❤️

---

## 📞 Contatti e supporto

- 🐛 **Segnala un bug**: [GitHub Issues](https://github.com/stellio-app/stellio/issues)
- 💡 **Richiedi una funzionalità**: [GitHub Discussions](https://github.com/stellio-app/stellio/discussions)
- 📧 **Email**: contact@stellio-app.com
- 🌐 **Sito web**: [stellio-app.com](https://stellio-app.com)

---

## ⭐ Sostieni il progetto

Se Stellio ti è utile, puoi:
- Mettere una **stella** ⭐ su GitHub
- Condividere il progetto con la tua community
- [Contribuire al codice](#-contribuire) o alle traduzioni
- Segnalare bug per aiutare a migliorare l'app
- Sostenere lo sviluppo con una piccola mancia su Ko-fi ☕

<p align="center">
  <a href="https://ko-fi.com/E6J828RYVD">
    <img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="Sostieni Stellio su Ko-fi">
  </a>
</p>

---

<p align="center"><strong>Fatto con ❤️ per la community dei maker</strong></p>

<p align="center">
  <a href="https://github.com/stellio-app/stellio">⭐ Metti una stella a questo repo</a> •
  <a href="https://github.com/stellio-app/stellio/issues">🐛 Segnala un bug</a> •
  <a href="https://github.com/stellio-app/stellio/discussions">💡 Proponi una funzionalità</a>
</p>
