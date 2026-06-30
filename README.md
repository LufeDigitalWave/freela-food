# freela-food

Marketplace bidirecional para freelancers de food service (garçom, barman, cozinheiro, auxiliar) e estabelecimentos que precisam contratar pontualmente.

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+PostGIS-336791?style=flat-square&logo=postgresql)
![Tests](https://img.shields.io/badge/testes-128%20integração-brightgreen?style=flat-square)
![mypy](https://img.shields.io/badge/mypy-strict-blue?style=flat-square)
![License](https://img.shields.io/badge/licença-MIT-green?style=flat-square)

## O que é

O **freela-food** conecta profissionais de food service a estabelecimentos para contratações avulsas — eventos, plantões, substituições. O diferencial é o modelo **bidirecional**:

- **Fluxo A** — Estabelecimento publica vaga → freelancers se candidatam → aceite transacional com cascade-reject automático.
- **Fluxo B** — Estabelecimento busca freelancers por proximidade + skill → convite direto → aceite → contrato.

Ambos os fluxos convergem em um `ServiceContract` com ciclo de vida gerenciado por worker ARQ e avaliação mútua anti-retaliação.

## Destaques técnicos

- **Geolocalização real** — busca `ST_DWithin` (PostGIS) por raio em km; índices GiST em perfis e vagas
- **LGPD desde o zero** — CPF/CNPJ cifrados via `pgcrypto` + chave separada do JWT; `GET /me/export`, `DELETE /me` (soft-delete com grace period + purge cron), filtro structlog que redige PII de todos os logs
- **Audit log automático** — decorator `@audit` em todas as mutações de entidade sensível
- **Workers async** — ARQ (Redis-backed) para ciclo de vida de contratos (`scheduled → in_progress → completed`), purge de usuários e lembretes
- **Auth própria** — JWT HS256 (PyJWT) + bcrypt ≥ cost 12; sem dependência de Supabase Auth no MVP
- **Storage S3-compatible** — avatares via MinIO, upload multipart com validação de tipo e tamanho
- **Type-safe** — `mypy --strict` + Ruff + Black; zero `Any` não justificado
- **128 testes de integração** — pytest-asyncio contra banco real; todos os fluxos de negócio cobertos de ponta a ponta

## Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.12 + **uv** |
| Framework | FastAPI + Pydantic v2 |
| ORM / Migrations | SQLAlchemy 2.x async + **Alembic** |
| Banco | **Postgres 15 + PostGIS** |
| Auth | Custom JWT HS256 (PyJWT) + passlib[bcrypt] |
| Cache / Workers | Redis 7 + **ARQ** |
| Storage | MinIO / S3-compatible |
| Criptografia PII | pgcrypto (pgp_sym_encrypt) |
| Observabilidade | structlog (filtro PII) + Sentry |
| Qualidade | mypy strict · Ruff · Black · pre-commit |
| Testes | pytest + pytest-asyncio + httpx |

## Endpoints implementados

```
Auth
  POST /v1/auth/register
  POST /v1/auth/login
  GET  /v1/auth/me

Perfil & LGPD
  GET/PATCH /v1/me
  POST/PATCH /v1/me/freelancer-profile
  POST/PATCH /v1/me/establishment-profile
  POST      /v1/me/avatar
  GET       /v1/me/export
  DELETE    /v1/me

Vagas
  POST/GET         /v1/jobs
  GET/PATCH/DELETE /v1/jobs/{id}
  POST             /v1/jobs/{id}/cancel
  GET              /v1/jobs/search          ← PostGIS ST_DWithin + filtros

Candidaturas (Fluxo A)
  POST /v1/jobs/{id}/applications
  GET  /v1/jobs/{id}/applications
  POST /v1/applications/{id}/accept
  POST /v1/applications/{id}/reject
  POST /v1/applications/{id}/withdraw

Convites (Fluxo B)
  POST /v1/invitations
  GET  /v1/invitations
  GET  /v1/invitations/{id}
  POST /v1/invitations/{id}/accept
  POST /v1/invitations/{id}/decline
  POST /v1/invitations/{id}/withdraw

Contratos
  GET  /v1/contracts
  GET  /v1/contracts/{id}
  POST /v1/contracts/{id}/cancel
  POST /v1/contracts/{id}/no-show

Notificações
  GET  /v1/notifications
  POST /v1/notifications/{id}/read
```

## Setup local

### Pré-requisitos

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Postgres 15 com extensão PostGIS
- Redis 7
- MinIO (opcional — só para upload de avatar)

A forma mais rápida de subir as dependências:

```bash
docker run -d --name pg \
  -e POSTGRES_USER=freela -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=freela_food \
  -p 5432:5432 postgis/postgis:15-3.4

docker run -d --name redis -p 6379:6379 redis:7-alpine
```

### Instalar e rodar

```bash
git clone https://github.com/LufeDigitalWave/freela-food.git
cd freela-food

uv sync
cp .env.example .env
# edite DATABASE_URL, REDIS_URL e JWT_SECRET no .env

uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

API disponível em `http://localhost:8000` · Docs em `http://localhost:8000/docs`.

### Rodar worker ARQ (opcional em dev)

```bash
uv run arq app.workers.arq_worker.WorkerSettings
```

### Testes

```bash
uv run pytest -v
```

Os testes rodam contra banco real — exige `DATABASE_URL` e `REDIS_URL` válidos no `.env`.

## Estrutura do projeto

```
app/
  api/v1/           # Routers FastAPI por domínio
  core/             # Config, segurança, DB, logging, exceções
  domain/
    models/         # Modelos SQLAlchemy
    schemas/        # Pydantic (XxxCreate / XxxUpdate / XxxRead)
    repositories/   # Acesso a dados — retornam models
    services/       # Regras de negócio — retornam schemas
  workers/          # WorkerSettings ARQ + tasks
  utils/
  main.py
alembic/versions/   # Migrations versionadas
tests/integration/  # 128 testes de integração
docs/adr/           # Decisões arquiteturais registradas
```

## Modelo de domínio (resumido)

```
User → FreelancerProfile | EstablishmentProfile
JobPosting → Application[] → ServiceContract   (Fluxo A)
              Invitation  → ServiceContract     (Fluxo B)
ServiceContract → Review (visibilidade: ambos avaliam OU 7 dias do primeiro)
AuditLog  ← toda mutação sensível
Notification ← eventos de negócio
```

## Roadmap

- [x] Sprint 0 — Scaffolding, auth, migrations, audit log
- [x] Sprint 1 — Perfis, avatar, LGPD endpoints
- [x] Sprint 2 — Vagas, busca geoespacial
- [x] Sprint 3 — Fluxo A completo (candidatura → contrato → ciclo de vida)
- [x] Sprint 4 — Fluxo B (busca direta → convite → contrato) ← em progresso
- [ ] Sprint 5 — Avaliações com regra de visibilidade anti-retaliação
- [ ] Sprint 6 — Notificações in-app + painel admin
- [ ] Sprint 7+ — Pagamento, matching IA, app mobile

## Licença

MIT
