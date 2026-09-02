import asyncio

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.database import Base
from app.models.assessment import SkillEvidence
from app.models.career_resilience import CareerEvidenceGap, CareerHypothesis
from app.models.diagnostic import Diagnostic
from app.models.learning import LearningPreferences
from app.models.profile import Profile
from app.models.recommendation import Recommendation
from app.models.user import User
from app.routers.roadmap import grounded_roadmap_data, roadmap_generation_context
from app.services.recommendation_engine import generate_recommendations


def session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def grounded_profile(db: Session) -> Profile:
    user = User(name="QA User", email="output-quality@example.test", hashed_password="x")
    db.add(user)
    db.flush()
    diagnostic = Diagnostic(user_id=user.id, status="completed", diagnostic_version="human-diagnostic-v2", payload={"preferred_learning_style": ["hands-on practice"]})
    db.add(diagnostic)
    db.flush()
    profile = Profile(
        user_id=user.id,
        diagnostic_id=diagnostic.id,
        data={
            "quick_diagnostic": {"completed": True},
            "human_potential_map": {"version": "v2"},
            "primary_archetype": {"name": "Curious Builder"},
            "strengths": ["Research", "Design"],
            "values": ["Human-centred judgment"],
            "user_feedback": {"strength_adjustments": {"Research": 80, "Design": 70}},
        },
    )
    db.add(profile)
    db.flush()
    hypotheses = [
        CareerHypothesis(profile_id=profile.id, user_id=user.id, title="UX Designer for AI Systems", status="active", current_alignment_score=0.8, current_version_number=2),
        CareerHypothesis(profile_id=profile.id, user_id=user.id, title="Learning Experience Designer", status="active", current_alignment_score=0.7, current_version_number=1),
    ]
    db.add_all(hypotheses)
    db.flush()
    db.add_all([
        CareerEvidenceGap(profile_id=profile.id, user_id=user.id, hypothesis_id=hypotheses[0].id, capability_label="Critical Thinking", importance=0.9, status="MISSING", reason="No reviewable evidence is stored for this capability.", suggested_action="Complete one bounded analysis artefact and review it."),
        CareerEvidenceGap(profile_id=profile.id, user_id=user.id, hypothesis_id=hypotheses[1].id, capability_label="Communication", importance=0.8, status="SELF_REPORT_ONLY", reason="The current signal is self-report only.", suggested_action="Create one concise learning explanation and collect feedback."),
    ])
    db.add(LearningPreferences(profile_id=profile.id, user_id=user.id, available_hours_per_week=6, preferred_content_formats_json=["Hands-on", "Reflection"], theory_practice_preference="practice"))
    db.commit()
    return profile


def test_roadmap_proposals_are_specific_ordered_and_human_traceable():
    db = session()
    profile = grounded_profile(db)

    context = roadmap_generation_context(db, profile)
    roadmap = grounded_roadmap_data({"seven_days": [], "thirty_days": [], "six_months": []}, context)
    actions = [*roadmap["seven_days"], *roadmap["thirty_days"], *roadmap["six_months"]]

    assert actions
    assert len({item["title"] for item in actions}) == len(actions)
    assert actions[0]["priority"] == 1
    assert "Critical Thinking" in actions[0]["title"]
    assert "UX Designer for AI Systems" in actions[0]["reason"]
    assert any(label.startswith("Career Hypothesis:") for label in actions[0]["source_labels"])
    assert any(label.startswith("Evidence Gap:") for label in actions[0]["source_labels"])
    assert actions[0]["estimated_minutes"] <= actions[2]["estimated_minutes"]
    assert all("Improve your skills" not in item["title"] for item in actions)


def test_recommendations_use_current_sources_remain_distinct_and_preserve_history(monkeypatch):
    db = session()
    profile = grounded_profile(db)

    async def no_knowledge_sources(_query):
        return []

    monkeypatch.setattr("app.services.recommendation_engine.search_knowledge_base", no_knowledge_sources)

    first = asyncio.run(generate_recommendations(db, profile, profile.user_id, None, False))
    first_titles = {item["title"] for item in first["recommendations"]}
    assert len(first_titles) == len(first["recommendations"])
    assert len({item["category"] for item in first["recommendations"]}) >= 4
    assert all(any(signal["source"] == "career_hypothesis" for signal in item["profile_signals"]) for item in first["recommendations"])
    assert all(any(signal["source"] == "evidence_gap" for signal in item["profile_signals"]) for item in first["recommendations"])
    assert all(any("does not confirm" in note.lower() for note in item["what_to_verify"]) for item in first["recommendations"])
    assert all("improve your skills" not in item["title"].lower() for item in first["recommendations"])
    assert db.scalar(select(func.count()).select_from(SkillEvidence)) == 0

    original_ids = {item["id"] for item in first["recommendations"]}
    second = asyncio.run(generate_recommendations(db, profile, profile.user_id, None, True))
    second_titles = {item["title"] for item in second["recommendations"]}
    assert second_titles
    assert first_titles.isdisjoint(second_titles)
    assert db.scalar(select(func.count()).select_from(Recommendation).where(Recommendation.profile_id == profile.id)) == len(first["recommendations"]) + len(second["recommendations"])
    archived = db.scalars(select(Recommendation).where(Recommendation.id.in_(original_ids))).all()
    assert archived and all(item.status == "archived" for item in archived)
