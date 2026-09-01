// Service Worker do painel interno (Gestor/Coordenador/Fotógrafo). Não é registrado nas páginas públicas de clientes.
const STATIC_CACHE = 'gestcaptur-static-v1';

const PRECACHE_URLS = [
  '/static/gestcaptur/manifest.json',
  '/static/gestcaptur/css/custom_mobile.css',
  '/static/gestcaptur/images/icons/icon-192.png',
  '/static/gestcaptur/images/icons/icon-512.png',
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then(cache => cache.addAll(PRECACHE_URLS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(key => key !== STATIC_CACHE).map(key => caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;

  // Páginas (HTML): rede primeiro, cai pro cache se estiver offline
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(() => caches.match(request))
    );
    return;
  }

  // Assets estáticos e CDNs (CSS/JS/imagens): cache primeiro, atualiza em segundo plano
  const url = new URL(request.url);
  const isStaticAsset = url.pathname.startsWith('/static/') || url.hostname !== self.location.hostname;
  if (isStaticAsset) {
    event.respondWith(
      caches.match(request).then(cached => {
        const networkFetch = fetch(request).then(response => {
          if (response && response.ok) {
            caches.open(STATIC_CACHE).then(cache => cache.put(request, response.clone()));
          }
          return response;
        }).catch(() => cached);
        return cached || networkFetch;
      })
    );
  }
});
