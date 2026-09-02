from datetime import timedelta
from typing import Annotated


from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.config import get_settings
from app.core.time import to_utc_naive, utc_now_naive
from app.database import get_db
from app.models.auth_security import AuthSession
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token.") from error

    user_id = payload.get("sub")
    session_id = payload.get("sid")
    auth_version = payload.get("ver")
    if payload.get("type") != "access" or not user_id or not session_id or auth_version is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token.")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    if user.account_status in {"disabled", "pending_deletion"}:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is not active.")
    if int(auth_version) != int(user.auth_version or 1):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication token is no longer valid.")
    session = db.get(AuthSession, session_id)
    now = utc_now_naive()
    if session is None or session.user_id != user.id or session.revoked_at is not None or to_utc_naive(session.expires_at) <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication session is not active.")
    user._auth_session_id = session.id  # type: ignore[attr-defined]

    return user


def get_optional_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    if credentials is None:
        if _is_public_optional_route(request):
            return None
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    try:
        return get_current_user(credentials, db)
    except (HTTPException, ValueError) as error:
        if _is_public_optional_route(request):
            return None
        if isinstance(error, HTTPException):
            raise
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token.") from error


def _is_public_optional_route(request: Request) -> bool:
    path = request.url.path
    return (
        path.startswith("/api/rag/search")
        or path.startswith("/api/v1/career-experiments/")
        or path.startswith("/api/v1/support/programmes")
        or path.startswith("/api/v1/learning/providers")
        or path.startswith("/api/v1/learning/resources")
    )


def require_recent_authentication(max_age_minutes: int = 10):
    def dependency(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
    ) -> User:
        session_id = getattr(user, "_auth_session_id", None)
        session = db.get(AuthSession, session_id) if session_id else None
        recent_at = session.last_used_at if session else None
        if recent_at is None or to_utc_naive(recent_at) < utc_now_naive() - timedelta(minutes=max_age_minutes):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="RECENT_AUTH_REQUIRED")
        return user

    return dependency


def require_admin_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    settings = get_settings()
    allowed = {email.strip().lower() for email in settings.admin_emails.split(",") if email.strip()}
    if not allowed or user.email.lower() not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return user

