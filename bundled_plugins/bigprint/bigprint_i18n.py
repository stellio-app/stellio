"""Stellio — traduction des textes produits par le moteur BigPrint (v1.1.4)

Le moteur BigPrint (AGPL-3.0, dossier `bigprint/`) écrit ses messages en anglais. Pour ne pas modifier le moteur, Stellio traduit
à la frontière : réglages « Usage » (libellé et explication), résumé du calcul (remplissage, coupes, avertissements), journal,
et l'aperçu 3D (page HTML servie à l'interface). Langues : fr, en, de, es, pt, it, zh, ja ; toute autre langue, ou « en »,
laisse le texte d'origine. Un message inconnu est rendu tel quel : jamais d'erreur, jamais de texte perdu.
Le rapport `bigprint_report.md` écrit à côté des pièces reste en anglais (document de référence du moteur).
Module pur (aucune dépendance) : testé sans le moteur.
"""
import json
import re

_REQUIRED = ('app',)
_ROUTES = ()

LANGS = ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja')

# ── presets (libellé, explication) ────────────────────────────────────────
PRESETS = {
    'display': {
        'fr': ("Pièce d'exposition", "Le plus léger qui s'imprime proprement : les parois portent la forme, et 6 couches supérieures couvrent le remplissage clairsemé sans affaissement ni effet « oreiller »."),
        'de': ("Ausstellungsstück", "So leicht wie möglich bei sauberem Druck: Die Wände tragen die Form, und 6 Deckschichten überbrücken die dünne Füllung ohne Durchhängen oder Kissenbildung."),
        'es': ("Pieza de exposición", "Lo más ligero que se imprime limpiamente: las paredes sostienen la forma y 6 capas superiores cubren el relleno escaso sin hundirse ni formar «almohadillado»."),
        'pt': ("Peça de exposição", "O mais leve que imprime bem: as paredes sustentam a forma e 6 camadas superiores cobrem o preenchimento esparso sem ceder nem fazer «almofada»."),
        'it': ("Pezzo da esposizione", "Il più leggero che si stampa pulito: le pareti reggono la forma e 6 strati superiori coprono il riempimento rado senza cedimenti né effetto «cuscino»."),
        'zh': ("展示件", "在保证打印干净的前提下尽量轻：由外壁支撑形状，6 层顶层可跨过稀疏填充而不下陷、不起“枕头”。"),
        'ja': ("展示用", "きれいに印刷できる範囲で最も軽量：壁が形を支え、6層の天面が疎なインフィルをたるみや枕状の凹みなく覆います。"),
    },
    'wearable': {
        'fr': ("Porté / manipulé", "Résiste aux chocs et à la manipulation : la quatrième paroi apporte l'essentiel de la résistance aux impacts."),
        'de': ("Tragbar / handgehalten", "Hält Stößen und Handhabung stand: Die vierte Wand bringt den größten Teil der Schlagfestigkeit."),
        'es': ("Para llevar / manipular", "Resiste golpes y manipulación: la cuarta pared aporta la mayor parte de la resistencia a impactos."),
        'pt': ("Para vestir / manusear", "Resiste a pancadas e ao manuseamento: a quarta parede dá a maior parte da resistência ao impacto."),
        'it': ("Indossabile / maneggiato", "Resiste a urti e manipolazione: la quarta parete dà gran parte della resistenza agli impatti."),
        'zh': ("穿戴 / 手持", "能承受碰撞和日常使用：第四层外壁贡献了大部分抗冲击强度。"),
        'ja': ("装着・手持ち用", "衝撃や取り扱いに耐えます：4枚目の壁が耐衝撃性の大部分を担います。"),
    },
    'structural': {
        'fr': ("Structurel", "Supporte une charge : la résistance vient surtout des parois, donc on augmente les parois plus que le remplissage."),
        'de': ("Tragend", "Trägt Last: Die Festigkeit kommt vor allem von den Wänden, daher werden die Wände stärker erhöht als die Füllung."),
        'es': ("Estructural", "Soporta carga: la resistencia viene sobre todo de las paredes, así que se suben más las paredes que el relleno."),
        'pt': ("Estrutural", "Suporta carga: a resistência vem sobretudo das paredes, por isso aumentam-se mais as paredes do que o preenchimento."),
        'it': ("Strutturale", "Regge un carico: la resistenza viene soprattutto dalle pareti, quindi si aumentano più le pareti del riempimento."),
        'zh': ("结构件", "承受载荷：强度主要来自外壁，因此优先增加外壁层数而不是填充密度。"),
        'ja': ("構造用", "荷重を支えます：強度は主に壁から得られるため、インフィルより壁を増やします。"),
    },
}

