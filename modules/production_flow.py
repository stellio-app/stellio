"""Stellio — flux de production assisté (1.1.8) : proposer → valider (humain) → envoyer → vérifier le résultat.

Stellio ne lance JAMAIS une impression sans clic humain, et il ne ment pas sur ce qu'il sait faire :
  1. proposition  : classe les imprimantes (répartiteur : libre, matière chargée, file d'attente) et recommande un profil de slicer
                    (Intelligence, corrigée par les retours des recommandations déjà suivies) ; vérifie le fichier et les consommables ;
  2. validation   : la personne confirme (ou change d'imprimante / de profil). Sans validation, l'envoi est refusé côté serveur ;
  3. envoi        : le fichier est envoyé à l'imprimante choisie (même fonction que le bouton « Envoyer à l'imprimante »). Stellio ne démarre
                    pas à distance le travail : le démarrage reste à la machine ou au slicer, et l'écran le dit ;
  4. résultat     : la surveillance des imprimantes (print_events) marque l'exécution « terminée » ou « échouée » ; à défaut, la personne
                    indique le résultat. Il alimente l'historique et le retour d'expérience d'Intelligence.
Contrôles : « block » (envoi impossible), « warn » (à lire, la validation reste possible), « ok ».
"""
import json
import os
import time

_REQUIRED = (
    '_is_path_within_sources',
    '_printer_status_cached',
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'parse_printer_config',
    'printer_hub',
    'request',
    'session',
)
_OPTIONAL = ('_check_restock_for_files', '_insert_notification_once', '_is_resin_printer_row', '_server_t')
_OVERRIDABLE = ('time', )

_MAIN = {}
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None
parse_printer_config = None
printer_hub = None
_is_path_within_sources = None
_printer_status_cached = None
_check_restock_for_files = None
_insert_notification_once = None
_is_resin_printer_row = None
_server_t = None

SLICED_FDM = ('.gcode', '.gco', '.bgcode', '.3mf', '.ufp')
SLICED_RESIN = ('.sl1', '.sl1s', '.ctb', '.cbddlp', '.photon', '.pwmx', '.pwma', '.pws', '.pw0', '.pwmo', '.goo', '.form', '.fdg')
RAW_MODEL = ('.stl', '.obj', '.step', '.stp', '.ply', '.off', '.amf')
OFFLINE = ('offline', 'error', 'unavailable', 'timeout', 'corrupted', 'unknown')
BUSY = ('printing', 'paused')
MATCH_WINDOW_S = 48 * 3600


def _ensure(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS production_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        file_path TEXT NOT NULL,
        file_name TEXT DEFAULT '',
        material TEXT DEFAULT '',
        status TEXT DEFAULT 'proposed',
        printer_id INTEGER,
        printer_name TEXT DEFAULT '',
        profile TEXT DEFAULT '',
        proposal_json TEXT DEFAULT '',
        history_id INTEGER,
        note TEXT DEFAULT '',
        created_at REAL,
        validated_at REAL,
        sent_at REAL,
        ended_at REAL)""")


def _ext(path):
    return os.path.splitext(str(path or ''))[1].lower()


def _is_resin(row):
    try:
        return bool(_is_resin_printer_row and _is_resin_printer_row(row['type'], row['name'] or ''))
    except Exception:
        return False


def check_file(path, resin):
    """Le fichier est-il prêt à partir sur ce type d'imprimante ? Fonction pure. Retourne (niveau, code)."""
    e = _ext(path)
    if e in RAW_MODEL:
        return 'block', 'needs_slicing'
    if resin and e in SLICED_FDM and e != '.3mf':
        return 'block', 'wrong_kind'
    if not resin and e in SLICED_RESIN:
        return 'block', 'wrong_kind'
    if resin and e not in SLICED_RESIN:
        return 'warn', 'format_unknown'
    if not resin and e not in SLICED_FDM:
        return 'warn', 'format_unknown'
    if e == '.3mf':
        return 'warn', 'project_3mf'
    return 'ok', 'file_ready'


def check_printer_state(status):
    st = str((status or {}).get('status') or 'unknown').lower()
    if st in OFFLINE:
        return 'block', 'printer_offline'
    if st in BUSY:
        return 'warn', 'printer_busy'
    return 'ok', 'printer_idle'


