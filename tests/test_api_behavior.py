"""Tests de comportement (v1.1.1) : le vrai main.py est chargé et on interroge les routes avec le client de test Flask.
Ils verrouillent la sécurité (toute route protégée refuse sans connexion), l'authentification, les chemins hors
dossiers autorisés et l'absence d'erreur 500 sur les lectures de base."""
import re
import pytest

# Routes volontairement publiques (réponse autre que 401/403 sans connexion).
PUBLIC_ROUTES = {
    ('GET', '/api/auth/first-launch'), ('GET', '/api/network-info'), ('GET', '/api/peer/identify'),
    ('GET', '/api/ping'), ('GET', '/api/update/version'), ('POST', '/api/auth/logout'),
    ('POST', '/api/auth/register'), ('POST', '/api/auth/reset-with-recovery'),
    ('GET', '/api/auth/security-question'), ('GET', '/api/slicer-fetch/<token>/<path:fname>'),
    ('GET', '/api/v1/docs'), ('GET', '/api/v1/openapi.json'),     # v1.1.8 : documentation publique de l'API (les routes /api/v1/* elles-mêmes exigent un jeton)
}
NEEDS_NETWORK = {'/api/ollama/models'}          # 502 normal sans Ollama
# Routes qui arrêtent, mettent à jour ou redémarrent l'application : jamais appelées avec une session valide dans les tests.
DANGEROUS = {'/api/app/quit', '/api/update/install', '/api/update/download', '/api/restart'}

USER = {'username': 'testeur', 'password': 'abcd1234', 'security_question_key': 'custom',
        'security_question_custom': 'Question ?', 'security_answer': 'reponse'}


def _url(rule):
    return re.sub(r'<(?:int:|path:|string:)?[^>]+>', '1', rule)


def _api_routes(app):
    for r in app.url_map.iter_rules():
        if r.rule.startswith('/api/'):
            for m in sorted(r.methods - {'HEAD', 'OPTIONS'}):
                yield m, r.rule


def _csrf(c):
    """Jeton CSRF (double soumission : cookie `stellio_csrf` renvoyé dans l'en-tête X-CSRF-Token) pour les requêtes d'écriture."""
    c.get('/api/auth/me')
    ck = c.get_cookie('stellio_csrf')
    return {'X-CSRF-Token': ck.value if ck else ''}


@pytest.fixture(scope='module')
def logged(stellio_app):
    c = stellio_app.test_client()
    r = c.post('/api/auth/register', json=USER)
    assert r.status_code == 200, r.get_data()
    return c


def test_every_protected_route_refuses_anonymous(stellio_app):
    c = stellio_app.test_client()
    open_routes = set()
    for m, rule in _api_routes(stellio_app):
        code = c.open(_url(rule), method=m, json={} if m != 'GET' else None).status_code
        if code not in (401, 403):
            open_routes.add((m, rule))
    assert open_routes == PUBLIC_ROUTES, (
        f"routes ouvertes sans connexion non prévues : {sorted(open_routes - PUBLIC_ROUTES)} ; "
        f"routes publiques devenues protégées : {sorted(PUBLIC_ROUTES - open_routes)}")


def test_login_flow(stellio_app, logged):
    c = stellio_app.test_client()
    assert c.get('/api/auth/me').status_code in (401, 403)
    bad = c.post('/api/auth/login', json={'username': USER['username'], 'password': 'mauvais'})
    assert bad.status_code == 401
    ok = c.post('/api/auth/login', json={'username': USER['username'], 'password': USER['password']})
    assert ok.status_code == 200 and ok.get_json()['user']['username'] == USER['username']
    assert c.get('/api/auth/me').status_code == 200
    assert c.post('/api/auth/logout').status_code == 403        # sans jeton CSRF : refusé
    assert c.post('/api/auth/logout', headers=_csrf(c)).status_code == 200
    assert c.get('/api/auth/me').status_code in (401, 403)


