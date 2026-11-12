/* Stellio — écran « Gestion » (v1.0.6) : devis clients en ligne, export comptable ZIP, stock de pièces. Répartition des imprimantes,
   résumé périodique, prévision de filament et partage de profils sont montés dans leurs pages (À imprimer bientôt, Notifications push, Inventaire filament, Slicer).
   Fichier autonome : ses textes (8 langues) sont ici, il ne dépend que de fetch() (le CSRF est ajouté par script.js). */
(function () {
'use strict';
const TXT = {"fr": {"title": "Gestion", "err": "Action impossible, réessayez.", "save": "Enregistrer", "saved": "Enregistré", "t_quotes": "Devis clients", "t_acc": "Comptabilité", "t_stock": "Stock de pièces", "t_disp": "Répartition", "t_digest": "Résumé", "t_fil": "Filament", "t_prof": "Profils", "q_intro": "Envoyez un lien à votre client : il consulte le devis, l'accepte ou le refuse en ligne. L'acceptation crée la tâche d'impression et vous prévient. Stellio ne traite aucun paiement.", "q_none": "Aucun devis pour le moment.", "q_create": "Créer le lien", "q_copy": "Copier le lien", "q_copied": "Lien copié", "q_revoke": "Révoquer", "st_draft": "Brouillon", "st_sent": "Envoyé", "st_accepted": "Accepté", "st_refused": "Refusé", "q_by": "par", "pay_title": "Acompte : informations affichées au client après acceptation", "pay_info": "Texte (IBAN, référence…)", "pay_link": "Lien de paiement (https://…)", "a_intro": "Un fichier ZIP pour votre comptable : CSV des documents, PDF des factures et récapitulatif des totaux par mois.", "a_month": "Mois", "a_quotes": "Inclure les devis", "a_download": "Télécharger le ZIP", "a_saved": "Fichier enregistré : ", "s_intro": "Suivez vos pièces finies. Sous le seuil, Stellio vous prévient et peut lancer le réassort.", "s_none": "Aucune pièce en stock suivie.", "s_name": "Pièce", "s_sku": "Référence", "s_mat": "Matière", "s_qty": "Stock", "s_min": "Seuil", "s_reorder": "Réassort (qté)", "s_auto": "Réassort automatique", "s_incoming": "en cours", "s_add": "Ajouter la pièce", "s_restock": "Réassort", "s_restocked": "Tâche de réassort créée", "s_delete": "Supprimer", "s_confirm": "Supprimer cette pièce ?", "d_intro": "Stellio propose l'imprimante la plus adaptée à chaque tâche en attente (libre, matière chargée, file d'attente). Il assigne seulement : il ne lance jamais d'impression.", "d_analyze": "Analyser", "d_apply": "Tout appliquer", "d_apply1": "Appliquer", "d_none": "Aucune tâche en attente.", "d_best": "Imprimante conseillée", "d_cur": "actuelle", "d_no_printer": "Aucune imprimante disponible", "r_idle": "libre", "r_busy": "occupée", "r_material_loaded": "matière chargée", "r_queue": "file d'attente", "w_material_change": "changer la matière", "w_not_enough_filament": "filament insuffisant", "d_applied": "tâche(s) réassignée(s)", "g_intro": "Un résumé par notification (et push si activé) : tâches terminées, retards, énergie, bobines, factures, stock.", "g_enable": "Activer le résumé", "g_freq": "Fréquence", "g_daily": "Quotidien", "g_weekly": "Hebdomadaire", "g_hour": "Heure", "g_weekday": "Jour", "g_preview": "Aperçu", "g_send": "Envoyer maintenant", "g_sent": "Résumé envoyé", "f_intro": "Poids restant des bobines TigerTag (relevé automatique) et pesées manuelles. Stellio en déduit la consommation par jour et la date de rupture.", "f_sync": "Relire TigerTag", "f_none": "Pas encore de pesée : utilisez TigerTag ou pesez une bobine.", "f_name": "Bobine", "f_remaining": "Restant (g)", "f_rate": "g / jour", "f_days": "Jours restants", "f_empty": "Rupture vers", "f_weigh": "Peser une bobine manuelle", "f_spool": "Bobine", "f_gross": "Poids total (g)", "f_tare": "Tare : bobine vide (g)", "f_save": "Enregistrer la pesée", "f_synced": "relevé(s) enregistré(s)", "p_intro": "Envoyez un profil de slicer à une autre instance Stellio appairée, ou téléchargez le fichier d'origine.", "p_none": "Aucun profil importé.", "p_instance": "Instance", "p_send": "Envoyer", "p_download": "Télécharger", "p_sent": "Profil envoyé", "p_exists": "Déjà présent sur l'autre instance", "p_no_inst": "Aucune instance appairée (Réglages → Instances distantes).", "h_prof": "Partage de profils de slicer", "h_disp": "Répartition des imprimantes", "h_digest": "Résumé périodique", "h_fil": "Pesée et prévision de filament", "q_need_remote": "Un lien de devis doit être accessible depuis Internet pour que votre client puisse l'ouvrir. Activez l'accès à distance pour créer des liens externes.", "q_remote_enable": "Activer l'accès à distance", "q_remote_wait": "Connexion en cours… cela peut prendre une minute.", "q_remote_refresh": "Actualiser", "q_remote_quick": "Adresse temporaire : elle change à chaque redémarrage de l'accès à distance et les liens déjà envoyés ne fonctionneront plus. Pour un lien durable, configurez une adresse fixe ou personnalisée dans Paramètres › Accès à distance.", "q_link_paused": "Lien en pause : l'accès à distance n'est pas actif."}, "en": {"title": "Management", "err": "Could not complete, please retry.", "save": "Save", "saved": "Saved", "t_quotes": "Customer quotes", "t_acc": "Accounting", "t_stock": "Parts stock", "t_disp": "Dispatch", "t_digest": "Summary", "t_fil": "Filament", "t_prof": "Profiles", "q_intro": "Send a link to your customer: they read the quote and accept or decline it online. Acceptance creates the print job and notifies you. Stellio does not process any payment.", "q_none": "No quotes yet.", "q_create": "Create link", "q_copy": "Copy link", "q_copied": "Link copied", "q_revoke": "Revoke", "st_draft": "Draft", "st_sent": "Sent", "st_accepted": "Accepted", "st_refused": "Declined", "q_by": "by", "pay_title": "Deposit: details shown to the customer after acceptance", "pay_info": "Text (IBAN, reference…)", "pay_link": "Payment link (https://…)", "a_intro": "One ZIP file for your accountant: document CSV, invoice PDFs and a monthly totals summary.", "a_month": "Month", "a_quotes": "Include quotes", "a_download": "Download the ZIP", "a_saved": "File saved: ", "s_intro": "Track your finished parts. Below the threshold, Stellio warns you and can start a restock.", "s_none": "No tracked parts yet.", "s_name": "Part", "s_sku": "SKU", "s_mat": "Material", "s_qty": "Stock", "s_min": "Threshold", "s_reorder": "Restock (qty)", "s_auto": "Automatic restock", "s_incoming": "in progress", "s_add": "Add part", "s_restock": "Restock", "s_restocked": "Restock job created", "s_delete": "Delete", "s_confirm": "Delete this part?", "d_intro": "Stellio suggests the best printer for each waiting job (free, material loaded, queue). It only assigns: it never starts a print.", "d_analyze": "Analyze", "d_apply": "Apply all", "d_apply1": "Apply", "d_none": "No waiting jobs.", "d_best": "Suggested printer", "d_cur": "current", "d_no_printer": "No printer available", "r_idle": "free", "r_busy": "busy", "r_material_loaded": "material loaded", "r_queue": "queue", "w_material_change": "change material", "w_not_enough_filament": "not enough filament", "d_applied": "job(s) reassigned", "g_intro": "A summary by notification (and push if enabled): finished jobs, delays, energy, spools, invoices, stock.", "g_enable": "Enable the summary", "g_freq": "Frequency", "g_daily": "Daily", "g_weekly": "Weekly", "g_hour": "Hour", "g_weekday": "Day", "g_preview": "Preview", "g_send": "Send now", "g_sent": "Summary sent", "f_intro": "Remaining weight of TigerTag spools (automatic) and manual weighings. Stellio derives daily use and the run-out date.", "f_sync": "Read TigerTag again", "f_none": "No weighings yet: use TigerTag or weigh a spool.", "f_name": "Spool", "f_remaining": "Remaining (g)", "f_rate": "g / day", "f_days": "Days left", "f_empty": "Runs out around", "f_weigh": "Weigh a manual spool", "f_spool": "Spool", "f_gross": "Total weight (g)", "f_tare": "Tare: empty spool (g)", "f_save": "Save weighing", "f_synced": "reading(s) recorded", "p_intro": "Send a slicer profile to another paired Stellio instance, or download the original file.", "p_none": "No imported profiles.", "p_instance": "Instance", "p_send": "Send", "p_download": "Download", "p_sent": "Profile sent", "p_exists": "Already on the other instance", "p_no_inst": "No paired instance (Settings → Remote instances).", "h_prof": "Slicer profile sharing", "h_disp": "Printer dispatch", "h_digest": "Periodic summary", "h_fil": "Filament weighing and forecast", "q_need_remote": "A quote link must be reachable from the Internet so your customer can open it. Turn on remote access to create external links.", "q_remote_enable": "Turn on remote access", "q_remote_wait": "Connecting… this can take a minute.", "q_remote_refresh": "Refresh", "q_remote_quick": "Temporary address: it changes every time remote access restarts and links already sent will stop working. For a lasting link, set up a fixed or custom address in Settings › Remote access.", "q_link_paused": "Link paused: remote access is not active."}, "de": {"title": "Verwaltung", "err": "Nicht möglich, bitte erneut versuchen.", "save": "Speichern", "saved": "Gespeichert", "t_quotes": "Kundenangebote", "t_acc": "Buchhaltung", "t_stock": "Teilelager", "t_disp": "Verteilung", "t_digest": "Zusammenfassung", "t_fil": "Filament", "t_prof": "Profile", "q_intro": "Senden Sie Ihrem Kunden einen Link: Er sieht das Angebot und nimmt es online an oder lehnt es ab. Die Annahme erstellt den Druckauftrag und benachrichtigt Sie. Stellio wickelt keine Zahlung ab.", "q_none": "Noch keine Angebote.", "q_create": "Link erstellen", "q_copy": "Link kopieren", "q_copied": "Link kopiert", "q_revoke": "Widerrufen", "st_draft": "Entwurf", "st_sent": "Gesendet", "st_accepted": "Angenommen", "st_refused": "Abgelehnt", "q_by": "von", "pay_title": "Anzahlung: Angaben, die dem Kunden nach der Annahme angezeigt werden", "pay_info": "Text (IBAN, Referenz …)", "pay_link": "Zahlungslink (https://…)", "a_intro": "Eine ZIP-Datei für Ihren Steuerberater: CSV der Belege, PDF der Rechnungen und Monatssummen.", "a_month": "Monat", "a_quotes": "Angebote einschließen", "a_download": "ZIP herunterladen", "a_saved": "Datei gespeichert: ", "s_intro": "Behalten Sie fertige Teile im Blick. Unter dem Schwellenwert warnt Stellio und kann Nachschub starten.", "s_none": "Noch keine Teile erfasst.", "s_name": "Teil", "s_sku": "Artikelnr.", "s_mat": "Material", "s_qty": "Bestand", "s_min": "Schwelle", "s_reorder": "Nachschub (Menge)", "s_auto": "Automatischer Nachschub", "s_incoming": "in Arbeit", "s_add": "Teil hinzufügen", "s_restock": "Nachschub", "s_restocked": "Nachschub-Auftrag erstellt", "s_delete": "Löschen", "s_confirm": "Dieses Teil löschen?", "d_intro": "Stellio schlägt für jeden wartenden Auftrag den besten Drucker vor (frei, Material geladen, Warteschlange). Er weist nur zu: Er startet nie einen Druck.", "d_analyze": "Analysieren", "d_apply": "Alle anwenden", "d_apply1": "Anwenden", "d_none": "Keine wartenden Aufträge.", "d_best": "Empfohlener Drucker", "d_cur": "aktuell", "d_no_printer": "Kein Drucker verfügbar", "r_idle": "frei", "r_busy": "belegt", "r_material_loaded": "Material geladen", "r_queue": "Warteschlange", "w_material_change": "Material wechseln", "w_not_enough_filament": "Filament reicht nicht", "d_applied": "Auftrag/Aufträge neu zugewiesen", "g_intro": "Eine Zusammenfassung per Benachrichtigung (und Push, falls aktiv): fertige Aufträge, Verzug, Energie, Spulen, Rechnungen, Bestand.", "g_enable": "Zusammenfassung aktivieren", "g_freq": "Häufigkeit", "g_daily": "Täglich", "g_weekly": "Wöchentlich", "g_hour": "Uhrzeit", "g_weekday": "Tag", "g_preview": "Vorschau", "g_send": "Jetzt senden", "g_sent": "Zusammenfassung gesendet", "f_intro": "Restgewicht der TigerTag-Spulen (automatisch) und manuelle Wiegungen. Stellio berechnet daraus den Tagesverbrauch und das Ende des Vorrats.", "f_sync": "TigerTag neu lesen", "f_none": "Noch keine Wiegungen: TigerTag nutzen oder eine Spule wiegen.", "f_name": "Spule", "f_remaining": "Rest (g)", "f_rate": "g / Tag", "f_days": "Verbleibende Tage", "f_empty": "Leer etwa am", "f_weigh": "Manuelle Spule wiegen", "f_spool": "Spule", "f_gross": "Gesamtgewicht (g)", "f_tare": "Tara: leere Spule (g)", "f_save": "Wiegung speichern", "f_synced": "Messung(en) gespeichert", "p_intro": "Senden Sie ein Slicer-Profil an eine andere gekoppelte Stellio-Instanz oder laden Sie die Originaldatei herunter.", "p_none": "Keine importierten Profile.", "p_instance": "Instanz", "p_send": "Senden", "p_download": "Herunterladen", "p_sent": "Profil gesendet", "p_exists": "Auf der anderen Instanz schon vorhanden", "p_no_inst": "Keine gekoppelte Instanz (Einstellungen → Remote-Instanzen).", "h_prof": "Slicer-Profile teilen", "h_disp": "Druckerverteilung", "h_digest": "Regelmäßige Zusammenfassung", "h_fil": "Filament wiegen und Prognose", "q_need_remote": "Ein Angebotslink muss aus dem Internet erreichbar sein, damit Ihr Kunde ihn öffnen kann. Aktivieren Sie den Fernzugriff, um externe Links zu erstellen.", "q_remote_enable": "Fernzugriff aktivieren", "q_remote_wait": "Verbindung wird aufgebaut … das kann eine Minute dauern.", "q_remote_refresh": "Aktualisieren", "q_remote_quick": "Temporäre Adresse: Sie ändert sich bei jedem Neustart des Fernzugriffs, bereits versendete Links funktionieren dann nicht mehr. Für einen dauerhaften Link richten Sie unter Einstellungen › Fernzugriff eine feste oder eigene Adresse ein.", "q_link_paused": "Link pausiert: Der Fernzugriff ist nicht aktiv."}, "es": {"title": "Gestión", "err": "No se pudo completar, inténtelo de nuevo.", "save": "Guardar", "saved": "Guardado", "t_quotes": "Presupuestos de clientes", "t_acc": "Contabilidad", "t_stock": "Stock de piezas", "t_disp": "Reparto", "t_digest": "Resumen", "t_fil": "Filamento", "t_prof": "Perfiles", "q_intro": "Envíe un enlace a su cliente: consulta el presupuesto y lo acepta o rechaza en línea. La aceptación crea la tarea de impresión y le avisa. Stellio no procesa ningún pago.", "q_none": "Aún no hay presupuestos.", "q_create": "Crear enlace", "q_copy": "Copiar enlace", "q_copied": "Enlace copiado", "q_revoke": "Revocar", "st_draft": "Borrador", "st_sent": "Enviado", "st_accepted": "Aceptado", "st_refused": "Rechazado", "q_by": "por", "pay_title": "Anticipo: datos que verá el cliente tras aceptar", "pay_info": "Texto (IBAN, referencia…)", "pay_link": "Enlace de pago (https://…)", "a_intro": "Un archivo ZIP para su contable: CSV de documentos, PDF de facturas y resumen de totales por mes.", "a_month": "Mes", "a_quotes": "Incluir presupuestos", "a_download": "Descargar el ZIP", "a_saved": "Archivo guardado: ", "s_intro": "Controle sus piezas terminadas. Por debajo del umbral, Stellio avisa y puede iniciar la reposición.", "s_none": "Aún no hay piezas.", "s_name": "Pieza", "s_sku": "Referencia", "s_mat": "Material", "s_qty": "Stock", "s_min": "Umbral", "s_reorder": "Reposición (cant.)", "s_auto": "Reposición automática", "s_incoming": "en curso", "s_add": "Añadir pieza", "s_restock": "Reponer", "s_restocked": "Tarea de reposición creada", "s_delete": "Eliminar", "s_confirm": "¿Eliminar esta pieza?", "d_intro": "Stellio propone la mejor impresora para cada tarea en espera (libre, material cargado, cola). Solo asigna: nunca inicia una impresión.", "d_analyze": "Analizar", "d_apply": "Aplicar todo", "d_apply1": "Aplicar", "d_none": "No hay tareas en espera.", "d_best": "Impresora sugerida", "d_cur": "actual", "d_no_printer": "Ninguna impresora disponible", "r_idle": "libre", "r_busy": "ocupada", "r_material_loaded": "material cargado", "r_queue": "cola", "w_material_change": "cambiar el material", "w_not_enough_filament": "filamento insuficiente", "d_applied": "tarea(s) reasignada(s)", "g_intro": "Un resumen por notificación (y push si está activo): tareas terminadas, retrasos, energía, bobinas, facturas, stock.", "g_enable": "Activar el resumen", "g_freq": "Frecuencia", "g_daily": "Diario", "g_weekly": "Semanal", "g_hour": "Hora", "g_weekday": "Día", "g_preview": "Vista previa", "g_send": "Enviar ahora", "g_sent": "Resumen enviado", "f_intro": "Peso restante de las bobinas TigerTag (automático) y pesadas manuales. Stellio calcula el consumo diario y la fecha de agotamiento.", "f_sync": "Releer TigerTag", "f_none": "Aún no hay pesadas: use TigerTag o pese una bobina.", "f_name": "Bobina", "f_remaining": "Restante (g)", "f_rate": "g / día", "f_days": "Días restantes", "f_empty": "Se agota hacia", "f_weigh": "Pesar una bobina manual", "f_spool": "Bobina", "f_gross": "Peso total (g)", "f_tare": "Tara: bobina vacía (g)", "f_save": "Guardar la pesada", "f_synced": "lectura(s) guardada(s)", "p_intro": "Envíe un perfil de slicer a otra instancia de Stellio vinculada, o descargue el archivo original.", "p_none": "No hay perfiles importados.", "p_instance": "Instancia", "p_send": "Enviar", "p_download": "Descargar", "p_sent": "Perfil enviado", "p_exists": "Ya está en la otra instancia", "p_no_inst": "Ninguna instancia vinculada (Ajustes → Instancias remotas).", "h_prof": "Compartir perfiles de slicer", "h_disp": "Reparto de impresoras", "h_digest": "Resumen periódico", "h_fil": "Pesaje y previsión de filamento", "q_need_remote": "Un enlace de presupuesto debe ser accesible desde Internet para que su cliente pueda abrirlo. Active el acceso remoto para crear enlaces externos.", "q_remote_enable": "Activar el acceso remoto", "q_remote_wait": "Conectando… puede tardar un minuto.", "q_remote_refresh": "Actualizar", "q_remote_quick": "Dirección temporal: cambia cada vez que se reinicia el acceso remoto y los enlaces ya enviados dejarán de funcionar. Para un enlace duradero, configure una dirección fija o personalizada en Ajustes › Acceso remoto.", "q_link_paused": "Enlace en pausa: el acceso remoto no está activo."}, "pt": {"title": "Gestão", "err": "Não foi possível concluir, tente novamente.", "save": "Guardar", "saved": "Guardado", "t_quotes": "Orçamentos de clientes", "t_acc": "Contabilidade", "t_stock": "Stock de peças", "t_disp": "Distribuição", "t_digest": "Resumo", "t_fil": "Filamento", "t_prof": "Perfis", "q_intro": "Envie uma ligação ao seu cliente: ele consulta o orçamento e aceita ou recusa online. A aceitação cria a tarefa de impressão e avisa-o. O Stellio não processa pagamentos.", "q_none": "Ainda não há orçamentos.", "q_create": "Criar ligação", "q_copy": "Copiar ligação", "q_copied": "Ligação copiada", "q_revoke": "Revogar", "st_draft": "Rascunho", "st_sent": "Enviado", "st_accepted": "Aceite", "st_refused": "Recusado", "q_by": "por", "pay_title": "Sinal: informações mostradas ao cliente após a aceitação", "pay_info": "Texto (IBAN, referência…)", "pay_link": "Ligação de pagamento (https://…)", "a_intro": "Um ficheiro ZIP para o seu contabilista: CSV dos documentos, PDF das faturas e resumo dos totais por mês.", "a_month": "Mês", "a_quotes": "Incluir orçamentos", "a_download": "Descarregar o ZIP", "a_saved": "Ficheiro guardado: ", "s_intro": "Acompanhe as suas peças acabadas. Abaixo do limite, o Stellio avisa e pode iniciar a reposição.", "s_none": "Ainda não há peças.", "s_name": "Peça", "s_sku": "Referência", "s_mat": "Material", "s_qty": "Stock", "s_min": "Limite", "s_reorder": "Reposição (qtd.)", "s_auto": "Reposição automática", "s_incoming": "em curso", "s_add": "Adicionar peça", "s_restock": "Repor", "s_restocked": "Tarefa de reposição criada", "s_delete": "Eliminar", "s_confirm": "Eliminar esta peça?", "d_intro": "O Stellio sugere a melhor impressora para cada tarefa em espera (livre, material carregado, fila). Apenas atribui: nunca inicia uma impressão.", "d_analyze": "Analisar", "d_apply": "Aplicar tudo", "d_apply1": "Aplicar", "d_none": "Sem tarefas em espera.", "d_best": "Impressora sugerida", "d_cur": "atual", "d_no_printer": "Nenhuma impressora disponível", "r_idle": "livre", "r_busy": "ocupada", "r_material_loaded": "material carregado", "r_queue": "fila", "w_material_change": "mudar o material", "w_not_enough_filament": "filamento insuficiente", "d_applied": "tarefa(s) reatribuída(s)", "g_intro": "Um resumo por notificação (e push, se ativo): tarefas concluídas, atrasos, energia, bobines, faturas, stock.", "g_enable": "Ativar o resumo", "g_freq": "Frequência", "g_daily": "Diário", "g_weekly": "Semanal", "g_hour": "Hora", "g_weekday": "Dia", "g_preview": "Pré-visualizar", "g_send": "Enviar agora", "g_sent": "Resumo enviado", "f_intro": "Peso restante das bobines TigerTag (automático) e pesagens manuais. O Stellio calcula o consumo diário e a data de esgotamento.", "f_sync": "Reler TigerTag", "f_none": "Ainda sem pesagens: use TigerTag ou pese uma bobine.", "f_name": "Bobine", "f_remaining": "Restante (g)", "f_rate": "g / dia", "f_days": "Dias restantes", "f_empty": "Esgota por volta de", "f_weigh": "Pesar uma bobine manual", "f_spool": "Bobine", "f_gross": "Peso total (g)", "f_tare": "Tara: bobine vazia (g)", "f_save": "Guardar a pesagem", "f_synced": "leitura(s) guardada(s)", "p_intro": "Envie um perfil de slicer a outra instância Stellio emparelhada, ou descarregue o ficheiro original.", "p_none": "Sem perfis importados.", "p_instance": "Instância", "p_send": "Enviar", "p_download": "Descarregar", "p_sent": "Perfil enviado", "p_exists": "Já existe na outra instância", "p_no_inst": "Nenhuma instância emparelhada (Definições → Instâncias remotas).", "h_prof": "Compartilhar perfis do slicer", "h_disp": "Distribuição de impressoras", "h_digest": "Resumo periódico", "h_fil": "Pesagem e previsão de filamento", "q_need_remote": "Um link de orçamento precisa estar acessível pela Internet para que o cliente possa abri-lo. Ative o acesso remoto para criar links externos.", "q_remote_enable": "Ativar o acesso remoto", "q_remote_wait": "Conectando… pode levar um minuto.", "q_remote_refresh": "Atualizar", "q_remote_quick": "Endereço temporário: muda a cada reinício do acesso remoto e os links já enviados deixam de funcionar. Para um link duradouro, configure um endereço fixo ou personalizado em Configurações › Acesso remoto.", "q_link_paused": "Link pausado: o acesso remoto não está ativo."}, "it": {"title": "Gestione", "err": "Operazione non riuscita, riprovi.", "save": "Salva", "saved": "Salvato", "t_quotes": "Preventivi clienti", "t_acc": "Contabilità", "t_stock": "Magazzino pezzi", "t_disp": "Ripartizione", "t_digest": "Riepilogo", "t_fil": "Filamento", "t_prof": "Profili", "q_intro": "Invii un link al cliente: consulta il preventivo e lo accetta o rifiuta online. L'accettazione crea il lavoro di stampa e La avvisa. Stellio non elabora pagamenti.", "q_none": "Nessun preventivo.", "q_create": "Crea link", "q_copy": "Copia link", "q_copied": "Link copiato", "q_revoke": "Revoca", "st_draft": "Bozza", "st_sent": "Inviato", "st_accepted": "Accettato", "st_refused": "Rifiutato", "q_by": "da", "pay_title": "Acconto: informazioni mostrate al cliente dopo l'accettazione", "pay_info": "Testo (IBAN, riferimento…)", "pay_link": "Link di pagamento (https://…)", "a_intro": "Un file ZIP per il commercialista: CSV dei documenti, PDF delle fatture e riepilogo dei totali per mese.", "a_month": "Mese", "a_quotes": "Includi i preventivi", "a_download": "Scarica lo ZIP", "a_saved": "File salvato: ", "s_intro": "Tenga traccia dei pezzi finiti. Sotto la soglia Stellio avvisa e può avviare il rifornimento.", "s_none": "Nessun pezzo monitorato.", "s_name": "Pezzo", "s_sku": "Riferimento", "s_mat": "Materiale", "s_qty": "Scorta", "s_min": "Soglia", "s_reorder": "Rifornimento (qtà)", "s_auto": "Rifornimento automatico", "s_incoming": "in corso", "s_add": "Aggiungi pezzo", "s_restock": "Rifornisci", "s_restocked": "Lavoro di rifornimento creato", "s_delete": "Elimina", "s_confirm": "Eliminare questo pezzo?", "d_intro": "Stellio propone la stampante migliore per ogni lavoro in attesa (libera, materiale caricato, coda). Assegna soltanto: non avvia mai una stampa.", "d_analyze": "Analizza", "d_apply": "Applica tutto", "d_apply1": "Applica", "d_none": "Nessun lavoro in attesa.", "d_best": "Stampante consigliata", "d_cur": "attuale", "d_no_printer": "Nessuna stampante disponibile", "r_idle": "libera", "r_busy": "occupata", "r_material_loaded": "materiale caricato", "r_queue": "coda", "w_material_change": "cambiare materiale", "w_not_enough_filament": "filamento insufficiente", "d_applied": "lavoro/i riassegnato/i", "g_intro": "Un riepilogo tramite notifica (e push se attivo): lavori finiti, ritardi, energia, bobine, fatture, scorte.", "g_enable": "Attiva il riepilogo", "g_freq": "Frequenza", "g_daily": "Giornaliero", "g_weekly": "Settimanale", "g_hour": "Ora", "g_weekday": "Giorno", "g_preview": "Anteprima", "g_send": "Invia ora", "g_sent": "Riepilogo inviato", "f_intro": "Peso residuo delle bobine TigerTag (automatico) e pesate manuali. Stellio ricava il consumo giornaliero e la data di esaurimento.", "f_sync": "Rileggi TigerTag", "f_none": "Nessuna pesata: usi TigerTag o pesi una bobina.", "f_name": "Bobina", "f_remaining": "Residuo (g)", "f_rate": "g / giorno", "f_days": "Giorni rimasti", "f_empty": "Esaurimento verso", "f_weigh": "Pesa una bobina manuale", "f_spool": "Bobina", "f_gross": "Peso totale (g)", "f_tare": "Tara: bobina vuota (g)", "f_save": "Salva la pesata", "f_synced": "lettura/e salvata/e", "p_intro": "Invii un profilo slicer a un'altra istanza Stellio associata, oppure scarichi il file originale.", "p_none": "Nessun profilo importato.", "p_instance": "Istanza", "p_send": "Invia", "p_download": "Scarica", "p_sent": "Profilo inviato", "p_exists": "Già presente sull'altra istanza", "p_no_inst": "Nessuna istanza associata (Impostazioni → Istanze remote).", "h_prof": "Condivisione profili slicer", "h_disp": "Assegnazione stampanti", "h_digest": "Riepilogo periodico", "h_fil": "Pesatura e previsione filamento", "q_need_remote": "Il link di un preventivo deve essere raggiungibile da Internet perché il cliente possa aprirlo. Attivi l'accesso remoto per creare link esterni.", "q_remote_enable": "Attiva l'accesso remoto", "q_remote_wait": "Connessione in corso… può richiedere un minuto.", "q_remote_refresh": "Aggiorna", "q_remote_quick": "Indirizzo temporaneo: cambia a ogni riavvio dell'accesso remoto e i link già inviati smetteranno di funzionare. Per un link duraturo, configuri un indirizzo fisso o personalizzato in Impostazioni › Accesso remoto.", "q_link_paused": "Link in pausa: l'accesso remoto non è attivo."}, "zh": {"title": "管理", "err": "操作失败，请重试。", "save": "保存", "saved": "已保存", "t_quotes": "客户报价", "t_acc": "会计", "t_stock": "零件库存", "t_disp": "分配", "t_digest": "摘要", "t_fil": "耗材", "t_prof": "配置文件", "q_intro": "向客户发送链接：客户可在线查看报价并接受或拒绝。接受后会创建打印任务并通知您。Stellio 不处理任何付款。", "q_none": "暂无报价。", "q_create": "创建链接", "q_copy": "复制链接", "q_copied": "链接已复制", "q_revoke": "撤销", "st_draft": "草稿", "st_sent": "已发送", "st_accepted": "已接受", "st_refused": "已拒绝", "q_by": "由", "pay_title": "定金：客户接受后显示的信息", "pay_info": "文本（IBAN、参考号…）", "pay_link": "支付链接 (https://…)", "a_intro": "给会计的一个 ZIP 文件：单据 CSV、发票 PDF 和按月汇总。", "a_month": "月份", "a_quotes": "包含报价单", "a_download": "下载 ZIP", "a_saved": "文件已保存：", "s_intro": "跟踪成品零件。低于阈值时 Stellio 会提醒，并可发起补货。", "s_none": "暂无跟踪的零件。", "s_name": "零件", "s_sku": "编号", "s_mat": "材料", "s_qty": "库存", "s_min": "阈值", "s_reorder": "补货（数量）", "s_auto": "自动补货", "s_incoming": "进行中", "s_add": "添加零件", "s_restock": "补货", "s_restocked": "已创建补货任务", "s_delete": "删除", "s_confirm": "删除此零件？", "d_intro": "Stellio 为每个等待中的任务推荐最合适的打印机（空闲、已装材料、队列）。它只做分配，绝不会自动开始打印。", "d_analyze": "分析", "d_apply": "全部应用", "d_apply1": "应用", "d_none": "没有等待中的任务。", "d_best": "推荐的打印机", "d_cur": "当前", "d_no_printer": "没有可用的打印机", "r_idle": "空闲", "r_busy": "忙碌", "r_material_loaded": "已装材料", "r_queue": "队列", "w_material_change": "需更换材料", "w_not_enough_filament": "耗材不足", "d_applied": "个任务已重新分配", "g_intro": "通过通知（启用后也可推送）发送摘要：已完成任务、延误、能耗、耗材盘、发票、库存。", "g_enable": "启用摘要", "g_freq": "频率", "g_daily": "每天", "g_weekly": "每周", "g_hour": "时间", "g_weekday": "星期", "g_preview": "预览", "g_send": "立即发送", "g_sent": "摘要已发送", "f_intro": "TigerTag 耗材盘的剩余重量（自动）和手动称重。Stellio 据此推算每日用量和用完日期。", "f_sync": "重新读取 TigerTag", "f_none": "还没有称重记录：请使用 TigerTag 或称一盘耗材。", "f_name": "耗材盘", "f_remaining": "剩余 (g)", "f_rate": "g / 天", "f_days": "剩余天数", "f_empty": "预计用完", "f_weigh": "称量手动耗材盘", "f_spool": "耗材盘", "f_gross": "总重 (g)", "f_tare": "皮重：空盘 (g)", "f_save": "保存称重", "f_synced": "条记录已保存", "p_intro": "将切片配置文件发送到另一个已配对的 Stellio 实例，或下载原始文件。", "p_none": "没有已导入的配置文件。", "p_instance": "实例", "p_send": "发送", "p_download": "下载", "p_sent": "配置文件已发送", "p_exists": "对方实例上已存在", "p_no_inst": "没有已配对的实例（设置 → 远程实例）。", "h_prof": "切片软件配置共享", "h_disp": "打印机智能分配", "h_digest": "定期摘要", "h_fil": "耗材称重与预测", "q_need_remote": "报价链接必须能从互联网访问，客户才能打开。请开启远程访问以创建外部链接。", "q_remote_enable": "开启远程访问", "q_remote_wait": "正在连接…可能需要一分钟。", "q_remote_refresh": "刷新", "q_remote_quick": "临时地址：每次重启远程访问都会改变，已发出的链接将失效。如需长期有效的链接，请在 设置 › 远程访问 中配置固定或自定义地址。", "q_link_paused": "链接已暂停：远程访问未开启。"}, "ja": {"title": "管理", "err": "実行できませんでした。もう一度お試しください。", "save": "保存", "saved": "保存しました", "t_quotes": "顧客見積", "t_acc": "会計", "t_stock": "部品在庫", "t_disp": "割り当て", "t_digest": "サマリー", "t_fil": "フィラメント", "t_prof": "プロファイル", "q_intro": "顧客にリンクを送ると、見積をオンラインで確認し、承認または辞退できます。承認すると印刷タスクが作成され通知されます。Stellio は支払いを処理しません。", "q_none": "見積はまだありません。", "q_create": "リンクを作成", "q_copy": "リンクをコピー", "q_copied": "コピーしました", "q_revoke": "無効にする", "st_draft": "下書き", "st_sent": "送信済み", "st_accepted": "承認済み", "st_refused": "辞退", "q_by": "承認者：", "pay_title": "手付金：承認後に顧客へ表示する情報", "pay_info": "テキスト（IBAN、参照番号など）", "pay_link": "支払いリンク (https://…)", "a_intro": "会計担当者向けの ZIP：書類の CSV、請求書の PDF、月別の合計。", "a_month": "月", "a_quotes": "見積を含める", "a_download": "ZIP をダウンロード", "a_saved": "保存しました：", "s_intro": "完成部品を管理します。しきい値を下回ると通知し、補充を開始できます。", "s_none": "管理中の部品はありません。", "s_name": "部品", "s_sku": "品番", "s_mat": "素材", "s_qty": "在庫", "s_min": "しきい値", "s_reorder": "補充（数量）", "s_auto": "自動補充", "s_incoming": "進行中", "s_add": "部品を追加", "s_restock": "補充", "s_restocked": "補充タスクを作成しました", "s_delete": "削除", "s_confirm": "この部品を削除しますか？", "d_intro": "待機中の各タスクに最適なプリンターを提案します（空き、素材装着、キュー）。割り当てのみで、印刷は開始しません。", "d_analyze": "分析", "d_apply": "すべて適用", "d_apply1": "適用", "d_none": "待機中のタスクはありません。", "d_best": "推奨プリンター", "d_cur": "現在", "d_no_printer": "利用可能なプリンターがありません", "r_idle": "空き", "r_busy": "使用中", "r_material_loaded": "素材装着済み", "r_queue": "キュー", "w_material_change": "素材の交換が必要", "w_not_enough_filament": "フィラメント不足", "d_applied": "件のタスクを再割り当てしました", "g_intro": "通知（有効ならプッシュも）でサマリーを送ります：完了タスク、遅延、電力、スプール、請求書、在庫。", "g_enable": "サマリーを有効にする", "g_freq": "頻度", "g_daily": "毎日", "g_weekly": "毎週", "g_hour": "時刻", "g_weekday": "曜日", "g_preview": "プレビュー", "g_send": "今すぐ送信", "g_sent": "サマリーを送信しました", "f_intro": "TigerTag スプールの残量（自動）と手動計量。Stellio が1日の使用量と使い切る日を算出します。", "f_sync": "TigerTag を再読み込み", "f_none": "計量データがありません。TigerTag を使うかスプールを計量してください。", "f_name": "スプール", "f_remaining": "残量 (g)", "f_rate": "g / 日", "f_days": "残り日数", "f_empty": "使い切り予定", "f_weigh": "手動スプールを計量", "f_spool": "スプール", "f_gross": "総重量 (g)", "f_tare": "風袋：空スプール (g)", "f_save": "計量を保存", "f_synced": "件の読み取りを保存しました", "p_intro": "スライサープロファイルをペアリング済みの別の Stellio に送信、または元のファイルをダウンロードします。", "p_none": "インポート済みプロファイルはありません。", "p_instance": "インスタンス", "p_send": "送信", "p_download": "ダウンロード", "p_sent": "プロファイルを送信しました", "p_exists": "相手側に既にあります", "p_no_inst": "ペアリング済みのインスタンスがありません（設定 → リモートインスタンス）。", "h_prof": "スライサープロファイルの共有", "h_disp": "プリンターの割り当て", "h_digest": "定期サマリー", "h_fil": "フィラメントの計量と予測", "q_need_remote": "見積もりリンクは、お客様が開けるようインターネットから到達できる必要があります。外部リンクを作成するにはリモートアクセスを有効にしてください。", "q_remote_enable": "リモートアクセスを有効にする", "q_remote_wait": "接続中です…1 分ほどかかることがあります。", "q_remote_refresh": "更新", "q_remote_quick": "一時的なアドレスです。リモートアクセスを再起動するたびに変わり、送信済みのリンクは使えなくなります。長く使えるリンクにするには、設定 › リモートアクセス で固定または独自のアドレスを設定してください。", "q_link_paused": "リンクは一時停止中です：リモートアクセスが有効ではありません。"}};
const TABS = ['quotes', 'acc', 'stock'];   // Gestion = le financier ; les autres vues sont montées dans leur page (initSlots)
const ICONS = {quotes: 'fa-file-signature', acc: 'fa-file-zipper', stock: 'fa-boxes-stacked', disp: 'fa-shuffle', digest: 'fa-bell', fil: 'fa-weight-scale', prof: 'fa-share-nodes'};
let tab = 'quotes';

function lang() {
    let l = '';
    try { l = (document.documentElement.lang || localStorage.getItem('stellio_lang') || navigator.language || 'fr'); } catch (e) { l = 'fr'; }
    l = String(l).toLowerCase().slice(0, 2);
    return TXT[l] ? l : 'en';
}
const t = (k) => (TXT[lang()] && TXT[lang()][k]) || TXT.en[k] || k;
const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const root = () => document.getElementById('mg-body');

async function api(method, url, body) {
    const opt = {method, headers: {}};
    if (body !== undefined) { opt.headers['Content-Type'] = 'application/json'; opt.body = JSON.stringify(body); }
    const r = await fetch(url, opt);
    let j = {};
    try { j = await r.json(); } catch (e) { /* corps vide */ }
    if (!r.ok && j.success === undefined) j.success = false;
    return j;
}
function toast(msg, bad) {
    if (typeof window.showToast === 'function') { try { window.showToast(msg, bad ? 'error' : 'success'); return; } catch (e) { /* repli */ } }
    const el = document.getElementById('mg-msg');
    if (el) { el.textContent = msg; el.className = 'mg-msg ' + (bad ? 'bad' : 'ok'); setTimeout(() => { el.textContent = ''; }, 4000); }
}
const fail = () => toast(t('err'), true);

function shell() {
    const page = document.getElementById('page-management');
    if (!page || page.dataset.ready) return;
    page.dataset.ready = '1';
    page.querySelector('.history-page').insertAdjacentHTML('beforeend',
        '<div class="mg-tabs" id="mg-tabs" role="tablist"></div><div id="mg-msg" class="mg-msg"></div><div id="mg-body" class="mg-body"></div>');
    page.querySelector('#mg-tabs').addEventListener('click', (e) => {
        const b = e.target.closest('[data-tab]');
        if (b) { tab = b.dataset.tab; render(); }
    });
}
function renderTabs() {
    document.getElementById('mg-tabs').innerHTML = TABS.map((k) =>
        `<button type="button" role="tab" class="mg-tab${k === tab ? ' active' : ''}" data-tab="${k}"><i class="fa-solid ${ICONS[k]}"></i> <span>${esc(t('t_' + k))}</span></button>`).join('');
}
function render() {
    renderTabs();
    const el = root();
    el.innerHTML = '<p class="mg-intro">…</p>';
    const fn = {quotes: vQuotes, acc: vAcc, stock: vStock, disp: vDisp, digest: vDigest, fil: vFil, prof: vProf}[tab];
    fn(el).catch(() => { el.innerHTML = ''; fail(); });
}
const intro = (k) => `<p class="mg-intro">${esc(t(k))}</p>`;
const btn = (cls, act, label, extra) => `<button type="button" class="mg-btn ${cls}" data-act="${act}" ${extra || ''}>${esc(label)}</button>`;
function on(el, handler) { el.onclick = (e) => { const b = e.target.closest('[data-act]'); if (b) handler(b, e); }; }

// ── Devis clients ──
async function vQuotes(el) {
    const [d, ] = await Promise.all([api('GET', '/api/quote-portal/links')]);
    const rows = d.quotes || [];
    const stl = (s) => t('st_' + (['draft', 'sent', 'accepted', 'refused'].includes(s) ? s : 'draft'));
    const warn = !d.remote
        ? `<div class="mg-card" style="border-left:3px solid var(--warning, #e0a030);"><p>${esc(t('q_need_remote'))}</p>` +
          (d.remote_status === 'starting'
              ? `<p class="mg-sub">${esc(t('q_remote_wait'))}</p><div class="mg-bar">${btn('', 'remote-refresh', t('q_remote_refresh'))}</div>`
              : `<div class="mg-bar">${btn('primary', 'remote-on', t('q_remote_enable'))}</div>`) + '</div>'
        : (d.remote_mode === 'quick' ? `<p class="mg-sub">${esc(t('q_remote_quick'))}</p>` : '');
    el.innerHTML = intro('q_intro') + warn + `
      <div class="mg-card"><h3>${esc(t('pay_title'))}</h3>
        <label class="mg-field"><span>${esc(t('pay_info'))}</span><textarea id="mg-pay-info" rows="2" maxlength="600">${esc(d.payment_info || '')}</textarea></label>
        <label class="mg-field"><span>${esc(t('pay_link'))}</span><input id="mg-pay-link" type="url" value="${esc(d.payment_link || '')}"></label>
        ${btn('primary', 'pay-save', t('save'))}</div>
      <div class="mg-list">${rows.length ? rows.map((q) => `
        <div class="mg-row" data-id="${q.id}">
          <div class="mg-row-main"><strong>${esc(q.number || '#' + q.id)}</strong> ${esc(q.client || '')}
            <span class="mg-pill st-${esc(q.status)}">${esc(stl(q.status))}</span>
            <div class="mg-sub">${esc(q.desc || '')} · ${esc(q.total)}${q.decision_by ? ` · ${esc(t('q_by'))} ${esc(q.decision_by)}` : ''}</div>
            ${q.url ? `<input class="mg-url" readonly value="${esc(q.url)}">` : (q.has_link ? `<div class="mg-sub">${esc(t('q_link_paused'))}</div>` : '')}</div>
          <div class="mg-row-act">${q.url ? btn('', 'copy', t('q_copy'), `data-url="${esc(q.url)}"`) + btn('danger', 'revoke', t('q_revoke')) : (q.has_link ? btn('danger', 'revoke', t('q_revoke')) : btn('primary', 'create', t('q_create')))}</div>
        </div>`).join('') : `<p class="mg-empty">${esc(t('q_none'))}</p>`}</div>`;
    on(el, async (b) => {
        const id = b.closest('.mg-row')?.dataset.id;
        if (b.dataset.act === 'pay-save') {
            const r = await api('POST', '/api/quote-portal/settings', {payment_info: el.querySelector('#mg-pay-info').value, payment_link: el.querySelector('#mg-pay-link').value});
            return r.success ? toast(t('saved')) : fail();
        }
        if (b.dataset.act === 'remote-refresh') return vQuotes(el);
        if (b.dataset.act === 'remote-on') {
            b.disabled = true;
            const r = await api('POST', '/api/remote-access/toggle', {enabled: true});
            if (r.success === false) { b.disabled = false; return fail(); }
            for (let i = 0; i < 40; i++) {                     // la connexion peut prendre une minute (téléchargement de cloudflared compris)
                await new Promise((res) => setTimeout(res, 1500));
                const st = await api('GET', '/api/remote-access');
                if (st.status === 'ready' || st.status === 'error') break;
            }
            return vQuotes(el);
        }
        if (b.dataset.act === 'create') {
            const r = await api('POST', `/api/quotes/${id}/portal`);
            if (r.success) return vQuotes(el);
            if (r.error === 'remote_required') { toast(t('q_need_remote'), true); return vQuotes(el); }
            return fail();
        }
        if (b.dataset.act === 'revoke') { const r = await api('DELETE', `/api/quotes/${id}/portal`); return r.success ? vQuotes(el) : fail(); }
        if (b.dataset.act === 'copy') {
            const url = b.dataset.url;
            try { await navigator.clipboard.writeText(url); } catch (e) { const i = b.closest('.mg-row').querySelector('.mg-url'); if (i) { i.select(); document.execCommand('copy'); } }
            toast(t('q_copied'));
        }
    });
}

// ── Comptabilité ──
async function vAcc(el) {
    const now = new Date();
    const prev = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    const val = `${prev.getFullYear()}-${String(prev.getMonth() + 1).padStart(2, '0')}`;
    el.innerHTML = intro('a_intro') + `<div class="mg-card">
      <label class="mg-field"><span>${esc(t('a_month'))}</span><input id="mg-month" type="month" value="${val}"></label>
      <label class="mg-check"><input id="mg-inc-q" type="checkbox"> <span>${esc(t('a_quotes'))}</span></label>
      ${btn('primary', 'dl', t('a_download'))}</div>`;
    on(el, async () => {
        const month = el.querySelector('#mg-month').value, inc = el.querySelector('#mg-inc-q').checked ? '1' : '0';
        const l = lang() === 'fr' ? 'fr' : 'en';
        if (window.pywebview) {
            const r = await api('POST', '/api/quotes/export-zip-native', {month, lang: l, include_quotes: inc});
            if (r.success) toast(t('a_saved') + r.path); else if (!r.cancelled) fail();
        } else {
            window.location.href = `/api/quotes/export-zip?month=${encodeURIComponent(month)}&lang=${l}&include_quotes=${inc}`;
        }
    });
}

// ── Stock de pièces ──
async function vStock(el) {
    const d = await api('GET', '/api/parts-stock');
    const parts = d.parts || [];
    el.innerHTML = intro('s_intro') + `<div class="mg-list">${parts.length ? parts.map((p) => `
      <div class="mg-row${p.low ? ' low' : ''}" data-id="${p.id}">
        <div class="mg-row-main"><strong>${esc(p.name)}</strong> <span class="mg-sub">${esc(p.sku)} ${esc(p.material)}</span>
          <div class="mg-sub">${esc(t('s_qty'))} <b>${p.qty}</b> · ${esc(t('s_min'))} ${p.min_qty}${p.incoming ? ` · ${esc(t('s_incoming'))} +${p.incoming}` : ''}${p.auto_restock ? ' · ⟳' : ''}</div></div>
        <div class="mg-row-act">${btn('', 'minus', '−1')}${btn('', 'plus', '+1')}${btn('', 'restock', t('s_restock'))}${btn('danger', 'del', t('s_delete'))}</div>
      </div>`).join('') : `<p class="mg-empty">${esc(t('s_none'))}</p>`}</div>
      <div class="mg-card"><h3>${esc(t('s_add'))}</h3><div class="mg-grid">
        <label class="mg-field"><span>${esc(t('s_name'))}</span><input id="sp-name"></label>
        <label class="mg-field"><span>${esc(t('s_sku'))}</span><input id="sp-sku"></label>
        <label class="mg-field"><span>${esc(t('s_mat'))}</span><input id="sp-mat" placeholder="PLA"></label>
        <label class="mg-field"><span>${esc(t('s_qty'))}</span><input id="sp-qty" type="number" min="0" value="0"></label>
        <label class="mg-field"><span>${esc(t('s_min'))}</span><input id="sp-min" type="number" min="0" value="0"></label>
        <label class="mg-field"><span>${esc(t('s_reorder'))}</span><input id="sp-re" type="number" min="1" value="10"></label></div>
        <label class="mg-check"><input id="sp-auto" type="checkbox"> <span>${esc(t('s_auto'))}</span></label>
        ${btn('primary', 'add', t('s_add'))}</div>`;
    on(el, async (b) => {
        const id = b.closest('.mg-row')?.dataset.id, a = b.dataset.act;
        let r;
        if (a === 'add') {
            const name = el.querySelector('#sp-name').value.trim(); if (!name) return;
            r = await api('POST', '/api/parts-stock', {name, sku: el.querySelector('#sp-sku').value, material: el.querySelector('#sp-mat').value,
                min_qty: el.querySelector('#sp-min').value, reorder_qty: el.querySelector('#sp-re').value, auto_restock: el.querySelector('#sp-auto').checked});
            if (r.success && Number(el.querySelector('#sp-qty').value) > 0) await api('POST', `/api/parts-stock/${r.id}/adjust`, {set: Number(el.querySelector('#sp-qty').value)});
        } else if (a === 'minus' || a === 'plus') r = await api('POST', `/api/parts-stock/${id}/adjust`, {delta: a === 'plus' ? 1 : -1});
        else if (a === 'restock') { r = await api('POST', `/api/parts-stock/${id}/restock`, {}); if (r.success) toast(t('s_restocked')); }
        else if (a === 'del') {
            if (b.dataset.sure !== '1') { b.dataset.sure = '1'; b.textContent = t('s_confirm'); return; }
            r = await api('DELETE', `/api/parts-stock/${id}`);
        }
        if (r && r.success) vStock(el); else fail();
    });
}

// ── Répartition ──
async function vDisp(el) {
    const d = await api('GET', '/api/dispatch/suggestions');
    const list = d.suggestions || [];
    const why = (c) => [...(c.reasons || []).map((r) => t('r_' + r)), ...(c.warnings || []).map((w) => '⚠ ' + t('w_' + w))].join(' · ');
    const todo = list.filter((s) => s.change);
    el.innerHTML = intro('d_intro') + (todo.length ? `<div class="mg-bar">${btn('primary', 'apply-all', t('d_apply'))}</div>` : '') +
      `<div class="mg-list">${list.length ? list.map((s) => `
        <div class="mg-row" data-id="${s.job_id}">
          <div class="mg-row-main"><strong>${esc(s.part)}</strong> <span class="mg-sub">${esc(s.client || '')} ${esc(s.material || '')} ×${s.quantity - s.qty_done}${s.due_date ? ' · ' + esc(s.due_date) : ''}</span>
            <div class="mg-sub">${s.best ? `${esc(t('d_best'))} : <b>${esc(s.best.printer_name)}</b> — ${esc(why(s.best))}` : esc(t('d_no_printer'))}</div></div>
          <div class="mg-row-act">${s.change ? btn('primary', 'apply', t('d_apply1')) : `<span class="mg-pill">${esc(t('d_cur'))}</span>`}</div>
        </div>`).join('') : `<p class="mg-empty">${esc(t('d_none'))}</p>`}</div>`;
    on(el, async (b) => {
        const ids = b.dataset.act === 'apply' ? [Number(b.closest('.mg-row').dataset.id)] : undefined;
        const r = await api('POST', '/api/dispatch/apply', ids ? {job_ids: ids} : {});
        if (r.success) { toast(`${r.changed} ${t('d_applied')}`); vDisp(el); } else fail();
    });
}

// ── Résumé ──
async function vDigest(el) {
    const c = await api('GET', '/api/digest/settings');
    const days = [...Array(7)].map((_, i) => new Intl.DateTimeFormat(lang(), {weekday: 'long'}).format(new Date(2024, 0, 1 + i)));
    el.innerHTML = intro('g_intro') + `<div class="mg-card">
      <label class="mg-check"><input id="dg-on" type="checkbox" ${c.enabled ? 'checked' : ''}> <span>${esc(t('g_enable'))}</span></label>
      <div class="mg-grid">
        <label class="mg-field"><span>${esc(t('g_freq'))}</span><select id="dg-freq"><option value="daily"${c.frequency === 'daily' ? ' selected' : ''}>${esc(t('g_daily'))}</option><option value="weekly"${c.frequency === 'weekly' ? ' selected' : ''}>${esc(t('g_weekly'))}</option></select></label>
        <label class="mg-field"><span>${esc(t('g_hour'))}</span><select id="dg-hour">${[...Array(24)].map((_, h) => `<option value="${h}"${h === c.hour ? ' selected' : ''}>${String(h).padStart(2, '0')}:00</option>`).join('')}</select></label>
        <label class="mg-field"><span>${esc(t('g_weekday'))}</span><select id="dg-wd">${days.map((n, i) => `<option value="${i}"${i === c.weekday ? ' selected' : ''}>${esc(n)}</option>`).join('')}</select></label></div>
      <div class="mg-bar">${btn('primary', 'save', t('save'))}${btn('', 'preview', t('g_preview'))}${btn('', 'send', t('g_send'))}</div>
      <pre id="dg-pre" class="mg-pre" hidden></pre></div>`;
    const freq = () => el.querySelector('#dg-freq').value;
    on(el, async (b) => {
        if (b.dataset.act === 'save') {
            const r = await api('POST', '/api/digest/settings', {enabled: el.querySelector('#dg-on').checked, frequency: freq(), hour: +el.querySelector('#dg-hour').value, weekday: +el.querySelector('#dg-wd').value});
            return r.success === false ? fail() : toast(t('saved'));
        }
        const pre = el.querySelector('#dg-pre');
        if (b.dataset.act === 'preview') { const r = await api('GET', '/api/digest/preview?frequency=' + freq()); pre.textContent = `${r.title}\n\n${r.text}`; pre.hidden = false; }
        if (b.dataset.act === 'send') { const r = await api('POST', '/api/digest/send-now', {frequency: freq()}); if (r.success) { pre.textContent = `${r.title}\n\n${r.text}`; pre.hidden = false; toast(t('g_sent')); } else fail(); }
    });
}

// ── Filament ──
async function vFil(el) {
    const [d, man] = await Promise.all([api('GET', '/api/filament/forecast'), api('GET', '/api/filament/manual')]);
    const spools = d.spools || [];
    const manual = (Array.isArray(man) ? man : []).filter((s) => !s.archived);
    el.innerHTML = intro('f_intro') + `<div class="mg-bar">${btn('', 'sync', t('f_sync'))}</div>
      <div class="mg-list">${spools.length ? spools.map((s) => `
        <div class="mg-row${s.days_left != null && s.days_left < 7 ? ' low' : ''}">
          <div class="mg-row-main"><strong>${esc(s.name || s.source_id)}</strong>
            <div class="mg-sub">${esc(t('f_remaining'))} <b>${s.remaining_g}</b> · ${s.g_per_day != null ? `${s.g_per_day} ${esc(t('f_rate'))} · ${esc(t('f_days'))} <b>${s.days_left}</b> · ${esc(t('f_empty'))} ${esc(s.empty_on)}` : '—'}</div></div>
        </div>`).join('') : `<p class="mg-empty">${esc(t('f_none'))}</p>`}</div>
      ${manual.length ? `<div class="mg-card"><h3>${esc(t('f_weigh'))}</h3><div class="mg-grid">
        <label class="mg-field"><span>${esc(t('f_spool'))}</span><select id="fw-id">${manual.map((s) => `<option value="${s.id}">${esc(s.name)} (${esc(s.material || '')})</option>`).join('')}</select></label>
        <label class="mg-field"><span>${esc(t('f_gross'))}</span><input id="fw-gross" type="number" min="0" step="0.1"></label>
        <label class="mg-field"><span>${esc(t('f_tare'))}</span><input id="fw-tare" type="number" min="0" step="0.1" value="0"></label></div>
        ${btn('primary', 'weigh', t('f_save'))}</div>` : ''}`;
    on(el, async (b) => {
        if (b.dataset.act === 'sync') { const r = await api('POST', '/api/filament/weigh-sync'); if (r.success) { toast(`${r.recorded} ${t('f_synced')}`); vFil(el); } else fail(); }
        if (b.dataset.act === 'weigh') {
            const gross = el.querySelector('#fw-gross').value; if (gross === '') return;
            const r = await api('POST', '/api/filament/weigh', {source_id: el.querySelector('#fw-id').value, gross_g: gross, tare_g: el.querySelector('#fw-tare').value});
            if (r.success) { toast(t('saved')); vFil(el); } else fail();
        }
    });
}

// ── Profils ──
async function vProf(el) {
    const [p, i] = await Promise.all([api('GET', '/api/slicer-profiles'), api('GET', '/api/remote-instances')]);
    const profiles = (p.profiles || []).filter((x) => x.source_path || x.source_filename);
    const inst = i.instances || [];
    const opts = inst.map((n) => `<option value="${n.id}">${esc(n.name)}</option>`).join('');
    el.innerHTML = intro('p_intro') + (inst.length ? '' : `<p class="mg-empty">${esc(t('p_no_inst'))}</p>`) +
      `<div class="mg-list">${profiles.length ? profiles.map((x) => `
        <div class="mg-row" data-id="${esc(x.id)}">
          <div class="mg-row-main"><strong>${esc(x.name)}</strong> <span class="mg-sub">${esc(x.slicer || '')}</span></div>
          <div class="mg-row-act">${inst.length ? `<select class="mg-sel">${opts}</select>${btn('primary', 'send', t('p_send'))}` : ''}${btn('', 'dl', t('p_download'))}</div>
        </div>`).join('') : `<p class="mg-empty">${esc(t('p_none'))}</p>`}</div>`;
    on(el, async (b) => {
        const row = b.closest('.mg-row'), id = row.dataset.id;
        if (b.dataset.act === 'dl') { window.location.href = `/api/slicer-profiles/${encodeURIComponent(id)}/export`; return; }
        const r = await api('POST', `/api/slicer-profiles/${encodeURIComponent(id)}/send-to-instance`, {instance_id: row.querySelector('.mg-sel').value});
        if (r.success) toast(r.already_present ? t('p_exists') : t('p_sent')); else fail();
    });
}

// Vues montées hors de « Gestion » : répartition (À imprimer bientôt), résumé (Paramètres › Notifications push),
// pesée de filament (Inventaire filament), partage de profils (Paramètres › Slicer). Chargées quand leur zone devient visible.
const SLOTS = {disp: vDisp, digest: vDigest, fil: vFil, prof: vProf};
function initSlots() {
    document.querySelectorAll('[data-mg-slot-title]').forEach((h) => { h.textContent = t('h_' + h.dataset.mgSlotTitle); });
    document.querySelectorAll('[data-mg-slot]').forEach((el) => {
        const fn = SLOTS[el.dataset.mgSlot];
        if (!fn || el.dataset.mgInit) return;
        el.dataset.mgInit = '1';
        let last = 0, busy = false;
        const run = () => {
            const now = Date.now();
            if (busy || now - last < 8000) return;
            busy = true; last = now;
            Promise.resolve().then(() => fn(el)).catch(() => { el.innerHTML = ''; }).finally(() => { busy = false; });
        };
        if ('IntersectionObserver' in window) new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) run(); }).observe(el);
        else run();
    });
}

function load() {
    shell();
    const h = document.querySelector('#page-management [data-mg-title]');
    if (h) h.textContent = t('title');
    render();
}
window.StellioManagement = {load, initSlots};
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initSlots); else initSlots();
})();
