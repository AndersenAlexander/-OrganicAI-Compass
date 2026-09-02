import asyncio
from types import SimpleNamespace

from openai import OpenAIError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.career_resilience import CareerEvidenceGap, CareerHypothesis
from app.models.profile import Profile
from app.models.user import User
from app.services import ai_provider, rag_service
from app.services.coach_chat_service import compact_profile_context


def run(coroutine):
    return asyncio.run(coroutine)


def db_session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def rag_settings():
    return SimpleNamespace(
        rag_top_k=4,
        rag_min_relevance_score=0.1,
        rag_min_context_chunks=1,
        rag_max_context_chunks=4,
        rag_store_query_text=True,
        rag_log_runs=True,
        openai_embedding_model="text-embedding-3-small",
    )


def test_embedding_provider_failure_uses_persisted_lexical_sources(monkeypatch):
    async def offline_embedding(_query: str):
        raise OpenAIError("embedding provider offline")

    monkeypatch.setattr(rag_service, "get_settings", rag_settings)
    monkeypatch.setattr(
        rag_service,
        "_load_store",
        lambda: [
            {
                "id": "responsible-ai",
                "document_name": "responsible_ai",
                "section_title": "Human oversight",
                "chunk_text": "Human oversight and transparent sources are central to responsible AI.",
                "embedding": [0.0] * 1536,
            }
        ],
    )
    monkeypatch.setattr(rag_service, "embed_text", offline_embedding)

    results = run(rag_service.search_knowledge_base("How does human oversight support responsible AI?"))

    assert getattr(results, "retrieval_mode") == "lexical_fallback"
    assert [result.id for result in results] == ["responsible-ai"]


def test_legacy_duplicate_vector_ids_are_normalized_for_rendering(monkeypatch):
    async def offline_embedding(_query: str):
        raise OpenAIError("embedding provider offline")

    monkeypatch.setattr(rag_service, "get_settings", rag_settings)
    monkeypatch.setattr(
        rag_service,
        "_load_store",
        lambda: [
            {"id": "ai-literacy:0", "document_name": "ai_literacy", "section_title": "Agency", "chunk_text": "Human agency remains central to AI literacy.", "embedding": [0.0] * 1536},
            {"id": "ai-literacy:0", "document_name": "ai_literacy", "section_title": "Boundaries", "chunk_text": "Human agency needs clear boundaries when working with AI.", "embedding": [0.0] * 1536},
        ],
    )
    monkeypatch.setattr(rag_service, "embed_text", offline_embedding)

    results = run(rag_service.search_knowledge_base("human agency and AI"))

    assert len(results) == 2
    assert len({result.id for result in results}) == 2


def test_provider_failure_returns_safe_deterministic_chat_answer(monkeypatch):
    configured = SimpleNamespace(openai_api_key="configured-only-for-test", rag_min_relevance_score=0.1)
    monkeypatch.setattr(ai_provider, "get_settings", lambda: configured)
    monkeypatch.setattr(ai_provider, "resolve_active_openai_api_key", lambda _settings: "configured-only-for-test")

    async def fake_rag(*_args, **_kwargs):
        return {
            "sources_used": [],
            "rag_run_id": None,
            "context_quality": "insufficient",
            "insufficient_context": True,
            "retrieval_mode": "unavailable",
        }

    class OfflineCompletions:
        async def create(self, **_kwargs):
            raise OpenAIError("chat provider offline")

    class OfflineClient:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(completions=OfflineCompletions())

    monkeypatch.setattr(ai_provider, "ask_with_rag", fake_rag)
    monkeypatch.setattr(ai_provider, "AsyncOpenAI", OfflineClient)

    response = run(
        ai_provider.generate_coach_response(
            "profile-1",
            "Does the LLM calculate my evidence score?",
            profile_context={"career_evidence": {"current_hypotheses": [], "practically_verified_skill_ids": [], "unresolved_gaps": []}},
        )
    )

    assert "does not calculate your evidence score" in str(response["answer"])
    assert response["retrieval_status"]["generation_mode"] == "provider_fallback"
    assert response["retrieval_status"]["provider_status"] == "unavailable"
    assert "temporarily unavailable" in str(response["confidence_note"])


def test_current_profile_context_excludes_superseded_records_and_other_users():
    db = db_session()
    owner = User(name="Owner", email="owner@example.test", hashed_password="x")
    other = User(name="Other", email="other@example.test", hashed_password="x")
    profile = Profile(user_id=owner.id, data={})
    db.add_all([owner, other])
    db.flush()
    profile.user_id = owner.id
    db.add(profile)
    db.flush()
    active = CareerHypothesis(profile_id=profile.id, user_id=owner.id, title="Human-Centred AI Product Designer", status="active")
    stale = CareerHypothesis(profile_id=profile.id, user_id=owner.id, title="Superseded direction", status="superseded")
    db.add_all([active, stale])
    db.flush()
    db.add_all(
        [
            CareerEvidenceGap(profile_id=profile.id, user_id=owner.id, hypothesis_id=active.id, skill_id="research", capability_label="User research", status="MISSING", importance=2),
            CareerEvidenceGap(profile_id=profile.id, user_id=owner.id, hypothesis_id=stale.id, skill_id="legacy", capability_label="Legacy gap", status="MISSING", importance=9),
        ]
    )
    db.commit()

    context = compact_profile_context(db, profile.id, owner.id)

    assert [item["title"] for item in context["career_evidence"]["current_hypotheses"]] == ["Human-Centred AI Product Designer"]
    assert [item["skill_id"] for item in context["career_evidence"]["unresolved_gaps"]] == ["research"]
    assert compact_profile_context(db, profile.id, other.id) == {}
