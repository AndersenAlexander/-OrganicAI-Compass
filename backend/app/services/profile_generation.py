from datetime import datetime
from app.core.time import utc_now_naive
import json

from openai import AsyncOpenAI

from app.config import get_settings, resolve_active_openai_api_key


def _list(value) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)] if value and str(value).strip() else []


def _slug(value: str) -> str:
    return value.lower().replace("&", "and").replace("/", " ").replace("-", " ").replace(" ", "_")


def _average(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 50.0


RIASEC_RULE_SET_VERSION = "riasec-career-interests-v1"

RIASEC_DIMENSIONS: dict[str, dict[str, str]] = {
    "realistic": {
        "code": "R",
        "label": "Realistic",
        "description": "Interest in practical hands-on activity, tools, physical systems, building, repair, or technical operations.",
    },
    "investigative": {
        "code": "I",
        "label": "Investigative",
        "description": "Interest in analysis, research, data, science, complex questions, and understanding how systems work.",
    },
    "artistic": {
        "code": "A",
        "label": "Artistic",
        "description": "Interest in design, writing, visual expression, originality, aesthetics, imagination, or creating new concepts.",
    },
    "social": {
        "code": "S",
        "label": "Social",
        "description": "Interest in helping, teaching, mentoring, supporting, communicating, collaboration, or human development.",
    },
    "enterprising": {
        "code": "E",
        "label": "Enterprising",
        "description": "Interest in initiating projects, influencing, persuading, negotiating, entrepreneurship, or leading decisions.",
    },
    "conventional": {
        "code": "C",
        "label": "Conventional",
        "description": "Interest in organization, structured processes, accuracy, documentation, planning, procedures, or predictable systems.",
    },
}

_DIRECT_INTEREST_FIELDS = {
    "realistic": "interest_realistic_practical",
    "investigative": "interest_investigative_research",
    "artistic": "interest_artistic_design",
    "social": "interest_social_teaching",
    "enterprising": "interest_enterprising_lead",
    "conventional": "interest_conventional_structure",
}

_LEGACY_RIASEC_SIGNALS: dict[str, dict[str, float]] = {
    "education": {"social": 0.85},
    "design": {"artistic": 0.9},
    "technology": {"investigative": 0.72, "realistic": 0.45},
    "nature": {"realistic": 0.65},
    "storytelling": {"artistic": 0.85},
    "well-being": {"social": 0.8},
    "science": {"investigative": 0.9},
    "community": {"social": 0.8},
    "people": {"social": 0.8},
    "ideas": {"investigative": 0.78},
    "systems": {"investigative": 0.7, "conventional": 0.45},
    "visual creation": {"artistic": 0.9},
    "learning": {"investigative": 0.55},
    "hands-on practice": {"realistic": 0.58},
    "visual examples": {"artistic": 0.45},
    "reading and reflection": {"investigative": 0.45},
    "conversation and feedback": {"social": 0.45},
    "structured": {"conventional": 0.6},
    "exploratory": {"investigative": 0.4, "artistic": 0.4},
    "visual": {"artistic": 0.45},
    "practical": {"realistic": 0.55},
    "social": {"social": 0.45},
    "plan projects": {"enterprising": 0.45, "conventional": 0.35},
    "make decisions": {"enterprising": 0.4},
    "automate repetition": {"conventional": 0.35, "realistic": 0.3},
}

_TEXT_RIASEC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "realistic": ("hands-on", "tool", "tools", "build", "repair", "machine", "equipment", "physical", "technical", "practical"),
    "investigative": ("research", "analysis", "data", "science", "investigate", "experiment", "evidence", "system", "complex"),
    "artistic": ("design", "write", "writing", "visual", "story", "creative", "art", "concept", "aesthetic", "imagination"),
    "social": ("help", "teach", "mentor", "support", "people", "community", "care", "communicate", "collaborate"),
    "enterprising": ("lead", "persuade", "business", "entrepreneur", "negotiate", "initiate", "sell", "influence"),
    "conventional": ("organize", "organise", "structure", "document", "plan", "procedure", "accurate", "administration", "process"),
}


def _career_interest_response(payload: dict, dimension: str) -> int | None:
    values = payload.get("career_interests")
    if not isinstance(values, dict):
        return None
    try:
        raw = int(values.get(dimension))
    except (TypeError, ValueError):
        return None
    return max(1, min(5, raw))


