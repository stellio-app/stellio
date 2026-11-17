"""Stellio — Origine du modèle (lien, auteur, licence, notes) et suppression de fichiers

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `file_origin_delete.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import hashlib
import os
import re
import shutil
import time
import uuid

_REQUIRED = (
    'THUMBNAILS_DIR',
    'TRASH_DIR',
    'TRASH_UNDO_SECONDS',
    '_cleanup_empty_parent_dirs',
    '_get_source_root_paths',
    '_is_path_within_sources',
    '_move_file_to_trash',
    '_purge_expired_trash',
    '_smb_kwargs_for_path',
    '_trash_registry',
    '_trash_registry_lock',
    '_trash_save_manifest',
    'app',
    'app_logger',
    'get_db',
    'invalidate_cache',
    'note_deleted_paths',
    'is_virtual_archive_path',
    'journal_log',
    'jsonify',
    'login_required',
    'request',
    'session',
    'smbclient',
    'split_virtual_archive_path',
)
_OPTIONAL = ()   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('hashlib', 'os', 're', 'shutil', 'time', 'uuid', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
THUMBNAILS_DIR = None
TRASH_DIR = None
TRASH_UNDO_SECONDS = None
_cleanup_empty_parent_dirs = None
_get_source_root_paths = None
_is_path_within_sources = None
_move_file_to_trash = None
_purge_expired_trash = None
_smb_kwargs_for_path = None
journal_log = None
smbclient = None
_trash_registry = None
_trash_registry_lock = None
_trash_save_manifest = None
app = None
app_logger = None
get_db = None
invalidate_cache = None
note_deleted_paths = None
is_virtual_archive_path = None
jsonify = None
login_required = None
request = None
session = None
split_virtual_archive_path = None


# ── Origine du modèle : lien d'origine, auteur, licence, notes ──
# Longueurs max par champ -> code d'erreur « <code>_too_long » attendu par script.js
_ORIGIN_LIMITS = (('source_url', 'url', 500), ('author', 'author', 120), ('license', 'license', 120), ('notes', 'notes', 1000))

def _origin_norm_path(p):
    return (p or '').strip().replace('\\', '/')

def _origin_path_allowed(raw_path, user_id):
    if is_virtual_archive_path(raw_path):
        raw_path, _ = split_virtual_archive_path(raw_path)
    native = raw_path.replace('/', '\\') if os.name == 'nt' else raw_path.replace('\\', '/')
    return _is_path_within_sources(native, user_id)

def api_get_file_origin():
    try:
        raw = (request.args.get('path') or '').strip()
        if not raw:
            return jsonify({"error": "Chemin requis"}), 400
        file_path = _origin_norm_path(raw)
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT source_url, author, license, notes, from_download, downloaded_at, platform "
                "FROM file_origins WHERE file_path=? AND user_id=?",
                (file_path, session['user_id'])
            ).fetchone()
            dl = conn.execute(
                "SELECT source_url, platform, downloaded_at FROM download_history "
                "WHERE user_id=? AND REPLACE(file_path, char(92), '/') = ? "
                "ORDER BY downloaded_at DESC LIMIT 1",
                (session['user_id'], file_path)
            ).fetchone()
        finally:
            conn.close()

        out = {
            "source_url": "", "author": "", "license": "", "notes": "",
            "from_download": False, "downloaded_at": None, "platform": ""
        }
        if row:
            out.update({
                "source_url": row["source_url"] or "", "author": row["author"] or "",
                "license": row["license"] or "", "notes": row["notes"] or "",
                "from_download": bool(row["from_download"]),
                "downloaded_at": row["downloaded_at"], "platform": row["platform"] or ""
            })
        if dl:
            out["from_download"] = True
            out["source_url"] = out["source_url"] or (dl["source_url"] or "")
            out["downloaded_at"] = out["downloaded_at"] or dl["downloaded_at"]
            out["platform"] = out["platform"] or (dl["platform"] or "")
        return jsonify(out), 200
    except Exception as e:
        app_logger.error(f"[ORIGIN] Erreur lecture: {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500

def api_set_file_origin():
    try:
        data = request.get_json(silent=True) or {}
        raw = (data.get('path') or '').strip()
        if not raw:
            return jsonify({"error": "Chemin requis"}), 400
        if not _origin_path_allowed(raw, session['user_id']):
            app_logger.warning(f"[SECURITY] Origine : chemin hors sources refusé: {raw}")
            return jsonify({"error": "Ce fichier n'appartient à aucune source configurée"}), 403

        values = {}
        for key, code, limit in _ORIGIN_LIMITS:
            val = re.sub(r'[\x00-\x1f\x7f]', ' ', str(data.get(key) or '')).strip() if key != 'notes' \
                else re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', str(data.get(key) or '')).strip()
            if len(val) > limit:
                return jsonify({"error": f"{code}_too_long"}), 400
            values[key] = val
        if values['source_url'] and not re.match(r'^https?://\S+$', values['source_url'], re.IGNORECASE):
            return jsonify({"error": "url_invalid"}), 400

        file_path = _origin_norm_path(raw)
        conn = get_db()
        try:
            existing = conn.execute(
                "SELECT from_download FROM file_origins WHERE file_path=? AND user_id=?",
                (file_path, session['user_id'])
            ).fetchone()
            if not any(values.values()) and not (existing and existing["from_download"]):
                conn.execute("DELETE FROM file_origins WHERE file_path=? AND user_id=?", (file_path, session['user_id']))
            else:
                conn.execute(
                    """INSERT INTO file_origins (file_path, user_id, source_url, author, license, notes, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                       ON CONFLICT(file_path, user_id) DO UPDATE SET
                           source_url=excluded.source_url, author=excluded.author,
                           license=excluded.license, notes=excluded.notes,
                           updated_at=CURRENT_TIMESTAMP""",
                    (file_path, session['user_id'], values['source_url'], values['author'],
                     values['license'], values['notes'])
                )
            conn.commit()
        finally:
            conn.close()
        return jsonify({"success": True}), 200
    except Exception as e:
        app_logger.error(f"[ORIGIN] Erreur enregistrement: {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500

def _follow_file_origin(old_path, new_path):
    """Fait suivre l'origine d'un fichier renommé ou déplacé (table file_origins).
    Si le fichier vient d'un téléchargement, le lien d'origine et la date sont
    recopiés sur le nouveau chemin (download_history reste indexé sur l'ancien).
    Ne doit jamais faire échouer l'opération de renommage / déplacement."""
    try:
        old_n = _origin_norm_path(old_path)
        new_n = _origin_norm_path(new_path)
        if not old_n or not new_n or old_n == new_n:
            return
        conn = get_db()
        try:
            conn.execute("DELETE FROM file_origins WHERE file_path=?", (new_n,))
            conn.execute(
                "UPDATE file_origins SET file_path=?, updated_at=CURRENT_TIMESTAMP WHERE file_path=?",
                (new_n, old_n)
            )
            seen_users = set()
            for dl in conn.execute(
                "SELECT user_id, source_url, platform, downloaded_at FROM download_history "
                "WHERE REPLACE(file_path, char(92), '/') = ? ORDER BY downloaded_at DESC",
                (old_n,)
            ).fetchall():
                if dl["user_id"] in seen_users:
                    continue
                seen_users.add(dl["user_id"])
                conn.execute(
                    """INSERT INTO file_origins (file_path, user_id, source_url, from_download, downloaded_at, platform, updated_at)
                       VALUES (?, ?, ?, 1, ?, ?, CURRENT_TIMESTAMP)
                       ON CONFLICT(file_path, user_id) DO UPDATE SET
                           from_download=1,
                           source_url=CASE WHEN file_origins.source_url='' THEN excluded.source_url ELSE file_origins.source_url END,
                           downloaded_at=COALESCE(file_origins.downloaded_at, excluded.downloaded_at),
                           platform=CASE WHEN file_origins.platform='' THEN excluded.platform ELSE file_origins.platform END""",
                    (new_n, dl["user_id"], dl["source_url"] or '', dl["downloaded_at"], dl["platform"] or '')
                )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        app_logger.warning(f"[ORIGIN] Suivi de l'origine ignoré ({old_path} → {new_path}): {e}")

# ── Fichiers sur un partage réseau (SMB) : accès avec les identifiants de la source, pas ceux de la session système ──
def _is_unc(path):
    return path.startswith('//') or path.startswith('\\\\')


def _smb_creds(path):
    kw = _smb_kwargs_for_path(session['user_id'], path.replace('\\', '/'))
    if kw is None:
        raise PermissionError("Source réseau introuvable pour ce fichier")
    return kw


def _is_existing_file(path):
    if _is_unc(path):
        try:
            return bool(smbclient.path.isfile(path.replace('\\', '/'), **_smb_creds(path)))
        except PermissionError:
            raise
        except Exception:
            return False
    return os.path.exists(path) and os.path.isfile(path)


def _drop_thumbs(norm_path):
    thumb_filename = hashlib.md5(norm_path.replace('\\', '/').encode()).hexdigest()
    for ext in ['.webp', '.png', '.jpg']:
        thumb_path = os.path.join(THUMBNAILS_DIR, thumb_filename + ext)
        if os.path.exists(thumb_path):
            try:
                os.remove(thumb_path)
            except Exception as e:
                app_logger.warning(f"[DELETE] Erreur suppression miniature: {e}")


def _trash_any(path, batch_id):
    """Déplace un fichier vers la corbeille de Stellio (local ou partage réseau : copie locale puis suppression sur le partage)."""
    if not _is_unc(path):
        return _move_file_to_trash(path, batch_id)
    kw = _smb_creds(path)
    smb_path = path.replace('\\', '/')
    batch_dir = os.path.join(TRASH_DIR, batch_id)
    os.makedirs(batch_dir, exist_ok=True)
    filename = os.path.basename(smb_path)
    base, ext = os.path.splitext(filename)
    trashed = os.path.join(batch_dir, filename)
    n = 1
    while os.path.exists(trashed):
        trashed = os.path.join(batch_dir, f"{base}_{n}{ext}")
        n += 1
    with smbclient.open_file(smb_path, mode='rb', **kw) as src, open(trashed, 'wb') as dst:
        shutil.copyfileobj(src, dst)
    smbclient.remove(smb_path, **kw)
    journal_log('delete', filename, smb_path, trashed, batch_id=batch_id)
    return trashed



def api_delete_file():
    try:
        _purge_expired_trash()
        data = request.json
        file_path = data.get('file_path', '').strip()
        if not file_path:
            return jsonify({"error": "Chemin du fichier requis"}), 400

        if is_virtual_archive_path(file_path):
            archive_path, internal_path = split_virtual_archive_path(file_path)
            return jsonify({
                "error": f"Ce fichier est à l'intérieur de l'archive '{os.path.basename(archive_path)}' — la suppression de fichiers individuels dans une archive n'est pas prise en charge.",
                "in_archive": True
            }), 400

        file_path = file_path.replace('/', '\\') if os.name == 'nt' else file_path.replace('\\', '/')

        if not _is_existing_file(file_path):
            return jsonify({"error": "Fichier introuvable"}), 404

        if not _is_path_within_sources(file_path, session['user_id']):
            app_logger.warning(f"[SECURITY] Tentative de suppression hors sources: {file_path}")
            return jsonify({"error": "Ce fichier n'appartient à aucune source configurée"}), 403

        filename = os.path.basename(file_path.replace('\\', '/'))

        batch_id = uuid.uuid4().hex
        trashed_path = _trash_any(file_path, batch_id)
        _drop_thumbs(file_path)      # les miniatures ne sont retirées qu'une fois le fichier réellement supprimé
        with _trash_registry_lock:
            _trash_registry[batch_id] = {
                "created_at": time.time(),
                "user_id": session['user_id'],
                "entries": [{"original": file_path, "trashed": trashed_path}],
            }
        _trash_save_manifest(batch_id)
        app_logger.info(f"[DELETE] ✅ Fichier déplacé vers la corbeille: {filename} (lot {batch_id})")

        try:
            if not _is_unc(file_path):
                _cleanup_empty_parent_dirs(file_path, stop_at_paths=_get_source_root_paths(session['user_id']))
        except Exception as e:
            app_logger.warning(f"[DELETE] Nettoyage dossier vide ignoré: {e}")

        note_deleted_paths([file_path])
        invalidate_cache()

        return jsonify({
            "success": True,
            "message": f"Fichier '{filename}' supprimé avec succès",
            "batch_id": batch_id,
            "undo_seconds": TRASH_UNDO_SECONDS,
        }), 200

    except PermissionError:
        app_logger.error(f"[DELETE] Permission refusée: {file_path}")
        return jsonify({"error": "Permission refusée. Le fichier est peut-être utilisé."}), 403
    except Exception as e:
        app_logger.error(f"[DELETE] Erreur: {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500

def api_delete_files_batch():
    try:
        _purge_expired_trash()
        data = request.json or {}
        file_paths = data.get('file_paths') or []
        if not file_paths:
            return jsonify({"error": "Aucun fichier à supprimer"}), 400

        batch_id = uuid.uuid4().hex
        trash_entries = []
        deleted, errors = [], []
        source_roots = _get_source_root_paths(session['user_id'])
        for raw_path in file_paths:
            file_path = (raw_path or '').strip()
            if not file_path:
                continue
            try:
                if is_virtual_archive_path(file_path):
                    archive_path, _ = split_virtual_archive_path(file_path)
                    errors.append({
                        "path": file_path,
                        "error": f"Dans l'archive '{os.path.basename(archive_path)}' — non supprimable individuellement"
                    })
                    continue

                norm_path = file_path.replace('/', '\\') if os.name == 'nt' else file_path.replace('\\', '/')
                if not _is_existing_file(norm_path):
                    errors.append({"path": file_path, "error": "Fichier introuvable"})
                    continue

                if not _is_path_within_sources(norm_path, session['user_id']):
                    app_logger.warning(f"[SECURITY] Tentative de suppression hors sources: {norm_path}")
                    errors.append({"path": file_path, "error": "N'appartient à aucune source configurée"})
                    continue

                filename = os.path.basename(norm_path.replace('\\', '/'))
                trashed_path = _trash_any(norm_path, batch_id)
                _drop_thumbs(norm_path)      # miniatures retirées seulement si la suppression a réussi
                trash_entries.append({"original": norm_path, "trashed": trashed_path})
                deleted.append(filename)
                try:
                    if not _is_unc(norm_path):
                        _cleanup_empty_parent_dirs(norm_path, stop_at_paths=source_roots)
                except Exception as e:
                    app_logger.warning(f"[DELETE] Nettoyage dossier vide ignoré: {e}")
            except PermissionError:
                errors.append({"path": file_path, "error": "Permission refusée (fichier peut-être utilisé)"})
            except Exception as e:
                errors.append({"path": file_path, "error": str(e)})

        if deleted:
            note_deleted_paths([e['original'] for e in trash_entries])
            invalidate_cache()
            app_logger.info(f"[DELETE] ✅ {len(deleted)} fichier(s) déplacé(s) vers la corbeille (lot {batch_id})")
            with _trash_registry_lock:
                _trash_registry[batch_id] = {
                    "created_at": time.time(),
                    "user_id": session['user_id'],
                    "entries": trash_entries,
                }
            _trash_save_manifest(batch_id)

        return jsonify({
            "success": len(errors) == 0,
            "deleted_count": len(deleted),
            "deleted": deleted,
            "errors": errors,
            "batch_id": batch_id if deleted else None,
            "undo_seconds": TRASH_UNDO_SECONDS,
        }), 200
    except Exception as e:
        app_logger.error(f"[DELETE] Erreur suppression en lot: {e}")
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de la requête"}), 500


_ROUTES = (
    ('/api/files/origin', ['GET'], 'api_get_file_origin', ('login_required', )),
    ('/api/files/origin', ['POST'], 'api_set_file_origin', ('login_required', )),
    ('/api/files/delete', ['POST'], 'api_delete_file', ('login_required', )),
    ('/api/files/delete-batch', ['POST'], 'api_delete_files_batch', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"file_origin_delete.init : services manquants : {missing}")
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
