from __future__ import annotations

import argparse
import json

from app.services.database_immutability import write_immutability_proof, write_sqlite_evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture read-only SQLite immutability evidence.")
    parser.add_argument("--database", default="./organicai.db")
    parser.add_argument("--output", default="../reports/database-integrity/original-sqlite-before-task11-3.json")
    parser.add_argument("--compare-before")
    parser.add_argument("--compare-after")
    parser.add_argument("--comparison-output", default="../reports/database-integrity/original-sqlite-immutability-proof.json")
    args = parser.parse_args()
    try:
        if args.compare_before and args.compare_after:
            proof = write_immutability_proof(args.compare_before, args.compare_after, args.comparison_output)
            print(
                json.dumps(
                    {
                        "status": "success",
                        "changedDuringTask": proof["changedDuringTask"],
                        "sha256Matches": proof["sha256Matches"],
                        "applicationRowCountsMatch": proof["applicationRowCountsMatch"],
                        "foreignKeyViolationCountMatches": proof["foreignKeyViolationCountMatches"],
                        "reportPath": proof["reportPath"],
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0 if not proof["changedDuringTask"] else 2
        report = write_sqlite_evidence(args.database, args.output)
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": exc.__class__.__name__, "message": str(exc)}, indent=2))
        return 1
    print(
        json.dumps(
            {
                "status": "success",
                "openedReadOnly": report["openedReadOnly"],
                "tableCount": report["schema"]["tableCount"],
                "applicationTableCount": report["schema"]["applicationTableCount"],
                "orphanViolations": report["foreignKeys"]["foreignKeyViolationCount"],
                "distinctAffectedRows": report["foreignKeys"]["distinctAffectedOrphanRowCount"],
                "reportPath": report["reportPath"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
