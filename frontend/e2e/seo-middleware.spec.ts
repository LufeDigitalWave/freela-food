import { test, expect } from '@playwright/test';

test.describe('SEO — Server-rendered landing', () => {
  test('landing page tem OpenGraph meta tags', async ({ page }) => {
    await page.goto('/');
    const ogTitle = await page.locator('meta[property="og:title"]').getAttribute('content');
    const ogDesc = await page.locator('meta[property="og:description"]').getAttribute('content');
    const ogType = await page.locator('meta[property="og:type"]').getAttribute('content');

    expect(ogTitle).toContain('freela-food');
    expect(ogDesc).toBeTruthy();
    expect(ogType).toBe('website');
  });

  test('landing page tem description meta tag', async ({ page }) => {
    await page.goto('/');
    const desc = await page.locator('meta[name="description"]').getAttribute('content');
    expect(desc).toContain('gastronomia');
  });

  test('landing page é pre-rendered (sem loading spinner)', async ({ page }) => {
    const response = await page.goto('/');
    const html = await response?.text();
    expect(html).toContain('food service');
    expect(html).toContain('Comece agora');
    expect(html).not.toContain('Carregando...');
  });

  test('como-funciona tem structured headings (h1 → h2)', async ({ page }) => {
    await page.goto('/como-funciona');
    const h1 = await page.locator('h1').textContent();
    expect(h1).toContain('Como funciona');

    const h2Count = await page.locator('h2').count();
    expect(h2Count).toBeGreaterThanOrEqual(3);
  });

  test('sobre page tem structured headings', async ({ page }) => {
    await page.goto('/sobre');
    const h1 = await page.locator('h1').textContent();
    expect(h1).toContain('freela-food');

    const h2Count = await page.locator('h2').count();
    expect(h2Count).toBeGreaterThanOrEqual(2);
  });

  test('robots.txt é acessível e bloqueia dashboard', async ({ page }) => {
    const response = await page.goto('/robots.txt');
    expect(response?.status()).toBe(200);
    const text = await response?.text();
    expect(text).toContain('Disallow: /dashboard');
    expect(text).toContain('Allow: /');
    expect(text).toContain('Sitemap:');
  });

  test('sitemap.xml é acessível e lista páginas públicas', async ({ page }) => {
    const response = await page.goto('/sitemap.xml');
    expect(response?.status()).toBe(200);
    const text = await response?.text();
    expect(text).toContain('<urlset');
    expect(text).toContain('/como-funciona');
    expect(text).toContain('/sobre');
    expect(text).toContain('priority');
  });
});

test.describe('Middleware — auth redirect', () => {
  test('landing page não redireciona sem cookie', async ({ page }) => {
    await page.goto('/');
    // Deve ficar na landing (não redireciona sem access_token cookie)
    await expect(page).toHaveURL('/');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('landing page com cookie access_token redireciona para /dashboard', async ({ page }) => {
    // Setar cookie antes de navegar
    await page.context().addCookies([{
      name: 'access_token',
      value: 'fake-token-for-test',
      domain: 'localhost',
      path: '/',
    }]);

    await page.goto('/');
    // Middleware deve redirecionar para /dashboard
    await expect(page).toHaveURL(/\/dashboard/);
  });
});
