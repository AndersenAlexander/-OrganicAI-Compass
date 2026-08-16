from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.database import SessionLocal
from app.services.email.validation import email_configuration_status, send_validation_email


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--offline", action="store_true")
    group.add_argument("--connection", action="store_true")
    group.add_argument("--send-test", action="store_true")
    args = parser.parse_args()
    if args.send_test:
        from app.config import get_settings

        settings = get_settings()
        with SessionLocal() as db:
            report = send_validation_email(db, settings.email_test_recipient)
    else:
        report = email_configuration_status()
        report["mode"] = "connection" if args.connection else "offline"
        if args.offline:
            report["connection"] = "not-executed"
    out = Path("..") / "reports" / "provider-validation" / "email-delivery-status.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
