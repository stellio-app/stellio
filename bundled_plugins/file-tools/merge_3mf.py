"""Stellio — fusion de plusieurs modèles en un seul fichier 3MF (v1.1.3)

À partir d'une sélection de modèles (STL, 3MF, OBJ…), crée UN fichier 3MF :
  • si toutes les pièces tiennent sur un plateau → un seul plateau ;
  • sinon → un fichier à plusieurs plateaux (les pièces sont réparties automatiquement).
Le fichier suit la structure « plateaux » des 3MF Bambu Studio / OrcaSlicer (`Metadata/model_settings.config`), que
Stellio sait déjà lire pour détecter les plateaux. Un slicer sans notion de plateaux (PrusaSlicer) affiche toutes les pièces.

Module séparé de main.py (même schéma que collections_sets.py) : main.py appelle `merge_3mf.init(globals())`.
"""
import io
import math
import os
import re
import secrets
import zipfile
from xml.sax.saxutils import quoteattr

_REQUIRED = (
    'DATA_DIR',
    'HAS_SHAPELY',
    '_get_polygon_footprint',
    '_is_path_within_sources',
    '_load_mesh_for_conversion',
    '_smb_kwargs_for_path',
    '_pack_footprints',
    '_pack_polygons',
    'app',
    'app_logger',
    'get_db',
    'invalidate_cache',
    'jsonify',
    'load_3mf_mesh',
    'load_model_mesh',
    'login_required',
    'np',
    'request',
    'session',
    'smbclient',
    'tra',
    'trimesh',
)
_OPTIONAL = ()
_OVERRIDABLE = ('os', 'secrets', 'math')

_MAIN = {}
DATA_DIR = None
HAS_SHAPELY = None
_get_polygon_footprint = None
_is_path_within_sources = None
_load_mesh_for_conversion = None
_smb_kwargs_for_path = None
load_3mf_mesh = None
load_model_mesh = None
smbclient = None
_pack_footprints = None
_pack_polygons = None
app = None
app_logger = None
get_db = None
invalidate_cache = None
jsonify = None
login_required = None
np = None
request = None
session = None
tra = None
trimesh = None

MAX_PIECES = 200
PLATE_GAP = 0.2   # écart logique entre plateaux dans l'espace Bambu (20 % de la taille du plateau)


def _plate_columns(count):
    """Nombre de colonnes de la grille de plateaux (même règle que Bambu Studio)."""
    value = math.sqrt(count)
    rounded = round(value)
    return rounded + 1 if value > rounded else max(1, rounded)


def _plate_origin(index, count, bed_w, bed_d):
    cols = _plate_columns(count)
    row, col = divmod(index, cols)
    return col * bed_w * (1 + PLATE_GAP), -row * bed_d * (1 + PLATE_GAP)


def _safe_name(path):
    base = os.path.splitext(os.path.basename(path))[0]
    return re.sub(r'[\x00-\x1f<>]', '', base).strip() or 'piece'


