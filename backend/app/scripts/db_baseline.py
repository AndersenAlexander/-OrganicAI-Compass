from __future__ import annotations

import argparse
import json
from pathlib import Path

from alembic import command
from sqlalchemy import create_engine, inspect

from app.config import get_settings
from app.database import Base, import_models
from app.db.migration_status import alembic_config
from app.services.sqlite_backup import backup_sqlite_database


def compare_legacy_schema(database_path: Path) -> dict:
    import_models()
    engine = create_engine(f"sqlite:///{database_path.resolve()}")
    inspector = inspect(engine)
    actual = set(inspector.get_table_names())
    expected = {table.name for table in Base.metadata.sorted_tables}
    table_drift = {
        "missingTables": sorted(expected - actual),
        "extraTables": sorted(actual - expected - {"alembic_version"}),
    }
    column_drift = []
    for table_name in sorted(expected & actual):
        actual_columns = {column["name"] for column in inspector.get_columns(table_name)}
        expected_columns = {column.name for column in Base.metadata.tables[table_name].columns}
        if actual_columns != expected_columns:
            column_drift.append(
                {
                    "table": table_name,
                    "missingColumns": sorted(expected_columns - actual_columns),
                    "extraColumns": sorted(actual_columns - expected_columns),
                }
            )
    engine.dispose()
    compatible = not table_drift["missingTables"] and not column_drift
    return {"compatible": compatible, "tableDrift": table_drift, "columnDrift": column_drift}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and optionally stamp a legacy SQLite database.")
    parser.add_argument("--database", default="./organicai.db")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    database_path = Path(args.database).resolve()
    report = compare_legacy_schema(database_path)
    report["applied"] = False
    if args.apply:
        if not report["compatible"]:
            print(json.dumps(report, indent=2, sort_keys=True))
            return 1
        backup_sqlite_database(database_path, settings.db_backup_directory, settings.app_version)
        config = alembic_config(settings)
        config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")
        command.stamp(config, "head")
        report["applied"] = True
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["compatible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
