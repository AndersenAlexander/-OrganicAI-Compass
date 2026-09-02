from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_optional_user
from app.database import get_db
from app.core.time import utc_now_naive
from app.models.diagnostic import Diagnostic, DiagnosticResponse
from app.models.profile import Profile
from app.schemas.diagnostic_schema import (
    DiagnosticCreate,
    DiagnosticCreated,
    DiagnosticDraftRequest,
    DiagnosticDraftResponse,
)
from app.services.profile_generation import generate_profile
from app.models.user import User

router = APIRouter()


def response_public(row: DiagnosticResponse) -> dict[str, Any]:
    return {
        "id": row.id,
        "diagnostic_id": row.diagnostic_id,
        "question_id": row.question_id,
        "assessment_domain": row.assessment_domain,
        "question_type": row.question_type,
        "response": row.response_json,
        "normalized_value": row.normalized_value,
        "confidence": row.confidence,
        "source": row.source,
        "version": row.version,
        "interpretation": row.interpretation,
        "completeness": row.completeness,
        "scoring_metadata": row.scoring_metadata,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def draft_public(db: Session, diagnostic: Diagnostic) -> DiagnosticDraftResponse:
    responses = db.scalars(
        select(DiagnosticResponse)
        .where(DiagnosticResponse.diagnostic_id == diagnostic.id)
        .order_by(DiagnosticResponse.created_at)
    ).all()
    return DiagnosticDraftResponse(
        diagnostic_id=diagnostic.id,
        status=diagnostic.status,
        current_step=diagnostic.current_step,
        updated_at=(diagnostic.updated_at or diagnostic.created_at).isoformat(),
        payload=diagnostic.payload,
        responses=[response_public(row) for row in responses],
    )


def owned_diagnostic(db: Session, diagnostic_id: str, current_user: User | None) -> Diagnostic:
    diagnostic = db.get(Diagnostic, diagnostic_id)
    if not diagnostic or current_user is None or diagnostic.user_id != current_user.id:
        raise HTTPException(404, "Diagnostic not found")
    return diagnostic


def upsert_diagnostic_responses(db: Session, diagnostic: Diagnostic, payload: DiagnosticDraftRequest, user_id: str | None) -> None:
    existing = {
        row.question_id: row
        for row in db.scalars(select(DiagnosticResponse).where(DiagnosticResponse.diagnostic_id == diagnostic.id)).all()
    }
    for item in payload.responses:
        row = existing.get(item.question_id)
        if row is None:
            row = DiagnosticResponse(diagnostic_id=diagnostic.id, user_id=user_id, question_id=item.question_id, assessment_domain=item.assessment_domain, question_type=item.question_type)
            db.add(row)
        row.assessment_domain = item.assessment_domain
        row.question_type = item.question_type
        row.response_json = item.response
        row.normalized_value = item.normalized_value
        row.confidence = item.confidence
        row.source = item.source
        row.version = item.version
        row.interpretation = item.interpretation
        row.completeness = item.completeness
        row.scoring_metadata = item.scoring_metadata
        row.updated_at = utc_now_naive()


@router.post("", response_model=DiagnosticCreated)
async def create_diagnostic(
    payload: DiagnosticCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> DiagnosticCreated:
    diagnostic = Diagnostic(user_id=current_user.id if current_user else None, payload=payload.model_dump(), status="completed", current_step=4, completed_at=utc_now_naive())
    db.add(diagnostic)
    db.flush()
    profile_data = await generate_profile(diagnostic.id, payload.model_dump())
    profile_data["interpretation_version"] = 1
    profile_data["interpretation_history"] = [{"version": 1, "source": "human_diagnostic", "status": "generated", "created_at": utc_now_naive().isoformat()}]
    profile = Profile(
        user_id=current_user.id if current_user else None,
        diagnostic_id=diagnostic.id,
        data=profile_data,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return DiagnosticCreated(diagnostic_id=diagnostic.id, profile_id=profile.id)


@router.post("/draft", response_model=DiagnosticDraftResponse)
async def save_diagnostic_draft(
    payload: DiagnosticDraftRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> DiagnosticDraftResponse:
    if current_user is None:
        raise HTTPException(401, "Sign in to save diagnostic progress.")
    diagnostic = owned_diagnostic(db, payload.diagnostic_id, current_user) if payload.diagnostic_id else None
    if diagnostic is None:
        diagnostic = Diagnostic(user_id=current_user.id, payload=payload.payload, current_step=payload.current_step, diagnostic_version=payload.diagnostic_version)
        db.add(diagnostic)
        db.flush()
    else:
        diagnostic.payload = payload.payload
        diagnostic.current_step = payload.current_step
        diagnostic.diagnostic_version = payload.diagnostic_version
        diagnostic.status = "in_progress"
        diagnostic.updated_at = utc_now_naive()
    upsert_diagnostic_responses(db, diagnostic, payload, current_user.id)
    db.commit()
    db.refresh(diagnostic)
    return draft_public(db, diagnostic)


@router.get("/current", response_model=DiagnosticDraftResponse | None)
async def current_diagnostic_draft(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> DiagnosticDraftResponse | None:
    if current_user is None:
        return None
    diagnostic = db.scalar(
        select(Diagnostic)
        .where(Diagnostic.user_id == current_user.id, Diagnostic.status == "in_progress")
        .order_by(Diagnostic.updated_at.desc(), Diagnostic.created_at.desc())
    )
    return draft_public(db, diagnostic) if diagnostic else None


@router.post("/{diagnostic_id}/complete", response_model=DiagnosticCreated)
async def complete_diagnostic(
    diagnostic_id: str,
    payload: DiagnosticCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> DiagnosticCreated:
    diagnostic = owned_diagnostic(db, diagnostic_id, current_user)
    diagnostic.payload = payload.model_dump()
    diagnostic.status = "completed"
    diagnostic.current_step = 4
    diagnostic.completed_at = utc_now_naive()
    diagnostic.updated_at = utc_now_naive()
    profile = db.scalar(select(Profile).where(Profile.diagnostic_id == diagnostic.id))
    profile_data = await generate_profile(diagnostic.id, payload.model_dump())
    if profile is None:
        profile_data["interpretation_version"] = 1
        profile_data["interpretation_history"] = [{"version": 1, "source": "human_diagnostic", "status": "generated", "created_at": utc_now_naive().isoformat()}]
        profile = Profile(user_id=diagnostic.user_id, diagnostic_id=diagnostic.id, data=profile_data)
        db.add(profile)
    else:
        previous = profile.data or {}
        previous_version = int(previous.get("interpretation_version") or 1)
        history = previous.get("interpretation_history") if isinstance(previous.get("interpretation_history"), list) else []
        profile_data["interpretation_version"] = previous_version + 1
        profile_data["interpretation_history"] = [
            *history,
            {
                "version": previous_version,
                "source": "human_diagnostic",
                "status": "superseded",
                "created_at": utc_now_naive().isoformat(),
                "diagnostic_id": previous.get("diagnostic_id"),
                "quick_diagnostic": previous.get("quick_diagnostic"),
                "human_potential_map": previous.get("human_potential_map"),
            },
        ]
        for key in ("user_feedback", "interpretation_feedback_history"):
            if key in previous:
                profile_data[key] = previous[key]
        profile.data = profile_data
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
    return [
        {
            "id": item.id,
            "created_at": item.created_at.isoformat(),
            "updated_at": (item.updated_at or item.created_at).isoformat(),
            "status": item.status,
            "current_step": item.current_step,
            "version": item.diagnostic_version,
            "payload": item.payload,
        }
        for item in diagnostics
    ]
