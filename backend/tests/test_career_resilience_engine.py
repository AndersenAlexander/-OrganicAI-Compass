from fastapi import HTTPException
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.assessment import AssessmentSession, CareerMatch, SkillEvidence
from app.models.career_resilience import (
    CareerEvidenceGap,
    CareerEvidenceProposal,
    CareerExperimentReview,
    CareerExperimentResult,
    CareerExperimentSession,
    CareerHypothesis,
    CareerHypothesisVersion,
    ImmediateActionPlan,
    JobLossProfile,
    SkillEvidenceConfidence,
    SkillEvidenceSource,
    SkillRecency,
    SupportProgrammeVersion,
    SupportScreening,
    SupportedPathRun,
)
from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.models.roadmap_adaptation import RoadmapAction, RoadmapEvent, RoadmapVersion
from app.models.user import User
from app.routers.career_resilience import require_profile
from app.services.assessment_engine import complete_assessment_session, upsert_responses
from app.services.career_resilience_engine import (
    add_manual_evidence,
    create_experiment_session,
    confirm_experiment_roadmap,
    create_immediate_action_plan,
    create_supported_paths,
    evaluate_experiment,
    evidence_passport,
    ensure_hypotheses_from_matches,
    list_experiment_templates,
    list_profile_evidence_gaps,
    list_support_programmes,
    recalibrate_career_recommendations,
    run_support_screening,
    safe_official_url,
    self_review_experiment,
    start_experiment,
    submit_experiment,
    sync_career_resilience_catalogue,
    upsert_job_loss_profile,
)
from app.services.roadmap_adaptation import roadmap_public
from app.services.demo_seed_service import demo_assessment_responses, restore_demo


HUMAN_REVIEW_SKILLS = {"ux_ui", "responsible_ai", "product_thinking", "risk_reasoning", "communication"}


def completed_human_review_experiment(db: Session):
    user, item, match = complete_demo_assessment(db)
    # The test creates a deliberately unrelated intended gap. The human-review
    # rubric must not convert it into observed ideation evidence.
    gap = CareerEvidenceGap(
        profile_id=item.id,
        user_id=user.id,
        career_match_id=match.id,
        skill_id="ideation",
        capability_label="Ideation",
        status="MISSING",
        current_evidence_status="MISSING",
        reason="No direct ideation evidence is stored.",
    )
    db.add(gap)
    db.commit()
    created = create_experiment_session(
        db,
        item,
        {
            "experiment_template_id": "ai-product-human-review-flow",
            "career_match_id": match.id,
            "evidence_gap_id": gap.id,
            "mode": "guided",
            "user_confirmed": True,
        },
        user.id,
    )
    experiment = db.get(CareerExperimentSession, created["id"])
    start_experiment(db, experiment)
    submit_experiment(
        db,
        experiment,
        {
            "text_response": "Designed a user journey and prototype for a human review flow with review states, override and correction controls, transparent explanations, accessibility, risk boundaries, stakeholder communication, validation checklist, product rationale, and limitations.",
            "project_url": "https://example.test/human-review-flow",
            "completion_notes": "Completed human review flow with a reviewable prototype and documented risk reasoning.",
            "time_spent_minutes": 150,
            "reflection": {"note": "The review flow surfaced remaining ideation evidence needs."},
        },
    )
    return user, item, match, gap, experiment, evaluate_experiment(db, experiment)


def adaptive_ai_product_context(db: Session):
    """Create the exact evidence state used by the adaptive recommendation tests."""
    user, item, match, _, experiment, _ = completed_human_review_experiment(db)
    match.missing_skills_json = sorted(HUMAN_REVIEW_SKILLS | {"ideation"})
    db.commit()
    hypotheses = ensure_hypotheses_from_matches(db, item)
    hypothesis = next(row for row in hypotheses if row.career_match_id == match.id)
    return user, item, match, hypothesis, experiment


def adaptive_recommendation(db: Session, user: User, item: Profile, match: CareerMatch) -> dict:
    return create_experiment_session(
        db,
        item,
        {"career_match_id": match.id, "mode": "guided", "user_confirmed": True},
        user.id,
    )


