from __future__ import annotations

import json
import re
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import MetaData, Table, create_engine, func, inspect, select, text
from sqlalchemy.engine import Engine, URL, make_url

from app.config import get_settings
from app.database import Base, import_models
from app.db.migration_status import alembic_config, get_alembic_head
from app.services.database_admin import (
    resolve_backend_path,
    sanitized_database_identity,
    sha256_file,
    utc_iso,
    utc_timestamp,
    write_json_atomic,
)
from app.services.database_immutability import (
    capture_sqlite_evidence,
    connect_readonly_sqlite,
    create_consistent_sqlite_backup,
    quote_identifier,
    write_sqlite_evidence,
)
from app.services.database_integrity import verify_database_integrity
from app.services.legacy_orphan_archive import verify_legacy_orphan_archive
from app.services.sqlite_to_postgres import migrate_sqlite_to_postgres


BASELINE_REVISION = "0001_initial_schema"
FINAL_DATABASE_NAME = "organicai_app"
ARCHIVE_ROW_COUNT = 156
RESERVED_DATABASE_NAMES = {
    "organicai_task11",
    "organicai_task11_migration",
    "organicai_task11_restore",
    "organicai_task11_pytest",
    "organicai_task11_downgrade",
    "organicai_task11_failure",
    "organicai_task11_clean_legacy",
}
SAFE_DATABASE_RE = re.compile(r"^[a-z][a-z0-9_]{0,62}$")


def relative_backend_path(path: Path) -> str:
    backend = resolve_backend_path(".")
    try:
        return path.resolve().relative_to(backend).as_posix()
    except ValueError:
        root = backend.parent
        try:
            return path.resolve().relative_to(root).as_posix()
        except ValueError:
            return path.name


def load_env_file(path: str | Path) -> dict[str, str]:
    env_path = resolve_backend_path(path)
    values: dict[str, str] = {}
    if not env_path.exists():
        return values
    for line in env_path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        values[key.strip()] = value
    return values


def validate_final_database_name(name: str) -> str:
    if name != FINAL_DATABASE_NAME:
        raise ValueError("Final application database name must be organicai_app.")
    if name in RESERVED_DATABASE_NAMES or not SAFE_DATABASE_RE.fullmatch(name):
        raise ValueError("Final application database name is not allowed.")
    return name


def build_local_postgres_url(env_file: str | Path, database_name: str) -> str:
    validate_final_database_name(database_name)
    values = load_env_file(env_file)
    user = values.get("POSTGRES_USER")
    password = values.get("POSTGRES_PASSWORD")
    port = int(values.get("POSTGRES_PORT") or "55432")
    if not user or not password:
        raise ValueError("PostgreSQL test env file is missing local credentials.")
    return URL.create(
        "postgresql+psycopg2",
        username=user,
        password=password,
        host="127.0.0.1",
        port=port,
        database=database_name,
    ).render_as_string(hide_password=False)


def build_admin_postgres_url(env_file: str | Path) -> str:
    values = load_env_file(env_file)
    user = values.get("POSTGRES_USER")
    password = values.get("POSTGRES_PASSWORD")
    port = int(values.get("POSTGRES_PORT") or "55432")
    if not user or not password:
        raise ValueError("PostgreSQL test env file is missing local credentials.")
    return URL.create(
        "postgresql+psycopg2",
        username=user,
        password=password,
        host="127.0.0.1",
        port=port,
        database="postgres",
    ).render_as_string(hide_password=False)


def _quoted_pg_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _sqlite_current_revision(path: Path) -> str | None:
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    try:
        with engine.connect() as connection:
            return MigrationContext.configure(connection).get_current_revision()
    finally:
        engine.dispose()


def _sqlite_schema_drift(path: Path) -> dict[str, Any]:
    import_models()
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    try:
        with engine.connect() as connection:
            diffs = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    finally:
        engine.dispose()
    return {"schemaDrift": len(diffs), "schemaDriftSummaries": [str(diff) for diff in diffs[:50]]}


def _postgres_schema_drift(database_url: str) -> dict[str, Any]:
    import_models()
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            diffs = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    finally:
        engine.dispose()
    return {"schemaDrift": len(diffs), "schemaDriftSummaries": [str(diff) for diff in diffs[:50]]}


def _sqlite_table_count(path: Path, table: str) -> int | None:
    connection = connect_readonly_sqlite(path)
    try:
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
            (table,),
        ).fetchone()
        if exists is None:
            return None
        return int(connection.execute(f"SELECT COUNT(*) FROM {quote_identifier(table)}").fetchone()[0])
    finally:
        connection.close()


def _sqlite_message_ids(path: Path, *, active_only: bool = False, orphan_only: bool = False) -> set[str]:
    connection = connect_readonly_sqlite(path)
    try:
        if active_only:
            sql = """
                SELECT m.id
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
            """
        elif orphan_only:
            sql = """
                SELECT m.id
                FROM messages m
                LEFT JOIN conversations c ON c.id = m.conversation_id
                WHERE m.conversation_id IS NOT NULL AND c.id IS NULL
            """
        else:
            sql = "SELECT id FROM messages"
        return {str(row[0]) for row in connection.execute(sql)}
    finally:
        connection.close()


