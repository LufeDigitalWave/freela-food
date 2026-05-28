# Sprint 3 — Fluxo A end-to-end (candidatura → aceite → contrato)

**Data:** 2026-05-28
**Status:** Design aprovado, pronto pra plano de implementação
**Pré-requisitos:** Sprint 2 (vagas + busca PostGIS) mergeada em `main` (commit `7e9e5de`)

---

## 1. Objetivo

Entregar o Fluxo A do marketplace completo: estabelecimento publica vaga → freelancers se candidatam → estabelecimento aceita uma → contrato (`ServiceContract`) é criado e tem seu ciclo de vida (scheduled → in_progress → completed) avançado automaticamente por um cron ARQ. Inclui também:

- Cancelamento de contrato por qualquer das partes (com regra de no-show <24h pro freelancer).
- Notifications in-app persistidas (sem push real — leitura é Sprint 6).
- Auto-reopen do JobPosting quando contrato é cancelado com >2h até `start_at`.

Reviews ficam fora desta sprint (Sprint 5).

## 2. Escopo

### Dentro
- Tabelas `applications`, `service_contracts`, `notifications` (migration 004).
- Endpoints `/v1/jobs/{id}/applications`, `/v1/applications/*`, `/v1/me/applications`, `/v1/contracts/*`, `/v1/me/contracts`, `/v1/notifications/*`, `/v1/me/notifications`.
- Cron ARQ `advance_contract_lifecycle` (5min).
- Contadores no `FreelancerProfile`: `no_show_count`, `completed_contracts_count`.
- Audit log em todas mutações.
- Testes integração + unit (~50+ novos).

### Fora
- Reviews/avaliações (Sprint 5).
- Notifications push real, e-mail, websocket (Sprint 6).
- Convites diretos / Fluxo B (Sprint 4).
- Pagamentos, contratos formais, chat.

## 3. Decisões de produto (validadas)

| # | Decisão | Justificativa |
|---|---|---|
| D1 | **Overlap de horário** do freelancer é checado **apenas no accept**, não na candidatura | Freelancer mantém flexibilidade de aplicar em paralelo; proteção real fica no momento do compromisso. |
| D2 | **Cancel de JobPosting `filled`** cascateia: contrato também é marcado `cancelled` com `cancelled_by='establishment'` | Atende caso comum sem exigir 2 chamadas; UI fica simples. `cancelled_by='system'` fica reservado pra futuras automações (ex.: limpeza de órfãos). |
| D3 | Freelancer **pode cancelar** ServiceContract; se faltar <24h pra `start_at`, marca `no_show=true` no contrato + incrementa `freelancer_profiles.no_show_count` | Implementa a regra transversal do CLAUDE.md ("cancelamento <24h gera no-show público"). |
| D4 | **Cron ARQ a cada 5min** avança `scheduled→in_progress` (em `start_at`) e `in_progress→completed` (em `end_at`); idempotente | 5min de drift é imperceptível pro usuário; baixo custo de DB. |
| D5 | **Auto-reopen** do JobPosting pra `open` quando contrato é cancelado e ainda faltar >2h até `start_at`; senão job vai pra `cancelled` | Dá chance do estabelecimento receber novas candidaturas se há tempo. |
| D6 | Application tem campo opcional `message` (text, até 500 chars) | Diferencial baixo custo; freelancer pode se vender. |
| D7 | UNIQUE `(job_posting_id, freelancer_id)` em applications é **total** (cobre também withdrawn) | Evita spam de candidaturas. Afrouxa em sprint futura se necessário. |

## 4. Arquitetura

### Padrão de módulos
Mantém a Abordagem A já validada (consistente com Sprint 0-2):

