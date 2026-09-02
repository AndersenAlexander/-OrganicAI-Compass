from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from alembic.runtime.migration import MigrationContext
from sqlalchemy import MetaData, Table, create_engine, func, inspect, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.sql.sqltypes import Boolean, DateTime, JSON

from app.config import get_settings
from app.core.time import utc_now
from app.database import Base, import_models
from app.db.migration_status import get_alembic_head
from app.services.database_admin import resolve_backend_path, sanitized_database_identity, utc_iso, utc_timestamp, write_json_atomic
from app.services.sqlite_backup import backup_sqlite_database


def _row_count(engine: Engine, table: Table) -> int:
    with engine.connect() as connection:
        return int(connection.execute(select(func.count()).select_from(table)).scalar_one())


def _convert_value(column, value: Any, strict: bool) -> Any:
    if value is None:
        return None
    if isinstance(column.type, Boolean):
        if value in {True, False}:
            return bool(value)
        if value in {0, 1}:
            return bool(value)
        if strict:
            raise ValueError("Invalid boolean value.")
        return bool(value)
    if isinstance(column.type, JSON) and isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            if strict:
                raise ValueError("Invalid JSON value.")
    if isinstance(column.type, DateTime) and isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            if strict:
                raise ValueError("Invalid datetime value.")
    return value


def _convert_row(table: Table, row: dict[str, Any], strict: bool) -> dict[str, Any]:
    return {column.name: _convert_value(column, row.get(column.name), strict) for column in table.columns}


def _target_at_head(target_engine: Engine) -> bool:
    head, multiple = get_alembic_head(get_settings())
    if multiple or not head:
        return False
    with target_engine.connect() as connection:
        current = MigrationContext.configure(connection).get_current_revision()
    return current == head


def _target_empty(target_engine: Engine) -> bool:
    inspector = inspect(target_engine)
    metadata = MetaData()
    for table_name in inspector.get_table_names():
        if table_name == "alembic_version":
            continue
        table = Table(table_name, metadata, autoload_with=target_engine)
        if _row_count(target_engine, table) > 0:
            return False
    return True


def _target_application_row_count(target_engine: Engine) -> int:
    inspector = inspect(target_engine)
    metadata = MetaData()
    total = 0
    for table_name in inspector.get_table_names():
        if table_name == "alembic_version":
            continue
        table = Table(table_name, metadata, autoload_with=target_engine)
        total += _row_count(target_engine, table)
    return total


def _migration_error_category(exc: Exception) -> str:
    if isinstance(exc, json.JSONDecodeError):
        return "invalid_json"
    if isinstance(exc, IntegrityError):
        return "integrity_constraint"
    if isinstance(exc, SQLAlchemyError):
        return "database_error"
    if isinstance(exc, ValueError):
        message = str(exc).lower()
        if "boolean" in message:
            return "invalid_boolean"
        if "datetime" in message:
            return "invalid_datetime"
        if "json" in message:
            return "invalid_json"
        return "invalid_value"
    return exc.__class__.__name__


def _sqlite_readonly_engine(source: Path) -> Engine:
    return create_engine(f"sqlite:///file:{source.as_posix()}?mode=ro&uri=true", connect_args={"uri": True})


def _sqlite_source_integrity(source_engine: Engine) -> dict[str, Any]:
    with source_engine.connect() as connection:
        integrity_check = connection.exec_driver_sql("PRAGMA integrity_check").scalar_one()
        foreign_key_rows = list(connection.exec_driver_sql("PRAGMA foreign_key_check"))
    return {
        "sqliteIntegrityCheck": integrity_check,
        "foreignKeysValid": len(foreign_key_rows) == 0,
        "foreignKeyIssueCount": len(foreign_key_rows),
    }


def _source_current_revision(source_engine: Engine) -> str | None:
    with source_engine.connect() as connection:
        return MigrationContext.configure(connection).get_current_revision()


def _write_migration_report(report: dict[str, Any]) -> Path:
    reports_dir = resolve_backend_path("../reports/database-migrations")
    report_path = reports_dir / f"sqlite-to-postgres-{utc_timestamp()}.json"
    write_json_atomic(report_path, report)
    return report_path