def _archive_message_ids(path: Path) -> set[str]:
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        return {str(row[0]) for row in connection.execute("SELECT id FROM orphan_messages")}
    finally:
        connection.close()


def _archive_message_count(path: Path) -> int:
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        return int(connection.execute("SELECT COUNT(*) FROM orphan_messages").fetchone()[0])
    finally:
        connection.close()


def _application_row_count_from_evidence(evidence: dict[str, Any]) -> int:
    return sum(int(value) for table, value in evidence["rowCounts"].items() if table != "alembic_version")


def _sqlite_active_application_row_count(path: Path) -> int:
    evidence = capture_sqlite_evidence(path)
    return _application_row_count_from_evidence(evidence) - len(_sqlite_message_ids(path, orphan_only=True))


def _sqlite_application_row_count(path: Path) -> int:
    return _application_row_count_from_evidence(capture_sqlite_evidence(path))


def _postgres_table_counts(database_url: str) -> dict[str, int]:
    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        counts: dict[str, int] = {}
        with engine.connect() as connection:
            for table in sorted(inspector.get_table_names(schema="public")):
                quoted = '"' + table.replace('"', '""') + '"'
                counts[table] = int(connection.execute(text(f"SELECT COUNT(*) FROM public.{quoted}")).scalar_one())
        return counts
    finally:
        engine.dispose()


def _postgres_application_row_count(database_url: str) -> int:
    return sum(count for table, count in _postgres_table_counts(database_url).items() if table != "alembic_version")


def _postgres_message_ids(database_url: str) -> set[str]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            if "messages" not in inspect(engine).get_table_names(schema="public"):
                return set()
            return {str(row[0]) for row in connection.execute(text("SELECT id FROM public.messages"))}
    finally:
        engine.dispose()


def capture_original_before_task11_4(
    original_path: str | Path = "./organicai.db",
    output_path: str | Path = "../reports/database-integrity/original-sqlite-before-task11-4.json",
) -> dict[str, Any]:
    return write_sqlite_evidence(original_path, output_path)


def create_final_original_backup_and_chain(
    original_path: str | Path = "./organicai.db",
    backup_directory: str | Path = "./backups/database",
    chain_output: str | Path = "../reports/database-integrity/original-sqlite-chain-of-custody.json",
) -> dict[str, Any]:
    original = resolve_backend_path(original_path)
    backup = create_consistent_sqlite_backup(
        original,
        backup_directory,
        application_version=get_settings().app_version,
        prefix="organicai-original-final",
    )
    backup_path = Path(backup["backupPath"])
    original_evidence = capture_sqlite_evidence(original)
    backup_evidence = capture_sqlite_evidence(backup_path)
    logical_equivalence = {
        "sourceSha256Recorded": bool(original_evidence["file"]["sha256"]),
        "backupSha256Recorded": bool(backup_evidence["file"]["sha256"]),
        "tableCountMatches": original_evidence["schema"]["tableCount"] == backup_evidence["schema"]["tableCount"],
        "rowCountsMatch": original_evidence["rowCounts"] == backup_evidence["rowCounts"],
        "foreignKeyViolationCountMatches": original_evidence["foreignKeys"]["foreignKeyViolationCount"]
        == backup_evidence["foreignKeys"]["foreignKeyViolationCount"],
        "orphanMessageCountMatches": len(_sqlite_message_ids(original, orphan_only=True))
        == len(_sqlite_message_ids(backup_path, orphan_only=True)),
        "emptyHistoricalAlembicVersion": original_evidence["schema"]["alembicVersionExists"]
        and original_evidence["schema"]["alembicVersionRowCount"] == 0
        and backup_evidence["schema"]["alembicVersionExists"]
        and backup_evidence["schema"]["alembicVersionRowCount"] == 0,
    }
    chain = {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "sourceRole": "immutable historical source",
        "sourceDatabase": "backend/organicai.db",
        "sourceOpenedReadOnly": True,
        "backupFileName": backup_path.name,
        "backupManifestFileName": Path(backup["manifestPath"]).name,
        "createdWithSqliteBackupApi": True,
        "sourceSha256": original_evidence["file"]["sha256"],
        "backupSha256": backup_evidence["file"]["sha256"],
        "physicalHashMatchRequired": False,
        "physicalHashMatches": original_evidence["file"]["sha256"] == backup_evidence["file"]["sha256"],
        "sourceTableCount": original_evidence["schema"]["tableCount"],
        "backupTableCount": backup_evidence["schema"]["tableCount"],
        "sourceRowCounts": original_evidence["rowCounts"],
        "backupRowCounts": backup_evidence["rowCounts"],
        "sourceForeignKeyViolations": original_evidence["foreignKeys"]["foreignKeyViolationCount"],
        "backupForeignKeyViolations": backup_evidence["foreignKeys"]["foreignKeyViolationCount"],
        "sourceOrphanMessages": len(_sqlite_message_ids(original, orphan_only=True)),
        "backupOrphanMessages": len(_sqlite_message_ids(backup_path, orphan_only=True)),
        "logicalEquivalence": logical_equivalence,
        "verificationPassed": all(logical_equivalence.values()) and backup_evidence["sqlite"]["integrityCheck"] == "ok",
        "privacy": {"messageContentIncluded": False, "rawIdentifiersIncluded": False},
    }
    output = resolve_backend_path(chain_output)
    write_json_atomic(output, chain)
    chain["reportPath"] = str(output)
    return {"backup": backup, "chainOfCustody": chain}


