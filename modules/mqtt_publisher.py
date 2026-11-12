"""Stellio — publication MQTT / Home Assistant (imprimantes, bobines, état de l'application)

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `mqtt_publisher.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import datetime
import json
import os
import re
import requests
import ssl
import threading
import time
import uuid

_REQUIRED = (
    'AUTO_BACKUP_NAME_RE',
    'CURRENT_VERSION',
    'DB_PATH',
    'GITHUB_API_URL',
    'HAS_MQTT',
    'IS_SERVER_EDITION',
    '_auto_backup_folder',
    '_get_manual_filament_slots',
    '_get_spoolman_slots',
    '_get_tigertag_slots',
    '_job_margin',
    '_load_auto_backup_config',
    '_maintenance_eta',
    '_printer_hours_per_day',
    '_printer_status_cached',
    '_server_edition_only',
    '_ws_state',
    'app',
    'app_logger',
    'get_current_version',
    'get_db',
    'jsonify',
    'load_file_cache',
    'load_settings',
    'login_required',
    'parse_printer_config',
    'request',
    'version',
)
_OPTIONAL = ('mqtt', )   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('datetime', 'json', 'os', 're', 'requests', 'ssl', 'threading', 'time', 'uuid', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
mqtt = None
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
AUTO_BACKUP_NAME_RE = None
CURRENT_VERSION = None
DB_PATH = None
GITHUB_API_URL = None
HAS_MQTT = None
IS_SERVER_EDITION = None
_auto_backup_folder = None
_get_manual_filament_slots = None
_get_spoolman_slots = None
_get_tigertag_slots = None
_job_margin = None
_load_auto_backup_config = None
_maintenance_eta = None
_printer_hours_per_day = None
_printer_status_cached = None
_server_edition_only = None
_ws_state = None
app = None
app_logger = None
get_current_version = None
get_db = None
jsonify = None
load_file_cache = None
load_settings = None
login_required = None
parse_printer_config = None
request = None
version = None


# ══════════════════════════════════════════════════════════════════════════════════════════════
# v0.8.7 — Intégration MQTT / Home Assistant (publication d'état + découverte automatique)
# ══════════════════════════════════════════════════════════════════════════════════════════════
_MQTT_PUB = {'client': None, 'sig': None, 'connected': False, 'error': '', 'discovered': set(),
             'prev': {}, 'last_publish': 0.0, 'count': 0}

_MQTT_PUB_LOCK = threading.Lock()

HA_DISCOVERY_PREFIX = 'homeassistant'

def _mqtt_pub_cfg(override=None):
    s = dict(load_settings() or {})
    if override:
        for k, v in override.items():
            if str(k).startswith('mqtt_'):
                s[k] = v
    host = str(s.get('mqtt_host') or '').strip()
    if not host:
        return None
    tls = bool(s.get('mqtt_tls'))
    try:
        port = int(s.get('mqtt_port') or (8883 if tls else 1883))
    except (TypeError, ValueError):
        port = 8883 if tls else 1883
    base = re.sub(r'[^\w\-/]+', '_', str(s.get('mqtt_base') or 'stellio').strip('/ ')) or 'stellio'
    try:
        interval = max(5, min(300, int(s.get('mqtt_interval') or 15)))
    except (TypeError, ValueError):
        interval = 15
    return {'enabled': bool(s.get('mqtt_enabled')), 'host': host, 'port': port, 'user': str(s.get('mqtt_user') or ''),
            'password': str(s.get('mqtt_password') or ''), 'tls': tls, 'tls_insecure': bool(s.get('mqtt_tls_insecure')),
            'base': base, 'discovery': s.get('mqtt_discovery', True) is not False, 'interval': interval,
            'prefix': re.sub(r'[^\w\-/]+', '_', str(s.get('mqtt_discovery_prefix') or HA_DISCOVERY_PREFIX).strip('/ ')) or HA_DISCOVERY_PREFIX}

def _mqtt_new_client(cfg, tag):
    cid = f"stellio_{tag}_{uuid.uuid4().hex[:6]}"
    try:
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1, client_id=cid, protocol=mqtt.MQTTv311, clean_session=True)
    except TypeError:
        client = mqtt.Client(client_id=cid, protocol=mqtt.MQTTv311, clean_session=True)
    if cfg['user']:
        client.username_pw_set(cfg['user'], cfg['password'])
    if cfg['tls']:
        client.tls_set(cert_reqs=ssl.CERT_NONE if cfg['tls_insecure'] else ssl.CERT_REQUIRED)
        if cfg['tls_insecure']:
            client.tls_insecure_set(True)
    return client

def _mqtt_state_payload(p, st):
    t = st.get('time') or {}
    temps = st.get('temps') or {}
    active = st.get('status') in ('printing', 'paused')
    return {
        'name': p.get('name') or '', 'status': st.get('status') or 'offline',
        'progress': round(float(st.get('progress') or 0), 1) if active else 0,
        'file': os.path.basename(str(st.get('file') or '').replace('\\', '/')) if active else '',
        'remaining': int(t.get('remaining') or 0) if active else 0,
        'elapsed': int(t.get('elapsed') or 0) if active else 0,
        'extruder': (temps.get('extruder') or {}).get('current'),
        'bed': (temps.get('bed') or {}).get('current'),
        'chamber': (temps.get('chamber') or {}).get('current'),
        'layer': int((st.get('layers') or {}).get('current') or 0) if active else 0,
        'layers_total': int((st.get('layers') or {}).get('total') or 0) if active else 0,
        'hours': round(float(p.get('total_print_hours') or 0), 1),
        'maintenance_days': (_MQTT_APP_CACHE['data'].get('maint_by_printer') or {}).get(p.get('id')),
        'spool_low': bool((_ws_state.get(p.get('id')) or {}).get('low')),
        'drift': bool((_ws_state.get(p.get('id')) or {}).get('drift')),
    }

def _mqtt_discovery_configs(cfg, p):
    pid, base = p['id'], cfg['base']
    state = f"{base}/printer/{pid}/state"
    dev = {'identifiers': [f"stellio_{pid}"], 'name': p.get('name') or f"Imprimante {pid}", 'manufacturer': 'Stellio', 'model': str(p.get('type') or '')}
    common = {'state_topic': state, 'device': dev, 'availability_topic': f"{base}/status",
              'payload_available': 'online', 'payload_not_available': 'offline'}
    ents = [
        ('sensor', 'status', {'name': 'Status', 'value_template': '{{ value_json.status }}', 'icon': 'mdi:printer-3d'}),
        ('sensor', 'progress', {'name': 'Progress', 'value_template': '{{ value_json.progress }}', 'unit_of_measurement': '%', 'state_class': 'measurement', 'icon': 'mdi:progress-clock'}),
        ('sensor', 'remaining', {'name': 'Time remaining', 'value_template': '{{ (value_json.remaining | float(0) / 60) | round(0) }}', 'unit_of_measurement': 'min', 'icon': 'mdi:timer-sand'}),
        ('sensor', 'file', {'name': 'File', 'value_template': '{{ value_json.file }}', 'icon': 'mdi:file-cad'}),
        ('sensor', 'nozzle', {'name': 'Nozzle temperature', 'value_template': '{{ value_json.extruder }}', 'unit_of_measurement': '°C', 'device_class': 'temperature', 'state_class': 'measurement'}),
        ('sensor', 'bed', {'name': 'Bed temperature', 'value_template': '{{ value_json.bed }}', 'unit_of_measurement': '°C', 'device_class': 'temperature', 'state_class': 'measurement'}),
        ('binary_sensor', 'printing', {'name': 'Printing', 'value_template': "{{ 'ON' if value_json.status == 'printing' else 'OFF' }}", 'device_class': 'running'}),
        ('sensor', 'chamber', {'name': 'Chamber temperature', 'value_template': '{{ value_json.chamber }}', 'unit_of_measurement': '°C', 'device_class': 'temperature', 'state_class': 'measurement'}),
        ('sensor', 'layer', {'name': 'Current layer', 'value_template': '{{ value_json.layer }}', 'state_class': 'measurement', 'icon': 'mdi:layers'}),
        ('sensor', 'layers_total', {'name': 'Total layers', 'value_template': '{{ value_json.layers_total }}', 'state_class': 'measurement', 'icon': 'mdi:layers-triple'}),
        ('sensor', 'hours', {'name': 'Print hours', 'value_template': '{{ value_json.hours }}', 'unit_of_measurement': 'h', 'device_class': 'duration', 'state_class': 'total_increasing', 'icon': 'mdi:clock-outline'}),
        ('sensor', 'maintenance_days', {'name': 'Next maintenance', 'value_template': "{{ 'unknown' if value_json.maintenance_days is none else value_json.maintenance_days }}", 'unit_of_measurement': 'd', 'icon': 'mdi:wrench-clock'}),
        ('binary_sensor', 'spool_low', {'name': 'Spool almost empty', 'value_template': "{{ 'ON' if value_json.spool_low else 'OFF' }}", 'device_class': 'problem', 'icon': 'mdi:printer-3d-nozzle'}),
        ('binary_sensor', 'drift', {'name': 'Print drift', 'value_template': "{{ 'ON' if value_json.drift else 'OFF' }}", 'device_class': 'problem', 'icon': 'mdi:alert-circle'}),
    ]
    out = []
    for comp, key, extra in ents:
        topic = f"{cfg['prefix']}/{comp}/stellio_{pid}/{key}/config"
        out.append((topic, {**common, **extra, 'unique_id': f"stellio_{pid}_{key}", 'object_id': f"stellio_{pid}_{key}"}))
    return out

def _mqtt_publish_all(client, cfg):
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM printers").fetchall()
    finally:
        conn.close()
    seen = set()
    states = []
    for row in rows:
        p = parse_printer_config(row)
        pid = p['id']
        seen.add(pid)
        st = _printer_status_cached(p, ttl=2.0)
        payload = _mqtt_state_payload(p, st)
        states.append(payload['status'])
        if cfg['discovery'] and pid not in _MQTT_PUB['discovered']:
            for topic, conf in _mqtt_discovery_configs(cfg, p):
                client.publish(topic, json.dumps(conf, ensure_ascii=False), qos=1, retain=True)
            _MQTT_PUB['discovered'].add(pid)
        client.publish(f"{cfg['base']}/printer/{pid}/state", json.dumps(payload, ensure_ascii=False), qos=0, retain=True)
        _MQTT_PUB['count'] += 1
        prev = _MQTT_PUB['prev'].get(pid)
        cur = payload['status']
        if prev == 'printing' and cur in ('idle', 'complete', 'error'):
            ev = 'print_failed' if cur == 'error' else 'print_finished'
            client.publish(f"{cfg['base']}/printer/{pid}/event", json.dumps({'event': ev, 'printer': payload['name'], 'file': _MQTT_PUB.get('last_file', {}).get(pid, '')}, ensure_ascii=False), qos=1, retain=False)
        _MQTT_PUB['prev'][pid] = cur
        if payload['file']:
            _MQTT_PUB.setdefault('last_file', {})[pid] = payload['file']
    try:
        _mqtt_app_publish(client, cfg, states)
    except Exception as e:
        app_logger.info(f"[MQTT] Appareil Stellio: {e}")
    # imprimantes supprimées : on retire leurs entités de Home Assistant
    for pid in list(_MQTT_PUB['discovered'] - seen):
        for topic, _conf in _mqtt_discovery_configs(cfg, {'id': pid, 'name': '', 'type': ''}):
            client.publish(topic, '', qos=1, retain=True)
        _MQTT_PUB['discovered'].discard(pid)

# ── Appareil « Stellio » : l'application elle-même (bibliothèque, impressions, atelier, commerce…) ──
_APP_STARTED = time.time()

_MQTT_APP_CACHE = {'t': 0.0, 'data': {}}

_MQTT_APP_STATE_TOPIC = '{base}/app/state'

# (composant, clé, nom, extras, réservé au commerce)
_MQTT_APP_ENTITIES = [
    ('sensor', 'files_total', 'Files', {'icon': 'mdi:file-multiple', 'state_class': 'measurement'}, False),
    ('sensor', 'files_stl', 'STL files', {'icon': 'mdi:cube-outline', 'state_class': 'measurement'}, False),
    ('sensor', 'files_3mf', '3MF files', {'icon': 'mdi:cube-scan', 'state_class': 'measurement'}, False),
    ('sensor', 'files_gcode', 'G-code files', {'icon': 'mdi:code-braces', 'state_class': 'measurement'}, False),
    ('sensor', 'files_other', 'Other files', {'icon': 'mdi:file-question-outline', 'state_class': 'measurement'}, False),
    ('sensor', 'files_new_month', 'New files this month', {'icon': 'mdi:file-plus', 'state_class': 'measurement'}, False),
    ('sensor', 'library_size', 'Library size', {'unit_of_measurement': 'GB', 'device_class': 'data_size', 'state_class': 'measurement', 'icon': 'mdi:harddisk'}, False),
    ('sensor', 'sources', 'File sources', {'icon': 'mdi:folder-network', 'state_class': 'measurement'}, False),
    ('sensor', 'favorites', 'Favorites', {'icon': 'mdi:star', 'state_class': 'measurement'}, False),
    ('sensor', 'projects', 'Projects', {'icon': 'mdi:folder-star-multiple', 'state_class': 'measurement'}, False),
    ('sensor', 'photos', 'Print photos', {'icon': 'mdi:image-multiple', 'state_class': 'measurement'}, False),
    ('sensor', 'print_queue', 'Print queue', {'icon': 'mdi:format-list-numbered', 'state_class': 'measurement'}, False),
    ('sensor', 'prints_total', 'Prints sent', {'icon': 'mdi:printer-3d', 'state_class': 'total_increasing'}, False),
    ('sensor', 'prints_today', 'Prints today', {'icon': 'mdi:calendar-today', 'state_class': 'measurement'}, False),
    ('sensor', 'prints_7d', 'Prints (7 days)', {'icon': 'mdi:calendar-week', 'state_class': 'measurement'}, False),
    ('sensor', 'prints_30d', 'Prints (30 days)', {'icon': 'mdi:calendar-month', 'state_class': 'measurement'}, False),
    ('sensor', 'prints_failed', 'Failed prints', {'icon': 'mdi:alert-octagon', 'state_class': 'total_increasing'}, False),
    ('sensor', 'success_rate', 'Success rate', {'unit_of_measurement': '%', 'icon': 'mdi:check-decagram', 'state_class': 'measurement'}, False),
    ('sensor', 'print_hours', 'Print hours', {'unit_of_measurement': 'h', 'icon': 'mdi:clock-outline', 'state_class': 'total_increasing'}, False),
    ('sensor', 'printers_total', 'Printers', {'icon': 'mdi:printer-3d-nozzle', 'state_class': 'measurement'}, False),
    ('sensor', 'printers_online', 'Printers online', {'icon': 'mdi:lan-connect', 'state_class': 'measurement'}, False),
    ('sensor', 'printers_printing', 'Printers printing', {'icon': 'mdi:printer-3d', 'state_class': 'measurement'}, False),
    ('sensor', 'spools', 'Manual spools', {'icon': 'mdi:circle-slice-8', 'state_class': 'measurement'}, False),
    ('sensor', 'spools_remaining', 'Manual spools remaining', {'unit_of_measurement': 'kg', 'device_class': 'weight', 'icon': 'mdi:weight-kilogram', 'state_class': 'measurement'}, False),
    ('sensor', 'maintenance_due', 'Maintenance due', {'icon': 'mdi:wrench-clock', 'state_class': 'measurement'}, False),
    ('sensor', 'notifications', 'Unread notifications', {'icon': 'mdi:bell-badge', 'state_class': 'measurement'}, False),
    ('sensor', 'spent_total', 'Print cost (total)', {'icon': 'mdi:cash', 'state_class': 'total_increasing'}, True),
    ('sensor', 'spent_month', 'Print cost (this month)', {'icon': 'mdi:cash-clock', 'state_class': 'measurement'}, True),
    ('sensor', 'quotes_pending', 'Quotes awaiting answer', {'icon': 'mdi:file-document-outline', 'state_class': 'measurement'}, True),
    ('sensor', 'invoices_unpaid', 'Unpaid invoices', {'icon': 'mdi:file-document-alert', 'state_class': 'measurement'}, True),
    ('sensor', 'invoices_unpaid_total', 'Unpaid amount', {'icon': 'mdi:cash-remove', 'state_class': 'measurement'}, True),
    ('sensor', 'invoices_overdue', 'Overdue invoices', {'icon': 'mdi:calendar-alert', 'state_class': 'measurement'}, True),
    ('sensor', 'clients', 'Customers', {'icon': 'mdi:account-group', 'state_class': 'measurement'}, True),
    ('sensor', 'orders_open', 'Open orders', {'icon': 'mdi:clipboard-list', 'state_class': 'measurement'}, True),
    ('sensor', 'orders_late', 'Late orders', {'icon': 'mdi:clipboard-alert', 'state_class': 'measurement'}, True),
    ('binary_sensor', 'has_overdue', 'Overdue invoice', {'device_class': 'problem', 'icon': 'mdi:cash-clock', 'bool_of': 'invoices_overdue'}, True),
    ('binary_sensor', 'has_maintenance', 'Maintenance needed', {'device_class': 'problem', 'icon': 'mdi:wrench', 'bool_of': 'maintenance_due'}, False),
    ('sensor', 'orders_next_due', 'Next order delivery', {'device_class': 'date', 'icon': 'mdi:truck-delivery'}, True),
    ('sensor', 'orders_pieces_left', 'Parts left to print', {'icon': 'mdi:cube-send', 'state_class': 'measurement'}, True),
    ('sensor', 'margin_est', 'Expected order margin', {'icon': 'mdi:chart-line', 'state_class': 'measurement'}, True),
    ('sensor', 'margin_real', 'Actual order margin', {'icon': 'mdi:chart-areaspline', 'state_class': 'measurement'}, True),
    ('binary_sensor', 'alert_spool_low', 'Spool almost empty', {'device_class': 'problem', 'icon': 'mdi:printer-3d-nozzle', 'bool_of': 'alerts_spool_low'}, False),
    ('binary_sensor', 'alert_drift', 'Print drift', {'device_class': 'problem', 'icon': 'mdi:alert-circle', 'bool_of': 'alerts_drift'}, False),
    ('sensor', 'last_backup', 'Last backup', {'device_class': 'timestamp', 'icon': 'mdi:backup-restore', 'entity_category': 'diagnostic'}, False),
    ('binary_sensor', 'update_available', 'Update available', {'device_class': 'update', 'icon': 'mdi:update', 'bool_of': 'update_flag', 'entity_category': 'diagnostic'}, False),
    ('sensor', 'latest_version', 'Latest version', {'icon': 'mdi:tag-arrow-up', 'entity_category': 'diagnostic'}, False),
    ('sensor', 'version', 'Version', {'icon': 'mdi:tag', 'entity_category': 'diagnostic'}, False),
    ('sensor', 'uptime', 'Uptime', {'unit_of_measurement': 'h', 'device_class': 'duration', 'icon': 'mdi:timer-outline', 'entity_category': 'diagnostic'}, False),
    ('sensor', 'db_size', 'Database size', {'unit_of_measurement': 'MB', 'device_class': 'data_size', 'icon': 'mdi:database', 'entity_category': 'diagnostic'}, False),
    ('sensor', 'users', 'Accounts', {'icon': 'mdi:account', 'entity_category': 'diagnostic'}, False),
]

_MQTT_SPOOLS = {'t': 0.0, 'slots': []}

_MQTT_UPDATE = {'t': 0.0, 'latest': '', 'avail': None, 'busy': False}

def _mqtt_spool_key(slot):
    return re.sub(r'\W+', '_', f"spool_{slot.get('source_type')}_{slot.get('source_id')}").strip('_')[:60]

def _mqtt_spool_slots():
    """Bobines Spoolman, TigerTag et manuelles (une entité chacune). Relues toutes les 5 min : Spoolman et TigerTag sont des appels réseau."""
    if time.time() - _MQTT_SPOOLS['t'] < 300:
        return _MQTT_SPOOLS['slots']
    slots, ok = [], True
    try:
        conn = get_db()
        try:
            uids = [r['id'] for r in conn.execute("SELECT id FROM users").fetchall()]
        finally:
            conn.close()
        url = str((load_settings() or {}).get('spoolman_url') or '').strip().rstrip('/')
        if url:
            sm, err = _get_spoolman_slots(url)
            if err:
                ok = False
            slots.extend(sm)
        for uid in uids:
            slots.extend(_get_manual_filament_slots(uid))
            slots.extend(_get_tigertag_slots(uid))
    except Exception as e:
        ok = False
        app_logger.info(f"[MQTT] Bobines: {e}")
    if ok or not _MQTT_SPOOLS['slots']:
        seen, out = set(), []
        for sl in slots:
            if sl.get('source_type') not in ('spoolman', 'tigertag', 'manual'):
                continue
            k = _mqtt_spool_key(sl)
            if k in seen:
                continue
            seen.add(k)
            out.append({'key': k, 'name': str(sl.get('name') or k)[:60], 'material': str(sl.get('material') or ''),
                        'remaining_g': sl.get('remaining_g')})
        _MQTT_SPOOLS['slots'] = out
    _MQTT_SPOOLS['t'] = time.time()
    return _MQTT_SPOOLS['slots']

def _mqtt_update_probe():
    """Vérifie la dernière version publiée au plus toutes les 6 h, dans un fil à part (appel réseau)."""
    if _MQTT_UPDATE['busy'] or time.time() - _MQTT_UPDATE['t'] < 6 * 3600:
        return
    _MQTT_UPDATE['busy'] = True

    def _run():
        try:
            r = requests.get(GITHUB_API_URL, timeout=10, headers={'User-Agent': f'Stellio-App/{CURRENT_VERSION}'})
            if r.status_code == 200:
                latest = str(r.json().get('tag_name', '')).lstrip('vV')
                _MQTT_UPDATE['latest'] = latest
                _MQTT_UPDATE['avail'] = bool(latest) and version.parse(latest) > version.parse(get_current_version())
        except Exception:
            pass
        finally:
            _MQTT_UPDATE['t'] = time.time()
            _MQTT_UPDATE['busy'] = False
    threading.Thread(target=_run, daemon=True, name='stellio-mqtt-update').start()

def _mqtt_last_backup_iso():
    try:
        folder = _auto_backup_folder(_load_auto_backup_config(), create=False)
        best = 0.0
        for n in os.listdir(folder):
            if AUTO_BACKUP_NAME_RE.match(n):
                best = max(best, os.stat(os.path.join(folder, n)).st_mtime)
        return datetime.datetime.fromtimestamp(best).astimezone().isoformat(timespec='seconds') if best else None
    except Exception:
        return None

def _mqtt_app_entities():
    """Entités existantes : fixes (sans celles du commerce si désactivé) + une par bobine."""
    commercial = (load_settings() or {}).get('commercial_enabled', True) is not False
    ents = [e for e in _MQTT_APP_ENTITIES if commercial or not e[4]]
    for sl in _mqtt_spool_slots():
        label = sl['name'] + (f" ({sl['material']})" if sl['material'] else '')
        ents.append(('sensor', sl['key'], f"Spool {label}", {'unit_of_measurement': 'g', 'device_class': 'weight', 'state_class': 'measurement',
                                                           'icon': 'mdi:printer-3d-nozzle', 'spool': True}, False))
    return ents

def _mqtt_app_wanted():
    return _mqtt_app_entities()

def _mqtt_app_metrics(force=False):
    """Instantané de l'application (mis en cache 60 s : on ne relit pas toute la base à chaque publication)."""
    if not force and time.time() - _MQTT_APP_CACHE['t'] < 60 and _MQTT_APP_CACHE['data']:
        return _MQTT_APP_CACHE['data']
    m = {}
    now = datetime.datetime.now()
    fmt = lambda d: d.strftime('%Y-%m-%d %H:%M:%S')

    def q1(conn, sql, args=(), default=0):
        try:
            r = conn.execute(sql, args).fetchone()
            return (r[0] if r and r[0] is not None else default)
        except Exception:
            return default

    try:
        cached = load_file_cache() or []
        m['files_total'] = len(cached)
        counts = {'stl': 0, '3mf': 0, 'gcode': 0, 'other': 0}
        month_ts = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).timestamp()
        size = 0
        new_month = 0
        for f in cached:
            ext = (f.get('extension') or '').lower().lstrip('.')
            counts['gcode' if ext in ('gcode', 'bgcode', 'gco') else ext if ext in ('stl', '3mf') else 'other'] += 1
            size += f.get('size', 0) or 0
            if (f.get('mtime') or 0) >= month_ts:
                new_month += 1
        m.update(files_stl=counts['stl'], files_3mf=counts['3mf'], files_gcode=counts['gcode'], files_other=counts['other'],
                 files_new_month=new_month, library_size=round(size / 1e9, 2))
    except Exception:
        pass
    conn = get_db()
    try:
        today = fmt(now.replace(hour=0, minute=0, second=0, microsecond=0))
        m['sources'] = q1(conn, "SELECT COUNT(*) FROM sources")
        m['favorites'] = q1(conn, "SELECT COUNT(*) FROM favorites")
        m['projects'] = q1(conn, "SELECT COUNT(*) FROM projects")
        m['photos'] = q1(conn, "SELECT COUNT(*) FROM print_photos")
        m['print_queue'] = q1(conn, "SELECT COUNT(*) FROM print_queue")
        m['prints_total'] = q1(conn, "SELECT COUNT(*) FROM print_history")
        m['prints_today'] = q1(conn, "SELECT COUNT(*) FROM print_history WHERE sent_at>=?", (today,))
        m['prints_7d'] = q1(conn, "SELECT COUNT(*) FROM print_history WHERE sent_at>=?", (fmt(now - datetime.timedelta(days=7)),))
        m['prints_30d'] = q1(conn, "SELECT COUNT(*) FROM print_history WHERE sent_at>=?", (fmt(now - datetime.timedelta(days=30)),))
        ok = q1(conn, "SELECT COUNT(*) FROM print_history WHERE result='success'")
        failed = q1(conn, "SELECT COUNT(*) FROM print_history WHERE result='failed'")
        m['prints_failed'] = failed
        m['success_rate'] = round(100 * ok / (ok + failed), 1) if (ok + failed) else None
        m['print_hours'] = round(q1(conn, "SELECT COALESCE(SUM(actual_seconds),0) FROM print_history") / 3600, 1)
        m['spools'] = q1(conn, "SELECT COUNT(*) FROM manual_filament_spools WHERE COALESCE(archived,0)=0")
        m['spools_remaining'] = round(q1(conn, "SELECT COALESCE(SUM(remaining_g),0) FROM manual_filament_spools WHERE COALESCE(archived,0)=0") / 1000, 2)
        m['notifications'] = q1(conn, "SELECT COUNT(*) FROM notifications WHERE is_read=0")
        m['users'] = q1(conn, "SELECT COUNT(*) FROM users")
        m['spent_total'] = round(q1(conn, "SELECT COALESCE(SUM(total_cost),0) FROM print_history WHERE total_cost IS NOT NULL"), 2)
        m['spent_month'] = round(q1(conn, "SELECT COALESCE(SUM(total_cost),0) FROM print_history WHERE total_cost IS NOT NULL AND sent_at>=?",
                                    (fmt(now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)),)), 2)
        # commerce
        todayd = datetime.date.today().isoformat()
        try:
            qrows = conn.execute("SELECT doc_type, status, due_date, total_value FROM quotes").fetchall()
        except Exception:
            qrows = []
        pend = unpaid = overdue = 0
        unpaid_total = 0.0
        for r in qrows:
            dt = r['doc_type'] or 'quote'
            st = r['status'] or 'draft'
            if dt == 'quote' and st in ('draft', 'sent'):
                pend += 1
            elif dt in ('invoice', 'deposit') and st != 'paid':
                unpaid += 1
                unpaid_total += float(r['total_value'] or 0)
                if r['due_date'] and r['due_date'] < todayd:
                    overdue += 1
        m.update(quotes_pending=pend, invoices_unpaid=unpaid, invoices_unpaid_total=round(unpaid_total, 2), invoices_overdue=overdue)
        m['clients'] = q1(conn, "SELECT COUNT(*) FROM clients")
        m['orders_open'] = q1(conn, "SELECT COUNT(*) FROM print_jobs WHERE status IN ('queued','printing')")
        m['orders_late'] = q1(conn, "SELECT COUNT(*) FROM print_jobs WHERE status IN ('queued','printing') AND due_date!='' AND due_date<?", (todayd,))
        # maintenance
        due = 0
        try:
            tasks = conn.execute("SELECT t.*, p.total_print_hours AS total FROM printer_maintenance_tasks t JOIN printers p ON p.id=t.printer_id").fetchall()
            rates = {}
            for t in tasks:
                if t['printer_id'] not in rates:
                    rates[t['printer_id']] = _printer_hours_per_day(conn, t['printer_id'])
                if _maintenance_eta(t, t['total'] or 0, rates[t['printer_id']]) == 0.0:
                    due += 1
        except Exception:
            pass
        m['maintenance_due'] = due
        eta_by = {}
        try:
            for t in tasks:
                e = _maintenance_eta(t, t['total'] or 0, rates.get(t['printer_id']))
                if e is not None:
                    eta_by[t['printer_id']] = min(e, eta_by.get(t['printer_id'], e))
        except Exception:
            pass
        m['maint_by_printer'] = {k: round(v, 1) for k, v in eta_by.items()}
        # commandes
        m['orders_next_due'] = q1(conn, "SELECT MIN(due_date) FROM print_jobs WHERE status IN ('queued','printing') AND due_date!=''", default=None)
        m['orders_pieces_left'] = q1(conn, "SELECT COALESCE(SUM(MAX(quantity-qty_done,0)),0) FROM print_jobs WHERE status IN ('queued','printing')")
        try:
            totals = {r['id']: r['total_value'] or 0 for r in conn.execute("SELECT id, total_value FROM quotes").fetchall()}
            est = real = 0.0
            for r in conn.execute("SELECT * FROM print_jobs WHERE status!='cancelled'").fetchall():
                mg = _job_margin(r, totals.get(r['quote_id'], 0))
                if mg:
                    est += mg['est_margin']
                    if r['qty_done']:
                        real += mg['real_margin']
            m['margin_est'], m['margin_real'] = round(est, 2), round(real, 2)
        except Exception:
            m['margin_est'] = m['margin_real'] = None
    finally:
        conn.close()
    try:
        m['db_size'] = round(os.path.getsize(DB_PATH) / 1e6, 1)
    except Exception:
        m['db_size'] = None
    m['last_backup'] = _mqtt_last_backup_iso()
    _mqtt_update_probe()
    m['version'] = CURRENT_VERSION
    m['uptime'] = round((time.time() - _APP_STARTED) / 3600, 2)
    _MQTT_APP_CACHE.update(t=time.time(), data=m)
    return m

