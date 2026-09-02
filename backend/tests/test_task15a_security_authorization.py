from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import app.models  # noqa: F401 - register SQLAlchemy models for create_all.
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth.security import create_access_token
from app.core.time import utc_now_naive
from app.database import Base, get_db
from app.models.auth_security import AuthSession
from app.models.market_application import LabourMarketProviderRecord, LabourMarketSyncCursor, LabourMarketSyncRun
from app.models.originality_research import ResearchOriginalitySession
from app.models.profile import Profile
from app.models.user import User
from app.routers import innovation_extension, market_application, originality_research, rag, voice


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        access_token_expire_minutes=30,
        admin_emails="admin@example.test",
        algorithm="HS256",
        demo_user_email="demo@organicai.local",
        elevenlabs_live_voice_enabled=False,
        labour_market_live_enabled=False,
        labour_market_provider="demo",
        max_audio_upload_bytes=8,
        max_chat_message_chars=20,
        max_context_field_chars=100,
        nav_stilling_feed_base_url="https://arbeidsplassen.nav.no",
        nav_stilling_feed_enabled=False,
        nav_stilling_feed_token=None,
        secret_key="x" * 40,
    )


@pytest.fixture(autouse=True)
def task15a_settings(monkeypatch):
    settings = _settings()
    monkeypatch.setattr("app.auth.security.get_settings", lambda: settings)
    monkeypatch.setattr("app.auth.dependencies.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.profile_authorization.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.market_application_engine.get_settings", lambda: settings)


def session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def client_for(db: Session, router, prefix: str) -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix=prefix)

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


def make_user(db: Session, email: str) -> User:
    item = User(name=email.split("@")[0], email=email, hashed_password="x")
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def auth_headers(db: Session, email: str) -> dict[str, str]:
    user = make_user(db, email)
    session_row = AuthSession(
        user_id=user.id,
        token_family_id=str(uuid4()),
        refresh_token_hash=f"refresh-{uuid4()}",
        created_at=utc_now_naive(),
        expires_at=utc_now_naive() + timedelta(days=1),
    )
    db.add(session_row)
    db.commit()
    db.refresh(user)
    db.refresh(session_row)
    token = create_access_token({"sub": user.id, "sid": session_row.id, "ver": user.auth_version})
    return {"Authorization": f"Bearer {token}"}


def test_voice_transcribe_and_speak_require_auth(monkeypatch):
    db = session()
    client = client_for(db, voice.router, "/api/voice")

    async def fake_transcribe(_path: str) -> str:
        return "hello"

    async def fake_speak(_text: str) -> str:
        return "/media/voice/test.mp3"

    monkeypatch.setattr(voice, "get_settings", _settings)
    monkeypatch.setattr(voice, "transcribe_audio", fake_transcribe)
    monkeypatch.setattr(voice, "synthesize_speech", fake_speak)

    assert client.post("/api/voice/transcribe", files={"file": ("voice.webm", b"abc", "audio/webm")}).status_code == 401
    assert client.post("/api/voice/speak", json={"text": "hello"}).status_code == 401

    headers = auth_headers(db, "voice@example.test")
    invalid = client.post("/api/voice/transcribe", headers=headers, files={"file": ("voice.txt", b"abc", "text/plain")})
    oversized = client.post("/api/voice/transcribe", headers=headers, files={"file": ("voice.webm", b"0123456789", "audio/webm")})
    ok = client.post("/api/voice/transcribe", headers=headers, files={"file": ("voice.webm", b"abc", "audio/webm")})
    spoken = client.post("/api/voice/speak", headers=headers, json={"text": "hello"})

    assert invalid.status_code == 422
    assert oversized.status_code == 413
    assert ok.status_code == 200
    assert ok.json()["transcript"] == "hello"
    assert spoken.status_code == 200
    assert spoken.json()["audio_url"] == "/media/voice/test.mp3"


def test_rag_reindex_is_admin_only_and_search_remains_public(monkeypatch):
    db = session()
    client = client_for(db, rag.router, "/api/rag")

    async def fake_reindex() -> dict[str, int]:
        return {"documents": 1, "chunks": 2}

    async def fake_search(_query: str):
        return [SimpleNamespace(source_id="doc-1", title="Doc", content="body")]

    monkeypatch.setattr(rag, "reindex_knowledge_base", fake_reindex)
    monkeypatch.setattr(rag, "search_knowledge_base", fake_search)

    assert client.post("/api/rag/reindex").status_code == 401
    assert client.post("/api/rag/reindex", headers=auth_headers(db, "user@example.test")).status_code == 403
    admin = client.post("/api/rag/reindex", headers=auth_headers(db, "admin@example.test"))
    search = client.get("/api/rag/search", params={"query": "policy"})

    assert admin.status_code == 200
    assert admin.json() == {"documents": 1, "chunks": 2}
    assert search.status_code == 200
    assert search.json()["results"][0]["source_id"] == "doc-1"


