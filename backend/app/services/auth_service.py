from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta

from fastapi import HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import create_access_token, generate_opaque_token, hash_password, verify_and_upgrade_password
from app.config import get_settings
from app.core.time import to_utc_naive, utc_now_naive as utcnow
from app.models.auth_security import AccountToken, AuthEvent, AuthSession
from app.models.user import User
from app.schemas.user_schema import UserPublic
from app.services.email.base import EmailMessage, EmailResult
from app.services.email.templates import render_template
from app.services.email.validation import driver_for_settings, record_email_event
from app.services.metrics import record_auth_metric
from app.services.token_hashing import hash_context, hash_secret

ACTIVE_STATUSES = {"active", "unverified"}
TOKEN_PURPOSE_EMAIL_VERIFICATION = "email_verification"
TOKEN_PURPOSE_PASSWORD_RESET = "password_reset"


@dataclass
class AuthResult:
    user: User
    access_token: str
    refresh_token: str
    session: AuthSession


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.strip().lower()))


def validate_password_policy(password: str, *, email: str, allow_demo_password: bool = False) -> None:
    settings = get_settings()
    if len(password) < 12:
        raise HTTPException(status_code=400, detail="Password must be at least 12 characters.")
    if len(password) > 256:
        raise HTTPException(status_code=400, detail="Password must not exceed 256 characters.")
    if password == email.strip().lower():
        raise HTTPException(status_code=400, detail="Password must not match the email address.")
    if not allow_demo_password and password == settings.demo_user_password:
        raise HTTPException(status_code=400, detail="Choose a password different from the configured demo password.")


def make_access_token(user: User, session: AuthSession) -> str:
    return create_access_token({"sub": user.id, "sid": session.id, "ver": user.auth_version})


def _request_hashes(request: Request | None) -> tuple[str | None, str | None]:
    if request is None:
        return None, None
    ip = request.client.host if request.client else None
    agent = request.headers.get("user-agent")
    return hash_context(ip), hash_context(agent)


def record_auth_event(
    db: Session,
    *,
    event_type: str,
    result: str,
    user_id: str | None = None,
    session_id: str | None = None,
    reason_code: str | None = None,
    request: Request | None = None,
) -> None:
    record_auth_metric(event_type, result)
    ip_hash, user_agent_hash = _request_hashes(request)
    request_id = request.headers.get("x-request-id") if request else None
    db.add(
        AuthEvent(
            user_id=user_id,
            session_id=session_id,
            event_type=event_type,
            result=result,
            reason_code=reason_code,
            request_id=request_id,
            ip_hash=ip_hash,
            user_agent_hash=user_agent_hash,
        )
    )


def create_session(db: Session, user: User, request: Request | None = None, *, family_id: str | None = None) -> tuple[AuthSession, str]:
    settings = get_settings()
    refresh_token = generate_opaque_token()
    ip_hash, user_agent_hash = _request_hashes(request)
    now = utcnow()
    session = AuthSession(
        user_id=user.id,
        token_family_id=family_id or str(uuid.uuid4()),
        refresh_token_hash=hash_secret(refresh_token),
        created_at=now,
        expires_at=now + timedelta(days=settings.refresh_token_expire_days),
        last_used_at=now,
        user_agent_hash=user_agent_hash,
        ip_hash=ip_hash,
        is_demo=user.is_demo,
    )
    db.add(session)
    db.flush()
    enforce_session_limit(db, user.id)
    return session, refresh_token


def enforce_session_limit(db: Session, user_id: str) -> None:
    settings = get_settings()
    active = list(
        db.scalars(
            select(AuthSession)
            .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
            .order_by(AuthSession.created_at.desc())
        )
    )
    for old in active[settings.auth_session_limit_per_user :]:
        old.revoked_at = utcnow()
        old.revocation_reason = "session_limit"


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        settings.auth_cookie_name,
        refresh_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path=settings.auth_cookie_path,
        domain=settings.auth_cookie_domain or None,
        secure=settings.auth_cookie_secure,
        httponly=settings.auth_cookie_httponly,
        samesite=settings.auth_cookie_samesite,
    )


def clear_refresh_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(settings.auth_cookie_name, path=settings.auth_cookie_path, domain=settings.auth_cookie_domain or None)


def auth_response_payload(result: AuthResult) -> dict:
    return {
        "access_token": result.access_token,
        "token_type": "bearer",
        "user": UserPublic.model_validate(result.user).model_dump(mode="json"),
        "expires_in": get_settings().access_token_expire_minutes * 60,
    }


def create_account_token(db: Session, user: User, purpose: str, request: Request | None = None) -> str:
    settings = get_settings()
    now = utcnow()
    for token in db.scalars(
        select(AccountToken).where(
            AccountToken.user_id == user.id,
            AccountToken.purpose == purpose,
            AccountToken.used_at.is_(None),
            AccountToken.invalidated_at.is_(None),
        )
    ):
        token.invalidated_at = now
    raw = generate_opaque_token()
    expiry = now + (
        timedelta(hours=settings.email_verification_expire_hours)
        if purpose == TOKEN_PURPOSE_EMAIL_VERIFICATION
        else timedelta(minutes=settings.password_reset_expire_minutes)
    )
    ip_hash, user_agent_hash = _request_hashes(request)
    context = ":".join(part for part in [ip_hash, user_agent_hash] if part)
    db.add(AccountToken(user_id=user.id, purpose=purpose, token_hash=hash_secret(raw), created_at=now, expires_at=expiry, request_context_hash=hash_context(context)))
    return raw


