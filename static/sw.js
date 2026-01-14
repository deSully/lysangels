// Service Worker pour LysAngels PWA
const CACHE_NAME = 'lysangels-v1.0.0';
const RUNTIME_CACHE = 'lysangels-runtime-v1';

// Assets à mettre en cache au moment de l'installation
const STATIC_ASSETS = [
  '/',
  '/vendors/',
  '/how-it-works/',
  '/about/',
  '/static/manifest.json',
  // Ajoutez vos CSS/JS critiques ici
];

// Installation du Service Worker
self.addEventListener('install', (event) => {
  console.log('[SW] Installation...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Cache ouvert');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('[SW] Installation terminée');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[SW] Erreur installation:', error);
      })
  );
});

// Activation et nettoyage des anciens caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activation...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((cacheName) => {
            return cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE;
          })
          .map((cacheName) => {
            console.log('[SW] Suppression ancien cache:', cacheName);
            return caches.delete(cacheName);
          })
      );
    })
    .then(() => {
      console.log('[SW] Activation terminée');
      return self.clients.claim();
    })
  );
});

// Stratégie de cache
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignorer les requêtes non-GET
  if (request.method !== 'GET') {
    return;
  }

  // Ignorer les requêtes admin et API
  if (url.pathname.startsWith('/admin/') || 
      url.pathname.startsWith('/api/') ||
      url.pathname.includes('django_debug')) {
    return;
  }

  // Stratégie Cache First pour les assets statiques
  if (url.pathname.startsWith('/static/') || 
      url.pathname.startsWith('/media/')) {
    event.respondWith(
      caches.match(request)
        .then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          return caches.open(RUNTIME_CACHE).then((cache) => {
            return fetch(request).then((response) => {
              // Mettre en cache seulement les réponses valides
              if (response && response.status === 200) {
                cache.put(request, response.clone());
              }
              return response;
            });
          });
        })
        .catch(() => {
          // Fallback pour les images
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
        // Mettre à jour le cache avec la nouvelle version
        if (response && response.status === 200) {
          const responseClone = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => {
            cache.put(request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        // Fallback vers le cache si offline
        return caches.match(request).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          // Page offline par défaut
          return caches.match('/offline/');
        });
      })
  );
});

// Synchronisation en arrière-plan (optionnel)
self.addEventListener('sync', (event) => {
  console.log('[SW] Background Sync:', event.tag);
  if (event.tag === 'sync-messages') {
    event.waitUntil(syncMessages());
  }
});

async function syncMessages() {
  // Logique de synchronisation des messages
  console.log('[SW] Synchronisation des messages...');
}

// Notifications Push (optionnel)
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'Nouvelle notification LysAngels',
    icon: '/static/images/icons/icon-192x192.png',
    badge: '/static/images/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Voir',
        icon: '/static/images/icons/checkmark.png'
      },
      {
        action: 'close',
        title: 'Fermer',
        icon: '/static/images/icons/xmark.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('LysAngels', options)
  );
});

// Gestion des clics sur les notifications
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});
