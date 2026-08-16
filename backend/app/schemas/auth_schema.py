from pydantic import BaseModel

from app.schemas.user_schema import UserPublic


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
    expires_in: int | None = None


class RefreshResponse(AuthResponse):
    pass


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class VerifyEmailRequest(BaseModel):
    token: str


class SessionPublic(BaseModel):
    id: str
    created_at: str
    last_used_at: str | None = None
    expires_at: str
    current_session: bool
    device: str
    revoked: bool
