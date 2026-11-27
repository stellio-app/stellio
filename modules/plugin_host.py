"""Stellio — plugins intégrés (1.1.7).

Un plugin intégré est une fonction de Stellio livrée DANS l'application (dossier `bundled_plugins/<id>/`, signé avec elle) mais
qui ne se charge que s'il est activé : ses routes, ses tâches de fond et ses dépendances n'existent pas tant qu'il est désactivé.
Il s'exécute dans le processus de Stellio (contrairement aux plugins Python tiers, isolés) ; c'est pourquoi seuls ceux livrés avec
l'application sont admis, SAUF une archive du catalogue (ou un .zip) dont la signature Ed25519 est valide pour une clé de confiance (1.2.0) :
c'est la seule exception, et elle est refusée dès qu'aucune clé n'est configurée. L'archive signée est conservée à part et revérifiée (signature,
empreinte, contenu du dossier) à CHAQUE lecture ; au moindre écart le plugin n'est ni listé ni chargé.

Manifeste `bundled_plugins/<id>/plugin.json` : champs habituels (id, name, version, description, author) +
  "host": {"modules": ["mqtt_publisher"],            # modules Python du dossier, dans l'ordre d'`init(globals())`
           "default_on": true,                       # facultatif : actif d'office, même sur une installation neuve (l'utilisateur peut le désactiver)
           "migrate": {"always": true}               # ou {"settings": [...], "settings_prefix": [...], "tables": [...], "dirs": [...], "printer_types": [...]}
           }
Migration invisible : au premier démarrage en 1.1.7 d'une installation existante, chaque plugin dont le manifeste reconnaît un usage
(réglage renseigné, table remplie, dossier non vide, imprimante d'un type géré) est activé SANS rien demander ; ses réglages
restent là où ils étaient (réglages globaux et base inchangés) : rien à ressaisir. Une installation neuve n'active rien.
L'activation ou la désactivation prend effet au redémarrage (les routes Flask ne se retirent pas à chaud).
"""
import importlib
import importlib.util
import types
import json
import os
import sys

_REQUIRED = (
    'DATA_DIR',
    'app',
    'app_logger',
    'get_db',
    'load_settings',
)
_ROUTES = ()          # les routes sont celles de plugins.py (/api/plugins/…) ; chaque plugin intégré enregistre les siennes dans son init()

BUNDLED_DIR = os.environ.get('STELLIO_BUNDLED_PLUGINS') or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bundled_plugins')
STATE_VERSION = 1

_MAIN = {}
_LOADED = {}        # id -> [modules Python initialisés]


def _say(level, msg):
    """Journalise sans jamais lever (le journal peut être factice dans les tests)."""
    try:
        getattr(_MAIN['app_logger'], level)(msg)
    except Exception:
        pass


def bundled_dirs():
    """[(id, dossier)] des plugins intégrés présents sur disque (ordre alphabétique)."""
    out = []
    try:
        for name in sorted(os.listdir(BUNDLED_DIR)):
            d = os.path.join(BUNDLED_DIR, name)
            if os.path.isfile(os.path.join(d, 'plugin.json')):
                out.append((name, d))
    except OSError:
        pass
    return out


def _plugins_root():
    base = _MAIN.get('DATA_DIR') or getattr(sys.modules.get('modules.plugin_security'), 'DATA_DIR', None) or '.'
    return os.path.join(base, 'plugins')


def _proof_dir():
    return os.path.join(_plugins_root(), '.host-proofs')


def _proof_paths(pid):
    return os.path.join(_proof_dir(), pid + '.zip'), os.path.join(_proof_dir(), pid + '.json')


def save_external_proof(pid, version, signature, data, unsigned=False):
    """Conserve l'archive (octets exacts) et sa signature : base de la revérification à chaque lecture.
    `unsigned` : archive NON signée, installée après acceptation explicite du risque (installation directe depuis un .zip) ; seule son intégrité est vérifiée."""
    import hashlib
    os.makedirs(_proof_dir(), exist_ok=True)
    zp, jp = _proof_paths(pid)
    with open(zp, 'wb') as f:
        f.write(data)
    with open(jp, 'w', encoding='utf-8') as f:
        json.dump({'id': pid, 'version': str(version), 'sha256': hashlib.sha256(data).hexdigest(), 'signature': str(signature or '').lower(), 'unsigned': bool(unsigned)}, f)


