"""Widget Santé : un clic sur « alerte(s) à vérifier » ouvre un popup listant les alertes (PC et téléphone)."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_widget_sante_alertes_cliquables_et_popup():
    js = open(os.path.join(ROOT, 'interface', 'script.js'), encoding='utf-8').read()
    assert 'openHealthAlertsPopup()' in js and 'window.openHealthAlertsPopup' in js and 'window._healthWarnings = warns' in js
    assert 'dashboard-health-alert-btn' in js and 'modal-health-alerts' in js
    assert 'escapeHtml(String(w))' in js                                       # alertes échappées dans le popup
    css = open(os.path.join(ROOT, 'interface', 'style.css'), encoding='utf-8').read()
    assert '.health-alerts-list' in css and 'dashboard-health-alert-btn' in css
    for lg in ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja'):
        d = json.load(open(os.path.join(ROOT, 'languages', lg + '.json'), encoding='utf-8'))
        assert d['dashboard.health_popup_open']
