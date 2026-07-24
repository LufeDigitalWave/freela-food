# Sprint 14 — Admin Frontend

> Design do painel administrativo no frontend. Marketplace `freela-food`.

## 1. Objetivo

Dar ao operador/admin um painel funcional para moderar conteúdo, gerenciar usuários, acompanhar pagamentos e consultar audit log — consumindo os endpoints admin já existentes no backend.

## 2. Escopo

### Dentro

**Rotas**
- `/admin` — dashboard com stats da plataforma.
- `/admin/users` — listar, buscar, desativar/reativar.
- `/admin/reports` — fila de denúncias com filtros.
- `/admin/reviews` — hide/unhide reviews.
- `/admin/payments` — overview, filtros por status.
- `/admin/audit-log` — consulta por ator, entidade, ação, datas.

**Guard de Acesso**
- Apenas `role === "admin"` acessa `/admin/*`.
- Redirect para 403 ou / se não-admin.

**UI**
- Layout admin separado (sidebar com rotas admin).
- Filtros e paginação em todas as tabelas.
- Confirmação para ações destrutivas (desativar, hide, resolver).
- Estados loading/error/empty.

**Endpoints Backend Consumidos**
- `GET /v1/admin/stats`
- `GET /v1/admin/users`
- `GET /v1/admin/users/{id}`
- `POST /v1/admin/users/{id}/deactivate`
- `POST /v1/admin/users/{id}/reactivate`
- `GET /v1/admin/audit-log`
- `GET /v1/admin/reports`
- `GET /v1/admin/reports/{id}`
- `POST /v1/admin/reports/{id}/resolve`
- `POST /v1/admin/reviews/{id}/hide`
- `POST /v1/admin/reviews/{id}/unhide`
- `GET /v1/admin/payments`

### Fora

- Criação de usuário admin pelo frontend.
- Dashboard analytics avançado.
- Export CSV.

## 3. Critérios de aceite

- [ ] Admin consegue operar reports/reviews/users/payments.
- [ ] Usuário não-admin não acessa telas.
- [ ] Todas ações sensíveis têm diálogo de confirmação.
- [ ] Audit log é consultável com filtros.
- [ ] Paginação funciona em todas as listas.
- [ ] TypeScript sem erros.
- [ ] `npm run lint` e `npm run build` passam.
