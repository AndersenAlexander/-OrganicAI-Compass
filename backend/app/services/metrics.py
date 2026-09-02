from __future__ import annotations

import threading
import time
from collections import Counter

_lock = threading.Lock()
_request_count: Counter[tuple[str, str, str]] = Counter()
_duration_sum: Counter[tuple[str, str]] = Counter()
_active_requests = 0
_database_available = 0
_database_pool_checked_out = 0
_database_pool_available = 0
_database_pool_overflow = 0
_auth_events: Counter[tuple[str, str]] = Counter()
_privacy_jobs: Counter[tuple[str, str]] = Counter()
_provider_requests: Counter[tuple[str, str]] = Counter()
_provider_failures: Counter[tuple[str, str]] = Counter()
_provider_latency_sum: Counter[tuple[str, str]] = Counter()
_email_attempts: Counter[tuple[str, str]] = Counter()
_email_failures: Counter[tuple[str, str]] = Counter()
_websocket_active_connections = 0
_live_voice_active_sessions = 0
_worker_heartbeat: Counter[str] = Counter()
_worker_jobs: Counter[tuple[str, str]] = Counter()
_dead_letter_jobs: Counter[str] = Counter()
_webhook_signature_failures = 0
_webhook_duplicates = 0

ALLOWED_LABELS = {
    "method",
    "route",
    "status_class",
    "service",
    "job_type",
    "provider",
    "result",
    "environment",
}


def status_class(status_code: int) -> str:
    return f"{int(status_code / 100)}xx"


def observe_http(method: str, route: str, status_code: int, duration_ms: int) -> None:
    safe_route = route if route.startswith(("/api", "/health", "/internal")) else "/frontend"
    with _lock:
        _request_count[(method.upper(), safe_route, status_class(status_code))] += 1
        _duration_sum[(method.upper(), safe_route)] += duration_ms / 1000


def set_active_requests(delta: int) -> None:
    global _active_requests
    with _lock:
        _active_requests = max(0, _active_requests + delta)


def set_database_metrics(*, available: bool, checked_out: int = 0, available_connections: int = 0, overflow: int = 0) -> None:
    global _database_available, _database_pool_checked_out, _database_pool_available, _database_pool_overflow
    with _lock:
        _database_available = 1 if available else 0
        _database_pool_checked_out = max(0, checked_out)
        _database_pool_available = max(0, available_connections)
        _database_pool_overflow = max(0, overflow)


def record_auth_metric(event_type: str, result: str) -> None:
    safe_event = event_type if event_type in {"login", "refresh", "refresh_reuse", "logout", "session_revocation"} else "other"
    safe_result = result if result in {"success", "failure", "revoked"} else "other"
    with _lock:
        _auth_events[(safe_event, safe_result)] += 1


def record_privacy_job(job_type: str, result: str) -> None:
    safe_job = job_type if job_type in {"privacy-export", "account-deletion", "category-deletion", "provider-deletion", "retention", "research-withdrawal"} else "other"
    safe_result = result if result in {"queued", "running", "completed", "failed", "dead_letter"} else "other"
    with _lock:
        _privacy_jobs[(safe_job, safe_result)] += 1


def record_provider_request(provider: str, result: str, duration_ms: int = 0) -> None:
    safe_provider = provider if provider in {"openai", "elevenlabs", "email", "demo", "disabled"} else "other"
    safe_result = result if result in {"success", "failure", "skipped"} else "other"
    with _lock:
        _provider_requests[(safe_provider, safe_result)] += 1
        _provider_latency_sum[(safe_provider, safe_result)] += max(0, duration_ms) / 1000
        if safe_result == "failure":
            _provider_failures[(safe_provider, safe_result)] += 1


def record_email_attempt(provider: str, result: str) -> None:
    safe_provider = provider if provider in {"smtp", "development-outbox", "disabled"} else "other"
    safe_result = result if result in {"success", "failure", "skipped"} else "other"
    with _lock:
        _email_attempts[(safe_provider, safe_result)] += 1
        if safe_result == "failure":
            _email_failures[(safe_provider, safe_result)] += 1


