"""Stellio — traçabilité d'impression : modèle → version → profil de slicer → résultat (v1.1.6 ; empreinte du profil de slicer : v1.1.7)

Chaque impression lancée (ou ajoutée à la main dans l'historique) est reliée à la VERSION exacte du modèle qui a servi :
  · le « modèle » est le fichier envoyé s'il s'agit d'un maillage (.stl, .3mf…), ou le modèle explicitement associé à un
    G-code (table `trace_links`) ;
  · la version est retrouvée par empreinte SHA-256 parmi les versions enregistrées (module `model_versions`) ; si le fichier
    a changé depuis la dernière version, une version automatique « Avant impression » est enregistrée : l'association est
    donc toujours exacte ;
  · le profil de slicer et le résultat (réussite / échec / partiel) viennent de l'historique d'impression noté.
On en déduit, pour chaque modèle, la combinaison version + profil qui réussit le mieux. Le classement utilise la borne basse
de Wilson : 1 réussite sur 1 ne bat pas 8 sur 9. La collecte démarre à la sortie : les anciennes impressions ne sont pas
reconstituées (mais peuvent être rattachées à la main).

Module séparé de main.py (même schéma que production_planning.py) : main.py appelle `print_traceability.init(globals())`.
Les fonctions de calcul (`wilson_low`, `aggregate`, `pick_best`, `resolve_version`) sont pures : testées sans base.
"""
import hashlib
import json
import math
import os
import time

_REQUIRED = (
    '_is_path_within_sources',
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'session',
)
_OPTIONAL = ()
_OVERRIDABLE = ('hashlib', 'os', 'time')

_MAIN = {}
_is_path_within_sources = None
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None

MESH_EXT = ('.stl', '.obj', '.3mf', '.ply', '.off')
HASH_MAX_BYTES = 300 * 1024 * 1024      # au-delà, pas d'empreinte (donc pas de version)
MIN_FOR_BEST = 2                        # impressions notées minimum pour proposer une « meilleure combinaison »
CONFIDENT = 3                           # à partir de là le taux est présenté comme fiable
RATED = ('success', 'failed', 'partial')


# ── calculs purs ──────────────────────────────────────────────────────────

def wilson_low(success, total, z=1.96):
    """Borne basse de l'intervalle de Wilson du taux de réussite (0 si aucune donnée)."""
    if total <= 0:
        return 0.0
    p = success / total
    d = 1 + z * z / total
    centre = p + z * z / (2 * total)
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total)
    return max(0.0, (centre - spread) / d)


# Réglages qui définissent un profil de slicer : leur empreinte distingue deux profils portant le même nom (v1.1.7).
FP_KEYS = ('slicer', 'profile_type', 'layer_height', 'nozzle_diameter', 'material_type', 'infill_density', 'infill_pattern',
           'wall_count', 'top_layers', 'bottom_layers', 'supports_enabled', 'print_speed', 'first_layer_speed', 'outer_wall_speed',
           'inner_wall_speed', 'infill_speed', 'travel_speed', 'retraction_distance', 'retraction_speed', 'fan_speed',
           'prime_tower_width', 'nozzle_temp', 'bed_temp')


def profile_fingerprint(profile):
    """Empreinte courte (10 caractères) des réglages d'un profil de slicer ; '' si le profil est inconnu.
    Le nom, l'identifiant, le chemin source et les dates n'y entrent pas : seuls les réglages comptent, donc renommer un profil ne
    change pas son empreinte alors que modifier une température ou une hauteur de couche la change."""
    if not isinstance(profile, dict):
        return ''
    keep = {k: profile.get(k) for k in FP_KEYS if profile.get(k) is not None}
    if len(keep) <= 1:      # seulement le logiciel de découpe : rien de comparable
        return ''
    raw = json.dumps(keep, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:10]


def resolve_version(versions, sha):
    """Numéro de la version dont l'empreinte est `sha` (la plus récente en cas de doublon), sinon None.
    versions : liste de dicts {version, sha256}."""
    if not sha:
        return None
    best = None
    for v in versions or []:
        if v.get('sha256') == sha and (best is None or v['version'] > best):
            best = v['version']
    return best


