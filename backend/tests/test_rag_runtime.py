import asyncio
from sqlalchemy import create_engine,select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi import HTTPException
from app.database import Base
from app.models.rag_observability import RagFeedback,RagRun,RagRunSource
from app.models.user import User
from app.routers.rag import save_feedback,save_source_feedback
from app.routers.research import export_csv,export_json,guard,settings as research_settings
from app.schemas.rag_schema import RagFeedbackRequest
from app.services import rag_service
from app.services.rag_service import RagSource

def db_session():
    engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool);Base.metadata.create_all(engine);return Session(engine)
def run(coro):return asyncio.run(coro)
def sources():return [RagSource("c1","responsible_ai","Agency","Human oversight and transparent sources support responsible AI.",.82),RagSource("c2","privacy","Consent","Voice data requires consent and limited retention.",.71)]
def test_rag_run_and_ranked_sources_are_persisted(monkeypatch):
    async def fake(*args,**kwargs):return sources()
    monkeypatch.setattr(rag_service,"search_knowledge_base",fake);db=db_session();result=run(rag_service.ask_with_rag("How should AI remain responsible?",db));record=db.get(RagRun,result["rag_run_id"]);stored=db.scalars(select(RagRunSource).order_by(RagRunSource.rank)).all();assert record.status=="completed";assert record.context_quality=="strong";assert [x.rank for x in stored]==[1,2];assert record.provider=="local-fallback"
def test_low_relevance_returns_explicit_fallback(monkeypatch):
    async def fake(*args,**kwargs):return [RagSource("c1","doc","Section","Unrelated text",.01)]
    monkeypatch.setattr(rag_service,"search_knowledge_base",fake);db=db_session();result=run(rag_service.ask_with_rag("Unknown topic",db));assert result["insufficient_context"] is True;assert result["fallback_reason"]=="no_source_above_threshold";assert result["sources_used"]==[]
def test_answer_feedback_is_created_and_updated(monkeypatch):
    async def fake(*args,**kwargs):return sources()
    monkeypatch.setattr(rag_service,"search_knowledge_base",fake);db=db_session();result=run(rag_service.ask_with_rag("Responsible AI",db));payload=RagFeedbackRequest(rating="helpful");first=run(save_feedback(result["rag_run_id"],payload,db,None));second=run(save_feedback(result["rag_run_id"],RagFeedbackRequest(rating="partially_helpful",reason_code="too_general"),db,None));assert first["id"]==second["id"];assert db.get(RagFeedback,first["id"]).rating=="partially_helpful"
def test_source_feedback_and_unrelated_source_rejection(monkeypatch):
    async def fake(*args,**kwargs):return sources()
    monkeypatch.setattr(rag_service,"search_knowledge_base",fake);db=db_session();result=run(rag_service.ask_with_rag("Responsible AI",db));source=result["sources_used"][0];saved=run(save_source_feedback(result["rag_run_id"],source["source_id"],RagFeedbackRequest(rating="relevant"),db,None));assert saved["saved"]
    other=RagRun(query="other");db.add(other);db.commit()
    try:run(save_source_feedback(other.id,source["source_id"],RagFeedbackRequest(rating="relevant"),db,None));assert False
    except HTTPException as error:assert error.status_code==404
def test_research_exports_require_explicit_admin():
    user=User(name="Researcher",email="research@example.test",hashed_password="x");research_settings.research_export_enabled=False
    try:guard(user);assert False
    except HTTPException as error:assert error.status_code==403
def test_authorized_json_and_csv_exports(monkeypatch):
    db=db_session();db.add(RagRun(query="safe query",status="completed",context_quality="partial"));db.commit();user=User(name="Researcher",email="research@example.test",hashed_password="x");monkeypatch.setattr(research_settings,"research_export_enabled",True);monkeypatch.setattr(research_settings,"admin_emails","research@example.test");monkeypatch.setattr("app.routers.research.research_readiness",lambda:{"ready":True});payload=export_json(user,db);csv_response=export_csv(user,db);assert len(payload["runs"])==1;assert csv_response.media_type=="text/csv"
