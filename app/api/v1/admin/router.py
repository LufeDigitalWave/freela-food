"""Endpoints /v1/admin/* — dashboard administrativo (Sprint 6)."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import require_admin
from app.domain.schemas.admin import (
    AdminUserDetail,
    AdminUserList,
    AdminUserRead,
    AuditLogList,
    PlatformStats,
)
from app.domain.schemas.report import ReportList, ReportRead, ResolveRequest
from app.domain.services.admin_service import AdminService
from app.domain.services.moderation_service import ModerationService

router = APIRouter(prefix="/admin", tags=["admin"])

AdminIdDep = Annotated[uuid.UUID, Depends(require_admin)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get(
    "/stats",
    response_model=PlatformStats,
    summary="Contadores agregados da plataforma",
)
async def get_platform_stats(
    _admin_id: AdminIdDep,
    session: SessionDep,
) -> PlatformStats:
    return await AdminService(session).get_platform_stats()


@router.get(
    "/users",
    response_model=AdminUserList,
    summary="Lista paginada de usuários (filtro por role, email, deleted)",
)
async def list_users(
    _admin_id: AdminIdDep,
    session: SessionDep,
    role: Annotated[str | None, Query()] = None,
    email: Annotated[str | None, Query(alias="email_search")] = None,
    include_deleted: Annotated[bool, Query()] = False,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AdminUserList:
    return await AdminService(session).list_users(
        role=role,
        email_search=email,
        include_deleted=include_deleted,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/users/{user_id}",
    response_model=AdminUserDetail,
    summary="Detalhe de um usuário (user + contagens)",
)
async def get_user_detail(
    user_id: uuid.UUID,
    _admin_id: AdminIdDep,
    session: SessionDep,
) -> AdminUserDetail:
    return await AdminService(session).get_user_detail(user_id=user_id)


@router.post(
    "/users/{user_id}/deactivate",
    response_model=AdminUserRead,
    summary="Soft-delete de usuário via admin",
)
async def deactivate_user(
    user_id: uuid.UUID,
    admin_id: AdminIdDep,
    session: SessionDep,
) -> AdminUserRead:
    return await AdminService(session).deactivate_user(
        admin_id=admin_id, user_id=user_id
    )


@router.post(
    "/users/{user_id}/reactivate",
    response_model=AdminUserRead,
    summary="Restaurar usuário soft-deleted",
)
async def reactivate_user(
    user_id: uuid.UUID,
    admin_id: AdminIdDep,
    session: SessionDep,
) -> AdminUserRead:
    return await AdminService(session).reactivate_user(
        admin_id=admin_id, user_id=user_id
    )


@router.get(
    "/audit-log",
    response_model=AuditLogList,
    summary="Log de auditoria paginado (filtros: action, entity, actor, dates)",
)
async def list_audit_log(
    _admin_id: AdminIdDep,
    session: SessionDep,
    action: Annotated[str | None, Query()] = None,
    entity: Annotated[str | None, Query()] = None,
    actor_id: Annotated[uuid.UUID | None, Query()] = None,
    since: Annotated[datetime | None, Query()] = None,
    until: Annotated[datetime | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AuditLogList:
    return await AdminService(session).list_audit_log(
        action=action,
        entity=entity,
        actor_id=actor_id,
        since=since,
        until=until,
        page=page,
        page_size=page_size,
    )


# ── Moderation (Sprint 8) ────────────────────────────────────────────────────


@router.get(
    "/reports",
    response_model=ReportList,
    summary="Fila de denúncias (filtros: status, target_type, reason)",
)
async def list_reports(
    _admin_id: AdminIdDep,
    session: SessionDep,
    status: Annotated[str | None, Query()] = None,
    target_type: Annotated[str | None, Query()] = None,
    reason: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ReportList:
    return await ModerationService(session).list_reports(
        status=status,
        target_type=target_type,
        reason=reason,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/reports/{report_id}",
    response_model=ReportRead,
    summary="Detalhe de uma denúncia",
)
async def get_report(
    report_id: uuid.UUID,
    _admin_id: AdminIdDep,
    session: SessionDep,
) -> ReportRead:
    return await ModerationService(session).get_report(report_id=report_id)


@router.post(
    "/reports/{report_id}/resolve",
    response_model=ReportRead,
    summary="Resolver denúncia (action_taken ou dismissed)",
)
async def resolve_report(
    report_id: uuid.UUID,
    payload: ResolveRequest,
    admin_id: AdminIdDep,
    session: SessionDep,
) -> ReportRead:
    return await ModerationService(session).resolve_report(
        admin_id=admin_id, report_id=report_id, payload=payload
    )


@router.post(
    "/reviews/{review_id}/hide",
    status_code=204,
    summary="Esconder review (admin)",
)
async def hide_review(
    review_id: uuid.UUID,
    admin_id: AdminIdDep,
    session: SessionDep,
) -> None:
    await ModerationService(session).hide_review(
        admin_id=admin_id, review_id=review_id
    )


@router.post(
    "/reviews/{review_id}/unhide",
    status_code=204,
    summary="Restaurar review oculta (admin)",
)
async def unhide_review(
    review_id: uuid.UUID,
    admin_id: AdminIdDep,
    session: SessionDep,
) -> None:
    await ModerationService(session).unhide_review(
        admin_id=admin_id, review_id=review_id
    )