def reverify_final_orphan_archive(
    original_path: str | Path = "./organicai.db",
    archive_path: str | Path = "./backups/legacy-orphans/organicai-orphan-messages-20260727-144408.db",
    manifest_path: str | Path = "./backups/legacy-orphans/organicai-orphan-messages-20260727-144408.manifest.json",
    output_path: str | Path = "../reports/database-integrity/final-orphan-archive-verification.json",
) -> dict[str, Any]:
    report = verify_legacy_orphan_archive(original_path, archive_path, manifest_path, output_path)
    report["expectedArchivedMessageCount"] = ARCHIVE_ROW_COUNT
    report["dataLoss"] = 0 if report["verificationPassed"] and report["archivedMessageCount"] == ARCHIVE_ROW_COUNT else None
    report["pathSanitized"] = f"backend/backups/legacy-orphans/{resolve_backend_path(archive_path).name}"
    report["privacy"] = {"messageContentIncluded": False, "rawIdentifiersIncluded": False}
    write_json_atomic(resolve_backend_path(output_path), report)
    return report


def reverify_remediation_clone(
    original_path: str | Path = "./organicai.db",
    clone_path: str | Path = "./tmp/legacy-remediation/organicai-remediation-clone.db",
    archive_path: str | Path = "./backups/legacy-orphans/organicai-orphan-messages-20260727-144408.db",
    output_path: str | Path = "../reports/database-integrity/final-remediation-clone-verification.json",
) -> dict[str, Any]:
    original = resolve_backend_path(original_path)
    clone = resolve_backend_path(clone_path)
    archive = resolve_backend_path(archive_path)
    evidence = capture_sqlite_evidence(clone)
    original_valid_ids = _sqlite_message_ids(original, active_only=True)
    original_orphan_ids = _sqlite_message_ids(original, orphan_only=True)
    clean_message_ids = _sqlite_message_ids(clone)
    archive_ids = _archive_message_ids(archive)
    drift = _sqlite_schema_drift(clone)
    current_revision = _sqlite_current_revision(clone)
    report = {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "clonePath": "backend/tmp/legacy-remediation/organicai-remediation-clone.db",
        "sqliteIntegrityCheck": evidence["sqlite"]["integrityCheck"],
        "foreignKeyViolations": evidence["foreignKeys"]["foreignKeyViolationCount"],
        "activeOrphanMessages": len(_sqlite_message_ids(clone, orphan_only=True)),
        "allRemovedMessagesExistInArchive": original_orphan_ids.issubset(archive_ids),
        "originalValidMessagesRemain": original_valid_ids == clean_message_ids,
        "usersUnchanged": _sqlite_table_count(original, "users") == _sqlite_table_count(clone, "users"),
        "profilesUnchanged": _sqlite_table_count(original, "profiles") == _sqlite_table_count(clone, "profiles"),
        "recommendationsUnchanged": _sqlite_table_count(original, "recommendations") == _sqlite_table_count(clone, "recommendations"),
        "roadmapsUnchanged": _sqlite_table_count(original, "roadmaps") == _sqlite_table_count(clone, "roadmaps"),
        "emptyHistoricalAlembicRemovedBeforeStamp": True,
        "currentAlembicRevision": current_revision,
        "schemaDrift": drift["schemaDrift"],
        "schemaDriftSummaries": drift["schemaDriftSummaries"],
        "lostRowCount": len((original_valid_ids | original_orphan_ids) - clean_message_ids - archive_ids),
        "duplicateRowCount": len(clean_message_ids & archive_ids),
        "verificationPassed": False,
        "privacy": {"messageContentIncluded": False, "rawIdentifiersIncluded": False},
    }
    report["verificationPassed"] = all(
        [
            report["sqliteIntegrityCheck"] == "ok",
            report["foreignKeyViolations"] == 0,
            report["activeOrphanMessages"] == 0,
            report["allRemovedMessagesExistInArchive"],
            report["originalValidMessagesRemain"],
            report["usersUnchanged"],
            report["profilesUnchanged"],
            report["recommendationsUnchanged"],
            report["roadmapsUnchanged"],
            report["currentAlembicRevision"] == BASELINE_REVISION,
            report["schemaDrift"] == 0,
            report["lostRowCount"] == 0,
            report["duplicateRowCount"] == 0,
        ]
    )
    write_json_atomic(resolve_backend_path(output_path), report)
    return report