def completed_ideation_sprint(db: Session):
    """Run the direct, high-evidence Ideation path used by the end-to-end loop."""
    user, item, match, hypothesis, _ = adaptive_ai_product_context(db)
    created = adaptive_recommendation(db, user, item, match)
    assert created["experiment_template_id"] == "ai-product-concept-generation-sprint"
    experiment = db.get(CareerExperimentSession, created["id"])
    start_experiment(db, experiment)
    submit_experiment(
        db,
        experiment,
        {
            "text_response": (
                "Problem: first-time jobseekers struggle to understand why an AI career assistant suggests a next step. "
                "The user need is a clear, controllable explanation, and the AI opportunity is a bounded feature that turns a recommendation into reviewable choices. "
                "Concept 1 is an explanation card that shows the top evidence signals and lets the user ask for a simpler explanation. "
                "Concept 2 is a comparison workspace that places two career directions beside each other with their evidence limits. "
                "Concept 3 is a next-step planner that lets the user select one small experiment while keeping a human override. "
                "I created a comparison matrix to compare user value, implementation effort, and safety. The trade-off is that the planner gives immediate action but can hide uncertainty, while the comparison workspace is slower but more transparent. "
                "I selected Concept 2 because it keeps the user in control and makes uncertainty visible. The first release scope is one comparison of two roles with three visible evidence signals. "
                "A delivery constraint is that live labour-market data is unavailable, so the design labels curated data clearly. Human control means the user can reject, save, or request another comparison. "
                "I will validate the concept by testing the comparison with three jobseekers and asking whether they can explain the trade-off before choosing. "
                "Reflection: this sprint demonstrates structured ideation and selection, but it does not demonstrate a production build or long-term market fit."
            ),
            "project_url": "https://example.test/ideation-sprint",
            "completion_notes": "Completed an AI concept comparison sprint with a bounded selected concept and validation plan.",
            "time_spent_minutes": 120,
            "reflection": {"note": "The sprint produced direct evidence of ideation while leaving real-world delivery and market evidence open."},
        },
    )
    self_review_experiment(db, experiment, {"reflection": "I compared alternatives before selecting the bounded concept.", "self_rated_difficulty": 3, "self_rated_enjoyment": 4})
    evaluated = evaluate_experiment(db, experiment)
    return user, item, match, hypothesis, experiment, evaluated


def session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def profile(db: Session) -> tuple[User, Profile]:
    user = User(name="Resilience User", email="resilience@example.test", hashed_password="x")
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


def test_experiment_template_retrieval_has_thirteen_templates_and_four_families():
    db = session()
    templates = list_experiment_templates(db)
    assert len(templates) == 13
    assert {item["target_role_family"] for item in templates} == {
        "AI Product Designer",
        "AI Integration Consultant",
        "RAG Application Developer",
        "Learning Experience Designer",
    }
    assert all(item["source_metadata"]["source_type"] == "curated_role_experiment" for item in templates)


def test_practically_verified_skills_are_removed_from_unresolved_gaps():
    db = session()
    _, item, _, hypothesis, _ = adaptive_ai_product_context(db)

    gaps = list_profile_evidence_gaps(db, item, hypothesis.id)["gaps"]
    assert {gap["skill_id"] for gap in gaps} == {"ideation"}
    assert all(gap["skill_id"] not in HUMAN_REVIEW_SKILLS for gap in gaps)


def test_ideation_remains_an_unresolved_gap_after_human_review_evidence():
    db = session()
    _, item, _, hypothesis, _ = adaptive_ai_product_context(db)

    gaps = list_profile_evidence_gaps(db, item, hypothesis.id)["gaps"]
    ideation = next(gap for gap in gaps if gap["skill_id"] == "ideation")
    assert ideation["status"] in {"MISSING", "SELF_REPORT_ONLY"}
    assert ideation["gap_kind"] == "evidence_gap"


def test_adaptive_recommendation_prioritizes_ideation_coverage_when_available():
    db = session()
    user, item, match, _, _ = adaptive_ai_product_context(db)

    recommended = adaptive_recommendation(db, user, item, match)

    assert recommended["template"]["id"] == "ai-product-concept-generation-sprint"
    assert recommended["recommendation"]["targeted_gap_skill_ids"] == ["ideation"]
    assert "Tests unresolved gap: Ideation." in recommended["recommendation"]["rationale"]
    assert recommended["expected_evidence_gain"] == "High"


def test_completed_human_review_flow_receives_redundancy_and_duplicate_penalties():
    db = session()
    user, item, match, _, _ = adaptive_ai_product_context(db)

    recommended = adaptive_recommendation(db, user, item, match)
    ranking = recommended["recommendation"]
    human_review_index = ranking["ranked_template_ids"].index("ai-product-human-review-flow")
    human_review = next(item for item in ranking["ranked_candidates"] if item["template_id"] == "ai-product-human-review-flow")

    assert human_review_index > 0
    assert {"ux_ui", "responsible_ai", "product_thinking", "risk_reasoning"}.issubset(
        set(ranking["already_practically_verified_skill_ids"])
    )
    assert human_review["score_breakdown"]["redundant_evidence_penalty"] > 0
    assert human_review["score_breakdown"]["duplicate_experiment_penalty"] > 0
    # The selected recommendation is stored, while its ordered ranking makes
    # the avoided duplicate externally inspectable without an LLM rationale.
    assert "ai-product-human-review-flow" != recommended["template"]["id"]


def test_recommendation_is_deterministic_when_evidence_is_unchanged():
    db = session()
    user, item, match, _, _ = adaptive_ai_product_context(db)

    first = adaptive_recommendation(db, user, item, match)
    second = adaptive_recommendation(db, user, item, match)

    assert second["template"]["id"] == first["template"]["id"]
    assert second["recommendation"] == first["recommendation"]


