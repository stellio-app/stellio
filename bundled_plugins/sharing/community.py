"""Stellio — partage communautaire par paquets `.stlpack` (1.1.7).

Un paquet est un zip : `manifest.json` (titre, auteur, LICENCE obligatoire, description, liste des fichiers avec taille et sha256) + `files/…`.
À l'import tout est vérifié : liste exacte des fichiers, empreintes, extensions autorisées, chemins sûrs, taille décompressée plafonnée,
jamais d'écrasement (un fichier existant garde son nom, le nouveau est suffixé). Rien n'est exécuté, rien n'est téléchargé tout seul.
« Communauté » = vos instances appairées : un pair expose la liste de ses paquets visibles ; vous récupérez un paquet dans votre étagère,
puis vous l'importez quand vous le décidez. Aucun serveur central. Modération par le propriétaire : signalements, masquage (un paquet masqué
n'est plus proposé aux pairs ni aux invités), suppression ; au bout de 3 signalements un paquet est masqué automatiquement.
"""
import hashlib
import io
import json
import os
import re
import shutil
import time
import zipfile

_REQUIRED = (
    'DATA_DIR',
    '_is_path_within_sources',
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'require_peer_key',
    'session',
)
_OPTIONAL = ('send_file', '_get_primary_user_id')
_OVERRIDABLE = ('os', 'time')

_MAIN = {}
DATA_DIR = None
_is_path_within_sources = None
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
require_peer_key = None
session = None
send_file = None
_get_primary_user_id = None

FORMAT = 1
LICENSES = ('CC0-1.0', 'CC-BY-4.0', 'CC-BY-SA-4.0', 'CC-BY-NC-4.0', 'CC-BY-NC-SA-4.0', 'CC-BY-ND-4.0', 'CC-BY-NC-ND-4.0', 'MIT', 'Personnel')
ALLOWED_EXT = ('.stl', '.obj', '.3mf', '.ply', '.off', '.step', '.stp', '.gcode', '.png', '.jpg', '.jpeg', '.webp', '.txt', '.md', '.pdf', '.json')
MAX_FILES = 200
MAX_TOTAL = 500 * 1024 * 1024
MAX_PACK = 300 * 1024 * 1024
REPORT_HIDE = 3
_ID = re.compile(r'^[0-9a-f]{16}$')


def _shelf():
    d = os.path.join(DATA_DIR, 'community')
    os.makedirs(d, exist_ok=True)
    return d


def safe_name(name):
    n = str(name or '').replace('\\', '/')
    parts = n.split('/')
    if not n or n.startswith('/') or any(p in ('', '.', '..') for p in parts) or ':' in parts[0]:
        raise ValueError(f'Nom de fichier refusé : {name!r}')
    if not n.lower().endswith(ALLOWED_EXT):
        raise ValueError(f'Type de fichier non autorisé : {name!r}')
    return n


def _slug(s):
    s = re.sub(r'[^\w\- ]+', '', str(s or ''), flags=re.UNICODE).strip().replace(' ', '-')
    return (s or 'paquet')[:60]


def _sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ── construction / lecture d'un paquet (fonctions pures) ──
def build_pack(files, title, license_id, author='', description='', now=None, remix_of=None):
    """files : [(chemin_disque, nom_dans_le_paquet)] → octets du zip. Refuse une licence absente ou inconnue."""
    if license_id not in LICENSES:
        raise ValueError('Licence obligatoire (' + ', '.join(LICENSES) + ').')
    title = str(title or '').strip()[:120]
    if not title:
        raise ValueError('Titre obligatoire.')
    if not files or len(files) > MAX_FILES:
        raise ValueError(f'Entre 1 et {MAX_FILES} fichiers.')
    entries, seen, total = [], set(), 0
    for path, name in files:
        name = safe_name(name)
        if name.lower() in seen:
            raise ValueError(f'Nom en double : {name}')
        seen.add(name.lower())
        size = os.path.getsize(path)
        total += size
        if total > MAX_TOTAL:
            raise ValueError('Paquet trop volumineux.')
        entries.append({'name': name, 'size': size, 'sha256': _sha(path)})
    manifest = {'format': FORMAT, 'title': title, 'author': str(author or '')[:80], 'license': license_id, 'description': str(description or '')[:2000],
                'created': int(now if now is not None else time.time()), 'files': entries}
    if remix_of:
        manifest['remix_of'] = clean_remix(remix_of)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=1))
        for (path, _), e in zip(files, entries):
            z.write(path, 'files/' + e['name'])
    return buf.getvalue()


