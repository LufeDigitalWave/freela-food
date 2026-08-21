import { test, expect } from '@playwright/test';

test.describe('Landing Page — /', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Esperar hero carregar (client-side render)
    await page.waitForSelector('h1', { timeout: 15000 });
  });

  test('renderiza hero com título principal', async ({ page }) => {
    const heading = page.locator('h1');
    await expect(heading).toContainText('food service');
  });

  test('renderiza navbar com links de navegação', async ({ page }) => {
    // Links "Como funciona" e "Sobre" existem na página (podem ser hidden em mobile)
    const comoFunciona = page.locator('a[href="/como-funciona"]');
    await expect(comoFunciona.first()).toBeAttached();
    const sobre = page.locator('a[href="/sobre"]');
    await expect(sobre.first()).toBeAttached();
  });

  test('renderiza botões CTA (cadastro e como funciona)', async ({ page }) => {
    await expect(page.locator('a[href="/register"]').first()).toBeVisible();
    await expect(page.locator('a[href="/como-funciona"]').first()).toBeAttached();
  });

  test('renderiza seção de features com 4 cards', async ({ page }) => {
    const features = page.locator('.card-lift');
    await expect(features).toHaveCount(4);
  });

  test('renderiza seção de stats', async ({ page }) => {
    await expect(page.getByText('224')).toBeVisible();
    await expect(page.getByText('62')).toBeVisible();
  });

  test('renderiza footer com links institucionais', async ({ page }) => {
    const footer = page.locator('footer');
    await expect(footer).toBeVisible();
    await expect(footer.locator('a[href="/termos"]').first()).toBeVisible();
    await expect(footer.locator('a[href="/privacidade"]').first()).toBeVisible();
    await expect(footer.locator('a[href*="github.com"]')).toBeVisible();
  });

  test('CTA "Cadastre-se grátis" navega para /register', async ({ page }) => {
    await page.locator('a[href="/register"]').first().click();
    await expect(page).toHaveURL(/\/register/);
  });

  test('link "Como funciona" navega para /como-funciona', async ({ page }) => {
    await page.locator('a[href="/como-funciona"]').first().click();
    await expect(page).toHaveURL(/\/como-funciona/);
  });
});
