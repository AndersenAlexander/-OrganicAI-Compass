import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utc_now_naive
from app.database import Base


def new_id() -> str:
    return str(uuid.uuid4())


class LearningProvider(Base):
    __tablename__ = "learning_providers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    provider_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(60), default="curated")
    base_url: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    supports_external_search: Mapped[bool] = mapped_column(Boolean, default=False)
    api_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class LearningResource(Base):
    __tablename__ = "learning_resources"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    provider_id: Mapped[str] = mapped_column(ForeignKey("learning_providers.id"), index=True)
    external_id: Mapped[str | None] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    resource_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    level: Mapped[str] = mapped_column(String(40), default="beginner", index=True)
    language: Mapped[str] = mapped_column(String(20), default="en", index=True)
    subtitles_json: Mapped[list] = mapped_column(JSON, default=list)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    cost_type: Mapped[str] = mapped_column(String(40), default="free", index=True)
    displayed_price: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str | None] = mapped_column(String(10))
    instructor_organization: Mapped[str | None] = mapped_column(String(255))
    rating: Mapped[float | None] = mapped_column(Float)
    review_count: Mapped[int | None] = mapped_column(Integer)
    publication_date: Mapped[str | None] = mapped_column(String(40))
    last_updated_date: Mapped[str | None] = mapped_column(String(40))
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    prerequisites_json: Mapped[list] = mapped_column(JSON, default=list)
    certificate_available: Mapped[bool | None] = mapped_column(Boolean)
    practical_exercises: Mapped[bool] = mapped_column(Boolean, default=False)
    project_included: Mapped[bool] = mapped_column(Boolean, default=False)
    quality_status: Mapped[str] = mapped_column(String(60), default="Partially verified", index=True)
    source_provenance: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    affiliate: Mapped[bool] = mapped_column(Boolean, default=False)
    affiliate_disclosure: Mapped[str] = mapped_column(Text, default="No affiliate relationship is used for ranking.")
    notes_limitations: Mapped[str] = mapped_column(Text, default="")
    metadata_version: Mapped[str] = mapped_column(String(60), default="learning-catalogue-v1")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class LearningResourceVersion(Base):
    __tablename__ = "learning_resource_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    resource_id: Mapped[str] = mapped_column(ForeignKey("learning_resources.id"), index=True)
    metadata_version: Mapped[str] = mapped_column(String(60), default="learning-catalogue-v1")
    snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class LearningResourceSkill(Base):
    __tablename__ = "learning_resource_skills"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    resource_id: Mapped[str] = mapped_column(ForeignKey("learning_resources.id"), index=True)
    skill_id: Mapped[str] = mapped_column(String(120), index=True)
    coverage_level: Mapped[str] = mapped_column(String(40), default="supporting")
    target_level: Mapped[str] = mapped_column(String(40), default="intermediate")
    weight: Mapped[float] = mapped_column(Float, default=1.0)


