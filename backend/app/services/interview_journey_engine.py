from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timedelta
from app.core.time import utc_now_naive
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.interview_journey import (
    Interview,
    InterviewAnswer,
    InterviewFollowUpDraft,
    InterviewPreparationBrief,
    InterviewQuestion,
    InterviewReflection,
    MockInterviewSession,
    MockInterviewTurn,
    OfferReview,
    StarStory,
    StarStoryVersion,
    VoiceProviderSession,
)
from app.models.market_application import (
    ApplicationDocument,
    ApplicationRecalibrationRun,
    JobAnalysis,
    JobApplication,
    JobApplicationEvent,
    JobRequirement,
    JobRequirementEvidenceMatch,
)
from app.models.profile import Profile
from app.services.career_resilience_engine import evidence_passport
from app.services.market_application_engine import (
    APPLICATION_STATUSES,
    _claim_status_from_text,
    _clean_text,
    _demo_marker,
    _normalise_skill_phrase,
    application_event_public,
    application_public,
    recalibration_public,
    require_analysis,
    require_application,
)

INTERVIEW_VERSION = "interview-journey-v1"

INTERVIEW_STAGE_ALIASES = {
    "recruiter": "recruiter_screening",
    "screening": "recruiter_screening",
    "recruiter_screening": "recruiter_screening",
    "first": "first_interview",
    "first_interview": "first_interview",
    "hiring_manager": "hiring_manager",
    "hiring_manager_interview": "hiring_manager",
    "behavioural": "behavioural",
    "behavioral": "behavioural",
    "technical": "technical",
    "case": "case_study",
    "case_study": "case_study",
    "portfolio": "portfolio",
    "panel": "panel",
    "final": "final",
    "reference": "reference_check",
    "reference_check": "reference_check",
    "offer": "offer_discussion",
    "offer_discussion": "offer_discussion",
    "salary": "salary_negotiation",
    "negotiation": "salary_negotiation",
    "custom": "custom",
    "unknown": "custom",
}

INTERVIEW_STAGES = {
    "recruiter_screening": {
        "label": "Recruiter screening",
        "purpose": "Verify high-level fit, logistics, motivation, and application basics.",
        "evaluates": ["professional introduction", "motivation", "availability", "location and language fit", "salary expectations when user-provided"],
        "status": "Recruiter screening",
    },
    "first_interview": {
        "label": "First interview",
        "purpose": "Establish role understanding, relevant background, and mutual fit.",
        "evaluates": ["role understanding", "transferable experience", "communication", "learning ability"],
        "status": "Interview 1",
    },
    "hiring_manager": {
        "label": "Hiring manager interview",
        "purpose": "Assess role-specific judgement, collaboration, impact, and first-90-day priorities.",
        "evaluates": ["relevant experience", "decision-making", "team fit", "professional judgement"],
        "status": "Interview 1",
    },
    "behavioural": {
        "label": "Behavioural interview",
        "purpose": "Explore past behaviour through evidence-backed examples and reflection.",
        "evaluates": ["conflict", "failure", "leadership", "ambiguity", "feedback", "ethical judgement"],
        "status": "Interview 2",
    },
    "technical": {
        "label": "Technical interview",
        "purpose": "Probe job-relevant technical knowledge, project evidence, architecture, testing, and gaps.",
        "evaluates": ["confirmed job stack", "debugging", "testing", "API design", "security", "deployment", "trade-offs"],
        "status": "Technical or case stage",
    },
    "case_study": {
        "label": "Case-study interview",
        "purpose": "Observe problem framing, assumptions, solution structure, trade-offs, and success metrics.",
        "evaluates": ["clarifying questions", "constraints", "alternatives", "risks", "presentation"],
        "status": "Technical or case stage",
    },
    "portfolio": {
        "label": "Portfolio interview",
        "purpose": "Review project choices, user need, process, decisions, limitations, and lessons learned.",
        "evaluates": ["project relevance", "user role", "constraints", "results", "what would improve"],
        "status": "Portfolio stage",
    },
    "panel": {
        "label": "Panel interview",
        "purpose": "Answer concise questions for multiple stakeholder perspectives.",
        "evaluates": ["conciseness", "stakeholder-specific evidence", "handling repeated questions"],
        "status": "Interview 2",
    },
    "final": {
        "label": "Final interview",
        "purpose": "Clarify strategic alignment, expectations, unresolved concerns, and decision criteria.",
        "evaluates": ["values", "long-term contribution", "expectations", "questions"],
        "status": "Final interview",
    },
    "reference_check": {
        "label": "Reference-check preparation",
        "purpose": "Prepare accurate references and evidence without inventing feedback.",
        "evaluates": ["reference readiness", "confirmed achievements", "unknowns"],
        "status": "Reference check",
    },
    "offer_discussion": {
        "label": "Offer discussion",
        "purpose": "Clarify offer components and user priorities without legal or tax conclusions.",
        "evaluates": ["salary", "benefits", "start date", "working mode", "unresolved risks"],
        "status": "Offer",
    },
    "salary_negotiation": {
        "label": "Salary negotiation",
        "purpose": "Prepare priority-based negotiation points and questions without definitive financial advice.",
        "evaluates": ["salary", "benefits", "training", "working hours", "review period"],
        "status": "Offer",
    },
    "custom": {
        "label": "Unknown or custom stage",
        "purpose": "Clarify what the organisation is likely evaluating before preparing.",
        "evaluates": ["stage uncertainty", "role evidence", "questions for clarification"],
        "status": "Unknown",
    },
}

READINESS_ITEMS = [
    "stage confirmed",
    "date and format confirmed",
    "job requirements reviewed",
    "introduction prepared",
    "relevant evidence selected",
    "STAR stories selected",
    "weak areas reviewed",
    "questions for employer prepared",
    "technical or portfolio preparation complete",
    "practical setup checked",
    "mock interview completed",
    "user final confirmation",
]

SUPPORTED_APPLICATION_EVENTS = {
    "interview_invitation_received",
    "interview_scheduled",
    "preparation_started",
    "mock_interview_completed",
    "interview_completed",
    "follow_up_sent",
    "feedback_received",
    "next_stage_received",
    "rejected",
    "offer_received",
    "withdrawn",
}

STAR_CATEGORIES = {
    "leadership",
    "teamwork",
    "conflict",
    "failure",
    "difficult_client",
    "ambiguity",
    "innovation",
    "deadline_pressure",
    "learning",
    "technical_problem",
    "ethical_decision",
    "user_centred_design",
    "process_improvement",
    "communication",
    "career_transition",
}

FOLLOW_UP_DRAFT_TYPES = {
    "thank_you",
    "requested_document",
    "clarification",
    "confirmation",
    "rescheduling",
    "withdrawal",
    "offer_acknowledgment",
    "decision_timeline",
}

def _now() -> datetime:
    return utc_now_naive()


def _parse_datetime(value: str | datetime | None) -> datetime | None:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).replace(tzinfo=None)
    except ValueError as error:
        raise ValueError("Interview date must be ISO date or date-time text.") from error


def _normalise_stage(stage: str | None) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", (stage or "custom").strip().lower()).strip("_")
    normalised = INTERVIEW_STAGE_ALIASES.get(key)
    if not normalised:
        raise ValueError("Unsupported interview stage.")
    return normalised


def _limited_list(value: Any, limit: int = 20) -> list[Any]:
    if not isinstance(value, list):
        return []
    return value[:limit]


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text or ""))


def _stage_definition(stage: str) -> dict[str, Any]:
    return INTERVIEW_STAGES.get(stage, INTERVIEW_STAGES["custom"])


def _stage_label(stage: str) -> str:
    return _stage_definition(stage)["label"]


def _stage_status(stage: str) -> str:
    return _stage_definition(stage)["status"]


def _stage_count(db: Session, profile_id: str, application_id: str | None) -> int:
    query = select(func.count()).select_from(Interview).where(Interview.profile_id == profile_id)
    if application_id:
        query = query.where(Interview.application_id == application_id)
    return int(db.scalar(query) or 0)


def _requirements(db: Session, analysis_id: str | None) -> list[JobRequirement]:
    if not analysis_id:
        return []
    return db.scalars(select(JobRequirement).where(JobRequirement.analysis_id == analysis_id, JobRequirement.status == "active").order_by(JobRequirement.order_index)).all()


def _requirement_matches(db: Session, requirement_id: str) -> list[JobRequirementEvidenceMatch]:
    return db.scalars(select(JobRequirementEvidenceMatch).where(JobRequirementEvidenceMatch.requirement_id == requirement_id).order_by(JobRequirementEvidenceMatch.created_at)).all()


def _evidence_for_requirement(db: Session, requirement: JobRequirement) -> list[dict[str, Any]]:
    links = []
    for match in _requirement_matches(db, requirement.id):
        if match.evidence_id:
            links.append(
                {
                    "evidence_id": match.evidence_id,
                    "evidence_type": match.evidence_type,
                    "match_category": match.match_category,
                    "evidence_strength": match.evidence_strength,
                    "deterministic_reason": match.deterministic_reason,
                }
            )
        for item in match.transferable_evidence_json or []:
            links.append({"evidence_type": "transferable", "label": item, "match_category": "Transferable evidence"})
    return links


def _passport_summary(db: Session, profile_id: str) -> dict[str, Any]:
    passport = evidence_passport(db, profile_id)
    skills = passport.get("skills", [])
    return {
        "profile_id": profile_id,
        "version": passport.get("version"),
        "methodology": passport.get("methodology"),
        "skills": skills,
        "skills_by_id": {item.get("skill_id"): item for item in skills if item.get("skill_id")},
    }


def _requirement_skill(requirement: JobRequirement) -> str:
    return requirement.normalised_skill_id or _normalise_skill_phrase(requirement.requirement_text)


def _demo_for_profile(profile: Profile | None) -> bool:
    return _demo_marker(profile)


def require_interview(db: Session, interview_id: str, profile: Profile | None = None) -> Interview:
    row = db.get(Interview, interview_id)
    if not row:
        raise LookupError("Interview not found")
    if profile and row.profile_id != profile.id:
        raise PermissionError("Interview does not belong to this profile")
    return row


def require_star_story(db: Session, story_id: str, profile: Profile | None = None) -> StarStory:
    row = db.get(StarStory, story_id)
    if not row or row.status == "deleted":
        raise LookupError("STAR story not found")
    if profile and row.profile_id != profile.id:
        raise PermissionError("STAR story does not belong to this profile")
    return row


def require_question(db: Session, question_id: str, profile: Profile | None = None) -> InterviewQuestion:
    row = db.get(InterviewQuestion, question_id)
    if not row:
        raise LookupError("Interview question not found")
    if profile and row.profile_id != profile.id:
        raise PermissionError("Interview question does not belong to this profile")
    return row


def require_mock_session(db: Session, session_id: str, profile: Profile | None = None) -> MockInterviewSession:
    row = db.get(MockInterviewSession, session_id)
    if not row:
        raise LookupError("Mock interview session not found")
    if profile and row.profile_id != profile.id:
        raise PermissionError("Mock interview session does not belong to this profile")
    return row


def require_offer_review(db: Session, review_id: str, profile: Profile | None = None) -> OfferReview:
    row = db.get(OfferReview, review_id)
    if not row:
        raise LookupError("Offer review not found")
    if profile and row.profile_id != profile.id:
        raise PermissionError("Offer review does not belong to this profile")
    return row


