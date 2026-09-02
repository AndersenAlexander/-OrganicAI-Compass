from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine

from app.database import Base
from app.models.assessment import AssessmentSession, CareerMatch
from app.models.market_application import (
    ApplicationDocument,
    ApplicationDocumentVersion,
    ApplicationRecalibrationRun,
    DocumentClaim,
    JobApplication,
    JobRequirement,
    JobPosting,
    JobPostingVersion,
    LabourMarketSyncRun,
    ResearchParticipant,
)
from app.models.profile import Profile
from app.models.roadmap_adaptation import RoadmapAction
from app.models.user import User
from app.services.assessment_engine import complete_assessment_session, upsert_responses
from app.services.demo_seed_service import demo_assessment_responses, restore_demo
from app.services.market_application_engine import (
    add_application_stage,
    add_document_claim,
    calculate_job_readiness,
    confirm_job_analysis,
    create_application,
    create_application_document,
    create_document_version,
    create_job_analysis,
    create_research_export,
    create_research_session,
    demo_job_catalogue,
    ensure_research_study,
    export_document,
    market_radar,
    match_analysis_evidence,
    normalise_skill_terms,
    list_jobs,
    providers_status,
    recalibrate_from_application,
    consent_to_research,
    record_application_outcome,
    record_research_metrics,
    record_research_responses,
    require_analysis,
    require_research_session,
    require_study,
    sync_demo_labour_market,
    upsert_job_event,
    update_document_claim,
    update_requirement,
    upsert_market_preferences,
)


def session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def profile(db: Session) -> tuple[User, Profile]:
    user = User(name="Market User", email="market@example.test", hashed_password="x")
    db.add(user)
    db.flush()
    item = Profile(user_id=user.id, diagnostic_id="diagnostic", data={"primary_archetype": {"name": "Curious Builder"}})
    db.add(item)
    db.commit()
    return user, item


def complete_demo_assessment(db: Session) -> tuple[User, Profile, CareerMatch]:
    user, item = profile(db)
    assessment = AssessmentSession(profile_id=item.id, user_id=user.id, mode="complete", status="in_progress", consent_accepted=True)
    db.add(assessment)
    db.flush()
    upsert_responses(db, assessment, demo_assessment_responses())
    result = complete_assessment_session(db, assessment, item)
    assert result["status"] == "completed"
    match = db.scalar(select(CareerMatch).where(CareerMatch.profile_id == item.id, CareerMatch.role_template_id == "human_centred_ai_product_designer"))
    assert match is not None
    return user, item, match


def test_demo_provider_sync_is_idempotent_and_keeps_inactive_jobs_out_of_active_results():
    db = session()
    first = sync_demo_labour_market(db)
    second = sync_demo_labour_market(db)
    status = providers_status(db)

    assert first["status"] == "completed"
    assert second["status"] == "completed"
    assert db.scalar(select(func.count()).select_from(JobPosting)) == len(demo_job_catalogue())
    assert db.scalar(select(func.count()).select_from(JobPostingVersion)) == len(demo_job_catalogue())
    assert db.scalar(select(func.count()).select_from(LabourMarketSyncRun)) >= 2
    assert status["active_provider"] == "demo"
    assert status["live_enabled"] is False
    assert any(provider["status"] in {"ready", "degraded"} for provider in status["providers"])

    _, item, _ = complete_demo_assessment(db)
    radar = market_radar(db, item, {"active_only": True, "limit": 50})
    assert radar["active_jobs"]
    assert all(job["is_active"] for job in radar["active_jobs"])
    assert not any("market_score" in str(job).lower() for job in radar["active_jobs"])


def test_market_preferences_filters_and_esco_fallback_are_explicitly_labelled():
    db = session()
    _, item, _ = complete_demo_assessment(db)
    preference = upsert_market_preferences(
        db,
        item,
        {
            "country": "Norway",
            "municipality": "Oslo",
            "work_modes": ["hybrid", "remote"],
            "preferred_languages": ["English"],
            "career_families": ["ai_product"],
            "user_confirmed_storage": True,
        },
    )
    radar = market_radar(db, item, {"municipality": "Oslo", "career_family": "ai_product", "active_only": True, "limit": 20})
    mapping = normalise_skill_terms(db, ["UX", "unknown specialised skill"])

    assert preference["user_confirmed_storage"] is True
    assert preference["municipality"] == "Oslo"
    assert radar["active_jobs"]
    assert all(job["municipality"] == "Oslo" for job in radar["active_jobs"])
    assert radar["recurring_requirements"]
    assert mapping["provider"] in {"disabled", "local", "web"}
    assert any(item["status"] in {"fallback_raw_term", "local_alias"} for item in mapping["mappings"])


