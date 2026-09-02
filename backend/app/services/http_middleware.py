from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import get_settings
from app.core.time import utc_now
from app.db.transaction_observability import observe_request_transactions
from app.services.error_responses import error_response
from app.services.metrics import observe_http, set_active_requests
from app.services.rate_limiter import RateLimitExceeded, check_request_rate_limit

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,80}$")


def valid_request_id(value: str | None) -> bool:
    return bool(value and REQUEST_ID_PATTERN.fullmatch(value))


def configure_logging() -> None:
    settings = get_settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO), force=False)


def user_id_hash(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get("x-request-id")
        request_id = incoming if valid_request_id(incoming) else str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestBodyLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > settings.max_request_body_bytes:
                    return error_response(
                        request,
                        status_code=413,
                        code="REQUEST_BODY_TOO_LARGE",
                        message="The request body is too large.",
                    )
            except ValueError:
                return error_response(
                    request,
                    status_code=400,
                    code="INVALID_CONTENT_LENGTH",
                    message="Content-Length must be a valid integer.",
                )
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            await check_request_rate_limit(request)
        except RateLimitExceeded as error:
            return error_response(
                request,
                status_code=429,
                code="RATE_LIMITED",
                message=error.public_message,
                headers={"Retry-After": str(error.retry_after)},
            )
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        settings = get_settings()
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(self), geolocation=()")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self' data:; "
            "connect-src 'self' http://127.0.0.1:5197 http://localhost:5197 "
            "http://127.0.0.1:5190 http://localhost:5190 "
            "http://127.0.0.1:8020 http://localhost:8020 https://api.elevenlabs.io wss://*.elevenlabs.io https://*.elevenlabs.io; "
            "media-src 'self' blob:; "
            "worker-src 'self' blob:; "
            "frame-ancestors 'none'"
        )
        response.headers.setdefault("Content-Security-Policy-Report-Only", csp)
        if settings.app_env == "production" and settings.hsts_enabled:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started = time.perf_counter()
        request.state.request_started_perf_counter = started
        status_code = 500
        error_code = None
        set_active_requests(1)
        try:
            with observe_request_transactions(
                request_id=str(getattr(request.state, "request_id", "") or ""),
                route=request.url.path,
                method=request.method,
            ):
                response: Response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            error_code = "UNHANDLED_EXCEPTION"
            raise
        finally:
            settings = get_settings()
            duration_ms = int((time.perf_counter() - started) * 1000)
            observe_http(request.method, request.url.path, status_code, duration_ms)
            set_active_requests(-1)
            if settings.log_format == "json":
                record = {
                    "timestamp": utc_now().isoformat(),
                    "level": "INFO" if status_code < 500 else "ERROR",
                    "service": settings.otel_service_name,
                    "environment": settings.app_env,
                    "version": settings.app_version,
                    "request_id": getattr(request.state, "request_id", ""),
                    "trace_id": getattr(request.state, "trace_id", None),
                    "span_id": getattr(request.state, "span_id", None),
                    "method": request.method,
                    "route": request.url.path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "event_type": "http_request",
                    "error_code": error_code,
                    "user_reference_hash": None,
                    "session_reference_hash": None,
                }
                logging.getLogger("organicai.http").info(json.dumps(record, separators=(",", ":")))
            else:
                logging.getLogger("organicai.http").info(
                    "%s %s status=%s duration_ms=%s request_id=%s",
                    request.method,
                    request.url.path,
                    status_code,
                    duration_ms,
                    getattr(request.state, "request_id", ""),
                )
