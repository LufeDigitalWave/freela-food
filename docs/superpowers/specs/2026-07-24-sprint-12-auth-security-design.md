# Sprint 12 — Segurança e Auth Production-Ready

> Design para reduzir risco de conta comprometida e abuso. Marketplace `freela-food`.

## 1. Objetivo

Implementar refresh tokens com revogação, rate limiting em endpoints críticos, e hardening de CORS/headers para preparar o produto para uso real.

## 2. Escopo

### Dentro

**Refresh Token + Logout Real**
- Access token: 15min (reduzir de 60min).
- Refresh token: opaco, 30 dias, rotação a cada uso.
- Armazenamento: hash SHA-256 no Redis (TTL 30d) OU tabela `refresh_tokens`.
- Endpoints: `POST /auth/refresh`, `POST /auth/logout`.
- Logout revoga refresh token.
- Blacklist opcional de access token via `jti` até expirar (Redis SET com TTL).

**Rate Limiting**
- Redis-backed (ratelimit ou custom middleware).
- Prioridade:
  - `/auth/login`: 5 req/min por IP.
  - `/auth/register`: 3 req/min por IP.
  - Uploads: 10 req/min por user.
  - Endpoints mutáveis: 30 req/min por user.

**Frontend Auth**
- Migrar token para cookie httpOnly (ideal).
- Se manter Bearer no MVP: refresh automático no interceptor 401.
- Logout limpa cookie/localStorage + chama `/auth/logout`.

**Hardening**
- CORS sem wildcard em prod (origin explícita).
- Security headers (via Caddy ou middleware): X-Content-Type-Options, X-Frame-Options, Strict-Transport-Security.
- Password policy: mínimo 8 chars, ao menos 1 número.
- Audit log em eventos auth (login, logout, refresh, password change).

### Fora

- 2FA/MFA.
- OAuth social login.
- CAPTCHA.

## 3. Critérios de aceite

- [ ] Sessão renova sem relogar (refresh token funcional).
- [ ] Logout invalida refresh token.
- [ ] Access token velho não funciona após expiração.
- [ ] Brute force em login é limitado (429 após threshold).
- [ ] CORS prod não aceita wildcard.
- [ ] Password policy aplicada no register.
- [ ] Migration para refresh_tokens (se DB) ou keys Redis documentadas.
- [ ] Frontend faz refresh transparente.
- [ ] Testes cobrem: refresh happy path, refresh revogado, rate limit hit, logout.

## 4. Decisões técnicas

1. **Redis para refresh tokens**: performance + TTL nativo; evita migration se preferir.
2. **Rotação a cada refresh**: limita janela de token comprometido.
3. **Cookie httpOnly se possível**: mais seguro que localStorage; requer same-origin ou subdomain.
4. **Rate limit por IP + por user**: IP para auth, user para operações autenticadas.
