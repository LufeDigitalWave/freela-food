# Sprint 5 — Avaliações mútuas com regra de visibilidade anti-retaliação

> Design validado em 2026-07-06. Marketplace `freela-food`. Continuação natural do Sprint 4 (Fluxo B).

## 1. Objetivo

Permitir que freelancers e estabelecimentos **avaliem mutuamente** após a conclusão de um contrato (`ServiceContract.status == 'completed'`). As avaliações usam regra de **visibilidade anti-retaliação**: a nota/comentário de uma parte só fica visível quando ambas avaliaram **OU** 7 dias após a primeira avaliação — impedindo que a segunda parte ajuste sua nota após ver a da primeira.

## 2. Escopo

### Dentro
- Nova entidade `Review` (1 por parte por contrato — max 2 reviews por contrato).
- Regra de visibilidade: `visible_at = min(ambas_avaliaram, first_review.created_at + 7d)`.
- Rating agregado nos perfis: `average_rating` + `total_reviews` (colunas em `FreelancerProfile` e `EstablishmentProfile`).
- Endpoints: criar review, listar reviews recebidas (por user ou perfil público), obter review individual.
- Janela de avaliação: 30 dias após `contract.status == 'completed'`. Após isso, janela fecha.
- Notificações: lembrete quando outra parte avaliou (sem revelar conteúdo), ambas visíveis.

### Fora (sprints futuras)
- Resposta/réplica do avaliado.
- Disputa de avaliação (moderação admin).
- Ordenação/filtro de busca por rating (Sprint 7+ — matching com IA).
- Badges ou gamificação.

## 3. Decisões de produto

1. **1 review por parte por contrato** — freelancer avalia o estabelecimento E vice-versa. Max 2 reviews por contrato.
2. **Escala 1–5 estrelas** + comentário opcional (max 2000 chars).
3. **Visibilidade anti-retaliação**: nenhuma review é visível ao público até que ambas partes avaliem OU 7 dias passem da primeira review (o que vier primeiro). A parte que avaliou primeiro vê SUA review imediatamente, mas não a da outra.
4. **Janela de 30 dias**: review só pode ser criada dentro de 30 dias após `completed_at` (ou `updated_at` quando status virou `completed`). Após esse prazo, janela fecha — sem review possível.
5. **Imutável após criação**: review não pode ser editada nem deletada (integridade do histórico).
6. **Rating agregado**: `average_rating` (Numeric 3,2) e `total_reviews` (int) em ambos perfis. Atualizados atomicamente na criação da review. O agregado usa TODAS as reviews recebidas (inclusive não-visíveis — o valor é correto; a visibilidade afeta apenas exibição individual).
7. **Perfil público mostra apenas reviews visíveis** — listagem filtra por `visible_at <= now()`.

## 4. Arquitetura

### Padrão de módulos (igual sprints anteriores)
- `app/domain/models/review.py` — model SQLAlchemy.
- `app/domain/schemas/review.py` — `ReviewCreate`, `ReviewRead`, `ReviewList`, `ReviewStats`.
- `app/domain/repositories/review_repository.py` — acesso a dados.
- `app/domain/services/review_service.py` — regras de negócio.
- `app/api/v1/reviews/router.py` — endpoints.
- `app/workers/tasks.py` — cron `reveal_reviews` (marca `visible_at` após 7 dias).

### Reuso
- `ContractRepository` / `ContractService` — verificar status `completed` e partes do contrato.
- `NotificationService.emit(...)` — notificações de review.
- `write_audit_log(...)` — auditoria na criação.

## 5. Schema (migration 006)

### Nova tabela `reviews`
| Coluna | Tipo | Constraints |
|---|---|---|
| `id` | uuid | PK (UUIDPKMixin) |
| `contract_id` | uuid | FK→service_contracts(id), NOT NULL |
| `reviewer_id` | uuid | FK→users(id), NOT NULL |
| `reviewee_id` | uuid | FK→users(id), NOT NULL |
| `stars` | smallint | NOT NULL, CHECK 1–5 |
| `comment` | text | NULL |
| `visible_at` | timestamptz | NULL (preenchido quando regra de visibilidade satisfeita) |
| `created_at` | timestamptz | NOT NULL, server_default now() |

Constraints:
- `UNIQUE(contract_id, reviewer_id)` — 1 review por parte por contrato.
- `CHECK(stars >= 1 AND stars <= 5)` — escala válida.
- `CHECK(comment IS NULL OR length(comment) <= 2000)` — limite de tamanho.
- `CHECK(reviewer_id != reviewee_id)` — não autoavaliação.

