// Stellio — relais de création d'issues GitHub (Cloudflare Worker)
//
// Rôle : Stellio envoie la demande de l'utilisateur à ce relais, qui crée l'issue sur GitHub avec un jeton
// gardé SECRET côté Cloudflare. Le jeton n'est donc jamais embarqué dans l'application.
//
// Secrets (wrangler secret put …) : GITHUB_TOKEN, HMAC_SECRET
// Variable (wrangler.toml)        : GITHUB_REPO  ex. "stellio-app/stellio"
// Optionnel                       : binding RATE_LIMITER (limitation par IP, voir wrangler.toml)

const TYPES = {
  bug:         { prefix: '[Bug]',         label: 'bug' },
  idea:        { prefix: '[Idée]',        label: 'enhancement' },
  improvement: { prefix: '[Amélioration]', label: 'enhancement' },
  question:    { prefix: '[Question]',    label: 'question' },
};
const LIMITS = { titleMin: 5, titleMax: 120, descMin: 10, descMax: 6000, shortField: 80 };
const GH_HEADERS = (env) => ({
  'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
  'Accept': 'application/vnd.github+json',
  'X-GitHub-Api-Version': '2022-11-28',
  'User-Agent': 'Stellio-Issue-Relay',
  'Content-Type': 'application/json',
});

const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { 'Content-Type': 'application/json; charset=utf-8' } });

const clean = (s, max) => String(s ?? '').replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, '').trim().slice(0, max);

const defang = (s) => s.replace(/@(?=[A-Za-z0-9_-])/g, '@\u200b');

const toHex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');

async function hmacKey(env) {
  return crypto.subtle.importKey('raw', new TextEncoder().encode(env.HMAC_SECRET), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign', 'verify']);
}
async function manageToken(env, number) {
  const sig = await crypto.subtle.sign('HMAC', await hmacKey(env), new TextEncoder().encode(`issue:${number}`));
  return toHex(sig);
}
async function verifyManageToken(env, number, token) {
  if (!/^[0-9a-f]{64}$/.test(String(token || ''))) return false;
  const bytes = new Uint8Array(token.match(/../g).map((h) => parseInt(h, 16)));
  return crypto.subtle.verify('HMAC', await hmacKey(env), bytes, new TextEncoder().encode(`issue:${number}`));
}

function buildBody(p, typeKey) {
  const lines = [defang(p.description), '', '---'];
  if (p.include_tech) {
    lines.push('<details><summary>Informations techniques</summary>', '');
    if (p.version) lines.push(`- Stellio : v${clean(p.version, 20)}`);
    if (p.os) lines.push(`- Système : ${clean(p.os, LIMITS.shortField)}`);
    if (p.lang) lines.push(`- Langue : ${clean(p.lang, 10)}`);
    lines.push(`- Type : ${typeKey}`, '', '</details>', '');
  }
  lines.push('_Envoyé depuis Stellio_');
  return lines.join('\n');
}

async function createIssue(request, env) {
  let p;
  try { p = await request.json(); } catch { return json({ error: 'invalid_json' }, 400); }
  if (p.website) return json({ error: 'rejected' }, 400);                 // champ piège anti-robots
  const type = TYPES[p.type];
  if (!type) return json({ error: 'invalid_type' }, 400);
  if (p.consent !== true) return json({ error: 'consent_required' }, 400);
  const title = clean(p.title, LIMITS.titleMax).replace(/\s+/g, ' ');
  const description = clean(p.description, LIMITS.descMax);
  if (title.length < LIMITS.titleMin) return json({ error: 'title_too_short' }, 400);
  if (description.length < LIMITS.descMin) return json({ error: 'description_too_short' }, 400);

  const res = await fetch(`https://api.github.com/repos/${env.GITHUB_REPO}/issues`, {
    method: 'POST',
    headers: GH_HEADERS(env),
    body: JSON.stringify({
      title: `${type.prefix} ${defang(title)}`,
      body: buildBody({ ...p, description }, p.type),
      labels: [type.label, 'from-stellio'],
    }),
  });
  if (res.status !== 201) {
    console.log('GitHub error', res.status, await res.text());
    return json({ error: 'github_error', status: res.status }, 502);
  }
  const issue = await res.json();
  return json({ number: issue.number, url: issue.html_url, manage_token: await manageToken(env, issue.number) }, 201);
}

async function closeIssue(request, env) {
  let p;
  try { p = await request.json(); } catch { return json({ error: 'invalid_json' }, 400); }
  const number = Number.parseInt(p.number, 10);
  if (!Number.isInteger(number) || number < 1 || !(await verifyManageToken(env, number, p.manage_token))) {
    return json({ error: 'forbidden' }, 403);
  }
  const base = `https://api.github.com/repos/${env.GITHUB_REPO}/issues/${number}`;
  await fetch(`${base}/comments`, {
    method: 'POST', headers: GH_HEADERS(env),
    body: JSON.stringify({ body: '_Demande fermée par son auteur depuis Stellio._' }),
  });
  const res = await fetch(base, {
    method: 'PATCH', headers: GH_HEADERS(env),
    body: JSON.stringify({ state: 'closed', state_reason: 'not_planned' }),
  });
  if (!res.ok) return json({ error: 'github_error', status: res.status }, 502);
  return json({ ok: true });
}

export default {
  async fetch(request, env) {
    if (request.method !== 'POST') return json({ error: 'method_not_allowed' }, 405);
    if (!env.GITHUB_TOKEN || !env.HMAC_SECRET || !env.GITHUB_REPO) return json({ error: 'relay_not_configured' }, 500);

    if (env.RATE_LIMITER) {
      const key = request.headers.get('CF-Connecting-IP') || 'unknown';
      const { success } = await env.RATE_LIMITER.limit({ key });
      if (!success) return json({ error: 'rate_limited' }, 429);
    }
    if (Number(request.headers.get('content-length') || 0) > 20000) return json({ error: 'too_large' }, 413);

    const path = new URL(request.url).pathname.replace(/\/+$/, '');
    if (path === '/issue') return createIssue(request, env);
    if (path === '/issue/close') return closeIssue(request, env);
    return json({ error: 'not_found' }, 404);
  },
};
