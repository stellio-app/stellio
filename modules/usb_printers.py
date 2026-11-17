"""Stellio — imprimantes branchées en USB au PC qui fait tourner Stellio (BÊTA, v1.1.4)

Détecte les ports série (USB) du PC et propose ceux qui ressemblent à une imprimante 3D dans « Détecter mes imprimantes ».
Une imprimante ajoutée ainsi a le type `usb_serial` ; son « adresse » est le nom du port (COM3, /dev/ttyACM0, /dev/cu.usbmodem…).

Règles de sécurité :
  • le port n'est JAMAIS ouvert par ce module : ouvrir une liaison série fait redémarrer beaucoup de cartes (Arduino/Marlin)
    et interromprait une impression en cours. On lit seulement la liste des ports du système ;
  • aucune commande, aucun lancement ni arrêt d'impression : suivi de présence uniquement (branchée / absente) ;
  • l'état de l'impression n'est donc pas connu (statut « inconnu » tant que l'imprimante est branchée).
Détection : `serial.tools.list_ports` (pyserial) s'il est installé, sinon repli sans dépendance (/dev/ttyUSB*, /dev/ttyACM*,
/dev/cu.usb* ; sous Windows le repli passe par le registre `HARDWARE\\DEVICEMAP\\SERIALCOMM`).
Les fonctions `classify` et `detect` sont pures (la liste des ports est injectée) : testées sans matériel.
Module séparé de main.py (même schéma que resin_printers.py) ; main.py appelle `usb_printers.init(globals())`.
"""
import glob
import os
import sys

_REQUIRED = ('app_logger',)
_OPTIONAL = ()
_OVERRIDABLE = ('os',)

_MAIN = {}
app_logger = None

USB_TYPE = 'usb_serial'

# (VID, PID) -> libellé. PID None = tout le fabricant. Ponts USB-série et cartes courantes des imprimantes 3D.
KNOWN = {
    (0x2C99, None): 'Prusa',
    (0x1A86, 0x7523): 'Creality / carte CH340',
    (0x1A86, 0x55D4): 'Carte CH9102',
    (0x1A86, None): 'Carte CH340',
    (0x10C4, 0xEA60): 'Carte CP210x',
    (0x0403, 0x6001): 'Carte FTDI',
    (0x0403, 0x6015): 'Carte FTDI',
    (0x2341, None): 'Arduino (Marlin)',
    (0x2A03, None): 'Arduino (Marlin)',
    (0x0483, 0x5740): 'Carte STM32 (Creality, BigTreeTech…)',
    (0x1D50, 0x614E): 'Carte Klipper (USB)',
    (0x1D50, 0x6015): 'Carte Klipper (USB)',
    (0x1D50, None): 'Carte 3D (OpenMoko ID)',
    (0x2E8A, None): 'Carte RP2040 (Klipper)',
    (0x239A, None): 'Carte Adafruit',
    (0x16C0, None): 'Carte Teensy',
}
# Ports qui ne sont jamais une imprimante : liaisons Bluetooth, modems, consoles
_IGNORE_WORDS = ('bluetooth', 'modem', 'irda', 'debug-console', 'wlan')
_IGNORE_PREFIX = ('/dev/ttys', '/dev/tty.bluetooth', '/dev/cu.bluetooth', '/dev/cu.debug', '/dev/cu.wlan')


def _known_label(vid, pid):
    if vid is None:
        return ''
    return KNOWN.get((vid, pid)) or KNOWN.get((vid, None)) or ''


