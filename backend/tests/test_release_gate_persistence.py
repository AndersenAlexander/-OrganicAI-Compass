from __future__ import annotations

import hashlib
import os
import sqlite3
import subprocess
import sys
from datetime import datetime
from app.core.time import utc_now_naive
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, delete, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.database import Base, create_database_engine, create_session_factory, import_models
from app.db.url import parse_database_url, redact_database_url
from app.models.conversation import Conversation
from app.models.diagnostic import Diagnostic
from app.models.market_application import JobAnalysis, JobRequirement
from app.models.message import Message
from app.models.provider_operations import OperationalJobRun
from app.models.profile import Profile
from app.models.user import User
from app.scripts.prepare_postgres_test_database import (
    assert_no_connection_or_worker_leak,
    create_postgres_test_engine,
    get_alembic_head,
    prepare_postgres_test_database,
    render_connection_url,
    schema_drift,
    upgrade_to_head,
    upgrade_to_revision,
)
from app.services.career_resilience_engine import sync_career_resilience_catalogue
from app.services.database_integrity import verify_database_integrity
from app.services.database_inventory import inventory_database
from app.services.runtime_configuration import check_runtime_configuration
from app.services.sqlite_backup import backup_sqlite_database


HISTORICAL_0009_NORMALIZED_SHA256 = "2cf795c3de99281896d13b550ff3e6de3463f8a67aee9e7f49ff985262995071"


def test_historical_0009_migration_is_immutable():
    migration = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "0009_collaboration_traceability_extensions.py"
    normalized = migration.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert hashlib.sha256(normalized.encode("utf-8")).hexdigest() == HISTORICAL_0009_NORMALIZED_SHA256


def test_sqlite_engine_and_session_rollback(tmp_path: Path):
    settings = Settings(_env_file=None, app_env="test", database_url=f"sqlite:///{tmp_path / 'test.db'}")
    engine = create_database_engine(settings)
    factory = create_session_factory(engine)
    import_models()
    Base.metadata.create_all(engine)
    with factory() as session:
        session.execute(text("create table rollback_probe (id integer primary key, value text)"))
        session.commit()
    with factory() as session:
        session.execute(text("insert into rollback_probe (value) values ('x')"))
        session.rollback()
    with engine.connect() as connection:
        assert connection.execute(text("select count(*) from rollback_probe")).scalar_one() == 0
        assert connection.exec_driver_sql("PRAGMA journal_mode").scalar_one() == "wal"
        assert connection.exec_driver_sql("PRAGMA busy_timeout").scalar_one() == settings.db_connect_timeout_seconds * 1000
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
    engine.dispose()


def test_sqlite_wal_allows_login_style_write_while_reader_is_open(tmp_path: Path):
    database_path = tmp_path / "wal-concurrency.db"
    settings = Settings(_env_file=None, app_env="test", database_url=f"sqlite:///{database_path}")
    engine = create_database_engine(settings)
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE login_probe (id INTEGER PRIMARY KEY, value TEXT)")
        connection.exec_driver_sql("INSERT INTO login_probe (value) VALUES ('existing')")

    reader = sqlite3.connect(database_path, timeout=5)
    try:
        reader.execute("BEGIN")
        assert reader.execute("SELECT COUNT(*) FROM login_probe").fetchone()[0] == 1
        with engine.begin() as writer:
            writer.exec_driver_sql("INSERT INTO login_probe (value) VALUES ('new session')")
        assert reader.execute("SELECT COUNT(*) FROM login_probe").fetchone()[0] == 1
    finally:
        reader.rollback()
        reader.close()

    with engine.connect() as connection:
        assert connection.exec_driver_sql("SELECT COUNT(*) FROM login_probe").scalar_one() == 2
    engine.dispose()


def test_runtime_configuration_production_requires_postgres():
    settings = Settings(
        _env_file=None,
        app_env="production",
        secret_key="x" * 40,
        database_url="sqlite:///./organicai.db",
        allowed_origins="https://organicai.example",
        allowed_hosts="organicai.example",
        public_backend_url="https://api.organicai.example",
    )
    report = check_runtime_configuration(settings)
    assert report.ready is False
    assert any(check.key == "DATABASE_URL" and check.status == "error" for check in report.checks)


def test_database_url_redaction_and_pool_config():
    rendered = redact_database_url("postgresql+psycopg2://user:secret@example.test:5432/organicai")
    assert "secret" not in rendered
    assert "user" in rendered
    parsed = parse_database_url("postgresql+psycopg2://user:secret@example.test:5432/organicai")
    assert parsed.dialect == "postgresql"
    assert parsed.host_configured is True
    assert parsed.database_configured is True


