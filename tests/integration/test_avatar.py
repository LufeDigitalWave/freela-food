"""Avatar upload via /v1/me/avatar."""

import uuid

import httpx
from httpx import AsyncClient


def _unique_email() -> str:
    return f"avatar-test-{uuid.uuid4()}@example.com"


async def _setup_freelancer(client: AsyncClient) -> str:
    email = _unique_email()
    pwd = "supersecret123"
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": pwd, "role": "freelancer"},
    )
    login = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": pwd},
    )
    token: str = login.json()["access_token"]

    await client.post(
        "/v1/me/freelancer-profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"display_name": "Avatar Test"},
    )
    return token


# 1x1 PNG transparente (67 bytes) - upload pra MinIO valida content_type, nao bytes
_PNG_1PX = bytes.fromhex(
    "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4"
    "890000000A49444154789C6300010000000500010D0A2DB40000000049454E44"
    "AE426082"
)


async def test_upload_avatar_ok(client: AsyncClient) -> None:
    token = await _setup_freelancer(client)
    response = await client.post(
        "/v1/me/avatar",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("avatar.png", _PNG_1PX, "image/png")},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["avatar_url"].endswith(".png")
    assert "freela-food-uploads" in data["avatar_url"]

    # Avatar deve estar acessível publicamente
    async with httpx.AsyncClient() as ext:
        resp = await ext.get(data["avatar_url"])
        assert resp.status_code == 200
        assert resp.content == _PNG_1PX


async def test_upload_avatar_wrong_content_type_returns_415(
    client: AsyncClient,
) -> None:
    token = await _setup_freelancer(client)
    response = await client.post(
        "/v1/me/avatar",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("avatar.gif", _PNG_1PX, "image/gif")},
    )
    assert response.status_code == 415


async def test_upload_avatar_oversized_returns_413(client: AsyncClient) -> None:
    token = await _setup_freelancer(client)
    big_blob = b"\x00" * (6 * 1024 * 1024)  # 6MB > limite de 5MB
    response = await client.post(
        "/v1/me/avatar",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("big.jpg", big_blob, "image/jpeg")},
    )
    assert response.status_code == 413


async def test_upload_avatar_without_auth_returns_401(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/me/avatar",
        files={"file": ("avatar.png", _PNG_1PX, "image/png")},
    )
    assert response.status_code == 401
