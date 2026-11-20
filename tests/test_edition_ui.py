"""1.1.7 — Windows : Webhooks, API publique et Accès mobile masqués (édition serveur seulement) ; un seul « Mode atelier » ; langue en tête d'Apparence."""
import os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
html = open(os.path.join(ROOT, 'interface', 'index.html'), encoding='utf-8').read()
js = open(os.path.join(ROOT, 'interface', 'script.js'), encoding='utf-8').read()


def test_sections_reservees_au_serveur():
    for i in ('api-settings-section', 'webhooks-settings-section', 'mobile-access-section'):
        assert re.search(rf'id="{i}" style="display:none;"', html), i            # masquées par défaut (pas de flash sous Windows)
        assert f"'{i}': 'block'" in js, i                                         # affichées par applyServerEditionUI en édition serveur


def test_un_seul_mode_atelier_dans_le_volet():
    assert re.search(r'id="nav-workshop-btn" style="display:none"', html)          # le bouton du volet est masqué, le rail le déclenche
    assert 'data-rail-click="#nav-workshop-btn"' in html and html.count('class="rail-btn" data-rail-click="#nav-workshop-btn"') == 1


def test_langue_en_tete_d_apparence():
    # la langue a sa propre section, juste après Apparence (et avant Accessibilité)
    a, l, c = (html.index(k) for k in ('data-i18n="settings.appearance"', 'fa-language"></i> <span data-i18n="settings.language"', 'data-i18n="settings.accessibility"'))
    assert a < l < c and html.count('id="language-selector"') == 1
