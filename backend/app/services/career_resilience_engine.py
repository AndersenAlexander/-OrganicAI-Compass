from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from app.core.time import utc_now_naive
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.assessment import AssessmentSession, CareerMatch, CareerMatchFactor, SkillEvidence, SkillsInventory
from app.models.career_resilience import (
    CareerExperimentCriterion,
    CareerExperimentResult,
    CareerExperimentReview,
    CareerExperimentRubric,
    CareerExperimentSession,
    CareerExperimentSubmission,
    CareerExperimentTemplate,
    CareerHypothesis,
    CareerHypothesisVersion,
    CareerRecalibrationFactor,
    CareerRecalibrationRun,
    ImmediateActionItem,
    ImmediateActionPlan,
    JobLossProfile,
    MarketRoleSignal,
    MarketSnapshot,
    SkillEvidenceConfidence,
    SkillEvidenceSource,
    SkillRecency,
    SupportApplicationBrief,
    SupportOpportunityLink,
    SupportProgramme,
    SupportProgrammeVersion,
    SupportRule,
    SupportScreening,
    SupportScreeningFactor,
    SupportedPathResult,
    SupportedPathRun,
)
from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.models.roadmap_adaptation import RoadmapAction
from app.services.assessment_engine import alignment_label, fit_label, title_case_slug
from app.services.profile_generation import generate_roadmap_fallback
from app.services.roadmap_adaptation import event as roadmap_event
from app.services.roadmap_adaptation import normalize_legacy, snapshot

CAREER_RESILIENCE_VERSION = "career-resilience-v1"
EXPERIMENT_CATALOGUE_VERSION = "career-experiment-catalogue-v1"
EXPERIMENT_RUBRIC_VERSION = "career-experiment-rubric-v1"
EXPERIMENT_EVAL_VERSION = "career-experiment-eval-v1"
EVIDENCE_CONFIDENCE_VERSION = "evidence-confidence-v1"
SUPPORT_RULE_VERSION = "support-rule-no-v1"
SUPPORT_LAST_CHECKED = "2026-07-21"

EXPERIMENT_STATUSES = {
    "suggested",
    "saved",
    "planned",
    "in_progress",
    "submitted",
    "needs_review",
    "evaluated",
    "rejected_by_user",
    "archived",
}

EXPERIMENT_MODES = {"guided", "independent", "evidence_only"}
PRELIMINARY_LABELS = {
    "Potentially relevant",
    "Possibly relevant",
    "Additional information required",
    "Probably not applicable",
    "Official assessment required",
}

APPROVED_OFFICIAL_HOSTS = {
    "nav.no",
    "www.nav.no",
    "arbeidsplassen.nav.no",
    "arbeidstilsynet.no",
    "www.arbeidstilsynet.no",
    "lovdata.no",
    "www.lovdata.no",
    "regjeringen.no",
    "www.regjeringen.no",
    "lanekassen.no",
    "www.lanekassen.no",
    "europa.eu",
    "ec.europa.eu",
}

ROLE_EXPERIMENT_MAP = {
    "ai product designer": [
        "human-centred ai product designer",
        "ai product designer",
        "ux designer for ai systems",
        "design and ai product",
    ],
    "ai integration consultant": ["ai integration consultant", "ai operations and consulting", "automation specialist"],
    "rag application developer": ["rag application developer", "software and ai engineering"],
    "learning experience designer": ["learning experience designer", "education and enablement"],
}


def safe_official_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.netloc.lower() in APPROVED_OFFICIAL_HOSTS


def safe_user_url(url: str | None) -> bool:
    if not url:
        return True
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _rating_scale() -> list[dict[str, Any]]:
    return [
        {"rating": 0, "label": "Not demonstrated"},
        {"rating": 1, "label": "Emerging evidence"},
        {"rating": 2, "label": "Basic evidence"},
        {"rating": 3, "label": "Competent evidence"},
        {"rating": 4, "label": "Strong evidence"},
    ]


def _criteria(skills: list[str]) -> list[dict[str, Any]]:
    specs = [
        ("task_understanding", "Task understanding", 0.12, "The submission addresses the scenario and requested scope."),
        ("deliverable_quality", "Quality of deliverable", 0.18, "A concrete artifact, plan, design, or structured output is provided."),
        ("reasoning_clarity", "Reasoning clarity", 0.14, "Choices are explained with assumptions and tradeoffs."),
        ("role_specific_technique", "Role-specific technique", 0.16, "The work applies methods from the target role family."),
        ("constraints", "Handling of constraints", 0.12, "The work addresses feasibility, limitations, risk, or accessibility constraints."),
        ("human_centred", "Human-centred considerations", 0.12, "The work considers users, stakeholders, ethics, inclusion, or trust."),
        ("testing_validation", "Testing or validation", 0.08, "The work includes a validation step, review, checklist, or user test."),
        ("reflection_quality", "Reflection quality", 0.08, "The user reflects on difficulty, interest, confidence, and next evidence needs."),
    ]
    return [
        {
            "criterion_id": criterion_id,
            "skill_id": skills[index % max(1, len(skills))],
            "description": description,
            "weight": weight,
            "evidence_requirement": evidence,
            "interpretation": {
                "0": "No usable evidence was submitted for this criterion.",
                "2": "The criterion is visible but still incomplete or weakly supported.",
                "4": "The criterion is strongly demonstrated for an MVP role experiment.",
            },
        }
        for index, (criterion_id, description, weight, evidence) in enumerate(specs)
    ]


def _experiment(
    experiment_id: str,
    title: str,
    role_family: str,
    purpose: str,
    scenario: str,
    deliverables: list[str],
    evaluated_skills: list[str],
    *,
    difficulty: str = "intermediate",
    duration: int = 180,
    required_skills: list[str] | None = None,
    prerequisites: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": experiment_id,
        "title": title,
        "target_role_family": role_family,
        "purpose": purpose,
        "real_world_scenario": scenario,
        "user_instructions": [
            "Review the scenario and decide whether to complete the guided, independent, or evidence-only mode.",
            "Produce the requested deliverables as a small practical artifact.",
            "Record assumptions, limitations, and how AI tools were used.",
            "Submit the artifact text, a URL, document metadata, or manual evidence notes.",
        ],
        "expected_deliverables": deliverables,
        "estimated_duration_minutes": duration,
        "difficulty": difficulty,
        "required_skills": required_skills or evaluated_skills[:3],
        "evaluated_skills": evaluated_skills,
        "optional_prerequisites": prerequisites or [],
        "allowed_tools": ["Whiteboard or design tool", "Text editor", "Spreadsheet", "Browser research", "AI assistant with disclosure"],
        "ai_assistance_policy": (
            "AI assistance is allowed for brainstorming, critique, rewriting, and checklist generation. "
            "The user must disclose tools used and keep final decisions, scoring, and reflection human-controlled."
        ),
        "reflection_questions": [
            "Which part of the role task felt energising or draining?",
            "What evidence did this experiment generate that did not exist before?",
            "What would you change before using this as portfolio evidence?",
            "What uncertainty remains about this career direction?",
        ],
        "completion_criteria": [
            "At least one concrete deliverable is submitted.",
            "The user records time spent and AI assistance level.",
            "The user completes a short reflection.",
            "The deterministic rubric is applied before evidence is added to the passport.",
        ],
        "evidence_generated": ["Career experiment submission", "Deterministic rubric result", "Self-review", "Skill evidence records"],
        "source_metadata": {
            "source_type": "curated_role_experiment",
            "version": EXPERIMENT_CATALOGUE_VERSION,
            "methodology": "prototype role simulation",
        },
    }


def experiment_catalogue() -> list[dict[str, Any]]:
    return [
        _experiment(
            "ai-product-explainable-recommendation-interface",
            "Design an Explainable AI Recommendation Interface",
            "AI Product Designer",
            "Test whether the user can translate AI uncertainty into understandable product interaction.",
            "A career-guidance platform generates recommendations, but users do not understand why a role was suggested or how to challenge it.",
            [
                "Responsive recommendation card wireframe or prototype",
                "State descriptions for correction, rejection, alternative request, and roadmap action",
                "Short design rationale",
                "Accessibility considerations",
                "Reflection note",
            ],
            ["ux_ui", "human_centred_ai", "explainability", "interaction_design", "accessibility", "critical_thinking"],
        ),
        _experiment(
            "ai-product-human-review-flow",
            "Prototype a Human Review Flow for an AI Feature",
            "AI Product Designer",
            "Test product judgment around review, override, transparency, and user control.",
            "A product team wants to launch AI-generated summaries but needs a human review flow before release.",
            ["User journey", "Review states", "Override and correction flow", "Risk note", "Reflection note"],
            ["ux_ui", "responsible_ai", "product_thinking", "risk_reasoning", "communication"],
            duration=150,
        ),
        _experiment(
            "ai-product-micro-usability-test",
            "Run a Micro Usability Test for an AI Suggestion Card",
            "AI Product Designer",
            "Test whether the user can validate an AI interface with lightweight evidence.",
            "Users must decide whether to accept, edit, or reject AI suggestions inside a career planning workflow.",
            ["Test plan", "Three task prompts", "Observation notes template", "Findings summary", "Next iteration"],
            ["ux_research", "interaction_design", "testing", "accessibility", "critical_thinking"],
            duration=210,
        ),
        _experiment(
            "ai-integration-workflow-map",
            "Map an AI Workflow Integration Opportunity",
            "AI Integration Consultant",
            "Test whether the user can identify a low-risk, useful AI integration point.",
            "A small service business wants to use AI without exposing sensitive client data or disrupting work.",
            ["Current workflow map", "Integration opportunity", "Risk boundaries", "Success measure", "Pilot recommendation"],
            ["workflow_analysis", "ai_tools", "systems_thinking", "privacy_reasoning", "consulting_communication"],
            duration=180,
        ),
        _experiment(
            "ai-integration-automation-pilot-plan",
            "Draft a Responsible Automation Pilot Plan",
            "AI Integration Consultant",
            "Test planning skill for a bounded AI automation pilot.",
            "A team wants to automate intake triage but must preserve human review and auditability.",
            ["Pilot scope", "Manual fallback", "Data boundary", "Measurement plan", "Stakeholder communication"],
            ["automation", "planning", "responsible_ai", "quality_assurance", "communication"],
            duration=210,
        ),
        _experiment(
            "ai-integration-stakeholder-readiness-brief",
            "Create a Stakeholder Readiness Brief for AI Adoption",
            "AI Integration Consultant",
            "Test change-readiness communication and practical adoption planning.",
            "Managers, frontline staff, and customers have different concerns about an AI-assisted service workflow.",
            ["Stakeholder map", "Concern matrix", "Readiness risks", "Training outline", "Decision questions"],
            ["stakeholder_analysis", "communication", "change_management", "ai_literacy", "empathy"],
            duration=150,
        ),
        _experiment(
            "rag-developer-source-grounded-answer-plan",
            "Build a Source-Grounded RAG Answer Plan",
            "RAG Application Developer",
            "Test whether the user can specify source-grounded answer behavior and failure states.",
            "A knowledge-base assistant must answer only from approved documents and clearly handle insufficient context.",
            ["Retrieval plan", "Answer policy", "Failure-state behavior", "Source display design", "Evaluation cases"],
            ["rag_fundamentals", "apis", "evaluation", "source_traceability", "software_development"],
            duration=240,
        ),
        _experiment(
            "rag-developer-evaluation-checklist",
            "Design a RAG Evaluation Checklist and Test Set",
            "RAG Application Developer",
            "Test practical reasoning about groundedness, recall, precision, and source quality.",
            "A RAG application sometimes answers from weak sources and needs a repeatable evaluation checklist.",
            ["Evaluation checklist", "Five test questions", "Expected source requirements", "Failure labels", "Improvement plan"],
            ["evaluation", "critical_thinking", "rag_fundamentals", "quality_assurance", "documentation"],
            duration=180,
        ),
        _experiment(
            "rag-developer-retrieval-pipeline-spec",
            "Specify a Retrieval Pipeline for a Knowledge Base",
            "RAG Application Developer",
            "Test system design skill without requiring production deployment.",
            "A team needs a retrieval pipeline that separates career guidance, labour-market, and legal-support documents.",
            ["Pipeline diagram or outline", "Metadata schema", "Filter rules", "Security notes", "Testing plan"],
            ["system_design", "databases", "apis", "metadata_design", "security_reasoning"],
            duration=210,
        ),
        _experiment(
            "learning-designer-ai-literacy-micro-lesson",
            "Design a 30-Minute AI Literacy Micro-Lesson",
            "Learning Experience Designer",
            "Test whether the user can convert AI concepts into a practical learning experience.",
            "Adult learners need a short lesson on AI strengths, limitations, and source checking before using AI at work.",
            ["Learning objectives", "Lesson outline", "Activity", "Assessment prompt", "Accessibility note"],
            ["instructional_design", "ai_literacy", "writing", "facilitation", "assessment_design"],
            duration=150,
        ),
        _experiment(
            "learning-designer-scenario-rubric",
            "Create a Scenario-Based Assessment Rubric",
            "Learning Experience Designer",
            "Test skill in assessing applied learning without false precision.",
            "A course on responsible AI needs a rubric for evaluating a learner's workplace scenario response.",
            ["Scenario prompt", "Rubric criteria", "Rating scale", "Feedback examples", "Limitations note"],
            ["assessment_design", "writing", "rubric_design", "responsible_ai", "critical_thinking"],
            duration=180,
        ),
        _experiment(
            "learning-designer-evidence-based-learning-path",
            "Adapt a Learning Path from Skill Evidence",
            "Learning Experience Designer",
            "Test learning-path design grounded in evidence rather than assumptions.",
            "A learner has self-reported UX skill, one course completion, and a weak portfolio artifact. They want a realistic AI product-design transition plan.",
            ["Evidence review", "Gap-based objectives", "Learning sequence", "Practice project", "Review checkpoint"],
            ["learning_path_design", "evidence_reasoning", "planning", "ux_ui", "communication"],
            duration=210,
        ),
    ]


