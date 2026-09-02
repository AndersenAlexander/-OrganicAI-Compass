from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models.auth_security import AuthSession
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.privacy import DataLifecycleEvent, DeletionSuppressionLedgerEntry, PrivacyConsentEvent, PrivacyExportArtifact, UserPrivacySettings
from app.models.rag_observability import RagRun
from app.routers import auth, chat, privacy, test_fixtures


def make_client(tmp_path: Path, monkeypatch) -> tuple[TestClient, Session]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = Session(engine)
    app = FastAPI()
    app.include_router(auth.router, prefix="/api/auth")
    app.include_router(privacy.router, prefix="/api/privacy")
    app.include_router(test_fixtures.router, prefix="/api")
    app.include_router(chat.router, prefix="/api/chat")

    def override_db():
        yield db

    class PrivacySettings:
        privacy_export_directory = str(tmp_path / "exports")
        privacy_export_expire_hours = 24
        privacy_account_deletion_grace_days = 7
        privacy_recent_auth_minutes = 10
        app_env = "test"
        account_deletion_fixture_enabled = True

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr("app.services.email.validation.get_settings", lambda: type("S", (), {"email_delivery_driver": "development-outbox", "email_development_outbox_dir": str(tmp_path), "email_public_base_url": "http://testserver"})())
    monkeypatch.setattr("app.services.email.development_outbox.get_settings", lambda: type("S", (), {"email_development_outbox_dir": str(tmp_path)})())
    monkeypatch.setattr("app.services.email.templates.get_settings", lambda: type("S", (), {"email_public_base_url": "http://testserver"})())
    monkeypatch.setattr("app.privacy.service.get_settings", lambda: PrivacySettings())

    async def fake_search(_query: str):
        return []

    monkeypatch.setattr("app.services.rag_service.search_knowledge_base", fake_search)

    async def fake_generate_coach_response(*_args, **_kwargs):
        return {
            "answer": "Stubbed privacy-safe coach response.",
            "suggested_actions": [],
            "confidence_note": "Test stub.",
            "sources_used": [],
            "ethical_note": "Test stub.",
            "profile_signals_used": [],
            "grounding_status": "general",
            "retrieval_status": {},
            "rag_run_id": None,
            "context_quality": "insufficient",
            "insufficient_context": False,
        }

    monkeypatch.setattr("app.services.coach_chat_service.generate_coach_response", fake_generate_coach_response)
    return TestClient(app, base_url="http://testserver"), db


def register_and_reauth(client: TestClient, email: str = "privacy@example.test") -> dict:
    password = "Correct horse battery staple"
    response = client.post("/api/auth/register", json={"name": "Privacy User", "email": email, "password": password})
    assert response.status_code == 200
    access = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access}"}
    reauth = client.post("/api/privacy/reauthenticate", json={"password": password}, headers=headers)
    assert reauth.status_code == 200
    return {"headers": headers, "password": password, "userId": response.json()["user"]["id"]}


def test_privacy_defaults_preferences_and_immutable_consent_events(tmp_path, monkeypatch):
    client, db = make_client(tmp_path, monkeypatch)
    auth_state = register_and_reauth(client)
    headers = auth_state["headers"]

    preferences = client.get("/api/privacy/preferences", headers=headers)
    assert preferences.status_code == 200
    assert preferences.json()["conversationPersistenceMode"] == "account-history"
    assert preferences.json()["voiceTranscriptPersistenceMode"] == "ephemeral"
    assert preferences.json()["voiceAudioStorageEnabled"] is False

    updated = client.put(
        "/api/privacy/preferences",
        headers=headers,
        json={"conversationPersistenceMode": "ephemeral", "productAnalyticsEnabled": True},
    )
    assert updated.status_code == 200
    assert updated.json()["conversationPersistenceMode"] == "ephemeral"
    research_attempt = client.put("/api/privacy/preferences", headers=headers, json={"researchParticipationEnabled": True})
    assert research_attempt.status_code == 403
    assert db.get(UserPrivacySettings, auth_state["userId"]).research_participation_enabled is False
    events = db.scalars(select(PrivacyConsentEvent).where(PrivacyConsentEvent.user_id == auth_state["userId"])).all()
    assert {event.action for event in events} >= {"not-required", "granted"}
    assert all("content" not in str(event.metadata_json).lower() for event in events)


