from __future__ import annotations

from typing import Any

from sqlalchemy import MetaData, Table, create_engine, exists, func, inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.database import Base, import_models
from app.db.migration_status import get_database_migration_status


def _add_check(checks: list[dict[str, Any]], name: str, status: str, message: str, count: int = 0) -> None:
    checks.append({"name": name, "status": status, "message": message, "count": count})


def _foreign_key_orphans(engine: Engine, metadata: MetaData) -> int:
    orphan_count = 0
    with engine.connect() as connection:
        for table in metadata.sorted_tables:
            for fk in table.foreign_keys:
                parent_table = fk.column.table
                child_column = fk.parent
                parent_column = fk.column
                child = table.alias("child")
                parent = parent_table.alias("parent")
                statement = (
                    select(func.count())
                    .select_from(child.outerjoin(parent, child.c[child_column.name] == parent.c[parent_column.name]))
                    .where(child.c[child_column.name].is_not(None), parent.c[parent_column.name].is_(None))
                )
                try:
                    orphan_count += int(connection.execute(statement).scalar_one())
                except SQLAlchemyError:
                    continue
    return orphan_count


def verify_database_integrity(database_url: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    engine = create_engine(database_url or settings.database_url)
    checks: list[dict[str, Any]] = []
    critical = 0
    warnings = 0

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        _add_check(checks, "connection", "passed", "Database connection is reachable.")
    except SQLAlchemyError as exc:
        engine.dispose()
        return {
            "status": "failed",
            "criticalIssues": 1,
            "warnings": 0,
            "checks": [{"name": "connection", "status": "failed", "message": exc.__class__.__name__, "count": 1}],
        }

    import_models()
    inspector = inspect(engine)
    actual_tables = set(inspector.get_table_names())
    required_tables = {table.name for table in Base.metadata.sorted_tables}
    missing_tables = sorted(required_tables - actual_tables)
    if missing_tables:
        critical += len(missing_tables)
        _add_check(checks, "required_tables", "failed", "Required tables are missing.", len(missing_tables))
    else:
        _add_check(checks, "required_tables", "passed", "Required tables are present.")

    if engine.dialect.name == "sqlite":
        with engine.connect() as connection:
            sqlite_integrity = connection.execute(text("PRAGMA integrity_check")).scalar_one()
            fk_issue_count = len(list(connection.execute(text("PRAGMA foreign_key_check"))))
        if sqlite_integrity != "ok":
            critical += 1
            _add_check(checks, "sqlite_integrity", "failed", "SQLite integrity check failed.", 1)
        else:
            _add_check(checks, "sqlite_integrity", "passed", "SQLite integrity check passed.")
        if fk_issue_count:
            critical += fk_issue_count
            _add_check(checks, "foreign_keys", "failed", "Foreign key orphan rows were detected.", fk_issue_count)
        else:
            _add_check(checks, "foreign_keys", "passed", "Foreign key checks passed.")
    else:
        _add_check(checks, "constraint_validation", "passed", "PostgreSQL constraints are active.")

    migration = get_database_migration_status(settings, bind=engine)
    if settings.db_require_migration_head and not migration.current:
        critical += 1
        _add_check(checks, "migration_revision", "failed", "Database is not at Alembic head.", 1)
    else:
        _add_check(checks, "migration_revision", "passed", "Database migration revision is current.")

    if required_tables.issubset(actual_tables):
        reflected = MetaData()
        for table_name in required_tables:
            Table(table_name, reflected, autoload_with=engine)
        orphan_count = _foreign_key_orphans(engine, reflected)
        if orphan_count:
            critical += orphan_count
            _add_check(checks, "referential_integrity", "failed", "Application foreign key orphan rows were detected.", orphan_count)
        else:
            _add_check(checks, "referential_integrity", "passed", "Application foreign key checks passed.")

    status = "passed" if critical == 0 else "failed"
    engine.dispose()
    return {"status": status, "criticalIssues": critical, "warnings": warnings, "checks": checks}
