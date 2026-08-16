from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.config import get_settings


class ChatRequest(BaseModel):
    message: str
    profile_id: str | None = None
    profileId: str | None = None
    conversation_id: str | None = None
    conversationId: str | None = None
    mode: str = "text"
    voice_personality: str = "Calm Guide"
    conversation_mode: str = "Explain simply"
    route: str = "/"
    selected_profile_node: str | None = None
    language: str = "en"
    client_context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        settings = get_settings()
        if not value.strip():
            raise ValueError("Message is required.")
        if len(value) > settings.max_chat_message_chars:
            raise ValueError("Message is too long.")
        return value

    @field_validator("route")
    @classmethod
    def validate_route(cls, value: str) -> str:
        if value and not value.startswith("/"):
            raise ValueError("Route must be an application path.")
        return value or "/"

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        if value not in {"en", "ro", "no"}:
            raise ValueError("Language must be one of en, ro, or no.")
        return value

    @model_validator(mode="after")
    def validate_context_size(self) -> "ChatRequest":
        settings = get_settings()
        for key, value in (self.client_context or {}).items():
            if len(str(key)) > 80 or len(str(value)) > settings.max_context_field_chars:
                raise ValueError("Client context contains a field that is too long.")
        if self.selected_profile_node and len(self.selected_profile_node) > settings.max_context_field_chars:
            raise ValueError("Selected profile node is too long.")
        return self


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    message_id: str
    suggested_actions: list[str] = Field(default_factory=list)
    confidence_note: str = ""
    sources_used: list[dict[str, str | float]] = Field(default_factory=list)
    ethical_note: str = ""
    intent: str = "conversational_question"
    executed_command: dict | None = None
    profile_signals_used: list[str] = Field(default_factory=list)
    grounding_status: str = "general"
    audio_available: bool = False
    retrieval_status: dict = Field(default_factory=dict)
    timing: dict[str, int] = Field(default_factory=dict)
    rag_run_id: str | None = None
    context_quality: str = "insufficient"
    insufficient_context: bool = False
