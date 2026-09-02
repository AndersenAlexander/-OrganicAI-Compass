from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin_user
from app.database import get_db
from app.models.user import User
from app.services.email.validation import email_configuration_status
from app.services.operational_workers import worker_status
from app.services.provider_registry import provider_registry
from app.services.release_readiness import release_readiness_summary

router = APIRouter()


@router.get("/providers")
async def system_providers(db: Annotated[Session, Depends(get_db)], _user: Annotated[User, Depends(require_admin_user)]) -> dict:
    return {"providers": provider_registry(db), "secretValuesIncluded": False}


@router.get("/email")
async def system_email(_user: Annotated[User, Depends(require_admin_user)]) -> dict:
    return email_configuration_status()


@router.get("/privacy-workers")
async def system_privacy_workers(db: Annotated[Session, Depends(get_db)], _user: Annotated[User, Depends(require_admin_user)]) -> dict:
    return worker_status(db)


@router.get("/release-readiness")
async def system_release_readiness(_user: Annotated[User, Depends(require_admin_user)]) -> dict:
    return release_readiness_summary()
