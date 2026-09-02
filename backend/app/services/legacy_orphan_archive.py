from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.services.database_admin import require_path_within, resolve_backend_path, sha256_file, utc_iso, utc_timestamp, write_json_atomic
from app.services.database_immutability import capture_sqlite_evidence, connect_readonly_sqlite, quote_identifier
from app.services.legacy_orphan_analysis import analyze_legacy_orphan_messages, get_legacy_orphan_message_rows


ARCHIVE_FORMAT_VERSION = 1
ARCHIVE_TOOL_VERSION = "task11.3-legacy-orphan-archive-v1"


def _table_info(connection: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(f"PRAGMA table_info({quote_identifier(table)})")]


def _create_orphan_messages_table(connection: sqlite3.Connection, message_columns: list[dict[str, Any]]) -> None:
    definitions = []
    for column in message_columns:
        name = str(column["name"])
        column_type = str(column["type"] or "TEXT")
        constraints = []
        if int(column.get("pk") or 0):
            constraints.append("PRIMARY KEY")
        elif int(column.get("notnull") or 0):
            constraints.append("NOT NULL")
        definition = f"{quote_identifier(name)} {column_type}"
        if constraints:
            definition += " " + " ".join(constraints)
        definitions.append(definition)
    connection.execute(f"CREATE TABLE orphan_messages ({', '.join(definitions)})")


