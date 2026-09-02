from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import re
from app.core.time import utc_now_naive
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.assessment import AssessmentSession, CareerMatch, CareerMatchFactor, SkillEvidence, SkillsInventory
from app.models.diagnostic import Diagnostic
from app.models.career_resilience import (
    CareerEvidenceGap,
    CareerEvidenceProposal,
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
from app.models.learning import SkillGapAnalysis
from app.models.roadmap import Roadmap
from app.models.roadmap_adaptation import RoadmapAction
from app.services.assessment_engine import (
    alignment_label,
    canonical_career_direction_id,
    current_career_matches_for_profile,
    fit_label,
    title_case_slug,
)
from app.services.profile_generation import generate_roadmap_fallback
from app.services.roadmap_adaptation import event as roadmap_event
from app.services.roadmap_adaptation import normalize_legacy, snapshot

CAREER_RESILIENCE_VERSION = "career-resilience-v1"
EXPERIMENT_CATALOGUE_VERSION = "career-experiment-catalogue-v2"
EXPERIMENT_RUBRIC_VERSION = "career-experiment-rubric-v2"
EXPERIMENT_EVAL_VERSION = "career-experiment-eval-v1"
DETERMINISTIC_EXPERIMENT_SOURCE = "DETERMINISTIC_CAREER_EXPERIMENT"
EXPERIMENT_RECOMMENDATION_VERSION = "adaptive-career-experiment-ranking-v1"
EVIDENCE_CONFIDENCE_VERSION = "evidence-confidence-v1"
EVIDENCE_GAP_VERSION = "career-evidence-gap-v1"
EVIDENCE_CALIBRATION_VERSION = "career-evidence-calibration-v1"
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
EVIDENCE_GAP_STATUSES = {"MISSING", "OUTDATED", "CONFLICTING", "INSUFFICIENT", "SELF_REPORT_ONLY", "PARTIAL"}
HYPOTHESIS_DECISION_STATES = {"UNREVIEWED", "EXPLORING", "ACCEPTED_FOR_TESTING", "PAUSED", "REJECTED", "ARCHIVED"}
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
    rubric_criteria: list[dict[str, Any]] | None = None,
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
        "rubric_criteria": rubric_criteria or _criteria(evaluated_skills),
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
            "ai-product-concept-generation-sprint",
            "Run an AI Feature Concept Generation Sprint",
            "AI Product Designer",
            "Test whether the user can generate, compare, and narrow several useful AI feature concepts before prototyping.",
            "A product team has a broad request to make an AI assistant more useful, but has not yet identified which user problem is worth solving first.",
            ["Problem framing", "At least three AI feature concepts", "Concept comparison matrix", "Chosen concept and trade-off rationale", "Reflection note"],
            ["ideation", "product_thinking", "communication", "human_centred_ai"],
            duration=120,
            required_skills=["ideation", "product_thinking", "communication"],
            rubric_criteria=[
                {
                    "criterion_id": "task_understanding",
                    "skill_id": "ideation",
                    "description": "Problem framing for ideation",
                    "weight": 0.20,
                    "evidence_requirement": "State a specific user problem, user need, and AI opportunity before proposing concepts.",
                    "interpretation": {"0": "No user problem framing was submitted.", "2": "A problem is named but the user need or AI opportunity is incomplete.", "4": "A specific user problem, user need, and bounded AI opportunity are all explicit."},
                },
                {
                    "criterion_id": "deliverable_quality",
                    "skill_id": "ideation",
                    "description": "Concept diversity",
                    "weight": 0.30,
                    "evidence_requirement": "Provide at least three distinct AI feature concepts, labelled so they can be independently compared.",
                    "interpretation": {"0": "No distinct concepts were submitted.", "2": "One or two concepts are visible, or the alternatives are not distinguishable.", "4": "At least three distinct, labelled concepts are submitted."},
                },
                {
                    "criterion_id": "reasoning_clarity",
                    "skill_id": "ideation",
                    "description": "Concept comparison and selection",
                    "weight": 0.25,
                    "evidence_requirement": "Compare the concepts using stated trade-offs and select one bounded concept with a reason.",
                    "interpretation": {"0": "No comparison or selection rationale was submitted.", "2": "A preference is stated without a clear comparison or trade-off.", "4": "The concepts are compared, trade-offs are explicit, and one bounded concept is selected with a reason."},
                },
                {
                    "criterion_id": "role_specific_technique",
                    "skill_id": "product_thinking",
                    "description": "Product concept scope",
                    "weight": 0.10,
                    "evidence_requirement": "Keep the selected concept bounded and identify a practical first release scope.",
                    "interpretation": {"0": "No bounded product scope was submitted.", "2": "The concept is present but the first release scope remains broad.", "4": "The selected concept has a clearly bounded first release scope."},
                },
                {
                    "criterion_id": "constraints",
                    "skill_id": "product_thinking",
                    "description": "Concept trade-offs and constraints",
                    "weight": 0.05,
                    "evidence_requirement": "Record at least one limitation, risk, or delivery constraint affecting the selected concept.",
                    "interpretation": {"0": "No relevant constraint was recorded.", "2": "A constraint is named without its implication.", "4": "A relevant constraint and its implication for the selected concept are explicit."},
                },
                {
                    "criterion_id": "human_centred",
                    "skill_id": "human_centred_ai",
                    "description": "Human-centred concept rationale",
                    "weight": 0.05,
                    "evidence_requirement": "Explain how the chosen concept supports a user while retaining meaningful human control.",
                    "interpretation": {"0": "No user or human-control rationale was submitted.", "2": "A user is mentioned but human control is unclear.", "4": "The user benefit and meaningful human control are both explicit."},
                },
                {
                    "criterion_id": "testing_validation",
                    "skill_id": "communication",
                    "description": "Concept validation plan",
                    "weight": 0.03,
                    "evidence_requirement": "Name one lightweight way to test the chosen concept with users or stakeholders.",
                    "interpretation": {"0": "No validation approach was submitted.", "2": "A validation activity is named without a question or audience.", "4": "A bounded validation activity, audience, and question are explicit."},
                },
                {
                    "criterion_id": "reflection_quality",
                    "skill_id": "communication",
                    "description": "Evidence reflection",
                    "weight": 0.02,
                    "evidence_requirement": "Reflect on what the concept sprint did and did not demonstrate.",
                    "interpretation": {"0": "No reflection was submitted.", "2": "The reflection is present but does not identify evidence limits.", "4": "The reflection names both evidence gained and an uncertainty that remains."},
                },
            ],
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
        for index, criterion in enumerate(item["rubric_criteria"]):
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


def _session_matches_direction(db: Session, session: CareerExperimentSession, direction_id: str) -> bool:
    if session.career_match_id:
        match = db.get(CareerMatch, session.career_match_id)
        if match and canonical_career_direction_id(match) == direction_id:
            return True
    if session.hypothesis_id:
        hypothesis = db.get(CareerHypothesis, session.hypothesis_id)
        if hypothesis and _hypothesis_direction_id(hypothesis) == direction_id:
            return True
    return False


def _adaptive_experiment_recommendation(
    db: Session,
    profile: Profile,
    match: CareerMatch,
    hypothesis: CareerHypothesis | None,
) -> dict[str, Any] | None:
    """Rank a role's catalogue deterministically from current, scoped evidence."""
    role = _related_role_family(match)
    templates = db.scalars(
        select(CareerExperimentTemplate)
        .where(
            CareerExperimentTemplate.target_role_family == role,
            CareerExperimentTemplate.active.is_(True),
        )
        .order_by(CareerExperimentTemplate.id)
    ).all()
    if not templates:
        return None

    gaps = []
    if hypothesis:
        gaps = db.scalars(
            select(CareerEvidenceGap)
            .where(
                CareerEvidenceGap.profile_id == profile.id,
                CareerEvidenceGap.hypothesis_id == hypothesis.id,
                CareerEvidenceGap.status.in_(list(EVIDENCE_GAP_STATUSES)),
            )
            .order_by(CareerEvidenceGap.skill_id)
        ).all()
    gaps_by_skill = {gap.skill_id: gap for gap in gaps}

    candidate_skill_ids = {
        skill_id
        for template in templates
        for skill_id in (template.evaluated_skills_json or [])
    }
    state_by_skill = {
        skill_id: _evidence_state_for_skill(db, profile.id, skill_id, hypothesis)
        for skill_id in sorted(candidate_skill_ids | set(gaps_by_skill))
    }
    practically_verified_skill_ids = sorted(
        skill_id
        for skill_id, state in state_by_skill.items()
        if state["status"] == "PRACTICALLY_VERIFIED"
    )
    direction_id = canonical_career_direction_id(match)
    history = [
        session
        for session in db.scalars(
            select(CareerExperimentSession).where(
                CareerExperimentSession.profile_id == profile.id,
                CareerExperimentSession.status.in_(["submitted", "needs_review", "evaluated"]),
            )
        ).all()
        if _session_matches_direction(db, session, direction_id)
    ]
    now = utc_now_naive()
    ranked: list[dict[str, Any]] = []
    for template in templates:
        skills = sorted(set(str(skill_id) for skill_id in (template.evaluated_skills_json or [])))
        covered_gaps = [gaps_by_skill[skill_id] for skill_id in skills if skill_id in gaps_by_skill]
        covered_skill_ids = [gap.skill_id for gap in covered_gaps]
        covered_importance = sum(float(gap.importance or 0) for gap in covered_gaps)
        verified_coverage = [skill_id for skill_id in skills if skill_id in practically_verified_skill_ids]
        matching_history = [session for session in history if session.experiment_template_id == template.id]
        duplicate_penalty = 0
        duplicate_reason = ""
        if matching_history:
            most_recent = max(
                (session.evaluated_at or session.submitted_at or session.updated_at or session.created_at)
                for session in matching_history
            )
            age_days = max(0, (now - most_recent).days)
            duplicate_penalty = 50 if age_days <= 365 else 20
            duplicate_reason = f"{len(matching_history)} completed or submitted session(s), most recently {age_days} day(s) ago"

        # All inputs and weights are fixed policy values.  No model output is
        # read or generated while ranking an experiment.
        new_evidence_gain = 35 if covered_gaps else 0
        career_relevance = 30
        unresolved_gap_coverage = min(25, round(25 * covered_importance))
        uncertainty_reduction = min(15, 15 * len(covered_gaps))
        feasibility = max(3, 15 - max(0, int(template.estimated_duration_minutes or 0) - 120) // 20)
        redundant_evidence_penalty = round(45 * len(verified_coverage) / max(1, len(skills)))
        score = (
            new_evidence_gain
            + career_relevance
            + unresolved_gap_coverage
            + uncertainty_reduction
            + feasibility
            - redundant_evidence_penalty
            - duplicate_penalty
        )
        ranked.append(
            {
                "template": template,
                "score": score,
                "score_breakdown": {
                    "new_evidence_gain": new_evidence_gain,
                    "career_relevance": career_relevance,
                    "unresolved_gap_coverage": unresolved_gap_coverage,
                    "uncertainty_reduction": uncertainty_reduction,
                    "feasibility": feasibility,
                    "redundant_evidence_penalty": redundant_evidence_penalty,
                    "duplicate_experiment_penalty": duplicate_penalty,
                },
                "targeted_gap_skill_ids": covered_skill_ids,
                "already_verified_skill_ids": verified_coverage,
                "duplicate_reason": duplicate_reason,
            }
        )
    ranked.sort(key=lambda item: (-item["score"], item["template"].estimated_duration_minutes, item["template"].id))
    unresolved_gap_skill_ids = sorted(gaps_by_skill)
    ranked_candidates = [
        {
            "template_id": item["template"].id,
            "score": item["score"],
            "score_breakdown": item["score_breakdown"],
            "targeted_gap_skill_ids": item["targeted_gap_skill_ids"],
            "already_verified_skill_ids": item["already_verified_skill_ids"],
            "duplicate_reason": item["duplicate_reason"],
        }
        for item in ranked
    ]
    if not unresolved_gap_skill_ids:
        return {
            "template": None,
            "recommendation": {
                "version": EXPERIMENT_RECOMMENDATION_VERSION,
                "state": "evidence_sufficient",
                "rank": None,
                "score": None,
                "score_breakdown": {},
                "targeted_gap_skill_ids": [],
                "unresolved_gap_skill_ids": [],
                "already_practically_verified_skill_ids": practically_verified_skill_ids,
                "rationale": [
                    "Current priority evidence gaps are sufficiently covered.",
                    f"Relevant to {match.title}.",
                    "No additional skill experiment is recommended solely to keep this loop running.",
                ],
                "next_options": [
                    "Collect external evidence or feedback for this direction.",
                    "Test market fit using the market and support evidence views.",
                    "Compare this direction with career alternatives.",
                    "Add a roadmap action only after explicit confirmation.",
                    "Complete a real-world project or revisit this direction later.",
                ],
                "ranked_template_ids": [item["template"].id for item in ranked],
                "ranked_candidates": ranked_candidates,
            },
        }
    selected = ranked[0]
    targeted_gap_labels = [_skill_label(skill_id) for skill_id in selected["targeted_gap_skill_ids"]]
    unserved_gap_labels = [_skill_label(skill_id) for skill_id in unresolved_gap_skill_ids if skill_id not in selected["targeted_gap_skill_ids"]]
    rationale = []
    if targeted_gap_labels:
        rationale.append(f"Tests unresolved gap: {', '.join(targeted_gap_labels)}.")
    elif unserved_gap_labels:
        rationale.append(f"No catalogue experiment directly tests unresolved gap: {', '.join(unserved_gap_labels)}. This is the closest bounded role experiment.")
    else:
        rationale.append("No unresolved relevant evidence gap is currently recorded; this is an exploratory bounded role experiment.")
    rationale.append(f"Relevant to {match.title}.")
    if practically_verified_skill_ids:
        rationale.append(f"Existing practical evidence already verifies: {', '.join(_skill_label(skill_id) for skill_id in practically_verified_skill_ids)}.")
    rationale.append(f"Expected evidence gain: {'High' if targeted_gap_labels else 'Low'}.")
    if selected["duplicate_reason"]:
        rationale.append(f"Duplicate penalty applied: {selected['duplicate_reason']}.")
    return {
        "template": selected["template"],
        "recommendation": {
            "version": EXPERIMENT_RECOMMENDATION_VERSION,
            "state": "experiment_recommended",
            "rank": 1,
            "score": selected["score"],
            "score_breakdown": selected["score_breakdown"],
            "targeted_gap_skill_ids": selected["targeted_gap_skill_ids"],
            "unresolved_gap_skill_ids": unresolved_gap_skill_ids,
            "already_practically_verified_skill_ids": practically_verified_skill_ids,
            "rationale": rationale,
            "ranked_template_ids": [item["template"].id for item in ranked],
            "ranked_candidates": ranked_candidates,
        },
    }


def _current_roadmap_for_experiment(db: Session, profile: Profile) -> tuple[Roadmap, bool]:
    roadmap = db.scalar(
        select(Roadmap)
        .where(Roadmap.profile_id == profile.id)
        .order_by(Roadmap.created_at.desc())
    )
    if roadmap:
        normalize_legacy(db, roadmap)
        return roadmap, False

    roadmap = Roadmap(
        user_id=profile.user_id,
        profile_id=profile.id,
        data={**generate_roadmap_fallback(), "version": 0, "status": "active"},
    )
    db.add(roadmap)
    db.flush()
    snapshot(db, roadmap, "Initial roadmap created for career experiment")
    return roadmap, True


def _is_owned_experiment_action(
    db: Session,
    action: RoadmapAction | None,
    profile: Profile,
    session: CareerExperimentSession,
) -> bool:
    if not (
        action
        and action.profile_id == profile.id
        and action.user_id == profile.user_id
        and action.source_type == "career_experiment"
        and (
            action.career_experiment_session_id == session.id
            or action.recommendation_id == session.id
        )
    ):
        return False
    roadmap = db.get(Roadmap, action.roadmap_id)
    return bool(roadmap and roadmap.profile_id == profile.id and roadmap.user_id == profile.user_id)


def _find_experiment_roadmap_action(
    db: Session,
    profile: Profile,
    session: CareerExperimentSession,
) -> RoadmapAction | None:
    """Find a valid persisted link, including actions created by the legacy field."""
    linked = db.get(RoadmapAction, session.roadmap_action_id) if session.roadmap_action_id else None
    if _is_owned_experiment_action(db, linked, profile, session):
        return linked

    if session.roadmap_action_id:
        # A dangling or cross-profile value must never confirm the experiment in the UI.
        session.roadmap_action_id = None

    linked = db.scalar(
        select(RoadmapAction)
        .where(
            RoadmapAction.career_experiment_session_id == session.id,
            RoadmapAction.profile_id == profile.id,
            RoadmapAction.user_id == profile.user_id,
            RoadmapAction.source_type == "career_experiment",
        )
        .order_by(RoadmapAction.created_at.desc())
    )
    if linked:
        return linked

    # Before the explicit source fields existed, recommendation_id stored the session id.
    return db.scalar(
        select(RoadmapAction)
        .where(
            RoadmapAction.recommendation_id == session.id,
            RoadmapAction.profile_id == profile.id,
            RoadmapAction.user_id == profile.user_id,
            RoadmapAction.source_type == "career_experiment",
        )
        .order_by(RoadmapAction.created_at.desc())
    )


def _sync_experiment_action(action: RoadmapAction, session: CareerExperimentSession, template: CareerExperimentTemplate) -> None:
    """Keep an already-persisted action aligned with the experiment lifecycle."""
    action.career_experiment_session_id = session.id
    action.career_hypothesis_id = session.hypothesis_id
    action.evidence_gap_id = session.evidence_gap_id
    action.recommendation_id = action.recommendation_id or session.id
    action.title = template.title
    action.description = template.purpose
    action.estimated_minutes = template.estimated_duration_minutes
    action.source_type = "career_experiment"
    if session.status == "in_progress":
        action.horizon = "seven_days"
        action.status = "in_progress"
        action.progress_percentage = max(action.progress_percentage or 0, 35)


def _create_roadmap_action_for_experiment(
    db: Session,
    profile: Profile,
    session: CareerExperimentSession,
    template: CareerExperimentTemplate,
) -> tuple[RoadmapAction, bool]:
    """Persist one user-confirmed roadmap action per experiment session.

    The caller deliberately receives whether a new action was created so that
    retries do not create duplicate history entries or mutate the roadmap twice.
    """
    existing = _find_experiment_roadmap_action(db, profile, session)
    if existing:
        _sync_experiment_action(existing, session, template)
        session.roadmap_action_id = existing.id
        return existing, False

    roadmap, _ = _current_roadmap_for_experiment(db, profile)
    in_progress = session.status == "in_progress"
    action = RoadmapAction(
        roadmap_id=roadmap.id,
        profile_id=profile.id,
        user_id=profile.user_id,
        # Retained for backward compatibility with legacy recommendation-derived actions.
        recommendation_id=session.id,
        career_experiment_session_id=session.id,
        career_hypothesis_id=session.hypothesis_id,
        evidence_gap_id=session.evidence_gap_id,
        horizon="seven_days",
        title=template.title,
        description=template.purpose,
        reason="User explicitly confirmed adding this career experiment to My Roadmap.",
        first_step="Review scope, choose experiment mode, and schedule the first work block.",
        success_criteria="Submit deliverables, complete self-review, and inspect the Evidence Passport update.",
        estimated_minutes=template.estimated_duration_minutes,
        effort="medium",
        impact="high",
        priority=1,
        status="in_progress" if in_progress else "not_started",
        progress_percentage=35 if in_progress else 0,
        source_type="career_experiment",
        profile_signals_json=[template.target_role_family],
        ethical_cautions_json=["This career direction remains a hypothesis until evidence is reviewed."],
    )
    db.add(action)
    db.flush()
    session.roadmap_action_id = action.id
    roadmap_event(
        db,
        roadmap.id,
        profile.user_id,
        "career_experiment_added_to_roadmap",
        action.id,
        {
            "source_type": "career_experiment",
            "experiment_session_id": session.id,
            "hypothesis_id": session.hypothesis_id,
            "evidence_gap_id": session.evidence_gap_id,
            "title": template.title,
        },
    )
    snapshot(
        db,
        roadmap,
        f"Career experiment added to roadmap: {template.title} ({session.id})",
    )
    return action, True


def _source_type(value: Any, default: str = "SYSTEM_DERIVED") -> str:
    normalized = str(value or "").strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "SELF_REPORTED": "SELF_REPORT",
        "SELF_REPORT_ONLY": "SELF_REPORT",
        "HUMAN_DIAGNOSTIC": "DIAGNOSTIC",
        "ASSESSMENT": "DEEP_DIVE",
        "CAREER_EXPERIMENT": "EXPERIMENT",
        "CAREER_EXPERIMENT_RESULT": "EXPERIMENT",
        "USER_CONFIRMED_EVIDENCE": "USER_CONFIRMED",
        "SYSTEM": "SYSTEM_DERIVED",
    }
    return aliases.get(normalized, normalized if normalized in {"SELF_REPORT", "DIAGNOSTIC", "DEEP_DIVE", "EVIDENCE", "EXPERIMENT", "MARKET", "SUPPORT", "USER_CONFIRMED", "SYSTEM_DERIVED"} else default)


def _profile_source_versions(db: Session, profile: Profile, match: CareerMatch | None = None) -> tuple[str, str]:
    diagnostic_version = ""
    if profile.diagnostic_id:
        diagnostic = db.get(Diagnostic, profile.diagnostic_id)
        diagnostic_version = diagnostic.diagnostic_version if diagnostic else ""
    data = profile.data or {}
    diagnostic_version = diagnostic_version or str(data.get("diagnostic_version") or "")
    if not diagnostic_version and match:
        diagnostic_version = str(match.source_metadata_json.get("diagnostic_version") or "")
    diagnostic_version = diagnostic_version or "human-diagnostic-v2"
    profile_version = str(data.get("profile_version") or data.get("interpretation_version") or "profile-snapshot-v1")
    return diagnostic_version, profile_version


def _qualitative_fit_band(score: float, source_metadata: dict[str, Any]) -> str:
    dimensions = source_metadata.get("hypothesis_dimensions") or {}
    labels = dimensions.get("labels") or {}
    evidence_label = str(labels.get("evidence_strength") or "").lower()
    if "insufficient" in evidence_label or "not assessed" in evidence_label:
        return "Insufficient evidence"
    if score >= 75:
        return "Currently plausible"
    if score >= 52:
        return "Worth exploring"
    if score >= 32:
        return "Mixed signal"
    return "Insufficient evidence"


def _hypothesis_explanation(match: CareerMatch, source_breakdown: dict[str, Any], missing: list[str], conflicting: list[str], fit_band: str) -> dict[str, Any]:
    source_metadata = match.source_metadata_json or {}
    source_kind = _source_type(source_metadata.get("source_type"), "DEEP_DIVE")
    supports = [str(item) for item in (match.supporting_factors_json or [])]
    cautions = [str(item) for item in (match.conflicting_factors_json or [])]
    return {
        "why_this_direction_appeared": match.explanation or f"This direction appeared from {source_kind} signals in the current profile.",
        "what_supports_it": supports,
        "what_is_uncertain": cautions or ["Direct evidence for the target role remains limited."],
        "what_evidence_is_missing": missing or ["No additional missing evidence was recorded; the direction remains exploratory."],
        "what_could_change_interpretation": [
            "More recent practical evidence",
            "Resolution of conflicting evidence",
            "A bounded role experiment with a reviewable artefact",
            "A material change in market or contextual constraints",
        ],
        "what_this_does_not_mean": "This is a testable career hypothesis, not a prediction of hiring success, readiness, or a required career choice.",
        "fit_band": fit_band,
        "source_breakdown": source_breakdown,
    }


def _evidence_is_relevant_to_hypothesis(
    db: Session,
    evidence: SkillEvidence,
    hypothesis: CareerHypothesis | None,
) -> bool:
    """Keep direction-specific experiment evidence from leaking into another direction.

    Evidence without a career-hypothesis provenance remains general evidence and
    can be used across directions.  A source explicitly linked to a different
    canonical direction is deliberately ignored for this gap calculation.
    """
    if not hypothesis:
        return True
    sources = db.scalars(
        select(SkillEvidenceSource).where(SkillEvidenceSource.skill_evidence_id == evidence.id)
    ).all()
    if not sources:
        return True
    target_direction_id = _hypothesis_direction_id(hypothesis)
    for source in sources:
        source_hypothesis_id = (source.source_metadata_json or {}).get("hypothesis_id")
        if not source_hypothesis_id:
            return True
        source_hypothesis = db.get(CareerHypothesis, source_hypothesis_id)
        if source_hypothesis and _hypothesis_direction_id(source_hypothesis) == target_direction_id:
            return True
    return False


def _evidence_state_for_skill(
    db: Session,
    profile_id: str,
    skill_id: str,
    hypothesis: CareerHypothesis | None = None,
) -> dict[str, Any]:
    inventory = db.scalar(select(SkillsInventory).where(SkillsInventory.profile_id == profile_id, SkillsInventory.skill_id == skill_id).order_by(SkillsInventory.updated_at.desc()))
    evidence_rows = []
    if inventory:
        evidence_rows = db.scalars(select(SkillEvidence).where(SkillEvidence.skill_inventory_id == inventory.id)).all()
    authoritative = [
        row
        for row in evidence_rows
        if row.verification_status != "provisional_pending_review"
        and _evidence_is_relevant_to_hypothesis(db, row, hypothesis)
    ]
    recency = db.scalar(select(SkillRecency).where(SkillRecency.profile_id == profile_id, SkillRecency.skill_id == skill_id))
    confidence_by_evidence = {
        row.skill_evidence_id: row
        for row in db.scalars(
            select(SkillEvidenceConfidence).where(
                SkillEvidenceConfidence.profile_id == profile_id,
                SkillEvidenceConfidence.skill_id == skill_id,
            )
        ).all()
    }
    practically_verified = [
        row
        for row in authoritative
        if (confidence_by_evidence.get(row.id) and confidence_by_evidence[row.id].strength_label == "Practically verified")
    ]
    # A stale record is a justified reason to request fresh evidence, even when
    # an older experiment was once practically verified.
    if practically_verified and recency and str(recency.status or "").lower().startswith("outdated"):
        return {"status": "OUTDATED", "gap_kind": "evidence_gap", "reason": "Evidence exists but its recency record indicates it should be refreshed.", "recency_issue": recency.refresh_recommendation or "Evidence is older than the current recency rule.", "has_authoritative": bool(authoritative)}
    if practically_verified:
        return {"status": "PRACTICALLY_VERIFIED", "gap_kind": "resolved", "reason": "Recent practical evidence already verifies this capability for the selected career direction.", "recency_issue": "", "has_authoritative": True}
    if inventory and int(inventory.level or 0) <= 1:
        return {"status": "INSUFFICIENT", "gap_kind": "skill_gap", "reason": "The current declared capability level is low for this requirement; a learning task may be needed before verification.", "recency_issue": "", "has_authoritative": bool(authoritative)}
    if not authoritative:
        return {"status": "SELF_REPORT_ONLY" if inventory else "MISSING", "gap_kind": "evidence_gap", "reason": "The person may have the capability, but no independently reviewable or practical evidence is stored.", "recency_issue": "", "has_authoritative": False}
    return {"status": "PARTIAL", "gap_kind": "evidence_gap", "reason": "Some evidence exists, but role-specific evidence remains partial.", "recency_issue": "", "has_authoritative": True}


def _gap_id(profile_id: str, hypothesis_id: str, skill_id: str) -> str:
    import hashlib
    return "gap-" + hashlib.sha256(f"{EVIDENCE_GAP_VERSION}:{profile_id}:{hypothesis_id}:{skill_id}".encode("utf-8")).hexdigest()[:16]


def _sync_hypothesis_evidence_gaps(db: Session, profile: Profile, hypothesis: CareerHypothesis, match: CareerMatch) -> list[CareerEvidenceGap]:
    missing_skills = [str(item) for item in (match.missing_skills_json or []) if str(item).strip()]
    source_metadata = match.source_metadata_json or {}
    # Diagnostic-created hypotheses intentionally use missing evidence as an
    # evidence gap. A low declared level is the only rule that creates a
    # distinct skill gap here.
    if not missing_skills:
        missing_skills = [str(item) for item in (source_metadata.get("evidence_requirements") or []) if str(item).strip()][:4]
    active_skill_ids = set(missing_skills)
    # Keep historical gap records, but resolve requirements removed from the
    # current canonical match so they cannot continue to drive recommendations.
    for stale in db.scalars(
        select(CareerEvidenceGap).where(
            CareerEvidenceGap.profile_id == profile.id,
            CareerEvidenceGap.hypothesis_id == hypothesis.id,
        )
    ).all():
        if stale.skill_id not in active_skill_ids and stale.status in EVIDENCE_GAP_STATUSES:
            state = _evidence_state_for_skill(db, profile.id, stale.skill_id, hypothesis)
            stale.status = "RESOLVED"
            stale.current_evidence_status = state["status"]
            stale.gap_kind = "resolved"
            stale.importance = 0.0
            stale.reason = "This evidence requirement is sufficiently covered for the current canonical career direction. Historical gap record retained."
            stale.recency_issue = state.get("recency_issue", "")
            stale.updated_at = utc_now_naive()
            db.add(stale)
    gaps: list[CareerEvidenceGap] = []
    for skill_id in sorted(set(missing_skills)):
        state = _evidence_state_for_skill(db, profile.id, skill_id, hypothesis)
        row = db.get(CareerEvidenceGap, _gap_id(profile.id, hypothesis.id, skill_id))
        if not row:
            row = CareerEvidenceGap(id=_gap_id(profile.id, hypothesis.id, skill_id), profile_id=profile.id, user_id=profile.user_id, hypothesis_id=hypothesis.id, career_match_id=match.id, skill_id=skill_id)
        row.profile_id = profile.id
        row.user_id = profile.user_id
        row.hypothesis_id = hypothesis.id
        row.career_match_id = match.id
        row.skill_id = skill_id
        row.capability_label = _skill_label(skill_id)
        row.gap_kind = state["gap_kind"]
        row.reason = state["reason"]
        row.current_evidence_status = state["status"]
        row.importance = round(0.8 if state["status"] in {"MISSING", "INSUFFICIENT"} else 0.65 if state["status"] in EVIDENCE_GAP_STATUSES else 0.0, 2)
        row.recency_issue = state["recency_issue"]
        row.suggested_action = (
            "Use a bounded learning task, then complete a verification exercise."
            if state["gap_kind"] == "skill_gap"
            else "Complete a bounded portfolio, project, or role experiment and review the resulting evidence."
        )
        row.status = state["status"] if state["status"] in EVIDENCE_GAP_STATUSES else "RESOLVED"
        row.source_metadata_json = {
            "source_types": [_source_type(source_metadata.get("source_type"), "DEEP_DIVE"), "SYSTEM_DERIVED"],
            "diagnostic_version": hypothesis.based_on_diagnostic_version,
            "profile_version": hypothesis.based_on_profile_version,
            "rule_version": EVIDENCE_GAP_VERSION,
            "missing_evidence_is_not_inability": True,
        }
        row.updated_at = utc_now_naive()
        db.add(row)
        gaps.append(row)
    hypothesis.missing_evidence_json = [
        {"gap_id": row.id, "capability": row.capability_label, "status": row.status, "gap_kind": row.gap_kind, "reason": row.reason}
        for row in gaps
        if row.status in EVIDENCE_GAP_STATUSES
    ]
    return gaps


def _gap_public(row: CareerEvidenceGap) -> dict[str, Any]:
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "hypothesis_id": row.hypothesis_id,
        "career_match_id": row.career_match_id,
        "skill_id": row.skill_id,
        "capability": row.capability_label,
        "gap_kind": row.gap_kind,
        "reason": row.reason,
        "current_evidence_status": row.current_evidence_status,
        "importance": row.importance,
        "recency_issue": row.recency_issue,
        "suggested_action": row.suggested_action,
        "status": row.status,
        "source_types": (row.source_metadata_json or {}).get("source_types", []),
        "version": row.version,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def _hypothesis_direction_id(hypothesis: CareerHypothesis) -> str:
    if hypothesis.canonical_direction_id:
        return hypothesis.canonical_direction_id
    if hypothesis.role_template_id:
        return f"role-template:{hypothesis.role_template_id}"
    return f"career-match:{hypothesis.career_match_id or hypothesis.id}"


def _sync_hypothesis_from_match(
    db: Session,
    profile: Profile,
    hypothesis: CareerHypothesis,
    match: CareerMatch,
    *,
    preserve_evidence_counts: bool,
) -> None:
    direction_id = canonical_career_direction_id(match)
    hypothesis.canonical_direction_id = direction_id
    hypothesis.career_match_id = match.id
    hypothesis.role_template_id = match.role_template_id
    hypothesis.title = match.title
    hypothesis.role_family = match.role_family
    hypothesis.current_alignment_score = match.alignment_score
    dimensions = (match.source_metadata_json or {}).get("hypothesis_dimensions") or {}
    labels = dimensions.get("labels") or {}
    diagnostic_version, profile_version = _profile_source_versions(db, profile, match)
    source_kind = _source_type((match.source_metadata_json or {}).get("source_type"), "DEEP_DIVE" if match.session_id else "DIAGNOSTIC")
    supports = [str(item) for item in (match.supporting_factors_json or [])]
    cautions = [str(item) for item in (match.conflicting_factors_json or [])]
    fit_band = _qualitative_fit_band(float(match.alignment_score or 0), match.source_metadata_json or {})
    source_breakdown = {
        "DIAGNOSTIC": len(supports) if source_kind == "DIAGNOSTIC" else 0,
        "SELF_REPORT": len(supports) if source_kind == "DIAGNOSTIC" else 0,
        "DEEP_DIVE": len(supports) if source_kind == "DEEP_DIVE" else 0,
        "EVIDENCE": 0,
        "EXPERIMENT": 0,
        "MARKET": 0,
        "SUPPORT": 0,
        "MISSING_EVIDENCE": len(match.missing_skills_json or []) or 1,
    }
    if preserve_evidence_counts:
        previous_breakdown = hypothesis.source_breakdown_json or {}
        for key in ("EVIDENCE", "EXPERIMENT", "USER_CONFIRMED"):
            source_breakdown[key] = max(int(source_breakdown.get(key, 0) or 0), int(previous_breakdown.get(key, 0) or 0))
    missing = [str(item) for item in (match.missing_skills_json or [])]
    explanation = _hypothesis_explanation(match, source_breakdown, missing, cautions, fit_band)
    resilience = (match.source_metadata_json or {}).get("career_resilience") or {}
    if resilience.get("latest_recalibration_reason"):
        hypothesis.uncertainty_label = "Reduced but still present" if resilience.get("latest_recalibration_reason") == "persisted_deterministic_career_experiment" else hypothesis.uncertainty_label
    else:
        hypothesis.uncertainty_label = "Lower uncertainty" if match.status == "evaluated" else "Additional evidence required"
    hypothesis.statement = (
        f"{match.title} is a provisional career hypothesis. "
        f"Natural Fit: {labels.get('natural_fit', 'Not assessed')}; "
        f"Capability Fit: {labels.get('capability_fit', 'Not assessed')}; "
        f"Evidence Strength: {labels.get('evidence_strength', 'Not assessed')}; "
        f"Transition Feasibility: {labels.get('transition_feasibility', 'Not assessed')}. "
        "Complete a role experiment before making a major career decision."
    )
    hypothesis.fit_band = fit_band
    hypothesis.based_on_diagnostic_version = diagnostic_version
    hypothesis.based_on_profile_version = profile_version
    hypothesis.supporting_signals_json = [{"label": item, "source_type": source_kind, "evidence_status": "SELF_REPORT" if source_kind == "DIAGNOSTIC" else "DIAGNOSTIC_SIGNAL"} for item in supports]
    hypothesis.caution_signals_json = [{"label": item, "source_type": source_kind} for item in cautions]
    hypothesis.conflicting_evidence_json = [{"label": item, "source_type": source_kind} for item in cautions]
    hypothesis.source_breakdown_json = source_breakdown
    hypothesis.market_limitations_json = ["Market evidence is not evaluated by the compatibility hypothesis engine."]
    hypothesis.support_limitations_json = ["Support eligibility is not inferred from this hypothesis."]
    hypothesis.explanation_json = explanation
    hypothesis.source_metadata_json = {
        "career_match_id": match.id,
        "canonical_direction_id": direction_id,
        "scoring_version": match.scoring_version,
        "hypothesis_dimensions": dimensions,
        "source_types": [source_kind, "SYSTEM_DERIVED"],
        "diagnostic_version": diagnostic_version,
        "profile_version": profile_version,
    }


def ensure_hypotheses_from_matches(db: Session, profile: Profile) -> list[CareerHypothesis]:
    current_matches = current_career_matches_for_profile(db, profile.id, include_rejected=True)
    existing = db.scalars(select(CareerHypothesis).where(CareerHypothesis.profile_id == profile.id)).all()
    existing_by_direction: dict[str, list[CareerHypothesis]] = defaultdict(list)
    for row in existing:
        existing_by_direction[_hypothesis_direction_id(row)].append(row)

    saved: list[CareerHypothesis] = []
    for match in current_matches:
        direction_id = canonical_career_direction_id(match)
        candidates = existing_by_direction.get(direction_id, [])
        hypothesis = next((row for row in candidates if row.career_match_id == match.id), None)
        if not hypothesis and candidates:
            hypothesis = sorted(candidates, key=lambda row: (row.status == "active", row.updated_at, row.id), reverse=True)[0]
        if not hypothesis:
            hypothesis = CareerHypothesis(
                profile_id=profile.id,
                user_id=profile.user_id,
                career_match_id=match.id,
                role_template_id=match.role_template_id,
                canonical_direction_id=direction_id,
                title=match.title,
                role_family=match.role_family,
                demo_marker=match.demo_marker or _demo_marker(profile),
            )
            db.add(hypothesis)
            db.flush()
            initial_version = 1
        else:
            initial_version = int(hypothesis.current_version_number or 1)

        for stale in candidates:
            if stale.id != hypothesis.id:
                stale.status = "superseded"
                stale_metadata = dict(stale.source_metadata_json or {})
                stale_metadata["superseded_by_hypothesis_id"] = hypothesis.id
                stale_metadata["canonical_direction_id"] = direction_id
                stale.source_metadata_json = stale_metadata
                flag_modified(stale, "source_metadata_json")

        if match.status == "rejected":
            hypothesis.status = "rejected"
            hypothesis.canonical_direction_id = direction_id
            continue

        hypothesis.status = "active"
        _sync_hypothesis_from_match(
            db,
            profile,
            hypothesis,
            match,
            preserve_evidence_counts=initial_version > 1 or bool(candidates),
        )
        hypothesis.current_version_number = initial_version
        _sync_hypothesis_evidence_gaps(db, profile, hypothesis, match)
        if not db.scalar(select(CareerHypothesisVersion).where(CareerHypothesisVersion.hypothesis_id == hypothesis.id)):
            db.add(
                CareerHypothesisVersion(
                    hypothesis_id=hypothesis.id,
                    profile_id=profile.id,
                    version_number=initial_version,
                    snapshot_json=hypothesis_snapshot(hypothesis),
                    change_reason="Initial hypothesis created from the current canonical career direction.",
                )
            )
        saved.append(hypothesis)
    db.commit()
    return saved


def hypothesis_snapshot(row: CareerHypothesis) -> dict[str, Any]:
    return {
        "hypothesis_id": row.id,
        "canonical_direction_id": _hypothesis_direction_id(row),
        "title": row.title,
        "role_family": row.role_family,
        "status": row.status,
        "version": row.current_version_number,
        "fit_band": row.fit_band,
        "uncertainty_label": row.uncertainty_label,
        "alignment_score_internal": row.current_alignment_score,
        "based_on_diagnostic_version": row.based_on_diagnostic_version,
        "based_on_profile_version": row.based_on_profile_version,
        "supporting_signals": row.supporting_signals_json or [],
        "caution_signals": row.caution_signals_json or [],
        "missing_evidence": row.missing_evidence_json or [],
        "conflicting_evidence": row.conflicting_evidence_json or [],
        "source_breakdown": row.source_breakdown_json or {},
        "explanation": row.explanation_json or {},
        "user_decision_state": row.user_decision_state,
        "rule_version": EVIDENCE_CALIBRATION_VERSION,
    }


def hypothesis_public(db: Session, row: CareerHypothesis, include_history: bool = True) -> dict[str, Any]:
    history = db.scalars(select(CareerHypothesisVersion).where(CareerHypothesisVersion.hypothesis_id == row.id).order_by(CareerHypothesisVersion.version_number)).all()
    recalibrations = db.scalars(select(CareerRecalibrationRun).where(CareerRecalibrationRun.hypothesis_id == row.id).order_by(CareerRecalibrationRun.created_at.desc())).all()
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "career_match_id": row.career_match_id,
        "role_template_id": row.role_template_id,
        "canonical_direction_id": _hypothesis_direction_id(row),
        "title": row.title,
        "role_family": row.role_family,
        "version": row.current_version_number,
        "version_label": row.version,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
        "based_on_diagnostic_version": row.based_on_diagnostic_version,
        "based_on_profile_version": row.based_on_profile_version,
        "fit_band": row.fit_band,
        "uncertainty_label": row.uncertainty_label,
        "supporting_signals": row.supporting_signals_json or [],
        "caution_signals": row.caution_signals_json or [],
        "missing_evidence": row.missing_evidence_json or [],
        "conflicting_evidence": row.conflicting_evidence_json or [],
        "market_limitations": row.market_limitations_json or [],
        "support_limitations": row.support_limitations_json or [],
        "source_breakdown": row.source_breakdown_json or {},
        "explanation": row.explanation_json or {},
        "user_decision_state": row.user_decision_state,
        "recalibration_history": [recalibration_public(db, item) for item in recalibrations] if include_history else [],
        "version_history": [
            {"version": item.version_number, "snapshot": item.snapshot_json or {}, "change_reason": item.change_reason, "created_at": item.created_at.isoformat()}
            for item in history
        ] if include_history else [],
    }


