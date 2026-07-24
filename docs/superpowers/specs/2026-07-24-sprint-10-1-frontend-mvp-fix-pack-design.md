# Sprint 10.1 — Frontend MVP Fix Pack: Navegação Mobile + Fluxos Corrigidos

> Design para correção de lacunas críticas do frontend. Marketplace `freela-food`. Continuação natural do Sprint 10 (frontend inicial).

## 1. Objetivo

Transformar o frontend de "demo avançada" em "MVP navegável e funcional". Prioridades:

1. **Navegação mobile**: sidebar desktop não funciona em celular; usuário fica preso sem menu.
2. **Fluxos quebrados**: `/candidates` e `/applications` exibem dados errados ou vazios.
3. **UX consistente**: trocar `alert()` por toast, ajustar grids para mobile, documentar variáveis de ambiente.

## 2. Escopo

### Dentro

**Mobile Navigation**
- Criar componente `MobileNav` com bottom tabs para ações principais + drawer para secundárias.
- Responsividade: rotas principais acessíveis em `md:` e abaixo.
- Rotas freelancer: Início, Vagas, Contratos, Notificações, Perfil.
- Rotas establishment: Início, Vagas, Candidatos, Convites, Perfil.
- Ajustar `layout.tsx`, `sidebar.tsx`, `header.tsx` para cooperar com mobile nav.

**Fluxo Candidaturas Corrigido**
- `/applications`: mostrar candidaturas reais (não contratos).
- Usar `GET /v1/me/applications` se disponível; senão mapear com `/contracts` + filtro status pending.
- Exibir status `pending|accepted|rejected|withdrawn`.
- Permitir withdraw em pending.
- Linkar para vaga correspondente.

**Fluxo Candidatos Corrigido**
- `/candidates`: listar vagas abertas/filled do establishment.
- Para cada vaga, buscar `GET /v1/jobs/{id}/applications`.
- Agrupar candidatos por vaga.
- Permitir aceitar/rejeitar com POST `applications/{id}/accept|reject`.
- UI atualiza sem reload (otimista ou refetch).

**UX Consistente**
- Substituir `alert()` nativo por `showToast()`.
- Ajustar grids quebrados: `grid-cols-3 → grid-cols-1 sm:grid-cols-3`, `grid-cols-2 → grid-cols-1 sm:grid-cols-2`.
- Criar `frontend/.env.example` documentando `NEXT_PUBLIC_API_URL`.

**Validação e Build**
- Rodar `npm install` (instalar deps).
- Rodar `npm run lint` sem erros.
- Rodar `npm run build` sem erros.

### Fora (sprints futuras)

- Onboarding pós-cadastro → Sprint 10.3.
- Busca de freelancers → Sprint 10.2.
- Envio de convites → Sprint 10.2.
- Refresh tokens / logout real → Sprint 12.

## 3. Critérios de aceite

- [ ] Usuário consegue navegar no mobile sem sidebar desktop.
- [ ] Freelancer vê candidaturas reais em `/applications`.
- [ ] Establishment vê candidatos reais em `/candidates`, agrupados por vaga.
- [ ] Aceite/rejeição funciona pela tela.
- [ ] Sem `alert()` nativo; todas notificações usam toast.
- [ ] Grids são responsivos (mobile-first).
- [ ] `frontend/.env.example` existe e documenta `NEXT_PUBLIC_API_URL`.
- [ ] `npm run lint` passa sem erros.
- [ ] `npm run build` passa sem erros.

## 4. Decisões técnicas

1. **Bottom tabs + drawer**: tabs para ações diárias (vagas, contratos, notificações), drawer para secundárias (perfil, settings).
2. **Candidates por vaga**: agrupa por oportunidade em vez de listar solto.
3. **Toast padronizado**: consistência visual.

## 5. Próximas sprints

- Sprint 10.2: Fluxo B completo (busca freelancers + envio de convites).
- Sprint 10.3: Onboarding pós-cadastro.
- Sprint 11: Deploy MVP na VPS.
- Sprint 12: Auth/security (refresh tokens, rate limit).
- Sprint 13: Gateway Pix real.
- Sprint 14: Admin frontend.