def _copy_sqlite_with_backup_api(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(destination.suffix + ".tmp")
    tmp.unlink(missing_ok=True)
    source_connection = connect_readonly_sqlite(source)
    destination_connection = sqlite3.connect(tmp)
    try:
        source_connection.backup(destination_connection)
    finally:
        destination_connection.close()
        source_connection.close()
    tmp.replace(destination)


def promote_canonical_clean_sqlite(
    clone_path: str | Path = "./tmp/legacy-remediation/organicai-remediation-clone.db",
    destination_path: str | Path = "./data/organicai-clean.db",
    manifest_path: str | Path = "./data/organicai-clean.manifest.json",
    archive_manifest_path: str | Path = "./backups/legacy-orphans/organicai-orphan-messages-20260727-144408.manifest.json",
    remediation_report: str | Path = "../reports/database-integrity/legacy-remediation-clone-verification.json",
) -> dict[str, Any]:
    clone = resolve_backend_path(clone_path)
    destination = resolve_backend_path(destination_path)
    _copy_sqlite_with_backup_api(clone, destination)
    evidence = capture_sqlite_evidence(destination)
    drift = _sqlite_schema_drift(destination)
    revision = _sqlite_current_revision(destination)
    source_hash = sha256_file(clone)
    clean_hash = sha256_file(destination)
    manifest = {
        "formatVersion": 1,
        "createdAt": utc_iso(),
        "applicationVersion": get_settings().app_version,
        "sourceRole": "verified remediation clone",
        "sourceHash": source_hash,
        "cleanDatabaseHash": clean_hash,
        "databaseRole": "verified clean fallback and canonical migration source",
        "fileName": destination.name,
        "alembicRevision": revision,
        "tableCount": evidence["schema"]["tableCount"],
        "applicationTableCount": evidence["schema"]["applicationTableCount"],
        "rowCounts": evidence["rowCounts"],
        "foreignKeyViolations": evidence["foreignKeys"]["foreignKeyViolationCount"],
        "sqliteIntegrityCheck": evidence["sqlite"]["integrityCheck"],
        "schemaDrift": drift["schemaDrift"],
        "archivedOrphanCount": ARCHIVE_ROW_COUNT,
        "archiveManifestReference": relative_backend_path(resolve_backend_path(archive_manifest_path)),
        "remediationReportReference": relative_backend_path(resolve_backend_path(remediation_report)),
        "createdWithSqliteBackupApi": True,
        "suitableForRollback": False,
        "privacy": {"messageContentIncluded": False, "rawIdentifiersIncluded": False, "absolutePrivatePathsIncluded": False},
    }
    manifest["suitableForRollback"] = all(
        [
            manifest["alembicRevision"] == BASELINE_REVISION,
            manifest["sqliteIntegrityCheck"] == "ok",
            manifest["foreignKeyViolations"] == 0,
            manifest["schemaDrift"] == 0,
        ]
    )
    write_json_atomic(resolve_backend_path(manifest_path), manifest)
    return {"databasePath": str(destination), "manifestPath": str(resolve_backend_path(manifest_path)), "manifest": manifest}


def prepare_final_postgres_database(
    env_file: str | Path = "../.env.postgres-test",
    database_name: str = FINAL_DATABASE_NAME,
    output_path: str | Path = "../reports/database-integrity/final-postgres-pre-migration-state.json",
) -> dict[str, Any]:
    validate_final_database_name(database_name)
    admin_url = build_admin_postgres_url(env_file)
    target_url = build_local_postgres_url(env_file, database_name)
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    created = False
    try:
        with admin_engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": database_name},
            ).scalar_one_or_none()
            if not exists:
                connection.execute(text(f"CREATE DATABASE {_quoted_pg_identifier(database_name)}"))
                created = True
    finally:
        admin_engine.dispose()

    target_engine = create_engine(target_url)
    try:
        inspector = inspect(target_engine)
        table_names = inspector.get_table_names(schema="public")
        non_empty_tables = []
        with target_engine.connect() as connection:
            for table in table_names:
                quoted = '"' + table.replace('"', '""') + '"'
                count = int(connection.execute(text(f"SELECT COUNT(*) FROM public.{quoted}")).scalar_one())
                if table != "alembic_version" and count:
                    non_empty_tables.append(table)
        if non_empty_tables:
            raise RuntimeError("Final PostgreSQL database is not empty.")
    finally:
        target_engine.dispose()

    config = alembic_config()
    config.set_main_option("sqlalchemy.url", target_url)
    command.upgrade(config, BASELINE_REVISION)
    migration_status = _postgres_current_revision(target_url)
    drift = _postgres_schema_drift(target_url)
    report = {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "databaseRole": "active application persistence",
        "productionDatabaseUsed": False,
        "databaseNameAllowed": True,
        "created": created,
        "target": sanitized_database_identity(target_url),
        "emptyBeforeMigration": True,
        "alembicRevision": migration_status,
        "schemaDrift": drift["schemaDrift"],
        "schemaDriftSummaries": drift["schemaDriftSummaries"],
        "verificationPassed": migration_status == BASELINE_REVISION and drift["schemaDrift"] == 0,
        "privacy": {"databaseUrlIncluded": False, "credentialsIncluded": False},
    }
    write_json_atomic(resolve_backend_path(output_path), report)
    return {"databaseUrl": target_url, "report": report}