def test_provider_provenance_deduplicates_results_but_preserves_source_records():
    db = session()
    base = {
        "title": "Evidence Product Designer",
        "employer": "Example Studio",
        "description": "Required UX design and responsible AI.",
        "source_url": "https://jobs.example.test/vacancies/evidence-product-designer",
        "publication_time": "2026-08-10T09:00:00",
        "last_provider_update": "2026-08-18T09:00:00",
        "is_active": True,
        "country": "Norway",
        "municipality": "Oslo",
        "work_mode": "hybrid",
        "extracted_skills": ["UX"],
        "career_families": ["AI Product"],
    }
    first, _ = upsert_job_event(db, {**base, "provider": "provider-a", "external_job_id": "a-1"})
    second, _ = upsert_job_event(db, {**base, "provider": "provider-b", "external_job_id": "b-1"})
    db.commit()

    jobs = list_jobs(db, None, {"demo_mode": False, "limit": 10})

    assert first is not None and second is not None
    assert first.canonical_job_key == second.canonical_job_key
    assert len(jobs) == 1
    assert jobs[0]["deduplication"]["source_count"] == 2
    assert {item["provider"] for item in jobs[0]["source_provenance"]} == {"provider-a", "provider-b"}


def test_requirements_need_confirmation_before_authoritative_mapping_and_readiness():
    db = session()
    user, item, _ = complete_demo_assessment(db)
    created = create_job_analysis(
        db,
        item,
        {
            "input_type": "pasted_text",
            "title": "Evidence Product Designer",
            "pasted_text": "Mandatory UX design and accessibility experience. Preferred Norwegian language and portfolio evidence.",
        },
    )
    analysis = require_analysis(db, created["id"], item)
    initial = calculate_job_readiness(db, analysis)

    assert initial["requires_user_confirmation"] is True
    assert all(match["evidence_status"] == "NOT ASSESSED" for match in match_analysis_evidence(db, analysis)["matches"])

    for requirement in db.scalars(select(JobRequirement).where(JobRequirement.analysis_id == analysis.id)).all():
        update_requirement(db, requirement, {"action": "accept", "requirement_type": requirement.requirement_type}, user.id)
    reviewed = calculate_job_readiness(db, analysis)
    assert analysis.user_confirmed is False
    assert reviewed["requires_user_confirmation"] is True
    confirmed = confirm_job_analysis(db, analysis, user.id)
    authoritative_matches = match_analysis_evidence(db, analysis)
    ready = calculate_job_readiness(db, analysis)

    assert confirmed["user_confirmed"] is True
    assert all(match["match_category"] != "Needs user confirmation" for match in authoritative_matches["matches"])
    assert ready["requires_user_confirmation"] is False
    assert "source_limitations" in ready["explanation"]


def test_job_analyser_extracts_correctable_requirements_and_deterministic_readiness():
    db = session()
    _, item, _ = complete_demo_assessment(db)
    analysis = create_job_analysis(
        db,
        item,
        {
            "input_type": "pasted_text",
            "title": "AI Product Role",
            "organisation": "Example Studio",
            "pasted_text": "Responsibilities include facilitating design research with product teams. Mandatory requirements include Python and three years experience. Preferred requirements include a portfolio. Preferred requirement: stakeholder communication. Preferred certification in accessibility is useful.",
        },
    )
    row = require_analysis(db, analysis["id"], item)
    match = match_analysis_evidence(db, row)
    readiness = calculate_job_readiness(db, row)
    requirements = row_requirements(db, row.id)
    requirement = requirements[0]
    corrected = update_requirement(
        db,
        requirement,
        {"requirement_text": "UX design with accessibility evidence", "user_confirmation_state": "confirmed", "change_reason": "User correction."},
        item.user_id,
    )

    assert analysis["requirements"]
    assert analysis["structured_output"]["responsibilities"] == ["Responsibilities include facilitating design research with product teams."]
    assert {item["requirement_type"] for item in analysis["requirements"]} == {"mandatory", "preferred"}
    assert {item["requirement_category"] for item in analysis["requirements"]}.issuperset({"experience", "portfolio", "soft_skills", "certifications"})
    assert all(item["source_excerpt"] and item["source_location"] for item in analysis["requirements"])
    assert len({item["requirement_text"].lower() for item in analysis["requirements"]}) == len(analysis["requirements"])
    assert match["matches"]
    assert readiness["readiness_label"] == "Insufficient information"
    assert corrected["user_confirmation_state"] == "confirmed"

    try:
        create_job_analysis(db, item, {"input_type": "url", "source_url": "http://127.0.0.1/private"})
        assert False
    except ValueError:
        pass


