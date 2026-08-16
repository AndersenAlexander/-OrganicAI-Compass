from __future__ import annotations

from dataclasses import dataclass
from html import escape
from urllib.parse import quote

from app.config import get_settings


@dataclass(frozen=True)
class RenderedEmail:
    subject: str
    text: str
    html: str


TEMPLATE_TITLES = {
    "verify-email": "Verify email address",
    "reset-password": "Reset password",
    "password-changed": "Password changed",
    "new-session": "New session detected",
    "session-revoked": "Session access changed",
    "account-deletion-requested": "Account deletion requested",
    "account-deletion-cancelled": "Account deletion cancelled",
    "account-deletion-completed": "Account deletion completed",
    "privacy-export-ready": "Privacy export ready",
    "privacy-export-expired": "Privacy export expired",
    "provider-deletion-pending": "Provider deletion pending",
    "security-alert": "Security alert",
}


def render_template(template_key: str, *, token: str | None = None, path: str = "/", expires: str = "the stated expiration window") -> RenderedEmail:
    settings = get_settings()
    title = TEMPLATE_TITLES.get(template_key, "OrganicAI Compass notification")
    link = f"{settings.email_public_base_url.rstrip('/')}{path}"
    if token:
        separator = "&" if "?" in link else "?"
        link = f"{link}{separator}token={quote(token, safe='')}"
    text = (
        f"{title}\n\n"
        f"This message is from OrganicAI Compass.\n"
        f"Open: {link}\n"
        f"This link expires in {expires}.\n"
        "If you did not request this, ignore the message or contact support.\n"
    )
    html = (
        "<!doctype html><html><body>"
        f"<h1>{escape(title)}</h1>"
        "<p>This message is from OrganicAI Compass.</p>"
        f"<p><a href=\"{escape(link)}\">Open OrganicAI Compass</a></p>"
        f"<p>This link expires in {escape(expires)}.</p>"
        "<p>If you did not request this, ignore the message or contact support.</p>"
        "</body></html>"
    )
    return RenderedEmail(subject=title, text=text, html=html)
