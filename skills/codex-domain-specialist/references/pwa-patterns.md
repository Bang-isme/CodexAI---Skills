# Progressive Web App (PWA) Patterns

## Manifest

```json
{
  "name": "My App",
  "short_name": "App",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#10b981",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

## Service Worker Strategy

- Cache-first for static assets.
- Network-first for API calls.

```javascript
const CACHE_NAME = 'app-v1';
const STATIC_ASSETS = ['/', '/index.html', '/styles.css', '/app.js'];
```

## When to Use PWA

- Internal tools needing offline fallback.
- Mobile-first web apps without app-store delivery.
- Content-heavy apps benefiting from cache.
