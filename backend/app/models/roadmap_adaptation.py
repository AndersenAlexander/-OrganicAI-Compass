import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utc_now_naive
from app.database import Base


class RoadmapAction(Base):
    __tablename__ = "roadmap_actions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    roadmap_id: Mapped[str] = mapped_column(ForeignKey("roadmaps.id"), index=True)
    profile_id: Mapped[str | None] = mapped_column(String, index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    recommendation_id: Mapped[str | None] = mapped_column(String, index=True)
    horizon: Mapped[str] = mapped_column(String, default="thirty_days")
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    reason: Mapped[str] = mapped_column(Text, default="")
    first_step: Mapped[str] = mapped_column(Text, default="")
    success_criteria: Mapped[str] = mapped_column(Text, default="")
    estimated_minutes: Mapped[int | None] = mapped_column(Integer)
    effort: Mapped[str] = mapped_column(String, default="medium")
    impact: Mapped[str] = mapped_column(String, default="medium")
    priority: Mapped[int] = mapped_column(Integer, default=3)
    status: Mapped[str] = mapped_column(String, default="not_started")
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0)
    due_date: Mapped[str | None] = mapped_column(String)
    scheduled_date: Mapped[str | None] = mapped_column(String)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    skipped_at: Mapped[datetime | None] = mapped_column(DateTime)
    skip_reason: Mapped[str | None] = mapped_column(Text)
    user_notes: Mapped[str] = mapped_column(Text, default="")
    source_type: Mapped[str] = mapped_column(String, default="profile")
    profile_signals_json: Mapped[list] = mapped_column(JSON, default=list)
    rag_sources_json: Mapped[list] = mapped_column(JSON, default=list)
    ethical_cautions_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class RoadmapMilestone(Base):
    __tablename__ = "roadmap_milestones"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    roadmap_id: Mapped[str] = mapped_column(ForeignKey("roadmaps.id"), index=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    target_date: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="upcoming")
    success_criteria: Mapped[str] = mapped_column(Text, default="")
    evidence_note: Mapped[str] = mapped_column(Text, default="")
    linked_action_ids: Mapped[list] = mapped_column(JSON, default=list)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)


class RoadmapCheckIn(Base):
    __tablename__ = "roadmap_checkins"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    roadmap_id: Mapped[str] = mapped_column(ForeignKey("roadmaps.id"), index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    profile_id: Mapped[str | None] = mapped_column(String, index=True)
    check_in_type: Mapped[str] = mapped_column(String, default="quick")
    energy_level: Mapped[int | None] = mapped_column(Integer)
    confidence_level: Mapped[int | None] = mapped_column(Integer)
    perceived_progress: Mapped[int | None] = mapped_column(Integer)
    main_blocker: Mapped[str] = mapped_column(Text, default="")
    what_worked: Mapped[str] = mapped_column(Text, default="")
    what_changed: Mapped[str] = mapped_column(Text, default="")
    user_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class RoadmapVersion(Base):
    __tablename__ = "roadmap_versions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    roadmap_id: Mapped[str] = mapped_column(ForeignKey("roadmaps.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class RoadmapEvent(Base):
    __tablename__ = "roadmap_events"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    roadmap_id: Mapped[str] = mapped_column(ForeignKey("roadmaps.id"), index=True)
    action_id: Mapped[str | None] = mapped_column(String, index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)

