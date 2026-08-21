import { test, expect } from '@playwright/test';

test.describe('PWA & Offline', () => {
  test('manifest.json é acessível e válido', async ({ page }) => {
    const response = await page.goto('/manifest.json');
    expect(response?.status()).toBe(200);

    const manifest = await response?.json();
    expect(manifest.name).toBe('freela-food');
    expect(manifest.short_name).toBe('freela-food');
    expect(manifest.display).toBe('standalone');
    expect(manifest.theme_color).toBe('#e85d2c');
    expect(manifest.icons).toBeDefined();
    expect(manifest.icons.length).toBeGreaterThan(0);
  });

  test('service worker está registrado (arquivo existe)', async ({ page }) => {
    const response = await page.goto('/sw.js');
    expect(response?.status()).toBe(200);
    const text = await response?.text();
    expect(text).toContain('CACHE_NAME');
    expect(text).toContain('freela-food-v1');
  });

  test('offline page renderiza corretamente', async ({ page }) => {
    await page.goto('/offline');
    await expect(page.locator('h1')).toContainText('offline');
    await expect(page.getByRole('button', { name: /tentar novamente/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /voltar/i })).toBeVisible();
  });
});

test.describe('Performance Basics', () => {
  test('landing page carrega em < 5s', async ({ page }) => {
    const start = Date.now();
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    const loadTime = Date.now() - start;
    expect(loadTime).toBeLessThan(5000);
  });

  test('como-funciona carrega em < 3s', async ({ page }) => {
    const start = Date.now();
    await page.goto('/como-funciona', { waitUntil: 'domcontentloaded' });
    const loadTime = Date.now() - start;
    expect(loadTime).toBeLessThan(3000);
  });

  test('nenhum recurso retorna 404 nas páginas públicas', async ({ page }) => {
    const failedRequests: string[] = [];
    page.on('response', (response) => {
      if (response.status() === 404 && !response.url().includes('favicon')) {
        failedRequests.push(response.url());
      }
    });

    await page.goto('/');
    await page.goto('/como-funciona');
    await page.goto('/sobre');

    expect(failedRequests).toHaveLength(0);
  });

  test('páginas públicas não têm erros de console', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/');
    await page.goto('/como-funciona');
    await page.goto('/sobre');

    // Filtrar erros de service worker (esperados em dev)
    const criticalErrors = errors.filter(
      (e) => !e.includes('service worker') && !e.includes('sw.js')
    );
    expect(criticalErrors).toHaveLength(0);
  });
});