def aggregate(rows):
    """rows : dicts {model_path, model_version, profile_name, profile_fp, result, sent_at}. Seules les impressions notées comptent.
    Retourne les combinaisons (modèle, version, profil) avec leurs compteurs, taux et score de classement."""
    groups = {}
    for r in rows:
        res = r.get('result')
        if res not in RATED:
            continue
        key = (r.get('model_path') or '', r.get('model_version'), (r.get('profile_name') or '').strip(), r.get('profile_fp') or '')
        g = groups.setdefault(key, {'model_path': key[0], 'version': key[1], 'profile': key[2], 'profile_fp': key[3],
                                    'success': 0, 'failed': 0, 'partial': 0, 'last': ''})
        g[res] += 1
        g['last'] = max(g['last'], str(r.get('sent_at') or ''))
    out = []
    for g in groups.values():
        n = g['success'] + g['failed'] + g['partial']
        g['total'] = n
        g['rate'] = round(g['success'] / n, 3)
        g['confident'] = n >= CONFIDENT
        g['score'] = round(wilson_low(g['success'], n), 4)
        out.append(g)
    out.sort(key=lambda g: (g['score'], g['total'], g['last']), reverse=True)
    return out


def pick_best(combos):
    """Meilleure combinaison identifiable : version connue, au moins MIN_FOR_BEST impressions, au moins une réussite."""
    cands = [c for c in combos if c['version'] is not None and c['total'] >= MIN_FOR_BEST and c['success'] > 0]
    if not cands:
        return None
    return max(cands, key=lambda c: (c['score'], c['total'], c['last']))


def version_stats(rows):
    """Compteurs par version (toutes combinaisons de profils confondues) : {version: {success, failed, partial, total, rate}}."""
    out = {}
    for r in rows:
        if r.get('result') not in RATED or r.get('model_version') is None:
            continue
        s = out.setdefault(r['model_version'], {'success': 0, 'failed': 0, 'partial': 0})
        s[r['result']] += 1
    for s in out.values():
        s['total'] = s['success'] + s['failed'] + s['partial']
        s['rate'] = round(s['success'] / s['total'], 3) if s['total'] else None
    return out


# ── accès base ────────────────────────────────────────────────────────────

def _ensure_tables(conn=None):
    own = conn is None
    if own:
        conn = get_db()
    if conn is None:
        return
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS print_trace (
            history_id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            model_path TEXT DEFAULT '',
            model_version INTEGER,
            model_sha TEXT DEFAULT '',
            file_sha TEXT DEFAULT '',
            profile_fp TEXT DEFAULT '',
            created_at REAL)""")
        if 'profile_fp' not in {r['name'] for r in conn.execute("PRAGMA table_info(print_trace)").fetchall()}:
            conn.execute("ALTER TABLE print_trace ADD COLUMN profile_fp TEXT DEFAULT ''")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_print_trace_model ON print_trace(user_id, model_path)")
        conn.execute("""CREATE TABLE IF NOT EXISTS trace_links (
            user_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            model_path TEXT NOT NULL,
            PRIMARY KEY (user_id, file_path))""")
        conn.commit()
    finally:
        if own:
            conn.close()


def _norm(p):
    return (p or '').strip().replace('\\', '/')


def _native(p):
    return p.replace('/', '\\') if os.name == 'nt' else p.replace('\\', '/')


def _sha(path):
    try:
        if os.path.getsize(path) > HASH_MAX_BYTES:
            return ''
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return ''


def _versions_mod():
    try:
        from modules import model_versions
        return model_versions
    except Exception:
        return None


def _model_for(conn, uid, file_path):
    """Chemin (normalisé) du modèle d'un fichier envoyé : lien explicite, sinon le fichier lui-même s'il est un maillage."""
    row = conn.execute("SELECT model_path FROM trace_links WHERE user_id = ? AND file_path = ?", (uid, file_path)).fetchone()
    if row:
        return row['model_path']
    return file_path if os.path.splitext(file_path)[1].lower() in MESH_EXT else ''


def _version_of(conn, uid, model_path, allow_snapshot=True):
    """(version, sha) du fichier modèle tel qu'il est maintenant ; enregistre une version automatique s'il est nouveau."""
    mv = _versions_mod()
    native = _native(model_path)
    if not model_path or mv is None or not os.path.isfile(native):
        return None, ''
    sha = _sha(native)
    if not sha:
        return None, ''
    mv._ensure_table(conn)
    rows = [dict(r) for r in conn.execute("SELECT version, sha256 FROM model_versions WHERE path = ?", (model_path,)).fetchall()]
    v = resolve_version(rows, sha)
    if v is None and allow_snapshot:
        try:
            if _is_path_within_sources(native, uid):
                v = mv._snapshot(conn, native, model_path, 'Avant impression', auto=1)['version']
        except Exception as e:
            try:
                app_logger.info(f"[TRACE] Version automatique impossible : {e}")
            except Exception:
                pass
    return v, sha


def _profiles_by_id():
    try:
        from modules import slicer_import
        return {p.get('id'): p for p in (slicer_import.load_slicer_profiles() or []) if isinstance(p, dict)}
    except Exception:
        return {}


def _fp_for_history(conn, uid, history_id):
    """Empreinte du profil de slicer noté sur une ligne d'historique (vide si aucun profil connu)."""
    try:
        row = conn.execute("SELECT slicer_profile_id FROM print_history WHERE id = ? AND user_id = ?", (history_id, uid)).fetchone()
        pid = (row['slicer_profile_id'] if row else '') or ''
        return profile_fingerprint(_profiles_by_id().get(pid)) if pid else ''
    except Exception:
        return ''


