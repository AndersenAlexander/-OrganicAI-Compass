from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services.ai_provider import (
    CoachGenerationContext,
    _deterministic_answer,
    build_coach_messages,
    prepare_coach_generation_context,
)
from app.services import ai_provider, rag_service
from app.services.coach_grounding import classify_grounding_source
from app.services.knowledge_loader import load_knowledge_chunks


BACKEND_ROOT = Path(__file__).resolve().parents[1]
MASTER_PATH = BACKEND_ROOT / "knowledge_base" / "organicai_compass_master_knowledge.md"
DEFENCE_PATH = BACKEND_ROOT / "knowledge_base" / "organicai_compass_defence_qa.md"
GOLDEN_PATH = BACKEND_ROOT / "evals" / "organicai_compass_golden_questions.json"


def generation_context(
    message: str,
    source: str = "STATIC_KB",
    profile_context: dict | None = None,
    mode: str = "text",
) -> CoachGenerationContext:
    profile_context = profile_context or {}
    return CoachGenerationContext(
        message=message,
        mode=mode,
        voice_personality="Calm Guide",
        conversation_mode="Explain simply",
        profile_context=profile_context,
        language="en",
        intent="conversational_question",
        sources=[],
        source_context="No sources.",
        suggested_actions=[],
        profile_signals=list(profile_context.get("profile_signals", [])),
        confidence_note="Test confidence.",
        ethical_note="Test ethical note.",
        grounding_status="general",
        retrieval_status={},
        rag_run_id=None,
        context_quality="insufficient",
        insufficient_context=True,
        question_source=source,
    )


def test_canonical_master_contains_all_41_numbered_sections():
    text = MASTER_PATH.read_text(encoding="utf-8")
    headings = re.findall(r"^## (\d+)\.\s+(.+)$", text, flags=re.MULTILINE)

    assert [int(number) for number, _title in headings] == list(range(1, 42))
    assert headings[0][1] == "Platform overview"
    assert headings[-1][1] == "Master's dissertation context"


def test_defence_bank_contains_at_least_100_unique_questions():
    text = DEFENCE_PATH.read_text(encoding="utf-8")
    questions = re.findall(r"^### ([A-Z]\d+)\.\s+(.+\?)$", text, flags=re.MULTILINE)

    assert len(questions) >= 100
    assert len({question_id for question_id, _question in questions}) == len(questions)
    assert len({question for _question_id, question in questions}) == len(questions)


def test_canonical_knowledge_chunks_have_unique_ids_and_metadata():
    chunks = load_knowledge_chunks()
    canonical = [chunk for chunk in chunks if chunk.document_name.startswith("organicai_compass_")]

    assert len({chunk.document_name for chunk in chunks}) >= 19
    assert len(chunks) >= 196
    assert len({chunk.id for chunk in chunks}) == len(chunks)
    assert len(canonical) == 151
    assert len({(chunk.document_name, chunk.section_title) for chunk in canonical}) == len(canonical)
    assert all(chunk.document_name and chunk.section_title and chunk.chunk_text for chunk in chunks)
    assert max(len(chunk.chunk_text.split()) for chunk in chunks) <= 640


def test_available_embedding_retrieval_prefers_matching_canonical_heading(monkeypatch):
    records = [
        {
            "id": "canonical:0:0",
            "document_name": "organicai_compass_defence_qa",
            "section_title": "C3. Does the LLM calculate career scores?",
            "chunk_text": "No. Deterministic application rules calculate scores; the LLM may explain them.",
            "embedding": [1.0, 0.0],
        },
        {
            "id": "unrelated:0:0",
            "document_name": "unrelated",
            "section_title": "Other topic",
            "chunk_text": "A different topic.",
            "embedding": [0.0, 1.0],
        },
    ]

    async def available_embedding(_query: str):
        return [1.0, 0.0]

    monkeypatch.setattr(rag_service, "get_settings", lambda: SimpleNamespace(rag_top_k=2))
    monkeypatch.setattr(rag_service, "_load_store", lambda: records)
    monkeypatch.setattr(rag_service, "embed_text", available_embedding)

    results = asyncio.run(rag_service.search_knowledge_base("Does the LLM calculate career scores?"))

    assert results.retrieval_mode == "semantic"
    assert results[0].id == "canonical:0:0"
    assert results[0].section_title.startswith("C3.")


