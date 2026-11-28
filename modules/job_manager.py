"""Stellio — gestionnaire central des tâches de fond (1.1.7).

Une seule file pour les traitements longs (analyses, index de formes, comparaisons 3D, synchronisation…) : états visibles
(en attente, en cours, en pause, terminée, en échec, annulée), nombre de tâches simultanées borné, annulation et pause
coopératives (la tâche appelle `ctx.check()` aux endroits où elle peut s'arrêter), journal des dernières tâches.
Les tâches vivent en mémoire : un redémarrage de Stellio les efface (elles sont relancées par leur fonction d'origine).
Les autres modules soumettent leur travail avec `submit(...)` ; l'interface lit `/api/jobs`.
"""
import threading
import time
import uuid

_REQUIRED = (
    'app',
    'app_logger',
    'jsonify',
    'login_required',
    'request',
    'session',
)
_OPTIONAL = ()
_OVERRIDABLE = ()

_MAIN = {}
app = None
app_logger = None
jsonify = None
login_required = None
request = None
session = None

STATES = ('queued', 'running', 'paused', 'done', 'failed', 'cancelled')
FINAL = ('done', 'failed', 'cancelled')
MAX_WORKERS = 2
KEEP_FINISHED = 100


_TL = threading.local()


def job_check():
    """Point d'annulation pour le code appelé depuis une tâche (ex. vue de plugin lancée en asynchrone) : lève Cancelled si la tâche
    a été annulée ; sans effet hors tâche."""
    c = getattr(_TL, 'ctx', None)
    if c is not None:
        c.check()


class Cancelled(Exception):
    """Levée par `ctx.check()` quand la tâche a été annulée."""


class JobContext:
    def __init__(self, job):
        self._job = job

    def check(self):
        """À appeler régulièrement : s'arrête si annulée, attend si en pause."""
        j = self._job
        while True:
            if j.cancel_requested:
                raise Cancelled()
            if not j.pause_requested:
                return
            j.set_state('paused')
            time.sleep(0.05)
        # (reprise : set_state('running') est refait par le worker)

    def progress(self, done, total=None, message=None):
        self._job.progress = {'done': done, 'total': total, 'message': message}
        self.check()
        if self._job.state == 'paused':
            self._job.set_state('running')


class Job:
    def __init__(self, name, fn, owner, kind='generic', args=(), kwargs=None):
        self.id = uuid.uuid4().hex[:12]
        self.name, self.kind, self.owner = str(name)[:120], str(kind)[:40], owner
        self.fn, self.args, self.kwargs = fn, args, kwargs or {}
        self.state = 'queued'
        self.created = time.time()
        self.started = self.finished = None
        self.progress = {'done': 0, 'total': None, 'message': None}
        self.result = None
        self.error = ''
        self.cancel_requested = False
        self.pause_requested = False
        self._lock = threading.Lock()

    def set_state(self, state):
        with self._lock:
            if self.state in FINAL:
                return
            self.state = state

    def public(self, with_result=False):
        d = {'id': self.id, 'name': self.name, 'kind': self.kind, 'state': self.state, 'created': self.created,
             'started': self.started, 'finished': self.finished, 'progress': self.progress, 'error': self.error}
        if with_result:
            d['result'] = self.result
        return d


class JobManager:
    def __init__(self, workers=MAX_WORKERS, keep=KEEP_FINISHED, autostart=True):
        self.workers, self.keep, self.autostart = workers, keep, autostart
        self._jobs = {}
        self._order = []
        self._lock = threading.RLock()
        self._running = 0

    # -- soumission et exécution --
    def submit(self, name, fn, owner=None, kind='generic', args=(), kwargs=None):
        job = Job(name, fn, owner, kind, args, kwargs)
        with self._lock:
            self._jobs[job.id] = job
            self._order.append(job.id)
            self._trim()
        if self.autostart:
            self._pump()
        return job

    def _trim(self):
        finished = [i for i in self._order if self._jobs[i].state in FINAL]
        for i in finished[:max(0, len(finished) - self.keep)]:
            self._order.remove(i)
            self._jobs.pop(i, None)

    def _pump(self):
        with self._lock:
            while self._running < self.workers:
                nxt = next((self._jobs[i] for i in self._order if self._jobs[i].state == 'queued'), None)
                if nxt is None:
                    return
                nxt.state = 'running'
                self._running += 1
                threading.Thread(target=self._run, args=(nxt,), daemon=True).start()

    def _run(self, job):
        job.started = time.time()
        try:
            if job.cancel_requested:
                raise Cancelled()
            _TL.ctx = JobContext(job)
            try:
                job.result = job.fn(_TL.ctx, *job.args, **job.kwargs)
            finally:
                _TL.ctx = None
            job.set_state('done')
        except Cancelled:
            job.set_state('cancelled')
        except Exception as e:     # une tâche en échec ne doit jamais faire tomber les autres
            job.error = f"{type(e).__name__}: {e}"[:300]
            job.set_state('failed')
        finally:
            job.finished = time.time()
            with self._lock:
                self._running -= 1
            if self.autostart:           # sans cela, un gestionnaire « manuel » (tests) lançait quand même des fils en cascade
                self._pump()

    def run_pending_inline(self):
        """Pour les tests (autostart=False) : exécute les tâches en attente dans l'ordre, sans thread."""
        while True:
            with self._lock:
                nxt = next((self._jobs[i] for i in self._order if self._jobs[i].state == 'queued'), None)
                if nxt is None:
                    return
                nxt.state = 'running'
                self._running += 1
            self._run(nxt)

    # -- contrôle --
    def get(self, job_id):
        return self._jobs.get(job_id)

    def list(self, owner=None):
        with self._lock:
            return [self._jobs[i].public() for i in reversed(self._order) if owner is None or self._jobs[i].owner == owner]

    def cancel(self, job_id, owner=None):
        j = self._jobs.get(job_id)
        if not j or (owner is not None and j.owner != owner) or j.state in FINAL:
            return False
        j.cancel_requested = True
        if j.state == 'queued':
            j.set_state('cancelled')
            j.finished = time.time()
        return True

    def pause(self, job_id, owner=None):
        j = self._jobs.get(job_id)
        if not j or (owner is not None and j.owner != owner) or j.state in FINAL:
            return False
        j.pause_requested = True
        return True

    def resume(self, job_id, owner=None):
        j = self._jobs.get(job_id)
        if not j or (owner is not None and j.owner != owner) or j.state in FINAL:
            return False
        j.pause_requested = False
        if j.state == 'paused':
            j.state = 'running'
        return True

    def summary(self, owner=None):
        out = {s: 0 for s in STATES}
        for j in self.list(owner):
            out[j['state']] += 1
        return out


