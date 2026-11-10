"""Mes likes / Mes créations : normalisation des réponses MakerWorld / Thingiverse, cache SQLite, fetchers (réseau simulé)."""
import datetime, logging, sqlite3, threading, time
import pytest
from conftest import load_from_main

NAMES = ['_acct_models_ensure', '_acct_extract_list', '_acct_ts', '_acct_norm_thingiverse', '_acct_norm_makerworld',
         '_acct_fetch_thingiverse', '_acct_fetch_makerworld', '_mw_get', '_mw_paged', '_MW_HDR', '_acct_sync_store',
         'ACCT_MODELS_MAX_ITEMS', 'ACCT_MODELS_PAGE_SIZE', '_parse_remote_dt', '_acct_redact', '_acct_log', '_acct_json_shape',
         '_acct_probe', '_acct_probe_log', '_acct_deep_items', '_acct_first', '_acct_norm_generic', '_ACCT_ID_KEYS',
         '_ACCT_TITLE_KEYS', '_acct_run_candidates', '_acct_cands', '_acct_endpoint_memo', '_acct_fetch_snapmaker',
         '_acct_fetch_nexprint', '_acct_fetch_crealitycloud', '_snapmaker_model_url', '_nexprint_model_url',
         '_crealitycloud_model_url', '_crealitycloud_headers', '_SNAPMAKER_PATHS', '_NEXPRINT_PATHS', '_CREALITY_PATHS',
         '_acct_ref_from_url', '_printables_parse_profile', '_acct_norm_printables', '_printables_gql', '_printables_introspect', '_acct_fetch_printables', '_PRINTABLES_MEDIA', '_PRINTABLES_FIELDS', 'PRINTABLES_HEADERS', 'PRINTABLES_API_URL', '_nexprint_clean_token', '_JWT_RE', '_cookie_header_to_dict', '_clean_cookie_header',
         '_MODEL_PAGE_UA', 'NEXPRINT_BASE', 'NEXPRINT_HEADERS', 'NEXPRINT_API', '_model_ref_from_url']


class Resp:
    def __init__(self, js, status=200):
        self._js, self.status_code, self.ok = js, status, status < 400
        self.headers, self.text = {'Content-Type': 'application/json'}, str(js)
    def json(self): return self._js
    def raise_for_status(self):
        if not self.ok: raise RuntimeError(f"HTTP {self.status_code}")


def make(requests_get, tmp_path=None):
    class R: pass
    r = R(); r.get = requests_get
    import collections, json, re
    r.post = lambda url, headers=None, params=None, json=None, timeout=0: requests_get(url, headers=headers, params=params, timeout=timeout, method='POST', json=json)
    r.Session = lambda: FakeSession(requests_get)
    return load_from_main(NAMES, {'requests': r, 'datetime': datetime, 'MAKERWORLD_API': 'https://api.bambulab.com',
                                  'app_logger': logging.getLogger('t'), 'time': time, 'collections': collections,
                                  'json': json, 're': re})


class FakeSession:
    def __init__(self, getter):
        self.headers, self.cookies, self._g = {}, type('C', (), {'set': lambda *a, **k: None})(), getter
        self.headers = type('H', (dict,), {})()
    def request(self, method, url, headers=None, params=None, json=None, timeout=0):
        return self._g(url, headers=headers, params=params or json, timeout=timeout, method=method)


def test_extract_list_shapes():
    ns = make(lambda *a, **k: None)
    f = ns['_acct_extract_list']
    assert f([{'a': 1}, 3]) == [{'a': 1}]
    assert f({'hits': [{'id': 1}]}) == [{'id': 1}]
    assert f({'data': {'list': [{'id': 2}]}}) == [{'id': 2}]
    assert f({'total': 0}) == []


def test_norm_thingiverse():
    ns = make(lambda *a, **k: None)
    n = ns['_acct_norm_thingiverse']({'id': 42, 'name': ' Vase ', 'thumbnail': 'http://t/x.jpg', 'like_count': 7,
        'creator': {'name': 'bob', 'public_url': 'https://tv/bob'}, 'added': '2024-05-01T10:00:00+00:00'})
    assert n['model_id'] == '42' and n['title'] == 'Vase' and n['creator'] == 'bob'
    assert n['url'] == 'https://www.thingiverse.com/thing:42' and n['ts'].startswith('2024-05-01')
    assert ns['_acct_norm_thingiverse']({'name': 'x'}) is None


