from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from app.core.time import utc_now_naive
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.assessment import (
    AIReadinessResult,
    AssessmentDefinition,
    AssessmentInterpretation,
    AssessmentItem,
    AssessmentModule,
    AssessmentOption,
    AssessmentResponse,
    AssessmentScore,
    AssessmentSession,
    CareerComparison,
    CareerDecision,
    CareerInterestResult,
    CareerMatch,
    CareerMatchFactor,
    CareerRoleTemplate,
    ChangeReadinessResult,
    PersonalityResult,
    SkillEvidence,
    SkillsInventory,
    WorkValueResult,
)
from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.models.roadmap_adaptation import RoadmapAction
from app.services.profile_generation import RIASEC_DIMENSIONS, generate_roadmap_fallback
from app.services.roadmap_adaptation import event as roadmap_event
from app.services.roadmap_adaptation import normalize_legacy, snapshot

ASSESSMENT_ID = "human-potential-career-assessment"
ASSESSMENT_VERSION = "career-assessment-v1"
SCORING_VERSION = "career-scoring-v2-four-layer"
ROLE_CATALOGUE_VERSION = "role-catalogue-v1"
HYPOTHESIS_RULESET = "human-discovery-career-hypothesis"
HYPOTHESIS_RULESET_VERSION = "v2"

DISCLAIMER = (
    "This assessment supports self-reflection and career exploration. "
    "It is based on self-reported information and prototype scoring methods. "
    "It is not a psychological diagnosis, employment decision, or guarantee of professional success. "
    "Final decisions remain with the user."
)

METHODOLOGY_NOTE = (
    "Personality Tendencies uses 30 original, non-clinical Big Five-informed self-reflection prompts "
    "created for this research prototype. They are not copied from proprietary tests and are "
    "not intended for diagnosis, hiring, clinical use, or deterministic personality claims."
)

LIKERT_OPTIONS = [
    {"value": 1, "label": "Strongly disagree"},
    {"value": 2, "label": "Disagree"},
    {"value": 3, "label": "Neither agree nor disagree"},
    {"value": 4, "label": "Agree"},
    {"value": 5, "label": "Strongly agree"},
]

SKILL_LEVELS = {
    "no_experience": 0,
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3,
    "expert": 4,
}

SKILL_LEVEL_LABELS = {
    0: "No experience",
    1: "Beginner",
    2: "Intermediate",
    3: "Advanced",
    4: "Expert",
}

EVIDENCE_STRENGTH = {
    "self_reported": 1,
    "supported_by_experience": 2,
    "supported_by_project": 3,
    "supported_by_certification": 4,
    "practically_verified": 5,
}

CAREER_MATCH_WEIGHTS = {
    "skills_match": 0.30,
    "interest_match": 0.25,
    "work_values_match": 0.15,
    "work_style_compatibility": 0.15,
    "ai_augmentation_opportunity": 0.10,
    "feasibility": 0.05,
}

CAREER_HYPOTHESIS_DIMENSION_WEIGHTS = {
    "natural_fit": 0.32,
    "capability_fit": 0.24,
    "evidence_strength": 0.16,
    "transition_feasibility": 0.18,
    "ai_augmentation_opportunity": 0.10,
}

COMPARISON_CRITERIA = {
    "natural_fit": 1.0,
    "capability_fit": 1.0,
    "evidence_strength": 1.0,
    "transition_feasibility": 1.0,
    "skills_match": 1.0,
    "interest_alignment": 1.0,
    "work_values_alignment": 1.0,
    "work_style_fit": 1.0,
    "ai_opportunity": 1.0,
    "training_required": 1.0,
    "transition_difficulty": 1.0,
    "time_horizon": 1.0,
    "resource_requirements": 1.0,
    "employment_entrepreneurship": 1.0,
    "identified_risks": 1.0,
    "user_priority": 1.0,
}


def reverse_score(value: float, scale_max: int = 5) -> float:
    return scale_max + 1 - value


def normalize_likert_average(value: float) -> float:
    return round(max(0, min(100, ((value - 1) / 4) * 100)), 2)


def normalize_skill_level(value: float) -> float:
    return round(max(0, min(100, (value / 4) * 100)), 2)


def alignment_label(score: float) -> str:
    if score >= 80:
        return "Strong alignment"
    if score >= 60:
        return "Moderate alignment"
    if score >= 40:
        return "Exploratory alignment"
    return "Substantial development required"


def fit_label(score: float) -> str:
    if score >= 78:
        return "Strong"
    if score >= 55:
        return "Moderate"
    if score >= 35:
        return "Developing"
    return "Limited"


def tendency_label(raw_score: float) -> str:
    if raw_score >= 4.05:
        return "Stronger current tendency"
    if raw_score >= 3.2:
        return "Moderate current preference"
    if raw_score >= 2.35:
        return "Mixed or context-dependent response pattern"
    return "Lower current preference"


def ai_level(normalized_score: float) -> str:
    if normalized_score >= 78:
        return "Advanced"
    if normalized_score >= 58:
        return "Operational"
    if normalized_score >= 36:
        return "Developing"
    return "Emerging"


def change_readiness_label(normalized_score: float, constraints: list[str]) -> str:
    if constraints and normalized_score < 45:
        return "Significant constraints currently present"
    if normalized_score >= 74:
        return "Ready for an adjacent transition"
    if normalized_score >= 58:
        return "Ready for incremental upskilling"
    if normalized_score >= 42:
        return "Exploring options"
    return "Longer preparation phase recommended"


def slug(value: str) -> str:
    return value.lower().replace("&", "and").replace("/", " ").replace("-", " ").replace(" ", "_")


def title_case_slug(value: str) -> str:
    return value.replace("_", " ").title().replace("Ai", "AI").replace("Ux", "UX").replace("Api", "API")


def _item(
    item_id: str,
    module_id: str,
    prompt: str,
    item_type: str,
    dimension: str | None = None,
    *,
    reverse: bool = False,
    required: bool = False,
    quick: bool = False,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": item_id,
        "module_id": module_id,
        "prompt": prompt,
        "item_type": item_type,
        "dimension": dimension,
        "reverse_scored": reverse,
        "required": required,
        "quick_mode": quick,
        "metadata": metadata or {},
    }


