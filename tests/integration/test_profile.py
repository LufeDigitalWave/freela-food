"""Endpoints de profile (freelancer + estabelecimento) + audit log."""

import uuid

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal
from app.domain.models.audit_log import AuditLog

# Documentos válidos canônicos pra teste
VALID_CPF = "11144477735"
VALID_CNPJ = "11222333000181"


def _unique_email() -> str:
    return f"profile-test-{uuid.uuid4()}@example.com"


async def _register_and_login(
    client: AsyncClient, email: str, role: str
) -> tuple[str, str]:
    """Cria user e retorna (user_id, access_token)."""
    pwd = "supersecret123"
    reg = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": pwd, "role": role},
    )
    assert reg.status_code == 201, reg.text
    user_id = reg.json()["id"]

    login = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": pwd},
    )
    token = login.json()["access_token"]
    return user_id, token


async def test_create_freelancer_profile(client: AsyncClient) -> None:
    _uid, token = await _register_and_login(client, _unique_email(), "freelancer")

    response = await client.post(
        "/v1/me/freelancer-profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "display_name": "Bia Garçonete",
            "bio": "8 anos em buffets",
            "phone": "+5511999998888",
            "cpf": VALID_CPF,
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["display_name"] == "Bia Garçonete"
    assert data["has_cpf"] is True
    assert "cpf" not in data  # nunca expor


async def test_create_freelancer_profile_invalid_cpf_returns_422(
    client: AsyncClient,
) -> None:
    _uid, token = await _register_and_login(client, _unique_email(), "freelancer")
    response = await client.post(
        "/v1/me/freelancer-profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"display_name": "Teste", "cpf": "12345678900"},
    )
    assert response.status_code == 422


async def test_establishment_cannot_create_freelancer_profile(
    client: AsyncClient,
) -> None:
    _uid, token = await _register_and_login(client, _unique_email(), "establishment")
    response = await client.post(
        "/v1/me/freelancer-profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"display_name": "Invalido"},
    )
    assert response.status_code == 403


async def test_create_freelancer_profile_duplicate_returns_409(
    client: AsyncClient,
) -> None:
    _uid, token = await _register_and_login(client, _unique_email(), "freelancer")
    payload = {"display_name": "Primeiro"}

    first = await client.post(
        "/v1/me/freelancer-profile",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert first.status_code == 201

    second = await client.post(
        "/v1/me/freelancer-profile",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert second.status_code == 409


async def test_update_freelancer_profile_partial(client: AsyncClient) -> None:
    _uid, token = await _register_and_login(client, _unique_email(), "freelancer")
    await client.post(
        "/v1/me/freelancer-profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"display_name": "Antigo", "bio": "Bio antiga"},
    )
    response = await client.patch(
        "/v1/me/freelancer-profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"display_name": "Novo"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Novo"
    assert data["bio"] == "Bio antiga"  # não foi tocado


async def test_create_establishment_profile(client: AsyncClient) -> None:
    _uid, token = await _register_and_login(client, _unique_email(), "establishment")
    response = await client.post(
        "/v1/me/establishment-profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "business_name": "Bar do Zé",
            "address_line": "Rua A, 123",
            "neighborhood": "Centro",
            "city": "São Paulo",
            "state": "SP",
            "cep": "01310100",
            "phone": "+551133334444",
            "cnpj": VALID_CNPJ,
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["business_name"] == "Bar do Zé"
    assert data["state"] == "SP"
    assert data["has_cnpj"] is True


async def test_create_establishment_invalid_cnpj_returns_422(
    client: AsyncClient,
) -> None:
    _uid, token = await _register_and_login(client, _unique_email(), "establishment")
    response = await client.post(
        "/v1/me/establishment-profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"business_name": "Bar X", "cnpj": "00000000000000"},
    )
    assert response.status_code == 422


async def test_audit_log_records_profile_creation(client: AsyncClient) -> None:
    uid, token = await _register_and_login(client, _unique_email(), "freelancer")
    await client.post(
        "/v1/me/freelancer-profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"display_name": "Audited"},
    )

    async with SessionLocal() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.actor_id == uuid.UUID(uid),
                AuditLog.action == "create",
                AuditLog.entity == "freelancer_profile",
            )
        )
        rows: AsyncSession = result.scalars().all()  # type: ignore[assignment]
        assert len(rows) == 1  # type: ignore[arg-type]
        log = rows[0]  # type: ignore[index]
        assert log.entity_id == uuid.UUID(uid)
        assert log.diff.get("display_name") == "Audited"