def record(conn, uid, history_id, file_path, real_path=None):
    """Relie une ligne d'historique à la version du modèle. Ne lève jamais : l'impression ne doit pas échouer pour ça."""
    try:
        if not history_id:
            return None
        _ensure_tables(conn)
        fp = _norm(file_path)
        model = _model_for(conn, uid, fp)
        version, msha = (None, '')
        if model:
            version, msha = _version_of(conn, uid, model)
        fsha = msha if model == fp else _sha(real_path or _native(fp))
        conn.execute("INSERT OR REPLACE INTO print_trace (history_id, user_id, model_path, model_version, model_sha, file_sha, profile_fp, created_at) "
                     "VALUES (?,?,?,?,?,?,?,?)", (history_id, uid, model, version, msha, fsha, _fp_for_history(conn, uid, history_id), time.time()))
        return {'model_path': model, 'version': version}
    except Exception as e:
        try:
            app_logger.warning(f"[TRACE] Association échouée : {e}")
        except Exception:
            pass
        return None


def _rows(conn, uid, model_path=None):
    sql = ("SELECT t.history_id, t.model_path, t.model_version, t.profile_fp, h.result, h.slicer_profile_name AS profile_name, "
           "h.sent_at, h.printer_id, h.file_name FROM print_trace t JOIN print_history h ON h.id = t.history_id "
           "WHERE t.user_id = ? AND h.user_id = ?")
    params = [uid, uid]
    if model_path is not None:
        sql += " AND t.model_path = ?"
        params.append(model_path)
    sql += " ORDER BY h.sent_at DESC"
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


# ── routes ────────────────────────────────────────────────────────────────

def api_trace_model():
    path = _norm(request.args.get('path'))
    if not path:
        return jsonify({'error': 'path_required'}), 400
    uid = session['user_id']
    if not _is_path_within_sources(_native(path), uid):
        return jsonify({'error': 'forbidden'}), 403
    conn = get_db()
    try:
        _ensure_tables(conn)
        mv = _versions_mod()
        vers = []
        if mv is not None:
            mv._ensure_table(conn)
            vers = [dict(r) for r in conn.execute(
                "SELECT id, version, note, auto, created_at, sha256 FROM model_versions WHERE path = ? ORDER BY version DESC", (path,)).fetchall()]
        rows = _rows(conn, uid, path)
        printers = {r['id']: r['name'] for r in conn.execute("SELECT id, name FROM printers").fetchall()}
    finally:
        conn.close()
    stats = version_stats(rows)
    combos = aggregate(rows)
    best = pick_best(combos)
    for v in vers:
        v.pop('sha256', None)
        v['auto'] = bool(v['auto'])
        v['stats'] = stats.get(v['version'])
        v['prints'] = sum(1 for r in rows if r['model_version'] == v['version'])
    recent = [{'history_id': r['history_id'], 'sent_at': r['sent_at'], 'result': r['result'] or '', 'version': r['model_version'],
               'profile': r['profile_name'] or '', 'profile_fp': r.get('profile_fp') or '', 'printer': printers.get(r['printer_id']) or ''} for r in rows[:20]]
    return jsonify({'path': path, 'versions': vers, 'combos': combos, 'best': best, 'recent': recent, 'prints': len(rows)})


