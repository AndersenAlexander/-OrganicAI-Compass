from __future__ import annotations

import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def fetch(url: str, method: str = "GET") -> dict:
    try:
        req = Request(url, method=method)
        with urlopen(req, timeout=10) as response:
            body = response.read(2048).decode("utf-8", errors="replace")
            return {"status": response.status, "ok": 200 <= response.status < 400, "bodySample": body[:120]}
    except HTTPError as error:
        return {"status": error.code, "ok": False, "bodySample": error.read(512).decode("utf-8", errors="replace")}
    except URLError as error:
        return {"status": "unreachable", "ok": False, "bodySample": str(error.reason)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local production rehearsal smoke checks without external providers.")
    parser.add_argument("--base-url", default="http://127.0.0.1:28080")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    checks = {
        "frontend": fetch(f"{base}/"),
        "frontendStaticHealth": fetch(f"{base}/health.txt"),
        "health": fetch(f"{base}/health"),
        "liveness": fetch(f"{base}/health/live"),
        "readiness": fetch(f"{base}/health/ready"),
        "privacyUnauthorized": fetch(f"{base}/api/privacy/summary"),
        "voiceStatus": fetch(f"{base}/api/voice/status"),
        "internalMetricsBlocked": fetch(f"{base}/internal/metrics"),
        "observabilityPathBlocked": fetch(f"{base}/prometheus"),
    }
    checks["privacyUnauthorized"]["expected"] = 401
    checks["internalMetricsBlocked"]["expected"] = 404
    checks["observabilityPathBlocked"]["expected"] = 404
    passed = all(item["ok"] or item.get("expected") == item["status"] for item in checks.values())
    result = {
        "baseUrl": base,
        "status": "PASSED" if passed else "FAILED",
        "externalProvidersCalled": False,
        "realEmailSent": False,
        "checks": checks,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