def _response_score(value: int) -> float:
    return round(((value - 1) / 4) * 100, 2)


def _interest_band(score: float | None) -> str:
    if score is None:
        return "Insufficient information"
    if score >= 75:
        return "High"
    if score >= 60:
        return "Moderate-High"
    if score >= 45:
        return "Moderate"
    if score >= 25:
        return "Lower"
    return "Limited"


def _add_signal(signals: dict[str, list[dict]], dimension: str, score: float, strength: str, source: str) -> None:
    signals.setdefault(dimension, []).append({"score": max(0, min(100, score)), "strength": strength, "source": source})


def riasec_career_interests(payload: dict) -> dict:
    signals: dict[str, list[dict]] = {dimension: [] for dimension in RIASEC_DIMENSIONS}
    direct_count = 0

    for dimension in RIASEC_DIMENSIONS:
        response = _career_interest_response(payload, dimension)
        if response is not None:
            direct_count += 1
            _add_signal(signals, dimension, _response_score(response), "DIRECT", "natural_discovery_career_interests")

    for field in ["interests", "preferred_orientation", "preferred_learning_style", "cognitive_style", "ai_help_goals"]:
        for selected in _list(payload.get(field)):
            mapped = _LEGACY_RIASEC_SIGNALS.get(selected.lower())
            if not mapped:
                continue
            for dimension, weight in mapped.items():
                _add_signal(signals, dimension, 50 + (weight * 40), "INDIRECT", f"legacy_{field}:{selected}")

    text_sources = []
    for field in ["natural_activities", "problems_noticed"]:
        text_sources.extend(_list(payload.get(field)))
    for field in ["desired_world", "contribution_if_supported"]:
        if payload.get(field):
            text_sources.append(str(payload.get(field)))
    raw_answers = payload.get("raw_answers") if isinstance(payload.get("raw_answers"), dict) else {}
    if raw_answers.get("human_needs"):
        text_sources.append(str(raw_answers["human_needs"]))
    for text in text_sources:
        lowered = text.lower()
        for dimension, keywords in _TEXT_RIASEC_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                _add_signal(signals, dimension, 62, "WEAK", f"free_text:{text[:80]}")

    scored_dimensions = 0
    dimensions: dict[str, dict] = {}
    for dimension, meta in RIASEC_DIMENSIONS.items():
        entries = signals[dimension]
        direct_entries = [entry for entry in entries if entry["strength"] == "DIRECT"]
        indirect_entries = [entry for entry in entries if entry["strength"] == "INDIRECT"]
        weak_entries = [entry for entry in entries if entry["strength"] == "WEAK"]
        if entries:
            scored_dimensions += 1
            direct_weight = sum(entry["score"] * 1.0 for entry in direct_entries)
            indirect_weight = sum(entry["score"] * 0.65 for entry in indirect_entries)
            weak_weight = sum(entry["score"] * 0.35 for entry in weak_entries)
            total_weight = (len(direct_entries) * 1.0) + (len(indirect_entries) * 0.65) + (len(weak_entries) * 0.35)
            score = round((direct_weight + indirect_weight + weak_weight) / total_weight, 2)
        else:
            score = None
        dimensions[dimension] = {
            "code": meta["code"],
            "label": meta["label"],
            "description": meta["description"],
            "score": score,
            "band": _interest_band(score),
            "direct_items": len(direct_entries),
            "indirect_items": len(indirect_entries),
            "weak_items": len(weak_entries),
            "scoring_opportunities": len(entries),
            "response": _career_interest_response(payload, dimension),
        }

    if direct_count == len(RIASEC_DIMENSIONS):
        status = "complete"
    elif scored_dimensions >= 3:
        status = "derived_from_legacy"
    else:
        status = "insufficient_information"

    ranked = sorted(
        ((dimension, data) for dimension, data in dimensions.items() if data["score"] is not None),
        key=lambda item: item[1]["score"],
        reverse=True,
    )
    top_three = [dimension for dimension, _ in ranked[:3]] if status != "insufficient_information" else []
    top_pattern = "-".join(dimensions[dimension]["code"] for dimension in top_three)
    close_notice = ""
    if len(ranked) >= 3 and ranked[0][1]["score"] - ranked[2][1]["score"] <= 8:
        close_notice = "Several interest dimensions are closely balanced; avoid treating the first code as decisively dominant."

    return {
        "model": "RIASEC-inspired Career Interests",
        "rule_set_version": RIASEC_RULE_SET_VERSION,
        "status": status,
        "dimensions": dimensions,
        "top_dimensions": top_three,
        "top_pattern": top_pattern,
        "close_score_notice": close_notice,
        "source": "Natural Discovery responses",
        "limitations": [
            "This is a transparent vocational-interest signal, not a clinical or personality diagnosis.",
            "Scores are platform-relative response summaries, not population norms.",
            "Interest does not imply current capability, demonstrated evidence, transition feasibility, market fit, or employment probability.",
        ],
    }