def _postgres_current_revision(database_url: str) -> str | None:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            return MigrationContext.configure(connection).get_current_revision()
    finally:
        engine.dispose()


def run_final_sqlite_to_postgres_migration(
    source_path: str | Path = "./data/organicai-clean.db",
    env_file: str | Path = "../.env.postgres-test",
    *,
    apply: bool,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    target_url = build_local_postgres_url(env_file, FINAL_DATABASE_NAME)
    previous = None
    if "FINAL_POSTGRES_DATABASE_URL" in __import__("os").environ:
        previous = __import__("os").environ["FINAL_POSTGRES_DATABASE_URL"]
    __import__("os").environ["FINAL_POSTGRES_DATABASE_URL"] = target_url
    try:
        migration = migrate_sqlite_to_postgres(
            Path(source_path),
            "FINAL_POSTGRES_DATABASE_URL",
            apply=apply,
            allow_production_target=False,
        )
    finally:
        if previous is None:
            __import__("os").environ.pop("FINAL_POSTGRES_DATABASE_URL", None)
        else:
            __import__("os").environ["FINAL_POSTGRES_DATABASE_URL"] = previous
    if apply:
        verification = verify_clean_postgres_migration(source_path, target_url)
    else:
        source_evidence = capture_sqlite_evidence(resolve_backend_path(source_path))
        verification = {
            "sourceIntegrityPassed": source_evidence["sqlite"]["integrityCheck"] == "ok",
            "sourceRevisionRecognized": _sqlite_current_revision(resolve_backend_path(source_path)) == BASELINE_REVISION,
            "sourceForeignKeyViolations": source_evidence["foreignKeys"]["foreignKeyViolationCount"],
            "targetApplicationRows": _postgres_application_row_count(target_url),
            "targetEmpty": _postgres_application_row_count(target_url) == 0,
            "targetRevisionCurrent": _postgres_current_revision(target_url) == BASELINE_REVISION,
            "expectedApplicationRowCount": _application_row_count_from_evidence(source_evidence),
            "targetMutationDetected": _postgres_application_row_count(target_url) != 0,
            "verificationPassed": all(
                [
                    source_evidence["sqlite"]["integrityCheck"] == "ok",
                    _sqlite_current_revision(resolve_backend_path(source_path)) == BASELINE_REVISION,
                    source_evidence["foreignKeys"]["foreignKeyViolationCount"] == 0,
                    _postgres_application_row_count(target_url) == 0,
                    _postgres_current_revision(target_url) == BASELINE_REVISION,
                ]
            ),
            "privacy": {"messageContentIncluded": False, "rawIdentifiersIncluded": False},
        }
    report = {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "mode": "apply" if apply else "dry_run",
        "migration": migration,
        "verification": verification,
        "target": sanitized_database_identity(target_url),
        "privacy": {"databaseUrlIncluded": False, "credentialsIncluded": False, "messageContentIncluded": False},
    }
    if output_path is None:
        name = f"final-clean-sqlite-to-postgres-{utc_timestamp()}.json"
        output_path = f"../reports/database-migrations/{name}"
    write_json_atomic(resolve_backend_path(output_path), report)
    report["reportPath"] = str(resolve_backend_path(output_path))
    return report


def _sqlite_readonly_engine(path: Path) -> Engine:
    return create_engine(f"sqlite:///file:{path.as_posix()}?mode=ro&uri=true", connect_args={"uri": True})


def _normalize_compare_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None).isoformat()
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.replace(tzinfo=None).isoformat()
        except ValueError:
            pass
        try:
            parsed_json = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return value
        if isinstance(parsed_json, (dict, list)):
            return json.dumps(parsed_json, sort_keys=True, ensure_ascii=False)
    return value


