from __future__ import annotations

import argparse
import json

from app.services.legacy_orphan_analysis import write_legacy_orphan_report, write_remediation_plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze legacy SQLite foreign-key orphan relations without exposing row content.")
    parser.add_argument("--database", default="./organicai.db")
    parser.add_argument("--output", default="../reports/database-integrity/legacy-orphans.json")
    parser.add_argument("--plan-output", default="../reports/database-integrity/legacy-orphan-remediation-plan.json")
    args = parser.parse_args()
    try:
        report = write_legacy_orphan_report(args.database, args.output)
        plan = write_remediation_plan(report, args.plan_output)
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": exc.__class__.__name__, "message": str(exc)}, indent=2))
        return 1
    print(
        json.dumps(
            {
                "status": "success",
                "openedReadOnly": report["openedReadOnly"],
                "orphanViolations": report["summary"]["orphanViolations"],
                "distinctAffectedRows": report["summary"]["distinctAffectedRows"],
                "sourceShaMatches": report["sourceProof"]["sha256Matches"],
                "reportPath": report["reportPath"],
                "remediationPlanPath": plan["reportPath"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
