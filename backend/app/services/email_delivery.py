from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from time import time

from app.config import get_settings
from app.services.email.base import EmailMessage as RichEmailMessage
from app.services.email.development_outbox import DevelopmentOutboxEmailDriver
from app.services.email.smtp_delivery import SmtpEmailDriver


@dataclass
class EmailMessage:
    to: str
    subject: str
    body: str


class EmailDelivery:
    def send(self, message: EmailMessage) -> None:
        settings = get_settings()
        if settings.email_delivery_driver == "development-outbox":
            outbox = Path(settings.email_development_outbox_dir)
            outbox.mkdir(parents=True, exist_ok=True)
            self._prune(outbox)
            message_id = f"dev-{int(time() * 1000)}"
            payload = {
                "to": message.to,
                "subject": message.subject,
                "body": message.body,
                "text": message.body,
                "html": f"<p>{message.body}</p>",
                "messageType": "legacy-auth",
                "providerMessageId": message_id,
            }
            (outbox / f"email-{message_id}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
            return
        if settings.email_delivery_driver == "smtp":
            driver = SmtpEmailDriver()
        else:
            driver = None
        if not driver:
            return
        driver.send(RichEmailMessage(to=message.to, subject=message.subject, text=message.body, html=f"<p>{message.body}</p>"))

    def _prune(self, outbox: Path, keep: int = 50) -> None:
        DevelopmentOutboxEmailDriver()._prune(outbox, keep)


email_delivery = EmailDelivery()