def read_pack(blob):
    """Valide le paquet SANS rien écrire. Retourne le manifeste ; ValueError au moindre écart."""
    if len(blob) > MAX_PACK:
        raise ValueError('Paquet trop volumineux.')
    try:
        z = zipfile.ZipFile(io.BytesIO(blob))
    except zipfile.BadZipFile:
        raise ValueError('Paquet illisible.')
    names = z.namelist()
    if 'manifest.json' not in names:
        raise ValueError('Manifeste absent.')
    try:
        man = json.loads(z.read('manifest.json').decode('utf-8'))
    except Exception:
        raise ValueError('Manifeste invalide.')
    if not isinstance(man, dict) or man.get('format') != FORMAT:
        raise ValueError('Format de paquet non pris en charge.')
    if man.get('license') not in LICENSES:
        raise ValueError('Licence absente ou inconnue : paquet refusé.')
    files = man.get('files')
    if not isinstance(files, list) or not files or len(files) > MAX_FILES:
        raise ValueError('Liste de fichiers invalide.')
    expected, total = {}, 0
    for e in files:
        if not isinstance(e, dict):
            raise ValueError('Liste de fichiers invalide.')
        n = safe_name(e.get('name'))
        if n in expected:
            raise ValueError('Nom en double.')
        expected[n] = e
        total += int(e.get('size', 0))
    if total > MAX_TOTAL:
        raise ValueError('Paquet trop volumineux une fois décompressé.')
    actual = {i.filename: i for i in z.infolist() if i.filename != 'manifest.json' and not i.filename.endswith('/')}
    if set(actual) != {'files/' + n for n in expected}:
        raise ValueError('Contenu différent du manifeste.')
    for n, e in expected.items():
        info = actual['files/' + n]
        if (info.external_attr >> 16) & 0o170000 == 0o120000:
            raise ValueError('Lien symbolique refusé.')
        if info.file_size != int(e.get('size', -1)):
            raise ValueError(f'Taille inattendue : {n}')
        h = hashlib.sha256()
        with z.open(info) as f:                                  # lecture bornée : on ne fait pas confiance à la taille déclarée
            read = 0
            for chunk in iter(lambda: f.read(1 << 20), b''):
                read += len(chunk)
                if read > info.file_size:
                    raise ValueError(f'Taille inattendue : {n}')
                h.update(chunk)
        if h.hexdigest() != e.get('sha256'):
            raise ValueError(f'Empreinte incorrecte : {n}')
    return man


def extract_pack(blob, dest):
    """Valide puis écrit dans dest (créé). Un fichier existant n'est jamais écrasé. Retourne [chemins écrits]."""
    man = read_pack(blob)
    z = zipfile.ZipFile(io.BytesIO(blob))
    base = os.path.realpath(dest)
    os.makedirs(base, exist_ok=True)
    written = []
    for e in man['files']:
        n = safe_name(e['name'])
        target = os.path.realpath(os.path.join(base, *n.split('/')))
        if not target.startswith(base + os.sep):
            raise ValueError('Chemin hors du dossier.')
        os.makedirs(os.path.dirname(target), exist_ok=True)
        root, ext = os.path.splitext(target)
        i = 1
        while os.path.exists(target):
            target = f'{root} ({i}){ext}'
            i += 1
        with z.open('files/' + n) as src, open(target, 'wb') as out:
            shutil.copyfileobj(src, out)
        written.append(target)
    with open(os.path.join(base, 'STELLIO-PACK.json'), 'w', encoding='utf-8') as f:
        json.dump({k: man[k] for k in ('title', 'author', 'license', 'description', 'created')}, f, ensure_ascii=False, indent=1)
    return written



