"""Stellio — stocks de bobines manuelles et affectation d'une bobine à un fichier (1.2.1).

Extrait de main.py (modularisation) : mêmes URL, mêmes réponses, mêmes droits. Les suppressions passent par la corbeille (`trash_record`).
"""
_REQUIRED = (
    '_trash_snapshot',
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'session',
    'trash_record',
)
_OPTIONAL = ()
_OVERRIDABLE = ()

_MAIN = {}
_trash_snapshot = None
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None
trash_record = None


def api_assign_filament():
    data = request.json or {}
    file_path = (data.get('path') or '').strip()
    source_type = (data.get('source_type') or '').strip()
    source_id = str(data.get('source_id', '')).strip()
    if not file_path or not source_type or not source_id:
        return jsonify({"error": "Paramètres manquants"}), 400
    try:
        conn = get_db()
        conn.execute("""
            INSERT INTO filament_assignments (file_path, user_id, source_type, source_id, source_label, material, color_hex, spoolman_url, printer_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_path, user_id) DO UPDATE SET
                source_type=excluded.source_type, source_id=excluded.source_id, source_label=excluded.source_label,
                material=excluded.material, color_hex=excluded.color_hex, spoolman_url=excluded.spoolman_url,
                printer_id=excluded.printer_id, assigned_at=CURRENT_TIMESTAMP
        """, (
            file_path.replace('\\', '/'), session['user_id'], source_type, source_id,
            (data.get('name') or '').strip(), (data.get('material') or '').strip(),
            (data.get('color_hex') or '').strip(), (data.get('spoolman_url') or '').strip(),
            data.get('printer_id')
        ))
        conn.commit()
        conn.close()
        if source_type == 'spoolman' and data.get('spoolman_url'):
            try:
                conn = get_db()
                conn.execute("""
                    INSERT INTO spool_assignments (file_path, user_id, spoolman_url, spool_id, spool_name, spool_material, spool_color_hex)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(file_path, user_id) DO UPDATE SET
                        spoolman_url=excluded.spoolman_url, spool_id=excluded.spool_id, spool_name=excluded.spool_name,
                        spool_material=excluded.spool_material, spool_color_hex=excluded.spool_color_hex, assigned_at=CURRENT_TIMESTAMP
                """, (
                    file_path.replace('\\', '/'), session['user_id'], data.get('spoolman_url').rstrip('/'),
                    int(source_id), (data.get('name') or '').strip(), (data.get('material') or '').strip(),
                    (data.get('color_hex') or '').strip()
                ))
                conn.commit()
                conn.close()
            except Exception:
                pass
        return jsonify({"success": True}), 200
    except Exception as e:
        app_logger.error(f"[API] Erreur non gérée: {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500


def api_get_filament_assignment():
    file_path = (request.args.get('path') or '').strip()
    if not file_path:
        return jsonify({"error": "Chemin requis"}), 400
    try:
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT source_type, source_id, source_label, material, color_hex, spoolman_url, printer_id FROM filament_assignments WHERE file_path=? AND user_id=?",
                (file_path.replace('\\', '/'), session['user_id'])
            ).fetchone()
        finally:
            conn.close()
        if not row:
            return jsonify({"assignment": None}), 200
        return jsonify({"assignment": {
            "source_type": row[0], "source_id": row[1], "name": row[2],
            "material": row[3], "color_hex": row[4], "spoolman_url": row[5], "printer_id": row[6]
        }}), 200
    except Exception as e:
        app_logger.error(f"[API] Erreur non gérée: {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500


def api_unassign_filament():
    data = request.json or {}
    file_path = (data.get('path') or '').strip()
    if not file_path:
        return jsonify({"error": "Chemin requis"}), 400
    try:
        norm = file_path.replace('\\', '/')
        conn = get_db()
        try:
            conn.execute("DELETE FROM filament_assignments WHERE file_path=? AND user_id=?", (norm, session['user_id']))
            conn.execute("DELETE FROM spool_assignments WHERE file_path=? AND user_id=?", (norm, session['user_id']))
            conn.commit()
        finally:
            conn.close()
        return jsonify({"success": True}), 200
    except Exception as e:
        app_logger.error(f"[API] Erreur non gérée: {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500


def api_list_manual_spools():
    try:
        conn = get_db()
        try:
            rows = conn.execute(
                "SELECT id, name, material, color_hex, remaining_g, capacity_g, vendor, price, diameter_mm, notes, archived, storage_location "
                "FROM manual_filament_spools WHERE user_id=? ORDER BY archived ASC, created_at DESC",
                (session['user_id'],)
            ).fetchall()
        finally:
            conn.close()
        return jsonify([dict(r) for r in rows]), 200
    except Exception as e:
        app_logger.error(f"[API] Erreur non gérée: {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500


def api_create_manual_spool():
    data = request.json or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({"error": "Nom requis"}), 400
    try:
        conn = get_db()
        try:
            cur = conn.execute("""
                INSERT INTO manual_filament_spools
                    (user_id, name, material, color_hex, remaining_g, capacity_g, source_label, vendor, price, diameter_mm, notes, storage_location)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session['user_id'], name, (data.get('material') or '').strip(),
                (data.get('color_hex') or '#888888').strip(),
                data.get('remaining_g'), data.get('capacity_g') or 1000,
                (data.get('source_label') or 'Manuel').strip(),
                (data.get('vendor') or '').strip(),
                data.get('price') if data.get('price') not in ('', None) else None,
                data.get('diameter_mm') or 1.75,
                (data.get('notes') or '').strip(),
                (data.get('storage_location') or '').strip(),
            ))
            conn.commit()
            new_id = cur.lastrowid
        finally:
            conn.close()
        return jsonify({"success": True, "id": new_id}), 200
    except Exception as e:
        app_logger.error(f"[API] Erreur non gérée: {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500


def api_update_manual_spool(spool_id):
    data = request.json or {}
    fields, params = [], []
    for key, col in (('name', 'name'), ('material', 'material'), ('color_hex', 'color_hex'),
                      ('remaining_g', 'remaining_g'), ('capacity_g', 'capacity_g'),
                      ('vendor', 'vendor'), ('price', 'price'), ('diameter_mm', 'diameter_mm'),
                      ('notes', 'notes'), ('archived', 'archived'),
                      ('storage_location', 'storage_location')):
        if key in data:
            fields.append(f"{col} = ?")
            params.append(data[key])
    if not fields:
        return jsonify({"error": "Rien à mettre à jour"}), 400
    fields.append("updated_at = CURRENT_TIMESTAMP")
    params.extend([spool_id, session['user_id']])
    try:
        conn = get_db()
        try:
            conn.execute(f"UPDATE manual_filament_spools SET {', '.join(fields)} WHERE id=? AND user_id=?", params)
            conn.commit()
        finally:
            conn.close()
        return jsonify({"success": True}), 200
    except Exception as e:
        app_logger.error(f"[API] Erreur non gérée: {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500


def api_delete_manual_spool(spool_id):
    try:
        conn = get_db()
        try:
            rows = _trash_snapshot(conn, 'manual_filament_spools', 'id = ? AND user_id = ?', (spool_id, session['user_id']))
            tid = None
            if rows:
                r = rows[0]
                label = r.get('name') or ' '.join(str(x) for x in (r.get('material'), r.get('color_hex')) if x) or f"#{spool_id}"
                tid = trash_record(conn, session['user_id'], 'spool', label, {'row': r})
            conn.execute("DELETE FROM manual_filament_spools WHERE id=? AND user_id=?", (spool_id, session['user_id']))
            conn.commit()
        finally:
            conn.close()
        return jsonify({"success": True, "trash_key": f"row:{tid}" if tid else None}), 200
    except Exception as e:
        app_logger.error(f"[API] Erreur non gérée: {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500


_ROUTES = (
    ('/api/files/assign-filament', ['POST'], 'api_assign_filament', ('login_required', )),
    ('/api/files/filament-assignment', ['GET'], 'api_get_filament_assignment', ('login_required', )),
    ('/api/files/unassign-filament', ['POST'], 'api_unassign_filament', ('login_required', )),
    ('/api/filament/manual', ['GET'], 'api_list_manual_spools', ('login_required', )),
    ('/api/filament/manual', ['POST'], 'api_create_manual_spool', ('login_required', )),
    ('/api/filament/manual/<int:spool_id>', ['PUT'], 'api_update_manual_spool', ('login_required', )),
    ('/api/filament/manual/<int:spool_id>', ['DELETE'], 'api_delete_manual_spool', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"{__name__}.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {}
