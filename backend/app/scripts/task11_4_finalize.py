from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.database_immutability import write_sqlite_evidence
from app.services.task11_4_finalization import (
    FINAL_DATABASE_NAME,
    build_local_postgres_url,
    capture_original_before_task11_4,
    create_final_original_backup_and_chain,
    prepare_final_postgres_database,
    promote_canonical_clean_sqlite,
    reverify_final_orphan_archive,
    reverify_remediation_clone,
    run_final_sqlite_to_postgres_migration,
    verify_clean_postgres_migration,
    warning_audit_report,
    write_final_data_reconciliation,
    write_legacy_artifact_access_report,
    write_original_post_activation_proof,
    write_postgres_backup_manifest,
    write_runtime_configuration_change,
)


def _print(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 11.4 final PostgreSQL activation utilities.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("capture-original-before")
    sub.add_parser("final-original-backup")
    sub.add_parser("verify-orphan-archive")
    sub.add_parser("verify-remediation-clone")
    sub.add_parser("promote-clean-sqlite")

    prepare = sub.add_parser("prepare-final-postgres")
    prepare.add_argument("--env-file", default="../.env.postgres-test")

    migrate = sub.add_parser("migrate-final-postgres")
    migrate.add_argument("--env-file", default="../.env.postgres-test")
    migrate.add_argument("--apply", action="store_true")
    migrate.add_argument("--output")

    verify = sub.add_parser("verify-final-migration")
    verify.add_argument("--env-file", default="../.env.postgres-test")

    reconcile = sub.add_parser("final-reconciliation")
    reconcile.add_argument("--env-file", default="../.env.postgres-test")

    manifest = sub.add_parser("postgres-backup-manifest")
    manifest.add_argument("--backup", required=True)
    manifest.add_argument("--env-file", default="../.env.postgres-test")
    manifest.add_argument("--pg-restore-list-entries", type=int)

    runtime = sub.add_parser("runtime-config")
    runtime.add_argument("--env-file", default="../.env.postgres-test")
    runtime.add_argument("--mode", choices=["postgresql", "sqlite"], default="postgresql")

    after = sub.add_parser("capture-original-after")
    after.add_argument("--output", default="../reports/database-integrity/original-sqlite-after-task11-4.json")

    sub.add_parser("original-post-activation-proof")

    access = sub.add_parser("artifact-access-report")
    access.add_argument("--checks-json", required=True)

    warnings = sub.add_parser("warning-audit")
    warnings.add_argument("--baseline-backend-warnings", type=int, required=True)
    warnings.add_argument("--baseline-postgres-warnings", type=int, required=True)
    warnings.add_argument("--final-backend-warnings", type=int, required=True)
    warnings.add_argument("--final-postgres-warnings", type=int, required=True)

    args = parser.parse_args()
    try:
        if args.command == "capture-original-before":
            _print(capture_original_before_task11_4())
        elif args.command == "final-original-backup":
            _print(create_final_original_backup_and_chain())
        elif args.command == "verify-orphan-archive":
            _print(reverify_final_orphan_archive())
        elif args.command == "verify-remediation-clone":
            _print(reverify_remediation_clone())
        elif args.command == "promote-clean-sqlite":
            _print(promote_canonical_clean_sqlite())
        elif args.command == "prepare-final-postgres":
            result = prepare_final_postgres_database(args.env_file)
            _print({"database": FINAL_DATABASE_NAME, "report": result["report"]})
        elif args.command == "migrate-final-postgres":
            _print(run_final_sqlite_to_postgres_migration(env_file=args.env_file, apply=args.apply, output_path=args.output))
        elif args.command == "verify-final-migration":
            _print(verify_clean_postgres_migration(database_url=build_local_postgres_url(args.env_file, FINAL_DATABASE_NAME)))
        elif args.command == "final-reconciliation":
            _print(write_final_data_reconciliation(env_file=args.env_file))
        elif args.command == "postgres-backup-manifest":
            url = build_local_postgres_url(args.env_file, FINAL_DATABASE_NAME)
            _print(
                write_postgres_backup_manifest(
                    Path(args.backup),
                    url,
                    pg_restore_list_verified=True,
                    pg_restore_list_entry_count=args.pg_restore_list_entries,
                )
            )
        elif args.command == "runtime-config":
            _print(write_runtime_configuration_change(env_file=args.env_file, mode=args.mode))
        elif args.command == "capture-original-after":
            _print(write_sqlite_evidence("./organicai.db", args.output))
        elif args.command == "original-post-activation-proof":
            _print(write_original_post_activation_proof())
        elif args.command == "artifact-access-report":
            checks = json.loads(Path(args.checks_json).read_text(encoding="utf-8"))
            _print(write_legacy_artifact_access_report(checks))
        elif args.command == "warning-audit":
            _print(
                warning_audit_report(
                    baseline_backend_warnings=args.baseline_backend_warnings,
                    baseline_postgres_warnings=args.baseline_postgres_warnings,
                    final_backend_warnings=args.final_backend_warnings,
                    final_postgres_warnings=args.final_postgres_warnings,
                )
            )
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": exc.__class__.__name__, "message": str(exc)}, indent=2, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
