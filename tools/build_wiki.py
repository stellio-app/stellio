#!/usr/bin/env python3
"""Génère le wiki GitHub de Stellio (8 langues) à partir de docs/wiki/.

    python tools/build_wiki.py --check            contrôle la structure des 8 langues (liens, tableaux, commandes)
    python tools/build_wiki.py --out wiki-out     génère les pages Markdown + les images dans wiki-out/

Sources :
  docs/wiki/src/<langue>.md          14 pages par langue, séparées par des lignes « @@@ Page | Titre »
  docs/wiki/images/<vX.Y.Z>/<langue>/<nom>.png   captures d'écran, un dossier par version
  changelog.json                     la page « Nouveautés » (Changelog) est générée à chaque fois

Dans les pages, une ligne « {{img:nom}} » est remplacée par la capture la plus récente portant ce nom
(version la plus haute qui la contient, dans la langue de la page, sinon en anglais, sinon en français).
Pour une nouvelle version, ajoutez seulement les captures qui ont changé dans docs/wiki/images/v<version>/.
"""
import argparse
import glob
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'docs', 'wiki', 'src')
IMG = os.path.join(ROOT, 'docs', 'wiki', 'images')
REPO = os.environ.get('GITHUB_REPOSITORY', 'stellio-app/stellio')

LANGS = [('fr', 'Français', '🇫🇷'), ('en', 'English', '🇬🇧'), ('de', 'Deutsch', '🇩🇪'), ('es', 'Español', '🇪🇸'),
         ('pt', 'Português', '🇵🇹'), ('it', 'Italiano', '🇮🇹'), ('zh', '中文', '🇨🇳'), ('ja', '日本語', '🇯🇵')]
PAGES = ['Home', 'Installation', 'Getting-Started', 'How-To', 'Library', 'Printers', 'Filament', 'Downloads', 'AI',
         'Costs-and-Management', 'Remote-Access', 'Server-Edition', 'Settings-and-Data', 'Troubleshooting', 'Contributing']
CHANGELOG_TITLE = {'fr': 'Nouveautés', 'en': "What's new", 'de': 'Neuigkeiten', 'es': 'Novedades', 'pt': 'Novidades',
                   'it': 'Novità', 'zh': '更新日志', 'ja': '更新履歴'}
CHANGELOG_INTRO = {
    'fr': "Les nouveautés de chaque version de Stellio (page générée automatiquement à partir du changelog).",
    'en': "What each Stellio version brings (page generated automatically from the changelog).",
    'de': "Was jede Stellio-Version bringt (Seite wird automatisch aus dem Changelog erzeugt).",
    'es': "Las novedades de cada versión de Stellio (página generada automáticamente a partir del changelog).",
    'pt': "As novidades de cada versão do Stellio (página gerada automaticamente a partir do changelog).",
    'it': "Le novità di ogni versione di Stellio (pagina generata automaticamente dal changelog).",
    'zh': "Stellio 每个版本的新内容（本页根据更新日志自动生成）。",
    'ja': "Stellio の各バージョンの新機能（この文書は更新履歴から自動生成されます）。"}
ALL_LANGS = {'fr': 'Toutes les langues', 'en': 'All languages', 'de': 'Alle Sprachen', 'es': 'Todos los idiomas',
             'pt': 'Todos os idiomas', 'it': 'Tutte le lingue', 'zh': '所有语言', 'ja': 'すべての言語'}
