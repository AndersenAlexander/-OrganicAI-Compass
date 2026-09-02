import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utc_now_naive
from app.database import Base


def new_id() -> str:
    return str(uuid.uuid4())


class LabourMarketProviderRecord(Base):
    __tablename__ = "labour_market_providers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    provider_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(60), default="demo")
    base_url: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    configured: Mapped[bool] = mapped_column(Boolean, default=False)
    reachable: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(60), default="disabled", index=True)
    degraded_reason: Mapped[str] = mapped_column(Text, default="")
    last_successful_fetch: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    freshness_timestamp: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    error_state: Mapped[str] = mapped_column(Text, default="")
    fallback_state: Mapped[str] = mapped_column(String(60), default="none")
    coverage_notes: Mapped[str] = mapped_column(Text, default="")
    documentation_url: Mapped[str] = mapped_column(Text, default="")
    documentation_checked_date: Mapped[str] = mapped_column(String(40), default="2026-07-21")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class LabourMarketSyncCursor(Base):
    __tablename__ = "labour_market_sync_cursors"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    provider_id: Mapped[str] = mapped_column(ForeignKey("labour_market_providers.id"), index=True)
    cursor_key: Mapped[str] = mapped_column(String(120), default="default", index=True)
    next_url: Mapped[str | None] = mapped_column(Text)
    next_id: Mapped[str | None] = mapped_column(String(255))
    etag: Mapped[str | None] = mapped_column(String(255))
    last_modified: Mapped[str | None] = mapped_column(String(255))
    latest_event_timestamp: Mapped[datetime | None] = mapped_column(DateTime)
    cursor_status: Mapped[str] = mapped_column(String(60), default="not_started", index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class LabourMarketSyncRun(Base):
    __tablename__ = "labour_market_sync_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    provider_id: Mapped[str] = mapped_column(ForeignKey("labour_market_providers.id"), index=True)
    status: Mapped[str] = mapped_column(String(60), default="started", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    fetched_count: Mapped[int] = mapped_column(Integer, default=0)
    created_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, default=0)
    inactive_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    error_json: Mapped[list] = mapped_column(JSON, default=list)
    cursor_before_json: Mapped[dict] = mapped_column(JSON, default=dict)
    cursor_after_json: Mapped[dict] = mapped_column(JSON, default=dict)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class JobPosting(Base):
    __tablename__ = "job_postings"
    __table_args__ = (UniqueConstraint("provider", "external_job_id", name="uq_job_provider_external"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    provider: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    external_job_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(Text, default="")
    provider_event_id: Mapped[str | None] = mapped_column(String(255), index=True)
    event_type: Mapped[str] = mapped_column(String(80), default="upsert", index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    employer: Mapped[str] = mapped_column(String(255), default="", index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    publication_time: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    expiry_time: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    last_provider_update: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    inactive_reason: Mapped[str] = mapped_column(String(120), default="")
    employment_type: Mapped[str] = mapped_column(String(120), default="")
    full_time_part_time: Mapped[str] = mapped_column(String(80), default="")
    work_mode: Mapped[str] = mapped_column(String(80), default="unspecified", index=True)
    country: Mapped[str] = mapped_column(String(80), default="Norway", index=True)
    county: Mapped[str] = mapped_column(String(120), default="", index=True)
    municipality: Mapped[str] = mapped_column(String(120), default="", index=True)
    city: Mapped[str] = mapped_column(String(120), default="", index=True)
    coordinates_json: Mapped[dict] = mapped_column(JSON, default=dict)
    language_requirements_json: Mapped[list] = mapped_column(JSON, default=list)
    experience_requirements_json: Mapped[list] = mapped_column(JSON, default=list)
    education_requirements_json: Mapped[list] = mapped_column(JSON, default=list)
    occupation_classifications_json: Mapped[list] = mapped_column(JSON, default=list)
    esco_classifications_json: Mapped[list] = mapped_column(JSON, default=list)
    styrk_classifications_json: Mapped[list] = mapped_column(JSON, default=list)
    extracted_skills_json: Mapped[list] = mapped_column(JSON, default=list)
    career_families_json: Mapped[list] = mapped_column(JSON, default=list)
    original_provider_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, index=True)
    source_version: Mapped[str] = mapped_column(String(80), default="demo-labour-market-v1")
    content_hash: Mapped[str] = mapped_column(String(128), default="", index=True)
    canonical_job_key: Mapped[str] = mapped_column(String(255), default="", index=True)
    source_provenance_json: Mapped[list] = mapped_column(JSON, default=list)
    historical_retention_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class JobPostingVersion(Base):
    __tablename__ = "job_posting_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    job_id: Mapped[str] = mapped_column(ForeignKey("job_postings.id"), index=True)
    provider_event_id: Mapped[str | None] = mapped_column(String(255), index=True)
    event_type: Mapped[str] = mapped_column(String(80), default="upsert")
    content_hash: Mapped[str] = mapped_column(String(128), default="", index=True)
    snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class JobLocation(Base):
    __tablename__ = "job_locations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    job_id: Mapped[str] = mapped_column(ForeignKey("job_postings.id"), index=True)
    country: Mapped[str] = mapped_column(String(80), default="Norway", index=True)
    county: Mapped[str] = mapped_column(String(120), default="", index=True)
    municipality: Mapped[str] = mapped_column(String(120), default="", index=True)
    city: Mapped[str] = mapped_column(String(120), default="", index=True)
    postal_code_area: Mapped[str] = mapped_column(String(40), default="")
    coordinates_json: Mapped[dict] = mapped_column(JSON, default=dict)


class JobClassification(Base):
    __tablename__ = "job_classifications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    job_id: Mapped[str] = mapped_column(ForeignKey("job_postings.id"), index=True)
    classification_type: Mapped[str] = mapped_column(String(80), index=True)
    code: Mapped[str] = mapped_column(String(120), default="", index=True)
    label: Mapped[str] = mapped_column(String(255), default="")
    source: Mapped[str] = mapped_column(String(80), default="provider")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class JobSkillMention(Base):
    __tablename__ = "job_skill_mentions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    job_id: Mapped[str] = mapped_column(ForeignKey("job_postings.id"), index=True)
    original_phrase: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    normalised_skill_id: Mapped[str | None] = mapped_column(String(160), index=True)
    normalised_label: Mapped[str] = mapped_column(String(255), default="")
    esco_uri: Mapped[str | None] = mapped_column(Text)
    requirement_type: Mapped[str] = mapped_column(String(60), default="observed", index=True)
    confidence: Mapped[str] = mapped_column(String(60), default="medium")
    extraction_method: Mapped[str] = mapped_column(String(80), default="deterministic")
    source_excerpt: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class JobLanguageRequirement(Base):
    __tablename__ = "job_language_requirements"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    job_id: Mapped[str] = mapped_column(ForeignKey("job_postings.id"), index=True)
    language: Mapped[str] = mapped_column(String(80), index=True)
    level: Mapped[str] = mapped_column(String(80), default="")
    requirement_type: Mapped[str] = mapped_column(String(60), default="preferred", index=True)
    source_excerpt: Mapped[str] = mapped_column(Text, default="")


class MarketRadarPreference(Base):
    __tablename__ = "market_radar_preferences"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    country: Mapped[str] = mapped_column(String(80), default="Norway")
    county: Mapped[str] = mapped_column(String(120), default="")
    municipality: Mapped[str] = mapped_column(String(120), default="")
    commuting_area: Mapped[str] = mapped_column(String(160), default="")
    radius_km: Mapped[int | None] = mapped_column(Integer)
    work_modes_json: Mapped[list] = mapped_column(JSON, default=list)
    preferred_languages_json: Mapped[list] = mapped_column(JSON, default=list)
    employment_types_json: Mapped[list] = mapped_column(JSON, default=list)
    full_time_part_time_json: Mapped[list] = mapped_column(JSON, default=list)
    career_families_json: Mapped[list] = mapped_column(JSON, default=list)
    selected_hypothesis_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    minimum_publication_date: Mapped[str | None] = mapped_column(String(40))
    experience_level: Mapped[str] = mapped_column(String(80), default="")
    role_title: Mapped[str] = mapped_column(String(255), default="")
    excluded_employers_json: Mapped[list] = mapped_column(JSON, default=list)
    excluded_keywords_json: Mapped[list] = mapped_column(JSON, default=list)
    relocation_preference: Mapped[str] = mapped_column(String(120), default="")
    user_confirmed_storage: Mapped[bool] = mapped_column(Boolean, default=False)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class MarketSignalRun(Base):
    __tablename__ = "market_signal_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(80), default="demo")
    observation_window_days: Mapped[int] = mapped_column(Integer, default=30)
    comparison_window_days: Mapped[int] = mapped_column(Integer, default=30)
    status: Mapped[str] = mapped_column(String(60), default="ready", index=True)
    coverage_label: Mapped[str] = mapped_column(String(120), default="curated demo dataset")
    provider_status_json: Mapped[dict] = mapped_column(JSON, default=dict)
    source_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    source_window_start: Mapped[datetime | None] = mapped_column(DateTime)
    source_window_end: Mapped[datetime | None] = mapped_column(DateTime)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    coverage_sufficient: Mapped[bool] = mapped_column(Boolean, default=False)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class MarketSignalResult(Base):
    __tablename__ = "market_signal_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("market_signal_runs.id"), index=True)
    signal_type: Mapped[str] = mapped_column(String(80), index=True)
    label: Mapped[str] = mapped_column(String(255), index=True)
    trend_label: Mapped[str] = mapped_column(String(120), default="Insufficient data", index=True)
    observation_count: Mapped[int] = mapped_column(Integer, default=0)
    comparison_count: Mapped[int] = mapped_column(Integer, default=0)
    confidence_label: Mapped[str] = mapped_column(String(120), default="Limited")
    limitations_json: Mapped[list] = mapped_column(JSON, default=list)
    factor_json: Mapped[dict] = mapped_column(JSON, default=dict)
    coverage_label: Mapped[str] = mapped_column(String(160), default="Insufficient coverage")
    source_window_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class EscoConcept(Base):
    __tablename__ = "esco_concepts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    esco_uri: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    preferred_label: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    concept_type: Mapped[str] = mapped_column(String(80), default="skill", index=True)
    taxonomy_version: Mapped[str] = mapped_column(String(80), default="ESCO unavailable/local")
    provider: Mapped[str] = mapped_column(String(80), default="local")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class EscoLabel(Base):
    __tablename__ = "esco_labels"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    concept_id: Mapped[str] = mapped_column(ForeignKey("esco_concepts.id"), index=True)
    language: Mapped[str] = mapped_column(String(20), default="en", index=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    label_type: Mapped[str] = mapped_column(String(60), default="preferred")


class EscoMapping(Base):
    __tablename__ = "esco_mappings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    original_phrase: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    normalised_phrase: Mapped[str] = mapped_column(String(255), default="", index=True)
    concept_id: Mapped[str | None] = mapped_column(ForeignKey("esco_concepts.id"), nullable=True, index=True)
    esco_uri: Mapped[str | None] = mapped_column(Text)
    preferred_label: Mapped[str] = mapped_column(String(255), default="")
    alternative_labels_json: Mapped[list] = mapped_column(JSON, default=list)
    concept_type: Mapped[str] = mapped_column(String(80), default="")
    taxonomy_version: Mapped[str] = mapped_column(String(80), default="")
    provider: Mapped[str] = mapped_column(String(80), default="disabled")
    confidence: Mapped[str] = mapped_column(String(60), default="unnormalised")
    status: Mapped[str] = mapped_column(String(60), default="fallback_raw_term", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class SkillNormalisationRun(Base):
    __tablename__ = "skill_normalisation_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    provider: Mapped[str] = mapped_column(String(80), default="disabled")
    status: Mapped[str] = mapped_column(String(60), default="completed", index=True)
    input_count: Mapped[int] = mapped_column(Integer, default=0)
    mapped_count: Mapped[int] = mapped_column(Integer, default=0)
    ambiguous_count: Mapped[int] = mapped_column(Integer, default=0)
    fallback_count: Mapped[int] = mapped_column(Integer, default=0)
    version: Mapped[str] = mapped_column(String(80), default="esco-normalisation-v1")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class JobAnalysis(Base):
    __tablename__ = "job_analyses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    job_id: Mapped[str | None] = mapped_column(ForeignKey("job_postings.id"), nullable=True, index=True)
    input_type: Mapped[str] = mapped_column(String(60), default="pasted_text", index=True)
    source_type: Mapped[str] = mapped_column(String(80), default="pasted_job_ad", index=True)
    source_url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(255), default="", index=True)
    organisation: Mapped[str] = mapped_column(String(255), default="")
    location: Mapped[str] = mapped_column(String(255), default="")
    deadline: Mapped[str | None] = mapped_column(String(80))
    raw_text_excerpt: Mapped[str] = mapped_column(Text, default="")
    source_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    user_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime)
    structured_output_json: Mapped[dict] = mapped_column(JSON, default=dict)
    uncertainties_json: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(60), default="analysed", index=True)
    extraction_version: Mapped[str] = mapped_column(String(80), default="job-analysis-v1")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class JobAnalysisVersion(Base):
    __tablename__ = "job_analysis_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("job_analyses.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    change_reason: Mapped[str] = mapped_column(Text, default="")
    version_kind: Mapped[str] = mapped_column(String(60), default="extraction")
    edited_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("job_analyses.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    requirement_text: Mapped[str] = mapped_column(Text, nullable=False)
    requirement_category: Mapped[str] = mapped_column(String(80), default="skills", index=True)
    requirement_type: Mapped[str] = mapped_column(String(60), default="preferred", index=True)
    extracted_requirement_type: Mapped[str] = mapped_column(String(60), default="unclear")
    extracted_requirement_category: Mapped[str] = mapped_column(String(80), default="skills")
    source_excerpt: Mapped[str] = mapped_column(Text, default="")
    source_location: Mapped[str] = mapped_column(String(160), default="")
    extraction_method: Mapped[str] = mapped_column(String(80), default="deterministic")
    confidence: Mapped[str] = mapped_column(String(60), default="medium")
    user_confirmation_state: Mapped[str] = mapped_column(String(60), default="needs_review", index=True)
    user_edited: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime)
    confirmed_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    confirmation_action: Mapped[str] = mapped_column(String(60), default="pending_review")
    extraction_timestamp: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    job_analysis_version: Mapped[str] = mapped_column(String(80), default="job-analysis-v1")
    normalised_skill_id: Mapped[str | None] = mapped_column(String(160), index=True)
    esco_uri: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(60), default="active", index=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class JobRequirementEvidenceMatch(Base):
    __tablename__ = "job_requirement_evidence_matches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    requirement_id: Mapped[str] = mapped_column(ForeignKey("job_requirements.id"), index=True)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("job_analyses.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    evidence_id: Mapped[str | None] = mapped_column(ForeignKey("skill_evidence.id"), nullable=True, index=True)
    evidence_type: Mapped[str] = mapped_column(String(80), default="")
    evidence_strength: Mapped[str] = mapped_column(String(80), default="Missing evidence", index=True)
    evidence_status: Mapped[str] = mapped_column(String(40), default="NOT ASSESSED", index=True)
    match_category: Mapped[str] = mapped_column(String(80), default="Missing evidence", index=True)
    recency_label: Mapped[str] = mapped_column(String(80), default="Unknown")
    gap: Mapped[str] = mapped_column(Text, default="")
    transferable_evidence_json: Mapped[list] = mapped_column(JSON, default=list)
    recommended_action: Mapped[str] = mapped_column(Text, default="")
    deterministic_reason: Mapped[str] = mapped_column(Text, default="")
    user_confirmation_state: Mapped[str] = mapped_column(String(60), default="needs_review")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class JobAnalysisCorrection(Base):
    __tablename__ = "job_analysis_corrections"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("job_analyses.id"), index=True)
    requirement_id: Mapped[str | None] = mapped_column(ForeignKey("job_requirements.id"), nullable=True, index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    correction_type: Mapped[str] = mapped_column(String(80), default="edit")
    before_json: Mapped[dict] = mapped_column(JSON, default=dict)
    after_json: Mapped[dict] = mapped_column(JSON, default=dict)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class JobReadinessResult(Base):
    __tablename__ = "job_readiness_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("job_analyses.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    readiness_label: Mapped[str] = mapped_column(String(80), default="Insufficient information", index=True)
    reasons_json: Mapped[list] = mapped_column(JSON, default=list)
    blockers_json: Mapped[list] = mapped_column(JSON, default=list)
    recommended_actions_json: Mapped[list] = mapped_column(JSON, default=list)
    supported_count: Mapped[int] = mapped_column(Integer, default=0)
    partial_count: Mapped[int] = mapped_column(Integer, default=0)
    missing_count: Mapped[int] = mapped_column(Integer, default=0)
    outdated_count: Mapped[int] = mapped_column(Integer, default=0)
    unknown_count: Mapped[int] = mapped_column(Integer, default=0)
    unsupported_claims_risk_json: Mapped[list] = mapped_column(JSON, default=list)
    source_limitations_json: Mapped[list] = mapped_column(JSON, default=list)
    formula_version: Mapped[str] = mapped_column(String(80), default="job-readiness-v2")
    deterministic_version: Mapped[str] = mapped_column(String(80), default="job-readiness-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class MasterCareerProfile(Base):
    __tablename__ = "master_career_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(60), default="draft", index=True)
    professional_summary: Mapped[str] = mapped_column(Text, default="")
    language_profile_json: Mapped[list] = mapped_column(JSON, default=list)
    portfolio_links_json: Mapped[list] = mapped_column(JSON, default=list)
    source_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    version: Mapped[str] = mapped_column(String(80), default="master-career-profile-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class CareerProfileEntry(Base):
    __tablename__ = "career_profile_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    master_profile_id: Mapped[str] = mapped_column(ForeignKey("master_career_profiles.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    entry_type: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    start_date: Mapped[str | None] = mapped_column(String(40))
    end_date: Mapped[str | None] = mapped_column(String(40))
    origin: Mapped[str] = mapped_column(String(80), default="profile")
    source_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    user_confirmation_state: Mapped[str] = mapped_column(String(60), default="needs_review", index=True)
    last_update: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    evidence_relationship_json: Mapped[list] = mapped_column(JSON, default=list)
    inclusion_permission: Mapped[str] = mapped_column(String(80), default="requires_confirmation")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class ApplicationDocument(Base):
    __tablename__ = "application_documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    job_analysis_id: Mapped[str | None] = mapped_column(ForeignKey("job_analyses.id"), nullable=True, index=True)
    job_application_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    document_type: Mapped[str] = mapped_column(String(60), default="cv", index=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    language: Mapped[str] = mapped_column(String(40), default="en")
    variant: Mapped[str] = mapped_column(String(80), default="concise")
    status: Mapped[str] = mapped_column(String(60), default="draft", index=True)
    evidence_lock_status: Mapped[str] = mapped_column(String(80), default="needs_review", index=True)
    readiness_status: Mapped[str] = mapped_column(String(80), default="Draft", index=True)
    source_profile_version: Mapped[str] = mapped_column(String(100), default="profile-current")
    source_job_analysis_version: Mapped[str] = mapped_column(String(100), default="")
    source_evidence_version: Mapped[str] = mapped_column(String(100), default="evidence-passport-v1")
    user_edited_at: Mapped[datetime | None] = mapped_column(DateTime)
    export_warning_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    source_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    version: Mapped[str] = mapped_column(String(80), default="application-document-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class ApplicationDocumentVersion(Base):
    __tablename__ = "application_document_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("application_documents.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    warnings_json: Mapped[list] = mapped_column(JSON, default=list)
    version_kind: Mapped[str] = mapped_column(String(60), default="generated")
    source_profile_version: Mapped[str] = mapped_column(String(100), default="profile-current")
    source_job_analysis_version: Mapped[str] = mapped_column(String(100), default="")
    source_evidence_version: Mapped[str] = mapped_column(String(100), default="evidence-passport-v1")
    evidence_lock_state: Mapped[str] = mapped_column(String(80), default="needs_review")
    edited_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class DocumentSection(Base):
    __tablename__ = "document_sections"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("application_documents.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    section_type: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    include_in_export: Mapped[bool] = mapped_column(Boolean, default=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class DocumentClaim(Base):
    __tablename__ = "document_claims"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("application_documents.id"), index=True)
    section_id: Mapped[str | None] = mapped_column(ForeignKey("document_sections.id"), nullable=True, index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(80), default="skill", index=True)
    status: Mapped[str] = mapped_column(String(80), default="Unverified", index=True)
    support_state: Mapped[str] = mapped_column(String(40), default="NEEDS_REVIEW", index=True)
    generated_by: Mapped[str] = mapped_column(String(80), default="deterministic_template")
    edited_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    claim_version: Mapped[int] = mapped_column(Integer, default=1)
    safer_alternative: Mapped[str] = mapped_column(Text, default="")
    deterministic_reason: Mapped[str] = mapped_column(Text, default="")
    user_confirmation_state: Mapped[str] = mapped_column(String(60), default="needs_review", index=True)
    blocked_for_export: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    source_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class DocumentClaimEvidenceLink(Base):
    __tablename__ = "document_claim_evidence_links"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    claim_id: Mapped[str] = mapped_column(ForeignKey("document_claims.id"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("application_documents.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(80), default="skill_evidence", index=True)
    evidence_id: Mapped[str | None] = mapped_column(ForeignKey("skill_evidence.id"), nullable=True, index=True)
    source_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    relationship: Mapped[str] = mapped_column(String(120), default="supports")
    confidence: Mapped[str] = mapped_column(String(80), default="Limited evidence")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class DocumentReviewEvent(Base):
    __tablename__ = "document_review_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("application_documents.id"), index=True)
    claim_id: Mapped[str | None] = mapped_column(ForeignKey("document_claims.id"), nullable=True, index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), default="review")
    event_json: Mapped[dict] = mapped_column(JSON, default=dict)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class JobApplication(Base):
    __tablename__ = "job_applications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    job_id: Mapped[str | None] = mapped_column(ForeignKey("job_postings.id"), nullable=True, index=True)
    job_analysis_id: Mapped[str | None] = mapped_column(ForeignKey("job_analyses.id"), nullable=True, index=True)
    career_match_id: Mapped[str | None] = mapped_column(ForeignKey("career_matches.id"), nullable=True, index=True)
    cv_document_id: Mapped[str | None] = mapped_column(ForeignKey("application_documents.id"), nullable=True, index=True)
    cover_letter_document_id: Mapped[str | None] = mapped_column(ForeignKey("application_documents.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), default="", index=True)
    organisation: Mapped[str] = mapped_column(String(255), default="")
    source: Mapped[str] = mapped_column(String(120), default="demo")
    application_date: Mapped[str | None] = mapped_column(String(40))
    deadline: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(80), default="Saved", index=True)
    contacts_json: Mapped[list] = mapped_column(JSON, default=list)
    notes: Mapped[str] = mapped_column(Text, default="")
    next_action: Mapped[str] = mapped_column(Text, default="")
    confirmed_job_analysis_version: Mapped[str] = mapped_column(String(100), default="")
    readiness_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    evidence_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    roadmap_action_id: Mapped[str | None] = mapped_column(ForeignKey("roadmap_actions.id"), nullable=True, index=True)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    version: Mapped[str] = mapped_column(String(80), default="job-application-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class JobApplicationEvent(Base):
    __tablename__ = "job_application_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    application_id: Mapped[str] = mapped_column(ForeignKey("job_applications.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), default="status_change", index=True)
    from_status: Mapped[str] = mapped_column(String(80), default="")
    to_status: Mapped[str] = mapped_column(String(80), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    event_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class ApplicationStageRecord(Base):
    __tablename__ = "application_stage_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    application_id: Mapped[str] = mapped_column(ForeignKey("job_applications.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    stage_type: Mapped[str] = mapped_column(String(80), index=True)
    scheduled_date: Mapped[str | None] = mapped_column(String(80))
    preparation_notes: Mapped[str] = mapped_column(Text, default="")
    probable_questions_json: Mapped[list] = mapped_column(JSON, default=list)
    selected_evidence_json: Mapped[list] = mapped_column(JSON, default=list)
    user_reflection: Mapped[str] = mapped_column(Text, default="")
    result: Mapped[str] = mapped_column(String(80), default="", index=True)
    feedback: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class ApplicationContact(Base):
    __tablename__ = "application_contacts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    application_id: Mapped[str] = mapped_column(ForeignKey("job_applications.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[str] = mapped_column(String(255), default="")
    contact_method: Mapped[str] = mapped_column(String(120), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class ApplicationOutcome(Base):
    __tablename__ = "application_outcomes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    application_id: Mapped[str] = mapped_column(ForeignKey("job_applications.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    outcome: Mapped[str] = mapped_column(String(80), default="Unknown", index=True)
    outcome_date: Mapped[str | None] = mapped_column(String(40))
    employer_feedback: Mapped[str] = mapped_column(Text, default="")
    feedback_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    user_interpretation: Mapped[str] = mapped_column(Text, default="")
    ai_interpretation: Mapped[str] = mapped_column(Text, default="")
    observed_data_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class ApplicationFeedback(Base):
    __tablename__ = "application_feedback"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    application_id: Mapped[str] = mapped_column(ForeignKey("job_applications.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    feedback_type: Mapped[str] = mapped_column(String(80), default="user_note", index=True)
    feedback_text: Mapped[str] = mapped_column(Text, default="")
    confirmed_source: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class ApplicationRecalibrationRun(Base):
    __tablename__ = "application_recalibration_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    application_id: Mapped[str | None] = mapped_column(ForeignKey("job_applications.id"), nullable=True, index=True)
    interview_id: Mapped[str | None] = mapped_column(ForeignKey("interviews.id"), nullable=True, index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(60), default="suggested", index=True)
    observed_data_json: Mapped[dict] = mapped_column(JSON, default=dict)
    user_interpretation_json: Mapped[dict] = mapped_column(JSON, default=dict)
    ai_interpretation_json: Mapped[dict] = mapped_column(JSON, default=dict)
    suggestions_json: Mapped[list] = mapped_column(JSON, default=list)
    roadmap_changes_require_confirmation: Mapped[bool] = mapped_column(Boolean, default=True)
    accepted_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    user_decision: Mapped[str] = mapped_column(String(40), default="PENDING", index=True)
    before_state_json: Mapped[dict] = mapped_column(JSON, default=dict)
    after_state_json: Mapped[dict] = mapped_column(JSON, default=dict)
    source_label: Mapped[str] = mapped_column(String(120), default="Interview reflection")
    limitation: Mapped[str] = mapped_column(Text, default="One interview outcome is limited evidence and does not determine career fit.")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    version: Mapped[str] = mapped_column(String(80), default="application-recalibration-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class ResearchStudy(Base):
    __tablename__ = "research_studies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    study_mode: Mapped[str] = mapped_column(String(80), default="experimental", index=True)
    status: Mapped[str] = mapped_column(String(60), default="draft", index=True)
    research_question: Mapped[str] = mapped_column(Text, default="")
    contribution_statement: Mapped[str] = mapped_column(Text, default="")
    consent_version: Mapped[str] = mapped_column(String(80), default="research-consent-v1")
    random_assignment_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class ResearchStudyVersion(Base):
    __tablename__ = "research_study_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    study_id: Mapped[str] = mapped_column(ForeignKey("research_studies.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    protocol_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class ResearchParticipant(Base):
    __tablename__ = "research_participants"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    study_id: Mapped[str] = mapped_column(ForeignKey("research_studies.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    pseudonymous_id: Mapped[str] = mapped_column(String(160), index=True)
    status: Mapped[str] = mapped_column(String(60), default="active", index=True)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class ResearchConsent(Base):
    __tablename__ = "research_consents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    study_id: Mapped[str] = mapped_column(ForeignKey("research_studies.id"), index=True)
    participant_id: Mapped[str] = mapped_column(ForeignKey("research_participants.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    consent_version: Mapped[str] = mapped_column(String(80), default="research-consent-v1")
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime)
    consent_text_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    study_id: Mapped[str] = mapped_column(ForeignKey("research_studies.id"), index=True)
    participant_id: Mapped[str] = mapped_column(ForeignKey("research_participants.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    workflow_stage: Mapped[str] = mapped_column(String(80), default="pre_test", index=True)
    status: Mapped[str] = mapped_column(String(60), default="in_progress", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class ResearchAssignment(Base):
    __tablename__ = "research_assignments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    study_id: Mapped[str] = mapped_column(ForeignKey("research_studies.id"), index=True)
    participant_id: Mapped[str] = mapped_column(ForeignKey("research_participants.id"), index=True)
    assignment_type: Mapped[str] = mapped_column(String(80), default="manual")
    workflow: Mapped[str] = mapped_column(String(80), default="experimental", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class ResearchQuestion(Base):
    __tablename__ = "research_questions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    study_id: Mapped[str] = mapped_column(ForeignKey("research_studies.id"), index=True)
    construct: Mapped[str] = mapped_column(String(120), index=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    scale_min: Mapped[int] = mapped_column(Integer, default=1)
    scale_max: Mapped[int] = mapped_column(Integer, default=5)
    scale_label: Mapped[str] = mapped_column(String(120), default="Likert")
    instrument_type: Mapped[str] = mapped_column(String(80), default="custom_likert", index=True)
    question_version: Mapped[str] = mapped_column(String(80), default="research-question-v1")
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class ResearchResponse(Base):
    __tablename__ = "research_responses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("research_sessions.id"), index=True)
    study_id: Mapped[str] = mapped_column(ForeignKey("research_studies.id"), index=True)
    participant_id: Mapped[str] = mapped_column(ForeignKey("research_participants.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    question_id: Mapped[str] = mapped_column(ForeignKey("research_questions.id"), index=True)
    workflow_stage: Mapped[str] = mapped_column(String(80), index=True)
    numeric_response: Mapped[float | None] = mapped_column(Float)
    text_response_redacted: Mapped[str] = mapped_column(Text, default="")
    response_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    question_version: Mapped[str] = mapped_column(String(80), default="research-question-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class ResearchInteractionMetric(Base):
    __tablename__ = "research_interaction_metrics"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("research_sessions.id"), index=True)
    study_id: Mapped[str] = mapped_column(ForeignKey("research_studies.id"), index=True)
    participant_id: Mapped[str] = mapped_column(ForeignKey("research_participants.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    metric_name: Mapped[str] = mapped_column(String(120), index=True)
    metric_value: Mapped[float] = mapped_column(Float, default=0)
    workflow_stage: Mapped[str] = mapped_column(String(80), default="")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    raw_text_excluded: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class ResearchExportRun(Base):
    __tablename__ = "research_export_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    study_id: Mapped[str] = mapped_column(ForeignKey("research_studies.id"), index=True)
    status: Mapped[str] = mapped_column(String(60), default="preview", index=True)
    export_format: Mapped[str] = mapped_column(String(40), default="json")
    schema_version: Mapped[str] = mapped_column(String(80), default="research-export-v1")
    study_version: Mapped[str] = mapped_column(String(80), default="research-study-v1")
    preview_json: Mapped[dict] = mapped_column(JSON, default=dict)
    exclusions_json: Mapped[list] = mapped_column(JSON, default=list)
    demo_records_excluded: Mapped[bool] = mapped_column(Boolean, default=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)

