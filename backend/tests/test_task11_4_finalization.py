from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services import postgres_backup
from app.services.task11_4_finalization import (
    FINAL_DATABASE_NAME,
    build_local_postgres_url,
    load_env_file,
    validate_final_database_name,
    write_runtime_configuration_change,
)


def test_task11_4_final_database_name_allowlist():
    assert validate_final_database_name(FINAL_DATABASE_NAME) == FINAL_DATABASE_NAME
    with pytest.raises(ValueError):
        validate_final_database_name("organicai_task11_clean_legacy")
    with pytest.raises(ValueError):
        validate_final_database_name("organicai_app;drop")


def test_task11_4_env_loader_builds_url_without_reporting_secret(tmp_path: Path):
    env_file = tmp_path / ".env.postgres-test"
    env_file.write_text(
        "POSTGRES_USER=organicai\nPOSTGRES_PASSWORD=local-secret\nPOSTGRES_PORT=55432\n",
        encoding="utf-8",
    )

    values = load_env_file(env_file)
    url = build_local_postgres_url(env_file, FINAL_DATABASE_NAME)

    assert values["POSTGRES_PASSWORD"] == "local-secret"
    assert "organicai_app" in url
    assert "local-secret" in url


def test_task11_4_runtime_config_change_creates_backup_and_sanitized_report(tmp_path: Path):
    env_file = tmp_path / ".env.postgres-test"
    env_file.write_text(
        "POSTGRES_USER=organicai\nPOSTGRES_PASSWORD=local-secret\nPOSTGRES_PORT=55432\n",
        encoding="utf-8",
    )
    runtime_env = tmp_path / ".env"
    runtime_env.write_text("DATABASE_URL=sqlite:///./organicai.db\nAPP_ENV=development\n", encoding="utf-8")
    backup_env = tmp_path / ".env.pre-task11-4"
    report_path = tmp_path / "runtime-report.json"

    report = write_runtime_configuration_change(
        env_path=runtime_env,
        env_backup_path=backup_env,
        env_file=env_file,
        output_path=report_path,
        mode="postgresql",
    )

    assert backup_env.exists()
    assert report["previousDialect"] == "sqlite"
    assert report["newDialect"] == "postgresql"
    rendered = json.dumps(report) + report_path.read_text(encoding="utf-8")
    assert "local-secret" not in rendered
    assert "postgresql://" not in rendered
    assert "DATABASE_URL" not in rendered


def test_postgres_backup_prefix_is_validated(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(postgres_backup, "resolve_backend_path", lambda value: Path(value).resolve())
    with pytest.raises(ValueError):
        postgres_backup.backup_postgres_database(
            "postgresql+psycopg2://user:secret@example.test/db",
            tmp_path,
            prefix="bad/name",
        )