MANAGER = JobManager()


def submit(name, fn, owner=None, kind='generic', args=(), kwargs=None):
    return MANAGER.submit(name, fn, owner, kind, args, kwargs)


def run_view_async(name, view, kind='plugin'):
    """Exécute une vue Flask (POST JSON) en tâche de fond : répond 202 {job_id} tout de suite ; état et résultat
    ({status, body}) se lisent sur /api/jobs/<id>. Utilisé par les plugins pour les traitements lourds (découpes, exports, calculs de maillage).
    La session (utilisateur, rôle) de la requête d'origine est rejouée dans la tâche ; le drapeau « async » est retiré du corps."""
    body = dict(request.get_json(silent=True) or {})
    body.pop('async', None)
    uid, role, path, args = session.get('user_id'), session.get('role'), request.path, request.args.to_dict()
    flask_app = _MAIN.get('app') or app

    def work(ctx):
        with flask_app.test_request_context(path, method='POST', json=body, query_string=args):
            session['user_id'] = uid
            if role:
                session['role'] = role
            resp = flask_app.make_response(view())
            return {'status': resp.status_code, 'body': resp.get_json(silent=True)}
    job = submit(name, work, owner=uid, kind=kind)
    return jsonify({'job_id': job.id, 'async': True}), 202


# ── routes ──────────────────────────────────────────────────────────────

def _owner():
    return session.get('user_id')


def api_jobs():
    return jsonify({'jobs': MANAGER.list(_owner()), 'summary': MANAGER.summary(_owner())})


def api_job_get(job_id):
    j = MANAGER.get(job_id)
    if not j or j.owner != _owner():
        return jsonify({'error': 'Tâche introuvable.'}), 404
    return jsonify(j.public(with_result=True))


def _action(job_id, what):
    if session.get('role') == 'viewer' and not _demo_ok():
        return jsonify({'error': 'Réservé au compte propriétaire.', 'code': 'viewer_forbidden'}), 403
    ok = getattr(MANAGER, what)(job_id, _owner())
    return (jsonify({'ok': True}) if ok else (jsonify({'error': 'Tâche introuvable ou déjà terminée.'}), 404))


def api_job_cancel(job_id):
    return _action(job_id, 'cancel')


def api_job_pause(job_id):
    return _action(job_id, 'pause')


def api_job_resume(job_id):
    return _action(job_id, 'resume')


_DEMO_COMPUTE = ('/api/plate/arrange', '/api/organize/preview', '/api/model-diff')


def _demo_ok():
    """Démo publique (lecture seule, `IS_DEMO` posé par la surcouche de démo) : consultation (GET) et calculs sans écriture."""
    try:
        return bool(_MAIN.get('IS_DEMO')) and (request.method in ('GET', 'HEAD') or request.path in _DEMO_COMPUTE)
    except Exception:
        return False


_ROUTES = (
    ('/api/jobs', ['GET'], 'api_jobs', ('login_required', )),
    ('/api/jobs/<job_id>', ['GET'], 'api_job_get', ('login_required', )),
    ('/api/jobs/<job_id>/cancel', ['POST'], 'api_job_cancel', ('login_required', )),
    ('/api/jobs/<job_id>/pause', ['POST'], 'api_job_pause', ('login_required', )),
    ('/api/jobs/<job_id>/resume', ['POST'], 'api_job_resume', ('login_required', )),
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
