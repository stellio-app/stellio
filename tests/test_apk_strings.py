"""Android : aucune ressource de texte ne doit être déclarée deux fois dans un même strings.xml (sinon mergeReleaseResources échoue)."""
import collections, glob, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_pas_de_doublon_de_chaines():
    files = glob.glob(os.path.join(ROOT, 'apk-src', 'app', 'src', 'main', 'res', 'values*', 'strings.xml'))
    assert len(files) >= 8
    for f in files:
        names = re.findall(r'<string name="([^"]+)"', open(f, encoding='utf-8').read())
        assert [k for k, v in collections.Counter(names).items() if v > 1] == [], f
