from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.assessment import AssessmentSession, CareerMatch
from app.models.profile import Profile
from app.models.user import User
from app.services.assessment_engine import (
    HYPOTHESIS_RULESET,
    HYPOTHESIS_RULESET_VERSION,
    assessment_prefill_from_profile,
    compute_role_match,
    complete_assessment_session,
    hypothesis_dimensions,
    role_templates,
    upsert_responses,
)
from app.services.career_resilience_engine import add_manual_evidence, evidence_passport
from app.services.demo_seed_service import demo_assessment_responses
from app.services.profile_generation import assessment_prefill, generate_profile_fallback


def session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def role(role_id: str = "human_centred_ai_product_designer") -> dict:
    return next(item for item in role_templates() if item["id"] == role_id)


def scores(
    *,
    interests: dict[str, float] | None = None,
    values: list[str] | None = None,
    style: dict[str, float] | None = None,
    skill_level: int = 0,
    evidence_status: str = "self_reported",
    years: str = "0-1",
    change: float = 50,
) -> dict:
    template = role()
    skill_items = {
        skill: {"level": skill_level, "label": skill.replace("_", " ").title(), "evidence_status": evidence_status, "category": "test"}
        for skill in template["required_skills"] + template["useful_transferable_skills"]
    }
    return {
        "career_interests": {key: {"normalized_score": value} for key, value in (interests or {"artistic": 85, "investigative": 80, "social": 70, "enterprising": 55}).items()},
        "work_values": {"top_values": [{"value": value} for value in (values or ["creativity", "autonomy", "meaningful_impact", "continuous_learning"])]},
        "personality": {key: {"normalized_score": value} for key, value in (style or {"openness": 82, "conscientiousness": 65, "agreeableness": 70}).items()},
        "skills": {"items": skill_items},
        "ai_literacy": {"ai_literacy": {"normalized_score": 60}, "ai_readiness": {"normalized_score": 60}},
        "change_readiness": {"normalized_score": change},
        "goals_constraints": {"years_experience": years},
    }


def test_a_same_natural_preferences_different_experience_changes_capability_not_natural_fit():
    low_experience = hypothesis_dimensions(role(), scores(years="0-1", skill_level=2))
    high_experience = hypothesis_dimensions(role(), scores(years="10+", skill_level=2))

    assert low_experience["scores"]["natural_fit"] == high_experience["scores"]["natural_fit"]
    assert high_experience["scores"]["capability_fit"] > low_experience["scores"]["capability_fit"]


def test_b_same_skills_different_evidence_changes_evidence_not_capability_fit():
    self_reported = hypothesis_dimensions(role(), scores(skill_level=3, evidence_status="self_reported"))
    project_supported = hypothesis_dimensions(role(), scores(skill_level=3, evidence_status="supported_by_project"))

    assert self_reported["scores"]["capability_fit"] == project_supported["scores"]["capability_fit"]
    assert project_supported["scores"]["evidence_strength"] > self_reported["scores"]["evidence_strength"]


def test_c_strong_natural_fit_weak_capability_remains_worth_testing():
    computation = compute_role_match(role(), scores(skill_level=0, evidence_status="self_reported", change=65))

    assert computation.dimensions["labels"]["natural_fit"] in {"Moderate", "Strong"}
    assert computation.dimensions["labels"]["capability_fit"] == "Limited"
    assert computation.dimensions["labels"]["evidence_strength"] == "Limited"
    assert any("career experiment" in item.lower() for item in computation.conflicting)


def test_d_strong_historical_experience_does_not_create_strong_natural_fit():
    conventional_role = role("data_analyst")
    weak_preference = scores(
        interests={"conventional": 20, "investigative": 25, "realistic": 20, "enterprising": 20},
        values=["creativity", "autonomy"],
        style={"conscientiousness": 25, "openness": 30},
        skill_level=4,
        evidence_status="practically_verified",
        years="10+",
    )
    weak_preference["skills"]["items"] = {
        skill: {"level": 4, "label": skill.replace("_", " ").title(), "evidence_status": "practically_verified", "category": "historical"}
        for skill in conventional_role["required_skills"] + conventional_role["useful_transferable_skills"]
    }
    dimensions = hypothesis_dimensions(conventional_role, weak_preference)

    assert dimensions["labels"]["capability_fit"] in {"Moderate", "Strong"}
    assert dimensions["labels"]["evidence_strength"] in {"Moderate", "Strong"}
    assert dimensions["labels"]["natural_fit"] != "Strong"