# ── remix : filiation et compatibilité de licence ──
def clean_remix(r):
    """Filiation déclarée d'un paquet : {id, title, author, license} nettoyé (déclaratif, non signé)."""
    r = r if isinstance(r, dict) else {}
    pid = str(r.get('id') or '')
    return {'id': pid if _ID.match(pid) else '', 'title': str(r.get('title') or '')[:120], 'author': str(r.get('author') or '')[:80],
            'license': r.get('license') if r.get('license') in LICENSES else ''}


def remix_allowed(parent_license, new_license):
    """(ok, raison). Garde-fou simple, pas un avis juridique : ND et « Personnel » interdisent le remix ; SA impose la même licence ; NC impose NC."""
    if parent_license not in LICENSES or new_license not in LICENSES:
        return False, 'Licence inconnue.'
    if parent_license == 'Personnel':
        return False, "Le paquet d'origine est sous licence « Personnel » : remix interdit."
    if 'ND' in parent_license.split('-'):
        return False, "Le paquet d'origine interdit les œuvres dérivées (ND) : remix interdit."
    if 'SA' in parent_license.split('-') and new_license != parent_license:
        return False, f"Le paquet d'origine impose le partage dans les mêmes conditions : le remix doit rester en {parent_license}."
    if 'NC' in parent_license.split('-') and 'NC' not in new_license.split('-'):
        return False, "Le paquet d'origine interdit l'usage commercial (NC) : le remix doit rester NC."
    return True, ''


def lineage(pid, depth=10):
    """Ancêtres connus localement d'un paquet (du parent direct vers la racine), sans boucle."""
    out, seen = [], {pid}
    cur = _load_meta(pid)
    while cur and cur.get('remix_of') and len(out) < depth:
        r = cur['remix_of']
        out.append(r)
        nxt = r.get('id')
        if not nxt or nxt in seen:
            break
        seen.add(nxt)
        cur = _load_meta(nxt)
    return out


# ── étagère locale ──
def _meta_path(pid):
    return os.path.join(_shelf(), pid, 'meta.json')


def _load_meta(pid):
    if not _ID.match(str(pid)):
        return None
    try:
        with open(_meta_path(pid), encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def _save_meta(pid, meta):
    with open(_meta_path(pid), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)


def store_pack(blob, origin='local'):
    man = read_pack(blob)
    pid = hashlib.sha256(blob).hexdigest()[:16]
    d = os.path.join(_shelf(), pid)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'pack.stlpack'), 'wb') as f:
        f.write(blob)
    meta = _load_meta(pid) or {'reports': [], 'hidden': False, 'added': int(time.time()), 'comments': [], 'favorites': []}
    meta.setdefault('comments', []); meta.setdefault('favorites', [])
    if man.get('remix_of'):
        meta['remix_of'] = clean_remix(man['remix_of'])
    meta.update({'id': pid, 'title': man['title'], 'author': man['author'], 'license': man['license'], 'description': man['description'],
                 'files': len(man['files']), 'size': sum(int(e['size']) for e in man['files']), 'origin': origin})
    _save_meta(pid, meta)
    return meta


def list_packs(include_hidden=False):
    out = []
    try:
        ids = sorted(os.listdir(_shelf()))
    except OSError:
        ids = []
    for pid in ids:
        m = _load_meta(pid)
        if m and (include_hidden or not m.get('hidden')):
            out.append({k: m.get(k) for k in ('id', 'title', 'author', 'license', 'description', 'files', 'size', 'origin', 'hidden')} |
                       {'reports': len(m.get('reports', [])), 'comments': len(m.get('comments', [])), 'favorites': len(m.get('favorites', [])), 'remix_of': m.get('remix_of')})
    return out


