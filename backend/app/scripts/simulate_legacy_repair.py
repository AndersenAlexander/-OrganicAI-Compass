from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from app.services.database_admin import resolve_backend_path, sha256_file, write_json_atomic
from app.services.legacy_orphan_analysis import analyze_legacy_orphans, load_json


def _copy_with_sqlite_backup(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    source_uri = source.resolve().as_uri() + "?mode=ro"
    source_connection = sqlite3.connect(source_uri, uri=True)
    try:
        destination_connection = sqlite3.connect(destination)
        try:
            source_connection.backup(destination_connection)
        finally:
            destination_connection.close()
    finally:
        source_connection.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate approved legacy orphan repairs on a disposable SQLite copy.")
    parser.add_argument("--source", default="./organicai.db")
    parser.add_argument("--plan", default="../reports/database-integrity/legacy-orphan-remediation-plan.json")
    parser.add_argument("--copy", default="./tmp/legacy-analysis/organicai-repair-simulation.db")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply-approved", action="store_true")
    parser.add_argument("--output", default="../reports/database-integrity/legacy-repair-simulation.json")
    args = parser.parse_args()

    source = resolve_backend_path(args.source)
    destination = resolve_backend_path(args.copy)
    source_sha_before = sha256_file(source)
    try:
        plan = load_json(args.plan)
        _copy_with_sqlite_backup(source, destination)
        before = analyze_legacy_orphans(destination)
        approved = [item for item in plan.get("items", []) if item.get("approvedForSimulation") is True]
        applied: list[dict[str, object]] = []
        blocked: list[dict[str, object]] = []
        for item in approved:
            blocked.append(
                {
                    "childTable": item.get("childTable"),
                    "parentTable": item.get("parentTable"),
                    "recommendedAction": item.get("recommendedAction"),
                    "reason": "Task 11.1 does not authorize automatic data repair actions.",
                }
            )
        after = analyze_legacy_orphans(destination)
        source_sha_after = sha256_file(source)
        report = {
            "status": "dry_run" if not args.apply_approved else "blocked",
            "copyPath": str(destination),
            "sourceOriginalUnchanged": source_sha_before == source_sha_after,
            "sourceSha256Before": source_sha_before,
            "sourceSha256After": source_sha_after,
            "copyCreatedWithSqliteBackupApi": True,
            "dryRun": not args.apply_approved,
            "approvedActionsFound": len(approved),
            "appliedActions": applied,
            "blockedActions": blocked,
            "before": {
                "orphanViolations": before["summary"]["orphanViolations"],
                "distinctAffectedRows": before["summary"]["distinctAffectedRows"],
            },
            "after": {
                "orphanViolations": after["summary"]["orphanViolations"],
                "distinctAffectedRows": after["summary"]["distinctAffectedRows"],
            },
            "copyIntegrity": after["summary"]["sqliteIntegrityCheck"],
        }
        output = resolve_backend_path(args.output)
        write_json_atomic(output, report)
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": exc.__class__.__name__, "message": str(exc)}, indent=2))
        return 1
    print(
        json.dumps(
            {
                "status": report["status"],
                "copyCreatedWithSqliteBackupApi": True,
                "sourceOriginalUnchanged": report["sourceOriginalUnchanged"],
                "beforeOrphanViolations": report["before"]["orphanViolations"],
                "afterOrphanViolations": report["after"]["orphanViolations"],
                "approvedActionsFound": report["approvedActionsFound"],
                "output": str(output),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