def natural_discovery_snapshot(payload: dict) -> dict:
    return {
        "version": "natural-discovery-v2-riasec",
        "source": "diagnostic",
        "role": "preference-oriented initial discovery",
        "interests": _list(payload.get("interests")),
        "preferred_activities": _list(payload.get("natural_activities")),
        "problems_noticed": _list(payload.get("problems_noticed")),
        "preferred_orientation": _list(payload.get("preferred_orientation")),
        "career_interests": riasec_career_interests(payload),
        "values": _list(payload.get("values")),
        "preferred_learning_style": _list(payload.get("preferred_learning_style")),
        "cognitive_style": _list(payload.get("cognitive_style")),
        "excluded_from_natural_fit": {
            "skills": _list(payload.get("skills")),
            "ai_experience": payload.get("ai_experience") or "",
            "ai_confidence": payload.get("ai_confidence"),
            "ai_tools_used": _list(payload.get("ai_tools_used")),
            "reason": "Capability and exposure fields may prefill deeper assessment but do not drive Natural Fit.",
        },
        "limitations": [
            "This is a lightweight discovery snapshot, not a psychological profile.",
            "Historical experience, current skill, evidence, market demand, budget, and time constraints are excluded from Natural Fit.",
        ],
    }


def _qualitative_band(value: float | None) -> str:
    if value is None:
        return "Insufficient data"
    if value < 2.75:
        return "Lower"
    if value < 4.75:
        return "Moderate"
    return "Higher"


def _profile_confidence(answered: int, total: int, contradictions: int = 0) -> str:
    coverage = answered / max(1, total)
    if coverage < 0.35:
        return "Limited"
    if coverage < 0.75 or contradictions:
        return "Moderate"
    return "Good"


