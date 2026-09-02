from __future__ import annotations

import argparse
import json

from app.database import SessionLocal
from app.privacy.service import retention_apply, retention_dry_run


def main() -> int:
    parser = argparse.ArgumentParser(description="Run privacy retention cleanup.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.dry_run == args.apply:
        parser.error("Choose exactly one of --dry-run or --apply.")
    with SessionLocal() as db:
        result = retention_apply(db) if args.apply else retention_dry_run(db)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
