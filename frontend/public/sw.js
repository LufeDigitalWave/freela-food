/// <reference lib="webworker" />

/**
 * Service Worker — freela-food PWA
 *
 * Estratégia: Network First com fallback offline para páginas estáticas.
 * Assets estáticos são cachados no install para offline básico.
 */

const CACHE_NAME = 'freela-food-v1';
const OFFLINE_URL = '/offline';

const STATIC_ASSETS = [
  '/',
  '/como-funciona',
  '/sobre',
  '/termos',
  '/privacidade',
  '/offline',
];

// @ts-expect-error: ServiceWorkerGlobalScope
const sw = self as unknown as ServiceWorkerGlobalScope;

sw.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  // Ativar imediatamente (não esperar outras tabs fecharem)
  sw.skipWaiting();
});

sw.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  // Tomar controle de todas as tabs
  sw.clients.claim();
});

sw.addEventListener('fetch', (event) => {
  const { request } = event;

  // Ignorar requests não-GET
  if (request.method !== 'GET') return;

  // Ignorar requests pra API
  if (request.url.includes('/v1/') || request.url.includes('/api/')) return;

  // Ignorar requests de extensões
  if (request.url.startsWith('chrome-extension://')) return;

  event.respondWith(
    fetch(request)
      .then((response) => {
        // Cache de navegação (páginas HTML)
        if (request.mode === 'navigate') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, clone);
          });
        }
        return response;
      })
      .catch(() => {
        // Offline: tentar servir do cache
        return caches.match(request).then((cached) => {
          if (cached) return cached;
          // Fallback para página offline
          if (request.mode === 'navigate') {
            return caches.match(OFFLINE_URL) as Promise<Response>;
          }
          return new Response('Offline', { status: 503 });
        });
      })
  );
});