CAPTIONS = {
    'fr': {'dashboard': 'Le tableau de bord', 'library': 'La bibliothèque', 'viewer': 'La visionneuse 3D', 'projects': 'Les projets',
           'printers': 'Les imprimantes', 'filament': "L'inventaire de filament et le bloc « Pesée et prévision »",
           'stats': 'Les statistiques', 'management': "L'écran « Gestion » (devis clients)", 'settings': 'Les réglages'},
    'en': {'dashboard': 'The dashboard', 'library': 'The library', 'viewer': 'The 3D viewer', 'projects': 'Projects',
           'printers': 'Printers', 'filament': 'The filament inventory and the "Weighing and forecast" block',
           'stats': 'Statistics', 'management': 'The "Management" screen (client quotes)', 'settings': 'Settings'},
    'de': {'dashboard': 'Das Dashboard', 'library': 'Die Bibliothek', 'viewer': 'Der 3D-Viewer', 'projects': 'Projekte',
           'printers': 'Drucker', 'filament': 'Der Filamentbestand und der Block „Wiegen und Prognose"',
           'stats': 'Statistiken', 'management': 'Der Bildschirm „Verwaltung" (Kundenangebote)', 'settings': 'Einstellungen'},
    'es': {'dashboard': 'El panel de control', 'library': 'La biblioteca', 'viewer': 'El visor 3D', 'projects': 'Proyectos',
           'printers': 'Impresoras', 'filament': 'El inventario de filamento y el bloque «Pesaje y previsión»',
           'stats': 'Estadísticas', 'management': 'La pantalla «Gestión» (presupuestos de clientes)', 'settings': 'Ajustes'},
    'pt': {'dashboard': 'O painel', 'library': 'A biblioteca', 'viewer': 'O visualizador 3D', 'projects': 'Projetos',
           'printers': 'Impressoras', 'filament': 'O inventário de filamento e o bloco «Pesagem e previsão»',
           'stats': 'Estatísticas', 'management': 'O ecrã «Gestão» (orçamentos de clientes)', 'settings': 'Definições'},
    'it': {'dashboard': 'La dashboard', 'library': 'La libreria', 'viewer': 'Il visualizzatore 3D', 'projects': 'Progetti',
           'printers': 'Stampanti', 'filament': "L'inventario dei filamenti e il blocco «Pesatura e previsione»",
           'stats': 'Statistiche', 'management': 'La schermata «Gestione» (preventivi clienti)', 'settings': 'Impostazioni'},
    'zh': {'dashboard': '仪表盘', 'library': '资料库', 'viewer': '3D 查看器', 'projects': '项目',
           'printers': '打印机', 'filament': '耗材库存和“耗材称重与预测”模块',
           'stats': '统计', 'management': '“管理”界面（客户报价）', 'settings': '设置'},
    'ja': {'dashboard': 'ダッシュボード', 'library': 'ライブラリ', 'viewer': '3D ビューアー', 'projects': 'プロジェクト',
           'printers': 'プリンター', 'filament': 'フィラメント在庫と「フィラメントの計量と予測」ブロック',
           'stats': '統計', 'management': '「管理」画面（顧客向け見積）', 'settings': '設定'},
}
CHANGELOG_MAX_VERSIONS = 25


def parse(lang):
    text = open(os.path.join(SRC, f'{lang}.md'), encoding='utf-8').read()
    parts = re.split(r'^@@@ (\S+) \| (.+)$\n', text, flags=re.M)
    pages = {}
    for i in range(1, len(parts), 3):
        pages[parts[i]] = (parts[i + 1].strip(), parts[i + 2].strip('\n'))
    return pages


def _vkey(v):
    return tuple(int(x) for x in re.findall(r'\d+', v))


def image_versions():
    return sorted((os.path.basename(d) for d in glob.glob(os.path.join(IMG, 'v*')) if os.path.isdir(d)), key=_vkey, reverse=True)


def find_image(lang, name):
    """(version, langue) de la capture la plus récente : langue de la page, sinon anglais, sinon français."""
    for lg in (lang, 'en', 'fr'):
        for v in image_versions():
            if os.path.exists(os.path.join(IMG, v, lg, f'{name}.png')):
                return v, lg
    return None


