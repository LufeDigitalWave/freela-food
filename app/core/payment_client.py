"""Payment gateway client — abstração para Asaas/MP.

Skeleton: implementação real depende de conta sandbox + API key.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger("payment_client")


@dataclass
class PixCharge:
    external_id: str
    qr_code: str
    copy_paste_code: str
    status: str


class PaymentClient:
    """Client para criar cobranças Pix via gateway.

    TODO: implementar com httpx quando tiver API key do Asaas.
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    async def create_pix_charge(
        self,
        *,
        amount: Decimal,
        description: str,
        idempotency_key: str,
    ) -> PixCharge:
        log.info(
            "payment_client.create_pix_charge.stub",
            amount=str(amount),
            idempotency_key=idempotency_key,
        )
        return PixCharge(
            external_id=f"stub_{idempotency_key}",
            qr_code="STUB_QR_CODE_BASE64",
            copy_paste_code="STUB_COPY_PASTE_PIX_CODE",
            status="pending",
        )

    async def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        log.info("payment_client.verify_signature.stub")
        return True
