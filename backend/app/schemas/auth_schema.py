from pydantic import BaseModel, field_validator

from app.schemas.user_schema import UserPublic


def _validate_email(value: str) -> str:
    clean = value.strip()
    local, separator, domain = clean.rpartition("@")
    if (
        not separator
        or not local
        or not domain
        or any(character.isspace() for character in clean)
        or "." not in domain
        or domain.startswith(".")
        or domain.endswith(".")
    ):
        raise ValueError("Enter a valid email address.")
    return clean


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

    _validate_email = field_validator("email")(_validate_email)


class LoginRequest(BaseModel):
    email: str
    password: str

    _validate_email = field_validator("email")(_validate_email)


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

    _validate_email = field_validator("email")(_validate_email)


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