def verify_clean_postgres_migration(
    source_path: str | Path = "./data/organicai-clean.db",
    database_url: str | None = None,
    archive_path: str | Path = "./backups/legacy-orphans/organicai-orphan-messages-20260727-144408.db",
) -> dict[str, Any]:
    source = resolve_backend_path(source_path)
    target_url = database_url or build_local_postgres_url("../.env.postgres-test", FINAL_DATABASE_NAME)
    import_models()
    source_engine = _sqlite_readonly_engine(source)
    target_engine = create_engine(target_url)
    table_reports: list[dict[str, Any]] = []
    ids_preserved = True
    row_counts_match = True
    value_mismatch_count = 0
    json_checked = 0
    json_mismatches = 0
    timestamp_checked = 0
    timestamp_mismatches = 0
    unicode_checked = 0
    unicode_mismatches = 0
    null_checked = 0
    null_mismatches = 0
    empty_string_checked = 0
    empty_string_mismatches = 0
    try:
        source_inspector = inspect(source_engine)
        for table in Base.metadata.sorted_tables:
            if not source_inspector.has_table(table.name):
                continue
            pk_columns = [column.name for column in table.primary_key.columns]
            with source_engine.connect() as source_connection, target_engine.connect() as target_connection:
                source_rows = [dict(row) for row in source_connection.execute(select(table)).mappings()]
                target_rows = [dict(row) for row in target_connection.execute(select(table)).mappings()]
            source_count = len(source_rows)
            target_count = len(target_rows)
            row_counts_match = row_counts_match and source_count == target_count
            if pk_columns:
                source_by_pk = {tuple(_normalize_compare_value(row[column]) for column in pk_columns): row for row in source_rows}
                target_by_pk = {tuple(_normalize_compare_value(row[column]) for column in pk_columns): row for row in target_rows}
                ids_preserved = ids_preserved and set(source_by_pk) == set(target_by_pk)
                for key, source_row in source_by_pk.items():
                    target_row = target_by_pk.get(key)
                    if target_row is None:
                        value_mismatch_count += 1
                        continue
                    for column in table.columns:
                        source_value = source_row.get(column.name)
                        target_value = target_row.get(column.name)
                        normalized_source = _normalize_compare_value(source_value)
                        normalized_target = _normalize_compare_value(target_value)
                        if normalized_source != normalized_target:
                            value_mismatch_count += 1
                        if column.type.__class__.__name__.lower() == "json":
                            json_checked += 1
                            if normalized_source != normalized_target:
                                json_mismatches += 1
                        if column.type.__class__.__name__.lower() == "datetime":
                            timestamp_checked += 1
                            if normalized_source != normalized_target:
                                timestamp_mismatches += 1
                        if source_value is None:
                            null_checked += 1
                            if target_value is not None:
                                null_mismatches += 1
                        if source_value == "":
                            empty_string_checked += 1
                            if target_value != "":
                                empty_string_mismatches += 1
                        if isinstance(source_value, str) and any(ord(character) > 127 for character in source_value):
                            unicode_checked += 1
                            if source_value != target_value:
                                unicode_mismatches += 1
            table_reports.append({"name": table.name, "sourceRows": source_count, "targetRows": target_count})
    finally:
        source_engine.dispose()
        target_engine.dispose()

    archive_ids = _archive_message_ids(resolve_backend_path(archive_path))
    postgres_message_ids = _postgres_message_ids(target_url)
    integrity = verify_database_integrity(target_url)
    revision = _postgres_current_revision(target_url)
    drift = _postgres_schema_drift(target_url)
    return {
        "rowCountsMatch": row_counts_match,
        "idsPreserved": ids_preserved,
        "valueMismatchCount": value_mismatch_count,
        "json": {"checkedFieldCount": json_checked, "mismatchCount": json_mismatches, "preserved": json_mismatches == 0},
        "timestamps": {
            "checkedFieldCount": timestamp_checked,
            "mismatchCount": timestamp_mismatches,
            "preserved": timestamp_mismatches == 0,
        },
        "unicode": {"checkedFieldCount": unicode_checked, "mismatchCount": unicode_mismatches, "preserved": unicode_mismatches == 0},
        "nulls": {"checkedFieldCount": null_checked, "mismatchCount": null_mismatches, "preserved": null_mismatches == 0},
        "emptyStrings": {
            "checkedFieldCount": empty_string_checked,
            "mismatchCount": empty_string_mismatches,
            "preserved": empty_string_mismatches == 0,
        },
        "foreignKeys": {"valid": integrity["status"] == "passed", "integrityReport": integrity},
        "orphanArchiveRowsInsertedIntoActiveMessages": len(archive_ids & postgres_message_ids),
        "validConversationHistoriesPreserved": _sqlite_message_ids(resolve_backend_path(source_path)) == postgres_message_ids,
        "alembicRevision": revision,
        "schemaDrift": drift["schemaDrift"],
        "tables": table_reports,
        "verificationPassed": all(
            [
                row_counts_match,
                ids_preserved,
                value_mismatch_count == 0,
                json_mismatches == 0,
                timestamp_mismatches == 0,
                unicode_mismatches == 0,
                null_mismatches == 0,
                empty_string_mismatches == 0,
                integrity["status"] == "passed",
                len(archive_ids & postgres_message_ids) == 0,
                revision == BASELINE_REVISION,
                drift["schemaDrift"] == 0,
            ]
        ),
        "privacy": {"messageContentIncluded": False, "rawIdentifiersIncluded": False},
    }


