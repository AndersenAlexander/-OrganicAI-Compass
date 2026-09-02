from __future__ import annotations

import json
import subprocess
import sys

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy.engine import make_url

from app.config import get_settings
from app.db.url import parse_database_url
from app.services.production_rehearsal import ACTIVE_DATABASE_NAME


def main() -> int:
    settings = get_settings()
    parsed = parse_database_url(settings.database_url)
    if settings.app_env != "production":
        print(json.dumps({"status": "blocked", "reason": "APP_ENV must be production"}))
        return 2
    if not settings.production_rehearsal_mode:
        print(json.dumps({"status": "blocked", "reason": "PRODUCTION_REHEARSAL_MODE must be true"}))
        return 2
    if parsed.dialect not in {"postgresql", "postgres"}:
        print(json.dumps({"status": "blocked", "reason": "Production rehearsal refuses non-PostgreSQL targets"}))
        return 2
    database_name = make_url(settings.database_url).database
    if database_name != ACTIVE_DATABASE_NAME:
        print(json.dumps({"status": "blocked", "reason": "Production rehearsal database mismatch"}))
        return 2
    source_heads = ScriptDirectory.from_config(Config("alembic.ini")).get_heads()
    if len(source_heads) != 1:
        print(json.dumps({"status": "blocked", "reason": "Alembic source must contain exactly one head", "sourceHeadCount": len(source_heads)}))
        return 2
    expected_head = source_heads[0]
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    current = subprocess.run([sys.executable, "-m", "alembic", "current"], check=True, capture_output=True, text=True)
    ok = expected_head in current.stdout
    print(json.dumps({"status": "completed" if ok else "failed", "currentContainsHead": ok, "expectedHead": expected_head, "targetDatabase": database_name}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
