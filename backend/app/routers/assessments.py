from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_optional_user
from app.database import get_db
from app.models.assessment import AssessmentInterpretation, AssessmentResponse, AssessmentSession, CareerMatch
from app.models.profile import Profile
from app.models.user import User
from app.services.profile_authorization import require_owned_profile, require_owned_record
from app.services.assessment_engine import (
    ASSESSMENT_ID,
    DISCLAIMER,
    SCORING_VERSION,
    assessment_prefill_from_profile,
    assessment_definition,
    career_matches_for_profile,
    comparison_public,
    complete_assessment_session,
    create_comparison,
    create_roadmap_draft_from_match,
    delete_assessment_data,
    definition_for_mode,
    match_public,
    response_public,
    results_for_profile,
    session_public,
    set_match_status,
    sync_assessment_definition,
    upsert_responses,
)

router = APIRouter()


class CreateSessionRequest(BaseModel):
    mode: str = Field(default="quick", pattern="^(quick|complete|evidence_based)$")
    consent_accepted: bool


class ResponseInput(BaseModel):
    item_id: str
    module_id: str | None = None
    response_type: str | None = None
    value: Any = None
    excluded_from_recommendations: bool = False
    confirmation_status: str | None = None
    source_type: str | None = None


class ResponseBatch(BaseModel):
    responses: list[ResponseInput] = Field(default_factory=list)


class ResponsePatch(BaseModel):
    value: Any = None
    excluded_from_recommendations: bool | None = None
    confirmation_status: str | None = None


class MatchFeedback(BaseModel):
    feedback_text: str | None = None
    reason_code: str | None = None
    user_priority: int | None = Field(default=None, ge=1, le=5)


class ComparisonRequest(BaseModel):
    match_ids: list[str] = Field(min_length=1, max_length=3)
    criteria_weights: dict[str, float] = Field(default_factory=dict)
    decision_priorities: dict[str, Any] = Field(default_factory=dict)


class ConfirmResultsRequest(BaseModel):
    confirmation_status: str = "confirmed"
    summary: str = ""
    corrections: dict[str, Any] = Field(default_factory=dict)
    reflection_answers: dict[str, Any] = Field(default_factory=dict)


def require_profile(db: Session, profile_id: str, user: User | None) -> Profile:
    return require_owned_profile(db, profile_id, user)


def require_session(db: Session, session_id: str, user: User | None) -> AssessmentSession:
    session = db.get(AssessmentSession, session_id)
    return require_owned_record(session, user, resource_name="Assessment session")


def require_match(db: Session, match_id: str, user: User | None) -> CareerMatch:
    match = db.get(CareerMatch, match_id)
    return require_owned_record(match, user, resource_name="Career match")


@router.get("/assessments")
async def list_assessments(db: Annotated[Session, Depends(get_db)]) -> list[dict[str, Any]]:
    sync_assessment_definition(db)
    definition = assessment_definition()
    return [
        {
            "id": definition["id"],
            "title": definition["title"],
            "version": definition["version"],
            "scoring_version": definition["scoring_version"],
            "modes": definition["modes"],
            "disclaimer": definition["disclaimer"],
            "methodology_note": definition["methodology_note"],
        }
    ]


@router.get("/assessments/{assessment_id}")
async def get_assessment(
    assessment_id: str,
    db: Annotated[Session, Depends(get_db)],
    mode: str | None = None,
) -> dict[str, Any]:
    if assessment_id != ASSESSMENT_ID:
        raise HTTPException(404, "Assessment not found")
    sync_assessment_definition(db)
    return definition_for_mode(mode or "complete")