def _mqtt_app_state(m, printers_state):
    out = dict(m)
    out['printers_total'] = len(printers_state)
    out['printers_online'] = sum(1 for s in printers_state if s not in ('offline', 'error', 'timeout', None))
    out['printers_printing'] = sum(1 for s in printers_state if s == 'printing')
    out['alerts_spool_low'] = sum(1 for v in _ws_state.values() if v.get('low'))
    out['alerts_drift'] = sum(1 for v in _ws_state.values() if v.get('drift'))
    out['update_flag'] = 1 if _MQTT_UPDATE['avail'] else 0
    out['latest_version'] = _MQTT_UPDATE['latest'] or None
    out['spools_detail'] = {sl['key']: sl['remaining_g'] for sl in _mqtt_spool_slots()}
    out.pop('maint_by_printer', None)
    return out

def _mqtt_app_discovery(cfg, ents=None):
    base = cfg['base']
    dev = {'identifiers': ['stellio_app'], 'name': 'Stellio', 'manufacturer': 'Stellio', 'model': 'Application', 'sw_version': CURRENT_VERSION}
    common = {'state_topic': _MQTT_APP_STATE_TOPIC.format(base=base), 'device': dev, 'availability_topic': f"{base}/status",
              'payload_available': 'online', 'payload_not_available': 'offline'}
    out = []
    for comp, key, name, extra, _commerce in (ents if ents is not None else _MQTT_APP_ENTITIES):
        extra = dict(extra)
        boolof = extra.pop('bool_of', None)
        spool = extra.pop('spool', False)
        conf = {**common, **extra, 'name': name, 'unique_id': f"stellio_app_{key}", 'object_id': f"stellio_app_{key}"}
        if comp == 'binary_sensor':
            conf['value_template'] = "{{ 'ON' if (value_json.%s | int(0)) > 0 else 'OFF' }}" % boolof
        elif spool:
            conf['value_template'] = "{%% set v = value_json.spools_detail.get('%s') %%}{{ 'unknown' if v is none else v }}" % key
        else:
            conf['value_template'] = "{{ 'unknown' if value_json.%s is none else value_json.%s }}" % (key, key)
        out.append((f"{cfg['prefix']}/{comp}/stellio_app/{key}/config", key, conf))
    return out

