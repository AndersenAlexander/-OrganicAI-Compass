from datetime import datetime
from app.core.time import utc_now_naive
from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.auth.dependencies import get_optional_user
from app.database import get_db
from app.models.diagnostic import Diagnostic
from app.models.career_resilience import CareerEvidenceGap, CareerHypothesis
from app.models.learning import LearningPreferences
from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.models.roadmap_adaptation import RoadmapAction, RoadmapCheckIn, RoadmapEvent, RoadmapVersion
from app.models.recommendation import Recommendation, RecommendationEvent
from app.models.user import User
from app.services.profile_generation import generate_roadmap as build_roadmap
from app.services.profile_authorization import require_owned_profile, require_owned_record
from app.services.roadmap_adaptation import ACTION_STATUSES,HORIZONS,action_public,event,normalize_legacy,propose_recalibration,roadmap_public,snapshot

router=APIRouter(); api_router=APIRouter()
class RoadmapGenerateRequest(BaseModel): profile_id:str
class ActionPayload(BaseModel):
    title:str; description:str=""; horizon:str="thirty_days"; reason:str=""; first_step:str=""; success_criteria:str=""; estimated_minutes:int|None=45; effort:str="medium"; impact:str="medium"; priority:int=3; due_date:str|None=None; scheduled_date:str|None=None; user_notes:str=""; source_type:str="user_created"; recommendation_id:str|None=None; profile_signals:list=Field(default_factory=list); rag_sources:list=Field(default_factory=list); ethical_cautions:list=Field(default_factory=list)
class ActionPatch(BaseModel):
    title:str|None=None;description:str|None=None;horizon:str|None=None;reason:str|None=None;first_step:str|None=None;success_criteria:str|None=None;estimated_minutes:int|None=None;effort:str|None=None;impact:str|None=None;priority:int|None=None;status:str|None=None;due_date:str|None=None;scheduled_date:str|None=None;user_notes:str|None=None;progress_percentage:int|None=None;skip_reason:str|None=None
class RoadmapPatch(BaseModel): status:str|None=None; title:str|None=None; summary:str|None=None
class CheckInPayload(BaseModel): check_in_type:str="quick";energy_level:int|None=Field(None,ge=1,le=5);confidence_level:int|None=Field(None,ge=1,le=5);perceived_progress:int|None=Field(None,ge=1,le=5);main_blocker:str="";what_worked:str="";what_changed:str="";user_note:str=""
class CompletePayload(BaseModel): outcome:str=""
class SkipPayload(BaseModel): reason:str
class PostponePayload(BaseModel): date:str|None=None; reason:str=""; horizon:str|None=None
class ApplyPayload(BaseModel): selected_changes:list[int]|None=None; reason:str="User-approved recalibration"

def require_roadmap(db,id,user):
    item=db.get(Roadmap,id)
    return require_owned_record(item,user,resource_name="Roadmap")
def require_action(db,id,user):
    item=db.get(RoadmapAction,id)
    if not item: raise HTTPException(404,"Roadmap action not found")
    roadmap=require_roadmap(db,item.roadmap_id,user); return item,roadmap
def check_horizon(value):
    if value not in HORIZONS: raise HTTPException(422,"Invalid horizon")
def check_status(value):
    if value not in ACTION_STATUSES: raise HTTPException(422,"Invalid action status")
def checkin_public(c): return {"id":c.id,"roadmap_id":c.roadmap_id,"check_in_type":c.check_in_type,"energy_level":c.energy_level,"confidence_level":c.confidence_level,"perceived_progress":c.perceived_progress,"main_blocker":c.main_blocker,"what_worked":c.what_worked,"what_changed":c.what_changed,"user_note":c.user_note,"created_at":c.created_at.isoformat()}
def roadmap_event_public(item): return {"id":item.id,"roadmap_id":item.roadmap_id,"action_id":item.action_id,"user_id":item.user_id,"event_type":item.event_type,"metadata":item.metadata_json or {},"created_at":item.created_at.isoformat()}


