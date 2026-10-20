# Privacy Policy

**Last updated:** October 20, 2026  
**Application:** Stellio  
**Website:** [stellio-app.com](https://stellio-app.com)  
**Repository:** [github.com/stellio-app/stellio](https://github.com/stellio-app/stellio)

## 1. Introduction
Welcome to Stellio's Privacy Policy. Stellio is a 3D file management and 3D printing application. This policy describes how we process data.

Our fundamental philosophy is simple: **Your data stays with you. Everything runs locally.**

## 2. Core Principle: "Local-First"
By default, Stellio does **not** collect, transmit, or store **any data** on external servers. All your 3D files (STL, 3MF, OBJ), your printer models, print history, tags, and settings are stored exclusively on your own machine (Windows, Raspberry Pi, or Linux) in a local SQLite database.

## 3. Locally Stored Data
The following items are saved only on your device:
- Your 3D file library and their metadata (tags, descriptions, statistics).
- 3D thumbnails generated locally (via PyRender or Matplotlib).
- Your printer and slicer configurations.
- Your API keys and credentials (stored locally and encrypted via AES-CFB).
- Print history and associated photos.
- Activity logs for diagnostics.

## 4. Third-Party Service Interactions (Optional)
To function, certain *optional* features of Stellio may communicate with external services. You retain full control over enabling these features:

- **Automatic updates**: Stellio may query GitHub repositories (`github.com/stellio-app/stellio`) to check for new version availability. No personal identifier is transmitted during this check.
- **3D Model Platforms**: If you use the download feature, Stellio connects directly to the Printables, MakerWorld, Thingiverse, or Nexprint (Elegoo's model library) services using **your own credentials or API keys**. This information is never sent to Stellio servers.
- **Printer Management**: Stellio communicates directly with your local/network printers or print servers (OctoPrint, Klipper/Moonraker, Bambu Lab via MQTT). These communications remain confined to your local network, unless you explicitly configure remote access.
- **Remote Access (Cloudflare Tunnel)**: If you enable remote access, your traffic is securely routed through Cloudflare servers. Please refer to [Cloudflare's privacy policy](https://www.cloudflare.com/privacypolicy/) for details.
- **Artificial Intelligence (Ollama)**: By default, AI (Ollama) runs locally on your machine. If you choose to configure a remote Ollama URL in settings, your requests (model descriptions, semantic search) will be sent to that third-party server you have chosen yourself.
- **Spoolman**: If you connect Stellio to an external Spoolman server, filament consumption data is sent to that server you control or have chosen.
- **Push notifications (optional, disabled by default)**: If you enable them in settings, Stellio sends the title and text of the notifications you select (for example the end or failure of a print, which may mention a file or printer name) to the service you choose: ntfy (the public `ntfy.sh` server or your own server), Telegram (using the bot token and chat identifier you provide), a Discord webhook, or a webhook URL of your own. That service's privacy policy then applies. On a public ntfy server, anyone who knows your topic name can read the messages: pick a hard-to-guess topic or host your own server.
- **TigerTag (optional)**: If you use the TigerTag integration, Stellio connects to your TigerTag account through Google's authentication and database services (Firebase: `securetoken.googleapis.com`, `identitytoolkit.googleapis.com`, `firestore.googleapis.com`, plus `tigertag-cdn.web.app`) to read your spool inventory, and to `api.tigertag.io` to download the public reference tables. The session token is stored encrypted on your machine.
- **Bug reports and suggestions (optional)**: Nothing is sent unless you submit the form and give your explicit consent. The type, title and description you write are sent to a relay hosted on Cloudflare Workers, which creates a **public** issue in the project's GitHub repository: do not include personal information or secrets. If you tick the technical information box, the Stellio version, operating system and interface language are added. Stellio then queries GitHub's public API to show the status and comments of your requests, and keeps a management token locally.
- **Model update tracking (enabled by default, can be disabled in settings)**: Stellio automatically asks Printables, MakerWorld or Thingiverse (with your Thingiverse token if you configured one) whether the models you downloaded have a new version. Only the identifier of each model is sent.
- **Filament shop search (only when you use it)**: When you check the availability of a spool in shops, Stellio sends your search terms (brand, material, color) to the shops' websites (for example Atome3D, Rainbow3D, Amazon, the Bambu Lab store, and the shops in your useful links list).
- **Other Stellio instances (optional)**: If you add a remote Stellio instance or use the discovery function (which scans your local network), Stellio contacts the addresses involved. The files or folders you choose to send travel directly to the instance you picked, authenticated by its access key, and never through our servers.

## 5. Data Security
- **Encryption**: Sensitive data (such as API keys or printer passwords) is encrypted locally using the AES-CFB algorithm.
- **Diagnostics**: If you encounter a bug, you can export a diagnostic log from settings. Stellio automatically masks secrets and sensitive information before export. We do not collect these logs automatically.

## 6. Your Rights
Since all your data is stored locally, you have absolute control over it:
- You can export all your data at any time via the backup function (`.zip`).
- You can delete any file, history entry, or setting directly from the interface.
- Uninstalling the application removes the program files, but you will need to manually delete the local data folder if you wish to permanently erase your history and database.

## 7. Changes to This Policy
We may update this privacy policy to reflect changes in Stellio's features or legal obligations. The "Last updated" date at the top of this document will be revised accordingly. We encourage you to review this page periodically.

## 8. Contact
If you have questions or concerns about this privacy policy or the management of your data, you can contact us:
- 📧 Email: [contact@stellio-app.com](mailto:contact@stellio-app.com)
- 🐛 Bug report: [GitHub Issues](https://github.com/stellio-app/stellio/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/stellio-app/stellio/discussions)

---
*This project is open-source. You are invited to audit the source code on our GitHub repository to verify for yourself compliance with this policy.*