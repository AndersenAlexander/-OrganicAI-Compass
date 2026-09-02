from datetime import datetime
from app.core.time import utc_now_naive
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_optional_user
from app.config import get_settings
from app.database import get_db
from app.models.learning import (
    LearningPath,
    LearningPathItem,
    LearningProvider,
    LearningObjective,
    LearningRecommendation,
    LearningRecommendationFactor,
    LearningResource,
    LearningResourceComparison,
    LearningResourceObjective,
    LearningResourceSkill,
    SkillGapItem,
)
from app.models.profile import Profile
from app.models.user import User
from app.services.profile_authorization import require_owned_profile, require_owned_record
from app.services.learning_engine import (
    NO_CAREER_SELECTED_MESSAGE,
    add_feedback,
    add_recommendation_to_roadmap,
    alternative_for_recommendation,
    comparison_public,
    create_learning_resource_comparison,
    create_skill_gap_analysis,
    delete_learning_data,
    generate_learning_path,
    generate_learning_recommendations,
    latest_gap_analysis,
    latest_learning_path,
    latest_recommendations,
    preferences_public,
    recommendation_public,
    resource_public,
    safe_resource_url,
    set_recommendation_status,
    sync_learning_catalogue,
    update_learning_path_item_progress,
    update_learning_preferences,
    ensure_learning_preferences,
    provider_public,
)

router = APIRouter()
settings = get_settings()


class LearningPreferencesPayload(BaseModel):
    preferred_language: str | None = Field(default=None, min_length=2, max_length=12)
    acceptable_secondary_languages: list[str] | None = None
    free_only: bool | None = None
    max_budget_per_course: float | None = Field(default=None, ge=0)
    monthly_learning_budget: float | None = Field(default=None, ge=0)
    available_hours_per_week: float | None = Field(default=None, ge=0, le=80)
    preferred_content_formats: list[str] | None = None
    preferred_session_length_minutes: int | None = Field(default=None, ge=5, le=480)
    theory_practice_preference: str | None = None
    certificate_importance: str | None = None
    preferred_difficulty: str | None = None
    target_completion_date: str | None = None
    accessibility_preferences: list[str] | None = None
    subtitles_required: bool | None = None
    mobile_friendly: bool | None = None
    offline_availability: bool | None = None
    provider_exclusions: list[str] | None = None
    strict_duration_limit_minutes: int | None = Field(default=None, ge=10)


class CareerMatchPayload(BaseModel):
    career_match_id: str | None = None


class RecommendationFeedbackPayload(BaseModel):
    reason_code: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    relevant: bool | None = None
    feedback_text: str | None = None


class RoadmapLearningActionPayload(BaseModel):
    roadmap_title: str | None = None
    learning_objective: str | None = None
    start_date: str | None = None
    target_completion_date: str | None = None
    weekly_commitment: str | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    expected_evidence: str | None = None
    associated_practical_project: str | None = None
    notes: str | None = None


class LearningComparisonPayload(BaseModel):
    recommendation_ids: list[str] = Field(min_length=1, max_length=3)
    criteria_weights: dict[str, float] = Field(default_factory=dict)


class LearningPathPayload(BaseModel):
    run_id: str | None = None


class LearningPathPatch(BaseModel):
    title: str | None = None
    summary: str | None = None
    status: str | None = None
    weekly_effort_hours: float | None = Field(default=None, ge=0, le=80)


class LearningProgressPayload(BaseModel):
    status: str | None = None
    progress_percentage: int | None = Field(default=None, ge=0, le=100)
    user_reported_progress: str | None = None
    completion_date: str | None = None
    evidence_url: str | None = None
    reflection: str | None = None
    difficulty_feedback: str | None = None
    relevance_feedback: str | None = None


class AdminResourcePayload(BaseModel):
    id: str
    provider_id: str
    title: str
    canonical_url: str
    resource_type: str
    skill_ids: list[str] = Field(default_factory=list)
    level: str = "beginner"
    language: str = "en"
    duration_minutes: int | None = None
    cost_type: str = "free"
    description: str = ""


