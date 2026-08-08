from collections import defaultdict, deque
from time import monotonic
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.services.demo_seed_service import ensure_demo, is_demo_user, restore_demo

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


def login_payload(db: Session) -> dict:
    settings = get_settings()
    user, profile, _ = ensure_demo(db, reset=settings.demo_reset_on_login)
    return {
        "access_token": create_access_token({"sub": user.id}),
        "token_type": "bearer",
        "user": {"id": user.id, "name": user.name, "email": user.email, "is_demo": True},
        "active_profile_id": profile.id,
        "demo_mode": True,
    }


@auth_router.post("/demo-login")
async def demo_login(request: Request, db: Annotated[Session, Depends(get_db)]) -> dict:
    require_enabled()
    check_rate_limit(request)
    return login_payload(db)


# Compatibility for clients using the prototype route.
@router.post("/login")
async def legacy_demo_login(request: Request, db: Annotated[Session, Depends(get_db)]) -> dict:
    require_enabled()
    check_rate_limit(request)
    return login_payload(db)


@router.post("/reset")
async def reset_demo(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    require_enabled()
    if not is_demo_user(user):
        raise HTTPException(403, "This action is unavailable in Demo Mode.")
    _, profile, _ = restore_demo(db)
    sections = ["diagnostic", "profile", "recommendations", "roadmap", "coach"]
    return {
        "ok": True,
        "status": "reset",
        "profile_id": profile.id,
        "active_profile_id": profile.id,
        "reset_sections": sections,
        "message": "Demonstration data has been restored.",
    }
