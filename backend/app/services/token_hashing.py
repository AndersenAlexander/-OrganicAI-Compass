import hashlib
import hmac

from app.config import get_settings


def hash_secret(value: str) -> str:
    key = get_settings().secret_key.encode("utf-8")
    return hmac.new(key, value.encode("utf-8"), hashlib.sha256).hexdigest()


def hash_context(value: str | None) -> str | None:
    clean = (value or "").strip()
    if not clean:
        return None
    return hash_secret(clean)

