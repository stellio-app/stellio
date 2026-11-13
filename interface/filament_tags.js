/* Stellio — catalogue Open Filament Database et étiquettes OpenPrintTag dans l'inventaire manuel de filament (v1.0.8).
   Fichier autonome (textes en 8 langues intégrés) : ajoute un bouton « Catalogue & étiquettes » dans l'en-tête de l'inventaire manuel
   et, sur chaque bobine, l'export du tag (et l'écriture NFC dans l'application Android). Ne modifie pas script.js :
   il observe la grille #manual-grid. Pont Android : window.StellioAndroid.nfcRead() / nfcWrite(ndefB64),
   résultat par window.__stellioNfcResult(json). */
(function () {
'use strict';
const TXT = {"fr": {"n_ofd_title": "Catalogue Open Filament Database", "n_ofd_intro": "Cherchez une bobine (marque, matière, couleur) : Stellio la crée avec le poids, le diamètre et la densité déjà remplis.", "n_search": "Marque, matière ou couleur…", "n_go": "Chercher", "n_add": "Ajouter", "n_added": "Bobine ajoutée", "n_count": "bobines au catalogue", "n_update": "Mettre à jour le catalogue", "n_updated": "Catalogue à jour", "n_offline": "Catalogue inaccessible (Internet ?). Vous pouvez importer le fichier filaments.json.", "n_import_cat": "Importer filaments.json", "n_empty_cat": "Catalogue vide : cliquez sur « Mettre à jour le catalogue ».", "n_noresult": "Aucun résultat.", "n_credit": "Données : Open Filament Database (licence MIT)", "n_opt_title": "Étiquettes OpenPrintTag", "n_opt_intro": "Standard ouvert d'étiquettes NFC pour bobines. Importez un fichier de tag, ou lisez l'étiquette avec l'application Android ; exportez une bobine vers un fichier ou écrivez-la sur une étiquette.", "n_opt_import": "Importer un tag (.bin)", "n_opt_imported": "Bobine importée depuis l'étiquette", "n_opt_bad": "Fichier OpenPrintTag illisible", "n_nfc_read": "Lire une étiquette NFC", "n_nfc_write": "Écrire sur une étiquette", "n_nfc_wait": "Approchez l'étiquette du téléphone…", "n_nfc_done": "Étiquette écrite", "n_export": "Exporter le tag", "n_spools": "Vos bobines", "n_no_spools": "Aucune bobine manuelle.", "n_nfc_only": "La lecture et l'écriture NFC passent par l'application Android Stellio.", "n_nfc_err": "Opération NFC impossible", "n_nfc_read_ok": "Étiquette lue", "open": "Catalogue & étiquettes", "close": "Fermer", "tip_export": "Exporter le tag OpenPrintTag", "tip_write": "Écrire sur une étiquette NFC"}, "en": {"n_ofd_title": "Open Filament Database catalog", "n_ofd_intro": "Search for a spool (brand, material, colour): Stellio creates it with weight, diameter and density already filled in.", "n_search": "Brand, material or colour…", "n_go": "Search", "n_add": "Add", "n_added": "Spool added", "n_count": "spools in the catalog", "n_update": "Update the catalog", "n_updated": "Catalog up to date", "n_offline": "Catalog unreachable (Internet?). You can import the filaments.json file instead.", "n_import_cat": "Import filaments.json", "n_empty_cat": "Empty catalog: click “Update the catalog”.", "n_noresult": "No result.", "n_credit": "Data: Open Filament Database (MIT licence)", "n_opt_title": "OpenPrintTag tags", "n_opt_intro": "Open standard for NFC spool tags. Import a tag file, or read the tag with the Android app; export a spool to a file or write it onto a tag.", "n_opt_import": "Import a tag (.bin)", "n_opt_imported": "Spool imported from the tag", "n_opt_bad": "Unreadable OpenPrintTag file", "n_nfc_read": "Read an NFC tag", "n_nfc_write": "Write to a tag", "n_nfc_wait": "Hold the tag against the phone…", "n_nfc_done": "Tag written", "n_export": "Export tag", "n_spools": "Your spools", "n_no_spools": "No manual spools.", "n_nfc_only": "NFC reading and writing go through the Stellio Android app.", "n_nfc_err": "NFC operation failed", "n_nfc_read_ok": "Tag read", "open": "Catalog & tags", "close": "Close", "tip_export": "Export OpenPrintTag tag", "tip_write": "Write to an NFC tag"}, "de": {"n_ofd_title": "Open-Filament-Database-Katalog", "n_ofd_intro": "Spule suchen (Marke, Material, Farbe): Stellio legt sie mit Gewicht, Durchmesser und Dichte an.", "n_search": "Marke, Material oder Farbe…", "n_go": "Suchen", "n_add": "Hinzufügen", "n_added": "Spule hinzugefügt", "n_count": "Spulen im Katalog", "n_update": "Katalog aktualisieren", "n_updated": "Katalog aktuell", "n_offline": "Katalog nicht erreichbar (Internet?). Sie können stattdessen die Datei filaments.json importieren.", "n_import_cat": "filaments.json importieren", "n_empty_cat": "Katalog leer: Klicken Sie auf „Katalog aktualisieren“.", "n_noresult": "Kein Ergebnis.", "n_credit": "Daten: Open Filament Database (MIT-Lizenz)", "n_opt_title": "OpenPrintTag-Etiketten", "n_opt_intro": "Offener Standard für NFC-Spulenetiketten. Importieren Sie eine Tag-Datei oder lesen Sie das Etikett mit der Android-App; exportieren Sie eine Spule in eine Datei oder schreiben Sie sie auf ein Etikett.", "n_opt_import": "Tag importieren (.bin)", "n_opt_imported": "Spule vom Etikett importiert", "n_opt_bad": "OpenPrintTag-Datei nicht lesbar", "n_nfc_read": "NFC-Etikett lesen", "n_nfc_write": "Auf Etikett schreiben", "n_nfc_wait": "Etikett ans Telefon halten…", "n_nfc_done": "Etikett geschrieben", "n_export": "Tag exportieren", "n_spools": "Ihre Spulen", "n_no_spools": "Keine manuellen Spulen.", "n_nfc_only": "NFC-Lesen und -Schreiben läuft über die Stellio-Android-App.", "n_nfc_err": "NFC-Vorgang fehlgeschlagen", "n_nfc_read_ok": "Etikett gelesen", "open": "Katalog & Etiketten", "close": "Schließen", "tip_export": "OpenPrintTag-Tag exportieren", "tip_write": "Auf NFC-Etikett schreiben"}, "es": {"n_ofd_title": "Catálogo Open Filament Database", "n_ofd_intro": "Busque una bobina (marca, material, color): Stellio la crea con el peso, el diámetro y la densidad ya rellenados.", "n_search": "Marca, material o color…", "n_go": "Buscar", "n_add": "Añadir", "n_added": "Bobina añadida", "n_count": "bobinas en el catálogo", "n_update": "Actualizar el catálogo", "n_updated": "Catálogo actualizado", "n_offline": "Catálogo inaccesible (¿Internet?). Puede importar el archivo filaments.json.", "n_import_cat": "Importar filaments.json", "n_empty_cat": "Catálogo vacío: pulse «Actualizar el catálogo».", "n_noresult": "Sin resultados.", "n_credit": "Datos: Open Filament Database (licencia MIT)", "n_opt_title": "Etiquetas OpenPrintTag", "n_opt_intro": "Estándar abierto de etiquetas NFC para bobinas. Importe un archivo de etiqueta o lea la etiqueta con la aplicación Android; exporte una bobina a un archivo o escríbala en una etiqueta.", "n_opt_import": "Importar una etiqueta (.bin)", "n_opt_imported": "Bobina importada desde la etiqueta", "n_opt_bad": "Archivo OpenPrintTag ilegible", "n_nfc_read": "Leer una etiqueta NFC", "n_nfc_write": "Escribir en una etiqueta", "n_nfc_wait": "Acerque la etiqueta al teléfono…", "n_nfc_done": "Etiqueta escrita", "n_export": "Exportar la etiqueta", "n_spools": "Sus bobinas", "n_no_spools": "Ninguna bobina manual.", "n_nfc_only": "La lectura y escritura NFC se hacen con la aplicación Android de Stellio.", "n_nfc_err": "Operación NFC imposible", "n_nfc_read_ok": "Etiqueta leída", "open": "Catálogo y etiquetas", "close": "Cerrar", "tip_export": "Exportar la etiqueta OpenPrintTag", "tip_write": "Escribir en una etiqueta NFC"}, "pt": {"n_ofd_title": "Catálogo Open Filament Database", "n_ofd_intro": "Procure uma bobina (marca, material, cor): o Stellio cria-a com peso, diâmetro e densidade já preenchidos.", "n_search": "Marca, material ou cor…", "n_go": "Procurar", "n_add": "Adicionar", "n_added": "Bobina adicionada", "n_count": "bobinas no catálogo", "n_update": "Atualizar o catálogo", "n_updated": "Catálogo atualizado", "n_offline": "Catálogo inacessível (Internet?). Pode importar o ficheiro filaments.json.", "n_import_cat": "Importar filaments.json", "n_empty_cat": "Catálogo vazio: clique em «Atualizar o catálogo».", "n_noresult": "Sem resultados.", "n_credit": "Dados: Open Filament Database (licença MIT)", "n_opt_title": "Etiquetas OpenPrintTag", "n_opt_intro": "Padrão aberto de etiquetas NFC para bobinas. Importe um ficheiro de etiqueta ou leia a etiqueta com a aplicação Android; exporte uma bobina para um ficheiro ou escreva-a numa etiqueta.", "n_opt_import": "Importar uma etiqueta (.bin)", "n_opt_imported": "Bobina importada da etiqueta", "n_opt_bad": "Ficheiro OpenPrintTag ilegível", "n_nfc_read": "Ler uma etiqueta NFC", "n_nfc_write": "Escrever numa etiqueta", "n_nfc_wait": "Aproxime a etiqueta do telemóvel…", "n_nfc_done": "Etiqueta escrita", "n_export": "Exportar a etiqueta", "n_spools": "As suas bobinas", "n_no_spools": "Nenhuma bobina manual.", "n_nfc_only": "A leitura e escrita NFC passam pela aplicação Android do Stellio.", "n_nfc_err": "Operação NFC impossível", "n_nfc_read_ok": "Etiqueta lida", "open": "Catálogo e etiquetas", "close": "Fechar", "tip_export": "Exportar a etiqueta OpenPrintTag", "tip_write": "Escrever numa etiqueta NFC"}, "it": {"n_ofd_title": "Catalogo Open Filament Database", "n_ofd_intro": "Cerca una bobina (marca, materiale, colore): Stellio la crea con peso, diametro e densità già compilati.", "n_search": "Marca, materiale o colore…", "n_go": "Cerca", "n_add": "Aggiungi", "n_added": "Bobina aggiunta", "n_count": "bobine nel catalogo", "n_update": "Aggiorna il catalogo", "n_updated": "Catalogo aggiornato", "n_offline": "Catalogo non raggiungibile (Internet?). Puoi importare il file filaments.json.", "n_import_cat": "Importa filaments.json", "n_empty_cat": "Catalogo vuoto: fai clic su «Aggiorna il catalogo».", "n_noresult": "Nessun risultato.", "n_credit": "Dati: Open Filament Database (licenza MIT)", "n_opt_title": "Etichette OpenPrintTag", "n_opt_intro": "Standard aperto di etichette NFC per bobine. Importa un file di tag o leggi l'etichetta con l'app Android; esporta una bobina in un file o scrivila su un'etichetta.", "n_opt_import": "Importa un tag (.bin)", "n_opt_imported": "Bobina importata dall'etichetta", "n_opt_bad": "File OpenPrintTag illeggibile", "n_nfc_read": "Leggi un'etichetta NFC", "n_nfc_write": "Scrivi su un'etichetta", "n_nfc_wait": "Avvicina l'etichetta al telefono…", "n_nfc_done": "Etichetta scritta", "n_export": "Esporta il tag", "n_spools": "Le tue bobine", "n_no_spools": "Nessuna bobina manuale.", "n_nfc_only": "La lettura e scrittura NFC passano dall'app Android di Stellio.", "n_nfc_err": "Operazione NFC non riuscita", "n_nfc_read_ok": "Etichetta letta", "open": "Catalogo ed etichette", "close": "Chiudi", "tip_export": "Esporta l'etichetta OpenPrintTag", "tip_write": "Scrivi su un'etichetta NFC"}, "zh": {"n_ofd_title": "Open Filament Database 目录", "n_ofd_intro": "搜索料盘（品牌、材料、颜色）：Stellio 会自动填入重量、直径和密度来创建。", "n_search": "品牌、材料或颜色…", "n_go": "搜索", "n_add": "添加", "n_added": "已添加料盘", "n_count": "个料盘在目录中", "n_update": "更新目录", "n_updated": "目录已是最新", "n_offline": "无法访问目录（是否已联网？）。您可以改为导入 filaments.json 文件。", "n_import_cat": "导入 filaments.json", "n_empty_cat": "目录为空：请点击“更新目录”。", "n_noresult": "无结果。", "n_credit": "数据：Open Filament Database（MIT 许可）", "n_opt_title": "OpenPrintTag 标签", "n_opt_intro": "料盘 NFC 标签的开放标准。导入标签文件，或用 Android 应用读取标签；将料盘导出为文件或写入标签。", "n_opt_import": "导入标签 (.bin)", "n_opt_imported": "已从标签导入料盘", "n_opt_bad": "无法读取 OpenPrintTag 文件", "n_nfc_read": "读取 NFC 标签", "n_nfc_write": "写入标签", "n_nfc_wait": "请将标签靠近手机…", "n_nfc_done": "标签已写入", "n_export": "导出标签", "n_spools": "您的料盘", "n_no_spools": "没有手动料盘。", "n_nfc_only": "NFC 读写需通过 Stellio Android 应用。", "n_nfc_err": "NFC 操作失败", "n_nfc_read_ok": "标签已读取", "open": "目录与标签", "close": "关闭", "tip_export": "导出 OpenPrintTag 标签", "tip_write": "写入 NFC 标签"}, "ja": {"n_ofd_title": "Open Filament Database カタログ", "n_ofd_intro": "スプールを検索（ブランド・素材・色）：重量・直径・密度が入力済みの状態で Stellio が作成します。", "n_search": "ブランド、素材、色…", "n_go": "検索", "n_add": "追加", "n_added": "スプールを追加しました", "n_count": "件のスプールを収録", "n_update": "カタログを更新", "n_updated": "カタログは最新です", "n_offline": "カタログにアクセスできません（インターネット接続は？）。filaments.json を取り込むこともできます。", "n_import_cat": "filaments.json を取り込む", "n_empty_cat": "カタログが空です：「カタログを更新」をクリックしてください。", "n_noresult": "該当なし。", "n_credit": "データ：Open Filament Database（MIT ライセンス）", "n_opt_title": "OpenPrintTag タグ", "n_opt_intro": "スプール用 NFC タグのオープン標準。タグファイルを取り込むか、Android アプリでタグを読み取り、スプールをファイルに書き出すかタグに書き込みます。", "n_opt_import": "タグを取り込む (.bin)", "n_opt_imported": "タグからスプールを取り込みました", "n_opt_bad": "OpenPrintTag ファイルを読み取れません", "n_nfc_read": "NFC タグを読み取る", "n_nfc_write": "タグに書き込む", "n_nfc_wait": "タグをスマートフォンに近づけてください…", "n_nfc_done": "タグに書き込みました", "n_export": "タグを書き出す", "n_spools": "お持ちのスプール", "n_no_spools": "手動スプールはありません。", "n_nfc_only": "NFC の読み書きは Stellio Android アプリで行います。", "n_nfc_err": "NFC 操作に失敗しました", "n_nfc_read_ok": "タグを読み取りました", "open": "カタログとタグ", "close": "閉じる", "tip_export": "OpenPrintTag タグを書き出す", "tip_write": "NFC タグに書き込む"}};
function lang() {
    let l = '';
    try { l = document.documentElement.lang || localStorage.getItem('stellio-lang') || navigator.language || 'fr'; } catch (e) { l = 'fr'; }
    l = String(l).toLowerCase().slice(0, 2);
    return TXT[l] ? l : 'en';
}
const t = (k) => (TXT[lang()] && TXT[lang()][k]) || TXT.en[k] || k;
const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));