def _mqtt_app_publish(client, cfg, printers_state, qos=0, wait=None):
    """Publie l'appareil Stellio : configs de découverte (seulement si elles ont changé) puis l'état."""
    ents = _mqtt_app_entities()
    wanted = {e[1]: e[0] for e in ents}
    prev = _MQTT_PUB.get('app_keys')
    if cfg['discovery'] and prev != wanted:
        for topic, key, conf in _mqtt_app_discovery(cfg, ents):
            r = client.publish(topic, json.dumps(conf, ensure_ascii=False), qos=1, retain=True)
            if wait is not None:
                wait.append(r)
        # entités disparues (commerce désactivé, bobine retirée) : on vide leur configuration retenue
        gone = {k: c for k, c in (prev or {}).items() if k not in wanted}
        if prev is None:
            gone.update({e[1]: e[0] for e in _MQTT_APP_ENTITIES if e[1] not in wanted})
        for key, comp in gone.items():
            r = client.publish(f"{cfg['prefix']}/{comp}/stellio_app/{key}/config", '', qos=1, retain=True)
            if wait is not None:
                wait.append(r)
        _MQTT_PUB['app_keys'] = wanted
    state = _mqtt_app_state(_mqtt_app_metrics(), printers_state)
    r = client.publish(_MQTT_APP_STATE_TOPIC.format(base=cfg['base']), json.dumps(state, ensure_ascii=False), qos=qos, retain=True)
    if wait is not None:
        wait.append(r)
    return state

