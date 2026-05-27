# freela-food

Marketplace bidirecional para freelancers de food service (garçom, barman, cozinheiro, auxiliar) e estabelecimentos que precisam contratar pontualmente.

> Em desenvolvimento — Sprint 0 (scaffolding).

Veja [CLAUDE.md](./CLAUDE.md) para visão, escopo, stack, modelo de domínio, convenções e roadmap.

## Pré-requisitos

- Python 3.12 (uv gerencia)
- [uv](https://docs.astral.sh/uv/)
- Acesso de rede ao Postgres+Redis da VPS (IP whitelistado pelo infra owner)

## Setup

```bash
uv sync
cp .env.example .env
# editar DATABASE_URL, REDIS_URL, JWT_SECRET (peça pro infra owner)
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## Licença

Proprietário.
