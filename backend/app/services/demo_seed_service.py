from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from app.auth.security import hash_password, verify_password
from app.config import get_settings
from app.models.assessment import (
    AIReadinessResult,
    AssessmentInterpretation,
    AssessmentResponse,
    AssessmentScore,
    AssessmentSession,
    CareerComparison,
    CareerDecision,
    CareerInterestResult,
    CareerMatch,
    CareerMatchFactor,
    ChangeReadinessResult,
    PersonalityResult,
    SkillEvidence,
    SkillsInventory,
    WorkValueResult,
)
from app.models.career_resilience import CareerExperimentSession
from app.models.conversation import Conversation
from app.models.diagnostic import Diagnostic
from app.models.fear_transform import FearTransformRecord
from app.models.learning import (
    LearningObjective,
    LearningPath,
    LearningPathItem,
    LearningPathPhase,
    LearningPreferences,
    LearningRecommendation,
    LearningRecommendationFactor,
    LearningRecommendationRun,
    LearningResourceComparison,
    LearningResourceFeedback,
    PracticalProject,
    RoadmapLearningAction,
    SkillGapAnalysis,
    SkillGapItem,
)
from app.models.message import Message
from app.models.interview_journey import Interview
from app.models.market_application import JobApplication
from app.models.profile import Profile
from app.models.rag_observability import RagRun
from app.models.recommendation import Recommendation, RecommendationEvent, RecommendationFeedback
from app.models.roadmap import Roadmap
from app.models.roadmap_adaptation import RoadmapAction, RoadmapCheckIn, RoadmapEvent, RoadmapMilestone, RoadmapVersion
from app.models.user import User
from app.services.assessment_engine import assessment_definition, complete_assessment_session, upsert_responses
from app.services.profile_generation import assessment_prefill, natural_discovery_snapshot
from app.services.learning_engine import (
    add_feedback,
    add_recommendation_to_roadmap,
    create_learning_resource_comparison,
    create_skill_gap_analysis,
    ensure_learning_preferences,
    generate_learning_path,
    generate_learning_recommendations,
    set_recommendation_status,
    update_learning_path_item_progress,
)
from app.services.career_resilience_engine import (
    create_experiment_session,
    create_immediate_action_plan,
    create_supported_paths,
    delete_career_resilience_for_profiles,
    ensure_hypotheses_from_matches,
    evaluate_experiment,
    generate_support_brief,
    recalibrate_career_recommendations,
    run_support_screening,
    self_review_experiment,
    start_experiment,
    submit_experiment,
    sync_career_resilience_catalogue,
    upsert_job_loss_profile,
)
from app.services.market_application_engine import (
    delete_market_application_for_profiles,
    seed_demo_market_application,
)
from app.services.interview_journey_engine import (
    delete_interview_journey_for_profiles,
    seed_demo_interview_journey,
)
from app.services.innovation_extension_engine import (
    delete_innovation_extension_for_profiles,
    seed_demo_innovation_extension,
)
from app.services.originality_research_engine import (
    delete_originality_research_for_profiles,
    seed_demo_originality_research,
)

DEMO_PROFILE_ID="demo-profile"
DEMO_DIAGNOSTIC_ID="demo-diagnostic"

def is_demo_user(user: User | None) -> bool: return bool(user and user.is_demo)

def diagnostic_payload(): return {"interests":["human-centred artificial intelligence","interior and digital design","creative technology","education","ethical innovation","future of work"],"natural_activities":["visualizing complex ideas","designing meaningful experiences","connecting people and technology","learning new digital tools","building interdisciplinary concepts"],"problems_noticed":["fear and confusion about AI","fragmented learning resources","lack of personalized guidance","difficulty translating AI knowledge into practical action"],"preferred_orientation":["creative","strategic","human-centred","interdisciplinary"],"career_interests":{"realistic":3,"investigative":5,"artistic":5,"social":4,"enterprising":3,"conventional":2},"fears":["professional displacement","loss of human creativity","overdependence on automated systems","misuse of personal data","unequal access to AI opportunities"],"ai_threat_or_opportunity":"AI can become a major opportunity when it augments human creativity and remains transparent, responsible, and user-controlled.","values":["creativity","human dignity","responsibility","learning","contribution","collaboration","autonomy"],"contribution_if_supported":"Create understandable, ethical, and visually engaging AI systems that help people adapt and grow.","skills":["design thinking","visual communication","spatial thinking","software development","research","systems thinking","empathy","concept development"],"preferred_learning_style":["visual","project-based","conversational","practical experimentation"],"cognitive_style":["systems-oriented","reflective","creative","strategic"],"ai_experience":"Intermediate","ai_help_goals":["develop meaningful AI products","improve technical confidence","create a structured learning roadmap","combine design and software engineering","prepare for future work"],"preferred_interaction":"both"}

