import csv,io
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter,Depends,HTTPException,Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.rag_observability import RagFeedback,RagRun,RagRunSource
from app.models.user import User
router=APIRouter();settings=get_settings()
def guard(user:User):
    if user.is_demo:raise HTTPException(403,"This action is unavailable in Demo Mode.")
    allowed={x.strip().lower() for x in settings.admin_emails.split(",") if x.strip()}
    if not settings.research_export_enabled or user.email.lower() not in allowed:raise HTTPException(403,"Research export is not enabled for this account.")
def query_runs(status=None,context_quality=None,date_from:datetime|None=None,date_to:datetime|None=None,feedback_rating=None,document_name=None,profile_id=None,include_demo:bool=False):
    stmt=select(RagRun).order_by(RagRun.created_at.desc())
    if not include_demo:stmt=stmt.where(RagRun.run_origin!="demo")
    if status:stmt=stmt.where(RagRun.status==status)
    if context_quality:stmt=stmt.where(RagRun.context_quality==context_quality)
    if date_from:stmt=stmt.where(RagRun.created_at>=date_from)
    if date_to:stmt=stmt.where(RagRun.created_at<=date_to)
    if profile_id:stmt=stmt.where(RagRun.profile_id==profile_id)
    if feedback_rating:stmt=stmt.join(RagRun.feedback).where(RagFeedback.rating==feedback_rating)
    if document_name:stmt=stmt.join(RagRun.sources).where(RagRunSource.document_name==document_name)
    return stmt
def flat(run:RagRun):
    answer=[f for f in run.feedback if f.feedback_type=="answer_usefulness"]
    return {"run_id":run.id,"created_at":run.created_at.isoformat(),"query":run.query,"run_origin":run.run_origin,"context_quality":run.context_quality,"retrieved_count":run.retrieved_count,"used_source_count":run.used_source_count,"highest_similarity_score":run.highest_similarity_score,"average_similarity_score":run.average_similarity_score,"retrieval_duration_ms":run.retrieval_duration_ms,"generation_duration_ms":run.generation_duration_ms,"total_duration_ms":run.total_duration_ms,"model":run.generation_model,"insufficient_context":run.insufficient_context,"fallback_reason":run.fallback_reason,"answer_usefulness":answer[-1].rating if answer else None,"answer_grounding":next((f.rating for f in run.feedback if f.feedback_type=="answer_grounding"),None),"source_relevant_count":sum(f.rating=="relevant" for f in run.feedback),"source_not_relevant_count":sum(f.rating=="not_relevant" for f in run.feedback)}
@router.get("/rag-runs")
def list_runs(user:Annotated[User,Depends(get_current_user)],db:Annotated[Session,Depends(get_db)],page:int=Query(1,ge=1),page_size:int=Query(25,ge=1,le=100),status:str|None=None,context_quality:str|None=None):guard(user);items=db.scalars(query_runs(status,context_quality).offset((page-1)*page_size).limit(page_size)).all();return {"page":page,"page_size":page_size,"items":[flat(x) for x in items]}
@router.get("/rag-runs/export.json")
def export_json(user:Annotated[User,Depends(get_current_user)],db:Annotated[Session,Depends(get_db)],status:str|None=None,context_quality:str|None=None,date_from:datetime|None=None,date_to:datetime|None=None,feedback_rating:str|None=None,document_name:str|None=None,profile_id:str|None=None,include_demo:bool=False):guard(user);return {"notice":"Software verification is not empirical user validation.","includes_demo":include_demo,"runs":[flat(x) for x in db.scalars(query_runs(status,context_quality,date_from,date_to,feedback_rating,document_name,profile_id,include_demo)).unique().all()]}
@router.get("/rag-runs/export.csv")
def export_csv(user:Annotated[User,Depends(get_current_user)],db:Annotated[Session,Depends(get_db)],status:str|None=None,context_quality:str|None=None,date_from:datetime|None=None,date_to:datetime|None=None,feedback_rating:str|None=None,document_name:str|None=None,profile_id:str|None=None,include_demo:bool=False):
    guard(user);rows=[flat(x) for x in db.scalars(query_runs(status,context_quality,date_from,date_to,feedback_rating,document_name,profile_id,include_demo)).unique().all()];stream=io.StringIO();fields=["run_id","created_at","query","run_origin","context_quality","retrieved_count","used_source_count","highest_similarity_score","average_similarity_score","retrieval_duration_ms","generation_duration_ms","total_duration_ms","model","insufficient_context","fallback_reason","answer_usefulness","answer_grounding","source_relevant_count","source_not_relevant_count"];writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows);return StreamingResponse(iter([stream.getvalue()]),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=rag-runs.csv"})
@router.get("/rag-runs/{run_id}")
def detail(run_id:str,user:Annotated[User,Depends(get_current_user)],db:Annotated[Session,Depends(get_db)]):
    guard(user);run=db.get(RagRun,run_id)
    if not run:raise HTTPException(404,"RAG run not found.")
    return {"run":flat(run),"answer":run.answer,"confidence_note":run.confidence_note,"ethical_note":run.ethical_note,"prompt_injection_flag":run.prompt_injection_flag,"sources":[{"source_id":s.id,"document_name":s.document_name,"section_title":s.section_title,"excerpt":s.source_excerpt,"similarity_score":s.similarity_score,"rank":s.rank,"used":s.was_used_in_context,"injection_risk":s.injection_risk} for s in run.sources],"feedback":[{"type":f.feedback_type,"rating":f.rating,"reason_code":f.reason_code,"comment":f.comment,"source_id":f.source_id} for f in run.feedback]}
