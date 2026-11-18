"""App téléphone : « Réessayer » donne un retour visuel (cercle, bouton grisé, message, heure du dernier échec)."""
import os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, 'apk-src', 'app', 'src', 'main')


def test_retour_visuel_pendant_la_tentative():
    j = open(os.path.join(RES, 'java/com/stellioapp/companion/MainActivity.java'), encoding='utf-8').read()
    assert 'setTrying(true, false)' in j and 'setTrying(false, true)' in j and 'ProgressBar offlineSpin' in j
    assert 'MIN_TRY_MS' in j and 'retryBtn.setEnabled(!trying)' in j
    assert 'import android.widget.ProgressBar;' in j and 'import android.content.res.ColorStateList;' in j
    assert j.count('{') == j.count('}')


def test_textes_dans_les_8_langues():
    for d in ('values', 'values-fr', 'values-de', 'values-es', 'values-pt', 'values-it', 'values-zh', 'values-ja'):
        x = open(os.path.join(RES, 'res', d, 'strings.xml'), encoding='utf-8').read()
        for k in ('connecting', 'connecting_short', 'still_unreachable'):
            assert f'name="{k}"' in x, (d, k)
        assert '%1$s' in re.search(r'name="still_unreachable">([^<]*)', x).group(1)