def test_norm_makerworld_nested_and_images():
    ns = make(lambda *a, **k: None)
    n = ns['_acct_norm_makerworld']({'design': {'id': 9, 'title': 'Box', 'images': [{'url': 'http://i/1.png'}],
        'designCreator': {'name': 'Ann', 'handle': 'ann1'}, 'likeCount': 3}})
    assert n['url'] == 'https://makerworld.com/en/models/9' and n['thumb'] == 'http://i/1.png'
    assert n['creator_url'] == 'https://makerworld.com/en/@ann1'


def test_fetch_thingiverse_paginates():
    calls = []
    def get(url, headers=None, params=None, timeout=0, method='GET', json=None):
        calls.append((url, (params or {}).get('page')))
        if url.endswith('/users/me'): return Resp({'name': 'zed'})
        page = params['page']
        rows = [{'id': page * 100 + i, 'name': f't{i}'} for i in range(30 if page == 1 else 5)]
        return Resp(rows)
    ns = make(get)
    out = ns['_acct_fetch_thingiverse']('tok', 'likes')
    assert len(out) == 35 and any('/users/zed/likes' in c[0] for c in calls)
    ns['_acct_fetch_thingiverse']('tok', 'creations')
    assert any('/users/zed/things' in c[0] for c in calls)


def test_fetch_makerworld_likes_merges_and_dedupes():
    def get(url, headers=None, params=None, timeout=0, method='GET', json=None):
        if 'my/profile' in url: return Resp({'uid': 77})
        if 'my/design/like' in url: return Resp({'hits': [{'id': 1, 'title': 'A'}, {'id': 2, 'title': 'B'}]})
        if 'favorites/designs/77' in url: return Resp({'hits': [{'id': 2, 'title': 'B'}, {'id': 3, 'title': 'C'}]})
        return Resp({}, 404)
    ns = make(get)
    ids = [x['model_id'] for x in ns['_acct_fetch_makerworld']('tok', 'likes')]
    assert ids == ['1', '2', '3']


def test_fetch_makerworld_creations_uses_first_working_and_raises_if_none():
    def get(url, headers=None, params=None, timeout=0, method='GET', json=None):
        if 'my/profile' in url: return Resp({'uid': 5})
        if 'published/5/designs' in url: return Resp({'hits': [{'id': 8, 'title': 'Mine'}]})
        return Resp({}, 404)
    assert [x['model_id'] for x in make(get)['_acct_fetch_makerworld']('t', 'creations')] == ['8']
    def none(url, headers=None, params=None, timeout=0, method='GET', json=None):
        return Resp({'uid': 5}) if 'my/profile' in url else Resp({}, 404)
    with pytest.raises(RuntimeError):
        make(none)['_acct_fetch_makerworld']('t', 'creations')


def test_makerworld_expired_session_is_explicit():
    ns = make(lambda *a, **k: Resp({}, 401))
    with pytest.raises(RuntimeError, match='reconnecte'):
        ns['_acct_fetch_makerworld']('t', 'likes')


def test_store_replaces_set_and_keeps_old_on_error(tmp_path):
    db = str(tmp_path / 'd.sqlite')
    def get_db():
        c = sqlite3.connect(db); c.row_factory = sqlite3.Row; return c
    ns = make(lambda *a, **k: None)
    c = get_db()
    item = lambda i: {'model_id': str(i), 'title': 't', 'thumb': '', 'creator': '', 'creator_url': '', 'url': 'u', 'likes': 0, 'ts': ''}
    ns['_acct_sync_store'](c, 1, 'makerworld', 'likes', [item(1), item(2)])
    ns['_acct_sync_store'](c, 1, 'makerworld', 'likes', [item(3)])
    assert [r['model_id'] for r in c.execute("SELECT model_id FROM account_models")] == ['3']
    ns['_acct_sync_store'](c, 1, 'makerworld', 'likes', [], 'HTTP 500')   # erreur : on garde l'ancien cache
    assert c.execute("SELECT COUNT(*) FROM account_models").fetchone()[0] == 1
    assert c.execute("SELECT error FROM account_models_sync").fetchone()[0] == 'HTTP 500'


