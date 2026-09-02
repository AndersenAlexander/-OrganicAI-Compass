from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_recent_authentication
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.privacy import service

router = APIRouter()


class PreferenceUpdate(BaseModel):
    conversationPersistenceMode: str | None = Field(default=None, pattern="^(account-history|ephemeral)$")
    voiceTranscriptPersistenceMode: str | None = Field(default=None, pattern="^(account-history|ephemeral)$")
    voiceAudioStorageEnabled: bool | None = None
    productAnalyticsEnabled: bool | None = None
    researchParticipationEnabled: bool | None = None
    personalizationEnabled: bool | None = None
    serviceEmailEnabled: bool | None = None
    marketingEmailEnabled: bool | None = None


class ReauthPayload(BaseModel):
    password: str = Field(min_length=1, max_length=512)


class CategoryDeletePayload(BaseModel):
    confirmation: str


class AccountDeletePayload(BaseModel):
    confirmation: str


@router.get("/summary")
async def privacy_summary(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return service.summary(db, user)


@router.get("/inventory")
async def privacy_inventory(user: Annotated[User, Depends(get_current_user)]) -> dict:
    return service.inventory_response()


@router.get("/preferences")
async def get_preferences(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return service.preferences_payload(service.ensure_privacy_settings(db, user))


@router.put("/preferences")
async def update_preferences(
    payload: PreferenceUpdate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    settings = service.update_preferences(db, user, payload.model_dump(exclude_none=True), request)
    return service.preferences_payload(settings)


@router.get("/consents")
async def list_consents(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[dict[str, Any]]:
    return service.consent_events(db, user)


@router.get("/requests")
async def list_requests(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[dict[str, Any]]:
    return service.requests_for_user(db, user)


@router.get("/providers")
async def list_providers(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[dict[str, Any]]:
    return service.provider_summary(db, user)


@router.get("/research")
async def get_research(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return service.research_summary(db, user)


@router.post("/research/withdraw")
async def withdraw_research(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_recent_authentication(get_settings().privacy_recent_auth_minutes))],
) -> dict:
    return service.withdraw_research(db, user, request)


@router.post("/reauthenticate")
async def reauthenticate(
    payload: ReauthPayload,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    service.reauthenticate(db, user, payload.password)
    return {"recentAuthentication": True}


@router.post("/exports")
async def create_export(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_recent_authentication(get_settings().privacy_recent_auth_minutes))],
) -> dict:
    return service.export_payload(service.export_user_data(db, user))


@router.get("/exports")
async def list_exports(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[dict[str, Any]]:
    return service.latest_exports(db, user)


@router.get("/exports/{artifact_id}/download")
async def download_export(
    artifact_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_recent_authentication(get_settings().privacy_recent_auth_minutes))],
):
    return service.download_export(db, user, artifact_id)


@router.delete("/exports/{artifact_id}", status_code=204)
async def delete_export(
    artifact_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Response:
    service.delete_export(db, user, artifact_id)
    return Response(status_code=204)


@router.get("/deletion/categories/{category_key}/preview")
async def category_deletion_preview(
    category_key: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return service.category_deletion_preview(db, user, category_key)


@router.post("/deletion/categories/{category_key}")
async def category_deletion(
    category_key: str,
    payload: CategoryDeletePayload,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_recent_authentication(get_settings().privacy_recent_auth_minutes))],
) -> dict:
    return service.delete_category(db, user, category_key, payload.confirmation)


@router.post("/account-deletion")
async def request_account_deletion(
    payload: AccountDeletePayload,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_recent_authentication(get_settings().privacy_recent_auth_minutes))],
) -> dict:
    return service.request_account_deletion(db, user, payload.confirmation)


@router.post("/account-deletion/{request_id}/cancel")
async def cancel_account_deletion(
    request_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_recent_authentication(get_settings().privacy_recent_auth_minutes))],
) -> dict:
    return service.cancel_account_deletion(db, user, request_id)