def calculate_quick_diagnostic_scores(payload: dict) -> dict:
    """Deterministic, inspectable interpretation for the five-step diagnostic.

    These are qualitative response summaries. They are not norms, probabilities,
    psychometric scores, or predictions of career success.
    """

    curiosity = payload.get("curiosity_score")
    fear_dimensions = payload.get("fear_dimensions") if isinstance(payload.get("fear_dimensions"), dict) else {}
    capabilities = payload.get("capability_confidence") if isinstance(payload.get("capability_confidence"), dict) else {}
    ai_values = [payload.get("ai_confidence"), payload.get("ai_explanation_need"), payload.get("ai_oversight"), payload.get("ai_automation_comfort")]
    ai_values = [float(value) for value in ai_values if isinstance(value, (int, float))]
    practical = payload.get("practical_conceptual")
    exploratory = payload.get("creative_analytical")
    contradictions: list[str] = []
    if isinstance(practical, (int, float)) and isinstance(exploratory, (int, float)) and abs(float(practical) - float(exploratory)) >= 4:
        contradictions.append("Practical and exploratory preferences pull in different directions; context may matter.")
    if payload.get("value_tradeoff") and payload.get("meaningful_work_acceptability") in {1, 2}:
        contradictions.append("Meaning and advancement may need a closer trade-off conversation.")

    fields = [
        payload.get("interests"), payload.get("natural_activities"), payload.get("preferred_orientation"),
        payload.get("fears"), payload.get("values"), payload.get("preferred_learning_style"),
        payload.get("ai_experience"), payload.get("ai_help_goals"), curiosity,
        payload.get("exploration_scenario"), payload.get("fear_management"), payload.get("value_tradeoff"),
        payload.get("learning_mode"), payload.get("decision_style"), payload.get("ai_roles"),
    ]
    answered = sum(1 for value in fields if value not in (None, "", [], {})) + len(capabilities) + len(fear_dimensions)
    total = len(fields) + 8
    confidence = _profile_confidence(answered, total, len(contradictions))

    sections = [
        {
            "key": "natural_tendencies",
            "title": "Natural Tendencies",
            "summary": "Current preferences for exploring, creating, analysing, and engaging with people or systems.",
            "signals": [*_list(payload.get("preferred_orientation"))[:3], _qualitative_band(curiosity) if isinstance(curiosity, (int, float)) else "Emerging signal"],
            "source": "SELF-REPORT · DIAGNOSTIC",
            "evidence_status": "MISSING",
            "confidence": confidence,
        },
        {
            "key": "values",
            "title": "Values & Contribution",
            "summary": "Values you currently want to protect and the contribution you would like to explore.",
            "signals": _list(payload.get("value_priorities"))[:4] or _list(payload.get("values"))[:4],
            "source": "SELF-REPORT · DIAGNOSTIC",
            "evidence_status": "SELF-REPORT",
            "confidence": confidence,
        },
        {
            "key": "work_style",
            "title": "Work & Learning Style",
            "summary": "Preferred ways of learning, deciding, collaborating, and adapting; not a fixed trait label.",
            "signals": [*_list(payload.get("preferred_learning_style"))[:2], payload.get("learning_mode") or "Learning preference emerging"],
            "source": "SELF-REPORT · DIAGNOSTIC",
            "evidence_status": "MISSING",
            "confidence": confidence,
        },
        {
            "key": "career_interests",
            "title": "Career Interests",
            "summary": "RIASEC-inspired Career Interest Signals based on current preferred activities, not a validated RIASEC assessment.",
            "signals": riasec_career_interests(payload).get("top_dimensions", []),
            "source": "DIAGNOSTIC · DETERMINISTIC",
            "evidence_status": "SELF-REPORT",
            "confidence": "Good" if riasec_career_interests(payload).get("status") == "complete" else "Moderate",
        },
        {
            "key": "capability_self_report",
            "title": "Capability Self-Report",
            "summary": "Your current view of capability. Evidence is intentionally kept separate and is not promoted automatically.",
            "signals": [f"{key}: {_qualitative_band(float(value))}" for key, value in list(capabilities.items())[:5] if isinstance(value, (int, float))],
            "source": "SELF-REPORT",
            "evidence_status": "MISSING",
            "confidence": "Moderate" if capabilities else "Insufficient data",
        },
        {
            "key": "ai_collaboration",
            "title": "AI Collaboration Style",
            "summary": "How much explanation, oversight, delegation, and human control you currently prefer when working with AI.",
            "signals": _list(payload.get("ai_roles"))[:4],
            "source": "SELF-REPORT · DIAGNOSTIC",
            "evidence_status": "SELF-REPORT",
            "confidence": _profile_confidence(len(ai_values), 4),
        },
    ]
    return {
        "version": "human-diagnostic-scoring-v2",
        "answered_fields": answered,
        "total_fields": total,
        "profile_completeness": confidence,
        "contradictions": contradictions,
        "areas_of_uncertainty": [
            "Responses describe current self-perception and preferences; they do not verify capability.",
            "Context, opportunity, resources, and lived experience may change how these signals appear.",
            *contradictions,
        ],
        "sections": sections,
        "raw_signals": {
            "curiosity": _qualitative_band(float(curiosity)) if isinstance(curiosity, (int, float)) else "Insufficient data",
            "fear_intensity": fear_dimensions,
            "ai_collaboration": _qualitative_band(sum(ai_values) / len(ai_values)) if ai_values else "Insufficient data",
        },
    }


