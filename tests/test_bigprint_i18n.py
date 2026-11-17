"""Traduction des textes BigPrint (modules/bigprint_i18n.py) : gabarits pur, repli sur l'original, aperçu HTML, route avec ?lang=."""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from modules import bigprint_i18n as b

ALL = ('fr', 'de', 'es', 'pt', 'it', 'zh', 'ja')
BASIS = "Display piece preset: 3 walls, 8% gyroid infill, 6 top / 4 bottom layers. 2 hollow pieces: 4 mm shells (4 walls fill the shell). 1 thin piece prints solid."


def test_every_language_has_every_template():
    for key, d in b.T.items():
        assert set(d) >= set(ALL), key
    for key, d in b.PRESETS.items():
        assert set(d) >= set(ALL), key


def test_english_and_unknown_languages_keep_original():
    for lg in ('en', '', 'xx', None):
        assert b.basis(BASIS, lg) == BASIS
        assert b.log_line('Done', lg) == 'Done'
        assert b.preset('display', lg, 'Display piece', 'why') == ('Display piece', 'why')


def test_basis_and_describe_translated_everywhere():
    for lg in ALL:
        out = b.basis(BASIS, lg)
        assert out != BASIS and 'preset' not in out and 'hollow' not in out and 'walls' not in out, (lg, out)
    assert b.describe('3 walls, 8% gyroid infill, 6 top / 4 bottom layers', 'fr').startswith('3 parois')


def test_log_warning_fill_and_unknown_fallback():
    assert b.log_line('Done', 'fr') == 'Terminé'
    assert b.log_line('Something new', 'fr') == 'Something new'
    assert b.log_line('Cuts: (no cuts needed)', 'de') == 'Schnitte: (keine Schnitte nötig)'
    assert 'Dübel' in b.warning('A1: contact (12 mm^2) too small for a dowel - glue only', 'de')
    assert b.warning('weird', 'ja') == 'weird'
    assert b.fill('solid', 'fr') == 'plein'
    assert b.fill('sparse: 3 walls, 8%', 'fr').startswith('clairsemé')


def test_summary_is_copied_not_mutated():
    s = {'cuts': '(no cuts needed)', 'basis': BASIS, 'warnings': ['A1: no room on cut faces for a label'], 'table': [{'id': 'A1', 'fill': 'solid'}]}
    out = b.summary(s, 'es')
    assert s['cuts'] == '(no cuts needed)' and out['cuts'] != s['cuts'] and out['table'][0]['fill'] == 'macizo'


def test_preview_html_literals_translated():
    data = json.dumps({'basis': BASIS, 'pieces': [{'fill': '3 walls, 8% gyroid'}]})
    html = ('<html lang="en"><span class="muted">Explode</span><label><input type="checkbox" id="tags" checked> Show IDs</label>'
            '<button id="all">Show all</button><th>Print size (mm)</th>`Estimate based on: ${DATA.basis}` pieces · ~ \\nTouches: '
            'const DATA = ' + data + ';')
    out = b.preview_html(html, 'fr')
    for en in ('>Explode<', 'Show IDs', 'Show all', 'Print size', 'Estimate based', 'Touches', ' pieces'):
        assert en not in out, en
    assert 'Éclaté' in out and 'Afficher les numéros' in out and 'lang="fr"' in out
    assert b.preview_html(html, 'en') == html
