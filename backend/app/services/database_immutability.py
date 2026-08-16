from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from typing import Any

from app.core.time import utc_from_timestamp
from app.services.database_admin import (
    require_path_within,
    resolve_backend_path,
    sha256_file,
    utc_iso,
    utc_timestamp,
    write_json_atomic,
)


def sqlite_readonly_uri(database_path: Path) -> str:
    return database_path.resolve().as_uri() + "?mode=ro"


def connect_readonly_sqlite(database_path: str | Path) -> sqlite3.Connection:
    database = resolve_backend_path(database_path)
    connection = sqlite3.connect(sqlite_readonly_uri(database), uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def list_sqlite_tables(connection: sqlite3.Connection) -> list[str]:
    return [
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]


def sqlite_table_row_counts(connection: sqlite3.Connection, tables: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in tables:
        counts[table] = int(connection.execute(f"SELECT COUNT(*) FROM {quote_identifier(table)}").fetchone()[0])
    return counts


def sqlite_foreign_key_summary(connection: sqlite3.Connection) -> dict[str, Any]:
    rows = [dict(row) for row in connection.execute("PRAGMA foreign_key_check")]
    relations: dict[str, int] = {}
    for row in rows:
        key = f"{row['table']}->{row['parent']}#{row['fkid']}"
        relations[key] = relations.get(key, 0) + 1
    return {
        "foreignKeyViolationCount": len(rows),
        "distinctAffectedOrphanRowCount": len({(row["table"], row["rowid"]) for row in rows}),
        "relations": relations,
    }


def capture_sqlite_evidence(database_path: str | Path) -> dict[str, Any]:
    database = resolve_backend_path(database_path)
    if not database.exists():
        raise FileNotFoundError("SQLite database does not exist.")
    stat = database.stat()
    connection = connect_readonly_sqlite(database)
    try:
        tables = list_sqlite_tables(connection)
        row_counts = sqlite_table_row_counts(connection, tables)
        application_tables = [table for table in tables if table != "alembic_version"]
        page_count = int(connection.execute("PRAGMA page_count").fetchone()[0])
        page_size = int(connection.execute("PRAGMA page_size").fetchone()[0])
        integrity_check = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
        alembic_exists = "alembic_version" in tables
        alembic_row_count = int(connection.execute("SELECT COUNT(*) FROM alembic_version").fetchone()[0]) if alembic_exists else None
        fk_summary = sqlite_foreign_key_summary(connection)
    finally:
        connection.close()

    return {
        "formatVersion": 1,
        "capturedAt": utc_iso(),
        "database": "backend/organicai.db" if database.name == "organicai.db" else database.name,
        "path": str(database),
        "openedReadOnly": True,
        "file": {
            "sizeBytes": stat.st_size,
            "modifiedTimeUtc": utc_from_timestamp(stat.st_mtime).isoformat(),
            "sha256": sha256_file(database),
        },
        "sqlite": {
            "pageCount": page_count,
            "pageSize": page_size,
            "integrityCheck": integrity_check,
        },
        "schema": {
            "tableCount": len(tables),
            "applicationTableCount": len(application_tables),
            "tables": tables,
            "alembicVersionExists": alembic_exists,
            "alembicVersionRowCount": alembic_row_count,
        },
        "rowCounts": row_counts,
        "applicationRowCounts": {table: row_counts[table] for table in application_tables},
        "foreignKeys": fk_summary,
        "privacy": {
            "rowContentIncluded": False,
            "rawIdentifiersIncluded": False,
        },
    }


def compare_sqlite_evidence(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_rows = before.get("applicationRowCounts", {})
    after_rows = after.get("applicationRowCounts", {})
    proof = {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "changedDuringTask": False,
        "sha256Matches": before.get("file", {}).get("sha256") == after.get("file", {}).get("sha256"),
        "sizeMatches": before.get("file", {}).get("sizeBytes") == after.get("file", {}).get("sizeBytes"),
        "pageCountMatches": before.get("sqlite", {}).get("pageCount") == after.get("sqlite", {}).get("pageCount"),
        "tableCountMatches": before.get("schema", {}).get("tableCount") == after.get("schema", {}).get("tableCount"),
        "applicationRowCountsMatch": before_rows == after_rows,
        "foreignKeyViolationCountMatches": before.get("foreignKeys", {}).get("foreignKeyViolationCount")
        == after.get("foreignKeys", {}).get("foreignKeyViolationCount"),
        "beforeReport": before.get("reportPath"),
        "afterReport": after.get("reportPath"),
    }
    proof["changedDuringTask"] = not all(
        [
            proof["sha256Matches"],
            proof["sizeMatches"],
            proof["pageCountMatches"],
            proof["tableCountMatches"],
            proof["applicationRowCountsMatch"],
            proof["foreignKeyViolationCountMatches"],
        ]
    )
    return proof


def write_sqlite_evidence(database_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    output = resolve_backend_path(output_path)
    report = capture_sqlite_evidence(database_path)
    write_json_atomic(output, report)
    report["reportPath"] = str(output)
    return report


def write_immutability_proof(before_path: str | Path, after_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    before = json.loads(resolve_backend_path(before_path).read_text(encoding="utf-8"))
    after = json.loads(resolve_backend_path(after_path).read_text(encoding="utf-8"))
    before["reportPath"] = str(resolve_backend_path(before_path))
    after["reportPath"] = str(resolve_backend_path(after_path))
    proof = compare_sqlite_evidence(before, after)
    output = resolve_backend_path(output_path)
    write_json_atomic(output, proof)
    proof["reportPath"] = str(output)
    return proof


def create_consistent_sqlite_backup(
    source_path: str | Path,
    backup_directory: str | Path = "./backups/database",
    *,
    application_version: str = "",
    prefix: str = "organicai-pre-remediation",
) -> dict[str, Any]:
    source = resolve_backend_path(source_path)
    if not source.exists():
        raise FileNotFoundError("SQLite source database does not exist.")
    backup_dir = resolve_backend_path(backup_directory)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = utc_timestamp()
    base_name = f"{prefix}-{timestamp}"
    final_db = require_path_within(backup_dir, backup_dir / f"{base_name}.db")
    tmp_db = require_path_within(backup_dir, backup_dir / f"{base_name}.db.tmp")
    manifest_path = require_path_within(backup_dir, backup_dir / f"{base_name}.manifest.json")
    if final_db.exists() or manifest_path.exists():
        raise FileExistsError("Backup target already exists.")
    if tmp_db.exists():
        tmp_db.unlink()

    source_connection = connect_readonly_sqlite(source)
    destination_connection = sqlite3.connect(tmp_db)
    try:
        source_connection.backup(destination_connection)
    finally:
        destination_connection.close()
        source_connection.close()

    try:
        source_evidence = capture_sqlite_evidence(source)
        backup_evidence = capture_sqlite_evidence(tmp_db)
        logical_equivalence = {
            "tableCountsMatch": source_evidence["schema"]["tableCount"] == backup_evidence["schema"]["tableCount"],
            "rowCountsMatch": source_evidence["rowCounts"] == backup_evidence["rowCounts"],
            "applicationRowCountsMatch": source_evidence["applicationRowCounts"] == backup_evidence["applicationRowCounts"],
            "foreignKeyViolationCountMatches": source_evidence["foreignKeys"]["foreignKeyViolationCount"]
            == backup_evidence["foreignKeys"]["foreignKeyViolationCount"],
            "integrityCheck": backup_evidence["sqlite"]["integrityCheck"],
        }
        if backup_evidence["sqlite"]["integrityCheck"] != "ok" or not all(
            value is True for key, value in logical_equivalence.items() if key != "integrityCheck"
        ):
            raise RuntimeError("SQLite backup verification failed.")
        tmp_db.replace(final_db)
        final_evidence = capture_sqlite_evidence(final_db)
        manifest = {
            "formatVersion": 1,
            "createdAt": utc_iso(),
            "applicationVersion": application_version,
            "databaseType": "sqlite",
            "sourceDatabase": "backend/organicai.db" if source.name == "organicai.db" else source.name,
            "fileName": final_db.name,
            "sha256": sha256_file(final_db),
            "sizeBytes": final_db.stat().st_size,
            "sqliteIntegrityCheck": final_evidence["sqlite"]["integrityCheck"],
            "tableCount": final_evidence["schema"]["tableCount"],
            "applicationTableCount": final_evidence["schema"]["applicationTableCount"],
            "rowCounts": final_evidence["rowCounts"],
            "orphanViolations": final_evidence["foreignKeys"]["foreignKeyViolationCount"],
            "distinctAffectedRows": final_evidence["foreignKeys"]["distinctAffectedOrphanRowCount"],
            "alembicVersionExists": final_evidence["schema"]["alembicVersionExists"],
            "alembicVersionRowCount": final_evidence["schema"]["alembicVersionRowCount"],
            "createdWithSqliteBackupApi": True,
            "logicalEquivalence": logical_equivalence,
            "containsRowContent": True,
            "manifestContainsRowContent": False,
        }
        write_json_atomic(manifest_path, manifest)
    except Exception:
        tmp_db.unlink(missing_ok=True)
        final_db.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)
        raise

    return {"backupPath": str(final_db), "manifestPath": str(manifest_path), "manifest": manifest}
