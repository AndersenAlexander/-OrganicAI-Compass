from __future__ import annotations

import json
from pathlib import Path
from time import time

from app.config import get_settings
from app.services.email.base import EmailDriver, EmailMessage, EmailResult


class DevelopmentOutboxEmailDriver(EmailDriver):
    provider = "development-outbox"

    def send(self, message: EmailMessage) -> EmailResult:
        settings = get_settings()
        outbox = Path(settings.email_development_outbox_dir)
        outbox.mkdir(parents=True, exist_ok=True)
        self._prune(outbox)
        message_id = f"dev-{int(time() * 1000)}"
        payload = {
            "to": message.to,
            "subject": message.subject,
            "text": message.text,
            "html": message.html,
            "messageType": message.message_type,
            "providerMessageId": message_id,
            "idempotencyKeyPresent": bool(message.idempotency_key),
        }
        (outbox / f"email-{message_id}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return EmailResult(status="accepted", provider=self.provider, provider_message_id=message_id, attempt_count=1)

    def _prune(self, outbox: Path, keep: int = 50) -> None:
        files = sorted(outbox.glob("email-*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
        for old in files[keep:]:
            old.unlink(missing_ok=True)
