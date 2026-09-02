from __future__ import annotations

import argparse
import json

from sqlalchemy import select

from app.database import SessionLocal
from app.models.privacy import DeletionSuppressionLedgerEntry


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply deletion suppression ledger to a restored database.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.dry_run:
        parser.error("Only --dry-run is supported by this local safeguard.")
    with SessionLocal() as db:
        rows = db.scalars(select(DeletionSuppressionLedgerEntry)).all()
    print(json.dumps({"dryRun": True, "ledgerEntries": len(rows), "suppressedSubjects": len({row.subject_hash for row in rows})}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
