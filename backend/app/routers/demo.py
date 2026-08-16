from collections import defaultdict, deque
from time import monotonic
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.services.demo_seed_service import ensure_demo, is_demo_user, restore_demo
from app.services.auth_service import create_session, make_access_token, set_refresh_cookie

router = APIRouter()
auth_router = APIRouter()
_attempts: dict[str, deque[float]] = defaultdict(deque)


def require_enabled() -> None:
    if not get_settings().demo_account_enabled:
        raise HTTPException(404, "Demo mode is disabled.")


def check_rate_limit(request: Request) -> None:
    settings = get_settings()
    key = request.client.host if request.client else "unknown"
    now = monotonic()
    attempts = _attempts[key]
    while attempts and now - attempts[0] > 60:
        attempts.popleft()
    if len(attempts) >= settings.demo_login_rate_limit:
        raise HTTPException(429, "Too many demo login attempts. Try again shortly.")
    attempts.append(now)


def login_payload(db: Session, request: Request | None = None) -> dict:
    settings = get_settings()
    user, profile, _ = ensure_demo(db, reset=settings.demo_reset_on_login)
    session, refresh_token = create_session(db, user, request)
    db.commit()
    return {
        "access_token": make_access_token(user, session),
        "token_type": "bearer",
        "expires_in": getattr(settings, "access_token_expire_minutes", 15) * 60,
        "user": {"id": user.id, "name": user.name, "email": user.email, "is_demo": True},
        "active_profile_id": profile.id,
        "demo_mode": True,
        "_refresh_token": refresh_token,
    }


@auth_router.post("/demo-login")
async def demo_login(request: Request, response: Response, db: Annotated[Session, Depends(get_db)]) -> dict:
    require_enabled()
    check_rate_limit(request)
    payload = login_payload(db, request)
    refresh_token = payload.pop("_refresh_token")
    set_refresh_cookie(response, refresh_token)
    return payload


# Compatibility for clients using the prototype route.
@router.post("/login")
async def legacy_demo_login(request: Request, response: Response, db: Annotated[Session, Depends(get_db)]) -> dict:
    require_enabled()
    check_rate_limit(request)
    payload = login_payload(db, request)
    refresh_token = payload.pop("_refresh_token")
    set_refresh_cookie(response, refresh_token)
    return payload


@router.post("/reset")
async def reset_demo(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    require_enabled()
    if not is_demo_user(user):
        raise HTTPException(403, "This action is unavailable in Demo Mode.")
    _, profile, _ = restore_demo(db)
    sections = ["diagnostic", "profile", "recommendations", "roadmap", "coach", "career_resilience", "market_application", "innovation_extension", "originality_research"]
    return {
        "ok": True,
        "status": "reset",
        "profile_id": profile.id,
        "active_profile_id": profile.id,
        "reset_sections": sections,
        "message": "Demonstration data has been restored.",
    }