def send_verification_email(db: Session, user: User, request: Request | None = None) -> None:
    settings = get_settings()
    token = create_account_token(db, user, TOKEN_PURPOSE_EMAIL_VERIFICATION, request)
    rendered = render_template("verify-email", token=token, path="/verify-email", expires=f"{settings.email_verification_expire_hours} hours")
    message = EmailMessage(to=user.email, subject=rendered.subject, text=rendered.text, html=rendered.html, message_type="verify-email")
    driver = driver_for_settings()
    result = driver.send(message) if driver else EmailResult(status="disabled", provider="disabled", failure_code="EMAIL_DISABLED")
    record_email_event(db, message, result)


def send_password_reset_email(db: Session, user: User, request: Request | None = None) -> None:
    settings = get_settings()
    token = create_account_token(db, user, TOKEN_PURPOSE_PASSWORD_RESET, request)
    rendered = render_template("reset-password", token=token, path="/reset-password", expires=f"{settings.password_reset_expire_minutes} minutes")
    message = EmailMessage(to=user.email, subject=rendered.subject, text=rendered.text, html=rendered.html, message_type="reset-password")
    driver = driver_for_settings()
    result = driver.send(message) if driver else EmailResult(status="disabled", provider="disabled", failure_code="EMAIL_DISABLED")
    record_email_event(db, message, result)


def send_account_notification_email(db: Session, user: User, template_key: str, message_type: str, path: str = "/account/security") -> None:
    rendered = render_template(template_key, path=path, expires="not applicable")
    message = EmailMessage(
        to=user.email,
        subject=rendered.subject,
        text=rendered.text,
        html=rendered.html,
        message_type=message_type,
        idempotency_key=hash_context(f"{user.id}:{message_type}:{user.auth_version or 1}"),
    )
    driver = driver_for_settings()
    result = driver.send(message) if driver else EmailResult(status="disabled", provider="disabled", failure_code="EMAIL_DISABLED")
    record_email_event(db, message, result)


def register_user(db: Session, name: str, email: str, password: str, request: Request | None = None) -> AuthResult:
    normalized_email = email.strip().lower()
    if get_user_by_email(db, normalized_email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")
    validate_password_policy(password, email=normalized_email)

    user = User(name=name.strip(), email=normalized_email, hashed_password=hash_password(password), account_status="unverified", auth_version=1)
    db.add(user)
    db.flush()
    session, refresh_token = create_session(db, user, request)
    access_token = make_access_token(user, session)
    send_verification_email(db, user, request)
    record_auth_event(db, event_type="register", result="success", user_id=user.id, session_id=session.id, request=request)
    db.commit()
    db.refresh(user)
    db.refresh(session)
    return AuthResult(user=user, access_token=access_token, refresh_token=refresh_token, session=session)


def authenticate_user(db: Session, email: str, password: str, request: Request | None = None) -> AuthResult:
    settings = get_settings()
    user = get_user_by_email(db, email)
    now = utcnow()
    if user and user.locked_until and to_utc_naive(user.locked_until) > now and not user.is_demo:
        record_auth_event(db, event_type="login", result="failure", user_id=user.id, reason_code="locked", request=request)
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if user is None:
        record_auth_event(db, event_type="login", result="failure", reason_code="invalid_credentials", request=request)
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    verified, upgraded_hash = verify_and_upgrade_password(password, user.hashed_password)
    if not verified:
        if not user.is_demo:
            user.failed_login_count = (user.failed_login_count or 0) + 1
            if user.failed_login_count >= settings.auth_max_failed_logins:
                user.locked_until = now + timedelta(minutes=settings.auth_lockout_minutes)
        record_auth_event(db, event_type="login", result="failure", user_id=user.id, reason_code="invalid_credentials", request=request)
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if user.account_status in {"disabled", "pending_deletion"}:
        record_auth_event(db, event_type="login", result="failure", user_id=user.id, reason_code="account_disabled", request=request)
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if upgraded_hash:
        user.hashed_password = upgraded_hash
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = now
    session, refresh_token = create_session(db, user, request)
    access_token = make_access_token(user, session)
    record_auth_event(db, event_type="login", result="success", user_id=user.id, session_id=session.id, request=request)
    db.commit()
    db.refresh(user)
    db.refresh(session)
    return AuthResult(user=user, access_token=access_token, refresh_token=refresh_token, session=session)


def refresh_session(db: Session, refresh_token: str | None, request: Request | None = None) -> AuthResult:
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token is missing.")
    token_hash = hash_secret(refresh_token)
    session = db.scalar(select(AuthSession).where(AuthSession.refresh_token_hash == token_hash))
    now = utcnow()
    if session is None:
        record_auth_event(db, event_type="refresh", result="failure", reason_code="unknown_refresh", request=request)
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid refresh token.")
    user = db.get(User, session.user_id)
    if session.revoked_at is not None:
        revoke_family(db, session.token_family_id, "refresh_reuse")
        record_auth_event(db, event_type="refresh_reuse", result="failure", user_id=session.user_id, session_id=session.id, reason_code="reuse", request=request)
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh token reuse detected.")
    if user is None or to_utc_naive(session.expires_at) <= now or user.account_status in {"disabled", "pending_deletion"}:
        session.revoked_at = now
        session.revocation_reason = "expired_or_invalid"
        record_auth_event(db, event_type="refresh", result="failure", user_id=session.user_id, session_id=session.id, reason_code="expired_or_invalid", request=request)
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid refresh token.")
    session.revoked_at = now
    session.revocation_reason = "rotated"
    replacement, new_refresh = create_session(db, user, request, family_id=session.token_family_id)
    session.replaced_by_session_id = replacement.id
    access_token = make_access_token(user, replacement)
    record_auth_event(db, event_type="refresh", result="success", user_id=user.id, session_id=replacement.id, request=request)
    db.commit()
    db.refresh(user)
    db.refresh(replacement)
    return AuthResult(user=user, access_token=access_token, refresh_token=new_refresh, session=replacement)


def revoke_family(db: Session, family_id: str, reason: str) -> None:
    now = utcnow()
    for session in db.scalars(select(AuthSession).where(AuthSession.token_family_id == family_id, AuthSession.revoked_at.is_(None))):
        session.revoked_at = now
        session.revocation_reason = reason


def revoke_session(db: Session, session: AuthSession, reason: str = "logout") -> None:
    if session.revoked_at is None:
        session.revoked_at = utcnow()
        session.revocation_reason = reason
        record_auth_metric("logout" if reason == "logout" else "session_revocation", "revoked")


def revoke_all_sessions(db: Session, user_id: str, reason: str = "logout_all", except_session_id: str | None = None) -> None:
    now = utcnow()
    for session in db.scalars(select(AuthSession).where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))):
        if except_session_id and session.id == except_session_id:
            continue
        session.revoked_at = now
        session.revocation_reason = reason
        record_auth_metric("session_revocation", "revoked")


