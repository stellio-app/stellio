"""Stellio — plugin signé « Séparer par couleur » (catalogue stellio-plugins, 1.2.0)

Un 3MF multicolore (Bambu / Orca / PrusaSlicer, matières 3MF, peinture par triangle) → un NOUVEAU 3MF avec un plateau par couleur.
La pièce garde sa position sur chaque plateau et chaque objet porte sa couleur. Le fichier d'origine n'est jamais modifié.
Plugin du catalogue qui déclare `host` : il s'exécute DANS Stellio, donc n'est installé que signé par une clé de confiance (voir docs/plugins.md).
Routes dans l'espace réservé aux plugins : /api/x/split-color/… ; page : split.html (cadre isolé, écriture via le pont `stellio.api(..., 'json', {method:'POST'})`).
"""
import io
import math
import os
import re
import zipfile
from xml.sax.saxutils import quoteattr

_REQUIRED = (
    'DATA_DIR',
    '_is_path_within_sources',
    '_smb_kwargs_for_path',
    '_resolve_3mf_plate_mesh',
    '_thumb_base_rgb',
    'app',
    'app_logger',
    'get_db',
    'invalidate_cache',
    'jsonify',
    'login_required',
    'np',
    'request',
    'session',
    'smbclient',
)
_OPTIONAL = ('CACHE_FILE', '_read_cache_json_safe')
_OVERRIDABLE = ("os", )

_MAIN = {}
DATA_DIR = None
_is_path_within_sources = None
_smb_kwargs_for_path = None
_resolve_3mf_plate_mesh = None
_thumb_base_rgb = None
app = None
app_logger = None
get_db = None
invalidate_cache = None
jsonify = None
login_required = None
np = None
request = None
session = None
smbclient = None
CACHE_FILE = None
_read_cache_json_safe = None

PLATE_GAP = 0.2   # écart logique entre plateaux dans l'espace Bambu (20 % de la taille du plateau)
MAX_COLORS = 24

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


def build_3mf(plates, bed_w, bed_d, out_path, plate_names=None):
    """Écrit le 3MF. `plates` = liste de plateaux ; chaque plateau = liste de dict
    {name, vertices (Nx3, centrés en XY, z ≥ 0), faces (Mx3), cx, cy (centre dans le plateau, mm)}."""
    count = len(plates)
    objects_xml, build_xml, config_objects, config_plates, materials_xml = [], [], [], [], []
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
            pid = ''
            if piece.get('rgb') is not None:     # couleur de la pièce (séparation par couleur) : matière de base 3MF, lue aussi par Stellio
                mat_id = 100000 + obj_id
                r, g_, b_ = (int(x) for x in piece['rgb'])
                materials_xml.append(f'<basematerials id="{mat_id}"><base name="{r:02X}{g_:02X}{b_:02X}" displaycolor="#{r:02X}{g_:02X}{b_:02X}FF"/></basematerials>')
                pid = f' pid="{mat_id}" pindex="0"'
            objects_xml.append(f'<object id="{obj_id}" name={name}{pid} type="model"><mesh><vertices>{verts}</vertices>'
                               f'<triangles>{tris}</triangles></mesh></object>')
            tx, ty = ox + piece['cx'], oy + piece['cy']
            build_xml.append(f'<item objectid="{obj_id}" transform="1 0 0 0 1 0 0 0 1 {tx:.4f} {ty:.4f} 0" printable="1"/>')
            config_objects.append(f'<object id="{obj_id}"><metadata key="name" value={name}/></object>')
            instances.append(f'<model_instance><metadata key="object_id" value="{obj_id}"/>'
                             f'<metadata key="instance_id" value="0"/><metadata key="identify_id" value="{obj_id}"/></model_instance>')
        config_plates.append(f'<plate><metadata key="plater_id" value="{p_idx + 1}"/>'
                             f'<metadata key="plater_name" value={quoteattr((plate_names[p_idx] if plate_names and p_idx < len(plate_names) else "") or "")}/><metadata key="locked" value="false"/>'
                             + ''.join(instances) + '</plate>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
             'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" requiredextensions="">\n'
             '<metadata name="Application">Stellio</metadata>\n<metadata name="BambuStudio:3mfVersion">1</metadata>\n'
             '<resources>' + ''.join(materials_xml) + ''.join(objects_xml) + '</resources>\n<build>' + ''.join(build_xml) + '</build>\n</model>')
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


def _is_unc(path):
    return path.startswith('//') or path.startswith('\\\\')


def _unc(path):
    return path.replace('\\', '/')


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


