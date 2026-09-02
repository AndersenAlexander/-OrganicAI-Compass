from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

from app.config import get_settings
from app.core.time import ensure_utc, utc_now
from app.services.database_admin import resolve_backend_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune old database backups. Dry-run by default.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    backup_dir = resolve_backend_path(settings.db_backup_directory)
    cutoff = utc_now() - timedelta(days=settings.db_backup_retention_days)
    manifests = sorted(backup_dir.glob("*.manifest.json")) if backup_dir.exists() else []
    valid = []
    invalid = []
    for manifest in manifests:
        try:
            created = ensure_utc(datetime.fromisoformat(json.loads(manifest.read_text(encoding="utf-8"))["createdAt"]))
            valid.append((manifest, created))
        except Exception:
            invalid.append(manifest.name)
    latest_valid = max(valid, key=lambda item: item[1])[0] if valid else None
    candidates = [manifest for manifest, created in valid if created < cutoff and manifest != latest_valid]
    deleted = []
    if args.apply:
        for manifest in candidates:
            backup_name = json.loads(manifest.read_text(encoding="utf-8")).get("fileName")
            backup_path = backup_dir / backup_name if backup_name else None
            if backup_path and backup_path.exists():
                backup_path.unlink()
            manifest.unlink()
            deleted.append(manifest.name)
    print(
        json.dumps(
            {
                "status": "applied" if args.apply else "dry_run",
                "candidates": [item.name for item in candidates],
                "deleted": deleted,
                "invalidManifests": invalid,
                "latestValidKept": latest_valid.name if latest_valid else None,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
