import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utc_now_naive
from app.database import Base


def new_id() -> str:
    return str(uuid.uuid4())


class AssessmentDefinition(Base):
    __tablename__ = "assessment_definitions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    methodology_note: Mapped[str] = mapped_column(Text, default="")
    disclaimer: Mapped[str] = mapped_column(Text, default="")
    source_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class AssessmentModule(Base):
    __tablename__ = "assessment_modules"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    assessment_id: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    optional: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class AssessmentItem(Base):
    __tablename__ = "assessment_items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    module_id: Mapped[str] = mapped_column(String, index=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    item_type: Mapped[str] = mapped_column(String(40), nullable=False)
    dimension: Mapped[str | None] = mapped_column(String(80), index=True)
    reverse_scored: Mapped[bool] = mapped_column(Boolean, default=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    quick_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class AssessmentOption(Base):
    __tablename__ = "assessment_options"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    item_id: Mapped[str] = mapped_column(String, index=True)
    value: Mapped[str] = mapped_column(String(120), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    score_value: Mapped[float | None] = mapped_column(Float)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    mode: Mapped[str] = mapped_column(String(30), default="quick", index=True)
    status: Mapped[str] = mapped_column(String(30), default="not_started", index=True)
    consent_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    assessment_version: Mapped[str] = mapped_column(String(50), default="career-assessment-v1")
    scoring_version: Mapped[str] = mapped_column(String(50), default="career-scoring-v1")
    completion_time_seconds: Mapped[int | None] = mapped_column(Integer)
    last_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime)
    source_type: Mapped[str] = mapped_column(String(30), default="user")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)


