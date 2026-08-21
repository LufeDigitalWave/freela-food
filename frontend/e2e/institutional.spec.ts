import { test, expect } from '@playwright/test';

test.describe('Como Funciona — /como-funciona', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/como-funciona');
  });

  test('renderiza título principal', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Como funciona');
  });

  test('renderiza seção Fluxo A com 3 passos', async ({ page }) => {
    await expect(page.getByText('Vagas públicas')).toBeVisible();
    await expect(page.getByText('Publicar vaga')).toBeVisible();
    await expect(page.getByText('Candidatar-se')).toBeVisible();
    await expect(page.getByText('Contrato firmado')).toBeVisible();
  });

  test('renderiza seção Fluxo B com 3 passos', async ({ page }) => {
    await expect(page.getByText('Convites diretos')).toBeVisible();
    await expect(page.getByText('Buscar freelancers')).toBeVisible();
    await expect(page.getByText('Enviar convite')).toBeVisible();
    await expect(page.getByText('Contrato direto')).toBeVisible();
  });

  test('renderiza seção anti-retaliação', async ({ page }) => {
    await expect(page.getByText('Anti-retaliação')).toBeVisible();
    await expect(page.getByText(/ambos avaliarem/i)).toBeVisible();
  });

  test('CTA final navega para /register', async ({ page }) => {
    await page.getByRole('link', { name: /crie sua conta/i }).click();
    await expect(page).toHaveURL(/\/register/);
  });

  test('navbar navega de volta para /', async ({ page }) => {
    await page.locator('header').getByRole('link').first().click();
    await expect(page).toHaveURL('/');
  });
});

test.describe('Sobre — /sobre', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/sobre');
  });

  test('renderiza título', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Sobre o freela-food');
  });

  test('renderiza seção de valores com 3 cards', async ({ page }) => {
    await expect(page.getByText('Transparência')).toBeVisible();
    await expect(page.getByText('Qualidade técnica')).toBeVisible();
    await expect(page.getByText('Comunidade')).toBeVisible();
  });

  test('renderiza seção open source com link GitHub', async ({ page }) => {
    await expect(page.locator('h2', { hasText: 'Open Source' })).toBeVisible();
    const githubLink = page.locator('a[href*="github.com"]').first();
    await expect(githubLink).toBeVisible();
  });
});

test.describe('Termos — /termos', () => {
  test('renderiza título e conteúdo legal', async ({ page }) => {
    await page.goto('/termos');
    await expect(page.locator('h1')).toContainText('Termos de Uso');
    await expect(page.getByText('Aceitação dos termos')).toBeVisible();
    await expect(page.getByText('Descrição do serviço')).toBeVisible();
    await expect(page.getByText('Cadastro e contas')).toBeVisible();
  });
});

test.describe('Privacidade — /privacidade', () => {
  test('renderiza título e seções LGPD', async ({ page }) => {
    await page.goto('/privacidade');
    await expect(page.locator('h1')).toContainText('Política de Privacidade');
    await expect(page.getByText('Dados coletados')).toBeVisible();
    await expect(page.getByText('Seus direitos (LGPD)')).toBeVisible();
    await expect(page.getByText('Criptografia e segurança')).toBeVisible();
  });
});
