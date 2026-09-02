from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth.security import bcrypt_context, verify_and_upgrade_password
from app.database import Base, get_db
from app.models.user import User
from app.routers import auth
from app.services import auth_service


def make_client() -> tuple[TestClient, Session]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = Session(engine)
    application = FastAPI()
    application.include_router(auth.router, prefix="/api/auth")

    def override_db():
        yield db

    application.dependency_overrides[get_db] = override_db
    return TestClient(application), db


def test_registration_and_login_normalize_email_and_preserve_ownership(monkeypatch):
    monkeypatch.setattr(auth_service, "send_verification_email", lambda *_args, **_kwargs: None)
    client, db = make_client()
    password = "OrganicAI-user-password-2026!"

    registered = client.post(
        "/api/auth/register",
        json={"name": "Existing User", "email": "  Existing@Example.test  ", "password": password},
    )
    assert registered.status_code == 200
    body = registered.json()
    assert body["user"]["email"] == "existing@example.test"
    user_id = body["user"]["id"]

    login = client.post("/api/auth/login", json={"email": " EXISTING@EXAMPLE.TEST ", "password": password})
    assert login.status_code == 200
    assert login.json()["user"]["id"] == user_id
    assert db.scalar(select(User).where(User.id == user_id)).email == "existing@example.test"

    current = client.get("/api/auth/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"})
    assert current.status_code == 200
    assert current.json()["id"] == user_id


def test_registration_returns_specific_validation_and_duplicate_errors(monkeypatch):
    monkeypatch.setattr(auth_service, "send_verification_email", lambda *_args, **_kwargs: None)
    client, _db = make_client()

    invalid_email = client.post(
        "/api/auth/register",
        json={"name": "Invalid", "email": "not-an-email", "password": "long enough password"},
    )
    assert invalid_email.status_code == 422

    short = client.post(
        "/api/auth/register",
        json={"name": "Short", "email": "short@example.test", "password": "12345678901"},
    )
    assert short.status_code == 400
    assert short.json()["detail"] == "Password must be at least 12 characters."

    password = "a" * 12
    registered = client.post(
        "/api/auth/register",
        json={"name": "Boundary", "email": "boundary@example.test", "password": password},
    )
    assert registered.status_code == 200

    duplicate = client.post(
        "/api/auth/register",
        json={"name": "Duplicate", "email": " BOUNDARY@EXAMPLE.TEST ", "password": password},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "An account with this email already exists."

    too_long = client.post(
        "/api/auth/register",
        json={"name": "Too Long", "email": "too-long@example.test", "password": "x" * 257},
    )
    assert too_long.status_code == 400
    assert too_long.json()["detail"] == "Password must not exceed 256 characters."


def test_password_policy_supports_unicode_and_rejects_bcrypt_truncation(monkeypatch):
    monkeypatch.setattr(auth_service, "send_verification_email", lambda *_args, **_kwargs: None)
    client, db = make_client()
    unicode_password = "🙂" * 12
    response = client.post(
        "/api/auth/register",
        json={"name": "Unicode", "email": "unicode@example.test", "password": unicode_password},
    )
    assert response.status_code == 200
    stored = db.scalar(select(User).where(User.email == "unicode@example.test"))
    assert stored is not None and stored.hashed_password.startswith("$argon2")
    assert verify_and_upgrade_password(unicode_password, stored.hashed_password)[0]

    legacy_hash = bcrypt_context.hash("a" * 72)
    assert verify_and_upgrade_password("a" * 72, legacy_hash)[0]
    assert verify_and_upgrade_password("a" * 73, legacy_hash) == (False, None)


def test_failed_logins_lock_an_account_without_revealing_its_state(monkeypatch):
    client, db = make_client()
    password = "correct password for lockout"
    user = User(
        name="Lockable",
        email="lockable@example.test",
        hashed_password=auth_service.hash_password(password),
        account_status="active",
        failed_login_count=4,
    )
    db.add(user)
    db.commit()

    monkeypatch.setattr(
        auth_service,
        "get_settings",
        lambda: SimpleNamespace(auth_max_failed_logins=5, auth_lockout_minutes=15),
    )

    invalid = client.post("/api/auth/login", json={"email": user.email, "password": "wrong password"})
    assert invalid.status_code == 401
    db.refresh(user)
    assert user.failed_login_count == 5
    assert user.locked_until is not None

    locked = client.post("/api/auth/login", json={"email": user.email, "password": password})
    assert locked.status_code == 401
    assert locked.json()["detail"] == "Invalid email or password."