class AdminVerifyPayload(BaseModel):
    quality_status: str = "Verified"
    notes: str = ""


def require_profile(db: Session, profile_id: str, user: User | None) -> Profile:
    return require_owned_profile(db, profile_id, user)


def require_recommendation(db: Session, recommendation_id: str, user: User | None) -> LearningRecommendation:
    item = db.get(LearningRecommendation, recommendation_id)
    return require_owned_record(item, user, resource_name="Learning recommendation")


def require_admin(user: User) -> None:
    if user.is_demo:
        raise HTTPException(403, "This action is unavailable in Demo Mode.")
    allowed = {item.strip().lower() for item in settings.admin_emails.split(",") if item.strip()}
    if not allowed or user.email.lower() not in allowed:
        raise HTTPException(403, "Admin access required")


def recommendation_details(db: Session, recommendation: LearningRecommendation) -> dict[str, Any]:
    resource = db.get(LearningResource, recommendation.learning_resource_id)
    factors = db.scalars(select(LearningResourceSkill).where(LearningResourceSkill.resource_id == resource.id)).all() if resource else []
    objectives = db.scalars(select(LearningResourceObjective).where(LearningResourceObjective.resource_id == resource.id)).all() if resource else []
    factor_rows = db.scalars(select(LearningRecommendationFactor).where(LearningRecommendationFactor.recommendation_id == recommendation.id)).all()
    gap = db.get(SkillGapItem, recommendation.skill_gap_item_id) if recommendation.skill_gap_item_id else None
    objective = db.get(LearningObjective, recommendation.learning_objective_id) if recommendation.learning_objective_id else None
    payload = recommendation_public(db, recommendation, resource, factor_rows, gap, objective)
    payload["resource"] = resource_public(resource, factors, objectives)
    return payload


@router.get("/learning/providers")
async def providers(db: Annotated[Session, Depends(get_db)]) -> list[dict[str, Any]]:
    sync_learning_catalogue(db)
    db.commit()
    rows = db.scalars(select(LearningProvider).order_by(LearningProvider.display_name)).all()
    return [provider_public(row) for row in rows]


@router.get("/learning/resources")
async def resources(
    db: Annotated[Session, Depends(get_db)],
    provider: str | None = None,
    skill_id: str | None = None,
    active_only: bool = True,
) -> list[dict[str, Any]]:
    sync_learning_catalogue(db)
    db.commit()
    statement = select(LearningResource)
    if provider:
        statement = statement.where(LearningResource.provider_id == provider)
    if active_only:
        statement = statement.where(LearningResource.active.is_(True))
    if skill_id:
        ids = db.scalars(select(LearningResourceSkill.resource_id).where(LearningResourceSkill.skill_id == skill_id)).all()
        statement = statement.where(LearningResource.id.in_(ids))
    rows = db.scalars(statement.order_by(LearningResource.provider_id, LearningResource.title)).all()
    return [resource_public(row) for row in rows]


