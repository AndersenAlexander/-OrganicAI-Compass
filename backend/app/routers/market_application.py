from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_optional_user, require_admin_user
from app.database import get_db
from app.models.market_application import JobPosting, JobRequirement
from app.models.profile import Profile
from app.models.user import User
from app.services.profile_authorization import require_owned_profile
from app.services.research_readiness import assert_research_ready
from app.services.market_application_engine import (
    add_application_event,
    add_application_stage,
    add_document_claim,
    application_public,
    calculate_document_readiness,
    calculate_job_readiness,
    confirm_job_analysis,
    confirm_document_claim,
    consent_to_research,
    create_application,
    create_application_document,
    create_document_version,
    create_job_analysis,
    create_research_export,
    create_research_session,
    ensure_master_career_profile,
    ensure_research_study,
    esco_status,
    export_document,
    document_public,
    get_document,
    get_job,
    get_research_export,
    job_analysis_public,
    link_claim_evidence,
    list_application_documents,
    list_applications,
    list_job_analyses,
    list_jobs,
    list_research_studies,
    market_radar,
    match_analysis_evidence,
    normalise_skill_terms,
    providers_status,
    recalibrate_from_application,
    record_application_outcome,
    record_research_metrics,
    record_research_responses,
    require_analysis,
    require_application,
    require_claim,
    require_research_session,
    require_study,
    research_consent_template,
    save_job_for_profile,
    study_summary,
    sync_demo_labour_market,
    update_application,
    update_document_claim,
    update_requirement,
    upsert_market_preferences,
    withdraw_research_consent,
)

router = APIRouter()


class DictRequest(BaseModel):
    model_config = {"extra": "allow"}


class MarketPreferenceRequest(DictRequest):
    country: str = "Norway"
    county: str = ""
    municipality: str = ""
    commuting_area: str = ""
    radius_km: int | None = Field(default=None, ge=1, le=250)
    work_modes: list[str] = Field(default_factory=list)
    preferred_languages: list[str] = Field(default_factory=list)
    employment_types: list[str] = Field(default_factory=list)
    full_time_part_time: list[str] = Field(default_factory=list)
    career_families: list[str] = Field(default_factory=list)
    selected_hypothesis_id: str | None = None
    minimum_publication_date: str | None = None
    experience_level: str = ""
    role_title: str = ""
    excluded_employers: list[str] = Field(default_factory=list)
    excluded_keywords: list[str] = Field(default_factory=list)
    relocation_preference: str = ""
    user_confirmed_storage: bool = False


class JobAnalysisRequest(DictRequest):
    job_id: str | None = None
    input_type: str = "pasted_text"
    pasted_text: str = ""
    source_url: str | None = None
    title: str = ""
    organisation: str = ""
    location: str = ""
    deadline: str | None = None
    capture_id: str | None = None
    user_confirmed: bool = False


class RequirementPatchRequest(DictRequest):
    requirement_text: str | None = None
    requirement_category: str | None = None
    requirement_type: str | None = None
    user_confirmation_state: str | None = None
    status: str | None = None
    action: str | None = None
    normalised_skill_id: str | None = None
    change_reason: str = "User corrected requirement extraction."


class ApplicationDocumentRequest(DictRequest):
    job_analysis_id: str | None = None
    document_type: str = "cv"
    title: str | None = None
    language: str = "en"
    variant: str = "concise"


class ClaimRequest(DictRequest):
    section_id: str | None = None
    claim_text: str
    claim_type: str = "manual"
    evidence_id: str | None = None


class ClaimPatchRequest(DictRequest):
    claim_text: str | None = None
    status: str | None = None
    safer_alternative: str | None = None
    user_confirmation_state: str | None = None


class EvidenceLinkRequest(DictRequest):
    evidence_id: str
    relationship: str = "supports"


class ApplicationRequest(DictRequest):
    job_id: str | None = None
    job_analysis_id: str | None = None
    career_match_id: str | None = None
    cv_document_id: str | None = None
    cover_letter_document_id: str | None = None
    title: str | None = None
    organisation: str | None = None
    source: str | None = None
    application_date: str | None = None
    deadline: str | None = None
    status: str = "Preparing"
    contacts: list[dict[str, Any]] = Field(default_factory=list)
    notes: str = ""
    next_action: str | None = None


