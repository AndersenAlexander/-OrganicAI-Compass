"""provider operations

Revision ID: 0004_provider_operations
Revises: 0003_privacy_data_lifecycle
Create Date: 2026-07-28
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_provider_operations"
down_revision = "0003_privacy_data_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "provider_verification_runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("verification_type", sa.String(length=120), nullable=False),
        sa.Column("execution_mode", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False, server_default="started"),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("configuration_fingerprint", sa.String(length=128), nullable=True),
        sa.Column("result_summary_json", sa.JSON(), nullable=False),
        sa.Column("failure_code", sa.String(length=120), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("created_by_user_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_provider_verification_runs_provider", "provider_verification_runs", ["provider"])
    op.create_index("ix_provider_verification_runs_status", "provider_verification_runs", ["status"])
    op.create_index("ix_provider_verification_runs_started_at", "provider_verification_runs", ["started_at"])
    op.create_table(
        "email_delivery_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("message_type", sa.String(length=120), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("recipient_hash", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False, server_default="queued"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider_message_id_hash", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("failed_at", sa.DateTime(), nullable=True),
        sa.Column("failure_code", sa.String(length=120), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_delivery_events_user_id", "email_delivery_events", ["user_id"])
    op.create_index("ix_email_delivery_events_status", "email_delivery_events", ["status"])
    op.create_index("ix_email_delivery_events_message_type", "email_delivery_events", ["message_type"])
    op.create_table(
        "webhook_delivery_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("external_event_key_hash", sa.String(length=128), nullable=False),
        sa.Column("signature_valid", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("duplicate", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(length=80), nullable=False, server_default="received"),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("failure_code", sa.String(length=120), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "external_event_key_hash", name="uq_webhook_provider_event_hash"),
    )
    op.create_index("ix_webhook_delivery_events_provider", "webhook_delivery_events", ["provider"])
    op.create_index("ix_webhook_delivery_events_status", "webhook_delivery_events", ["status"])
    op.create_index("ix_webhook_delivery_events_received_at", "webhook_delivery_events", ["received_at"])
    op.create_table(
        "operational_job_runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("job_type", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False, server_default="started"),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("processed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("succeeded_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_summary_json", sa.JSON(), nullable=False),
        sa.Column("worker_id_hash", sa.String(length=128), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_operational_job_runs_job_type", "operational_job_runs", ["job_type"])
    op.create_index("ix_operational_job_runs_status", "operational_job_runs", ["status"])
    op.create_index("ix_operational_job_runs_started_at", "operational_job_runs", ["started_at"])


def downgrade() -> None:
    op.drop_index("ix_operational_job_runs_started_at", table_name="operational_job_runs")
    op.drop_index("ix_operational_job_runs_status", table_name="operational_job_runs")
    op.drop_index("ix_operational_job_runs_job_type", table_name="operational_job_runs")
    op.drop_table("operational_job_runs")
    op.drop_index("ix_webhook_delivery_events_received_at", table_name="webhook_delivery_events")
    op.drop_index("ix_webhook_delivery_events_status", table_name="webhook_delivery_events")
    op.drop_index("ix_webhook_delivery_events_provider", table_name="webhook_delivery_events")
    op.drop_table("webhook_delivery_events")
    op.drop_index("ix_email_delivery_events_message_type", table_name="email_delivery_events")
    op.drop_index("ix_email_delivery_events_status", table_name="email_delivery_events")
    op.drop_index("ix_email_delivery_events_user_id", table_name="email_delivery_events")
    op.drop_table("email_delivery_events")
    op.drop_index("ix_provider_verification_runs_started_at", table_name="provider_verification_runs")
    op.drop_index("ix_provider_verification_runs_status", table_name="provider_verification_runs")
    op.drop_index("ix_provider_verification_runs_provider", table_name="provider_verification_runs")
    op.drop_table("provider_verification_runs")