# ── Plateformes à endpoints devinés : cascade, schéma inconnu, journalisation ──
def test_redact_masks_secrets():
    ns = make(lambda *a, **k: None)
    r = ns['_acct_redact']
    out = r('Authorization: Bearer eyJabc.def.ghi cookie=abcdef token=XYZ mail a@b.fr ' + 'A' * 50)
    assert 'eyJabc' not in out and 'a@b.fr' not in out and 'XYZ' not in out and 'A' * 50 not in out


def test_probe_logs_status_and_shape():
    ns = make(lambda url, **k: Resp({'code': 0, 'data': {'list': [{'id': 1}]}}))
    ns['_acct_probe']('T', 'GET', 'https://x/y', headers={'Authorization': 'Bearer SECRET'})
    line = list(ns['_acct_probe_log'])[-1]
    assert 'HTTP 200' in line and 'https://x/y' in line and 'SECRET' not in line and 'objet{code, data}' in line


def test_deep_items_and_generic_norm():
    ns = make(lambda *a, **k: None)
    js = {'code': 0, 'data': {'weird': {'deep': [{'modelId': 'G12', 'modelName': 'Boîte', 'coverUrl': 'http://i/c.png',
                                                   'user': {'nickName': 'Zoé', 'id': 5}, 'likeNum': '4'}]}}}
    rows = ns['_acct_deep_items'](js)
    n = ns['_acct_norm_generic'](rows[0], ns['_nexprint_model_url'])
    assert (n['model_id'], n['title'], n['creator'], n['likes']) == ('G12', 'Boîte', 'Zoé', 4)
    assert n['url'] == 'https://www.nexprint.com/models/G12' and n['thumb'] == 'http://i/c.png'


def test_snapmaker_cascade_picks_working_endpoint_and_memoizes():
    seen = []
    def get(url, headers=None, params=None, timeout=0, method='GET', json=None):
        seen.append(url)
        if url.endswith('/api/model/collect/list'):
            return Resp({'code': 200, 'data': {'records': [{'id': 7, 'title': 'Pièce', 'cover': 'http://c/1.png'}]}})
        return Resp({'code': 404, 'msg': 'nope'}, 404)
    ns = make(get)
    tok = 'eyJaaa.bbb.ccc'
    out = ns['_acct_fetch_snapmaker'](tok, 'likes')
    assert [x['model_id'] for x in out] == ['7'] and out[0]['url'] == 'https://space.snapmaker.com/en/model/7'
    assert ns['_acct_endpoint_memo'][('snapmaker', 'likes')].endswith('/api/model/collect/list')
    seen.clear(); ns['_acct_fetch_snapmaker'](tok, 'likes')
    assert seen[0].endswith('/api/model/collect/list')          # l'endpoint mémorisé passe en premier


def test_snapmaker_all_fail_raises_with_hint_and_no_token_message():
    ns = make(lambda *a, **k: Resp({}, 404))
    with pytest.raises(RuntimeError, match='diagnostic'):
        ns['_acct_fetch_snapmaker']('eyJaaa.bbb.ccc', 'likes')
    with pytest.raises(RuntimeError, match='reconnecte'):
        ns['_acct_fetch_snapmaker']('rien', 'likes')


def test_nexprint_tries_post_after_get_and_normalizes():
    def get(url, headers=None, params=None, timeout=0, method='GET', json=None):
        if method == 'POST' and url.endswith('/model-base-info/like/list'):
            return Resp({'code': 0, 'data': {'list': [{'id': 'G9', 'name': 'Vase', 'coverUrl': 'http://c.png'}]}})
        return Resp({'code': 404}, 404)
    out = make(get)['_acct_fetch_nexprint']('auth_token=abc123', 'likes')
    assert out and out[0]['model_id'] == 'G9' and out[0]['url'].endswith('/models/G9')