def set_websocket_active(delta: int) -> None:
    global _websocket_active_connections
    with _lock:
        _websocket_active_connections = max(0, _websocket_active_connections + delta)


def set_live_voice_active(delta: int) -> None:
    global _live_voice_active_sessions
    with _lock:
        _live_voice_active_sessions = max(0, _live_voice_active_sessions + delta)


def record_worker_heartbeat(job_type: str) -> None:
    safe_job = job_type if job_type else "unknown"
    with _lock:
        _worker_heartbeat[safe_job] = int(time.time())


def record_worker_job(job_type: str, status: str) -> None:
    safe_job = job_type if job_type else "unknown"
    safe_status = status if status in {"queued", "running", "completed", "failed", "dead_letter", "lease_expired"} else "other"
    with _lock:
        _worker_jobs[(safe_job, safe_status)] += 1
        if safe_status == "dead_letter":
            _dead_letter_jobs[safe_job] += 1


def record_webhook_signature_failure() -> None:
    global _webhook_signature_failures
    with _lock:
        _webhook_signature_failures += 1


def record_webhook_duplicate() -> None:
    global _webhook_duplicates
    with _lock:
        _webhook_duplicates += 1


def prometheus_text() -> str:
    lines = [
        "# HELP organicai_http_requests_total HTTP requests by method, safe route, and status class.",
        "# TYPE organicai_http_requests_total counter",
    ]
    with _lock:
        for (method, route, cls), value in sorted(_request_count.items()):
            lines.append(f'organicai_http_requests_total{{method="{method}",route="{route}",status_class="{cls}"}} {value}')
        lines.extend(
            [
                "# HELP organicai_http_request_duration_seconds_sum HTTP request duration sum.",
                "# TYPE organicai_http_request_duration_seconds_sum counter",
            ]
        )
        for (method, route), value in sorted(_duration_sum.items()):
            lines.append(f'organicai_http_request_duration_seconds_sum{{method="{method}",route="{route}"}} {value:.6f}')
        lines.extend(
            [
                "# HELP organicai_http_active_requests Active HTTP requests.",
                "# TYPE organicai_http_active_requests gauge",
                f"organicai_http_active_requests {_active_requests}",
                "# HELP organicai_database_available Database availability.",
                "# TYPE organicai_database_available gauge",
                f"organicai_database_available {_database_available}",
                "# HELP organicai_database_pool_checked_out Checked-out database pool connections.",
                "# TYPE organicai_database_pool_checked_out gauge",
                f"organicai_database_pool_checked_out {_database_pool_checked_out}",
                "# HELP organicai_database_pool_available Available database pool connections.",
                "# TYPE organicai_database_pool_available gauge",
                f"organicai_database_pool_available {_database_pool_available}",
                "# HELP organicai_database_pool_overflow Database pool overflow connections.",
                "# TYPE organicai_database_pool_overflow gauge",
                f"organicai_database_pool_overflow {_database_pool_overflow}",
                "# HELP organicai_auth_events_total Authentication events.",
                "# TYPE organicai_auth_events_total counter",
            ]
        )
        for (event_type, result), value in sorted(_auth_events.items()):
            lines.append(f'organicai_auth_events_total{{service="backend",job_type="{event_type}",result="{result}"}} {value}')
        lines.extend(
            [
                "# HELP organicai_privacy_jobs_total Privacy and retention jobs by status.",
                "# TYPE organicai_privacy_jobs_total counter",
            ]
        )
        for (job_type, result), value in sorted(_privacy_jobs.items()):
            lines.append(f'organicai_privacy_jobs_total{{job_type="{job_type}",result="{result}"}} {value}')
        lines.extend(
            [
                "# HELP organicai_provider_requests_total Provider requests by provider and result.",
                "# TYPE organicai_provider_requests_total counter",
            ]
        )
        for (provider, result), value in sorted(_provider_requests.items()):
            lines.append(f'organicai_provider_requests_total{{provider="{provider}",result="{result}"}} {value}')
        lines.extend(
            [
                "# HELP organicai_provider_failures_total Provider failures by provider.",
                "# TYPE organicai_provider_failures_total counter",
            ]
        )
        for (provider, result), value in sorted(_provider_failures.items()):
            lines.append(f'organicai_provider_failures_total{{provider="{provider}",result="{result}"}} {value}')
        lines.extend(
            [
                "# HELP organicai_provider_latency_seconds_sum Provider latency sum by provider and result.",
                "# TYPE organicai_provider_latency_seconds_sum counter",
            ]
        )
        for (provider, result), value in sorted(_provider_latency_sum.items()):
            lines.append(f'organicai_provider_latency_seconds_sum{{provider="{provider}",result="{result}"}} {value:.6f}')
        lines.extend(
            [
                "# HELP organicai_email_send_attempts_total Email send attempts.",
                "# TYPE organicai_email_send_attempts_total counter",
            ]
        )
        for (provider, result), value in sorted(_email_attempts.items()):
            lines.append(f'organicai_email_send_attempts_total{{provider="{provider}",result="{result}"}} {value}')
        lines.extend(
            [
                "# HELP organicai_email_send_failures_total Email send failures.",
                "# TYPE organicai_email_send_failures_total counter",
            ]
        )
        for (provider, result), value in sorted(_email_failures.items()):
            lines.append(f'organicai_email_send_failures_total{{provider="{provider}",result="{result}"}} {value}')
        lines.extend(
            [
                "# HELP organicai_websocket_active_connections Active WebSocket connections.",
                "# TYPE organicai_websocket_active_connections gauge",
                f"organicai_websocket_active_connections {_websocket_active_connections}",
                "# HELP organicai_live_voice_active_sessions Active live voice sessions.",
                "# TYPE organicai_live_voice_active_sessions gauge",
                f"organicai_live_voice_active_sessions {_live_voice_active_sessions}",
                "# HELP organicai_worker_heartbeat_timestamp_seconds Latest worker heartbeat timestamp.",
                "# TYPE organicai_worker_heartbeat_timestamp_seconds gauge",
            ]
        )
        for job_type, value in sorted(_worker_heartbeat.items()):
            lines.append(f'organicai_worker_heartbeat_timestamp_seconds{{job_type="{job_type}"}} {value}')
        lines.extend(
            [
                "# HELP organicai_worker_jobs_total Worker jobs by type and status.",
                "# TYPE organicai_worker_jobs_total counter",
            ]
        )
        for (job_type, status), value in sorted(_worker_jobs.items()):
            lines.append(f'organicai_worker_jobs_total{{job_type="{job_type}",result="{status}"}} {value}')
        lines.extend(
            [
                "# HELP organicai_dead_letter_jobs_total Dead-letter worker jobs.",
                "# TYPE organicai_dead_letter_jobs_total counter",
            ]
        )
        for job_type, value in sorted(_dead_letter_jobs.items()):
            lines.append(f'organicai_dead_letter_jobs_total{{job_type="{job_type}"}} {value}')
        lines.extend(
            [
                "# HELP organicai_webhook_signature_failures_total Rejected provider webhooks with invalid signatures.",
                "# TYPE organicai_webhook_signature_failures_total counter",
                f"organicai_webhook_signature_failures_total {_webhook_signature_failures}",
                "# HELP organicai_webhook_duplicates_total Duplicate provider webhook deliveries.",
                "# TYPE organicai_webhook_duplicates_total counter",
                f"organicai_webhook_duplicates_total {_webhook_duplicates}",
                "# HELP organicai_build_info Safe build metadata.",
                "# TYPE organicai_build_info gauge",
                'organicai_build_info{service="backend"} 1',
            ]
        )
    return "\n".join(lines) + "\n"
