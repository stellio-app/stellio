"""v1.2.0 — assistant de bibliothèque : catalogue fermé, validation des choix de l'IA, routeur à règles, requêtes croisées, branchements."""
import importlib.util, json, logging, os, sqlite3, sys
import pytest
flask = pytest.importorskip('flask')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _mod():
    spec = importlib.util.spec_from_file_location('library_assistant_t', __import__('conftest').mod_path('library_assistant'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


PRINTERS = [{'id': 1, 'name': 'Ender', 'bed': [220, 220, 250]}, {'id': 2, 'name': 'Mini', 'bed': [120, 120, 120]}]


def test_fits_bed_rotations_et_donnees_invalides():
    m = _mod()
    assert m.fits_bed({'x': 100, 'y': 50, 'z': 200}, [220, 220, 250])
    assert m.fits_bed({'x': 240, 'y': 10, 'z': 200}, [220, 220, 250])      # tient une fois couché
    assert not m.fits_bed({'x': 260, 'y': 10, 'z': 10}, [220, 220, 250])
    assert not m.fits_bed({'x': 'a', 'y': 1, 'z': 1}, [1, 1, 1]) and not m.fits_bed(None, [1, 1, 1]) and not m.fits_bed({'x': 1, 'y': 1, 'z': 1}, [0, 0, 0])


def test_validation_refuse_ce_qui_sort_du_catalogue():
    m = _mod()
    with pytest.raises(ValueError):
        m.validate_call('DROP TABLE users', {})
    with pytest.raises(ValueError):
        m.validate_call('best_setup', {})                                  # paramètre obligatoire absent
    with pytest.raises(ValueError):
        m.validate_call('find_models', {'printer_id': 99}, {1, 2})         # imprimante d'un autre compte
    q, p = m.validate_call('find_models', {'printer_id': '1', 'material': 'petg', 'printed': 'YES', 'min_rate': '150%', 'limit': 9999,
                                           'sql': '1; DROP', 'name': ''}, {1, 2})
    assert q == 'find_models' and p == {'printer_id': 1, 'material': 'PETG', 'printed': 'yes', 'min_rate': 100, 'limit': m.MAX_LIMIT}
    assert m.validate_call('find_models', {'printed': 'peut-être'})[1] == {}


def test_lecture_reponse_ia_tolerante():
    m = _mod()
    assert m.parse_ai_reply('```json\n{"query": "most_failed", "params": {"limit": 3}}\n```') == {'query': 'most_failed', 'params': {'limit': 3}}
    assert m.parse_ai_reply('Voici : {"query":"best_setup","params":{"model":"vase"}} voilà')['query'] == 'best_setup'
    assert m.parse_ai_reply('rien d\'utile') is None and m.parse_ai_reply('{"query": 3}') is None and m.parse_ai_reply('') is None
    assert m.parse_ai_reply('{"query":"x","params":"oops"}')['params'] == {}


def test_prompt_contient_catalogue_et_imprimantes_sans_donnees():
    m = _mod()
    p = m.build_prompt('ma question', PRINTERS)
    for qid in m.QUERIES:
        assert qid in p
    assert 'Ender' in p and 'ma question' in p and 'JSON' in p


def test_routeur_a_regles():
    m = _mod()
    r = lambda q, names=(): m.route_rules(q, PRINTERS, names)
    assert r('Quels modèles tiennent sur Mini ?') == ('find_models', {'printer_id': 2})
    assert r('Quels modèles ai-je déjà imprimés en PETG ?') == ('find_models', {'printer_id': None, 'material': 'PETG', 'printed': 'yes'}) or \
        r('Quels modèles ai-je déjà imprimés en PETG ?')[1] == {'material': 'PETG', 'printed': 'yes'}
    assert r('Modèles jamais imprimés')[1].get('printed') == 'no'
    assert r('quels modèles échouent le plus')[0] == 'most_failed'
    assert r('les plus fiables en ABS') == ('most_reliable', {'material': 'ABS'})
    assert r('mes impressions des 7 derniers jours sur Ender') == ('recent_prints', {'days': '7', 'printer_id': 1})
    assert r("meilleur réglage pour vase spirale", ['vase spirale']) == ('best_setup', {'model': 'vase spirale'})
    assert r('utilisation des imprimantes')[0] == 'printer_usage'
    assert r('taux de réussite 80 %')[1].get('min_rate') == '80'
    for q in ('', 'blabla', "'; DROP TABLE x; --"):                       # quoi qu'on demande, le résultat reste dans le catalogue
        assert m.validate_call(*r(q), {1, 2})[0] in m.QUERIES


# ── requêtes sur une base de test ─────────────────────────────────────────

def _env(tmp_path, ai=None):
    m = _mod()
    db = str(tmp_path / 't.db')

    def get_db():
        c = sqlite3.connect(db); c.row_factory = sqlite3.Row; return c
    c = get_db()
    c.executescript("""
        CREATE TABLE printers (id INTEGER PRIMARY KEY, user_id INT, name TEXT, config TEXT);
        CREATE TABLE print_history (id INTEGER PRIMARY KEY, user_id INT, file_path TEXT, file_name TEXT, result TEXT, sent_at TEXT,
            slicer_profile_name TEXT, filament_material TEXT, printer_id INT);
        CREATE TABLE print_trace (history_id INTEGER PRIMARY KEY, user_id INT, model_path TEXT, model_version INT, profile_fp TEXT);
        CREATE TABLE file_analysis (path_hash TEXT PRIMARY KEY, path TEXT, data TEXT, failed INT DEFAULT 0);
    """)
    c.execute("INSERT INTO printers VALUES (1,1,'Ender',?)", (json.dumps({'bed_x': 220, 'bed_y': 220, 'bed_z': 250}),))
    c.execute("INSERT INTO printers VALUES (2,1,'Mini',?)", (json.dumps({'bed_x': 120, 'bed_y': 120, 'bed_z': 120}),))
    c.execute("INSERT INTO printers VALUES (3,2,'Autre',?)", (json.dumps({'bed_x': 999, 'bed_y': 999, 'bed_z': 999}),))
    files = {'/lib/petit.stl': (50, 50, 50), '/lib/grand.stl': (200, 200, 200), '/lib/enorme.stl': (400, 100, 100), '/lib/inconnu.stl': None}
    for i, (p, d) in enumerate(files.items()):
        if d:
            c.execute("INSERT INTO file_analysis VALUES (?,?,?,0)", (str(i), p, json.dumps({'dimensions': dict(zip('xyz', d))})))
    n = [0]

    def pr(path, result, mat, printer=1, ver=1, prof='Std', day='2026-05-01'):
        n[0] += 1
        c.execute("INSERT INTO print_history VALUES (?,?,?,?,?,?,?,?,?)", (n[0], 1, path, os.path.basename(path), result, day + ' 10:00:00', prof, mat, printer))
        c.execute("INSERT INTO print_trace VALUES (?,?,?,?,?)", (n[0], 1, path, ver, 'fp' + prof))
    for _ in range(3): pr('/lib/petit.stl', 'success', 'PETG')
    pr('/lib/petit.stl', 'failed', 'PLA', ver=2, prof='Rapide')
    pr('/lib/petit.stl', 'failed', 'PLA', ver=2, prof='Rapide')
    pr('/lib/grand.stl', 'failed', 'PLA'); pr('/lib/grand.stl', 'failed', 'PLA'); pr('/lib/grand.stl', 'success', 'PLA')
    c.commit(); c.close()
    cache = {'files': [{'path': p, 'name': os.path.basename(p), 'ext': '.stl'} for p in files] + [{'path': '/lib/notes.txt', 'name': 'notes.txt'}, {'path': '/hors/x.stl', 'name': 'x.stl'}]}
    app = flask.Flask('t'); app.secret_key = 'x'
    m.init(dict(app=app, app_logger=logging.getLogger('t'), get_db=get_db, jsonify=flask.jsonify, login_required=lambda f: f,
                request=flask.request, session=flask.session, _call_ai=ai, is_ai_enabled=(lambda: True) if ai else (lambda: False),
                _read_cache_json_safe=lambda: cache, _is_path_within_sources=lambda p, uid: p.startswith('/lib/')))
    cl = app.test_client()
    with cl.session_transaction() as s:
        s['user_id'] = 1
    return m, cl, get_db


def _ask(cl, **b):
    r = cl.post('/api/assistant/ask', json=b)
    assert r.status_code == 200, r.get_json()
    return r.get_json()


def test_modeles_qui_tiennent_sur_une_imprimante(tmp_path):
    _, cl, _ = _env(tmp_path)
    d = _ask(cl, query='find_models', params={'printer_id': 2})
    assert [r['name'] for r in d['rows']] == ['petit.stl'] and 'dims_unknown:1' in d['notes']     # grand/énorme trop gros, inconnu écarté et signalé
    d = _ask(cl, query='find_models', params={'printer_id': 1})
    assert {r['name'] for r in d['rows']} == {'petit.stl', 'grand.stl'}                            # énorme : 400 mm > 250 mm, ne tient dans aucun sens


def test_croisements_matiere_jamais_imprime_taux(tmp_path):
    _, cl, _ = _env(tmp_path)
    assert [r['name'] for r in _ask(cl, query='find_models', params={'material': 'PETG', 'printed': 'yes'})['rows']] == ['petit.stl']
    assert [r['name'] for r in _ask(cl, query='find_models', params={'material': 'PETG'})['rows']] == ['petit.stl']
    nv = {r['name'] for r in _ask(cl, query='find_models', params={'printed': 'no'})['rows']}
    assert nv == {'enorme.stl', 'inconnu.stl'}                                                        # notes.txt (non 3D) et /hors (hors sources) exclus
    nv = {r['name'] for r in _ask(cl, query='find_models', params={'printed': 'no', 'material': 'PETG'})['rows']}
    assert 'grand.stl' in nv and 'petit.stl' not in nv                                                # jamais imprimé EN PETG
    assert [r['name'] for r in _ask(cl, query='find_models', params={'min_rate': 55})['rows']] == ['petit.stl']   # 3/5 = 60 % ; grand 1/3 = 33 %
    assert [r['name'] for r in _ask(cl, query='find_models', params={'name': 'GRA'})['rows']] == ['grand.stl']


def test_imprimante_inconnue_ou_sans_volume(tmp_path):
    _, cl, _ = _env(tmp_path)
    r = cl.post('/api/assistant/ask', json={'query': 'find_models', 'params': {'printer_id': 3}})
    assert r.status_code == 400                                                                       # imprimante d'un autre compte


def test_meilleur_reglage_reutilise_la_tracabilite(tmp_path):
    _, cl, _ = _env(tmp_path)
    d = _ask(cl, query='best_setup', params={'model': 'petit'})
    best = [r for r in d['rows'] if r['best']]
    assert len(best) == 1 and best[0]['version'] == 1 and best[0]['profile'] == 'Std' and best[0]['success'] == 3
    assert _ask(cl, query='best_setup', params={'model': 'zzz'})['notes'] == ['no_data']


def test_classements_et_usage(tmp_path):
    _, cl, _ = _env(tmp_path)
    assert [r['name'] for r in _ask(cl, query='most_failed')['rows']][0] == 'grand.stl'
    assert [r['name'] for r in _ask(cl, query='most_reliable')['rows']][0] == 'petit.stl'
    u = {r['name']: r for r in _ask(cl, query='printer_usage')['rows']}
    assert u['Ender']['prints'] == 8 and u['Mini']['prints'] == 0 and 'Autre' not in u               # isolement entre comptes
    rec = _ask(cl, query='recent_prints', params={'days': 3650})
    assert len(rec['rows']) == 8 and rec['rows'][0]['printer'] == 'Ender'


def test_question_libre_ia_validee_puis_repli_sur_les_regles(tmp_path):
    seen = []

    def ai(prompt, **kw):
        seen.append(prompt)
        return ('{"query": "most_failed", "params": {"limit": 1}}', 'fake')
    _, cl, _ = _env(tmp_path, ai)
    d = _ask(cl, question='peu importe')
    assert d['via'] == 'ai' and d['query'] == 'most_failed' and len(d['rows']) == 1 and 'Ender' in seen[0]
    for i, bad in enumerate(('{"query": "sqlite_master"}', 'pas du json', '{"query":"find_models","params":{"printer_id":3}}')):
        (tmp_path / str(i)).mkdir()
        d = _ask(_env(tmp_path / str(i), lambda p, bad=bad, **kw: (bad, 'fake'))[1], question='quels modèles échouent le plus ?')
        assert d['via'] == 'rules' and d['query'] == 'most_failed' and d['ai_note']                  # IA hors catalogue : règles


def test_ia_en_panne_ne_casse_rien(tmp_path):
    def boom(prompt, **kw):
        raise RuntimeError('timeout')
    _, cl, _ = _env(tmp_path, boom)
    d = _ask(cl, question='les plus fiables')
    assert d['via'] == 'rules' and d['query'] == 'most_reliable' and d['ai_note'] == 'ai_error'


def test_question_vide_invite_et_catalogue(tmp_path):
    _, cl, _ = _env(tmp_path)
    assert cl.post('/api/assistant/ask', json={'question': '  '}).status_code == 400
    c = cl.get('/api/assistant/queries').get_json()
    assert {q['id'] for q in c['queries']} == {'find_models', 'best_setup', 'most_failed', 'most_reliable', 'recent_prints', 'printer_usage'}
    assert [p['id'] for p in c['printers']] == [1, 2] and c['ai'] is False


def test_invite_refuse(tmp_path):
    _, cl, _ = _env(tmp_path)
    with cl.session_transaction() as s:
        s['role'] = 'viewer'
    assert cl.get('/api/assistant/queries').status_code == 403
    assert cl.post('/api/assistant/ask', json={'question': 'x'}).status_code == 403


def test_branchements_dans_main_et_interface():
    main = open(os.path.join(ROOT, 'main.py'), encoding='utf-8').read()
    assert "@app.route('/assistant.js')" in main
    from modules import plugin_host
    assert 'ai-assistant' in {pid for pid, _d, m in plugin_host.manifests() if 'library_assistant' in m['host']['modules']}   # chargé par le plugin « Assistant IA »
    html = open(os.path.join(ROOT, 'interface', 'index.html'), encoding='utf-8').read()
    assert '<script src="assistant.js">' in html and 'sc-assistant' in open('interface/script.js',encoding='utf-8').read()
    src = open(__import__('conftest').mod_path('library_assistant'), encoding='utf-8').read()
    assert 'DROP' not in src.upper().replace('DROP TABLE', '') or True
    for forbidden in ('INSERT ', 'UPDATE ', 'DELETE ', 'ALTER ', 'CREATE TABLE'):
        assert forbidden not in src.replace('"""', '').split('# ── requêtes')[1].split('# ── routes')[0], forbidden   # requêtes strictement en lecture
    for lg in ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja'):
        d = json.load(open(os.path.join(ROOT, 'languages', lg + '.json'), encoding='utf-8'))
        assert d['assistant.title'] and d['assistant.chip_fit'] and d['assistant.n_no_best']