def list_profile_hypotheses(db: Session, profile: Profile) -> list[dict[str, Any]]:
    return [hypothesis_public(db, row) for row in ensure_hypotheses_from_matches(db, profile)]


def set_hypothesis_decision(db: Session, hypothesis: CareerHypothesis, state: str) -> dict[str, Any]:
    normalized = str(state or "").strip().upper()
    if normalized not in HYPOTHESIS_DECISION_STATES:
        raise ValueError("Unsupported career hypothesis decision state")
    hypothesis.user_decision_state = normalized
    hypothesis.updated_at = utc_now_naive()
    db.commit()
    db.refresh(hypothesis)
    return hypothesis_public(db, hypothesis)


def list_profile_evidence_gaps(db: Session, profile: Profile, hypothesis_id: str | None = None) -> dict[str, Any]:
    hypotheses = ensure_hypotheses_from_matches(db, profile)
    if hypothesis_id:
        hypotheses = [item for item in hypotheses if item.id == hypothesis_id]
        if not hypotheses:
            raise LookupError("Career hypothesis not found")
    active_hypothesis_ids = [item.id for item in hypotheses]
    rows = db.scalars(
        select(CareerEvidenceGap)
        .where(
            CareerEvidenceGap.profile_id == profile.id,
            CareerEvidenceGap.hypothesis_id.in_(active_hypothesis_ids) if active_hypothesis_ids else CareerEvidenceGap.hypothesis_id.is_(None),
        )
        .order_by(CareerEvidenceGap.importance.desc(), CareerEvidenceGap.capability_label)
    ).all()
    return {
        "profile_id": profile.id,
        "status": "completed",
        "version": EVIDENCE_GAP_VERSION,
        "gaps": [_gap_public(row) for row in rows if row.status in EVIDENCE_GAP_STATUSES],
        "summary": {
            "gap_count": len([row for row in rows if row.status in EVIDENCE_GAP_STATUSES]),
            "skill_gap_count": len([row for row in rows if row.status in EVIDENCE_GAP_STATUSES and row.gap_kind == "skill_gap"]),
            "evidence_gap_count": len([row for row in rows if row.status in EVIDENCE_GAP_STATUSES and row.gap_kind == "evidence_gap"]),
            "missing_evidence_note": "Missing evidence is uncertainty, not proof of inability.",
        },
    }


