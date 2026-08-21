# Observabilidade — freela-food

## Estrutura

### 1. Logging Estruturado (structlog)

Todos os logs usam **structlog** com formato JSON em produção.

```python
from app.core.logging import get_logger

log = get_logger("mymodule.function")
log.info("user_registered", user_id=user.id, email=user.email)
log.warning("high_latency", response_time_ms=523)
log.error("db_error", exception=str(e), stack_trace=traceback.format_exc())
```

**PII Filtrada automaticamente:** CPF, RG, email, password não aparecem em logs.

Arquivo: `app/core/logging.py`

### 2. Sentry (Error Tracking + APM)

Rastreamento de erros e performance monitoring via Sentry.

#### Setup

```bash
# 1. Instalar
uv add sentry-sdk[fastapi]

# 2. Configurar .env
SENTRY_DSN=https://key@sentry.io/project-id
```

#### Como funciona

- Inicializa no lifespan da aplicação (`app/main.py`)
- Integra com: FastAPI, SQLAlchemy, Redis, logging
- Sample rate: 1.0 em dev, 0.1 em prod (10% de traces)
- Profile sampling: 0 em dev, 0.1 em prod (10% de profiles)
- PII é filtrado automaticamente (`before_send` hook)

#### Uso manual

```python
import sentry_sdk

# Capturar exceção explicitamente
try:
    risky_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)

# Marcar transação
with sentry_sdk.start_transaction(op="db", name="save_user"):
    await db.save(user)

# Adicionar breadcrumb
sentry_sdk.add_breadcrumb(
    category="user",
    message="User login",
    level="info",
    data={"user_id": user_id}
)
```

#### Monitoramento

- Painel: https://sentry.io/organizations/[org]/issues/
- Alerts por threshold de erros/latência
- Release tracking (marcar releases para rastrear regressões)

Arquivo: `app/core/sentry_client.py`

### 3. Performance

#### Frontend (Next.js)

- **bundle-size:** 1.6 MB (.next/static)
- **Lighthouse target:** ≥ 90
- **Performance budget:** veja `frontend/performance-budget.json`
- **Otimizações ativas:**
  - Image optimization (AVIF + WebP)
  - Tree-shaking lucide-react via `experimental.optimizePackageImports`
  - Security headers (CSP, X-Frame-Options, etc.)

#### Backend (FastAPI)

- **Query logging:** `structlog` captura SQL lento (> 100ms)
- **Middleware metrics:** tempo de resposta por endpoint
- **Health check:** `GET /health` (liveness + readiness)

### 4. Métricas (Futuro)

Preparação para Prometheus/OpenTelemetry:

```bash
# Instalação futura
uv add prometheus-client opentelemetry-api opentelemetry-sdk
```

Endpoints de métricas via middleware:
- `GET /metrics` (Prometheus format)
- Contadores: requests, errors, latency
- Histogramas: response time por endpoint

---

## Checklist de Deploy

- [ ] `SENTRY_DSN` configurado em produção
- [ ] Sentry release linked ao git commit
- [ ] Logging level = INFO em prod, DEBUG em dev
- [ ] Structlog output = JSON em prod, human-readable em dev
- [ ] Health checks passando
- [ ] Lighthouse audit ≥ 90 (público)
- [ ] Sem hardcoded secrets em logs/errors

---

## Dashboards Recomendados

1. **Sentry** — erros em tempo real
2. **Prometheus** (futuro) — métricas de infra
3. **DataDog** (futuro) — correlação logs/metrics/traces
4. **Grafana** (futuro) — dashboards customizados

---

## Troubleshooting

### "Sentry DSN not configured"
- Normal em dev se `SENTRY_DSN` não estiver em `.env`
- Adicione para testar: `SENTRY_DSN=https://fake@fake.ingest.sentry.io/123`

### PII aparecendo em Sentry
- Confirmar que `sentry_client.py` `_filter_pii` está capturando a chave
- Adicionar à lista `_sensitive_keys` se necessário

### APM traces não aparecem
- Verificar `traces_sample_rate` em `.env` ou `app/core/sentry_client.py`
- Em prod, usa 0.1 (10%) — aumentar para 1.0 para debug
