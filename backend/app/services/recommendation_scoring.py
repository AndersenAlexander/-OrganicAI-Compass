WEIGHTS={"profile_match":.25,"goal_alignment":.20,"learning_style_match":.15,"feasibility":.15,"expected_impact":.15,"evidence_quality":.10,"risk_penalty":.15}
def clamp(value):return max(0,min(1,value))
def score_candidate(candidate:dict,ctx:dict,rag_sources:list[dict])->dict:
    title=(candidate["title"]+" "+candidate["summary"]).lower();signals=[*ctx.get("confirmed_strengths",[]),*ctx.get("values",[]),*ctx.get("interests",[]),*ctx.get("learning_preferences",[])];matches=sum(1 for signal in signals if any(word in title for word in str(signal).lower().split()))
    factors={"profile_match":clamp(.55+matches*.08),"goal_alignment":.78 if ctx.get("goals") else .55,"learning_style_match":.76 if ctx.get("learning_preferences") else .5,"feasibility":.9 if candidate["effort"]=="low" else .72,"expected_impact":.85 if candidate["impact"]=="high" else .65,"evidence_quality":min(1,.45+len(rag_sources)*.15),"novelty":.7,"risk_penalty":.08 if candidate["category"]=="ethical_safeguards" else .12}
    relevance=sum(factors[k]*v for k,v in WEIGHTS.items() if k!="risk_penalty")-factors["risk_penalty"]*WEIGHTS["risk_penalty"]
    confidence=clamp(.3+min(5,len(signals))*.08+len(rag_sources)*.08+ctx.get("diagnostic_completeness",.3)*.15)
    return {**candidate,"score_components":factors,"relevance_score":round(clamp(relevance),4),"confidence":round(confidence,4)}
