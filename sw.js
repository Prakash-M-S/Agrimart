const CACHE_NAME = 'agrimart-ai-pwa-v1';
const ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './static/agrimart_data.js'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(cached => cached || fetch(event.request))
  );
});