def test_sqlite_inventory_integrity_and_backup(tmp_path: Path):
    database = tmp_path / "inventory.db"
    engine = create_engine(f"sqlite:///{database}")
    import_models()
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                "insert into users (id, name, email, hashed_password, is_demo, created_at, updated_at) "
                "values ('u1', 'User', 'u@example.test', 'hash', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            )
        )
    engine.dispose()

    inventory = inventory_database(f"sqlite:///{database}")
    assert inventory["dialect"] == "sqlite"
    assert any(table["name"] == "users" and table["rowCount"] == 1 for table in inventory["tables"])
    integrity = verify_database_integrity(f"sqlite:///{database}")
    assert integrity["status"] in {"passed", "failed"}

    result = backup_sqlite_database(database, tmp_path / "backups", "test")
    assert Path(result["backupPath"]).exists()
    assert result["manifest"]["sha256"]
    assert result["manifest"]["verification"]["integrityCheck"] == "ok"


@pytest.mark.postgres
def test_postgres_url_available_for_optional_real_tests(postgres_database_url: str):
    parsed = parse_database_url(postgres_database_url)
    assert parsed.dialect in {"postgresql", "postgres"}


@pytest.mark.postgres
def test_postgres_historical_0009_state_converges_through_forward_migrations(postgres_database_url: str):
    database_url = postgres_database_url
    prepare_postgres_test_database(
        database_url,
        database_name=None,
        drop_recreate=True,
        migrate=False,
        validate_schema=False,
        downgrade_reupgrade=False,
    )
    upgrade_to_revision(database_url, "0010_alembic_version_capacity")

    engine = create_postgres_test_engine(database_url, application_name="organicai-pgtest-historical-0009")
    try:
        inspector = inspect(engine)
        assert "ix_browser_job_captures_analysis_version" in {item["name"] for item in inspector.get_indexes("browser_job_captures")}
        assert "ix_advisor_shares_version_number" in {item["name"] for item in inspector.get_indexes("advisor_shares")}
        assert "ix_advisor_comments_version_number" in {item["name"] for item in inspector.get_indexes("advisor_comments")}
        assert "ix_interviews_requirement_set_version" in {item["name"] for item in inspector.get_indexes("interviews")}
        assert "ix_star_stories_canonical_story_id" not in {item["name"] for item in inspector.get_indexes("star_stories")}

        foreign_keys = {
            table: {
                (tuple(item["constrained_columns"]), item["referred_table"], tuple(item["referred_columns"]))
                for item in inspector.get_foreign_keys(table)
            }
            for table in ("application_recalibration_runs", "career_decision_journal_entries", "job_requirements")
        }
        assert (("interview_id",), "interviews", ("id",)) not in foreign_keys["application_recalibration_runs"]
        assert (("linked_experiment_id",), "career_experiment_sessions", ("id",)) not in foreign_keys["career_decision_journal_entries"]
        assert (("interview_id",), "interviews", ("id",)) not in foreign_keys["career_decision_journal_entries"]
        assert (("confirmed_by",), "users", ("id",)) not in foreign_keys["job_requirements"]
        extraction_column = next(item for item in inspector.get_columns("job_requirements") if item["name"] == "extraction_timestamp")
        assert extraction_column["nullable"] is True

        with Session(engine) as session:
            session.add(JobAnalysis(id="historical-analysis", profile_id="historical-profile"))
            session.add(
                JobRequirement(
                    id="historical-requirement",
                    analysis_id="historical-analysis",
                    profile_id="historical-profile",
                    requirement_text="Historical migration timestamp probe",
                )
            )
            session.commit()
        with engine.begin() as connection:
            connection.execute(
                text("update job_requirements set extraction_timestamp = null where id = 'historical-requirement'")
            )
    finally:
        engine.dispose()

    upgrade_to_head(database_url)

    engine = create_postgres_test_engine(database_url, application_name="organicai-pgtest-converged-0011")
    try:
        inspector = inspect(engine)
        assert "ix_browser_job_captures_analysis_version" not in {item["name"] for item in inspector.get_indexes("browser_job_captures")}
        assert "ix_advisor_shares_version_number" not in {item["name"] for item in inspector.get_indexes("advisor_shares")}
        assert "ix_advisor_comments_version_number" not in {item["name"] for item in inspector.get_indexes("advisor_comments")}
        assert "ix_interviews_requirement_set_version" not in {item["name"] for item in inspector.get_indexes("interviews")}
        assert "ix_star_stories_canonical_story_id" in {item["name"] for item in inspector.get_indexes("star_stories")}

        foreign_keys = {
            table: {
                (tuple(item["constrained_columns"]), item["referred_table"], tuple(item["referred_columns"]))
                for item in inspector.get_foreign_keys(table)
            }
            for table in ("application_recalibration_runs", "career_decision_journal_entries", "job_requirements")
        }
        assert (("interview_id",), "interviews", ("id",)) in foreign_keys["application_recalibration_runs"]
        assert (("linked_experiment_id",), "career_experiment_sessions", ("id",)) in foreign_keys["career_decision_journal_entries"]
        assert (("interview_id",), "interviews", ("id",)) in foreign_keys["career_decision_journal_entries"]
        assert (("confirmed_by",), "users", ("id",)) in foreign_keys["job_requirements"]
        extraction_column = next(item for item in inspector.get_columns("job_requirements") if item["name"] == "extraction_timestamp")
        assert extraction_column["nullable"] is False
        version_column = next(item for item in inspector.get_columns("alembic_version") if item["name"] == "version_num")
        assert version_column["type"].length == 128

        with engine.connect() as connection:
            migration_context = MigrationContext.configure(connection)
            assert migration_context.get_current_revision() == get_alembic_head(database_url)
            assert compare_metadata(migration_context, Base.metadata) == []
            assert connection.execute(
                text("select extraction_timestamp is not null from job_requirements where id = 'historical-requirement'")
            ).scalar_one() is True
    finally:
        engine.dispose()

    assert schema_drift(database_url) == []
    assert_no_connection_or_worker_leak(database_url)


