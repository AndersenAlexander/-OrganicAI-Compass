from __future__ import annotations

import asyncio
import hmac
import json
import time
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.profile import Profile
from app.models.recommendation import Recommendation
from app.models.roadmap_adaptation import RoadmapAction
from app.models.user import User
from app.privacy.service import ensure_privacy_settings
from app.schemas.chat_schema import ChatRequest
from app.services.ai_provider import stream_coach_response
from app.services.coach_chat_service import compact_profile_context, enrich_selected_context, get_or_create_conversation
from app.services.intent_service import classify_intent
from app.services.live_voice_metadata import save_latest_voice_turn

router = APIRouter()


class ElevenLabsLlmMessage(BaseModel):
    role: str
    content: str | None = None
    name: str | None = None
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None


class ElevenLabsChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str
    messages: list[ElevenLabsLlmMessage]
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool = True
    user_id: str | None = None
    tools: list[dict] | None = None
    tool_choice: object | str | None = None
    elevenlabs_extra_body: dict[str, Any] | None = None


def _bearer_secret(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def _require_secret(authorization: str | None) -> None:
    settings = get_settings()
    if not settings.elevenlabs_custom_llm_enabled:
        raise HTTPException(status_code=503, detail="Custom LLM integration is disabled.")
    configured = settings.elevenlabs_custom_llm_secret or ""
    supplied = _bearer_secret(authorization) or ""
    if not configured or not hmac.compare_digest(configured, supplied):
        raise HTTPException(status_code=401, detail="Invalid Custom LLM authorization.")


def _safe_uuid(value: str | None, field_name: str) -> str | None:
    if value in {None, ""}:
        return None
    try:
        UUID(str(value))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=f"{field_name} must be a valid UUID.") from error
    return str(value)


def _safe_text(value: Any, field_name: str, max_length: int, default: str = "") -> str:
    if value is None:
        return default
    text = str(value)
    if len(text) > max_length:
        raise HTTPException(status_code=422, detail=f"{field_name} is too long.")
    return text


def _last_user_message(messages: list[ElevenLabsLlmMessage]) -> str:
    for message in reversed(messages):
        if message.role == "user" and message.content and message.content.strip():
            text = message.content.strip()
            if len(text) > getattr(get_settings(), "max_chat_message_chars", 8_000):
                raise HTTPException(status_code=422, detail="User message is too long.")
            return text
    raise HTTPException(status_code=422, detail="A user message is required.")


def _validate_context(extra: dict[str, Any], db: Session) -> tuple[User, dict[str, Any]]:
    user_id = _safe_uuid(_safe_text(extra.get("organicai_user_id"), "organicai_user_id", 80), "organicai_user_id")
    if not user_id:
        raise HTTPException(status_code=422, detail="organicai_user_id is required.")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=422, detail="OrganicAI user was not found.")

    profile_id = _safe_text(extra.get("profile_id"), "profile_id", 80) or None
    if profile_id:
        profile = db.get(Profile, profile_id)
        if profile is None or profile.user_id != user.id:
            raise HTTPException(status_code=403, detail="Profile does not belong to the OrganicAI user.")

    app_conversation_id = _safe_uuid(
        _safe_text(extra.get("app_conversation_id"), "app_conversation_id", 80) or None,
        "app_conversation_id",
    )
    if app_conversation_id:
        conversation = db.get(Conversation, app_conversation_id)
        if conversation is None or conversation.user_id != user.id:
            raise HTTPException(status_code=403, detail="Conversation does not belong to the OrganicAI user.")

    selected_recommendation_id = _safe_uuid(
        _safe_text(extra.get("selected_recommendation_id"), "selected_recommendation_id", 80) or None,
        "selected_recommendation_id",
    )
    if selected_recommendation_id:
        recommendation = db.get(Recommendation, selected_recommendation_id)
        if recommendation is None or recommendation.profile_id != profile_id:
            raise HTTPException(status_code=403, detail="Recommendation does not belong to the selected profile.")

    roadmap_action_id = _safe_uuid(_safe_text(extra.get("roadmap_action_id"), "roadmap_action_id", 80) or None, "roadmap_action_id")
    if roadmap_action_id:
        action = db.get(RoadmapAction, roadmap_action_id)
        if action is None or action.profile_id != profile_id:
            raise HTTPException(status_code=403, detail="Roadmap action does not belong to the selected profile.")

    language = _safe_text(extra.get("language"), "language", 8, "en")
    if language not in {"en", "ro", "no"}:
        raise HTTPException(status_code=422, detail="Language must be one of en, ro, or no.")

    return user, {
        "profile_id": profile_id,
        "app_conversation_id": app_conversation_id,
        "elevenlabs_conversation_id": _safe_text(extra.get("elevenlabs_conversation_id"), "elevenlabs_conversation_id", 120),
        "route": _safe_text(extra.get("route"), "route", 240, "/"),
        "selected_profile_node": _safe_text(extra.get("selected_profile_node"), "selected_profile_node", 120) or None,
        "selected_recommendation_id": selected_recommendation_id,
        "roadmap_action_id": roadmap_action_id,
        "language": language,
        "voice_personality": _safe_text(extra.get("voice_personality"), "voice_personality", 80, "Calm Guide"),
        "conversation_mode": _safe_text(extra.get("conversation_mode"), "conversation_mode", 120, "Explain simply"),
        "theme": _safe_text(extra.get("theme"), "theme", 30, ""),
    }