def roadmap_generation_context(db: Session, profile: Profile) -> dict[str, Any]:
    """Read the existing decision-support records without changing their meaning."""
    diagnostic = db.get(Diagnostic, profile.diagnostic_id) if profile.diagnostic_id else None
    hypotheses = db.scalars(
        select(CareerHypothesis)
        .where(CareerHypothesis.profile_id == profile.id, CareerHypothesis.status != "archived")
        .order_by(CareerHypothesis.current_alignment_score.desc(), CareerHypothesis.title)
    ).all()
    hypothesis_titles = {item.id: item.title for item in hypotheses}
    gaps = db.scalars(
        select(CareerEvidenceGap)
        .where(CareerEvidenceGap.profile_id == profile.id)
        .order_by(CareerEvidenceGap.importance.desc(), CareerEvidenceGap.capability_label)
    ).all()
    actionable_gaps = [
        {
            "capability": gap.capability_label or gap.skill_id.replace("_", " ").title(),
            "hypothesis": hypothesis_titles.get(gap.hypothesis_id, "your active career direction"),
            "importance": gap.importance,
            "reason": gap.reason,
            "suggested_action": gap.suggested_action,
        }
        for gap in gaps
        if gap.status not in {"RESOLVED", "CLOSED", "ARCHIVED"}
    ]
    preference = db.scalar(select(LearningPreferences).where(LearningPreferences.profile_id == profile.id))
    preference_label = ""
    if preference:
        formats = ", ".join(str(item) for item in (preference.preferred_content_formats_json or []) if str(item).strip())
        preference_label = f"{formats or 'Mixed'} learning, about {preference.available_hours_per_week:g} hours per week"
    return {
        "diagnostic_label": f"Human Diagnostic {diagnostic.diagnostic_version}" if diagnostic else "Saved Human Potential Map",
        "hypotheses": [{"title": item.title, "version": item.current_version_number} for item in hypotheses[:3]],
        "gaps": actionable_gaps[:4],
        "learning_preference": preference_label,
    }


