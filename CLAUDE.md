# freela-food

> Marketplace bidirecional pra freelancers de restaurantes e bares (garçom, barman, cozinheiro, auxiliar, etc.) e estabelecimentos que precisam contratar pontualmente.

---

## 1. Visão e diferenciais

- **Quem usa**: freelancers do setor de food service + bares/restaurantes que precisam de mão de obra avulsa (eventos, plantões, substituições).
- **Modelo de match**: bidirecional
  - Estabelecimento publica vaga → freelancers se candidatam.
  - Estabelecimento busca freelancers disponíveis e envia convite direto.
- **Confiança**: avaliação mútua após conclusão do serviço.
- **Cobertura**: Brasil, LGPD-compliant desde o dia zero.

## 2. Escopo

### MVP
1. Cadastro e auth (freelancer, estabelecimento, admin) — **custom JWT HS256** (Supabase Auth deferido).
2. Perfis completos (freela: skills, certificações, disponibilidade, raio de atuação; estabelecimento: endereço, tipo, horário).
3. CRUD de vagas com filtros (categoria, data, geolocalização, faixa de pagamento).
4. Fluxo A: candidatura → aceite → confirmação.
5. Fluxo B: busca de freelancers disponíveis → convite direto → aceite.
6. Avaliação mútua pós-serviço (1–5 + comentário).
7. Histórico de trabalhos.
8. Notificações in-app.

### Fora do MVP
Pagamento (Pix/Stripe Connect), matching com IA, moderação automatizada, chat de suporte, apps nativos.

### Explicitamente fora de escopo
Carteira interna / saldo; contratos formais (só registro do acordo).

## 3. Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.12 |
| Package manager | **uv** |
| Framework API | FastAPI |
| Validação | Pydantic v2 |
| ORM / Migrations | SQLAlchemy 2.x async + **Alembic** (única fonte de verdade do schema) |
| Banco | **Postgres 15 + PostGIS** |
| Auth | **Custom JWT HS256** (PyJWT) + bcrypt via `passlib[bcrypt]`. Tabela `users` própria. |
| Storage | **Deferido** — entra na Sprint 1+ quando precisar upload (provavelmente S3-compatible). |
| Cache / Filas | Redis 7 |
| Workers | **ARQ** (async-native, Redis-backed) |
| Testes | Pytest + pytest-asyncio + httpx |
| Lint/Format | Ruff + Black + mypy (strict) |
| Pre-commit | ruff + black + mypy + check-yaml |
| Containerização | Docker + docker-compose (pra deploy futuro, não usado em dev local) |
| Deploy alvo | Docker Compose / VPS |
| Observabilidade | structlog (com filtro PII) + Sentry |

### Decisões registradas (não revisitar sem ADR)
- **uv** sobre Poetry: performance e padrão atual.
- **Postgres puro na VPS** sobre Supabase: simplificar infra Sprint 0, evitar dependência cloud, reusar VPS própria. Trade-off aceito: refactor de `security.py` + tabela `users` quando migrar pra Supabase Auth (ou outro provider) no futuro.
- **Custom JWT HS256** sobre OAuth/Supabase Auth: cobre MVP sem dependência externa. Migração possível em sprints futuras.
- **Alembic** sobre migrations diretas: schema versionado em Python.
- **ARQ** sobre Celery: stack async-first, Redis disponível, config mínima.
- **PyJWT** sobre python-jose: jose tem CVEs abertos e está sem manutenção ativa.
- **passlib[bcrypt]** sobre argon2: padrão estabelecido, suficiente pra MVP.
- **`audit_log` desde Sprint 0**: backfill é impossível depois.

## 4. Modelo de domínio

