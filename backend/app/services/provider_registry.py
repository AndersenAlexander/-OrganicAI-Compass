from __future__ import annotations

from datetime import datetime
from app.core.time import utc_now_naive

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import active_provider_secret, get_settings
from app.models.provider_operations import EmailDeliveryEvent, ProviderVerificationRun


def _latest_provider_run(db: Session, provider: str) -> ProviderVerificationRun | None:
    return db.scalar(select(ProviderVerificationRun).where(ProviderVerificationRun.provider == provider).order_by(ProviderVerificationRun.started_at.desc()))


def _latest_email_event(db: Session) -> EmailDeliveryEvent | None:
    return db.scalar(select(EmailDeliveryEvent).order_by(EmailDeliveryEvent.created_at.desc()))


def provider_registry(db: Session) -> list[dict]:
    settings = get_settings()
    rows = []
    for provider, configured in [
        ("OpenAI", active_provider_secret(settings.openai_api_key) is not None),
        ("ElevenLabs", active_provider_secret(settings.elevenlabs_api_key) is not None and active_provider_secret(settings.elevenlabs_agent_id) is not None),
    ]:
        latest = _latest_provider_run(db, provider)
        rows.append(
            {
                "provider": provider,
                "capability": "AI generation" if provider == "OpenAI" else "Live voice",
                "configured": configured,
                "connectivity": latest.status if latest else ("configured-unverified" if configured else "not-configured"),
                "dataControlStatus": "verified" if provider == "OpenAI" and settings.openai_project_data_controls_verified and settings.openai_data_controls_verified_at else "manual-review-required",
                "retentionStatus": settings.elevenlabs_retention_status if provider == "ElevenLabs" else settings.openai_abuse_monitoring_mode,
                "deletionCapability": "configured" if provider == "ElevenLabs" and settings.elevenlabs_provider_deletion_enabled else "manual-review-required",
                "lastVerified": latest.completed_at.isoformat() if latest and latest.completed_at else None,
                "verificationSource": latest.execution_mode if latest else "configuration",
                "manualReviewRequired": True,
            }
        )
    email = _latest_email_event(db)
    rows.append(
        {
            "provider": "Email",
            "capability": "Transactional email",
            "configured": settings.email_delivery_driver == "smtp" and bool(settings.email_from_address and settings.smtp_host),
            "connectivity": email.status if email else ("configured-unverified" if settings.email_delivery_driver == "smtp" else "not-configured"),
            "dataControlStatus": "manual-review-required",
            "retentionStatus": "operational-events-only",
            "deletionCapability": "not-applicable",
            "lastVerified": email.sent_at.isoformat() if email and email.sent_at else None,
            "verificationSource": "email-delivery-events",
            "manualReviewRequired": True,
        }
    )
    rows.extend(
        [
            {
                "provider": "PostgreSQL",
                "capability": "Active application persistence",
                "configured": True,
                "connectivity": "verified",
                "dataControlStatus": "configured-unverified",
                "retentionStatus": "configured",
                "deletionCapability": "active-database-delete",
                "lastVerified": utc_now_naive().date().isoformat(),
                "verificationSource": "runtime-persistence",
                "manualReviewRequired": False,
            },
            {
                "provider": "Local encrypted storage",
                "capability": "Temporary privacy exports",
                "configured": True,
                "connectivity": "verified",
                "dataControlStatus": "configured-unverified",
                "retentionStatus": "configured",
                "deletionCapability": "retention-policy",
                "lastVerified": utc_now_naive().date().isoformat(),
                "verificationSource": "privacy-service",
                "manualReviewRequired": False,
            },
        ]
    )
    return rows

