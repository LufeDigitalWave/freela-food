"""CRUD de JobPosting + RBAC."""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.domain.models.skill_category import SkillCategory


def _unique_email() -> str:
    return f"jobs-test-{uuid.uuid4()}@example.com"


async def _register_and_login(client: AsyncClient, email: str, role: str) -> tuple[str, str]:
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
    return user_id, login.json()["access_token"]


async def _get_a_skill_category_id() -> uuid.UUID:
    """Pega o ID de uma skill_category seedada pela migration 003."""
    async with SessionLocal() as session:
        result = await session.execute(
            select(SkillCategory.id).where(SkillCategory.slug == "garcom")
        )
        return result.scalar_one()


async def _setup_establishment(client: AsyncClient, *, with_location: bool = True) -> str:
    """Registra estabelecimento, cria perfil, retorna token."""
    _uid, token = await _register_and_login(client, _unique_email(), "establishment")
    payload: dict[str, object] = {"business_name": "Bar dos Testes"}
    if with_location:
        payload.update({"latitude": -23.561, "longitude": -46.656})
    await client.post(
        "/v1/me/establishment-profile",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    return token


def _job_payload(skill_id: uuid.UUID, **overrides: object) -> dict[str, object]:
    start = datetime.now(UTC) + timedelta(days=3)
    end = start + timedelta(hours=6)
    payload: dict[str, object] = {
        "skill_category_id": str(skill_id),
        "title": "Garçom para evento de casamento",
        "description": "200 convidados, traje a rigor",
        "start_at": start.isoformat(),
        "end_at": end.isoformat(),
        "hourly_rate": "35.00",
    }
    payload.update(overrides)
    return payload


async def test_create_job_uses_profile_location_if_omitted(
    client: AsyncClient,
) -> None:
    token = await _setup_establishment(client, with_location=True)
    skill_id = await _get_a_skill_category_id()

    response = await client.post(
        "/v1/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json=_job_payload(skill_id),
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["latitude"] == -23.561
    assert data["longitude"] == -46.656
    assert data["status"] == "open"


async def test_create_job_explicit_location(client: AsyncClient) -> None:
    token = await _setup_establishment(client, with_location=False)
    skill_id = await _get_a_skill_category_id()

    response = await client.post(
        "/v1/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json=_job_payload(
            skill_id, latitude=-23.5, longitude=-46.6, address_line="Av Paulista 1000"
        ),
    )
    assert response.status_code == 201, response.text


async def test_create_job_without_location_anywhere_fails(client: AsyncClient) -> None:
    token = await _setup_establishment(client, with_location=False)
    skill_id = await _get_a_skill_category_id()

    response = await client.post(
        "/v1/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json=_job_payload(skill_id),
    )
    assert response.status_code == 422


async def test_freelancer_cannot_create_job(client: AsyncClient) -> None:
    _uid, token = await _register_and_login(client, _unique_email(), "freelancer")
    skill_id = await _get_a_skill_category_id()

    response = await client.post(
        "/v1/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json=_job_payload(skill_id, latitude=-23.5, longitude=-46.6),
    )
    assert response.status_code == 403


async def test_get_job(client: AsyncClient) -> None:
    token = await _setup_establishment(client)
    skill_id = await _get_a_skill_category_id()
    created = await client.post(
        "/v1/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json=_job_payload(skill_id),
    )
    job_id = created.json()["id"]

    response = await client.get(
        f"/v1/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == job_id


async def test_update_job_partial(client: AsyncClient) -> None:
    token = await _setup_establishment(client)
    skill_id = await _get_a_skill_category_id()
    created = await client.post(
        "/v1/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json=_job_payload(skill_id),
    )
    job_id = created.json()["id"]

    response = await client.patch(
        f"/v1/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Garçom para casamento (atualizado)"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Garçom para casamento (atualizado)"


async def test_only_owner_can_update_job(client: AsyncClient) -> None:
    owner_token = await _setup_establishment(client)
    skill_id = await _get_a_skill_category_id()
    created = await client.post(
        "/v1/jobs",
        headers={"Authorization": f"Bearer {owner_token}"},
        json=_job_payload(skill_id),
    )
    job_id = created.json()["id"]

    # Outro estabelecimento tenta editar
    other_token = await _setup_establishment(client)
    response = await client.patch(
        f"/v1/jobs/{job_id}",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"title": "Hack"},
    )
    assert response.status_code == 403


async def test_cancel_job(client: AsyncClient) -> None:
    token = await _setup_establishment(client)
    skill_id = await _get_a_skill_category_id()
    created = await client.post(
        "/v1/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json=_job_payload(skill_id),
    )
    job_id = created.json()["id"]

    response = await client.post(
        f"/v1/jobs/{job_id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


async def test_cancel_twice_returns_409(client: AsyncClient) -> None:
    token = await _setup_establishment(client)
    skill_id = await _get_a_skill_category_id()
    created = await client.post(
        "/v1/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json=_job_payload(skill_id),
    )
    job_id = created.json()["id"]

    await client.post(
        f"/v1/jobs/{job_id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    response = await client.post(
        f"/v1/jobs/{job_id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409


async def test_soft_delete_job(client: AsyncClient) -> None:
    token = await _setup_establishment(client)
    skill_id = await _get_a_skill_category_id()
    created = await client.post(
        "/v1/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json=_job_payload(skill_id),
    )
    job_id = created.json()["id"]

    delete_resp = await client.delete(
        f"/v1/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_resp.status_code == 204

    get_resp = await client.get(
        f"/v1/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 404


async def test_invalid_dates_rejected(client: AsyncClient) -> None:
    token = await _setup_establishment(client)
    skill_id = await _get_a_skill_category_id()
    start = datetime.now(UTC) + timedelta(days=2)
    end = start - timedelta(hours=1)  # end antes do start

    response = await client.post(
        "/v1/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "skill_category_id": str(skill_id),
            "title": "Garçom",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "hourly_rate": "30.00",
        },
    )
    assert response.status_code == 422


async def test_pay_required(client: AsyncClient) -> None:
    token = await _setup_establishment(client)
    skill_id = await _get_a_skill_category_id()
    start = datetime.now(UTC) + timedelta(days=2)

    response = await client.post(
        "/v1/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "skill_category_id": str(skill_id),
            "title": "Garçom sem pagamento",
            "start_at": start.isoformat(),
            "end_at": (start + timedelta(hours=4)).isoformat(),
        },
    )
    assert response.status_code == 422
