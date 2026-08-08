from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.assessment import AssessmentResponse, AssessmentScore, AssessmentSession, CareerMatch
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
    reverse_score,
    set_match_status,
    upsert_responses,
)
from app.services.demo_seed_service import demo_assessment_responses


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
