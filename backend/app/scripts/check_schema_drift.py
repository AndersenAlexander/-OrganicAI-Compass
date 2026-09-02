from __future__ import annotations

import json

from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext

from app.database import Base, engine, import_models


def main() -> int:
    import_models()
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        diffs = compare_metadata(context, Base.metadata)
    sanitized = [str(diff[0]) for diff in diffs]
    payload = {"status": "passed" if not diffs else "failed", "diffCount": len(diffs), "diffTypes": sanitized}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not diffs else 1


if __name__ == "__main__":
    raise SystemExit(main())
