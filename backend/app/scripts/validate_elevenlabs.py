from __future__ import annotations

import argparse
import asyncio
import re
import sys

from app.config import get_settings
from app.services.elevenlabs_conversation import ElevenLabsConversationError, conversation_token_url, get_conversation_token
from app.services.runtime_configuration import elevenlabs_blocking_issues, is_private_or_local_url


AGENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{6,160}$")


def _truncate(value: str) -> str:
    if len(value) <= 12:
        return "***"
    return f"{value[:6]}...{value[-4:]}"


def config_checks() -> tuple[bool, list[str]]:
    settings = get_settings()
    lines: list[str] = []
    ok = True
    lines.append(f"Environment: {settings.app_env}")
    lines.append(f"Live voice enabled: {settings.elevenlabs_live_voice_enabled}")
    lines.append(f"Residency mode: {settings.elevenlabs_residency_mode}")
    lines.append(f"Token endpoint host: {conversation_token_url(settings).split('/v1/')[0]}")
    provider_required = bool(settings.elevenlabs_live_voice_enabled)
    if settings.elevenlabs_agent_id and AGENT_ID_PATTERN.fullmatch(settings.elevenlabs_agent_id):
        lines.append("Agent ID format: ok")
    elif provider_required:
        ok = False
        lines.append("Agent ID format: invalid or missing")
    else:
        lines.append("Agent ID format: skipped because live voice is disabled")
    if not settings.elevenlabs_api_key:
        if provider_required:
            ok = False
            lines.append("API key: missing")
        else:
            lines.append("API key: skipped because live voice is disabled")
    else:
        lines.append("API key: configured")
    if settings.public_backend_url:
        lines.append("Public backend URL: local/private" if is_private_or_local_url(settings.public_backend_url) else "Public backend URL: public-looking")
    else:
        lines.append("Public backend URL: missing")
    issues = elevenlabs_blocking_issues(settings)
    for issue in issues:
        ok = False
        lines.append(f"Blocking issue: {issue.code}")
    return ok, lines


async def request_token() -> tuple[bool, str]:
    settings = get_settings()
    if not settings.real_provider_tests_enabled:
        return False, "Real provider tests are disabled. Set REAL_PROVIDER_TESTS_ENABLED=true to request a token."
    try:
        token = await get_conversation_token(participant_name="organicai-cli-validation")
    except ElevenLabsConversationError as error:
        if error.status_code == 429:
            return False, "Provider rate limit while requesting a token."
        if error.status_code == 503 and "authentication" in error.public_message.lower():
            return False, "Provider authentication failed."
        if error.status_code == 503 and "time" in error.public_message.lower():
            return False, "Provider timeout while requesting a token."
        return False, f"Provider validation failed: {error.public_message}"
    return True, f"Real token request succeeded. Conversation ID: {_truncate(token['conversation_id'])}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate OrganicAI ElevenLabs live voice configuration.")
    parser.add_argument("--request-token", action="store_true", help="Opt in to a real ElevenLabs conversation-token request.")
    args = parser.parse_args()

    ok, lines = config_checks()
    for line in lines:
        print(line)

    if args.request_token:
        real_ok, message = asyncio.run(request_token())
        print(message)
        ok = ok and real_ok
    else:
        print("Real token request: skipped")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
