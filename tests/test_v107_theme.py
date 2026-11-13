"""v1.0.7 — thème : suit le système, clair par défaut (sombre seulement si le système le demande)."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = open(os.path.join(ROOT, 'interface', 'script.js'), encoding='utf-8').read()
HTML = open(os.path.join(ROOT, 'interface', 'index.html'), encoding='utf-8').read()


def test_theme_is_light_unless_system_asks_dark():
    assert JS.count("const isLight = !(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);") == 2
    assert "(prefers-color-scheme: dark)').matches)?'dark':'light'" in HTML.split('</script>')[0]
    assert "prefers-color-scheme: light" not in JS
    assert "matchMedia('(prefers-color-scheme: dark)').addEventListener('change'" in JS