def test_register_validation(stellio_app):
    c = stellio_app.test_client()
    assert c.post('/api/auth/register', json={**USER, 'username': 'x', 'password': 'ab'}).status_code == 400
    assert c.post('/api/auth/register', json={**USER, 'username': 'y', 'security_question_key': 'inconnue'}).status_code == 400
    assert c.post('/api/auth/register', json={**USER, 'username': 'z', 'security_answer': ''}).status_code == 400


def test_login_is_rate_limited(stellio_app):
    c = stellio_app.test_client()
    codes = [c.post('/api/auth/login', json={'username': 'bruteforce', 'password': f'x{i}'}).status_code for i in range(15)]
    assert codes[0] == 401 and 429 in codes, codes


def test_authenticated_reads_never_crash(stellio_app, logged):
    crashed = []
    for m, rule in _api_routes(stellio_app):
        if m != 'GET' or rule in NEEDS_NETWORK:
            continue
        code = logged.get(_url(rule)).status_code
        if code >= 500:
            crashed.append((code, rule))
    assert not crashed, crashed


def test_paths_outside_sources_never_leak_files(stellio_app, logged):
    """Aucune route ne doit renvoyer le contenu d'un fichier système quand on lui passe un chemin hors des sources."""
    leaks, crashes = [], []
    for m, rule in _api_routes(stellio_app):
        if rule in NEEDS_NETWORK or rule in DANGEROUS or rule.startswith('/api/auth/'):
            continue
        for val in ('/etc/passwd', '../../../../etc/passwd', '..\\..\\..\\windows\\win.ini'):
            qs = {k: val for k in ('path', 'file_path', 'file', 'name', 'filepath')}
            resp = logged.get(_url(rule), query_string=qs) if m == 'GET' else logged.open(_url(rule), method=m, json=qs, headers=_csrf(logged))
            body = resp.get_data()[:4000]
            if resp.status_code == 200 and (b'root:x:' in body or b'[fonts]' in body.lower()):
                leaks.append((m, rule, val))
            if resp.status_code == 500 and not rule.endswith('-native'):    # « -native » = boîte d'enregistrement du bureau, absente en test
                crashes.append((m, rule))      # 501 = fonction indisponible hors bureau : normal
    assert not leaks, leaks
    assert not crashes, sorted(set(crashes))


def test_writes_without_csrf_token_are_refused(stellio_app, logged):
    assert logged.post('/api/tags', json={'name': 'x'}).status_code == 403
    assert logged.delete('/api/print-history/by-file', json={'path': 'a'}).status_code == 403


def test_health_reports_jobs(stellio_app, logged):
    d = logged.get('/api/diagnostic/health').get_json()
    assert d['jobs'] == {'convert_running': 0, 'integrity_running': False, 'split_running': 0}


def test_printed_files_page_api(stellio_app, logged):
    r = logged.get('/api/printed-files')
    assert r.status_code == 200
    unknown = logged.delete('/api/print-history/by-file', json={'path': '/inconnu/fichier.stl'}, headers=_csrf(logged))
    assert unknown.status_code < 500


def test_security_headers_and_cookie_flags(stellio_app, logged):
    r = logged.get('/api/ping')
    h = r.headers
    assert h['X-Content-Type-Options'] == 'nosniff' and h['X-Frame-Options'] == 'SAMEORIGIN'
    assert "frame-ancestors 'self'" in h['Content-Security-Policy'] and "object-src 'none'" in h['Content-Security-Policy']
    assert 'Strict-Transport-Security' not in h                    # servi en HTTP : pas de HSTS
    https = logged.get('/api/ping', headers={'X-Forwarded-Proto': 'https'})
    assert 'Strict-Transport-Security' in https.headers            # derrière un proxy HTTPS : HSTS
    c = stellio_app.test_client()
    resp = c.post('/api/auth/login', json={'username': USER['username'], 'password': USER['password']})
    cookies = ' '.join(resp.headers.get_all('Set-Cookie'))
    assert 'HttpOnly' in cookies and 'SameSite=Lax' in cookies


