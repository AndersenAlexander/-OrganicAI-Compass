from __future__ import annotations

import ipaddress
from datetime import datetime
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from app.config import Settings, active_provider_secret, get_settings, resolve_active_openai_api_key
from app.core.time import utc_now
from app.db.url import parse_database_url


CheckStatus = Literal["ok", "warning", "error", "disabled"]


class ConfigurationCheck(BaseModel):
    key: str
    category: str
    status: CheckStatus
    message: str
    required_in_production: bool
    secret: bool = False


class RuntimeConfigurationReport(BaseModel):
    environment: str
    ready: bool
    checks: list[ConfigurationCheck]
    generated_at: datetime = Field(default_factory=utc_now)


class BlockingIssue(BaseModel):
    code: str
    message: str


PLACEHOLDER_VALUES = {
    "",
    "change-this-secret-key",
    "replace-with-a-local-demo-password",
    "changeme",
    "change-me",
    "placeholder",
    "secret",
    "server-secret",
    "your-secret",
    "your-api-key",
    "agent_...",
}


def csv_items(value: str | None) -> list[str]:
    return [part.strip() for part in str(value or "").split(",") if part.strip()]


def is_placeholder(value: str | None) -> bool:
    if value is None:
        return True
    clean = str(value).strip()
    if clean.lower() in PLACEHOLDER_VALUES:
        return True
    return "replace" in clean.lower() or clean.endswith("...")


def is_weak_secret(value: str | None, *, min_length: int = 32) -> bool:
    if value is None:
        return True
    return is_placeholder(value) or len(str(value).strip()) < min_length


def parsed_url(value: str | None):
    if not value:
        return None
    parsed = urlparse(str(value))
    if not parsed.scheme or not parsed.netloc:
        return None
    return parsed


def is_private_or_local_url(value: str | None) -> bool:
    parsed = parsed_url(value)
    if parsed is None:
        return True
    host = (parsed.hostname or "").lower()
    if host in {"localhost", "127.0.0.1", "::1"}:
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local


def is_https_url(value: str | None) -> bool:
    parsed = parsed_url(value)
    return bool(parsed and parsed.scheme == "https")


def contains_mask_marker(value: str | None) -> bool:
    return "***" in str(value or "")


def postgres_ssl_mode(database_url: str | None) -> str:
    if not database_url:
        return ""
    try:
        url = make_url(database_url)
    except ArgumentError:
        return ""
    value = url.query.get("sslmode")
    return str(value or "").lower()


def production_url_status(value: str | None) -> CheckStatus:
    if not value or contains_mask_marker(value):
        return "error"
    if is_private_or_local_url(value) or not is_https_url(value):
        return "error"
    return "ok"


def custom_llm_public_url(settings: Settings) -> str | None:
    public_backend_url = getattr(settings, "public_backend_url", None)
    if not public_backend_url:
        return None
    return f"{public_backend_url.rstrip('/')}/api/elevenlabs/v1/chat/completions"


def elevenlabs_residency_issue(settings: Settings) -> BlockingIssue | None:
    residency_mode = getattr(settings, "elevenlabs_residency_mode", "standard")
    api_base_url = getattr(settings, "elevenlabs_api_base_url", "https://api.elevenlabs.io")
    if residency_mode == "standard":
        return None
    if not api_base_url or api_base_url.rstrip("/") == "https://api.elevenlabs.io":
        return BlockingIssue(
            code="ELEVENLABS_ISOLATED_BASE_URL_REQUIRED",
            message="Isolated ElevenLabs residency requires an explicit API base URL.",
        )
    return None


def public_backend_issues(settings: Settings) -> list[BlockingIssue]:
    issues: list[BlockingIssue] = []
    if getattr(settings, "elevenlabs_custom_llm_enabled", False):
        public_backend_url = getattr(settings, "public_backend_url", None)
        if not public_backend_url:
            issues.append(
                BlockingIssue(
                    code="PUBLIC_BACKEND_URL_MISSING",
                    message="Custom LLM requires PUBLIC_BACKEND_URL.",
                )
            )
        elif is_private_or_local_url(public_backend_url):
            issues.append(
                BlockingIssue(
                    code="PUBLIC_BACKEND_URL_LOCAL",
                    message="Custom LLM requires a public HTTPS backend URL.",
                )
            )
        elif getattr(settings, "app_env", "development") == "production" and not is_https_url(public_backend_url):
            issues.append(
                BlockingIssue(
                    code="PUBLIC_BACKEND_URL_NOT_HTTPS",
                    message="Production Custom LLM requires an HTTPS backend URL.",
                )
            )
    return issues


