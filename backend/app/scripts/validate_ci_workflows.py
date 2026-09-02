from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


REQUIRED_SNIPPETS = {
    "backend compile": "python -m compileall -q app tests",
    "backend tests": "python -m pytest -q",
    "postgres service": "postgres:16.6-bookworm",
    "postgres marker": "-m postgres",
    "frontend unit": "npm run test",
    "typecheck": "npm run typecheck",
    "frontend build": "npm run build",
    "playwright mock": "npm run test:e2e",
    "archive audit": "create_source_archive",
    "secret scan": "security_scan",
    "schema drift": "prepare_postgres_test_database",
    "artifact upload": "actions/upload-artifact",
}


def main() -> int:
    workflow = ROOT / ".github" / "workflows" / "ci.yml"
    text = workflow.read_text(encoding="utf-8") if workflow.exists() else ""
    findings = [
        {"check": name, "status": "passed" if snippet in text else "blocked", "snippet": snippet}
        for name, snippet in REQUIRED_SNIPPETS.items()
    ]
    blocking = [item for item in findings if item["status"] == "blocked"]
    payload = {
        "formatVersion": 1,
        "workflow": ".github/workflows/ci.yml",
        "status": "passed" if not blocking else "blocked",
        "blockingFindingCount": len(blocking),
        "checks": findings,
        "secretValuesIncluded": False,
    }
    print(json.dumps(payload, indent=2))
    return 0 if not blocking else 2


if __name__ == "__main__":
    raise SystemExit(main())
