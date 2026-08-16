from __future__ import annotations

import argparse
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


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
    parser = argparse.ArgumentParser(description="Run local staging smoke checks without external providers.")
    parser.add_argument("--base-url", default="http://127.0.0.1:18080")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    checks = {
        "frontend": fetch(f"{base}/"),
        "health": fetch(f"{base}/health"),
        "liveness": fetch(f"{base}/health/live"),
        "readiness": fetch(f"{base}/health/ready"),
        "privacyUnauthorized": fetch(f"{base}/api/privacy/summary"),
        "websocketPath": fetch(f"{base}/api/voice/status"),
        "staticHealth": fetch(f"{base}/health.txt"),
    }
    checks["privacyUnauthorized"]["expected"] = 401
    result = {
        "baseUrl": base,
        "externalProvidersCalled": False,
        "status": "passed" if all(item["ok"] or item.get("expected") == item["status"] for item in checks.values()) else "failed",
        "checks": checks,
    }
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
