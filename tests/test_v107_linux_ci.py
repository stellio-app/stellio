"""v1.0.7 — le job build-linux (Ubuntu 22.04) n'installe que des paquets qui existent sur jammy."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WF = open(os.path.join(ROOT, '.github', 'workflows', 'build-and-sign.yml'), encoding='utf-8').read()


def test_linux_deps_compatibles_jammy():
    assert 'runs-on: ubuntu-22.04' in WF
    assert 'libgirepository-2.0-dev' not in WF      # n'existe qu'à partir d'Ubuntu 24.04
    assert 'libgirepository1.0-dev' in WF
    assert '"PyGObject<3.51"' in WF                 # 3.52+ exige girepository-2.0