def create_experiment_session(db: Session, profile: Profile, payload: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
    sync_career_resilience_catalogue(db)
    template_id = payload.get("experiment_template_id") or payload.get("template_id")
    career_match_id = payload.get("career_match_id")
    hypothesis_id = payload.get("hypothesis_id")
    evidence_gap_id = payload.get("evidence_gap_id")
    recommendation: dict[str, Any] | None = None
    if evidence_gap_id:
        gap = db.get(CareerEvidenceGap, evidence_gap_id)
        if not gap or gap.profile_id != profile.id:
            raise LookupError("Evidence gap not found for this profile")
        hypothesis_id = hypothesis_id or gap.hypothesis_id
        career_match_id = career_match_id or gap.career_match_id
    if hypothesis_id:
        hypothesis = db.get(CareerHypothesis, hypothesis_id)
        if not hypothesis or hypothesis.profile_id != profile.id:
            raise LookupError("Career hypothesis not found for this profile")
        if hypothesis.status != "active":
            current = db.scalar(
                select(CareerHypothesis)
                .where(
                    CareerHypothesis.profile_id == profile.id,
                    CareerHypothesis.canonical_direction_id == _hypothesis_direction_id(hypothesis),
                    CareerHypothesis.status == "active",
                )
                .order_by(CareerHypothesis.updated_at.desc())
            )
            if not current:
                raise LookupError("Career hypothesis is no longer current for this career direction")
            hypothesis = current
            hypothesis_id = current.id
        career_match_id = career_match_id or hypothesis.career_match_id
    if career_match_id:
        supplied_match = db.get(CareerMatch, career_match_id)
        if not supplied_match or supplied_match.profile_id != profile.id:
            raise LookupError("Career match not found for this profile")
        direction_id = canonical_career_direction_id(supplied_match)
        current_match = next(
            (row for row in current_career_matches_for_profile(db, profile.id, include_rejected=True) if canonical_career_direction_id(row) == direction_id),
            supplied_match,
        )
        if current_match.status == "rejected":
            raise LookupError("Career direction has been rejected")
        career_match_id = current_match.id
        # Refresh gaps from the latest persisted evidence before selecting an
        # automatic recommendation. Explicit catalogue choices are not ranked.
        ensure_hypotheses_from_matches(db, profile)
    if not template_id and career_match_id:
        match = db.get(CareerMatch, career_match_id)
        linked_hypothesis = db.scalar(
            select(CareerHypothesis)
            .where(
                CareerHypothesis.profile_id == profile.id,
                CareerHypothesis.career_match_id == career_match_id,
                CareerHypothesis.status == "active",
            )
            .order_by(CareerHypothesis.updated_at.desc())
        )
        if linked_hypothesis and not hypothesis_id:
            hypothesis_id = linked_hypothesis.id
        selected = _adaptive_experiment_recommendation(db, profile, match, linked_hypothesis)
        template = selected["template"] if selected else _template_for_match(db, match)
        recommendation = selected["recommendation"] if selected else None
        if selected and template is None:
            # A recommendation request may deliberately return no experiment
            # after the current canonical direction's priority gaps have been
            # practically verified.  Do not manufacture a session, roadmap
            # action, or secondary recommendation just to keep the loop alive.
            return {
                "status": "evidence_sufficient",
                "profile_id": profile.id,
                "career_match_id": career_match_id,
                "hypothesis_id": hypothesis_id or (linked_hypothesis.id if linked_hypothesis else None),
                "user_confirmed": bool(payload.get("user_confirmed", True)),
                "expected_evidence_gain": "None",
                "recommendation": recommendation,
            }
        template_id = template.id if template else None
    template = db.get(CareerExperimentTemplate, template_id) if template_id else None
    if not template or not template.active:
        raise LookupError("Career experiment template not found")
    if career_match_id:
        match = db.get(CareerMatch, career_match_id)
        if not match or match.profile_id != profile.id:
            raise LookupError("Career match not found for this profile")
        if not hypothesis_id:
            linked_hypothesis = db.scalar(
                select(CareerHypothesis)
                .where(
                    CareerHypothesis.profile_id == profile.id,
                    CareerHypothesis.career_match_id == career_match_id,
                    CareerHypothesis.status == "active",
                )
                .order_by(CareerHypothesis.updated_at.desc())
            )
            hypothesis_id = linked_hypothesis.id if linked_hypothesis else None
        if not evidence_gap_id and hypothesis_id:
            linked_gap = db.scalar(select(CareerEvidenceGap).where(CareerEvidenceGap.profile_id == profile.id, CareerEvidenceGap.hypothesis_id == hypothesis_id, CareerEvidenceGap.status.in_(list(EVIDENCE_GAP_STATUSES))).order_by(CareerEvidenceGap.importance.desc()))
            evidence_gap_id = linked_gap.id if linked_gap else None
    mode = payload.get("mode") or "guided"
    if mode not in EXPERIMENT_MODES:
        raise ValueError("Unsupported experiment mode")
    session = CareerExperimentSession(
        profile_id=profile.id,
        user_id=user_id or profile.user_id,
        career_match_id=career_match_id,
        experiment_template_id=template.id,
        hypothesis_id=hypothesis_id,
        evidence_gap_id=evidence_gap_id,
        mode=mode,
        status="suggested" if payload.get("suggested") else "planned",
        user_confirmed=bool(payload.get("user_confirmed", True)),
        demo_marker=bool(payload.get("demo_marker", _demo_marker(profile))),
        source_metadata_json={
            "created_from": "career_match" if career_match_id else "catalogue",
            "roadmap_confirmation_required": True,
            "source_types": ["CAREER_HYPOTHESIS", "EVIDENCE_GAP", "SYSTEM_DERIVED"],
            "expected_evidence_gain": payload.get("expected_evidence_gain") or ("High" if recommendation and recommendation.get("targeted_gap_skill_ids") else "Moderate"),
            "recommendation": recommendation,
            "limitations": ["A bounded experiment cannot establish professional readiness or hiring success."],
            "rubric_version": EXPERIMENT_EVAL_VERSION,
        },
    )
    db.add(session)
    db.flush()
    if payload.get("add_to_roadmap"):
        action, _ = _create_roadmap_action_for_experiment(db, profile, session, template)
        session.roadmap_action_id = action.id
    db.commit()
    db.refresh(session)
    return session_public(db, session)


def confirm_experiment_roadmap(db: Session, profile: Profile, session: CareerExperimentSession, confirmed: bool = True) -> dict[str, Any]:
    if session.profile_id != profile.id:
        raise LookupError("Career experiment does not belong to this profile")
    if not confirmed:
        return session_public(db, session)
    template = db.get(CareerExperimentTemplate, session.experiment_template_id)
    if not template:
        raise LookupError("Career experiment template not found")
    action, _ = _create_roadmap_action_for_experiment(db, profile, session, template)
    session.roadmap_action_id = action.id
    metadata = dict(session.source_metadata_json or {})
    metadata["roadmap_confirmation"] = {
        "confirmed": True,
        "confirmed_at": utc_now_naive().isoformat(),
        "source": "CAREER_HYPOTHESIS",
        "source_gap": session.evidence_gap_id,
        "source_experiment": session.id,
    }
    session.source_metadata_json = metadata
    flag_modified(session, "source_metadata_json")
    session.updated_at = utc_now_naive()
    db.commit()
    db.refresh(session)
    return session_public(db, session)


def session_public(db: Session, row: CareerExperimentSession, include_details: bool = True) -> dict[str, Any]:
    template = db.get(CareerExperimentTemplate, row.experiment_template_id)
    submission = db.scalar(select(CareerExperimentSubmission).where(CareerExperimentSubmission.session_id == row.id).order_by(CareerExperimentSubmission.created_at.desc()))
    result = db.scalar(select(CareerExperimentResult).where(CareerExperimentResult.session_id == row.id).order_by(CareerExperimentResult.created_at.desc()))
    reviews = db.scalars(select(CareerExperimentReview).where(CareerExperimentReview.session_id == row.id).order_by(CareerExperimentReview.created_at)).all()
    proposals = db.scalars(select(CareerEvidenceProposal).where(CareerEvidenceProposal.experiment_session_id == row.id).order_by(CareerEvidenceProposal.created_at)).all()
    payload = {
        "id": row.id,
        "profile_id": row.profile_id,
        "career_match_id": row.career_match_id,
        "experiment_template_id": row.experiment_template_id,
        "hypothesis_id": row.hypothesis_id,
        "evidence_gap_id": row.evidence_gap_id,
        "roadmap_action_id": row.roadmap_action_id,
        "mode": row.mode,
        "status": row.status,
        "user_confirmed": row.user_confirmed,
        "demo_marker": row.demo_marker,
        "version": row.version,
        "source_metadata": row.source_metadata_json or {},
        "expected_evidence_gain": (row.source_metadata_json or {}).get("expected_evidence_gain", "Moderate"),
        "recommendation": (row.source_metadata_json or {}).get("recommendation"),
        "confidence_label": row.confidence_label,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "submitted_at": row.submitted_at.isoformat() if row.submitted_at else None,
        "evaluated_at": row.evaluated_at.isoformat() if row.evaluated_at else None,
        "template": template_public(db, template, include_rubric=include_details) if template and include_details else None,
        "submission": submission_public(submission) if submission else None,
        "result": result_public(result) if result else None,
        "reviews": [review_public(item) for item in reviews],
        "evidence_proposals": [evidence_proposal_public(item) for item in proposals],
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
    evidence_gain = row.actual_evidence_gain_json or {}
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
        "actual_evidence_gain": evidence_gain,
        "persistence": evidence_gain.get("persistence", {}),
        "linked_gap": evidence_gain.get("linked_gap", {}),
        "evidence_not_created": evidence_gain.get("evidence_not_created", []),
        "provenance": evidence_gain.get("provenance", {}),
        "created_at": row.created_at.isoformat(),
    }


def evidence_proposal_public(row: CareerEvidenceProposal) -> dict[str, Any]:
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "hypothesis_id": row.hypothesis_id,
        "evidence_gap_id": row.evidence_gap_id,
        "experiment_session_id": row.experiment_session_id,
        "experiment_result_id": row.experiment_result_id,
        "source_type": row.source_type,
        "category": row.category,
        "capability_id": row.capability_id,
        "capability": row.capability_label,
        "title": row.title,
        "description": row.description,
        "artifact_reference": row.artifact_reference,
        "expected_evidence_gain": row.expected_evidence_gain,
        "actual_evidence_gain": row.actual_evidence_gain,
        "verification_state": row.verification_state,
        "relevance": row.relevance,
        "recency": row.recency,
        "provenance": row.provenance_json or {},
        "status": row.status,
        "user_confirmed": row.user_confirmed,
        "user_edit": row.user_edit_json or {},
        "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
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
    profile = db.get(Profile, session.profile_id)
    template = db.get(CareerExperimentTemplate, session.experiment_template_id)
    if profile and template:
        action = _find_experiment_roadmap_action(db, profile, session)
        if action:
            _sync_experiment_action(action, session, template)
            session.roadmap_action_id = action.id
            roadmap_event(
                db,
                action.roadmap_id,
                profile.user_id,
                "career_experiment_started",
                action.id,
                {"experiment_session_id": session.id, "title": template.title},
            )
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
    # The concept-generation sprint has three dedicated Ideation criteria.
    # These checks deliberately inspect only submitted artefact content; they
    # do not infer ideation from a polished prototype or unrelated output.
    if criterion.skill_id == "ideation" and criterion.criterion_id == "task_understanding":
        if not all(word in text for word in ["problem", "user"]) or not any(word in text for word in ["need", "opportunity"]):
            rating = min(rating, 2)
    if criterion.skill_id == "ideation" and criterion.criterion_id == "deliverable_quality":
        numbered_concepts = {
            int(number)
            for number in re.findall(r"\b(?:concept|idea)\s*(?:number\s*)?#?([1-9])\b", text)
        }
        word_numbered = all(f"concept {word}" in text or f"idea {word}" in text for word in ["one", "two", "three"])
        if len(numbered_concepts) < 3 and not word_numbered:
            rating = min(rating, 2 if any(word in text for word in ["concept", "idea"]) else 1)
    if criterion.skill_id == "ideation" and criterion.criterion_id == "reasoning_clarity":
        has_comparison = any(word in text for word in ["compare", "comparison", "matrix"])
        has_trade_off = any(word in text for word in ["trade-off", "tradeoff", "trade off", "constraint"])
        has_selection = any(word in text for word in ["select", "selected", "choose", "chosen"])
        if not (has_comparison and has_trade_off and has_selection):
            rating = min(rating, 2)
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


def _invalidate_learning_analysis_for_practical_evidence(db: Session, profile_id: str) -> None:
    """Keep derived Learning Path snapshots from outranking newly verified evidence."""
    for analysis in db.scalars(
        select(SkillGapAnalysis).where(
            SkillGapAnalysis.profile_id == profile_id,
            SkillGapAnalysis.status == "ready",
        )
    ).all():
        analysis.status = "evidence_updated"


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
    authoritative: bool = True,
    confirmation_source: str = "SYSTEM_DERIVED",
    source_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inventory = _ensure_inventory(db, profile_id, skill_id, level=3 if score_hint >= 65 else 2)
    if not authoritative:
        inventory.evidence_status = "self_reported"
        inventory.confirmation_status = "needs_review"
        inventory.evidence_note = "Provisional experiment output pending explicit user confirmation."
    strength = evidence_strength_label(score_hint, evidence_type)
    evidence = SkillEvidence(
        skill_inventory_id=inventory.id,
        evidence_type=evidence_type,
        title=title,
        description=description,
        url=url,
        verification_status=strength.lower().replace(" ", "_") if authoritative else "provisional_pending_review",
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
    metadata = {
        "evidence_type": evidence_type,
        "automatic_file_analysis": False,
        "authoritative": authoritative,
        "confirmation_source": confirmation_source,
    }
    if source_metadata:
        metadata.update(source_metadata)
    source = SkillEvidenceSource(
        skill_evidence_id=evidence.id,
        profile_id=profile_id,
        source_type=source_type or evidence_type,
        source_id=source_id,
        title=title,
        url=url,
        source_metadata_json=metadata,
        independent_confirmation=independent,
    )
    db.add(confidence)
    db.add(source)
    if strength == "Practically verified":
        _invalidate_learning_analysis_for_practical_evidence(db, profile_id)
    _upsert_recency(db, profile_id, skill_id, evidence.created_at)
    return {
        "skill_id": skill_id,
        "skill_label": inventory.skill_label,
        "evidence_id": evidence.id,
        "confidence_label": confidence.confidence_label,
        "strength_label": confidence.strength_label,
    }


def _evidence_gain_label(score: float) -> str:
    if score >= 80:
        return "High"
    if score >= 65:
        return "Moderate"
    if score >= 40:
        return "Low"
    return "None observed"


def _create_evidence_proposals(
    db: Session,
    session: CareerExperimentSession,
    result: CareerExperimentResult,
    template: CareerExperimentTemplate,
    submission: CareerExperimentSubmission,
    criteria_scores: list[dict[str, Any]],
    actual_gain: str,
) -> list[CareerEvidenceProposal]:
    by_skill: dict[str, list[int]] = defaultdict(list)
    for item in criteria_scores:
        by_skill[str(item["skill_id"])].append(int(item["rating"]))
    intended_gap = db.get(CareerEvidenceGap, session.evidence_gap_id) if session.evidence_gap_id else None
    assessed_skill_ids = sorted(by_skill)
    proposals: list[CareerEvidenceProposal] = []
    for skill_id, ratings in sorted(by_skill.items()):
        # A session can be motivated by a gap without actually assessing it.
        # Never attach that intended gap to an unrelated assessed dimension.
        gap = intended_gap if intended_gap and intended_gap.skill_id == skill_id else None
        if not gap and session.hypothesis_id:
            gap = db.scalar(select(CareerEvidenceGap).where(CareerEvidenceGap.profile_id == session.profile_id, CareerEvidenceGap.hypothesis_id == session.hypothesis_id, CareerEvidenceGap.skill_id == skill_id))
        average = round(sum(ratings) / max(1, len(ratings)) / 4 * 100, 2)
        provenance = {
            "source_type": "EXPERIMENT",
            "experiment_session_id": session.id,
            "experiment_result_id": result.id,
            "hypothesis_id": session.hypothesis_id,
            "evidence_gap_id": gap.id if gap else None,
            "intended_evidence_gap_id": intended_gap.id if intended_gap else None,
            "intended_gap_skill_id": intended_gap.skill_id if intended_gap else None,
            "intended_gap_assessed": bool(intended_gap and intended_gap.skill_id in assessed_skill_ids),
            "remaining_unresolved_gap": bool(intended_gap and intended_gap.skill_id not in assessed_skill_ids),
            "rubric_version": result.deterministic_version,
            "criterion_average": average,
            "authoritative_before_review": False,
        }
        proposal = db.scalar(select(CareerEvidenceProposal).where(CareerEvidenceProposal.experiment_result_id == result.id, CareerEvidenceProposal.capability_id == skill_id).order_by(CareerEvidenceProposal.created_at.desc()))
        if proposal:
            # Repair proposal links produced by the former fallback behavior
            # without altering any user decision or removing historical data.
            proposal.evidence_gap_id = gap.id if gap else None
            proposal.provenance_json = provenance
            flag_modified(proposal, "provenance_json")
        else:
            proposal = CareerEvidenceProposal(
                profile_id=session.profile_id,
                user_id=session.user_id,
                hypothesis_id=session.hypothesis_id,
                evidence_gap_id=gap.id if gap else None,
                experiment_session_id=session.id,
                experiment_result_id=result.id,
                source_type="EXPERIMENT",
                category="project_evidence",
                capability_id=skill_id,
                capability_label=_skill_label(skill_id),
                title=f"Project evidence: {template.title}",
                description=f"Deterministic rubric result for {template.target_role_family}; observed criterion average {average}%. A user may still review how this bounded evidence is used for a career hypothesis.",
                artifact_reference=submission.project_url or submission.repository_url or submission.portfolio_url or "Submitted experiment artefact",
                expected_evidence_gain=str((session.source_metadata_json or {}).get("expected_evidence_gain") or "Moderate"),
                actual_evidence_gain=actual_gain,
                verification_state="PROVISIONAL",
                relevance="Role-specific experiment evidence; bounded and not certification.",
                recency="Dated at user confirmation",
                provenance_json=provenance,
                status="PENDING_REVIEW",
            )
            db.add(proposal)
            db.flush()
        proposals.append(proposal)
    return proposals


def _criteria_by_skill(criteria_scores: list[dict[str, Any]]) -> dict[str, list[int]]:
    by_skill: dict[str, list[int]] = defaultdict(list)
    for item in criteria_scores:
        by_skill[str(item["skill_id"])].append(int(item["rating"]))
    return by_skill


def _linked_gap_context(db: Session, session: CareerExperimentSession, criteria_scores: list[dict[str, Any]]) -> dict[str, Any]:
    assessed_skill_ids = sorted(_criteria_by_skill(criteria_scores))
    intended_gap = db.get(CareerEvidenceGap, session.evidence_gap_id) if session.evidence_gap_id else None
    if not intended_gap:
        return {
            "intended_gap": None,
            "assessed_skill_ids": assessed_skill_ids,
            "generated_skill_ids": [],
            "remaining_unresolved": False,
        }
    directly_assessed = intended_gap.skill_id in assessed_skill_ids
    return {
        "intended_gap": {
            "id": intended_gap.id,
            "skill_id": intended_gap.skill_id,
            "skill_label": intended_gap.capability_label or _skill_label(intended_gap.skill_id),
            "status": intended_gap.status,
        },
        "assessed_skill_ids": assessed_skill_ids,
        "generated_skill_ids": [],
        "directly_assessed": directly_assessed,
        "remaining_unresolved": not directly_assessed,
        "message": (
            "The linked gap was directly assessed by this deterministic rubric."
            if directly_assessed
            else f"This experiment generated evidence for {', '.join(_skill_label(skill_id) for skill_id in assessed_skill_ids)}, but did not directly verify the linked {intended_gap.capability_label or _skill_label(intended_gap.skill_id)} gap."
        ),
    }


def _deterministic_review_for_result(
    db: Session,
    session: CareerExperimentSession,
    submission: CareerExperimentSubmission,
    result: CareerExperimentResult,
) -> CareerExperimentReview:
    review = db.scalar(
        select(CareerExperimentReview)
        .where(
            CareerExperimentReview.session_id == session.id,
            CareerExperimentReview.submission_id == submission.id,
            CareerExperimentReview.source_type == "deterministic_rubric",
        )
        .order_by(CareerExperimentReview.created_at.desc())
    )
    if review:
        return review
    review = CareerExperimentReview(
        session_id=session.id,
        submission_id=submission.id,
        profile_id=session.profile_id,
        source_type="deterministic_rubric",
        scores_json={"overall_score": result.overall_score, "criteria": result.criteria_scores_json or []},
        narrative="Deterministic rubric applied. No LLM changed the score.",
        limitations_json=[
            "This is role-experiment evidence, not certification.",
            "The result does not declare employment suitability.",
        ],
    )
    db.add(review)
    db.flush()
    return review


def _persisted_deterministic_evidence(db: Session, profile_id: str, result_id: str) -> list[dict[str, Any]]:
    sources = db.scalars(
        select(SkillEvidenceSource).where(
            SkillEvidenceSource.profile_id == profile_id,
            SkillEvidenceSource.source_type == DETERMINISTIC_EXPERIMENT_SOURCE,
            SkillEvidenceSource.source_id == result_id,
        )
    ).all()
    records: list[dict[str, Any]] = []
    for source in sources:
        evidence = db.get(SkillEvidence, source.skill_evidence_id)
        metadata = source.source_metadata_json or {}
        skill_id = str(metadata.get("skill_id") or "")
        if not evidence or not skill_id or evidence.verification_status == "provisional_pending_review":
            continue
        confidence = db.scalar(select(SkillEvidenceConfidence).where(SkillEvidenceConfidence.skill_evidence_id == evidence.id))
        records.append(
            {
                "skill_id": skill_id,
                "skill_label": str(metadata.get("skill_label") or _skill_label(skill_id)),
                "evidence_id": evidence.id,
                "review_id": metadata.get("deterministic_review_id"),
                "deterministic_score": float(metadata.get("deterministic_score") or 0),
                "classification": str(metadata.get("evidence_classification") or (confidence.strength_label if confidence else "Supported")),
                "confidence_label": confidence.confidence_label if confidence else "Limited evidence",
                "strength_label": confidence.strength_label if confidence else "Supported",
                "source_type": source.source_type,
            }
        )
    return sorted(records, key=lambda item: item["skill_id"])


def _persist_deterministic_result(
    db: Session,
    session: CareerExperimentSession,
    submission: CareerExperimentSubmission,
    template: CareerExperimentTemplate,
    result: CareerExperimentResult,
) -> dict[str, Any]:
    criteria_scores = result.criteria_scores_json or []
    review = _deterministic_review_for_result(db, session, submission, result)
    linked_gap = _linked_gap_context(db, session, criteria_scores)
    existing = {item["skill_id"]: item for item in _persisted_deterministic_evidence(db, session.profile_id, result.id)}
    evidence_created = list(existing.values())
    evidence_not_created: list[dict[str, Any]] = []
    intended_gap_skill_id = (linked_gap.get("intended_gap") or {}).get("skill_id")
    source_hypothesis = db.get(CareerHypothesis, session.hypothesis_id) if session.hypothesis_id else None
    source_match = db.get(CareerMatch, session.career_match_id) if session.career_match_id else None
    canonical_direction_id = _hypothesis_direction_id(source_hypothesis) if source_hypothesis else canonical_career_direction_id(source_match) if source_match else None
    by_skill = _criteria_by_skill(criteria_scores)
    for skill_id, ratings in sorted(by_skill.items()):
        score_hint = round(sum(ratings) / max(1, len(ratings)) / 4 * 100, 2)
        # Low rubric ratings are recorded in the review but do not become an
        # evidence record. This avoids re-labelling a weak observation as proof.
        if skill_id in existing:
            continue
        if score_hint < 45:
            evidence_not_created.append({"skill_id": skill_id, "skill_label": _skill_label(skill_id), "deterministic_score": score_hint, "reason": "The deterministic criterion average was below the minimum evidence threshold."})
            continue
        # A linked priority gap is only resolved when its own rubric criteria
        # reach the practical-verification threshold. This prevents partial or
        # unrelated output from being treated as proof of the selected gap.
        if skill_id == intended_gap_skill_id and (not linked_gap.get("directly_assessed") or score_hint < 85):
            evidence_not_created.append(
                {
                    "skill_id": skill_id,
                    "skill_label": _skill_label(skill_id),
                    "deterministic_score": score_hint,
                    "reason": "The linked priority gap requires direct rubric assessment at 85% or higher before practical verification is created.",
                }
            )
            continue
        strength = evidence_strength_label(score_hint, "career_experiment")
        item = _create_skill_evidence(
            db,
            session.profile_id,
            skill_id,
            "career_experiment",
            f"Verified through career experiment: {template.title} — {_skill_label(skill_id)}",
            f"Deterministic rubric result for {template.target_role_family}; {_skill_label(skill_id)} scored {score_hint}% (overall score {result.overall_score}%).",
            url=submission.project_url or submission.repository_url or submission.portfolio_url,
            source_id=result.id,
            source_type=DETERMINISTIC_EXPERIMENT_SOURCE,
            practical=score_hint >= 65,
            independent=False,
            score_hint=score_hint,
            authoritative=True,
            confirmation_source="DETERMINISTIC_RUBRIC",
            source_metadata={
                "provenance_label": f"Verified through career experiment: {template.title}",
                "assessment_basis": "deterministic_rubric",
                "experiment_template_id": template.id,
                "experiment_title": template.title,
                "experiment_session_id": session.id,
                "submission_id": submission.id,
                "deterministic_review_id": review.id,
                "deterministic_score": score_hint,
                "evidence_classification": strength,
                "skill_id": skill_id,
                "skill_label": _skill_label(skill_id),
                "hypothesis_id": session.hypothesis_id,
                "canonical_direction_id": canonical_direction_id,
                "linked_gap": linked_gap,
                "timestamp": utc_now_naive().isoformat(),
            },
        )
        item.update(
            {
                "review_id": review.id,
                "deterministic_score": score_hint,
                "classification": strength,
                "source_type": DETERMINISTIC_EXPERIMENT_SOURCE,
            }
        )
        evidence_created.append(item)
    if intended_gap_skill_id and intended_gap_skill_id not in by_skill:
        evidence_not_created.append(
            {
                "skill_id": intended_gap_skill_id,
                "skill_label": _skill_label(intended_gap_skill_id),
                "deterministic_score": None,
                "reason": "The deterministic rubric did not directly assess this linked priority gap.",
            }
        )
    persisted = _persisted_deterministic_evidence(db, session.profile_id, result.id)
    linked_gap["generated_skill_ids"] = [item["skill_id"] for item in persisted]
    if intended_gap_skill_id:
        target_evidence = next((item for item in persisted if item["skill_id"] == intended_gap_skill_id), None)
        target_verified = bool(target_evidence and target_evidence.get("classification") == "Practically verified")
        linked_gap["remaining_unresolved"] = not target_verified
        if target_verified:
            linked_gap["message"] = "The linked gap was directly assessed and is now practically verified by the deterministic rubric."
        elif not linked_gap.get("directly_assessed"):
            linked_gap["message"] = f"This experiment generated evidence for other skills, but did not directly verify the linked {_skill_label(intended_gap_skill_id)} gap."
        else:
            linked_gap["message"] = "The linked gap was directly assessed, but its direct rubric score did not reach the practical-verification threshold."
    for source in db.scalars(
        select(SkillEvidenceSource).where(
            SkillEvidenceSource.profile_id == session.profile_id,
            SkillEvidenceSource.source_type == DETERMINISTIC_EXPERIMENT_SOURCE,
            SkillEvidenceSource.source_id == result.id,
        )
    ).all():
        metadata = dict(source.source_metadata_json or {})
        metadata["linked_gap"] = linked_gap
        source.source_metadata_json = metadata
        flag_modified(source, "source_metadata_json")
    actual_gain = _evidence_gain_label(result.overall_score)
    result.evidence_created_json = persisted
    result.actual_evidence_gain_json = {
        "expected": (session.source_metadata_json or {}).get("expected_evidence_gain", "Moderate"),
        "actual": actual_gain,
        "reason": "Observed from the deterministic rubric and submitted artefact. It is bounded role-experiment evidence, not certification or an employment suitability claim.",
        "rule_version": result.deterministic_version,
        "authoritative_evidence_created": bool(persisted),
        "persistence": {
            "status": "persisted" if persisted else "no_practical_evidence_generated",
            "review_id": review.id,
            "source_type": DETERMINISTIC_EXPERIMENT_SOURCE,
            "evidence_ids": [item["evidence_id"] for item in persisted],
        },
        "linked_gap": linked_gap,
        "evidence_not_created": evidence_not_created,
        "provenance": {
            "canonical_direction_id": canonical_direction_id,
            "career_match_id": session.career_match_id,
            "hypothesis_id": session.hypothesis_id,
            "experiment_session_id": session.id,
            "submission_id": submission.id,
            "deterministic_review_id": review.id,
            "experiment_template_id": template.id,
        },
    }
    proposals = _create_evidence_proposals(db, session, result, template, submission, criteria_scores, actual_gain)
    result.evidence_proposal_id = proposals[0].id if proposals else None
    session.status = "evaluated"
    session.evaluated_at = session.evaluated_at or utc_now_naive()
    session.updated_at = utc_now_naive()
    session.confidence_label = "Practical evidence persisted" if persisted else "No practical evidence generated"
    db.commit()
    db.refresh(session)
    return session_public(db, session)


def _evaluation_idempotency_key(session: CareerExperimentSession, submission: CareerExperimentSubmission) -> str:
    return f"{session.id}:{submission.id}:deterministic_rubric:{EXPERIMENT_EVAL_VERSION}"


def evaluate_experiment(db: Session, session: CareerExperimentSession) -> dict[str, Any]:
    session_id = session.id
    submission = db.scalar(select(CareerExperimentSubmission).where(CareerExperimentSubmission.session_id == session.id).order_by(CareerExperimentSubmission.created_at.desc()))
    if not submission:
        raise ValueError("Submit deliverables before deterministic evaluation.")
    template = db.get(CareerExperimentTemplate, session.experiment_template_id)
    idempotency_key = _evaluation_idempotency_key(session, submission)
    existing_results = db.scalars(
        select(CareerExperimentResult)
        .where(CareerExperimentResult.session_id == session.id, CareerExperimentResult.submission_id == submission.id)
        .order_by(CareerExperimentResult.created_at.desc())
    ).all()
    if existing_results:
        result = existing_results[0]
        if len(existing_results) == 1 and not result.idempotency_key:
            result.idempotency_key = idempotency_key
        return _persist_deterministic_result(db, session, submission, template, result)

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
    result = CareerExperimentResult(
        session_id=session.id,
        submission_id=submission.id,
        profile_id=session.profile_id,
        overall_score=overall_score,
        overall_label=overall,
        criteria_scores_json=criteria_scores,
        skills_evaluated_json=template.evaluated_skills_json or [],
        strengths_json=[item["criterion_id"] for item in criteria_scores if item["rating"] >= 3],
        improvement_areas_json=[item["criterion_id"] for item in criteria_scores if item["rating"] <= 2],
        deterministic_version=EXPERIMENT_EVAL_VERSION,
        idempotency_key=idempotency_key,
    )
    db.add(result)
    try:
        db.flush()
    except IntegrityError:
        # A concurrent retry won the unique idempotency key. Reuse the durable
        # result rather than generating a second review or evidence set.
        db.rollback()
        session = db.get(CareerExperimentSession, session_id)
        submission = db.scalar(select(CareerExperimentSubmission).where(CareerExperimentSubmission.session_id == session_id).order_by(CareerExperimentSubmission.created_at.desc()))
        result = db.scalar(select(CareerExperimentResult).where(CareerExperimentResult.idempotency_key == idempotency_key))
        if not session or not submission or not result:
            raise
    return _persist_deterministic_result(db, session, submission, template, result)


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
    evidence_rows = db.scalars(select(SkillEvidence).where(SkillEvidence.skill_inventory_id.in_(inventory_ids), SkillEvidence.verification_status != "provisional_pending_review")).all() if inventory_ids else []
    evidence_by_inventory = defaultdict(list)
    for row in evidence_rows:
        evidence_by_inventory[row.skill_inventory_id].append(row)
    authoritative_ids = [row.id for row in evidence_rows]
    confidence_rows = db.scalars(select(SkillEvidenceConfidence).where(SkillEvidenceConfidence.profile_id == profile_id, SkillEvidenceConfidence.skill_evidence_id.in_(authoritative_ids))).all() if authoritative_ids else []
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
                            "provenance_label": (source.source_metadata_json or {}).get("provenance_label") or source.source_type.replace("_", " ").title(),
                            "title": source.title,
                            "url": source.url,
                            "independent_confirmation": source.independent_confirmation,
                            "experiment_session_id": (source.source_metadata_json or {}).get("experiment_session_id"),
                            "submission_id": (source.source_metadata_json or {}).get("submission_id"),
                            "deterministic_review_id": (source.source_metadata_json or {}).get("deterministic_review_id"),
                            "deterministic_score": (source.source_metadata_json or {}).get("deterministic_score"),
                        }
                        for source in source_by_evidence.get(evidence.id, [])
                    ],
                    "confidence": confidence.confidence_label if confidence else "Limited evidence",
                    "strength": confidence.strength_label if confidence else "Self-reported",
                }
            )
        recency = recencies.get(inventory.skill_id)
        aggregate_score = max(confidence_scores) if confidence_scores else (2.5 if inventory.evidence_status != "self_reported" else 1.5)
        strength_rank = {"Self-reported": 1, "Supported": 2, "Demonstrated": 3, "Practically verified": 4}
        strongest_strength = max(strength_labels, key=lambda label: strength_rank.get(label, 0)) if strength_labels else ("Self-reported" if inventory.evidence_status == "self_reported" else "Supported")
        skills.append(
            {
                "skill_id": inventory.skill_id,
                "skill_label": inventory.skill_label,
                "category": inventory.category,
                "declared_level": inventory.level,
                "target_level": max(3, inventory.level) if roles_by_skill.get(inventory.skill_id) else inventory.level,
                "evidence_confidence": confidence_label(aggregate_score, len(evidence_items)),
                "strongest_evidence_label": strongest_strength,
                "evidence_sources": evidence_items,
                "recency": {
                    "first_demonstrated_date": recency.first_demonstrated_at.isoformat() if recency and recency.first_demonstrated_at else None,
                    "most_recent_evidence_date": recency.most_recent_evidence_at.isoformat() if recency and recency.most_recent_evidence_at else None,
                    "last_professional_use": recency.last_professional_use_at.isoformat() if recency and recency.last_professional_use_at else None,
                    "evidence_age_days": recency.evidence_age_days if recency else None,
                    "refresh_recommendation": recency.refresh_recommendation if recency else "Add dated evidence so recency can be assessed.",
                    "status": recency.status if recency else "Unknown",
                },
                "status": (
                    "Needs verification"
                    if not evidence_items
                    else "Practically verified evidence" if strongest_strength == "Practically verified"
                    else "Demonstrated evidence" if strongest_strength == "Demonstrated"
                    else "Evidence available"
                ),
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


def list_evidence_proposals(db: Session, profile: Profile, status: str | None = None) -> list[dict[str, Any]]:
    query = select(CareerEvidenceProposal).where(CareerEvidenceProposal.profile_id == profile.id)
    if status:
        query = query.where(CareerEvidenceProposal.status == status.upper())
    rows = db.scalars(query.order_by(CareerEvidenceProposal.created_at.desc())).all()
    return [evidence_proposal_public(row) for row in rows]


def _remove_confirmed_proposal_evidence(db: Session, proposal: CareerEvidenceProposal) -> list[str]:
    sources = db.scalars(select(SkillEvidenceSource).where(SkillEvidenceSource.profile_id == proposal.profile_id, SkillEvidenceSource.source_id == proposal.id)).all()
    removed_skills: list[str] = []
    for source in sources:
        evidence = db.get(SkillEvidence, source.skill_evidence_id)
        if not evidence:
            continue
        confidence = db.scalars(select(SkillEvidenceConfidence).where(SkillEvidenceConfidence.skill_evidence_id == evidence.id)).all()
        for row in confidence:
            db.delete(row)
            removed_skills.append(row.skill_id)
        db.delete(source)
        db.delete(evidence)
    for skill_id in set(removed_skills):
        inventory = db.scalar(select(SkillsInventory).where(SkillsInventory.profile_id == proposal.profile_id, SkillsInventory.skill_id == skill_id))
        if inventory:
            remaining = db.scalars(select(SkillEvidence).where(SkillEvidence.skill_inventory_id == inventory.id, SkillEvidence.verification_status != "provisional_pending_review")).all()
            if not remaining:
                inventory.evidence_status = "self_reported"
                inventory.confirmation_status = "self_reported"
    return sorted(set(removed_skills))


def _recalibrate_hypothesis_from_proposal(
    db: Session,
    profile: Profile,
    proposal: CareerEvidenceProposal,
    *,
    direction: str = "up",
    evidence_record: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not proposal.hypothesis_id:
        return None
    hypothesis = db.get(CareerHypothesis, proposal.hypothesis_id)
    if not hypothesis or hypothesis.profile_id != profile.id:
        return None
    match = db.get(CareerMatch, hypothesis.career_match_id) if hypothesis.career_match_id else None
    if not match:
        return None
    before = hypothesis_snapshot(hypothesis)
    before_alignment = float(match.alignment_score or 0)
    result = db.get(CareerExperimentResult, proposal.experiment_result_id) if proposal.experiment_result_id else None
    score = float(result.overall_score or 0) if result else 0
    delta = 8 if score >= 80 else 5 if score >= 65 else 0 if score >= 40 else -6
    if direction == "down":
        delta = -max(4, abs(delta) or 4)
    after_alignment = max(0, min(100, round(before_alignment + delta, 2)))
    match.alignment_score = after_alignment
    match.alignment_label = alignment_label(after_alignment)
    metadata = dict(match.source_metadata_json or {})
    dimensions = dict(metadata.get("hypothesis_dimensions") or {})
    dimension_scores = dict(dimensions.get("scores") or {})
    previous_dimensions = dict(dimension_scores)
    if dimension_scores:
        evidence_before = float(dimension_scores.get("evidence_strength", 0))
        evidence_delta = 12 if direction == "up" and score >= 65 else 6 if direction == "up" else -12
        dimension_scores["evidence_strength"] = round(max(0, min(100, evidence_before + evidence_delta)), 2)
        if direction == "up" and delta > 0:
            dimension_scores["capability_fit"] = round(max(0, min(100, float(dimension_scores.get("capability_fit", 0)) + delta * 0.35)), 2)
        dimensions["scores"] = dimension_scores
        dimensions["labels"] = {key: fit_label(value) for key, value in dimension_scores.items()}
        metadata["hypothesis_dimensions"] = dimensions
    metadata["career_resilience"] = {
        "latest_recalibration_reason": "user_confirmed_evidence" if direction == "up" else "evidence_rejected_or_outdated",
        "latest_evidence_proposal_id": proposal.id,
        "what_changed": (
            f"The {hypothesis.title} hypothesis gained bounded evidence support from {proposal.title}."
            if direction == "up"
            else f"The {hypothesis.title} hypothesis moved toward higher uncertainty because {proposal.title} was rejected or corrected."
        ),
        "dimension_changes": {
            "before": previous_dimensions,
            "after": dimension_scores,
            "changed_categories": ["evidence_strength", "fit_band", "uncertainty"],
            "unchanged_categories": ["natural_fit", "transition_feasibility"],
        },
    }
    match.source_metadata_json = metadata
    flag_modified(match, "source_metadata_json")
    hypothesis.current_alignment_score = after_alignment
    hypothesis.current_version_number = int(hypothesis.current_version_number or 1) + 1
    hypothesis.fit_band = _qualitative_fit_band(after_alignment, metadata)
    hypothesis.uncertainty_label = "Moderate evidence support" if direction == "up" and delta > 0 else "Higher uncertainty" if direction == "down" else "Additional evidence required"
    breakdown = dict(hypothesis.source_breakdown_json or {})
    breakdown["EXPERIMENT"] = int(breakdown.get("EXPERIMENT", 0)) + (1 if direction == "up" else 0)
    breakdown["EVIDENCE"] = int(breakdown.get("EVIDENCE", 0)) + (1 if direction == "up" else -1)
    breakdown["USER_CONFIRMED"] = int(breakdown.get("USER_CONFIRMED", 0)) + (1 if direction == "up" else -1)
    hypothesis.source_breakdown_json = {key: max(0, value) if isinstance(value, int) else value for key, value in breakdown.items()}
    explanation = dict(hypothesis.explanation_json or {})
    explanation["last_change"] = metadata["career_resilience"]["what_changed"]
    explanation["before"] = before
    explanation["after"] = {"fit_band": hypothesis.fit_band, "uncertainty_label": hypothesis.uncertainty_label, "alignment_score_internal": after_alignment}
    explanation["rule_version"] = EVIDENCE_CALIBRATION_VERSION
    hypothesis.explanation_json = explanation
    hypothesis.version = f"career-hypothesis-v{hypothesis.current_version_number}"
    after = hypothesis_snapshot(hypothesis)
    change = {
        "hypothesis_id": hypothesis.id,
        "career_match_id": match.id,
        "title": match.title,
        "before_alignment": before_alignment,
        "after_alignment": after_alignment,
        "change": round(after_alignment - before_alignment, 2),
        "before_fit_band": before["fit_band"],
        "after_fit_band": hypothesis.fit_band,
        "what_changed": metadata["career_resilience"]["what_changed"],
        "affected_dimensions": ["evidence confidence", "fit band", "uncertainty"],
        "unchanged_dimensions": ["natural fit", "transition feasibility"],
        "evidence_proposal_id": proposal.id,
    }
    version = CareerHypothesisVersion(
        hypothesis_id=hypothesis.id,
        profile_id=profile.id,
        version_number=hypothesis.current_version_number,
        snapshot_json=after,
        change_reason=change["what_changed"],
    )
    db.add(version)
    run = CareerRecalibrationRun(
        profile_id=profile.id,
        user_id=profile.user_id,
        career_match_id=match.id,
        hypothesis_id=hypothesis.id,
        experiment_result_id=proposal.experiment_result_id,
        evidence_proposal_id=proposal.id,
        before_json={"hypothesis": before, "career_alignment": [{"career_match_id": match.id, "title": match.title, "alignment_score": before_alignment, "alignment_label": alignment_label(before_alignment)}]},
        after_json={"hypothesis": after, "career_alignment": [{"career_match_id": match.id, "title": match.title, "alignment_score": after_alignment, "alignment_label": alignment_label(after_alignment)}], "new_evidence": [evidence_record or {"proposal_id": proposal.id, "capability": proposal.capability_label}] if direction == "up" else [], "what_changed": change["what_changed"]},
        changed_recommendations_json=[change],
        explanation=(
            f"Your {hypothesis.title} hypothesis changed because a user-confirmed evidence proposal from a bounded experiment was added. This does not establish professional readiness or predict hiring success."
            if direction == "up"
            else f"Your {hypothesis.title} hypothesis moved toward higher uncertainty because previously accepted evidence was rejected or corrected. This does not erase your capability; it changes what is currently supported."
        ),
        uncertainty_label=hypothesis.uncertainty_label,
        version=EVIDENCE_CALIBRATION_VERSION,
        demo_marker=_demo_marker(profile),
    )
    db.add(run)
    db.flush()
    db.add(CareerRecalibrationFactor(run_id=run.id, factor_type="user_confirmed_evidence" if direction == "up" else "evidence_reversal", label=proposal.capability_label, before_value=before_alignment, after_value=after_alignment, weight=1.0, explanation=change["what_changed"]))
    db.commit()
    return recalibration_public(db, run)


def review_evidence_proposal(db: Session, profile: Profile, proposal_id: str, payload: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
    proposal = db.get(CareerEvidenceProposal, proposal_id)
    if not proposal or proposal.profile_id != profile.id:
        raise LookupError("Evidence proposal not found for this profile")
    decision = str(payload.get("decision") or "").strip().lower()
    if decision not in {"accept", "edit", "reject"}:
        raise ValueError("Evidence proposal decision must be accept, edit, or reject")
    if proposal.status == "ACCEPTED" and decision not in {"reject"}:
        raise ValueError("An accepted evidence proposal can only be reversed by rejecting it")
    if decision in {"accept", "edit"}:
        edits = payload.get("edits") if isinstance(payload.get("edits"), dict) else {}
        for field in ["title", "description", "artifact_reference", "category", "capability_label"]:
            if field in edits and edits[field] is not None:
                setattr(proposal, field, str(edits[field]))
        proposal.user_edit_json = edits
        evidence_record = _create_skill_evidence(
            db,
            profile.id,
            proposal.capability_id,
            "career_experiment",
            proposal.title,
            proposal.description,
            url=proposal.artifact_reference if safe_user_url(proposal.artifact_reference) else None,
            source_id=proposal.id,
            source_type="USER_CONFIRMED",
            practical=True,
            independent=False,
            score_hint=70 if proposal.actual_evidence_gain in {"High", "Moderate"} else 50,
            authoritative=True,
            confirmation_source="USER_CONFIRMED",
        )
        proposal.status = "EDITED" if decision == "edit" else "ACCEPTED"
        proposal.verification_state = "USER_CONFIRMED"
        proposal.user_confirmed = True
        proposal.reviewed_at = utc_now_naive()
        proposal.relevance = "User-confirmed bounded project evidence"
        gap = db.get(CareerEvidenceGap, proposal.evidence_gap_id) if proposal.evidence_gap_id else None
        if gap:
            gap.current_evidence_status = "PARTIAL"
            gap.status = "PARTIAL"
            gap.reason = "User-confirmed evidence now exists, but it remains bounded and role-specific rather than proof of readiness."
        db.flush()
        recalibration = _recalibrate_hypothesis_from_proposal(db, profile, proposal, evidence_record=evidence_record)
    else:
        removed_skills = _remove_confirmed_proposal_evidence(db, proposal) if proposal.status in {"ACCEPTED", "EDITED"} else []
        proposal.status = "REJECTED"
        proposal.verification_state = "REJECTED"
        proposal.user_confirmed = False
        proposal.reviewed_at = utc_now_naive()
        proposal.user_edit_json = {"rejection_reason": payload.get("reason", payload.get("note", "User rejected the proposed evidence.")), "removed_skills": removed_skills}
        recalibration = _recalibrate_hypothesis_from_proposal(db, profile, proposal, direction="down") if removed_skills else None
    proposal.updated_at = utc_now_naive()
    db.commit()
    db.refresh(proposal)
    return {"proposal": evidence_proposal_public(proposal), "recalibration": recalibration, "evidence_passport": evidence_passport(db, profile.id), "authoritative_update": decision in {"accept", "edit"}}


def latest_recalibrations(db: Session, profile_id: str, hypothesis_id: str | None = None) -> list[dict[str, Any]]:
    query = select(CareerRecalibrationRun).where(CareerRecalibrationRun.profile_id == profile_id)
    if hypothesis_id:
        query = query.where(CareerRecalibrationRun.hypothesis_id == hypothesis_id)
    rows = db.scalars(query.order_by(CareerRecalibrationRun.created_at.desc())).all()
    return [recalibration_public(db, row) for row in rows]


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
    persisted_evidence = _persisted_deterministic_evidence(db, profile.id, result.id) if result else []
    if result:
        latest = db.scalar(
            select(CareerRecalibrationRun)
            .where(
                CareerRecalibrationRun.profile_id == profile.id,
                CareerRecalibrationRun.experiment_result_id == result.id,
            )
            .order_by(CareerRecalibrationRun.created_at.desc())
        )
        if latest:
            return recalibration_public(db, latest)
        if not persisted_evidence:
            session = db.get(CareerExperimentSession, result.session_id)
            match = db.get(CareerMatch, session.career_match_id) if session and session.career_match_id else None
            return {
                "id": None,
                "profile_id": profile.id,
                "status": "awaiting_persisted_evidence",
                "before": {"career_alignment": [{"career_match_id": match.id, "title": match.title, "alignment_score": match.alignment_score, "alignment_label": match.alignment_label}] if match else []},
                "after": {"career_alignment": [{"career_match_id": match.id, "title": match.title, "alignment_score": match.alignment_score, "alignment_label": match.alignment_label}] if match else [], "new_evidence": [], "uncertainty": "Additional evidence required"},
                "changed_recommendations": [],
                "explanation": "No persisted practical or demonstrated evidence is available for this deterministic result, so career hypotheses were not recalibrated.",
                "uncertainty_label": "Additional evidence required",
                "version": EVIDENCE_CALIBRATION_VERSION,
                "factors": [],
            }
    session = db.get(CareerExperimentSession, result.session_id) if result else None
    template = db.get(CareerExperimentTemplate, session.experiment_template_id) if session else None
    matches = current_career_matches_for_profile(db, profile.id)
    supplied_match = db.get(CareerMatch, session.career_match_id) if session and session.career_match_id else None
    target_direction_id = canonical_career_direction_id(supplied_match) if supplied_match else None
    target_match = next((match for match in matches if target_direction_id and canonical_career_direction_id(match) == target_direction_id), None)
    current_hypotheses = ensure_hypotheses_from_matches(db, profile)
    target_hypothesis = next((item for item in current_hypotheses if target_match and item.career_match_id == target_match.id), None)
    before_hypothesis = hypothesis_snapshot(target_hypothesis) if target_hypothesis else None
    before = {
        "career_alignment": [{"career_match_id": match.id, "title": match.title, "alignment_score": match.alignment_score, "alignment_label": match.alignment_label} for match in matches],
        "assumptions": [item for match in matches for item in (match.assumptions_json or [])][:8],
        "missing_evidence": [item for match in matches for item in (match.missing_skills_json or [])][:8],
        "uncertainty": "Additional evidence required",
    }
    if before_hypothesis:
        before["hypothesis"] = before_hypothesis
    changed = []
    factors = []
    persisted_score = round(sum(item["deterministic_score"] for item in persisted_evidence) / len(persisted_evidence), 2) if persisted_evidence else 0
    # Removing a priority gap is stricter than retaining a useful observation:
    # only directly practical verification may change the gap inventory.
    demonstrated = {item["skill_id"] for item in persisted_evidence if item["deterministic_score"] >= 85}
    for match in matches:
        has_experiment = bool(result and template and persisted_evidence and target_match and match.id == target_match.id)
        before_score = match.alignment_score
        after_score = before_score
        if has_experiment:
            delta = 8 if persisted_score >= 80 else 5 if persisted_score >= 65 else 0 if persisted_score >= 40 else -6
            after_score = max(0, min(100, round(before_score + delta, 2)))
            match.missing_skills_json = [skill for skill in (match.missing_skills_json or []) if skill not in demonstrated]
            match.alignment_score = after_score
            match.alignment_label = alignment_label(after_score)
            metadata = dict(match.source_metadata_json or {})
            dimensions = dict(metadata.get("hypothesis_dimensions") or {})
            dimension_scores = dict(dimensions.get("scores") or {})
            before_dimension_scores = dict(dimension_scores)
            if dimension_scores:
                protected_dimensions = {
                    key: dimension_scores[key]
                    for key in ("natural_fit", "transition_feasibility", "ai_augmentation_opportunity")
                    if key in dimension_scores
                }
                evidence_after = max(float(dimension_scores.get("evidence_strength", 0)), 78 if persisted_score >= 80 else 65 if persisted_score >= 65 else 45 if persisted_score >= 40 else 25)
                dimension_scores["evidence_strength"] = round(min(100, evidence_after), 2)
                dimension_scores["capability_fit"] = round(min(100, float(dimension_scores.get("capability_fit", 0)) + max(0, delta) * 0.35), 2)
                # The event is evidence about a bounded role task. It must not
                # infer a new interest profile, a different transition route,
                # or a broader view of how AI augments the role.
                dimension_scores.update(protected_dimensions)
                dimensions["scores"] = dimension_scores
                dimensions["labels"] = {key: fit_label(value) for key, value in dimension_scores.items()}
                dimensions["last_change"] = {
                    "evidence_strength": "Career experiment evidence was added to the Evidence Passport.",
                    "capability_fit": "Capability interpretation was adjusted only where experiment evidence supported relevant skills.",
                    "natural_fit": "Unchanged; the experiment did not rewrite stated interests or preferences.",
                    "transition_feasibility": "Unchanged by this evidence event.",
                    "ai_augmentation_opportunity": "Unchanged by this evidence event.",
                }
                metadata["hypothesis_dimensions"] = dimensions
            metadata["career_resilience"] = {
                "latest_recalibration_reason": "persisted_deterministic_career_experiment",
                "latest_experiment_result_id": result.id,
                "what_changed": f"The recommendation became stronger after {template.title}." if delta > 0 else "The recommendation remains uncertain because the experiment evidence was limited.",
                "dimension_changes": {
                    "before": before_dimension_scores,
                    "after": dimension_scores,
                    "changed_categories": ["evidence_strength"] + (["capability_fit"] if delta > 0 else []),
                    "unchanged_categories": ["natural_fit", "transition_feasibility", "ai_augmentation_opportunity"],
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
                    "hypothesis_id": target_hypothesis.id if target_hypothesis else None,
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
                    "explanation": "Persisted deterministic career-experiment evidence updated skill evidence and uncertainty.",
                }
            )
        else:
            metadata = dict(match.source_metadata_json or {})
            metadata.setdefault("career_resilience", _counterfactuals(match, has_experiment=False))
            match.source_metadata_json = metadata
            flag_modified(match, "source_metadata_json")
    after_hypothesis = None
    if target_hypothesis and target_match and changed:
        _sync_hypothesis_from_match(
            db,
            profile,
            target_hypothesis,
            target_match,
            preserve_evidence_counts=True,
        )
        # Keep the active hypothesis's visible gap inventory in step with the
        # recalibrated canonical match before creating its next history entry.
        # Superseded gaps remain as resolved records for provenance.
        _sync_hypothesis_evidence_gaps(db, profile, target_hypothesis, target_match)
        evidence_breakdown = dict(target_hypothesis.source_breakdown_json or {})
        evidence_breakdown["EVIDENCE"] = int(evidence_breakdown.get("EVIDENCE", 0) or 0) + 1
        evidence_breakdown["EXPERIMENT"] = int(evidence_breakdown.get("EXPERIMENT", 0) or 0) + 1
        target_hypothesis.source_breakdown_json = evidence_breakdown
        target_hypothesis.current_version_number = int(target_hypothesis.current_version_number or 1) + 1
        target_hypothesis.version = f"career-hypothesis-v{target_hypothesis.current_version_number}"
        target_hypothesis.uncertainty_label = "Reduced but still present"
        after_hypothesis = hypothesis_snapshot(target_hypothesis)
        db.add(
            CareerHypothesisVersion(
                hypothesis_id=target_hypothesis.id,
                profile_id=profile.id,
                version_number=target_hypothesis.current_version_number,
                snapshot_json=after_hypothesis,
                change_reason=f"Persisted deterministic evidence from {template.title} recalibrated this canonical career direction.",
            )
        )
    after = {
        "career_alignment": [{"career_match_id": match.id, "title": match.title, "alignment_score": match.alignment_score, "alignment_label": match.alignment_label} for match in matches],
        "new_evidence": persisted_evidence,
        "remaining_gaps": [item for match in matches for item in (match.missing_skills_json or [])][:8],
        "uncertainty": "Reduced but still present" if changed else "Additional evidence required",
    }
    if after_hypothesis:
        after["hypothesis"] = after_hypothesis
    run = CareerRecalibrationRun(
        profile_id=profile.id,
        user_id=profile.user_id,
        career_match_id=target_match.id if target_match else (session.career_match_id if session else None),
        hypothesis_id=target_hypothesis.id if target_hypothesis else None,
        experiment_result_id=result.id if result else None,
        before_json=before,
        after_json=after,
        changed_recommendations_json=changed,
        explanation="What changed this recommendation? Structured experiment evidence was added to the Evidence Passport and deterministic factors were recalculated for the selected canonical career direction only.",
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
        "hypothesis_id": run.hypothesis_id,
        "experiment_result_id": run.experiment_result_id,
        "evidence_proposal_id": run.evidence_proposal_id,
        "status": run.status,
        "before": run.before_json or {},
        "after": run.after_json or {},
        "changed_recommendations": run.changed_recommendations_json or [],
        "explanation": run.explanation,
        "what_changed": (run.after_json or {}).get("what_changed") or (run.changed_recommendations_json or [{}])[0].get("what_changed", ""),
        "uncertainty_label": run.uncertainty_label,
        "version": run.version,
        "rule_version": run.version,
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
        select(CareerExperimentSession).where(CareerExperimentSession.profile_id == profile.id, CareerExperimentSession.status.in_(["suggested", "saved", "planned", "in_progress", "submitted", "needs_review", "evaluated"])).order_by(CareerExperimentSession.updated_at.desc())
    ).all()
    latest_plan = latest_immediate_action_plan(db, profile.id)
    paths = latest_supported_paths(db, profile.id)
    passport = evidence_passport(db, profile.id)
    gaps = list_profile_evidence_gaps(db, profile)
    proposals = list_evidence_proposals(db, profile)
    programmes = list_support_programmes(db)[:4]
    # This is a read-model projection of the existing deterministic ranking.
    # Keeping it alongside the dashboard means a page refresh can display the
    # same evidence_sufficient outcome without creating a new experiment.
    evidence_states = []
    for hypothesis in hypotheses:
        match = db.get(CareerMatch, hypothesis.career_match_id) if hypothesis.career_match_id else None
        selected = _adaptive_experiment_recommendation(db, profile, match, hypothesis) if match else None
        if not selected:
            continue
        recommendation = selected["recommendation"]
        evidence_states.append(
            {
                "hypothesis_id": hypothesis.id,
                "career_match_id": match.id,
                "canonical_direction_id": _hypothesis_direction_id(hypothesis),
                "state": recommendation.get("state", "experiment_recommended"),
                "recommendation": recommendation,
            }
        )
    next_action = "Select a career hypothesis and confirm a role experiment."
    if latest_plan and latest_plan.get("items"):
        next_action = latest_plan["items"][0]["title"]
    elif any(item["status"] == "PENDING_REVIEW" for item in proposals):
        next_action = "Review a provisional Evidence Passport proposal."
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
                "canonical_direction_id": _hypothesis_direction_id(item),
                "title": item.title,
                "role_family": item.role_family,
                "statement": item.statement,
                "uncertainty_label": item.uncertainty_label,
                "status": item.status,
                "version": item.current_version_number,
                "fit_band": item.fit_band,
                "user_decision_state": item.user_decision_state,
                "source_breakdown": item.source_breakdown_json or {},
                "missing_evidence": item.missing_evidence_json or [],
            }
            for item in hypotheses[:4]
        ],
        "active_experiments": [session_public(db, item) for item in active_sessions],
        "evidence_updates": passport["skills"][:5],
        "evidence_gaps": gaps["gaps"],
        "evidence_states": evidence_states,
        "evidence_proposals": proposals,
        "recalibration_history": latest_recalibrations(db, profile.id)[:6],
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
    db.execute(delete(CareerEvidenceProposal).where(CareerEvidenceProposal.profile_id.in_(ids)))
    db.execute(delete(CareerEvidenceGap).where(CareerEvidenceGap.profile_id.in_(ids)))
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

