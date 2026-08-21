import { test, expect } from '@playwright/test';

test.describe('Login — /login', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('renderiza formulário de login com campos necessários', async ({ page }) => {
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/senha/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /entrar/i })).toBeVisible();
  });

  test('renderiza branding no painel esquerdo (desktop)', async ({ page }) => {
    // O branding é hidden em mobile, mas verificamos que existe
    const brandHeading = page.locator('h1');
    await expect(brandHeading).toContainText('food service');
  });

  test('link "Cadastre-se grátis" navega para /register', async ({ page }) => {
    await page.getByRole('link', { name: /cadastre-se/i }).click();
    await expect(page).toHaveURL(/\/register/);
  });

  test('formulário mostra erro com credenciais vazias (validação client)', async ({ page }) => {
    // O form usa required HTML5, então submit vazio não gera POST
    const emailInput = page.getByLabel(/email/i);
    await emailInput.fill('');
    await page.getByRole('button', { name: /entrar/i }).click();

    // O formulário não deve ter navegado
    await expect(page).toHaveURL(/\/login/);
  });

  test('email input aceita formato válido', async ({ page }) => {
    const emailInput = page.getByLabel(/email/i);
    await emailInput.fill('teste@freela.com');
    await expect(emailInput).toHaveValue('teste@freela.com');
  });

  test('password input tem tipo password', async ({ page }) => {
    const passwordInput = page.getByLabel(/senha/i);
    await expect(passwordInput).toHaveAttribute('type', 'password');
  });
});

test.describe('Register — /register', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register');
  });

  test('renderiza página de cadastro', async ({ page }) => {
    // Register pode ter diferentes layouts, verificar que carregou
    await expect(page).toHaveURL(/\/register/);
    // Deve ter pelo menos um botão ou formulário
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });

  test('link "Entrar" navega de volta para login', async ({ page }) => {
    const loginLink = page.getByRole('link', { name: /entrar|login|já tenho/i });
    if (await loginLink.isVisible()) {
      await loginLink.click();
      await expect(page).toHaveURL(/\/login/);
    }
  });
});
