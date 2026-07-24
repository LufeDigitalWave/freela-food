# Sprint 10.2 — Fluxo B Completo no Frontend: Busca + Convite Direto

> Design para completar o fluxo de convites diretos no frontend. Marketplace `freela-food`.

## 1. Objetivo

Implementar busca de freelancers por proximidade/skill e permitir que establishments enviem convites diretos — completando o Fluxo B do lado do usuário.

## 2. Escopo

### Dentro

**Página `/freelancers`**
- Nova página para establishment.
- Filtros: endereço/CEP, raio, skill/category, data/hora do plantão.
- Resultados: nome, bio, distância, rating, no-show count, contratos concluídos.
- CTA "Convidar" abre modal de convite.

**Modal/Form de Convite**
- Campos: freelancer, skill, data início, data fim, valor hora OU total, mensagem.
- Chamada: `POST /invitations`.
- Sucesso: confirmar e voltar à lista.
- Erro: mostrar toast + manter form preenchido.

**Melhorar `/invitations`**
- Separar por role: establishment vê enviados; freelancer vê recebidos.
- Freelancer: aceitar/recusar convite.
- Establishment: retirar convite.

**Dashboard establishment**
- Atualizar CTA "Buscar freelancers" para apontar para `/freelancers`.

### Fora

- Matching score em tempo real.
- Salvação de busca/favoritos.
- Notificação push.

## 3. Critérios de aceite

- [ ] Establishment consegue buscar freelancer por localização.
- [ ] Establishment envia convite com termos propostos.
- [ ] Freelancer visualiza e aceita/recusa convite.
- [ ] Aceite cria contrato visível em `/contracts`.
- [ ] `/invitations` mostra fluxo correto por role.
- [ ] Geocoding funciona (Nominatim ou backend).
- [ ] Todos os estados de erro/loading/empty são tratados.
- [ ] TypeScript sem erros.
- [ ] `npm run lint` e `npm run build` passam.
