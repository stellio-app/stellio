import json, os, re, subprocess, shutil
import pytest
from conftest import load_from_main, ROOT

LANGS = ['fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja']


def _lang(l):
    return json.load(open(os.path.join(ROOT, 'languages', f'{l}.json'), encoding='utf-8'))


def test_safe_int():
    f = load_from_main(['_safe_int'])['_safe_int']
    assert f('12') == 12 and f(None, 5) == 5 and f('', 1) == 1 and f('abc', 7) == 7 and f('null') is None


def test_journal_can_undo(tmp_path):
    ns = load_from_main(['JOURNAL_UNDOABLE', '_journal_entry_can_undo'])
    f = ns['_journal_entry_can_undo']
    dst = tmp_path / 'b.stl'; dst.write_text('x'); src = tmp_path / 'a.stl'
    row = {'undone': 0, 'action': 'rename', 'from_path': str(src), 'to_path': str(dst)}
    assert f(row) is True
    src.write_text('y')                      # ancien emplacement occupé
    assert f(row) is False
    assert f({**row, 'undone': 1}) is False
    assert f({**row, 'action': 'convert'}) is False
    assert f({**row, 'to_path': str(tmp_path / 'absent')}) is False


def test_raster_basic_and_cancel():
    np = pytest.importorskip('numpy')
    ns = load_from_main(['RASTER_BATCH_PIXELS', '_raster_zbuffer'])
    w = h = 64
    # deux triangles se recouvrant : le plus proche (z plus petit) doit gagner
    tx = np.array([[5, 55, 5], [5, 55, 5]], float); ty = np.array([[5, 5, 55], [5, 5, 55]], float)
    tz = np.array([[2, 2, 2], [1, 1, 1]], float)
    zb = np.full((h, w), np.inf, np.float32); fid = np.full((h, w), -1, np.int32)
    assert ns['_raster_zbuffer'](tx, ty, tz, w, h, zb, fid) is not False
    assert fid[20, 20] == 1 and fid[0, 0] == -1 and zb[20, 20] == pytest.approx(1)
    ns['RASTER_BATCH_PIXELS'] = 10
    zb2 = np.full((h, w), np.inf, np.float32); fid2 = np.full((h, w), -1, np.int32)
    assert ns['_raster_zbuffer'](tx, ty, tz, w, h, zb2, fid2, lambda: True) is False


@pytest.mark.parametrize('l', LANGS)
def test_language_files(l):
    d, fr = _lang(l), _lang('fr')
    assert set(d) == set(fr), f'{l}: clés différentes de fr'
    for k, v in d.items():
        if k.startswith('__') or not isinstance(v, str):
            continue
        assert sorted(re.findall(r'\{\{\w+\}\}', v)) == sorted(re.findall(r'\{\{\w+\}\}', str(fr[k]))), f'{l}:{k} placeholders'


def test_changelog_consistent(main_src):
    a = json.load(open(os.path.join(ROOT, 'changelog.json'), encoding='utf-8'))
    b = json.load(open(os.path.join(ROOT, 'languages', 'changelog.json'), encoding='utf-8'))
    assert a == b, 'changelog.json racine et languages/ doivent être identiques'
    ver = re.search(r'^CURRENT_VERSION\s*=\s*"([^"]+)"', main_src, re.M).group(1)
    assert a[0]['version'] == ver, 'la 1re entrée du changelog doit être la version courante'
    assert os.path.exists(os.path.join(ROOT, f'notes_version_{ver}.txt'))
    for l in LANGS:
        assert a[0]['items'].get(l), f'changelog {ver} sans texte {l}'


def test_i18n_keys_used_in_html_exist():
    html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    fr = _lang('fr')
    missing = sorted({k for k in re.findall(r'data-i18n(?:-[a-z]+)?="([\w.]+)"', html) if k not in fr})
    assert not missing, f'clés data-i18n absentes de fr.json : {missing[:15]}'


def test_main_py_parses(main_src):
    import ast; ast.parse(main_src)


@pytest.mark.skipif(not shutil.which('node'), reason='node absent')
def test_script_js_syntax():
    r = subprocess.run(['node', '--check', os.path.join(ROOT, 'script.js')], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