def build_3mf(plates, bed_w, bed_d, out_path):
    """Écrit le 3MF. `plates` = liste de plateaux ; chaque plateau = liste de dict
    {name, vertices (Nx3, centrés en XY, z ≥ 0), faces (Mx3), cx, cy (centre dans le plateau, mm)}."""
    count = len(plates)
    objects_xml, build_xml, config_objects, config_plates = [], [], [], []
    obj_id = 0
    for p_idx, pieces in enumerate(plates):
        ox, oy = _plate_origin(p_idx, count, bed_w, bed_d)
        instances = []
        for piece in pieces:
            obj_id += 1
            v = piece['vertices']
            f = piece['faces']
            verts = ''.join(f'<vertex x="{x:.5f}" y="{y:.5f}" z="{z:.5f}"/>' for x, y, z in v)
            tris = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in f)
            name = quoteattr(piece['name'])
            objects_xml.append(f'<object id="{obj_id}" name={name} type="model"><mesh><vertices>{verts}</vertices>'
                               f'<triangles>{tris}</triangles></mesh></object>')
            tx, ty = ox + piece['cx'], oy + piece['cy']
            build_xml.append(f'<item objectid="{obj_id}" transform="1 0 0 0 1 0 0 0 1 {tx:.4f} {ty:.4f} 0" printable="1"/>')
            config_objects.append(f'<object id="{obj_id}"><metadata key="name" value={name}/></object>')
            instances.append(f'<model_instance><metadata key="object_id" value="{obj_id}"/>'
                             f'<metadata key="instance_id" value="0"/><metadata key="identify_id" value="{obj_id}"/></model_instance>')
        config_plates.append(f'<plate><metadata key="plater_id" value="{p_idx + 1}"/>'
                             f'<metadata key="plater_name" value=""/><metadata key="locked" value="false"/>'
                             + ''.join(instances) + '</plate>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
             'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" requiredextensions="">\n'
             '<metadata name="Application">Stellio</metadata>\n<metadata name="BambuStudio:3mfVersion">1</metadata>\n'
             '<resources>' + ''.join(objects_xml) + '</resources>\n<build>' + ''.join(build_xml) + '</build>\n</model>')
    config = '<?xml version="1.0" encoding="UTF-8"?>\n<config>' + ''.join(config_objects) + ''.join(config_plates) + '</config>'
    content_types = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
                     '<Default Extension="config" ContentType="text/xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types)
        zf.writestr('_rels/.rels', rels)
        zf.writestr('3D/3dmodel.model', model)
        zf.writestr('Metadata/model_settings.config', config)
    return obj_id


def _pack_plates(meshes, bed_w, bed_d, spacing):
    """Répartit les pièces sur autant de plateaux que nécessaire.
    meshes : {path: mesh posé à (0,0,0)}. Renvoie (plates, too_big) ; plates = liste de listes de
    {path, mesh (déjà placé dans le plateau, repère 0..bed)}."""
    remaining = dict(meshes)
    plates, too_big = [], []
    while remaining:
        items = []
        for path, mesh in remaining.items():
            dims = mesh.bounds[1] - mesh.bounds[0]
            if HAS_SHAPELY:
                items.append({'id': path, 'polygon': _get_polygon_footprint(mesh)})
            else:
                items.append({'id': path, 'w': float(dims[0]) + spacing, 'h': float(dims[1]) + spacing})
        if HAS_SHAPELY:
            placed, unplaced = _pack_polygons(items, bed_w, bed_d, spacing=spacing)
        else:
            placed, unplaced = _pack_footprints(items, bed_w, bed_d, spacing=0)
            for p in placed:
                p['rotation_deg'] = 90 if p.get('rotated') else 0
        if not placed:               # aucune pièce ne tient même seule sur un plateau vide
            too_big.extend(remaining.keys())
            break
        gx0 = min(p['x'] for p in placed)
        gy0 = min(p['y'] for p in placed)
        gx1 = max(p['x'] + p['w'] for p in placed)
        gy1 = max(p['y'] + p['h'] for p in placed)
        dx = (bed_w - (gx1 - gx0)) / 2 - gx0
        dy = (bed_d - (gy1 - gy0)) / 2 - gy0
        plate = []
        for p in placed:
            mesh = remaining.pop(p['id']).copy()
            rot = p.get('rotation_deg') or 0
            if rot:
                mesh.apply_transform(tra.rotation_matrix(np.radians(rot), [0, 0, 1]))
                b = mesh.bounds
                mesh.apply_translation([-b[0][0], -b[0][1], 0])
            off = 0 if HAS_SHAPELY else spacing / 2
            mesh.apply_translation([p['x'] + dx + off, p['y'] + dy + off, 0])
            plate.append({'path': p['id'], 'mesh': mesh})
        plates.append(plate)
        if not unplaced:
            break
    return plates, too_big


def _is_unc(path):
    return path.startswith('//') or path.startswith('\\\\')


def _unc(path):
    return path.replace('\\', '/')


