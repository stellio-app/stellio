"""Test v1.0.5 : Stellio n'écrit jamais la consommation dans Spoolman (Spoolman débite lui-même via Moonraker / OctoPrint)."""
import os


def test_stellio_never_writes_consumption_to_spoolman():
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'main.py'), encoding='utf-8').read()
    assert '/use"' not in src and "/use'" not in src and '_consume_spool_filament' not in src
    start = src.index('def _consume_filament_slot(')
    block = src[start:src.index("elif source_type == 'manual':", start)]
    assert 'requests.' not in block and 'return False' in block