def test_creality_requires_cookies_then_cascades():
    ns = make(lambda *a, **k: Resp({}, 404))
    with pytest.raises(RuntimeError, match='incomplète'):
        ns['_acct_fetch_crealitycloud']('a=b', 'likes')
    def get(url, headers=None, params=None, timeout=0, method='GET', json=None):
        assert method == 'POST' and json['userId'] == '42' or method == 'GET'
        if url.endswith('/api/cxy/v3/model/collectList'):
            return Resp({'code': 0, 'result': {'list': [{'id': 'abc', 'modelName': 'Clip', 'profileId': 'p1'}]}})
        return Resp({'code': 404}, 404)
    ns = make(get)
    out = ns['_acct_fetch_crealitycloud']('model_token=T; model_user_id=42', 'likes')
    assert out[0]['url'] == 'https://www.crealitycloud.com/model-detail/abc?profileId=p1'


def test_ref_from_url_extended():
    ns = make(lambda *a, **k: None)
    f = ns['_acct_ref_from_url']
    assert f('https://www.nexprint.com/models/G123') == ('Nexprint', 'G123')
    assert f('https://space.snapmaker.com/en/model/2430-x') == ('Snapmaker Space', '2430')
    assert f('https://www.crealitycloud.com/model-detail/abc?profileId=p1') == ('Creality Cloud', 'abc')
    assert f('https://makerworld.com/en/models/55') == ('MakerWorld', '55')


# ── Printables ──
def test_printables_profile_parsing():
    ns = make(lambda *a, **k: None)
    f = ns['_printables_parse_profile']
    assert f('https://www.printables.com/@Floppy_872036/models') == ('Floppy_872036', '872036')
    assert f('@Bob_12') == ('Bob_12', '12') and f('872036') == ('872036', '872036') and f('nope')[1] == ''


def test_norm_printables():
    ns = make(lambda *a, **k: None)
    n = ns['_acct_norm_printables']({'id': '55', 'name': 'Gear', 'slug': 'gear', 'likesCount': 9, 'datePublished': '2025-01-02T03:04:05Z',
                                      'image': {'filePath': 'media/prints/55/x.jpg'}, 'user': {'handle': 'Bob_12', 'publicUsername': 'Bob'}})
    assert n['url'] == 'https://www.printables.com/model/55-gear' and n['thumb'].endswith('/media/prints/55/x.jpg')
    assert n['creator'] == 'Bob' and n['creator_url'].endswith('/@Bob_12') and n['ts'].startswith('2025-01-02')


def test_printables_creations_second_variant_and_likes_need_token():
    posts = []
    def get(url, headers=None, params=None, timeout=0, method='GET', json=None):
        q = json['query']; posts.append(q[:40])
        if '__schema' in q: return Resp({'errors': [{'message': 'introspection disabled'}]})
        if 'user(id: $id) { id' in q: return Resp({'data': {'user': {'id': '12', 'handle': 'Bob_12'}}})
        if 'morePrints' in q: return Resp({'errors': [{'message': 'Cannot query field'}]})
        if 'user(id: $id) { prints' in q:
            return Resp({'data': {'user': {'prints': [{'id': '1', 'name': 'A', 'slug': 'a'}]}}})
        return Resp({'errors': [{'message': 'x'}]})
    ns = make(get)
    cred = '{"handle": "@Bob_12", "token": ""}'
    out = ns['_acct_fetch_printables'](cred, 'creations')
    assert [x['model_id'] for x in out] == ['1']
    with pytest.raises(RuntimeError, match='jeton'):
        ns['_acct_fetch_printables'](cred, 'likes')
    with pytest.raises(RuntimeError, match='profil'):
        ns['_acct_fetch_printables']('{"handle": "nope"}', 'creations')


def test_printables_likes_use_bearer_and_cookie_forms():
    seen = []
    def get(url, headers=None, params=None, timeout=0, method='GET', json=None):
        seen.append(dict(headers or {}))
        q = json['query']
        if 'likedPrints' in q and 'me {' not in q and 'user(id' not in q:
            return Resp({'data': {'likedPrints': [{'id': '3', 'name': 'L', 'slug': 'l'}]}})
        return Resp({'errors': [{'message': 'nope'}]})
    ns = make(get)
    out = ns['_acct_fetch_printables']('{"handle": "@B_1", "token": "abc.def"}', 'likes')
    assert out and any(h.get('Authorization') == 'Bearer abc.def' for h in seen)
    seen.clear()
    ns['_acct_fetch_printables']('{"handle": "@B_1", "token": "a=1; b=2"}', 'likes')
    assert any(h.get('Cookie') for h in seen)
