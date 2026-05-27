"""Endpoints /v1/me: get_me, export (LGPD), delete (soft)."""

import uuid

from httpx import AsyncClient

VALID_CPF = "11144477735"


def _unique_email() -> str:
    return f"me-test-{uuid.uuid4()}@example.com"


async def _register_and_login(
    client: AsyncClient, email: str, role: str = "freelancer"
) -> tuple[str, str]:
    pwd = "supersecret123"
    reg = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": pwd, "role": role},
    )
    user_id = reg.json()["id"]
    login = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": pwd},
    )
    return user_id, login.json()["access_token"]


async def test_get_me_without_profile(client: AsyncClient) -> None:
    email = _unique_email()
    _uid, token = await _register_and_login(client, email)
    response = await client.get(
        "/v1/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert data["role"] == "freelancer"
    assert data["freelancer_profile"] is None
    assert data["establishment_profile"] is None


async def test_get_me_with_profile(client: AsyncClient) -> None:
    _uid, token = await _register_and_login(client, _unique_email())
    await client.post(
        "/v1/me/freelancer-profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"display_name": "Tested", "phone": "+5511988887777"},
    )

    response = await client.get(
        "/v1/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["freelancer_profile"]["display_name"] == "Tested"


async def test_export_includes_decrypted_cpf(client: AsyncClient) -> None:
    _uid, token = await _register_and_login(client, _unique_email())
    await client.post(
        "/v1/me/freelancer-profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"display_name": "Exporter", "cpf": VALID_CPF},
    )

    response = await client.get(
        "/v1/me/export", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["cpf"] == VALID_CPF  # decriptado
    assert data["freelancer_profile"]["display_name"] == "Exporter"
    # Audit log deve conter a entrada de create + export
    actions = {entry["action"] for entry in data["audit_log"]}
    assert "create" in actions
    assert "export" in actions


async def test_delete_me_soft_deletes_and_returns_purge_date(
    client: AsyncClient,
) -> None:
    _uid, token = await _register_and_login(client, _unique_email())

    response = await client.delete(
        "/v1/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "scheduled_for_deletion"
    assert "purge_at" in data


async def test_login_fails_after_delete_me(client: AsyncClient) -> None:
    email = _unique_email()
    pwd = "supersecret123"
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": pwd, "role": "freelancer"},
    )
    login = await client.post(
        "/v1/auth/login", json={"email": email, "password": pwd}
    )
    token = login.json()["access_token"]

    delete = await client.delete(
        "/v1/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete.status_code == 200

    # UserRepository.get_by_email filtra deleted_at IS NULL → login agora falha
    after = await client.post(
        "/v1/auth/login", json={"email": email, "password": pwd}
    )
    assert after.status_code == 401