def profile_payload():
    diagnostic = diagnostic_payload()
    return {"natural_discovery_snapshot": natural_discovery_snapshot(diagnostic), "assessment_prefill": assessment_prefill(diagnostic), "human_potential_sections": {"career_interests": "RIASEC-inspired Career Interests: Artistic and Investigative are high, Social is moderate-high, Enterprising and Realistic are moderate, and Conventional is lower.", "natural_tendencies": "Creative, strategic, human-centred and interdisciplinary preferences.", "current_capabilities": "Design, research, communication, and developing software/AI capability.", "evidence_overview": "Demo project evidence is intentionally distinct from self-reported capability.", "development_opportunities": "Career experiments test AI product-design and RAG directions."}, "primary_archetype":{"name":"The Visionary Architect","summary":"Your answers suggest visual imagination, systems thinking, empathy, and practical execution. Treat this as a preference-oriented discovery signal, not a fixed identity.","confidence":.92,"signals":["visual systems","future-oriented thinking","responsible innovation"]},"secondary_archetype":{"name":"The Human-Centred Systems Builder","summary":"You connect people, systems, and practical experimentation.","confidence":.86,"signals":["empathy","systems thinking"]},"strengths":[{"name":"Strategic Thinking","score":94,"explanation":"Connects future possibilities with practical priorities.","evidence":[]},{"name":"Creative Problem Solving","score":91,"explanation":"Generates meaningful alternatives.","evidence":[]},{"name":"Empathy and Influence","score":88,"explanation":"Keeps people visible in technical change.","evidence":[]},{"name":"Systems Thinking","score":84,"explanation":"Sees relationships across a complex product.","evidence":[]},{"name":"Adaptability","score":82,"explanation":"Learns through change and experimentation.","evidence":[]}],"values":[{"name":name,"score":90-i*2,"evidence":[]} for i,name in enumerate(["Human Dignity","Creativity","Responsible Innovation","Learning","Autonomy","Meaningful Contribution"])],"fears":diagnostic["fears"],"creative_tendencies":["conceptual synthesis","visual storytelling","organic and systems-based design","interdisciplinary experimentation","future-oriented thinking"],"ai_collaboration_style":{"name":"Co-Creator","summary":"You work best with AI as an iterative creative and analytical partner. You prefer to generate alternatives, refine ideas, evaluate implications, and keep final judgment under human control.","strengths":["ideation","evaluation"],"cautions":["Keep final judgment human-led"],"recommended_uses":["Generate and compare alternatives"],"human_led_decisions":["authorship","values","final selection"]},"contribution_domains":[{"name":name,"score":score,"explanation":"A current exploratory domain for meaningful contribution."} for name,score in [("Future of Work",95),("Human-AI Collaboration",92),("Education and Learning",88),("Sustainable Innovation",84)]],"recommended_learning_paths":[{"name":name,"level":level,"duration":duration,"reason":"Build practical, responsible capability."} for name,level,duration in [("AI Collaboration Mastery","Intermediate","6 weeks"),("Designing the Future","Advanced","8 weeks"),("Leadership in the Age of AI","Intermediate","5 weeks")]],"uncertainties":[],"risk_notes":["Avoid trying to master too many fields simultaneously.","Validate ambitious ideas through small prototypes.","Maintain boundaries between AI assistance and human judgment.","Review privacy implications before using personal or voice data."],"ethical_note":"This is an exploratory profile. You can confirm, correct, or expand it."}