def support_programme_catalogue() -> list[dict[str, Any]]:
    common_limitations = [
        "This prototype stores official-source summaries only and does not make eligibility decisions.",
        "Final eligibility, funding, and participation are determined by NAV or the responsible authority.",
    ]
    return [
        {
            "id": "nav_jobseeker_registration",
            "category": "jobseeker_registration",
            "norwegian_name": "Registrer deg som arbeidssoker",
            "english_name": "Register as a jobseeker",
            "authority": "NAV",
            "official_url": "https://www.nav.no/registrer-arbeidssoker/en",
            "summary": "Registration with NAV for people seeking work or occupational follow-up.",
            "target_group": "People legally resident in Norway who want to find work or request occupational follow-up.",
            "known_conditions": ["Legal residence in Norway", "Electronic ID or contact with a NAV office"],
            "required_information": ["age", "work history", "education", "support needs"],
            "application_or_contact_route": "Register digitally at nav.no or contact a NAV office if electronic ID is unavailable.",
            "documents": ["BankID or other electronic ID where available"],
            "deadlines": ["Registered jobseekers must confirm they still want to stay registered every 14 days."],
            "incompatibilities": [],
            "source_publication_date": "2026-04-29",
            "categories": ["jobseeker registration", "occupational follow-up"],
            "limitations": common_limitations,
        },
        {
            "id": "nav_unemployment_benefit",
            "category": "unemployment_benefit_guidance",
            "norwegian_name": "Dagpenger",
            "english_name": "Unemployment benefit",
            "authority": "NAV",
            "official_url": "https://www.nav.no/dagpenger/en",
            "summary": "Financial support that may be available if a person is unemployed or temporarily laid off.",
            "target_group": "People who have lost work or income and are genuine jobseekers.",
            "known_conditions": [
                "Lost at least 50 percent of total working hours",
                "Lost income or reduced income",
                "Registered as a jobseeker",
                "Resident in Norway with Norwegian national insurance coverage",
                "Submit employment status forms every 14 days",
            ],
            "required_information": ["working-hours reduction", "income history", "residence", "national insurance coverage", "jobseeker registration"],
            "application_or_contact_route": "Apply digitally through NAV. The application is in Norwegian.",
            "documents": ["employment documentation", "income documentation", "termination or layoff information where relevant"],
            "deadlines": ["NAV says to apply 2 weeks before the last day with salary where possible."],
            "incompatibilities": ["Some other benefits or work situations may reduce or affect payment."],
            "source_publication_date": "2026-05-21",
            "categories": ["unemployment benefit guidance", "social protection"],
            "limitations": common_limitations,
        },
        {
            "id": "nav_employment_status_form",
            "category": "activity_card_reporting_obligations",
            "norwegian_name": "Meldekort for dagpenger",
            "english_name": "Employment status form for unemployment benefit",
            "authority": "NAV",
            "official_url": "https://www.nav.no/send-meldekort-dagpenger/en",
            "summary": "Regular reporting used by NAV while waiting for or receiving unemployment benefit.",
            "target_group": "People registered as jobseekers and applying for or receiving unemployment benefit.",
            "known_conditions": ["Employment status forms must be submitted every 14 days during the benefit period."],
            "required_information": ["work hours", "activity", "courses or education", "sickness", "holidays or absence"],
            "application_or_contact_route": "Submit the employment status form through NAV's logged-in services.",
            "documents": [],
            "deadlines": ["Every 14 days while relevant."],
            "incompatibilities": [],
            "source_publication_date": "2026-03-01",
            "categories": ["activity card", "reporting obligations"],
            "limitations": common_limitations,
        },
        {
            "id": "nav_training_measures",
            "category": "training_measures",
            "norwegian_name": "Opplaering",
            "english_name": "Training measures",
            "authority": "NAV",
            "official_url": "https://www.nav.no/opplaring",
            "summary": "Training support when qualification is needed to get work.",
            "target_group": "Jobseekers who have difficulty getting work because of missing formal qualifications or weak basic skills.",
            "known_conditions": ["NAV must assess that training is needed and is an appropriate measure."],
            "required_information": ["education", "formal qualifications", "labour-market goal", "age", "work ability where relevant"],
            "application_or_contact_route": "Contact the NAV office where you live.",
            "documents": ["education history", "documentation requested by NAV"],
            "deadlines": [],
            "incompatibilities": ["Higher education support has additional age and work-ability restrictions."],
            "source_publication_date": "2025-12-08",
            "categories": ["training", "reskilling", "publicly funded training"],
            "limitations": common_limitations,
        },
        {
            "id": "nav_work_training",
            "category": "work_training",
            "norwegian_name": "Arbeidstrening",
            "english_name": "Work training",
            "authority": "NAV",
            "official_url": "https://www.nav.no/arbeidstrening",
            "summary": "Workplace-based training for people who need work experience or a reference.",
            "target_group": "People with little work experience or reduced work ability who need help entering work.",
            "known_conditions": ["NAV, employer, and participant make an agreement; NAV assesses need."],
            "required_information": ["work experience", "work ability", "target occupation", "support needs"],
            "application_or_contact_route": "Contact the NAV office where you live.",
            "documents": ["information requested for the work-training agreement"],
            "deadlines": [],
            "incompatibilities": ["Participants are not ordinary employees during work training."],
            "source_publication_date": "2025-12-08",
            "categories": ["work training", "practical placement"],
            "limitations": common_limitations,
        },
        {
            "id": "nav_temporary_wage_subsidy",
            "category": "wage_subsidy_related_measures",
            "norwegian_name": "Midlertidig lonnstilskudd",
            "english_name": "Temporary wage subsidy",
            "authority": "NAV",
            "official_url": "https://www.nav.no/midlertidig-lonnstilskudd",
            "summary": "A wage-subsidy arrangement where the employer applies and NAV assesses the need.",
            "target_group": "People seeking work who have difficulty getting ordinary work, or people at risk of losing work after long sickness absence.",
            "known_conditions": ["NAV must assess need; employer applies; agreement must be made before the measure starts."],
            "required_information": ["employer involvement", "work situation", "NAV assessment", "support needs"],
            "application_or_contact_route": "Contact the NAV office where you live; employer/NAV creates the agreement.",
            "documents": ["employment and agreement information requested by NAV"],
            "deadlines": ["The agreement must be made before the measure starts."],
            "incompatibilities": [],
            "source_publication_date": "2025-12-08",
            "categories": ["wage subsidy", "employment measures"],
            "limitations": common_limitations,
        },
        {
            "id": "nav_qualification_programme",
            "category": "qualification_programmes",
            "norwegian_name": "Kvalifiseringsprogrammet",
            "english_name": "Qualification Programme",
            "authority": "NAV",
            "official_url": "https://www.nav.no/kvalifiseringsprogrammet/en",
            "summary": "A full-time programme for people aged 18 to 67 who need extra follow-up to get into work.",
            "target_group": "People who need extra support to find work and can participate in a full-time programme.",
            "known_conditions": ["Age 18-67", "Need for extra follow-up", "Programme content should support work entry"],
            "required_information": ["age", "work situation", "need for follow-up", "income and support situation"],
            "application_or_contact_route": "Contact NAV or municipality/NAV office for assessment.",
            "documents": ["documentation requested by NAV or municipality"],
            "deadlines": [],
            "incompatibilities": ["Full-time programme requirements may conflict with some activities."],
            "source_publication_date": "2026-03-19",
            "categories": ["qualification programme", "municipal services", "employment measures"],
            "limitations": common_limitations,
        },
        {
            "id": "nav_supplemental_benefit",
            "category": "additional_education_related_support",
            "norwegian_name": "Tilleggsstonader",
            "english_name": "Supplemental benefit",
            "authority": "NAV",
            "official_url": "https://www.nav.no/tilleggsstonader/en",
            "summary": "Support for childcare or expenses connected to NAV-assessed education or job search.",
            "target_group": "People in approved work-oriented activity, education, or job search situations described by NAV.",
            "known_conditions": ["NAV-assessed necessary education or work-oriented activity", "Additional qualifying conditions may apply"],
            "required_information": ["activity or education", "expenses", "family situation where relevant", "NAV assessment"],
            "application_or_contact_route": "Apply or forward documentation through NAV.",
            "documents": ["expense documentation", "activity or education confirmation"],
            "deadlines": ["Normally applies from the date of application; NAV may assess limited backdating in some cases."],
            "incompatibilities": [],
            "source_publication_date": "2025-08-01",
            "categories": ["education support", "additional support", "job-search expenses"],
            "limitations": common_limitations + ["Exact source publication date should be rechecked before production use."],
        },
        {
            "id": "arbeidstilsynet_dismissal_guidance",
            "category": "job_search_support",
            "norwegian_name": "Oppsigelse med varsel",
            "english_name": "Dismissal with notice",
            "authority": "Arbeidstilsynet",
            "official_url": "https://www.arbeidstilsynet.no/en/pay-and-engagement-of-employees/dismissal-with-notice/",
            "summary": "Official guidance about dismissal with notice, written notice, reasons, negotiations, and references.",
            "target_group": "Employees and employers seeking general regulatory guidance on dismissal.",
            "known_conditions": ["Arbeidstilsynet provides general guidance but does not decide disputes."],
            "required_information": ["termination notice", "employment contract", "notice period", "reason for dismissal where requested"],
            "application_or_contact_route": "Use the guidance and seek legal, union, or advisory support where there is a dispute.",
            "documents": ["employment contract", "notice of termination", "written reason or reference where relevant"],
            "deadlines": ["Negotiation requests and legal action can have statutory time limits."],
            "incompatibilities": [],
            "source_publication_date": "2026-07-21",
            "categories": ["job-loss guidance", "employment rights"],
            "limitations": common_limitations + ["This is general guidance, not legal advice."],
        },
    ]


def market_snapshot_catalogue() -> dict[str, Any]:
    return {
        "id": "norway-demo-ai-career-market-2026-07",
        "title": "Norway demo market snapshot for AI-adjacent career transitions",
        "country": "Norway",
        "region": "National",
        "source_type": "demo_curated_snapshot",
        "snapshot_date": "2026-07-21",
        "source_metadata": {
            "coverage": "Demo data only. Not live market intelligence.",
            "official_job_board": "https://arbeidsplassen.nav.no/stillinger",
            "provider_adapter_status": "future_live_api_adapter_not_enabled",
        },
        "signals": [
            {
                "role_family": "AI Product Designer",
                "opportunity_count": 12,
                "geography": ["Oslo", "Bergen", "remote/hybrid"],
                "work_modes": ["hybrid", "remote", "on-site"],
                "language_requirements": ["English often required", "Norwegian often advantageous"],
                "recurring_skills": ["UX/UI", "product thinking", "AI literacy", "accessibility", "user research"],
                "experience_level": "mixed junior-to-mid",
                "emerging_requirements": ["responsible AI", "AI evaluation", "product analytics"],
                "posting_recency_label": "demo snapshot only",
                "demand_direction": "emerging",
            },
            {
                "role_family": "AI Integration Consultant",
                "opportunity_count": 16,
                "geography": ["Oslo", "Trondheim", "national consultancies", "remote/hybrid"],
                "work_modes": ["hybrid", "client-site", "remote"],
                "language_requirements": ["Norwegian often required for client work", "English for technical documentation"],
                "recurring_skills": ["process mapping", "automation", "stakeholder communication", "AI tools", "risk management"],
                "experience_level": "mid-level",
                "emerging_requirements": ["change management", "privacy", "workflow governance"],
                "posting_recency_label": "demo snapshot only",
                "demand_direction": "emerging",
            },
            {
                "role_family": "RAG Application Developer",
                "opportunity_count": 10,
                "geography": ["Oslo", "remote", "technology hubs"],
                "work_modes": ["hybrid", "remote"],
                "language_requirements": ["English technical fluency", "Norwegian useful in public-sector contexts"],
                "recurring_skills": ["Python", "APIs", "databases", "retrieval", "evaluation", "source traceability"],
                "experience_level": "mid-level technical",
                "emerging_requirements": ["LLM evaluation", "security", "observability"],
                "posting_recency_label": "demo snapshot only",
                "demand_direction": "emerging",
            },
            {
                "role_family": "Learning Experience Designer",
                "opportunity_count": 8,
                "geography": ["Oslo", "regional education providers", "remote/hybrid"],
                "work_modes": ["hybrid", "remote", "on-site facilitation"],
                "language_requirements": ["Norwegian often required", "English useful for digital learning"],
                "recurring_skills": ["instructional design", "facilitation", "writing", "digital learning", "assessment"],
                "experience_level": "mixed",
                "emerging_requirements": ["AI literacy", "scenario-based learning", "learning analytics"],
                "posting_recency_label": "demo snapshot only",
                "demand_direction": "stable-to-emerging",
            },
        ],
    }