@pytest.mark.parametrize(
    ("question", "expected_source"),
    [
        ("What is OrganicAI Compass?", "STATIC_KB"),
        ("Does the LLM calculate my evidence score?", "STATIC_KB"),
        ("What is my current career hypothesis?", "CAREER_HYPOTHESIS"),
        ("What evidence has been verified for my current direction?", "EVIDENCE_PASSPORT"),
        ("What evidence has been practically verified?", "EVIDENCE_PASSPORT"),
        ("Which career hypothesis is currently strongest?", "CAREER_HYPOTHESIS"),
        ("What is still unresolved for my current direction?", "CAREER_HYPOTHESIS"),
        ("What is still unresolved?", "CAREER_HYPOTHESIS"),
        ("Which skills still need verification?", "EVIDENCE_PASSPORT"),
        ("Which evidence gaps remain?", "EVIDENCE_PASSPORT"),
        ("Which important evidence gaps are still unresolved?", "EVIDENCE_PASSPORT"),
        ("Which experiment did I complete?", "EXPERIMENT"),
        ("What did that experiment verify?", "EXPERIMENT"),
        ("What is my next useful experiment?", "EXPERIMENT"),
        ("What experiment should reduce that uncertainty?", "EXPERIMENT"),
        ("What is in my current roadmap?", "ROADMAP"),
        ("What applications do I currently have?", "EMPLOYMENT_JOURNEY"),
        ("What interview stage am I in?", "EMPLOYMENT_JOURNEY"),
        ("What did I decide and why?", "DECISION_JOURNAL"),
        ("What are my current strengths?", "USER_PROFILE"),
    ],
)
def test_question_routes_to_required_grounding_source(question: str, expected_source: str):
    assert classify_grounding_source(question) == expected_source


def test_user_context_fallback_never_fills_missing_record_from_static_knowledge():
    context = generation_context(
        "What is in my current roadmap?",
        source="ROADMAP",
        profile_context={},
    )

    answer = _deterministic_answer(context)

    assert "do not see persisted roadmap actions" in answer
    assert "generic suggestion" in answer


def test_personal_evidence_answer_uses_only_persisted_context():
    context = generation_context(
        "What evidence has been verified for my current direction?",
        source="EVIDENCE_PASSPORT",
        profile_context={
            "career_evidence": {
                "current_hypotheses": [{"title": "Human-Centred AI Product Designer"}],
                "practically_verified_skill_ids": ["user-research"],
                "unresolved_gaps": [],
                "recent_experiments": [],
            }
        },
    )

    answer = _deterministic_answer(context)

    assert "user-research" in answer
    assert "read-only" in answer
    assert "Human-Centred AI Product Designer" not in answer


def test_evidence_gap_question_never_substitutes_verified_skills_when_no_gap_is_persisted():
    context = generation_context(
        "Which evidence gaps remain unresolved?",
        source="EVIDENCE_PASSPORT",
        profile_context={
            "career_evidence": {
                "practically_verified_skill_ids": ["user-research"],
                "unresolved_gaps": [],
            }
        },
    )

    answer = _deterministic_answer(context)

    assert "do not see persisted unresolved evidence gaps" in answer.lower()
    assert "user-research" not in answer


def test_personal_hypothesis_questions_use_persisted_rank_and_unresolved_gaps():
    context = generation_context(
        "What is still unresolved?",
        source="CAREER_HYPOTHESIS",
        profile_context={
            "career_evidence": {
                "current_hypotheses": [{"title": "Human-Centred AI Product Designer"}],
                "unresolved_gaps": [{"skill_id": "prototype-testing", "capability_label": "Prototype testing"}],
            }
        },
    )

    assert "Prototype testing" in _deterministic_answer(context)

    strongest = _deterministic_answer(
        generation_context(
            "What is my strongest career hypothesis?",
            source="CAREER_HYPOTHESIS",
            profile_context={"career_evidence": {"current_hypotheses": [{"title": "Human-Centred AI Product Designer"}]}},
        )
    )
    assert "highest currently persisted" in strongest


def test_user_context_never_retrieves_or_injects_static_knowledge(monkeypatch):
    async def unexpected_rag(*_args, **_kwargs):
        raise AssertionError("Static RAG must not run for a user-context question")

    monkeypatch.setattr("app.services.ai_provider.ask_with_rag", unexpected_rag)

    context = asyncio.run(
        prepare_coach_generation_context(
            "profile-1",
            "What evidence has been verified for my current direction?",
            profile_context={"career_evidence": {"practically_verified_skill_ids": ["user-research"]}},
        )
    )
    messages = build_coach_messages(context)

    assert context.question_source == "EVIDENCE_PASSPORT"
    assert context.sources == []
    assert context.rag_run_id is None
    assert context.retrieval_status["retrieval_mode"] == "not_requested"
    assert "No static Knowledge Base context is supplied" in messages[1]["content"]


def test_deterministic_safety_answers_preserve_human_control():
    scoring = _deterministic_answer(generation_context("Does the LLM calculate my evidence score?"))
    decision = _deterministic_answer(generation_context("Choose my career for me."))

    assert "does not calculate" in scoring
    assert "deterministic" in scoring
    assert "cannot choose your career" in decision
    assert "decision remains yours" in decision


def test_prompt_contains_grounding_policy_and_source_boundary():
    messages = build_coach_messages(
        generation_context(
            "What applications do I currently have?",
            source="EMPLOYMENT_JOURNEY",
            profile_context={"employment_journey": {"applications": [], "interviews": []}},
        )
    )

    assert "Deterministic scores come from versioned application rules" in messages[0]["content"]
    assert "Required grounding source: EMPLOYMENT_JOURNEY" in messages[1]["content"]
    assert "If the required record is empty or absent, say it is unavailable" in messages[1]["content"]


