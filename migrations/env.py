import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config 

from database.models import Base 
from config import config as bot_config 

from alembic import context

alembic_config = context.config

if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = bot_config.DB_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        render_as_batch=True 
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    section = alembic_config.get_section(alembic_config.config_ini_section, {})
    section["sqlalchemy.url"] = bot_config.DB_URL

    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())