from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.pool import StaticPool

from app.config import Settings, get_settings


def create_database_engine(settings: Settings) -> Engine:
    try:
        url = make_url(settings.database_url)
    except ArgumentError as exc:
        raise RuntimeError("DATABASE_URL is invalid.") from exc

    dialect = url.get_backend_name()
    kwargs: dict[str, object] = {"echo": settings.db_echo, "pool_pre_ping": settings.db_pool_pre_ping}
    connect_args: dict[str, object] = {}
    sqlite_memory_database = False

    if dialect == "sqlite":
        sqlite_memory_database = url.database in {None, "", ":memory:"}
        connect_args["check_same_thread"] = False
        connect_args["timeout"] = max(float(settings.db_connect_timeout_seconds), 1.0)
        if sqlite_memory_database:
            kwargs["poolclass"] = StaticPool
    elif dialect in {"postgresql", "postgres"}:
        kwargs.update(
            {
                "pool_size": settings.db_pool_size,
                "max_overflow": settings.db_max_overflow,
                "pool_timeout": settings.db_pool_timeout_seconds,
                "pool_recycle": settings.db_pool_recycle_seconds,
                "pool_reset_on_return": "rollback",
            }
        )
        connect_args["connect_timeout"] = settings.db_connect_timeout_seconds
        connect_args["application_name"] = settings.db_application_name
        options = []
        if settings.db_statement_timeout_ms > 0:
            options.append(f"-c statement_timeout={settings.db_statement_timeout_ms}")
        if settings.db_lock_timeout_ms > 0:
            options.append(f"-c lock_timeout={settings.db_lock_timeout_ms}")
        if settings.db_idle_in_transaction_session_timeout_ms > 0:
            options.append(f"-c idle_in_transaction_session_timeout={settings.db_idle_in_transaction_session_timeout_ms}")
        if options:
            connect_args["options"] = " ".join(options)

    if connect_args:
        kwargs["connect_args"] = connect_args

    db_engine = create_engine(settings.database_url, **kwargs)

    if dialect == "sqlite":
        @event.listens_for(db_engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute(f"PRAGMA busy_timeout={max(settings.db_connect_timeout_seconds * 1000, 1000)}")
            if not sqlite_memory_database:
                cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return db_engine


settings = get_settings()
engine = create_database_engine(settings)


def get_database_dialect() -> str:
    return engine.dialect.name


def dispose_database_engine() -> None:
    engine.dispose()
