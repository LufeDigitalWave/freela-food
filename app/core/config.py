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
