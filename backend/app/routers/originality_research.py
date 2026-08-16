from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_optional_user, require_admin_user
from app.database import get_db
from app.models.originality_research import (
    AdaptiveExperimentRecommendation,
    CareerTransitionPath,
    CareerTransitionSimulation,
    RecommendationRobustnessRun,
    ResearchOriginalitySession,
)
from app.models.profile import Profile
from app.models.user import User
from app.services.profile_authorization import is_admin_user, require_owned_profile
from app.services.research_readiness import assert_research_ready
from app.services.originality_research_engine import (
    adaptive_alternatives,
    adaptive_recommendation_action,
    archive_transition_simulation,
    analyse_adaptive_experiments,
    compare_transition_scenarios,
    create_originality_research_session,
    create_transition_simulation,
    discover_evidence_gaps,
    ensure_system_card_version,
    fairness_audit_failures,
    fairness_audit_limitations,
    fairness_audit_public,
    fairness_test_suites,
    get_adaptive_recommendation,
    get_evidence_capture_proposal,
    get_fairness_audit,
    get_robustness_run,
    get_transition_simulation,
    list_adaptive_experiments,
    list_fairness_audits,
    list_robustness_runs,
    list_transition_simulations,
    originality_session_results,
    path_to_decision_journal,
    propose_roadmap_for_path,
    record_adaptive_outcome,
    recommendation_provenance,
    reset_synthetic_fairness_lab,
    recommendation_system_card,
    rerun_transition_simulation,
    review_evidence_capture_proposal,
    robustness_dependencies,
    run_fairness_audit,
    run_recommendation_robustness,
    transition_adaptive_lifecycle,
    transition_pareto_front,
    transition_presets,
    update_transition_constraints,
    update_originality_baseline,
    update_originality_experimental,
    update_originality_feedback,
)

router = APIRouter()


class DictRequest(BaseModel):
    model_config = {"extra": "allow"}


class AdaptiveAnalyseRequest(DictRequest):
    weekly_learning_time: int = Field(default=8, ge=0, le=80)
    learning_budget: int = Field(default=50, ge=0, le=10000)
    remote_work_preference: str = "hybrid"
    preferred_languages: list[str] = Field(default_factory=lambda: ["English"])


class RecommendationActionRequest(DictRequest):
    reason: str | None = None
    note: str = ""
    add_to_roadmap: bool = False
    mode: str = "guided"


class AdaptiveLifecycleRequest(DictRequest):
    status: str
    note: str = ""


class EvidenceCaptureReviewRequest(DictRequest):
    decision: str
    note: str = ""


class TransitionSimulationRequest(DictRequest):
    scenario_name: str = "Balanced transition"
    preset: str = "balanced_transition"
    controls: dict[str, Any] = Field(default_factory=dict)
    selected_objectives: list[str] = Field(default_factory=list)
    priority_preferences: dict[str, float] = Field(default_factory=dict)
    save_scenario: bool = False


class ResearchSessionRequest(DictRequest):
    profile_id: str | None = None
    consent_confirmed: bool = False
    assigned_condition: str = "experimental"


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


def require_originality_session_access(db: Session, session_id: str, user: User | None) -> ResearchOriginalitySession:
    row = db.get(ResearchOriginalitySession, session_id)
    if not row:
        raise HTTPException(404, "Originality research session not found")
    if row.profile_id:
        require_profile(db, row.profile_id, user)
        return row
    if row.user_id:
        if not user:
            raise HTTPException(401, "Authentication required.")
        if row.user_id != user.id and not is_admin_user(user):
            raise HTTPException(403, "Not authorized for this originality research session.")
        return row
    if not user:
        raise HTTPException(401, "Authentication required.")
    if not is_admin_user(user):
        raise HTTPException(403, "Admin access required for orphan originality research sessions.")
    return row


def require_recommendation_profile(db: Session, recommendation_id: str, user: User | None) -> Profile:
    row = db.get(AdaptiveExperimentRecommendation, recommendation_id)
    if not row:
        raise HTTPException(404, "Adaptive experiment recommendation not found")
    return require_profile(db, row.profile_id, user)