def assessment_definition() -> dict[str, Any]:
    personality = [
        _item("personality_openness_ideas", "personality_work_style", "I enjoy exploring unfamiliar ideas.", "likert", "openness", required=True, quick=True),
        _item("personality_openness_creative", "personality_work_style", "I am interested in creative and experimental work.", "likert", "openness", quick=True),
        _item("personality_openness_familiar_reverse", "personality_work_style", "I prefer familiar methods to new approaches.", "likert", "openness", reverse=True),
        _item("personality_openness_perspectives", "personality_work_style", "I enjoy considering perspectives that differ from my own.", "likert", "openness"),
        _item("personality_openness_routine_reverse", "personality_work_style", "I would rather repeat a familiar routine than explore a new approach.", "likert", "openness", reverse=True),
        _item("personality_openness_questions", "personality_work_style", "I often follow a question simply because it is interesting.", "likert", "openness"),
        _item("personality_conscientious_plan", "personality_work_style", "I organise my work before starting.", "likert", "conscientiousness", required=True, quick=True),
        _item("personality_conscientious_complete", "personality_work_style", "I usually complete tasks I have committed to.", "likert", "conscientiousness", quick=True),
        _item("personality_conscientious_unfinished_reverse", "personality_work_style", "I often leave tasks unfinished.", "likert", "conscientiousness", reverse=True),
        _item("personality_conscientious_detail", "personality_work_style", "I notice important details before considering a task complete.", "likert", "conscientiousness"),
        _item("personality_conscientious_spontaneous_reverse", "personality_work_style", "I frequently change plans before giving them enough time to work.", "likert", "conscientiousness", reverse=True),
        _item("personality_conscientious_followthrough", "personality_work_style", "People can generally rely on me to follow through on commitments.", "likert", "conscientiousness"),
        _item("personality_extraversion_interaction", "personality_work_style", "I gain energy from frequent interaction with other people.", "likert", "extraversion", quick=True),
        _item("personality_extraversion_present", "personality_work_style", "I feel comfortable presenting ideas to groups.", "likert", "extraversion"),
        _item("personality_extraversion_independent_reverse", "personality_work_style", "I prefer long periods of independent work.", "likert", "extraversion", reverse=True),
        _item("personality_extraversion_start", "personality_work_style", "I am comfortable starting a conversation with someone new.", "likert", "extraversion"),
        _item("personality_extraversion_quiet_reverse", "personality_work_style", "In group settings, I usually wait for others to draw me into the discussion.", "likert", "extraversion", reverse=True),
        _item("personality_extraversion_activity", "personality_work_style", "Active, collaborative environments usually feel energising to me.", "likert", "extraversion"),
        _item("personality_agreeableness_effects", "personality_work_style", "I consider how decisions affect other people.", "likert", "agreeableness", required=True, quick=True),
        _item("personality_agreeableness_collaboration", "personality_work_style", "I prefer collaboration over competition.", "likert", "agreeableness", quick=True),
        _item("personality_agreeableness_compromise_reverse", "personality_work_style", "I find it difficult to compromise.", "likert", "agreeableness", reverse=True),
        _item("personality_agreeableness_perspective", "personality_work_style", "I try to understand another person's perspective before responding.", "likert", "agreeableness"),
        _item("personality_agreeableness_challenge", "personality_work_style", "I am comfortable challenging someone respectfully when I think they are wrong.", "likert", "agreeableness"),
        _item("personality_agreeableness_support", "personality_work_style", "I often notice when someone may need support in a group.", "likert", "agreeableness"),
        _item("personality_stability_change", "personality_work_style", "I remain composed when plans change unexpectedly.", "likert", "emotional_stability", quick=True),
        _item("personality_stability_pressure", "personality_work_style", "I can continue working effectively under moderate pressure.", "likert", "emotional_stability"),
        _item("personality_stability_uncertainty_reverse", "personality_work_style", "Uncertainty often disrupts my concentration.", "likert", "emotional_stability", reverse=True),
        _item("personality_stability_recover", "personality_work_style", "After a setback, I can usually regain perspective and continue.", "likert", "emotional_stability"),
        _item("personality_stability_worry_reverse", "personality_work_style", "I can spend a long time worrying about things I cannot control.", "likert", "emotional_stability", reverse=True),
        _item("personality_stability_feedback", "personality_work_style", "I can receive useful criticism without it overwhelming me.", "likert", "emotional_stability"),
    ]
    interests = [
        _item("interest_realistic_practical", "career_interests", "I enjoy practical construction, equipment, or hands-on technical work.", "likert", "realistic", quick=True),
        _item("interest_realistic_spatial", "career_interests", "Physical, spatial, or operational problem-solving interests me.", "likert", "realistic"),
        _item("interest_investigative_research", "career_interests", "I enjoy research, analysis, experimentation, or complex problem-solving.", "likert", "investigative", required=True, quick=True),
        _item("interest_investigative_evidence", "career_interests", "I like comparing evidence before forming conclusions.", "likert", "investigative"),
        _item("interest_artistic_design", "career_interests", "I enjoy design, writing, visual creation, or conceptual exploration.", "likert", "artistic", required=True, quick=True),
        _item("interest_artistic_original", "career_interests", "I prefer work where I can create original forms, stories, or concepts.", "likert", "artistic"),
        _item("interest_social_teaching", "career_interests", "I enjoy teaching, mentoring, supporting, or collaborating with people.", "likert", "social", required=True, quick=True),
        _item("interest_social_growth", "career_interests", "Helping others understand or grow gives me energy.", "likert", "social"),
        _item("interest_enterprising_lead", "career_interests", "I enjoy leadership, negotiation, entrepreneurship, or influencing decisions.", "likert", "enterprising", quick=True),
        _item("interest_enterprising_initiate", "career_interests", "I like initiating projects and persuading others to support them.", "likert", "enterprising"),
        _item("interest_conventional_structure", "career_interests", "I enjoy organisation, structured processes, data administration, or detailed operations.", "likert", "conventional", quick=True),
        _item("interest_conventional_accuracy", "career_interests", "I appreciate predictable workflows, accuracy, and clear procedures.", "likert", "conventional"),
    ]
    values = [
        _item(f"value_{slug(name)}", "work_values", f"How important is {name.lower()} in your work?", "value_rating", slug(name), quick=True)
        for name in [
            "Autonomy",
            "Stability",
            "Income",
            "Creativity",
            "Meaningful Impact",
            "Flexibility",
            "Leadership",
            "Collaboration",
            "Recognition",
            "Continuous Learning",
            "Work-Life Balance",
            "Predictable Structure",
        ]
    ]
    skill_specs = {
        "technical": ["software development", "data analysis", "AI tools", "APIs", "databases", "cybersecurity", "automation"],
        "creative": ["graphic design", "UX/UI", "architecture", "writing", "visual communication", "video", "ideation"],
        "analytical": ["research", "critical thinking", "systems thinking", "problem-solving", "evaluation"],
        "human_collaborative": ["communication", "teaching", "empathy", "negotiation", "teamwork", "client relations"],
        "management": ["planning", "leadership", "budgeting", "coordination", "quality assurance"],
    }
    skills = [
        _item(
            f"skill_{slug(name)}",
            "skills_inventory",
            f"Current level for {name}",
            "skill_level",
            slug(name),
            quick=name
            in {
                "software development",
                "AI tools",
                "UX/UI",
                "visual communication",
                "research",
                "systems thinking",
                "communication",
                "coordination",
            },
            metadata={"category": category, "label": name},
        )
        for category, names in skill_specs.items()
        for name in names
    ]
    ai_items = [
        _item("ai_literacy_llm", "ai_literacy_readiness", "I understand at a high level what a large language model does.", "likert", "ai_literacy", quick=True),
        _item("ai_literacy_hallucinations", "ai_literacy_readiness", "I know that AI can produce confident but incorrect answers.", "likert", "ai_literacy", required=True, quick=True),
        _item("ai_literacy_sources", "ai_literacy_readiness", "I can evaluate sources before relying on AI-generated claims.", "likert", "ai_literacy", quick=True),
        _item("ai_literacy_privacy", "ai_literacy_readiness", "I think carefully before sharing private or sensitive data with AI tools.", "likert", "ai_literacy"),
        _item("ai_literacy_limits", "ai_literacy_readiness", "I can recognise situations where AI should not be used.", "likert", "ai_literacy"),
        _item("ai_readiness_prompts", "ai_literacy_readiness", "I can formulate prompts that give useful context and constraints.", "likert", "ai_readiness", quick=True),
        _item("ai_readiness_workflows", "ai_literacy_readiness", "I have used AI tools inside a practical workflow.", "likert", "ai_readiness", quick=True),
        _item("ai_readiness_tools", "ai_literacy_readiness", "I can choose an appropriate AI tool for a task.", "likert", "ai_readiness"),
        _item("ai_readiness_api", "ai_literacy_readiness", "I understand the basic idea of using APIs to connect software systems.", "likert", "ai_readiness"),
        _item("ai_readiness_learning", "ai_literacy_readiness", "I am willing to keep learning as AI tools change.", "likert", "ai_readiness", required=True, quick=True),
    ]
    change = [
        _item("change_motivation", "change_readiness", "I have a clear reason for exploring professional change.", "likert", "motivation", required=True, quick=True),
        _item("change_time", "change_readiness", "I can reserve regular weekly time for learning or experimentation.", "likert", "time", required=True, quick=True),
        _item("change_study", "change_readiness", "I am willing to study or practise before expecting a transition.", "likert", "study", quick=True),
        _item("change_uncertainty", "change_readiness", "I can tolerate some temporary uncertainty while testing a direction.", "likert", "uncertainty", quick=True),
        _item("change_adjacent_role", "change_readiness", "I would consider an adjacent or more junior role if it were a realistic bridge.", "likert", "adjacent_role"),
        _item("change_budget", "change_readiness", "I currently have budget or free resources available for learning.", "likert", "budget"),
        _item("change_remote_preference", "change_readiness", "Remote or hybrid work would materially affect my decision.", "likert", "remote_preference"),
    ]
    background = [
        _item("background_current_profession", "professional_background", "Current profession or role", "text", "current_profession", required=True, quick=True),
        _item("background_experience", "professional_background", "Years of relevant work experience", "single_select", "years_experience", quick=True, metadata={"options": ["0-1", "2-4", "5-9", "10+"]}),
        _item("background_projects", "professional_background", "Relevant project, portfolio, certification, or education evidence", "long_text", "evidence", metadata={"optional": True}),
    ]
    goals = [
        _item("goals_desired_area", "goals_constraints", "Desired profession or areas of interest", "text", "desired_area", quick=True),
        _item("goals_market", "goals_constraints", "Target country or labour market", "text", "target_market"),
        _item("goals_work_mode", "goals_constraints", "Preferred work mode", "single_select", "work_mode", quick=True, metadata={"options": ["remote", "hybrid", "on_site", "flexible"]}),
        _item("goals_timeline", "goals_constraints", "Preferred transition timeline", "single_select", "timeline", quick=True, metadata={"options": ["1-3 months", "3-6 months", "6-12 months", "12+ months", "exploring"]}),
        _item("goals_salary", "goals_constraints", "Salary expectations", "text", "salary", metadata={"optional": True}),
        _item("goals_weekly_time", "goals_constraints", "Available weekly learning time", "single_select", "weekly_time", quick=True, metadata={"options": ["0-2 hours", "3-5 hours", "6-10 hours", "10+ hours"]}),
        _item("goals_budget", "goals_constraints", "Learning budget", "single_select", "learning_budget", metadata={"options": ["none", "low", "moderate", "significant"]}),
        _item("goals_learning_format", "goals_constraints", "Preferred education format", "single_select", "education_format", metadata={"options": ["self-paced", "course", "mentor", "bootcamp", "project-based"]}),
        _item("goals_languages", "goals_constraints", "Languages", "text", "languages", metadata={"optional": True}),
        _item("goals_accessibility", "goals_constraints", "Accessibility needs", "long_text", "accessibility_needs", metadata={"optional": True}),
        _item("goals_relocate", "goals_constraints", "Willingness to relocate", "single_select", "relocate", metadata={"options": ["yes", "no", "maybe"]}),
        _item("goals_entrepreneurship", "goals_constraints", "Interest in entrepreneurship or independent work", "single_select", "entrepreneurship", quick=True, metadata={"options": ["low", "medium", "high", "not sure"]}),
    ]
    modules = [
        {"id": "professional_background", "title": "Professional Background", "description": "Current context and optional evidence.", "order": 1},
        {"id": "skills_inventory", "title": "Skills Inventory", "description": "Self-reported skills plus evidence status.", "order": 2},
        {"id": "personality_work_style", "title": "Personality Tendencies & Work Style", "description": "Big Five-informed, non-clinical current tendencies and preferences.", "order": 3},
        {"id": "career_interests", "title": "Career Interests", "description": "Preferred activities and environments.", "order": 4},
        {"id": "work_values", "title": "Work Values", "description": "Professional priorities and possible value conflicts.", "order": 5},
        {"id": "ai_literacy_readiness", "title": "AI Literacy & Readiness", "description": "Conceptual understanding and practical readiness.", "order": 6},
        {"id": "change_readiness", "title": "Change Readiness", "description": "Professional transition feasibility without clinical claims.", "order": 7},
        {"id": "goals_constraints", "title": "Goals & Constraints", "description": "Optional goals, market, format, time, and constraints.", "order": 8},
    ]
    items = background + skills + personality + interests + values + ai_items + change + goals
    return {
        "id": ASSESSMENT_ID,
        "title": "Human Potential & Career Assessment",
        "version": ASSESSMENT_VERSION,
        "scoring_version": SCORING_VERSION,
        "disclaimer": DISCLAIMER,
        "methodology_note": METHODOLOGY_NOTE,
        "modes": [
            {
                "id": "quick",
                "title": "Quick Assessment",
                "estimated_minutes": "8-10",
                "description": "A focused version for preliminary self-understanding and broad career families.",
            },
            {
                "id": "complete",
                "title": "Complete Assessment",
                "estimated_minutes": "20-30",
                "description": "A detailed profile covering all modules and career compatibility results.",
            },
            {
                "id": "evidence_based",
                "title": "Evidence-Based Assessment",
                "estimated_minutes": "30+",
                "description": "Complete assessment plus structured manual evidence. Automatic CV parsing is not included in this sprint.",
            },
        ],
        "modules": modules,
        "items": items,
        "likert_options": LIKERT_OPTIONS,
        "skill_levels": [{"value": key, "score": score, "label": SKILL_LEVEL_LABELS[score]} for key, score in SKILL_LEVELS.items()],
        "evidence_statuses": [
            {"value": "self_reported", "label": "Self-reported"},
            {"value": "supported_by_experience", "label": "Supported by experience"},
            {"value": "supported_by_project", "label": "Supported by project"},
            {"value": "supported_by_certification", "label": "Supported by certification"},
            {"value": "practically_verified", "label": "Practically verified"},
        ],
    }


def definition_for_mode(mode: str) -> dict[str, Any]:
    definition = assessment_definition()
    if mode == "quick":
        items = [item for item in definition["items"] if item["quick_mode"] or item["required"]]
        module_ids = {item["module_id"] for item in items}
        definition["items"] = items
        definition["modules"] = [module for module in definition["modules"] if module["id"] in module_ids]
    return definition


def sync_assessment_definition(db: Session) -> None:
    definition = assessment_definition()
    row = db.get(AssessmentDefinition, definition["id"])
    if row is None:
        row = AssessmentDefinition(id=definition["id"], title=definition["title"], version=definition["version"])
        db.add(row)
    row.description = "Optional self-reflection and professional exploration assessment."
    row.methodology_note = definition["methodology_note"]
    row.disclaimer = definition["disclaimer"]
    row.source_metadata_json = {"item_origin": "Original neutral prototype items", "license": "Project-owned research prototype content"}
    existing_modules = {item.id: item for item in db.scalars(select(AssessmentModule)).all()}
    for module in definition["modules"]:
        record = existing_modules.get(module["id"]) or AssessmentModule(id=module["id"], assessment_id=definition["id"], title=module["title"])
        record.assessment_id = definition["id"]
        record.title = module["title"]
        record.description = module["description"]
        record.order_index = module["order"]
        db.add(record)
    existing_items = {item.id: item for item in db.scalars(select(AssessmentItem)).all()}
    for index, item in enumerate(definition["items"]):
        record = existing_items.get(item["id"]) or AssessmentItem(id=item["id"], module_id=item["module_id"], prompt=item["prompt"], item_type=item["item_type"])
        record.module_id = item["module_id"]
        record.prompt = item["prompt"]
        record.item_type = item["item_type"]
        record.dimension = item["dimension"]
        record.reverse_scored = item["reverse_scored"]
        record.required = item["required"]
        record.quick_mode = item["quick_mode"]
        record.order_index = index
        record.metadata_json = item["metadata"]
        db.add(record)
    for index, option in enumerate(LIKERT_OPTIONS):
        option_id = f"likert_{option['value']}"
        record = db.get(AssessmentOption, option_id) or AssessmentOption(id=option_id, item_id="likert", value=str(option["value"]), label=option["label"])
        record.score_value = float(option["value"])
        record.order_index = index
        db.add(record)
    sync_role_templates(db)
    db.commit()


