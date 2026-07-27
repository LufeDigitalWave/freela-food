"""Webhook endpoint para notificações de pagamento do gateway."""

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.core.payment_client import PaymentClient

router = APIRouter(tags=["webhooks"])
log = get_logger("webhook.payments")


@router.post(
    "/webhooks/payments",
    status_code=status.HTTP_200_OK,
    summary="Webhook de confirmação de pagamento do gateway Pix",
)
async def payment_webhook(request: Request) -> JSONResponse:
    body = await request.body()
    signature = request.headers.get("x-webhook-signature", "")

    client = PaymentClient()
    if not await client.verify_webhook_signature(body, signature):
        log.warning("webhook.invalid_signature")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid signature"},
        )

    # TODO: parse payload, find Payment by external_id, update status
    log.info("webhook.received", payload_size=len(body))

    return JSONResponse(content={"status": "received"})