def test_application_documents_block_unsupported_claims_and_export_only_after_warning_acknowledgement():
    db = session()
    _, item, _ = complete_demo_assessment(db)
    sync_demo_labour_market(db)
    job = db.scalar(select(JobPosting).where(JobPosting.is_active.is_(True)).order_by(JobPosting.publication_time.desc()))
    analysis = create_job_analysis(db, item, {"job_id": job.id})
    row = require_analysis(db, analysis["id"], item)
    match_analysis_evidence(db, row)
    document = create_application_document(db, item, {"job_analysis_id": row.id, "document_type": "cv"})
    document_row = db.get(ApplicationDocument, document["id"])
    blocked = [claim for claim in document["claims"] if claim["blocked_for_export"]]

    assert blocked
    try:
        export_document(db, document_row)
        assert False
    except ValueError:
        pass

    for claim in document["claims"]:
        if claim["blocked_for_export"]:
            update_document_claim(db, db.get(DocumentClaim, claim["id"]), {"claim_text": claim["safer_alternative"], "status": "User-confirmed", "user_confirmation_state": "confirmed"})

    exported = export_document(db, document_row, {"confirm_blocked_claim_export": True})
    assert exported["auto_apply"] is False
    assert exported["ats_guarantee"] is False
    assert "structured_json" in exported


def test_evidence_lock_blocks_high_risk_claims_and_preserves_document_versions():
    db = session()
    _, item, _ = complete_demo_assessment(db)
    document = create_application_document(db, item, {"document_type": "cover_letter"})
    document_row = db.get(ApplicationDocument, document["id"])

    for claim_text in [
        "I led enterprise AI transformation.",
        "I managed a cross-functional team of 20.",
        "I increased revenue by 35%.",
    ]:
        claim = add_document_claim(db, document_row, {"claim_text": claim_text, "claim_type": "manual"})
        assert claim["status"] == "Blocked"
        assert claim["support_state"] == "UNSUPPORTED"
        assert claim["blocked_for_export"] is True
        assert "enterprise" not in claim["safer_alternative"].lower()
        assert "revenue" not in claim["safer_alternative"].lower()

    blocked_claim = db.scalar(select(DocumentClaim).where(DocumentClaim.document_id == document_row.id, DocumentClaim.status == "Blocked"))
    try:
        update_document_claim(db, blocked_claim, {"status": "Supported"})
        assert False
    except ValueError:
        pass

    first_version_count = db.scalar(select(func.count()).select_from(ApplicationDocumentVersion).where(ApplicationDocumentVersion.document_id == document_row.id))
    version = create_document_version(db, document_row, "User saved a second review version.")
    assert version["version_number"] == first_version_count + 1
    assert db.scalar(select(func.count()).select_from(ApplicationDocumentVersion).where(ApplicationDocumentVersion.document_id == document_row.id)) == first_version_count + 1


