import asyncio

from sqlalchemy import func, select
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.assessment import AssessmentSession, SkillEvidence, SkillsInventory
from app.models.career_resilience import SkillEvidenceConfidence
from app.models.interview_journey import Interview, InterviewQuestion, MockInterviewSession, StarStory, VoiceProviderSession
from app.models.market_application import ApplicationDocument, ApplicationRecalibrationRun, DocumentClaim, JobAnalysis, JobApplication, JobApplicationEvent, JobRequirement, JobRequirementEvidenceMatch
from app.models.profile import Profile
from app.models.roadmap_adaptation import RoadmapAction
from app.models.user import User
from app.routers.profiles import get_profile_journey_state
from app.services.interview_journey_engine import (
    add_mock_turn,
    adapt_star_story,
    build_answer,
    compare_offer_reviews,
    complete_mock_session,
    create_interview,
    create_mock_session,
    create_offer_review,
    create_reflection,
    create_star_story,
    create_custom_question,
    create_voice_session,
    generate_interview_questions,
    generate_preparation_brief,
    interview_voice_status,
    interview_dashboard,
    list_interview_recalibration_proposals,
    decide_interview_recalibration,
    record_interview_outcome,
    record_interview_application_event,
    require_interview,
    seed_demo_interview_journey,
    start_mock_session,
    update_interview_question,
)


def session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def profile(db: Session, email: str = "interview@example.test") -> tuple[User, Profile]:
    user = User(name="Interview User", email=email, hashed_password="x")
    db.add(user)
    db.flush()
    item = Profile(user_id=user.id, diagnostic_id="diagnostic", data={"primary_archetype": {"name": "Curious Builder"}})
    db.add(item)
    db.commit()
    return user, item


def seed_application_context(db: Session) -> tuple[User, Profile, JobApplication, JobAnalysis, SkillEvidence]:
    user, item = profile(db)
    assessment = AssessmentSession(profile_id=item.id, user_id=user.id, mode="complete", status="completed", consent_accepted=True)
    db.add(assessment)
    db.flush()
    inventory = SkillsInventory(session_id=assessment.id, profile_id=item.id, user_id=user.id, category="technical", skill_id="ux_ui", skill_label="UX/UI", level=3, evidence_status="supported_by_project")
    db.add(inventory)
    db.flush()
    evidence = SkillEvidence(skill_inventory_id=inventory.id, evidence_type="project", title="Explainable recommendation prototype", description="Designed and tested a local prototype.", verification_status="supported")
    db.add(evidence)
    db.flush()
    db.add(SkillEvidenceConfidence(skill_evidence_id=evidence.id, profile_id=item.id, skill_id="ux_ui", confidence_label="Moderate evidence", strength_label="Supported", score_internal=3.2))
    analysis = JobAnalysis(profile_id=item.id, user_id=user.id, title="AI Product Designer", organisation="Fictional Fjord Labs", raw_text_excerpt="UX, responsible AI and APIs.", user_confirmed=True)
    db.add(analysis)
    db.flush()
    req_ux = JobRequirement(analysis_id=analysis.id, profile_id=item.id, requirement_text="UX design and responsible AI", requirement_category="skills", requirement_type="mandatory", normalised_skill_id="ux_ui", user_confirmation_state="confirmed", order_index=1)
    req_api = JobRequirement(analysis_id=analysis.id, profile_id=item.id, requirement_text="API integration", requirement_category="technology", requirement_type="mandatory", normalised_skill_id="apis", user_confirmation_state="confirmed", order_index=2)
    db.add_all([req_ux, req_api])
    db.flush()
    db.add(JobRequirementEvidenceMatch(requirement_id=req_ux.id, analysis_id=analysis.id, profile_id=item.id, evidence_id=evidence.id, evidence_type="skill_evidence", evidence_strength="Supported", match_category="Strong evidence", deterministic_reason="Existing evidence supports UX."))
    app = JobApplication(profile_id=item.id, user_id=user.id, job_analysis_id=analysis.id, title=analysis.title, organisation=analysis.organisation, status="Preparing", source="manual")
    db.add(app)
    db.commit()
    return user, item, app, analysis, evidence


