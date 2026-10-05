# Deploy — freela-food em VPS

Guia para deploy da stack freela-food.

## Pré-requisitos

- VPS com Docker + Docker Compose
- Postgres + PostGIS, Redis 7, MinIO como Swarm services
- Acesso SSH na VPS
- Credenciais no arquivo `.env.deploy` (ver `.env.deploy.example`)
- Chave do host da VPS em `~/.ssh/known_hosts`: o script recusa host desconhecido
  (proteção contra MITM). Conecte uma vez com `ssh root@VPS_IP` e confira o fingerprint.

## Deploy Automatizado

O script para no primeiro comando remoto que falhar (exit code != 0) e sai com código 1
também quando o health check falha. O `.env` remoto é gravado com permissão `0600`.

```bash
# 1. Preencher credenciais
cp .env.deploy.example .env.deploy
nano .env.deploy

# 2. Executar
python scripts/deploy-vps.py
```

## Deploy Manual

```bash
# 1. SSH
ssh root@VPS_IP
cd /opt/freela-food
git pull origin main

# 2. Criar .env com credenciais de produção
nano .env

# 3. Build + Up
docker compose -f docker-compose.deploy.yml build
docker compose -f docker-compose.deploy.yml up -d

# 4. Verificar
docker compose -f docker-compose.deploy.yml ps
curl http://localhost/health
```

## Rede Docker

Serviços de dados usam rede overlay `freela-food` do Swarm:

| Serviço | Hostname Interno | Porta |
|---------|-----------------|-------|
| Postgres | `freela_food_postgres` | 5432 |
| Redis | `freela_food_redis` | 6379 |
| MinIO | `freela_food_minio` | 9000 |

## Caddy + Domínio

Quando tiver domínio, editar `Caddyfile`:

```caddyfile
seudominio.com.br {
  encode gzip
  reverse_proxy /v1/* api:8000
  reverse_proxy /health api:8000
  reverse_proxy /* frontend:3000
}
```

Caddy gera SSL automaticamente via Let's Encrypt.

## Verificação

```bash
curl http://VPS_IP/health      # API liveness
curl http://VPS_IP/            # Frontend
docker compose ps              # Status containers
docker compose logs -f api     # Logs
```

## Rollback

```bash
docker compose -f docker-compose.deploy.yml down
git checkout COMMIT_ANTERIOR
docker compose -f docker-compose.deploy.yml build
docker compose -f docker-compose.deploy.yml up -d
```

## Troubleshooting

- **Containers restartando**: verificar .env (DATABASE_URL, REDIS_URL)
- **Network not found**: `docker network create --driver overlay --attachable freela-food`
- **Frontend 404**: verificar que `output: "standalone"` está no next.config.ts
- **Migração**: `docker compose run --rm api uv run alembic upgrade head`

## Checklist

- [ ] .env.deploy preenchido
- [ ] SSH testado
- [ ] `git pull` executado
- [ ] `docker compose build` OK
- [ ] `docker compose up -d` OK
- [ ] Health check retorna 200
- [ ] Frontend carrega
- [ ] API responde
