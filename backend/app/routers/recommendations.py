from typing import Annotated, Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.auth.dependencies import get_optional_user
from app.database import get_db
from app.models.profile import Profile
from app.models.recommendation import Recommendation, RecommendationEvent, RecommendationFeedback
from app.models.roadmap import Roadmap
from app.models.roadmap_adaptation import RoadmapAction
from app.models.user import User
from app.services.profile_generation import generate_roadmap_fallback
from app.services.profile_authorization import require_owned_profile, require_owned_record
from app.services.recommendation_engine import generate_recommendations, public
from app.services.recommendation_context import archive_resolved_evidence_gap_recommendations
from app.services.roadmap_adaptation import normalize_legacy, snapshot, event as roadmap_event

router=APIRouter();STATUSES={"suggested","accepted","rejected","in_progress","completed","archived"}
class GenerateRequest(BaseModel):profile_id:str;categories:list[str]=Field(default_factory=list);force_regenerate:bool=False
class PatchRequest(BaseModel):status:str|None=None;user_feedback:str|None=None;user_rating:int|None=Field(default=None,ge=1,le=5)
class FeedbackRequest(BaseModel):rating:int|None=Field(default=None,ge=1,le=5);relevant:bool|None=None;feedback_text:str|None=None;reason_code:str|None=None

def require_profile(db,id,user):
    return require_owned_profile(db,id,user)
def require_rec(db,id,user):
    item=db.get(Recommendation,id)
    return require_owned_record(item,user,resource_name="Recommendation")
def event(db,item,user,event_type,metadata=None):db.add(RecommendationEvent(recommendation_id=item.id,user_id=user.id if user else None,event_type=event_type,metadata_json=metadata or {}))

@router.post("/generate")
async def generate(payload:GenerateRequest,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    profile=require_profile(db,payload.profile_id,user);return await generate_recommendations(db,profile,user.id if user else profile.user_id,payload.categories or None,payload.force_regenerate)

@router.get("/profile/{profile_id}")
async def by_profile(profile_id:str,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)],category:str|None=None,status:str|None=None,limit:int=Query(50,le=100)):
    profile=require_profile(db,profile_id,user);archive_resolved_evidence_gap_recommendations(db,profile);query=select(Recommendation).where(Recommendation.profile_id==profile_id)
    if category:query=query.where(Recommendation.category==category)
    if status:query=query.where(Recommendation.status==status)
    return [public(item) for item in db.scalars(query.order_by(Recommendation.relevance_score.desc()).limit(limit)).all()]

@router.get("/{recommendation_id}")
async def get_one(recommendation_id:str,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    item=require_rec(db,recommendation_id,user);event(db,item,user,"viewed");db.commit();return public(item)

@router.patch("/{recommendation_id}")
async def update(recommendation_id:str,payload:PatchRequest,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    item=require_rec(db,recommendation_id,user)
    if payload.status:
        if payload.status not in STATUSES:raise HTTPException(422,"Invalid status")
        item.status=payload.status;event(db,item,user,payload.status)
    if payload.user_feedback is not None:item.user_feedback=payload.user_feedback
    if payload.user_rating is not None:item.user_rating=payload.user_rating;event(db,item,user,"rated",{"rating":payload.user_rating})
    db.commit();db.refresh(item);return public(item)

async def set_status(id,status,db,user):
    item=require_rec(db,id,user);item.status=status;event(db,item,user,status);db.commit();db.refresh(item);return public(item)
@router.post("/{recommendation_id}/accept")
async def accept(recommendation_id:str,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):return await set_status(recommendation_id,"accepted",db,user)
@router.post("/{recommendation_id}/reject")
async def reject(recommendation_id:str,payload:FeedbackRequest,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    item=require_rec(db,recommendation_id,user);item.status="rejected";item.user_feedback=payload.feedback_text;db.add(RecommendationFeedback(recommendation_id=item.id,user_id=user.id if user else None,rating=payload.rating,relevant=False,feedback_text=payload.feedback_text,reason_code=payload.reason_code));event(db,item,user,"rejected",{"reason_code":payload.reason_code});db.commit();db.refresh(item);return public(item)
@router.post("/{recommendation_id}/complete")
async def complete(recommendation_id:str,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):return await set_status(recommendation_id,"completed",db,user)
@router.post("/{recommendation_id}/feedback")
async def feedback(recommendation_id:str,payload:FeedbackRequest,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    item=require_rec(db,recommendation_id,user);db.add(RecommendationFeedback(recommendation_id=item.id,user_id=user.id if user else None,rating=payload.rating,relevant=payload.relevant,feedback_text=payload.feedback_text,reason_code=payload.reason_code));
    if payload.rating:item.user_rating=payload.rating
    event(db,item,user,"rated",{"rating":payload.rating,"relevant":payload.relevant});db.commit();return {"status":"saved"}

@router.post("/{recommendation_id}/add-to-roadmap")
async def add_to_roadmap(recommendation_id:str,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    item=require_rec(db,recommendation_id,user);roadmap=db.scalar(select(Roadmap).where(Roadmap.profile_id==item.profile_id).order_by(Roadmap.created_at.desc()));created=False
    if not roadmap:roadmap=Roadmap(user_id=item.user_id,profile_id=item.profile_id,data={**generate_roadmap_fallback(),"version":0});db.add(roadmap);db.flush();created=True
    key={"seven_days":"seven_days","thirty_days":"thirty_days","six_months":"six_months"}.get(item.time_horizon,"thirty_days");actions=roadmap.data.setdefault(key,[])
    normalize_legacy(db,roadmap)
    if created:snapshot(db,roadmap,"Initial roadmap created from recommendation")
    structured=db.scalar(select(RoadmapAction).where(RoadmapAction.roadmap_id==roadmap.id,RoadmapAction.recommendation_id==item.id))
    if not structured:
        structured=RoadmapAction(roadmap_id=roadmap.id,profile_id=roadmap.profile_id,user_id=roadmap.user_id,recommendation_id=item.id,horizon=key,title=item.title,description=item.summary,reason=item.reason,first_step=item.first_action,success_criteria="Record what you produced or learned.",estimated_minutes=45,effort="medium",impact="high",priority=1,source_type="recommendation",profile_signals_json=item.profile_signals_json or [],rag_sources_json=item.rag_sources_json or [],ethical_cautions_json=item.ethical_cautions_json or [])
        db.add(structured);roadmap_event(db,roadmap.id,user.id if user else roadmap.user_id,"action_added",structured.id,{"source_type":"recommendation","recommendation_id":item.id})
    if not any(action.get("recommendation_id")==item.id for action in actions):actions.append({"title":item.title,"description":item.first_action,"recommendation_id":item.id,"source":"recommendation"});flag_modified(roadmap,"data")
    item.status="in_progress";event(db,item,user,"added_to_roadmap",{"roadmap_id":roadmap.id,"period":key});db.commit();db.refresh(roadmap);return {"recommendation":public(item),"roadmap":{"id":roadmap.id,**roadmap.data}}