async function api(method, url, body) {
    const opt = {method, headers: {}};
    if (body !== undefined) { opt.headers['Content-Type'] = 'application/json'; opt.body = JSON.stringify(body); }
    const r = await fetch(url, opt);
    let j = {};
    try { j = await r.json(); } catch (e) { /* corps vide */ }
    if (!r.ok && j.success === undefined) j.success = false;
    return j;
}
async function postFile(url, file) {
    const fd = new FormData(); fd.append('file', file);
    const r = await fetch(url, {method: 'POST', body: fd});
    let j = {}; try { j = await r.json(); } catch (e) { /* corps vide */ }
    if (!r.ok && j.success === undefined) j.success = false;
    return j;
}
function toast(msg, bad) {
    if (typeof window.showToast === 'function') { try { window.showToast(msg, bad ? 'error' : 'success'); return; } catch (e) { /* repli */ } }
    const el = document.getElementById('ft-msg');
    if (el) { el.textContent = msg; el.style.color = bad ? 'var(--danger)' : 'var(--success)'; setTimeout(() => { el.textContent = ''; }, 4000); }
}
const refreshInventory = () => { if (typeof window.loadManualSpoolInventory === 'function') { try { window.loadManualSpoolInventory(); } catch (e) { /* ignoré */ } } };

