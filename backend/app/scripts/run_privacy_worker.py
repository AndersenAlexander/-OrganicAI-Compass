from __future__ import annotations

import argparse
import json

from app.database import SessionLocal
from app.privacy.service import retention_dry_run


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one privacy worker pass.")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if not args.once:
        parser.error("Only --once is supported for the local release-gate worker.")
    with SessionLocal() as db:
        result = retention_dry_run(db)
    print(json.dumps({"status": "completed", "retention": result, "providerDeletion": "not-run"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