```
User (custom, tabela própria)
 ├─ id (uuid), email, password_hash (bcrypt), role (freelancer|establishment|admin)
 ├─ created_at, updated_at, deleted_at
 │
 ├─ FreelancerProfile (1:1, opcional)
 │   ├─ Skills[] (M:N com SkillCategory)
 │   ├─ Certifications[]
 │   ├─ AvailabilitySlots[]
 │   └─ ServiceArea (geo: ponto + raio_km)
 │
 └─ EstablishmentProfile (1:1, opcional)
     ├─ Address (geo: ponto)
     ├─ EstablishmentType
     └─ OperatingHours

JobPosting
 ├─ establishment_id, skill_category_id
 ├─ start_at, end_at, hourly_rate, total_pay
 ├─ status: draft | open | filled | cancelled | completed
 └─ Applications[]

Application (Fluxo A)
 └─ status: pending | accepted | rejected | withdrawn

Invitation (Fluxo B)
 ├─ proposed_terms (jsonb)
 └─ status: pending | accepted | declined | expired

ServiceContract (consequência dos dois fluxos)
 ├─ agreed_terms, started_at, completed_at
 └─ status: scheduled | in_progress | completed | cancelled | disputed

Review (após contract.completed)
 ├─ stars (1-5), comment
 └─ visibility_rule: ambos avaliam OU 7 dias após o primeiro

Notification
 └─ user_id, type, payload, read_at

AuditLog (LGPD)
 └─ actor_id, action, entity, entity_id, diff (jsonb), ip, user_agent, created_at
```

## 5. Fluxos principais

### Fluxo A — Vaga pública
1. Estabelecimento cria `JobPosting` (`open`).
2. Sistema notifica freelancers compatíveis (skill + geo + disponibilidade).
3. Freelancer envia `Application`.
4. Estabelecimento aceita uma → demais viram `rejected`, `JobPosting.status = filled`, `ServiceContract` criado.
5. Em `end_at`, contrato vira `completed` (job ARQ). Janela de avaliação de 7 dias abre.

### Fluxo B — Convite direto
1. Estabelecimento busca freelancers (skill, proximidade, rating).
2. Envia `Invitation` com termos propostos.
3. Aceite → `ServiceContract` direto (sem `JobPosting` obrigatório).

### Regras transversais
- Freelancer não aceita contratos sobrepostos.
- Avaliação visível só após ambos avaliarem **ou** 7 dias do primeiro (anti-retaliação).
- Cancelamento <24h da `start_at` gera "no-show" público no perfil.

## 6. Estrutura de pastas

```
app/
  api/v1/
    auth/              # /register, /login, /me
    freelancers/  establishments/  jobs/
    applications/  invitations/  contracts/  reviews/  notifications/
  core/
    config.py          # Pydantic Settings
    security.py        # JWT issue+validate, password hash
    database.py        # SQLAlchemy engine/session
    redis_client.py
    logging.py         # structlog + filtro PII
    exceptions.py      # DomainError e subclasses
  domain/
    models/            # SQLAlchemy models
    schemas/           # Pydantic schemas (XxxCreate/Update/Read separados)
    repositories/      # Acesso a dados (retornam models)
    services/          # Regras de negócio (retornam schemas)
  workers/
    arq_worker.py      # WorkerSettings ARQ
    tasks.py
  utils/
  main.py
alembic/
  versions/
  env.py
tests/
  unit/
  integration/
  conftest.py
docker-compose.yml     # pra deploy futuro
Dockerfile
pyproject.toml         # uv
.pre-commit-config.yaml
.env.example
docs/
  adr/                 # decisões arquiteturais (NNNN-titulo.md)
```

## 7. Convenções de código

- **Tipagem**: 100% type hints, `mypy --strict` no CI.
- **Schemas**: `XxxCreate`, `XxxUpdate`, `XxxRead` — nunca reutilizar entrada e saída.
- **Repositórios** retornam models SQLAlchemy; **services** retornam schemas Pydantic.
- **Endpoints** nunca acessam DB direto — sempre via service.
- **Async** em endpoints e DB (asyncpg + SQLAlchemy async).
- **Erros**: subclasses de `DomainError` em `app/core/exceptions.py`, mapeadas pra HTTP no handler central.
- **Migrations**: nunca editar uma aplicada em prod — gerar nova. Sempre incluir downgrade testado quando alterar dados.
- **Logs**: nunca PII direta — usar o filtro do `logging.py`.
- **Commits**: Conventional Commits (`feat:`, `fix:`, `refactor:`, ...).
- **Branches**: `main` (prod), `dev` (integração), `feat/<nome>`, `fix/<nome>`.
- Português em comentários e docstrings, inglês em identificadores.

