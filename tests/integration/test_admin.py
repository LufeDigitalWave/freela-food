"""Testes do dashboard admin (Sprint 6)."""

import uuid

import pytest
from httpx import AsyncClient

from app.core.database import SessionLocal
from tests.factories import (
    auth_header_for,
    make_admin,
    make_freelancer,
)


async def _create_admin(client: AsyncClient) -> tuple[str, dict[str, str]]:
    """Registra admin direto no DB e retorna (email, headers)."""
    suffix = uuid.uuid4().hex[:8]
    email = f"admin-{suffix}@test.com"
    async with SessionLocal() as session:
        await make_admin(session, email=email)
        await session.commit()
    headers = await auth_header_for(client, email)
    return email, headers


async def _create_non_admin(client: AsyncClient) -> tuple[str, dict[str, str]]:
    suffix = uuid.uuid4().hex[:8]
    email = f"user-{suffix}@test.com"
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "Senha123!", "role": "freelancer"},
    )
    login = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": "Senha123!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    return email, headers


# ── Access control ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_non_admin_gets_403(client: AsyncClient) -> None:
    _, headers = await _create_non_admin(client)
    resp = await client.get("/v1/admin/stats", headers=headers)
    assert resp.status_code == 403
    assert "administradores" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_unauthenticated_gets_401(client: AsyncClient) -> None:
    resp = await client.get("/v1/admin/stats")
    assert resp.status_code == 401


# ── Stats ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stats_returns_counts(client: AsyncClient) -> None:
    _, headers = await _create_admin(client)
    resp = await client.get("/v1/admin/stats", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "users" in body
    assert "jobs" in body
    assert "contracts" in body
    assert "reviews_total" in body
    assert "notifications_total" in body
    # Verifica que os sub-campos existem
    assert "freelancers" in body["users"]
    assert "total" in body["users"]


# ── User listing ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient) -> None:
    _, headers = await _create_admin(client)
    resp = await client.get("/v1/admin/users", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert body["total"] > 0


@pytest.mark.asyncio
async def test_list_users_filter_by_role(client: AsyncClient) -> None:
    _, headers = await _create_admin(client)
    resp = await client.get("/v1/admin/users?role=admin", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert all(u["role"] == "admin" for u in body["items"])


@pytest.mark.asyncio
async def test_list_users_email_search(client: AsyncClient) -> None:
    admin_email, headers = await _create_admin(client)
    # Search por parte do email do admin
    search_term = admin_email.split("@")[0]
    resp = await client.get(
        f"/v1/admin/users?email_search={search_term}", headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert any(search_term in u["email"] for u in body["items"])


# ── User detail ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_user_detail(client: AsyncClient) -> None:
    _, headers = await _create_admin(client)
    # Criar um freelancer pra consultar
    suffix = uuid.uuid4().hex[:8]
    async with SessionLocal() as session:
        fl, _ = await make_freelancer(session, email=f"fl-{suffix}@test.com")
        await session.commit()
        fl_id = fl.id

    resp = await client.get(f"/v1/admin/users/{fl_id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(fl_id)
    assert body["role"] == "freelancer"
    assert "contracts_count" in body
    assert "reviews_given" in body
    assert "reviews_received" in body


@pytest.mark.asyncio
async def test_user_detail_not_found(client: AsyncClient) -> None:
    _, headers = await _create_admin(client)
    fake_id = uuid.uuid4()
    resp = await client.get(f"/v1/admin/users/{fake_id}", headers=headers)
    assert resp.status_code == 404


# ── Deactivate / Reactivate ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_deactivate_user(client: AsyncClient) -> None:
    _, headers = await _create_admin(client)
    suffix = uuid.uuid4().hex[:8]
    async with SessionLocal() as session:
        fl, _ = await make_freelancer(session, email=f"fl-{suffix}@test.com")
        await session.commit()
        fl_id = fl.id

    resp = await client.post(f"/v1/admin/users/{fl_id}/deactivate", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["deleted_at"] is not None


@pytest.mark.asyncio
async def test_reactivate_user(client: AsyncClient) -> None:
    _, headers = await _create_admin(client)
    suffix = uuid.uuid4().hex[:8]
    async with SessionLocal() as session:
        fl, _ = await make_freelancer(session, email=f"fl-{suffix}@test.com")
        await session.commit()
        fl_id = fl.id

    # Deactivate first
    await client.post(f"/v1/admin/users/{fl_id}/deactivate", headers=headers)
    # Then reactivate
    resp = await client.post(f"/v1/admin/users/{fl_id}/reactivate", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["deleted_at"] is None


# ── Audit log ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_audit_log_list(client: AsyncClient) -> None:
    _, headers = await _create_admin(client)
    # Gerar uma entrada de audit (deactivate cria audit log)
    suffix = uuid.uuid4().hex[:8]
    async with SessionLocal() as session:
        fl, _ = await make_freelancer(session, email=f"fl-{suffix}@test.com")
        await session.commit()
        fl_id = fl.id
    await client.post(f"/v1/admin/users/{fl_id}/deactivate", headers=headers)

    resp = await client.get("/v1/admin/audit-log", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert body["total"] >= 1


@pytest.mark.asyncio
async def test_audit_log_filter_by_action(client: AsyncClient) -> None:
    _, headers = await _create_admin(client)
    suffix = uuid.uuid4().hex[:8]
    async with SessionLocal() as session:
        fl, _ = await make_freelancer(session, email=f"fl-{suffix}@test.com")
        await session.commit()
        fl_id = fl.id
    await client.post(f"/v1/admin/users/{fl_id}/deactivate", headers=headers)

    resp = await client.get(
        "/v1/admin/audit-log?action=deactivate", headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert all(a["action"] == "deactivate" for a in body["items"])
