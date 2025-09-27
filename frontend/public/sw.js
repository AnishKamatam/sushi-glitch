const CACHE_NAME = 'leviathan-v1';
const STATIC_ASSETS = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json'
];

const API_CACHE_NAME = 'leviathan-api-v1';

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  if (request.method === 'GET') {
    if (url.pathname.includes('/api/')) {
      event.respondWith(handleApiRequest(request));
    } else {
      event.respondWith(handleStaticRequest(request));
    }
  }
});

async function handleStaticRequest(request) {
  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
      return networkResponse;
    }
  } catch (error) {
    console.log('Network failed, trying cache:', error);
  }

  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  if (request.mode === 'navigate') {
    const cachedIndex = await caches.match('/');
    if (cachedIndex) {
      return cachedIndex;
    }
  }

  return new Response('Offline - Resource not available', {
    status: 503,
    statusText: 'Service Unavailable'
  });
}

async function handleApiRequest(request) {
  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      const cache = await caches.open(API_CACHE_NAME);
      cache.put(request, networkResponse.clone());
      return networkResponse;
    }
  } catch (error) {
    console.log('API request failed, trying cache:', error);
  }

  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    const response = cachedResponse.clone();
    response.headers.set('X-From-Cache', 'true');
    return response;
  }

  return new Response(JSON.stringify({
    error: 'Service unavailable',
    message: 'API is offline and no cached data available',
    offline: true
  }), {
    status: 503,
    statusText: 'Service Unavailable',
    headers: {
      'Content-Type': 'application/json'
    }
  });
}

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-trip-data') {
    event.waitUntil(syncTripData());
  }
});

async function syncTripData() {
  try {
    const tripData = await getStoredTripData();
    if (tripData.length > 0) {
      for (const trip of tripData) {
        await fetch('/api/trips/sync', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(trip)
        });
      }

      await clearStoredTripData();
    }
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

async function getStoredTripData() {
  const cache = await caches.open('leviathan-sync');
  const response = await cache.match('/sync-data');
  if (response) {
    return response.json();
  }
  return [];
}

async function clearStoredTripData() {
  const cache = await caches.open('leviathan-sync');
  await cache.delete('/sync-data');
}