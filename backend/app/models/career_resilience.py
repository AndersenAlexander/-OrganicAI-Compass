import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utc_now_naive
from app.database import Base


def new_id() -> str:
    return str(uuid.uuid4())


class CareerExperimentTemplate(Base):
    __tablename__ = "career_experiment_templates"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    target_role_family: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(Text, default="")
    real_world_scenario: Mapped[str] = mapped_column(Text, default="")
    user_instructions_json: Mapped[list] = mapped_column(JSON, default=list)
    expected_deliverables_json: Mapped[list] = mapped_column(JSON, default=list)
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, default=180)
    difficulty: Mapped[str] = mapped_column(String(40), default="intermediate", index=True)
    required_skills_json: Mapped[list] = mapped_column(JSON, default=list)
    evaluated_skills_json: Mapped[list] = mapped_column(JSON, default=list)
    optional_prerequisites_json: Mapped[list] = mapped_column(JSON, default=list)
    allowed_tools_json: Mapped[list] = mapped_column(JSON, default=list)
    ai_assistance_policy: Mapped[str] = mapped_column(Text, default="")
    reflection_questions_json: Mapped[list] = mapped_column(JSON, default=list)
    completion_criteria_json: Mapped[list] = mapped_column(JSON, default=list)
    evidence_generated_json: Mapped[list] = mapped_column(JSON, default=list)
    version: Mapped[str] = mapped_column(String(60), default="career-experiment-catalogue-v1")
    source_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class CareerExperimentRubric(Base):
    __tablename__ = "career_experiment_rubrics"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    experiment_template_id: Mapped[str] = mapped_column(ForeignKey("career_experiment_templates.id"), index=True)
    version: Mapped[str] = mapped_column(String(60), default="career-experiment-rubric-v1")
    rating_scale_json: Mapped[list] = mapped_column(JSON, default=list)
    source_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class CareerExperimentCriterion(Base):
    __tablename__ = "career_experiment_criteria"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    rubric_id: Mapped[str] = mapped_column(ForeignKey("career_experiment_rubrics.id"), index=True)
    criterion_id: Mapped[str] = mapped_column(String(120), index=True)
    skill_id: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    rating_scale_json: Mapped[list] = mapped_column(JSON, default=list)
    evidence_requirement: Mapped[str] = mapped_column(Text, default="")
    interpretation_json: Mapped[dict] = mapped_column(JSON, default=dict)
    order_index: Mapped[int] = mapped_column(Integer, default=0)


class CareerExperimentSession(Base):
    __tablename__ = "career_experiment_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    career_match_id: Mapped[str | None] = mapped_column(ForeignKey("career_matches.id"), nullable=True, index=True)
    experiment_template_id: Mapped[str] = mapped_column(ForeignKey("career_experiment_templates.id"), index=True)
    hypothesis_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    roadmap_action_id: Mapped[str | None] = mapped_column(ForeignKey("roadmap_actions.id"), nullable=True, index=True)
    mode: Mapped[str] = mapped_column(String(40), default="guided", index=True)
    status: Mapped[str] = mapped_column(String(40), default="planned", index=True)
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    version: Mapped[str] = mapped_column(String(60), default="career-experiment-session-v1")
    source_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence_label: Mapped[str] = mapped_column(String(80), default="Additional evidence required")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime)


