from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.auth_security import AuthSession
from app.models.user import User
from app.schemas.auth_schema import (
    AuthResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SessionPublic,
    VerifyEmailRequest,
)
from app.schemas.user_schema import UserPublic
from app.services.auth_service import (
    authenticate_user,
    auth_response_payload,
    change_password,
    clear_refresh_cookie,
    refresh_session,
    register_user,
    request_password_reset,
    revoke_all_sessions,
    revoke_session,
    send_verification_email,
    set_refresh_cookie,
    verify_email,
)
from app.services.token_hashing import hash_secret

router = APIRouter()


def require_origin(request: Request) -> None:
    settings = get_settings()
    if not settings.auth_require_origin_check:
        return
    origin = request.headers.get("origin")
    if not origin:
        if settings.app_env == "production":
            raise HTTPException(status_code=403, detail="Origin header is required.")
        return
    if origin not in set(settings.allowed_origin_list + [settings.frontend_public_url, settings.frontend_url]):
        raise HTTPException(status_code=403, detail="Origin is not allowed.")


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest, response: Response, request: Request, db: Annotated[Session, Depends(get_db)]) -> dict:
    result = register_user(db, payload.name, payload.email, payload.password, request)
    set_refresh_cookie(response, result.refresh_token)
    return auth_response_payload(result)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, response: Response, request: Request, db: Annotated[Session, Depends(get_db)]) -> dict:
    result = authenticate_user(db, payload.email, payload.password, request)
    set_refresh_cookie(response, result.refresh_token)
    return auth_response_payload(result)


@router.post("/refresh", response_model=AuthResponse)
async def refresh(response: Response, request: Request, db: Annotated[Session, Depends(get_db)]) -> dict:
    require_origin(request)
    try:
        result = refresh_session(db, request.cookies.get(get_settings().auth_cookie_name), request)
    except HTTPException:
        clear_refresh_cookie(response)
        raise
    set_refresh_cookie(response, result.refresh_token)
    return auth_response_payload(result)


@router.post("/logout")
async def logout(response: Response, request: Request, db: Annotated[Session, Depends(get_db)]) -> dict:
    require_origin(request)
    raw_refresh = request.cookies.get(get_settings().auth_cookie_name)
    if raw_refresh:
        session = db.scalar(select(AuthSession).where(AuthSession.refresh_token_hash == hash_secret(raw_refresh)))
        if session:
            revoke_session(db, session, "logout")
            db.commit()
    clear_refresh_cookie(response)
    return {"ok": True}


@router.post("/logout-all")
async def logout_all(response: Response, request: Request, db: Annotated[Session, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user)]) -> dict:
    require_origin(request)
    revoke_all_sessions(db, current_user.id, "logout_all")
    db.commit()
    clear_refresh_cookie(response)
    return {"ok": True}


@router.get("/me", response_model=UserPublic)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserPublic:
    return UserPublic.model_validate(current_user)


@router.get("/sessions", response_model=list[SessionPublic])
async def sessions(request: Request, db: Annotated[Session, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user)]) -> list[dict]:
    require_origin(request)
    current_session_id = getattr(current_user, "_auth_session_id", None)
    rows = db.scalars(select(AuthSession).where(AuthSession.user_id == current_user.id).order_by(AuthSession.created_at.desc())).all()
    return [
        {
            "id": row.id,
            "created_at": row.created_at.isoformat(),
            "last_used_at": row.last_used_at.isoformat() if row.last_used_at else None,
            "expires_at": row.expires_at.isoformat(),
            "current_session": row.id == current_session_id,
            "device": "Known browser" if row.user_agent_hash else "Unknown device",
            "revoked": row.revoked_at is not None,
        }
        for row in rows
    ]


@router.delete("/sessions/{session_id}")
async def revoke_auth_session(session_id: str, request: Request, db: Annotated[Session, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user)]) -> dict:
    require_origin(request)
    session = db.get(AuthSession, session_id)
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found.")
    revoke_session(db, session, "user_revoked")
    db.commit()
    return {"ok": True}


@router.post("/change-password")
async def change_password_endpoint(payload: ChangePasswordRequest, request: Request, db: Annotated[Session, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user)]) -> dict:
    require_origin(request)
    change_password(db, current_user, payload.current_password, payload.new_password, getattr(current_user, "_auth_session_id", None))
    return {"ok": True}


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, request: Request, db: Annotated[Session, Depends(get_db)]) -> dict:
    request_password_reset(db, payload.email, request)
    return {"ok": True, "message": "If an account exists, password reset instructions have been sent."}


@router.post("/reset-password")
async def reset_password_endpoint(payload: ResetPasswordRequest, request: Request, db: Annotated[Session, Depends(get_db)]) -> dict:
    require_origin(request)
    from app.services.auth_service import reset_password

    reset_password(db, payload.token, payload.new_password)
    return {"ok": True}


@router.post("/verify-email", response_model=UserPublic)
async def verify_email_endpoint(payload: VerifyEmailRequest, db: Annotated[Session, Depends(get_db)]) -> UserPublic:
    user = verify_email(db, payload.token)
    return UserPublic.model_validate(user)


@router.post("/resend-verification")
async def resend_verification(request: Request, db: Annotated[Session, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user)]) -> dict:
    require_origin(request)
    send_verification_email(db, current_user, request)
    db.commit()
    return {"ok": True, "message": "If verification is required, a new email has been sent."}
