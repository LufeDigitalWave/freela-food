"""Testes do módulo de security (sem DB, sem HTTP)."""

import uuid

import pytest
from fastapi import HTTPException

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify_roundtrip() -> None:
    pwd = "supersecret-123"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_roundtrip_preserves_subject() -> None:
    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert "exp" in payload
    assert "iat" in payload
    assert "jti" in payload


def test_jwt_invalid_token_raises_401() -> None:
    with pytest.raises(HTTPException) as exc_info:
        decode_token("not.a.valid.token")
    assert exc_info.value.status_code == 401


def test_jwt_tampered_signature_raises_401() -> None:
    token = create_access_token(uuid.uuid4())
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(HTTPException) as exc_info:
        decode_token(tampered)
    assert exc_info.value.status_code == 401
