from sqlalchemy import func, select

from app.models.career_resilience import CareerEvidenceGap, CareerHypothesis
from app.models.recommendation import Recommendation, RecommendationEvent
from app.models.roadmap_adaptation import RoadmapAction
from app.services.coach_chat_service import compact_profile_context
from app.services.career_resilience_engine import (
    add_manual_evidence,
    career_resilience_dashboard,
    create_experiment_session,
    evidence_passport,
    list_profile_evidence_gaps,
)
from app.services.learning_engine import (
    create_skill_gap_analysis,
    generate_learning_recommendations,
    latest_gap_analysis,
    latest_recommendations,
)
from app.services.recommendation_context import (
    archive_resolved_evidence_gap_recommendations,
    build_recommendation_context,
)

from test_career_resilience_engine import (
    HUMAN_REVIEW_SKILLS,
    complete_demo_assessment,
    completed_human_review_experiment,
    completed_ideation_sprint,
    session,
)


def test_completed_experiment_state_survives_fresh_cross_page_reads():
    db = session()
    user, profile, match, hypothesis, experiment, _ = completed_ideation_sprint(db)

    passport_before = evidence_passport(db, profile.id)
    dashboard_before = career_resilience_dashboard(db, profile)
    gaps_before = list_profile_evidence_gaps(db, profile, hypothesis.id)
    actions_before = db.scalar(select(func.count()).select_from(RoadmapAction).where(RoadmapAction.profile_id == profile.id))

    sufficient = create_experiment_session(
        db,
        profile,
        {"career_match_id": match.id, "mode": "guided", "user_confirmed": True},
        user.id,
    )

    db.expire_all()
    passport_after = evidence_passport(db, profile.id)
    dashboard_after = career_resilience_dashboard(db, profile)
    gaps_after = list_profile_evidence_gaps(db, profile, hypothesis.id)

    verified_before = {
        item["skill_id"]
        for item in passport_before["skills"]
        if item["strongest_evidence_label"] == "Practically verified"
    }
    verified_after = {
        item["skill_id"]
        for item in passport_after["skills"]
        if item["strongest_evidence_label"] == "Practically verified"
    }
    expected_skills = HUMAN_REVIEW_SKILLS | {"ideation"}
    assert expected_skills.issubset(verified_before)
    assert verified_after == verified_before
    assert sufficient["status"] == "evidence_sufficient"
    assert sufficient["recommendation"]["state"] == "evidence_sufficient"
    persisted_evidence_state = next(
        item
        for item in dashboard_after["evidence_states"]
        if item["hypothesis_id"] == hypothesis.id
    )
    assert persisted_evidence_state["state"] == "evidence_sufficient"
    assert persisted_evidence_state["recommendation"] == sufficient["recommendation"]
    assert [
        row.id
        for row in db.scalars(
            select(CareerHypothesis).where(
                CareerHypothesis.profile_id == profile.id,
                CareerHypothesis.canonical_direction_id == hypothesis.canonical_direction_id,
                CareerHypothesis.status == "active",
            )
        ).all()
    ] == [hypothesis.id]
    current_before = [item for item in dashboard_before["career_hypotheses"] if item["id"] == hypothesis.id]
    current_after = [item for item in dashboard_after["career_hypotheses"] if item["id"] == hypothesis.id]
    assert len(current_before) == 1
    assert len(current_after) == 1
    assert current_after[0]["title"] == "Human-Centred AI Product Designer"
    assert not {item["skill_id"] for item in gaps_before["gaps"]} & expected_skills
    assert gaps_after == gaps_before
    assert db.scalar(select(func.count()).select_from(RoadmapAction).where(RoadmapAction.profile_id == profile.id)) == actions_before
    assert experiment.status == "evaluated"

    coach_context = compact_profile_context(db, profile.id)
    assert {
        "title": "Human-Centred AI Product Designer",
        "canonical_direction_id": hypothesis.canonical_direction_id,
        "version": hypothesis.current_version_number,
        "uncertainty_label": hypothesis.uncertainty_label,
    } in coach_context["career_evidence"]["current_hypotheses"]
    assert expected_skills.issubset(set(coach_context["career_evidence"]["practically_verified_skill_ids"]))
    assert coach_context["career_evidence"]["recent_experiment_statuses"][0]["status"] == "evaluated"


