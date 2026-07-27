# Plano de Execução Master — freela-food Sprints 10.1-14

> Gerado em 2026-07-27. Usa frameworks canônicos [[task-impl-framework]] + [[project-init-framework]] + skills relevantes.

---

## 0. Contexto e Estado

| Campo | Valor |
|-------|-------|
| Projeto | freela-food — marketplace food service |
| Repo | https://github.com/LufeDigitalWave/freela-food (público, MIT) |
| Local | `C:\Users\luizf\projetos\freela-food` |
| Branch | `main` — commit `45fc641` |
| Backend | Python 3.12, FastAPI, 224 testes, 62 endpoints, mypy strict |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind v4, shadcn/ui |
| VPS | 93.127.211.7 — Postgres 5435, Redis 6380, MinIO 9000/9001 |
| Migration | `008_payments` (confirmado) |
| Skills usadas | `/brainstorming`, `/ui-ux-pro-max`, `/shadcn`, `/fastapi-python`, `/code-review`, `/verify` |

---

## 1. Sequência de Sprints

```
10.1 → 10.2 → 10.3 → 11 → 12 → 13 → 14
 └── frontend fix     └── deploy   └── pix
      └── fluxo B          └── auth    └── admin
           └── onboarding
```

**Estimativa total**: 6-10 semanas (1-2 semanas por sprint)

---

## 2. Sprint 10.1 — Frontend Fix Pack (1-2 semanas)

### Framework aplicado: [[task-impl-framework]]

### Skills sugeridas
- `/shadcn` — componentes UI (Sheet, Dialog)
- `/ui-ux-pro-max` — mobile-first layout, bottom tabs, responsive grids
- `/code-review` — antes do commit final

### Diagnóstico (Etapa 1)
- [x] Endpoints existem no backend: `GET /me/applications`, `GET /jobs/{id}/applications`, `POST /applications/{id}/accept|reject|withdraw`
- [x] Tipo `Application` existe em `frontend/src/lib/types.ts`
- [x] Sidebar usa `hidden md:flex` — sem mobile nav
- [x] `candidates/page.tsx` chama `/me/contracts` e faz `setApps([])`
- [x] `applications/page.tsx` chama `/me/contracts` (errado)
- [x] `alert()` em `jobs/page.tsx` linhas 35, 57
- [x] Grids sem breakpoint: `jobs/new` (grid-cols-3), `profile` (grid-cols-2)

### Plano (Etapa 2)

| # | Task | Arquivos | Ação |
|---|------|----------|------|
| 1 | Mobile Navigation | `bottom-tabs.tsx`, `mobile-drawer.tsx`, `header.tsx`, `layout.tsx`, `sidebar.tsx` | Criar + Modificar |
| 2 | Corrigir `/applications` | `applications/page.tsx` | Reescrever |
| 3 | Corrigir `/candidates` | `candidates/page.tsx` | Reescrever |
| 4 | UX: alerts → toast + grids | `jobs/page.tsx`, `jobs/new/page.tsx`, `profile/page.tsx` | Modificar |
| 5 | `.env.example` | `frontend/.env.example` | Criar |
| 6 | Validação + Build | — | `npm install`, `lint`, `build`, commit |

### Implementação (Etapa 3)

Seguir plano task-by-task em:
`docs/superpowers/plans/2026-07-24-sprint-10-1-frontend-mvp-fix-pack.md`

### Validação (Etapa 4)
- [ ] `npm run lint` → 0 errors
- [ ] `npm run build` → sucesso
- [ ] `npx tsc --noEmit` → 0 errors
- [ ] Mobile nav renderiza em viewport < 768px
- [ ] `/applications` mostra candidaturas reais
- [ ] `/candidates` mostra candidatos agrupados por vaga
- [ ] Aceitar/rejeitar/withdraw funciona
- [ ] Sem `alert()` no código
- [ ] Grids não quebram em mobile

### Revisão final (Etapa 5)
- [ ] Diff não contém código morto
- [ ] Sem imports não usados
- [ ] Sem `console.log` esquecido
- [ ] Nomenclatura consistente com projeto
- [ ] Toast com mensagens PT-BR

### Commit
```
feat(sprint-10.1): frontend fix pack - mobile nav + candidaturas reais + responsividade
```

---

## 3. Sprint 10.2 — Fluxo B Frontend (1-2 semanas)

### Framework aplicado: [[task-impl-framework]]

### Skills sugeridas
- `/ui-ux-pro-max` — design da busca de freelancers
- `/shadcn` — modal de convite
- `/code-review`

### Plano resumido

| # | Task | Arquivos | Ação |
|---|------|----------|------|
| 1 | Página `/freelancers` | `(dashboard)/freelancers/page.tsx` | Criar |
| 2 | Modal de convite | `components/modals/invite-freelancer.tsx` | Criar |
| 3 | Melhorar `/invitations` | `invitations/page.tsx` | Reescrever |
| 4 | Dashboard CTA | `page.tsx` (dashboard) | Modificar |
| 5 | Validação + Build | — | lint, build, commit |

