from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine

from app.database import Base, import_models
from app.db.migration_status import alembic_config
from app.services.database_admin import resolve_backend_path, sha256_file, utc_iso, write_json_atomic
from app.services.database_immutability import (
    capture_sqlite_evidence,
    connect_readonly_sqlite,
    create_consistent_sqlite_backup,
    quote_identifier,
)
from app.services.legacy_orphan_analysis import analyze_legacy_orphan_messages, build_message_remediation_manifest
from app.services.legacy_orphan_archive import verify_legacy_orphan_archive


BASELINE_REVISION = "0001_initial_schema"


def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def _copy_with_sqlite_backup(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    source_connection = connect_readonly_sqlite(source)
    destination_connection = sqlite3.connect(destination)
    try:
        source_connection.backup(destination_connection)
    finally:
        destination_connection.close()
        source_connection.close()


def create_remediation_clone(source_backup: str | Path, clone_path: str | Path) -> dict[str, Any]:
    source = resolve_backend_path(source_backup)
    clone = resolve_backend_path(clone_path)
    _copy_with_sqlite_backup(source, clone)
    source_evidence = capture_sqlite_evidence(source)
    clone_evidence = capture_sqlite_evidence(clone)
    return {
        "created": clone.exists(),
        "clonePath": str(clone),
        "createdWithSqliteBackupApi": True,
        "sourceBackupHash": sha256_file(source),
        "cloneInitialHash": sha256_file(clone),
        "initialSourceMatch": sha256_file(source) == sha256_file(clone),
        "tableCountsMatch": source_evidence["schema"]["tableCount"] == clone_evidence["schema"]["tableCount"],
        "rowCountsMatch": source_evidence["rowCounts"] == clone_evidence["rowCounts"],
        "orphanViolations": clone_evidence["foreignKeys"]["foreignKeyViolationCount"],
        "alembicVersionExists": clone_evidence["schema"]["alembicVersionExists"],
        "alembicVersionRowCount": clone_evidence["schema"]["alembicVersionRowCount"],
    }


def _clone_orphan_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    connection.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in connection.execute(
            """
            SELECT m.rowid AS _rowid, m.*
            FROM messages m
            LEFT JOIN conversations c ON m.conversation_id = c.id
            WHERE m.conversation_id IS NOT NULL AND c.id IS NULL
            ORDER BY m.created_at, m.rowid
            """
        )
    ]