def grounded_roadmap_data(data: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Map existing hypotheses and evidence gaps into bounded, explainable proposals.

    This deliberately does not score or alter a hypothesis or evidence record; it
    only prevents the legacy generic fallback from discarding their provenance.
    """
    gaps = context.get("gaps") or []
    if not gaps:
        return data

    def labels(gap: dict[str, Any]) -> list[str]:
        output = [
            f"Career Hypothesis: {gap['hypothesis']}",
            f"Evidence Gap: {gap['capability']}",
            f"Diagnostic: {context['diagnostic_label']}",
        ]
        if context.get("learning_preference"):
            output.append(f"Learning preference: {context['learning_preference']}")
        return output

    def proposal(
        gap: dict[str, Any],
        *,
        title: str,
        description: str,
        first_step: str,
        success_criteria: str,
        horizon: str,
        priority: int,
        estimated_minutes: int,
    ) -> dict[str, Any]:
        return {
            "title": title,
            "description": description,
            "reason": f"Priority {priority}: {gap['capability']} is an unresolved evidence gap for the {gap['hypothesis']} hypothesis. {gap['reason']}",
            "first_step": first_step,
            "success_criteria": success_criteria,
            "horizon": horizon,
            "priority": priority,
            "estimated_minutes": estimated_minutes,
            "effort": "low" if estimated_minutes <= 60 else "medium",
            "impact": "high",
            "source_type": "evidence_gap_proposal",
            "source_labels": labels(gap),
            "ethical_cautions": ["This is a proposed evidence-building action; completing it does not by itself confirm professional capability."],
        }

    first = gaps[0]
    second = gaps[1] if len(gaps) > 1 else first
    return {
        **data,
        "seven_days": [
            proposal(
                first,
                title=f"Plan one bounded {first['capability']} evidence task",
                description=f"{first['suggested_action'] or 'Choose one small task that can produce reviewable evidence.'} Keep the scope to a single artefact for {first['hypothesis']}.",
                first_step=f"Spend 30 minutes defining the artefact, review criteria, and a stop point for the {first['capability']} task.",
                success_criteria="A small, reviewable task plan with criteria for what the artefact can and cannot demonstrate.",
                horizon="seven_days",
                priority=1,
                estimated_minutes=30,
            ),
            proposal(
                first,
                title=f"Start a focused {first['capability']} practice session",
                description=f"Complete one time-boxed practice session that contributes to the planned evidence task for {first['hypothesis']}.",
                first_step="Schedule one focused session and record which part needed more evidence or guidance.",
                success_criteria="A short practice note and a partial artefact, including at least one uncertainty to review.",
                horizon="seven_days",
                priority=2,
                estimated_minutes=60,
            ),
        ],
        "thirty_days": [
            proposal(
                second,
                title=f"Complete one reviewable {second['capability']} artefact",
                description=f"Turn the bounded task into one artefact that can be reviewed against the {second['hypothesis']} hypothesis rather than treated as assumed capability.",
                first_step="Choose the smallest artefact format that makes the work and its limitations inspectable.",
                success_criteria="One artefact, a short rationale, and a note describing what evidence remains missing.",
                horizon="thirty_days",
                priority=1,
                estimated_minutes=180,
            ),
        ],
        "six_months": [
            proposal(
                first,
                title=f"Review new evidence for {first['hypothesis']}",
                description=f"Compare the completed artefact and reflection with the original {first['capability']} evidence gap before deciding whether the hypothesis needs more testing.",
                first_step="Collect the artefact, reflection, and any feedback in one place for a user-led review.",
                success_criteria="A recorded review of what changed, what remains uncertain, and whether to continue testing the hypothesis.",
                horizon="six_months",
                priority=1,
                estimated_minutes=60,
            ),
        ],
    }

@router.post("/generate")
async def generate_roadmap(payload:RoadmapGenerateRequest,db:Annotated[Session,Depends(get_db)],current_user:Annotated[User|None,Depends(get_optional_user)]):
    profile=require_owned_profile(db,payload.profile_id,current_user)
    context = roadmap_generation_context(db, profile)
    data = await build_roadmap({**profile.data, "roadmap_generation_context": context})
    data = grounded_roadmap_data(data, context)
    data={**data,"title":"Your Human-AI Growth Roadmap","status":"active","version":1,"summary":data.get("contribution_direction","A flexible guide you can adapt."),"updated_at":utc_now_naive().isoformat()}
    roadmap=Roadmap(user_id=profile.user_id,profile_id=profile.id,data=data); db.add(roadmap);db.flush();normalize_legacy(db,roadmap);snapshot(db,roadmap,"Initial roadmap generated");event(db,roadmap.id,profile.user_id,"roadmap_created");db.commit();return roadmap_public(db,roadmap)

@router.get("/{profile_id}")
async def get_latest_roadmap(profile_id:str,db:Annotated[Session,Depends(get_db)],current_user:Annotated[User|None,Depends(get_optional_user)]):
    profile=require_owned_profile(db,profile_id,current_user)
    item=db.scalar(select(Roadmap).where(Roadmap.profile_id==profile_id).order_by(Roadmap.created_at.desc()))
    if not item:return None
    value=roadmap_public(db,item);db.commit();return value
@router.get("")
async def list_roadmaps(db:Annotated[Session,Depends(get_db)],current_user:Annotated[User|None,Depends(get_optional_user)]):
    if not current_user:return []
    rows=db.scalars(select(Roadmap).where(Roadmap.user_id==current_user.id).order_by(Roadmap.created_at.desc())).all();return [roadmap_public(db,r) for r in rows]

@api_router.get("/roadmaps/{roadmap_id}")
async def get_by_id(roadmap_id:str,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    roadmap=require_roadmap(db,roadmap_id,user);value=roadmap_public(db,roadmap);db.commit();return value
@api_router.patch("/roadmaps/{roadmap_id}")
async def patch_roadmap(roadmap_id:str,payload:RoadmapPatch,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    roadmap=require_roadmap(db,roadmap_id,user);data=dict(roadmap.data or {})
    for key,value in payload.model_dump(exclude_none=True).items():data[key]=value
    data["updated_at"]=utc_now_naive().isoformat();roadmap.data=data;flag_modified(roadmap,"data");event(db,roadmap.id,user.id if user else roadmap.user_id,"roadmap_paused" if payload.status=="paused" else "roadmap_resumed" if payload.status=="active" else "roadmap_updated");db.commit();return roadmap_public(db,roadmap)
@api_router.get("/roadmaps/{roadmap_id}/actions")
async def actions(roadmap_id:str,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    roadmap=require_roadmap(db,roadmap_id,user);normalize_legacy(db,roadmap);db.commit();return [action_public(a) for a in db.scalars(select(RoadmapAction).where(RoadmapAction.roadmap_id==roadmap.id).order_by(RoadmapAction.horizon,RoadmapAction.priority)).all()]
@api_router.post("/roadmaps/{roadmap_id}/actions")
async def create_action(roadmap_id:str,payload:ActionPayload,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    roadmap=require_roadmap(db,roadmap_id,user);check_horizon(payload.horizon)
    if payload.recommendation_id and db.scalar(select(RoadmapAction).where(RoadmapAction.roadmap_id==roadmap.id,RoadmapAction.recommendation_id==payload.recommendation_id)):
        raise HTTPException(409,"This recommendation is already in the roadmap")
    values=payload.model_dump();values["profile_signals_json"]=values.pop("profile_signals");values["rag_sources_json"]=values.pop("rag_sources");values["ethical_cautions_json"]=values.pop("ethical_cautions")
    item=RoadmapAction(roadmap_id=roadmap.id,profile_id=roadmap.profile_id,user_id=roadmap.user_id,**values);db.add(item);db.flush();event(db,roadmap.id,user.id if user else roadmap.user_id,"action_added",item.id,{"source_type":item.source_type});db.commit();return action_public(item)
@api_router.get("/roadmap-actions/{action_id}")
async def get_action(action_id:str,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]): item,_=require_action(db,action_id,user);return action_public(item)
@api_router.patch("/roadmap-actions/{action_id}")
async def patch_action(action_id:str,payload:ActionPatch,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    item,roadmap=require_action(db,action_id,user);values=payload.model_dump(exclude_none=True)
    if "horizon" in values:check_horizon(values["horizon"])
    if "status" in values:check_status(values["status"])
    for key,value in values.items():setattr(item,key,value)
    event(db,roadmap.id,user.id if user else roadmap.user_id,"action_updated",item.id);db.commit();db.refresh(item);return action_public(item)
@api_router.delete("/roadmap-actions/{action_id}")
async def delete_action(action_id:str,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    item,roadmap=require_action(db,action_id,user);event(db,roadmap.id,user.id if user else roadmap.user_id,"action_removed",item.id);db.delete(item);db.commit();return {"status":"removed"}
def transition(item,kind,note=""):
    now=utc_now_naive()
    if kind=="start":item.status="in_progress";item.progress_percentage=max(item.progress_percentage,35)
    elif kind=="complete":item.status="completed";item.progress_percentage=100;item.completed_at=now;item.user_notes=(item.user_notes+"\n"+note).strip()
    elif kind=="skip":item.status="skipped";item.skipped_at=now;item.skip_reason=note
    elif kind=="postpone":item.status="postponed";item.user_notes=(item.user_notes+"\nPostponed: "+note).strip()
@api_router.post("/roadmap-actions/{action_id}/start")
async def start(action_id:str,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    item,roadmap=require_action(db,action_id,user);transition(item,"start");event(db,roadmap.id,user.id if user else roadmap.user_id,"action_started",item.id);db.commit();return action_public(item)
@api_router.post("/roadmap-actions/{action_id}/complete")
async def complete(action_id:str,payload:CompletePayload,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    item,roadmap=require_action(db,action_id,user);transition(item,"complete",payload.outcome);event(db,roadmap.id,user.id if user else roadmap.user_id,"action_completed",item.id,{"outcome":payload.outcome})
    if item.recommendation_id:
        rec=db.get(Recommendation,item.recommendation_id)
        if rec:rec.status="completed";db.add(RecommendationEvent(recommendation_id=rec.id,user_id=user.id if user else None,event_type="completed_from_roadmap",metadata_json={"roadmap_action_id":item.id,"outcome":payload.outcome}))
    db.commit();return action_public(item)
@api_router.post("/roadmap-actions/{action_id}/skip")
async def skip(action_id:str,payload:SkipPayload,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    item,roadmap=require_action(db,action_id,user);transition(item,"skip",payload.reason);event(db,roadmap.id,user.id if user else roadmap.user_id,"action_skipped",item.id,{"reason":payload.reason});db.commit();return action_public(item)
@api_router.post("/roadmap-actions/{action_id}/postpone")
async def postpone(action_id:str,payload:PostponePayload,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    item,roadmap=require_action(db,action_id,user)
    if payload.horizon:check_horizon(payload.horizon);item.horizon=payload.horizon
    item.scheduled_date=payload.date or item.scheduled_date;transition(item,"postpone",payload.reason);event(db,roadmap.id,user.id if user else roadmap.user_id,"action_postponed",item.id,{"date":payload.date,"reason":payload.reason});db.commit();return action_public(item)
@api_router.post("/roadmaps/{roadmap_id}/check-ins")
async def submit_checkin(roadmap_id:str,payload:CheckInPayload,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    roadmap=require_roadmap(db,roadmap_id,user);item=RoadmapCheckIn(roadmap_id=roadmap.id,user_id=user.id if user else roadmap.user_id,profile_id=roadmap.profile_id,**payload.model_dump());db.add(item);db.flush();event(db,roadmap.id,user.id if user else roadmap.user_id,"check_in_submitted",metadata={"energy":item.energy_level});db.commit();return checkin_public(item)
@api_router.get("/roadmaps/{roadmap_id}/check-ins")
async def get_checkins(roadmap_id:str,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    require_roadmap(db,roadmap_id,user);return [checkin_public(c) for c in db.scalars(select(RoadmapCheckIn).where(RoadmapCheckIn.roadmap_id==roadmap_id).order_by(RoadmapCheckIn.created_at.desc())).all()]
@api_router.get("/roadmaps/{roadmap_id}/events")
async def roadmap_events(roadmap_id:str,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    require_roadmap(db,roadmap_id,user);return [roadmap_event_public(item) for item in db.scalars(select(RoadmapEvent).where(RoadmapEvent.roadmap_id==roadmap_id).order_by(RoadmapEvent.created_at.desc())).all()]
@api_router.post("/roadmaps/{roadmap_id}/recalibrate")
async def recalibrate(roadmap_id:str,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    roadmap=require_roadmap(db,roadmap_id,user);proposal=propose_recalibration(db,roadmap);data={**(roadmap.data or {}),"pending_recalibration":proposal};roadmap.data=data;flag_modified(roadmap,"data");event(db,roadmap.id,user.id if user else roadmap.user_id,"recalibration_requested");db.commit();return proposal
@api_router.post("/roadmaps/{roadmap_id}/apply-recalibration")
async def apply_recalibration(roadmap_id:str,payload:ApplyPayload,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    roadmap=require_roadmap(db,roadmap_id,user);proposal=(roadmap.data or {}).get("pending_recalibration")
    if not proposal:raise HTTPException(409,"No recalibration proposal to apply")
    selected=set(payload.selected_changes if payload.selected_changes is not None else range(len(proposal["changes"])))
    for index,change in enumerate(proposal["changes"]):
        if index not in selected:continue
        if change["type"]=="add_action":
            body=change["action"];db.add(RoadmapAction(roadmap_id=roadmap.id,profile_id=roadmap.profile_id,user_id=roadmap.user_id,title=body["title"],description=body.get("description",""),horizon=body.get("horizon","thirty_days"),first_step=body.get("first_step",""),success_criteria=body.get("success_criteria",""),estimated_minutes=body.get("estimated_minutes",30),priority=body.get("priority",3),source_type="recalibration"))
        else:
            item=db.get(RoadmapAction,change["action_id"])
            if item:
                if change["type"]=="postpone_action":transition(item,"postpone",change["reason"])
                if change["type"]=="update_action":
                    for key,value in change.get("patch",{}).items():setattr(item,key,value)
    data={**(roadmap.data or {})};data.pop("pending_recalibration",None);data["last_recalibrated_at"]=utc_now_naive().isoformat();data.setdefault("recalibration_notes",[]).append(proposal["summary"]);roadmap.data=data;flag_modified(roadmap,"data");db.flush();snapshot(db,roadmap,payload.reason);event(db,roadmap.id,user.id if user else roadmap.user_id,"recalibration_applied",metadata={"selected_changes":len(selected)});db.commit();return roadmap_public(db,roadmap)
@api_router.get("/roadmaps/{roadmap_id}/versions")
async def versions(roadmap_id:str,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    require_roadmap(db,roadmap_id,user);return [{"id":v.id,"version_number":v.version_number,"reason":v.reason,"created_at":v.created_at.isoformat()} for v in db.scalars(select(RoadmapVersion).where(RoadmapVersion.roadmap_id==roadmap_id).order_by(RoadmapVersion.version_number.desc())).all()]
@api_router.get("/roadmaps/{roadmap_id}/versions/{version}")
async def version(roadmap_id:str,version:int,db:Annotated[Session,Depends(get_db)],user:Annotated[User|None,Depends(get_optional_user)]):
    require_roadmap(db,roadmap_id,user);item=db.scalar(select(RoadmapVersion).where(RoadmapVersion.roadmap_id==roadmap_id,RoadmapVersion.version_number==version))
    if not item:raise HTTPException(404,"Version not found")
    return {"id":item.id,"version_number":item.version_number,"reason":item.reason,"created_at":item.created_at.isoformat(),"snapshot":item.snapshot_json}

