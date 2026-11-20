"""Stellio — tests de compatibilité modèle ↔ imprimante (1.1.7).

Pour un modèle (dimensions analysées) et une matière, vérifie chaque imprimante : le modèle tient-il (dans n'importe quelle orientation),
la buse et le plateau montent-ils assez en température, faut-il un caisson fermé, une buse durcie (fibres de carbone / verre),
un diamètre de buse adapté (TPU). Chaque test rend `ok`, `warn`, `fail` ou `unknown` (donnée absente : jamais présumé).
Les caractéristiques des imprimantes (`nozzle_diameter`, `nozzle_max_temp`, `bed_max_temp`, `enclosed`, `hardened_nozzle`) sont saisies dans
la configuration de l'imprimante ; le volume (`bed_x/y/z`) est celui que Stellio utilise déjà.
Les tables de matières sont des plages courantes de fabricants : indicatives, à confirmer avec la fiche de votre bobine.
"""
import itertools
import json

_REQUIRED = (
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'session',
)
_OPTIONAL = ()
_OVERRIDABLE = ()

_MAIN = {}
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None

# matière : (buse mini, buse maxi recommandée, plateau mini, plateau maxi, caisson : 'no' | 'recommended' | 'required', flexible)
MATERIALS = {
    'PLA': (190, 230, 0, 70, 'no', False),
    'PETG': (220, 250, 60, 90, 'no', False),
    'ABS': (230, 260, 90, 110, 'recommended', False),
    'ASA': (240, 270, 90, 110, 'recommended', False),
    'TPU': (210, 240, 0, 60, 'no', True),
    'NYLON': (240, 275, 70, 90, 'recommended', False),
    'PA': (240, 275, 70, 90, 'recommended', False),
    'PC': (260, 310, 100, 120, 'required', False),
    'PVA': (185, 210, 45, 60, 'no', False),
    'HIPS': (230, 250, 90, 110, 'recommended', False),
}
ABRASIVE_WORDS = ('CF', 'GF', 'CARBON', 'CARBONE', 'GLASS', 'VERRE', 'FIBRE', 'FIBER', 'GLOW', 'PHOSPHO', 'METAL', 'WOOD-FILL')
SPEC_KEYS = {'nozzle_diameter': (0.1, 2.0), 'nozzle_max_temp': (150, 500), 'bed_max_temp': (30, 200)}
RANK = {'ok': 0, 'unknown': 1, 'warn': 2, 'fail': 3}


def material_profile(name):
    """(clé, profil, abrasif) à partir d'un texte comme « PETG-CF » ou « pla »."""
    t = str(name or '').upper().strip()
    if not t:
        return None, None, False
    abrasive = any(w in t.replace('-', ' ').replace('_', ' ').split() or w in t for w in ABRASIVE_WORDS if len(w) > 2) or any(
        part in ABRASIVE_WORDS for part in t.replace('-', ' ').replace('+', ' ').split())
    for key in sorted(MATERIALS, key=len, reverse=True):
        if key in t.replace('-', ' ').replace('+', ' ').split() or t.startswith(key):
            return key, MATERIALS[key], abrasive
    return None, None, abrasive


def fits(dims, bed):
    """Tient dans le volume dans l'une des 6 orientations ? Retourne (tient, tient_tel_quel)."""
    d = [float(dims.get(k) or 0) for k in ('x', 'y', 'z')] if isinstance(dims, dict) else [float(x) for x in dims]
    b = [float(x) for x in bed]
    as_is = all(d[i] <= b[i] + 1e-6 for i in range(3))
    anyway = any(all(p[i] <= b[i] + 1e-6 for i in range(3)) for p in itertools.permutations(d))
    return anyway, as_is


