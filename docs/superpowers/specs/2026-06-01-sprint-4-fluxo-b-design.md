# Sprint 4 — Fluxo B end-to-end (busca de freelancers → convite direto → aceite → contrato)

> Design validado em 2026-06-01. Marketplace `freela-food`. Continuação natural do Sprint 3 (Fluxo A).
> Abordagem escolhida: **A — origem polimórfica direta no `ServiceContract`** (candidatura XOR convite).

## 1. Objetivo

Permitir que um **estabelecimento** busque freelancers por função + proximidade e os **convide diretamente** para um serviço, com termos propostos (data/hora/valor). O freelancer aceita ou recusa; o aceite gera um `ServiceContract` **sem necessidade de vaga pública (`JobPosting`)**, convergindo no mesmo modelo de contrato do Fluxo A.

## 2. Escopo

### Dentro
- Busca de freelancers (`GET /v1/freelancers/search`) por skill + raio geográfico (PostGIS), ordenada por distância.
- Nova entidade `Invitation` (convite direto) com termos propostos e ciclo de vida próprio.
- Endpoints de convite: criar, listar, detalhar, aceitar, recusar, retirar.
- Aceite transacional: cria contrato + auto-decline de convites sobrepostos + notificações.
- Expiração automática de convites pendentes via cron ARQ.
- Ajuste no `ServiceContract` para aceitar duas origens (candidatura **ou** convite).

### Fora (sprints futuras)
- Avaliações / rating (Sprint 5) — busca **não** ordena/filtra por estrelas ainda.
- Negociação de termos (contraproposta) — convite é aceita-ou-recusa, sem ida-e-volta.
- Pagamento, chat, matching com IA, mobile.

## 3. Decisões de produto (validadas)

1. **Convite freeform**: não exige `JobPosting`. O contrato nasce direto do convite. (CLAUDE.md: "sem JobPosting obrigatório".)
2. **5 status de convite**: `pending`, `accepted`, `declined` (freelancer recusa), `withdrawn` (estabelecimento retira), `expired` (TTL).
3. **TTL = min(now + `invitation_ttl_hours`, `start_at`)**, com `invitation_ttl_hours` default **72** em `Settings`. Convite expira em 72h OU no horário do serviço, o que vier antes.
4. **Busca de freelancers**: filtra por `skill_category_id` + raio (PostGIS `ST_DWithin`), exclui soft-deleted, ordena por distância asc com `completed_contracts_count` desc como critério secundário. Paginada. **Sem filtro de rating** (Sprint 5).
5. **Cascade no aceite**: ao aceitar, os demais convites `pending` do freelancer que se **sobrepõem no horário** viram `declined` automaticamente, com notificação aos estabelecimentos.
6. **Origem única do contrato**: todo `ServiceContract` tem exatamente uma origem — `application_id` XOR `invitation_id` (garantido por CHECK no banco).

## 4. Arquitetura

### Padrão de módulos (igual Sprint 1–3)
- `app/domain/models/invitation.py` — model SQLAlchemy.
- `app/domain/schemas/invitation.py` — `InvitationCreate`, `InvitationRead`, `InvitationList`.
- `app/domain/schemas/freelancer_search.py` — `FreelancerSearchRead` (perfil público + `distance_m`).
- `app/domain/repositories/invitation_repository.py` — acesso a dados (retorna models).
- `app/domain/repositories/freelancer_repository.py` — busca PostGIS de freelancers.
- `app/domain/services/invitation_service.py` — regras de negócio (retorna schemas).
- `app/domain/services/freelancer_search_service.py` — orquestra a busca.
- `app/api/v1/invitations/router.py` — endpoints de convite.
- `app/api/v1/freelancers/router.py` — endpoint de busca.
- Repositórios retornam models; services retornam schemas Pydantic; endpoints só falam com services.

### Reuso do Sprint 3
- `ContractRepository.has_overlap(...)` — reaproveitado tal qual no aceite do convite.
- `ContractRepository.create(...)` — **estendido** para aceitar origem por convite (ver §5).
- `NotificationService.emit(...)` — reaproveitado para todas as notificações.
- `write_audit_log(...)` — reaproveitado em todas as mutações.

### Extração leve (parte boa da Abordagem B)
A sequência **overlap-check → create contract → emit notification** é extraída para um helper privado em `ContractRepository.create` (que passa a receber `application_id: uuid | None` e `invitation_id: uuid | None`). O método `application_service.accept` continua intacto na sua lógica; só a assinatura de `create` é generalizada (passa `invitation_id=None` no Fluxo A).

