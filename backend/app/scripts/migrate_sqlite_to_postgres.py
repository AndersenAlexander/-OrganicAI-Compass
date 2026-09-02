from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.sqlite_to_postgres import migrate_sqlite_to_postgres


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely migrate data from SQLite to PostgreSQL.")
    parser.add_argument("--source", default="./organicai.db")
    parser.add_argument("--target-env", "--target-url-env", dest="target_env", default="DATABASE_URL")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--allow-production-target", action="store_true")
    parser.add_argument("--allow-non-empty", action="store_true")
    args = parser.parse_args()
    apply = args.apply and not args.dry_run
    try:
        report = migrate_sqlite_to_postgres(
            Path(args.source),
            args.target_env,
            apply=apply,
            allow_production_target=args.allow_production_target,
            allow_non_empty=args.allow_non_empty,
        )
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": exc.__class__.__name__, "message": str(exc)}, indent=2))
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
