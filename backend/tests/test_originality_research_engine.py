from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.career_resilience import CareerHypothesis
from app.models.innovation_extension import CareerDecisionJournalEntry
from app.models.originality_research import (
    AdaptiveExperimentRecommendation,
    AdaptiveExperimentRun,
    CareerTransitionPath,
    CareerTransitionSimulation,
    FairnessAuditRun,
    RecommendationRobustnessRun,
    ResearchOriginalitySession,
)
from app.models.profile import Profile
from app.models.roadmap_adaptation import RoadmapAction
from app.models.user import User
from app.services.originality_research_engine import (
    _apply_pareto,
    _normalise_paths,
    adaptive_recommendation_action,
    analyse_adaptive_experiments,
    archive_transition_simulation,
    compare_transition_scenarios,
    create_originality_research_session,
    create_transition_simulation,
    delete_originality_research_for_profiles,
    discover_evidence_gaps,
    ensure_system_card_version,
    fairness_audit_failures,
    fairness_audit_limitations,
    fairness_test_suites,
    get_evidence_capture_proposal,
    get_transition_simulation,
    list_adaptive_runs,
    path_to_decision_journal,
    propose_roadmap_for_path,
    record_adaptive_outcome,
    recommendation_provenance,
    reset_synthetic_fairness_lab,
    review_evidence_capture_proposal,
    run_fairness_audit,
    run_recommendation_robustness,
    transition_adaptive_lifecycle,
    transition_pareto_front,
    update_transition_constraints,
    update_originality_baseline,
    update_originality_experimental,
    update_originality_feedback,
)


def session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def profile(db: Session) -> tuple[User, Profile]:
    user = User(name="Originality User", email="originality@example.test", hashed_password="x")
    db.add(user)
    db.flush()
    item = Profile(user_id=user.id, diagnostic_id="diagnostic", data={"primary_archetype": {"name": "Curious Builder"}})
    db.add(item)
    db.flush()
    hypotheses = [
        ("AI Product Designer", "Design and product", 0.72),
        ("RAG Application Developer", "AI and software", 0.61),
        ("AI Integration Consultant", "Consulting and strategy", 0.66),
    ]
    for title, family, score in hypotheses:
        db.add(
            CareerHypothesis(
                profile_id=item.id,
                user_id=user.id,
                title=title,
                role_family=family,
                statement=f"{title} remains a testable career hypothesis.",
                current_alignment_score=score,
                uncertainty_label="Additional evidence required",
                status="active",
            )
        )
    db.commit()
    return user, item


def profile_without_hypotheses(db: Session) -> tuple[User, Profile]:
    user = User(name="No Hypothesis User", email="no-hypothesis@example.test", hashed_password="x")
    db.add(user)
    db.flush()
    item = Profile(user_id=user.id, diagnostic_id="diagnostic-no-hypothesis", data={})
    db.add(item)
    db.commit()
    return user, item


def _pareto_vectors(*items: tuple[str, float, float]) -> list[dict]:
    paths = [
        {
            "title": title,
            "role_slug": title.lower().replace(" ", "-"),
            "objectives": {"transition_duration": duration, "personal_fit": fit},
        }
        for title, duration, fit in items
    ]
    _normalise_paths(paths, ["transition_duration", "personal_fit"])
    _apply_pareto(paths, ["transition_duration", "personal_fit"])
    return paths


def test_pareto_dominance_handles_dominance_ties_tradeoffs_single_and_empty_inputs():
    dominated = _pareto_vectors(("A", 0.2, 0.8), ("B", 0.5, 0.7))
    assert dominated[0]["is_pareto_optimal"] is True
    assert dominated[1]["is_pareto_optimal"] is False

    ties = _pareto_vectors(("A", 0.3, 0.7), ("B", 0.3, 0.7))
    assert all(path["is_pareto_optimal"] for path in ties)

    tradeoffs = _pareto_vectors(("Lower effort", 0.2, 0.6), ("Stronger fit", 0.5, 0.9))
    assert all(path["is_pareto_optimal"] for path in tradeoffs)

    single = _pareto_vectors(("Only path", 0.4, 0.6))
    assert single[0]["is_pareto_optimal"] is True

    empty: list[dict] = []
    _normalise_paths(empty, ["transition_duration", "personal_fit"])
    _apply_pareto(empty, ["transition_duration", "personal_fit"])
    assert empty == []