### Concorrência crítica — accept de Invitation
Mesma estratégia do accept do Fluxo A: toda a operação de aceite roda numa transação única (`async with session.begin()` no nível do service via commit ao final). O `has_overlap` + criação do contrato + cascade + notificações são atômicos. Em caso de corrida (dois aceites simultâneos do mesmo freelancer em horários sobrepostos), o segundo falha no `has_overlap` ou no unique de `invitation_id`.

## 5. Schema (migration 005)

### Nova tabela `invitations`
| Coluna | Tipo | Constraints |
|---|---|---|
| `id` | uuid | PK (UUIDPKMixin) |
| `establishment_id` | uuid | FK→users(id), NOT NULL |
| `freelancer_id` | uuid | FK→users(id), NOT NULL |
| `skill_category_id` | uuid | FK→skill_categories(id), NOT NULL |
| `start_at` | timestamptz | NOT NULL |
| `end_at` | timestamptz | NOT NULL |
| `proposed_hourly_rate` | Numeric(10,2) | NULL |
| `proposed_total_pay` | Numeric(10,2) | NULL |
| `message` | Text | NULL |
| `status` | varchar(20) | NOT NULL, default `'pending'`, server_default `'pending'` |
| `expires_at` | timestamptz | NOT NULL |
| `decided_at` | timestamptz | NULL |
| `created_at` / `updated_at` | timestamptz | TimestampMixin |

CHECKs:
- `invitations_status_check`: `status IN ('pending','accepted','declined','withdrawn','expired')`
- `invitations_dates_check`: `end_at > start_at`
- `invitations_message_length_check`: `message IS NULL OR length(message) <= 1000`

Índices:
- `ix_invitations_freelancer_status` em `(freelancer_id, status)`
- `ix_invitations_establishment_status` em `(establishment_id, status)`
- `ix_invitations_expires_at` em `(expires_at)` (filtrado/usado pelo cron)

### Alterações em `service_contracts`
- `ALTER COLUMN application_id DROP NOT NULL`
- `ALTER COLUMN job_posting_id DROP NOT NULL`
- `ADD COLUMN invitation_id uuid NULL` FK→invitations(id)
- `ADD CONSTRAINT uq_service_contracts_invitation UNIQUE (invitation_id)` (múltiplos NULL permitidos no Postgres)
- `ADD CONSTRAINT service_contracts_origin_check CHECK`:
  `(application_id IS NOT NULL AND invitation_id IS NULL) OR (application_id IS NULL AND invitation_id IS NOT NULL)`

> O unique pré-existente `uq_service_contracts_application` permanece. Contratos do Fluxo A já existentes (todos com `application_id` preenchido e `invitation_id` NULL) satisfazem o novo CHECK → migration segura sobre dados de produção.

### Downgrade
Reverte na ordem inversa: dropa CHECK de origem + unique de invitation + coluna `invitation_id`; restaura NOT NULL em `application_id`/`job_posting_id` (seguro pois Fluxo A sempre preencheu ambos); dropa tabela `invitations`. Testado localmente (`downgrade` → `upgrade`).

## 6. Endpoints (contratos)

### Freelancer search
- `GET /v1/freelancers/search` — **estabelecimento only**. Query: `latitude`, `longitude`, `radius_km`, `skill_category_id` (opcional), `page`, `page_size`. Retorna `FreelancerSearchRead[]` com `distance_m`, ordenado por distância asc, `completed_contracts_count` desc. Exclui soft-deleted e quem não tem `location`.

### Invitations
- `POST /v1/invitations` — **estabelecimento only**. Body: `freelancer_id`, `skill_category_id`, `start_at`, `end_at`, `proposed_hourly_rate?`, `proposed_total_pay?`, `message?`. Retorna `InvitationRead` (201).
- `GET /v1/invitations` — **ambos**. Query: `status?`, `page`, `page_size`. Role-aware: estabelecimento vê enviados; freelancer vê recebidos. Retorna `InvitationList`.
- `GET /v1/invitations/{id}` — **parte do convite only**. Retorna `InvitationRead`.
- `POST /v1/invitations/{id}/accept` — **freelancer convidado only**. Cria contrato. Retorna `InvitationRead` (status accepted) + contrato referenciado no payload de notificação.
- `POST /v1/invitations/{id}/decline` — **freelancer convidado only**. Retorna `InvitationRead`.
- `POST /v1/invitations/{id}/withdraw` — **estabelecimento dono only**. Retorna `InvitationRead`.