def test_interview_creation_from_application_preserves_tracker_status_and_validates_stage():
    db = session()
    user, item, app, analysis, _ = seed_application_context(db)
    created = create_interview(
        db,
        item,
        {"application_id": app.id, "stage_type": "technical", "scheduled_at": "2026-07-25T10:00:00", "interview_format": "online", "participants": [{"role": "technical lead"}], "user_confirmed": True},
        user.id,
    )
    db.refresh(app)

    assert created["application_id"] == app.id
    assert created["job_analysis_id"] == analysis.id
    assert created["stage_type"] == "technical"
    assert app.status == "Preparing"
    assert db.scalar(select(func.count()).select_from(JobApplicationEvent).where(JobApplicationEvent.application_id == app.id)) == 1

    try:
        create_interview(db, item, {"application_id": app.id, "stage_type": "invented_stage"}, user.id)
        assert False
    except ValueError:
        pass

    _, other_profile = profile(db, "other-interview@example.test")
    try:
        create_interview(db, other_profile, {"application_id": app.id, "stage_type": "recruiter_screening"}, other_profile.user_id)
        assert False
    except PermissionError:
        pass


def test_dashboard_next_action_tracks_the_interview_lifecycle_in_order():
    db = session()
    user, item = profile(db)

    assert interview_dashboard(db, item)["next_recommended_action"] == "Create or save an application before adding an interview."

    application = JobApplication(profile_id=item.id, user_id=user.id, title="Evidence-led role", organisation="Example", status="Preparing", source="manual")
    db.add(application)
    db.commit()
    assert interview_dashboard(db, item)["next_recommended_action"] == "Create an Interview Journey record or add an interview."

    created = create_interview(db, item, {"application_id": application.id, "stage_type": "recruiter_screening", "scheduled_at": "2026-07-25T10:00:00"}, user.id)
    interview = db.get(Interview, created["id"])
    assert interview_dashboard(db, item)["next_recommended_action"] == "Prepare for your next interview."

    interview.status = "COMPLETED"
    interview.scheduled_at = None
    db.commit()
    assert interview_dashboard(db, item)["next_recommended_action"] == "Record a post-interview reflection."

    create_reflection(db, interview, {"user_confirmed": True})
    assert interview_dashboard(db, item)["next_recommended_action"] == "Record the interview outcome."

    record_interview_outcome(db, interview, {"outcome": "REJECTED", "source": "User confirmed", "reason": "No reason provided"}, user.id)
    assert interview_dashboard(db, item)["next_recommended_action"] == "Review the recalibration proposal."


def test_preparation_questions_answer_builder_and_explicit_application_update():
    db = session()
    user, item, app, _, _ = seed_application_context(db)
    interview = db.get(Interview, create_interview(db, item, {"application_id": app.id, "stage_type": "technical"}, user.id)["id"])

    generated = generate_interview_questions(db, interview)
    brief = generate_preparation_brief(db, interview, {"language": "en"})
    requirement_questions = [question for question in generated["questions"] if question["source_type"] == "confirmed_job_requirement"]
    answer = build_answer(db, db.get(InterviewQuestion, requirement_questions[0]["id"]), {"user_draft": "I developed production-ready AI systems for this company.", "selected_evidence": []})

    assert brief["sections"]["confirmed_job_requirements"]["confirmed_facts"]
    assert not any("They will ask" in question["why_it_may_be_asked"] for question in generated["questions"])
    assert {question["related_job_requirement"] for question in requirement_questions} <= {"UX design and responsible AI", "API integration"}
    assert answer["claim_statuses"][0]["status"] == "Blocked"

    unchanged = record_interview_application_event(db, interview, {"event_type": "interview_scheduled", "confirm_status_update": False}, user.id)
    db.refresh(app)
    assert unchanged["status_update_confirmed"] is False
    assert app.status == "Preparing"

    changed = record_interview_application_event(db, interview, {"event_type": "interview_scheduled", "confirm_status_update": True}, user.id)
    db.refresh(app)
    assert changed["status_update_confirmed"] is True
    assert app.status == "Technical or case stage"
    assert db.scalar(select(func.count()).select_from(JobApplicationEvent).where(JobApplicationEvent.application_id == app.id)) >= 3


