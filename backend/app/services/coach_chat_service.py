from __future__ import annotations

import re
from time import perf_counter
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.assessment import SkillEvidence
from app.models.career_resilience import (
    CareerEvidenceGap,
    CareerExperimentResult,
    CareerExperimentSession,
    CareerExperimentTemplate,
    CareerHypothesis,
    SkillEvidenceConfidence,
)
from app.models.fear_transform import FearTransformRecord
from app.models.innovation_extension import CareerDecisionJournalEntry
from app.models.interview_journey import Interview
from app.models.market_application import JobApplication
from app.models.message import Message
from app.models.profile import Profile
from app.models.recommendation import Recommendation
from app.models.roadmap import Roadmap
from app.models.roadmap_adaptation import RoadmapAction
from app.models.user import User
from app.privacy.service import ensure_privacy_settings
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.ai_provider import generate_coach_response
from app.services.intent_service import classify_intent


def compact_profile_context(db: Session, profile_id: str | None, owner_user_id: str | None = None) -> dict:
    if not profile_id:
        return {}
    profile = db.get(Profile, profile_id)
    if not profile:
        return {}
    if owner_user_id is not None and profile.user_id != owner_user_id:
        return {}
    data = profile.data
    feedback = data.get("user_feedback", {})
    primary = data.get("primary_archetype", {})
    primary_name = feedback.get("archetype_override") or (primary.get("name") if isinstance(primary, dict) else primary)
    strengths = data.get("strengths", [])
    strength_names = [item.get("name") if isinstance(item, dict) else str(item) for item in strengths]
    values = data.get("values", [])
    value_names = [item.get("name") if isinstance(item, dict) else str(item) for item in values]
    collaboration = data.get("ai_collaboration_style", {})
    collaboration_name = collaboration.get("name") if isinstance(collaboration, dict) else collaboration
    roadmap = db.scalar(select(Roadmap).where(Roadmap.profile_id == profile_id).order_by(Roadmap.created_at.desc()))
    fears = db.scalars(
        select(FearTransformRecord).where(FearTransformRecord.profile_id == profile_id).order_by(FearTransformRecord.created_at.desc()).limit(3)
    ).all()
    current_hypotheses = db.scalars(
        select(CareerHypothesis)
        .where(CareerHypothesis.profile_id == profile_id, CareerHypothesis.status == "active")
        .order_by(CareerHypothesis.current_alignment_score.desc(), CareerHypothesis.updated_at.desc())
        .limit(3)
    ).all()
    practical_evidence = db.scalars(
        select(SkillEvidenceConfidence)
        .join(SkillEvidence, SkillEvidence.id == SkillEvidenceConfidence.skill_evidence_id)
        .where(
            SkillEvidenceConfidence.profile_id == profile_id,
            SkillEvidenceConfidence.strength_label == "Practically verified",
            SkillEvidence.verification_status != "provisional_pending_review",
        )
        .order_by(SkillEvidenceConfidence.skill_id)
    ).all()
    recent_experiments = db.scalars(
        select(CareerExperimentSession)
        .where(CareerExperimentSession.profile_id == profile_id)
        .order_by(CareerExperimentSession.updated_at.desc())
        .limit(3)
    ).all()
    experiment_template_ids = sorted({item.experiment_template_id for item in recent_experiments})
    experiment_templates = {
        item.id: item
        for item in (
            db.scalars(select(CareerExperimentTemplate).where(CareerExperimentTemplate.id.in_(experiment_template_ids))).all()
            if experiment_template_ids
            else []
        )
    }
    experiment_session_ids = [item.id for item in recent_experiments]
    experiment_results: dict[str, CareerExperimentResult] = {}
    if experiment_session_ids:
        for item in db.scalars(
            select(CareerExperimentResult)
            .where(CareerExperimentResult.session_id.in_(experiment_session_ids))
            .order_by(CareerExperimentResult.created_at.desc())
        ).all():
            experiment_results.setdefault(item.session_id, item)
    roadmap_actions = (
        db.scalars(
            select(RoadmapAction)
            .where(RoadmapAction.roadmap_id == roadmap.id)
            .order_by(RoadmapAction.priority, RoadmapAction.updated_at.desc())
            .limit(8)
        ).all()
        if roadmap
        else []
    )
    applications = db.scalars(
        select(JobApplication)
        .where(JobApplication.profile_id == profile_id)
        .order_by(JobApplication.updated_at.desc())
        .limit(5)
    ).all()
    interviews = db.scalars(
        select(Interview)
        .where(Interview.profile_id == profile_id)
        .order_by(Interview.updated_at.desc())
        .limit(5)
    ).all()
    decision_entries = db.scalars(
        select(CareerDecisionJournalEntry)
        .where(CareerDecisionJournalEntry.profile_id == profile_id)
        .order_by(CareerDecisionJournalEntry.updated_at.desc())
        .limit(5)
    ).all()
    active_hypothesis_ids = [item.id for item in current_hypotheses]
    unresolved_gaps = (
        db.scalars(
            select(CareerEvidenceGap)
            .where(
                CareerEvidenceGap.profile_id == profile_id,
                CareerEvidenceGap.hypothesis_id.in_(active_hypothesis_ids),
                CareerEvidenceGap.status.notin_(("RESOLVED", "ARCHIVED", "EVIDENCE_SUFFICIENT")),
            )
            .order_by(CareerEvidenceGap.importance.desc(), CareerEvidenceGap.updated_at.desc())
            .limit(6)
        ).all()
        if active_hypothesis_ids
        else []
    )
    signals = [str(primary_name), *strength_names[:3], *value_names[:2]]
    return {
        "primary_archetype": primary_name,
        "secondary_archetype": data.get("secondary_archetype"),
        "confirmed_strengths": strength_names,
        "values": value_names,
        "fears": [item.input_fear for item in fears],
        "ai_collaboration_style": collaboration_name,
        "contribution_domains": data.get("contribution_domains", []),
        "hidden_recommendations": feedback.get("hidden_recommendations", []),
        "user_notes": feedback.get("user_notes", {}),
        "roadmap": roadmap.data if roadmap else None,
        "roadmap_state": {
            "id": roadmap.id if roadmap else None,
            "actions": [
                {
                    "id": item.id,
                    "title": item.title,
                    "status": item.status,
                    "horizon": item.horizon,
                    "priority": item.priority,
                    "source_type": item.source_type,
                }
                for item in roadmap_actions
            ],
        },
        # These are persisted records only. The Coach receives no inferred
        # profile change and no authority to mutate the roadmap from them.
        "career_evidence": {
            "current_hypotheses": [
                {
                    "title": item.title,
                    "canonical_direction_id": item.canonical_direction_id,
                    "version": item.current_version_number,
                    "uncertainty_label": item.uncertainty_label,
                }
                for item in current_hypotheses
            ],
            "practically_verified_skill_ids": sorted({item.skill_id for item in practical_evidence}),
            "recent_experiment_statuses": [
                {"id": item.id, "status": item.status, "hypothesis_id": item.hypothesis_id}
                for item in recent_experiments
            ],
            "recent_experiments": [
                {
                    "id": item.id,
                    "title": experiment_templates[item.experiment_template_id].title if item.experiment_template_id in experiment_templates else item.experiment_template_id,
                    "status": item.status,
                    "hypothesis_id": item.hypothesis_id,
                    "evidence_gap_id": item.evidence_gap_id,
                    "result_label": experiment_results[item.id].overall_label if item.id in experiment_results else None,
                    "evidence_created": experiment_results[item.id].evidence_created_json if item.id in experiment_results else [],
                }
                for item in recent_experiments
            ],
            "unresolved_gaps": [
                {
                    "skill_id": item.skill_id,
                    "capability_label": item.capability_label,
                    "status": item.status,
                    "importance": item.importance,
                }
                for item in unresolved_gaps
            ],
        },
        "employment_journey": {
            "applications": [
                {
                    "id": item.id,
                    "title": item.title,
                    "organisation": item.organisation,
                    "status": item.status,
                    "next_action": item.next_action,
                }
                for item in applications
            ],
            "interviews": [
                {
                    "id": item.id,
                    "role": item.role,
                    "organisation": item.organisation,
                    "stage_type": item.stage_type,
                    "status": item.status,
                    "preparation_status": item.preparation_status,
                    "interview_result": item.interview_result,
                }
                for item in interviews
            ],
        },
        "decision_journal": [
            {
                "id": item.id,
                "title": item.title,
                "status": item.status,
                "selected_option": item.selected_option,
                "confidence": item.confidence,
                "reversibility": item.reversibility,
                "outcome_status": item.outcome_status,
            }
            for item in decision_entries
        ],
        "profile_signals": [item for item in signals if item],
    }


