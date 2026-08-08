from functools import lru_cache

from pydantic import model_validator
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
    rag_min_relevance_score: float = 0.10
    rag_min_context_chunks: int = 2
    rag_max_context_chunks: int = 4
    rag_log_runs: bool = True
    rag_store_query_text: bool = True
    rag_feedback_enabled: bool = True
    rag_injection_detection_enabled: bool = True
    research_export_enabled: bool = False
    admin_emails: str = ""
    openai_transcription_model: str = "gpt-4o-mini-transcribe"
    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str | None = None
    elevenlabs_model_id: str = "eleven_multilingual_v2"
    frontend_url: str = "http://localhost:5173"
    demo_account_enabled: bool = True
    demo_user_email: str = "demo@organicai.local"
    demo_user_password: str = "replace-with-a-local-demo-password"
    demo_user_display_name: str = "OrganicAI Demo"
    demo_reset_on_login: bool = False
    demo_dataset_version: int = 1
    demo_login_rate_limit: int = 10
    # Backward-compatible keys for existing local environments.
    demo_mode: bool | None = None
    demo_email: str | None = None
    demo_password: str | None = None
    demo_reset_on_startup: bool = False
    learning_resource_external_search_enabled: bool = False
    youtube_api_enabled: bool = False
    youtube_api_key: str | None = None
    youtube_region_code: str = "US"
    youtube_default_language: str = "en"
    udemy_api_enabled: bool = False
    udemy_client_id: str | None = None
    udemy_client_secret: str | None = None
    udemy_affiliate_id: str | None = None
    learning_resource_cache_ttl_seconds: int = 86400
    learning_resource_request_timeout_seconds: int = 10

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def validate_demo(self) -> "Settings":
        if self.app_env.lower() == "production" and self.demo_mode is None:
            self.demo_account_enabled = False
        if self.demo_mode is not None:
            self.demo_account_enabled = self.demo_mode
        if self.demo_email:
            self.demo_user_email = self.demo_email
        if self.demo_password:
            self.demo_user_password = self.demo_password
        if self.demo_account_enabled and not self.demo_user_password.strip():
            raise ValueError("DEMO_USER_PASSWORD must not be empty when demo mode is enabled")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
