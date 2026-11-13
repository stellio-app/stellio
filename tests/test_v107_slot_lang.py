"""v1.0.7 — les titres des zones montées (pesée de filament…) suivent la langue appliquée après le chargement."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = open(os.path.join(ROOT, 'interface', 'management.js'), encoding='utf-8').read()


def test_slot_titles_refresh_on_lang_change():
    assert 'function refreshSlotTitles()' in JS
    assert "attributeFilter: ['lang']" in JS
    assert JS.count('refreshSlotTitles') >= 3
    assert "localStorage.getItem('stellio-lang')" in JS and "stellio_lang" not in JS
