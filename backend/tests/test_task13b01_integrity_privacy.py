from __future__ import annotations

import os
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth.security import create_access_token
from app.database import Base, get_db
from app.models.auth_security import AuthSession
from app.models.profile import Profile
from app.models.user import User
from app.privacy import service as privacy_service
from app.routers import advanced, privacy, profiles, test_fixtures
from app.services.auth_service import utcnow
from app.services.research_readiness import assert_research_ready, research_readiness


def make_db_app(*routers: tuple[object, str]) -> tuple[TestClient, Session]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = Session(engine)
    app = FastAPI()
    for router, prefix in routers:
        app.include_router(router, prefix=prefix)

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app, base_url="http://testserver"), db


def auth_header(db: Session, email: str, *, is_demo: bool = False) -> tuple[dict[str, str], User]:
    now = utcnow()
    user = User(name=email.split("@", 1)[0], email=email, hashed_password="x", account_status="active", auth_version=1, is_demo=is_demo)
    db.add(user)
    db.flush()
    session = AuthSession(
        user_id=user.id,
        token_family_id=f"family-{user.id}",
        refresh_token_hash=f"hash-{user.id}",
        created_at=now,
        last_used_at=now,
        expires_at=now + timedelta(days=1),
        is_demo=is_demo,
    )
    db.add(session)
    db.commit()
    token = create_access_token({"sub": user.id, "sid": session.id, "ver": user.auth_version})
    return {"Authorization": f"Bearer {token}"}, user


def fixture_settings(*, enabled: bool = True, app_env: str = "test"):
    return type(
        "S",
        (),
        {
            "app_env": app_env,
            "account_deletion_fixture_enabled": enabled,
            "privacy_account_deletion_grace_days": 7,
            "privacy_export_directory": "./tmp/test-exports",
            "privacy_export_expire_hours": 24,
        },
    )()


def test_public_account_deletion_fixture_route_absent_from_privacy_router():
    app = FastAPI()
    app.include_router(privacy.router, prefix="/api/privacy")
    paths = {getattr(route, "path", "") for route in app.routes}
    assert "/api/privacy/account-deletion/{request_id}/execute-fixture" not in paths
    assert TestClient(app).post("/api/privacy/account-deletion/request-id/execute-fixture").status_code == 404


def test_test_only_account_deletion_fixture_requires_synthetic_user(monkeypatch):
    monkeypatch.setattr(privacy_service, "get_settings", lambda: fixture_settings(enabled=True, app_env="test"))
    client, db = make_db_app((privacy.router, "/api/privacy"), (test_fixtures.router, "/api"))
    headers, _user = auth_header(db, "ordinary@organicai.local")
    requested = client.post("/api/privacy/account-deletion", headers=headers, json={"confirmation": "DELETE MY ORGANICAI ACCOUNT"})
    assert requested.status_code == 200
    executed = client.post(f"/api/privacy/account-deletion/{requested.json()['requestId']}/execute-fixture", headers=headers)
    assert executed.status_code == 403


def test_test_only_account_deletion_fixture_executes_for_synthetic_test_user(monkeypatch):
    monkeypatch.setattr(privacy_service, "get_settings", lambda: fixture_settings(enabled=True, app_env="test"))
    client, db = make_db_app((privacy.router, "/api/privacy"), (test_fixtures.router, "/api"))
    headers, _user = auth_header(db, "synthetic@example.test")
    requested = client.post("/api/privacy/account-deletion", headers=headers, json={"confirmation": "DELETE MY ORGANICAI ACCOUNT"})
    assert requested.status_code == 200
    queued = client.get("/api/privacy/requests", headers=headers)
    assert queued.status_code == 200
    assert queued.json()[0]["status"] == "queued"
    executed = client.post(f"/api/privacy/account-deletion/{requested.json()['requestId']}/execute-fixture", headers=headers)
    assert executed.status_code == 200
    assert executed.json()["status"] == "completed"


def test_profile_ownership_denies_other_user_and_null_owned_profiles(monkeypatch):
    monkeypatch.setattr(
        "app.services.profile_authorization.get_settings",
        lambda: type("S", (), {"admin_emails": "admin@example.test", "demo_user_email": "demo@organicai.local"})(),
    )
    client, db = make_db_app((profiles.router, "/api/profiles"))
    owner_headers, owner = auth_header(db, "owner@example.test")
    other_headers, _other = auth_header(db, "other@example.test")
    admin_headers, _admin = auth_header(db, "admin@example.test")
    demo_headers, demo = auth_header(db, "demo@organicai.local", is_demo=True)
    owned = Profile(user_id=owner.id, data={"label": "owned"})
    orphan = Profile(user_id=None, data={"label": "orphan"})
    demo_profile = Profile(user_id=demo.id, data={"label": "demo"})
    db.add_all([owned, orphan, demo_profile])
    db.commit()

    assert client.get(f"/api/profiles/{owned.id}", headers=owner_headers).status_code == 200
    assert client.get(f"/api/profiles/{owned.id}", headers=other_headers).status_code == 403
    assert client.get(f"/api/profiles/{orphan.id}", headers=owner_headers).status_code == 403
    assert client.get(f"/api/profiles/{orphan.id}", headers=admin_headers).status_code == 200
    assert client.get(f"/api/profiles/{demo_profile.id}", headers=demo_headers).status_code == 200
    assert client.get(f"/api/profiles/{owned.id}", headers=demo_headers).status_code == 403
    assert client.patch(
        f"/api/profiles/{owned.id}/feedback",
        headers=other_headers,
        json={"confirmed_nodes": ["x"]},
    ).status_code == 403


def test_advanced_api_requires_authentication_and_does_not_echo_arbitrary_payload():
    client, db = make_db_app((advanced.router, "/api"))
    assert client.post("/api/projects/generate", json={"prompt": "x"}).status_code == 401
    headers, _user = auth_header(db, "advanced@example.test")
    rejected = client.post("/api/projects/generate", headers=headers, json={"prompt": "x", "unexpected": "leak"})
    assert rejected.status_code == 422
    accepted = client.post("/api/projects/generate", headers=headers, json={"prompt": "x", "selections": ["a"]})
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "experimental-concept-demo"
    assert "request" not in accepted.json()


def test_research_readiness_blocks_placeholder_configuration(monkeypatch):
    settings = type(
        "S",
        (),
        {
            "researcher_identity": "placeholder",
            "research_contact": "placeholder",
            "research_storage_duration": "placeholder",
            "research_study_version": "placeholder",
            "research_consent_document_version": "placeholder",
        },
    )()
    readiness = research_readiness(settings)
    assert readiness["ready"] is False
    assert readiness["liveRecruitmentEnabled"] is False
    assert readiness["syntheticEvaluationEnabled"] is True
    monkeypatch.setattr("app.services.research_readiness.get_settings", lambda: settings)
    with pytest.raises(HTTPException):
        assert_research_ready()


def test_importing_app_main_does_not_initialize_database():
    backend_root = Path(__file__).resolve().parents[1]
    code = (
        "import app.database as d\n"
        "def fail():\n"
        "    raise RuntimeError('init_db side effect')\n"
        "d.init_db = fail\n"
        "import app.main\n"
        "print('imported')\n"
    )
    env = {**os.environ, "APP_ENV": "test", "DB_AUTO_CREATE_SCHEMA": "false"}
    result = subprocess.run([sys.executable, "-c", code], cwd=backend_root, env=env, text=True, capture_output=True, timeout=120)
    assert result.returncode == 0, result.stderr
    assert "imported" in result.stdout