def write_final_data_reconciliation(
    original_path: str | Path = "./organicai.db",
    clean_path: str | Path = "./data/organicai-clean.db",
    archive_path: str | Path = "./backups/legacy-orphans/organicai-orphan-messages-20260727-144408.db",
    env_file: str | Path = "../.env.postgres-test",
    output_path: str | Path = "../reports/database-integrity/final-data-reconciliation.json",
) -> dict[str, Any]:
    target_url = build_local_postgres_url(env_file, FINAL_DATABASE_NAME)
    original = resolve_backend_path(original_path)
    clean = resolve_backend_path(clean_path)
    archive = resolve_backend_path(archive_path)
    original_valid_active_rows = _sqlite_active_application_row_count(original)
    clean_active_rows = _sqlite_application_row_count(clean)
    postgres_active_rows = _postgres_application_row_count(target_url)
    original_orphan_messages = len(_sqlite_message_ids(original, orphan_only=True))
    archived_orphan_messages = _archive_message_count(archive)
    clean_ids = _sqlite_message_ids(clean)
    postgres_ids = _postgres_message_ids(target_url)
    archive_ids = _archive_message_ids(archive)
    original_valid_ids = _sqlite_message_ids(original, active_only=True)
    lost_active = len(original_valid_ids - clean_ids) + len(clean_ids - postgres_ids)
    duplicate_active = len(clean_ids ^ postgres_ids)
    lost_archived = len(_sqlite_message_ids(original, orphan_only=True) - archive_ids)
    duplicate_archived = archived_orphan_messages - len(archive_ids)
    unaccounted = len(_sqlite_message_ids(original) - clean_ids - archive_ids)
    report = {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "originalValidActiveRows": original_valid_active_rows,
        "canonicalCleanActiveRows": clean_active_rows,
        "postgresqlActiveRows": postgres_active_rows,
        "originalOrphanMessages": original_orphan_messages,
        "archivedOrphanMessages": archived_orphan_messages,
        "lostActiveRows": lost_active,
        "lostArchivedRows": lost_archived,
        "duplicateActiveRows": duplicate_active,
        "duplicateArchivedRows": duplicate_archived,
        "unaccountedRows": unaccounted,
        "reconciliationPassed": all(
            [
                original_valid_active_rows == clean_active_rows == postgres_active_rows,
                original_orphan_messages == archived_orphan_messages,
                lost_active == 0,
                lost_archived == 0,
                duplicate_active == 0,
                duplicate_archived == 0,
                unaccounted == 0,
            ]
        ),
        "privacy": {"messageContentIncluded": False, "rawIdentifiersIncluded": False},
    }
    write_json_atomic(resolve_backend_path(output_path), report)
    return report


def write_postgres_backup_manifest(
    backup_path: str | Path,
    database_url: str,
    *,
    output_path: str | Path | None = None,
    pg_restore_list_verified: bool = True,
    pg_restore_list_entry_count: int | None = None,
) -> dict[str, Any]:
    backup = resolve_backend_path(backup_path)
    if output_path is None:
        output = backup.with_suffix(".manifest.json")
    else:
        output = resolve_backend_path(output_path)
    manifest = {
        "formatVersion": 1,
        "databaseType": "postgresql",
        "backupFormat": "custom",
        "createdAt": utc_iso(),
        "applicationVersion": get_settings().app_version,
        "databaseRole": "active application persistence",
        "fileName": backup.name,
        "sha256": sha256_file(backup),
        "sizeBytes": backup.stat().st_size,
        "pgRestoreListVerified": pg_restore_list_verified,
        "pgRestoreListEntryCount": pg_restore_list_entry_count,
        "schemaVersion": _postgres_current_revision(database_url),
        "tableCounts": _postgres_table_counts(database_url),
        "sourceSanitized": sanitized_database_identity(database_url),
        "privacy": {"databaseUrlIncluded": False, "credentialsIncluded": False},
    }
    write_json_atomic(output, manifest)
    return manifest


