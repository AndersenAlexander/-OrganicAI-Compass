from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from fastapi import HTTPException

from app.database import Base
from app.models.assessment import AssessmentSession, CareerMatch
from app.models.learning import (
    LearningObjective,
    LearningRecommendation,
    LearningRecommendationFactor,
    LearningRecommendationRun,
    LearningResource,
    LearningResourceFeedback,
    SkillGapItem,
)
from app.models.profile import Profile
from app.models.roadmap_adaptation import RoadmapAction
from app.models.user import User
from app.routers.learning import require_profile
from app.services.assessment_engine import complete_assessment_session, upsert_responses
from app.services.demo_seed_service import demo_assessment_responses
from app.services.learning_engine import (
    CuratedCatalogueProvider,
    LearningResourceQuery,
    NO_CAREER_SELECTED_MESSAGE,
    add_feedback,
    add_recommendation_to_roadmap,
    create_skill_gap_analysis,
    ensure_learning_preferences,
    generate_learning_path,
    generate_learning_recommendations,
    safe_resource_url,
    search_with_provider_fallback,
    sync_learning_catalogue,
    update_learning_preferences,
)


def session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def profile(db: Session) -> tuple[User, Profile]:
    user = User(name="Learning User", email="learning@example.test", hashed_password="x")
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


def test_catalogue_sync_and_unsafe_url_validation():
    db = session()
    sync_learning_catalogue(db)
    db.commit()
    assert db.scalar(select(func.count()).select_from(LearningResource)) >= 40
    assert safe_resource_url("https://react.dev/learn")
    assert safe_resource_url("/knowledge-base/ai_literacy")
    assert not safe_resource_url("javascript:alert(1)")


def test_no_career_selected_blocks_generic_recommendations():
    db = session()
    _, item = profile(db)
    result = generate_learning_recommendations(db, item)
    assert result["status"] == "no_career_selected"
    assert result["message"] == NO_CAREER_SELECTED_MESSAGE


def test_skill_gap_generation_prioritises_and_creates_objectives():
    db = session()
    _, item, match = complete_demo_assessment(db)
    result = create_skill_gap_analysis(db, item, match.id)
    assert result["status"] == "ready"
    assert result["items"]
    assert any(gap["status"] in {"Small gap", "Moderate gap", "Significant gap", "Evidence required"} for gap in result["items"])
    assert any(gap["priority_label"] in {"Essential", "High priority", "Recommended"} for gap in result["items"])
    assert db.scalar(select(func.count()).select_from(LearningObjective)) > 0


def test_learning_recommendations_rank_resources_and_store_factors():
    db = session()
    _, item, match = complete_demo_assessment(db)
    result = generate_learning_recommendations(db, item, match.id)
    assert result["status"] == "ready"
    assert result["recommendations"]
    resource_types = {rec["resource"]["resource_type"] for rec in result["recommendations"]}
    assert "official_documentation" in resource_types
    assert {"practical_project", "portfolio_project"} & resource_types
    recommendation = db.scalar(select(LearningRecommendation).where(LearningRecommendation.run_id == result["id"]))
    assert recommendation is not None
    assert db.scalar(select(func.count()).select_from(LearningRecommendationFactor).where(LearningRecommendationFactor.recommendation_id == recommendation.id)) == 10


def test_language_budget_duration_and_feedback_filters_are_deterministic():
    db = session()
    _, item, match = complete_demo_assessment(db)
    update_learning_preferences(
        db,
        item,
        {
            "preferred_language": "en",
            "acceptable_secondary_languages": [],
            "free_only": True,
            "strict_duration_limit_minutes": 600,
            "preferred_content_formats": ["Project-based", "Text"],
        },
    )
    first = generate_learning_recommendations(db, item, match.id)
    assert first["recommendations"]
    assert all(rec["resource"]["cost_type"] in {"free", "open"} for rec in first["recommendations"])
    assert all((rec["resource"]["duration_minutes"] or 0) <= 600 for rec in first["recommendations"] if rec["resource"]["duration_minutes"])
    add_feedback(db, db.get(LearningRecommendation, first["recommendations"][0]["id"]), {"reason_code": "already_completed"})
    second = generate_learning_recommendations(db, item, match.id)
    assert first["recommendations"][0]["learning_resource_id"] not in {rec["learning_resource_id"] for rec in second["recommendations"]}


def test_roadmap_confirmation_is_required_before_learning_action_is_added():
    db = session()
    _, item, match = complete_demo_assessment(db)
    result = generate_learning_recommendations(db, item, match.id)
    recommendation = db.get(LearningRecommendation, result["recommendations"][0]["id"])
    assert db.scalar(select(func.count()).select_from(RoadmapAction).where(RoadmapAction.profile_id == item.id, RoadmapAction.source_type == "learning_resource")) == 0
    add_recommendation_to_roadmap(db, recommendation, {"roadmap_title": "Learn responsibly", "expected_evidence": "Reflection and project note"})
    assert db.scalar(select(func.count()).select_from(RoadmapAction).where(RoadmapAction.profile_id == item.id, RoadmapAction.source_type == "learning_resource")) == 1


def test_learning_path_and_provider_failure_fallback():
    db = session()
    _, item, match = complete_demo_assessment(db)
    result = generate_learning_recommendations(db, item, match.id)
    path = generate_learning_path(db, item, result["id"])
    assert path["status"] == "draft"
    assert len(path["phases"]) == 5

    class TimeoutProvider:
        provider_name = "timeout_provider"

        def search_resources(self, query):
            raise TimeoutError("provider timeout")

        def get_resource(self, external_id):
            return None

        def check_availability(self, external_id):
            return None

    query = LearningResourceQuery(profile_id=item.id, skill_ids=["ux_ui"], objective_keys=[])
    resources, statuses = search_with_provider_fallback(db, [TimeoutProvider(), CuratedCatalogueProvider(db)], query)
    assert resources
    assert any(status["status"] == "timeout" for status in statuses)
    assert any(status["provider"] == "curated_catalogue" and status["status"] == "ok" for status in statuses)


def test_profile_ownership_is_enforced_for_learning_routes():
    db = session()
    owner, item, _ = complete_demo_assessment(db)
    other = User(name="Other", email="other@example.test", hashed_password="x")
    db.add(other)
    db.commit()
    assert require_profile(db, item.id, owner).id == item.id
    try:
        require_profile(db, item.id, other)
        assert False
    except HTTPException as error:
        assert error.status_code == 403
