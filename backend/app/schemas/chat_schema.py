from pydantic import BaseModel


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
    client_context: dict = {}


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    message_id: str
    suggested_actions: list[str] = []
    confidence_note: str = ""
    sources_used: list[dict[str, str | float]] = []
    ethical_note: str = ""
    intent: str = "conversational_question"
    executed_command: dict | None = None
    profile_signals_used: list[str] = []
    grounding_status: str = "general"
    audio_available: bool = False
    retrieval_status: dict = {}
    timing: dict[str, int] = {}
