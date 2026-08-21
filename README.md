# freela-food

Marketplace bidirecional para freelancers de food service (garçom, barman, cozinheiro, auxiliar) e estabelecimentos que precisam contratar pontualmente.

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+PostGIS-336791?style=flat-square&logo=postgresql)
![Tests](https://img.shields.io/badge/Backend_testes-224-brightgreen?style=flat-square)
![E2E](https://img.shields.io/badge/E2E_testes-44-brightgreen?style=flat-square)
![Routes](https://img.shields.io/badge/Rotas-32-blue?style=flat-square)
![mypy](https://img.shields.io/badge/mypy-strict-blue?style=flat-square)
![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?style=flat-square&logo=github-actions)
![PWA](https://img.shields.io/badge/PWA-Ready-orange?style=flat-square&logo=pwa)
![License](https://img.shields.io/badge/licença-MIT-green?style=flat-square)

## O que é

O **freela-food** conecta profissionais de food service a estabelecimentos para contratações avulsas — eventos, plantões, substituições. Modelo **bidirecional**:

- **Fluxo A** — Estabelecimento publica vaga → freelancers se candidatam → aceite transacional.
- **Fluxo B** — Estabelecimento busca freelancers por proximidade → convite direto → contrato.

## Destaques

- **Geolocalização** — PostGIS `ST_DWithin` + geocoding Nominatim
- **Matching IA** — scoring multi-fator (proximity, skill, rating, reliability, experience, repeat-hire)
- **Reviews anti-retaliação** — visíveis só após ambos avaliarem ou 7 dias
- **Moderação** — denúncias + fila admin + hide reviews
- **Pagamentos** — registro + confirmação Pix + disputa
- **LGPD** — CPF/CNPJ cifrados (pgcrypto), export, soft-delete + purge
- **Admin dashboard** — stats, users, audit log, moderação
- **Frontend premium** — Next.js + Tailwind + shadcn/ui, role-based UI
- **224 testes backend** — integração + unitários, mypy --strict, Ruff
- **44 E2E tests** — Playwright (landing, auth, nav, mobile, a11y, PWA, performance)
- **PWA ready** — Service Worker, manifest.json, offline support
- **Accessibility** — WCAG AA: skip-links, aria-labels, landmarks, semantic HTML
- **CI/CD** — GitHub Actions: lint + type-check + tests + E2E + build
- **Observability** — Sentry error tracking, structlog, PII filter
- **Performance** — gzip, AVIF/WebP, font-display swap, tree-shaking

## Stack

| Backend | Frontend |
|---|---|
| Python 3.12 + uv | Next.js 16 (App Router) |
| FastAPI + Pydantic v2 | React 19 + TypeScript |
| SQLAlchemy 2 async + Alembic | Tailwind CSS v4 + shadcn/ui |
| Postgres 15 + PostGIS | Inter + Instrument Serif (next/font) |
| Redis 7 + ARQ | Responsive, mobile-first design |
| MinIO (S3) | 32 rotas (landing + dashboard + admin) |
| JWT HS256 + bcrypt | 37 E2E tests (Playwright) |
| structlog + Sentry | PWA ready (manifest + SW) |

## Como rodar

### Backend

```bash
git clone https://github.com/LufeDigitalWave/freela-food.git
cd freela-food
uv sync
cp .env.example .env   # editar credenciais
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

### Docker (deploy)

```bash
docker compose -f docker-compose.deploy.yml build
docker compose -f docker-compose.deploy.yml up -d
```

## Testes

```bash
# Backend (224 testes integração)
uv run pytest          # all tests
uv run ruff check .    # lint
uv run mypy app/       # type check

# Frontend (44 E2E tests)
cd frontend
npx playwright test          # headless
npx playwright test --ui     # visual UI

# Bundle size analysis
npm run build && node scripts/perf-check.js
```

## Documentação Adicional

- [CHANGELOG.md](./CHANGELOG.md) — histórico de releases
- [CONTRIBUTING.md](./CONTRIBUTING.md) — como contribuir
- [QUALITY_CHECKLIST.md](./QUALITY_CHECKLIST.md) — go/no-go criteria
- [docs/RUNBOOKS.md](./docs/RUNBOOKS.md) — operações (deploy, backup, restore, rollback)
- [docs/OBSERVABILITY.md](./docs/OBSERVABILITY.md) — Sentry, logging, metrics
- [frontend/PWA.md](./frontend/PWA.md) — Progressive Web App guide
- [frontend/e2e/README.md](./frontend/e2e/README.md) — test suite documentation

## Endpoints (~62)

<details>
<summary>Ver lista completa</summary>

```
Auth:           POST register, POST login, POST refresh, GET me
Perfil:         GET/PATCH me, POST/PATCH profiles, POST avatar, GET export, DELETE me
Vagas:          CRUD jobs, GET search, GET matches
Candidaturas:   POST apply, GET list, POST accept/reject/withdraw
Convites:       POST create, GET list, POST accept/decline
Contratos:      GET list, GET detail, POST cancel
Reviews:        POST create, GET by-contract, GET me/reviews, GET public, GET stats
Pagamentos:     GET payment, POST confirm, POST dispute, GET me/payments
Notificações:   GET list, GET count, POST read, POST read-all, DELETE
Reports:        POST create, GET mine
Admin:          GET stats, users, audit-log, reports, payments; POST deactivate/reactivate/resolve/hide/unhide
Health:         GET /health (liveness + readiness)
Webhooks:       POST /webhooks/asaas
```

</details>

## Arquitetura

```
app/api/v1/        → Routers FastAPI (62 endpoints)
app/domain/models/ → SQLAlchemy models
app/domain/schemas/→ Pydantic schemas
app/domain/services/→ Business logic
app/workers/       → ARQ cron jobs
frontend/src/app/  → Next.js pages (30 routes)
frontend/src/components/ → UI components (shadcn/ui)
alembic/versions/  → 8 migrations
tests/             → 224 testes
.github/workflows/ → CI pipeline
```

## Roadmap

- ✅ Sprint 0-4: Auth, Perfis, LGPD, Vagas, Fluxo A+B
- ✅ Sprint 5: Reviews anti-retaliação
- ✅ Sprint 6: Notificações + Admin
- ✅ Sprint 7: Matching engine
- ✅ Sprint 8: Moderação
- ✅ Sprint 9: Pagamentos
- ✅ Sprint 10: Frontend (freelancer + establishment)
- ✅ Sprint 11: Deploy infra (Docker, Caddy, healthcheck)
- ✅ Sprint 12: Auth/security (refresh tokens, rate limit, CORS)
- ✅ Sprint 13: Gateway Pix skeleton (Asaas)
- ✅ Sprint 14: Admin frontend (6 páginas)
- ✅ Sprint 15: Landing page pública + páginas institucionais
- ✅ Sprint 16: E2E tests Playwright (37 tests)
- ✅ Sprint 17: PWA (manifest, SW, offline) + WCAG AA accessibility
- ✅ CI/CD: GitHub Actions (lint + type-check + tests + build + E2E)
- 🔜 Domínio + HTTPS (Caddy TLS automático)
- 🔜 Lighthouse performance optimization (target ≥ 90)
- 🔜 Closed beta with real users

## Licença

MIT
