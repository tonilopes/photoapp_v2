// Service Worker do fluxo público de formandos (fotoid.photum.com.br).
// Ligero e "network-first": as páginas SEMPRE tentam red antes de servir cache;
// os estáticos públicos se cacheam (rond trip). Nunca interfere com o
// service worker do backoffice (/sw.js) — cache separada "photum-fotoid-*".
var VERSION = 'f4-v1';
var CACHE = 'photum-fotoid-' + VERSION;

var PRECACHE = [
  '/static/gestcaptur/css/fase4_publico.css',
  '/static/gestcaptur/js/fase4_publico.js',
  '/static/gestcaptur/manifest_fotoid.json',
  '/static/gestcaptur/images/logo.png',
  '/static/gestcaptur/images/icons/icon-192.png',
  '/static/gestcaptur/images/icons/icon-512.png'
];

addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE).then(function (cache) { return cache.addAll(PRECACHE); }).catch(function () {})
  );
});

addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys
          .filter(function (key) { return key.indexOf('photum-fotoid-') === 0 && key !== CACHE; })
          .map(function (key) { return caches.delete(key); })
      );
    }).catch(function () {})
  );
});

function semCache() {
  return Promise.reject(new Error('sin cache offline disponible'));
}

addEventListener('fetch', function (event) {
  var req = event.request;
  if (req.method !== 'GET') return;

  var url = new URL(req.url);

  // Navegación (páginas HTML): red primeiro, cache só como plano B (offline)
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req).catch(function () { return caches.match(req).catch(semCache); })
    );
    return;
  }

  // Estáticos do nosso domínio: red primeiro, atualiza cache en segundo plano,
  // cache como fallback si falla a red.
  if (url.origin === location.origin && url.pathname.indexOf('/static/') === 0) {
    event.respondWith(
      fetch(req)
        .then(function (resp) {
          if (resp && resp.ok) {
            var copia = resp.clone();
            caches.open(CACHE)
              .then(function (cache) { return cache.put(req, copia); })
              .catch(function () {});
          }
          return resp;
        })
        .catch(function () { return caches.match(req).catch(semCache); })
    );
  }
});