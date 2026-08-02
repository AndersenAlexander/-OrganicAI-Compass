from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "OrganicAI Compass"
    app_env: str = "development"
    database_url: str = "sqlite:///./organicai.db"
    secret_key: str = "change-this-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    rag_top_k: int = 4
    openai_transcription_model: str = "gpt-4o-mini-transcribe"
    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str | None = None
    elevenlabs_model_id: str = "eleven_multilingual_v2"
    frontend_url: str = "http://localhost:5173"
    demo_mode: bool = False
    demo_email: str = "demo@organicai.local"
    demo_password: str = "OrganicAI-Demo-2026!"
    demo_reset_on_startup: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
