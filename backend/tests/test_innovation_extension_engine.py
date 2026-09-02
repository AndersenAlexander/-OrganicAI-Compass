from datetime import datetime, timedelta
from app.core.time import utc_now_naive

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.career_resilience import CareerHypothesis
from app.models.innovation_extension import (
    AdvisorComment,
    BrowserJobCapture,
    CareerDecisionJournalEntry,
    CareerDecisionJournalVersion,
    CareerRoleProfile,
)
from app.models.interview_journey import Interview, MockInterviewSession
from app.models.market_application import JobAnalysis, JobRequirement
from app.models.profile import Profile
from app.models.roadmap_adaptation import RoadmapAction
from app.models.user import User
from app.services.innovation_extension_engine import (
    add_panel_turn,
    advisor_review,
    career_role_compare,
    complete_panel_session,
    confirm_job_capture,
    create_advisor_share,
    create_extension_connection,
    create_job_capture,
    create_journal_entry,
    create_panel_session,
    delete_innovation_extension_for_profiles,
    journal_research_export_preview,
    list_career_roles,
    record_journal_outcome,
    respond_to_advisor_comment,
    revoke_advisor_share,
    revoke_extension_connection,
    save_career_hypothesis,
    submit_advisor_comment,
    sync_career_encyclopedia,
    validate_extension_token,
)


def session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def profile(db: Session) -> tuple[User, Profile]:
    user = User(name="Innovation User", email="innovation@example.test", hashed_password="x")
    db.add(user)
    db.flush()
    item = Profile(user_id=user.id, diagnostic_id="diagnostic", data={"primary_archetype": {"name": "Curious Builder"}})
    db.add(item)
    db.commit()
    return user, item


def interview_context(db: Session) -> tuple[User, Profile, Interview]:
    user, item = profile(db)
    analysis = JobAnalysis(profile_id=item.id, user_id=user.id, title="AI Product Designer", organisation="Fictional Studio", raw_text_excerpt="UX and API integration.")
    db.add(analysis)
    db.flush()
    db.add(JobRequirement(analysis_id=analysis.id, profile_id=item.id, requirement_text="UX design and responsible AI", requirement_category="skills", requirement_type="mandatory", normalised_skill_id="ux_ui", user_confirmation_state="confirmed", order_index=1))
    db.add(JobRequirement(analysis_id=analysis.id, profile_id=item.id, requirement_text="API integration", requirement_category="technology", requirement_type="mandatory", normalised_skill_id="apis", user_confirmation_state="confirmed", order_index=2))
    interview = Interview(profile_id=item.id, user_id=user.id, job_analysis_id=analysis.id, role="AI Product Designer", organisation="Fictional Studio", stage_type="panel", stage_order=1)
    db.add(interview)
    db.commit()
    return user, item, interview


