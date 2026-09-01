# Informativa sulla Privacy

**Ultimo aggiornamento:** 1° settembre 2026  
**Applicazione:** Stellio  
**Sito web:** [stellio-app.com](https://stellio-app.com)  
**Repository:** [github.com/stellio-app/stellio](https://github.com/stellio-app/stellio)

## 1. Introduzione
Benvenuto nell'Informativa sulla Privacy di Stellio. Stellio è un'applicazione per la gestione di file 3D e la stampa 3D. Questa informativa descrive come elaboriamo i dati.

La nostra filosofia fondamentale è semplice: **I tuoi dati restano con te. Tutto viene eseguito localmente.**

## 2. Principio Fondamentale: "Local-First"
Per impostazione predefinita, Stellio **non** raccoglie, trasmette né archivia **alcun dato** su server esterni. Tutti i tuoi file 3D (STL, 3MF, OBJ), i tuoi modelli di stampante, la cronologia di stampa, i tag e le impostazioni sono archiviati esclusivamente sulla tua macchina (Windows, Raspberry Pi o Linux) in un database SQLite locale.

## 3. Dati Archiviati Localmente
I seguenti elementi vengono salvati solo sul tuo dispositivo:
- La tua libreria di file 3D e i relativi metadati (tag, descrizioni, statistiche).
- Miniature 3D generate localmente (tramite PyRender o Matplotlib).
- Le tue configurazioni di stampanti e slicer.
- Le tue chiavi API e credenziali (archiviate localmente e crittografate tramite AES-CFB).
- Cronologia di stampa e foto associate.
- Registri di attività per la diagnostica.

## 4. Interazioni con Servizi di Terze Parti (Opzionali)
Per funzionare, alcune funzionalità *opzionali* di Stellio possono comunicare con servizi esterni. Mantieni il pieno controllo sull'attivazione di queste funzionalità:

- **Aggiornamenti automatici**: Stellio può interrogare i repository GitHub (`github.com/stellio-app/stellio`) per verificare la disponibilità di nuove versioni. Nessun identificativo personale viene trasmesso durante questa verifica.
- **Piattaforme di Modelli 3D**: Se utilizzi la funzione di download, Stellio si connette direttamente alle API di Printables, MakerWorld o Thingiverse utilizzando **le tue credenziali o chiavi API**. Queste informazioni non vengono mai inviate ai server di Stellio.
- **Gestione Stampanti**: Stellio comunica direttamente con le tue stampanti locali/di rete o server di stampa (OctoPrint, Klipper/Moonraker, Bambu Lab tramite MQTT). Queste comunicazioni rimangono confinate alla tua rete locale, a meno che non configuri esplicitamente l'accesso remoto.
- **Accesso Remoto (Tunnel Cloudflare)**: Se abiliti l'accesso remoto, il tuo traffico viene instradato in modo sicuro attraverso i server Cloudflare. Si prega di fare riferimento all'[informativa sulla privacy di Cloudflare](https://www.cloudflare.com/privacypolicy/) per i dettagli.
- **Intelligenza Artificiale (Ollama)**: Per impostazione predefinita, l'IA (Ollama) viene eseguita localmente sulla tua macchina. Se scegli di configurare un URL Ollama remoto nelle impostazioni, le tue richieste (descrizioni dei modelli, ricerca semantica) verranno inviate a quel server di terze parti che hai scelto tu stesso.
- **Spoolman**: Se colleghi Stellio a un server Spoolman esterno, i dati sul consumo di filamento vengono inviati a quel server che controlli o hai scelto.

## 5. Sicurezza dei Dati
- **Crittografia**: I dati sensibili (come chiavi API o password delle stampanti) vengono crittografati localmente utilizzando l'algoritmo AES-CFB.
- **Diagnostica**: Se incontri un bug, puoi esportare un registro diagnostico dalle impostazioni. Stellio maschera automaticamente i segreti e le informazioni sensibili prima dell'esportazione. Non raccogliamo questi registri automaticamente.

## 6. I Tuoi Diritti
Poiché tutti i tuoi dati sono archiviati localmente, hai il controllo assoluto su di essi:
- Puoi esportare tutti i tuoi dati in qualsiasi momento tramite la funzione di backup (`.zip`).
- Puoi eliminare qualsiasi file, voce di cronologia o impostazione direttamente dall'interfaccia.
- La disinstallazione dell'applicazione rimuove i file del programma, ma dovrai eliminare manualmente la cartella dei dati locali se desideri cancellare definitivamente la tua cronologia e il database.

## 7. Modifiche a Questa Informativa
Potremmo aggiornare questa informativa sulla privacy per riflettere le modifiche alle funzionalità di Stellio o agli obblighi legali. La data di "Ultimo aggiornamento" in cima a questo documento verrà rivista di conseguenza. Ti incoraggiamo a consultare periodicamente questa pagina.

## 8. Contatti
Se hai domande o preoccupazioni riguardanti questa informativa sulla privacy o la gestione dei tuoi dati, puoi contattarci:
- 📧 Email: [contact@stellio-app.com](mailto:contact@stellio-app.com)
- 🐛 Segnalazione bug: [GitHub Issues](https://github.com/stellio-app/stellio/issues)
- 💬 Discussioni: [GitHub Discussions](https://github.com/stellio-app/stellio/discussions)

---
*Questo progetto è open-source. Sei invitato a verificare il codice sorgente nel nostro repository GitHub per constatare personalmente il rispetto di questa informativa.*