def test_new_relevant_evidence_changes_the_recommendation_ranking():
    db = session()
    user, item, match, _, _ = adaptive_ai_product_context(db)
    before = adaptive_recommendation(db, user, item, match)

    add_manual_evidence(
        db,
        item,
        {
            "skill_id": "ideation",
            "evidence_type": "practical_exercise",
            "title": "AI concept comparison exercise",
            "description": "Generated, compared, and selected AI feature concepts with clear trade-offs.",
            "score_hint": 90,
        },
    )
    after = adaptive_recommendation(db, user, item, match)

    assert before["template"]["id"] == "ai-product-concept-generation-sprint"
    assert "ideation" not in after["recommendation"]["unresolved_gap_skill_ids"]
    assert after["status"] == "evidence_sufficient"
    assert after["recommendation"]["state"] == "evidence_sufficient"


def test_direct_ideation_sprint_closes_only_its_linked_gap_and_persists_provenance():
    db = session()
    _, item, match, hypothesis, experiment, evaluated = completed_ideation_sprint(db)

    ideation_scores = [item for item in evaluated["result"]["criteria_scores"] if item["skill_id"] == "ideation"]
    assert {item["criterion_id"] for item in ideation_scores} == {"task_understanding", "deliverable_quality", "reasoning_clarity"}
    assert all(item["rating"] == 4 for item in ideation_scores)
    assert evaluated["template"]["evaluation_rubric"]["criteria"]
    assert evaluated["result"]["linked_gap"]["remaining_unresolved"] is False
    assert "practically verified" in evaluated["result"]["linked_gap"]["message"].lower()

    result = db.get(CareerExperimentResult, evaluated["result"]["id"])
    source = next(
        (
            row
            for row in db.scalars(
                select(SkillEvidenceSource).where(
                    SkillEvidenceSource.profile_id == item.id,
                    SkillEvidenceSource.source_type == "DETERMINISTIC_CAREER_EXPERIMENT",
                    SkillEvidenceSource.source_id == result.id,
                )
            ).all()
            if (row.source_metadata_json or {}).get("skill_id") == "ideation"
        ),
        None,
    )
    assert source is not None
    provenance = source.source_metadata_json
    assert provenance["canonical_direction_id"] == hypothesis.canonical_direction_id
    assert provenance["hypothesis_id"] == hypothesis.id
    assert provenance["experiment_session_id"] == experiment.id
    assert provenance["submission_id"] == result.submission_id
    assert provenance["deterministic_review_id"] == evaluated["result"]["persistence"]["review_id"]
    assert provenance["deterministic_score"] == 100.0
    assert provenance["provenance_label"] == "Verified through career experiment: Run an AI Feature Concept Generation Sprint"

    source_count_before_retry = db.scalar(
        select(func.count()).select_from(SkillEvidenceSource).where(
            SkillEvidenceSource.profile_id == item.id,
            SkillEvidenceSource.source_type == "DETERMINISTIC_CAREER_EXPERIMENT",
            SkillEvidenceSource.source_id == result.id,
        )
    )
    retried = evaluate_experiment(db, db.get(CareerExperimentSession, experiment.id))
    assert retried["result"]["id"] == result.id
    assert db.scalar(
        select(func.count()).select_from(SkillEvidenceSource).where(
            SkillEvidenceSource.profile_id == item.id,
            SkillEvidenceSource.source_type == "DETERMINISTIC_CAREER_EXPERIMENT",
            SkillEvidenceSource.source_id == result.id,
        )
    ) == source_count_before_retry

    passport = evidence_passport(db, item.id)
    ideation = next(skill for skill in passport["skills"] if skill["skill_id"] == "ideation")
    assert ideation["strongest_evidence_label"] == "Practically verified"
    assert ideation["evidence_confidence"] == "Strong evidence"
    assert any(
        item["source_type"] == "DETERMINISTIC_CAREER_EXPERIMENT"
        and item["experiment_session_id"] == experiment.id
        and item["provenance_label"] == "Verified through career experiment: Run an AI Feature Concept Generation Sprint"
        for evidence in ideation["evidence_sources"]
        for item in evidence["sources"]
    )

    before_dimensions = dict((db.get(CareerMatch, match.id).source_metadata_json or {})["hypothesis_dimensions"]["scores"])
    run = recalibrate_career_recommendations(db, item, result.id)
    assert run["status"] == "completed"
    assert run["hypothesis_id"] == hypothesis.id
    assert "ideation" not in db.get(CareerMatch, match.id).missing_skills_json
    after_dimensions = (db.get(CareerMatch, match.id).source_metadata_json or {})["hypothesis_dimensions"]["scores"]
    assert after_dimensions["evidence_strength"] >= before_dimensions["evidence_strength"]
    assert after_dimensions["capability_fit"] >= before_dimensions["capability_fit"]
    for dimension in ("natural_fit", "transition_feasibility", "ai_augmentation_opportunity"):
        assert after_dimensions[dimension] == before_dimensions[dimension]
    changes = run["changed_recommendations"][0]["dimension_changes"]
    assert changes["changed_categories"] == ["evidence_strength", "capability_fit"]
    assert changes["unchanged_categories"] == ["natural_fit", "transition_feasibility", "ai_augmentation_opportunity"]
    assert db.get(CareerHypothesis, hypothesis.id).current_version_number == 2
    history = db.scalars(
        select(CareerHypothesisVersion)
        .where(CareerHypothesisVersion.hypothesis_id == hypothesis.id)
        .order_by(CareerHypothesisVersion.version_number)
    ).all()
    assert len(history) == 2
    assert history[0].version_number == 1
    assert history[0].snapshot_json != history[1].snapshot_json
    assert all(item["capability"] != "Ideation" for item in history[1].snapshot_json["missing_evidence"])