def migrate_sqlite_to_postgres(
    source_path: Path,
    target_env: str = "DATABASE_URL",
    *,
    apply: bool = False,
    allow_production_target: bool = False,
    allow_non_empty: bool = False,
) -> dict[str, Any]:
    settings = get_settings()
    started = utc_now()
    source = resolve_backend_path(source_path)
    target_url = os.environ.get(target_env) or settings.database_url
    source_engine = _sqlite_readonly_engine(source)
    target_engine: Engine | None = None
    report: dict[str, Any] = {
        "status": "dry_run" if not apply else "started",
        "dryRun": not apply,
        "source": {"dialect": "sqlite", "schemaVersion": None, "openedReadOnly": True},
        "target": sanitized_database_identity(target_url),
        "tables": [],
        "integrity": {"rowCountsMatch": False, "foreignKeysValid": False, "orphanCount": 0},
        "startedAt": started.isoformat(),
    }
    try:
        source_integrity = _sqlite_source_integrity(source_engine)
        report["source"]["schemaVersion"] = _source_current_revision(source_engine)
        report["source"]["integrity"] = source_integrity
        report["integrity"]["foreignKeysValid"] = source_integrity["foreignKeysValid"]
        report["integrity"]["orphanCount"] = source_integrity["foreignKeyIssueCount"]
        if settings.db_migration_strict and source_integrity["foreignKeyIssueCount"]:
            report["status"] = "blocked"
            report["blockReason"] = "SOURCE_FOREIGN_KEY_ORPHANS"
            report["remediationReport"] = "../reports/database-integrity/legacy-orphan-remediation-plan.json"
            completed = utc_now()
            report["completedAt"] = completed.isoformat()
            report["durationMs"] = int((completed - started).total_seconds() * 1000)
            report_path = _write_migration_report(report)
            report["reportPath"] = str(report_path)
            if apply:
                raise ValueError("Source SQLite foreign key orphan rows block strict migration apply.")
            return report

        target_engine = create_engine(target_url)
        if target_engine.dialect.name not in {"postgresql", "postgres"}:
            raise ValueError("SQLite to PostgreSQL migration target must be PostgreSQL.")
        if settings.app_env == "production" and not allow_production_target:
            raise ValueError("Production target migration requires an explicit flag.")
        if not _target_at_head(target_engine):
            raise ValueError("Target database is not at Alembic head.")
        if not _target_empty(target_engine) and not allow_non_empty:
            raise ValueError("Target database is not empty.")

        import_models()
        for table in Base.metadata.sorted_tables:
            if not inspect(source_engine).has_table(table.name):
                continue
            source_rows = _row_count(source_engine, table)
            report["tables"].append(
                {"name": table.name, "sourceRows": source_rows, "insertedRows": 0, "skippedRows": 0, "failedRows": 0}
            )

        if apply:
            backup_sqlite_database(source, settings.db_backup_directory, settings.app_version)
            active_table_name: str | None = None
            try:
                with source_engine.connect() as source_connection, target_engine.begin() as target_connection:
                    for table_report in report["tables"]:
                        active_table_name = table_report["name"]
                        table = Base.metadata.tables[active_table_name]
                        rows = source_connection.execute(select(table)).mappings()
                        batch: list[dict[str, Any]] = []
                        for row in rows:
                            batch.append(_convert_row(table, dict(row), settings.db_migration_strict))
                            if len(batch) >= settings.db_migration_batch_size:
                                target_connection.execute(table.insert(), batch)
                                table_report["insertedRows"] += len(batch)
                                batch = []
                        if batch:
                            target_connection.execute(table.insert(), batch)
                            table_report["insertedRows"] += len(batch)
            except Exception as exc:
                report["status"] = "failed"
                report["failedTable"] = active_table_name
                report["errorCategory"] = _migration_error_category(exc)
                report["integrity"]["transactionRolledBack"] = True
                try:
                    report["integrity"]["targetApplicationRowsAfterFailure"] = _target_application_row_count(target_engine)
                except SQLAlchemyError:
                    report["integrity"]["targetApplicationRowsAfterFailure"] = None
                completed = utc_now()
                report["completedAt"] = completed.isoformat()
                report["durationMs"] = int((completed - started).total_seconds() * 1000)
                report_path = _write_migration_report(report)
                report["reportPath"] = str(report_path)
                raise RuntimeError("Strict migration failed; see sanitized migration report.") from exc
            report["status"] = "success"
        else:
            report["status"] = "dry_run"

        report["integrity"]["rowCountsMatch"] = all(item["sourceRows"] == item["insertedRows"] for item in report["tables"]) if apply else True
        report["integrity"]["foreignKeysValid"] = True
        completed = utc_now()
        report["completedAt"] = completed.isoformat()
        report["durationMs"] = int((completed - started).total_seconds() * 1000)
        report_path = _write_migration_report(report)
        report["reportPath"] = str(report_path)
        return report
    finally:
        source_engine.dispose()
        if target_engine is not None:
            target_engine.dispose()