```
app/api/v1/
  applications/    router.py
  contracts/       router.py
  notifications/   router.py
app/domain/
  models/          application.py, service_contract.py, notification.py
  schemas/         application.py, contract.py, notification.py
  repositories/    application_repository.py, contract_repository.py, notification_repository.py
  services/        application_service.py, contract_service.py, notification_service.py
app/workers/
  tasks.py         (+ advance_contract_lifecycle)
  arq_worker.py    (+ cron 5min)
alembic/versions/
  004_applications_contracts_notifications.py
tests/integration/
  test_applications.py, test_application_accept.py,
  test_contracts.py, test_cron_lifecycle.py, test_notifications.py
tests/
  factories.py     (novo: helpers make_*)
```

**`NotificationService` é serviço infra**: chamado pelos `ApplicationService` e `ContractService` dentro da mesma transação. Não é dono de fluxo, não tem regra de negócio própria além de persistir.

### Concorrência crítica — accept de Application

Operação isolada em uma transação. Sequência:

1. `BEGIN ISOLATION LEVEL REPEATABLE READ`
2. `SELECT … FROM applications WHERE id=:id AND status='pending' FOR UPDATE` → 409 se não encontrado.
3. `SELECT … FROM job_postings WHERE id=:job_id AND status='open' FOR UPDATE` → 409 se não `open`.
4. Overlap-check:
   ```sql
   SELECT 1 FROM service_contracts
   WHERE freelancer_id = :fid
     AND status IN ('scheduled', 'in_progress')
     AND tstzrange(start_at, end_at, '[)') && tstzrange(:js, :je, '[)')
   LIMIT 1
   ```
   Se encontrar → 409 `FreelancerOverlap`, ROLLBACK.
5. `UPDATE applications SET status='accepted', decided_at=now() WHERE id=:id`
6. `UPDATE applications SET status='rejected', decided_at=now() WHERE job_posting_id=:job_id AND status='pending' AND id != :id`
7. `UPDATE job_postings SET status='filled', updated_at=now() WHERE id=:job_id`
8. `INSERT INTO service_contracts (...) VALUES (...)` (status='scheduled', dados copiados do job)
9. `INSERT INTO notifications (...) VALUES (...)` — 1 pro vencedor + N pros rejeitados
10. `INSERT INTO audit_log (...)` — para cada mutação
11. `COMMIT`

## 5. Schema (migration 004)

### Nova tabela `applications`
```sql
id                 uuid PK DEFAULT gen_random_uuid()
job_posting_id     uuid NOT NULL FK→job_postings(id) ON DELETE CASCADE
freelancer_id      uuid NOT NULL FK→users(id) ON DELETE CASCADE
status             varchar(20) NOT NULL DEFAULT 'pending'
                   CHECK IN ('pending','accepted','rejected','withdrawn')
message            text NULL CHECK (length(message) <= 500)
created_at         timestamptz NOT NULL DEFAULT now()
updated_at         timestamptz NOT NULL DEFAULT now()
decided_at         timestamptz NULL
UNIQUE (job_posting_id, freelancer_id)
INDEX (job_posting_id, status)
INDEX (freelancer_id, status)
```

### Nova tabela `service_contracts`
```sql
id                 uuid PK DEFAULT gen_random_uuid()
application_id     uuid NOT NULL UNIQUE FK→applications(id)
job_posting_id     uuid NOT NULL FK→job_postings(id)
freelancer_id      uuid NOT NULL FK→users(id)
establishment_id   uuid NOT NULL FK→users(id)
start_at           timestamptz NOT NULL
end_at             timestamptz NOT NULL
agreed_hourly_rate numeric(10,2) NULL
agreed_total_pay   numeric(10,2) NULL
status             varchar(20) NOT NULL DEFAULT 'scheduled'
                   CHECK IN ('scheduled','in_progress','completed','cancelled')
cancelled_by       varchar(20) NULL
                   CHECK (cancelled_by IS NULL OR cancelled_by IN
                          ('freelancer','establishment','system'))
cancelled_at       timestamptz NULL
cancel_reason      text NULL CHECK (length(cancel_reason) <= 1000)
no_show            bool NOT NULL DEFAULT false
created_at         timestamptz NOT NULL DEFAULT now()
updated_at         timestamptz NOT NULL DEFAULT now()
CHECK (end_at > start_at)
CHECK ((cancelled_at IS NULL AND cancelled_by IS NULL)
       OR (cancelled_at IS NOT NULL AND cancelled_by IS NOT NULL))
INDEX (freelancer_id, status, start_at, end_at)   -- overlap-check
INDEX (status, start_at)                          -- cron scheduled→in_progress
INDEX (status, end_at)                            -- cron in_progress→completed
INDEX (job_posting_id)
```