def roadmap_payload(): return {"title":"My Personal Roadmap","summary":"A practical, human-centred direction for Alex Demo.","version":1,"status":"active","contribution_direction":"Build and evaluate a human-centred AI guidance platform combining voice interaction, RAG, personalization, and adaptive roadmaps.","recommended_skills":["RAG architecture","AI evaluation","accessibility","responsible AI","conversational interface design","React and FastAPI architecture","user research","product strategy"],"project_idea":"Build and evaluate a human-centred AI guidance platform combining voice interaction, RAG, personalization, and adaptive roadmaps.","social_contribution_idea":"Provide understandable AI-literacy guidance for professionals and adults adapting to technological change.","ethical_cautions":["Clearly label AI-generated recommendations.","Preserve user choice.","Protect voice and diagnostic data.","Communicate uncertainty."],"recalibration_notes":[],"growth_score":78,"harmony_score":92,"potential_intelligence_score":89,"alignment":92,"growth_momentum":24,"current_streak":28,"focus":"Deep Work","energy":"High"}

def delete_assessment_for_profiles(db: Session, profile_ids: list[str]) -> None:
    ids=[pid for pid in profile_ids if pid]
    if not ids:return
    match_ids=db.scalars(select(CareerMatch.id).where(CareerMatch.profile_id.in_(ids))).all()
    inventory_ids=db.scalars(select(SkillsInventory.id).where(SkillsInventory.profile_id.in_(ids))).all()
    if match_ids:db.execute(delete(CareerMatchFactor).where(CareerMatchFactor.match_id.in_(match_ids)))
    if inventory_ids:db.execute(delete(SkillEvidence).where(SkillEvidence.skill_inventory_id.in_(inventory_ids)))
    for model in [CareerDecision,CareerComparison,CareerMatch,AssessmentInterpretation,ChangeReadinessResult,AIReadinessResult,WorkValueResult,CareerInterestResult,PersonalityResult,SkillsInventory,AssessmentScore,AssessmentResponse,AssessmentSession]:
      db.execute(delete(model).where(model.profile_id.in_(ids)))

def delete_learning_for_profiles(db: Session, profile_ids: list[str]) -> None:
    ids=[pid for pid in profile_ids if pid]
    if not ids:return
    recommendation_ids=db.scalars(select(LearningRecommendation.id).where(LearningRecommendation.profile_id.in_(ids))).all()
    path_ids=db.scalars(select(LearningPath.id).where(LearningPath.profile_id.in_(ids))).all()
    phase_ids=db.scalars(select(LearningPathPhase.id).where(LearningPathPhase.learning_path_id.in_(path_ids))).all() if path_ids else []
    if recommendation_ids:
      db.execute(delete(LearningRecommendationFactor).where(LearningRecommendationFactor.recommendation_id.in_(recommendation_ids)))
      db.execute(delete(LearningResourceFeedback).where(LearningResourceFeedback.recommendation_id.in_(recommendation_ids)))
    db.execute(delete(LearningResourceFeedback).where(LearningResourceFeedback.profile_id.in_(ids)))
    if phase_ids:db.execute(delete(LearningPathItem).where(LearningPathItem.phase_id.in_(phase_ids)))
    if path_ids:db.execute(delete(LearningPathPhase).where(LearningPathPhase.learning_path_id.in_(path_ids)))
    for model in [RoadmapLearningAction,LearningResourceComparison,LearningPath,PracticalProject,LearningRecommendation,LearningRecommendationRun,LearningObjective,SkillGapItem,SkillGapAnalysis,LearningPreferences]:
      db.execute(delete(model).where(model.profile_id.in_(ids)))

