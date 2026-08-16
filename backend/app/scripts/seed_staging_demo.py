from __future__ import annotations

import argparse
import json
import secrets

from app.config import get_settings
from app.database import SessionLocal
from app.services.demo_seed_service import ensure_demo


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed deterministic staging demo data without provider calls.")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--print-local-password", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    if settings.app_env != "staging":
        print(json.dumps({"status": "blocked", "reason": "APP_ENV must be staging"}))
        return 2
    if not settings.demo_account_enabled:
        print(json.dumps({"status": "blocked", "reason": "Demo account is disabled"}))
        return 2
    generated = False
    if not settings.demo_user_password or "replace" in settings.demo_user_password.lower():
        settings.demo_user_password = "staging-" + secrets.token_urlsafe(24)
        generated = True
    with SessionLocal() as db:
        user = ensure_demo(db, reset=args.reset)
    output = {
        "status": "completed",
        "fixtureVersion": settings.demo_dataset_version,
        "email": settings.demo_user_email,
        "userIdIncluded": False,
        "passwordGenerated": generated,
        "passwordIncluded": bool(args.print_local_password),
    }
    if args.print_local_password:
        output["localPassword"] = settings.demo_user_password
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
