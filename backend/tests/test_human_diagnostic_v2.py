from app.services.assessment_engine import assessment_definition
from app.services.profile_generation import calculate_quick_diagnostic_scores


def diagnostic_payload(**overrides):
    payload = {
        "interests": ["Design", "Technology"],
        "natural_activities": ["research and prototyping"],
        "preferred_orientation": ["Ideas", "People"],
        "curiosity_score": 6,
        "practical_conceptual": 2,
        "creative_analytical": 6,
        "exploration_scenario": "look for examples or prior evidence",
        "values": ["Creativity", "Learning"],
        "value_priorities": ["Autonomy", "Learning"],
        "value_tradeoff": "right",
        "meaningful_work_acceptability": 5,
        "preferred_learning_style": ["Hands-on practice"],
        "learning_mode": "right",
        "decision_style": "Try the smallest reversible step",
        "fears": ["rapid change"],
        "fear_dimensions": {"job_displacement": 4, "learning_anxiety": 3},
        "fear_management": "A small experiment and clearer information",
        "ai_experience": "Beginner",
        "ai_roles": ["Tutor", "Critic"],
        "ai_never_decisions": ["My core values"],
        "ai_confidence": 4,
        "ai_explanation_need": 6,
        "ai_oversight": 6,
        "ai_automation_comfort": 3,
        "ai_help_goals": ["Learn faster"],
        "capability_confidence": {"Communication": 5},
    }
    return {**payload, **overrides}


def test_quick_scores_are_deterministic_and_keep_evidence_separate():
    first = calculate_quick_diagnostic_scores(diagnostic_payload())
    second = calculate_quick_diagnostic_scores(diagnostic_payload())

    assert first == second
    capability = next(item for item in first["sections"] if item["key"] == "capability_self_report")
    assert capability["source"] == "SELF-REPORT"
    assert capability["evidence_status"] == "MISSING"
    assert first["profile_completeness"] in {"Limited", "Moderate", "Good"}


def test_quick_scores_surface_mixed_signals_instead_of_averaging_them_away():
    result = calculate_quick_diagnostic_scores(diagnostic_payload(practical_conceptual=1, creative_analytical=7, meaningful_work_acceptability=1, value_tradeoff="left"))

    assert result["contradictions"]
    assert any("Mixed" not in item for item in result["contradictions"])
    assert result["areas_of_uncertainty"]


def test_personality_tendencies_prototype_has_balanced_thirty_items_and_reverse_scoring():
    definition = assessment_definition()
    items = [item for item in definition["items"] if item["module_id"] == "personality_work_style"]
    assert len(items) == 30
    assert {item["dimension"] for item in items} == {"openness", "conscientiousness", "extraversion", "agreeableness", "emotional_stability"}
    assert all(sum(item["dimension"] == dimension for item in items) == 6 for dimension in {item["dimension"] for item in items})
    assert sum(item["reverse_scored"] for item in items) >= 5