def get_or_create_conversation(
    db: Session,
    current_user: User | None,
    conversation_id: str | None,
    profile_id: str | None,
) -> Conversation | None:
    if current_user is None:
        return None

    if conversation_id:
        conversation = db.get(Conversation, conversation_id)
        if conversation and conversation.user_id == current_user.id:
            return conversation

    conversation = Conversation(user_id=current_user.id, profile_id=profile_id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def selected_uuid_from_text(text: str) -> str | None:
    match = re.search(r"\b[0-9a-f]{8}-[0-9a-f-]{27,36}\b", text.lower())
    return match.group(0) if match else None


def enrich_selected_context(db: Session, profile_id: str | None, request: ChatRequest, profile_context: dict) -> None:
    if not profile_id:
        return

    client_context = request.client_context or {}
    recommendation_id = client_context.get("recommendation_id") or client_context.get("selected_recommendation_id")
    if not recommendation_id:
        recommendation_id = selected_uuid_from_text(request.message)
    if recommendation_id:
        recommendation = db.get(Recommendation, str(recommendation_id))
        if recommendation and recommendation.profile_id == profile_id:
            profile_context["selected_recommendation"] = {
                "id": recommendation.id,
                "title": recommendation.title,
                "summary": recommendation.summary,
                "reason": recommendation.reason,
                "signals": recommendation.profile_signals_json,
                "sources": recommendation.rag_sources_json,
                "first_action": recommendation.first_action,
                "ethical_cautions": recommendation.ethical_cautions_json,
            }

    action_id = client_context.get("roadmap_action_id")
    if not action_id:
        action_id = selected_uuid_from_text(request.message)
    if action_id:
        action = db.get(RoadmapAction, str(action_id))
        if action and action.profile_id == profile_id:
            profile_context["selected_roadmap_action"] = {
                "id": action.id,
                "title": action.title,
                "description": action.description,
                "reason": action.reason,
                "first_step": action.first_step,
                "success_criteria": action.success_criteria,
                "status": action.status,
                "horizon": action.horizon,
                "source_type": action.source_type,
                "profile_signals": action.profile_signals_json,
                "rag_sources": action.rag_sources_json,
            }


async def handle_chat_request(request: ChatRequest, db: Session, current_user: User | None) -> ChatResponse:
    started = perf_counter()
    profile_id = request.profile_id or request.profileId
    conversation_id = request.conversation_id or request.conversationId
    if profile_id and current_user:
        profile = db.get(Profile, profile_id)
        if profile is None or profile.user_id != current_user.id:
            # A caller may still use the Coach without profile context, but it
            # must never attach an arbitrary profile id to a conversation,
            # RAG run, or selected-record lookup.
            profile_id = None
    privacy_settings = ensure_privacy_settings(db, current_user) if current_user else None
    persist_conversation = bool(privacy_settings.conversation_history_enabled) if privacy_settings else False
    conversation = get_or_create_conversation(db, current_user, conversation_id, profile_id) if persist_conversation else None

    classify_started = perf_counter()
    classification = await classify_intent(request.message)
    classification_ms = int((perf_counter() - classify_started) * 1000)
    command = classification.get("command")
    response_conversation_id = conversation.id if conversation else f"ephemeral-{uuid4()}"

    if classification["intent"] == "ui_command" and command:
        name = str(command["name"])
        return ChatResponse(
            answer=f"Command recognized: {name.replace('_', ' ')}.",
            conversation_id=response_conversation_id,
            message_id=str(uuid4()),
            intent="ui_command",
            executed_command=command,
            confidence_note="Deterministic command match.",
            grounding_status="general",
            timing={"classification_ms": classification_ms, "total_ms": int((perf_counter() - started) * 1000)},
        )

    if (
        classification["intent"] == "contextual_command"
        and not request.selected_profile_node
        and command
        and command["name"] in {"explain_selected_node", "confirm_selected_node", "hide_selected_recommendation", "open_selected_learning_path"}
    ):
        return ChatResponse(
            answer="Please open your Human Potential Map and select a node first.",
            conversation_id=response_conversation_id,
            message_id=str(uuid4()),
            intent="contextual_command",
            executed_command=None,
            confidence_note="Required page context was missing.",
            grounding_status="general",
            timing={"classification_ms": classification_ms, "total_ms": int((perf_counter() - started) * 1000)},
        )

    if conversation:
        db.add(Message(conversation_id=conversation.id, role="user", content=request.message, input_mode=request.mode))
        db.commit()

    profile_context = compact_profile_context(db, profile_id, current_user.id if current_user else None)
    enrich_selected_context(db, profile_id, request, profile_context)

    generation_started = perf_counter()
    response = await generate_coach_response(
        profile_id or "anonymous",
        request.message,
        request.mode,
        request.voice_personality,
        request.conversation_mode,
        profile_context,
        request.language,
        str(classification["intent"]),
        db if persist_conversation else None,
        current_user.id if current_user else None,
        conversation.id if conversation else conversation_id,
    )
    generation_ms = int((perf_counter() - generation_started) * 1000)
    assistant_message_id = str(uuid4())

    if conversation:
        db.add(Message(conversation_id=conversation.id, role="assistant", content=str(response["answer"])))
        db.commit()

    return ChatResponse(
        answer=str(response["answer"]),
        conversation_id=response_conversation_id,
        message_id=assistant_message_id,
        suggested_actions=list(response.get("suggested_actions", [])),
        confidence_note=str(response.get("confidence_note", "")),
        sources_used=list(response.get("sources_used", [])),
        ethical_note=str(response.get("ethical_note", "")),
        intent=str(classification["intent"]),
        executed_command=command if classification["intent"] == "contextual_command" else None,
        profile_signals_used=list(response.get("profile_signals_used", [])),
        grounding_status=str(response.get("grounding_status", "general")),
        retrieval_status=dict(response.get("retrieval_status", {})),
        audio_available=False,
        timing={
            "classification_ms": classification_ms,
            "generation_ms": generation_ms,
            "total_ms": int((perf_counter() - started) * 1000),
        },
        rag_run_id=response.get("rag_run_id"),
        context_quality=str(response.get("context_quality", "insufficient")),
        insufficient_context=bool(response.get("insufficient_context", False)),
    )