@pytest.mark.postgres
def test_postgres_release_gate_core_persistence_behaviors(postgres_test_engine):
    engine = postgres_test_engine
    database_url = render_connection_url(engine.url)
    parsed = parse_database_url(database_url)
    assert parsed.dialect in {"postgresql", "postgres"}

    import_models()
    with engine.connect() as connection:
        migration_context = MigrationContext.configure(connection)
        assert migration_context.get_current_revision() == get_alembic_head(database_url)
        assert compare_metadata(migration_context, Base.metadata) == []
        assert connection.execute(text("select to_regclass('public.user_privacy_settings')")).scalar_one() == "user_privacy_settings"
        assert connection.execute(text("select to_regclass('public.provider_verification_runs')")).scalar_one() == "provider_verification_runs"
        assert connection.execute(text("select to_regclass('public.email_delivery_events')")).scalar_one() == "email_delivery_events"

    integrity = verify_database_integrity(database_url)
    assert integrity["status"] == "passed"

    with Session(engine) as session:
        sync_career_resilience_catalogue(session)
    assert verify_database_integrity(database_url)["status"] == "passed"

    persisted_at = datetime(2026, 7, 27, 12, 0, 0)
    with Session(engine) as session:
        session.add(
            User(
                id="pg-rollback-user",
                name="Rollback User",
                email="pg-rollback@example.test",
                hashed_password="hash",
                is_demo=True,
                created_at=persisted_at,
                updated_at=persisted_at,
            )
        )
        session.flush()
        session.rollback()

    with engine.connect() as connection:
        rollback_count = connection.execute(text("select count(*) from users where id = 'pg-rollback-user'")).scalar_one()
    assert rollback_count == 0

    with Session(engine) as session:
        user = User(
            id="pg-user-001",
            name="PostgreSQL User",
            email="pg-user@example.test",
            hashed_password="hash",
            is_demo=True,
            demo_dataset_version=112,
            created_at=persisted_at,
            updated_at=persisted_at,
        )
        diagnostic = Diagnostic(
            id="pg-diagnostic-001",
            user_id=user.id,
            payload={
                "english": "AI collaboration",
                "romanian": "Invatare responsabila",
                "norwegian": "laeringsplan",
                "unicode": {"romanian": "invatare", "norwegian": "laeringsplan"},
                "active": True,
                "empty": "",
                "nullable": None,
            },
            created_at=persisted_at,
        )
        profile = Profile(
            id="pg-profile-001",
            user_id=user.id,
            diagnostic_id=diagnostic.id,
            data={"strengths": ["systems thinking"], "ready": True},
            created_at=persisted_at,
        )
        conversation = Conversation(
            id="pg-conversation-001",
            user_id=user.id,
            profile_id=profile.id,
            title="PostgreSQL persistence smoke",
            created_at=persisted_at,
            updated_at=persisted_at,
        )
        message = Message(
            id="pg-message-001",
            conversation_id=conversation.id,
            role="user",
            content="Persist this synthetic message.",
            input_mode="text",
            audio_url=None,
            created_at=persisted_at,
        )
        session.add_all([user, diagnostic, profile, conversation, message])
        session.commit()

    with Session(engine) as session:
        diagnostic = session.get(Diagnostic, "pg-diagnostic-001")
        user = session.get(User, "pg-user-001")
        message = session.get(Message, "pg-message-001")
        assert diagnostic is not None
        assert user is not None
        assert message is not None
        assert diagnostic.payload["unicode"]["romanian"] == "invatare"
        assert diagnostic.payload["unicode"]["norwegian"] == "laeringsplan"
        assert diagnostic.payload["active"] is True
        assert diagnostic.payload["empty"] == ""
        assert diagnostic.payload["nullable"] is None
        assert user.is_demo is True
        assert user.created_at == persisted_at
        assert message.conversation_id == "pg-conversation-001"

    with Session(engine) as session:
        session.add(
            User(
                id="pg-user-duplicate",
                name="Duplicate User",
                email="pg-user@example.test",
                hashed_password="hash",
                created_at=persisted_at,
                updated_at=persisted_at,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    with Session(engine) as session:
        session.add(
            Message(
                id="pg-message-invalid-fk",
                conversation_id="missing-conversation",
                role="user",
                content="This row must fail.",
                created_at=persisted_at,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


@pytest.mark.postgres
def test_postgres_operational_job_skip_locked_prevents_duplicate_acquisition(postgres_test_engine):
    engine = postgres_test_engine
    parsed = parse_database_url(render_connection_url(engine.url))
    assert parsed.dialect in {"postgresql", "postgres"}
    now = utc_now_naive()
    with Session(engine) as session:
        session.add_all(
            [
                OperationalJobRun(
                    job_type="synthetic_validation",
                    status="queued",
                    started_at=now,
                    failure_summary_json={"validation": True},
                ),
                OperationalJobRun(
                    job_type="synthetic_validation",
                    status="queued",
                    started_at=now,
                    failure_summary_json={"validation": True},
                ),
            ]
        )
        session.commit()

    first = Session(engine)
    second = Session(engine)
    try:
        first.begin()
        first_job = first.scalar(
            select(OperationalJobRun)
            .where(OperationalJobRun.job_type == "synthetic_validation", OperationalJobRun.status == "queued")
            .order_by(OperationalJobRun.started_at.asc())
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        assert first_job is not None
        first_job.status = "processing"

        second.begin()
        second_job = second.scalar(
            select(OperationalJobRun)
            .where(OperationalJobRun.job_type == "synthetic_validation", OperationalJobRun.status == "queued")
            .order_by(OperationalJobRun.started_at.asc())
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        assert second_job is not None
        assert second_job.id != first_job.id
        second_job.status = "processing"
        second.commit()
        first.commit()
    finally:
        first.close()
        second.close()

    with Session(engine) as session:
        session.execute(delete(OperationalJobRun).where(OperationalJobRun.job_type == "synthetic_validation"))
        session.commit()


@pytest.mark.postgres
def test_postgres_behavior_leaves_no_connection_or_worker_leak(prepared_postgres_database_url: str):
    diagnostics = assert_no_connection_or_worker_leak(prepared_postgres_database_url)
    assert diagnostics["pool"]["checkedOut"] == 0
    assert diagnostics["advisoryLocks"] == 0
    assert diagnostics["unfinishedSyntheticJobs"] == 0


@pytest.mark.postgres
def test_postgres_app_lifespan_closes_database_resources(prepared_postgres_database_url: str):
    backend_root = Path(__file__).resolve().parents[1]
    code = (
        "from fastapi.testclient import TestClient\n"
        "import app.config as config\n"
        "config.get_settings.cache_clear()\n"
        "import app.main as main\n"
        "with TestClient(main.app) as client:\n"
        "    response = client.get('/health/live')\n"
        "    print('lifespan-response', response.status_code)\n"
        "print('lifespan-completed')\n"
    )
    env = {
        **os.environ,
        "APP_ENV": "test",
        "DATABASE_URL": prepared_postgres_database_url,
        "DB_AUTO_CREATE_SCHEMA": "false",
        "DB_AUTO_MIGRATE": "false",
        "DB_REQUIRE_MIGRATION_HEAD": "true",
        "DEMO_ACCOUNT_ENABLED": "false",
        "SECRET_KEY": "x" * 40,
        "EMAIL_DELIVERY_DRIVER": "disabled",
        "OPENAI_API_KEY": "disabled",
        "ELEVENLABS_API_KEY": "disabled",
        "DB_STATEMENT_TIMEOUT_MS": "30000",
        "DB_LOCK_TIMEOUT_MS": "5000",
        "DB_IDLE_IN_TRANSACTION_SESSION_TIMEOUT_MS": "30000",
    }
    result = subprocess.run([sys.executable, "-c", code], cwd=backend_root, env=env, text=True, capture_output=True, timeout=60)
    assert result.returncode == 0, result.stderr[-2000:]
    assert "lifespan-response 200" in result.stdout
    assert "lifespan-completed" in result.stdout
    assert result.stdout.count("application_startup_completed") == 1
    assert result.stdout.count("application_shutdown_completed") == 1
    assert result.stdout.count("database_pool_disposed") == 1
    assert_no_connection_or_worker_leak(prepared_postgres_database_url)

