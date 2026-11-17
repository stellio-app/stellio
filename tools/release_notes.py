#!/usr/bin/env python3
"""Génère le corps d'une release GitHub à partir de release-notes/notes.txt (fichier unique, contenu remplacé à chaque release).

Usage : python3 tools/release_notes.py <version> [sortie.md]

`<version>` ne sert que pour le titre : le contenu de notes.txt est celui de la release en cours.

Le fichier contient une section par langue (<!--fr-->, <!--en-->…), une ligne « ✓ » par nouveauté.
Le corps de la release reprend ces lignes telles quelles : français et anglais dépliés, les autres
langues dans des blocs repliables. Sans sortie, écrit sur stdout. Code retour 1 si la version est inconnue.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = [("fr", "🇫🇷 Français", True), ("en", "🇬🇧 English", True), ("de", "🇩🇪 Deutsch", False),
         ("es", "🇪🇸 Español", False), ("pt", "🇵🇹 Português", False), ("it", "🇮🇹 Italiano", False),
         ("zh", "🇨🇳 中文", False), ("ja", "🇯🇵 日本語", False)]


def parse(text):
    """{'fr': ['✓ …', …], …} à partir du fichier de notes."""
    sections, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^<!--\s*([a-z]{2})\s*-->\s*$", line.strip())
        if m:
            cur = m.group(1)
            sections[cur] = []
        elif cur and line.strip():
            sections[cur].append(line.strip())
    return sections


def build(version, repo="stellio-app/stellio"):
    path = os.path.join(ROOT, "release-notes", "notes.txt")
    if not os.path.isfile(path):
        raise SystemExit("Notes absentes : release-notes/notes.txt")
    with open(path, encoding="utf-8") as f:
        sections = parse(f.read())
    out = [f"## Stellio v{version}", ""]
    for code, title, opened in LANGS:
        lines = sections.get(code)
        if not lines:
            continue
        body = "\n".join(line + "  " for line in lines)   # deux espaces : un saut de ligne par « ✓ »
        if opened:
            out += [f"### {title}", "", body, ""]
        else:
            out += ["<details>", f"<summary><b>{title}</b></summary>", "", body, "", "</details>", ""]
    out.append(f"Full changelog / Historique complet : https://github.com/{repo}/blob/main/changelog.json")
    out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    text = build(sys.argv[1].lstrip("v"))
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            f.write(text)
    else:
        sys.stdout.write(text)
