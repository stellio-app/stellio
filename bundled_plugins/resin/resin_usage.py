"""Stellio — consommation de résine déduite automatiquement à la fin d'une impression (1.1.8).

Chaque imprimante résine peut recevoir un « flacon actif ». Quand une impression résine se termine, Stellio retire du flacon actif le volume
utilisé, jamais plus que ce qu'il reste, et garde une ligne d'historique annulable.

Origine du volume, par ordre de confiance (la source est toujours enregistrée et affichée) :
  1. `sl1`   : le fichier découpé `.sl1` (PrusaSlicer) est dans la bibliothèque : champ `usedMaterial` de son `config.ini` (en ml) ;
  2. `model` : un modèle de même nom (STL, 3MF, OBJ, PLY, OFF) est dans la bibliothèque : volume du maillage fermé + marge pour les supports
               et les pertes (réglage `resin_overhead_pct`, 15 % par défaut) ; c'est une estimation, signalée comme telle ;
  3. aucun   : rien n'est déduit, une notification le dit (le bouton « Utiliser » reste disponible).
Une impression échouée ne retire que la part déjà imprimée (progression × volume), seulement quand la progression est connue.
Aucun volume n'est jamais inventé. Le même évènement ne déduit jamais deux fois (clé de dédoublonnage).
"""
import os
import time
import zipfile

_REQUIRED = (
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'session',
    'load_settings',
    '_is_resin_printer_row',
)
_OPTIONAL = ('_insert_notification_once', '_read_cache_json_safe', '_server_t', 'parse_printer_config')
_OVERRIDABLE = ('time',)

_MAIN = {}
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None
load_settings = None
_is_resin_printer_row = None
_insert_notification_once = None
_read_cache_json_safe = None
_server_t = None
parse_printer_config = None

MESH_EXT = ('.stl', '.obj', '.3mf', '.ply', '.off')
DEFAULT_OVERHEAD_PCT = 15.0
MAX_ML = 20000.0
_PUBLISHED = {'ok': False}


