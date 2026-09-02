from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import datetime
from app.core.time import utc_now_naive
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.provider_operations import WebhookDeliveryEvent
from app.services.error_responses import request_id_from_request
from app.services.token_hashing import hash_secret

router = APIRouter()
ALLOWED_EVENTS = {"post_call_transcription", "call_initiation_failure"}
MAX_WEBHOOK_BYTES = 256_000
TIMESTAMP_WINDOW_SECONDS = 300


def _parse_signature(header: str) -> tuple[int, str]:
    values = {}
    for part in header.split(","):
        if "=" in part:
            key, value = part.split("=", 1)
            values[key.strip()] = value.strip()
    timestamp = int(values.get("t", "0"))
    signature = values.get("v1", "")
    return timestamp, signature


def sign_elevenlabs_webhook(body: bytes, secret: str, timestamp: int | None = None) -> str:
    timestamp = timestamp or int(time.time())
    digest = hmac.new(secret.encode("utf-8"), f"{timestamp}.".encode("utf-8") + body, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


@router.post("/elevenlabs")
async def elevenlabs_webhook(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    elevenlabs_signature: str | None = Header(default=None, alias="ElevenLabs-Signature"),
) -> dict:
    settings = get_settings()
    secret = settings.elevenlabs_webhook_secret or settings.webhook_secret
    body = await request.body()
    if len(body) > MAX_WEBHOOK_BYTES:
        raise HTTPException(status_code=413, detail="Webhook payload too large.")
    if not secret or not elevenlabs_signature:
        raise HTTPException(status_code=401, detail="Invalid webhook signature.")
    try:
        timestamp, signature = _parse_signature(elevenlabs_signature)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid webhook signature.")
    if abs(int(time.time()) - timestamp) > TIMESTAMP_WINDOW_SECONDS:
        raise HTTPException(status_code=401, detail="Invalid webhook signature.")
    expected = sign_elevenlabs_webhook(body, secret, timestamp).split("v1=", 1)[1]
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature.")
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid webhook payload.")
    event_type = str(payload.get("type") or payload.get("event_type") or "")
    if event_type not in ALLOWED_EVENTS:
        raise HTTPException(status_code=422, detail="Unsupported webhook event.")
    if event_type == "post_call_audio":
        raise HTTPException(status_code=422, detail="Unsupported webhook event.")
    conversation_id = str(payload.get("conversation_id") or payload.get("conversationId") or "")
    event_key_hash = hash_secret(f"{event_type}:{timestamp}:{conversation_id}")
    event = WebhookDeliveryEvent(
        provider="ElevenLabs",
        event_type=event_type,
        external_event_key_hash=event_key_hash,
        signature_valid=True,
        duplicate=False,
        status="processed",
        received_at=utc_now_naive(),
        processed_at=utc_now_naive(),
        request_id=request_id_from_request(request),
    )
    try:
        db.add(event)
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(WebhookDeliveryEvent).filter_by(provider="ElevenLabs", external_event_key_hash=event_key_hash).first()
        if existing:
            existing.duplicate = True
            db.commit()
        return {"status": "duplicate"}
    return {"status": "accepted"}

