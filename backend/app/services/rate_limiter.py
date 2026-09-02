from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Protocol

from fastapi import Request

from app.auth.security import decode_access_token
from app.config import Settings, get_settings


@dataclass
class RateLimitExceeded(Exception):
    category: str
    retry_after: int
    public_message: str = "Too many requests. Please wait and try again."


class RateLimiter(Protocol):
    async def check(self, *, category: str, key: str, limit: int, window_seconds: int) -> None:
        ...

    def reset(self) -> None:
        ...


class MemoryRateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    async def check(self, *, category: str, key: str, limit: int, window_seconds: int) -> None:
        now = time.monotonic()
        bucket = self._buckets[(category, key)]
        while bucket and now - bucket[0] >= window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            retry_after = max(1, int(window_seconds - (now - bucket[0])))
            raise RateLimitExceeded(category=category, retry_after=retry_after)
        bucket.append(now)

    def reset(self) -> None:
        self._buckets.clear()


memory_rate_limiter = MemoryRateLimiter()


RATE_LIMITS: dict[str, tuple[int, int]] = {
    "auth": (8, 60),
    "voice_token": (5, 60),
    "voice_legacy": (12, 60),
    "chat": (30, 60),
    "custom_llm": (120, 60),
    "rag_query": (30, 60),
    "rag_admin": (4, 300),
}


def reset_rate_limiters() -> None:
    memory_rate_limiter.reset()


def limiter_for_settings(settings: Settings | None = None) -> RateLimiter:
    settings = settings or get_settings()
    # Redis is a documented production target for Task 11/14. This task keeps the
    # concrete implementation in-memory and reports production limitations in readiness.
    return memory_rate_limiter


def category_for_request(method: str, path: str) -> str | None:
    if method.upper() != "POST":
        return None
    if path in {"/api/auth/login", "/api/auth/register"}:
        return "auth"
    if path == "/api/voice/conversation-token":
        return "voice_token"
    if path in {"/api/voice/transcribe", "/api/voice/speak"}:
        return "voice_legacy"
    if path == "/api/chat":
        return "chat"
    if path == "/api/elevenlabs/v1/chat/completions":
        return "custom_llm"
    if path == "/api/rag/ask":
        return "rag_query"
    if path == "/api/rag/reindex":
        return "rag_admin"
    return None


def _bearer_token(request: Request) -> str | None:
    header = request.headers.get("authorization") or ""
    scheme, _, token = header.partition(" ")
    if scheme.lower() == "bearer" and token:
        return token
    return None


def _client_ip(request: Request, settings: Settings) -> str:
    if settings.trust_proxy_headers:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()[:80]
    return request.client.host if request.client else "unknown"


def rate_limit_key(request: Request, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    token = _bearer_token(request)
    if token:
        try:
            payload = decode_access_token(token)
            user_id = str(payload.get("sub") or "")
            if user_id:
                return f"user:{user_id}"
        except ValueError:
            pass
    return f"ip:{_client_ip(request, settings)}"


async def check_request_rate_limit(request: Request, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    category = category_for_request(request.method, request.url.path)
    if category is None:
        return
    limit, window_seconds = RATE_LIMITS[category]
    await limiter_for_settings(settings).check(
        category=category,
        key=rate_limit_key(request, settings),
        limit=limit,
        window_seconds=window_seconds,
    )