def assessment_prefill(payload: dict) -> dict:
    responses: dict[str, object] = {}
    notes: dict[str, str] = {}

    interest_map = {
        "design": ["interest_artistic_design", "interest_artistic_original"],
        "storytelling": ["interest_artistic_design"],
        "technology": ["interest_investigative_research", "interest_realistic_practical"],
        "science": ["interest_investigative_research", "interest_investigative_evidence"],
        "education": ["interest_social_teaching", "interest_social_growth"],
        "well-being": ["interest_social_teaching"],
        "community": ["interest_social_teaching", "interest_social_growth"],
        "nature": ["interest_realistic_practical"],
    }
    orientation_map = {
        "people": ["interest_social_teaching", "personality_agreeableness_effects"],
        "ideas": ["interest_investigative_research", "personality_openness_ideas"],
        "systems": ["interest_investigative_evidence", "personality_conscientious_plan"],
        "visual creation": ["interest_artistic_design", "personality_openness_creative"],
        "technology": ["interest_investigative_research"],
        "learning": ["personality_openness_ideas"],
        "community": ["interest_social_growth"],
    }
    value_map = {
        "autonomy": "value_autonomy",
        "freedom": "value_autonomy",
        "stability": "value_stability",
        "income": "value_income",
        "creativity": "value_creativity",
        "care": "value_meaningful_impact",
        "responsibility": "value_meaningful_impact",
        "fairness": "value_meaningful_impact",
        "community": "value_collaboration",
        "collaboration": "value_collaboration",
        "learning": "value_continuous_learning",
    }
    skill_map = {
        "communication": "skill_communication",
        "analysis": "skill_critical_thinking",
        "design": "skill_ux_ui",
        "teaching": "skill_teaching",
        "facilitation": "skill_communication",
        "research": "skill_research",
        "building": "skill_software_development",
        "leadership": "skill_leadership",
        "software development": "skill_software_development",
        "visual communication": "skill_visual_communication",
        "systems thinking": "skill_systems_thinking",
        "empathy": "skill_empathy",
    }
    direct_interest_notes: dict[str, str] = {}

    scored: dict[str, list[float]] = {}
    for value in _list(payload.get("interests")):
        for item_id in interest_map.get(value.lower(), []):
            scored.setdefault(item_id, []).append(4)
    for value in _list(payload.get("preferred_orientation")):
        for item_id in orientation_map.get(value.lower(), []):
            scored.setdefault(item_id, []).append(4)
    for item_id, values in scored.items():
        responses[item_id] = min(5, max(1, round(_average(values))))
        notes[item_id] = "Previously provided during Natural Discovery as an interest or work-style preference."

    for dimension, item_id in _DIRECT_INTEREST_FIELDS.items():
        response = _career_interest_response(payload, dimension)
        if response is None:
            continue
        responses[item_id] = response
        direct_interest_notes[item_id] = (
            "Previously provided in RIASEC-inspired Career Interests during Natural Discovery; confirm or edit before scoring."
        )
    notes.update(direct_interest_notes)

    for value in _list(payload.get("values")):
        item_id = value_map.get(value.lower())
        if item_id:
            responses[item_id] = 5
            notes[item_id] = "Previously selected as a value during Natural Discovery."

    for value in _list(payload.get("skills")):
        item_id = skill_map.get(value.lower()) or skill_map.get(_slug(value).replace("_", " "))
        if item_id:
            responses[item_id] = {"level": "beginner", "evidence_status": "self_reported", "note": "Previously selected during Natural Discovery; confirm actual current level."}
            notes[item_id] = "Previously provided as a skill signal; confirm or edit in Capability & Evidence Assessment."

    ai_experience = str(payload.get("ai_experience") or "").lower()
    ai_level = {"new to ai": 2, "beginner": 3, "intermediate": 4, "advanced": 5}.get(ai_experience)
    if ai_level:
        for item_id in ["ai_readiness_workflows", "ai_readiness_tools"]:
            responses[item_id] = ai_level
            notes[item_id] = "Previously provided as AI experience during Natural Discovery; confirm current capability."
    if payload.get("ai_confidence"):
        responses["ai_readiness_prompts"] = max(1, min(5, round(float(payload.get("ai_confidence", 5)) / 2)))
        notes["ai_readiness_prompts"] = "Previously provided as AI confidence during Natural Discovery; confirm current capability."

    learning_styles = [item.lower() for item in _list(payload.get("preferred_learning_style"))]
    if any("project" in item or "hands" in item for item in learning_styles):
        responses["goals_learning_format"] = "project-based"
        notes["goals_learning_format"] = "Previously provided as a preferred learning style."
    elif any("conversation" in item for item in learning_styles):
        responses["goals_learning_format"] = "mentor"
        notes["goals_learning_format"] = "Previously provided as a preferred learning style."

    return {
        "version": "assessment-prefill-from-natural-discovery-v1",
        "responses": responses,
        "notes": notes,
        "limitations": [
            "Prefill suggestions reduce repeated questions but require user confirmation.",
            "Skill prefill is self-reported and does not create demonstrated evidence.",
        ],
    }


async def _openai_json(instruction: str, payload: dict, fallback: dict) -> dict:
    settings = get_settings()
    api_key = resolve_active_openai_api_key(settings)
    if not api_key:
        return fallback
    try:
        client = AsyncOpenAI(api_key=api_key, timeout=12.0, max_retries=0)
        response = await client.chat.completions.create(model="gpt-4o-mini", response_format={"type": "json_object"}, messages=[{"role": "system", "content": instruction}, {"role": "user", "content": json.dumps(payload)}], temperature=0.3, store=False)
        parsed = json.loads(response.choices[0].message.content or "{}")
        return {**fallback, **parsed}
    except Exception:
        return fallback