def role_templates() -> list[dict[str, Any]]:
    def role(
        role_id: str,
        title: str,
        family: str,
        skills: list[str],
        transferable: list[str],
        interests: dict[str, float],
        values: list[str],
        style: dict[str, float],
        ai_opportunities: list[str],
        entry: list[str],
        gaps: list[str],
        path: list[str],
        *,
        entrepreneurship: bool = False,
    ) -> dict[str, Any]:
        return {
            "id": role_id,
            "title": title,
            "role_family": family,
            "description": (
                f"{title} combines human judgment, practical delivery, and AI-aware workflows. "
                "The template is curated for exploration, not a labour-market guarantee."
            ),
            "required_skills": skills,
            "useful_transferable_skills": transferable,
            "interest_profile": interests,
            "work_style_tendencies": style,
            "compatible_work_values": values,
            "ai_augmentation_opportunities": ai_opportunities,
            "entry_requirements": entry,
            "skill_gap_categories": gaps,
            "typical_transition_path": path,
            "source_metadata": {
                "source_type": "curated_prototype_template",
                "version": ROLE_CATALOGUE_VERSION,
                "entrepreneurship": entrepreneurship,
            },
        }

    return [
        role("human_centred_ai_product_designer", "Human-Centred AI Product Designer", "Design and AI Product", ["ux_ui", "visual_communication", "ai_tools", "research", "ideation"], ["client_relations", "communication", "systems_thinking", "architecture"], {"artistic": 0.34, "investigative": 0.28, "social": 0.2, "enterprising": 0.12}, ["creativity", "autonomy", "meaningful_impact", "continuous_learning"], {"openness": 4, "conscientiousness": 3.4, "agreeableness": 3.5}, ["Prototype interface alternatives", "Generate user-flow variations", "Evaluate risks and explainability"], ["Portfolio with AI product case study", "Basic usability research", "Responsible AI literacy"], ["AI evaluation", "production product process"], ["Audit AI products", "Build a small prototype", "Document decisions"]),
        role("ux_designer_ai_systems", "UX Designer for AI Systems", "UX and Digital Experience", ["ux_ui", "research", "visual_communication", "communication", "critical_thinking"], ["client_relations", "teaching", "empathy", "architecture"], {"artistic": 0.3, "social": 0.24, "investigative": 0.22, "conventional": 0.1}, ["creativity", "collaboration", "meaningful_impact", "work_life_balance"], {"openness": 3.7, "agreeableness": 3.7, "conscientiousness": 3.2}, ["Draft test plans", "Summarise interviews", "Compare design alternatives"], ["UX research evidence", "Interaction design portfolio"], ["systematic UX methods", "AI-specific risk patterns"], ["Interview one UX professional", "Review AI UX job descriptions", "Run a usability test"]),
        role("creative_ai_technologist", "Creative AI Technologist", "Creative Technology", ["ai_tools", "ideation", "visual_communication", "software_development", "automation"], ["graphic_design", "video", "writing", "systems_thinking"], {"artistic": 0.36, "investigative": 0.28, "realistic": 0.14, "enterprising": 0.1}, ["creativity", "autonomy", "continuous_learning", "recognition"], {"openness": 4.2, "conscientiousness": 3.0}, ["Generate prototypes", "Automate creative workflows", "Evaluate originality and rights issues"], ["Creative portfolio", "Tool experimentation evidence"], ["production deployment", "AI rights and evaluation"], ["Build a two-week prototype", "Publish a process note", "Compare tools"]),
        role("ai_integration_consultant", "AI Integration Consultant", "AI Operations and Consulting", ["ai_tools", "automation", "communication", "planning", "systems_thinking"], ["client_relations", "coordination", "quality_assurance", "software_development"], {"enterprising": 0.28, "investigative": 0.24, "conventional": 0.18, "social": 0.16}, ["meaningful_impact", "income", "leadership", "continuous_learning"], {"conscientiousness": 3.8, "extraversion": 3.2, "agreeableness": 3.2}, ["Map workflows", "Create prompt libraries", "Monitor automation risk"], ["Workflow analysis evidence", "Responsible automation knowledge"], ["business process evidence", "change management"], ["Map one workflow", "Estimate time saved", "Test a low-risk automation"]),
        role("learning_experience_designer", "Learning Experience Designer", "Education and Enablement", ["teaching", "writing", "ux_ui", "communication", "research"], ["empathy", "visual_communication", "client_relations", "planning"], {"social": 0.34, "artistic": 0.22, "investigative": 0.18, "conventional": 0.1}, ["meaningful_impact", "collaboration", "continuous_learning", "work_life_balance"], {"agreeableness": 3.8, "conscientiousness": 3.4, "openness": 3.4}, ["Generate learning activities", "Personalise examples", "Create assessment rubrics"], ["Instructional design sample", "Teaching or facilitation evidence"], ["learning assessment design", "content evaluation"], ["Design a mini-lesson", "Run a feedback session", "Iterate content"]),
        role("ai_product_manager", "AI Product Manager", "Product Strategy", ["planning", "leadership", "communication", "ai_tools", "critical_thinking"], ["coordination", "client_relations", "systems_thinking", "quality_assurance"], {"enterprising": 0.32, "investigative": 0.22, "social": 0.18, "conventional": 0.12}, ["leadership", "meaningful_impact", "recognition", "income"], {"conscientiousness": 3.8, "extraversion": 3.3, "agreeableness": 3.2}, ["Prioritise AI features", "Draft experiments", "Track evaluation metrics"], ["Product case study", "Stakeholder communication"], ["product analytics", "AI evaluation"], ["Write a product brief", "Define one metric", "Interview users"]),
        role("rag_application_developer", "RAG Application Developer", "Software and AI Engineering", ["software_development", "apis", "databases", "ai_tools", "evaluation"], ["systems_thinking", "research", "automation"], {"investigative": 0.34, "realistic": 0.2, "conventional": 0.18, "artistic": 0.1}, ["continuous_learning", "income", "autonomy", "predictable_structure"], {"conscientiousness": 3.6, "openness": 3.4}, ["Build retrieval pipelines", "Evaluate grounded answers", "Create source feedback loops"], ["Working app", "API and database evidence"], ["backend deployment", "systematic evaluation"], ["Build a small RAG app", "Add source feedback", "Document eval results"]),
        role("data_analyst", "Data Analyst", "Data and Insight", ["data_analysis", "databases", "critical_thinking", "evaluation", "writing"], ["research", "problem_solving", "quality_assurance"], {"investigative": 0.34, "conventional": 0.24, "realistic": 0.12, "enterprising": 0.1}, ["stability", "predictable_structure", "income", "continuous_learning"], {"conscientiousness": 3.7, "openness": 3.0}, ["Clean data", "Explain charts", "Generate analysis hypotheses"], ["Analysis portfolio", "Spreadsheet or SQL evidence"], ["statistics", "SQL/Python evidence"], ["Analyse one public dataset", "Write findings", "Review analyst postings"]),
        role("frontend_developer", "Frontend Developer", "Software Engineering", ["software_development", "ux_ui", "apis", "problem_solving", "quality_assurance"], ["visual_communication", "systems_thinking", "ideation"], {"realistic": 0.22, "investigative": 0.22, "artistic": 0.2, "conventional": 0.12}, ["income", "autonomy", "continuous_learning", "predictable_structure"], {"conscientiousness": 3.5, "openness": 3.2}, ["Generate UI variants", "Test accessibility", "Explain code"], ["Deployed frontend project", "Version-control evidence"], ["testing", "deployment", "performance"], ["Ship a small app", "Add tests", "Document implementation"]),
        role("digital_experience_designer", "Digital Experience Designer", "Digital Design", ["visual_communication", "ux_ui", "ideation", "graphic_design", "writing"], ["architecture", "client_relations", "communication"], {"artistic": 0.34, "social": 0.18, "investigative": 0.16, "enterprising": 0.12}, ["creativity", "flexibility", "recognition", "meaningful_impact"], {"openness": 4.0, "agreeableness": 3.2}, ["Produce visual systems", "Explore layout alternatives", "Document design rationale"], ["Portfolio", "User-centred design evidence"], ["interactive prototyping", "accessibility"], ["Redesign one workflow", "Test with users", "Publish case study"]),
        role("automation_specialist", "Automation Specialist", "Operations and Automation", ["automation", "apis", "databases", "planning", "problem_solving"], ["coordination", "quality_assurance", "software_development"], {"realistic": 0.24, "investigative": 0.24, "conventional": 0.22, "enterprising": 0.1}, ["stability", "income", "predictable_structure", "continuous_learning"], {"conscientiousness": 3.9, "openness": 3.1}, ["Automate repetitive tasks", "Monitor exceptions", "Document workflows"], ["Automation example", "Process map"], ["integration testing", "security basics"], ["Automate a simple process", "Measure errors", "Add a manual override"]),
        role("technical_project_manager", "Technical Project Manager", "Technical Coordination", ["planning", "coordination", "communication", "quality_assurance", "leadership"], ["client_relations", "budgeting", "systems_thinking"], {"enterprising": 0.26, "conventional": 0.24, "social": 0.2, "investigative": 0.12}, ["leadership", "stability", "collaboration", "income"], {"conscientiousness": 3.9, "extraversion": 3.2, "agreeableness": 3.3}, ["Summarise risks", "Create project plans", "Track decisions"], ["Project coordination evidence", "Stakeholder communication"], ["technical delivery vocabulary", "risk management"], ["Run a project retrospective", "Build a delivery dashboard", "Interview a TPM"]),
        role("independent_ai_design_service", "Independent AI Design Service", "Entrepreneurship and Independent Work", ["communication", "client_relations", "ai_tools", "visual_communication", "planning"], ["ux_ui", "teaching", "writing", "ideation"], {"enterprising": 0.28, "artistic": 0.24, "social": 0.18, "investigative": 0.12}, ["autonomy", "flexibility", "creativity", "income"], {"openness": 3.8, "conscientiousness": 3.3, "extraversion": 3.0}, ["Offer AI workflow audits", "Create client education materials", "Prototype service packages"], ["Service concept", "Client discovery conversations"], ["pricing", "client acquisition", "scope boundaries"], ["Interview three potential users", "Create a one-page offer", "Run a pilot"], entrepreneurship=True),
    ]


def sync_role_templates(db: Session) -> None:
    for item in role_templates():
        record = db.get(CareerRoleTemplate, item["id"]) or CareerRoleTemplate(id=item["id"], title=item["title"], role_family=item["role_family"])
        record.title = item["title"]
        record.role_family = item["role_family"]
        record.description = item["description"]
        record.required_skills_json = item["required_skills"]
        record.useful_transferable_skills_json = item["useful_transferable_skills"]
        record.interest_profile_json = item["interest_profile"]
        record.work_style_tendencies_json = item["work_style_tendencies"]
        record.compatible_work_values_json = item["compatible_work_values"]
        record.ai_augmentation_opportunities_json = item["ai_augmentation_opportunities"]
        record.entry_requirements_json = item["entry_requirements"]
        record.skill_gap_categories_json = item["skill_gap_categories"]
        record.typical_transition_path_json = item["typical_transition_path"]
        record.source_metadata_json = item["source_metadata"]
        record.version = ROLE_CATALOGUE_VERSION
        record.active = True
        db.add(record)


def item_index(mode: str | None = None) -> dict[str, dict[str, Any]]:
    definition = definition_for_mode(mode or "complete") if mode else assessment_definition()
    return {item["id"]: item for item in definition["items"]}