def demo_assessment_responses() -> list[dict]:
    definition=assessment_definition(); responses=[]
    high_personality={"openness":5,"conscientiousness":4,"extraversion":3,"agreeableness":4,"emotional_stability":4}
    high_interests={"artistic":5,"investigative":5,"social":4,"enterprising":3,"realistic":3,"conventional":2}
    values={"creativity":5,"autonomy":5,"meaningful_impact":5,"continuous_learning":5,"collaboration":4,"flexibility":4,"work_life_balance":4,"stability":3,"income":3,"leadership":3,"recognition":2,"predictable_structure":2}
    skills={"software_development":2,"data_analysis":1,"ai_tools":2,"apis":1,"databases":1,"cybersecurity":0,"automation":1,"graphic_design":3,"ux_ui":3,"architecture":3,"writing":2,"visual_communication":3,"video":1,"ideation":3,"research":2,"critical_thinking":3,"systems_thinking":3,"problem_solving":3,"evaluation":2,"communication":3,"teaching":2,"empathy":3,"negotiation":2,"teamwork":3,"client_relations":3,"planning":3,"leadership":2,"budgeting":1,"coordination":3,"quality_assurance":2}
    evidence={"visual_communication":"supported_by_project","ux_ui":"supported_by_project","architecture":"supported_by_experience","communication":"supported_by_experience","coordination":"supported_by_experience","software_development":"supported_by_project","ai_tools":"supported_by_project","systems_thinking":"supported_by_experience"}
    text_values={"background_current_profession":"Interior and digital experience designer","background_projects":"Academic software engineering project, human-centred AI platform prototype, visual design portfolio.","goals_desired_area":"AI product design, UX for AI systems, creative AI technology","goals_market":"European remote or hybrid market","goals_salary":"Optional; depends on role and country","goals_languages":"Romanian, English","goals_accessibility":"","background_experience":"5-9","goals_work_mode":"hybrid","goals_timeline":"6-12 months","goals_weekly_time":"6-10 hours","goals_budget":"low","goals_learning_format":"project-based","goals_relocate":"maybe","goals_entrepreneurship":"medium"}
    ai={"ai_literacy_llm":4,"ai_literacy_hallucinations":4,"ai_literacy_sources":4,"ai_literacy_privacy":4,"ai_literacy_limits":3,"ai_readiness_prompts":4,"ai_readiness_workflows":4,"ai_readiness_tools":3,"ai_readiness_api":2,"ai_readiness_learning":5}
    change={"change_motivation":5,"change_time":4,"change_study":5,"change_uncertainty":3,"change_adjacent_role":4,"change_budget":3,"change_remote_preference":4}
    for item in definition["items"]:
      value=None
      if item["item_type"]=="likert":
        if item["module_id"]=="personality_work_style":
          value=2 if item["reverse_scored"] else high_personality.get(item["dimension"],3)
        elif item["module_id"]=="career_interests":value=high_interests.get(item["dimension"],3)
        elif item["module_id"]=="ai_literacy_readiness":value=ai.get(item["id"],3)
        elif item["module_id"]=="change_readiness":value=change.get(item["id"],3)
      elif item["item_type"]=="value_rating":value=values.get(item["dimension"],3)
      elif item["item_type"]=="skill_level":
        skill=item["dimension"];value={"level":skills.get(skill,0),"evidence_status":evidence.get(skill,"self_reported"),"note":"Demo evidence only; no real personal data."}
      elif item["item_type"] in {"text","long_text","single_select"}:value=text_values.get(item["id"],"")
      if value is not None:responses.append({"item_id":item["id"],"module_id":item["module_id"],"response_type":item["item_type"],"value":value})
    return responses

def seed_demo_assessment(db: Session, user: User, profile: Profile) -> None:
    session=AssessmentSession(profile_id=profile.id,user_id=user.id,mode="complete",status="in_progress",consent_accepted=True,source_type="demo",demo_marker=True)
    db.add(session);db.flush();upsert_responses(db,session,demo_assessment_responses());complete_assessment_session(db,session,profile)

