import asyncio

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.innovation_extension import CareerDecisionJournalEntry
from app.models.interview_journey import Interview, InterviewReflection, MockInterviewSession, OfferReview, StarStory
from app.models.market_application import JobAnalysis, JobApplication, JobPosting, JobRequirement
from app.models.profile import Profile
from app.models.roadmap_adaptation import RoadmapAction
from app.models.user import User
from app.routers.profiles import get_profile_journey_state
from app.services.innovation_extension_engine import get_journal_entry
from app.services.interview_journey_engine import (
    add_mock_turn,
    complete_mock_session,
    create_decision_journal_hook,
    create_interview,
    create_mock_session,
    create_offer_review,
    create_reflection,
    create_star_story,
    generate_interview_questions,
    generate_preparation_brief,
    start_mock_session,
)
from app.services.market_application_engine import (
    confirm_job_analysis,
    create_application,
    create_job_analysis,
    require_analysis,
    save_job_for_profile,
    update_requirement,
)


def session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def profile_with_job(db: Session) -> tuple[User, Profile, JobPosting]:
    user = User(name="Employment Journey User", email="employment-journey@example.test", hashed_password="x")
    db.add(user)
    db.flush()
    profile = Profile(user_id=user.id, diagnostic_id="employment-journey-diagnostic", data={"primary_archetype": {"name": "Curious Builder"}})
    db.add(profile)
    job = JobPosting(
        provider="employment-journey-demo",
        external_job_id="human-centred-ai-product-designer-001",
        source_url="https://jobs.example.test/human-centred-ai-product-designer-001",
        title="Human-Centred AI Product Designer",
        employer="Example Product Studio",
        description="Mandatory requirements include UX design, responsible AI, stakeholder communication, and API collaboration.",
        municipality="Oslo",
        country="Norway",
        work_mode="hybrid",
        is_active=True,
    )
    db.add(job)
    db.commit()
    return user, profile, job


def confirmed_analysis(db: Session, profile: Profile, job: JobPosting, user_id: str) -> JobAnalysis:
    analysis = create_job_analysis(db, profile, {"job_id": job.id, "input_type": "saved_job"})
    row = require_analysis(db, analysis["id"], profile)
    for requirement in db.scalars(select(JobRequirement).where(JobRequirement.analysis_id == row.id)).all():
        update_requirement(db, requirement, {"action": "accept"}, user_id)
    confirm_job_analysis(db, row, user_id)
    return row


