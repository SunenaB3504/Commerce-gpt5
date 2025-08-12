const CACHE_NAME = 'commerce-gpt5-shell-v2';
const SHELL_ASSETS = [
  '/web/index.html',
  '/web/assets/css/styles.css',
  '/web/assets/js/config.js',
  '/web/assets/js/upload.js',
  '/web/assets/js/ask.js',
  '/web/manifest.webmanifest',
  '/web/offline.html'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_ASSETS))
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))))
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  const isAPI = url.pathname.startsWith('/ask') || url.pathname.startsWith('/data/') || url.pathname.startsWith('/health');
  // Never cache API requests; try network, fallback offline page for navigations
  if (isAPI) {
    event.respondWith(
      fetch(request).catch(() => new Response(JSON.stringify({ error: 'offline' }), { headers: { 'Content-Type': 'application/json' }, status: 503 }))
    );
    return;
  }
  // For static assets: cache-first, fallback to offline page for navigations
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).catch(() => {
        if (request.mode === 'navigate' || (request.headers.get('accept') || '').includes('text/html')) {
          return caches.match('/web/offline.html');
        }
        return new Response('', { status: 504 });
      });
    })
  );
});
