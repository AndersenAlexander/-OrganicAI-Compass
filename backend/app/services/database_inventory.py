from __future__ import annotations

from typing import Any

from sqlalchemy import MetaData, Table, create_engine, func, inspect, select, text
from sqlalchemy.engine import Engine

from app.config import get_settings
from app.db.migration_status import get_database_migration_status


def _count_rows(engine: Engine, table_name: str) -> int:
    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)
    with engine.connect() as connection:
        return int(connection.execute(select(func.count()).select_from(table)).scalar_one())


def inventory_database(database_url: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    engine = create_engine(database_url or settings.database_url)
    inspector = inspect(engine)
    tables = []
    for table_name in sorted(inspector.get_table_names()):
        if table_name.startswith("sqlite_"):
            continue
        columns = inspector.get_columns(table_name)
        primary_key = inspector.get_pk_constraint(table_name) or {}
        foreign_keys = inspector.get_foreign_keys(table_name)
        indexes = inspector.get_indexes(table_name)
        unique_constraints = inspector.get_unique_constraints(table_name)
        tables.append(
            {
                "name": table_name,
                "rowCount": _count_rows(engine, table_name),
                "columns": [
                    {
                        "name": column["name"],
                        "type": str(column["type"]),
                        "nullable": bool(column.get("nullable", True)),
                        "primaryKey": column["name"] in set(primary_key.get("constrained_columns") or []),
                    }
                    for column in columns
                ],
                "primaryKeyColumns": primary_key.get("constrained_columns") or [],
                "foreignKeyCount": len(foreign_keys),
                "indexCount": len(indexes),
                "uniqueConstraintCount": len(unique_constraints),
                "uniqueIndexCount": sum(1 for item in indexes if item.get("unique")),
            }
        )

    integrity: dict[str, Any] = {"foreignKeysValid": True, "duplicatePrimaryKeys": 0}
    if engine.dialect.name == "sqlite":
        with engine.connect() as connection:
            integrity["sqliteIntegrityCheck"] = connection.execute(text("PRAGMA integrity_check")).scalar_one()
            fk_rows = list(connection.execute(text("PRAGMA foreign_key_check")))
            integrity["foreignKeysValid"] = len(fk_rows) == 0
            integrity["foreignKeyIssueCount"] = len(fk_rows)

    schema_version = None
    try:
        schema_version = get_database_migration_status(settings, bind=engine).current_revision
    except Exception:
        schema_version = None

    engine.dispose()
    return {
        "dialect": engine.dialect.name,
        "schemaVersion": schema_version,
        "tables": tables,
        "tableCount": len(tables),
        "integrity": integrity,
    }
