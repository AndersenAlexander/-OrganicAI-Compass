from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.services.database_immutability import capture_sqlite_evidence, create_consistent_sqlite_backup
from app.services.legacy_orphan_analysis import analyze_legacy_orphan_messages
from app.services.legacy_orphan_archive import create_legacy_orphan_archive, verify_legacy_orphan_archive
from app.services.legacy_remediation import apply_legacy_remediation_to_clone


def _legacy_messages_db(path: Path) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute("CREATE TABLE users (id TEXT PRIMARY KEY, email TEXT)")
        connection.execute("CREATE TABLE conversations (id TEXT PRIMARY KEY, user_id TEXT, created_at TEXT)")
        connection.execute(
            "CREATE TABLE messages (id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, role TEXT NOT NULL, "
            "content TEXT NOT NULL, input_mode TEXT, created_at TEXT NOT NULL, "
            "FOREIGN KEY(conversation_id) REFERENCES conversations(id))"
        )
        connection.execute("CREATE TABLE alembic_version (version_num TEXT PRIMARY KEY)")
        connection.execute("INSERT INTO users (id, email) VALUES ('user-1', 'person@example.test')")
        connection.execute("INSERT INTO conversations (id, user_id, created_at) VALUES ('conversation-1', 'user-1', '2026-01-01T00:00:00')")
        connection.execute(
            "INSERT INTO messages (id, conversation_id, role, content, input_mode, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("message-valid", "conversation-1", "user", "kept active", "text", "2026-01-01T00:00:00"),
        )
        connection.execute(
            "INSERT INTO messages (id, conversation_id, role, content, input_mode, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("message-orphan", "missing-conversation", "user", "private orphan body", "text", "2026-01-01T00:01:00"),
        )
        connection.commit()
    finally:
        connection.close()


def test_task11_3_evidence_and_forensics_are_read_only_and_sanitized(tmp_path: Path):
    database = tmp_path / "legacy.db"
    _legacy_messages_db(database)
    before = database.read_bytes()

    evidence = capture_sqlite_evidence(database)
    analysis = analyze_legacy_orphan_messages(database)
    rendered = json.dumps(analysis)

    assert database.read_bytes() == before
    assert evidence["openedReadOnly"] is True
    assert evidence["foreignKeys"]["foreignKeyViolationCount"] == 1
    assert evidence["schema"]["alembicVersionRowCount"] == 0
    assert analysis["summary"]["messageOrphanRows"] == 1
    assert analysis["summary"]["archiveOnlyCandidateRows"] == 1
    assert "private orphan body" not in rendered
    assert "missing-conversation" not in rendered


def test_task11_3_archive_verification_preserves_complete_rows_without_report_content(tmp_path: Path):
    database = tmp_path / "legacy.db"
    _legacy_messages_db(database)
    result = create_legacy_orphan_archive(database, tmp_path / "archives")

    verification = verify_legacy_orphan_archive(database, result["archivePath"], result["manifestPath"], tmp_path / "verification.json")
    rendered = json.dumps(verification)

    assert verification["verificationPassed"] is True
    assert verification["archivedMessageCount"] == 1
    assert verification["archivedMessageIdsMatchSource"] is True
    assert verification["sqliteIntegrityCheck"] == "ok"
    assert "private orphan body" not in rendered


def test_task11_3_clone_remediation_archives_and_removes_only_clone_orphans(tmp_path: Path):
    database = tmp_path / "legacy.db"
    _legacy_messages_db(database)
    backup = create_consistent_sqlite_backup(database, tmp_path / "backups")
    archive = create_legacy_orphan_archive(database, tmp_path / "archives")
    clone = tmp_path / "clone.db"

    result = apply_legacy_remediation_to_clone(
        original_path=database,
        source_backup_path=backup["backupPath"],
        archive_path=archive["archivePath"],
        archive_manifest_path=archive["manifestPath"],
        clone_path=clone,
        manifest_output=tmp_path / "manifest.json",
        journal_output=tmp_path / "journal.json",
        verification_output=tmp_path / "clone-verification.json",
        reconciliation_output=tmp_path / "reconciliation.json",
        inventory_output=tmp_path / "inventory.json",
        proposed_actions_output=tmp_path / "proposed-actions.json",
    )

    assert result["cloneCreation"]["initialSourceMatch"] is True
    assert result["journal"]["summary"]["archivedAndRemovedFromActiveClone"] == 1
    assert result["verification"]["foreignKeyViolations"] == 0
    assert result["verification"]["emptyAlembicVersionTableAbsent"] is True
    assert result["reconciliation"]["lostRowCount"] == 0
    assert result["reconciliation"]["duplicateRowCount"] == 0

    original = sqlite3.connect(database)
    cleaned = sqlite3.connect(clone)
    try:
        assert original.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 2
        assert cleaned.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 1
        assert cleaned.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='alembic_version'").fetchone() is None
    finally:
        original.close()
        cleaned.close()
