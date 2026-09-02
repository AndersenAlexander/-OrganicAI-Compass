import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.services.elevenlabs_conversation import (
    ElevenLabsConversationError,
    check_token_rate_limit,
    client_server_location,
    get_conversation_token,
    live_voice_status,
)
from app.services.live_voice_metadata import get_latest_voice_turn
from app.services.openai_realtime import OpenAIRealtimeSessionError, create_realtime_sdp_answer
from app.services.speech_to_text import transcribe_audio
from app.services.text_to_speech import synthesize_speech

router = APIRouter()
ALLOWED_AUDIO_MIME_TYPES = {"audio/webm", "audio/wav", "audio/mpeg", "audio/mp4", "audio/ogg", "application/octet-stream"}
ALLOWED_AUDIO_EXTENSIONS = {".webm", ".wav", ".mp3", ".m4a", ".ogg"}
MAX_SDP_BYTES = 120_000


class TranscriptionResponse(BaseModel):
    transcript: str


class SpeechRequest(BaseModel):
    text: str


class SpeechResponse(BaseModel):
    audio_url: str


class LiveVoiceStatusResponse(BaseModel):
    provider: str
    liveVoiceEnabled: bool
    liveVoiceConfigured: bool
    customLlmEnabled: bool = False
    customLlmConfigured: bool = False
    legacyFallbackEnabled: bool
    agentIdConfigured: bool
    apiKeyConfigured: bool = False
    serverLocation: str
    residencyMode: str = "standard"
    environment: str
    publicBackendReachable: bool = False
    blockingIssues: list[dict[str, str]] = []


class ConversationTokenRequest(BaseModel):
    profile_id: str | None = Field(default=None, max_length=80)
    app_conversation_id: str | None = Field(default=None, max_length=80)
    route: str = Field(default="/", max_length=240)
    selected_profile_node: str | None = Field(default=None, max_length=120)
    selected_recommendation_id: str | None = Field(default=None, max_length=80)
    language: str = Field(default="en")
    voice_personality: str = Field(default="Calm Guide", max_length=80)
    conversation_mode: str = Field(default="Explain simply", max_length=120)
    client_context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        if value not in {"en", "ro", "no"}:
            raise ValueError("Language must be one of en, ro, or no.")
        return value

    @field_validator("route")
    @classmethod
    def validate_route(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("Route must be an application path.")
        return value

    @model_validator(mode="after")
    def validate_client_context(self) -> "ConversationTokenRequest":
        settings = get_settings()
        if len(self.client_context) > 12:
            raise ValueError("Client context is too large.")
        total_size = sum(len(str(key)) + len(str(value)) for key, value in self.client_context.items())
        if total_size > getattr(settings, "max_context_field_chars", 1500):
            raise ValueError("Client context is too large.")
        return self


class ConversationTokenResponse(BaseModel):
    token: str
    conversation_id: str
    server_location: str
    environment: str


def _validate_sdp_offer(payload: bytes) -> str:
    if not payload:
        raise HTTPException(status_code=422, detail="SDP offer is required.")
    if len(payload) > MAX_SDP_BYTES:
        raise HTTPException(status_code=413, detail="SDP offer is too large.")
    try:
        sdp = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise HTTPException(status_code=422, detail="SDP offer must be UTF-8 text.") from error
    if not sdp.lstrip().startswith("v=0") or "m=audio" not in sdp:
        raise HTTPException(status_code=422, detail="A valid audio SDP offer is required.")
    return sdp


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(
    request: Request,
    file: UploadFile = File(...),
    _current_user: User = Depends(get_current_user),
) -> TranscriptionResponse:
    settings = get_settings()
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > getattr(settings, "max_audio_upload_bytes", 8_000_000) + 1_000_000:
                raise HTTPException(status_code=413, detail="Audio upload is too large.")
        except ValueError as error:
            raise HTTPException(status_code=400, detail="Content-Length must be a valid integer.") from error
    content_type = (file.content_type or "").split(";")[0].lower()
    suffix = Path(file.filename or "voice-message.webm").suffix.lower() or ".webm"
    if content_type not in ALLOWED_AUDIO_MIME_TYPES or suffix not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=422, detail="Unsupported audio upload format.")
    temp_path = ""

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = temp_file.name
            total = 0
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > getattr(settings, "max_audio_upload_bytes", 8_000_000):
                    raise HTTPException(status_code=413, detail="Audio upload is too large.")
                temp_file.write(chunk)

        transcript = await transcribe_audio(temp_path)
        return TranscriptionResponse(transcript=transcript)
    except HTTPException:
        raise
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="We could not transcribe the audio.") from error
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


@router.post("/speak", response_model=SpeechResponse)
async def speak(request: SpeechRequest, _current_user: User = Depends(get_current_user)) -> SpeechResponse:
    settings = get_settings()
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text is required.")
    if len(request.text) > getattr(settings, "max_chat_message_chars", 8_000):
        raise HTTPException(status_code=422, detail="Text is too long.")

    try:
        audio_url = await synthesize_speech(request.text)
        return SpeechResponse(audio_url=audio_url)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="The voice response could not be generated.") from error


@router.get("/status", response_model=LiveVoiceStatusResponse)
async def status() -> LiveVoiceStatusResponse:
    return LiveVoiceStatusResponse(**live_voice_status())


@router.post("/realtime/session")
async def realtime_session(request: Request) -> PlainTextResponse:
    content_type = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    if content_type not in {"application/sdp", "text/plain"}:
        raise HTTPException(status_code=415, detail="Realtime session requires an SDP offer.")

    sdp_offer = _validate_sdp_offer(await request.body())
    # TODO: before production, require an authenticated user or a scoped public-session limiter for this POC route.
    try:
        sdp_answer = await create_realtime_sdp_answer(
            sdp_offer,
            safety_identifier="organicai-living-compass-poc",
        )
    except OpenAIRealtimeSessionError as error:
        raise HTTPException(status_code=error.status_code, detail=error.public_message) from error

    return PlainTextResponse(sdp_answer, media_type="application/sdp")


@router.post("/conversation-token", response_model=ConversationTokenResponse)
async def conversation_token(
    request: ConversationTokenRequest,
    current_user: User = Depends(get_current_user),
) -> ConversationTokenResponse:
    settings = get_settings()
    if not settings.elevenlabs_live_voice_enabled:
        raise HTTPException(status_code=409, detail="Live voice conversation is disabled.")

    try:
        check_token_rate_limit(current_user.id)
        token = await get_conversation_token(participant_name=current_user.id)
    except ElevenLabsConversationError as error:
        raise HTTPException(status_code=error.status_code, detail=error.public_message) from error

    return ConversationTokenResponse(
        token=token["token"],
        conversation_id=token["conversation_id"],
        server_location=client_server_location(settings),
        environment=settings.elevenlabs_environment,
    )


@router.get("/conversations/{elevenlabs_conversation_id}/latest-turn")
async def latest_live_voice_turn(
    elevenlabs_conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _ = db
    payload = get_latest_voice_turn(user_id=current_user.id, elevenlabs_conversation_id=elevenlabs_conversation_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="No live voice metadata is available for this conversation.")
    return payload
