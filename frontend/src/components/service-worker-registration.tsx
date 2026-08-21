'use client';

import { useEffect } from 'react';

/**
 * Component para registrar service worker (PWA support)
 * Roda apenas no cliente e não quebra SSR
 */
export function ServiceWorkerRegistration() {
  useEffect(() => {
    if (typeof window === 'undefined') return;

    // Registrar SW apenas em produção ou se explicitamente habilitado
    const isProduction = process.env.NODE_ENV === 'production';
    const enableSWLocal = process.env.NEXT_PUBLIC_ENABLE_SW === 'true';

    if (!isProduction && !enableSWLocal) {
      console.debug('[PWA] Service Worker registration disabled in dev');
      return;
    }

    if (!('serviceWorker' in navigator)) {
      console.warn('[PWA] Service Workers not supported in this browser');
      return;
    }

    navigator.serviceWorker
      .register('/sw.js', { scope: '/' })
      .then((reg) => {
        console.log('[PWA] Service Worker registered successfully', reg);
      })
      .catch((err) => {
        console.error('[PWA] Service Worker registration failed:', err);
      });
  }, []);

  return null;
}
