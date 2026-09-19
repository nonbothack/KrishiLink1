/* Static shell only. This worker never queues or replays an application write. */
const CACHE_NAME = 'krishilink-shell-v1';
const SHELL = [
  '/app-shell.html',
  '/offline.html',
  '/manifest.webmanifest',
  '/favicon.svg',
  '/icons/krishilink.svg',
];

function isCacheableStaticPath(pathname) {
  if (SHELL.includes(pathname)) return true;
  return /^\/assets\/[A-Za-z0-9_-]+\.(?:js|css|svg|png|webp|woff2?)$/.test(pathname);
}

function safeNotificationPath(path) {
  if (typeof path !== 'string' || path.length > 256 || !path.startsWith('/') || path.startsWith('//') || path.includes('\\')) return '/';
  if (path === '/' || path === '/prices' || path === '/offers' || path === '/transactions' || path === '/grievances') return path;
  const offer = path.match(/^\/offers\?offer_id=([0-9a-fA-F-]{36})$/);
  if (offer && /^[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$/.test(offer[1])) return path;
  const trade = path.match(/^\/trades\/([0-9a-fA-F-]{36})$/);
  if (trade && /^[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$/.test(trade[1])) return path;
  return '/';
}

self.addEventListener('push', (event) => {
  event.waitUntil((async () => {
    let payload = null;
    try { payload = event.data?.json?.(); } catch { payload = null; }
    const valid = payload && payload.schema_version === 1 && typeof payload.title === 'string'
      && typeof payload.body === 'string' && ['price', 'offer', 'trade', 'support', 'general'].includes(payload.category);
    const title = valid ? payload.title.slice(0, 80) : 'KrishiLink update';
    const body = valid ? payload.body.slice(0, 180) : 'Open KrishiLink to review your updates.';
    const path = safeNotificationPath(valid ? payload.path : '/');
    const notificationId = valid && /^[0-9a-fA-F-]{36}$/.test(payload.notification_id || '')
      ? payload.notification_id
      : 'general';
    await self.registration.showNotification(title, {
      body,
      icon: '/icons/krishilink.svg',
      badge: '/icons/krishilink.svg',
      tag: `krishilink-${notificationId}`,
      data: { path, schema_version: 1 },
    });
  })());
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const path = safeNotificationPath(event.notification.data?.path);
  const target = new URL(path, self.location.origin);
  event.waitUntil((async () => {
    const windows = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const client of windows) {
      try {
        if (new URL(client.url).origin === self.location.origin) {
          await client.navigate(target.href);
          return await client.focus();
        }
      } catch { /* Open a clean same-origin window below. */ }
    }
    return self.clients.openWindow(target.href);
  })());
});

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(
    SHELL.map((path) => new Request(new URL(path, self.location.origin), { credentials: 'omit', cache: 'reload' })),
  )));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key.startsWith('krishilink-shell-') && key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('message', (event) => {
  if (event.data?.type === 'ACTIVATE_UPDATE') self.skipWaiting();
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).catch(async () => (await caches.match('/app-shell.html')) || caches.match('/offline.html')));
    return;
  }
  if (url.search || !isCacheableStaticPath(url.pathname)) return;
  event.respondWith(
    caches.match(request, { ignoreVary: true }).then((cached) => cached || fetch(request).then((response) => {
      if (response.ok && response.type === 'basic') {
        const copy = response.clone();
        void caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
      }
      return response;
    })),
  );
});
