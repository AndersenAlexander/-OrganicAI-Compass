import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utc_now_naive
from app.database import Base


def new_id() -> str:
    return str(uuid.uuid4())


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    application_id: Mapped[str | None] = mapped_column(ForeignKey("job_applications.id"), nullable=True, index=True)
    job_analysis_id: Mapped[str | None] = mapped_column(ForeignKey("job_analyses.id"), nullable=True, index=True)
    cv_document_id: Mapped[str | None] = mapped_column(ForeignKey("application_documents.id"), nullable=True, index=True)
    cover_letter_document_id: Mapped[str | None] = mapped_column(ForeignKey("application_documents.id"), nullable=True, index=True)
    organisation: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[str] = mapped_column(String(255), default="")
    stage_type: Mapped[str] = mapped_column(String(80), index=True)
    stage_order: Mapped[int] = mapped_column(Integer, default=1)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime)
    timezone: Mapped[str] = mapped_column(String(80), default="Europe/Bucharest")
    location_or_platform: Mapped[str] = mapped_column(String(255), default="")
    interview_format: Mapped[str] = mapped_column(String(80), default="unknown")
    expected_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    participants_json: Mapped[list] = mapped_column(JSON, default=list)
    preparation_status: Mapped[str] = mapped_column(String(80), default="Not started", index=True)
    mock_session_status: Mapped[str] = mapped_column(String(80), default="Not started", index=True)
    confidence_before: Mapped[int | None] = mapped_column(Integer)
    confidence_after: Mapped[int | None] = mapped_column(Integer)
    interview_result: Mapped[str] = mapped_column(String(80), default="Unknown", index=True)
    follow_up_status: Mapped[str] = mapped_column(String(80), default="Not started", index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(80), default="manual", index=True)
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    version: Mapped[str] = mapped_column(String(80), default="interview-journey-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class InterviewPreparationBrief(Base):
    __tablename__ = "interview_preparation_briefs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    interview_id: Mapped[str] = mapped_column(ForeignKey("interviews.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    application_id: Mapped[str | None] = mapped_column(ForeignKey("job_applications.id"), nullable=True, index=True)
    job_analysis_id: Mapped[str | None] = mapped_column(ForeignKey("job_analyses.id"), nullable=True, index=True)
    sections_json: Mapped[dict] = mapped_column(JSON, default=dict)
    readiness_checklist_json: Mapped[list] = mapped_column(JSON, default=list)
    source_notes_json: Mapped[list] = mapped_column(JSON, default=list)
    language: Mapped[str] = mapped_column(String(40), default="en")
    status: Mapped[str] = mapped_column(String(80), default="draft", index=True)
    source: Mapped[str] = mapped_column(String(80), default="deterministic")
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    deterministic_origin: Mapped[str] = mapped_column(String(80), default="interview-brief-v1")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    interview_id: Mapped[str] = mapped_column(ForeignKey("interviews.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    application_id: Mapped[str | None] = mapped_column(ForeignKey("job_applications.id"), nullable=True, index=True)
    job_analysis_id: Mapped[str | None] = mapped_column(ForeignKey("job_analyses.id"), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    stage: Mapped[str] = mapped_column(String(80), index=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    why_it_may_be_asked: Mapped[str] = mapped_column(Text, default="")
    related_job_requirement_id: Mapped[str | None] = mapped_column(ForeignKey("job_requirements.id"), nullable=True, index=True)
    related_job_requirement: Mapped[str] = mapped_column(Text, default="")
    related_evidence_json: Mapped[list] = mapped_column(JSON, default=list)
    answer_objective: Mapped[str] = mapped_column(Text, default="")
    risk_level: Mapped[str] = mapped_column(String(40), default="medium", index=True)
    difficulty: Mapped[str] = mapped_column(String(40), default="moderate", index=True)
    source_type: Mapped[str] = mapped_column(String(80), default="stage_template")
    origin: Mapped[str] = mapped_column(String(80), default="deterministic")
    saved_by_user: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    question_id: Mapped[str] = mapped_column(ForeignKey("interview_questions.id"), index=True)
    interview_id: Mapped[str] = mapped_column(ForeignKey("interviews.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    answer_objective: Mapped[str] = mapped_column(Text, default="")
    key_points_json: Mapped[list] = mapped_column(JSON, default=list)
    selected_evidence_json: Mapped[list] = mapped_column(JSON, default=list)
    selected_star_story_id: Mapped[str | None] = mapped_column(ForeignKey("star_stories.id"), nullable=True, index=True)
    suggested_structure_json: Mapped[list] = mapped_column(JSON, default=list)
    possible_opening: Mapped[str] = mapped_column(Text, default="")
    possible_closing: Mapped[str] = mapped_column(Text, default="")
    risk_areas_json: Mapped[list] = mapped_column(JSON, default=list)
    unsupported_claims_json: Mapped[list] = mapped_column(JSON, default=list)
    claim_statuses_json: Mapped[list] = mapped_column(JSON, default=list)
    user_draft: Mapped[str] = mapped_column(Text, default="")
    revised_draft: Mapped[str] = mapped_column(Text, default="")
    final_approved_answer: Mapped[str] = mapped_column(Text, default="")
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    origin: Mapped[str] = mapped_column(String(80), default="deterministic")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class StarStory(Base):
    __tablename__ = "star_stories"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    situation: Mapped[str] = mapped_column(Text, default="")
    task: Mapped[str] = mapped_column(Text, default="")
    action: Mapped[str] = mapped_column(Text, default="")
    result: Mapped[str] = mapped_column(Text, default="")
    reflection: Mapped[str] = mapped_column(Text, default="")
    skills_demonstrated_json: Mapped[list] = mapped_column(JSON, default=list)
    related_job_requirements_json: Mapped[list] = mapped_column(JSON, default=list)
    evidence_links_json: Mapped[list] = mapped_column(JSON, default=list)
    dates_json: Mapped[dict] = mapped_column(JSON, default=dict)
    organisation_or_context: Mapped[str] = mapped_column(String(255), default="")
    confidentiality_status: Mapped[str] = mapped_column(String(80), default="review_needed", index=True)
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    claim_statuses_json: Mapped[list] = mapped_column(JSON, default=list)
    suitable_stages_json: Mapped[list] = mapped_column(JSON, default=list)
    tags_json: Mapped[list] = mapped_column(JSON, default=list)
    quality_status: Mapped[str] = mapped_column(String(120), default="Needs clearer action", index=True)
    quality_json: Mapped[dict] = mapped_column(JSON, default=dict)
    source: Mapped[str] = mapped_column(String(80), default="manual")
    status: Mapped[str] = mapped_column(String(80), default="active", index=True)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class StarStoryVersion(Base):
    __tablename__ = "star_story_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    story_id: Mapped[str] = mapped_column(ForeignKey("star_stories.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    change_reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class MockInterviewSession(Base):
    __tablename__ = "mock_interview_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    interview_id: Mapped[str] = mapped_column(ForeignKey("interviews.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    application_id: Mapped[str | None] = mapped_column(ForeignKey("job_applications.id"), nullable=True, index=True)
    mode: Mapped[str] = mapped_column(String(80), default="guided_practice", index=True)
    delivery_mode: Mapped[str] = mapped_column(String(40), default="text", index=True)
    persona: Mapped[str] = mapped_column(String(80), default="unknown_interviewer", index=True)
    status: Mapped[str] = mapped_column(String(80), default="created", index=True)
    question_sequence_json: Mapped[list] = mapped_column(JSON, default=list)
    transcript_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    transcript_retained: Mapped[bool] = mapped_column(Boolean, default=False)
    timing_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    feedback_json: Mapped[dict] = mapped_column(JSON, default=dict)
    rubric_results_json: Mapped[list] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(80), default="deterministic")
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class MockInterviewTurn(Base):
    __tablename__ = "mock_interview_turns"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("mock_interview_sessions.id"), index=True)
    interview_id: Mapped[str] = mapped_column(ForeignKey("interviews.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    question_id: Mapped[str | None] = mapped_column(ForeignKey("interview_questions.id"), nullable=True, index=True)
    turn_index: Mapped[int] = mapped_column(Integer, default=1)
    question_text: Mapped[str] = mapped_column(Text, default="")
    answer_text: Mapped[str] = mapped_column(Text, default="")
    corrected_transcript: Mapped[str] = mapped_column(Text, default="")
    response_duration_seconds: Mapped[int | None] = mapped_column(Integer)
    estimated_word_count: Mapped[int] = mapped_column(Integer, default=0)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    completion_status: Mapped[str] = mapped_column(String(80), default="answered")
    follow_up_questions_json: Mapped[list] = mapped_column(JSON, default=list)
    rubric_json: Mapped[list] = mapped_column(JSON, default=list)
    feedback_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class VoiceProviderSession(Base):
    __tablename__ = "voice_provider_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    mock_session_id: Mapped[str | None] = mapped_column(ForeignKey("mock_interview_sessions.id"), nullable=True, index=True)
    interview_id: Mapped[str | None] = mapped_column(ForeignKey("interviews.id"), nullable=True, index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(80), default="elevenlabs")
    provider_session_id: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(80), default="created", index=True)
    language: Mapped[str] = mapped_column(String(40), default="en")
    consent_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    audio_retained: Mapped[bool] = mapped_column(Boolean, default=False)
    transcript_retained: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class InterviewReflection(Base):
    __tablename__ = "interview_reflections"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    interview_id: Mapped[str] = mapped_column(ForeignKey("interviews.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    application_id: Mapped[str | None] = mapped_column(ForeignKey("job_applications.id"), nullable=True, index=True)
    stage_completed: Mapped[str] = mapped_column(String(80), default="")
    completed_date: Mapped[str | None] = mapped_column(String(40))
    participants_json: Mapped[list] = mapped_column(JSON, default=list)
    questions_remembered_json: Mapped[list] = mapped_column(JSON, default=list)
    strong_answers_json: Mapped[list] = mapped_column(JSON, default=list)
    weak_answers_json: Mapped[list] = mapped_column(JSON, default=list)
    unexpected_topics_json: Mapped[list] = mapped_column(JSON, default=list)
    confirmed_interviewer_feedback: Mapped[str] = mapped_column(Text, default="")
    user_interpretation: Mapped[str] = mapped_column(Text, default="")
    ai_interpretation_json: Mapped[dict] = mapped_column(JSON, default=dict)
    next_step: Mapped[str] = mapped_column(String(160), default="unknown")
    follow_up_deadline: Mapped[str | None] = mapped_column(String(40))
    confidence_before: Mapped[int | None] = mapped_column(Integer)
    confidence_after: Mapped[int | None] = mapped_column(Integer)
    additional_evidence_needed_json: Mapped[list] = mapped_column(JSON, default=list)
    outcome_status: Mapped[str] = mapped_column(String(80), default="unknown", index=True)
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class InterviewFollowUpDraft(Base):
    __tablename__ = "interview_follow_up_drafts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    interview_id: Mapped[str] = mapped_column(ForeignKey("interviews.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    application_id: Mapped[str | None] = mapped_column(ForeignKey("job_applications.id"), nullable=True, index=True)
    draft_type: Mapped[str] = mapped_column(String(80), default="thank_you", index=True)
    subject: Mapped[str] = mapped_column(String(255), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    source_facts_json: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(80), default="draft", index=True)
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class OfferReview(Base):
    __tablename__ = "offer_reviews"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    application_id: Mapped[str | None] = mapped_column(ForeignKey("job_applications.id"), nullable=True, index=True)
    interview_id: Mapped[str | None] = mapped_column(ForeignKey("interviews.id"), nullable=True, index=True)
    organisation: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[str] = mapped_column(String(255), default="")
    offer_items_json: Mapped[dict] = mapped_column(JSON, default=dict)
    user_priorities_json: Mapped[list] = mapped_column(JSON, default=list)
    review_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(80), default="draft", index=True)
    source: Mapped[str] = mapped_column(String(80), default="manual")
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    demo_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

