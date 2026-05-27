"""Alembic env — async + URL injetada de Settings."""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.core.config import get_settings
from app.domain.models import Base  # importa todos os models via __init__

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Injeta DATABASE_URL em runtime
config.set_main_option("sqlalchemy.url", get_settings().database_url)

target_metadata = Base.metadata

# Whitelist: só as tabelas da app entram em autogenerate.
# PostGIS, alembic_version e outras tabelas externas são ignoradas.
_APP_TABLES = frozenset(
    {
        "users",
        "audit_log",
        "freelancer_profiles",
        "establishment_profiles",
        "skill_categories",
        "freelancer_skills",
    }
)


def include_object(
    _obj: object,
    name: str | None,
    type_: str,
    _reflected: bool,
    _compare_to: object,
) -> bool:
    if type_ == "table":
        return name in _APP_TABLES
    return True


def include_name(name: str | None, type_: str, _parent_names: dict[str, str | None]) -> bool:
    if type_ == "schema":
        return name in (None, "public")
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        include_name=include_name,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        include_name=include_name,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    connectable = async_engine_from_config(
        section, prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
