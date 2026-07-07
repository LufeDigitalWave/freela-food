"""Endpoints /v1/me/contracts, /v1/contracts/{id}, /v1/contracts/{id}/cancel."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.domain.schemas.contract import (
    ContractCancelRequest,
    ServiceContractList,
    ServiceContractRead,
)
from app.domain.schemas.payment import ConfirmPaymentRequest, PaymentList, PaymentRead
from app.domain.services.contract_service import ContractService
from app.domain.services.payment_service import PaymentService

router = APIRouter(tags=["contracts"])

UserIdDep = Annotated[uuid.UUID, Depends(get_current_user_id)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get(
    "/me/contracts",
    response_model=ServiceContractList,
    summary="Lista contratos do user (como freelancer ou estabelecimento)",
)
async def list_my_contracts(
    user_id: UserIdDep,
    session: SessionDep,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ServiceContractList:
    return await ContractService(session).list_mine(
        user_id=user_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/contracts/{contract_id}",
    response_model=ServiceContractRead,
    summary="Detalhe de um contrato (apenas partes)",
)
async def get_contract(
    contract_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> ServiceContractRead:
    return await ContractService(session).get_by_id(
        user_id=user_id, contract_id=contract_id
    )


@router.post(
    "/contracts/{contract_id}/cancel",
    response_model=ServiceContractRead,
    summary="Cancela contrato (freelancer ou estabelecimento parte)",
)
async def cancel_contract(
    contract_id: uuid.UUID,
    payload: ContractCancelRequest,
    user_id: UserIdDep,
    session: SessionDep,
) -> ServiceContractRead:
    return await ContractService(session).cancel(
        user_id=user_id, contract_id=contract_id, payload=payload
    )


# ── Payments (Sprint 9) ───────────────────────────────────────────────────────


@router.get(
    "/contracts/{contract_id}/payment",
    response_model=PaymentRead,
    summary="Status do pagamento do contrato (ambas partes)",
)
async def get_payment(
    contract_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> PaymentRead:
    return await PaymentService(session).get_for_contract(
        user_id=user_id, contract_id=contract_id
    )


@router.post(
    "/contracts/{contract_id}/payment/confirm",
    response_model=PaymentRead,
    summary="Establishment confirma pagamento realizado",
)
async def confirm_payment(
    contract_id: uuid.UUID,
    payload: ConfirmPaymentRequest,
    user_id: UserIdDep,
    session: SessionDep,
) -> PaymentRead:
    return await PaymentService(session).confirm(
        user_id=user_id, contract_id=contract_id, payload=payload
    )


@router.post(
    "/contracts/{contract_id}/payment/dispute",
    response_model=PaymentRead,
    summary="Freelancer contesta que não recebeu pagamento",
)
async def dispute_payment(
    contract_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> PaymentRead:
    return await PaymentService(session).dispute(
        user_id=user_id, contract_id=contract_id
    )


@router.get(
    "/me/payments",
    response_model=PaymentList,
    summary="Histórico de pagamentos do user",
)
async def list_my_payments(
    user_id: UserIdDep,
    session: SessionDep,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaymentList:
    return await PaymentService(session).list_mine(
        user_id=user_id, status_filter=status_filter, page=page, page_size=page_size
    )