def test_originality_modules_return_insufficient_data_without_an_active_hypothesis():
    db = session()
    user, item = profile_without_hypotheses(db)

    gaps = discover_evidence_gaps(db, item)
    adaptive = analyse_adaptive_experiments(db, item, {}, user.id)
    transition = create_transition_simulation(db, item, {}, user.id)
    robustness = run_recommendation_robustness(db, item, {}, user.id)

    assert gaps["status"] == "insufficient_data"
    assert gaps["gaps"] == []
    assert adaptive["status"] == "insufficient_data"
    assert adaptive["recommendations"] == []
    assert "Active Career Hypothesis" in adaptive["missing_inputs"]
    assert transition["status"] == "insufficient_data"
    assert transition["paths"] == []
    assert "No fallback career path" in transition["explanation"]
    assert robustness["status"] == "insufficient_data"
    assert robustness["scenario_results"] == []
    assert robustness["metrics"]["qualitative_interpretation"] == "Insufficient basis"
    assert db.scalar(select(AdaptiveExperimentRecommendation).where(AdaptiveExperimentRecommendation.profile_id == item.id)) is None


def test_adaptive_runs_are_append_only_snapshots():
    db = session()
    user, item = profile(db)

    first = analyse_adaptive_experiments(db, item, {"weekly_learning_time": 4}, user.id)
    second = analyse_adaptive_experiments(db, item, {"weekly_learning_time": 12}, user.id)
    runs = list_adaptive_runs(db, item)

    snapshots = {run["id"]: run["input_snapshot"] for run in runs}
    assert set(snapshots) == {first["id"], second["id"]}
    assert snapshots[second["id"]]["constraints"]["weekly_learning_time"] == 12
    assert snapshots[first["id"]]["constraints"]["weekly_learning_time"] == 4


def test_adaptive_experiment_scoring_alternatives_rejection_start_and_outcome_are_deterministic():
    db = session()
    user, item = profile(db)

    run = analyse_adaptive_experiments(db, item, {"weekly_learning_time": 8, "learning_budget": 50}, user.id)
    gaps = discover_evidence_gaps(db, item)
    recommendations = run["recommendations"]
    top = recommendations[0]
    row = db.get(AdaptiveExperimentRecommendation, top["id"])

    assert len(recommendations) >= 6
    assert gaps["gaps"]
    assert run["decision_support_snapshot"]["version"] == "decision-support-snapshot-v1"
    assert run["evidence_gaps"]
    assert run["weight_version"] == "adaptive-evidence-gain-weights-v1"
    assert top["priority_band"] in {"High evidence value", "Useful evidence value", "Exploratory value", "Low current feasibility", "Insufficient information"}
    assert top["score_components"]["score_precision_note"].startswith("Scores are deterministic")
    assert all(0 <= item["value"] <= 1 for item in top["score_components"]["positive"].values())
    assert all(0 <= item["value"] <= 1 for item in top["score_components"]["negative"].values())
    assert "Missing evidence is never interpreted as proof of inability." == run["uncertainty_summary"]["missing_evidence_note"]
    assert {item["type"] for item in top["alternatives"]} >= {"lower_effort_alternative", "higher_evidence_alternative", "lower_cost_alternative", "no_action_reflection"}
    assert top["linked_evidence_gap_ids"]
    assert row.score_internal == db.get(AdaptiveExperimentRecommendation, top["id"]).score_internal

    rejected = adaptive_recommendation_action(db, recommendations[1]["id"], "reject", {"reason": "too_expensive", "note": "Not possible this week."}, user.id)
    started = adaptive_recommendation_action(db, top["id"], "start", {"add_to_roadmap": False}, user.id)
    paused = transition_adaptive_lifecycle(db, top["id"], {"status": "paused", "note": "Need a shorter session."}, user.id)
    active = transition_adaptive_lifecycle(db, top["id"], {"status": "active"}, user.id)
    outcome = record_adaptive_outcome(db, top["id"], {"actual_evidence_gained": [{"skill_id": "ux_ui"}], "produced_artefact": "demo-url", "user_reflection": "Useful but partial."}, user.id)
    proposal = get_evidence_capture_proposal(db, top["id"])
    reviewed = review_evidence_capture_proposal(db, top["id"], {"decision": "accept", "note": "Looks sufficient for a proposal."}, user.id)
    provenance = recommendation_provenance(db, "adaptive-experiment", top["id"])

    assert rejected["rejection_feedback"]["career_direction_rejected"] is False
    assert started["career_experiment_session_id"]
    assert paused["status"] == "paused"
    assert active["status"] == "active"
    assert db.scalar(select(RoadmapAction).where(RoadmapAction.profile_id == item.id)) is None
    assert outcome["actual_evidence_gain"]["success_not_auto_marked"] is True
    assert outcome["actual_evidence_gain"]["verified_evidence_created"] is False
    assert proposal["accept_reject_required"] is True
    assert reviewed["status"] == "evidence reviewed"
    assert reviewed["actual_evidence_gain"]["evidence_capture_review"]["evidence_passport_mutated"] is False
    assert provenance["change_explanation"].startswith("Historical recommendation rows")
    assert db.scalar(select(AdaptiveExperimentRun).where(AdaptiveExperimentRun.profile_id == item.id)).scoring_version == "adaptive-evidence-gain-score-v1"


