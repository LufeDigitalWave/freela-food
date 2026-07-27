# ADR-002: Payment Gateway Provider

## Status
Pending (skeleton implementado, integração real depende de conta sandbox)

## Context
Pagamentos até Sprint 9 são manuais (establishment confirma via POST). Sprint 13 introduz gateway Pix real.

## Decision
**Asaas** como provider primário:
- API brasileira focada em cobranças/Pix.
- Bom para marketplace B2B/serviços.
- Webhook com assinatura HMAC.

Alternativa: Mercado Pago (se Asaas não atender requisitos de split).

## Consequences
- Migration para adicionar campos de provider na tabela `payments`.
- Novo módulo `app/core/payment_client.py`.
- Webhook endpoint `POST /v1/webhooks/payments`.
- Frontend mostra QR code/copia-e-cola.
- Confirmação manual permanece como fallback.

## Next steps
1. Criar conta sandbox Asaas.
2. Obter API key.
3. Implementar client real.
4. Testar webhook end-to-end.