def report(pid, reason, who='', hide_at=REPORT_HIDE):
    m = _load_meta(pid)
    if not m:
        return None
    if who and any(r.get('who') == who for r in m['reports']):
        return m                                             # un seul signalement par personne
    m['reports'].append({'who': who, 'reason': str(reason or '')[:300], 'at': int(time.time())})
    if len(m['reports']) >= hide_at:
        m['hidden'] = True
    _save_meta(pid, m)
    return m


# ── routes ──
def _is_owner():
    return session.get('role') != 'viewer' and bool(session.get('user_id'))


def _deny():
    return jsonify({'error': 'Accès refusé.'}), 403


def api_community_packs():
    owner = _is_owner()
    return jsonify({'ok': True, 'licenses': list(LICENSES), 'packs': list_packs(include_hidden=owner), 'owner': owner})


def api_community_publish():
    if not _is_owner():
        return _deny()
    d = request.get_json(silent=True) or {}
    paths = d.get('paths')
    if not isinstance(paths, list) or not paths:
        return jsonify({'error': 'Aucun fichier.'}), 400
    files, used = [], set()
    try:
        for p in paths:
            rp = os.path.realpath(str(p))
            if not os.path.isfile(rp):
                raise ValueError(f'Fichier introuvable : {os.path.basename(rp)}')
            if not _is_path_within_sources(rp, session['user_id']):
                return _deny()
            name, i = os.path.basename(rp), 1
            while name.lower() in used:
                r, e = os.path.splitext(os.path.basename(rp))
                name, i = f'{r} ({i}){e}', i + 1
            used.add(name.lower())
            files.append((rp, name))
        remix = None
        if d.get('remix_of'):
            parent = _load_meta(str(d['remix_of']))
            if not parent:
                raise ValueError("Paquet d'origine introuvable sur cette étagère.")
            ok, why = remix_allowed(parent.get('license'), d.get('license'))
            if not ok:
                raise ValueError(why)
            remix = {'id': parent['id'], 'title': parent.get('title'), 'author': parent.get('author'), 'license': parent.get('license')}
        blob = build_pack(files, d.get('title'), d.get('license'), d.get('author') or '', d.get('description') or '', remix_of=remix)
        meta = store_pack(blob)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        app_logger.warning('community publish: %s', e)
        return jsonify({'error': 'Publication impossible.'}), 500
    return jsonify({'ok': True, 'pack': meta})


def api_community_import():
    """Importe un paquet de l'étagère (JSON {pack_id, dest}) ou téléversé (multipart `file` + `dest`)."""
    if not _is_owner():
        return _deny()
    try:
        if request.files.get('file'):
            blob, dest = request.files['file'].read(MAX_PACK + 1), request.form.get('dest', '')
            origin = 'upload'
        else:
            d = request.get_json(silent=True) or {}
            pid, dest = d.get('pack_id'), d.get('dest', '')
            if not _load_meta(pid):
                return jsonify({'error': 'Paquet introuvable.'}), 404
            with open(os.path.join(_shelf(), pid, 'pack.stlpack'), 'rb') as f:
                blob = f.read()
            origin = pid
        dest = os.path.realpath(str(dest))
        if not dest or not _is_path_within_sources(dest, session['user_id']):
            return jsonify({'error': 'Dossier de destination hors des sources.'}), 403
        man = read_pack(blob)
        target = os.path.join(dest, _slug(man['title']))
        written = extract_pack(blob, target)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        app_logger.warning('community import: %s', e)
        return jsonify({'error': 'Import impossible.'}), 500
    return jsonify({'ok': True, 'folder': target, 'files': len(written), 'license': man['license'], 'origin': origin})