def seed_demo_learning(db: Session, user: User, profile: Profile) -> None:
    match=db.scalar(select(CareerMatch).where(CareerMatch.profile_id==profile.id,CareerMatch.role_template_id=="human_centred_ai_product_designer").order_by(CareerMatch.alignment_score.desc()))
    if not match:match=db.scalar(select(CareerMatch).where(CareerMatch.profile_id==profile.id,CareerMatch.category!="augment_current_profession").order_by(CareerMatch.alignment_score.desc()))
    if not match:return
    match.status="saved";match.user_priority=5;db.commit()
    preferences=ensure_learning_preferences(db,profile)
    preferences.preferred_language="en";preferences.acceptable_secondary_languages_json=["ro"];preferences.free_only=False;preferences.max_budget_per_course=50;preferences.monthly_learning_budget=50;preferences.available_hours_per_week=8;preferences.preferred_content_formats_json=["Project-based","Text","Video"];preferences.theory_practice_preference="practical";preferences.certificate_importance="medium";preferences.provider_exclusions_json=[];db.commit()
    create_skill_gap_analysis(db,profile,match.id)
    run=generate_learning_recommendations(db,profile,match.id)
    recommendations=db.scalars(select(LearningRecommendation).where(LearningRecommendation.run_id==run["id"]).order_by(LearningRecommendation.rank_position)).all()
    if recommendations:
      set_recommendation_status(db,recommendations[0],"saved","saved","Demo resource saved for later review.")
      add_recommendation_to_roadmap(db,recommendations[0],{"roadmap_title":"Learning Action: AI product-design evidence","learning_objective":"Build practical evidence for the selected career direction.","weekly_commitment":"4 hours/week","priority":2,"expected_evidence":"Portfolio note, project artifact, and reflection."})
      add_feedback(db,recommendations[0],{"reason_code":"too_theoretical","feedback_text":"Demo feedback: prefer practical follow-up resources."})
    if len(recommendations)>1:set_recommendation_status(db,recommendations[1],"rejected","too_long","Demo rejection: too long for the current time budget.")
    if len(recommendations)>=3:create_learning_resource_comparison(db,profile,[item.id for item in recommendations[:3]],{"project_component":1.25,"cost_type":1.1})
    path=generate_learning_path(db,profile,run["id"])
    if path.get("phases"):
      first_item=next((item for phase in path["phases"] for item in phase["items"]),None)
      if first_item:
        item=db.get(LearningPathItem,first_item["id"])
        update_learning_path_item_progress(db,item,{"status":"completed","progress_percentage":100,"completion_date":"2026-07-20","evidence_url":"/learning/demo/evidence/ai-product-design-note","reflection":"Demo progress: completed a short summary and selected a practical follow-up project.","difficulty_feedback":"useful","relevance_feedback":"relevant"})

def seed_demo_career_resilience(db: Session, user: User, profile: Profile) -> None:
    sync_career_resilience_catalogue(db)
    match=db.scalar(select(CareerMatch).where(CareerMatch.profile_id==profile.id,CareerMatch.role_template_id=="human_centred_ai_product_designer").order_by(CareerMatch.alignment_score.desc()))
    completed=create_experiment_session(db,profile,{"experiment_template_id":"ai-product-explainable-recommendation-interface","career_match_id":match.id if match else None,"mode":"guided","user_confirmed":True,"add_to_roadmap":True,"demo_marker":True},user.id)
    completed_session=db.get(CareerExperimentSession,completed["id"])
    start_experiment(db,completed_session)
    submit_experiment(db,completed_session,{"text_response":"Designed a responsive explainable recommendation card with reason, supporting evidence, uncertainty, limitations, correction, reject, alternative, and roadmap states. The rationale focuses on user agency, accessibility, source traceability, and transparent uncertainty. I would validate the card with a short usability task and compare whether users understand why the recommendation is a hypothesis.","project_url":"https://example.test/demo/explainable-ai-card","completion_notes":"Demo evidence only. The artifact is a synthetic portfolio-style note for the demo profile.","time_spent_minutes":180,"ai_tools_used":["ChatGPT"],"assistance_level":"brainstorming_and_critique","self_rated_difficulty":3,"self_rated_enjoyment":5,"confidence_before":3,"confidence_after":4,"reflection":{"interest":"The explainability and interaction design work felt energising.","uncertainty":"More product analytics and AI evaluation evidence is still needed."}})
    self_review_experiment(db,completed_session,{"reflection":"The role task felt aligned with design, responsible AI, and user-control interests. It remains a hypothesis until more technical evaluation evidence is added.","self_rated_difficulty":3,"self_rated_enjoyment":5,"confidence_before":3,"confidence_after":4})
    evaluated=evaluate_experiment(db,completed_session)
    if evaluated.get("result"):
      recalibrate_career_recommendations(db,profile,evaluated["result"]["id"])
    in_progress=create_experiment_session(db,profile,{"experiment_template_id":"rag-developer-retrieval-pipeline-spec","mode":"independent","user_confirmed":True,"add_to_roadmap":False,"demo_marker":True},user.id)
    in_progress_session=db.get(CareerExperimentSession,in_progress["id"])
    start_experiment(db,in_progress_session)
    upsert_job_loss_profile(db,profile,{"consent_accepted":True,"country_of_residence":"Norway","country_of_employment":"Norway","municipality_or_region":"Oslo","last_working_date":"2026-07-15","contract_termination_type":"terminated","employment_status":"unemployed","reduction_in_working_hours":100,"jobseeker_registration_status":"not_registered","current_benefits":[],"work_permit_or_residency_status":"","education":"Master student with design and software engineering background","training_interest":"yes","availability_for_work":"yes","relocation_preferences":"Hybrid or remote preferred"})
    create_immediate_action_plan(db,profile)
    run_support_screening(db,profile,{})
    create_supported_paths(db,profile,{})
    generate_support_brief(db,profile)

