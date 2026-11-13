"""Stellio — OpenPrintTag (étiquettes NFC de bobines, standard ouvert de Prusa Research, licence MIT)

Spécification : https://github.com/OpenPrintTag/openprinttag-specification — Stellio lit et écrit ce format nativement :
  • import / export d'un fichier de tag (`.bin` : image complète du tag NFC-V, ou message NDEF, ou charge utile brute) ;
  • lecture / écriture NFC depuis l'application Android (le serveur fait le codage, l'application ne fait que lire/écrire les octets) ;
  • mise à jour de la zone auxiliaire (poids consommé) sans toucher au reste du tag, comme le demande la spécification.

Module séparé de main.py (même schéma que filament_weighing.py) : main.py appelle `openprinttag.init(globals())`.
Le codec CBOR / NDEF est en Python pur (aucune dépendance) ; les tests le comparent à la bibliothèque `cbor2`.
"""
import base64
import json
import struct
import uuid as _uuid

_REQUIRED = (
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'session',
)
_OPTIONAL = ('send_file',)
_OVERRIDABLE = ()

_MAIN = {}
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None
send_file = None

MIME_TYPE = b'application/vnd.openprinttag'
NS_BRAND = _uuid.UUID('5269dfb7-1559-440a-85be-aba5f3eff2d2')
NS_MATERIAL = _uuid.UUID('616fc86d-7d99-4953-96c7-46d2836b9be9')
NS_PACKAGE = _uuid.UUID('6f7d485e-db8d-4979-904e-a231cd6602b2')
NS_INSTANCE = _uuid.UUID('31062f81-b5bd-4f86-a5f8-46367e841508')

# ── Tables de la spécification (data/*.yaml du dépôt OpenPrintTag) ──────────────────────────────────────────────────
MAIN_KEYS = {
    'instance_uuid': (0, 'uuid'), 'package_uuid': (1, 'uuid'), 'material_uuid': (2, 'uuid'), 'brand_uuid': (3, 'uuid'),
    'gtin': (4, 'int'), 'brand_specific_instance_id': (5, 'str'), 'brand_specific_package_id': (6, 'str'),
    'brand_specific_material_id': (7, 'str'), 'material_class': (8, 'int'), 'material_type': (9, 'int'),
    'material_name': (10, 'str'), 'brand_name': (11, 'str'), 'write_protection': (13, 'int'),
    'manufactured_date': (14, 'int'), 'expiration_date': (15, 'int'), 'nominal_netto_full_weight': (16, 'num'),
    'actual_netto_full_weight': (17, 'num'), 'empty_container_weight': (18, 'num'), 'primary_color': (19, 'color'),
    'secondary_color_0': (20, 'color'), 'secondary_color_1': (21, 'color'), 'secondary_color_2': (22, 'color'),
    'secondary_color_3': (23, 'color'), 'secondary_color_4': (24, 'color'), 'transmission_distance': (27, 'num'),
    'tags': (28, 'ints'), 'density': (29, 'num'), 'filament_diameter': (30, 'num'), 'hardness_shore_a': (31, 'int'),
    'hardness_shore_d': (32, 'int'), 'min_nozzle_diameter': (33, 'num'), 'min_print_temperature': (34, 'int'),
    'max_print_temperature': (35, 'int'), 'preheat_temperature': (36, 'int'), 'min_bed_temperature': (37, 'int'),
    'max_bed_temperature': (38, 'int'), 'min_chamber_temperature': (39, 'int'), 'max_chamber_temperature': (40, 'int'),
    'chamber_temperature': (41, 'int'), 'container_width': (42, 'int'), 'container_outer_diameter': (43, 'int'),
    'container_inner_diameter': (44, 'int'), 'container_hole_diameter': (45, 'int'),
    'viscosity_18c': (46, 'num'), 'viscosity_25c': (47, 'num'), 'viscosity_40c': (48, 'num'), 'viscosity_60c': (49, 'num'),
    'container_volumetric_capacity': (50, 'num'), 'cure_wavelength': (51, 'int'), 'material_abbreviation': (52, 'str'),
    'nominal_full_length': (53, 'num'), 'actual_full_length': (54, 'num'), 'country_of_origin': (55, 'str'),
    'certifications': (56, 'ints'), 'drying_temperature': (57, 'int'), 'drying_time': (58, 'int'),
    'primary_color_lab': (59, 'lab'), 'primary_color_ral': (60, 'str'),
}
MAIN_BY_KEY = {v[0]: (k, v[1]) for k, v in MAIN_KEYS.items()}
AUX_KEYS = {'consumed_weight': (0, 'num'), 'workgroup': (1, 'str'), 'general_purpose_range_user': (2, 'str'),
            'last_stir_time': (3, 'int')}
