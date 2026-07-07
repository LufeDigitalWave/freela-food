"""Service de Payment — criação automática, confirmação, disputa (Sprint 9)."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, PermissionDenied
from app.domain.models.freelancer_profile import FreelancerProfile
from app.domain.repositories.contract_repository import ContractRepository
from app.domain.repositories.payment_repository import PaymentRepository
from app.domain.schemas.payment import (
    ConfirmPaymentRequest,
    PaymentList,
    PaymentRead,
)
from app.domain.services.notification_service import NotificationService
from app.utils.audit import write_audit_log


class PaymentAlreadyConfirmed(ConflictError):
    detail = "Pagamento já foi confirmado"


class PaymentAlreadyDisputed(ConflictError):
    detail = "Pagamento já está em disputa"


class PaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._payments = PaymentRepository(session)
        self._contracts = ContractRepository(session)
        self._notifications = NotificationService(session)

    async def create_for_contract(
        self, *, contract_id: uuid.UUID, freelancer_id: uuid.UUID
    ) -> None:
        """Cria payment pending pro contrato completed. Chamado pelo cron."""
        # Verificar se já existe
        existing = await self._payments.get_by_contract_id(contract_id)
        if existing is not None:
            return  # idempotente

        contract = await self._contracts.get_by_id(contract_id)
        if contract is None:
            return

        # Calcular amount
        if contract.agreed_total_pay:
            amount = contract.agreed_total_pay
        elif contract.agreed_hourly_rate:
            hours = Decimal(
                str((contract.end_at - contract.start_at).total_seconds() / 3600)
            )
            amount = (contract.agreed_hourly_rate * hours).quantize(Decimal("0.01"))
        else:
            amount = Decimal("0.00")

        # Buscar pix_key do freelancer
        fp = await self._session.scalar(
            select(FreelancerProfile.pix_key).where(
                FreelancerProfile.user_id == freelancer_id
            )
        )

        await self._payments.create(
            contract_id=contract_id,
            amount=amount,
            pix_key=fp,
        )

        # Notificar freelancer
        await self._notifications.emit(
            user_id=freelancer_id,
            type="payment.pending",
            payload={"contract_id": str(contract_id), "amount": str(amount)},
        )

    async def get_for_contract(
        self, *, user_id: uuid.UUID, contract_id: uuid.UUID
    ) -> PaymentRead:
        contract = await self._contracts.get_by_id(contract_id)
        if contract is None:
            raise NotFoundError("Contrato não encontrado")
        if user_id not in (contract.freelancer_id, contract.establishment_id):
            raise PermissionDenied()

        payment = await self._payments.get_by_contract_id(contract_id)
        if payment is None:
            raise NotFoundError("Pagamento ainda não disponível")
        return PaymentRead.model_validate(payment)

    async def confirm(
        self,
        *,
        user_id: uuid.UUID,
        contract_id: uuid.UUID,
        payload: ConfirmPaymentRequest,
    ) -> PaymentRead:
        contract = await self._contracts.get_by_id(contract_id)
        if contract is None:
            raise NotFoundError("Contrato não encontrado")
        if user_id != contract.establishment_id:
            raise PermissionDenied("Apenas o estabelecimento pode confirmar pagamento")

        payment = await self._payments.get_by_contract_id(contract_id)
        if payment is None:
            raise NotFoundError("Pagamento não encontrado")
        if payment.status == "confirmed":
            raise PaymentAlreadyConfirmed()

        payment.status = "confirmed"
        payment.confirmed_at = datetime.now(UTC)
        payment.confirmed_by = user_id
        payment.notes = payload.notes
        await self._session.flush()

        # Notificar freelancer
        await self._notifications.emit(
            user_id=contract.freelancer_id,
            type="payment.confirmed",
            payload={"contract_id": str(contract_id), "amount": str(payment.amount)},
        )

        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="confirm",
            entity="payment",
            entity_id=payment.id,
        )

        await self._session.commit()
        await self._session.refresh(payment)
        return PaymentRead.model_validate(payment)

    async def dispute(
        self, *, user_id: uuid.UUID, contract_id: uuid.UUID
    ) -> PaymentRead:
        contract = await self._contracts.get_by_id(contract_id)
        if contract is None:
            raise NotFoundError("Contrato não encontrado")
        if user_id != contract.freelancer_id:
            raise PermissionDenied("Apenas o freelancer pode disputar pagamento")

        payment = await self._payments.get_by_contract_id(contract_id)
        if payment is None:
            raise NotFoundError("Pagamento não encontrado")
        if payment.status == "disputed":
            raise PaymentAlreadyDisputed()

        payment.status = "disputed"
        payment.disputed_at = datetime.now(UTC)
        await self._session.flush()

        # Notificar establishment
        await self._notifications.emit(
            user_id=contract.establishment_id,
            type="payment.disputed",
            payload={"contract_id": str(contract_id), "amount": str(payment.amount)},
        )

        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="dispute",
            entity="payment",
            entity_id=payment.id,
        )

        await self._session.commit()
        await self._session.refresh(payment)
        return PaymentRead.model_validate(payment)

    async def list_mine(
        self,
        *,
        user_id: uuid.UUID,
        status_filter: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaymentList:
        items, total = await self._payments.list_for_user(
            user_id, status_filter=status_filter, page=page, page_size=page_size
        )
        return PaymentList(
            items=[PaymentRead.model_validate(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def list_all_admin(
        self,
        *,
        status_filter: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaymentList:
        items, total = await self._payments.list_all(
            status_filter=status_filter, page=page, page_size=page_size
        )
        return PaymentList(
            items=[PaymentRead.model_validate(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
        )
