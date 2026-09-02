from __future__ import annotations

from dataclasses import dataclass

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.interview_journey import VoiceProviderSession
from app.models.provider_operations import OperationalJobRun
from app.services.token_hashing import hash_secret


@dataclass(frozen=True)
class ProviderDeletionResult:
    status: str
    capability: str
    error_code: str | None = None


def retention_summary() -> dict[str, str]:
    settings = get_settings()
    return {
        "provider": "ElevenLabs",
        "retentionStatus": settings.elevenlabs_retention_status,
        "audioSavingStatus": settings.elevenlabs_audio_saving_status,
        "zeroRetentionStatus": settings.elevenlabs_zero_retention_status,
        "deletionCapability": "direct-api-delete" if settings.elevenlabs_provider_deletion_enabled else "manual-provider-request",
    }


async def delete_conversation(conversation_id: str) -> ProviderDeletionResult:
    settings = get_settings()
    if not settings.elevenlabs_provider_deletion_enabled:
        return ProviderDeletionResult(status="not-configured", capability="manual-provider-request")
    if not settings.elevenlabs_api_key:
        return ProviderDeletionResult(status="failed", capability="direct-api-delete", error_code="PROVIDER_KEY_MISSING")
    url = f"{settings.elevenlabs_api_base_url.rstrip('/')}/v1/convai/conversations/{conversation_id}"
    try:
        async with httpx.AsyncClient(timeout=settings.elevenlabs_request_timeout_seconds) as client:
            response = await client.delete(url, headers={"xi-api-key": settings.elevenlabs_api_key})
        if response.status_code in {200, 202, 204, 404}:
            return ProviderDeletionResult(status="completed", capability="direct-api-delete")
        if response.status_code == 429:
            return ProviderDeletionResult(status="failed", capability="direct-api-delete", error_code="RATE_LIMITED")
        return ProviderDeletionResult(status="failed", capability="direct-api-delete", error_code="PROVIDER_ERROR")
    except httpx.HTTPError:
        return ProviderDeletionResult(status="failed", capability="direct-api-delete", error_code="PROVIDER_UNAVAILABLE")


async def get_conversation_status(conversation_id: str) -> dict:
    settings = get_settings()
    if not settings.elevenlabs_api_key:
        return {"status": "not-configured", "configured": False}
    url = f"{settings.elevenlabs_api_base_url.rstrip('/')}/v1/convai/conversations/{conversation_id}"
    try:
        async with httpx.AsyncClient(timeout=settings.elevenlabs_request_timeout_seconds) as client:
            response = await client.get(url, headers={"xi-api-key": settings.elevenlabs_api_key})
        if response.status_code == 404:
            return {"status": "not-found", "configured": True}
        if response.status_code == 403:
            return {"status": "forbidden", "configured": True}
        if response.status_code == 429:
            return {"status": "rate-limited", "configured": True}
        if response.status_code >= 400:
            return {"status": "failed", "configured": True}
        data = response.json()
        return {
            "status": "found",
            "configured": True,
            "agentIdFingerprint": hash_secret(str(data.get("agent_id") or data.get("agentId") or ""))[:12] if data.get("agent_id") or data.get("agentId") else None,
            "conversationIdFingerprint": hash_secret(conversation_id)[:12],
        }
    except httpx.TimeoutException:
        return {"status": "failed", "configured": True, "failureCode": "TIMEOUT"}
    except httpx.HTTPError:
        return {"status": "failed", "configured": True, "failureCode": "PROVIDER_UNAVAILABLE"}


def is_disposable_test_conversation(conversation_id: str) -> bool:
    settings = get_settings()
    return (
        settings.live_provider_validation_enabled
        and settings.live_provider_write_validation_enabled
        and settings.elevenlabs_real_deletion_test_enabled
        and bool(settings.elevenlabs_test_conversation_id)
        and conversation_id == settings.elevenlabs_test_conversation_id
        and ("test" in conversation_id.lower() or "disposable" in conversation_id.lower())
    )


async def validate_disposable_conversation_deletion(db: Session) -> dict:
    settings = get_settings()
    conversation_id = settings.elevenlabs_test_conversation_id
    run = OperationalJobRun(job_type="provider-deletion", status="started", failure_summary_json={}, worker_id_hash=hash_secret("elevenlabs-disposable-delete"))
    db.add(run)
    db.flush()
    if not is_disposable_test_conversation(conversation_id):
        run.status = "skipped"
        run.failure_summary_json = {"reason": "no approved disposable conversation"}
        db.commit()
        return {"status": "not-executed", "reason": "no approved disposable conversation"}
    linked = db.scalar(select(VoiceProviderSession).where(VoiceProviderSession.provider_session_id == conversation_id))
    if linked:
        run.status = "failed"
        run.failure_summary_json = {"reason": "conversation linked to local user record"}
        db.commit()
        return {"status": "failed", "reason": "conversation linked to local user record"}
    before = await get_conversation_status(conversation_id)
    if before["status"] not in {"found", "not-found"}:
        run.status = "failed"
        run.failure_summary_json = {"reason": before["status"]}
        db.commit()
        return {"status": "failed", "reason": before["status"]}
    result = await delete_conversation(conversation_id)
    after = await get_conversation_status(conversation_id)
    run.status = "completed" if result.status == "completed" and after["status"] in {"not-found", "found"} else "failed"
    run.processed_count = 1
    run.succeeded_count = 1 if run.status == "completed" else 0
    run.failed_count = 0 if run.status == "completed" else 1
    run.failure_summary_json = {"afterStatus": after["status"], "errorCode": result.error_code}
    db.commit()
    return {"status": run.status, "before": before["status"], "after": after["status"], "conversationIdFingerprint": hash_secret(conversation_id)[:12]}
