import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utc_now_naive
from app.database import Base


def new_id() -> str:
    return str(uuid.uuid4())


class BrowserExtensionConnection(Base):
    __tablename__ = "browser_extension_connections"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(160), default="Save to OrganicAI Compass")
    status: Mapped[str] = mapped_column(String(60), default="active", index=True)
    permissions_json: Mapped[list] = mapped_column(JSON, default=list)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class BrowserJobCapture(Base):
    __tablename__ = "browser_job_captures"
    __table_args__ = (UniqueConstraint("profile_id", "source_url", "content_hash", name="uq_browser_capture_profile_url_hash"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    extension_connection_id: Mapped[str | None] = mapped_column(ForeignKey("browser_extension_connections.id"), nullable=True, index=True)
    job_analysis_id: Mapped[str | None] = mapped_column(ForeignKey("job_analyses.id"), nullable=True, index=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), default="BROWSER_CAPTURE", index=True)
    page_title: Mapped[str] = mapped_column(String(255), default="")
    detected_title: Mapped[str] = mapped_column(String(255), default="")
    detected_employer: Mapped[str] = mapped_column(String(255), default="")
    source_domain: Mapped[str] = mapped_column(String(255), default="", index=True)
    captured_text_raw: Mapped[str] = mapped_column(Text, default="")
    sanitised_text: Mapped[str] = mapped_column(Text, default="")
    confirmed_text: Mapped[str] = mapped_column(Text, default="")
    user_edited_text: Mapped[bool] = mapped_column(Boolean, default=False)
    selected_text: Mapped[str] = mapped_column(Text, default="")
    confirmed_fields_json: Mapped[dict] = mapped_column(JSON, default=dict)
    capture_method: Mapped[str] = mapped_column(String(120), default="user_triggered_browser_extension", index=True)
    requested_action: Mapped[str] = mapped_column(String(80), default="save", index=True)
    status: Mapped[str] = mapped_column(String(60), default="Captured", index=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime)
    analysis_version: Mapped[str] = mapped_column(String(80), default="not_analysed")
    content_hash: Mapped[str] = mapped_column(String(128), default="", index=True)
    quality_warnings_json: Mapped[list] = mapped_column(JSON, default=list)
    extension_version: Mapped[str] = mapped_column(String(80), default="unknown")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class AdvisorShare(Base):
    __tablename__ = "advisor_shares"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    adviser_display_name: Mapped[str] = mapped_column(String(160), default="")
    adviser_role: Mapped[str] = mapped_column(String(80), default="Other", index=True)
    purpose: Mapped[str] = mapped_column(Text, default="")
    permission_level: Mapped[str] = mapped_column(String(80), default="View only", index=True)
    permission_code: Mapped[str] = mapped_column(String(40), default="READ_ONLY", index=True)
    allowed_sections_json: Mapped[list] = mapped_column(JSON, default=list)
    excluded_sections_json: Mapped[list] = mapped_column(JSON, default=list)
    scope_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    allowed_actions_json: Mapped[list] = mapped_column(JSON, default=list)
    export_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(60), default="active", index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    max_access_attempts: Mapped[int] = mapped_column(Integer, default=20)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    access_attempts: Mapped[int] = mapped_column(Integer, default=0)
    optional_pin_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class AdvisorComment(Base):
    __tablename__ = "advisor_comments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    share_id: Mapped[str] = mapped_column(ForeignKey("advisor_shares.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    adviser_display_name: Mapped[str] = mapped_column(String(160), default="")
    adviser_role: Mapped[str] = mapped_column(String(80), default="Other", index=True)
    target_type: Mapped[str] = mapped_column(String(80), default="share", index=True)
    target_id: Mapped[str] = mapped_column(String, default="", index=True)
    target_version: Mapped[str] = mapped_column(String(120), default="")
    proposal_type: Mapped[str] = mapped_column(String(80), default="COMMENT", index=True)
    proposal_payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    suggestion_type: Mapped[str] = mapped_column(String(120), default="General comment", index=True)
    comment_text: Mapped[str] = mapped_column(Text, default="")
    evidence_validation: Mapped[str] = mapped_column(String(120), default="Recommendation only", index=True)
    supporting_reference: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(60), default="pending", index=True)
    user_response: Mapped[str] = mapped_column(Text, default="")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    provenance: Mapped[str] = mapped_column(String(80), default="human_adviser")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class CareerRoleProfile(Base):
    __tablename__ = "career_role_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    career_family: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    aliases_json: Mapped[list] = mapped_column(JSON, default=list)
    summary: Mapped[str] = mapped_column(Text, default="")
    profile_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(80), default="Curated", index=True)
    source_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    last_reviewed_date: Mapped[str] = mapped_column(String(40), default="2026-07-24")
    version: Mapped[str] = mapped_column(String(80), default="career-role-profile-v1")
    archived_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class CareerRoleProfileVersion(Base):
    __tablename__ = "career_role_profile_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    role_profile_id: Mapped[str] = mapped_column(ForeignKey("career_role_profiles.id"), index=True)
    slug: Mapped[str] = mapped_column(String(180), index=True)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    change_reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class CareerDecisionJournalEntry(Base):
    __tablename__ = "career_decision_journal_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    decision_type: Mapped[str] = mapped_column(String(80), default="career_direction", index=True)
    status: Mapped[str] = mapped_column(String(80), default="active", index=True)
    decision_summary: Mapped[str] = mapped_column(Text, default="")
    context: Mapped[str] = mapped_column(Text, default="")
    selected_option: Mapped[str] = mapped_column(String(255), default="")
    options_json: Mapped[list] = mapped_column(JSON, default=list)
    assumptions_json: Mapped[list] = mapped_column(JSON, default=list)
    uncertainty_json: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[str] = mapped_column(String(80), default="")
    reversibility: Mapped[str] = mapped_column(String(80), default="")
    evidence_links_json: Mapped[list] = mapped_column(JSON, default=list)
    source_attributions_json: Mapped[list] = mapped_column(JSON, default=list)
    system_suggestions_json: Mapped[list] = mapped_column(JSON, default=list)
    ai_explanations_json: Mapped[list] = mapped_column(JSON, default=list)
    evidence_observations_json: Mapped[list] = mapped_column(JSON, default=list)
    adviser_inputs_json: Mapped[list] = mapped_column(JSON, default=list)
    user_reasoning: Mapped[str] = mapped_column(Text, default="")
    adviser_comment_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    career_slug: Mapped[str | None] = mapped_column(String(180), nullable=True, index=True)
    linked_experiment_id: Mapped[str | None] = mapped_column(ForeignKey("career_experiment_sessions.id"), nullable=True, index=True)
    interview_id: Mapped[str | None] = mapped_column(ForeignKey("interviews.id"), nullable=True, index=True)
    job_analysis_id: Mapped[str | None] = mapped_column(ForeignKey("job_analyses.id"), nullable=True, index=True)
    application_id: Mapped[str | None] = mapped_column(ForeignKey("job_applications.id"), nullable=True, index=True)
    privacy_scope: Mapped[str] = mapped_column(String(80), default="private", index=True)
    review_date: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    outcome_status: Mapped[str] = mapped_column(String(80), default="", index=True)
    outcome_json: Mapped[dict] = mapped_column(JSON, default=dict)
    later_outcome: Mapped[str] = mapped_column(Text, default="")
    lessons_learned: Mapped[str] = mapped_column(Text, default="")
    reconsideration_reason: Mapped[str] = mapped_column(Text, default="")
    roadmap_mutation_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class CareerDecisionJournalVersion(Base):
    __tablename__ = "career_decision_journal_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    entry_id: Mapped[str] = mapped_column(ForeignKey("career_decision_journal_entries.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    change_reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class InnovationAuditEvent(Base):
    __tablename__ = "innovation_audit_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    actor_type: Mapped[str] = mapped_column(String(80), default="system", index=True)
    actor_id: Mapped[str] = mapped_column(String, default="", index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(80), default="", index=True)
    target_id: Mapped[str] = mapped_column(String, default="", index=True)
    event_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)