### Schemas Pydantic principais
- `InvitationCreate`: validação de tipos + `start_at`/`end_at` aware; regras de negócio (futuro, ordem) ficam no service.
- `InvitationRead`: todos os campos públicos do convite.
- `InvitationList`: `{items, total, page, page_size}`.
- `FreelancerSearchRead`: `user_id`, `display_name`, `bio`, `avatar_url`, `completed_contracts_count`, `no_show_count`, `distance_m`. **Nunca** expõe CPF/telefone (LGPD).

## 7. Máquina de estados

### Invitation
```
pending ──accept──▶ accepted   (cria ServiceContract)
pending ──decline─▶ declined   (freelancer recusa)
pending ──withdraw▶ withdrawn  (estabelecimento retira)
pending ──cron────▶ expired    (expires_at <= now)
```
Estados terminais: accepted, declined, withdrawn, expired. Transição só a partir de `pending`.

### ServiceContract (origem nova)
Inalterada na máquina de estados (scheduled→in_progress→completed / cancelled). Muda só a **origem**: agora pode nascer de `invitation_id` em vez de `application_id`. Contrato de convite tem `job_posting_id = NULL`.

## 8. Regras transversais (validações no service)

**Criar convite (`POST /invitations`):**
- Ator deve ter papel `establishment` e perfil de estabelecimento (`ProfileRequired`).
- `freelancer_id` deve ser um `User` papel `freelancer`, não soft-deleted, com `FreelancerProfile` (`InvalidInvitationTarget` → 400).
- `start_at` no futuro e `end_at > start_at` (`InvalidInvitationWindow` → 400).
- Sem convite duplicado: não pode haver outro convite `pending` do **mesmo** `establishment_id`→`freelancer_id` com janela sobreposta (`DuplicateInvitation` → 409).
- `expires_at` calculado server-side = `min(now + settings.invitation_ttl_hours, start_at)`.
- Emite `invitation.received` ao freelancer.

**Aceitar (`POST /invitations/{id}/accept`):**
- Ator deve ser o `freelancer_id` do convite (`PermissionDenied`).
- Status deve ser `pending` (`InvitationNotPending` → 409).
- `expires_at > now`, senão `InvitationExpired` → 409.
- `has_overlap(freelancer_id, start_at, end_at)` deve ser falso (`FreelancerOverlap` → 409).
- Marca convite `accepted` + `decided_at = now`.
- Cria `ServiceContract` (origem `invitation_id`, `job_posting_id=NULL`, `agreed_*` = `proposed_*`, status `scheduled`).
- **Cascade**: demais convites `pending` do freelancer com janela sobreposta → `declined` + `decided_at` + notificação `invitation.declined` (payload `auto=true`) aos estabelecimentos.
- Emite `invitation.accepted` ao estabelecimento (payload com `contract_id`).
- `write_audit_log` (action `accept`, entity `invitation`).
- Tudo numa transação (commit único ao final).

**Recusar (`POST /invitations/{id}/decline`):** ator = freelancer convidado; status `pending`→`declined` + `decided_at`; notifica estabelecimento (`invitation.declined`, `auto=false`); audit.

**Retirar (`POST /invitations/{id}/withdraw`):** ator = estabelecimento dono; status `pending`→`withdrawn` + `decided_at`; notifica freelancer (`invitation.withdrawn`); audit.

**Busca (`GET /freelancers/search`):** ator papel `establishment`; aplica `ST_DWithin` no `location` do freelancer; exclui soft-deleted e sem `location`; join com `freelancer_skills` quando `skill_category_id` informado.

## 9. Notifications geradas
| Tipo | Destinatário | Quando |
|---|---|---|
| `invitation.received` | freelancer | convite criado |
| `invitation.accepted` | estabelecimento | freelancer aceita (payload com `contract_id`) |
| `invitation.declined` | estabelecimento | freelancer recusa (`auto=false`) ou cascade (`auto=true`) |
| `invitation.withdrawn` | freelancer | estabelecimento retira |

> Expiração via cron **não** emite notificação no MVP (decisão de enxugar; pode entrar depois).

## 10. Cron ARQ — `expire_invitations`
Função nova em `app/workers/tasks.py`, registrada em `WorkerSettings.cron_jobs` na **mesma cadência de 5 min** do `advance_contract_lifecycle`.
- Idempotente: `UPDATE invitations SET status='expired', updated_at=now() WHERE status='pending' AND expires_at <= now()` (usa `func.now()` do DB).
- Retorna `{"expired": N}` e loga `invitation_lifecycle.tick`.
- Responsabilidade separada do lifecycle de contratos (módulos coesos), apenas compartilham o agendamento.

