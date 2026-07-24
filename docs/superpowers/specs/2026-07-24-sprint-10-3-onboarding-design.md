# Sprint 10.3 — Onboarding + Profile Completeness

> Design para reduzir cadastros mortos e garantir dados mínimos. Marketplace `freela-food`.

## 1. Objetivo

Implementar wizard pós-cadastro que coleta dados mínimos necessários para matching, geolocalização e pagamento — reduzindo taxa de abandono.

## 2. Escopo

### Dentro

**Freelancer Onboarding**
1. Dados públicos: nome, telefone, bio.
2. Localização: endereço/CEP, raio de atuação.
3. Skills: ao menos uma.
4. Pix: chave (opcional para MVP, requerido pra receber).

**Establishment Onboarding**
1. Nome do estabelecimento.
2. Telefone.
3. Endereço.
4. Tipo de estabelecimento.

**Guard de Completude**
- Dashboard mostra banner "complete seu perfil".
- Ações críticas orientam: freelancer sem localização não busca vaga por raio.

**Fluxo**
- Novo usuário cai no onboarding após register.
- Cada seção é um step separado.
- Botão "Skip" com aviso (opcional).
- Progresso visual (1/4, 2/4, etc).

### Fora

- Email verification.
- Telefone SMS verification.

## 3. Critérios de aceite

- [ ] Novo usuário cai no onboarding.
- [ ] Perfil mínimo fica completo antes do uso principal.
- [ ] Dashboard indica claramente o que falta.
- [ ] Form valida com `react-hook-form` + `zod`.
- [ ] Progresso não se perde ao recarregar.
- [ ] Skip é possível mas avisa.
- [ ] TypeScript sem erros.
- [ ] `npm run lint` e `npm run build` passam.
