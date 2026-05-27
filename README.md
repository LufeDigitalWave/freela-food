# freela-food

Marketplace bidirecional para freelancers de food service (garçom, barman, cozinheiro, auxiliar) e estabelecimentos que precisam contratar pontualmente.

> Em desenvolvimento — Sprint 0 (scaffolding).

Veja [CLAUDE.md](./CLAUDE.md) para visão, escopo, stack, modelo de domínio, convenções e roadmap.

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/)
- [uv](https://docs.astral.sh/uv/) (package manager Python)
- [Supabase CLI](https://supabase.com/docs/guides/cli)

## Setup

Instruções completas serão adicionadas ao final da Sprint 0. Visão geral:

```bash
uv sync
cp .env.example .env
supabase start
docker-compose up -d redis
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## Licença

Proprietário.
