# bigprint inside Stellio

This folder contains the **bigprint** engine — free model cutter for life-size 3D prints —
by **Michael Christopher Stone**, https://github.com/PooterTF/bigprint, licensed under the
**GNU Affero General Public License v3 or later** (see `LICENSE` in this folder), the same license as Stellio.

- Imported from the upstream repository at commit `79f285ac8eb738fae51e5a6661d9158c879c991e` (2026-10-12, version 0.1.0).
- The Python files are **unmodified copies** (each keeps its `SPDX-License-Identifier` and copyright header).
- Not copied: the command line (`cli.py`, `__main__.py`), the standalone GUI page (`static/gui.html`), tests, packaging scripts and documentation.
  Stellio's own page (`interface/bigprint.js`) and routes (`modules/bigprint_tool.py`) replace the standalone GUI.
- `static/vendor/three/` is three.js r160 (MIT, see `LICENSE.txt` there), used for the 3D preview.

To update the engine, copy the same files from a newer upstream release and run `tests/test_bigprint_tool.py`.
