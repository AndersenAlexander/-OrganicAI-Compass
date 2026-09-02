from __future__ import annotations

from app.config import get_settings
from app.db.url import parse_database_url
from app.services.secret_readiness import audit_secret_readiness


def release_readiness_summary() -> dict:
    settings = get_settings()
    secret_report = audit_secret_readiness(settings)
    database = parse_database_url(settings.database_url)
    results = []

    def add(category: str, status: str, summary: str):
        results.append({"category": category, "status": status, "summary": summary})

    fail_closed = settings.app_env in {"staging", "production"}
    add("database", "passed" if database.dialect in {"postgresql", "postgres"} else "blocked" if fail_closed else "warning", "PostgreSQL is required for production release.")
    add("authentication", "blocked" if fail_closed and settings.secret_key == "change-this-secret-key" else "warning" if settings.secret_key == "change-this-secret-key" else "passed", "JWT secret must be non-default.")
    add("privacy", "blocked" if fail_closed and (not settings.data_export_encryption_key or not settings.deletion_ledger_hmac_key) else "warning" if (not settings.data_export_encryption_key or not settings.deletion_ledger_hmac_key) else "passed", "Export and deletion ledger keys are required for production.")
    add("OpenAI", "warning" if settings.openai_api_key else "manual-action-required", "Provider data controls require manual attestation.")
    add("ElevenLabs", "warning" if settings.elevenlabs_api_key else "manual-action-required", "Voice provider privacy settings require verification.")
    add("email", "blocked" if fail_closed and settings.email_delivery_driver != "smtp" else "warning", "Production email requires SMTP with TLS and verified sender.")
    add("secrets", "blocked" if fail_closed and secret_report["blockingFindingCount"] else "manual-action-required", "Previous exposure remains rotation-required until attested.")
    add("workers", "warning", "Operational workers are implemented but destructive jobs remain configuration-gated.")
    add("backup", "warning", "Backup evidence must be checked before each active migration.")
    add("logging", "passed" if not settings.log_conversation_content else "blocked", "Conversation content logging must remain disabled.")
    add("frontend", "warning", "Privacy Center must be smoke-tested in deployed environment.")
    add("legal-manual", "manual-action-required", "Technical draft — requires legal and operational review before public deployment.")
    blocking = [row for row in results if row["status"] == "blocked"]
    return {
        "formatVersion": 1,
        "environment": settings.app_env,
        "productionReleaseGateEnabled": settings.production_release_gate_enabled,
        "status": "blocked" if blocking else "manual-action-required",
        "blockingFindingCount": len(blocking),
        "results": results,
        "secretValuesIncluded": False,
    }