def drop_external_proof(pid):
    for p in _proof_paths(pid):
        try:
            os.remove(p)
        except OSError:
            pass
    _VERIFIED.pop(pid, None)


_VERIFIED = {}      # pid -> (empreinte des fichiers de preuve, résultat) : évite de relire l'archive à chaque appel de manifests()


def _zip_files(data):
    """{chemin relatif: sha256} des fichiers d'une archive de plugin (tolère un dossier racine unique, comme l'installation)."""
    import hashlib
    import io
    import zipfile
    zf = zipfile.ZipFile(io.BytesIO(data))
    infos = [i for i in zf.infolist() if not i.is_dir()]
    names = [i.filename.replace('\\', '/') for i in infos]
    prefix = ''
    if 'plugin.json' not in names:
        tops = {n.split('/', 1)[0] for n in names}
        if len(tops) == 1 and f"{list(tops)[0]}/plugin.json" in names:
            prefix = list(tops)[0] + '/'
    return {n[len(prefix):]: hashlib.sha256(zf.read(i)).hexdigest() for n, i in zip(names, infos)}


def _walk(d):
    """os.walk sans les dossiers `__pycache__` : le code d'un plugin signé n'est JAMAIS chargé depuis du bytecode (il est compilé depuis les sources
    vérifiées, voir load_enabled) ; ces dossiers ne comptent donc ni comme contenu de l'archive ni comme modification."""
    for r, ds, fs in os.walk(d):
        ds[:] = [x for x in ds if x != '__pycache__']
        yield r, ds, fs


def verify_external(pid, d):
    """(ok, raison) — le dossier `d` est EXACTEMENT le contenu de l'archive signée par une clé de confiance. Refus par défaut : sans clé
    de confiance configurée, sans preuve, ou au moindre écart, la réponse est non."""
    import hashlib
    zp, jp = _proof_paths(pid)
    try:
        sig_key = (os.path.getmtime(zp), os.path.getsize(zp), os.path.getmtime(jp))
        files_key = tuple(sorted((os.path.relpath(os.path.join(r, f), d), os.path.getmtime(os.path.join(r, f)), os.path.getsize(os.path.join(r, f)))
                                 for r, _ds, fs in _walk(d) for f in fs))
    except OSError:
        return False, 'preuve absente'
    from modules import plugin_security
    keys = plugin_security.trusted_keys()
    stamp = (sig_key, files_key, tuple(keys))
    hit = _VERIFIED.get(pid)
    if hit and hit[0] == stamp:
        return hit[1]
    res = (False, 'invalide')
    try:
        proof = json.load(open(jp, encoding='utf-8'))
        data = open(zp, 'rb').read()
        sha = hashlib.sha256(data).hexdigest()
        unsigned = proof.get('unsigned') is True
        if not keys and not unsigned:
            res = (False, 'aucune clé de confiance configurée')
        elif proof.get('id') != pid or proof.get('sha256') != sha:
            res = (False, 'archive modifiée')
        elif not unsigned and plugin_security.signature_status(proof.get('signature') or '', pid, proof.get('version') or '', sha, keys)['status'] != 'valid':
            res = (False, 'signature invalide')
        else:
            expected = _zip_files(data)
            actual = {os.path.relpath(os.path.join(r, f), d).replace(os.sep, '/'): hashlib.sha256(open(os.path.join(r, f), 'rb').read()).hexdigest()
                      for r, _ds, fs in _walk(d) for f in fs}
            res = (True, 'ok') if actual == expected else (False, 'fichiers modifiés après installation')
    except Exception:
        res = (False, 'preuve illisible')
    _VERIFIED[pid] = (stamp, res)
    return res