AUX_BY_KEY = {v[0]: (k, v[1]) for k, v in AUX_KEYS.items()}
META_KEYS = {0: 'main_region_offset', 1: 'main_region_size', 2: 'aux_region_offset', 3: 'aux_region_size'}

MATERIAL_TYPES = {0: 'PLA', 1: 'PETG', 2: 'TPU', 3: 'ABS', 4: 'ASA', 5: 'PC', 6: 'PCTG', 7: 'PP', 8: 'PA6', 9: 'PA11',
                  10: 'PA12', 11: 'PA66', 12: 'CPE', 13: 'TPE', 14: 'HIPS', 15: 'PHA', 16: 'PET', 17: 'PEI', 18: 'PBT',
                  19: 'PVB', 20: 'PVA', 21: 'PEKK', 22: 'PEEK', 23: 'BVOH', 24: 'TPC', 25: 'PPS', 26: 'PPSU', 27: 'PVC',
                  28: 'PEBA', 29: 'PVDF', 30: 'PPA', 31: 'PCL', 32: 'PES', 33: 'PMMA', 34: 'POM', 35: 'PPE', 36: 'PS',
                  37: 'PSU', 38: 'TPI', 39: 'SBS', 40: 'OBC', 41: 'EVA', 42: 'PA612'}
MATERIAL_BY_NAME = {v: k for k, v in MATERIAL_TYPES.items()}
MATERIAL_CLASSES = {0: 'FFF', 1: 'SLA'}
CERTIFICATIONS = {0: 'ul_2818', 1: 'ul_94_v0', 2: 'ul_2904'}
TAGS = {0: 'filtration_recommended', 1: 'biocompatible', 2: 'antibacterial', 3: 'air_filtering', 4: 'abrasive',
        5: 'foaming', 6: 'self_extinguishing', 7: 'paramagnetic', 8: 'radiation_shielding', 9: 'high_temperature',
        10: 'esd_safe', 11: 'conductive', 12: 'blend', 13: 'water_soluble', 14: 'ipa_soluble', 15: 'limonene_soluble',
        16: 'matte', 17: 'silk', 19: 'translucent', 20: 'transparent', 21: 'iridescent', 22: 'pearlescent',
        23: 'glitter', 24: 'glow_in_the_dark', 25: 'neon', 26: 'illuminescent_color_change',
        27: 'temperature_color_change', 28: 'gradual_color_change', 29: 'coextruded', 30: 'contains_carbon',
        31: 'contains_carbon_fiber', 32: 'contains_carbon_nano_tubes', 33: 'contains_glass', 34: 'contains_glass_fiber',
        35: 'contains_kevlar', 36: 'contains_stone', 37: 'contains_magnetite', 38: 'contains_organic_material',
        39: 'contains_cork', 40: 'contains_wax', 41: 'contains_wood', 42: 'contains_bamboo', 43: 'contains_pine',
        44: 'contains_ceramic', 45: 'contains_boron_carbide', 46: 'contains_metal', 47: 'contains_bronze',
        48: 'contains_iron', 49: 'contains_steel', 50: 'contains_silver', 51: 'contains_copper',
        52: 'contains_aluminium', 53: 'contains_brass', 54: 'contains_tungsten', 55: 'imitates_wood',
        56: 'imitates_metal', 57: 'imitates_marble', 58: 'imitates_stone', 59: 'lithophane', 60: 'recycled',
        61: 'home_compostable', 62: 'industrially_compostable', 63: 'bio_based', 64: 'low_outgassing',
        65: 'without_pigments', 66: 'contains_algae', 67: 'castable', 68: 'contains_ptfe', 69: 'limited_edition',
        70: 'emi_shielding', 71: 'high_speed', 72: 'contains_graphene', 73: 'uv_resistant', 74: 'acetone_soluble'}


class OptError(ValueError):
    """Données OpenPrintTag invalides ou qui ne tiennent pas dans le tag."""


# ── CBOR minimal (RFC 8949) ─────────────────────────────────────────────────────────────────────────────────────────
class _Float:
    """Nombre à virgule encodé au plus court (demi-flottant, flottant ou double) — évite les 8 octets inutiles."""
    def __init__(self, v):
        self.v = float(v)


def _head(major, n):
    if n < 24:
        return bytes([(major << 5) | n])
    if n < 256:
        return bytes([(major << 5) | 24, n])
    if n < 65536:
        return bytes([(major << 5) | 25]) + struct.pack('>H', n)
    if n < 2 ** 32:
        return bytes([(major << 5) | 26]) + struct.pack('>I', n)
    return bytes([(major << 5) | 27]) + struct.pack('>Q', n)


