from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROUTERS = ROOT / "backend" / "app" / "routers"
REPORT = ROOT / "reports" / "security" / "route-authorization-audit-task12a.json"

PUBLIC_ALLOWLIST = {
    "auth.py",
    "demo.py",
    "elevenlabs_llm.py",
}

SIGNED_PROVIDER_WEBHOOKS = {
    "webhooks.py": "Signed provider webhook authenticated with timestamped HMAC.",
}

OPTIONAL_PUBLIC_HINTS = (
    "support_programmes",
    "support_programme",
    "providers",
    "resource_detail",
    "search(",
)


def audit() -> dict:
    findings: list[dict[str, str]] = []
    for path in sorted(ROUTERS.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if "get_optional_user" in text and path.name not in PUBLIC_ALLOWLIST:
            for line_number, line in enumerate(text.splitlines(), start=1):
                if "get_optional_user" in line and not any(hint in text[max(0, text.rfind("async def", 0, text.find(line))) : text.find(line) + 300] for hint in OPTIONAL_PUBLIC_HINTS):
                    findings.append(
                        {
                            "file": f"backend/app/routers/{path.name}",
                            "line": str(line_number),
                            "category": "optional_user_dependency",
                            "message": "Route uses centralized optional-user dependency; confirm it is public or replace with get_current_user.",
                        }
                    )
        if path.name in SIGNED_PROVIDER_WEBHOOKS:
            findings.append(
                {
                    "file": f"backend/app/routers/{path.name}",
                    "line": "1",
                    "category": "signed_provider_webhook",
                    "message": SIGNED_PROVIDER_WEBHOOKS[path.name],
                }
            )
            continue
        if re.search(r"@router\.(post|put|patch|delete)", text) and "get_db" in text and "get_current_user" not in text and "get_optional_user" not in text and path.name not in PUBLIC_ALLOWLIST:
            findings.append(
                {
                    "file": f"backend/app/routers/{path.name}",
                    "line": "1",
                    "category": "mutating_route_without_auth_dependency",
                    "message": "Mutating router has no detected auth dependency.",
                }
            )
    blocking = [finding for finding in findings if finding["category"] == "mutating_route_without_auth_dependency"]
    report = {
        "formatVersion": 1,
        "blockingFindingCount": len(blocking),
        "advisoryFindingCount": len(findings) - len(blocking),
        "findings": findings,
        "policy": {
            "getOptionalUser": "Centralized dependency rejects anonymous users except explicit public allowlist paths.",
            "signedProviderWebhooks": "Provider callbacks may use timestamped HMAC authentication instead of user sessions.",
            "rawIdentifiersIncluded": False,
            "secretValuesIncluded": False,
        },
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    report = audit()
    print(json.dumps(report, indent=2))
    return 1 if report["blockingFindingCount"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