Índices:
- `ix_reviews_reviewee_visible` em `(reviewee_id, visible_at)` — listagem de reviews visíveis de um perfil.
- `ix_reviews_contract` em `(contract_id)` — lookup rápido das 2 reviews de um contrato.

### Alterações em `freelancer_profiles`
- `ADD COLUMN average_rating NUMERIC(3,2) NULL` — NULL = sem reviews ainda.
- `ADD COLUMN total_reviews INTEGER NOT NULL DEFAULT 0`.

### Alterações em `establishment_profiles`
- `ADD COLUMN average_rating NUMERIC(3,2) NULL`.
- `ADD COLUMN total_reviews INTEGER NOT NULL DEFAULT 0`.

### Downgrade
Dropar tabela `reviews` + remover colunas `average_rating`/`total_reviews` dos perfis. Seguro: não há dados em produção ainda.

## 6. Endpoints

### Reviews
- `POST /v1/contracts/{contract_id}/reviews` — **parte do contrato only**. Body: `stars` (1–5), `comment?`. Retorna `ReviewRead` (201). Regras no §8.
- `GET /v1/contracts/{contract_id}/reviews` — **parte do contrato only**. Retorna até 2 reviews (com visibilidade aplicada — se a outra review não está visível, não retorna conteúdo dela).
- `GET /v1/me/reviews` — **autenticado**. Reviews recebidas pelo user (todas, inclusive não-visíveis ao público — user vê suas próprias reviews recebidas). Query: `page`, `page_size`.
- `GET /v1/freelancers/{user_id}/reviews` — **público (auth required)**. Reviews visíveis recebidas por um freelancer. Query: `page`, `page_size`. Retorna `ReviewList`.
- `GET /v1/establishments/{user_id}/reviews` — **público (auth required)**. Reviews visíveis recebidas por um estabelecimento. Query: `page`, `page_size`. Retorna `ReviewList`.
- `GET /v1/freelancers/{user_id}/stats` — **público**. Retorna `ReviewStats` (average_rating, total_reviews, distribuição por estrela).
- `GET /v1/establishments/{user_id}/stats` — **público**. Idem.

### Schemas Pydantic
- `ReviewCreate`: `stars: int` (ge=1, le=5), `comment: str | None` (max_length=2000).
- `ReviewRead`: `id`, `contract_id`, `reviewer_id`, `reviewee_id`, `stars`, `comment`, `visible_at`, `created_at`, `reviewer_display_name` (join).
- `ReviewList`: `{items, total, page, page_size}`.
- `ReviewStats`: `average_rating: float | None`, `total_reviews: int`, `distribution: dict[int, int]` (ex: `{1: 0, 2: 1, 3: 5, 4: 12, 5: 30}`).

## 7. Regra de visibilidade — lógica detalhada

### Ao criar uma review:
1. Se a outra parte **já** avaliou (já existe review com `reviewer_id == outra_parte` no mesmo contrato):
   - Marcar **ambas** reviews com `visible_at = now()`.
   - Notificar ambas partes: `review.both_visible`.
2. Se a outra parte **ainda não** avaliou:
   - `visible_at` permanece NULL na review criada.
   - Notificar a outra parte: `review.peer_submitted` (sem revelar stars/comment).

### Cron `reveal_reviews` (a cada 5 min, junto com os outros crons):
- `UPDATE reviews SET visible_at = now() WHERE visible_at IS NULL AND created_at <= now() - interval '7 days'`.
- Idempotente. Revela reviews "órfãs" (a outra parte nunca avaliou dentro de 7 dias).
- Emite notificação `review.revealed` pra quem criou a review (informando que agora está pública).

### Exibição:
- Endpoint público (`GET /freelancers/{id}/reviews`) filtra: `WHERE reviewee_id = :id AND visible_at IS NOT NULL AND visible_at <= now()`.
- Endpoint do contrato (`GET /contracts/{id}/reviews`): a parte vê sua própria review sempre; vê a do outro **só se `visible_at` preenchido**.

## 8. Regras de negócio (validações no service)

**Criar review (`POST /contracts/{contract_id}/reviews`):**
- Ator deve ser parte do contrato (freelancer_id OU establishment_id). Senão `PermissionDenied`.
- Contrato deve estar `completed`. Senão `ContractNotCompleted` → 409.
- Janela de 30 dias: `now() - contract.updated_at <= 30 days`. Senão `ReviewWindowClosed` → 409.
- Ator não pode já ter review neste contrato. Senão `DuplicateReview` → 409.
- `reviewee_id` calculado server-side (a outra parte do contrato).
- Cria review + aplica regra de visibilidade (§7) + atualiza rating agregado do reviewee + audit + notificação.
- Tudo numa transação.

