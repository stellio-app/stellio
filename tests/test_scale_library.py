"""1.1.7 — grosses bibliothèques (test de charge à 50 000 modèles) : étiquettes au-delà de la limite SQLite, rendu progressif."""
import ast, os, sqlite3
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _helper():
    src = open(os.path.join(ROOT, 'main.py'), encoding='utf-8').read()
    for n in ast.parse(src).body:
        if isinstance(n, ast.FunctionDef) and n.name == '_tags_for_paths':
            ns = {}; exec(ast.get_source_segment(src, n), ns); return ns['_tags_for_paths']
    raise AssertionError('_tags_for_paths introuvable')


def test_etiquettes_avec_50000_fichiers():
    c = sqlite3.connect(':memory:'); c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE tags (id INTEGER PRIMARY KEY, name TEXT, color TEXT)")
    c.execute("CREATE TABLE file_tags (file_path TEXT, tag_id INTEGER)")
    c.execute("INSERT INTO tags VALUES (1,'favori','#f00'),(2,'dragon','#0f0')")
    paths = [f'/lib/m{i}.stl' for i in range(50000)]
    c.executemany("INSERT INTO file_tags VALUES (?,?)", [(paths[0], 1), (paths[49999], 1), (paths[49999], 2), (paths[30000], 2)])
    got = _helper()(c, paths)
    assert [t['name'] for t in got[paths[49999]]] == ['favori', 'dragon'] and len(got) == 3
    assert got[paths[0]][0]['color'] == '#f00' and paths[1] not in got
    assert _helper()(c, []) == {}


def test_plus_aucune_requete_in_non_decoupee_sur_la_liste_des_fichiers():
    src = open(os.path.join(ROOT, 'main.py'), encoding='utf-8').read()
    assert src.count("WHERE ft.file_path IN") == 1               # une seule requête, celle de l'aide découpée


def test_rendu_progressif_de_la_grille():
    js = open(os.path.join(ROOT, 'interface', 'script.js'), encoding='utf-8').read()
    assert 'LAZY_RENDER_AFTER = 1000' in js and 'armMoreSentinel' in js and 'files-more-sentinel' in js
    assert 'requestIdleCallback(() => renderChunk()' in js        # sinon l'IdleDeadline serait pris pour la taille du lot


def _analysis_ns(tmp_path):
    import hashlib, json, threading, time, atexit
    src = open(os.path.join(ROOT, 'main.py'), encoding='utf-8').read()
    wanted = {'_flush_analysis_pending', '_queue_analysis_for_cache', 'get_cached_3d_analysis'}
    names = {'_ANALYSIS_PENDING', '_ANALYSIS_PENDING_LOCK', '_analysis_flush_timer', '_analysis_json_memo'}
    chunks = []
    for n in ast.parse(src).body:
        if isinstance(n, ast.FunctionDef) and n.name in wanted:
            chunks.append(ast.get_source_segment(src, n))
        elif isinstance(n, ast.Assign) and any(getattr(t, 'id', '') in names for t in n.targets):
            chunks.append(ast.get_source_segment(src, n))
    db, calls = {}, []
    ns = dict(os=os, json=json, time=time, hashlib=hashlib, threading=threading, atexit=atexit,
              CACHE_FILE=str(tmp_path / 'cache.json'), cache_file_lock=threading.Lock(), _atomic_replace=os.replace,
              analysis_db_get=lambda p: (db.get(p), False), analysis_db_put=lambda p, m: db.__setitem__(p, m),
              analyze_3d_file=lambda p: calls.append(p) or {'volume_cm3': 2.0, 'dimensions': {'x': 1, 'y': 2, 'z': 3}, 'triangle_count': 4})
    exec('\n'.join(chunks), ns)
    return ns, db, calls


def test_analyse_en_cache_sans_reecrire_tout_le_fichier(tmp_path):
    ns, db, calls = _analysis_ns(tmp_path)
    open(ns['CACHE_FILE'], 'w').write('{"files": [], "timestamp": 1}')
    before = os.stat(ns['CACHE_FILE']).st_mtime_ns
    get = ns['get_cached_3d_analysis']
    for i in range(50):
        assert get(f'/lib/m{i}.stl')['volume_cm3'] == 2.0
    assert len(calls) == 50 and os.stat(ns['CACHE_FILE']).st_mtime_ns == before      # aucune réécriture pendant la rafale
    get('/lib/m3.stl'); assert len(calls) == 50                                      # relu depuis la base, pas recalculé
    ns['_flush_analysis_pending']()                                                  # puis une seule écriture groupée
    import json
    data = json.load(open(ns['CACHE_FILE']))
    assert data['files'] == [] and sum(1 for k in data if k.startswith('analysis_') and not k.endswith('_ts')) == 50


def test_compression_des_gros_json():
    import gzip, json
    flask = __import__('pytest').importorskip('flask')
    src = open(os.path.join(ROOT, 'main.py'), encoding='utf-8').read()
    ns = {'request': flask.request, 'GZIP_JSON_MIN_BYTES': 64 * 1024}
    for n in ast.parse(src).body:
        if isinstance(n, ast.FunctionDef) and n.name == '_gzip_big_json':
            n.decorator_list = []
            exec(ast.unparse(n), ns)
    app = flask.Flask('t')
    app.after_request(ns['_gzip_big_json'])
    big = [{'path': f'/lib/{i}.stl', 'name': f'm{i}.stl'} for i in range(5000)]
    app.add_url_rule('/big', 'big', lambda: flask.jsonify(big))
    app.add_url_rule('/small', 'small', lambda: flask.jsonify({'a': 1}))
    c = app.test_client()
    r = c.get('/big', headers={'Accept-Encoding': 'gzip'})
    assert r.headers.get('Content-Encoding') == 'gzip' and len(r.data) < 0.2 * len(json.dumps(big)) and json.loads(gzip.decompress(r.data)) == big
    assert int(r.headers['Content-Length']) == len(r.data)
    assert c.get('/big').headers.get('Content-Encoding') is None                        # navigateur sans gzip : inchangé
    assert c.get('/small', headers={'Accept-Encoding': 'gzip'}).headers.get('Content-Encoding') is None