class AssessmentResponse(Base):
    __tablename__ = "assessment_responses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("assessment_sessions.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    module_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    item_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    response_type: Mapped[str] = mapped_column(String(40), default="likert")
    numeric_value: Mapped[float | None] = mapped_column(Float)
    text_value: Mapped[str | None] = mapped_column(Text)
    option_value: Mapped[str | None] = mapped_column(String(255))
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    excluded_from_recommendations: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmation_status: Mapped[str] = mapped_column(String(30), default="self_reported")
    source_type: Mapped[str] = mapped_column(String(30), default="self_reported")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class AssessmentScore(Base):
    __tablename__ = "assessment_scores"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("assessment_sessions.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    score_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    dimension: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    raw_score: Mapped[float] = mapped_column(Float, default=0)
    normalized_score: Mapped[float] = mapped_column(Float, default=0)
    label: Mapped[str] = mapped_column(String(120), default="")
    interpretation: Mapped[str] = mapped_column(Text, default="")
    assessment_version: Mapped[str] = mapped_column(String(50), default="career-assessment-v1")
    scoring_version: Mapped[str] = mapped_column(String(50), default="career-scoring-v1")
    source_type: Mapped[str] = mapped_column(String(30), default="calculated")
    confirmation_status: Mapped[str] = mapped_column(String(30), default="needs_review")
    score_json: Mapped[dict] = mapped_column(JSON, default=dict)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class PersonalityResult(Base):
    __tablename__ = "personality_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("assessment_sessions.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    results_json: Mapped[dict] = mapped_column(JSON, default=dict)
    assessment_version: Mapped[str] = mapped_column(String(50), default="career-assessment-v1")
    scoring_version: Mapped[str] = mapped_column(String(50), default="career-scoring-v1")
    confirmation_status: Mapped[str] = mapped_column(String(30), default="needs_review")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class CareerInterestResult(Base):
    __tablename__ = "career_interest_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("assessment_sessions.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    combined_profile: Mapped[str] = mapped_column(String(160), default="")
    results_json: Mapped[dict] = mapped_column(JSON, default=dict)
    assessment_version: Mapped[str] = mapped_column(String(50), default="career-assessment-v1")
    scoring_version: Mapped[str] = mapped_column(String(50), default="career-scoring-v1")
    confirmation_status: Mapped[str] = mapped_column(String(30), default="needs_review")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class WorkValueResult(Base):
    __tablename__ = "work_value_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("assessment_sessions.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    top_values_json: Mapped[list] = mapped_column(JSON, default=list)
    conflicts_json: Mapped[list] = mapped_column(JSON, default=list)
    results_json: Mapped[dict] = mapped_column(JSON, default=dict)
    assessment_version: Mapped[str] = mapped_column(String(50), default="career-assessment-v1")
    scoring_version: Mapped[str] = mapped_column(String(50), default="career-scoring-v1")
    confirmation_status: Mapped[str] = mapped_column(String(30), default="needs_review")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class SkillsInventory(Base):
    __tablename__ = "skills_inventory"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("assessment_sessions.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    skill_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    skill_label: Mapped[str] = mapped_column(String(160), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=0)
    evidence_status: Mapped[str] = mapped_column(String(50), default="self_reported")
    evidence_note: Mapped[str] = mapped_column(Text, default="")
    confirmation_status: Mapped[str] = mapped_column(String(30), default="self_reported")
    assessment_version: Mapped[str] = mapped_column(String(50), default="career-assessment-v1")
    scoring_version: Mapped[str] = mapped_column(String(50), default="career-scoring-v1")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class SkillEvidence(Base):
    __tablename__ = "skill_evidence"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    skill_inventory_id: Mapped[str] = mapped_column(ForeignKey("skills_inventory.id"), index=True)
    evidence_type: Mapped[str] = mapped_column(String(60), default="self_reported")
    title: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(String(40), default="unverified")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class AIReadinessResult(Base):
    __tablename__ = "ai_readiness_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("assessment_sessions.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    literacy_level: Mapped[str] = mapped_column(String(40), default="Emerging")
    readiness_level: Mapped[str] = mapped_column(String(40), default="Emerging")
    results_json: Mapped[dict] = mapped_column(JSON, default=dict)
    assessment_version: Mapped[str] = mapped_column(String(50), default="career-assessment-v1")
    scoring_version: Mapped[str] = mapped_column(String(50), default="career-scoring-v1")
    confirmation_status: Mapped[str] = mapped_column(String(30), default="needs_review")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class ChangeReadinessResult(Base):
    __tablename__ = "change_readiness_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("assessment_sessions.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    feasibility_label: Mapped[str] = mapped_column(String(120), default="Exploring options")
    results_json: Mapped[dict] = mapped_column(JSON, default=dict)
    constraints_json: Mapped[list] = mapped_column(JSON, default=list)
    assessment_version: Mapped[str] = mapped_column(String(50), default="career-assessment-v1")
    scoring_version: Mapped[str] = mapped_column(String(50), default="career-scoring-v1")
    confirmation_status: Mapped[str] = mapped_column(String(30), default="needs_review")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class CareerRoleTemplate(Base):
    __tablename__ = "career_role_templates"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role_family: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    required_skills_json: Mapped[list] = mapped_column(JSON, default=list)
    useful_transferable_skills_json: Mapped[list] = mapped_column(JSON, default=list)
    interest_profile_json: Mapped[dict] = mapped_column(JSON, default=dict)
    work_style_tendencies_json: Mapped[dict] = mapped_column(JSON, default=dict)
    compatible_work_values_json: Mapped[list] = mapped_column(JSON, default=list)
    ai_augmentation_opportunities_json: Mapped[list] = mapped_column(JSON, default=list)
    entry_requirements_json: Mapped[list] = mapped_column(JSON, default=list)
    skill_gap_categories_json: Mapped[list] = mapped_column(JSON, default=list)
    typical_transition_path_json: Mapped[list] = mapped_column(JSON, default=list)
    source_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[str] = mapped_column(String(50), default="role-catalogue-v1")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class CareerMatch(Base):
    __tablename__ = "career_matches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    session_id: Mapped[str | None] = mapped_column(ForeignKey("assessment_sessions.id"), nullable=True, index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    role_template_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role_family: Mapped[str] = mapped_column(String(120), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    alignment_score: Mapped[float] = mapped_column(Float, default=0)
    alignment_label: Mapped[str] = mapped_column(String(80), default="")
    explanation: Mapped[str] = mapped_column(Text, default="")
    supporting_factors_json: Mapped[list] = mapped_column(JSON, default=list)
    conflicting_factors_json: Mapped[list] = mapped_column(JSON, default=list)
    missing_skills_json: Mapped[list] = mapped_column(JSON, default=list)
    transferable_skills_json: Mapped[list] = mapped_column(JSON, default=list)
    ai_opportunities_json: Mapped[list] = mapped_column(JSON, default=list)
    next_step: Mapped[str] = mapped_column(Text, default="")
    transition_difficulty: Mapped[str] = mapped_column(String(80), default="moderate")
    time_horizon: Mapped[str] = mapped_column(String(80), default="2-6 months")
    status: Mapped[str] = mapped_column(String(40), default="suggested", index=True)
    user_feedback: Mapped[str | None] = mapped_column(Text)
    user_priority: Mapped[int | None] = mapped_column(Integer)
    assumptions_json: Mapped[list] = mapped_column(JSON, default=list)
    limitations_json: Mapped[list] = mapped_column(JSON, default=list)
    source_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    assessment_version: Mapped[str] = mapped_column(String(50), default="career-assessment-v1")
    scoring_version: Mapped[str] = mapped_column(String(50), default="career-scoring-v1")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class CareerMatchFactor(Base):
    __tablename__ = "career_match_factors"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    match_id: Mapped[str] = mapped_column(ForeignKey("career_matches.id"), index=True)
    factor_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(160), nullable=False)
    raw_value: Mapped[float] = mapped_column(Float, default=0)
    normalized_value: Mapped[float] = mapped_column(Float, default=0)
    weight: Mapped[float] = mapped_column(Float, default=0)
    polarity: Mapped[str] = mapped_column(String(20), default="supporting")
    evidence_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class CareerComparison(Base):
    __tablename__ = "career_comparisons"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    match_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    criteria_weights_json: Mapped[dict] = mapped_column(JSON, default=dict)
    decision_priorities_json: Mapped[dict] = mapped_column(JSON, default=dict)
    matrix_json: Mapped[dict] = mapped_column(JSON, default=dict)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class CareerDecision(Base):
    __tablename__ = "career_decisions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    career_match_id: Mapped[str | None] = mapped_column(ForeignKey("career_matches.id"), nullable=True, index=True)
    decision_type: Mapped[str] = mapped_column(String(60), default="reflection")
    status: Mapped[str] = mapped_column(String(40), default="saved")
    notes: Mapped[str] = mapped_column(Text, default="")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class AssessmentInterpretation(Base):
    __tablename__ = "assessment_interpretations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    session_id: Mapped[str | None] = mapped_column(ForeignKey("assessment_sessions.id"), nullable=True, index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    source_type: Mapped[str] = mapped_column(String(40), default="user_confirmed")
    confirmation_status: Mapped[str] = mapped_column(String(40), default="needs_review")
    summary: Mapped[str] = mapped_column(Text, default="")
    corrections_json: Mapped[dict] = mapped_column(JSON, default=dict)
    reflection_answers_json: Mapped[dict] = mapped_column(JSON, default=dict)
    assessment_version: Mapped[str] = mapped_column(String(50), default="career-assessment-v1")
    scoring_version: Mapped[str] = mapped_column(String(50), default="career-scoring-v1")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