def test_star_story_quality_mock_feedback_reflection_voice_and_offer_safeguards():
    db = session()
    user, item, app, _, _ = seed_application_context(db)
    interview = db.get(Interview, create_interview(db, item, {"application_id": app.id, "stage_type": "recruiter_screening"}, user.id)["id"])
    story = create_star_story(
        db,
        item,
        {
            "title": "Unsupported metric story",
            "situation": "A workflow was repetitive.",
            "task": "Improve the workflow.",
            "action": "I reduced steps and documented the limitation.",
            "result": "Increased efficiency by 40%.",
            "reflection": "I should verify the metric before using it.",
            "confidentiality_status": "review_needed",
        },
        user.id,
    )
    assert story["quality_status"] in {"Contains unsupported claims", "Confidentiality review required", "Needs stronger result evidence"}
    assert "Blocked" in str(story["claim_statuses"])

    questions = generate_interview_questions(db, interview)["questions"]
    mock = db.get(MockInterviewSession, create_mock_session(db, interview, {"mode": "guided_practice", "delivery_mode": "voice"})["id"])
    assert mock.delivery_mode == "text"
    start_mock_session(db, mock)
    add_mock_turn(db, mock, {"question_id": questions[0]["id"], "answer_text": "I can discuss a project with evidence, tested locally, where I designed the interface and learned what to improve.", "response_duration_seconds": 70})
    completed = complete_mock_session(db, mock, {"transcript_confirmed": True, "transcript_retained": True})
    assert completed["feedback"]["no_single_opaque_score"] is True
    assert completed["rubric_results"]

    before_roadmap = db.scalar(select(func.count()).select_from(RoadmapAction).where(RoadmapAction.profile_id == item.id)) or 0
    reflection = create_reflection(db, interview, {"weak_answers": ["salary discussion"], "additional_evidence_needed": ["API evidence"], "user_confirmed": True})
    after_roadmap = db.scalar(select(func.count()).select_from(RoadmapAction).where(RoadmapAction.profile_id == item.id)) or 0
    assert reflection["confirmed_interviewer_feedback"] == ""
    assert reflection["outcome"] == "UNKNOWN"
    assert db.scalar(select(func.count()).select_from(ApplicationRecalibrationRun).where(ApplicationRecalibrationRun.application_id == app.id)) == 0
    record_interview_outcome(db, interview, {"outcome": "NEXT_STAGE", "source": "User-recorded outcome"}, user.id)
    assert db.scalar(select(func.count()).select_from(ApplicationRecalibrationRun).where(ApplicationRecalibrationRun.application_id == app.id)) == 1
    assert before_roadmap == after_roadmap

    assert interview_voice_status()["enabled"] is False
    try:
        create_voice_session(db, item, {"interview_id": interview.id})
        assert False
    except ValueError:
        pass
    voice = create_voice_session(db, item, {"interview_id": interview.id, "microphone_consent": True})
    assert voice["status"] == "disabled_fallback"
    assert db.scalar(select(func.count()).select_from(VoiceProviderSession).where(VoiceProviderSession.profile_id == item.id)) == 1

    offer = create_offer_review(db, item, {"application_id": app.id, "salary": 650000, "currency": "NOK", "user_priorities": ["remote flexibility", "training support"]}, user.id)
    assert offer["review"]["legal_or_financial_advice"] is False
    assert "working_hours" in offer["review"]["missing_information"]


