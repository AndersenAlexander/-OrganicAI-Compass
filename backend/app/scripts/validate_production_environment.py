from __future__ import annotations

import argparse
import json

from app.services.runtime_configuration import check_runtime_configuration, sanitized_report_dict


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate production environment configuration without printing secret values.")
    parser.add_argument("--strict-production", action="store_true", help="Fail unless APP_ENV is production and production checks pass.")
    args = parser.parse_args()
    report = check_runtime_configuration()
    payload = sanitized_report_dict(report)
    errors = [check for check in payload["checks"] if check["status"] == "error"]
    if args.strict_production and payload["environment"] != "production":
        errors.append({"key": "APP_ENV", "category": "runtime", "status": "error", "message": "APP_ENV must be production for strict validation."})
    payload["status"] = "passed" if not errors else "blocked"
    payload["blockingFindingCount"] = len(errors)
    payload["secretValuesIncluded"] = False
    print(json.dumps(payload, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
