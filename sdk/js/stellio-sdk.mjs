// Stellio SDK pour JavaScript (1.1.7) — Node 18+ ou navigateur ; aucune dépendance.
//   import { Stellio } from './stellio-sdk.mjs';
//   const s = new Stellio('http://localhost:8765', 'stl_...');   // jeton : Paramètres > API publique
//   console.log(await s.printers());
export class StellioError extends Error {
  constructor(status, message, code) { super(`${status} ${message}`); this.status = status; this.code = code; }
}

export class Stellio {
  constructor(baseUrl, token) {
    if (!baseUrl || !token) throw new Error('baseUrl et token sont obligatoires');
    this.base = baseUrl.replace(/\/+$/, ''); this.token = token;
  }
  async _call(method, path, params, body) {
    const qs = params ? '?' + new URLSearchParams(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')) : '';
    const r = await fetch(`${this.base}/api/v1${path}${qs}`, {
      method, headers: { Authorization: `Bearer ${this.token}`, 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body),
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new StellioError(r.status, d.error || r.statusText, d.code);
    return d;
  }
  me() { return this._call('GET', '/me'); }
  async files(opts = {}) { return (await this._call('GET', '/files', opts)).files; }
  async printers() { return (await this._call('GET', '/printers')).printers; }
  printerStatus(id) { return this._call('GET', `/printers/${Number(id)}/status`); }
  async tasks(status) { return (await this._call('GET', '/tasks', { status })).tasks; }
  task(id) { return this._call('GET', `/tasks/${Number(id)}`); }
  createTask(part, fields = {}) { return this._call('POST', '/tasks', undefined, { ...fields, part }); }
  updateTask(id, fields) { return this._call('PATCH', `/tasks/${Number(id)}`, undefined, fields); }
  createMaterial(name, fields = {}) { return this._call('POST', '/materials', undefined, { ...fields, name }); }
  updateMaterial(id, fields) { return this._call('PATCH', `/materials/${Number(id)}`, undefined, fields); }
  createProject(name, fields = {}) { return this._call('POST', '/projects', undefined, { ...fields, name }); }
  updateProject(id, fields) { return this._call('PATCH', `/projects/${Number(id)}`, undefined, fields); }
  async materials() { return (await this._call('GET', '/materials')).materials; }
  async history(opts = {}) { return (await this._call('GET', '/history', opts)).history; }
  async projects() { return (await this._call('GET', '/projects')).projects; }
  project(id) { return this._call('GET', `/projects/${Number(id)}`); }
}
