from __future__ import annotations

from datetime import datetime, timedelta
from app.core.time import utc_now_naive
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.auth_security import AuthSession
from app.models.user import User
from app.privacy import service

router = APIRouter()


def require_recent_fixture_user(db: Session, user: User) -> User:
    session_id = getattr(user, "_auth_session_id", None)
    session = db.get(AuthSession, session_id) if session_id else None
    recent_at = session.last_used_at if session else None
    if recent_at is None or recent_at < utc_now_naive() - timedelta(minutes=get_settings().privacy_recent_auth_minutes):
        raise HTTPException(status_code=403, detail="RECENT_AUTH_REQUIRED")
    return user


@router.post("/privacy/account-deletion/{request_id}/execute-fixture")
async def execute_account_deletion_fixture(
    request_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return service.execute_account_deletion_fixture(db, require_recent_fixture_user(db, user), request_id)

