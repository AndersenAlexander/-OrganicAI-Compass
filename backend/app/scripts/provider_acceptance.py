from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.config import get_settings
from app.database import SessionLocal
from app.scripts.validate_openai_provider import run as run_openai_validation
from app.services.email.validation import email_configuration_status, send_validation_email


def _blocked(provider: str, reason: str) -> dict:
    return {
        "provider": provider,
        "status": "EXTERNAL MANUAL ACTION REQUIRED",
        "reason": reason,
        "secretValuesIncluded": False,
        "personalDataUsed": False,
    }


def _not_executed(provider: str) -> dict:
    return {
        "provider": provider,
        "status": "NOT EXECUTED",
        "reason": "Acceptance harness is disabled by default. Pass --execute and provider-specific approval flags to run.",
        "secretValuesIncluded": False,
        "personalDataUsed": False,
    }


async def run_provider(provider: str, execute: bool) -> dict:
    settings = get_settings()
    if not execute:
        return _not_executed(provider)
    if provider == "openai":
        if not (settings.real_provider_tests_enabled and settings.live_provider_validation_enabled and settings.active_openai_api_key):
            return _blocked("openai", "REAL_PROVIDER_TESTS_ENABLED, LIVE_PROVIDER_VALIDATION_ENABLED and OPENAI_API_KEY are required.")
        result = await run_openai_validation("live-read-only")
        return {**result, "personalDataUsed": False, "secretValuesIncluded": False, "costLimit": "read-only model listing"}
    if provider == "email":
        if not (settings.email_live_validation_enabled and settings.email_test_recipient):
            return _blocked("email", "EMAIL_LIVE_VALIDATION_ENABLED and EMAIL_TEST_RECIPIENT are required.")
        with SessionLocal() as db:
            result = send_validation_email(db, settings.email_test_recipient)
        return {**result, "personalDataUsed": False, "secretValuesIncluded": False}
    if provider == "elevenlabs":
        if not (
            settings.real_provider_tests_enabled
            and settings.live_provider_validation_enabled
            and settings.elevenlabs_live_voice_enabled
            and settings.elevenlabs_api_key
            and settings.elevenlabs_agent_id
        ):
            return _blocked("elevenlabs", "Real provider flags, ElevenLabs credentials and an approved live voice test are required.")
        return _blocked("elevenlabs", "Use the opt-in Playwright live voice real-provider test; it remains skipped by default for pull requests.")
    raise ValueError(f"Unsupported provider: {provider}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Opt-in real provider acceptance harness. Disabled by default.")
    parser.add_argument("--provider", choices=["openai", "elevenlabs", "email", "all"], default="all")
    parser.add_argument("--execute", action="store_true", help="Execute provider checks only when provider-specific flags and credentials are present.")
    parser.add_argument("--output", default="../reports/provider-validation/provider-acceptance.json")
    args = parser.parse_args()
    providers = ["openai", "elevenlabs", "email"] if args.provider == "all" else [args.provider]
    results = [asyncio.run(run_provider(provider, args.execute)) for provider in providers]
    payload = {
        "formatVersion": 1,
        "execute": args.execute,
        "status": "PASSED" if all(item.get("status") in {"completed", "accepted", "PASSED"} for item in results) else "BLOCKED",
        "results": results,
        "secretValuesIncluded": False,
        "personalDataUsed": False,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "PASSED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
