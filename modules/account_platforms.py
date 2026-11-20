"""Stellio — Plateformes de comptes (Thingiverse, MakerWorld, Creality Cloud, Printables, Nexprint, Snapmaker) : likes et créations

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `account_platforms.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
import json
import os
import platform
import re
import requests
import threading
import time
import uuid

_REQUIRED = (
    'ACCT_MODELS_AUTO_SYNC_SECONDS',
    'ACCT_MODELS_EXPERIMENTAL_RETRY_SECONDS',
    'ACCT_MODELS_KINDS',
    'ACCT_MODELS_MAX_ITEMS',
    'ACCT_MODELS_MIN_SYNC_GAP',
    'ACCT_MODELS_PAGE_SIZE',
    'CURRENT_VERSION',
    'MAKERWORLD_API',
    'NEXPRINT_API',
    'NEXPRINT_HEADERS',
    'PRINTABLES_API_URL',
    'PRINTABLES_HEADERS',
    'Response',
    '_JWT_RE',
    '_MODEL_PAGE_UA',
    '_acct_blank_resynced',
    '_acct_cands',
    '_acct_deep_items',
    '_acct_endpoint_memo',
    '_acct_extract_list',
    '_acct_first',
    '_acct_log',
    '_acct_models_lock',
    '_acct_models_running',
    '_acct_norm_generic',
    '_acct_norm_makerworld',
    '_acct_norm_thingiverse',
    '_acct_probe',
    '_acct_probe_log',
    '_acct_run_candidates',
    '_acct_token_for',
    '_acct_ts',
    '_clean_cookie_header',
    '_cookie_header_to_dict',
    '_model_ref_from_url',
    '_nexprint_clean_token',
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'load_settings',
    'login_required',
    'request',
    'save_settings',
    'session',
)
_OPTIONAL = ()   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('json', 'os', 'platform', 're', 'requests', 'threading', 'time', 'uuid', )

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
ACCT_MODELS_AUTO_SYNC_SECONDS = None
ACCT_MODELS_EXPERIMENTAL_RETRY_SECONDS = None
ACCT_MODELS_KINDS = None
ACCT_MODELS_MAX_ITEMS = None
ACCT_MODELS_MIN_SYNC_GAP = None
ACCT_MODELS_PAGE_SIZE = None
CURRENT_VERSION = None
MAKERWORLD_API = None
NEXPRINT_API = None
NEXPRINT_HEADERS = None
PRINTABLES_API_URL = None
PRINTABLES_HEADERS = None
Response = None
_JWT_RE = None
_MODEL_PAGE_UA = None
_acct_blank_resynced = None
_acct_cands = None
_acct_deep_items = None
_acct_endpoint_memo = None
_acct_extract_list = None
_acct_first = None
_acct_log = None
_acct_models_lock = None
_acct_models_running = None
_acct_norm_generic = None
_acct_norm_makerworld = None
_acct_norm_thingiverse = None
_acct_probe = None
_acct_probe_log = None
_acct_run_candidates = None
_acct_token_for = None
_acct_ts = None
_clean_cookie_header = None
_cookie_header_to_dict = None
_model_ref_from_url = None
_nexprint_clean_token = None
app = None
app_logger = None
get_db = None
jsonify = None
load_settings = None
login_required = None
request = None
save_settings = None
session = None


# ── Thingiverse (API officielle) ──────────────────────────────────────────
def _acct_fetch_thingiverse(token, kind):
    hdr = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    r, js = _acct_probe("Thingiverse profil", 'GET', "https://api.thingiverse.com/users/me", headers=hdr)
    if r is None or not r.ok:
        raise RuntimeError(f"Thingiverse : profil inaccessible (HTTP {getattr(r, 'status_code', '?')}), vérifie le token")
    name = (js or {}).get('name')
    if not name:
        raise RuntimeError("profil Thingiverse introuvable")
    path = f"/users/{name}/likes" if kind == 'likes' else f"/users/{name}/things"
    out, page, per = [], 1, ACCT_MODELS_PAGE_SIZE
    while len(out) < ACCT_MODELS_MAX_ITEMS:
        r, js = _acct_probe(f"Thingiverse {kind} p{page}", 'GET', "https://api.thingiverse.com" + path, headers=hdr,
                            params={"page": page, "per_page": per})
        if r is None:
            raise RuntimeError("Thingiverse injoignable")
        if not r.ok:
            raise RuntimeError(f"Thingiverse a répondu HTTP {r.status_code}")
        rows = _acct_extract_list(js)
        if not rows:
            break
        out.extend(rows)
        if len(rows) < per:
            break
        page += 1
    return [n for n in (_acct_norm_thingiverse(x) for x in out) if n]

# ── MakerWorld (likes : endpoints connus ; créations : variantes) ──────────
_MW_HDR = {"User-Agent": "BambuStudio/01.09.00.00", "Accept": "application/json"}

def _mw_get(path, token, params=None, label='MakerWorld'):
    return _acct_probe(label, 'GET', MAKERWORLD_API + path, headers={**_MW_HDR, "Authorization": f"Bearer {token}"}, params=params)

def _mw_paged(path, token, limit=None):
    limit = limit or ACCT_MODELS_PAGE_SIZE      # lu à l'appel : la valeur est injectée par main.py après l'import du module
    out, offset = [], 0
    while len(out) < ACCT_MODELS_MAX_ITEMS:
        r, js = _mw_get(path, token, {"offset": offset, "limit": limit}, label=f"MakerWorld o{offset}")
        if r is None:
            return out if out else None
        if r.status_code in (401, 403):
            raise RuntimeError(f"MakerWorld a refusé la session (HTTP {r.status_code}), reconnecte-toi")
        if not r.ok:
            return out if out else None
        rows = _acct_extract_list(js) or _acct_deep_items(js)
        if not rows:
            break
        out.extend(rows)
        if len(rows) < limit:
            break
        offset += limit
    return out

def _acct_fetch_makerworld(token, kind):
    rp, prof = _mw_get("/v1/design-user-service/my/profile", token, label='MakerWorld profil')
    if rp is not None and rp.status_code in (401, 403):
        raise RuntimeError(f"MakerWorld a refusé la session (HTTP {rp.status_code}), reconnecte-toi")
    prof = prof if isinstance(prof, dict) else {}
    uid = prof.get('uid') or (prof.get('data') or {}).get('uid') if isinstance(prof, dict) else None
    _acct_log(f"MakerWorld uid détecté = {uid!r}")
    if kind == 'likes':
        paths = ["/v1/design-service/my/design/like"]
        if uid:
            paths.append(f"/v1/design-service/favorites/designs/{uid}")
    else:
        if not uid:
            raise RuntimeError("MakerWorld : identifiant utilisateur introuvable (profil)")
        paths = [f"/v1/design-service/published/{uid}/design", "/v1/design-service/my/design/published",
                 f"/v1/design-service/published/{uid}/designs", f"/v1/design-service/my/design/list",
                 f"/v1/design-service/design/user/{uid}"]
    seen, merged, worked = set(), [], False
    for p in paths:
        rows = _mw_paged(p, token)
        if rows is None:
            continue
        worked = True
        _acct_log(f"MakerWorld {kind} via {p} : {len(rows)} modèle(s)")
        for x in rows:
            n = _acct_norm_makerworld(x)
            if n and n['model_id'] not in seen:
                seen.add(n['model_id'])
                merged.append(n)
        if kind == 'creations' and rows:
            break
    if not worked:
        raise RuntimeError("aucun endpoint MakerWorld n'a répondu")
    return merged

# ── Creality Cloud (endpoints devinés, session par cookies) ────────────────
def _crealitycloud_headers(cookie_header, ck, referer="https://www.crealitycloud.com/"):
    import uuid
    offset = -(time.altzone if (time.daylight and time.localtime().tm_isdst > 0) else time.timezone)
    return {
        "User-Agent": _MODEL_PAGE_UA, "Accept": "application/json", "Content-Type": "application/json",
        "Origin": "https://www.crealitycloud.com", "Referer": referer, "Cookie": cookie_header,
        "__cxy_app_ch_": "Chrome 124.0", "__cxy_app_id_": "cxy-gen2", "__cxy_app_ver_": "7.3.28",
        "__cxy_brand_": "creality", "__cxy_duid_": ck.get('model_device_id') or str(uuid.uuid4()),
        "__cxy_os_lang_": ck.get('__CXY_OS_LANG_') or ck.get('model_lang') or '9', "__cxy_os_ver_": "Windows 10",
        "__cxy_platform_": "2", "__cxy_requestid_": str(uuid.uuid4()), "__cxy_timezone_": str(offset),
        "__cxy_token_": ck.get('model_token', ''), "__cxy_uid_": ck.get('model_user_id', ''),
    }

_CREALITY_PATHS = {
    'likes': ['/api/cxy/v3/model/likeList', '/api/cxy/v3/model/collectList', '/api/cxy/v3/model/collectionList',
              '/api/cxy/v3/model/favoriteList', '/api/cxy/v2/model/likeList', '/api/cxy/v2/model/collectList',
              '/api/cxy/v3/user/likeModelList', '/api/cxy/v3/user/collectModelList'],
    'creations': ['/api/cxy/v3/model/userModelList', '/api/cxy/v3/model/listByUser', '/api/cxy/v3/model/myModelList',
                  '/api/cxy/v3/model/publishList', '/api/cxy/v2/model/userModelList', '/api/cxy/v3/user/modelList'],
}

def _crealitycloud_model_url(d, n, uid):
    mid = n['model_id']
    pid = _acct_first(d, ('profileId', 'defaultProfileId', 'printProfileId'), '')
    url = f"https://www.crealitycloud.com/model-detail/{mid}" + (f"?profileId={pid}" if pid else '')
    return url, (f"https://www.crealitycloud.com/user/{uid}" if uid else '')

def _acct_fetch_crealitycloud(cookie, kind):
    ck_header = _clean_cookie_header(cookie)
    ck = _cookie_header_to_dict(ck_header)
    uid, token = ck.get('model_user_id'), ck.get('model_token')
    _acct_log(f"Creality Cloud : cookies présents = {sorted(ck.keys())} ; model_user_id={'oui' if uid else 'NON'} ; model_token={'oui' if token else 'NON'}")
    if not uid or not token:
        raise RuntimeError("session Creality Cloud incomplète (cookies model_token / model_user_id absents), reconnecte-toi")
    hdr = _crealitycloud_headers(ck_header, ck)
    cands = _acct_cands('POST ', _CREALITY_PATHS[kind], paged=True)

    def call(c, page):
        body = {"page": page + 1, "pageSize": ACCT_MODELS_PAGE_SIZE, "userId": uid, "uid": uid, "pageNum": page + 1}
        return _acct_probe(f"Creality {kind}", 'POST', "https://www.crealitycloud.com" + c['path'], headers=hdr, json_body=body)
    try:
        return _acct_run_candidates('crealitycloud', kind, cands, call, lambda x: _acct_norm_generic(x, _crealitycloud_model_url))
    except RuntimeError:
        if kind != 'creations':
            raise
    # Repli : la page publique du profil (rendu serveur) contient parfois la liste des modèles
    r, _js = _acct_probe("Creality profil HTML", 'GET', f"https://www.crealitycloud.com/user/{uid}",
                         headers={"User-Agent": _MODEL_PAGE_UA, "Cookie": ck_header, "Accept": "text/html"})
    if r is not None and r.ok:
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text or '', re.S)
        _acct_log(f"Creality profil HTML : __NEXT_DATA__ {'trouvé' if m else 'absent'} ({len(r.text or '')} octets)")
        if m:
            try:
                rows = _acct_deep_items(json.loads(m.group(1)))
            except ValueError:
                rows = []
            items = [n for n in (_acct_norm_generic(x, _crealitycloud_model_url) for x in rows) if n]
            if items:
                return items
    raise RuntimeError("aucun endpoint Creality Cloud n'a répondu : voir le rapport de diagnostic")

# ── Snapmaker Space (endpoints devinés, JWT) ───────────────────────────────
_SNAPMAKER_PATHS = {
    'likes': ['/api/model/like/list', '/api/model/collect/list', '/api/model/favorite/list', '/api/user/like/list',
              '/api/model/likes', '/api/model/liked'],
    'creations': ['/api/model/my/list', '/api/model/user/list', '/api/user/model/list', '/api/model/mine',
                  '/api/model/my', '/api/model/published/list'],
}

def _snapmaker_model_url(d, n, uid):
    return f"https://space.snapmaker.com/en/model/{n['model_id']}", (f"https://space.snapmaker.com/en/user/{uid}" if uid else '')

def _acct_fetch_snapmaker(stored, kind):
    tokens = _JWT_RE.findall(stored or '')
    _acct_log(f"Snapmaker : {len(tokens)} JWT dans la session enregistrée")
    if not tokens:
        raise RuntimeError("session Snapmaker Space absente, reconnecte-toi")
    last = None
    for tok in tokens:
        hdr = {"User-Agent": _MODEL_PAGE_UA, "Accept": "application/json", "Content-Type": "application/json",
               "x-custom-site": "Web-Space", "Authorization": f"Bearer {tok}",
               "Origin": "https://space.snapmaker.com", "Referer": "https://space.snapmaker.com/"}
        cands = _acct_cands('GET ', _SNAPMAKER_PATHS[kind], paged=True)

        def call(c, page):
            params = {"page": page + 1, "pageNum": page + 1, "pageSize": ACCT_MODELS_PAGE_SIZE, "size": ACCT_MODELS_PAGE_SIZE}
            return _acct_probe(f"Snapmaker {kind}", 'GET', "https://api-models.snapmaker.com" + c['path'], headers=hdr, params=params)
        try:
            return _acct_run_candidates('snapmaker', kind, cands, call, lambda x: _acct_norm_generic(x, _snapmaker_model_url))
        except RuntimeError as e:
            last = e
    raise last or RuntimeError("Snapmaker Space : aucun endpoint n'a répondu")

# ── Nexprint (endpoints devinés, cookie auth_token) ────────────────────────
_NEXPRINT_PATHS = {
    'likes': ['/model-base-info/like/list', '/model-base-info/collect/list', '/model-base-info/user-like/list',
              '/user/like/list', '/collection/model/list'],
    'creations': ['/model-base-info/my/list', '/model-base-info/user/list', '/model-base-info/mine/list',
                  '/model-base-info/publish/list', '/user/model/list'],
}

def _nexprint_model_url(d, n, uid):
    return f"https://www.nexprint.com/models/{n['model_id']}", ''

def _acct_fetch_nexprint(stored, kind):
    token = _nexprint_clean_token(stored)
    if not token:
        raise RuntimeError("cookie auth_token Nexprint absent, reconnecte-toi")
    _acct_log(f"Nexprint : jeton longueur={len(token)}")
    sess = requests.Session()
    sess.headers.update(NEXPRINT_HEADERS)
    sess.headers.update({"Authorization": "Bearer " + token, "client-id": "Nexprint", "user-lang": "en"})
    sess.cookies.set('auth_token', token, domain='.nexprint.com', path='/')
    cands = []
    for p in _NEXPRINT_PATHS[kind]:
        cands.append({'label': f"GET {p}", 'path': p, 'method': 'GET', 'paged': True})
        cands.append({'label': f"POST {p}", 'path': p, 'method': 'POST', 'paged': True})

    def call(c, page):
        q = {"pageNum": page + 1, "page": page + 1, "pageSize": ACCT_MODELS_PAGE_SIZE, "size": ACCT_MODELS_PAGE_SIZE}
        if c['method'] == 'GET':
            return _acct_probe(f"Nexprint {kind}", 'GET', NEXPRINT_API + c['path'], params=q, session_obj=sess)
        return _acct_probe(f"Nexprint {kind}", 'POST', NEXPRINT_API + c['path'], json_body=q, session_obj=sess)
    return _acct_run_candidates('nexprint', kind, cands, call, lambda x: _acct_norm_generic(x, _nexprint_model_url))

# ── Printables (API GraphQL publique non officielle) ───────────────────────
# Créations : requêtes publiques à partir du profil (@pseudo_123456 : les chiffres finaux sont l'identifiant).
# Likes : nécessitent une session (jeton / cookie collé dans Paramètres) ; noms de requêtes inconnus → variantes + introspection.
_PRINTABLES_MEDIA = "https://media.printables.com/"

_PRINTABLES_FIELDS = "id name slug likesCount datePublished image { filePath } user { id handle publicUsername }"

def _printables_parse_profile(raw):
    """'@Nom_123456', 'https://www.printables.com/@Nom_123456/models' ou '123456' -> (handle, id numérique)."""
    s = str(raw or '').strip()
    m = re.search(r'@([\w.\-]+)', s)
    handle = m.group(1) if m else s.strip('/@ ')
    uid = re.search(r'(\d+)$', handle)
    return handle, (uid.group(1) if uid else '')

def _acct_norm_printables(it):
    p = it.get('print') if isinstance(it.get('print'), dict) else it
    if not isinstance(p, dict) or not p.get('id'):
        return None
    pid = str(p['id'])
    u = p.get('user') if isinstance(p.get('user'), dict) else {}
    img = p.get('image') if isinstance(p.get('image'), dict) else {}
    fp = img.get('filePath') or ''
    thumb = (fp if fp.startswith('http') else _PRINTABLES_MEDIA + fp.lstrip('/')) if fp else ''
    slug = p.get('slug') or ''
    return {
        'model_id': pid,
        'title': str(p.get('name') or '').strip(),
        'thumb': thumb,
        'creator': str(u.get('publicUsername') or u.get('handle') or '').strip(),
        'creator_url': f"https://www.printables.com/@{u['handle']}" if u.get('handle') else '',
        'url': f"https://www.printables.com/model/{pid}" + (f"-{slug}" if slug else ''),
        'likes': int(p.get('likesCount') or 0),
        'ts': _acct_ts(p.get('datePublished') or p.get('firstPublish')),
    }

def _printables_gql(label, query, variables, headers):
    r, js = _acct_probe(label, 'POST', PRINTABLES_API_URL, headers=headers,
                        json_body={"query": query, "variables": variables})
    errs = (js or {}).get('errors') if isinstance(js, dict) else None
    if errs:
        _acct_log(f"{label} erreurs GraphQL : {str(errs)[:300]}")
    return r, (js.get('data') if isinstance(js, dict) else None), errs

def _printables_introspect(headers, user_type_hint=None):
    """Journalise les requêtes/champs du schéma qui parlent de likes, collections ou impressions (aide au diagnostic)."""
    q = "{ __schema { queryType { fields { name args { name } type { name kind ofType { name kind } } } } } }"
    r, data, errs = _printables_gql("Printables introspection", q, {}, headers)
    try:
        fields = data['__schema']['queryType']['fields']
    except Exception:
        _acct_log("Printables introspection : désactivée ou refusée (normal), on continue avec les variantes connues")
        return
    pat = re.compile(r'like|saved|collection|favou?rite|print|user|me$|my', re.I)
    keep = [f for f in fields if pat.search(f.get('name', ''))]
    _acct_log(f"Printables schéma : {len(fields)} requêtes racine, {len(keep)} pertinentes :")
    for f in keep[:80]:
        t = f.get('type') or {}
        tn = t.get('name') or (t.get('ofType') or {}).get('name') or t.get('kind')
        _acct_log(f"   Query.{f['name']}({', '.join(a['name'] for a in f.get('args') or [])}) -> {tn}")

def _acct_fetch_printables(cred, kind):
    try:
        c = json.loads(cred) if cred else {}
    except ValueError:
        c = {}
    handle, uid = _printables_parse_profile(c.get('handle'))
    token = (c.get('token') or '').strip()
    hdr = dict(PRINTABLES_HEADERS)
    if token:
        if '=' in token and ' ' not in token.replace('; ', ''):
            hdr['Cookie'] = _clean_cookie_header(token)
        else:
            hdr['Authorization'] = token if token.lower().startswith('bearer ') else f"Bearer {token}"
    _acct_log(f"Printables : profil={handle!r} id={uid!r} jeton={'oui' if token else 'non'} ({kind})")
    if not uid:
        raise RuntimeError("profil Printables illisible : colle le lien du profil (https://www.printables.com/@pseudo_123456)")
    _printables_introspect(hdr)
    r, data, _e = _printables_gql("Printables profil", "query($id: ID!) { user(id: $id) { id handle publicUsername } }", {"id": uid}, hdr)
    _acct_log(f"Printables profil résolu : {(data or {}).get('user')}")

    F = _PRINTABLES_FIELDS
    P = ACCT_MODELS_PAGE_SIZE
    if kind == 'creations':
        qs = [
            ("morePrints", f"query($id: ID!, $limit: Int, $offset: Int) {{ morePrints(userId: $id, limit: $limit, offset: $offset) {{ {F} }} }}"),
            ("user.prints", f"query($id: ID!, $limit: Int, $offset: Int) {{ user(id: $id) {{ prints(limit: $limit, offset: $offset) {{ {F} }} }} }}"),
            ("userPrints", f"query($id: ID!, $limit: Int, $offset: Int) {{ userPrints(userId: $id, limit: $limit, offset: $offset) {{ {F} }} }}"),
            ("searchPrints2(userId)", f"query($id: ID!, $limit: Int, $offset: Int) {{ searchPrints2(userId: $id, limit: $limit, offset: $offset, printType: print) {{ items {{ {F} }} }} }}"),
        ]
    else:
        if not token:
            raise RuntimeError("Printables : les likes nécessitent un jeton de session (Paramètres → Comptes externes → Printables)")
        qs = [
            ("likedPrints", f"query($limit: Int, $offset: Int) {{ likedPrints(limit: $limit, offset: $offset) {{ {F} }} }}"),
            ("me.likedPrints", f"query($limit: Int, $offset: Int) {{ me {{ likedPrints(limit: $limit, offset: $offset) {{ {F} }} }} }}"),
            ("user.likedPrints", f"query($id: ID!, $limit: Int, $offset: Int) {{ user(id: $id) {{ likedPrints(limit: $limit, offset: $offset) {{ {F} }} }} }}"),
            ("userLikedPrints", f"query($id: ID!, $limit: Int, $offset: Int) {{ userLikedPrints(userId: $id, limit: $limit, offset: $offset) {{ {F} }} }}"),
            ("likedModels", f"query($limit: Int, $offset: Int) {{ likedModels(limit: $limit, offset: $offset) {{ {F} }} }}"),
        ]
    memo = _acct_endpoint_memo.get(('printables', kind))
    qs.sort(key=lambda x: 0 if x[0] == memo else 1)
    any_ok = False
    for label, q in qs:
        out, offset = [], 0
        while len(out) < ACCT_MODELS_MAX_ITEMS:
            r, data, errs = _printables_gql(f"Printables {kind} [{label}] o{offset}", q, {"id": uid, "limit": P, "offset": offset}, hdr)
            if r is None or r.status_code >= 400 or errs or not isinstance(data, dict):
                break
            rows = _acct_extract_list(data) or _acct_deep_items(data)
            any_ok = True
            if not rows:
                break
            out.extend(rows)
            if len(rows) < P:
                break
            offset += P
        if out:
            _acct_log(f"printables {kind} : requête retenue = {label} ({len(out)} élément(s)) ; champs du 1er : {sorted(out[0].keys())[:20]}")
            _acct_endpoint_memo[('printables', kind)] = label
            return [n for n in (_acct_norm_printables(x) for x in out) if n]
    if any_ok:
        _acct_log(f"printables {kind} : requêtes valides mais aucune donnée")
        return []
    raise RuntimeError("aucune requête Printables n'a abouti : voir le rapport de diagnostic (schéma + erreurs GraphQL)")

ACCT_MODELS_PLATFORMS = {
    'makerworld': {'label': 'MakerWorld', 'fetch': _acct_fetch_makerworld},
    'thingiverse': {'label': 'Thingiverse', 'fetch': _acct_fetch_thingiverse},
    'crealitycloud': {'label': 'Creality Cloud', 'fetch': _acct_fetch_crealitycloud, 'experimental': True},
    'snapmaker': {'label': 'Snapmaker Space', 'fetch': _acct_fetch_snapmaker, 'experimental': True},
    'nexprint': {'label': 'Nexprint', 'fetch': _acct_fetch_nexprint, 'experimental': True},
    'printables': {'label': 'Printables', 'fetch': _acct_fetch_printables, 'experimental': True},
}

def _acct_ref_from_url(url):
    """Comme _model_ref_from_url, étendu aux plateformes de Mes likes (sans toucher au vérificateur de mises à jour)."""
    ref = _model_ref_from_url(url)
    if ref:
        return ref
    u, low = str(url or ''), str(url or '').lower()
    m = re.search(r'/models/([A-Za-z]\d+)', u)
    if 'nexprint.com' in low and m:
        return ('Nexprint', m.group(1))
    m = re.search(r'/model/(\d+)', u)
    if 'snapmaker.com' in low and m:
        return ('Snapmaker Space', m.group(1))
    m = re.search(r'/model-detail/([^/?#]+)', u)
    if 'crealitycloud.com' in low and m:
        return ('Creality Cloud', m.group(1))
    return None

def _acct_models_ensure(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS account_models (
        user_id INTEGER NOT NULL, platform TEXT NOT NULL, kind TEXT NOT NULL, model_id TEXT NOT NULL,
        title TEXT DEFAULT '', thumb TEXT DEFAULT '', creator TEXT DEFAULT '', creator_url TEXT DEFAULT '',
        url TEXT DEFAULT '', likes INTEGER DEFAULT 0, item_ts TEXT DEFAULT '', pos INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, platform, kind, model_id))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS account_models_sync (
        user_id INTEGER NOT NULL, platform TEXT NOT NULL, kind TEXT NOT NULL,
        synced_at REAL DEFAULT 0, error TEXT DEFAULT '', PRIMARY KEY (user_id, platform, kind))""")