def response_public(row: AssessmentResponse) -> dict[str, Any]:
    value: Any = row.payload_json if row.payload_json else row.numeric_value
    if row.text_value is not None:
        value = row.text_value
    if row.option_value is not None:
        value = row.option_value
    return {
        "id": row.id,
        "session_id": row.session_id,
        "profile_id": row.profile_id,
        "module_id": row.module_id,
        "item_id": row.item_id,
        "response_type": row.response_type,
        "value": value,
        "numeric_value": row.numeric_value,
        "text_value": row.text_value,
        "option_value": row.option_value,
        "payload": row.payload_json,
        "excluded_from_recommendations": row.excluded_from_recommendations,
        "confirmation_status": row.confirmation_status,
        "source_type": row.source_type,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def assessment_prefill_from_profile(profile: Profile) -> dict[str, Any]:
    data = profile.data or {}
    prefill = data.get("assessment_prefill") if isinstance(data.get("assessment_prefill"), dict) else {}
    responses = prefill.get("responses") if isinstance(prefill.get("responses"), dict) else {}
    notes = prefill.get("notes") if isinstance(prefill.get("notes"), dict) else {}
    valid_items = item_index()
    filtered = {item_id: value for item_id, value in responses.items() if item_id in valid_items}
    return {
        "source": "natural_discovery_profile",
        "source_profile_id": profile.id,
        "responses": filtered,
        "notes": {item_id: notes.get(item_id, "Previously provided during Natural Discovery.") for item_id in filtered},
        "strategy": "Assessment may show these as previously provided values for confirmation or editing; they are not persisted until the user saves.",
    }


def score_public(row: AssessmentScore) -> dict[str, Any]:
    return {
        "id": row.id,
        "score_type": row.score_type,
        "dimension": row.dimension,
        "raw_score": row.raw_score,
        "normalized_score": row.normalized_score,
        "label": row.label,
        "interpretation": row.interpretation,
        "source_type": row.source_type,
        "confirmation_status": row.confirmation_status,
        "metadata": row.score_json,
    }


def match_factor_public(row: CareerMatchFactor) -> dict[str, Any]:
    return {
        "id": row.id,
        "factor_type": row.factor_type,
        "label": row.label,
        "raw_value": row.raw_value,
        "normalized_value": row.normalized_value,
        "weight": row.weight,
        "polarity": row.polarity,
        "evidence": row.evidence_json,
    }


def match_public(row: CareerMatch, factors: list[CareerMatchFactor] | None = None) -> dict[str, Any]:
    source_metadata = row.source_metadata_json or {}
    hypothesis_dimensions = source_metadata.get("hypothesis_dimensions") or {}
    return {
        "id": row.id,
        "session_id": row.session_id,
        "profile_id": row.profile_id,
        "role_template_id": row.role_template_id,
        "canonical_direction_id": canonical_career_direction_id(row),
        "category": row.category,
        "title": row.title,
        "role_family": row.role_family,
        "description": row.description,
        "alignment_score": row.alignment_score,
        "alignment_label": row.alignment_label,
        "explanation": row.explanation,
        "supporting_factors": row.supporting_factors_json,
        "conflicting_factors": row.conflicting_factors_json,
        "missing_skills": row.missing_skills_json,
        "transferable_skills": row.transferable_skills_json,
        "ai_opportunities": row.ai_opportunities_json,
        "next_step": row.next_step,
        "transition_difficulty": row.transition_difficulty,
        "time_horizon": row.time_horizon,
        "status": row.status,
        "user_feedback": row.user_feedback,
        "user_priority": row.user_priority,
        "assumptions": row.assumptions_json,
        "limitations": row.limitations_json,
        "source_metadata": source_metadata,
        "hypothesis_dimensions": hypothesis_dimensions,
        "dimension_scores": hypothesis_dimensions.get("scores", {}),
        "dimension_labels": hypothesis_dimensions.get("labels", {}),
        "dimension_explanations": hypothesis_dimensions.get("explanations", {}),
        "factors": [match_factor_public(factor) for factor in factors or []],
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def canonical_career_direction_id(match: CareerMatch) -> str:
    """Return the stable identity for a career direction, never its title.

    A role template is the catalogue identity shared by diagnostic and
    deep-dive snapshots.  The current-profession augmentation has one stable
    direction per profile.  Older unclassified records remain addressable by
    their match id rather than being deduplicated from a display title.
    """
    metadata = match.source_metadata_json or {}
    explicit = str(metadata.get("canonical_direction_id") or "").strip()
    if explicit:
        return explicit
    if match.role_template_id:
        return f"role-template:{match.role_template_id}"
    if str(metadata.get("source_type") or "").strip() == "current_profession_augmentation":
        return f"current-profession-augmentation:{match.profile_id}"
    return f"career-match:{match.id}"


def current_career_matches_for_profile(
    db: Session,
    profile_id: str,
    *,
    include_rejected: bool = False,
) -> list[CareerMatch]:
    """Choose one current snapshot per canonical career direction.

    A completed deep-dive assessment outranks an earlier Human Diagnostic for
    the same role-template id.  Rejected current directions stay rejected;
    they do not silently fall back to an older diagnostic snapshot.
    """
    rows = db.scalars(
        select(CareerMatch)
        .where(CareerMatch.profile_id == profile_id)
        .order_by(CareerMatch.created_at.desc(), CareerMatch.id.desc())
    ).all()
    latest_completed_session_id = db.scalar(
        select(AssessmentSession.id)
        .where(AssessmentSession.profile_id == profile_id, AssessmentSession.status == "completed")
        .order_by(AssessmentSession.completed_at.desc(), AssessmentSession.updated_at.desc())
        .limit(1)
    )

    current_by_direction: dict[str, CareerMatch] = {}
    for row in rows:
        direction_id = canonical_career_direction_id(row)
        existing = current_by_direction.get(direction_id)
        if not existing:
            current_by_direction[direction_id] = row
            continue
        row_session_rank = 2 if row.session_id and row.session_id == latest_completed_session_id else 1 if row.session_id else 0
        existing_session_rank = 2 if existing.session_id and existing.session_id == latest_completed_session_id else 1 if existing.session_id else 0
        row_key = (row_session_rank, row.created_at, row.id)
        existing_key = (existing_session_rank, existing.created_at, existing.id)
        if row_key > existing_key:
            current_by_direction[direction_id] = row

    current = list(current_by_direction.values())
    if not include_rejected:
        current = [row for row in current if row.status != "rejected"]
    return sorted(current, key=lambda row: (row.category, -float(row.alignment_score or 0), row.title, row.id))


def session_public(row: AssessmentSession, include_responses: bool = False, db: Session | None = None) -> dict[str, Any]:
    payload = {
        "id": row.id,
        "profile_id": row.profile_id,
        "mode": row.mode,
        "status": row.status,
        "consent_accepted": row.consent_accepted,
        "assessment_version": row.assessment_version,
        "scoring_version": row.scoring_version,
        "completion_time_seconds": row.completion_time_seconds,
        "last_confirmed_at": row.last_confirmed_at.isoformat() if row.last_confirmed_at else None,
        "source_type": row.source_type,
        "demo_marker": row.demo_marker,
        "metadata": row.metadata_json,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
        "completed_at": row.completed_at.isoformat() if row.completed_at else None,
    }
    if include_responses and db:
        responses = db.scalars(select(AssessmentResponse).where(AssessmentResponse.session_id == row.id).order_by(AssessmentResponse.created_at)).all()
        payload["responses"] = [response_public(item) for item in responses]
    return payload


def _as_numeric(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    if isinstance(value, dict):
        for key in ("score", "level", "value", "numeric_value"):
            if key in value:
                return _as_numeric(value[key])
    return None


def upsert_responses(db: Session, session: AssessmentSession, responses: list[dict[str, Any]]) -> list[AssessmentResponse]:
    index = item_index(session.mode)
    existing = {
        row.item_id: row
        for row in db.scalars(select(AssessmentResponse).where(AssessmentResponse.session_id == session.id)).all()
    }
    saved: list[AssessmentResponse] = []
    for payload in responses:
        item_id = str(payload.get("item_id", "")).strip()
        if not item_id:
            continue
        item = index.get(item_id) or item_index().get(item_id)
        module_id = str(payload.get("module_id") or (item or {}).get("module_id") or "")
        if not module_id:
            continue
        response_type = str(payload.get("response_type") or (item or {}).get("item_type") or "likert")
        value = payload.get("value")
        row = existing.get(item_id) or AssessmentResponse(
            session_id=session.id,
            profile_id=session.profile_id,
            user_id=session.user_id,
            module_id=module_id,
            item_id=item_id,
        )
        row.module_id = module_id
        row.response_type = response_type
        row.numeric_value = None
        row.text_value = None
        row.option_value = None
        row.payload_json = {}
        if response_type in {"likert", "value_rating"}:
            row.numeric_value = _as_numeric(value)
        elif response_type == "skill_level":
            row.payload_json = value if isinstance(value, dict) else {"level": value}
            row.numeric_value = _as_numeric(row.payload_json)
        elif response_type == "single_select":
            row.option_value = str(value) if value is not None else None
        elif response_type in {"text", "long_text"}:
            row.text_value = str(value or "")
        else:
            row.payload_json = value if isinstance(value, dict) else {"value": value}
            row.numeric_value = _as_numeric(value)
        row.excluded_from_recommendations = bool(payload.get("excluded_from_recommendations", row.excluded_from_recommendations))
        row.confirmation_status = str(payload.get("confirmation_status") or row.confirmation_status or "self_reported")
        row.source_type = str(payload.get("source_type") or "self_reported")
        db.add(row)
        saved.append(row)
    session.status = "in_progress"
    session.updated_at = utc_now_naive()
    db.flush()
    return saved


def _group_numeric_responses(session: AssessmentSession, responses: list[AssessmentResponse]) -> dict[str, list[tuple[dict[str, Any], float]]]:
    indexed = item_index()
    grouped: dict[str, list[tuple[dict[str, Any], float]]] = defaultdict(list)
    for response in responses:
        if response.excluded_from_recommendations:
            continue
        item = indexed.get(response.item_id)
        if not item or response.numeric_value is None:
            continue
        value = response.numeric_value
        if item["reverse_scored"]:
            value = reverse_score(value)
        grouped[item["dimension"] or item["module_id"]].append((item, value))
    return grouped


def _add_score(
    db: Session,
    session: AssessmentSession,
    score_type: str,
    dimension: str,
    raw_score: float,
    normalized_score: float,
    label: str,
    interpretation: str,
    metadata: dict[str, Any] | None = None,
) -> AssessmentScore:
    row = AssessmentScore(
        session_id=session.id,
        profile_id=session.profile_id,
        user_id=session.user_id,
        score_type=score_type,
        dimension=dimension,
        raw_score=round(raw_score, 4),
        normalized_score=round(normalized_score, 2),
        label=label,
        interpretation=interpretation,
        assessment_version=session.assessment_version,
        scoring_version=session.scoring_version,
        score_json=metadata or {},
        demo_marker=session.demo_marker,
    )
    db.add(row)
    return row


def calculate_scores(db: Session, session: AssessmentSession) -> dict[str, Any]:
    responses = db.scalars(select(AssessmentResponse).where(AssessmentResponse.session_id == session.id)).all()
    grouped = _group_numeric_responses(session, responses)
    definition = assessment_definition()
    indexed = {item["id"]: item for item in definition["items"]}
    db.execute(delete(AssessmentScore).where(AssessmentScore.session_id == session.id))
    db.execute(delete(PersonalityResult).where(PersonalityResult.session_id == session.id))
    db.execute(delete(CareerInterestResult).where(CareerInterestResult.session_id == session.id))
    db.execute(delete(WorkValueResult).where(WorkValueResult.session_id == session.id))
    db.execute(delete(SkillsInventory).where(SkillsInventory.session_id == session.id))
    db.execute(delete(AIReadinessResult).where(AIReadinessResult.session_id == session.id))
    db.execute(delete(ChangeReadinessResult).where(ChangeReadinessResult.session_id == session.id))
    scores: dict[str, Any] = {
        "personality": {},
        "career_interests": {},
        "work_values": {},
        "skills": {},
        "ai_literacy": {},
        "change_readiness": {},
        "goals_constraints": {},
        "raw_response_count": len(responses),
    }

    for dimension in ["openness", "conscientiousness", "extraversion", "agreeableness", "emotional_stability"]:
        values = [value for item, value in grouped.get(dimension, []) if item["module_id"] == "personality_work_style"]
        if not values:
            continue
        raw = sum(values) / len(values)
        normalized = normalize_likert_average(raw)
        label = tendency_label(raw)
        interpretation = f"Your current answers suggest {label.lower()} for {title_case_slug(dimension)}."
        scores["personality"][dimension] = {"raw_score": round(raw, 2), "normalized_score": normalized, "label": label, "item_count": len(values)}
        _add_score(db, session, "personality", dimension, raw, normalized, label, interpretation, {"item_count": len(values)})

    if scores["personality"]:
        db.add(PersonalityResult(session_id=session.id, profile_id=session.profile_id, user_id=session.user_id, results_json=scores["personality"], demo_marker=session.demo_marker))

    for dimension in ["realistic", "investigative", "artistic", "social", "enterprising", "conventional"]:
        values = [value for item, value in grouped.get(dimension, []) if item["module_id"] == "career_interests"]
        if not values:
            continue
        raw = sum(values) / len(values)
        normalized = normalize_likert_average(raw)
        label = alignment_label(normalized)
        interpretation = f"Your current answers suggest {label.lower()} with {title_case_slug(dimension)} activities."
        scores["career_interests"][dimension] = {"raw_score": round(raw, 2), "normalized_score": normalized, "label": label, "item_count": len(values)}
        _add_score(db, session, "career_interest", dimension, raw, normalized, label, interpretation, {"item_count": len(values)})

    top_interests = sorted(scores["career_interests"].items(), key=lambda item: item[1]["normalized_score"], reverse=True)[:3]
    combined_interest = "-".join(title_case_slug(key) for key, _ in top_interests)
    if scores["career_interests"]:
        db.add(CareerInterestResult(session_id=session.id, profile_id=session.profile_id, user_id=session.user_id, combined_profile=combined_interest, results_json={"dimensions": scores["career_interests"], "top_three": [key for key, _ in top_interests]}, demo_marker=session.demo_marker))

    value_scores: list[tuple[str, float, float]] = []
    for response in responses:
        item = indexed.get(response.item_id)
        if not item or item["module_id"] != "work_values" or response.numeric_value is None or response.excluded_from_recommendations:
            continue
        raw = response.numeric_value
        normalized = normalize_likert_average(raw)
        key = item["dimension"] or response.item_id
        value_scores.append((key, raw, normalized))
        label = "High priority" if raw >= 4 else "Moderate priority" if raw >= 3 else "Lower current priority"
        scores["work_values"][key] = {"raw_score": raw, "normalized_score": normalized, "label": label}
        _add_score(db, session, "work_value", key, raw, normalized, label, f"{title_case_slug(key)} is marked as {label.lower()}.")
    top_values = [{"value": key, "label": title_case_slug(key), "raw_score": raw, "normalized_score": norm} for key, raw, norm in sorted(value_scores, key=lambda item: item[1], reverse=True)[:5]]
    if value_scores:
        scores["work_values"]["top_values"] = top_values
        db.add(WorkValueResult(session_id=session.id, profile_id=session.profile_id, user_id=session.user_id, top_values_json=top_values, results_json=scores["work_values"], demo_marker=session.demo_marker))

    skill_rows: list[SkillsInventory] = []
    category_levels: dict[str, list[int]] = defaultdict(list)
    evidence_strengths: dict[str, list[int]] = defaultdict(list)
    skill_by_id: dict[str, dict[str, Any]] = {}
    for response in responses:
        item = indexed.get(response.item_id)
        if not item or item["module_id"] != "skills_inventory" or response.excluded_from_recommendations:
            continue
        payload = response.payload_json or {}
        raw_level = payload.get("level", response.numeric_value)
        if isinstance(raw_level, str):
            level = SKILL_LEVELS.get(raw_level, int(float(raw_level)) if raw_level.isdigit() else 0)
        else:
            level = int(raw_level or 0)
        level = max(0, min(4, level))
        evidence_status = str(payload.get("evidence_status") or payload.get("evidence") or "self_reported")
        category = str(item["metadata"].get("category") or "general")
        skill_label = str(item["metadata"].get("label") or title_case_slug(item["dimension"] or response.item_id))
        row = SkillsInventory(
            session_id=session.id,
            profile_id=session.profile_id,
            user_id=session.user_id,
            category=category,
            skill_id=item["dimension"] or response.item_id,
            skill_label=skill_label,
            level=level,
            evidence_status=evidence_status,
            evidence_note=str(payload.get("note") or ""),
            demo_marker=session.demo_marker,
        )
        db.add(row)
        skill_rows.append(row)
        category_levels[category].append(level)
        evidence_strengths[category].append(EVIDENCE_STRENGTH.get(evidence_status, 1))
        skill_by_id[row.skill_id] = {"level": level, "label": skill_label, "evidence_status": evidence_status, "category": category}
    for category, levels in category_levels.items():
        average_level = sum(levels) / len(levels)
        evidence_average = sum(evidence_strengths[category]) / len(evidence_strengths[category])
        normalized = normalize_skill_level(average_level)
        evidence_normalized = round(((evidence_average - 1) / 4) * 100, 2)
        label = alignment_label(normalized)
        scores["skills"][category] = {"average_level": round(average_level, 2), "normalized_score": normalized, "evidence_strength": evidence_normalized, "label": label}
        _add_score(db, session, "skill_category", category, average_level, normalized, label, f"{title_case_slug(category)} skills are currently {label.lower()}.", {"evidence_strength": evidence_normalized})
    scores["skills"]["items"] = skill_by_id

    ai_dimensions = {"ai_literacy": [], "ai_readiness": []}
    for response in responses:
        item = indexed.get(response.item_id)
        if not item or item["module_id"] != "ai_literacy_readiness" or response.numeric_value is None or response.excluded_from_recommendations:
            continue
        key = item["dimension"] or "ai_readiness"
        ai_dimensions.setdefault(key, []).append(response.numeric_value)
    ai_result: dict[str, Any] = {}
    for key, values in ai_dimensions.items():
        if not values:
            continue
        raw = sum(values) / len(values)
        normalized = normalize_likert_average(raw)
        level = ai_level(normalized)
        ai_result[key] = {"raw_score": round(raw, 2), "normalized_score": normalized, "level": level, "item_count": len(values)}
        _add_score(db, session, key, key, raw, normalized, level, f"Current {key.replace('_', ' ')} is described as {level}.", {"item_count": len(values)})
    scores["ai_literacy"] = ai_result
    if ai_result:
        db.add(AIReadinessResult(session_id=session.id, profile_id=session.profile_id, user_id=session.user_id, literacy_level=ai_result.get("ai_literacy", {}).get("level", "Emerging"), readiness_level=ai_result.get("ai_readiness", {}).get("level", "Emerging"), results_json=ai_result, demo_marker=session.demo_marker))

    change_values: list[float] = []
    constraints: list[str] = []
    for response in responses:
        item = indexed.get(response.item_id)
        if not item or item["module_id"] != "change_readiness" or response.numeric_value is None or response.excluded_from_recommendations:
            continue
        change_values.append(response.numeric_value)
        if response.numeric_value <= 2 and item["dimension"] in {"time", "budget", "uncertainty"}:
            constraints.append(title_case_slug(item["dimension"]))
    if change_values:
        raw = sum(change_values) / len(change_values)
        normalized = normalize_likert_average(raw)
        label = change_readiness_label(normalized, constraints)
        scores["change_readiness"] = {"raw_score": round(raw, 2), "normalized_score": normalized, "label": label, "constraints": constraints}
        _add_score(db, session, "change_readiness", "overall", raw, normalized, label, f"Professional change feasibility is currently: {label}.", {"constraints": constraints})
        db.add(ChangeReadinessResult(session_id=session.id, profile_id=session.profile_id, user_id=session.user_id, feasibility_label=label, results_json=scores["change_readiness"], constraints_json=constraints, demo_marker=session.demo_marker))

    for response in responses:
        item = indexed.get(response.item_id)
        if item and item["module_id"] in {"professional_background", "goals_constraints"}:
            scores["goals_constraints"][item["dimension"] or response.item_id] = response.text_value or response.option_value or response.payload_json or response.numeric_value

    db.flush()
    return scores


@dataclass
class MatchComputation:
    components: dict[str, float]
    dimensions: dict[str, Any]
    missing_skills: list[str]
    transferable_skills: list[dict[str, Any]]
    supporting: list[str]
    conflicting: list[str]


def _score_lookup(scores: dict[str, Any], section: str, dimension: str, default: float = 50) -> float:
    item = scores.get(section, {}).get(dimension)
    if isinstance(item, dict):
        return float(item.get("normalized_score", default))
    return default


def _skill_match(template: dict[str, Any], scores: dict[str, Any]) -> tuple[float, list[str], list[dict[str, Any]]]:
    skills = scores.get("skills", {}).get("items", {})
    required = template["required_skills"]
    useful = template["useful_transferable_skills"]
    if not required:
        return 50, [], []
    total = 0
    missing: list[str] = []
    transferable: list[dict[str, Any]] = []
    for skill in required:
        item = skills.get(skill)
        level = item.get("level", 0) if item else 0
        total += normalize_skill_level(level)
        if level < 2:
            missing.append(title_case_slug(skill))
    for skill in useful:
        item = skills.get(skill)
        if item and item.get("level", 0) >= 2:
            transferable.append(
                {
                    "original_skill": item["label"],
                    "potential_target_role": template["title"],
                    "relevance_level": "moderate" if item["level"] == 2 else "strong",
                    "explanation": f"{item['label']} may transfer to {template['title']} through practical context and communication.",
                    "evidence_level": item.get("evidence_status", "self_reported"),
                }
            )
    transfer_bonus = min(12, len(transferable) * 4)
    return round(min(100, total / len(required) + transfer_bonus), 2), missing, transferable


def _interest_match(template: dict[str, Any], scores: dict[str, Any]) -> float:
    profile = template["interest_profile"]
    if not profile:
        return 50
    total_weight = sum(profile.values())
    return round(sum(_score_lookup(scores, "career_interests", key) * weight for key, weight in profile.items()) / total_weight, 2)


def _values_match(template: dict[str, Any], scores: dict[str, Any]) -> tuple[float, list[str], list[str]]:
    top_values = {item["value"] for item in scores.get("work_values", {}).get("top_values", [])}
    compatible = set(template["compatible_work_values"])
    if not compatible:
        return 50, [], []
    overlap = top_values & compatible
    score = 45 + (len(overlap) / max(1, min(5, len(compatible)))) * 55
    conflicts: list[str] = []
    if "stability" in top_values and template["source_metadata"].get("entrepreneurship"):
        conflicts.append("Strong stability preference may conflict with independent-work uncertainty.")
    if "predictable_structure" in top_values and template["role_family"] in {"Creative Technology", "Entrepreneurship and Independent Work"}:
        conflicts.append("Predictable structure may require intentional boundaries in this direction.")
    return round(min(100, score), 2), [title_case_slug(item) for item in overlap], conflicts


def _work_style_match(template: dict[str, Any], scores: dict[str, Any]) -> float:
    tendencies = template["work_style_tendencies"]
    if not tendencies:
        return 50
    values = []
    for dimension, target_raw in tendencies.items():
        normalized = _score_lookup(scores, "personality", dimension)
        target_normalized = normalize_likert_average(float(target_raw))
        distance = abs(normalized - target_normalized)
        values.append(max(0, 100 - distance))
    return round(sum(values) / len(values), 2)


def _ai_opportunity_score(template: dict[str, Any], scores: dict[str, Any]) -> float:
    literacy = scores.get("ai_literacy", {}).get("ai_literacy", {}).get("normalized_score", 45)
    readiness = scores.get("ai_literacy", {}).get("ai_readiness", {}).get("normalized_score", 45)
    return round((float(literacy) * 0.45) + (float(readiness) * 0.55), 2)


def _feasibility_score(scores: dict[str, Any], missing_skills: list[str]) -> float:
    base = float(scores.get("change_readiness", {}).get("normalized_score", 50) or 50)
    return round(max(0, base - min(25, len(missing_skills) * 5)), 2)


def _experience_score(scores: dict[str, Any]) -> float:
    years = str(scores.get("goals_constraints", {}).get("years_experience") or "").strip().lower()
    return {
        "0-1": 20,
        "2-4": 45,
        "5-9": 65,
        "10+": 80,
    }.get(years, 45 if years else 35)


def _evidence_score_for_status(status: str) -> float:
    value = EVIDENCE_STRENGTH.get(status, 1)
    return round(20 + ((value - 1) / 4) * 70, 2)


def _evidence_strength_for_template(template: dict[str, Any], scores: dict[str, Any]) -> float:
    skills = scores.get("skills", {}).get("items", {})
    relevant = template["required_skills"] + template["useful_transferable_skills"]
    values: list[float] = []
    for skill in relevant:
        item = skills.get(skill)
        if item:
            values.append(_evidence_score_for_status(str(item.get("evidence_status", "self_reported"))))
    if not values:
        return 20
    base = sum(values) / len(values)
    project_text = str(scores.get("goals_constraints", {}).get("evidence") or "").strip()
    if project_text:
        base += 6
    return round(min(100, base), 2)


def hypothesis_dimensions(template: dict[str, Any], scores: dict[str, Any], computation: MatchComputation | None = None) -> dict[str, Any]:
    skills_match, missing, _transferable = _skill_match(template, scores)
    interest_match = _interest_match(template, scores)
    values_match, _aligned_values, _value_conflicts = _values_match(template, scores)
    work_style = _work_style_match(template, scores)
    ai_score = _ai_opportunity_score(template, scores)
    feasibility = _feasibility_score(scores, missing)
    if computation:
        skills_match = computation.components["skills_match"]
        interest_match = computation.components["interest_match"]
        values_match = computation.components["work_values_match"]
        work_style = computation.components["work_style_compatibility"]
        ai_score = computation.components["ai_augmentation_opportunity"]
        feasibility = computation.components["feasibility"]

    natural_fit = round((interest_match * 0.50) + (values_match * 0.28) + (work_style * 0.22), 2)
    capability_fit = round((skills_match * 0.68) + (ai_score * 0.17) + (_experience_score(scores) * 0.15), 2)
    evidence_strength = _evidence_strength_for_template(template, scores)
    transition_feasibility = feasibility
    scores_by_dimension = {
        "natural_fit": natural_fit,
        "capability_fit": capability_fit,
        "evidence_strength": evidence_strength,
        "transition_feasibility": transition_feasibility,
        "ai_augmentation_opportunity": ai_score,
    }
    labels = {key: fit_label(value) for key, value in scores_by_dimension.items()}
    explanations = {
        "natural_fit": "Derived from interests, values, and work-style preferences. Professional history, skill level, evidence, market, budget, and timeline are excluded.",
        "capability_fit": "Derived from current self-reported skills, AI capability, and broad professional exposure. It does not mean the capability is demonstrated.",
        "evidence_strength": "Derived from evidence statuses on relevant skills and optional project/evidence notes. Self-report remains weaker than project, certification, or practical evidence.",
        "transition_feasibility": "Derived from change readiness and current development gaps. It reflects practical constraints, not natural preference.",
        "ai_augmentation_opportunity": "Derived from AI literacy and practical AI readiness responses.",
    }
    return {
        "scores": scores_by_dimension,
        "labels": labels,
        "explanations": explanations,
        "rule_set": HYPOTHESIS_RULESET,
        "rule_set_version": HYPOTHESIS_RULESET_VERSION,
        "weights": CAREER_HYPOTHESIS_DIMENSION_WEIGHTS,
        "market_fit": {"label": "Not assessed in core assessment", "relationship": "Market fit is evaluated by market modules and must not modify Natural Fit."},
        "support_fit": {"label": "Not assessed in core assessment", "relationship": "Support fit is evaluated by supported-path modules and must not modify Natural Fit."},
    }


def compute_role_match(template: dict[str, Any], scores: dict[str, Any]) -> MatchComputation:
    skills_match, missing, transferable = _skill_match(template, scores)
    interest_match = _interest_match(template, scores)
    values_match, aligned_values, value_conflicts = _values_match(template, scores)
    work_style = _work_style_match(template, scores)
    ai_score = _ai_opportunity_score(template, scores)
    feasibility = _feasibility_score(scores, missing)
    components = {
        "skills_match": skills_match,
        "interest_match": interest_match,
        "work_values_match": values_match,
        "work_style_compatibility": work_style,
        "ai_augmentation_opportunity": ai_score,
        "feasibility": feasibility,
    }
    dimensions = hypothesis_dimensions(template, scores)
    supporting = []
    if dimensions["scores"]["natural_fit"] >= 65:
        supporting.append("Natural preference signals make this direction worth exploring.")
    if dimensions["scores"]["capability_fit"] >= 60:
        supporting.append("Current self-reported capability or transferable skills support this direction.")
    if dimensions["scores"]["evidence_strength"] >= 60:
        supporting.append("Some relevant evidence is already available.")
    if aligned_values:
        supporting.append(f"Aligned values: {', '.join(aligned_values)}.")
    if ai_score >= 55:
        supporting.append("AI readiness can support experimentation in this role family.")
    conflicting = value_conflicts[:]
    if missing:
        conflicting.append(f"Important development areas remain: {', '.join(missing[:4])}.")
    if dimensions["scores"]["evidence_strength"] < 45:
        conflicting.append("Evidence is currently limited; a career experiment can test this hypothesis.")
    if feasibility < 45:
        conflicting.append("Current time, budget, or uncertainty constraints may slow transition.")
    return MatchComputation(components, dimensions, missing, transferable, supporting, conflicting)


def weighted_alignment(components: dict[str, float]) -> float:
    return round(sum(components[key] * weight for key, weight in CAREER_MATCH_WEIGHTS.items()), 2)


def hypothesis_alignment_score(dimensions: dict[str, Any]) -> float:
    scores = dimensions.get("scores", dimensions)
    return round(sum(float(scores[key]) * weight for key, weight in CAREER_HYPOTHESIS_DIMENSION_WEIGHTS.items()), 2)


def categorize_match(template: dict[str, Any], computation: MatchComputation) -> str:
    if template["source_metadata"].get("entrepreneurship"):
        return "entrepreneurship_independent_work"
    if computation.components["skills_match"] >= 62 and len(computation.missing_skills) <= 2:
        return "adjacent_professional_roles"
    return "reskilling_opportunities"


def transition_difficulty(computation: MatchComputation) -> str:
    gaps = len(computation.missing_skills)
    feasibility = computation.components["feasibility"]
    if gaps <= 1 and feasibility >= 60:
        return "low-to-moderate"
    if gaps <= 3 and feasibility >= 45:
        return "moderate"
    return "substantial"


def time_horizon_for(difficulty: str) -> str:
    return {"low-to-moderate": "1-3 months", "moderate": "3-6 months", "substantial": "6-12+ months"}[difficulty]


def _current_profession(scores: dict[str, Any], profile: Profile) -> str:
    value = scores.get("goals_constraints", {}).get("current_profession")
    if value:
        return str(value)
    profile_data = profile.data or {}
    if profile_data.get("current_profession"):
        return str(profile_data["current_profession"])
    return "current profession"


def create_career_matches(db: Session, session: AssessmentSession, profile: Profile, scores: dict[str, Any]) -> list[CareerMatch]:
    sync_role_templates(db)
    existing_rejected_titles = {
        item.title.lower()
        for item in db.scalars(select(CareerMatch).where(CareerMatch.profile_id == profile.id, CareerMatch.status == "rejected")).all()
    }
    existing_session_matches = db.scalars(select(CareerMatch).where(CareerMatch.session_id == session.id)).all()
    replace_match_ids = [item.id for item in existing_session_matches if item.status not in {"saved", "rejected"}]
    if replace_match_ids:
        db.execute(delete(CareerMatchFactor).where(CareerMatchFactor.match_id.in_(replace_match_ids)))
        db.execute(delete(CareerMatch).where(CareerMatch.id.in_(replace_match_ids)))
    saved: list[CareerMatch] = []

    profession = _current_profession(scores, profile)
    ai_readiness_score = _ai_opportunity_score({"ai_augmentation_opportunities": []}, scores)
    feasibility = float(scores.get("change_readiness", {}).get("normalized_score", 50) or 50)
    current_context_dimensions = {
        "scores": {
            "natural_fit": 50.0,
            "capability_fit": round((ai_readiness_score * 0.35) + (_experience_score(scores) * 0.65), 2),
            "evidence_strength": 35.0,
            "transition_feasibility": feasibility,
            "ai_augmentation_opportunity": ai_readiness_score,
        },
        "labels": {},
        "explanations": {
            "natural_fit": "Current profession augmentation does not infer natural preference from historical work experience.",
            "capability_fit": "Uses broad professional exposure and current AI readiness.",
            "evidence_strength": "Requires explicit evidence before being treated as demonstrated capability.",
            "transition_feasibility": "Uses current change-readiness and constraints.",
            "ai_augmentation_opportunity": "Derived from AI literacy and practical AI readiness responses.",
        },
        "rule_set": HYPOTHESIS_RULESET,
        "rule_set_version": HYPOTHESIS_RULESET_VERSION,
        "weights": CAREER_HYPOTHESIS_DIMENSION_WEIGHTS,
        "market_fit": {"label": "Not assessed in core assessment"},
        "support_fit": {"label": "Not assessed in core assessment"},
    }
    current_context_dimensions["labels"] = {key: fit_label(value) for key, value in current_context_dimensions["scores"].items()}
    augment_score = round((ai_readiness_score * 0.55) + (feasibility * 0.2) + 25, 2)
    augment = CareerMatch(
        session_id=session.id,
        profile_id=profile.id,
        user_id=session.user_id,
        category="augment_current_profession",
        title=f"AI Augmentation for {profession.title()}",
        role_family="Current Profession",
        description="Explore how AI can improve current work before committing to a larger transition.",
        alignment_score=min(100, augment_score),
        alignment_label=alignment_label(min(100, augment_score)),
        explanation="This option starts with the user's current context and tests practical AI support before reskilling. It does not treat past work as proof of natural preference.",
        supporting_factors_json=["Uses existing professional context.", "Keeps transition reversible.", "Supports low-risk experimentation."],
        conflicting_factors_json=["Requires careful privacy and verification boundaries."],
        missing_skills_json=[],
        transferable_skills_json=[],
        ai_opportunities_json=["Automate repetitive tasks", "Improve research", "Generate alternatives", "Improve documentation"],
        next_step="Test one AI-assisted workflow in the current profession for one week.",
        transition_difficulty="low-to-moderate",
        time_horizon="1-4 weeks",
        assumptions_json=["The current profession has at least one knowledge-work, design, analysis, coordination, or documentation task."],
        limitations_json=["This is not a prediction of employment outcomes."],
        source_metadata_json={
            "source_type": "current_profession_augmentation",
            "version": ROLE_CATALOGUE_VERSION,
            "hypothesis_dimensions": current_context_dimensions,
            "source_of_truth": {
                "natural_fit": "not inferred from current profession",
                "capability_fit": "professional background plus AI readiness",
                "evidence_strength": "Evidence Passport or explicit assessment evidence only",
                "transition_feasibility": "change readiness and constraints",
            },
        },
        assessment_version=session.assessment_version,
        scoring_version=session.scoring_version,
        demo_marker=session.demo_marker,
    )
    if augment.title.lower() not in existing_rejected_titles:
        db.add(augment)
        db.flush()
        db.add(CareerMatchFactor(match_id=augment.id, factor_type="ai_augmentation_opportunity", label="AI readiness for current work", raw_value=ai_readiness_score, normalized_value=ai_readiness_score, weight=CAREER_MATCH_WEIGHTS["ai_augmentation_opportunity"], evidence_json={"source": "deterministic_ai_readiness_score"}))
        for key, value in current_context_dimensions["scores"].items():
            db.add(CareerMatchFactor(match_id=augment.id, factor_type=key, label=title_case_slug(key), raw_value=value, normalized_value=value, weight=CAREER_HYPOTHESIS_DIMENSION_WEIGHTS.get(key, 0), evidence_json={"source": "four_layer_hypothesis_dimension", "rule_set": HYPOTHESIS_RULESET, "version": HYPOTHESIS_RULESET_VERSION}))
        saved.append(augment)

    role_rows = db.scalars(select(CareerRoleTemplate).where(CareerRoleTemplate.active.is_(True))).all()
    candidates: list[tuple[float, CareerMatch, MatchComputation, CareerRoleTemplate]] = []
    for role_row in role_rows:
        template = {
            "id": role_row.id,
            "title": role_row.title,
            "role_family": role_row.role_family,
            "description": role_row.description,
            "required_skills": role_row.required_skills_json,
            "useful_transferable_skills": role_row.useful_transferable_skills_json,
            "interest_profile": role_row.interest_profile_json,
            "work_style_tendencies": role_row.work_style_tendencies_json,
            "compatible_work_values": role_row.compatible_work_values_json,
            "ai_augmentation_opportunities": role_row.ai_augmentation_opportunities_json,
            "entry_requirements": role_row.entry_requirements_json,
            "skill_gap_categories": role_row.skill_gap_categories_json,
            "typical_transition_path": role_row.typical_transition_path_json,
            "source_metadata": role_row.source_metadata_json,
        }
        computation = compute_role_match(template, scores)
        score = hypothesis_alignment_score(computation.dimensions)
        category = categorize_match(template, computation)
        difficulty = transition_difficulty(computation)
        row = CareerMatch(
            session_id=session.id,
            profile_id=profile.id,
            user_id=session.user_id,
            role_template_id=role_row.id,
            category=category,
            title=role_row.title,
            role_family=role_row.role_family,
            description=role_row.description,
            alignment_score=score,
            alignment_label=alignment_label(score),
            explanation=(
                f"Your current answers suggest this role family may have {alignment_label(score).lower()} as a provisional career hypothesis. "
                "The dimensions below separate natural preference, current capability, demonstrated evidence, and transition feasibility."
            ),
            supporting_factors_json=computation.supporting,
            conflicting_factors_json=computation.conflicting,
            missing_skills_json=computation.missing_skills,
            transferable_skills_json=computation.transferable_skills,
            ai_opportunities_json=role_row.ai_augmentation_opportunities_json,
            next_step=(
                "Complete a small role experiment to test this direction and create evidence."
                if computation.dimensions["scores"]["natural_fit"] >= 65 and computation.dimensions["scores"]["evidence_strength"] < 45
                else (role_row.typical_transition_path_json or ["Review real job descriptions"])[0]
            ),
            transition_difficulty=difficulty,
            time_horizon=time_horizon_for(difficulty),
            assumptions_json=[
                "Role templates are curated prototype data, not universal labour-market truth.",
                "Self-reported skills are not treated as objectively verified.",
                "Natural preference is calculated without professional history, salary, budget, or market demand.",
            ],
            limitations_json=[
                "Interests and tendencies are exploration signals, not proof of suitability.",
                "Employment outcomes depend on market, evidence, practice, and timing.",
                "A strong natural fit with weak evidence should be tested through a small career experiment.",
            ],
            source_metadata_json={
                **(role_row.source_metadata_json or {}),
                "hypothesis_dimensions": computation.dimensions,
                "legacy_component_scores": computation.components,
                "source_of_truth": {
                    "natural_fit": "career interests, work values, and work-style preferences",
                    "capability_fit": "skills inventory, AI readiness, and broad professional exposure",
                    "evidence_strength": "Evidence Passport-compatible evidence status and explicit project evidence",
                    "transition_feasibility": "change readiness, development gaps, time, budget, and constraints",
                    "market_fit": "market modules only",
                    "support_fit": "supported-path modules only",
                },
            },
            assessment_version=session.assessment_version,
            scoring_version=session.scoring_version,
            demo_marker=session.demo_marker,
        )
        candidates.append((score, row, computation, role_row))
    category_limits = {"adjacent_professional_roles": 4, "reskilling_opportunities": 3, "entrepreneurship_independent_work": 2}
    category_counts: dict[str, int] = defaultdict(int)
    for _, row, computation, _role_row in sorted(candidates, key=lambda item: item[0], reverse=True):
        if row.title.lower() in existing_rejected_titles:
            continue
        if category_counts[row.category] >= category_limits.get(row.category, 2):
            continue
        category_counts[row.category] += 1
        db.add(row)
        db.flush()
        for key, value in computation.components.items():
            polarity = "supporting" if value >= 55 else "conflicting"
            db.add(
                CareerMatchFactor(
                    match_id=row.id,
                    factor_type=key,
                    label=title_case_slug(key),
                    raw_value=value,
                    normalized_value=value,
                    weight=CAREER_MATCH_WEIGHTS[key],
                    polarity=polarity,
                    evidence_json={"scoring_version": session.scoring_version, "source": "deterministic_assessment_score"},
                )
            )
        for key, value in computation.dimensions["scores"].items():
            polarity = "supporting" if value >= 55 else "conflicting"
            db.add(
                CareerMatchFactor(
                    match_id=row.id,
                    factor_type=key,
                    label=title_case_slug(key),
                    raw_value=value,
                    normalized_value=value,
                    weight=CAREER_HYPOTHESIS_DIMENSION_WEIGHTS.get(key, 0),
                    polarity=polarity,
                    evidence_json={
                        "scoring_version": session.scoring_version,
                        "source": "four_layer_hypothesis_dimension",
                        "rule_set": HYPOTHESIS_RULESET,
                        "version": HYPOTHESIS_RULESET_VERSION,
                    },
                )
            )
        saved.append(row)
    db.flush()
    return saved


def _diagnostic_matching_scores(profile: Profile) -> dict[str, Any]:
    data = profile.data or {}
    snapshot = data.get("natural_discovery_snapshot") if isinstance(data.get("natural_discovery_snapshot"), dict) else {}
    career_interests = snapshot.get("career_interests") if isinstance(snapshot.get("career_interests"), dict) else {}
    dimensions = career_interests.get("dimensions") if isinstance(career_interests.get("dimensions"), dict) else {}
    interest_scores = {
        key: {"normalized_score": float(value.get("score") or 50)}
        for key, value in dimensions.items()
        if isinstance(value, dict) and isinstance(value.get("score"), (int, float))
    }
    if not interest_scores:
        interest_scores = {key: {"normalized_score": 50.0} for key in RIASEC_DIMENSIONS}
    values = snapshot.get("values") if isinstance(snapshot.get("values"), list) else []
    top_values = []
    for value in values[:5]:
        label = str(value).strip()
        if label:
            top_values.append({"value": slug(label), "label": label})

    # A quick diagnostic intentionally has no verified capability, personality,
    # market, or transition evidence. Neutral defaults keep those dimensions
    # visible without silently converting missing data into a low score.
    return {
        "career_interests": interest_scores,
        "work_values": {"top_values": top_values},
        "personality": {},
        "skills": {"items": {}},
        "ai_literacy": {"ai_literacy": {"normalized_score": 50.0}, "ai_readiness": {"normalized_score": 50.0}},
        "change_readiness": {"normalized_score": 50.0},
        "goals_constraints": {},
    }


def create_diagnostic_career_matches(db: Session, profile: Profile) -> list[CareerMatch]:
    """Create persisted career hypotheses directly from the Human Diagnostic.

    This is deliberately separate from the complete assessment scorer. It uses
    only the deterministic diagnostic output and leaves capability/evidence,
    market, and transition data explicitly unassessed.
    """
    existing = db.scalars(select(CareerMatch).where(CareerMatch.profile_id == profile.id)).all()
    if existing:
        return existing
    data = profile.data or {}
    if not isinstance(data.get("quick_diagnostic"), dict):
        return []

    sync_role_templates(db)
    db.flush()
    scores = _diagnostic_matching_scores(profile)
    quick = data.get("quick_diagnostic") or {}
    snapshot = data.get("natural_discovery_snapshot") or {}
    interest_result = snapshot.get("career_interests") if isinstance(snapshot, dict) else {}
    top_dimensions = interest_result.get("top_dimensions", []) if isinstance(interest_result, dict) else []
    contradictions = quick.get("contradictions", []) if isinstance(quick, dict) else []
    diagnostic_version = quick.get("version", "human-diagnostic-scoring-v2") if isinstance(quick, dict) else "human-diagnostic-scoring-v2"
    source_metadata_base = {
        "source_type": "human_diagnostic_hypothesis",
        "hypothesis_kind": "exploratory_direction",
        "input_sources": ["SELF-REPORT", "DIAGNOSTIC", "MISSING"],
        "diagnostic_id": profile.diagnostic_id,
        "diagnostic_version": diagnostic_version,
        "profile_completeness": quick.get("profile_completeness", "Limited") if isinstance(quick, dict) else "Limited",
        "contradictions": contradictions,
        "missing_evidence": ["No project, certification, or practical evidence was supplied by the Human Diagnostic."],
        "what_changed": ["Created from the latest Human Diagnostic snapshot; no assessment score or roadmap was mutated."],
    }

    candidates: list[tuple[float, CareerMatch, MatchComputation, CareerRoleTemplate]] = []
    for role_row in db.scalars(select(CareerRoleTemplate).where(CareerRoleTemplate.active.is_(True))).all():
        template = {
            "id": role_row.id,
            "title": role_row.title,
            "role_family": role_row.role_family,
            "description": role_row.description,
            "required_skills": role_row.required_skills_json,
            "useful_transferable_skills": role_row.useful_transferable_skills_json,
            "interest_profile": role_row.interest_profile_json,
            "work_style_tendencies": role_row.work_style_tendencies_json,
            "compatible_work_values": role_row.compatible_work_values_json,
            "ai_augmentation_opportunities": role_row.ai_augmentation_opportunities_json,
            "entry_requirements": role_row.entry_requirements_json,
            "skill_gap_categories": role_row.skill_gap_categories_json,
            "typical_transition_path": role_row.typical_transition_path_json,
            "source_metadata": role_row.source_metadata_json,
        }
        computation = compute_role_match(template, scores)
        score = hypothesis_alignment_score(computation.dimensions)
        row = CareerMatch(
            profile_id=profile.id,
            user_id=profile.user_id,
            role_template_id=role_row.id,
            category="reskilling_opportunities",
            title=role_row.title,
            role_family=role_row.role_family,
            description=role_row.description,
            alignment_score=score,
            alignment_label=alignment_label(score),
            explanation=(
                f"The Human Diagnostic suggests {role_row.title} is worth exploring as a provisional hypothesis. "
                "Natural preference signals are shown separately from capability, evidence, and transition readiness."
            ),
            supporting_factors_json=[
                f"Diagnostic interest signals: {', '.join(str(item) for item in top_dimensions[:3]) or 'still emerging'}.",
                "This direction is presented for exploration, not as a prediction or recommendation to commit.",
            ] + computation.supporting[:2],
            conflicting_factors_json=(list(contradictions) if isinstance(contradictions, list) else []) + [
                "Capability and evidence remain unverified until the relevant deep-dive and Evidence Passport steps are completed."
            ] + computation.conflicting[:2],
            missing_skills_json=computation.missing_skills,
            transferable_skills_json=[],
            ai_opportunities_json=role_row.ai_augmentation_opportunities_json,
            next_step="Run a small reversible experiment and record evidence before making a major decision.",
            transition_difficulty="not_assessed",
            time_horizon="not_assessed",
            assumptions_json=["The Human Diagnostic captures current self-perception and preferences only."],
            limitations_json=[
                "This is not a validated personality classification or employment prediction.",
                "Missing evidence is not treated as low capability.",
            ],
            source_metadata_json={
                **(role_row.source_metadata_json or {}),
                **source_metadata_base,
                "hypothesis_dimensions": computation.dimensions,
                "source_of_truth": {
                    "natural_fit": "diagnostic career-interest and value signals",
                    "capability_fit": "not assessed by Human Diagnostic",
                    "evidence_strength": "not assessed; Evidence Passport remains empty until evidence is added",
                    "transition_feasibility": "not assessed by Human Diagnostic",
                    "market_fit": "not assessed",
                },
            },
            assessment_version="human-diagnostic-v2",
            scoring_version="human-diagnostic-hypothesis-v1",
            demo_marker=bool(getattr(profile.user, "is_demo", False)) if getattr(profile, "user", None) else False,
        )
        candidates.append((score, row, computation, role_row))

    for _, row, computation, _role_row in sorted(candidates, key=lambda item: item[0], reverse=True)[:6]:
        db.add(row)
        db.flush()
        for key, value in computation.dimensions["scores"].items():
            db.add(
                CareerMatchFactor(
                    match_id=row.id,
                    factor_type=key,
                    label=title_case_slug(key),
                    raw_value=value,
                    normalized_value=value,
                    weight=CAREER_HYPOTHESIS_DIMENSION_WEIGHTS.get(key, 0),
                    polarity="supporting" if value >= 55 else "unassessed",
                    evidence_json={
                        "source": "human_diagnostic",
                        "diagnostic_version": diagnostic_version,
                        "missing_data_policy": "neutral_unassessed",
                    },
                )
            )
    db.commit()
    return db.scalars(select(CareerMatch).where(CareerMatch.profile_id == profile.id)).all()


def complete_assessment_session(db: Session, session: AssessmentSession, profile: Profile) -> dict[str, Any]:
    responses = db.scalars(select(AssessmentResponse).where(AssessmentResponse.session_id == session.id)).all()
    required_ids = {item["id"] for item in definition_for_mode(session.mode)["items"] if item["required"]}
    answered_required = {response.item_id for response in responses if (response.numeric_value is not None or response.text_value or response.option_value or response.payload_json)}
    missing = sorted(required_ids - answered_required)
    if missing:
        return {"status": "incomplete", "missing_required_items": missing, "session": session_public(session)}
    session.assessment_version = ASSESSMENT_VERSION
    session.scoring_version = SCORING_VERSION
    scores = calculate_scores(db, session)
    matches = create_career_matches(db, session, profile, scores)
    session.status = "completed"
    session.completed_at = utc_now_naive()
    session.updated_at = utc_now_naive()
    session.completion_time_seconds = int((session.completed_at - session.created_at).total_seconds())
    db.commit()
    return {
        "status": "completed",
        "session": session_public(session),
        "results": results_for_profile(db, profile.id),
        "career_matches": [match_public(match, db.scalars(select(CareerMatchFactor).where(CareerMatchFactor.match_id == match.id)).all()) for match in matches],
    }


def results_for_profile(db: Session, profile_id: str) -> dict[str, Any]:
    session = db.scalar(select(AssessmentSession).where(AssessmentSession.profile_id == profile_id).order_by(AssessmentSession.updated_at.desc()))
    if not session:
        return {
            "status": "not_started",
            "disclaimer": DISCLAIMER,
            "assessment_version": ASSESSMENT_VERSION,
            "scoring_version": SCORING_VERSION,
            "session": None,
            "scores": [],
            "grouped_scores": {},
            "methodology_note": METHODOLOGY_NOTE,
            "summary": {},
            "module_statuses": {},
            "reflection_prompts": [],
        }
    scores = db.scalars(select(AssessmentScore).where(AssessmentScore.session_id == session.id)).all()
    grouped: dict[str, dict[str, Any]] = defaultdict(dict)
    for score in scores:
        grouped[score.score_type][score.dimension] = score_public(score)
    career_interest = db.scalar(select(CareerInterestResult).where(CareerInterestResult.session_id == session.id).order_by(CareerInterestResult.created_at.desc()))
    ai_result = db.scalar(select(AIReadinessResult).where(AIReadinessResult.session_id == session.id).order_by(AIReadinessResult.created_at.desc()))
    change_result = db.scalar(select(ChangeReadinessResult).where(ChangeReadinessResult.session_id == session.id).order_by(ChangeReadinessResult.created_at.desc()))
    work_values = db.scalar(select(WorkValueResult).where(WorkValueResult.session_id == session.id).order_by(WorkValueResult.created_at.desc()))
    skills = db.scalars(select(SkillsInventory).where(SkillsInventory.session_id == session.id).order_by(SkillsInventory.category, SkillsInventory.skill_label)).all()
    definition = definition_for_mode(session.mode)
    items_by_module: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in definition["items"]:
        items_by_module[item["module_id"]].append(item)
    answered_responses = db.scalars(select(AssessmentResponse).where(AssessmentResponse.session_id == session.id)).all()
    answered_by_module: dict[str, set[str]] = defaultdict(set)
    for response in answered_responses:
        answered = response.numeric_value is not None or bool(response.text_value) or bool(response.option_value) or bool(response.payload_json)
        if answered:
            answered_by_module[response.module_id].add(response.item_id)
    module_statuses: dict[str, dict[str, Any]] = {}
    for module in assessment_definition()["modules"]:
        module_items = items_by_module.get(module["id"], [])
        required_ids = {item["id"] for item in module_items if item["required"]}
        answered_ids = answered_by_module.get(module["id"], set())
        required_answered = len(required_ids & answered_ids)
        complete = bool(module_items) and required_answered == len(required_ids) and (bool(required_ids) or len(answered_ids) == len(module_items))
        status = "completed" if complete and session.status == "completed" else ("in_progress" if answered_ids else "not_started")
        module_statuses[module["id"]] = {
            "status": status,
            "answered": len(answered_ids),
            "total": len(module_items),
            "required": len(required_ids),
            "required_answered": required_answered,
            "source": "assessment_responses",
        }
    return {
        "status": session.status,
        "disclaimer": DISCLAIMER,
        "methodology_note": METHODOLOGY_NOTE,
        "assessment_version": session.assessment_version,
        "scoring_version": session.scoring_version,
        "session": session_public(session),
        "scores": [score_public(score) for score in scores],
        "grouped_scores": dict(grouped),
        "module_statuses": module_statuses,
        "summary": {
            "combined_interest_profile": career_interest.combined_profile if career_interest else "",
            "top_work_values": work_values.top_values_json if work_values else [],
            "ai_literacy_level": ai_result.literacy_level if ai_result else "Emerging",
            "ai_readiness_level": ai_result.readiness_level if ai_result else "Emerging",
            "change_readiness": change_result.feasibility_label if change_result else "Exploring options",
            "skills": [
                {
                    "id": skill.id,
                    "skill_id": skill.skill_id,
                    "label": skill.skill_label,
                    "category": skill.category,
                    "level": skill.level,
                    "level_label": SKILL_LEVEL_LABELS.get(skill.level, "No experience"),
                    "evidence_status": skill.evidence_status,
                    "evidence_note": skill.evidence_note,
                }
                for skill in skills
            ],
        },
        "reflection_prompts": [
            "Which result felt most accurate?",
            "Which result did not represent you?",
            "Which work environment would you avoid?",
            "Which career option interests you even if its score is lower?",
            "Which values are non-negotiable?",
            "What constraint has the greatest influence on your decision?",
            "What small experiment could reduce uncertainty?",
        ],
    }


def career_matches_for_profile(db: Session, profile_id: str, include_rejected: bool = False) -> list[dict[str, Any]]:
    profile = db.get(Profile, profile_id)
    if profile:
        create_diagnostic_career_matches(db, profile)
        # Keep the downstream Career Hypotheses table synchronized with the
        # persisted match snapshot. Import locally to avoid a service cycle.
        from app.services.career_resilience_engine import ensure_hypotheses_from_matches

        ensure_hypotheses_from_matches(db, profile)
    rows = current_career_matches_for_profile(db, profile_id, include_rejected=include_rejected)
    factors = db.scalars(select(CareerMatchFactor).where(CareerMatchFactor.match_id.in_([row.id for row in rows]))).all() if rows else []
    by_match: dict[str, list[CareerMatchFactor]] = defaultdict(list)
    for factor in factors:
        by_match[factor.match_id].append(factor)
    return [match_public(row, by_match.get(row.id, [])) for row in rows]


def set_match_status(db: Session, match: CareerMatch, status: str, user_feedback: str | None = None) -> CareerMatch:
    match.status = status
    if user_feedback is not None:
        match.user_feedback = user_feedback
    db.add(
        CareerDecision(
            profile_id=match.profile_id,
            user_id=match.user_id,
            career_match_id=match.id,
            decision_type=status,
            status="saved",
            notes=user_feedback or "",
            demo_marker=match.demo_marker,
        )
    )
    db.commit()
    db.refresh(match)
    return match


def comparison_public(row: CareerComparison) -> dict[str, Any]:
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "match_ids": row.match_ids_json,
        "criteria_weights": row.criteria_weights_json,
        "decision_priorities": row.decision_priorities_json,
        "matrix": row.matrix_json,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def create_comparison(db: Session, profile: Profile, match_ids: list[str], weights: dict[str, float] | None, priorities: dict[str, Any] | None, user_id: str | None = None) -> CareerComparison:
    selected = match_ids[:3]
    rows = db.scalars(select(CareerMatch).where(CareerMatch.profile_id == profile.id, CareerMatch.id.in_(selected))).all()
    criteria_weights = {**COMPARISON_CRITERIA, **(weights or {})}
    matrix = {"items": []}
    for row in rows:
        factors = {factor.factor_type: factor.normalized_value for factor in db.scalars(select(CareerMatchFactor).where(CareerMatchFactor.match_id == row.id)).all()}
        matrix["items"].append(
            {
                "match_id": row.id,
                "title": row.title,
                "alignment_label": row.alignment_label,
                "strengths": row.supporting_factors_json,
                "challenges": row.conflicting_factors_json,
                "uncertainties": row.assumptions_json + row.limitations_json,
                "next_experiment": row.next_step,
                "evidence_required": row.missing_skills_json or ["Collect external evidence before committing."],
                "criteria": {
                    "natural_fit": factors.get("natural_fit", 50),
                    "capability_fit": factors.get("capability_fit", 50),
                    "evidence_strength": factors.get("evidence_strength", 50),
                    "transition_feasibility": factors.get("transition_feasibility", 50),
                    "skills_match": factors.get("skills_match", row.alignment_score),
                    "interest_alignment": factors.get("interest_match", 50),
                    "work_values_alignment": factors.get("work_values_match", 50),
                    "work_style_fit": factors.get("work_style_compatibility", 50),
                    "ai_opportunity": factors.get("ai_augmentation_opportunity", 50),
                    "training_required": 100 - min(100, len(row.missing_skills_json) * 20),
                    "transition_difficulty": {"low-to-moderate": 80, "moderate": 55, "substantial": 30}.get(row.transition_difficulty, 50),
                    "time_horizon": {"1-4 weeks": 90, "1-3 months": 78, "3-6 months": 55, "6-12+ months": 35}.get(row.time_horizon, 50),
                    "resource_requirements": 70 if row.transition_difficulty != "substantial" else 40,
                    "employment_entrepreneurship": 70 if row.category != "entrepreneurship_independent_work" else 55,
                    "identified_risks": 100 - min(80, len(row.conflicting_factors_json) * 18),
                    "user_priority": row.user_priority or 50,
                },
            }
        )
    row = CareerComparison(
        profile_id=profile.id,
        user_id=user_id or profile.user_id,
        match_ids_json=[item.id for item in rows],
        criteria_weights_json=criteria_weights,
        decision_priorities_json=priorities or {},
        matrix_json=matrix,
        demo_marker=bool(getattr(profile.user, "is_demo", False)) if getattr(profile, "user", None) else False,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def create_roadmap_draft_from_match(db: Session, match: CareerMatch) -> dict[str, Any]:
    roadmap = db.scalar(select(Roadmap).where(Roadmap.profile_id == match.profile_id).order_by(Roadmap.created_at.desc()))
    created = False
    if not roadmap:
        roadmap = Roadmap(user_id=match.user_id, profile_id=match.profile_id, data={**generate_roadmap_fallback(), "version": 0, "status": "active"})
        db.add(roadmap)
        db.flush()
        created = True
    normalize_legacy(db, roadmap)
    if created:
        snapshot(db, roadmap, "Initial roadmap created from career assessment")
    stages = [
        ("seven_days", "Validate the direction", "Inspect real job descriptions, interview a professional, or complete a small practical exercise."),
        ("thirty_days", "Close one skill gap", "Complete a focused course, build a small portfolio project, or learn one required tool."),
        ("thirty_days", "Demonstrate capability", "Publish a project, update a portfolio, or document transferable skills."),
        ("six_months", "Market transition carefully", "Update CV, prepare role-specific applications, contact networks, or test a client offer."),
    ]
    created_actions = []
    for index, (horizon, stage, description) in enumerate(stages, start=1):
        action = RoadmapAction(
            roadmap_id=roadmap.id,
            profile_id=match.profile_id,
            user_id=match.user_id,
            horizon=horizon,
            title=f"{stage}: {match.title}",
            description=description,
            reason=f"Created from user-confirmed career match {match.title}.",
            first_step=match.next_step if index == 1 else description.split(",")[0],
            success_criteria="Record evidence and decide whether to continue, adapt, or stop this direction.",
            estimated_minutes=60,
            effort="medium",
            impact="high",
            priority=index,
            status="not_started",
            source_type="career_match",
            profile_signals_json=match.supporting_factors_json,
            rag_sources_json=[],
            ethical_cautions_json=match.limitations_json,
        )
        db.add(action)
        db.flush()
        roadmap_event(db, roadmap.id, match.user_id or roadmap.user_id, "action_added", action.id, {"source_type": "career_match", "career_match_id": match.id})
        created_actions.append(action)
    match.status = "roadmap_draft_created"
    db.add(CareerDecision(profile_id=match.profile_id, user_id=match.user_id, career_match_id=match.id, decision_type="create_roadmap_draft", status="saved", notes="User explicitly requested an exploratory roadmap draft.", demo_marker=match.demo_marker))
    db.commit()
    return {
        "roadmap_id": roadmap.id,
        "career_match": match_public(match),
        "actions": [
            {
                "id": action.id,
                "title": action.title,
                "horizon": action.horizon,
                "status": action.status,
            }
            for action in created_actions
        ],
    }


def delete_assessment_data(db: Session, profile_id: str) -> dict[str, Any]:
    sessions = db.scalars(select(AssessmentSession.id).where(AssessmentSession.profile_id == profile_id)).all()
    match_ids = db.scalars(select(CareerMatch.id).where(CareerMatch.profile_id == profile_id)).all()
    inventory_ids = db.scalars(select(SkillsInventory.id).where(SkillsInventory.profile_id == profile_id)).all()
    deleted = {
        "sessions": len(sessions),
        "matches": len(match_ids),
        "skills": len(inventory_ids),
    }
    if match_ids:
        db.execute(delete(CareerMatchFactor).where(CareerMatchFactor.match_id.in_(match_ids)))
    if inventory_ids:
        db.execute(delete(SkillEvidence).where(SkillEvidence.skill_inventory_id.in_(inventory_ids)))
    for model in [
        CareerDecision,
        CareerComparison,
        CareerMatch,
        AssessmentInterpretation,
        ChangeReadinessResult,
        AIReadinessResult,
        WorkValueResult,
        CareerInterestResult,
        PersonalityResult,
        SkillsInventory,
        AssessmentScore,
        AssessmentResponse,
        AssessmentSession,
    ]:
        db.execute(delete(model).where(model.profile_id == profile_id))
    db.commit()
    return {"status": "deleted", "deleted": deleted}