def test_e_constraints_change_transition_feasibility_without_changing_natural_fit():
    constrained = hypothesis_dimensions(role(), scores(skill_level=2, change=25))
    unconstrained = hypothesis_dimensions(role(), scores(skill_level=2, change=85))

    assert constrained["scores"]["natural_fit"] == unconstrained["scores"]["natural_fit"]
    assert unconstrained["scores"]["transition_feasibility"] > constrained["scores"]["transition_feasibility"]


def test_f_self_report_then_verified_project_evidence_increases_evidence_strength_only():
    before = hypothesis_dimensions(role(), scores(skill_level=3, evidence_status="self_reported"))
    after = hypothesis_dimensions(role(), scores(skill_level=3, evidence_status="practically_verified"))

    assert after["scores"]["evidence_strength"] > before["scores"]["evidence_strength"]
    assert after["scores"]["capability_fit"] == before["scores"]["capability_fit"]
    assert after["rule_set"] == HYPOTHESIS_RULESET
    assert after["rule_set_version"] == HYPOTHESIS_RULESET_VERSION


def test_g_course_completion_is_not_practical_verification():
    db = session()
    user = User(name="Evidence User", email="evidence-task15b@example.test", hashed_password="x")
    db.add(user)
    db.flush()
    profile = Profile(user_id=user.id, diagnostic_id="diagnostic", data={})
    db.add(profile)
    db.flush()
    assessment = AssessmentSession(profile_id=profile.id, user_id=user.id, mode="complete", status="in_progress", consent_accepted=True)
    db.add(assessment)
    db.flush()
    upsert_responses(db, assessment, demo_assessment_responses())
    assert complete_assessment_session(db, assessment, profile)["status"] == "completed"

    add_manual_evidence(
        db,
        profile,
        {
            "skill_id": "ux_ui",
            "evidence_type": "course_completion",
            "title": "Course only",
            "description": "Educational exposure without practical artifact.",
            "score_hint": 80,
        },
    )
    ux = next(skill for skill in evidence_passport(db, profile.id)["skills"] if skill["skill_id"] == "ux_ui")

    assert ux["strongest_evidence_label"] != "Practically verified"
    assert "Course completion alone does not create practical verification" in evidence_passport(db, profile.id)["methodology"]


def test_diagnostic_profile_prefill_is_confirm_edit_not_persisted_assessment_data():
    payload = {
        "interests": ["Design", "Technology", "Community"],
        "natural_activities": ["Sketching interfaces"],
        "preferred_orientation": ["Visual creation", "People"],
        "values": ["Creativity", "Learning"],
        "skills": ["Design", "Communication"],
        "preferred_learning_style": ["Hands-on practice"],
        "cognitive_style": ["Visual"],
        "ai_experience": "Intermediate",
        "ai_confidence": 8,
    }
    profile_data = generate_profile_fallback("diagnostic-1", payload)
    db = session()
    user = User(name="Prefill User", email="prefill-task15b@example.test", hashed_password="x")
    db.add(user)
    db.flush()
    profile = Profile(user_id=user.id, diagnostic_id="diagnostic-1", data=profile_data)
    db.add(profile)
    db.commit()

    direct = assessment_prefill(payload)
    from_profile = assessment_prefill_from_profile(profile)

    assert "skill_ux_ui" in direct["responses"]
    assert direct["responses"]["skill_ux_ui"]["evidence_status"] == "self_reported"
    assert from_profile["strategy"].startswith("Assessment may show")
    assert db.scalar(select(AssessmentSession).where(AssessmentSession.profile_id == profile.id)) is None
