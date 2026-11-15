"""Test de fumée de bout en bout (v1.1.1) : démarre le vrai serveur et ouvre l'interface dans Chromium.
Lent (~40 s) : lancé seulement avec STELLIO_E2E=1 (ex. avant une release : `STELLIO_E2E=1 pytest tests/test_e2e_smoke.py`)."""
import os, socket, subprocess, sys, tempfile, time
import pytest

pytestmark = pytest.mark.skipif(os.environ.get('STELLIO_E2E') != '1', reason='test de bout en bout : STELLIO_E2E=1')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0)); return s.getsockname()[1]


@pytest.fixture(scope='module')
def server():
    port = _free_port()
    env = dict(os.environ, STELLIO_DATA_DIR=tempfile.mkdtemp(), STELLIO_PORT=str(port), STELLIO_NO_AUTO_INSTALL='1', STELLIO_SERVER_EDITION='1')
    p = subprocess.Popen([sys.executable, 'main.py'], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import urllib.request
    for _ in range(90):
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{port}/api/ping', timeout=1); break
        except Exception:
            time.sleep(1)
    else:
        p.kill(); pytest.fail('le serveur ne démarre pas')
    yield f'http://127.0.0.1:{port}'
    p.kill()


def test_app_loads_logs_in_and_opens_pages(server):
    sync_api = pytest.importorskip('playwright.sync_api')
    with sync_api.sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.add_init_script("try{localStorage.setItem('stellio_tour_done_v2','1')}catch(e){}")
        page.goto(server)
        page.wait_for_selector('#register-form, #login-username', timeout=20000)
        # création du premier compte par l'API (même chemin que le formulaire), puis rechargement connecté
        page.evaluate("""() => fetch('/api/auth/register', {method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({username:'e2e', password:'e2e-pass', security_question_key:'custom', security_question_custom:'q', security_answer:'a'})})""")
        page.reload()
        page.wait_for_selector('#page-dashboard.active', state='attached', timeout=30000)
        page.wait_for_timeout(2000)
        for name in ('library', 'printed'):      # clic sur le bouton de navigation (le volet peut être replié : clic via JS)
            page.evaluate("n => document.querySelector(`.nav-btn[data-page=\"${n}\"]`).click()", name)
            page.wait_for_selector(f'#page-{name}.active', state='attached', timeout=10000)
        assert not errors, errors
        browser.close()