def test_extension_token_lifecycle_capture_sanitisation_duplicate_private_url_and_analyse_flow():
    db = session()
    user, item = profile(db)
    connection = create_extension_connection(db, item, {"expires_in_days": 7}, user.id)
    token = connection["connection_token"]
    row = validate_extension_token(db, item, token)

    capture = create_job_capture(
        db,
        item,
        {
            "source_url": "https://jobs.example.test/roles/ai-product-designer",
            "page_title": "AI Product Designer - Example Studio",
            "captured_text": "<section>Mandatory requirements include UX design, responsible AI, accessibility and API integration.</section>",
            "selected_text": "UX design and responsible AI",
            "capture_method": "user_triggered_browser_extension",
            "requested_action": "save_and_analyse",
            "extension_version": "0.1.0",
        },
        row,
        user.id,
    )
    duplicate = create_job_capture(
        db,
        item,
        {
            "source_url": "https://jobs.example.test/roles/ai-product-designer",
            "page_title": "AI Product Designer - Example Studio",
            "captured_text": "<section>Mandatory requirements include UX design, responsible AI, accessibility and API integration.</section>",
            "selected_text": "UX design and responsible AI",
            "capture_method": "user_triggered_browser_extension",
            "requested_action": "save_and_analyse",
        },
        row,
        user.id,
    )

    assert capture["status"] == "Needs review"
    assert capture["job_analysis_id"] is None
    assert capture["source_type"] == "BROWSER_CAPTURE"
    assert capture["review_required"] is True
    assert "<section>" not in capture["sanitised_text"]
    assert duplicate["status"] == "Duplicate"
    confirmed = confirm_job_capture(db, item, capture["id"], {"title": "AI Product Designer", "employer": "Example Studio", "sanitised_text": "Edited, user-confirmed job content.", "analyse": True}, user.id)
    assert confirmed["status"] == "Analysed"
    assert confirmed["job_analysis_id"]
    assert confirmed["user_edited_text"] is True
    assert db.get(JobAnalysis, confirmed["job_analysis_id"]).source_url.startswith("https://jobs.example.test")
    assert db.get(JobAnalysis, confirmed["job_analysis_id"]).source_metadata_json["capture_id"] == capture["id"]
    assert db.scalar(select(BrowserJobCapture).where(BrowserJobCapture.profile_id == item.id)).status == "Analysed"

    try:
        create_job_capture(db, item, {"source_url": "http://127.0.0.1/private", "captured_text": "private", "capture_method": "user_triggered_browser_extension"})
        assert False
    except ValueError:
        pass

    connection_row = db.get(type(row), row.id)
    connection_row.expires_at = utc_now_naive() - timedelta(days=1)
    db.commit()
    try:
        validate_extension_token(db, item, token)
        assert False
    except PermissionError:
        pass

    fresh = create_extension_connection(db, item, {}, user.id)
    revoked = revoke_extension_connection(db, item, fresh["id"], user.id)
    assert revoked["status"] == "revoked"
    try:
        validate_extension_token(db, item, fresh["connection_token"])
        assert False
    except PermissionError:
        pass


def test_advisor_share_limits_sections_comments_acceptance_and_profile_mutation():
    db = session()
    user, item = profile(db)
    original_profile_data = dict(item.data)
    share = create_advisor_share(
        db,
        item,
        {
            "adviser_display_name": "Mentor Example",
            "adviser_role": "Mentor",
            "permission_level": "PROPOSE_CHANGE",
            "allowed_sections": ["Evidence Passport", "Job Analysis", "Job Loss fields"],
            "allowed_actions": ["view", "comment", "suggest_changes", "validate_selected_evidence"],
        },
        user.id,
    )
    review = advisor_review(db, share["share_token"])
    comment = submit_advisor_comment(db, share["share_token"], {"comment_text": "This supports the evidence only partially.", "evidence_validation": "Partially supports"})
    edited = respond_to_advisor_comment(db, item, comment["id"], {"decision": "edited", "proposal_payload": {"owner_wording": "Keep the claim bounded."}, "user_response": "Edited for scope."}, user.id)
    accepted = respond_to_advisor_comment(db, item, comment["id"], {"status": "accepted", "user_response": "Accepted as adviser feedback."}, user.id)
    rejected = respond_to_advisor_comment(db, item, comment["id"], {"status": "rejected", "user_response": "Not used for this decision."}, user.id)
    revoked = revoke_advisor_share(db, item, share["id"], user.id)

    assert "Job Loss fields" not in review["allowed_sections"]
    assert review["permission_code"] == "PROPOSE_CHANGE"
    assert review["share_preview"]["included_sections"] == review["allowed_sections"]
    assert "Private transcripts" in review["share_preview"]["excluded_sections"]
    assert edited["version_number"] == 2
    assert accepted["provenance"] == "human_adviser"
    assert rejected["status"] == "rejected"
    assert db.get(Profile, item.id).data == original_profile_data
    assert db.scalar(select(AdvisorComment).where(AdvisorComment.profile_id == item.id)).status == "rejected"
    assert revoked["status"] == "revoked"