def test_generic_recommendations_ignore_superseded_hypothesis_gaps():
    db = session()
    _, profile, match, hypothesis, _, _ = completed_ideation_sprint(db)
    stale = CareerHypothesis(
        profile_id=profile.id,
        user_id=profile.user_id,
        career_match_id=match.id,
        title="Superseded direction",
        status="superseded",
        current_version_number=1,
    )
    db.add(stale)
    db.flush()
    db.add(
        CareerEvidenceGap(
            profile_id=profile.id,
            user_id=profile.user_id,
            career_match_id=match.id,
            hypothesis_id=stale.id,
            skill_id="ideation",
            capability_label="Legacy Ideation",
            status="MISSING",
            current_evidence_status="MISSING",
            reason="A superseded record must not drive current recommendations.",
            importance=10,
        )
    )
    db.commit()

    context = build_recommendation_context(db, profile)

    assert {item["title"] for item in context["active_hypotheses"]}.issubset(
        {row.title for row in db.scalars(select(CareerHypothesis).where(CareerHypothesis.profile_id == profile.id, CareerHypothesis.status == "active")).all()}
    )
    assert all(item["hypothesis"] != "Superseded direction" for item in context["evidence_gaps"])
    assert all(item["capability"] != "Legacy Ideation" for item in context["evidence_gaps"])


def test_resolved_gap_recommendations_are_archived_without_losing_history():
    db = session()
    _, profile, _, hypothesis, _, _ = completed_ideation_sprint(db)
    stale = Recommendation(
        profile_id=profile.id,
        user_id=profile.user_id,
        category="career_experiments",
        title="Test ideation in a future-role task",
        summary="A bounded task that was originally scoped to the Ideation evidence gap.",
        reason="The evidence gap was unresolved when this was generated.",
        profile_signals_json=[
            {"signal": hypothesis.title, "source": "career_hypothesis"},
            {"signal": "Ideation", "source": "evidence_gap"},
        ],
        first_action="Review the supplied evidence.",
        success_indicator="Evidence is practically verified.",
    )
    historical = Recommendation(
        profile_id=profile.id,
        user_id=profile.user_id,
        category="career_experiments",
        title="Previously accepted ideation task",
        summary="A historical user-controlled task.",
        reason="It must remain available as history.",
        profile_signals_json=stale.profile_signals_json,
        first_action="Keep the user's decision.",
        success_indicator="History remains intact.",
        status="accepted",
    )
    db.add_all([stale, historical])
    db.commit()

    assert all(item["capability"] != "Ideation" for item in build_recommendation_context(db, profile)["evidence_gaps"])
    assert archive_resolved_evidence_gap_recommendations(db, profile) == 1
    assert db.get(Recommendation, stale.id).status == "archived"
    assert db.get(Recommendation, historical.id).status == "accepted"
    assert db.scalar(
        select(func.count())
        .select_from(RecommendationEvent)
        .where(
            RecommendationEvent.recommendation_id == stale.id,
            RecommendationEvent.event_type == "archived_resolved_evidence_gap",
        )
    ) == 1


def test_learning_path_does_not_treat_practical_experiment_evidence_as_unverified():
    db = session()
    _, profile, match, _, _, _ = completed_human_review_experiment(db)

    analysis = create_skill_gap_analysis(db, profile, match.id)
    ux_ui = next(item for item in analysis["items"] if item["skill_id"] == "ux_ui")

    assert ux_ui["evidence_level"] == "practically_verified"
    assert ux_ui["status"] == "No gap"
    assert ux_ui["priority_label"] == "Optional"


def test_practical_evidence_invalidates_pre_evidence_learning_snapshots():
    db = session()
    _, profile, match = complete_demo_assessment(db)

    original_analysis = create_skill_gap_analysis(db, profile, match.id)
    original_run = generate_learning_recommendations(db, profile, match.id)
    assert original_analysis["status"] == "ready"
    assert original_run["status"] == "ready"

    add_manual_evidence(
        db,
        profile,
        {
            "skill_id": "ux_ui",
            "evidence_type": "practical_exercise",
            "title": "Verified interaction prototype",
            "description": "A bounded practical prototype with tested interface states and documented trade-offs.",
            "score_hint": 90,
        },
    )

    db.expire_all()
    assert latest_gap_analysis(db, profile.id, match.id)["status"] == "not_started"
    assert latest_recommendations(db, profile.id, match.id)["status"] == "not_started"
