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
from app.domain.services.contract_service import ContractService

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
