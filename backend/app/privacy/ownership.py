from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile import Profile


def user_owns_profile(db: Session, user_id: str, profile_id: str | None) -> bool:
    if not profile_id:
        return False
    return db.scalar(select(Profile.id).where(Profile.id == profile_id, Profile.user_id == user_id)) is not None


def owner_filter_for_table(table_name: str, user_id: str) -> dict[str, str]:
    if table_name == "messages":
        return {"conversation_owner": user_id}
    if table_name in {"conversations", "users"} or table_name.startswith(("auth_", "privacy_", "data_", "external_provider")):
        return {"user_id": user_id}
    return {"user_or_profile_owner": user_id}
