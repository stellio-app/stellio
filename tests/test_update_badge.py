"""Surveillance des mises à jour (à partir de la 1.1.6) : interrogation chaque minute, cache GitHub de 3 min, badge persistant."""
import json, os, re, threading, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(*p):
    return open(os.path.join(ROOT, *p), encoding='utf-8').read()


def test_interface_interroge_chaque_minute_et_affiche_un_badge():
    js = _read('interface', 'script.js')
    assert 'checkInterval: 60 * 1000' in js
    assert 'renderBadge(data)' in js and "id = 'update-badge'" in js and "this.showUpdateModal(info)" in js
    assert "visibilitychange" in js
    body = js[js.index('async checkForUpdates(showModal = true)'):js.index('renderBadge(data) {')]
    assert 'this.renderBadge(null)' in body and '_toastedVersion' in body       # déconnecté ou à jour : badge retiré ; une seule bulle par version
    assert '.update-badge' in _read('interface', 'style.css')


def test_textes_du_badge_dans_les_huit_langues():
    for lg in ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja'):
        d = json.loads(_read('languages', lg + '.json'))
        assert d.get('update.badge') and '{{version}}' in d.get('update.badge_title', ''), lg


def test_cache_github_de_trois_minutes_mais_verification_manuelle_toujours_directe():
    src = _read('main.py')
    a = src.index('_UPDATE_POLL_TTL_S = 180')
    b = src.index("@app.route('/api/update/check'")
    calls = []
    ns = {'time': time, 'threading': threading, 'check_for_updates': lambda force=False: calls.append(force) or {'version': '9.9.9'}}
    exec(src[a:b], ns)
    f = ns['_check_for_updates_cached']
    assert f() == {'version': '9.9.9'} and f() == {'version': '9.9.9'} and f() == {'version': '9.9.9'}
    assert calls == [False]                                  # trois appels, un seul contact avec GitHub
    f(force=True)
    assert calls == [False, True]                            # « Vérifier les mises à jour » : jamais mis en cache
    ns['_update_poll_cache']['ts'] -= 181
    f()
    assert len(calls) == 3                                   # le cache expire au bout de 3 minutes
    assert "_check_for_updates_cached(force=request.args.get('force') == '1')" in src