def generate_profile_fallback(diagnostic_id: str, payload: dict) -> dict:
    """Transparent mapping: systems/visual/technology -> Architect; people/community -> Integrator; ideas/learning -> Explorer."""
    interests = _list(payload.get("interests")) or ["Creative exploration"]
    orientations = _list(payload.get("preferred_orientation"))
    values = _list(payload.get("values")) or ["Responsibility", "Growth"]
    skills = _list(payload.get("skills")) or ["Adaptive learning"]
    fears = _list(payload.get("fears")) or ["Uncertainty about AI"]
    signals = [*interests, *orientations, *values]
    signal_text = " ".join(signals).lower()
    if any(word in signal_text for word in ("systems", "visual", "technology")):
        primary, secondary = "Visionary Architect", "Purposeful Explorer"
    elif any(word in signal_text for word in ("people", "community", "care", "empathy")):
        primary, secondary = "Human-Centred Integrator", "Reflective Co-Creator"
    else:
        primary, secondary = "Curious Explorer", "Reflective Co-Creator"
    strength_names = list(dict.fromkeys(["Curiosity", "Human-centred judgment", *skills]))[:5]
    primary_signals = signals[:4]
    quick_scores = calculate_quick_diagnostic_scores(payload)
    profile_completeness = quick_scores["profile_completeness"]
    return {
        "diagnostic_id": diagnostic_id,
        "profile_model": "Human Potential Map · exploratory interpretation",
        "source": "SELF-REPORT",
        "quick_diagnostic": quick_scores,
        "human_potential_map": {
            "status": "generated",
            "interpretation": "Generated summary based on current responses. This is not a validated personality classification.",
            "source": "SELF-REPORT · DIAGNOSTIC",
            "profile_completeness": profile_completeness,
            "evidence_layers": [
                {"label": "SELF-REPORT", "status": "present", "description": "What you currently say about your preferences, values, concerns, and confidence."},
                {"label": "DIAGNOSTIC", "status": "present", "description": "Transparent deterministic summaries of the quick diagnostic responses."},
                {"label": "EVIDENCE-BACKED", "status": "missing", "description": "No capability is promoted here without separate evidence."},
                {"label": "EXPERIMENT-BASED", "status": "missing", "description": "Career experiments can add evidence later."},
            ],
            "areas_of_uncertainty": quick_scores["areas_of_uncertainty"],
        },
        "natural_discovery_snapshot": natural_discovery_snapshot(payload),
        "assessment_prefill": assessment_prefill(payload),
        "human_potential_sections": {
            "career_interests": "RIASEC-inspired Career Interests summarize current vocational activity preferences.",
            "natural_tendencies": "Interests, preferred activities, values, orientation, career interests, and work-style preferences.",
            "current_capabilities": "Self-reported skills and AI exposure are stored for later confirmation.",
            "evidence_overview": "No capability is treated as demonstrated until evidence is added or confirmed.",
            "development_opportunities": "Career experiments can test promising directions and create evidence.",
        },
        "primary_archetype": {"name": primary, "summary": "A narrative summary of how current answers may connect curiosity with meaningful action.", "confidence": 0.78, "confidence_label": profile_completeness, "signals": primary_signals},
        "secondary_archetype": {"name": secondary, "summary": "A possible secondary narrative about reflective exploration and collaboration.", "confidence": 0.66, "confidence_label": profile_completeness, "signals": signals[2:6] or primary_signals},
        "strengths": [{"name": name, "score": max(55, 84 - index * 6), "band": "Emerging signal", "source": "SELF-REPORT", "evidence_status": "MISSING", "explanation": f"This possible strength is reflected in your answers about {name.lower()} and contribution.", "evidence": (skills + interests)[index:index + 2] or primary_signals[:2]} for index, name in enumerate(strength_names)],
        "values": [{"name": name, "score": max(55, 82 - index * 5), "source": "SELF-REPORT", "evidence_status": "SELF-REPORT", "evidence": [f"Selected as a core value: {name}"]} for index, name in enumerate(values[:5])],
        "fears": fears,
        "creative_tendencies": [f"Exploring {item}" for item in interests[:3]],
        "ai_collaboration_style": {"name": "Co-Creator", "summary": "This exploratory profile indicates that AI may serve you best as an option generator while judgment remains human-led.", "strengths": ["Ideation", "Pattern exploration", "Draft refinement"], "cautions": ["Avoid over-trusting confident outputs"], "recommended_uses": ["Ideation", "Prototyping", "Scenario exploration"], "human_led_decisions": ["Final decisions", "Personal values", "Ethical responsibility"]},
        "contribution_domains": [{"name": name, "score": max(55, 80 - index * 6), "explanation": f"Your interest in {name} may support meaningful contribution."} for index, name in enumerate(interests[:3] + ["Responsible human-AI collaboration"])],
        "recommended_learning_paths": [{"name": "AI literacy foundations", "level": "Beginner", "duration": "3 weeks", "reason": "Build a safe, verifiable foundation."}, {"name": "Prompting with verification", "level": "Intermediate", "duration": "4 weeks", "reason": "Combine effective prompting with human review."}, {"name": "Ethical co-creation", "level": "All levels", "duration": "2 weeks", "reason": "Keep agency, privacy, and responsibility visible."}],
        "uncertainties": quick_scores["areas_of_uncertainty"],
        "risk_notes": ["This is an exploratory, user-confirmable interpretation, not a psychological or clinical assessment."],
        "ethical_note": "You can confirm or adjust this interpretation. Your values and final decisions remain human-led.",
        "created_at": utc_now_naive().isoformat(),
    }