def _load_mesh(path):
    """Maillage d'un fichier local ou d'un partage réseau (SMB : lu en mémoire)."""
    if not _is_unc(path):
        return _load_mesh_for_conversion(path)
    kw = _smb_kwargs_for_path(session['user_id'], path)
    if kw is None:
        raise ValueError("Source réseau introuvable pour ce fichier")
    ext = os.path.splitext(path)[1].lower()
    with smbclient.open_file(_unc(path), mode='rb', share_access='r', **kw) as fh:
        data = fh.read()
    mesh = load_3mf_mesh(data) if ext == '.3mf' else load_model_mesh(data, ext)
    if isinstance(mesh, trimesh.Scene):
        geoms = [m for m in mesh.geometry.values() if hasattr(m, 'vertices') and len(m.vertices) > 0]
        if not geoms:
            raise ValueError("Maillage vide")
        mesh = trimesh.util.concatenate(geoms)
    if mesh is None or mesh.is_empty or len(mesh.vertices) == 0:
        raise ValueError("Maillage vide")
    return mesh


def _clean_filename(name):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', (name or '').strip()).strip('. ')
    if name.lower().endswith('.3mf'):
        name = name[:-4].rstrip('. ')
    return name[:120]


def _dest_dir(paths, source_id, sub_rel):
    """Dossier de sortie : source + sous-dossier choisis dans la fenêtre ; sinon dossier du premier fichier
    (si on peut y écrire) ; sinon dossier de données de Stellio. Les dossiers réseau (SMB) sont acceptés.
    Lève ValueError si le choix est invalide."""
    folder = None
    if source_id:
        conn = get_db()
        try:
            row = conn.execute("SELECT path FROM sources WHERE id = ? AND user_id = ?", (source_id, session['user_id'])).fetchone()
        finally:
            conn.close()
        if not row or not row['path']:
            raise ValueError("Dossier de destination introuvable")
        base = row['path']
        parts = [x for x in (sub_rel or '').replace('\\', '/').strip('/').split('/') if x]
        if any(x in ('.', '..') or re.search(r'[<>:"|?*]', x) for x in parts):
            raise ValueError("Dossier de destination invalide")
        if _is_unc(base):
            folder = '/'.join([_unc(base).rstrip('/')] + parts)
            kw = _smb_kwargs_for_path(session['user_id'], folder)
            if kw is None:
                raise ValueError("Source réseau introuvable pour ce dossier")
            smbclient.makedirs(folder, exist_ok=True, **kw)
        else:
            folder = os.path.join(base, *parts)
            os.makedirs(folder, exist_ok=True)
    if not folder:
        first = paths[0]
        if _is_unc(first):
            folder = _unc(first).rsplit('/', 1)[0]
        else:
            folder = os.path.dirname(first)
            if not (folder and os.path.isdir(folder) and os.access(folder, os.W_OK)):
                folder = os.path.join(DATA_DIR, 'nesting_output')
                os.makedirs(folder, exist_ok=True)
    return folder


def _out_path(folder, name, count):
    base = _clean_filename(name) or f'fusion_{count}_pieces'
    unc = _is_unc(folder)
    kw = (_smb_kwargs_for_path(session['user_id'], folder) or {}) if unc else {}
    join = (lambda n: _unc(folder).rstrip('/') + '/' + n) if unc else (lambda n: os.path.join(folder, n))
    exists = (lambda p: smbclient.path.exists(p, **kw)) if unc else os.path.exists
    candidate = join(base + '.3mf')
    n = 2
    while exists(candidate):
        candidate = join(f'{base}_{n}.3mf')
        n += 1
    return candidate


def _write_output(plates, bed_w, bed_d, out_path):
    if not _is_unc(out_path):
        build_3mf(plates, bed_w, bed_d, out_path)
        return
    kw = _smb_kwargs_for_path(session['user_id'], out_path)
    if kw is None:
        raise ValueError("Source réseau introuvable pour ce dossier")
    buf = io.BytesIO()
    build_3mf(plates, bed_w, bed_d, buf)
    with smbclient.open_file(out_path, mode='wb', **kw) as fh:
        fh.write(buf.getvalue())


