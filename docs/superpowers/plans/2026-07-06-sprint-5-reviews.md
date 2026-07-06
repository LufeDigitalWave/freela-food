# Sprint 5 — Reviews Implementation Plan

**Goal:** Avaliações mútuas pós-contrato com regra de visibilidade anti-retaliação, rating agregado nos perfis, e cron de revelação após 7 dias.

**Architecture:** Nova entidade `Review` (1 por parte por contrato). Visibilidade controlada por `visible_at` (NULL = invisível ao público). Rating agregado via fórmula incremental em `FreelancerProfile` e `EstablishmentProfile`. Cron ARQ `reveal_reviews` revela reviews órfãs após 7 dias.

**Tech Stack:** Python 3.12 + uv, FastAPI, SQLAlchemy 2.x async, Alembic, Postgres 15 + PostGIS, ARQ, pytest-asyncio. DB de teste = DB da VPS (porta 5435).

**Spec:** `docs/superpowers/specs/2026-07-06-sprint-5-reviews-design.md`

---

## File structure

**Criar:**
- `alembic/versions/006_reviews.py` — migration
- `app/domain/models/review.py` — model Review
- `app/domain/schemas/review.py` — ReviewCreate, ReviewRead, ReviewList, ReviewStats
- `app/domain/repositories/review_repository.py` — acesso a dados
- `app/domain/services/review_service.py` — regras de negócio
- `app/api/v1/reviews/__init__.py` — package
- `app/api/v1/reviews/router.py` — endpoints
- `tests/integration/test_reviews_create.py`
- `tests/integration/test_reviews_visibility.py`
- `tests/integration/test_reviews_listing.py`
- `tests/integration/test_reviews_rating.py`
- `tests/integration/test_cron_reveal.py`

**Modificar:**
- `app/domain/models/__init__.py` — re-export Review
- `app/domain/models/freelancer_profile.py` — colunas average_rating + total_reviews
- `app/domain/models/establishment_profile.py` — colunas average_rating + total_reviews
- `app/domain/schemas/contract.py` — ServiceContractRead aceita application_id/job_posting_id nullable (fix pra Fluxo B)
- `app/core/exceptions.py` — novas exceções Sprint 5
- `app/workers/tasks.py` — cron reveal_reviews
- `app/workers/arq_worker.py` — registrar novo cron
- `app/api/v1/freelancers/router.py` — endpoints /reviews e /stats
- `app/api/v1/establishments/router.py` — endpoints /reviews e /stats (criar se não existir)
- `app/main.py` — registrar router de reviews
- `tests/factories.py` — make_review, make_completed_contract

---

## Tasks

### Task 1 — Migration 006: tabela reviews + colunas de rating nos perfis

**Objetivo:** Criar tabela `reviews` e adicionar `average_rating`/`total_reviews` em ambos perfis.

- [ ] Gerar migration `006_reviews` com Alembic
- [ ] Tabela `reviews`: id (uuid PK), contract_id (FK), reviewer_id (FK), reviewee_id (FK), stars (smallint), comment (text), visible_at (timestamptz nullable), created_at (timestamptz)
- [ ] Constraints: UNIQUE(contract_id, reviewer_id), CHECK stars 1-5, CHECK comment length ≤ 2000, CHECK reviewer != reviewee
- [ ] Índices: ix_reviews_reviewee_visible, ix_reviews_contract
- [ ] ALTER freelancer_profiles ADD average_rating NUMERIC(3,2) NULL, total_reviews INT NOT NULL DEFAULT 0
- [ ] ALTER establishment_profiles ADD average_rating NUMERIC(3,2) NULL, total_reviews INT NOT NULL DEFAULT 0
- [ ] Downgrade: drop table + drop columns
- [ ] Testar upgrade + downgrade + upgrade

### Task 2 — Model Review + atualizar models existentes

**Objetivo:** Model SQLAlchemy da Review + adicionar colunas nos perfis.

- [ ] Criar `app/domain/models/review.py` com mapped columns
- [ ] Adicionar `average_rating` e `total_reviews` em `FreelancerProfile`
- [ ] Adicionar `average_rating` e `total_reviews` em `EstablishmentProfile`
- [ ] Registrar `Review` em `app/domain/models/__init__.py`
- [ ] `mypy --strict` limpo

### Task 3 — Exceptions Sprint 5

**Objetivo:** Adicionar exceções de domínio específicas.

- [ ] `ContractNotCompleted(ConflictError)` — "Contrato precisa estar completed para avaliação"
- [ ] `ReviewWindowClosed(ConflictError)` — "Janela de avaliação encerrada (30 dias)"
- [ ] `DuplicateReview(ConflictError)` — "Você já avaliou este contrato"