async def generate_profile(diagnostic_id: str, payload: dict) -> dict:
    fallback = generate_profile_fallback(diagnostic_id, payload)
    # The quick diagnostic is a deterministic product boundary. An AI model may
    # later explain these stored results, but it must not rewrite scores, source
    # status, contradictions, or evidence state during profile generation.
    return {**fallback, "interpretation_engine": "deterministic_rules", "ai_explanation": "Available as a separate, non-scoring explanation step."}


def generate_roadmap_fallback() -> dict:
    return {"seven_days": [{"title": "Choose one useful experiment", "description": "Use AI on a low-risk task and keep human review."}, {"title": "Reflect", "description": "Record what AI improved and where your judgment mattered."}], "thirty_days": [{"title": "Build a repeatable workflow", "description": "Create and test a verified human-AI process."}], "six_months": [{"title": "Lead a contribution project", "description": "Apply your strengths to a meaningful community need."}], "recommended_skills": ["AI literacy", "Verification", "Creative facilitation"], "ai_workflows": ["Explore options, verify evidence, decide with human judgment"], "project_idea": "Create a guide showing responsible AI collaboration in your field.", "social_contribution_idea": "Host a practical AI literacy session.", "ethical_cautions": ["Protect private data", "Verify high-impact outputs"], "contribution_direction": "Turn curiosity into verified, human-centred contribution."}


async def generate_roadmap(profile: dict) -> dict:
    fallback = generate_roadmap_fallback()
    return await _openai_json("Return a practical, ethical human-AI roadmap as JSON using exactly required_shape.", {"profile": profile, "required_shape": fallback}, fallback)


def transform_fear_fallback(fear: str) -> dict:
    return {"fear_summary": fear, "validation": "Uncertainty about rapid technological change is understandable.", "what_is_real": "AI can change tasks and its outputs can be wrong.", "what_is_uncertain": "The exact personal impact cannot be predicted reliably.", "what_the_user_can_control": ["What you learn", "What data you share", "Where you keep human judgment"], "what_user_can_control": ["What you learn", "What data you share"], "creative_reframe": "Treat AI as a tool to test possibilities while retaining responsibility.", "ai_collaboration_opportunities": ["Research assistant", "Idea generator"], "collaboration_opportunity": "Generate options, then evaluate them against your values.", "fifteen_minute_action": "Ask for three low-risk options and verify one.", "seven_day_action": "Run one small experiment and document your judgment.", "ethical_cautions": ["Do not share sensitive data", "Verify claims"], "ethical_note": "Maintain human agency, privacy, and verification."}


async def transform_fear(fear: str, profile: dict) -> dict:
    fallback = transform_fear_fallback(fear)
    return await _openai_json("Return a non-clinical fear-to-creativity reflection as JSON using exactly required_shape.", {"fear": fear, "profile": profile, "required_shape": fallback}, fallback)