def sync_career_resilience_catalogue(db: Session) -> None:
    for item in experiment_catalogue():
        row = db.get(CareerExperimentTemplate, item["id"]) or CareerExperimentTemplate(id=item["id"], title=item["title"], target_role_family=item["target_role_family"])
        row.title = item["title"]
        row.target_role_family = item["target_role_family"]
        row.purpose = item["purpose"]
        row.real_world_scenario = item["real_world_scenario"]
        row.user_instructions_json = item["user_instructions"]
        row.expected_deliverables_json = item["expected_deliverables"]
        row.estimated_duration_minutes = item["estimated_duration_minutes"]
        row.difficulty = item["difficulty"]
        row.required_skills_json = item["required_skills"]
        row.evaluated_skills_json = item["evaluated_skills"]
        row.optional_prerequisites_json = item["optional_prerequisites"]
        row.allowed_tools_json = item["allowed_tools"]
        row.ai_assistance_policy = item["ai_assistance_policy"]
        row.reflection_questions_json = item["reflection_questions"]
        row.completion_criteria_json = item["completion_criteria"]
        row.evidence_generated_json = item["evidence_generated"]
        row.version = EXPERIMENT_CATALOGUE_VERSION
        row.source_metadata_json = item["source_metadata"]
        row.active = True
        db.add(row)
        db.flush()
        rubric_id = f"{item['id']}:rubric"
        rubric = db.get(CareerExperimentRubric, rubric_id) or CareerExperimentRubric(id=rubric_id, experiment_template_id=item["id"])
        rubric.experiment_template_id = item["id"]
        rubric.version = EXPERIMENT_RUBRIC_VERSION
        rubric.rating_scale_json = _rating_scale()
        rubric.source_metadata_json = {"source_type": "deterministic_prototype_rubric", "llm_scoring": False}
        rubric.active = True
        db.add(rubric)
        db.flush()
        for index, criterion in enumerate(_criteria(item["evaluated_skills"])):
            criterion_row_id = f"{rubric_id}:{criterion['criterion_id']}"
            criterion_row = db.get(CareerExperimentCriterion, criterion_row_id) or CareerExperimentCriterion(id=criterion_row_id, rubric_id=rubric_id, criterion_id=criterion["criterion_id"], skill_id=criterion["skill_id"])
            criterion_row.rubric_id = rubric_id
            criterion_row.criterion_id = criterion["criterion_id"]
            criterion_row.skill_id = criterion["skill_id"]
            criterion_row.description = criterion["description"]
            criterion_row.weight = criterion["weight"]
            criterion_row.rating_scale_json = _rating_scale()
            criterion_row.evidence_requirement = criterion["evidence_requirement"]
            criterion_row.interpretation_json = criterion["interpretation"]
            criterion_row.order_index = index
            db.add(criterion_row)
    for item in support_programme_catalogue():
        if not safe_official_url(item["official_url"]):
            raise ValueError(f"Unsupported official support URL: {item['official_url']}")
        programme = db.get(SupportProgramme, item["id"]) or SupportProgramme(id=item["id"], category=item["category"])
        programme.category = item["category"]
        programme.authority = item["authority"]
        programme.jurisdiction = "Norway"
        programme.active = True
        programme.current_rule_version = SUPPORT_RULE_VERSION
        db.add(programme)
        db.flush()
        version_id = f"{item['id']}:{SUPPORT_RULE_VERSION}"
        version = db.get(SupportProgrammeVersion, version_id) or SupportProgrammeVersion(id=version_id, programme_id=item["id"], norwegian_name=item["norwegian_name"], english_name=item["english_name"], official_url=item["official_url"])
        version.programme_id = item["id"]
        version.norwegian_name = item["norwegian_name"]
        version.english_name = item["english_name"]
        version.authority = item["authority"]
        version.jurisdiction = "Norway"
        version.official_url = item["official_url"]
        version.summary = item["summary"]
        version.target_group = item["target_group"]
        version.known_conditions_json = item["known_conditions"]
        version.required_information_json = item["required_information"]
        version.application_or_contact_route = item["application_or_contact_route"]
        version.documents_json = item["documents"]
        version.deadlines_json = item["deadlines"]
        version.incompatibilities_json = item["incompatibilities"]
        version.source_publication_date = item["source_publication_date"]
        version.last_checked_date = SUPPORT_LAST_CHECKED
        version.rule_version = SUPPORT_RULE_VERSION
        version.verification_status = "official_source_checked"
        version.human_assessment_required = True
        version.limitations_json = item["limitations"]
        version.categories_json = item["categories"]
        db.add(version)
        db.flush()
        rule_id = f"{item['id']}:{SUPPORT_RULE_VERSION}:rule"
        rule = db.get(SupportRule, rule_id) or SupportRule(id=rule_id, programme_id=item["id"], programme_version_id=version_id)
        rule.programme_id = item["id"]
        rule.programme_version_id = version_id
        rule.rule_version = SUPPORT_RULE_VERSION
        rule.conditions_json = item["known_conditions"]
        rule.missing_information_fields_json = item["required_information"]
        rule.relevance_logic_json = {"deterministic_screening_only": True, "allowed_labels": sorted(PRELIMINARY_LABELS)}
        rule.active = True
        db.add(rule)
    market = market_snapshot_catalogue()
    snapshot_row = db.get(MarketSnapshot, market["id"]) or MarketSnapshot(id=market["id"], title=market["title"])
    snapshot_row.country = market["country"]
    snapshot_row.region = market["region"]
    snapshot_row.source_type = market["source_type"]
    snapshot_row.title = market["title"]
    snapshot_row.snapshot_date = market["snapshot_date"]
    snapshot_row.status = "active"
    snapshot_row.version = "market-snapshot-no-demo-v1"
    snapshot_row.source_metadata_json = market["source_metadata"]
    snapshot_row.last_checked_at = utc_now_naive()
    db.add(snapshot_row)
    db.flush()
    existing_signals = {row.role_family: row for row in db.scalars(select(MarketRoleSignal).where(MarketRoleSignal.snapshot_id == market["id"])).all()}
    for signal in market["signals"]:
        signal_row = existing_signals.get(signal["role_family"]) or MarketRoleSignal(snapshot_id=market["id"], role_family=signal["role_family"])
        signal_row.snapshot_id = market["id"]
        signal_row.role_family = signal["role_family"]
        signal_row.opportunity_count = signal["opportunity_count"]
        signal_row.geography_json = signal["geography"]
        signal_row.work_modes_json = signal["work_modes"]
        signal_row.language_requirements_json = signal["language_requirements"]
        signal_row.recurring_skills_json = signal["recurring_skills"]
        signal_row.experience_level = signal["experience_level"]
        signal_row.emerging_requirements_json = signal["emerging_requirements"]
        signal_row.posting_recency_label = signal["posting_recency_label"]
        signal_row.demand_direction = signal["demand_direction"]
        signal_row.limitations_json = ["Demo market dataset. Do not treat as real-time market coverage."]
        db.add(signal_row)
    db.commit()


def template_public(db: Session, row: CareerExperimentTemplate, include_rubric: bool = False) -> dict[str, Any]:
    payload = {
        "id": row.id,
        "title": row.title,
        "target_role_family": row.target_role_family,
        "purpose": row.purpose,
        "real_world_scenario": row.real_world_scenario,
        "user_instructions": row.user_instructions_json or [],
        "expected_deliverables": row.expected_deliverables_json or [],
        "estimated_duration_minutes": row.estimated_duration_minutes,
        "difficulty": row.difficulty,
        "required_skills": row.required_skills_json or [],
        "skills_being_evaluated": row.evaluated_skills_json or [],
        "optional_prerequisites": row.optional_prerequisites_json or [],
        "allowed_tools": row.allowed_tools_json or [],
        "ai_assistance_policy": row.ai_assistance_policy,
        "reflection_questions": row.reflection_questions_json or [],
        "completion_criteria": row.completion_criteria_json or [],
        "evidence_generated": row.evidence_generated_json or [],
        "version": row.version,
        "source_metadata": row.source_metadata_json or {},
        "active": row.active,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }
    if include_rubric:
        rubric = db.scalar(select(CareerExperimentRubric).where(CareerExperimentRubric.experiment_template_id == row.id, CareerExperimentRubric.active.is_(True)))
        criteria = db.scalars(select(CareerExperimentCriterion).where(CareerExperimentCriterion.rubric_id == rubric.id).order_by(CareerExperimentCriterion.order_index)).all() if rubric else []
        payload["evaluation_rubric"] = {
            "id": rubric.id if rubric else None,
            "version": rubric.version if rubric else EXPERIMENT_RUBRIC_VERSION,
            "rating_scale": rubric.rating_scale_json if rubric else _rating_scale(),
            "criteria": [criterion_public(item) for item in criteria],
        }
    return payload


def criterion_public(row: CareerExperimentCriterion) -> dict[str, Any]:
    return {
        "id": row.id,
        "criterion_id": row.criterion_id,
        "skill_id": row.skill_id,
        "description": row.description,
        "weight": row.weight,
        "rating_scale": row.rating_scale_json or _rating_scale(),
        "evidence_requirement": row.evidence_requirement,
        "interpretation": row.interpretation_json or {},
    }


def list_experiment_templates(db: Session, role_family: str | None = None) -> list[dict[str, Any]]:
    sync_career_resilience_catalogue(db)
    query = select(CareerExperimentTemplate).where(CareerExperimentTemplate.active.is_(True))
    if role_family:
        query = query.where(CareerExperimentTemplate.target_role_family == role_family)
    rows = db.scalars(query.order_by(CareerExperimentTemplate.target_role_family, CareerExperimentTemplate.title)).all()
    return [template_public(db, row) for row in rows]


def get_experiment_template(db: Session, experiment_id: str) -> dict[str, Any]:
    sync_career_resilience_catalogue(db)
    row = db.get(CareerExperimentTemplate, experiment_id)
    if not row or not row.active:
        raise LookupError("Career experiment template not found")
    return template_public(db, row, include_rubric=True)


def _demo_marker(profile: Profile) -> bool:
    return bool(getattr(getattr(profile, "user", None), "is_demo", False))


def _related_role_family(match: CareerMatch | None) -> str:
    if not match:
        return ""
    combined = f"{match.title} {match.role_family}".lower()
    for target, aliases in ROLE_EXPERIMENT_MAP.items():
        if any(alias in combined for alias in aliases):
            return target.title().replace("Ai", "AI").replace("Rag", "RAG")
    return match.title


def _template_for_match(db: Session, match: CareerMatch | None) -> CareerExperimentTemplate | None:
    role = _related_role_family(match)
    if not role:
        return None
    return db.scalar(select(CareerExperimentTemplate).where(CareerExperimentTemplate.target_role_family == role, CareerExperimentTemplate.active.is_(True)).order_by(CareerExperimentTemplate.estimated_duration_minutes))


def _create_roadmap_action_for_experiment(db: Session, profile: Profile, session: CareerExperimentSession, template: CareerExperimentTemplate) -> RoadmapAction:
    roadmap = db.scalar(select(Roadmap).where(Roadmap.profile_id == profile.id).order_by(Roadmap.created_at.desc()))
    created = False
    if not roadmap:
        roadmap = Roadmap(user_id=profile.user_id, profile_id=profile.id, data={**generate_roadmap_fallback(), "version": 0, "status": "active"})
        db.add(roadmap)
        db.flush()
        created = True
    normalize_legacy(db, roadmap)
    if created:
        snapshot(db, roadmap, "Initial roadmap created for career experiment")
    action = RoadmapAction(
        roadmap_id=roadmap.id,
        profile_id=profile.id,
        user_id=profile.user_id,
        recommendation_id=session.id,
        horizon="thirty_days",
        title=f"Career experiment: {template.title}",
        description=template.purpose,
        reason="User explicitly confirmed adding a career experiment to My Roadmap.",
        first_step="Review scope, choose experiment mode, and schedule the first work block.",
        success_criteria="Submit deliverables, complete self-review, and inspect the Evidence Passport update.",
        estimated_minutes=template.estimated_duration_minutes,
        effort="medium",
        impact="high",
        priority=1,
        status="not_started",
        source_type="career_experiment",
        profile_signals_json=[template.target_role_family],
        ethical_cautions_json=["This career direction remains a hypothesis until evidence is reviewed."],
    )
    db.add(action)
    db.flush()
    roadmap_event(db, roadmap.id, profile.user_id, "action_added", action.id, {"source_type": "career_experiment", "experiment_session_id": session.id})
    return action