def restore_demo(db: Session) -> tuple[User,Profile,Roadmap]:
    s=get_settings(); user=db.scalar(select(User).where(User.email==s.demo_user_email.lower()))
    if not user: user=User(name=s.demo_user_display_name,email=s.demo_user_email.lower(),hashed_password=hash_password(s.demo_user_password),is_demo=True,demo_dataset_version=s.demo_dataset_version);db.add(user);db.flush()
    else: user.name=s.demo_user_display_name;user.is_demo=True;user.demo_dataset_version=s.demo_dataset_version
    profile_ids=[p.id for p in db.scalars(select(Profile).where(Profile.user_id==user.id)).all()]
    roadmap_ids=[r.id for r in db.scalars(select(Roadmap).where(Roadmap.user_id==user.id)).all()]
    recommendation_ids=[r.id for r in db.scalars(select(Recommendation).where(Recommendation.user_id==user.id)).all()]
    conversation_ids=[c.id for c in db.scalars(select(Conversation).where(Conversation.user_id==user.id)).all()]
    cleanup_profile_ids=profile_ids+[DEMO_PROFILE_ID]
    if recommendation_ids:
      db.execute(delete(RecommendationFeedback).where(RecommendationFeedback.recommendation_id.in_(recommendation_ids)));db.execute(delete(RecommendationEvent).where(RecommendationEvent.recommendation_id.in_(recommendation_ids)));db.execute(delete(Recommendation).where(Recommendation.id.in_(recommendation_ids)))
    db.execute(delete(RagRun).where(RagRun.user_id==user.id,RagRun.run_origin=="demo"))
    delete_career_resilience_for_profiles(db,cleanup_profile_ids)
    if roadmap_ids:
      roadmap_action_ids=select(RoadmapAction.id).where(RoadmapAction.roadmap_id.in_(roadmap_ids))
      db.execute(delete(RoadmapLearningAction).where(RoadmapLearningAction.roadmap_action_id.in_(roadmap_action_ids)))
      for model,column in [(RoadmapAction,RoadmapAction.roadmap_id),(RoadmapCheckIn,RoadmapCheckIn.roadmap_id),(RoadmapEvent,RoadmapEvent.roadmap_id),(RoadmapMilestone,RoadmapMilestone.roadmap_id),(RoadmapVersion,RoadmapVersion.roadmap_id)]: db.execute(delete(model).where(column.in_(roadmap_ids)))
      db.execute(delete(Roadmap).where(Roadmap.id.in_(roadmap_ids)))
    delete_originality_research_for_profiles(db,cleanup_profile_ids)
    delete_innovation_extension_for_profiles(db,cleanup_profile_ids)
    delete_interview_journey_for_profiles(db,cleanup_profile_ids)
    delete_market_application_for_profiles(db,cleanup_profile_ids)
    delete_learning_for_profiles(db,cleanup_profile_ids)
    delete_assessment_for_profiles(db,cleanup_profile_ids)
    if profile_ids: db.execute(delete(FearTransformRecord).where(FearTransformRecord.profile_id.in_(profile_ids)));db.execute(delete(Profile).where(Profile.id.in_(profile_ids)))
    if conversation_ids: db.execute(delete(Message).where(Message.conversation_id.in_(conversation_ids)))
    db.execute(delete(Diagnostic).where(Diagnostic.user_id==user.id)); db.execute(delete(Conversation).where(Conversation.user_id==user.id)); db.flush()
    legacy_profile=db.get(Profile,DEMO_PROFILE_ID)
    if legacy_profile:
      if legacy_profile.user_id is not None and legacy_profile.user_id!=user.id:raise RuntimeError("The configured demo profile id belongs to another user.")
      db.execute(delete(FearTransformRecord).where(FearTransformRecord.profile_id==legacy_profile.id));db.delete(legacy_profile);db.flush()
    legacy_diagnostic=db.get(Diagnostic,DEMO_DIAGNOSTIC_ID)
    if legacy_diagnostic:
      if legacy_diagnostic.user_id is not None and legacy_diagnostic.user_id!=user.id:raise RuntimeError("The configured demo diagnostic id belongs to another user.")
      db.delete(legacy_diagnostic);db.flush()
    diagnostic=Diagnostic(id=DEMO_DIAGNOSTIC_ID,user_id=user.id,payload=diagnostic_payload());db.add(diagnostic)
    profile=Profile(id=DEMO_PROFILE_ID,user_id=user.id,diagnostic_id=diagnostic.id,data=profile_payload());db.add(profile)
    roadmap=Roadmap(user_id=user.id,profile_id=profile.id,data=roadmap_payload());db.add(roadmap);db.flush()
    seed_demo_assessment(db,user,profile)
    seed_demo_learning(db,user,profile)
    seed_demo_career_resilience(db,user,profile)
    seed_demo_market_application(db,profile)
    seed_demo_interview_journey(db,profile)
    seed_demo_innovation_extension(db,user.id,profile)
    # Adaptive experiment recommendations require active hypotheses.  For the
    # demo, derive them from the already seeded CareerMatch records instead of
    # fabricating a hypothesis solely to populate the example journey.
    ensure_hypotheses_from_matches(db,profile)
    seed_demo_originality_research(db,user.id,profile)
    recommendations=[("AI collaboration","Create a weekly human-AI review ritual","accepted"),("Learning","Build a source-grounded RAG prototype","in_progress"),("Wellbeing","Protect one technology-free reflection block","rejected"),("Contribution","Share an accessible AI-literacy guide","suggested")]
    for index,(category,title,status) in enumerate(recommendations): db.add(Recommendation(user_id=user.id,profile_id=profile.id,category=category,title=title,summary="Demonstration recommendation for a coherent OrganicAI journey.",reason="Connected to the demo profile's strengths, values, and stated goals.",profile_signals_json=["human-centred design","responsible innovation"],rag_sources_json=[{"document_name":"responsible_ai.md","section_title":"Human oversight"}],relevance_score=.92-index*.05,confidence=.86,effort="medium",impact="high",time_horizon="thirty_days",first_action="Schedule a focused 30-minute first step.",success_indicator="A small, reviewable artifact is completed.",ethical_cautions_json=["Keep final judgment human-led."],status=status,generation_version="demo-v1"))
    actions=[("seven_days","Morning Alignment","completed"),("seven_days","AI Literacy Session","completed"),("seven_days","Move Your Body","completed"),("seven_days","Deep Work Block","in_progress"),("seven_days","Human–AI Reflection","not_started"),("seven_days","Prototype and Share","not_started"),("thirty_days","Build a Valuable Skill","in_progress"),("thirty_days","Ship a Meaningful Project","in_progress"),("thirty_days","Strengthen Relationships","not_started"),("thirty_days","Optimize Systems","not_started"),("six_months","Complete the dissertation platform","not_started"),("six_months","Evaluate usability and recommendation relevance","not_started"),("six_months","Build a professional OrganicAI case study","not_started"),("six_months","Publish a portfolio-ready demonstration","not_started"),("six_months","Develop a responsible AI service proposition","not_started"),("six_months","Expand professional opportunities in AI and design","not_started")]
    for priority,(horizon,title,status) in enumerate(actions,1): db.add(RoadmapAction(roadmap_id=roadmap.id,profile_id=profile.id,user_id=user.id,horizon=horizon,title=title,description="A realistic demo action supporting Alex’s human-centred AI direction.",first_step="Choose the smallest useful next step.",success_criteria="Record a short outcome.",estimated_minutes=45,priority=priority,status=status,progress_percentage=100 if status=="completed" else 35 if status=="in_progress" else 0,source_type="demo_seed"))
    db.add(RoadmapCheckIn(roadmap_id=roadmap.id,user_id=user.id,profile_id=profile.id,energy_level=4,confidence_level=4,perceived_progress=4,what_worked="A focused deep-work block and a practical AI learning session.",main_blocker="Protecting enough time for ambitious interdisciplinary work."))
    fears=[("AI may make my professional experience irrelevant.","Your previous experience can become the context that makes AI output more useful, realistic, and human-centred."),("Using AI may weaken my own creativity.","Use AI as a divergent-thinking partner while keeping authorship, selection, and meaning under human control.")]
    for fear,reframe in fears: db.add(FearTransformRecord(profile_id=profile.id,input_fear=fear,output={"clarity":"AI changes tasks faster than it removes the need for judgment, context, empathy, and domain expertise.","controllable_factors":["learning practical AI collaboration","building demonstrable projects"],"creative_reframe":reframe,"fifteen_minute_action":"Write down three professional strengths that AI does not possess independently.","seven_day_action":"Build one small AI-assisted project.","ethical_note":"This is exploratory guidance, not a prediction."}))
    conversation=Conversation(user_id=user.id,profile_id=profile.id,title="Demo AI Coach conversations");db.add(conversation);db.flush()
    for role,content in [("user","How can I build trust when introducing AI in my team?"),("assistant","Building trust starts with transparency, education, and early participation. Explain what the system can and cannot do, invite the team to test it, and preserve human review for meaningful decisions. Sources: Responsible AI, AI Literacy, Human–AI Collaboration, Privacy and Voice Data."),("user","What should I focus on this week?"),("assistant","Focus on one deep-work block, one practical AI-learning activity, and one small prototype that you can show to another person."),("user","Can AI replace human creativity?"),("assistant","AI can generate and recombine patterns, but humans still provide intent, lived context, values, selection, responsibility, and meaning.")]: db.add(Message(conversation_id=conversation.id,role=role,content=content,input_mode="text"))
    db.commit();db.refresh(user);db.refresh(profile);db.refresh(roadmap);return user,profile,roadmap

