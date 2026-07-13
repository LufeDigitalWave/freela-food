# freela-food

Marketplace bidirecional para freelancers de food service (garçom, barman, cozinheiro, auxiliar) e estabelecimentos que precisam contratar pontualmente.

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-14+-black?style=flat-square&logo=next.js)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+PostGIS-336791?style=flat-square&logo=postgresql)
![Tests](https://img.shields.io/badge/testes-224-brightgreen?style=flat-square)
![mypy](https://img.shields.io/badge/mypy-strict-blue?style=flat-square)
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
- **224 testes** — integração + unitários, mypy --strict, Ruff

## Stack

| Backend | Frontend |
|---|---|
| Python 3.12 + uv | Next.js 14 (App Router) |
| FastAPI + Pydantic v2 | TypeScript |
| SQLAlchemy 2 async + Alembic | Tailwind CSS + shadcn/ui |
| Postgres 15 + PostGIS | Inter + Instrument Serif |
| Redis 7 + ARQ | Axios |
| MinIO (S3) | Docker standalone |
| JWT HS256 + bcrypt | |

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
uv run pytest          # 224 testes
uv run ruff check .    # lint
uv run mypy app/       # type check
```

## Endpoints (~50)

<details>
<summary>Ver lista completa</summary>

```
Auth:           POST register, POST login, GET me
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
```

</details>

## Arquitetura

```
app/api/v1/        → Routers FastAPI
app/domain/models/ → SQLAlchemy models
app/domain/schemas/→ Pydantic schemas
app/domain/services/→ Business logic
app/workers/       → ARQ cron jobs
frontend/src/app/  → Next.js pages
frontend/src/components/ → UI components
alembic/versions/  → 8 migrations
tests/             → 224 testes
```

## Roadmap

- ✅ Sprint 0-4: Auth, Perfis, LGPD, Vagas, Fluxo A+B
- ✅ Sprint 5: Reviews anti-retaliação
- ✅ Sprint 6: Notificações + Admin
- ✅ Sprint 7: Matching engine
- ✅ Sprint 8: Moderação
- ✅ Sprint 9: Pagamentos
- ✅ Sprint 10: Frontend (freelancer + establishment)
- 🔜 Gateway Pix real, mobile responsive, refresh tokens

## Licença

MIT
