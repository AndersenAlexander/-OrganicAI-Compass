from __future__ import annotations

import hashlib
import html
import ipaddress
import re
import secrets
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from app.core.time import utc_now_naive
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.assessment import CareerMatch, SkillsInventory
from app.models.career_resilience import CareerHypothesis
from app.models.innovation_extension import (
    AdvisorComment,
    AdvisorShare,
    BrowserExtensionConnection,
    BrowserJobCapture,
    CareerDecisionJournalEntry,
    CareerDecisionJournalVersion,
    CareerRoleProfile,
    CareerRoleProfileVersion,
    InnovationAuditEvent,
)
from app.models.interview_journey import Interview, InterviewQuestion, MockInterviewSession, MockInterviewTurn
from app.models.market_application import JobAnalysis, JobApplication, JobRequirement
from app.models.profile import Profile
from app.services.career_resilience_engine import create_experiment_session, evidence_passport, list_experiment_templates
from app.services.interview_journey_engine import generate_follow_ups, interview_voice_status, mock_turn_public, question_public, score_answer
from app.services.market_application_engine import (
    _demo_marker,
    create_job_analysis,
    job_analysis_public,
    list_applications,
    list_job_analyses,
    match_analysis_evidence,
    require_analysis,
)

INNOVATION_EXTENSION_VERSION = "innovation-extension-pack-v1"
MAX_CAPTURED_TEXT_CHARS = 24000
MAX_JOURNAL_TEXT_CHARS = 8000
EXTENSION_TOKEN_DAYS = 14
ADVISOR_TOKEN_DAYS = 14

CAPTURE_STATUSES = {"Captured", "Needs review", "Confirmed", "Analysed", "Duplicate", "Rejected", "Archived"}
REQUESTED_ACTIONS = {"save", "save_and_analyse", "save_as_job_candidate", "saved_job", "job_analysis_draft"}
ADVISOR_ROLES = {"Career adviser", "Academic supervisor", "Mentor", "NAV counsellor", "Recruiter or HR specialist", "Teacher or trainer", "Other"}
ADVISOR_PERMISSION_LEVELS = {"View only", "Comment", "Suggest changes", "Validate selected evidence", "Recommend an experiment", "Recommend a roadmap action"}
ADVISOR_ALLOWED_ACTIONS = {"view", "comment", "suggest_changes", "validate_selected_evidence", "recommend_experiment", "recommend_roadmap_action", "export"}
ADVISOR_SHAREABLE_SECTIONS = {
    "Career Hypotheses",
    "Career Compatibility summary",
    "Evidence Passport",
    "Skill gaps",
    "Career Experiment results",
    "Learning Path",
    "Supported Paths",
    "Job Analysis",
    "CV review version",
    "Cover Letter review version",
    "Interview preparation",
    "Support Application Brief",
    "Career Decision Journal",
}
SENSITIVE_EXCLUDED_SECTIONS = {"Job Loss fields", "Benefit-screening inputs", "Private transcripts", "Unrelated applications"}
EVIDENCE_VALIDATION_STATES = {"Supports this evidence", "Partially supports", "Needs clarification", "Cannot verify", "Disagrees", "Recommendation only"}
PANEL_SEQUENCE_MODES = {"round_robin", "recruiter_led", "hiring_manager_led", "technical_heavy", "portfolio_heavy", "custom_order"}


def _now() -> datetime:
    return utc_now_naive()


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _make_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    return token, _hash(token)


def _clean_text(value: Any, limit: int = MAX_CAPTURED_TEXT_CHARS) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def _limited_list(value: Any, limit: int = 20) -> list[Any]:
    return list(value[:limit]) if isinstance(value, list) else []


def _demo(profile: Profile) -> bool:
    return _demo_marker(profile)


def _audit(db: Session, profile_id: str | None, event_type: str, target_type: str, target_id: str, actor_type: str = "system", actor_id: str = "", event: dict[str, Any] | None = None) -> None:
    db.add(
        InnovationAuditEvent(
            profile_id=profile_id,
            event_type=event_type,
            target_type=target_type,
            target_id=target_id,
            actor_type=actor_type,
            actor_id=actor_id,
            event_json=event or {},
        )
    )


def validate_external_url(source_url: str) -> tuple[str, str]:
    parsed = urlparse(source_url or "")
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Capture source_url must be an absolute http or https URL.")
    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise ValueError("Capture URL host is required.")
    if hostname in {"localhost", "0.0.0.0"} or hostname.endswith(".localhost") or hostname.endswith(".local"):
        raise ValueError("Localhost and private-network URLs cannot be captured.")
    try:
        address = ipaddress.ip_address(hostname)
        if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved or address.is_multicast:
            raise ValueError("Localhost and private-network URLs cannot be captured.")
    except ValueError as error:
        if "URLs cannot be captured" in str(error):
            raise
    if "." not in hostname:
        raise ValueError("Private or intranet-style hostnames cannot be captured.")
    return source_url, hostname


def _title_from_capture(page_title: str, text: str) -> tuple[str, str]:
    title = _clean_text(page_title, 255)
    employer = ""
    if " - " in title:
        first, second = [part.strip() for part in title.split(" - ", 1)]
        if first and second and len(second) <= 120:
            title, employer = first[:255], second[:255]
    if not title and text:
        title = text.split(".")[0][:255]
    return title, employer


def _capture_quality_warnings(page_title: str, captured_text: str, selected_text: str) -> list[str]:
    warnings: list[str] = []
    if len(captured_text) < 180 and len(selected_text) < 80:
        warnings.append("Some job information could not be identified automatically. Please review the captured content before saving.")
    if not page_title.strip():
        warnings.append("Page title was empty.")
    if not re.search(r"\b(requirement|responsibilit|experience|skill|qualification|candidate|role|job)\b", captured_text, re.I):
        warnings.append("Captured content may not contain a complete job description.")
    return warnings


def extension_connection_public(db: Session, row: BrowserExtensionConnection, include_token: str | None = None) -> dict[str, Any]:
    last_capture = db.scalar(select(BrowserJobCapture).where(BrowserJobCapture.extension_connection_id == row.id).order_by(BrowserJobCapture.captured_at.desc()))
    now = _now()
    effective_status = "expired" if row.expires_at <= now and row.status == "active" else row.status
    payload = {
        "id": row.id,
        "profile_id": row.profile_id,
        "display_name": row.display_name,
        "status": effective_status,
        "permissions": row.permissions_json or [],
        "expires_at": row.expires_at.isoformat(),
        "last_used_at": row.last_used_at.isoformat() if row.last_used_at else None,
        "revoked_at": row.revoked_at.isoformat() if row.revoked_at else None,
        "last_capture": capture_public(last_capture) if last_capture else None,
        "created_at": row.created_at.isoformat(),
    }
    if include_token:
        payload["connection_token"] = include_token
        payload["token_visible_once"] = True
    return payload


def create_extension_connection(db: Session, profile: Profile, payload: dict[str, Any] | None = None, user_id: str | None = None) -> dict[str, Any]:
    payload = payload or {}
    token, token_hash = _make_token()
    row = BrowserExtensionConnection(
        profile_id=profile.id,
        user_id=user_id or profile.user_id,
        token_hash=token_hash,
        display_name=_clean_text(payload.get("display_name") or "Save to OrganicAI Compass", 160),
        permissions_json=["activeTab", "storage", "scripting:user_triggered_visible_text"],
        expires_at=_now() + timedelta(days=int(payload.get("expires_in_days") or EXTENSION_TOKEN_DAYS)),
        demo_marker=_demo(profile),
    )
    db.add(row)
    db.flush()
    _audit(db, profile.id, "extension_connection_created", "browser_extension_connection", row.id, "user", user_id or profile.user_id or "", {"permissions": row.permissions_json})
    db.commit()
    return extension_connection_public(db, row, include_token=token)


def list_extension_connections(db: Session, profile: Profile) -> dict[str, Any]:
    rows = db.scalars(select(BrowserExtensionConnection).where(BrowserExtensionConnection.profile_id == profile.id).order_by(BrowserExtensionConnection.created_at.desc())).all()
    active = [row for row in rows if row.status == "active" and row.expires_at > _now()]
    return {
        "profile_id": profile.id,
        "feature_name": "Save to OrganicAI Compass",
        "connections": [extension_connection_public(db, row) for row in rows],
        "connected": bool(active),
        "privacy": {
            "user_triggered_only": True,
            "automatic_background_scraping": False,
            "raw_html_storage": False,
            "permissions": ["activeTab", "storage", "scripting only after user action"],
        },
    }


def revoke_extension_connection(db: Session, profile: Profile, connection_id: str, actor_id: str | None = None) -> dict[str, Any]:
    row = db.get(BrowserExtensionConnection, connection_id)
    if not row or row.profile_id != profile.id:
        raise LookupError("Extension connection not found")
    row.status = "revoked"
    row.revoked_at = _now()
    row.updated_at = _now()
    _audit(db, profile.id, "extension_connection_revoked", "browser_extension_connection", row.id, "user", actor_id or profile.user_id or "")
    db.commit()
    return extension_connection_public(db, row)


def validate_extension_token(db: Session, profile: Profile, token: str | None) -> BrowserExtensionConnection | None:
    if not token:
        return None
    row = db.scalar(select(BrowserExtensionConnection).where(BrowserExtensionConnection.profile_id == profile.id, BrowserExtensionConnection.token_hash == _hash(token)))
    if not row:
        raise PermissionError("Invalid extension token.")
    return validate_extension_connection(db, row)


def validate_extension_connection(db: Session, row: BrowserExtensionConnection) -> BrowserExtensionConnection:
    if row.status != "active":
        raise PermissionError("Extension token is revoked.")
    if row.expires_at <= _now():
        row.status = "expired"
        db.commit()
        raise PermissionError("Extension token is expired.")
    row.last_used_at = _now()
    row.updated_at = _now()
    db.flush()
    return row


