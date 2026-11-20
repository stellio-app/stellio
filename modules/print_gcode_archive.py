"""Stellio — archive du G-code réellement imprimé, rattachée à une ligne de l'historique de fabrication (1.1.7).

Le G-code est compressé (gzip) dans `<données>/gcode_archive/`, avec empreinte SHA-256 du fichier d'origine. Plafond : 200 Mo décompressé par archive.
Deux sources : un fichier envoyé (`file`) ou, à défaut, le fichier de l'entrée d'historique s'il est un G-code situé dans les dossiers sources.
Réservé au propriétaire (invités et démo : aucun accès, le G-code peut contenir des chemins et réglages privés).
"""
import gzip
import hashlib
import os
import re
import shutil
import tempfile
import time

_REQUIRED = ('DATA_DIR', '_is_path_within_sources', 'app', 'app_logger', 'get_db', 'jsonify', 'login_required', 'request', 'session')
_OPTIONAL = ('Response',)
_OVERRIDABLE = ('time',)

_MAIN = {}
DATA_DIR = None
_is_path_within_sources = None
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None
Response = None

EXT = ('.gcode', '.bgcode', '.gco', '.g')
MAX_RAW = 200 * 1024 * 1024


def _dir():
    d = os.path.join(DATA_DIR, 'gcode_archive')
    os.makedirs(d, exist_ok=True)
    return d


def ensure(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS gcode_archive (
        history_id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, name TEXT, raw_size INTEGER, gz_size INTEGER, sha256 TEXT, stored TEXT, created REAL)""")


def compress(src_fp, dest_path, limit=MAX_RAW):
    """Compresse un flux ouvert vers dest_path ; retourne (taille brute, sha256). Lève ValueError au-delà de la limite (fichier partiel supprimé)."""
    h, n = hashlib.sha256(), 0
    try:
        with gzip.open(dest_path, 'wb', compresslevel=6) as out:
            while True:
                b = src_fp.read(1024 * 1024)
                if not b:
                    break
                n += len(b)
                if n > limit:
                    raise ValueError('Fichier trop volumineux (plafond %d Mo).' % (limit // 1048576))
                h.update(b)
                out.write(b)
    except Exception:
        try:
            os.remove(dest_path)
        except OSError:
            pass
        raise
    return n, h.hexdigest()


def _safe_name(name):
    name = os.path.basename(str(name or 'impression.gcode').replace('\\', '/'))
    return re.sub(r'[^\w.\- ]', '_', name)[:120] or 'impression.gcode'


def _owner():
    return session.get('role') != 'viewer'


def _entry(conn, hid):
    return conn.execute("SELECT id, file_path, file_name FROM print_history WHERE id = ? AND user_id = ?", (hid, session['user_id'])).fetchone()


def api_gcode_store(hid):
    if not _owner():
        return jsonify({'error': 'Réservé au propriétaire.', 'code': 'viewer_forbidden'}), 403
    conn = get_db()
    try:
        ensure(conn)
        e = _entry(conn, hid)
        if not e:
            return jsonify({'error': 'Entrée introuvable.'}), 404
        up = request.files.get('file')
        tmp_in = None
        if up and up.filename:
            name = _safe_name(up.filename)
            fp = up.stream
        else:
            path = e['file_path'] or ''
            if not path.lower().endswith(EXT) or not os.path.isfile(path) or not _is_path_within_sources(path, session['user_id']):
                return jsonify({'error': "Aucun G-code : joignez un fichier ou choisissez une entrée dont le fichier est un G-code.", 'code': 'bad_request'}), 400
            name = _safe_name(os.path.basename(path))
            fp = tmp_in = open(path, 'rb')
        if not name.lower().endswith(EXT):
            return jsonify({'error': 'Extension non acceptée (.gcode, .bgcode).', 'code': 'bad_request'}), 400
        stored = f"{session['user_id']}_{hid}.gz"
        dest = os.path.join(_dir(), stored)
        try:
            raw, sha = compress(fp, dest)
        except ValueError as ex:
            return jsonify({'error': str(ex), 'code': 'too_large'}), 413
        finally:
            if tmp_in:
                tmp_in.close()
        conn.execute("INSERT OR REPLACE INTO gcode_archive (history_id, user_id, name, raw_size, gz_size, sha256, stored, created) VALUES (?,?,?,?,?,?,?,?)",
                     (hid, session['user_id'], name, raw, os.path.getsize(dest), sha, stored, time.time()))
        conn.commit()
        return jsonify({'ok': True, 'name': name, 'raw_size': raw, 'gz_size': os.path.getsize(dest), 'sha256': sha}), 201
    finally:
        conn.close()


def api_gcode_info(hid):
    if not _owner():
        return jsonify({'error': 'Réservé au propriétaire.', 'code': 'viewer_forbidden'}), 403
    conn = get_db()
    try:
        ensure(conn)
        r = conn.execute("SELECT history_id, name, raw_size, gz_size, sha256, created FROM gcode_archive WHERE history_id = ? AND user_id = ?", (hid, session['user_id'])).fetchone()
        return jsonify({'archived': bool(r), 'archive': dict(r) if r else None})
    finally:
        conn.close()


def api_gcode_download(hid):
    if not _owner():
        return jsonify({'error': 'Réservé au propriétaire.', 'code': 'viewer_forbidden'}), 403
    conn = get_db()
    try:
        ensure(conn)
        r = conn.execute("SELECT name, stored, raw_size FROM gcode_archive WHERE history_id = ? AND user_id = ?", (hid, session['user_id'])).fetchone()
    finally:
        conn.close()
    path = os.path.join(_dir(), r['stored']) if r else ''
    if not r or not os.path.isfile(path):
        return jsonify({'error': 'Aucune archive pour cette impression.'}), 404

    def gen():
        with gzip.open(path, 'rb') as f:
            while True:
                b = f.read(1024 * 1024)
                if not b:
                    break
                yield b
    return Response(gen(), mimetype='application/octet-stream', headers={'Content-Disposition': 'attachment; filename="%s"' % r['name'], 'Content-Length': str(r['raw_size'])})


def api_gcode_delete(hid):
    if not _owner():
        return jsonify({'error': 'Réservé au propriétaire.', 'code': 'viewer_forbidden'}), 403
    conn = get_db()
    try:
        ensure(conn)
        r = conn.execute("SELECT stored FROM gcode_archive WHERE history_id = ? AND user_id = ?", (hid, session['user_id'])).fetchone()
        if not r:
            return jsonify({'error': 'Aucune archive.'}), 404
        conn.execute("DELETE FROM gcode_archive WHERE history_id = ? AND user_id = ?", (hid, session['user_id']))
        conn.commit()
    finally:
        conn.close()
    try:
        os.remove(os.path.join(_dir(), r['stored']))
    except OSError:
        pass
    return jsonify({'ok': True})


def _demo_ok():
    """Démo : aucun accès au G-code (réglages et chemins privés) — la fonction existe pour que la règle soit explicite et testable."""
    return False


_ROUTES = (
    ('/api/print-history/<int:hid>/gcode', ['POST'], 'api_gcode_store', ('login_required', )),
    ('/api/print-history/<int:hid>/gcode', ['GET'], 'api_gcode_info', ('login_required', )),
    ('/api/print-history/<int:hid>/gcode/download', ['GET'], 'api_gcode_download', ('login_required', )),
    ('/api/print-history/<int:hid>/gcode', ['DELETE'], 'api_gcode_delete', ('login_required', )),
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
