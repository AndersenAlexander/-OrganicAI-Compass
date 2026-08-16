from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_optional_user
from app.database import get_db
from app.models.assessment import SkillEvidence, SkillsInventory
from app.models.career_resilience import CareerExperimentSession
from app.models.profile import Profile
from app.models.user import User
from app.services.profile_authorization import assert_profile_access, require_owned_profile, require_owned_record
from app.services.career_resilience_engine import (
    add_manual_evidence,
    career_resilience_dashboard,
    create_experiment_session,
    create_immediate_action_plan,
    create_supported_paths,
    delete_evidence,
    evaluate_experiment,
    evidence_passport,
    generate_support_brief,
    get_experiment_template,
    get_support_programme,
    latest_immediate_action_plan,
    latest_job_loss_profile,
    latest_recalibration,
    latest_support_brief,
    latest_support_screening,
    latest_supported_paths,
    list_experiment_templates,
    list_profile_experiment_sessions,
    list_support_programmes,
    recalibrate_career_recommendations,
    run_support_screening,
    self_review_experiment,
    session_public,
    start_experiment,
    submit_experiment,
    update_evidence,
    upsert_job_loss_profile,
)

router = APIRouter()


class ExperimentSessionRequest(BaseModel):
    experiment_template_id: str | None = None
    template_id: str | None = None
    career_match_id: str | None = None
    mode: str = "guided"
    user_confirmed: bool = True
    add_to_roadmap: bool = False


class ExperimentSubmissionRequest(BaseModel):
    text_response: str = ""
    project_url: str | None = None
    repository_url: str | None = None
    portfolio_url: str | None = None
    document_metadata: dict[str, Any] = Field(default_factory=dict)
    file_references: list[dict[str, Any]] = Field(default_factory=list)
    completion_notes: str = ""
    time_spent_minutes: int | None = Field(default=None, ge=0)
    ai_tools_used: list[str] = Field(default_factory=list)
    assistance_level: str = "not_specified"
    self_rated_difficulty: int | None = Field(default=None, ge=1, le=5)
    self_rated_enjoyment: int | None = Field(default=None, ge=1, le=5)
    confidence_before: int | None = Field(default=None, ge=1, le=5)
    confidence_after: int | None = Field(default=None, ge=1, le=5)
    reflection: dict[str, Any] = Field(default_factory=dict)


class SelfReviewRequest(BaseModel):
    reflection: str = ""
    self_rated_difficulty: int | None = Field(default=None, ge=1, le=5)
    self_rated_enjoyment: int | None = Field(default=None, ge=1, le=5)
    confidence_before: int | None = Field(default=None, ge=1, le=5)
    confidence_after: int | None = Field(default=None, ge=1, le=5)


class EvidenceRequest(BaseModel):
    skill_id: str
    evidence_type: str = "user_confirmed_external_evidence"
    title: str = "Manual skill evidence"
    description: str = ""
    url: str | None = None
    source_id: str | None = None
    score_hint: float = 55


class EvidencePatch(BaseModel):
    title: str | None = None
    description: str | None = None
    url: str | None = None
    verification_status: str | None = None


class RecalibrationRequest(BaseModel):
    experiment_result_id: str | None = None


class JobLossProfileRequest(BaseModel):
    consent_accepted: bool
    country_of_residence: str = ""
    country_of_employment: str = ""
    municipality_or_region: str = ""
    last_working_date: str | None = None
    contract_termination_type: str = ""
    employment_status: str = ""
    reduction_in_working_hours: int | None = Field(default=None, ge=0, le=100)
    jobseeker_registration_status: str = ""
    current_benefits: list[str] = Field(default_factory=list)
    work_permit_or_residency_status: str = ""
    education: str = ""
    training_interest: str = ""
    availability_for_work: str = ""
    relocation_preferences: str = ""


class SupportScreeningRequest(BaseModel):
    country: str | None = None
    values: dict[str, Any] = Field(default_factory=dict)


def _handle(error: Exception) -> None:
    if isinstance(error, LookupError):
        raise HTTPException(404, str(error))
    if isinstance(error, ValueError):
        raise HTTPException(422, str(error))
    raise error


def require_profile(db: Session, profile_id: str, user: User | None) -> Profile:
    return require_owned_profile(db, profile_id, user)


def require_session(db: Session, session_id: str, user: User | None) -> CareerExperimentSession:
    row = db.get(CareerExperimentSession, session_id)
    return require_owned_record(row, user, resource_name="Career experiment session")


def require_evidence(db: Session, evidence_id: str, user: User | None) -> SkillEvidence:
    row = db.get(SkillEvidence, evidence_id)
    if not row:
        raise HTTPException(404, "Evidence not found")
    inventory = db.get(SkillsInventory, row.skill_inventory_id)
    if not inventory:
        raise HTTPException(404, "Evidence inventory not found")
    profile = db.get(Profile, inventory.profile_id)
    if not profile:
        raise HTTPException(404, "Evidence profile not found")
    assert_profile_access(profile, user)
    return row


@router.get("/career-experiments")
async def career_experiments(
    db: Annotated[Session, Depends(get_db)],
    role_family: str | None = None,
) -> list[dict[str, Any]]:
    return list_experiment_templates(db, role_family)