def validate_extension_capture_context(
    db: Session,
    profile_id: str,
    token: str | None,
    current_user_id: str | None = None,
) -> tuple[Profile, BrowserExtensionConnection]:
    if not token:
        raise PermissionError("Extension connection token is required.")
    row = db.scalar(select(BrowserExtensionConnection).where(BrowserExtensionConnection.token_hash == _hash(token)))
    if not row:
        raise PermissionError("Invalid extension token.")
    if row.profile_id != profile_id:
        raise PermissionError("Extension token is not valid for this profile.")
    if current_user_id and row.user_id and row.user_id != current_user_id:
        raise PermissionError("Extension token does not belong to the current user.")
    row = validate_extension_connection(db, row)
    profile = db.get(Profile, row.profile_id)
    if not profile:
        raise LookupError("Profile not found")
    if row.user_id and profile.user_id and row.user_id != profile.user_id:
        raise PermissionError("Extension token owner does not match the profile owner.")
    return profile, row


def create_job_capture(db: Session, profile: Profile, payload: dict[str, Any], connection: BrowserExtensionConnection | None = None, user_id: str | None = None) -> dict[str, Any]:
    source_url, source_domain = validate_external_url(str(payload.get("source_url") or ""))
    page_title = _clean_text(payload.get("page_title") or "", 255)
    captured_text_raw = str(payload.get("captured_text") or "")
    sanitised_text = _clean_text(captured_text_raw, MAX_CAPTURED_TEXT_CHARS)
    selected_text = _clean_text(payload.get("selected_text") or "", MAX_CAPTURED_TEXT_CHARS)
    if len(captured_text_raw) > MAX_CAPTURED_TEXT_CHARS * 2:
        raise ValueError("Captured text exceeds the configured request-size limit.")
    if not sanitised_text and not selected_text:
        raise ValueError("Captured text or selected text is required.")
    requested_action = payload.get("requested_action") or "save"
    if requested_action not in REQUESTED_ACTIONS:
        raise ValueError("Unsupported capture requested_action.")
    method = payload.get("capture_method") or "user_triggered_browser_extension"
    if method != "user_triggered_browser_extension":
        raise ValueError("Browser captures must be explicitly user-triggered.")
    content_hash = _hash(f"{source_url}\n{sanitised_text}\n{selected_text}")
    duplicate = db.scalar(select(BrowserJobCapture).where(BrowserJobCapture.profile_id == profile.id, BrowserJobCapture.source_url == source_url, BrowserJobCapture.content_hash == content_hash))
    if duplicate:
        public = capture_public(duplicate)
        public["status"] = "Duplicate"
        public["duplicate_of"] = duplicate.id
        _audit(db, profile.id, "job_capture_duplicate", "browser_job_capture", duplicate.id, "extension" if connection else "user", connection.id if connection else user_id or profile.user_id or "")
        db.commit()
        return public
    detected_title, detected_employer = _title_from_capture(page_title, sanitised_text or selected_text)
    warnings = _capture_quality_warnings(page_title, sanitised_text, selected_text)
    row = BrowserJobCapture(
        profile_id=profile.id,
        user_id=user_id or profile.user_id,
        extension_connection_id=connection.id if connection else None,
        source_url=source_url,
        page_title=page_title,
        detected_title=detected_title,
        detected_employer=detected_employer,
        source_domain=source_domain,
        captured_text_raw=captured_text_raw[:MAX_CAPTURED_TEXT_CHARS],
        sanitised_text=sanitised_text,
        selected_text=selected_text,
        confirmed_fields_json={
            "title": _clean_text(payload.get("title") or detected_title, 255),
            "employer": _clean_text(payload.get("employer") or detected_employer, 255),
            "verified": False,
        },
        capture_method=method,
        requested_action=requested_action,
        status="Needs review" if warnings else "Captured",
        content_hash=content_hash,
        quality_warnings_json=warnings,
        extension_version=_clean_text(payload.get("extension_version") or "unknown", 80),
        demo_marker=_demo(profile),
    )
    db.add(row)
    db.flush()
    if requested_action in {"save_and_analyse", "job_analysis_draft"}:
        analysis = create_job_analysis(
            db,
            profile,
            {
                "input_type": "browser_capture",
                "pasted_text": sanitised_text or selected_text,
                "title": row.confirmed_fields_json.get("title") or detected_title or "Captured job advertisement",
                "organisation": row.confirmed_fields_json.get("employer") or detected_employer,
                "location": "",
            },
        )
        analysis_row = db.get(JobAnalysis, analysis["id"])
        if analysis_row:
            analysis_row.source_url = source_url
            analysis_row.status = "draft" if requested_action == "job_analysis_draft" else "analysed"
            row.job_analysis_id = analysis_row.id
            row.status = "Analysed" if requested_action == "save_and_analyse" else "Captured"
            match_analysis_evidence(db, analysis_row)
    _audit(db, profile.id, "job_capture_created", "browser_job_capture", row.id, "extension" if connection else "user", connection.id if connection else user_id or profile.user_id or "", {"requested_action": requested_action, "source_domain": source_domain})
    db.commit()
    return capture_public(row)