def test_completed_ideation_sprint_stops_recommending_duplicate_work_without_a_roadmap_mutation():
    db = session()
    user, item, match, _, experiment, evaluated = completed_ideation_sprint(db)
    before_sessions = db.scalar(select(func.count()).select_from(CareerExperimentSession).where(CareerExperimentSession.profile_id == item.id))
    before_roadmap_actions = db.scalar(select(func.count()).select_from(RoadmapAction).where(RoadmapAction.profile_id == item.id))

    recalibrate_career_recommendations(db, item, evaluated["result"]["id"])
    sufficient = adaptive_recommendation(db, user, item, match)

    assert sufficient["status"] == "evidence_sufficient"
    assert sufficient["recommendation"]["state"] == "evidence_sufficient"
    assert sufficient["recommendation"]["unresolved_gap_skill_ids"] == []
    assert sufficient["recommendation"]["ranked_candidates"]
    sprint = next(item for item in sufficient["recommendation"]["ranked_candidates"] if item["template_id"] == experiment.experiment_template_id)
    assert sprint["score_breakdown"]["redundant_evidence_penalty"] > 0
    assert sprint["score_breakdown"]["duplicate_experiment_penalty"] > 0
    assert db.scalar(select(func.count()).select_from(CareerExperimentSession).where(CareerExperimentSession.profile_id == item.id)) == before_sessions
    assert db.scalar(select(func.count()).select_from(RoadmapAction).where(RoadmapAction.profile_id == item.id)) == before_roadmap_actions


def test_unrelated_career_evidence_does_not_change_this_direction_ranking():
    db = session()
    user, item, match, _, _ = adaptive_ai_product_context(db)
    before = adaptive_recommendation(db, user, item, match)

    add_manual_evidence(
        db,
        item,
        {
            "skill_id": "rag_fundamentals",
            "evidence_type": "practical_exercise",
            "title": "Unrelated RAG exercise",
            "description": "A bounded retrieval exercise for a different career direction.",
            "score_hint": 90,
        },
    )
    after = adaptive_recommendation(db, user, item, match)

    assert after["template"]["id"] == before["template"]["id"]
    assert after["recommendation"] == before["recommendation"]


def test_experiment_lifecycle_requires_confirmation_before_roadmap_and_scores_deterministically():
    db = session()
    user, item, match = complete_demo_assessment(db)
    created = create_experiment_session(
        db,
        item,
        {"experiment_template_id": "ai-product-human-review-flow", "career_match_id": match.id, "mode": "guided", "user_confirmed": True, "add_to_roadmap": False},
        user.id,
    )
    assert created["status"] == "planned"
    assert db.scalar(select(func.count()).select_from(RoadmapAction).where(RoadmapAction.profile_id == item.id, RoadmapAction.source_type == "career_experiment")) == 0
    row = db.get(CareerExperimentSession, created["id"])
    start_experiment(db, row)
    try:
        submit_experiment(db, row, {"completion_notes": "No artifact"})
        assert False
    except ValueError:
        pass
    submit_experiment(
        db,
        row,
        {
            "text_response": "Prototype design with user states, accessibility, explainability, validation checklist, and limitations. The artifact includes correction, rejection, request alternative, and roadmap states for a hypothesis-based recommendation card.",
            "project_url": "https://example.test/project",
            "completion_notes": "Manual submission for deterministic review.",
            "time_spent_minutes": 120,
            "reflection": {"note": "The task was useful and clarified remaining gaps."},
        },
    )
    self_review_experiment(db, row, {"reflection": "Useful task.", "self_rated_difficulty": 3, "self_rated_enjoyment": 4})
    evaluated = evaluate_experiment(db, row)
    assert evaluated["status"] == "evaluated"
    assert evaluated["result"]["overall_score"] > 0
    assert db.scalar(select(func.count()).select_from(CareerExperimentResult).where(CareerExperimentResult.profile_id == item.id)) == 1
    assert db.scalar(select(func.count()).select_from(SkillEvidence).join(SkillEvidenceConfidence, SkillEvidenceConfidence.skill_evidence_id == SkillEvidence.id).where(SkillEvidenceConfidence.profile_id == item.id)) > 0


