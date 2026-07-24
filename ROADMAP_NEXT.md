# Roadmap Próximos Passos (Sprints 10.1-14)

**Data**: 2026-07-24  
**Status**: Specs de design gravadas em `docs/superpowers/specs/`  
**Commit**: `53719d4`

## Visão Geral

Backend está maduro (Sprints 0-9 completas, 224 testes, 62 endpoints).
Frontend existe mas tem lacunas críticas de UX/mobile.
Infra precisa de deploy + hardening.

### Abordagem Recomendada: "MVP Piloto Confiável"

Foco em transformar demo em produto usável:
1. Mobile-first + fluxos corretos
2. Deploy + segurança básica
3. Pagamento real (opcional para MVP piloto)
4. Admin operacional (opcional para MVP piloto)

---

## Sprints Propostas

### Sprint 10.1 — Frontend MVP Fix Pack

**Duração**: ~1-2 semanas  
**Foco**: Corrigir lacunas críticas de UX

**Deliverables**:
- [ ] Mobile navigation (bottom tabs + drawer)
- [ ] `/applications` mostra candidaturas reais
- [ ] `/candidates` mostra candidatos por vaga
- [ ] Todos alerts → toast
- [ ] Grids responsivos
- [ ] `npm run lint` + `npm run build` passam

**Spec**: `docs/superpowers/specs/2026-07-24-sprint-10-1-frontend-mvp-fix-pack-design.md`

---

### Sprint 10.2 — Fluxo B Frontend Completo

**Duração**: ~1-2 semanas  
**Foco**: Completar fluxo de convites diretos

**Deliverables**:
- [ ] Página `/freelancers` para buscar por proximidade/skill
- [ ] Modal de convite com termos (valor, datas, mensagem)
- [ ] `/invitations` com fluxo correto por role
- [ ] Freelancer aceita/recusa; establishment retira

**Spec**: `docs/superpowers/specs/2026-07-24-sprint-10-2-fluxo-b-frontend-design.md`

---

### Sprint 10.3 — Onboarding + Profile Completeness

**Duração**: ~1 semana  
**Foco**: Reduzir cadastros mortos

**Deliverables**:
- [ ] Wizard pós-cadastro (4 steps por role)
- [ ] Validação com `react-hook-form` + `zod`
- [ ] Dashboard mostra progresso
- [ ] Ações críticas guiam pra onboarding

**Spec**: `docs/superpowers/specs/2026-07-24-sprint-10-3-onboarding-design.md`

---

### Sprint 11 — Deploy MVP na VPS

**Duração**: ~1 semana  
**Foco**: Subir com URL acessível

**Deliverables**:
- [ ] `docker-compose.deploy.yml` (API + worker + frontend + Caddy)
- [ ] `frontend/Dockerfile` (Node 20 → standalone Next.js)
- [ ] TLS automático (Caddy)
- [ ] Healthcheck liveness + readiness
- [ ] Scripts: `deploy.sh`, `backup-db.sh`, `restore-db.sh`
- [ ] Sentry inicializado se `SENTRY_DSN` existir

**Spec**: `docs/superpowers/specs/2026-07-24-sprint-11-deploy-mvp-vps-design.md`

---

### Sprint 12 — Auth + Security Production-Ready

**Duração**: ~1 semana  
**Foco**: Preparar pra uso real

**Deliverables**:
- [ ] Refresh tokens (30d, rotação a cada uso)
- [ ] Logout real (revogação de token)
- [ ] Rate limiting (auth endpoints, operações autenticadas)
- [ ] CORS sem wildcard em prod
- [ ] Password policy (8+ chars, min 1 número)
- [ ] Security headers

**Spec**: `docs/superpowers/specs/2026-07-24-sprint-12-auth-security-design.md`

---

### Sprint 13 — Gateway Pix Real (Opcional pra Piloto)

**Duração**: ~1-2 semanas  
**Foco**: Sair de confirmação manual

**Deliverables**:
- [ ] Provider escolhido (Asaas ou Mercado Pago)
- [ ] Cobrança automática quando contrato completa
- [ ] QR code + copia-e-cola no frontend
- [ ] Webhook confirma pagamento
- [ ] Admin vê divergências

**Spec**: `docs/superpowers/specs/2026-07-24-sprint-13-pix-gateway-design.md`

---

### Sprint 14 — Admin Frontend (Opcional pra Piloto)

**Duração**: ~1-2 semanas  
**Foco**: Painel operacional

**Deliverables**:
- [ ] `/admin` dashboard com stats
- [ ] `/admin/users` (list, deactivate, reactivate)
- [ ] `/admin/reports` (resolve denúncias)
- [ ] `/admin/reviews` (hide/unhide)
- [ ] `/admin/payments` (overview)
- [ ] `/admin/audit-log` (consulta)

**Spec**: `docs/superpowers/specs/2026-07-24-sprint-14-admin-frontend-design.md`

---

## Roadmap Backlog (Pós-MVP)

- Landing pública
- Chat interno ou WhatsApp redirect
- Perfis públicos
- Favoritos / recontratação
- Cupons / referral
- Multi-cidade
- Termos / política de privacidade
- Playwright E2E tests
- CI/CD (GitHub Actions)
- Prometheus / OpenTelemetry
- PWA / notificações push
- Dark mode ativação

---

## Notas Técnicas

### VPS Status

- Host: `93.127.211.7`
- Postgres: porta 5435, migration `008_payments`
- Redis: porta 6380
- MinIO: portas 9000/9001
- ⚠️ **IP whitelist desatualizado**: pytest falha por timeout. Atualizar iptables com seu IP atual.

### Backend Estado

- 224 testes (integração + 1 unitário)
- ruff + mypy strict passam
- 62 endpoints (auth, perfis, vagas, fluxo A+B, reviews, notificações, moderação, pagamento, admin)

### Frontend Estado

- Next.js 16, React 19, TypeScript
- Tailwind v4 + shadcn/ui
- Funciona para freelancer e establishment
- ❌ Falta: mobile nav, onboarding, busca de freelancers, envio de convites, admin

---

## Como Começar

1. **Ler spec de Sprint 10.1**: `docs/superpowers/specs/2026-07-24-sprint-10-1-frontend-mvp-fix-pack-design.md`
2. **Pedir plano de implementação**: "gera plano task-by-task no formato TDD"
3. **Implementar**: task-by-task com testes no início
4. **Validar**: `npm run lint`, `npm run build`, testes passam
5. **Commit + push**: padrão Conventional Commits

---

## Contato / Suporte

Memória persistente em: `C:\Users\luizf\.claude\projects\c--Users-luizf\memory\`
- `project_freela_food.md` — estado geral
- `project_freela_food_sprint10.md` — Sprint 10 e roadmap
- `reference_freela_food_infra.md` — VPS/credenciais

GitHub: https://github.com/LufeDigitalWave/freela-food (público, MIT)
