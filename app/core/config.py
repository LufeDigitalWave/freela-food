"""Configurações globais via Pydantic Settings."""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    env: Literal["dev", "staging", "prod"] = "dev"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    database_url: str
    redis_url: str

    jwt_secret: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = Field(default=60, ge=1)

    bcrypt_rounds: int = Field(default=12, ge=4, le=15)

    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)
    sentry_dsn: str | None = None

    # Chave simétrica pra pgcrypto (pgp_sym_encrypt) — campos sensíveis no Postgres
    db_encryption_key: SecretStr

    # S3 / MinIO
    s3_endpoint_url: str
    s3_region: str = "us-east-1"
    s3_bucket: str
    s3_public_base_url: str
    s3_access_key: SecretStr
    s3_secret_key: SecretStr

    # LGPD: grace period entre soft-delete e purge definitivo
    delete_grace_period_days: int = Field(default=30, ge=1)

    # Fluxo B: validade default de um convite (limitada também pelo start_at)
    invitation_ttl_hours: int = Field(default=72, ge=1)

    # Matching engine — pesos do scoring (somam ~1.0)
    match_weight_proximity: float = Field(default=0.25, ge=0, le=1)
    match_weight_skill: float = Field(default=0.20, ge=0, le=1)
    match_weight_rating: float = Field(default=0.20, ge=0, le=1)
    match_weight_reliability: float = Field(default=0.15, ge=0, le=1)
    match_weight_experience: float = Field(default=0.10, ge=0, le=1)
    match_weight_repeat_hire: float = Field(default=0.10, ge=0, le=1)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    """Singleton de Settings — recarregar exige restart do processo."""
    return Settings()