def capture_public(row: BrowserJobCapture | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "job_analysis_id": row.job_analysis_id,
        "source_url": row.source_url,
        "page_title": row.page_title,
        "detected_title": row.detected_title,
        "detected_employer": row.detected_employer,
        "source_domain": row.source_domain,
        "sanitised_text": row.sanitised_text,
        "captured_text_preview": (row.sanitised_text or row.selected_text)[:600],
        "selected_text": row.selected_text,
        "confirmed_fields": row.confirmed_fields_json or {},
        "capture_method": row.capture_method,
        "requested_action": row.requested_action,
        "status": row.status,
        "quality_warnings": row.quality_warnings_json or [],
        "extension_version": row.extension_version,
        "captured_at": row.captured_at.isoformat(),
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def list_job_captures(db: Session, profile: Profile) -> list[dict[str, Any]]:
    rows = db.scalars(select(BrowserJobCapture).where(BrowserJobCapture.profile_id == profile.id).order_by(BrowserJobCapture.captured_at.desc())).all()
    return [capture_public(row) for row in rows]


def confirm_job_capture(db: Session, profile: Profile, capture_id: str, payload: dict[str, Any] | None = None, user_id: str | None = None) -> dict[str, Any]:
    row = db.get(BrowserJobCapture, capture_id)
    if not row or row.profile_id != profile.id:
        raise LookupError("Job capture not found")
    payload = payload or {}
    row.confirmed_fields_json = {
        **(row.confirmed_fields_json or {}),
        "title": _clean_text(payload.get("title") or (row.confirmed_fields_json or {}).get("title") or row.detected_title, 255),
        "employer": _clean_text(payload.get("employer") or (row.confirmed_fields_json or {}).get("employer") or row.detected_employer, 255),
        "verified": False,
        "user_confirmed_capture_fields": True,
    }
    if payload.get("sanitised_text"):
        row.sanitised_text = _clean_text(payload["sanitised_text"], MAX_CAPTURED_TEXT_CHARS)
        row.content_hash = _hash(f"{row.source_url}\n{row.sanitised_text}\n{row.selected_text}")
    row.status = "Confirmed"
    if payload.get("analyse") or row.requested_action == "save_and_analyse":
        analysis = create_job_analysis(
            db,
            profile,
            {
                "input_type": "browser_capture_confirmed",
                "pasted_text": row.sanitised_text or row.selected_text,
                "title": row.confirmed_fields_json.get("title") or row.detected_title,
                "organisation": row.confirmed_fields_json.get("employer") or row.detected_employer,
            },
        )
        analysis_row = db.get(JobAnalysis, analysis["id"])
        if analysis_row:
            analysis_row.source_url = row.source_url
            row.job_analysis_id = analysis_row.id
            row.status = "Analysed"
            match_analysis_evidence(db, analysis_row)
    row.updated_at = _now()
    _audit(db, profile.id, "job_capture_confirmed", "browser_job_capture", row.id, "user", user_id or profile.user_id or "")
    db.commit()
    return capture_public(row)


def _normalise_sections(values: list[str]) -> list[str]:
    sections = [item for item in values if item in ADVISOR_SHAREABLE_SECTIONS and item not in SENSITIVE_EXCLUDED_SECTIONS]
    return sections[:12]


def advisor_share_public(db: Session, row: AdvisorShare, include_token: str | None = None, include_sections: bool = False) -> dict[str, Any]:
    comments = db.scalars(select(AdvisorComment).where(AdvisorComment.share_id == row.id).order_by(AdvisorComment.created_at.desc())).all()
    payload = {
        "id": row.id,
        "profile_id": row.profile_id,
        "adviser_display_name": row.adviser_display_name,
        "adviser_role": row.adviser_role,
        "purpose": row.purpose,
        "permission_level": row.permission_level,
        "allowed_sections": row.allowed_sections_json or [],
        "allowed_actions": row.allowed_actions_json or [],
        "export_allowed": row.export_allowed,
        "status": "expired" if row.expires_at <= _now() and row.status == "active" else row.status,
        "expires_at": row.expires_at.isoformat(),
        "access_attempts": row.access_attempts,
        "max_access_attempts": row.max_access_attempts,
        "last_accessed_at": row.last_accessed_at.isoformat() if row.last_accessed_at else None,
        "comments": [advisor_comment_public(item) for item in comments],
        "limitations": [
            "This shared review does not grant access to your full OrganicAI Compass account.",
            "Adviser feedback cannot directly modify profile facts, evidence levels, benefit screening, application status, or roadmap actions.",
            "Sensitive Job Loss fields, benefit-screening inputs, private transcripts, and unrelated applications are excluded by default.",
        ],
        "created_at": row.created_at.isoformat(),
    }
    if include_token:
        payload["share_token"] = include_token
        payload["review_url"] = f"/advisor-review/{include_token}"
        payload["token_visible_once"] = True
    if include_sections:
        payload["sections"] = _share_sections(db, row)
        payload["no_index"] = True
    return payload


def create_advisor_share(db: Session, profile: Profile, payload: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
    role = payload.get("adviser_role") or "Other"
    if role not in ADVISOR_ROLES:
        role = "Other"
    permission_level = payload.get("permission_level") or "View only"
    if permission_level not in ADVISOR_PERMISSION_LEVELS:
        raise ValueError("Unsupported adviser permission level.")
    sections = _normalise_sections(_limited_list(payload.get("allowed_sections"), 20) or ["Career Hypotheses", "Evidence Passport"])
    if not sections:
        raise ValueError("At least one allowed share section is required.")
    actions = [action for action in _limited_list(payload.get("allowed_actions"), 12) if action in ADVISOR_ALLOWED_ACTIONS] or ["view"]
    if permission_level == "View only":
        actions = ["view"]
    token, token_hash = _make_token()
    pin = _clean_text(payload.get("pin") or "", 40)
    days = min(max(int(payload.get("access_days") or ADVISOR_TOKEN_DAYS), 1), 90)
    row = AdvisorShare(
        profile_id=profile.id,
        user_id=user_id or profile.user_id,
        token_hash=token_hash,
        adviser_display_name=_clean_text(payload.get("adviser_display_name") or "External adviser", 160),
        adviser_role=role,
        purpose=_clean_text(payload.get("purpose") or "Review selected OrganicAI Compass materials.", 2000),
        permission_level=permission_level,
        allowed_sections_json=sections,
        allowed_actions_json=actions,
        export_allowed=bool(payload.get("export_allowed", False) and "export" in actions),
        expires_at=_now() + timedelta(days=days),
        max_access_attempts=min(max(int(payload.get("max_access_attempts") or 20), 3), 100),
        optional_pin_hash=_hash(pin) if pin else None,
        demo_marker=_demo(profile),
    )
    db.add(row)
    db.flush()
    _audit(db, profile.id, "advisor_share_created", "advisor_share", row.id, "user", user_id or profile.user_id or "", {"sections": sections, "permission_level": permission_level})
    db.commit()
    return advisor_share_public(db, row, include_token=token)


def list_advisor_shares(db: Session, profile: Profile) -> list[dict[str, Any]]:
    rows = db.scalars(select(AdvisorShare).where(AdvisorShare.profile_id == profile.id).order_by(AdvisorShare.created_at.desc())).all()
    return [advisor_share_public(db, row) for row in rows]


def get_advisor_share(db: Session, profile: Profile, share_id: str) -> dict[str, Any]:
    row = db.get(AdvisorShare, share_id)
    if not row or row.profile_id != profile.id:
        raise LookupError("Advisor share not found")
    return advisor_share_public(db, row, include_sections=True)


def revoke_advisor_share(db: Session, profile: Profile, share_id: str, actor_id: str | None = None) -> dict[str, Any]:
    row = db.get(AdvisorShare, share_id)
    if not row or row.profile_id != profile.id:
        raise LookupError("Advisor share not found")
    row.status = "revoked"
    row.revoked_at = _now()
    row.updated_at = _now()
    _audit(db, profile.id, "advisor_share_revoked", "advisor_share", row.id, "user", actor_id or profile.user_id or "")
    db.commit()
    return advisor_share_public(db, row)


def _share_by_token(db: Session, token: str, pin: str | None = None) -> AdvisorShare:
    row = db.scalar(select(AdvisorShare).where(AdvisorShare.token_hash == _hash(token)))
    if not row:
        raise LookupError("Advisor share not found.")
    if row.status != "active":
        raise PermissionError("Advisor share is not active.")
    if row.expires_at <= _now():
        row.status = "expired"
        db.commit()
        raise PermissionError("Advisor share has expired.")
    if row.access_attempts >= row.max_access_attempts:
        row.status = "expired"
        db.commit()
        raise PermissionError("Advisor share access limit has been reached.")
    if row.optional_pin_hash and _hash(pin or "") != row.optional_pin_hash:
        row.access_attempts += 1
        row.updated_at = _now()
        db.commit()
        raise PermissionError("Advisor PIN is invalid.")
    row.access_attempts += 1
    row.last_accessed_at = _now()
    row.updated_at = _now()
    _audit(db, row.profile_id, "advisor_share_accessed", "advisor_share", row.id, "advisor", row.adviser_display_name, {"attempt": row.access_attempts})
    db.flush()
    return row


def advisor_review(db: Session, token: str, pin: str | None = None) -> dict[str, Any]:
    row = _share_by_token(db, token, pin)
    db.commit()
    return advisor_share_public(db, row, include_sections=True)


def _share_sections(db: Session, share: AdvisorShare) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    allowed = share.allowed_sections_json or []
    if "Career Hypotheses" in allowed:
        rows = db.scalars(select(CareerHypothesis).where(CareerHypothesis.profile_id == share.profile_id, CareerHypothesis.status != "archived").order_by(CareerHypothesis.updated_at.desc())).all()
        sections.append({"name": "Career Hypotheses", "items": [{"id": row.id, "title": row.title, "statement": row.statement, "status": row.status, "uncertainty_label": row.uncertainty_label, "source": "career_hypothesis"} for row in rows[:10]]})
    if "Evidence Passport" in allowed:
        passport = evidence_passport(db, share.profile_id)
        sections.append({"name": "Evidence Passport", "items": passport.get("skills", [])[:12], "excluded": ["private transcripts", "raw audio"]})
    if "Job Analysis" in allowed:
        sections.append({"name": "Job Analysis", "items": [{"id": item["id"], "title": item["title"], "organisation": item["organisation"], "status": item["status"], "requirements": item.get("requirements", [])[:8]} for item in list_job_analyses(db, share.profile_id)[:6]]})
    if "Career Decision Journal" in allowed:
        rows = db.scalars(select(CareerDecisionJournalEntry).where(CareerDecisionJournalEntry.profile_id == share.profile_id, CareerDecisionJournalEntry.privacy_scope != "research_excluded").order_by(CareerDecisionJournalEntry.updated_at.desc())).all()
        sections.append({"name": "Career Decision Journal", "items": [{"id": row.id, "title": row.title, "decision_summary": row.decision_summary, "status": row.status, "review_date": row.review_date, "outcome_status": row.outcome_status} for row in rows[:8]]})
    if "Career Experiment results" in allowed:
        sections.append({"name": "Career Experiment results", "items": [{"summary": "Career experiment records can be reviewed here without granting full profile access.", "source": "career_experiments"}]})
    for name in allowed:
        if not any(section["name"] == name for section in sections):
            sections.append({"name": name, "items": [], "limitations": ["No shareable records are currently available for this section."]})
    return sections


def submit_advisor_comment(db: Session, token: str, payload: dict[str, Any], pin: str | None = None) -> dict[str, Any]:
    share = _share_by_token(db, token, pin)
    if not any(action in (share.allowed_actions_json or []) for action in ["comment", "suggest_changes", "validate_selected_evidence", "recommend_experiment", "recommend_roadmap_action"]):
        raise PermissionError("This adviser share is view-only.")
    validation = payload.get("evidence_validation") or "Recommendation only"
    if validation not in EVIDENCE_VALIDATION_STATES:
        validation = "Recommendation only"
    comment = AdvisorComment(
        share_id=share.id,
        profile_id=share.profile_id,
        adviser_display_name=share.adviser_display_name,
        adviser_role=share.adviser_role,
        target_type=_clean_text(payload.get("target_type") or "share", 80),
        target_id=_clean_text(payload.get("target_id") or "", 120),
        suggestion_type=_clean_text(payload.get("suggestion_type") or "General comment", 120),
        comment_text=_clean_text(payload.get("comment_text") or "", 4000),
        evidence_validation=validation,
        supporting_reference=_clean_text(payload.get("supporting_reference") or "", 1000),
        status="pending",
        provenance="human_adviser",
    )
    if not comment.comment_text:
        raise ValueError("Advisor comment text is required.")
    db.add(comment)
    db.flush()
    _audit(db, share.profile_id, "advisor_comment_created", "advisor_comment", comment.id, "advisor", share.adviser_display_name, {"share_id": share.id, "suggestion_type": comment.suggestion_type})
    db.commit()
    return advisor_comment_public(comment)


def advisor_comment_public(row: AdvisorComment) -> dict[str, Any]:
    return {
        "id": row.id,
        "share_id": row.share_id,
        "profile_id": row.profile_id,
        "adviser_display_name": row.adviser_display_name,
        "adviser_role": row.adviser_role,
        "target_type": row.target_type,
        "target_id": row.target_id,
        "suggestion_type": row.suggestion_type,
        "comment_text": row.comment_text,
        "evidence_validation": row.evidence_validation,
        "supporting_reference": row.supporting_reference,
        "status": row.status,
        "user_response": row.user_response,
        "provenance": row.provenance,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def respond_to_advisor_comment(db: Session, profile: Profile, comment_id: str, payload: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
    row = db.get(AdvisorComment, comment_id)
    if not row or row.profile_id != profile.id:
        raise LookupError("Advisor comment not found")
    decision = payload.get("status") or payload.get("decision")
    if decision not in {"accepted", "rejected", "pending"}:
        raise ValueError("Advisor comment response must be accepted, rejected, or pending.")
    row.status = decision
    row.user_response = _clean_text(payload.get("user_response") or "", 2000)
    row.updated_at = _now()
    _audit(db, profile.id, f"advisor_comment_{decision}", "advisor_comment", row.id, "user", user_id or profile.user_id or "", {"profile_mutated": False, "evidence_mutated": False})
    db.commit()
    return advisor_comment_public(row)


PANEL_PERSONAS: dict[str, dict[str, Any]] = {
    "recruiter": {"persona_id": "recruiter", "role_label": "Recruiter", "purpose": "Verify motivation, availability, career transition, suitability, salary expectations, and communication clarity.", "question_categories": ["motivation", "availability", "career transition", "general suitability", "salary expectations", "communication clarity"], "expected_depth": "concise", "follow_up_style": "clarify logistics and evidence boundaries", "terminology_level": "general", "allowed_evidence_focus": ["career narrative", "confirmed requirements", "application facts"], "maximum_question_count": 4, "voice_configuration": {"voice": "default", "multi_voice_optional": True}},
    "hiring_manager": {"persona_id": "hiring_manager", "role_label": "Hiring Manager", "purpose": "Explore relevant experience, responsibility, impact, collaboration, problem solving, and first 90 days.", "question_categories": ["relevant experience", "responsibility", "impact", "collaboration", "problem solving", "first 90 days"], "expected_depth": "specific", "follow_up_style": "ask for ownership and outcomes", "terminology_level": "role-specific", "allowed_evidence_focus": ["Evidence Passport", "STAR stories", "career experiments"], "maximum_question_count": 4, "voice_configuration": {"voice": "default", "multi_voice_optional": True}},
    "technical_lead": {"persona_id": "technical_lead", "role_label": "Technical Lead", "purpose": "Probe architecture, implementation decisions, testing, debugging, API design, security, and failure handling.", "question_categories": ["architecture", "implementation decisions", "testing", "debugging", "API design", "security", "failure handling"], "expected_depth": "advanced", "follow_up_style": "ask for trade-offs and verification", "terminology_level": "technical", "allowed_evidence_focus": ["confirmed technical requirements", "portfolio evidence", "experiments"], "maximum_question_count": 5, "voice_configuration": {"voice": "default", "multi_voice_optional": True}},
    "product_manager": {"persona_id": "product_manager", "role_label": "Product Manager", "purpose": "Assess product judgment, prioritisation, users, metrics, and trade-offs.", "question_categories": ["user needs", "prioritisation", "metrics", "roadmap", "trade-offs"], "expected_depth": "specific", "follow_up_style": "connect decisions to users and constraints", "terminology_level": "product", "allowed_evidence_focus": ["product evidence", "job requirements"], "maximum_question_count": 4, "voice_configuration": {"voice": "default", "multi_voice_optional": True}},
    "design_lead": {"persona_id": "design_lead", "role_label": "Design Lead", "purpose": "Review user needs, design decisions, accessibility, research, trade-offs, and portfolio evidence.", "question_categories": ["user needs", "design decisions", "accessibility", "research", "trade-offs", "portfolio evidence"], "expected_depth": "specific", "follow_up_style": "ask for design rationale and evidence", "terminology_level": "design", "allowed_evidence_focus": ["portfolio", "research", "accessibility"], "maximum_question_count": 4, "voice_configuration": {"voice": "default", "multi_voice_optional": True}},
    "client_stakeholder": {"persona_id": "client_stakeholder", "role_label": "Client Stakeholder", "purpose": "Evaluate communication, risk handling, collaboration, and practical value.", "question_categories": ["communication", "risk", "value", "collaboration"], "expected_depth": "plain language", "follow_up_style": "ask for practical outcomes", "terminology_level": "business", "allowed_evidence_focus": ["client-facing evidence"], "maximum_question_count": 3, "voice_configuration": {"voice": "default", "multi_voice_optional": True}},
    "academic_research_reviewer": {"persona_id": "academic_research_reviewer", "role_label": "Academic or Research Reviewer", "purpose": "Probe methodology, evidence quality, limitations, and ethical reasoning.", "question_categories": ["methodology", "evidence quality", "limitations", "ethics"], "expected_depth": "analytical", "follow_up_style": "ask for limitations and sources", "terminology_level": "academic", "allowed_evidence_focus": ["research evidence", "evaluation"], "maximum_question_count": 3, "voice_configuration": {"voice": "default", "multi_voice_optional": True}},
    "custom_panel_member": {"persona_id": "custom_panel_member", "role_label": "Custom panel member", "purpose": "Ask role-specific questions configured by the user.", "question_categories": ["custom"], "expected_depth": "user-defined", "follow_up_style": "user-defined", "terminology_level": "user-defined", "allowed_evidence_focus": ["selected evidence"], "maximum_question_count": 3, "voice_configuration": {"voice": "default", "multi_voice_optional": True}},
}


def panel_personas() -> list[dict[str, Any]]:
    voice = interview_voice_status()
    return [{**persona, "voice_configuration": {**persona["voice_configuration"], "multi_voice_supported": bool(voice.get("enabled") and voice.get("configured"))}} for persona in PANEL_PERSONAS.values()]


def _requirements_for_interview(db: Session, interview: Interview) -> list[JobRequirement]:
    if not interview.job_analysis_id:
        return []
    return db.scalars(
        select(JobRequirement)
        .where(
            JobRequirement.analysis_id == interview.job_analysis_id,
            JobRequirement.profile_id == interview.profile_id,
            JobRequirement.status == "active",
            JobRequirement.user_confirmation_state.in_(["confirmed", "needs_review"]),
        )
        .order_by(JobRequirement.order_index)
    ).all()


def create_panel_session(db: Session, interview: Interview, payload: dict[str, Any]) -> dict[str, Any]:
    persona_ids = [item for item in _limited_list(payload.get("personas"), 5) if item in PANEL_PERSONAS]
    if len(persona_ids) < 2 or len(persona_ids) > 5:
        raise ValueError("Panel interviews require two to five supported personas.")
    delivery = payload.get("delivery_mode") or "text"
    voice_status = interview_voice_status()
    voice_fallback = ""
    if delivery == "voice" and not (voice_status.get("enabled") and voice_status.get("configured")):
        delivery = "text"
        voice_fallback = "Multi-voice panel mode is not configured; text mode is used and each question names the persona."
    sequence_mode = payload.get("sequence_mode") or "round_robin"
    if sequence_mode not in PANEL_SEQUENCE_MODES:
        raise ValueError("Unsupported panel sequence mode.")
    requirements = _requirements_for_interview(db, interview)
    questions: list[InterviewQuestion] = []
    ordered_personas = _ordered_panel_personas(persona_ids, sequence_mode, _limited_list(payload.get("custom_order"), 5))
    max_questions = min(max(int(payload.get("duration_minutes") or 30) // 8, len(ordered_personas)), 12)
    if not requirements:
        for index, persona_id in enumerate(ordered_personas):
            persona = PANEL_PERSONAS[persona_id]
            question = InterviewQuestion(
                interview_id=interview.id,
                profile_id=interview.profile_id,
                application_id=interview.application_id,
                job_analysis_id=interview.job_analysis_id,
                category=persona["question_categories"][0],
                stage="panel",
                question_text=f"{persona['role_label']}: Which role facts are confirmed, and what information still needs clarification before this interview?",
                why_it_may_be_asked="This safeguard question is used because no confirmed job-analysis requirements are available.",
                answer_objective="Separate confirmed facts from missing information without inventing company requirements.",
                risk_level="high",
                difficulty=payload.get("difficulty") or "moderate",
                source_type="missing_job_analysis_safeguard",
                origin="deterministic_panel",
            )
            db.add(question)
            questions.append(question)
            if index + 1 >= max_questions:
                break
    else:
        turn_index = 0
        while len(questions) < max_questions:
            persona_id = ordered_personas[turn_index % len(ordered_personas)]
            persona = PANEL_PERSONAS[persona_id]
            requirement = requirements[turn_index % len(requirements)]
            category = _category_for_persona_requirement(persona_id, requirement)
            question = InterviewQuestion(
                interview_id=interview.id,
                profile_id=interview.profile_id,
                application_id=interview.application_id,
                job_analysis_id=interview.job_analysis_id,
                category=category,
                stage="panel",
                question_text=f"{persona['role_label']}: How would you discuss this confirmed requirement: {requirement.requirement_text}?",
                why_it_may_be_asked="This panel question is based on a requirement stored in the Job Analyzer. It does not add company facts.",
                related_job_requirement_id=requirement.id,
                related_job_requirement=requirement.requirement_text,
                related_evidence_json=[],
                answer_objective="Answer with confirmed evidence, transferable evidence, or a clear limitation.",
                risk_level="high" if requirement.requirement_type == "mandatory" else "medium",
                difficulty=payload.get("difficulty") or "moderate",
                source_type="confirmed_job_requirement",
                origin="deterministic_panel",
            )
            db.add(question)
            questions.append(question)
            turn_index += 1
    db.flush()
    sequence = [
        {
            "question_id": question.id,
            "persona_id": ordered_personas[index % len(ordered_personas)],
            "turn_index": index + 1,
            "category": question.category,
            "source": question.source_type,
            "related_requirement": question.related_job_requirement,
        }
        for index, question in enumerate(questions)
    ]
    session = MockInterviewSession(
        interview_id=interview.id,
        profile_id=interview.profile_id,
        application_id=interview.application_id,
        mode=payload.get("mode") or "panel_simulation",
        delivery_mode=delivery,
        persona="panel",
        status="created",
        question_sequence_json=sequence,
        timing_enabled=bool(payload.get("timing_enabled", True)),
        feedback_json={
            "panel_config": {
                "personas": [PANEL_PERSONAS[item] for item in persona_ids],
                "language": payload.get("language") or "en",
                "guided": payload.get("simulation_style", "guided") == "guided",
                "sequence_mode": sequence_mode,
                "difficulty": payload.get("difficulty") or "moderate",
                "evidence_focus": _limited_list(payload.get("evidence_focus"), 10),
                "follow_up_questions_enabled": bool(payload.get("follow_up_questions_enabled", True)),
                "voice_fallback": voice_fallback,
            },
            "no_single_opaque_score": True,
        },
        source="deterministic_panel",
        demo_marker=interview.demo_marker,
    )
    db.add(session)
    interview.stage_type = "panel"
    interview.mock_session_status = "Created"
    interview.updated_at = _now()
    db.commit()
    return panel_session_public(db, session)


def _ordered_panel_personas(persona_ids: list[str], mode: str, custom_order: list[Any]) -> list[str]:
    if mode == "custom_order":
        custom = [item for item in custom_order if item in persona_ids]
        return custom + [item for item in persona_ids if item not in custom]
    if mode == "recruiter_led" and "recruiter" in persona_ids:
        return ["recruiter"] + [item for item in persona_ids if item != "recruiter"]
    if mode == "hiring_manager_led" and "hiring_manager" in persona_ids:
        return ["hiring_manager"] + [item for item in persona_ids if item != "hiring_manager"]
    if mode == "technical_heavy" and "technical_lead" in persona_ids:
        return ["technical_lead"] + persona_ids + ["technical_lead"]
    if mode == "portfolio_heavy" and "design_lead" in persona_ids:
        return ["design_lead"] + persona_ids
    return persona_ids


def _category_for_persona_requirement(persona_id: str, requirement: JobRequirement) -> str:
    if persona_id == "technical_lead" and requirement.requirement_category in {"skills", "technology"}:
        return "technical depth"
    if persona_id == "design_lead":
        return "portfolio evidence"
    if persona_id == "recruiter":
        return "general suitability"
    if persona_id == "hiring_manager":
        return "impact and ownership"
    return PANEL_PERSONAS[persona_id]["question_categories"][0]


def add_panel_turn(db: Session, session: MockInterviewSession, payload: dict[str, Any]) -> dict[str, Any]:
    if session.mode not in {"panel_simulation", "full_panel_simulation"} and session.persona != "panel":
        raise ValueError("Mock session is not a panel interview.")
    sequence = session.question_sequence_json or []
    question = db.get(InterviewQuestion, payload.get("question_id")) if payload.get("question_id") else None
    if question and question.interview_id != session.interview_id:
        raise PermissionError("Question does not belong to this panel session.")
    if not question and sequence:
        question = db.get(InterviewQuestion, sequence[0].get("question_id")) if isinstance(sequence[0], dict) else None
    turn_count = db.scalar(select(func.count()).select_from(MockInterviewTurn).where(MockInterviewTurn.session_id == session.id)) or 0
    sequence_item = next((item for item in sequence if isinstance(item, dict) and item.get("question_id") == (question.id if question else payload.get("question_id"))), {})
    persona_id = payload.get("persona_id") or sequence_item.get("persona_id") or "custom_panel_member"
    if persona_id not in PANEL_PERSONAS:
        persona_id = "custom_panel_member"
    answer = _clean_text(payload.get("answer_text") or payload.get("transcript") or "", 12000)
    rubric = score_answer(question.question_text if question else payload.get("question_text", ""), answer, payload.get("response_duration_seconds"))
    turn = MockInterviewTurn(
        session_id=session.id,
        interview_id=session.interview_id,
        profile_id=session.profile_id,
        question_id=question.id if question else None,
        turn_index=int(turn_count) + 1,
        question_text=question.question_text if question else _clean_text(payload.get("question_text") or "", 2000),
        answer_text=answer,
        corrected_transcript=_clean_text(payload.get("corrected_transcript") or answer, 12000),
        response_duration_seconds=payload.get("response_duration_seconds"),
        estimated_word_count=len(answer.split()) if answer else 0,
        completion_status=payload.get("completion_status") or "answered",
        follow_up_questions_json=generate_follow_ups(answer, rubric["rubric"]) if (session.feedback_json or {}).get("panel_config", {}).get("follow_up_questions_enabled", True) else [],
        rubric_json=rubric["rubric"],
        feedback_json={
            **rubric["feedback"],
            "persona_id": persona_id,
            "persona_label": PANEL_PERSONAS[persona_id]["role_label"],
            "category": question.category if question else payload.get("category", ""),
            "source": question.source_type if question else "manual_panel_turn",
            "related_requirement": question.related_job_requirement if question else "",
            "related_evidence": question.related_evidence_json if question else [],
            "prohibited_inferences": ["emotion", "personality", "honesty", "employability", "accent quality"],
        },
    )
    db.add(turn)
    session.status = "in_progress"
    session.updated_at = _now()
    db.commit()
    return panel_turn_public(turn)


def complete_panel_session(db: Session, session: MockInterviewSession, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    turns = db.scalars(select(MockInterviewTurn).where(MockInterviewTurn.session_id == session.id).order_by(MockInterviewTurn.turn_index)).all()
    by_persona: dict[str, list[MockInterviewTurn]] = defaultdict(list)
    for turn in turns:
        by_persona[(turn.feedback_json or {}).get("persona_id", "custom_panel_member")].append(turn)
    persona_feedback = []
    shared_strength_counter: Counter[str] = Counter()
    repeated_gap_counter: Counter[str] = Counter()
    unsupported_claims = []
    difficult_questions = []
    for persona_id, persona_turns in by_persona.items():
        strengths: Counter[str] = Counter()
        needs: Counter[str] = Counter()
        for turn in persona_turns:
            feedback = turn.feedback_json or {}
            strengths.update(feedback.get("strengths", []))
            needs.update(feedback.get("needs_improvement", []))
            unsupported_claims.extend(feedback.get("unsupported_or_unclear_claims", []))
            if any(item.get("score", 0) <= 1 for item in (turn.rubric_json or [])):
                difficult_questions.append(turn.question_text)
        shared_strength_counter.update(strengths)
        repeated_gap_counter.update(needs)
        persona_feedback.append(
            {
                "persona_id": persona_id,
                "persona_label": PANEL_PERSONAS.get(persona_id, PANEL_PERSONAS["custom_panel_member"])["role_label"],
                "strengths": [item for item, _ in strengths.most_common(4)],
                "weaknesses": [item for item, _ in needs.most_common(4)],
                "recommended_next_practice": f"Practise one answer for the {PANEL_PERSONAS.get(persona_id, PANEL_PERSONAS['custom_panel_member'])['role_label']} using evidence-linked claims.",
                "turn_count": len(persona_turns),
            }
        )
    feedback = {
        "personas": persona_feedback,
        "shared_strengths": [item for item, count in shared_strength_counter.items() if count > 1][:5],
        "persona_specific_weaknesses": {item["persona_id"]: item["weaknesses"] for item in persona_feedback},
        "unsupported_claims": unsupported_claims[:8],
        "repeated_gaps": [item for item, _ in repeated_gap_counter.most_common(6)],
        "questions_that_caused_difficulty": difficult_questions[:6],
        "recommended_next_practice": "Repeat the panel with the persona that exposed the clearest evidence gap.",
        "user_reflection": _clean_text(payload.get("user_reflection") or "", 2000),
        "no_single_opaque_score": True,
        "prohibited_inferences": ["emotion", "personality", "honesty", "employability", "accent quality"],
    }
    session.status = "completed"
    session.completed_at = _now()
    session.transcript_confirmed = bool(payload.get("transcript_confirmed", False))
    session.transcript_retained = bool(payload.get("transcript_retained", False))
    session.feedback_json = {**(session.feedback_json or {}), "panel_feedback": feedback, "no_single_opaque_score": True}
    session.rubric_results_json = persona_feedback
    session.updated_at = _now()
    db.commit()
    return panel_session_public(db, session)


def panel_turn_public(row: MockInterviewTurn) -> dict[str, Any]:
    base = mock_turn_public(row)
    feedback = row.feedback_json or {}
    base.update(
        {
            "persona_id": feedback.get("persona_id"),
            "persona_label": feedback.get("persona_label"),
            "category": feedback.get("category"),
            "source": feedback.get("source"),
            "related_requirement": feedback.get("related_requirement"),
            "related_evidence": feedback.get("related_evidence", []),
            "prohibited_inferences": feedback.get("prohibited_inferences", []),
        }
    )
    return base


def panel_session_public(db: Session, row: MockInterviewSession) -> dict[str, Any]:
    turns = db.scalars(select(MockInterviewTurn).where(MockInterviewTurn.session_id == row.id).order_by(MockInterviewTurn.turn_index)).all()
    questions = []
    for item in row.question_sequence_json or []:
        question = db.get(InterviewQuestion, item.get("question_id")) if isinstance(item, dict) else None
        if question:
            questions.append({**question_public(question), "persona_id": item.get("persona_id"), "persona_label": PANEL_PERSONAS.get(item.get("persona_id", ""), {}).get("role_label", "Panel member"), "turn_index": item.get("turn_index")})
    return {
        "id": row.id,
        "interview_id": row.interview_id,
        "profile_id": row.profile_id,
        "application_id": row.application_id,
        "mode": row.mode,
        "delivery_mode": row.delivery_mode,
        "persona": row.persona,
        "status": row.status,
        "panel_config": (row.feedback_json or {}).get("panel_config", {}),
        "questions": questions,
        "turns": [panel_turn_public(turn) for turn in turns],
        "feedback": (row.feedback_json or {}).get("panel_feedback", row.feedback_json or {}),
        "rubric_results": row.rubric_results_json or [],
        "no_single_opaque_score": True,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
        "completed_at": row.completed_at.isoformat() if row.completed_at else None,
    }


def career_role_catalogue() -> list[dict[str, Any]]:
    families = {
        "AI and software": [
            ("rag-application-developer", "RAG Application Developer", ["retrieval developer", "AI application engineer"], ["retrieval pipelines", "grounded answers", "evaluation traces"]),
            ("ai-integration-developer", "AI Integration Developer", ["AI automation developer", "LLM integration engineer"], ["API orchestration", "tool integrations", "workflow safety"]),
            ("frontend-developer", "Frontend Developer", ["UI developer", "React developer"], ["accessible interfaces", "typed frontend systems", "performance"]),
            ("ai-product-engineer", "AI Product Engineer", ["product-minded AI engineer"], ["AI product prototypes", "evaluation UX", "feature instrumentation"]),
        ],
        "Design and product": [
            ("ai-product-designer", "AI Product Designer", ["human-centred AI designer"], ["explainable interfaces", "research synthesis", "interaction trade-offs"]),
            ("ux-designer", "UX Designer", ["user experience designer"], ["user research", "flows", "accessibility"]),
            ("service-designer", "Service Designer", ["journey designer"], ["service blueprints", "stakeholder alignment", "touchpoint design"]),
            ("creative-technologist", "Creative Technologist", ["prototype technologist"], ["interactive prototypes", "creative coding", "tool exploration"]),
        ],
        "Consulting and strategy": [
            ("ai-integration-consultant", "AI Integration Consultant", ["AI workflow consultant"], ["workflow mapping", "risk boundaries", "adoption support"]),
            ("digital-transformation-consultant", "Digital Transformation Consultant", ["transformation adviser"], ["change planning", "process redesign", "stakeholder communication"]),
            ("human-centred-ai-specialist", "Human-Centred AI Specialist", ["responsible AI specialist"], ["AI governance", "human oversight", "evaluation facilitation"]),
            ("technology-consultant", "Technology Consultant", ["digital consultant"], ["requirements discovery", "solution options", "implementation planning"]),
        ],
        "Learning and communication": [
            ("learning-experience-designer", "Learning Experience Designer", ["instructional designer"], ["learning journeys", "activities", "assessment rubrics"]),
            ("technical-trainer", "Technical Trainer", ["software trainer"], ["technical workshops", "hands-on labs", "learner support"]),
            ("ai-career-coach", "AI Career Coach", ["career transition coach"], ["career reflection", "AI literacy", "evidence-based planning"]),
            ("digital-learning-specialist", "Digital Learning Specialist", ["e-learning specialist"], ["digital courses", "learning analytics", "content operations"]),
        ],
    }
    roles: list[dict[str, Any]] = []
    for family, items in families.items():
        for slug, title, aliases, focus in items:
            technical = ["AI tools", "data literacy", "evaluation"] if "AI" in title or "RAG" in title else ["digital collaboration", "documentation", "accessibility"]
            profile = {
                "role_id": slug,
                "slug": slug,
                "title": title,
                "aliases": aliases,
                "career_family": family,
                "role_summary": f"{title} work centres on {', '.join(focus)} while keeping evidence, limitations, and human accountability visible.",
                "typical_responsibilities": [f"Plan and deliver {focus[0]}", f"Document decisions related to {focus[1]}", "Communicate limitations and evidence to stakeholders"],
                "typical_daily_tasks": [f"Review goals for {focus[0]}", "Create or improve artefacts", "Discuss trade-offs with collaborators", "Record decisions and next steps"],
                "work_environment": "Usually cross-functional, with a mix of focused production work, review sessions, and stakeholder communication.",
                "entry_routes": ["portfolio project", "career experiment", "adjacent role transition", "formal learning path"],
                "experience_expectations": ["Evidence of practical work matters more than title labels", "Junior routes require clear portfolio examples and reviewable process notes"],
                "technical_skills": technical + focus,
                "transferable_skills": ["communication", "critical thinking", "planning", "collaboration"],
                "human_critical_skills": ["judgment", "ethics", "user empathy", "accountability", "sense-making"],
                "ai_augmented_tasks": ["drafting alternatives", "summarising source material", "checking consistency", "generating test cases"],
                "potentially_automatable_tasks": ["first drafts", "routine summaries", "format conversion", "basic classification"],
                "tasks_requiring_human_accountability": ["final decisions", "stakeholder commitments", "ethical trade-offs", "claims about personal experience"],
                "education_pathways": ["project-based portfolio pathway", "targeted course sequence", "supervised internship or practicum"],
                "certifications": ["Optional vendor or domain certificate when relevant and verified"],
                "typical_portfolio_evidence": [f"case study demonstrating {focus[0]}", "decision log", "evaluation notes", "reflection on limitations"],
                "recommended_career_experiments": ["ai-product-explainable-recommendation-interface", "rag-developer-retrieval-pipeline-spec"],
                "related_learning_objectives": ["document evidence", "evaluate quality", "communicate limitations"],
                "related_esco_concepts": ["digital competence", "communication", "software development" if "Developer" in title or "Engineer" in title else "design"],
                "related_labour_market_job_titles": [title, *aliases],
                "related_local_job_opportunities": [],
                "language_considerations": ["English is common in international teams", "Norwegian may be required for local public-sector or client-facing roles"],
                "interview_categories": ["motivation", "evidence", "trade-offs", "collaboration", "limitations"],
                "adjacent_roles": [other_title for _, other_title, _, _ in items if other_title != title][:3],
                "progression_routes": ["specialist contributor", "lead role", "consultant", "product or programme leadership"],
                "known_uncertainties": ["Local demand varies by provider coverage", "Task mix differs by organisation", "No salary claims are included without an approved source"],
                "source_metadata": {"source_type": "curated OrganicAI thesis catalogue", "salary_figures_included": False, "future_proof_claim": False},
                "last_reviewed_date": "2026-07-24",
                "version": "career-role-profile-v1",
            }
            roles.append({"slug": slug, "title": title, "career_family": family, "aliases": aliases, "summary": profile["role_summary"], "profile": profile})
    return roles


def sync_career_encyclopedia(db: Session) -> dict[str, Any]:
    created = 0
    updated = 0
    for item in career_role_catalogue():
        row = db.scalar(select(CareerRoleProfile).where(CareerRoleProfile.slug == item["slug"]))
        if not row:
            row = CareerRoleProfile(slug=item["slug"], title=item["title"], career_family=item["career_family"])
            db.add(row)
            created += 1
        else:
            updated += 1
        row.title = item["title"]
        row.career_family = item["career_family"]
        row.aliases_json = item["aliases"]
        row.summary = item["summary"]
        row.profile_json = item["profile"]
        row.status = "Curated"
        row.source_metadata_json = item["profile"]["source_metadata"]
        row.last_reviewed_date = item["profile"]["last_reviewed_date"]
        row.version = item["profile"]["version"]
        row.archived_at = None
        row.updated_at = _now()
        db.flush()
        existing_version = db.scalar(select(CareerRoleProfileVersion).where(CareerRoleProfileVersion.role_profile_id == row.id, CareerRoleProfileVersion.version_number == 1))
        if not existing_version:
            db.add(CareerRoleProfileVersion(role_profile_id=row.id, slug=row.slug, version_number=1, snapshot_json=career_role_public(row), change_reason="Initial curated role profile."))
    db.commit()
    return {"status": "ready", "created": created, "updated": updated, "role_count": len(career_role_catalogue())}


def career_role_public(row: CareerRoleProfile) -> dict[str, Any]:
    return {
        "id": row.id,
        "role_id": (row.profile_json or {}).get("role_id", row.slug),
        "slug": row.slug,
        "title": row.title,
        "aliases": row.aliases_json or [],
        "career_family": row.career_family,
        "summary": row.summary,
        "profile": row.profile_json or {},
        "status": row.status,
        "source_metadata": row.source_metadata_json or {},
        "last_reviewed_date": row.last_reviewed_date,
        "version": row.version,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def list_career_roles(db: Session, family: str | None = None, include_archived: bool = False) -> list[dict[str, Any]]:
    sync_career_encyclopedia(db)
    query = select(CareerRoleProfile)
    if family:
        query = query.where(CareerRoleProfile.career_family == family)
    if not include_archived:
        query = query.where(CareerRoleProfile.status != "Archived")
    rows = db.scalars(query.order_by(CareerRoleProfile.career_family, CareerRoleProfile.title)).all()
    return [career_role_public(row) for row in rows]


def get_career_role(db: Session, slug: str) -> dict[str, Any]:
    sync_career_encyclopedia(db)
    row = db.scalar(select(CareerRoleProfile).where(CareerRoleProfile.slug == slug))
    if not row or row.status == "Archived":
        raise LookupError("Career role profile not found")
    return career_role_public(row)


def career_role_compare(db: Session, profile: Profile, slug: str) -> dict[str, Any]:
    role = get_career_role(db, slug)
    passport = evidence_passport(db, profile.id)
    passport_skills = {str(item.get("skill_id") or item.get("skill_label", "")).lower(): item for item in passport.get("skills", [])}
    target_skills = [str(item).lower().replace(" ", "_") for item in role["profile"].get("technical_skills", [])[:8]]
    covered = [skill for skill in target_skills if skill in passport_skills or any(skill in key or key in skill for key in passport_skills)]
    missing = [skill for skill in target_skills if skill not in covered]
    applications = list_applications(db, profile.id)
    market_links = [app for app in applications if slug.replace("-", " ")[:10].lower() in (app.get("title") or "").lower()]
    return {
        "profile_id": profile.id,
        "career_slug": slug,
        "career_title": role["title"],
        "fit_dimensions": {
            "Personal Fit": {"label": "Exploratory", "reason": "Uses existing profile interests and career hypotheses; not a personality prediction."},
            "Capability Fit": {"label": "Partial" if missing else "Strong", "covered_skills": covered, "missing_skills": missing},
            "Market Fit": {"label": "Market-linked" if market_links else "Needs local market review", "linked_applications": market_links[:3]},
            "Support Fit": {"label": "Requires user confirmation", "reason": "Support routes and constraints are not inferred automatically."},
        },
        "evidence_passport_links": list(passport_skills.values())[:8],
        "recommended_experiments": role["profile"].get("recommended_career_experiments", []),
        "learning_objectives": role["profile"].get("related_learning_objectives", []),
        "status": "comparison_ready",
    }


def save_career_hypothesis(db: Session, profile: Profile, slug: str, user_id: str | None = None) -> dict[str, Any]:
    role = get_career_role(db, slug)
    existing = db.scalar(select(CareerHypothesis).where(CareerHypothesis.profile_id == profile.id, CareerHypothesis.role_template_id == slug, CareerHypothesis.status != "archived"))
    if existing:
        return {"id": existing.id, "status": existing.status, "title": existing.title, "created": False}
    row = CareerHypothesis(
        profile_id=profile.id,
        user_id=user_id or profile.user_id,
        role_template_id=slug,
        title=role["title"],
        role_family=role["career_family"],
        statement=f"Explore whether {role['title']} is supported by my evidence, experiments, market signals, and constraints.",
        status="active",
        source_metadata_json={"source": "career_encyclopedia", "career_slug": slug},
        demo_marker=_demo(profile),
    )
    db.add(row)
    db.commit()
    return {"id": row.id, "status": row.status, "title": row.title, "created": True}


def start_role_experiment(db: Session, profile: Profile, slug: str, user_id: str | None = None) -> dict[str, Any]:
    role = get_career_role(db, slug)
    templates = list_experiment_templates(db)
    recommended = role["profile"].get("recommended_career_experiments", [])
    template = next((item for item in templates if item.get("id") in recommended), None) or (templates[0] if templates else None)
    if not template:
        raise LookupError("No career experiment templates are available.")
    return create_experiment_session(db, profile, {"experiment_template_id": template["id"], "mode": "guided", "user_confirmed": True, "add_to_roadmap": False}, user_id or profile.user_id)


def upsert_career_role(db: Session, payload: dict[str, Any], archive: bool = False) -> dict[str, Any]:
    slug = _clean_text(payload.get("slug") or "", 180)
    if not slug:
        raise ValueError("Career role slug is required.")
    row = db.scalar(select(CareerRoleProfile).where(CareerRoleProfile.slug == slug)) or CareerRoleProfile(slug=slug, title=_clean_text(payload.get("title") or slug.replace("-", " ").title(), 255), career_family=_clean_text(payload.get("career_family") or "Internal", 160))
    db.add(row)
    before_version = db.scalar(select(func.max(CareerRoleProfileVersion.version_number)).where(CareerRoleProfileVersion.role_profile_id == row.id)) or 0
    row.title = _clean_text(payload.get("title") or row.title, 255)
    row.career_family = _clean_text(payload.get("career_family") or row.career_family, 160)
    row.aliases_json = _limited_list(payload.get("aliases") or row.aliases_json, 20)
    row.summary = _clean_text(payload.get("summary") or row.summary, 4000)
    row.profile_json = payload.get("profile") if isinstance(payload.get("profile"), dict) else row.profile_json
    row.status = "Archived" if archive else payload.get("status") or row.status or "Curated"
    row.archived_at = _now() if archive else None
    row.updated_at = _now()
    db.flush()
    db.add(CareerRoleProfileVersion(role_profile_id=row.id, slug=row.slug, version_number=int(before_version) + 1, snapshot_json=career_role_public(row), change_reason=payload.get("change_reason") or ("Archived role profile." if archive else "Role profile updated.")))
    db.commit()
    return career_role_public(row)


def journal_snapshot(row: CareerDecisionJournalEntry) -> dict[str, Any]:
    return {
        "title": row.title,
        "decision_type": row.decision_type,
        "status": row.status,
        "decision_summary": row.decision_summary,
        "context": row.context,
        "selected_option": row.selected_option,
        "options": row.options_json or [],
        "assumptions": row.assumptions_json or [],
        "evidence_links": row.evidence_links_json or [],
        "adviser_comment_ids": row.adviser_comment_ids_json or [],
        "career_slug": row.career_slug,
        "job_analysis_id": row.job_analysis_id,
        "application_id": row.application_id,
        "privacy_scope": row.privacy_scope,
        "review_date": row.review_date,
        "outcome_status": row.outcome_status,
        "outcome": row.outcome_json or {},
        "reconsideration_reason": row.reconsideration_reason,
        "roadmap_mutation_allowed": row.roadmap_mutation_allowed,
        "version_number": row.version_number,
    }


def journal_public(db: Session, row: CareerDecisionJournalEntry, include_versions: bool = False) -> dict[str, Any]:
    versions = []
    if include_versions:
        version_rows = db.scalars(select(CareerDecisionJournalVersion).where(CareerDecisionJournalVersion.entry_id == row.id).order_by(CareerDecisionJournalVersion.version_number)).all()
        versions = [{"id": item.id, "version_number": item.version_number, "snapshot": item.snapshot_json, "change_reason": item.change_reason, "created_at": item.created_at.isoformat()} for item in version_rows]
    reminder_status = "not_scheduled"
    if row.review_date:
        reminder_status = "due" if row.review_date <= _now().date().isoformat() and row.status == "active" else "scheduled"
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        **journal_snapshot(row),
        "reminder_status": reminder_status,
        "versions": versions,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def list_journal_entries(db: Session, profile: Profile) -> list[dict[str, Any]]:
    rows = db.scalars(select(CareerDecisionJournalEntry).where(CareerDecisionJournalEntry.profile_id == profile.id).order_by(CareerDecisionJournalEntry.updated_at.desc())).all()
    return [journal_public(db, row) for row in rows]


def create_journal_entry(db: Session, profile: Profile, payload: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
    row = CareerDecisionJournalEntry(
        profile_id=profile.id,
        user_id=user_id or profile.user_id,
        title=_clean_text(payload.get("title") or "Career decision", 255),
        decision_type=_clean_text(payload.get("decision_type") or "career_direction", 80),
        status=_clean_text(payload.get("status") or "active", 80),
        decision_summary=_clean_text(payload.get("decision_summary") or "", MAX_JOURNAL_TEXT_CHARS),
        context=_clean_text(payload.get("context") or "", MAX_JOURNAL_TEXT_CHARS),
        selected_option=_clean_text(payload.get("selected_option") or "", 255),
        options_json=_limited_list(payload.get("options"), 12),
        assumptions_json=_limited_list(payload.get("assumptions"), 24),
        evidence_links_json=_limited_list(payload.get("evidence_links"), 24),
        adviser_comment_ids_json=_limited_list(payload.get("adviser_comment_ids"), 20),
        career_slug=payload.get("career_slug"),
        job_analysis_id=payload.get("job_analysis_id"),
        application_id=payload.get("application_id"),
        privacy_scope=payload.get("privacy_scope") or "private",
        review_date=payload.get("review_date"),
        roadmap_mutation_allowed=False,
        demo_marker=_demo(profile),
    )
    db.add(row)
    db.flush()
    db.add(CareerDecisionJournalVersion(entry_id=row.id, profile_id=profile.id, version_number=1, snapshot_json=journal_snapshot(row), change_reason="Initial journal entry."))
    _audit(db, profile.id, "decision_journal_entry_created", "career_decision_journal_entry", row.id, "user", user_id or profile.user_id or "")
    db.commit()
    return journal_public(db, row, include_versions=True)


def get_journal_entry(db: Session, profile: Profile, entry_id: str) -> dict[str, Any]:
    row = db.get(CareerDecisionJournalEntry, entry_id)
    if not row or row.profile_id != profile.id:
        raise LookupError("Decision journal entry not found")
    return journal_public(db, row, include_versions=True)


def update_journal_entry(db: Session, profile: Profile, entry_id: str, payload: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
    row = db.get(CareerDecisionJournalEntry, entry_id)
    if not row or row.profile_id != profile.id:
        raise LookupError("Decision journal entry not found")
    for key, limit in [("title", 255), ("decision_type", 80), ("status", 80), ("decision_summary", MAX_JOURNAL_TEXT_CHARS), ("context", MAX_JOURNAL_TEXT_CHARS), ("selected_option", 255), ("privacy_scope", 80), ("reconsideration_reason", MAX_JOURNAL_TEXT_CHARS)]:
        if key in payload and payload[key] is not None:
            setattr(row, key, _clean_text(payload[key], limit))
    for source, target, limit in [("options", "options_json", 12), ("assumptions", "assumptions_json", 24), ("evidence_links", "evidence_links_json", 24), ("adviser_comment_ids", "adviser_comment_ids_json", 20)]:
        if source in payload:
            setattr(row, target, _limited_list(payload.get(source), limit))
    for key in ["career_slug", "job_analysis_id", "application_id", "review_date"]:
        if key in payload:
            setattr(row, key, payload.get(key))
    row.roadmap_mutation_allowed = False
    row.version_number += 1
    row.updated_at = _now()
    db.add(CareerDecisionJournalVersion(entry_id=row.id, profile_id=profile.id, version_number=row.version_number, snapshot_json=journal_snapshot(row), change_reason=payload.get("change_reason") or "Journal entry updated."))
    _audit(db, profile.id, "decision_journal_entry_updated", "career_decision_journal_entry", row.id, "user", user_id or profile.user_id or "", {"roadmap_mutated": False})
    db.commit()
    return journal_public(db, row, include_versions=True)


def record_journal_outcome(db: Session, profile: Profile, entry_id: str, payload: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
    row = db.get(CareerDecisionJournalEntry, entry_id)
    if not row or row.profile_id != profile.id:
        raise LookupError("Decision journal entry not found")
    row.outcome_status = _clean_text(payload.get("outcome_status") or "recorded", 80)
    row.outcome_json = {
        "recorded_at": _now().isoformat(),
        "expected_outcome": _clean_text(payload.get("expected_outcome") or "", 4000),
        "actual_outcome": _clean_text(payload.get("actual_outcome") or "", 4000),
        "assumptions_confirmed": _limited_list(payload.get("assumptions_confirmed"), 20),
        "assumptions_disconfirmed": _limited_list(payload.get("assumptions_disconfirmed"), 20),
        "next_decision_needed": bool(payload.get("next_decision_needed", False)),
        "roadmap_mutated": False,
    }
    row.status = payload.get("status") or ("reconsidered" if payload.get("next_decision_needed") else "outcome_recorded")
    row.version_number += 1
    row.updated_at = _now()
    db.add(CareerDecisionJournalVersion(entry_id=row.id, profile_id=profile.id, version_number=row.version_number, snapshot_json=journal_snapshot(row), change_reason="Decision outcome recorded."))
    _audit(db, profile.id, "decision_journal_outcome_recorded", "career_decision_journal_entry", row.id, "user", user_id or profile.user_id or "", {"roadmap_mutated": False})
    db.commit()
    return journal_public(db, row, include_versions=True)


def journal_research_export_preview(db: Session, profile: Profile) -> dict[str, Any]:
    rows = db.scalars(select(CareerDecisionJournalEntry).where(CareerDecisionJournalEntry.profile_id == profile.id)).all()
    return {
        "profile_id": profile.id,
        "schema_version": "decision-journal-research-export-v1",
        "raw_journal_text_included": False,
        "excluded_fields": ["decision_summary", "context", "raw_assumptions_text", "private_adviser_comments", "raw_journal_text"],
        "aggregate": {
            "entry_count": len(rows),
            "active_count": sum(1 for row in rows if row.status == "active"),
            "outcome_recorded_count": sum(1 for row in rows if row.outcome_status),
            "reconsidered_count": sum(1 for row in rows if row.status == "reconsidered"),
            "adviser_related_count": sum(1 for row in rows if row.adviser_comment_ids_json),
        },
    }


def seed_demo_innovation_extension(db: Session, user_id: str, profile: Profile) -> None:
    sync_career_encyclopedia(db)
    connection = BrowserExtensionConnection(
        profile_id=profile.id,
        user_id=user_id,
        token_hash=_hash("demo-extension-token"),
        display_name="Save to OrganicAI Compass demo extension",
        permissions_json=["activeTab", "storage", "scripting:user_triggered_visible_text"],
        expires_at=_now() + timedelta(days=14),
        last_used_at=_now(),
        demo_marker=True,
    )
    db.add(connection)
    db.flush()
    capture = BrowserJobCapture(
        profile_id=profile.id,
        user_id=user_id,
        extension_connection_id=connection.id,
        source_url="https://jobs.example.test/roles/ai-product-designer",
        page_title="AI Product Designer - Aurora Learning Lab",
        detected_title="AI Product Designer",
        detected_employer="Aurora Learning Lab",
        source_domain="jobs.example.test",
        captured_text_raw="Mandatory requirements include UX design, responsible AI, accessibility, evaluation and stakeholder communication.",
        sanitised_text="Mandatory requirements include UX design, responsible AI, accessibility, evaluation and stakeholder communication.",
        selected_text="UX design, responsible AI, accessibility.",
        confirmed_fields_json={"title": "AI Product Designer", "employer": "Aurora Learning Lab", "verified": False},
        requested_action="save_and_analyse",
        status="Analysed",
        content_hash=_hash("demo-capture"),
        extension_version="0.1.0",
        demo_marker=True,
    )
    db.add(capture)
    db.flush()
    try:
        analysis = create_job_analysis(db, profile, {"input_type": "browser_capture", "pasted_text": capture.sanitised_text, "title": capture.detected_title, "organisation": capture.detected_employer})
        analysis_row = db.get(JobAnalysis, analysis["id"])
        if analysis_row:
            analysis_row.source_url = capture.source_url
            capture.job_analysis_id = analysis_row.id
            match_analysis_evidence(db, analysis_row)
    except ValueError:
        pass
    share = AdvisorShare(
        profile_id=profile.id,
        user_id=user_id,
        token_hash=_hash("demo-advisor-token"),
        adviser_display_name="Dr. Ingrid Solheim",
        adviser_role="Academic supervisor",
        purpose="Review selected evidence and one AI Product Designer hypothesis.",
        permission_level="Suggest changes",
        allowed_sections_json=["Career Hypotheses", "Evidence Passport", "Job Analysis", "Career Decision Journal"],
        allowed_actions_json=["view", "comment", "suggest_changes", "validate_selected_evidence"],
        expires_at=_now() + timedelta(days=14),
        demo_marker=True,
    )
    db.add(share)
    db.flush()
    comments = [
        ("Evidence review", "The explainable recommendation prototype supports the UX evidence, but production claims should stay limited.", "Supports this evidence", "accepted"),
        ("Career-direction comment", "The AI Product Designer direction looks coherent if technical evaluation evidence is strengthened.", "Recommendation only", "pending"),
        ("Learning recommendation", "Add one small API evaluation task before presenting this role as a primary target.", "Recommendation only", "rejected"),
    ]
    for suggestion_type, text, validation, status in comments:
        db.add(AdvisorComment(share_id=share.id, profile_id=profile.id, adviser_display_name=share.adviser_display_name, adviser_role=share.adviser_role, suggestion_type=suggestion_type, comment_text=text, evidence_validation=validation, status=status, user_response="Demo user response." if status != "pending" else "", provenance="human_adviser"))
    interview = db.scalar(select(Interview).where(Interview.profile_id == profile.id).order_by(Interview.created_at.desc()))
    if interview:
        try:
            create_panel_session(db, interview, {"personas": ["recruiter", "hiring_manager", "technical_lead"], "delivery_mode": "text", "sequence_mode": "round_robin", "duration_minutes": 30, "difficulty": "moderate"})
        except ValueError:
            pass
    journal_payloads = [
        {"title": "Explore AI Product Designer as primary direction", "status": "active", "decision_summary": "Continue testing AI Product Designer with evidence-focused experiments.", "career_slug": "ai-product-designer", "review_date": "2026-08-15"},
        {"title": "Record outcome from first captured job", "status": "outcome_recorded", "decision_summary": "Apply only if evidence claims stay conservative.", "job_analysis_id": capture.job_analysis_id, "outcome_status": "recorded", "outcome": {"actual_outcome": "Application preparation improved, submission not automatic."}},
        {"title": "Reconsider consulting-first path", "status": "reconsidered", "decision_summary": "Consulting remains interesting but needs stronger stakeholder evidence.", "career_slug": "ai-integration-consultant", "reconsideration_reason": "Evidence gap discovered during adviser review."},
        {"title": "Adviser-related evidence decision", "status": "active", "decision_summary": "Accept adviser support for UX evidence but reject unsupported production wording.", "adviser_comment_ids": []},
        {"title": "Weekly reflection on career assumptions", "decision_type": "weekly_reflection", "status": "active", "decision_summary": "Assumption: visible portfolio evidence changes confidence more than abstract planning.", "assumptions": [{"text": "Portfolio evidence will clarify fit", "state": "testing"}]},
        {"title": "Keep RAG developer as secondary hypothesis", "status": "active", "decision_summary": "RAG development remains a secondary path pending deeper technical evidence.", "career_slug": "rag-application-developer"},
    ]
    comment_ids = [row.id for row in db.scalars(select(AdvisorComment).where(AdvisorComment.share_id == share.id)).all()]
    for payload in journal_payloads:
        if payload["title"].startswith("Adviser-related"):
            payload["adviser_comment_ids"] = comment_ids[:2]
        row = CareerDecisionJournalEntry(
            profile_id=profile.id,
            user_id=user_id,
            title=payload["title"],
            decision_type=payload.get("decision_type", "career_direction"),
            status=payload.get("status", "active"),
            decision_summary=payload.get("decision_summary", ""),
            assumptions_json=payload.get("assumptions", []),
            adviser_comment_ids_json=payload.get("adviser_comment_ids", []),
            career_slug=payload.get("career_slug"),
            job_analysis_id=payload.get("job_analysis_id"),
            review_date=payload.get("review_date"),
            outcome_status=payload.get("outcome_status", ""),
            outcome_json=payload.get("outcome", {}),
            reconsideration_reason=payload.get("reconsideration_reason", ""),
            demo_marker=True,
        )
        db.add(row)
        db.flush()
        db.add(CareerDecisionJournalVersion(entry_id=row.id, profile_id=profile.id, version_number=1, snapshot_json=journal_snapshot(row), change_reason="Demo seed entry."))
    db.commit()


def delete_innovation_extension_for_profiles(db: Session, profile_ids: list[str]) -> None:
    if not profile_ids:
        return
    share_ids = list(db.scalars(select(AdvisorShare.id).where(AdvisorShare.profile_id.in_(profile_ids))).all())
    journal_ids = list(db.scalars(select(CareerDecisionJournalEntry.id).where(CareerDecisionJournalEntry.profile_id.in_(profile_ids))).all())
    if share_ids:
        db.execute(delete(AdvisorComment).where(AdvisorComment.share_id.in_(share_ids)))
        db.execute(delete(AdvisorShare).where(AdvisorShare.id.in_(share_ids)))
    if journal_ids:
        db.execute(delete(CareerDecisionJournalVersion).where(CareerDecisionJournalVersion.entry_id.in_(journal_ids)))
        db.execute(delete(CareerDecisionJournalEntry).where(CareerDecisionJournalEntry.id.in_(journal_ids)))
    db.execute(delete(BrowserJobCapture).where(BrowserJobCapture.profile_id.in_(profile_ids)))
    db.execute(delete(BrowserExtensionConnection).where(BrowserExtensionConnection.profile_id.in_(profile_ids)))
    db.execute(delete(InnovationAuditEvent).where(InnovationAuditEvent.profile_id.in_(profile_ids)))

