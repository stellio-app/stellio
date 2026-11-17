"""BigPrint : calcul réel puis lecture en français — plus aucun texte anglais du moteur dans le résumé, le journal et l'aperçu."""
import os, sys
import pytest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tests'))
pytest.importorskip('trimesh'); pytest.importorskip('flask'); pytest.importorskip('manifold3d')
from test_bigprint_tool import _client, _sphere, _wait, _settings  # noqa: E402


def test_calcul_reel_en_francais(tmp_path):
    c, _ = _client(tmp_path)
    cfg = c.get('/api/bigprint/config?lang=fr').get_json()
    assert cfg['presets']['display']['label'] == "Pièce d'exposition" and 'parois' in cfg['presets']['display']['describe']
    assert c.get('/api/bigprint/config?lang=en').get_json()['presets']['display']['label'] == 'Display piece'
    info = c.post('/api/bigprint/model', json={'path': str(_sphere(tmp_path))}).get_json()
    assert c.post('/api/bigprint/preview', json={'settings': _settings(info['id'])}).status_code == 200
    _wait(c)
    d = c.get('/api/bigprint/job?lang=fr').get_json()
    assert d['job']['state'] == 'done'
    assert 'préréglage' in d['summary']['basis'].lower() and 'hollow' not in d['summary']['basis']
    assert any(l.startswith('Chargement') for l in d['job']['log']) and not any(l.startswith(('Loading', 'Scaled', 'Hollowing')) for l in d['job']['log'])
    assert d['summary']['preset']['label'] == "Pièce d'exposition" and all(r['fill'].startswith('creux') for r in d['summary']['table'])
    assert '..' not in d['summary']['basis']
    html = c.get('/api/bigprint/preview.html?lang=fr').data.decode()
    for en in ('>Explode<', 'Show IDs', 'Show all', 'Print size', 'Estimate based', 'Touches'):
        assert en not in html, en
    assert 'Éclaté' in html
    assert '>Explode<' in c.get('/api/bigprint/preview.html').data.decode()
    import json, re
    for lg in ('fr', 'ja', 'de'):
        h = c.get('/api/bigprint/preview.html?lang=' + lg).data.decode()
        raw = re.search(r'const DATA = (\{.*?\});\n', h, re.S).group(1)
        data = json.loads(raw)   # le JSON embarqué doit rester valide après traduction
        assert data['pieces'] and data['basis']
    c.post('/api/bigprint/close')
