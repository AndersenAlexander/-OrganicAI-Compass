from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    text: str
    html: str
    message_type: str = "transactional"
    idempotency_key: str | None = None


@dataclass(frozen=True)
class EmailResult:
    status: str
    provider: str
    provider_message_id: str | None = None
    failure_code: str | None = None
    inbox_delivery_verified: bool = False
    attempt_count: int = 0


class EmailDriver:
    provider = "disabled"

    def send(self, message: EmailMessage) -> EmailResult:
        return EmailResult(status="disabled", provider=self.provider, failure_code="EMAIL_DISABLED", attempt_count=0)
