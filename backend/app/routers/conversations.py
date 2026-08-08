from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_optional_user
from app.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User

router = APIRouter()

class ConversationCreate(BaseModel):
    profile_id: str | None = None
    title: str = "AI Coach conversation"

def public(item: Conversation) -> dict:
    return {"id": item.id, "profile_id": item.profile_id, "title": item.title, "created_at": item.created_at.isoformat(), "updated_at": item.updated_at.isoformat()}

@router.get("")
async def list_conversations(db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> list[dict]:
    if not user: return []
    return [public(item) for item in db.scalars(select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.updated_at.desc())).all()]

@router.post("")
async def create_conversation(payload: ConversationCreate, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict:
    if not user: raise HTTPException(status_code=401, detail="Authentication required for server-side history")
    item=Conversation(user_id=user.id,profile_id=payload.profile_id,title=payload.title[:255]);db.add(item);db.commit();db.refresh(item);return public(item)

@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict:
    item=db.get(Conversation,conversation_id)
    if not item or not user or item.user_id != user.id: raise HTTPException(status_code=404,detail="Conversation not found")
    messages=db.scalars(select(Message).where(Message.conversation_id==item.id).order_by(Message.created_at.asc())).all()
    return {**public(item),"messages":[{"id":message.id,"role":message.role,"content":message.content,"input_mode":message.input_mode,"created_at":message.created_at.isoformat()} for message in messages]}

@router.delete("/{conversation_id}",status_code=204)
async def delete_conversation(conversation_id: str, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> Response:
    item=db.get(Conversation,conversation_id)
    if not item or not user or item.user_id != user.id: raise HTTPException(status_code=404,detail="Conversation not found")
    db.delete(item);db.commit();return Response(status_code=204)
