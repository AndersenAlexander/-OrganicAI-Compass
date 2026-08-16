from __future__ import annotations

import json
import os
import re
from pathlib import Path

from app.services.metrics import ALLOWED_LABELS, prometheus_text


LABEL_RE = re.compile(r"\{([^}]*)\}")
LABEL_NAME_RE = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)=")


def main() -> int:
    findings: list[dict[str, str]] = []
    metrics = prometheus_text()
    for line in metrics.splitlines():
        if not line or line.startswith("#") or "{" not in line:
            continue
        label_block = LABEL_RE.search(line)
        if not label_block:
            continue
        for label in LABEL_NAME_RE.findall(label_block.group(1)):
            if label not in ALLOWED_LABELS:
                findings.append({"metric": line.split("{", 1)[0], "label": label, "severity": "blocking"})

    report = {
        "formatVersion": 1,
        "blockingFindingCount": len([item for item in findings if item["severity"] == "blocking"]),
        "allowedLabels": sorted(ALLOWED_LABELS),
        "findings": findings,
        "secretValuesIncluded": False,
        "personalDataIncluded": False,
    }
    path = Path(os.environ.get("METRICS_CARDINALITY_REPORT_PATH", "/tmp/metrics-cardinality-audit.json"))
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except OSError:
        pass
    print(json.dumps(report, indent=2))
    return 1 if report["blockingFindingCount"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
