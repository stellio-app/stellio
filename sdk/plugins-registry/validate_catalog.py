#!/usr/bin/env python3
"""Valide catalog.json (bibliothèque standard seulement).

    python validate_catalog.py catalog.json            # contrôle complet (réseau)
    python validate_catalog.py catalog.json --offline  # structure seulement

Contrôles : champs obligatoires, id unique, https, empreinte sha256 (hex 64) égale à celle de l'archive
téléchargée, plugin.json de l'archive cohérent avec l'entrée, logo PNG/JPEG/WebP <= 200 Ko.
"""
import hashlib, io, json, re, sys, urllib.request, zipfile

ID_RE = re.compile(r'^[a-z0-9][a-z0-9_-]{1,39}$')
LANGS = ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja')
MAX_ZIP, MAX_LOGO = 2 * 1024 * 1024, 200 * 1024
PERMS = {'events', 'api:read', 'api:write', 'network', 'ui'}


def sniff(b):
    if b[:8] == b'\x89PNG\r\n\x1a\n': return 'png'
    if b[:3] == b'\xff\xd8\xff': return 'jpeg'
    if b[:4] == b'RIFF' and b[8:12] == b'WEBP': return 'webp'
    return None


def fetch(url, limit):
    req = urllib.request.Request(url, headers={'User-Agent': 'stellio-plugins-validator'})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read(limit + 1)
    if len(data) > limit:
        raise ValueError('trop volumineux (> %d octets)' % limit)
    return data


def check_entry(e, offline):
    errs = []
    pid = e.get('id', '?')
    if not isinstance(e.get('id'), str) or not ID_RE.match(e['id']): errs.append('id invalide')
    for k in ('name', 'version', 'author'):
        if not isinstance(e.get(k), str) or not e[k].strip(): errs.append(f'« {k} » manquant')
    d = e.get('description')
    if isinstance(d, dict):
        if not d or any(k not in LANGS or not isinstance(v, str) or not v.strip() for k, v in d.items()): errs.append('description : langues fr/en/de/es/pt/it/zh/ja, textes non vides')
        elif 'en' not in d and 'fr' not in d: errs.append('description : fournir au moins « en » ou « fr »')
        txt = ' '.join(d.values())
    elif isinstance(d, str) and d.strip(): txt = d
    else: errs.append('description manquante'); txt = ''
    if any(len(v) > 200 for v in (d.values() if isinstance(d, dict) else [txt])): errs.append('description trop longue (200 caractères maximum, 140 conseillés)')
    if not re.match(r'^https://', str(e.get('url', ''))): errs.append('url https requise')
    if not re.match(r'^[0-9a-f]{64}$', str(e.get('sha256', '')).lower()): errs.append('sha256 : 64 caractères hexadécimaux')
    if not isinstance(e.get('permissions', []), list) or set(e.get('permissions', [])) - PERMS: errs.append('permissions inconnues')
    for k in ('logo', 'homepage'):
        if e.get(k) and not str(e[k]).startswith('https://'): errs.append(f'« {k} » doit être en https')
    if offline or errs:
        return errs
    try:
        z = fetch(e['url'], MAX_ZIP)
        if hashlib.sha256(z).hexdigest() != e['sha256'].lower(): errs.append('sha256 différent de celui de l\'archive')
        with zipfile.ZipFile(io.BytesIO(z)) as zf:
            names = [n for n in zf.namelist() if n.endswith('plugin.json') and n.count('/') <= 1]
            if not names: errs.append('plugin.json absent de l\'archive')
            else:
                m = json.loads(zf.read(names[0]))
                for k in ('id', 'version'):
                    if m.get(k) != e.get(k): errs.append(f'« {k} » : catalogue {e.get(k)!r} ≠ archive {m.get(k)!r}')
                if sorted(m.get('permissions', [])) != sorted(e.get('permissions', [])): errs.append('permissions différentes de celles de plugin.json')
    except Exception as ex:
        errs.append(f'archive : {type(ex).__name__}: {ex}')
    if e.get('logo'):
        try:
            b = fetch(e['logo'], MAX_LOGO)
            if not sniff(b): errs.append('logo : PNG, JPEG ou WebP uniquement')
        except Exception as ex:
            errs.append(f'logo : {type(ex).__name__}: {ex}')
    return errs


def main(argv):
    if not argv:
        print(__doc__); return 2
    offline = '--offline' in argv
    path = [a for a in argv if not a.startswith('--')][0]
    try:
        cat = json.load(open(path, encoding='utf-8'))
    except Exception as ex:
        print(f'JSON illisible : {ex}'); return 1
    plugins = cat.get('plugins') if isinstance(cat, dict) else None
    if not isinstance(plugins, list):
        print('« plugins » doit être une liste'); return 1
    bad, seen = 0, set()
    for e in plugins:
        if not isinstance(e, dict): print('entrée invalide'); bad += 1; continue
        errs = check_entry(e, offline)
        if e.get('id') in seen: errs.append('id en double')
        seen.add(e.get('id'))
        for m in errs: print(f"{e.get('id', '?')}: {m}")
        bad += bool(errs)
    print(f'{len(plugins)} plugin(s), {bad} en erreur')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
