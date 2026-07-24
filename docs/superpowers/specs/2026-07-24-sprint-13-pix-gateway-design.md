# Sprint 13 — Gateway Pix Real

> Design para sair de confirmação Pix manual para fluxo real com provider. Marketplace `freela-food`.

## 1. Objetivo

Integrar gateway de pagamento Pix (Asaas ou Mercado Pago) para geração automática de cobranças, confirmação via webhook e exposição de QR code no frontend.

## 2. Escopo

### Dentro

**Backend**
- ADR escolhendo provider (Asaas ou Mercado Pago).
- Client HTTP do provider (async, retry, timeout).
- Migration: adicionar campos em `payments`:
  - `provider` (varchar).
  - `external_id` (varchar unique).
  - `provider_status` (varchar).
  - `qr_code` (text — base64 da imagem).
  - `copy_paste_code` (text — copia-e-cola).
  - `webhook_received_at` (timestamptz).
  - `provider_payload` (jsonb).
  - `idempotency_key` (uuid unique).
- Webhook endpoint: `POST /v1/webhooks/payments`.
  - Validação de assinatura do provider.
  - Idempotência por `external_id`.
  - Atualiza status do payment.
  - Emite notificação.
- Criação automática de cobrança quando contrato completa (no cron lifecycle).
- Admin: vê divergências provider vs local.

**Frontend**
- Tela de pagamento mostra QR code e copia-e-cola.
- Status atualiza em polling ou SSE.
- Establishment não precisa mais confirmar manualmente (provider confirma via webhook).
- Fallback: manter confirmação manual se provider falhar.

### Fora

- Split payment (repasse direto ao freelancer).
- Boleto/cartão.
- Saque/wallet interna.
- Conciliação batch.

## 3. Critérios de aceite

- [ ] Payment pending gera Pix real no provider.
- [ ] Frontend mostra QR code e copia-e-cola.
- [ ] Webhook muda status para confirmed.
- [ ] Webhook é idempotente (reprocessar não duplica).
- [ ] Assinatura do webhook é validada.
- [ ] Admin vê falhas/divergências.
- [ ] Fallback manual existe se provider estiver offline.
- [ ] Migration com downgrade testado.
- [ ] Testes: criação, webhook confirmed, webhook duplicado, assinatura inválida.

## 4. Decisões técnicas

1. **Asaas (recomendação inicial)**: API brasileira focada em cobrança, bom para marketplace.
2. **Idempotency key**: UUID gerado no cron, salvo antes de chamar provider.
3. **Webhook com validação de signature**: evita spoofing.
4. **Provider_payload jsonb**: salvar resposta completa para auditoria.
