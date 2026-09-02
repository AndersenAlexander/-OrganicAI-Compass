from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_optional_user
from app.database import get_db
from app.models.interview_journey import VoiceProviderSession
from app.models.profile import Profile
from app.models.user import User
from app.services.profile_authorization import require_owned_profile
from app.services.interview_journey_engine import (
    build_answer,
    build_personal_introduction,
    case_templates,
    complete_mock_session,
    complete_voice_session,
    compare_offer_reviews,
    create_custom_question,
    create_decision_journal_hook,
    create_follow_up_draft,
    create_interview,
    create_mock_session,
    create_offer_review,
    create_reflection,
    create_star_story,
    create_voice_session,
    delete_interview,
    delete_mock_session,
    delete_star_story,
    delete_voice_session,
    decide_interview_recalibration,
    evaluate_star_story,
    generate_interview_questions,
    generate_preparation_brief,
    get_mock_feedback,
    get_preparation_brief,
    get_reflection,
    interview_dashboard,
    interview_public,
    interview_voice_status,
    list_follow_up_drafts,
    list_interview_questions,
    list_interviews,
    list_interview_recalibration_proposals,
    list_mock_sessions,
    list_offer_reviews,
    list_star_stories,
    mock_session_public,
    offer_review_public,
    portfolio_preparation,
    record_interview_application_event,
    record_interview_outcome,
    require_interview,
    require_mock_session,
    require_offer_review,
    require_question,
    require_star_story,
    save_question,
    start_mock_session,
    star_story_public,
    update_interview,
    update_interview_question,
    update_offer_review,
    update_star_story,
    adapt_star_story,
    update_voice_transcript,
    add_mock_turn,
)

router = APIRouter()


class DictRequest(BaseModel):
    model_config = {"extra": "allow"}


class InterviewRequest(DictRequest):
    application_id: str | None = None
    job_analysis_id: str | None = None
    organisation: str | None = None
    role: str | None = None
    stage_type: str = "recruiter_screening"
    scheduled_at: str | None = None
    timezone: str = "Europe/Bucharest"
    location_or_platform: str = ""
    interview_format: str = "unknown"
    expected_duration_minutes: int | None = Field(default=None, ge=1, le=600)
    participants: list[dict[str, Any]] = Field(default_factory=list)
    notes: str = ""
    source: str = "manual"
    user_confirmed: bool = False


class StarStoryRequest(DictRequest):
    title: str
    situation: str = ""
    task: str = ""
    action: str = ""
    result: str = ""
    reflection: str = ""
    skills_demonstrated: list[str] = Field(default_factory=list)
    related_job_requirements: list[dict[str, Any]] = Field(default_factory=list)
    evidence_links: list[dict[str, Any]] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    confidentiality_status: str = "review_needed"
    user_confirmed: bool = False


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


def check_profile_row(db: Session, profile_id: str, user: User | None) -> Profile:
    return require_profile(db, profile_id, user)


def check_interview(db: Session, interview_id: str, user: User | None):
    interview = require_interview(db, interview_id)
    check_profile_row(db, interview.profile_id, user)
    return interview


@router.get("/profiles/{profile_id}/interviews/dashboard")
async def get_interview_dashboard(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any] | None:
    profile = require_profile(db, profile_id, user)
    return interview_dashboard(db, profile)