def _write_output(plates, bed_w, bed_d, out_path, plate_names=None):
    if not _is_unc(out_path):
        build_3mf(plates, bed_w, bed_d, out_path, plate_names)
        return
    kw = _smb_kwargs_for_path(session['user_id'], out_path)
    if kw is None:
        raise ValueError("Source réseau introuvable pour ce dossier")
    buf = io.BytesIO()
    build_3mf(plates, bed_w, bed_d, buf, plate_names)
    with smbclient.open_file(out_path, mode='wb', **kw) as fh:
        fh.write(buf.getvalue())


# ── Séparer par couleur (1.2.0) : un 3MF multicolore → un 3MF avec un plateau par couleur ──

def _hex(rgb):
    return '#%02X%02X%02X' % tuple(int(x) for x in rgb)


def _group_colors(face_rgb, tolerance):
    """Regroupe les faces par couleur. Renvoie (étiquette par face, couleurs [(r,g,b)], effectifs).
    tolerance (0-100) : des couleurs proches (distance RVB ≤ tolérance) sont fusionnées dans la plus fréquente."""
    uniq, inv, counts = np.unique(np.asarray(face_rgb, dtype=np.int32), axis=0, return_inverse=True, return_counts=True)
    inv = np.asarray(inv).reshape(-1)
    order = np.argsort(-counts, kind='stable')
    reps, remap = [], np.zeros(len(uniq), dtype=np.int32)
    for i in order:
        target = None
        if tolerance > 0:
            for k, r in enumerate(reps):
                if float(np.linalg.norm(uniq[i] - uniq[r])) <= tolerance:
                    target = k
                    break
        if target is None:
            reps.append(int(i))
            target = len(reps) - 1
        remap[i] = target
    labels = remap[inv]
    sizes = np.bincount(labels, minlength=len(reps))
    return labels, [tuple(int(x) for x in uniq[r]) for r in reps], [int(x) for x in sizes]


def _load_colored_mesh(path):
    """Maillage 3MF de TOUS les plateaux, avec la couleur de chaque face (metadata['stellio_face_rgb'])."""
    if _resolve_3mf_plate_mesh is None:
        raise ValueError("Lecture des couleurs 3MF indisponible")
    if _is_unc(path):
        kw = _smb_kwargs_for_path(session['user_id'], path)
        if kw is None:
            raise ValueError("Source réseau introuvable pour ce fichier")
        with smbclient.open_file(_unc(path), mode='rb', share_access='r', **kw) as fh:
            source = fh.read()
    else:
        source = path
    mesh = _resolve_3mf_plate_mesh(source, None, True, None)
    if mesh is None or len(getattr(mesh, 'faces', [])) == 0:
        raise ValueError("Maillage 3MF vide ou illisible")
    rgb = mesh.metadata.get('stellio_face_rgb') if hasattr(mesh, 'metadata') else None
    if rgb is None or len(rgb) != len(mesh.faces):
        raise ValueError("Ce 3MF ne contient aucune information de couleur")
    return mesh, np.asarray(rgb)


def split_mesh_by_color(mesh, face_rgb, tolerance=0.0):
    """Une pièce par couleur : [{'rgb', 'vertices', 'faces', 'count'}], de la plus grande à la plus petite."""
    labels, colors, sizes = _group_colors(face_rgb, tolerance)
    verts = np.asarray(mesh.vertices, dtype=float)
    faces = np.asarray(mesh.faces)
    out = []
    for k, rgb in enumerate(colors):
        sel = faces[labels == k]
        used, inv = np.unique(sel, return_inverse=True)
        out.append({'rgb': rgb, 'vertices': verts[used], 'faces': inv.reshape(-1, 3), 'count': int(sizes[k])})
    return out


