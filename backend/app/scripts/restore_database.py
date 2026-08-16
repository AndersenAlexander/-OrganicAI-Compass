from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from app.config import get_settings
from app.services.postgres_restore import restore_postgres_backup


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore a PostgreSQL backup into an explicit target.")
    parser.add_argument("--backup", required=True)
    parser.add_argument("--target-url-env", default="RESTORE_DATABASE_URL")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--allow-active-target", action="store_true")
    parser.add_argument("--allow-non-empty", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    if args.dry_run and args.apply:
        print(json.dumps({"status": "failed", "error": "INVALID_ARGUMENTS", "message": "--dry-run and --apply are mutually exclusive."}, indent=2))
        return 1
    target_url = os.environ.get(args.target_url_env)
    if not target_url:
        print(json.dumps({"status": "failed", "error": "TARGET_URL_MISSING"}, indent=2))
        return 1
    try:
        result = restore_postgres_backup(
            Path(args.backup),
            target_url,
            active_database_url=settings.database_url,
            apply=args.apply,
            allow_active_target=args.allow_active_target,
            allow_non_empty=args.allow_non_empty,
        )
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": exc.__class__.__name__, "message": str(exc)}, indent=2))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
