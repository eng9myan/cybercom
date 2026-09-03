// CyMed Patient App — offline-first service worker (PWA shell)
const CACHE = 'cymed-patient-v1';
const SHELL = [
  '/patient-app/',
  '/patient-app/main.dart.js',
  '/patient-app/flutter.js',
  '/patient-app/flutter_bootstrap.js',
  '/patient-app/assets/AssetManifest.bin.json',
  '/static/patient_app/manifest.json',
];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL).catch(() => {})));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // API — network first, no caching of PHI
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(fetch(event.request));
    return;
  }

  // Shell / assets — cache first
  event.respondWith(
    caches.match(event.request).then((hit) => hit || fetch(event.request).then((resp) => {
      const copy = resp.clone();
      caches.open(CACHE).then((c) => c.put(event.request, copy)).catch(() => {});
      return resp;
    }).catch(() => caches.match('/patient-app/')))
  );
});

// Push (Firebase Web Push)
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : {};
  event.waitUntil(
    self.registration.showNotification(data.title || 'CyMed', {
      body: data.body || '',
      icon: '/static/patient_app/icons/icon-192.png',
      badge: '/static/patient_app/icons/icon-192.png',
      data: data.deeplink ? { deeplink: data.deeplink } : {},
      dir: 'auto',
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const dl = event.notification.data?.deeplink;
  event.waitUntil(clients.openWindow(dl || '/patient-app/'));
});