def test_transition_pareto_sorting_keeps_dominated_paths_visible_and_requires_confirmation():
    db = session()
    user, item = profile(db)

    simulation = create_transition_simulation(db, item, {"preset": "balanced_transition", "save_scenario": True}, user.id)
    paths = simulation["paths"]
    pareto = [path for path in paths if path["is_pareto_optimal"]]
    dominated = [path for path in paths if not path["is_pareto_optimal"]]
    first_path = pareto[0]
    path_row = db.get(CareerTransitionPath, first_path["id"])

    assert len(paths) >= 4
    assert len(pareto) >= 2
    assert dominated
    assert "dominated by" in dominated[0]["dominated_explanation"].lower()
    assert all(path["constraint_results"] for path in paths)
    assert all(path["feasibility_status"] for path in paths)
    assert "universal best-career ranking" in simulation["explanation"]
    assert simulation["objective_config"]["hidden_career_preferences"] is False
    assert set(simulation["objective_config"]["directions"].values()) <= {"min", "max"}

    faster = create_transition_simulation(db, item, {"preset": "fastest_realistic_transition", "controls": {"weekly_learning_time": 12}}, user.id)
    comparison = compare_transition_scenarios(db, simulation["id"], {"comparison_ids": [faster["id"]]})
    front = transition_pareto_front(db, simulation["id"])
    updated_constraints = update_transition_constraints(db, simulation["id"], {"controls": {"weekly_learning_time": 2, "learning_budget": 0}}, user.id)
    journal = path_to_decision_journal(db, path_row.id, {}, user.id)
    roadmap = propose_roadmap_for_path(db, path_row.id, {})
    archived = archive_transition_simulation(db, simulation["id"], {"reason": "superseded"}, user.id)
    provenance = recommendation_provenance(db, "transition-simulation", simulation["id"])

    assert comparison["comparisons"]
    assert front["pareto_front"]
    assert front["methodology"]["missing_value_rule"].startswith("Missing")
    assert updated_constraints["historical_result_preserved"] is True
    assert journal["roadmap_changed"] is False
    assert db.scalar(select(CareerDecisionJournalEntry).where(CareerDecisionJournalEntry.profile_id == item.id)) is not None
    assert roadmap["confirmation_required"] is True
    assert roadmap["roadmap_changed"] is False
    assert archived["status"] == "archived"
    assert provenance["change_explanation"].startswith("Recalculation creates")
    assert db.scalar(select(RoadmapAction).where(RoadmapAction.profile_id == item.id)) is None
    assert db.scalar(select(CareerTransitionSimulation).where(CareerTransitionSimulation.profile_id == item.id)) is not None


