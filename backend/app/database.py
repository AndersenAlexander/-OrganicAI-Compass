from __future__ import annotations

from sqlalchemy import text

from app.config import get_settings
from app.db.base import Base
from app.db.engine import create_database_engine, dispose_database_engine, engine, get_database_dialect
from app.db.health import DatabaseConnectionStatus, check_database_connection
from app.db.migration_status import DatabaseMigrationStatus, get_database_migration_status
from app.db.session import SessionLocal, create_session_factory, get_db


def import_models() -> None:
    from app import models  # noqa: F401


def init_db() -> None:
    settings = get_settings()
    import_models()
    if not settings.db_auto_create_schema:
        return
    if settings.app_env == "production":
        raise RuntimeError("DB_AUTO_CREATE_SCHEMA is not allowed in production.")
    Base.metadata.create_all(bind=engine)
    if get_database_dialect() == "sqlite":
        apply_legacy_sqlite_compatibility()


def apply_legacy_sqlite_compatibility() -> None:
    with engine.begin() as connection:
        columns = {row[1] for row in connection.execute(text("PRAGMA table_info(users)"))}
        if columns and "is_demo" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN is_demo BOOLEAN NOT NULL DEFAULT 0"))
        if columns and "demo_dataset_version" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN demo_dataset_version INTEGER"))
        rag_columns = {row[1] for row in connection.execute(text("PRAGMA table_info(rag_runs)"))}
        if rag_columns and "run_origin" not in rag_columns:
            connection.execute(text("ALTER TABLE rag_runs ADD COLUMN run_origin VARCHAR(20) NOT NULL DEFAULT 'user'"))
        diagnostic_columns = {row[1] for row in connection.execute(text("PRAGMA table_info(diagnostics)"))}
        if diagnostic_columns and "status" not in diagnostic_columns:
            connection.execute(text("ALTER TABLE diagnostics ADD COLUMN status VARCHAR(30) NOT NULL DEFAULT 'in_progress'"))
        if diagnostic_columns and "current_step" not in diagnostic_columns:
            connection.execute(text("ALTER TABLE diagnostics ADD COLUMN current_step INTEGER NOT NULL DEFAULT 0"))
        if diagnostic_columns and "diagnostic_version" not in diagnostic_columns:
            connection.execute(text("ALTER TABLE diagnostics ADD COLUMN diagnostic_version VARCHAR(50) NOT NULL DEFAULT 'human-diagnostic-v2'"))
        if diagnostic_columns and "updated_at" not in diagnostic_columns:
            connection.execute(text("ALTER TABLE diagnostics ADD COLUMN updated_at DATETIME"))
            connection.execute(text("UPDATE diagnostics SET updated_at = created_at WHERE updated_at IS NULL"))
        if diagnostic_columns and "completed_at" not in diagnostic_columns:
            connection.execute(text("ALTER TABLE diagnostics ADD COLUMN completed_at DATETIME"))


__all__ = [
    "Base",
    "DatabaseConnectionStatus",
    "DatabaseMigrationStatus",
    "SessionLocal",
    "apply_legacy_sqlite_compatibility",
    "check_database_connection",
    "create_database_engine",
    "create_session_factory",
    "dispose_database_engine",
    "engine",
    "get_database_dialect",
    "get_database_migration_status",
    "get_db",
    "import_models",
    "init_db",
]
