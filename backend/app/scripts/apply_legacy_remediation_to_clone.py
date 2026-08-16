from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.database_admin import resolve_backend_path
from app.services.legacy_remediation import apply_legacy_remediation_to_clone


def _latest_file(directory: str | Path, pattern: str) -> Path:
    base = resolve_backend_path(directory)
    files = sorted(base.glob(pattern), key=lambda item: item.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"No file matching {pattern} found.")
    return files[-1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply conservative Task 11.3 remediation to a disposable SQLite clone.")
    parser.add_argument("--original", default="./organicai.db")
    parser.add_argument("--source-backup")
    parser.add_argument("--backup-dir", default="./backups/database")
    parser.add_argument("--archive")
    parser.add_argument("--archive-manifest")
    parser.add_argument("--archive-dir", default="./backups/legacy-orphans")
    parser.add_argument("--clone", default="./tmp/legacy-remediation/organicai-remediation-clone.db")
    args = parser.parse_args()
    try:
        source_backup = resolve_backend_path(args.source_backup) if args.source_backup else _latest_file(args.backup_dir, "organicai-pre-remediation-*.db")
        archive = resolve_backend_path(args.archive) if args.archive else _latest_file(args.archive_dir, "organicai-orphan-messages-*.db")
        archive_manifest = (
            resolve_backend_path(args.archive_manifest)
            if args.archive_manifest
            else archive.with_name(archive.name.replace(".db", ".manifest.json"))
        )
        result = apply_legacy_remediation_to_clone(
            original_path=args.original,
            source_backup_path=source_backup,
            archive_path=archive,
            archive_manifest_path=archive_manifest,
            clone_path=args.clone,
        )
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": exc.__class__.__name__, "message": str(exc)}, indent=2))
        return 1
    print(
        json.dumps(
            {
                "status": "success",
                "cloneCreated": result["cloneCreation"]["created"],
                "initialSourceMatch": result["cloneCreation"]["initialSourceMatch"],
                "archiveVerified": result["archiveVerification"]["verificationPassed"],
                "archivedAndRemovedFromActiveClone": result["journal"]["summary"]["archivedAndRemovedFromActiveClone"],
                "foreignKeyViolationsAfter": result["verification"]["foreignKeyViolations"],
                "sqliteIntegrityCheck": result["verification"]["sqliteIntegrityCheck"],
                "reconciliationPassed": result["reconciliation"]["reconciliationPassed"],
                "schemaEquivalencePassed": result["schema"]["schemaEquivalencePassed"],
                "revisionStamped": result["stamp"]["revisionStamped"],
                "currentRevision": result["stamp"]["currentRevision"],
                "cleanInventory": result["cleanInventory"]["reportPath"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
