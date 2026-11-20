#!/usr/bin/env python3
"""Génère le wiki GitHub de Stellio (8 langues) à partir de docs/wiki/.

    python tools/build_wiki.py --check            contrôle la structure des 8 langues (liens, tableaux, commandes)
    python tools/build_wiki.py --out wiki-out     génère les pages Markdown + les images dans wiki-out/

Sources :
  docs/wiki/src/<langue>.md          14 pages par langue, séparées par des lignes « @@@ Page | Titre »
  docs/wiki/images/<langue>/<nom>.png   captures d'écran, une par langue (à défaut : docs/wiki/images/<nom>.png)
  changelog.json                     la page « Nouveautés » (Changelog) est générée à chaque fois

Dans les pages, une ligne « {{img:nom}} » est remplacée par la capture docs/wiki/images/<langue>/<nom>.png (à défaut, docs/wiki/images/<nom>.png).
Pour mettre une capture à jour, remplacez simplement le fichier (même nom).
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
         'Costs-and-Management', 'Remote-Access', 'Desktop-Edition', 'Server-Edition', 'Settings-and-Data', 'Troubleshooting', 'Plugins', 'Contributing']
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
    'fr': {'already-printed': '« Déjà imprimé » : imprimante, réglages, bobine', 'library-halo': 'Halo vert (réussi) et rouge (raté) sur les miniatures', 'printer-slicer': 'Un slicer par imprimante', 'android-update': "Mise à jour de l'application Android", 'dashboard': 'Le tableau de bord', 'library': 'La bibliothèque', 'viewer': 'La visionneuse 3D', 'projects': 'Les projets',
           'printers': 'Les imprimantes', 'filament': "L'inventaire de filament et le bloc « Pesée et prévision »",
           'stats': 'Les statistiques', 'management': "L'écran « Gestion » (devis clients)", 'settings': 'Les réglages'},
    'en': {'already-printed': '“Already printed”: printer, settings, spool', 'library-halo': 'Green (success) and red (failed) halo on thumbnails', 'printer-slicer': 'One slicer per printer', 'android-update': 'Android app update', 'dashboard': 'The dashboard', 'library': 'The library', 'viewer': 'The 3D viewer', 'projects': 'Projects',
           'printers': 'Printers', 'filament': 'The filament inventory and the "Weighing and forecast" block',
           'stats': 'Statistics', 'management': 'The "Management" screen (client quotes)', 'settings': 'Settings'},
    'de': {'already-printed': '„Schon gedruckt“: Drucker, Einstellungen, Spule', 'library-halo': 'Grüner (Erfolg) und roter (Fehlschlag) Schimmer um die Vorschau', 'printer-slicer': 'Ein Slicer pro Drucker', 'android-update': 'Update der Android-App', 'dashboard': 'Das Dashboard', 'library': 'Die Bibliothek', 'viewer': 'Der 3D-Viewer', 'projects': 'Projekte',
           'printers': 'Drucker', 'filament': 'Der Filamentbestand und der Block „Wiegen und Prognose"',
           'stats': 'Statistiken', 'management': 'Der Bildschirm „Verwaltung" (Kundenangebote)', 'settings': 'Einstellungen'},
    'es': {'already-printed': '«Ya impreso»: impresora, ajustes, bobina', 'library-halo': 'Halo verde (logrado) y rojo (fallido) en las miniaturas', 'printer-slicer': 'Un slicer por impresora', 'android-update': 'Actualización de la app Android', 'dashboard': 'El panel de control', 'library': 'La biblioteca', 'viewer': 'El visor 3D', 'projects': 'Proyectos',
           'printers': 'Impresoras', 'filament': 'El inventario de filamento y el bloque «Pesaje y previsión»',
           'stats': 'Estadísticas', 'management': 'La pantalla «Gestión» (presupuestos de clientes)', 'settings': 'Ajustes'},
    'pt': {'already-printed': '«Já impresso»: impressora, definições, bobina', 'library-halo': 'Halo verde (sucesso) e vermelho (falhou) nas miniaturas', 'printer-slicer': 'Um slicer por impressora', 'android-update': 'Atualização da app Android', 'dashboard': 'O painel', 'library': 'A biblioteca', 'viewer': 'O visualizador 3D', 'projects': 'Projetos',
           'printers': 'Impressoras', 'filament': 'O inventário de filamento e o bloco «Pesagem e previsão»',
           'stats': 'Estatísticas', 'management': 'O ecrã «Gestão» (orçamentos de clientes)', 'settings': 'Definições'},
    'it': {'already-printed': '«Già stampato»: stampante, impostazioni, bobina', 'library-halo': 'Alone verde (riuscita) e rosso (fallita) sulle miniature', 'printer-slicer': 'Uno slicer per stampante', 'android-update': "Aggiornamento dell'app Android", 'dashboard': 'La dashboard', 'library': 'La libreria', 'viewer': 'Il visualizzatore 3D', 'projects': 'Progetti',
           'printers': 'Stampanti', 'filament': "L'inventario dei filamenti e il blocco «Pesatura e previsione»",
           'stats': 'Statistiche', 'management': 'La schermata «Gestione» (preventivi clienti)', 'settings': 'Impostazioni'},
    'zh': {'already-printed': '“已打印”：打印机、设置、线材盘', 'library-halo': '缩略图上的绿色（成功）和红色（失败）光晕', 'printer-slicer': '每台打印机一个切片软件', 'android-update': 'Android 应用更新', 'dashboard': '仪表盘', 'library': '资料库', 'viewer': '3D 查看器', 'projects': '项目',
           'printers': '打印机', 'filament': '耗材库存和“耗材称重与预测”模块',
           'stats': '统计', 'management': '“管理”界面（客户报价）', 'settings': '设置'},
    'ja': {'already-printed': '「印刷済み」：プリンター・設定・スプール', 'library-halo': 'サムネイルの緑（成功）と赤（失敗）のハロー', 'printer-slicer': 'プリンターごとのスライサー', 'android-update': 'Android アプリの更新', 'dashboard': 'ダッシュボード', 'library': 'ライブラリ', 'viewer': '3D ビューアー', 'projects': 'プロジェクト',
           'printers': 'プリンター', 'filament': 'フィラメント在庫と「フィラメントの計量と予測」ブロック',
           'stats': '統計', 'management': '「管理」画面（顧客向け見積）', 'settings': '設定'},
}

# v1.1.2 : nouvelles captures (page « Déjà imprimés » avec croix au survol, plateaux/couleurs, barre latérale, menu téléphone)
CAPTIONS_V112 = {
    'fr': {'already-printed': '« Déjà imprimés » : la croix rouge apparaît au survol', 'already-printed-plates': 'Une bobine (ou plusieurs couleurs) par plateau', 'sidebar-panel': 'La barre latérale : rail et volet', 'mobile-drawer': 'Le menu sur téléphone (application Android)'},
    'en': {'already-printed': '“Already printed”: the red cross appears on hover', 'already-printed-plates': 'One spool (or several colors) per plate', 'sidebar-panel': 'The sidebar: rail and panel', 'mobile-drawer': 'The menu on a phone (Android app)'},
    'de': {'already-printed': '„Bereits gedruckt“: das rote Kreuz erscheint beim Überfahren', 'already-printed-plates': 'Eine Spule (oder mehrere Farben) pro Platte', 'sidebar-panel': 'Die Seitenleiste: Leiste und Panel', 'mobile-drawer': 'Das Menü am Smartphone (Android-App)'},
    'es': {'already-printed': '«Ya impresos»: la cruz roja aparece al pasar el ratón', 'already-printed-plates': 'Una bobina (o varios colores) por bandeja', 'sidebar-panel': 'La barra lateral: riel y panel', 'mobile-drawer': 'El menú en el móvil (app Android)'},
    'pt': {'already-printed': '«Já impressos»: a cruz vermelha aparece ao passar o rato', 'already-printed-plates': 'Uma bobina (ou várias cores) por placa', 'sidebar-panel': 'A barra lateral: régua e painel', 'mobile-drawer': 'O menu no telemóvel (app Android)'},
    'it': {'already-printed': '«Già stampati»: la croce rossa compare al passaggio del mouse', 'already-printed-plates': 'Una bobina (o più colori) per piatto', 'sidebar-panel': 'La barra laterale: colonna e pannello', 'mobile-drawer': 'Il menu su telefono (app Android)'},
    'zh': {'already-printed': '“已打印”：悬停时出现红色叉号', 'already-printed-plates': '每个盘一个耗材盘（或多种颜色）', 'sidebar-panel': '侧边栏：导轨与面板', 'mobile-drawer': '手机上的菜单（Android 应用）'},
    'ja': {'already-printed': '「印刷済み」：ホバーで赤い×が表示', 'already-printed-plates': 'プレートごとに1つのスプール（または複数の色）', 'sidebar-panel': 'サイドバー：レールとパネル', 'mobile-drawer': 'スマートフォンのメニュー（Android アプリ）'},
}
for _l, _c in CAPTIONS_V112.items():
    CAPTIONS[_l].update(_c)
# v1.1.4 : captures BigPrint
CAPTIONS_V114 = {
    'fr': {'bigprint': 'BigPrint : réglages en trois colonnes', 'bigprint-result': 'BigPrint : aperçu éclaté, filament et liste des pièces'},
    'en': {'bigprint': 'BigPrint: settings in three columns', 'bigprint-result': 'BigPrint: exploded preview, filament and piece list'},
    'de': {'bigprint': 'BigPrint: Einstellungen in drei Spalten', 'bigprint-result': 'BigPrint: Explosionsansicht, Filament und Teileliste'},
    'es': {'bigprint': 'BigPrint: ajustes en tres columnas', 'bigprint-result': 'BigPrint: vista explosionada, filamento y lista de piezas'},
    'pt': {'bigprint': 'BigPrint: definições em três colunas', 'bigprint-result': 'BigPrint: vista explodida, filamento e lista de peças'},
    'it': {'bigprint': 'BigPrint: impostazioni in tre colonne', 'bigprint-result': 'BigPrint: anteprima esplosa, filamento ed elenco dei pezzi'},
    'zh': {'bigprint': 'BigPrint：三栏设置', 'bigprint-result': 'BigPrint：分解预览、耗材与部件列表'},
    'ja': {'bigprint': 'BigPrint：3列の設定', 'bigprint-result': 'BigPrint：分解プレビュー・フィラメント・パーツ一覧'},
}
for _l, _c in CAPTIONS_V114.items():
    CAPTIONS[_l].update(_c)
# v1.1.5 : capture du planning
CAPTIONS_V115 = {
    'fr': {'planning': 'Planning de production : fin estimée par imprimante, capacité et alertes'},
    'en': {'planning': 'Production planning: end dates per printer, capacity and alerts'},
    'de': {'planning': 'Produktionsplanung: Enddaten je Drucker, Kapazität und Warnungen'},
    'es': {'planning': 'Planificación de producción: fechas de fin por impresora, capacidad y alertas'},
    'pt': {'planning': 'Planeamento de produção: datas de fim por impressora, capacidade e alertas'},
    'it': {'planning': 'Pianificazione della produzione: date di fine per stampante, capacità e avvisi'},
    'zh': {'planning': '生产计划：各打印机完成日期、产能与提醒'},
    'ja': {'planning': '生産計画：プリンター別の完了日・能力・警告'},
}
for _l, _c in CAPTIONS_V115.items():
    CAPTIONS[_l].update(_c)
# v1.1.6 : captures de la traçabilité
CAPTIONS_V116 = {
    'fr': {'trace': 'Traçabilité : meilleure combinaison version + profil par modèle', 'trace_versions': 'Versions du modèle : taux de réussite par version et par profil'},
    'en': {'trace': 'Traceability: best version + profile combination per model', 'trace_versions': 'Model versions: success rate per version and per profile'},
    'de': {'trace': 'Rückverfolgbarkeit: beste Kombination aus Version und Profil je Modell', 'trace_versions': 'Modellversionen: Erfolgsquote je Version und Profil'},
    'es': {'trace': 'Trazabilidad: mejor combinación de versión y perfil por modelo', 'trace_versions': 'Versiones del modelo: tasa de éxito por versión y perfil'},
    'pt': {'trace': 'Rastreabilidade: melhor combinação de versão e perfil por modelo', 'trace_versions': 'Versões do modelo: taxa de sucesso por versão e perfil'},
    'it': {'trace': 'Tracciabilità: migliore combinazione di versione e profilo per modello', 'trace_versions': 'Versioni del modello: tasso di successo per versione e profilo'},
    'zh': {'trace': '可追溯性：每个模型的最佳版本 + 配置组合', 'trace_versions': '模型版本：各版本与各配置的成功率'},
    'ja': {'trace': 'トレーサビリティ：モデルごとの最良のバージョン＋プロファイル', 'trace_versions': 'モデルのバージョン：バージョン・プロファイル別の成功率'},
}
for _l, _c in CAPTIONS_V116.items():
    CAPTIONS[_l].update(_c)
CHANGELOG_MAX_VERSIONS = 25


def parse(lang):
    text = open(os.path.join(SRC, f'{lang}.md'), encoding='utf-8').read()
    parts = re.split(r'^@@@ (\S+) \| (.+)$\n', text, flags=re.M)
    pages = {}
    for i in range(1, len(parts), 3):
        pages[parts[i]] = (parts[i + 1].strip(), parts[i + 2].strip('\n'))
    return pages


def find_image(lang, name):
    """Chemin de la capture « nom » dans la langue demandée (docs/wiki/images/<langue>/<nom>.png),
    à défaut la capture commune docs/wiki/images/<nom>.png ; None si aucune n'existe."""
    for path in (os.path.join(IMG, lang, f'{name}.png'), os.path.join(IMG, f'{name}.png')):
        if os.path.exists(path):
            return path
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
            if re.findall(r'\{\{img:[\w-]+\}\}', a) != re.findall(r'\{\{img:[\w-]+\}\}', b):
                errs.append(f'{lang}/{s}: captures {{img:…}} différentes')
            for name in re.findall(r'\{\{img:([\w-]+)\}\}', b):
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
                used.add((lang, name))
                url = f'https://raw.githubusercontent.com/wiki/{REPO}/images/{lang}/{name}.png'
                cap = CAPTIONS[lang].get(name, name)
                return f'\n\n[![{cap}]({url})]({url})\n\n'
            body = re.sub(r'\n*\{\{img:([\w-]+)\}\}\n*', img, body)
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
            + f'\n\n**[📖 Documentation](https://stellio-app.com/docs/)** · **[⬇️ Download](https://github.com/{REPO}/releases)** · **[▶ Online demo](https://demo.stellio-app.com)**'
              f' · **[🌐 stellio-app.com](https://stellio-app.com)** · **[💬 Discord](https://discord.gg/ySxpHvS6bd)**\n')
    open(os.path.join(out_dir, 'Home.md'), 'w', encoding='utf-8', newline='\n').write(home)
    side = ('### 🌍 Stellio\n\n' + '\n'.join(f'- {fl} [{nm}]({c}-Home)' for c, nm, fl in LANGS)
            + f'\n\n---\n[stellio-app.com](https://stellio-app.com) · [Releases](https://github.com/{REPO}/releases)'
              ' · [Discord](https://discord.gg/ySxpHvS6bd)\n')
    open(os.path.join(out_dir, '_Sidebar.md'), 'w', encoding='utf-8', newline='\n').write(side)
    for lang, name in sorted(used):
        dst = os.path.join(out_dir, 'images', lang)
        os.makedirs(dst, exist_ok=True)
        shutil.copyfile(find_image(lang, name), os.path.join(dst, f'{name}.png'))
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