class ApplicationPatchRequest(DictRequest):
    status: str | None = None
    notes: str | None = None
    next_action: str | None = None
    application_date: str | None = None
    description: str | None = None
    contacts: list[dict[str, Any]] | None = None


class ResearchConsentRequest(DictRequest):
    consent_given: bool
    consent_scope: list[str] = Field(default_factory=list)


class ResearchSessionRequest(DictRequest):
    workflow_stage: str = "pre_test"
    workflow: str = "control"


class ResearchResponsesRequest(DictRequest):
    responses: list[dict[str, Any]] = Field(default_factory=list)
    complete_session: bool = False


class ResearchMetricsRequest(DictRequest):
    metrics: list[dict[str, Any]] = Field(default_factory=list)


def _handle(error: Exception) -> None:
    if isinstance(error, LookupError):
        raise HTTPException(404, str(error))
    if isinstance(error, PermissionError):
        raise HTTPException(403, str(error))
    if isinstance(error, ValueError):
        raise HTTPException(422, str(error))
    raise error


def require_profile(db: Session, profile_id: str, user: User | None) -> Profile:
    return require_owned_profile(db, profile_id, user)


def _check_profile_access(db: Session, profile_id: str, user: User | None) -> Profile:
    return require_profile(db, profile_id, user)


def _filters(
    provider: str | None = None,
    query: str | None = None,
    country: str | None = None,
    municipality: str | None = None,
    work_mode: str | None = None,
    career_family: str | None = None,
    language: str | None = None,
    role_title: str | None = None,
    seniority: str | None = None,
    selected_hypothesis_id: str | None = None,
    demo_mode: bool = False,
    active_only: bool = True,
    limit: int = 30,
) -> dict[str, Any]:
    return {
        "provider": provider,
        "query": query,
        "country": country,
        "municipality": municipality,
        "work_mode": work_mode,
        "career_family": career_family,
        "language": language,
        "role_title": role_title,
        "seniority": seniority,
        "selected_hypothesis_id": selected_hypothesis_id,
        "demo_mode": demo_mode,
        "active_only": active_only,
        "limit": min(max(limit, 1), 100),
    }


@router.get("/market/providers/status")
async def get_market_provider_status(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    return providers_status(db)


@router.post("/market/providers/demo/sync")
async def sync_demo_market(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin_user)],
) -> dict[str, Any]:
    return sync_demo_labour_market(db)


@router.get("/market/esco/status")
async def get_esco_status(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    return esco_status(db)


@router.post("/market/esco/normalise")
async def normalise_market_terms(
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin_user)],
) -> dict[str, Any]:
    phrases = payload.model_dump().get("phrases") or []
    return normalise_skill_terms(db, phrases)


