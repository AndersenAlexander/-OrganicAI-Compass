"""privacy data lifecycle

Revision ID: 0003_privacy_data_lifecycle
Revises: 0002_auth_sessions_security
Create Date: 2026-07-27
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_privacy_data_lifecycle"
down_revision = "0002_auth_sessions_security"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "privacy_policy_versions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("version", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("effective_at", sa.DateTime(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("document_path", sa.String(length=512), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version", name="uq_privacy_policy_versions_version"),
    )
    op.create_table(
        "retention_policies",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("policy_key", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("retention_days", sa.Integer(), nullable=True),
        sa.Column("applies_to", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("policy_key", name="uq_retention_policies_policy_key"),
    )
    op.create_table(
        "user_privacy_settings",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("conversation_history_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("voice_transcript_history_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("voice_audio_storage_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("product_analytics_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("research_participation_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("personalization_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("service_email_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("marketing_email_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("current_policy_version_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["current_policy_version_id"], ["privacy_policy_versions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "privacy_consent_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("purpose_key", sa.String(length=120), nullable=False),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("policy_version_id", sa.String(), nullable=True),
        sa.Column("legal_basis_label", sa.String(length=120), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("session_id", sa.String(), nullable=True),
        sa.Column("ip_hash", sa.String(length=128), nullable=True),
        sa.Column("user_agent_hash", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["policy_version_id"], ["privacy_policy_versions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_privacy_consent_events_user_id", "privacy_consent_events", ["user_id"])
    op.create_index("ix_privacy_consent_events_purpose_key", "privacy_consent_events", ["purpose_key"])
    op.create_index("ix_privacy_consent_events_occurred_at", "privacy_consent_events", ["occurred_at"])
    op.create_table(
        "data_subject_requests",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("request_type", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False, server_default="queued"),
        sa.Column("scope_json", sa.JSON(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("processing_started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("failed_at", sa.DateTime(), nullable=True),
        sa.Column("failure_code", sa.String(length=120), nullable=True),
        sa.Column("result_summary_json", sa.JSON(), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_subject_requests_user_id", "data_subject_requests", ["user_id"])
    op.create_index("ix_data_subject_requests_status", "data_subject_requests", ["status"])
    op.create_index("ix_data_subject_requests_request_type", "data_subject_requests", ["request_type"])
    op.create_table(
        "data_lifecycle_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("request_id", sa.String(), nullable=True),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("resource_type", sa.String(length=120), nullable=True),
        sa.Column("resource_id_hash", sa.String(length=128), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["request_id"], ["data_subject_requests.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_lifecycle_events_user_id", "data_lifecycle_events", ["user_id"])
    op.create_index("ix_data_lifecycle_events_event_type", "data_lifecycle_events", ["event_type"])
    op.create_index("ix_data_lifecycle_events_occurred_at", "data_lifecycle_events", ["occurred_at"])
    op.create_table(
        "external_provider_records",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("object_type", sa.String(length=120), nullable=False),
        sa.Column("external_object_id_hash", sa.String(length=128), nullable=False),
        sa.Column("local_resource_type", sa.String(length=120), nullable=True),
        sa.Column("local_resource_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("retention_status", sa.String(length=80), nullable=False, server_default="unknown"),
        sa.Column("deletion_capability", sa.String(length=80), nullable=False, server_default="unknown"),
        sa.Column("deletion_requested_at", sa.DateTime(), nullable=True),
        sa.Column("deletion_completed_at", sa.DateTime(), nullable=True),
        sa.Column("last_error_code", sa.String(length=120), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_external_provider_records_user_id", "external_provider_records", ["user_id"])
    op.create_index("ix_external_provider_records_provider", "external_provider_records", ["provider"])
    op.create_index("ix_external_provider_records_local_resource", "external_provider_records", ["local_resource_type", "local_resource_id"])
    op.create_table(
        "privacy_export_artifacts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("request_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(length=60), nullable=False, server_default="ready"),
        sa.Column("format", sa.String(length=40), nullable=False, server_default="zip-json"),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("encryption_key_hash", sa.String(length=128), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=128), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("downloaded_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["request_id"], ["data_subject_requests.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "status", name="uq_privacy_export_user_status"),
    )
    op.create_index("ix_privacy_export_artifacts_user_id", "privacy_export_artifacts", ["user_id"])
    op.create_index("ix_privacy_export_artifacts_status", "privacy_export_artifacts", ["status"])
    op.create_table(
        "deletion_suppression_ledger",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("subject_type", sa.String(length=80), nullable=False),
        sa.Column("subject_hash", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("request_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("previous_entry_hash", sa.String(length=128), nullable=True),
        sa.Column("entry_hash", sa.String(length=128), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deletion_suppression_ledger_subject_hash", "deletion_suppression_ledger", ["subject_hash"])
    op.create_index("ix_deletion_suppression_ledger_created_at", "deletion_suppression_ledger", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_deletion_suppression_ledger_created_at", table_name="deletion_suppression_ledger")
    op.drop_index("ix_deletion_suppression_ledger_subject_hash", table_name="deletion_suppression_ledger")
    op.drop_table("deletion_suppression_ledger")
    op.drop_index("ix_privacy_export_artifacts_status", table_name="privacy_export_artifacts")
    op.drop_index("ix_privacy_export_artifacts_user_id", table_name="privacy_export_artifacts")
    op.drop_table("privacy_export_artifacts")
    op.drop_index("ix_external_provider_records_local_resource", table_name="external_provider_records")
    op.drop_index("ix_external_provider_records_provider", table_name="external_provider_records")
    op.drop_index("ix_external_provider_records_user_id", table_name="external_provider_records")
    op.drop_table("external_provider_records")
    op.drop_index("ix_data_lifecycle_events_occurred_at", table_name="data_lifecycle_events")
    op.drop_index("ix_data_lifecycle_events_event_type", table_name="data_lifecycle_events")
    op.drop_index("ix_data_lifecycle_events_user_id", table_name="data_lifecycle_events")
    op.drop_table("data_lifecycle_events")
    op.drop_index("ix_data_subject_requests_request_type", table_name="data_subject_requests")
    op.drop_index("ix_data_subject_requests_status", table_name="data_subject_requests")
    op.drop_index("ix_data_subject_requests_user_id", table_name="data_subject_requests")
    op.drop_table("data_subject_requests")
    op.drop_index("ix_privacy_consent_events_occurred_at", table_name="privacy_consent_events")
    op.drop_index("ix_privacy_consent_events_purpose_key", table_name="privacy_consent_events")
    op.drop_index("ix_privacy_consent_events_user_id", table_name="privacy_consent_events")
    op.drop_table("privacy_consent_events")
    op.drop_table("user_privacy_settings")
    op.drop_table("retention_policies")
    op.drop_table("privacy_policy_versions")
