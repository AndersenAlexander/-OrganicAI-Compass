import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utc_now_naive
from app.database import Base


def _id() -> str:
    return str(uuid.uuid4())


class ProviderVerificationRun(Base):
    __tablename__ = "provider_verification_runs"
    __table_args__ = (
        Index("ix_provider_verification_runs_provider", "provider"),
        Index("ix_provider_verification_runs_status", "status"),
        Index("ix_provider_verification_runs_started_at", "started_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    verification_type: Mapped[str] = mapped_column(String(120), nullable=False)
    execution_mode: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(80), nullable=False, default="started", server_default="started")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    configuration_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    result_summary_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_by_user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class EmailDeliveryEvent(Base):
    __tablename__ = "email_delivery_events"
    __table_args__ = (
        Index("ix_email_delivery_events_user_id", "user_id"),
        Index("ix_email_delivery_events_status", "status"),
        Index("ix_email_delivery_events_message_type", "message_type"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    message_type: Mapped[str] = mapped_column(String(120), nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    recipient_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(80), nullable=False, default="queued", server_default="queued")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    provider_message_id_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)


class WebhookDeliveryEvent(Base):
    __tablename__ = "webhook_delivery_events"
    __table_args__ = (
        UniqueConstraint("provider", "external_event_key_hash", name="uq_webhook_provider_event_hash"),
        Index("ix_webhook_delivery_events_provider", "provider"),
        Index("ix_webhook_delivery_events_status", "status"),
        Index("ix_webhook_delivery_events_received_at", "received_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    external_event_key_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    signature_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    duplicate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    status: Mapped[str] = mapped_column(String(80), nullable=False, default="received", server_default="received")
    received_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)


class OperationalJobRun(Base):
    __tablename__ = "operational_job_runs"
    __table_args__ = (
        Index("ix_operational_job_runs_job_type", "job_type"),
        Index("ix_operational_job_runs_status", "status"),
        Index("ix_operational_job_runs_started_at", "started_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    job_type: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(80), nullable=False, default="started", server_default="started")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    processed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    succeeded_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    failure_summary_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    worker_id_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