# ── gabarits : clé -> {lang: gabarit} ({0}, {1}… = groupes capturés) ───────
T = {
    'hollow_word': {'fr': "creux", 'de': "hohl", 'es': "hueco", 'pt': "oco", 'it': "cavo", 'zh': "空心", 'ja': "中空"},
    'describe': {  # walls, pct, pattern, top, bottom
        'fr': "{0} parois, remplissage {2} {1}, {3} couches sup. / {4} inf.",
        'de': "{0} Wände, {2}-Füllung {1}, {3} Deck- / {4} Bodenschichten",
        'es': "{0} paredes, relleno {2} {1}, {3} capas sup. / {4} inf.",
        'pt': "{0} paredes, preenchimento {2} {1}, {3} camadas sup. / {4} inf.",
        'it': "{0} pareti, riempimento {2} {1}, {3} strati sup. / {4} inf.",
        'zh': "{0} 层外壁，{2} 填充 {1}，顶层 {3} / 底层 {4}",
        'ja': "壁{0}枚、{2}インフィル{1}、天面{3}層／底面{4}層",
    },
    'solid_fill': {'fr': "plein (100 %)", 'de': "massiv (100 %)", 'es': "macizo (100 %)", 'pt': "maciço (100 %)", 'it': "pieno (100 %)", 'zh': "实心 (100%)", 'ja': "中実 (100%)"},
    'solid_word': {'fr': "plein", 'de': "massiv", 'es': "macizo", 'pt': "maciço", 'it': "pieno", 'zh': "实心", 'ja': "中実"},
    'sparse_word': {'fr': "clairsemé", 'de': "dünn", 'es': "escaso", 'pt': "esparso", 'it': "rado", 'zh': "稀疏", 'ja': "疎"},
    'no_cuts': {'fr': "(aucune coupe nécessaire)", 'de': "(keine Schnitte nötig)", 'es': "(no hacen falta cortes)", 'pt': "(não são precisos cortes)", 'it': "(nessun taglio necessario)", 'zh': "（无需切割）", 'ja': "（切断不要）"},
    'basis_preset': {  # label, describe
        'fr': "Préréglage « {0} » : {1}.", 'de': "Voreinstellung „{0}“: {1}.", 'es': "Preajuste «{0}»: {1}.", 'pt': "Predefinição «{0}»: {1}.",
        'it': "Preimpostazione «{0}»: {1}.", 'zh': "预设“{0}”：{1}。", 'ja': "プリセット「{0}」：{1}。"},
    'basis_hollow_1': {
        'fr': "1 pièce creuse : coques de {1} mm ({2} parois remplissent la coque).", 'de': "1 hohles Teil: {1}-mm-Schalen ({2} Wände füllen die Schale).",
        'es': "1 pieza hueca: carcasas de {1} mm ({2} paredes llenan la carcasa).", 'pt': "1 peça oca: cascas de {1} mm ({2} paredes enchem a casca).",
        'it': "1 pezzo cavo: gusci da {1} mm ({2} pareti riempiono il guscio).", 'zh': "1 个空心件：{1} mm 壳体（{2} 层外壁填满壳体）。", 'ja': "中空パーツ1個：{1} mm のシェル（壁{2}枚でシェルを満たします）。"},
    'basis_hollow_n': {
        'fr': "{0} pièces creuses : coques de {1} mm ({2} parois remplissent la coque).", 'de': "{0} hohle Teile: {1}-mm-Schalen ({2} Wände füllen die Schale).",
        'es': "{0} piezas huecas: carcasas de {1} mm ({2} paredes llenan la carcasa).", 'pt': "{0} peças ocas: cascas de {1} mm ({2} paredes enchem a casca).",
        'it': "{0} pezzi cavi: gusci da {1} mm ({2} pareti riempiono il guscio).", 'zh': "{0} 个空心件：{1} mm 壳体（{2} 层外壁填满壳体）。", 'ja': "中空パーツ{0}個：{1} mm のシェル（壁{2}枚でシェルを満たします）。"},
    'basis_solid_1': {'fr': "1 pièce fine s'imprime pleine.", 'de': "1 dünnes Teil wird massiv gedruckt.", 'es': "1 pieza fina se imprime maciza.", 'pt': "1 peça fina imprime-se maciça.",
                      'it': "1 pezzo sottile si stampa pieno.", 'zh': "1 个薄件按实心打印。", 'ja': "薄いパーツ1個は中実で印刷します。"},
    'basis_solid_n': {'fr': "{0} pièces fines s'impriment pleines.", 'de': "{0} dünne Teile werden massiv gedruckt.", 'es': "{0} piezas finas se imprimen macizas.", 'pt': "{0} peças finas imprimem-se maciças.",
                      'it': "{0} pezzi sottili si stampano pieni.", 'zh': "{0} 个薄件按实心打印。", 'ja': "薄いパーツ{0}個は中実で印刷します。"},
    # journal
    'log_loading': {'fr': "Chargement de {0}", 'de': "Lade {0}", 'es': "Cargando {0}", 'pt': "A carregar {0}", 'it': "Caricamento di {0}", 'zh': "正在加载 {0}", 'ja': "{0} を読み込み中"},
    'log_damaged': {'fr': "Modèle abîmé ({0}) ; réparation automatique, {1}", 'de': "Beschädigtes Modell ({0}); automatische Reparatur, {1}", 'es': "Modelo dañado ({0}); reparación automática, {1}",
                    'pt': "Modelo danificado ({0}); reparação automática, {1}", 'it': "Modello danneggiato ({0}); riparazione automatica, {1}", 'zh': "模型有损坏（{0}）；自动修复，{1}", 'ja': "モデルに損傷があります（{0}）。自動修復中、{1}"},
    'log_repaired': {'fr': "Réparé : surface fermée de {0} triangles", 'de': "Repariert: geschlossene Oberfläche mit {0} Dreiecken", 'es': "Reparado: superficie cerrada de {0} triángulos",
                     'pt': "Reparado: superfície fechada com {0} triângulos", 'it': "Riparato: superficie chiusa di {0} triangoli", 'zh': "已修复：封闭表面，{0} 个三角形", 'ja': "修復完了：{0} 三角形の閉じた表面"},
    'log_scaled': {'fr': "Mis à l'échelle ×{0} → {1}", 'de': "Skaliert ×{0} → {1}", 'es': "Escalado ×{0} → {1}", 'pt': "Escalado ×{0} → {1}", 'it': "Scalato ×{0} → {1}", 'zh': "已缩放 ×{0} → {1}", 'ja': "×{0} に拡大 → {1}"},
    'log_smoothed': {'fr': "Lissé : {0} → {1} triangles (arêtes plus vives que {2}° conservées)", 'de': "Geglättet: {0} → {1} Dreiecke (Kanten schärfer als {2}° bleiben erhalten)",
                     'es': "Suavizado: {0} → {1} triángulos (se conservan aristas más vivas que {2}°)", 'pt': "Suavizado: {0} → {1} triângulos (arestas mais vivas que {2}° mantidas)",
                     'it': "Levigato: {0} → {1} triangoli (spigoli più vivi di {2}° mantenuti)", 'zh': "已平滑：{0} → {1} 个三角形（保留大于 {2}° 的锐边）", 'ja': "スムージング：{0} → {1} 三角形（{2}° より鋭い稜線は維持）"},
    'log_cuts': {'fr': "Coupes : {0}", 'de': "Schnitte: {0}", 'es': "Cortes: {0}", 'pt': "Cortes: {0}", 'it': "Tagli: {0}", 'zh': "切割：{0}", 'ja': "切断：{0}"},
    'log_hollowing': {'fr': "Évidement de {0} cellules (parois de {1} mm, collerettes de joint de {2} mm)", 'de': "Aushöhlen von {0} Zellen ({1}-mm-Wände, {2}-mm-Verbindungskragen)",
                      'es': "Vaciado de {0} celdas (paredes de {1} mm, collarines de unión de {2} mm)", 'pt': "A esvaziar {0} células (paredes de {1} mm, colares de junta de {2} mm)",
                      'it': "Svuotamento di {0} celle (pareti da {1} mm, collari di giunzione da {2} mm)", 'zh': "正在掏空 {0} 个单元（壁厚 {1} mm，接缝套环 {2} mm）", 'ja': "{0} セルを中空化（壁 {1} mm、接合カラー {2} mm）"},
    'log_interior': {'fr': "{0} cellule(s) intérieure(s) entièrement dans le creux : rien à imprimer", 'de': "{0} innere Zelle(n) liegen komplett im Hohlraum und müssen nicht gedruckt werden",
                     'es': "{0} celda(s) interior(es) caen por completo dentro del hueco y no se imprimen", 'pt': "{0} célula(s) interior(es) ficam totalmente dentro do oco e não se imprimem",
                     'it': "{0} cella/e interna/e cadono interamente nel cavo e non vanno stampate", 'zh': "{0} 个内部单元完全落在空腔内，无需打印", 'ja': "内部セル{0}個は空洞内に完全に収まり、印刷不要です"},
    'log_merged': {'fr': "{0} petit(s) fragment(s) fusionné(s) avec leurs voisins", 'de': "{0} kleine(s) Fragment(e) mit Nachbarn verschmolzen", 'es': "{0} fragmento(s) pequeño(s) fusionado(s) con sus vecinos",
                   'pt': "{0} fragmento(s) pequeno(s) fundido(s) com os vizinhos", 'it': "{0} piccolo/i frammento/i unito/i ai vicini", 'zh': "已将 {0} 个小碎片并入相邻部分", 'ja': "小さな破片{0}個を隣接部分に統合しました"},
    'log_pieces': {'fr': "{0} pièces, {1} joints", 'de': "{0} Teile, {1} Verbindungen", 'es': "{0} piezas, {1} uniones", 'pt': "{0} peças, {1} juntas", 'it': "{0} pezzi, {1} giunzioni", 'zh': "{0} 个零件，{1} 处接缝", 'ja': "パーツ{0}個、接合{1}か所"},
    'log_dowels': {'fr': "{0} goujons placés", 'de': "{0} Dübel gesetzt", 'es': "{0} pasadores colocados", 'pt': "{0} cavilhas colocadas", 'it': "{0} spinotti posizionati", 'zh': "已放置 {0} 个定位销", 'ja': "ダボ{0}本を配置"},
    'log_done': {'fr': "Terminé", 'de': "Fertig", 'es': "Hecho", 'pt': "Concluído", 'it': "Fatto", 'zh': "完成", 'ja': "完了"},
    # avertissements
    'w_contact': {'fr': "{0} : surface de contact ({1} mm²) trop petite pour un goujon — collage seul", 'de': "{0}: Kontaktfläche ({1} mm²) zu klein für einen Dübel – nur kleben",
                  'es': "{0}: contacto ({1} mm²) demasiado pequeño para un pasador — solo pegamento", 'pt': "{0}: contacto ({1} mm²) demasiado pequeno para uma cavilha — só cola",
                  'it': "{0}: contatto ({1} mm²) troppo piccolo per uno spinotto — solo colla", 'zh': "{0}：接触面积（{1} mm²）太小，放不下定位销——仅用胶粘", 'ja': "{0}：接触面（{1} mm²）が小さくダボを入れられません。接着のみ"},
    'w_thin': {'fr': "{0} : matière trop fine pour un goujon de {1} mm — collage seul", 'de': "{0}: Material zu dünn für einen {1}-mm-Dübel – nur kleben",
               'es': "{0}: material demasiado fino para un pasador de {1} mm — solo pegamento", 'pt': "{0}: material demasiado fino para uma cavilha de {1} mm — só cola",
               'it': "{0}: materiale troppo sottile per uno spinotto da {1} mm — solo colla", 'zh': "{0}：材料太薄，放不下 {1} mm 定位销——仅用胶粘", 'ja': "{0}：材料が薄く {1} mm のダボを入れられません。接着のみ"},
    'w_label': {'fr': "{0} : pas de place sur les faces de coupe pour un numéro", 'de': "{0}: kein Platz auf den Schnittflächen für eine Beschriftung",
                'es': "{0}: no hay espacio en las caras de corte para una etiqueta", 'pt': "{0}: sem espaço nas faces de corte para uma etiqueta",
                'it': "{0}: nessuno spazio sulle facce di taglio per un'etichetta", 'zh': "{0}：切割面上没有放置编号的空间", 'ja': "{0}：切断面に番号を入れる余地がありません"},
    'w_bed': {'fr': "{0} : {1} mm ne tient pas sur le plateau", 'de': "{0}: {1} mm passt nicht auf das Druckbett", 'es': "{0}: {1} mm no cabe en la cama", 'pt': "{0}: {1} mm não cabe na mesa",
              'it': "{0}: {1} mm non sta sul piatto", 'zh': "{0}：{1} mm 放不进打印平台", 'ja': "{0}：{1} mm はベッドに収まりません"},
    'w_touch': {'fr': "{0} : les surfaces se touchent sur quelques arêtes. Les slicers réparent cela à l'import, mais vérifiez ces pièces.",
                'de': "{0}: Flächen berühren sich an einigen Kanten. Slicer reparieren das beim Import, prüfen Sie diese Teile trotzdem.",
                'es': "{0}: las superficies se tocan en algunas aristas. Los slicers lo reparan al importar, pero revise estas piezas.",
                'pt': "{0}: as superfícies tocam-se em algumas arestas. Os slicers reparam isto ao importar, mas verifique estas peças.",
                'it': "{0}: le superfici si toccano lungo alcuni spigoli. Gli slicer lo riparano all'importazione, ma controlla questi pezzi.",
                'zh': "{0}：表面在少数边缘处相接。切片软件导入时会自动修复，但请检查这些零件。", 'ja': "{0}：数か所の稜線で面が接触しています。スライサーが読み込み時に修復しますが、これらのパーツを確認してください。"},
    # aperçu 3D
    'v_explode': {'fr': "Éclaté", 'de': "Explosion", 'es': "Explosionar", 'pt': "Explodir", 'it': "Esplodi", 'zh': "分解", 'ja': "分解"},
    'v_show_ids': {'fr': "Afficher les numéros", 'de': "Nummern anzeigen", 'es': "Mostrar números", 'pt': "Mostrar números", 'it': "Mostra numeri", 'zh': "显示编号", 'ja': "番号を表示"},
    'v_show_all': {'fr': "Tout afficher", 'de': "Alle anzeigen", 'es': "Mostrar todo", 'pt': "Mostrar tudo", 'it': "Mostra tutto", 'zh': "全部显示", 'ja': "すべて表示"},
    'v_print_size': {'fr': "Taille d'impression (mm)", 'de': "Druckgröße (mm)", 'es': "Tamaño de impresión (mm)", 'pt': "Tamanho de impressão (mm)", 'it': "Dimensioni di stampa (mm)", 'zh': "打印尺寸 (mm)", 'ja': "印刷サイズ (mm)"},
    'v_estimate': {'fr': "Estimation basée sur :", 'de': "Schätzung basiert auf:", 'es': "Estimación basada en:", 'pt': "Estimativa baseada em:", 'it': "Stima basata su:", 'zh': "估算依据：", 'ja': "見積もりの前提："},
    'v_pieces': {'fr': "pièces", 'de': "Teile", 'es': "piezas", 'pt': "peças", 'it': "pezzi", 'zh': "个零件", 'ja': "パーツ"},
    'v_touches': {'fr': "Touche :", 'de': "Berührt:", 'es': "Toca:", 'pt': "Toca:", 'it': "Tocca:", 'zh': "相邻：", 'ja': "接触："},
}