// ── Pont NFC (application Android) ──
const nfcAvailable = () => { try { return !!(window.StellioAndroid && typeof window.StellioAndroid.nfcRead === 'function' && window.StellioAndroid.nfcSupported()); } catch (e) { return false; } };
function nfcCall(fn, arg) {
    return new Promise((resolve) => {
        const timer = setTimeout(() => { window.__stellioNfcResult = null; resolve({ok: false, error: 'timeout'}); }, 60000);
        window.__stellioNfcResult = (json) => {
            clearTimeout(timer); window.__stellioNfcResult = null;
            let r; try { r = typeof json === 'string' ? JSON.parse(json) : json; } catch (e) { r = {ok: false}; }
            resolve(r || {ok: false});
        };
        try { window.StellioAndroid[fn](arg || ''); } catch (e) { clearTimeout(timer); resolve({ok: false}); }
    });
}
async function writeNfc(spoolId) {
    const j = await api('GET', `/api/openprinttag/export/${spoolId}?format=json`);
    if (!j.ndef_b64) return toast(t('n_nfc_err'), true);
    toast(t('n_nfc_wait'));
    const r = await nfcCall('nfcWrite', j.ndef_b64);
    if (r.ok) toast(t('n_nfc_done')); else toast(t('n_nfc_err'), true);
}

