from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from app.services.database_admin import require_path_within, resolve_backend_path, sha256_file, utc_iso, utc_timestamp, write_json_atomic


def sqlite_table_counts(path: Path) -> dict[str, int]:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        tables = [
            row[0]
            for row in connection.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name")
        ]
        counts = {}
        for table in tables:
            quoted = '"' + table.replace('"', '""') + '"'
            counts[table] = int(connection.execute(f"select count(*) from {quoted}").fetchone()[0])
        return counts
    finally:
        connection.close()


def sqlite_schema_version(path: Path) -> str | None:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        table_exists = connection.execute("select 1 from sqlite_master where type='table' and name='alembic_version'").fetchone()
        if not table_exists:
            return None
        row = connection.execute("select version_num from alembic_version limit 1").fetchone()
        return row[0] if row else None
    finally:
        connection.close()


def verify_sqlite_backup(source: Path, backup: Path) -> dict[str, Any]:
    source_counts = sqlite_table_counts(source)
    backup_counts = sqlite_table_counts(backup)
    connection = sqlite3.connect(f"file:{backup}?mode=ro", uri=True)
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        connection.close()
    return {
        "integrityCheck": integrity,
        "tableCountsMatch": source_counts == backup_counts,
        "sourceTableCount": len(source_counts),
        "backupTableCount": len(backup_counts),
    }


def backup_sqlite_database(source_path: Path, backup_directory: str | Path, application_version: str = "") -> dict[str, Any]:
    source = resolve_backend_path(source_path)
    if not source.exists():
        raise FileNotFoundError("SQLite source database does not exist.")
    backup_dir = resolve_backend_path(backup_directory)
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = utc_timestamp()
    base_name = f"organicai-sqlite-{timestamp}"
    final_db = require_path_within(backup_dir, backup_dir / f"{base_name}.db")
    tmp_db = require_path_within(backup_dir, backup_dir / f"{base_name}.db.tmp")
    manifest_path = require_path_within(backup_dir, backup_dir / f"{base_name}.manifest.json")

    if tmp_db.exists():
        tmp_db.unlink()
    source_connection = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    destination_connection = sqlite3.connect(tmp_db)
    try:
        source_connection.backup(destination_connection)
    finally:
        destination_connection.close()
        source_connection.close()

    verification = verify_sqlite_backup(source, tmp_db)
    if verification["integrityCheck"] != "ok" or not verification["tableCountsMatch"]:
        tmp_db.unlink(missing_ok=True)
        raise RuntimeError("SQLite backup verification failed.")

    tmp_db.replace(final_db)
    manifest = {
        "formatVersion": 1,
        "databaseType": "sqlite",
        "createdAt": utc_iso(),
        "applicationVersion": application_version,
        "schemaVersion": sqlite_schema_version(final_db),
        "fileName": final_db.name,
        "sha256": sha256_file(final_db),
        "sizeBytes": final_db.stat().st_size,
        "tableCounts": sqlite_table_counts(final_db),
        "sourceSanitized": "backend/organicai.db" if source.name == "organicai.db" else source.name,
        "verification": verification,
    }
    write_json_atomic(manifest_path, manifest)
    return {"backupPath": str(final_db), "manifestPath": str(manifest_path), "manifest": manifest}