_NUM = r'([\d.,]+)'
_LOG = [
    (r'^Loading (.+)$', 'log_loading'),
    (r'^Damaged model \((.+?)\); repairing automatically, (.+)$', 'log_damaged'),
    (r'^Repaired: closed surface with ([\d,]+) triangles$', 'log_repaired'),
    (r'^Scaled x([\d.]+) -> (.+)$', 'log_scaled'),
    (r'^Smoothed: (\d+) -> (\d+) triangles \(edges sharper than (\S+) deg kept\)$', 'log_smoothed'),
    (r'^Hollowing (\d+) cells \((\S+) mm walls, (\S+) mm joint collars\)$', 'log_hollowing'),
    (r'^(\d+) interior cell\(s\) fall entirely inside the hollow and need no printing$', 'log_interior'),
    (r'^Merged (\d+) small fragment\(s\) into neighbours$', 'log_merged'),
    (r'^(\d+) pieces, (\d+) joints$', 'log_pieces'),
    (r'^(\d+) dowels placed$', 'log_dowels'),
    (r'^Done$', 'log_done'),
]
_WARN = [
    (r'^(\S+): contact \((\d+) mm\^2\) too small for a dowel - glue only$', 'w_contact'),
    (r'^(\S+): material too thin for a (\S+) mm dowel - glue only$', 'w_thin'),
    (r'^(\S+): no room on cut faces for a label$', 'w_label'),
    (r'^(\S+): (\d+x\d+x\d+) mm does not fit the bed$', 'w_bed'),
    (r'^(.+): surfaces touch along a few edges\. Slicers repair this on import, but check these pieces\.(?: .*)?$', 'w_touch'),
]
_DESC = re.compile(r'^(\d+) walls, (\S+) (\S+) infill, (\d+) top / (\d+) bottom layers$')
_FILL = re.compile(r'^(solid|sparse|hollow): (\d+) walls, (\S+)$')
_BASIS = [
    (re.compile(r'^(.+?) preset: (.+?)\.$'), 'basis_preset'),
    (re.compile(r'^(\d+) hollow pieces?: (\S+) mm shells \((\d+) walls fill the shell\)\.$'), 'hollow'),
    (re.compile(r'^(\d+) thin pieces? prints? solid\.$'), 'solid'),
]


