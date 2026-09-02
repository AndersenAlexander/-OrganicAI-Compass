from __future__ import annotations

import json

from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings
from app.main import app
from app.services.http_middleware import valid_request_id
from app.services.metrics import prometheus_text
from app.services.runtime_configuration import check_runtime_configuration
from app.services.telemetry import _now_unix_nano, _trace_payload, flush_telemetry


def test_request_id_accepts_strict_values_and_rejects_unsafe_values():
    assert valid_request_id("task13a-123_OK")
    assert not valid_request_id("../secret")
    assert not valid_request_id("x" * 81)


def test_metrics_endpoint_uses_safe_low_cardinality_labels():
    client = TestClient(app)
    response = client.get("/internal/metrics")
    assert response.status_code == 200
    text = response.text
    assert "organicai_http_requests_total" in text
    assert "email@" not in text
    assert "/api/privacy/summary/" not in text


def test_staging_configuration_fails_closed_for_sqlite_and_placeholder_secrets():
    settings = Settings(app_env="staging", database_url="sqlite:///./bad.db", secret_key="change-this-secret-key")
    report = check_runtime_configuration(settings)
    assert not report.ready
    categories = {check.category for check in report.checks if check.status == "error"}
    assert "database" in categories
    assert "auth" in categories
    assert "privacy" in categories


def test_staging_configuration_accepts_postgres_and_required_keys():
    settings = Settings(
        app_env="staging",
        database_url="postgresql+psycopg2://user:pass@postgres:5432/organicai_staging",
        secret_key="x" * 48,
        data_export_encryption_key="e" * 48,
        deletion_ledger_hmac_key="d" * 48,
        allowed_origins="http://127.0.0.1:18080",
        staging_public_base_url="http://127.0.0.1:18080",
        email_delivery_driver="disabled",
        log_format="json",
        openai_api_key="",
        elevenlabs_api_key="",
        elevenlabs_live_voice_enabled=False,
        elevenlabs_custom_llm_enabled=False,
        elevenlabs_agent_id="",
    )
    report = check_runtime_configuration(settings)
    assert not any(check.status == "error" for check in report.checks)


def test_version_endpoint_reports_incomplete_provenance_without_git():
    client = TestClient(app)
    response = client.get("/api/system/version")
    assert response.status_code == 200
    payload = response.json()
    assert payload["provenanceStatus"] in {"complete", "incomplete"}
    assert "secret" not in json.dumps(payload).lower()


def test_otel_trace_payload_uses_only_sanitized_operational_attributes():
    payload = _trace_payload(
        "organicai-backend",
        "0" * 32,
        "1" * 16,
        "HTTP /api/privacy",
        _now_unix_nano(),
        _now_unix_nano(),
        {
            "http.request.method": "GET",
            "http.route": "/api/privacy",
            "http.response.status_code": "200",
            "db.system": "postgresql",
            "db.operation": "SELECT",
        },
    )
    text = json.dumps(payload).lower()
    assert "organicai-backend" in text
    for forbidden in ["authorization", "cookie", "access_token", "refresh_token", "email", "prompt", "transcript", "db.statement.parameters"]:
        assert forbidden not in text


def test_telemetry_flush_is_bounded_without_pending_exports():
    assert flush_telemetry(timeout_seconds=0.01) == 0
