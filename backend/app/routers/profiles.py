from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from pydantic import BaseModel, Field

from app.auth.dependencies import get_optional_user
from app.database import get_db
from app.models.profile import Profile
from app.models.user import User
from app.services.profile_authorization import require_owned_profile

router = APIRouter()


class ProfileFeedback(BaseModel):
    confirmed_nodes: list[str] = Field(default_factory=list)
    hidden_recommendations: list[str] = Field(default_factory=list)
    strength_adjustments: dict[str, int] = Field(default_factory=dict)
    archetype_override: str | None = None
    user_notes: dict[str, str] = Field(default_factory=dict)


def default_feedback() -> dict:
    return ProfileFeedback().model_dump()


@router.get("/{profile_id}")
async def get_profile(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> dict:
    profile = require_owned_profile(db, profile_id, current_user)
    return {"id": profile.id, **profile.data, "created_at": profile.created_at.isoformat()}


@router.get("/{profile_id}/feedback", response_model=ProfileFeedback)
async def get_profile_feedback(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> dict:
    profile = require_owned_profile(db, profile_id, current_user)
    return {**default_feedback(), **profile.data.get("user_feedback", {})}


@router.patch("/{profile_id}/feedback", response_model=ProfileFeedback)
async def update_profile_feedback(
    profile_id: str,
    feedback: ProfileFeedback,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> dict:
    profile = require_owned_profile(db, profile_id, current_user)
    profile.data["user_feedback"] = feedback.model_dump()
    flag_modified(profile, "data")
    db.commit()
    return feedback.model_dump()


@router.get("")
async def list_profiles(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> list[dict]:
    if current_user is None:
        return []
    profiles = db.scalars(
        select(Profile).where(Profile.user_id == current_user.id).order_by(Profile.created_at.desc())
    ).all()
    return [{"id": item.id, "created_at": item.created_at.isoformat(), "data": item.data} for item in profiles]
