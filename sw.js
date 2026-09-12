const CACHE_VERSION = 'stellio-v4';
const SHELL_CACHE = `${CACHE_VERSION}-shell`;
const ASSETS_CACHE = `${CACHE_VERSION}-assets`;

const SHELL_URLS = ['/', '/index.html', '/script.js', '/style.css'];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(SHELL_CACHE).then((cache) => cache.addAll(SHELL_URLS).catch(() => {
        }))
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((names) => Promise.all(
            names
                .filter((name) => name.startsWith('stellio-') && name !== SHELL_CACHE && name !== ASSETS_CACHE)
                .map((name) => caches.delete(name))
        ))
    );
    self.clients.claim();
});

function isApiRequest(url) {
    return url.pathname.startsWith('/api/') || url.pathname.startsWith('/share/');
}

function isStaticAsset(url) {
    return url.pathname.startsWith('/assets/');
}

self.addEventListener('fetch', (event) => {
    const req = event.request;
    if (req.method !== 'GET') return;

    const url = new URL(req.url);
    if (url.origin !== self.location.origin) return;

    if (isApiRequest(url)) {
        return; 
    }

    if (isStaticAsset(url)) {
        event.respondWith(
            caches.open(ASSETS_CACHE).then(async (cache) => {
                const cached = await cache.match(req);
                if (cached) return cached;
                try {
                    const fresh = await fetch(req);
                    if (fresh.ok) cache.put(req, fresh.clone());
                    return fresh;
                } catch (e) {
                    return cached || Response.error();
                }
            })
        );
        return;
    }

    event.respondWith(
        fetch(req)
            .then((fresh) => {
                if (fresh.ok) {
                    caches.open(SHELL_CACHE).then((cache) => cache.put(req, fresh.clone()));
                }
                return fresh;
            })
            .catch(() => caches.match(req).then((cached) => cached || caches.match('/index.html')))
    );
});