class CareerExperimentSubmission(Base):
    __tablename__ = "career_experiment_submissions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("career_experiment_sessions.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    text_response: Mapped[str] = mapped_column(Text, default="")
    project_url: Mapped[str | None] = mapped_column(Text)
    repository_url: Mapped[str | None] = mapped_column(Text)
    portfolio_url: Mapped[str | None] = mapped_column(Text)
    document_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    file_references_json: Mapped[list] = mapped_column(JSON, default=list)
    completion_notes: Mapped[str] = mapped_column(Text, default="")
    time_spent_minutes: Mapped[int | None] = mapped_column(Integer)
    ai_tools_used_json: Mapped[list] = mapped_column(JSON, default=list)
    assistance_level: Mapped[str] = mapped_column(String(60), default="not_specified")
    self_rated_difficulty: Mapped[int | None] = mapped_column(Integer)
    self_rated_enjoyment: Mapped[int | None] = mapped_column(Integer)
    confidence_before: Mapped[int | None] = mapped_column(Integer)
    confidence_after: Mapped[int | None] = mapped_column(Integer)
    reflection_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(40), default="submitted", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class CareerExperimentReview(Base):
    __tablename__ = "career_experiment_reviews"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("career_experiment_sessions.id"), index=True)
    submission_id: Mapped[str | None] = mapped_column(ForeignKey("career_experiment_submissions.id"), nullable=True, index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(60), default="self_review", index=True)
    reviewer_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    scores_json: Mapped[dict] = mapped_column(JSON, default=dict)
    narrative: Mapped[str] = mapped_column(Text, default="")
    limitations_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class CareerExperimentResult(Base):
    __tablename__ = "career_experiment_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("career_experiment_sessions.id"), index=True)
    submission_id: Mapped[str] = mapped_column(ForeignKey("career_experiment_submissions.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, default=0)
    overall_label: Mapped[str] = mapped_column(String(80), default="Emerging evidence")
    criteria_scores_json: Mapped[list] = mapped_column(JSON, default=list)
    skills_evaluated_json: Mapped[list] = mapped_column(JSON, default=list)
    strengths_json: Mapped[list] = mapped_column(JSON, default=list)
    improvement_areas_json: Mapped[list] = mapped_column(JSON, default=list)
    deterministic_version: Mapped[str] = mapped_column(String(60), default="career-experiment-eval-v1")
    evidence_created_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class SkillEvidenceSource(Base):
    __tablename__ = "skill_evidence_sources"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    skill_evidence_id: Mapped[str] = mapped_column(ForeignKey("skill_evidence.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), default="career_experiment", index=True)
    source_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    url: Mapped[str | None] = mapped_column(Text)
    source_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    verified_by: Mapped[str | None] = mapped_column(String(120))
    independent_confirmation: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class SkillEvidenceConfidence(Base):
    __tablename__ = "skill_evidence_confidence"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    skill_evidence_id: Mapped[str] = mapped_column(ForeignKey("skill_evidence.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    skill_id: Mapped[str] = mapped_column(String(120), index=True)
    confidence_label: Mapped[str] = mapped_column(String(80), default="Limited evidence", index=True)
    strength_label: Mapped[str] = mapped_column(String(80), default="Self-reported", index=True)
    score_internal: Mapped[float] = mapped_column(Float, default=0)
    factors_json: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[str] = mapped_column(String(60), default="evidence-confidence-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class SkillRecency(Base):
    __tablename__ = "skill_recency"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    skill_id: Mapped[str] = mapped_column(String(120), index=True)
    first_demonstrated_at: Mapped[datetime | None] = mapped_column(DateTime)
    most_recent_evidence_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_professional_use_at: Mapped[datetime | None] = mapped_column(DateTime)
    evidence_age_days: Mapped[int | None] = mapped_column(Integer)
    refresh_recommendation: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(80), default="Unknown", index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class CareerHypothesis(Base):
    __tablename__ = "career_hypotheses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    career_match_id: Mapped[str | None] = mapped_column(ForeignKey("career_matches.id"), nullable=True, index=True)
    role_template_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role_family: Mapped[str] = mapped_column(String(160), default="", index=True)
    statement: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)
    uncertainty_label: Mapped[str] = mapped_column(String(80), default="Additional evidence required")
    current_alignment_score: Mapped[float] = mapped_column(Float, default=0)
    source_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    version: Mapped[str] = mapped_column(String(60), default="career-hypothesis-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class CareerHypothesisVersion(Base):
    __tablename__ = "career_hypothesis_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    hypothesis_id: Mapped[str] = mapped_column(ForeignKey("career_hypotheses.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    change_reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class CareerRecalibrationRun(Base):
    __tablename__ = "career_recalibration_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    career_match_id: Mapped[str | None] = mapped_column(ForeignKey("career_matches.id"), nullable=True, index=True)
    experiment_result_id: Mapped[str | None] = mapped_column(ForeignKey("career_experiment_results.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(40), default="completed", index=True)
    before_json: Mapped[dict] = mapped_column(JSON, default=dict)
    after_json: Mapped[dict] = mapped_column(JSON, default=dict)
    changed_recommendations_json: Mapped[list] = mapped_column(JSON, default=list)
    explanation: Mapped[str] = mapped_column(Text, default="")
    uncertainty_label: Mapped[str] = mapped_column(String(80), default="Additional evidence required")
    version: Mapped[str] = mapped_column(String(60), default="career-recalibration-v1")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class CareerRecalibrationFactor(Base):
    __tablename__ = "career_recalibration_factors"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("career_recalibration_runs.id"), index=True)
    factor_type: Mapped[str] = mapped_column(String(80), index=True)
    label: Mapped[str] = mapped_column(String(160), default="")
    before_value: Mapped[float | None] = mapped_column(Float)
    after_value: Mapped[float | None] = mapped_column(Float)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    explanation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class SupportedPathRun(Base):
    __tablename__ = "supported_path_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    market_snapshot_id: Mapped[str | None] = mapped_column(ForeignKey("market_snapshots.id"), nullable=True, index=True)
    support_screening_id: Mapped[str | None] = mapped_column(ForeignKey("support_screenings.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(40), default="ready", index=True)
    version: Mapped[str] = mapped_column(String(60), default="supported-path-v1")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class SupportedPathResult(Base):
    __tablename__ = "supported_path_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("supported_path_runs.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    career_match_id: Mapped[str | None] = mapped_column(ForeignKey("career_matches.id"), nullable=True, index=True)
    role_family: Mapped[str] = mapped_column(String(160), default="", index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    personal_fit_label: Mapped[str] = mapped_column(String(80), default="Moderate")
    capability_fit_label: Mapped[str] = mapped_column(String(80), default="Moderate")
    market_fit_label: Mapped[str] = mapped_column(String(80), default="Additional information required")
    support_fit_label: Mapped[str] = mapped_column(String(80), default="Additional information required")
    transition_difficulty: Mapped[str] = mapped_column(String(80), default="moderate")
    estimated_preparation_range: Mapped[str] = mapped_column(String(80), default="3-6 months")
    main_strengths_json: Mapped[list] = mapped_column(JSON, default=list)
    main_gaps_json: Mapped[list] = mapped_column(JSON, default=list)
    main_uncertainties_json: Mapped[list] = mapped_column(JSON, default=list)
    required_experiment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    required_experiment_title: Mapped[str] = mapped_column(String(255), default="")
    possible_public_support_json: Mapped[list] = mapped_column(JSON, default=list)
    next_best_action: Mapped[str] = mapped_column(Text, default="")
    official_assessment_required: Mapped[bool] = mapped_column(Boolean, default=True)
    factor_scores_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    country: Mapped[str] = mapped_column(String(80), default="Norway", index=True)
    region: Mapped[str] = mapped_column(String(120), default="National", index=True)
    source_type: Mapped[str] = mapped_column(String(60), default="demo_curated_snapshot")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    snapshot_date: Mapped[str] = mapped_column(String(40), default="2026-07-21")
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)
    version: Mapped[str] = mapped_column(String(60), default="market-snapshot-no-demo-v1")
    source_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    last_checked_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class MarketRoleSignal(Base):
    __tablename__ = "market_role_signals"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    snapshot_id: Mapped[str] = mapped_column(ForeignKey("market_snapshots.id"), index=True)
    role_family: Mapped[str] = mapped_column(String(160), index=True)
    opportunity_count: Mapped[int] = mapped_column(Integer, default=0)
    geography_json: Mapped[list] = mapped_column(JSON, default=list)
    work_modes_json: Mapped[list] = mapped_column(JSON, default=list)
    language_requirements_json: Mapped[list] = mapped_column(JSON, default=list)
    recurring_skills_json: Mapped[list] = mapped_column(JSON, default=list)
    experience_level: Mapped[str] = mapped_column(String(80), default="mixed")
    emerging_requirements_json: Mapped[list] = mapped_column(JSON, default=list)
    posting_recency_label: Mapped[str] = mapped_column(String(80), default="demo snapshot")
    demand_direction: Mapped[str] = mapped_column(String(80), default="stable")
    limitations_json: Mapped[list] = mapped_column(JSON, default=list)


class SupportProgramme(Base):
    __tablename__ = "support_programmes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    authority: Mapped[str] = mapped_column(String(120), default="NAV", index=True)
    jurisdiction: Mapped[str] = mapped_column(String(80), default="Norway", index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    current_rule_version: Mapped[str] = mapped_column(String(80), default="support-rule-no-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class SupportProgrammeVersion(Base):
    __tablename__ = "support_programme_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    programme_id: Mapped[str] = mapped_column(ForeignKey("support_programmes.id"), index=True)
    norwegian_name: Mapped[str] = mapped_column(String(255), nullable=False)
    english_name: Mapped[str] = mapped_column(String(255), nullable=False)
    authority: Mapped[str] = mapped_column(String(120), default="NAV")
    jurisdiction: Mapped[str] = mapped_column(String(80), default="Norway")
    official_url: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    target_group: Mapped[str] = mapped_column(Text, default="")
    known_conditions_json: Mapped[list] = mapped_column(JSON, default=list)
    required_information_json: Mapped[list] = mapped_column(JSON, default=list)
    application_or_contact_route: Mapped[str] = mapped_column(Text, default="")
    documents_json: Mapped[list] = mapped_column(JSON, default=list)
    deadlines_json: Mapped[list] = mapped_column(JSON, default=list)
    incompatibilities_json: Mapped[list] = mapped_column(JSON, default=list)
    source_publication_date: Mapped[str] = mapped_column(String(40), default="")
    last_checked_date: Mapped[str] = mapped_column(String(40), default="2026-07-21")
    rule_version: Mapped[str] = mapped_column(String(80), default="support-rule-no-v1")
    verification_status: Mapped[str] = mapped_column(String(80), default="official_source_checked")
    human_assessment_required: Mapped[bool] = mapped_column(Boolean, default=True)
    limitations_json: Mapped[list] = mapped_column(JSON, default=list)
    categories_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class SupportRule(Base):
    __tablename__ = "support_rules"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    programme_id: Mapped[str] = mapped_column(ForeignKey("support_programmes.id"), index=True)
    programme_version_id: Mapped[str] = mapped_column(ForeignKey("support_programme_versions.id"), index=True)
    rule_version: Mapped[str] = mapped_column(String(80), default="support-rule-no-v1", index=True)
    conditions_json: Mapped[list] = mapped_column(JSON, default=list)
    missing_information_fields_json: Mapped[list] = mapped_column(JSON, default=list)
    relevance_logic_json: Mapped[dict] = mapped_column(JSON, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class SupportScreening(Base):
    __tablename__ = "support_screenings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    job_loss_profile_id: Mapped[str | None] = mapped_column(ForeignKey("job_loss_profiles.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(40), default="preliminary", index=True)
    country: Mapped[str] = mapped_column(String(80), default="Norway", index=True)
    input_values_json: Mapped[dict] = mapped_column(JSON, default=dict)
    unknown_fields_json: Mapped[list] = mapped_column(JSON, default=list)
    preliminary_result_json: Mapped[dict] = mapped_column(JSON, default=dict)
    source_references_json: Mapped[list] = mapped_column(JSON, default=list)
    rule_version: Mapped[str] = mapped_column(String(80), default="support-rule-no-v1")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class SupportScreeningFactor(Base):
    __tablename__ = "support_screening_factors"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    screening_id: Mapped[str] = mapped_column(ForeignKey("support_screenings.id"), index=True)
    programme_id: Mapped[str] = mapped_column(ForeignKey("support_programmes.id"), index=True)
    input_values_json: Mapped[dict] = mapped_column(JSON, default=dict)
    unknown_fields_json: Mapped[list] = mapped_column(JSON, default=list)
    preliminary_label: Mapped[str] = mapped_column(String(80), default="Additional information required", index=True)
    explanation: Mapped[str] = mapped_column(Text, default="")
    source_references_json: Mapped[list] = mapped_column(JSON, default=list)
    last_checked_date: Mapped[str] = mapped_column(String(40), default="2026-07-21")
    rule_version: Mapped[str] = mapped_column(String(80), default="support-rule-no-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class JobLossProfile(Base):
    __tablename__ = "job_loss_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    consent_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    country_of_residence: Mapped[str] = mapped_column(String(80), default="")
    country_of_employment: Mapped[str] = mapped_column(String(80), default="")
    municipality_or_region: Mapped[str] = mapped_column(String(160), default="")
    last_working_date: Mapped[str | None] = mapped_column(String(40))
    contract_termination_type: Mapped[str] = mapped_column(String(80), default="")
    employment_status: Mapped[str] = mapped_column(String(80), default="")
    reduction_in_working_hours: Mapped[int | None] = mapped_column(Integer)
    jobseeker_registration_status: Mapped[str] = mapped_column(String(80), default="")
    current_benefits_json: Mapped[list] = mapped_column(JSON, default=list)
    work_permit_or_residency_status: Mapped[str] = mapped_column(String(120), default="")
    education: Mapped[str] = mapped_column(Text, default="")
    training_interest: Mapped[str] = mapped_column(String(120), default="")
    availability_for_work: Mapped[str] = mapped_column(String(120), default="")
    relocation_preferences: Mapped[str] = mapped_column(Text, default="")
    sensitive_explanations_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class ImmediateActionPlan(Base):
    __tablename__ = "immediate_action_plans"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    job_loss_profile_id: Mapped[str | None] = mapped_column(ForeignKey("job_loss_profiles.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)
    version: Mapped[str] = mapped_column(String(60), default="immediate-action-plan-no-v1")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class ImmediateActionItem(Base):
    __tablename__ = "immediate_action_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    plan_id: Mapped[str] = mapped_column(ForeignKey("immediate_action_plans.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="")
    urgency: Mapped[str] = mapped_column(String(80), default="high", index=True)
    official_source_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(40), default="not_started", index=True)
    due_date: Mapped[str | None] = mapped_column(String(40))
    user_confirmation: Mapped[bool] = mapped_column(Boolean, default=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class SupportApplicationBrief(Base):
    __tablename__ = "support_application_briefs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    job_loss_profile_id: Mapped[str | None] = mapped_column(ForeignKey("job_loss_profiles.id"), nullable=True, index=True)
    support_screening_id: Mapped[str | None] = mapped_column(ForeignKey("support_screenings.id"), nullable=True, index=True)
    supported_path_run_id: Mapped[str | None] = mapped_column(ForeignKey("supported_path_runs.id"), nullable=True, index=True)
    content_json: Mapped[dict] = mapped_column(JSON, default=dict)
    disclaimer: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="draft", index=True)
    official_source_references_json: Mapped[list] = mapped_column(JSON, default=list)
    unresolved_questions_json: Mapped[list] = mapped_column(JSON, default=list)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class SupportOpportunityLink(Base):
    __tablename__ = "support_opportunity_links"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), index=True)
    source_id: Mapped[str] = mapped_column(String, index=True)
    target_type: Mapped[str] = mapped_column(String(80), index=True)
    target_id: Mapped[str] = mapped_column(String, index=True)
    relationship: Mapped[str] = mapped_column(String(160), default="")
    explanation: Mapped[str] = mapped_column(Text, default="")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)