def _lang(lang):
    lang = (lang or '').lower()[:2]
    return lang if lang in LANGS and lang != 'en' else ''


def _t(key, lang, *args):
    tpl = T[key].get(lang)
    return tpl.format(*args) if tpl else None


def _match(rules, text, lang):
    for pat, key in rules:
        m = re.match(pat, text)
        if m:
            out = _t(key, lang, *m.groups())
            if out:
                return out
    return None


def preset(key, lang, label, why):
    lang = _lang(lang)
    return PRESETS.get(key, {}).get(lang, (label, why)) if lang else (label, why)


def describe(text, lang):
    """« 3 walls, 8% gyroid infill, 6 top / 4 bottom layers » -> langue."""
    lang = _lang(lang)
    m = _DESC.match(text or '')
    if not lang or not m:
        return text
    return _t('describe', lang, *m.groups())


def log_line(text, lang):
    lang = _lang(lang)
    if not lang:
        return text
    text = str(text)
    if text.startswith('Cuts: '):
        return _t('log_cuts', lang, cuts(text[6:], lang))
    return _match(_LOG, text, lang) or text


def cuts(text, lang):
    lang = _lang(lang)
    return _t('no_cuts', lang) if lang and text == '(no cuts needed)' else text


def warning(text, lang):
    lang = _lang(lang)
    return (_match(_WARN, str(text), lang) or text) if lang else text


