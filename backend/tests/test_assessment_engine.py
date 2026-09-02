from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.assessment import AssessmentResponse, AssessmentScore, AssessmentSession, CareerMatch, SkillsInventory, SkillEvidence
from app.models.career_resilience import CareerHypothesis
from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.models.roadmap_adaptation import RoadmapAction
from app.models.user import User
from app.services.assessment_engine import (
    SCORING_VERSION,
    career_matches_for_profile,
    complete_assessment_session,
    create_roadmap_draft_from_match,
    delete_assessment_data,
    results_for_profile,
    reverse_score,
    set_match_status,
    upsert_responses,
)
from app.services.demo_seed_service import demo_assessment_responses
from app.services.profile_generation import generate_profile_fallback


def session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def profile(db: Session) -> tuple[User, Profile]:
    user = User(name="Assessment User", email="assessment@example.test", hashed_password="x")
    db.add(user)
    db.flush()
    item = Profile(user_id=user.id, diagnostic_id="diagnostic", data={"primary_archetype": {"name": "Curious Explorer"}})
    db.add(item)
    db.commit()
    return user, item


def complete_demo_assessment(db: Session) -> tuple[AssessmentSession, Profile]:
    user, item = profile(db)
    assessment = AssessmentSession(profile_id=item.id, user_id=user.id, mode="complete", status="in_progress", consent_accepted=True)
    db.add(assessment)
    db.flush()
    upsert_responses(db, assessment, demo_assessment_responses())
    result = complete_assessment_session(db, assessment, item)
    assert result["status"] == "completed"
    return assessment, item


def test_reverse_scoring_helper():
    assert reverse_score(1) == 5
    assert reverse_score(5) == 1
    assert reverse_score(3) == 3


def test_complete_assessment_calculates_versioned_scores_and_matches():
    db = session()
    assessment, item = complete_demo_assessment(db)
    scores = db.scalars(select(AssessmentScore).where(AssessmentScore.session_id == assessment.id)).all()
    assert scores
    assert {score.scoring_version for score in scores} == {SCORING_VERSION}
    assert db.scalar(select(func.count()).select_from(AssessmentResponse).where(AssessmentResponse.session_id == assessment.id)) > 20
    categories = {match["category"] for match in career_matches_for_profile(db, item.id)}
    assert "augment_current_profession" in categories
    assert "adjacent_professional_roles" in categories
    assert "reskilling_opportunities" in categories
    assert any(match["supporting_factors"] or match["conflicting_factors"] for match in career_matches_for_profile(db, item.id))


def test_incomplete_assessment_reports_missing_required_items():
    db = session()
    user, item = profile(db)
    assessment = AssessmentSession(profile_id=item.id, user_id=user.id, mode="quick", status="in_progress", consent_accepted=True)
    db.add(assessment)
    db.commit()
    result = complete_assessment_session(db, assessment, item)
    assert result["status"] == "incomplete"
    assert result["missing_required_items"]


def test_reject_hides_match_and_roadmap_draft_requires_explicit_action():
    db = session()
    _, item = complete_demo_assessment(db)
    match = db.scalar(select(CareerMatch).where(CareerMatch.profile_id == item.id, CareerMatch.category != "augment_current_profession"))
    assert match is not None
    set_match_status(db, match, "rejected", "Not for me")
    assert match.id not in {row["id"] for row in career_matches_for_profile(db, item.id)}
    visible = db.scalar(select(CareerMatch).where(CareerMatch.profile_id == item.id, CareerMatch.status == "suggested"))
    draft = create_roadmap_draft_from_match(db, visible)
    assert draft["actions"]
    roadmap = db.scalar(select(Roadmap).where(Roadmap.profile_id == item.id))
    assert roadmap is not None
    assert db.scalar(select(func.count()).select_from(RoadmapAction).where(RoadmapAction.roadmap_id == roadmap.id, RoadmapAction.source_type == "career_match")) == 4


def test_assessment_data_can_be_deleted_without_deleting_profile():
    db = session()
    _, item = complete_demo_assessment(db)
    assert db.scalar(select(func.count()).select_from(AssessmentSession).where(AssessmentSession.profile_id == item.id)) == 1
    result = delete_assessment_data(db, item.id)
    assert result["status"] == "deleted"
    assert db.get(Profile, item.id) is not None
    assert db.scalar(select(func.count()).select_from(AssessmentSession).where(AssessmentSession.profile_id == item.id)) == 0
    assert db.scalar(select(func.count()).select_from(CareerMatch).where(CareerMatch.profile_id == item.id)) == 0