## 8. Segurança e LGPD

- **RLS opcional**: como estamos com Postgres puro (sem Supabase Auth via JWT no DB), RLS perde valor — política de acesso vive na camada de service. Reativar se migrar pra Supabase Auth.
- `cpf`, `rg` criptografados em repouso (pgcrypto).
- `GET /me/export` e `DELETE /me` desde a sprint que tocar perfil.
- Filtro structlog remove `cpf`, `rg`, `email`, `phone`, `password` de qualquer log.
- JWT: expiração curta (60min) + endpoint de refresh.
- Senhas com bcrypt cost factor ≥ 12.
- Toda mutação em entidade sensível grava `audit_log` (via decorator no service).

## 9. Como rodar

Pré-requisitos:
- Python 3.12 (uv gerencia)
- [uv](https://docs.astral.sh/uv/) instalado
- Acesso de rede ao Postgres+Redis da VPS (IP whitelistado)

```bash
# 1. Clonar e instalar deps
uv sync

# 2. Setup do .env
cp .env.example .env
# editar DATABASE_URL, REDIS_URL, JWT_SECRET (peça pro infra owner)

# 3. Aplicar migrations (Alembic)
uv run alembic upgrade head

# 4. Rodar API
uv run uvicorn app.main:app --reload

# 5. Em outro terminal: worker ARQ (opcional em dev)
uv run arq app.workers.arq_worker.WorkerSettings
```

## 10. Como o Claude Code deve trabalhar neste repo

- **Sempre** mostrar plano antes de mudanças que toquem 3+ arquivos.
- **Sempre** rodar `ruff check && mypy app && pytest` antes de declarar feature pronta.
- **Nunca** commitar `.env`, chaves ou secrets — usar `.env.example`.
- **Nunca** mudar a stack da seção 3 sem ADR em `docs/adr/`.
- **Nunca** rodar migration destrutiva em DB compartilhado sem confirmar.
- Ao adicionar dependência: justificar (1-2 linhas).
- Decisão arquitetural não óbvia: registrar em `docs/adr/NNNN-titulo.md`.
- Migration que altera dados: incluir downgrade testado.
- Preferir composição a herança; funções puras quando der; evitar "managers"/"helpers" sem responsabilidade clara.
- Português em comentário/docstring, inglês em identificador.

## 11. Roadmap macro

- **Sprint 0**: Scaffolding, Postgres+PostGIS provisionado, Redis provisionado, custom JWT auth, modelos base, audit_log, migrations, ARQ skeleton, pre-commit, testes base. ✅
- **Sprint 1**: Perfis (freela + estabelecimento) + upload de foto (S3-compatible) + LGPD endpoints (`/me/export`, `DELETE /me`). ✅
- **Sprint 2**: CRUD de vagas + busca com filtros + geolocalização (PostGIS `ST_DWithin`). ✅
- **Sprint 3**: Fluxo A end-to-end (candidatura → aceite transacional → contrato + cron de ciclo de vida + notificações). ✅ (53 testes novos; suíte 99/99)
- **Sprint 4**: Fluxo B end-to-end (busca freelancers por proximidade → convite direto → aceite → contrato). ✅ (29 testes novos; suíte 128/128)
- **Sprint 5**: Avaliações mútuas + regra de visibilidade anti-retaliação + rating agregado + cron reveal. ✅ (34 testes novos; suíte 162/162)
- **Sprint 6**: Notificações in-app (delete + count + emissões lifecycle) + dashboard admin (stats, users, audit-log). ✅ (18 testes novos; suíte 180/180)
- **Sprint 7**: Matching engine — scoring multi-fator de freelancers (proximity, skill, rating, reliability, experience, repeat-hire). ✅ (15 testes novos; suíte 195/195)
- **Sprint 8**: Moderação — reports user-facing + admin moderation queue + hide/unhide reviews + notificações. ✅ (18 testes novos; suíte 213/213)
- **Sprint 9**: Pagamento — registro + confirmação Pix manual + disputa + auto-create no lifecycle. ✅ (11 testes novos; suíte 224/224)
- **Sprint 10+**: Gateway Pix real (Mercado Pago/Asaas), refresh tokens, mobile.
