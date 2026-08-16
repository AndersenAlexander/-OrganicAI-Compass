from __future__ import annotations

import json
import subprocess
import sys

from app.config import get_settings
from app.db.url import parse_database_url
from sqlalchemy.engine import make_url


def main() -> int:
    settings = get_settings()
    parsed = parse_database_url(settings.database_url)
    if settings.app_env != "staging":
        print(json.dumps({"status": "blocked", "reason": "APP_ENV must be staging"}))
        return 2
    if parsed.dialect not in {"postgresql", "postgres"}:
        print(json.dumps({"status": "blocked", "reason": "Staging migrator refuses non-PostgreSQL targets"}))
        return 2
    database_name = make_url(settings.database_url).database
    if database_name != "organicai_staging":
        print(json.dumps({"status": "blocked", "reason": "Staging migrator target database mismatch"}))
        return 2
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    current = subprocess.run([sys.executable, "-m", "alembic", "current"], check=True, capture_output=True, text=True)
    ok = "0004_provider_operations" in current.stdout
    print(json.dumps({"status": "completed" if ok else "failed", "currentContainsHead": ok, "targetDatabase": database_name}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
