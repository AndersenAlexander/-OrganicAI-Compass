import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utc_now_naive
from app.database import Base


def _id() -> str:
    return str(uuid.uuid4())


class PrivacyPolicyVersion(Base):
    __tablename__ = "privacy_policy_versions"
    __table_args__ = (UniqueConstraint("version", name="uq_privacy_policy_versions_version"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    version: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    effective_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    document_path: Mapped[str] = mapped_column(String(512), nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)


class UserPrivacySettings(Base):
    __tablename__ = "user_privacy_settings"

    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    conversation_history_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", nullable=False)
    voice_transcript_history_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)
    voice_audio_storage_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)
    product_analytics_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)
    research_participation_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)
    personalization_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", nullable=False)
    service_email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", nullable=False)
    marketing_email_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)
    current_policy_version_id: Mapped[str | None] = mapped_column(String, ForeignKey("privacy_policy_versions.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive, nullable=False)

    user = relationship("User")
    current_policy_version = relationship("PrivacyPolicyVersion")


class PrivacyConsentEvent(Base):
    __tablename__ = "privacy_consent_events"
    __table_args__ = (
        Index("ix_privacy_consent_events_user_id", "user_id"),
        Index("ix_privacy_consent_events_purpose_key", "purpose_key"),
        Index("ix_privacy_consent_events_occurred_at", "occurred_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    purpose_key: Mapped[str] = mapped_column(String(120), nullable=False)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    policy_version_id: Mapped[str | None] = mapped_column(String, ForeignKey("privacy_policy_versions.id"), nullable=True)
    legal_basis_label: Mapped[str] = mapped_column(String(120), nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String, nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    user_agent_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class DataSubjectRequest(Base):
    __tablename__ = "data_subject_requests"
    __table_args__ = (
        Index("ix_data_subject_requests_user_id", "user_id"),
        Index("ix_data_subject_requests_status", "status"),
        Index("ix_data_subject_requests_request_type", "request_type"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    request_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(80), nullable=False, default="queued", server_default="queued")
    scope_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    result_summary_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)


class DataLifecycleEvent(Base):
    __tablename__ = "data_lifecycle_events"
    __table_args__ = (
        Index("ix_data_lifecycle_events_user_id", "user_id"),
        Index("ix_data_lifecycle_events_event_type", "event_type"),
        Index("ix_data_lifecycle_events_occurred_at", "occurred_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String, ForeignKey("data_subject_requests.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    resource_id_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class ExternalProviderRecord(Base):
    __tablename__ = "external_provider_records"
    __table_args__ = (
        Index("ix_external_provider_records_user_id", "user_id"),
        Index("ix_external_provider_records_provider", "provider"),
        Index("ix_external_provider_records_local_resource", "local_resource_type", "local_resource_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    object_type: Mapped[str] = mapped_column(String(120), nullable=False)
    external_object_id_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    local_resource_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    local_resource_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    retention_status: Mapped[str] = mapped_column(String(80), default="unknown", server_default="unknown", nullable=False)
    deletion_capability: Mapped[str] = mapped_column(String(80), default="unknown", server_default="unknown", nullable=False)
    deletion_requested_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deletion_completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class PrivacyExportArtifact(Base):
    __tablename__ = "privacy_export_artifacts"
    __table_args__ = (
        Index("ix_privacy_export_artifacts_user_id", "user_id"),
        Index("ix_privacy_export_artifacts_status", "status"),
        UniqueConstraint("user_id", "status", name="uq_privacy_export_user_status"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String, ForeignKey("data_subject_requests.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(60), default="ready", server_default="ready", nullable=False)
    format: Mapped[str] = mapped_column(String(40), default="zip-json", server_default="zip-json", nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    encryption_key_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    downloaded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class DeletionSuppressionLedgerEntry(Base):
    __tablename__ = "deletion_suppression_ledger"
    __table_args__ = (
        Index("ix_deletion_suppression_ledger_subject_hash", "subject_hash"),
        Index("ix_deletion_suppression_ledger_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    subject_type: Mapped[str] = mapped_column(String(80), nullable=False)
    subject_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    previous_entry_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    entry_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class RetentionPolicy(Base):
    __tablename__ = "retention_policies"
    __table_args__ = (UniqueConstraint("policy_key", name="uq_retention_policies_policy_key"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    policy_key: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    retention_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    applies_to: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(80), default="manual-review", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)