### Nova tabela `notifications`
```sql
id           uuid PK DEFAULT gen_random_uuid()
user_id      uuid NOT NULL FK→users(id) ON DELETE CASCADE
type         varchar(50) NOT NULL
payload      jsonb NOT NULL DEFAULT '{}'::jsonb
read_at      timestamptz NULL
created_at   timestamptz NOT NULL DEFAULT now()
INDEX (user_id, read_at, created_at DESC)
```

### Alterações em `freelancer_profiles`
```sql
ALTER TABLE freelancer_profiles
  ADD COLUMN no_show_count int NOT NULL DEFAULT 0,
  ADD COLUMN completed_contracts_count int NOT NULL DEFAULT 0;
```

### Downgrade
DROP das 3 tabelas + DROP das 2 colunas em `freelancer_profiles`.

## 6. Endpoints (contratos)

Todos sob `/v1/`, JWT obrigatório, payloads/respostas em Pydantic v2.

### Applications

| Método | Path | Auth | Códigos relevantes |
|---|---|---|---|
| `POST` | `/jobs/{job_id}/applications` | freelancer | 201, 400 (job não `open`), 403 (estabelecimento), 409 (duplicada / sem profile) |
| `GET` | `/jobs/{job_id}/applications?status=` | estabelecimento dono | 200, 403 |
| `GET` | `/me/applications?status=&page=&page_size=` | freelancer | 200 |
| `GET` | `/applications/{id}` | freelancer dono OU estabelecimento dono | 200, 403 |
| `POST` | `/applications/{id}/accept` | estabelecimento dono | 200, 403, 409 (não pending / job não open / overlap freelancer) |
| `POST` | `/applications/{id}/reject` | estabelecimento dono | 200, 403, 409 |
| `POST` | `/applications/{id}/withdraw` | freelancer dono | 200, 403, 409 (não pending) |

### Contracts

| Método | Path | Auth | Códigos relevantes |
|---|---|---|---|
| `GET` | `/me/contracts?status=&page=&page_size=` | qualquer user (vê os que é parte) | 200 |
| `GET` | `/contracts/{id}` | freelancer OU estabelecimento parte | 200, 403 |
| `POST` | `/contracts/{id}/cancel` (body: `{reason?: string}`) | freelancer OU estabelecimento parte | 200, 403, 409 (status terminal) |

### Notifications

| Método | Path | Auth | Códigos relevantes |
|---|---|---|---|
| `GET` | `/me/notifications?unread_only=&page=&page_size=` | qualquer user | 200 |
| `POST` | `/notifications/{id}/read` | dono | 200, 403, 404 |
| `POST` | `/me/notifications/read-all` | qualquer user | 200 (retorna `{updated: int}`) |

### Schemas Pydantic principais
- `ApplicationCreate { message?: str (max 500) }`
- `ApplicationRead { id, job_posting_id, freelancer_id, status, message?, created_at, decided_at? }`
- `ApplicationList { items: list[ApplicationRead], total: int, page: int, page_size: int }`
- `ServiceContractRead { id, application_id, job_posting_id, freelancer_id, establishment_id, start_at, end_at, agreed_hourly_rate?, agreed_total_pay?, status, cancelled_by?, cancelled_at?, cancel_reason?, no_show, created_at }`
- `ServiceContractList { ... }`
- `ContractCancelRequest { reason?: str (max 1000) }`
- `NotificationRead { id, type, payload, read_at?, created_at }`
- `NotificationList { items, total, unread_count, page, page_size }`
- `ReadAllResponse { updated: int }`

