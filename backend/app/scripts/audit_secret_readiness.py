from __future__ import annotations

import json

from app.services.secret_readiness import audit_secret_readiness


def main() -> int:
    print(json.dumps(audit_secret_readiness(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