def compact_number(v):
    """Entier si la valeur est entière, sinon flottant le plus court qui garde 3 décimales."""
    f = float(v)
    if f.is_integer():
        return int(f)
    return _Float(f)


def _enc_float(f):
    for fmt, code in (('>e', 0xF9), ('>f', 0xFA)):
        try:
            b = struct.pack(fmt, f)
            if abs(struct.unpack(fmt, b)[0] - f) < 1e-3:
                return bytes([code]) + b
        except (OverflowError, struct.error):
            pass
    return b'\xfb' + struct.pack('>d', f)


def cbor_encode(obj, indefinite_map=False):
    if isinstance(obj, bool):
        return b'\xf5' if obj else b'\xf4'
    if obj is None:
        return b'\xf6'
    if isinstance(obj, int):
        return _head(0, obj) if obj >= 0 else _head(1, -1 - obj)
    if isinstance(obj, _Float):
        return _enc_float(obj.v)
    if isinstance(obj, float):
        return _enc_float(obj)
    if isinstance(obj, (bytes, bytearray)):
        return _head(2, len(obj)) + bytes(obj)
    if isinstance(obj, str):
        b = obj.encode('utf-8')
        return _head(3, len(b)) + b
    if isinstance(obj, (list, tuple)):
        return _head(4, len(obj)) + b''.join(cbor_encode(x) for x in obj)
    if isinstance(obj, dict):
        items = sorted(obj.items(), key=lambda kv: kv[0])
        body = b''.join(cbor_encode(k) + cbor_encode(v) for k, v in items)
        return (b'\xbf' + body + b'\xff') if indefinite_map else _head(5, len(items)) + body
    raise OptError(f'type non encodable : {type(obj).__name__}')


def _half(h):
    s, e, m = (h >> 15) & 1, (h >> 10) & 0x1F, h & 0x3FF
    if e == 0:
        v = m * 2.0 ** -24
    elif e == 31:
        v = float('inf') if m == 0 else float('nan')
    else:
        v = (1 + m / 1024.0) * 2.0 ** (e - 15)
    return -v if s else v


_BREAK = object()


def _dec(buf, i, depth=0):
    if depth > 16:
        raise OptError('CBOR trop imbriqué')
    if i >= len(buf):
        raise OptError('CBOR tronqué')
    ib = buf[i]
    major, info = ib >> 5, ib & 31
    i += 1
    if major == 7 and info == 31:
        return _BREAK, i
    if info < 24:
        n = info
    elif info in (24, 25, 26, 27):
        size = 1 << (info - 24)
        if i + size > len(buf):
            raise OptError('CBOR tronqué')
        raw = buf[i:i + size]
        i += size
        if major == 7:
            if info == 25:
                return _half(struct.unpack('>H', raw)[0]), i
            if info == 26:
                return struct.unpack('>f', raw)[0], i
            if info == 27:
                return struct.unpack('>d', raw)[0], i
            return int(raw[0]), i
        n = int.from_bytes(raw, 'big')
    elif info == 31:
        n = None
    else:
        raise OptError('CBOR invalide')
    if major == 0:
        return n, i
    if major == 1:
        return -1 - n, i
    if major in (2, 3):
        if n is None:
            chunks = b''
            while True:
                c, i = _dec(buf, i, depth + 1)
                if c is _BREAK:
                    break
                chunks += c if isinstance(c, bytes) else c.encode('utf-8')
            return (chunks if major == 2 else chunks.decode('utf-8', 'replace')), i
        if i + n > len(buf):
            raise OptError('CBOR tronqué')
        raw = bytes(buf[i:i + n])
        return (raw if major == 2 else raw.decode('utf-8', 'replace')), i + n
    if major == 4:
        out = []
        if n is None:
            while True:
                v, i = _dec(buf, i, depth + 1)
                if v is _BREAK:
                    return out, i
                out.append(v)
        for _ in range(n):
            v, i = _dec(buf, i, depth + 1)
            out.append(v)
        return out, i
    if major == 5:
        out = {}
        count = 0
        while n is None or count < n:
            k, i = _dec(buf, i, depth + 1)
            if k is _BREAK and n is None:
                return out, i
            v, i = _dec(buf, i, depth + 1)
            try:
                out[k] = v
            except TypeError:
                out[repr(k)] = v
            count += 1
        return out, i
    if major == 6:                      # étiquette sémantique : on ignore l'étiquette
        return _dec(buf, i, depth + 1)
    if info == 20:
        return False, i
    if info == 21:
        return True, i
    return None, i


def cbor_decode(buf, offset=0):
    """Décode un objet CBOR ; retourne (valeur, nombre d'octets utilisés)."""
    v, end = _dec(bytes(buf), offset)
    if v is _BREAK:
        raise OptError('CBOR invalide')
    return v, end - offset


