"""Endpoints de auth: /register, /login, /me. Requer Postgres + migrations aplicadas."""

import uuid

from httpx import AsyncClient


def _unique_email() -> str:
    return f"test-{uuid.uuid4()}@example.com"


async def test_register_creates_user(client: AsyncClient) -> None:
    email = _unique_email()
    response = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "supersecret123", "role": "freelancer"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == email
    assert data["role"] == "freelancer"
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data


async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:
    payload = {
        "email": _unique_email(),
        "password": "supersecret123",
        "role": "freelancer",
    }
    first = await client.post("/v1/auth/register", json=payload)
    assert first.status_code == 201

    duplicate = await client.post("/v1/auth/register", json=payload)
    assert duplicate.status_code == 409


async def test_login_returns_token(client: AsyncClient) -> None:
    email = _unique_email()
    pwd = "supersecret123"

    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": pwd, "role": "freelancer"},
    )
    response = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": pwd},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


async def test_login_wrong_password_returns_401(client: AsyncClient) -> None:
    email = _unique_email()
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "supersecret123", "role": "freelancer"},
    )
    response = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": "wrong-password"},
    )
    assert response.status_code == 401


async def test_me_with_valid_token(client: AsyncClient) -> None:
    email = _unique_email()
    pwd = "supersecret123"

    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": pwd, "role": "establishment"},
    )
    login = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": pwd},
    )
    token = login.json()["access_token"]

    response = await client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == email
    assert data["role"] == "establishment"


async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/v1/auth/me")
    assert response.status_code == 401


async def test_me_with_invalid_token_returns_401(client: AsyncClient) -> None:
    response = await client.get(
        "/v1/auth/me",
        headers={"Authorization": "Bearer not.a.valid.token"},
    )
    assert response.status_code == 401