def test_robustness_and_synthetic_fairness_card_separate_contextual_effects_from_capability():
    db = session()
    user, item = profile(db)

    robustness = run_recommendation_robustness(db, item, {}, user.id)
    fairness = run_fairness_audit(db, {})
    card = ensure_system_card_version(db)

    assert robustness["metrics"]["top_k_overlap"] <= 1
    assert robustness["metrics"]["top_1_stability"] <= 1
    assert "maximum_rank_movement" in robustness["metrics"]
    assert robustness["scenario_results"]
    assert robustness["decision_support_snapshot"]["version"] == "decision-support-snapshot-v1"
    assert robustness["dependency_flags"]
    assert any(row["tested_variable"] == "market_data_window" for row in robustness["sensitivity_matrix"])
    assert "Confirmed qualifications and professional history are not perturbed." in robustness["limitations"]
    assert db.scalar(select(RecommendationRobustnessRun).where(RecommendationRobustnessRun.profile_id == item.id)) is not None

    statuses = {item["status"] for item in fairness["results"]}
    location = next(item for item in fairness["results"] if item["case_id"] == "location-market-context")
    failures = fairness_audit_failures(db, fairness["id"])
    limitations = fairness_audit_limitations(db, fairness["id"])
    suites = fairness_test_suites()
    assert fairness["synthetic_only"] is True
    assert {"Passed", "Review required", "Expected contextual difference", "Data limitation"} <= statuses
    assert "Capability Fit remained unchanged" in location["output_difference"]
    assert fairness["summary"]["real_user_data_included"] is False
    assert fairness["summary"]["fairness_certification_claimed"] is False
    assert any(item["case_id"] == "dominance-consistency" for item in fairness["results"])
    assert failures["failure_count"] == 1
    assert limitations["fairness_certification_claimed"] is False
    assert suites and all(suite["synthetic_only"] for suite in suites)
    assert db.scalar(select(FairnessAuditRun)) is not None

    assert card["version"] == "recommendation-system-card-v1"
    assert "No automatic roadmap mutation" in card["human_oversight"]
    assert "Evidence-capture proposals require user review" in card["human_oversight"]
    assert card["validation_status"].startswith("Implemented for deterministic technical evaluation")


def test_originality_research_consent_results_export_filter_and_reset_delete():
    db = session()
    user, item = profile(db)

    try:
        create_originality_research_session(db, {"consent_confirmed": False}, item, user.id)
        assert False
    except PermissionError:
        pass

    research = create_originality_research_session(db, {"consent_confirmed": True, "assigned_condition": "experimental"}, item, user.id)
    update_originality_baseline(db, research["id"], {"actionability": 2, "uncertainty_clarity": 2})
    update_originality_experimental(db, research["id"], {"actionability": 4, "uncertainty_clarity": 4})
    results = update_originality_feedback(db, research["id"], {"trust_calibration": 4})

    assert research["pseudonymous_id"].startswith("ori-")
    assert results["results"]["raw_journal_text_included"] is False
    assert results["results"]["raw_transcripts_included"] is False
    assert results["results"]["scientific_validation_claimed"] is False
    assert db.scalar(select(ResearchOriginalitySession).where(ResearchOriginalitySession.profile_id == item.id)) is not None

    analyse_adaptive_experiments(db, item, {}, user.id)
    create_transition_simulation(db, item, {}, user.id)
    run_recommendation_robustness(db, item, {}, user.id)
    run_fairness_audit(db, {"demo_marker": True})
    reset = reset_synthetic_fairness_lab(db, {"demo_only": True})
    delete_originality_research_for_profiles(db, [item.id])
    db.commit()

    assert reset["normal_user_profiles_affected"] == 0
    assert db.scalar(select(AdaptiveExperimentRecommendation).where(AdaptiveExperimentRecommendation.profile_id == item.id)) is None
    assert db.scalar(select(CareerTransitionPath).where(CareerTransitionPath.profile_id == item.id)) is None
    assert db.scalar(select(RecommendationRobustnessRun).where(RecommendationRobustnessRun.profile_id == item.id)) is None