### Task 4 — Schemas de Review

**Objetivo:** Pydantic schemas para criação, leitura, listagem e stats.

- [ ] `ReviewCreate`: stars (int, ge=1, le=5), comment (str | None, max_length=2000)
- [ ] `ReviewRead`: id, contract_id, reviewer_id, reviewee_id, stars, comment, visible_at, created_at, reviewer_display_name (str)
- [ ] `ReviewList`: items (list[ReviewRead]), total, page, page_size
- [ ] `ReviewStats`: average_rating (float | None), total_reviews (int), distribution (dict[int, int])
- [ ] `mypy --strict` limpo

### Task 5 — Repository de Review

**Objetivo:** Camada de acesso a dados.

- [ ] `create(contract_id, reviewer_id, reviewee_id, stars, comment) -> Review`
- [ ] `get_by_contract_and_reviewer(contract_id, reviewer_id) -> Review | None`
- [ ] `get_peer_review(contract_id, reviewee_id) -> Review | None` — review que o reviewee escreveu (é reviewer nesse caso)
- [ ] `list_visible_for_user(reviewee_id, page, page_size) -> tuple[list[Review], int]` — filtra visible_at <= now()
- [ ] `list_received_for_user(reviewee_id, page, page_size) -> tuple[list[Review], int]` — todas recebidas (pra /me)
- [ ] `list_for_contract(contract_id) -> list[Review]`
- [ ] `get_distribution(reviewee_id) -> dict[int, int]` — COUNT por stars (apenas visíveis)
- [ ] `mark_visible(review_ids: list[uuid]) -> int` — batch update visible_at = now()
- [ ] `find_orphan_reviews_to_reveal() -> list[Review]` — visible_at IS NULL AND created_at <= now() - 7d

### Task 6 — Service de Review

**Objetivo:** Regras de negócio completas.

- [ ] `create_review(user_id, contract_id, payload: ReviewCreate) -> ReviewRead`
  - Validar: user é parte do contrato
  - Validar: contrato está `completed`
  - Validar: dentro da janela de 30 dias
  - Validar: sem review duplicada
  - Calcular `reviewee_id` (a outra parte)
  - Criar review (visible_at = NULL)
  - Verificar se peer review existe → se sim, marcar ambas `visible_at = now()` + notificar `review.both_visible`
  - Se peer não existe → notificar outra parte `review.peer_submitted`
  - Atualizar rating agregado do reviewee (fórmula incremental)
  - write_audit_log
  - Commit
- [ ] `list_for_contract(user_id, contract_id) -> list[ReviewRead]` — com visibilidade aplicada
- [ ] `list_received(user_id, page, page_size) -> ReviewList` — todas recebidas (/me)
- [ ] `list_public(reviewee_id, page, page_size) -> ReviewList` — apenas visíveis
- [ ] `get_stats(reviewee_id) -> ReviewStats` — rating + distribuição
- [ ] Helper `_update_rating(reviewee_id, new_stars)` — fórmula incremental

### Task 7 — Router de Reviews

**Objetivo:** Endpoints HTTP.

- [ ] `POST /v1/contracts/{contract_id}/reviews` → 201 ReviewRead
- [ ] `GET /v1/contracts/{contract_id}/reviews` → list (com visibilidade)
- [ ] `GET /v1/me/reviews` → ReviewList (recebidas, paginado)
- [ ] Registrar router em `app/main.py`

### Task 8 — Endpoints públicos em freelancers e establishments

**Objetivo:** Reviews visíveis e stats nos perfis públicos.

- [ ] `GET /v1/freelancers/{user_id}/reviews` → ReviewList (visíveis)
- [ ] `GET /v1/freelancers/{user_id}/stats` → ReviewStats
- [ ] `GET /v1/establishments/{user_id}/reviews` → ReviewList (visíveis)
- [ ] `GET /v1/establishments/{user_id}/stats` → ReviewStats
- [ ] Criar `app/api/v1/establishments/router.py` se não existir

### Task 9 — Cron `reveal_reviews`

**Objetivo:** Worker que revela reviews órfãs após 7 dias.

- [ ] Implementar `reveal_reviews(_ctx)` em `app/workers/tasks.py`
- [ ] Query: reviews com visible_at IS NULL AND created_at <= now() - 7 days
- [ ] Marcar visible_at = now()
- [ ] Emitir notificação `review.revealed` por review revelada
- [ ] Registrar em `WorkerSettings.cron_jobs` (5 min)
- [ ] Log estruturado `review_lifecycle.tick`