def _mqtt_pub_disconnect():
    c = _MQTT_PUB.get('client')
    _MQTT_PUB['client'] = None
    _MQTT_PUB['connected'] = False
    if c:
        try:
            c.publish(f"{(_MQTT_PUB.get('sig') or ('',))[0]}/status", 'offline', qos=1, retain=True)
        except Exception:
            pass
        try:
            c.loop_stop()
            c.disconnect()
        except Exception:
            pass

def _mqtt_pub_tick():
    cfg = _mqtt_pub_cfg()
    if not IS_SERVER_EDITION or not HAS_MQTT or not cfg or not cfg['enabled']:
        if _MQTT_PUB['client']:
            with _MQTT_PUB_LOCK:
                _mqtt_pub_disconnect()
                _MQTT_PUB['sig'] = None
        return
    sig = (cfg['base'], cfg['host'], cfg['port'], cfg['user'], cfg['password'], cfg['tls'], cfg['tls_insecure'], cfg['discovery'], cfg['prefix'])
    with _MQTT_PUB_LOCK:
        if _MQTT_PUB['client'] is None or _MQTT_PUB['sig'] != sig:
            if _MQTT_PUB['client']:
                _mqtt_pub_disconnect()
            _MQTT_PUB['discovered'] = set()
            _MQTT_PUB['app_keys'] = None
            client = _mqtt_new_client(cfg, 'pub')
            client.will_set(f"{cfg['base']}/status", 'offline', qos=1, retain=True)

            def _on_connect(c, userdata, flags, rc, *a):
                if rc == 0:
                    _MQTT_PUB['connected'] = True
                    _MQTT_PUB['error'] = ''
                    _MQTT_PUB['discovered'] = set()
                    _MQTT_PUB['app_keys'] = None
                    c.publish(f"{cfg['base']}/status", 'online', qos=1, retain=True)
                else:
                    _MQTT_PUB['connected'] = False
                    _MQTT_PUB['error'] = {4: 'identifiants refusés', 5: 'non autorisé'}.get(rc, f'code {rc}')

            def _on_disconnect(c, userdata, rc, *a):
                _MQTT_PUB['connected'] = False

            client.on_connect = _on_connect
            client.on_disconnect = _on_disconnect
            try:
                client.reconnect_delay_set(min_delay=2, max_delay=60)
                client.connect_async(cfg['host'], cfg['port'], keepalive=60)
                client.loop_start()
                _MQTT_PUB['client'] = client
                _MQTT_PUB['sig'] = sig
            except Exception as e:
                _MQTT_PUB['error'] = str(e)[:120]
                return
        client = _MQTT_PUB['client']
    if client is not None and _MQTT_PUB['connected'] and time.time() - _MQTT_PUB['last_publish'] >= cfg['interval']:
        _MQTT_PUB['last_publish'] = time.time()
        _mqtt_publish_all(client, cfg)

