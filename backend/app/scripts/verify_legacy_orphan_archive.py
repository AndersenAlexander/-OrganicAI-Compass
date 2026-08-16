from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.database_admin import resolve_backend_path
from app.services.legacy_orphan_archive import verify_legacy_orphan_archive


def _latest_archive_pair(directory: str | Path) -> tuple[Path, Path]:
    archive_dir = resolve_backend_path(directory)
    manifests = sorted(archive_dir.glob("organicai-orphan-messages-*.manifest.json"), key=lambda item: item.stat().st_mtime)
    if not manifests:
        raise FileNotFoundError("No legacy orphan archive manifest found.")
    manifest = manifests[-1]
    archive = manifest.with_name(manifest.name.replace(".manifest.json", ".db"))
    return archive, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a local legacy orphan-message archive.")
    parser.add_argument("--source", default="./organicai.db")
    parser.add_argument("--archive")
    parser.add_argument("--manifest")
    parser.add_argument("--archive-dir", default="./backups/legacy-orphans")
    parser.add_argument("--output", default="../reports/database-integrity/legacy-orphan-archive-verification.json")
    args = parser.parse_args()
    try:
        if args.archive and args.manifest:
            archive = resolve_backend_path(args.archive)
            manifest = resolve_backend_path(args.manifest)
        else:
            archive, manifest = _latest_archive_pair(args.archive_dir)
        report = verify_legacy_orphan_archive(args.source, archive, manifest, args.output)
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": exc.__class__.__name__, "message": str(exc)}, indent=2))
        return 1
    print(
        json.dumps(
            {
                "status": "success" if report["verificationPassed"] else "failed",
                "verificationPassed": report["verificationPassed"],
                "archiveOpenedReadOnly": report["archiveOpenedReadOnly"],
                "archivedMessageCount": report["archivedMessageCount"],
                "archivedMessageIdsMatchSource": report["archivedMessageIdsMatchSource"],
                "sqliteIntegrityCheck": report["sqliteIntegrityCheck"],
                "reportPath": report["reportPath"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if report["verificationPassed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