# ── NDEF / TLV / image de tag NFC-V ─────────────────────────────────────────────────────────────────────────────────
def ndef_record(payload, mime=MIME_TYPE):
    """Enregistrement NDEF unique (MB+ME), type MIME ; format court si la charge utile tient sur un octet."""
    if len(payload) <= 255:
        return bytes([0xD2, len(mime), len(payload)]) + mime + payload
    return bytes([0xC2, len(mime)]) + struct.pack('>I', len(payload)) + mime + payload


def parse_ndef(message):
    """Retourne la liste des enregistrements NDEF [(tnf, type, charge_utile)]."""
    out, i, n = [], 0, len(message)
    while i < n:
        hdr = message[i]
        i += 1
        sr, il, tnf = bool(hdr & 0x10), bool(hdr & 0x08), hdr & 7
        if i >= n:
            raise OptError('NDEF tronqué')
        tlen = message[i]
        i += 1
        if sr:
            plen = message[i]
            i += 1
        else:
            plen = struct.unpack('>I', message[i:i + 4])[0]
            i += 4
        ilen = 0
        if il:
            ilen = message[i]
            i += 1
        typ = bytes(message[i:i + tlen])
        i += tlen + ilen
        if i + plen > n:
            raise OptError('NDEF tronqué')
        out.append((tnf, typ, bytes(message[i:i + plen])))
        i += plen
        if hdr & 0x40:                  # ME : dernier enregistrement
            break
    return out


def _tlv_ndef(mem):
    """Extrait le message NDEF (TLV 0x03) d'une image mémoire de tag, après le conteneur de capacités."""
    i = 8 if len(mem) > 8 and (mem[2] == 0 and mem[0] == 0xE2) else 4
    while i < len(mem):
        t = mem[i]
        i += 1
        if t == 0x00:
            continue
        if t == 0xFE:
            break
        if i >= len(mem):
            break
        ln = mem[i]
        i += 1
        if ln == 0xFF:
            ln = struct.unpack('>H', mem[i:i + 2])[0]
            i += 2
        if t == 0x03:
            return bytes(mem[i:i + ln])
        i += ln
    raise OptError('Aucun message NDEF dans le tag')


