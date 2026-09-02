from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

import httpx

from app.config import get_settings
from app.services.providers.elevenlabs_privacy import retention_summary
from app.services.secret_readiness import safe_fingerprint


async def inspect(mode: str) -> dict:
    settings = get_settings()
    report = {
        "provider": "ElevenLabs",
        "mode": mode,
        "configured": bool(settings.elevenlabs_api_key and settings.elevenlabs_agent_id),
        "agentIdFingerprint": safe_fingerprint(settings.elevenlabs_agent_id),
        "connectivity": "not-executed",
        "privacy": retention_summary(),
        "webhookConfigured": bool(settings.elevenlabs_post_call_webhook_enabled and settings.elevenlabs_webhook_secret),
        "audioWebhookEnabled": False,
        "manualReviewRequired": True,
        "secretValuesIncluded": False,
    }
    if mode == "live-read-only" and settings.live_provider_validation_enabled and report["configured"]:
        try:
            url = f"{settings.elevenlabs_api_base_url.rstrip('/')}/v1/convai/agents/{settings.elevenlabs_agent_id}"
            async with httpx.AsyncClient(timeout=settings.elevenlabs_request_timeout_seconds) as client:
                response = await client.get(url, headers={"xi-api-key": settings.elevenlabs_api_key})
            report["connectivity"] = "verified" if response.status_code == 200 else "failed"
            report["statusCodeClass"] = f"{response.status_code // 100}xx"
        except httpx.HTTPError:
            report["connectivity"] = "failed"
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--live-read-only", action="store_true")
    args = parser.parse_args()
    mode = "live-read-only" if args.live_read_only else "offline"
    report = asyncio.run(inspect(mode))
    out = Path("..") / "reports" / "provider-validation" / "elevenlabs-privacy-status.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out.parent / "elevenlabs-provider-status.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
