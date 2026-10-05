"""Testes do endpoint /v1/notifications."""

from __future__ import annotations

import uuid
from itertools import pairwise

import pytest
from httpx import AsyncClient


def _unique_email(prefix: str) -> str:
    """Email único por execução pra evitar pollution entre runs do mesmo teste."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}@test.com"


@pytest.mark.asyncio
async def test_list_my_notifications_empty(client: AsyncClient) -> None:
    """User novo não tem notifications, lista retorna vazia."""
    email = _unique_email("n1")
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "Senha123!", "role": "freelancer"},
    )
    login = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": "Senha123!"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/v1/me/notifications", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["unread_count"] == 0


@pytest.mark.asyncio
async def test_emit_and_list_notification(client: AsyncClient) -> None:
    """Notification persistida via service direto aparece na listagem."""
    from app.core.database import SessionLocal
    from app.domain.repositories.user_repository import UserRepository
    from app.domain.services.notification_service import NotificationService

    email = _unique_email("n2")
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "Senha123!", "role": "freelancer"},
    )
    login = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": "Senha123!"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    async with SessionLocal() as session:
        user = await UserRepository(session).get_by_email(email)
        assert user is not None
        await NotificationService(session).emit(
            user_id=user.id,
            type="application.received",
            payload={"job_posting_id": "fake"},
        )
        await session.commit()

    resp = await client.get("/v1/me/notifications", headers=headers)
    body = resp.json()
    assert body["total"] == 1
    assert body["unread_count"] == 1
    assert body["items"][0]["type"] == "application.received"


@pytest.mark.asyncio
async def test_unread_only_filter(client: AsyncClient) -> None:
    """Filtro unread_only=true só retorna não-lidas."""
    from app.core.database import SessionLocal
    from app.domain.repositories.user_repository import UserRepository
    from app.domain.services.notification_service import NotificationService

    email = _unique_email("n3")
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "Senha123!", "role": "freelancer"},
    )
    login = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": "Senha123!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    async with SessionLocal() as session:
        user = await UserRepository(session).get_by_email(email)
        assert user is not None
        await NotificationService(session).emit(user_id=user.id, type="a", payload={})
        n = await NotificationService(session).emit(user_id=user.id, type="b", payload={})
        await NotificationService(session).mark_read(user_id=user.id, notif_id=n.id)
        await session.commit()

    resp = await client.get("/v1/me/notifications?unread_only=true", headers=headers)
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["type"] == "a"


@pytest.mark.asyncio
async def test_mark_read_single(client: AsyncClient) -> None:
    from app.core.database import SessionLocal
    from app.domain.repositories.user_repository import UserRepository
    from app.domain.services.notification_service import NotificationService

    email = _unique_email("n4")
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "Senha123!", "role": "freelancer"},
    )
    login = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": "Senha123!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    async with SessionLocal() as session:
        user = await UserRepository(session).get_by_email(email)
        assert user is not None
        n = await NotificationService(session).emit(user_id=user.id, type="x", payload={})
        await session.commit()
        nid = n.id

    resp = await client.post(f"/v1/notifications/{nid}/read", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["read_at"] is not None


@pytest.mark.asyncio
async def test_mark_read_not_owner(client: AsyncClient) -> None:
    """User B não pode marcar como lida notification do A."""
    from app.core.database import SessionLocal
    from app.domain.repositories.user_repository import UserRepository
    from app.domain.services.notification_service import NotificationService

    email_a = _unique_email("n5a")
    email_b = _unique_email("n5b")
    for email in (email_a, email_b):
        await client.post(
            "/v1/auth/register",
            json={"email": email, "password": "Senha123!", "role": "freelancer"},
        )

    async with SessionLocal() as session:
        user_a = await UserRepository(session).get_by_email(email_a)
        assert user_a is not None
        n = await NotificationService(session).emit(user_id=user_a.id, type="x", payload={})
        await session.commit()
        nid = n.id

    login_b = await client.post(
        "/v1/auth/login",
        json={"email": email_b, "password": "Senha123!"},
    )
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}
    resp = await client.post(f"/v1/notifications/{nid}/read", headers=headers_b)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_mark_all_read(client: AsyncClient) -> None:
    from app.core.database import SessionLocal
    from app.domain.repositories.user_repository import UserRepository
    from app.domain.services.notification_service import NotificationService

    email = _unique_email("n6")
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "Senha123!", "role": "freelancer"},
    )
    login = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": "Senha123!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    async with SessionLocal() as session:
        user = await UserRepository(session).get_by_email(email)
        assert user is not None
        for t in ("a", "b", "c"):
            await NotificationService(session).emit(user_id=user.id, type=t, payload={})
        await session.commit()

    resp = await client.post("/v1/me/notifications/read-all", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["updated"] == 3


@pytest.mark.asyncio
async def test_pagination_order_desc(client: AsyncClient) -> None:
    from app.core.database import SessionLocal
    from app.domain.repositories.user_repository import UserRepository
    from app.domain.services.notification_service import NotificationService

    email = _unique_email("n7")
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "Senha123!", "role": "freelancer"},
    )
    login = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": "Senha123!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    async with SessionLocal() as session:
        user = await UserRepository(session).get_by_email(email)
        assert user is not None
        for t in ("first", "second", "third"):
            await NotificationService(session).emit(user_id=user.id, type=t, payload={})
        await session.commit()

    resp = await client.get("/v1/me/notifications?page=1&page_size=2", headers=headers)
    body = resp.json()
    assert body["total"] == 3
    assert body["page_size"] == 2
    assert len(body["items"]) == 2
    # ordem desc por created_at: 'third' antes
    assert body["items"][0]["type"] == "third"


@pytest.mark.asyncio
async def test_created_at_strictly_increasing_in_same_transaction(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Emissões em sequência na mesma tx não podem empatar no created_at.

    O relógio do processo pode repetir o valor (no Windows avança em saltos de
    1-16 ms); congelamos ele para tornar o empate determinístico. O created_at
    precisa vir do banco (clock_timestamp), não do relógio do processo.
    """
    from datetime import UTC, datetime

    from app.core.database import SessionLocal
    from app.domain.repositories import notification_repository
    from app.domain.repositories.notification_repository import NotificationRepository
    from app.domain.repositories.user_repository import UserRepository

    frozen = datetime(2026, 1, 1, tzinfo=UTC)

    class _FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[no-untyped-def,override]
            return frozen

    monkeypatch.setattr(notification_repository, "datetime", _FrozenDatetime)

    email = _unique_email("n8")
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "Senha123!", "role": "freelancer"},
    )

    async with SessionLocal() as session:
        user = await UserRepository(session).get_by_email(email)
        assert user is not None
        repo = NotificationRepository(session)
        created = [await repo.create(user_id=user.id, type=f"t{i}", payload={}) for i in range(5)]
        await session.rollback()

    stamps = [n.created_at for n in created]
    assert all(a < b for a, b in pairwise(stamps)), stamps