def build_tag_image(payload_len, tag_size=320):
    """Retourne (entête, pied) autour d'une charge utile de `payload_len` octets : CC + TLV + entête NDEF / terminateur."""
    hdr_ndef = 3 + len(MIME_TYPE) if payload_len <= 255 else 6 + len(MIME_TYPE)
    msg_len = hdr_ndef + payload_len
    cc = bytes([0xE1, 0x40, tag_size // 8, 0x01])
    tlv = bytes([0x03, msg_len]) if msg_len <= 0xFE else bytes([0x03, 0xFF]) + struct.pack('>H', msg_len)
    return cc + tlv, b'\xfe'


def extract_payload(raw):
    """Accepte une image de tag (CC E1…), un message NDEF ou une charge utile brute ; retourne la charge utile OpenPrintTag."""
    raw = bytes(raw)
    if not raw:
        raise OptError('Fichier vide')
    if raw[0] in (0xE1, 0xE2):
        raw = _tlv_ndef(raw)
        recs = parse_ndef(raw)
    elif raw[0] & 0x07 == 2 and raw[0] & 0x80 and 1 < len(raw):
        try:
            recs = parse_ndef(raw)
        except (OptError, IndexError, struct.error):
            recs = []
    else:
        recs = []
    for tnf, typ, pl in recs:
        if tnf == 2 and typ == MIME_TYPE:
            return pl
    if recs:
        raise OptError("Ce tag ne contient pas d'enregistrement OpenPrintTag")
    return raw


# ── Charge utile : méta + région principale + région auxiliaire ─────────────────────────────────────────────────────
def _typed(spec, value):
    kind = spec
    if kind == 'num':
        return compact_number(value)
    if kind in ('int',):
        return int(value)
    if kind == 'str':
        return str(value)
    if kind == 'uuid':
        return value.bytes if isinstance(value, _uuid.UUID) else _uuid.UUID(str(value)).bytes
    if kind == 'color':
        s = str(value).lstrip('#')
        if len(s) not in (6, 8):
            raise OptError('couleur invalide')
        return bytes.fromhex(s)
    if kind == 'ints':
        return [int(x) for x in value]
    if kind == 'lab':
        return [compact_number(x) for x in value]
    return value


def encode_section(fields, table, indefinite=False):
    out = {}
    for name, val in fields.items():
        if val is None or name not in table:
            continue
        key, kind = table[name]
        out[key] = _typed(kind, val)
    return cbor_encode(out, indefinite_map=indefinite)


def decode_section(data, by_key):
    """Retourne (champs connus, champs inconnus {clé: valeur})."""
    if not data:
        return {}, {}
    try:
        obj, _ = cbor_decode(data)
    except (OptError, IndexError, struct.error):
        return {}, {}
    if not isinstance(obj, dict):
        return {}, {}
    known, unknown = {}, {}
    for k, v in obj.items():
        spec = by_key.get(k) if isinstance(k, int) else None
        if not spec:
            unknown[k] = v
            continue
        name, kind = spec
        if kind == 'uuid' and isinstance(v, bytes) and len(v) == 16:
            v = str(_uuid.UUID(bytes=v))
        elif kind == 'color' and isinstance(v, bytes):
            v = '#' + v.hex()
        elif kind == 'num' and isinstance(v, (int, float)):
            v = int(v) if float(v).is_integer() else round(float(v), 3)
        known[name] = v
    return known, unknown


def encode_payload(main, aux=None, payload_size=None, aux_size=32):
    """Construit la charge utile. Sans `payload_size`, elle est la plus courte possible (tag à fixer ensuite) ;
    avec, elle est complétée de zéros jusqu'à cette taille et la zone auxiliaire est placée en fin de charge utile."""
    main_b = encode_section(main, MAIN_KEYS)
    if len(main_b) > 512:
        raise OptError('La région principale dépasse 512 octets')
    aux = aux or {}
    aux_b = encode_section(aux, AUX_KEYS, indefinite=True)
    if payload_size is None:
        asz = max(aux_size, len(aux_b)) if aux_size else 0
        msize = 0
        for _ in range(5):              # la taille de la méta dépend de l'encodage de l'offset : on itère jusqu'à stabilité
            meta_b = cbor_encode({2: msize + len(main_b), 3: asz}) if asz else cbor_encode({})
            if len(meta_b) == msize:
                break
            msize = len(meta_b)
        buf = bytearray(len(meta_b) + len(main_b) + asz)
        buf[:len(meta_b)] = meta_b
        buf[len(meta_b):len(meta_b) + len(main_b)] = main_b
        if asz:
            off = len(meta_b) + len(main_b)
            buf[off:off + len(aux_b)] = aux_b
        return bytes(buf)
    if aux_size and aux_size < len(aux_b):
        raise OptError('Zone auxiliaire trop petite')
    aux_off = payload_size - aux_size if aux_size else None
    meta = {2: aux_off, 3: aux_size} if aux_size else {}
    meta_b = cbor_encode(meta)
    if len(meta_b) + len(main_b) > (aux_off if aux_off is not None else payload_size):
        raise OptError("Les données ne tiennent pas dans ce tag")
    buf = bytearray(payload_size)
    buf[:len(meta_b)] = meta_b
    buf[len(meta_b):len(meta_b) + len(main_b)] = main_b
    if aux_off is not None:
        buf[aux_off:aux_off + len(aux_b)] = aux_b
    return bytes(buf)


def decode_payload(payload):
    """Décode une charge utile OpenPrintTag → dict avec meta, main, aux (+ champs inconnus conservés)."""
    payload = bytes(payload)
    meta_raw, meta_len = cbor_decode(payload)
    if not isinstance(meta_raw, dict):
        raise OptError('Section méta invalide')
    meta = {META_KEYS.get(k, k): v for k, v in meta_raw.items()}
    main_off = meta.get('main_region_offset', meta_len)
    aux_off = meta.get('aux_region_offset')
    main_size = meta.get('main_region_size')
    if main_size is None:
        ends = [o for o in (aux_off,) if o is not None and o > main_off]
        main_size = (min(ends) if ends else len(payload)) - main_off
    main_raw = payload[main_off:main_off + main_size]
    main, main_unknown = decode_section(main_raw, MAIN_BY_KEY)
    aux, aux_unknown = {}, {}
    if aux_off is not None:
        aux_size = meta.get('aux_region_size')
        aux_raw = payload[aux_off:(aux_off + aux_size) if aux_size else len(payload)]
        aux, aux_unknown = decode_section(aux_raw, AUX_BY_KEY)
    if not main and not main_unknown:
        raise OptError('Région principale vide ou illisible')
    return {'meta': meta, 'main': main, 'aux': aux, 'main_unknown': main_unknown, 'aux_unknown': aux_unknown}


def update_aux(payload, **changes):
    """Met à jour la zone auxiliaire (ex. consumed_weight) sans modifier la méta ni la région principale ;
    retourne la nouvelle charge utile (même taille)."""
    payload = bytearray(payload)
    meta_raw, meta_len = cbor_decode(bytes(payload))
    aux_off = meta_raw.get(2)
    if aux_off is None:
        raise OptError("Ce tag n'a pas de zone auxiliaire")
    aux_size = meta_raw.get(3) or (len(payload) - aux_off)
    cur, unknown = decode_section(bytes(payload[aux_off:aux_off + aux_size]), AUX_BY_KEY)
    cur.update({k: v for k, v in changes.items() if v is not None})
    obj = {AUX_KEYS[k][0]: _typed(AUX_KEYS[k][1], v) for k, v in cur.items() if k in AUX_KEYS}
    obj.update({k: v for k, v in unknown.items() if isinstance(k, int)})
    new = cbor_encode(obj, indefinite_map=True)
    if len(new) > aux_size:
        raise OptError('Zone auxiliaire trop petite')
    payload[aux_off:aux_off + aux_size] = new + bytes(aux_size - len(new))
    return bytes(payload)


def build_tag_file(main, aux=None, tag_size=320, aux_size=32):
    """Image complète d'un tag NFC-V (CC + TLV + NDEF + terminateur) remplissant `tag_size` octets."""
    for plen in range(tag_size - 8, 16, -1):
        head, tail = build_tag_image(plen, tag_size)
        if len(head) + 3 + len(MIME_TYPE) + (0 if plen <= 255 else 3) + plen + len(tail) <= tag_size:
            break
    payload = encode_payload(main, aux or {}, payload_size=plen, aux_size=aux_size)
    img = head + ndef_record(payload) + tail
    return img + bytes(tag_size - len(img))


# ── UUID dérivés (spécification §3.2) ───────────────────────────────────────────────────────────────────────────────
def brand_uuid(brand_name):
    return _uuid.uuid5(NS_BRAND, brand_name.encode('utf-8'))


def material_uuid(brand_name, material_name):
    return _uuid.uuid5(NS_MATERIAL, brand_uuid(brand_name).bytes + material_name.encode('utf-8'))


def instance_uuid_from_tag(tag_uid):
    return _uuid.uuid5(NS_INSTANCE, bytes(tag_uid))


# ── Correspondance bobine Stellio ↔ champs OpenPrintTag ─────────────────────────────────────────────────────────────
def _hex(c, default='#888888'):
    c = (c or '').strip()
    return c if len(c) == 7 and c.startswith('#') else default


def spool_to_tag(spool, extra=None):
    """`spool` : dict d'une ligne manual_filament_spools. Retourne (main, aux)."""
    ex = dict(extra or {})
    main = {k: v for k, v in ex.items() if k in MAIN_KEYS}
    brand = (spool.get('vendor') or '').strip()[:31]
    name = (spool.get('name') or '').strip()[:63]
    mat = (spool.get('material') or '').strip().upper()
    main['material_class'] = 0
    if brand:
        main['brand_name'] = brand
    if name:
        main['material_name'] = name
    if mat in MATERIAL_BY_NAME:
        main['material_type'] = MATERIAL_BY_NAME[mat]
    elif mat:
        main['material_abbreviation'] = mat[:7]
    cap = spool.get('capacity_g')
    if cap:
        main['nominal_netto_full_weight'] = float(cap)
        main['actual_netto_full_weight'] = float(cap)
    if spool.get('diameter_mm'):
        main['filament_diameter'] = float(spool['diameter_mm'])
    col = _hex(spool.get('color_hex'), '')
    if col:
        main['primary_color'] = col
    if spool.get('opt_instance_uuid'):
        main['instance_uuid'] = spool['opt_instance_uuid']
    aux = {}
    if spool.get('remaining_g') is not None and cap:
        aux['consumed_weight'] = max(0.0, round(float(cap) - float(spool['remaining_g']), 1))
    return main, aux


def tag_to_spool(main, aux=None):
    """Champs d'une bobine Stellio construits depuis un tag décodé (+ `extra` à conserver pour la ré-écriture)."""
    aux = aux or {}
    mt = main.get('material_type')
    material = MATERIAL_TYPES.get(mt) if mt is not None else (main.get('material_abbreviation') or '')
    cap = main.get('actual_netto_full_weight') or main.get('nominal_netto_full_weight') or 1000
    consumed = aux.get('consumed_weight') or 0
    brand = main.get('brand_name') or ''
    name = main.get('material_name') or material or 'Bobine OpenPrintTag'
    color = main.get('primary_color') or ''
    spool = {
        'name': name, 'vendor': brand, 'material': material or '',
        'color_hex': ('#' + color.lstrip('#')[:6]) if color else '#888888',
        'capacity_g': float(cap), 'remaining_g': max(0.0, round(float(cap) - float(consumed), 1)),
        'diameter_mm': float(main.get('filament_diameter') or 1.75),
        'opt_instance_uuid': main.get('instance_uuid') or '',
    }
    keep = ('package_uuid', 'material_uuid', 'brand_uuid', 'gtin', 'density', 'min_print_temperature',
            'max_print_temperature', 'preheat_temperature', 'min_bed_temperature', 'max_bed_temperature',
            'drying_temperature', 'drying_time', 'tags', 'certifications', 'hardness_shore_a', 'hardness_shore_d',
            'min_nozzle_diameter', 'country_of_origin', 'secondary_color_0', 'secondary_color_1',
            'secondary_color_2', 'secondary_color_3', 'secondary_color_4', 'empty_container_weight',
            'brand_specific_material_id', 'brand_specific_package_id', 'transmission_distance')
    extra = {k: main[k] for k in keep if k in main}
    return spool, extra


def describe(main, aux=None):
    """Version lisible (noms d'énumérations) pour l'interface."""
    out = dict(main)
    if 'material_type' in out:
        out['material_type_name'] = MATERIAL_TYPES.get(out['material_type'], str(out['material_type']))
    if 'material_class' in out:
        out['material_class_name'] = MATERIAL_CLASSES.get(out['material_class'], str(out['material_class']))
    if 'tags' in out:
        out['tag_names'] = [TAGS.get(t, str(t)) for t in out['tags']]
    if 'certifications' in out:
        out['certification_names'] = [CERTIFICATIONS.get(t, str(t)) for t in out['certifications']]
    return {'main': out, 'aux': aux or {}}


# ── Base de données ─────────────────────────────────────────────────────────────────────────────────────────────────
_COLS = ('opt_instance_uuid TEXT DEFAULT \'\'', 'opt_json TEXT DEFAULT \'\'', 'ofd_id TEXT DEFAULT \'\'')


_COLS_READY = False


def ensure_columns():
    global _COLS_READY
    if _COLS_READY:
        return
    conn = get_db()
    try:
        have = {r[1] for r in conn.execute("PRAGMA table_info(manual_filament_spools)").fetchall()}
        for col in _COLS:
            if col.split()[0] not in have:
                conn.execute(f"ALTER TABLE manual_filament_spools ADD COLUMN {col}")
        conn.commit()
    finally:
        conn.close()
    _COLS_READY = True


def _row(conn, sid, uid):
    r = conn.execute("SELECT * FROM manual_filament_spools WHERE id=? AND user_id=?", (sid, uid)).fetchone()
    return dict(r) if r else None


def _read_input():
    """Octets du tag envoyés soit en fichier (`file`), soit en base64 JSON (`payload_b64` / `data_b64`)."""
    f = request.files.get('file') if request.files else None
    if f is not None:
        data = f.read(65536)
        if not data:
            raise OptError('Fichier vide')
        return data
    body = request.get_json(silent=True) or {}
    b64 = body.get('data_b64') or body.get('payload_b64') or ''
    try:
        data = base64.b64decode(b64, validate=False)
    except Exception:
        raise OptError('Base64 invalide')
    if not data or len(data) > 65536:
        raise OptError('Données absentes ou trop volumineuses')
    return data


def _extra(row):
    try:
        return json.loads(row.get('opt_json') or '{}') or {}
    except (TypeError, ValueError):
        return {}


# ── Routes ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def api_opt_decode():
    try:
        payload = extract_payload(_read_input())
        d = decode_payload(payload)
        spool, _ = tag_to_spool(d['main'], d['aux'])
        out = describe(d['main'], d['aux'])
        out['spool'] = spool
        out['unknown_fields'] = len(d['main_unknown']) + len(d['aux_unknown'])
        return jsonify(out), 200
    except OptError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app_logger.error(f"[OPT] decode : {e}")
        return jsonify({"error": "Tag illisible"}), 400


def api_opt_import():
    """Crée une bobine depuis un tag ; si une bobine porte déjà cet instance_uuid, elle est mise à jour."""
    ensure_columns()
    try:
        d = decode_payload(extract_payload(_read_input()))
    except OptError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app_logger.error(f"[OPT] import : {e}")
        return jsonify({"error": "Tag illisible"}), 400
    spool, extra = tag_to_spool(d['main'], d['aux'])
    uid = session['user_id']
    conn = get_db()
    try:
        existing = None
        if spool['opt_instance_uuid']:
            r = conn.execute("SELECT id FROM manual_filament_spools WHERE user_id=? AND opt_instance_uuid=? LIMIT 1",
                             (uid, spool['opt_instance_uuid'])).fetchone()
            existing = r['id'] if r else None
        vals = (spool['name'], spool['material'], spool['color_hex'], spool['remaining_g'], spool['capacity_g'],
                spool['vendor'], spool['diameter_mm'], spool['opt_instance_uuid'], json.dumps(extra, sort_keys=True))
        if existing:
            conn.execute("UPDATE manual_filament_spools SET name=?, material=?, color_hex=?, remaining_g=?, capacity_g=?, "
                         "vendor=?, diameter_mm=?, opt_instance_uuid=?, opt_json=?, updated_at=CURRENT_TIMESTAMP "
                         "WHERE id=? AND user_id=?", vals + (existing, uid))
            sid, created = existing, False
        else:
            cur = conn.execute("INSERT INTO manual_filament_spools (user_id, name, material, color_hex, remaining_g, capacity_g, "
                               "source_label, vendor, diameter_mm, opt_instance_uuid, opt_json) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                               (uid, spool['name'], spool['material'], spool['color_hex'], spool['remaining_g'],
                                spool['capacity_g'], 'OpenPrintTag', spool['vendor'], spool['diameter_mm'],
                                spool['opt_instance_uuid'], json.dumps(extra, sort_keys=True)))
            sid, created = cur.lastrowid, True
        conn.commit()
    finally:
        conn.close()
    return jsonify({"success": True, "id": sid, "created": created, "spool": spool}), 200


def api_opt_export(spool_id):
    """Fichier de tag d'une bobine. ?format=bin (image complète, défaut) | ndef | json (base64 pour l'application Android)."""
    ensure_columns()
    uid = session['user_id']
    conn = get_db()
    try:
        row = _row(conn, spool_id, uid)
        if not row:
            return jsonify({"error": "Bobine introuvable"}), 404
        extra = _extra(row)
        if not row.get('opt_instance_uuid'):
            row['opt_instance_uuid'] = str(_uuid.uuid4())
            conn.execute("UPDATE manual_filament_spools SET opt_instance_uuid=? WHERE id=? AND user_id=?",
                         (row['opt_instance_uuid'], spool_id, uid))
            conn.commit()
    finally:
        conn.close()
    main, aux = spool_to_tag(row, extra)
    fmt = (request.args.get('format') or 'bin').lower()
    try:
        size = int(request.args.get('size') or 320)
        size = max(96, min(size - size % 8, 2040))
        if fmt == 'json':
            payload = encode_payload(main, aux, payload_size=None, aux_size=32)
            return jsonify({"payload_b64": base64.b64encode(payload).decode(), "mime": MIME_TYPE.decode(),
                            "ndef_b64": base64.b64encode(ndef_record(payload)).decode(),
                            "instance_uuid": row['opt_instance_uuid'], "spool_id": spool_id}), 200
        if fmt == 'ndef':
            data = ndef_record(encode_payload(main, aux, payload_size=None, aux_size=32))
        else:
            data = build_tag_file(main, aux, tag_size=size)
    except OptError as e:
        return jsonify({"error": str(e)}), 400
    import io
    name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in (row.get('name') or 'bobine'))[:40]
    return send_file(io.BytesIO(data), mimetype='application/octet-stream', as_attachment=True,
                     download_name=f"openprinttag_{name}.bin")


