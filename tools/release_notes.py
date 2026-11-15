#!/usr/bin/env python3
"""Génère le corps d'une release GitHub à partir de changelog.json.

Usage : python3 tools/release_notes.py <version> [sortie.md]

Anglais d'abord puis français, puis le lien vers le changelog complet.
Sans sortie, écrit sur stdout. Code retour 1 si la version est inconnue.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build(version, repo="stellio-app/stellio"):
    with open(os.path.join(ROOT, "changelog.json"), encoding="utf-8") as f:
        entries = json.load(f)
    entry = next((e for e in entries if e.get("version") == version), None)
    if entry is None:
        raise SystemExit(f"Version {version} absente de changelog.json")
    items = entry.get("items", {})
    out = [f"## Stellio v{version}", ""]
    for lang, title in (("en", "What's new"), ("fr", "Nouveautés")):
        lines = items.get(lang) or []
        if not lines:
            continue
        out.append(f"### {title}")
        out.extend(f"- {line}" for line in lines)
        out.append("")
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