// ── Fenêtre « Catalogue & étiquettes » ──
const swatch = (c) => {
    const v = String(c || '').replace('#', '');
    return `<span style="display:inline-block;width:1em;height:1em;border-radius:50%;vertical-align:-2px;margin-right:.4em;border:1px solid var(--border);background:${/^[0-9a-f]{6}$/i.test(v) ? '#' + v : 'transparent'}"></span>`;
};
let modal = null;
function buildModal() {
    modal = document.createElement('div');
    modal.id = 'modal-filament-tags';
    modal.className = 'modal hidden';
    modal.innerHTML = `<div class="modal-content" style="width:640px">
      <div class="modal-header"><h3><i class="fa-solid fa-tags"></i> <span id="ft-title"></span></h3>
        <button class="modal-close" type="button" id="ft-close" aria-label="">&times;</button></div>
      <div class="modal-body" id="ft-body"></div></div>`;
    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });
    modal.querySelector('#ft-close').onclick = closeModal;
}
function closeModal() { if (modal) modal.classList.add('hidden'); }
const btn = (cls, act, label, icon) => `<button type="button" class="btn ${cls} btn-sm" data-act="${act}">${icon ? `<i class="fa-solid ${icon}"></i> ` : ''}${esc(label)}</button>`;
const sub = (s) => `<p style="margin:0 0 10px;color:var(--text-secondary);font-size:calc(12.5px * var(--fs,1))">${esc(s)}</p>`;
const fileBtn = (id, label, accept, primary) => `<label class="btn ${primary ? 'btn-primary' : 'btn-ghost'} btn-sm" style="cursor:pointer;margin:0">${esc(label)}<input id="${id}" type="file" accept="${accept}" hidden></label>`;

