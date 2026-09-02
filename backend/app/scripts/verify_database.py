from __future__ import annotations

import json

from app.services.database_integrity import verify_database_integrity


def main() -> int:
    payload = verify_database_integrity()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "passed" else 4


if __name__ == "__main__":
    raise SystemExit(main())
