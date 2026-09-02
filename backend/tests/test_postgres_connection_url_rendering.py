from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
from sqlalchemy.engine import URL, make_url

from app.scripts import prepare_postgres_test_database as pgprep


SOURCE_URL = "postgresql+psycopg2://test_user:s3cret-pass@127.0.0.1:55432/source_test"
TARGET_DATABASE = "organicai_task13b03_test"


def test_url_with_database_preserves_password_and_does_not_mask():
    rendered = pgprep.url_with_database(SOURCE_URL, TARGET_DATABASE)
    parsed = make_url(rendered)

    assert "***" not in rendered
    assert parsed.database == TARGET_DATABASE
    assert parsed.username == "test_user"
    assert parsed.password == "s3cret-pass"
    assert parsed.host == "127.0.0.1"
    assert parsed.port == 55432


def test_render_connection_url_keeps_credentials_for_url_object():
    source = make_url(SOURCE_URL)
    rendered = pgprep.render_connection_url(source.set(database=TARGET_DATABASE))

    assert "***" not in rendered
    assert "s3cret-pass" in rendered
    assert make_url(rendered).database == TARGET_DATABASE


def test_create_engine_helpers_receive_connection_capable_url(monkeypatch: pytest.MonkeyPatch):
    captured: list[URL] = []

    class FakeEngine:
        pass

    def fake_create_engine(url, **_kwargs):
        captured.append(url)
        return FakeEngine()

    monkeypatch.setattr(pgprep, "create_engine", fake_create_engine)

    pgprep.create_postgres_test_engine(SOURCE_URL)
    pgprep.create_admin_engine(pgprep.maintenance_url(make_url(SOURCE_URL)))

    assert len(captured) == 2
    assert all(isinstance(url, URL) for url in captured)
    assert [url.password for url in captured] == ["s3cret-pass", "s3cret-pass"]
    assert all("***" not in pgprep.render_connection_url(url) for url in captured)
    assert captured[1].database == "postgres"


def test_alembic_upgrade_and_downgrade_urls_retain_credentials(monkeypatch: pytest.MonkeyPatch):
    configured: list[str] = []

    class FakeConfig:
        def set_main_option(self, key: str, value: str) -> None:
            if key == "sqlalchemy.url":
                configured.append(value)

    monkeypatch.setattr(pgprep, "alembic_config", lambda: FakeConfig())
    monkeypatch.setattr(pgprep.command, "upgrade", lambda _config, _revision: None)
    monkeypatch.setattr(pgprep.command, "downgrade", lambda _config, _revision: None)
    monkeypatch.setattr(pgprep, "get_alembic_head", lambda _database_url=None: "0004_provider_operations")

    pgprep.upgrade_to_head(pgprep.url_with_database(SOURCE_URL, TARGET_DATABASE))
    pgprep.downgrade_to_revision(pgprep.url_with_database(SOURCE_URL, TARGET_DATABASE), "0003_privacy_data_lifecycle")

    assert len(configured) == 2
    assert all("s3cret-pass" in value for value in configured)
    assert all("***" not in value for value in configured)
    assert all(make_url(value).database == TARGET_DATABASE for value in configured)


def test_redacted_diagnostics_do_not_expose_password():
    target = pgprep.target_from_url(SOURCE_URL, database_name=TARGET_DATABASE)
    report = pgprep.markdown_report(
        {
            "databaseName": target.database_name,
            "redactedUrl": target.redacted_url,
            "postgresql": True,
            "protectedNameGuard": "passed",
            "existingApplicationDatabasesAffected": False,
            "sqliteFallback": False,
            "alembicHead": "0004_provider_operations",
            "currentRevision": "0004_provider_operations",
            "schemaCurrent": True,
            "schemaDriftCount": 0,
            "operations": [],
        }
    )

    assert "s3cret-pass" not in target.redacted_url
    assert "s3cret-pass" not in report
    assert "postgresql+psycopg2://test_user:" in target.redacted_url


def test_prepare_powershell_script_rejects_masked_url_before_workflow_continues():
    powershell = shutil.which("powershell.exe") or shutil.which("pwsh")
    if not powershell:
        pytest.skip("PowerShell is not available.")

    project_root = Path(__file__).resolve().parents[2]
    script = project_root / "scripts" / "prepare-postgres-test-database.ps1"
    env = os.environ.copy()
    env["TEST_POSTGRES_DATABASE_URL"] = (
        "postgresql+psycopg2://test_user:***@127.0.0.1:55432/"
        f"{TARGET_DATABASE}"
    )

    result = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            "-DatabaseName",
            TARGET_DATABASE,
        ],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "Refusing to use masked PostgreSQL connection URL" in output
    assert "s3cret-pass" not in output
