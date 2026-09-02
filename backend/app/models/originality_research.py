import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utc_now_naive
from app.database import Base


def new_id() -> str:
    return str(uuid.uuid4())


class AdaptiveExperimentRun(Base):
    __tablename__ = "adaptive_experiment_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(60), default="completed", index=True)
    input_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    scoring_version: Mapped[str] = mapped_column(String(80), default="adaptive-evidence-gain-score-v1")
    weight_version: Mapped[str] = mapped_column(String(80), default="adaptive-evidence-gain-weights-v1")
    weights_json: Mapped[dict] = mapped_column(JSON, default=dict)
    source_versions_json: Mapped[dict] = mapped_column(JSON, default=dict)
    data_coverage_json: Mapped[dict] = mapped_column(JSON, default=dict)
    limitations_json: Mapped[list] = mapped_column(JSON, default=list)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class AdaptiveExperimentRecommendation(Base):
    __tablename__ = "adaptive_experiment_recommendations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("adaptive_experiment_runs.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    experiment_template_id: Mapped[str | None] = mapped_column(ForeignKey("career_experiment_templates.id"), nullable=True, index=True)
    career_experiment_session_id: Mapped[str | None] = mapped_column(ForeignKey("career_experiment_sessions.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    experiment_type: Mapped[str] = mapped_column(String(120), default="practical_portfolio_experiment")
    priority_band: Mapped[str] = mapped_column(String(80), default="Exploratory value", index=True)
    score_internal: Mapped[float] = mapped_column(Float, default=0)
    rank_position: Mapped[int] = mapped_column(Integer, default=1)
    related_hypotheses_json: Mapped[list] = mapped_column(JSON, default=list)
    uncertainty_json: Mapped[dict] = mapped_column(JSON, default=dict)
    skills_tested_json: Mapped[list] = mapped_column(JSON, default=list)
    evidence_expected_json: Mapped[list] = mapped_column(JSON, default=list)
    expected_evidence_gain_json: Mapped[dict] = mapped_column(JSON, default=dict)
    actual_evidence_gain_json: Mapped[dict] = mapped_column(JSON, default=dict)
    estimated_duration: Mapped[str] = mapped_column(String(80), default="")
    estimated_effort: Mapped[str] = mapped_column(String(80), default="")
    estimated_cost: Mapped[str] = mapped_column(String(80), default="")
    market_relevance: Mapped[str] = mapped_column(String(80), default="")
    cross_path_usefulness: Mapped[str] = mapped_column(String(80), default="")
    accessibility_considerations_json: Mapped[list] = mapped_column(JSON, default=list)
    support_options_json: Mapped[list] = mapped_column(JSON, default=list)
    limitations_json: Mapped[list] = mapped_column(JSON, default=list)
    score_components_json: Mapped[dict] = mapped_column(JSON, default=dict)
    alternatives_json: Mapped[list] = mapped_column(JSON, default=list)
    data_quality_warnings_json: Mapped[list] = mapped_column(JSON, default=list)
    explanation: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(60), default="proposed", index=True)
    user_confirmation_status: Mapped[str] = mapped_column(String(80), default="pending", index=True)
    rejection_reason: Mapped[str] = mapped_column(String(120), default="")
    rejection_feedback_json: Mapped[dict] = mapped_column(JSON, default=dict)
    roadmap_confirmation_status: Mapped[str] = mapped_column(String(80), default="not_requested")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class CareerTransitionSimulation(Base):
    __tablename__ = "career_transition_simulations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    scenario_name: Mapped[str] = mapped_column(String(180), default="Balanced transition", index=True)
    preset: Mapped[str] = mapped_column(String(120), default="balanced_transition", index=True)
    status: Mapped[str] = mapped_column(String(60), default="completed", index=True)
    controls_json: Mapped[dict] = mapped_column(JSON, default=dict)
    objective_config_json: Mapped[dict] = mapped_column(JSON, default=dict)
    input_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    pareto_front_json: Mapped[list] = mapped_column(JSON, default=list)
    scenario_comparisons_json: Mapped[list] = mapped_column(JSON, default=list)
    explanation: Mapped[str] = mapped_column(Text, default="")
    objective_version: Mapped[str] = mapped_column(String(80), default="career-transition-objectives-v1")
    source_versions_json: Mapped[dict] = mapped_column(JSON, default=dict)
    data_coverage_json: Mapped[dict] = mapped_column(JSON, default=dict)
    limitations_json: Mapped[list] = mapped_column(JSON, default=list)
    saved: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class CareerTransitionPath(Base):
    __tablename__ = "career_transition_paths"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    simulation_id: Mapped[str] = mapped_column(ForeignKey("career_transition_simulations.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role_slug: Mapped[str] = mapped_column(String(180), default="", index=True)
    path_type: Mapped[str] = mapped_column(String(120), default="adjacent_transition")
    objectives_json: Mapped[dict] = mapped_column(JSON, default=dict)
    normalised_objectives_json: Mapped[dict] = mapped_column(JSON, default=dict)
    objective_directions_json: Mapped[dict] = mapped_column(JSON, default=dict)
    is_pareto_optimal: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    dominated_by_json: Mapped[list] = mapped_column(JSON, default=list)
    dominated_explanation: Mapped[str] = mapped_column(Text, default="")
    existing_assets_json: Mapped[list] = mapped_column(JSON, default=list)
    missing_assets_json: Mapped[list] = mapped_column(JSON, default=list)
    required_experiments_json: Mapped[list] = mapped_column(JSON, default=list)
    required_learning_json: Mapped[list] = mapped_column(JSON, default=list)
    transition_stages_json: Mapped[list] = mapped_column(JSON, default=list)
    relevant_jobs_json: Mapped[list] = mapped_column(JSON, default=list)
    support_opportunities_json: Mapped[list] = mapped_column(JSON, default=list)
    assumptions_json: Mapped[list] = mapped_column(JSON, default=list)
    uncertainties_json: Mapped[list] = mapped_column(JSON, default=list)
    reversibility: Mapped[str] = mapped_column(String(80), default="")
    next_action: Mapped[str] = mapped_column(Text, default="")
    user_selection_status: Mapped[str] = mapped_column(String(80), default="not_selected")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class RecommendationRobustnessRun(Base):
    __tablename__ = "recommendation_robustness_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(60), default="completed", index=True)
    input_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    baseline_json: Mapped[list] = mapped_column(JSON, default=list)
    variations_json: Mapped[list] = mapped_column(JSON, default=list)
    stability_results_json: Mapped[list] = mapped_column(JSON, default=list)
    sensitivity_matrix_json: Mapped[list] = mapped_column(JSON, default=list)
    dependency_flags_json: Mapped[list] = mapped_column(JSON, default=list)
    metrics_json: Mapped[dict] = mapped_column(JSON, default=dict)
    data_coverage_json: Mapped[dict] = mapped_column(JSON, default=dict)
    limitations_json: Mapped[list] = mapped_column(JSON, default=list)
    scoring_version: Mapped[str] = mapped_column(String(80), default="recommendation-robustness-v1")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class FairnessAuditRun(Base):
    __tablename__ = "fairness_audit_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    status: Mapped[str] = mapped_column(String(80), default="completed", index=True)
    audit_type: Mapped[str] = mapped_column(String(120), default="synthetic_counterfactual_rules")
    synthetic_only: Mapped[bool] = mapped_column(Boolean, default=True)
    fixtures_json: Mapped[list] = mapped_column(JSON, default=list)
    results_json: Mapped[list] = mapped_column(JSON, default=list)
    summary_json: Mapped[dict] = mapped_column(JSON, default=dict)
    system_card_version: Mapped[str] = mapped_column(String(80), default="recommendation-system-card-v1")
    reproducibility_json: Mapped[dict] = mapped_column(JSON, default=dict)
    limitations_json: Mapped[list] = mapped_column(JSON, default=list)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class RecommendationSystemCardVersion(Base):
    __tablename__ = "recommendation_system_card_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    version: Mapped[str] = mapped_column(String(80), default="recommendation-system-card-v1", index=True)
    status: Mapped[str] = mapped_column(String(60), default="active", index=True)
    card_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class ResearchOriginalitySession(Base):
    __tablename__ = "research_originality_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    pseudonymous_id: Mapped[str] = mapped_column(String(120), default="", index=True)
    consent_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    assigned_condition: Mapped[str] = mapped_column(String(80), default="experimental", index=True)
    status: Mapped[str] = mapped_column(String(80), default="started", index=True)
    baseline_json: Mapped[dict] = mapped_column(JSON, default=dict)
    experimental_json: Mapped[dict] = mapped_column(JSON, default=dict)
    feedback_json: Mapped[dict] = mapped_column(JSON, default=dict)
    results_json: Mapped[dict] = mapped_column(JSON, default=dict)
    export_filter_json: Mapped[dict] = mapped_column(JSON, default=dict)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class OriginalityAuditEvent(Base):
    __tablename__ = "originality_audit_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    actor_type: Mapped[str] = mapped_column(String(80), default="system", index=True)
    actor_id: Mapped[str] = mapped_column(String, default="", index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(80), default="", index=True)
    target_id: Mapped[str] = mapped_column(String, default="", index=True)
    event_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)

