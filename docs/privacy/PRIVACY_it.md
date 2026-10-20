# Informativa sulla Privacy

**Ultimo aggiornamento:** 20 ottobre 2026  
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
- **Piattaforme di Modelli 3D**: Se utilizzi la funzione di download, Stellio si connette direttamente alle API di Printables, MakerWorld, Thingiverse o Nexprint (la libreria di Elegoo) utilizzando **le tue credenziali o chiavi API**. Queste informazioni non vengono mai inviate ai server di Stellio.
- **Gestione Stampanti**: Stellio comunica direttamente con le tue stampanti locali/di rete o server di stampa (OctoPrint, Klipper/Moonraker, Bambu Lab tramite MQTT). Queste comunicazioni rimangono confinate alla tua rete locale, a meno che non configuri esplicitamente l'accesso remoto.
- **Accesso Remoto (Tunnel Cloudflare)**: Se abiliti l'accesso remoto, il tuo traffico viene instradato in modo sicuro attraverso i server Cloudflare. Si prega di fare riferimento all'[informativa sulla privacy di Cloudflare](https://www.cloudflare.com/privacypolicy/) per i dettagli.
- **Intelligenza Artificiale (Ollama)**: Per impostazione predefinita, l'IA (Ollama) viene eseguita localmente sulla tua macchina. Se scegli di configurare un URL Ollama remoto nelle impostazioni, le tue richieste (descrizioni dei modelli, ricerca semantica) verranno inviate a quel server di terze parti che hai scelto tu stesso.
- **Spoolman**: Se colleghi Stellio a un server Spoolman esterno, i dati sul consumo di filamento vengono inviati a quel server che controlli o hai scelto.
- **Notifiche push (opzionali, disattivate per impostazione predefinita)**: Se le attivi nelle impostazioni, Stellio invia il titolo e il testo delle notifiche selezionate (ad esempio la fine o il fallimento di una stampa, che può citare il nome di un file o di una stampante) al servizio che scegli: ntfy (il server pubblico `ntfy.sh` o il tuo server), Telegram (con il token del bot e l'identificativo della chat che fornisci), un webhook Discord o un URL di webhook personale. Si applica quindi l'informativa sulla privacy di quel servizio. Su un server ntfy pubblico, chiunque conosca il nome del tuo topic può leggere i messaggi: scegli un topic difficile da indovinare oppure ospita il tuo server.
- **TigerTag (opzionale)**: Se usi l'integrazione TigerTag, Stellio si collega al tuo account TigerTag tramite i servizi di autenticazione e di database di Google (Firebase: `securetoken.googleapis.com`, `identitytoolkit.googleapis.com`, `firestore.googleapis.com`, oltre a `tigertag-cdn.web.app`) per leggere l'inventario delle tue bobine, e a `api.tigertag.io` per scaricare le tabelle di riferimento pubbliche. Il token di sessione è archiviato in forma crittografata sulla tua macchina.
- **Segnalazioni e suggerimenti (opzionali)**: Non viene inviato nulla finché non invii il modulo dando il tuo consenso esplicito. Il tipo, il titolo e la descrizione che scrivi vengono inviati a un relay ospitato su Cloudflare Workers, che crea una issue **pubblica** nel repository GitHub del progetto: non inserire informazioni personali né segreti. Se selezioni la casella delle informazioni tecniche, vengono aggiunti la versione di Stellio, il sistema operativo e la lingua dell'interfaccia. Stellio interroga poi l'API pubblica di GitHub per mostrare lo stato e i commenti delle tue richieste, e conserva localmente un token di gestione.
- **Monitoraggio degli aggiornamenti dei modelli (attivo per impostazione predefinita, disattivabile nelle impostazioni)**: Stellio chiede automaticamente a Printables, MakerWorld o Thingiverse (con il tuo token Thingiverse, se configurato) se i modelli che hai scaricato hanno una nuova versione. Viene inviato solo l'identificativo di ciascun modello.
- **Ricerca di bobine nei negozi (solo quando la usi)**: Quando verifichi la disponibilità di una bobina nei negozi, Stellio invia i tuoi termini di ricerca (marca, materiale, colore) ai siti dei negozi (ad esempio Atome3D, Rainbow3D, Amazon, il negozio Bambu Lab e i negozi della tua lista di link utili).
- **Altre istanze di Stellio (opzionale)**: Se aggiungi un'istanza Stellio remota o usi la funzione di rilevamento (che esegue la scansione della tua rete locale), Stellio contatta gli indirizzi interessati. I file o le cartelle che scegli di inviare viaggiano direttamente verso l'istanza selezionata, autenticati con la sua chiave di accesso, e non passano mai dai nostri server.

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