def test_deterministic_human_review_persists_practical_evidence_with_provenance_and_keeps_self_report():
    db = session()
    user, item, _, gap, experiment, evaluated = completed_human_review_experiment(db)
    add_manual_evidence(
        db,
        item,
        {
            "skill_id": "ux_ui",
            "evidence_type": "self_reported",
            "title": "Earlier self-report",
            "description": "A historical declaration that must remain inspectable.",
            "score_hint": 25,
        },
    )
    # Re-evaluating repairs/persists the deterministic result without removing
    # or rewriting the existing self-report.
    evaluated = evaluate_experiment(db, db.get(CareerExperimentSession, experiment.id))
    result = db.get(CareerExperimentResult, evaluated["result"]["id"])
    sources = db.scalars(
        select(SkillEvidenceSource).where(
            SkillEvidenceSource.profile_id == item.id,
            SkillEvidenceSource.source_type == "DETERMINISTIC_CAREER_EXPERIMENT",
            SkillEvidenceSource.source_id == result.id,
        )
    ).all()

    assert {source.source_metadata_json["skill_id"] for source in sources} == HUMAN_REVIEW_SKILLS
    assert all(source.source_metadata_json["experiment_template_id"] == "ai-product-human-review-flow" for source in sources)
    assert all(source.source_metadata_json["experiment_session_id"] == experiment.id for source in sources)
    assert all(source.source_metadata_json["submission_id"] == result.submission_id for source in sources)
    assert all(source.source_metadata_json["deterministic_review_id"] for source in sources)
    assert all(source.source_metadata_json["deterministic_score"] >= 85 for source in sources)
    assert all(source.source_metadata_json["evidence_classification"] == "Practically verified" for source in sources)
    assert all(source.source_metadata_json["hypothesis_id"] is None or isinstance(source.source_metadata_json["hypothesis_id"], str) for source in sources)
    assert db.scalar(select(func.count()).select_from(SkillEvidence).where(SkillEvidence.title == "Earlier self-report")) == 1

    passport = evidence_passport(db, item.id)
    reviewed = {item["skill_id"]: item for item in passport["skills"] if item["skill_id"] in HUMAN_REVIEW_SKILLS}
    assert set(reviewed) == HUMAN_REVIEW_SKILLS
    assert all(item["strongest_evidence_label"] == "Practically verified" for item in reviewed.values())
    assert all(item["status"] == "Practically verified evidence" for item in reviewed.values())
    ux_titles = {item["title"] for item in reviewed["ux_ui"]["evidence_sources"]}
    assert "Earlier self-report" in ux_titles
    assert any(source["source_type"] == "DETERMINISTIC_CAREER_EXPERIMENT" for item in reviewed.values() for evidence in item["evidence_sources"] for source in evidence["sources"])
    assert db.get(CareerEvidenceGap, gap.id).status == "MISSING"
    assert evaluated["result"]["linked_gap"]["remaining_unresolved"] is True
    assert "did not directly verify the linked Ideation gap" in evaluated["result"]["linked_gap"]["message"]


def test_repeated_deterministic_review_reuses_result_evidence_review_and_proposals():
    db = session()
    _, item, _, _, experiment, first = completed_human_review_experiment(db)
    counts_before = {
        "results": db.scalar(select(func.count()).select_from(CareerExperimentResult).where(CareerExperimentResult.profile_id == item.id)),
        "reviews": db.scalar(select(func.count()).select_from(CareerExperimentReview).where(CareerExperimentReview.session_id == experiment.id, CareerExperimentReview.source_type == "deterministic_rubric")),
        "sources": db.scalar(select(func.count()).select_from(SkillEvidenceSource).where(SkillEvidenceSource.source_type == "DETERMINISTIC_CAREER_EXPERIMENT")),
        "proposals": db.scalar(select(func.count()).select_from(CareerEvidenceProposal).where(CareerEvidenceProposal.experiment_result_id == first["result"]["id"])),
    }

    second = evaluate_experiment(db, db.get(CareerExperimentSession, experiment.id))
    counts_after = {
        "results": db.scalar(select(func.count()).select_from(CareerExperimentResult).where(CareerExperimentResult.profile_id == item.id)),
        "reviews": db.scalar(select(func.count()).select_from(CareerExperimentReview).where(CareerExperimentReview.session_id == experiment.id, CareerExperimentReview.source_type == "deterministic_rubric")),
        "sources": db.scalar(select(func.count()).select_from(SkillEvidenceSource).where(SkillEvidenceSource.source_type == "DETERMINISTIC_CAREER_EXPERIMENT")),
        "proposals": db.scalar(select(func.count()).select_from(CareerEvidenceProposal).where(CareerEvidenceProposal.experiment_result_id == first["result"]["id"])),
    }
    assert second["result"]["id"] == first["result"]["id"]
    assert counts_after == counts_before


