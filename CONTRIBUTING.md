# Contribuindo para o freela-food

Obrigado por considerar contribuir! Este projeto é open-source (MIT) e aceita contribuições.

## Setup de Desenvolvimento

### Requisitos

- Python 3.12+ (recomendamos [uv](https://docs.astral.sh/uv/))
- Node.js 20+ (LTS)
- PostgreSQL 15 + PostGIS
- Redis 7

### Backend

```bash
git clone https://github.com/LufeDigitalWave/freela-food.git
cd freela-food
uv sync              # instala todas deps (dev + prod)
cp .env.example .env # editar com credenciais locais
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/v1" > .env.local
npm run dev
```

### Testes

```bash
# Backend (224 testes)
uv run pytest

# Frontend E2E (37 testes Playwright)
cd frontend
npx playwright test

# Lint + type check
uv run ruff check .
uv run mypy app/ --strict
cd frontend && npm run lint
```

## Workflow

1. Fork o repositório
2. Crie uma branch: `git checkout -b feat/minha-feature`
3. Implemente com testes
4. Rode a validação completa:
   ```bash
   uv run ruff check . && uv run mypy app/ --strict && uv run pytest
   cd frontend && npm run lint && npm run build && npx playwright test
   ```
5. Commit (Conventional Commits): `git commit -m "feat: minha feature"`
6. Push e abra PR

## Convenções

### Código

- **Python**: tipagem completa (mypy --strict), docstrings em português, identificadores em inglês
- **TypeScript**: strict mode, sem `any` (exceto onde justificado)
- **Commits**: [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `refactor:`, etc.)
- **Branches**: `feat/<nome>`, `fix/<nome>`, `docs/<nome>`

### Arquitetura

- **Endpoints** nunca acessam DB diretamente — passam por services
- **Services** retornam schemas Pydantic
- **Repositories** retornam models SQLAlchemy
- **Migrations** nunca editam uma já aplicada — crie uma nova
- **Decisões arquiteturais** precisam de ADR em `docs/adr/`

### Acessibilidade

- Toda interação precisa funcionar com teclado
- Links/buttons com ícone precisam de `aria-label`
- Ícones decorativos precisam de `aria-hidden="true"`
- Formulários precisam de `<Label htmlFor="id">`
- Headings seguem hierarquia (h1 → h2 → h3)

### Segurança

- Zero secrets no código (use `.env`)
- Inputs validados (Pydantic)
- SQL parameterizado (SQLAlchemy)
- PII nunca em logs (structlog filter)
- CPF/RG criptografados em repouso

## O que NÃO aceitar

- Mudanças de stack sem ADR aprovado
- PRs sem testes
- Código com `type: ignore` sem justificativa
- Remoção de testes existentes
- Secrets ou dados reais

## Reportar Bugs

Abra uma issue com:
1. Passos para reproduzir
2. Comportamento esperado vs real
3. Screenshots (se visual)
4. Browser/versão (se frontend)

## Prioridades (agosto 2026)

1. Performance (Lighthouse ≥ 90)
2. E2E tests para fluxos autenticados
3. Multi-language (i18n)
4. Real payment integration
5. Mobile app (PWA refinement)

## Licença

Ao contribuir, você aceita que sua contribuição será licenciada sob a mesma licença do projeto (MIT).