def check():
    """Liste des problèmes de structure entre le français (référence) et les autres langues."""
    errs = []
    ref = parse('fr')
    for lang, _, _ in LANGS:
        path = os.path.join(SRC, f'{lang}.md')
        if not os.path.exists(path):
            errs.append(f'{lang}: fichier manquant')
            continue
        p = parse(lang)
        if list(p) != PAGES:
            errs.append(f'{lang}: pages {list(p)}')
            continue
        for s in PAGES:
            a, b = ref[s][1], p[s][1]
            if a.count('```') != b.count('```'):
                errs.append(f'{lang}/{s}: blocs de code')
            if len(re.findall(r'^#{1,3} ', a, re.M)) != len(re.findall(r'^#{1,3} ', b, re.M)):
                errs.append(f'{lang}/{s}: titres')
            if a.count('\n|') != b.count('\n|'):
                errs.append(f'{lang}/{s}: lignes de tableau')
            for x, y in zip(re.findall(r'```.*?```', a, re.S), re.findall(r'```.*?```', b, re.S)):
                if x.split('\n')[0] != y.split('\n')[0]:
                    errs.append(f'{lang}/{s}: langage de bloc de code')
            la = [re.sub(r'^fr-', '', m) for m in re.findall(r'\]\((fr-[A-Za-z-]+)\)', a)]
            lb = [re.sub(rf'^{lang}-', '', m) for m in re.findall(rf'\]\(({lang}-[A-Za-z-]+)\)', b)]
            if la != lb:
                errs.append(f'{lang}/{s}: liens internes {la} / {lb}')
            if re.findall(r'\]\((?!https?://|[a-z]{2}-)([^)]+)\)', b):
                errs.append(f'{lang}/{s}: lien relatif suspect')
            ua = sorted(x for x in re.findall(r'https?://[^\s)>]+', a) if '<' not in x)
            ub = sorted(x for x in re.findall(r'https?://[^\s)>]+', b) if '<' not in x)
            if ua != ub:
                errs.append(f'{lang}/{s}: URLs différentes')
            if re.findall(r'\{\{img:\w+\}\}', a) != re.findall(r'\{\{img:\w+\}\}', b):
                errs.append(f'{lang}/{s}: captures {{img:…}} différentes')
            for name in re.findall(r'\{\{img:(\w+)\}\}', b):
                if not find_image(lang, name):
                    errs.append(f'{lang}/{s}: capture introuvable « {name} »')
                if name not in CAPTIONS[lang]:
                    errs.append(f'{lang}/{s}: légende manquante « {name} »')
    return errs


def changelog_page(lang):
    data = json.load(open(os.path.join(ROOT, 'changelog.json'), encoding='utf-8'))
    out = [f'# {CHANGELOG_TITLE[lang]}', '', CHANGELOG_INTRO[lang], '']
    for entry in data[:CHANGELOG_MAX_VERSIONS]:
        items = (entry.get('items') or {}).get(lang) or (entry.get('items') or {}).get('en') or []
        if not items:
            continue
        out.append(f"## v{entry['version']}")
        out.append('')
        out += [f'- {x}' for x in items]
        out.append('')
    out += ['', f'🔗 [GitHub Releases](https://github.com/{REPO}/releases)', '']
    return '\n'.join(out)


