from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from app.core.time import utc_now_naive
from pathlib import Path
from time import perf_counter

from openai import AsyncOpenAI

from app.config import get_settings
from app.database import SessionLocal
from app.models.provider_operations import ProviderVerificationRun
from app.services.secret_readiness import safe_fingerprint


def _record(provider: str, verification_type: str, mode: str, status: str, summary: dict, failure_code: str | None = None) -> None:
    with SessionLocal() as db:
        db.add(
            ProviderVerificationRun(
                provider=provider,
                verification_type=verification_type,
                execution_mode=mode,
                status=status,
                started_at=utc_now_naive(),
                completed_at=utc_now_naive(),
                configuration_fingerprint=summary.get("configurationFingerprint"),
                result_summary_json=summary,
                failure_code=failure_code,
            )
        )
        db.commit()


async def run(mode: str) -> dict:
    settings = get_settings()
    configured = bool(settings.active_openai_api_key)
    base = {
        "provider": "OpenAI",
        "mode": mode,
        "configured": configured,
        "trainingOptInStatus": settings.openai_training_opt_in_status,
        "abuseMonitoringMode": settings.openai_abuse_monitoring_mode,
        "dataResidency": settings.openai_data_residency_region,
        "dataControlsVerified": bool(settings.openai_project_data_controls_verified and settings.openai_data_controls_verified_at),
        "personalDataUsed": False,
        "promptContentStored": False,
        "answerContentStored": False,
        "configurationFingerprint": safe_fingerprint(settings.active_openai_api_key),
    }
    if mode == "offline":
        result = {**base, "status": "offline", "connectivity": "not-executed", "storeFalseEnforced": True}
        _record("OpenAI", "offline", mode, "completed", result)
        return result
    if mode == "live-read-only":
        if not settings.live_provider_validation_enabled or not configured:
            result = {**base, "status": "not-executed", "reason": "LIVE_PROVIDER_VALIDATION_ENABLED or OPENAI_API_KEY missing"}
            _record("OpenAI", "read-only", mode, "skipped", result)
            return result
        started = perf_counter()
        try:
            client = AsyncOpenAI(api_key=settings.active_openai_api_key, timeout=20.0, max_retries=1)
            models = await client.models.list()
            result = {**base, "status": "completed", "connectivity": "verified", "modelCountObserved": len(models.data), "latencyMs": int((perf_counter() - started) * 1000)}
            _record("OpenAI", "read-only", mode, "completed", result)
            return result
        except Exception:
            result = {**base, "status": "failed", "connectivity": "failed", "failureCode": "OPENAI_CONNECTIVITY_FAILED"}
            _record("OpenAI", "read-only", mode, "failed", result, "OPENAI_CONNECTIVITY_FAILED")
            return result
    if not (settings.live_provider_validation_enabled and settings.live_provider_write_validation_enabled and settings.openai_live_canary_enabled and configured):
        result = {**base, "status": "not-executed", "reason": "live write flags or OPENAI_API_KEY missing"}
        _record("OpenAI", "canary", mode, "skipped", result)
        return result
    started = perf_counter()
    try:
        client = AsyncOpenAI(api_key=settings.active_openai_api_key, timeout=20.0, max_retries=1)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Return the exact token: ORGANICAI_PROVIDER_OK"}],
            max_tokens=8,
            temperature=0,
            store=False,
        )
        ok = (response.choices[0].message.content or "").strip() == "ORGANICAI_PROVIDER_OK"
        result = {**base, "status": "completed" if ok else "failed", "connectivity": "verified", "model": response.model, "latencyMs": int((perf_counter() - started) * 1000), "storeFalseEnforced": True}
        _record("OpenAI", "canary", mode, result["status"], result, None if ok else "OPENAI_CANARY_MISMATCH")
        return result
    except Exception:
        result = {**base, "status": "failed", "connectivity": "failed", "failureCode": "OPENAI_CANARY_FAILED", "storeFalseEnforced": True}
        _record("OpenAI", "canary", mode, "failed", result, "OPENAI_CANARY_FAILED")
        return result


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--offline", action="store_true")
    group.add_argument("--live-read-only", action="store_true")
    group.add_argument("--live-canary", action="store_true")
    args = parser.parse_args()
    mode = "offline" if args.offline else "live-read-only" if args.live_read_only else "live-canary"
    report = asyncio.run(run(mode))
    out = Path("..") / "reports" / "provider-validation" / "openai-provider-status.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