def _resin_checks(conn, uid, printer_row, path):
    """Flacon actif de l'imprimante et reste suffisant pour le volume connu (jamais de volume inventé)."""
    out = []
    try:
        from modules import resin_usage
    except Exception:
        return out
    try:
        resin_usage._ensure(conn)
        link = conn.execute("SELECT bottle_id FROM resin_printer_bottle WHERE printer_id = ? AND user_id = ?", (printer_row['id'], uid)).fetchone()
        if not link:
            return [{'id': 'resin_bottle', 'level': 'warn', 'code': 'no_active_bottle'}]
        b = conn.execute("SELECT name, remaining_ml FROM resin_bottles WHERE id = ? AND user_id = ?", (link['bottle_id'], uid)).fetchone()
        if not b:
            return [{'id': 'resin_bottle', 'level': 'warn', 'code': 'no_active_bottle'}]
        ml, src = resin_usage.find_volume(path)
        if not ml:
            return [{'id': 'resin_bottle', 'level': 'warn', 'code': 'resin_volume_unknown', 'bottle': b['name']}]
        if float(b['remaining_ml'] or 0) < ml:
            return [{'id': 'resin_bottle', 'level': 'block', 'code': 'resin_not_enough', 'bottle': b['name'], 'need_ml': ml, 'left_ml': round(float(b['remaining_ml'] or 0), 1)}]
        return [{'id': 'resin_bottle', 'level': 'ok', 'code': 'resin_ok', 'bottle': b['name'], 'need_ml': ml, 'left_ml': round(float(b['remaining_ml'] or 0), 1), 'source': src}]
    except Exception as e:
        app_logger.debug(f"[PRODUCTION] Contrôle résine ignoré : {e}")
    return out


def _filament_checks(uid, path):
    if not _check_restock_for_files:
        return []
    try:
        alerts = _check_restock_for_files([path], uid) or []
    except Exception:
        return []
    if alerts:
        return [{'id': 'filament', 'level': 'warn', 'code': 'filament_low', 'detail': str((alerts[0] or {}).get('message') or '')[:160]}]
    return [{'id': 'filament', 'level': 'ok', 'code': 'filament_ok'}]


def rank(printers_scored):
    """Classe des candidats {score, rec_bonus} : score répartiteur + bonus Intelligence (0 à 30), puis id. Fonction pure."""
    return sorted(printers_scored, key=lambda c: (-(c['score'] + c.get('rec_bonus', 0)), c['printer_id']))


def build_proposal(conn, uid, path, material=''):
    from modules import intelligence, printer_dispatch
    norm = str(path).replace('\\', '/')
    rows = [r for r in conn.execute("SELECT * FROM printers WHERE user_id = ? ORDER BY id", (uid, )).fetchall()]
    hist = intelligence._load_rows(conn, uid)
    prof = intelligence._profiles()
    fb = intelligence.load_feedback(conn, uid)
    job = {'material': material or '', 'quantity': 1, 'qty_done': 0, 'cost_model': ''}
    cands = []
    for r in rows:
        cfg = parse_printer_config(r)
        try:
            status = _printer_status_cached(cfg) or {}
        except Exception:
            status = {'status': 'offline'}
        resin = _is_resin(r)
        sc = printer_dispatch.score_printer(job, cfg, status, 0)
        if sc is None:
            continue
        kind, code = check_file(norm, resin)
        if kind == 'block':
            continue
        rec = intelligence.recommend(hist, prof, material, r['id'], norm, fb)
        best = rec.get('best')
        bonus = round(best['score'] * 30, 1) if best else 0
        cands.append({'printer_id': r['id'], 'printer_name': r['name'] or f"#{r['id']}", 'resin': resin, 'status': str(status.get('status') or ''),
                      'score': sc[0], 'rec_bonus': bonus, 'reasons': sc[1], 'warnings': sc[2],
                      'profile': (best or {}).get('profile') or '', 'profile_fp': (best or {}).get('profile_fp') or '',
                      'confidence': (best or {}).get('confidence') or '', 'sample': rec.get('sample', 0),
                      'feedback': (best or {}).get('feedback')})
    cands = rank(cands)
    chosen = cands[0] if cands else None
    checks = []
    if chosen:
        row = next(r for r in rows if r['id'] == chosen['printer_id'])
        checks.append(dict(zip(('level', 'code'), check_file(norm, chosen['resin'])), id='file'))
        checks.append(dict(zip(('level', 'code'), check_printer_state({'status': chosen['status']})), id='printer'))
        checks += _resin_checks(conn, uid, row, norm) if chosen['resin'] else _filament_checks(uid, norm)
    else:
        checks.append({'id': 'file', 'level': 'block', 'code': check_file(norm, False)[1] if _ext(norm) in RAW_MODEL else 'no_printer'})
    return {'file': os.path.basename(norm), 'material': material or '', 'candidates': cands[:4], 'chosen': chosen, 'checks': checks,
            'blocked': any(c['level'] == 'block' for c in checks)}