def check(dims, material, specs):
    """dims : {'x','y','z'} ou None ; specs : dict de l'imprimante (bed_x/y/z, nozzle_diameter, …). Retourne {'status', 'checks': [...]}."""
    checks = []

    def add(cid, status, msg):
        checks.append({'id': cid, 'status': status, 'message': msg})

    bed = [specs.get('bed_x'), specs.get('bed_y'), specs.get('bed_z')]
    if not dims:
        add('fit', 'unknown', "Dimensions du modèle non analysées.")
    elif not all(isinstance(v, (int, float)) and v > 0 for v in bed):
        add('fit', 'unknown', "Volume d'impression de l'imprimante non renseigné.")
    else:
        anyway, as_is = fits(dims, bed)
        if as_is:
            add('fit', 'ok', "Tient dans le volume d'impression.")
        elif anyway:
            add('fit', 'warn', "Tient seulement en changeant l'orientation du modèle.")
        else:
            add('fit', 'fail', "Trop grand pour cette imprimante, quelle que soit l'orientation.")
    key, prof, abrasive = material_profile(material)
    if material and not prof:
        add('material', 'unknown', f"Matière « {material} » absente de la table de compatibilité.")
    if prof:
        nmin, nmax, bmin, bmax, enc, flex = prof
        nz = specs.get('nozzle_max_temp')
        if nz is None:
            add('nozzle_temp', 'unknown', "Température maximale de la buse non renseignée.")
        elif float(nz) < nmin:
            add('nozzle_temp', 'fail', f"{key} demande environ {nmin}–{nmax} °C, la buse est limitée à {nz} °C.")
        elif float(nz) < nmax:
            add('nozzle_temp', 'warn', f"Limite de buse ({nz} °C) sous la plage conseillée du {key} ({nmin}–{nmax} °C).")
        else:
            add('nozzle_temp', 'ok', f"Buse suffisante pour le {key} ({nz} °C).")
        bd = specs.get('bed_max_temp')
        if bmax <= 0 or bmin <= 0:
            pass
        elif bd is None:
            add('bed_temp', 'unknown', "Température maximale du plateau non renseignée.")
        elif float(bd) < bmin:
            add('bed_temp', 'fail', f"{key} demande un plateau à {bmin}–{bmax} °C, limité à {bd} °C.")
        elif float(bd) < bmax:
            add('bed_temp', 'warn', f"Plateau limité à {bd} °C (conseillé {bmin}–{bmax} °C).")
        else:
            add('bed_temp', 'ok', f"Plateau suffisant ({bd} °C).")
        if enc != 'no':
            e = specs.get('enclosed')
            if e is None:
                add('enclosure', 'unknown', "Caisson fermé : information absente.")
            elif not e:
                add('enclosure', 'fail' if enc == 'required' else 'warn', f"{key} s'imprime {'obligatoirement' if enc == 'required' else 'de préférence'} en caisson fermé.")
            else:
                add('enclosure', 'ok', "Imprimante fermée.")
        nd = specs.get('nozzle_diameter')
        if flex and nd is not None and float(nd) < 0.4:
            add('nozzle_size', 'warn', "Buse fine (<0,4 mm) : le TPU risque de se bloquer.")
    if abrasive:
        h = specs.get('hardened_nozzle')
        if h is None:
            add('abrasive', 'unknown', "Matière abrasive : buse durcie non renseignée.")
        elif not h:
            add('abrasive', 'fail', "Matière chargée (fibres, verre…) : une buse durcie est nécessaire.")
        else:
            add('abrasive', 'ok', "Buse durcie.")
    status = max((c['status'] for c in checks), key=lambda s: RANK[s], default='unknown')
    return {'status': status, 'checks': checks, 'material': key}


def normalize_specs(data):
    """Valide les caractéristiques saisies ; retourne (specs propres, erreur)."""
    out = {}
    for k, (lo, hi) in SPEC_KEYS.items():
        if k in data:
            if data[k] in (None, ''):
                out[k] = None
                continue
            try:
                v = float(data[k])
            except (TypeError, ValueError):
                return None, f'{k} invalide.'
            if not lo <= v <= hi:
                return None, f'{k} hors limites ({lo}–{hi}).'
            out[k] = v
    for k in ('enclosed', 'hardened_nozzle'):
        if k in data:
            out[k] = None if data[k] is None else bool(data[k])
    return out, None


