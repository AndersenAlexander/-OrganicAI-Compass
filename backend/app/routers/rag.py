from typing import Annotated
from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.auth.dependencies import get_optional_user, require_admin_user
from app.database import get_db
from app.models.rag_observability import RagFeedback,RagRun,RagRunSource
from app.models.user import User
from app.schemas.rag_schema import RagAskRequest,RagFeedbackRequest

from app.services.rag_service import ask_with_rag, reindex_knowledge_base, search_knowledge_base

router = APIRouter()


@router.post("/reindex")
async def reindex(_admin: Annotated[User, Depends(require_admin_user)]) -> dict[str, int]:
    return await reindex_knowledge_base()


@router.get("/search")
async def search(query: str = Query(..., min_length=2)) -> dict[str, object]:
    sources = await search_knowledge_base(query)
    return {"query": query, "results": [source.__dict__ for source in sources]}


@router.post("/ask")
async def ask(request:RagAskRequest,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)])->dict[str,object]:
    return await ask_with_rag(request.query,db,user.id if user else None,request.profile_id,request.conversation_id)

def require_run(db:Session,run_id:str,user:User|None)->RagRun:
    run=db.get(RagRun,run_id)
    if not run:raise HTTPException(404,"RAG run not found.")
    if run.user_id and (not user or run.user_id!=user.id):raise HTTPException(403,"Not authorized for this RAG run.")
    return run

@router.post("/runs/{run_id}/feedback")
async def save_feedback(run_id:str,payload:RagFeedbackRequest,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    run=require_run(db,run_id,user);uid=user.id if user else None
    item=db.scalar(select(RagFeedback).where(RagFeedback.rag_run_id==run.id,RagFeedback.user_id==uid,RagFeedback.feedback_type==payload.feedback_type,RagFeedback.source_id.is_(None)))
    if not item:item=RagFeedback(rag_run_id=run.id,user_id=uid,profile_id=payload.profile_id,feedback_type=payload.feedback_type,rating=payload.rating)
    item.rating=payload.rating;item.reason_code=payload.reason_code;item.comment=payload.comment;db.add(item);db.commit();db.refresh(item)
    return {"id":item.id,"rag_run_id":run.id,"feedback_type":item.feedback_type,"rating":item.rating,"saved":True}

@router.post("/runs/{run_id}/sources/{source_id}/feedback")
async def save_source_feedback(run_id:str,source_id:str,payload:RagFeedbackRequest,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    run=require_run(db,run_id,user);source=db.get(RagRunSource,source_id)
    if not source or source.rag_run_id!=run.id:raise HTTPException(404,"Source does not belong to this RAG run.")
    uid=user.id if user else None;item=db.scalar(select(RagFeedback).where(RagFeedback.rag_run_id==run.id,RagFeedback.user_id==uid,RagFeedback.feedback_type=="source_relevance",RagFeedback.source_id==source.id))
    if not item:item=RagFeedback(rag_run_id=run.id,user_id=uid,profile_id=payload.profile_id,feedback_type="source_relevance",rating=payload.rating,source_id=source.id)
    item.rating=payload.rating;item.comment=payload.comment;db.add(item);db.commit();db.refresh(item);return {"id":item.id,"rag_run_id":run.id,"source_id":source.id,"rating":item.rating,"saved":True}

@router.get("/runs/{run_id}/feedback")
async def get_feedback(run_id:str,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    run=require_run(db,run_id,user);items=db.scalars(select(RagFeedback).where(RagFeedback.rag_run_id==run.id)).all();return {"rag_run_id":run.id,"feedback":[{"id":x.id,"feedback_type":x.feedback_type,"rating":x.rating,"reason_code":x.reason_code,"source_id":x.source_id,"comment":x.comment} for x in items]}
