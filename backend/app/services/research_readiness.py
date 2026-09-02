from __future__ import annotations

from fastapi import HTTPException

from app.config import Settings, get_settings

REQUIRED_RESEARCH_FIELDS = {
    "researcher_identity": "researcher identity",
    "research_contact": "contact",
    "research_storage_duration": "storage duration",
    "research_study_version": "study version",
    "research_consent_document_version": "consent document version",
}

PLACEHOLDER_MARKERS = {"", "placeholder", "tbd", "todo", "to be completed", "manual-review-required", "unknown"}


def _is_placeholder(value: str | None) -> bool:
    clean = str(value or "").strip().lower()
    return clean in PLACEHOLDER_MARKERS or "placeholder" in clean


def research_readiness(settings: Settings | None = None) -> dict:
    resolved = settings or get_settings()
    missing = [label for field, label in REQUIRED_RESEARCH_FIELDS.items() if _is_placeholder(getattr(resolved, field, ""))]
    ready = not missing
    return {
        "ready": ready,
        "missingFields": missing,
        "liveRecruitmentEnabled": ready,
        "empiricalDataCollectionEnabled": ready,
        "syntheticEvaluationEnabled": True,
    }


def assert_research_ready() -> None:
    readiness = research_readiness()
    if not readiness["ready"]:
        raise HTTPException(
            status_code=403,
            detail="Research configuration incomplete. Live recruitment and empirical data collection are disabled.",
        )