### Endpoints consumidos
- `GET /v1/freelancers/search?latitude=&longitude=&radius_km=&skill_category_id=`
- `POST /v1/invitations`
- `GET /v1/invitations`
- `POST /v1/invitations/{id}/accept|decline|withdraw`

### Validação
- [ ] Establishment busca freelancer por localização
- [ ] Modal de convite funciona (POST + toast)
- [ ] Freelancer aceita/recusa convite
- [ ] Establishment retira convite
- [ ] Geocoding funciona
- [ ] Build passa

---

## 4. Sprint 10.3 — Onboarding (1 semana)

### Framework aplicado: [[task-impl-framework]]

### Skills sugeridas
- `/ui-ux-pro-max` — wizard UX
- `/shadcn` — stepper/progress components

### Plano resumido

| # | Task | Arquivos | Ação |
|---|------|----------|------|
| 1 | Wizard freelancer | `(onboarding)/freelancer/page.tsx` | Criar |
| 2 | Wizard establishment | `(onboarding)/establishment/page.tsx` | Criar |
| 3 | Guard de completude | `use-auth.ts`, `layout.tsx` | Modificar |
| 4 | Banner no dashboard | `page.tsx` (dashboard) | Modificar |
| 5 | react-hook-form + zod | forms do wizard | Integrar |
| 6 | Validação + Build | — | lint, build, commit |

### Validação
- [ ] Novo usuário cai no onboarding
- [ ] Form valida com zod
- [ ] Dados persistem via API
- [ ] Dashboard mostra banner se perfil incompleto
- [ ] Build passa

---

## 5. Sprint 11 — Deploy MVP VPS (1 semana)

### Framework aplicado: [[project-init-framework]] (seções 3, 5, 8)

### Skills sugeridas
- `/verify` — validar deploy real
- `/code-review` — Dockerfile/compose review

### Plano resumido

| # | Task | Arquivos | Ação |
|---|------|----------|------|
| 1 | Frontend Dockerfile | `frontend/Dockerfile` | Criar |
| 2 | docker-compose.deploy.yml | `docker-compose.deploy.yml` | Criar |
| 3 | Caddy config | `Caddyfile` | Criar |
| 4 | Readiness endpoint | `app/api/v1/health/router.py` | Modificar |
| 5 | Sentry init | `app/main.py` | Modificar |
| 6 | Request-ID middleware | `app/core/middleware.py` | Criar |
| 7 | `.dockerignore` | `.dockerignore` | Criar |
| 8 | Scripts operacionais | `scripts/deploy.sh`, `backup-db.sh`, `restore-db.sh` | Criar |
| 9 | Deploy na VPS | — | SSH + docker compose up |
| 10 | Validação | — | curl health, curl frontend, backup test |

### Validação
- [ ] API acessível via HTTPS (ou IP:porta)
- [ ] Frontend acessível
- [ ] Worker rodando (crons ativos)
- [ ] `/health/ready` checa DB + Redis
- [ ] Sentry captura erro de teste
- [ ] Backup restaurável

---

## 6. Sprint 12 — Auth/Security (1 semana)

### Framework aplicado: [[task-impl-framework]]

### Skills sugeridas
- `/fastapi-python` — middleware patterns
- `/code-review` — security focus
- `/supabase-postgres-best-practices` — se tocar schema

### Plano resumido

| # | Task | Arquivos | Ação |
|---|------|----------|------|
| 1 | Refresh token model/store | `app/domain/models/refresh_token.py` ou Redis keys | Criar |
| 2 | Migration (se DB) | `alembic/versions/009_refresh_tokens.py` | Criar |
| 3 | Endpoints refresh/logout | `app/api/v1/auth/router.py` | Modificar |
| 4 | Rate limit middleware | `app/core/rate_limit.py` | Criar |
| 5 | Password policy | `app/domain/services/auth_service.py` | Modificar |
| 6 | CORS hardening | `app/main.py` | Modificar |
| 7 | Frontend auth update | `frontend/src/lib/api.ts`, `use-auth.ts` | Modificar |
| 8 | Testes | `tests/integration/test_refresh.py`, `test_rate_limit.py` | Criar |
| 9 | Validação | — | pytest, lint, mypy, build |

### Validação
- [ ] Refresh token funciona
- [ ] Logout revoga refresh
- [ ] Rate limit retorna 429
- [ ] CORS não aceita wildcard em prod
- [ ] Password fraco é rejeitado
- [ ] Frontend refresh transparente
- [ ] Testes passam (backend + frontend build)

---

## 7. Sprint 13 — Gateway Pix Real (1-2 semanas)

### Framework aplicado: [[task-impl-framework]]

### Skills sugeridas
- `/fastapi-python` — webhook endpoint
- `/deep-research` — avaliar Asaas vs Mercado Pago
- `/code-review`

### Plano resumido