def api_trace_overview():
    """Un modèle par ligne, avec sa meilleure combinaison : « qu'est-ce qui marche le mieux » en quelques secondes."""
    uid = session['user_id']
    q = (request.args.get('q') or '').strip().lower()
    try:
        limit = max(1, min(200, int(request.args.get('limit') or 60)))
    except ValueError:
        limit = 60
    conn = get_db()
    try:
        _ensure_tables(conn)
        rows = [r for r in _rows(conn, uid) if r['model_path']]
    finally:
        conn.close()
    by_model = {}
    for r in rows:
        by_model.setdefault(r['model_path'], []).append(r)
    out = []
    for path, rs in by_model.items():
        name = path.rsplit('/', 1)[-1]
        if q and q not in name.lower():
            continue
        combos = aggregate(rs)
        rated = sum(c['total'] for c in combos)
        versions = sorted({r['model_version'] for r in rs if r['model_version'] is not None})
        out.append({'path': path, 'name': name, 'prints': len(rs), 'rated': rated, 'versions': versions,
                    'best': pick_best(combos), 'last': max(str(r['sent_at'] or '') for r in rs)})
    out.sort(key=lambda m: m['last'], reverse=True)
    return jsonify({'models': out[:limit], 'total': len(out)})


def api_trace_link():
    """Associe un G-code (ou tout fichier envoyé) à son modèle ; rattache aussi ses impressions déjà notées sans modèle."""
    data = request.get_json(silent=True) or {}
    uid = session['user_id']
    fp, mp = _norm(data.get('file_path')), _norm(data.get('model_path'))
    if not fp or not mp:
        return jsonify({'error': 'path_required'}), 400
    if os.path.splitext(mp)[1].lower() not in MESH_EXT:
        return jsonify({'error': 'not_a_model'}), 400
    if not (_is_path_within_sources(_native(fp), uid) and _is_path_within_sources(_native(mp), uid)):
        return jsonify({'error': 'forbidden'}), 403
    if not os.path.isfile(_native(mp)):
        return jsonify({'error': 'not_local'}), 400
    conn = get_db()
    try:
        _ensure_tables(conn)
        conn.execute("INSERT OR REPLACE INTO trace_links (user_id, file_path, model_path) VALUES (?,?,?)", (uid, fp, mp))
        version, msha = _version_of(conn, uid, mp)
        ids = [r['history_id'] for r in conn.execute(
            "SELECT t.history_id FROM print_trace t JOIN print_history h ON h.id = t.history_id "
            "WHERE t.user_id = ? AND t.model_path = '' AND h.file_path = ?", (uid, fp)).fetchall()]
        for hid in ids:
            conn.execute("UPDATE print_trace SET model_path = ?, model_version = ?, model_sha = ? WHERE history_id = ?",
                         (mp, version, msha, hid))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'success': True, 'version': version, 'relinked': len(ids)})


def api_trace_entry():
    """Rattache à la main une impression de l'historique à un modèle et une version (anciennes impressions)."""
    data = request.get_json(silent=True) or {}
    uid = session['user_id']
    try:
        hid = int(data.get('history_id'))
        version = int(data.get('version')) if data.get('version') not in (None, '') else None
    except (TypeError, ValueError):
        return jsonify({'error': 'bad_request'}), 400
    mp = _norm(data.get('model_path'))
    if not mp or not _is_path_within_sources(_native(mp), uid):
        return jsonify({'error': 'forbidden'}), 403
    conn = get_db()
    try:
        _ensure_tables(conn)
        if not conn.execute("SELECT 1 FROM print_history WHERE id = ? AND user_id = ?", (hid, uid)).fetchone():
            return jsonify({'error': 'not_found'}), 404
        if version is not None:
            mv = _versions_mod()
            if mv is None:
                return jsonify({'error': 'unavailable'}), 500
            mv._ensure_table(conn)
            if not conn.execute("SELECT 1 FROM model_versions WHERE path = ? AND version = ?", (mp, version)).fetchone():
                return jsonify({'error': 'version_not_found'}), 404
        conn.execute("INSERT OR REPLACE INTO print_trace (history_id, user_id, model_path, model_version, model_sha, file_sha, profile_fp, created_at) "
                     "VALUES (?,?,?,?,?,?,?,?)", (hid, uid, mp, version, '', '', _fp_for_history(conn, uid, hid), time.time()))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'success': True})


_ROUTES = (
    ('/api/trace/model', ['GET'], 'api_trace_model', ('login_required', )),
    ('/api/trace/overview', ['GET'], 'api_trace_overview', ('login_required', )),
    ('/api/trace/link', ['POST'], 'api_trace_link', ('login_required', )),
    ('/api/trace/entry', ['POST'], 'api_trace_entry', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"print_traceability.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if routes:
        try:
            _ensure_tables()
        except Exception as e:
            try:
                app_logger.warning(f"[TRACE] Tables non préparées : {e}")
            except Exception:
                pass
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {}
