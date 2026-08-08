from datetime import datetime
import json

from openai import AsyncOpenAI

from app.config import get_settings


def _list(value) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)] if value and str(value).strip() else []


async def _openai_json(instruction: str, payload: dict, fallback: dict) -> dict:
    settings = get_settings()
    if not settings.openai_api_key:
        return fallback
    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=12.0, max_retries=0)
        response = await client.chat.completions.create(model="gpt-4o-mini", response_format={"type": "json_object"}, messages=[{"role": "system", "content": instruction}, {"role": "user", "content": json.dumps(payload)}], temperature=0.3)
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
    return {
        "diagnostic_id": diagnostic_id,
        "primary_archetype": {"name": primary, "summary": "Your answers suggest a tendency to connect curiosity with meaningful action.", "confidence": 0.78, "signals": primary_signals},
        "secondary_archetype": {"name": secondary, "summary": "A possible secondary tendency is reflective exploration and collaboration.", "confidence": 0.66, "signals": signals[2:6] or primary_signals},
        "strengths": [{"name": name, "score": max(55, 84 - index * 6), "explanation": f"This possible strength is reflected in your answers about {name.lower()} and contribution.", "evidence": (skills + interests)[index:index + 2] or primary_signals[:2]} for index, name in enumerate(strength_names)],
        "values": [{"name": name, "score": max(55, 82 - index * 5), "evidence": [f"Selected as a core value: {name}"]} for index, name in enumerate(values[:5])],
        "fears": fears,
        "creative_tendencies": [f"Exploring {item}" for item in interests[:3]],
        "ai_collaboration_style": {"name": "Co-Creator", "summary": "This exploratory profile indicates that AI may serve you best as an option generator while judgment remains human-led.", "strengths": ["Ideation", "Pattern exploration", "Draft refinement"], "cautions": ["Avoid over-trusting confident outputs"], "recommended_uses": ["Ideation", "Prototyping", "Scenario exploration"], "human_led_decisions": ["Final decisions", "Personal values", "Ethical responsibility"]},
        "contribution_domains": [{"name": name, "score": max(55, 80 - index * 6), "explanation": f"Your interest in {name} may support meaningful contribution."} for index, name in enumerate(interests[:3] + ["Responsible human-AI collaboration"])],
        "recommended_learning_paths": [{"name": "AI literacy foundations", "level": "Beginner", "duration": "3 weeks", "reason": "Build a safe, verifiable foundation."}, {"name": "Prompting with verification", "level": "Intermediate", "duration": "4 weeks", "reason": "Combine effective prompting with human review."}, {"name": "Ethical co-creation", "level": "All levels", "duration": "2 weeks", "reason": "Keep agency, privacy, and responsibility visible."}],
        "uncertainties": ["Confidence indicators reflect answer coverage, not scientific certainty."],
        "risk_notes": ["This is an exploratory, user-confirmable interpretation, not a psychological or clinical assessment."],
        "ethical_note": "You can confirm or adjust this interpretation. Your values and final decisions remain human-led.",
        "created_at": datetime.utcnow().isoformat(),
    }


async def generate_profile(diagnostic_id: str, payload: dict) -> dict:
    fallback = generate_profile_fallback(diagnostic_id, payload)
    instruction = "Return JSON matching required_shape exactly. This is an exploratory, explainable human-potential profile. Never diagnose, claim scientific certainty, determine identity, or present destiny. Use 'answers suggest', 'possible tendency', and user-confirmable language."
    return await _openai_json(instruction, {"diagnostic": payload, "required_shape": fallback}, fallback)


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
