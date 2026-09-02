from __future__ import annotations

import logging
import threading
import time
from contextlib import suppress
from uuid import uuid4

import httpx
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

_logger = logging.getLogger("organicai.telemetry")
_pending_threads: list[threading.Thread] = []
_pending_lock = threading.Lock()


def _now_unix_nano() -> int:
    return int(time.time() * 1_000_000_000)


def _safe_route(path: str) -> str:
    if path.startswith("/api/auth"):
        return "/api/auth"
    if path.startswith("/api/privacy"):
        return "/api/privacy"
    if path.startswith("/api/system"):
        return "/api/system"
    if path.startswith("/api"):
        return "/api"
    if path.startswith("/health"):
        return path
    return "/frontend"


def _trace_payload(service_name: str, trace_id: str, span_id: str, name: str, start_ns: int, end_ns: int, attributes: dict[str, str]) -> dict:
    attrs = [{"key": key, "value": {"stringValue": value}} for key, value in sorted(attributes.items())]
    return {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": service_name}},
                    ]
                },
                "scopeSpans": [
                    {
                        "scope": {"name": "organicai.local"},
                        "spans": [
                            {
                                "traceId": trace_id,
                                "spanId": span_id,
                                "name": name,
                                "kind": 2,
                                "startTimeUnixNano": str(start_ns),
                                "endTimeUnixNano": str(end_ns),
                                "attributes": attrs,
                                "status": {"code": 1},
                            }
                        ],
                    }
                ],
            }
        ]
    }


def export_span(trace_id: str, span_id: str, name: str, start_ns: int, end_ns: int, attributes: dict[str, str]) -> bool:
    settings = get_settings()
    if not settings.otel_enabled or not settings.otel_exporter_otlp_endpoint:
        return False
    endpoint = settings.otel_exporter_otlp_endpoint.rstrip("/") + "/v1/traces"
    payload = _trace_payload(settings.otel_service_name, trace_id, span_id, name, start_ns, end_ns, attributes)
    try:
        with httpx.Client(timeout=2.0) as client:
            response = client.post(endpoint, json=payload)
            return response.status_code < 300
    except Exception as exc:
        _logger.warning(
            "otel_export_failed",
            extra={
                "event_type": "otel_export_failed",
                "reason": exc.__class__.__name__,
            },
        )
        return False


def export_span_async(trace_id: str, span_id: str, name: str, start_ns: int, end_ns: int, attributes: dict[str, str]) -> None:
    settings = get_settings()
    if not settings.otel_enabled:
        return
    thread = threading.Thread(
        target=export_span,
        args=(trace_id, span_id, name, start_ns, end_ns, attributes),
        daemon=True,
    )
    with _pending_lock:
        _pending_threads.append(thread)
    thread.start()


def flush_telemetry(timeout_seconds: float = 5.0) -> int:
    deadline = time.monotonic() + timeout_seconds
    with _pending_lock:
        threads = list(_pending_threads)
    completed = 0
    for thread in threads:
        remaining = max(0.0, deadline - time.monotonic())
        if remaining <= 0:
            break
        with suppress(RuntimeError):
            thread.join(timeout=remaining)
        if not thread.is_alive():
            completed += 1
    with _pending_lock:
        _pending_threads[:] = [thread for thread in _pending_threads if thread.is_alive()]
    return completed


def emit_validation_span(name: str, attributes: dict[str, str] | None = None) -> tuple[str, str]:
    trace_id = uuid4().hex
    span_id = uuid4().hex[:16]
    start_ns = _now_unix_nano()
    end_ns = _now_unix_nano()
    export_span_async(trace_id, span_id, name, start_ns, end_ns, attributes or {})
    return trace_id, span_id


class OpenTelemetryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = uuid4().hex
        span_id = uuid4().hex[:16]
        request.state.trace_id = trace_id
        request.state.span_id = span_id
        start_ns = _now_unix_nano()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["Traceparent"] = f"00-{trace_id}-{span_id}-01"
            return response
        finally:
            end_ns = _now_unix_nano()
            export_span_async(
                trace_id,
                span_id,
                "HTTP " + _safe_route(request.url.path),
                start_ns,
                end_ns,
                {
                    "http.request.method": request.method,
                    "http.route": _safe_route(request.url.path),
                    "http.response.status_code": str(status_code),
                },
            )
