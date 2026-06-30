// Service Worker pour LysAngels PWA
const CACHE_NAME = 'lysangels-v2.1.0';
const RUNTIME_CACHE = 'lysangels-runtime-v2.1';

// Assets à mettre en cache au moment de l'installation
const STATIC_ASSETS = [
  '/',
  '/vendors/',
  '/how-it-works/',
  '/about/',
  '/static/manifest.json',
];

// Installation du Service Worker
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
      .catch((error) => console.error('[SW] Erreur installation:', error))
  );
});

// Activation et nettoyage des anciens caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((cacheName) => cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE)
          .map((cacheName) => caches.delete(cacheName))
      );
    })
    .then(() => self.clients.claim())
  );
});

// Stratégie de cache
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignorer les requêtes non-GET
  if (request.method !== 'GET') return;

  // Ignorer les requêtes admin
  if (url.pathname.startsWith('/admin/') || url.pathname.startsWith('/accounts/')) return;

  // Stratégie Cache First pour les assets statiques
  if (url.pathname.startsWith('/static/') || url.pathname.startsWith('/media/')) {
    event.respondWith(
      caches.match(request)
        .then((cachedResponse) => {
          if (cachedResponse) return cachedResponse;
          return caches.open(RUNTIME_CACHE).then((cache) => {
            return fetch(request).then((response) => {
              if (response && response.status === 200) {
                cache.put(request, response.clone());
              }
              return response;
            });
          });
        })
        .catch(() => {
          if (request.destination === 'image') {
            return caches.match('/static/images/placeholder.png');
          }
        })
    );
    return;
  }

  // Stratégie Network First pour le HTML
  event.respondWith(
    fetch(request)
      .then((response) => {
        if (response && response.status === 200) {
          const responseClone = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => {
            cache.put(request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        return caches.match(request).then((cachedResponse) => {
          if (cachedResponse) return cachedResponse;
          // Page d'accueil en fallback
          return caches.match('/');
        });
      })
  );
});
