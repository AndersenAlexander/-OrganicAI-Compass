from __future__ import annotations

import smtplib
from email.message import EmailMessage as SmtpMessage
from email.utils import make_msgid

from app.config import get_settings
from app.services.email.base import EmailDriver, EmailMessage, EmailResult


class SmtpEmailDriver(EmailDriver):
    provider = "smtp"

    def send(self, message: EmailMessage) -> EmailResult:
        settings = get_settings()
        if not settings.smtp_host or not settings.email_from_address:
            return EmailResult(status="failed", provider=self.provider, failure_code="SMTP_NOT_CONFIGURED", attempt_count=0)
        smtp_message = SmtpMessage()
        smtp_message["Subject"] = message.subject
        smtp_message["From"] = f"{settings.email_from_name} <{settings.email_from_address}>"
        smtp_message["To"] = message.to
        smtp_message["Message-ID"] = make_msgid(domain=(settings.email_from_address.split("@", 1)[-1] or None))
        if message.idempotency_key:
            smtp_message["X-OrganicAI-Idempotency-Key"] = message.idempotency_key
        if settings.email_reply_to:
            smtp_message["Reply-To"] = settings.email_reply_to
        smtp_message.set_content(message.text)
        smtp_message.add_alternative(message.html, subtype="html")
        max_attempts = max(1, min(int(settings.smtp_max_attempts or 1), 3))
        for attempt in range(1, max_attempts + 1):
            try:
                cls = smtplib.SMTP_SSL if settings.smtp_use_ssl else smtplib.SMTP
                with cls(settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_seconds) as smtp:
                    if settings.smtp_use_starttls and not settings.smtp_use_ssl:
                        smtp.starttls()
                    if settings.smtp_username:
                        smtp.login(settings.smtp_username, settings.smtp_password or "")
                    refused = smtp.send_message(smtp_message)
                if refused:
                    return EmailResult(status="failed", provider=self.provider, failure_code="SMTP_RECIPIENT_REFUSED", attempt_count=attempt)
                return EmailResult(status="accepted", provider=self.provider, provider_message_id=smtp_message["Message-ID"], attempt_count=attempt)
            except TimeoutError:
                if attempt >= max_attempts:
                    return EmailResult(status="failed", provider=self.provider, failure_code="SMTP_TIMEOUT", attempt_count=attempt)
            except smtplib.SMTPAuthenticationError:
                return EmailResult(status="failed", provider=self.provider, failure_code="SMTP_AUTH_FAILED", attempt_count=attempt)
            except smtplib.SMTPException:
                if attempt >= max_attempts:
                    return EmailResult(status="failed", provider=self.provider, failure_code="SMTP_FAILED", attempt_count=attempt)
        return EmailResult(status="failed", provider=self.provider, failure_code="SMTP_FAILED", attempt_count=max_attempts)
