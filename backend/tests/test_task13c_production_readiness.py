from __future__ import annotations

import json
from types import SimpleNamespace

from app.config import Settings
from app.services.email.base import EmailMessage
from app.services.email.smtp_delivery import SmtpEmailDriver
from app.services.production_readiness import production_go_no_go_report
from app.services.runtime_configuration import check_runtime_configuration


def production_settings(**overrides) -> Settings:
    values = {
        "app_env": "production",
        "secret_key": "x" * 48,
        "database_url": "postgresql+psycopg2://organicai:strong-password@db.example.com:5432/organicai?sslmode=verify-full",
        "data_export_encryption_key": "e" * 48,
        "deletion_ledger_hmac_key": "d" * 48,
        "public_backend_url": "https://api.example.com",
        "frontend_public_url": "https://app.example.com",
        "frontend_url": "https://app.example.com",
        "email_public_base_url": "https://app.example.com",
        "allowed_origins": "https://app.example.com",
        "allowed_hosts": "api.example.com,app.example.com",
        "auth_cookie_secure": True,
        "auth_cookie_httponly": True,
        "auth_cookie_samesite": "lax",
        "email_delivery_driver": "smtp",
        "email_from_address": "no-reply@example.com",
        "smtp_host": "smtp.example.com",
        "smtp_username": "smtp-user",
        "smtp_password": "smtp-password-long",
        "smtp_use_starttls": True,
        "smtp_timeout_seconds": 15,
        "smtp_max_attempts": 2,
        "rate_limit_driver": "redis",
        "redis_url": "redis://redis.example.com:6379/0",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_production_runtime_rejects_masked_database_url_and_never_renders_password():
    settings = production_settings(database_url="postgresql+psycopg2://organicai:***@db.example.com:5432/organicai?sslmode=verify-full")
    report = check_runtime_configuration(settings)
    errors = {check.key for check in report.checks if check.status == "error"}
    rendered = report.model_dump_json()

    assert "DATABASE_URL" in errors
    assert "***" not in rendered
    assert "strong-password" not in rendered


def test_production_runtime_requires_postgres_ssl_mode():
    settings = production_settings(database_url="postgresql+psycopg2://organicai:strong-password@db.example.com:5432/organicai")
    report = check_runtime_configuration(settings)

    assert any(check.key == "PRODUCTION_POSTGRES_SSL_REQUIRED" and check.status == "error" for check in report.checks)


def test_production_runtime_rejects_localhost_cors_and_insecure_cookie():
    settings = production_settings(allowed_origins="http://127.0.0.1:5190", allowed_hosts="localhost", auth_cookie_secure=False)
    report = check_runtime_configuration(settings)
    errors = {check.key for check in report.checks if check.status == "error"}

    assert {"ALLOWED_ORIGINS", "ALLOWED_HOSTS", "AUTH_COOKIE_SECURE"}.issubset(errors)


def test_smtp_driver_success_failure_and_timeout_are_sanitized(monkeypatch):
    sent_messages = []

    class SuccessfulSMTP:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def starttls(self):
            return None

        def login(self, *_args):
            return None

        def send_message(self, message):
            sent_messages.append(message)
            return {}

    settings = SimpleNamespace(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_timeout_seconds=5,
        smtp_max_attempts=2,
        smtp_use_ssl=False,
        smtp_use_starttls=True,
        smtp_username="smtp-user",
        smtp_password="smtp-secret-value",
        email_from_address="no-reply@example.com",
        email_from_name="OrganicAI Compass",
        email_reply_to="support@example.com",
    )
    monkeypatch.setattr("app.services.email.smtp_delivery.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.email.smtp_delivery.smtplib.SMTP", SuccessfulSMTP)

    result = SmtpEmailDriver().send(
        EmailMessage(
            to="recipient@example.test",
            subject="Subject",
            text="text",
            html="<p>text</p>",
            idempotency_key="idem-123",
        )
    )
    assert result.status == "accepted"
    assert result.attempt_count == 1
    assert sent_messages[0]["X-OrganicAI-Idempotency-Key"] == "idem-123"
    assert "smtp-secret-value" not in str(result)

    class RefusedSMTP(SuccessfulSMTP):
        def send_message(self, _message):
            return {"recipient@example.test": (550, "refused")}

    monkeypatch.setattr("app.services.email.smtp_delivery.smtplib.SMTP", RefusedSMTP)
    refused = SmtpEmailDriver().send(EmailMessage(to="recipient@example.test", subject="Subject", text="text", html="<p>text</p>"))
    assert refused.status == "failed"
    assert refused.failure_code == "SMTP_RECIPIENT_REFUSED"

    class TimeoutSMTP(SuccessfulSMTP):
        attempts = 0

        def send_message(self, _message):
            TimeoutSMTP.attempts += 1
            raise TimeoutError

    monkeypatch.setattr("app.services.email.smtp_delivery.smtplib.SMTP", TimeoutSMTP)
    timeout = SmtpEmailDriver().send(EmailMessage(to="recipient@example.test", subject="Subject", text="text", html="<p>text</p>"))
    assert timeout.status == "failed"
    assert timeout.failure_code == "SMTP_TIMEOUT"
    assert timeout.attempt_count == 2
    assert TimeoutSMTP.attempts == 2


def test_production_go_no_go_blocks_external_manual_actions_without_secrets(tmp_path):
    evidence = tmp_path
    (evidence / "final-test-summary.json").write_text(
        json.dumps(
            {
                "backend": {"fullNonPostgres": {"status": "passed"}},
                "postgresql": {"markerSuite": {"failed": 0}},
                "frontend": {"build": {"status": "passed"}},
                "e2e": {"fullPlaywright": {"failed": 0}},
            }
        ),
        encoding="utf-8",
    )
    (evidence / "staging-service-summary.json").write_text(
        json.dumps({"runtimeSmoke": {"status": "passed"}, "observability": {"status": "passed"}}),
        encoding="utf-8",
    )
    (evidence / "source-archive-audit-final.json").write_text(
        json.dumps({"status": "passed", "blockedEntryCount": 0}),
        encoding="utf-8",
    )
    settings = production_settings(secret_rotation_postgres_confirmed=False)

    report = production_go_no_go_report(evidence, settings)
    rendered = json.dumps(report)

    assert report["classifications"]["local_release_candidate_ready"] is True
    assert report["classifications"]["production_deployment_ready"] is False
    assert report["status"] == "BLOCKED"
    assert report["secretReadiness"]["fingerprintsIncluded"] is False
    assert "safe_fingerprint" not in rendered
    assert any(check["status"] == "EXTERNAL MANUAL ACTION REQUIRED" for check in report["checks"])
    assert "strong-password" not in rendered
    assert "smtp-password-long" not in rendered