def test_preparation_uses_only_final_confirmed_requirements_and_current_document_claims():
    db = session()
    user, item, app, analysis, _ = seed_application_context(db)
    cv = ApplicationDocument(profile_id=item.id, user_id=user.id, job_analysis_id=analysis.id, document_type="cv", title="Current CV")
    db.add(cv)
    db.flush()
    db.add(DocumentClaim(document_id=cv.id, profile_id=item.id, claim_text="I designed a locally tested prototype.", status="Partially supported", support_state="PARTIALLY_SUPPORTED"))
    app.cv_document_id = cv.id
    db.commit()
    interview = db.get(Interview, create_interview(db, item, {"application_id": app.id, "stage_type": "technical"}, user.id)["id"])

    analysis.user_confirmed = False
    db.commit()
    unconfirmed = generate_interview_questions(db, interview)
    unconfirmed_brief = generate_preparation_brief(db, interview)
    assert not [item for item in unconfirmed["questions"] if item["source_type"] == "confirmed_job_requirement"]
    assert unconfirmed_brief["sections"]["confirmed_job_requirements"]["missing_information"] == ["No confirmed requirements are available."]

    analysis.user_confirmed = True
    db.commit()
    generated = generate_interview_questions(db, interview, {"force": True})
    repeated = generate_interview_questions(db, interview, {"force": True})
    requirement_questions = [item for item in generated["questions"] if item["source_type"] == "confirmed_job_requirement"]
    assert {item["related_job_requirement"] for item in requirement_questions} == {"UX design and responsible AI", "API integration"}
    assert repeated["generated"] is False
    assert len(repeated["questions"]) == len(generated["questions"])

    brief = generate_preparation_brief(db, interview)
    claim_section = brief["sections"]["application_claims_to_support"]
    assert claim_section["missing_information"][0]["claim"] == "I designed a locally tested prototype."
    assert "id" not in claim_section["missing_information"][0]


def test_reflection_outcome_mock_and_offer_boundaries_remain_explicit():
    db = session()
    user, item, app, _, _ = seed_application_context(db)
    interview = db.get(Interview, create_interview(db, item, {"application_id": app.id, "stage_type": "recruiter_screening"}, user.id)["id"])

    try:
        record_interview_outcome(db, interview, {"outcome": "OFFER"}, user.id)
        assert False
    except ValueError:
        pass

    reflection = create_reflection(
        db,
        interview,
        {
            "confirmed_interviewer_feedback": "Please share one more work sample.",
            "user_observation": "The interviewer asked follow-up questions about API experience.",
            "user_interpretation": "I think my API example was too brief.",
            "user_confirmed": True,
        },
    )
    assert reflection["confirmed_interviewer_feedback"] == "Please share one more work sample."
    assert reflection["user_interpretation"] == "I think my API example was too brief."
    assert reflection["outcome"] == "UNKNOWN"
    assert db.get(Interview, interview.id).status == "COMPLETED"

    questions = generate_interview_questions(db, interview)["questions"]
    mock = db.get(MockInterviewSession, create_mock_session(db, interview, {"delivery_mode": "text"})["id"])
    start_mock_session(db, mock)
    turn = add_mock_turn(db, mock, {"question_id": questions[0]["id"], "answer_text": "I managed 30 engineers across a global programme.", "response_duration_seconds": 40})
    assert "Unsupported factual claim — verify or revise before using this in a real interview." in turn["feedback"]["unsupported_or_unclear_claims"]
    assert db.scalar(select(func.count()).select_from(SkillEvidence)) == 1

    record_interview_outcome(db, interview, {"outcome": "OFFER", "source": "Employer email"}, user.id)
    assert interview_dashboard(db, item)["next_recommended_action"] == "Review the recorded offer facts and remaining unknowns."
    offer = create_offer_review(db, item, {"application_id": app.id, "interview_id": interview.id, "salary": 650000}, user.id)
    assert offer["review_type"] == "LINKED_APPLICATION_COMPARISON"
    assert offer["actual_offer_confirmed"] is False
    assert "working_hours" in offer["review"]["missing_information"]

    _, other_profile = profile(db, "ownership-check@example.test")
    try:
        require_interview(db, interview.id, other_profile)
        assert False
    except PermissionError:
        pass


def test_my_journey_receives_the_persisted_interview_next_action():
    db = session()
    user, item, app, _, _ = seed_application_context(db)
    interview = db.get(Interview, create_interview(db, item, {"application_id": app.id, "stage_type": "recruiter_screening"}, user.id)["id"])
    create_reflection(db, interview, {"user_observation": "The interview concluded.", "user_confirmed": True})

    state = asyncio.run(get_profile_journey_state(item.id, db, user))

    assert state["interview_summary"]["lifecycle_status"] == "COMPLETED"
    assert state["interview_summary"]["has_reflection"] is True
    assert state["interview_summary"]["next_action"] == "Record the interview outcome."