def test_renaming_tag_to_existing_name_is_a_conflict_not_a_crash(stellio_app, logged):
    h = _csrf(logged)
    a = logged.post('/api/tags', json={'name': 'alpha-v111'}, headers=h).get_json()
    b = logged.post('/api/tags', json={'name': 'beta-v111'}, headers=h).get_json()
    r = logged.put(f"/api/tags/{b['id']}", json={'name': 'alpha-v111'}, headers=h)
    assert r.status_code == 409
    assert logged.put(f"/api/tags/{b['id']}", json={'name': 'gamma-v111'}, headers=h).status_code == 200


def test_already_printed_keeps_one_color_per_plate(stellio_app, logged):
    body = {'path': '/x/plateaux.3mf', 'result': 'success', 'plates': [
        {'plate': 1, 'spools': [{'source_type': 'manual', 'source_id': '1', 'name': 'PLA rouge', 'material': 'PLA', 'color_hex': 'ff0000'}]},
        {'plate': 2, 'spools': [{'source_type': 'manual', 'source_id': '2', 'name': 'PLA bleu', 'material': 'PLA', 'color_hex': '0000ff'},
                                {'source_type': 'manual', 'source_id': '3', 'name': 'PLA blanc', 'material': 'PLA', 'color_hex': 'ffffff'}]}]}
    assert logged.post('/api/print-history/manual', json=body, headers=_csrf(logged)).status_code == 200
    h = logged.get('/api/print-history/by-file', query_string={'path': '/x/plateaux.3mf'}).get_json()['history']
    assert len(h) == 1 and [p['plate'] for p in h[0]['plates']] == [1, 2]
    assert [len(p['spools']) for p in h[0]['plates']] == [1, 2]
    assert h[0]['filament_label'] == 'PLA rouge, PLA bleu, PLA blanc'
    # ancien format (une seule bobine) toujours accepté
    old = {'path': '/x/simple.stl', 'result': 'failed', 'spool': {'source_type': 'manual', 'source_id': '9', 'name': 'PETG noir', 'material': 'PETG'}}
    assert logged.post('/api/print-history/manual', json=old, headers=_csrf(logged)).status_code == 200
    h2 = logged.get('/api/print-history/by-file', query_string={'path': '/x/simple.stl'}).get_json()['history']
    assert h2[0]['plates'][0]['spools'][0]['name'] == 'PETG noir'


def test_already_printed_failure_reason_only_when_failed(stellio_app, logged):
    h = _csrf(logged)
    assert logged.post('/api/print-history/manual', json={'path': '/x/raison-ko.stl', 'result': 'failed', 'failure_reason': '  Décollé du plateau  '}, headers=h).status_code == 200
    assert logged.post('/api/print-history/manual', json={'path': '/x/raison-ok.stl', 'result': 'success', 'failure_reason': 'ignorée'}, headers=h).status_code == 200
    ko = logged.get('/api/print-history/by-file', query_string={'path': '/x/raison-ko.stl'}).get_json()['history'][0]
    ok = logged.get('/api/print-history/by-file', query_string={'path': '/x/raison-ok.stl'}).get_json()['history'][0]
    assert ko['failure_reason'] == 'Décollé du plateau' and not ok.get('failure_reason')


def test_open_filament_database_shops_are_merged(stellio_app, logged):
    links = logged.get('/api/links').get_json()['links']
    ofd = [l for l in links if l['group'] == 'Boutiques Open Filament Database']
    assert len(ofd) >= 40            # les doublons avec les liens existants (même site) sont ignorés
    assert len({l['id'] for l in links}) == len(links)
    r = logged.get('/api/filament/buy-links', query_string={'vendor': 'Polymaker', 'material': 'PLA', 'color': 'Rouge'})
    assert r.status_code == 200 and r.get_json()['shops']