def _mqtt_pub_loop():
    time.sleep(25)
    while True:
        try:
            _mqtt_pub_tick()
        except Exception as e:
            _MQTT_PUB['error'] = str(e)[:120]
            app_logger.info(f"[MQTT] Erreur boucle: {e}")
        time.sleep(3)

def _start_mqtt_publisher():
    threading.Thread(target=_mqtt_pub_loop, daemon=True, name='stellio-mqtt-ha').start()

def api_mqtt_status():
    blocked = _server_edition_only()
    if blocked:
        return blocked
    cfg = _mqtt_pub_cfg()
    return jsonify({"available": bool(HAS_MQTT), "enabled": bool(cfg and cfg['enabled']),
                    "connected": bool(_MQTT_PUB['connected']), "error": _MQTT_PUB['error'],
                    "published": _MQTT_PUB['count'], "host": (cfg or {}).get('host', ''), "discovery": bool(cfg and cfg['discovery'])})

def api_mqtt_entities():
    """Liste des entités publiées vers Home Assistant (avec leur valeur actuelle)."""
    blocked = _server_edition_only()
    if blocked:
        return blocked
    cfg = _mqtt_pub_cfg()
    out = {"enabled": bool(cfg and cfg['enabled']), "connected": bool(_MQTT_PUB['connected']),
           "discovery": bool(cfg and cfg['discovery']), "base": cfg['base'] if cfg else 'stellio', "printers": []}
    if not cfg:
        return jsonify(out)
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM printers").fetchall()
    finally:
        conn.close()
    for row in rows:
        p = parse_printer_config(row)
        try:
            payload = _mqtt_state_payload(p, _printer_status_cached(p, ttl=5.0))
        except Exception:
            payload = _mqtt_state_payload(p, {})
        values = {'status': payload['status'], 'progress': payload['progress'], 'remaining': round(payload['remaining'] / 60),
                  'file': payload['file'], 'nozzle': payload['extruder'], 'bed': payload['bed'],
                  'printing': 'ON' if payload['status'] == 'printing' else 'OFF',
                  'chamber': payload['chamber'], 'layer': payload['layer'], 'layers_total': payload['layers_total'],
                  'hours': payload['hours'], 'maintenance_days': payload['maintenance_days'],
                  'spool_low': 'ON' if payload['spool_low'] else 'OFF', 'drift': 'ON' if payload['drift'] else 'OFF'}
        ents = []
        for topic, conf in _mqtt_discovery_configs(cfg, p):
            key = conf['unique_id'].split('_', 2)[2]
            ents.append({"key": key, "name": conf['name'], "component": topic.split('/')[1], "unique_id": conf['unique_id'],
                         "unit": conf.get('unit_of_measurement', ''), "value": values.get(key)})
        out["printers"].append({"id": p['id'], "name": p.get('name') or f"#{p['id']}", "state_topic": f"{cfg['base']}/printer/{p['id']}/state",
                                "event_topic": f"{cfg['base']}/printer/{p['id']}/event", "entities": ents})
    try:
        pstates = [pr['entities'][0]['value'] for pr in out['printers'] if pr['entities']]
        values = _mqtt_app_state(_mqtt_app_metrics(), pstates)
        app_ents = []
        for comp, key, name, extra, _c in _mqtt_app_entities():
            if comp == 'binary_sensor':
                val = 'ON' if (values.get(extra.get('bool_of')) or 0) > 0 else 'OFF'
            elif extra.get('spool'):
                val = values.get('spools_detail', {}).get(key)
            else:
                val = values.get(key)
            app_ents.append({"key": key, "name": name, "component": comp, "unique_id": f"stellio_app_{key}",
                             "unit": extra.get('unit_of_measurement', ''), "value": val})
        out["app"] = {"name": "Stellio", "state_topic": _MQTT_APP_STATE_TOPIC.format(base=cfg['base']), "entities": app_ents}
    except Exception as e:
        app_logger.info(f"[MQTT] Entités Stellio: {e}")
    return jsonify(out)