def external_dirs():
    """[(id, dossier)] des plugins signés installés depuis le catalogue (déclarant `host`), vérifiés."""
    out = []
    try:
        names = sorted(os.listdir(_plugins_root()))
    except OSError:
        return out
    bundled = {n for n, _d in bundled_dirs()}
    for name in names:
        d = os.path.join(_plugins_root(), name)
        if name.startswith('.') or name in bundled or not os.path.isfile(os.path.join(d, 'plugin.json')) or not os.path.isfile(_proof_paths(name)[1]):
            continue
        if verify_external(name, d)[0]:
            out.append((name, d))
    return out


def is_bundled(pid):
    return any(n == pid for n, _d in bundled_dirs())


def manifests():
    """[(id, dossier, manifeste)] des plugins intégrés valides, puis des plugins signés du catalogue (clé `_external`)."""
    out = []
    for pid, d in bundled_dirs() + external_dirs():
        try:
            m = json.load(open(os.path.join(d, 'plugin.json'), encoding='utf-8'))
        except (OSError, ValueError):
            continue
        h = m.get('host') if isinstance(m, dict) else None
        if m.get('id') != pid or not isinstance(h, dict) or not isinstance(h.get('modules'), list) or not h['modules']:
            continue
        if not all(isinstance(x, str) and x.isidentifier() for x in h['modules']):
            continue
        if not is_bundled(pid):
            m = dict(m, _external=True)
        out.append((pid, d, m))
    return out


def available(m):
    """Un plugin « server_only » (fournisseurs d'IA à clé d'API…) n'existe que dans l'édition serveur : jamais proposé, activé, migré ni chargé sous Windows."""
    return not (m or {}).get('server_only') or bool(_MAIN.get('IS_SERVER_EDITION', True))


def manifest(pid):
    for i, _d, m in manifests():
        if i == pid:
            return m
    return None


def _state_path(data_dir=None):
    d = os.path.join(data_dir or _MAIN.get('DATA_DIR') or '.', 'plugins')
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, '.host.json')


def read_state(data_dir=None):
    try:
        d = json.load(open(_state_path(data_dir), encoding='utf-8'))
        if isinstance(d, dict):
            d.setdefault('enabled', {})
            return d
    except (OSError, ValueError):
        pass
    return {'enabled': {}}


def write_state(st, data_dir=None):
    p = _state_path(data_dir)
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(st, f, indent=1)
    os.replace(tmp, p)


def _forced():
    """Variable d'environnement STELLIO_ENABLE_PLUGINS (tests, démo, essais) : « all » ou une liste d'identifiants séparés par des virgules."""
    v = (os.environ.get('STELLIO_ENABLE_PLUGINS') or '').strip().lower()
    if not v:
        return None
    return {pid for pid, _d, _m in manifests()} if v == 'all' else {x.strip() for x in v.split(',') if x.strip()}


def enabled_map(data_dir=None):
    en = dict(read_state(data_dir)['enabled'])
    for pid, _d, m in manifests():                       # « default_on » : actif d'office (installation neuve comprise) tant que l'utilisateur ne l'a pas désactivé lui-même
        if m['host'].get('default_on') and not m.get('_external') and pid not in en:
            en[pid] = True
    for pid in _forced() or ():
        en[pid] = True
    return en


def is_enabled(pid, data_dir=None):
    m = manifest(pid)
    return bool(enabled_map(data_dir).get(pid)) and (m is None or available(m))


def features(data_dir=None):
    """{id: activé} pour l'interface (masque les menus et sections des plugins absents)."""
    en = enabled_map(data_dir)
    return {pid: bool(en.get(pid)) and available(_m) for pid, _d, _m in manifests()}


def set_enabled(pid, value, data_dir=None):
    if manifest(pid) is None:
        raise KeyError(pid)
    if not available(manifest(pid)):
        raise PermissionError(pid)
    st = read_state(data_dir)
    st['enabled'][pid] = bool(value)
    write_state(st, data_dir)
    return {'enabled': bool(value), 'restart_required': bool(value) != (pid in _LOADED)}


def module(name):
    """Module d'un plugin intégré actif (None s'il n'est pas chargé) : à utiliser par le cœur pour les appels facultatifs."""
    for mods in _LOADED.values():
        for m in mods:
            if m.__name__.rsplit('.', 1)[-1] == name:
                return m
    return None