@router.get("/profiles/{profile_id}/interviews")
async def get_interviews(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> list[dict[str, Any]]:
    require_profile(db, profile_id, user)
    return list_interviews(db, profile_id)


@router.post("/profiles/{profile_id}/interviews")
async def post_interview(
    profile_id: str,
    payload: InterviewRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any] | None:
    profile = require_profile(db, profile_id, user)
    try:
        return create_interview(db, profile, payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.get("/interviews/{interview_id}")
async def get_interview(
    interview_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        interview = check_interview(db, interview_id, user)
        return interview_public(db, interview, include_details=True)
    except Exception as error:
        _handle(error)
        raise


@router.put("/interviews/{interview_id}")
async def put_interview(
    interview_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        return update_interview(db, check_interview(db, interview_id, user), payload.model_dump(exclude_none=True))
    except Exception as error:
        _handle(error)
        raise


@router.delete("/interviews/{interview_id}")
async def delete_interview_route(
    interview_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        return delete_interview(db, check_interview(db, interview_id, user))
    except Exception as error:
        _handle(error)
        raise


@router.post("/interviews/{interview_id}/preparation")
async def post_preparation(
    interview_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        return generate_preparation_brief(db, check_interview(db, interview_id, user), payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.get("/interviews/{interview_id}/preparation", response_model=None)
async def get_preparation(
    interview_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> Any:
    try:
        result = get_preparation_brief(db, check_interview(db, interview_id, user))
        return result if result is not None else JSONResponse(content=None)
    except Exception as error:
        _handle(error)
        raise


@router.get("/interviews/{interview_id}/introduction")
async def get_introduction(
    interview_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
    language: str = "en",
) -> dict[str, Any]:
    try:
        return build_personal_introduction(db, check_interview(db, interview_id, user), language)
    except Exception as error:
        _handle(error)
        raise


@router.post("/interviews/{interview_id}/questions/generate")
async def post_questions_generate(
    interview_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        return generate_interview_questions(db, check_interview(db, interview_id, user), payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.get("/interviews/{interview_id}/questions")
async def get_questions(
    interview_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> list[dict[str, Any]]:
    try:
        return list_interview_questions(db, check_interview(db, interview_id, user))
    except Exception as error:
        _handle(error)
        raise


@router.post("/interview-questions/{question_id}/save")
async def post_question_save(
    question_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        question = require_question(db, question_id)
        check_profile_row(db, question.profile_id, user)
        return save_question(db, question, bool(payload.model_dump().get("saved", True)))
    except Exception as error:
        _handle(error)
        raise


@router.put("/interview-questions/{question_id}")
async def put_question(
    question_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        question = require_question(db, question_id)
        check_profile_row(db, question.profile_id, user)
        return update_interview_question(db, question, payload.model_dump(exclude_none=True))
    except Exception as error:
        _handle(error)
        raise


@router.post("/interviews/{interview_id}/questions/custom")
async def post_custom_question(
    interview_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        return create_custom_question(db, check_interview(db, interview_id, user), payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.post("/interview-questions/{question_id}/answer")
async def post_question_answer(
    question_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        question = require_question(db, question_id)
        check_profile_row(db, question.profile_id, user)
        return build_answer(db, question, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/star-stories")
async def get_star_stories(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> list[dict[str, Any]]:
    require_profile(db, profile_id, user)
    return list_star_stories(db, profile_id)


@router.post("/profiles/{profile_id}/star-stories")
async def post_star_story(
    profile_id: str,
    payload: StarStoryRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return create_star_story(db, profile, payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.get("/star-stories/{story_id}")
async def get_star_story(
    story_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        story = require_star_story(db, story_id)
        check_profile_row(db, story.profile_id, user)
        return star_story_public(story)
    except Exception as error:
        _handle(error)
        raise


@router.put("/star-stories/{story_id}")
async def put_star_story(
    story_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        story = require_star_story(db, story_id)
        check_profile_row(db, story.profile_id, user)
        return update_star_story(db, story, payload.model_dump(exclude_none=True))
    except Exception as error:
        _handle(error)
        raise


@router.delete("/star-stories/{story_id}")
async def delete_star_story_route(
    story_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        story = require_star_story(db, story_id)
        check_profile_row(db, story.profile_id, user)
        return delete_star_story(db, story)
    except Exception as error:
        _handle(error)
        raise


@router.post("/star-stories/{story_id}/evaluate")
async def post_star_story_evaluate(
    story_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        story = require_star_story(db, story_id)
        check_profile_row(db, story.profile_id, user)
        return evaluate_star_story(db, story)
    except Exception as error:
        _handle(error)
        raise


@router.post("/star-stories/{story_id}/adapt")
async def post_star_story_adapt(
    story_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        story = require_star_story(db, story_id)
        check_profile_row(db, story.profile_id, user)
        return adapt_star_story(db, story, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.post("/interviews/{interview_id}/mock-sessions")
async def post_mock_session(
    interview_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        return create_mock_session(db, check_interview(db, interview_id, user), payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.get("/interviews/{interview_id}/mock-sessions")
async def get_mock_sessions(
    interview_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> list[dict[str, Any]]:
    try:
        return list_mock_sessions(db, check_interview(db, interview_id, user))
    except Exception as error:
        _handle(error)
        raise


@router.get("/mock-sessions/{session_id}")
async def get_mock_session(
    session_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        session = require_mock_session(db, session_id)
        check_profile_row(db, session.profile_id, user)
        return mock_session_public(db, session)
    except Exception as error:
        _handle(error)
        raise


@router.post("/mock-sessions/{session_id}/start")
async def post_mock_start(
    session_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        session = require_mock_session(db, session_id)
        check_profile_row(db, session.profile_id, user)
        return start_mock_session(db, session)
    except Exception as error:
        _handle(error)
        raise


@router.post("/mock-sessions/{session_id}/turns")
async def post_mock_turn(
    session_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        session = require_mock_session(db, session_id)
        check_profile_row(db, session.profile_id, user)
        return add_mock_turn(db, session, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.post("/mock-sessions/{session_id}/complete")
async def post_mock_complete(
    session_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        session = require_mock_session(db, session_id)
        check_profile_row(db, session.profile_id, user)
        return complete_mock_session(db, session, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.post("/mock-sessions/{session_id}/feedback")
async def post_mock_feedback(
    session_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        session = require_mock_session(db, session_id)
        check_profile_row(db, session.profile_id, user)
        return get_mock_feedback(db, session)
    except Exception as error:
        _handle(error)
        raise


@router.delete("/mock-sessions/{session_id}")
async def delete_mock_session_route(
    session_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        session = require_mock_session(db, session_id)
        check_profile_row(db, session.profile_id, user)
        return delete_mock_session(db, session)
    except Exception as error:
        _handle(error)
        raise


@router.get("/interview-voice/status")
async def get_voice_status() -> dict[str, Any]:
    return interview_voice_status()


@router.post("/interview-voice/sessions")
async def post_voice_session(
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        data = payload.model_dump()
        profile = require_profile(db, data.get("profile_id") or "", user)
        return create_voice_session(db, profile, data)
    except Exception as error:
        _handle(error)
        raise


def check_voice_session(db: Session, session_id: str, user: User | None) -> VoiceProviderSession:
    row = db.get(VoiceProviderSession, session_id)
    if not row:
        raise LookupError("Voice session not found")
    check_profile_row(db, row.profile_id, user)
    return row


@router.post("/interview-voice/sessions/{session_id}/complete")
async def post_voice_complete(
    session_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        return complete_voice_session(db, check_voice_session(db, session_id, user), payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.put("/interview-voice/sessions/{session_id}/transcript")
async def put_voice_transcript(
    session_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        return update_voice_transcript(db, check_voice_session(db, session_id, user), payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.delete("/interview-voice/sessions/{session_id}")
async def delete_voice_route(
    session_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        return delete_voice_session(db, check_voice_session(db, session_id, user))
    except Exception as error:
        _handle(error)
        raise


@router.post("/interviews/{interview_id}/reflection")
async def post_reflection(
    interview_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        return create_reflection(db, check_interview(db, interview_id, user), payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.get("/interviews/{interview_id}/reflection", response_model=None)
async def get_reflection_route(
    interview_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> Any:
    try:
        result = get_reflection(db, check_interview(db, interview_id, user))
        return result if result is not None else JSONResponse(content=None)
    except Exception as error:
        _handle(error)
        raise


@router.post("/interviews/{interview_id}/outcome")
async def post_interview_outcome(
    interview_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        return record_interview_outcome(db, check_interview(db, interview_id, user), payload.model_dump(), user.id if user else None)
    except Exception as error:
        _handle(error)
        raise


@router.get("/interviews/{interview_id}/recalibration-proposals")
async def get_interview_recalibration_proposals(
    interview_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> list[dict[str, Any]]:
    try:
        return list_interview_recalibration_proposals(db, check_interview(db, interview_id, user))
    except Exception as error:
        _handle(error)
        raise


@router.post("/interviews/{interview_id}/recalibration-proposals/{proposal_id}/decision")
async def post_interview_recalibration_decision(
    interview_id: str,
    proposal_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        interview = check_interview(db, interview_id, user)
        from app.models.market_application import ApplicationRecalibrationRun

        proposal = db.get(ApplicationRecalibrationRun, proposal_id)
        if not proposal or proposal.interview_id != interview.id:
            raise LookupError("Recalibration proposal not found")
        return decide_interview_recalibration(db, proposal, payload.model_dump(), user.id if user else None)
    except Exception as error:
        _handle(error)
        raise


@router.post("/interviews/{interview_id}/decision-journal")
async def post_interview_decision_journal(
    interview_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        return create_decision_journal_hook(db, check_interview(db, interview_id, user), payload.model_dump(), user.id if user else None)
    except Exception as error:
        _handle(error)
        raise


@router.post("/interviews/{interview_id}/follow-up-drafts")
async def post_follow_up(
    interview_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        return create_follow_up_draft(db, check_interview(db, interview_id, user), payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.get("/interviews/{interview_id}/follow-up-drafts")
async def get_follow_ups(
    interview_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> list[dict[str, Any]]:
    try:
        return list_follow_up_drafts(db, check_interview(db, interview_id, user))
    except Exception as error:
        _handle(error)
        raise


@router.post("/interviews/{interview_id}/application-events")
async def post_interview_application_event(
    interview_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        return record_interview_application_event(db, check_interview(db, interview_id, user), payload.model_dump(), user.id if user else None)
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/offer-reviews")
async def get_offer_reviews(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> list[dict[str, Any]]:
    require_profile(db, profile_id, user)
    return list_offer_reviews(db, profile_id)


@router.post("/profiles/{profile_id}/offer-reviews/compare")
async def post_offer_review_compare(
    profile_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return compare_offer_reviews(db, profile, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/offer-reviews")
async def post_offer_review(
    profile_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return create_offer_review(db, profile, payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.get("/offer-reviews/{review_id}")
async def get_offer_review(
    review_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        row = require_offer_review(db, review_id)
        check_profile_row(db, row.profile_id, user)
        return offer_review_public(row)
    except Exception as error:
        _handle(error)
        raise


@router.put("/offer-reviews/{review_id}")
async def put_offer_review(
    review_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    try:
        row = require_offer_review(db, review_id)
        check_profile_row(db, row.profile_id, user)
        return update_offer_review(db, row, payload.model_dump(exclude_none=True))
    except Exception as error:
        _handle(error)
        raise


@router.get("/interview-case-templates")
async def get_case_templates() -> list[dict[str, Any]]:
    return case_templates()


@router.get("/profiles/{profile_id}/portfolio-preparation")
async def get_portfolio_preparation(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    return portfolio_preparation(db, profile)