class LearningResourceObjective(Base):
    __tablename__ = "learning_resource_objectives"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    resource_id: Mapped[str] = mapped_column(ForeignKey("learning_resources.id"), index=True)
    objective_key: Mapped[str] = mapped_column(String(160), index=True)
    coverage_level: Mapped[str] = mapped_column(String(40), default="supporting")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class LearningResourceVerification(Base):
    __tablename__ = "learning_resource_verifications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    resource_id: Mapped[str] = mapped_column(ForeignKey("learning_resources.id"), index=True)
    verification_status: Mapped[str] = mapped_column(String(60), default="Partially verified", index=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime)
    verified_by: Mapped[str | None] = mapped_column(String(120))
    verification_method: Mapped[str] = mapped_column(String(120), default="manual catalogue review")
    last_availability_check: Mapped[datetime | None] = mapped_column(DateTime)
    external_metadata_timestamp: Mapped[datetime | None] = mapped_column(DateTime)
    verification_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class LearningPreferences(Base):
    __tablename__ = "learning_preferences"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    preferred_language: Mapped[str] = mapped_column(String(20), default="en")
    acceptable_secondary_languages_json: Mapped[list] = mapped_column(JSON, default=list)
    free_only: Mapped[bool] = mapped_column(Boolean, default=False)
    max_budget_per_course: Mapped[float | None] = mapped_column(Float)
    monthly_learning_budget: Mapped[float | None] = mapped_column(Float)
    available_hours_per_week: Mapped[float] = mapped_column(Float, default=6)
    preferred_content_formats_json: Mapped[list] = mapped_column(JSON, default=list)
    preferred_session_length_minutes: Mapped[int | None] = mapped_column(Integer)
    theory_practice_preference: Mapped[str] = mapped_column(String(40), default="mixed")
    certificate_importance: Mapped[str] = mapped_column(String(40), default="medium")
    preferred_difficulty: Mapped[str] = mapped_column(String(40), default="adaptive")
    target_completion_date: Mapped[str | None] = mapped_column(String(40))
    accessibility_preferences_json: Mapped[list] = mapped_column(JSON, default=list)
    subtitles_required: Mapped[bool] = mapped_column(Boolean, default=False)
    mobile_friendly: Mapped[bool] = mapped_column(Boolean, default=False)
    offline_availability: Mapped[bool] = mapped_column(Boolean, default=False)
    provider_exclusions_json: Mapped[list] = mapped_column(JSON, default=list)
    strict_duration_limit_minutes: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class SkillGapAnalysis(Base):
    __tablename__ = "skill_gap_analyses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    career_match_id: Mapped[str | None] = mapped_column(ForeignKey("career_matches.id"), nullable=True, index=True)
    role_template_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    analysis_version: Mapped[str] = mapped_column(String(60), default="skill-gap-v1")
    status: Mapped[str] = mapped_column(String(40), default="ready", index=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    hard_filters_json: Mapped[list] = mapped_column(JSON, default=list)
    context_json: Mapped[dict] = mapped_column(JSON, default=dict)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class SkillGapItem(Base):
    __tablename__ = "skill_gap_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("skill_gap_analyses.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    career_match_id: Mapped[str | None] = mapped_column(ForeignKey("career_matches.id"), nullable=True, index=True)
    skill_id: Mapped[str] = mapped_column(String(120), index=True)
    skill_label: Mapped[str] = mapped_column(String(160), nullable=False)
    current_level: Mapped[int] = mapped_column(Integer, default=0)
    target_level: Mapped[int] = mapped_column(Integer, default=2)
    gap_size: Mapped[int] = mapped_column(Integer, default=0)
    importance: Mapped[float] = mapped_column(Float, default=1.0)
    evidence_level: Mapped[str] = mapped_column(String(60), default="self_reported")
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_augmentable: Mapped[bool] = mapped_column(Boolean, default=False)
    prerequisite_skill_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    missing_prerequisites_json: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(60), default="No gap", index=True)
    priority_label: Mapped[str] = mapped_column(String(40), default="Optional", index=True)
    priority_score_internal: Mapped[float] = mapped_column(Float, default=0)
    user_priority: Mapped[int | None] = mapped_column(Integer)
    dependency_order: Mapped[int] = mapped_column(Integer, default=0)
    explanation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class LearningObjective(Base):
    __tablename__ = "learning_objectives"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("skill_gap_analyses.id"), index=True)
    gap_item_id: Mapped[str] = mapped_column(ForeignKey("skill_gap_items.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    career_match_id: Mapped[str | None] = mapped_column(ForeignKey("career_matches.id"), nullable=True, index=True)
    objective_key: Mapped[str] = mapped_column(String(160), index=True)
    skill_id: Mapped[str] = mapped_column(String(120), index=True)
    target_level: Mapped[int] = mapped_column(Integer, default=2)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    prerequisite_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    estimated_effort_minutes: Mapped[int] = mapped_column(Integer, default=120)
    evidence_expected: Mapped[str] = mapped_column(Text, default="")
    role_relevance: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String(40), default="Recommended")
    objective_version: Mapped[str] = mapped_column(String(60), default="learning-objective-v1")
    status: Mapped[str] = mapped_column(String(40), default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class LearningRecommendationRun(Base):
    __tablename__ = "learning_recommendation_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    career_match_id: Mapped[str | None] = mapped_column(ForeignKey("career_matches.id"), nullable=True, index=True)
    skill_gap_analysis_id: Mapped[str | None] = mapped_column(ForeignKey("skill_gap_analyses.id"), nullable=True, index=True)
    preferences_id: Mapped[str | None] = mapped_column(ForeignKey("learning_preferences.id"), nullable=True, index=True)
    recommendation_version: Mapped[str] = mapped_column(String(60), default="learning-rec-v1")
    status: Mapped[str] = mapped_column(String(40), default="ready", index=True)
    provider_status_json: Mapped[list] = mapped_column(JSON, default=list)
    filters_json: Mapped[list] = mapped_column(JSON, default=list)
    ranking_weights_json: Mapped[dict] = mapped_column(JSON, default=dict)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class LearningRecommendation(Base):
    __tablename__ = "learning_recommendations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("learning_recommendation_runs.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    career_match_id: Mapped[str | None] = mapped_column(ForeignKey("career_matches.id"), nullable=True, index=True)
    skill_gap_item_id: Mapped[str | None] = mapped_column(ForeignKey("skill_gap_items.id"), nullable=True, index=True)
    learning_objective_id: Mapped[str | None] = mapped_column(ForeignKey("learning_objectives.id"), nullable=True, index=True)
    learning_resource_id: Mapped[str] = mapped_column(ForeignKey("learning_resources.id"), index=True)
    alignment_label: Mapped[str] = mapped_column(String(80), default="Alternative option")
    ranking_score_internal: Mapped[float] = mapped_column(Float, default=0)
    rank_position: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(40), default="suggested", index=True)
    explanation: Mapped[str] = mapped_column(Text, default="")
    limitations_json: Mapped[list] = mapped_column(JSON, default=list)
    recommendation_version: Mapped[str] = mapped_column(String(60), default="learning-rec-v1")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class LearningRecommendationFactor(Base):
    __tablename__ = "learning_recommendation_factors"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    recommendation_id: Mapped[str] = mapped_column(ForeignKey("learning_recommendations.id"), index=True)
    factor_type: Mapped[str] = mapped_column(String(80), index=True)
    factor_value: Mapped[float] = mapped_column(Float, default=0)
    weight: Mapped[float] = mapped_column(Float, default=0)
    explanation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class LearningResourceFeedback(Base):
    __tablename__ = "learning_resource_feedback"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    recommendation_id: Mapped[str | None] = mapped_column(ForeignKey("learning_recommendations.id"), nullable=True, index=True)
    learning_resource_id: Mapped[str | None] = mapped_column(ForeignKey("learning_resources.id"), nullable=True, index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    reason_code: Mapped[str | None] = mapped_column(String(60), index=True)
    rating: Mapped[int | None] = mapped_column(Integer)
    relevant: Mapped[bool | None] = mapped_column(Boolean)
    feedback_text: Mapped[str | None] = mapped_column(Text)
    effect_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    career_match_id: Mapped[str | None] = mapped_column(ForeignKey("career_matches.id"), nullable=True, index=True)
    recommendation_run_id: Mapped[str | None] = mapped_column(ForeignKey("learning_recommendation_runs.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), default="Personalised Learning Path")
    summary: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="draft", index=True)
    weekly_effort_hours: Mapped[float] = mapped_column(Float, default=6)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class LearningPathPhase(Base):
    __tablename__ = "learning_path_phases"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    learning_path_id: Mapped[str] = mapped_column(ForeignKey("learning_paths.id"), index=True)
    phase_index: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    objectives_json: Mapped[list] = mapped_column(JSON, default=list)
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, default=240)
    weekly_effort_hours: Mapped[float] = mapped_column(Float, default=3)
    completion_evidence: Mapped[str] = mapped_column(Text, default="")
    dependencies_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class LearningPathItem(Base):
    __tablename__ = "learning_path_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    learning_path_id: Mapped[str] = mapped_column(ForeignKey("learning_paths.id"), index=True)
    phase_id: Mapped[str] = mapped_column(ForeignKey("learning_path_phases.id"), index=True)
    recommendation_id: Mapped[str | None] = mapped_column(ForeignKey("learning_recommendations.id"), nullable=True, index=True)
    learning_resource_id: Mapped[str | None] = mapped_column(ForeignKey("learning_resources.id"), nullable=True, index=True)
    learning_objective_id: Mapped[str | None] = mapped_column(ForeignKey("learning_objectives.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="planned", index=True)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0)
    user_reported_progress: Mapped[str] = mapped_column(Text, default="")
    completion_date: Mapped[str | None] = mapped_column(String(40))
    evidence_url: Mapped[str | None] = mapped_column(Text)
    reflection: Mapped[str] = mapped_column(Text, default="")
    difficulty_feedback: Mapped[str | None] = mapped_column(String(60))
    relevance_feedback: Mapped[str | None] = mapped_column(String(60))
    expected_evidence: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class PracticalProject(Base):
    __tablename__ = "practical_projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    career_match_id: Mapped[str | None] = mapped_column(ForeignKey("career_matches.id"), nullable=True, index=True)
    skill_gap_item_id: Mapped[str | None] = mapped_column(ForeignKey("skill_gap_items.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    skills_demonstrated_json: Mapped[list] = mapped_column(JSON, default=list)
    estimated_effort_minutes: Mapped[int] = mapped_column(Integer, default=240)
    suggested_deliverables_json: Mapped[list] = mapped_column(JSON, default=list)
    completion_criteria_json: Mapped[list] = mapped_column(JSON, default=list)
    portfolio_value: Mapped[str] = mapped_column(Text, default="")
    prerequisites_json: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(40), default="suggested", index=True)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class RoadmapLearningAction(Base):
    __tablename__ = "roadmap_learning_actions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    roadmap_action_id: Mapped[str] = mapped_column(ForeignKey("roadmap_actions.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    recommendation_id: Mapped[str | None] = mapped_column(ForeignKey("learning_recommendations.id"), nullable=True, index=True)
    learning_resource_id: Mapped[str | None] = mapped_column(ForeignKey("learning_resources.id"), nullable=True, index=True)
    learning_objective_id: Mapped[str | None] = mapped_column(ForeignKey("learning_objectives.id"), nullable=True, index=True)
    expected_evidence: Mapped[str] = mapped_column(Text, default="")
    evidence_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="planned", index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class LearningResourceComparison(Base):
    __tablename__ = "learning_resource_comparisons"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    recommendation_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    resource_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    criteria_weights_json: Mapped[dict] = mapped_column(JSON, default=dict)
    matrix_json: Mapped[dict] = mapped_column(JSON, default=dict)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class ExternalProviderCache(Base):
    __tablename__ = "external_provider_cache"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    provider_name: Mapped[str] = mapped_column(String(80), index=True)
    cache_key: Mapped[str] = mapped_column(String(255), index=True)
    response_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(40), default="cached")
    error_message: Mapped[str] = mapped_column(Text, default="")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)

