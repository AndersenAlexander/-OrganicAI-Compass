from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path


BLOCKING_CATEGORIES = {
    "git",
    "remote repository",
    "remote CI evidence",
    "secret rotation",
    "provider selection",
    "region",
    "budget",
    "secret management",
    "database",
}


@dataclass(frozen=True)
class Check:
    category: str
    status: str
    reason: str


def _exists(root: Path, relative: str) -> bool:
    return (root / relative).exists()


def audit_cloud_staging_readiness(root: Path) -> dict:
    git_available = shutil.which("git") is not None
    checks = [
        Check("git", "passed" if git_available else "blocked", "Git is available in PATH." if git_available else "Git is not available in PATH."),
        Check("remote repository", "blocked", "No approved remote URL or remote execution evidence is recorded."),
        Check("CI definition", "passed" if _exists(root, ".github/workflows/ci.yml") else "blocked", "GitHub Actions workflow file present."),
        Check("remote CI evidence", "blocked", "GitHub Actions have not run remotely."),
        Check("secret rotation", "blocked", "Previously exposed credentials remain manual-action-required until rotated and verified."),
        Check("provider selection", "blocked", "No cloud provider has been approved."),
        Check("region", "blocked", "No cloud deployment region has been approved."),
        Check("budget", "manual-action-required", "Monthly staging budget requires user approval."),
        Check("domain", "manual-action-required", "No staging domain has been approved."),
        Check("TLS", "manual-action-required", "TLS can be configured only after a staging hostname exists."),
        Check("database", "passed" if _exists(root, "docs/CLOUD_POSTGRESQL_MIGRATION_PLAN.md") else "blocked", "Cloud PostgreSQL migration plan documented."),
        Check("secret management", "passed" if _exists(root, "docs/CLOUD_SECRET_MANAGEMENT_PLAN.md") else "blocked", "Cloud secret-management plan documented."),
        Check("container registry", "manual-action-required", "Registry is not selected."),
        Check("observability", "passed" if _exists(root, "docs/CLOUD_OBSERVABILITY_PLAN.md") else "blocked", "Cloud observability plan documented."),
        Check("backup", "passed" if _exists(root, "docs/CLOUD_BACKUP_AND_RECOVERY_PLAN.md") else "blocked", "Cloud backup and recovery plan documented."),
        Check("privacy review", "manual-action-required", "Legal and operational privacy review remains required."),
    ]
    blocking = [check for check in checks if check.status == "blocked" and check.category in BLOCKING_CATEGORIES]
    return {
        "formatVersion": 1,
        "cloudDeployment": "blocked",
        "task13b1ApprovedToStart": False,
        "blockingFindingCount": len(blocking),
        "manualActionCount": sum(1 for check in checks if check.status == "manual-action-required"),
        "secretValuesIncluded": False,
        "checks": [check.__dict__ for check in checks],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[3]))
    args = parser.parse_args()
    print(json.dumps(audit_cloud_staging_readiness(Path(args.root).resolve()), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
