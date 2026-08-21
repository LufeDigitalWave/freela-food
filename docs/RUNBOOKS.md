# Runbooks — freela-food Operações

Procedimentos passo-a-passo para operações comuns em produção.

## 1. Deploy Inicial (VPS 93.127.211.7)

**Requisitos:**
- VPS Ubuntu 24.04
- Docker + docker-compose instalados
- Domínio configurado (DNS)
- SSL certificate (Caddy auto-renew)

**Passos:**

```bash
# 1. SSH na VPS
ssh root@93.127.211.7

# 2. Clonar repo
cd /opt
git clone https://github.com/LufeDigitalWave/freela-food.git
cd freela-food

# 3. Setup .env (produção)
cp .env.example .env
# Editar:
# - DATABASE_URL (Postgres VPS)
# - REDIS_URL (Redis VPS)
# - JWT_SECRET (novo)
# - SENTRY_DSN (opcional)
# - S3_* (MinIO)
nano .env

# 4. Setup Caddyfile
cat > Caddyfile << 'EOF'
{
  auto_https off
}

:80 {
  reverse_proxy /v1/* api:8000
  reverse_proxy /* frontend:3000
  
  log {
    output stdout
    format json
  }
}

freela-food.com {
  encode gzip
  reverse_proxy /v1/* api:8000
  reverse_proxy /* frontend:3000
}
EOF

# 5. Build e suba services
docker-compose -f docker-compose.deploy.yml build
docker-compose -f docker-compose.deploy.yml up -d

# 6. Verifique health
docker-compose -f docker-compose.deploy.yml ps
curl http://localhost/health
```

## 2. Rolling Deployment (sem downtime)

```bash
# 1. Novo build
cd /opt/freela-food
git pull origin main
docker-compose -f docker-compose.deploy.yml build --no-cache api frontend

# 2. Suba novos containers (old continuam)
docker-compose -f docker-compose.deploy.yml up -d --no-deps --scale api=2 api

# 3. Espere health check passar (Caddy já está loadbalancing)
sleep 30
docker-compose -f docker-compose.deploy.yml ps

# 4. Remova contêineres antigos
docker-compose -f docker-compose.deploy.yml up -d --no-deps api
docker image prune -f
```

## 3. Backup de Dados

```bash
# Executar manual
./scripts/backup-db.sh

# Agendado (cron)
# 0 2 * * * cd /opt/freela-food && ./scripts/backup-db.sh >> /var/log/freela-food-backup.log 2>&1
```

## 4. Restore de Backup

```bash
# 1. Listar backups
ls -lah backups/

# 2. Restore
./scripts/restore-db.sh backups/db-2026-08-21-020000.sql.gz

# 3. Verifique
psql freela_food -c "SELECT COUNT(*) FROM users;"
```

## 5. Rotar Secrets

**JWT_SECRET (mudar sem downtime):**
```bash
# 1. Gere novo
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 2. Update .env
sed -i 's/JWT_SECRET=.*/JWT_SECRET=new_value/' .env

# 3. Restart (refresh tokens continuam válidos)
docker-compose -f docker-compose.deploy.yml restart api worker
```

**S3/SENTRY/Database passwords:** Update .env, restart containers.

## 6. Monitoring & Logs

```bash
# Logs em tempo real
docker-compose -f docker-compose.deploy.yml logs -f api

# Apenas erros
docker-compose -f docker-compose.deploy.yml logs api | grep ERROR

# Métricas
curl http://localhost/metrics

# Sentry (se configurado)
# Acesse https://sentry.io/organizations/your-org/issues/
```

## 7. Database Maintenance

```bash
# Backup automático
PGPASSWORD=pass pg_dump -h localhost -U postgres freela_food | gzip > db-backup.sql.gz

# Vacuum (cleanup)
psql freela_food -c "VACUUM ANALYZE;"

# Reindex (performance)
psql freela_food -c "REINDEX DATABASE freela_food;"

# Check índices
psql freela_food -c "SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0;"
```

## 8. Emergency: Rollback

```bash
# 1. Stop novo deployment
docker-compose -f docker-compose.deploy.yml down

# 2. Checkout versão anterior
git checkout previous_commit

# 3. Rebuild e restart
docker-compose -f docker-compose.deploy.yml build api frontend
docker-compose -f docker-compose.deploy.yml up -d

# 4. Se DB precisa revert
./scripts/restore-db.sh backups/db-last-good.sql.gz
docker-compose -f docker-compose.deploy.yml restart api worker
```

## 9. Scaling (se necessário)

```bash
# Scale API
docker-compose -f docker-compose.deploy.yml up -d --scale api=3

# Verifique Caddy rodando load balance
curl -v http://localhost/health | grep Server

# Monitor memory/CPU
docker stats
```

## 10. SSL/TLS Renewal (Caddy auto-renew)

Caddy renova certificados automaticamente 30 dias antes do vencimento.

```bash
# Verifique status
docker-compose -f docker-compose.deploy.yml exec caddy caddy list-modules

# Logs de renew
docker-compose -f docker-compose.deploy.yml logs caddy | grep renew
```

---

## Escalação de Problemas

| Sintoma | Causa Provável | Ação |
|---------|---|---|
| 502 Bad Gateway | API down | `docker-compose ps` → restart |
| 503 Timeout | DB lento | Check `pg_stat_user_tables` |
| High memory | Memory leak | Restart container + check logs |
| Certificate error | Expired cert | Caddy auto-renew (2-3 dias) |
| Can't connect DB | Network/credentials | Verifique .env + firewall |

---

## Alertas Recomendados

Setupar no Sentry ou equivalente:

- [ ] Error rate > 1%
- [ ] Response time p95 > 5s
- [ ] Failed health checks (2+ consecutivas)
- [ ] Database connection pool exhausted
- [ ] Low disk space (< 10%)
- [ ] Redis evictions