def ensure_demo(db:Session, reset:bool=False):
    s=get_settings(); user=db.scalar(select(User).where(User.email==s.demo_user_email.lower()))
    if reset or not user or not user.is_demo or user.demo_dataset_version!=s.demo_dataset_version: return restore_demo(db)
    if user.name != s.demo_user_display_name:
        user.name=s.demo_user_display_name
    if not verify_password(s.demo_user_password,user.hashed_password):user.hashed_password=hash_password(s.demo_user_password)
    profile=db.scalar(select(Profile).where(Profile.user_id==user.id).order_by(Profile.created_at.desc()))
    roadmap=db.scalar(select(Roadmap).where(Roadmap.user_id==user.id).order_by(Roadmap.created_at.desc()))
    fear_count=len(db.scalars(select(FearTransformRecord).where(FearTransformRecord.profile_id==profile.id)).all()) if profile else 0
    assessment_count=len(db.scalars(select(AssessmentSession).where(AssessmentSession.profile_id==profile.id,AssessmentSession.status=="completed")).all()) if profile else 0
    learning_count=len(db.scalars(select(LearningRecommendationRun).where(LearningRecommendationRun.profile_id==profile.id)).all()) if profile else 0
    conversation_count=len(db.scalars(select(Conversation).where(Conversation.user_id==user.id)).all())
    resilience_count=len(db.scalars(select(CareerExperimentSession).where(CareerExperimentSession.profile_id==profile.id)).all()) if profile else 0
    market_count=len(db.scalars(select(JobApplication).where(JobApplication.profile_id==profile.id)).all()) if profile else 0
    interview_count=len(db.scalars(select(Interview).where(Interview.profile_id==profile.id)).all()) if profile else 0
    from app.models.innovation_extension import CareerDecisionJournalEntry
    innovation_count=len(db.scalars(select(CareerDecisionJournalEntry).where(CareerDecisionJournalEntry.profile_id==profile.id)).all()) if profile else 0
    from app.models.originality_research import AdaptiveExperimentRecommendation
    originality_count=len(db.scalars(select(AdaptiveExperimentRecommendation).where(AdaptiveExperimentRecommendation.profile_id==profile.id)).all()) if profile else 0
    if profile and roadmap and fear_count >= 2 and conversation_count and assessment_count and learning_count and resilience_count and market_count and interview_count and innovation_count and originality_count:
        db.commit();return user,profile,roadmap
    return restore_demo(db)