def _insert_archive_metadata(connection: sqlite3.Connection, metadata: dict[str, Any]) -> None:
    connection.execute("CREATE TABLE archive_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    rows = []
    for key, value in metadata.items():
        rendered = value if isinstance(value, str) else json.dumps(value, sort_keys=True)
        rows.append((key, rendered))
    connection.executemany("INSERT INTO archive_metadata (key, value) VALUES (?, ?)", rows)


def _insert_orphan_evidence(connection: sqlite3.Connection, analysis: dict[str, Any]) -> None:
    connection.execute(
        """
        CREATE TABLE orphan_evidence (
            message_id_hash TEXT PRIMARY KEY,
            missing_conversation_id_hash TEXT NOT NULL,
            confidence TEXT NOT NULL,
            proposed_action TEXT NOT NULL,
            reason_codes_json TEXT NOT NULL,
            related_surviving_record_hashes_json TEXT NOT NULL,
            content_classification TEXT NOT NULL,
            approved_for_simulation INTEGER NOT NULL,
            approved_for_original INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    rows = []
    for item in analysis.get("items", []):
        related_hashes = [record.get("tableHash") for record in item.get("relatedSurvivingRecords", []) if record.get("tableHash")]
        rows.append(
            (
                item["messageIdHash"],
                item["missingConversationIdHash"],
                item.get("relinkConfidence", "none"),
                item.get("proposedAction", "archive-and-remove-from-active-data"),
                json.dumps(item.get("reasonCodes", []), sort_keys=True),
                json.dumps(related_hashes, sort_keys=True),
                item.get("contentClassification", "unknown"),
                1 if item.get("approvedForSimulation") else 0,
                1 if item.get("approvedForOriginal") else 0,
                utc_iso(),
            )
        )
    connection.executemany(
        """
        INSERT INTO orphan_evidence (
            message_id_hash,
            missing_conversation_id_hash,
            confidence,
            proposed_action,
            reason_codes_json,
            related_surviving_record_hashes_json,
            content_classification,
            approved_for_simulation,
            approved_for_original,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def _insert_orphan_index(connection: sqlite3.Connection, analysis: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    connection.execute("CREATE TABLE orphan_message_index (message_id_hash TEXT PRIMARY KEY, message_id TEXT NOT NULL UNIQUE)")
    index_rows = []
    for item, row in zip(analysis.get("items", []), rows, strict=True):
        index_rows.append((item["messageIdHash"], str(row["id"])))
    connection.executemany("INSERT INTO orphan_message_index (message_id_hash, message_id) VALUES (?, ?)", index_rows)


def _insert_orphan_messages(connection: sqlite3.Connection, rows: list[dict[str, Any]], columns: list[str]) -> None:
    quoted_columns = ", ".join(quote_identifier(column) for column in columns)
    placeholders = ", ".join("?" for _ in columns)
    values = [tuple(row.get(column) for column in columns) for row in rows]
    connection.executemany(f"INSERT INTO orphan_messages ({quoted_columns}) VALUES ({placeholders})", values)


def create_legacy_orphan_archive(
    source_path: str | Path,
    output_directory: str | Path = "./backups/legacy-orphans",
    *,
    analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = resolve_backend_path(source_path)
    output_dir = resolve_backend_path(output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = utc_timestamp()
    base_name = f"organicai-orphan-messages-{timestamp}"
    final_db = require_path_within(output_dir, output_dir / f"{base_name}.db")
    tmp_db = require_path_within(output_dir, output_dir / f"{base_name}.db.tmp")
    manifest_path = require_path_within(output_dir, output_dir / f"{base_name}.manifest.json")
    if final_db.exists() or manifest_path.exists():
        raise FileExistsError("Archive target already exists.")
    if tmp_db.exists():
        tmp_db.unlink()

    analysis = analysis or analyze_legacy_orphan_messages(source)
    orphan_rows = get_legacy_orphan_message_rows(source)
    source_evidence = capture_sqlite_evidence(source)
    source_connection = connect_readonly_sqlite(source)
    try:
        message_columns = _table_info(source_connection, "messages")
    finally:
        source_connection.close()
    column_names = [column["name"] for column in message_columns]

    archive_connection = sqlite3.connect(tmp_db)
    try:
        archive_connection.execute("PRAGMA journal_mode=DELETE")
        archive_connection.execute("PRAGMA foreign_keys=OFF")
        _insert_archive_metadata(
            archive_connection,
            {
                "archive_format_version": ARCHIVE_FORMAT_VERSION,
                "created_at": utc_iso(),
                "application_version": get_settings().app_version,
                "source_schema_state": {
                    "tableCount": source_evidence["schema"]["tableCount"],
                    "applicationTableCount": source_evidence["schema"]["applicationTableCount"],
                },
                "source_alembic_state": {
                    "exists": source_evidence["schema"]["alembicVersionExists"],
                    "rowCount": source_evidence["schema"]["alembicVersionRowCount"],
                },
                "source_database_hash": source_evidence["file"]["sha256"],
                "orphan_count": len(orphan_rows),
                "archive_reason": "Legacy messages reference missing conversations and block strict PostgreSQL migration.",
                "tool_version": ARCHIVE_TOOL_VERSION,
            },
        )
        _create_orphan_messages_table(archive_connection, message_columns)
        _insert_orphan_messages(archive_connection, orphan_rows, column_names)
        _insert_orphan_evidence(archive_connection, analysis)
        _insert_orphan_index(archive_connection, analysis, orphan_rows)
        archive_connection.commit()
    except Exception:
        archive_connection.rollback()
        raise
    finally:
        archive_connection.close()

    try:
        integrity = capture_sqlite_evidence(tmp_db)["sqlite"]["integrityCheck"]
        if integrity != "ok":
            raise RuntimeError("Archive SQLite integrity check failed.")
        tmp_db.replace(final_db)
        archive_sha = sha256_file(final_db)
        manifest = {
            "formatVersion": ARCHIVE_FORMAT_VERSION,
            "createdAt": utc_iso(),
            "archiveFormat": "organicai-legacy-orphan-messages",
            "toolVersion": ARCHIVE_TOOL_VERSION,
            "fileName": final_db.name,
            "sha256": archive_sha,
            "sizeBytes": final_db.stat().st_size,
            "sourceDatabase": "backend/organicai.db" if source.name == "organicai.db" else source.name,
            "sourceDatabaseHash": source_evidence["file"]["sha256"],
            "sourceAlembicState": {
                "exists": source_evidence["schema"]["alembicVersionExists"],
                "rowCount": source_evidence["schema"]["alembicVersionRowCount"],
            },
            "sourceOrphanRows": len(orphan_rows),
            "archivedRows": len(orphan_rows),
            "messageColumns": column_names,
            "containsMessageContent": "content" in column_names,
            "manifestContainsMessageContent": False,
            "rawIdentifiersIncludedInManifest": False,
            "gitIgnored": True,
            "localOnly": True,
        }
        write_json_atomic(manifest_path, manifest)
    except Exception:
        tmp_db.unlink(missing_ok=True)
        final_db.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)
        raise
    return {"archivePath": str(final_db), "manifestPath": str(manifest_path), "manifest": manifest, "analysis": analysis}


def verify_legacy_orphan_archive(
    source_path: str | Path,
    archive_path: str | Path,
    manifest_path: str | Path,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    source = resolve_backend_path(source_path)
    archive = resolve_backend_path(archive_path)
    manifest_file = resolve_backend_path(manifest_path)
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    source_rows = get_legacy_orphan_message_rows(source)
    source_by_id = {str(row["id"]): row for row in source_rows}
    source_columns = list(source_rows[0].keys()) if source_rows else []
    source_columns = [column for column in source_columns if column != "_rowid"]

    archive_connection = sqlite3.connect(archive.resolve().as_uri() + "?mode=ro", uri=True)
    archive_connection.row_factory = sqlite3.Row
    try:
        integrity = archive_connection.execute("PRAGMA integrity_check").fetchone()[0]
        tables = {
            row[0]
            for row in archive_connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        archive_columns = [row["name"] for row in archive_connection.execute("PRAGMA table_info(orphan_messages)")]
        archive_rows = [dict(row) for row in archive_connection.execute("SELECT * FROM orphan_messages")]
    finally:
        archive_connection.close()

    archive_ids = [str(row.get("id")) for row in archive_rows]
    archive_id_set = set(archive_ids)
    source_id_set = set(source_by_id)
    duplicate_count = len(archive_ids) - len(archive_id_set)
    missing_count = len(source_id_set - archive_id_set)
    unexpected_count = len(archive_id_set - source_id_set)
    null_content_count = sum(1 for row in archive_rows if "content" in row and row.get("content") is None)
    represented_columns = set(source_columns).issubset(set(archive_columns))
    rows_identical = True
    if represented_columns and not missing_count and not unexpected_count:
        for row in archive_rows:
            source_row = source_by_id.get(str(row.get("id")))
            if source_row is None:
                rows_identical = False
                break
            for column in source_columns:
                if row.get(column) != source_row.get(column):
                    rows_identical = False
                    break
            if not rows_identical:
                break
    else:
        rows_identical = False

    current_sha = sha256_file(archive)
    report = {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "archiveOpenedReadOnly": True,
        "manifestExists": manifest_file.exists(),
        "archiveExists": archive.exists(),
        "manifestSha256Matches": manifest.get("sha256") == current_sha,
        "sqliteIntegrityCheck": integrity,
        "expectedArchiveTablesExist": {"archive_metadata", "orphan_messages", "orphan_evidence", "orphan_message_index"}.issubset(tables),
        "sourceOrphanCount": len(source_rows),
        "archivedMessageCount": len(archive_rows),
        "archivedMessageIdsMatchSource": archive_id_set == source_id_set,
        "allOriginalColumnsRepresented": represented_columns,
        "noDuplicateMessageIds": duplicate_count == 0,
        "duplicateMessageIdCount": duplicate_count,
        "noMissingMessageContent": null_content_count == 0,
        "missingMessageContentCount": null_content_count,
        "noUnexpectedNonOrphanMessages": unexpected_count == 0,
        "unexpectedNonOrphanMessageCount": unexpected_count,
        "missingArchivedMessageCount": missing_count,
        "archivedRowsIdenticalToSource": rows_identical,
        "verificationPassed": False,
        "privacy": {
            "rawIdentifiersIncluded": False,
            "messageContentIncluded": False,
        },
    }
    report["verificationPassed"] = all(
        [
            report["manifestExists"],
            report["archiveExists"],
            report["manifestSha256Matches"],
            report["sqliteIntegrityCheck"] == "ok",
            report["expectedArchiveTablesExist"],
            report["archivedMessageCount"] == report["sourceOrphanCount"],
            report["archivedMessageIdsMatchSource"],
            report["allOriginalColumnsRepresented"],
            report["noDuplicateMessageIds"],
            report["noMissingMessageContent"],
            report["noUnexpectedNonOrphanMessages"],
            report["archivedRowsIdenticalToSource"],
        ]
    )
    if output_path is not None:
        output = resolve_backend_path(output_path)
        write_json_atomic(output, report)
        report["reportPath"] = str(output)
    return report


def summarize_legacy_orphan_archive(archive_path: str | Path) -> dict[str, Any]:
    archive = resolve_backend_path(archive_path)
    connection = sqlite3.connect(archive.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        message_count = int(connection.execute("SELECT COUNT(*) FROM orphan_messages").fetchone()[0])
        role_counts = dict(Counter(row[0] or "unknown" for row in connection.execute("SELECT role FROM orphan_messages")))
        row = connection.execute("SELECT MIN(created_at), MAX(created_at) FROM orphan_messages").fetchone()
        classifications = dict(Counter(row[0] or "unknown" for row in connection.execute("SELECT content_classification FROM orphan_evidence")))
    finally:
        connection.close()
    return {
        "archiveOpenedReadOnly": True,
        "sqliteIntegrityCheck": integrity,
        "messageCount": message_count,
        "roleCounts": role_counts,
        "dateRange": {"oldestCreatedAt": row[0], "newestCreatedAt": row[1]},
        "contentClassification": classifications,
        "messageContentIncluded": False,
    }