def create_interview(db: Session, profile: Profile, payload: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
    stage = _normalise_stage(payload.get("stage_type"))
    application = None
    analysis = None
    if payload.get("application_id"):
        application = require_application(db, payload["application_id"], profile)
        analysis = require_analysis(db, application.job_analysis_id, profile) if application.job_analysis_id else None
    elif payload.get("job_analysis_id"):
        analysis = require_analysis(db, payload["job_analysis_id"], profile)

    if payload.get("job_analysis_id") and analysis is None:
        analysis = require_analysis(db, payload["job_analysis_id"], profile)

    if payload.get("application_id") and not application:
        raise LookupError("Application not found")

    participants = []
    for item in _limited_list(payload.get("participants"), 12):
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or item.get("participant_role") or "unknown interviewer").strip()[:120]
        participants.append(
            {
                "role": role or "unknown interviewer",
                "name": str(item.get("name") or "").strip()[:160],
                "user_confirmed": bool(item.get("user_confirmed", False)),
            }
        )

    scheduled_at = _parse_datetime(payload.get("scheduled_at") or payload.get("scheduled_date"))
    interview = Interview(
        profile_id=profile.id,
        user_id=user_id or profile.user_id,
        application_id=application.id if application else payload.get("application_id"),
        job_analysis_id=analysis.id if analysis else None,
        cv_document_id=(application.cv_document_id if application else payload.get("cv_document_id")),
        cover_letter_document_id=(application.cover_letter_document_id if application else payload.get("cover_letter_document_id")),
        organisation=_clean_text(payload.get("organisation") or (application.organisation if application else analysis.organisation if analysis else ""), 255),
        role=_clean_text(payload.get("role") or payload.get("title") or (application.title if application else analysis.title if analysis else "Manual interview"), 255),
        stage_type=stage,
        stage_order=int(payload.get("stage_order") or _stage_count(db, profile.id, application.id if application else None) + 1),
        scheduled_at=scheduled_at,
        timezone=str(payload.get("timezone") or "Europe/Bucharest")[:80],
        location_or_platform=_clean_text(payload.get("location_or_platform") or payload.get("location") or "", 255),
        interview_format=str(payload.get("interview_format") or "unknown")[:80],
        expected_duration_minutes=payload.get("expected_duration_minutes"),
        participants_json=participants,
        preparation_status="Not started",
        mock_session_status="Not started",
        confidence_before=payload.get("confidence_before"),
        confidence_after=payload.get("confidence_after"),
        interview_result=payload.get("interview_result") or "Unknown",
        follow_up_status=payload.get("follow_up_status") or "Not started",
        notes=_clean_text(payload.get("notes") or "", 4000),
        source=payload.get("source") or ("application" if application else "manual"),
        user_confirmed=bool(payload.get("user_confirmed", False)),
        demo_marker=_demo_for_profile(profile) or bool(application and application.demo_marker),
    )
    db.add(interview)
    db.flush()
    if application:
        db.add(
            JobApplicationEvent(
                application_id=application.id,
                profile_id=profile.id,
                event_type="interview_invitation_received" if payload.get("source") != "manual" else "interview_created",
                from_status=application.status,
                to_status=application.status,
                description=f"Interview Journey record created for {_stage_label(stage)}. Application status was not changed automatically.",
                event_metadata_json={"interview_id": interview.id, "requires_status_confirmation": True},
                created_by=user_id,
            )
        )
    db.commit()
    return interview_public(db, interview)


