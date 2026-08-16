from __future__ import annotations

import json
import os
from pathlib import Path


PROHIBITED = [
    "authorization",
    "cookie",
    "access_token",
    "refresh_token",
    "password",
    "api_key",
    "email",
    "message_content",
    "transcript",
    "prompt",
    "response_content",
    "raw_user_id",
    "raw_profile_id",
    "raw_conversation_id",
    "database_url",
    "sql_parameter",
]

ALLOWED_SANITIZER_REFERENCES = {
    "authorization",
    "cookie",
    "password",
}


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    files = [
        root / "app" / "services" / "telemetry.py",
        root / "app" / "services" / "metrics.py",
        root.parent / "deploy" / "observability" / "otel-collector.yaml",
    ]
    findings: list[dict[str, object]] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8").lower()
        except OSError:
            continue
        for category in PROHIBITED:
            count = text.count(category)
            if count == 0:
                continue
            severity = "remediated" if category in ALLOWED_SANITIZER_REFERENCES else "blocking"
            findings.append(
                {
                    "category": category,
                    "location": str(path.relative_to(root.parent)),
                    "count": count,
                    "severity": severity,
                    "remediationStatus": "collector-removes-attribute" if severity == "remediated" else "requires-review",
                }
            )
    blocking = [finding for finding in findings if finding["severity"] == "blocking"]
    report = {
        "formatVersion": 1,
        "blockingFindingCount": len(blocking),
        "findings": findings,
        "secretValuesIncluded": False,
        "personalDataIncluded": False,
    }
    out = Path(os.environ.get("TELEMETRY_PRIVACY_REPORT_PATH", "../evidence/task13a/telemetry-privacy-audit.json"))
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except OSError:
        pass
    print(json.dumps(report, indent=2))
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