def api_mqtt_test():
    blocked = _server_edition_only()
    if blocked:
        return blocked
    if not HAS_MQTT:
        return jsonify({"success": False, "error": "paho-mqtt n'est pas installé"}), 200
    cfg = _mqtt_pub_cfg(request.json or {})
    if not cfg:
        return jsonify({"success": False, "error": "Adresse du broker manquante"}), 200
    result = {'rc': None}
    done = threading.Event()
    client = _mqtt_new_client(cfg, 'test')

    def _on_connect(c, userdata, flags, rc, *a):
        result['rc'] = rc
        done.set()
    client.on_connect = _on_connect
    published = 0
    try:
        client.connect_async(cfg['host'], cfg['port'], keepalive=20)
        client.loop_start()
        ok = done.wait(7)
        if ok and result['rc'] == 0:
            # Le test publie réellement les entités (comme le ferait la publication normale),
            # pour qu'elles apparaissent tout de suite dans Home Assistant.
            infos = []
            test_states = []
            conn = get_db()
            try:
                rows = conn.execute("SELECT * FROM printers").fetchall()
            finally:
                conn.close()
            if cfg['enabled']:
                infos.append(client.publish(f"{cfg['base']}/status", 'online', qos=1, retain=True))
            for row in rows:
                p = parse_printer_config(row)
                try:
                    st = _printer_status_cached(p, ttl=5.0)
                except Exception:
                    st = {}
                if cfg['discovery']:
                    for topic, conf in _mqtt_discovery_configs(cfg, p):
                        infos.append(client.publish(topic, json.dumps(conf, ensure_ascii=False), qos=1, retain=True))
                infos.append(client.publish(f"{cfg['base']}/printer/{p['id']}/state", json.dumps(_mqtt_state_payload(p, st), ensure_ascii=False), qos=1, retain=True))
                published += 1
                test_states.append((st or {}).get('status'))
            try:
                _MQTT_PUB['app_keys'] = None
                _mqtt_app_publish(client, cfg, test_states, qos=1, wait=infos)
                published += 1
            except Exception as e:
                app_logger.info(f"[MQTT] Test appareil Stellio: {e}")
            for i in infos:
                try:
                    i.wait_for_publish(3)
                except Exception:
                    pass
    except Exception as e:
        return jsonify({"success": False, "error": f"{type(e).__name__}: {str(e)[:100]}"}), 200
    finally:
        try:
            client.loop_stop()
            client.disconnect()
        except Exception:
            pass
    if not ok:
        return jsonify({"success": False, "error": "Aucune réponse du broker (adresse, port ou pare-feu ?)"}), 200
    if result['rc'] != 0:
        return jsonify({"success": False, "error": {4: 'Identifiant ou mot de passe refusé', 5: 'Non autorisé'}.get(result['rc'], f"Connexion refusée (code {result['rc']})")}), 200
    return jsonify({"success": True, "printers": published, "discovery": cfg['discovery'], "prefix": cfg['prefix'], "enabled": cfg['enabled']}), 200


_ROUTES = (
    ('/api/mqtt/status', ['GET'], 'api_mqtt_status', ('login_required', )),
    ('/api/mqtt/entities', ['GET'], 'api_mqtt_entities', ('login_required', )),
    ('/api/mqtt/test', ['POST'], 'api_mqtt_test', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"mqtt_publisher.init : services manquants : {missing}")
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
