from app.services.profile_generation import (
    RIASEC_RULE_SET_VERSION,
    assessment_prefill,
    generate_profile_fallback,
    riasec_career_interests,
)


DIMENSIONS = ["realistic", "investigative", "artistic", "social", "enterprising", "conventional"]


def payload_with(**career_interests: int) -> dict:
    values = {dimension: 1 for dimension in DIMENSIONS}
    values.update(career_interests)
    return {
        "interests": ["Design"],
        "natural_activities": ["Exploring ideas"],
        "preferred_orientation": ["Visual creation"],
        "career_interests": values,
        "values": ["Creativity"],
        "preferred_learning_style": ["Hands-on practice"],
        "cognitive_style": ["Exploratory"],
    }


def score_for(payload: dict, dimension: str) -> float:
    result = riasec_career_interests(payload)
    score = result["dimensions"][dimension]["score"]
    assert score is not None
    return score


def test_realistic_direct_interest_scores_high_without_capability_claim():
    result = riasec_career_interests(payload_with(realistic=5))

    assert result["rule_set_version"] == RIASEC_RULE_SET_VERSION
    assert result["dimensions"]["realistic"]["band"] == "High"
    assert "capability" in result["limitations"][2].lower()


def test_investigative_direct_interest_scores_high():
    assert riasec_career_interests(payload_with(investigative=5))["dimensions"]["investigative"]["band"] == "High"


def test_artistic_direct_interest_scores_high():
    assert riasec_career_interests(payload_with(artistic=5))["dimensions"]["artistic"]["band"] == "High"


def test_social_direct_interest_scores_high():
    assert riasec_career_interests(payload_with(social=5))["dimensions"]["social"]["band"] == "High"


def test_enterprising_direct_interest_scores_high():
    assert riasec_career_interests(payload_with(enterprising=5))["dimensions"]["enterprising"]["band"] == "High"


def test_conventional_direct_interest_scores_high():
    assert riasec_career_interests(payload_with(conventional=5))["dimensions"]["conventional"]["band"] == "High"


def test_balanced_user_has_no_artificially_dominant_code():
    result = riasec_career_interests(
        {
            "interests": [],
            "natural_activities": [],
            "preferred_orientation": [],
            "career_interests": {dimension: 3 for dimension in DIMENSIONS},
            "preferred_learning_style": [],
            "cognitive_style": [],
        }
    )
    scores = {dimension: item["score"] for dimension, item in result["dimensions"].items()}

    assert len(set(scores.values())) == 1
    assert result["close_score_notice"]


def test_missing_data_returns_insufficient_information():
    result = riasec_career_interests({"interests": [], "preferred_orientation": []})

    assert result["status"] == "insufficient_information"
    assert result["top_pattern"] == ""


def test_assessment_prefill_uses_direct_interests_for_confirm_edit():
    payload = payload_with(artistic=2, investigative=5)
    payload["interests"] = ["Design", "Science"]
    prefill = assessment_prefill(payload)

    assert prefill["responses"]["interest_artistic_design"] == 2
    assert prefill["responses"]["interest_investigative_research"] == 5
    assert "confirm or edit" in prefill["notes"]["interest_artistic_design"].lower()


def test_experience_evidence_and_constraints_do_not_rewrite_riasec_interests():
    base = payload_with(artistic=5, conventional=1)
    altered = {
        **base,
        "skills": ["Leadership", "Analysis", "Building"],
        "ai_experience": "Advanced",
        "ai_confidence": 10,
        "raw_answers": {"budget": "high", "time": "10+ hours", "portfolio": "many projects"},
    }

    assert riasec_career_interests(base)["dimensions"] == riasec_career_interests(altered)["dimensions"]


def test_high_artistic_interest_can_coexist_with_conventional_experience_signals():
    payload = payload_with(artistic=5, conventional=1)
    payload.update(
        {
            "skills": ["Analysis", "Leadership", "Building"],
            "raw_answers": {"career_history": "20 years in structured administration and documented operations."},
        }
    )
    profile = generate_profile_fallback("diagnostic-task16a", payload)
    interests = profile["natural_discovery_snapshot"]["career_interests"]["dimensions"]

    assert interests["artistic"]["band"] == "High"
    assert interests["conventional"]["band"] in {"Limited", "Lower"}
