from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.auth_schema import AuthResponse, LoginRequest, RegisterRequest
from app.schemas.user_schema import UserPublic
from app.services.auth_service import authenticate_user, register_user

router = APIRouter()


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest, db: Annotated[Session, Depends(get_db)]) -> AuthResponse:
    user, token = register_user(db, payload.name, payload.email, payload.password)
    return AuthResponse(access_token=token, user=UserPublic.model_validate(user))


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> AuthResponse:
    user, token = authenticate_user(db, payload.email, payload.password)
    return AuthResponse(access_token=token, user=UserPublic.model_validate(user))


@router.get("/me", response_model=UserPublic)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserPublic:
    return UserPublic.model_validate(current_user)
