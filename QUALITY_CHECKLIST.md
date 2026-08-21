# Quality Checklist — freela-food MVP

## Frontend (next-dev com npm run dev)

- [ ] Landing page renderiza em mobile/desktop
- [ ] Todas as 32 rotas compilam (`npm run build`)
- [ ] Zero ESLint errors (`npm run lint`)
- [ ] TypeScript strict mode sem erros
- [ ] E2E tests passam (37/37 com `npx playwright test`)
- [ ] Skip-to-content link ativável por Tab
- [ ] Sidebar/navbar/footer têm aria-labels
- [ ] Notificações com aria-live updates
- [ ] Service Worker registra em produção (não dev)
- [ ] Manifest.json válido (Chrome DevTools)

## Backend

- [ ] `uv run ruff check` — zero erros
- [ ] `uv run mypy app/ --strict` — zero erros
- [ ] `uv run pytest -x` — 224+ testes passam
- [ ] Migrations aplicadas (`alembic upgrade head`)
- [ ] Seed data disponível (opcional)
- [ ] Logs não incluem PII (estrutlog filter ativo)
- [ ] JWTs expiram corretamente (60 min)
- [ ] Rate limiting ativo nos endpoints sensíveis
- [ ] Webhook retries com exponential backoff
- [ ] CORS restrito (não wildcard em prod)

## CI/CD (GitHub Actions)

- [ ] Workflow `.github/workflows/ci.yml` defini
- [ ] Backend lint + type-check + tests
- [ ] Frontend build + E2E tests
- [ ] Services (Postgres, Redis) spinned via compose
- [ ] Concurrency prevents duplicate runs
- [ ] Artifact output (test results, coverage)

## Documentation

- [ ] README atualizado (stack, como rodar, status)
- [ ] CLAUDE.md mantém conventions
- [ ] ADR folder com decisões arquiteturais
- [ ] PWA.md explica offline + install
- [ ] API Docs gerados (62 endpoints documentados)
- [ ] Changelog updated

## Security

- [ ] No secrets in .env.example
- [ ] No hardcoded credentials em código
- [ ] Passwords hashed com bcrypt (cost ≥ 12)
- [ ] JWT refresh tokens rodacionados
- [ ] LGPD endpoints (`/me/export`, `DELETE /me`)
- [ ] Audit log preenchido em mutações sensíveis
- [ ] CPF/RG criptografados em repouso
- [ ] SQL injection mitigated (parameterized queries)

## Performance (Baseline)

- [ ] Bundle size < 500KB gzipped (Next.js)
- [ ] Lighthouse score ≥ 80 (public pages)
- [ ] API response time < 200ms (p95)
- [ ] Database queries indexed (explain analyze)
- [ ] N+1 queries eliminated
- [ ] Caching headers set (public/private/max-age)
- [ ] Images lazy-loaded (<img loading=lazy>)

## Deployment Readiness

- [ ] Docker images build successfully
- [ ] Health checks respond correctly
- [ ] Environment variables documented
- [ ] Database migrations reversible
- [ ] Rollback procedure documented
- [ ] Monitoring/logging configured (Sentry, if enabled)
- [ ] Backup strategy in place

## Accessibility (WCAG AA Target)

- [ ] All 32 pages have <title> + meta description
- [ ] Main content labeled (id=main-content)
- [ ] Navigation landmarks (<nav>, <aside>, <header>, <main>)
- [ ] Skip-to-content link functional
- [ ] Icon buttons have aria-label
- [ ] Form inputs associated with labels
- [ ] Heading hierarchy correct (no h1 → h3 jumps)
- [ ] Focus visible on interactive elements
- [ ] Color contrast ≥ 4.5:1 (WCAG AA)
- [ ] Mobile accessible at 320px width

## Data

- [ ] Database schemas clean (no orphaned columns)
- [ ] Test data seedable in dev
- [ ] Backups automated (VPS)
- [ ] Sensitive data retention policy defined
- [ ] GDPR/LGPD consent captured

## Go/No-Go Criteria

**GO if all of:**
- 224+ backend tests passing
- 37/37 E2E tests passing
- 0 ESLint errors
- 0 mypy errors
- npm build succeeds
- Lighthouse public pages ≥ 80
- No critical security issues
- All landing + institutional pages accessible

**NO-GO if:**
- Any critical security finding
- > 10% E2E test failure rate
- Production bundle > 1MB
- API response time > 500ms
- Database query without index
- Hardcoded secrets found

---

**Last updated:** 2026-08-21  
**MVP Target:** Closed beta week of 08-26  
**Public launch:** September 2026
