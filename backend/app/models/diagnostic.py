import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utc_now_naive
from app.database import Base


class Diagnostic(Base):
    __tablename__ = "diagnostics"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="in_progress", index=True, nullable=False)
    current_step: Mapped[int] = mapped_column(default=0, nullable=False)
    diagnostic_version: Mapped[str] = mapped_column(String(50), default="human-diagnostic-v2", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    user = relationship("User", back_populates="diagnostics")


class DiagnosticResponse(Base):
    """Inspectable response rows for the quick diagnostic.

    The Diagnostic payload remains a compatibility snapshot, while these rows
    keep question-level provenance and deterministic scoring inputs queryable.
    """

    __tablename__ = "diagnostic_responses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    diagnostic_id: Mapped[str] = mapped_column(ForeignKey("diagnostics.id"), index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    question_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    assessment_domain: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    question_type: Mapped[str] = mapped_column(String(40), nullable=False)
    response_json: Mapped[dict | list | str | int | float | None] = mapped_column(JSON, nullable=True)
    normalized_value: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[int | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(40), default="self_report", nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="human-diagnostic-v2", nullable=False)
    interpretation: Mapped[str | None] = mapped_column(Text)
    completeness: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    scoring_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive, nullable=False)