@router.get("/learning/resources/{resource_id}")
async def resource_detail(resource_id: str, db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    sync_learning_catalogue(db)
    db.commit()
    row = db.get(LearningResource, resource_id)
    if not row:
        raise HTTPException(404, "Learning resource not found")
    skills = db.scalars(select(LearningResourceSkill).where(LearningResourceSkill.resource_id == row.id)).all()
    objectives = db.scalars(select(LearningResourceObjective).where(LearningResourceObjective.resource_id == row.id)).all()
    return resource_public(row, skills, objectives)


@router.get("/profiles/{profile_id}/learning-preferences")
async def get_preferences(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    row = ensure_learning_preferences(db, profile)
    db.commit()
    return preferences_public(row)


@router.put("/profiles/{profile_id}/learning-preferences")
async def put_preferences(
    profile_id: str,
    payload: LearningPreferencesPayload,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    return preferences_public(update_learning_preferences(db, profile, payload.model_dump(exclude_none=True)))


@router.post("/profiles/{profile_id}/skill-gap-analysis")
async def post_skill_gap_analysis(
    profile_id: str,
    payload: CareerMatchPayload,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    result = create_skill_gap_analysis(db, profile, payload.career_match_id)
    if result.get("status") == "no_career_selected":
        raise HTTPException(409, NO_CAREER_SELECTED_MESSAGE)
    return result


@router.get("/profiles/{profile_id}/skill-gap-analysis")
async def get_skill_gap_analysis(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
    career_match_id: str | None = None,
) -> dict[str, Any]:
    require_profile(db, profile_id, user)
    return latest_gap_analysis(db, profile_id, career_match_id)


@router.post("/profiles/{profile_id}/learning-recommendations")
async def post_learning_recommendations(
    profile_id: str,
    payload: CareerMatchPayload,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    result = generate_learning_recommendations(db, profile, payload.career_match_id)
    if result.get("status") == "no_career_selected":
        raise HTTPException(409, NO_CAREER_SELECTED_MESSAGE)
    return result


@router.get("/profiles/{profile_id}/learning-recommendations")
async def get_learning_recommendations(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
    career_match_id: str | None = None,
) -> dict[str, Any]:
    require_profile(db, profile_id, user)
    return latest_recommendations(db, profile_id, career_match_id)


@router.post("/learning-recommendations/{recommendation_id}/save")
async def save_learning_recommendation(
    recommendation_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    item = require_recommendation(db, recommendation_id, user)
    return recommendation_details(db, set_recommendation_status(db, item, "saved", "saved"))


@router.post("/learning-recommendations/{recommendation_id}/reject")
async def reject_learning_recommendation(
    recommendation_id: str,
    payload: RecommendationFeedbackPayload,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    item = require_recommendation(db, recommendation_id, user)
    return recommendation_details(db, set_recommendation_status(db, item, "rejected", payload.reason_code or "not_relevant", payload.feedback_text))


@router.post("/learning-recommendations/{recommendation_id}/feedback")
async def feedback_learning_recommendation(
    recommendation_id: str,
    payload: RecommendationFeedbackPayload,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    item = require_recommendation(db, recommendation_id, user)
    return add_feedback(db, item, payload.model_dump(exclude_none=True))


@router.post("/learning-recommendations/{recommendation_id}/alternative")
async def alternative_learning_recommendation(
    recommendation_id: str,
    payload: RecommendationFeedbackPayload,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    item = require_recommendation(db, recommendation_id, user)
    return alternative_for_recommendation(db, item, payload.reason_code)


@router.post("/learning-recommendations/{recommendation_id}/add-to-roadmap")
async def add_learning_to_roadmap(
    recommendation_id: str,
    payload: RoadmapLearningActionPayload,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    item = require_recommendation(db, recommendation_id, user)
    return add_recommendation_to_roadmap(db, item, payload.model_dump(exclude_none=True))


@router.post("/profiles/{profile_id}/learning-resource-comparisons")
async def post_resource_comparison(
    profile_id: str,
    payload: LearningComparisonPayload,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    return comparison_public(create_learning_resource_comparison(db, profile, payload.recommendation_ids, payload.criteria_weights))


@router.get("/profiles/{profile_id}/learning-resource-comparisons")
async def get_resource_comparisons(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> list[dict[str, Any]]:
    require_profile(db, profile_id, user)
    rows = db.scalars(select(LearningResourceComparison).where(LearningResourceComparison.profile_id == profile_id).order_by(LearningResourceComparison.created_at.desc())).all()
    return [comparison_public(row) for row in rows]


@router.get("/profiles/{profile_id}/learning-path")
async def get_learning_path(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    require_profile(db, profile_id, user)
    return latest_learning_path(db, profile_id)


@router.post("/profiles/{profile_id}/learning-path/generate")
async def post_learning_path(
    profile_id: str,
    payload: LearningPathPayload,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    return generate_learning_path(db, profile, payload.run_id)


@router.put("/profiles/{profile_id}/learning-path")
async def put_learning_path(
    profile_id: str,
    payload: LearningPathPatch,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    require_profile(db, profile_id, user)
    path = db.scalar(select(LearningPath).where(LearningPath.profile_id == profile_id).order_by(LearningPath.created_at.desc()))
    if not path:
        raise HTTPException(404, "Learning path not found")
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(path, key, value)
    db.commit()
    return latest_learning_path(db, profile_id)


@router.post("/learning-path-items/{item_id}/progress")
async def post_learning_path_progress(
    item_id: str,
    payload: LearningProgressPayload,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    item = db.get(LearningPathItem, item_id)
    if not item:
        raise HTTPException(404, "Learning path item not found")
    path = db.get(LearningPath, item.learning_path_id)
    require_owned_record(path, user, resource_name="Learning path item")
    if payload.evidence_url and not safe_resource_url(payload.evidence_url):
        raise HTTPException(422, "Evidence URL must be http(s) or an internal path.")
    return update_learning_path_item_progress(db, item, payload.model_dump(exclude_none=True))


@router.delete("/profiles/{profile_id}/learning-data")
async def delete_profile_learning_data(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    require_profile(db, profile_id, user)
    return delete_learning_data(db, profile_id)


@router.post("/admin/learning-resources")
async def admin_create_resource(
    payload: AdminResourcePayload,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    require_admin(user)
    if not safe_resource_url(payload.canonical_url):
        raise HTTPException(422, "Unsafe resource URL")
    sync_learning_catalogue(db)
    provider = db.get(LearningProvider, payload.provider_id)
    if not provider:
        raise HTTPException(404, "Learning provider not found")
    row = LearningResource(
        id=payload.id,
        provider_id=payload.provider_id,
        title=payload.title,
        canonical_url=payload.canonical_url,
        description=payload.description,
        resource_type=payload.resource_type,
        level=payload.level,
        language=payload.language,
        duration_minutes=payload.duration_minutes,
        cost_type=payload.cost_type,
        quality_status="Needs review",
        source_provenance="admin submitted",
        active=True,
    )
    db.add(row)
    db.flush()
    for skill_id in payload.skill_ids:
        db.add(LearningResourceSkill(resource_id=row.id, skill_id=skill_id, coverage_level="primary"))
    db.commit()
    return resource_public(row)


@router.put("/admin/learning-resources/{resource_id}")
async def admin_update_resource(
    resource_id: str,
    payload: AdminResourcePayload,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    require_admin(user)
    row = db.get(LearningResource, resource_id)
    if not row:
        raise HTTPException(404, "Learning resource not found")
    if not safe_resource_url(payload.canonical_url):
        raise HTTPException(422, "Unsafe resource URL")
    for key, value in payload.model_dump(exclude={"skill_ids"}).items():
        if key == "provider_id":
            row.provider_id = value
        elif key != "id":
            setattr(row, key, value)
    db.execute(delete(LearningResourceSkill).where(LearningResourceSkill.resource_id == row.id))
    for skill_id in payload.skill_ids:
        db.add(LearningResourceSkill(resource_id=row.id, skill_id=skill_id, coverage_level="primary"))
    db.commit()
    return resource_public(row)


@router.post("/admin/learning-resources/{resource_id}/verify")
async def admin_verify_resource(
    resource_id: str,
    payload: AdminVerifyPayload,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    require_admin(user)
    row = db.get(LearningResource, resource_id)
    if not row:
        raise HTTPException(404, "Learning resource not found")
    row.quality_status = payload.quality_status
    row.last_verified_at = utc_now_naive()
    row.notes_limitations = payload.notes or row.notes_limitations
    db.commit()
    return resource_public(row)


@router.post("/admin/learning-resources/refresh")
async def admin_refresh_resources(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    require_admin(user)
    sync_learning_catalogue(db)
    db.commit()
    return {"status": "refreshed", "resource_count": len(db.scalars(select(LearningResource.id)).all())}

