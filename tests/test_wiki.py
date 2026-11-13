"""v1.0.7 — le wiki GitHub (8 langues, captures, changelog) se génère sans lien cassé."""
import importlib.util
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location('build_wiki', os.path.join(ROOT, 'tools', 'build_wiki.py'))
bw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bw)


def test_structure_8_langues():
    assert bw.check() == []


def test_build_sans_lien_casse(tmp_path):
    broken, n_pages, n_imgs = bw.build(str(tmp_path / 'w'))
    assert broken == []
    assert n_pages == 8 * (len(bw.PAGES) + 1) + 2  # 14 pages + Changelog par langue, Home, _Sidebar
    assert n_imgs > 0
    out = tmp_path / 'w'
    for lang, _, _ in bw.LANGS:
        assert (out / f'{lang}-Home.md').exists() and (out / f'{lang}-Changelog.md').exists()
    txt = (out / 'fr-Home.md').read_text(encoding='utf-8')
    assert '{{img:' not in txt and 'raw.githubusercontent.com/wiki/' in txt


def test_captures_referencees_existent(tmp_path):
    bw.build(str(tmp_path / 'w'))
    out = tmp_path / 'w'
    for f in out.glob('*.md'):
        for m in re.findall(r'raw\.githubusercontent\.com/wiki/[^/]+/[^/]+/(images/[^)\s]+\.png)', f.read_text(encoding='utf-8')):
            assert (out / m).exists(), (f.name, m)


def test_capture_la_plus_recente(tmp_path, monkeypatch):
    img = tmp_path / 'images'
    for v in ('v1.0.7', 'v1.0.10', 'v1.0.9'):
        (img / v / 'fr').mkdir(parents=True)
    (img / 'v1.0.7' / 'fr' / 'library.png').write_bytes(b'x')
    (img / 'v1.0.10' / 'fr' / 'library.png').write_bytes(b'x')
    (img / 'v1.0.9' / 'en').mkdir()
    (img / 'v1.0.9' / 'en' / 'viewer.png').write_bytes(b'x')
    monkeypatch.setattr(bw, 'IMG', str(img))
    assert bw.find_image('fr', 'library') == ('v1.0.10', 'fr')      # tri numérique, pas alphabétique
    assert bw.find_image('de', 'viewer') == ('v1.0.9', 'en')        # repli sur l'anglais
    assert bw.find_image('fr', 'inconnue') is None
