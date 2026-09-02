from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Literal

from app.config import Settings, active_provider_secret, get_settings

SecretStatus = Literal["missing", "placeholder", "configured-unverified", "configured-verified", "rotation-required"]

PLACEHOLDERS = {
    "",
    "change-this-secret-key",
    "replace-with-a-generated-local-password",
    "replace-with-a-local-demo-password",
    "your-api-key",
    "placeholder",
    "<postgresql-connection-string-for-organicai_app>",
}

SECRET_SPECS = {
    "OPENAI_API_KEY": ("openai_api_key", "secret_rotation_openai_confirmed"),
    "ELEVENLABS_API_KEY": ("elevenlabs_api_key", "secret_rotation_elevenlabs_confirmed"),
    "ELEVENLABS_AGENT_ID": ("elevenlabs_agent_id", "secret_rotation_elevenlabs_confirmed"),
    "ELEVENLABS_WEBHOOK_SECRET": ("elevenlabs_webhook_secret", None),
    "DATABASE_URL": ("database_url", "secret_rotation_postgres_confirmed"),
    "SECRET_KEY": ("secret_key", "secret_rotation_application_confirmed"),
    "CUSTOM_LLM_SECRET": ("custom_llm_secret", None),
    "WEBHOOK_SECRET": ("webhook_secret", None),
    "DATA_EXPORT_ENCRYPTION_KEY": ("data_export_encryption_key", None),
    "DELETION_LEDGER_HMAC_KEY": ("deletion_ledger_hmac_key", None),
    "EMAIL_PROVIDER_SECRET": ("smtp_password", None),
    "SMTP_PASSWORD": ("smtp_password", None),
}

CRITICAL_PRODUCTION = {"DATABASE_URL", "SECRET_KEY", "DATA_EXPORT_ENCRYPTION_KEY", "DELETION_LEDGER_HMAC_KEY"}
PREVIOUSLY_EXPOSED = {"OPENAI_API_KEY", "ELEVENLABS_API_KEY", "DATABASE_URL", "SECRET_KEY"}


@dataclass(frozen=True)
class SecretReadinessItem:
    name: str
    status: SecretStatus
    configured: bool
    safe_fingerprint: str | None
    rotation_attested: bool | None
    production_critical: bool
    blocking: bool


def safe_fingerprint(value: str | None) -> str | None:
    clean = str(value or "").strip()
    if not clean:
        return None
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()[:12]


def _is_placeholder(value: str | None) -> bool:
    clean = str(value or "").strip()
    if clean in PLACEHOLDERS:
        return True
    return clean.startswith("<") and clean.endswith(">")


def classify_secret(name: str, settings: Settings | None = None) -> SecretReadinessItem:
    settings = settings or get_settings()
    attr, attestation_attr = SECRET_SPECS[name]
    value = getattr(settings, attr, None)
    configured = active_provider_secret(value) is not None
    attested = bool(getattr(settings, attestation_attr)) if attestation_attr else None
    if not configured:
        status: SecretStatus = "missing"
    elif _is_placeholder(str(value)):
        status = "placeholder"
    elif name in PREVIOUSLY_EXPOSED and attestation_attr and not attested:
        status = "rotation-required"
    elif attested:
        status = "configured-verified"
    else:
        status = "configured-unverified"
    production_critical = name in CRITICAL_PRODUCTION
    blocking = settings.app_env == "production" and production_critical and status in {"missing", "placeholder", "rotation-required"}
    return SecretReadinessItem(
        name=name,
        status=status,
        configured=configured,
        safe_fingerprint=safe_fingerprint(str(value)) if configured and not _is_placeholder(str(value)) else None,
        rotation_attested=attested,
        production_critical=production_critical,
        blocking=blocking,
    )


def audit_secret_readiness(settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    items = [classify_secret(name, settings) for name in SECRET_SPECS]
    return {
        "formatVersion": 1,
        "environment": settings.app_env,
        "blockingFindingCount": sum(1 for item in items if item.blocking),
        "defaultSecretsRejected": any(item.status == "placeholder" for item in items),
        "rotationRequiredCount": sum(1 for item in items if item.status == "rotation-required"),
        "items": [asdict(item) for item in items],
        "secretValuesIncluded": False,
    }
