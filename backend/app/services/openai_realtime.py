from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import get_settings, resolve_active_openai_api_key


OPENAI_REALTIME_CALLS_URL = "https://api.openai.com/v1/realtime/calls"
DEFAULT_REALTIME_MODEL = "gpt-realtime-2.1"
DEFAULT_REALTIME_VOICE = "marin"

ORGANICAI_REALTIME_INSTRUCTIONS = """
You are OrganicAI Compass, a calm AI guide inside the OrganicAI Compass platform.
Speak naturally and concisely.
Your role in this prototype is to demonstrate conversational voice interaction and explain at a high level how OrganicAI Compass helps users explore their context, potential, direction, and next steps.
Do not claim access to personal data or platform capabilities that are not actually connected.
Keep responses relatively short so voice interaction feels responsive.
""".strip()


@dataclass
class OpenAIRealtimeSessionError(Exception):
    public_message: str
    status_code: int = 503


def _setting(settings: Any, name: str, default: Any) -> Any:
    return getattr(settings, name, default)


def realtime_session_config(settings: Any | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    model = str(_setting(settings, "openai_realtime_model", DEFAULT_REALTIME_MODEL) or DEFAULT_REALTIME_MODEL).strip()
    voice = str(_setting(settings, "openai_realtime_voice", DEFAULT_REALTIME_VOICE) or DEFAULT_REALTIME_VOICE).strip()
    return {
        "type": "realtime",
        "model": model,
        "instructions": ORGANICAI_REALTIME_INSTRUCTIONS,
        "audio": {
            "output": {
                "voice": voice,
            },
        },
    }


def _provider_error(status_code: int) -> OpenAIRealtimeSessionError:
    if status_code in {401, 403}:
        return OpenAIRealtimeSessionError("OpenAI realtime authentication failed.", 503)
    if status_code == 429:
        return OpenAIRealtimeSessionError("OpenAI realtime voice is rate limited. Try again shortly.", 429)
    if status_code in {400, 404, 409, 422}:
        return OpenAIRealtimeSessionError("OpenAI rejected the realtime session request.", 502)
    if status_code >= 500:
        return OpenAIRealtimeSessionError("OpenAI realtime voice is temporarily unavailable.", 503)
    return OpenAIRealtimeSessionError("OpenAI realtime voice could not start.", 503)


async def create_realtime_sdp_answer(sdp_offer: str, *, safety_identifier: str | None = None) -> str:
    settings = get_settings()
    api_key = resolve_active_openai_api_key(settings)
    if not api_key:
        raise OpenAIRealtimeSessionError("OpenAI realtime voice is not configured.", 503)

    timeout = float(_setting(settings, "openai_realtime_request_timeout_seconds", 20))
    headers = {"Authorization": f"Bearer {api_key}"}
    if safety_identifier:
        headers["OpenAI-Safety-Identifier"] = safety_identifier

    files = {
        "sdp": (None, sdp_offer, "application/sdp"),
        "session": (None, json.dumps(realtime_session_config(settings), separators=(",", ":")), "application/json"),
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(OPENAI_REALTIME_CALLS_URL, headers=headers, files=files)
    except httpx.TimeoutException as error:
        raise OpenAIRealtimeSessionError("OpenAI realtime voice did not respond in time.", 503) from error
    except httpx.HTTPError as error:
        raise OpenAIRealtimeSessionError("OpenAI realtime voice is temporarily unavailable.", 503) from error

    if response.status_code >= 400:
        raise _provider_error(response.status_code)

    answer = response.text.strip()
    if not answer.startswith("v=0"):
        raise OpenAIRealtimeSessionError("OpenAI returned an invalid realtime session response.", 502)
    return answer