@router.get("/career-experiments/{experiment_id}")
async def career_experiment(experiment_id: str, db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    try:
        return get_experiment_template(db, experiment_id)
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/career-resilience")
async def career_resilience(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    return career_resilience_dashboard(db, profile)


@router.post("/profiles/{profile_id}/career-experiments")
async def create_profile_experiment(
    profile_id: str,
    payload: ExperimentSessionRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return create_experiment_session(db, profile, payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/career-experiments")
async def get_profile_experiments(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> list[dict[str, Any]]:
    require_profile(db, profile_id, user)
    return list_profile_experiment_sessions(db, profile_id)


@router.post("/career-experiment-sessions/{session_id}/start")
async def start_profile_experiment(
    session_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    session = require_session(db, session_id, user)
    try:
        return start_experiment(db, session)
    except Exception as error:
        _handle(error)
        raise


@router.post("/career-experiment-sessions/{session_id}/submit")
async def submit_profile_experiment(
    session_id: str,
    payload: ExperimentSubmissionRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    session = require_session(db, session_id, user)
    try:
        return submit_experiment(db, session, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.post("/career-experiment-sessions/{session_id}/self-review")
async def self_review_profile_experiment(
    session_id: str,
    payload: SelfReviewRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    session = require_session(db, session_id, user)
    try:
        return self_review_experiment(db, session, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.post("/career-experiment-sessions/{session_id}/evaluate")
async def evaluate_profile_experiment(
    session_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    session = require_session(db, session_id, user)
    try:
        return evaluate_experiment(db, session)
    except Exception as error:
        _handle(error)
        raise


@router.get("/career-experiment-sessions/{session_id}")
async def get_profile_experiment_session(
    session_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    session = require_session(db, session_id, user)
    return session_public(db, session)


@router.get("/profiles/{profile_id}/evidence-passport")
async def get_evidence_passport(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    require_profile(db, profile_id, user)
    return evidence_passport(db, profile_id)


@router.post("/profiles/{profile_id}/evidence")
async def post_evidence(
    profile_id: str,
    payload: EvidenceRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return add_manual_evidence(db, profile, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.put("/evidence/{evidence_id}")
async def put_evidence(
    evidence_id: str,
    payload: EvidencePatch,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    evidence = require_evidence(db, evidence_id, user)
    try:
        return update_evidence(db, evidence, payload.model_dump(exclude_none=True))
    except Exception as error:
        _handle(error)
        raise


@router.delete("/evidence/{evidence_id}")
async def remove_evidence(
    evidence_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    evidence = require_evidence(db, evidence_id, user)
    return delete_evidence(db, evidence)


@router.post("/profiles/{profile_id}/career-recalibration")
async def post_recalibration(
    profile_id: str,
    payload: RecalibrationRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    return recalibrate_career_recommendations(db, profile, payload.experiment_result_id)


@router.get("/profiles/{profile_id}/career-recalibration/latest")
async def get_latest_recalibration(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any] | None:
    require_profile(db, profile_id, user)
    return latest_recalibration(db, profile_id)


@router.post("/profiles/{profile_id}/supported-paths")
async def post_supported_paths(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    return create_supported_paths(db, profile, {})


@router.get("/profiles/{profile_id}/supported-paths")
async def get_supported_paths(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    require_profile(db, profile_id, user)
    return latest_supported_paths(db, profile_id)


@router.get("/support/programmes")
async def support_programmes(db: Annotated[Session, Depends(get_db)]) -> list[dict[str, Any]]:
    return list_support_programmes(db)


@router.get("/support/programmes/{programme_id}")
async def support_programme(programme_id: str, db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    try:
        return get_support_programme(db, programme_id)
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/job-loss-profile")
async def post_job_loss_profile(
    profile_id: str,
    payload: JobLossProfileRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return upsert_job_loss_profile(db, profile, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/job-loss-profile")
async def get_job_loss_profile(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any] | None:
    require_profile(db, profile_id, user)
    return latest_job_loss_profile(db, profile_id)


@router.post("/profiles/{profile_id}/support-screening")
async def post_support_screening(
    profile_id: str,
    payload: SupportScreeningRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    values = {**payload.values}
    if payload.country:
        values["country"] = payload.country
    return run_support_screening(db, profile, values)


@router.get("/profiles/{profile_id}/support-screening")
async def get_support_screening(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any] | None:
    require_profile(db, profile_id, user)
    return latest_support_screening(db, profile_id)


@router.post("/profiles/{profile_id}/immediate-action-plan")
async def post_immediate_action_plan(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return create_immediate_action_plan(db, profile)
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/immediate-action-plan")
async def get_immediate_action_plan(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any] | None:
    require_profile(db, profile_id, user)
    return latest_immediate_action_plan(db, profile_id)


@router.post("/profiles/{profile_id}/support-brief")
async def post_support_brief(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    return generate_support_brief(db, profile)


@router.get("/profiles/{profile_id}/support-brief")
async def get_support_brief(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any] | None:
    require_profile(db, profile_id, user)
    return latest_support_brief(db, profile_id)
