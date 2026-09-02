from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import app.models  # noqa: F401 - register SQLAlchemy models for create_all.
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth.security import create_access_token
from app.core.time import utc_now_naive
from app.database import Base, get_db
from app.models.auth_security import AuthSession
from app.models.innovation_extension import BrowserExtensionConnection, BrowserJobCapture
from app.models.profile import Profile
from app.models.user import User
from app.routers import innovation_extension
from app.services.innovation_extension_engine import create_extension_connection


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        access_token_expire_minutes=30,
        admin_emails="admin@example.test",
        algorithm="HS256",
        demo_user_email="demo@organicai.local",
        secret_key="x" * 40,
    )


@pytest.fixture(autouse=True)
def task15c_settings(monkeypatch):
    settings = _settings()
    monkeypatch.setattr("app.auth.security.get_settings", lambda: settings)
    monkeypatch.setattr("app.auth.dependencies.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.profile_authorization.get_settings", lambda: settings)


def session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def client_for(db: Session) -> TestClient:
    app = FastAPI()
    app.include_router(innovation_extension.router, prefix="/api/v1")

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


def make_user_profile(db: Session, email: str) -> tuple[User, Profile]:
    user = User(name=email.split("@")[0], email=email, hashed_password="x")
    db.add(user)
    db.flush()
    profile = Profile(user_id=user.id, diagnostic_id=f"diagnostic-{email}", data={"primary_archetype": {"name": "Curious Builder"}})
    db.add(profile)
    db.commit()
    db.refresh(user)
    db.refresh(profile)
    return user, profile


def auth_headers(db: Session, user: User) -> dict[str, str]:
    session_row = AuthSession(
        user_id=user.id,
        token_family_id=str(uuid4()),
        refresh_token_hash=f"refresh-{uuid4()}",
        created_at=utc_now_naive(),
        expires_at=utc_now_naive() + timedelta(days=1),
    )
    db.add(session_row)
    db.commit()
    token = create_access_token({"sub": user.id, "sid": session_row.id, "ver": user.auth_version})
    return {"Authorization": f"Bearer {token}"}


def capture_payload(url_suffix: str = "ai-product-designer") -> dict:
    return {
        "source_url": f"https://jobs.example.test/roles/{url_suffix}",
        "page_title": "AI Product Designer - Example Studio",
        "captured_text": "Mandatory requirements include UX design, responsible AI, accessibility and API integration.",
        "selected_text": "UX design and responsible AI",
        "capture_method": "user_triggered_browser_extension",
        "requested_action": "save",
        "extension_version": "0.1.0",
    }


def test_extension_token_only_capture_is_bound_to_profile_and_rejects_substitution():
    db = session()
    client = client_for(db)
    owner, profile = make_user_profile(db, "owner@example.test")
    _, other_profile = make_user_profile(db, "other@example.test")
    connection = create_extension_connection(db, profile, {"expires_in_days": 7}, owner.id)
    token = connection["connection_token"]

    anonymous = client.post(f"/api/v1/profiles/{profile.id}/job-captures", json=capture_payload("anonymous"))
    valid = client.post(
        f"/api/v1/profiles/{profile.id}/job-captures",
        headers={"X-OrganicAI-Extension-Token": token},
        json=capture_payload("valid"),
    )
    wrong_profile = client.post(
        f"/api/v1/profiles/{other_profile.id}/job-captures",
        headers={"X-OrganicAI-Extension-Token": token},
        json=capture_payload("wrong-profile"),
    )
    demo_substitution = client.post(
        "/api/v1/profiles/demo-profile/job-captures",
        headers={"X-OrganicAI-Extension-Token": token},
        json=capture_payload("demo-substitution"),
    )

    assert anonymous.status_code == 401
    assert valid.status_code == 200
    assert valid.json()["profile_id"] == profile.id
    assert wrong_profile.status_code == 403
    assert demo_substitution.status_code == 403
    assert db.scalar(select(BrowserJobCapture).where(BrowserJobCapture.profile_id == profile.id)).extension_connection_id == connection["id"]


def test_extension_invalid_expired_and_other_user_session_are_rejected():
    db = session()
    client = client_for(db)
    owner, profile = make_user_profile(db, "owner2@example.test")
    other_user, _ = make_user_profile(db, "intruder@example.test")
    connection = create_extension_connection(db, profile, {"expires_in_days": 7}, owner.id)

    invalid = client.post(
        f"/api/v1/profiles/{profile.id}/job-captures",
        headers={"X-OrganicAI-Extension-Token": "invalid-token"},
        json=capture_payload("invalid"),
    )
    other_user_attempt = client.post(
        f"/api/v1/profiles/{profile.id}/job-captures",
        headers={**auth_headers(db, other_user), "X-OrganicAI-Extension-Token": connection["connection_token"]},
        json=capture_payload("other-user"),
    )

    connection_row = db.get(BrowserExtensionConnection, connection["id"])
    connection_row.expires_at = utc_now_naive() - timedelta(minutes=1)
    db.commit()
    expired = client.post(
        f"/api/v1/profiles/{profile.id}/job-captures",
        headers={"X-OrganicAI-Extension-Token": connection["connection_token"]},
        json=capture_payload("expired"),
    )

    assert invalid.status_code == 403
    assert other_user_attempt.status_code == 403
    assert expired.status_code == 403
    assert db.get(BrowserExtensionConnection, connection["id"]).status == "expired"
