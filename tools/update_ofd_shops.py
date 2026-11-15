#!/usr/bin/env python3
"""Génère languages/ofd_shops.json depuis un clone de l'Open Filament Database (licence MIT).

Usage :
    git clone --depth 1 https://github.com/OpenFilamentCollective/open-filament-database /tmp/ofd
    python3 tools/update_ofd_shops.py /tmp/ofd

Chaque dossier stores/<id>/store.json devient une boutique (nom, site, pays d'expédition). Les boutiques dont
l'id correspond à une marque de data/ sont marquées « boutique du fabricant » (champ `brands`).
La recherche s'appuie sur « site: » (le moteur de recherche cherche dans la boutique), car l'OFD ne fournit pas
d'adresse de recherche propre à chaque boutique.
"""
import glob
import json
import os
import sys
from urllib.parse import urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(ofd_dir):
    brand_names = {}
    for d in os.listdir(os.path.join(ofd_dir, 'data')):
        bj = os.path.join(ofd_dir, 'data', d, 'brand.json')
        if os.path.isfile(bj):
            try:
                brand_names[d] = json.load(open(bj, encoding='utf-8')).get('name') or d
            except Exception:
                brand_names[d] = d
        else:
            brand_names[d] = d
    shops = []
    for f in sorted(glob.glob(os.path.join(ofd_dir, 'stores', '*', 'store.json'))):
        s = json.load(open(f, encoding='utf-8'))
        url = (s.get('storefront_url') or '').strip()
        host = urlsplit(url).netloc
        if not s.get('id') or not s.get('name') or not host:
            continue
        entry = {'id': 'ofd_' + s['id'], 'name': s['name'], 'url': url, 'host': host,
                 'ships_from': s.get('ships_from') or [], 'ships_to': s.get('ships_to') or []}
        if s['id'] in brand_names:
            entry['brands'] = sorted({brand_names[s['id']], s['id'].replace('_', ' ')})
        shops.append(entry)
    out = {'source': 'https://github.com/OpenFilamentCollective/open-filament-database',
           'license': 'MIT', 'shops': shops}
    path = os.path.join(ROOT, 'languages', 'ofd_shops.json')
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    print(f'{len(shops)} boutiques -> {path}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
