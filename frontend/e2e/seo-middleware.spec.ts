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
    // Navegar e verificar que conteúdo está presente imediatamente
    const response = await page.goto('/');
    const html = await response?.text();
    // Server-rendered: conteúdo deve estar no HTML inicial
    expect(html).toContain('food service');
    expect(html).toContain('Comece agora');
    // Não deve ter spinner de loading
    expect(html).not.toContain('Carregando...');
  });

  test('como-funciona tem structured headings (h1 → h2)', async ({ page }) => {
    await page.goto('/como-funciona');
    const h1 = await page.locator('h1').textContent();
    expect(h1).toContain('Como funciona');

    const h2Count = await page.locator('h2').count();
    expect(h2Count).toBeGreaterThanOrEqual(3); // Fluxo A, Fluxo B, Depois
  });

  test('sobre page tem structured headings', async ({ page }) => {
    await page.goto('/sobre');
    const h1 = await page.locator('h1').textContent();
    expect(h1).toContain('freela-food');

    const h2Count = await page.locator('h2').count();
    expect(h2Count).toBeGreaterThanOrEqual(2);
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
