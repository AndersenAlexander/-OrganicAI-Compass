from __future__ import annotations

import time
from datetime import datetime
from app.core.time import utc_now_naive
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models.interview_journey import VoiceProviderSession
from app.models.provider_operations import EmailDeliveryEvent, OperationalJobRun, ProviderVerificationRun, WebhookDeliveryEvent
from app.routers import webhooks
from app.services.email.base import EmailMessage
from app.services.email.templates import render_template
from app.services.email.validation import record_email_event
from app.services.operational_workers import run_worker_once
from app.services.providers.elevenlabs_privacy import is_disposable_test_conversation, validate_disposable_conversation_deletion
from app.services.release_readiness import release_readiness_summary
from app.services.secret_readiness import audit_secret_readiness


def db_session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def test_secret_readiness_classifies_placeholders_rotation_and_production_blocks():
    settings = SimpleNamespace(
        app_env="production",
        openai_api_key="sk-test",
        elevenlabs_api_key="eleven-test",
        elevenlabs_agent_id="agent-test",
        elevenlabs_webhook_secret="",
        database_url="postgresql://user:pass@localhost/db",
        secret_key="change-this-secret-key",
        custom_llm_secret="",
        webhook_secret="",
        data_export_encryption_key="",
        deletion_ledger_hmac_key="",
        smtp_password="",
        secret_rotation_openai_confirmed=False,
        secret_rotation_elevenlabs_confirmed=False,
        secret_rotation_postgres_confirmed=False,
        secret_rotation_application_confirmed=False,
    )
    report = audit_secret_readiness(settings)  # type: ignore[arg-type]
    items = {item["name"]: item for item in report["items"]}
    assert items["OPENAI_API_KEY"]["status"] == "rotation-required"
    assert items["SECRET_KEY"]["status"] == "placeholder"
    assert items["DATA_EXPORT_ENCRYPTION_KEY"]["blocking"] is True
    assert report["secretValuesIncluded"] is False
    assert "sk-test" not in str(report)


def test_email_templates_and_event_do_not_store_raw_tokens_or_recipient(monkeypatch):
    monkeypatch.setattr("app.services.email.templates.get_settings", lambda: SimpleNamespace(email_public_base_url="http://127.0.0.1:5190"))
    rendered = render_template("reset-password", token="token with spaces", path="/reset-password", expires="30 minutes")
    assert "token%20with%20spaces" in rendered.text
    assert "<img" not in rendered.html.lower()
    db = db_session()
    message = EmailMessage(to="recipient@example.test", subject=rendered.subject, text=rendered.text, html=rendered.html, message_type="reset-password")
    event = record_email_event(db, message, SimpleNamespace(status="accepted", provider="development-outbox", provider_message_id="provider-id", failure_code=None))
    assert db.get(EmailDeliveryEvent, event.id).recipient_hash
    assert "recipient@example.test" not in str(event.__dict__)


def test_operational_worker_records_lock_heartbeat_and_completion():
    db = db_session()
    result = run_worker_once(db, "retention", worker_id="worker-1")
    assert result["status"] == "completed"
    row = db.scalar(select(OperationalJobRun).where(OperationalJobRun.job_type == "retention"))
    assert row is not None
    assert row.worker_id_hash and row.heartbeat_at and row.lease_expires_at


def test_elevenlabs_disposable_conversation_gate_rejects_wrong_or_linked(monkeypatch):
    db = db_session()
    settings = SimpleNamespace(
        live_provider_validation_enabled=True,
        live_provider_write_validation_enabled=True,
        elevenlabs_real_deletion_test_enabled=True,
        elevenlabs_test_conversation_id="disposable-test-conversation",
    )
    monkeypatch.setattr("app.services.providers.elevenlabs_privacy.get_settings", lambda: settings)
    assert is_disposable_test_conversation("disposable-test-conversation") is True
    assert is_disposable_test_conversation("real-conversation") is False
    db.add(VoiceProviderSession(profile_id="profile-1", provider_session_id="disposable-test-conversation"))
    db.commit()
    import asyncio

    result = asyncio.run(validate_disposable_conversation_deletion(db))
    assert result["status"] == "failed"
    assert "linked" in result["reason"]


def test_webhook_hmac_replay_and_event_allowlist(monkeypatch):
    db = db_session()
    app = FastAPI()

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.include_router(webhooks.router, prefix="/api/webhooks")
    monkeypatch.setattr(webhooks, "get_settings", lambda: SimpleNamespace(elevenlabs_webhook_secret="test-secret", webhook_secret="", max_request_body_bytes=100000))
    client = TestClient(app)
    body = b'{"type":"post_call_transcription","conversation_id":"disposable-test-conversation"}'
    signature = webhooks.sign_elevenlabs_webhook(body, "test-secret", int(time.time()))
    response = client.post("/api/webhooks/elevenlabs", content=body, headers={"ElevenLabs-Signature": signature, "Content-Type": "application/json"})
    assert response.status_code == 200
    replay = client.post("/api/webhooks/elevenlabs", content=body, headers={"ElevenLabs-Signature": signature, "Content-Type": "application/json"})
    assert replay.status_code == 200 and replay.json()["status"] == "duplicate"
    invalid = client.post("/api/webhooks/elevenlabs", content=body, headers={"ElevenLabs-Signature": "t=1,v1=bad"})
    assert invalid.status_code == 401
    assert db.scalar(select(WebhookDeliveryEvent).where(WebhookDeliveryEvent.event_type == "post_call_transcription")) is not None


def test_release_readiness_blocks_unsafe_production(monkeypatch):
    settings = SimpleNamespace(
        app_env="production",
        production_release_gate_enabled=True,
        database_url="sqlite:///./organicai.db",
        secret_key="change-this-secret-key",
        data_export_encryption_key="",
        deletion_ledger_hmac_key="",
        openai_api_key=None,
        elevenlabs_api_key=None,
        email_delivery_driver="development-outbox",
        log_conversation_content=False,
        elevenlabs_agent_id=None,
        elevenlabs_webhook_secret=None,
        smtp_password=None,
        custom_llm_secret=None,
        webhook_secret=None,
        secret_rotation_openai_confirmed=False,
        secret_rotation_elevenlabs_confirmed=False,
        secret_rotation_postgres_confirmed=False,
        secret_rotation_application_confirmed=False,
    )
    monkeypatch.setattr("app.services.release_readiness.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.secret_readiness.get_settings", lambda: settings)
    report = release_readiness_summary()
    assert report["status"] == "blocked"
    assert report["blockingFindingCount"] >= 1


def test_provider_verification_model_excludes_content():
    db = db_session()
    run = ProviderVerificationRun(
        provider="OpenAI",
        verification_type="canary",
        execution_mode="offline",
        status="completed",
        started_at=utc_now_naive(),
        completed_at=utc_now_naive(),
        result_summary_json={"model": "gpt-4o-mini", "promptContentStored": False, "answerContentStored": False},
    )
    db.add(run)
    db.commit()
    assert "ORGANICAI_PROVIDER_OK" not in str(db.get(ProviderVerificationRun, run.id).result_summary_json)

