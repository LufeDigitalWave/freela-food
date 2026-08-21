"""Testes unitários para payment_client.py (webhook signature stub)."""

import pytest

from app.core.payment_client import PaymentClient


async def test_verify_webhook_signature_rejects_all():
    """Stub DEVE rejeitar tudo (secure default até implementação real)."""
    client = PaymentClient()
    result = await client.verify_webhook_signature(b"any payload", "any-signature")
    assert result is False


async def test_verify_webhook_signature_rejects_empty():
    """Rejeita inclusive payload vazio."""
    client = PaymentClient()
    result = await client.verify_webhook_signature(b"", "")
    assert result is False


async def test_create_pix_charge_returns_stub():
    """Stub retorna PixCharge com status pending."""
    from decimal import Decimal

    client = PaymentClient()
    charge = await client.create_pix_charge(
        amount=Decimal("150.00"),
        description="Serviço de garçom - evento X",
        idempotency_key="test-idem-123",
    )
    assert charge.external_id.startswith("stub_")
    assert charge.status == "pending"
    assert charge.qr_code != ""
    assert charge.copy_paste_code != ""