def test_recalibration_uses_persisted_deterministic_evidence_after_a_fresh_session():
    db = session()
    _, item, match, _, experiment, evaluated = completed_human_review_experiment(db)
    result = db.get(CareerExperimentResult, evaluated["result"]["id"])
    # Prove recalibration uses the durable evidence sources, not transient
    # criterion JSON returned to the frontend.
    result.criteria_scores_json = []
    db.commit()
    fresh_db = Session(db.get_bind())
    try:
        fresh_profile = fresh_db.get(Profile, item.id)
        run = recalibrate_career_recommendations(fresh_db, fresh_profile, result.id)
        assert run["status"] == "completed"
        assert {item["skill_id"] for item in run["after"]["new_evidence"]} == HUMAN_REVIEW_SKILLS
        assert run["changed_recommendations"]
        assert fresh_db.get(CareerMatch, match.id).alignment_score > match.alignment_score - 1
        passport = evidence_passport(fresh_db, fresh_profile.id)
        assert all(next(skill for skill in passport["skills"] if skill["skill_id"] == skill_id)["strongest_evidence_label"] == "Practically verified" for skill_id in HUMAN_REVIEW_SKILLS)
    finally:
        fresh_db.close()


def test_recalibration_updates_only_the_selected_canonical_direction_and_versions_it():
    db = session()
    user, item, match, _, _, evaluated = completed_human_review_experiment(db)
    unrelated = CareerMatch(
        profile_id=item.id,
        user_id=user.id,
        role_template_id="ux_designer_ai_systems",
        category="reskilling_opportunities",
        title="UX Designer for AI Systems",
        role_family="UX and Digital Experience",
        alignment_score=52.0,
        alignment_label="Developing alignment",
        missing_skills_json=["ideation"],
        source_metadata_json={
            "source_type": "test_snapshot",
            "hypothesis_dimensions": {
                "scores": {
                    "natural_fit": 70.0,
                    "capability_fit": 41.0,
                    "evidence_strength": 22.0,
                    "transition_feasibility": 58.0,
                },
                "labels": {
                    "natural_fit": "Moderate",
                    "capability_fit": "Developing",
                    "evidence_strength": "Limited",
                    "transition_feasibility": "Moderate",
                },
            },
        },
    )
    db.add(unrelated)
    db.commit()
    before_unrelated_score = unrelated.alignment_score
    before_unrelated_dimensions = dict(unrelated.source_metadata_json["hypothesis_dimensions"]["scores"])
    result = db.get(CareerExperimentResult, evaluated["result"]["id"])

    run = recalibrate_career_recommendations(db, item, result.id)
    refreshed_unrelated = db.get(CareerMatch, unrelated.id)
    target_hypothesis = db.scalar(
        select(CareerHypothesis).where(
            CareerHypothesis.profile_id == item.id,
            CareerHypothesis.career_match_id == match.id,
            CareerHypothesis.status == "active",
        )
    )

    assert [change["career_match_id"] for change in run["changed_recommendations"]] == [match.id]
    assert run["hypothesis_id"] == target_hypothesis.id
    assert refreshed_unrelated.alignment_score == before_unrelated_score
    assert refreshed_unrelated.source_metadata_json["hypothesis_dimensions"]["scores"] == before_unrelated_dimensions
    assert target_hypothesis.current_version_number == 2
    assert db.scalar(
        select(func.count()).select_from(CareerHypothesisVersion).where(CareerHypothesisVersion.hypothesis_id == target_hypothesis.id)
    ) == 2


def test_failed_deterministic_evidence_persistence_raises_without_a_successful_result(monkeypatch):
    db = session()
    user, item, match = complete_demo_assessment(db)
    created = create_experiment_session(db, item, {"experiment_template_id": "ai-product-human-review-flow", "career_match_id": match.id, "mode": "guided", "user_confirmed": True}, user.id)
    experiment = db.get(CareerExperimentSession, created["id"])
    start_experiment(db, experiment)
    submit_experiment(db, experiment, {"text_response": "Prototype with user correction, validation, accessibility, explanation, risk boundaries and communication.", "project_url": "https://example.test/failure", "completion_notes": "Reviewable human review flow.", "time_spent_minutes": 120})

    import app.services.career_resilience_engine as engine

    monkeypatch.setattr(engine, "_create_skill_evidence", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("simulated evidence persistence failure")))
    try:
        evaluate_experiment(db, experiment)
        assert False, "Expected persistence failure"
    except RuntimeError as error:
        assert "persistence failure" in str(error)
    db.rollback()
    assert db.scalar(select(func.count()).select_from(CareerExperimentResult).where(CareerExperimentResult.session_id == experiment.id)) == 0
    assert db.scalar(select(func.count()).select_from(SkillEvidenceSource).where(SkillEvidenceSource.profile_id == item.id, SkillEvidenceSource.source_type == "DETERMINISTIC_CAREER_EXPERIMENT")) == 0


