from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from urllib.parse import urlparse
from typing import Any

import httpx

from app.config import get_settings
from app.services.runtime_configuration import (
    BlockingIssue,
    custom_llm_public_url,
    elevenlabs_blocking_issues,
    elevenlabs_residency_issue,
    is_placeholder,
    is_private_or_local_url,
)

DEFAULT_API_BASE_URL = "https://api.elevenlabs.io"
TOKEN_LIMIT_WINDOW_SECONDS = 60
TOKEN_LIMIT_MAX_REQUESTS = 5


@dataclass
class ElevenLabsConversationError(Exception):
    public_message: str
    status_code: int


_token_attempts: dict[str, deque[float]] = defaultdict(deque)


def _setting(settings: Any, name: str, default: Any = None) -> Any:
    return getattr(settings, name, default)


def conversation_token_url(settings: Any | None = None) -> str:
    settings = settings or get_settings()
    base_url = str(_setting(settings, "elevenlabs_api_base_url", DEFAULT_API_BASE_URL) or DEFAULT_API_BASE_URL).rstrip("/")
    return f"{base_url}/v1/convai/conversation/token"


def client_server_location(settings: Any | None = None) -> str:
    settings = settings or get_settings()
    mode = _setting(settings, "elevenlabs_residency_mode", "standard")
    if mode == "isolated-eu":
        return "eu-residency"
    if mode == "isolated-in":
        return "in-residency"
    if mode == "isolated-sg":
        return "sg-residency"
    legacy = str(_setting(settings, "elevenlabs_server_location", "") or "")
    return legacy if legacy not in {"eu-residency", "in-residency", "sg-residency"} else ""


def _public_backend_reachable(settings: Any) -> bool:
    public_url = _setting(settings, "public_backend_url", None)
    return bool(public_url and not is_private_or_local_url(public_url))


def live_voice_status() -> dict[str, Any]:
    settings = get_settings()
    issues = elevenlabs_blocking_issues(settings)
    blocking = [issue.model_dump() if isinstance(issue, BlockingIssue) else issue for issue in issues]
    api_key_configured = bool(_setting(settings, "elevenlabs_api_key", None))
    agent_configured = bool(_setting(settings, "elevenlabs_agent_id", None) and not is_placeholder(_setting(settings, "elevenlabs_agent_id", None)))
    custom_llm_configured = bool(
        _setting(settings, "elevenlabs_custom_llm_secret", None)
        and not is_placeholder(_setting(settings, "elevenlabs_custom_llm_secret", None))
        and not elevenlabs_residency_issue(settings)
        and (not _setting(settings, "elevenlabs_custom_llm_enabled", False) or custom_llm_public_url(settings))
    )
    live_configured = bool(
        api_key_configured
        and agent_configured
        and not elevenlabs_residency_issue(settings)
    )
    return {
        "provider": "elevenlabs",
        "liveVoiceEnabled": bool(_setting(settings, "elevenlabs_live_voice_enabled", False)),
        "liveVoiceConfigured": live_configured,
        "customLlmEnabled": bool(_setting(settings, "elevenlabs_custom_llm_enabled", False)),
        "customLlmConfigured": custom_llm_configured,
        "legacyFallbackEnabled": bool(_setting(settings, "elevenlabs_legacy_voice_fallback_enabled", True)),
        "agentIdConfigured": agent_configured,
        "apiKeyConfigured": api_key_configured,
        "serverLocation": client_server_location(settings),
        "residencyMode": _setting(settings, "elevenlabs_residency_mode", "standard"),
        "environment": _setting(settings, "elevenlabs_environment", "production"),
        "publicBackendReachable": _public_backend_reachable(settings),
        "blockingIssues": blocking,
    }


def check_token_rate_limit(participant_name: str, now: float | None = None) -> None:
    current_time = now if now is not None else time.monotonic()
    attempts = _token_attempts[participant_name]
    while attempts and current_time - attempts[0] > TOKEN_LIMIT_WINDOW_SECONDS:
        attempts.popleft()
    if len(attempts) >= TOKEN_LIMIT_MAX_REQUESTS:
        raise ElevenLabsConversationError(
            "Too many live voice sessions were requested. Wait a minute and try again.",
            429,
        )
    attempts.append(current_time)


def clear_token_rate_limit() -> None:
    _token_attempts.clear()


def _validate_token_payload(payload: Any) -> dict[str, str]:
    if not isinstance(payload, dict):
        raise ElevenLabsConversationError("ElevenLabs returned an invalid token response.", 502)
    token = payload.get("token")
    conversation_id = payload.get("conversation_id")
    if not isinstance(token, str) or not token.strip():
        raise ElevenLabsConversationError("ElevenLabs returned an invalid token response.", 502)
    if not isinstance(conversation_id, str) or not conversation_id.strip():
        raise ElevenLabsConversationError("ElevenLabs returned an invalid token response.", 502)
    return {"token": token, "conversation_id": conversation_id}


def _provider_error(status_code: int) -> ElevenLabsConversationError:
    if status_code in {401, 403}:
        return ElevenLabsConversationError("ElevenLabs authentication failed.", 503)
    if status_code == 404:
        return ElevenLabsConversationError("The configured ElevenLabs agent was not found.", 503)
    if status_code == 422:
        return ElevenLabsConversationError("ElevenLabs rejected the conversation token request.", 502)
    if status_code == 429:
        return ElevenLabsConversationError("ElevenLabs rate limited the voice request.", 429)
    if status_code >= 500:
        return ElevenLabsConversationError("ElevenLabs is temporarily unavailable.", 503)
    return ElevenLabsConversationError("ElevenLabs could not create a conversation token.", 503)


async def get_conversation_token(*, participant_name: str) -> dict[str, str]:
    settings = get_settings()
    if not settings.elevenlabs_live_voice_enabled:
        raise ElevenLabsConversationError("Live voice conversation is disabled.", 409)
    if not settings.elevenlabs_api_key:
        raise ElevenLabsConversationError("ElevenLabs API key is not configured.", 503)
    if not settings.elevenlabs_agent_id:
        raise ElevenLabsConversationError("ElevenLabs agent ID is not configured.", 503)
    residency_issue = elevenlabs_residency_issue(settings)
    if residency_issue:
        raise ElevenLabsConversationError(residency_issue.message, 503)

    params = {
        "agent_id": settings.elevenlabs_agent_id,
        "participant_name": participant_name,
        "environment": settings.elevenlabs_environment,
    }
    headers = {"xi-api-key": settings.elevenlabs_api_key}

    try:
        async with httpx.AsyncClient(timeout=settings.elevenlabs_request_timeout_seconds) as client:
            response = await client.get(conversation_token_url(settings), params=params, headers=headers)
    except httpx.TimeoutException as error:
        raise ElevenLabsConversationError("ElevenLabs did not respond in time.", 503) from error
    except httpx.HTTPError as error:
        raise ElevenLabsConversationError("ElevenLabs is temporarily unavailable.", 503) from error

    if response.status_code >= 400:
        raise _provider_error(response.status_code)

    try:
        payload = response.json()
    except ValueError as error:
        raise ElevenLabsConversationError("ElevenLabs returned an invalid token response.", 502) from error

    return _validate_token_payload(payload)
