from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_optional_user
from app.database import get_db
from app.models.fear_transform import FearTransformRecord
from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.models.user import User
from app.services.roadmap_adaptation import roadmap_public
from app.services.profile_generation import transform_fear as generate_fear_transform

router = APIRouter()


class FearTransformRequest(BaseModel):
    profile_id: str
    fear: str = Field(min_length=2)


def require_profile(db: Session, profile_id: str, current_user: User | None) -> Profile:
    profile = db.get(Profile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    if current_user and profile.user_id and profile.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Profile does not belong to the current user")
    return profile


def fear_public(item: FearTransformRecord) -> dict:
    return {
        "id": item.id,
        "profile_id": item.profile_id,
        "input_fear": item.input_fear,
        "output": item.output,
        "created_at": item.created_at.isoformat(),
    }


@router.post("/fear-transform")
async def transform_fear(
    payload: FearTransformRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> dict:
    require_profile(db, payload.profile_id, current_user)
    item = FearTransformRecord(
        profile_id=payload.profile_id,
        input_fear=payload.fear,
        output=await generate_fear_transform(payload.fear, require_profile(db, payload.profile_id, current_user).data),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return fear_public(item)


@router.get("/report/{profile_id}")
async def get_report(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> dict:
    profile = require_profile(db, profile_id, current_user)
    fears = db.scalars(
        select(FearTransformRecord)
        .where(FearTransformRecord.profile_id == profile_id)
        .order_by(FearTransformRecord.created_at.asc())
    ).all()
    roadmap = db.scalar(
        select(Roadmap).where(Roadmap.profile_id == profile_id).order_by(Roadmap.created_at.desc())
    )
    result = {
        "profile": {"id": profile.id, **profile.data, "created_at": profile.created_at.isoformat()},
        "fear_transforms": [fear_public(item) for item in fears],
        "roadmap": (roadmap_public(db, roadmap) if roadmap else None),
    }
    db.commit()
    return result