def change_password(db: Session, user: User, current_password: str, new_password: str, current_session_id: str | None = None) -> None:
    verified, _ = verify_and_upgrade_password(current_password, user.hashed_password)
    if not verified:
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    validate_password_policy(new_password, email=user.email, allow_demo_password=user.is_demo)
    user.hashed_password = hash_password(new_password)
    user.password_changed_at = utcnow()
    user.auth_version = (user.auth_version or 1) + 1
    revoke_all_sessions(db, user.id, "password_changed", except_session_id=current_session_id)
    send_account_notification_email(db, user, "password-changed", "password-changed")
    db.commit()


def request_password_reset(db: Session, email: str, request: Request | None = None) -> None:
    user = get_user_by_email(db, email)
    if user and user.account_status not in {"disabled", "pending_deletion"}:
        send_password_reset_email(db, user, request)
        record_auth_event(db, event_type="forgot_password", result="success", user_id=user.id, request=request)
    else:
        record_auth_event(db, event_type="forgot_password", result="success", reason_code="generic", request=request)
    db.commit()


def consume_account_token(db: Session, raw_token: str, purpose: str) -> User:
    token = db.scalar(select(AccountToken).where(AccountToken.token_hash == hash_secret(raw_token), AccountToken.purpose == purpose))
    now = utcnow()
    if token is None or token.used_at or token.invalidated_at or to_utc_naive(token.expires_at) <= now:
        raise HTTPException(status_code=400, detail="Token is invalid or expired.")
    user = db.get(User, token.user_id)
    if user is None:
        raise HTTPException(status_code=400, detail="Token is invalid or expired.")
    token.used_at = now
    return user


def reset_password(db: Session, raw_token: str, new_password: str) -> None:
    user = consume_account_token(db, raw_token, TOKEN_PURPOSE_PASSWORD_RESET)
    validate_password_policy(new_password, email=user.email, allow_demo_password=user.is_demo)
    user.hashed_password = hash_password(new_password)
    user.password_changed_at = utcnow()
    user.auth_version = (user.auth_version or 1) + 1
    revoke_all_sessions(db, user.id, "password_reset")
    record_auth_event(db, event_type="password_reset", result="success", user_id=user.id)
    send_account_notification_email(db, user, "password-changed", "password-reset-completed")
    db.commit()


def verify_email(db: Session, raw_token: str) -> User:
    user = consume_account_token(db, raw_token, TOKEN_PURPOSE_EMAIL_VERIFICATION)
    user.email_verified_at = utcnow()
    if user.account_status == "unverified":
        user.account_status = "active"
    record_auth_event(db, event_type="email_verify", result="success", user_id=user.id)
    db.commit()
    db.refresh(user)
    return user
