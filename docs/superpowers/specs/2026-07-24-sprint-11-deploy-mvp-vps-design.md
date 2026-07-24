# Sprint 11 — Deploy MVP na VPS

> Design para subir API + worker + frontend com URL acessível. Marketplace `freela-food`.

## 1. Objetivo

Deployar o freela-food completo (backend + worker + frontend) na VPS existente (`93.127.211.7`) com TLS, healthcheck e scripts operacionais mínimos.

## 2. Escopo

### Dentro

**Backend Deploy**
- Usar Dockerfile atual (multi-stage, non-root, healthcheck).
- API + worker via `docker-compose.deploy.yml`.
- Migrations via step explícito (script ou job init).
- Healthcheck liveness `/health` + readiness `/health/ready` (DB + Redis ping).

**Frontend Deploy**
- Criar `frontend/Dockerfile` multi-stage (Node 20 → standalone Next.js).
- Configurar `NEXT_PUBLIC_API_URL` para domínio público.

**Reverse Proxy / TLS**
- Caddy: TLS automático via Let's Encrypt.
- Proxy: frontend na / (porta 3000), API em /api ou subdomínio.

**Scripts Operacionais**
- `scripts/deploy.sh` — build + up + migrate.
- `scripts/backup-db.sh` — pg_dump via docker exec.
- `scripts/restore-db.sh` — pg_restore.

**Segurança Mínima**
- CORS fechado para domínio real.
- Log rotation Docker (json-file, max-size 10MB, max-file 5).
- `.dockerignore` para não copiar .venv, .git, tests, node_modules.
- Postgres/Redis/MinIO permanecem na whitelist iptables.

**Observabilidade**
- Inicializar Sentry se `SENTRY_DSN` existir (backend lifespan).
- Request-ID middleware (UUID no header + structlog).

### Fora

- CI/CD (GitHub Actions) → backlog.
- Prometheus/OpenTelemetry → backlog.
- Multi-region / load balancer.
- Domínio próprio (pode usar IP:porta no MVP).

## 3. Critérios de aceite

- [ ] API acessível em URL definida.
- [ ] Frontend acessível.
- [ ] Worker rodando (crons ativos).
- [ ] Migrations aplicadas (`008_payments`).
- [ ] `/health` retorna 200.
- [ ] `/health/ready` checa Postgres + Redis.
- [ ] Sentry captura erros se DSN configurado.
- [ ] Backup manual testado e restaurável.
- [ ] Logs disponíveis (`docker logs`).
- [ ] TLS ativo se domínio configurado.

## 4. Decisões técnicas

1. **Caddy sobre Nginx**: TLS zero-config, Caddyfile simples.
2. **Standalone Next.js**: output já configurado; image leve.
3. **Migrations fora do CMD**: evita race condition em replicas.
4. **Request-ID**: correlação de logs em prod.
