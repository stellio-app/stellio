# Privacy Policy

**Last updated:** September 1, 2026  
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
- **3D Model Platforms**: If you use the download feature, Stellio connects directly to the Printables, MakerWorld, or Thingiverse APIs using **your own credentials or API keys**. This information is never sent to Stellio servers.
- **Printer Management**: Stellio communicates directly with your local/network printers or print servers (OctoPrint, Klipper/Moonraker, Bambu Lab via MQTT). These communications remain confined to your local network, unless you explicitly configure remote access.
- **Remote Access (Cloudflare Tunnel)**: If you enable remote access, your traffic is securely routed through Cloudflare servers. Please refer to [Cloudflare's privacy policy](https://www.cloudflare.com/privacypolicy/) for details.
- **Artificial Intelligence (Ollama)**: By default, AI (Ollama) runs locally on your machine. If you choose to configure a remote Ollama URL in settings, your requests (model descriptions, semantic search) will be sent to that third-party server you have chosen yourself.
- **Spoolman**: If you connect Stellio to an external Spoolman server, filament consumption data is sent to that server you control or have chosen.

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