def update_interview(db: Session, interview: Interview, payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("stage_type") is not None:
        interview.stage_type = _normalise_stage(payload.get("stage_type"))
    for key, limit in [
        ("organisation", 255),
        ("role", 255),
        ("timezone", 80),
        ("location_or_platform", 255),
        ("interview_format", 80),
        ("preparation_status", 80),
        ("mock_session_status", 80),
        ("interview_result", 80),
        ("follow_up_status", 80),
        ("notes", 4000),
    ]:
        if key in payload and payload[key] is not None:
            setattr(interview, key, _clean_text(str(payload[key]), limit))
    if "scheduled_at" in payload or "scheduled_date" in payload:
        interview.scheduled_at = _parse_datetime(payload.get("scheduled_at") or payload.get("scheduled_date"))
    for key in ["stage_order", "expected_duration_minutes", "confidence_before", "confidence_after"]:
        if key in payload:
            setattr(interview, key, payload[key])
    if "participants" in payload:
        interview.participants_json = _limited_list(payload.get("participants"), 12)
    if "user_confirmed" in payload:
        interview.user_confirmed = bool(payload["user_confirmed"])
    interview.updated_at = _now()
    db.commit()
    return interview_public(db, interview)


def delete_interview(db: Session, interview: Interview) -> dict[str, Any]:
    session_ids = db.scalars(select(MockInterviewSession.id).where(MockInterviewSession.interview_id == interview.id)).all()
    question_ids = db.scalars(select(InterviewQuestion.id).where(InterviewQuestion.interview_id == interview.id)).all()
    if session_ids:
        db.execute(delete(MockInterviewTurn).where(MockInterviewTurn.session_id.in_(session_ids)))
        db.execute(delete(VoiceProviderSession).where(VoiceProviderSession.mock_session_id.in_(session_ids)))
    if question_ids:
        db.execute(delete(InterviewAnswer).where(InterviewAnswer.question_id.in_(question_ids)))
    for model in [
        InterviewFollowUpDraft,
        InterviewReflection,
        InterviewPreparationBrief,
        InterviewQuestion,
        MockInterviewSession,
        VoiceProviderSession,
    ]:
        db.execute(delete(model).where(model.interview_id == interview.id))
    db.delete(interview)
    db.commit()
    return {"status": "deleted", "id": interview.id}


def list_interviews(db: Session, profile_id: str) -> list[dict[str, Any]]:
    rows = db.scalars(select(Interview).where(Interview.profile_id == profile_id).order_by(Interview.scheduled_at.is_(None), Interview.scheduled_at, Interview.created_at.desc())).all()
    return [interview_public(db, row) for row in rows]


def interview_public(db: Session, row: Interview, include_details: bool = False) -> dict[str, Any]:
    question_count = db.scalar(select(func.count()).select_from(InterviewQuestion).where(InterviewQuestion.interview_id == row.id)) or 0
    mock_count = db.scalar(select(func.count()).select_from(MockInterviewSession).where(MockInterviewSession.interview_id == row.id)) or 0
    reflection = db.scalar(select(InterviewReflection).where(InterviewReflection.interview_id == row.id).order_by(InterviewReflection.updated_at.desc()))
    brief = db.scalar(select(InterviewPreparationBrief).where(InterviewPreparationBrief.interview_id == row.id).order_by(InterviewPreparationBrief.updated_at.desc()))
    app = db.get(JobApplication, row.application_id) if row.application_id else None
    payload = {
        "id": row.id,
        "profile_id": row.profile_id,
        "application_id": row.application_id,
        "job_analysis_id": row.job_analysis_id,
        "cv_document_id": row.cv_document_id,
        "cover_letter_document_id": row.cover_letter_document_id,
        "organisation": row.organisation,
        "role": row.role,
        "stage_type": row.stage_type,
        "stage_label": _stage_label(row.stage_type),
        "stage_order": row.stage_order,
        "scheduled_at": row.scheduled_at.isoformat() if row.scheduled_at else None,
        "timezone": row.timezone,
        "location_or_platform": row.location_or_platform,
        "interview_format": row.interview_format,
        "expected_duration_minutes": row.expected_duration_minutes,
        "participants": row.participants_json or [],
        "preparation_status": row.preparation_status,
        "mock_session_status": row.mock_session_status,
        "confidence_before": row.confidence_before,
        "confidence_after": row.confidence_after,
        "interview_result": row.interview_result,
        "follow_up_status": row.follow_up_status,
        "notes": row.notes,
        "source": row.source,
        "user_confirmed": row.user_confirmed,
        "demo_marker": row.demo_marker,
        "question_count": question_count,
        "mock_session_count": mock_count,
        "has_preparation": bool(brief),
        "has_reflection": bool(reflection),
        "application_status": app.status if app else "",
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }
    if include_details:
        payload["application"] = application_public(db, app) if app else None
        payload["preparation"] = preparation_public(brief) if brief else None
        payload["questions"] = list_interview_questions(db, row)
        payload["mock_sessions"] = list_mock_sessions(db, row)
        payload["reflection"] = reflection_public(reflection) if reflection else None
    return payload


def interview_dashboard(db: Session, profile: Profile) -> dict[str, Any]:
    interviews = list_interviews(db, profile.id)
    stories = list_star_stories(db, profile.id)
    upcoming = [item for item in interviews if item["scheduled_at"] and item["interview_result"] == "Unknown"]
    pending_reflections = [item for item in interviews if item["interview_result"] != "Unknown" and not item["has_reflection"]]
    active_preparation = [item for item in interviews if item["preparation_status"] in {"Not started", "In progress", "Needs evidence", "Ready for practice"}]
    gaps = Counter()
    for interview in interviews:
        if not interview["job_analysis_id"]:
            gaps["missing job analysis"] += 1
            continue
        for req in _requirements(db, interview["job_analysis_id"]):
            matches = _requirement_matches(db, req.id)
            if not matches or any(match.match_category == "Missing evidence" for match in matches):
                gaps[req.requirement_text] += 1
    recent_sessions = db.scalars(select(MockInterviewSession).where(MockInterviewSession.profile_id == profile.id).order_by(MockInterviewSession.updated_at.desc()).limit(4)).all()
    next_action = "Generate a preparation brief for the next interview." if active_preparation else "Record a post-interview reflection when the next real interview is completed."
    return {
        "profile_id": profile.id,
        "upcoming_interviews": upcoming[:4],
        "active_preparation": active_preparation[:4],
        "saved_star_stories": stories[:8],
        "readiness_checklist": READINESS_ITEMS,
        "recent_mock_sessions": [mock_session_public(db, item) for item in recent_sessions],
        "unresolved_evidence_gaps": [{"label": label, "count": count} for label, count in gaps.most_common(8)],
        "pending_reflections": pending_reflections[:4],
        "application_stage_links": [{"interview_id": item["id"], "application_id": item["application_id"], "application_status": item["application_status"]} for item in interviews if item["application_id"]],
        "next_recommended_action": next_action,
        "source_notes": [
            "Interview Journey reuses Application Tracker, Job Analysis, Evidence Passport, CV Evidence Lock, and application event history.",
            "Mock interviews are optional; text mode remains available when voice is disabled.",
        ],
    }


def _confirmed_requirements_payload(db: Session, interview: Interview) -> list[dict[str, Any]]:
    requirements = []
    for requirement in _requirements(db, interview.job_analysis_id):
        requirements.append(
            {
                "id": requirement.id,
                "text": requirement.requirement_text,
                "category": requirement.requirement_category,
                "type": requirement.requirement_type,
                "source_excerpt": requirement.source_excerpt,
                "user_confirmation_state": requirement.user_confirmation_state,
                "evidence": _evidence_for_requirement(db, requirement),
            }
        )
    return requirements


def _preparation_checklist(interview: Interview, requirements: list[dict[str, Any]], story_count: int, question_count: int, mock_count: int) -> list[dict[str, Any]]:
    evidence_selected = any(item.get("evidence") for item in requirements)
    missing_evidence = any(not item.get("evidence") for item in requirements)
    status_map = {
        "stage confirmed": "Completed" if interview.user_confirmed else "In progress",
        "date and format confirmed": "Completed" if interview.scheduled_at and interview.interview_format != "unknown" else "Not started",
        "job requirements reviewed": "Completed" if requirements else "Needs evidence",
        "introduction prepared": "In progress",
        "relevant evidence selected": "Completed" if evidence_selected else "Needs evidence",
        "STAR stories selected": "Completed" if story_count else "Needs evidence",
        "weak areas reviewed": "Needs evidence" if missing_evidence else "In progress",
        "questions for employer prepared": "In progress" if question_count else "Not started",
        "technical or portfolio preparation complete": "In progress" if interview.stage_type in {"technical", "portfolio", "case_study"} else "Completed",
        "practical setup checked": "Not started",
        "mock interview completed": "Completed" if mock_count else "Not started",
        "user final confirmation": "Completed" if interview.preparation_status == "Ready for interview" else "Not started",
    }
    return [{"label": item, "status": status_map[item], "optional": item == "mock interview completed"} for item in READINESS_ITEMS]


def generate_preparation_brief(db: Session, interview: Interview, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    stage = _stage_definition(interview.stage_type)
    requirements = _confirmed_requirements_payload(db, interview)
    passport = _passport_summary(db, interview.profile_id)
    questions = db.scalars(select(InterviewQuestion).where(InterviewQuestion.interview_id == interview.id)).all()
    stories = db.scalars(select(StarStory).where(StarStory.profile_id == interview.profile_id, StarStory.status == "active")).all()
    mock_count = db.scalar(select(func.count()).select_from(MockInterviewSession).where(MockInterviewSession.interview_id == interview.id, MockInterviewSession.status == "completed")) or 0
    app = db.get(JobApplication, interview.application_id) if interview.application_id else None
    analysis = db.get(JobAnalysis, interview.job_analysis_id) if interview.job_analysis_id else None
    supported_requirements = [item for item in requirements if item["evidence"]]
    missing_requirements = [item for item in requirements if not item["evidence"]]
    transferable = []
    for requirement in missing_requirements:
        skill = _normalise_skill_phrase(requirement["text"])
        for related in passport["skills"][:8]:
            if skill in related.get("skill_id", "") or skill in str(related.get("skill_label", "")).lower():
                transferable.append({"requirement": requirement["text"], "evidence": related})
    introduction = build_personal_introduction(db, interview, payload.get("language") or "en")
    sections = {
        "role_summary": {
            "confirmed_facts": [
                f"Role: {interview.role}",
                f"Organisation: {interview.organisation or 'not confirmed'}",
                f"Application status: {app.status if app else 'not linked to an application tracker record'}",
            ],
            "missing_information": [] if app or analysis else ["No application or job analysis is linked."],
        },
        "stage_purpose": {"likely_stage_expectations": [stage["purpose"]], "source": "stage_template"},
        "what_interviewer_may_evaluate": {"likely_stage_expectations": stage["evaluates"]},
        "confirmed_job_requirements": {"confirmed_facts": requirements, "missing_information": ["No confirmed requirements are available."] if not requirements else []},
        "relevant_user_evidence": {"confirmed_facts": supported_requirements[:8], "source": "Evidence Passport and requirement-evidence matches"},
        "weak_or_missing_evidence": {"missing_information": missing_requirements[:8]},
        "transferable_strengths": {"confirmed_facts": transferable[:6], "source": "Evidence Passport transferable comparison"},
        "career_narrative": {"ai_generated_suggestions": introduction["versions"], "source": "Evidence-based introduction builder"},
        "likely_questions": {"ai_generated_suggestions": [question.question_text for question in questions[:8]], "uncertainty_note": "Questions are plausible for this stage, not guaranteed."},
        "questions_for_employer": {"ai_generated_suggestions": employer_questions(interview.stage_type)},
        "risk_areas": {
            "missing_information": [item["text"] for item in missing_requirements[:6]],
            "source_and_uncertainty_notes": ["Do not present unsupported claims as confirmed experience.", "Do not infer employer intentions from the job ad."],
        },
        "practical_preparation_checklist": {"confirmed_facts": _preparation_checklist(interview, requirements, len(stories), len(questions), mock_count)},
        "day_of_interview_checklist": {
            "ai_generated_suggestions": [
                "Confirm time zone, platform link, and backup contact method.",
                "Keep evidence-linked notes available, but answer naturally.",
                "Prepare one concise question about next steps.",
            ]
        },
        "source_and_uncertainty_notes": {
            "confirmed_facts": ["Application Tracker", "Job Analysis", "Evidence Passport", "CV Evidence Lock"],
            "likely_stage_expectations": ["Stage templates are deterministic guidance."],
            "user_assumptions": _limited_list(payload.get("user_assumptions"), 8),
            "missing_information": ["Participant names are optional and not required."] if not interview.participants_json else [],
        },
    }
    brief = db.scalar(select(InterviewPreparationBrief).where(InterviewPreparationBrief.interview_id == interview.id).order_by(InterviewPreparationBrief.updated_at.desc()))
    if not brief:
        brief = InterviewPreparationBrief(
            interview_id=interview.id,
            profile_id=interview.profile_id,
            application_id=interview.application_id,
            job_analysis_id=interview.job_analysis_id,
            demo_marker=interview.demo_marker,
        )
    brief.sections_json = sections
    brief.readiness_checklist_json = sections["practical_preparation_checklist"]["confirmed_facts"]
    brief.source_notes_json = sections["source_and_uncertainty_notes"]["confirmed_facts"]
    brief.language = payload.get("language") or brief.language or "en"
    brief.status = "ready_for_review"
    brief.user_confirmed = bool(payload.get("user_confirmed", False))
    brief.updated_at = _now()
    interview.preparation_status = "Needs evidence" if missing_requirements else "Ready for practice"
    interview.updated_at = _now()
    db.add(brief)
    db.add(interview)
    if interview.application_id:
        db.add(
            JobApplicationEvent(
                application_id=interview.application_id,
                profile_id=interview.profile_id,
                event_type="preparation_started",
                from_status=app.status if app else "",
                to_status=app.status if app else "",
                description="Interview preparation brief generated. Application status was not changed automatically.",
                event_metadata_json={"interview_id": interview.id, "brief_id": brief.id},
            )
        )
    db.commit()
    return preparation_public(brief)


def preparation_public(row: InterviewPreparationBrief) -> dict[str, Any]:
    return {
        "id": row.id,
        "interview_id": row.interview_id,
        "profile_id": row.profile_id,
        "application_id": row.application_id,
        "job_analysis_id": row.job_analysis_id,
        "sections": row.sections_json or {},
        "readiness_checklist": row.readiness_checklist_json or [],
        "source_notes": row.source_notes_json or [],
        "language": row.language,
        "status": row.status,
        "source": row.source,
        "user_confirmed": row.user_confirmed,
        "deterministic_origin": row.deterministic_origin,
        "demo_marker": row.demo_marker,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def get_preparation_brief(db: Session, interview: Interview) -> dict[str, Any] | None:
    row = db.scalar(select(InterviewPreparationBrief).where(InterviewPreparationBrief.interview_id == interview.id).order_by(InterviewPreparationBrief.updated_at.desc()))
    if not row:
        return None
    return preparation_public(row)


def employer_questions(stage_type: str) -> list[dict[str, Any]]:
    base = [
        {"category": "role expectations", "question": "What would success look like in the first 90 days?", "flag": "stage-appropriate"},
        {"category": "team", "question": "Which teams or stakeholders would this role work with most often?", "flag": "stage-appropriate"},
        {"category": "next steps", "question": "What are the next steps in the process after this conversation?", "flag": "stage-appropriate"},
    ]
    if stage_type in {"technical", "case_study", "portfolio"}:
        base.append({"category": "product or technical challenges", "question": "Which technical or product constraints are most important for this role right now?", "flag": "stage-appropriate"})
        base.append({"category": "AI governance", "question": "How does the team review AI-related decisions for quality, privacy, and user impact?", "flag": "role-specific if AI is part of the job analysis"})
    if stage_type in {"offer_discussion", "salary_negotiation"}:
        base.append({"category": "offer components", "question": "Could you confirm the full offer package and review timeline in writing?", "flag": "stage-appropriate"})
    return base


def build_personal_introduction(db: Session, interview: Interview, language: str = "en") -> dict[str, Any]:
    language = language if language in {"en", "nb", "ro"} else "en"
    passport = _passport_summary(db, interview.profile_id)
    top_skills = [skill for skill in passport["skills"] if skill.get("evidence_sources")][:4]
    role_phrase = interview.role or "this role"
    evidence_bits = []
    for skill in top_skills[:2]:
        evidence = (skill.get("evidence_sources") or [{}])[0]
        label = evidence.get("title") or skill.get("skill_label")
        evidence_bits.append(f"{skill.get('skill_label')} through {label}")
    if not evidence_bits:
        evidence_bits.append("evidence currently marked for user review")
    if language == "nb":
        opening = f"Jeg arbeider med {', '.join(item.get('skill_label', '') for item in top_skills[:2]) or 'tverrfaglig problemlosning'} og forbereder meg pa {role_phrase}."
    elif language == "ro":
        opening = f"Lucrez la intersectia dintre design, tehnologie si invatare, cu dovezi revizuibile pentru {role_phrase}."
    else:
        opening = f"I work at the intersection of design, technology, and learning, and I am preparing for {role_phrase} with reviewable evidence."
    versions = [
        {
            "duration": "30 seconds",
            "text": f"{opening} My strongest relevant evidence is {evidence_bits[0]}. I am interested in this role because it connects confirmed strengths with practical contribution.",
            "claim_status": "Partially supported" if top_skills else "Unverified",
        },
        {
            "duration": "60 seconds",
            "text": f"{opening} The most relevant evidence I would discuss is {', '.join(evidence_bits[:2])}. I would also be explicit about current gaps and where I am building stronger proof.",
            "claim_status": "Partially supported" if top_skills else "Unverified",
        },
        {
            "duration": "2 minutes",
            "text": f"{opening} I would frame my transition around evidence, practical projects, and responsible use of AI. I can connect my examples to the role requirements while separating confirmed experience from transferable strengths.",
            "claim_status": "Transferable",
        },
    ]
    return {
        "interview_id": interview.id,
        "language": language,
        "versions": versions,
        "editable": True,
        "evidence_links": [{"skill_id": item.get("skill_id"), "evidence": item.get("evidence_sources", [])[:2]} for item in top_skills],
        "supported_languages": ["en", "nb", "ro"],
        "evidence_lock_required": True,
    }


def _base_questions(stage_type: str) -> list[dict[str, str]]:
    stage = _stage_definition(stage_type)
    questions = [
        {
            "category": "introduction",
            "text": "Could you introduce yourself and highlight the evidence most relevant to this role?",
            "why": f"This question is plausible for this interview stage because {stage['label']} commonly starts by verifying fit and context.",
            "objective": "Give a concise, evidence-linked introduction without unsupported claims.",
            "risk": "medium",
            "difficulty": "moderate",
        },
        {
            "category": "motivation",
            "text": "What interests you in this role based on the confirmed job description?",
            "why": "This question is plausible because interviewers often check whether motivation is role-specific without assuming hidden company facts.",
            "objective": "Connect motivation to confirmed role responsibilities and user-confirmed career direction.",
            "risk": "medium",
            "difficulty": "moderate",
        },
    ]
    if stage_type == "recruiter_screening":
        questions.extend(
            [
                {
                    "category": "salary",
                    "text": "What salary range or compensation priorities would you like to discuss, if you have chosen to share them?",
                    "why": "This question is plausible for recruiter screening because logistics and salary expectations may be covered early.",
                    "objective": "State user-confirmed priorities or say that the range depends on the full role and package.",
                    "risk": "high",
                    "difficulty": "moderate",
                },
                {
                    "category": "career-transition explanation",
                    "text": "How would you explain your transition into this type of role?",
                    "why": "This question is plausible because the application context may include transferable experience.",
                    "objective": "Frame the transition through evidence, learning, and relevant projects.",
                    "risk": "medium",
                    "difficulty": "moderate",
                },
            ]
        )
    if stage_type == "behavioural":
        questions.extend(
            [
                {
                    "category": "behavioural",
                    "text": "Tell me about a time you handled ambiguity or unclear requirements.",
                    "why": "This question is plausible for behavioural interviews because it can reveal structure, judgement, and reflection.",
                    "objective": "Use a STAR story with clear personal contribution and result evidence.",
                    "risk": "medium",
                    "difficulty": "moderate",
                },
                {
                    "category": "behavioural",
                    "text": "Tell me about a time you received difficult feedback and what changed afterward.",
                    "why": "This question is plausible for behavioural interviews because feedback and learning are common evaluation areas.",
                    "objective": "Show learning without over-claiming impact.",
                    "risk": "medium",
                    "difficulty": "moderate",
                },
            ]
        )
    if stage_type == "technical":
        questions.extend(
            [
                {
                    "category": "technical",
                    "text": "How would you explain one technical decision from a relevant project, including trade-offs and limitations?",
                    "why": "This question is plausible for technical interviews because interviewers may verify demonstrated project evidence.",
                    "objective": "Explain architecture, testing, limitations, and what evidence supports the work.",
                    "risk": "high",
                    "difficulty": "advanced",
                },
                {
                    "category": "technical",
                    "text": "How do you approach debugging or failure handling in a system like the one described in the job analysis?",
                    "why": "This question is plausible when the job analysis includes software, API, data, or deployment requirements.",
                    "objective": "Use confirmed stack requirements and avoid unrelated advanced topics.",
                    "risk": "medium",
                    "difficulty": "moderate",
                },
            ]
        )
    if stage_type == "case_study":
        questions.append(
            {
                "category": "case",
                "text": "How would you improve an existing digital service while making assumptions explicit?",
                "why": "This question is plausible for case interviews because it evaluates framing, assumptions, options, risks, and success indicators.",
                "objective": "Ask clarifying questions, define users and constraints, propose options, and state trade-offs.",
                "risk": "medium",
                "difficulty": "moderate",
            }
        )
    if stage_type == "portfolio":
        questions.append(
            {
                "category": "portfolio",
                "text": "Which project would you present first for this role, and what evidence supports your contribution?",
                "why": "This question is plausible for portfolio interviews because project selection and ownership need verification.",
                "objective": "Select a relevant project, state context, decisions, result, limitations, and lessons.",
                "risk": "medium",
                "difficulty": "moderate",
            }
        )
    if stage_type in {"offer_discussion", "salary_negotiation"}:
        questions.append(
            {
                "category": "candidate questions",
                "text": "Which offer components matter most to you, and what information is still missing?",
                "why": "This question is plausible for offer stages because decisions depend on the full package, not salary alone.",
                "objective": "Separate confirmed offer facts, priorities, questions, and unresolved risks.",
                "risk": "high",
                "difficulty": "moderate",
            }
        )
    return questions


def generate_interview_questions(db: Session, interview: Interview, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    if payload.get("replace_existing"):
        db.execute(delete(InterviewAnswer).where(InterviewAnswer.interview_id == interview.id))
        db.execute(delete(InterviewQuestion).where(InterviewQuestion.interview_id == interview.id))
        db.flush()
    existing = db.scalars(select(InterviewQuestion).where(InterviewQuestion.interview_id == interview.id).order_by(InterviewQuestion.created_at)).all()
    if existing and not payload.get("force"):
        return {"interview_id": interview.id, "questions": [question_public(item) for item in existing], "generated": False}

    created: list[InterviewQuestion] = []
    requirements = _requirements(db, interview.job_analysis_id)
    for template in _base_questions(interview.stage_type):
        row = InterviewQuestion(
            interview_id=interview.id,
            profile_id=interview.profile_id,
            application_id=interview.application_id,
            job_analysis_id=interview.job_analysis_id,
            category=template["category"],
            stage=interview.stage_type,
            question_text=template["text"],
            why_it_may_be_asked=template["why"],
            answer_objective=template["objective"],
            risk_level=template["risk"],
            difficulty=template["difficulty"],
            source_type="stage_template",
            origin="deterministic",
        )
        db.add(row)
        created.append(row)
    for requirement in requirements[:8]:
        category = "technical" if interview.stage_type == "technical" or requirement.requirement_category in {"skills", "technology"} else "evidence verification"
        evidence = _evidence_for_requirement(db, requirement)
        row = InterviewQuestion(
            interview_id=interview.id,
            profile_id=interview.profile_id,
            application_id=interview.application_id,
            job_analysis_id=interview.job_analysis_id,
            category=category,
            stage=interview.stage_type,
            question_text=f"How would you demonstrate or discuss this requirement: {requirement.requirement_text}?",
            why_it_may_be_asked="This question is plausible for this interview stage because the requirement appears in the confirmed job analysis.",
            related_job_requirement_id=requirement.id,
            related_job_requirement=requirement.requirement_text,
            related_evidence_json=evidence,
            answer_objective="Link the answer to confirmed evidence, or clearly label it as transferable or still developing.",
            risk_level="high" if not evidence or requirement.requirement_type == "mandatory" else "medium",
            difficulty="advanced" if interview.stage_type == "technical" and requirement.requirement_type == "mandatory" else "moderate",
            source_type="confirmed_job_requirement",
            origin="deterministic",
        )
        db.add(row)
        created.append(row)
    if not requirements:
        row = InterviewQuestion(
            interview_id=interview.id,
            profile_id=interview.profile_id,
            application_id=interview.application_id,
            job_analysis_id=interview.job_analysis_id,
            category="role knowledge",
            stage=interview.stage_type,
            question_text="Which parts of the role are confirmed, and which parts do you still need to clarify?",
            why_it_may_be_asked="This question is plausible because no confirmed job-analysis requirements are available.",
            answer_objective="Separate confirmed facts from missing information.",
            risk_level="high",
            difficulty="moderate",
            source_type="missing_job_analysis_safeguard",
            origin="deterministic",
        )
        db.add(row)
        created.append(row)
    db.flush()
    interview.preparation_status = "In progress"
    interview.updated_at = _now()
    db.commit()
    return {"interview_id": interview.id, "questions": [question_public(item) for item in created], "generated": True}


def list_interview_questions(db: Session, interview: Interview) -> list[dict[str, Any]]:
    rows = db.scalars(select(InterviewQuestion).where(InterviewQuestion.interview_id == interview.id).order_by(InterviewQuestion.created_at)).all()
    return [question_public(item) for item in rows]


def question_public(row: InterviewQuestion) -> dict[str, Any]:
    return {
        "id": row.id,
        "interview_id": row.interview_id,
        "profile_id": row.profile_id,
        "category": row.category,
        "stage": row.stage,
        "question_text": row.question_text,
        "why_it_may_be_asked": row.why_it_may_be_asked,
        "related_job_requirement_id": row.related_job_requirement_id,
        "related_job_requirement": row.related_job_requirement,
        "related_evidence": row.related_evidence_json or [],
        "answer_objective": row.answer_objective,
        "risk_level": row.risk_level,
        "difficulty": row.difficulty,
        "source_type": row.source_type,
        "origin": row.origin,
        "saved_by_user": row.saved_by_user,
        "version": row.version,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def save_question(db: Session, question: InterviewQuestion, saved: bool = True) -> dict[str, Any]:
    question.saved_by_user = saved
    question.updated_at = _now()
    db.commit()
    return question_public(question)


def build_answer(db: Session, question: InterviewQuestion, payload: dict[str, Any]) -> dict[str, Any]:
    interview = db.get(Interview, question.interview_id)
    if not interview:
        raise LookupError("Interview not found")
    selected_evidence = _limited_list(payload.get("selected_evidence") or question.related_evidence_json, 12)
    user_draft = _clean_text(payload.get("user_draft") or "", 12000)
    linked_count = len([item for item in selected_evidence if item.get("evidence_id")]) if selected_evidence and all(isinstance(item, dict) for item in selected_evidence) else 0
    user_confirmed = bool(payload.get("user_confirmed", False))
    status, reason, safer, blocked = _claim_status_from_text(user_draft or question.question_text, linked_count=linked_count, user_confirmed=user_confirmed)
    claim = {
        "claim_text": user_draft[:800] if user_draft else "No user draft yet.",
        "status": status,
        "deterministic_reason": reason,
        "safer_alternative": safer,
        "blocked": blocked,
    }
    risk_areas = []
    if status in {"Unverified", "Blocked"}:
        risk_areas.append("The answer includes unsupported or blocked claims. Replace with evidence-linked wording.")
    if not selected_evidence:
        risk_areas.append("No evidence has been selected for this answer.")
    if _word_count(user_draft) > 220:
        risk_areas.append("The draft may be too long for a concise interview answer.")
    answer = InterviewAnswer(
        question_id=question.id,
        interview_id=interview.id,
        profile_id=question.profile_id,
        answer_objective=payload.get("answer_objective") or question.answer_objective,
        key_points_json=_limited_list(payload.get("key_points"), 12),
        selected_evidence_json=selected_evidence,
        selected_star_story_id=payload.get("selected_star_story_id"),
        suggested_structure_json=payload.get("suggested_structure") or ["Answer the question directly", "Add evidence or STAR context", "State result or limitation", "Close with relevance to the role"],
        possible_opening=payload.get("possible_opening") or "A relevant example I can discuss is...",
        possible_closing=payload.get("possible_closing") or "The main relevance for this role is...",
        risk_areas_json=risk_areas,
        unsupported_claims_json=[claim] if status in {"Unverified", "Blocked"} else [],
        claim_statuses_json=[claim],
        user_draft=user_draft,
        revised_draft=payload.get("revised_draft") or (safer if blocked else user_draft),
        final_approved_answer=payload.get("final_approved_answer") or "",
        user_confirmed=user_confirmed,
        origin="deterministic",
    )
    db.add(answer)
    db.commit()
    return answer_public(answer)


def answer_public(row: InterviewAnswer) -> dict[str, Any]:
    return {
        "id": row.id,
        "question_id": row.question_id,
        "interview_id": row.interview_id,
        "profile_id": row.profile_id,
        "answer_objective": row.answer_objective,
        "key_points": row.key_points_json or [],
        "selected_evidence": row.selected_evidence_json or [],
        "selected_star_story_id": row.selected_star_story_id,
        "suggested_structure": row.suggested_structure_json or [],
        "possible_opening": row.possible_opening,
        "possible_closing": row.possible_closing,
        "risk_areas": row.risk_areas_json or [],
        "unsupported_claims": row.unsupported_claims_json or [],
        "claim_statuses": row.claim_statuses_json or [],
        "user_draft": row.user_draft,
        "revised_draft": row.revised_draft,
        "final_approved_answer": row.final_approved_answer,
        "user_confirmed": row.user_confirmed,
        "origin": row.origin,
        "version": row.version,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def _story_snapshot(story: StarStory) -> dict[str, Any]:
    return {
        "title": story.title,
        "situation": story.situation,
        "task": story.task,
        "action": story.action,
        "result": story.result,
        "reflection": story.reflection,
        "skills_demonstrated": story.skills_demonstrated_json or [],
        "related_job_requirements": story.related_job_requirements_json or [],
        "evidence_links": story.evidence_links_json or [],
        "claim_statuses": story.claim_statuses_json or [],
        "quality_status": story.quality_status,
        "version": story.version,
    }


def create_star_story(db: Session, profile: Profile, payload: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
    story = StarStory(
        profile_id=profile.id,
        user_id=user_id or profile.user_id,
        title=_clean_text(payload.get("title") or "Untitled STAR story", 255),
        situation=_clean_text(payload.get("situation") or "", 3000),
        task=_clean_text(payload.get("task") or "", 3000),
        action=_clean_text(payload.get("action") or "", 5000),
        result=_clean_text(payload.get("result") or "", 3000),
        reflection=_clean_text(payload.get("reflection") or "", 3000),
        skills_demonstrated_json=_limited_list(payload.get("skills_demonstrated"), 20),
        related_job_requirements_json=_limited_list(payload.get("related_job_requirements"), 20),
        evidence_links_json=_limited_list(payload.get("evidence_links"), 20),
        dates_json=payload.get("dates") if isinstance(payload.get("dates"), dict) else {},
        organisation_or_context=_clean_text(payload.get("organisation_or_context") or "", 255),
        confidentiality_status=payload.get("confidentiality_status") or "review_needed",
        user_confirmed=bool(payload.get("user_confirmed", False)),
        suitable_stages_json=_limited_list(payload.get("suitable_stages"), 12),
        tags_json=[tag for tag in _limited_list(payload.get("tags"), 20) if str(tag).replace("-", "_") in STAR_CATEGORIES],
        source=payload.get("source") or "manual",
        demo_marker=_demo_for_profile(profile),
    )
    db.add(story)
    db.flush()
    quality = evaluate_star_story_row(story)
    story.quality_status = quality["status"]
    story.quality_json = quality
    story.claim_statuses_json = quality["claim_statuses"]
    story.last_reviewed_at = _now()
    db.add(StarStoryVersion(story_id=story.id, profile_id=profile.id, version_number=1, snapshot_json=_story_snapshot(story), change_reason="Initial STAR story."))
    db.commit()
    return star_story_public(story)


def update_star_story(db: Session, story: StarStory, payload: dict[str, Any]) -> dict[str, Any]:
    for key, limit in [("title", 255), ("situation", 3000), ("task", 3000), ("action", 5000), ("result", 3000), ("reflection", 3000), ("organisation_or_context", 255), ("confidentiality_status", 80)]:
        if key in payload and payload[key] is not None:
            setattr(story, key, _clean_text(str(payload[key]), limit))
    for source, target in [
        ("skills_demonstrated", "skills_demonstrated_json"),
        ("related_job_requirements", "related_job_requirements_json"),
        ("evidence_links", "evidence_links_json"),
        ("suitable_stages", "suitable_stages_json"),
        ("tags", "tags_json"),
    ]:
        if source in payload:
            setattr(story, target, _limited_list(payload.get(source), 20))
    if "dates" in payload and isinstance(payload["dates"], dict):
        story.dates_json = payload["dates"]
    if "user_confirmed" in payload:
        story.user_confirmed = bool(payload["user_confirmed"])
    if payload.get("archive"):
        story.status = "archived"
    story.version += 1
    story.updated_at = _now()
    quality = evaluate_star_story_row(story)
    story.quality_status = quality["status"]
    story.quality_json = quality
    story.claim_statuses_json = quality["claim_statuses"]
    story.last_reviewed_at = _now()
    db.add(StarStoryVersion(story_id=story.id, profile_id=story.profile_id, version_number=story.version, snapshot_json=_story_snapshot(story), change_reason=payload.get("change_reason") or "Story updated."))
    db.commit()
    return star_story_public(story)


def delete_star_story(db: Session, story: StarStory) -> dict[str, Any]:
    story.status = "archived"
    story.updated_at = _now()
    db.commit()
    return {"status": "archived", "id": story.id}


def list_star_stories(db: Session, profile_id: str, include_archived: bool = False) -> list[dict[str, Any]]:
    query = select(StarStory).where(StarStory.profile_id == profile_id)
    if not include_archived:
        query = query.where(StarStory.status == "active")
    rows = db.scalars(query.order_by(StarStory.updated_at.desc())).all()
    return [star_story_public(item) for item in rows]


def evaluate_star_story_row(story: StarStory) -> dict[str, Any]:
    checks = []
    scores = {
        "situation clarity": 4 if _word_count(story.situation) >= 8 else 1 if story.situation else 0,
        "task ownership": 4 if re.search(r"\b(I|my|me)\b", story.task, re.I) else 2 if story.task else 0,
        "action specificity": 4 if _word_count(story.action) >= 18 and re.search(r"\b(I|my|designed|built|created|tested|led|coordinated|analysed|analyzed)\b", story.action, re.I) else 2 if story.action else 0,
        "user contribution": 4 if re.search(r"\bI\b", story.action) else 1,
        "result evidence": 4 if story.evidence_links_json and story.result else 2 if story.result else 0,
        "relevance": 4 if story.skills_demonstrated_json or story.related_job_requirements_json else 2,
        "conciseness": 4 if _word_count(" ".join([story.situation, story.task, story.action, story.result, story.reflection])) <= 260 else 1,
        "reflection": 4 if _word_count(story.reflection) >= 8 else 1 if story.reflection else 0,
        "confidentiality safety": 4 if story.confidentiality_status in {"public", "anonymised", "safe"} else 1,
    }
    metric_claim = bool(re.search(r"\b\d{1,3}\s?%|\b\d+x\b|\bincreased|reduced|saved|revenue|profit\b", story.result, re.I))
    unsupported = metric_claim and not story.evidence_links_json and not story.user_confirmed
    if unsupported:
        checks.append("Contains unsupported claims")
    if story.confidentiality_status not in {"public", "anonymised", "safe"}:
        checks.append("Confidentiality review required")
    if scores["action specificity"] < 3:
        checks.append("Needs clearer action")
    if scores["result evidence"] < 3:
        checks.append("Needs stronger result evidence")
    if scores["conciseness"] < 3:
        checks.append("Too long")
    if not checks:
        checks.append("Ready")
    status = checks[0]
    claim_statuses = []
    for claim_text in [story.situation, story.task, story.action, story.result]:
        if not claim_text:
            continue
        claim_statuses.append(
            {
                "claim_text": claim_text[:500],
                "status": "Supported" if story.evidence_links_json else "User-confirmed" if story.user_confirmed else "Unverified",
                "unsupported_metric": unsupported and claim_text == story.result,
            }
        )
    if unsupported:
        claim_statuses.append(
            {
                "claim_text": story.result[:500],
                "status": "Blocked",
                "safer_alternative": "Reduced manual steps and improved workflow consistency.",
                "deterministic_reason": "Estimated result metrics need linked evidence or explicit user confirmation.",
            }
        )
    return {"status": status, "labels": checks, "criteria": scores, "claim_statuses": claim_statuses, "deterministic_version": "star-story-quality-v1"}


def evaluate_star_story(db: Session, story: StarStory) -> dict[str, Any]:
    quality = evaluate_star_story_row(story)
    story.quality_status = quality["status"]
    story.quality_json = quality
    story.claim_statuses_json = quality["claim_statuses"]
    story.last_reviewed_at = _now()
    db.commit()
    return star_story_public(story)


def star_story_public(row: StarStory) -> dict[str, Any]:
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "title": row.title,
        "situation": row.situation,
        "task": row.task,
        "action": row.action,
        "result": row.result,
        "reflection": row.reflection,
        "skills_demonstrated": row.skills_demonstrated_json or [],
        "related_job_requirements": row.related_job_requirements_json or [],
        "evidence_links": row.evidence_links_json or [],
        "dates": row.dates_json or {},
        "organisation_or_context": row.organisation_or_context,
        "confidentiality_status": row.confidentiality_status,
        "user_confirmed": row.user_confirmed,
        "claim_statuses": row.claim_statuses_json or [],
        "suitable_stages": row.suitable_stages_json or [],
        "tags": row.tags_json or [],
        "quality_status": row.quality_status,
        "quality": row.quality_json or {},
        "source": row.source,
        "status": row.status,
        "demo_marker": row.demo_marker,
        "version": row.version,
        "last_reviewed_at": row.last_reviewed_at.isoformat() if row.last_reviewed_at else None,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def create_mock_session(db: Session, interview: Interview, payload: dict[str, Any]) -> dict[str, Any]:
    delivery = payload.get("delivery_mode") or payload.get("mode_type") or "text"
    if delivery not in {"text", "voice"}:
        raise ValueError("Mock interview delivery mode must be text or voice.")
    if delivery == "voice" and not get_settings().interview_voice_enabled:
        delivery = "text"
        fallback = "Voice is disabled; text mock interview remains available."
    else:
        fallback = ""
    mode = payload.get("mode") or "guided_practice"
    session = MockInterviewSession(
        interview_id=interview.id,
        profile_id=interview.profile_id,
        application_id=interview.application_id,
        mode=mode,
        delivery_mode=delivery,
        persona=payload.get("persona") or _persona_for_stage(interview.stage_type),
        status="created",
        timing_enabled=bool(payload.get("timing_enabled", True)),
        source="deterministic",
        demo_marker=interview.demo_marker,
        feedback_json={"voice_fallback": fallback} if fallback else {},
    )
    db.add(session)
    interview.mock_session_status = "Created"
    interview.updated_at = _now()
    db.commit()
    return mock_session_public(db, session)


def _persona_for_stage(stage_type: str) -> str:
    return {
        "recruiter_screening": "recruiter",
        "hiring_manager": "hiring_manager",
        "technical": "technical_lead",
        "portfolio": "design_lead",
        "case_study": "product_manager",
        "panel": "panel",
    }.get(stage_type, "unknown_interviewer")


def start_mock_session(db: Session, session: MockInterviewSession) -> dict[str, Any]:
    interview = db.get(Interview, session.interview_id)
    if not interview:
        raise LookupError("Interview not found")
    questions = db.scalars(select(InterviewQuestion).where(InterviewQuestion.interview_id == interview.id).order_by(InterviewQuestion.created_at)).all()
    if not questions:
        generate_interview_questions(db, interview)
        questions = db.scalars(select(InterviewQuestion).where(InterviewQuestion.interview_id == interview.id).order_by(InterviewQuestion.created_at)).all()
    session.question_sequence_json = [item.id for item in questions[:8 if session.mode == "full_simulation" else 5]]
    session.status = "in_progress"
    session.started_at = _now()
    session.updated_at = _now()
    interview.mock_session_status = "In progress"
    db.commit()
    return mock_session_public(db, session)


def add_mock_turn(db: Session, session: MockInterviewSession, payload: dict[str, Any]) -> dict[str, Any]:
    question = db.get(InterviewQuestion, payload.get("question_id")) if payload.get("question_id") else None
    if question and question.interview_id != session.interview_id:
        raise PermissionError("Question does not belong to this mock interview.")
    existing_count = db.scalar(select(func.count()).select_from(MockInterviewTurn).where(MockInterviewTurn.session_id == session.id)) or 0
    answer_text = _clean_text(payload.get("answer_text") or payload.get("transcript") or "", 12000)
    turn = MockInterviewTurn(
        session_id=session.id,
        interview_id=session.interview_id,
        profile_id=session.profile_id,
        question_id=question.id if question else None,
        turn_index=int(existing_count) + 1,
        question_text=question.question_text if question else _clean_text(payload.get("question_text") or "", 2000),
        answer_text=answer_text,
        corrected_transcript=_clean_text(payload.get("corrected_transcript") or answer_text, 12000),
        response_duration_seconds=payload.get("response_duration_seconds"),
        estimated_word_count=_word_count(answer_text),
        attempt_number=int(payload.get("attempt_number") or 1),
        completion_status=payload.get("completion_status") or "answered",
    )
    rubric = score_answer(question.question_text if question else turn.question_text, answer_text, payload.get("response_duration_seconds"))
    turn.rubric_json = rubric["rubric"]
    turn.follow_up_questions_json = generate_follow_ups(answer_text, rubric["rubric"])
    turn.feedback_json = rubric["feedback"]
    db.add(turn)
    session.updated_at = _now()
    db.commit()
    return mock_turn_public(turn)


def generate_follow_ups(answer_text: str, rubric: list[dict[str, Any]]) -> list[str]:
    lower = answer_text.lower()
    follow_ups = []
    if not re.search(r"\bI\b", answer_text):
        follow_ups.append("What part of this work was specifically your responsibility?")
    if not any(word in lower for word in ["verified", "tested", "measured", "evidence", "confirmed"]):
        follow_ups.append("What evidence supports that result?")
    if not any(word in lower for word in ["trade-off", "tradeoff", "constraint", "risk", "limitation"]):
        follow_ups.append("What trade-off or constraint did you manage?")
    if not any(word in lower for word in ["learned", "differently", "reflect", "improve"]):
        follow_ups.append("What would you do differently now?")
    weak = [item for item in rubric if item["score"] <= 1]
    if weak and len(follow_ups) < 3:
        follow_ups.append("Could you add the missing detail without introducing new facts?")
    return follow_ups[:3]


def score_answer(question_text: str, answer_text: str, duration_seconds: int | None = None) -> dict[str, Any]:
    lower_question = question_text.lower()
    lower_answer = answer_text.lower()
    words = _word_count(answer_text)
    answered = 3 if words >= 20 else 1 if words else 0
    evidence = 4 if any(word in lower_answer for word in ["evidence", "project", "portfolio", "tested", "verified", "confirmed"]) else 2 if words >= 50 else 0
    contribution = 4 if re.search(r"\bI\b", answer_text) else 1 if words else 0
    context = 4 if any(word in lower_answer for word in ["context", "situation", "role", "problem", "user"]) else 2 if words >= 40 else 0
    actions = 4 if any(word in lower_answer for word in ["designed", "built", "created", "tested", "analysed", "analyzed", "coordinated", "decided"]) else 1 if words else 0
    result = 4 if any(word in lower_answer for word in ["result", "outcome", "reduced", "improved", "learned", "validated"]) else 1 if words else 0
    unsupported_status, _, _, blocked = _claim_status_from_text(answer_text, linked_count=1 if evidence >= 3 else 0)
    unsupported_score = 0 if blocked else 4 if unsupported_status != "Unverified" else 2
    timing_score = 3
    if duration_seconds is not None:
        if duration_seconds <= 0:
            timing_score = 0
        elif duration_seconds < 25 and words < 35:
            timing_score = 2
        elif duration_seconds > 240 or words > 420:
            timing_score = 2
        else:
            timing_score = 4
    language = 4 if words and len(answer_text.split(".")) >= 2 else 2 if words else 0
    reflection = 4 if any(word in lower_answer for word in ["learned", "reflect", "differently", "improve"]) else 2 if "behaviour" not in lower_question and "behavior" not in lower_question else 0
    rubric = [
        {"criterion": "answered the actual question", "score": answered},
        {"criterion": "used relevant evidence", "score": evidence},
        {"criterion": "explained personal contribution", "score": contribution},
        {"criterion": "provided sufficient context", "score": context},
        {"criterion": "described actions", "score": actions},
        {"criterion": "described result", "score": result},
        {"criterion": "avoided unsupported claims", "score": unsupported_score},
        {"criterion": "stayed within suggested time", "score": timing_score},
        {"criterion": "used understandable language", "score": language},
        {"criterion": "included reflection where appropriate", "score": reflection},
    ]
    strengths = [item["criterion"] for item in rubric if item["score"] >= 3][:4]
    needs = [item["criterion"] for item in rubric if item["score"] <= 2][:4]
    return {
        "rubric": rubric,
        "feedback": {
            "strengths": strengths,
            "needs_improvement": needs,
            "unsupported_or_unclear_claims": [answer_text[:300]] if blocked or unsupported_status == "Unverified" else [],
            "missing_evidence": [] if evidence >= 3 else ["Add one evidence-linked project, experiment, or confirmed experience."],
            "suggested_next_practice": "Repeat the answer with clearer evidence and personal contribution." if needs else "Practise a concise follow-up answer.",
            "user_reflection": "",
            "no_single_opaque_score": True,
        },
    }


def complete_mock_session(db: Session, session: MockInterviewSession, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    turns = db.scalars(select(MockInterviewTurn).where(MockInterviewTurn.session_id == session.id).order_by(MockInterviewTurn.turn_index)).all()
    rubric_rows = [item for turn in turns for item in (turn.rubric_json or [])]
    criteria = {}
    for row in rubric_rows:
        criteria.setdefault(row["criterion"], []).append(row["score"])
    aggregate = [{"criterion": criterion, "average_score": round(sum(scores) / len(scores), 2), "attempts": len(scores)} for criterion, scores in criteria.items()]
    feedback = {
        "strengths": [item["criterion"] for item in aggregate if item["average_score"] >= 3][:5],
        "needs_improvement": [item["criterion"] for item in aggregate if item["average_score"] < 3][:5],
        "unsupported_or_unclear_claims": [claim for turn in turns for claim in (turn.feedback_json or {}).get("unsupported_or_unclear_claims", [])][:5],
        "missing_evidence": [claim for turn in turns for claim in (turn.feedback_json or {}).get("missing_evidence", [])][:5],
        "suggested_next_practice": "Practise the lowest-scoring answer criterion next.",
        "user_reflection": payload.get("user_reflection") or "",
        "no_single_opaque_score": True,
    }
    session.status = "completed"
    session.completed_at = _now()
    session.transcript_confirmed = bool(payload.get("transcript_confirmed", False))
    session.transcript_retained = bool(payload.get("transcript_retained", False))
    session.rubric_results_json = aggregate
    session.feedback_json = feedback
    session.updated_at = _now()
    interview = db.get(Interview, session.interview_id)
    if interview:
        interview.mock_session_status = "Completed"
        interview.updated_at = _now()
        if interview.application_id:
            app = db.get(JobApplication, interview.application_id)
            db.add(
                JobApplicationEvent(
                    application_id=interview.application_id,
                    profile_id=interview.profile_id,
                    event_type="mock_interview_completed",
                    from_status=app.status if app else "",
                    to_status=app.status if app else "",
                    description="Mock interview completed. Application status was not changed automatically.",
                    event_metadata_json={"mock_session_id": session.id, "interview_id": interview.id},
                )
            )
    db.commit()
    return mock_session_public(db, session)


def get_mock_feedback(db: Session, session: MockInterviewSession) -> dict[str, Any]:
    if not session.feedback_json:
        complete_mock_session(db, session)
    return mock_session_public(db, session)["feedback"]


def delete_mock_session(db: Session, session: MockInterviewSession) -> dict[str, Any]:
    db.execute(delete(MockInterviewTurn).where(MockInterviewTurn.session_id == session.id))
    db.execute(delete(VoiceProviderSession).where(VoiceProviderSession.mock_session_id == session.id))
    db.delete(session)
    db.commit()
    return {"status": "deleted", "id": session.id, "transcript_deleted": True, "raw_audio_deleted": True}


def list_mock_sessions(db: Session, interview: Interview) -> list[dict[str, Any]]:
    rows = db.scalars(select(MockInterviewSession).where(MockInterviewSession.interview_id == interview.id).order_by(MockInterviewSession.updated_at.desc())).all()
    return [mock_session_public(db, item) for item in rows]


def mock_session_public(db: Session, row: MockInterviewSession) -> dict[str, Any]:
    turns = db.scalars(select(MockInterviewTurn).where(MockInterviewTurn.session_id == row.id).order_by(MockInterviewTurn.turn_index)).all()
    return {
        "id": row.id,
        "interview_id": row.interview_id,
        "profile_id": row.profile_id,
        "application_id": row.application_id,
        "mode": row.mode,
        "delivery_mode": row.delivery_mode,
        "persona": row.persona,
        "status": row.status,
        "question_sequence": row.question_sequence_json or [],
        "transcript_confirmed": row.transcript_confirmed,
        "transcript_retained": row.transcript_retained,
        "timing_enabled": row.timing_enabled,
        "rubric_results": row.rubric_results_json or [],
        "feedback": row.feedback_json or {},
        "turns": [mock_turn_public(item) for item in turns],
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "completed_at": row.completed_at.isoformat() if row.completed_at else None,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def mock_turn_public(row: MockInterviewTurn) -> dict[str, Any]:
    return {
        "id": row.id,
        "session_id": row.session_id,
        "interview_id": row.interview_id,
        "profile_id": row.profile_id,
        "question_id": row.question_id,
        "turn_index": row.turn_index,
        "question_text": row.question_text,
        "answer_text": row.answer_text,
        "corrected_transcript": row.corrected_transcript,
        "response_duration_seconds": row.response_duration_seconds,
        "estimated_word_count": row.estimated_word_count,
        "attempt_number": row.attempt_number,
        "completion_status": row.completion_status,
        "follow_up_questions": row.follow_up_questions_json or [],
        "rubric": row.rubric_json or [],
        "feedback": row.feedback_json or {},
        "created_at": row.created_at.isoformat(),
    }


def interview_voice_status() -> dict[str, Any]:
    settings = get_settings()
    return {
        "enabled": settings.interview_voice_enabled,
        "provider": settings.interview_voice_provider,
        "configured": bool(settings.elevenlabs_api_key) if settings.interview_voice_provider == "elevenlabs" else False,
        "default_language": settings.interview_voice_default_language,
        "session_timeout_seconds": settings.interview_voice_session_timeout_seconds,
        "max_session_minutes": settings.interview_voice_max_session_minutes,
        "transcript_retention_enabled": settings.interview_voice_transcript_retention_enabled,
        "raw_audio_retention_enabled": False,
        "text_mode_available": True,
        "status": "ready" if settings.interview_voice_enabled and settings.elevenlabs_api_key else "disabled",
        "privacy_notes": [
            "Provider credentials remain backend-only.",
            "Raw audio is not permanently stored by default.",
            "Transcript persistence requires user confirmation.",
            "Voice is not used for biometric identification, emotion detection, or protected-attribute inference.",
        ],
    }


def create_voice_session(db: Session, profile: Profile, payload: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    mock_session = db.get(MockInterviewSession, payload.get("mock_session_id")) if payload.get("mock_session_id") else None
    interview = db.get(Interview, payload.get("interview_id")) if payload.get("interview_id") else (db.get(Interview, mock_session.interview_id) if mock_session else None)
    if interview and interview.profile_id != profile.id:
        raise PermissionError("Interview does not belong to this profile")
    if mock_session and mock_session.profile_id != profile.id:
        raise PermissionError("Mock session does not belong to this profile")
    if not payload.get("microphone_consent"):
        raise ValueError("Microphone consent is required before starting a voice session.")
    status = interview_voice_status()
    row = VoiceProviderSession(
        mock_session_id=mock_session.id if mock_session else None,
        interview_id=interview.id if interview else None,
        profile_id=profile.id,
        provider=settings.interview_voice_provider,
        provider_session_id="" if not status["enabled"] else f"local-{profile.id}-{int(_now().timestamp())}",
        status="disabled_fallback" if not status["enabled"] else "created",
        language=payload.get("language") or settings.interview_voice_default_language,
        consent_confirmed=True,
        audio_retained=False,
        transcript_retained=bool(payload.get("transcript_retained", False) and settings.interview_voice_transcript_retention_enabled),
        metadata_json={"text_mode_available": True, "provider_status": status["status"]},
        expires_at=_now() + timedelta(seconds=settings.interview_voice_session_timeout_seconds),
    )
    db.add(row)
    db.commit()
    return voice_session_public(row)


def complete_voice_session(db: Session, row: VoiceProviderSession, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    settings = get_settings()
    row.status = "completed"
    row.transcript_retained = bool(payload.get("transcript_retained", row.transcript_retained) and settings.interview_voice_transcript_retention_enabled)
    row.updated_at = _now()
    db.commit()
    return voice_session_public(row)


def delete_voice_session(db: Session, row: VoiceProviderSession) -> dict[str, Any]:
    row.status = "deleted"
    row.provider_session_id = ""
    row.transcript_retained = False
    row.audio_retained = False
    row.updated_at = _now()
    db.commit()
    return {"status": "deleted", "id": row.id, "transcript_deleted": True, "raw_audio_deleted": True}


def voice_session_public(row: VoiceProviderSession) -> dict[str, Any]:
    return {
        "id": row.id,
        "mock_session_id": row.mock_session_id,
        "interview_id": row.interview_id,
        "profile_id": row.profile_id,
        "provider": row.provider,
        "status": row.status,
        "language": row.language,
        "consent_confirmed": row.consent_confirmed,
        "audio_retained": row.audio_retained,
        "transcript_retained": row.transcript_retained,
        "metadata": row.metadata_json or {},
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
        "provider_key_exposed": False,
    }


def create_reflection(db: Session, interview: Interview, payload: dict[str, Any]) -> dict[str, Any]:
    row = db.scalar(select(InterviewReflection).where(InterviewReflection.interview_id == interview.id).order_by(InterviewReflection.updated_at.desc()))
    if not row:
        row = InterviewReflection(interview_id=interview.id, profile_id=interview.profile_id, application_id=interview.application_id)
    row.stage_completed = _normalise_stage(payload.get("stage_completed") or interview.stage_type)
    row.completed_date = payload.get("completed_date") or payload.get("date")
    row.participants_json = _limited_list(payload.get("participants"), 12)
    row.questions_remembered_json = _limited_list(payload.get("questions_remembered"), 30)
    row.strong_answers_json = _limited_list(payload.get("strong_answers"), 20)
    row.weak_answers_json = _limited_list(payload.get("weak_answers"), 20)
    row.unexpected_topics_json = _limited_list(payload.get("unexpected_topics"), 20)
    row.confirmed_interviewer_feedback = _clean_text(payload.get("confirmed_interviewer_feedback") or "", 5000)
    row.user_interpretation = _clean_text(payload.get("user_interpretation") or "", 5000)
    row.ai_interpretation_json = {
        "note": "AI interpretation is separated from confirmed interviewer feedback and must not infer rejection reasons.",
        "possible_preparation_updates": _reflection_suggestions(payload),
    }
    row.next_step = payload.get("next_step") or "unknown"
    row.follow_up_deadline = payload.get("follow_up_deadline")
    row.confidence_before = payload.get("confidence_before")
    row.confidence_after = payload.get("confidence_after")
    row.additional_evidence_needed_json = _limited_list(payload.get("additional_evidence_needed"), 20)
    row.outcome_status = payload.get("outcome_status") or "unknown"
    row.user_confirmed = bool(payload.get("user_confirmed", False))
    row.updated_at = _now()
    interview.confidence_before = row.confidence_before if row.confidence_before is not None else interview.confidence_before
    interview.confidence_after = row.confidence_after if row.confidence_after is not None else interview.confidence_after
    interview.interview_result = row.outcome_status
    interview.updated_at = _now()
    db.add(row)
    app = db.get(JobApplication, interview.application_id) if interview.application_id else None
    if app:
        db.add(
            JobApplicationEvent(
                application_id=app.id,
                profile_id=interview.profile_id,
                event_type="interview_completed",
                from_status=app.status,
                to_status=app.status,
                description="Post-interview reflection recorded. Application status was not changed automatically.",
                event_metadata_json={"interview_id": interview.id, "reflection_requires_confirmation": True},
            )
        )
        if payload.get("create_recalibration", True):
            db.add(
                ApplicationRecalibrationRun(
                    application_id=app.id,
                    profile_id=interview.profile_id,
                    status="suggested",
                    observed_data_json={
                        "interview_id": interview.id,
                        "stage_completed": row.stage_completed,
                        "questions_remembered_count": len(row.questions_remembered_json or []),
                        "additional_evidence_needed_count": len(row.additional_evidence_needed_json or []),
                    },
                    user_interpretation_json={"note": row.user_interpretation},
                    ai_interpretation_json={"note": "No hiring outcome prediction is made."},
                    suggestions_json=_reflection_suggestions(payload),
                    roadmap_changes_require_confirmation=True,
                    demo_marker=interview.demo_marker,
                    version="interview-recalibration-v1",
                )
            )
    db.commit()
    return reflection_public(row)


def _reflection_suggestions(payload: dict[str, Any]) -> list[dict[str, Any]]:
    suggestions = []
    if payload.get("weak_answers"):
        suggestions.append({"suggestion_type": "strengthen_star_story", "label": "Strengthen one STAR story connected to a weak answer.", "requires_user_confirmation": True})
    if payload.get("additional_evidence_needed"):
        suggestions.append({"suggestion_type": "add_evidence", "label": "Add evidence for a repeated or difficult requirement.", "requires_user_confirmation": True})
    if payload.get("unexpected_topics"):
        suggestions.append({"suggestion_type": "revise_preparation", "label": "Prepare a clearer explanation for the unexpected topic before the next stage.", "requires_user_confirmation": True})
    if not suggestions:
        suggestions.append({"suggestion_type": "continue_practice", "label": "Review the preparation brief before the next application event.", "requires_user_confirmation": True})
    return suggestions


def get_reflection(db: Session, interview: Interview) -> dict[str, Any] | None:
    row = db.scalar(select(InterviewReflection).where(InterviewReflection.interview_id == interview.id).order_by(InterviewReflection.updated_at.desc()))
    if not row:
        return None
    return reflection_public(row)


def reflection_public(row: InterviewReflection) -> dict[str, Any]:
    return {
        "id": row.id,
        "interview_id": row.interview_id,
        "profile_id": row.profile_id,
        "application_id": row.application_id,
        "stage_completed": row.stage_completed,
        "completed_date": row.completed_date,
        "participants": row.participants_json or [],
        "questions_remembered": row.questions_remembered_json or [],
        "strong_answers": row.strong_answers_json or [],
        "weak_answers": row.weak_answers_json or [],
        "unexpected_topics": row.unexpected_topics_json or [],
        "confirmed_interviewer_feedback": row.confirmed_interviewer_feedback,
        "user_interpretation": row.user_interpretation,
        "ai_interpretation": row.ai_interpretation_json or {},
        "next_step": row.next_step,
        "follow_up_deadline": row.follow_up_deadline,
        "confidence_before": row.confidence_before,
        "confidence_after": row.confidence_after,
        "additional_evidence_needed": row.additional_evidence_needed_json or [],
        "outcome_status": row.outcome_status,
        "user_confirmed": row.user_confirmed,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def create_follow_up_draft(db: Session, interview: Interview, payload: dict[str, Any]) -> dict[str, Any]:
    draft_type = payload.get("draft_type") or "thank_you"
    if draft_type not in FOLLOW_UP_DRAFT_TYPES:
        raise ValueError("Unsupported follow-up draft type.")
    app = db.get(JobApplication, interview.application_id) if interview.application_id else None
    subject = payload.get("subject") or _draft_subject(draft_type, interview)
    body = payload.get("body") or _draft_body(draft_type, interview)
    row = InterviewFollowUpDraft(
        interview_id=interview.id,
        profile_id=interview.profile_id,
        application_id=interview.application_id,
        draft_type=draft_type,
        subject=_clean_text(subject, 255),
        body=_clean_text(body, 6000),
        source_facts_json=[
            {"label": "organisation", "value": interview.organisation},
            {"label": "role", "value": interview.role},
            {"label": "stage", "value": _stage_label(interview.stage_type)},
            {"label": "application_status", "value": app.status if app else ""},
        ],
        user_confirmed=bool(payload.get("user_confirmed", False)),
    )
    db.add(row)
    interview.follow_up_status = "Drafted"
    if app:
        db.add(
            JobApplicationEvent(
                application_id=app.id,
                profile_id=interview.profile_id,
                event_type="follow_up_draft_created",
                from_status=app.status,
                to_status=app.status,
                description="Follow-up draft created locally. No email was sent automatically.",
                event_metadata_json={"interview_id": interview.id, "draft_type": draft_type},
            )
        )
    db.commit()
    return follow_up_public(row)


def _draft_subject(draft_type: str, interview: Interview) -> str:
    if draft_type == "thank_you":
        return f"Thank you for the {_stage_label(interview.stage_type).lower()} conversation"
    if draft_type == "decision_timeline":
        return "Follow-up on decision timeline"
    if draft_type == "offer_acknowledgment":
        return "Thank you for the offer"
    return f"Follow-up regarding {interview.role}"


def _draft_body(draft_type: str, interview: Interview) -> str:
    if draft_type == "thank_you":
        return f"Thank you for speaking with me about {interview.role}. I appreciated the chance to discuss the role and will be happy to provide any additional confirmed information you need."
    if draft_type == "decision_timeline":
        return f"Thank you again for the conversation about {interview.role}. Could you share the expected decision timeline or next step when available?"
    if draft_type == "offer_acknowledgment":
        return f"Thank you for the offer for {interview.role}. I appreciate it and would like to review the full package and any written details before confirming my response."
    return f"I am following up regarding {interview.role}. Please let me know if any further confirmed information would be useful."


def list_follow_up_drafts(db: Session, interview: Interview) -> list[dict[str, Any]]:
    rows = db.scalars(select(InterviewFollowUpDraft).where(InterviewFollowUpDraft.interview_id == interview.id).order_by(InterviewFollowUpDraft.updated_at.desc())).all()
    return [follow_up_public(item) for item in rows]


def follow_up_public(row: InterviewFollowUpDraft) -> dict[str, Any]:
    return {
        "id": row.id,
        "interview_id": row.interview_id,
        "profile_id": row.profile_id,
        "application_id": row.application_id,
        "draft_type": row.draft_type,
        "subject": row.subject,
        "body": row.body,
        "source_facts": row.source_facts_json or [],
        "status": row.status,
        "user_confirmed": row.user_confirmed,
        "auto_sent": False,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def record_interview_application_event(db: Session, interview: Interview, payload: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
    if not interview.application_id:
        raise ValueError("Interview is not linked to an application.")
    event_type = payload.get("event_type")
    if event_type not in SUPPORTED_APPLICATION_EVENTS:
        raise ValueError("Unsupported interview application event.")
    app = db.get(JobApplication, interview.application_id)
    if not app or app.profile_id != interview.profile_id:
        raise PermissionError("Application does not belong to this interview profile.")
    from_status = app.status
    target_status = payload.get("target_status") or _status_for_event(event_type, interview.stage_type)
    confirmed = bool(payload.get("confirm_status_update", False))
    if confirmed and target_status in APPLICATION_STATUSES:
        app.status = target_status
        app.updated_at = _now()
    event = JobApplicationEvent(
        application_id=app.id,
        profile_id=app.profile_id,
        event_type=event_type,
        from_status=from_status,
        to_status=app.status,
        description=payload.get("description") or f"Interview event recorded: {event_type}.",
        event_metadata_json={"interview_id": interview.id, "status_update_confirmed": confirmed},
        created_by=user_id,
    )
    db.add(event)
    db.commit()
    return {"event": application_event_public(event), "application": application_public(db, app), "status_update_confirmed": confirmed}


def _status_for_event(event_type: str, stage_type: str) -> str:
    if event_type in {"interview_invitation_received", "interview_scheduled", "preparation_started", "mock_interview_completed"}:
        return _stage_status(stage_type)
    if event_type == "offer_received":
        return "Offer"
    if event_type == "rejected":
        return "Rejected"
    if event_type == "withdrawn":
        return "Withdrawn"
    return _stage_status(stage_type)


def create_offer_review(db: Session, profile: Profile, payload: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
    app = require_application(db, payload["application_id"], profile) if payload.get("application_id") else None
    interview = require_interview(db, payload["interview_id"], profile) if payload.get("interview_id") else None
    offer_items = _offer_items(payload)
    review = _offer_review(offer_items, _limited_list(payload.get("user_priorities"), 12))
    row = OfferReview(
        profile_id=profile.id,
        user_id=user_id or profile.user_id,
        application_id=app.id if app else None,
        interview_id=interview.id if interview else None,
        organisation=_clean_text(payload.get("organisation") or (app.organisation if app else interview.organisation if interview else ""), 255),
        role=_clean_text(payload.get("role") or (app.title if app else interview.role if interview else ""), 255),
        offer_items_json=offer_items,
        user_priorities_json=_limited_list(payload.get("user_priorities"), 12),
        review_json=review,
        status=payload.get("status") or "draft",
        source=payload.get("source") or "manual",
        user_confirmed=bool(payload.get("user_confirmed", False)),
        demo_marker=_demo_for_profile(profile),
    )
    db.add(row)
    db.flush()
    if app:
        db.add(
            JobApplicationEvent(
                application_id=app.id,
                profile_id=profile.id,
                event_type="offer_received",
                from_status=app.status,
                to_status=app.status,
                description="Offer review created locally. Application status was not changed automatically.",
                event_metadata_json={"offer_review_id": row.id, "requires_status_confirmation": True},
                created_by=user_id,
            )
        )
    db.commit()
    return offer_review_public(row)


def update_offer_review(db: Session, row: OfferReview, payload: dict[str, Any]) -> dict[str, Any]:
    offer_items = _offer_items({**(row.offer_items_json or {}), **payload})
    if "offer_items" in payload and isinstance(payload["offer_items"], dict):
        offer_items = _offer_items({**offer_items, **payload["offer_items"]})
    row.offer_items_json = offer_items
    if "user_priorities" in payload:
        row.user_priorities_json = _limited_list(payload.get("user_priorities"), 12)
    row.review_json = _offer_review(row.offer_items_json or {}, row.user_priorities_json or [])
    for key in ["organisation", "role", "status"]:
        if key in payload and payload[key] is not None:
            setattr(row, key, _clean_text(str(payload[key]), 255))
    if "user_confirmed" in payload:
        row.user_confirmed = bool(payload["user_confirmed"])
    row.updated_at = _now()
    db.commit()
    return offer_review_public(row)


def _offer_items(payload: dict[str, Any]) -> dict[str, Any]:
    fields = [
        "salary",
        "currency",
        "bonus",
        "pension",
        "holiday",
        "working_hours",
        "remote_hybrid_arrangement",
        "location",
        "probation",
        "start_date",
        "training_support",
        "equipment",
        "travel",
        "title",
        "other_benefits",
    ]
    source = payload.get("offer_items") if isinstance(payload.get("offer_items"), dict) else payload
    return {field: source.get(field) for field in fields if source.get(field) not in {None, ""}}


def _offer_review(offer_items: dict[str, Any], priorities: list[Any]) -> dict[str, Any]:
    missing = [field for field in ["salary", "currency", "working_hours", "remote_hybrid_arrangement", "probation", "start_date"] if not offer_items.get(field)]
    confirmed = [{"field": field, "value": value} for field, value in offer_items.items() if value not in {None, ""}]
    questions = [f"Could you confirm {field.replace('_', ' ')} in writing?" for field in missing[:6]]
    negotiation_priorities = []
    for priority in priorities:
        text = str(priority)
        if any(field in text.lower() for field in ["salary", "remote", "training", "title", "hours", "holiday"]):
            negotiation_priorities.append({"priority": text, "draft_point": f"I would like to discuss {text} as part of the full package."})
    return {
        "confirmed_offer_facts": confirmed,
        "missing_information": missing,
        "comparison_with_user_priorities": [{"priority": str(item), "matched": any(str(item).lower() in str(value).lower() for value in offer_items.values())} for item in priorities],
        "questions_to_clarify": questions,
        "negotiation_priorities": negotiation_priorities,
        "draft_negotiation_points": [item["draft_point"] for item in negotiation_priorities],
        "acceptance_considerations": ["Review the full written offer, start date, working mode, probation, and support for growth."],
        "unresolved_risks": ["No tax calculation or legal compliance assessment is provided."],
        "legal_or_financial_advice": False,
    }


def list_offer_reviews(db: Session, profile_id: str) -> list[dict[str, Any]]:
    rows = db.scalars(select(OfferReview).where(OfferReview.profile_id == profile_id).order_by(OfferReview.updated_at.desc())).all()
    return [offer_review_public(item) for item in rows]


def offer_review_public(row: OfferReview) -> dict[str, Any]:
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "application_id": row.application_id,
        "interview_id": row.interview_id,
        "organisation": row.organisation,
        "role": row.role,
        "offer_items": row.offer_items_json or {},
        "user_priorities": row.user_priorities_json or [],
        "review": row.review_json or {},
        "status": row.status,
        "source": row.source,
        "user_confirmed": row.user_confirmed,
        "demo_marker": row.demo_marker,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def case_templates() -> list[dict[str, Any]]:
    templates = [
        "improve an existing digital service",
        "introduce AI into a manual workflow",
        "design an explainable recommendation feature",
        "reduce user drop-off",
        "evaluate a RAG system",
        "improve an application process",
        "plan a new product feature",
    ]
    workflow = ["understand the problem", "ask clarifying questions", "identify users", "define constraints", "propose alternatives", "select approach", "explain trade-offs", "define risks", "define success indicators", "summarise"]
    return [{"id": re.sub(r"[^a-z0-9]+", "_", item), "title": item, "workflow": workflow, "rubric": ["problem framing", "assumptions", "trade-offs", "risks", "success indicators"]} for item in templates]


def portfolio_preparation(db: Session, profile: Profile) -> dict[str, Any]:
    passport = _passport_summary(db, profile.id)
    projects = []
    for skill in passport["skills"]:
        for evidence in skill.get("evidence_sources", [])[:2]:
            if evidence.get("type") in {"project", "portfolio", "career_experiment", "practical_project"} or "project" in str(evidence.get("title", "")).lower():
                projects.append(
                    {
                        "id": evidence.get("id"),
                        "title": evidence.get("title"),
                        "skill": skill.get("skill_label"),
                        "overview_30_seconds": f"{evidence.get('title')} demonstrates {skill.get('skill_label')} with reviewable evidence.",
                        "presentation_2_minutes": "Explain problem, context, your role, process, decisions, constraints, result, limitations, and lessons learned.",
                        "likely_questions": ["What was your specific contribution?", "What constraint mattered most?", "What would you improve?"],
                        "confidentiality_warning": "Do not disclose client or employer details unless explicitly safe.",
                    }
                )
    return {"profile_id": profile.id, "projects": projects[:12], "presentation_order": [item["id"] for item in projects[:4]], "source": "Evidence Passport"}


def delete_interview_journey_for_profiles(db: Session, profile_ids: list[str]) -> None:
    ids = [profile_id for profile_id in profile_ids if profile_id]
    if not ids:
        return
    interview_ids = db.scalars(select(Interview.id).where(Interview.profile_id.in_(ids))).all()
    story_ids = db.scalars(select(StarStory.id).where(StarStory.profile_id.in_(ids))).all()
    session_ids = db.scalars(select(MockInterviewSession.id).where(MockInterviewSession.profile_id.in_(ids))).all()
    question_ids = db.scalars(select(InterviewQuestion.id).where(InterviewQuestion.profile_id.in_(ids))).all()
    if session_ids:
        db.execute(delete(MockInterviewTurn).where(MockInterviewTurn.session_id.in_(session_ids)))
    if question_ids:
        db.execute(delete(InterviewAnswer).where(InterviewAnswer.question_id.in_(question_ids)))
    if story_ids:
        db.execute(delete(StarStoryVersion).where(StarStoryVersion.story_id.in_(story_ids)))
    for model in [
        VoiceProviderSession,
        MockInterviewSession,
        InterviewFollowUpDraft,
        InterviewReflection,
        InterviewPreparationBrief,
        InterviewQuestion,
        OfferReview,
        StarStory,
    ]:
        db.execute(delete(model).where(model.profile_id.in_(ids)))
    if interview_ids:
        db.execute(delete(Interview).where(Interview.id.in_(interview_ids)))
    db.commit()


def seed_demo_interview_journey(db: Session, profile: Profile) -> None:
    if db.scalar(select(func.count()).select_from(Interview).where(Interview.profile_id == profile.id)):
        return
    apps = db.scalars(select(JobApplication).where(JobApplication.profile_id == profile.id).order_by(JobApplication.created_at)).all()
    analysed_app = next((item for item in apps if item.job_analysis_id), apps[0] if apps else None)
    if not analysed_app:
        return
    stages = [
        ("recruiter_screening", "2026-07-25T10:00:00"),
        ("technical", "2026-07-29T14:00:00"),
        ("final", None),
    ]
    interviews = []
    for index, (stage, scheduled) in enumerate(stages, 1):
        payload = {
            "application_id": analysed_app.id,
            "stage_type": stage,
            "scheduled_at": scheduled,
            "timezone": "Europe/Bucharest",
            "location_or_platform": "Video call" if scheduled else "",
            "interview_format": "online" if scheduled else "unknown",
            "expected_duration_minutes": 30 if stage == "recruiter_screening" else 60,
            "participants": [{"role": "recruiter" if stage == "recruiter_screening" else "technical lead" if stage == "technical" else "director"}],
            "source": "demo",
            "user_confirmed": index == 1,
        }
        interviews.append(db.get(Interview, create_interview(db, profile, payload, profile.user_id)["id"]))
    story_payloads = [
        ("Explainable recommendation card", "Designed a recommendation UI with evidence, uncertainty, and correction states.", "Create a prototype for human-centred AI guidance.", "I defined user states, wrote rationale text, and reviewed limitations.", "Improved workflow consistency in the prototype.", "I would add user testing earlier.", ["ux_ui", "responsible_ai"], ["public"]),
        ("RAG evaluation checklist", "A retrieval prototype needed quality review.", "Define a practical evaluation checklist.", "I documented source relevance, uncertainty, and failure states.", "The checklist made review steps clearer.", "More automated metrics would strengthen it.", ["evaluation", "rag_fundamentals"], ["public"]),
        ("Ambiguous stakeholder request", "A design request had unclear success criteria.", "Clarify scope without blocking progress.", "I mapped assumptions and proposed two options.", "The team selected a smaller first version.", "Clarifying questions saved rework.", ["communication", "systems_thinking"], ["anonymised"]),
        ("Learning technical APIs", "A project required backend integration.", "Build enough API understanding for the prototype.", "I implemented FastAPI endpoints and tested responses.", "The feature worked locally with documented limits.", "More production deployment evidence is needed.", ["apis", "testing"], ["public"]),
        ("Deadline pressure", "A prototype deadline moved earlier.", "Prioritise the most useful user flow.", "I reduced scope and protected accessibility checks.", "The demo stayed coherent.", "I should record trade-offs sooner.", ["planning", "quality_assurance"], ["anonymised"]),
        ("Career transition narrative", "I needed to connect design experience with AI product work.", "Create a truthful transition story.", "I selected evidence from projects and avoided unsupported seniority claims.", "The narrative became clearer and safer.", "I need stronger employer-facing metrics.", ["communication", "ai_tools"], ["public"]),
        ("Unsupported metric example", "A workflow seemed faster after automation.", "Describe impact safely.", "I reduced manual steps and noted limitations.", "Increased efficiency by 40%.", "Use only verified metrics.", ["automation"], ["review_needed"]),
        ("Ethical decision", "A voice feature raised privacy questions.", "Protect user consent and data minimisation.", "I separated text mode, consent, retention, and deletion states.", "The design avoided requiring voice interaction.", "Future testing should include accessibility review.", ["privacy_reasoning", "responsible_ai"], ["public"]),
    ]
    for title, situation, task, action, result, reflection, skills, confidentiality in story_payloads:
        create_star_story(
            db,
            profile,
            {
                "title": title,
                "situation": situation,
                "task": task,
                "action": action,
                "result": result,
                "reflection": reflection,
                "skills_demonstrated": skills,
                "confidentiality_status": confidentiality[0],
                "evidence_links": [{"source": "demo"}] if confidentiality[0] != "review_needed" else [],
                "tags": ["communication", "technical_problem", "career_transition"],
                "user_confirmed": confidentiality[0] != "review_needed",
                "source": "demo",
            },
            profile.user_id,
        )
    first = interviews[0]
    generate_interview_questions(db, first)
    generate_preparation_brief(db, first, {"language": "en"})
    session_payload = create_mock_session(db, first, {"mode": "guided_practice", "delivery_mode": "text", "persona": "recruiter"})
    session = db.get(MockInterviewSession, session_payload["id"])
    start_mock_session(db, session)
    first_question = db.scalar(select(InterviewQuestion).where(InterviewQuestion.interview_id == first.id).order_by(InterviewQuestion.created_at))
    add_mock_turn(
        db,
        session,
        {
            "question_id": first_question.id if first_question else None,
            "answer_text": "I work at the intersection of design, technology, and learning. I can discuss evidence from a project where I designed an explainable recommendation interface and documented limitations.",
            "response_duration_seconds": 74,
        },
    )
    complete_mock_session(db, session, {"transcript_confirmed": True, "transcript_retained": True, "user_reflection": "Text-only practice helped identify a concise introduction."})
    create_mock_session(db, first, {"mode": "voice_disabled_fallback", "delivery_mode": "voice", "persona": "recruiter"})
    create_reflection(
        db,
        first,
        {
            "completed_date": "2026-07-21",
            "questions_remembered": ["Tell me about yourself.", "Why this role?"],
            "strong_answers": ["Evidence-based project introduction."],
            "weak_answers": ["Salary range needed clearer priorities."],
            "unexpected_topics": ["Notice period."],
            "user_interpretation": "Demo reflection only; no real employer feedback.",
            "outcome_status": "next_stage_received",
            "additional_evidence_needed": ["Clearer API evidence."],
            "confidence_before": 3,
            "confidence_after": 4,
            "user_confirmed": True,
        },
    )
    create_follow_up_draft(db, first, {"draft_type": "thank_you"})
    create_offer_review(
        db,
        profile,
        {
            "application_id": analysed_app.id,
            "interview_id": first.id,
            "salary": 650000,
            "currency": "NOK",
            "remote_hybrid_arrangement": "Hybrid",
            "working_hours": "Full time",
            "start_date": "2026-09-01",
            "user_priorities": ["remote flexibility", "training support", "clear title"],
            "source": "demo",
        },
        profile.user_id,
    )