def test_employment_journey_preserves_one_identity_chain_after_fresh_reads():
    db = session()
    user, profile, job = profile_with_job(db)
    roadmap_actions_before = db.scalar(select(func.count()).select_from(RoadmapAction).where(RoadmapAction.profile_id == profile.id)) or 0

    # Market Radar / Job Analyzer: repeated analysis may create historical
    # analyses, but must not create a second source job record.
    analysis = confirmed_analysis(db, profile, job, user.id)
    repeated_analysis = create_job_analysis(db, profile, {"job_id": job.id, "input_type": "saved_job"})
    assert repeated_analysis["job_id"] == job.id
    assert db.scalar(select(func.count()).select_from(JobPosting).where(JobPosting.provider == job.provider, JobPosting.external_job_id == job.external_job_id)) == 1

    # A saved opportunity and the later analysed tracker record resolve to one
    # canonical application without overwriting user-entered notes on retry.
    saved = save_job_for_profile(db, profile, job)
    application = create_application(
        db,
        profile,
        {
            "job_id": job.id,
            "job_analysis_id": analysis.id,
            "status": "Preparing",
            "notes": "User-entered application note.",
            "next_action": "Review the confirmed requirements.",
        },
    )
    retried_application = create_application(
        db,
        profile,
        {
            "job_id": job.id,
            "job_analysis_id": analysis.id,
            "status": "Preparing",
            "notes": "This retry must not replace the original note.",
        },
    )
    assert saved["id"] == application["id"] == retried_application["id"]
    app = db.get(JobApplication, application["id"])
    assert app.job_id == job.id
    assert app.job_analysis_id == analysis.id
    assert app.notes == "User-entered application note."
    assert db.scalar(select(func.count()).select_from(JobApplication).where(JobApplication.profile_id == profile.id, JobApplication.job_id == job.id)) == 1

    # Interview creation is explicit and idempotent for an identical tracker
    # action; preparation and simulation retain the same application context.
    interview_payload = {
        "application_id": app.id,
        "stage_type": "technical",
        "scheduled_at": "2026-09-15T10:00:00",
        "interview_format": "online",
        "participants": [{"role": "technical lead", "user_confirmed": True}],
        "user_confirmed": True,
    }
    interview_created = create_interview(db, profile, interview_payload, user.id)
    interview_retried = create_interview(db, profile, interview_payload, user.id)
    assert interview_created["id"] == interview_retried["id"]
    interview = db.get(Interview, interview_created["id"])
    assert interview.application_id == app.id
    assert interview.job_analysis_id == analysis.id
    assert db.scalar(select(func.count()).select_from(Interview).where(Interview.profile_id == profile.id, Interview.application_id == app.id)) == 1

    preparation = generate_preparation_brief(db, interview)
    questions = generate_interview_questions(db, interview)["questions"]
    story = create_star_story(
        db,
        profile,
        {
            "title": "Evidence-based product trade-off",
            "situation": "A product team needed a reviewable AI recommendation flow.",
            "task": "Make constraints and user control visible.",
            "action": "I designed comparison states and tested the explanation with users.",
            "result": "The team selected a bounded, reviewable prototype.",
            "reflection": "More external feedback would strengthen the evidence.",
            "evidence_links": [{"source": "user-confirmed example"}],
            "user_confirmed": True,
        },
        user.id,
    )
    mock_created = create_mock_session(
        db,
        interview,
        {"mode": "full_simulation", "delivery_mode": "text", "panel_personas": ["technical_lead", "product_lead"]},
    )
    mock = db.get(MockInterviewSession, mock_created["id"])
    start_mock_session(db, mock)
    add_mock_turn(
        db,
        mock,
        {
            "question_id": questions[0]["id"],
            "answer_text": "I designed and tested a reviewable product flow, explained the trade-off, and learned where further evidence was needed.",
            "response_duration_seconds": 75,
        },
    )
    completed_mock = complete_mock_session(db, mock, {"transcript_confirmed": True, "transcript_retained": False})
    assert preparation["application_id"] == app.id
    assert story["user_confirmed"] is True
    assert completed_mock["interview_id"] == interview.id
    assert set(completed_mock["panel_personas"]) == {"technical_lead", "product_lead"}
    assert completed_mock["transcript_retained"] is False

    reflection = create_reflection(
        db,
        interview,
        {
            "user_observation": "The panel asked for a concrete API collaboration example.",
            "user_interpretation": "I should improve that explanation before another technical stage.",
            "confirmed_interviewer_feedback": "Please clarify the API collaboration example.",
            "weak_answers": ["API collaboration"],
            "additional_evidence_needed": ["API collaboration example"],
            "user_confirmed": True,
        },
    )
    offer = create_offer_review(
        db,
        profile,
        {"application_id": app.id, "interview_id": interview.id, "salary": 900000, "currency": "NOK", "user_priorities": ["remote flexibility"]},
        user.id,
    )
    journal = create_decision_journal_hook(
        db,
        interview,
        {
            "source_type": "offer_decision",
            "title": "Offer decision for Example Product Studio",
            "selected_option": "Review before deciding",
            "assumptions": ["Working hours still need confirmation."],
            "evidence_links": [
                {"type": "interview_reflection", "id": reflection["id"]},
                {"type": "offer_review", "id": offer["id"]},
            ],
            "evidence_observations": [{"reflection_id": reflection["id"], "confirmed_feedback": True}],
            "ai_explanations": [{"suggestion": "Compare the full package before deciding."}],
            "system_suggestions": [{"calculation": "Missing offer fields remain unresolved."}],
            "user_reasoning": "I will wait for the written conditions before making a decision.",
        },
        user.id,
    )

    db.expire_all()
    persisted_reflection = db.get(InterviewReflection, reflection["id"])
    persisted_offer = db.get(OfferReview, offer["id"])
    persisted_journal = db.get(CareerDecisionJournalEntry, journal["id"])
    journal_detail = get_journal_entry(db, profile, journal["id"])
    journey_state = asyncio.run(get_profile_journey_state(profile.id, db, user))

    assert persisted_reflection.interview_id == interview.id
    assert persisted_reflection.application_id == app.id
    assert persisted_offer.application_id == app.id
    assert persisted_offer.interview_id == interview.id
    assert persisted_offer.user_confirmed is False
    assert "working_hours" in offer["review"]["missing_information"]
    assert persisted_journal.application_id == app.id
    assert persisted_journal.interview_id == interview.id
    assert journal_detail["user_reasoning"] == "I will wait for the written conditions before making a decision."
    assert journal_detail["evidence_observations"] == [{"reflection_id": reflection["id"], "confirmed_feedback": True}]
    assert journal_detail["ai_explanations"] == [{"suggestion": "Compare the full package before deciding."}]
    assert journal_detail["system_suggestions"] == [{"calculation": "Missing offer fields remain unresolved."}]
    assert journey_state["has_application_activity"] is True
    assert journey_state["has_interview_activity"] is True
    assert journey_state["employment_summary"] == {
        "application_count": 1,
        "interview_count": 1,
        "completed_interview_count": 1,
        "offer_review_count": 1,
        "roadmap_mutated": False,
    }
    assert journey_state["interview_summary"]["id"] == interview.id
    assert db.scalar(select(func.count()).select_from(RoadmapAction).where(RoadmapAction.profile_id == profile.id)) == roadmap_actions_before