def test_career_encyclopedia_admin_write_routes(monkeypatch):
    db = session()
    client = client_for(db, innovation_extension.router, "/api/v1")

    def fake_sync(_db: Session) -> dict:
        return {"synced": 1}

    def fake_upsert(_db: Session, data: dict, archive: bool = False) -> dict:
        if archive and data.get("slug") == "missing":
            raise LookupError("career not found")
        return {"slug": data.get("slug", "created-role"), "archived": archive}

    monkeypatch.setattr(innovation_extension, "sync_career_encyclopedia", fake_sync)
    monkeypatch.setattr(innovation_extension, "upsert_career_role", fake_upsert)

    assert client.post("/api/v1/admin/career-encyclopedia/sync").status_code == 401
    assert client.post("/api/v1/admin/career-encyclopedia/sync", headers=auth_headers(db, "user2@example.test")).status_code == 403
    admin_headers = auth_headers(db, "admin@example.test")

    assert client.post("/api/v1/admin/career-encyclopedia/sync", headers=admin_headers).status_code == 200
    assert client.post("/api/v1/admin/career-encyclopedia/roles", headers=admin_headers, json={"slug": "new-role"}).status_code == 200
    assert client.put("/api/v1/admin/career-encyclopedia/roles/existing-role", headers=admin_headers, json={"title": "Existing"}).status_code == 200
    assert client.delete("/api/v1/admin/career-encyclopedia/roles/existing-role", headers=admin_headers).status_code == 200
    assert client.delete("/api/v1/admin/career-encyclopedia/roles/missing", headers=admin_headers).status_code == 404


def test_market_provider_esco_and_research_admin_boundaries(monkeypatch):
    db = session()
    client = client_for(db, market_application.router, "/api/v1")

    monkeypatch.setattr(market_application, "sync_demo_labour_market", lambda _db: {"status": "completed"})
    monkeypatch.setattr(market_application, "normalise_skill_terms", lambda _db, phrases: {"provider": "local", "mappings": phrases})
    monkeypatch.setattr(market_application, "assert_research_ready", lambda: None)
    monkeypatch.setattr(market_application, "ensure_research_study", lambda _db, demo=False: {"id": "study-1", "demo": demo})
    monkeypatch.setattr(market_application, "require_study", lambda _db, study_id: SimpleNamespace(id=study_id))
    monkeypatch.setattr(market_application, "create_research_export", lambda _db, study, payload: {"id": "export-1", "study_id": study.id, "payload": payload})
    monkeypatch.setattr(market_application, "get_research_export", lambda _db, export_id: {"id": export_id})

    status = client.get("/api/v1/market/providers/status")
    assert status.status_code == 200
    assert db.scalar(select(func.count()).select_from(LabourMarketProviderRecord)) == 0
    assert db.scalar(select(func.count()).select_from(LabourMarketSyncCursor)) == 0
    assert db.scalar(select(func.count()).select_from(LabourMarketSyncRun)) == 0

    user_headers = auth_headers(db, "market-user@example.test")
    admin_headers = auth_headers(db, "admin@example.test")
    admin_only_cases = [
        ("post", "/api/v1/market/providers/demo/sync", {}),
        ("post", "/api/v1/market/esco/normalise", {"phrases": ["UX"]}),
        ("post", "/api/v1/research/studies/ensure", {"demo": True}),
        ("post", "/api/v1/research/studies/study-1/exports", {}),
        ("get", "/api/v1/research/exports/export-1", None),
    ]

    for method, path, payload in admin_only_cases:
        request = getattr(client, method)
        assert request(path, json=payload).status_code == 401 if payload is not None else request(path).status_code == 401
        assert request(path, headers=user_headers, json=payload).status_code == 403 if payload is not None else request(path, headers=user_headers).status_code == 403
        response = request(path, headers=admin_headers, json=payload) if payload is not None else request(path, headers=admin_headers)
        assert response.status_code == 200


def test_originality_fairness_admin_and_session_owner_boundaries(monkeypatch):
    db = session()
    client = client_for(db, originality_research.router, "/api/v1")
    monkeypatch.setattr(originality_research, "assert_research_ready", lambda: None)
    monkeypatch.setattr(originality_research, "run_fairness_audit", lambda _db, payload: {"id": "audit-1", "payload": payload})
    monkeypatch.setattr(originality_research, "reset_synthetic_fairness_lab", lambda _db, payload: {"reset": True, "payload": payload})

    assert client.post("/api/v1/research/fairness-audits", json={}).status_code == 401
    assert client.post("/api/v1/research/fairness-audits", headers=auth_headers(db, "ordinary@example.test"), json={}).status_code == 403
    admin_headers = auth_headers(db, "admin@example.test")
    assert client.post("/api/v1/research/fairness-audits", headers=admin_headers, json={}).status_code == 200
    assert client.post("/api/v1/research/fairness-audits/reset", headers=admin_headers, json={}).status_code == 200

    owner_headers = auth_headers(db, "owner@example.test")
    other_headers = auth_headers(db, "other@example.test")
    owner = db.scalar(select(User).where(User.email == "owner@example.test"))
    assert owner is not None
    profile = Profile(user_id=owner.id, diagnostic_id="diagnostic", data={})
    db.add(profile)
    db.flush()
    session_row = ResearchOriginalitySession(profile_id=profile.id, user_id=owner.id, consent_confirmed=True)
    db.add(session_row)
    db.commit()
    db.refresh(session_row)

    baseline_path = f"/api/v1/research/originality-sessions/{session_row.id}/baseline"
    results_path = f"/api/v1/research/originality-sessions/{session_row.id}/results"

    assert client.post(baseline_path, json={"actionability": 3}).status_code == 401
    assert client.post(baseline_path, headers=other_headers, json={"actionability": 3}).status_code == 403
    owner_update = client.post(baseline_path, headers=owner_headers, json={"actionability": 4})
    assert owner_update.status_code == 200
    assert owner_update.json()["baseline"]["actionability"] == 4
    assert client.get(results_path, headers=other_headers).status_code == 403
    assert client.get(results_path, headers=owner_headers).status_code == 200