def _acct_sync_store(conn, user_id, platform, kind, items, error=''):
    _acct_models_ensure(conn)
    if not error:
        conn.execute("DELETE FROM account_models WHERE user_id = ? AND platform = ? AND kind = ?", (user_id, platform, kind))
        for pos, n in enumerate(items):
            conn.execute(
                """INSERT OR REPLACE INTO account_models
                   (user_id, platform, kind, model_id, title, thumb, creator, creator_url, url, likes, item_ts, pos)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (user_id, platform, kind, n['model_id'], n['title'], n['thumb'], n['creator'], n['creator_url'],
                 n['url'], n['likes'], n['ts'], pos))
    conn.execute(
        """INSERT INTO account_models_sync (user_id, platform, kind, synced_at, error) VALUES (?,?,?,?,?)
           ON CONFLICT(user_id, platform, kind) DO UPDATE SET synced_at = excluded.synced_at, error = excluded.error""",
        (user_id, platform, kind, time.time(), error or ''))
    conn.commit()

def _acct_sync_platform(user_id, platform):
    spec = ACCT_MODELS_PLATFORMS.get(platform)
    token = _acct_token_for(user_id, platform)
    if not spec or not token:
        return {}
    key = (user_id, platform)
    with _acct_models_lock:
        if key in _acct_models_running:
            return {}
        _acct_models_running.add(key)
    result = {}
    try:
        _acct_log(f"=== Synchronisation {spec['label']} (utilisateur {user_id}) ===")
        for kind in ACCT_MODELS_KINDS:
            try:
                items = spec['fetch'](token, kind)
                err = ''
            except Exception as e:
                items, err = [], (str(e)[:200] or e.__class__.__name__)
                _acct_log(f"{spec['label']} {kind} : ERREUR {e.__class__.__name__}: {err}")
            result[kind] = (len(items), err)
            conn = get_db()
            try:
                _acct_sync_store(conn, user_id, platform, kind, items, err)
            finally:
                conn.close()
            _acct_log(f"{spec['label']} {kind} : {len(items)} modèle(s) enregistré(s){' (erreur : ' + err + ')' if err else ''}")
    finally:
        with _acct_models_lock:
            _acct_models_running.discard(key)
    return result

def _acct_sync_async(user_id, platforms, force=False):
    conn = get_db()
    try:
        _acct_models_ensure(conn)
        rows = conn.execute(
            "SELECT platform, MAX(synced_at) AS s, MAX(CASE WHEN error != '' THEN 1 ELSE 0 END) AS e "
            "FROM account_models_sync WHERE user_id = ? GROUP BY platform", (user_id,)).fetchall()
    finally:
        conn.close()
    last = {r['platform']: (r['s'] or 0, bool(r['e'])) for r in rows}
    now = time.time()
    started = []
    for p in platforms:
        s, failing = last.get(p, (0, False))
        gap = now - s
        wait = ACCT_MODELS_EXPERIMENTAL_RETRY_SECONDS if (failing and ACCT_MODELS_PLATFORMS[p].get('experimental')) else ACCT_MODELS_AUTO_SYNC_SECONDS
        if gap < ACCT_MODELS_MIN_SYNC_GAP or (not force and gap < wait):
            continue
        threading.Thread(target=_acct_sync_platform, args=(user_id, p), daemon=True).start()
        started.append(p)
    return started

ACCT_MODELS_AUTO_DAILY_SECONDS = 24 * 3600

def _acct_models_connected_pairs():
    """(utilisateur, plateforme) de tous les comptes externes connectés."""
    conn = get_db()
    try:
        _acct_models_ensure(conn)
        rows = conn.execute(
            "SELECT DISTINCT user_id, platform FROM account_credentials WHERE ((api_key IS NOT NULL AND api_key != '') "
            "OR (platform = 'printables' AND email IS NOT NULL AND email != ''))").fetchall()
    finally:
        conn.close()
    return [(r['user_id'], r['platform']) for r in rows if r['platform'] in ACCT_MODELS_PLATFORMS]

def _acct_models_auto_check(reason=''):
    """Test automatique de « Mes likes / Mes créations » : resynchronise chaque compte connecté (tous les utilisateurs) et note le moment du test."""
    by_user = {}
    for uid, platform in _acct_models_connected_pairs():
        by_user.setdefault(uid, []).append(platform)
    started = 0
    for uid, plats in by_user.items():
        started += len(_acct_sync_async(uid, plats, force=True))
    settings = load_settings() or {}
    settings['acct_models_auto_last'] = time.time()
    settings['acct_models_auto_reason'] = reason
    save_settings(settings)
    app_logger.info(f"[Comptes] Test automatique Mes likes / Mes créations ({reason}) : {started} synchronisation(s) lancée(s)")
    return started

def _acct_models_auto_loop():
    """Version de bureau : un test à chaque lancement de l'application. Serveur (sans fenêtre) : un test toutes les 24 h ;
    le moment du dernier test est mémorisé, un redémarrage du serveur n'en relance donc pas un autre avant 24 h."""
    time.sleep(45)
    if not _MAIN.get('STELLIO_HEADLESS'):
        try:
            _acct_models_auto_check('lancement')
        except Exception as e:
            app_logger.info(f"[Comptes] Test automatique impossible : {e}")
        return
    while True:
        try:
            last = float((load_settings() or {}).get('acct_models_auto_last') or 0)
            if time.time() - last >= ACCT_MODELS_AUTO_DAILY_SECONDS:
                _acct_models_auto_check('toutes les 24 h')
        except Exception as e:
            app_logger.info(f"[Comptes] Test automatique impossible : {e}")
        time.sleep(600)

def api_account_models_overview():
    uid = session['user_id']
    conn = get_db()
    try:
        _acct_models_ensure(conn)
        connected = [p for p in ACCT_MODELS_PLATFORMS
                     if conn.execute("SELECT 1 FROM account_credentials WHERE user_id = ? AND platform = ? AND ((api_key IS NOT NULL AND api_key != '') OR (platform = 'printables' AND email IS NOT NULL AND email != ''))",
                                     (uid, p)).fetchone()]
        counts = {(r['platform'], r['kind']): r['n'] for r in conn.execute(
            "SELECT platform, kind, COUNT(*) AS n FROM account_models WHERE user_id = ? GROUP BY platform, kind", (uid,))}
        sync = {(r['platform'], r['kind']): r for r in conn.execute(
            "SELECT platform, kind, synced_at, error FROM account_models_sync WHERE user_id = ?", (uid,))}
    finally:
        conn.close()
    blank = []
    try:   # fiches enregistrées sans titre ni image (ancienne lecture incomplète) : une seule resynchronisation automatique par plateforme et par lancement
        conn = get_db()
        try:
            blank = [p for p in connected if (uid, p) not in _acct_blank_resynced and conn.execute(
                "SELECT 1 FROM account_models WHERE user_id = ? AND platform = ? AND title = '' AND thumb = '' LIMIT 1", (uid, p)).fetchone()]
        finally:
            conn.close()
        for p in blank:
            _acct_blank_resynced.add((uid, p))
    except Exception:
        blank = []
    started = _acct_sync_async(uid, connected, force=(request.args.get('force') == '1') or bool(blank)) if connected else []
    platforms = []
    for p in connected:
        platforms.append({
            'platform': p, 'label': ACCT_MODELS_PLATFORMS[p]['label'],
            'likes': counts.get((p, 'likes'), 0), 'creations': counts.get((p, 'creations'), 0),
            'synced_at': max([(sync.get((p, k)) or {'synced_at': 0})['synced_at'] or 0 for k in ACCT_MODELS_KINDS] or [0]),
            'error': ('' if (counts.get((p, 'likes'), 0) + counts.get((p, 'creations'), 0)) > 0 else
                      next((sync[(p, k)]['error'] for k in ACCT_MODELS_KINDS if sync.get((p, k)) and sync[(p, k)]['error']), '')),   # erreur partielle (ex. « créations » introuvables) : pas affichée si des modèles existent
            'syncing': (uid, p) in _acct_models_running or p in started,
        })
    return jsonify({'platforms': platforms, 'auto_checked_at': (load_settings() or {}).get('acct_models_auto_last') or 0,
                    'likes_total': sum(x['likes'] for x in platforms),
                    'creations_total': sum(x['creations'] for x in platforms)})

def api_account_models_list(kind):
    if kind not in ACCT_MODELS_KINDS:
        return jsonify({"error": "type inconnu"}), 404
    uid = session['user_id']
    conn = get_db()
    try:
        _acct_models_ensure(conn)
        rows = conn.execute("SELECT * FROM account_models WHERE user_id = ? AND kind = ? ORDER BY platform, pos",
                            (uid, kind)).fetchall()
        hist = {}
        for r in conn.execute("SELECT source_url, file_name, file_path FROM download_history WHERE user_id = ? AND source_url != '' ORDER BY id ASC", (uid,)):
            ref = _acct_ref_from_url(r['source_url'])
            if ref:
                hist[ref] = {'file_name': r['file_name'], 'file_path': r['file_path']}
    finally:
        conn.close()
    out = {}
    for r in rows:
        label = ACCT_MODELS_PLATFORMS.get(r['platform'], {}).get('label', r['platform'])
        h = hist.get((label, r['model_id']))
        if h and not os.path.exists(h['file_path'] or ''):
            h = None
        out.setdefault(r['platform'], {'platform': r['platform'], 'label': label, 'items': []})['items'].append({
            'model_id': r['model_id'], 'title': r['title'], 'thumb': r['thumb'], 'creator': r['creator'],
            'creator_url': r['creator_url'], 'url': r['url'], 'likes': r['likes'], 'ts': r['item_ts'],
            'in_library': bool(h), 'file_name': h['file_name'] if h else '', 'file_path': h['file_path'] if h else '',
        })
    return jsonify({'kind': kind, 'platforms': list(out.values())})

def api_account_models_sync():
    uid = session['user_id']
    wanted = (request.json or {}).get('platform')
    plats = [wanted] if wanted in ACCT_MODELS_PLATFORMS else list(ACCT_MODELS_PLATFORMS)
    started = _acct_sync_async(uid, plats, force=True)
    return jsonify({'started': started})

def api_account_models_debug():
    """Lance une synchronisation complète (de façon synchrone) et renvoie le rapport détaillé : chaque requête
    envoyée aux plateformes, statut, forme de la réponse. Secrets masqués. À coller tel quel dans un message d'aide."""
    uid = session['user_id']
    conn = get_db()
    try:
        _acct_models_ensure(conn)
        connected = [p for p in ACCT_MODELS_PLATFORMS
                     if conn.execute("SELECT 1 FROM account_credentials WHERE user_id = ? AND platform = ? AND ((api_key IS NOT NULL AND api_key != '') OR (platform = 'printables' AND email IS NOT NULL AND email != ''))",
                                     (uid, p)).fetchone()]
    finally:
        conn.close()
    only = (request.args.get('platform') or (request.json or {}).get('platform') if request.method == 'POST' else request.args.get('platform'))
    if only in ACCT_MODELS_PLATFORMS:
        connected = [p for p in connected if p == only]
    _acct_probe_log.clear()
    _acct_log(f"Rapport Mes likes / Mes créations — Stellio {CURRENT_VERSION} — comptes connectés : {connected or 'aucun'}")
    summary = []
    for p in connected:
        res = _acct_sync_platform(uid, p)
        for kind, (n, err) in res.items():
            summary.append(f"  {ACCT_MODELS_PLATFORMS[p]['label']:<16} {kind:<10} {n:>4} modèle(s){('  ERREUR : ' + err) if err else ''}")
    text = "RÉSUMÉ\n" + ("\n".join(summary) or "  (aucun compte connecté parmi les plateformes prises en charge)") + \
           "\n\nDÉTAIL DES REQUÊTES\n" + "\n".join(_acct_probe_log)
    return Response(text, mimetype='text/plain; charset=utf-8')


_ROUTES = (
    ('/api/account-models/overview', ['GET'], 'api_account_models_overview', ('login_required', )),
    ('/api/account-models/<kind>', ['GET'], 'api_account_models_list', ('login_required', )),
    ('/api/account-models/sync', ['POST'], 'api_account_models_sync', ('login_required', )),
    ('/api/account-models/debug', ['GET', 'POST'], 'api_account_models_debug', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"account_platforms.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {}