def test_panel_interview_reuses_mock_session_and_only_uses_confirmed_requirements():
    db = session()
    _, item, interview = interview_context(db)
    panel = create_panel_session(
        db,
        interview,
        {"personas": ["recruiter", "hiring_manager", "technical_lead"], "delivery_mode": "voice", "sequence_mode": "round_robin", "duration_minutes": 30},
    )
    first_question = panel["questions"][0]
    turn = add_panel_turn(db, db.get(MockInterviewSession, panel["id"]), {"question_id": first_question["id"], "persona_id": first_question["persona_id"], "answer_text": "I can explain a project with evidence, my contribution, testing and limitations.", "response_duration_seconds": 80})
    completed = complete_panel_session(db, db.get(MockInterviewSession, panel["id"]), {"user_reflection": "Technical evidence needs more depth."})
    question_text = " ".join(question["question_text"] for question in panel["questions"])

    assert panel["persona"] == "panel"
    assert panel["delivery_mode"] == "text"
    assert {question["source_type"] for question in panel["questions"]} == {"confirmed_job_requirement"}
    assert "invented requirement" not in question_text.lower()
    assert turn["persona_id"] in {"recruiter", "hiring_manager", "technical_lead"}
    assert completed["feedback"]["personas"]
    assert completed["no_single_opaque_score"] is True
    assert "emotion" in completed["feedback"]["prohibited_inferences"]


def test_career_encyclopedia_has_sixteen_curated_roles_comparison_and_no_salary_claims():
    db = session()
    user, item = profile(db)
    sync = sync_career_encyclopedia(db)
    roles = list_career_roles(db)
    searched = list_career_roles(db, search="AI Product Designer")
    comparison = career_role_compare(db, item, "ai-product-designer")
    hypothesis = save_career_hypothesis(db, item, "ai-product-designer", user.id)
    payload = str(roles).lower()

    assert sync["role_count"] >= 16
    assert len(roles) >= 16
    assert [role["slug"] for role in searched] == ["ai-product-designer"]
    assert roles[0]["curated_status"] == "CURATED REFERENCE"
    assert roles[0]["market_data_status"] == "NOT LIVE MARKET DATA"
    assert {role["career_family"] for role in roles} >= {"AI and software", "Design and product", "Consulting and strategy", "Learning and communication"}
    assert "salary" in roles[0]["profile"]["known_uncertainties"][2].lower()
    assert "future-proof" not in payload
    assert "salary figures" not in payload
    assert set(comparison["fit_dimensions"].keys()) == {"Personal Fit", "Capability Fit", "Market Fit", "Support Fit"}
    assert hypothesis["created"] is True
    assert db.scalar(select(CareerHypothesis).where(CareerHypothesis.profile_id == item.id)).role_template_id == "ai-product-designer"
    assert db.scalar(select(CareerRoleProfile).where(CareerRoleProfile.slug == "ai-product-designer")).status == "Curated"


def test_decision_journal_versions_outcome_privacy_export_and_reset_delete():
    db = session()
    user, item = profile(db)
    entry = create_journal_entry(
        db,
        item,
        {
            "title": "Test AI Product Designer",
            "decision_summary": "Choose a direction to test.",
            "assumptions": [{"text": "Design evidence is stronger", "state": "testing"}],
            "review_date": "2026-08-15",
        },
        user.id,
    )
    outcome = record_journal_outcome(
        db,
        item,
        entry["id"],
        {
            "expected_outcome": "The experiment clarifies fit.",
            "actual_outcome": "It clarified one technical gap.",
            "assumptions_disconfirmed": ["API evidence was weaker than expected."],
            "next_decision_needed": True,
        },
        user.id,
    )
    export = journal_research_export_preview(db, item)
    roadmap_count = db.scalar(select(RoadmapAction).where(RoadmapAction.profile_id == item.id))

    assert outcome["status"] == "reconsidered"
    assert outcome["version_number"] == 2
    assert len(outcome["versions"]) == 2
    assert db.scalar(select(CareerDecisionJournalVersion).where(CareerDecisionJournalVersion.entry_id == entry["id"], CareerDecisionJournalVersion.version_number == 1)).snapshot_json["outcome"] == {}
    assert export["raw_journal_text_included"] is False
    assert "decision_summary" in export["excluded_fields"]
    assert roadmap_count is None

    delete_innovation_extension_for_profiles(db, [item.id])
    db.commit()
    assert db.scalar(select(CareerDecisionJournalEntry).where(CareerDecisionJournalEntry.profile_id == item.id)) is None