def _ensure(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS resin_printer_bottle (
        printer_id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        bottle_id INTEGER NOT NULL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS resin_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        printer_id INTEGER,
        bottle_id INTEGER,
        file TEXT DEFAULT '',
        ml REAL NOT NULL,
        source TEXT DEFAULT '',
        outcome TEXT DEFAULT 'finished',
        event_key TEXT UNIQUE,
        undone INTEGER DEFAULT 0,
        created_at REAL)""")


def _stem(name):
    return os.path.splitext(os.path.basename(str(name or '').replace('\\', '/')))[0].strip().lower()


def sl1_used_ml(path):
    """`usedMaterial` (ml) d'un fichier .sl1 ; None s'il manque ou n'est pas lisible."""
    try:
        with zipfile.ZipFile(path) as z:
            raw = z.read('config.ini').decode('utf-8', 'ignore')
    except Exception:
        return None
    for line in raw.splitlines():
        k, _, v = line.partition('=')
        if k.strip().lower() == 'usedmaterial':
            try:
                ml = float(v.strip().replace(',', '.'))
            except ValueError:
                return None
            return ml if 0 < ml <= MAX_ML else None
    return None


def mesh_volume_ml(path):
    """Volume (ml) d'un maillage fermé, None sinon (jamais d'estimation sur un maillage ouvert)."""
    try:
        from modules import model_diff
        m = model_diff.load_mesh(path)
        vol = model_diff.volume(m.vertices, m.faces)
    except Exception:
        return None
    if vol is None:
        return None
    ml = vol / 1000.0
    return ml if 0 < ml <= MAX_ML else None


def _library_files():
    try:
        data = _read_cache_json_safe() if _read_cache_json_safe else None
    except Exception:
        data = None
    return (data or {}).get('files') or []


def find_volume(file_name, overhead_pct=DEFAULT_OVERHEAD_PCT, files=None):
    """(ml, source) pour un fichier d'impression, ou (None, '') s'il n'y a rien de fiable."""
    stem = _stem(file_name)
    if not stem:
        return None, ''
    files = _library_files() if files is None else files
    same = [f for f in files if _stem(f.get('name') or f.get('path')) == stem and f.get('path')]
    for f in same:
        if str(f.get('path')).lower().endswith('.sl1') and os.path.isfile(f['path']):
            ml = sl1_used_ml(f['path'])
            if ml:
                return round(ml, 1), 'sl1'
    for f in same:
        p = str(f['path'])
        if p.lower().endswith(MESH_EXT) and os.path.isfile(p):
            ml = mesh_volume_ml(p)
            if ml:
                return round(ml * (1 + max(0.0, overhead_pct) / 100.0), 1), 'model'
    return None, ''


def _title(key, fb):
    try:
        return _server_t(key, fb) if _server_t else fb
    except Exception:
        return fb


def _notify(uid, ntype, title, msg, key):
    if _insert_notification_once:
        try:
            _insert_notification_once(uid, ntype, title, msg, 'resin', key)
        except Exception as e:
            app_logger.debug(f"[RESIN] Notification ignorée : {e}")


def apply_usage(conn, user_id, printer_id, file_name, outcome, progress, event_key, overhead_pct=DEFAULT_OVERHEAD_PCT, files=None, printer_name=''):
    """Cœur du calcul. Retourne {'status': 'deducted'|'duplicate'|'no_bottle'|'no_volume'|'no_progress', ...}. N'écrit rien en dehors d'un cas « deducted »."""
    _ensure(conn)
    if conn.execute("SELECT 1 FROM resin_usage WHERE event_key = ?", (event_key,)).fetchone():
        return {'status': 'duplicate'}
    link = conn.execute("SELECT bottle_id, user_id FROM resin_printer_bottle WHERE printer_id = ?", (printer_id,)).fetchone()
    if not link:
        return {'status': 'no_bottle'}
    bottle = conn.execute("SELECT * FROM resin_bottles WHERE id = ? AND user_id = ?", (link['bottle_id'], link['user_id'])).fetchone()
    if not bottle:
        return {'status': 'no_bottle'}
    ml, source = find_volume(file_name, overhead_pct, files)
    if not ml:
        return {'status': 'no_volume'}
    if outcome == 'failed':
        try:
            frac = float(progress)
        except (TypeError, ValueError):
            return {'status': 'no_progress'}
        if not 0 < frac <= 100:
            return {'status': 'no_progress'}
        ml = round(ml * frac / 100.0, 1)
        source += '+partial'
    left_before = float(bottle['remaining_ml'] or 0)
    used = round(min(ml, left_before), 1)
    if used <= 0:
        return {'status': 'empty', 'bottle': bottle['name']}
    conn.execute("UPDATE resin_bottles SET remaining_ml = ? WHERE id = ?", (round(left_before - used, 1), bottle['id']))
    conn.execute("INSERT INTO resin_usage (user_id, printer_id, bottle_id, file, ml, source, outcome, event_key, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                 (link['user_id'], printer_id, bottle['id'], os.path.basename(str(file_name or '')), used, source, outcome, event_key, time.time()))
    conn.commit()
    return {'status': 'deducted', 'ml': used, 'source': source, 'bottle': bottle['name'], 'left': round(left_before - used, 1), 'user_id': link['user_id']}


def on_print_event(ev):
    """Écouteur branché sur `print_events` : ev = {'event': 'finished'|'failed', 'printer': {...}, 'file', 'progress', 'ts'}."""
    p = ev.get('printer') or {}
    try:
        if not _is_resin_printer_row(p.get('type'), p.get('name') or ''):
            return
    except Exception:
        return
    pid = p.get('id')
    file_name = ev.get('file') or ''
    if not file_name:
        return
    key = f"{pid}:{file_name}:{int((ev.get('ts') or time.time()) // 600)}"
    cfg = load_settings() or {}
    try:
        overhead = float(cfg.get('resin_overhead_pct', DEFAULT_OVERHEAD_PCT))
    except (TypeError, ValueError):
        overhead = DEFAULT_OVERHEAD_PCT
    conn = get_db()
    try:
        r = apply_usage(conn, p.get('user_id'), pid, file_name, 'failed' if ev.get('event') == 'failed' else 'finished', ev.get('progress'), key, overhead, printer_name=p.get('name') or '')
        owner = r.get('user_id') or p.get('user_id')
    except Exception as e:
        app_logger.info(f"[RESIN] Déduction impossible ({file_name}) : {e}")
        return
    finally:
        conn.close()
    if owner is None:
        return
    name = p.get('name') or f"#{pid}"
    st = r['status']
    if st == 'deducted':
        tag = ' (estimation)' if 'model' in r['source'] else ''
        _notify(owner, 'resin_used', _title('notif.resin_used_title', 'Résine déduite'),
                f"{name} — {os.path.basename(file_name)} : {r['ml']} ml{tag} → {r['bottle']} ({r['left']} ml restants)", f"resin_used:{key}")
    elif st == 'no_bottle':
        _notify(owner, 'resin_unassigned', _title('notif.resin_unassigned_title', 'Résine non déduite'),
                f"{name} : aucun flacon actif. Choisissez-le dans Matières › Résine.", f"resin_unassigned:{pid}:{int(time.time() // 86400)}")
    elif st in ('no_volume', 'no_progress'):
        _notify(owner, 'resin_unknown', _title('notif.resin_unknown_title', 'Volume de résine inconnu'),
                f"{name} — {os.path.basename(file_name)} : volume introuvable, rien n'a été déduit. Utilisez le bouton « Utiliser » du flacon.", f"resin_unknown:{key}")


# ── routes ──
def api_resin_printers():
    """Imprimantes résine du compte avec leur flacon actif."""
    conn = get_db()
    try:
        _ensure(conn)
        uid = session['user_id']
        links = {r['printer_id']: r['bottle_id'] for r in conn.execute("SELECT printer_id, bottle_id FROM resin_printer_bottle WHERE user_id = ?", (uid,)).fetchall()}
        out = []
        for row in conn.execute("SELECT id, name, type FROM printers").fetchall():
            if _is_resin_printer_row(row['type'], row['name'] or ''):
                out.append({'id': row['id'], 'name': row['name'], 'bottle_id': links.get(row['id'])})
        return jsonify({'printers': out})
    finally:
        conn.close()


def api_resin_printer_bottle():
    d = request.get_json(silent=True) or {}
    try:
        pid = int(d.get('printer_id'))
        bid = None if d.get('bottle_id') in (None, '', 0) else int(d.get('bottle_id'))
    except (TypeError, ValueError):
        return jsonify({'error': 'bad_number'}), 400
    conn = get_db()
    try:
        _ensure(conn)
        uid = session['user_id']
        p = conn.execute("SELECT id, name, type FROM printers WHERE id = ?", (pid,)).fetchone()
        if not p or not _is_resin_printer_row(p['type'], p['name'] or ''):
            return jsonify({'error': 'not_found'}), 404
        if bid is None:
            conn.execute("DELETE FROM resin_printer_bottle WHERE printer_id = ? AND user_id = ?", (pid, uid))
        else:
            if not conn.execute("SELECT 1 FROM resin_bottles WHERE id = ? AND user_id = ?", (bid, uid)).fetchone():
                return jsonify({'error': 'not_found'}), 404
            conn.execute("INSERT INTO resin_printer_bottle (printer_id, user_id, bottle_id) VALUES (?,?,?) "
                         "ON CONFLICT(printer_id) DO UPDATE SET bottle_id = excluded.bottle_id, user_id = excluded.user_id", (pid, uid, bid))
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


def api_resin_usage():
    conn = get_db()
    try:
        _ensure(conn)
        rows = conn.execute("SELECT u.*, b.name AS bottle_name FROM resin_usage u LEFT JOIN resin_bottles b ON b.id = u.bottle_id "
                            "WHERE u.user_id = ? ORDER BY u.id DESC LIMIT 50", (session['user_id'],)).fetchall()
        return jsonify({'usage': [{'id': r['id'], 'printer_id': r['printer_id'], 'bottle_id': r['bottle_id'], 'bottle': r['bottle_name'] or '', 'file': r['file'],
                                   'ml': r['ml'], 'source': r['source'], 'outcome': r['outcome'], 'undone': bool(r['undone']), 'at': r['created_at']} for r in rows]})
    finally:
        conn.close()


def api_resin_usage_undo():
    d = request.get_json(silent=True) or {}
    try:
        uid_row = int(d.get('id'))
    except (TypeError, ValueError):
        return jsonify({'error': 'bad_number'}), 400
    conn = get_db()
    try:
        _ensure(conn)
        r = conn.execute("SELECT * FROM resin_usage WHERE id = ? AND user_id = ?", (uid_row, session['user_id'])).fetchone()
        if not r:
            return jsonify({'error': 'not_found'}), 404
        if r['undone']:
            return jsonify({'error': 'already_undone'}), 409
        b = conn.execute("SELECT * FROM resin_bottles WHERE id = ? AND user_id = ?", (r['bottle_id'], session['user_id'])).fetchone()
        if b:
            back = min(float(b['volume_ml'] or 0) or 1e9, float(b['remaining_ml'] or 0) + float(r['ml']))
            conn.execute("UPDATE resin_bottles SET remaining_ml = ? WHERE id = ?", (round(back, 1), b['id']))
        conn.execute("UPDATE resin_usage SET undone = 1 WHERE id = ?", (r['id'],))
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


_ROUTES = (
    ('/api/resin/printers', ['GET'], 'api_resin_printers', ('login_required', )),
    ('/api/resin/printer-bottle', ['POST'], 'api_resin_printer_bottle', ('login_required', )),
    ('/api/resin/usage', ['GET'], 'api_resin_usage', ('login_required', )),
    ('/api/resin/usage/undo', ['POST'], 'api_resin_usage_undo', ('login_required', )),
)


def _has_links():
    conn = get_db()
    try:
        _ensure(conn)
        return conn.execute("SELECT 1 FROM resin_printer_bottle LIMIT 1").fetchone() is not None
    finally:
        conn.close()


def autostart():
    """Branche l'écouteur sur la surveillance des imprimantes (le cœur la lance dès qu'un écouteur existe)."""
    try:
        from modules import print_events
        print_events.register_listener(on_print_event, _has_links)
        _PUBLISHED['ok'] = True
    except Exception as e:
        app_logger.info(f"[RESIN] Écouteur d'impressions non branché : {e}")


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"resin_usage.init : services manquants : {missing}")
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