@router.get("/profiles/{profile_id}/market-radar")
async def get_market_radar(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
    provider: str | None = None,
    query: str | None = None,
    country: str | None = None,
    municipality: str | None = None,
    work_mode: str | None = None,
    career_family: str | None = None,
    language: str | None = None,
    role_title: str | None = None,
    seniority: str | None = None,
    selected_hypothesis_id: str | None = None,
    demo_mode: bool = False,
    active_only: bool = True,
    limit: int = Query(30, ge=1, le=100),
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    return market_radar(db, profile, _filters(provider, query, country, municipality, work_mode, career_family, language, role_title, seniority, selected_hypothesis_id, demo_mode, active_only, limit))


@router.put("/profiles/{profile_id}/market-preferences")
async def put_market_preferences(
    profile_id: str,
    payload: MarketPreferenceRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return upsert_market_preferences(db, profile, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/jobs")
async def get_market_jobs(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
    provider: str | None = None,
    query: str | None = None,
    country: str | None = None,
    municipality: str | None = None,
    work_mode: str | None = None,
    career_family: str | None = None,
    language: str | None = None,
    role_title: str | None = None,
    seniority: str | None = None,
    selected_hypothesis_id: str | None = None,
    demo_mode: bool = False,
    active_only: bool = True,
    limit: int = Query(30, ge=1, le=100),
) -> list[dict[str, Any]]:
    profile = require_profile(db, profile_id, user)
    return list_jobs(db, profile, _filters(provider, query, country, municipality, work_mode, career_family, language, role_title, seniority, selected_hypothesis_id, demo_mode, active_only, limit))


@router.get("/profiles/{profile_id}/jobs/{job_id}")
async def get_profile_job(
    profile_id: str,
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return get_job(db, job_id, profile)
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/jobs/{job_id}/save")
async def save_profile_job(
    profile_id: str,
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        job_payload = get_job(db, job_id, profile)
        job_row = db.get(JobPosting, job_payload["id"])
        return save_job_for_profile(db, profile, job_row)
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/job-analyses")
async def get_job_analyses(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> list[dict[str, Any]]:
    require_profile(db, profile_id, user)
    return list_job_analyses(db, profile_id)


@router.post("/profiles/{profile_id}/job-analyses")
async def post_job_analysis(
    profile_id: str,
    payload: JobAnalysisRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return create_job_analysis(db, profile, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/job-analyses/{analysis_id}")
async def get_job_analysis(
    profile_id: str,
    analysis_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return job_analysis_public(db, require_analysis(db, analysis_id, profile))
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/job-analyses/{analysis_id}/match")
async def match_job_analysis(
    profile_id: str,
    analysis_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return match_analysis_evidence(db, require_analysis(db, analysis_id, profile))
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/job-analyses/{analysis_id}/confirm")
async def confirm_job_analysis_route(
    profile_id: str,
    analysis_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return confirm_job_analysis(db, require_analysis(db, analysis_id, profile), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/job-analyses/{analysis_id}/readiness")
async def calculate_analysis_readiness(
    profile_id: str,
    analysis_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return calculate_job_readiness(db, require_analysis(db, analysis_id, profile))
    except Exception as error:
        _handle(error)
        raise


@router.patch("/profiles/{profile_id}/job-requirements/{requirement_id}")
async def patch_job_requirement(
    profile_id: str,
    requirement_id: str,
    payload: RequirementPatchRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    requirement = db.get(JobRequirement, requirement_id)
    if not requirement or requirement.profile_id != profile.id:
        raise HTTPException(404, "Job requirement not found")
    try:
        return update_requirement(db, requirement, payload.model_dump(exclude_none=True), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/master-career-profile")
async def get_master_career_profile(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    return ensure_master_career_profile(db, profile)


@router.get("/profiles/{profile_id}/application-documents")
async def get_application_documents(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> list[dict[str, Any]]:
    require_profile(db, profile_id, user)
    return list_application_documents(db, profile_id)


@router.post("/profiles/{profile_id}/application-documents")
async def post_application_document(
    profile_id: str,
    payload: ApplicationDocumentRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return create_application_document(db, profile, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/application-documents/{document_id}")
async def get_application_document(
    profile_id: str,
    document_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return document_public(db, get_document(db, document_id, profile))
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/application-documents/{document_id}/versions")
async def post_document_version(
    profile_id: str,
    document_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return create_document_version(db, get_document(db, document_id, profile), payload.model_dump().get("reason") or "Manual version save.")
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/application-documents/{document_id}/claims")
async def post_document_claim(
    profile_id: str,
    document_id: str,
    payload: ClaimRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return add_document_claim(db, get_document(db, document_id, profile), payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.patch("/profiles/{profile_id}/document-claims/{claim_id}")
async def patch_document_claim(
    profile_id: str,
    claim_id: str,
    payload: ClaimPatchRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return update_document_claim(db, require_claim(db, claim_id, profile), payload.model_dump(exclude_none=True))
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/document-claims/{claim_id}/confirm")
async def confirm_claim(
    profile_id: str,
    claim_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return confirm_document_claim(db, require_claim(db, claim_id, profile))
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/document-claims/{claim_id}/evidence")
async def post_claim_evidence(
    profile_id: str,
    claim_id: str,
    payload: EvidenceLinkRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return link_claim_evidence(db, require_claim(db, claim_id, profile), payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/application-documents/{document_id}/readiness")
async def post_document_readiness(
    profile_id: str,
    document_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return calculate_document_readiness(db, get_document(db, document_id, profile))
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/application-documents/{document_id}/export")
async def post_document_export(
    profile_id: str,
    document_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return export_document(db, get_document(db, document_id, profile), payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/applications")
async def get_applications(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> list[dict[str, Any]]:
    require_profile(db, profile_id, user)
    return list_applications(db, profile_id)


@router.post("/profiles/{profile_id}/applications")
async def post_application(
    profile_id: str,
    payload: ApplicationRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return create_application(db, profile, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/applications/{application_id}")
async def get_application(
    profile_id: str,
    application_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return application_public(db, require_application(db, application_id, profile))
    except Exception as error:
        _handle(error)
        raise


@router.patch("/profiles/{profile_id}/applications/{application_id}")
async def patch_application(
    profile_id: str,
    application_id: str,
    payload: ApplicationPatchRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return update_application(db, require_application(db, application_id, profile), payload.model_dump(exclude_none=True))
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/applications/{application_id}/events")
async def post_application_event(
    profile_id: str,
    application_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return add_application_event(db, require_application(db, application_id, profile), payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/applications/{application_id}/stages")
async def post_application_stage(
    profile_id: str,
    application_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return add_application_stage(db, require_application(db, application_id, profile), payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/applications/{application_id}/outcome")
async def post_application_outcome(
    profile_id: str,
    application_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return record_application_outcome(db, require_application(db, application_id, profile), payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/applications/{application_id}/recalibrate")
async def post_application_recalibration(
    profile_id: str,
    application_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return recalibrate_from_application(db, require_application(db, application_id, profile))
    except Exception as error:
        _handle(error)
        raise


@router.get("/research/studies")
async def get_research_studies(db: Annotated[Session, Depends(get_db)]) -> list[dict[str, Any]]:
    return list_research_studies(db)


@router.post("/research/studies/ensure")
async def ensure_default_study(
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin_user)],
) -> dict[str, Any]:
    assert_research_ready()
    return ensure_research_study(db, demo=bool(payload.model_dump().get("demo", False)))


@router.get("/profiles/{profile_id}/research-evaluation")
async def get_research_evaluation(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    assert_research_ready()
    profile = require_profile(db, profile_id, user)
    study = ensure_research_study(db, demo=bool(user and user.is_demo))
    study_row = require_study(db, study["id"])
    return {
        "study": study,
        "summary": study_summary(db, study_row),
        "consent_template": research_consent_template(),
        "profile_id": profile.id,
    }


@router.post("/research/studies/{study_id}/profiles/{profile_id}/consent")
async def post_research_consent(
    study_id: str,
    profile_id: str,
    payload: ResearchConsentRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    assert_research_ready()
    profile = require_profile(db, profile_id, user)
    try:
        return consent_to_research(db, require_study(db, study_id), profile, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.post("/research/studies/{study_id}/profiles/{profile_id}/withdraw")
async def post_research_withdrawal(
    study_id: str,
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    assert_research_ready()
    profile = require_profile(db, profile_id, user)
    try:
        return withdraw_research_consent(db, require_study(db, study_id), profile)
    except Exception as error:
        _handle(error)
        raise


@router.post("/research/studies/{study_id}/profiles/{profile_id}/sessions")
async def post_research_session(
    study_id: str,
    profile_id: str,
    payload: ResearchSessionRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    assert_research_ready()
    profile = require_profile(db, profile_id, user)
    try:
        return create_research_session(db, require_study(db, study_id), profile, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/research-sessions/{session_id}/responses")
async def post_research_responses(
    profile_id: str,
    session_id: str,
    payload: ResearchResponsesRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    assert_research_ready()
    profile = require_profile(db, profile_id, user)
    try:
        return record_research_responses(db, require_research_session(db, session_id, profile), payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/research-sessions/{session_id}/metrics")
async def post_research_metrics(
    profile_id: str,
    session_id: str,
    payload: ResearchMetricsRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    assert_research_ready()
    profile = require_profile(db, profile_id, user)
    try:
        return record_research_metrics(db, require_research_session(db, session_id, profile), payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.get("/research/studies/{study_id}/summary")
async def get_study_summary(study_id: str, db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    try:
        return study_summary(db, require_study(db, study_id))
    except Exception as error:
        _handle(error)
        raise


@router.post("/research/studies/{study_id}/exports")
async def post_research_export(
    study_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin_user)],
) -> dict[str, Any]:
    assert_research_ready()
    try:
        return create_research_export(db, require_study(db, study_id), payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.get("/research/exports/{export_id}")
async def get_export(
    export_id: str,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin_user)],
) -> dict[str, Any]:
    try:
        return get_research_export(db, export_id)
    except Exception as error:
        _handle(error)
        raise
