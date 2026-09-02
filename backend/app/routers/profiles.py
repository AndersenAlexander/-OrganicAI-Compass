from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from pydantic import BaseModel, Field

from app.auth.dependencies import get_optional_user
from app.database import get_db
from app.core.time import utc_now_naive
from app.models.diagnostic import Diagnostic
from app.models.profile import Profile
from app.models.assessment import AssessmentSession
from app.models.career_resilience import CareerEvidenceProposal, CareerExperimentSession, CareerHypothesis
from app.models.interview_journey import Interview, InterviewReflection, OfferReview
from app.models.market_application import JobApplication
from app.models.user import User
from app.services.profile_authorization import require_owned_profile
from app.services.interview_journey_engine import interview_dashboard

router = APIRouter()


class ProfileFeedback(BaseModel):
    confirmed_nodes: list[str] = Field(default_factory=list)
    hidden_recommendations: list[str] = Field(default_factory=list)
    strength_adjustments: dict[str, int] = Field(default_factory=dict)
    archetype_override: str | None = None
    user_notes: dict[str, str] = Field(default_factory=dict)
    interpretation_status: Literal["needs_confirmation", "confirmed", "needs_review"] = "needs_confirmation"


def default_feedback() -> dict:
    return ProfileFeedback().model_dump()


@router.get("/{profile_id}")
async def get_profile(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> dict:
    profile = require_owned_profile(db, profile_id, current_user)
    return {
        "id": profile.id,
        "diagnostic_id": profile.diagnostic_id,
        **profile.data,
        "created_at": profile.created_at.isoformat(),
    }


@router.get("/{profile_id}/feedback", response_model=ProfileFeedback)
async def get_profile_feedback(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> dict:
    profile = require_owned_profile(db, profile_id, current_user)
    diagnostic = db.get(Diagnostic, profile.diagnostic_id) if profile.diagnostic_id else None
    return {**default_feedback(), **profile.data.get("user_feedback", {})}


@router.get("/{profile_id}/journey-state")
async def get_profile_journey_state(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> dict:
    """Return persisted workflow markers without generating or changing any records."""
    profile = require_owned_profile(db, profile_id, current_user)
    diagnostic = db.get(Diagnostic, profile.diagnostic_id) if profile.diagnostic_id else None
    assessment = db.scalar(
        select(AssessmentSession)
        .where(AssessmentSession.profile_id == profile.id)
        .order_by(AssessmentSession.updated_at.desc(), AssessmentSession.created_at.desc())
    )
    hypotheses = db.scalars(
        select(CareerHypothesis)
        .where(CareerHypothesis.profile_id == profile.id)
        .order_by(CareerHypothesis.updated_at.desc())
    ).all()
    experiments = db.scalars(
        select(CareerExperimentSession)
        .where(CareerExperimentSession.profile_id == profile.id)
        .order_by(CareerExperimentSession.updated_at.desc())
    ).all()
    proposals = db.scalars(
        select(CareerEvidenceProposal)
        .where(CareerEvidenceProposal.profile_id == profile.id)
        .order_by(CareerEvidenceProposal.updated_at.desc())
    ).all()
    applications = db.scalars(select(JobApplication).where(JobApplication.profile_id == profile.id)).all()
    interviews = db.scalars(select(Interview).where(Interview.profile_id == profile.id)).all()
    offer_review_count = db.scalar(select(func.count()).select_from(OfferReview).where(OfferReview.profile_id == profile.id)) or 0
    latest_interview = max(interviews, key=lambda row: (row.updated_at, row.created_at), default=None)
    interview_state = interview_dashboard(db, profile) if latest_interview else None
    return {
        "profile_id": profile.id,
        "diagnostic_id": profile.diagnostic_id,
        "diagnostic_status": diagnostic.status if diagnostic else "not_started",
        "diagnostic_version": diagnostic.diagnostic_version if diagnostic else None,
        "assessment_status": assessment.status if assessment else "not_started",
        "deep_dive_status": assessment.status if assessment else "not_started",
        "hypothesis_decision_states": [row.user_decision_state for row in hypotheses],
        "experiment_statuses": [row.status for row in experiments],
        "has_pending_evidence_review": any(row.status == "PENDING_REVIEW" for row in proposals),
        "has_market_activity": bool(applications),
        "has_application_activity": bool(applications),
        "has_interview_activity": bool(interviews),
        "employment_summary": {
            "application_count": len(applications),
            "interview_count": len(interviews),
            "completed_interview_count": sum(row.status == "COMPLETED" for row in interviews),
            "offer_review_count": offer_review_count,
            "roadmap_mutated": False,
        },
        "interview_summary": {
            "id": latest_interview.id,
            "lifecycle_status": latest_interview.status,
            "stage_type": latest_interview.stage_type,
            "preparation_status": latest_interview.preparation_status,
            "has_reflection": bool(
                db.scalar(select(InterviewReflection.id).where(InterviewReflection.interview_id == latest_interview.id))
            ),
            "outcome": latest_interview.interview_result,
            "next_action": interview_state["next_recommended_action"] if interview_state else "Create an Interview Journey record.",
        } if latest_interview and interview_state else None,
    }


@router.patch("/{profile_id}/feedback", response_model=ProfileFeedback)
async def update_profile_feedback(
    profile_id: str,
    feedback: ProfileFeedback,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> dict:
    profile = require_owned_profile(db, profile_id, current_user)
    next_feedback = feedback.model_dump()
    existing_history = profile.data.get("interpretation_feedback_history") if isinstance(profile.data.get("interpretation_feedback_history"), list) else []
    next_version = len(existing_history) + 1
    profile.data["user_feedback"] = next_feedback
    profile.data["interpretation_feedback_history"] = [
        *existing_history,
        {"version": next_version, "updated_at": utc_now_naive().isoformat(), "feedback": next_feedback},
    ]
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
    return [
        {
            "id": item.id,
            "diagnostic_id": item.diagnostic_id,
            "created_at": item.created_at.isoformat(),
            "data": item.data,
        }
        for item in profiles
    ]
