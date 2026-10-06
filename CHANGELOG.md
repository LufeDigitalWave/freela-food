# Changelog

Todas as mudanças notáveis do projeto serão documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto segue [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Added (Sprints 15-18)
- Public landing page with hero, features, stats, CTA
- Institutional pages: /como-funciona, /sobre, /termos, /privacidade
- Offline fallback page
- PWA support: manifest.json, Service Worker, PWA metadata
- Playwright E2E test suite (37 tests): landing, institutional, auth, navigation, mobile, a11y
- GitHub Actions CI/CD pipeline: lint + type-check + tests + build + E2E
- Production Next.js config: gzip, image optimization, security headers, cache control
- Sentry integration (backend) with PII filtering
- structlog structured logging
- Skip-to-content link (sr-only)
- WCAG AA improvements: aria-labels, landmarks, focus management
- Auth layout metadata (robots: noindex)
- Quality checklist documentation
- Observability documentation
- Runbooks (deploy, backup, restore, rollback)
- Contributing guide
- Performance budget
- Font-display swap (Inter, Instrument Serif)

### Changed
- README: full status update with 13 new commits metrics
- Frontend layout: viewport export (theme color, initial scale)
- README roadmap: Sprints 15-17 marked complete

### Fixed
- 9 ESLint errors (entity escaping, React hooks, fonts)
- Flaky integration test (order dependency)
- Viewport metadata deprecation warning

## [0.1.0] - 2026-07-27

### Added (Sprints 0-14)
- Custom JWT HS256 authentication (login, register, refresh tokens)
- User profiles (freelancer, establishment) with avatars
- LGPD compliance: /me/export, DELETE /me
- Job posting CRUD with geolocation (PostGIS ST_DWithin)
- Application flow (Fluxo A): candidature → accept → contract
- Invitation flow (Fluxo B): freelancer search → direct invite
- Service contracts with lifecycle management
- Anti-retaliation reviews with visibility rules
- In-app notifications
- Matching engine (multi-factor scoring)
- Moderation: reports, hide/unhide reviews
- Payment registration (manual Pix confirmation)
- Admin dashboard: stats, users, audit log, moderation
- Payment gateway skeleton (Asaas)
- 62 API endpoints
- 224 backend tests (integration + unit)
- 25 frontend pages (freelancer + establishment)
- Docker + Caddy deployment config
- Healthcheck (liveness + readiness)
- CI/CD pipeline (lint + tests + build)
- ARQ workers with cron jobs
- structlog with PII filter
- Rate limiting (auth endpoints)
- CORS hardening
- Password policy

### Infrastructure
- PostgreSQL 15 + PostGIS
- Redis 7 + ARQ
- MinIO (S3-compatible)
- Alembic migrations
- Docker multi-stage build
- VPS deployment (<VPS_IP>)

---

**Maintained by:** Luiz Felipe (luiz23.lfsc@gmail.com)  
**License:** MIT  
**Repository:** https://github.com/LufeDigitalWave/freela-food
