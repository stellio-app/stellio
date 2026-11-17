"""v1.1.4 — imprimantes USB : classification des ports (pure), statut par présence, jamais d'ouverture du port."""
import importlib.util, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _mod():
    spec = importlib.util.spec_from_file_location('usb_printers_t', os.path.join(ROOT, 'modules', 'usb_printers.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def P(dev, vid=None, pid=None, desc='', manu=''):
    return {'device': dev, 'description': desc, 'vid': vid, 'pid': pid, 'manufacturer': manu, 'serial': 'SN1'}


def test_cartes_connues_et_inconnues():
    m = _mod()
    ports = [P('/dev/ttyACM0', 0x2C99, 0x0002, 'Original Prusa MK4'), P('COM4', 0x1A86, 0x7523, 'USB-SERIAL CH340 (COM4)'),
             P('/dev/ttyUSB0', 0x9999, 0x0001, 'Gadget inconnu', 'Acme')]
    r = m.detect(ports)
    assert [x['ip'] for x in r] == ['/dev/ttyACM0', 'COM4', '/dev/ttyUSB0']        # probables d'abord
    assert r[0]['type'] == 'usb_serial' and r[0]['likely'] and 'Prusa' in r[0]['name'] and r[0]['source'] == 'usb'
    assert r[1]['likely'] and r[2]['likely'] is False and r[2]['model'] == 'Acme'


def test_ports_ignores():
    m = _mod()
    ports = [P('COM5', None, None, 'Standard Serial over Bluetooth link (COM5)'), P('/dev/ttyS0'), P('/dev/ttyS1', 0, 0),
             P('/dev/cu.Bluetooth-Incoming-Port'), P('COM1', None, None, 'Port de communication (COM1)'), P('', 0x2C99, 1), P('COM9', 0x2C99, 1, 'Prusa', 'Prusa Research')]
    assert [x['ip'] for x in m.detect(ports)] == ['COM9']


def test_doublons_fusionnes():
    m = _mod()
    assert len(m.detect([P('COM3', 0x1A86, 1), P('COM3', 0x1A86, 1)])) == 1
    assert m.detect(None) == [] and m.detect([]) == []


def test_status_presence_sans_ouvrir_le_port(tmp_path, monkeypatch):
    m = _mod()
    m.init({'app_logger': type('L', (), {'info': lambda *a, **k: None})()})
    opened = []
    monkeypatch.setattr('builtins.open', lambda *a, **k: opened.append(a) or (_ for _ in ()).throw(AssertionError('open')))
    monkeypatch.setattr(m, 'list_system_ports', lambda: [{'device': 'COM3', 'vid': 1, 'pid': 1}])
    assert m.connect('com3') is True and m.connect('COM8') is False
    st = m.status('COM3')
    assert st['status'] == 'unknown' and st['temps']['bed']['current'] == 0
    try:
        m.status('COM8')
        assert False
    except RuntimeError as e:
        assert str(e) == 'unreachable'
    assert opened == []


def test_present_pour_un_chemin_linux(tmp_path):
    m = _mod()
    if os.name == 'nt':
        return
    f = tmp_path / 'ttyACM9'
    f.write_text('')
    assert m.is_present(str(f)) is False         # n'est pas sous /dev/ : on interroge la liste des ports
    assert m.is_present('') is False
    assert m.is_present('/dev/null') is True
