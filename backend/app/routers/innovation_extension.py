from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import bearer_scheme, get_current_user, get_optional_user, require_admin_user
from app.database import get_db
from app.models.interview_journey import MockInterviewSession
from app.models.profile import Profile
from app.models.user import User
from app.services.profile_authorization import require_owned_profile
from app.services.innovation_extension_engine import (
    add_panel_turn,
    advisor_review,
    career_role_compare,
    complete_panel_session,
    confirm_job_capture,
    create_advisor_share,
    create_extension_connection,
    create_job_capture,
    create_journal_entry,
    create_panel_session,
    get_advisor_share,
    get_career_role,
    get_journal_entry,
    journal_research_export_preview,
    list_advisor_shares,
    list_career_roles,
    list_extension_connections,
    list_job_captures,
    list_journal_entries,
    panel_personas,
    panel_session_public,
    record_journal_outcome,
    respond_to_advisor_comment,
    revoke_advisor_share,
    revoke_extension_connection,
    save_career_hypothesis,
    start_role_experiment,
    submit_advisor_comment,
    sync_career_encyclopedia,
    upsert_career_role,
    update_journal_entry,
    validate_extension_token,
    validate_extension_capture_context,
)
from app.services.interview_journey_engine import require_interview

router = APIRouter()


class DictRequest(BaseModel):
    model_config = {"extra": "allow"}


class ExtensionConnectionRequest(DictRequest):
    display_name: str = "Save to OrganicAI Compass"
    expires_in_days: int = Field(default=14, ge=1, le=90)


class JobCaptureRequest(DictRequest):
    source_url: str
    page_title: str = ""
    captured_text: str = ""
    selected_text: str = ""
    source_domain: str = ""
    capture_method: str = "user_triggered_browser_extension"
    requested_action: str = "save"
    extension_version: str = "unknown"
    title: str | None = None
    employer: str | None = None


class AdvisorShareRequest(DictRequest):
    adviser_display_name: str = "External adviser"
    adviser_role: str = "Other"
    purpose: str = ""
    permission_level: str = "View only"
    allowed_sections: list[str] = Field(default_factory=list)
    allowed_actions: list[str] = Field(default_factory=list)
    access_days: int = Field(default=14, ge=1, le=90)
    max_access_attempts: int = Field(default=20, ge=3, le=100)
    export_allowed: bool = False
    pin: str | None = None


class AdvisorCommentRequest(DictRequest):
    target_type: str = "share"
    target_id: str = ""
    suggestion_type: str = "General comment"
    comment_text: str
    evidence_validation: str = "Recommendation only"
    supporting_reference: str = ""
    pin: str | None = None


class PanelSessionRequest(DictRequest):
    personas: list[str]
    language: str = "en"
    mode: str = "panel_simulation"
    delivery_mode: str = "text"
    duration_minutes: int = Field(default=30, ge=10, le=120)
    difficulty: str = "moderate"
    sequence_mode: str = "round_robin"
    custom_order: list[str] = Field(default_factory=list)
    evidence_focus: list[str] = Field(default_factory=list)
    follow_up_questions_enabled: bool = True


class JournalRequest(DictRequest):
    title: str
    decision_type: str = "career_direction"
    status: str = "active"
    decision_summary: str = ""
    context: str = ""
    selected_option: str = ""
    options: list[dict[str, Any]] = Field(default_factory=list)
    assumptions: list[dict[str, Any]] = Field(default_factory=list)
    evidence_links: list[dict[str, Any]] = Field(default_factory=list)
    adviser_comment_ids: list[str] = Field(default_factory=list)
    career_slug: str | None = None
    job_analysis_id: str | None = None
    application_id: str | None = None
    privacy_scope: str = "private"
    review_date: str | None = None


def _handle(error: Exception) -> None:
    if isinstance(error, LookupError):
        raise HTTPException(404, str(error))
    if isinstance(error, PermissionError):
        raise HTTPException(403, str(error))
    if isinstance(error, ValueError):
        raise HTTPException(422, str(error))
    raise error


def require_profile(db: Session, profile_id: str, user: User | None) -> Profile:
    return require_owned_profile(db, profile_id, user)


def require_user_or_extension(user: User | None, extension_token: str | None) -> None:
    if user is None and not extension_token:
        raise HTTPException(401, "Authentication or an extension connection token is required.")