async function openModal() {
    if (!modal) buildModal();
    modal.querySelector('#ft-title').textContent = t('open');
    modal.querySelector('#ft-close').setAttribute('aria-label', t('close'));
    modal.classList.remove('hidden');
    await renderModal();
}
async function renderModal() {
    const body = modal.querySelector('#ft-body');
    const st = await api('GET', '/api/ofd/status');
    const nfc = nfcAvailable();
    body.innerHTML = `
      <h4 style="margin:0 0 6px">${esc(t('n_ofd_title'))}</h4>${sub(t('n_ofd_intro'))}
      <div style="display:flex;gap:8px;margin-bottom:10px">
        <input id="ft-q" type="search" class="settings-input" style="flex:1;min-width:0" placeholder="${esc(t('n_search'))}">
        ${btn('btn-primary', 'go', t('n_go'))}</div>
      <div id="ft-res" style="display:flex;flex-direction:column;gap:6px;max-height:40vh;overflow:auto"></div>
      <p id="ft-count" style="margin:8px 0 6px;font-size:calc(12px * var(--fs,1));color:var(--text-muted)">${st.count ? esc(st.count + ' ' + t('n_count')) : esc(t('n_empty_cat'))}</p>
      <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
        ${btn('btn-ghost', 'update', t('n_update'), 'fa-rotate')}${fileBtn('ft-cat-file', t('n_import_cat'), '.json,application/json', false)}
        <a href="https://openfilamentdatabase.org" target="_blank" rel="noopener" style="font-size:calc(12px * var(--fs,1))">${esc(t('n_credit'))}</a></div>
      <hr style="border:0;border-top:1px solid var(--border);margin:16px 0">
      <h4 style="margin:0 0 6px">${esc(t('n_opt_title'))}</h4>${sub(t('n_opt_intro'))}
      <div style="display:flex;gap:8px;flex-wrap:wrap">${fileBtn('ft-opt-file', t('n_opt_import'), '.bin,application/octet-stream', true)}${nfc ? btn('btn-ghost', 'nfc-read', t('n_nfc_read'), 'fa-tower-broadcast') : ''}</div>
      ${nfc ? '' : sub(t('n_nfc_only')).replace('margin:0 0 10px', 'margin:8px 0 0')}
      <p id="ft-msg" style="margin:10px 0 0;min-height:1.2em;font-size:calc(12.5px * var(--fs,1))"></p>`;
    const res = body.querySelector('#ft-res');
    const search = async () => {
        const q = body.querySelector('#ft-q').value.trim();
        const d = await api('GET', '/api/ofd/search?limit=40&q=' + encodeURIComponent(q));
        const items = d.items || [];
        res.innerHTML = items.length ? items.map((e) => `
          <div data-ofd="${esc(e.id)}" style="display:flex;align-items:center;gap:8px;padding:8px 10px;border:1px solid var(--border);border-radius:8px;background:var(--bg-card)">
            <div style="flex:1;min-width:0">${swatch(e.color_hex || (e.color_hexes || '').split(',')[0])}<strong>${esc(e.name)}</strong>
              <div style="font-size:calc(12px * var(--fs,1));color:var(--text-muted)">${esc(e.manufacturer)} · ${esc(e.material)}${e.weight ? ' · ' + esc(e.weight) + ' g' : ''}${e.diameter ? ' · ' + esc(e.diameter) + ' mm' : ''}</div></div>
            ${btn('btn-primary', 'add', t('n_add'), 'fa-plus')}</div>`).join('')
          : `<p style="color:var(--text-muted);margin:4px 0">${esc(d.count ? t('n_noresult') : t('n_empty_cat'))}</p>`;
    };
    body.querySelector('#ft-q').onkeydown = (e) => { if (e.key === 'Enter') search(); };
    body.querySelector('#ft-cat-file').onchange = async (e) => {
        const f = e.target.files[0]; if (!f) return;
        const r = await postFile('/api/ofd/import-file', f);
        if (r.success) { toast(t('n_updated')); renderModal(); } else toast(t('n_offline'), true);
    };
    body.querySelector('#ft-opt-file').onchange = async (e) => {
        const f = e.target.files[0]; if (!f) return;
        const r = await postFile('/api/openprinttag/import', f);
        if (r.success) { toast(t('n_opt_imported')); refreshInventory(); } else toast(t('n_opt_bad'), true);
    };
    body.onclick = async (e) => {
        const b = e.target.closest('[data-act]'); if (!b) return;
        const act = b.dataset.act;
        if (act === 'go') return search();
        if (act === 'update') {
            toast('…');
            const r = await api('POST', '/api/ofd/refresh', {force: true});
            if (r.count) { toast(t('n_updated')); renderModal(); } else toast(t('n_offline'), true);
        }
        if (act === 'add') {
            const r = await api('POST', '/api/ofd/add', {ofd_id: b.closest('[data-ofd]').dataset.ofd});
            if (r.success) { toast(t('n_added')); refreshInventory(); } else toast(t('n_nfc_err'), true);
        }
        if (act === 'nfc-read') {
            toast(t('n_nfc_wait'));
            const r = await nfcCall('nfcRead');
            if (!r.ok || !r.payload_b64) return toast(t('n_nfc_err'), true);
            const j = await api('POST', '/api/openprinttag/import', {data_b64: r.payload_b64});
            if (j.success) { toast(t('n_nfc_read_ok')); refreshInventory(); } else toast(t('n_opt_bad'), true);
        }
    };
    if (st.count) search();
}

