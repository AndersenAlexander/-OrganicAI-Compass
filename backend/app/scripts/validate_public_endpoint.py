from __future__ import annotations

import sys

import httpx

from app.config import get_settings
from app.services.runtime_configuration import is_private_or_local_url, is_https_url


def main() -> int:
    settings = get_settings()
    public_url = settings.public_backend_url
    if not public_url:
        print("PUBLIC_BACKEND_URL is missing.")
        return 1
    if is_private_or_local_url(public_url):
        print("PUBLIC_BACKEND_URL is local or private; public endpoint validation cannot pass.")
        return 1
    if settings.app_env == "production" and not is_https_url(public_url):
        print("PUBLIC_BACKEND_URL must be HTTPS in production.")
        return 1

    base = public_url.rstrip("/")
    ok = True
    for path in ["/health/live", "/health/ready"]:
        url = f"{base}{path}"
        try:
            response = httpx.get(url, timeout=10)
        except httpx.HTTPError as error:
            print(f"{path}: unavailable ({error.__class__.__name__})")
            ok = False
            continue
        print(f"{path}: HTTP {response.status_code}")
        ok = ok and response.status_code < 500
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
