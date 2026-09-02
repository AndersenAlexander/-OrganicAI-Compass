import secrets
import uuid
from datetime import timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings
from app.core.time import utc_now

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    settings = get_settings()
    hasher = PasswordHasher(
        time_cost=settings.password_hash_time_cost,
        memory_cost=settings.password_hash_memory_cost_kib,
        parallelism=settings.password_hash_parallelism,
    )
    return hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return verify_and_upgrade_password(plain_password, hashed_password)[0]


def verify_and_upgrade_password(plain_password: str, hashed_password: str) -> tuple[bool, str | None]:
    if hashed_password.startswith("$argon2"):
        settings = get_settings()
        hasher = PasswordHasher(
            time_cost=settings.password_hash_time_cost,
            memory_cost=settings.password_hash_memory_cost_kib,
            parallelism=settings.password_hash_parallelism,
        )
        try:
            verified = hasher.verify(hashed_password, plain_password)
        except (InvalidHashError, VerifyMismatchError):
            return False, None
        if verified and hasher.check_needs_rehash(hashed_password):
            return True, hasher.hash(plain_password)
        return verified, None
    # Legacy bcrypt cannot represent more than 72 UTF-8 bytes. Reject an
    # over-limit candidate instead of allowing silent truncation to authenticate.
    if len(plain_password.encode("utf-8")) > 72:
        return False, None
    try:
        verified = bcrypt_context.verify(plain_password, hashed_password)
    except Exception:
        return False, None
    return (True, hash_password(plain_password)) if verified else (False, None)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    to_encode = data.copy()
    now = utc_now()
    expires_at = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"type": "access", "iat": now, "exp": expires_at, "jti": to_encode.get("jti") or str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as error:
        raise ValueError("Invalid token.") from error


def generate_opaque_token() -> str:
    return secrets.token_urlsafe(48)
