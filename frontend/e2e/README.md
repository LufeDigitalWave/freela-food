# Playwright E2E Tests

Suite de testes end-to-end para validar fluxos críticos do freela-food.

## Setup

```bash
npm install -D @playwright/test
npx playwright install
```

## Rodar testes

```bash
# Modo headless
npm run test:e2e

# Modo UI (recomendado para desenvolvimento)
npm run test:e2e:ui

# Teste específico
npx playwright test landing.spec.ts

# Debug mode
npx playwright test --debug
```

## Cobertura

### Landing Page (`landing.spec.ts`)
- ✓ Hero renderizado corretamente
- ✓ Navbar com links de navegação
- ✓ Botões CTA funcionais
- ✓ Seção de features (4 cards)
- ✓ Seção de stats
- ✓ Footer com links institucionais
- ✓ Navegação entre páginas

### Páginas Institucionais (`institutional.spec.ts`)
- ✓ Como Funciona (Fluxo A + B)
- ✓ Sobre (valores + open source)
- ✓ Termos de Uso
- ✓ Política de Privacidade

### Autenticação (`auth.spec.ts`)
- ✓ Formulário de login
- ✓ Validação de inputs
- ✓ Página de registro
- ✓ Navegação auth ↔ public

### Navegação e UX (`navigation.spec.ts`)
- ✓ Navegação entre páginas públicas
- ✓ Responsividade mobile (375px)
- ✓ Acessibilidade básica (títulos, aria-labels)
- ✓ Navegação por teclado

## Futuro: Testes autenticados

Quando o backend estiver acessível (IP whitelist atualizado), adicionar:

- `dashboard.spec.ts` — Fluxo freelancer (jobs, applications, contracts, reviews)
- `establishment.spec.ts` — Fluxo establishment (criar vagas, convites, candidatos)
- `admin.spec.ts` — Painel admin (users, audit log, moderação)

## CI/CD

Os testes rodam no GitHub Actions (`.github/workflows/ci.yml`) após `npm run build` passar.

## Arquivos gerados

- `playwright-report/` — Relatório HTML após cada run
- `test-results/` — Screenshots/traces em caso de falha
- `.auth/` — Cookies de autenticação (se usar login)
