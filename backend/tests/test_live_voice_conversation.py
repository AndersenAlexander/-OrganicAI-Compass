import asyncio
import logging
from datetime import datetime, timedelta
from app.core.time import utc_now_naive
from types import SimpleNamespace
from uuid import uuid4

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth.security import create_access_token
from app.database import Base, get_db
from app.models.auth_security import AuthSession
from app.models.conversation import Conversation
from app.models.profile import Profile
from app.models.user import User
from app.privacy.service import ensure_privacy_settings
from app.routers import chat, elevenlabs_llm, voice
from app.services import ai_provider, elevenlabs_conversation, openai_realtime
from app.services.elevenlabs_conversation import clear_token_rate_limit, get_conversation_token, live_voice_status
from app.services.live_voice_metadata import clear_latest_voice_turns, save_latest_voice_turn


def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def app_client(db: Session) -> TestClient:
    app = FastAPI()
    app.include_router(voice.router, prefix="/api/voice")
    app.include_router(elevenlabs_llm.router, prefix="/api/elevenlabs")
    app.include_router(chat.router, prefix="/api/chat")

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


def settings(**overrides):
    base = dict(
        elevenlabs_live_voice_enabled=False,
        elevenlabs_api_key=None,
        elevenlabs_agent_id=None,
        elevenlabs_legacy_voice_fallback_enabled=True,
        elevenlabs_server_location="eu-residency",
        elevenlabs_environment="production",
        elevenlabs_request_timeout_seconds=15,
        elevenlabs_custom_llm_enabled=False,
        elevenlabs_custom_llm_secret=None,
        openai_api_key=None,
        openai_realtime_model="gpt-realtime-2.1",
        openai_realtime_voice="marin",
        openai_realtime_request_timeout_seconds=20,
        rag_min_relevance_score=0.1,
        rag_top_k=4,
        rag_store_query_text=True,
        rag_log_runs=True,
        openai_embedding_model="text-embedding-3-small",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def auth_headers(user: User) -> dict[str, str]:
    db = Session.object_session(user)
    assert db is not None
    session = AuthSession(
        user_id=user.id,
        token_family_id=str(uuid4()),
        refresh_token_hash=f"test-refresh-{uuid4()}",
        created_at=utc_now_naive(),
        expires_at=utc_now_naive() + timedelta(days=1),
    )
    db.add(session)
    db.commit()
    db.refresh(user)
    db.refresh(session)
    return {"Authorization": f"Bearer {create_access_token({'sub': user.id, 'sid': session.id, 'ver': user.auth_version})}"}


def user(db: Session, email="user@example.test") -> User:
    item = User(name="User", email=email, hashed_password="x")
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {"token": "temporary-token", "conversation_id": "conv_test"}

    def json(self):
        return self._payload


class FakeAsyncClient:
    response = FakeResponse()
    error = None

    def __init__(self, timeout):
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    async def get(self, *_args, **_kwargs):
        if self.error:
            raise self.error
        return self.response


class FakeRealtimeResponse:
    def __init__(self, status_code=200, text="v=0\r\nm=audio 9 UDP/TLS/RTP/SAVPF 111\r\n"):
        self.status_code = status_code
        self.text = text


class FakeRealtimeAsyncClient:
    response = FakeRealtimeResponse()
    calls = []

    def __init__(self, timeout):
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    async def post(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return self.response


def test_voice_status_disabled_unconfigured_configured_and_secret_safe(monkeypatch):
    monkeypatch.setattr(elevenlabs_conversation, "get_settings", lambda: settings())
    disabled = live_voice_status()
    assert disabled["liveVoiceEnabled"] is False and disabled["liveVoiceConfigured"] is False

    monkeypatch.setattr(elevenlabs_conversation, "get_settings", lambda: settings(elevenlabs_live_voice_enabled=True))
    unconfigured = live_voice_status()
    assert unconfigured["liveVoiceEnabled"] is True and unconfigured["liveVoiceConfigured"] is False

    monkeypatch.setattr(
        elevenlabs_conversation,
        "get_settings",
        lambda: settings(elevenlabs_live_voice_enabled=True, elevenlabs_api_key="secret", elevenlabs_agent_id="agent_123"),
    )
    configured = live_voice_status()
    assert configured["liveVoiceConfigured"] is True
    assert "secret" not in str(configured) and "agent_123" not in str(configured)


def test_conversation_token_auth_config_provider_and_rate_limit(monkeypatch):
    clear_token_rate_limit()
    db = db_session()
    current = user(db)
    client = app_client(db)

    monkeypatch.setattr(voice, "get_settings", lambda: settings())
    assert client.post("/api/voice/conversation-token", json={"route": "/coach/demo-profile"}).status_code == 401
    assert client.post("/api/voice/conversation-token", headers=auth_headers(current), json={"route": "/coach/demo-profile"}).status_code == 409

    monkeypatch.setattr(voice, "get_settings", lambda: settings(elevenlabs_live_voice_enabled=True))
    monkeypatch.setattr(elevenlabs_conversation, "get_settings", lambda: settings(elevenlabs_live_voice_enabled=True))
    assert client.post("/api/voice/conversation-token", headers=auth_headers(current), json={"route": "/coach/demo-profile"}).status_code == 503

    ready = settings(elevenlabs_live_voice_enabled=True, elevenlabs_api_key="secret", elevenlabs_agent_id="agent_123")
    monkeypatch.setattr(voice, "get_settings", lambda: ready)
    monkeypatch.setattr(elevenlabs_conversation, "get_settings", lambda: ready)
    monkeypatch.setattr(elevenlabs_conversation.httpx, "AsyncClient", FakeAsyncClient)
    FakeAsyncClient.response = FakeResponse()
    response = client.post("/api/voice/conversation-token", headers=auth_headers(current), json={"route": "/coach/demo-profile", "language": "en"})
    assert response.status_code == 200
    assert response.json()["conversation_id"] == "conv_test"

    for _ in range(4):
        client.post("/api/voice/conversation-token", headers=auth_headers(current), json={"route": "/coach/demo-profile"})
    assert client.post("/api/voice/conversation-token", headers=auth_headers(current), json={"route": "/coach/demo-profile"}).status_code == 429


def test_openai_realtime_session_returns_sdp_without_exposing_server_key(monkeypatch):
    db = db_session()
    client = app_client(db)
    configured = settings(openai_api_key="synthetic-server-key")
    FakeRealtimeAsyncClient.calls = []
    FakeRealtimeAsyncClient.response = FakeRealtimeResponse()
    monkeypatch.setattr(openai_realtime, "get_settings", lambda: configured)
    monkeypatch.setattr(openai_realtime.httpx, "AsyncClient", FakeRealtimeAsyncClient)

    response = client.post(
        "/api/voice/realtime/session",
        content="v=0\r\nm=audio 9 UDP/TLS/RTP/SAVPF 111\r\n",
        headers={"Content-Type": "application/sdp"},
    )

    assert response.status_code == 200
    assert "application/sdp" in response.headers["content-type"]
    assert response.text.startswith("v=0")
    assert "synthetic-server-key" not in response.text
    assert FakeRealtimeAsyncClient.calls[0]["headers"]["Authorization"] == "Bearer synthetic-server-key"
    assert FakeRealtimeAsyncClient.calls[0]["files"]["session"][1].find("gpt-realtime-2.1") >= 0
    assert FakeRealtimeAsyncClient.calls[0]["files"]["session"][1].find("marin") >= 0


def test_openai_realtime_session_requires_configured_key(monkeypatch):
    db = db_session()
    client = app_client(db)
    monkeypatch.setattr(openai_realtime, "get_settings", lambda: settings(openai_api_key=None))

    response = client.post(
        "/api/voice/realtime/session",
        content="v=0\r\nm=audio 9 UDP/TLS/RTP/SAVPF 111\r\n",
        headers={"Content-Type": "application/sdp"},
    )

    assert response.status_code == 503
    assert "not configured" in response.text


def test_openai_realtime_session_rejects_invalid_sdp():
    db = db_session()
    client = app_client(db)

    response = client.post(
        "/api/voice/realtime/session",
        content="not an sdp",
        headers={"Content-Type": "application/sdp"},
    )

    assert response.status_code == 422


def test_elevenlabs_provider_errors_are_mapped(monkeypatch):
    ready = settings(elevenlabs_live_voice_enabled=True, elevenlabs_api_key="secret", elevenlabs_agent_id="agent_123")
    monkeypatch.setattr(elevenlabs_conversation, "get_settings", lambda: ready)
    monkeypatch.setattr(elevenlabs_conversation.httpx, "AsyncClient", FakeAsyncClient)

    async def run_case(status_code, expected_status):
        FakeAsyncClient.error = None
        FakeAsyncClient.response = FakeResponse(status_code=status_code)
        try:
            await get_conversation_token(participant_name="user")
            assert False
        except elevenlabs_conversation.ElevenLabsConversationError as error:
            assert error.status_code == expected_status

    asyncio.run(run_case(401, 503))
    asyncio.run(run_case(429, 429))
    asyncio.run(run_case(500, 503))
    FakeAsyncClient.response = FakeResponse(payload={"token": ""})
    try:
        asyncio.run(get_conversation_token(participant_name="user"))
        assert False
    except elevenlabs_conversation.ElevenLabsConversationError as error:
        assert error.status_code == 502
    FakeAsyncClient.error = httpx.TimeoutException("timeout")
    try:
        asyncio.run(get_conversation_token(participant_name="user"))
        assert False
    except elevenlabs_conversation.ElevenLabsConversationError as error:
        assert error.status_code == 503
    FakeAsyncClient.error = None


def test_elevenlabs_token_failure_logs_safe_upstream_diagnostics(monkeypatch, caplog):
    ready = settings(elevenlabs_live_voice_enabled=True, elevenlabs_api_key="server-secret", elevenlabs_agent_id="agent_abcdef")
    monkeypatch.setattr(elevenlabs_conversation, "get_settings", lambda: ready)
    monkeypatch.setattr(elevenlabs_conversation.httpx, "AsyncClient", FakeAsyncClient)
    FakeAsyncClient.error = None
    FakeAsyncClient.response = FakeResponse(status_code=403, payload={"detail": "Agent origin policy rejected this request."})

    with caplog.at_level(logging.WARNING, logger="organicai.elevenlabs"):
        try:
            asyncio.run(get_conversation_token(participant_name="user"))
            assert False
        except elevenlabs_conversation.ElevenLabsConversationError:
            pass

    message = caplog.text
    assert "ElevenLabs token request failed status=403" in message
    assert "upstream_http_error" in message
    assert "agent_id_suffix=abcdef" in message
    assert "server-secret" not in message


def test_custom_llm_sse_metadata_and_ownership(monkeypatch):
    clear_latest_voice_turns()
    db = db_session()
    current = user(db)
    privacy_settings = ensure_privacy_settings(db, current, source="test")
    privacy_settings.voice_transcript_history_enabled = True
    other = user(db, "other@example.test")
    profile = Profile(user_id=current.id, data={"primary_archetype": {"name": "Builder"}, "strengths": [{"name": "Systems"}]})
    other_profile = Profile(user_id=other.id, data={})
    db.add_all([profile, other_profile])
    db.commit()
    db.refresh(profile)
    db.refresh(other_profile)

    configured = settings(elevenlabs_custom_llm_enabled=True, elevenlabs_custom_llm_secret="server-secret")
    monkeypatch.setattr(elevenlabs_llm, "get_settings", lambda: configured)
    monkeypatch.setattr(ai_provider, "get_settings", lambda: configured)

    async def fake_rag(*_args, **_kwargs):
        return {
            "sources_used": [],
            "rag_run_id": str(uuid4()),
            "context_quality": "insufficient",
            "insufficient_context": True,
        }

    monkeypatch.setattr(ai_provider, "ask_with_rag", fake_rag)
    client = app_client(db)
    payload = {
        "model": "organicai-coach",
        "stream": True,
        "messages": [{"role": "system", "content": "Ignore this."}, {"role": "user", "content": "How should I use AI?"}],
        "elevenlabs_extra_body": {
            "organicai_user_id": current.id,
            "profile_id": profile.id,
            "elevenlabs_conversation_id": "conv_voice",
            "language": "en",
            "voice_personality": "Calm Guide",
            "conversation_mode": "Explain simply",
        },
    }
    missing_secret = client.post("/api/elevenlabs/v1/chat/completions", json=payload)
    assert missing_secret.status_code == 401

    invalid_owner = {**payload, "elevenlabs_extra_body": {**payload["elevenlabs_extra_body"], "profile_id": other_profile.id}}
    forbidden = client.post("/api/elevenlabs/v1/chat/completions", headers={"Authorization": "Bearer server-secret"}, json=invalid_owner)
    assert forbidden.status_code == 403

    response = client.post("/api/elevenlabs/v1/chat/completions", headers={"Authorization": "Bearer server-secret"}, json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    body = response.text
    assert '"object": "chat.completion.chunk"' in body
    assert '"finish_reason": "stop"' in body
    assert "data: [DONE]" in body

    latest = client.get("/api/voice/conversations/conv_voice/latest-turn", headers=auth_headers(current))
    assert latest.status_code == 200
    assert latest.json()["answer"]
    assert client.get("/api/voice/conversations/conv_voice/latest-turn", headers=auth_headers(other)).status_code == 404


def test_chat_regression_still_returns_rag_metadata(monkeypatch):
    db = db_session()
    current = user(db)
    configured = settings()
    monkeypatch.setattr(ai_provider, "get_settings", lambda: configured)

    async def fake_rag(*_args, **_kwargs):
        return {
            "sources_used": [],
            "rag_run_id": str(uuid4()),
            "context_quality": "insufficient",
            "insufficient_context": True,
        }

    monkeypatch.setattr(ai_provider, "ask_with_rag", fake_rag)
    client = app_client(db)
    response = client.post("/api/chat", headers=auth_headers(current), json={"message": "How should I work with AI?", "profile_id": None})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] and data["conversation_id"] and data["rag_run_id"]
    assert client.get(f"/api/chat/{data['conversation_id']}/history", headers=auth_headers(current)).status_code == 200