def loaded(pid):
    return pid in _LOADED


# ── migration invisible ───────────────────────────────────────────────────────────────────────────

def _val_in(val, want):
    wants = want if isinstance(want, list) else [want]
    return any((val in (None, '') if w is None else val == w) for w in wants)


def _used(rule, settings, conn, data_dir):
    """Vrai si le plugin était utilisé avant la 1.1.7 (selon les indices du manifeste)."""
    if not isinstance(rule, dict):
        return False
    if rule.get('always'):
        return True
    for k in rule.get('settings') or []:
        if settings.get(k) not in (None, '', False, 0, [], {}):
            return True
    for pre in rule.get('settings_prefix') or []:
        if any(str(k).startswith(pre) and v not in (None, '', False, 0, [], {}) for k, v in settings.items()):
            return True
    for cond in rule.get('settings_match') or []:               # [{réglage: valeur | [valeurs]}] : toutes les conditions d'un bloc, un bloc suffit (None = absent ou vide)
        if isinstance(cond, dict) and cond and all(_val_in(settings.get(k), v) for k, v in cond.items()):
            return True
    for t in rule.get('tables') or []:
        try:
            if t.isidentifier() and conn.execute(f"SELECT 1 FROM {t} LIMIT 1").fetchone():
                return True
        except Exception:
            pass
    for dn in rule.get('dirs') or []:
        p = os.path.join(data_dir or '', dn)
        try:
            if os.path.isdir(p) and any(os.scandir(p)):
                return True
        except OSError:
            pass
    for like in rule.get('printer_config_like') or []:          # réglage stocké dans la configuration JSON d'une imprimante
        try:
            if conn.execute("SELECT 1 FROM printers WHERE config LIKE ? LIMIT 1", (f"%{like}%",)).fetchone():
                return True
        except Exception:
            pass
    types = [t for t in rule.get('printer_types') or [] if isinstance(t, str)]
    if types:
        try:
            q = ','.join('?' * len(types))
            if conn.execute(f"SELECT 1 FROM printers WHERE type IN ({q}) LIMIT 1", types).fetchone():
                return True
        except Exception:
            pass
    return False


def migrate(settings, conn, data_dir, existing_install):
    """Première exécution (pas de `.host.json` migré) : active les plugins utilisés. Retourne la liste des ids activés."""
    st = read_state(data_dir)
    if st.get('migrated') == STATE_VERSION:
        return []
    done = []
    if existing_install:
        for pid, _d, m in manifests():
            if pid in st['enabled'] or not available(m):
                continue
            if not m.get('_external') and _used(m['host'].get('migrate'), settings or {}, conn, data_dir):
                st['enabled'][pid] = True
                done.append(pid)
    st['migrated'] = STATE_VERSION
    write_state(st, data_dir)
    return done


def existing_install(settings, conn):
    """Une installation « existante » a déjà un compte (toute installation d'avant la 1.1.7 en a un : la connexion est obligatoire) :
    on ne migre pas une installation neuve, où l'on choisit ce que l'on veut charger."""
    try:
        return bool(conn.execute("SELECT 1 FROM users LIMIT 1").fetchone())
    except Exception:
        return False


# ── chargement ────────────────────────────────────────────────────────────────────────────────────

_SENSITIVE = ('secret', 'password', 'passwd', 'credential', 'token', 'private_key', 'api_key', 'encrypt', 'decrypt')


def scoped_services(mod, ns, manifest=None):
    """Services réellement transmis à un plugin SIGNÉ du catalogue : uniquement ceux que son module déclare (_REQUIRED/_OPTIONAL/_OVERRIDABLE),
    sans jamais les noms sensibles (secrets, mots de passe, jetons, chiffrement) ; si le manifeste liste `host.services`, le module ne peut
    pas en demander davantage. Les plugins intégrés (livrés et signés avec Stellio) gardent l'accès complet."""
    names = tuple(getattr(mod, '_REQUIRED', ())) + tuple(getattr(mod, '_OPTIONAL', ())) + tuple(getattr(mod, '_OVERRIDABLE', ()))
    bad = [n for n in names if any(w in n.lower() for w in _SENSITIVE)]
    if bad:
        raise RuntimeError(f"services sensibles refusés : {bad}")
    allowed = ((manifest or {}).get('host') or {}).get('services')
    if allowed is not None:
        extra = [n for n in names if n not in allowed]
        if extra:
            raise RuntimeError(f"services non déclarés dans plugin.json (host.services) : {extra}")
    return {n: ns[n] for n in names if n in ns}


