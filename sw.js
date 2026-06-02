// ── Service Worker — Mes Menus ────────────────────────────────
// Stratégie :
//   - App shell (HTML, manifest, firebase-sync) : cache-first
//   - menus_data.js : network-first → mise à jour hebdo propagée
//   - Polices Google : cache-first après premier chargement
//
// ⚠️ __CACHE_VERSION__ est remplacé automatiquement par la date du jour
//    lors de chaque upload via _github_upload_test.html
//    → force tous les navigateurs à vider l'ancien cache

const CACHE_APP  = 'menus-app-__CACHE_VERSION__';
const CACHE_DATA = 'menus-data-__CACHE_VERSION__';

const APP_SHELL = [
  './menus_app.html',
  './manifest.json',
  './icon.svg',
  './firebase-sync.js',
  'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=DM+Mono:wght@400;500&display=swap',
];

// ── Install : mise en cache du shell ──────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_APP)
      .then(cache => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

// ── Activate : nettoyage des anciens caches ───────────────────
self.addEventListener('activate', event => {
  const VALID = [CACHE_APP, CACHE_DATA];
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => !VALID.includes(k)).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

// ── Fetch : stratégie selon la ressource ─────────────────────
self.addEventListener('fetch', event => {
  const url = event.request.url;

  // menus_data.js → network-first (les menus changent chaque semaine)
  if (url.includes('menus_data.js')) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          const clone = response.clone();
          caches.open(CACHE_DATA).then(c => c.put(event.request, clone));
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // Polices et ressources Firebase CDN → cache-first
  if (url.startsWith('https://fonts.') || url.includes('firebasejs')) {
    event.respondWith(
      caches.match(event.request).then(r => r || fetch(event.request)
        .then(response => {
          const clone = response.clone();
          caches.open(CACHE_APP).then(c => c.put(event.request, clone));
          return response;
        })
      )
    );
    return;
  }

  // App shell → cache-first
  event.respondWith(
    caches.match(event.request)
      .then(r => r || fetch(event.request))
  );
});

// ── Periodic Sync — Chrome Android (notification app fermée) ──
self.addEventListener('periodicsync', event => {
  if (event.tag === 'courses-reminder') {
    event.waitUntil(_checkSaturdayNotif());
  }
});

// ── Push — serveur VAPID futur ────────────────────────────────
self.addEventListener('push', event => {
  const data = event.data?.json() || {};
  event.waitUntil(
    self.registration.showNotification(data.title || '🛒 Courses du weekend', {
      body: data.body || "N'oubliez pas votre liste de courses !",
      icon: './icon.svg',
      badge: './icon.svg',
      tag: 'courses-reminder'
    })
  );
});

// ── Message depuis la page — heure planifiée ─────────────────
self.addEventListener('message', event => {
  if (event.data?.type === 'SCHEDULE_NOTIF') {
    self._nextNotifMs = event.data.nextSat;
  }
});

async function _checkSaturdayNotif() {
  if (!self._nextNotifMs) return;
  const diff = Math.abs(Date.now() - self._nextNotifMs);
  if (diff < 2 * 3600 * 1000) {
    await self.registration.showNotification('🛒 Courses du weekend', {
      body: "C'est samedi ! N'oubliez pas vos courses.",
      icon: './icon.svg',
      tag: 'courses-reminder',
      renotify: false
    });
  }
}
