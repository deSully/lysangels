{% load static %}
'use strict';

const CACHE_VERSION = 'v1';
const STATIC_CACHE = `lysangels-static-${CACHE_VERSION}`;
const HTML_CACHE   = `lysangels-html-${CACHE_VERSION}`;
const HTML_TTL     = 10 * 60 * 1000; // 10 minutes en ms

const STATIC_ASSETS = [
  '{% static "css/tailwind.css" %}',
  '{% static "css/design-system.css" %}',
  '{% static "css/components.css" %}',
  '{% static "css/mobile.css" %}',
  '{% static "images/favicon.svg" %}',
  '/offline/',
];

// ── Install : précache les assets statiques ────────────────────────────
self.addEventListener('install', event => {
  self.skipWaiting(); // Active le nouveau SW immédiatement (deploy → refresh = nouvelle version)
  event.waitUntil(
    caches.open(STATIC_CACHE).then(cache => cache.addAll(STATIC_ASSETS))
  );
});

// ── Activate : purge les anciens caches ───────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(k => k !== STATIC_CACHE && k !== HTML_CACHE)
          .map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

// ── Fetch ─────────────────────────────────────────────────────────────
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  if (request.method !== 'GET') return;
  if (!url.protocol.startsWith('http')) return;

  // Assets statiques et fonts Bunny : cache-first
  if (url.pathname.startsWith('/static/') || url.hostname === 'fonts.bunny.net') {
    event.respondWith(cacheFirst(request));
    return;
  }

  // Navigation HTML : network-first, cache offline 10 min
  if (request.mode === 'navigate') {
    event.respondWith(networkFirstHtml(request));
  }
});

// ── Stratégies ───────────────────────────────────────────────────────

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return new Response('', { status: 503 });
  }
}

async function networkFirstHtml(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      // Stocke la page avec horodatage pour le TTL offline
      const body = await response.arrayBuffer();
      const headers = new Headers(response.headers);
      headers.set('x-sw-cached-at', String(Date.now()));
      const toCache = new Response(body, {
        status: response.status,
        statusText: response.statusText,
        headers,
      });
      const cache = await caches.open(HTML_CACHE);
      cache.put(request, toCache);
    }
    return response;
  } catch {
    // Hors ligne : tente le cache si < 10 min
    const cache = await caches.open(HTML_CACHE);
    const cached = await cache.match(request);
    if (cached) {
      const cachedAt = parseInt(cached.headers.get('x-sw-cached-at') || '0');
      if (Date.now() - cachedAt < HTML_TTL) {
        return cached;
      }
    }
    // Cache absent ou périmé → page offline
    const offline = await caches.match('/offline/');
    return offline || new Response('<h1>Hors ligne</h1>', {
      status: 503,
      headers: { 'Content-Type': 'text/html; charset=utf-8' },
    });
  }
}