def classify(port):
    """port : dict {device, description, vid, pid, serial, manufacturer} -> dict de découverte, ou None si ce n'est pas une imprimante probable."""
    dev = str(port.get('device') or '').strip()
    if not dev:
        return None
    low = dev.lower()
    text = ' '.join(str(port.get(k) or '') for k in ('description', 'manufacturer', 'product')).lower()
    if any(low.startswith(p) for p in _IGNORE_PREFIX) or any(w in text for w in _IGNORE_WORDS):
        return None
    vid, pid = port.get('vid'), port.get('pid')
    label = _known_label(vid, pid)
    if not label and vid is None:
        return None        # port sans identifiant USB (série interne, ttyS0…) : pas un appareil branché en USB
    model = label or (str(port.get('manufacturer') or '').strip() or str(port.get('description') or '').strip())
    shown = (str(port.get('description') or '').strip() or label or 'Carte série')
    return {'type': USB_TYPE, 'ip': dev, 'name': f"USB — {label or shown} ({dev})", 'model': model,
            'serial': str(port.get('serial') or ''), 'source': 'usb', 'likely': bool(label)}


def detect(ports):
    """Liste de découvertes (probables d'abord), sans doublon de port."""
    seen, out = set(), []
    for p in ports or []:
        r = classify(p)
        if r and r['ip'] not in seen:
            seen.add(r['ip'])
            out.append(r)
    out.sort(key=lambda r: (not r['likely'], r['ip']))
    return out


def _fallback_ports():
    ports = []
    if sys.platform.startswith('win'):
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'HARDWARE\DEVICEMAP\SERIALCOMM') as k:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(k, i)
                    except OSError:
                        break
                    i += 1
                    if 'usb' in str(name).lower() or 'vcp' in str(name).lower() or 'acm' in str(name).lower():
                        ports.append({'device': str(value), 'description': f'USB ({value})', 'vid': 0, 'pid': 0})
        except Exception:
            pass
        return ports
    pats = ['/dev/ttyUSB*', '/dev/ttyACM*'] if not sys.platform.startswith('darwin') else ['/dev/cu.usbmodem*', '/dev/cu.usbserial*']
    for pat in pats:
        for dev in sorted(glob.glob(pat)):
            ports.append({'device': dev, 'description': os.path.basename(dev), 'vid': 0, 'pid': 0})
    return ports


def list_system_ports():
    """Ports série du système, au format de `classify` (n'ouvre aucun port)."""
    try:
        from serial.tools import list_ports
        return [{'device': p.device, 'description': p.description if p.description != 'n/a' else '', 'vid': p.vid, 'pid': p.pid,
                 'serial': p.serial_number or '', 'manufacturer': p.manufacturer or '', 'product': p.product or ''}
                for p in list_ports.comports()]
    except ImportError:
        return _fallback_ports()
    except Exception as e:
        try:
            app_logger.info(f"[USB] Liste des ports impossible : {e}")
        except Exception:
            pass
        return _fallback_ports()


def discover():
    """Imprimantes USB probables branchées au PC (appelé par /api/printers/discover)."""
    return detect(list_system_ports())


def is_present(device):
    """Le port est-il toujours branché ? (sans l'ouvrir)"""
    device = str(device or '').strip()
    if not device:
        return False
    if os.name != 'nt' and device.startswith('/dev/'):
        return os.path.exists(device)
    return any(p['device'].lower() == device.lower() for p in list_system_ports())


def connect(device):
    return is_present(device)


def status(device):
    """Suivi de présence : pas de lecture sur la liaison série (voir l'en-tête). Lève RuntimeError('unreachable') si débranchée."""
    if not is_present(device):
        raise RuntimeError('unreachable')
    return {'status': 'unknown', 'progress': 0, 'file': '',
            'temps': {'extruder': {'current': 0, 'target': 0}, 'bed': {'current': 0, 'target': 0}, 'chamber': {'current': 0, 'target': 0}},
            'time': {'elapsed': 0, 'remaining': 0, 'total': 0}, 'layers': {'current': 0, 'total': 0}, 'ams': [],
            'last_print': {'filename': '', 'duration': 0, 'finished_at': ''}}


_ROUTES = ()


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) ; ce module n'ajoute aucune route."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"usb_printers.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    return {}