def ensure_hypotheses_from_matches(db: Session, profile: Profile) -> list[CareerHypothesis]:
    rows = db.scalars(select(CareerMatch).where(CareerMatch.profile_id == profile.id, CareerMatch.status != "rejected").order_by(CareerMatch.alignment_score.desc())).all()
    saved: list[CareerHypothesis] = []
    existing = {row.career_match_id: row for row in db.scalars(select(CareerHypothesis).where(CareerHypothesis.profile_id == profile.id)).all()}
    for match in rows:
        hypothesis = existing.get(match.id)
        if not hypothesis:
            hypothesis = CareerHypothesis(
                profile_id=profile.id,
                user_id=profile.user_id,
                career_match_id=match.id,
                role_template_id=match.role_template_id,
                title=match.title,
                role_family=match.role_family,
                demo_marker=match.demo_marker or _demo_marker(profile),
            )
            db.add(hypothesis)
            db.flush()
            db.add(
                CareerHypothesisVersion(
                    hypothesis_id=hypothesis.id,
                    profile_id=profile.id,
                    version_number=1,
                    snapshot_json={"career_match_id": match.id, "alignment_score": match.alignment_score, "status": match.status},
                    change_reason="Initial hypothesis created from career compatibility result.",
                )
            )
        hypothesis.title = match.title
        hypothesis.role_family = match.role_family
        hypothesis.current_alignment_score = match.alignment_score
        hypothesis.uncertainty_label = "Lower uncertainty" if match.status == "evaluated" else "Additional evidence required"
        dimensions = (match.source_metadata_json or {}).get("hypothesis_dimensions") or {}
        labels = dimensions.get("labels") or {}
        hypothesis.statement = (
            f"{match.title} is a provisional career hypothesis. "
            f"Natural Fit: {labels.get('natural_fit', 'Not assessed')}; "
            f"Capability Fit: {labels.get('capability_fit', 'Not assessed')}; "
            f"Evidence Strength: {labels.get('evidence_strength', 'Not assessed')}; "
            f"Transition Feasibility: {labels.get('transition_feasibility', 'Not assessed')}. "
            "Complete a role experiment before making a major career decision."
        )
        hypothesis.source_metadata_json = {"career_match_id": match.id, "scoring_version": match.scoring_version, "hypothesis_dimensions": dimensions}
        saved.append(hypothesis)
    db.commit()
    return saved


