from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.profile import Profile
from app.models.user import User


def is_admin_user(user: User | None) -> bool:
    if user is None:
        return False
    allowed = {email.strip().lower() for email in get_settings().admin_emails.split(",") if email.strip()}
    return bool(allowed and user.email.lower() in allowed)


def is_configured_demo_user(user: User | None) -> bool:
    settings = get_settings()
    return bool(user and user.is_demo and user.email.lower() == settings.demo_user_email.lower())


def _validate_profile_id(profile_id: str) -> None:
    if profile_id in {"undefined", "null", ""}:
        raise HTTPException(status_code=422, detail="A valid profile id is required.")


def assert_profile_access(profile: Profile, user: User | None, *, allow_admin_remediation: bool = True) -> Profile:
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    if profile.user_id is None:
        if allow_admin_remediation and is_admin_user(user):
            return profile
        raise HTTPException(status_code=403, detail="Legacy orphan profile requires administrator remediation.")
    if is_configured_demo_user(user):
        if profile.user_id == user.id:
            return profile
        raise HTTPException(status_code=403, detail="Profile does not belong to the configured demo user.")
    if user.is_demo:
        raise HTTPException(status_code=403, detail="Demo profile access is limited to the configured demo user.")
    if profile.user_id != user.id:
        raise HTTPException(status_code=403, detail="Profile does not belong to the current user.")
    return profile


def require_owned_profile(db: Session, profile_id: str, user: User | None, *, allow_admin_remediation: bool = True) -> Profile:
    _validate_profile_id(profile_id)
    profile = db.get(Profile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return assert_profile_access(profile, user, allow_admin_remediation=allow_admin_remediation)


def require_owned_record(
    record: object | None,
    user: User | None,
    *,
    resource_name: str,
    owner_attr: str = "user_id",
    allow_admin_remediation: bool = True,
) -> object:
    if record is None:
        raise HTTPException(status_code=404, detail=f"{resource_name} not found")
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    owner_id = getattr(record, owner_attr, None)
    if owner_id is None:
        if allow_admin_remediation and is_admin_user(user):
            return record
        raise HTTPException(status_code=403, detail=f"{resource_name} requires administrator remediation.")
    if owner_id != user.id:
        raise HTTPException(status_code=403, detail=f"{resource_name} does not belong to the current user.")
    return record