## 7. Máquina de estados

### Application
```
pending → accepted (via /accept; gera ServiceContract, cascade reject)
pending → rejected (via /reject OU cascade do accept)
pending → withdrawn (via /withdraw, só freelancer)
```
Terminais: `accepted`, `rejected`, `withdrawn`. Sem retorno.

### ServiceContract
```
scheduled → in_progress (cron, em start_at)
scheduled → cancelled    (via /cancel ou cascade do job)
in_progress → completed  (cron, em end_at)
in_progress → cancelled  (via /cancel ou cascade do job)
```
Terminais: `completed`, `cancelled`.

### JobPosting (transições novas)
```
open → filled            (no accept de application)
filled → completed       (cron, quando contrato vira completed)
filled → cancelled       (POST /jobs/{id}/cancel cascateia)
filled → open            (cancel do contrato com >2h pra start_at)
```

## 8. Regras transversais (validações no service)

| Regra | Local | Erro |
|---|---|---|
| Job precisa estar `open` pra receber candidatura | `ApplicationService.create` | 409 `JobNotOpen` |
| Estabelecimento não candidata em vaga própria | `ApplicationService.create` | 403 `SelfApplicationForbidden` |
| Freelancer precisa ter `FreelancerProfile` | `ApplicationService.create` | 409 `ProfileRequired` |
| Application UNIQUE (job, freelancer) | DB constraint | 409 `DuplicateApplication` (mapeado de IntegrityError) |
| Accept: application precisa estar `pending` | `ApplicationService.accept` | 409 `ApplicationNotPending` |
| Accept: job precisa estar `open` | `ApplicationService.accept` | 409 `JobNotOpen` |
| Accept: freelancer não pode ter contrato sobreposto | `ApplicationService.accept` (query no item 4 da seção 4) | 409 `FreelancerOverlap` |
| Cancel: contrato precisa estar `scheduled` ou `in_progress` | `ContractService.cancel` | 409 `ContractAlreadyTerminal` |
| Cancel <24h pelo freelancer: marca `no_show=true` + incrementa profile | `ContractService.cancel` | — (não é erro) |
| Auto-reopen do job: `start_at - now() > 2h` | `ContractService.cancel` | — (não é erro) |
| Listagem/detalhe: só partes envolvidas | `ContractService.get_by_id`, `ApplicationService.list_for_job` | 403 |

## 9. Notifications geradas

| Evento | Destinatário | `type` | `payload` |
|---|---|---|---|
| Application criada | estabelecimento dono | `application.received` | `{application_id, job_posting_id, freelancer_id}` |
| Application accepted | freelancer vencedor | `application.accepted` | `{application_id, job_posting_id, contract_id}` |
| Application rejected (manual ou cascade) | freelancer perdedor | `application.rejected` | `{application_id, job_posting_id}` |
| Contract cancelled | parte que não cancelou | `contract.cancelled_by_other_party` | `{contract_id, job_posting_id, cancelled_by, no_show}` |

Sem rate limit nesta sprint (Sprint 6 cuida).

## 10. Cron ARQ — `advance_contract_lifecycle`

Cadastrado em `app/workers/arq_worker.py` rodando a cada 5min:

```python
cron(advance_contract_lifecycle,
     minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55})
```

Lógica em `app/workers/tasks.py` (ver seção 4 do brainstorming, código já esboçado). Pontos-chave:
- **Idempotente**: queries usam status + comparação temporal, não dependem de "última execução".
- **Recovery natural**: contrato com `end_at` passado e ainda `scheduled` pula direto pra `completed` (acontece se cron parou de rodar).
- **Side-effects do completed**: incrementa `freelancer_profiles.completed_contracts_count`; marca `job_postings.status='completed'`.
- **Sem notification** ainda — `contract.starting_soon` e `contract.completed` ficam pra Sprint 5+ (quando reviews abrirem).

