## Stellio v1.2.1
<details>
<summary><b>🇫🇷 Français</b></summary>

✓ Plugins : l'installation directe d'un .zip non signé est possible après un avertissement explicite (responsabilité de l'utilisateur, jamais pour le catalogue) ; un plugin signé du catalogue ne reçoit plus que les services qu'il déclare (jamais de secrets, mots de passe ou jetons) et ne peut plus remplacer ceux de l'application  
✓ Base de données : nouvelle migration (index sur les étiquettes et l'historique d'impression, requêtes d'étiquettes ~2× plus rapides sur 200 000 lignes) ; une copie de sauvegarde est faite automatiquement avant toute migration (les 3 dernières sont conservées)  
✓ Modularisation : les bobines manuelles et l'affectation d'une bobine à un fichier quittent main.py pour modules/filament_spools.py (mêmes URL, mêmes réponses)  
✓ Qualité : test de non-régression des routes (aucune route ne peut disparaître sans alerte), tests de migration et de portée des plugins, benchmarks reproductibles (bench/run_bench.py, comparaison à une exécution précédente)  
✓ Exemples de plugins du SDK : « Séparer par couleur » (tenons/logements plus propres, une seule patte par pièce), « Découpe 3D » (plans de coupe, tenons, aimants, guide PDF, aperçu WebGL) et « Peinture filaments » (peindre un 3MF/STL avec les couleurs de votre stock, 3MF peint pour Bambu Studio / OrcaSlicer)  
</details>

<details>
<summary><b>🇬🇧 English</b></summary>

✓ Plugins: a non-signed .zip can be installed directly after an explicit warning (user's responsibility, never for the catalog); a signed catalog plugin now only receives the services it declares (never secrets, passwords or tokens) and can no longer replace the application's services  
✓ Database: new migration (indexes on tags and print history, tag queries ~2× faster on 200,000 rows); a backup copy is taken automatically before any migration (the last 3 are kept)  
✓ Modularization: manual spools and spool-to-file assignment moved from main.py to modules/filament_spools.py (same URLs, same responses)  
✓ Quality: route regression test (no route can disappear unnoticed), migration and plugin-scope tests, reproducible benchmarks (bench/run_bench.py, comparison with a previous run)  
✓ SDK plugin examples: “Split by color” (cleaner pegs/sockets, a single peg per piece), “3D cutter” (cut planes, pegs, magnets, PDF guide, WebGL preview) and “Filament painter” (paint a 3MF/STL with the colors of your stock, painted 3MF for Bambu Studio / OrcaSlicer)  
</details>

<details>
<summary><b>🇩🇪 Deutsch</b></summary>

✓ Plugins: eine nicht signierte .zip kann nach ausdrücklicher Warnung direkt installiert werden (Verantwortung des Nutzers, nie für den Katalog); ein signiertes Katalog-Plugin erhält nur noch die Dienste, die es deklariert (nie Geheimnisse, Passwörter oder Token) und kann Dienste der Anwendung nicht mehr ersetzen  
✓ Datenbank: neue Migration (Indizes für Tags und Druckverlauf, Tag-Abfragen bei 200 000 Zeilen ~2× schneller); vor jeder Migration wird automatisch eine Sicherungskopie angelegt (die letzten 3 bleiben erhalten)  
✓ Modularisierung: manuelle Spulen und die Zuordnung einer Spule zu einer Datei wandern von main.py nach modules/filament_spools.py (gleiche URLs, gleiche Antworten)  
✓ Qualität: Regressionstest der Routen (keine Route verschwindet unbemerkt), Migrations- und Plugin-Scope-Tests, reproduzierbare Benchmarks (bench/run_bench.py, Vergleich mit einem früheren Lauf)  
✓ SDK-Plugin-Beispiele: „Nach Farbe trennen“ (sauberere Zapfen/Aufnahmen, ein Zapfen pro Teil), „3D-Schnitt“ (Schnittebenen, Zapfen, Magnete, PDF-Anleitung, WebGL-Vorschau) und „Filament-Malen“ (3MF/STL mit den Farben Ihres Bestands bemalen, bemalte 3MF für Bambu Studio / OrcaSlicer)  
</details>

<details>
<summary><b>🇪🇸 Español</b></summary>

✓ Plugins: se puede instalar directamente un .zip sin firma tras una advertencia explícita (responsabilidad del usuario, nunca para el catálogo); un plugin firmado del catálogo solo recibe los servicios que declara (nunca secretos, contraseñas ni tokens) y ya no puede reemplazar los de la aplicación  
✓ Base de datos: nueva migración (índices en etiquetas e historial de impresión, consultas de etiquetas ~2× más rápidas con 200 000 filas); se hace una copia de seguridad automática antes de cualquier migración (se conservan las 3 últimas)  
✓ Modularización: las bobinas manuales y la asignación de una bobina a un archivo pasan de main.py a modules/filament_spools.py (mismas URL, mismas respuestas)  
✓ Calidad: prueba de regresión de rutas (ninguna ruta puede desaparecer sin aviso), pruebas de migración y alcance de plugins, benchmarks reproducibles (bench/run_bench.py, comparación con una ejecución anterior)  
✓ Ejemplos de plugins del SDK: «Separar por color» (espigas/alojamientos más limpios, una sola espiga por pieza), «Corte 3D» (planos de corte, espigas, imanes, guía PDF, vista WebGL) y «Pintura de filamentos» (pintar un 3MF/STL con los colores de tu stock, 3MF pintado para Bambu Studio / OrcaSlicer)  
</details>

<details>
<summary><b>🇵🇹 Português</b></summary>

✓ Plugins: é possível instalar diretamente um .zip não assinado após um aviso explícito (responsabilidade do utilizador, nunca para o catálogo); um plugin assinado do catálogo só recebe os serviços que declara (nunca segredos, palavras-passe ou tokens) e já não pode substituir os da aplicação  
✓ Base de dados: nova migração (índices nas etiquetas e no histórico de impressão, consultas de etiquetas ~2× mais rápidas com 200 000 linhas); é feita uma cópia de segurança automática antes de qualquer migração (as 3 últimas são mantidas)  
✓ Modularização: as bobinas manuais e a atribuição de uma bobina a um ficheiro passam de main.py para modules/filament_spools.py (mesmos URL, mesmas respostas)  
✓ Qualidade: teste de regressão das rotas (nenhuma rota desaparece sem aviso), testes de migração e de âmbito dos plugins, benchmarks reproduzíveis (bench/run_bench.py, comparação com uma execução anterior)  
✓ Exemplos de plugins do SDK: «Separar por cor» (pinos/encaixes mais limpos, um só pino por peça), «Corte 3D» (planos de corte, pinos, ímanes, guia PDF, pré-visualização WebGL) e «Pintura de filamentos» (pintar um 3MF/STL com as cores do seu stock, 3MF pintado para Bambu Studio / OrcaSlicer)  
</details>

<details>
<summary><b>🇮🇹 Italiano</b></summary>

✓ Plugin: è possibile installare direttamente un .zip non firmato dopo un avviso esplicito (responsabilità dell'utente, mai per il catalogo); un plugin firmato del catalogo riceve solo i servizi che dichiara (mai segreti, password o token) e non può più sostituire quelli dell'applicazione  
✓ Database: nuova migrazione (indici su etichette e cronologia di stampa, query delle etichette ~2× più veloci con 200 000 righe); prima di ogni migrazione viene eseguita una copia di sicurezza automatica (le ultime 3 vengono conservate)  
✓ Modularizzazione: le bobine manuali e l'assegnazione di una bobina a un file passano da main.py a modules/filament_spools.py (stessi URL, stesse risposte)  
✓ Qualità: test di regressione delle rotte (nessuna rotta può sparire senza avviso), test di migrazione e di ambito dei plugin, benchmark riproducibili (bench/run_bench.py, confronto con un'esecuzione precedente)  
✓ Esempi di plugin dell'SDK: «Separa per colore» (spinotti/alloggiamenti più puliti, un solo spinotto per pezzo), «Taglio 3D» (piani di taglio, spinotti, magneti, guida PDF, anteprima WebGL) e «Pittura filamenti» (dipingere un 3MF/STL con i colori del tuo stock, 3MF dipinto per Bambu Studio / OrcaSlicer)  
</details>

<details>
<summary><b>🇨🇳 中文</b></summary>

✓ 插件：显示明确警告后可直接安装未签名的 .zip（由用户自行负责，目录插件永不适用）；目录中的已签名插件现在只会获得其声明的服务（绝不包含密钥、密码或令牌），也不能再替换应用的服务  
✓ 数据库：新增迁移（为标签和打印历史建立索引，20 万行时标签查询约快 2 倍）；每次迁移前自动备份（保留最近 3 份）  
✓ 模块化：手动耗材盘及耗材盘与文件的关联从 main.py 移至 modules/filament_spools.py（URL 与响应不变）  
✓ 质量：路由回归测试（任何路由消失都会报警）、迁移与插件作用域测试、可复现的基准测试（bench/run_bench.py，可与先前结果比较）  
✓ SDK 插件示例：「按颜色拆分」（更干净的榫头/榫孔，每件只有一个榫头）、「3D 切割」（切割面、榫头、磁铁、PDF 指南、WebGL 预览）和「耗材上色」（用库存耗材的颜色给 3MF/STL 上色，生成适用于 Bambu Studio / OrcaSlicer 的 3MF）  
</details>

<details>
<summary><b>🇯🇵 日本語</b></summary>

✓ プラグイン：明示的な警告の後、署名のない .zip を直接インストールできます（ユーザーの責任。カタログには適用されません）。カタログの署名付きプラグインは宣言したサービスのみを受け取り（秘密情報・パスワード・トークンは対象外）、アプリのサービスを置き換えられなくなりました  
✓ データベース：新しいマイグレーション（タグと印刷履歴のインデックス。20 万行でタグ検索が約 2 倍高速）。マイグレーション前に自動でバックアップを作成します（直近 3 件を保持）  
✓ モジュール化：手動スプールとスプールのファイルへの割り当てを main.py から modules/filament_spools.py に移動（URL・応答は同一）  
✓ 品質：ルートの回帰テスト（ルートが黙って消えることはありません）、マイグレーションとプラグイン範囲のテスト、再現可能なベンチマーク（bench/run_bench.py、前回との比較）  
✓ SDK プラグイン例：「色で分割」（よりきれいなピン/ソケット、1 パーツ 1 ピン）、「3D カット」（切断面、ピン、マグネット、PDF ガイド、WebGL プレビュー）、「フィラメント塗装」（在庫の色で 3MF/STL を塗り、Bambu Studio / OrcaSlicer 用の 3MF を作成）  
</details>
