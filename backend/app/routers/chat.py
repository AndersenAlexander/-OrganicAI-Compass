from typing import Annotated
from uuid import uuid4
from time import perf_counter
import re

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_optional_user
from app.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.models.fear_transform import FearTransformRecord
from app.models.recommendation import Recommendation
from app.models.roadmap_adaptation import RoadmapAction
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.ai_provider import generate_coach_response
from app.services.intent_service import classify_intent

router = APIRouter()


def compact_profile_context(db: Session, profile_id: str | None) -> dict:
    if not profile_id:
        return {}
    profile = db.get(Profile, profile_id)
    if not profile:
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
    fears = db.scalars(select(FearTransformRecord).where(FearTransformRecord.profile_id == profile_id).order_by(FearTransformRecord.created_at.desc()).limit(3)).all()
    signals = [str(primary_name), *strength_names[:3], *value_names[:2]]
    return {"primary_archetype": primary_name, "secondary_archetype": data.get("secondary_archetype"), "confirmed_strengths": strength_names, "values": value_names, "fears": [item.input_fear for item in fears], "ai_collaboration_style": collaboration_name, "contribution_domains": data.get("contribution_domains", []), "hidden_recommendations": feedback.get("hidden_recommendations", []), "user_notes": feedback.get("user_notes", {}), "roadmap": roadmap.data if roadmap else None, "profile_signals": [item for item in signals if item]}


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


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> ChatResponse:
    started = perf_counter()
    profile_id = request.profile_id or request.profileId
    conversation_id = request.conversation_id or request.conversationId
    conversation = get_or_create_conversation(db, current_user, conversation_id, profile_id)
    classify_started = perf_counter()
    classification = await classify_intent(request.message)
    classification_ms = int((perf_counter() - classify_started) * 1000)
    command = classification.get("command")
    if classification["intent"] == "ui_command" and command:
        name = str(command["name"])
        answer = f"Command recognized: {name.replace('_', ' ')}."
        return ChatResponse(answer=answer, conversation_id=conversation.id if conversation else conversation_id or f"anonymous-{uuid4()}", message_id=str(uuid4()), intent="ui_command", executed_command=command, confidence_note="Deterministic command match.", grounding_status="general", timing={"classification_ms": classification_ms, "total_ms": int((perf_counter()-started)*1000)})
    if classification["intent"] == "contextual_command" and not request.selected_profile_node and command and command["name"] in {"explain_selected_node", "confirm_selected_node", "hide_selected_recommendation", "open_selected_learning_path"}:
        return ChatResponse(answer="Please open your Human Potential Map and select a node first.", conversation_id=conversation.id if conversation else conversation_id or f"anonymous-{uuid4()}", message_id=str(uuid4()), intent="contextual_command", executed_command=None, confidence_note="Required page context was missing.", grounding_status="general", timing={"classification_ms": classification_ms, "total_ms": int((perf_counter()-started)*1000)})

    user_message_id = str(uuid4())
    if conversation:
        user_message = Message(
            id=user_message_id,
            conversation_id=conversation.id,
            role="user",
            content=request.message,
            input_mode=request.mode,
        )
        db.add(user_message)
        db.commit()

    profile_context = compact_profile_context(db, profile_id)
    recommendation_id = request.client_context.get("recommendation_id") if request.client_context else None
    if not recommendation_id:
        match = re.search(r"\b[0-9a-f]{8}-[0-9a-f-]{27,36}\b", request.message.lower())
        recommendation_id = match.group(0) if match else None
    if recommendation_id:
        recommendation = db.get(Recommendation, str(recommendation_id))
        if recommendation and recommendation.profile_id == profile_id:
            profile_context["selected_recommendation"] = {"id": recommendation.id, "title": recommendation.title, "summary": recommendation.summary, "reason": recommendation.reason, "signals": recommendation.profile_signals_json, "sources": recommendation.rag_sources_json, "first_action": recommendation.first_action, "ethical_cautions": recommendation.ethical_cautions_json}
    action_id = request.client_context.get("roadmap_action_id") if request.client_context else None
    if not action_id:
        match = re.search(r"\b[0-9a-f]{8}-[0-9a-f-]{27,36}\b", request.message.lower())
        action_id = match.group(0) if match else None
    if action_id:
        action = db.get(RoadmapAction, str(action_id))
        if action and action.profile_id == profile_id:
            profile_context["selected_roadmap_action"] = {"id":action.id,"title":action.title,"description":action.description,"reason":action.reason,"first_step":action.first_step,"success_criteria":action.success_criteria,"status":action.status,"horizon":action.horizon,"source_type":action.source_type,"profile_signals":action.profile_signals_json,"rag_sources":action.rag_sources_json}
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
    )
    generation_ms = int((perf_counter() - generation_started) * 1000)
    assistant_message_id = str(uuid4())
    response_conversation_id = conversation.id if conversation else conversation_id or f"anonymous-{uuid4()}"

    if conversation:
        assistant_message = Message(
            id=assistant_message_id,
            conversation_id=conversation.id,
            role="assistant",
            content=str(response["answer"]),
        )
        db.add(assistant_message)
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
        timing={"classification_ms": classification_ms, "generation_ms": generation_ms, "total_ms": int((perf_counter()-started)*1000)},
    )


@router.get("/{profile_id}/history")
async def chat_history(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> list[dict[str, str | None]]:
    if current_user is None:
        return []

    conversation = db.scalar(
        select(Conversation)
        .where(Conversation.user_id == current_user.id, Conversation.profile_id == profile_id)
        .order_by(Conversation.updated_at.desc())
    )
    if conversation is None:
        return []

    messages = db.scalars(
        select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at.asc())
    ).all()
    return [
        {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "createdAt": message.created_at.isoformat(),
            "audioUrl": message.audio_url,
            "inputMode": message.input_mode,
        }
        for message in messages
    ]
