from __future__ import annotations

import json
from urllib.parse import parse_qs, urlparse
from datetime import timedelta
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth.security import bcrypt_context, create_access_token, decode_access_token
from app.database import Base, get_db
from app.models.auth_security import AccountToken, AuthSession
from app.models.provider_operations import EmailDeliveryEvent
from app.models.user import User
from app.routers import auth
from app.services import auth_service
from app.services.auth_service import utcnow


def email_settings(tmp_path: Path):
    return type(
        "S",
        (),
        {
            "email_delivery_driver": "development-outbox",
            "email_development_outbox_dir": str(tmp_path),
            "email_public_base_url": "http://testserver",
            "email_verification_expire_hours": 24,
            "password_reset_expire_minutes": 30,
        },
    )()


def configure_email(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("app.services.email.validation.get_settings", lambda: email_settings(tmp_path))
    monkeypatch.setattr("app.services.email.development_outbox.get_settings", lambda: email_settings(tmp_path))
    monkeypatch.setattr("app.services.email.templates.get_settings", lambda: email_settings(tmp_path))


def token_from_outbox(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    link_line = next(line for line in payload["text"].splitlines() if line.startswith("Open: "))
    return parse_qs(urlparse(link_line.split("Open: ", 1)[1]).query)["token"][0]


def make_client(tmp_path: Path) -> tuple[TestClient, Session]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = Session(engine)
    app = FastAPI()
    app.include_router(auth.router, prefix="/api/auth")

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app, base_url="http://testserver"), db


def test_register_login_refresh_rotation_reuse_and_logout(tmp_path, monkeypatch):
    configure_email(monkeypatch, tmp_path)
    client, db = make_client(tmp_path)
    payload = {"name": "Task Twelve", "email": "task12@example.test", "password": "Correct horse battery staple"}

    registered = client.post("/api/auth/register", json=payload)
    assert registered.status_code == 200
    assert "organicai_refresh" in registered.cookies
    access = registered.json()["access_token"]
    decoded = decode_access_token(access)
    assert decoded["type"] == "access" and decoded["sid"] and decoded["ver"] == 1
    assert db.scalar(select(AuthSession).where(AuthSession.user_id == registered.json()["user"]["id"])).refresh_token_hash

    refreshed = client.post("/api/auth/refresh", headers={"Origin": "http://127.0.0.1:5190"})
    assert refreshed.status_code == 200
    sessions = list(db.scalars(select(AuthSession).order_by(AuthSession.created_at)))
    assert len(sessions) == 2
    assert sessions[0].revoked_at is not None and sessions[0].revocation_reason == "rotated"
    assert sessions[1].revoked_at is None

    stale = TestClient(client.app, base_url="http://testserver")
    stale.cookies.set("organicai_refresh", registered.cookies["organicai_refresh"])
    reused = stale.post("/api/auth/refresh", headers={"Origin": "http://127.0.0.1:5190"})
    assert reused.status_code == 401
    assert all(row.revoked_at is not None for row in db.scalars(select(AuthSession)).all())

    login = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert login.status_code == 200
    listed = client.get("/api/auth/sessions", headers={"Authorization": f"Bearer {login.json()['access_token']}", "Origin": "http://127.0.0.1:5190"})
    assert listed.status_code == 200 and listed.json()[0]["current_session"]
    logout = client.post("/api/auth/logout", headers={"Origin": "http://127.0.0.1:5190"})
    assert logout.status_code == 200


def test_bcrypt_login_upgrades_hash_and_password_change_invalidates_old_access(tmp_path):
    client, db = make_client(tmp_path)
    user = User(name="Legacy", email="legacy@example.test", hashed_password=bcrypt_context.hash("legacy-password-long"), account_status="active")
    db.add(user)
    db.commit()
    login = client.post("/api/auth/login", json={"email": user.email, "password": "legacy-password-long"})
    assert login.status_code == 200
    db.refresh(user)
    assert user.hashed_password.startswith("$argon2")
    old_access = login.json()["access_token"]
    changed = client.post(
        "/api/auth/change-password",
        json={"current_password": "legacy-password-long", "new_password": "new password with enough length"},
        headers={"Authorization": f"Bearer {old_access}", "Origin": "http://127.0.0.1:5190"},
    )
    assert changed.status_code == 200
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {old_access}"}).status_code == 401


def test_password_reset_and_email_verification_tokens_are_hashed_single_use(tmp_path, monkeypatch):
    configure_email(monkeypatch, tmp_path)
    client, db = make_client(tmp_path)
    response = client.post("/api/auth/register", json={"name": "Verify", "email": "verify@example.test", "password": "verification password ok"})
    assert response.status_code == 200
    token_rows = list(db.scalars(select(AccountToken)))
    assert token_rows and not any("verification" in row.token_hash for row in token_rows)
    outbox = sorted(tmp_path.glob("email-*.json"))
    verify_payload = json.loads(outbox[-1].read_text(encoding="utf-8"))
    assert verify_payload["messageType"] == "verify-email"
    assert "token" not in verify_payload["subject"].lower()
    verify_token = token_from_outbox(outbox[-1])
    assert client.post("/api/auth/verify-email", json={"token": verify_token}).status_code == 200
    assert client.post("/api/auth/verify-email", json={"token": verify_token}).status_code == 400

    client.post("/api/auth/forgot-password", json={"email": "verify@example.test"})
    reset_payload = json.loads(sorted(tmp_path.glob("email-*.json"))[-1].read_text(encoding="utf-8"))
    assert reset_payload["messageType"] == "reset-password"
    assert "<a href=" in reset_payload["html"]
    reset_token = token_from_outbox(sorted(tmp_path.glob("email-*.json"))[-1])
    assert client.post("/api/auth/reset-password", json={"token": reset_token, "new_password": "reset password long enough"}, headers={"Origin": "http://127.0.0.1:5190"}).status_code == 200
    assert client.post("/api/auth/reset-password", json={"token": reset_token, "new_password": "another password long enough"}, headers={"Origin": "http://127.0.0.1:5190"}).status_code == 400
    events = list(db.scalars(select(EmailDeliveryEvent).order_by(EmailDeliveryEvent.created_at)).all())
    assert {event.message_type for event in events} >= {"verify-email", "reset-password"}
    assert all(event.recipient_hash and "verify@example.test" not in event.recipient_hash for event in events)


def test_invalid_access_tokens_are_rejected(tmp_path):
    client, db = make_client(tmp_path)
    user = User(name="Disabled", email="disabled@example.test", hashed_password="x", account_status="disabled")
    db.add(user)
    db.flush()
    session = AuthSession(user_id=user.id, token_family_id="family", refresh_token_hash="hash", created_at=utcnow(), expires_at=utcnow() + timedelta(days=1))
    db.add(session)
    db.commit()
    access = create_access_token({"sub": user.id, "sid": session.id, "ver": 1})
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {access}"}).status_code == 401
    wrong_type = create_access_token({"sub": user.id, "sid": session.id, "ver": 1, "type": "refresh"})
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {wrong_type}"}).status_code == 401
