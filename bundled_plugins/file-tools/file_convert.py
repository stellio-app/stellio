"""Stellio — Réparation de maillage et convertisseur de formats 3D

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `file_convert.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import hashlib
import os
import shutil
import threading
import time
import uuid

_REQUIRED = (
    'CONVERT_SOURCE_FORMATS',
    '_load_mesh_for_conversion',
    'FuturesTimeoutError',
    'HAS_PYMESHFIX',
    'SUPPORTED_EXTENSIONS',
    'THUMBNAILS_DIR',
    'ThreadPoolExecutor',
    '_JobCancelled',
    '_convert_jobs',
    '_is_path_within_sources',
    '_journal_convert_results',
    '_purge_split_jobs',
    '_queue_thumb_task',
    '_split_jobs_lock',
    'app',
    'app_logger',
    'get_integrity_timeout',
    'invalidate_cache',
    'jsonify',
    'load_3mf_mesh',
    'load_model_mesh',
    'login_required',
    'mark_repair_attempted',
    'request',
    'session',
    'trimesh',
)
_OPTIONAL = ('pymeshfix', )   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('hashlib', 'os', 'shutil', 'threading', 'time', 'uuid', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
pymeshfix = None
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
FuturesTimeoutError = None
HAS_PYMESHFIX = None
SUPPORTED_EXTENSIONS = None
CONVERT_SOURCE_FORMATS = None
_load_mesh_for_conversion = None
THUMBNAILS_DIR = None
ThreadPoolExecutor = None
_JobCancelled = None
_convert_jobs = None
_is_path_within_sources = None
_journal_convert_results = None
_purge_split_jobs = None
_queue_thumb_task = None
_split_jobs_lock = None
app = None
app_logger = None
get_integrity_timeout = None
invalidate_cache = None
jsonify = None
load_3mf_mesh = None
load_model_mesh = None
login_required = None
mark_repair_attempted = None
request = None
session = None
trimesh = None


def api_repair_file():
    data = request.json
    file_path = data.get('path')
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "Fichier non trouvé"}), 404
    if not _is_path_within_sources(file_path, session['user_id']):
        app_logger.warning(f"[SECURITY] Tentative de réparation hors sources: {file_path}")
        return jsonify({"error": "Ce fichier n'appartient à aucune source configurée"}), 403

    def _load_mesh_to_repair():
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.3mf':
            return load_3mf_mesh(file_path)
        else:
            return load_model_mesh(file_path, ext)

    try:
        ext = os.path.splitext(file_path)[1].lower()
        load_timeout = get_integrity_timeout(file_path)
        _load_pool = ThreadPoolExecutor(max_workers=1)
        try:
            _load_future = _load_pool.submit(_load_mesh_to_repair)
            try:
                mesh = _load_future.result(timeout=load_timeout)
            except FuturesTimeoutError:
                return jsonify({"error": f"Délai dépassé lors de la lecture du fichier (>{load_timeout:.0f}s). "
                                          f"Le fichier semble valide mais le partage réseau est trop lent — "
                                          f"réessayez, ou copiez-le en local avant de le réparer."}), 504
        finally:
            _load_pool.shutdown(wait=False)

        if isinstance(mesh, trimesh.Scene):
            geoms = [m for m in mesh.geometry.values() if hasattr(m, 'vertices') and len(m.vertices) > 0]
            if not geoms: return jsonify({"error": "Maillage vide"}), 400
            mesh = trimesh.util.concatenate(geoms)

        def _winding_ok(m):
            try:
                return bool(m.is_winding_consistent)
            except Exception:
                return True

        was_watertight_initially = mesh.is_watertight
        before_stats = {
            "triangle_count": len(mesh.faces),
            "vertex_count": len(mesh.vertices),
            "watertight": was_watertight_initially,
            "file_size": os.path.getsize(file_path),
        }
        if was_watertight_initially and _winding_ok(mesh):
            return jsonify({"success": True, "message": "Déjà valide (watertight)"})

        backup_path = file_path + ".bak"
        if not os.path.exists(backup_path):
            shutil.copy2(file_path, backup_path)

        if was_watertight_initially:
            trimesh.repair.fix_winding(mesh)
            trimesh.repair.fix_normals(mesh, multibody=True)
        else:
            _repair_mesh_inplace(mesh)
            if not mesh.is_watertight:
                trimesh.repair.fix_winding(mesh)
                trimesh.repair.fill_holes(mesh)
                trimesh.repair.fix_normals(mesh)

            if not mesh.is_watertight and HAS_PYMESHFIX:
                try:
                    fixer = pymeshfix.MeshFix(mesh.vertices.copy(), mesh.faces.copy())
                    try:
                        fixer.repair(verbose=False)
                    except TypeError:
                        fixer.repair()
                    if fixer.v is not None and len(fixer.v) > 0:
                        mesh = trimesh.Trimesh(vertices=fixer.v, faces=fixer.f, process=True)
                except Exception as e:
                    app_logger.warning(f"[Repair] Passe pymeshfix échouée pour {file_path}: {e}")

        still_broken = not (mesh.is_watertight and _winding_ok(mesh))
        after_stats = {
            "triangle_count": len(mesh.faces),
            "vertex_count": len(mesh.vertices),
            "watertight": mesh.is_watertight,
        }

        mark_repair_attempted(file_path)

        if ext in ['.stl', '.obj']:
            mesh.export(file_path, file_type=ext[1:])
        else:
            out_path = os.path.splitext(file_path)[0] + "_repaired.stl"
            mesh.export(out_path, file_type='stl')
            invalidate_cache()
            after_stats["file_size"] = os.path.getsize(out_path)
            if still_broken:
                return jsonify({
                    "success": True, "partial": True, "watertight": False,
                    "message": "Exporté en STL, mais le maillage présente encore des problèmes non résolus automatiquement (géométrie complexe non-manifold)",
                    "new_path": out_path, "before": before_stats, "after": after_stats,
                })
            return jsonify({"success": True, "watertight": True, "message": "Exporté en STL réparé (format original non supporté)", "new_path": out_path, "before": before_stats, "after": after_stats})

        invalidate_cache()
        after_stats["file_size"] = os.path.getsize(file_path)

        if still_broken:
            return jsonify({
                "success": True, "partial": True, "watertight": False,
                "message": "Réparation partielle : le maillage a été nettoyé mais présente encore des problèmes non résolus automatiquement (trous complexes ou géométrie non-manifold). Une sauvegarde a été conservée (.bak).",
                "before": before_stats, "after": after_stats,
            })

        return jsonify({"success": True, "watertight": True, "message": "Réparé avec succès", "before": before_stats, "after": after_stats})

    except Exception as e:
        if type(e).__name__ == 'ModelTooLargeError':       # trop gros pour la mémoire : l'interface propose la version allégée
            app_logger.info(f"[Repair] Refusé : {e}")
            low = file_path.lower().endswith('.stl')
            return jsonify({"error": str(e) + (" Créez d'abord une version allégée du fichier." if low else ''), "code": "model_too_large", "lightenable": low}), 413
        app_logger.error(f"[Repair] Erreur: {e}")
        return jsonify({"error": f"Échec: {str(e)}"}), 500



# format de sortie demandé → (type d'export trimesh, extension du fichier créé)
CONVERT_TARGET_FORMATS = {
    'stl': ('stl', 'stl'), 'stl_ascii': ('stl_ascii', 'stl'), 'obj': ('obj', 'obj'), '3mf': ('3mf', '3mf'),
    'ply': ('ply', 'ply'), 'off': ('off', 'off'), 'glb': ('glb', 'glb'),
}

CONVERT_UNIT_TO_MM = {
    'mm': 1.0,
    'cm': 10.0,
    'm': 1000.0,
    'in': 25.4,
    'ft': 304.8,
}

def _repair_mesh_inplace(mesh):
    repaired = {'normals': False, 'holes_filled': False, 'cleaned': False}
    try:
        mesh.merge_vertices()
    except Exception:
        pass
    try:
        trimesh.repair.fix_normals(mesh, multibody=True)
        repaired['normals'] = True
    except Exception:
        pass
    try:
        was_watertight = mesh.is_watertight
        trimesh.repair.fill_holes(mesh)
        repaired['holes_filled'] = (not was_watertight) and mesh.is_watertight
    except Exception:
        pass
    try:
        mesh.update_faces(mesh.nondegenerate_faces())
        mesh.update_faces(mesh.unique_faces())
        repaired['cleaned'] = True
    except Exception:
        pass
    return repaired


def _convert_single_file(file_path, target_format, delete_original, repair=False, source_unit='mm'):
    target_format = (target_format or '').lower().lstrip('.')
    if target_format not in CONVERT_TARGET_FORMATS:
        return {"success": False, "path": file_path, "error": "Format de sortie non supporté"}

    if not file_path or not os.path.exists(file_path):
        return {"success": False, "path": file_path, "error": "Fichier non trouvé"}

    src_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
    if src_ext not in CONVERT_SOURCE_FORMATS:
        return {"success": False, "path": file_path, "error": "Format d'entrée non supporté"}
    export_type, target_ext = CONVERT_TARGET_FORMATS[target_format]
    if src_ext == target_ext and target_format != 'stl_ascii':
        return {"success": False, "path": file_path, "error": "Le fichier est déjà dans ce format"}

    try:
        mesh = _load_mesh_for_conversion(file_path)

        repaired_info = None
        if repair:
            repaired_info = _repair_mesh_inplace(mesh)

        scale_factor = CONVERT_UNIT_TO_MM.get((source_unit or 'mm').lower(), 1.0)
        if scale_factor != 1.0:
            mesh.apply_scale(scale_factor)

        base_dir = os.path.dirname(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        out_path = os.path.join(base_dir, f"{base_name}.{target_ext}")

        counter = 1
        while os.path.exists(out_path):
            out_path = os.path.join(base_dir, f"{base_name} ({counter}).{target_ext}")
            counter += 1

        mesh.export(out_path, file_type=export_type)

        original_size = os.path.getsize(file_path)
        new_size = os.path.getsize(out_path) if os.path.exists(out_path) else 0
        size_reduction_pct = round((1 - new_size / original_size) * 100, 1) if original_size > 0 else 0

        deleted_original = False
        if delete_original:
            try:
                os.remove(file_path)
                deleted_original = True
                normalized_old = file_path.replace('\\', '/')
                old_thumb = os.path.join(THUMBNAILS_DIR, hashlib.md5(normalized_old.encode()).hexdigest() + '.webp')
                if os.path.exists(old_thumb):
                    os.remove(old_thumb)
            except Exception as e:
                app_logger.warning(f"[Convert] Suppression de l'original impossible pour {os.path.basename(file_path)}: {e}")

        invalidate_cache()

        normalized_new = out_path.replace('\\', '/')
        new_thumb_path = os.path.join(THUMBNAILS_DIR, hashlib.md5(normalized_new.encode()).hexdigest() + '.webp')
        _queue_thumb_task(out_path, new_thumb_path, priority='high')

        app_logger.info(
            f"[CONVERT] {os.path.basename(file_path)} → {os.path.basename(out_path)} "
            f"(original {'supprimé' if deleted_original else 'conservé'}"
            f"{', réparé' if repair else ''}"
            f"{f', échelle x{scale_factor}' if scale_factor != 1.0 else ''})"
        )
        return {
            "success": True, "path": file_path, "new_path": out_path,
            "deleted_original": deleted_original,
            "original_size": original_size, "new_size": new_size,
            "size_reduction_pct": size_reduction_pct,
            "repaired": repaired_info,
        }

    except Exception as e:
        app_logger.error(f"[Convert] Erreur pour {os.path.basename(file_path)}: {e}")
        return {"success": False, "path": file_path, "error": f"Échec de la conversion : {str(e)}"}

def api_convert_file():
    data = request.json or {}
    file_path = data.get('path')
    target_format = data.get('target_format')
    delete_original = bool(data.get('delete_original', False))
    repair = bool(data.get('repair', False))
    source_unit = data.get('source_unit', 'mm')

    if not file_path or not _is_path_within_sources(file_path, session['user_id']):
        app_logger.warning(f"[SECURITY] Tentative de conversion hors sources: {file_path}")
        return jsonify({"error": "Ce fichier n'appartient à aucune source configurée"}), 403

    result = _convert_single_file(file_path, target_format, delete_original, repair=repair, source_unit=source_unit)
    if result.get('success'):
        return jsonify(result)
    return jsonify({"error": result.get('error', 'Échec de la conversion')}), 400

def api_convert_file_batch():
    data = request.json or {}
    paths = data.get('paths')
    target_format = data.get('target_format')
    delete_original = bool(data.get('delete_original', False))
    repair = bool(data.get('repair', False))
    source_unit = data.get('source_unit', 'mm')

    if not paths or not isinstance(paths, list):
        return jsonify({"error": "Liste de chemins requise"}), 400

    for p in paths:
        if not _is_path_within_sources(p, session['user_id']):
            app_logger.warning(f"[SECURITY] Tentative de conversion batch hors sources: {p}")
            return jsonify({"error": "Un ou plusieurs fichiers n'appartiennent à aucune source configurée"}), 403

    if data.get('async'):
        _purge_split_jobs()
        job_id = uuid.uuid4().hex
        job = {'state': 'running', 'user_id': session['user_id'], 'done': 0, 'current': 1, 'total': len(paths),
               'results': [], 'converted': 0, 'error': None, 'finished': None}
        with _split_jobs_lock:
            _convert_jobs[job_id] = job

        def _run_convert_job():
            try:
                for idx, p in enumerate(paths, start=1):
                    with _split_jobs_lock:
                        if job.get('cancel'):
                            raise _JobCancelled()
                        job['current'] = idx
                    r = _convert_single_file(p, target_format, delete_original, repair=repair, source_unit=source_unit)
                    _journal_convert_results([r], user_id=job['user_id'])
                    with _split_jobs_lock:
                        job['results'].append(r)
                        job['done'] = idx
                        if r.get('success'):
                            job['converted'] += 1
                app_logger.info(f"[CONVERT-BATCH] {job['converted']}/{len(paths)} fichier(s) converti(s) avec succès")
                with _split_jobs_lock:
                    job['state'] = 'done'
            except _JobCancelled:
                app_logger.info(f"[CONVERT-BATCH] Annulée par l'utilisateur après {job['done']}/{len(paths)} fichier(s)")
                with _split_jobs_lock:
                    job['state'] = 'cancelled'
            except Exception as e:
                app_logger.error(f"[CONVERT-BATCH] {e}")
                with _split_jobs_lock:
                    job['state'] = 'error'
                    job['error'] = "Une erreur interne est survenue lors de la conversion"
            finally:
                with _split_jobs_lock:
                    job['finished'] = time.time()

        threading.Thread(target=_run_convert_job, daemon=True, name='convert-batch').start()
        return jsonify({"job_id": job_id, "total": len(paths)}), 202

    results = [_convert_single_file(p, target_format, delete_original, repair=repair, source_unit=source_unit) for p in paths]
    _journal_convert_results(results)
    succeeded = sum(1 for r in results if r.get('success'))
    app_logger.info(f"[CONVERT-BATCH] {succeeded}/{len(results)} fichier(s) converti(s) avec succès")
    return jsonify({"success": True, "results": results, "converted": succeeded, "total": len(results)})

def api_convert_file_batch_status(job_id):
    with _split_jobs_lock:
        job = _convert_jobs.get(job_id)
        if not job or job.get('user_id') != session['user_id']:
            return jsonify({"error": "Tâche introuvable"}), 404
        out = {k: job.get(k) for k in ('state', 'done', 'current', 'total', 'converted', 'error')}
        if job.get('state') != 'running':
            out['results'] = list(job.get('results') or [])
    return jsonify(out)

def api_convert_file_batch_cancel(job_id):
    """Arrête la conversion en lot après le fichier en cours ; les fichiers déjà convertis restent."""
    with _split_jobs_lock:
        job = _convert_jobs.get(job_id)
        if not job or job.get('user_id') != session['user_id']:
            return jsonify({"error": "Tâche introuvable"}), 404
        if job.get('state') == 'running':
            job['cancel'] = True
    return jsonify({"success": True})


_ROUTES = (
    ('/api/files/repair', ['POST'], 'api_repair_file', ('login_required', )),
    ('/api/files/convert', ['POST'], 'api_convert_file', ('login_required', )),
    ('/api/files/convert-batch', ['POST'], 'api_convert_file_batch', ('login_required', )),
    ('/api/files/convert-batch/<job_id>', ['GET'], 'api_convert_file_batch_status', ('login_required', )),
    ('/api/files/convert-batch/<job_id>/cancel', ['POST'], 'api_convert_file_batch_cancel', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"file_convert.init : services manquants : {missing}")
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
