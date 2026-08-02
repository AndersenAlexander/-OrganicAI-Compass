from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.diagnostic import Diagnostic
from app.models.profile import Profile
from app.models.recommendation import Recommendation, RecommendationFeedback
from app.models.roadmap import Roadmap

def names(items): return [item.get("name") if isinstance(item,dict) else str(item) for item in items or []]

def build_recommendation_context(db:Session,profile:Profile)->dict:
    data=profile.data;feedback=data.get("user_feedback",{});diagnostic=db.get(Diagnostic,profile.diagnostic_id) if profile.diagnostic_id else None;answers=diagnostic.payload if diagnostic else {}
    primary=data.get("primary_archetype",{});primary_name=feedback.get("archetype_override") or (primary.get("name") if isinstance(primary,dict) else primary)
    strengths=names(data.get("strengths",[]));adjusted=feedback.get("strength_adjustments",{});confirmed=[name for name in strengths if adjusted.get(name,50)>=50]
    previous=db.scalars(select(Recommendation).where(Recommendation.profile_id==profile.id)).all();accepted=[item.title for item in previous if item.status in {"accepted","in_progress","completed"}];rejected=[item.title for item in previous if item.status=="rejected"]
    roadmap=db.scalar(select(Roadmap).where(Roadmap.profile_id==profile.id).order_by(Roadmap.created_at.desc()))
    return {"primary_archetype":primary_name,"confirmed_strengths":confirmed,"values":names(data.get("values",[])),"learning_preferences":answers.get("preferred_learning_style",[]),"ai_experience":answers.get("ai_experience","unknown"),"ai_confidence":answers.get("ai_confidence",0),"tools_used":answers.get("ai_tools_used",[]),"fears":answers.get("fears",data.get("fears",[])),"goals":answers.get("ai_help_goals",[]),"interests":answers.get("interests",[]),"orientations":answers.get("preferred_orientation",[]),"contribution_domains":names(data.get("contribution_domains",[])),"accepted_recommendations":accepted,"rejected_patterns":rejected,"hidden_recommendations":feedback.get("hidden_recommendations",[]),"recent_roadmap_focus":([item.get("title") for key in ("seven_days","thirty_days","six_months") for item in roadmap.data.get(key,[])] if roadmap else []),"feedback_applied":bool(feedback),"diagnostic_completeness":min(1,len([v for v in answers.values() if v])/12) if answers else .35}