def api_merge_3mf():
    data = request.json or {}
    paths = [p for p in (data.get('paths') or []) if isinstance(p, str)]
    try:
        bed_w = float(data.get('bed_width') or 220)
        bed_d = float(data.get('bed_height') or 220)
        bed_z = float(data.get('bed_height_z') or 250)
        spacing = max(float(data.get('spacing') or 3.0), 0.5)
    except (TypeError, ValueError):
        return jsonify({"error": "Dimensions de plateau invalides"}), 400
    if bed_w < 20 or bed_d < 20:
        return jsonify({"error": "Dimensions de plateau invalides"}), 400
    if len(paths) < 2:
        return jsonify({"error": "Sélectionnez au moins 2 fichiers à fusionner"}), 400
    if len(paths) > MAX_PIECES:
        return jsonify({"error": f"Trop de fichiers (maximum {MAX_PIECES})"}), 400

    meshes, errors = {}, []
    for path in paths:
        if not _is_path_within_sources(path, session['user_id']):
            errors.append({"path": path, "error": "Fichier hors des sources de la bibliothèque"})
            continue
        if not _is_unc(path) and not os.path.exists(path):
            errors.append({"path": path, "error": "Fichier introuvable"})
            continue
        try:
            mesh = _load_mesh(path)
            b = mesh.bounds
            if float(b[1][2] - b[0][2]) > bed_z:
                errors.append({"path": path, "error": f"Trop haute pour ce plateau ({round(float(b[1][2] - b[0][2]), 1)} mm > {bed_z} mm)"})
                continue
            mesh.apply_translation([-b[0][0], -b[0][1], -b[0][2]])
            meshes[path] = mesh
        except Exception as e:
            errors.append({"path": path, "error": str(e)})
    if not meshes:
        return jsonify({"error": "Aucun fichier exploitable à fusionner", "errors": errors}), 400

    plates, too_big = _pack_plates(meshes, bed_w, bed_d, spacing)
    for path in too_big:
        errors.append({"path": path, "error": "Trop grande pour ce plateau, même seule"})
    if not plates:
        return jsonify({"error": "Aucune pièce ne tient sur le plateau", "errors": errors}), 400

    out_plates, total, merged_paths = [], 0, []
    for plate in plates:
        pieces = []
        for entry in plate:
            mesh = entry['mesh']
            b = mesh.bounds
            cx, cy = float((b[0][0] + b[1][0]) / 2), float((b[0][1] + b[1][1]) / 2)
            verts = np.asarray(mesh.vertices, dtype=float).copy()
            verts[:, 0] -= cx
            verts[:, 1] -= cy
            merged_paths.append(entry['path'])
            pieces.append({'name': _safe_name(entry['path']), 'vertices': verts, 'faces': np.asarray(mesh.faces), 'cx': cx, 'cy': cy})
        out_plates.append(pieces)
        total += len(pieces)

    try:
        folder = _dest_dir(paths, str(data.get('source_id') or '').strip() or None, data.get('target_subfolder'))
        out_path = _out_path(folder, data.get('filename'), total)
        _write_output(out_plates, bed_w, bed_d, out_path)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app_logger.warning(f"[Fusion 3MF] échec : {e}")
        return jsonify({"error": f"Échec de la création du fichier 3MF : {e}"}), 500
    try:
        invalidate_cache()
    except Exception:
        pass
    return jsonify({
        "output_path": out_path,
        "output_filename": os.path.basename(_unc(out_path)),
        "plate_count": len(out_plates),
        "merged_paths": merged_paths,
        "piece_count": total,
        "plates": [[p['name'] for p in pl] for pl in out_plates],
        "errors": errors,
    }), 200


_ROUTES = (
    ('/api/files/merge-3mf', ['POST'], 'api_merge_3mf', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"merge_3mf.init : services manquants : {missing}")
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
