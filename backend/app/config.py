from functools import lru_cache
from typing import Literal
from urllib.parse import urlparse

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DISABLED_PROVIDER_VALUES = {"", "disabled", "none", "null", "false", "off", "placeholder", "your-api-key"}


def active_provider_secret(value: str | None) -> str | None:
    clean = str(value or "").strip()
    if clean.lower() in DISABLED_PROVIDER_VALUES:
        return None
    return clean


def resolve_active_openai_api_key(settings: object) -> str | None:
    return active_provider_secret(getattr(settings, "openai_api_key", None))


class Settings(BaseSettings):
    app_name: str = "OrganicAI Compass"
    app_version: str = "0.9.0-rc.2"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    production_release_gate_enabled: bool = True
    remote_ci_validated: bool = False
    production_dns_validated: bool = False
    production_tls_validated: bool = False
    production_monitoring_validated: bool = False
    production_backup_restore_validated: bool = False
    production_rehearsal_mode: bool = False
    production_legal_privacy_review_approved: bool = False
    production_incident_response_owner: str = ""
    openai_acceptance_test_passed: bool = False
    elevenlabs_acceptance_test_passed: bool = False
    email_acceptance_test_passed: bool = False
    build_commit: str = "unavailable"
    build_timestamp: str = ""
    build_environment: str = ""
    staging_public_base_url: str = "http://127.0.0.1:18080"
    database_url: str = "sqlite:///./organicai.db"
    database_require_postgres_in_production: bool = True
    production_postgres_ssl_required: bool = True
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout_seconds: int = 30
    db_pool_recycle_seconds: int = 1800
    db_pool_pre_ping: bool = True
    db_connect_timeout_seconds: int = 10
    db_statement_timeout_ms: int = 30000
    db_lock_timeout_ms: int = 0
    db_idle_in_transaction_session_timeout_ms: int = 0
    db_application_name: str = "organicai-compass"
    db_auto_create_schema: bool = False
    db_auto_migrate: bool = False
    db_require_migration_head: bool = True
    db_backup_directory: str = "./backups/database"
    db_backup_retention_days: int = 30
    db_backup_compression: Literal["custom", "plain"] = "custom"
    db_migration_batch_size: int = 500
    db_migration_strict: bool = True
    db_migration_allow_partial: bool = False
    secret_key: str = "change-this-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    auth_cookie_name: str = "organicai_refresh"
    auth_cookie_secure: bool = False
    auth_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    auth_cookie_path: str = "/api/auth"
    auth_cookie_domain: str = ""
    auth_cookie_httponly: bool = True
    auth_require_origin_check: bool = True
    auth_require_verified_email: bool = False
    auth_max_failed_logins: int = 5
    auth_lockout_minutes: int = 15
    auth_session_limit_per_user: int = 10
    email_verification_expire_hours: int = 24
    password_reset_expire_minutes: int = 30
    password_hash_memory_cost_kib: int = 65536
    password_hash_time_cost: int = 3
    password_hash_parallelism: int = 4
    email_delivery_driver: Literal["disabled", "development-outbox", "smtp"] = "development-outbox"
    email_development_outbox_dir: str = "./tmp/email-outbox"
    privacy_export_directory: str = "./tmp/privacy-exports"
    privacy_export_expire_hours: int = 24
    privacy_account_deletion_grace_days: int = 7
    account_deletion_fixture_enabled: bool = False
    privacy_recent_auth_minutes: int = 10
    real_privacy_provider_tests_enabled: bool = False
    live_provider_validation_enabled: bool = False
    live_provider_write_validation_enabled: bool = False
    openai_live_canary_enabled: bool = False
    openai_training_opt_in_status: Literal["unknown", "opted-in", "not-opted-in", "manual-review-required"] = "unknown"
    openai_abuse_monitoring_mode: Literal["default", "modified-abuse-monitoring", "zero-data-retention", "unknown"] = "unknown"
    openai_data_residency_region: str = "unknown"
    openai_project_data_controls_verified: bool = False
    openai_data_controls_verified_at: str = ""
    openai_data_controls_verified_by: str = ""
    elevenlabs_provider_deletion_enabled: bool = False
    elevenlabs_real_deletion_test_enabled: bool = False
    elevenlabs_test_conversation_id: str = ""
    elevenlabs_privacy_configuration_apply_enabled: bool = False
    elevenlabs_retention_status: Literal["verified", "configured", "unknown", "manual-review-required", "not-applicable"] = "unknown"
    elevenlabs_audio_saving_status: Literal["verified", "configured", "unknown", "manual-review-required", "not-applicable"] = "unknown"
    elevenlabs_zero_retention_status: Literal["verified", "configured", "unknown", "manual-review-required", "not-applicable"] = "unknown"
    secret_rotation_openai_confirmed: bool = False
    secret_rotation_elevenlabs_confirmed: bool = False
    secret_rotation_postgres_confirmed: bool = False
    secret_rotation_application_confirmed: bool = False
    public_backend_url: str | None = None
    frontend_public_url: str = "http://127.0.0.1:5197"
    allowed_origins: str = "http://127.0.0.1:5197,http://localhost:5197,http://127.0.0.1:5190,http://localhost:5190"
    allowed_hosts: str = "127.0.0.1,localhost,testserver"
    trust_proxy_headers: bool = False
    integration_diagnostics_enabled: bool = True
    real_provider_tests_enabled: bool = False
    diagnostic_access_token: str | None = None
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
    researcher_identity: str = "placeholder"
    research_contact: str = "placeholder"
    research_storage_duration: str = "placeholder"
    research_study_version: str = "placeholder"
    research_consent_document_version: str = "placeholder"
    admin_emails: str = ""
    openai_transcription_model: str = "gpt-4o-mini-transcribe"
    openai_realtime_model: str = "gpt-realtime-2.1"
    openai_realtime_voice: str = "marin"
    openai_realtime_request_timeout_seconds: int = 20
    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str | None = None
    elevenlabs_model_id: str = "eleven_multilingual_v2"
    elevenlabs_api_base_url: str = "https://api.elevenlabs.io"
    elevenlabs_residency_mode: Literal["standard", "isolated-eu", "isolated-in", "isolated-sg"] = "standard"
    elevenlabs_agent_id: str | None = None
    elevenlabs_live_voice_enabled: bool = False
    elevenlabs_server_location: str = ""
    elevenlabs_environment: str = "production"
    elevenlabs_request_timeout_seconds: int = 15
    elevenlabs_custom_llm_enabled: bool = False
    elevenlabs_custom_llm_secret: str | None = None
    elevenlabs_legacy_voice_fallback_enabled: bool = True
    elevenlabs_post_call_webhook_enabled: bool = False
    elevenlabs_webhook_secret: str | None = None
    data_export_encryption_key: str | None = None
    deletion_ledger_hmac_key: str | None = None
    webhook_secret: str | None = None
    custom_llm_secret: str | None = None
    email_driver: Literal["disabled", "development-outbox", "smtp"] | None = None
    email_from_address: str = ""
    email_from_name: str = "OrganicAI Compass"
    email_reply_to: str = ""
    email_public_base_url: str = "http://127.0.0.1:5197"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str | None = None
    smtp_use_starttls: bool = True
    smtp_use_ssl: bool = False
    smtp_timeout_seconds: int = 15
    smtp_max_attempts: int = 2
    email_live_validation_enabled: bool = False
    email_test_recipient: str = ""
    frontend_url: str = "http://127.0.0.1:5197"
    rate_limit_driver: Literal["memory", "redis"] = "memory"
    redis_url: str | None = None
    rate_limit_policy_strict: bool = False
    max_request_body_bytes: int = 2_000_000
    max_audio_upload_bytes: int = 8_000_000
    max_audio_duration_seconds: int = 120
    max_chat_message_chars: int = 8_000
    max_context_field_chars: int = 1_500
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"
    log_conversation_content: bool = False
    hsts_enabled: bool = False
    csp_report_only: bool = True
    prometheus_metrics_enabled: bool = True
    otel_enabled: bool = False
    otel_service_name: str = "organicai-backend"
    otel_exporter_otlp_endpoint: str = ""
    otel_traces_sampler: str = "parentbased_traceidratio"
    otel_traces_sampler_arg: str = "0.1"
    otel_exporter_otlp_insecure: bool = True
    sentry_enabled: bool = False
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
    labour_market_provider: str = "demo"
    labour_market_live_enabled: bool = False
    nav_stilling_feed_enabled: bool = False
    nav_stilling_feed_base_url: str = "https://pam-stilling-feed.nav.no"
    nav_stilling_feed_token: str | None = None
    nav_stilling_feed_consumer_id: str | None = None
    nav_stilling_feed_request_timeout_seconds: int = 15
    nav_stilling_feed_sync_batch_size: int = 250
    nav_stilling_feed_cache_ttl_seconds: int = 3600
    esco_provider: str = "disabled"
    esco_base_url: str = "https://ec.europa.eu/esco/api"
    esco_cache_ttl_seconds: int = 86400
    interview_voice_enabled: bool = False
    interview_voice_provider: str = "elevenlabs"
    interview_voice_default_language: str = "en"
    interview_voice_session_timeout_seconds: int = 1800
    interview_voice_max_session_minutes: int = 30
    interview_voice_transcript_retention_enabled: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("allowed_origins", "allowed_hosts")
    @classmethod
    def validate_csv_not_empty(cls, value: str) -> str:
        if not value.strip():
            return ""
        return ",".join(part.strip() for part in value.split(",") if part.strip())

    @field_validator("max_request_body_bytes", "max_audio_upload_bytes", "max_chat_message_chars", "max_context_field_chars")
    @classmethod
    def validate_positive_limits(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Runtime limits must be positive integers.")
        return value

    @field_validator(
        "db_pool_size",
        "db_max_overflow",
        "db_pool_timeout_seconds",
        "db_pool_recycle_seconds",
        "db_connect_timeout_seconds",
        "db_statement_timeout_ms",
        "db_lock_timeout_ms",
        "db_idle_in_transaction_session_timeout_ms",
        "db_backup_retention_days",
        "db_migration_batch_size",
        "refresh_token_expire_days",
        "auth_max_failed_logins",
        "auth_lockout_minutes",
        "auth_session_limit_per_user",
        "email_verification_expire_hours",
        "password_reset_expire_minutes",
        "password_hash_memory_cost_kib",
        "password_hash_time_cost",
        "password_hash_parallelism",
        "privacy_export_expire_hours",
        "privacy_account_deletion_grace_days",
        "privacy_recent_auth_minutes",
        "smtp_port",
        "smtp_timeout_seconds",
        "smtp_max_attempts",
    )
    @classmethod
    def validate_database_limits(cls, value: int) -> int:
        if value < 0:
            raise ValueError("Database limits must not be negative.")
        return value

    @field_validator("max_audio_duration_seconds")
    @classmethod
    def validate_audio_duration(cls, value: int) -> int:
        if value <= 0 or value > 3600:
            raise ValueError("MAX_AUDIO_DURATION_SECONDS must be between 1 and 3600.")
        return value

    @model_validator(mode="after")
    def validate_demo(self) -> "Settings":
        if self.app_env.lower() == "production" and self.demo_mode is None:
            self.demo_account_enabled = False
        if self.demo_mode is not None:
            self.demo_account_enabled = self.demo_mode
        if self.email_driver:
            self.email_delivery_driver = self.email_driver
        if self.demo_email:
            self.demo_user_email = self.demo_email
        if self.demo_password:
            self.demo_user_password = self.demo_password
        if self.demo_account_enabled and not self.demo_user_password.strip():
            raise ValueError("DEMO_USER_PASSWORD must not be empty when demo mode is enabled")
        if self.frontend_url == "http://localhost:5173":
            self.frontend_url = self.frontend_public_url
        if self.app_env == "production" and self.hsts_enabled:
            for value in [self.public_backend_url, self.frontend_public_url]:
                if value and urlparse(value).scheme != "https":
                    raise ValueError("HSTS requires HTTPS public URLs in production.")
        return self

    @property
    def allowed_origin_list(self) -> list[str]:
        return [part.strip() for part in self.allowed_origins.split(",") if part.strip()]

    @property
    def allowed_host_list(self) -> list[str]:
        return [part.strip() for part in self.allowed_hosts.split(",") if part.strip()]

    @property
    def public_custom_llm_url(self) -> str | None:
        if not self.public_backend_url:
            return None
        return f"{self.public_backend_url.rstrip('/')}/api/elevenlabs/v1/chat/completions"

    @property
    def active_openai_api_key(self) -> str | None:
        return resolve_active_openai_api_key(self)


@lru_cache
def get_settings() -> Settings:
    return Settings()
