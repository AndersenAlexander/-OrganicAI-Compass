from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from app.config import get_settings
from app.services import postgres_backup
from app.services.legacy_orphan_analysis import analyze_legacy_orphans, write_remediation_plan
from app.services.sqlite_to_postgres import migrate_sqlite_to_postgres


def _orphan_sqlite(path: Path, *, include_second_fk: bool = False) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute("CREATE TABLE parent (id TEXT PRIMARY KEY)")
        if include_second_fk:
            conn.execute(
                "CREATE TABLE child (id TEXT PRIMARY KEY, parent_id TEXT, other_parent_id TEXT, email TEXT, message TEXT, "
                "created_at TEXT, FOREIGN KEY(parent_id) REFERENCES parent(id), FOREIGN KEY(other_parent_id) REFERENCES parent(id))"
            )
            conn.execute(
                "INSERT INTO child (id, parent_id, other_parent_id, email, message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                ("child-1", "missing-1", "missing-2", "person@example.test", "private message", "2026-01-01T00:00:00"),
            )
        else:
            conn.execute(
                "CREATE TABLE child (id TEXT PRIMARY KEY, parent_id TEXT, email TEXT, message TEXT, created_at TEXT, "
                "FOREIGN KEY(parent_id) REFERENCES parent(id))"
            )
            conn.execute(
                "INSERT INTO child (id, parent_id, email, message, created_at) VALUES (?, ?, ?, ?, ?)",
                ("child-1", "missing-1", "person@example.test", "private message", "2026-01-01T00:00:00"),
            )
        conn.commit()
    finally:
        conn.close()


def test_pg_dump_local_command_redacts_password_to_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("PG_TOOLS_MODE", "local")
    monkeypatch.setattr(postgres_backup.shutil, "which", lambda name: f"C:/pg/bin/{name}.exe")

    command, env = postgres_backup.build_pg_dump_command(
        "postgresql+psycopg2://organicai:secret@127.0.0.1:55432/organicai_task11",
        tmp_path / "backup.dump",
    )

    rendered = " ".join(command)
    assert "secret" not in rendered
    assert env["PGPASSWORD"] == "secret"
    assert "--format=custom" in command
    assert "--file" in command


def test_pg_tools_docker_compose_mode_validates_service_and_compose_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    compose = tmp_path / "docker-compose.persistence.yml"
    compose.write_text("services: {}\n", encoding="utf-8")
    monkeypatch.setenv("PG_TOOLS_MODE", "docker-compose")
    monkeypatch.setenv("PG_DOCKER_COMPOSE_FILE", str(compose))
    monkeypatch.setenv("PG_DOCKER_SERVICE", "organicai-postgres")
    monkeypatch.setattr(postgres_backup.shutil, "which", lambda name: "C:/Docker/docker.exe" if name == "docker" else None)

    prefix = postgres_backup._docker_compose_exec_prefix()

    assert prefix[:4] == ["C:/Docker/docker.exe", "compose", "-f", str(compose.resolve())]
    assert prefix[-2:] == ["-T", "organicai-postgres"]

    monkeypatch.setenv("PG_DOCKER_SERVICE", "organicai-postgres;drop")
    with pytest.raises(ValueError):
        postgres_backup.docker_compose_config()

    monkeypatch.setenv("PG_DOCKER_SERVICE", "organicai-postgres")
    monkeypatch.setenv("PG_DOCKER_COMPOSE_FILE", str(tmp_path / "missing.yml"))
    with pytest.raises(FileNotFoundError):
        postgres_backup.docker_compose_config()


def test_pg_identifier_injection_rejected():
    with pytest.raises(ValueError):
        postgres_backup._validate_pg_identifier("organicai;drop", "database name")


