from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth.dependencies import get_current_user, require_recent_authentication
from app.auth.security import create_access_token
from app.core.time import ensure_utc, parse_utc_datetime, to_utc_naive, utc_isoformat, utc_now, utc_now_naive
from app.database import Base, import_models
from app.models.auth_security import AuthSession
from app.models.privacy import PrivacyExportArtifact
from app.models.provider_operations import OperationalJobRun
from app.models.user import User
from app.privacy.service import retention_dry_run
from app.services.operational_workers import SYNTHETIC_WORKER, acquire_synthetic_job


def db_session() -> Session:
    import_models()
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def active_user_session(db: Session, *, expires_at: datetime | None = None, last_used_at: datetime | None = None) -> tuple[User, AuthSession]:
    user = User(name="UTC User", email="utc@example.test", hashed_password="x", account_status="active", auth_version=1)
    db.add(user)
    db.flush()
    now = utc_now_naive()
    session = AuthSession(
        user_id=user.id,
        token_family_id="family",
        refresh_token_hash="hash",
        created_at=now,
        expires_at=expires_at or now + timedelta(days=1),
        last_used_at=last_used_at or now,
    )
    db.add(session)
    db.commit()
    return user, session


def credentials_for(user: User, session: AuthSession) -> HTTPAuthorizationCredentials:
    token = create_access_token({"sub": user.id, "sid": session.id, "ver": user.auth_version})
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_utc_now_returns_aware_utc_datetime():
    value = utc_now()
    assert value.tzinfo is UTC
    assert value.utcoffset() == timedelta(0)


def test_ensure_utc_interprets_legacy_naive_values_as_utc():
    legacy = datetime(2026, 1, 1, 10, 0, 0)
    normalized = ensure_utc(legacy)
    assert normalized == datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)


def test_aware_values_remain_semantically_unchanged_and_host_timezone_independent():
    oslo_time = datetime(2026, 1, 1, 12, 30, 0, tzinfo=timezone(timedelta(hours=1)))
    assert ensure_utc(oslo_time) == datetime(2026, 1, 1, 11, 30, 0, tzinfo=UTC)
    assert parse_utc_datetime("2026-01-01T12:30:00") == datetime(2026, 1, 1, 12, 30, 0, tzinfo=UTC)
    assert parse_utc_datetime("2026-01-01T12:30:00+01:00") == datetime(2026, 1, 1, 11, 30, 0, tzinfo=UTC)


def test_naive_and_aware_comparisons_use_normalized_boundaries():
    legacy = datetime(2026, 1, 1, 10, 0, 0)
    aware = datetime(2026, 1, 1, 11, 0, 0, tzinfo=UTC)
    assert to_utc_naive(legacy) < to_utc_naive(aware)


def test_json_timestamp_serialization_remains_legacy_compatible_by_default():
    value = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
    assert utc_isoformat(value) == "2026-01-01T10:00:00"
    assert utc_isoformat(value, include_offset=True) == "2026-01-01T10:00:00+00:00"


def test_auth_expiration_accepts_aware_utc_values_without_type_errors():
    db = db_session()
    user, session = active_user_session(db, expires_at=utc_now() + timedelta(days=1))
    current = get_current_user(credentials_for(user, session), db)
    assert current.id == user.id

    session.expires_at = utc_now() - timedelta(minutes=1)
    db.commit()
    with pytest.raises(HTTPException) as exc:
        get_current_user(credentials_for(user, session), db)
    assert exc.value.status_code == 401


def test_recent_authentication_window_accepts_aware_and_rejects_stale_values():
    db = db_session()
    user, session = active_user_session(db, last_used_at=utc_now() - timedelta(minutes=2))
    user._auth_session_id = session.id  # type: ignore[attr-defined]
    dependency = require_recent_authentication(max_age_minutes=10)
    assert dependency(user, db).id == user.id

    session.last_used_at = utc_now() - timedelta(minutes=30)
    db.commit()
    with pytest.raises(HTTPException) as exc:
        dependency(user, db)
    assert exc.value.status_code == 403


def test_privacy_retention_deadline_counts_legacy_compatible_expired_artifacts(tmp_path):
    db = db_session()
    user, _session = active_user_session(db)
    artifact = PrivacyExportArtifact(
        user_id=user.id,
        status="ready",
        format="zip-json",
        storage_path=str(tmp_path / "export.zip.enc"),
        encryption_key_hash="hash",
        checksum_sha256="checksum",
        size_bytes=1,
        created_at=utc_now(),
        expires_at=utc_now() - timedelta(hours=1),
    )
    db.add(artifact)
    db.commit()
    assert retention_dry_run(db)["expiredExports"] == 1


def test_operational_worker_acquires_stale_aware_lease_without_type_errors():
    db = db_session()
    run = OperationalJobRun(
        job_type=SYNTHETIC_WORKER,
        status="queued",
        started_at=utc_now(),
        lease_expires_at=utc_now() - timedelta(seconds=1),
        failure_summary_json={"mode": "single"},
    )
    db.add(run)
    db.commit()
    acquired = acquire_synthetic_job(db, "utc-worker", lease_seconds=30)
    assert acquired is not None
    assert acquired.status == "processing"
    assert acquired.heartbeat_at is not None


def test_sqlite_persistence_keeps_existing_naive_utc_storage_contract():
    db = db_session()
    user = User(name="SQLite UTC", email="sqlite-utc@example.test", hashed_password="x")
    db.add(user)
    db.commit()
    db.refresh(user)
    assert user.created_at.tzinfo is None
    assert user.updated_at.tzinfo is None
    assert user.created_at <= utc_now_naive()
