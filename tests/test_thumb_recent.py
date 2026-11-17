"""v1.1.4 — widget « Dernières miniatures » : sélection des 10 dernières miniatures générées (pur)."""
import hashlib, importlib.util, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _mod():
    spec = importlib.util.spec_from_file_location('thumb_recent_t', os.path.join(ROOT, 'modules', 'thumb_recent.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _k(p):
    return hashlib.md5(p.replace('\\', '/').encode()).hexdigest()


def F(p, **kw):
    d = {'path': p, 'name': os.path.basename(p), 'has_thumb': True, 'size': 10}
    d.update(kw)
    return d


def test_dix_plus_recentes_dans_l_ordre():
    m = _mod()
    files = [F(f'/lib/p{i}.stl') for i in range(15)]
    thumbs = [(_k(f'/lib/p{i}.stl') + '.webp', 1000 + i) for i in range(15)]
    r = m.recent_items(thumbs, files, 10)
    assert [x['name'] for x in r] == [f'p{i}.stl' for i in range(14, 4, -1)]
    assert r[0]['generated_at'] == 1014


def test_ignore_remplacement_masques_orphelins_et_autres_fichiers():
    m = _mod()
    files = [F('/lib/ok.stl'), F('/lib/fb.stl', thumb_fallback=True), F('/lib/.stellio_plateaux/x.stl'), F('/lib/nothumb.stl', has_thumb=False)]
    thumbs = [(_k('/lib/ok.stl') + '.webp', 5), (_k('/lib/fb.stl') + '.webp', 9), (_k('/lib/.stellio_plateaux/x.stl') + '.webp', 8),
              (_k('/lib/nothumb.stl') + '.webp', 7), ('orphelin.webp', 99), (_k('/lib/ok.stl') + '.txt', 50)]
    r = m.recent_items(thumbs, files, 10, hidden=lambda p: '.stellio_plateaux' in p)
    assert [x['name'] for x in r] == ['ok.stl']


def test_une_seule_ligne_par_fichier_et_chemins_windows():
    m = _mod()
    files = [F('C:\\lib\\a.stl')]
    thumbs = [(_k('C:/lib/a.stl') + '.webp', 5), (_k('C:/lib/a.stl') + '.png', 9)]
    r = m.recent_items(thumbs, files)
    assert len(r) == 1 and r[0]['generated_at'] == 9
    assert m.recent_items([], files) == [] and m.recent_items(thumbs, None) == []