## 11. Auditoria
`write_audit_log` em toda mutação de convite: `create`, `accept`, `decline`, `withdraw` (entity `invitation`, `entity_id`, `diff` relevante). Cascade auto-declines registram audit em lote (um por convite recusado). Expiração via cron **não** gera audit por linha (operação de sistema em massa) — coberta pelo log estruturado da rotina.

## 12. Testes (TDD)
Integração contra o DB real da VPS (mesma infra do Sprint 3), seguindo `conftest`/`factories` existentes.

- `tests/integration/test_freelancer_search.py`: filtro por skill + raio, ordenação por distância, critério secundário, paginação, exclui soft-deleted e sem-location, bloqueio de papel não-estabelecimento. (~8)
- `tests/integration/test_invitations.py`: criar (happy + validações: papel, target inválido, janela inválida, duplicado), listar (visão estabelecimento vs freelancer + filtro status), detalhar (permissão), recusar, retirar, bloqueios de permissão. (~16)
- `tests/integration/test_invitation_accept.py`: aceite cria contrato (origem invitation, job nulo), termos copiados, cascade auto-decline de sobrepostos (+ não toca os não-sobrepostos), bloqueio por overlap, por expirado, por não-pendente, por não-ser-o-convidado. (~10)
- `tests/integration/test_cron_invitation_expiry.py`: marca pendentes vencidos, ignora não-vencidos, ignora não-pendentes, idempotência, bloqueio de aceite pós-expiração. (~5)

Total estimado: **~39 testes novos**. Suíte global permanece 100% verde; `ruff` + `mypy --strict` limpos.

### Padrões obrigatórios (lições do Sprint 3)
- **Emails/identificadores únicos por execução** (uuid) — DB da VPS é compartilhado; nada de valores fixos que colidam entre runs.
- Asserções robustas a poluição: preferir checagem por ID/contagem específica do próprio teste, não composição do result set global.
- Novas factories: `make_invitation(...)` em `tests/factories.py`.

### Pontos de risco a comunicar
- Migration 005 altera tabela com dados de produção (`service_contracts`) → conferir CHECK antes de aplicar e ter downgrade testado.
- Cascade no aceite e o `has_overlap` são o núcleo de correção — cobertura adversarial obrigatória.

## 13. Dependências novas
Nenhuma. Reusa `geoalchemy2`/`shapely` (busca PostGIS, já no Sprint 2/3), `arq` (cron), stack inalterada.

## 14. Migration plan
1. Gerar `005_invitations_and_contract_origin.py` (revision `005_invitations_origin`, down_revision `004_apps_contracts_notif`).
2. `alembic upgrade head` localmente (aponta pro DB da VPS, porta 5435) — mesma prática dos sprints anteriores.
3. Verificar tabelas/constraints (`\d invitations`, CHECK de origem em `service_contracts`).
4. Testar `downgrade` → `upgrade` reversível.
5. Não há worker ARQ deployado na VPS (só infra de dados) — o cron novo roda quando o worker for iniciado; registrar em `WorkerSettings` é suficiente neste momento.

## 15. Convenções respeitadas (CLAUDE.md)
- Schemas `Create`/`Read`/`List` separados; repos retornam models, services retornam schemas; endpoints só via service.
- 100% type hints + `mypy --strict`; Conventional Commits; português em docstring/comentário, inglês em identificador.
- LGPD: `FreelancerSearchRead` nunca expõe CPF/telefone; toda mutação gera `audit_log`.
- Alembic como fonte de verdade; migration que altera dados com downgrade testado; sem migration destrutiva sem confirmar.
- Mudança de stack? Nenhuma — sem ADR necessário.

## 16. Critérios de aceite
- [ ] Estabelecimento busca freelancers por skill + raio, ordenado por distância.
- [ ] Estabelecimento envia convite com termos; freelancer recebe notificação.
- [ ] Freelancer aceita → contrato criado (origem invitation, sem job), convites sobrepostos auto-recusados, estabelecimentos notificados.
- [ ] Freelancer recusa / estabelecimento retira → status e notificações corretos.
- [ ] Convites pendentes vencidos viram `expired` via cron; aceite pós-expiração bloqueado.
- [ ] CHECK de origem única ativo; contratos do Fluxo A intactos.
- [ ] ~39 testes novos verdes; suíte global verde; `ruff` + `mypy --strict` limpos.

## 17. Próximo passo
Invocar a skill **writing-plans** para gerar o plano de implementação TDD (tasks por módulo: migration → models → schemas → repos → services → endpoints → cron → verificação/deploy/merge), espelhando a granularidade do plano do Sprint 3.