def elevenlabs_blocking_issues(settings: Settings) -> list[BlockingIssue]:
    issues: list[BlockingIssue] = []
    if getattr(settings, "elevenlabs_live_voice_enabled", False):
        if not getattr(settings, "elevenlabs_api_key", None):
            issues.append(BlockingIssue(code="VOICE_API_KEY_NOT_CONFIGURED", message="ElevenLabs API key is not configured."))
        if not getattr(settings, "elevenlabs_agent_id", None) or is_placeholder(getattr(settings, "elevenlabs_agent_id", None)):
            issues.append(BlockingIssue(code="VOICE_AGENT_NOT_CONFIGURED", message="ElevenLabs Agent ID is not configured."))
        residency_issue = elevenlabs_residency_issue(settings)
        if residency_issue:
            issues.append(residency_issue)
    if getattr(settings, "elevenlabs_custom_llm_enabled", False):
        if not getattr(settings, "elevenlabs_custom_llm_secret", None) or is_placeholder(getattr(settings, "elevenlabs_custom_llm_secret", None)):
            issues.append(BlockingIssue(code="CUSTOM_LLM_SECRET_NOT_CONFIGURED", message="Custom LLM secret is not configured."))
        issues.extend(public_backend_issues(settings))
    return issues


def check_runtime_configuration(settings: Settings | None = None) -> RuntimeConfigurationReport:
    settings = settings or get_settings()
    checks: list[ConfigurationCheck] = []

    def add(
        key: str,
        category: str,
        status: CheckStatus,
        message: str,
        required_in_production: bool = False,
        secret: bool = False,
    ) -> None:
        checks.append(
            ConfigurationCheck(
                key=key,
                category=category,
                status=status,
                message=message,
                required_in_production=required_in_production,
                secret=secret,
            )
        )

    add("APP_ENV", "runtime", "ok", f"Runtime environment is {settings.app_env}.", True)
    add("APP_VERSION", "runtime", "ok" if settings.app_version else "warning", "Application version is configured." if settings.app_version else "Application version is not set.", False)

    database_info = parse_database_url(settings.database_url)
    if contains_mask_marker(settings.database_url):
        add("DATABASE_URL", "database", "error", "Database URL contains a masked password marker.", True, True)
    elif not settings.database_url:
        add("DATABASE_URL", "database", "error", "Database URL is missing.", True, True)
    elif database_info.dialect == "invalid":
        add("DATABASE_URL", "database", "error", "Database URL is invalid.", True, True)
    elif (
        settings.app_env in {"staging", "production"}
        and settings.database_require_postgres_in_production
        and database_info.dialect not in {"postgresql", "postgres"}
    ):
        add("DATABASE_URL", "database", "error", f"{settings.app_env.title()} requires PostgreSQL persistence.", True, True)
    elif settings.app_env == "production" and database_info.dialect == "sqlite":
        add("DATABASE_URL", "database", "warning", "SQLite is configured in production.", True, True)
    else:
        add("DATABASE_URL", "database", "ok", f"Database dialect is {database_info.dialect}.", True, True)

    add(
        "DATABASE_REQUIRE_POSTGRES_IN_PRODUCTION",
        "database",
        "ok" if settings.database_require_postgres_in_production else "warning",
        "Production PostgreSQL requirement is enabled." if settings.database_require_postgres_in_production else "Production PostgreSQL requirement is disabled.",
        True,
    )
    if settings.app_env == "production" and database_info.dialect in {"postgresql", "postgres"}:
        ssl_mode = postgres_ssl_mode(settings.database_url)
        ssl_ok = not settings.production_postgres_ssl_required or ssl_mode in {"require", "verify-ca", "verify-full"}
        add(
            "PRODUCTION_POSTGRES_SSL_REQUIRED",
            "database",
            "ok" if ssl_ok else "error",
            "Production PostgreSQL SSL mode is acceptable." if ssl_ok else "Production PostgreSQL requires sslmode=require, verify-ca, or verify-full.",
            True,
        )
    add(
        "DB_AUTO_CREATE_SCHEMA",
        "database",
        "error" if settings.app_env == "production" and settings.db_auto_create_schema else "warning" if settings.db_auto_create_schema else "ok",
        "Automatic schema creation is disabled." if not settings.db_auto_create_schema else "Automatic schema creation is enabled.",
        True,
    )
    add(
        "DB_AUTO_MIGRATE",
        "database",
        "error" if settings.app_env == "production" and settings.db_auto_migrate else "warning" if settings.db_auto_migrate else "ok",
        "Automatic migrations are disabled." if not settings.db_auto_migrate else "Automatic migrations are enabled.",
        True,
    )
    add(
        "DB_REQUIRE_MIGRATION_HEAD",
        "database",
        "ok" if settings.db_require_migration_head else "warning",
        "Readiness requires Alembic head." if settings.db_require_migration_head else "Readiness does not require Alembic head.",
        True,
    )

    if settings.app_env in {"staging", "production"} and is_weak_secret(settings.secret_key):
        add("SECRET_KEY", "auth", "error", "JWT secret is missing, weak, or uses a placeholder.", True, True)
    elif is_weak_secret(settings.secret_key):
        add("SECRET_KEY", "auth", "warning", "JWT secret should be replaced before production.", True, True)
    else:
        add("SECRET_KEY", "auth", "ok", "JWT secret is configured.", True, True)

    openai_enabled = bool(resolve_active_openai_api_key(settings))
    add("OPENAI_API_KEY", "openai", "ok" if openai_enabled else "disabled", "OpenAI key is configured." if openai_enabled else "OpenAI provider is disabled.", False, True)
    if settings.app_env == "staging" and openai_enabled and not settings.live_provider_validation_enabled:
        add("OPENAI_STAGING_DISABLED", "openai", "error", "Staging external providers must remain disabled unless explicitly approved.", True, True)

    if contains_mask_marker(settings.elevenlabs_api_base_url):
        add("ELEVENLABS_API_BASE_URL", "elevenlabs", "error", "ElevenLabs API base URL contains a masked marker.", True)
    elif settings.app_env == "production" and (settings.elevenlabs_live_voice_enabled or settings.elevenlabs_custom_llm_enabled) and not is_https_url(settings.elevenlabs_api_base_url):
        add("ELEVENLABS_API_BASE_URL", "elevenlabs", "error", "Production ElevenLabs API base URL must use HTTPS.", True)
    else:
        add("ELEVENLABS_API_BASE_URL", "elevenlabs", "ok", "ElevenLabs API base URL uses an acceptable scheme.", False)

    if settings.elevenlabs_live_voice_enabled:
        issues = elevenlabs_blocking_issues(settings)
        add(
            "ELEVENLABS_LIVE_VOICE_ENABLED",
            "elevenlabs",
            "error" if any(issue.code.startswith("VOICE_") or issue.code.startswith("ELEVENLABS_") for issue in issues) else "ok",
            "ElevenLabs live voice is enabled.",
            True,
        )
    else:
        add("ELEVENLABS_LIVE_VOICE_ENABLED", "elevenlabs", "disabled", "ElevenLabs live voice is disabled.", False)

    add(
        "ELEVENLABS_RESIDENCY_MODE",
        "elevenlabs",
        "error" if elevenlabs_residency_issue(settings) else "ok",
        f"ElevenLabs residency mode is {settings.elevenlabs_residency_mode}.",
        True,
    )
    elevenlabs_key_configured = active_provider_secret(settings.elevenlabs_api_key) is not None
    elevenlabs_agent_configured = active_provider_secret(settings.elevenlabs_agent_id) is not None and not is_placeholder(settings.elevenlabs_agent_id)
    add("ELEVENLABS_API_KEY", "elevenlabs", "ok" if elevenlabs_key_configured else "disabled", "ElevenLabs API key is configured." if elevenlabs_key_configured else "ElevenLabs API key is not configured.", settings.elevenlabs_live_voice_enabled, True)
    add("ELEVENLABS_AGENT_ID", "elevenlabs", "ok" if elevenlabs_agent_configured else "disabled", "ElevenLabs Agent ID is configured." if elevenlabs_agent_configured else "ElevenLabs Agent ID is not configured.", settings.elevenlabs_live_voice_enabled, True)

    if settings.elevenlabs_custom_llm_enabled:
        custom_issues = public_backend_issues(settings)
        secret_ok = bool(settings.elevenlabs_custom_llm_secret and not is_placeholder(settings.elevenlabs_custom_llm_secret))
        add(
            "ELEVENLABS_CUSTOM_LLM",
            "custom_llm",
            "error" if custom_issues or not secret_ok else "ok",
            "Custom LLM integration is enabled.",
            True,
        )
    else:
        add("ELEVENLABS_CUSTOM_LLM", "custom_llm", "disabled", "Custom LLM integration is disabled.", False)

    if contains_mask_marker(settings.public_backend_url):
        add("PUBLIC_BACKEND_URL", "network", "error", "Public backend URL contains a masked marker.", True)
    elif not settings.public_backend_url:
        add("PUBLIC_BACKEND_URL", "network", "warning" if settings.app_env != "production" else "error", "Public backend URL is not set.", settings.app_env == "production")
    elif settings.app_env == "production" and (is_private_or_local_url(settings.public_backend_url) or not is_https_url(settings.public_backend_url)):
        add("PUBLIC_BACKEND_URL", "network", "error", "Production backend URL must be public HTTPS.", True)
    else:
        add("PUBLIC_BACKEND_URL", "network", "ok", "Public backend URL is configured.", settings.app_env == "production")

    for key, value in [
        ("FRONTEND_PUBLIC_URL", settings.frontend_public_url),
        ("EMAIL_PUBLIC_BASE_URL", settings.email_public_base_url),
    ]:
        if settings.app_env == "production":
            status = production_url_status(value)
            add(
                key,
                "network" if key == "FRONTEND_PUBLIC_URL" else "email",
                status,
                f"{key} is configured for public HTTPS production use." if status == "ok" else f"{key} must be a public HTTPS URL in production and must not contain masked markers.",
                True,
            )
        elif contains_mask_marker(value):
            add(key, "network" if key == "FRONTEND_PUBLIC_URL" else "email", "error", f"{key} contains a masked marker.", False)

    origins = csv_items(settings.allowed_origins)
    if not origins or "*" in origins:
        add("ALLOWED_ORIGINS", "cors", "error", "Allowed origins must be an explicit allowlist.", True)
    elif settings.app_env == "production" and any(is_private_or_local_url(origin) or not is_https_url(origin) or contains_mask_marker(origin) for origin in origins):
        add("ALLOWED_ORIGINS", "cors", "error", "Production allowed origins must be public HTTPS origins and must not include localhost, private IPs, wildcards, or masked markers.", True)
    else:
        add("ALLOWED_ORIGINS", "cors", "ok", "Allowed origins are configured as an explicit allowlist.", True)
    if settings.app_env == "staging" and settings.staging_public_base_url not in origins:
        add("STAGING_PUBLIC_BASE_URL", "cors", "error", "Staging public origin must be explicitly allowed.", True)

    hosts = csv_items(settings.allowed_hosts)
    if not hosts or "*" in hosts:
        add("ALLOWED_HOSTS", "hosts", "error", "Allowed hosts must be an explicit allowlist.", True)
    elif settings.app_env == "production" and any(host in {"localhost", "127.0.0.1", "::1"} or contains_mask_marker(host) for host in hosts):
        add("ALLOWED_HOSTS", "hosts", "error", "Production trusted hosts must not include localhost, loopback, wildcards, or masked markers.", True)
    else:
        add("ALLOWED_HOSTS", "hosts", "ok", "Allowed hosts are configured as an explicit allowlist.", True)

    if settings.app_env == "production":
        add(
            "AUTH_COOKIE_SECURE",
            "auth",
            "ok" if settings.auth_cookie_secure else "error",
            "Refresh cookie Secure flag is enabled." if settings.auth_cookie_secure else "Refresh cookie Secure flag must be enabled in production.",
            True,
        )
        add(
            "AUTH_COOKIE_HTTPONLY",
            "auth",
            "ok" if settings.auth_cookie_httponly else "error",
            "Refresh cookie HttpOnly flag is enabled." if settings.auth_cookie_httponly else "Refresh cookie HttpOnly flag must remain enabled.",
            True,
        )
        add(
            "AUTH_COOKIE_SAMESITE",
            "auth",
            "ok" if settings.auth_cookie_samesite in {"lax", "strict"} else "error",
            "Refresh cookie SameSite policy is acceptable." if settings.auth_cookie_samesite in {"lax", "strict"} else "Production SameSite=None requires explicit cross-site review and is blocked by default.",
            True,
        )

        email_rehearsal_disabled = bool(getattr(settings, "production_rehearsal_mode", False)) and settings.email_delivery_driver == "disabled"
        email_configured = (
            settings.email_delivery_driver == "smtp"
            and bool(settings.smtp_host and settings.email_from_address)
            and is_https_url(settings.email_public_base_url)
            and (settings.smtp_use_ssl or settings.smtp_use_starttls)
            and not contains_mask_marker(settings.smtp_host)
            and not contains_mask_marker(settings.email_from_address)
            and (not settings.smtp_username or bool(settings.smtp_password and not is_placeholder(settings.smtp_password)))
        )
        add(
            "EMAIL_DELIVERY_DRIVER",
            "email",
            "ok" if email_configured or email_rehearsal_disabled else "error",
            (
                "Production email is configured with SMTP, TLS, sender, HTTPS public URL, and required credential material."
                if email_configured
                else "Production rehearsal mode uses disabled email delivery to prevent real sends."
                if email_rehearsal_disabled
                else "Production email requires SMTP with TLS, sender address, HTTPS public URL, and required credential material."
            ),
            True,
            True,
        )
        add(
            "SMTP_TIMEOUT_SECONDS",
            "email",
            "ok" if 1 <= settings.smtp_timeout_seconds <= 60 else "error",
            "SMTP timeout is bounded." if 1 <= settings.smtp_timeout_seconds <= 60 else "SMTP timeout must be between 1 and 60 seconds.",
            True,
        )
        add(
            "SMTP_MAX_ATTEMPTS",
            "email",
            "ok" if 1 <= settings.smtp_max_attempts <= 3 else "error",
            "SMTP retry limit is bounded." if 1 <= settings.smtp_max_attempts <= 3 else "SMTP retry attempts must be between 1 and 3.",
            True,
        )

        add(
            "HSTS_ENABLED",
            "network",
            "ok" if settings.hsts_enabled else "warning",
            "HSTS is enabled." if settings.hsts_enabled else "HSTS should be enabled only after HTTPS deployment and rollback window are verified.",
            True,
        )
        add(
            "CSP_REPORT_ONLY",
            "network",
            "warning" if settings.csp_report_only else "ok",
            "CSP is still report-only." if settings.csp_report_only else "CSP enforcement is enabled.",
            True,
        )

    add("MAX_REQUEST_BODY_BYTES", "limits", "ok", "Request body limit is configured.", True)
    add("MAX_AUDIO_UPLOAD_BYTES", "limits", "ok", "Audio upload limit is configured.", True)
    add("LOG_FORMAT", "logging", "ok", f"Log format is {settings.log_format}.", False)
    if settings.app_env == "staging" and settings.log_format != "json":
        add("LOG_FORMAT_STAGING", "logging", "error", "Staging requires JSON logs.", True)
    if settings.app_env == "staging" and settings.db_auto_create_schema:
        add("DB_AUTO_CREATE_SCHEMA_STAGING", "database", "error", "Staging must not auto-create schema.", True)
    if settings.app_env == "staging" and settings.db_auto_migrate:
        add("DB_AUTO_MIGRATE_STAGING", "database", "error", "Staging migrations must run only through the migrator.", True)
    if settings.app_env == "staging" and is_weak_secret(settings.data_export_encryption_key):
        add("DATA_EXPORT_ENCRYPTION_KEY", "privacy", "error", "Staging export encryption key is missing or weak.", True, True)
    if settings.app_env == "staging" and is_weak_secret(settings.deletion_ledger_hmac_key):
        add("DELETION_LEDGER_HMAC_KEY", "privacy", "error", "Staging deletion ledger key is missing or weak.", True, True)
    if settings.app_env == "staging" and settings.email_delivery_driver == "development-outbox":
        add("EMAIL_DELIVERY_DRIVER", "email", "error", "Staging must not use development outbox unless a separate exception is documented.", True)
    add("RATE_LIMIT_DRIVER", "rate_limit", "ok" if settings.rate_limit_driver == "memory" or settings.redis_url else "warning", "Rate limiting is configured.", True)
    add("RESEARCH_EXPORT_ENABLED", "research", "ok" if settings.research_export_enabled else "disabled", "Research export is enabled." if settings.research_export_enabled else "Research export is disabled.", False)
    add("DEMO_ACCOUNT_ENABLED", "demo", "ok" if settings.demo_account_enabled else "disabled", "Demo account is enabled." if settings.demo_account_enabled else "Demo account is disabled.", False)

    ready = not any(check.status == "error" for check in checks)
    return RuntimeConfigurationReport(environment=settings.app_env, ready=ready, checks=checks)


def failed_required_categories(report: RuntimeConfigurationReport) -> list[str]:
    return sorted({check.category for check in report.checks if check.status == "error"})


def assert_startup_configuration(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    if settings.app_env not in {"staging", "production"}:
        return
    report = check_runtime_configuration(settings)
    errors = [check for check in report.checks if check.status == "error" and check.required_in_production]
    if errors:
        categories = ", ".join(sorted({item.category for item in errors}))
        raise RuntimeError(f"Production configuration is not ready: {categories}.")


def sanitized_report_dict(report: RuntimeConfigurationReport) -> dict[str, Any]:
    return report.model_dump(mode="json")