def api_community_report(pack_id):
    m = _load_meta(pack_id)
    if not m or (m.get('hidden') and not _is_owner()):
        return jsonify({'error': 'Paquet introuvable.'}), 404
    who = f"u{session.get('user_id')}" if session.get('user_id') else f"v{session.get('viewer_id', '')}"
    r = report(pack_id, (request.get_json(silent=True) or {}).get('reason', ''), who)
    return jsonify({'ok': True, 'hidden': bool(r.get('hidden')), 'reports': len(r['reports'])})


def api_community_moderate(pack_id):
    if not _is_owner():
        return _deny()
    m = _load_meta(pack_id)
    if not m:
        return jsonify({'error': 'Paquet introuvable.'}), 404
    action = (request.get_json(silent=True) or {}).get('action')
    if action == 'hide':
        m['hidden'] = True
    elif action == 'unhide':
        m['hidden'] = False
        m['reports'] = []
    elif action == 'delete':
        shutil.rmtree(os.path.join(_shelf(), pack_id), ignore_errors=True)
        return jsonify({'ok': True, 'deleted': True})
    else:
        return jsonify({'error': 'Action inconnue.'}), 400
    _save_meta(pack_id, m)
    return jsonify({'ok': True, 'hidden': m['hidden']})


MAX_COMMENTS = 200


def _who():
    return f"u{session.get('user_id')}" if session.get('user_id') else ''


def api_community_comments(pack_id):
    """GET : lire les commentaires (les invités peuvent lire un paquet visible). POST : commenter (propriétaire). Locaux à cette instance."""
    m = _load_meta(pack_id)
    if not m or (m.get('hidden') and not _is_owner()):
        return jsonify({'error': 'Paquet introuvable.'}), 404
    if request.method == 'GET':
        return jsonify({'ok': True, 'comments': m.get('comments', []), 'favorites': len(m.get('favorites', [])),
                        'favorite': _who() in m.get('favorites', []), 'lineage': lineage(pack_id)})
    if not _is_owner():
        return _deny()
    text = str((request.get_json(silent=True) or {}).get('text') or '').strip()[:1000]
    if not text:
        return jsonify({'error': 'Commentaire vide.'}), 400
    cs = m.setdefault('comments', [])
    if len(cs) >= MAX_COMMENTS:
        return jsonify({'error': 'Trop de commentaires sur ce paquet.'}), 400
    c = {'id': (max([x['id'] for x in cs]) + 1) if cs else 1, 'who': _who(), 'text': text, 'at': int(time.time())}
    cs.append(c)
    _save_meta(pack_id, m)
    return jsonify({'ok': True, 'comment': c}), 201


def api_community_comment_delete(pack_id, cid):
    if not _is_owner():
        return _deny()
    m = _load_meta(pack_id)
    if not m:
        return jsonify({'error': 'Paquet introuvable.'}), 404
    n = len(m.get('comments', []))
    m['comments'] = [c for c in m.get('comments', []) if c['id'] != cid]
    if len(m['comments']) == n:
        return jsonify({'error': 'Commentaire introuvable.'}), 404
    _save_meta(pack_id, m)
    return jsonify({'ok': True})


def api_community_favorite(pack_id):
    """Bascule le favori de ce compte (propriétaire)."""
    if not _is_owner():
        return _deny()
    m = _load_meta(pack_id)
    if not m:
        return jsonify({'error': 'Paquet introuvable.'}), 404
    favs, me = m.setdefault('favorites', []), _who()
    on = me not in favs
    if on:
        favs.append(me)
    else:
        favs.remove(me)
    _save_meta(pack_id, m)
    return jsonify({'ok': True, 'favorite': on, 'favorites': len(favs)})


def api_peer_community_list():
    return jsonify({'ok': True, 'packs': list_packs(include_hidden=False)})