def test_live_voice_prompt_is_explicitly_shorter_and_does_not_read_metadata():
    messages = build_coach_messages(generation_context("What is OrganicAI Compass?", mode="live_voice"))

    assert "keep it concise" in messages[0]["content"]
    assert "do not read technical metadata or citations aloud" in messages[0]["content"]


def test_presentation_demo_questions_have_safe_text_fallbacks(monkeypatch):
    async def static_rag(*_args, **_kwargs):
        return {
            "sources_used": [],
            "rag_run_id": None,
            "context_quality": "insufficient",
            "insufficient_context": True,
            "retrieval_mode": "unavailable",
        }

    monkeypatch.setattr(ai_provider, "ask_with_rag", static_rag)
    monkeypatch.setattr(ai_provider, "get_settings", lambda: SimpleNamespace(openai_api_key=None, rag_min_relevance_score=0.1))
    monkeypatch.setattr(ai_provider, "resolve_active_openai_api_key", lambda _settings: None)

    demo_context = {
        "profile_signals": ["Systems Thinking"],
        "career_evidence": {
            "current_hypotheses": [{"title": "Human-Centred AI Product Designer"}],
            "practically_verified_skill_ids": ["user-research"],
            "unresolved_gaps": [{"skill_id": "prototype-testing", "capability_label": "Prototype testing"}],
            "recent_experiments": [],
        },
        "roadmap_state": {"actions": [{"title": "Review an evidence gap", "status": "planned"}]},
    }
    presentation_questions = [
        ("What is OrganicAI Compass?", "human-centred"),
        ("Why was this platform created?", "research prototype"),
        ("How does the Human Diagnostic work?", "self-report"),
        ("Does the LLM calculate my career scores?", "does not calculate"),
        ("What does Evidence Strength mean?", "deterministic"),
        ("What is a career hypothesis?", "provisional"),
        ("What evidence has been verified for me?", "user-research"),
        ("Which evidence gaps remain?", "prototype testing"),
        ("How do career experiments work?", "reversible"),
        ("Can you choose my career for me?", "decision remains yours"),
        ("What is the Human-AI Growth Roadmap?", "seven-day"),
        ("How is my data protected?", "authentication"),
        ("What role does ElevenLabs play?", "webrtc"),
        ("What happens when an AI provider is unavailable?", "degrade safely"),
        ("What are the limitations of this prototype?", "no recorded participant-outcome"),
    ]

    for question, expected_concept in presentation_questions:
        response = asyncio.run(
            ai_provider.generate_coach_response(
                "demo-profile",
                question,
                profile_context=demo_context,
            )
        )
        assert expected_concept in str(response["answer"]).lower(), question

    personal = asyncio.run(
        ai_provider.generate_coach_response(
            "demo-profile",
            "What evidence has been verified for me?",
            profile_context=demo_context,
        )
    )
    assert personal["retrieval_status"]["retrieval_mode"] == "not_requested"
    assert personal["sources_used"] == []


def test_golden_set_has_required_coverage_and_unique_ids():
    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    categories = {item["category"] for item in golden}
    required_categories = {
        "platform_facts",
        "scoring",
        "evidence",
        "roadmap",
        "employment_journey",
        "coach_and_rag",
        "voice",
        "privacy",
        "human_control",
        "limitations",
        "user_context",
    }

    assert len(golden) >= 40
    assert len({item["id"] for item in golden}) == len(golden)
    assert required_categories <= categories
    assert all(item["expected_concepts"] for item in golden)
    assert all(classify_grounding_source(item["question"]) == item["source"] for item in golden)


@pytest.mark.parametrize(
    ("question", "expected_source"),
    [
        ("What is OrganicAI Compass?", "STATIC_KB"),
        ("Why was this platform created?", "STATIC_KB"),
        ("Does the LLM calculate my career scores?", "STATIC_KB"),
        ("What is my current career hypothesis?", "CAREER_HYPOTHESIS"),
        ("What evidence has been practically verified for my current direction?", "EVIDENCE_PASSPORT"),
        ("Which evidence gaps remain unresolved?", "EVIDENCE_PASSPORT"),
        ("Which important evidence gaps are still unresolved?", "EVIDENCE_PASSPORT"),
        ("What experiment should reduce that uncertainty?", "EXPERIMENT"),
        ("What happens after an experiment is reviewed?", "STATIC_KB"),
        ("How does Evidence Passport differ from self-reported skills?", "STATIC_KB"),
        ("Can you choose my career for me?", "STATIC_KB"),
        ("What is the Human-AI Growth Roadmap?", "STATIC_KB"),
        ("Why did you use RAG rather than fine-tuning?", "STATIC_KB"),
        ("What happens if OpenAI is unavailable?", "STATIC_KB"),
        ("What role does ElevenLabs play?", "STATIC_KB"),
        ("What are the main limitations of this prototype?", "STATIC_KB"),
    ],
)
def test_presentation_sequence_routes_to_its_required_source(question: str, expected_source: str):
    assert classify_grounding_source(question) == expected_source