def test_human_diagnostic_creates_persisted_hypotheses_without_promoting_evidence_or_roadmap():
    db = session()
    _, item = profile(db)
    item.data = generate_profile_fallback(
        "diagnostic-human",
        {
            "interests": ["Design", "Technology"],
            "preferred_orientation": ["Ideas", "People"],
            "natural_activities": ["research and prototyping"],
            "values": ["Creativity", "Learning"],
            "career_interests": {"artistic": 5, "investigative": 4, "social": 4, "realistic": 3, "enterprising": 2, "conventional": 2},
        },
    )
    db.commit()

    matches = career_matches_for_profile(db, item.id)
    assert matches
    assert all(match["session_id"] is None for match in matches)
    assert all(match["source_metadata"]["source_type"] == "human_diagnostic_hypothesis" for match in matches)
    assert all("SELF-REPORT" in match["source_metadata"]["input_sources"] for match in matches)
    assert all("MISSING" in match["source_metadata"]["input_sources"] for match in matches)
    assert db.scalar(select(func.count()).select_from(SkillsInventory).where(SkillsInventory.profile_id == item.id)) == 0
    assert db.scalar(select(func.count()).select_from(SkillEvidence)) == 0
    assert db.scalar(select(func.count()).select_from(CareerHypothesis).where(CareerHypothesis.profile_id == item.id)) == len(matches)
    assert db.scalar(select(func.count()).select_from(Roadmap).where(Roadmap.profile_id == item.id)) == 0
    assert {match["id"] for match in career_matches_for_profile(db, item.id)} == {match["id"] for match in matches}


def test_canonical_direction_prefers_the_deep_dive_snapshot_and_supersedes_the_diagnostic_duplicate():
    db = session()
    _, item = complete_demo_assessment(db)
    deep_dive = db.scalar(
        select(CareerMatch).where(
            CareerMatch.profile_id == item.id,
            CareerMatch.role_template_id == "human_centred_ai_product_designer",
        )
    )
    assert deep_dive is not None
    diagnostic = CareerMatch(
        profile_id=item.id,
        user_id=item.user_id,
        role_template_id=deep_dive.role_template_id,
        category=deep_dive.category,
        title=deep_dive.title,
        role_family=deep_dive.role_family,
        alignment_score=46.0,
        alignment_label="Developing alignment",
        source_metadata_json={
            "source_type": "human_diagnostic_hypothesis",
            "hypothesis_dimensions": {
                "scores": {
                    "natural_fit": 71.0,
                    "capability_fit": 17.0,
                    "evidence_strength": 20.0,
                    "transition_feasibility": 25.0,
                }
            },
        },
    )
    db.add(diagnostic)
    db.flush()
    canonical_id = f"role-template:{deep_dive.role_template_id}"
    stale = CareerHypothesis(
        profile_id=item.id,
        user_id=item.user_id,
        career_match_id=diagnostic.id,
        role_template_id=diagnostic.role_template_id,
        canonical_direction_id=canonical_id,
        title=diagnostic.title,
        status="active",
    )
    current = CareerHypothesis(
        profile_id=item.id,
        user_id=item.user_id,
        career_match_id=deep_dive.id,
        role_template_id=deep_dive.role_template_id,
        canonical_direction_id=canonical_id,
        title=deep_dive.title,
        status="active",
    )
    db.add_all([stale, current])
    db.commit()

    visible = career_matches_for_profile(db, item.id)
    matching_direction = [row for row in visible if row["canonical_direction_id"] == canonical_id]
    assert [row["id"] for row in matching_direction] == [deep_dive.id]
    assert matching_direction[0]["dimension_scores"]["capability_fit"] != diagnostic.source_metadata_json["hypothesis_dimensions"]["scores"]["capability_fit"]

    active = db.scalars(
        select(CareerHypothesis).where(
            CareerHypothesis.profile_id == item.id,
            CareerHypothesis.canonical_direction_id == canonical_id,
            CareerHypothesis.status == "active",
        )
    ).all()
    assert [row.id for row in active] == [current.id]
    assert db.get(CareerHypothesis, stale.id).status == "superseded"


def test_assessment_results_expose_per_module_progress_without_turning_missing_data_into_scores():
    db = session()
    user, item = profile(db)
    assessment = AssessmentSession(profile_id=item.id, user_id=user.id, mode="complete", status="in_progress", consent_accepted=True)
    db.add(assessment)
    db.flush()
    upsert_responses(
        db,
        assessment,
        [
            {"item_id": "personality_openness_ideas", "module_id": "personality_work_style", "value": 4},
            {"item_id": "interest_artistic_design", "module_id": "career_interests", "value": 5},
        ],
    )
    db.commit()

    results = results_for_profile(db, item.id)
    assert results["module_statuses"]["personality_work_style"]["status"] == "in_progress"
    assert results["module_statuses"]["career_interests"]["status"] == "in_progress"
    assert results["module_statuses"]["work_values"]["status"] == "not_started"
    assert results["scores"] == []
