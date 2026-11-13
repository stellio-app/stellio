"""v1.0.7 — bouton « Ouvrir dans le slicer » dans Mes G-codes."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = open(os.path.join(ROOT, 'main.py'), encoding='utf-8').read()
JS = open(os.path.join(ROOT, 'interface', 'script.js'), encoding='utf-8').read()


def test_backend_route_opens_stored_gcode_in_default_slicer():
    a = MAIN.index('def api_project_gcode_open_in_slicer')
    b = MAIN.index("@app.route('/api/projects/<int:project_id>/files', methods=['DELETE'])")
    s = MAIN[a:b]
    assert "find_slicer_by_name(slicer_name)" in s and "subprocess.Popen([slicer_path, path])" in s
    assert "IS_SERVER_EDITION" in s and "_slicer_fetch_links[ftoken]" in s and "_gcode_row(gid)" in s


def test_buttons_in_list_and_details_and_i18n():
    assert JS.count('openProjectGcodeInSlicer(${g.id}, event)') == 2 and 'window.openProjectGcodeInSlicer' in JS
    import json
    for l in ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja'):
        d = json.load(open(os.path.join(ROOT, 'languages', f'{l}.json'), encoding='utf-8'))
        assert d.get('projects.gcode_open_slicer')