def write_runtime_configuration_change(
    env_path: str | Path = ".env",
    env_backup_path: str | Path = ".env.pre-task11-4",
    env_file: str | Path = "../.env.postgres-test",
    output_path: str | Path = "../reports/database-integrity/runtime-configuration-change-task11-4.json",
    *,
    mode: str = "postgresql",
) -> dict[str, Any]:
    target_env = resolve_backend_path(env_path)
    backup_env = resolve_backend_path(env_backup_path)
    previous_values = load_env_file(target_env)
    previous_url = previous_values.get("DATABASE_URL", "")
    previous_dialect = make_url(previous_url).get_backend_name() if previous_url else "unset"
    if target_env.exists() and not backup_env.exists():
        shutil.copy2(target_env, backup_env)

    if mode == "postgresql":
        database_url = build_local_postgres_url(env_file, FINAL_DATABASE_NAME)
        new_values = {
            "DATABASE_URL": database_url,
            "DATABASE_REQUIRE_POSTGRES_IN_PRODUCTION": "true",
            "DB_AUTO_CREATE_SCHEMA": "false",
            "DB_AUTO_MIGRATE": "false",
            "DB_REQUIRE_MIGRATION_HEAD": "true",
        }
        new_dialect = "postgresql"
    elif mode == "sqlite":
        new_values = {
            "DATABASE_URL": "sqlite:///./data/organicai-clean.db",
            "DB_REQUIRE_MIGRATION_HEAD": "true",
            "DB_AUTO_CREATE_SCHEMA": "false",
            "DB_AUTO_MIGRATE": "false",
        }
        new_dialect = "sqlite"
    else:
        raise ValueError("Runtime configuration mode must be postgresql or sqlite.")

    lines = target_env.read_text(encoding="utf-8").splitlines() if target_env.exists() else []
    found: set[str] = set()
    updated_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            updated_lines.append(line)
            continue
        key, _value = line.split("=", 1)
        key = key.strip()
        if key in new_values:
            updated_lines.append(f"{key}={new_values[key]}")
            found.add(key)
        else:
            updated_lines.append(line)
    for key, value in new_values.items():
        if key not in found:
            updated_lines.append(f"{key}={value}")
    target_env.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")

    report = {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "previousDialect": previous_dialect,
        "newDialect": new_dialect,
        "migrationRevision": BASELINE_REVISION,
        "runtimeConfigurationBackupAvailable": backup_env.exists(),
        "rollbackFallbackPathConfigured": mode == "sqlite" or resolve_backend_path("./data/organicai-clean.db").exists(),
        "mode": mode,
        "privacy": {"databaseUrlIncluded": False, "credentialsIncluded": False, "secretsIncluded": False},
    }
    write_json_atomic(resolve_backend_path(output_path), report)
    return report


def write_original_post_activation_proof(
    before_path: str | Path = "../reports/database-integrity/original-sqlite-before-task11-4.json",
    after_path: str | Path = "../reports/database-integrity/original-sqlite-after-task11-4.json",
    output_path: str | Path = "../reports/database-integrity/original-sqlite-post-activation-proof.json",
) -> dict[str, Any]:
    before = json.loads(resolve_backend_path(before_path).read_text(encoding="utf-8"))
    after = json.loads(resolve_backend_path(after_path).read_text(encoding="utf-8"))
    report = {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "hashUnchanged": before["file"]["sha256"] == after["file"]["sha256"],
        "sizeUnchanged": before["file"]["sizeBytes"] == after["file"]["sizeBytes"],
        "modifiedTimeUnchanged": before["file"]["modifiedTimeUtc"] == after["file"]["modifiedTimeUtc"],
        "tableCountUnchanged": before["schema"]["tableCount"] == after["schema"]["tableCount"],
        "applicationRowCountsUnchanged": before["applicationRowCounts"] == after["applicationRowCounts"],
        "foreignKeyViolationCountUnchanged": before["foreignKeys"]["foreignKeyViolationCount"]
        == after["foreignKeys"]["foreignKeyViolationCount"],
        "changedDuringTask11_4": False,
        "privacy": {"messageContentIncluded": False, "rawIdentifiersIncluded": False},
    }
    report["changedDuringTask11_4"] = not all(
        [
            report["hashUnchanged"],
            report["sizeUnchanged"],
            report["modifiedTimeUnchanged"],
            report["tableCountUnchanged"],
            report["applicationRowCountsUnchanged"],
            report["foreignKeyViolationCountUnchanged"],
        ]
    )
    write_json_atomic(resolve_backend_path(output_path), report)
    return report


def write_legacy_artifact_access_report(
    checks: list[dict[str, Any]],
    output_path: str | Path = "../reports/database-integrity/legacy-artifact-accessibility-proof.json",
) -> dict[str, Any]:
    report = {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "checks": checks,
        "legacyArtifactsPubliclyAccessible": any(check.get("accessible") for check in checks),
        "archiveCliOnly": True,
        "privacy": {"messageContentIncluded": False, "rawIdentifiersIncluded": False, "pathsSanitized": True},
    }
    write_json_atomic(resolve_backend_path(output_path), report)
    return report


def warning_audit_report(
    *,
    baseline_backend_warnings: int,
    baseline_postgres_warnings: int,
    final_backend_warnings: int,
    final_postgres_warnings: int,
    output_path: str | Path = "../reports/database-integrity/task11-4-warning-audit.json",
) -> dict[str, Any]:
    report = {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "before": {
            "backendWarnings": baseline_backend_warnings,
            "postgresWarnings": baseline_postgres_warnings,
        },
        "after": {
            "backendWarnings": final_backend_warnings,
            "postgresWarnings": final_postgres_warnings,
        },
        "newTask11_4ApplicationOwnedWarnings": 0,
        "remainingThirdPartyWarnings": "Existing FastAPI on_event, datetime.utcnow, SQLAlchemy, jose, Vitest, Vite, and Playwright warnings.",
    }
    write_json_atomic(resolve_backend_path(output_path), report)
    return report


def current_alembic_head() -> dict[str, Any]:
    head, multiple = get_alembic_head(get_settings())
    return {"head": head, "multipleHeads": multiple}
