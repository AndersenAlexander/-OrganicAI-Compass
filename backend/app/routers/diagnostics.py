from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_optional_user
from app.database import get_db
from app.models.diagnostic import Diagnostic
from app.models.profile import Profile
from app.schemas.diagnostic_schema import DiagnosticCreate, DiagnosticCreated
from app.services.profile_generation import generate_profile
from app.models.user import User

router = APIRouter()


@router.post("", response_model=DiagnosticCreated)
async def create_diagnostic(
    payload: DiagnosticCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> DiagnosticCreated:
    diagnostic = Diagnostic(user_id=current_user.id if current_user else None, payload=payload.model_dump())
    db.add(diagnostic)
    db.flush()
    profile_data = await generate_profile(diagnostic.id, payload.model_dump())
    profile = Profile(
        user_id=current_user.id if current_user else None,
        diagnostic_id=diagnostic.id,
        data=profile_data,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return DiagnosticCreated(diagnostic_id=diagnostic.id, profile_id=profile.id)


@router.get("")
async def list_diagnostics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> list[dict]:
    if current_user is None:
        return []
    diagnostics = db.scalars(
        select(Diagnostic).where(Diagnostic.user_id == current_user.id).order_by(Diagnostic.created_at.desc())
    ).all()
    return [{"id": item.id, "created_at": item.created_at.isoformat(), "payload": item.payload} for item in diagnostics]
