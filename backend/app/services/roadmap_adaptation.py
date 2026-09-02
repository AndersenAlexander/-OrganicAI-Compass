"""Compatibility, progress, and transparent rule-based recalibration helpers."""
from datetime import datetime
from app.core.time import utc_now_naive
from time import perf_counter
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.roadmap import Roadmap
from app.models.roadmap_adaptation import RoadmapAction, RoadmapCheckIn, RoadmapEvent, RoadmapMilestone, RoadmapVersion

HORIZONS = {"seven_days", "thirty_days", "six_months"}
ACTION_STATUSES = {"not_started", "in_progress", "completed", "skipped", "postponed", "blocked", "archived"}

def action_public(item: RoadmapAction) -> dict:
    return {"id":item.id,"roadmap_id":item.roadmap_id,"profile_id":item.profile_id,"user_id":item.user_id,"recommendation_id":item.recommendation_id,"career_experiment_session_id":item.career_experiment_session_id,"career_hypothesis_id":item.career_hypothesis_id,"evidence_gap_id":item.evidence_gap_id,"horizon":item.horizon,"title":item.title,"description":item.description,"reason":item.reason,"first_step":item.first_step,"success_criteria":item.success_criteria,"estimated_minutes":item.estimated_minutes,"effort":item.effort,"impact":item.impact,"priority":item.priority,"status":item.status,"progress_percentage":item.progress_percentage,"due_date":item.due_date,"scheduled_date":item.scheduled_date,"completed_at":item.completed_at.isoformat() if item.completed_at else None,"skipped_at":item.skipped_at.isoformat() if item.skipped_at else None,"skip_reason":item.skip_reason,"user_notes":item.user_notes,"source_type":item.source_type,"profile_signals":item.profile_signals_json or [],"rag_sources":item.rag_sources_json or [],"ethical_cautions":item.ethical_cautions_json or [],"created_at":item.created_at.isoformat(),"updated_at":item.updated_at.isoformat()}

def event(db, roadmap_id, user_id, event_type, action_id=None, metadata=None):
    db.add(RoadmapEvent(roadmap_id=roadmap_id,user_id=user_id,event_type=event_type,action_id=action_id,metadata_json=metadata or {}))

def normalize_legacy(db: Session, roadmap: Roadmap) -> None:
    """Materialize old JSON roadmap sections once without deleting legacy fields."""
    if db.scalar(select(RoadmapAction.id).where(RoadmapAction.roadmap_id==roadmap.id).limit(1)):
        return
    for horizon in HORIZONS:
        raw = roadmap.data.get(horizon, [])
        if isinstance(raw, str): raw = [raw]
        for index, item in enumerate(raw if isinstance(raw, list) else []):
            if isinstance(item, str): item={"title":item,"description":""}
            title=str(item.get("title") or item.get("description") or "Roadmap action")
            db.add(RoadmapAction(
                roadmap_id=roadmap.id,
                profile_id=roadmap.profile_id,
                user_id=roadmap.user_id,
                recommendation_id=item.get("recommendation_id"),
                horizon=horizon,
                title=title,
                description=str(item.get("description") or ""),
                reason=str(item.get("reason") or "Carried forward from your existing roadmap."),
                first_step=str(item.get("first_step") or "Choose a small first step and schedule it."),
                success_criteria=str(item.get("success_criteria") or "Record a short outcome."),
                estimated_minutes=item.get("estimated_minutes") or 45,
                effort=str(item.get("effort") or "medium"),
                impact=str(item.get("impact") or "medium"),
                priority=int(item.get("priority") or index + 1),
                source_type=str(item.get("source_type") or ("recommendation" if item.get("recommendation_id") or item.get("source")=="recommendation" else "legacy_roadmap")),
                profile_signals_json=item.get("source_labels") or item.get("profile_signals") or [],
                rag_sources_json=item.get("rag_sources") or [],
                ethical_cautions_json=item.get("ethical_cautions") or [],
            ))
    db.flush()

def progress(actions):
    active=[a for a in actions if a.status not in {"skipped","archived"}]
    completed=sum(a.status=="completed" for a in actions); in_progress=sum(a.status=="in_progress" for a in actions)
    score=sum(1 if a.status=="completed" else .35 if a.status=="in_progress" else 0 for a in active)
    return {"total_actions":len(actions),"completed_actions":completed,"in_progress_actions":in_progress,"skipped_actions":sum(a.status=="skipped" for a in actions),"blocked_actions":sum(a.status=="blocked" for a in actions),"completion_percentage":round((score/len(active)*100) if active else 0)}

