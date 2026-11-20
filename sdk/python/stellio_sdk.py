"""Stellio SDK pour Python (1.1.7) — sans dépendance (bibliothèque standard uniquement).

Deux usages :
  1. Script externe qui appelle l'API publique :
         from stellio_sdk import Stellio
         s = Stellio("http://localhost:8765", "stl_...")   # jeton créé dans Paramètres > API publique
         print(s.printers())
  2. Plugin : Stellio lance le script avec l'évènement sur l'entrée standard.
         from stellio_sdk import plugin_event, from_env
         event, data = plugin_event()
         s = from_env()          # utilise STELLIO_API_URL / STELLIO_API_TOKEN si la permission api:* est accordée
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


class StellioError(Exception):
    def __init__(self, status, message, code=None):
        super().__init__(f"{status} {message}")
        self.status, self.message, self.code = status, message, code


class Stellio:
    def __init__(self, base_url, token, timeout=15):
        if not base_url or not token:
            raise ValueError("base_url et token sont obligatoires")
        self.base, self.token, self.timeout = base_url.rstrip('/'), token, timeout

    def _call(self, method, path, params=None, body=None):
        url = f"{self.base}/api/v1{path}"
        if params:
            url += '?' + urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, '')})
        data = json.dumps(body).encode('utf-8') if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read().decode('utf-8') or '{}')
        except urllib.error.HTTPError as e:
            try:
                d = json.loads(e.read().decode('utf-8'))
            except Exception:
                d = {}
            raise StellioError(e.code, d.get('error') or e.reason, d.get('code')) from None

    def me(self): return self._call('GET', '/me')
    def files(self, q=None, type=None, limit=100, offset=0): return self._call('GET', '/files', dict(q=q, type=type, limit=limit, offset=offset))['files']
    def printers(self): return self._call('GET', '/printers')['printers']
    def printer_status(self, printer_id): return self._call('GET', f'/printers/{int(printer_id)}/status')
    def tasks(self, status=None): return self._call('GET', '/tasks', dict(status=status))['tasks']
    def task(self, task_id): return self._call('GET', f'/tasks/{int(task_id)}')
    def create_task(self, part, **kw): return self._call('POST', '/tasks', body=dict(kw, part=part))
    def update_task(self, task_id, **kw): return self._call('PATCH', f'/tasks/{int(task_id)}', body=kw)
    def materials(self): return self._call('GET', '/materials')['materials']
    def history(self, result=None, printer_id=None, limit=100): return self._call('GET', '/history', dict(result=result, printer_id=printer_id, limit=limit))['history']
    def create_material(self, name, **kw): return self._call('POST', '/materials', body=dict(kw, name=name))
    def update_material(self, material_id, **kw): return self._call('PATCH', f'/materials/{int(material_id)}', body=kw)
    def create_project(self, name, **kw): return self._call('POST', '/projects', body=dict(kw, name=name))
    def update_project(self, project_id, **kw): return self._call('PATCH', f'/projects/{int(project_id)}', body=kw)
    def projects(self): return self._call('GET', '/projects')['projects']
    def project(self, project_id): return self._call('GET', f'/projects/{int(project_id)}')


def from_env():
    """Client construit depuis l'environnement d'un plugin (permission api:read / api:write)."""
    return Stellio(os.environ.get('STELLIO_API_URL', ''), os.environ.get('STELLIO_API_TOKEN', ''))


def plugin_config():
    return json.loads(os.environ.get('STELLIO_PLUGIN_CONFIG') or '{}')


def plugin_event():
    """(nom de l'évènement, données) reçus par ce plugin."""
    payload = json.loads(sys.stdin.read() or '{}')
    return payload.get('event') or (sys.argv[1] if len(sys.argv) > 1 else ''), payload.get('data') or {}