def require_simulation_profile(db: Session, simulation_id: str, user: User | None) -> Profile:
    row = db.get(CareerTransitionSimulation, simulation_id)
    if not row:
        raise HTTPException(404, "Transition simulation not found")
    return require_profile(db, row.profile_id, user)


def require_path_profile(db: Session, path_id: str, user: User | None) -> Profile:
    row = db.get(CareerTransitionPath, path_id)
    if not row:
        raise HTTPException(404, "Transition path not found")
    return require_profile(db, row.profile_id, user)


def require_robustness_profile(db: Session, run_id: str, user: User | None) -> Profile:
    row = db.get(RecommendationRobustnessRun, run_id)
    if not row:
        raise HTTPException(404, "Recommendation robustness run not found")
    return require_profile(db, row.profile_id, user)


@router.post("/profiles/{profile_id}/adaptive-experiments/analyse")
async def post_adaptive_analyse(
    profile_id: str,
    payload: AdaptiveAnalyseRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return analyse_adaptive_experiments(db, profile, payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/evidence-gaps")
async def get_profile_evidence_gaps(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return discover_evidence_gaps(db, profile)
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/adaptive-experiments")
async def get_adaptive_profile_recommendations(
    profile_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> list[dict[str, Any]]:
    profile = require_profile(db, profile_id, user)
    return list_adaptive_experiments(db, profile)


@router.get("/adaptive-experiments/{recommendation_id}")
async def get_adaptive_recommendation_route(
    recommendation_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_recommendation_profile(db, recommendation_id, user)
    try:
        return get_adaptive_recommendation(db, recommendation_id, profile)
    except Exception as error:
        _handle(error)
        raise


@router.post("/adaptive-experiments/{recommendation_id}/accept")
async def post_adaptive_accept(recommendation_id: str, payload: RecommendationActionRequest, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    profile = require_recommendation_profile(db, recommendation_id, user)
    try:
        return adaptive_recommendation_action(db, recommendation_id, "accept", payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.post("/adaptive-experiments/{recommendation_id}/reject")
async def post_adaptive_reject(recommendation_id: str, payload: RecommendationActionRequest, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    profile = require_recommendation_profile(db, recommendation_id, user)
    try:
        return adaptive_recommendation_action(db, recommendation_id, "reject", payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.post("/adaptive-experiments/{recommendation_id}/save")
async def post_adaptive_save(recommendation_id: str, payload: RecommendationActionRequest, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    profile = require_recommendation_profile(db, recommendation_id, user)
    try:
        return adaptive_recommendation_action(db, recommendation_id, "save", payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.post("/adaptive-experiments/{recommendation_id}/start")
async def post_adaptive_start(recommendation_id: str, payload: RecommendationActionRequest, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    profile = require_recommendation_profile(db, recommendation_id, user)
    try:
        return adaptive_recommendation_action(db, recommendation_id, "start", payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.post("/adaptive-experiments/{recommendation_id}/lifecycle")
async def post_adaptive_lifecycle(recommendation_id: str, payload: AdaptiveLifecycleRequest, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    profile = require_recommendation_profile(db, recommendation_id, user)
    try:
        return transition_adaptive_lifecycle(db, recommendation_id, payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.post("/adaptive-experiments/{recommendation_id}/outcome")
async def post_adaptive_outcome(recommendation_id: str, payload: DictRequest, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    profile = require_recommendation_profile(db, recommendation_id, user)
    try:
        return record_adaptive_outcome(db, recommendation_id, payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.post("/adaptive-experiments/{recommendation_id}/complete")
async def post_adaptive_complete(recommendation_id: str, payload: DictRequest, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    profile = require_recommendation_profile(db, recommendation_id, user)
    try:
        return record_adaptive_outcome(db, recommendation_id, payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.get("/adaptive-experiments/{recommendation_id}/evidence-capture")
async def get_adaptive_evidence_capture(recommendation_id: str, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    require_recommendation_profile(db, recommendation_id, user)
    try:
        return get_evidence_capture_proposal(db, recommendation_id)
    except Exception as error:
        _handle(error)
        raise


@router.post("/adaptive-experiments/{recommendation_id}/evidence-capture/review")
async def post_adaptive_evidence_capture_review(recommendation_id: str, payload: EvidenceCaptureReviewRequest, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    profile = require_recommendation_profile(db, recommendation_id, user)
    try:
        return review_evidence_capture_proposal(db, recommendation_id, payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.get("/adaptive-experiments/{recommendation_id}/alternatives")
async def get_adaptive_alternatives(recommendation_id: str, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> list[dict[str, Any]]:
    require_recommendation_profile(db, recommendation_id, user)
    try:
        return adaptive_alternatives(db, recommendation_id)
    except Exception as error:
        _handle(error)
        raise


@router.get("/transition-simulations/presets")
async def get_transition_presets() -> list[dict[str, Any]]:
    return transition_presets()


@router.post("/profiles/{profile_id}/transition-simulations")
async def post_transition_simulation(
    profile_id: str,
    payload: TransitionSimulationRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    try:
        return create_transition_simulation(db, profile, payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.get("/profiles/{profile_id}/transition-simulations")
async def get_profile_transition_simulations(profile_id: str, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> list[dict[str, Any]]:
    profile = require_profile(db, profile_id, user)
    return list_transition_simulations(db, profile)


@router.get("/transition-simulations/{simulation_id}")
async def get_transition_simulation_route(simulation_id: str, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    profile = require_simulation_profile(db, simulation_id, user)
    return get_transition_simulation(db, simulation_id, profile)


@router.post("/transition-simulations/{simulation_id}/run")
async def post_transition_simulation_run(simulation_id: str, payload: TransitionSimulationRequest, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    profile = require_simulation_profile(db, simulation_id, user)
    try:
        return rerun_transition_simulation(db, simulation_id, payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.post("/transition-simulations/{simulation_id}/scenarios")
async def post_transition_scenario(simulation_id: str, payload: TransitionSimulationRequest, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    profile = require_simulation_profile(db, simulation_id, user)
    try:
        return rerun_transition_simulation(db, simulation_id, payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.get("/transition-simulations/{simulation_id}/pareto-front")
async def get_transition_pareto_front(simulation_id: str, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    require_simulation_profile(db, simulation_id, user)
    try:
        return transition_pareto_front(db, simulation_id)
    except Exception as error:
        _handle(error)
        raise


@router.post("/transition-simulations/{simulation_id}/compare")
async def post_transition_compare(simulation_id: str, payload: DictRequest, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    require_simulation_profile(db, simulation_id, user)
    try:
        return compare_transition_scenarios(db, simulation_id, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.post("/transition-simulations/{simulation_id}/constraints")
async def post_transition_constraints(simulation_id: str, payload: DictRequest, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    profile = require_simulation_profile(db, simulation_id, user)
    try:
        return update_transition_constraints(db, simulation_id, payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.post("/transition-simulations/{simulation_id}/archive")
async def post_transition_archive(simulation_id: str, payload: DictRequest, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    profile = require_simulation_profile(db, simulation_id, user)
    try:
        return archive_transition_simulation(db, simulation_id, payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.post("/transition-paths/{path_id}/decision-journal")
async def post_transition_path_journal(path_id: str, payload: DictRequest, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    profile = require_path_profile(db, path_id, user)
    try:
        return path_to_decision_journal(db, path_id, payload.model_dump(), user.id if user else profile.user_id)
    except Exception as error:
        _handle(error)
        raise


@router.post("/transition-paths/{path_id}/propose-roadmap")
async def post_transition_path_roadmap(path_id: str, payload: DictRequest, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    require_path_profile(db, path_id, user)
    try:
        return propose_roadmap_for_path(db, path_id, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.post("/profiles/{profile_id}/recommendation-robustness")
async def post_recommendation_robustness(profile_id: str, payload: DictRequest, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    profile = require_profile(db, profile_id, user)
    return run_recommendation_robustness(db, profile, payload.model_dump(), user.id if user else profile.user_id)


@router.get("/profiles/{profile_id}/recommendation-robustness")
async def get_profile_recommendation_robustness(profile_id: str, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> list[dict[str, Any]]:
    profile = require_profile(db, profile_id, user)
    return list_robustness_runs(db, profile)


@router.get("/recommendation-robustness/{run_id}")
async def get_recommendation_robustness_run(run_id: str, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    profile = require_robustness_profile(db, run_id, user)
    return get_robustness_run(db, run_id, profile)


@router.get("/recommendation-robustness/{run_id}/dependencies")
async def get_recommendation_robustness_dependencies(run_id: str, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    require_robustness_profile(db, run_id, user)
    return robustness_dependencies(db, run_id)


@router.get("/recommendation-provenance/{target_type}/{target_id}")
async def get_recommendation_provenance(target_type: str, target_id: str, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    try:
        result = recommendation_provenance(db, target_type, target_id)
    except Exception as error:
        _handle(error)
        raise
    profile_id = result.get("profile_id")
    if profile_id:
        require_profile(db, str(profile_id), user)
    return result


@router.get("/research/fairness-test-suites")
async def get_fairness_test_suites() -> list[dict[str, Any]]:
    return fairness_test_suites()


@router.post("/research/fairness-audits")
async def post_fairness_audit(
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin_user)],
) -> dict[str, Any]:
    return run_fairness_audit(db, payload.model_dump())


@router.get("/research/fairness-audits")
async def get_fairness_audits(db: Annotated[Session, Depends(get_db)]) -> list[dict[str, Any]]:
    return list_fairness_audits(db)


@router.get("/research/fairness-audits/{audit_id}")
async def get_fairness_audit_route(audit_id: str, db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    try:
        return get_fairness_audit(db, audit_id)
    except Exception as error:
        _handle(error)
        raise


@router.get("/research/fairness-audits/{audit_id}/failures")
async def get_fairness_audit_failures(audit_id: str, db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    try:
        return fairness_audit_failures(db, audit_id)
    except Exception as error:
        _handle(error)
        raise


@router.get("/research/fairness-audits/{audit_id}/limitations")
async def get_fairness_audit_limitations(audit_id: str, db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    try:
        return fairness_audit_limitations(db, audit_id)
    except Exception as error:
        _handle(error)
        raise


@router.post("/research/fairness-audits/reset")
async def post_fairness_audit_reset(
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin_user)],
) -> dict[str, Any]:
    return reset_synthetic_fairness_lab(db, payload.model_dump())


@router.get("/recommendation-system-card")
async def get_recommendation_system_card(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    return ensure_system_card_version(db)


@router.get("/recommendation-system-card.json")
async def get_recommendation_system_card_json(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    return ensure_system_card_version(db)


@router.post("/research/originality-sessions")
async def post_originality_session(payload: ResearchSessionRequest, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_optional_user)]) -> dict[str, Any]:
    assert_research_ready()
    profile = require_profile(db, payload.profile_id, user) if payload.profile_id else None
    try:
        return create_originality_research_session(db, payload.model_dump(), profile, user.id if user else profile.user_id if profile else None)
    except Exception as error:
        _handle(error)
        raise


@router.post("/research/originality-sessions/{session_id}/baseline")
async def post_originality_baseline(
    session_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    assert_research_ready()
    require_originality_session_access(db, session_id, user)
    try:
        return update_originality_baseline(db, session_id, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.post("/research/originality-sessions/{session_id}/experimental")
async def post_originality_experimental(
    session_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    assert_research_ready()
    require_originality_session_access(db, session_id, user)
    try:
        return update_originality_experimental(db, session_id, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.post("/research/originality-sessions/{session_id}/feedback")
async def post_originality_feedback(
    session_id: str,
    payload: DictRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    assert_research_ready()
    require_originality_session_access(db, session_id, user)
    try:
        return update_originality_feedback(db, session_id, payload.model_dump())
    except Exception as error:
        _handle(error)
        raise


@router.get("/research/originality-sessions/{session_id}/results")
async def get_originality_results(
    session_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, Any]:
    require_originality_session_access(db, session_id, user)
    try:
        return originality_session_results(db, session_id)
    except Exception as error:
        _handle(error)
        raise
