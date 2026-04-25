# PWA Patterns

Progressive Web App patterns for offline-capable, installable web applications.

## Service Worker Strategy

### Cache-First (Static Assets)

Best for: fonts, images, CSS, JS bundles — content that rarely changes.

```javascript
// sw.js
const CACHE_NAME = 'static-v1';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/styles/app.css',
  '/scripts/app.js',
  '/fonts/inter-regular.woff2',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request))
  );
});
```

### Network-First (API Data)

Best for: user data, dynamic content — freshness matters more than speed.

```javascript
self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          const clone = response.clone();
          caches.open('api-v1').then((cache) => cache.put(event.request, clone));
          return response;
        })
        .catch(() => caches.match(event.request))
    );
  }
});
```

### Stale-While-Revalidate (Semi-Dynamic)

Best for: news feeds, product listings — acceptable to show stale briefly.

```javascript
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.open('swr-v1').then((cache) =>
      cache.match(event.request).then((cached) => {
        const fetchPromise = fetch(event.request).then((response) => {
          cache.put(event.request, response.clone());
          return response;
        });
        return cached || fetchPromise;
      })
    )
  );
});
```

## Web App Manifest

```json
{
  "name": "My Application",
  "short_name": "MyApp",
  "description": "Description for install prompt",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#1a1a2e",
  "theme_color": "#16213e",
  "orientation": "portrait-primary",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/icons/icon-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ],
  "screenshots": [
    { "src": "/screenshots/home.png", "sizes": "1080x1920", "type": "image/png" }
  ]
}
```

**Required icons:** 192×192 + 512×512 minimum. Add maskable icon for Android adaptive icons.

## Offline Patterns

### Offline Detection

```javascript
// Show offline indicator
window.addEventListener('online', () => showStatus('Online'));
window.addEventListener('offline', () => showStatus('Offline — changes saved locally'));
```

### Background Sync (Queue Failed Requests)

```javascript
// In main app — register sync when offline
if ('serviceWorker' in navigator && 'SyncManager' in window) {
  navigator.serviceWorker.ready.then((reg) => {
    return reg.sync.register('sync-pending-orders');
  });
}

// In service worker — process queue when online
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-pending-orders') {
    event.waitUntil(processPendingOrders());
  }
});
```

### IndexedDB for Offline Data

```javascript
// Store data locally when offline
const db = await openDB('myapp', 1, {
  upgrade(db) {
    db.createObjectStore('pending-orders', { keyPath: 'id', autoIncrement: true });
  },
});

// Save order when offline
await db.add('pending-orders', { items, total, createdAt: Date.now() });

// Sync when back online
const pending = await db.getAll('pending-orders');
for (const order of pending) {
  await fetch('/api/orders', { method: 'POST', body: JSON.stringify(order) });
  await db.delete('pending-orders', order.id);
}
```

## Install Prompt

```javascript
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  showInstallButton();
});

installButton.addEventListener('click', async () => {
  deferredPrompt.prompt();
  const { outcome } = await deferredPrompt.userChoice;
  console.log(`Install ${outcome}`); // 'accepted' or 'dismissed'
  deferredPrompt = null;
});
```

## PWA Checklist

| Requirement | How to Verify |
|---|---|
| HTTPS | Check `location.protocol === 'https:'` |
| Service Worker registered | `navigator.serviceWorker.controller` exists |
| Web App Manifest linked | `<link rel="manifest" href="/manifest.json">` in HTML |
| 192px + 512px icons | Check manifest `icons` array |
| Offline page works | Disconnect network → reload → see cached content |
| Install prompt appears | Chrome DevTools → Application → Manifest → "Add to homescreen" |
| Lighthouse PWA score | `npx lighthouse <url> --only-categories=pwa` |

## Common Mistakes

| Mistake | Fix |
|---|---|
| Caching API responses forever | Set max-age or use stale-while-revalidate |
| No cache versioning | Use `CACHE_NAME = 'v2'` and delete old caches on activate |
| Registering SW in development | Gate behind `if (process.env.NODE_ENV === 'production')` |
| Missing maskable icon | Users see white circle on Android — add `purpose: maskable` |
| No offline fallback page | Create `/offline.html` and serve from cache on network failure |
