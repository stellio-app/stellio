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

### 📚 Gestione della libreria
- 🗂️ **Sorgenti multiple**: cartelle locali, singoli file, condivisioni SMB/NFS
- 🖼️ **Miniature 3D automatiche** tramite PyRender (rendering di alta qualità) o un rasterizzatore CPU numpy (soluzione di riserva)
- 🏷️ **Tag personalizzati** con colori + tagging automatico via IA
- 🔍 **Ricerca semantica assistita dall'IA** ("cerco un supporto per...")
- ⭐ **Preferiti** e filtri avanzati (tipo, dimensione, peso, stato di stampa)
- 🧩 **Progetti/Assemblaggi**: raggruppa più file in un unico oggetto, con supporto multi-piatto 3MF (navigazione tra i piatti nel visualizzatore)
- 🔁 **Rilevamento duplicati** (esatti e simili per geometria)
- 📊 **Statistiche dettagliate** (formati, piattaforme, affidabilità dei profili)

### 🤖 Intelligenza artificiale (Ollama locale)
- 🏷️ **Tagging automatico** intelligente dei file
- 📝 **Descrizione automatica** dei modelli
- 🔎 **Ricerca semantica** in linguaggio naturale
- 📐 **Analisi di stampabilità** (rilevamento degli sbalzi)
- 🎯 **Raccomandazione del profilo slicer** basata su geometria + storico dei successi
- 🩺 **S.O.S Print**: diagnosi adattiva dei fallimenti di stampa, passo dopo passo — Stellio pone una domanda alla volta, restringe una lista di ipotesi in base alle tue risposte (massimo 4 domande) e infine fornisce una diagnosi finale; l'analisi delle foto è disponibile in qualsiasi momento

### 🖨️ Gestione delle stampanti
- 🔌 Supporto per **OctoPrint**, **Klipper/Moonraker**, **Bambu Lab** (MQTT), **Creality** (WebSocket), **FlashForge**
- 📡 **Rilevamento automatico in rete**: Stellio scansiona la tua rete locale (SSDP per Bambu Lab, broadcast UDP per Elegoo/Centauri/FlashForge, probing mirato per Klipper/OctoPrint/PrusaLink/Creality) e ti permette di aggiungere le stampanti rilevate con un clic
- 📡 Monitoraggio in tempo reale (temperature, avanzamento, telecamera)
- 🔧 **Manutenzione predittiva** con tracciamento delle attività e raccomandazioni specifiche per marca (Bambu, Prusa, Creality, ecc.)
- ⏱️ Contatore automatico delle ore di stampa
- 📤 Invio diretto allo slicer, con un selettore di bobina per assegnare il filamento giusto direttamente dalla finestra di invio, oppure upload alla stampante

### 🧵 Gestione del filamento
- 🔗 Integrazione **Spoolman** (server di gestione bobine)
- 🏷️ Integrazione dell'inventario **TigerTag** (sola lettura)
- 🟠 Supporto **AMS Bambu Lab** (lettura degli slot)
- 🟢 Supporto **CFS Creality**
- ⚪ Bobine manuali
- 📉 Tracciamento automatico del consumo all'invio allo slicer, con verifica di compatibilità prima della stampa (materiale sufficiente?)
- 🔔 **Avvisi di scorte basse** all'avvio, con un link rapido per riacquistare

### 📥 Download dalle piattaforme
- 🟠 **Printables** (API GraphQL)
- 🟢 **MakerWorld** (login Bambu Lab in 2 passaggi)
- 🔵 **Thingiverse** (tramite chiave API)
- 🟣 **Cults3D**
- 📁 Download diretto nelle sorgenti configurate

