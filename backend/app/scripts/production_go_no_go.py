from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.production_readiness import production_go_no_go_report, readable_summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Production go/no-go checker. Does not print secret values.")
    parser.add_argument("--evidence-dir", default=None)
    parser.add_argument("--format", choices=["json", "text"], default="json")
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    report = production_go_no_go_report(args.evidence_dir)
    rendered = json.dumps(report, indent=2) if args.format == "json" else readable_summary(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered)
    return 0 if report["classifications"]["production_operationally_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
