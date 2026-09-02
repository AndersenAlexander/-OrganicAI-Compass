from __future__ import annotations

import socket

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.provider_operations import EmailDeliveryEvent
from app.services.email.base import EmailMessage, EmailResult
from app.services.email.development_outbox import DevelopmentOutboxEmailDriver
from app.services.email.smtp_delivery import SmtpEmailDriver
from app.services.email.templates import render_template
from app.services.token_hashing import hash_secret


def driver_for_settings():
    settings = get_settings()
    if settings.email_delivery_driver == "development-outbox":
        return DevelopmentOutboxEmailDriver()
    if settings.email_delivery_driver == "smtp":
        return SmtpEmailDriver()
    return None


def record_email_event(db: Session, message: EmailMessage, result: EmailResult) -> EmailDeliveryEvent:
    event = EmailDeliveryEvent(
        message_type=message.message_type,
        provider=result.provider,
        recipient_hash=hash_secret(message.to.lower()),
        status=result.status,
        attempt_count=max(1, getattr(result, "attempt_count", 1)),
        provider_message_id_hash=hash_secret(result.provider_message_id) if result.provider_message_id else None,
        failure_code=result.failure_code,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def email_configuration_status(settings=None) -> dict:
    settings = settings or get_settings()
    dns = "not-checked"
    if settings.smtp_host:
        try:
            socket.getaddrinfo(settings.smtp_host, settings.smtp_port)
            dns = "verified"
        except socket.gaierror:
            dns = "failed"
    production_ready = not (
        settings.app_env == "production"
        and (settings.email_delivery_driver in {"disabled", "development-outbox"} or not settings.email_from_address or not settings.email_public_base_url.startswith("https://"))
    )
    return {
        "driver": settings.email_delivery_driver,
        "configured": settings.email_delivery_driver == "smtp" and bool(settings.smtp_host and settings.email_from_address),
        "tls": settings.smtp_use_ssl or settings.smtp_use_starttls,
        "senderConfigured": bool(settings.email_from_address),
        "timeoutSeconds": settings.smtp_timeout_seconds,
        "maxAttempts": settings.smtp_max_attempts,
        "dns": dns,
        "productionReady": production_ready,
        "inboxDeliveryVerified": False,
        "secretValuesIncluded": False,
    }


def send_validation_email(db: Session, recipient: str) -> dict:
    settings = get_settings()
    if not settings.email_live_validation_enabled or not recipient or recipient != settings.email_test_recipient:
        return {"status": "not-executed", "reason": "approved recipient or EMAIL_LIVE_VALIDATION_ENABLED missing"}
    rendered = render_template("security-alert", path="/privacy")
    message = EmailMessage(to=recipient, subject=rendered.subject, text=rendered.text, html=rendered.html, message_type="validation-test")
    driver = driver_for_settings()
    result = driver.send(message) if driver else EmailResult(status="disabled", provider="disabled", failure_code="EMAIL_DISABLED")
    event = record_email_event(db, message, result)
    return {"status": result.status, "provider": result.provider, "eventId": event.id, "providerAccepted": result.status == "accepted", "inboxDeliveryVerified": False}