def fill(text, lang):
    """Colonne « remplissage » du résumé : « sparse: 3 walls, 8% » / « solid »."""
    lang = _lang(lang)
    if not lang:
        return text
    if text == 'solid':
        return _t('solid_word', lang)
    m = _FILL.match(text or '')
    if m:
        mode = {'solid': 'solid_word', 'sparse': 'sparse_word', 'hollow': 'hollow_word'}.get(m.group(1))
        word = _t(mode, lang) if mode else m.group(1)
        return {'fr': f"{word} : {m.group(2)} parois, {m.group(3)}", 'de': f"{word}: {m.group(2)} Wände, {m.group(3)}", 'es': f"{word}: {m.group(2)} paredes, {m.group(3)}",
                'pt': f"{word}: {m.group(2)} paredes, {m.group(3)}", 'it': f"{word}: {m.group(2)} pareti, {m.group(3)}", 'zh': f"{word}：{m.group(2)} 层外壁，{m.group(3)}",
                'ja': f"{word}：壁{m.group(2)}枚、{m.group(3)}"}[lang]
    return text


def basis(text, lang):
    """Phrase « Display piece preset: … hollow pieces … » -> langue (phrase par phrase, repli sur l'original)."""
    lang = _lang(lang)
    if not lang or not text:
        return text
    out = []
    # le libellé d'usage peut contenir « . » : on découpe sur « . » suivi d'un chiffre ou fin
    for part in re.split(r'(?<=\.)\s+(?=\d)', text.strip()):
        mm = None
        for rx, kind in _BASIS:
            mm = rx.match(part)
            if not mm:
                continue
            if kind == 'basis_preset':
                label, desc = mm.group(1), mm.group(2)
                key = next((k for k, v in PRESETS.items() if PRESETS_EN.get(k) == label), None)
                label2 = PRESETS[key][lang][0] if key else label
                out.append(_t('basis_preset', lang, label2, describe(desc, lang)))
            elif kind == 'hollow':
                n = int(mm.group(1))
                out.append(_t('basis_hollow_1' if n == 1 else 'basis_hollow_n', lang, n, mm.group(2), mm.group(3)))
            else:
                n = int(mm.group(1))
                out.append(_t('basis_solid_1' if n == 1 else 'basis_solid_n', lang, n))
            break
        if not mm:
            out.append(part)
    return re.sub(r'\.\.(?!\.)', '.', ' '.join(out))


