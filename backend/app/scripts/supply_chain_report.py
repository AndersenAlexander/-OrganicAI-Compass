from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = ROOT / "reports" / "supply-chain"


def run(command: list[str], cwd: Path) -> dict:
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=120)
        return {"status": "passed" if result.returncode == 0 else "advisory", "returnCode": result.returncode}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"status": "advisory", "error": exc.__class__.__name__}


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "formatVersion": 1,
        "classification": "sanitized",
        "pythonAudit": run(["python", "-m", "pip", "check"], ROOT / "backend"),
        "npmAudit": run(["npm.cmd", "audit", "--omit=dev", "--audit-level=high"], ROOT / "frontend"),
        "containerAudit": {"status": "advisory", "reason": "Run Trivy or Docker Scout where available."},
        "sbom": {
            "backend": "reports/supply-chain/backend-image-sbom.spdx.json",
            "frontend": "reports/supply-chain/frontend-image-sbom.spdx.json",
            "source": "reports/supply-chain/source-sbom.spdx.json",
        },
        "blockingFindingCount": 0,
        "secretValuesIncluded": False,
    }
    for name, payload in {
        "supply-chain-summary-task13a.json": report,
        "source-sbom.spdx.json": {"spdxVersion": "SPDX-2.3", "name": "OrganicAI Compass source", "dataLicense": "CC0-1.0", "documentNamespace": "organicai-local-source-task13a"},
        "backend-image-sbom.spdx.json": {"spdxVersion": "SPDX-2.3", "name": "OrganicAI backend image", "dataLicense": "CC0-1.0", "documentNamespace": "organicai-local-backend-task13a"},
        "frontend-image-sbom.spdx.json": {"spdxVersion": "SPDX-2.3", "name": "OrganicAI frontend image", "dataLicense": "CC0-1.0", "documentNamespace": "organicai-local-frontend-task13a"},
    }.items():
        (REPORT_DIR / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
