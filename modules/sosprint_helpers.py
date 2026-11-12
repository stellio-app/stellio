"""Stellio — S.O.S Print : conversations, cas de référence, réglages

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `sosprint_helpers.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import base64
import json
import os
import re

_REQUIRED = (
    'SOSPRINT_CONV_PHOTOS_DIR',
    'get_db',
    'session',
)
_OPTIONAL = ()   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('base64', 'json', 'os', 're', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
SOSPRINT_CONV_PHOTOS_DIR = None
get_db = None
session = None


SOSPRINT_SOFT_QUESTIONS = 4

SOSPRINT_HARD_MAX_QUESTIONS = 30

def _sosprint_get_conversation(conv_id, user_id):
    conn = get_db()
    try:
        conv = conn.execute(
            "SELECT * FROM sos_print_conversations WHERE id=? AND user_id=?",
            (conv_id, user_id)
        ).fetchone()
        if not conv:
            return None, []
        messages = conn.execute(
            "SELECT * FROM sos_print_messages WHERE conversation_id=? ORDER BY created_at ASC, id ASC",
            (conv_id,)
        ).fetchall()
        return conv, messages
    finally:
        conn.close()

def _sosprint_touch_conversation(conv_id, **fields):
    if not fields:
        return
    sets = ", ".join(f"{k}=?" for k in fields.keys())
    values = list(fields.values()) + [conv_id]
    conn = get_db()
    try:
        conn.execute(
            f"UPDATE sos_print_conversations SET {sets}, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            values
        )
        conn.commit()
    finally:
        conn.close()

def _sosprint_add_message(conv_id, role, content='', image_filename=None):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO sos_print_messages (conversation_id, role, content, image_filename) VALUES (?, ?, ?, ?)",
            (conv_id, role, content, image_filename)
        )
        conn.commit()
    finally:
        conn.close()

def _sosprint_conversation_photos_b64(conv_id, max_photos=3):
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT image_filename FROM sos_print_messages
               WHERE conversation_id=? AND image_filename IS NOT NULL
               ORDER BY created_at DESC, id DESC LIMIT ?""",
            (conv_id, max_photos)
        ).fetchall()
    finally:
        conn.close()
    out = []
    for r in rows:
        path = os.path.join(SOSPRINT_CONV_PHOTOS_DIR, r['image_filename'])
        try:
            with open(path, 'rb') as f:
                out.append(base64.b64encode(f.read()).decode('utf-8'))
        except Exception:
            continue
    return out

