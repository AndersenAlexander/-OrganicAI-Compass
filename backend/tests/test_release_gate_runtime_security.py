import asyncio
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config import Settings
from app.main import app
from app.routers import voice
from app.schemas import chat_schema
from app.schemas.chat_schema import ChatRequest
from app.services import http_middleware
from app.services.rate_limiter import MemoryRateLimiter, RateLimitExceeded, reset_rate_limiters
from app.services.runtime_configuration import check_runtime_configuration


def test_runtime_configuration_development_is_ready_without_provider_keys():
    settings = Settings(_env_file=None, secret_key="x" * 40, allowed_origins="http://127.0.0.1:5190", allowed_hosts="127.0.0.1,localhost,testserver")
    report = check_runtime_configuration(settings)
    assert report.environment == "development"
    assert report.ready is True
    assert any(check.key == "ELEVENLABS_LIVE_VOICE_ENABLED" and check.status == "disabled" for check in report.checks)


def test_openai_disabled_sentinel_is_reported_as_disabled():
    settings = Settings(_env_file=None, secret_key="x" * 40, openai_api_key="disabled")
    report = check_runtime_configuration(settings)
    openai_check = next(check for check in report.checks if check.key == "OPENAI_API_KEY")
    assert settings.active_openai_api_key is None
    assert openai_check.status == "disabled"


def test_runtime_configuration_production_weak_jwt_wildcard_cors_and_localhost_url_fail():
    weak = Settings(
        _env_file=None,
        app_env="production",
        secret_key="change-this-secret-key",
        public_backend_url="http://127.0.0.1:8020",
        allowed_origins="*",
        allowed_hosts="*",
    )
    report = check_runtime_configuration(weak)
    assert report.ready is False
    keys = {check.key for check in report.checks if check.status == "error"}
    assert {"SECRET_KEY", "PUBLIC_BACKEND_URL", "ALLOWED_ORIGINS", "ALLOWED_HOSTS"}.issubset(keys)


def test_runtime_configuration_elevenlabs_standard_default_and_isolated_requires_base_url():
    standard = Settings(_env_file=None, secret_key="x" * 40, elevenlabs_residency_mode="standard")
    standard_report = check_runtime_configuration(standard)
    assert not any(check.key == "ELEVENLABS_RESIDENCY_MODE" and check.status == "error" for check in standard_report.checks)

    isolated = Settings(
        _env_file=None,
        secret_key="x" * 40,
        elevenlabs_live_voice_enabled=True,
        elevenlabs_api_key="configured-key",
        elevenlabs_agent_id="agent_valid_123",
        elevenlabs_residency_mode="isolated-eu",
    )
    isolated_report = check_runtime_configuration(isolated)
    assert isolated_report.ready is False
    assert any(check.key == "ELEVENLABS_RESIDENCY_MODE" and check.status == "error" for check in isolated_report.checks)


def test_runtime_configuration_report_does_not_include_secret_values():
    settings = Settings(
        _env_file=None,
        secret_key="super-secret-value-that-must-not-appear",
        elevenlabs_api_key="elevenlabs-secret-value",
        elevenlabs_custom_llm_secret="custom-llm-secret-value",
        database_url="postgresql://example.test/db",
    )
    rendered = check_runtime_configuration(settings).model_dump_json()
    assert "super-secret-value" not in rendered
    assert "elevenlabs-secret-value" not in rendered
    assert "custom-llm-secret-value" not in rendered
    assert "postgresql://example.test/db" not in rendered


def test_health_liveness_readiness_and_request_id():
    client = TestClient(app)
    response = client.get("/health/live", headers={"X-Request-ID": "release-gate-request"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "release-gate-request"
    assert response.json()["requestId"] == "release-gate-request"

    ready = client.get("/health/ready")
    assert ready.status_code in {200, 503}
    assert "X-Request-ID" in ready.headers


def test_auth_validation_returns_a_safe_field_specific_message():
    client = TestClient(app)
    response = client.post(
        "/api/auth/register",
        json={"name": "Invalid Email", "email": "not-an-email", "password": "long enough password"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["message"] == "Enter a valid email address."


def test_security_headers_and_hsts_policy(monkeypatch):
    client = TestClient(app)
    response = client.get("/health/live")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Strict-Transport-Security" not in response.headers

    secure_app = FastAPI()

    @secure_app.get("/")
    async def root():
        return {"ok": True}

    monkeypatch.setattr(
        http_middleware,
        "get_settings",
        lambda: SimpleNamespace(app_env="production", hsts_enabled=True, log_format="json", log_level="INFO"),
    )
    secure_app.add_middleware(http_middleware.SecurityHeadersMiddleware)
    secure_client = TestClient(secure_app)
    assert "Strict-Transport-Security" in secure_client.get("/").headers


def test_cors_and_trusted_hosts():
    client = TestClient(app)
    for origin in ("http://127.0.0.1:5197", "http://127.0.0.1:5190"):
        preflight = client.options(
            "/health/live",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Host": "testserver",
            },
        )
        assert preflight.status_code == 200
        assert preflight.headers["access-control-allow-origin"] == origin

    rejected_origin = client.options(
        "/health/live",
        headers={
            "Origin": "http://unknown.example",
            "Access-Control-Request-Method": "GET",
            "Host": "testserver",
        },
    )
    assert "access-control-allow-origin" not in rejected_origin.headers

    invalid_host = client.get("/health/live", headers={"Host": "evil.example"})
    assert invalid_host.status_code == 400


def test_rate_limiter_allows_separate_buckets_and_returns_retry_after():
    limiter = MemoryRateLimiter()
    asyncio.run(limiter.check(category="chat", key="user:1", limit=1, window_seconds=60))
    asyncio.run(limiter.check(category="chat", key="user:2", limit=1, window_seconds=60))
    with pytest.raises(RateLimitExceeded) as exc:
        asyncio.run(limiter.check(category="chat", key="user:1", limit=1, window_seconds=60))
    assert exc.value.retry_after > 0
    reset_rate_limiters()


def test_audio_request_limits_invalid_mime_and_oversized_upload(monkeypatch):
    test_app = FastAPI()
    test_app.include_router(voice.router, prefix="/api/voice")
    monkeypatch.setattr(
        voice,
        "get_settings",
        lambda: SimpleNamespace(max_audio_upload_bytes=8, max_chat_message_chars=20, max_context_field_chars=100),
    )
    client = TestClient(test_app)
    response = client.post("/api/voice/transcribe", files={"file": ("voice.webm", b"abc", "audio/webm")})
    assert response.status_code == 401


def test_chat_message_and_context_limits(monkeypatch):
    monkeypatch.setattr(chat_schema, "get_settings", lambda: SimpleNamespace(max_chat_message_chars=5, max_context_field_chars=5))
    with pytest.raises(ValueError):
        ChatRequest(message="123456")
    with pytest.raises(ValueError):
        ChatRequest(message="1234", client_context={"field": "too-long"})


def test_standard_error_response_has_request_id_and_no_stack_trace():
    client = TestClient(app)
    response = client.post("/api/auth/register", json={}, headers={"X-Request-ID": "bad-auth-request"})
    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["requestId"] == "bad-auth-request"
    assert "Traceback" not in str(payload)
    assert "C:\\" not in str(payload)