def snapshot(db, roadmap, reason):
    actions=db.scalars(select(RoadmapAction).where(RoadmapAction.roadmap_id==roadmap.id).order_by(RoadmapAction.horizon,RoadmapAction.priority)).all()
    version=int(roadmap.data.get("version",0))+1
    roadmap.data={**roadmap.data,"version":version,"updated_at":utc_now_naive().isoformat()}
    db.add(RoadmapVersion(roadmap_id=roadmap.id,version_number=version,snapshot_json={"roadmap":roadmap.data,"actions":[action_public(a) for a in actions]},reason=reason))

def roadmap_public(db, roadmap):
    normalize_legacy(db,roadmap)
    actions=db.scalars(select(RoadmapAction).where(RoadmapAction.roadmap_id==roadmap.id).order_by(RoadmapAction.horizon,RoadmapAction.priority,RoadmapAction.created_at)).all()
    milestones=db.scalars(select(RoadmapMilestone).where(RoadmapMilestone.roadmap_id==roadmap.id)).all()
    data=roadmap.data or {}; groups={h:[action_public(a) for a in actions if a.horizon==h] for h in HORIZONS}
    return {"id":roadmap.id,"profile_id":roadmap.profile_id,"title":data.get("title","Your Human-AI Growth Roadmap"),"summary":data.get("summary",data.get("contribution_direction","A flexible guide you can change as your goals and energy evolve.")),"status":data.get("status","active"),"version":int(data.get("version",1)),"created_at":roadmap.created_at.isoformat(),"updated_at":data.get("updated_at",roadmap.created_at.isoformat()),"last_recalibrated_at":data.get("last_recalibrated_at"),"progress":progress(actions),"horizons":groups,"milestones":[{"id":m.id,"title":m.title,"description":m.description,"target_date":m.target_date,"status":m.status,"success_criteria":m.success_criteria,"evidence_note":m.evidence_note,"linked_action_ids":m.linked_action_ids,"completed_at":m.completed_at.isoformat() if m.completed_at else None} for m in milestones],"recalibration_notes":data.get("recalibration_notes",[]),"ethical_cautions":data.get("ethical_cautions",[]),"contribution_direction":data.get("contribution_direction",""),"seven_days":groups["seven_days"],"thirty_days":groups["thirty_days"],"six_months":groups["six_months"],"recommended_skills":data.get("recommended_skills",[]),"ai_workflows":data.get("ai_workflows",[]),"project_idea":data.get("project_idea",""),"social_contribution_idea":data.get("social_contribution_idea","")}

def propose_recalibration(db, roadmap):
    started=perf_counter(); actions=db.scalars(select(RoadmapAction).where(RoadmapAction.roadmap_id==roadmap.id)).all(); checkins=db.scalars(select(RoadmapCheckIn).where(RoadmapCheckIn.roadmap_id==roadmap.id).order_by(RoadmapCheckIn.created_at.desc()).limit(3)).all(); changes=[]; rules=[]
    for a in actions:
        if a.status=="skipped" and (a.skip_reason or "").lower() in {"too difficult","blocked"}:
            changes.append({"type":"add_action","action":{"horizon":a.horizon,"title":f"Prepare for: {a.title}","description":"Create a smaller prerequisite before returning to the original action.","first_step":"Spend 15 minutes listing what you need.","success_criteria":"You have one realistic prerequisite.","estimated_minutes":15,"source_type":"recalibration","priority":max(1,a.priority-1)},"reason":"The action was skipped as difficult or blocked."}); rules.append("Skipped difficult/blocked action â†’ propose a smaller prerequisite")
    unstarted=[a for a in actions if a.horizon=="seven_days" and a.status=="not_started"]
    if len(unstarted)>=3:
        for a in unstarted[2:]: changes.append({"type":"postpone_action","action_id":a.id,"reason":"Three or more seven-day actions are still unstarted; reduce immediate workload."})
        rules.append("Three unstarted seven-day actions â†’ postpone lower-priority actions")
    if checkins and checkins[0].energy_level and checkins[0].energy_level<=2:
        for a in unstarted[:1]: changes.append({"type":"update_action","action_id":a.id,"patch":{"estimated_minutes":min(a.estimated_minutes or 30,20)},"reason":"Low energy check-in; make the next action smaller."})
        rules.append("Low energy â†’ reduce the next action scope")
    return {"roadmap_id":roadmap.id,"current_version":int((roadmap.data or {}).get("version",1)),"proposed_version":int((roadmap.data or {}).get("version",1))+1,"summary":"A transparent, rule-based proposal. Nothing changes until you apply it.","changes":changes,"profile_signals_used":[],"check_in_signals_used":[{"energy_level":c.energy_level,"main_blocker":c.main_blocker} for c in checkins],"recommendation_feedback_used":[],"sources_used":[],"ethical_note":"This is a flexible guide, not a judgment of your productivity.","confidence_note":"Rule-based proposal; OpenAI and RAG are optional and were not required.","rules_triggered":rules,"metrics":{"proposal_generation_ms":int((perf_counter()-started)*1000)}}

