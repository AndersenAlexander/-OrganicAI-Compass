import asyncio
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth.security import decode_access_token, verify_password
from app.database import Base
from app.models.assessment import AssessmentSession, CareerMatch
from app.models.learning import LearningRecommendationRun
from app.models.profile import Profile
from app.models.rag_observability import RagRun
from app.models.recommendation import Recommendation
from app.models.user import User
from app.routers import demo, research
from app.services import demo_seed_service, rag_service


def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def settings(enabled=True, version=1):
    return SimpleNamespace(demo_account_enabled=enabled, demo_user_email="demo@organicai.local", demo_user_password="local-test-password", demo_user_display_name="OrganicAI Demo", demo_dataset_version=version, demo_reset_on_login=False, demo_login_rate_limit=10)


def seed(monkeypatch, db, enabled=True, version=1):
    value = settings(enabled, version)
    monkeypatch.setattr(demo_seed_service, "get_settings", lambda: value)
    monkeypatch.setattr(demo, "get_settings", lambda: value)
    return demo_seed_service.ensure_demo(db)


def test_demo_account_is_hashed_complete_and_idempotent(monkeypatch):
    db = session(); user, profile, roadmap = seed(monkeypatch, db); again = seed(monkeypatch, db)
    assert db.scalar(select(func.count()).select_from(User).where(User.is_demo.is_(True))) == 1
    assert user.id == again[0].id and profile.id == "demo-profile" and roadmap.profile_id == profile.id
    assert user.hashed_password != "local-test-password" and verify_password("local-test-password", user.hashed_password)
    assert user.is_demo and user.demo_dataset_version == 1
    assert db.scalar(select(func.count()).select_from(Recommendation).where(Recommendation.user_id == user.id)) == 4
    assert db.scalar(select(func.count()).select_from(AssessmentSession).where(AssessmentSession.profile_id == profile.id, AssessmentSession.status == "completed")) == 1
    assert db.scalar(select(func.count()).select_from(CareerMatch).where(CareerMatch.profile_id == profile.id)) >= 4
    assert db.scalar(select(func.count()).select_from(LearningRecommendationRun).where(LearningRecommendationRun.profile_id == profile.id)) >= 1


def test_dataset_upgrade_restores_only_demo_user(monkeypatch):
    db = session(); real = User(name="Real", email="real@example.test", hashed_password="unchanged"); db.add(real); db.commit()
    user, _, _ = seed(monkeypatch, db, version=1); seed(monkeypatch, db, version=2)
    assert db.get(User, real.id).hashed_password == "unchanged"
    assert db.get(User, user.id).demo_dataset_version == 2


def test_demo_login_uses_normal_jwt_and_never_returns_password(monkeypatch):
    db = session(); seed(monkeypatch, db); payload = demo.login_payload(db)
    assert decode_access_token(payload["access_token"])["sub"] == payload["user"]["id"]
    assert payload["active_profile_id"] == "demo-profile" and payload["user"]["is_demo"] is True
    assert "password" not in str(payload).lower()


def test_reset_restores_data_without_changing_real_user(monkeypatch):
    db = session(); real = User(name="Real", email="real@example.test", hashed_password="x"); db.add(real); db.commit()
    user, profile, _ = seed(monkeypatch, db); profile.data = {"changed": True}; db.commit()
    _, restored, _ = demo_seed_service.restore_demo(db)
    assert "primary_archetype" in restored.data and db.get(User, real.id).email == "real@example.test"
    assert db.get(User, user.id).is_demo
    assert db.scalar(select(func.count()).select_from(AssessmentSession).where(AssessmentSession.profile_id == restored.id, AssessmentSession.status == "completed")) == 1
    assert db.scalar(select(func.count()).select_from(LearningRecommendationRun).where(LearningRecommendationRun.profile_id == restored.id)) >= 1


def test_non_demo_cannot_reset_and_demo_cannot_export(monkeypatch):
    db = session(); value = settings(); monkeypatch.setattr(demo, "get_settings", lambda: value)
    real = User(name="Real", email="admin@example.test", hashed_password="x", is_demo=False)
    try: asyncio.run(demo.reset_demo(db, real)); assert False
    except HTTPException as error: assert error.status_code == 403
    demo_user = User(name="Demo", email="demo@organicai.local", hashed_password="x", is_demo=True)
    try: research.guard(demo_user); assert False
    except HTTPException as error: assert error.status_code == 403


def test_disabled_demo_mode_rejects_login(monkeypatch):
    monkeypatch.setattr(demo, "get_settings", lambda: settings(False))
    try: demo.require_enabled(); assert False
    except HTTPException as error: assert error.status_code == 404


def test_research_exports_exclude_demo_by_default_and_allow_explicit_filter(monkeypatch):
    db = session(); db.add_all([RagRun(query="real", run_origin="user"), RagRun(query="demo", run_origin="demo")]); db.commit()
    admin = User(name="Admin", email="admin@example.test", hashed_password="x")
    monkeypatch.setattr(research.settings, "research_export_enabled", True); monkeypatch.setattr(research.settings, "admin_emails", admin.email)
    assert [row["query"] for row in research.export_json(admin, db)["runs"]] == ["real"]
    assert {row["query"] for row in research.export_json(admin, db, include_demo=True)["runs"]} == {"real", "demo"}


def test_demo_rag_run_is_marked_and_local_fallback_works(monkeypatch):
    db = session(); user, profile, _ = seed(monkeypatch, db)
    async def fake(_query): return []
    monkeypatch.setattr(rag_service, "search_knowledge_base", fake)
    result = asyncio.run(rag_service.ask_with_rag("demo question", db, user.id, profile.id))
    run = db.get(RagRun, result["rag_run_id"])
    assert run.run_origin == "demo" and run.provider == "local-fallback" and result["insufficient_context"]