def load_enabled(ns):
    """Initialise (import + `init(globals())`) les plugins intégrés activés. Un plugin en échec est ignoré et journalisé."""
    _MAIN.update(ns)
    log = ns.get('app_logger')
    en = enabled_map(ns.get('DATA_DIR'))
    for pid, d, m in manifests():
        if not en.get(pid) or pid in _LOADED or not available(m):
            continue
        mods = []
        try:
            if d not in sys.path and not m.get('_external'):
                sys.path.append(d)
            for name in m['host']['modules']:
                if m.get('_external'):
                    if not verify_external(pid, d)[0]:          # revérification juste avant d'exécuter du code
                        raise RuntimeError('signature ou contenu invalide')
                    path = os.path.join(d, name + '.py')
                    src = open(path, 'rb').read()                     # compilé depuis les sources vérifiées : ni bytecode lu, ni bytecode écrit dans le dossier du plugin
                    modname = f"stellio_ext_{pid.replace('-', '_')}_{name}"
                    mod = types.ModuleType(modname)
                    mod.__file__ = path
                    sys.modules[modname] = mod
                    exec(compile(src, path, 'exec'), mod.__dict__)
                else:
                    mod = importlib.import_module('modules.' + name)
                if m.get('_external'):
                    given = scoped_services(mod, ns, m)
                    _say('info', f"[PLUGINS] « {pid} » reçoit {len(given)} service(s) : {', '.join(sorted(given))}")
                    r = mod.init(given)                  # plugin tiers : services déclarés seulement
                    if isinstance(r, dict):
                        for k, v in r.items():
                            if k not in ns:              # il peut ajouter des services, jamais remplacer ceux de l'application
                                ns[k] = v
                            else:
                                _say('warning', f"[PLUGINS] « {pid} » : remplacement du service « {k} » refusé")
                else:
                    r = mod.init(ns)
                    if isinstance(r, dict):
                        ns.update(r)
                mods.append(mod)
        except Exception as e:           # un plugin cassé ne doit pas empêcher Stellio de démarrer
            _say('error', f"[PLUGINS] plugin intégré « {pid} » non chargé : {e}")
            continue
        _LOADED[pid] = mods
        _say('info', f"[PLUGINS] plugin intégré « {pid} » chargé")
    return list(_LOADED)


def autostart():
    """Lance les tâches de fond des plugins chargés (fonction `autostart()` facultative de chaque module)."""
    log = _MAIN.get('app_logger')
    for pid, mods in _LOADED.items():
        for mod in mods:
            fn = getattr(mod, 'autostart', None)
            if callable(fn):
                try:
                    fn()
                except Exception as e:
                    _say('error', f"[PLUGINS] démarrage de « {pid} » : {e}")


def init(ns, routes=True):
    """Appelé par main.py avant le chargement : migration invisible, puis chargement des plugins activés."""
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"plugin_host.init : services manquants : {missing}")
    _MAIN.update(ns)
    _LOADED.clear()          # un démarrage = un état neuf (tests : plusieurs applications dans le même processus)
    try:
        conn = ns['get_db']()
        if conn is not None:
            try:
                settings = ns['load_settings']() or {}
                done = migrate(settings, conn, ns.get('DATA_DIR'), existing_install(settings, conn))
            finally:
                conn.close()
            if done:
                _say('info', f"[PLUGINS] migration 1.1.7 : plugins intégrés activés automatiquement : {', '.join(done)}")
    except Exception as e:
        _say('error', f"[PLUGINS] migration des plugins intégrés : {e}")
    load_enabled(ns)
    return {}