def _cfg(row):
    try:
        return json.loads(row['config'] or '{}')
    except (ValueError, TypeError):
        return {}


def printers_specs(conn, uid):
    out = []
    for r in conn.execute("SELECT id, name, config FROM printers WHERE user_id = ? ORDER BY id", (uid,)).fetchall():
        c = _cfg(r)
        out.append({'id': r['id'], 'name': r['name'] or f"#{r['id']}", 'specs': {k: c.get(k) for k in
                    ('bed_x', 'bed_y', 'bed_z', 'nozzle_diameter', 'nozzle_max_temp', 'bed_max_temp', 'enclosed', 'hardened_nozzle')}})
    return out


def model_dims(conn, path):
    r = conn.execute("SELECT data FROM file_analysis WHERE path = ? AND failed = 0", (str(path).replace('\\', '/'),)).fetchone()
    if not r:
        return None
    try:
        d = json.loads(r['data'] or '{}').get('dimensions')
        return d if d and all(k in d for k in ('x', 'y', 'z')) else None
    except (ValueError, AttributeError):
        return None


def api_compat_model():
    path = (request.args.get('path') or '').strip()
    material = (request.args.get('material') or '').strip()[:30]
    if not path:
        return jsonify({'error': 'Fichier manquant.'}), 400
    conn = get_db()
    try:
        dims = model_dims(conn, path)
        rows = []
        for p in printers_specs(conn, session['user_id']):
            res = check(dims, material, p['specs'])
            rows.append({'printer_id': p['id'], 'printer': p['name'], **res})
        order = {'ok': 0, 'warn': 1, 'unknown': 2, 'fail': 3}
        rows.sort(key=lambda r: (order[r['status']], r['printer_id']))
        return jsonify({'path': path, 'material': material, 'dimensions': dims, 'printers': rows,
                        'compatible': sum(1 for r in rows if r['status'] in ('ok', 'warn'))})
    finally:
        conn.close()


def api_compat_specs_get():
    conn = get_db()
    try:
        return jsonify({'printers': printers_specs(conn, session['user_id']), 'materials': sorted(MATERIALS)})
    finally:
        conn.close()


def api_compat_specs_set(pid):
    if session.get('role') == 'viewer' and not _demo_ok():
        return jsonify({'error': 'Réservé au compte propriétaire.', 'code': 'viewer_forbidden'}), 403
    specs, err = normalize_specs(request.get_json(silent=True) or {})
    if err:
        return jsonify({'error': err}), 400
    if not specs:
        return jsonify({'error': 'Rien à modifier.'}), 400
    conn = get_db()
    try:
        row = conn.execute("SELECT config FROM printers WHERE id = ? AND user_id = ?", (pid, session['user_id'])).fetchone()
        if not row:
            return jsonify({'error': 'Imprimante introuvable.'}), 404
        cfg = _cfg(row)
        for k, v in specs.items():
            if v is None:
                cfg.pop(k, None)
            else:
                cfg[k] = v
        conn.execute("UPDATE printers SET config = ? WHERE id = ? AND user_id = ?", (json.dumps(cfg, ensure_ascii=False), pid, session['user_id']))
        conn.commit()
        return jsonify({'ok': True, 'specs': specs})
    finally:
        conn.close()


_DEMO_COMPUTE = ('/api/plate/arrange', '/api/organize/preview', '/api/model-diff')


def _demo_ok():
    """Démo publique (lecture seule, `IS_DEMO` posé par la surcouche de démo) : consultation (GET) et calculs sans écriture."""
    try:
        return bool(_MAIN.get('IS_DEMO')) and (request.method in ('GET', 'HEAD') or request.path in _DEMO_COMPUTE)
    except Exception:
        return False


_ROUTES = (
    ('/api/compat/model', ['GET'], 'api_compat_model', ('login_required', )),
    ('/api/compat/printers', ['GET'], 'api_compat_specs_get', ('login_required', )),
    ('/api/compat/printers/<int:pid>', ['PUT'], 'api_compat_specs_set', ('login_required', )),
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
