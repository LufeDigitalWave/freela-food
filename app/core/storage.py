"""Cliente S3-compatible (MinIO/AWS S3) com upload e delete async.

boto3 é síncrono — embrulhamos em asyncio.to_thread pra não bloquear o event loop.
"""

import asyncio
from functools import lru_cache
from typing import TYPE_CHECKING, Final

import boto3
from botocore.client import Config

from app.core.config import get_settings

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client

ALLOWED_AVATAR_TYPES: Final[frozenset[str]] = frozenset(
    {"image/jpeg", "image/png", "image/webp"}
)
MAX_AVATAR_BYTES: Final[int] = 5 * 1024 * 1024  # 5 MB

_EXT_BY_TYPE: Final[dict[str, str]] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


@lru_cache
def _client() -> "S3Client":
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key.get_secret_value(),
        aws_secret_access_key=settings.s3_secret_key.get_secret_value(),
        region_name=settings.s3_region,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def _avatar_key(user_id: str, ext: str) -> str:
    return f"avatars/{user_id}.{ext}"


async def upload_avatar(user_id: str, content_type: str, body: bytes) -> str:
    """Upload um avatar e retorna a URL pública."""
    if content_type not in ALLOWED_AVATAR_TYPES:
        raise ValueError(f"Tipo não permitido: {content_type}")
    if len(body) > MAX_AVATAR_BYTES:
        raise ValueError(f"Avatar excede {MAX_AVATAR_BYTES} bytes")

    ext = _EXT_BY_TYPE[content_type]
    key = _avatar_key(user_id, ext)
    settings = get_settings()

    def _put() -> None:
        _client().put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
        )

    await asyncio.to_thread(_put)

    # Limpa avatares anteriores com extensão diferente (idempotência: 1 avatar por user)
    other_keys = [_avatar_key(user_id, e) for e in _EXT_BY_TYPE.values() if e != ext]
    await asyncio.to_thread(_delete_keys, settings.s3_bucket, other_keys)

    return f"{settings.s3_public_base_url}/{key}"


async def delete_avatar(user_id: str) -> None:
    """Remove qualquer avatar do usuário (todas as extensões possíveis)."""
    settings = get_settings()
    keys = [_avatar_key(user_id, ext) for ext in _EXT_BY_TYPE.values()]
    await asyncio.to_thread(_delete_keys, settings.s3_bucket, keys)


def _delete_keys(bucket: str, keys: list[str]) -> None:
    if not keys:
        return
    _client().delete_objects(
        Bucket=bucket,
        Delete={"Objects": [{"Key": k} for k in keys], "Quiet": True},
    )