def api_opt_aux():
    """Corps : {payload_b64 (charge utile lue sur le tag), spool_id}. Retourne la charge utile avec le poids consommé à jour
    (zone auxiliaire seule modifiée) — l'application Android la réécrit sur le tag."""
    ensure_columns()
    body = request.get_json(silent=True) or {}
    try:
        payload = extract_payload(base64.b64decode(body.get('payload_b64') or ''))
        uid = session['user_id']
        conn = get_db()
        try:
            row = _row(conn, int(body.get('spool_id') or 0), uid)
        finally:
            conn.close()
        if not row:
            return jsonify({"error": "Bobine introuvable"}), 404
        cap = float(row.get('capacity_g') or 1000)
        rem = float(row.get('remaining_g') if row.get('remaining_g') is not None else cap)
        new = update_aux(payload, consumed_weight=max(0.0, round(cap - rem, 1)))
        return jsonify({"payload_b64": base64.b64encode(new).decode(),
                        "ndef_b64": base64.b64encode(ndef_record(new)).decode()}), 200
    except OptError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app_logger.error(f"[OPT] aux : {e}")
        return jsonify({"error": "Mise à jour impossible"}), 400


_ROUTES = (
    ('/api/openprinttag/decode', ['POST'], 'api_opt_decode', ('login_required', )),
    ('/api/openprinttag/import', ['POST'], 'api_opt_import', ('login_required', )),
    ('/api/openprinttag/export/<int:spool_id>', ['GET'], 'api_opt_export', ('login_required', )),
    ('/api/openprinttag/aux', ['POST'], 'api_opt_aux', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"openprinttag.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if g.get('send_file') is None:
        from flask import send_file as _sf
        g['send_file'] = _sf
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {}