def _sse_chunk(chat_id: str, created: int, content: str | None = None, finish_reason: str | None = None) -> str:
    delta = {"content": content} if content is not None else {}
    payload = {
        "id": chat_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": "organicai-coach",
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
    }
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/v1/chat/completions")
async def chat_completions(
    request: ElevenLabsChatCompletionRequest,
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> StreamingResponse:
    _require_secret(authorization)
    message = _last_user_message(request.messages)
    user, context = _validate_context(request.elevenlabs_extra_body or {}, db)

    profile_id = context["profile_id"]
    app_conversation_id = context["app_conversation_id"]
    privacy_settings = ensure_privacy_settings(db, user)
    persist_voice_transcript = bool(privacy_settings.voice_transcript_history_enabled)
    conversation = get_or_create_conversation(db, user, app_conversation_id, profile_id) if persist_voice_transcript else None
    user_id = user.id
    conversation_id = conversation.id if conversation else None
    write_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=db.get_bind())
    if conversation:
        db.add(Message(conversation_id=conversation_id, role="user", content=message, input_mode="voice"))
        db.commit()

    chat_request = ChatRequest(
        message=message,
        profile_id=profile_id,
        conversation_id=conversation_id,
        mode="live_voice",
        voice_personality=context["voice_personality"],
        conversation_mode=context["conversation_mode"],
        route=context["route"],
        selected_profile_node=context["selected_profile_node"],
        language=context["language"],
        client_context={
            "selected_recommendation_id": context["selected_recommendation_id"],
            "roadmap_action_id": context["roadmap_action_id"],
            "theme": context["theme"],
        },
    )
    classification = await classify_intent(message)
    profile_context = compact_profile_context(db, profile_id, user.id)
    enrich_selected_context(db, profile_id, chat_request, profile_context)
    chat_id = f"chatcmpl-{uuid4()}"
    created = int(time.time())

    async def on_complete(response: dict[str, object]) -> None:
        assistant_message_id = str(uuid4())
        answer = str(response["answer"])
        if persist_voice_transcript and conversation_id:
            with write_session_factory() as write_db:
                if write_db.get(Conversation, conversation_id):
                    write_db.add(Message(id=assistant_message_id, conversation_id=conversation_id, role="assistant", content=answer))
                    write_db.commit()
        elevenlabs_conversation_id = context["elevenlabs_conversation_id"]
        if persist_voice_transcript and elevenlabs_conversation_id:
            save_latest_voice_turn(
                user_id=user_id,
                elevenlabs_conversation_id=elevenlabs_conversation_id,
                payload={
                    "messageId": assistant_message_id,
                    "appConversationId": conversation_id,
                    "answer": answer,
                    "sourcesUsed": list(response.get("sources_used", [])),
                    "confidenceNote": str(response.get("confidence_note", "")),
                    "ethicalNote": str(response.get("ethical_note", "")),
                    "groundingStatus": str(response.get("grounding_status", "general")),
                    "profileSignals": list(response.get("profile_signals_used", [])),
                    "retrievalStatus": dict(response.get("retrieval_status", {})),
                    "timing": {},
                    "ragRunId": response.get("rag_run_id"),
                    "contextQuality": str(response.get("context_quality", "insufficient")),
                },
            )

    async def events():
        try:
            async for chunk in stream_coach_response(
                profile_id or "anonymous",
                message,
                "live_voice",
                context["voice_personality"],
                context["conversation_mode"],
                profile_context,
                context["language"],
                str(classification["intent"]),
                db if persist_voice_transcript else None,
                user_id,
                conversation_id,
                on_complete=on_complete,
            ):
                yield _sse_chunk(chat_id, created, content=chunk)
            yield _sse_chunk(chat_id, created, finish_reason="stop")
            yield "data: [DONE]\n\n"
        except asyncio.CancelledError:
            raise
        except Exception:
            yield _sse_chunk(chat_id, created, content="OrganicAI Coach is temporarily unavailable. Please continue with text chat.")
            yield _sse_chunk(chat_id, created, finish_reason="stop")
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