PRESETS_EN = {'display': 'Display piece', 'wearable': 'Wearable / handled', 'structural': 'Structural'}


def summary(s, lang):
    """Traduit le résumé du moteur (copie) : coupes, base d'estimation, avertissements, remplissage de chaque pièce."""
    if not _lang(lang) or not isinstance(s, dict):
        return s
    s = dict(s)
    if 'cuts' in s:
        s['cuts'] = cuts(s['cuts'], lang)
    if 'basis' in s:
        s['basis'] = basis(s['basis'], lang)
    pr = s.get('preset')
    if isinstance(pr, dict):
        key = next((k for k, v in PRESETS_EN.items() if v == pr.get('label')), None)
        if key:
            s['preset'] = dict(pr, label=PRESETS[key][_lang(lang)][0], why=PRESETS[key][_lang(lang)][1])
    if 'warnings' in s:
        s['warnings'] = [warning(w, lang) for w in s['warnings']]
    if 'table' in s:
        s['table'] = [dict(r, fill=fill(r.get('fill', ''), lang)) for r in s['table']]
    return s


def job_log(job, lang):
    if not _lang(lang) or not isinstance(job, dict) or not isinstance(job.get('log'), list):
        return job
    job = dict(job)
    job['log'] = [log_line(x, lang) for x in job['log']]
    return job


