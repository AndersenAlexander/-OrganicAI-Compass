from __future__ import annotations

import json
from pathlib import Path

from app.services.release_readiness import release_readiness_summary


def main() -> int:
    report = release_readiness_summary()
    out = Path("..") / "reports" / "provider-validation" / "release-readiness.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
