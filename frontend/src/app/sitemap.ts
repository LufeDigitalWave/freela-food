import type { MetadataRoute } from 'next';

/**
 * Sitemap dinâmico para SEO.
 * Gera URLs das páginas públicas indexáveis.
 */
export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://freela-food.com.br';

  return [
    {
      url: baseUrl,
      lastModified: new Date('2026-08-21'),
      changeFrequency: 'weekly',
      priority: 1.0,
    },
    {
      url: `${baseUrl}/como-funciona`,
      lastModified: new Date('2026-08-21'),
      changeFrequency: 'monthly',
      priority: 0.8,
    },
    {
      url: `${baseUrl}/sobre`,
      lastModified: new Date('2026-08-21'),
      changeFrequency: 'monthly',
      priority: 0.7,
    },
    {
      url: `${baseUrl}/termos`,
      lastModified: new Date('2026-08-21'),
      changeFrequency: 'yearly',
      priority: 0.3,
    },
    {
      url: `${baseUrl}/privacidade`,
      lastModified: new Date('2026-08-21'),
      changeFrequency: 'yearly',
      priority: 0.3,
    },
    {
      url: `${baseUrl}/login`,
      lastModified: new Date('2026-08-21'),
      changeFrequency: 'yearly',
      priority: 0.5,
    },
    {
      url: `${baseUrl}/register`,
      lastModified: new Date('2026-08-21'),
      changeFrequency: 'yearly',
      priority: 0.6,
    },
  ];
}
