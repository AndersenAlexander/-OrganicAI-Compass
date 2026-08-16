from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    """Interpret legacy naive datetimes as UTC and normalize aware values to UTC."""
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def utc_now_naive() -> datetime:
    """Return naive UTC for existing SQLAlchemy DateTime columns."""
    return utc_now().replace(tzinfo=None)


def to_utc_naive(value: datetime) -> datetime:
    """Normalize a datetime to UTC and strip tzinfo for legacy persistence."""
    return ensure_utc(value).replace(tzinfo=None)


def utc_isoformat(value: datetime | None = None, *, include_offset: bool = False) -> str:
    """Serialize UTC deterministically while preserving legacy naive API format by default."""
    normalized = utc_now() if value is None else ensure_utc(value)
    if include_offset:
        return normalized.isoformat()
    return normalized.replace(tzinfo=None).isoformat()


def parse_utc_datetime(value: str | datetime) -> datetime:
    """Parse an ISO timestamp as timezone-aware UTC, treating naive strings as UTC."""
    if isinstance(value, datetime):
        return ensure_utc(value)
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    return ensure_utc(datetime.fromisoformat(text))


def utc_from_timestamp(timestamp: float) -> datetime:
    """Return a timezone-aware UTC datetime from a POSIX timestamp."""
    return datetime.fromtimestamp(timestamp, UTC)
