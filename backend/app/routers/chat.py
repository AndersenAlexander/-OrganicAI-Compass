from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_optional_user
from app.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.coach_chat_service import handle_chat_request

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> ChatResponse:
    return await handle_chat_request(request, db, current_user)


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