// ── Intégration dans l'inventaire manuel ──
function addHeaderButton() {
    const imp = document.getElementById('import-manual-spool-btn');
    if (!imp || document.getElementById('ft-open-btn')) return !!document.getElementById('ft-open-btn');
    const b = document.createElement('button');
    b.id = 'ft-open-btn'; b.type = 'button'; b.className = 'btn btn-ghost btn-sm';
    b.innerHTML = `<i class="fa-solid fa-tags"></i> <span id="ft-open-label"></span>`;
    b.querySelector('#ft-open-label').textContent = t('open');
    b.onclick = openModal;
    imp.insertAdjacentElement('afterend', b);
    return true;
}
function decorateCards() {
    const lab = document.getElementById('ft-open-label'); if (lab) lab.textContent = t('open');
    const nfc = nfcAvailable();
    document.querySelectorAll('#manual-grid .spool-card-actions').forEach((bar) => {
        if (bar.dataset.ftDone) return;
        const edit = bar.querySelector('[onclick*="openSpoolInventoryModal("]');
        const m = edit && /openSpoolInventoryModal\((\d+)\)/.exec(edit.getAttribute('onclick'));
        if (!m) return;
        bar.dataset.ftDone = '1';
        const id = m[1];
        const exp = document.createElement('button');
        exp.type = 'button'; exp.className = 'btn btn-ghost btn-sm'; exp.title = t('tip_export');
        exp.setAttribute('aria-label', t('tip_export')); exp.innerHTML = '<i class="fa-solid fa-tag"></i>';
        exp.onclick = (ev) => { ev.stopPropagation(); window.location.href = `/api/openprinttag/export/${id}`; };
        edit.insertAdjacentElement('afterend', exp);
        if (nfc) {
            const w = document.createElement('button');
            w.type = 'button'; w.className = 'btn btn-ghost btn-sm'; w.title = t('tip_write');
            w.setAttribute('aria-label', t('tip_write')); w.innerHTML = '<i class="fa-solid fa-tower-broadcast"></i>';
            w.onclick = (ev) => { ev.stopPropagation(); writeNfc(id); };
            exp.insertAdjacentElement('afterend', w);
        }
    });
}
function start() {
    addHeaderButton();
    const grid = document.getElementById('manual-grid');
    if (grid) new MutationObserver(decorateCards).observe(grid, {childList: true, subtree: true});
    decorateCards();
    document.addEventListener('languagechange', () => { const l = document.getElementById('ft-open-label'); if (l) l.textContent = t('open'); });
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
