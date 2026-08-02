from typing import Literal

from pydantic import BaseModel, Field, field_validator


class DiagnosticCreate(BaseModel):
    interests: list[str] = Field(min_length=1)
    natural_activities: list[str] = Field(default_factory=list)
    problems_noticed: list[str] = Field(default_factory=list)
    preferred_orientation: list[str] = Field(default_factory=list)
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
    raw_answers: dict[str, str] = Field(default_factory=dict)

    @field_validator("natural_activities", "problems_noticed", "preferred_orientation", "fears", "skills", "preferred_learning_style", "cognitive_style", "ai_tools_used", "ai_help_goals", mode="before")
    @classmethod
    def accept_legacy_strings(cls, value):
        if isinstance(value, str):
            return [value] if value.strip() else []
        return value or []

    @field_validator("preferred_interaction", mode="before")
    @classmethod
    def normalize_interaction(cls, value):
        normalized = str(value or "both").lower()
        return normalized if normalized in {"text", "voice", "both"} else "both"


class DiagnosticCreated(BaseModel):
    diagnostic_id: str
    profile_id: str


class DiagnosticPublic(BaseModel):
    id: str
    created_at: str
    payload: dict
