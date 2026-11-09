# Third-party licenses

Stellio itself is released under the **GNU Affero General Public License v3.0** (see `LICENSE`).
It uses the third-party components below, each under its own license. All of them are compatible with
distribution inside an AGPL-3.0 application. Versions are those checked on 2026-11-09 (`check_deps.py` lists the
Python modules the application needs).

## Python libraries

| Component | License |
|---|---|
| Flask, Werkzeug | BSD-3-Clause |
| cryptography | Apache-2.0 OR BSD-3-Clause |
| numpy | BSD-3-Clause (bundles 0BSD, MIT, Zlib, CC0 parts) |
| Pillow | MIT-CMU (HPND) |
| trimesh, cascadio | MIT (cascadio embeds OpenCASCADE, LGPL-2.1 with exception) |
| requests, websocket-client, rectpack | Apache-2.0 |
| packaging | Apache-2.0 OR BSD-2-Clause |
| nest_asyncio, pywebview, xlrd, PyOpenGL, qrcode, psutil, shapely, reportlab | BSD (2- or 3-clause) |
| smbprotocol, fast-simplification, pyrender, plyer, flashforge-python-api, openpyxl, argon2-cffi, pwdlib, amqtt, PyYAML | MIT |
| rarfile | ISC |
| waitress | ZPL-2.1 |
| defusedxml, matplotlib | Python Software Foundation License (matplotlib: PSF-based) |
| paho-mqtt | EPL-2.0 OR BSD-3-Clause (used under BSD-3-Clause) |
| py7zr | LGPL-2.1-or-later (used as an unmodified library) |
| pymeshfix | GNU AGPL v3 (same license as Stellio) |

Packaging: PyInstaller (GPL-2.0 with the bootloader exception, which allows any license for the packaged program).

## Programs downloaded or bundled at install time

| Component | License / terms |
|---|---|
| UnRAR (`UnRAR.exe` / `unrar`), used only to extract `.rar` archives | RARLAB freeware license: redistribution of the unmodified extractor is allowed; it may not be used to create RAR-compatible archivers. Include RARLAB's `license.txt` next to the binary. |
| Microsoft Edge WebView2 Runtime, Visual C++ Redistributable (downloaded by the Windows installer, not bundled) | Microsoft redistribution terms |

## Front-end assets (`assets/vendor/`)

| Component | License | Notes |
|---|---|---|
| three.js (+ OrbitControls, TrackballControls, STLLoader, OBJLoader, 3MFLoader) | MIT | Header kept in `three.min.js` |
| Font Awesome Free 6.7.2 | Icons: CC BY 4.0, fonts: SIL OFL 1.1, code: MIT | Attribution header kept in `all.min.css`; this file is the attribution |
| Material Design Icons (`mdi`) | Apache-2.0 (icons), SIL OFL 1.1 (font) | Source: https://github.com/Templarian/MaterialDesign |
| Inter | SIL OFL 1.1 | Source: https://github.com/rsms/inter. The OFL requires keeping the copyright and license text with the font files |

## Names and logos

The TigerTag logo is used with the permission that comes with the official integration partnership
(https://tigersystem.io). Printer, slicer, filament-service and model-site names (Bambu Lab, Prusa, Elegoo, Creality,
FlashForge, Klipper, OctoPrint, Spoolman, Printables, MakerWorld, Thingiverse, and others) are trademarks of their
owners and are used only to say which products Stellio works with. No affiliation is implied unless stated.