def api_peer_community_bundle(pack_id):
    m = _load_meta(pack_id)
    if not m or m.get('hidden'):
        return jsonify({'error': 'Paquet introuvable.'}), 404
    return send_file(os.path.join(_shelf(), pack_id, 'pack.stlpack'), mimetype='application/zip', as_attachment=True, download_name=f'{pack_id}.stlpack')


def _peer(instance_id):
    uid = _get_primary_user_id() if _get_primary_user_id else session.get('user_id')
    c = get_db()
    try:
        return c.execute('SELECT url, peer_key FROM remote_instances WHERE id=? AND user_id=?', (instance_id, uid)).fetchone()
    finally:
        c.close()


def _http():
    import requests
    return requests


def api_community_remote():
    """Liste (GET ?instance_id=) ou récupération (POST {instance_id, pack_id}) de paquets d'une instance appairée."""
    if not _is_owner():
        return _deny()
    d = request.get_json(silent=True) or {} if request.method == 'POST' else request.args
    try:
        row = _peer(int(d.get('instance_id') or 0))
    except (TypeError, ValueError):
        row = None
    if not row:
        return jsonify({'error': 'Instance introuvable.'}), 404
    base, hdr = str(row['url']).rstrip('/'), {'X-Stellio-Peer-Key': row['peer_key']}
    try:
        if request.method == 'GET':
            r = _http().get(base + '/api/peer/community/list', headers=hdr, timeout=15)
            if r.status_code != 200:
                return jsonify({'error': 'Réponse du pair : %s' % r.status_code}), 502
            return jsonify({'ok': True, 'packs': (r.json() or {}).get('packs', [])})
        pid = str(d.get('pack_id') or '')
        if not _ID.match(pid):
            return jsonify({'error': 'Identifiant invalide.'}), 400
        r = _http().get(f'{base}/api/peer/community/{pid}/bundle', headers=hdr, timeout=60, stream=True)
        if r.status_code != 200:
            return jsonify({'error': 'Réponse du pair : %s' % r.status_code}), 502
        buf, size = io.BytesIO(), 0
        for chunk in r.iter_content(1 << 20):
            size += len(chunk)
            if size > MAX_PACK:
                return jsonify({'error': 'Paquet trop volumineux.'}), 400
            buf.write(chunk)
        meta = store_pack(buf.getvalue(), origin=f"instance {d.get('instance_id')}")          # validé avant d'entrer dans l'étagère
    except ValueError as e:
        return jsonify({'error': 'Paquet refusé : %s' % e}), 400
    except Exception as e:
        app_logger.warning('community remote: %s', e)
        return jsonify({'error': 'Instance injoignable.'}), 502
    return jsonify({'ok': True, 'pack': meta})


_ROUTES = (
    ('/api/community/packs', ['GET'], 'api_community_packs', ('login_required', )),
    ('/api/community/publish', ['POST'], 'api_community_publish', ('login_required', )),
    ('/api/community/import', ['POST'], 'api_community_import', ('login_required', )),
    ('/api/community/<pack_id>/report', ['POST'], 'api_community_report', ('login_required', )),
    ('/api/community/<pack_id>/moderate', ['POST'], 'api_community_moderate', ('login_required', )),
    ('/api/community/<pack_id>/comments', ['GET', 'POST'], 'api_community_comments', ('login_required', )),
    ('/api/community/<pack_id>/comments/<int:cid>', ['DELETE'], 'api_community_comment_delete', ('login_required', )),
    ('/api/community/<pack_id>/favorite', ['POST'], 'api_community_favorite', ('login_required', )),
    ('/api/community/remote', ['GET', 'POST'], 'api_community_remote', ('login_required', )),
    ('/api/peer/community/list', ['GET'], 'api_peer_community_list', ('require_peer_key', )),
    ('/api/peer/community/<pack_id>/bundle', ['GET'], 'api_peer_community_bundle', ('require_peer_key', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"{__name__}.init : services manquants : {missing}")
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
