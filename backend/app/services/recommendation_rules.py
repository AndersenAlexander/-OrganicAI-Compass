CATEGORIES=["skills","learning_paths","human_ai_workflows","practical_projects","contribution_opportunities","seven_day_actions","career_experiments","ethical_safeguards"]

def candidate(category,title,summary,horizon="thirty_days",effort="medium",impact="high",rule="general_profile_match"):
    return {"category":category,"title":title,"summary":summary,"time_horizon":horizon,"effort":effort,"impact":impact,"rule":rule,"estimated_duration":"3–4 weeks" if horizon!="seven_days" else "7 days","prerequisites":[],"first_action":f"Spend 20 minutes defining a small first version of: {title}.","success_indicator":"You can explain what improved, what required human judgment, and what you would change next.","ethical_cautions":["Verify generated claims and references.","Keep final decisions human-led."],"what_to_verify":["Fit with your actual goals and available time"]}

def generate_rule_candidates(ctx:dict,categories:list[str]|None=None,alternative:bool=False)->list[dict]:
    """Transparent rules: visual+design→prototyping; systems+tech→workflow mapping; people+community→facilitation; anxiety+low experience→low-risk practice; advanced confidence→evaluation/orchestration."""
    wanted=set(categories or CATEGORIES);text=" ".join(map(str,ctx.get("interests",[])+ctx.get("orientations",[])+ctx.get("confirmed_strengths",[]))).lower();visual=any(x in text for x in ("visual","design"));systems=any(x in text for x in ("systems","technology"));people=any(x in text for x in ("people","community","care","empathy"));low=str(ctx.get("ai_experience","")).lower() in {"unknown","new to ai","beginner"} or int(ctx.get("ai_confidence",0) or 0)<5
    pool=[candidate("skills","Build verification literacy","Practice checking claims, references, limitations, and uncertainty in AI outputs.",rule="verification_foundation"),candidate("skills","Learn structured AI-assisted prototyping","Generate and compare alternatives while keeping evaluation human-led.",rule="visual_systems" if visual or systems else "profile_match"),candidate("learning_paths","Follow a project-based AI literacy path","Learn through a small artifact connected to your interests.",rule="learning_preference"),candidate("learning_paths","Study responsible human-AI collaboration","Combine practical prompting with privacy, oversight, and verification.",rule="responsible_ai"),candidate("human_ai_workflows","Use an explore–verify–decide workflow","Let AI expand options, verify evidence, then decide against human values.",rule="systems_workflow"),candidate("human_ai_workflows","Create a human-review checklist","Define what AI may suggest and what always requires human approval.",rule="human_oversight"),candidate("practical_projects","Build a small AI-assisted prototype","Compare an AI-assisted version with a human-only version.",rule="visual_prototyping"),candidate("practical_projects","Create an AI literacy guide","Turn your learning into a clear guide for peers or community.",rule="community_learning"),candidate("contribution_opportunities","Facilitate a responsible AI conversation","Help a group identify opportunities, risks, and human-led boundaries.",rule="people_community"),candidate("contribution_opportunities","Contribute a reusable verification checklist","Share a practical resource that improves responsible adoption.",rule="meaningful_contribution"),candidate("seven_day_actions","Run one low-risk AI experiment","Choose a reversible task, test AI support, and record where judgment mattered.","seven_days","low","medium","low_risk_intro"),candidate("seven_day_actions","Map one repetitive workflow","Identify a safe step AI may support without exposing sensitive data.","seven_days","low","medium","workflow_mapping"),candidate("career_experiments","Interview someone using AI responsibly","Explore a real role without committing to a career change.",rule="career_exploration"),candidate("career_experiments","Prototype a future-role task","Test one activity from a role that combines your strengths and AI.",rule="career_experiment"),candidate("ethical_safeguards","Create your personal AI boundary checklist","Define privacy, verification, disclosure, and human-approval rules.","seven_days","low","high","ethical_guardrails"),candidate("ethical_safeguards","Add a verification pause to high-impact work","Require source checking before decisions affecting people.","seven_days","low","high","responsible_ai")]
    if low: pool=[item for item in pool if "orchestration" not in item["title"].lower()]
    if people: pool.sort(key=lambda x:0 if x["category"]=="contribution_opportunities" else 1)

    gaps=ctx.get("evidence_gaps",[]) or []
    hypotheses=ctx.get("active_hypotheses",[]) or []
    preference=next((str(item) for item in (ctx.get("learning_preferences",[]) or []) if str(item).strip()), "")

    def contextualise(item:dict,index:int)->dict:
        result=dict(item)
        gap=gaps[(index + (1 if alternative else 0)) % len(gaps)] if gaps else None
        hypothesis=(gap or (hypotheses[index % len(hypotheses)] if hypotheses else None))
        sources=[]
        if hypothesis:
            title=hypothesis.get("hypothesis") or hypothesis.get("title") or "your active career direction"
            sources.append({"signal":title,"source":"career_hypothesis","weight":0.9})
        else:
            title="your saved profile"
        if gap:
            capability=gap.get("capability") or "current evidence gap"
            sources.append({"signal":capability,"source":"evidence_gap","weight":0.88})
            result["title"]=f"{result['title']} for {capability}"
            result["summary"]=f"{result['summary']} This may help reduce uncertainty around {capability} for {title}."
            result["source_reason"]=f"This may help test the {title} hypothesis by addressing the current {capability} evidence gap. {gap.get('reason') or ''}".strip()
            result["what_to_verify"]=list(result["what_to_verify"])+[f"This does not confirm {capability} as professional capability; review a resulting artefact separately."]
        else:
            result["source_reason"]=f"This may support the available profile signals and the {title} direction; confirm that it fits your current circumstances."
        if preference:
            sources.append({"signal":preference,"source":"user_preference","weight":0.72})
        result["source_context"]=sources
        return result

    return [contextualise(item,index) for index,item in enumerate(pool) if item["category"] in wanted]