@router.post("/profiles/{profile_id}/assessment-sessions")
async def create_session(
    profile_id: str,
    payload: CreateSessionRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    if not payload.consent_accepted:
        raise HTTPException(422, "Explicit consent is required before starting the assessment.")
    sync_assessment_definition(db)
    session = AssessmentSession(
        profile_id=profile.id,
        user_id=user.id if user else profile.user_id,
        mode=payload.mode,
        status="in_progress",
        consent_accepted=True,
        scoring_version=SCORING_VERSION,
        source_type="demo" if bool(getattr(profile.user, "is_demo", False)) else "user",
        demo_marker=bool(getattr(profile.user, "is_demo", False)),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"session": session_public(session), "definition": definition_for_mode(payload.mode), "disclaimer": DISCLAIMER, "prefill": assessment_prefill_from_profile(profile)}


@router.get("/profiles/{profile_id}/assessment-sessions/current")
async def current_session(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    session = db.scalar(select(AssessmentSession).where(AssessmentSession.profile_id == profile_id).order_by(AssessmentSession.updated_at.desc()))
    if not session:
        return {"session": None, "definition": definition_for_mode("quick"), "disclaimer": DISCLAIMER, "prefill": assessment_prefill_from_profile(profile)}
    return {"session": session_public(session, include_responses=True, db=db), "definition": definition_for_mode(session.mode), "disclaimer": DISCLAIMER, "prefill": assessment_prefill_from_profile(profile)}


@router.post("/assessment-sessions/{session_id}/responses")
async def save_responses(
    session_id: str,
    payload: ResponseBatch,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    session = require_session(db, session_id, user)
    saved = upsert_responses(db, session, [item.model_dump() for item in payload.responses])
    db.commit()
    return {"status": "saved", "responses": [response_public(item) for item in saved], "session": session_public(session)}


@router.patch("/assessment-responses/{response_id}")
async def patch_response(
    response_id: str,
    payload: ResponsePatch,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    response = db.get(AssessmentResponse, response_id)
    if not response:
        raise HTTPException(404, "Assessment response not found")
    session = require_session(db, response.session_id, user)
    update = ResponseInput(
        item_id=response.item_id,
        module_id=response.module_id,
        response_type=response.response_type,
        value=payload.value if payload.value is not None else response_public(response)["value"],
        excluded_from_recommendations=payload.excluded_from_recommendations if payload.excluded_from_recommendations is not None else response.excluded_from_recommendations,
        confirmation_status=payload.confirmation_status or response.confirmation_status,
    )
    saved = upsert_responses(db, session, [update.model_dump()])
    db.commit()
    return response_public(saved[0])


@router.post("/assessment-sessions/{session_id}/complete")
async def complete_session(
    session_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    session = require_session(db, session_id, user)
    profile = require_profile(db, session.profile_id, user)
    return complete_assessment_session(db, session, profile)


@router.get("/profiles/{profile_id}/assessment-results")
async def get_results(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    require_profile(db, profile_id, user)
    return results_for_profile(db, profile_id)


@router.post("/profiles/{profile_id}/assessment-results/confirm")
async def confirm_results(
    profile_id: str,
    payload: ConfirmResultsRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    session = db.scalar(select(AssessmentSession).where(AssessmentSession.profile_id == profile.id).order_by(AssessmentSession.updated_at.desc()))
    if session:
        session.last_confirmed_at = session.updated_at
    row = AssessmentInterpretation(
        session_id=session.id if session else None,
        profile_id=profile.id,
        user_id=user.id if user else profile.user_id,
        source_type="user_confirmed",
        confirmation_status=payload.confirmation_status,
        summary=payload.summary,
        corrections_json=payload.corrections,
        reflection_answers_json=payload.reflection_answers,
        demo_marker=bool(getattr(profile.user, "is_demo", False)),
    )
    db.add(row)
    db.commit()
    return {"status": "saved", "id": row.id, "confirmation_status": row.confirmation_status}


@router.get("/profiles/{profile_id}/career-matches")
async def get_career_matches(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
    include_rejected: bool = False,
) -> list[dict[str, Any]]:
    require_profile(db, profile_id, user)
    return career_matches_for_profile(db, profile_id, include_rejected=include_rejected)


@router.post("/profiles/{profile_id}/career-comparisons")
async def post_comparison(
    profile_id: str,
    payload: ComparisonRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    row = create_comparison(db, profile, payload.match_ids, payload.criteria_weights, payload.decision_priorities, user.id if user else None)
    return comparison_public(row)


@router.post("/career-matches/{match_id}/save")
async def save_match(
    match_id: str,
    payload: MatchFeedback,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    match = require_match(db, match_id, user)
    if payload.user_priority is not None:
        match.user_priority = payload.user_priority
    return match_public(set_match_status(db, match, "saved", payload.feedback_text))


@router.post("/career-matches/{match_id}/reject")
async def reject_match(
    match_id: str,
    payload: MatchFeedback,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    match = require_match(db, match_id, user)
    feedback = payload.feedback_text or payload.reason_code or "Not for me"
    return match_public(set_match_status(db, match, "rejected", feedback))


@router.post("/career-matches/{match_id}/request-alternative")
async def request_alternative(
    match_id: str,
    payload: MatchFeedback,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    match = require_match(db, match_id, user)
    saved = set_match_status(db, match, "alternative_requested", payload.feedback_text or "User requested alternatives")
    alternatives = [item for item in career_matches_for_profile(db, match.profile_id) if item["id"] != match.id and item["status"] != "rejected"][:3]
    return {"status": "alternative_requested", "career_match": match_public(saved), "alternatives": alternatives}


@router.post("/career-matches/{match_id}/create-roadmap-draft")
async def create_roadmap_draft(
    match_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    match = require_match(db, match_id, user)
    return create_roadmap_draft_from_match(db, match)


@router.delete("/profiles/{profile_id}/assessment-data")
async def delete_profile_assessment_data(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    require_profile(db, profile_id, user)
    return delete_assessment_data(db, profile_id)