def test_confirmed_in_progress_experiment_persists_one_active_roadmap_action_and_history_event():
    db = session()
    user, item, match = complete_demo_assessment(db)
    created = create_experiment_session(
        db,
        item,
        {"experiment_template_id": "ai-product-human-review-flow", "career_match_id": match.id, "mode": "guided", "user_confirmed": True},
        user.id,
    )
    experiment = db.get(CareerExperimentSession, created["id"])
    start_experiment(db, experiment)

    confirmed = confirm_experiment_roadmap(db, item, experiment)
    db.expire_all()
    reloaded_experiment = db.get(CareerExperimentSession, experiment.id)
    action = db.get(RoadmapAction, confirmed["roadmap_action_id"])
    roadmap = db.get(Roadmap, action.roadmap_id)
    public = roadmap_public(db, roadmap)

    assert reloaded_experiment.roadmap_action_id == action.id
    assert action.user_id == user.id
    assert action.profile_id == item.id
    assert action.roadmap_id == roadmap.id
    assert action.career_experiment_session_id == experiment.id
    assert action.career_hypothesis_id == experiment.hypothesis_id
    assert action.evidence_gap_id == experiment.evidence_gap_id
    assert action.source_type == "career_experiment"
    assert action.title == confirmed["template"]["title"]
    assert action.status == "in_progress"
    assert action.progress_percentage >= 35
    assert action.horizon == "seven_days"
    assert action.id in {row["id"] for row in public["seven_days"]}
    assert public["progress"]["in_progress_actions"] == 1
    assert public["progress"]["completion_percentage"] > 0
    event = db.scalar(
        select(RoadmapEvent).where(
            RoadmapEvent.roadmap_id == roadmap.id,
            RoadmapEvent.action_id == action.id,
            RoadmapEvent.event_type == "career_experiment_added_to_roadmap",
        )
    )
    assert event is not None
    assert event.metadata_json["experiment_session_id"] == experiment.id
    assert event.metadata_json["title"] == action.title
    assert db.scalar(
        select(RoadmapVersion).where(
            RoadmapVersion.roadmap_id == roadmap.id,
            RoadmapVersion.reason.like("Career experiment added to roadmap:%"),
        )
    ) is not None

    # A double click or a retry after a refresh must return the persisted link,
    # not insert another action or history event.
    retry = confirm_experiment_roadmap(db, item, db.get(CareerExperimentSession, experiment.id))
    assert retry["roadmap_action_id"] == action.id
    assert db.scalar(
        select(func.count()).select_from(RoadmapAction).where(
            RoadmapAction.career_experiment_session_id == experiment.id
        )
    ) == 1
    assert db.scalar(
        select(func.count()).select_from(RoadmapEvent).where(
            RoadmapEvent.action_id == action.id,
            RoadmapEvent.event_type == "career_experiment_added_to_roadmap",
        )
    ) == 1

    # A fresh database session observes the same persisted action and active count.
    reloaded_db = Session(db.get_bind())
    try:
        reloaded_roadmap = reloaded_db.get(Roadmap, roadmap.id)
        reloaded_public = roadmap_public(reloaded_db, reloaded_roadmap)
        assert any(row["id"] == action.id for row in reloaded_public["seven_days"])
        assert reloaded_public["progress"]["in_progress_actions"] == 1
    finally:
        reloaded_db.close()


def test_experiment_roadmap_links_are_isolated_between_users():
    db = session()
    owner, owner_profile, owner_match = complete_demo_assessment(db)
    owner_session_data = create_experiment_session(
        db,
        owner_profile,
        {"experiment_template_id": "ai-product-human-review-flow", "career_match_id": owner_match.id, "mode": "guided", "user_confirmed": True},
        owner.id,
    )
    owner_session = db.get(CareerExperimentSession, owner_session_data["id"])
    start_experiment(db, owner_session)
    owner_confirmed = confirm_experiment_roadmap(db, owner_profile, owner_session)

    other = User(name="Other Resilience User", email="other-resilience@example.test", hashed_password="x")
    db.add(other)
    db.flush()
    other_profile = Profile(user_id=other.id, diagnostic_id="other-diagnostic", data={"primary_archetype": {"name": "Systems Builder"}})
    db.add(other_profile)
    db.commit()
    other_session_data = create_experiment_session(
        db,
        other_profile,
        {"experiment_template_id": owner_session.experiment_template_id, "mode": "guided", "user_confirmed": True},
        other.id,
    )
    other_session = db.get(CareerExperimentSession, other_session_data["id"])
    start_experiment(db, other_session)
    other_confirmed = confirm_experiment_roadmap(db, other_profile, other_session)

    owner_action = db.get(RoadmapAction, owner_confirmed["roadmap_action_id"])
    other_action = db.get(RoadmapAction, other_confirmed["roadmap_action_id"])
    assert owner_action.id != other_action.id
    assert owner_action.user_id == owner.id
    assert other_action.user_id == other.id
    assert owner_action.profile_id == owner_profile.id
    assert other_action.profile_id == other_profile.id
    assert owner_action.career_experiment_session_id == owner_session.id
    assert other_action.career_experiment_session_id == other_session.id


