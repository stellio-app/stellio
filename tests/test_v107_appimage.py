"""v1.0.7 — AppImage : base plus ancienne (glibc) et informations de mise à jour (.zsync)."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WF = open(os.path.join(ROOT, '.github', 'workflows', 'build-and-sign.yml'), encoding='utf-8').read()


def _job():
    a = WF.index('  build-linux:')
    return WF[a:WF.index('# 2 bis', a)]


def test_linux_build_runs_on_older_ubuntu():
    j = _job()
    assert 'runs-on: ubuntu-22.04' in j and 'ubuntu-latest' not in j


def test_appimage_embeds_update_info_and_publishes_zsync():
    j = _job()
    assert 'appimagetool --appimage-extract-and-run' in j and '-u "gh-releases-zsync|stellio-app|stellio|latest|Stellio-v*-x86_64.AppImage.zsync"' in j
    assert 'zsync' in j and 'AppImage.zsync' in j.split('upload-artifact')[1]
    assert 'release-files/*.zsync' in WF


def test_appimage_name_has_no_linux_word():
    assert '-linux-x86_64.AppImage' not in WF and 'Stellio-v${{ needs.check-version.outputs.version }}-x86_64.AppImage' in WF
