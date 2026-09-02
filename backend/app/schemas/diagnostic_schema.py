from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class DiagnosticCreate(BaseModel):
    interests: list[str] = Field(min_length=1)
    natural_activities: list[str] = Field(default_factory=list)
    problems_noticed: list[str] = Field(default_factory=list)
    preferred_orientation: list[str] = Field(default_factory=list)
    career_interests: dict[str, int] = Field(default_factory=dict)
    fears: list[str] = Field(default_factory=list)
    fear_intensity: int = Field(default=5, ge=1, le=10)
    ai_threat_or_opportunity: str
    unclear_future: str
    desired_world: str
    values: list[str] = Field(min_length=1)
    contribution_if_supported: str
    skills: list[str] = Field(default_factory=list)
    preferred_learning_style: list[str] = Field(default_factory=list)
    cognitive_style: list[str] = Field(default_factory=list)
    ai_experience: str
    ai_tools_used: list[str] = Field(default_factory=list)
    ai_confidence: int = Field(default=5, ge=1, le=10)
    ai_help_goals: list[str] = Field(default_factory=list)
    preferred_interaction: Literal["text", "voice", "both"] = "both"
    # The five-step Human Diagnostic stores these as explicit self-report
    # signals. Keeping them in the API contract prevents Pydantic from
    # silently discarding them before deterministic profile generation.
    curiosity_score: int = Field(default=0, ge=0, le=7)
    practical_conceptual: int = Field(default=0, ge=0, le=7)
    people_systems: int = Field(default=0, ge=0, le=7)
    creative_analytical: int = Field(default=0, ge=0, le=7)
    exploration_scenario: str = ""
    fear_dimensions: dict[str, int] = Field(default_factory=dict)
    fear_management: str = ""
    value_priorities: list[str] = Field(default_factory=list)
    value_tradeoff: str = ""
    meaningful_work_acceptability: int = Field(default=0, ge=0, le=7)
    capability_confidence: dict[str, int] = Field(default_factory=dict)
    learning_mode: str = ""
    decision_style: str = ""
    ai_roles: list[str] = Field(default_factory=list)
    ai_never_decisions: list[str] = Field(default_factory=list)
    ai_explanation_need: int = Field(default=0, ge=0, le=7)
    ai_oversight: int = Field(default=0, ge=0, le=7)
    ai_automation_comfort: int = Field(default=0, ge=0, le=7)
    raw_answers: dict[str, Any] = Field(default_factory=dict)

    @field_validator("natural_activities", "problems_noticed", "preferred_orientation", "fears", "skills", "preferred_learning_style", "cognitive_style", "ai_tools_used", "ai_help_goals", mode="before")
    @classmethod
    def accept_legacy_strings(cls, value):
        if isinstance(value, str):
            return [value] if value.strip() else []
        return value or []

    @field_validator("career_interests", mode="before")
    @classmethod
    def normalize_career_interests(cls, value):
        if not isinstance(value, dict):
            return {}
        allowed = {"realistic", "investigative", "artistic", "social", "enterprising", "conventional"}
        normalized: dict[str, int] = {}
        for key, raw in value.items():
            dimension = str(key).strip().lower()
            if dimension not in allowed:
                continue
            try:
                score = int(raw)
            except (TypeError, ValueError):
                continue
            normalized[dimension] = max(1, min(5, score))
        return normalized

    @field_validator("preferred_interaction", mode="before")
    @classmethod
    def normalize_interaction(cls, value):
        normalized = str(value or "both").lower()
        return normalized if normalized in {"text", "voice", "both"} else "both"


class DiagnosticCreated(BaseModel):
    diagnostic_id: str
    profile_id: str


class DiagnosticResponseInput(BaseModel):
    question_id: str
    assessment_domain: str
    question_type: str
    response: Any = None
    normalized_value: float | None = None
    confidence: float | None = Field(default=None, ge=1, le=7)
    source: str = "self_report"
    version: str = "human-diagnostic-v2"
    interpretation: str | None = None
    completeness: float = Field(default=1, ge=0, le=1)
    scoring_metadata: dict[str, Any] = Field(default_factory=dict)


class DiagnosticDraftRequest(BaseModel):
    diagnostic_id: str | None = None
    current_step: int = Field(default=0, ge=0, le=4)
    payload: dict[str, Any] = Field(default_factory=dict)
    responses: list[DiagnosticResponseInput] = Field(default_factory=list)
    diagnostic_version: str = "human-diagnostic-v2"


class DiagnosticDraftResponse(BaseModel):
    diagnostic_id: str
    status: str
    current_step: int
    updated_at: str
    payload: dict[str, Any]
    responses: list[dict[str, Any]]


class DiagnosticPublic(BaseModel):
    id: str
    created_at: str
    payload: dict
