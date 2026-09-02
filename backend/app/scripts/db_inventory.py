from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.database_inventory import inventory_database


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a sanitized database inventory.")
    parser.add_argument("--output", help="Optional JSON output path.")
    args = parser.parse_args()
    payload = inventory_database()
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        print(
            json.dumps(
                {
                    "dialect": payload["dialect"],
                    "schemaVersion": payload["schemaVersion"],
                    "tableCount": payload["tableCount"],
                    "output": str(output),
                    "integrity": payload["integrity"],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