def test_demo_interview_seed_creates_complete_initial_state():
    db = session()
    _, item, app, _, _ = seed_application_context(db)
    seed_demo_interview_journey(db, item)

    assert db.scalar(select(func.count()).select_from(Interview).where(Interview.profile_id == item.id)) >= 3
    assert db.scalar(select(func.count()).select_from(StarStory).where(StarStory.profile_id == item.id)) >= 8
    assert db.scalar(select(func.count()).select_from(MockInterviewSession).where(MockInterviewSession.profile_id == item.id)) >= 2
    assert db.scalar(select(func.count()).select_from(ApplicationRecalibrationRun).where(ApplicationRecalibrationRun.application_id == app.id)) >= 1


def test_interview_controls_outcome_recalibration_and_offer_tradeoffs_are_explicit():
    db = session()
    user, item, app, _, _ = seed_application_context(db)
    interview_payload = create_interview(db, item, {"application_id": app.id, "stage_type": "hiring_manager", "status": "PLANNED"}, user.id)
    interview = db.get(Interview, interview_payload["id"])
    assert interview_payload["status"] == "PLANNED"
    assert interview_payload["requirement_set_version"]

    generated = generate_interview_questions(db, interview)["questions"]
    custom = create_custom_question(db, interview, {"question_text": "What would you clarify first?", "category": "situational"})
    assert custom["custom"] is True
    assert custom["label"] == "Plausible practice question"
    update_interview_question(db, db.get(InterviewQuestion, custom["id"]), {"question_status": "dismissed"})
    assert db.get(InterviewQuestion, custom["id"]).question_status == "dismissed"

    story = create_star_story(db, item, {"title": "Canonical story", "situation": "A team had unclear requirements.", "task": "Clarify the task with the team.", "action": "I mapped assumptions and tested two options.", "result": "The team selected a smaller first version.", "evidence_links": [{"evidence_id": "evidence-1", "verification_status": "supported"}], "user_confirmed": True}, user.id)
    adaptation = adapt_star_story(db, db.get(StarStory, story["id"]), {"interview_id": interview.id})
    assert adaptation["canonical_story_id"] == story["id"]
    assert adaptation["id"] != story["id"]
    assert db.get(StarStory, story["id"]).title == "Canonical story"

    create_reflection(db, interview, {"user_observation": "The interview has concluded.", "user_confirmed": True})
    outcome = record_interview_outcome(db, interview, {"outcome": "REJECTED", "source": "Employer email", "reason": "Not provided"}, user.id)
    db.refresh(app)
    assert outcome["outcome"] == "REJECTED"
    assert outcome["outcome_reason"] == "Not provided"
    assert app.status == "Preparing"
    proposals = list_interview_recalibration_proposals(db, interview)
    assert proposals[0]["proposal_type"] == "PROPOSED_CHANGE"
    assert proposals[0]["limitation"]
    proposal = db.get(ApplicationRecalibrationRun, proposals[0]["id"])
    decided = decide_interview_recalibration(db, proposal, {"decision": "accept"}, user.id)
    assert decided["user_decision"] == "ACCEPT"
    assert decided["after"]["profile_mutated"] is False

    offer_a = create_offer_review(db, item, {"application_id": app.id, "salary": 100, "currency": "EUR", "remote_hybrid_arrangement": "Hybrid", "user_priorities": ["remote flexibility"]}, user.id)
    offer_b = create_offer_review(db, item, {"application_id": app.id, "salary": 120, "currency": "EUR", "working_hours": "Full time", "user_priorities": ["learning"]}, user.id)
    comparison = compare_offer_reviews(db, item, {"offer_review_ids": [offer_a["id"], offer_b["id"]], "user_priorities": ["remote flexibility", "learning"]})
    assert comparison["winner"] is None
    assert len(comparison["offers"]) == 2