## 11. Auditoria

Toda mutação grava `audit_log`:
- `application.create`, `application.accept`, `application.reject`, `application.withdraw`
- `application.cascade_reject` (gerado dentro do accept, com `meta.parent_application_id`)
- `contract.create`, `contract.cancel`, `contract.advance` (cron)
- `job_posting.cascade_cancel`, `job_posting.auto_reopen`, `job_posting.auto_complete`

Decorator/helper existente em `app/utils/audit.py` é reutilizado.

## 12. Testes (TDD)

Estrutura por arquivo já decidida — totais aproximados:

| Arquivo | # testes |
|---|---|
| `test_applications.py` | 18-20 |
| `test_application_accept.py` | 12-14 |
| `test_contracts.py` | 10-12 |
| `test_cron_lifecycle.py` | 6-7 |
| `test_notifications.py` | 6-8 |
| **Total** | **~52-61** |

### Padrões
- Rollback transacional por test (igual Sprint 0-2).
- Factories novas em `tests/factories.py`: `make_freelancer_user`, `make_establishment_user`, `make_job`, `make_application`, `make_contract`.
- Auth via fixture `auth_headers(user)`.
- Tempo controlado: adicionar `freezegun` em dev-deps (não tem hoje no `pyproject.toml`). Alternativa de injetar clock no service foi descartada — refator grande pra Sprint 3 e `freezegun` cobre os casos de cron + no_show <24h.

### Pontos de risco a comunicar
- **Race de accept entre 2 estabelecimentos diferentes pra freelancers em janelas conflitantes**: testar com `pytest-asyncio` + sessions concorrentes é capcioso. Cobertura: test unit da query de overlap + confiança no `SELECT FOR UPDATE` + `REPEATABLE READ`. E2E de race fica como TODO em sprint futura.
- **Cron em test**: chamar `advance_contract_lifecycle(ctx={})` direto, sem ARQ runtime.

## 13. Dependências novas

- `freezegun` em `[tool.uv.dev-dependencies]` (controle de tempo nos testes).
- Nenhuma outra. SQLAlchemy 2.x, GeoAlchemy2, asyncpg já cobrem.

## 14. Migration plan

1. Criar `alembic/versions/004_applications_contracts_notifications.py` com upgrade/downgrade testados localmente.
2. Aplicar primeiro em dev local (`uv run alembic upgrade head`).
3. Aplicar na VPS via SSH (`ssh root@93.127.211.7 -t "docker exec -it <api-container> alembic upgrade head"` — ou diretamente via psql como na Sprint 2 se a API ainda não tá deployada lá).
4. Verificar `alembic_version` table.

## 15. Convenções respeitadas (CLAUDE.md)

- ✅ Tipagem 100%, `mypy --strict`.
- ✅ Schemas separados Create/Update/Read.
- ✅ Repositórios retornam models; services retornam schemas.
- ✅ Endpoints sem acesso direto a DB.
- ✅ Erros via `DomainError` subclasses → handler central.
- ✅ Audit log em toda mutação sensível.
- ✅ Português em comentários, inglês em identificadores.
- ✅ Conventional Commits.
- ✅ Branch `feat/sprint-3-flow-a`.

## 16. Critérios de aceite

- [ ] Migration 004 aplicada local e VPS.
- [ ] ~52+ testes integração passando.
- [ ] `ruff check`, `mypy app` (strict), `pytest` todos verdes.
- [ ] Audit log gravado em toda mutação.
- [ ] Cron rodando na VPS (verificável via logs ARQ).
- [ ] Branch mergeada em `main` via PR ou merge direto, conforme Sprint 2.
- [ ] CLAUDE.md atualizado (seção 11 — roadmap) marcando Sprint 3 ✅.

## 17. Próximo passo

Após aprovação deste spec → invocar `superpowers:writing-plans` pra gerar plano de implementação por tasks TDD.
