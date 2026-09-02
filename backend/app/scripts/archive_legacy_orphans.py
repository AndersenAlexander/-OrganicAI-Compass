from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.database_admin import resolve_backend_path
from app.services.legacy_orphan_analysis import write_legacy_orphan_forensic_report
from app.services.legacy_orphan_archive import create_legacy_orphan_archive


def _sanitize_path(path_value: str) -> str:
    path = Path(path_value)
    try:
        return str(path.relative_to(resolve_backend_path(".")))
    except ValueError:
        return path.name


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a lossless local archive of legacy orphan messages.")
    parser.add_argument("--source", default="./organicai.db")
    parser.add_argument("--output-dir", default="./backups/legacy-orphans")
    parser.add_argument("--forensic-output", default="../reports/database-integrity/legacy-orphan-forensic-analysis.json")
    args = parser.parse_args()
    try:
        analysis = write_legacy_orphan_forensic_report(args.source, args.forensic_output)
        result = create_legacy_orphan_archive(args.source, args.output_dir, analysis=analysis)
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": exc.__class__.__name__, "message": str(exc)}, indent=2))
        return 1
    print(
        json.dumps(
            {
                "status": "success",
                "openedReadOnly": analysis["openedReadOnly"],
                "orphanRows": analysis["summary"]["messageOrphanRows"],
                "missingConversationGroups": analysis["summary"]["missingConversationGroups"],
                "archivePathSanitized": _sanitize_path(result["archivePath"]),
                "manifestPathSanitized": _sanitize_path(result["manifestPath"]),
                "forensicReportPath": analysis["reportPath"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
