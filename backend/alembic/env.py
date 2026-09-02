from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, inspect, pool, text

from app.config import get_settings
from app.database import Base, import_models

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
configured_url = config.get_main_option("sqlalchemy.url")
if not configured_url or configured_url == "sqlite:///./organicai.db":
    configured_url = settings.database_url
config.set_main_option("sqlalchemy.url", configured_url)
import_models()
target_metadata = Base.metadata


def include_object(object_, name, type_, reflected, compare_to):
    return True


def ensure_postgresql_version_table_capacity(connection) -> None:
    if connection.dialect.name != "postgresql":
        return
    inspector = inspect(connection)
    if "alembic_version" not in inspector.get_table_names():
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(128) NOT NULL PRIMARY KEY)"))
        return
    version_column = next(column for column in inspector.get_columns("alembic_version") if column["name"] == "version_num")
    if getattr(version_column["type"], "length", None) and version_column["type"].length < 128:
        connection.execute(text("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)"))


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    dialect = url.split(":", 1)[0]
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=dialect == "sqlite",
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        with connection.begin():
            ensure_postgresql_version_table_capacity(connection)
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=connection.dialect.name == "sqlite",
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