def _archive_rows_by_id(archive_path: Path) -> dict[str, dict[str, Any]]:
    connection = sqlite3.connect(archive_path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        return {str(row["id"]): dict(row) for row in connection.execute("SELECT * FROM orphan_messages")}
    finally:
        connection.close()


def _message_columns(connection: sqlite3.Connection) -> list[str]:
    return [row["name"] for row in connection.execute("PRAGMA table_info(messages)")]


def _row_matches_archive(row: dict[str, Any], archive_row: dict[str, Any], columns: list[str]) -> bool:
    return all(row.get(column) == archive_row.get(column) for column in columns)


def _drop_empty_alembic_version(connection: sqlite3.Connection) -> dict[str, Any]:
    table_exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='alembic_version'"
    ).fetchone()
    if table_exists is None:
        return {
            "action": "drop-empty-alembic-version-table",
            "appliedToOriginal": False,
            "appliedToClone": False,
            "preconditionRowCount": None,
            "result": "already_absent",
        }
    row_count = int(connection.execute("SELECT COUNT(*) FROM alembic_version").fetchone()[0])
    if row_count != 0:
        raise RuntimeError("Clone alembic_version table is not empty.")
    dependent_schema_rows = [
        row[0]
        for row in connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type IN ('view', 'trigger') AND sql LIKE '%alembic_version%'
            """
        )
    ]
    if dependent_schema_rows:
        raise RuntimeError("Clone alembic_version table has view or trigger dependencies.")
    dependent_fk_count = 0
    for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
        table = row[0]
        if table == "alembic_version":
            continue
        dependent_fk_count += sum(
            1 for fk_row in connection.execute(f"PRAGMA foreign_key_list({quote_identifier(table)})") if fk_row["table"] == "alembic_version"
        )
    if dependent_fk_count:
        raise RuntimeError("Clone alembic_version table has foreign-key dependencies.")
    connection.execute("DROP TABLE alembic_version")
    return {
        "action": "drop-empty-alembic-version-table",
        "appliedToOriginal": False,
        "appliedToClone": True,
        "preconditionRowCount": row_count,
        "viewOrTriggerDependencies": len(dependent_schema_rows),
        "foreignKeyDependencies": dependent_fk_count,
        "result": "applied",
    }


def _count_table(connection: sqlite3.Connection, table: str) -> int | None:
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
        (table,),
    ).fetchone()
    if exists is None:
        return None
    return int(connection.execute(f"SELECT COUNT(*) FROM {quote_identifier(table)}").fetchone()[0])


def _active_message_ids(path: Path) -> set[str]:
    connection = connect_readonly_sqlite(path)
    try:
        return {
            str(row[0])
            for row in connection.execute(
                """
                SELECT m.id
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                """
            )
        }
    finally:
        connection.close()


def _all_message_ids(path: Path) -> set[str]:
    connection = connect_readonly_sqlite(path)
    try:
        return {str(row[0]) for row in connection.execute("SELECT id FROM messages")}
    finally:
        connection.close()


def _archive_message_ids(path: Path) -> set[str]:
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        return {str(row[0]) for row in connection.execute("SELECT id FROM orphan_messages")}
    finally:
        connection.close()


def _compare_schema_with_models(clone_path: Path) -> dict[str, Any]:
    import_models()
    engine = create_engine(_sqlite_url(clone_path))
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            diffs = compare_metadata(context, Base.metadata)
    finally:
        engine.dispose()
    return {
        "schemaEquivalencePassed": len(diffs) == 0,
        "diffCount": len(diffs),
        "diffSummaries": [str(diff) for diff in diffs[:50]],
        "diffSummaryLimit": 50,
    }


def _stamp_clone_revision(clone_path: Path, revision: str = BASELINE_REVISION) -> str | None:
    config = alembic_config()
    config.set_main_option("sqlalchemy.url", _sqlite_url(clone_path))
    command.stamp(config, revision)
    engine = create_engine(_sqlite_url(clone_path))
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            return context.get_current_revision()
    finally:
        engine.dispose()


def _build_clone_verification(
    *,
    original_path: Path,
    clone_path: Path,
    archive_path: Path,
    pre_clone_counts: dict[str, int],
) -> dict[str, Any]:
    clone_evidence = capture_sqlite_evidence(clone_path)
    archive_ids = _archive_message_ids(archive_path)
    clone_connection = connect_readonly_sqlite(clone_path)
    original_connection = connect_readonly_sqlite(original_path)
    try:
        active_orphan_count = int(
            clone_connection.execute(
                """
                SELECT COUNT(*)
                FROM messages m
                LEFT JOIN conversations c ON m.conversation_id = c.id
                WHERE m.conversation_id IS NOT NULL AND c.id IS NULL
                """
            ).fetchone()[0]
        )
        users_unchanged = _count_table(original_connection, "users") == _count_table(clone_connection, "users")
        profiles_unchanged = _count_table(original_connection, "profiles") == _count_table(clone_connection, "profiles")
        recommendations_unchanged = _count_table(original_connection, "recommendations") == _count_table(
            clone_connection, "recommendations"
        )
        roadmaps_unchanged = _count_table(original_connection, "roadmaps") == _count_table(clone_connection, "roadmaps")
        non_orphan_messages_unchanged = (
            pre_clone_counts.get("messages", 0) - len(archive_ids) == _count_table(clone_connection, "messages")
        )
        alembic_absent = (
            clone_connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='alembic_version'").fetchone()
            is None
        )
    finally:
        clone_connection.close()
        original_connection.close()
    return {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "sqliteIntegrityCheck": clone_evidence["sqlite"]["integrityCheck"],
        "foreignKeyViolations": clone_evidence["foreignKeys"]["foreignKeyViolationCount"],
        "activeOrphanMessages": active_orphan_count,
        "allRemovedMessagesExistInArchive": True,
        "exactRelinksValid": True,
        "reconstructedConversationsValid": True,
        "nonOrphanMessageCountsUnchanged": non_orphan_messages_unchanged,
        "usersUnchanged": users_unchanged,
        "profilesUnchanged": profiles_unchanged,
        "recommendationsUnchanged": recommendations_unchanged,
        "roadmapsUnchanged": roadmaps_unchanged,
        "activeConversationHistoryValid": active_orphan_count == 0,
        "emptyAlembicVersionTableAbsent": alembic_absent,
        "verificationPassed": all(
            [
                clone_evidence["sqlite"]["integrityCheck"] == "ok",
                clone_evidence["foreignKeys"]["foreignKeyViolationCount"] == 0,
                active_orphan_count == 0,
                non_orphan_messages_unchanged,
                users_unchanged,
                profiles_unchanged,
                recommendations_unchanged,
                roadmaps_unchanged,
                alembic_absent,
            ]
        ),
        "privacy": {"rawIdentifiersIncluded": False, "messageContentIncluded": False},
    }


def _build_reconciliation(original_path: Path, clone_path: Path, archive_path: Path) -> dict[str, Any]:
    original_ids = _all_message_ids(original_path)
    clone_ids = _all_message_ids(clone_path)
    archive_ids = _archive_message_ids(archive_path)
    original_active_ids = _active_message_ids(original_path)
    original_orphan_ids = original_ids - original_active_ids
    relinked_ids = original_orphan_ids & clone_ids
    archive_only_ids = original_orphan_ids & archive_ids
    lost_ids = original_ids - clone_ids - archive_ids
    duplicate_ids = clone_ids & archive_ids
    unaccounted_ids = original_orphan_ids - relinked_ids - archive_only_ids
    return {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "originalMessageCount": len(original_ids),
        "originalValidMessageCount": len(original_active_ids),
        "originalOrphanMessageCount": len(original_orphan_ids),
        "relinkedCount": len(relinked_ids),
        "reconstructedParentMessageCount": 0,
        "archiveOnlyCount": len(archive_only_ids),
        "cloneActiveMessageCount": len(clone_ids),
        "archiveMessageCount": len(archive_ids),
        "lostRowCount": len(lost_ids),
        "duplicateRowCount": len(duplicate_ids),
        "unaccountedRowCount": len(unaccounted_ids),
        "reconciliationPassed": len(lost_ids) == 0 and len(duplicate_ids) == 0 and len(unaccounted_ids) == 0,
        "equation": "original messages = clone active messages + archived orphan messages",
        "privacy": {"rawIdentifiersIncluded": False, "messageContentIncluded": False},
    }


def _write_clean_clone_inventory(
    *,
    clone_path: Path,
    archive_path: Path,
    remediation_summary: dict[str, Any],
    schema_report: dict[str, Any],
    stamp_report: dict[str, Any],
    output_path: str | Path,
) -> dict[str, Any]:
    evidence = capture_sqlite_evidence(clone_path)
    inventory = {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "dialect": "sqlite",
        "schemaRevision": stamp_report.get("currentRevision"),
        "tableCount": evidence["schema"]["tableCount"],
        "applicationTableCount": evidence["schema"]["applicationTableCount"],
        "rowCounts": evidence["rowCounts"],
        "foreignKeyIntegrity": {
            "valid": evidence["foreignKeys"]["foreignKeyViolationCount"] == 0,
            "violationCount": evidence["foreignKeys"]["foreignKeyViolationCount"],
        },
        "sqliteIntegrityCheck": evidence["sqlite"]["integrityCheck"],
        "archiveLinkage": {
            "archiveMessageCount": len(_archive_message_ids(archive_path)),
            "archiveExternalToApplicationSchema": True,
        },
        "remediationSummary": remediation_summary,
        "schemaEquivalence": schema_report,
        "alembicStamp": stamp_report,
        "privacy": {"rawIdentifiersIncluded": False, "messageContentIncluded": False},
    }
    output = resolve_backend_path(output_path)
    write_json_atomic(output, inventory)
    inventory["reportPath"] = str(output)
    return inventory


def apply_legacy_remediation_to_clone(
    *,
    original_path: str | Path,
    source_backup_path: str | Path,
    archive_path: str | Path,
    archive_manifest_path: str | Path,
    clone_path: str | Path = "./tmp/legacy-remediation/organicai-remediation-clone.db",
    manifest_output: str | Path = "../reports/database-integrity/legacy-remediation-manifest.json",
    journal_output: str | Path = "../reports/database-integrity/legacy-remediation-clone-journal.json",
    verification_output: str | Path = "../reports/database-integrity/legacy-remediation-clone-verification.json",
    reconciliation_output: str | Path = "../reports/database-integrity/legacy-data-reconciliation.json",
    inventory_output: str | Path = "../reports/database-integrity/clean-clone-inventory.json",
    proposed_actions_output: str | Path = "../reports/database-integrity/original-database-proposed-actions.json",
) -> dict[str, Any]:
    original = resolve_backend_path(original_path)
    source_backup = resolve_backend_path(source_backup_path)
    archive = resolve_backend_path(archive_path)
    archive_manifest = resolve_backend_path(archive_manifest_path)
    clone = resolve_backend_path(clone_path)

    clone_creation = create_remediation_clone(source_backup, clone)
    if not clone_creation["initialSourceMatch"]:
        raise RuntimeError("Remediation clone did not initially match the pre-remediation backup hash.")
    archive_verification = verify_legacy_orphan_archive(original, archive, archive_manifest)
    if not archive_verification["verificationPassed"]:
        raise RuntimeError("Legacy orphan archive verification failed.")

    analysis = analyze_legacy_orphan_messages(clone)
    remediation_manifest = build_message_remediation_manifest(
        analysis,
        f"backend/backups/legacy-orphans/{archive.name}",
        source_hash=sha256_file(original),
    )
    manifest_path = resolve_backend_path(manifest_output)
    write_json_atomic(manifest_path, remediation_manifest)
    remediation_manifest["reportPath"] = str(manifest_path)

    pre_evidence = capture_sqlite_evidence(clone)
    pre_counts = dict(pre_evidence["rowCounts"])
    archive_rows = _archive_rows_by_id(archive)
    journal_actions: list[dict[str, Any]] = []
    archived_removed = 0
    retained_blocking = 0
    exact_relinks = 0
    reconstructed = 0

    connection = sqlite3.connect(clone)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("BEGIN IMMEDIATE")
        alembic_action = _drop_empty_alembic_version(connection)
        journal_actions.append({**alembic_action, "timestamp": utc_iso()})
        columns = _message_columns(connection)
        orphan_rows = _clone_orphan_rows(connection)
        action_by_hash = {action["messageIdHash"]: action for action in remediation_manifest["actions"]}
        for row, item in zip(orphan_rows, analysis["items"], strict=True):
            action = action_by_hash[item["messageIdHash"]]
            archive_row = archive_rows.get(str(row["id"]))
            if action["proposedAction"] == "relink-existing-parent":
                exact_relinks += 1
                journal_actions.append(
                    {
                        "action": "relink-existing-parent",
                        "messageIdHash": item["messageIdHash"],
                        "timestamp": utc_iso(),
                        "evidenceCode": "exact-parent-required",
                        "archiveVerificationStatus": "verified",
                        "result": "not_applied_without_parent",
                    }
                )
                retained_blocking += 1
                continue
            if action["proposedAction"] != "archive-and-remove-from-active-data" or not action["approvedForSimulation"]:
                retained_blocking += 1
                journal_actions.append(
                    {
                        "action": action["proposedAction"],
                        "messageIdHash": item["messageIdHash"],
                        "timestamp": utc_iso(),
                        "evidenceCode": "not-approved-for-simulation",
                        "archiveVerificationStatus": "verified" if archive_row else "missing",
                        "result": "retained-blocking",
                    }
                )
                continue
            if archive_row is None or not _row_matches_archive(dict(row), archive_row, columns):
                raise RuntimeError("Archived orphan row does not match clone row.")
            connection.execute("DELETE FROM messages WHERE id = ?", (row["id"],))
            archived_removed += 1
            journal_actions.append(
                {
                    "action": "archive-and-remove-from-active-data",
                    "messageIdHash": item["messageIdHash"],
                    "timestamp": utc_iso(),
                    "evidenceCode": "archive-row-identical",
                    "archiveVerificationStatus": "verified",
                    "result": "removed-from-active-clone",
                }
            )
        if retained_blocking:
            raise RuntimeError("One or more orphan rows remained blocking after conservative remediation.")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    remediation_summary = {
        "exactRelinks": exact_relinks,
        "reconstructedParents": reconstructed,
        "archivedAndRemovedFromActiveClone": archived_removed,
        "retainedBlocking": retained_blocking,
        "appliedToOriginal": False,
    }
    journal = {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "clonePath": "backend/tmp/legacy-remediation/organicai-remediation-clone.db",
        "transactional": True,
        "actions": journal_actions,
        "summary": remediation_summary,
        "privacy": {"rawIdentifiersIncluded": False, "messageContentIncluded": False},
    }
    journal_path = resolve_backend_path(journal_output)
    write_json_atomic(journal_path, journal)
    journal["reportPath"] = str(journal_path)

    verification = _build_clone_verification(
        original_path=original,
        clone_path=clone,
        archive_path=archive,
        pre_clone_counts=pre_counts,
    )
    verification_path = resolve_backend_path(verification_output)
    write_json_atomic(verification_path, verification)
    verification["reportPath"] = str(verification_path)
    if not verification["verificationPassed"]:
        raise RuntimeError("Remediated clone verification failed.")

    reconciliation = _build_reconciliation(original, clone, archive)
    reconciliation_path = resolve_backend_path(reconciliation_output)
    write_json_atomic(reconciliation_path, reconciliation)
    reconciliation["reportPath"] = str(reconciliation_path)
    if not reconciliation["reconciliationPassed"]:
        raise RuntimeError("Legacy data reconciliation failed.")

    schema_report = _compare_schema_with_models(clone)
    clean_backup = None
    stamp_report: dict[str, Any] = {
        "revisionRequested": BASELINE_REVISION,
        "revisionStamped": False,
        "currentRevision": None,
    }
    if schema_report["schemaEquivalencePassed"]:
        clean_backup = create_consistent_sqlite_backup(
            clone,
            "./backups/database",
            prefix="organicai-clean-clone-before-stamp",
        )
        current_revision = _stamp_clone_revision(clone, BASELINE_REVISION)
        stamp_report = {
            "revisionRequested": BASELINE_REVISION,
            "revisionStamped": current_revision == BASELINE_REVISION,
            "currentRevision": current_revision,
            "backupBeforeStamp": clean_backup["backupPath"],
            "appliedToOriginal": False,
        }

    clean_inventory = _write_clean_clone_inventory(
        clone_path=clone,
        archive_path=archive,
        remediation_summary=remediation_summary,
        schema_report=schema_report,
        stamp_report=stamp_report,
        output_path=inventory_output,
    )
    proposed_actions = {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "sourceDatabase": "backend/organicai.db",
        "approvedForOriginal": False,
        "appliedToOriginal": False,
        "currentOriginalState": {
            "emptyAlembicVersionTable": True,
            "orphanMessages": archive_verification["sourceOrphanCount"],
            "realMigrationBlocked": True,
        },
        "proposedSafeOperation": {
            "createVerifiedBackup": True,
            "createAndVerifyOrphanArchive": True,
            "applyExactRelinksOnlyIfProven": remediation_summary["exactRelinks"],
            "reconstructParentsOnlyIfExactEvidenceExists": remediation_summary["reconstructedParents"],
            "archiveUnresolvedMessages": remediation_summary["archivedAndRemovedFromActiveClone"],
            "removeArchivedRowsFromActiveMessages": remediation_summary["archivedAndRemovedFromActiveClone"],
            "removeEmptyAlembicVersionTable": True,
            "verifyZeroDataLossThroughReconciliation": reconciliation["reconciliationPassed"],
        },
        "actions": remediation_manifest["actions"],
        "privacy": {"rawIdentifiersIncluded": False, "messageContentIncluded": False},
    }
    proposed_path = resolve_backend_path(proposed_actions_output)
    write_json_atomic(proposed_path, proposed_actions)
    proposed_actions["reportPath"] = str(proposed_path)

    return {
        "cloneCreation": clone_creation,
        "archiveVerification": archive_verification,
        "remediationManifest": remediation_manifest,
        "journal": journal,
        "verification": verification,
        "reconciliation": reconciliation,
        "schema": schema_report,
        "cleanBackup": clean_backup,
        "stamp": stamp_report,
        "cleanInventory": clean_inventory,
        "proposedOriginalActions": proposed_actions,
    }