def test_docker_compose_archive_verification_uses_binary_safe_copy(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    compose = tmp_path / "docker-compose.persistence.yml"
    compose.write_text("services: {}\n", encoding="utf-8")
    archive = tmp_path / "organicai-postgres-test.dump"
    archive.write_bytes(b"PGDMP")
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setenv("PG_TOOLS_MODE", "docker-compose")
    monkeypatch.setenv("PG_DOCKER_COMPOSE_FILE", str(compose))
    monkeypatch.setenv("PG_DOCKER_SERVICE", "organicai-postgres")
    monkeypatch.setattr(postgres_backup.shutil, "which", lambda name: "docker" if name == "docker" else None)
    monkeypatch.setattr(postgres_backup, "run_pg_tool", fake_run)

    postgres_backup.verify_pg_dump_archive(archive)

    assert any(command[:3] == ["docker", "compose", "-f"] and "cp" in command for command in calls)
    assert any("pg_restore" in command and "--list" in command for command in calls)
    assert any(command[-3:] == ["rm", "-f", f"/tmp/{archive.name}"] for command in calls)


def test_legacy_orphan_analysis_counts_distinct_rows_and_sanitizes_content(tmp_path: Path):
    database = tmp_path / "legacy.db"
    _orphan_sqlite(database, include_second_fk=True)

    report = analyze_legacy_orphans(database)
    rendered = json.dumps(report)

    assert report["openedReadOnly"] is True
    assert report["summary"]["orphanViolations"] == 2
    assert report["summary"]["distinctAffectedRows"] == 1
    assert report["sourceProof"]["sha256Matches"] is True
    assert "person@example.test" not in rendered
    assert "private message" not in rendered
    assert report["relations"][0]["affectedIdentifierHashes"]


def test_remediation_plan_requires_review_and_no_placeholder_parent(tmp_path: Path):
    database = tmp_path / "legacy.db"
    _orphan_sqlite(database)
    analysis = analyze_legacy_orphans(database)

    plan = write_remediation_plan(analysis, tmp_path / "plan.json")

    assert plan["policy"]["createPlaceholderParentsAutomatically"] is False
    assert plan["policy"]["legacyDatabaseModificationAuthorized"] is False
    assert all(item["approvedForSimulation"] is False for item in plan["items"])
    assert "create-placeholder-parent" not in json.dumps(plan)


def test_sqlite_to_postgres_dry_run_blocks_orphan_source_before_target(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    database = tmp_path / "legacy.db"
    _orphan_sqlite(database)
    monkeypatch.setenv(
        "TEST_MIGRATION_DATABASE_URL",
        "postgresql+psycopg2://organicai:placeholder@127.0.0.1:55432/organicai_task11_migration",
    )
    get_settings.cache_clear()
    try:
        report = migrate_sqlite_to_postgres(database, "TEST_MIGRATION_DATABASE_URL", apply=False)
    finally:
        get_settings.cache_clear()

    assert report["status"] == "blocked"
    assert report["blockReason"] == "SOURCE_FOREIGN_KEY_ORPHANS"
    assert report["source"]["openedReadOnly"] is True
    assert report["target"]["dialect"] == "postgresql"


def test_repair_simulation_cli_copies_only_and_leaves_original_unchanged(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    database = tmp_path / "legacy.db"
    _orphan_sqlite(database)
    analysis = analyze_legacy_orphans(database)
    plan = write_remediation_plan(analysis, tmp_path / "plan.json")
    copy_path = tmp_path / "copy.db"
    output = tmp_path / "simulation.json"
    before = database.read_bytes()

    from app.scripts.simulate_legacy_repair import main as simulate_main

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "simulate_legacy_repair",
            "--source",
            str(database),
            "--plan",
            plan["reportPath"],
            "--copy",
            str(copy_path),
            "--output",
            str(output),
        ],
    )

    assert simulate_main() == 0
    assert database.read_bytes() == before
    assert copy_path.exists()
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["sourceOriginalUnchanged"] is True
    assert result["approvedActionsFound"] == 0