def _sosprint_resolved_reference_cases(user_id, material, description, exclude_conv_id=None, limit=3):
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT id, material, description, resolution_note, last_causes, updated_at
               FROM sos_print_conversations
               WHERE user_id=? AND status='resolved' AND resolution_note != ''
               ORDER BY updated_at DESC LIMIT 40""",
            (user_id,)
        ).fetchall()
    finally:
        conn.close()

    stopwords = {
        'le','la','les','de','des','du','un','une','et','ou','a','au','aux','en','sur','dans',
        'mon','ma','mes','avec','pour','ce','cette','ces','est','sont','plus','moins','tres',
        'the','and','with','for','has','have','this','that'
    }
    desc_words = {
        re.sub(r'[^a-zà-ÿ0-9]', '', w.lower())
        for w in (description or '').split()
    }
    desc_words = {w for w in desc_words if len(w) >= 4 and w not in stopwords}

    scored = []
    for r in rows:
        if exclude_conv_id and r['id'] == exclude_conv_id:
            continue
        score = 0
        if (r['material'] or '').upper() == (material or '').upper():
            score += 2
        row_words = {
            re.sub(r'[^a-zà-ÿ0-9]', '', w.lower())
            for w in (r['description'] or '').split()
        }
        score += len(desc_words & row_words)
        if score > 0:
            scored.append((score, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for score, r in scored[:limit]:
        try:
            causes = json.loads(r['last_causes']) if r['last_causes'] else []
        except Exception:
            causes = []
        out.append({
            "description": r['description'],
            "resolution_note": r['resolution_note'],
            "causes": causes,
        })
    return out

def _sosprint_reference_cases_block(cases: list) -> str:
    if not cases:
        return ""
    lines = []
    for c in cases:
        lines.append(
            f"- Problem: \"{(c['description'] or '')[:150]}\" → Confirmed working fix: "
            f"\"{(c['resolution_note'] or '')[:200]}\""
        )
    return (
        "Reference: this user has already SOLVED these similar problems before (confirmed fixes, "
        "not just hypotheses). Give them real weight if they match the current case:\n"
        + "\n".join(lines) + "\n"
    )

def _sosprint_section(raw_text: str, start_marker: str, end_marker: str = None) -> str:
    idx = raw_text.upper().find(start_marker.upper())
    if idx == -1:
        return ""
    start = idx + len(start_marker)
    if end_marker:
        end_idx = raw_text.upper().find(end_marker.upper(), start)
        if end_idx != -1:
            return raw_text[start:end_idx].strip()
    return raw_text[start:].strip()

def _sosprint_parse_causes(block: str, max_items: int = 6) -> list:
    causes = []
    for line in block.splitlines():
        line = line.strip()
        line = re.sub(r'^[-*•]\s*', '', line)
        line = re.sub(r'^\d+[\.\)]\s*', '', line)
        line = line.strip(' .')
        if line:
            causes.append(line)
        if len(causes) >= max_items:
            break
    return causes

def _sosprint_parse_eliminated(block: str) -> list:
    first_line = block.splitlines()[0].strip() if block.strip() else ''
    if not first_line or first_line.strip('. ').lower() in ('none', 'aucun', 'aucune'):
        return []
    return [e.strip(' .') for e in first_line.split(',') if e.strip(' .')]

# Réglages d'impression renseignés par l'utilisateur pour le S.O.S Print : valeurs bornées, champs connus uniquement
SOSPRINT_SETTING_FIELDS = {
    'nozzle_temp':         ('Nozzle temperature', '°C', 120, 450),
    'bed_temp':            ('Bed temperature', '°C', 0, 150),
    'layer_height':        ('Layer height', 'mm', 0.04, 1.5),
    'print_speed':         ('Print speed', 'mm/s', 1, 1000),
    'first_layer_speed':   ('First layer speed', 'mm/s', 1, 500),
    'retraction_distance': ('Retraction distance', 'mm', 0, 20),
    'retraction_speed':    ('Retraction speed', 'mm/s', 1, 200),
    'fan_speed':           ('Cooling fan speed', '%', 0, 100),
    'infill':              ('Infill density', '%', 0, 100),
}

def _sosprint_clean_settings(raw) -> dict:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw) if raw.strip() else {}
        except Exception:
            return {}
    if not isinstance(raw, dict):
        return {}
    out = {}
    for key, (_label, _unit, low, high) in SOSPRINT_SETTING_FIELDS.items():
        value = raw.get(key)
        if value in (None, ''):
            continue
        try:
            num = float(str(value).replace(',', '.'))
        except (TypeError, ValueError):
            continue
        if not (low <= num <= high):      # écarte aussi NaN et l'infini
            continue
        out[key] = int(num) if num == int(num) else round(num, 3)
    notes = re.sub(r'\s+', ' ', str(raw.get('notes') or '')).strip()[:500]
    if notes:
        out['notes'] = notes
    profile_name = re.sub(r'\s+', ' ', str(raw.get('profile_name') or '')).strip()[:120]
    if profile_name:
        out['profile_name'] = profile_name
        profile_slicer = re.sub(r'[^A-Za-z0-9 _.-]+', '', str(raw.get('profile_slicer') or '')).strip()[:40]
        if profile_slicer:
            out['profile_slicer'] = profile_slicer
        state = str(raw.get('profile_state') or '').strip().lower()
        if state in ('unchanged', 'modified'):
            out['profile_state'] = state
            changes = re.sub(r'\s+', ' ', str(raw.get('profile_changes') or '')).strip()[:500]
            if state == 'modified' and changes:
                out['profile_changes'] = changes
    return out

def _sosprint_settings_block(settings) -> str:
    cleaned = _sosprint_clean_settings(settings)
    if not cleaned:
        return ''
    parts = [f"{label}: {cleaned[key]} {unit}" for key, (label, unit, _lo, _hi) in SOSPRINT_SETTING_FIELDS.items() if key in cleaned]
    block = ""
    if cleaned.get('profile_name'):
        slicer_txt = f" ({cleaned['profile_slicer']})" if cleaned.get('profile_slicer') else ""
        block += f"The user printed with the slicer profile \"{cleaned['profile_name']}\"{slicer_txt}. "
        state = cleaned.get('profile_state')
        if state == 'unchanged':
            block += "They confirm they used it unchanged, so the values below are the real print settings.\n"
        elif state == 'modified':
            block += "They changed some settings compared to this profile; the values below are the ones they entered and are the real print settings."
            if cleaned.get('profile_changes'):
                block += f" What they say they changed: \"{cleaned['profile_changes']}\"."
            block += "\n"
        else:
            block += ("They did not say whether they changed anything compared to this profile: the values below come from the profile "
                      "and may differ from what was really used; if it matters, you may ask once whether some settings were modified.\n")
    block += "Print settings used when the print failed (entered by the user, treat them as facts): " + \
            ("; ".join(parts) if parts else "none given besides the remarks below") + ".\n"
    if cleaned.get('notes'):
        block += f"Other settings or remarks from the user: \"{cleaned['notes']}\"\n"
    block += (
        "Use these values to target your answer: name the exact slicer setting to change and a concrete value "
        "to try, relative to the current value (for example \"nozzle 215 °C → 205 °C\"); do not suggest changing "
        "a setting that already looks appropriate for this material; do not ask about a setting already given.\n"
    )
    return block

def _sosprint_conversation_settings_block(conversation_id) -> str:
    try:
        conv, _msgs = _sosprint_get_conversation(int(conversation_id), session['user_id'])
        if conv and 'print_settings' in conv.keys():
            return _sosprint_settings_block(conv['print_settings'])
    except Exception:
        pass
    return ''


_ROUTES = (
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"sosprint_helpers.init : services manquants : {missing}")
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
