"""Testes dos endpoints novos de notificação: delete + count (Sprint 6)."""

import uuid

import pytest
from httpx import AsyncClient


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@test.com"


async def _register_and_login(
    client: AsyncClient, email: str
) -> dict[str, str]:
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "Senha123!", "role": "freelancer"},
    )
    login = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": "Senha123!"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.mark.asyncio
async def test_count_unread_empty(client: AsyncClient) -> None:
    email = _unique_email("cnt1")
    headers = await _register_and_login(client, email)

    resp = await client.get("/v1/me/notifications/count", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"unread": 0}


@pytest.mark.asyncio
async def test_count_unread_with_notifications(client: AsyncClient) -> None:
    from app.core.database import SessionLocal
    from app.domain.repositories.user_repository import UserRepository
    from app.domain.services.notification_service import NotificationService

    email = _unique_email("cnt2")
    headers = await _register_and_login(client, email)

    async with SessionLocal() as session:
        user = await UserRepository(session).get_by_email(email)
        assert user is not None
        await NotificationService(session).emit(
            user_id=user.id, type="test.a", payload={}
        )
        await NotificationService(session).emit(
            user_id=user.id, type="test.b", payload={}
        )
        await session.commit()

    resp = await client.get("/v1/me/notifications/count", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["unread"] == 2


@pytest.mark.asyncio
async def test_delete_notification_success(client: AsyncClient) -> None:
    from app.core.database import SessionLocal
    from app.domain.repositories.user_repository import UserRepository
    from app.domain.services.notification_service import NotificationService

    email = _unique_email("del1")
    headers = await _register_and_login(client, email)

    async with SessionLocal() as session:
        user = await UserRepository(session).get_by_email(email)
        assert user is not None
        n = await NotificationService(session).emit(
            user_id=user.id, type="test.del", payload={}
        )
        await session.commit()
        nid = n.id

    resp = await client.delete(f"/v1/notifications/{nid}", headers=headers)
    assert resp.status_code == 204

    # Confirmar que sumiu da listagem
    resp2 = await client.get("/v1/me/notifications", headers=headers)
    assert resp2.json()["total"] == 0


@pytest.mark.asyncio
async def test_delete_notification_not_owner(client: AsyncClient) -> None:
    from app.core.database import SessionLocal
    from app.domain.repositories.user_repository import UserRepository
    from app.domain.services.notification_service import NotificationService

    email_a = _unique_email("del2a")
    email_b = _unique_email("del2b")
    await _register_and_login(client, email_a)
    headers_b = await _register_and_login(client, email_b)

    async with SessionLocal() as session:
        user_a = await UserRepository(session).get_by_email(email_a)
        assert user_a is not None
        n = await NotificationService(session).emit(
            user_id=user_a.id, type="test.x", payload={}
        )
        await session.commit()
        nid = n.id

    # User B tenta deletar notification do A
    resp = await client.delete(f"/v1/notifications/{nid}", headers=headers_b)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_notification_not_found(client: AsyncClient) -> None:
    email = _unique_email("del3")
    headers = await _register_and_login(client, email)

    fake_id = uuid.uuid4()
    resp = await client.delete(f"/v1/notifications/{fake_id}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_count_reflects_unread_accurately(client: AsyncClient) -> None:
    """count_unread retorna valor correto após mark_read via service direto."""
    from app.core.database import SessionLocal
    from app.domain.repositories.user_repository import UserRepository
    from app.domain.services.notification_service import NotificationService

    email = _unique_email("cnt3")
    headers = await _register_and_login(client, email)

    async with SessionLocal() as session:
        user = await UserRepository(session).get_by_email(email)
        assert user is not None
        n = await NotificationService(session).emit(
            user_id=user.id, type="test.c", payload={}
        )
        await session.commit()
        nid = n.id

    # Marcar como lida via service (com commit)
    async with SessionLocal() as session:
        svc = NotificationService(session)
        await svc.mark_read(user_id=user.id, notif_id=nid)
        await session.commit()

    # Count deve ser 0
    resp = await client.get("/v1/me/notifications/count", headers=headers)
    assert resp.json()["unread"] == 0