def create_experiment_session(db: Session, profile: Profile, payload: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
    sync_career_resilience_catalogue(db)
    template_id = payload.get("experiment_template_id") or payload.get("template_id")
    career_match_id = payload.get("career_match_id")
    if not template_id and career_match_id:
        match = db.get(CareerMatch, career_match_id)
        template = _template_for_match(db, match)
        template_id = template.id if template else None
    template = db.get(CareerExperimentTemplate, template_id) if template_id else None
    if not template or not template.active:
        raise LookupError("Career experiment template not found")
    if career_match_id:
        match = db.get(CareerMatch, career_match_id)
        if not match or match.profile_id != profile.id:
            raise LookupError("Career match not found for this profile")
    mode = payload.get("mode") or "guided"
    if mode not in EXPERIMENT_MODES:
        raise ValueError("Unsupported experiment mode")
    session = CareerExperimentSession(
        profile_id=profile.id,
        user_id=user_id or profile.user_id,
        career_match_id=career_match_id,
        experiment_template_id=template.id,
        mode=mode,
        status="planned",
        user_confirmed=bool(payload.get("user_confirmed", True)),
        demo_marker=bool(payload.get("demo_marker", _demo_marker(profile))),
        source_metadata_json={
            "created_from": "career_match" if career_match_id else "catalogue",
            "roadmap_confirmation_required": True,
        },
    )
    db.add(session)
    db.flush()
    if payload.get("add_to_roadmap"):
        action = _create_roadmap_action_for_experiment(db, profile, session, template)
        session.roadmap_action_id = action.id
    db.commit()
    db.refresh(session)
    return session_public(db, session)


def session_public(db: Session, row: CareerExperimentSession, include_details: bool = True) -> dict[str, Any]:
    template = db.get(CareerExperimentTemplate, row.experiment_template_id)
    submission = db.scalar(select(CareerExperimentSubmission).where(CareerExperimentSubmission.session_id == row.id).order_by(CareerExperimentSubmission.created_at.desc()))
    result = db.scalar(select(CareerExperimentResult).where(CareerExperimentResult.session_id == row.id).order_by(CareerExperimentResult.created_at.desc()))
    reviews = db.scalars(select(CareerExperimentReview).where(CareerExperimentReview.session_id == row.id).order_by(CareerExperimentReview.created_at)).all()
    payload = {
        "id": row.id,
        "profile_id": row.profile_id,
        "career_match_id": row.career_match_id,
        "experiment_template_id": row.experiment_template_id,
        "hypothesis_id": row.hypothesis_id,
        "roadmap_action_id": row.roadmap_action_id,
        "mode": row.mode,
        "status": row.status,
        "user_confirmed": row.user_confirmed,
        "demo_marker": row.demo_marker,
        "version": row.version,
        "source_metadata": row.source_metadata_json or {},
        "confidence_label": row.confidence_label,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "submitted_at": row.submitted_at.isoformat() if row.submitted_at else None,
        "evaluated_at": row.evaluated_at.isoformat() if row.evaluated_at else None,
        "template": template_public(db, template) if template and include_details else None,
        "submission": submission_public(submission) if submission else None,
        "result": result_public(result) if result else None,
        "reviews": [review_public(item) for item in reviews],
    }
    return payload


def submission_public(row: CareerExperimentSubmission) -> dict[str, Any]:
    return {
        "id": row.id,
        "session_id": row.session_id,
        "profile_id": row.profile_id,
        "text_response": row.text_response,
        "project_url": row.project_url,
        "repository_url": row.repository_url,
        "portfolio_url": row.portfolio_url,
        "document_metadata": row.document_metadata_json or {},
        "file_references": row.file_references_json or [],
        "completion_notes": row.completion_notes,
        "time_spent_minutes": row.time_spent_minutes,
        "ai_tools_used": row.ai_tools_used_json or [],
        "assistance_level": row.assistance_level,
        "self_rated_difficulty": row.self_rated_difficulty,
        "self_rated_enjoyment": row.self_rated_enjoyment,
        "confidence_before": row.confidence_before,
        "confidence_after": row.confidence_after,
        "reflection": row.reflection_json or {},
        "status": row.status,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def review_public(row: CareerExperimentReview) -> dict[str, Any]:
    return {
        "id": row.id,
        "session_id": row.session_id,
        "submission_id": row.submission_id,
        "profile_id": row.profile_id,
        "source_type": row.source_type,
        "reviewer_id": row.reviewer_id,
        "scores": row.scores_json or {},
        "narrative": row.narrative,
        "limitations": row.limitations_json or [],
        "created_at": row.created_at.isoformat(),
    }


def result_public(row: CareerExperimentResult) -> dict[str, Any]:
    return {
        "id": row.id,
        "session_id": row.session_id,
        "submission_id": row.submission_id,
        "profile_id": row.profile_id,
        "overall_score": row.overall_score,
        "overall_label": row.overall_label,
        "criteria_scores": row.criteria_scores_json or [],
        "skills_evaluated": row.skills_evaluated_json or [],
        "strengths": row.strengths_json or [],
        "improvement_areas": row.improvement_areas_json or [],
        "deterministic_version": row.deterministic_version,
        "evidence_created": row.evidence_created_json or [],
        "created_at": row.created_at.isoformat(),
    }


def list_profile_experiment_sessions(db: Session, profile_id: str) -> list[dict[str, Any]]:
    rows = db.scalars(select(CareerExperimentSession).where(CareerExperimentSession.profile_id == profile_id).order_by(CareerExperimentSession.updated_at.desc())).all()
    return [session_public(db, row) for row in rows]


def start_experiment(db: Session, session: CareerExperimentSession) -> dict[str, Any]:
    if session.status not in {"suggested", "saved", "planned"}:
        raise ValueError("Only suggested, saved, or planned experiments can be started")
    session.status = "in_progress"
    session.started_at = utc_now_naive()
    session.updated_at = utc_now_naive()
    db.commit()
    db.refresh(session)
    return session_public(db, session)


def _validate_submission(payload: dict[str, Any]) -> None:
    has_artifact = any(
        [
            str(payload.get("text_response") or "").strip(),
            payload.get("project_url"),
            payload.get("repository_url"),
            payload.get("portfolio_url"),
            payload.get("document_metadata"),
            payload.get("file_references"),
        ]
    )
    if not has_artifact:
        raise ValueError("Submit text, a URL, document metadata, or file references before review.")
    for key in ["project_url", "repository_url", "portfolio_url"]:
        if not safe_user_url(payload.get(key)):
            raise ValueError(f"Unsafe URL supplied for {key}.")
    if not str(payload.get("completion_notes") or "").strip():
        raise ValueError("Completion notes are required for manual evidence review.")


def submit_experiment(db: Session, session: CareerExperimentSession, payload: dict[str, Any]) -> dict[str, Any]:
    _validate_submission(payload)
    submission = CareerExperimentSubmission(
        session_id=session.id,
        profile_id=session.profile_id,
        user_id=session.user_id,
        text_response=payload.get("text_response") or "",
        project_url=payload.get("project_url"),
        repository_url=payload.get("repository_url"),
        portfolio_url=payload.get("portfolio_url"),
        document_metadata_json=payload.get("document_metadata") or {},
        file_references_json=payload.get("file_references") or [],
        completion_notes=payload.get("completion_notes") or "",
        time_spent_minutes=payload.get("time_spent_minutes"),
        ai_tools_used_json=payload.get("ai_tools_used") or [],
        assistance_level=payload.get("assistance_level") or "not_specified",
        self_rated_difficulty=payload.get("self_rated_difficulty"),
        self_rated_enjoyment=payload.get("self_rated_enjoyment"),
        confidence_before=payload.get("confidence_before"),
        confidence_after=payload.get("confidence_after"),
        reflection_json=payload.get("reflection") or {},
    )
    db.add(submission)
    session.status = "submitted"
    session.submitted_at = utc_now_naive()
    session.updated_at = utc_now_naive()
    db.commit()
    db.refresh(session)
    return session_public(db, session)


def self_review_experiment(db: Session, session: CareerExperimentSession, payload: dict[str, Any]) -> dict[str, Any]:
    submission = db.scalar(select(CareerExperimentSubmission).where(CareerExperimentSubmission.session_id == session.id).order_by(CareerExperimentSubmission.created_at.desc()))
    if not submission:
        raise ValueError("Submit deliverables before self-review.")
    review = CareerExperimentReview(
        session_id=session.id,
        submission_id=submission.id,
        profile_id=session.profile_id,
        source_type="self_review",
        scores_json={
            "difficulty": payload.get("self_rated_difficulty"),
            "enjoyment": payload.get("self_rated_enjoyment"),
            "confidence_before": payload.get("confidence_before"),
            "confidence_after": payload.get("confidence_after"),
        },
        narrative=payload.get("reflection") or "",
        limitations_json=["Self-review is stored separately from deterministic rubric evidence."],
    )
    db.add(review)
    session.status = "needs_review"
    session.updated_at = utc_now_naive()
    db.commit()
    db.refresh(session)
    return session_public(db, session)


def _criterion_rating(criterion: CareerExperimentCriterion, submission: CareerExperimentSubmission) -> int:
    text = " ".join(
        [
            submission.text_response or "",
            submission.completion_notes or "",
            " ".join(str(value) for value in (submission.reflection_json or {}).values()),
        ]
    ).lower()
    has_url = bool(submission.project_url or submission.repository_url or submission.portfolio_url)
    has_metadata = bool(submission.document_metadata_json or submission.file_references_json)
    rating = 1
    if len(text) >= 120 or has_url or has_metadata:
        rating += 1
    if len(text) >= 300 or (has_url and (submission.completion_notes or submission.reflection_json)):
        rating += 1
    if submission.time_spent_minutes and submission.time_spent_minutes >= 60 and (submission.reflection_json or submission.completion_notes):
        rating += 1
    if criterion.criterion_id == "testing_validation" and not any(word in text for word in ["test", "validate", "feedback", "review", "checklist", "metric"]):
        rating = min(rating, 2)
    if criterion.criterion_id == "human_centred" and not any(word in text for word in ["user", "human", "accessib", "stakeholder", "ethic", "trust", "learner"]):
        rating = min(rating, 3)
    if criterion.criterion_id == "role_specific_technique" and not any(word in text for word in ["prototype", "workflow", "rag", "rubric", "lesson", "design", "pipeline", "pilot"]):
        rating = min(rating, 2)
    return max(0, min(4, rating))


def evidence_strength_label(score: float, source_type: str) -> str:
    if source_type == "course_completion":
        return "Supported"
    if score >= 85:
        return "Practically verified"
    if score >= 65:
        return "Demonstrated"
    if score >= 45:
        return "Supported"
    return "Self-reported"


def confidence_label(score: float, source_count: int = 1) -> str:
    if source_count >= 3 and score >= 8:
        return "Multiple supporting sources"
    if score >= 8:
        return "Strong evidence"
    if score >= 6:
        return "Moderate evidence"
    if score >= 4:
        return "Emerging evidence"
    return "Limited evidence"


def _confidence_factors(evidence_type: str, practical: bool, specific: bool, independent: bool, recent: bool) -> dict[str, Any]:
    source_strength = {
        "self_reported": 1.0,
        "employment_experience": 2.0,
        "formal_education": 2.0,
        "certification": 2.5,
        "course_completion": 2.0,
        "practical_exercise": 3.0,
        "career_experiment": 3.5,
        "portfolio_project": 3.0,
        "professional_project": 4.0,
        "mentor_review": 4.0,
        "user_confirmed_external_evidence": 3.0,
    }.get(evidence_type, 1.0)
    factors = {
        "source_strength": source_strength,
        "practical_relevance": 2.0 if practical else 0.5,
        "recency": 1.5 if recent else 0.5,
        "specificity": 1.5 if specific else 0.5,
        "independent_confirmation": 1.5 if independent else 0,
    }
    factors["total_internal"] = round(sum(factors.values()), 2)
    return factors


def _recency_status(most_recent: datetime | None) -> tuple[str, int | None, str]:
    if not most_recent:
        return "Unknown", None, "Add dated evidence so recency can be assessed."
    age = (utc_now_naive() - most_recent).days
    if age <= 90:
        return "Current", age, "No refresh needed yet."
    if age <= 365:
        return "Recently demonstrated", age, "Keep evidence fresh with a small project or work sample."
    if age <= 730:
        return "Needs refresh", age, "Add recent practical evidence before relying on this skill for a transition."
    return "Outdated evidence", age, "Refresh this skill with recent practical or professional evidence."


def _upsert_recency(db: Session, profile_id: str, skill_id: str, evidence_date: datetime) -> SkillRecency:
    row = db.scalar(select(SkillRecency).where(SkillRecency.profile_id == profile_id, SkillRecency.skill_id == skill_id))
    if not row:
        row = SkillRecency(profile_id=profile_id, skill_id=skill_id, first_demonstrated_at=evidence_date)
    if not row.first_demonstrated_at or evidence_date < row.first_demonstrated_at:
        row.first_demonstrated_at = evidence_date
    if not row.most_recent_evidence_at or evidence_date > row.most_recent_evidence_at:
        row.most_recent_evidence_at = evidence_date
    status, age, recommendation = _recency_status(row.most_recent_evidence_at)
    row.status = status
    row.evidence_age_days = age
    row.refresh_recommendation = recommendation
    row.updated_at = utc_now_naive()
    db.add(row)
    return row


def _skill_label(skill_id: str) -> str:
    return title_case_slug(skill_id).replace("Ai", "AI").replace("Rag", "RAG").replace("Ux", "UX")


def _ensure_inventory(db: Session, profile_id: str, skill_id: str, level: int = 2, category: str = "career_experiment") -> SkillsInventory:
    row = db.scalar(select(SkillsInventory).where(SkillsInventory.profile_id == profile_id, SkillsInventory.skill_id == skill_id).order_by(SkillsInventory.created_at.desc()))
    if not row:
        profile = db.get(Profile, profile_id)
        assessment_session = db.scalar(
            select(AssessmentSession)
            .where(AssessmentSession.profile_id == profile_id, AssessmentSession.status == "completed")
            .order_by(AssessmentSession.updated_at.desc())
        ) or db.scalar(
            select(AssessmentSession)
            .where(AssessmentSession.profile_id == profile_id)
            .order_by(AssessmentSession.updated_at.desc())
        )
        if not assessment_session:
            assessment_session = AssessmentSession(
                profile_id=profile_id,
                user_id=profile.user_id if profile else None,
                mode="evidence_passport",
                status="evidence_only",
                consent_accepted=False,
                source_type="career_resilience",
                demo_marker=_demo_marker(profile),
                metadata_json={
                    "purpose": "Container for Evidence Passport skills created outside a completed assessment.",
                    "not_a_career_assessment": True,
                },
            )
            db.add(assessment_session)
            db.flush()
        row = SkillsInventory(
            session_id=assessment_session.id,
            profile_id=profile_id,
            user_id=assessment_session.user_id,
            category=category,
            skill_id=skill_id,
            skill_label=_skill_label(skill_id),
            level=level,
            evidence_status="demonstrated",
            evidence_note="Created from Career Resilience evidence.",
            demo_marker=assessment_session.demo_marker,
        )
        db.add(row)
        db.flush()
    else:
        row.level = max(row.level, level)
        if row.evidence_status in {"self_reported", "unverified"}:
            row.evidence_status = "demonstrated"
    return row


def _create_skill_evidence(
    db: Session,
    profile_id: str,
    skill_id: str,
    evidence_type: str,
    title: str,
    description: str,
    *,
    url: str | None = None,
    source_id: str | None = None,
    source_type: str | None = None,
    practical: bool = True,
    independent: bool = False,
    score_hint: float = 65,
) -> dict[str, Any]:
    inventory = _ensure_inventory(db, profile_id, skill_id, level=3 if score_hint >= 65 else 2)
    strength = evidence_strength_label(score_hint, evidence_type)
    evidence = SkillEvidence(
        skill_inventory_id=inventory.id,
        evidence_type=evidence_type,
        title=title,
        description=description,
        url=url,
        verification_status=strength.lower().replace(" ", "_"),
    )
    db.add(evidence)
    db.flush()
    factors = _confidence_factors(evidence_type, practical=practical, specific=True, independent=independent, recent=True)
    confidence = SkillEvidenceConfidence(
        skill_evidence_id=evidence.id,
        profile_id=profile_id,
        skill_id=skill_id,
        confidence_label=confidence_label(factors["total_internal"]),
        strength_label=strength,
        score_internal=factors["total_internal"],
        factors_json=factors,
        version=EVIDENCE_CONFIDENCE_VERSION,
    )
    source = SkillEvidenceSource(
        skill_evidence_id=evidence.id,
        profile_id=profile_id,
        source_type=source_type or evidence_type,
        source_id=source_id,
        title=title,
        url=url,
        source_metadata_json={"evidence_type": evidence_type, "automatic_file_analysis": False},
        independent_confirmation=independent,
    )
    db.add(confidence)
    db.add(source)
    _upsert_recency(db, profile_id, skill_id, evidence.created_at)
    return {
        "skill_id": skill_id,
        "skill_label": inventory.skill_label,
        "evidence_id": evidence.id,
        "confidence_label": confidence.confidence_label,
        "strength_label": confidence.strength_label,
    }


def evaluate_experiment(db: Session, session: CareerExperimentSession) -> dict[str, Any]:
    submission = db.scalar(select(CareerExperimentSubmission).where(CareerExperimentSubmission.session_id == session.id).order_by(CareerExperimentSubmission.created_at.desc()))
    if not submission:
        raise ValueError("Submit deliverables before deterministic evaluation.")
    template = db.get(CareerExperimentTemplate, session.experiment_template_id)
    rubric = db.scalar(select(CareerExperimentRubric).where(CareerExperimentRubric.experiment_template_id == template.id, CareerExperimentRubric.active.is_(True)))
    criteria = db.scalars(select(CareerExperimentCriterion).where(CareerExperimentCriterion.rubric_id == rubric.id).order_by(CareerExperimentCriterion.order_index)).all()
    criteria_scores = []
    weighted = 0.0
    total_weight = 0.0
    for criterion in criteria:
        rating = _criterion_rating(criterion, submission)
        weighted += rating * criterion.weight
        total_weight += criterion.weight
        criteria_scores.append(
            {
                "criterion_id": criterion.criterion_id,
                "skill_id": criterion.skill_id,
                "rating": rating,
                "weight": criterion.weight,
                "interpretation": (criterion.interpretation_json or {}).get(str(rating), "Deterministic rubric rating."),
            }
        )
    overall_score = round((weighted / max(total_weight, 0.01)) / 4 * 100, 2)
    overall = "Strong evidence" if overall_score >= 80 else "Competent evidence" if overall_score >= 65 else "Emerging evidence" if overall_score >= 40 else "Limited evidence"
    strengths = [item["criterion_id"] for item in criteria_scores if item["rating"] >= 3]
    improvement = [item["criterion_id"] for item in criteria_scores if item["rating"] <= 2]
    result = CareerExperimentResult(
        session_id=session.id,
        submission_id=submission.id,
        profile_id=session.profile_id,
        overall_score=overall_score,
        overall_label=overall,
        criteria_scores_json=criteria_scores,
        skills_evaluated_json=template.evaluated_skills_json or [],
        strengths_json=strengths,
        improvement_areas_json=improvement,
        deterministic_version=EXPERIMENT_EVAL_VERSION,
    )
    db.add(result)
    db.flush()
    evidence_created = []
    by_skill = defaultdict(list)
    for item in criteria_scores:
        by_skill[item["skill_id"]].append(item["rating"])
    for skill_id, ratings in by_skill.items():
        score_hint = round(sum(ratings) / max(1, len(ratings)) / 4 * 100, 2)
        evidence_created.append(
            _create_skill_evidence(
                db,
                session.profile_id,
                skill_id,
                "career_experiment",
                f"Career experiment: {template.title}",
                f"Deterministic rubric result from {template.target_role_family}. Overall score: {overall_score}.",
                url=submission.project_url or submission.repository_url or submission.portfolio_url,
                source_id=result.id,
                source_type="career_experiment_result",
                practical=True,
                independent=False,
                score_hint=score_hint,
            )
        )
    result.evidence_created_json = evidence_created
    db.add(
        CareerExperimentReview(
            session_id=session.id,
            submission_id=submission.id,
            profile_id=session.profile_id,
            source_type="deterministic_rubric",
            scores_json={"overall_score": overall_score, "criteria": criteria_scores},
            narrative="Deterministic rubric applied. No LLM changed the score.",
            limitations_json=[
                "This is role-experiment evidence, not certification.",
                "The result does not declare employment suitability.",
            ],
        )
    )
    session.status = "evaluated"
    session.evaluated_at = utc_now_naive()
    session.updated_at = utc_now_naive()
    session.confidence_label = "Evidence generated"
    db.commit()
    db.refresh(session)
    return session_public(db, session)


def add_manual_evidence(db: Session, profile: Profile, payload: dict[str, Any]) -> dict[str, Any]:
    evidence_type = payload.get("evidence_type") or "user_confirmed_external_evidence"
    if evidence_type == "course_completion":
        practical = False
    else:
        practical = evidence_type in {"practical_exercise", "career_experiment", "portfolio_project", "professional_project"}
    url = payload.get("url")
    if not safe_user_url(url):
        raise ValueError("Unsafe evidence URL.")
    item = _create_skill_evidence(
        db,
        profile.id,
        payload["skill_id"],
        evidence_type,
        payload.get("title") or "Manual skill evidence",
        payload.get("description") or "",
        url=url,
        source_id=payload.get("source_id"),
        source_type=evidence_type,
        practical=practical,
        independent=evidence_type in {"mentor_review", "certification", "professional_project"},
        score_hint=payload.get("score_hint", 55),
    )
    db.commit()
    return item


def update_evidence(db: Session, evidence: SkillEvidence, payload: dict[str, Any]) -> dict[str, Any]:
    for key in ["title", "description", "url", "verification_status"]:
        if key in payload and payload[key] is not None:
            if key == "url" and not safe_user_url(payload[key]):
                raise ValueError("Unsafe evidence URL.")
            setattr(evidence, key, payload[key])
    db.commit()
    return {"id": evidence.id, "title": evidence.title, "description": evidence.description, "url": evidence.url, "verification_status": evidence.verification_status}


def delete_evidence(db: Session, evidence: SkillEvidence) -> dict[str, Any]:
    db.execute(delete(SkillEvidenceConfidence).where(SkillEvidenceConfidence.skill_evidence_id == evidence.id))
    db.execute(delete(SkillEvidenceSource).where(SkillEvidenceSource.skill_evidence_id == evidence.id))
    db.delete(evidence)
    db.commit()
    return {"status": "deleted", "id": evidence.id}


def evidence_passport(db: Session, profile_id: str) -> dict[str, Any]:
    inventories = db.scalars(select(SkillsInventory).where(SkillsInventory.profile_id == profile_id).order_by(SkillsInventory.category, SkillsInventory.skill_label)).all()
    inventory_ids = [item.id for item in inventories]
    evidence_rows = db.scalars(select(SkillEvidence).where(SkillEvidence.skill_inventory_id.in_(inventory_ids))).all() if inventory_ids else []
    evidence_by_inventory = defaultdict(list)
    for row in evidence_rows:
        evidence_by_inventory[row.skill_inventory_id].append(row)
    confidence_rows = db.scalars(select(SkillEvidenceConfidence).where(SkillEvidenceConfidence.profile_id == profile_id)).all()
    sources = db.scalars(select(SkillEvidenceSource).where(SkillEvidenceSource.profile_id == profile_id)).all()
    source_by_evidence = defaultdict(list)
    for source in sources:
        source_by_evidence[source.skill_evidence_id].append(source)
    confidence_by_evidence = {row.skill_evidence_id: row for row in confidence_rows}
    recencies = {row.skill_id: row for row in db.scalars(select(SkillRecency).where(SkillRecency.profile_id == profile_id)).all()}
    matches = db.scalars(select(CareerMatch).where(CareerMatch.profile_id == profile_id, CareerMatch.status != "rejected")).all()
    roles_by_skill = defaultdict(list)
    for match in matches:
        for skill in (match.missing_skills_json or []):
            roles_by_skill[str(skill)].append(match.title)
    skills = []
    for inventory in inventories:
        evidence_items = []
        confidence_scores = []
        strength_labels = []
        for evidence in evidence_by_inventory.get(inventory.id, []):
            confidence = confidence_by_evidence.get(evidence.id)
            if confidence:
                confidence_scores.append(confidence.score_internal)
                strength_labels.append(confidence.strength_label)
            evidence_items.append(
                {
                    "id": evidence.id,
                    "type": evidence.evidence_type,
                    "title": evidence.title,
                    "description": evidence.description,
                    "url": evidence.url,
                    "verification_status": evidence.verification_status,
                    "created_at": evidence.created_at.isoformat(),
                    "sources": [
                        {
                            "id": source.id,
                            "source_type": source.source_type,
                            "title": source.title,
                            "url": source.url,
                            "independent_confirmation": source.independent_confirmation,
                        }
                        for source in source_by_evidence.get(evidence.id, [])
                    ],
                    "confidence": confidence.confidence_label if confidence else "Limited evidence",
                    "strength": confidence.strength_label if confidence else "Self-reported",
                }
            )
        recency = recencies.get(inventory.skill_id)
        aggregate_score = max(confidence_scores) if confidence_scores else (2.5 if inventory.evidence_status != "self_reported" else 1.5)
        skills.append(
            {
                "skill_id": inventory.skill_id,
                "skill_label": inventory.skill_label,
                "category": inventory.category,
                "declared_level": inventory.level,
                "target_level": max(3, inventory.level) if roles_by_skill.get(inventory.skill_id) else inventory.level,
                "evidence_confidence": confidence_label(aggregate_score, len(evidence_items)),
                "strongest_evidence_label": strength_labels[0] if strength_labels else ("Self-reported" if inventory.evidence_status == "self_reported" else "Supported"),
                "evidence_sources": evidence_items,
                "recency": {
                    "first_demonstrated_date": recency.first_demonstrated_at.isoformat() if recency and recency.first_demonstrated_at else None,
                    "most_recent_evidence_date": recency.most_recent_evidence_at.isoformat() if recency and recency.most_recent_evidence_at else None,
                    "last_professional_use": recency.last_professional_use_at.isoformat() if recency and recency.last_professional_use_at else None,
                    "evidence_age_days": recency.evidence_age_days if recency else None,
                    "refresh_recommendation": recency.refresh_recommendation if recency else "Add dated evidence so recency can be assessed.",
                    "status": recency.status if recency else "Unknown",
                },
                "status": "Needs verification" if not evidence_items else "Evidence available",
                "related_roles": sorted(set(roles_by_skill.get(inventory.skill_id, []))),
                "outstanding_verification_needs": [] if strength_labels else ["Add practical or externally confirmed evidence."],
            }
        )
    return {
        "profile_id": profile_id,
        "version": "evidence-passport-v1",
        "methodology": "Self-reported, demonstrated, and externally supported evidence are stored separately. Course completion alone does not create practical verification.",
        "skills": skills,
        "generated_at": utc_now_naive().isoformat(),
    }


def _match_related_to_template(match: CareerMatch, template: CareerExperimentTemplate) -> bool:
    combined = f"{match.title} {match.role_family}".lower()
    target = template.target_role_family.lower()
    aliases = ROLE_EXPERIMENT_MAP.get(target, [target])
    return any(alias in combined for alias in aliases) or target in combined


def _counterfactuals(match: CareerMatch, has_experiment: bool) -> dict[str, list[str]]:
    strengthen = []
    if not has_experiment:
        strengthen.append("Complete one role experiment.")
    strengthen.extend([f"Obtain recent evidence for {skill}." for skill in (match.missing_skills_json or [])[:3]])
    strengthen.extend(["Demonstrate one practical project.", "Provide portfolio evidence.", "Complete a market-relevant certification where appropriate."])
    weaken = [
        "Repeated low interest in role tasks.",
        "Weak evidence after multiple experiments.",
        "Changing career values or feasibility constraints.",
        "Low local demand or unavailable support routes.",
    ]
    return {"what_would_strengthen": strengthen, "what_would_weaken": weaken}


def recalibrate_career_recommendations(db: Session, profile: Profile, experiment_result_id: str | None = None) -> dict[str, Any]:
    result = db.get(CareerExperimentResult, experiment_result_id) if experiment_result_id else db.scalar(select(CareerExperimentResult).where(CareerExperimentResult.profile_id == profile.id).order_by(CareerExperimentResult.created_at.desc()))
    session = db.get(CareerExperimentSession, result.session_id) if result else None
    template = db.get(CareerExperimentTemplate, session.experiment_template_id) if session else None
    matches = db.scalars(select(CareerMatch).where(CareerMatch.profile_id == profile.id, CareerMatch.status != "rejected").order_by(CareerMatch.alignment_score.desc())).all()
    before = {
        "career_alignment": [{"career_match_id": match.id, "title": match.title, "alignment_score": match.alignment_score, "alignment_label": match.alignment_label} for match in matches],
        "assumptions": [item for match in matches for item in (match.assumptions_json or [])][:8],
        "missing_evidence": [item for match in matches for item in (match.missing_skills_json or [])][:8],
        "uncertainty": "Additional evidence required",
    }
    changed = []
    factors = []
    for match in matches:
        has_experiment = bool(result and template and _match_related_to_template(match, template))
        before_score = match.alignment_score
        after_score = before_score
        if has_experiment:
            delta = 8 if result.overall_score >= 80 else 5 if result.overall_score >= 65 else 0 if result.overall_score >= 40 else -6
            after_score = max(0, min(100, round(before_score + delta, 2)))
            demonstrated = {item["skill_id"] for item in (result.criteria_scores_json or []) if item.get("rating", 0) >= 3}
            match.missing_skills_json = [skill for skill in (match.missing_skills_json or []) if skill not in demonstrated]
            match.alignment_score = after_score
            match.alignment_label = alignment_label(after_score)
            metadata = dict(match.source_metadata_json or {})
            dimensions = dict(metadata.get("hypothesis_dimensions") or {})
            dimension_scores = dict(dimensions.get("scores") or {})
            before_dimension_scores = dict(dimension_scores)
            if dimension_scores:
                evidence_after = max(float(dimension_scores.get("evidence_strength", 0)), 78 if result.overall_score >= 80 else 65 if result.overall_score >= 65 else 45 if result.overall_score >= 40 else 25)
                dimension_scores["evidence_strength"] = round(min(100, evidence_after), 2)
                dimension_scores["capability_fit"] = round(min(100, float(dimension_scores.get("capability_fit", 0)) + max(0, delta) * 0.35), 2)
                dimensions["scores"] = dimension_scores
                dimensions["labels"] = {key: fit_label(value) for key, value in dimension_scores.items()}
                dimensions["last_change"] = {
                    "evidence_strength": "Career experiment evidence was added to the Evidence Passport.",
                    "capability_fit": "Capability interpretation was adjusted only where experiment evidence supported relevant skills.",
                    "natural_fit": "Unchanged; the experiment did not rewrite stated interests or preferences.",
                    "transition_feasibility": "Unchanged by this evidence event.",
                }
                metadata["hypothesis_dimensions"] = dimensions
            metadata["career_resilience"] = {
                "latest_recalibration_reason": "career_experiment_result",
                "latest_experiment_result_id": result.id,
                "what_changed": f"The recommendation became stronger after {template.title}." if delta > 0 else "The recommendation remains uncertain because the experiment evidence was limited.",
                "dimension_changes": {
                    "before": before_dimension_scores,
                    "after": dimension_scores,
                    "changed_categories": ["evidence_strength"] + (["capability_fit"] if delta > 0 else []),
                    "unchanged_categories": ["natural_fit", "transition_feasibility"],
                },
                **_counterfactuals(match, has_experiment=True),
            }
            match.source_metadata_json = metadata
            flag_modified(match, "source_metadata_json")
            changed.append(
                {
                    "career_match_id": match.id,
                    "title": match.title,
                    "before_alignment": before_score,
                    "after_alignment": after_score,
                    "change": round(after_score - before_score, 2),
                    "what_changed": metadata["career_resilience"]["what_changed"],
                    "dimension_changes": metadata["career_resilience"]["dimension_changes"],
                    "remaining_gaps": match.missing_skills_json or [],
                    **_counterfactuals(match, has_experiment=True),
                }
            )
            factors.append(
                {
                    "factor_type": "career_experiment",
                    "label": template.title,
                    "before_value": before_score,
                    "after_value": after_score,
                    "weight": 1.0,
                    "explanation": "Deterministic rubric result updated skill evidence and uncertainty.",
                }
            )
        else:
            metadata = dict(match.source_metadata_json or {})
            metadata.setdefault("career_resilience", _counterfactuals(match, has_experiment=False))
            match.source_metadata_json = metadata
            flag_modified(match, "source_metadata_json")
    after = {
        "career_alignment": [{"career_match_id": match.id, "title": match.title, "alignment_score": match.alignment_score, "alignment_label": match.alignment_label} for match in matches],
        "new_evidence": result.evidence_created_json if result else [],
        "remaining_gaps": [item for match in matches for item in (match.missing_skills_json or [])][:8],
        "uncertainty": "Reduced but still present" if changed else "Additional evidence required",
    }
    run = CareerRecalibrationRun(
        profile_id=profile.id,
        user_id=profile.user_id,
        career_match_id=session.career_match_id if session else None,
        experiment_result_id=result.id if result else None,
        before_json=before,
        after_json=after,
        changed_recommendations_json=changed,
        explanation="What changed this recommendation? Structured experiment evidence was added to the Evidence Passport and deterministic career factors were recalculated.",
        uncertainty_label=after["uncertainty"],
        demo_marker=_demo_marker(profile),
    )
    db.add(run)
    db.flush()
    for factor in factors:
        db.add(CareerRecalibrationFactor(run_id=run.id, **factor))
    db.commit()
    return recalibration_public(db, run)


def recalibration_public(db: Session, run: CareerRecalibrationRun) -> dict[str, Any]:
    factors = db.scalars(select(CareerRecalibrationFactor).where(CareerRecalibrationFactor.run_id == run.id)).all()
    return {
        "id": run.id,
        "profile_id": run.profile_id,
        "career_match_id": run.career_match_id,
        "experiment_result_id": run.experiment_result_id,
        "status": run.status,
        "before": run.before_json or {},
        "after": run.after_json or {},
        "changed_recommendations": run.changed_recommendations_json or [],
        "explanation": run.explanation,
        "uncertainty_label": run.uncertainty_label,
        "version": run.version,
        "factors": [
            {
                "id": factor.id,
                "factor_type": factor.factor_type,
                "label": factor.label,
                "before_value": factor.before_value,
                "after_value": factor.after_value,
                "weight": factor.weight,
                "explanation": factor.explanation,
            }
            for factor in factors
        ],
        "created_at": run.created_at.isoformat(),
    }


def latest_recalibration(db: Session, profile_id: str) -> dict[str, Any] | None:
    run = db.scalar(select(CareerRecalibrationRun).where(CareerRecalibrationRun.profile_id == profile_id).order_by(CareerRecalibrationRun.created_at.desc()))
    return recalibration_public(db, run) if run else None


def _fit_label(score: float) -> str:
    if score >= 78:
        return "Strong"
    if score >= 55:
        return "Moderate"
    if score >= 35:
        return "Developing"
    return "Limited"


def _market_label(signal: MarketRoleSignal | None) -> str:
    if not signal:
        return "Additional information required"
    if signal.opportunity_count >= 14:
        return "Moderate"
    if signal.opportunity_count >= 8:
        return "Moderate"
    if signal.opportunity_count > 0:
        return "Limited"
    return "Additional information required"


def _support_label(screening: SupportScreening | None) -> str:
    if not screening:
        return "Additional information required"
    labels = [item.get("preliminary_label") for item in (screening.preliminary_result_json or {}).get("programmes", [])]
    if "Potentially relevant" in labels:
        return "Potentially relevant"
    if "Possibly relevant" in labels:
        return "Possibly relevant"
    if labels:
        return "Additional information required"
    return "Additional information required"


def _signal_for_match(signals: list[MarketRoleSignal], match: CareerMatch) -> MarketRoleSignal | None:
    related = _related_role_family(match).lower()
    for signal in signals:
        if signal.role_family.lower() == related:
            return signal
    return None


def create_supported_paths(db: Session, profile: Profile, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    sync_career_resilience_catalogue(db)
    snapshot_row = db.scalar(select(MarketSnapshot).where(MarketSnapshot.country == "Norway", MarketSnapshot.status == "active").order_by(MarketSnapshot.created_at.desc()))
    signals = db.scalars(select(MarketRoleSignal).where(MarketRoleSignal.snapshot_id == snapshot_row.id)).all() if snapshot_row else []
    screening = db.scalar(select(SupportScreening).where(SupportScreening.profile_id == profile.id).order_by(SupportScreening.created_at.desc()))
    matches = db.scalars(select(CareerMatch).where(CareerMatch.profile_id == profile.id, CareerMatch.status != "rejected").order_by(CareerMatch.alignment_score.desc()).limit(4)).all()
    templates = db.scalars(select(CareerExperimentTemplate).where(CareerExperimentTemplate.active.is_(True))).all()
    run = SupportedPathRun(
        profile_id=profile.id,
        user_id=profile.user_id,
        market_snapshot_id=snapshot_row.id if snapshot_row else None,
        support_screening_id=screening.id if screening else None,
        demo_marker=_demo_marker(profile),
    )
    db.add(run)
    db.flush()
    if not matches:
        db.commit()
        return supported_path_run_public(db, run)
    for match in matches:
        signal = _signal_for_match(signals, match)
        required_template = next((template for template in templates if _match_related_to_template(match, template)), None)
        missing = match.missing_skills_json or []
        dimensions = ((match.source_metadata_json or {}).get("hypothesis_dimensions") or {}).get("scores") or {}
        natural_score = float(dimensions.get("natural_fit", match.alignment_score))
        capability_score = float(dimensions.get("capability_fit", max(20, min(100, match.alignment_score - len(missing) * 7))))
        evidence_score = float(dimensions.get("evidence_strength", 30))
        transition_score = float(dimensions.get("transition_feasibility", 50))
        support_programmes = (screening.preliminary_result_json or {}).get("programmes", [])[:3] if screening else []
        result = SupportedPathResult(
            run_id=run.id,
            profile_id=profile.id,
            career_match_id=match.id,
            role_family=_related_role_family(match) or match.role_family,
            title=match.title,
            personal_fit_label=_fit_label(natural_score),
            capability_fit_label=_fit_label(capability_score),
            market_fit_label=_market_label(signal),
            support_fit_label=_support_label(screening),
            transition_difficulty=match.transition_difficulty,
            estimated_preparation_range=match.time_horizon,
            main_strengths_json=(match.supporting_factors_json or [])[:4],
            main_gaps_json=missing[:4],
            main_uncertainties_json=(match.assumptions_json or [])[:2] + (match.limitations_json or [])[:2] + ["Market data is a demo snapshot, not live coverage."],
            required_experiment_id=required_template.id if required_template else None,
            required_experiment_title=required_template.title if required_template else "Select a role experiment before committing.",
            possible_public_support_json=support_programmes,
            next_best_action=f"Review and confirm a role experiment for {match.title}.",
            official_assessment_required=True,
            factor_scores_json={
                "personal_fit": natural_score,
                "capability_fit": capability_score,
                "evidence_strength": evidence_score,
                "transition_feasibility": transition_score,
                "market_fit_source": signal.role_family if signal else None,
                "support_fit_source": screening.id if screening else None,
            },
        )
        db.add(result)
    db.commit()
    db.refresh(run)
    return supported_path_run_public(db, run)


def supported_path_run_public(db: Session, run: SupportedPathRun) -> dict[str, Any]:
    rows = db.scalars(select(SupportedPathResult).where(SupportedPathResult.run_id == run.id).order_by(SupportedPathResult.created_at)).all()
    return {
        "id": run.id,
        "profile_id": run.profile_id,
        "market_snapshot_id": run.market_snapshot_id,
        "support_screening_id": run.support_screening_id,
        "status": run.status,
        "version": run.version,
        "created_at": run.created_at.isoformat(),
        "results": [
            {
                "id": row.id,
                "career_match_id": row.career_match_id,
                "role_family": row.role_family,
                "title": row.title,
                "personal_fit": row.personal_fit_label,
                "capability_fit": row.capability_fit_label,
                "market_fit": row.market_fit_label,
                "support_fit": row.support_fit_label,
                "transition_difficulty": row.transition_difficulty,
                "estimated_preparation_range": row.estimated_preparation_range,
                "main_strengths": row.main_strengths_json or [],
                "main_gaps": row.main_gaps_json or [],
                "main_uncertainties": row.main_uncertainties_json or [],
                "required_experiment_id": row.required_experiment_id,
                "required_experiment_title": row.required_experiment_title,
                "possible_public_support": row.possible_public_support_json or [],
                "next_best_action": row.next_best_action,
                "official_assessment_required": row.official_assessment_required,
                "factor_scores": row.factor_scores_json or {},
            }
            for row in rows
        ],
    }


def latest_supported_paths(db: Session, profile_id: str) -> dict[str, Any]:
    run = db.scalar(select(SupportedPathRun).where(SupportedPathRun.profile_id == profile_id).order_by(SupportedPathRun.created_at.desc()))
    return supported_path_run_public(db, run) if run else {"status": "not_started", "results": []}


def support_programme_public(row: SupportProgrammeVersion) -> dict[str, Any]:
    return {
        "programme_id": row.programme_id,
        "norwegian_name": row.norwegian_name,
        "english_name": row.english_name,
        "authority": row.authority,
        "jurisdiction": row.jurisdiction,
        "official_url": row.official_url,
        "summary": row.summary,
        "target_group": row.target_group,
        "known_conditions": row.known_conditions_json or [],
        "required_information": row.required_information_json or [],
        "application_or_contact_route": row.application_or_contact_route,
        "documents": row.documents_json or [],
        "deadlines": row.deadlines_json or [],
        "incompatibilities": row.incompatibilities_json or [],
        "source_publication_date": row.source_publication_date,
        "last_checked_date": row.last_checked_date,
        "rule_version": row.rule_version,
        "verification_status": row.verification_status,
        "human_assessment_required": row.human_assessment_required,
        "limitations": row.limitations_json or [],
        "categories": row.categories_json or [],
    }


def list_support_programmes(db: Session) -> list[dict[str, Any]]:
    sync_career_resilience_catalogue(db)
    rows = db.scalars(select(SupportProgrammeVersion).order_by(SupportProgrammeVersion.english_name)).all()
    return [support_programme_public(row) for row in rows]


def get_support_programme(db: Session, programme_id: str) -> dict[str, Any]:
    sync_career_resilience_catalogue(db)
    row = db.scalar(select(SupportProgrammeVersion).where(SupportProgrammeVersion.programme_id == programme_id).order_by(SupportProgrammeVersion.created_at.desc()))
    if not row:
        raise LookupError("Support programme not found")
    return support_programme_public(row)


def upsert_job_loss_profile(db: Session, profile: Profile, payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("consent_accepted"):
        raise ValueError("Consent is required before Job Loss Mode stores job-loss information.")
    row = db.scalar(select(JobLossProfile).where(JobLossProfile.profile_id == profile.id).order_by(JobLossProfile.created_at.desc()))
    if not row:
        row = JobLossProfile(profile_id=profile.id, user_id=profile.user_id, demo_marker=_demo_marker(profile))
    for key in [
        "country_of_residence",
        "country_of_employment",
        "municipality_or_region",
        "last_working_date",
        "contract_termination_type",
        "employment_status",
        "reduction_in_working_hours",
        "jobseeker_registration_status",
        "work_permit_or_residency_status",
        "education",
        "training_interest",
        "availability_for_work",
        "relocation_preferences",
    ]:
        if key in payload:
            setattr(row, key, payload[key] or "")
    row.current_benefits_json = payload.get("current_benefits") or []
    row.consent_accepted = True
    row.sensitive_explanations_json = {
        "work_permit_or_residency_status": "Requested only where residence or work authorization may affect which authority can assess support.",
        "current_benefits": "Requested because some benefits can affect or combine with other support. It remains optional in this prototype.",
        "last_working_date": "Requested to help prioritise actions and deadlines without calculating legal eligibility.",
    }
    row.updated_at = utc_now_naive()
    db.add(row)
    db.commit()
    db.refresh(row)
    return job_loss_profile_public(row)


def job_loss_profile_public(row: JobLossProfile | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "consent_accepted": row.consent_accepted,
        "country_of_residence": row.country_of_residence,
        "country_of_employment": row.country_of_employment,
        "municipality_or_region": row.municipality_or_region,
        "last_working_date": row.last_working_date,
        "contract_termination_type": row.contract_termination_type,
        "employment_status": row.employment_status,
        "reduction_in_working_hours": row.reduction_in_working_hours,
        "jobseeker_registration_status": row.jobseeker_registration_status,
        "current_benefits": row.current_benefits_json or [],
        "work_permit_or_residency_status": row.work_permit_or_residency_status,
        "education": row.education,
        "training_interest": row.training_interest,
        "availability_for_work": row.availability_for_work,
        "relocation_preferences": row.relocation_preferences,
        "sensitive_explanations": row.sensitive_explanations_json or {},
        "status": row.status,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def latest_job_loss_profile(db: Session, profile_id: str) -> dict[str, Any] | None:
    row = db.scalar(select(JobLossProfile).where(JobLossProfile.profile_id == profile_id).order_by(JobLossProfile.created_at.desc()))
    return job_loss_profile_public(row)


def _official_source(programme_id: str, title: str | None = None) -> dict[str, str]:
    url_map = {item["id"]: item["official_url"] for item in support_programme_catalogue()}
    return {"title": title or programme_id.replace("_", " "), "url": url_map[programme_id], "last_checked_date": SUPPORT_LAST_CHECKED}


def create_immediate_action_plan(db: Session, profile: Profile) -> dict[str, Any]:
    job = db.scalar(select(JobLossProfile).where(JobLossProfile.profile_id == profile.id).order_by(JobLossProfile.created_at.desc()))
    if not job:
        raise ValueError("Create a Job Loss profile before generating immediate actions.")
    existing = db.scalars(select(ImmediateActionPlan).where(ImmediateActionPlan.profile_id == profile.id)).all()
    for plan in existing:
        db.execute(delete(ImmediateActionItem).where(ImmediateActionItem.plan_id == plan.id))
        db.delete(plan)
    plan = ImmediateActionPlan(profile_id=profile.id, user_id=profile.user_id, job_loss_profile_id=job.id, demo_marker=_demo_marker(profile))
    db.add(plan)
    db.flush()
    actions = [
        ("Register as a jobseeker", "Registration unlocks NAV follow-up and is required before applying for some support.", "immediate", "nav_jobseeker_registration"),
        ("Check unemployment benefit guidance", "NAV guidance says unemployment benefit may require application, registration, and 14-day reporting.", "immediate", "nav_unemployment_benefit"),
        ("Gather employment documents", "Documents such as contract, termination notice, income history, and references help official assessment and applications.", "high", "arbeidstilsynet_dismissal_guidance"),
        ("Verify employment status form requirements", "If applying for or receiving unemployment benefit, NAV describes recurring employment-status reporting.", "high", "nav_employment_status_form"),
        ("Contact a NAV adviser about training or work measures", "Training, work training, or wage subsidy routes require NAV assessment.", "medium", "nav_training_measures"),
        ("Compare realistic career directions", "Use supported paths to compare personal, capability, market, and support fit before committing.", "medium", "nav_work_training"),
    ]
    for index, (title, reason, urgency, programme_id) in enumerate(actions, start=1):
        db.add(
            ImmediateActionItem(
                plan_id=plan.id,
                profile_id=profile.id,
                title=title,
                reason=reason,
                urgency=urgency,
                official_source_json=_official_source(programme_id),
                status="not_started",
                due_date=None,
                user_confirmation=False,
                order_index=index,
            )
        )
    db.commit()
    db.refresh(plan)
    return immediate_action_plan_public(db, plan)


def immediate_action_plan_public(db: Session, plan: ImmediateActionPlan) -> dict[str, Any]:
    rows = db.scalars(select(ImmediateActionItem).where(ImmediateActionItem.plan_id == plan.id).order_by(ImmediateActionItem.order_index)).all()
    return {
        "id": plan.id,
        "profile_id": plan.profile_id,
        "job_loss_profile_id": plan.job_loss_profile_id,
        "status": plan.status,
        "version": plan.version,
        "created_at": plan.created_at.isoformat(),
        "updated_at": plan.updated_at.isoformat(),
        "items": [
            {
                "id": row.id,
                "title": row.title,
                "reason": row.reason,
                "urgency": row.urgency,
                "official_source": row.official_source_json,
                "status": row.status,
                "due_date": row.due_date,
                "user_confirmation": row.user_confirmation,
            }
            for row in rows
        ],
    }


def latest_immediate_action_plan(db: Session, profile_id: str) -> dict[str, Any] | None:
    plan = db.scalar(select(ImmediateActionPlan).where(ImmediateActionPlan.profile_id == profile_id).order_by(ImmediateActionPlan.created_at.desc()))
    return immediate_action_plan_public(db, plan) if plan else None


def _screen_programme(programme: SupportProgrammeVersion, values: dict[str, Any]) -> tuple[str, list[str], str]:
    country = (values.get("country_of_residence") or values.get("country") or "").lower()
    employment_status = (values.get("employment_status") or "").lower()
    jobseeker = (values.get("jobseeker_registration_status") or "").lower()
    training_interest = (values.get("training_interest") or "").lower()
    work_hours_reduction = values.get("reduction_in_working_hours")
    unknown = []
    if country and country not in {"norway", "norge"}:
        return "Probably not applicable", [], "This MVP screens Norway-only support records."
    if programme.programme_id == "nav_jobseeker_registration":
        if not country:
            unknown.append("country_of_residence")
        return ("Potentially relevant" if jobseeker not in {"registered", "yes"} else "Possibly relevant"), unknown, "Registration may be relevant before benefit applications or NAV follow-up."
    if programme.programme_id == "nav_unemployment_benefit":
        for field in ["country_of_residence", "employment_status", "jobseeker_registration_status", "reduction_in_working_hours"]:
            if values.get(field) in {None, ""}:
                unknown.append(field)
        if unknown:
            return "Additional information required", unknown, "NAV unemployment benefit rules require more work, residence, registration, and income context."
        if employment_status in {"unemployed", "temporarily_laid_off", "laid_off"} or (isinstance(work_hours_reduction, int) and work_hours_reduction >= 50):
            return "Potentially relevant", unknown, "The situation resembles a job-loss or reduced-hours case, but NAV must assess all conditions."
        return "Probably not applicable", unknown, "The current intake does not indicate unemployment or a large working-hours reduction."
    if programme.programme_id == "nav_employment_status_form":
        if jobseeker in {"registered", "yes"} or employment_status in {"unemployed", "temporarily_laid_off", "laid_off"}:
            return "Potentially relevant", [], "NAV describes 14-day reporting for relevant unemployment benefit situations."
        return "Additional information required", ["jobseeker_registration_status"], "Reporting depends on registration and benefit context."
    if programme.programme_id in {"nav_training_measures", "nav_supplemental_benefit"}:
        if not training_interest:
            return "Additional information required", ["training_interest"], "Training support relevance depends on training goals and NAV assessment."
        return ("Possibly relevant" if training_interest in {"yes", "interested", "high", "medium"} else "Additional information required"), [], "Training-related support may be relevant if NAV assesses it as appropriate."
    if programme.programme_id in {"nav_work_training", "nav_temporary_wage_subsidy"}:
        if not values.get("availability_for_work"):
            unknown.append("availability_for_work")
        return "Possibly relevant" if not unknown else "Additional information required", unknown, "Employment measures depend on NAV assessment, work ability, and employer or placement context."
    if programme.programme_id == "nav_qualification_programme":
        return "Additional information required", ["age", "need_for_extra_follow_up", "income_support_context"], "Qualification Programme relevance requires a broader NAV or municipal assessment."
    return "Possibly relevant", [], "Official guidance may be useful for preparing questions, but it is not an eligibility result."


def run_support_screening(db: Session, profile: Profile, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    sync_career_resilience_catalogue(db)
    job = db.scalar(select(JobLossProfile).where(JobLossProfile.profile_id == profile.id).order_by(JobLossProfile.created_at.desc()))
    values = dict(payload or {})
    if job:
        values = {**job_loss_profile_public(job), **values}
    programmes = db.scalars(select(SupportProgrammeVersion).order_by(SupportProgrammeVersion.english_name)).all()
    screening = SupportScreening(
        profile_id=profile.id,
        user_id=profile.user_id,
        job_loss_profile_id=job.id if job else None,
        country=values.get("country_of_residence") or values.get("country") or "Norway",
        input_values_json=values,
        rule_version=SUPPORT_RULE_VERSION,
        demo_marker=_demo_marker(profile),
    )
    db.add(screening)
    db.flush()
    results = []
    unknown_all = set()
    sources = []
    for programme in programmes:
        label, unknown, explanation = _screen_programme(programme, values)
        unknown_all.update(unknown)
        source_ref = {"programme_id": programme.programme_id, "title": programme.english_name, "url": programme.official_url, "last_checked_date": programme.last_checked_date}
        sources.append(source_ref)
        result = {
            "programme_id": programme.programme_id,
            "programme_name": programme.english_name,
            "preliminary_label": label,
            "explanation": explanation,
            "unknown_fields": unknown,
            "official_source": source_ref,
            "human_assessment_required": True,
        }
        results.append(result)
        db.add(
            SupportScreeningFactor(
                screening_id=screening.id,
                programme_id=programme.programme_id,
                input_values_json=values,
                unknown_fields_json=unknown,
                preliminary_label=label,
                explanation=explanation,
                source_references_json=[source_ref],
                last_checked_date=programme.last_checked_date,
                rule_version=programme.rule_version,
            )
        )
    screening.unknown_fields_json = sorted(unknown_all)
    screening.preliminary_result_json = {
        "programmes": results,
        "limitations": [
            "Final eligibility is determined by the responsible authority.",
            "This screening is preliminary and deterministic.",
        ],
    }
    screening.source_references_json = sources
    db.commit()
    db.refresh(screening)
    return support_screening_public(db, screening)


def support_screening_public(db: Session, screening: SupportScreening) -> dict[str, Any]:
    factors = db.scalars(select(SupportScreeningFactor).where(SupportScreeningFactor.screening_id == screening.id)).all()
    return {
        "id": screening.id,
        "profile_id": screening.profile_id,
        "job_loss_profile_id": screening.job_loss_profile_id,
        "status": screening.status,
        "country": screening.country,
        "input_values": screening.input_values_json or {},
        "unknown_fields": screening.unknown_fields_json or [],
        "preliminary_result": screening.preliminary_result_json or {},
        "source_references": screening.source_references_json or [],
        "rule_version": screening.rule_version,
        "created_at": screening.created_at.isoformat(),
        "factors": [
            {
                "programme_id": factor.programme_id,
                "preliminary_label": factor.preliminary_label,
                "unknown_fields": factor.unknown_fields_json or [],
                "explanation": factor.explanation,
                "source_references": factor.source_references_json or [],
                "rule_version": factor.rule_version,
            }
            for factor in factors
        ],
    }


def latest_support_screening(db: Session, profile_id: str) -> dict[str, Any] | None:
    row = db.scalar(select(SupportScreening).where(SupportScreening.profile_id == profile_id).order_by(SupportScreening.created_at.desc()))
    return support_screening_public(db, row) if row else None


BRIEF_DISCLAIMER = "This document supports preparation for a discussion with the relevant authority. It is not an eligibility decision or legal advice."


def generate_support_brief(db: Session, profile: Profile) -> dict[str, Any]:
    job = db.scalar(select(JobLossProfile).where(JobLossProfile.profile_id == profile.id).order_by(JobLossProfile.created_at.desc()))
    screening = db.scalar(select(SupportScreening).where(SupportScreening.profile_id == profile.id).order_by(SupportScreening.created_at.desc()))
    paths = db.scalar(select(SupportedPathRun).where(SupportedPathRun.profile_id == profile.id).order_by(SupportedPathRun.created_at.desc()))
    passport = evidence_passport(db, profile.id)
    path_results = supported_path_run_public(db, paths)["results"] if paths else []
    programmes = (screening.preliminary_result_json or {}).get("programmes", [])[:5] if screening else []
    unresolved = sorted(set((screening.unknown_fields_json or []) if screening else ["job_loss_profile", "support_screening"]))
    content = {
        "current_employment_situation": job_loss_profile_public(job) if job else None,
        "professional_background": (profile.data or {}).get("primary_archetype", {}),
        "transferable_skills": [skill["skill_label"] for skill in passport["skills"] if skill["declared_level"] >= 2][:8],
        "proposed_career_direction": path_results[0]["title"] if path_results else "Career direction not yet selected",
        "market_relevance": path_results[0]["market_fit"] if path_results else "Additional information required",
        "capability_gaps": path_results[0]["main_gaps"] if path_results else [],
        "selected_course_or_training": "To be discussed with NAV or the responsible authority.",
        "proposed_career_experiment": path_results[0]["required_experiment_title"] if path_results else "Select a role experiment first.",
        "expected_outcome": "Generate practical evidence, clarify fit, and reduce transition uncertainty.",
        "possible_support_programmes": programmes,
        "questions_for_adviser": [
            "Which measures may be relevant for this situation?",
            "What documentation should be prepared before applying?",
            "Can targeted training or work-oriented qualification be assessed?",
            "What obligations or reporting deadlines should be prioritised?",
        ],
        "official_source_references": (screening.source_references_json if screening else [])[:8],
        "unresolved_eligibility_questions": unresolved,
    }
    brief = SupportApplicationBrief(
        profile_id=profile.id,
        user_id=profile.user_id,
        job_loss_profile_id=job.id if job else None,
        support_screening_id=screening.id if screening else None,
        supported_path_run_id=paths.id if paths else None,
        content_json=content,
        disclaimer=BRIEF_DISCLAIMER,
        official_source_references_json=content["official_source_references"],
        unresolved_questions_json=unresolved,
        demo_marker=_demo_marker(profile),
    )
    db.add(brief)
    db.commit()
    db.refresh(brief)
    return support_brief_public(brief)


def support_brief_public(row: SupportApplicationBrief) -> dict[str, Any]:
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "job_loss_profile_id": row.job_loss_profile_id,
        "support_screening_id": row.support_screening_id,
        "supported_path_run_id": row.supported_path_run_id,
        "content": row.content_json or {},
        "disclaimer": row.disclaimer,
        "status": row.status,
        "official_source_references": row.official_source_references_json or [],
        "unresolved_questions": row.unresolved_questions_json or [],
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def latest_support_brief(db: Session, profile_id: str) -> dict[str, Any] | None:
    row = db.scalar(select(SupportApplicationBrief).where(SupportApplicationBrief.profile_id == profile_id).order_by(SupportApplicationBrief.created_at.desc()))
    return support_brief_public(row) if row else None


def support_opportunity_graph(db: Session, profile_id: str) -> list[dict[str, Any]]:
    rows = db.scalars(select(SupportOpportunityLink).where(SupportOpportunityLink.profile_id == profile_id).order_by(SupportOpportunityLink.created_at.desc())).all()
    if rows:
        return [
            {
                "id": row.id,
                "source_type": row.source_type,
                "source_id": row.source_id,
                "target_type": row.target_type,
                "target_id": row.target_id,
                "relationship": row.relationship,
                "explanation": row.explanation,
                "metadata": row.metadata_json or {},
            }
            for row in rows
        ]
    paths = latest_supported_paths(db, profile_id)
    links = []
    for result in paths.get("results", []):
        for programme in result.get("possible_public_support", []):
            links.append(
                {
                    "source_type": "support_programme",
                    "source_id": programme.get("programme_id"),
                    "target_type": "career_direction",
                    "target_id": result.get("career_match_id"),
                    "relationship": "may support transition feasibility",
                    "explanation": "Programme may support training, placement, counselling, or transition planning. Official assessment required.",
                    "metadata": {"role_family": result.get("role_family")},
                }
            )
    return links


def career_resilience_dashboard(db: Session, profile: Profile) -> dict[str, Any]:
    sync_career_resilience_catalogue(db)
    hypotheses = ensure_hypotheses_from_matches(db, profile)
    active_sessions = db.scalars(
        select(CareerExperimentSession).where(CareerExperimentSession.profile_id == profile.id, CareerExperimentSession.status.in_(["planned", "in_progress", "submitted", "needs_review"])).order_by(CareerExperimentSession.updated_at.desc())
    ).all()
    latest_plan = latest_immediate_action_plan(db, profile.id)
    paths = latest_supported_paths(db, profile.id)
    passport = evidence_passport(db, profile.id)
    programmes = list_support_programmes(db)[:4]
    next_action = "Select a career hypothesis and confirm a role experiment."
    if latest_plan and latest_plan.get("items"):
        next_action = latest_plan["items"][0]["title"]
    elif active_sessions:
        next_action = f"Continue experiment: {session_public(db, active_sessions[0])['template']['title']}"
    return {
        "profile_id": profile.id,
        "workflow": [
            "Assessment",
            "Career hypothesis",
            "Career experiment",
            "Evidence collection",
            "Career recommendation recalibration",
            "Market and support feasibility",
            "Best supported career path",
            "User-confirmed roadmap",
        ],
        "life_event": latest_job_loss_profile(db, profile.id),
        "urgent_actions": latest_plan["items"][:3] if latest_plan else [],
        "career_hypotheses": [
            {
                "id": item.id,
                "career_match_id": item.career_match_id,
                "title": item.title,
                "role_family": item.role_family,
                "statement": item.statement,
                "uncertainty_label": item.uncertainty_label,
                "status": item.status,
            }
            for item in hypotheses[:4]
        ],
        "active_experiments": [session_public(db, item) for item in active_sessions],
        "evidence_updates": passport["skills"][:5],
        "best_supported_paths": paths.get("results", [])[:4],
        "market_snapshot": market_snapshot_catalogue(),
        "potential_programmes": programmes,
        "support_opportunity_graph": support_opportunity_graph(db, profile.id),
        "next_recommended_action": next_action,
        "required_language": {
            "hypothesis": "This career direction remains a hypothesis.",
            "support": "Final eligibility is determined by the responsible authority.",
        },
    }


def delete_career_resilience_for_profiles(db: Session, profile_ids: list[str]) -> None:
    ids = [profile_id for profile_id in profile_ids if profile_id]
    if not ids:
        return
    session_ids = db.scalars(select(CareerExperimentSession.id).where(CareerExperimentSession.profile_id.in_(ids))).all()
    submission_ids = db.scalars(select(CareerExperimentSubmission.id).where(CareerExperimentSubmission.profile_id.in_(ids))).all()
    result_ids = db.scalars(select(CareerExperimentResult.id).where(CareerExperimentResult.profile_id.in_(ids))).all()
    run_ids = db.scalars(select(CareerRecalibrationRun.id).where(CareerRecalibrationRun.profile_id.in_(ids))).all()
    support_screening_ids = db.scalars(select(SupportScreening.id).where(SupportScreening.profile_id.in_(ids))).all()
    supported_run_ids = db.scalars(select(SupportedPathRun.id).where(SupportedPathRun.profile_id.in_(ids))).all()
    plan_ids = db.scalars(select(ImmediateActionPlan.id).where(ImmediateActionPlan.profile_id.in_(ids))).all()
    hypothesis_ids = db.scalars(select(CareerHypothesis.id).where(CareerHypothesis.profile_id.in_(ids))).all()
    if run_ids:
        db.execute(delete(CareerRecalibrationFactor).where(CareerRecalibrationFactor.run_id.in_(run_ids)))
    if support_screening_ids:
        db.execute(delete(SupportScreeningFactor).where(SupportScreeningFactor.screening_id.in_(support_screening_ids)))
    if supported_run_ids:
        db.execute(delete(SupportedPathResult).where(SupportedPathResult.run_id.in_(supported_run_ids)))
    if plan_ids:
        db.execute(delete(ImmediateActionItem).where(ImmediateActionItem.plan_id.in_(plan_ids)))
    if hypothesis_ids:
        db.execute(delete(CareerHypothesisVersion).where(CareerHypothesisVersion.hypothesis_id.in_(hypothesis_ids)))
    if submission_ids:
        db.execute(delete(CareerExperimentReview).where(CareerExperimentReview.submission_id.in_(submission_ids)))
    if session_ids:
        db.execute(delete(CareerExperimentReview).where(CareerExperimentReview.session_id.in_(session_ids)))
    for model in [
        CareerRecalibrationRun,
        CareerExperimentResult,
        CareerExperimentSubmission,
        CareerExperimentSession,
        SkillEvidenceConfidence,
        SkillEvidenceSource,
        SkillRecency,
        SupportApplicationBrief,
        SupportOpportunityLink,
        SupportedPathRun,
        SupportScreening,
        ImmediateActionPlan,
        JobLossProfile,
        CareerHypothesis,
    ]:
        db.execute(delete(model).where(model.profile_id.in_(ids)))

