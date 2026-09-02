from datetime import datetime
from app.core.time import utc_now_naive
from time import perf_counter
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.profile import Profile
from app.models.recommendation import Recommendation
from app.services.rag_service import search_knowledge_base
from app.services.recommendation_context import build_recommendation_context
from app.services.recommendation_rules import generate_rule_candidates
from app.services.recommendation_scoring import score_candidate

def public(item:Recommendation)->dict:
    return {"id":item.id,"profile_id":item.profile_id,"category":item.category,"title":item.title,"summary":item.summary,"reason":item.reason,"profile_signals":item.profile_signals_json,"rag_sources":item.rag_sources_json,"relevance_score":item.relevance_score,"confidence":item.confidence,"effort":item.effort,"impact":item.impact,"time_horizon":item.time_horizon,"estimated_duration":item.estimated_duration,"prerequisites":item.prerequisites_json,"first_action":item.first_action,"success_indicator":item.success_indicator,"ethical_cautions":item.ethical_cautions_json,"what_to_verify":item.what_to_verify_json,"status":item.status,"user_rating":item.user_rating,"user_feedback":item.user_feedback,"generation_version":item.generation_version,"score_components":item.score_components_json,"retrieval_metadata":item.retrieval_metadata_json,"created_at":item.created_at.isoformat(),"updated_at":item.updated_at.isoformat()}

def keywords(text):return {word for word in text.lower().split() if len(word)>4}
def action_keywords(text): return keywords(text.split(" for ",1)[0])
def diverse(items:list[dict],max_per_category=1):
    output=[];counts={}
    for item in sorted(items,key=lambda x:x["relevance_score"],reverse=True):
        if counts.get(item["category"],0)>=max_per_category:continue
        if any(len(action_keywords(item["title"])&action_keywords(old["title"]))>=2 for old in output):continue
        output.append(item);counts[item["category"]]=counts.get(item["category"],0)+1
    return output

async def generate_recommendations(db:Session,profile:Profile,user_id:str|None,categories:list[str]|None,force:bool)->dict:
    started=perf_counter();t=perf_counter();ctx=build_recommendation_context(db,profile);context_ms=int((perf_counter()-t)*1000);t=perf_counter();candidates=generate_rule_candidates(ctx,categories,alternative=force);candidate_ms=int((perf_counter()-t)*1000)
    previous=db.scalars(select(Recommendation).where(Recommendation.profile_id==profile.id)).all();blocked=[action_keywords(item.title) for item in previous if item.status=="rejected"]
    candidates=[item for item in candidates if not any(len(action_keywords(item["title"])&words)>=2 for words in blocked)]
    if force:
        seen_titles={item.title.lower() for item in previous}
        candidates=[item for item in candidates if item["title"].lower() not in seen_titles]
    enriched=[];retrieval_started=perf_counter()
    for item in candidates:
        query=f"{item['category']} {item['title']} responsible AI human-centred collaboration"
        try:sources=await search_knowledge_base(query);used=[source for source in sources if source.score>=.10][:2]
        except Exception:used=[]
        rag=[{"document":s.document_name,"section":s.section_title,"snippet":s.chunk_text[:280],"score":round(s.score,4)} for s in used]
        profile_signals=[{"signal":str(signal),"source":"profile_feedback" if signal in ctx.get("confirmed_strengths",[]) else "diagnostic","weight":round(.82-index*.06,2)} for index,signal in enumerate((ctx.get("confirmed_strengths",[])+ctx.get("values",[]))[:4])]
        signals=[*(item.get("source_context") or []),*profile_signals]
        scored=score_candidate(item,ctx,rag);scored.update({"rag_sources":rag,"profile_signals":signals,"retrieval_metadata":{"query":query,"top_score":rag[0]["score"] if rag else 0,"chunks_used":len(rag),"threshold":.10},"reason":item.get("source_reason") or f"This may fit the available signals: {', '.join(x['signal'] for x in signals[:3]) or ctx.get('primary_archetype','your profile')}."});enriched.append(scored)
    retrieval_ms=int((perf_counter()-retrieval_started)*1000);t=perf_counter();ranked=diverse(enriched);scoring_ms=int((perf_counter()-t)*1000);generation_id=str(uuid4());persist_started=perf_counter()
    if force:
        for item in previous:
            if item.status=="suggested":item.status="archived"
    existing_titles={item.title.lower() for item in previous if item.status in {"accepted","in_progress","completed"} or (item.status=="suggested" and not force)}
    saved=[]
    for item in ranked:
        if item["title"].lower() in existing_titles:continue
        record=Recommendation(user_id=user_id,profile_id=profile.id,category=item["category"],title=item["title"],summary=item["summary"],reason=item["reason"],profile_signals_json=item["profile_signals"],rag_sources_json=item["rag_sources"],score_components_json=item["score_components"],retrieval_metadata_json=item["retrieval_metadata"],relevance_score=item["relevance_score"],confidence=item["confidence"],effort=item["effort"],impact=item["impact"],time_horizon=item["time_horizon"],estimated_duration=item["estimated_duration"],prerequisites_json=item["prerequisites"],first_action=item["first_action"],success_indicator=item["success_indicator"],ethical_cautions_json=item["ethical_cautions"],what_to_verify_json=item["what_to_verify"],generation_version="hybrid-v1");db.add(record);saved.append(record)
    db.commit();[db.refresh(item) for item in saved];persistence_ms=int((perf_counter()-persist_started)*1000)
    sources_used=[*ctx.get("confirmed_strengths",[])[:2],*[item["title"] for item in ctx.get("active_hypotheses",[])[:2]],*[item["capability"] for item in ctx.get("evidence_gaps",[])[:2]]]
    return {"profile_id":profile.id,"generation_id":generation_id,"recommendations":[public(item) for item in saved],"generated_at":utc_now_naive().isoformat(),"context_summary":{"profile_signals_used":sources_used,"feedback_applied":ctx.get("feedback_applied",False),"rag_used":any(item.rag_sources_json for item in saved)},"metadata":{"context_build_ms":context_ms,"candidate_generation_ms":candidate_ms,"retrieval_ms":retrieval_ms,"llm_refinement_ms":0,"scoring_ms":scoring_ms,"persistence_ms":persistence_ms,"total_ms":int((perf_counter()-started)*1000),"pipeline":["Profile Context","Feedback Overrides","Candidate Generation","RAG Retrieval","Scoring","Diversity Filter","Explanation","User Feedback"]}}

