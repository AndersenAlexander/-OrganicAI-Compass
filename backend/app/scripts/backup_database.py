from __future__ import annotations

import argparse
import json

from app.config import get_settings
from app.services.database_admin import sqlite_path_from_url
from app.services.postgres_backup import backup_postgres_database
from app.services.sqlite_backup import backup_sqlite_database


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a verified database backup.")
    parser.add_argument("--source", choices=["sqlite", "postgres"], required=True)
    parser.add_argument("--prefix", default="")
    args = parser.parse_args()
    settings = get_settings()
    try:
        if args.source == "sqlite":
            result = backup_sqlite_database(sqlite_path_from_url(settings.database_url), settings.db_backup_directory, settings.app_version)
        else:
            result = backup_postgres_database(
                settings.database_url,
                settings.db_backup_directory,
                settings.app_version,
                prefix=args.prefix or "organicai-postgres",
            )
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": exc.__class__.__name__, "message": str(exc)}, indent=2))
        return 1
    print(json.dumps({"status": "success", **result}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