**Rating agregado — cálculo:**
- Na criação da review, incrementar `total_reviews` e recalcular `average_rating` do reviewee.
- Fórmula: `new_avg = ((old_avg * (total - 1)) + new_stars) / total` (ou query `AVG(stars)` se preferir precisão — depende de volume; incremental é mais performático).
- Decisão: usar **fórmula incremental** (O(1), sem full-scan). Edge case: primeira review → `average_rating = stars`.

## 9. Notifications geradas
| Tipo | Destinatário | Quando |
|---|---|---|
| `review.peer_submitted` | outra parte | review criada (sem revelar conteúdo) |
| `review.both_visible` | ambas partes | segunda review criada (ambas ficam visíveis) |
| `review.revealed` | autor da review | cron revelou após 7 dias |

## 10. Cron ARQ — `reveal_reviews`
Função nova em `app/workers/tasks.py`, registrada em `WorkerSettings.cron_jobs` na mesma cadência de 5 min.
- Idempotente: busca reviews com `visible_at IS NULL AND created_at <= now() - interval '7 days'`.
- Para cada review revelada, emite `review.revealed` ao autor.
- Retorna `{"revealed": N}`.

## 11. Auditoria
`write_audit_log` na criação de review: action `create`, entity `review`, entity_id, diff `{stars, has_comment: bool, contract_id}`. Nunca loga o conteúdo do comentário no diff (pode conter dados sensíveis).

## 12. Testes (TDD)

- `tests/integration/test_reviews_create.py`: happy path (ambos fluxos A e B), validações (não-parte → 403, contrato não completed → 409, janela fechada → 409, duplicado → 409), auto-cálculo de reviewee_id. (~8)
- `tests/integration/test_reviews_visibility.py`: primeira review fica invisible, segunda torna ambas visíveis, endpoint público filtra por visible_at, endpoint do contrato mostra/esconde conforme regra. (~8)
- `tests/integration/test_reviews_listing.py`: listar por freelancer (público), por estabelecimento (público), /me/reviews, paginação, stats com distribuição. (~8)
- `tests/integration/test_reviews_rating.py`: rating agregado atualiza no profile, primeira review, segunda review recalcula média, stats refletem distribuição. (~5)
- `tests/integration/test_cron_reveal.py`: revela após 7 dias, não toca reviews já visíveis, não toca reviews com <7 dias, notificação emitida, idempotência. (~5)

Total estimado: **~34 testes novos**. Suíte global permanece 100% verde; `ruff` + `mypy --strict` limpos.

### Padrões obrigatórios
- Emails/identificadores únicos por execução (uuid) — DB da VPS é compartilhado.
- Factory `make_review(...)` e `make_completed_contract(...)` em `tests/factories.py`.
- Contratos de teste devem estar em status `completed` (usar `advance_contract_lifecycle` ou settar direto).

## 13. Dependências novas
Nenhuma. Stack inalterada.

## 14. Migration plan
1. Gerar `006_reviews.py` (revision `006_reviews`, down_revision `005_invitations_origin`).
2. `alembic upgrade head` localmente contra VPS (porta 5435).
3. Verificar tabela + constraints + índices.
4. Testar `downgrade` → `upgrade`.

## 15. Convenções respeitadas (CLAUDE.md)
- Schemas `Create`/`Read`/`List` separados; repos retornam models, services retornam schemas.
- 100% type hints + `mypy --strict`; Conventional Commits.
- LGPD: reviews não expõem PII; audit nunca loga conteúdo do comentário.
- Alembic fonte de verdade; migration com downgrade testado.
- Nenhuma mudança de stack → sem ADR.

## 16. Critérios de aceite
- [ ] Freelancer e estabelecimento avaliam mutuamente após contrato completed.
- [ ] Review só criada dentro de 30 dias da conclusão.
- [ ] Visibilidade anti-retaliação: primeira review invisível ao público; segunda torna ambas visíveis.
- [ ] Cron revela reviews "órfãs" após 7 dias.
- [ ] Rating agregado (average + count) atualizado atomicamente nos perfis.
- [ ] Endpoints públicos filtram por `visible_at <= now()`.
- [ ] Stats com distribuição por estrela.
- [ ] ~34 testes novos verdes; suíte global verde; `ruff` + `mypy --strict` limpos.

## 17. Pontos de risco
- Fórmula incremental de rating pode divergir com o tempo por arredondamento — aceitável no MVP; recalcular com `AVG(stars)` em cron noturno se necessário no futuro.
- Cron `reveal_reviews` + notificação em batch pode gerar muitas notifications de uma vez se houver acúmulo — volume esperado é baixo no MVP.