def preview_html(html, lang):
    """Traduit les textes fixes de la page d'aperçu et la phrase « base d'estimation » embarquée dans ses données."""
    lang = _lang(lang)
    if not lang:
        return html
    h = html
    reps = [
        ('<span class="muted">Explode</span>', f'<span class="muted">{_t("v_explode", lang)}</span>'),
        ('id="tags" checked> Show IDs</label>', f'id="tags" checked> {_t("v_show_ids", lang)}</label>'),
        ('<button id="all">Show all</button>', f'<button id="all">{_t("v_show_all", lang)}</button>'),
        ('<th>Print size (mm)</th>', f'<th>{_t("v_print_size", lang)}</th>'),
        ('`Estimate based on: ${DATA.basis}`', '`' + _t('v_estimate', lang) + ' ${DATA.basis}`'),
        (' pieces · ~', f' {_t("v_pieces", lang)} · ~'),
        ('\\nTouches: ', f'\\n{_t("v_touches", lang)} '),
        ('<br>Touches: ', f'<br>{_t("v_touches", lang)} '),
        ('<html lang="en">', f'<html lang="{lang}">'),
    ]
    for a, b in reps:
        h = h.replace(a, b, 1)
    # données JSON embarquées : base d'estimation et libellé de remplissage de chaque pièce
    def _json_str_sub(src, fn):
        def repl(m):
            try:
                val = json.loads('"' + m.group(2) + '"')
            except ValueError:
                return m.group(0)
            new = fn(val)
            return m.group(1) + json.dumps(new, ensure_ascii=False)[1:-1].replace('</', '<\\/')
        return repl
    h = re.sub(r'("basis":\s*")((?:[^"\\]|\\.)*)(?=")', lambda m: _json_str_sub(None, lambda v: basis(v, lang))(m), h, count=1)
    h = re.sub(r'("fill":\s*")((?:[^"\\]|\\.)*)(?=")', lambda m: _json_str_sub(None, lambda v: _fill_piece(v, lang))(m), h)
    return h


def _fill_piece(text, lang):
    m = re.match(r'^(\d+) walls, (\S+) (\S+)$', text)
    if m:
        return describe_short(m, lang)
    return text.replace('solid (100%)', _t('solid_fill', lang)) if text.startswith('solid') else text


def describe_short(m, lang):
    return {'fr': f"{m.group(1)} parois, {m.group(3)} {m.group(2)}", 'de': f"{m.group(1)} Wände, {m.group(3)} {m.group(2)}", 'es': f"{m.group(1)} paredes, {m.group(3)} {m.group(2)}",
            'pt': f"{m.group(1)} paredes, {m.group(3)} {m.group(2)}", 'it': f"{m.group(1)} pareti, {m.group(3)} {m.group(2)}", 'zh': f"{m.group(1)} 层外壁，{m.group(3)} {m.group(2)}",
            'ja': f"壁{m.group(1)}枚、{m.group(3)} {m.group(2)}"}[lang]


def init(ns, routes=True):
    """Module sans route : n'expose que des fonctions pures (schéma commun des modules)."""
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"bigprint_i18n.init : services manquants : {missing}")
    return {}