def _run_dict(r):
    try:
        prop = json.loads(r['proposal_json'] or '{}')
    except ValueError:
        prop = {}
    return {'id': r['id'], 'file_name': r['file_name'], 'file_path': r['file_path'], 'material': r['material'], 'status': r['status'], 'printer_id': r['printer_id'],
            'printer_name': r['printer_name'], 'profile': r['profile'], 'proposal': prop, 'history_id': r['history_id'], 'note': r['note'],
            'created_at': r['created_at'], 'validated_at': r['validated_at'], 'sent_at': r['sent_at'], 'ended_at': r['ended_at']}


def _own_run(conn, rid):
    return conn.execute("SELECT * FROM production_runs WHERE id = ? AND user_id = ?", (rid, session['user_id'])).fetchone()


def api_production_propose():
    d = request.get_json(silent=True) or {}
    path = str(d.get('file_path') or '')
    if not path or not os.path.isfile(path):
        return jsonify({'error': 'file_not_found'}), 404
    if not _is_path_within_sources(path, session['user_id']):
        return jsonify({'error': 'forbidden'}), 403
    material = str(d.get('material') or '').strip()[:40]
    conn = get_db()
    try:
        _ensure(conn)
        prop = build_proposal(conn, session['user_id'], path, material)
        ch = prop['chosen'] or {}
        cur = conn.execute("INSERT INTO production_runs (user_id, file_path, file_name, material, status, printer_id, printer_name, profile, proposal_json, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (session['user_id'], path, os.path.basename(path), material, 'proposed', ch.get('printer_id'), ch.get('printer_name') or '', ch.get('profile') or '', json.dumps(prop, ensure_ascii=False), time.time()))
        conn.commit()
        return jsonify(_run_dict(conn.execute("SELECT * FROM production_runs WHERE id = ?", (cur.lastrowid, )).fetchone()))
    except Exception as e:
        app_logger.error(f"[PRODUCTION] Proposition impossible : {e}")
        return jsonify({'error': 'internal'}), 500
    finally:
        conn.close()


def api_production_list():
    conn = get_db()
    try:
        _ensure(conn)
        rows = conn.execute("SELECT * FROM production_runs WHERE user_id = ? ORDER BY id DESC LIMIT 30", (session['user_id'], )).fetchall()
        return jsonify({'runs': [_run_dict(r) for r in rows]})
    finally:
        conn.close()


def api_production_validate(rid):
    """Validation humaine : choix final de l'imprimante et du profil. Refusée si un contrôle bloque sur l'imprimante choisie."""
    d = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        _ensure(conn)
        r = _own_run(conn, rid)
        if not r:
            return jsonify({'error': 'not_found'}), 404
        if r['status'] not in ('proposed', 'validated'):
            return jsonify({'error': 'bad_state'}), 409
        prop = json.loads(r['proposal_json'] or '{}')
        cands = {c['printer_id']: c for c in prop.get('candidates') or []}
        pid = d.get('printer_id', r['printer_id'])
        try:
            pid = int(pid)
        except (TypeError, ValueError):
            return jsonify({'error': 'bad_printer'}), 400
        if pid not in cands:
            return jsonify({'error': 'bad_printer'}), 400
        row = conn.execute("SELECT * FROM printers WHERE id = ? AND user_id = ?", (pid, session['user_id'])).fetchone()
        if not row:
            return jsonify({'error': 'not_found'}), 404
        try:
            status = _printer_status_cached(parse_printer_config(row)) or {}
        except Exception:
            status = {'status': 'offline'}
        lvl, code = check_printer_state(status)
        resin = cands[pid]['resin']
        fl, fcode = check_file(r['file_path'], resin)
        extra = _resin_checks(conn, session['user_id'], row, r['file_path']) if resin else []
        blockers = [c for c in [{'level': lvl, 'code': code}, {'level': fl, 'code': fcode}] + extra if c['level'] == 'block']
        if blockers:
            return jsonify({'error': 'blocked', 'checks': blockers}), 409
        profile = str(d.get('profile') if d.get('profile') is not None else (cands[pid].get('profile') or ''))[:200]
        conn.execute("UPDATE production_runs SET status = 'validated', printer_id = ?, printer_name = ?, profile = ?, validated_at = ? WHERE id = ?",
                     (pid, row['name'] or '', profile, time.time(), rid))
        conn.commit()
        return jsonify(_run_dict(_own_run(conn, rid)))
    finally:
        conn.close()


def _record_history(conn, uid, run, row):
    path = run['file_path']
    try:
        size = os.path.getsize(path)
    except OSError:
        size = 0
    cur = conn.execute("INSERT INTO print_history (user_id, file_path, file_name, file_size, file_ext, slicer, source_platform, slicer_profile_name, printer_id, filament_material) VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (uid, path.replace('\\', '/'), run['file_name'], size, _ext(path), '', 'production', run['profile'] or '', row['id'], run['material'] or ''))
    hid = cur.lastrowid
    try:
        from modules import print_traceability
        print_traceability.record(conn, uid, hid, path.replace('\\', '/'), path)
    except Exception:
        pass
    return hid


def api_production_send(rid):
    """Envoi après validation. Aucune impression n'est démarrée à distance : le fichier arrive sur l'imprimante, la personne la lance."""
    conn = get_db()
    try:
        _ensure(conn)
        r = _own_run(conn, rid)
        if not r:
            return jsonify({'error': 'not_found'}), 404
        if r['status'] != 'validated':
            return jsonify({'error': 'not_validated'}), 409
        row = conn.execute("SELECT * FROM printers WHERE id = ? AND user_id = ?", (r['printer_id'], session['user_id'])).fetchone()
        if not row or not os.path.isfile(r['file_path']) or not _is_path_within_sources(r['file_path'], session['user_id']):
            return jsonify({'error': 'not_found'}), 404
        try:
            status = _printer_status_cached(parse_printer_config(row)) or {}
        except Exception:
            status = {'status': 'offline'}
        if check_printer_state(status)[0] == 'block':
            return jsonify({'error': 'printer_offline'}), 409
        try:
            ok = bool(printer_hub.upload_file(parse_printer_config(row), r['file_path']))
        except Exception as e:
            app_logger.info(f"[PRODUCTION] Envoi impossible : {e}")
            ok = False
        if not ok:
            conn.execute("UPDATE production_runs SET status = 'send_failed', note = ? WHERE id = ?", ('upload', rid))
            conn.commit()
            return jsonify({'error': 'send_failed'}), 502
        hid = _record_history(conn, session['user_id'], r, row)
        conn.execute("UPDATE production_runs SET status = 'sent', sent_at = ?, history_id = ? WHERE id = ?", (time.time(), hid, rid))
        try:
            from modules import intelligence
            prop = json.loads(r['proposal_json'] or '{}')
            rec = next((c for c in prop.get('candidates') or [] if c['printer_id'] == (prop.get('chosen') or {}).get('printer_id')), {})
            intelligence.record_feedback(conn, session['user_id'], rid, row['id'], r['material'], r['file_path'].replace('\\', '/'), rec.get('profile'), rec.get('profile_fp'), r['profile'])
        except Exception as e:
            app_logger.debug(f"[PRODUCTION] Retour d'expérience non enregistré : {e}")
        conn.commit()
        return jsonify(_run_dict(_own_run(conn, rid)))
    finally:
        conn.close()


def _close_run(conn, run, result, note=''):
    """Clôt une exécution envoyée : résultat dans l'historique et dans le retour d'expérience d'Intelligence."""
    status = {'success': 'finished', 'failed': 'failed', 'partial': 'failed'}.get(result)
    if not status:
        return False
    conn.execute("UPDATE production_runs SET status = ?, ended_at = ?, note = ? WHERE id = ?", (status, time.time(), note or run['note'] or '', run['id']))
    if run['history_id']:
        conn.execute("UPDATE print_history SET result = ?, rated_at = CURRENT_TIMESTAMP WHERE id = ? AND COALESCE(result, '') = ''", (result, run['history_id']))
    try:
        from modules import intelligence
        intelligence.finish_feedback(conn, run['id'], result)
    except Exception:
        pass
    conn.commit()
    return True


def api_production_result(rid):
    """Résultat saisi par la personne (quand la surveillance n'a pas vu la fin) : success | failed | partial."""
    d = request.get_json(silent=True) or {}
    result = d.get('result')
    if result not in ('success', 'failed', 'partial'):
        return jsonify({'error': 'bad_result'}), 400
    conn = get_db()
    try:
        _ensure(conn)
        r = _own_run(conn, rid)
        if not r:
            return jsonify({'error': 'not_found'}), 404
        if r['status'] != 'sent':
            return jsonify({'error': 'bad_state'}), 409
        _close_run(conn, r, result, 'manual')
        return jsonify(_run_dict(_own_run(conn, rid)))
    finally:
        conn.close()


def api_production_cancel(rid):
    conn = get_db()
    try:
        _ensure(conn)
        r = _own_run(conn, rid)
        if not r:
            return jsonify({'error': 'not_found'}), 404
        if r['status'] not in ('proposed', 'validated', 'send_failed'):
            return jsonify({'error': 'bad_state'}), 409
        conn.execute("UPDATE production_runs SET status = 'cancelled', ended_at = ? WHERE id = ?", (time.time(), rid))
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


def _has_sent_runs():
    conn = get_db()
    try:
        _ensure(conn)
        return conn.execute("SELECT 1 FROM production_runs WHERE status = 'sent' AND sent_at > ? LIMIT 1", (time.time() - MATCH_WINDOW_S, )).fetchone() is not None
    finally:
        conn.close()


def on_print_event(ev):
    """Écouteur de print_events : relie la fin d'une impression à l'exécution envoyée sur cette imprimante avec ce nom de fichier."""
    p = ev.get('printer') or {}
    name = os.path.basename(str(ev.get('file') or '').replace('\\', '/')).lower()
    if not name or p.get('id') is None:
        return
    conn = get_db()
    try:
        _ensure(conn)
        r = conn.execute("SELECT * FROM production_runs WHERE status = 'sent' AND printer_id = ? AND lower(file_name) = ? AND sent_at > ? ORDER BY id DESC LIMIT 1",
                         (p['id'], name, time.time() - MATCH_WINDOW_S)).fetchone()
        if not r:
            return
        ok = ev.get('event') == 'finished'
        _close_run(conn, r, 'success' if ok else 'failed', 'auto')
        if _insert_notification_once:
            try:
                title = _server_t('notif.production_done_title' if ok else 'notif.production_failed_title', 'Production terminée' if ok else 'Production échouée') if _server_t else ''
                _insert_notification_once(r['user_id'], 'production_result', title, f"{r['file_name']} — {p.get('name') or ''}", 'production', f"production:{r['id']}")
            except Exception:
                pass
    except Exception as e:
        app_logger.info(f"[PRODUCTION] Résultat non relié : {e}")
    finally:
        conn.close()


_ROUTES = (
    ('/api/production', ['GET'], 'api_production_list', ('login_required', )),
    ('/api/production/propose', ['POST'], 'api_production_propose', ('login_required', )),
    ('/api/production/<int:rid>/validate', ['POST'], 'api_production_validate', ('login_required', )),
    ('/api/production/<int:rid>/send', ['POST'], 'api_production_send', ('login_required', )),
    ('/api/production/<int:rid>/result', ['POST'], 'api_production_result', ('login_required', )),
    ('/api/production/<int:rid>/cancel', ['POST'], 'api_production_cancel', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals), enregistre les routes et branche l'écouteur de fin d'impression."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"production_flow.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
        try:
            from modules import print_events
            print_events.register_listener(on_print_event, _has_sent_runs)
        except Exception as e:
            app_logger.info(f"[PRODUCTION] Écouteur non branché : {e}")
    return {}