def test_evidence_passport_confidence_and_recency_keep_self_report_separate():
    db = session()
    _, item, _ = complete_demo_assessment(db)
    add_manual_evidence(
        db,
        item,
        {
            "skill_id": "ux_ui",
            "evidence_type": "course_completion",
            "title": "UX course",
            "description": "Completed course only.",
            "url": "https://example.test/course",
            "score_hint": 80,
        },
    )
    passport = evidence_passport(db, item.id)
    ux = next(skill for skill in passport["skills"] if skill["skill_id"] == "ux_ui")
    assert ux["evidence_confidence"] in {"Emerging evidence", "Moderate evidence", "Strong evidence", "Multiple supporting sources"}
    assert ux["strongest_evidence_label"] != "Practically verified"
    assert db.scalar(select(func.count()).select_from(SkillRecency).where(SkillRecency.profile_id == item.id, SkillRecency.skill_id == "ux_ui")) == 1


def test_recalibration_stores_before_after_and_counterfactuals():
    db = session()
    user, item, match = complete_demo_assessment(db)
    created = create_experiment_session(db, item, {"experiment_template_id": "ai-product-human-review-flow", "career_match_id": match.id, "mode": "guided", "user_confirmed": True}, user.id)
    row = db.get(CareerExperimentSession, created["id"])
    start_experiment(db, row)
    submit_experiment(
        db,
        row,
        {
            "text_response": "Designed a prototype with user correction, validation review, accessibility and explainability notes.",
            "project_url": "https://example.test/prototype",
            "completion_notes": "Completed enough for deterministic evidence.",
            "time_spent_minutes": 120,
            "reflection": {"note": "More product analytics would strengthen this."},
        },
    )
    evaluated = evaluate_experiment(db, row)
    run = recalibrate_career_recommendations(db, item, evaluated["result"]["id"])
    assert run["before"]["career_alignment"]
    assert run["after"]["new_evidence"]
    assert run["changed_recommendations"]
    assert "what_would_strengthen" in run["changed_recommendations"][0]


def test_supported_paths_keep_four_fit_dimensions_and_handle_support_screening():
    db = session()
    _, item, _ = complete_demo_assessment(db)
    upsert_job_loss_profile(db, item, {"consent_accepted": True, "country_of_residence": "Norway", "country_of_employment": "Norway", "employment_status": "unemployed", "reduction_in_working_hours": 100, "jobseeker_registration_status": "not_registered", "training_interest": "yes", "availability_for_work": "yes"})
    run_support_screening(db, item, {})
    paths = create_supported_paths(db, item, {})
    assert paths["results"]
    first = paths["results"][0]
    assert {"personal_fit", "capability_fit", "market_fit", "support_fit"} <= set(first)
    assert first["official_assessment_required"] is True
    assert db.scalar(select(func.count()).select_from(SupportedPathRun).where(SupportedPathRun.profile_id == item.id)) == 1


def test_support_registry_uses_official_sources_and_screening_never_approves_eligibility():
    db = session()
    sync_career_resilience_catalogue(db)
    programmes = list_support_programmes(db)
    assert len(programmes) >= 8
    assert all(safe_official_url(item["official_url"]) for item in programmes)
    user, item = profile(db)
    screening = run_support_screening(db, item, {"country_of_residence": "Norway", "employment_status": "unemployed", "reduction_in_working_hours": 100, "jobseeker_registration_status": "not_registered"})
    labels = {item["preliminary_label"] for item in screening["preliminary_result"]["programmes"]}
    assert "Potentially relevant" in labels
    assert "eligible" not in str(screening).lower()
    assert db.scalar(select(func.count()).select_from(SupportScreening).where(SupportScreening.profile_id == item.id)) == 1
    assert db.scalar(select(func.count()).select_from(SupportProgrammeVersion)) >= 8


def test_job_loss_mode_consent_action_plan_and_profile_ownership():
    db = session()
    owner, item = profile(db)
    other = User(name="Other", email="other-resilience@example.test", hashed_password="x")
    db.add(other)
    db.commit()
    try:
        upsert_job_loss_profile(db, item, {"consent_accepted": False})
        assert False
    except ValueError:
        pass
    upsert_job_loss_profile(db, item, {"consent_accepted": True, "country_of_residence": "Norway", "employment_status": "unemployed"})
    create_immediate_action_plan(db, item)
    assert db.scalar(select(func.count()).select_from(JobLossProfile).where(JobLossProfile.profile_id == item.id)) == 1
    assert db.scalar(select(func.count()).select_from(ImmediateActionPlan).where(ImmediateActionPlan.profile_id == item.id)) == 1
    assert require_profile(db, item.id, owner).id == item.id
    try:
        require_profile(db, item.id, other)
        assert False
    except HTTPException as error:
        assert error.status_code == 403


def test_demo_reset_seeds_career_resilience_records():
    db = session()
    _, profile, _ = restore_demo(db)
    assert db.scalar(select(func.count()).select_from(CareerExperimentSession).where(CareerExperimentSession.profile_id == profile.id)) >= 2
    assert db.scalar(select(func.count()).select_from(SupportScreening).where(SupportScreening.profile_id == profile.id)) >= 1