### Task 10 — Factories de teste

**Objetivo:** Helpers de teste reutilizáveis.

- [ ] `make_completed_contract(session, freelancer_id, establishment_id, ...)` — cria contrato com status=completed
- [ ] `make_review(session, contract_id, reviewer_id, reviewee_id, stars, ...)` — cria review direta
- [ ] Garantir que contratos de teste usem UUIDs únicos

### Task 11 — Testes: criação de review

**Arquivo:** `tests/integration/test_reviews_create.py`

- [ ] Happy path: freelancer avalia estabelecimento após contrato completed
- [ ] Happy path: estabelecimento avalia freelancer
- [ ] Happy path: contrato do Fluxo B (sem job_posting)
- [ ] Erro 403: user não é parte do contrato
- [ ] Erro 409: contrato não está completed (scheduled, in_progress, cancelled)
- [ ] Erro 409: janela de 30 dias expirada
- [ ] Erro 409: review duplicada (mesma parte mesmo contrato)
- [ ] Verifica reviewee_id calculado automaticamente

### Task 12 — Testes: visibilidade

**Arquivo:** `tests/integration/test_reviews_visibility.py`

- [ ] Primeira review: visible_at = NULL
- [ ] Segunda review: ambas ganham visible_at = now()
- [ ] Endpoint público: filtra reviews sem visible_at
- [ ] Endpoint do contrato: parte vê sua review; não vê a do outro se invisible
- [ ] Endpoint do contrato: ambas visíveis após segunda review
- [ ] GET /me/reviews: user vê todas as reviews recebidas (visíveis e não)
- [ ] Notificação peer_submitted emitida na primeira review
- [ ] Notificação both_visible emitida na segunda review

### Task 13 — Testes: listagem e stats

**Arquivo:** `tests/integration/test_reviews_listing.py`

- [ ] GET /freelancers/{id}/reviews: retorna apenas visíveis, paginado
- [ ] GET /establishments/{id}/reviews: retorna apenas visíveis, paginado
- [ ] GET /freelancers/{id}/stats: average + total + distribution
- [ ] GET /establishments/{id}/stats: average + total + distribution
- [ ] Stats com zero reviews: average=null, total=0
- [ ] Paginação: page=1, page=2 com page_size=2
- [ ] reviewer_display_name presente no read
- [ ] Reviews de outro user não aparecem

### Task 14 — Testes: rating agregado

**Arquivo:** `tests/integration/test_reviews_rating.py`

- [ ] Primeira review: average = stars, total = 1
- [ ] Segunda review (de outro contrato): recalcula average corretamente
- [ ] Profile reflete rating atualizado via GET /me
- [ ] Rating não muda quando user avalia (é o reviewee que ganha rating)
- [ ] Edge case: 5 reviews, average preciso (verificar arredondamento)

### Task 15 — Testes: cron reveal

**Arquivo:** `tests/integration/test_cron_reveal.py`

- [ ] Review com >7 dias e visible_at NULL → revelada
- [ ] Review com <7 dias e visible_at NULL → não tocada
- [ ] Review já com visible_at → não tocada (idempotente)
- [ ] Notificação review.revealed emitida
- [ ] Múltiplas reviews reveladas em batch

### Task 16 — Verificação final

- [ ] `ruff check .` limpo
- [ ] `mypy --strict app` limpo
- [ ] `pytest` — suíte inteira verde (128 antigos + ~34 novos = ~162 testes)
- [ ] Commit: `feat(sprint-5): avaliações mútuas + anti-retaliação + rating agregado + N tests`
- [ ] Push para branch `feat/sprint-5-reviews`

---

## Sequência de execução

```
Task 1 (migration) → Task 2 (model) → Task 3 (exceptions) → Task 4 (schemas)
→ Task 5 (repository) → Task 6 (service) → Task 7 (router reviews)
→ Task 8 (endpoints públicos) → Task 9 (cron) → Task 10 (factories)
→ Task 11-15 (testes, podem rodar em paralelo entre si)
→ Task 16 (verificação final)
```

Dependências lineares na maioria; testes dependem de tudo anterior. Migration precisa rodar primeiro para os testes de integração passarem.

---

## Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Fórmula incremental diverge com arredondamento | Aceitável no MVP; futuro: cron noturno com `AVG(stars)` |
| Batch de notificações no reveal | Volume baixo no MVP; se crescer, usar ARQ task por batch |
| ServiceContractRead assume application_id NOT NULL | Ajustar schema pra aceitar None (Fluxo B já existe) |
| Down_revision errada | Verificar `005_invitations_origin` como prev |