def test_application_outcome_recalibration_creates_suggestions_without_roadmap_changes():
    db = session()
    _, item, _ = complete_demo_assessment(db)
    sync_demo_labour_market(db)
    job = db.scalar(select(JobPosting).where(JobPosting.is_active.is_(True)).order_by(JobPosting.publication_time.desc()))
    analysis = create_job_analysis(db, item, {"job_id": job.id})
    analysis_row = require_analysis(db, analysis["id"], item)
    try:
        create_application(db, item, {"job_id": job.id, "job_analysis_id": analysis["id"], "status": "Preparing"})
        assert False
    except ValueError:
        pass
    for requirement in row_requirements(db, analysis_row.id):
        update_requirement(db, requirement, {"action": "accept"}, item.user_id)
    confirm_job_analysis(db, analysis_row, item.user_id)
    cv = create_application_document(db, item, {"job_analysis_id": analysis["id"], "document_type": "cv"})
    cover_letter = create_application_document(db, item, {"job_analysis_id": analysis["id"], "document_type": "cover_letter"})
    cv_text = " ".join(section["content"] for section in cv["sections"])
    cover_letter_text = " ".join(section["content"] for section in cover_letter["sections"])
    assert analysis["title"] in cv_text
    assert analysis["title"] in cover_letter_text
    assert any(requirement["requirement_text"] in cv_text for requirement in analysis["requirements"])
    assert any(requirement["requirement_text"] in cover_letter_text for requirement in analysis["requirements"])
    app = create_application(
        db,
        item,
        {
            "job_id": job.id,
            "job_analysis_id": analysis["id"],
            "cv_document_id": cv["id"],
            "cover_letter_document_id": cover_letter["id"],
            "status": "Preparing",
        },
    )
    app_row = db.get(JobApplication, app["id"])
    before_roadmap_count = db.scalar(select(func.count()).select_from(RoadmapAction).where(RoadmapAction.profile_id == item.id)) or 0
    profile_data_before = dict(item.data)

    add_application_stage(db, app_row, {"stage_type": "recruiter"})
    assert app_row.status == "Preparing"
    assert app["job_analysis_id"] == analysis["id"]
    assert app["cv_document_id"] == cv["id"]
    assert app["cover_letter_document_id"] == cover_letter["id"]
    assert app["confirmed_job_analysis_version"] == "job-analysis-v1"
    assert app["readiness_snapshot"]
    assert app["evidence_snapshot"]

    outcome = record_application_outcome(db, app_row, {"outcome": "Recruiter screening", "outcome_date": "2026-07-21", "feedback_confirmed": False})
    recalibration = recalibrate_from_application(db, app_row)
    after_roadmap_count = db.scalar(select(func.count()).select_from(RoadmapAction).where(RoadmapAction.profile_id == item.id)) or 0

    assert outcome["employer_feedback"] == ""
    assert recalibration["suggestions"]
    assert recalibration["roadmap_changes_require_confirmation"] is True
    assert db.scalar(select(func.count()).select_from(ApplicationRecalibrationRun).where(ApplicationRecalibrationRun.profile_id == item.id)) == 1
    assert before_roadmap_count == after_roadmap_count
    assert item.data == profile_data_before


def test_research_consent_sessions_and_export_are_pseudonymous_and_versioned():
    db = session()
    _, item, _ = complete_demo_assessment(db)
    study = ensure_research_study(db)
    study_row = require_study(db, study["id"])
    consent = consent_to_research(db, study_row, item, {"consent_given": True})
    session_payload = create_research_session(db, study_row, item, {"workflow_stage": "post_test", "workflow": "experimental"})
    session_row = require_research_session(db, session_payload["id"], item)
    questions = study["questions"][:6]
    record_research_responses(db, session_row, {"responses": [{"question_id": question["id"], "numeric_response": 4, "workflow_stage": "post_test"} for question in questions], "complete_session": True})
    record_research_metrics(db, session_row, {"metrics": [{"metric_name": "job_analysed", "metric_value": 1, "workflow_stage": "post_test"}]})
    export = create_research_export(db, study_row)
    payload = export["preview"]

    assert consent["consent_given"] is True
    assert payload["schema_version"]
    assert payload["participant_summary"]
    assert "raw_cv_text" in payload["excluded_fields"]
    assert "market@example.test" not in str(payload)
    assert db.scalar(select(func.count()).select_from(ResearchParticipant).where(ResearchParticipant.profile_id == item.id)) == 1


def test_demo_reset_seeds_market_application_records():
    db = session()
    _, profile, _ = restore_demo(db)
    assert db.scalar(select(func.count()).select_from(JobApplication).where(JobApplication.profile_id == profile.id)) >= 3
    assert db.scalar(select(func.count()).select_from(ApplicationDocument).where(ApplicationDocument.profile_id == profile.id)) >= 2


def row_requirements(db: Session, analysis_id: str):
    return db.scalars(select(JobRequirement).where(JobRequirement.analysis_id == analysis_id).order_by(JobRequirement.order_index)).all()