def api_split_color_3mf():
    data = request.json or {}
    path = data.get('path')
    if not isinstance(path, str) or not path:
        return jsonify({"error": "Sélectionnez un fichier 3MF"}), 400
    if os.path.splitext(path)[1].lower() != '.3mf':
        return jsonify({"error": "Seuls les fichiers 3MF multicolores sont pris en charge"}), 400
    try:
        bed_w = float(data.get('bed_width') or 220)
        bed_d = float(data.get('bed_height') or 220)
        tol = min(max(float(data.get('tolerance') or 0), 0.0), 100.0)
    except (TypeError, ValueError):
        return jsonify({"error": "Paramètres invalides"}), 400
    if bed_w < 20 or bed_d < 20:
        return jsonify({"error": "Dimensions de plateau invalides"}), 400
    if not _is_path_within_sources(path, session['user_id']):
        return jsonify({"error": "Fichier hors des sources de la bibliothèque"}), 400
    if not _is_unc(path) and not os.path.exists(path):
        return jsonify({"error": "Fichier introuvable"}), 404
    try:
        mesh, face_rgb = _load_colored_mesh(path)
        pieces = split_mesh_by_color(mesh, face_rgb, tol)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app_logger.warning(f"[Séparation couleur] lecture impossible : {e}")
        return jsonify({"error": f"Lecture du fichier impossible : {e}"}), 500
    default_rgb = None
    try:
        default_rgb = tuple(_thumb_base_rgb()) if _thumb_base_rgb else None
    except Exception:
        default_rgb = None
    total_faces = sum(p['count'] for p in pieces) or 1
    colors = [{"hex": _hex(p['rgb']), "faces": p['count'], "percent": round(100.0 * p['count'] / total_faces, 1),
               "default": default_rgb is not None and tuple(p['rgb']) == default_rgb} for p in pieces]
    if len(pieces) > MAX_COLORS:
        return jsonify({"error": f"Trop de couleurs distinctes ({len(pieces)}, maximum {MAX_COLORS}) : augmentez la tolérance de regroupement",
                        "colors": colors[:MAX_COLORS], "color_count": len(pieces)}), 400
    if data.get('dry_run'):
        return jsonify({"color_count": len(pieces), "colors": colors}), 200
    if len(pieces) < 2:
        return jsonify({"error": "Une seule couleur détectée : rien à séparer", "colors": colors, "color_count": len(pieces)}), 400

    b = mesh.bounds
    cx, cy, z0 = float((b[0][0] + b[1][0]) / 2), float((b[0][1] + b[1][1]) / 2), float(b[0][2])
    fits = float(b[1][0] - b[0][0]) <= bed_w and float(b[1][1] - b[0][1]) <= bed_d
    base = _safe_name(path)
    plates, names = [], []
    for i, p in enumerate(pieces, 1):
        v = p['vertices'].copy()
        v[:, 0] -= cx
        v[:, 1] -= cy
        v[:, 2] -= z0
        label = f"{base} {_hex(p['rgb'])}"
        plates.append([{'name': label, 'vertices': v, 'faces': p['faces'], 'cx': bed_w / 2.0, 'cy': bed_d / 2.0, 'rgb': p['rgb']}])
        names.append(_hex(p['rgb']))
    try:
        folder = _dest_dir([path], str(data.get('source_id') or '').strip() or None, data.get('target_subfolder'))
        out_path = _out_path(folder, data.get('filename') or f'{base}_couleurs', len(plates))
        _write_output(plates, bed_w, bed_d, out_path, names)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app_logger.warning(f"[Séparation couleur] échec : {e}")
        return jsonify({"error": f"Échec de la création du fichier 3MF : {e}"}), 500
    try:
        invalidate_cache()
    except Exception:
        pass
    return jsonify({
        "output_path": out_path,
        "output_filename": os.path.basename(_unc(out_path)),
        "plate_count": len(plates),
        "colors": colors,
        "too_big": not fits,
    }), 200


def api_split_color_files():
    """Fichiers 3MF de la bibliothèque (cache de Stellio), filtrés par nom : sélecteur de la page du plugin."""
    if session.get('role') == 'viewer':
        return jsonify({"error": "Réservé au compte propriétaire"}), 403
    q = (request.args.get('q') or '').strip().lower()
    files = []
    try:
        data = _read_cache_json_safe() if (CACHE_FILE and _read_cache_json_safe and os.path.exists(CACHE_FILE)) else None
        files = (data or {}).get('files') or []
    except Exception:
        files = []
    out = []
    for f in files:
        p = str(f.get('path') or '')
        name = str(f.get('name') or os.path.basename(p))
        if p.lower().endswith('.3mf') and q in name.lower() and _is_path_within_sources(p, session['user_id']):
            out.append({"path": p, "name": name})
            if len(out) >= 60:
                break
    return jsonify({"files": out})


def _owner_post(fn):
    def wrapper(*a, **k):
        if session.get('role') == 'viewer':
            return jsonify({"error": "Réservé au compte propriétaire"}), 403
        return fn(*a, **k)
    wrapper.__name__ = fn.__name__
    return wrapper


_ROUTES = (
    ('/api/x/split-color/files', ['GET'], 'api_split_color_files', ('login_required', )),
    ('/api/x/split-color/split', ['POST'], 'api_split_color_3mf', ('login_required', '_owner_post')),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"split_color.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint='split_color_' + fname, view_func=view, methods=methods)
    return {}
