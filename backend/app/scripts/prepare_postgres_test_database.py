from __future__ import annotations

import argparse
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL, make_url
from sqlalchemy.exc import ArgumentError, SQLAlchemyError

from app.database import Base, import_models
from app.db.migration_status import alembic_config
from app.db.url import redact_database_url


PROTECTED_DATABASE_NAMES = {
    "organicai_app",
    "organicai_staging",
    "organicai_staging_restore_validation",
    "organicai_task11",
    "organicai_task11_migration",
    "organicai_task11_restore",
    "postgres",
    "template0",
    "template1",
}
DISPOSABLE_DATABASE_TOKENS = ("_test", "test_", "_task", "_validation")
DEFAULT_TEST_DATABASE_NAME = "organicai_task13b03_test"
DEFAULT_STATEMENT_TIMEOUT_MS = 30_000
DEFAULT_LOCK_TIMEOUT_MS = 5_000
DEFAULT_IDLE_IN_TRANSACTION_TIMEOUT_MS = 30_000
APPLICATION_NAME_PREFIX = "organicai-pgtest"
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")


class PostgresTestDatabaseError(RuntimeError):
    pass


@dataclass(frozen=True)
class PostgresTestDatabaseTarget:
    url: URL
    database_name: str
    redacted_url: str


def _application_name(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")
    return (clean or APPLICATION_NAME_PREFIX)[:63]


def _timeout_options(
    *,
    statement_timeout_ms: int = DEFAULT_STATEMENT_TIMEOUT_MS,
    lock_timeout_ms: int = DEFAULT_LOCK_TIMEOUT_MS,
    idle_in_transaction_timeout_ms: int = DEFAULT_IDLE_IN_TRANSACTION_TIMEOUT_MS,
) -> str:
    values = [
        ("statement_timeout", statement_timeout_ms),
        ("lock_timeout", lock_timeout_ms),
        ("idle_in_transaction_session_timeout", idle_in_transaction_timeout_ms),
    ]
    return " ".join(f"-c {name}={int(value)}" for name, value in values if int(value) > 0)


def render_connection_url(url: URL) -> str:
    return url.render_as_string(hide_password=False)


def parse_postgres_test_database_url(database_url: str | URL) -> URL:
    if isinstance(database_url, URL):
        url = database_url
        if not url.database:
            raise PostgresTestDatabaseError("PostgreSQL test database URL must include a database name.")
        if url.get_backend_name() not in {"postgresql", "postgres"}:
            raise PostgresTestDatabaseError("PostgreSQL test database URL must use the PostgreSQL dialect.")
        return url
    if not str(database_url or "").strip():
        raise PostgresTestDatabaseError("PostgreSQL test database URL is missing.")
    try:
        url = make_url(database_url)
    except ArgumentError as exc:
        raise PostgresTestDatabaseError("PostgreSQL test database URL is malformed.") from exc
    if url.get_backend_name() not in {"postgresql", "postgres"}:
        raise PostgresTestDatabaseError("PostgreSQL test database URL must use the PostgreSQL dialect.")
    if not url.database:
        raise PostgresTestDatabaseError("PostgreSQL test database URL must include a database name.")
    return url


def is_disposable_database_name(database_name: str) -> bool:
    name = str(database_name or "").strip()
    lowered = name.lower()
    return (
        bool(name)
        and lowered not in PROTECTED_DATABASE_NAMES
        and bool(IDENTIFIER_RE.fullmatch(name))
        and any(token in lowered for token in DISPOSABLE_DATABASE_TOKENS)
    )


def assert_disposable_database_name(database_name: str) -> None:
    name = str(database_name or "").strip()
    lowered = name.lower()
    if lowered in PROTECTED_DATABASE_NAMES:
        raise PostgresTestDatabaseError(f"Refusing to reset protected database name: {name}.")
    if not IDENTIFIER_RE.fullmatch(name):
        raise PostgresTestDatabaseError("PostgreSQL test database name must be an unquoted identifier.")
    if not any(token in lowered for token in DISPOSABLE_DATABASE_TOKENS):
        raise PostgresTestDatabaseError("PostgreSQL test database name must be clearly disposable.")


def target_from_url(database_url: str | URL, *, database_name: str | None = None) -> PostgresTestDatabaseTarget:
    url = parse_postgres_test_database_url(database_url)
    if database_name:
        assert_disposable_database_name(database_name)
        url = url.set(database=database_name)
    database = str(url.database or "")
    assert_disposable_database_name(database)
    return PostgresTestDatabaseTarget(
        url=url,
        database_name=database,
        redacted_url=redact_database_url(render_connection_url(url)),
    )


def url_with_database(database_url: str | URL, database_name: str) -> str:
    assert_disposable_database_name(database_name)
    url = make_url(database_url) if isinstance(database_url, str) else database_url
    return render_connection_url(url.set(database=database_name))


def maintenance_url(target_url: URL) -> URL:
    return target_url.set(database="postgres")


def create_postgres_test_engine(
    database_url: str | URL,
    *,
    application_name: str = APPLICATION_NAME_PREFIX,
) -> Engine:
    target = target_from_url(database_url)
    return create_engine(
        target.url,
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=0,
        pool_timeout=10,
        pool_recycle=300,
        pool_reset_on_return="rollback",
        connect_args={
            "connect_timeout": 10,
            "application_name": _application_name(application_name),
            "options": _timeout_options(),
        },
    )


def create_admin_engine(database_url: str | URL, *, application_name: str = f"{APPLICATION_NAME_PREFIX}-admin") -> Engine:
    url = make_url(database_url) if isinstance(database_url, str) else database_url
    return create_engine(
        url,
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=0,
        pool_timeout=10,
        pool_reset_on_return="rollback",
        connect_args={
            "connect_timeout": 10,
            "application_name": _application_name(application_name),
            "options": _timeout_options(),
        },
    )


def _quoted_identifier(database_name: str) -> str:
    assert_disposable_database_name(database_name)
    return f'"{database_name}"'


def terminate_database_sessions(target: PostgresTestDatabaseTarget) -> int:
    admin = create_admin_engine(maintenance_url(target.url), application_name=f"{APPLICATION_NAME_PREFIX}-terminator")
    try:
        with admin.begin() as connection:
            rows = connection.execute(
                text(
                    """
                    select pg_terminate_backend(pid)
                    from pg_stat_activity
                    where datname = :database_name
                      and pid <> pg_backend_pid()
                    """
                ),
                {"database_name": target.database_name},
            ).all()
            return sum(1 for (terminated,) in rows if terminated)
    finally:
        admin.dispose()


def recreate_database(target: PostgresTestDatabaseTarget) -> dict[str, Any]:
    terminated = terminate_database_sessions(target)
    admin = create_admin_engine(maintenance_url(target.url), application_name=f"{APPLICATION_NAME_PREFIX}-recreate")
    try:
        with admin.begin() as connection:
            name = _quoted_identifier(target.database_name)
            connection.execute(text(f"DROP DATABASE IF EXISTS {name}"))
            connection.execute(text(f"CREATE DATABASE {name}"))
    finally:
        admin.dispose()
    return {"database": target.database_name, "terminatedSessions": terminated, "recreated": True}


def reset_public_schema(database_url: str | URL) -> None:
    target = target_from_url(database_url)
    engine = create_admin_engine(target.url, application_name=f"{APPLICATION_NAME_PREFIX}-schema-reset")
    try:
        with engine.begin() as connection:
            connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            connection.execute(text("CREATE SCHEMA public"))
            connection.execute(text("GRANT ALL ON SCHEMA public TO public"))
    finally:
        engine.dispose()


def upgrade_to_head(database_url: str | URL) -> dict[str, Any]:
    target = target_from_url(database_url)
    config = alembic_config()
    config.set_main_option("sqlalchemy.url", render_connection_url(target.url))
    start = time.monotonic()
    command.upgrade(config, "head")
    return {"upgradedTo": get_alembic_head(database_url), "durationSeconds": round(time.monotonic() - start, 3)}


def upgrade_to_revision(database_url: str | URL, revision: str) -> dict[str, Any]:
    target = target_from_url(database_url)
    config = alembic_config()
    config.set_main_option("sqlalchemy.url", render_connection_url(target.url))
    start = time.monotonic()
    command.upgrade(config, revision)
    return {"upgradedTo": revision, "durationSeconds": round(time.monotonic() - start, 3)}


def downgrade_to_revision(database_url: str | URL, revision: str) -> dict[str, Any]:
    target = target_from_url(database_url)
    config = alembic_config()
    config.set_main_option("sqlalchemy.url", render_connection_url(target.url))
    start = time.monotonic()
    command.downgrade(config, revision)
    return {"downgradedTo": revision, "durationSeconds": round(time.monotonic() - start, 3)}


def get_alembic_head(database_url: str | URL | None = None) -> str | None:
    settings_config = alembic_config()
    if database_url:
        url = make_url(database_url) if isinstance(database_url, str) else database_url
        settings_config.set_main_option("sqlalchemy.url", render_connection_url(url))
    script = ScriptDirectory.from_config(settings_config)
    heads = script.get_heads()
    return heads[0] if len(heads) == 1 else None


def get_current_revision(database_url: str | URL) -> str | None:
    engine = create_postgres_test_engine(database_url, application_name=f"{APPLICATION_NAME_PREFIX}-revision")
    try:
        with engine.connect() as connection:
            return MigrationContext.configure(connection).get_current_revision()
    finally:
        engine.dispose()


def schema_drift(database_url: str | URL) -> list[str]:
    import_models()
    engine = create_postgres_test_engine(database_url, application_name=f"{APPLICATION_NAME_PREFIX}-schema-drift")
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            return [str(item) for item in compare_metadata(context, Base.metadata)]
    finally:
        engine.dispose()


def collect_connection_lifecycle(database_url: str | URL) -> dict[str, Any]:
    target = target_from_url(database_url)
    engine = create_postgres_test_engine(target.url, application_name=f"{APPLICATION_NAME_PREFIX}-diagnostics")
    try:
        with engine.connect() as connection:
            activity = connection.execute(
                text(
                    """
                    select state, wait_event_type, wait_event, count(*)::int
                    from pg_stat_activity
                    where datname = current_database()
                      and pid <> pg_backend_pid()
                    group by state, wait_event_type, wait_event
                    order by state nulls last, wait_event_type nulls last, wait_event nulls last
                    """
                )
            ).mappings().all()
            test_activity_count = connection.execute(
                text(
                    """
                    select count(*)::int
                    from pg_stat_activity
                    where datname = current_database()
                      and pid <> pg_backend_pid()
                      and application_name like :prefix
                    """
                ),
                {"prefix": f"{APPLICATION_NAME_PREFIX}%"},
            ).scalar_one()
            advisory_locks = connection.execute(
                text(
                    """
                    select count(*)::int
                    from pg_locks locks
                    join pg_stat_activity activity on activity.pid = locks.pid
                    where activity.datname = current_database()
                      and locks.locktype = 'advisory'
                    """
                )
            ).scalar_one()
            table_locks = connection.execute(
                text(
                    """
                    select locktype, mode, granted, count(*)::int
                    from pg_locks locks
                    join pg_stat_activity activity on activity.pid = locks.pid
                    where activity.datname = current_database()
                      and locks.locktype in ('relation', 'transactionid', 'tuple', 'advisory')
                    group by locktype, mode, granted
                    order by locktype, mode, granted
                    """
                )
            ).mappings().all()
            unfinished_jobs = 0
            table_exists = connection.execute(text("select to_regclass('public.operational_job_runs')")).scalar_one()
            if table_exists:
                unfinished_jobs = connection.execute(
                    text(
                        """
                        select count(*)::int
                        from operational_job_runs
                        where job_type = 'synthetic_validation'
                          and status in ('queued', 'running', 'processing')
                        """
                    )
                ).scalar_one()
        pool = engine.pool
        checked_out = pool.checkedout() if hasattr(pool, "checkedout") else None
        checked_in = pool.checkedin() if hasattr(pool, "checkedin") else None
        size = pool.size() if hasattr(pool, "size") else None
        overflow = pool.overflow() if hasattr(pool, "overflow") else None
        return {
            "databaseName": target.database_name,
            "activity": [dict(row) for row in activity],
            "testActivityCount": int(test_activity_count),
            "advisoryLocks": int(advisory_locks),
            "tableLocks": [dict(row) for row in table_locks],
            "unfinishedSyntheticJobs": int(unfinished_jobs),
            "pool": {
                "checkedOut": checked_out,
                "checkedIn": checked_in,
                "size": size,
                "overflow": overflow,
                "invalidated": 0,
            },
        }
    finally:
        engine.dispose()


def assert_no_connection_or_worker_leak(database_url: str | URL) -> dict[str, Any]:
    diagnostics = collect_connection_lifecycle(database_url)
    active_test_connections = diagnostics["testActivityCount"]
    unfinished_jobs = diagnostics["unfinishedSyntheticJobs"]
    advisory_locks = diagnostics["advisoryLocks"]
    if active_test_connections or unfinished_jobs or advisory_locks:
        raise AssertionError(
            "PostgreSQL test lifecycle leak detected: "
            f"testConnections={active_test_connections}, unfinishedJobs={unfinished_jobs}, advisoryLocks={advisory_locks}"
        )
    return diagnostics


def prepare_postgres_test_database(
    database_url: str,
    *,
    database_name: str | None = DEFAULT_TEST_DATABASE_NAME,
    drop_recreate: bool = True,
    migrate: bool = True,
    validate_schema: bool = True,
    downgrade_reupgrade: bool = False,
) -> dict[str, Any]:
    target = target_from_url(database_url, database_name=database_name)
    report: dict[str, Any] = {
        "databaseName": target.database_name,
        "redactedUrl": target.redacted_url,
        "postgresql": True,
        "protectedNameGuard": "passed",
        "existingApplicationDatabasesAffected": False,
        "sqliteFallback": False,
        "operations": [],
    }
    if drop_recreate:
        report["operations"].append(recreate_database(target))
    if migrate:
        report["operations"].append(upgrade_to_head(render_connection_url(target.url)))
    report["alembicHead"] = get_alembic_head(target.url)
    report["currentRevision"] = get_current_revision(render_connection_url(target.url))
    report["schemaCurrent"] = report["alembicHead"] == report["currentRevision"]
    if validate_schema:
        drift = schema_drift(render_connection_url(target.url))
        report["schemaDrift"] = drift
        report["schemaDriftCount"] = len(drift)
    if downgrade_reupgrade:
        report["downgrade"] = downgrade_to_revision(
            render_connection_url(target.url),
            "0003_privacy_data_lifecycle",
        )
        report["revisionAfterDowngrade"] = get_current_revision(render_connection_url(target.url))
        report["reupgrade"] = upgrade_to_head(render_connection_url(target.url))
        report["revisionAfterReupgrade"] = get_current_revision(render_connection_url(target.url))
    report["connectionLifecycle"] = collect_connection_lifecycle(render_connection_url(target.url))
    return report


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# PostgreSQL Test Database Preparation",
        "",
        f"- Database name: `{report.get('databaseName')}`",
        f"- Redacted URL: `{report.get('redactedUrl')}`",
        f"- PostgreSQL: `{report.get('postgresql')}`",
        f"- Protected-name guard: `{report.get('protectedNameGuard')}`",
        f"- Existing application databases affected: `{report.get('existingApplicationDatabasesAffected')}`",
        f"- SQLite fallback: `{report.get('sqliteFallback')}`",
        f"- Alembic head: `{report.get('alembicHead')}`",
        f"- Current revision: `{report.get('currentRevision')}`",
        f"- Schema current: `{report.get('schemaCurrent')}`",
        f"- Schema drift count: `{report.get('schemaDriftCount', 'not-run')}`",
        "",
        "## Operations",
    ]
    for operation in report.get("operations", []):
        lines.append(f"- `{json.dumps(operation, sort_keys=True)}`")
    if "downgrade" in report:
        lines.extend(
            [
                "",
                "## Downgrade/Re-upgrade",
                f"- Downgrade: `{report['downgrade']}`",
                f"- Revision after downgrade: `{report.get('revisionAfterDowngrade')}`",
                f"- Re-upgrade: `{report['reupgrade']}`",
                f"- Revision after re-upgrade: `{report.get('revisionAfterReupgrade')}`",
            ]
        )
    lines.extend(["", "## Sanitization", "- Credentials and complete database URLs are not included."])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare an isolated PostgreSQL database for test validation.")
    parser.add_argument("--database-url-env", default="TEST_POSTGRES_DATABASE_URL")
    parser.add_argument("--database-url", default="")
    parser.add_argument("--database-name", default=DEFAULT_TEST_DATABASE_NAME)
    parser.add_argument("--no-drop-recreate", action="store_true")
    parser.add_argument("--no-migrate", action="store_true")
    parser.add_argument("--validate-schema", action="store_true")
    parser.add_argument("--downgrade-reupgrade", action="store_true")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    database_url = args.database_url or os.environ.get(args.database_url_env, "")
    try:
        report = prepare_postgres_test_database(
            database_url,
            database_name=args.database_name,
            drop_recreate=not args.no_drop_recreate,
            migrate=not args.no_migrate,
            validate_schema=args.validate_schema,
            downgrade_reupgrade=args.downgrade_reupgrade,
        )
    except (PostgresTestDatabaseError, SQLAlchemyError) as exc:
        print(json.dumps({"status": "failed", "error": exc.__class__.__name__, "message": str(exc)}, sort_keys=True))
        return 1

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown_report(report), encoding="utf-8")
    print(json.dumps({"status": "passed", **report}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