def build(out_dir):
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir)
    pages_all = {lang: parse(lang) for lang, _, _ in LANGS}
    used = set()
    nav_pages = PAGES + ['Changelog']
    for lang, _, flag in LANGS:
        pg = pages_all[lang]
        titles = {s: pg[s][0] for s in PAGES}
        titles['Changelog'] = CHANGELOG_TITLE[lang]
        for slug in nav_pages:
            body = changelog_page(lang) if slug == 'Changelog' else pg[slug][1]

            def img(m):
                name = m.group(1)
                found = find_image(lang, name)
                if not found:
                    return ''
                ver, lg = found
                used.add((ver, lg, name))
                url = f'https://raw.githubusercontent.com/wiki/{REPO}/images/{ver}/{lg}/{name}.png'
                cap = CAPTIONS[lang].get(name, name)
                return f'\n\n[![{cap}]({url})]({url})\n\n'
            body = re.sub(r'\n*\{\{img:(\w+)\}\}\n*', img, body)
            body = re.sub(r'\n{3,}', '\n\n', body)
            nav = ' · '.join(f'**{titles[x]}**' if x == slug else f'[{titles[x]}]({lang}-{x})' for x in nav_pages)
            foot = ' · '.join(f'[{fl} {nm}]({c}-{slug})' for c, nm, fl in LANGS if c != lang)
            md = f'> {flag} {nav}\n\n{body.strip()}\n\n---\n<sub>🌍 {foot} · [{ALL_LANGS[lang]}](Home)</sub>\n'
            open(os.path.join(out_dir, f'{lang}-{slug}.md'), 'w', encoding='utf-8', newline='\n').write(md)
    rows = '\n'.join(
        f'| {fl} **[{nm}]({c}-Home)** | [{pages_all[c]["How-To"][0]}]({c}-How-To) · [{pages_all[c]["Installation"][0]}]({c}-Installation)'
        f' · [{CHANGELOG_TITLE[c]}]({c}-Changelog) |' for c, nm, fl in LANGS)
    home = ('<p align="center">\n  <img src="https://stellio-app.com/assets/logo-nom-stellio.png" alt="Stellio Logo" width="360">\n</p>\n\n'
            '<h3 align="center">The ultimate 3D file manager for makers and 3D printer owners</h3>\n\n'
            '<p align="center">Library · printers · spools · costs · AI, all local.</p>\n\n'
            '### 👇 Choose your language\n\n| Language | Start here |\n|---|---|\n' + rows
            + f'\n\n**[⬇️ Download](https://github.com/{REPO}/releases)** · **[▶ Online demo](https://demo.stellio-app.com)**'
              f' · **[🌐 stellio-app.com](https://stellio-app.com)** · **[💬 Discord](https://discord.gg/ySxpHvS6bd)**\n')
    open(os.path.join(out_dir, 'Home.md'), 'w', encoding='utf-8', newline='\n').write(home)
    side = ('### 🌍 Stellio\n\n' + '\n'.join(f'- {fl} [{nm}]({c}-Home)' for c, nm, fl in LANGS)
            + f'\n\n---\n[stellio-app.com](https://stellio-app.com) · [Releases](https://github.com/{REPO}/releases)'
              ' · [Discord](https://discord.gg/ySxpHvS6bd)\n')
    open(os.path.join(out_dir, '_Sidebar.md'), 'w', encoding='utf-8', newline='\n').write(side)
    for ver, lg, name in sorted(used):
        dst = os.path.join(out_dir, 'images', ver, lg)
        os.makedirs(dst, exist_ok=True)
        shutil.copyfile(os.path.join(IMG, ver, lg, f'{name}.png'), os.path.join(dst, f'{name}.png'))
    # contrôle des liens internes
    names = {os.path.basename(f)[:-3] for f in glob.glob(os.path.join(out_dir, '*.md'))}
    broken = []
    for f in glob.glob(os.path.join(out_dir, '*.md')):
        for m in re.findall(r'\]\(([A-Za-z-]+)\)', open(f, encoding='utf-8').read()):
            if m not in names:
                broken.append((os.path.basename(f), m))
    return broken, len(names), len(used)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--out')
    a = ap.parse_args()
    errs = check()
    for e in errs:
        print('ERREUR', e)
    if errs:
        sys.exit(1)
    if a.out:
        broken, n, ni = build(a.out)
        print(f'{n} pages, {ni} captures, liens cassés : {broken}')
        if broken:
            sys.exit(1)
    elif not a.check:
        ap.print_help()
    else:
        print('Structure des 8 langues OK')


if __name__ == '__main__':
    main()