| # | Task | Arquivos | Ação |
|---|------|----------|------|
| 1 | ADR provider | `docs/adr/002-payment-provider.md` | Criar |
| 2 | Migration campos | `alembic/versions/009_payment_provider.py` (ou 010) | Criar |
| 3 | Provider client | `app/core/payment_client.py` | Criar |
| 4 | Webhook endpoint | `app/api/v1/webhooks/payments.py` | Criar |
| 5 | Atualizar cron lifecycle | `app/workers/tasks.py` | Modificar |
| 6 | Frontend QR code | `contracts/[id]/page.tsx` | Modificar |
| 7 | Testes webhook | `tests/integration/test_payment_webhook.py` | Criar |
| 8 | Validação | — | pytest, lint, mypy, build |

### Validação
- [ ] Payment gera cobrança no provider
- [ ] QR code visível no frontend
- [ ] Webhook confirma pagamento
- [ ] Webhook é idempotente
- [ ] Assinatura validada
- [ ] Admin vê divergências

---

## 8. Sprint 14 — Admin Frontend (1-2 semanas)

### Framework aplicado: [[task-impl-framework]]

### Skills sugeridas
- `/ui-ux-pro-max` — admin tables, filters
- `/shadcn` — DataTable, Dialog
- `/code-review`

### Plano resumido

| # | Task | Arquivos | Ação |
|---|------|----------|------|
| 1 | Layout admin | `(admin)/layout.tsx` | Criar |
| 2 | Guard admin role | `(admin)/layout.tsx` + `use-auth.ts` | Modificar |
| 3 | Dashboard stats | `(admin)/page.tsx` | Criar |
| 4 | Users page | `(admin)/users/page.tsx` | Criar |
| 5 | Reports page | `(admin)/reports/page.tsx` | Criar |
| 6 | Reviews page | `(admin)/reviews/page.tsx` | Criar |
| 7 | Payments page | `(admin)/payments/page.tsx` | Criar |
| 8 | Audit log page | `(admin)/audit-log/page.tsx` | Criar |
| 9 | Validação + Build | — | lint, build, commit |

### Validação
- [ ] Admin acessa painel
- [ ] Não-admin recebe 403/redirect
- [ ] CRUD de moderação funciona
- [ ] Paginação/filtros funcionam
- [ ] Build passa

---

## 9. Checklist Global (Framework canônico)

### Antes de cada sprint:
- [ ] Ler spec em `docs/superpowers/specs/2026-07-24-sprint-*`
- [ ] Ler plano em `docs/superpowers/plans/` (se existir)
- [ ] Diagnóstico: verificar endpoints/tipos/deps necessários
- [ ] Plano: listar arquivos criar/alterar

### Após cada sprint:
- [ ] Lint passa (`ruff check` ou `npm run lint`)
- [ ] TypeScript passa (`mypy app` ou `npx tsc --noEmit`)
- [ ] Build passa (`npm run build` ou `uv run pytest`)
- [ ] Commit com Conventional Commits
- [ ] Push para `origin/main`
- [ ] Memória atualizada se estado mudou significativamente
- [ ] Sem segredos no diff
- [ ] CLAUDE.md atualizado se roadmap mudou

---

## 10. Pré-requisitos Técnicos

### Antes de Sprint 10.1:
- [ ] `npm install` no frontend (deps ausentes)
- [ ] Verificar se `Sheet` component existe (shadcn/ui) — se não, instalar: `npx shadcn@latest add sheet`

### Antes de Sprint 11:
- [ ] Atualizar IP whitelist na VPS (iptables) para rodar testes
- [ ] Definir domínio ou subdomínio (ou usar IP:porta no MVP)
- [ ] Ter `SENTRY_DSN` configurado (criar projeto no sentry.io)

### Antes de Sprint 13:
- [ ] Criar conta no provider (Asaas ou Mercado Pago)
- [ ] Obter API keys sandbox
- [ ] Documentar webhook URL no provider

---

## 11. Skills por Sprint (Quick Reference)

| Sprint | Skills Recomendadas |
|--------|---------------------|
| 10.1 | `/shadcn`, `/ui-ux-pro-max`, `/code-review` |
| 10.2 | `/ui-ux-pro-max`, `/shadcn`, `/code-review` |
| 10.3 | `/ui-ux-pro-max`, `/shadcn` |
| 11 | `/verify`, `/code-review` |
| 12 | `/fastapi-python`, `/code-review`, `/supabase-postgres-best-practices` |
| 13 | `/fastapi-python`, `/deep-research`, `/code-review` |
| 14 | `/ui-ux-pro-max`, `/shadcn`, `/code-review` |

---

## 12. Comando Rápido para Começar

Para iniciar qualquer sprint, o comando é:

```
implementa Sprint 10.X seguindo o plano
```

Ou para execução completa:

```
siga sprint 10.1 até o final (framework task-impl, sem perguntar)
```

---

*Gerado com frameworks [[task-impl-framework]] + [[project-init-framework]] + skills `/brainstorming`, `/ui-ux-pro-max`, `/shadcn`, `/fastapi-python`.*