### 🧩 Strumenti avanzati
- 🎨 **Nesting automatico** sul piatto (rectpack o sagoma reale tramite shapely)
- 🔧 **Riparazione mesh** (trimesh + pymeshfix)
- 🔄 **Convertitore di formato** (STL ↔ 3MF ↔ OBJ)
- 🛡️ **Verifica dell'integrità** (file corrotti/mancanti)
- 💰 **Calcolo del costo di stampa** (materiale + elettricità)
- 📸 **Galleria fotografica delle stampe** (riuscite/fallite)
- 🕒 **Cronologia** con valutazione successo/fallimento (alimenta l'IA)

### 🌐 Accesso mobile e remoto
- 📱 **QR code** per accedere alla libreria da mobile (PWA installabile)
- 📲 **App companion Android**: un QR code dedicato consente di scaricare e installare l'APK dell'app companion Stellio direttamente dalle impostazioni di accesso mobile
- 🌍 **Accesso remoto** tramite Cloudflare Tunnel (gratuito, URL casuale o fisso)
- 🔗 **Link di condivisione** temporanei (24 ore, uso singolo)

### 🎨 Personalizzazione
- 🌓 Temi: Scuro / Chiaro / Sistema
- 🎨 Temi del brand: Stellio, Bambu, Prusa, Voron, Creality
- 🎯 Colore d'accento personalizzato
- 🌍 **8 lingue**: FR, EN, DE, ES, IT, PT, JA, ZH
- 🧲 Riordino della navigazione tramite drag & drop

### 💾 Backup e aggiornamenti
- 📦 Esportazione/importazione di backup completo (.zip)
- 🔄 Aggiornamenti automatici da GitHub (patch `.zip` — stesso meccanismo su Windows e Raspberry Pi/Linux)
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
2. Esegui `Stellio-Setup.exe`
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
- le dipendenze di sistema (`ffmpeg`, `unrar-free`, librerie di rendering 3D)
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
| `Ctrl+F` | Ricerca |
| `Ctrl+N` | Nuovo download |
| `Ctrl+,` | Impostazioni |
| `Alt+1-8` | Navigazione rapida |
| `F` | Attiva/disattiva preferiti |
| `T` | Gestore dei tag |
| `?` | Guida scorciatoie |
| `Esc` | Chiudi modale / svuota ricerca |

### Struttura del progetto

```
stellio/
├── main.py                 # Backend Flask + Desktop
├── script.js                # JavaScript frontend
├── index.html                # Interfaccia principale
├── style.css                  # Stili
├── launcher.py                  # Launcher leggero / bootstrap del runtime
├── check_deps.py                 # Verifica dipendenze auto-riparante
├── worker.py                       # Worker in background (miniature, scansioni)
├── assets/                          # Loghi, icone
├── languages/                        # File di traduzione (JSON)
├── apk/                                # Pacchetto dell'app companion Android
├── docs/                                # Documentazione, informativa sulla privacy, README tradotti
├── requirements.txt                      # Dipendenze Python
├── install-pi.sh                          # Script di installazione per Raspberry Pi / Linux (servizio systemd)
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

Gli eseguibili Windows pubblicati nelle [Releases](https://github.com/stellio-app/stellio/releases) sono firmati digitalmente. Vedi [CODE_SIGNING_POLICY.md](../../CODE_SIGNING_POLICY.md) per i dettagli sul nostro processo di firma e sulla protezione della chiave privata.

---

## 🙏 Ringraziamenti

- [Ollama](https://ollama.com/) per l'IA locale
- [Flask](https://flask.palletsprojects.com/) per il backend
- [Three.js](https://threejs.org/) per il rendering 3D sul web
- [trimesh](https://github.com/mikedh/trimesh) per l'elaborazione delle mesh
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

---

<p align="center"><strong>Fatto con ❤️ per la community dei maker</strong></p>

<p align="center">
  <a href="https://github.com/stellio-app/stellio">⭐ Metti una stella a questo repo</a> •
  <a href="https://github.com/stellio-app/stellio/issues">🐛 Segnala un bug</a> •
  <a href="https://github.com/stellio-app/stellio/discussions">💡 Proponi una funzionalità</a>
</p>