def test_ephemeral_chat_creates_no_persistent_transcript_or_rag_rows(tmp_path, monkeypatch):
    client, db = make_client(tmp_path, monkeypatch)
    auth_state = register_and_reauth(client, "ephemeral@example.test")
    headers = auth_state["headers"]
    client.put("/api/privacy/preferences", headers=headers, json={"conversationPersistenceMode": "ephemeral"})

    response = client.post("/api/chat", headers=headers, json={"message": "How should I use AI carefully?", "profile_id": None})
    assert response.status_code == 200
    assert response.json()["conversation_id"].startswith("ephemeral-")
    assert db.scalar(select(Conversation)) is None
    assert db.scalar(select(Message)) is None
    assert db.scalar(select(RagRun)) is None


def test_export_download_delete_and_secret_exclusion(tmp_path, monkeypatch):
    client, db = make_client(tmp_path, monkeypatch)
    auth_state = register_and_reauth(client, "export@example.test")
    headers = auth_state["headers"]

    created = client.post("/api/privacy/exports", headers=headers)
    assert created.status_code == 200
    artifact_id = created.json()["id"]
    artifact = db.get(PrivacyExportArtifact, artifact_id)
    assert artifact is not None and artifact.checksum_sha256
    assert Path(artifact.storage_path).exists()
    assert artifact.storage_path.endswith(".zip.enc")

    downloaded = client.get(f"/api/privacy/exports/{artifact_id}/download", headers=headers)
    assert downloaded.status_code == 200
    assert b"hashed_password" not in downloaded.content
    deleted = client.delete(f"/api/privacy/exports/{artifact_id}", headers=headers)
    assert deleted.status_code == 204
    db.refresh(artifact)
    assert artifact.status == "deleted" and artifact.deleted_at is not None


def test_category_deletion_account_deletion_research_withdrawal_and_retention(tmp_path, monkeypatch):
    client, db = make_client(tmp_path, monkeypatch)
    auth_state = register_and_reauth(client, "delete@example.test")
    headers = auth_state["headers"]
    chat_response = client.post("/api/chat", headers=headers, json={"message": "Persist this conversation."})
    assert chat_response.status_code == 200
    assert db.scalar(select(Message)) is not None

    preview = client.get("/api/privacy/deletion/categories/conversation-history/preview", headers=headers)
    assert preview.status_code == 200
    assert preview.json()["rowCounts"]["messages"] >= 1
    deleted = client.post("/api/privacy/deletion/categories/conversation-history", headers=headers, json={"confirmation": "conversation-history"})
    assert deleted.status_code == 200
    assert db.scalar(select(Message)) is None

    settings = db.get(UserPrivacySettings, auth_state["userId"])
    settings.research_participation_enabled = True
    db.commit()
    withdrawn = client.post("/api/privacy/research/withdraw", headers=headers)
    assert withdrawn.status_code == 200
    assert db.get(UserPrivacySettings, auth_state["userId"]).research_participation_enabled is False

    requested = client.post("/api/privacy/account-deletion", headers=headers, json={"confirmation": "DELETE MY ORGANICAI ACCOUNT"})
    assert requested.status_code == 200
    cancelled = client.post(f"/api/privacy/account-deletion/{requested.json()['requestId']}/cancel", headers=headers)
    assert cancelled.status_code == 200 and cancelled.json()["status"] == "cancelled"
    requested_again = client.post("/api/privacy/account-deletion", headers=headers, json={"confirmation": "DELETE MY ORGANICAI ACCOUNT"})
    queued_request = requested_again.json()["requestId"]
    assert db.scalar(select(DataLifecycleEvent).where(DataLifecycleEvent.request_id == queued_request, DataLifecycleEvent.event_type == "account-deletion-completed")) is None
    executed = client.post(f"/api/privacy/account-deletion/{requested_again.json()['requestId']}/execute-fixture", headers=headers)
    assert executed.status_code == 200
    assert db.scalar(select(AuthSession).where(AuthSession.user_id == auth_state["userId"])) is None
    assert db.scalar(select(DeletionSuppressionLedgerEntry)) is not None
    assert db.scalar(select(DataLifecycleEvent).where(DataLifecycleEvent.event_type == "account-deletion-completed")) is not None