def get_optional_user_for_extension_capture(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    if credentials is None:
        return None
    return get_current_user(credentials, db)


@router.post("/profiles/{profile_id}/browser-extension/connection")
async def post_extension_connection(
    profile_id: str,
    payload: ExtensionConnectionRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    return create_extension_connection(db, profile, payload.model_dump(), user.id if user else profile.user_id)


@router.get("/profiles/{profile_id}/browser-extension/connection")
async def get_extension_connections(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    return list_extension_connections(db, profile)


@router.delete("/profiles/{profile_id}/browser-extension/connection/{connection_id}")
async def delete_extension_connection(
    profile_id: str,
    connection_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return revoke_extension_connection(db, profile, connection_id, user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/browser-extension/settings")
async def get_extension_settings(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    status = list_extension_connections(db, profile)
    return {
        **status,
        "installation_instructions": [
            "Build the browser-extension package.",
            "Load the generated extension folder using Chrome or Edge developer mode.",
            "Create an OrganicAI Compass connection token from this settings page.",
            "Paste the token into the extension popup.",
        ],
        "privacy_explanation": "Capture is user-triggered. The extension captures the current URL, page title, selected text, and visible text only after the user presses the extension action.",
    }


@router.post("/profiles/{profile_id}/job-captures")
async def post_job_capture(
    profile_id: str,
    payload: JobCaptureRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user_for_extension_capture)],
    x_organicai_extension_token: Annotated[str | None, Header(alias="X-OrganicAI-Extension-Token")] = None,
) -> dict[str, Any]:
    try:
        if x_organicai_extension_token:
            profile, connection = validate_extension_capture_context(db, profile_id, x_organicai_extension_token, user.id if user else None)
            return create_job_capture(db, profile, payload.model_dump(), connection, connection.user_id or profile.user_id)
        profile = require_profile(db, profile_id, user)
        return create_job_capture(db, profile, payload.model_dump(), None, user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/job-captures")
async def get_job_captures(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> list[dict[str, Any]]:
    profile = require_profile(db, profile_id, user)
    return list_job_captures(db, profile)


@router.post("/profiles/{profile_id}/job-captures/{capture_id}/confirm")
async def post_capture_confirm(
    profile_id: str,
    capture_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return confirm_job_capture(db, profile, capture_id, payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/advisor-shares")
async def post_advisor_share(
    profile_id: str,
    payload: AdvisorShareRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return create_advisor_share(db, profile, payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/advisor-shares")
async def get_advisor_shares(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> list[dict[str, Any]]:
    profile = require_profile(db, profile_id, user)
    return list_advisor_shares(db, profile)


@router.get("/profiles/{profile_id}/advisor-shares/{share_id}")
async def get_advisor_share_route(
    profile_id: str,
    share_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return get_advisor_share(db, profile, share_id)
    except Exception as error:
        _handle(error)
        raise


@router.delete("/profiles/{profile_id}/advisor-shares/{share_id}")
async def delete_advisor_share_route(
    profile_id: str,
    share_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return revoke_advisor_share(db, profile, share_id, user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.patch("/profiles/{profile_id}/advisor-comments/{comment_id}")
async def patch_advisor_comment(
    profile_id: str,
    comment_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return respond_to_advisor_comment(db, profile, comment_id, payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.get("/advisor-review/{share_token}")
async def get_advisor_review_route(
    share_token: str,
    db: Annotated[Session, Depends(get_db)],
    pin: str | None = Query(default=None),
) -> dict[str, Any]:
    try:
        return advisor_review(db, share_token, pin)
    except Exception as error:
        _handle(error)
        raise


@router.post("/advisor-review/{share_token}/comments")
async def post_advisor_review_comment(
    share_token: str,
    payload: AdvisorCommentRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    try:
        return submit_advisor_comment(db, share_token, payload.model_dump(), payload.pin)
    except Exception as error:
        _handle(error)
        raise


@router.get("/interviews/panel-personas")
async def get_panel_personas() -> list[dict[str, Any]]:
    return panel_personas()


@router.post("/interviews/{interview_id}/panel-simulation")
async def post_panel_simulation(
    interview_id: str,
    payload: PanelSessionRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        interview = require_interview(db, interview_id)
        require_profile(db, interview.profile_id, user)
        return create_panel_session(db, interview, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.get("/mock-sessions/{session_id}/panel")
async def get_panel_session(
    session_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    session = db.get(MockInterviewSession, session_id)
    if not session:
        raise HTTPException(404, "Panel session not found")
    require_profile(db, session.profile_id, user)
    return panel_session_public(db, session)


@router.post("/mock-sessions/{session_id}/panel-turns")
async def post_panel_turn(
    session_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    session = db.get(MockInterviewSession, session_id)
    if not session:
        raise HTTPException(404, "Panel session not found")
    require_profile(db, session.profile_id, user)
    try:
        return add_panel_turn(db, session, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.post("/mock-sessions/{session_id}/panel-complete")
async def post_panel_complete(
    session_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    session = db.get(MockInterviewSession, session_id)
    if not session:
        raise HTTPException(404, "Panel session not found")
    require_profile(db, session.profile_id, user)
    try:
        return complete_panel_session(db, session, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.get("/careers")
async def get_careers(
    db: Annotated[Session, Depends(get_db)],
    family: str | None = None,
) -> list[dict[str, Any]]:
    return list_career_roles(db, family)


@router.get("/careers/{career_slug}")
async def get_career(career_slug: str, db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    try:
        return get_career_role(db, career_slug)
    except Exception as error:
        _handle(error)
        raise


@router.post("/admin/career-encyclopedia/sync")
async def post_career_sync(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin_user)],
) -> dict[str, Any]:
    return sync_career_encyclopedia(db)


@router.post("/admin/career-encyclopedia/roles")
async def post_career_role(
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin_user)],
) -> dict[str, Any]:
    try:
        return upsert_career_role(db, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.put("/admin/career-encyclopedia/roles/{career_slug}")
async def put_career_role(
    career_slug: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin_user)],
) -> dict[str, Any]:
    data = payload.model_dump()
    data["slug"] = career_slug
    try:
        return upsert_career_role(db, data)
    except Exception as error:
        _handle(error)
        raise


@router.delete("/admin/career-encyclopedia/roles/{career_slug}")
async def delete_career_role(
    career_slug: str,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin_user)],
) -> dict[str, Any]:
    try:
        return upsert_career_role(db, {"slug": career_slug}, archive=True)
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/career-encyclopedia")
async def get_profile_careers(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
    family: str | None = None,
) -> list[dict[str, Any]]:
    require_profile(db, profile_id, user)
    return list_career_roles(db, family)


@router.get("/profiles/{profile_id}/career-encyclopedia/{career_slug}")
async def get_profile_career(
    profile_id: str,
    career_slug: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    require_profile(db, profile_id, user)
    try:
        return get_career_role(db, career_slug)
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/career-encyclopedia/{career_slug}/compare")
async def get_career_compare(
    profile_id: str,
    career_slug: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return career_role_compare(db, profile, career_slug)
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/career-encyclopedia/{career_slug}/hypothesis")
async def post_career_hypothesis(
    profile_id: str,
    career_slug: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return save_career_hypothesis(db, profile, career_slug, user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/career-encyclopedia/{career_slug}/experiment")
async def post_career_experiment(
    profile_id: str,
    career_slug: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return start_role_experiment(db, profile, career_slug, user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/decision-journal")
async def get_decision_journal(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> list[dict[str, Any]]:
    profile = require_profile(db, profile_id, user)
    return list_journal_entries(db, profile)


@router.post("/profiles/{profile_id}/decision-journal")
async def post_decision_journal(
    profile_id: str,
    payload: JournalRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return create_journal_entry(db, profile, payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/decision-journal/research-export")
async def get_decision_journal_export(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    return journal_research_export_preview(db, profile)


@router.get("/profiles/{profile_id}/decision-journal/{entry_id}")
async def get_decision_entry(
    profile_id: str,
    entry_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return get_journal_entry(db, profile, entry_id)
    except Exception as error:
        _handle(error)
        raise


@router.put("/profiles/{profile_id}/decision-journal/{entry_id}")
async def put_decision_entry(
    profile_id: str,
    entry_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return update_journal_entry(db, profile, entry_id, payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/decision-journal/{entry_id}/outcome")
async def post_decision_outcome(
    profile_id: str,
    entry_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return record_journal_outcome(db, profile, entry_id, payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise
