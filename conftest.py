"""
Stubs pour les dépendances lourdes/natives (trimesh, pyrender, smbclient,
rarfile, pymeshfix) non disponibles dans cet environnement de test isolé.

Objectif : permettre d'importer le vrai main.py (et donc de tester le vrai
code, pas une réimplémentation) même quand ces bibliothèques ne sont pas
installées. Dans l'environnement de dev/CI réel de Stellio, où elles SONT
installées, ces stubs ne sont jamais utilisés (le "sys.modules.setdefault"
ne prend effet que si le vrai module est absent).
"""
import sys
import types
import tempfile
import os


def _install_stub(name, **attrs):
    if name in sys.modules:
        return
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[name] = mod


def _try_real_or_stub(name, stub_attrs_factory):
    try:
        __import__(name)
    except ImportError:
        _install_stub(name, **stub_attrs_factory())


_try_real_or_stub('trimesh', lambda: {
    'load': lambda *a, **k: None,
    'Trimesh': type('Trimesh', (), {}),
    'transformations': types.ModuleType('trimesh.transformations'),
})
if 'trimesh' in sys.modules:
    sys.modules.setdefault('trimesh.transformations', sys.modules['trimesh'].transformations
                            if hasattr(sys.modules['trimesh'], 'transformations')
                            else types.ModuleType('trimesh.transformations'))

_try_real_or_stub('pyrender', lambda: {
    'Scene': type('Scene', (), {}),
    'Mesh': type('Mesh', (), {'from_trimesh': staticmethod(lambda *a, **k: None)}),
    'OffscreenRenderer': type('OffscreenRenderer', (), {}),
    'PerspectiveCamera': type('PerspectiveCamera', (), {}),
    'DirectionalLight': type('DirectionalLight', (), {}),
})

_try_real_or_stub('pymeshfix', lambda: {})

_try_real_or_stub('smbclient', lambda: {
    'register_session': lambda *a, **k: None,
    'listdir': lambda *a, **k: [],
    'stat': lambda *a, **k: None,
    'open_file': lambda *a, **k: None,
    'path': types.ModuleType('smbclient.path'),
})
sys.modules.setdefault('smbclient.path', types.ModuleType('smbclient.path'))

_try_real_or_stub('rarfile', lambda: {
    'RarFile': type('RarFile', (), {}),
    'UNRAR_TOOL': None,
    'Error': Exception,
})

# --- Environnement de test isolé pour Stellio (DATA_DIR temporaire) ---
# main.py lit STELLIO_DATA_DIR au chargement (voir get_data_path()) : on
# l'utilise pour ne jamais toucher aux vraies données de l'utilisateur
# pendant les tests, ni dépendre de %APPDATA% (absent hors Windows).
_TEST_DATA_DIR = tempfile.mkdtemp(prefix='stellio_test_data_')
os.environ['STELLIO_DATA_DIR'] = _TEST_DATA_DIR
os.environ.setdefault('STELLIO_PORT', '0')
